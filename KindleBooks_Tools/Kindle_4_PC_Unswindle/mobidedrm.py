#!/usr/bin/python
#
# This is a python script. You need a Python interpreter to run it.
# For example, ActiveState Python, which exists for windows.
#
# Changelog
#  0.01 - Initial version
#  0.02 - Huffdic compressed books were not properly decrypted
#  0.03 - Wasn't checking MOBI header length
#  0.04 - Wasn't sanity checking size of data record
#  0.05 - It seems that the extra data flags take two bytes not four
#  0.06 - And that low bit does mean something after all :-)
#  0.07 - The extra data flags aren't present in MOBI header < 0xE8 in size
#  0.08 - ...and also not in Mobi header version < 6
#  0.09 - ...but they are there with Mobi header version 6, header size 0xE4!
#  0.10 - Outputs unencrypted files as-is, so that when run as a Calibre
#         import filter it works when importing unencrypted files.
#         Also now handles encrypted files that don't need a specific PID.
#  0.11 - use autoflushed stdout and proper return values
#  0.12 - Fix for problems with metadata import as Calibre plugin, report errors
#  0.13 - Formatting fixes: retabbed file, removed trailing whitespace
#         and extra blank lines, converted CR/LF pairs at ends of each line,
#         and other cosmetic fixes.
#  0.14 - Working out when the extra data flags are present has been problematic
#         Versions 7 through 9 have tried to tweak the conditions, but have been
#         only partially successful. Closer examination of lots of sample
#         files reveals that a confusin has arisen because trailing data entries
#         are not encrypted, but it turns out that the multibyte entries
#         in utf8 file are encrypted. (Although neither kind gets compressed.)
#         This knowledge leads to a simplification of the test for the 
#         trailing data byte flags - version 5 and higher AND header size >= 0xE4. 
#  0.15 - Now outputs 'heartbeat', and is also quicker for long files.
#  0.16 - And reverts to 'done' not 'done.' at the end for unswindle compatibility.
#  0.17 - added modifications to support its use as an imported python module
#         both inside calibre and also in other places (ie K4DeDRM tools)
#  0.17a- disabled the standalone plugin feature since a plugin can not import
#         a plugin
#  0.18 - It seems that multibyte entries aren't encrypted in a v7 file...
#         Removed the disabled Calibre plug-in code
#         Permit use of 8-digit PIDs
#  0.19 - It seems that multibyte entries aren't encrypted in a v6 file either.
#  0.20 - Corretion: It seems that multibyte entries are encrypted in a v6 file.

__version__ = '0.20'

import sys
import struct
import binascii

class Unbuffered:
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

class DrmException(Exception):
    pass

# Implementation of Pukall Cipher 1
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

def getSizeOfTrailingDataEntries(ptr, size, flags):
    def getSizeOfTrailingDataEntry(ptr, size):
        bitpos, result = 0, 0
        if size <= 0:
            return result
        while True:
            v = ord(ptr[size-1])
            result |= (v & 0x7F) << bitpos
            bitpos += 7
            size -= 1
            if (v & 0x80) != 0 or (bitpos >= 28) or (size == 0):
                return result
    num = 0
    testflags = flags >> 1
    while testflags:
        if testflags & 1:
            num += getSizeOfTrailingDataEntry(ptr, size - num)
        testflags >>= 1
    # Check the low bit to see if there's multibyte data present.
    # if multibyte data is included in the encryped data, we'll
    # have already cleared this flag.
    if flags & 1:
        num += (ord(ptr[size - num - 1]) & 0x3) + 1
    return num

