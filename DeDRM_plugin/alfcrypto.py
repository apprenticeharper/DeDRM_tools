#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# crypto library mainly by some_updates

# pbkdf2.py pbkdf2 code taken from pbkdf2.py
# pbkdf2.py Copyright © 2004 Matt Johnston <matt @ ucc asn au>
# pbkdf2.py Copyright © 2009 Daniel Holth <dholth@fastmail.fm>
# pbkdf2.py This code may be freely used and modified for any purpose.

import sys
import hmac
from struct import pack
import hashlib
import aescbc

class Pukall_Cipher(object):
    def __init__(self):
        self.key = None

    def PC1(self, key, src, decryption=True):
        sum1 = 0;
        sum2 = 0;
        keyXorVal = 0;
        if len(key)!=16:
            raise Exception("PC1: Bad key length")
        wkey = []
        for i in range(8):
            if sys.version_info[0] == 2:
                wkey.append(ord(key[i*2])<<8 | ord(key[i*2+1]))
            else: 
                wkey.append(key[i*2]<<8 | key[i*2+1])
        dst = bytearray(len(src))
        for i in range(len(src)):
            temp1 = 0;
            byteXorVal = 0;
            for j in range(8):
                temp1 ^= wkey[j]
                sum2  = (sum2+j)*20021 + sum1
                sum1  = (temp1*346)&0xFFFF
                sum2  = (sum2+sum1)&0xFFFF
                temp1 = (temp1*20021+1)&0xFFFF
                byteXorVal ^= temp1 ^ sum2

            if sys.version_info[0] == 2:
                curByte = ord(src[i])
            else:
                curByte = src[i]

            if not decryption:
                keyXorVal = curByte * 257;
            curByte = ((curByte ^ (byteXorVal >> 8)) ^ byteXorVal) & 0xFF
            if decryption:
                keyXorVal = curByte * 257;
            for j in range(8):
                wkey[j] ^= keyXorVal;
            
            if sys.version_info[0] == 2:
                dst[i] = chr(curByte)
            else: 
                dst[i] = curByte
                
        return bytes(dst)

class Topaz_Cipher(object):
    def __init__(self):
        self._ctx = None

    def ctx_init(self, key):
        ctx1 = 0x0CAFFE19E
        if isinstance(key, str):
            key = key.encode('latin-1')
        for keyByte in key:
            ctx2 = ctx1
            ctx1 = ((((ctx1 >>2) * (ctx1 >>7))&0xFFFFFFFF) ^ (keyByte * keyByte * 0x0F902007)& 0xFFFFFFFF )
        self._ctx = [ctx1, ctx2]
        return [ctx1,ctx2]

    def decrypt(self, data,  ctx=None):
        if ctx == None:
            ctx = self._ctx
        ctx1 = ctx[0]
        ctx2 = ctx[1]
        plainText = ""
        if isinstance(data, str):
            data = data.encode('latin-1')
        for dataByte in data:
            m = (dataByte ^ ((ctx1 >> 3) &0xFF) ^ ((ctx2<<3) & 0xFF)) &0xFF
            ctx2 = ctx1
            ctx1 = (((ctx1 >> 2) * (ctx1 >> 7)) &0xFFFFFFFF) ^((m * m * 0x0F902007) &0xFFFFFFFF)
            plainText += chr(m)
        return plainText

class AES_CBC(object):
    def __init__(self):
        self._key = None
        self._iv = None
        self.aes = None

    def set_decrypt_key(self, userkey, iv):
        self._key = userkey
        self._iv = iv
        self.aes = aescbc.AES_CBC(userkey, aescbc.noPadding(), len(userkey))

    def decrypt(self, data):
        iv = self._iv
        cleartext = self.aes.decrypt(iv + data)
        return cleartext


class KeyIVGen(object):
    # this only exists in openssl so we will use pure python implementation instead
    # PKCS5_PBKDF2_HMAC_SHA1 = F(c_int, 'PKCS5_PBKDF2_HMAC_SHA1',
    #                             [c_char_p, c_ulong, c_char_p, c_ulong, c_ulong, c_ulong, c_char_p])
    def pbkdf2(self, passwd, salt, iter, keylen):

        def xorbytes( a, b ):
            if len(a) != len(b):
                raise Exception("xorbytes(): lengths differ")
            return bytes(bytearray([x ^ y for x, y in zip(a, b)]))

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


