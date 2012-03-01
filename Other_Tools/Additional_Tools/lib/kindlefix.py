class Unbuffered:
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

import sys
sys.stdout=Unbuffered(sys.stdout)


import prc, struct
from binascii import hexlify

def strByte(s,off=0):
    return struct.unpack(">B",s[off])[0];

def strSWord(s,off=0):
    return struct.unpack(">h",s[off:off+2])[0];

def strWord(s,off=0):
    return struct.unpack(">H",s[off:off+2])[0];

def strDWord(s,off=0):
    return struct.unpack(">L",s[off:off+4])[0];

def strPutDWord(s,off,i):
    return s[:off]+struct.pack(">L",i)+s[off+4:];

keyvec1 = "\x72\x38\x33\xB0\xB4\xF2\xE3\xCA\xDF\x09\x01\xD6\xE2\xE0\x3F\x96"

#implementation of Pukall Cipher 1
def PC1(key, src, decryption=True):
    sum1 = 0;
    sum2 = 0;
    keyXorVal = 0;
    if len(key)!=16:
        print "Bad key length!"
        return None
    wkey = []
    for i in xrange(8):
        wkey.append(ord(key[i*2])<<8 | ord(key[i*2+1]))

    dst = ""
    for i in xrange(len(src)):
        temp1 = 0;
        byteXorVal = 0;
        for j in xrange(8):
            temp1 ^= wkey[j]
            sum2  = (sum2+j)*20021 + sum1
            sum1  = (temp1*346)&0xFFFF
            sum2  = (sum2+sum1)&0xFFFF
            temp1 = (temp1*20021+1)&0xFFFF
            byteXorVal ^= temp1 ^ sum2
        
        curByte = ord(src[i])
        if not decryption:
            keyXorVal = curByte * 257;
        curByte = ((curByte ^ (byteXorVal >> 8)) ^ byteXorVal) & 0xFF
        if decryption:
            keyXorVal = curByte * 257;
        for j in xrange(8):
            wkey[j] ^= keyXorVal;

        dst+=chr(curByte)
    
    return dst

def find_key(rec0, pid):
    off1 = strDWord(rec0, 0xA8)
    if off1==0xFFFFFFFF or off1==0:
      print "No DRM"
      return None
    size1 = strDWord(rec0, 0xB0)
    cnt  = strDWord(rec0, 0xAC)
    flag = strDWord(rec0, 0xB4)

    temp_key = PC1(keyvec1, pid.ljust(16,'\0'), False)
    cksum = 0
    #print pid, "->", hexlify(temp_key)
    for i in xrange(len(temp_key)):
      cksum += ord(temp_key[i])
    cksum &= 0xFF
    temp_key = temp_key.ljust(16,'\0')
    #print "pid cksum: %02X"%cksum

    #print "Key records: %02X-%02X, count: %d, flag: %02X"%(off1, off1+size1, cnt, flag)
    iOff = off1
    drm_key = None
    for i in xrange(cnt):
      dwCheck = strDWord(rec0, iOff)
      dwSize  = strDWord(rec0, iOff+4)
      dwType  = strDWord(rec0, iOff+8)
      nCksum  = strByte(rec0, iOff+0xC)
      #print "Key record %d: check=%08X, size=%d, type=%d, cksum=%02X"%(i, dwCheck, dwSize, dwType, nCksum)
      if nCksum==cksum:
        drmInfo = PC1(temp_key, rec0[iOff+0x10:iOff+0x30])
        dw0, dw4, dw18, dw1c = struct.unpack(">II16xII", drmInfo)
        #print "Decrypted drmInfo:", "%08X, %08X, %s, %08X, %08X"%(dw0, dw4, hexlify(drmInfo[0x8:0x18]), dw18, dw1c)
        #print "Decrypted drmInfo:", hexlify(drmInfo)
        if dw0==dwCheck:
            print "Found the matching record; setting the CustomDRM flag for Kindle" 
            drmInfo = strPutDWord(drmInfo,4,(dw4|0x800))
            dw0, dw4, dw18, dw1c = struct.unpack(">II16xII", drmInfo)
            #print "Updated drmInfo:", "%08X, %08X, %s, %08X, %08X"%(dw0, dw4, hexlify(drmInfo[0x8:0x18]), dw18, dw1c)
            return rec0[:iOff+0x10] + PC1(temp_key, drmInfo, False) + rec0[:iOff+0x30]
      iOff += dwSize
    return None

def replaceext(filename, newext):
  nameparts = filename.split(".")
  if len(nameparts)>1:
    return (".".join(nameparts[:-1]))+newext
  else:
    return nameparts[0]+newext

def main(argv=sys.argv):
  print "The Kindleizer v0.2. Copyright (c) 2007 Igor Skochinsky"
  if len(sys.argv) != 3:
      print "Fixes encrypted Mobipocket books to be readable by Kindle"
      print "Usage: kindlefix.py file.mobi PID"
      return 1
  fname = sys.argv[1]
  pid = sys.argv[2]
  if len(pid)==10 and pid[-3]=='*':
    pid = pid[:-2]
  if len(pid)!=8 or pid[-1]!='*':
    print "PID is not valid! (should be in format AAAAAAA*DD)"
    return 3
  db = prc.File(fname)
  #print dir(db)
  if db.getDBInfo()["creator"]!='MOBI':
    print "Not a Mobi file!"
    return 1
  rec0 = db.getRecord(0)[0]
  enc = strSWord(rec0, 0xC)
  print "Encryption:", enc
  if enc!=2:
    print "Unknown encryption type"
    return 1

  if len(rec0)<0x28 or rec0[0x10:0x14] != 'MOBI':
    print "bad file format"
    return 1
  print "Mobi publication type:", strDWord(rec0, 0x18)
  formatVer = strDWord(rec0, 0x24)
  print "Mobi format version:", formatVer
  last_rec = strWord(rec0, 8)
  dwE0 = 0
  if formatVer>=4:
    new_rec0 = find_key(rec0, pid)
    if new_rec0:
      db.setRecordIdx(0,new_rec0)
    else:
      print "PID doesn't match this file"
      return 2
  else:
    print "Wrong Mobi format version"
    return 1

  outfname = replaceext(fname, ".azw")
  if outfname==fname:
    outfname = replaceext(fname, "_fixed.azw")
  db.save(outfname)
  print "Output written to "+outfname
  return 0


if __name__ == "__main__":
    sys.exit(main())
