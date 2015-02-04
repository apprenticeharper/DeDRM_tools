# This is a python script. You need a Python interpreter to run it.
# For example, ActiveState Python, which exists for windows.
#
# Big Thanks to Igor SKOCHINSKY for providing me with all his information
# and source code relating to the inner workings of this compression scheme.
# Without it, I wouldn't be able to solve this as easily.
#
# Changelog
#  0.01 - Initial version
#  0.02 - Fix issue with size computing
#  0.03 - Fix issue with some files
#  0.04 - make stdout self flushing and fix return values

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


import struct

class BitReader:
	def __init__(self, data):
		self.data, self.pos, self.nbits = data + "\x00\x00\x00\x00", 0, len(data) * 8
	def peek(self, n):
		r, g = 0, 0
		while g < n:
			r, g = (r << 8) | ord(self.data[(self.pos+g)>>3]), g + 8 - ((self.pos+g) & 7)
		return (r >> (g - n)) & ((1 << n) - 1)
	def eat(self, n):
		self.pos += n
		return self.pos <= self.nbits
	def left(self):
		return self.nbits - self.pos

class HuffReader:
	def __init__(self, huffs):
		self.huffs = huffs
		h = huffs[0]
		if huffs[0][0:4] != 'HUFF' or huffs[0][4:8] != '\x00\x00\x00\x18':
			raise ValueError('invalid huff1 header')
		if huffs[1][0:4] != 'CDIC' or huffs[1][4:8] != '\x00\x00\x00\x10':
			raise ValueError('invalid huff2 header')
		self.entry_bits, = struct.unpack('>L', huffs[1][12:16])
		off1,off2 = struct.unpack('>LL', huffs[0][16:24])
		self.dict1 = struct.unpack('<256L', huffs[0][off1:off1+256*4])
		self.dict2 = struct.unpack('<64L', huffs[0][off2:off2+64*4])
		self.dicts = huffs[1:]
		self.r = ''
		
	def _unpack(self, bits, depth = 0):
		if depth > 32:
			raise ValueError('corrupt file')
		while bits.left():
			dw = bits.peek(32)
			v = self.dict1[dw >> 24]
			codelen = v & 0x1F
			assert codelen != 0
			code = dw >> (32 - codelen)
			r = (v >> 8)
			if not (v & 0x80):
				while code < self.dict2[(codelen-1)*2]:
					codelen += 1
					code = dw >> (32 - codelen)
				r = self.dict2[(codelen-1)*2+1]
			r -= code
			assert codelen != 0
			if not bits.eat(codelen):
				return
			dicno = r >> self.entry_bits
			off1 = 16 + (r - (dicno << self.entry_bits)) * 2
			dic = self.dicts[dicno]
			off2 = 16 + ord(dic[off1]) * 256 + ord(dic[off1+1])
			blen = ord(dic[off2]) * 256 + ord(dic[off2+1])
			slice = dic[off2+2:off2+2+(blen&0x7fff)]
			if blen & 0x8000:
				self.r += slice
			else:
				self._unpack(BitReader(slice), depth + 1)

	def unpack(self, data):
		self.r = ''
		self._unpack(BitReader(data))
		return self.r

class Sectionizer:
	def __init__(self, filename, ident):
		self.contents = file(filename, 'rb').read()
		self.header = self.contents[0:72]
		self.num_sections, = struct.unpack('>H', self.contents[76:78])
		if self.header[0x3C:0x3C+8] != ident:
			raise ValueError('Invalid file format')
		self.sections = []
		for i in xrange(self.num_sections):
			offset, a1,a2,a3,a4 = struct.unpack('>LBBBB', self.contents[78+i*8:78+i*8+8])
			flags, val = a1, a2<<16|a3<<8|a4
			self.sections.append( (offset, flags, val) )
	def loadSection(self, section):
		if section + 1 == self.num_sections:
			end_off = len(self.contents)
		else:
			end_off = self.sections[section + 1][0]
		off = self.sections[section][0]
		return self.contents[off:end_off]


def getSizeOfTrailingDataEntry(ptr, size):
	bitpos, result = 0, 0
	while True:
		v = ord(ptr[size-1])
		result |= (v & 0x7F) << bitpos
		bitpos += 7
		size -= 1
		if (v & 0x80) != 0 or (bitpos >= 28) or (size == 0):
			return result

def getSizeOfTrailingDataEntries(ptr, size, flags):
	num = 0
	flags >>= 1
	while flags:
		if flags & 1:
			num += getSizeOfTrailingDataEntry(ptr, size - num)
		flags >>= 1		
	return num

def unpackBook(input_file):
	sect = Sectionizer(input_file, 'BOOKMOBI')

	header = sect.loadSection(0)

	crypto_type, = struct.unpack('>H', header[0xC:0xC+2])
	if crypto_type != 0:
		raise ValueError('The book is encrypted. Run mobidedrm first')

	if header[0:2] != 'DH':
		raise ValueError('invalid compression type')

	extra_flags, = struct.unpack('>L', header[0xF0:0xF4])
	records, = struct.unpack('>H', header[0x8:0x8+2])

	huffoff,huffnum = struct.unpack('>LL', header[0x70:0x78])
	huffs = [sect.loadSection(i) for i in xrange(huffoff, huffoff+huffnum)]
	huff = HuffReader(huffs)

	def decompressSection(nr):
		data = sect.loadSection(nr)
		trail_size = getSizeOfTrailingDataEntries(data, len(data), extra_flags)
		return huff.unpack(data[0:len(data)-trail_size])

	r = ''
	for i in xrange(1, records+1):
		r += decompressSection(i)
	return r

def main(argv=sys.argv):
    print "MobiHuff v0.03"
    print "  Copyright (c) 2008 The Dark Reverser <dark.reverser@googlemail.com>"
    if len(sys.argv)!=3:
        print ""
	print "Description:"
	print "  Unpacks the new mobipocket huffdic compression."
	print "  This program works with unencrypted files only."
	print "Usage:"
	print "  mobihuff.py infile.mobi outfile.html"
	return 1
    else:  
	infile = sys.argv[1]
	outfile = sys.argv[2]
	try:
		print "Decompressing...",
		result = unpackBook(infile)
		file(outfile, 'wb').write(result)
		print "done"
	except ValueError, e:
		print 
		print "Error: %s" % e
		return 1
	return 0


if __name__ == "__main__":
    sys.exit(main())
