#!/usr/bin/env python

# engine to remove drm from Kindle for Mac and Kindle for PC books
# for personal use for archiving and converting your ebooks

# PLEASE DO NOT PIRATE EBOOKS! 

# We want all authors and publishers, and eBook stores to live
# long and prosperous lives but at the same time  we just want to 
# be able to read OUR books on whatever device we want and to keep 
# readable for a long, long time

#  This borrows very heavily from works by CMBDTC, IHeartCabbages, skindle, 
#    unswindle, DarkReverser, ApprenticeAlf, DiapDealer, some_updates 
#    and many many others

# It can run standalone to convert K4M/K4PC/Mobi files, or it can be installed as a
# plugin for Calibre (http://calibre-ebook.com/about) so that importing
# K4 or Mobi with DRM is no londer a multi-step process.
#
# ***NOTE*** If you are using this script as a calibre plugin for a K4M or K4PC ebook
# then calibre must be installed on the same machine and in the same account as K4PC or K4M
# for the plugin version to function properly.
#
# To create a Calibre plugin, rename this file so that the filename
# ends in '_plugin.py', put it into a ZIP file with all its supporting python routines
# and import that ZIP into Calibre using its plugin configuration GUI.

from __future__ import with_statement

__version__ = '1.1'

class Unbuffered:
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

import sys
import os, csv, getopt
import binascii
import zlib
import re
from struct import pack, unpack, unpack_from


#Exception Handling
class DrmException(Exception):
    pass

#
# crypto digestroutines
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

# determine if we are running as a calibre plugin
if 'calibre' in sys.modules:
    inCalibre = True
    global openKindleInfo, CryptUnprotectData, GetUserName, GetVolumeSerialNumber, charMap1, charMap2, charMap3, charMap4
else:
    inCalibre = False

#
# start of Kindle specific routines
#

if not inCalibre:
    import mobidedrm
    if sys.platform.startswith('win'):
        from k4pcutils import openKindleInfo, CryptUnprotectData, GetUserName, GetVolumeSerialNumber, charMap1, charMap2, charMap3, charMap4
    if sys.platform.startswith('darwin'):
        from k4mutils import openKindleInfo, CryptUnprotectData, GetUserName, GetVolumeSerialNumber, charMap1, charMap2, charMap3, charMap4

global kindleDatabase

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


# Parse the Kindle.info file and return the records as a list of key-values
def parseKindleInfo(kInfoFile):
    DB = {}
    infoReader = openKindleInfo(kInfoFile)
    infoReader.read(1)
    data = infoReader.read()
    if sys.platform.startswith('win'):
        items = data.split('{')
    else :
        items = data.split('[')
    for item in items:
        splito = item.split(':')
        DB[splito[0]] =splito[1]
    return DB

# Get a record from the Kindle.info file for the key "hashedKey" (already hashed and encoded). Return the decoded and decrypted record
def getKindleInfoValueForHash(hashedKey):
    global kindleDatabase
    encryptedValue = decode(kindleDatabase[hashedKey],charMap2)
    if sys.platform.startswith('win'):
        return CryptUnprotectData(encryptedValue,"")
    else:
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

# Encryption table used to generate the device PID
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

# Seed value used to generate the device PID
def generatePidSeed(table,dsn) :
    value = 0
    for counter in range (0,4) :
       index = (ord(dsn[counter]) ^ value) &0xFF
       value = (value >> 8) ^ table[index]
    return value

# Generate the device PID
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

