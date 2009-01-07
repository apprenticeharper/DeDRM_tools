#!/usr/bin/python
#
# This is a python script. You need a Python interpreter to run it.
# For example, ActiveState Python, which exists for windows.
#
# It can run standalone to convert files, or it can be installed as a
# plugin for Calibre (http://calibre-ebook.com/about) so that
# importing files with DRM 'Just Works'.
#
# To create a Calibre plugin, rename this file so that the filename
# ends in '_plugin.py', put it into a ZIP file and import that Calibre
# using its plugin configuration GUI.
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
		mobi_length, = struct.unpack('>L',sect[0x14:0x18])
		mobi_version, = struct.unpack('>L',sect[0x68:0x6C])
		extra_data_flags = 0
		print "MOBI header length = %d" %mobi_length
		print "MOBI header version = %d" %mobi_version
		if (mobi_length >= 0xE4) and (mobi_version > 5):
			extra_data_flags, = struct.unpack('>H', sect[0xF2:0xF4])
			print "Extra Data Flags = %d" %extra_data_flags


		crypto_type, = struct.unpack('>H', sect[0xC:0xC+2])
		if crypto_type == 0:
			raise DrmException("it seems that this book isn't encrypted")
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
		print "Decrypting. Please wait...",
		for i in xrange(1, records+1):
			data = self.loadSection(i)
			extra_size = getSizeOfTrailingDataEntries(data, len(data), extra_data_flags)
			# print "record %d, extra_size %d" %(i,extra_size)
			self.patchSection(i, PC1(found_key, data[0:len(data) - extra_size]))
		print "done"
	def getResult(self):
		return self.data_file

if not __name__ == "__main__":
	from calibre.customize import FileTypePlugin

	class MobiDeDRM(FileTypePlugin):

		name                = 'MobiDeDRM' # Name of the plugin
		description         = 'Removes DRM from secure Mobi files'
		supported_platforms = ['linux', 'osx', 'windows'] # Platforms this plugin will run on
		author              = 'The Dark Reverser' # The author of this plugin
		version             = (0, 0, 9)   # The version number of this plugin
		file_types          = set(['prc','mobi','azw']) # The file types that this plugin will be applied to
		on_import           = True # Run this plugin during the import

	
		def run(self, path_to_ebook):
			of = self.temporary_file('.mobi')
			PID = self.site_customization
			data_file = file(path_to_ebook, 'rb').read()
			ar = PID.split(',')
			for i in ar:
				try:
					file(of.name, 'wb').write(DrmStripper(data_file, i).getResult())
				except DrmException:
					# Hm, we should display an error dialog here.
					# Dunno how though.
					# Ignore the dirty hack behind the curtain.
#					strexcept = 'echo exception: %s > /dev/tty' % e
#					subprocess.call(strexcept,shell=True)
					print i + ": not PID for book"
				else:
					return of.name

		def customization_help(self, gui=False):
			return 'Enter PID (separate multiple PIDs with comma)'

if __name__ == "__main__":
	print "MobiDeDrm v0.09. Copyright (c) 2008 The Dark Reverser"
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
