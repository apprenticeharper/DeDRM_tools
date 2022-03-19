#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ineptepub.py
# Copyright © 2009-2022 by i♥cabbages, Apprentice Harper et al.

# Released under the terms of the GNU General Public Licence, version 3
# <http://www.gnu.org/licenses/>


# Revision history:
#   1 - Initial release
#   2 - Rename to INEPT, fix exit code
#   5 - Version bump to avoid (?) confusion;
#       Improve OS X support by using OpenSSL when available
#   5.1 - Improve OpenSSL error checking
#   5.2 - Fix ctypes error causing segfaults on some systems
#   5.3 - add support for OpenSSL on Windows, fix bug with some versions of libcrypto 0.9.8 prior to path level o
#   5.4 - add support for encoding to 'utf-8' when building up list of files to decrypt from encryption.xml
#   5.5 - On Windows try PyCrypto first, OpenSSL next
#   5.6 - Modify interface to allow use with import
#   5.7 - Fix for potential problem with PyCrypto
#   5.8 - Revised to allow use in calibre plugins to eliminate need for duplicate code
#   5.9 - Fixed to retain zip file metadata (e.g. file modification date)
#   6.0 - moved unicode_argv call inside main for Windows DeDRM compatibility
#   6.1 - Work if TkInter is missing
#   6.2 - Handle UTF-8 file names inside an ePub, fix by Jose Luis
#   6.3 - Add additional check on DER file sanity
#   6.4 - Remove erroneous check on DER file sanity
#   6.5 - Completely remove erroneous check on DER file sanity
#   6.6 - Import tkFileDialog, don't assume something else will import it.
#   7.0 - Add Python 3 compatibility for calibre 5.0
#   7.1 - Add ignoble support, dropping the dedicated ignobleepub.py script
#   7.2 - Only support PyCryptodome; clean up the code
#   8.0 - Add support for "hardened" Adobe DRM (RMSDK >= 10)

"""
Decrypt Adobe Digital Editions encrypted ePub books.
"""

__license__ = 'GPL v3'
__version__ = "8.0"

import sys
import os
import traceback
import base64
import zlib
import zipfile
from zipfile import ZipInfo, ZipFile, ZIP_STORED, ZIP_DEFLATED
from contextlib import closing
from lxml import etree
from uuid import UUID
import hashlib

try:
    from Cryptodome.Cipher import AES, PKCS1_v1_5
    from Cryptodome.PublicKey import RSA
except ImportError:
    from Crypto.Cipher import AES, PKCS1_v1_5
    from Crypto.PublicKey import RSA


def unpad(data, padding=16):
    if sys.version_info[0] == 2:
        pad_len = ord(data[-1])
    else:
        pad_len = data[-1]

    return data[:-pad_len]

# Wrap a stream so that output gets flushed immediately
# and also make sure that any unicode strings get
# encoded using "replace" before writing them.
class SafeUnbuffered:
    def __init__(self, stream):
        self.stream = stream
        self.encoding = stream.encoding
        if self.encoding == None:
            self.encoding = "utf-8"
    def write(self, data):
        if isinstance(data,str) or isinstance(data,unicode):
            # str for Python3, unicode for Python2
            data = data.encode(self.encoding,"replace")
        try:
            buffer = getattr(self.stream, 'buffer', self.stream)
            # self.stream.buffer for Python3, self.stream for Python2
            buffer.write(data)
            buffer.flush()
        except:
            # We can do nothing if a write fails
            raise
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

try:
    from calibre.constants import iswindows, isosx
except:
    iswindows = sys.platform.startswith('win')
    isosx = sys.platform.startswith('darwin')

