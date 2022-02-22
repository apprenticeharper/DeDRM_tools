#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# kindlekey.py
# Copyright © 2008-2022 Apprentice Harper et al.

__license__ = 'GPL v3'
__version__ = '3.1'

# Revision history:
#  1.0   - Kindle info file decryption, extracted from k4mobidedrm, etc.
#  1.1   - Added Tkinter to match adobekey.py
#  1.2   - Fixed testing of successful retrieval on Mac
#  1.3   - Added getkey interface for Windows DeDRM application
#          Simplified some of the Kindle for Mac code.
#  1.4   - Remove dependency on alfcrypto
#  1.5   - moved unicode_argv call inside main for Windows DeDRM compatibility
#  1.6   - Fixed a problem getting the disk serial numbers
#  1.7   - Work if TkInter is missing
#  1.8   - Fixes for Kindle for Mac, and non-ascii in Windows user names
#  1.9   - Fixes for Unicode in Windows user names
#  2.0   - Added comments and extra fix for non-ascii Windows user names
#  2.1   - Fixed Kindle for PC encryption changes March 2016
#  2.2   - Fixes for Macs with bonded ethernet ports
#          Also removed old .kinfo file support (pre-2011)
#  2.3   - Added more field names thanks to concavegit's KFX code.
#  2.4   - Fix for complex Mac disk setups, thanks to Tibs
#  2.5   - Final Fix for Windows user names with non-ascii characters, thanks to oneofusoneofus
#  2.6   - Start adding support for Kindle 1.25+ .kinf2018 file
#  2.7   - Finish .kinf2018 support, PC & Mac by Apprentice Sakuya
#  2.8   - Fix for Mac OS X Big Sur
#  3.0   - Python 3 for calibre 5.0
#  3.1   - Only support PyCryptodome; clean up the code


"""
Retrieve Kindle for PC/Mac user key.
"""

import sys, os, re
import codecs
from struct import pack, unpack, unpack_from
import json
import getopt
import traceback
import hashlib

try:
    from Cryptodome.Cipher import AES
    from Cryptodome.Util import Counter
    from Cryptodome.Protocol.KDF import PBKDF2
except ImportError:
    from Crypto.Cipher import AES
    from Crypto.Util import Counter
    from Crypto.Protocol.KDF import PBKDF2

try:
    RegError
except NameError:
    class RegError(Exception):
        pass

# Routines common to Mac and PC

# Wrap a stream so that output gets flushed immediately
# and also make sure that any unicode strings get
# encoded using "replace" before writing them.
class SafeUnbuffered:
    def __init__(self, stream):
        self.stream = stream
        self.encoding = stream.encoding
        if self.encoding == None:
            self.encoding = "utf-8"
    def write(self, data):
        if isinstance(data,str) or isinstance(data,unicode):
            # str for Python3, unicode for Python2
            data = data.encode(self.encoding,"replace")
        try:
            buffer = getattr(self.stream, 'buffer', self.stream)
            # self.stream.buffer for Python3, self.stream for Python2
            buffer.write(data)
            buffer.flush()
        except:
            # We can do nothing if a write fails
            raise
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

try:
    from calibre.constants import iswindows, isosx
except:
    iswindows = sys.platform.startswith('win')
    isosx = sys.platform.startswith('darwin')

def unicode_argv():
    if iswindows:
        # Uses shell32.GetCommandLineArgvW to get sys.argv as a list of Unicode
        # strings.

        # Versions 2.x of Python don't support Unicode in sys.argv on
        # Windows, with the underlying Windows API instead replacing multi-byte
        # characters with '?'.  So use shell32.GetCommandLineArgvW to get sys.argv
        # as a list of Unicode strings and encode them as utf-8

        from ctypes import POINTER, byref, cdll, c_int, windll
        from ctypes.wintypes import LPCWSTR, LPWSTR

        GetCommandLineW = cdll.kernel32.GetCommandLineW
        GetCommandLineW.argtypes = []
        GetCommandLineW.restype = LPCWSTR

        CommandLineToArgvW = windll.shell32.CommandLineToArgvW
        CommandLineToArgvW.argtypes = [LPCWSTR, POINTER(c_int)]
        CommandLineToArgvW.restype = POINTER(LPWSTR)

        cmd = GetCommandLineW()
        argc = c_int(0)
        argv = CommandLineToArgvW(cmd, byref(argc))
        if argc.value > 0:
            # Remove Python executable and commands if present
            start = argc.value - len(sys.argv)
            return [argv[i] for i in
                    range(start, argc.value)]
        # if we don't have any arguments at all, just pass back script name
        # this should never happen
        return ["kindlekey.py"]
    else:
        argvencoding = sys.stdin.encoding or "utf-8"
        return [arg if (isinstance(arg, str) or isinstance(arg,unicode)) else str(arg, argvencoding) for arg in sys.argv]

