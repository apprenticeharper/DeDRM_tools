#! /usr/bin/python

from __future__ import with_statement

# ignobleepub.pyw, version 3.5

# To run this program install Python 2.6 from <http://www.python.org/download/>
# and OpenSSL or PyCrypto from http://www.voidspace.org.uk/python/modules.shtml#pycrypto
# (make sure to install the version for Python 2.6).  Save this script file as
# ignobleepub.pyw and double-click on it to run it.

# Revision history:
#   1 - Initial release
#   2 - Added OS X support by using OpenSSL when available
#   3 - screen out improper key lengths to prevent segfaults on Linux
#   3.1 - Allow Windows versions of libcrypto to be found
#   3.2 - add support for encoding to 'utf-8' when building up list of files to cecrypt from encryption.xml
#   3.3 - On Windows try PyCrypto first and OpenSSL next
#   3.4 - Modify interace to allow use with import
#   3.5 - Fix for potential problem with PyCrypto


__license__ = 'GPL v3'

import sys
import os
import zlib
import zipfile
from zipfile import ZipFile, ZIP_STORED, ZIP_DEFLATED
from contextlib import closing
import xml.etree.ElementTree as etree
import Tkinter
import Tkconstants
import tkFileDialog
import tkMessageBox

class IGNOBLEError(Exception):
    pass

def _load_crypto_libcrypto():
    from ctypes import CDLL, POINTER, c_void_p, c_char_p, c_int, c_long, \
        Structure, c_ulong, create_string_buffer, cast
    from ctypes.util import find_library

    if sys.platform.startswith('win'):
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

    AES_cbc_encrypt = F(None, 'AES_cbc_encrypt',
                        [c_char_p, c_char_p, c_ulong, AES_KEY_p, c_char_p,
                         c_int])
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
            iv = ("\x00" * self._blocksize)
            rv = AES_cbc_encrypt(data, out, len(data), self._key, iv, 0)
            if rv == 0:
                raise IGNOBLEError('AES decryption failed')
            return out.raw

    return AES

def _load_crypto_pycrypto():
    from Crypto.Cipher import AES as _AES

    class AES(object):
        def __init__(self, key):
            self._aes = _AES.new(key, _AES.MODE_CBC, '\x00'*16)

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



"""
Decrypt Barnes & Noble ADEPT encrypted EPUB books.
"""


META_NAMES = ('mimetype', 'META-INF/rights.xml', 'META-INF/encryption.xml')
NSMAP = {'adept': 'http://ns.adobe.com/adept',
         'enc': 'http://www.w3.org/2001/04/xmlenc#'}

class ZipInfo(zipfile.ZipInfo):
    def __init__(self, *args, **kwargs):
        if 'compress_type' in kwargs:
            compress_type = kwargs.pop('compress_type')
        super(ZipInfo, self).__init__(*args, **kwargs)
        self.compress_type = compress_type

class Decryptor(object):
    def __init__(self, bookkey, encryption):
        enc = lambda tag: '{%s}%s' % (NSMAP['enc'], tag)
        # self._aes = AES.new(bookkey, AES.MODE_CBC, '\x00'*16)
        self._aes = AES(bookkey)
        encryption = etree.fromstring(encryption)
        self._encrypted = encrypted = set()
        expr = './%s/%s/%s' % (enc('EncryptedData'), enc('CipherData'),
                               enc('CipherReference'))
        for elem in encryption.findall(expr):
            path = elem.get('URI', None)
            path = path.encode('utf-8')
            if path is not None:
                encrypted.add(path)

    def decompress(self, bytes):
        dc = zlib.decompressobj(-15)
        bytes = dc.decompress(bytes)
        ex = dc.decompress('Z') + dc.flush()
        if ex:
            bytes = bytes + ex
        return bytes

    def decrypt(self, path, data):
        if path in self._encrypted:
            data = self._aes.decrypt(data)[16:]
            data = data[:-ord(data[-1])]
            data = self.decompress(data)
        return data


