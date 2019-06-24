#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement
from __future__ import print_function

# kgenpids.py
# Copyright © 2008-2017 Apprentice Harper et al.

__license__ = 'GPL v3'
__version__ = '2.1'

# Revision history:
#  2.0   - Fix for non-ascii Windows user names
#  2.1   - Actual fix for non-ascii WIndows user names.
#  x.x   - Return information needed for KFX decryption

import sys
import os, csv
import binascii
import zlib
import re
from struct import pack, unpack, unpack_from
import traceback

class DrmException(Exception):
    pass

global charMap1
global charMap3
global charMap4


charMap1 = 'n5Pr6St7Uv8Wx9YzAb0Cd1Ef2Gh3Jk4M'
charMap3 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
charMap4 = 'ABCDEFGHIJKLMNPQRSTUVWXYZ123456789'

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


# Encode the bytes in data with the characters in map
def encode(data, map):
    result = ''
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
    result = ''
    for i in range (0,len(data)-1,2):
        high = map.find(data[i])
        low = map.find(data[i+1])
        if (high == -1) or (low == -1) :
            break
        value = (((high * len(map)) ^ 0x80) & 0xFF) + low
        result += pack('B',value)
    return result

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
    PID = ''
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
    global charMap4
    seed = generatePidSeed(table,dsn)
    pidAscii = ''
    pid = [(seed >>24) &0xFF,(seed >> 16) &0xff,(seed >> 8) &0xFF,(seed) & 0xFF,(seed>>24) & 0xFF,(seed >> 16) &0xff,(seed >> 8) &0xFF,(seed) & 0xFF]
    index = 0
    for counter in range (0,nbRoll):
        pid[index] = pid[index] ^ ord(dsn[counter])
        index = (index+1) %8
    for counter in range (0,8):
        index = ((((pid[counter] >>5) & 3) ^ pid[counter]) & 0x1f) + (pid[counter] >> 7)
        pidAscii += charMap4[index]
    return pidAscii

def crc32(s):
    return (~binascii.crc32(s,-1))&0xFFFFFFFF

