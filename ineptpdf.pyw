#! /usr/bin/python

# ineptpdf.pyw, version 6.1

# To run this program install Python 2.6 from http://www.python.org/download/
# and PyCrypto from http://www.voidspace.org.uk/python/modules.shtml#pycrypto
# (make sure to install the version for Python 2.6).  Save this script file as
# ineptpdf.pyw and double-click on it to run it.

# Revision history:
#   1 - Initial release
#   2 - Improved determination of key-generation algorithm
#   3 - Correctly handle PDF >=1.5 cross-reference streams
#   4 - Removal of ciando's personal ID (anon)
#   5 - removing small bug with V3 ebooks (anon)
#   6 - changed to adeptkey4.der format for 1.7.2 support (anon)
#   6.1 - backward compatibility for 1.7.1 and old adeptkey.der
"""
Decrypt Adobe ADEPT-encrypted PDF files.
"""

from __future__ import with_statement

__license__ = 'GPL v3'

import sys
import os
import re
import zlib
import struct
import hashlib
from itertools import chain, islice
import xml.etree.ElementTree as etree
import Tkinter
import Tkconstants
import tkFileDialog
import tkMessageBox

try:
    from Crypto.Cipher import ARC4
    from Crypto.PublicKey import RSA
except ImportError:
    ARC4 = None
    RSA = None


class ADEPTError(Exception):
    pass


### 
### ASN.1 parsing code from tlslite

def bytesToNumber(bytes):
    total = 0L
    for byte in bytes:
        total = (total << 8) + byte
    return total

class ASN1Error(Exception):
    pass

class ASN1Parser(object):
    class Parser(object):
        def __init__(self, bytes):
            self.bytes = bytes
            self.index = 0
    
        def get(self, length):
            if self.index + length > len(self.bytes):
                raise ASN1Error("Error decoding ASN.1")
            x = 0
            for count in range(length):
                x <<= 8
                x |= self.bytes[self.index]
                self.index += 1
            return x
    
        def getFixBytes(self, lengthBytes):
            bytes = self.bytes[self.index : self.index+lengthBytes]
            self.index += lengthBytes
            return bytes
    
        def getVarBytes(self, lengthLength):
            lengthBytes = self.get(lengthLength)
            return self.getFixBytes(lengthBytes)
    
        def getFixList(self, length, lengthList):
            l = [0] * lengthList
            for x in range(lengthList):
                l[x] = self.get(length)
            return l
    
        def getVarList(self, length, lengthLength):
            lengthList = self.get(lengthLength)
            if lengthList % length != 0:
                raise ASN1Error("Error decoding ASN.1")
            lengthList = int(lengthList/length)
            l = [0] * lengthList
            for x in range(lengthList):
                l[x] = self.get(length)
            return l
    
        def startLengthCheck(self, lengthLength):
            self.lengthCheck = self.get(lengthLength)
            self.indexCheck = self.index
    
        def setLengthCheck(self, length):
            self.lengthCheck = length
            self.indexCheck = self.index
    
        def stopLengthCheck(self):
            if (self.index - self.indexCheck) != self.lengthCheck:
                raise ASN1Error("Error decoding ASN.1")
    
        def atLengthCheck(self):
            if (self.index - self.indexCheck) < self.lengthCheck:
                return False
            elif (self.index - self.indexCheck) == self.lengthCheck:
                return True
            else:
                raise ASN1Error("Error decoding ASN.1")

    def __init__(self, bytes):
        p = self.Parser(bytes)
        p.get(1)
        self.length = self._getASN1Length(p)
        self.value = p.getFixBytes(self.length)

    def getChild(self, which):
        p = self.Parser(self.value)
        for x in range(which+1):
            markIndex = p.index
            p.get(1)
            length = self._getASN1Length(p)
            p.getFixBytes(length)
        return ASN1Parser(p.bytes[markIndex:p.index])

    def _getASN1Length(self, p):
        firstLength = p.get(1)
        if firstLength<=127:
            return firstLength
        else:
            lengthLength = firstLength & 0x7F
            return p.get(lengthLength)

###
### PDF parsing routines from pdfminer, with changes for EBX_HANDLER

##  Utilities
##
def choplist(n, seq):
    '''Groups every n elements of the list.'''
    r = []
    for x in seq:
        r.append(x)
        if len(r) == n:
            yield tuple(r)
            r = []
    return

def nunpack(s, default=0):
    '''Unpacks up to 4 bytes big endian.'''
    l = len(s)
    if not l:
        return default
    elif l == 1:
        return ord(s)
    elif l == 2:
        return struct.unpack('>H', s)[0]
    elif l == 3:
        return struct.unpack('>L', '\x00'+s)[0]
    elif l == 4:
        return struct.unpack('>L', s)[0]
    else:
        return TypeError('invalid length: %d' % l)


STRICT = 1


##  PS Exceptions
##
class PSException(Exception): pass
class PSEOF(PSException): pass
class PSSyntaxError(PSException): pass
class PSTypeError(PSException): pass
class PSValueError(PSException): pass


##  Basic PostScript Types
##

# PSLiteral
class PSObject(object): pass

class PSLiteral(PSObject):
    '''
    PS literals (e.g. "/Name").
    Caution: Never create these objects directly.
    Use PSLiteralTable.intern() instead.
    '''
    def __init__(self, name):
        self.name = name
        return
    
    def __repr__(self):
        name = []
        for char in self.name:
            if not char.isalnum():
                char = '#%02x' % ord(char)
            name.append(char)
        return '/%s' % ''.join(name)

# PSKeyword
class PSKeyword(PSObject):
    '''
    PS keywords (e.g. "showpage").
    Caution: Never create these objects directly.
    Use PSKeywordTable.intern() instead.
    '''
    def __init__(self, name):
        self.name = name
        return
    
    def __repr__(self):
        return self.name

# PSSymbolTable
class PSSymbolTable(object):
    
    '''
    Symbol table that stores PSLiteral or PSKeyword.
    '''
    
    def __init__(self, classe):
        self.dic = {}
        self.classe = classe
        return
    
    def intern(self, name):
        if name in self.dic:
            lit = self.dic[name]
        else:
            lit = self.classe(name)
            self.dic[name] = lit
        return lit

PSLiteralTable = PSSymbolTable(PSLiteral)
PSKeywordTable = PSSymbolTable(PSKeyword)
LIT = PSLiteralTable.intern
KWD = PSKeywordTable.intern
KEYWORD_BRACE_BEGIN = KWD('{')
KEYWORD_BRACE_END = KWD('}')
KEYWORD_ARRAY_BEGIN = KWD('[')
KEYWORD_ARRAY_END = KWD(']')
KEYWORD_DICT_BEGIN = KWD('<<')
KEYWORD_DICT_END = KWD('>>')


