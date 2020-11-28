#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ignobleepub.py
# Copyright © 2009-2020 by i♥cabbages, Apprentice Harper et al.

# Released under the terms of the GNU General Public Licence, version 3
# <http://www.gnu.org/licenses/>

#
# Revision history:
#   1 - Initial release
#   2 - Added OS X support by using OpenSSL when available
#   3 - screen out improper key lengths to prevent segfaults on Linux
#   3.1 - Allow Windows versions of libcrypto to be found
#   3.2 - add support for encoding to 'utf-8' when building up list of files to decrypt from encryption.xml
#   3.3 - On Windows try PyCrypto first, OpenSSL next
#   3.4 - Modify interface to allow use with import
#   3.5 - Fix for potential problem with PyCrypto
#   3.6 - Revised to allow use in calibre plugins to eliminate need for duplicate code
#   3.7 - Tweaked to match ineptepub more closely
#   3.8 - Fixed to retain zip file metadata (e.g. file modification date)
#   3.9 - moved unicode_argv call inside main for Windows DeDRM compatibility
#   4.0 - Work if TkInter is missing
#   4.1 - Import tkFileDialog, don't assume something else will import it.
#   5.0 - Python 3 for calibre 5.0

"""
Decrypt Barnes & Noble encrypted ePub books.
"""

__license__ = 'GPL v3'
__version__ = "5.0"

import sys
import os
import traceback
import base64
import zlib
import zipfile
from zipfile import ZipInfo, ZipFile, ZIP_STORED, ZIP_DEFLATED
from contextlib import closing
import xml.etree.ElementTree as etree

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
        if isinstance(data,str):
            data = data.encode(self.encoding,"replace")
        self.stream.buffer.write(data)
        self.stream.buffer.flush()
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
        return [arg if isinstance(arg, str) else str(arg, argvencoding) for arg in sys.argv]


class IGNOBLEError(Exception):
    pass

def _load_crypto_libcrypto():
    from ctypes import CDLL, POINTER, c_void_p, c_char_p, c_int, c_long, \
        Structure, c_ulong, create_string_buffer, cast
    from ctypes.util import find_library

    if iswindows:
        libcrypto = find_library('libeay32')
    else:
        libcrypto = find_library('crypto')

    if libcrypto is None:
        raise IGNOBLEError('libcrypto not found')
    libcrypto = CDLL(libcrypto)

    AES_MAXNR = 14

    c_char_pp = POINTER(c_char_p)
    c_int_p = POINTER(c_int)

    class AES_KEY(Structure):
        _fields_ = [('rd_key', c_long * (4 * (AES_MAXNR + 1))),
                    ('rounds', c_int)]
    AES_KEY_p = POINTER(AES_KEY)

    def F(restype, name, argtypes):
        func = getattr(libcrypto, name)
        func.restype = restype
        func.argtypes = argtypes
        return func

    AES_set_decrypt_key = F(c_int, 'AES_set_decrypt_key',
                            [c_char_p, c_int, AES_KEY_p])
    AES_cbc_encrypt = F(None, 'AES_cbc_encrypt',
                        [c_char_p, c_char_p, c_ulong, AES_KEY_p, c_char_p,
                         c_int])

    class AES(object):
        def __init__(self, userkey):
            self._blocksize = len(userkey)
            if (self._blocksize != 16) and (self._blocksize != 24) and (self._blocksize != 32) :
                raise IGNOBLEError('AES improper key used')
                return
            key = self._key = AES_KEY()
            rv = AES_set_decrypt_key(userkey, len(userkey) * 8, key)
            if rv < 0:
                raise IGNOBLEError('Failed to initialize AES key')

        def decrypt(self, data):
            out = create_string_buffer(len(data))
            iv = (b'\x00' * self._blocksize)
            rv = AES_cbc_encrypt(data, out, len(data), self._key, iv, 0)
            if rv == 0:
                raise IGNOBLEError('AES decryption failed')
            return out.raw

    return AES

def _load_crypto_pycrypto():
    from Crypto.Cipher import AES as _AES

    class AES(object):
        def __init__(self, key):
            self._aes = _AES.new(key, _AES.MODE_CBC, b'\x00'*16)

        def decrypt(self, data):
            return self._aes.decrypt(data)

    return AES

def _load_crypto():
    AES = None
    cryptolist = (_load_crypto_libcrypto, _load_crypto_pycrypto)
    if sys.platform.startswith('win'):
        cryptolist = (_load_crypto_pycrypto, _load_crypto_libcrypto)
    for loader in cryptolist:
        try:
            AES = loader()
            break
        except (ImportError, IGNOBLEError):
            pass
    return AES

