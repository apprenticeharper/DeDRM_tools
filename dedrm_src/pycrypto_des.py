#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab


def load_pycrypto():
    try :
        from Crypto.Cipher import DES as _DES
    except:
        return None

    class DES(object):
        def __init__(self, key):
            if len(key) != 8 :
                raise ValueError('DES improper key used')
            self.key = key
            self._des = _DES.new(key,_DES.MODE_ECB)
        def desdecrypt(self, data):
            return self._des.decrypt(data)
        def decrypt(self, data):
            if not data:
                return ''
            i = 0
            result = []
            while i < len(data):
                block = data[i:i+8]
                processed_block = self.desdecrypt(block)
                result.append(processed_block)
                i += 8
            return ''.join(result)
    return DES
