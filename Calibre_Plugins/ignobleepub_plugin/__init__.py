#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
# -*- coding: utf-8 -*-

from __future__ import with_statement
__license__   = 'GPL v3'
__docformat__ = 'restructuredtext en'


# Released under the terms of the GNU General Public Licence, version 3 or
# later.  <http://www.gnu.org/licenses/>
#
# Requires Calibre version 0.7.55 or higher.
#
# All credit given to I ♥ Cabbages for the original standalone scripts.
# I had the much easier job of converting them to Calibre a plugin.
#
# This plugin is meant to decrypt Barnes & Noble Epubs that are protected
# with a version of Adobe's Adept encryption. It is meant to function without having to
# install any dependencies... other than having Calibre installed, of course. It will still
# work if you have Python and PyCrypto already installed, but they aren't necessary.
#
# Configuration:
# Check out the plugin's configuration settings by clicking the "Customize plugin"
# button when you have the "BnN ePub DeDRM" plugin highlighted (under Preferences->
# Plugins->File type plugins). Once you have the configuration dialog open, you'll
# see a Help link on the top right-hand side.
#
# Revision history:
#   0.1.0 - Initial release
#   0.1.1 - Allow Windows users to make use of openssl if they have it installed.
#          - Incorporated SomeUpdates zipfix routine.
#   0.1.2 - bug fix for non-ascii file names in encryption.xml
#   0.1.3 - Try PyCrypto on Windows first
#   0.1.4 - update zipfix to deal with mimetype not in correct place
#   0.1.5 - update zipfix to deal with completely missing mimetype files
#   0.1.6 - update for the new calibre plugin interface
#   0.1.7 - Fix for potential problem with PyCrypto
#   0.1.8 - an updated/modified zipfix.py and included zipfilerugged.py
#   0.2.0 - Completely overhauled plugin configuration dialog and key management/storage
#   0.2.1 - an updated/modified zipfix.py and included zipfilerugged.py
#   0.2.2 - added in potential fixes from 0.1.7 that had been missed.
#   0.2.3 - fixed possible output/unicode problem
#   0.2.4 - ditched nearly hopeless caselessStrCmp method in favor of uStrCmp.
#         - added ability to rename existing keys.

"""
Decrypt Barnes & Noble ADEPT encrypted EPUB books.
"""

PLUGIN_NAME = 'Ignoble Epub DeDRM'
PLUGIN_VERSION_TUPLE = (0, 2, 4)
PLUGIN_VERSION = '.'.join([str(x) for x in PLUGIN_VERSION_TUPLE])
# Include an html helpfile in the plugin's zipfile with the following name.
RESOURCE_NAME = PLUGIN_NAME + '_Help.htm'

import sys, os, zlib, re
from zipfile import ZipFile, ZIP_STORED, ZIP_DEFLATED
from zipfile import ZipInfo as _ZipInfo
#from lxml import etree
try:
    import xml.etree.cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree
from contextlib import closing

global AES

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
        raise IGNOBLEError('%s Plugin v%s: libcrypto not found' % (PLUGIN_NAME, PLUGIN_VERSION))
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
                raise IGNOBLEError('%s Plugin v%s: AES improper key used' % (PLUGIN_NAME, PLUGIN_VERSION))
                return
            key = self._key = AES_KEY()
            rv = AES_set_decrypt_key(userkey, len(userkey) * 8, key)
            if rv < 0:
                raise IGNOBLEError('%s Plugin v%s: Failed to initialize AES key' % (PLUGIN_NAME, PLUGIN_VERSION))
    
        def decrypt(self, data):
            out = create_string_buffer(len(data))
            iv = ("\x00" * self._blocksize)
            rv = AES_cbc_encrypt(data, out, len(data), self._key, iv, 0)
            if rv == 0:
                raise IGNOBLEError('%s Plugin v%s: AES decryption failed' % (PLUGIN_NAME, PLUGIN_VERSION))
            return out.raw
        
    print '%s Plugin v%s: Using libcrypto.' %(PLUGIN_NAME, PLUGIN_VERSION)
    return AES

def _load_crypto_pycrypto():
    from Crypto.Cipher import AES as _AES

    class AES(object):
        def __init__(self, key):
            self._aes = _AES.new(key, _AES.MODE_CBC, '\x00'*16)

        def decrypt(self, data):
            return self._aes.decrypt(data)
            
    print '%s Plugin v%s: Using PyCrypto.' %(PLUGIN_NAME, PLUGIN_VERSION)
    return AES
    
def _load_crypto():
    _aes = None
    cryptolist = (_load_crypto_libcrypto, _load_crypto_pycrypto)
    if sys.platform.startswith('win'):
        cryptolist = (_load_crypto_pycrypto, _load_crypto_libcrypto)
    for loader in cryptolist:
        try:
            _aes = loader()
            break
        except (ImportError, IGNOBLEError):
            pass
    return _aes

class ZipInfo(_ZipInfo):
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
    key = userkey.decode('base64')[:16]
    aes = AES(key)
    
    with closing(ZipFile(open(inpath, 'rb'))) as inf:
        namelist = set(inf.namelist())
        if 'META-INF/rights.xml' not in namelist or 'META-INF/encryption.xml' not in namelist:
            print '%s Plugin: Not Encrypted.' % PLUGIN_NAME
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
from calibre.gui2 import is_ok_to_use_qt