class DrmException(Exception):
    pass

# crypto digestroutines

def MD5(message):
    return hashlib.md5(message).digest()

def SHA1(message):
    return hashlib.sha1(message).digest()

def SHA256(message):
    return hashlib.sha256(message).digest()


# For K4M/PC 1.6.X and later
def primes(n):
    """
    Return a list of prime integers smaller than or equal to n
    :param n: int
    :return: list->int
    """
    if n == 2:
        return [2]
    elif n < 2:
        return []
    primeList = [2]

    for potentialPrime in range(3, n + 1, 2):
        isItPrime = True
        for prime in primeList:
            if potentialPrime % prime == 0:
                isItPrime = False
        if isItPrime is True:
            primeList.append(potentialPrime)

    return primeList

# Encode the bytes in data with the characters in map
# data and map should be byte arrays
def encode(data, map):
    result = b''
    for char in data:
        value = char
        Q = (value ^ 0x80) // len(map)
        R = value % len(map)
        result += bytes([map[Q]])
        result += bytes([map[R]])
    return result

# Hash the bytes in data and then encode the digest with the characters in map
def encodeHash(data,map):
    return encode(MD5(data),map)

# Decode the string in data with the characters in map. Returns the decoded bytes
def decode(data,map):
    result = b''
    for i in range (0,len(data)-1,2):
        high = map.find(data[i])
        low = map.find(data[i+1])
        if (high == -1) or (low == -1) :
            break
        value = (((high * len(map)) ^ 0x80) & 0xFF) + low
        result += pack('B',value)
    return result

def UnprotectHeaderData(encryptedData):
    passwdData = b'header_key_data'
    salt = b'HEADER.2011'
    key_iv = PBKDF2(passwdData, salt, dkLen=256, count=128)
    return AES.new(key_iv[0:32], AES.MODE_CBC, key_iv[32:48]).decrypt(encryptedData)

