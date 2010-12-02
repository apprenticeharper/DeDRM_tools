#!/usr/bin/env python
# For use with Topaz Scripts Version 2.6

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

import csv
import os
import getopt
import zlib
from struct import pack
from struct import unpack
import traceback
import hashlib

MAX_PATH = 255

global bookFile
global bookPayloadOffset
global bookHeaderRecords
global bookMetadata
global bookKey
global command
global kindleDatabase
global verbose
global PIDs

if sys.platform.startswith('win'):
    from k4pcutils import openKindleInfo, CryptUnprotectData, GetUserName, GetVolumeSerialNumber, charMap1, charMap2, charMap3, charMap4
if sys.platform.startswith('darwin'):
    from k4mutils import openKindleInfo, CryptUnprotectData, GetUserName, GetVolumeSerialNumber, charMap1, charMap2, charMap3, charMap4



# Exceptions for all the problems that might happen during the script
class CMBDTCError(Exception):
    pass
    
class CMBDTCFatal(Exception):
    pass
    

# Returns the MD5 digest of "message"
def MD5(message):
    ctx = hashlib.md5()
    ctx.update(message)
    return ctx.digest()


# Returns the MD5 digest of "message"
def SHA1(message):
    ctx = hashlib.sha1()
    ctx.update(message)
    return ctx.digest()


# Open the book file at path
def openBook(path):
    try:
        return open(path,'rb')
    except:
        raise CMBDTCFatal("Could not open book file: " + path)

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

# Get a 7 bit encoded number from the book file
def bookReadEncodedNumber():
    flag = False
    data = ord(bookFile.read(1))
    
    if data == 0xFF:
       flag = True
       data = ord(bookFile.read(1))
       
    if data >= 0x80:
        datax = (data & 0x7F)
        while data >= 0x80 :
            data = ord(bookFile.read(1))
            datax = (datax <<7) + (data & 0x7F)
        data = datax 
    
    if flag:
       data = -data
    return data
    
# Encode a number in 7 bit format
def encodeNumber(number):
   result = ""
   negative = False
   flag = 0
   print("Using encodeNumber routine")
   
   if number < 0 :
       number = -number + 1
       negative = True
   
   while True:
       byte = number & 0x7F
       number = number >> 7
       byte += flag
       result += chr(byte)
       flag = 0x80
       if number == 0 :
           if (byte == 0xFF and negative == False) :
               result += chr(0x80)
           break
   
   if negative:
       result += chr(0xFF)
   
   return result[::-1]
  

# Get a length prefixed string from the file 
def bookReadString():
    stringLength = bookReadEncodedNumber()
    return unpack(str(stringLength)+"s",bookFile.read(stringLength))[0]  
    
# Returns a length prefixed string
def lengthPrefixString(data):
    return encodeNumber(len(data))+data
    
# Read and return the data of one header record at the current book file position [[offset,decompressedLength,compressedLength],...]
def bookReadHeaderRecordData():
    nbValues = bookReadEncodedNumber()
    values = []
    for i in range (0,nbValues):
        values.append([bookReadEncodedNumber(),bookReadEncodedNumber(),bookReadEncodedNumber()])
    return values
   
# Read and parse one header record at the current book file position and return the associated data [[offset,decompressedLength,compressedLength],...]
def parseTopazHeaderRecord():
    if ord(bookFile.read(1)) != 0x63:
        raise CMBDTCFatal("Parse Error : Invalid Header")
    
    tag = bookReadString()
    record = bookReadHeaderRecordData()
    return [tag,record]

# Parse the header of a Topaz file, get all the header records and the offset for the payload
def parseTopazHeader():
    global bookHeaderRecords
    global bookPayloadOffset
    magic = unpack("4s",bookFile.read(4))[0]
    
    if magic != 'TPZ0':
        raise CMBDTCFatal("Parse Error : Invalid Header, not a Topaz file")
        
    nbRecords = bookReadEncodedNumber()
    bookHeaderRecords = {}
   
    for i in range (0,nbRecords):
        result = parseTopazHeaderRecord()
        #print result[0], result[1]
        bookHeaderRecords[result[0]] = result[1]
    
    if ord(bookFile.read(1))  != 0x64 :
        raise CMBDTCFatal("Parse Error : Invalid Header")
    
    bookPayloadOffset = bookFile.tell()
   
