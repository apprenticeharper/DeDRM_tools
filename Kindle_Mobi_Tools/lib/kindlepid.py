import sys, binascii

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

print "Mobipocket PID calculator for Amazon Kindle. Copyright (c) 2007 Igor Skochinsky <skochinsky@mail.ru>"
if len(sys.argv)>1:
  pid = pidFromSerial(sys.argv[1],7)+"*"
  print "Mobipocked PID for Kindle serial# "+sys.argv[1]+" is "+checksumPid(pid)
else:
  print "Usage: kindlepid.py <Kindle Serial Number>"