# Routines unique to Mac and PC
if iswindows:
    from ctypes import windll, c_char_p, c_wchar_p, c_uint, POINTER, byref, \
        create_unicode_buffer, create_string_buffer, CFUNCTYPE, addressof, \
        string_at, Structure, c_void_p, cast

    try:
        import winreg
    except ImportError:
        import _winreg as winreg

    MAX_PATH = 255
    kernel32 = windll.kernel32
    advapi32 = windll.advapi32
    crypt32 = windll.crypt32

    # Various character maps used to decrypt kindle info values.
    # Probably supposed to act as obfuscation
    charMap2 = b"AaZzB0bYyCc1XxDdW2wEeVv3FfUuG4g-TtHh5SsIiR6rJjQq7KkPpL8lOoMm9Nn_"
    charMap5 = b"AzB0bYyCeVvaZ3FfUuG4g-TtHh5SsIiR6rJjQq7KkPpL8lOoMm9Nn_c1XxDdW2wE"
    # New maps in K4PC 1.9.0
    testMap1 = b"n5Pr6St7Uv8Wx9YzAb0Cd1Ef2Gh3Jk4M"
    testMap6 = b"9YzAb0Cd1Ef2n5Pr6St7Uvh3Jk4M8WxG"
    testMap8 = b"YvaZ3FfUm9Nn_c1XuG4yCAzB0beVg-TtHh5SsIiR6rJjQdW2wEq7KkPpL8lOoMxD"

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
        #print('Using Volume Serial Number for ID: '+vsn)
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
                # double the buffer size
                buffer = create_unicode_buffer(len(buffer) * 2)
                size.value = len(buffer)

            # replace any non-ASCII values with 0xfffd
            for i in range(0,len(buffer)):
                if buffer[i]>"\u007f":
                    #print "swapping char "+str(i)+" ("+buffer[i]+")"
                    buffer[i] = "\ufffd"
            # return utf-8 encoding of modified username
            #print "modified username:"+buffer.value
            return buffer.value.encode('utf-8')
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
                return b'failed'
            return string_at(outdata.pbData, outdata.cbData)
        return CryptUnprotectData
    CryptUnprotectData = CryptUnprotectData()

    # Returns Environmental Variables that contain unicode
    # name must be unicode string, not byte string.
    def getEnvironmentVariable(name):
        import ctypes
        n = ctypes.windll.kernel32.GetEnvironmentVariableW(name, None, 0)
        if n == 0:
            return None
        buf = ctypes.create_unicode_buffer("\0"*n)
        ctypes.windll.kernel32.GetEnvironmentVariableW(name, buf, n)
        return buf.value

    # Locate all of the kindle-info style files and return as list
    def getKindleInfoFiles():
        kInfoFiles = []
        # some 64 bit machines do not have the proper registry key for some reason
        # or the python interface to the 32 vs 64 bit registry is broken
        path = ""
        if 'LOCALAPPDATA' in os.environ.keys():
            # Python 2.x does not return unicode env. Use Python 3.x
            path = winreg.ExpandEnvironmentStrings("%LOCALAPPDATA%")
            # this is just another alternative.
            # path = getEnvironmentVariable('LOCALAPPDATA')
            if not os.path.isdir(path):
                path = ""
        else:
            # User Shell Folders show take precedent over Shell Folders if present
            try:
                # this will still break
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
            # Probably not the best. To Fix (shouldn't ignore in encoding) or use utf-8
            print("searching for kinfoFiles in " + path)

            # look for (K4PC 1.25.1 and later) .kinf2018 file
            kinfopath = path +'\\Amazon\\Kindle\\storage\\.kinf2018'
            if os.path.isfile(kinfopath):
                found = True
                print('Found K4PC 1.25+ kinf2018 file: ' + kinfopath)
                kInfoFiles.append(kinfopath)

            # look for (K4PC 1.9.0 and later) .kinf2011 file
            kinfopath = path +'\\Amazon\\Kindle\\storage\\.kinf2011'
            if os.path.isfile(kinfopath):
                found = True
                print('Found K4PC 1.9+ kinf2011 file: ' + kinfopath)
                kInfoFiles.append(kinfopath)

            # look for (K4PC 1.6.0 and later) rainier.2.1.1.kinf file
            kinfopath = path +'\\Amazon\\Kindle\\storage\\rainier.2.1.1.kinf'
            if os.path.isfile(kinfopath):
                found = True
                print('Found K4PC 1.6-1.8 kinf file: ' + kinfopath)
                kInfoFiles.append(kinfopath)

            # look for (K4PC 1.5.0 and later) rainier.2.1.1.kinf file
            kinfopath = path +'\\Amazon\\Kindle For PC\\storage\\rainier.2.1.1.kinf'
            if os.path.isfile(kinfopath):
                found = True
                print('Found K4PC 1.5 kinf file: ' + kinfopath)
                kInfoFiles.append(kinfopath)

           # look for original (earlier than K4PC 1.5.0) kindle-info files
            kinfopath = path +'\\Amazon\\Kindle For PC\\{AMAwzsaPaaZAzmZzZQzgZCAkZ3AjA_AY}\\kindle.info'
            if os.path.isfile(kinfopath):
                found = True
                print('Found K4PC kindle.info file: ' + kinfopath)
                kInfoFiles.append(kinfopath)

        if not found:
            print('No K4PC kindle.info/kinf/kinf2011 files have been found.')
        return kInfoFiles


    # determine type of kindle info provided and return a
    # database of keynames and values
    def getDBfromFile(kInfoFile):
        names = [\
            b'kindle.account.tokens',\
            b'kindle.cookie.item',\
            b'eulaVersionAccepted',\
            b'login_date',\
            b'kindle.token.item',\
            b'login',\
            b'kindle.key.item',\
            b'kindle.name.info',\
            b'kindle.device.info',\
            b'MazamaRandomNumber',\
            b'max_date',\
            b'SIGVERIF',\
            b'build_version',\
            b'SerialNumber',\
            b'UsernameHash',\
            b'kindle.directedid.info',\
            b'DSN',\
            b'kindle.accounttype.info',\
            b'krx.flashcardsplugin.data.encryption_key',\
            b'krx.notebookexportplugin.data.encryption_key',\
            b'proxy.http.password',\
            b'proxy.http.username'
            ]
        namehashmap = {encodeHash(n,testMap8):n for n in names}
        # print(namehashmap)
        DB = {}
        with open(kInfoFile, 'rb') as infoReader:
            data = infoReader.read()
        # assume .kinf2011 or .kinf2018 style .kinf file
        # the .kinf file uses "/" to separate it into records
        # so remove the trailing "/" to make it easy to use split
        data = data[:-1]
        items = data.split(b'/')

        # starts with an encoded and encrypted header blob
        headerblob = items.pop(0)
        encryptedValue = decode(headerblob, testMap1)
        cleartext = UnprotectHeaderData(encryptedValue)
        #print "header  cleartext:",cleartext
        # now extract the pieces that form the added entropy
        pattern = re.compile(br'''\[Version:(\d+)\]\[Build:(\d+)\]\[Cksum:([^\]]+)\]\[Guid:([\{\}a-z0-9\-]+)\]''', re.IGNORECASE)
        for m in re.finditer(pattern, cleartext):
            version = int(m.group(1))
            build = m.group(2)
            guid = m.group(4)

        if version == 5:  # .kinf2011
            added_entropy = build + guid
        elif version == 6:  # .kinf2018
            salt = str(0x6d8 * int(build)).encode('utf-8') + guid
            sp = GetUserName() + b'+@#$%+' + GetIDString().encode('utf-8')
            passwd = encode(SHA256(sp), charMap5)
            key = PBKDF2(passwd, salt, count=10000, dkLen=0x400)[:32]  # this is very slow

        # loop through the item records until all are processed
        while len(items) > 0:

            # get the first item record
            item = items.pop(0)

            # the first 32 chars of the first record of a group
            # is the MD5 hash of the key name encoded by charMap5
            keyhash = item[0:32]

            # the remainder of the first record when decoded with charMap5
            # has the ':' split char followed by the string representation
            # of the number of records that follow
            # and make up the contents
            srcnt = decode(item[34:],charMap5)
            rcnt = int(srcnt)

            # read and store in rcnt records of data
            # that make up the contents value
            edlst = []
            for i in range(rcnt):
                item = items.pop(0)
                edlst.append(item)

            # key names now use the new testMap8 encoding
            if keyhash in namehashmap:
                keyname=namehashmap[keyhash]
                #print "keyname found from hash:",keyname
            else:
                keyname = keyhash
                #print "keyname not found, hash is:",keyname

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
            encdata = b"".join(edlst)
            #print "encrypted data:",encdata
            contlen = len(encdata)
            noffset = contlen - primes(int(contlen/3))[-1]
            pfx = encdata[0:noffset]
            encdata = encdata[noffset:]
            encdata = encdata + pfx
            #print "rearranged data:",encdata

            if version == 5:
                # decode using new testMap8 to get the original CryptProtect Data
                encryptedValue = decode(encdata,testMap8)
                #print "decoded data:",encryptedValue.encode('hex')
                entropy = SHA1(keyhash) + added_entropy
                cleartext = CryptUnprotectData(encryptedValue, entropy, 1)
            elif version == 6:
                # decode using new testMap8 to get IV + ciphertext
                iv_ciphertext = decode(encdata, testMap8)
                # pad IV so that we can substitute AES-CTR for GCM
                iv = iv_ciphertext[:12] + b'\x00\x00\x00\x02'
                ciphertext = iv_ciphertext[12:]
                # convert IV to int for use with pycrypto
                iv_ints = unpack('>QQ', iv)
                iv = iv_ints[0] << 64 | iv_ints[1]
                # set up AES-CTR
                ctr = Counter.new(128, initial_value=iv)
                cipher = AES.new(key, AES.MODE_CTR, counter=ctr)
                # decrypt and decode
                cleartext = decode(cipher.decrypt(ciphertext), charMap5)

            if len(cleartext)>0:
                #print "cleartext data:",cleartext,":end data"
                DB[keyname] = cleartext
            #print keyname, cleartext

        if len(DB)>6:
            # store values used in decryption
            DB[b'IDString'] = GetIDString().encode('utf-8')
            DB[b'UserName'] = GetUserName()
            print("Decrypted key file using IDString '{0:s}' and UserName '{1:s}'".format(GetIDString(), GetUserName().decode('utf-8')))
        else:
            print("Couldn't decrypt file.")
            DB = {}
        return DB