# convert from 8 digit PID to 10 digit PID with checksum
def checksumPid(s):
    letters = "ABCDEFGHIJKLMNPQRSTUVWXYZ123456789"
    crc = (~binascii.crc32(s,-1))&0xFFFFFFFF
    crc = crc ^ (crc >> 16)
    res = s
    l = len(letters)
    for i in (0,1):
        b = crc & 0xff
        pos = (b // l) ^ (b % l)
        res += letters[pos%l]
        crc >>= 8
    return res


class MobiPeek:
    def loadSection(self, section):
        before, after = self.sections[section:section+2]
        self.f.seek(before)
        return self.f.read(after - before)
    def __init__(self, filename):
        self.f = file(filename, 'rb')
        self.header = self.f.read(78)
        self.ident = self.header[0x3C:0x3C+8]
        if self.ident != 'BOOKMOBI' and self.ident != 'TEXtREAd':
            raise DrmException('invalid file format')
        self.num_sections, = unpack_from('>H', self.header, 76)
        sections = self.f.read(self.num_sections*8)
        self.sections = unpack_from('>%dL' % (self.num_sections*2), sections, 0)[::2] + (0xfffffff, )
        self.sect0 = self.loadSection(0)
        self.f.close()
    def getBookTitle(self):
        # get book title
        toff, tlen = unpack('>II', self.sect0[0x54:0x5c])
        tend = toff + tlen
        title = self.sect0[toff:tend]
        return title
    def getexthData(self):
        # if exth region exists then grab it
        # get length of this header
        length, type, codepage, unique_id, version = unpack('>LLLLL', self.sect0[20:40])
        exth_flag, = unpack('>L', self.sect0[0x80:0x84])
        exth = ''
        if exth_flag & 0x40:
            exth = self.sect0[16 + length:]
        return exth
    def isNotEncrypted(self):
        lock_type, = unpack('>H', self.sect0[0xC:0xC+2])
        if lock_type == 0:
            return True
        return False

# DiapDealer's stuff: Parse the EXTH header records and parse the Kindleinfo
# file to calculate the book pid.
def getK4Pids(exth, title, kInfoFile=None):
    global kindleDatabase
    try:
        kindleDatabase = parseKindleInfo(kInfoFile)
    except Exception as message:
        print(message)
    
    if kindleDatabase != None :
        # Get the Mazama Random number
        MazamaRandomNumber = getKindleInfoValueForKey("MazamaRandomNumber")

        # Get the HDD serial
        encodedSystemVolumeSerialNumber = encodeHash(GetVolumeSerialNumber(),charMap1)

        # Get the current user name
        encodedUsername = encodeHash(GetUserName(),charMap1)

        # concat, hash and encode to calculate the DSN
        DSN = encode(SHA1(MazamaRandomNumber+encodedSystemVolumeSerialNumber+encodedUsername),charMap1)
       
        print("\nDSN: " + DSN)

        # Compute the device PID (for which I can tell, is used for nothing).
        # But hey, stuff being printed out is apparently cool.
        table =  generatePidEncryptionTable()
        devicePID = generateDevicePID(table,DSN,4)
            
        print("Device PID: " + checksumPid(devicePID))
            
        # Compute book PID
        exth_records = {}
        nitems, = unpack('>I', exth[8:12])
        pos = 12
        # Parse the exth records, storing data indexed by type
        for i in xrange(nitems):
            type, size = unpack('>II', exth[pos: pos + 8])
            content = exth[pos + 8: pos + size]

            exth_records[type] = content
            pos += size

        # Grab the contents of the type 209 exth record
        if exth_records[209] != None:
            data = exth_records[209]
        else:
            raise DrmException("\nNo EXTH record type 209 - Perhaps not a K4 file?")
        
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
        bookPID = checksumPid(bookPID)

        if exth_records[503] != None:
            print "Pid for " + exth_records[503] + ": " + bookPID
        else:
            print "Pid for " + title + ":" + bookPID
        return bookPID
    
    raise DrmException("\nCould not access K4 data - Perhaps K4 is not installed/configured?")
    return null

def usage(progname):
    print "Removes DRM protection from K4PC, K4M, and Mobi ebooks"
    print "Usage:"
    print "    %s [-k <kindle.info>] [-p <pidnums>] <infile> <outfile>  " % progname

#
# Main
#   
def main(argv=sys.argv):
    global kindleDatabase
    import mobidedrm
    
    progname = os.path.basename(argv[0])
    kInfoFiles = []
    pidnums = ""
    
    print ('K4MobiDeDrm v%(__version__)s '
	   'provided by the work of many including DiapDealer, SomeUpdates, IHeartCabbages, CMBDTC, Skindle, DarkReverser, ApprenticeAlf, etc .' % globals())

    try:
        opts, args = getopt.getopt(sys.argv[1:], "k:p:")
    except getopt.GetoptError, err:
        print str(err)
        usage(progname)
        sys.exit(2)
        
    if len(args)<2:
        usage(progname)
        sys.exit(2)
        
    for o, a in opts:
        if o == "-k":
            if a == None :
                raise DrmException("Invalid parameter for -k")
            kInfoFiles.append(a)
        if o == "-p":
            if a == None :
                raise DrmException("Invalid parameter for -p")
            pidnums = a

    kindleDatabase = None
    infile = args[0]
    outfile = args[1]
    try:
        # first try with K4PC/K4M
        ex = MobiPeek(infile)
        if ex.isNotEncrypted():
            print "File was Not Encrypted"
            return 2
        title = ex.getBookTitle()
        exth = ex.getexthData()
        pid = getK4Pids(exth, title)
        unlocked_file = mobidedrm.getUnencryptedBook(infile, pid)
    except DrmException:
        pass
    except mobidedrm.DrmException:
        pass
    else:
        file(outfile, 'wb').write(unlocked_file)
        return 0
    
    # now try alternate kindle.info files
    if kInfoFiles:
        for infoFile in kInfoFiles:
            kindleDatabase = None
            try:
                title = ex.getBookTitle()
                exth = ex.getexthData()
                pid = getK4Pids(exth, title, infoFile)
                unlocked_file = mobidedrm.getUnencryptedBook(infile, pid)
            except DrmException:
                pass
            except mobidedrm.DrmException:
                pass
            else:
                file(outfile, 'wb').write(unlocked_file)
                return 0            
    
    # Lastly, try from the pid list
    pids = pidnums.split(',')
    for pid in pids:
        try:
            print 'Trying: "'+ pid + '"'
            unlocked_file = mobidedrm.getUnencryptedBook(infile, pid)
        except mobidedrm.DrmException:
            pass
        else:
            file(outfile, 'wb').write(unlocked_file)
            return 0

    # we could not unencrypt book
    print "Error: Could Not Unencrypt Book"
    return 1


if __name__ == '__main__':
    sys.stdout=Unbuffered(sys.stdout)
    sys.exit(main())


if not __name__ == "__main__" and inCalibre:
    from calibre.customize import FileTypePlugin

    class K4DeDRM(FileTypePlugin):
        name                = 'K4PC, K4Mac, Mobi DeDRM' # Name of the plugin
        description         = 'Removes DRM from K4PC, K4Mac, and Mobi files. \
                                Provided by the work of many including DiapDealer, SomeUpdates, IHeartCabbages, CMBDTC, Skindle, DarkReverser, ApprenticeAlf, etc.'
        supported_platforms = ['osx', 'windows', 'linux'] # Platforms this plugin will run on
        author              = 'DiapDealer, SomeUpdates' # The author of this plugin
        version             = (0, 1, 1)   # The version number of this plugin
        file_types          = set(['prc','mobi','azw']) # The file types that this plugin will be applied to
        on_import           = True # Run this plugin during the import
        priority            = 200  # run this plugin before mobidedrm, k4pcdedrm, k4dedrm

        def run(self, path_to_ebook):
            from calibre.gui2 import is_ok_to_use_qt
            from PyQt4.Qt import QMessageBox
            global kindleDatabase
            global openKindleInfo, CryptUnprotectData, GetUserName, GetVolumeSerialNumber, charMap1, charMap2, charMap3, charMap4
            if sys.platform.startswith('win'):
                from k4pcutils import openKindleInfo, CryptUnprotectData, GetUserName, GetVolumeSerialNumber, charMap1, charMap2, charMap3, charMap4
            if sys.platform.startswith('darwin'):
                from k4mutils import openKindleInfo, CryptUnprotectData, GetUserName, GetVolumeSerialNumber, charMap1, charMap2, charMap3, charMap4
            import mobidedrm

            # Get supplied list of PIDs to try from plugin customization.
            pidnums = self.site_customization
            
            # Load any kindle info files (*.info) included Calibre's config directory.
            kInfoFiles = []
            try:
                # Find Calibre's configuration directory.
                confpath = os.path.split(os.path.split(self.plugin_path)[0])[0]
                print 'K4MobiDeDRM: Calibre configuration directory = %s' % confpath
                files = os.listdir(confpath)
                filefilter = re.compile("\.info$", re.IGNORECASE)
                files = filter(filefilter.search, files)
    
                if files:
                    for filename in files:
                        fpath = os.path.join(confpath, filename)
                        kInfoFiles.append(fpath)
                        print 'K4MobiDeDRM: Kindle info file %s found in config folder.' % filename
            except IOError:
                print 'K4MobiDeDRM: Error reading kindle info files from config directory.'
                pass

            # first try with book specifc pid from K4PC or K4M
            try:
                kindleDatabase = None
                ex = MobiPeek(path_to_ebook)
                if ex.isNotEncrypted():
                    return path_to_ebook
                title = ex.getBookTitle()
                exth = ex.getexthData()
                pid = getK4Pids(exth, title)
                unlocked_file = mobidedrm.getUnencryptedBook(path_to_ebook,pid)
            except DrmException:
                pass
            except mobidedrm.DrmException:
                pass
            else:
                of = self.temporary_file('.mobi')
                of.write(unlocked_file)
                of.close()
                return of.name
            
            # Now try alternate kindle info files
            if kInfoFiles:
                for infoFile in kInfoFiles:
                    kindleDatabase = None 
                    try:
                        title = ex.getBookTitle()
                        exth = ex.getexthData()
                        pid = getK4Pids(exth, title, infoFile)
                        unlocked_file = mobidedrm.getUnencryptedBook(path_to_ebook,pid)
                    except DrmException:
                        pass
                    except mobidedrm.DrmException:
                        pass
                    else:
                        of = self.temporary_file('.mobi')
                        of.write(unlocked_file)
                        of.close()
                        return of.name            

            # now try from the pid list
            pids = pidnums.split(',')
            for pid in pids:
                try:
                    unlocked_file = mobidedrm.getUnencryptedBook(path_to_ebook, pid)
                except mobidedrm.DrmException:
                    pass
                else:
                    of = self.temporary_file('.mobi')
                    of.write(unlocked_file)
                    of.close()
                    return of.name

            #if you reached here then no luck raise and exception
            if is_ok_to_use_qt():
                d = QMessageBox(QMessageBox.Warning, "K4MobiDeDRM Plugin", "Error decoding: %s\n" % path_to_ebook)
                d.show()
                d.raise_()
                d.exec_()
            raise Exception("K4MobiDeDRM plugin could not decode the file")
            return ""

        def customization_help(self, gui=False):
            return 'Enter each 10 character PID separated by a comma (no spaces).'