# Get a record in the book payload, given its name and index. If necessary the record is decrypted. The record is not decompressed
# Correction, the record is correctly decompressed too
def getBookPayloadRecord(name, index):   
    encrypted = False
    compressed = False

    try: 
        recordOffset = bookHeaderRecords[name][index][0]
    except:
        raise CMBDTCFatal("Parse Error : Invalid Record, record not found")
    
    bookFile.seek(bookPayloadOffset + recordOffset)
    
    tag = bookReadString()
    if tag != name :
        raise CMBDTCFatal("Parse Error : Invalid Record, record name doesn't match")
    
    recordIndex = bookReadEncodedNumber()
    
    if recordIndex < 0 :
        encrypted = True
        recordIndex = -recordIndex -1
    
    if recordIndex != index :
      raise CMBDTCFatal("Parse Error : Invalid Record, index doesn't match")
            
    if (bookHeaderRecords[name][index][2] > 0):
        compressed = True
        record = bookFile.read(bookHeaderRecords[name][index][2])
    else:
        record = bookFile.read(bookHeaderRecords[name][index][1])
 
    if encrypted:
       ctx = topazCryptoInit(bookKey)
       record = topazCryptoDecrypt(record,ctx)

    if compressed:
        record = zlib.decompress(record)
    
    return record

# Extract, decrypt and decompress a book record indicated by name and index and print it or save it in "filename"
def extractBookPayloadRecord(name, index, filename):
    compressed = False

    try:
        compressed = bookHeaderRecords[name][index][2] != 0
        record = getBookPayloadRecord(name,index)
    except:
        print("Could not find record")
    
    # if compressed:
    #    try:
    #        record = zlib.decompress(record)
    #    except:
    #        raise CMBDTCFatal("Could not decompress record")
            
    if filename != "":
        try:
            file = open(filename,"wb")
            file.write(record)
            file.close()
        except:
            raise CMBDTCFatal("Could not write to destination file")
    else:
        print(record)
    
# return next record [key,value] from the book metadata from the current book position
def readMetadataRecord():
    return [bookReadString(),bookReadString()]
    
# Parse the metadata record from the book payload and return a list of [key,values]
def parseMetadata():
    global bookHeaderRecords
    global bookPayloadAddress
    global bookMetadata
    bookMetadata = {}
    bookFile.seek(bookPayloadOffset + bookHeaderRecords["metadata"][0][0])
    tag = bookReadString()
    if tag != "metadata" :
        raise CMBDTCFatal("Parse Error : Record Names Don't Match")
    
    flags = ord(bookFile.read(1))
    nbRecords = ord(bookFile.read(1))
    
    for i in range (0,nbRecords) :
        record =readMetadataRecord()
        bookMetadata[record[0]] = record[1]

# Context initialisation for the Topaz Crypto
def topazCryptoInit(key):
    ctx1 = 0x0CAFFE19E
    
    for keyChar in key:
        keyByte = ord(keyChar)
        ctx2 = ctx1 
        ctx1 = ((((ctx1 >>2) * (ctx1 >>7))&0xFFFFFFFF) ^ (keyByte * keyByte * 0x0F902007)& 0xFFFFFFFF )
    return [ctx1,ctx2]
    
# decrypt data with the context prepared by topazCryptoInit()
def topazCryptoDecrypt(data, ctx):
    ctx1 = ctx[0]
    ctx2 = ctx[1]
    
    plainText = ""
    
    for dataChar in data:
        dataByte = ord(dataChar)
        m = (dataByte ^ ((ctx1 >> 3) &0xFF) ^ ((ctx2<<3) & 0xFF)) &0xFF
        ctx2 = ctx1
        ctx1 = (((ctx1 >> 2) * (ctx1 >> 7)) &0xFFFFFFFF) ^((m * m * 0x0F902007) &0xFFFFFFFF)
        plainText += chr(m)
        
    return plainText

