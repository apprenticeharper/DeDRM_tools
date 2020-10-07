#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Routines for doing AES CBC in one file

    Modified by some_updates to extract
    and combine only those parts needed for AES CBC
    into one simple to add python file

    Original Version
    Copyright (c) 2002 by Paul A. Lambert
    Under:
    CryptoPy Artisitic License Version 1.0
    See the wonderful pure python package cryptopy-1.2.5
    and read its LICENSE.txt for complete license details.

    Adjusted for Python 3, September 2020
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

def xorS(a,b):
    """ XOR two strings """
    assert len(a)==len(b)
    x = []
    for i in range(len(a)):
        x.append( chr(ord(a[i])^ord(b[i])))
    return ''.join(x)

def xor(a,b):
    """ XOR two strings """
    x = []
    for i in range(min(len(a),len(b))):
        x.append( chr(ord(a[i])^ord(b[i])))
    return ''.join(x)

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
        self.bytesToEncrypt = ''
    def resetDecrypt(self):
        self.decryptBlockCount = 0
        self.bytesToDecrypt = ''

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

        plainText = ''
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

        assert( keySize%4==0 and keySize/4 in NrTable[4]),'key size must be 16,20,24,29 or 32 bytes'
        assert( blockSize%4==0 and blockSize/4 in NrTable), 'block size must be 16,20,24,29 or 32 bytes'

        self.Nb = self.blockSize/4          # Nb is number of columns of 32 bit words
        self.Nk = keySize/4                 # Nk is the key length in 32-bit words
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
        return [[ord(bs[4*i]),ord(bs[4*i+1]),ord(bs[4*i+2]),ord(bs[4*i+3])] for i in range(self.Nb)]

    def _toBString(self, block):
        """ Convert block (array of bytes) to binary string """
        l = []
        for col in block:
            for rowElement in col:
                l.append(chr(rowElement))
        return ''.join(l)
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
def keyExpansion(algInstance, keyString):
    """ Expand a string of size keySize into a larger array """
    Nk, Nb, Nr = algInstance.Nk, algInstance.Nb, algInstance.Nr # for readability
    key = [ord(byte) for byte in keyString]  # convert string to list
    w = [[key[4*i],key[4*i+1],key[4*i+2],key[4*i+3]] for i in range(Nk)]
    for i in range(Nk,Nb*(Nr+1)):
        temp = w[i-1]        # a four byte column
        if (i%Nk) == 0 :
            temp     = temp[1:]+[temp[0]]  # RotWord(temp)
            temp     = [ Sbox[byte] for byte in temp ]
            temp[0] ^= Rcon[i/Nk]
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
                return ''
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

class AES_CBC(CBC):
    """ AES encryption in CBC feedback mode """
    def __init__(self, key=None, padding=padWithPadLen(), keySize=16):
        CBC.__init__( self, AES(key, noPadding(), keySize), padding)
        self.name       = 'AES_CBC'