elif isosx:
    import subprocess

    # Various character maps used to decrypt books. Probably supposed to act as obfuscation
    charMap1 = b'n5Pr6St7Uv8Wx9YzAb0Cd1Ef2Gh3Jk4M'
    charMap2 = b'ZB0bYyc1xDdW2wEV3Ff7KkPpL8UuGA4gz-Tme9Nn_tHh5SvXCsIiR6rJjQaqlOoM'

    # For kinf approach of K4Mac 1.6.X or later
    # On K4PC charMap5 = 'AzB0bYyCeVvaZ3FfUuG4g-TtHh5SsIiR6rJjQq7KkPpL8lOoMm9Nn_c1XxDdW2wE'
    # For Mac they seem to re-use charMap2 here
    charMap5 = charMap2

    # new in K4M 1.9.X
    testMap8 = b'YvaZ3FfUm9Nn_c1XuG4yCAzB0beVg-TtHh5SsIiR6rJjQdW2wEq7KkPpL8lOoMxD'

    # uses a sub process to get the Hard Drive Serial Number using ioreg
    # returns serial numbers of all internal hard drive drives
    def GetVolumesSerialNumbers():
        sernums = []
        sernum = os.getenv('MYSERIALNUMBER')
        if sernum != None:
            sernums.append(sernum.strip())
        cmdline = '/usr/sbin/ioreg -w 0 -r -c AppleAHCIDiskDriver'
        cmdline = cmdline.encode(sys.getfilesystemencoding())
        p = subprocess.Popen(cmdline, shell=True, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=False)
        out1, out2 = p.communicate()
        #print out1
        reslst = out1.split(b'\n')
        cnt = len(reslst)
        for j in range(cnt):
            resline = reslst[j]
            pp = resline.find(b'\"Serial Number\" = \"')
            if pp >= 0:
                sernum = resline[pp+19:-1]
                sernums.append(sernum.strip())
        return sernums

    def GetDiskPartitionNames():
        names = []
        cmdline = '/sbin/mount'
        cmdline = cmdline.encode(sys.getfilesystemencoding())
        p = subprocess.Popen(cmdline, shell=True, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=False)
        out1, out2 = p.communicate()
        reslst = out1.split(b'\n')
        cnt = len(reslst)
        for j in range(cnt):
            resline = reslst[j]
            if resline.startswith(b'/dev'):
                (devpart, mpath) = resline.split(b' on ')[:2]
                dpart = devpart[5:]
                names.append(dpart)
        return names

    # uses a sub process to get the UUID of all disk partitions
    def GetDiskPartitionUUIDs():
        uuids = []
        uuidnum = os.getenv('MYUUIDNUMBER')
        if uuidnum != None:
            uuids.append(uuidnum.strip())
        cmdline = '/usr/sbin/ioreg -l -S -w 0 -r -c AppleAHCIDiskDriver'
        cmdline = cmdline.encode(sys.getfilesystemencoding())
        p = subprocess.Popen(cmdline, shell=True, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=False)
        out1, out2 = p.communicate()
        #print out1
        reslst = out1.split(b'\n')
        cnt = len(reslst)
        for j in range(cnt):
            resline = reslst[j]
            pp = resline.find(b'\"UUID\" = \"')
            if pp >= 0:
                uuidnum = resline[pp+10:-1]
                uuidnum = uuidnum.strip()
                uuids.append(uuidnum)
        return uuids

    def GetMACAddressesMunged():
        macnums = []
        macnum = os.getenv('MYMACNUM')
        if macnum != None:
            macnums.append(macnum)
        cmdline = 'networksetup -listallhardwareports' # en0'
        cmdline = cmdline.encode(sys.getfilesystemencoding())
        p = subprocess.Popen(cmdline, shell=True, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=False)
        out1, out2 = p.communicate()
        reslst = out1.split(b'\n')
        cnt = len(reslst)
        for j in range(cnt):
            resline = reslst[j]
            pp = resline.find(b'Ethernet Address: ')
            if pp >= 0:
                #print resline
                macnum = resline[pp+18:]
                macnum = macnum.strip()
                maclst = macnum.split(b':')
                n = len(maclst)
                if n != 6:
                    continue
                #print 'original mac', macnum
                # now munge it up the way Kindle app does
                # by xoring it with 0xa5 and swapping elements 3 and 4
                for i in range(6):
                    maclst[i] = int(b'0x' + maclst[i], 0)
                mlst = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
                mlst[5] = maclst[5] ^ 0xa5
                mlst[4] = maclst[3] ^ 0xa5
                mlst[3] = maclst[4] ^ 0xa5
                mlst[2] = maclst[2] ^ 0xa5
                mlst[1] = maclst[1] ^ 0xa5
                mlst[0] = maclst[0] ^ 0xa5
                macnum = b'%0.2x%0.2x%0.2x%0.2x%0.2x%0.2x' % (mlst[0], mlst[1], mlst[2], mlst[3], mlst[4], mlst[5])
                #print 'munged mac', macnum
                macnums.append(macnum)
        return macnums


    # uses unix env to get username instead of using sysctlbyname
    def GetUserName():
        username = os.getenv('USER')
        #print "Username:",username
        return username.encode('utf-8')

    def GetIDStrings():
        # Return all possible ID Strings
        strings = []
        strings.extend(GetMACAddressesMunged())
        strings.extend(GetVolumesSerialNumbers())
        strings.extend(GetDiskPartitionNames())
        strings.extend(GetDiskPartitionUUIDs())
        strings.append(b'9999999999')
        #print "ID Strings:\n",strings
        return strings

    # implements an Pseudo Mac Version of Windows built-in Crypto routine
    class CryptUnprotectData(object):
        def __init__(self, entropy, IDString):
            sp = GetUserName() + b'+@#$%+' + IDString
            passwdData = encode(SHA256(sp),charMap2)
            salt = entropy
            key_iv = PBKDF2(passwdData, salt, count=0x800, dkLen=0x400)
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
        # check for  .kinf2018 file in new location (App Store Kindle for Mac)
        testpath = home + '/Library/Containers/com.amazon.Kindle/Data/Library/Application Support/Kindle/storage/.kinf2018'
        if os.path.isfile(testpath):
            kInfoFiles.append(testpath)
            print('Found k4Mac kinf2018 file: ' + testpath)
            found = True
        # check for  .kinf2018 files
        testpath = home + '/Library/Application Support/Kindle/storage/.kinf2018'
        if os.path.isfile(testpath):
            kInfoFiles.append(testpath)
            print('Found k4Mac kinf2018 file: ' + testpath)
            found = True
        # check for  .kinf2011 file in new location (App Store Kindle for Mac)
        testpath = home + '/Library/Containers/com.amazon.Kindle/Data/Library/Application Support/Kindle/storage/.kinf2011'
        if os.path.isfile(testpath):
            kInfoFiles.append(testpath)
            print('Found k4Mac kinf2011 file: ' + testpath)
            found = True
        # check for  .kinf2011 files from 1.10
        testpath = home + '/Library/Application Support/Kindle/storage/.kinf2011'
        if os.path.isfile(testpath):
            kInfoFiles.append(testpath)
            print('Found k4Mac kinf2011 file: ' + testpath)
            found = True
        # check for  .rainier-2.1.1-kinf files from 1.6
        testpath = home + '/Library/Application Support/Kindle/storage/.rainier-2.1.1-kinf'
        if os.path.isfile(testpath):
            kInfoFiles.append(testpath)
            print('Found k4Mac rainier file: ' + testpath)
            found = True
        # check for  .kindle-info files from 1.4
        testpath = home + '/Library/Application Support/Kindle/storage/.kindle-info'
        if os.path.isfile(testpath):
            kInfoFiles.append(testpath)
            print('Found k4Mac kindle-info file: ' + testpath)
            found = True
        # check for  .kindle-info file from 1.2.2
        testpath = home + '/Library/Application Support/Amazon/Kindle/storage/.kindle-info'
        if os.path.isfile(testpath):
            kInfoFiles.append(testpath)
            print('Found k4Mac kindle-info file: ' + testpath)
            found = True
        # check for  .kindle-info file from 1.0 beta 1 (27214)
        testpath = home + '/Library/Application Support/Amazon/Kindle for Mac/storage/.kindle-info'
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
        names = [\
            b'kindle.account.tokens',\
            b'kindle.cookie.item',\
            b'eulaVersionAccepted',\
            b'login_date',\
            b'kindle.token.item',\
            b'login',\
            b'kindle.key.item',\
            b'kindle.name.info',\
            b'kindle.device.info',\
            b'MazamaRandomNumber',\
            b'max_date',\
            b'SIGVERIF',\
            b'build_version',\
            b'SerialNumber',\
            b'UsernameHash',\
            b'kindle.directedid.info',\
            b'DSN',\
            b'kindle.accounttype.info',\
            b'krx.flashcardsplugin.data.encryption_key',\
            b'krx.notebookexportplugin.data.encryption_key',\
            b'proxy.http.password',\
            b'proxy.http.username'
            ]
        with open(kInfoFile, 'rb') as infoReader:
            filedata = infoReader.read()

        data = filedata[:-1]
        items = data.split(b'/')
        IDStrings = GetIDStrings()
        print ("trying username ", GetUserName(), " on file ", kInfoFile)
        for IDString in IDStrings:
            print ("trying IDString:",IDString)
            try:
                DB = {}
                items = data.split(b'/')

                # the headerblob is the encrypted information needed to build the entropy string
                headerblob = items.pop(0)
                #print ("headerblob: ",headerblob)
                encryptedValue = decode(headerblob, charMap1)
                #print ("encryptedvalue: ",encryptedValue)
                cleartext = UnprotectHeaderData(encryptedValue)
                #print ("cleartext: ",cleartext)

                # now extract the pieces in the same way
                pattern = re.compile(br'''\[Version:(\d+)\]\[Build:(\d+)\]\[Cksum:([^\]]+)\]\[Guid:([\{\}a-z0-9\-]+)\]''', re.IGNORECASE)
                for m in re.finditer(pattern, cleartext):
                    version = int(m.group(1))
                    build = m.group(2)
                    guid = m.group(4)

                #print ("version",version)
                #print ("build",build)
                #print ("guid",guid,"\n")

                if version == 5:  # .kinf2011: identical to K4PC, except the build number gets multiplied
                    entropy = str(0x2df * int(build)).encode('utf-8') + guid
                    cud = CryptUnprotectData(entropy,IDString)
                    #print ("entropy",entropy)
                    #print ("cud",cud)

                elif version == 6:  # .kinf2018: identical to K4PC
                    salt = str(0x6d8 * int(build)).encode('utf-8') + guid
                    sp = GetUserName() + b'+@#$%+' + IDString
                    passwd = encode(SHA256(sp), charMap5)
                    key = PBKDF2(passwd, salt, count=10000, dkLen=0x400)[:32]

                    #print ("salt",salt)
                    #print ("sp",sp)
                    #print ("passwd",passwd)
                    #print ("key",key)

               # loop through the item records until all are processed
                while len(items) > 0:

                    # get the first item record
                    item = items.pop(0)

                    # the first 32 chars of the first record of a group
                    # is the MD5 hash of the key name encoded by charMap5
                    keyhash = item[0:32]
                    keyname = b'unknown'

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
                    for i in range(rcnt):
                        item = items.pop(0)
                        edlst.append(item)

                    keyname = b'unknown'
                    for name in names:
                        if encodeHash(name,testMap8) == keyhash:
                            keyname = name
                            break
                    if keyname == b'unknown':
                        keyname = keyhash

                    # the testMap8 encoded contents data has had a length
                    # of chars (always odd) cut off of the front and moved
                    # to the end to prevent decoding using testMap8 from
                    # working properly, and thereby preventing the ensuing
                    # CryptUnprotectData call from succeeding.

                    # The offset into the testMap8 encoded contents seems to be:
                    # len(contents) - largest prime number less than or equal to int(len(content)/3)
                    # (in other words split 'about' 2/3rds of the way through)

                    # move first offsets chars to end to align for decode by testMap8
                    encdata = b''.join(edlst)
                    contlen = len(encdata)

                    # now properly split and recombine
                    # by moving noffset chars from the start of the
                    # string to the end of the string
                    noffset = contlen - primes(int(contlen/3))[-1]
                    pfx = encdata[0:noffset]
                    encdata = encdata[noffset:]
                    encdata = encdata + pfx

                    if version == 5:
                        # decode using testMap8 to get the CryptProtect Data
                        encryptedValue = decode(encdata,testMap8)
                        cleartext = cud.decrypt(encryptedValue)

                    elif version == 6:
                        # decode using new testMap8 to get IV + ciphertext
                        iv_ciphertext = decode(encdata, testMap8)
                        # pad IV so that we can substitute AES-CTR for GCM
                        iv = iv_ciphertext[:12] + b'\x00\x00\x00\x02'
                        ciphertext = iv_ciphertext[12:]
                        # convert IV to int for use with pycrypto
                        iv_ints = unpack('>QQ', iv)
                        iv = iv_ints[0] << 64 | iv_ints[1]
                        # set up AES-CTR
                        ctr = Counter.new(128, initial_value=iv)
                        cipher = AES.new(key, AES.MODE_CTR, counter=ctr)
                        # decrypt and decode
                        cleartext = decode(cipher.decrypt(ciphertext), charMap5)

                    # print keyname
                    # print cleartext
                    if len(cleartext) > 0:
                        DB[keyname] = cleartext

                if len(DB)>6:
                    break

            except Exception:
                print (traceback.format_exc())
                pass
        if len(DB)>6:
            # store values used in decryption
            print("Decrypted key file using IDString '{0:s}' and UserName '{1:s}'".format(IDString.decode('utf-8'), GetUserName().decode('utf-8')))
            DB[b'IDString'] = IDString
            DB[b'UserName'] = GetUserName()
        else:
            print("Couldn't decrypt file.")
            DB = {}
        return DB
