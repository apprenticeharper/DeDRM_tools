# This is a python script. You need a Python interpreter to run it.
# For example, ActiveState Python, which exists for windows.
# Changelog
#  0.01 - Initial version
#  0.02 - Support more eReader files. Support bold text and links. Fix PML decoder parsing bug.
#  0.03 - Fix incorrect variable usage at one place.
#  0.03b - Add support for type 259

import struct, binascii, zlib, os, sha, sys, os.path

ECB =	0
CBC =	1
class Des:
	__pc1 = [56, 48, 40, 32, 24, 16,  8,  0, 57, 49, 41, 33, 25, 17,
		  9,  1, 58, 50, 42, 34, 26, 18, 10,  2, 59, 51, 43, 35,
		 62, 54, 46, 38, 30, 22, 14,  6, 61, 53, 45, 37, 29, 21,
		 13,  5, 60, 52, 44, 36, 28, 20, 12,  4, 27, 19, 11,  3]
	__left_rotations = [1, 1, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 1]
	__pc2 = [13, 16, 10, 23,  0,  4,2, 27, 14,  5, 20,  9,
		22, 18, 11,  3, 25,  7,	15,  6, 26, 19, 12,  1,
		40, 51, 30, 36, 46, 54,	29, 39, 50, 44, 32, 47,
		43, 48, 38, 55, 33, 52,	45, 41, 49, 35, 28, 31]
	__ip = [57, 49, 41, 33, 25, 17, 9,  1,	59, 51, 43, 35, 27, 19, 11, 3,
		61, 53, 45, 37, 29, 21, 13, 5,	63, 55, 47, 39, 31, 23, 15, 7,
		56, 48, 40, 32, 24, 16, 8,  0,	58, 50, 42, 34, 26, 18, 10, 2,
		60, 52, 44, 36, 28, 20, 12, 4,	62, 54, 46, 38, 30, 22, 14, 6]
	__expansion_table = [31,  0,  1,  2,  3,  4, 3,  4,  5,  6,  7,  8,
		 7,  8,  9, 10, 11, 12,11, 12, 13, 14, 15, 16,
		15, 16, 17, 18, 19, 20,19, 20, 21, 22, 23, 24,
		23, 24, 25, 26, 27, 28,27, 28, 29, 30, 31,  0]
	__sbox = [[14, 4, 13, 1, 2, 15, 11, 8, 3, 10, 6, 12, 5, 9, 0, 7,
		 0, 15, 7, 4, 14, 2, 13, 1, 10, 6, 12, 11, 9, 5, 3, 8,
		 4, 1, 14, 8, 13, 6, 2, 11, 15, 12, 9, 7, 3, 10, 5, 0,
		 15, 12, 8, 2, 4, 9, 1, 7, 5, 11, 3, 14, 10, 0, 6, 13],
		[15, 1, 8, 14, 6, 11, 3, 4, 9, 7, 2, 13, 12, 0, 5, 10,
		 3, 13, 4, 7, 15, 2, 8, 14, 12, 0, 1, 10, 6, 9, 11, 5,
		 0, 14, 7, 11, 10, 4, 13, 1, 5, 8, 12, 6, 9, 3, 2, 15,
		 13, 8, 10, 1, 3, 15, 4, 2, 11, 6, 7, 12, 0, 5, 14, 9],
		[10, 0, 9, 14, 6, 3, 15, 5, 1, 13, 12, 7, 11, 4, 2, 8,
		 13, 7, 0, 9, 3, 4, 6, 10, 2, 8, 5, 14, 12, 11, 15, 1,
		 13, 6, 4, 9, 8, 15, 3, 0, 11, 1, 2, 12, 5, 10, 14, 7,
		 1, 10, 13, 0, 6, 9, 8, 7, 4, 15, 14, 3, 11, 5, 2, 12],
		[7, 13, 14, 3, 0, 6, 9, 10, 1, 2, 8, 5, 11, 12, 4, 15,
		 13, 8, 11, 5, 6, 15, 0, 3, 4, 7, 2, 12, 1, 10, 14, 9,
		 10, 6, 9, 0, 12, 11, 7, 13, 15, 1, 3, 14, 5, 2, 8, 4,
		 3, 15, 0, 6, 10, 1, 13, 8, 9, 4, 5, 11, 12, 7, 2, 14],
		[2, 12, 4, 1, 7, 10, 11, 6, 8, 5, 3, 15, 13, 0, 14, 9,
		 14, 11, 2, 12, 4, 7, 13, 1, 5, 0, 15, 10, 3, 9, 8, 6,
		 4, 2, 1, 11, 10, 13, 7, 8, 15, 9, 12, 5, 6, 3, 0, 14,
		 11, 8, 12, 7, 1, 14, 2, 13, 6, 15, 0, 9, 10, 4, 5, 3],
		[12, 1, 10, 15, 9, 2, 6, 8, 0, 13, 3, 4, 14, 7, 5, 11,
		 10, 15, 4, 2, 7, 12, 9, 5, 6, 1, 13, 14, 0, 11, 3, 8,
		 9, 14, 15, 5, 2, 8, 12, 3, 7, 0, 4, 10, 1, 13, 11, 6,
		 4, 3, 2, 12, 9, 5, 15, 10, 11, 14, 1, 7, 6, 0, 8, 13],
		[4, 11, 2, 14, 15, 0, 8, 13, 3, 12, 9, 7, 5, 10, 6, 1,
		 13, 0, 11, 7, 4, 9, 1, 10, 14, 3, 5, 12, 2, 15, 8, 6,
		 1, 4, 11, 13, 12, 3, 7, 14, 10, 15, 6, 8, 0, 5, 9, 2,
		 6, 11, 13, 8, 1, 4, 10, 7, 9, 5, 0, 15, 14, 2, 3, 12],
		[13, 2, 8, 4, 6, 15, 11, 1, 10, 9, 3, 14, 5, 0, 12, 7,
		 1, 15, 13, 8, 10, 3, 7, 4, 12, 5, 6, 11, 0, 14, 9, 2,
		 7, 11, 4, 1, 9, 12, 14, 2, 0, 6, 10, 13, 15, 3, 5, 8,
		 2, 1, 14, 7, 4, 10, 8, 13, 15, 12, 9, 0, 3, 5, 6, 11],]
	__p = [15, 6, 19, 20, 28, 11,27, 16, 0, 14, 22, 25,
		4, 17, 30, 9, 1, 7,23,13, 31, 26, 2, 8,18, 12, 29, 5, 21, 10,3, 24]
	__fp = [39,  7, 47, 15, 55, 23, 63, 31,38,  6, 46, 14, 54, 22, 62, 30,
		37,  5, 45, 13, 53, 21, 61, 29,36,  4, 44, 12, 52, 20, 60, 28,
		35,  3, 43, 11, 51, 19, 59, 27,34,  2, 42, 10, 50, 18, 58, 26,
		33,  1, 41,  9, 49, 17, 57, 25,32,  0, 40,  8, 48, 16, 56, 24]
	# Type of crypting being done
	ENCRYPT =	0x00
	DECRYPT =	0x01
	def __init__(self, key, mode=ECB, IV=None):
		if len(key) != 8:
			raise ValueError("Invalid DES key size. Key must be exactly 8 bytes long.")
		self.block_size = 8
		self.key_size = 8
		self.__padding = ''
		self.setMode(mode)
		if IV:
			self.setIV(IV)
		self.L = []
		self.R = []
		self.Kn = [ [0] * 48 ] * 16	# 16 48-bit keys (K1 - K16)
		self.final = []
		self.setKey(key)
	def getKey(self):
		return self.__key
	def setKey(self, key):
		self.__key = key
		self.__create_sub_keys()
	def getMode(self):
		return self.__mode
	def setMode(self, mode):
		self.__mode = mode
	def getIV(self):
		return self.__iv
	def setIV(self, IV):
		if not IV or len(IV) != self.block_size:
			raise ValueError("Invalid Initial Value (IV), must be a multiple of " + str(self.block_size) + " bytes")
		self.__iv = IV
	def getPadding(self):
		return self.__padding
	def __String_to_BitList(self, data):
		l = len(data) * 8
		result = [0] * l
		pos = 0
		for c in data:
			i = 7
			ch = ord(c)
			while i >= 0:
				if ch & (1 << i) != 0:
					result[pos] = 1
				else:
					result[pos] = 0
				pos += 1
				i -= 1
		return result
	def __BitList_to_String(self, data):
		result = ''
		pos = 0
		c = 0
		while pos < len(data):
			c += data[pos] << (7 - (pos % 8))
			if (pos % 8) == 7:
				result += chr(c)
				c = 0
			pos += 1
		return result
	def __permutate(self, table, block):
		return map(lambda x: block[x], table)
	def __create_sub_keys(self):
		key = self.__permutate(Des.__pc1, self.__String_to_BitList(self.getKey()))
		i = 0
		self.L = key[:28]
		self.R = key[28:]
		while i < 16:
			j = 0
			while j < Des.__left_rotations[i]:
				self.L.append(self.L[0])
				del self.L[0]
				self.R.append(self.R[0])
				del self.R[0]
				j += 1
			self.Kn[i] = self.__permutate(Des.__pc2, self.L + self.R)
			i += 1
	def __des_crypt(self, block, crypt_type):
		block = self.__permutate(Des.__ip, block)
		self.L = block[:32]
		self.R = block[32:]
		if crypt_type == Des.ENCRYPT:
			iteration = 0
			iteration_adjustment = 1
		else:
			iteration = 15
			iteration_adjustment = -1
		i = 0
		while i < 16:
			tempR = self.R[:]
			self.R = self.__permutate(Des.__expansion_table, self.R)
			self.R = map(lambda x, y: x ^ y, self.R, self.Kn[iteration])
			B = [self.R[:6], self.R[6:12], self.R[12:18], self.R[18:24], self.R[24:30], self.R[30:36], self.R[36:42], self.R[42:]]
			j = 0
			Bn = [0] * 32
			pos = 0
			while j < 8:
				m = (B[j][0] << 1) + B[j][5]
				n = (B[j][1] << 3) + (B[j][2] << 2) + (B[j][3] << 1) + B[j][4]
				v = Des.__sbox[j][(m << 4) + n]
				Bn[pos] = (v & 8) >> 3
				Bn[pos + 1] = (v & 4) >> 2
				Bn[pos + 2] = (v & 2) >> 1
				Bn[pos + 3] = v & 1
				pos += 4
				j += 1
			self.R = self.__permutate(Des.__p, Bn)
			self.R = map(lambda x, y: x ^ y, self.R, self.L)
			self.L = tempR
			i += 1
			iteration += iteration_adjustment
		self.final = self.__permutate(Des.__fp, self.R + self.L)
		return self.final
	def crypt(self, data, crypt_type):
		if not data:
			return ''
		if len(data) % self.block_size != 0:
			if crypt_type == Des.DECRYPT: # Decryption must work on 8 byte blocks
				raise ValueError("Invalid data length, data must be a multiple of " + str(self.block_size) + " bytes\n.")
			if not self.getPadding():
				raise ValueError("Invalid data length, data must be a multiple of " + str(self.block_size) + " bytes\n. Try setting the optional padding character")
			else:
				data += (self.block_size - (len(data) % self.block_size)) * self.getPadding()
		if self.getMode() == CBC:
			if self.getIV():
				iv = self.__String_to_BitList(self.getIV())
			else:
				raise ValueError("For CBC mode, you must supply the Initial Value (IV) for ciphering")
		i = 0
		dict = {}
		result = []
		while i < len(data):
			block = self.__String_to_BitList(data[i:i+8])
			if self.getMode() == CBC:
				if crypt_type == Des.ENCRYPT:
					block = map(lambda x, y: x ^ y, block, iv)
				processed_block = self.__des_crypt(block, crypt_type)
				if crypt_type == Des.DECRYPT:
					processed_block = map(lambda x, y: x ^ y, processed_block, iv)
					iv = block
				else:
					iv = processed_block
			else:
				processed_block = self.__des_crypt(block, crypt_type)
			result.append(self.__BitList_to_String(processed_block))
			i += 8
		if crypt_type == Des.DECRYPT and self.getPadding():
			s = result[-1]
			while s[-1] == self.getPadding():
				s = s[:-1]
			result[-1] = s
		return ''.join(result)
	def encrypt(self, data, pad=''):
		self.__padding = pad
		return self.crypt(data, Des.ENCRYPT)
	def decrypt(self, data, pad=''):
		self.__padding = pad
		return self.crypt(data, Des.DECRYPT)

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

