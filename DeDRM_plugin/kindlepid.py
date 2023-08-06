#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Mobipocket PID calculator v0.4 for Amazon Kindle.
# Copyright (c) 2007, 2009 Igor Skochinsky <skochinsky@mail.ru>
# History:
#  0.1 Initial release
#  0.2 Added support for generating PID for iPhone (thanks to mbp)
#  0.3 changed to autoflush stdout, fixed return code usage
#  0.3 updated for unicode
#  0.4 Added support for serial numbers starting with '9', fixed unicode bugs.
#  0.5 moved unicode_argv call inside main for Windows DeDRM compatibility
#  1.0 Python 3 for calibre 5.0


import sys
import binascii

#@@CALIBRE_COMPAT_CODE@@

from .utilities import SafeUnbuffered
from .argv_utils import unicode_argv

letters = b'ABCDEFGHIJKLMNPQRSTUVWXYZ123456789'

def crc32(s):
    return (~binascii.crc32(s,-1))&0xFFFFFFFF

def checksumPid(s):
    crc = crc32(s)
    crc = crc ^ (crc >> 16)
    res = s
    l = len(letters)
    for i in (0,1):
        b = crc & 0xff
        pos = (b // l) ^ (b % l)
        res += bytes(bytearray([letters[pos%l]]))
        crc >>= 8

    return res

def pidFromSerial(s, l):
    crc = crc32(s)

    arr1 = [0]*l
    for i in range(len(s)):
        if sys.version_info[0] == 2:
            arr1[i%l] ^= ord(s[i])
        else: 
            arr1[i%l] ^= s[i]

    crc_bytes = [crc >> 24 & 0xff, crc >> 16 & 0xff, crc >> 8 & 0xff, crc & 0xff]
    for i in range(l):
        arr1[i] ^= crc_bytes[i&3]

    pid = b""
    for i in range(l):
        b = arr1[i] & 0xff
        pid+=bytes(bytearray([letters[(b >> 7) + ((b >> 5 & 3) ^ (b & 0x1f))]]))

    return pid

def cli_main():
    print("Mobipocket PID calculator for Amazon Kindle. Copyright © 2007, 2009 Igor Skochinsky")
    argv=unicode_argv("kindlepid.py")
    if len(argv)==2:
        serial = argv[1]
    else:
        print("Usage: kindlepid.py <Kindle Serial Number>/<iPhone/iPod Touch UDID>")
        return 1
    if len(serial)==16:
        if serial.startswith("B") or serial.startswith("9"):
            print("Kindle serial number detected")
        else:
            print("Warning: unrecognized serial number. Please recheck input.")
            return 1
        pid = pidFromSerial(serial.encode("utf-8"),7)+'*'
        print("Mobipocket PID for Kindle serial#{0} is {1}".format(serial,checksumPid(pid)))
        return 0
    elif len(serial)==40:
        print("iPhone serial number (UDID) detected")
        pid = pidFromSerial(serial.encode("utf-8"),8)
        print("Mobipocket PID for iPhone serial#{0} is {1}".format(serial,checksumPid(pid)))
        return 0
    print("Warning: unrecognized serial number. Please recheck input.")
    return 1


if __name__ == "__main__":
    sys.stdout=SafeUnbuffered(sys.stdout)
    sys.stderr=SafeUnbuffered(sys.stderr)
    sys.exit(cli_main())
