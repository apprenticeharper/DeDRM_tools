#! /usr/bin/python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# For use with Topaz Scripts Version 2.6

import csv
import sys
import os
import getopt
from struct import pack
from struct import unpack

#
# Get a 7 bit encoded number from string
#

def readEncodedNumber(file):
    flag = False
    c = file.read(1)
    if (len(c) == 0):
        return None
    data = ord(c)
    
    if data == 0xFF:
       flag = True
       c = file.read(1)
       if (len(c) == 0):
           return None
       data = ord(c)
       
    if data >= 0x80:
        datax = (data & 0x7F)
        while data >= 0x80 :
            c = file.read(1)
            if (len(c) == 0): 
                return None
            data = ord(c)
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
  
#
# Get a length prefixed string from the file 
#
def lengthPrefixString(data):
    return encodeNumber(len(data))+data

def readString(file):
    stringLength = readEncodedNumber(file)
    if (stringLength == None):
        return None
    sv = file.read(stringLength)
    if (len(sv)  != stringLength):
        return ""
    return unpack(str(stringLength)+"s",sv)[0]  



def getMetaArray(metaFile):
    # parse the meta file into a Python dictionary (associative array)
    result = {}
    fo = file(metaFile,'rb')
    size = readEncodedNumber(fo)
    for i in xrange(size):
        temp = readString(fo)
        result[temp] = readString(fo)
    fo.close()
    return result



def getMetaData(metaFile):
    # parse the meta file
    result = ''    
    fo = file(metaFile,'rb')
    size = readEncodedNumber(fo)
    for i in xrange(size):
        result += readString(fo) + '|'
        result += readString(fo) + '\n'
    fo.close()
    return result