def literal_name(x):
    if not isinstance(x, PSLiteral):
        if STRICT:
            raise PSTypeError('Literal required: %r' % x)
        else:
            return str(x)
    return x.name

def keyword_name(x):
    if not isinstance(x, PSKeyword):
        if STRICT:
            raise PSTypeError('Keyword required: %r' % x)
        else:
            return str(x)
    return x.name


##  PSBaseParser
##
EOL = re.compile(r'[\r\n]')
SPC = re.compile(r'\s')
NONSPC = re.compile(r'\S')
HEX = re.compile(r'[0-9a-fA-F]')
END_LITERAL = re.compile(r'[#/%\[\]()<>{}\s]')
END_HEX_STRING = re.compile(r'[^\s0-9a-fA-F]')
HEX_PAIR = re.compile(r'[0-9a-fA-F]{2}|.')
END_NUMBER = re.compile(r'[^0-9]')
END_KEYWORD = re.compile(r'[#/%\[\]()<>{}\s]')
END_STRING = re.compile(r'[()\134]')
OCT_STRING = re.compile(r'[0-7]')
ESC_STRING = { 'b':8, 't':9, 'n':10, 'f':12, 'r':13, '(':40, ')':41, '\\':92 }
class PSBaseParser(object):

    '''
    Most basic PostScript parser that performs only basic tokenization.
    '''
    BUFSIZ = 4096

    def __init__(self, fp):
        self.fp = fp
        self.seek(0)
        return

    def __repr__(self):
        return '<PSBaseParser: %r, bufpos=%d>' % (self.fp, self.bufpos)

    def flush(self):
        return
    
    def close(self):
        self.flush()
        return
    
    def tell(self):
        return self.bufpos+self.charpos

    def poll(self, pos=None, n=80):
        pos0 = self.fp.tell()
        if not pos:
            pos = self.bufpos+self.charpos
        self.fp.seek(pos)
        print >>sys.stderr, 'poll(%d): %r' % (pos, self.fp.read(n))
        self.fp.seek(pos0)
        return

    def seek(self, pos):
        '''
        Seeks the parser to the given position.
        '''
        self.fp.seek(pos)
        # reset the status for nextline()
        self.bufpos = pos
        self.buf = ''
        self.charpos = 0
        # reset the status for nexttoken()
        self.parse1 = self.parse_main
        self.tokens = []
        return

    def fillbuf(self):
        if self.charpos < len(self.buf): return
        # fetch next chunk.
        self.bufpos = self.fp.tell()
        self.buf = self.fp.read(self.BUFSIZ)
        if not self.buf:
            raise PSEOF('Unexpected EOF')
        self.charpos = 0
        return
    
    def parse_main(self, s, i):
        m = NONSPC.search(s, i)
        if not m:
            return (self.parse_main, len(s))
        j = m.start(0)
        c = s[j]
        self.tokenstart = self.bufpos+j
        if c == '%':
            self.token = '%'
            return (self.parse_comment, j+1)
        if c == '/':
            self.token = ''
            return (self.parse_literal, j+1)
        if c in '-+' or c.isdigit():
            self.token = c
            return (self.parse_number, j+1)
        if c == '.':
            self.token = c
            return (self.parse_float, j+1)
        if c.isalpha():
            self.token = c
            return (self.parse_keyword, j+1)
        if c == '(':
            self.token = ''
            self.paren = 1
            return (self.parse_string, j+1)
        if c == '<':
            self.token = ''
            return (self.parse_wopen, j+1)
        if c == '>':
            self.token = ''
            return (self.parse_wclose, j+1)
        self.add_token(KWD(c))
        return (self.parse_main, j+1)
                            
    def add_token(self, obj):
        self.tokens.append((self.tokenstart, obj))
        return
    
    def parse_comment(self, s, i):
        m = EOL.search(s, i)
        if not m:
            self.token += s[i:]
            return (self.parse_comment, len(s))
        j = m.start(0)
        self.token += s[i:j]
        # We ignore comments.
        #self.tokens.append(self.token)
        return (self.parse_main, j)
    
    def parse_literal(self, s, i):
        m = END_LITERAL.search(s, i)
        if not m:
            self.token += s[i:]
            return (self.parse_literal, len(s))
        j = m.start(0)
        self.token += s[i:j]
        c = s[j]
        if c == '#':
            self.hex = ''
            return (self.parse_literal_hex, j+1)
        self.add_token(LIT(self.token))
        return (self.parse_main, j)
    
    def parse_literal_hex(self, s, i):
        c = s[i]
        if HEX.match(c) and len(self.hex) < 2:
            self.hex += c
            return (self.parse_literal_hex, i+1)
        if self.hex:
            self.token += chr(int(self.hex, 16))
        return (self.parse_literal, i)

    def parse_number(self, s, i):
        m = END_NUMBER.search(s, i)
        if not m:
            self.token += s[i:]
            return (self.parse_number, len(s))
        j = m.start(0)
        self.token += s[i:j]
        c = s[j]
        if c == '.':
            self.token += c
            return (self.parse_float, j+1)
        try:
            self.add_token(int(self.token))
        except ValueError:
            pass
        return (self.parse_main, j)
    def parse_float(self, s, i):
        m = END_NUMBER.search(s, i)
        if not m:
            self.token += s[i:]
            return (self.parse_float, len(s))
        j = m.start(0)
        self.token += s[i:j]
        self.add_token(float(self.token))
        return (self.parse_main, j)
    
    def parse_keyword(self, s, i):
        m = END_KEYWORD.search(s, i)
        if not m:
            self.token += s[i:]
            return (self.parse_keyword, len(s))
        j = m.start(0)
        self.token += s[i:j]
        if self.token == 'true':
            token = True
        elif self.token == 'false':
            token = False
        else:
            token = KWD(self.token)
        self.add_token(token)
        return (self.parse_main, j)

    def parse_string(self, s, i):
        m = END_STRING.search(s, i)
        if not m:
            self.token += s[i:]
            return (self.parse_string, len(s))
        j = m.start(0)
        self.token += s[i:j]
        c = s[j]
        if c == '\\':
            self.oct = ''
            return (self.parse_string_1, j+1)
        if c == '(':
            self.paren += 1
            self.token += c
            return (self.parse_string, j+1)
        if c == ')':
            self.paren -= 1
            if self.paren:
                self.token += c
                return (self.parse_string, j+1)
        self.add_token(self.token)
        return (self.parse_main, j+1)
    def parse_string_1(self, s, i):
        c = s[i]
        if OCT_STRING.match(c) and len(self.oct) < 3:
            self.oct += c
            return (self.parse_string_1, i+1)
        if self.oct:
            self.token += chr(int(self.oct, 8))
            return (self.parse_string, i)
        if c in ESC_STRING:
            self.token += chr(ESC_STRING[c])
        return (self.parse_string, i+1)

    def parse_wopen(self, s, i):
        c = s[i]
        if c.isspace() or HEX.match(c):
            return (self.parse_hexstring, i)
        if c == '<':
            self.add_token(KEYWORD_DICT_BEGIN)
            i += 1
        return (self.parse_main, i)

    def parse_wclose(self, s, i):
        c = s[i]
        if c == '>':
            self.add_token(KEYWORD_DICT_END)
            i += 1
        return (self.parse_main, i)

    def parse_hexstring(self, s, i):
        m = END_HEX_STRING.search(s, i)
        if not m:
            self.token += s[i:]
            return (self.parse_hexstring, len(s))
        j = m.start(0)
        self.token += s[i:j]
        token = HEX_PAIR.sub(lambda m: chr(int(m.group(0), 16)),
                                                 SPC.sub('', self.token))
        self.add_token(token)
        return (self.parse_main, j)

    def nexttoken(self):
        while not self.tokens:
            self.fillbuf()
            (self.parse1, self.charpos) = self.parse1(self.buf, self.charpos)
        token = self.tokens.pop(0)
        return token

    def nextline(self):
        '''
        Fetches a next line that ends either with \\r or \\n.
        '''
        linebuf = ''
        linepos = self.bufpos + self.charpos
        eol = False
        while 1:
            self.fillbuf()
            if eol:
                c = self.buf[self.charpos]
                # handle '\r\n'
                if c == '\n':
                    linebuf += c
                    self.charpos += 1
                break
            m = EOL.search(self.buf, self.charpos)
            if m:
                linebuf += self.buf[self.charpos:m.end(0)]
                self.charpos = m.end(0)
                if linebuf[-1] == '\r':
                    eol = True
                else:
                    break
            else:
                linebuf += self.buf[self.charpos:]
                self.charpos = len(self.buf)
        return (linepos, linebuf)

    def revreadlines(self):
        '''
        Fetches a next line backword. This is used to locate
        the trailers at the end of a file.
        '''
        self.fp.seek(0, 2)
        pos = self.fp.tell()
        buf = ''
        while 0 < pos:
            pos = max(0, pos-self.BUFSIZ)
            self.fp.seek(pos)
            s = self.fp.read(self.BUFSIZ)
            if not s: break
            while 1:
                n = max(s.rfind('\r'), s.rfind('\n'))
                if n == -1:
                    buf = s + buf
                    break
                yield buf+s[n:]
                s = s[:n]
                buf = ''
        return


