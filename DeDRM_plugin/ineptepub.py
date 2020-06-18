#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement
from __future__ import absolute_import
from __future__ import print_function

# ineptepub.pyw, version 6.6
# Copyright © 2009-2020 by Apprentice Harper et al.

# Released under the terms of the GNU General Public Licence, version 3
# <http://www.gnu.org/licenses/>

# Original script by i♥cabbages
# Modified 2010–2013 by some_updates, DiapDealer and Apprentice Alf
# Modified 2015–2020 by Apprentice Harper et al.

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
#   6.7 - Add Python 3 compatibility while still working with Python 2.7

"""
Decrypt Adobe Digital Editions encrypted ePub books.
"""

__license__ = 'GPL v3'
__version__ = "6.7"

import six
from six.moves import range
import sys
import os
import traceback
import zlib
import zipfile
from zipfile import ZipInfo, ZipFile, ZIP_STORED, ZIP_DEFLATED
from contextlib import closing
import xml.etree.ElementTree as etree
import base64

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
        if isinstance(data,six.text_type):
            data = data.encode(self.encoding,"replace")
        self.stream.write(data)
        self.stream.flush()
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
        return [u"ineptepub.py"]
    else:
        argvencoding = sys.stdin.encoding
        if argvencoding == None:
            argvencoding = "utf-8"
        return [arg if (type(arg) == six.text_type) else six.text_type(arg,argvencoding) for arg in sys.argv]


class ADEPTError(Exception):
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
        raise ADEPTError('libcrypto not found')
    libcrypto = CDLL(libcrypto)

    RSA_NO_PADDING = 3
    AES_MAXNR = 14

    c_char_pp = POINTER(c_char_p)
    c_int_p = POINTER(c_int)

    class RSA(Structure):
        pass
    RSA_p = POINTER(RSA)

    class AES_KEY(Structure):
        _fields_ = [('rd_key', c_long * (4 * (AES_MAXNR + 1))),
                    ('rounds', c_int)]
    AES_KEY_p = POINTER(AES_KEY)

    def F(restype, name, argtypes):
        func = getattr(libcrypto, name)
        func.restype = restype
        func.argtypes = argtypes
        return func

    d2i_RSAPrivateKey = F(RSA_p, 'd2i_RSAPrivateKey',
                          [RSA_p, c_char_pp, c_long])
    RSA_size = F(c_int, 'RSA_size', [RSA_p])
    RSA_private_decrypt = F(c_int, 'RSA_private_decrypt',
                            [c_int, c_char_p, c_char_p, RSA_p, c_int])
    RSA_free = F(None, 'RSA_free', [RSA_p])
    AES_set_decrypt_key = F(c_int, 'AES_set_decrypt_key',
                            [c_char_p, c_int, AES_KEY_p])
    AES_cbc_encrypt = F(None, 'AES_cbc_encrypt',
                        [c_char_p, c_char_p, c_ulong, AES_KEY_p, c_char_p,
                         c_int])

    class RSA(object):
        def __init__(self, der):
            buf = create_string_buffer(der)
            pp = c_char_pp(cast(buf, c_char_p))
            rsa = self._rsa = d2i_RSAPrivateKey(None, pp, len(der))
            if rsa is None:
                raise ADEPTError('Error parsing ADEPT user key DER')

        def decrypt(self, from_):
            rsa = self._rsa
            to = create_string_buffer(RSA_size(rsa))
            dlen = RSA_private_decrypt(len(from_), from_, to, rsa,
                                       RSA_NO_PADDING)
            if dlen < 0:
                raise ADEPTError('RSA decryption failed')
            return to[:dlen]

        def __del__(self):
            if self._rsa is not None:
                RSA_free(self._rsa)
                self._rsa = None

    class AES(object):
        def __init__(self, userkey):
            self._blocksize = len(userkey)
            if (self._blocksize != 16) and (self._blocksize != 24) and (self._blocksize != 32) :
                raise ADEPTError('AES improper key used')
                return
            key = self._key = AES_KEY()
            rv = AES_set_decrypt_key(userkey, len(userkey) * 8, key)
            if rv < 0:
                raise ADEPTError('Failed to initialize AES key')

        def decrypt(self, data):
            out = create_string_buffer(len(data))
            iv = (b"\x00" * self._blocksize)
            rv = AES_cbc_encrypt(data, out, len(data), self._key, iv, 0)
            if rv == 0:
                raise ADEPTError('AES decryption failed')
            return out.raw

    return (AES, RSA)

