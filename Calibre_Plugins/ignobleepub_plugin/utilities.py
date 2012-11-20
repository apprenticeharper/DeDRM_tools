#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai

from __future__ import with_statement
__license__ = 'GPL v3'

import hashlib

from ctypes import CDLL, POINTER, c_void_p, c_char_p, c_int, c_long, \
                        Structure, c_ulong, create_string_buffer, cast
from ctypes.util import find_library

from calibre.constants import iswindows
from calibre_plugins.ignoble_epub.__init__ import PLUGIN_NAME, PLUGIN_VERSION

DETAILED_MESSAGE = \
'You have personal information stored in this plugin\'s customization '+ \
'string from a previous version of this plugin.\n\n'+ \
'This new version of the plugin can convert that info '+ \
'into key data that the new plugin can then use (which doesn\'t '+ \
'require personal information to be stored/displayed in an insecure '+ \
'manner like the old plugin did).\n\nIf you choose NOT to migrate this data at this time '+ \
'you will be prompted to save that personal data to a file elsewhere; and you\'ll have '+ \
'to manually re-configure this plugin with your information.\n\nEither way... ' + \
'this new version of the plugin will not be responsible for storing that personal '+ \
'info in plain sight any longer.'

class IGNOBLEError(Exception):
    pass

def normalize_name(name): # Strip spaces and convert to lowercase.
    return ''.join(x for x in name.lower() if x != ' ')

# These are the key ENCRYPTING aes crypto functions
def generate_keyfile(name, ccn):
    # Load the necessary crypto libs.
    AES = _load_crypto()
    name = normalize_name(name) + '\x00'
    ccn = ccn + '\x00'
    name_sha = hashlib.sha1(name).digest()[:16]
    ccn_sha = hashlib.sha1(ccn).digest()[:16]
    both_sha = hashlib.sha1(name + ccn).digest()
    aes = AES(ccn_sha, name_sha)
    crypt = aes.encrypt(both_sha + ('\x0c' * 0x0c))
    userkey = hashlib.sha1(crypt).digest()

    return userkey.encode('base64')

def _load_crypto_libcrypto():
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
    
    AES_set_encrypt_key = F(c_int, 'AES_set_encrypt_key',
                            [c_char_p, c_int, AES_KEY_p])
    AES_cbc_encrypt = F(None, 'AES_cbc_encrypt',
                        [c_char_p, c_char_p, c_ulong, AES_KEY_p, c_char_p,
                         c_int])
    
    class AES(object):
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
    return AES

def _load_crypto_pycrypto():
    from Crypto.Cipher import AES as _AES

    class AES(object):
        def __init__(self, key, iv):
            self._aes = _AES.new(key, _AES.MODE_CBC, iv)

        def encrypt(self, data):
            return self._aes.encrypt(data)
    return AES
    
def _load_crypto():
    _aes = None
    cryptolist = (_load_crypto_libcrypto, _load_crypto_pycrypto)
    if iswindows:
        cryptolist = (_load_crypto_pycrypto, _load_crypto_libcrypto)
    for loader in cryptolist:
        try:
            _aes = loader()
            break
        except (ImportError, IGNOBLEError):
            pass
    return _aes

def uStrCmp (s1, s2, caseless=False):
    import unicodedata as ud
    str1 = s1 if isinstance(s1, unicode) else unicode(s1)
    str2 = s2 if isinstance(s2, unicode) else unicode(s2)
    if caseless:
        return ud.normalize('NFC', str1.lower()) == ud.normalize('NFC', str2.lower())
    else:
        return ud.normalize('NFC', str1) == ud.normalize('NFC', str2)

def parseCustString(keystuff):
    userkeys = []
    ar = keystuff.split(':')
    for i in ar:
        try:
            name, ccn = i.split(',')
        except:
            return False
        # Generate Barnes & Noble EPUB user key from name and credit card number.
        userkeys.append(generate_keyfile(name, ccn))
    return userkeys