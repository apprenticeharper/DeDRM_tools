# engine to remove drm from Kindle for Mac books
# for personal use for archiving and converting your ebooks
#  PLEASE DO NOT PIRATE!
# We want all authors and Publishers, and eBook stores to live long and prosperous lives
#
# it borrows heavily from works by CMBDTC, IHeartCabbages, skindle,
#    unswindle, DiapDealer, some_updates and many many others

from __future__ import with_statement

class Unbuffered:
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

import sys
sys.stdout=Unbuffered(sys.stdout)
import os, csv, getopt
from struct import pack
from struct import unpack
import zlib

# for handling sub processes
import subprocess
from subprocess import Popen, PIPE, STDOUT
import subasyncio
from subasyncio import Process


#Exception Handling
class K4MDEDRMError(Exception):
    pass
class K4MDEDRMFatal(Exception):
    pass

#
# crypto routines
#
import hashlib

def MD5(message):
    ctx = hashlib.md5()
    ctx.update(message)
    return ctx.digest()

def SHA1(message):
    ctx = hashlib.sha1()
    ctx.update(message)
    return ctx.digest()

def SHA256(message):
    ctx = hashlib.sha256()
    ctx.update(message)
    return ctx.digest()

# interface to needed routines in openssl's libcrypto
def _load_crypto_libcrypto():
    from ctypes import CDLL, byref, POINTER, c_void_p, c_char_p, c_int, c_long, \
        Structure, c_ulong, create_string_buffer, addressof, string_at, cast
    from ctypes.util import find_library

    libcrypto = find_library('crypto')
    if libcrypto is None:
        raise K4MDEDRMError('libcrypto not found')
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
                raise K4MDEDRMError('AES improper key used')
                return
            keyctx = self._keyctx = AES_KEY()
            self.iv = iv
            rv = AES_set_decrypt_key(userkey, len(userkey) * 8, keyctx)
            if rv < 0:
                raise K4MDEDRMError('Failed to initialize AES key')
        def decrypt(self, data):
            out = create_string_buffer(len(data))
            rv = AES_cbc_encrypt(data, out, len(data), self._keyctx, self.iv, 0)
            if rv == 0:
                raise K4MDEDRMError('AES decryption failed')
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
    except (ImportError, K4MDEDRMError):
        pass
    return LibCrypto

LibCrypto = _load_crypto()

#
# Utility Routines
#

# uses a sub process to get the Hard Drive Serial Number using ioreg
# returns with the first found serial number in that class
def GetVolumeSerialNumber():
    sernum = os.getenv('MYSERIALNUMBER')
    if sernum != None:
        return sernum
    cmdline = '/usr/sbin/ioreg -l -S -w 0 -r -c AppleAHCIDiskDriver'
    cmdline = cmdline.encode(sys.getfilesystemencoding())
    p = Process(cmdline, shell=True, bufsize=1, stdin=None, stdout=PIPE, stderr=PIPE, close_fds=False)
    poll = p.wait('wait')
    results = p.read()
    reslst = results.split('\n')
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

MAX_PATH = 255

#
# start of Kindle specific routines
#

global kindleDatabase

# Various character maps used to decrypt books. Probably supposed to act as obfuscation
charMap1 = "n5Pr6St7Uv8Wx9YzAb0Cd1Ef2Gh3Jk4M"
charMap2 = "ZB0bYyc1xDdW2wEV3Ff7KkPpL8UuGA4gz-Tme9Nn_tHh5SvXCsIiR6rJjQaqlOoM"
charMap3 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
charMap4 = "ABCDEFGHIJKLMNPQRSTUVWXYZ123456789"

# Encode the bytes in data with the characters in map
def encode(data, map):
    result = ""
    for char in data:
        value = ord(char)
        Q = (value ^ 0x80) // len(map)
        R = value % len(map)
        result += map[Q]
        result += map[R]
    return result