##  PSStackParser
##
class PSStackParser(PSBaseParser):

    def __init__(self, fp):
        PSBaseParser.__init__(self, fp)
        self.reset()
        return
    
    def reset(self):
        self.context = []
        self.curtype = None
        self.curstack = []
        self.results = []
        return

    def seek(self, pos):
        PSBaseParser.seek(self, pos)
        self.reset()
        return

    def push(self, *objs):
        self.curstack.extend(objs)
        return
    def pop(self, n):
        objs = self.curstack[-n:]
        self.curstack[-n:] = []
        return objs
    def popall(self):
        objs = self.curstack
        self.curstack = []
        return objs
    def add_results(self, *objs):
        self.results.extend(objs)
        return

    def start_type(self, pos, type):
        self.context.append((pos, self.curtype, self.curstack))
        (self.curtype, self.curstack) = (type, [])
        return
    def end_type(self, type):
        if self.curtype != type:
            raise PSTypeError('Type mismatch: %r != %r' % (self.curtype, type))
        objs = [ obj for (_,obj) in self.curstack ]
        (pos, self.curtype, self.curstack) = self.context.pop()
        return (pos, objs)

    def do_keyword(self, pos, token):
        return
    
    def nextobject(self):
        '''
        Yields a list of objects: keywords, literals, strings, 
        numbers, arrays and dictionaries. Arrays and dictionaries
        are represented as Python sequence and dictionaries.
        '''
        while not self.results:
            (pos, token) = self.nexttoken()
            #print (pos,token), (self.curtype, self.curstack)
            if (isinstance(token, int) or
                    isinstance(token, float) or
                    isinstance(token, bool) or
                    isinstance(token, str) or
                    isinstance(token, PSLiteral)):
                # normal token
                self.push((pos, token))
            elif token == KEYWORD_ARRAY_BEGIN:
                # begin array
                self.start_type(pos, 'a')
            elif token == KEYWORD_ARRAY_END:
                # end array
                try:
                    self.push(self.end_type('a'))
                except PSTypeError:
                    if STRICT: raise
            elif token == KEYWORD_DICT_BEGIN:
                # begin dictionary
                self.start_type(pos, 'd')
            elif token == KEYWORD_DICT_END:
                # end dictionary
                try:
                    (pos, objs) = self.end_type('d')
                    if len(objs) % 2 != 0:
                        raise PSSyntaxError(
                            'Invalid dictionary construct: %r' % objs)
                    d = dict((literal_name(k), v) \
                                 for (k,v) in choplist(2, objs))
                    self.push((pos, d))
                except PSTypeError:
                    if STRICT: raise
            else:
                self.do_keyword(pos, token)
            if self.context:
                continue
            else:
                self.flush()
        obj = self.results.pop(0)
        return obj


LITERAL_CRYPT = PSLiteralTable.intern('Crypt')
LITERALS_FLATE_DECODE = (PSLiteralTable.intern('FlateDecode'), PSLiteralTable.intern('Fl'))
LITERALS_LZW_DECODE = (PSLiteralTable.intern('LZWDecode'), PSLiteralTable.intern('LZW'))
LITERALS_ASCII85_DECODE = (PSLiteralTable.intern('ASCII85Decode'), PSLiteralTable.intern('A85'))


##  PDF Objects
##
class PDFObject(PSObject): pass

class PDFException(PSException): pass
class PDFTypeError(PDFException): pass
class PDFValueError(PDFException): pass
class PDFNotImplementedError(PSException): pass


##  PDFObjRef
##
class PDFObjRef(PDFObject):
    
    def __init__(self, doc, objid, _):
        if objid == 0:
            if STRICT:
                raise PDFValueError('PDF object id cannot be 0.')
        self.doc = doc
        self.objid = objid
        #self.genno = genno  # Never used.
        return

    def __repr__(self):
        return '<PDFObjRef:%d>' % (self.objid)

    def resolve(self):
        return self.doc.getobj(self.objid)


# resolve
def resolve1(x):
    '''
    Resolve an object. If this is an array or dictionary,
    it may still contains some indirect objects inside.
    '''
    while isinstance(x, PDFObjRef):
        x = x.resolve()
    return x

