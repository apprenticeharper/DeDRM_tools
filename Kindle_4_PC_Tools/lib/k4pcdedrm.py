#!/usr/bin/env python
#
# This is a WINDOWS python script. You need a Python interpreter to run it.
# For example, ActiveState Python, which exists for windows.
#
# It can run standalone to convert K4PC files, or it can be installed as a
# plugin for Calibre (http://calibre-ebook.com/about) so that importing
# K4PC files with DRM is no londer a multi-step process.
#
# ***NOTE*** Calibre and K4PC must be installed on the same windows machine
# for the plugin version to function properly.
#
# To create a Calibre plugin, rename this file so that the filename
# ends in '_plugin.py', put it into a ZIP file and import that ZIP into Calibre
# using its plugin configuration GUI.
#
# Thanks to The Dark Reverser for MobiDeDrm and CMBDTC for cmbdtc_dump from
# which this script steals most unashamedly.
#
# Changelog
#  0.01 - Initial version - Utilizes skindle and CMBDTC method of obtaining
#         book specific pids from K4PC books. If Calibre and K4PC are installed
#         on the same windows machine, Calibre plugin functionality is once
#         again restored.


"""

Comprehensive Mazama Book DRM with Topaz Cryptography V2.0

-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDdBHJ4CNc6DNFCw4MRCw4SWAK6
M8hYfnNEI0yQmn5Ti+W8biT7EatpauE/5jgQMPBmdNrDr1hbHyHBSP7xeC2qlRWC
B62UCxeu/fpfnvNHDN/wPWWH4jynZ2M6cdcnE5LQ+FfeKqZn7gnG2No1U9h7oOHx
y2/pHuYme7U1TsgSjwIDAQAB
-----END PUBLIC KEY-----

"""

from __future__ import with_statement

import csv
import sys
import os
import getopt
import zlib
import binascii
from struct import pack
from struct import unpack
from ctypes import windll, c_char_p, c_wchar_p, c_uint, POINTER, byref, \
    create_unicode_buffer, create_string_buffer, CFUNCTYPE, addressof, \
    string_at, Structure, c_void_p, cast
import _winreg as winreg
import traceback
import hashlib

__version__ = '0.01'

global kindleDatabase
MAX_PATH = 255
kernel32 = windll.kernel32
advapi32 = windll.advapi32
crypt32 = windll.crypt32


#
# Various character maps used to decrypt books. Probably supposed to act as obfuscation
#
charMap1 = "n5Pr6St7Uv8Wx9YzAb0Cd1Ef2Gh3Jk4M"
charMap2 = "AaZzB0bYyCc1XxDdW2wEeVv3FfUuG4g-TtHh5SsIiR6rJjQq7KkPpL8lOoMm9Nn_"
charMap3 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
charMap4 = "ABCDEFGHIJKLMNPQRSTUVWXYZ123456789"


#
# Exceptions for all the problems that might happen during the script
#
class DrmException(Exception):
    pass
    

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
    def GetVolumeSerialNumber(path):
        vsn = c_uint(0)
        GetVolumeInformationW(path, None, 0, byref(vsn), None, None, None, 0)
        return vsn.value
    return GetVolumeSerialNumber
GetVolumeSerialNumber = GetVolumeSerialNumber()


def GetUserName():
    GetUserNameW = advapi32.GetUserNameW
    GetUserNameW.argtypes = [c_wchar_p, POINTER(c_uint)]
    GetUserNameW.restype = c_uint
    def GetUserName():
        buffer = create_unicode_buffer(32)
        size = c_uint(len(buffer))
        while not GetUserNameW(buffer, byref(size)):
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
    def CryptUnprotectData(indata, entropy):
        indatab = create_string_buffer(indata)
        indata = DataBlob(len(indata), cast(indatab, c_void_p))
        entropyb = create_string_buffer(entropy)
        entropy = DataBlob(len(entropy), cast(entropyb, c_void_p))
        outdata = DataBlob()
        if not _CryptUnprotectData(byref(indata), None, byref(entropy),
                                   None, None, 0, byref(outdata)):
            raise DrmException("Failed to Unprotect Data")
        return string_at(outdata.pbData, outdata.cbData)
    return CryptUnprotectData
CryptUnprotectData = CryptUnprotectData()


#
# Returns the MD5 digest of "message"
#
def MD5(message):
    ctx = hashlib.md5()
    ctx.update(message)
    return ctx.digest()


