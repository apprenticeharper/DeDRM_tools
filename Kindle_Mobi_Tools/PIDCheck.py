#!/usr/bin/python
#
# This is a python script. You need a Python interpreter to run it.
# For example, ActiveState Python, which exists for windows.
#
# Changelog
#  1.00 - Initial version

__version__ = '1.00'

import sys
import struct
import binascii

def checksumPid(s):
    letters = "ABCDEFGHIJKLMNPQRSTUVWXYZ123456789"
    crc = (~binascii.crc32(s,-1))&0xFFFFFFFF
    crc = crc ^ (crc >> 16)
    res = s
    l = len(letters)
    for i in (0,1):
        b = crc & 0xff
        pos = (b // l) ^ (b % l)
        res += letters[pos%l]
        crc >>= 8
    return res

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "Checks Mobipocket PID checksum"
        print "Usage:"
        print "    %s <PID>" % sys.argv[0]
        sys.exit(1)
    else:
        pid = sys.argv[1]
        if len(pid) == 8:
           pid = checksumPid(pid)
        else:
           pid = checksumPid(pid[:8])
        print pid
    sys.exit(0)