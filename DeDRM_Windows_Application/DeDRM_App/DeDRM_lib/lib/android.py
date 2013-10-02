#!/usr/bin/env python
#fileencoding: utf-8

import os
import sys
import zlib
import tarfile
from hashlib import md5
from cStringIO import StringIO
from binascii import a2b_hex, b2a_hex

STORAGE = 'AmazonSecureStorage.xml'

class AndroidObfuscation(object):
    '''AndroidObfuscation
    For the key, it's written in java, and run in android dalvikvm
    '''

    key = a2b_hex('0176e04c9408b1702d90be333fd53523')

    def encrypt(self, plaintext):
        cipher = self._get_cipher()
        padding = len(self.key) - len(plaintext) % len(self.key)
        plaintext += chr(padding) * padding
        return b2a_hex(cipher.encrypt(plaintext))

    def decrypt(self, ciphertext):
        cipher = self._get_cipher()
        plaintext = cipher.decrypt(a2b_hex(ciphertext))
        return plaintext[:-ord(plaintext[-1])]

    def _get_cipher(self):
        try:
            from Crypto.Cipher import AES
            return AES.new(self.key)
        except ImportError:
            from aescbc import AES, noPadding
            return AES(self.key, padding=noPadding())

class AndroidObfuscationV2(AndroidObfuscation):
    '''AndroidObfuscationV2
    '''

    count = 503
    password = 'Thomsun was here!'

    def __init__(self, salt):
        key = self.password + salt
        for _ in range(self.count):
            key = md5(key).digest()
        self.key = key[:8]
        self.iv = key[8:16]

    def _get_cipher(self):
        try :
            from Crypto.Cipher import DES
            return DES.new(self.key, DES.MODE_CBC, self.iv)
        except ImportError:
            from python_des import Des, CBC
            return Des(self.key, CBC, self.iv)

def parse_preference(path):
    ''' parse android's shared preference xml '''
    storage = {}
    read = open(path)
    for line in read:
        line = line.strip()
        # <string name="key">value</string>
        if line.startswith('<string name="'):
            index = line.find('"', 14)
            key = line[14:index]
            value = line[index+2:-9]
            storage[key] = value
    read.close()
    return storage

def get_serials(path=None):
    ''' get serials from android's shared preference xml '''
    if path is None:
        if not os.path.isfile(STORAGE):
            if os.path.isfile("backup.ab"):
                get_storage()
            else:
                return []
        path = STORAGE

    if not os.path.isfile(path):
        return []

    storage = parse_preference(path)
    salt = storage.get('AmazonSaltKey')
    if salt and len(salt) == 16:
        sys.stdout.write('Using AndroidObfuscationV2\n')
        obfuscation = AndroidObfuscationV2(a2b_hex(salt))
    else:
        sys.stdout.write('Using AndroidObfuscation\n')
        obfuscation = AndroidObfuscation()

    def get_value(key):
        encrypted_key = obfuscation.encrypt(key)
        encrypted_value = storage.get(encrypted_key)
        if encrypted_value:
            return obfuscation.decrypt(encrypted_value)
        return ''

    # also see getK4Pids in kgenpids.py
    try:
        dsnid = get_value('DsnId')
    except:
        sys.stderr.write('cannot get DsnId\n')
        return []

    try:
        tokens = set(get_value('kindle.account.tokens').split(','))
    except:
        return [dsnid]

    serials = []
    for token in tokens:
        if token:
            serials.append('%s%s' % (dsnid, token))
    serials.append(dsnid)
    for token in tokens:
        if token:
            serials.append(token)
    return serials

def get_storage(path='backup.ab'):
    '''get AmazonSecureStorage.xml from android backup.ab
    backup.ab can be get using adb command:
    shell> adb backup com.amazon.kindle
    '''
    output = None
    read = open(path, 'rb')
    head = read.read(24)
    if head == 'ANDROID BACKUP\n1\n1\nnone\n':
        output = StringIO(zlib.decompress(read.read()))
    read.close()

    if not output:
        return False

    tar = tarfile.open(fileobj=output)
    for member in tar.getmembers():
        if member.name.strip().endswith(STORAGE):
            write = open(STORAGE, 'w')
            write.write(tar.extractfile(member).read())
            write.close()
            break

    return True

__all__ = [ 'get_storage', 'get_serials', 'parse_preference',
            'AndroidObfuscation', 'AndroidObfuscationV2', 'STORAGE']

if __name__ == '__main__':
    print get_serials()