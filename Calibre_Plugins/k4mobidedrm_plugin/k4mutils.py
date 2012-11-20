# standlone set of Mac OSX specific routines needed for KindleBooks

from __future__ import with_statement

import sys
import os
import os.path
import re
import copy
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

    # From OpenSSL's crypto aes header
    #
    # AES_ENCRYPT     1
    # AES_DECRYPT     0
    # AES_MAXNR 14 (in bytes)
    # AES_BLOCK_SIZE 16 (in bytes)
    #
    # struct aes_key_st {
    #    unsigned long rd_key[4 *(AES_MAXNR + 1)];
    #    int rounds;
    # };
    # typedef struct aes_key_st AES_KEY;
    #
    # int AES_set_decrypt_key(const unsigned char *userKey, const int bits, AES_KEY *key);
    #
    # note:  the ivec string, and output buffer are both mutable
    # void AES_cbc_encrypt(const unsigned char *in, unsigned char *out,
    #     const unsigned long length, const AES_KEY *key, unsigned char *ivec, const int enc);

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

    # From OpenSSL's Crypto evp/p5_crpt2.c
    #
    # int PKCS5_PBKDF2_HMAC_SHA1(const char *pass, int passlen,
    #                        const unsigned char *salt, int saltlen, int iter,
    #                        int keylen, unsigned char *out);

    PKCS5_PBKDF2_HMAC_SHA1 = F(c_int, 'PKCS5_PBKDF2_HMAC_SHA1',
                                [c_char_p, c_ulong, c_char_p, c_ulong, c_ulong, c_ulong, c_char_p])

    class LibCrypto(object):
        def __init__(self):
            self._blocksize = 0
            self._keyctx = None
            self._iv = 0

        def set_decrypt_key(self, userkey, iv):
            self._blocksize = len(userkey)
            if (self._blocksize != 16) and (self._blocksize != 24) and (self._blocksize != 32) :
                raise DrmException('AES improper key used')
                return
            keyctx = self._keyctx = AES_KEY()
            self._iv = iv
            self._userkey = userkey
            rv = AES_set_decrypt_key(userkey, len(userkey) * 8, keyctx)
            if rv < 0:
                raise DrmException('Failed to initialize AES key')

        def decrypt(self, data):
            out = create_string_buffer(len(data))
            mutable_iv = create_string_buffer(self._iv, len(self._iv))
            keyctx = self._keyctx
            rv = AES_cbc_encrypt(data, out, len(data), keyctx, mutable_iv, 0)
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

# For kinf approach of K4Mac 1.6.X or later
# On K4PC charMap5 = "AzB0bYyCeVvaZ3FfUuG4g-TtHh5SsIiR6rJjQq7KkPpL8lOoMm9Nn_c1XxDdW2wE"
# For Mac they seem to re-use charMap2 here
charMap5 = charMap2

# new in K4M 1.9.X
testMap8 = "YvaZ3FfUm9Nn_c1XuG4yCAzB0beVg-TtHh5SsIiR6rJjQdW2wEq7KkPpL8lOoMxD"


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

# For K4M 1.6.X and later
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
    dpath =  home + '/Library'
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

def isNewInstall():
    home = os.getenv('HOME')
    # soccer game fan anyone
    dpath = home + '/Library/Application Support/Kindle/storage/.pes2011'
    # print dpath, os.path.exists(dpath)
    if os.path.exists(dpath):
        return True
    dpath = home + '/Library/Containers/com.amazon.Kindle/Data/Library/Application Support/Kindle/storage/.pes2011'
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
            print('Using Munged MAC Address for ID: '+mungedmac)
            return mungedmac
    sernum = GetVolumeSerialNumber()
    if len(sernum) > 7:
        print('Using Volume Serial Number for ID: '+sernum)
        return sernum
    diskpart = GetUserHomeAppSupKindleDirParitionName()
    uuidnum = GetDiskPartitionUUID(diskpart)
    if len(uuidnum) > 7:
        print('Using Disk Partition UUID for ID: '+uuidnum)
        return uuidnum
    mungedmac = GetMACAddressMunged()
    if len(mungedmac) > 7:
        print('Using Munged MAC Address for ID: '+mungedmac)
        return mungedmac
    print('Using Fixed constant 9999999999 for ID.')
    return '9999999999'


