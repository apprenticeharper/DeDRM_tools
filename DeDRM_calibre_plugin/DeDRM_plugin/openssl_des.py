#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# implement just enough of des from openssl to make erdr2pml.py happy

def load_libcrypto():
    from ctypes import CDLL, POINTER, c_void_p, c_char_p, c_char, c_int, c_long, \
        Structure, c_ulong, create_string_buffer, cast
    from ctypes.util import find_library
    import sys

    if sys.platform.startswith('win'):
        libcrypto = find_library('libeay32')
    else:
        libcrypto = find_library('crypto')

    if libcrypto is None:
        return None

    libcrypto = CDLL(libcrypto)

    # typedef struct DES_ks
    #     {
    #     union
    #         {
    #         DES_cblock cblock;
    #         /* make sure things are correct size on machines with
    #          * 8 byte longs */
    #         DES_LONG deslong[2];
    #         } ks[16];
    #     } DES_key_schedule;

    # just create a big enough place to hold everything
    # it will have alignment of structure so we should be okay (16 byte aligned?)
    class DES_KEY_SCHEDULE(Structure):
        _fields_ = [('DES_cblock1', c_char * 16),
                    ('DES_cblock2', c_char * 16),
                    ('DES_cblock3', c_char * 16),
                    ('DES_cblock4', c_char * 16),
                    ('DES_cblock5', c_char * 16),
                    ('DES_cblock6', c_char * 16),
                    ('DES_cblock7', c_char * 16),
                    ('DES_cblock8', c_char * 16),
                    ('DES_cblock9', c_char * 16),
                    ('DES_cblock10', c_char * 16),
                    ('DES_cblock11', c_char * 16),
                    ('DES_cblock12', c_char * 16),
                    ('DES_cblock13', c_char * 16),
                    ('DES_cblock14', c_char * 16),
                    ('DES_cblock15', c_char * 16),
                    ('DES_cblock16', c_char * 16)]

    DES_KEY_SCHEDULE_p = POINTER(DES_KEY_SCHEDULE)

    def F(restype, name, argtypes):
        func = getattr(libcrypto, name)
        func.restype = restype
        func.argtypes = argtypes
        return func

    DES_set_key = F(None, 'DES_set_key',[c_char_p, DES_KEY_SCHEDULE_p])
    DES_ecb_encrypt = F(None, 'DES_ecb_encrypt',[c_char_p, c_char_p, DES_KEY_SCHEDULE_p, c_int])


    class DES(object):
        def __init__(self, key):
            if len(key) != 8 :
                raise Exception('DES improper key used')
                return
            self.key = key
            self.keyschedule = DES_KEY_SCHEDULE()
            DES_set_key(self.key, self.keyschedule)
        def desdecrypt(self, data):
            ob = create_string_buffer(len(data))
            DES_ecb_encrypt(data, ob, self.keyschedule, 0)
            return ob.raw
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
