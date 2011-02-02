#! /usr/bin/python

# ineptepub_plugin.py
# Released under the terms of the GNU General Public Licence, version 3 or
# later.  <http://www.gnu.org/licenses/>
#
# Requires Calibre version 0.6.44 or higher.
#
# All credit given to I <3 Cabbages for the original standalone scripts.
# I had the much easier job of converting them to a Calibre plugin.
#
# This plugin is meant to decrypt Adobe Digital Edition Epubs that are protected
# with Adobe's Adept encryption. It is meant to function without having to install
# any dependencies... other than having Calibre installed, of course. It will still
# work if you have Python and PyCrypto already installed, but they aren't necessary.
#
# Configuration:
# When first run, the plugin will attempt to find your Adobe Digital Editions installation
# (on Windows and Mac OS's). If successful, it will create an 'adeptkey.der' file and
# save it in Calibre's configuration directory. It will use that file on subsequent runs.
# If there are already '*.der' files in the directory, the plugin won't attempt to
# find the ADE installation. So if you have ADE installed on the same machine as Calibre...
# you are ready to go.
#
# If you already have keyfiles generated with I <3 Cabbages' ineptkey.pyw script,
# you can put those keyfiles in Calibre's configuration directory. The easiest
# way to find the correct directory is to go to Calibre's Preferences page... click
# on the 'Miscellaneous' button (looks like a gear),  and then click the 'Open Calibre
# configuration directory' button. Paste your keyfiles in there. Just make sure that
# they have different names and are saved with the '.der' extension (like the ineptkey
# script produces). This directory isn't touched when upgrading Calibre, so it's quite
# safe to leave them there.
#
# Since there is no Linux version of Adobe Digital Editions, Linux users will have to
# obtain a keyfile through other methods and put the file in Calibre's configuration directory.
#
# All keyfiles with a '.der' extension found in Calibre's configuration directory will
# be used to attempt to decrypt a book.
#
# ** NOTE ** There is no plugin customization data for the Inept Epub DeDRM plugin.
#
# Revision history:
#   0.1 - Initial release
#   0.1.1 - Allow Windows users to make use of openssl if they have it installed.
#         - Incorporated SomeUpdates zipfix routine.
#   0.1.2 - Removed Carbon dependency for Mac users. Fixes an issue that was a
#           result of Calibre changing to python 2.7.
#   0.1.3 - bug fix for epubs with non-ascii chars in file names
#   0.1.4 - default to try PyCrypto first on Windows


"""
Decrypt Adobe ADEPT-encrypted EPUB books.
"""

from __future__ import with_statement

__license__ = 'GPL v3'

import sys
import os
import zlib
import zipfile
import re
from zipfile import ZipFile, ZIP_STORED, ZIP_DEFLATED
from contextlib import closing
import xml.etree.ElementTree as etree

global AES
global RSA

META_NAMES = ('mimetype', 'META-INF/rights.xml', 'META-INF/encryption.xml')
NSMAP = {'adept': 'http://ns.adobe.com/adept',
         'enc': 'http://www.w3.org/2001/04/xmlenc#'}


class ADEPTError(Exception):
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
            iv = ("\x00" * self._blocksize)
            rv = AES_cbc_encrypt(data, out, len(data), self._key, iv, 0)
            if rv == 0:
                raise ADEPTError('AES decryption failed')
            return out.raw
    print 'IneptEpub: Using libcrypto.'
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
            self._aes = _AES.new(key, _AES.MODE_CBC)

        def decrypt(self, data):
            return self._aes.decrypt(data)

    class RSA(object):
        def __init__(self, der):
            key = ASN1Parser([ord(x) for x in der])
            key = [key.getChild(x).value for x in xrange(1, 4)]
            key = [self.bytesToNumber(v) for v in key]
            self._rsa = _RSA.construct(key)

        def bytesToNumber(self, bytes):
            total = 0L
            for byte in bytes:
                total = (total << 8) + byte
            return total
    
        def decrypt(self, data):
            return self._rsa.decrypt(data)
    print 'IneptEpub: Using pycrypto.'
    return (AES, RSA)

def _load_crypto():
    _aes = _rsa = None
    cryptolist = (_load_crypto_libcrypto, _load_crypto_pycrypto)
    if sys.platform.startswith('win'):
        cryptolist = (_load_crypto_pycrypto, _load_crypto_libcrypto)
    for loader in cryptolist:
        try:
            _aes, _rsa = loader()
            break
        except (ImportError, ADEPTError):
            pass
    return (_aes, _rsa)
    
