#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# kindlekey.py
# Copyright © 2008-2020 Apprentice Harper et al.

__license__ = 'GPL v3'
__version__ = '3.0'

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


"""
Retrieve Kindle for PC/Mac user key.
"""

import sys, os, re
import codecs
from struct import pack, unpack, unpack_from
import json
import getopt
import traceback

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
        if isinstance(data, str):
            data = data.encode(self.encoding,"replace")
        self.stream.buffer.write(data)
        self.stream.buffer.flush()

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
        return [arg if isinstance(arg, str) else str(arg, argvencoding) for arg in sys.argv]

class DrmException(Exception):
    pass

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

# Routines unique to Mac and PC
if iswindows:
    from ctypes import windll, c_char_p, c_wchar_p, c_uint, POINTER, byref, \
        create_unicode_buffer, create_string_buffer, CFUNCTYPE, addressof, \
        string_at, Structure, c_void_p, cast

    import winreg
    MAX_PATH = 255
    kernel32 = windll.kernel32
    advapi32 = windll.advapi32
    crypt32 = windll.crypt32

    try:
        # try to get fast routines from alfcrypto
        from alfcrypto import AES_CBC, KeyIVGen
    except:
        # alfcrypto not available, so use python implementations
        """
            Routines for doing AES CBC in one file

            Modified by some_updates to extract
            and combine only those parts needed for AES CBC
            into one simple to add python file

            Original Version
            Copyright (c) 2002 by Paul A. Lambert
            Under:
            CryptoPy Artistic License Version 1.0
            See the wonderful pure python package cryptopy-1.2.5
            and read its LICENSE.txt for complete license details.
        """

        class CryptoError(Exception):
            """ Base class for crypto exceptions """
            def __init__(self,errorMessage='Error!'):
                self.message = errorMessage
            def __str__(self):
                return self.message

        class InitCryptoError(CryptoError):
            """ Crypto errors during algorithm initialization """
        class BadKeySizeError(InitCryptoError):
            """ Bad key size error """
        class EncryptError(CryptoError):
            """ Error in encryption processing """
        class DecryptError(CryptoError):
            """ Error in decryption processing """
        class DecryptNotBlockAlignedError(DecryptError):
            """ Error in decryption processing """

        def xor(a,b):
            """ XOR two byte arrays, to lesser length """
            x = []
            for i in range(min(len(a),len(b))):
                x.append( a[i] ^ b[i])
            return bytes(x)

        """
            Base 'BlockCipher' and Pad classes for cipher instances.
            BlockCipher supports automatic padding and type conversion. The BlockCipher
            class was written to make the actual algorithm code more readable and
            not for performance.
        """

        class BlockCipher:
            """ Block ciphers """
            def __init__(self):
                self.reset()

            def reset(self):
                self.resetEncrypt()
                self.resetDecrypt()
            def resetEncrypt(self):
                self.encryptBlockCount = 0
                self.bytesToEncrypt = b''
            def resetDecrypt(self):
                self.decryptBlockCount = 0
                self.bytesToDecrypt = b''

            def encrypt(self, plainText, more = None):
                """ Encrypt a string and return a binary string """
                self.bytesToEncrypt += plainText  # append plainText to any bytes from prior encrypt
                numBlocks, numExtraBytes = divmod(len(self.bytesToEncrypt), self.blockSize)
                cipherText = ''
                for i in range(numBlocks):
                    bStart = i*self.blockSize
                    ctBlock = self.encryptBlock(self.bytesToEncrypt[bStart:bStart+self.blockSize])
                    self.encryptBlockCount += 1
                    cipherText += ctBlock
                if numExtraBytes > 0:        # save any bytes that are not block aligned
                    self.bytesToEncrypt = self.bytesToEncrypt[-numExtraBytes:]
                else:
                    self.bytesToEncrypt = ''

                if more == None:   # no more data expected from caller
                    finalBytes = self.padding.addPad(self.bytesToEncrypt,self.blockSize)
                    if len(finalBytes) > 0:
                        ctBlock = self.encryptBlock(finalBytes)
                        self.encryptBlockCount += 1
                        cipherText += ctBlock
                    self.resetEncrypt()
                return cipherText

            def decrypt(self, cipherText, more = None):
                """ Decrypt a string and return a string """
                self.bytesToDecrypt += cipherText  # append to any bytes from prior decrypt

                numBlocks, numExtraBytes = divmod(len(self.bytesToDecrypt), self.blockSize)
                if more == None:  # no more calls to decrypt, should have all the data
                    if numExtraBytes  != 0:
                        raise DecryptNotBlockAlignedError('Data not block aligned on decrypt')

                # hold back some bytes in case last decrypt has zero len
                if (more != None) and (numExtraBytes == 0) and (numBlocks >0) :
                    numBlocks -= 1
                    numExtraBytes = self.blockSize

                plainText = b''
                for i in range(numBlocks):
                    bStart = i*self.blockSize
                    ptBlock = self.decryptBlock(self.bytesToDecrypt[bStart : bStart+self.blockSize])
                    self.decryptBlockCount += 1
                    plainText += ptBlock

                if numExtraBytes > 0:        # save any bytes that are not block aligned
                    self.bytesToEncrypt = self.bytesToEncrypt[-numExtraBytes:]
                else:
                    self.bytesToEncrypt = ''

                if more == None:         # last decrypt remove padding
                    plainText = self.padding.removePad(plainText, self.blockSize)
                    self.resetDecrypt()
                return plainText


        class Pad:
            def __init__(self):
                pass              # eventually could put in calculation of min and max size extension

        class padWithPadLen(Pad):
            """ Pad a binary string with the length of the padding """

            def addPad(self, extraBytes, blockSize):
                """ Add padding to a binary string to make it an even multiple
                    of the block size """
                blocks, numExtraBytes = divmod(len(extraBytes), blockSize)
                padLength = blockSize - numExtraBytes
                return extraBytes + padLength*chr(padLength)

            def removePad(self, paddedBinaryString, blockSize):
                """ Remove padding from a binary string """
                if not(0<len(paddedBinaryString)):
                    raise DecryptNotBlockAlignedError('Expected More Data')
                return paddedBinaryString[:-ord(paddedBinaryString[-1])]

        class noPadding(Pad):
            """ No padding. Use this to get ECB behavior from encrypt/decrypt """

            def addPad(self, extraBytes, blockSize):
                """ Add no padding """
                return extraBytes

            def removePad(self, paddedBinaryString, blockSize):
                """ Remove no padding """
                return paddedBinaryString

        """
            Rijndael encryption algorithm
            This byte oriented implementation is intended to closely
            match FIPS specification for readability.  It is not implemented
            for performance.
        """

        class Rijndael(BlockCipher):
            """ Rijndael encryption algorithm """
            def __init__(self, key = None, padding = padWithPadLen(), keySize=16, blockSize=16 ):
                self.name       = 'RIJNDAEL'
                self.keySize    = keySize
                self.strength   = keySize*8
                self.blockSize  = blockSize  # blockSize is in bytes
                self.padding    = padding    # change default to noPadding() to get normal ECB behavior

                assert( keySize%4==0 and (keySize//4) in NrTable[4]),'key size must be 16,20,24,29 or 32 bytes'
                assert( blockSize%4==0 and (blockSize//4) in NrTable), 'block size must be 16,20,24,29 or 32 bytes'

                self.Nb = self.blockSize//4          # Nb is number of columns of 32 bit words
                self.Nk = keySize//4                 # Nk is the key length in 32-bit words
                self.Nr = NrTable[self.Nb][self.Nk] # The number of rounds (Nr) is a function of
                                                    # the block (Nb) and key (Nk) sizes.
                if key != None:
                    self.setKey(key)

            def setKey(self, key):
                """ Set a key and generate the expanded key """
                assert( len(key) == (self.Nk*4) ), 'Key length must be same as keySize parameter'
                self.__expandedKey = keyExpansion(self, key)
                self.reset()                   # BlockCipher.reset()

            def encryptBlock(self, plainTextBlock):
                """ Encrypt a block, plainTextBlock must be a array of bytes [Nb by 4] """
                self.state = self._toBlock(plainTextBlock)
                AddRoundKey(self, self.__expandedKey[0:self.Nb])
                for round in range(1,self.Nr):          #for round = 1 step 1 to Nr
                    SubBytes(self)
                    ShiftRows(self)
                    MixColumns(self)
                    AddRoundKey(self, self.__expandedKey[round*self.Nb:(round+1)*self.Nb])
                SubBytes(self)
                ShiftRows(self)
                AddRoundKey(self, self.__expandedKey[self.Nr*self.Nb:(self.Nr+1)*self.Nb])
                return self._toBString(self.state)


            def decryptBlock(self, encryptedBlock):
                """ decrypt a block (array of bytes) """
                self.state = self._toBlock(encryptedBlock)
                AddRoundKey(self, self.__expandedKey[self.Nr*self.Nb:(self.Nr+1)*self.Nb])
                for round in range(self.Nr-1,0,-1):
                    InvShiftRows(self)
                    InvSubBytes(self)
                    AddRoundKey(self, self.__expandedKey[round*self.Nb:(round+1)*self.Nb])
                    InvMixColumns(self)
                InvShiftRows(self)
                InvSubBytes(self)
                AddRoundKey(self, self.__expandedKey[0:self.Nb])
                return self._toBString(self.state)

            def _toBlock(self, bs):
                """ Convert binary string to array of bytes, state[col][row]"""
                assert ( len(bs) == 4*self.Nb ), 'Rijndarl blocks must be of size blockSize'
                return [[bs[4*i],bs[4*i+1],bs[4*i+2],bs[4*i+3]] for i in range(self.Nb)]

            def _toBString(self, block):
                """ Convert block (array of bytes) to binary string """
                l = []
                for col in block:
                    for rowElement in col:
                        l.append(rowElement)
                return bytes(l)
        #-------------------------------------
        """    Number of rounds Nr = NrTable[Nb][Nk]

                    Nb  Nk=4   Nk=5   Nk=6   Nk=7   Nk=8
                    -------------------------------------   """
        NrTable =  {4: {4:10,  5:11,  6:12,  7:13,  8:14},
                    5: {4:11,  5:11,  6:12,  7:13,  8:14},
                    6: {4:12,  5:12,  6:12,  7:13,  8:14},
                    7: {4:13,  5:13,  6:13,  7:13,  8:14},
                    8: {4:14,  5:14,  6:14,  7:14,  8:14}}
        #-------------------------------------
        def keyExpansion(algInstance, keyArray):
            """ Expand a byte array of size keySize into a larger array """
            Nk, Nb, Nr = algInstance.Nk, algInstance.Nb, algInstance.Nr # for readability
            w = [[keyArray[4*i],keyArray[4*i+1],keyArray[4*i+2],keyArray[4*i+3]] for i in range(Nk)]
            for i in range(Nk,Nb*(Nr+1)):
                temp = w[i-1]        # a four byte column
                if (i%Nk) == 0 :
                    temp     = temp[1:]+[temp[0]]  # RotWord(temp)
                    temp     = [ Sbox[byte] for byte in temp ]
                    temp[0] ^= Rcon[i//Nk]
                elif Nk > 6 and  i%Nk == 4 :
                    temp     = [ Sbox[byte] for byte in temp ]  # SubWord(temp)
                w.append( [ w[i-Nk][byte]^temp[byte] for byte in range(4) ] )
            return w

        Rcon = (0,0x01,0x02,0x04,0x08,0x10,0x20,0x40,0x80,0x1b,0x36,     # note extra '0' !!!
                0x6c,0xd8,0xab,0x4d,0x9a,0x2f,0x5e,0xbc,0x63,0xc6,
                0x97,0x35,0x6a,0xd4,0xb3,0x7d,0xfa,0xef,0xc5,0x91)

        #-------------------------------------
        def AddRoundKey(algInstance, keyBlock):
            """ XOR the algorithm state with a block of key material """
            for column in range(algInstance.Nb):
                for row in range(4):
                    algInstance.state[column][row] ^= keyBlock[column][row]
        #-------------------------------------

        def SubBytes(algInstance):
            for column in range(algInstance.Nb):
                for row in range(4):
                    algInstance.state[column][row] = Sbox[algInstance.state[column][row]]

        def InvSubBytes(algInstance):
            for column in range(algInstance.Nb):
                for row in range(4):
                    algInstance.state[column][row] = InvSbox[algInstance.state[column][row]]

        Sbox =    (0x63,0x7c,0x77,0x7b,0xf2,0x6b,0x6f,0xc5,
                   0x30,0x01,0x67,0x2b,0xfe,0xd7,0xab,0x76,
                   0xca,0x82,0xc9,0x7d,0xfa,0x59,0x47,0xf0,
                   0xad,0xd4,0xa2,0xaf,0x9c,0xa4,0x72,0xc0,
                   0xb7,0xfd,0x93,0x26,0x36,0x3f,0xf7,0xcc,
                   0x34,0xa5,0xe5,0xf1,0x71,0xd8,0x31,0x15,
                   0x04,0xc7,0x23,0xc3,0x18,0x96,0x05,0x9a,
                   0x07,0x12,0x80,0xe2,0xeb,0x27,0xb2,0x75,
                   0x09,0x83,0x2c,0x1a,0x1b,0x6e,0x5a,0xa0,
                   0x52,0x3b,0xd6,0xb3,0x29,0xe3,0x2f,0x84,
                   0x53,0xd1,0x00,0xed,0x20,0xfc,0xb1,0x5b,
                   0x6a,0xcb,0xbe,0x39,0x4a,0x4c,0x58,0xcf,
                   0xd0,0xef,0xaa,0xfb,0x43,0x4d,0x33,0x85,
                   0x45,0xf9,0x02,0x7f,0x50,0x3c,0x9f,0xa8,
                   0x51,0xa3,0x40,0x8f,0x92,0x9d,0x38,0xf5,
                   0xbc,0xb6,0xda,0x21,0x10,0xff,0xf3,0xd2,
                   0xcd,0x0c,0x13,0xec,0x5f,0x97,0x44,0x17,
                   0xc4,0xa7,0x7e,0x3d,0x64,0x5d,0x19,0x73,
                   0x60,0x81,0x4f,0xdc,0x22,0x2a,0x90,0x88,
                   0x46,0xee,0xb8,0x14,0xde,0x5e,0x0b,0xdb,
                   0xe0,0x32,0x3a,0x0a,0x49,0x06,0x24,0x5c,
                   0xc2,0xd3,0xac,0x62,0x91,0x95,0xe4,0x79,
                   0xe7,0xc8,0x37,0x6d,0x8d,0xd5,0x4e,0xa9,
                   0x6c,0x56,0xf4,0xea,0x65,0x7a,0xae,0x08,
                   0xba,0x78,0x25,0x2e,0x1c,0xa6,0xb4,0xc6,
                   0xe8,0xdd,0x74,0x1f,0x4b,0xbd,0x8b,0x8a,
                   0x70,0x3e,0xb5,0x66,0x48,0x03,0xf6,0x0e,
                   0x61,0x35,0x57,0xb9,0x86,0xc1,0x1d,0x9e,
                   0xe1,0xf8,0x98,0x11,0x69,0xd9,0x8e,0x94,
                   0x9b,0x1e,0x87,0xe9,0xce,0x55,0x28,0xdf,
                   0x8c,0xa1,0x89,0x0d,0xbf,0xe6,0x42,0x68,
                   0x41,0x99,0x2d,0x0f,0xb0,0x54,0xbb,0x16)

        InvSbox = (0x52,0x09,0x6a,0xd5,0x30,0x36,0xa5,0x38,
                   0xbf,0x40,0xa3,0x9e,0x81,0xf3,0xd7,0xfb,
                   0x7c,0xe3,0x39,0x82,0x9b,0x2f,0xff,0x87,
                   0x34,0x8e,0x43,0x44,0xc4,0xde,0xe9,0xcb,
                   0x54,0x7b,0x94,0x32,0xa6,0xc2,0x23,0x3d,
                   0xee,0x4c,0x95,0x0b,0x42,0xfa,0xc3,0x4e,
                   0x08,0x2e,0xa1,0x66,0x28,0xd9,0x24,0xb2,
                   0x76,0x5b,0xa2,0x49,0x6d,0x8b,0xd1,0x25,
                   0x72,0xf8,0xf6,0x64,0x86,0x68,0x98,0x16,
                   0xd4,0xa4,0x5c,0xcc,0x5d,0x65,0xb6,0x92,
                   0x6c,0x70,0x48,0x50,0xfd,0xed,0xb9,0xda,
                   0x5e,0x15,0x46,0x57,0xa7,0x8d,0x9d,0x84,
                   0x90,0xd8,0xab,0x00,0x8c,0xbc,0xd3,0x0a,
                   0xf7,0xe4,0x58,0x05,0xb8,0xb3,0x45,0x06,
                   0xd0,0x2c,0x1e,0x8f,0xca,0x3f,0x0f,0x02,
                   0xc1,0xaf,0xbd,0x03,0x01,0x13,0x8a,0x6b,
                   0x3a,0x91,0x11,0x41,0x4f,0x67,0xdc,0xea,
                   0x97,0xf2,0xcf,0xce,0xf0,0xb4,0xe6,0x73,
                   0x96,0xac,0x74,0x22,0xe7,0xad,0x35,0x85,
                   0xe2,0xf9,0x37,0xe8,0x1c,0x75,0xdf,0x6e,
                   0x47,0xf1,0x1a,0x71,0x1d,0x29,0xc5,0x89,
                   0x6f,0xb7,0x62,0x0e,0xaa,0x18,0xbe,0x1b,
                   0xfc,0x56,0x3e,0x4b,0xc6,0xd2,0x79,0x20,
                   0x9a,0xdb,0xc0,0xfe,0x78,0xcd,0x5a,0xf4,
                   0x1f,0xdd,0xa8,0x33,0x88,0x07,0xc7,0x31,
                   0xb1,0x12,0x10,0x59,0x27,0x80,0xec,0x5f,
                   0x60,0x51,0x7f,0xa9,0x19,0xb5,0x4a,0x0d,
                   0x2d,0xe5,0x7a,0x9f,0x93,0xc9,0x9c,0xef,
                   0xa0,0xe0,0x3b,0x4d,0xae,0x2a,0xf5,0xb0,
                   0xc8,0xeb,0xbb,0x3c,0x83,0x53,0x99,0x61,
                   0x17,0x2b,0x04,0x7e,0xba,0x77,0xd6,0x26,
                   0xe1,0x69,0x14,0x63,0x55,0x21,0x0c,0x7d)

        #-------------------------------------
        """ For each block size (Nb), the ShiftRow operation shifts row i
            by the amount Ci.  Note that row 0 is not shifted.
                         Nb      C1 C2 C3
                       -------------------  """
        shiftOffset  = { 4 : ( 0, 1, 2, 3),
                         5 : ( 0, 1, 2, 3),
                         6 : ( 0, 1, 2, 3),
                         7 : ( 0, 1, 2, 4),
                         8 : ( 0, 1, 3, 4) }
        def ShiftRows(algInstance):
            tmp = [0]*algInstance.Nb   # list of size Nb
            for r in range(1,4):       # row 0 reamains unchanged and can be skipped
                for c in range(algInstance.Nb):
                    tmp[c] = algInstance.state[(c+shiftOffset[algInstance.Nb][r]) % algInstance.Nb][r]
                for c in range(algInstance.Nb):
                    algInstance.state[c][r] = tmp[c]
        def InvShiftRows(algInstance):
            tmp = [0]*algInstance.Nb   # list of size Nb
            for r in range(1,4):       # row 0 reamains unchanged and can be skipped
                for c in range(algInstance.Nb):
                    tmp[c] = algInstance.state[(c+algInstance.Nb-shiftOffset[algInstance.Nb][r]) % algInstance.Nb][r]
                for c in range(algInstance.Nb):
                    algInstance.state[c][r] = tmp[c]
        #-------------------------------------
        def MixColumns(a):
            Sprime = [0,0,0,0]
            for j in range(a.Nb):    # for each column
                Sprime[0] = mul(2,a.state[j][0])^mul(3,a.state[j][1])^mul(1,a.state[j][2])^mul(1,a.state[j][3])
                Sprime[1] = mul(1,a.state[j][0])^mul(2,a.state[j][1])^mul(3,a.state[j][2])^mul(1,a.state[j][3])
                Sprime[2] = mul(1,a.state[j][0])^mul(1,a.state[j][1])^mul(2,a.state[j][2])^mul(3,a.state[j][3])
                Sprime[3] = mul(3,a.state[j][0])^mul(1,a.state[j][1])^mul(1,a.state[j][2])^mul(2,a.state[j][3])
                for i in range(4):
                    a.state[j][i] = Sprime[i]

        def InvMixColumns(a):
            """ Mix the four bytes of every column in a linear way
                This is the opposite operation of Mixcolumn """
            Sprime = [0,0,0,0]
            for j in range(a.Nb):    # for each column
                Sprime[0] = mul(0x0E,a.state[j][0])^mul(0x0B,a.state[j][1])^mul(0x0D,a.state[j][2])^mul(0x09,a.state[j][3])
                Sprime[1] = mul(0x09,a.state[j][0])^mul(0x0E,a.state[j][1])^mul(0x0B,a.state[j][2])^mul(0x0D,a.state[j][3])
                Sprime[2] = mul(0x0D,a.state[j][0])^mul(0x09,a.state[j][1])^mul(0x0E,a.state[j][2])^mul(0x0B,a.state[j][3])
                Sprime[3] = mul(0x0B,a.state[j][0])^mul(0x0D,a.state[j][1])^mul(0x09,a.state[j][2])^mul(0x0E,a.state[j][3])
                for i in range(4):
                    a.state[j][i] = Sprime[i]

        #-------------------------------------
        def mul(a, b):
            """ Multiply two elements of GF(2^m)
                needed for MixColumn and InvMixColumn """
            if (a !=0 and  b!=0):
                return Alogtable[(Logtable[a] + Logtable[b])%255]
            else:
                return 0

        Logtable = ( 0,   0,  25,   1,  50,   2,  26, 198,  75, 199,  27, 104,  51, 238, 223,   3,
                   100,   4, 224,  14,  52, 141, 129, 239,  76, 113,   8, 200, 248, 105,  28, 193,
                   125, 194,  29, 181, 249, 185,  39, 106,  77, 228, 166, 114, 154, 201,   9, 120,
                   101,  47, 138,   5,  33,  15, 225,  36,  18, 240, 130,  69,  53, 147, 218, 142,
                   150, 143, 219, 189,  54, 208, 206, 148,  19,  92, 210, 241,  64,  70, 131,  56,
                   102, 221, 253,  48, 191,   6, 139,  98, 179,  37, 226, 152,  34, 136, 145,  16,
                   126, 110,  72, 195, 163, 182,  30,  66,  58, 107,  40,  84, 250, 133,  61, 186,
                    43, 121,  10,  21, 155, 159,  94, 202,  78, 212, 172, 229, 243, 115, 167,  87,
                   175,  88, 168,  80, 244, 234, 214, 116,  79, 174, 233, 213, 231, 230, 173, 232,
                    44, 215, 117, 122, 235,  22,  11, 245,  89, 203,  95, 176, 156, 169,  81, 160,
                   127,  12, 246, 111,  23, 196,  73, 236, 216,  67,  31,  45, 164, 118, 123, 183,
                   204, 187,  62,  90, 251,  96, 177, 134,  59,  82, 161, 108, 170,  85,  41, 157,
                   151, 178, 135, 144,  97, 190, 220, 252, 188, 149, 207, 205,  55,  63,  91, 209,
                    83,  57, 132,  60,  65, 162, 109,  71,  20,  42, 158,  93,  86, 242, 211, 171,
                    68,  17, 146, 217,  35,  32,  46, 137, 180, 124, 184,  38, 119, 153, 227, 165,
                   103,  74, 237, 222, 197,  49, 254,  24,  13,  99, 140, 128, 192, 247, 112,   7)

        Alogtable= ( 1,   3,   5,  15,  17,  51,  85, 255,  26,  46, 114, 150, 161, 248,  19,  53,
                    95, 225,  56,  72, 216, 115, 149, 164, 247,   2,   6,  10,  30,  34, 102, 170,
                   229,  52,  92, 228,  55,  89, 235,  38, 106, 190, 217, 112, 144, 171, 230,  49,
                    83, 245,   4,  12,  20,  60,  68, 204,  79, 209, 104, 184, 211, 110, 178, 205,
                    76, 212, 103, 169, 224,  59,  77, 215,  98, 166, 241,   8,  24,  40, 120, 136,
                   131, 158, 185, 208, 107, 189, 220, 127, 129, 152, 179, 206,  73, 219, 118, 154,
                   181, 196,  87, 249,  16,  48,  80, 240,  11,  29,  39, 105, 187, 214,  97, 163,
                   254,  25,  43, 125, 135, 146, 173, 236,  47, 113, 147, 174, 233,  32,  96, 160,
                   251,  22,  58,  78, 210, 109, 183, 194,  93, 231,  50,  86, 250,  21,  63,  65,
                   195,  94, 226,  61,  71, 201,  64, 192,  91, 237,  44, 116, 156, 191, 218, 117,
                   159, 186, 213, 100, 172, 239,  42, 126, 130, 157, 188, 223, 122, 142, 137, 128,
                   155, 182, 193,  88, 232,  35, 101, 175, 234,  37, 111, 177, 200,  67, 197,  84,
                   252,  31,  33,  99, 165, 244,   7,   9,  27,  45, 119, 153, 176, 203,  70, 202,
                    69, 207,  74, 222, 121, 139, 134, 145, 168, 227,  62,  66, 198,  81, 243,  14,
                    18,  54,  90, 238,  41, 123, 141, 140, 143, 138, 133, 148, 167, 242,  13,  23,
                    57,  75, 221, 124, 132, 151, 162, 253,  28,  36, 108, 180, 199,  82, 246,   1)




        """
            AES Encryption Algorithm
            The AES algorithm is just Rijndael algorithm restricted to the default
            blockSize of 128 bits.
        """

        class AES(Rijndael):
            """ The AES algorithm is the Rijndael block cipher restricted to block
                sizes of 128 bits and key sizes of 128, 192 or 256 bits
            """
            def __init__(self, key = None, padding = padWithPadLen(), keySize=16):
                """ Initialize AES, keySize is in bytes """
                if  not (keySize == 16 or keySize == 24 or keySize == 32) :
                    raise BadKeySizeError('Illegal AES key size, must be 16, 24, or 32 bytes')

                Rijndael.__init__( self, key, padding=padding, keySize=keySize, blockSize=16 )

                self.name       = 'AES'


        """
            CBC mode of encryption for block ciphers.
            This algorithm mode wraps any BlockCipher to make a
            Cipher Block Chaining mode.
        """
        from random             import Random  # should change to crypto.random!!!


        class CBC(BlockCipher):
            """ The CBC class wraps block ciphers to make cipher block chaining (CBC) mode
                algorithms.  The initialization (IV) is automatic if set to None.  Padding
                is also automatic based on the Pad class used to initialize the algorithm
            """
            def __init__(self, blockCipherInstance, padding = padWithPadLen()):
                """ CBC algorithms are created by initializing with a BlockCipher instance """
                self.baseCipher = blockCipherInstance
                self.name       = self.baseCipher.name + '_CBC'
                self.blockSize  = self.baseCipher.blockSize
                self.keySize    = self.baseCipher.keySize
                self.padding    = padding
                self.baseCipher.padding = noPadding()   # baseCipher should NOT pad!!
                self.r          = Random()            # for IV generation, currently uses
                                                      # mediocre standard distro version     <----------------
                import time
                newSeed = time.ctime()+str(self.r)    # seed with instance location
                self.r.seed(newSeed)                  # to make unique
                self.reset()

            def setKey(self, key):
                self.baseCipher.setKey(key)

            # Overload to reset both CBC state and the wrapped baseCipher
            def resetEncrypt(self):
                BlockCipher.resetEncrypt(self)  # reset CBC encrypt state (super class)
                self.baseCipher.resetEncrypt()  # reset base cipher encrypt state

            def resetDecrypt(self):
                BlockCipher.resetDecrypt(self)  # reset CBC state (super class)
                self.baseCipher.resetDecrypt()  # reset base cipher decrypt state

            def encrypt(self, plainText, iv=None, more=None):
                """ CBC encryption - overloads baseCipher to allow optional explicit IV
                    when iv=None, iv is auto generated!
                """
                if self.encryptBlockCount == 0:
                    self.iv = iv
                else:
                    assert(iv==None), 'IV used only on first call to encrypt'

                return BlockCipher.encrypt(self,plainText, more=more)

            def decrypt(self, cipherText, iv=None, more=None):
                """ CBC decryption - overloads baseCipher to allow optional explicit IV
                    when iv=None, iv is auto generated!
                """
                if self.decryptBlockCount == 0:
                    self.iv = iv
                else:
                    assert(iv==None), 'IV used only on first call to decrypt'

                return BlockCipher.decrypt(self, cipherText, more=more)

            def encryptBlock(self, plainTextBlock):
                """ CBC block encryption, IV is set with 'encrypt' """
                auto_IV = ''
                if self.encryptBlockCount == 0:
                    if self.iv == None:
                        # generate IV and use
                        self.iv = ''.join([chr(self.r.randrange(256)) for i in range(self.blockSize)])
                        self.prior_encr_CT_block = self.iv
                        auto_IV = self.prior_encr_CT_block    # prepend IV if it's automatic
                    else:                       # application provided IV
                        assert(len(self.iv) == self.blockSize ),'IV must be same length as block'
                        self.prior_encr_CT_block = self.iv
                """ encrypt the prior CT XORed with the PT """
                ct = self.baseCipher.encryptBlock( xor(self.prior_encr_CT_block, plainTextBlock) )
                self.prior_encr_CT_block = ct
                return auto_IV+ct

            def decryptBlock(self, encryptedBlock):
                """ Decrypt a single block """

                if self.decryptBlockCount == 0:   # first call, process IV
                    if self.iv == None:    # auto decrypt IV?
                        self.prior_CT_block = encryptedBlock
                        return b''
                    else:
                        assert(len(self.iv)==self.blockSize),"Bad IV size on CBC decryption"
                        self.prior_CT_block = self.iv

                dct = self.baseCipher.decryptBlock(encryptedBlock)
                """ XOR the prior decrypted CT with the prior CT """
                dct_XOR_priorCT = xor( self.prior_CT_block, dct )

                self.prior_CT_block = encryptedBlock

                return dct_XOR_priorCT


        """
            AES_CBC Encryption Algorithm
        """

        class aescbc_AES_CBC(CBC):
            """ AES encryption in CBC feedback mode """
            def __init__(self, key=None, padding=padWithPadLen(), keySize=16):
                CBC.__init__( self, AES(key, noPadding(), keySize), padding)
                self.name       = 'AES_CBC'

        class AES_CBC(object):
            def __init__(self):
                self._key = None
                self._iv = None
                self.aes = None

            def set_decrypt_key(self, userkey, iv):
                self._key = userkey
                self._iv = iv
                self.aes = aescbc_AES_CBC(userkey, noPadding(), len(userkey))

            def decrypt(self, data):
                iv = self._iv
                cleartext = self.aes.decrypt(iv + data)
                return cleartext

        import hmac

        class KeyIVGen(object):
            # this only exists in openssl so we will use pure python implementation instead
            # PKCS5_PBKDF2_HMAC_SHA1 = F(c_int, 'PKCS5_PBKDF2_HMAC_SHA1',
            #                             [c_char_p, c_ulong, c_char_p, c_ulong, c_ulong, c_ulong, c_char_p])
            def pbkdf2(self, passwd, salt, iter, keylen):

                def xorbytes( a, b ):
                    if len(a) != len(b):
                        raise Exception("xorbytes(): lengths differ")
                    return bytes([x ^ y for x, y in zip(a, b)])

                def prf( h, data ):
                    hm = h.copy()
                    hm.update( data )
                    return hm.digest()

                def pbkdf2_F( h, salt, itercount, blocknum ):
                    U = prf( h, salt + pack('>i',blocknum ) )
                    T = U
                    for i in range(2, itercount+1):
                        U = prf( h, U )
                        T = xorbytes( T, U )
                    return T

                sha = hashlib.sha1
                digest_size = sha().digest_size
                # l - number of output blocks to produce
                l = keylen // digest_size
                if keylen % digest_size != 0:
                    l += 1
                h = hmac.new( passwd, None, sha )
                T = b""
                for i in range(1, l+1):
                    T += pbkdf2_F( h, salt, iter, i )
                return T[0: keylen]

    def UnprotectHeaderData(encryptedData):
        passwdData = b'header_key_data'
        salt = b'HEADER.2011'
        iter = 0x80
        keylen = 0x100
        key_iv = KeyIVGen().pbkdf2(passwdData, salt, iter, keylen)
        key = key_iv[0:32]
        iv = key_iv[32:48]
        aes=AES_CBC()
        aes.set_decrypt_key(key, iv)
        cleartext = aes.decrypt(encryptedData)
        return cleartext

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
            key = KeyIVGen().pbkdf2(passwd, salt, 10000, 0x400)[:32]  # this is very slow

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
                from Crypto.Cipher import AES
                from Crypto.Util import Counter
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
    import copy
    import subprocess

    # interface to needed routines in openssl's libcrypto
    def _load_crypto_libcrypto():
        from ctypes import CDLL, byref, POINTER, c_void_p, c_char_p, c_int, c_long, \
            Structure, c_ulong, create_string_buffer, addressof, string_at, cast
        from ctypes.util import find_library

        libcrypto = find_library('crypto')
        if libcrypto is None:
            libcrypto = '/usr/lib/libcrypto.dylib'
        try:
            libcrypto = CDLL(libcrypto)
        except Exception as e:
            raise DrmException("libcrypto not found: " % e)

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
                    raise DrmException("AES improper key used")
                    return
                keyctx = self._keyctx = AES_KEY()
                self._iv = iv
                self._userkey = userkey
                rv = AES_set_decrypt_key(userkey, len(userkey) * 8, keyctx)
                if rv < 0:
                    raise DrmException("Failed to initialize AES key")

            def decrypt(self, data):
                out = create_string_buffer(len(data))
                mutable_iv = create_string_buffer(self._iv, len(self._iv))
                keyctx = self._keyctx
                rv = AES_cbc_encrypt(data, out, len(data), keyctx, mutable_iv, 0)
                if rv == 0:
                    raise DrmException("AES decryption failed")
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


    # unprotect the new header blob in .kinf2011
    # used in Kindle for Mac Version >= 1.9.0
    def UnprotectHeaderData(encryptedData):
        passwdData = b'header_key_data'
        salt = b'HEADER.2011'
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
    class CryptUnprotectData(object):
        def __init__(self, entropy, IDString):
            sp = GetUserName() + b'+@#$%+' + IDString
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
            b'DSN'
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
                    key = LibCrypto().keyivgen(passwd, salt, 10000, 0x400)[:32]

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
                        from Crypto.Cipher import AES
                        from Crypto.Util import Counter
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