else:
    def getDBfromFile(kInfoFile):
        raise DrmException("This script only runs under Windows or Mac OS X.")
        return {}

def kindlekeys(files = []):
    keys = []
    if files == []:
        files = getKindleInfoFiles()
    for file in files:
        key = getDBfromFile(file)
        if key:
            # convert all values to hex, just in case.
            n_key = {}
            for k,v in key.items():
                n_key[k.decode()]=codecs.encode(v, 'hex_codec').decode()
            # key = {k.decode():v.decode() for k,v in key.items()}
            keys.append(n_key)
    return keys

# interface for Python DeDRM
# returns single key or multiple keys, depending on path or file passed in
def getkey(outpath, files=[]):
    keys = kindlekeys(files)
    if len(keys) > 0:
        if not os.path.isdir(outpath):
            outfile = outpath
            with open(outfile, 'w') as keyfileout:
                keyfileout.write(json.dumps(keys[0]))
            print("Saved a key to {0}".format(outfile))
        else:
            keycount = 0
            for key in keys:
                while True:
                    keycount += 1
                    outfile = os.path.join(outpath,"kindlekey{0:d}.k4i".format(keycount))
                    if not os.path.exists(outfile):
                        break
                with open(outfile, 'w') as keyfileout:
                    keyfileout.write(json.dumps(key))
                print("Saved a key to {0}".format(outfile))
        return True
    return False

