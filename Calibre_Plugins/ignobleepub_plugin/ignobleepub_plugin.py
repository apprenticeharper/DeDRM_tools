#!/usr/bin/env python

# ignobleepub_plugin.py
# Released under the terms of the GNU General Public Licence, version 3 or
# later.  <http://www.gnu.org/licenses/>
#
# Requires Calibre version 0.6.44 or higher.
#
# All credit given to I <3 Cabbages for the original standalone scripts.
# I had the much easier job of converting them to Calibre a plugin.
#
# This plugin is meant to decrypt Barnes & Noble Epubs that are protected
# with Adobe's Adept encryption. It is meant to function without having to install
# any dependencies... other than having Calibre installed, of course. It will still
# work if you have Python and PyCrypto already installed, but they aren't necessary.
#
# Configuration:
# 1) The easiest way to configure the plugin is to enter your name (Barnes & Noble account
# name) and credit card number (the one used to purchase the books) into the plugin's
# customization window. Highlight the plugin (Ignoble Epub DeDRM) and click the
# "Customize Plugin" button on Calibre's Preferences->Plugins page.
# Enter the name and credit card number separated by a comma: Your Name,1234123412341234
#
# If you've purchased books with more than one credit card, separate the info with
# a colon: Your Name,1234123412341234:Other Name,2345234523452345
#
# ** Method 1 is your only option if you don't have/can't run the original
# I <3 Cabbages scripts on your particular machine. **
#
# 2) If you already have keyfiles generated with I <3 Cabbages' ignoblekeygen.pyw
# script, you can put those keyfiles in Calibre's configuration directory. The easiest
# way to find the correct directory is to go to Calibre's Preferences page... click
# on the 'Miscellaneous' button (looks like a gear),  and then click the 'Open Calibre
# configuration directory' button. Paste your keyfiles in there. Just make sure that
# they have different names and are saved with the '.b64' extension (like the ignoblekeygen
# script produces). This directory isn't touched when upgrading Calibre, so it's quite safe
# to leave then there.
#
# All keyfiles from option 2 and all data entered from option 1 will be used to attempt
# to decrypt a book. You can use option 1 or option 2, or a combination of both.
#
#
# Revision history:
#   0.1.0 - Initial release
#   0.1.1 - Allow Windows users to make use of openssl if they have it installed.
#          - Incorporated SomeUpdates zipfix routine.


"""
Decrypt Barnes & Noble ADEPT encrypted EPUB books.
"""

from __future__ import with_statement

__license__ = 'GPL v3'

import sys
import os
import hashlib
import zlib
import zipfile
import re
from zipfile import ZipFile, ZIP_STORED, ZIP_DEFLATED
import xml.etree.ElementTree as etree
from contextlib import closing

global AES
global AES2

META_NAMES = ('mimetype', 'META-INF/rights.xml', 'META-INF/encryption.xml')
NSMAP = {'adept': 'http://ns.adobe.com/adept',
         'enc': 'http://www.w3.org/2001/04/xmlenc#'}

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
    
    AES_set_encrypt_key = F(c_int, 'AES_set_encrypt_key',
                            [c_char_p, c_int, AES_KEY_p])
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
        
    class AES2(object):
         def __init__(self, userkey, iv):
            self._blocksize = len(userkey)
            self._iv = iv
            key = self._key = AES_KEY()
            rv = AES_set_encrypt_key(userkey, len(userkey) * 8, key)
            if rv < 0:
                raise IGNOBLEError('Failed to initialize AES Encrypt key')
    
         def encrypt(self, data):
            out = create_string_buffer(len(data))
            rv = AES_cbc_encrypt(data, out, len(data), self._key, self._iv, 1)
            if rv == 0:
                raise IGNOBLEError('AES encryption failed')
            return out.raw
    print 'IgnobleEpub: Using libcrypto.'
    return (AES, AES2)

def _load_crypto_pycrypto():
    from Crypto.Cipher import AES as _AES

    class AES(object):
        def __init__(self, key):
            self._aes = _AES.new(key, _AES.MODE_CBC)

        def decrypt(self, data):
            return self._aes.decrypt(data)
            
    class AES2(object):
        def __init__(self, key, iv):
            self._aes = _AES.new(key, _AES.MODE_CBC, iv)

        def encrypt(self, data):
            return self._aes.encrypt(data)
    print 'IgnobleEpub: Using PyCrypto.'
    return (AES, AES2)
    
def _load_crypto():
    _aes = _aes2 = None
    for loader in (_load_crypto_libcrypto, _load_crypto_pycrypto):
        try:
            _aes, _aes2 = loader()
            break
        except (ImportError, IGNOBLEError):
            pass
    return (_aes, _aes2)

def normalize_name(name): # Strip spaces and convert to lowercase.
    return ''.join(x for x in name.lower() if x != ' ')