def resolve_all(x):
    '''
    Recursively resolve X and all the internals.
    Make sure there is no indirect reference within the nested object.
    This procedure might be slow.
    '''
    while isinstance(x, PDFObjRef):
        x = x.resolve()
    if isinstance(x, list):
        x = [ resolve_all(v) for v in x ]
    elif isinstance(x, dict):
        for (k,v) in x.iteritems():
            x[k] = resolve_all(v)
    return x

def decipher_all(decipher, objid, genno, x):
    '''
    Recursively decipher X.
    '''
    if isinstance(x, str):
        return decipher(objid, genno, x)
    decf = lambda v: decipher_all(decipher, objid, genno, v)
    if isinstance(x, list):
        x = [decf(v) for v in x]
    elif isinstance(x, dict):
        x = dict((k, decf(v)) for (k, v) in x.iteritems())
    return x

# Type cheking
def int_value(x):
    x = resolve1(x)
    if not isinstance(x, int):
        if STRICT:
            raise PDFTypeError('Integer required: %r' % x)
        return 0
    return x

def float_value(x):
    x = resolve1(x)
    if not isinstance(x, float):
        if STRICT:
            raise PDFTypeError('Float required: %r' % x)
        return 0.0
    return x

def num_value(x):
    x = resolve1(x)
    if not (isinstance(x, int) or isinstance(x, float)):
        if STRICT:
            raise PDFTypeError('Int or Float required: %r' % x)
        return 0
    return x

def str_value(x):
    x = resolve1(x)
    if not isinstance(x, str):
        if STRICT:
            raise PDFTypeError('String required: %r' % x)
        return ''
    return x

def list_value(x):
    x = resolve1(x)
    if not (isinstance(x, list) or isinstance(x, tuple)):
        if STRICT:
            raise PDFTypeError('List required: %r' % x)
        return []
    return x

def dict_value(x):
    x = resolve1(x)
    if not isinstance(x, dict):
        if STRICT:
            raise PDFTypeError('Dict required: %r' % x)
        return {}
    return x

def stream_value(x):
    x = resolve1(x)
    if not isinstance(x, PDFStream):
        if STRICT:
            raise PDFTypeError('PDFStream required: %r' % x)
        return PDFStream({}, '')
    return x

# ascii85decode(data)
def ascii85decode(data):
  n = b = 0
  out = ''
  for c in data:
    if '!' <= c and c <= 'u':
      n += 1
      b = b*85+(ord(c)-33)
      if n == 5:
        out += struct.pack('>L',b)
        n = b = 0
    elif c == 'z':
      assert n == 0
      out += '\0\0\0\0'
    elif c == '~':
      if n:
        for _ in range(5-n):
          b = b*85+84
        out += struct.pack('>L',b)[:n-1]
      break
  return out


##  PDFStream type
##
class PDFStream(PDFObject):
    
    def __init__(self, dic, rawdata, decipher=None):
        length = int_value(dic.get('Length', 0))
        eol = rawdata[length:]
        if eol in ('\r', '\n', '\r\n'):
            rawdata = rawdata[:length]
        if length != len(rawdata):
            print >>sys.stderr, "[warning] data length mismatch"
        self.dic = dic
        self.rawdata = rawdata
        self.decipher = decipher
        self.data = None
        self.objid = None
        self.genno = None
        return

    def set_objid(self, objid, genno):
        self.objid = objid
        self.genno = genno
        return
    
    def __repr__(self):
        return '<PDFStream(%r): raw=%d, %r>' % \
            (self.objid, len(self.rawdata), self.dic)

    def decode(self):
        assert self.data == None and self.rawdata != None
        data = self.rawdata
        if self.decipher:
            # Handle encryption
            data = self.decipher(self.objid, self.genno, data)
        if 'Filter' not in self.dic:
            self.data = data
            self.rawdata = None
            return
        filters = self.dic['Filter']
        if not isinstance(filters, list):
            filters = [ filters ]
        for f in filters:
            if f in LITERALS_FLATE_DECODE:
                # will get errors if the document is encrypted.
                data = zlib.decompress(data)
            elif f in LITERALS_LZW_DECODE:
                try:
                    from cStringIO import StringIO
                except ImportError:
                    from StringIO import StringIO
                data = ''.join(LZWDecoder(StringIO(data)).run())
            elif f in LITERALS_ASCII85_DECODE:
                data = ascii85decode(data)
            elif f == LITERAL_CRYPT:
                raise PDFNotImplementedError('/Crypt filter is unsupported')
            else:
                raise PDFNotImplementedError('Unsupported filter: %r' % f)
            # apply predictors
            if 'DP' in self.dic:
                params = self.dic['DP']
            else:
                params = self.dic.get('DecodeParms', {})
            if 'Predictor' in params:
                pred = int_value(params['Predictor'])
                if pred:
                    if pred != 12:
                        raise PDFNotImplementedError(
                            'Unsupported predictor: %r' % pred)
                    if 'Columns' not in params:
                        raise PDFValueError(
                            'Columns undefined for predictor=12')
                    columns = int_value(params['Columns'])
                    buf = ''
                    ent0 = '\x00' * columns
                    for i in xrange(0, len(data), columns+1):
                        pred = data[i]
                        ent1 = data[i+1:i+1+columns]
                        if pred == '\x02':
                            ent1 = ''.join(chr((ord(a)+ord(b)) & 255) \
                                               for (a,b) in zip(ent0,ent1))
                        buf += ent1
                        ent0 = ent1
                    data = buf
        self.data = data
        self.rawdata = None
        return

    def get_data(self):
        if self.data == None:
            self.decode()
        return self.data

    def get_rawdata(self):
        return self.rawdata

    def get_decdata(self):
        data = self.rawdata
        if self.decipher and data:
            # Handle encryption
            data = self.decipher(self.objid, self.genno, data)
        return data

        
##  PDF Exceptions
##
class PDFSyntaxError(PDFException): pass
class PDFNoValidXRef(PDFSyntaxError): pass
class PDFEncryptionError(PDFException): pass
class PDFPasswordIncorrect(PDFEncryptionError): pass

# some predefined literals and keywords.
LITERAL_OBJSTM = PSLiteralTable.intern('ObjStm')
LITERAL_XREF = PSLiteralTable.intern('XRef')
LITERAL_PAGE = PSLiteralTable.intern('Page')
LITERAL_PAGES = PSLiteralTable.intern('Pages')
LITERAL_CATALOG = PSLiteralTable.intern('Catalog')


##  XRefs
##

