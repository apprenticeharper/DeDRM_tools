# This is a python script. You need a Python interpreter to run it.
# For example, ActiveState Python, which exists for windows.
#
# Changelog
#  0.01 - Initial version
#  0.02 - Huffdic compressed books were not properly decrypted

import sys,struct,binascii

class DrmException(Exception):
	pass

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
		while True:
			v = ord(ptr[size-1])
			result |= (v & 0x7F) << bitpos
			bitpos += 7
			size -= 1
			if (v & 0x80) != 0 or (bitpos >= 28) or (size == 0):
				return result
	num = 0
	flags >>= 1
	while flags:
		if flags & 1:
			num += getSizeOfTrailingDataEntry(ptr, size - num)
		flags >>= 1		
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
		return found_key		


	def __init__(self, data_file, pid):

		if checksumPid(pid[0:-2]) != pid:
			raise DrmException("invalid PID checksum")
		pid = pid[0:-2]
		
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
		extra_data_flags, = struct.unpack('>L', sect[0xF0:0xF4])

		crypto_type, = struct.unpack('>H', sect[0xC:0xC+2])
		if crypto_type != 2:
			raise DrmException("invalid encryption type: %d" % crypto_type)

		# calculate the keys
		drm_ptr, drm_count, drm_size, drm_flags = struct.unpack('>LLLL', sect[0xA8:0xA8+16])
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
		print "Decrypting. Please wait...",
		for i in xrange(1, records+1):
			data = self.loadSection(i)
			extra_size = getSizeOfTrailingDataEntries(data, len(data), extra_data_flags)
			self.patchSection(i, PC1(found_key, data[0:len(data) - extra_size]))
		print "done"
	def getResult(self):
		return self.data_file

print "MobiDeDrm v0.02. Copyright (c) 2008 The Dark Reverser"
if len(sys.argv)<4:
	print "Removes protection from Mobipocket books"
	print "Usage:"
	print "  mobidedrm infile.mobi outfile.mobi PID"
else:  
	infile = sys.argv[1]
	outfile = sys.argv[2]
	pid = sys.argv[3]
	data_file = file(infile, 'rb').read()
	try:
		file(outfile, 'wb').write(DrmStripper(data_file, pid).getResult())
	except DrmException, e:
		print "Error: %s" % e