def sanitizeFileName(s):
	r = ''
	for c in s.lower():
		if c in "abcdefghijklmnopqrstuvwxyz0123456789_.-":
			r += c
	return r

def fixKey(key):
	def fixByte(b):
		return b ^ ((b ^ (b<<1) ^ (b<<2) ^ (b<<3) ^ (b<<4) ^ (b<<5) ^ (b<<6) ^ (b<<7) ^ 0x80) & 0x80)
	return 	"".join([chr(fixByte(ord(a))) for a in key])

class EreaderProcessor:
	def __init__(self, section_reader, username, creditcard):
		self.section_reader = section_reader
		data = section_reader(0)
		version,  = struct.unpack('>H', data[0:2])
		if version != 272 and version != 260 and version != 259:
			raise ValueError('incorrect eReader version %d (error 1)' % version)
		data = section_reader(1)
		self.data = data
		des = Des(fixKey(data[0:8]))
		cookie_shuf, cookie_size = struct.unpack('>LL', des.decrypt(data[-8:]))
		if cookie_shuf < 3 or cookie_shuf > 0x14 or cookie_size < 0xf0 or cookie_size > 0x200:
			raise ValueError('incorrect eReader version (error 2)')
		input = des.decrypt(data[-cookie_size:])
		def unshuff(data, shuf):
			r = [''] * len(data)
			j = 0
			for i in xrange(len(data)):
				j = (j + shuf) % len(data)
				r[j] = data[i]
			assert	len("".join(r)) == len(data)
			return "".join(r)
		r = unshuff(input[0:-8], cookie_shuf)
		def fixUsername(s):
			r = ''
			for c in s.lower():
				if (c >= 'a' and c <= 'z' or c >= '0' and c <= '9'):
					r += c
			return r
		user_key = struct.pack('>LL', binascii.crc32(fixUsername(username)) & 0xffffffff, binascii.crc32(creditcard[-8:])& 0xffffffff)
		drm_sub_version = struct.unpack('>H', r[0:2])[0]
		self.num_text_pages = struct.unpack('>H', r[2:4])[0] - 1
		self.num_image_pages = struct.unpack('>H', r[26:26+2])[0]
		self.first_image_page = struct.unpack('>H', r[24:24+2])[0]
		self.flags = struct.unpack('>L', r[4:8])[0]
		reqd_flags = (1<<9) | (1<<7) | (1<<10)
		if (self.flags & reqd_flags) != reqd_flags:
			print "Flags: 0x%X" % self.flags
			raise ValueError('incompatible eReader file')
		des = Des(fixKey(user_key))
		if version == 259:
			if drm_sub_version != 7:
				raise ValueError('incorrect eReader version %d (error 3)' % drm_sub_version)
			encrypted_key_sha = r[44:44+20]
			encrypted_key = r[64:64+8]
		elif version == 260:
			if drm_sub_version != 13:
				raise ValueError('incorrect eReader version %d (error 3)' % drm_sub_version)
			encrypted_key = r[44:44+8]
			encrypted_key_sha = r[52:52+20]
		elif version == 272:
			encrypted_key = r[172:172+8]
			encrypted_key_sha = r[56:56+20]
		self.content_key = des.decrypt(encrypted_key)
		if sha.new(self.content_key).digest() != encrypted_key_sha:
			raise ValueError('Incorrect Name and/or Credit Card')
	def getNumImages(self):
		return self.num_image_pages
	def getImage(self, i):
		sect = self.section_reader(self.first_image_page + i)
		name = sect[4:4+32].strip('\0')
		data = sect[62:]
		return sanitizeFileName(name), data
	def getText(self):
		des = Des(fixKey(self.content_key))
		r = ''
		for i in xrange(self.num_text_pages):
			r += zlib.decompress(des.decrypt(self.section_reader(1 + i)))
		return r