##  PDFXRef
##
class PDFXRef(object):

    def __init__(self):
        self.offsets = None
        return

    def __repr__(self):
        return '<PDFXRef: objs=%d>' % len(self.offsets)

    def objids(self):
        return self.offsets.iterkeys()

    def load(self, parser):
        self.offsets = {}
        while 1:
            try:
                (pos, line) = parser.nextline()
            except PSEOF:
                raise PDFNoValidXRef('Unexpected EOF - file corrupted?')
            if not line:
                raise PDFNoValidXRef('Premature eof: %r' % parser)
            if line.startswith('trailer'):
                parser.seek(pos)
                break
            f = line.strip().split(' ')
            if len(f) != 2:
                raise PDFNoValidXRef('Trailer not found: %r: line=%r' % (parser, line))
            try:
                (start, nobjs) = map(long, f)
            except ValueError:
                raise PDFNoValidXRef('Invalid line: %r: line=%r' % (parser, line))
            for objid in xrange(start, start+nobjs):
                try:
                    (_, line) = parser.nextline()
                except PSEOF:
                    raise PDFNoValidXRef('Unexpected EOF - file corrupted?')
                f = line.strip().split(' ')
                if len(f) != 3:
                    raise PDFNoValidXRef('Invalid XRef format: %r, line=%r' % (parser, line))
                (pos, genno, use) = f
                if use != 'n': continue
                self.offsets[objid] = (int(genno), long(pos))
        self.load_trailer(parser)
        return
    
    KEYWORD_TRAILER = PSKeywordTable.intern('trailer')
    def load_trailer(self, parser):
        try:
            (_,kwd) = parser.nexttoken()
            assert kwd is self.KEYWORD_TRAILER
            (_,dic) = parser.nextobject()
        except PSEOF:
            x = parser.pop(1)
            if not x:
                raise PDFNoValidXRef('Unexpected EOF - file corrupted')
            (_,dic) = x[0]
        self.trailer = dict_value(dic)
        return

    def getpos(self, objid):
        try:
            (genno, pos) = self.offsets[objid]
        except KeyError:
            raise
        return (None, pos)


##  PDFXRefStream
##
class PDFXRefStream(object):

    def __init__(self):
        self.index = None
        self.data = None
        self.entlen = None
        self.fl1 = self.fl2 = self.fl3 = None
        return

    def __repr__(self):
        return '<PDFXRef: objid=%d-%d>' % (self.objid_first, self.objid_last)

    def objids(self):
        for first, size in self.index:
            for objid in xrange(first, first + size):
                yield objid
    
    def load(self, parser, debug=0):
        (_,objid) = parser.nexttoken() # ignored
        (_,genno) = parser.nexttoken() # ignored
        (_,kwd) = parser.nexttoken()
        (_,stream) = parser.nextobject()
        if not isinstance(stream, PDFStream) or \
           stream.dic['Type'] is not LITERAL_XREF:
            raise PDFNoValidXRef('Invalid PDF stream spec.')
        size = stream.dic['Size']
        index = stream.dic.get('Index', (0,size))
        self.index = zip(islice(index, 0, None, 2),
                         islice(index, 1, None, 2))
        (self.fl1, self.fl2, self.fl3) = stream.dic['W']
        self.data = stream.get_data()
        self.entlen = self.fl1+self.fl2+self.fl3
        self.trailer = stream.dic
        return
    
    def getpos(self, objid):
        offset = 0
        for first, size in self.index:
            if first <= objid  and objid < (first + size):
                break
            offset += size
        else:
            raise KeyError(objid)
        i = self.entlen * ((objid - first) + offset)
        ent = self.data[i:i+self.entlen]
        f1 = nunpack(ent[:self.fl1], 1)
        if f1 == 1:
            pos = nunpack(ent[self.fl1:self.fl1+self.fl2])
            genno = nunpack(ent[self.fl1+self.fl2:])
            return (None, pos)
        elif f1 == 2:
            objid = nunpack(ent[self.fl1:self.fl1+self.fl2])
            index = nunpack(ent[self.fl1+self.fl2:])
            return (objid, index)
        # this is a free object
        raise KeyError(objid)