# convert from 8 digit PID to 10 digit PID with checksum
def checksumPid(s):
    global charMap4
    crc = crc32(s)
    crc = crc ^ (crc >> 16)
    res = s
    l = len(charMap4)
    for i in (0,1):
        b = crc & 0xff
        pos = (b // l) ^ (b % l)
        res += charMap4[pos%l]
        crc >>= 8
    return res


# old kindle serial number to fixed pid
def pidFromSerial(s, l):
    global charMap4
    crc = crc32(s)
    arr1 = [0]*l
    for i in xrange(len(s)):
        arr1[i%l] ^= ord(s[i])
    crc_bytes = [crc >> 24 & 0xff, crc >> 16 & 0xff, crc >> 8 & 0xff, crc & 0xff]
    for i in xrange(l):
        arr1[i] ^= crc_bytes[i&3]
    pid = ""
    for i in xrange(l):
        b = arr1[i] & 0xff
        pid+=charMap4[(b >> 7) + ((b >> 5 & 3) ^ (b & 0x1f))]
    return pid


# Parse the EXTH header records and use the Kindle serial number to calculate the book pid.
def getKindlePids(rec209, token, serialnum):
    if rec209 is None:
        return [serialnum]

    pids=[]

    if isinstance(serialnum,unicode):
        serialnum = serialnum.encode('utf-8')

    # Compute book PID
    pidHash = SHA1(serialnum+rec209+token)
    bookPID = encodePID(pidHash)
    bookPID = checksumPid(bookPID)
    pids.append(bookPID)

    # compute fixed pid for old pre 2.5 firmware update pid as well
    kindlePID = pidFromSerial(serialnum, 7) + "*"
    kindlePID = checksumPid(kindlePID)
    pids.append(kindlePID)

    return pids


# parse the Kindleinfo file to calculate the book pid.

keynames = ['kindle.account.tokens','kindle.cookie.item','eulaVersionAccepted','login_date','kindle.token.item','login','kindle.key.item','kindle.name.info','kindle.device.info', 'MazamaRandomNumber']

def getK4Pids(rec209, token, kindleDatabase):
    global charMap1
    pids = []

    try:
        # Get the kindle account token, if present
        kindleAccountToken = (kindleDatabase[1])['kindle.account.tokens'].decode('hex')

    except KeyError:
        kindleAccountToken=""
        pass

    try:
        # Get the DSN token, if present
        DSN = (kindleDatabase[1])['DSN'].decode('hex')
        print(u"Got DSN key from database {0}".format(kindleDatabase[0]))
    except KeyError:
        # See if we have the info to generate the DSN
        try:
            # Get the Mazama Random number
            MazamaRandomNumber = (kindleDatabase[1])['MazamaRandomNumber'].decode('hex')
            #print u"Got MazamaRandomNumber from database {0}".format(kindleDatabase[0])

            try:
                # Get the SerialNumber token, if present
                IDString = (kindleDatabase[1])['SerialNumber'].decode('hex')
                print(u"Got SerialNumber from database {0}".format(kindleDatabase[0]))
            except KeyError:
                 # Get the IDString we added
                IDString = (kindleDatabase[1])['IDString'].decode('hex')

            try:
                # Get the UsernameHash token, if present
                encodedUsername = (kindleDatabase[1])['UsernameHash'].decode('hex')
                print(u"Got UsernameHash from database {0}".format(kindleDatabase[0]))
            except KeyError:
                # Get the UserName we added
                UserName = (kindleDatabase[1])['UserName'].decode('hex')
                # encode it
                encodedUsername = encodeHash(UserName,charMap1)
                #print u"encodedUsername",encodedUsername.encode('hex')
        except KeyError:
            print(u"Keys not found in the database {0}.".format(kindleDatabase[0]))
            return pids

        # Get the ID string used
        encodedIDString = encodeHash(IDString,charMap1)
        #print u"encodedIDString",encodedIDString.encode('hex')

        # concat, hash and encode to calculate the DSN
        DSN = encode(SHA1(MazamaRandomNumber+encodedIDString+encodedUsername),charMap1)
        #print u"DSN",DSN.encode('hex')
        pass

    if rec209 is None:
        pids.append(DSN+kindleAccountToken)
        return pids

    # Compute the device PID (for which I can tell, is used for nothing).
    table =  generatePidEncryptionTable()
    devicePID = generateDevicePID(table,DSN,4)
    devicePID = checksumPid(devicePID)
    pids.append(devicePID)

    # Compute book PIDs

    # book pid
    pidHash = SHA1(DSN+kindleAccountToken+rec209+token)
    bookPID = encodePID(pidHash)
    bookPID = checksumPid(bookPID)
    pids.append(bookPID)

    # variant 1
    pidHash = SHA1(kindleAccountToken+rec209+token)
    bookPID = encodePID(pidHash)
    bookPID = checksumPid(bookPID)
    pids.append(bookPID)

    # variant 2
    pidHash = SHA1(DSN+rec209+token)
    bookPID = encodePID(pidHash)
    bookPID = checksumPid(bookPID)
    pids.append(bookPID)

    return pids

def getPidList(md1, md2, serials=[], kDatabases=[]):
    pidlst = []

    if kDatabases is None:
        kDatabases = []
    if serials is None:
        serials = []

    for kDatabase in kDatabases:
        try:
            pidlst.extend(getK4Pids(md1, md2, kDatabase))
        except Exception, e:
            print(u"Error getting PIDs from database {0}: {1}".format(kDatabase[0],e.args[0]))
            traceback.print_exc()

    for serialnum in serials:
        try:
            pidlst.extend(getKindlePids(md1, md2, serialnum))
        except Exception, e:
            print(u"Error getting PIDs from serial number {0}: {1}".format(serialnum ,e.args[0]))
            traceback.print_exc()

    return pidlst