def unicode_argv():
    if iswindows:
        # Uses shell32.GetCommandLineArgvW to get sys.argv as a list of Unicode
        # strings.

        # Versions 2.x of Python don't support Unicode in sys.argv on
        # Windows, with the underlying Windows API instead replacing multi-byte
        # characters with '?'.


        from ctypes import POINTER, byref, cdll, c_int, windll
        from ctypes.wintypes import LPCWSTR, LPWSTR

        GetCommandLineW = cdll.kernel32.GetCommandLineW
        GetCommandLineW.argtypes = []
        GetCommandLineW.restype = LPCWSTR

        CommandLineToArgvW = windll.shell32.CommandLineToArgvW
        CommandLineToArgvW.argtypes = [LPCWSTR, POINTER(c_int)]
        CommandLineToArgvW.restype = POINTER(LPWSTR)

        cmd = GetCommandLineW()
        argc = c_int(0)
        argv = CommandLineToArgvW(cmd, byref(argc))
        if argc.value > 0:
            # Remove Python executable and commands if present
            start = argc.value - len(sys.argv)
            return [argv[i] for i in
                    range(start, argc.value)]
        return ["ineptepub.py"]
    else:
        argvencoding = sys.stdin.encoding or "utf-8"
        return [arg if (isinstance(arg, str) or isinstance(arg,unicode)) else str(arg, argvencoding) for arg in sys.argv]


class ADEPTError(Exception):
    pass

class ADEPTNewVersionError(Exception):
    pass

META_NAMES = ('mimetype', 'META-INF/rights.xml')
NSMAP = {'adept': 'http://ns.adobe.com/adept',
         'enc': 'http://www.w3.org/2001/04/xmlenc#'}

class Decryptor(object):
    def __init__(self, bookkey, encryption):
        enc = lambda tag: '{%s}%s' % (NSMAP['enc'], tag)
        self._aes = AES.new(bookkey, AES.MODE_CBC, b'\x00'*16)
        encryption = etree.fromstring(encryption)
        self._encrypted = encrypted = set()
        self._otherData = otherData = set()

        self._json_elements_to_remove = json_elements_to_remove = set()
        self._has_remaining_xml = False
        expr = './%s/%s/%s' % (enc('EncryptedData'), enc('CipherData'),
                               enc('CipherReference'))
        for elem in encryption.findall(expr):
            path = elem.get('URI', None)
            encryption_type_url = (elem.getparent().getparent().find("./%s" % (enc('EncryptionMethod'))).get('Algorithm', None))
            if path is not None:
                if (encryption_type_url == "http://www.w3.org/2001/04/xmlenc#aes128-cbc"):
                    # Adobe
                    path = path.encode('utf-8')
                    encrypted.add(path)
                    json_elements_to_remove.add(elem.getparent().getparent())
                else:
                    path = path.encode('utf-8')
                    otherData.add(path)
                    self._has_remaining_xml = True

        for elem in json_elements_to_remove:
            elem.getparent().remove(elem)

    def check_if_remaining(self):
        return self._has_remaining_xml

    def get_xml(self):
        return "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" + etree.tostring(self._encryption, encoding="utf-8", pretty_print=True, xml_declaration=False).decode("utf-8")


    def decompress(self, bytes):
        dc = zlib.decompressobj(-15)
        try:
            decompressed_bytes = dc.decompress(bytes)
            ex = dc.decompress(b'Z') + dc.flush()
            if ex:
                decompressed_bytes = decompressed_bytes + ex
        except:
            # possibly not compressed by zip - just return bytes
            return bytes
        return decompressed_bytes

    def decrypt(self, path, data):
        if path.encode('utf-8') in self._encrypted:
            data = self._aes.decrypt(data)[16:]
            if type(data[-1]) != int:
                place = ord(data[-1])
            else:
                place = data[-1]
            data = data[:-place]
            data = self.decompress(data)
        return data

# check file to make check whether it's probably an Adobe Adept encrypted ePub
def adeptBook(inpath):
    with closing(ZipFile(open(inpath, 'rb'))) as inf:
        namelist = set(inf.namelist())
        if 'META-INF/rights.xml' not in namelist or \
           'META-INF/encryption.xml' not in namelist:
            return False
        try:
            rights = etree.fromstring(inf.read('META-INF/rights.xml'))
            adept = lambda tag: '{%s}%s' % (NSMAP['adept'], tag)
            expr = './/%s' % (adept('encryptedKey'),)
            bookkey = ''.join(rights.findtext(expr))
            if len(bookkey) in [192, 172, 64]:
                return True
        except:
            # if we couldn't check, assume it is
            return True
    return False

