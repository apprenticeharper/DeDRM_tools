# standlone set of Mac OSX specific routines needed for KindleBooks

from __future__ import with_statement

import sys
import os
import os.path

import subprocess
from struct import pack, unpack, unpack_from

class DrmException(Exception):
    pass


# interface to needed routines in openssl's libcrypto
def _load_crypto_libcrypto():
    from ctypes import CDLL, byref, POINTER, c_void_p, c_char_p, c_int, c_long, \
        Structure, c_ulong, create_string_buffer, addressof, string_at, cast
    from ctypes.util import find_library

    libcrypto = find_library('crypto')
    if libcrypto is None:
        raise DrmException('libcrypto not found')
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
                raise DrmException('AES improper key used')
                return
            keyctx = self._keyctx = AES_KEY()
            self.iv = iv
            rv = AES_set_decrypt_key(userkey, len(userkey) * 8, keyctx)
            if rv < 0:
                raise DrmException('Failed to initialize AES key')

        def decrypt(self, data):
            out = create_string_buffer(len(data))
            rv = AES_cbc_encrypt(data, out, len(data), self._keyctx, self.iv, 0)
            if rv == 0:
                raise DrmException('AES decryption failed')
            return out.raw

        def keyivgen(self, passwd, salt, iter, keylen):
            saltlen = len(salt)
            passlen = len(passwd)
            out = create_string_buffer(keylen)
            rv = PKCS5_PBKDF2_HMAC_SHA1(passwd, passlen, salt, saltlen, iter, keylen, out)
            return out.raw
    return LibCrypto

def _load_crypto():
    LibCrypto = None
    try:
        LibCrypto = _load_crypto_libcrypto()
    except (ImportError, DrmException):
        pass
    return LibCrypto

LibCrypto = _load_crypto()

#
# Utility Routines
#

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

# Various character maps used to decrypt books. Probably supposed to act as obfuscation
charMap1 = "n5Pr6St7Uv8Wx9YzAb0Cd1Ef2Gh3Jk4M"
charMap2 = "ZB0bYyc1xDdW2wEV3Ff7KkPpL8UuGA4gz-Tme9Nn_tHh5SvXCsIiR6rJjQaqlOoM" 

# For kinf approach of K4PC/K4Mac
# On K4PC charMap5 = "AzB0bYyCeVvaZ3FfUuG4g-TtHh5SsIiR6rJjQq7KkPpL8lOoMm9Nn_c1XxDdW2wE"
# For Mac they seem to re-use charMap2 here
charMap5 = charMap2

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

# For .kinf approach of K4PC and now K4Mac
# generate table of prime number less than or equal to int n
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
        sernum = ''
    return sernum

def GetUserHomeAppSupKindleDirParitionName():
    home = os.getenv('HOME')
    dpath =  home + '/Library/Application Support/Kindle'
    cmdline = '/sbin/mount'
    cmdline = cmdline.encode(sys.getfilesystemencoding())
    p = subprocess.Popen(cmdline, shell=True, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=False)
    out1, out2 = p.communicate()
    reslst = out1.split('\n')
    cnt = len(reslst)
    disk = ''
    foundIt = False
    for j in xrange(cnt):
        resline = reslst[j]
        if resline.startswith('/dev'):
            (devpart, mpath) = resline.split(' on ')
            dpart = devpart[5:]
            pp = mpath.find('(')
            if pp >= 0:
                mpath = mpath[:pp-1]
            if dpath.startswith(mpath):
                disk = dpart
    return disk