class IgnobleDeDRM(FileTypePlugin):
    name                    = PLUGIN_NAME
    description             = 'Removes DRM from secure Barnes & Noble epub files. Credit given to I ♥ Cabbages for the original stand-alone scripts.'
    supported_platforms     = ['linux', 'osx', 'windows']
    author                  = 'DiapDealer'
    version                 = PLUGIN_VERSION_TUPLE
    minimum_calibre_version = (0, 7, 55)  # Compiled python libraries cannot be imported in earlier versions.
    file_types              = set(['epub'])
    on_import               = True
    
    def run(self, path_to_ebook):
        from calibre_plugins.ignoble_epub import outputfix
         
        if sys.stdout.encoding == None:
            sys.stdout = outputfix.getwriter('utf-8')(sys.stdout)
        else:
            sys.stdout = outputfix.getwriter(sys.stdout.encoding)(sys.stdout)
        if sys.stderr.encoding == None:
            sys.stderr = outputfix.getwriter('utf-8')(sys.stderr)
        else:
            sys.stderr = outputfix.getwriter(sys.stderr.encoding)(sys.stderr)
            
        global AES

        print '\n\nRunning {0} v{1} on "{2}"'.format(PLUGIN_NAME, PLUGIN_VERSION, os.path.basename(path_to_ebook))
        AES = _load_crypto()
        if AES == None:
            # Failed to load libcrypto or PyCrypto... Adobe Epubs can't be decrypted.'
            raise Exception('%s Plugin v%s: Failed to load crypto libs.' % (PLUGIN_NAME, PLUGIN_VERSION))

        # First time use or first time after upgrade to new key-handling/storage method
        # or no keys configured. Give a visual prompt to configure.
        import calibre_plugins.ignoble_epub.config as cfg
        if not cfg.prefs['configured']:
            titlemsg = '%s v%s' % (PLUGIN_NAME, PLUGIN_VERSION)
            errmsg = titlemsg + ' not (properly) configured!\n' + \
                    '\nThis may be the first time you\'ve used this plugin' + \
                    ' (or the first time since upgrading this plugin).' + \
                    ' You\'ll need to open the customization dialog (Preferences->Plugins->File type plugins)' + \
                    ' and follow the instructions there.\n' + \
                    '\nIf you don\'t use the ' + PLUGIN_NAME + ' plugin, you should disable or uninstall it.'
            if is_ok_to_use_qt():
                from PyQt4.Qt import QMessageBox
                d = QMessageBox(QMessageBox.Warning, titlemsg, errmsg )
                d.show()
                d.raise_()
                d.exec_()
            raise Exception('%s Plugin v%s: Plugin not configured.' % (PLUGIN_NAME, PLUGIN_VERSION))

        # Check original epub archive for zip errors.
        from calibre_plugins.ignoble_epub import zipfix
        inf = self.temporary_file('.epub')
        try:
            print '%s Plugin: Verifying zip archive integrity.' % PLUGIN_NAME
            fr = zipfix.fixZip(path_to_ebook, inf.name)
            fr.fix()
        except Exception, e:
            print '%s Plugin: unforeseen zip archive issue.' % PLUGIN_NAME
            raise Exception(e)
        # Create a TemporaryPersistent file to work with.
        of = self.temporary_file('.epub')
        
        # Attempt to decrypt epub with each encryption key (generated or provided).
        key_counter = 1
        for keyname, userkey in cfg.prefs['keys'].items():
            keyname_masked = keyname[:4] + ''.join('x' for x in keyname[4:]) 
            # Give the user key, ebook and TemporaryPersistent file to the Stripper function.
            result = plugin_main(userkey, inf.name, of.name)

            # Ebook is not a B&N Adept epub... do nothing and pass it on.
            # This allows a non-encrypted epub to be imported without error messages.
            if  result == 1:
                print '%s Plugin: Not a B&N Epub - doing nothing.\n' % PLUGIN_NAME
                of.close()
                return path_to_ebook
                break

            # Decryption was successful return the modified PersistentTemporary
            # file to Calibre's import process.
            if  result == 0:
                print '{0} Plugin: Encryption key {1} ("{2}") correct!'.format(PLUGIN_NAME, key_counter, keyname_masked)
                of.close()
                return of.name
                break

            print '{0} Plugin: Encryption key {1} ("{2}") incorrect!'.format(PLUGIN_NAME, key_counter, keyname_masked)
            key_counter += 1

        # Something went wrong with decryption.
        # Import the original unmolested epub.
        of.close
        raise Exception('%s Plugin v%s: Ultimately failed to decrypt.\n' % (PLUGIN_NAME, PLUGIN_VERSION))

    def is_customizable(self):
        # return true to allow customization via the Plugin->Preferences.
        return True

    def config_widget(self):
        from calibre_plugins.ignoble_epub.config import ConfigWidget
        # Extract the helpfile contents from in the plugin's zipfile.
        # The helpfile must be named <plugin name variable> + '_Help.htm'
        return ConfigWidget(self.load_resources(RESOURCE_NAME)[RESOURCE_NAME])

    def load_resources(self, names):
        ans = {}
        with ZipFile(self.plugin_path, 'r') as zf:
            for candidate in zf.namelist():
                if candidate in names:
                    ans[candidate] = zf.read(candidate)
        return ans

    def save_settings(self, config_widget):
        config_widget.save_settings()