def isPassHashBook(inpath):
    # If this is an Adobe book, check if it's a PassHash-encrypted book (B&N)
    with closing(ZipFile(open(inpath, 'rb'))) as inf:
        namelist = set(inf.namelist())
        if 'META-INF/rights.xml' not in namelist or \
           'META-INF/encryption.xml' not in namelist:
            return False
        try:
            rights = etree.fromstring(inf.read('META-INF/rights.xml'))
            adept = lambda tag: '{%s}%s' % (NSMAP['adept'], tag)
            expr = './/%s' % (adept('encryptedKey'),)
            bookkey = ''.join(rights.findtext(expr))
            if len(bookkey) == 64:
                return True
        except:
            pass

    return False

# Checks the license file and returns the UUID the book is licensed for.
# This is used so that the Calibre plugin can pick the correct decryption key
# first try without having to loop through all possible keys.
def adeptGetUserUUID(inpath):
    with closing(ZipFile(open(inpath, 'rb'))) as inf:
        try:
            rights = etree.fromstring(inf.read('META-INF/rights.xml'))
            adept = lambda tag: '{%s}%s' % (NSMAP['adept'], tag)
            expr = './/%s' % (adept('user'),)
            user_uuid = ''.join(rights.findtext(expr))
            if user_uuid[:9] != "urn:uuid:":
                return None
            return user_uuid[9:]
        except:
            return None

def removeHardening(rights, keytype, keydata):
    adept = lambda tag: '{%s}%s' % (NSMAP['adept'], tag)
    textGetter = lambda name: ''.join(rights.findtext('.//%s' % (adept(name),)))

    # Gather what we need, and generate the IV
    resourceuuid = UUID(textGetter("resource"))
    deviceuuid = UUID(textGetter("device"))
    fullfillmentuuid = UUID(textGetter("fulfillment")[:36])
    kekiv = UUID(int=resourceuuid.int ^ deviceuuid.int ^ fullfillmentuuid.int).bytes

    # Derive kek from just "keytype"
    rem = int(keytype, 10) % 16
    H = hashlib.sha256(keytype.encode("ascii")).digest()
    kek = H[2*rem : 16 + rem] + H[rem : 2*rem]

    return unpad(AES.new(kek, AES.MODE_CBC, kekiv).decrypt(keydata), 16) # PKCS#7