def usage(progname):
    print("Finds, decrypts and saves the default Kindle For Mac/PC encryption keys.")
    print("Keys are saved to the current directory, or a specified output directory.")
    print("If a file name is passed instead of a directory, only the first key is saved, in that file.")
    print("Usage:")
    print("    {0:s} [-h] [-k <kindle.info>] [<outpath>]".format(progname))


def cli_main():
    sys.stdout=SafeUnbuffered(sys.stdout)
    sys.stderr=SafeUnbuffered(sys.stderr)
    argv=unicode_argv()
    progname = os.path.basename(argv[0])
    print("{0} v{1}\nCopyright © 2010-2020 by some_updates, Apprentice Harper et al.".format(progname,__version__))

    try:
        opts, args = getopt.getopt(argv[1:], "hk:")
    except getopt.GetoptError as err:
        print("Error in options or arguments: {0}".format(err.args[0]))
        usage(progname)
        sys.exit(2)

    files = []
    for o, a in opts:
        if o == "-h":
            usage(progname)
            sys.exit(0)
        if o == "-k":
            files = [a]

    if len(args) > 1:
        usage(progname)
        sys.exit(2)

    if len(args) == 1:
        # save to the specified file or directory
        outpath = args[0]
        if not os.path.isabs(outpath):
           outpath = os.path.abspath(outpath)
    else:
        # save to the same directory as the script
        outpath = os.path.dirname(argv[0])

    # make sure the outpath is canonical
    outpath = os.path.realpath(os.path.normpath(outpath))

    if not getkey(outpath, files):
        print("Could not retrieve Kindle for Mac/PC key.")
    return 0