##  PDFDocument
##
##  A PDFDocument object represents a PDF document.
##  Since a PDF file is usually pretty big, normally it is not loaded
##  at once. Rather it is parsed dynamically as processing goes.
##  A PDF parser is associated with the document.
##
class PDFDocument(object):

    def __init__(self):
        self.xrefs = []
        self.objs = {}
        self.parsed_objs = {}
        self.root = None
        self.catalog = None
        self.parser = None
        self.encryption = None
        self.decipher = None
        self.ready = False
        return

    # set_parser(parser)
    #   Associates the document with an (already initialized) parser object.
    def set_parser(self, parser):
        if self.parser: return
        self.parser = parser
        # The document is set to be temporarily ready during collecting
        # all the basic information about the document, e.g.
        # the header, the encryption information, and the access rights 
        # for the document.
        self.ready = True
        # Retrieve the information of each header that was appended
        # (maybe multiple times) at the end of the document.
        self.xrefs = parser.read_xref()
        for xref in self.xrefs:
            trailer = xref.trailer
            if not trailer: continue
            # If there's an encryption info, remember it.
            if 'Encrypt' in trailer:
                #assert not self.encryption
                self.encryption = (list_value(trailer['ID']),
                                   dict_value(trailer['Encrypt']))
            if 'Root' in trailer:
                self.set_root(dict_value(trailer['Root']))
                break
        else:
            raise PDFSyntaxError('No /Root object! - Is this really a PDF?')
        # The document is set to be non-ready again, until all the
        # proper initialization (asking the password key and
        # verifying the access permission, so on) is finished.
        self.ready = False
        return

    # set_root(root)
    #   Set the Root dictionary of the document.
    #   Each PDF file must have exactly one /Root dictionary.
    def set_root(self, root):
        self.root = root
        self.catalog = dict_value(self.root)
        if self.catalog.get('Type') is not LITERAL_CATALOG:
            if STRICT:
                raise PDFSyntaxError('Catalog not found!')
        return
    
    # initialize(password='')
    #   Perform the initialization with a given password.
    #   This step is mandatory even if there's no password associated
    #   with the document.
    def initialize(self, password=''):
        if not self.encryption:
            self.is_printable = self.is_modifiable = self.is_extractable = True
            self.ready = True
            return
        (docid, param) = self.encryption
        type = literal_name(param['Filter'])
        if type == 'Standard':
            return self.initialize_standard(password, docid, param)
        if type == 'EBX_HANDLER':
            return self.initialize_ebx(password, docid, param)
        raise PDFEncryptionError('Unknown filter: param=%r' % param)

    def initialize_ebx(self, password, docid, param):
        self.is_printable = self.is_modifiable = self.is_extractable = True
        with open(password, 'rb') as f:
            keyder = f.read()
        key = ASN1Parser([ord(x) for x in keyder])
        key = [bytesToNumber(key.getChild(x).value) for x in xrange(1, 4)]
        rsa = RSA.construct(key)
        length = int_value(param.get('Length', 0)) / 8
        rights = str_value(param.get('ADEPT_LICENSE')).decode('base64')
        rights = zlib.decompress(rights, -15)
        rights = etree.fromstring(rights)
        expr = './/{http://ns.adobe.com/adept}encryptedKey'
        bookkey = ''.join(rights.findtext(expr)).decode('base64')
        bookkey = rsa.decrypt(bookkey)
        if bookkey[0] != '\x02':
            raise ADEPTError('error decrypting book session key')
        index = bookkey.index('\0') + 1
        bookkey = bookkey[index:]
        ebx_V = int_value(param.get('V', 4))
        ebx_type = int_value(param.get('EBX_ENCRYPTIONTYPE', 6))
        # added because of the booktype / decryption book session key error
        if ebx_V == 3:
            V = 3        
        elif ebx_V < 4 or ebx_type < 6:
            V = ord(bookkey[0])
            bookkey = bookkey[1:]
        else:
            V = 2
        if length and len(bookkey) != length:
            raise ADEPTError('error decrypting book session key')
        self.decrypt_key = bookkey
        self.genkey = self.genkey_v3 if V == 3 else self.genkey_v2
        self.decipher = self.decrypt_rc4
        self.ready = True
        return

    
    PASSWORD_PADDING = '(\xbfN^Nu\x8aAd\x00NV\xff\xfa\x01\x08..' \
                       '\x00\xb6\xd0h>\x80/\x0c\xa9\xfedSiz'
    def initialize_standard(self, password, docid, param):
        V = int_value(param.get('V', 0))
        if not (V == 1 or V == 2):
            raise PDFEncryptionError('Unknown algorithm: param=%r' % param)
        length = int_value(param.get('Length', 40)) # Key length (bits)
        O = str_value(param['O'])
        R = int_value(param['R']) # Revision
        if 5 <= R:
            raise PDFEncryptionError('Unknown revision: %r' % R)
        U = str_value(param['U'])
        P = int_value(param['P'])
        self.is_printable = bool(P & 4)        
        self.is_modifiable = bool(P & 8)
        self.is_extractable = bool(P & 16)
        # Algorithm 3.2
        password = (password+self.PASSWORD_PADDING)[:32] # 1
        hash = hashlib.md5(password) # 2
        hash.update(O) # 3
        hash.update(struct.pack('<l', P)) # 4
        hash.update(docid[0]) # 5
        if 4 <= R:
            # 6
            raise PDFNotImplementedError(
                'Revision 4 encryption is currently unsupported')
        if 3 <= R:
            # 8
            for _ in xrange(50):
                hash = hashlib.md5(hash.digest()[:length/8])
        key = hash.digest()[:length/8]
        if R == 2:
            # Algorithm 3.4
            u1 = ARC4.new(key).decrypt(password)
        elif R == 3:
            # Algorithm 3.5
            hash = hashlib.md5(self.PASSWORD_PADDING) # 2
            hash.update(docid[0]) # 3
            x = ARC4.new(key).decrypt(hash.digest()[:16]) # 4
            for i in xrange(1,19+1):
                k = ''.join( chr(ord(c) ^ i) for c in key )
                x = ARC4.new(k).decrypt(x)
            u1 = x+x # 32bytes total
        if R == 2:
            is_authenticated = (u1 == U)
        else:
            is_authenticated = (u1[:16] == U[:16])
        if not is_authenticated:
            raise PDFPasswordIncorrect
        self.decrypt_key = key
        self.genkey = self.genkey_v2
        self.decipher = self.decipher_rc4  # XXX may be AES
        self.ready = True
        return

    def genkey_v2(self, objid, genno):
        objid = struct.pack('<L', objid)[:3]
        genno = struct.pack('<L', genno)[:2]
        key = self.decrypt_key + objid + genno
        hash = hashlib.md5(key)
        key = hash.digest()[:min(len(self.decrypt_key) + 5, 16)]
        return key
    
    def genkey_v3(self, objid, genno):
        objid = struct.pack('<L', objid ^ 0x3569ac)
        genno = struct.pack('<L', genno ^ 0xca96)
        key = self.decrypt_key
        key += objid[0] + genno[0] + objid[1] + genno[1] + objid[2] + 'sAlT'
        hash = hashlib.md5(key)
        key = hash.digest()[:min(len(self.decrypt_key) + 5, 16)]
        return key
    
    def decrypt_rc4(self, objid, genno, data):
        key = self.genkey(objid, genno)
        return ARC4.new(key).decrypt(data)
    
    KEYWORD_OBJ = PSKeywordTable.intern('obj')
    def getobj(self, objid):
        if not self.ready:
            raise PDFException('PDFDocument not initialized')
        #assert self.xrefs
        if objid in self.objs:
            genno = 0
            obj = self.objs[objid]
        else:
            for xref in self.xrefs:
                try:
                    (stmid, index) = xref.getpos(objid)
                    break
                except KeyError:
                    pass
            else:
                return
                #if STRICT:
                #    raise PDFSyntaxError('Cannot locate objid=%r' % objid)
                return None
            if stmid:
                return PDFObjStmRef(objid, stmid, index)
            else:
                self.parser.seek(index)
                (_,objid1) = self.parser.nexttoken() # objid
                (_,genno) = self.parser.nexttoken() # genno
                #assert objid1 == objid, (objid, objid1)
                (_,kwd) = self.parser.nexttoken()
                if kwd is not self.KEYWORD_OBJ:
                    raise PDFSyntaxError(
                        'Invalid object spec: offset=%r' % index)
                (_,obj) = self.parser.nextobject()
                if isinstance(obj, PDFStream):
                    obj.set_objid(objid, genno)
            self.objs[objid] = obj
        if self.decipher:
            obj = decipher_all(self.decipher, objid, genno, obj)
        return obj

class PDFObjStmRef(object):
    def __init__(self, objid, stmid, index):
        self.objid = objid
        self.stmid = stmid
        self.index = index

    