class DrmStripper:
    def loadSection(self, section):
        if (section + 1 == self.num_sections):
            endoff = len(self.data_file)
        else:
            endoff = self.sections[section + 1][0]
        off = self.sections[section][0]
        return self.data_file[off:endoff]

    def patch(self, off, new):
        self.data_file = self.data_file[:off] + new + self.data_file[off+len(new):]

    def patchSection(self, section, new, in_off = 0):
        if (section + 1 == self.num_sections):
            endoff = len(self.data_file)
        else:
            endoff = self.sections[section + 1][0]
        off = self.sections[section][0]
        assert off + in_off + len(new) <= endoff
        self.patch(off + in_off, new)

    def parseDRM(self, data, count, pid):
        pid = pid.ljust(16,'\0')
        keyvec1 = "\x72\x38\x33\xB0\xB4\xF2\xE3\xCA\xDF\x09\x01\xD6\xE2\xE0\x3F\x96"
        temp_key = PC1(keyvec1, pid, False)
        temp_key_sum = sum(map(ord,temp_key)) & 0xff
        found_key = None
        for i in xrange(count):
            verification, size, type, cksum, cookie = struct.unpack('>LLLBxxx32s', data[i*0x30:i*0x30+0x30])
            cookie = PC1(temp_key, cookie)
            ver,flags,finalkey,expiry,expiry2 = struct.unpack('>LL16sLL', cookie)
            if verification == ver and cksum == temp_key_sum and (flags & 0x1F) == 1:
                found_key = finalkey
                break
        if not found_key:
            # Then try the default encoding that doesn't require a PID
            temp_key = keyvec1
            temp_key_sum = sum(map(ord,temp_key)) & 0xff
            for i in xrange(count):
                verification, size, type, cksum, cookie = struct.unpack('>LLLBxxx32s', data[i*0x30:i*0x30+0x30])
                cookie = PC1(temp_key, cookie)
                ver,flags,finalkey,expiry,expiry2 = struct.unpack('>LL16sLL', cookie)
                if verification == ver and cksum == temp_key_sum:
                    found_key = finalkey
                    break
        return found_key

    def __init__(self, data_file, pid):
        if len(pid)==10:
            if checksumPid(pid[0:-2]) != pid:
                raise DrmException("invalid PID checksum")
            pid = pid[0:-2]
        elif len(pid)==8:
            print "PID without checksum given. With checksum PID is "+checksumPid(pid)
        else:
            raise DrmException("Invalid PID length")

        self.data_file = data_file
        header = data_file[0:72]
        if header[0x3C:0x3C+8] != 'BOOKMOBI':
            raise DrmException("invalid file format")
        self.num_sections, = struct.unpack('>H', data_file[76:78])

        self.sections = []
        for i in xrange(self.num_sections):
            offset, a1,a2,a3,a4 = struct.unpack('>LBBBB', data_file[78+i*8:78+i*8+8])
            flags, val = a1, a2<<16|a3<<8|a4
            self.sections.append( (offset, flags, val) )

        sect = self.loadSection(0)
        records, = struct.unpack('>H', sect[0x8:0x8+2])
        mobi_length, = struct.unpack('>L',sect[0x14:0x18])
        mobi_version, = struct.unpack('>L',sect[0x68:0x6C])
        extra_data_flags = 0
        print "MOBI header version = %d, length = %d" %(mobi_version, mobi_length)
        if (mobi_length >= 0xE4) and (mobi_version >= 5):
            extra_data_flags, = struct.unpack('>H', sect[0xF2:0xF4])
            print "Extra Data Flags = %d" %extra_data_flags
        if mobi_version < 7:
            # multibyte utf8 data is included in the encryption for mobi_version 6 and below
            # so clear that byte so that we leave it to be decrypted.
            extra_data_flags &= 0xFFFE

        crypto_type, = struct.unpack('>H', sect[0xC:0xC+2])
        if crypto_type == 0:
            print "This book is not encrypted."
        else:
            if crypto_type == 1:
                raise DrmException("cannot decode Mobipocket encryption type 1")
            if crypto_type != 2:
                raise DrmException("unknown encryption type: %d" % crypto_type)

            # calculate the keys
            drm_ptr, drm_count, drm_size, drm_flags = struct.unpack('>LLLL', sect[0xA8:0xA8+16])
            if drm_count == 0:
                raise DrmException("no PIDs found in this file")
            found_key = self.parseDRM(sect[drm_ptr:drm_ptr+drm_size], drm_count, pid)
            if not found_key:
                raise DrmException("no key found. maybe the PID is incorrect")

            # kill the drm keys
            self.patchSection(0, "\0" * drm_size, drm_ptr)
            # kill the drm pointers
            self.patchSection(0, "\xff" * 4 + "\0" * 12, 0xA8)
            # clear the crypto type
            self.patchSection(0, "\0" * 2, 0xC)

            # decrypt sections
            print "Decrypting. Please wait . . .",
            new_data = self.data_file[:self.sections[1][0]]
            for i in xrange(1, records+1):
                data = self.loadSection(i)
                extra_size = getSizeOfTrailingDataEntries(data, len(data), extra_data_flags)
                if i%100 == 0:
                    print ".",
                # print "record %d, extra_size %d" %(i,extra_size)
                new_data += PC1(found_key, data[0:len(data) - extra_size])
                if extra_size > 0:
                    new_data += data[-extra_size:]
                #self.patchSection(i, PC1(found_key, data[0:len(data) - extra_size]))
            if self.num_sections > records+1:
                new_data += self.data_file[self.sections[records+1][0]:]
            self.data_file = new_data
            print "done"

    def getResult(self):
        return self.data_file

def getUnencryptedBook(infile,pid):
    sys.stdout=Unbuffered(sys.stdout)
    data_file = file(infile, 'rb').read()
    strippedFile = DrmStripper(data_file, pid)
    return strippedFile.getResult()

def main(argv=sys.argv):
    sys.stdout=Unbuffered(sys.stdout)
    print ('MobiDeDrm v%(__version__)s. '
	   'Copyright 2008-2010 The Dark Reverser.' % globals())
    if len(argv)<4:
        print "Removes protection from Mobipocket books"
        print "Usage:"
        print "    %s <infile> <outfile> <PID>" % sys.argv[0]
        return 1
    else:
        infile = argv[1]
        outfile = argv[2]
        pid = argv[3]
        try:
            stripped_file = getUnencryptedBook(infile, pid)
            file(outfile, 'wb').write(stripped_file)
        except DrmException, e:
            print "Error: %s" % e
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