def gui_main():
    try:
        import tkinter
        import tkinter.constants
        import tkinter.messagebox
        import traceback
    except:
        return cli_main()

    class ExceptionDialog(tkinter.Frame):
        def __init__(self, root, text):
            tkinter.Frame.__init__(self, root, border=5)
            label = tkinter.Label(self, text="Unexpected error:",
                                  anchor=tkinter.constants.W, justify=tkinter.constants.LEFT)
            label.pack(fill=tkinter.constants.X, expand=0)
            self.text = tkinter.Text(self)
            self.text.pack(fill=tkinter.constants.BOTH, expand=1)

            self.text.insert(tkinter.constants.END, text)


    argv=unicode_argv()
    root = tkinter.Tk()
    root.withdraw()
    progpath, progname = os.path.split(argv[0])
    success = False
    try:
        keys = kindlekeys()
        keycount = 0
        for key in keys:
            while True:
                keycount += 1
                outfile = os.path.join(progpath,"kindlekey{0:d}.k4i".format(keycount))
                if not os.path.exists(outfile):
                    break

            with open(outfile, 'w') as keyfileout:
                keyfileout.write(json.dumps(key))
            success = True
            tkinter.messagebox.showinfo(progname, "Key successfully retrieved to {0}".format(outfile))
    except DrmException as e:
        tkinter.messagebox.showerror(progname, "Error: {0}".format(str(e)))
    except Exception:
        root.wm_state('normal')
        root.title(progname)
        text = traceback.format_exc()
        ExceptionDialog(root, text).pack(fill=tkinter.constants.BOTH, expand=1)
        root.mainloop()
    if not success:
        return 1
    return 0

if __name__ == '__main__':
    if len(sys.argv) > 1:
        sys.exit(cli_main())
    sys.exit(gui_main())
