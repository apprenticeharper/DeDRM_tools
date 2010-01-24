#! /usr/bin/python
# For use with Topaz Scripts Version 1.8

from __future__ import with_statement

import csv
import sys
import os
import getopt
import zlib
from struct import pack
from struct import unpack

MAX_PATH = 255

# Put the first 8 characters of your Kindle PID here
# or supply it with the -p option in the command line
####################################################
kindlePID = "12345678"
####################################################

global bookFile
global bookPayloadOffset
global bookHeaderRecords
global bookMetadata
global bookKey
global command

#
# Exceptions for all the problems that might happen during the script
#

class CMBDTCError(Exception):
    pass
    
class CMBDTCFatal(Exception):
    pass
    

#
# Open the book file at path
#

def openBook(path):
    try:
        return open(path,'rb')
    except:
        raise CMBDTCFatal("Could not open book file: " + path)

#
# Get a 7 bit encoded number from the book file
#

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
    
#
# Encode a number in 7 bit format
#

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
       if number == 0 : break
   
   if negative:
       result += chr(0xFF)
   
   return result[::-1]
  
#
# Get a length prefixed string from the file 
#

def bookReadString():
    stringLength = bookReadEncodedNumber()
    return unpack(str(stringLength)+"s",bookFile.read(stringLength))[0]  
    
#
# Returns a length prefixed string
#

def lengthPrefixString(data):
    return encodeNumber(len(data))+data
    

#
# Read and return the data of one header record at the current book file position [[offset,decompressedLength,compressedLength],...]
#
    
def bookReadHeaderRecordData():
    nbValues = bookReadEncodedNumber()
    values = []
    for i in range (0,nbValues):
        values.append([bookReadEncodedNumber(),bookReadEncodedNumber(),bookReadEncodedNumber()])
    return values
   
#
# Read and parse one header record at the current book file position and return the associated data [[offset,decompressedLength,compressedLength],...]
#

def parseTopazHeaderRecord():
    if ord(bookFile.read(1)) != 0x63:
        raise CMBDTCFatal("Parse Error : Invalid Header")
    
    tag = bookReadString()
    record = bookReadHeaderRecordData()
    return [tag,record]

#
# Parse the header of a Topaz file, get all the header records and the offset for the payload
#
 
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
        print result[0], result[1]
        bookHeaderRecords[result[0]] = result[1]
    
    if ord(bookFile.read(1))  != 0x64 :
        raise CMBDTCFatal("Parse Error : Invalid Header")
    
    bookPayloadOffset = bookFile.tell()
   
#
# Get a record in the book payload, given its name and index. If necessary the record is decrypted. The record is not decompressed
# Correction, the record is correctly decompressed too
#

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

#
# Extract, decrypt and decompress a book record indicated by name and index and print it or save it in "filename"
#

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
    
#
# return next record [key,value] from the book metadata from the current book position
#  

def readMetadataRecord():
    return [bookReadString(),bookReadString()]
    
#
# Parse the metadata record from the book payload and return a list of [key,values]
#

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

#
# Context initialisation for the Topaz Crypto
#

def topazCryptoInit(key):
    ctx1 = 0x0CAFFE19E
    
    for keyChar in key:
        keyByte = ord(keyChar)
        ctx2 = ctx1 
        ctx1 = ((((ctx1 >>2) * (ctx1 >>7))&0xFFFFFFFF) ^ (keyByte * keyByte * 0x0F902007)& 0xFFFFFFFF )
    return [ctx1,ctx2]
    
#
# decrypt data with the context prepared by topazCryptoInit()
#
    
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

#
# Decrypt a payload record with the PID
#

def decryptRecord(data,PID):
    ctx = topazCryptoInit(PID)
    return topazCryptoDecrypt(data, ctx)

#
# Try to decrypt a dkey record (contains the book PID)
#

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
    
#
# Decrypt all the book's dkey records (contain the book PID)
#
  
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
    
#
# Create decrypted book payload
#

def createDecryptedPayload(payload):
    for headerRecord in bookHeaderRecords:
       name = headerRecord
       if name != "dkey" :
           ext = '.dat'
           if name == 'img' : ext = '.jpg'
           for index in range (0,len(bookHeaderRecords[name])) :
               fnum = "%04d" % index
               fname = name + fnum + ext
               destdir = payload
               if name == 'img':
                   destdir =  os.path.join(payload,'img')
               if name == 'page':
                   destdir =  os.path.join(payload,'page')
               if name == 'glyphs':
                   destdir =  os.path.join(payload,'glyphs')
               outputFile = os.path.join(destdir,fname)
               file(outputFile, 'wb').write(getBookPayloadRecord(name, index))
                   

# Create decrypted book
#

def createDecryptedBook(outdir):
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    destdir =  os.path.join(outdir,'img')
    if not os.path.exists(destdir):
        os.makedirs(destdir)

    destdir =  os.path.join(outdir,'page')
    if not os.path.exists(destdir):
        os.makedirs(destdir)

    destdir =  os.path.join(outdir,'glyphs')
    if not os.path.exists(destdir):
        os.makedirs(destdir)

    createDecryptedPayload(outdir)


#
# Set the command to execute by the programm according to cmdLine parameters
#

def setCommand(name) :
    global command
    if command != "" :
         raise CMBDTCFatal("Invalid command line parameters")
    else :
        command = name

# 
# Program usage
#
   
def usage():
    print("\nUsage:")
    print("\ncmbtc_dump_linux.py [options] bookFileName\n")
    print("-p Adds a PID to the list of PIDs that are tried to decrypt the book key (can be used several times)")
    print("-d Dumps the unencrypted book as files to outdir")
    print("-o Output directory to save book files to")
    print("-v Verbose (can be used several times)")

 
#
# Main
#   

def main(argv=sys.argv):
    global bookMetadata
    global bookKey
    global bookFile
    global command
    
    progname = os.path.basename(argv[0])
    
    verbose = 0
    recordName = ""
    recordIndex = 0
    outdir = ""
    PIDs = []
    command = ""
    
    # Preloads your Kindle pid from the top of the program.
    PIDs.append(kindlePID)
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "vo:p:d")
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
        if o =="-o":
            if a == None :
                raise CMBDTCFatal("Invalid parameter for -o")
            outdir = a
        if o =="-p":
            PIDs.append(a)
        if o =="-d":
            setCommand("doit")
            
    if command == "" :
        raise CMBDTCFatal("No action supplied on command line")
   
    #
    # Open book and parse metadata
    #
        
    if len(args) == 1:
    
        bookFile = openBook(args[0])
        parseTopazHeader()
        parseMetadata()
    
    #
    #  Decrypt book key
    #
    
        dkey = getBookPayloadRecord('dkey', 0) 
        
        bookKeys = []
        for PID in PIDs :
            bookKeys+=decryptDkeyRecords(dkey,PID)
            
        if len(bookKeys) == 0 :
            if verbose > 0 :
                print ("Book key could not be found. Maybe this book is not registered with this device.")
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
                    if verbose >0 :
                        print ("Decrypted book saved. Don't pirate!")
                elif verbose > 0:
                    print("Output directory name was not supplied.")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