def _load_crypto_pycrypto():
    from Crypto.Cipher import AES as _AES
    from Crypto.PublicKey import RSA as _RSA

    # ASN.1 parsing code from tlslite
    class ASN1Error(Exception):
        pass

    class ASN1Parser(object):
        class Parser(object):
            def __init__(self, bytes):
                self.bytes = bytes
                self.index = 0

            def get(self, length):
                if self.index + length > len(self.bytes):
                    raise ASN1Error("Error decoding ASN.1")
                x = 0
                for count in range(length):
                    x <<= 8
                    x |= self.bytes[self.index]
                    self.index += 1
                return x

            def getFixBytes(self, lengthBytes):
                bytes = self.bytes[self.index : self.index+lengthBytes]
                self.index += lengthBytes
                return bytes

            def getVarBytes(self, lengthLength):
                lengthBytes = self.get(lengthLength)
                return self.getFixBytes(lengthBytes)

            def getFixList(self, length, lengthList):
                l = [0] * lengthList
                for x in range(lengthList):
                    l[x] = self.get(length)
                return l

            def getVarList(self, length, lengthLength):
                lengthList = self.get(lengthLength)
                if lengthList % length != 0:
                    raise ASN1Error("Error decoding ASN.1")
                lengthList = int(lengthList/length)
                l = [0] * lengthList
                for x in range(lengthList):
                    l[x] = self.get(length)
                return l

            def startLengthCheck(self, lengthLength):
                self.lengthCheck = self.get(lengthLength)
                self.indexCheck = self.index

            def setLengthCheck(self, length):
                self.lengthCheck = length
                self.indexCheck = self.index

            def stopLengthCheck(self):
                if (self.index - self.indexCheck) != self.lengthCheck:
                    raise ASN1Error("Error decoding ASN.1")

            def atLengthCheck(self):
                if (self.index - self.indexCheck) < self.lengthCheck:
                    return False
                elif (self.index - self.indexCheck) == self.lengthCheck:
                    return True
                else:
                    raise ASN1Error("Error decoding ASN.1")

        def __init__(self, bytes):
            p = self.Parser(bytes)
            p.get(1)
            self.length = self._getASN1Length(p)
            self.value = p.getFixBytes(self.length)

        def getChild(self, which):
            p = self.Parser(self.value)
            for x in range(which+1):
                markIndex = p.index
                p.get(1)
                length = self._getASN1Length(p)
                p.getFixBytes(length)
            return ASN1Parser(p.bytes[markIndex:p.index])

        def _getASN1Length(self, p):
            firstLength = p.get(1)
            if firstLength<=127:
                return firstLength
            else:
                lengthLength = firstLength & 0x7F
                return p.get(lengthLength)

    class AES(object):
        def __init__(self, key):
            self._aes = _AES.new(key, _AES.MODE_CBC, '\x00'*16)

        def decrypt(self, data):
            return self._aes.decrypt(data)

    class RSA(object):
        def __init__(self, der):
            key = ASN1Parser([ord(x) for x in der])
            key = [key.getChild(x).value for x in range(1, 4)]
            key = [self.bytesToNumber(v) for v in key]
            self._rsa = _RSA.construct(key)

        def bytesToNumber(self, bytes):
            total = 0
            for byte in bytes:
                total = (total << 8) + byte
            return total

        def decrypt(self, data):
            return self._rsa.decrypt(data)

    return (AES, RSA)

