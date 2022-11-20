# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai

'''
Obtain the user's ccHash from the Barnes & Noble Nook Windows Store app. 
https://www.microsoft.com/en-us/p/nook-books-magazines-newspapers-comics/9wzdncrfj33h
(Requires a recent Windows version in a supported region (US).)
This procedure has been tested with Nook app version 1.11.0.4 under Windows 11.

Based on experimental standalone python script created by fesiwi at 
https://github.com/noDRM/DeDRM_tools/discussions/9
'''

import sys, os
import apsw
import base64
import traceback
try: 
    from Cryptodome.Cipher import AES
except:
    from Crypto.Cipher import AES
import hashlib
from lxml import etree

def unpad(data, padding=16):
    if sys.version_info[0] == 2:
        pad_len = ord(data[-1])
    else:
        pad_len = data[-1]

    return data[:-pad_len]


NOOK_DATA_FOLDER = "%LOCALAPPDATA%\\Packages\\BarnesNoble.Nook_ahnzqzva31enc\\LocalState"
PASS_HASH_SECRET = "9ca588496a1bc4394553d9e018d70b9e"


def dump_keys(print_result=False):
    db_filename = os.path.expandvars(NOOK_DATA_FOLDER + "\\NookDB.db3")


    if not os.path.isfile(db_filename):
        print("Database file not found. Is the Nook Windows Store app installed?")
        return []

    
    # Python2 has no fetchone() so we have to use fetchall() and discard everything but the first result.
    # There should only be one result anyways.
    serial_number = apsw.Connection(db_filename).cursor().execute(
                "SELECT value FROM bn_internal_key_value_table WHERE key = 'serialNumber';").fetchall()[0][0]


    hash_key = hashlib.sha1(bytearray.fromhex(serial_number + PASS_HASH_SECRET)).digest()[:16]

    activation_file_name = os.path.expandvars(NOOK_DATA_FOLDER + "\\settings\\activation.xml")

    if not os.path.isfile(activation_file_name):
        print("Activation file not found. Are you logged in to your Nook account?")
        return []


    activation_xml = etree.parse(activation_file_name)

    decrypted_hashes = []

    for pass_hash in activation_xml.findall(".//{http://ns.adobe.com/adept}passHash"):
        try: 
            encrypted_cc_hash = base64.b64decode(pass_hash.text)
            cc_hash = unpad(AES.new(hash_key, AES.MODE_CBC, encrypted_cc_hash[:16]).decrypt(encrypted_cc_hash[16:]), 16)
            decrypted_hashes.append((base64.b64encode(cc_hash).decode("ascii")))
            if print_result:
                print("Nook ccHash is %s" % (base64.b64encode(cc_hash).decode("ascii")))
        except: 
            traceback.print_exc()
    
    return decrypted_hashes

if __name__ == "__main__":
    dump_keys(True)