def decryptBook(userkey, inpath, outpath):
    with closing(ZipFile(open(inpath, 'rb'))) as inf:
        namelist = inf.namelist()
        if 'META-INF/rights.xml' not in namelist or \
           'META-INF/encryption.xml' not in namelist:
            print("{0:s} is DRM-free.".format(os.path.basename(inpath)))
            return 1
        for name in META_NAMES:
            namelist.remove(name)
        try:
            rights = etree.fromstring(inf.read('META-INF/rights.xml'))
            adept = lambda tag: '{%s}%s' % (NSMAP['adept'], tag)
            expr = './/%s' % (adept('encryptedKey'),)
            bookkeyelem = rights.find(expr)
            bookkey = bookkeyelem.text
            keytype = bookkeyelem.attrib.get('keyType', '0')
            if len(bookkey) >= 172 and int(keytype, 10) > 2:
                print("{0:s} is a secure Adobe Adept ePub with hardening.".format(os.path.basename(inpath)))
            elif len(bookkey) == 172:
                print("{0:s} is a secure Adobe Adept ePub.".format(os.path.basename(inpath)))
            elif len(bookkey) == 64:
                print("{0:s} is a secure Adobe PassHash (B&N) ePub.".format(os.path.basename(inpath)))
            else:
                print("{0:s} is not an Adobe-protected ePub!".format(os.path.basename(inpath)))
                return 1

            if len(bookkey) != 64:
                # Normal or "hardened" Adobe ADEPT
                rsakey = RSA.import_key(userkey) # parses the ASN1 structure
                bookkey = base64.b64decode(bookkey)
                if int(keytype, 10) > 2:
                    bookkey = removeHardening(rights, keytype, bookkey)
                try:
                    bookkey = PKCS1_v1_5.new(rsakey).decrypt(bookkey, None) # automatically unpads
                except ValueError:
                    bookkey = None

                if bookkey is None:
                    print("Could not decrypt {0:s}. Wrong key".format(os.path.basename(inpath)))
                    return 2
            else:
                # Adobe PassHash / B&N
                key = base64.b64decode(userkey)[:16]
                bookkey = base64.b64decode(bookkey)
                bookkey = unpad(AES.new(key, AES.MODE_CBC, b'\x00'*16).decrypt(bookkey), 16) # PKCS#7

                if len(bookkey) > 16:
                    bookkey = bookkey[-16:]

            encryption = inf.read('META-INF/encryption.xml')
            decryptor = Decryptor(bookkey, encryption)
            kwds = dict(compression=ZIP_DEFLATED, allowZip64=False)
            with closing(ZipFile(open(outpath, 'wb'), 'w', **kwds)) as outf:

                for path in (["mimetype"] + namelist):
                    data = inf.read(path)
                    zi = ZipInfo(path)
                    zi.compress_type=ZIP_DEFLATED

                    if path == "mimetype":
                        zi.compress_type = ZIP_STORED

                    elif path == "META-INF/encryption.xml":
                        # Check if there's still something in there
                        if (decryptor.check_if_remaining()):
                            data = decryptor.get_xml()
                            print("Adding encryption.xml for the remaining embedded files.")
                            # We removed DRM, but there's still stuff like obfuscated fonts.
                        else:
                            continue


                    try:
                        # get the file info, including time-stamp
                        oldzi = inf.getinfo(path)
                        # copy across useful fields
                        zi.date_time = oldzi.date_time
                        zi.comment = oldzi.comment
                        zi.extra = oldzi.extra
                        zi.internal_attr = oldzi.internal_attr
                        # external attributes are dependent on the create system, so copy both.
                        zi.external_attr = oldzi.external_attr
                        zi.create_system = oldzi.create_system
                        if any(ord(c) >= 128 for c in path) or any(ord(c) >= 128 for c in zi.comment):
                            # If the file name or the comment contains any non-ASCII char, set the UTF8-flag
                            zi.flag_bits |= 0x800
                    except:
                        pass
                    if path == "META-INF/encryption.xml":
                        outf.writestr(zi, data)
                    else:
                        outf.writestr(zi, decryptor.decrypt(path, data))
        except:
            print("Could not decrypt {0:s} because of an exception:\n{1:s}".format(os.path.basename(inpath), traceback.format_exc()))
            return 2
    return 0


def cli_main():
    sys.stdout=SafeUnbuffered(sys.stdout)
    sys.stderr=SafeUnbuffered(sys.stderr)
    argv=unicode_argv()
    progname = os.path.basename(argv[0])
    if len(argv) != 4:
        print("usage: {0} <keyfile.der> <inbook.epub> <outbook.epub>".format(progname))
        return 1
    keypath, inpath, outpath = argv[1:]
    userkey = open(keypath,'rb').read()
    result = decryptBook(userkey, inpath, outpath)
    if result == 0:
        print("Successfully decrypted {0:s} as {1:s}".format(os.path.basename(inpath),os.path.basename(outpath)))
    return result