#
# Returns the MD5 digest of "message"
#
def SHA1(message):
    ctx = hashlib.sha1()
    ctx.update(message)
    return ctx.digest()


#
# Locate and open the Kindle.info file.
#
def openKindleInfo():
    regkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Folders\\")
    path = winreg.QueryValueEx(regkey, 'Local AppData')[0] 
    return open(path+'\\Amazon\\Kindle For PC\\{AMAwzsaPaaZAzmZzZQzgZCAkZ3AjA_AY}\\kindle.info','r')


#
# Parse the Kindle.info file and return the records as a list of key-values
#
def parseKindleInfo():
    DB = {}
    infoReader = openKindleInfo()
    infoReader.read(1)
    data = infoReader.read()
    items = data.split('{')
    
    for item in items:
        splito = item.split(':')
        DB[splito[0]] =splito[1]
    return DB


#
# Find if the original string for a hashed/encoded string is known. If so return the original string othwise return an empty string. (Totally not optimal)
#
def findNameForHash(hash):
    names = ["kindle.account.tokens","kindle.cookie.item","eulaVersionAccepted","login_date","kindle.token.item","login","kindle.key.item","kindle.name.info","kindle.device.info", "MazamaRandomNumber"]
    result = ""
    for name in names:
        if hash == encodeHash(name, charMap2):
           result = name
           break
    return name

    
#
# Print all the records from the kindle.info file.
#
def printKindleInfo():
    for record in kindleDatabase:
        name = findNameForHash(record)
        if name != "" :
            print (name)
            print ("--------------------------\n")
        else :
            print ("Unknown Record")
        print getKindleInfoValueForHash(record)
        print "\n"


#
# Get a record from the Kindle.info file for the key "hashedKey" (already hashed and encoded). Return the decoded and decrypted record
#
def getKindleInfoValueForHash(hashedKey):
    global kindleDatabase
    encryptedValue = decode(kindleDatabase[hashedKey],charMap2)
    return CryptUnprotectData(encryptedValue,"")


#
#  Get a record from the Kindle.info file for the string in "key" (plaintext). Return the decoded and decrypted record
#
def getKindleInfoValueForKey(key):
    return getKindleInfoValueForHash(encodeHash(key,charMap2))


#
# 8 bits to six bits encoding from hash to generate PID string
#  
def encodePID(hash):
    global charMap3
    PID = ""
    for position in range (0,8):
        PID += charMap3[getSixBitsFromBitField(hash,position)]
    return PID


#
# Hash the bytes in data and then encode the digest with the characters in map
#
def encodeHash(data,map):
    return encode(MD5(data),map)

   
#
# Encode the bytes in data with the characters in map
#
def encode(data, map):
    result = ""
    for char in data:
        value = ord(char)
        Q = (value ^ 0x80) // len(map)
        R = value % len(map)
        result += map[Q]
        result += map[R]
    return result


#
# Decode the string in data with the characters in map. Returns the decoded bytes
#
def decode(data,map):
    result = ""
    for i in range (0,len(data),2):
        high = map.find(data[i])
        low = map.find(data[i+1])
        value = (((high * 0x40) ^ 0x80) & 0xFF) + low
        result += pack("B",value)
    return result


#
# Encryption table used to generate the device PID
#
def generatePidEncryptionTable() :
    table = []
    for counter1 in range (0,0x100):
        value = counter1
        for counter2 in range (0,8):
            if (value & 1 == 0) :
                value = value >> 1
            else :
                value = value >> 1
                value = value ^ 0xEDB88320
        table.append(value)
    return table


#
# Seed value used to generate the device PID
#
def generatePidSeed(table,dsn) :
    value = 0
    for counter in range (0,4) :
       index = (ord(dsn[counter]) ^ value) &0xFF
       value = (value >> 8) ^ table[index]
    return value

   
#
# Generate the device PID
#
def generateDevicePID(table,dsn,nbRoll):
    seed = generatePidSeed(table,dsn)
    pidAscii = ""
    pid = [(seed >>24) &0xFF,(seed >> 16) &0xff,(seed >> 8) &0xFF,(seed) & 0xFF,(seed>>24) & 0xFF,(seed >> 16) &0xff,(seed >> 8) &0xFF,(seed) & 0xFF]
    index = 0
    
    for counter in range (0,nbRoll):
        pid[index] = pid[index] ^ ord(dsn[counter])
        index = (index+1) %8
 
    for counter in range (0,8):
        index = ((((pid[counter] >>5) & 3) ^ pid[counter]) & 0x1f) + (pid[counter] >> 7)
        pidAscii += charMap4[index]
    return pidAscii