# Decrypt a payload record with the PID
def decryptRecord(data,PID):
    ctx = topazCryptoInit(PID)
    return topazCryptoDecrypt(data, ctx)

# Try to decrypt a dkey record (contains the book PID)
def decryptDkeyRecord(data,PID):
    record = decryptRecord(data,PID)
    fields = unpack("3sB8sB8s3s",record)
    
    if fields[0] != "PID" or fields[5] != "pid" :
        raise CMBDTCError("Didn't find PID magic numbers in record")
    elif fields[1] != 8 or fields[3] != 8 :
        raise CMBDTCError("Record didn't contain correct length fields")
    elif fields[2] != PID :
        raise CMBDTCError("Record didn't contain PID")
    
    return fields[4]

# Decrypt all the book's dkey records (contain the book PID)
def decryptDkeyRecords(data,PID):
    nbKeyRecords = ord(data[0])
    records = []
    data = data[1:]
    for i in range (0,nbKeyRecords):
        length = ord(data[0])
        try:
            key = decryptDkeyRecord(data[1:length+1],PID)
            records.append(key)
        except CMBDTCError:
            pass
        data = data[1+length:]
        
    return records
    
# Create decrypted book payload
def createDecryptedPayload(payload):
    for headerRecord in bookHeaderRecords:
       name = headerRecord
       if name != "dkey" :
           ext = '.dat'
           if name == 'img' : ext = '.jpg'
           if name == 'color' : ext = '.jpg'
           for index in range (0,len(bookHeaderRecords[name])) :
               fnum = "%04d" % index
               fname = name + fnum + ext
               destdir = payload
               if name == 'img':
                   destdir =  os.path.join(payload,'img')
               if name == 'color':
                   destdir =  os.path.join(payload,'color_img')
               if name == 'page':
                   destdir =  os.path.join(payload,'page')
               if name == 'glyphs':
                   destdir =  os.path.join(payload,'glyphs')
               outputFile = os.path.join(destdir,fname)
               file(outputFile, 'wb').write(getBookPayloadRecord(name, index))
                   
# Create decrypted book
def createDecryptedBook(outdir):
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    destdir =  os.path.join(outdir,'img')
    if not os.path.exists(destdir):
        os.makedirs(destdir)

    destdir =  os.path.join(outdir,'color_img')
    if not os.path.exists(destdir):
        os.makedirs(destdir)

    destdir =  os.path.join(outdir,'page')
    if not os.path.exists(destdir):
        os.makedirs(destdir)

    destdir =  os.path.join(outdir,'glyphs')
    if not os.path.exists(destdir):
        os.makedirs(destdir)

    createDecryptedPayload(outdir)

# Set the command to execute by the programm according to cmdLine parameters
def setCommand(name) :
    global command
    if command != "" :
         raise CMBDTCFatal("Invalid command line parameters")
    else :
        command = name

# Program usage
def usage():
    print("\nUsage:")
    print("\ncmbtc_dump_linux.py [options] bookFileName\n")
    print("-p Adds a PID to the list of PIDs that are tried to decrypt the book key (can be used several times)")
    print("-d Dumps the unencrypted book as files to outdir")
    print("-o Output directory to save book files to")
    print("-v Verbose (can be used several times)")
    print("-i Prints kindle.info database")
    print("-k Adds the path to an alternate kindle.info file")
    
def prepTopazBook(bookPath):
    global bookFile
    bookFile = openBook(bookPath)
    parseTopazHeader()
    parseMetadata() 