# uses a sub process to get the UUID of the specified disk partition using ioreg
def GetDiskPartitionUUID(diskpart):
    uuidnum = os.getenv('MYUUIDNUMBER')
    if uuidnum != None:
        return uuidnum
    cmdline = '/usr/sbin/ioreg -l -S -w 0 -r -c AppleAHCIDiskDriver'
    cmdline = cmdline.encode(sys.getfilesystemencoding())
    p = subprocess.Popen(cmdline, shell=True, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=False)
    out1, out2 = p.communicate()
    reslst = out1.split('\n')
    cnt = len(reslst)
    bsdname = None
    uuidnum = None
    foundIt = False
    nest = 0
    uuidnest = -1
    partnest = -2
    for j in xrange(cnt):
        resline = reslst[j]
        if resline.find('{') >= 0:
            nest += 1
        if resline.find('}') >= 0:
            nest -= 1
        pp = resline.find('"UUID" = "')
        if pp >= 0:
            uuidnum = resline[pp+10:-1]
            uuidnum = uuidnum.strip()
            uuidnest = nest
            if partnest == uuidnest and uuidnest > 0:
                foundIt = True
                break
        bb = resline.find('"BSD Name" = "')
        if bb >= 0:
            bsdname = resline[bb+14:-1]
            bsdname = bsdname.strip()
            if (bsdname == diskpart):
                partnest = nest
            else :
                partnest = -2
            if partnest == uuidnest and partnest > 0:
                foundIt = True
                break
        if nest == 0:
            partnest = -2
            uuidnest = -1
            uuidnum = None
            bsdname = None
    if not foundIt:
        uuidnum = ''
    return uuidnum
    
def GetMACAddressMunged():
    macnum = os.getenv('MYMACNUM')
    if macnum != None:
        return macnum
    cmdline = '/sbin/ifconfig en0'
    cmdline = cmdline.encode(sys.getfilesystemencoding())
    p = subprocess.Popen(cmdline, shell=True, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=False)
    out1, out2 = p.communicate()
    reslst = out1.split('\n')
    cnt = len(reslst)
    macnum = None
    foundIt = False
    for j in xrange(cnt):
        resline = reslst[j]
        pp = resline.find('ether ')
        if pp >= 0:
            macnum = resline[pp+6:-1]
            macnum = macnum.strip()
            # print "original mac", macnum
            # now munge it up the way Kindle app does
            # by xoring it with 0xa5 and swapping elements 3 and 4
            maclst = macnum.split(':')
            n = len(maclst)
            if n != 6:
                fountIt = False
                break
            for i in range(6):
                maclst[i] = int('0x' + maclst[i], 0)
            mlst = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
            mlst[5] = maclst[5] ^ 0xa5
            mlst[4] = maclst[3] ^ 0xa5
            mlst[3] = maclst[4] ^ 0xa5
            mlst[2] = maclst[2] ^ 0xa5
            mlst[1] = maclst[1] ^ 0xa5
            mlst[0] = maclst[0] ^ 0xa5
            macnum = "%0.2x%0.2x%0.2x%0.2x%0.2x%0.2x" % (mlst[0], mlst[1], mlst[2], mlst[3], mlst[4], mlst[5])
            foundIt = True
            break
    if not foundIt:
        macnum = ''
    return macnum


# uses unix env to get username instead of using sysctlbyname 
def GetUserName():
    username = os.getenv('USER')
    return username


# implements an Pseudo Mac Version of Windows built-in Crypto routine
# used by Kindle for Mac versions < 1.6.0
def CryptUnprotectData(encryptedData):
    sernum = GetVolumeSerialNumber()
    if sernum == '':
        sernum = '9999999999'
    sp = sernum + '!@#' + GetUserName()
    passwdData = encode(SHA256(sp),charMap1)
    salt = '16743'
    iter = 0x3e8
    keylen = 0x80
    crp = LibCrypto()
    key_iv = crp.keyivgen(passwdData, salt, iter, keylen)
    key = key_iv[0:32]
    iv = key_iv[32:48]
    crp.set_decrypt_key(key,iv)
    cleartext = crp.decrypt(encryptedData)
    cleartext = decode(cleartext,charMap1)
    return cleartext


def isNewInstall():
    home = os.getenv('HOME')
    # soccer game fan anyone
    dpath = home + '/Library/Application Support/Kindle/storage/.pes2011'
    # print dpath, os.path.exists(dpath)
    if os.path.exists(dpath):
        return True
    return False
    