#
# Returns two bit at offset from a bit field
#
def getTwoBitsFromBitField(bitField,offset):
    byteNumber = offset // 4
    bitPosition = 6 - 2*(offset % 4)
    
    return ord(bitField[byteNumber]) >> bitPosition & 3


#
# Returns the six bits at offset from a bit field
#    
def getSixBitsFromBitField(bitField,offset):
    offset *= 3
    value = (getTwoBitsFromBitField(bitField,offset) <<4) + (getTwoBitsFromBitField(bitField,offset+1) << 2) +getTwoBitsFromBitField(bitField,offset+2)
    return value


#
# MobiDeDrm-0.16 Stuff
#
class Unbuffered:
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)


# Implementation of Pukall Cipher 1
def PC1(key, src, decryption=True):
    sum1 = 0;
    sum2 = 0;
    keyXorVal = 0;
    if len(key)!=16:
        print "Bad key length!"
        return None
    wkey = []
    for i in xrange(8):
        wkey.append(ord(key[i*2])<<8 | ord(key[i*2+1]))

    dst = ""
    for i in xrange(len(src)):
        temp1 = 0;
        byteXorVal = 0;
        for j in xrange(8):
            temp1 ^= wkey[j]
            sum2  = (sum2+j)*20021 + sum1
            sum1  = (temp1*346)&0xFFFF
            sum2  = (sum2+sum1)&0xFFFF
            temp1 = (temp1*20021+1)&0xFFFF
            byteXorVal ^= temp1 ^ sum2
        curByte = ord(src[i])
        if not decryption:
            keyXorVal = curByte * 257;
        curByte = ((curByte ^ (byteXorVal >> 8)) ^ byteXorVal) & 0xFF
        if decryption:
            keyXorVal = curByte * 257;
        for j in xrange(8):
            wkey[j] ^= keyXorVal;
        dst+=chr(curByte)
    return dst


def getSizeOfTrailingDataEntries(ptr, size, flags):
    def getSizeOfTrailingDataEntry(ptr, size):
        bitpos, result = 0, 0
        if size <= 0:
            return result
        while True:
            v = ord(ptr[size-1])
            result |= (v & 0x7F) << bitpos
            bitpos += 7
            size -= 1
            if (v & 0x80) != 0 or (bitpos >= 28) or (size == 0):
                return result
    num = 0
    testflags = flags >> 1
    while testflags:
        if testflags & 1:
            num += getSizeOfTrailingDataEntry(ptr, size - num)
        testflags >>= 1
    # Multibyte data, if present, is included in the encryption, so
    # we do not need to check the low bit.
    # if flags & 1:
    #    num += (ord(ptr[size - num - 1]) & 0x3) + 1
    return num