# Get Pids
def getK4Pids(kInfoFile=None):
    global kindleDatabase
    global PIDs
    
    # Read the encrypted database
    kindleDatabase = None
    try:
        kindleDatabase = parseKindleInfo(kInfoFile)
    except Exception, message:
        #if verbose > 0:
        #    print(message)
        pass
    
    if kindleDatabase != None :
        # Compute the DSN
        # Get the Mazama Random number
        MazamaRandomNumber = getKindleInfoValueForKey("MazamaRandomNumber")
    
        # Get the HDD serial
        encodedSystemVolumeSerialNumber = encodeHash(GetVolumeSerialNumber(),charMap1)
    
        # Get the current user name
        encodedUsername = encodeHash(GetUserName(),charMap1)
    
        # concat, hash and encode
        DSN = encode(SHA1(MazamaRandomNumber+encodedSystemVolumeSerialNumber+encodedUsername),charMap1)
       
        if verbose > 0:
            print("DSN: " + DSN)
        
        # Compute the device PID    
        table =  generatePidEncryptionTable()
        devicePID = generateDevicePID(table,DSN,4)
        PIDs.append(devicePID)
    
        if verbose > 0:
            print("Device PID: " + devicePID)
        
        # Compute book PID
        # Get the account token
        kindleAccountToken = getKindleInfoValueForKey("kindle.account.tokens")
    
        if verbose > 0:
            print("Account Token: " + kindleAccountToken)

            keysRecord = bookMetadata["keys"]
            keysRecordRecord = bookMetadata[keysRecord]
    
            pidHash = SHA1(DSN+kindleAccountToken+keysRecord+keysRecordRecord)
   
            bookPID = encodePID(pidHash)
            PIDs.append(bookPID)
    
            if verbose > 0:
                print ("Book PID: " + bookPID )

# Main
def main(argv=sys.argv):
    global verbose
    global PIDs
    global bookKey
    global command
    
    progname = os.path.basename(argv[0])
    
    verbose = 0
    recordName = ""
    recordIndex = 0
    outdir = ""
    PIDs = []
    command = ""
    kInfoFiles = []
    
  
    try:
        opts, args = getopt.getopt(sys.argv[1:], "vi:k:o:p:d")
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    
    if len(opts) == 0 and len(args) == 0 :
        usage()
        sys.exit(2) 
       
    for o, a in opts:
        if o == "-v":
            verbose+=1
        if o == "-i":
            setCommand("printInfo")
        if o == "-k":
            if a == None :
                raise CMBDTCFatal("Invalid parameter for -k")
            kInfoFiles.append(a)
        if o =="-o":
            if a == None :
                raise CMBDTCFatal("Invalid parameter for -o")
            outdir = a
        if o =="-p":
            if a == None :
                raise CMBDTCFatal("Invalid parameter for -p")
            PIDs.append(a)
        if o =="-d":
            setCommand("doit")
            
    if command == "" :
        raise Exception("No action supplied on command line")
        
    # Open book and parse metadata
    if len(args) == 1:
        # Open the ebook
        prepTopazBook(args[0])
        # Always try to get the default Kindle installation info.
        getK4Pids()
        
        # If Alternate kindle.info files were supplied, parse them too.
        if kInfoFiles:
            for infoFile in kInfoFiles:
                getK4Pids(infoFile)
        
        # Print the kindle info if requested.        
        if kindleDatabase != None :        
            if command == "printInfo" :
                printKindleInfo()
                
        # Remove any duplicates that may occur from the PIDs List
        PIDs = list(set(PIDs))
        
        #  Decrypt book key
        dkey = getBookPayloadRecord('dkey', 0)
        
        bookKeys = []
        for PID in PIDs :
            print PID
            bookKeys+=decryptDkeyRecords(dkey,PID)
            
        if len(bookKeys) == 0 :
            if verbose > 0 :
                print ("Book key could not be found. Maybe this book is not registered with this device.")
                return 1
        else :
            bookKey = bookKeys[0]
            if verbose > 0:
                print("Book key: " + bookKey.encode('hex'))
                  
            if command == "printRecord" :
                extractBookPayloadRecord(recordName,int(recordIndex),outputFile)
                if outputFile != "" and verbose>0 :
                    print("Wrote record to file: "+outputFile) 
            elif command == "doit" :
                if outdir != "" :
                    createDecryptedBook(outdir)
                    if verbose > 0 :
                        print ("Decrypted book saved. Don't pirate!")
                elif verbose > 0:
                    print("Output directory name was not supplied.")
                    return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
