#!/usr/bin/env python
# K4PC Windows specific routines

from __future__ import with_statement

import sys, os, re
from struct import pack, unpack, unpack_from

from ctypes import windll, c_char_p, c_wchar_p, c_uint, POINTER, byref, \
    create_unicode_buffer, create_string_buffer, CFUNCTYPE, addressof, \
    string_at, Structure, c_void_p, cast

import _winreg as winreg
MAX_PATH = 255
kernel32 = windll.kernel32
advapi32 = windll.advapi32
crypt32 = windll.crypt32

import traceback

# crypto digestroutines
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

# For K4PC 1.9.X
# use routines in alfcrypto:
#    AES_cbc_encrypt
#    AES_set_decrypt_key
#    PKCS5_PBKDF2_HMAC_SHA1

from alfcrypto import AES_CBC, KeyIVGen

def UnprotectHeaderData(encryptedData):
    passwdData = 'header_key_data'
    salt = 'HEADER.2011'
    iter = 0x80
    keylen = 0x100
    key_iv = KeyIVGen().pbkdf2(passwdData, salt, iter, keylen)
    key = key_iv[0:32]
    iv = key_iv[32:48]
    aes=AES_CBC()
    aes.set_decrypt_key(key, iv)
    cleartext = aes.decrypt(encryptedData)
    return cleartext


# simple primes table (<= n) calculator
def primes(n):
    if n==2: return [2]
    elif n<2: return []
    s=range(3,n+1,2)
    mroot = n ** 0.5
    half=(n+1)/2-1
    i=0
    m=3
    while m <= mroot:
        if s[i]:
            j=(m*m-3)/2
            s[j]=0
            while j<half:
                s[j]=0
                j+=m
        i=i+1
        m=2*i+3
    return [2]+[x for x in s if x]


# Various character maps used to decrypt kindle info values.
# Probably supposed to act as obfuscation
charMap2 = "AaZzB0bYyCc1XxDdW2wEeVv3FfUuG4g-TtHh5SsIiR6rJjQq7KkPpL8lOoMm9Nn_"
charMap5 = "AzB0bYyCeVvaZ3FfUuG4g-TtHh5SsIiR6rJjQq7KkPpL8lOoMm9Nn_c1XxDdW2wE"
# New maps in K4PC 1.9.0
testMap1 = "n5Pr6St7Uv8Wx9YzAb0Cd1Ef2Gh3Jk4M"
testMap6 = "9YzAb0Cd1Ef2n5Pr6St7Uvh3Jk4M8WxG"
testMap8 = "YvaZ3FfUm9Nn_c1XuG4yCAzB0beVg-TtHh5SsIiR6rJjQdW2wEq7KkPpL8lOoMxD"

class DrmException(Exception):
    pass

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


# interface with Windows OS Routines
class DataBlob(Structure):
    _fields_ = [('cbData', c_uint),
                ('pbData', c_void_p)]
DataBlob_p = POINTER(DataBlob)


def GetSystemDirectory():
    GetSystemDirectoryW = kernel32.GetSystemDirectoryW
    GetSystemDirectoryW.argtypes = [c_wchar_p, c_uint]
    GetSystemDirectoryW.restype = c_uint
    def GetSystemDirectory():
        buffer = create_unicode_buffer(MAX_PATH + 1)
        GetSystemDirectoryW(buffer, len(buffer))
        return buffer.value
    return GetSystemDirectory
GetSystemDirectory = GetSystemDirectory()

def GetVolumeSerialNumber():
    GetVolumeInformationW = kernel32.GetVolumeInformationW
    GetVolumeInformationW.argtypes = [c_wchar_p, c_wchar_p, c_uint,
                                      POINTER(c_uint), POINTER(c_uint),
                                      POINTER(c_uint), c_wchar_p, c_uint]
    GetVolumeInformationW.restype = c_uint
    def GetVolumeSerialNumber(path = GetSystemDirectory().split('\\')[0] + '\\'):
        vsn = c_uint(0)
        GetVolumeInformationW(path, None, 0, byref(vsn), None, None, None, 0)
        return str(vsn.value)
    return GetVolumeSerialNumber
GetVolumeSerialNumber = GetVolumeSerialNumber()

def GetIDString():
    vsn = GetVolumeSerialNumber()
    print('Using Volume Serial Number for ID: '+vsn)
    return vsn

def getLastError():
    GetLastError = kernel32.GetLastError
    GetLastError.argtypes = None
    GetLastError.restype = c_uint
    def getLastError():
        return GetLastError()
    return getLastError
getLastError = getLastError()

def GetUserName():
    GetUserNameW = advapi32.GetUserNameW
    GetUserNameW.argtypes = [c_wchar_p, POINTER(c_uint)]
    GetUserNameW.restype = c_uint
    def GetUserName():
        buffer = create_unicode_buffer(2)
        size = c_uint(len(buffer))
        while not GetUserNameW(buffer, byref(size)):
            errcd = getLastError()
            if errcd == 234:
                # bad wine implementation up through wine 1.3.21
                return "AlternateUserName"
            buffer = create_unicode_buffer(len(buffer) * 2)
            size.value = len(buffer)
        return buffer.value.encode('utf-16-le')[::2]
    return GetUserName