# implements an Pseudo Mac Version of Windows built-in Crypto routine
# used by Kindle for Mac versions < 1.6.0
class CryptUnprotectData(object):
    def __init__(self):
        sernum = GetVolumeSerialNumber()
        if sernum == '':
            sernum = '9999999999'
        sp = sernum + '!@#' + GetUserName()
        passwdData = encode(SHA256(sp),charMap1)
        salt = '16743'
        self.crp = LibCrypto()
        iter = 0x3e8
        keylen = 0x80
        key_iv = self.crp.keyivgen(passwdData, salt, iter, keylen)
        self.key = key_iv[0:32]
        self.iv = key_iv[32:48]
        self.crp.set_decrypt_key(self.key, self.iv)

    def decrypt(self, encryptedData):
        cleartext = self.crp.decrypt(encryptedData)
        cleartext = decode(cleartext,charMap1)
        return cleartext


# implements an Pseudo Mac Version of Windows built-in Crypto routine
# used for Kindle for Mac Versions >= 1.6.0
class CryptUnprotectDataV2(object):
    def __init__(self):
        sp = GetUserName() + ':&%:' + GetIDString()
        passwdData = encode(SHA256(sp),charMap5)
        # salt generation as per the code
        salt = 0x0512981d * 2 * 1 * 1
        salt = str(salt) + GetUserName()
        salt = encode(salt,charMap5)
        self.crp = LibCrypto()
        iter = 0x800
        keylen = 0x400
        key_iv = self.crp.keyivgen(passwdData, salt, iter, keylen)
        self.key = key_iv[0:32]
        self.iv = key_iv[32:48]
        self.crp.set_decrypt_key(self.key, self.iv)

    def decrypt(self, encryptedData):
        cleartext = self.crp.decrypt(encryptedData)
        cleartext = decode(cleartext, charMap5)
        return cleartext


# unprotect the new header blob in .kinf2011
# used in Kindle for Mac Version >= 1.9.0
def UnprotectHeaderData(encryptedData):
    passwdData = 'header_key_data'
    salt = 'HEADER.2011'
    iter = 0x80
    keylen = 0x100
    crp = LibCrypto()
    key_iv = crp.keyivgen(passwdData, salt, iter, keylen)
    key = key_iv[0:32]
    iv = key_iv[32:48]
    crp.set_decrypt_key(key,iv)
    cleartext = crp.decrypt(encryptedData)
    return cleartext


# implements an Pseudo Mac Version of Windows built-in Crypto routine
# used for Kindle for Mac Versions >= 1.9.0
class CryptUnprotectDataV3(object):
    def __init__(self, entropy):
        sp = GetUserName() + '+@#$%+' + GetIDString()
        passwdData = encode(SHA256(sp),charMap2)
        salt = entropy
        self.crp = LibCrypto()
        iter = 0x800
        keylen = 0x400
        key_iv = self.crp.keyivgen(passwdData, salt, iter, keylen)
        self.key = key_iv[0:32]
        self.iv = key_iv[32:48]
        self.crp.set_decrypt_key(self.key, self.iv)

    def decrypt(self, encryptedData):
        cleartext = self.crp.decrypt(encryptedData)
        cleartext = decode(cleartext, charMap2)
        return cleartext