AES = _load_crypto()

META_NAMES = ('mimetype', 'META-INF/rights.xml', 'META-INF/encryption.xml')
NSMAP = {'adept': 'http://ns.adobe.com/adept',
         'enc': 'http://www.w3.org/2001/04/xmlenc#'}

class Decryptor(object):
    def __init__(self, bookkey, encryption):
        enc = lambda tag: '{%s}%s' % (NSMAP['enc'], tag)
        self._aes = AES(bookkey)
        encryption = etree.fromstring(encryption)
        self._encrypted = encrypted = set()
        expr = './%s/%s/%s' % (enc('EncryptedData'), enc('CipherData'),
                               enc('CipherReference'))
        for elem in encryption.findall(expr):
            path = elem.get('URI', None)
            if path is not None:
                path = path.encode('utf-8')
                encrypted.add(path)

    def decompress(self, bytes):
        dc = zlib.decompressobj(-15)
        bytes = dc.decompress(bytes)
        ex = dc.decompress(b'Z') + dc.flush()
        if ex:
            bytes = bytes + ex
        return bytes

    def decrypt(self, path, data):
        if bytes(path,'utf-8') in self._encrypted:
            data = self._aes.decrypt(data)[16:]
            data = data[:-data[-1]]
            data = self.decompress(data)
        return data

# check file to make check whether it's probably an Adobe Adept encrypted ePub
def ignobleBook(inpath):
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
            # if we couldn't check, assume it is
            return True
    return False

def decryptBook(keyb64, inpath, outpath):
    if AES is None:
        raise IGNOBLEError("PyCrypto or OpenSSL must be installed.")
    key = base64.b64decode(keyb64)[:16]
    aes = AES(key)
    with closing(ZipFile(open(inpath, 'rb'))) as inf:
        namelist = set(inf.namelist())
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
            bookkey = ''.join(rights.findtext(expr))
            if len(bookkey) != 64:
                print("{0:s} is not a secure Barnes & Noble ePub.".format(os.path.basename(inpath)))
                return 1
            bookkey = aes.decrypt(base64.b64decode(bookkey))
            bookkey = bookkey[:-bookkey[-1]]
            encryption = inf.read('META-INF/encryption.xml')
            decryptor = Decryptor(bookkey[-16:], encryption)
            kwds = dict(compression=ZIP_DEFLATED, allowZip64=False)
            with closing(ZipFile(open(outpath, 'wb'), 'w', **kwds)) as outf:
                zi = ZipInfo('mimetype')
                zi.compress_type=ZIP_STORED
                try:
                    # if the mimetype is present, get its info, including time-stamp
                    oldzi = inf.getinfo('mimetype')
                    # copy across fields to be preserved
                    zi.date_time = oldzi.date_time
                    zi.comment = oldzi.comment
                    zi.extra = oldzi.extra
                    zi.internal_attr = oldzi.internal_attr
                    # external attributes are dependent on the create system, so copy both.
                    zi.external_attr = oldzi.external_attr
                    zi.create_system = oldzi.create_system
                except:
                    pass
                outf.writestr(zi, inf.read('mimetype'))
                for path in namelist:
                    data = inf.read(path)
                    zi = ZipInfo(path)
                    zi.compress_type=ZIP_DEFLATED
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
                    except:
                        pass
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
        print("usage: {0} <keyfile.b64> <inbook.epub> <outbook.epub>".format(progname))
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
            if os.path.exists("bnepubkey.b64"):
                self.keypath.insert(0, "bnepubkey.b64")
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
                parent=None, title="Select Barnes & Noble \'.b64\' key file",
                defaultextension=".b64",
                filetypes=[('base64-encoded files', '.b64'),
                           ('All Files', '.*')])
            if keypath:
                keypath = os.path.normpath(keypath)
                self.keypath.delete(0, tkinter.constants.END)
                self.keypath.insert(0, keypath)
            return

        def get_inpath(self):
            inpath = tkinter.filedialog.askopenfilename(
                parent=None, title="Select B&N-encrypted ePub file to decrypt",
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
                self.status['text'] = "The was an error decrypting the file."

    root = tkinter.Tk()
    root.title("Barnes & Noble ePub Decrypter v.{0}".format(__version__))
    root.resizable(True, False)
    root.minsize(300, 0)
    DecryptionDialog(root).pack(fill=tkinter.constants.X, expand=1)
    root.mainloop()
    return 0

if __name__ == '__main__':
    if len(sys.argv) > 1:
        sys.exit(cli_main())
    sys.exit(gui_main())