GetUserName = GetUserName()

def CryptUnprotectData():
    _CryptUnprotectData = crypt32.CryptUnprotectData
    _CryptUnprotectData.argtypes = [DataBlob_p, c_wchar_p, DataBlob_p,
                                   c_void_p, c_void_p, c_uint, DataBlob_p]
    _CryptUnprotectData.restype = c_uint
    def CryptUnprotectData(indata, entropy, flags):
        indatab = create_string_buffer(indata)
        indata = DataBlob(len(indata), cast(indatab, c_void_p))
        entropyb = create_string_buffer(entropy)
        entropy = DataBlob(len(entropy), cast(entropyb, c_void_p))
        outdata = DataBlob()
        if not _CryptUnprotectData(byref(indata), None, byref(entropy),
                                   None, None, flags, byref(outdata)):
            # raise DrmException("Failed to Unprotect Data")
            return 'failed'
        return string_at(outdata.pbData, outdata.cbData)
    return CryptUnprotectData
CryptUnprotectData = CryptUnprotectData()


# Locate all of the kindle-info style files and return as list
def getKindleInfoFiles():
    kInfoFiles = []
    # some 64 bit machines do not have the proper registry key for some reason
    # or the pythonn interface to the 32 vs 64 bit registry is broken
    path = ""
    if 'LOCALAPPDATA' in os.environ.keys():
        path = os.environ['LOCALAPPDATA']
    else:
        # User Shell Folders show take precedent over Shell Folders if present
        try:
            regkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\User Shell Folders\\")
            path = winreg.QueryValueEx(regkey, 'Local AppData')[0]
            if not os.path.isdir(path):
                path = ""
                try:
                    regkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Folders\\")
                    path = winreg.QueryValueEx(regkey, 'Local AppData')[0]
                    if not os.path.isdir(path):
                        path = ""
                except RegError:
                    pass
        except RegError:
            pass

    found = False
    if path == "":
        print ('Could not find the folder in which to look for kinfoFiles.')
    else:
        print('searching for kinfoFiles in ' + path)

        # first look for older kindle-info files
        kinfopath = path +'\\Amazon\\Kindle For PC\\{AMAwzsaPaaZAzmZzZQzgZCAkZ3AjA_AY}\\kindle.info'
        if os.path.isfile(kinfopath):
            found = True
            print('Found K4PC kindle.info file: ' + kinfopath)
            kInfoFiles.append(kinfopath)

        # now look for newer (K4PC 1.5.0 and later rainier.2.1.1.kinf file

        kinfopath = path +'\\Amazon\\Kindle For PC\\storage\\rainier.2.1.1.kinf'
        if os.path.isfile(kinfopath):
            found = True
            print('Found K4PC 1.5.X kinf file: ' + kinfopath)
            kInfoFiles.append(kinfopath)

        # now look for even newer (K4PC 1.6.0 and later) rainier.2.1.1.kinf file
        kinfopath = path +'\\Amazon\\Kindle\\storage\\rainier.2.1.1.kinf'
        if os.path.isfile(kinfopath):
            found = True
            print('Found K4PC 1.6.X kinf file: ' + kinfopath)
            kInfoFiles.append(kinfopath)

        # now look for even newer (K4PC 1.9.0 and later) .kinf2011 file
        kinfopath = path +'\\Amazon\\Kindle\\storage\\.kinf2011'
        if os.path.isfile(kinfopath):
            found = True
            print('Found K4PC kinf2011 file: ' + kinfopath)
            kInfoFiles.append(kinfopath)

    if not found:
        print('No K4PC kindle.info/kinf/kinf2011 files have been found.')
    return kInfoFiles


