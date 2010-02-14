#! /usr/bin/python

# ineptepub.pyw, version 2

# To run this program install Python 2.6 from http://www.python.org/download/
# and PyCrypto from http://www.voidspace.org.uk/python/modules.shtml#pycrypto
# (make sure to install the version for Python 2.6).  Save this script file as
# ineptepub.pyw and double-click on it to run it.

# Revision history:
#   1 - Initial release
#   2 - Rename to INEPT, fix exit code

"""
Decrypt Adobe ADEPT-encrypted EPUB books.
"""

from __future__ import with_statement

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

try:
    from Crypto.Cipher import AES
    from Crypto.PublicKey import RSA
except ImportError:
    AES = None
    RSA = None

META_NAMES = ('mimetype', 'META-INF/rights.xml', 'META-INF/encryption.xml')
NSMAP = {'adept': 'http://ns.adobe.com/adept',
         'enc': 'http://www.w3.org/2001/04/xmlenc#'}


# ASN.1 parsing code from tlslite

def bytesToNumber(bytes):
    total = 0L
    multiplier = 1L
    for count in range(len(bytes)-1, -1, -1):
        byte = bytes[count]
        total += multiplier * byte
        multiplier *= 256
    return total

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


class ZipInfo(zipfile.ZipInfo):
    def __init__(self, *args, **kwargs):
        if 'compress_type' in kwargs:
            compress_type = kwargs.pop('compress_type')
        super(ZipInfo, self).__init__(*args, **kwargs)
        self.compress_type = compress_type


class Decryptor(object):
    def __init__(self, bookkey, encryption):
        enc = lambda tag: '{%s}%s' % (NSMAP['enc'], tag)
        self._aes = AES.new(bookkey, AES.MODE_CBC)
        encryption = etree.fromstring(encryption)
        self._encrypted = encrypted = set()
        expr = './%s/%s/%s' % (enc('EncryptedData'), enc('CipherData'),
                               enc('CipherReference'))
        for elem in encryption.findall(expr):
            path = elem.get('URI', None)
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


class ADEPTError(Exception):
    pass

def cli_main(argv=sys.argv):
    progname = os.path.basename(argv[0])
    if AES is None:
        print "%s: This script requires PyCrypto, which must be installed " \
              "separately.  Read the top-of-script comment for details." % \
              (progname,)
        return 1
    if len(argv) != 4:
        print "usage: %s KEYFILE INBOOK OUTBOOK" % (progname,)
        return 1
    keypath, inpath, outpath = argv[1:]
    with open(keypath, 'rb') as f:
        keyder = f.read()
    key = ASN1Parser([ord(x) for x in keyder])
    key = [bytesToNumber(key.getChild(x).value) for x in xrange(1, 4)]
    rsa = RSA.construct(key)
    with closing(ZipFile(open(inpath, 'rb'))) as inf:
        namelist = set(inf.namelist())
        if 'META-INF/rights.xml' not in namelist or \
           'META-INF/encryption.xml' not in namelist:
            raise ADEPTError('%s: not an ADEPT EPUB' % (inpath,))
        for name in META_NAMES:
            namelist.remove(name)
        rights = etree.fromstring(inf.read('META-INF/rights.xml'))
        adept = lambda tag: '{%s}%s' % (NSMAP['adept'], tag)
        expr = './/%s' % (adept('encryptedKey'),)
        bookkey = ''.join(rights.findtext(expr))
        bookkey = rsa.decrypt(bookkey.decode('base64'))
        # Padded as per RSAES-PKCS1-v1_5
        if bookkey[-17] != '\x00':
            raise ADEPTError('problem decrypting session key')
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
        if os.path.exists('adeptkey.der'):
            self.keypath.insert(0, 'adeptkey.der')
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
            parent=None, title='Select ADEPT key file',
            defaultextension='.der', filetypes=[('DER-encoded files', '.der'),
                                                ('All Files', '.*')])
        if keypath:
            keypath = os.path.normpath(keypath)
            self.keypath.delete(0, Tkconstants.END)
            self.keypath.insert(0, keypath)
        return

    def get_inpath(self):
        inpath = tkFileDialog.askopenfilename(
            parent=None, title='Select ADEPT-encrypted EPUB file to decrypt',
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

def gui_main():
    root = Tkinter.Tk()
    if AES is None:
        root.withdraw()
        tkMessageBox.showerror(
            "INEPT EPUB Decrypter",
            "This script requires PyCrypto, which must be installed "
            "separately.  Read the top-of-script comment for details.")
        return 1
    root.title('INEPT EPUB Decrypter')
    root.resizable(True, False)
    root.minsize(300, 0)
    DecryptionDialog(root).pack(fill=Tkconstants.X, expand=1)
    root.mainloop()
    return 0

if __name__ == '__main__':
    if len(sys.argv) > 1:
        sys.exit(cli_main())
    sys.exit(gui_main())