def _load_crypto():
    AES = RSA = None
    cryptolist = (_load_crypto_libcrypto, _load_crypto_pycrypto)
    if sys.platform.startswith('win'):
        cryptolist = (_load_crypto_pycrypto, _load_crypto_libcrypto)
    for loader in cryptolist:
        try:
            AES, RSA = loader()
            break
        except (ImportError, ADEPTError):
            pass
    return (AES, RSA)

AES, RSA = _load_crypto()

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
            if len(bookkey) == 172:
                return True
        except:
            # if we couldn't check, assume it is
            return True
    return False

def decryptBook(userkey, inpath, outpath):
    if AES is None:
        raise ADEPTError(u"PyCrypto or OpenSSL must be installed.")
    rsa = RSA(userkey)
    with closing(ZipFile(open(inpath, 'rb'))) as inf:
        namelist = set(inf.namelist())
        if 'META-INF/rights.xml' not in namelist or \
           'META-INF/encryption.xml' not in namelist:
            print(u"{0:s} is DRM-free.".format(os.path.basename(inpath)))
            return 1
        for name in META_NAMES:
            namelist.remove(name)
        try:
            rights = etree.fromstring(inf.read('META-INF/rights.xml'))
            adept = lambda tag: '{%s}%s' % (NSMAP['adept'], tag)
            expr = './/%s' % (adept('encryptedKey'),)
            bookkey = ''.join(rights.findtext(expr))
            if len(bookkey) != 172:
                print(u"{0:s} is not a secure Adobe Adept ePub.".format(os.path.basename(inpath)))
                return 1
            bookkey = bookkey.encode('ascii')
            bookkey = base64.b64decode(bookkey)
            bookkey = rsa.decrypt(bookkey)
            # Padded as per RSAES-PKCS1-v1_5
            if bookkey[-17] != '\x00' and bookkey[-17] != 0:
                print(u"Could not decrypt {0:s}. Wrong key".format(os.path.basename(inpath)))
                return 2
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
            print(u"Could not decrypt {0:s} because of an exception:\n{1:s}".format(os.path.basename(inpath), traceback.format_exc()))
            return 2
    return 0


def cli_main():
    sys.stdout=SafeUnbuffered(sys.stdout)
    sys.stderr=SafeUnbuffered(sys.stderr)
    argv=unicode_argv()
    progname = os.path.basename(argv[0])
    if len(argv) != 4:
        print(u"usage: {0} <keyfile.der> <inbook.epub> <outbook.epub>".format(progname))
        return 1
    keypath, inpath, outpath = argv[1:]
    userkey = open(keypath,'rb').read()
    result = decryptBook(userkey, inpath, outpath)
    if result == 0:
        print(u"Successfully decrypted {0:s} as {1:s}".format(os.path.basename(inpath),os.path.basename(outpath)))
    return result