class DecryptionDialog(Tkinter.Frame):
    def __init__(self, root):
        Tkinter.Frame.__init__(self, root, border=5)
        self.status = Tkinter.Label(self, text='Select files for decryption')
        self.status.pack(fill=Tkconstants.X, expand=1)
        body = Tkinter.Frame(self)
        body.pack(fill=Tkconstants.X, expand=1)
        sticky = Tkconstants.E + Tkconstants.W
        body.grid_columnconfigure(1, weight=2)
        Tkinter.Label(body, text='Key file').grid(row=0)
        self.keypath = Tkinter.Entry(body, width=30)
        self.keypath.grid(row=0, column=1, sticky=sticky)
        if os.path.exists('bnepubkey.b64'):
            self.keypath.insert(0, 'bnepubkey.b64')
        button = Tkinter.Button(body, text="...", command=self.get_keypath)
        button.grid(row=0, column=2)
        Tkinter.Label(body, text='Input file').grid(row=1)
        self.inpath = Tkinter.Entry(body, width=30)
        self.inpath.grid(row=1, column=1, sticky=sticky)
        button = Tkinter.Button(body, text="...", command=self.get_inpath)
        button.grid(row=1, column=2)
        Tkinter.Label(body, text='Output file').grid(row=2)
        self.outpath = Tkinter.Entry(body, width=30)
        self.outpath.grid(row=2, column=1, sticky=sticky)
        button = Tkinter.Button(body, text="...", command=self.get_outpath)
        button.grid(row=2, column=2)
        buttons = Tkinter.Frame(self)
        buttons.pack()
        botton = Tkinter.Button(
            buttons, text="Decrypt", width=10, command=self.decrypt)
        botton.pack(side=Tkconstants.LEFT)
        Tkinter.Frame(buttons, width=10).pack(side=Tkconstants.LEFT)
        button = Tkinter.Button(
            buttons, text="Quit", width=10, command=self.quit)
        button.pack(side=Tkconstants.RIGHT)

    def get_keypath(self):
        keypath = tkFileDialog.askopenfilename(
            parent=None, title='Select B&N EPUB key file',
            defaultextension='.b64',
            filetypes=[('base64-encoded files', '.b64'),
                       ('All Files', '.*')])
        if keypath:
            keypath = os.path.normpath(keypath)
            self.keypath.delete(0, Tkconstants.END)
            self.keypath.insert(0, keypath)
        return

    def get_inpath(self):
        inpath = tkFileDialog.askopenfilename(
            parent=None, title='Select B&N-encrypted EPUB file to decrypt',
            defaultextension='.epub', filetypes=[('EPUB files', '.epub'),
                                                 ('All files', '.*')])
        if inpath:
            inpath = os.path.normpath(inpath)
            self.inpath.delete(0, Tkconstants.END)
            self.inpath.insert(0, inpath)
        return

    def get_outpath(self):
        outpath = tkFileDialog.asksaveasfilename(
            parent=None, title='Select unencrypted EPUB file to produce',
            defaultextension='.epub', filetypes=[('EPUB files', '.epub'),
                                                 ('All files', '.*')])
        if outpath:
            outpath = os.path.normpath(outpath)
            self.outpath.delete(0, Tkconstants.END)
            self.outpath.insert(0, outpath)
        return

    def decrypt(self):
        keypath = self.keypath.get()
        inpath = self.inpath.get()
        outpath = self.outpath.get()
        if not keypath or not os.path.exists(keypath):
            self.status['text'] = 'Specified key file does not exist'
            return
        if not inpath or not os.path.exists(inpath):
            self.status['text'] = 'Specified input file does not exist'
            return
        if not outpath:
            self.status['text'] = 'Output file not specified'
            return
        if inpath == outpath:
            self.status['text'] = 'Must have different input and output files'
            return
        argv = [sys.argv[0], keypath, inpath, outpath]
        self.status['text'] = 'Decrypting...'
        try:
            cli_main(argv)
        except Exception, e:
            self.status['text'] = 'Error: ' + str(e)
            return
        self.status['text'] = 'File successfully decrypted'


def decryptBook(keypath, inpath, outpath):
    with open(keypath, 'rb') as f:
        keyb64 = f.read()
    key = keyb64.decode('base64')[:16]
    # aes = AES.new(key, AES.MODE_CBC, '\x00'*16)
    aes = AES(key)

    with closing(ZipFile(open(inpath, 'rb'))) as inf:
        namelist = set(inf.namelist())
        if 'META-INF/rights.xml' not in namelist or \
           'META-INF/encryption.xml' not in namelist:
            raise IGNOBLEError('%s: not an B&N ADEPT EPUB' % (inpath,))
        for name in META_NAMES:
            namelist.remove(name)
        rights = etree.fromstring(inf.read('META-INF/rights.xml'))
        adept = lambda tag: '{%s}%s' % (NSMAP['adept'], tag)
        expr = './/%s' % (adept('encryptedKey'),)
        bookkey = ''.join(rights.findtext(expr))
        bookkey = aes.decrypt(bookkey.decode('base64'))
        bookkey = bookkey[:-ord(bookkey[-1])]
        encryption = inf.read('META-INF/encryption.xml')
        decryptor = Decryptor(bookkey[-16:], encryption)
        kwds = dict(compression=ZIP_DEFLATED, allowZip64=False)
        with closing(ZipFile(open(outpath, 'wb'), 'w', **kwds)) as outf:
            zi = ZipInfo('mimetype', compress_type=ZIP_STORED)
            outf.writestr(zi, inf.read('mimetype'))
            for path in namelist:
                data = inf.read(path)
                outf.writestr(path, decryptor.decrypt(path, data))
    return 0


def cli_main(argv=sys.argv):
    progname = os.path.basename(argv[0])
    if AES is None:
        print "%s: This script requires OpenSSL or PyCrypto, which must be installed " \
              "separately.  Read the top-of-script comment for details." % \
              (progname,)
        return 1
    if len(argv) != 4:
        print "usage: %s KEYFILE INBOOK OUTBOOK" % (progname,)
        return 1
    keypath, inpath, outpath = argv[1:]
    return decryptBook(keypath, inpath, outpath)


def gui_main():
    root = Tkinter.Tk()
    if AES is None:
        root.withdraw()
        tkMessageBox.showerror(
            "Ignoble EPUB Decrypter",
            "This script requires OpenSSL or PyCrypto, which must be installed "
            "separately.  Read the top-of-script comment for details.")
        return 1
    root.title('Ignoble EPUB Decrypter')
    root.resizable(True, False)
    root.minsize(300, 0)
    DecryptionDialog(root).pack(fill=Tkconstants.X, expand=1)
    root.mainloop()
    return 0


if __name__ == '__main__':
    if len(sys.argv) > 1:
        sys.exit(cli_main())
    sys.exit(gui_main())
