#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# adobekey_get_passhash.py, version 1
# based on adobekey.pyw, version 7.2
# Copyright © 2009-2021 i♥cabbages, Apprentice Harper et al.
# Copyright © 2021 noDRM

# Released under the terms of the GNU General Public Licence, version 3
# <http://www.gnu.org/licenses/>

# Revision history:
#   1 - Initial release

"""
Retrieve Adobe ADEPT user passhash keys
"""

__license__ = 'GPL v3'
__version__ = '1'

import sys, os, time
import base64, hashlib
try: 
    from Cryptodome.Cipher import AES
except ImportError:
    from Crypto.Cipher import AES


def unpad(data, padding=16):
    if sys.version_info[0] == 2:
        pad_len = ord(data[-1])
    else:
        pad_len = data[-1]

    return data[:-pad_len]

PASS_HASH_SECRET = "9ca588496a1bc4394553d9e018d70b9e"


try:
    from calibre.constants import iswindows, isosx
except:
    iswindows = sys.platform.startswith('win')
    isosx = sys.platform.startswith('darwin')


class ADEPTError(Exception):
    pass

def decrypt_passhash(passhash, fp):

    serial_number = base64.b64decode(fp).hex()

    hash_key = hashlib.sha1(bytearray.fromhex(serial_number + PASS_HASH_SECRET)).digest()[:16]

    encrypted_cc_hash = base64.b64decode(passhash)
    cc_hash = unpad(AES.new(hash_key, AES.MODE_CBC, encrypted_cc_hash[:16]).decrypt(encrypted_cc_hash[16:]))
    return base64.b64encode(cc_hash).decode("ascii")


if iswindows:
    try:
        import winreg
    except ImportError:
        import _winreg as winreg

    PRIVATE_LICENCE_KEY_PATH = r'Software\Adobe\Adept\Activation'

    def passhash_keys():
        cuser = winreg.HKEY_CURRENT_USER
        keys = []
        names = []
        try:
            plkroot = winreg.OpenKey(cuser, PRIVATE_LICENCE_KEY_PATH)
        except WindowsError:
            raise ADEPTError("Could not locate ADE activation")
        except FileNotFoundError:
            raise ADEPTError("Could not locate ADE activation")

        idx = 1

        fp = None

        i = -1
        while True:
            i = i + 1   # start with 0
            try:
                plkparent = winreg.OpenKey(plkroot, "%04d" % (i,))
            except:
                # No more keys
                break
                
            ktype = winreg.QueryValueEx(plkparent, None)[0]

            if ktype == "activationToken":
                # find fingerprint for hash decryption
                j = -1
                while True:
                    j = j + 1   # start with 0
                    try:
                        plkkey = winreg.OpenKey(plkparent, "%04d" % (j,))
                    except WindowsError:
                        break
                    except FileNotFoundError:
                        break
                    ktype = winreg.QueryValueEx(plkkey, None)[0]
                    if ktype == 'fingerprint':
                        fp = winreg.QueryValueEx(plkkey, 'value')[0]
                        #print("Found fingerprint: " + fp)


            # Note: There can be multiple lists, with multiple entries each.
            if ktype == 'passHashList':
            
                # Find operator (used in key name)
                j = -1
                lastOperator = "Unknown"
                while True:
                    j = j + 1   # start with 0
                    try:
                        plkkey = winreg.OpenKey(plkparent, "%04d" % (j,))
                    except WindowsError:
                        break
                    except FileNotFoundError:
                        break
                    ktype = winreg.QueryValueEx(plkkey, None)[0]
                    if ktype == 'operatorURL':
                        operatorURL = winreg.QueryValueEx(plkkey, 'value')[0]
                        try: 
                            lastOperator = operatorURL.split('//')[1].split('/')[0]
                        except:
                            pass
                
                
                # Find hashes
                j = -1
                while True:
                    j = j + 1   # start with 0
                    try:
                        plkkey = winreg.OpenKey(plkparent, "%04d" % (j,))
                    except WindowsError:
                        break
                    except FileNotFoundError:
                        break
                    ktype = winreg.QueryValueEx(plkkey, None)[0]

                    if ktype == "passHash":
                        passhash_encrypted = winreg.QueryValueEx(plkkey, 'value')[0]
                        names.append("ADE_key_" + lastOperator + "_" + str(int(time.time())) + "_" + str(idx))
                        idx = idx + 1
                        keys.append(passhash_encrypted)

        if fp is None:
            #print("Didn't find fingerprint for decryption ...")
            return [], []

        print("Found {0:d} passhashes".format(len(keys)), file=sys.stderr)

        keys_decrypted = []

        for key in keys:
            decrypted = decrypt_passhash(key, fp)
            #print("Input key: " + key)
            #print("Output key: " + decrypted)
            keys_decrypted.append(decrypted)

        return keys_decrypted, names

   
else:
    def passhash_keys():
        raise ADEPTError("This script only supports Windows.")
        #TODO: Add MacOS support by parsing the activation.xml file.
        return [], []


if __name__ == '__main__':
    print("This is a python calibre plugin. It can't be directly executed.")