# Locate the .kindle-info files
def getKindleInfoFiles():
    # file searches can take a long time on some systems, so just look in known specific places.
    kInfoFiles=[]
    found = False
    home = os.getenv('HOME')
    # check for  .kinf2011 file in new location (App Store Kindle for Mac)
    testpath = home + '/Library/Containers/com.amazon.Kindle/Data/Library/Application Support/Kindle/storage/.kinf2011'
    if os.path.isfile(testpath):
        kInfoFiles.append(testpath)
        print('Found k4Mac kinf2011 file: ' + testpath)
        found = True
    # check for  .kinf2011 files
    testpath = home + '/Library/Application Support/Kindle/storage/.kinf2011'
    if os.path.isfile(testpath):
        kInfoFiles.append(testpath)
        print('Found k4Mac kinf2011 file: ' + testpath)
        found = True
    # check for  .rainier-2.1.1-kinf files
    testpath = home + '/Library/Application Support/Kindle/storage/.rainier-2.1.1-kinf'
    if os.path.isfile(testpath):
        kInfoFiles.append(testpath)
        print('Found k4Mac rainier file: ' + testpath)
        found = True
    # check for  .rainier-2.1.1-kinf files
    testpath = home + '/Library/Application Support/Kindle/storage/.kindle-info'
    if os.path.isfile(testpath):
        kInfoFiles.append(testpath)
        print('Found k4Mac kindle-info file: ' + testpath)
        found = True
    if not found:
        print('No k4Mac kindle-info/rainier/kinf2011 files have been found.')
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
        cud = CryptUnprotectData()
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
                cleartext = cud.decrypt(encryptedValue)
                DB[keyname] = cleartext
                cnt = cnt + 1
        if cnt == 0:
            DB = None
        return DB

    if hdr == '/':

        # else newer style .kinf file used by K4Mac >= 1.6.0
        # the .kinf file uses "/" to separate it into records
        # so remove the trailing "/" to make it easy to use split
        data = data[:-1]
        items = data.split('/')
        cud = CryptUnprotectDataV2()

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
            cleartext = cud.decrypt(encryptedValue)
            DB[keyname] = cleartext
            cnt = cnt + 1

        if cnt == 0:
            DB = None
        return DB

    # the latest .kinf2011 version for K4M 1.9.1
    # put back the hdr char, it is needed
    data = hdr + data
    data = data[:-1]
    items = data.split('/')

    # the headerblob is the encrypted information needed to build the entropy string
    headerblob = items.pop(0)
    encryptedValue = decode(headerblob, charMap1)
    cleartext = UnprotectHeaderData(encryptedValue)

    # now extract the pieces in the same way
    # this version is different from K4PC it scales the build number by multipying by 735
    pattern = re.compile(r'''\[Version:(\d+)\]\[Build:(\d+)\]\[Cksum:([^\]]+)\]\[Guid:([\{\}a-z0-9\-]+)\]''', re.IGNORECASE)
    for m in re.finditer(pattern, cleartext):
        entropy = str(int(m.group(2)) * 0x2df) + m.group(4)

    cud = CryptUnprotectDataV3(entropy)

    # loop through the item records until all are processed
    while len(items) > 0:

        # get the first item record
        item = items.pop(0)

        # the first 32 chars of the first record of a group
        # is the MD5 hash of the key name encoded by charMap5
        keyhash = item[0:32]
        keyname = "unknown"

        # unlike K4PC the keyhash is not used in generating entropy
        # entropy = SHA1(keyhash) + added_entropy
        # entropy = added_entropy

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
            if encodeHash(name,testMap8) == keyhash:
                keyname = name
                break
        if keyname == "unknown":
            keyname = keyhash

        # the testMap8 encoded contents data has had a length
        # of chars (always odd) cut off of the front and moved
        # to the end to prevent decoding using testMap8 from
        # working properly, and thereby preventing the ensuing
        # CryptUnprotectData call from succeeding.

        # The offset into the testMap8 encoded contents seems to be:
        # len(contents) - largest prime number less than or equal to int(len(content)/3)
        # (in other words split "about" 2/3rds of the way through)

        # move first offsets chars to end to align for decode by testMap8
        encdata = "".join(edlst)
        contlen = len(encdata)

        # now properly split and recombine
        # by moving noffset chars from the start of the
        # string to the end of the string
        noffset = contlen - primes(int(contlen/3))[-1]
        pfx = encdata[0:noffset]
        encdata = encdata[noffset:]
        encdata = encdata + pfx

        # decode using testMap8 to get the CryptProtect Data
        encryptedValue = decode(encdata,testMap8)
        cleartext = cud.decrypt(encryptedValue)
        # print keyname
        # print cleartext
        DB[keyname] = cleartext
        cnt = cnt + 1

    if cnt == 0:
        DB = None
    return DB