def gui_main():
    try:
        import six.moves.tkinter
        import six.moves.tkinter_constants
        import six.moves.tkinter_filedialog
        import six.moves.tkinter_messagebox
        import traceback
    except:
        return cli_main()

    class DecryptionDialog(six.moves.tkinter.Frame):
        def __init__(self, root):
            six.moves.tkinter.Frame.__init__(self, root, border=5)
            self.status = six.moves.tkinter.Label(self, text=u"Select files for decryption")
            self.status.pack(fill=six.moves.tkinter_constants.X, expand=1)
            body = six.moves.tkinter.Frame(self)
            body.pack(fill=six.moves.tkinter_constants.X, expand=1)
            sticky = six.moves.tkinter_constants.E + six.moves.tkinter_constants.W
            body.grid_columnconfigure(1, weight=2)
            six.moves.tkinter.Label(body, text=u"Key file").grid(row=0)
            self.keypath = six.moves.tkinter.Entry(body, width=30)
            self.keypath.grid(row=0, column=1, sticky=sticky)
            if os.path.exists(u"adeptkey.der"):
                self.keypath.insert(0, u"adeptkey.der")
            button = six.moves.tkinter.Button(body, text=u"...", command=self.get_keypath)
            button.grid(row=0, column=2)
            six.moves.tkinter.Label(body, text=u"Input file").grid(row=1)
            self.inpath = six.moves.tkinter.Entry(body, width=30)
            self.inpath.grid(row=1, column=1, sticky=sticky)
            button = six.moves.tkinter.Button(body, text=u"...", command=self.get_inpath)
            button.grid(row=1, column=2)
            six.moves.tkinter.Label(body, text=u"Output file").grid(row=2)
            self.outpath = six.moves.tkinter.Entry(body, width=30)
            self.outpath.grid(row=2, column=1, sticky=sticky)
            button = six.moves.tkinter.Button(body, text=u"...", command=self.get_outpath)
            button.grid(row=2, column=2)
            buttons = six.moves.tkinter.Frame(self)
            buttons.pack()
            botton = six.moves.tkinter.Button(
                buttons, text=u"Decrypt", width=10, command=self.decrypt)
            botton.pack(side=six.moves.tkinter_constants.LEFT)
            six.moves.tkinter.Frame(buttons, width=10).pack(side=six.moves.tkinter_constants.LEFT)
            button = six.moves.tkinter.Button(
                buttons, text=u"Quit", width=10, command=self.quit)
            button.pack(side=six.moves.tkinter_constants.RIGHT)

        def get_keypath(self):
            keypath = six.moves.tkinter_filedialog.askopenfilename(
                parent=None, title=u"Select Adobe Adept \'.der\' key file",
                defaultextension=u".der",
                filetypes=[('Adobe Adept DER-encoded files', '.der'),
                           ('All Files', '.*')])
            if keypath:
                keypath = os.path.normpath(keypath)
                self.keypath.delete(0, six.moves.tkinter_constants.END)
                self.keypath.insert(0, keypath)
            return

        def get_inpath(self):
            inpath = six.moves.tkinter_filedialog.askopenfilename(
                parent=None, title=u"Select ADEPT-encrypted ePub file to decrypt",
                defaultextension=u".epub", filetypes=[('ePub files', '.epub')])
            if inpath:
                inpath = os.path.normpath(inpath)
                self.inpath.delete(0, six.moves.tkinter_constants.END)
                self.inpath.insert(0, inpath)
            return

        def get_outpath(self):
            outpath = six.moves.tkinter_filedialog.asksaveasfilename(
                parent=None, title=u"Select unencrypted ePub file to produce",
                defaultextension=u".epub", filetypes=[('ePub files', '.epub')])
            if outpath:
                outpath = os.path.normpath(outpath)
                self.outpath.delete(0, six.moves.tkinter_constants.END)
                self.outpath.insert(0, outpath)
            return

        def decrypt(self):
            keypath = self.keypath.get()
            inpath = self.inpath.get()
            outpath = self.outpath.get()
            if not keypath or not os.path.exists(keypath):
                self.status['text'] = u"Specified key file does not exist"
                return
            if not inpath or not os.path.exists(inpath):
                self.status['text'] = u"Specified input file does not exist"
                return
            if not outpath:
                self.status['text'] = u"Output file not specified"
                return
            if inpath == outpath:
                self.status['text'] = u"Must have different input and output files"
                return
            userkey = open(keypath,'rb').read()
            self.status['text'] = u"Decrypting..."
            try:
                decrypt_status = decryptBook(userkey, inpath, outpath)
            except Exception as e:
                self.status['text'] = u"Error: {0}".format(e.args[0])
                return
            if decrypt_status == 0:
                self.status['text'] = u"File successfully decrypted"
            else:
                self.status['text'] = u"The was an error decrypting the file."

    root = six.moves.tkinter.Tk()
    root.title(u"Adobe Adept ePub Decrypter v.{0}".format(__version__))
    root.resizable(True, False)
    root.minsize(300, 0)
    DecryptionDialog(root).pack(fill=six.moves.tkinter_constants.X, expand=1)
    root.mainloop()
    return 0

if __name__ == '__main__':
    if len(sys.argv) > 1:
        sys.exit(cli_main())
    sys.exit(gui_main())