# Hash the bytes in data and then encode the digest with the characters in map
def encodeHash(data,map):
    return encode(MD5(data),map)

# Decode the string in data with the characters in map. Returns the decoded bytes
def decode(data,map):
    result = ""
    for i in range (0,len(data)-1,2):
        high = map.find(data[i])
        low = map.find(data[i+1])
        if (high == -1) or (low == -1) :
            break
        value = (((high * len(map)) ^ 0x80) & 0xFF) + low
        result += pack("B",value)
    return result

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
def openKindleInfo():
    home = os.getenv('HOME')
    kinfopath = home +  '/Library/Application Support/Amazon/Kindle/storage/.kindle-info'
    if not os.path.exists(kinfopath):
        kinfopath = home +  '/Library/Application Support/Amazon/Kindle for Mac/storage/.kindle-info'
        if not os.path.exists(kinfopath):
            raise K4MDEDRMError('Error: .kindle-info file can not be found')
    return open(kinfopath,'r')

# Parse the Kindle.info file and return the records as a list of key-values
def parseKindleInfo():
    DB = {}
    infoReader = openKindleInfo()
    infoReader.read(1)
    data = infoReader.read()
    items = data.split('[')
    for item in items:
        splito = item.split(':')
        DB[splito[0]] =splito[1]
    return DB

# Get a record from the Kindle.info file for the key "hashedKey" (already hashed and encoded). Return the decoded and decrypted record
def getKindleInfoValueForHash(hashedKey):
    global kindleDatabase
    encryptedValue = decode(kindleDatabase[hashedKey],charMap2)
    cleartext = CryptUnprotectData(encryptedValue)
    return decode(cleartext, charMap1)

#  Get a record from the Kindle.info file for the string in "key" (plaintext). Return the decoded and decrypted record
def getKindleInfoValueForKey(key):
    return getKindleInfoValueForHash(encodeHash(key,charMap2))

# Find if the original string for a hashed/encoded string is known. If so return the original string othwise return an empty string.
def findNameForHash(hash):
    names = ["kindle.account.tokens","kindle.cookie.item","eulaVersionAccepted","login_date","kindle.token.item","login","kindle.key.item","kindle.name.info","kindle.device.info", "MazamaRandomNumber"]
    result = ""
    for name in names:
        if hash == encodeHash(name, charMap2):
            result = name
            break
    return result

# Print all the records from the kindle.info file (option -i)
def printKindleInfo():
    for record in kindleDatabase:
        name = findNameForHash(record)
        if name != "" :
            print (name)
            print ("--------------------------")
        else :
            print ("Unknown Record")
        print getKindleInfoValueForHash(record)
        print "\n"

#
# PID generation routines
#

# Returns two bit at offset from a bit field
def getTwoBitsFromBitField(bitField,offset):
    byteNumber = offset // 4
    bitPosition = 6 - 2*(offset % 4)
    return ord(bitField[byteNumber]) >> bitPosition & 3

# Returns the six bits at offset from a bit field
def getSixBitsFromBitField(bitField,offset):
    offset *= 3
    value = (getTwoBitsFromBitField(bitField,offset) <<4) + (getTwoBitsFromBitField(bitField,offset+1) << 2) +getTwoBitsFromBitField(bitField,offset+2)
    return value

# 8 bits to six bits encoding from hash to generate PID string
def encodePID(hash):
    global charMap3
    PID = ""
    for position in range (0,8):
        PID += charMap3[getSixBitsFromBitField(hash,position)]
    return PID


#
# Main
#

def main(argv=sys.argv):
    global kindleDatabase

    kindleDatabase = None

    #
    # Read the encrypted database
    #

    try:
        kindleDatabase = parseKindleInfo()
    except Exception, message:
        print(message)

    if kindleDatabase != None :
        printKindleInfo()

    return 0

if __name__ == '__main__':
    sys.exit(main())