##  PDFParser
##
class PDFParser(PSStackParser):

    def __init__(self, doc, fp):
        PSStackParser.__init__(self, fp)
        self.doc = doc
        self.doc.set_parser(self)
        return

    def __repr__(self):
        return '<PDFParser>'

    KEYWORD_R = PSKeywordTable.intern('R')
    KEYWORD_ENDOBJ = PSKeywordTable.intern('endobj')
    KEYWORD_STREAM = PSKeywordTable.intern('stream')
    KEYWORD_XREF = PSKeywordTable.intern('xref')
    KEYWORD_STARTXREF = PSKeywordTable.intern('startxref')
    def do_keyword(self, pos, token):
        if token in (self.KEYWORD_XREF, self.KEYWORD_STARTXREF):
            self.add_results(*self.pop(1))
            return
        if token is self.KEYWORD_ENDOBJ:
            self.add_results(*self.pop(4))
            return
        
        if token is self.KEYWORD_R:
            # reference to indirect object
            try:
                ((_,objid), (_,genno)) = self.pop(2)
                (objid, genno) = (int(objid), int(genno))
                obj = PDFObjRef(self.doc, objid, genno)
                self.push((pos, obj))
            except PSSyntaxError:
                pass
            return
            
        if token is self.KEYWORD_STREAM:
            # stream object
            ((_,dic),) = self.pop(1)
            dic = dict_value(dic)
            try:
                objlen = int_value(dic['Length'])
            except KeyError:
                if STRICT:
                    raise PDFSyntaxError('/Length is undefined: %r' % dic)
                objlen = 0
            self.seek(pos)
            try:
                (_, line) = self.nextline()  # 'stream'
            except PSEOF:
                if STRICT:
                    raise PDFSyntaxError('Unexpected EOF')
                return
            pos += len(line)
            self.fp.seek(pos)
            data = self.fp.read(objlen)
            self.seek(pos+objlen)
            while 1:
                try:
                    (linepos, line) = self.nextline()
                except PSEOF:
                    if STRICT:
                        raise PDFSyntaxError('Unexpected EOF')
                    break
                if 'endstream' in line:
                    i = line.index('endstream')
                    objlen += i
                    data += line[:i]
                    break
                objlen += len(line)
                data += line
            self.seek(pos+objlen)
            obj = PDFStream(dic, data, self.doc.decipher)
            self.push((pos, obj))
            return
        
        # others
        self.push((pos, token))
        return

    def find_xref(self):
        # search the last xref table by scanning the file backwards.
        prev = None
        for line in self.revreadlines():
            line = line.strip()
            if line == 'startxref': break
            if line:
                prev = line
        else:
            raise PDFNoValidXRef('Unexpected EOF')
        return long(prev)

    # read xref table
    def read_xref_from(self, start, xrefs):
        self.seek(start)
        self.reset()
        try:
            (pos, token) = self.nexttoken()
        except PSEOF:
            raise PDFNoValidXRef('Unexpected EOF')
        if isinstance(token, int):
            # XRefStream: PDF-1.5
            self.seek(pos)
            self.reset()
            xref = PDFXRefStream()
            xref.load(self)
        else:
            if token is not self.KEYWORD_XREF:
                raise PDFNoValidXRef('xref not found: pos=%d, token=%r' % 
                                     (pos, token))
            self.nextline()
            xref = PDFXRef()
            xref.load(self)
        xrefs.append(xref)
        trailer = xref.trailer
        if 'XRefStm' in trailer:
            pos = int_value(trailer['XRefStm'])
            self.read_xref_from(pos, xrefs)
        if 'Prev' in trailer:
            # find previous xref
            pos = int_value(trailer['Prev'])
            self.read_xref_from(pos, xrefs)
        return
        
    # read xref tables and trailers
    def read_xref(self):
        xrefs = []
        try:
            pos = self.find_xref()
            self.read_xref_from(pos, xrefs)
        except PDFNoValidXRef:
            # fallback
            self.seek(0)
            pat = re.compile(r'^(\d+)\s+(\d+)\s+obj\b')
            offsets = {}
            xref = PDFXRef()
            while 1:
                try:
                    (pos, line) = self.nextline()
                except PSEOF:
                    break
                if line.startswith('trailer'): break
                m = pat.match(line)
                if not m: continue
                (objid, genno) = m.groups()
                offsets[int(objid)] = (0, pos)
            if not offsets: raise
            xref.offsets = offsets
            self.seek(pos)
            xref.load_trailer(self)
            xrefs.append(xref)
        return xrefs


###
### My own code, for which there is none else to blame

class PDFSerializer(object):
    def __init__(self, inf, keypath):
        self.version = inf.read(8)
        inf.seek(0)
        self.doc = doc = PDFDocument()
        parser = PDFParser(doc, inf)
        doc.initialize(keypath)
        self.objids = objids = set()
        for xref in reversed(doc.xrefs):
            trailer = xref.trailer
            for objid in xref.objids():
                objids.add(objid)
        trailer = dict(trailer)
        trailer.pop('Prev', None)
        trailer.pop('XRefStm', None)
        if 'Encrypt' in trailer:
            objids.remove(trailer.pop('Encrypt').objid)
        self.trailer = trailer

    def dump(self, outf):
        self.outf = outf
        self.write(self.version)
        self.write('\n%\xe2\xe3\xcf\xd3\n')
        doc = self.doc
        objids = self.objids
        xrefs = {}
        xrefstm = {}
        maxobj = max(objids)
        trailer = dict(self.trailer)
        trailer['Size'] = maxobj + 1
        for objid in objids:
            obj = doc.getobj(objid)
            if isinstance(obj, PDFObjStmRef):
                xrefstm[objid] = obj
                continue
            xrefs[objid] = self.tell()
            self.serialize_indirect(objid, obj)
        startxref = self.tell()
        self.write('xref\n')
        self.write('0 %d\n' % (maxobj + 1,))
        for objid in xrange(0, maxobj + 1):
            if objid in xrefs:
                self.write("%010d %05d n \n" % (xrefs[objid], 0))
            else:
                self.write("%010d %05d f \n" % (0, 65535))
        self.write('trailer\n')
        self.serialize_object(trailer)
        self.write('\nstartxref\n%d\n%%%%EOF' % startxref)
        if not xrefstm:
            return
        index = []
        first = None
        prev = None
        data = []
        for objid in sorted(xrefstm):
            if first is None:
                first = objid
            elif objid != prev + 1:
                index.extend((first, prev - first + 1))
                first = objid
            prev = objid
            stmid = xrefstm[objid].stmid
            data.append(struct.pack('>BHB', 2, stmid, 0))
        index.extend((first, prev - first + 1))
        data = zlib.compress(''.join(data))
        dic = {'Type': LITERAL_XREF, 'Size': prev + 1, 'Index': index,
               'W': [1, 2, 1], 'Length': len(data), 'Prev': startxref,
               'Filter': LITERALS_FLATE_DECODE[0],}
        obj = PDFStream(dic, data)
        self.write('\n')
        trailer['XRefStm'] = startxrefstm = self.tell()
        self.serialize_indirect(maxobj + 1, obj)
        trailer['Prev'] = startxref
        startxref = self.tell()
        self.write('xref\n')
        self.write('%d 1\n' % (maxobj + 1,))
        self.write("%010d %05d n \n" % (startxrefstm, 0))
        self.write('trailer\n')
        self.serialize_object(trailer)
        self.write('\nstartxref\n%d\n%%%%EOF' % startxref)
    
    def write(self, data):
        self.outf.write(data)
        self.last = data[-1:]

    def tell(self):
        return self.outf.tell()

    def escape_string(self, string):
        string = string.replace('\\', '\\\\')
        string = string.replace('\n', r'\n')
        string = string.replace('(', r'\(')
        string = string.replace(')', r'\)')
         # get rid of ciando id
        regularexp = re.compile(r'http://www.ciando.com/index.cfm/intRefererID/\d{5}')
        if regularexp.match(string): return ('http://www.ciando.com') 
        return string
    
    def serialize_object(self, obj):
        if isinstance(obj, dict):
            self.write('<<')
            for key, val in obj.items():
                self.write('/%s' % key)
                self.serialize_object(val)
            self.write('>>')
        elif isinstance(obj, list):
            self.write('[')
            for val in obj:
                self.serialize_object(val)
            self.write(']')
        elif isinstance(obj, str):
            self.write('(%s)' % self.escape_string(obj))
        elif isinstance(obj, bool):
            if self.last.isalnum():
                self.write(' ')
            self.write(str(obj).lower())            
        elif isinstance(obj, (int, long, float)):
            if self.last.isalnum():
                self.write(' ')
            self.write(str(obj))
        elif isinstance(obj, PDFObjRef):
            if self.last.isalnum():
                self.write(' ')            
            self.write('%d %d R' % (obj.objid, 0))
        elif isinstance(obj, PDFStream):
            data = obj.get_decdata()
            self.serialize_object(obj.dic)
            self.write('stream\n')
            self.write(data)
            self.write('\nendstream')
        else:
            data = str(obj)
            if data[0].isalnum() and self.last.isalnum():
                self.write(' ')
            self.write(data)
    
    def serialize_indirect(self, objid, obj):
        self.write('%d 0 obj' % (objid,))
        self.serialize_object(obj)
        if self.last.isalnum():
            self.write('\n')
        self.write('endobj\n')