class ZipInfo(zipfile.ZipInfo):
    def __init__(self, *args, **kwargs):
        if 'compress_type' in kwargs:
            compress_type = kwargs.pop('compress_type')
        super(ZipInfo, self).__init__(*args, **kwargs)
        self.compress_type = compress_type

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

def plugin_main(userkey, inpath, outpath):
    rsa = RSA(userkey)
    with closing(ZipFile(open(inpath, 'rb'))) as inf:
        namelist = set(inf.namelist())
        if 'META-INF/rights.xml' not in namelist or \
           'META-INF/encryption.xml' not in namelist:
            return 1
        for name in META_NAMES:
            namelist.remove(name)
        try:
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
        except:
            return 2
    return 0

from calibre.customize import FileTypePlugin

class IneptDeDRM(FileTypePlugin):
    name                    = 'Inept Epub DeDRM'
    description             = 'Removes DRM from secure Adobe epub files. \
                                Credit given to I <3 Cabbages for the original stand-alone scripts.'
    supported_platforms     = ['linux', 'osx', 'windows']
    author                  = 'DiapDealer'
    version                 = (0, 1, 5)
    minimum_calibre_version = (0, 6, 44)  # Compiled python libraries cannot be imported in earlier versions.
    file_types              = set(['epub'])
    on_import               = True
    priority                = 100
    
    def run(self, path_to_ebook):
        global AES
        global RSA
        
        from calibre.gui2 import is_ok_to_use_qt
        from PyQt4.Qt import QMessageBox
        from calibre.constants import iswindows, isosx
        
        AES, RSA = _load_crypto()
        
        if AES == None or RSA == None:
            # Failed to load libcrypto or PyCrypto... Adobe Epubs can\'t be decrypted.'
            raise ADEPTError('IneptEpub: Failed to load crypto libs... Adobe Epubs can\'t be decrypted.')
            return
        
        # Load any keyfiles (*.der) included Calibre's config directory.
        userkeys = []

        # Find Calibre's configuration directory.
        confpath = os.path.split(os.path.split(self.plugin_path)[0])[0]
        print 'IneptEpub: Calibre configuration directory = %s' % confpath
        files = os.listdir(confpath)
        filefilter = re.compile("\.der$", re.IGNORECASE)
        files = filter(filefilter.search, files)

        if files:
            try:
                for filename in files:
                    fpath = os.path.join(confpath, filename)
                    with open(fpath, 'rb') as f:
                        userkeys.append(f.read())
                    print 'IneptEpub: Keyfile %s found in config folder.' % filename
            except IOError:
                print 'IneptEpub: Error reading keyfiles from config directory.'
                pass
        else:
            # Try to find key from ADE install and save the key in
            # Calibre's configuration directory for future use.
            if iswindows or isosx:
                # ADE key retrieval script included in respective OS folder.
                from ade_key import retrieve_key
                try:
                    keydata = retrieve_key()
                    userkeys.append(keydata)
                    keypath = os.path.join(confpath, 'calibre-adeptkey.der')
                    with open(keypath, 'wb') as f:
                        f.write(keydata)
                    print 'IneptEpub: Created keyfile from ADE install.'    
                except:
                    print 'IneptEpub: Couldn\'t Retrieve key from ADE install.'
                    pass

        if not userkeys:
            # No user keys found... bail out.
            raise ADEPTError('IneptEpub - No keys found. Check keyfile(s)/ADE install')
            return
        
        # Attempt to decrypt epub with each encryption key found.
        for userkey in userkeys:
            # Create a TemporaryPersistent file to work with.
            # Check original epub archive for zip errors.
            import zipfix
            inf = self.temporary_file('.epub')
            try:
                fr = zipfix.fixZip(path_to_ebook, inf.name)
                fr.fix()
            except Exception, e:
                raise Exception(e)
                return
            of = self.temporary_file('.epub')
        
            # Give the user key, ebook and TemporaryPersistent file to the plugin_main function.
            result = plugin_main(userkey, inf.name, of.name)
        
            # Ebook is not an Adobe Adept epub... do nothing and pass it on.
            # This allows a non-encrypted epub to be imported without error messages.
            if  result == 1:
                print 'IneptEpub: Not an Adobe Adept Epub... punting.'
                of.close()
                return path_to_ebook
                break
        
            # Decryption was successful return the modified PersistentTemporary
            # file to Calibre's import process.
            if  result == 0:
                print 'IneptEpub: Encryption successfully removed.'
                of.close
                return of.name
                break
            
            print 'IneptEpub: Encryption key invalid... trying others.'
            of.close()
        
        # Something went wrong with decryption.
        # Import the original unmolested epub.
        of.close
        raise ADEPTError('IneptEpub - Ultimately failed to decrypt')
        return