def generate_keyfile(name, ccn):
    name = normalize_name(name) + '\x00'
    ccn = ccn + '\x00'
    name_sha = hashlib.sha1(name).digest()[:16]
    ccn_sha = hashlib.sha1(ccn).digest()[:16]
    both_sha = hashlib.sha1(name + ccn).digest()
    aes = AES2(ccn_sha, name_sha)
    crypt = aes.encrypt(both_sha + ('\x0c' * 0x0c))
    userkey = hashlib.sha1(crypt).digest()

    return userkey.encode('base64')

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
    key = userkey.decode('base64')[:16]
    aes = AES(key)
    
    with closing(ZipFile(open(inpath, 'rb'))) as inf:
        namelist = set(inf.namelist())
        if 'META-INF/rights.xml' not in namelist or \
           'META-INF/encryption.xml' not in namelist:
            return 1
        for name in META_NAMES:
            namelist.remove(name)
        try: # If the generated keyfile doesn't match the bookkey, this is where it's likely to blow up.
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
        except:
            return 2
    return 0

from calibre.customize import FileTypePlugin

class IgnobleDeDRM(FileTypePlugin):
    name                    = 'Ignoble Epub DeDRM'
    description             = 'Removes DRM from secure Barnes & Noble epub files. \
                                Credit given to I <3 Cabbages for the original stand-alone scripts.'
    supported_platforms     = ['linux', 'osx', 'windows']
    author                  = 'DiapDealer'
    version                 = (0, 1, 1)
    minimum_calibre_version = (0, 6, 44)  # Compiled python libraries cannot be imported in earlier versions.
    file_types              = set(['epub'])
    on_import               = True

    def run(self, path_to_ebook):
        global AES
        global AES2
        
        from calibre.gui2 import is_ok_to_use_qt
        from PyQt4.Qt import QMessageBox
        from calibre.constants import iswindows, isosx
        
        # Add the included pycrypto import directory for Windows users.
        pdir = 'windows' if iswindows else 'osx' if isosx else 'linux'
        ppath = os.path.join(self.sys_insertion_path, pdir)
        sys.path.append(ppath)
        
        AES, AES2 = _load_crypto()
        
        if AES == None or AES2 == None:
            # Failed to load libcrypto or PyCrypto... Adobe Epubs can't be decrypted.'
            sys.path.remove(ppath)
            raise IGNOBLEError('IgnobleEpub - Failed to load crypto libs.')
            return

        # Load any keyfiles (*.b64) included Calibre's config directory.
        userkeys = []
        try:
            # Find Calibre's configuration directory.
            confpath = os.path.split(os.path.split(self.plugin_path)[0])[0]
            print 'IgnobleEpub: Calibre configuration directory = %s' % confpath
            files = os.listdir(confpath)
            filefilter = re.compile("\.b64$", re.IGNORECASE)
            files = filter(filefilter.search, files)

            if files:
                for filename in files:
                    fpath = os.path.join(confpath, filename)
                    with open(fpath, 'rb') as f:
                        userkeys.append(f.read())
                    print 'IgnobleEpub: Keyfile %s found in config folder.' % filename
            else:
                print 'IgnobleEpub: No keyfiles found. Checking plugin customization string.'
        except IOError:
            print 'IgnobleEpub: Error reading keyfiles from config directory.'
            pass
        
        # Get name and credit card number from Plugin Customization
        if not userkeys and not self.site_customization:
            # Plugin hasn't been configured... do nothing.
            sys.path.remove(ppath)
            raise IGNOBLEError('IgnobleEpub - No keys found. Plugin not configured.')
            return
        
        if self.site_customization:
            keystuff = self.site_customization
            ar = keystuff.split(':')
            keycount = 0
            for i in ar:
                try:
                    name, ccn = i.split(',')
                    keycount += 1
                except ValueError:
                    sys.path.remove(ppath)
                    raise IGNOBLEError('IgnobleEpub - Error parsing user supplied data.')
                    return
        
                # Generate Barnes & Noble EPUB user key from name and credit card number.
                userkeys.append( generate_keyfile(name, ccn) )
            print 'IgnobleEpub: %d userkey(s) generated from customization data.' % keycount
        
        # Attempt to decrypt epub with each encryption key (generated or provided).
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
        
            # Give the user key, ebook and TemporaryPersistent file to the Stripper function.
            result = plugin_main(userkey, inf.name, of.name)
        
            # Ebook is not a B&N Adept epub... do nothing and pass it on.
            # This allows a non-encrypted epub to be imported without error messages.
            if  result == 1:
                print 'IgnobleEpub: Not a B&N Adept Epub... punting.'
                of.close()
                sys.path.remove(ppath)
                return path_to_ebook
                break
        
            # Decryption was successful return the modified PersistentTemporary
            # file to Calibre's import process.
            if  result == 0:
                print 'IgnobleEpub: Encryption successfully removed.'
                of.close()
                sys.path.remove(ppath)
                return of.name
                break
            
            print 'IgnobleEpub: Encryption key invalid... trying others.'
            of.close()
        
        # Something went wrong with decryption.
        # Import the original unmolested epub.
        of.close
        sys.path.remove(ppath)
        raise IGNOBLEError('IgnobleEpub - Ultimately failed to decrypt.')
        return
        
        
    def customization_help(self, gui=False):
        return 'Enter B&N Account name and CC# (separate name and CC# with a comma)'
