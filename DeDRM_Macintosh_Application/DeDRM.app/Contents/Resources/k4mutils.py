# standlone set of Mac OSX specific routines needed for K4DeDRM

from __future__ import with_statement
import sys
import os
import subprocess


class K4MDrmException(Exception):
    pass


# interface to needed routines in openssl's libcrypto
def _load_crypto_libcrypto():
    from ctypes import CDLL, byref, POINTER, c_void_p, c_char_p, c_int, c_long, \
        Structure, c_ulong, create_string_buffer, addressof, string_at, cast
    from ctypes.util import find_library

    libcrypto = find_library('crypto')
    if libcrypto is None:
        raise K4MDrmException('libcrypto not found')
    libcrypto = CDLL(libcrypto)

    AES_MAXNR = 14
    c_char_pp = POINTER(c_char_p)
    c_int_p = POINTER(c_int)

    class AES_KEY(Structure):
        _fields_ = [('rd_key', c_long * (4 * (AES_MAXNR + 1))), ('rounds', c_int)]
    AES_KEY_p = POINTER(AES_KEY)
    
    def F(restype, name, argtypes):
        func = getattr(libcrypto, name)
        func.restype = restype
        func.argtypes = argtypes
        return func
    
    AES_cbc_encrypt = F(None, 'AES_cbc_encrypt',[c_char_p, c_char_p, c_ulong, AES_KEY_p, c_char_p,c_int])

    AES_set_decrypt_key = F(c_int, 'AES_set_decrypt_key',[c_char_p, c_int, AES_KEY_p])

    PKCS5_PBKDF2_HMAC_SHA1 = F(c_int, 'PKCS5_PBKDF2_HMAC_SHA1', 
                                [c_char_p, c_ulong, c_char_p, c_ulong, c_ulong, c_ulong, c_char_p])
    
    class LibCrypto(object):
        def __init__(self):
            self._blocksize = 0
            self._keyctx = None
            self.iv = 0

        def set_decrypt_key(self, userkey, iv):
            self._blocksize = len(userkey)
            if (self._blocksize != 16) and (self._blocksize != 24) and (self._blocksize != 32) :
                raise K4MDrmException('AES improper key used')
                return
            keyctx = self._keyctx = AES_KEY()
            self.iv = iv
            rv = AES_set_decrypt_key(userkey, len(userkey) * 8, keyctx)
            if rv < 0:
                raise K4MDrmException('Failed to initialize AES key')

        def decrypt(self, data):
            out = create_string_buffer(len(data))
            rv = AES_cbc_encrypt(data, out, len(data), self._keyctx, self.iv, 0)
            if rv == 0:
                raise K4MDrmException('AES decryption failed')
            return out.raw

        def keyivgen(self, passwd):
            salt = '16743'
            saltlen = 5
            passlen = len(passwd)
            iter = 0x3e8
            keylen = 80
            out = create_string_buffer(keylen)
            rv = PKCS5_PBKDF2_HMAC_SHA1(passwd, passlen, salt, saltlen, iter, keylen, out)
            return out.raw
    return LibCrypto

def _load_crypto():
    LibCrypto = None
    try:
        LibCrypto = _load_crypto_libcrypto()
    except (ImportError, K4MDrmException):
        pass
    return LibCrypto

LibCrypto = _load_crypto()

#
# Utility Routines
#


# Various character maps used to decrypt books. Probably supposed to act as obfuscation
charMap1 = "n5Pr6St7Uv8Wx9YzAb0Cd1Ef2Gh3Jk4M"
charMap2 = "ZB0bYyc1xDdW2wEV3Ff7KkPpL8UuGA4gz-Tme9Nn_tHh5SvXCsIiR6rJjQaqlOoM" 
charMap3 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
charMap4 = "ABCDEFGHIJKLMNPQRSTUVWXYZ123456789"



# uses a sub process to get the Hard Drive Serial Number using ioreg
# returns with the serial number of drive whose BSD Name is "disk0"
def GetVolumeSerialNumber():
    sernum = os.getenv('MYSERIALNUMBER')
    if sernum != None:
        return sernum
    cmdline = '/usr/sbin/ioreg -l -S -w 0 -r -c AppleAHCIDiskDriver'
    cmdline = cmdline.encode(sys.getfilesystemencoding())
    p = subprocess.Popen(cmdline, shell=True, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=False)
    out1, out2 = p.communicate()
    reslst = out1.split('\n')
    cnt = len(reslst)
    bsdname = None
    sernum = None
    foundIt = False
    for j in xrange(cnt):
        resline = reslst[j]
        pp = resline.find('"Serial Number" = "')
        if pp >= 0:
            sernum = resline[pp+19:-1]
            sernum = sernum.strip()
        bb = resline.find('"BSD Name" = "')
        if bb >= 0:
            bsdname = resline[bb+14:-1]
            bsdname = bsdname.strip()
            if (bsdname == 'disk0') and (sernum != None):
                foundIt = True
                break
    if not foundIt:
        sernum = '9999999999'
    return sernum

# uses unix env to get username instead of using sysctlbyname 
def GetUserName():
    username = os.getenv('USER')
    return username


def encode(data, map):
    result = ""
    for char in data:
        value = ord(char)
        Q = (value ^ 0x80) // len(map)
        R = value % len(map)
        result += map[Q]
        result += map[R]
    return result

import hashlib

def SHA256(message):
    ctx = hashlib.sha256()
    ctx.update(message)
    return ctx.digest()

# implements an Pseudo Mac Version of Windows built-in Crypto routine
def CryptUnprotectData(encryptedData):
    sp = GetVolumeSerialNumber() + '!@#' + GetUserName()
    passwdData = encode(SHA256(sp),charMap1)
    crp = LibCrypto()
    key_iv = crp.keyivgen(passwdData)
    key = key_iv[0:32]
    iv = key_iv[32:48]
    crp.set_decrypt_key(key,iv)
    cleartext = crp.decrypt(encryptedData)
    return cleartext


# Locate and open the .kindle-info file
def openKindleInfo(kInfoFile=None):
    if kInfoFile == None:
	home = os.getenv('HOME')
	cmdline = 'find "' + home + '/Library/Application Support" -name ".kindle-info"'
	cmdline = cmdline.encode(sys.getfilesystemencoding())
	p1 = subprocess.Popen(cmdline, shell=True, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=False)
        out1, out2 = p1.communicate()
	reslst = out1.split('\n')
	kinfopath = 'NONE'
	cnt = len(reslst)
	for j in xrange(cnt):
	    resline = reslst[j]
	    pp = resline.find('.kindle-info')
	    if pp >= 0:
		kinfopath = resline
		break
	if not os.path.exists(kinfopath):
	    raise K4MDrmException('Error: .kindle-info file can not be found')
	return open(kinfopath,'r')
    else:
        return open(kInfoFile, 'r')