#
# This class does all the heavy lifting.
#
class DrmStripper:
    def loadSection(self, section):
        if (section + 1 == self.num_sections):
            endoff = len(self.data_file)
        else:
            endoff = self.sections[section + 1][0]
        off = self.sections[section][0]
        return self.data_file[off:endoff]

    def patch(self, off, new):
        self.data_file = self.data_file[:off] + new + self.data_file[off+len(new):]

    def patchSection(self, section, new, in_off = 0):
        if (section + 1 == self.num_sections):
            endoff = len(self.data_file)
        else:
            endoff = self.sections[section + 1][0]
        off = self.sections[section][0]
        assert off + in_off + len(new) <= endoff
        self.patch(off + in_off, new)

    def parseDRM(self, data, count, pid):
        pid = pid.ljust(16,'\0')
        keyvec1 = "\x72\x38\x33\xB0\xB4\xF2\xE3\xCA\xDF\x09\x01\xD6\xE2\xE0\x3F\x96"
        temp_key = PC1(keyvec1, pid, False)
        temp_key_sum = sum(map(ord,temp_key)) & 0xff
        found_key = None
        for i in xrange(count):
            verification, size, type, cksum, cookie = unpack('>LLLBxxx32s', data[i*0x30:i*0x30+0x30])
            cookie = PC1(temp_key, cookie)
            ver,flags,finalkey,expiry,expiry2 = unpack('>LL16sLL', cookie)
            if verification == ver and cksum == temp_key_sum and (flags & 0x1F) == 1:
                found_key = finalkey
                break
        if not found_key:
            # Then try the default encoding that doesn't require a PID
            temp_key = keyvec1
            temp_key_sum = sum(map(ord,temp_key)) & 0xff
            for i in xrange(count):
                verification, size, type, cksum, cookie = unpack('>LLLBxxx32s', data[i*0x30:i*0x30+0x30])
                cookie = PC1(temp_key, cookie)
                ver,flags,finalkey,expiry,expiry2 = unpack('>LL16sLL', cookie)
                if verification == ver and cksum == temp_key_sum:
                    found_key = finalkey
                    break
        return found_key

    def __init__(self, data_file):
        self.data_file = data_file
        header = data_file[0:72]
        if header[0x3C:0x3C+8] != 'BOOKMOBI':
            raise DrmException("invalid file format")
        self.num_sections, = unpack('>H', data_file[76:78])

        self.sections = []
        for i in xrange(self.num_sections):
            offset, a1,a2,a3,a4 = unpack('>LBBBB', data_file[78+i*8:78+i*8+8])
            flags, val = a1, a2<<16|a3<<8|a4
            self.sections.append( (offset, flags, val) )

        sect = self.loadSection(0)
        records, = unpack('>H', sect[0x8:0x8+2])
        mobi_length, = unpack('>L',sect[0x14:0x18])
        mobi_version, = unpack('>L',sect[0x68:0x6C])
        extra_data_flags = 0
        print "MOBI header version = %d, length = %d" %(mobi_version, mobi_length)
        if (mobi_length >= 0xE4) and (mobi_version >= 5):
            extra_data_flags, = unpack('>H', sect[0xF2:0xF4])
            print "Extra Data Flags = %d" %extra_data_flags

        crypto_type, = unpack('>H', sect[0xC:0xC+2])
        if crypto_type == 0:
            print "This book is not encrypted."
        else:
            if crypto_type == 1:
                raise DrmException("cannot decode Mobipocket encryption type 1")
            if crypto_type != 2:
                raise DrmException("unknown encryption type: %d" % crypto_type)

            # determine the EXTH Offset.
            exth_off = unpack('>I', sect[20:24])[0] + 16 + self.sections[0][0]
            # Grab the entire EXTH block and feed it to the getK4PCPids function.
            exth = data_file[exth_off:self.sections[0+1][0]]
            pid = getK4PCPids(exth)

            # calculate the keys
            drm_ptr, drm_count, drm_size, drm_flags = unpack('>LLLL', sect[0xA8:0xA8+16])
            if drm_count == 0:
                raise DrmException("no PIDs found in this file")
            found_key = self.parseDRM(sect[drm_ptr:drm_ptr+drm_size], drm_count, pid)
            if not found_key:
                raise DrmException("no key found. maybe the PID is incorrect")

            # kill the drm keys
            self.patchSection(0, "\0" * drm_size, drm_ptr)
            # kill the drm pointers
            self.patchSection(0, "\xff" * 4 + "\0" * 12, 0xA8)
            # clear the crypto type
            self.patchSection(0, "\0" * 2, 0xC)

            # decrypt sections
            print "\nDecrypting. Please wait . . .",
            new_data = self.data_file[:self.sections[1][0]]
            for i in xrange(1, records+1):
                data = self.loadSection(i)
                extra_size = getSizeOfTrailingDataEntries(data, len(data), extra_data_flags)
                if i%100 == 0:
                    print ".",
                # print "record %d, extra_size %d" %(i,extra_size)
                new_data += PC1(found_key, data[0:len(data) - extra_size])
                if extra_size > 0:
                    new_data += data[-extra_size:]
                #self.patchSection(i, PC1(found_key, data[0:len(data) - extra_size]))
            if self.num_sections > records+1:
                new_data += self.data_file[self.sections[records+1][0]:]
            self.data_file = new_data
            print "done!"
            print "\nPlease only use your new-found powers for good."

    def getResult(self):
        return self.data_file


