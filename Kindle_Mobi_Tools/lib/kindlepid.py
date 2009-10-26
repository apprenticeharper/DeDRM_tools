#!/usr/bin/python
# Mobipocket PID calculator v0.2 for Amazon Kindle.
# Copyright (c) 2007, 2009 Igor Skochinsky <skochinsky@mail.ru>
# History:
#  0.1 Initial release
#  0.2 Added support for generating PID for iPhone (thanks to mbp)
#  Unofficial: Added support for Kindle DX and Kindle 2 International

import sys, binascii

if sys.hexversion >= 0x3000000:
  print "This script is incompatible with Python 3.x. Please install Python 2.6.x from python.org"
  sys.exit(2)

letters = "ABCDEFGHIJKLMNPQRSTUVWXYZ123456789"

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
    res += letters[pos%l]
    crc >>= 8

  return res


def pidFromSerial(s, l):
  crc = crc32(s)
  
  arr1 = [0]*l
  for i in xrange(len(s)):
    arr1[i%l] ^= ord(s[i])

  crc_bytes = [crc >> 24 & 0xff, crc >> 16 & 0xff, crc >> 8 & 0xff, crc & 0xff]
  for i in xrange(l):
    arr1[i] ^= crc_bytes[i&3]

  pid = ""
  for i in xrange(l):
    b = arr1[i] & 0xff
    pid+=letters[(b >> 7) + ((b >> 5 & 3) ^ (b & 0x1f))]

  return pid

print "Mobipocket PID calculator for Amazon Kindle. Copyright (c) 2007, 2009 Igor Skochinsky"
if len(sys.argv)>1:
  serial = sys.argv[1]
  if len(serial)==16:
    if serial.startswith("B001"):
      print "Kindle 1 serial number detected"
    elif serial.startswith("B002"):
      print "Kindle 2 serial number detected"
    elif serial.startswith("B003"):
      print "Kindle 2i serial number detected"
    elif serial.startswith("B004"):
      print "Kindle DX serial number detected"
    else:
      print "Warning: unrecognized serial number. Please recheck input."
      sys.exit(1)
    pid = pidFromSerial(serial,7)+"*"
    print "Mobipocked PID for Kindle serial# "+serial+" is "+checksumPid(pid)
  elif len(serial)==40:
    print "iPhone serial number (UDID) detected"
    pid = pidFromSerial(serial,8)
    print "Mobipocked PID for iPhone serial# "+serial+" is "+checksumPid(pid)
  else:
    print "Warning: unrecognized serial number. Please recheck input."
    sys.exit(1)
else:
  print "Usage: kindlepid.py <Kindle Serial Number>/<iPhone/iPod Touch UDID>"