def GetIDString():
    # K4Mac now has an extensive set of ids strings it uses
    # in encoding pids and in creating unique passwords
    # for use in its own version of CryptUnprotectDataV2

    # BUT Amazon has now become nasty enough to detect when its app
    # is being run under a debugger and actually changes code paths
    # including which one of these strings is chosen, all to try 
    # to prevent reverse engineering

    # Sad really ... they will only hurt their own sales ...
    # true book lovers really want to keep their books forever
    # and move them to their devices and DRM prevents that so they 
    # will just buy from someplace else that they can remove 
    # the DRM from

    # Amazon should know by now that true book lover's are not like
    # penniless kids that pirate music, we do not pirate books

    if isNewInstall():
        mungedmac = GetMACAddressMunged()
        if len(mungedmac) > 7:
            return mungedmac
    sernum = GetVolumeSerialNumber()
    if len(sernum) > 7:
        return sernum
    diskpart = GetUserHomeAppSupKindleDirParitionName()
    uuidnum = GetDiskPartitionUUID(diskpart)
    if len(uuidnum) > 7:
        return uuidnum
    mungedmac = GetMACAddressMunged()
    if len(mungedmac) > 7:
        return mungedmac
    return '9999999999'


# implements an Pseudo Mac Version of Windows built-in Crypto routine
# used for Kindle for Mac Versions >= 1.6.0
def CryptUnprotectDataV2(encryptedData):
    sp = GetUserName() + ':&%:' + GetIDString()
    passwdData = encode(SHA256(sp),charMap5)
    # salt generation as per the code
    salt = 0x0512981d * 2 * 1 * 1
    salt = str(salt) + GetUserName()
    salt = encode(salt,charMap5)
    crp = LibCrypto()
    iter = 0x800
    keylen = 0x400
    key_iv = crp.keyivgen(passwdData, salt, iter, keylen)
    key = key_iv[0:32]
    iv = key_iv[32:48]
    crp.set_decrypt_key(key,iv)
    cleartext = crp.decrypt(encryptedData)
    cleartext = decode(cleartext, charMap5)
    return cleartext


# Locate the .kindle-info files
def getKindleInfoFiles(kInfoFiles):
    # first search for current .kindle-info files
    home = os.getenv('HOME')
    cmdline = 'find "' + home + '/Library/Application Support" -name ".kindle-info"'
    cmdline = cmdline.encode(sys.getfilesystemencoding())
    p1 = subprocess.Popen(cmdline, shell=True, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=False)
    out1, out2 = p1.communicate()
    reslst = out1.split('\n')
    kinfopath = 'NONE'
    found = False
    for resline in reslst:
        if os.path.isfile(resline):
            kInfoFiles.append(resline)
            found = True
    # add any .kinf files 
    cmdline = 'find "' + home + '/Library/Application Support" -name ".rainier*-kinf"'
    cmdline = cmdline.encode(sys.getfilesystemencoding())
    p1 = subprocess.Popen(cmdline, shell=True, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=False)
    out1, out2 = p1.communicate()
    reslst = out1.split('\n')
    for resline in reslst:
        if os.path.isfile(resline):
            kInfoFiles.append(resline)
            found = True
    if not found:
        print('No kindle-info files have been found.')
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

    if data.find('[') != -1 :
        # older style kindle-info file
        items = data.split('[')
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
                cleartext = CryptUnprotectData(encryptedValue)
                DB[keyname] = cleartext
                cnt = cnt + 1
        if cnt == 0:
            DB = None
        return DB

    # else newer style .kinf file used by K4Mac >= 1.6.0
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
        keyname = "unknown"

        # the raw keyhash string is also used to create entropy for the actual
        # CryptProtectData Blob that represents that keys contents
        # "entropy" not used for K4Mac only K4PC
        # entropy = SHA1(keyhash)
    
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
        # len(contents) - largest prime number less than or equal to int(len(content)/3)
        # (in other words split "about" 2/3rds of the way through)
    
        # move first offsets chars to end to align for decode by charMap5
        encdata = "".join(edlst)
        contlen = len(encdata)

        # now properly split and recombine 
        # by moving noffset chars from the start of the 
        # string to the end of the string 
        noffset = contlen - primes(int(contlen/3))[-1]
        pfx = encdata[0:noffset]
        encdata = encdata[noffset:]
        encdata = encdata + pfx
    
        # decode using charMap5 to get the CryptProtect Data
        encryptedValue = decode(encdata,charMap5)
        cleartext = CryptUnprotectDataV2(encryptedValue)
        # Debugging
        # print keyname
        # print cleartext
        # print cleartext.encode('hex')
        # print
        DB[keyname] = cleartext
        cnt = cnt + 1

    if cnt == 0:
        DB = None
    return DB