# determine type of kindle info provided and return a
# database of keynames and values
def getDBfromFile(kInfoFile):
    names = ["kindle.account.tokens","kindle.cookie.item","eulaVersionAccepted","login_date","kindle.token.item","login","kindle.key.item","kindle.name.info","kindle.device.info", "MazamaRandomNumber", "max_date", "SIGVERIF"]
    DB = {}
    cnt = 0
    infoReader = open(kInfoFile, 'r')
    hdr = infoReader.read(1)
    data = infoReader.read()

    if data.find('{') != -1 :

        # older style kindle-info file
        items = data.split('{')
        for item in items:
            if item != '':
                keyhash, rawdata = item.split(':')
                keyname = "unknown"
                for name in names:
                    if encodeHash(name,charMap2) == keyhash:
                        keyname = name
                        break
                if keyname == "unknown":
                    keyname = keyhash
                encryptedValue = decode(rawdata,charMap2)
                DB[keyname] = CryptUnprotectData(encryptedValue, "", 0)
                cnt = cnt + 1
        if cnt == 0:
            DB = None
        return DB

    if hdr == '/':
        # else rainier-2-1-1 .kinf file
        # the .kinf file uses "/" to separate it into records
        # so remove the trailing "/" to make it easy to use split
        data = data[:-1]
        items = data.split('/')

        # loop through the item records until all are processed
        while len(items) > 0:

            # get the first item record
            item = items.pop(0)

            # the first 32 chars of the first record of a group
            # is the MD5 hash of the key name encoded by charMap5
            keyhash = item[0:32]

            # the raw keyhash string is used to create entropy for the actual
            # CryptProtectData Blob that represents that keys contents
            entropy = SHA1(keyhash)

            # the remainder of the first record when decoded with charMap5
            # has the ':' split char followed by the string representation
            # of the number of records that follow
            # and make up the contents
            srcnt = decode(item[34:],charMap5)
            rcnt = int(srcnt)

            # read and store in rcnt records of data
            # that make up the contents value
            edlst = []
            for i in xrange(rcnt):
                item = items.pop(0)
                edlst.append(item)

            keyname = "unknown"
            for name in names:
                if encodeHash(name,charMap5) == keyhash:
                    keyname = name
                    break
            if keyname == "unknown":
                keyname = keyhash
            # the charMap5 encoded contents data has had a length
            # of chars (always odd) cut off of the front and moved
            # to the end to prevent decoding using charMap5 from
            # working properly, and thereby preventing the ensuing
            # CryptUnprotectData call from succeeding.

            # The offset into the charMap5 encoded contents seems to be:
            # len(contents)-largest prime number <=  int(len(content)/3)
            # (in other words split "about" 2/3rds of the way through)

            # move first offsets chars to end to align for decode by charMap5
            encdata = "".join(edlst)
            contlen = len(encdata)
            noffset = contlen - primes(int(contlen/3))[-1]

            # now properly split and recombine
            # by moving noffset chars from the start of the
            # string to the end of the string
            pfx = encdata[0:noffset]
            encdata = encdata[noffset:]
            encdata = encdata + pfx

            # decode using Map5 to get the CryptProtect Data
            encryptedValue = decode(encdata,charMap5)
            DB[keyname] = CryptUnprotectData(encryptedValue, entropy, 1)
            cnt = cnt + 1

        if cnt == 0:
            DB = None
        return DB

    # else newest .kinf2011 style .kinf file
    # the .kinf file uses "/" to separate it into records
    # so remove the trailing "/" to make it easy to use split
    # need to put back the first char read because it it part
    # of the added entropy blob
    data = hdr + data[:-1]
    items = data.split('/')

    # starts with and encoded and encrypted header blob
    headerblob = items.pop(0)
    encryptedValue = decode(headerblob, testMap1)
    cleartext = UnprotectHeaderData(encryptedValue)
    # now extract the pieces that form the added entropy
    pattern = re.compile(r'''\[Version:(\d+)\]\[Build:(\d+)\]\[Cksum:([^\]]+)\]\[Guid:([\{\}a-z0-9\-]+)\]''', re.IGNORECASE)
    for m in re.finditer(pattern, cleartext):
        added_entropy = m.group(2) + m.group(4)


    # loop through the item records until all are processed
    while len(items) > 0:

        # get the first item record
        item = items.pop(0)

        # the first 32 chars of the first record of a group
        # is the MD5 hash of the key name encoded by charMap5
        keyhash = item[0:32]

        # the sha1 of raw keyhash string is used to create entropy along
        # with the added entropy provided above from the headerblob
        entropy = SHA1(keyhash) + added_entropy

        # the remainder of the first record when decoded with charMap5
        # has the ':' split char followed by the string representation
        # of the number of records that follow
        # and make up the contents
        srcnt = decode(item[34:],charMap5)
        rcnt = int(srcnt)

        # read and store in rcnt records of data
        # that make up the contents value
        edlst = []
        for i in xrange(rcnt):
            item = items.pop(0)
            edlst.append(item)

        # key names now use the new testMap8 encoding
        keyname = "unknown"
        for name in names:
            if encodeHash(name,testMap8) == keyhash:
                keyname = name
                break

        # the testMap8 encoded contents data has had a length
        # of chars (always odd) cut off of the front and moved
        # to the end to prevent decoding using testMap8 from
        # working properly, and thereby preventing the ensuing
        # CryptUnprotectData call from succeeding.

        # The offset into the testMap8 encoded contents seems to be:
        # len(contents)-largest prime number <=  int(len(content)/3)
        # (in other words split "about" 2/3rds of the way through)

        # move first offsets chars to end to align for decode by testMap8
        # by moving noffset chars from the start of the
        # string to the end of the string
        encdata = "".join(edlst)
        contlen = len(encdata)
        noffset = contlen - primes(int(contlen/3))[-1]
        pfx = encdata[0:noffset]
        encdata = encdata[noffset:]
        encdata = encdata + pfx

        # decode using new testMap8 to get the original CryptProtect Data
        encryptedValue = decode(encdata,testMap8)
        cleartext = CryptUnprotectData(encryptedValue, entropy, 1)
        DB[keyname] = cleartext
        cnt = cnt + 1

    if cnt == 0:
        DB = None
    return DB