def cli_main(argv=sys.argv):
    progname = os.path.basename(argv[0])
    if RSA is None:
        print "%s: This script requires PyCrypto, which must be installed " \
              "separately.  Read the top-of-script comment for details." % \
              (progname,)
        return 1
    if len(argv) != 4:
        print "usage: %s KEYFILE INBOOK OUTBOOK" % (progname,)
        return 1
    keypath, inpath, outpath = argv[1:]
    with open(inpath, 'rb') as inf:
        serializer = PDFSerializer(inf, keypath)
        with open(outpath, 'wb') as outf:
            serializer.dump(outf)
    return 0


class DecryptionDialog(Tkinter.Frame):
    def __init__(self, root):
        Tkinter.Frame.__init__(self, root, border=5)
        self.status = Tkinter.Label(self, text='Select files for decryption')
        self.status.pack(fill=Tkconstants.X, expand=1)
        body = Tkinter.Frame(self)
        body.pack(fill=Tkconstants.X, expand=1)
        sticky = Tkconstants.E + Tkconstants.W
        body.grid_columnconfigure(1, weight=2)
        Tkinter.Label(body, text='Key file').grid(row=0)
        self.keypath = Tkinter.Entry(body, width=30)
        self.keypath.grid(row=0, column=1, sticky=sticky)
        if os.path.exists('adeptkey.der'):
            self.keypath.insert(0, 'adeptkey.der')
        button = Tkinter.Button(body, text="...", command=self.get_keypath)
        button.grid(row=0, column=2)
        Tkinter.Label(body, text='Input file').grid(row=1)
        self.inpath = Tkinter.Entry(body, width=30)
        self.inpath.grid(row=1, column=1, sticky=sticky)
        button = Tkinter.Button(body, text="...", command=self.get_inpath)
        button.grid(row=1, column=2)
        Tkinter.Label(body, text='Output file').grid(row=2)
        self.outpath = Tkinter.Entry(body, width=30)
        self.outpath.grid(row=2, column=1, sticky=sticky)
        button = Tkinter.Button(body, text="...", command=self.get_outpath)
        button.grid(row=2, column=2)
        buttons = Tkinter.Frame(self)
        buttons.pack()
        botton = Tkinter.Button(
            buttons, text="Decrypt", width=10, command=self.decrypt)
        botton.pack(side=Tkconstants.LEFT)
        Tkinter.Frame(buttons, width=10).pack(side=Tkconstants.LEFT)
        button = Tkinter.Button(
            buttons, text="Quit", width=10, command=self.quit)
        button.pack(side=Tkconstants.RIGHT)

    def get_keypath(self):
        keypath = tkFileDialog.askopenfilename(
            parent=None, title='Select ADEPT key file',
            defaultextension='.der', filetypes=[('DER-encoded files', '.der'),
                                                ('All Files', '.*')])
        if keypath:
            keypath = os.path.normpath(keypath)
            self.keypath.delete(0, Tkconstants.END)
            self.keypath.insert(0, keypath)
        return

    def get_inpath(self):
        inpath = tkFileDialog.askopenfilename(
            parent=None, title='Select ADEPT-encrypted PDF file to decrypt',
            defaultextension='.epub', filetypes=[('PDF files', '.pdf'),
                                                 ('All files', '.*')])
        if inpath:
            inpath = os.path.normpath(inpath)
            self.inpath.delete(0, Tkconstants.END)
            self.inpath.insert(0, inpath)
        return

    def get_outpath(self):
        outpath = tkFileDialog.asksaveasfilename(
            parent=None, title='Select unencrypted PDF file to produce',
            defaultextension='.epub', filetypes=[('PDF files', '.pdf'),
                                                 ('All files', '.*')])
        if outpath:
            outpath = os.path.normpath(outpath)
            self.outpath.delete(0, Tkconstants.END)
            self.outpath.insert(0, outpath)
        return

    def decrypt(self):
        keypath = self.keypath.get()
        inpath = self.inpath.get()
        outpath = self.outpath.get()
        if not keypath or not os.path.exists(keypath):
            self.status['text'] = 'Specified key file does not exist'
            return
        if not inpath or not os.path.exists(inpath):
            self.status['text'] = 'Specified input file does not exist'
            return
        if not outpath:
            self.status['text'] = 'Output file not specified'
            return
        if inpath == outpath:
            self.status['text'] = 'Must have different input and output files'
            return
        argv = [sys.argv[0], keypath, inpath, outpath]
        self.status['text'] = 'Decrypting...'
        try:
            cli_main(argv)
        except Exception, e:
            self.status['text'] = 'Error: ' + str(e)
            return
        self.status['text'] = 'File successfully decrypted'

def gui_main():
    root = Tkinter.Tk()
    if RSA is None:
        root.withdraw()
        tkMessageBox.showerror(
            "INEPT PDF Decrypter",
            "This script requires PyCrypto, which must be installed "
            "separately.  Read the top-of-script comment for details.")
        return 1
    root.title('INEPT PDF Decrypter')
    root.resizable(True, False)
    root.minsize(300, 0)
    DecryptionDialog(root).pack(fill=Tkconstants.X, expand=1)
    root.mainloop()
    return 0


if __name__ == '__main__':
    if len(sys.argv) > 1:
        sys.exit(cli_main())
    sys.exit(gui_main())