class PmlConverter:
	def __init__(self, s):
		self.s = s
		self.pos = 0
	def nextOptAttr(self):
		p = self.pos
		if self.s[p:p+2] != '="':
			return None
		r = ''
		p += 2
		while self.s[p] != '"':
			r += self.s[p]
			p += 1
		self.pos = p + 1
		return r
	def next(self):
		p = self.pos
		if p >= len(self.s):
			return None
		if self.s[p] != '\\':
			res = self.s.find('\\', p)
			if res == -1:
				res = len(self.s)
			self.pos = res
			return self.s[p : res], None, None
		c = self.s[p+1]
		if c in 'pxcriuovtnsblBk-lI\\d':
			self.pos = p + 2
			return None, c, None
		if c in 'TwmqQ':
			self.pos = p + 2
			return None, c, self.nextOptAttr()
		if c == 'a':
			self.pos = p + 5
			return None, c, int(self.s[p+2:p+5])
		if c == 'U':
			self.pos = p + 6
			return None, c, int(self.s[p+2:p+6], 16)
		c = self.s[p+1:p+1+2]
		if c in ('X0','X1','X2','X3','X4','Sp','Sb'):
			self.pos = p + 3
			return None, c, None
		if c in ('C0','C1','C2','C3','C4','Fn','Sd'):
			self.pos = p + 3
			return None, c, self.nextOptAttr()
		print "unknown escape code %s" % c
		self.pos = p + 1
		return None, None, None
	def linkPrinter(link):
		return '<a href="%s">' % link
	
	html_tags = {
		'c' : ('<p align="center">', '</p>'),
		'r' : ('<p align="right">', '</p>'),
		'i' : ('<i>', '</i>'),
		'u' : ('<u>', '</u>'),
		'b' : ('<strong>', '</strong>'),
		'B' : ('<strong>', '</strong>'),
		'o' : ('<strike>', '</strike>'),
		'v' : ('<!-- ', ' -->'),
		't' : ('', ''),
		'Sb' : ('<sub>', '</sub>'),
		'Sp' : ('<sup>', '</sup>'),
		'X0' : ('<h1>', '</h1>'),
		'X1' : ('<h2>', '</h2>'),
		'X2' : ('<h3>', '</h3>'),
		'X3' : ('<h4>', '</h4>'),
		'X4' : ('<h5>', '</h5>'),
		'l' : ('<font size="+2">', '</font>'),
		'q' : (linkPrinter, '</a>'),
	}
	html_one_tags = {
		'p' : '<br><br>'
	}
	pml_chars = {
		160 : '&nbsp;',130 : '&#8212;',131: '&#402;',132: '&#8222;',
		133: '&#8230;',134: '&#8224;',135: '&#8225;',138: '&#352;',
		139: '&#8249;',140: '&#338;',145: '&#8216;',146: '&#8217;',
		147: '&#8220;',148: '&#8221;',149: '&#8226;',150: '&#8211;',
		151: '&#8212;',153: '&#8482;',154: '&#353;',155: '&#8250;',
		156: '&#339;',159: '&#376;'
	}
	def process(self):
		final = '<html><body>\n'
		in_tags = []
		def makeText(s):
			s = s.replace('&', '&amp;')
			#s = s.replace('"', '&quot;')
			s = s.replace('<', '&lt;')
			s = s.replace('>', '&gt;')
			s = s.replace('\n', '<br>\n')
			return s
		while True:
			r = self.next()
			if not r:
				break
			text, cmd, attr = r
			if text:
				final += makeText(text)
			if cmd:
				def getTag(ti, end):
					cmd, attr = ti
					r = self.html_tags[cmd][end]
					if type(r) != str:
						r = r(attr)
					return r
					
				if cmd in self.html_tags:
					pair = (cmd, attr)
					if cmd not in [a for (a,b) in in_tags]:
						final += getTag(pair, False)
						in_tags.append(pair)
					else:
						j = len(in_tags)
						while True:
							j = j - 1
							final += getTag(in_tags[j], True)
							if in_tags[j][0] == cmd:
								break
						del in_tags[j]
						while j < len(in_tags):
							final += getTag(in_tags[j], False)
							j = j + 1
							
				if cmd in self.html_one_tags:
					final += self.html_one_tags[cmd]
				if cmd == 'm':
					final += '<img src="%s">' % attr
				if cmd == 'Q':
					final += '<a name="%s"> </a>' % attr
				if cmd == 'a':
					final += self.pml_chars.get(attr, '&#%d;' % attr)
				if cmd == 'U':
					final += '&#%d;' % attr
		final += '</body></html>\n'
		while True:
			s = final.replace('<br>\n<br>\n<br>\n', '<br>\n<br>\n')
			if s == final:
				break
			final = s
		return final

def convertEreaderToHtml(infile, name, cc, outdir):
	if not os.path.exists(outdir):
		os.makedirs(outdir)
	sect = Sectionizer(infile, 'PNRdPPrs')
	er = EreaderProcessor(sect.loadSection, name, cc)

	for i in xrange(er.getNumImages()):
		name, contents = er.getImage(i)
		file(os.path.join(outdir, name), 'wb').write(contents)

	pml = PmlConverter(er.getText())
	file(os.path.join(outdir, 'book.html'),'wb').write(pml.process())

print "eReader2Html v0.03b, derived from:"
print "\teReader2Html v0.03. Copyright (c) 2008 The Dark Reverser"
print "with enhancement by DeBockle"
if len(sys.argv)!=5:
	print "Converts eReader books to HTML"
	print "Usage:"
	print "  ereader2html infile.pdb outdir \"your name\" credit_card_number "
	print "Note:"
	print "  It's enough to enter the last 8 digits of the credit card number"
else:  
	infile, outdir, name, cc = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
	try:
		print "Processing...",
		convertEreaderToHtml(infile, name, cc, outdir)
		print "done"
	except ValueError, e:
		print "Error: %s" % e
