'''
Extracts the user's ccHash from an .adobe-digital-editions folder
typically included in the Nook Android app's data folder.

Based on ignoblekeyWindowsStore.py, updated for Android by noDRM.
'''

import sys
import os
import base64
try: 
    from Cryptodome.Cipher import AES
except ImportError:
    from Crypto.Cipher import AES
import hashlib
from lxml import etree

def unpad(data, padding=16):
    if sys.version_info[0] == 2:
        pad_len = ord(data[-1])
    else:
        pad_len = data[-1]

    return data[:-pad_len]


PASS_HASH_SECRET = "9ca588496a1bc4394553d9e018d70b9e"


def dump_keys(path_to_adobe_folder):
    
    activation_path = os.path.join(path_to_adobe_folder, "activation.xml")
    device_path = os.path.join(path_to_adobe_folder, "device.xml")

    if not os.path.isfile(activation_path):
        print("Nook activation file is missing: %s\n" % activation_path)
        return []
    if not os.path.isfile(device_path):
        print("Nook device file is missing: %s\n" % device_path)
        return []

    # Load files:
    activation_xml = etree.parse(activation_path)
    device_xml = etree.parse(device_path)
    
    # Get fingerprint: 
    device_fingerprint = device_xml.findall(".//{http://ns.adobe.com/adept}fingerprint")[0].text
    device_fingerprint = base64.b64decode(device_fingerprint).hex()

    hash_key = hashlib.sha1(bytearray.fromhex(device_fingerprint + PASS_HASH_SECRET)).digest()[:16]

    hashes = []

    for pass_hash in activation_xml.findall(".//{http://ns.adobe.com/adept}passHash"):
        try: 
            encrypted_cc_hash = base64.b64decode(pass_hash.text)
            cc_hash = unpad(AES.new(hash_key, AES.MODE_CBC, encrypted_cc_hash[:16]).decrypt(encrypted_cc_hash[16:]))
            hashes.append(base64.b64encode(cc_hash).decode("ascii"))
            #print("Nook ccHash is %s" % (base64.b64encode(cc_hash).decode("ascii")))
        except:
            pass

    return hashes



if __name__ == "__main__":
    print("No standalone version available.")