#
# DiapDealer's stuff: Parse the EXTH header records and parse the Kindleinfo
# file to calculate the book pid.
#
def getK4PCPids(exth):
    global kindleDatabase
    try:
        kindleDatabase = parseKindleInfo()
    except Exception as message:
        print(message)
    
    if kindleDatabase != None :
  
        # Get the Mazama Random number
        MazamaRandomNumber = getKindleInfoValueForKey("MazamaRandomNumber")
    
        # Get the HDD serial
        encodedSystemVolumeSerialNumber = encodeHash(str(GetVolumeSerialNumber(GetSystemDirectory().split('\\')[0] + '\\')),charMap1)
    
        # Get the current user name
        encodedUsername = encodeHash(GetUserName(),charMap1)
    
        # concat, hash and encode to calculate the DSN
        DSN = encode(SHA1(MazamaRandomNumber+encodedSystemVolumeSerialNumber+encodedUsername),charMap1)
       
        print("\nDSN: " + DSN)
    

        # Compute the device PID (for which I can tell, is used for nothing).
        # But hey, stuff being printed out is apparently cool.
        table =  generatePidEncryptionTable()
        devicePID = generateDevicePID(table,DSN,4)
            
        print("Device PID: " + devicePID)
            
        # Compute book PID
        exth_records = {}
        nitems, = unpack('>I', exth[8:12])
        pos = 12
        # Parse the EXTH records, storing data indexed by type
        for i in xrange(nitems):
            type, size = unpack('>II', exth[pos: pos + 8])
            content = exth[pos + 8: pos + size]

            exth_records[type] = content
            pos += size

        # Grab the contents of the type 209 exth record
        if exth_records[209] != None:
            data = exth_records[209]
        else:
            raise DrmException("\nNo EXTH record type 209 - Perhaps not a K4PC file?")
        
        # Parse the 209 data to find the the exth record with the token data.
        # The last character of the 209 data points to the record with the token.
        # Always 208 from my experience, but I'll leave the logic in case that changes.
        for i in xrange(len(data)):
            if ord(data[i]) != 0:
                if exth_records[ord(data[i])] != None:
                    token = exth_records[ord(data[i])]

        # Get the kindle account token
        kindleAccountToken = getKindleInfoValueForKey("kindle.account.tokens")
    
        print("Account Token: " + kindleAccountToken)

        pidHash = SHA1(DSN+kindleAccountToken+exth_records[209]+token)
   
        bookPID = encodePID(pidHash)

        if exth_records[503] != None:
            print "Pid for " + exth_records[503] + ": " + bookPID
        else:
            print ("Book PID: " + bookPID )
            
        return bookPID
    
    raise DrmException("\nCould not access K4PC data - Perhaps K4PC is not installed/configured?")
    return null

if not __name__ == "__main__":
    from calibre.customize import FileTypePlugin

    class K4PCDeDRM(FileTypePlugin):
        name                = 'K4PCDeDRM' # Name of the plugin
        description         = 'Removes DRM from K4PC files'
        supported_platforms = ['windows'] # Platforms this plugin will run on
        author              = 'DiapDealer' # The author of this plugin
        version             = (0, 0, 1)   # The version number of this plugin
        file_types          = set(['prc','mobi','azw']) # The file types that this plugin will be applied to
        on_import           = True # Run this plugin during the import

        def run(self, path_to_ebook):
            from calibre.gui2 import is_ok_to_use_qt
            from PyQt4.Qt import QMessageBox
            data_file = file(path_to_ebook, 'rb').read()

            try:
                unlocked_file = DrmStripper(data_file).getResult()
            except DrmException:
                # ignore the error
                pass
            else:
                of = self.temporary_file('.mobi')
                of.write(unlocked_file)
                of.close()
                return of.name

            if is_ok_to_use_qt():
                d = QMessageBox(QMessageBox.Warning, "K4PCDeDRM Plugin", "Couldn't decode: %s\n\nImporting encrypted version." % path_to_ebook)
                d.show()
                d.raise_()
                d.exec_()
            return path_to_ebook

        #def customization_help(self, gui=False):
        #    return 'Enter PID (separate multiple PIDs with comma)'

if __name__ == "__main__":
    sys.stdout=Unbuffered(sys.stdout)
    print ('K4PCDeDrm v%(__version__)s '
	   'provided DiapDealer.' % globals())
    if len(sys.argv)<3:
        print "Removes DRM protection from K4PC books"
        print "Usage:"
        print "    %s <infile> <outfile>" % sys.argv[0]
        sys.exit(1)
    else:
        infile = sys.argv[1]
        outfile = sys.argv[2]
        data_file = file(infile, 'rb').read()
        try:
            strippedFile = DrmStripper(data_file)
            file(outfile, 'wb').write(strippedFile.getResult())
        except DrmException, e:
            print "Error: %s" % e
            sys.exit(1)
    sys.exit(0)