def gui_main():
    try:
        import tkinter
        import tkinter.constants
        import tkinter.filedialog
        import tkinter.messagebox
        import traceback
    except:
        return cli_main()

    class DecryptionDialog(tkinter.Frame):
        def __init__(self, root):
            tkinter.Frame.__init__(self, root, border=5)
            self.status = tkinter.Label(self, text="Select files for decryption")
            self.status.pack(fill=tkinter.constants.X, expand=1)
            body = tkinter.Frame(self)
            body.pack(fill=tkinter.constants.X, expand=1)
            sticky = tkinter.constants.E + tkinter.constants.W
            body.grid_columnconfigure(1, weight=2)
            tkinter.Label(body, text="Key file").grid(row=0)
            self.keypath = tkinter.Entry(body, width=30)
            self.keypath.grid(row=0, column=1, sticky=sticky)
            if os.path.exists("adeptkey.der"):
                self.keypath.insert(0, "adeptkey.der")
            button = tkinter.Button(body, text="...", command=self.get_keypath)
            button.grid(row=0, column=2)
            tkinter.Label(body, text="Input file").grid(row=1)
            self.inpath = tkinter.Entry(body, width=30)
            self.inpath.grid(row=1, column=1, sticky=sticky)
            button = tkinter.Button(body, text="...", command=self.get_inpath)
            button.grid(row=1, column=2)
            tkinter.Label(body, text="Output file").grid(row=2)
            self.outpath = tkinter.Entry(body, width=30)
            self.outpath.grid(row=2, column=1, sticky=sticky)
            button = tkinter.Button(body, text="...", command=self.get_outpath)
            button.grid(row=2, column=2)
            buttons = tkinter.Frame(self)
            buttons.pack()
            botton = tkinter.Button(
                buttons, text="Decrypt", width=10, command=self.decrypt)
            botton.pack(side=tkinter.constants.LEFT)
            tkinter.Frame(buttons, width=10).pack(side=tkinter.constants.LEFT)
            button = tkinter.Button(
                buttons, text="Quit", width=10, command=self.quit)
            button.pack(side=tkinter.constants.RIGHT)

        def get_keypath(self):
            keypath = tkinter.filedialog.askopenfilename(
                parent=None, title="Select Adobe Adept \'.der\' key file",
                defaultextension=".der",
                filetypes=[('Adobe Adept DER-encoded files', '.der'),
                           ('All Files', '.*')])
            if keypath:
                keypath = os.path.normpath(keypath)
                self.keypath.delete(0, tkinter.constants.END)
                self.keypath.insert(0, keypath)
            return

        def get_inpath(self):
            inpath = tkinter.filedialog.askopenfilename(
                parent=None, title="Select ADEPT-encrypted ePub file to decrypt",
                defaultextension=".epub", filetypes=[('ePub files', '.epub')])
            if inpath:
                inpath = os.path.normpath(inpath)
                self.inpath.delete(0, tkinter.constants.END)
                self.inpath.insert(0, inpath)
            return

        def get_outpath(self):
            outpath = tkinter.filedialog.asksaveasfilename(
                parent=None, title="Select unencrypted ePub file to produce",
                defaultextension=".epub", filetypes=[('ePub files', '.epub')])
            if outpath:
                outpath = os.path.normpath(outpath)
                self.outpath.delete(0, tkinter.constants.END)
                self.outpath.insert(0, outpath)
            return

        def decrypt(self):
            keypath = self.keypath.get()
            inpath = self.inpath.get()
            outpath = self.outpath.get()
            if not keypath or not os.path.exists(keypath):
                self.status['text'] = "Specified key file does not exist"
                return
            if not inpath or not os.path.exists(inpath):
                self.status['text'] = "Specified input file does not exist"
                return
            if not outpath:
                self.status['text'] = "Output file not specified"
                return
            if inpath == outpath:
                self.status['text'] = "Must have different input and output files"
                return
            userkey = open(keypath,'rb').read()
            self.status['text'] = "Decrypting..."
            try:
                decrypt_status = decryptBook(userkey, inpath, outpath)
            except Exception as e:
                self.status['text'] = "Error: {0}".format(e.args[0])
                return
            if decrypt_status == 0:
                self.status['text'] = "File successfully decrypted"
            else:
                self.status['text'] = "There was an error decrypting the file."

    root = tkinter.Tk()
    root.title("Adobe Adept ePub Decrypter v.{0}".format(__version__))
    root.resizable(True, False)
    root.minsize(300, 0)
    DecryptionDialog(root).pack(fill=tkinter.constants.X, expand=1)
    root.mainloop()
    return 0

if __name__ == '__main__':
    if len(sys.argv) > 1:
        sys.exit(cli_main())
    sys.exit(gui_main())
