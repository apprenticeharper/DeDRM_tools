#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ineptpdf.py
# Copyright © 2009-2020 by i♥cabbages, Apprentice Harper et al.
# Copyright © 2021-2022 by noDRM et al.

# Released under the terms of the GNU General Public Licence, version 3
# <http://www.gnu.org/licenses/>


# Revision history:
#   1 - Initial release
#   2 - Improved determination of key-generation algorithm
#   3 - Correctly handle PDF >=1.5 cross-reference streams
#   4 - Removal of ciando's personal ID
#   5 - Automated decryption of a complete directory
#   6.1 - backward compatibility for 1.7.1 and old adeptkey.der
#   7 - Get cross reference streams and object streams working for input.
#       Not yet supported on output but this only effects file size,
#       not functionality. (anon2)
#   7.1 - Correct a problem when an old trailer is not followed by startxref
#   7.2 - Correct malformed Mac OS resource forks for Stanza (anon2)
#       - Support for cross ref streams on output (decreases file size)
#   7.3 - Correct bug in trailer with cross ref stream that caused the error
#         "The root object is missing or invalid" in Adobe Reader. (anon2)
#   7.4 - Force all generation numbers in output file to be 0, like in v6.
#         Fallback code for wrong xref improved (search till last trailer
#         instead of first) (anon2)
#   7.5 - allow support for OpenSSL to replace pycrypto on all platforms
#         implemented ARC4 interface to OpenSSL
#         fixed minor typos
#   7.6 - backported AES and other fixes from version 8.4.48
#   7.7 - On Windows try PyCrypto first and OpenSSL next
#   7.8 - Modify interface to allow use of import
#   7.9 - Bug fix for some session key errors when len(bookkey) > length required
#   7.10 - Various tweaks to fix minor problems.
#   7.11 - More tweaks to fix minor problems.
#   7.12 - Revised to allow use in calibre plugins to eliminate need for duplicate code
#   7.13 - Fixed erroneous mentions of ineptepub
#   7.14 - moved unicode_argv call inside main for Windows DeDRM compatibility
#   8.0  - Work if TkInter is missing
#   8.0.1 - Broken Metadata fix.
#   8.0.2 - Add additional check on DER file sanity
#   8.0.3 - Remove erroneous check on DER file sanity
#   8.0.4 - Completely remove erroneous check on DER file sanity
#   8.0.5 - Do not process DRM-free documents
#   8.0.6 - Replace use of float by Decimal for greater precision, and import tkFileDialog
#   9.0.0 - Add Python 3 compatibility for calibre 5
#   9.1.0 - Support for decrypting with owner password, support for V=5, R=5 and R=6 PDF files, support for AES256-encrypted PDFs.
#   9.1.1 - Only support PyCryptodome; clean up the code
#   10.0.0 - Add support for "hardened" Adobe DRM (RMSDK >= 10)
#   10.0.2 - Fix some Python2 stuff

"""
Decrypts Adobe ADEPT-encrypted PDF files.
"""

__license__ = 'GPL v3'
__version__ = "10.0.2"

import codecs
import hashlib
import sys
import os
import re
import zlib
import struct
import binascii
import base64
from io import BytesIO
from decimal import Decimal
import itertools
import xml.etree.ElementTree as etree
import traceback
from uuid import UUID

try:
    from Cryptodome.Cipher import AES, ARC4, PKCS1_v1_5
    from Cryptodome.PublicKey import RSA
except ImportError:
    from Crypto.Cipher import AES, ARC4, PKCS1_v1_5
    from Crypto.PublicKey import RSA


def unpad(data, padding=16):
    if sys.version_info[0] == 2:
        pad_len = ord(data[-1])
    else:
        pad_len = data[-1]

    return data[:-pad_len]


# Wrap a stream so that output gets flushed immediately
# and also make sure that any unicode strings get
# encoded using "replace" before writing them.
class SafeUnbuffered:
    def __init__(self, stream):
        self.stream = stream
        self.encoding = stream.encoding
        if self.encoding == None:
            self.encoding = "utf-8"
    def write(self, data):
        if isinstance(data,str) or isinstance(data,unicode):
            # str for Python3, unicode for Python2
            data = data.encode(self.encoding,"replace")
        try:
            buffer = getattr(self.stream, 'buffer', self.stream)
            # self.stream.buffer for Python3, self.stream for Python2
            buffer.write(data)
            buffer.flush()
        except:
            # We can do nothing if a write fails
            raise
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

iswindows = sys.platform.startswith('win')
isosx = sys.platform.startswith('darwin')

def unicode_argv():
    if iswindows:
        # Uses shell32.GetCommandLineArgvW to get sys.argv as a list of Unicode
        # strings.

        # Versions 2.x of Python don't support Unicode in sys.argv on
        # Windows, with the underlying Windows API instead replacing multi-byte
        # characters with '?'.


        from ctypes import POINTER, byref, cdll, c_int, windll
        from ctypes.wintypes import LPCWSTR, LPWSTR

        GetCommandLineW = cdll.kernel32.GetCommandLineW
        GetCommandLineW.argtypes = []
        GetCommandLineW.restype = LPCWSTR

        CommandLineToArgvW = windll.shell32.CommandLineToArgvW
        CommandLineToArgvW.argtypes = [LPCWSTR, POINTER(c_int)]
        CommandLineToArgvW.restype = POINTER(LPWSTR)

        cmd = GetCommandLineW()
        argc = c_int(0)
        argv = CommandLineToArgvW(cmd, byref(argc))
        if argc.value > 0:
            # Remove Python executable and commands if present
            start = argc.value - len(sys.argv)
            return [argv[i] for i in
                    range(start, argc.value)]
        return ["ineptpdf.py"]
    else:
        argvencoding = sys.stdin.encoding or "utf-8"
        return [arg if (isinstance(arg, str) or isinstance(arg,unicode)) else str(arg, argvencoding) for arg in sys.argv]


class ADEPTError(Exception):
    pass

class ADEPTInvalidPasswordError(Exception):
    pass

class ADEPTNewVersionError(Exception):
    pass

def SHA256(message):
    return hashlib.sha256(message).digest()

# Do we generate cross reference streams on output?
# 0 = never
# 1 = only if present in input
# 2 = always

GEN_XREF_STM = 0

# This is the value for the current document
gen_xref_stm = False # will be set in PDFSerializer

# PDF parsing routines from pdfminer, with changes for EBX_HANDLER

#  Utilities

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
        return struct.unpack('>L', bytes([0]) + s)[0]
    elif l == 4:
        return struct.unpack('>L', s)[0]
    else:
        return TypeError('invalid length: %d' % l)


STRICT = 0


#  PS Exceptions

class PSException(Exception): pass
class PSEOF(PSException): pass
class PSSyntaxError(PSException): pass
class PSTypeError(PSException): pass
class PSValueError(PSException): pass


#  Basic PostScript Types


# PSLiteral
class PSObject(object): pass

class PSLiteral(PSObject):
    '''
    PS literals (e.g. "/Name").
    Caution: Never create these objects directly.
    Use PSLiteralTable.intern() instead.
    '''
    def __init__(self, name):
        self.name = name.decode('utf-8')
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
        self.name = name.decode('utf-8')
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
KEYWORD_BRACE_BEGIN = KWD(b'{')
KEYWORD_BRACE_END = KWD(b'}')
KEYWORD_ARRAY_BEGIN = KWD(b'[')
KEYWORD_ARRAY_END = KWD(b']')
KEYWORD_DICT_BEGIN = KWD(b'<<')
KEYWORD_DICT_END = KWD(b'>>')


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
EOL = re.compile(br'[\r\n]')
SPC = re.compile(br'\s')
NONSPC = re.compile(br'\S')
HEX = re.compile(br'[0-9a-fA-F]')
END_LITERAL = re.compile(br'[#/%\[\]()<>{}\s]')
END_HEX_STRING = re.compile(br'[^\s0-9a-fA-F]')
HEX_PAIR = re.compile(br'[0-9a-fA-F]{2}|.')
END_NUMBER = re.compile(br'[^0-9]')
END_KEYWORD = re.compile(br'[#/%\[\]()<>{}\s]')
END_STRING = re.compile(br'[()\\]')
OCT_STRING = re.compile(br'[0-7]')
ESC_STRING = { b'b':8, b't':9, b'n':10, b'f':12, b'r':13, b'(':40, b')':41, b'\\':92 }

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
        self.fp.seek(pos0)
        return

    def seek(self, pos):
        '''
        Seeks the parser to the given position.
        '''
        self.fp.seek(pos)
        # reset the status for nextline()
        self.bufpos = pos
        self.buf = b''
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
        if isinstance(s[j], str):
            # Python 2
            c = s[j]
        else:
            # Python 3
            c = bytes([s[j]])
        self.tokenstart = self.bufpos+j
        if c == b'%':
            self.token = c
            return (self.parse_comment, j+1)
        if c == b'/':
            self.token = b''
            return (self.parse_literal, j+1)
        if c in b'-+' or c.isdigit():
            self.token = c
            return (self.parse_number, j+1)
        if c == b'.':
            self.token = c
            return (self.parse_decimal, j+1)
        if c.isalpha():
            self.token = c
            return (self.parse_keyword, j+1)
        if c == b'(':
            self.token = b''
            self.paren = 1
            return (self.parse_string, j+1)
        if c == b'<':
            self.token = b''
            return (self.parse_wopen, j+1)
        if c == b'>':
            self.token = b''
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
        if isinstance(s[j], str):
            c = s[j]
        else:
            c = bytes([s[j]])
        if c == b'#':
            self.hex = b''
            return (self.parse_literal_hex, j+1)
        self.add_token(LIT(self.token))
        return (self.parse_main, j)

    def parse_literal_hex(self, s, i):
        if isinstance(s[i], str):
            c = s[i]
        else:
            c = bytes([s[i]])
        if HEX.match(c) and len(self.hex) < 2:
            self.hex += c
            return (self.parse_literal_hex, i+1)
        if self.hex:
            self.token += bytes([int(self.hex, 16)])
        return (self.parse_literal, i)

    def parse_number(self, s, i):
        m = END_NUMBER.search(s, i)
        if not m:
            self.token += s[i:]
            return (self.parse_number, len(s))
        j = m.start(0)
        self.token += s[i:j]
        if isinstance(s[j], str):
            c = s[j]
        else:
            c = bytes([s[j]])
        if c == b'.':
            self.token += c
            return (self.parse_decimal, j+1)
        try:
            self.add_token(int(self.token))
        except ValueError:
            pass
        return (self.parse_main, j)

    def parse_decimal(self, s, i):
        m = END_NUMBER.search(s, i)
        if not m:
            self.token += s[i:]
            return (self.parse_decimal, len(s))
        j = m.start(0)
        self.token += s[i:j]
        self.add_token(Decimal(self.token.decode('utf-8')))
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
        if isinstance(s[j], str):
            c = s[j]
        else:
            c = bytes([s[j]])
        if c == b'\\':
            self.oct = ''
            return (self.parse_string_1, j+1)
        if c == b'(':
            self.paren += 1
            self.token += c
            return (self.parse_string, j+1)
        if c == b')':
            self.paren -= 1
            if self.paren:
                self.token += c
                return (self.parse_string, j+1)
        self.add_token(self.token)
        return (self.parse_main, j+1)

    def parse_string_1(self, s, i):
        if isinstance(s[i], str):
            c = s[i]
        else:
            c = bytes([s[i]])
        if OCT_STRING.match(c) and len(self.oct) < 3:
            self.oct += c
            return (self.parse_string_1, i+1)
        if self.oct:
            self.token += bytes([int(self.oct, 8)])
            return (self.parse_string, i)
        if c in ESC_STRING:
            self.token += bytes([ESC_STRING[c]])
        return (self.parse_string, i+1)

    def parse_wopen(self, s, i):
        if isinstance(s[i], str):
            c = s[i]
        else:
            c = bytes([s[i]])
        if c.isspace() or HEX.match(c):
            return (self.parse_hexstring, i)
        if c == b'<':
            self.add_token(KEYWORD_DICT_BEGIN)
            i += 1
        return (self.parse_main, i)

    def parse_wclose(self, s, i):
        if isinstance(s[i], str):
            c = s[i]
        else:
            c = bytes([s[i]])
        if c == b'>':
            self.add_token(KEYWORD_DICT_END)
            i += 1
        return (self.parse_main, i)

    def parse_hexstring(self, s, i):
        m1 = END_HEX_STRING.search(s, i)
        if not m1:
            self.token += s[i:]
            return (self.parse_hexstring, len(s))
        j = m1.start(0)
        self.token += s[i:j]
        token = HEX_PAIR.sub(lambda m2: bytes([int(m2.group(0), 16)]),
                                                 SPC.sub(b'', self.token))
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
        linebuf = b''
        linepos = self.bufpos + self.charpos
        eol = False
        while 1:
            self.fillbuf()
            if eol:
                c = bytes([self.buf[self.charpos]])
                # handle '\r\n'
                if c == b'\n':
                    linebuf += c
                    self.charpos += 1
                break
            m = EOL.search(self.buf, self.charpos)
            if m:
                linebuf += self.buf[self.charpos:m.end(0)]
                self.charpos = m.end(0)
                if bytes([linebuf[-1]]) == b'\r':
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
        buf = b''
        while 0 < pos:
            prevpos = pos
            pos = max(0, pos-self.BUFSIZ)
            self.fp.seek(pos)
            s = self.fp.read(prevpos-pos)
            if not s: break
            while 1:
                n = max(s.rfind(b'\r'), s.rfind(b'\n'))
                if n == -1:
                    buf = s + buf
                    break
                yield s[n:]+buf
                s = s[:n]
                buf = b''
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

    def nextobject(self, direct=False):
        '''
        Yields a list of objects: keywords, literals, strings (byte arrays),
        numbers, arrays and dictionaries. Arrays and dictionaries
        are represented as Python sequence and dictionaries.
        '''
        while not self.results:
            (pos, token) = self.nexttoken()
            if (isinstance(token, int) or
                    isinstance(token, Decimal) or
                    isinstance(token, bool) or
                    isinstance(token, bytearray) or
                    isinstance(token, bytes) or
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
                        print("Incomplete dictionary construct")
                        objs.append("") # this isn't necessary.
                        # temporary fix. is this due to rental books?
                        # raise PSSyntaxError(
                        #     'Invalid dictionary construct: %r' % objs)
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
                if direct:
                    return self.pop(1)[0]
                self.flush()
        obj = self.results.pop(0)
        return obj


LITERAL_CRYPT = LIT(b'Crypt')
LITERALS_FLATE_DECODE = (LIT(b'FlateDecode'), LIT(b'Fl'))
LITERALS_LZW_DECODE = (LIT(b'LZWDecode'), LIT(b'LZW'))
LITERALS_ASCII85_DECODE = (LIT(b'ASCII85Decode'), LIT(b'A85'))


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

    def __init__(self, doc, objid, genno):
        if objid == 0:
            if STRICT:
                raise PDFValueError('PDF object id cannot be 0.')
        self.doc = doc
        self.objid = objid
        self.genno = genno
        return

    def __repr__(self):
        return '<PDFObjRef:%d %d>' % (self.objid, self.genno)

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
        for (k,v) in iter(x.items()):
            x[k] = resolve_all(v)
    return x

def decipher_all(decipher, objid, genno, x):
    '''
    Recursively decipher X.
    '''
    if isinstance(x, bytearray) or isinstance(x,bytes) or isinstance(x,str):
        return decipher(objid, genno, x)
    decf = lambda v: decipher_all(decipher, objid, genno, v)
    if isinstance(x, list):
        x = [decf(v) for v in x]
    elif isinstance(x, dict):
        x = dict((k, decf(v)) for (k, v) in iter(x.items()))
    return x


# Type cheking
def int_value(x):
    x = resolve1(x)
    if not isinstance(x, int):
        if STRICT:
            raise PDFTypeError('Integer required: %r' % x)
        return 0
    return x

def decimal_value(x):
    x = resolve1(x)
    if not isinstance(x, Decimal):
        if STRICT:
            raise PDFTypeError('Decimal required: %r' % x)
        return 0.0
    return x

def num_value(x):
    x = resolve1(x)
    if not (isinstance(x, int) or isinstance(x, Decimal)):
        if STRICT:
            raise PDFTypeError('Int or Float required: %r' % x)
        return 0
    return x

def str_value(x):
    x = resolve1(x)
    if not (isinstance(x, bytearray) or isinstance(x, bytes) or isinstance(x, str)):
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
    out = b''
    for c in data:
        if b'!' <= c and c <= b'u':
            n += 1
            b = b*85+(c-33)
            if n == 5:
                out += struct.pack('>L',b)
                n = b = 0
        elif c == b'z':
            assert n == 0
            out += b'\0\0\0\0'
        elif c == b'~':
            if n:
                for _ in range(5-n):
                    b = b*85+84
                out += struct.pack('>L',b)[:n-1]
            break
    return out


##  PDFStream type
class PDFStream(PDFObject):
    def __init__(self, dic, rawdata, decipher=None):
        length = int_value(dic.get('Length', 0))
        eol = rawdata[length:]
        # quick and dirty fix for false length attribute,
        # might not work if the pdf stream parser has a problem
        if decipher != None and decipher.__name__ == 'decrypt_aes':
            if (len(rawdata) % 16) != 0:
                cutdiv = len(rawdata) // 16
                rawdata = rawdata[:16*cutdiv]
        else:
            if eol in (b'\r', b'\n', b'\r\n'):
                rawdata = rawdata[:length]

        self.dic = dic
        self.rawdata = rawdata
        self.decipher = decipher
        self.data = None
        self.decdata = None
        self.objid = None
        self.genno = None
        return

    def set_objid(self, objid, genno):
        self.objid = objid
        self.genno = genno
        return

    def __repr__(self):
        if self.rawdata:
            return '<PDFStream(%r): raw=%d, %r>' % \
                   (self.objid, len(self.rawdata), self.dic)
        else:
            return '<PDFStream(%r): data=%d, %r>' % \
                   (self.objid, len(self.data), self.dic)

    def decode(self):
        assert self.data is None and self.rawdata is not None
        data = self.rawdata
        if self.decipher:
            # Handle encryption
            data = self.decipher(self.objid, self.genno, data)
            if gen_xref_stm:
                self.decdata = data # keep decrypted data
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
                data = b''.join(LZWDecoder(BytesIO(data)).run())
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
                    buf = b''
                    ent0 = b'\x00' * columns
                    for i in range(0, len(data), columns+1):
                        pred = data[i]
                        ent1 = data[i+1:i+1+columns]
                        if pred == 2:
                            ent1 = b''.join(bytes([(a+b) & 255]) \
                                           for (a,b) in zip(ent0,ent1))
                        buf += ent1
                        ent0 = ent1
                    data = buf
        self.data = data
        self.rawdata = None
        return

    def get_data(self):
        if self.data is None:
            self.decode()
        return self.data

    def get_rawdata(self):
        return self.rawdata

    def get_decdata(self):
        if self.decdata is not None:
            return self.decdata
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
LITERAL_OBJSTM = LIT(b'ObjStm')
LITERAL_XREF = LIT(b'XRef')
LITERAL_PAGE = LIT(b'Page')
LITERAL_PAGES = LIT(b'Pages')
LITERAL_CATALOG = LIT(b'Catalog')


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
        return iter(self.offsets.keys())

    def load(self, parser):
        self.offsets = {}
        while 1:
            try:
                (pos, line) = parser.nextline()
            except PSEOF:
                raise PDFNoValidXRef('Unexpected EOF - file corrupted?')
            if not line:
                raise PDFNoValidXRef('Premature eof: %r' % parser)
            if line.startswith(b'trailer'):
                parser.seek(pos)
                break
            f = line.strip().split(b' ')
            if len(f) != 2:
                raise PDFNoValidXRef('Trailer not found: %r: line=%r' % (parser, line))
            try:
                (start, nobjs) = map(int, f)
            except ValueError:
                raise PDFNoValidXRef('Invalid line: %r: line=%r' % (parser, line))
            for objid in range(start, start+nobjs):
                try:
                    (_, line) = parser.nextline()
                except PSEOF:
                    raise PDFNoValidXRef('Unexpected EOF - file corrupted?')
                f = line.strip().split(b' ')
                if len(f) != 3:
                    raise PDFNoValidXRef('Invalid XRef format: %r, line=%r' % (parser, line))
                (pos, genno, use) = f
                if use != b'n':
                    continue
                self.offsets[objid] = (int(genno.decode('utf-8')), int(pos.decode('utf-8')))
        self.load_trailer(parser)
        return

    KEYWORD_TRAILER = KWD(b'trailer')
    def load_trailer(self, parser):
        try:
            (_,kwd) = parser.nexttoken()
            assert kwd is self.KEYWORD_TRAILER
            (_,dic) = parser.nextobject(direct=True)
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
        return '<PDFXRef: objids=%s>' % self.index

    def objids(self):
        for first, size in self.index:
            for objid in range(first, first + size):
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
        self.index = list(zip(itertools.islice(index, 0, None, 2),
                              itertools.islice(index, 1, None, 2)))
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
        return

    # set_parser(parser)
    #   Associates the document with an (already initialized) parser object.
    def set_parser(self, parser):
        if self.parser:
            return
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
                try:
                    self.encryption = (list_value(trailer['ID']),
                                   dict_value(trailer['Encrypt']))
                # fix for bad files
                except:
                    self.encryption = (b'ffffffffffffffffffffffffffffffffffff',
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
    def initialize(self, password=b'', inept=True):
        if not self.encryption:
            self.is_printable = self.is_modifiable = self.is_extractable = True
            self.ready = True
            raise PDFEncryptionError('Document is not encrypted.')
            return
        (docid, param) = self.encryption
        type = literal_name(param['Filter'])
        if type == 'Adobe.APS':
            return self.initialize_adobe_ps(password, docid, param)
        if type == 'Standard':
            return self.initialize_standard(password, docid, param)
        if type == 'EBX_HANDLER' and inept is True:
            return self.initialize_ebx_inept(password, docid, param)
        if type == 'EBX_HANDLER' and inept is False:
            return self.initialize_ebx_ignoble(password, docid, param)

        raise PDFEncryptionError('Unknown filter: param=%r' % param)

    def initialize_and_return_filter(self):
        if not self.encryption:
            self.is_printable = self.is_modifiable = self.is_extractable = True
            self.ready = True
            return None

        (docid, param) = self.encryption
        type = literal_name(param['Filter'])
        return type

    def initialize_adobe_ps(self, password, docid, param):
        global KEYFILEPATH
        self.decrypt_key = self.genkey_adobe_ps(param)
        self.genkey = self.genkey_v4
        self.decipher = self.decrypt_aes
        self.ready = True
        return

    def genkey_adobe_ps(self, param):
        # nice little offline principal keys dictionary
        # global static principal key for German Onleihe / Bibliothek Digital
        principalkeys = { b'bibliothek-digital.de': codecs.decode(b'rRwGv2tbpKov1krvv7PO0ws9S436/lArPlfipz5Pqhw=','base64')}
        self.is_printable = self.is_modifiable = self.is_extractable = True
        length = int_value(param.get('Length', 0)) // 8
        edcdata = str_value(param.get('EDCData')).decode('base64')
        pdrllic = str_value(param.get('PDRLLic')).decode('base64')
        pdrlpol = str_value(param.get('PDRLPol')).decode('base64')
        edclist = []
        for pair in edcdata.split(b'\n'):
            edclist.append(pair)
        # principal key request
        for key in principalkeys:
            if key in pdrllic:
                principalkey = principalkeys[key]
            else:
                raise ADEPTError('Cannot find principal key for this pdf')
        shakey = SHA256(principalkey)
        ivector = bytes(16) # 16 zero bytes
        plaintext = AES.new(shakey,AES.MODE_CBC,ivector).decrypt(edclist[9].decode('base64'))
        if plaintext[-16:] != bytearray(b'\0x10')*16:
            raise ADEPTError('Offlinekey cannot be decrypted, aborting ...')
        pdrlpol = AES.new(plaintext[16:32],AES.MODE_CBC,edclist[2].decode('base64')).decrypt(pdrlpol)
        if pdrlpol[-1] < 1 or pdrlpol[-1] > 16:
            raise ADEPTError('Could not decrypt PDRLPol, aborting ...')
        else:
            cutter = -1 * pdrlpol[-1]
            pdrlpol = pdrlpol[:cutter]
        return plaintext[:16]

    PASSWORD_PADDING = b'(\xbfN^Nu\x8aAd\x00NV\xff\xfa\x01\x08..' \
                       b'\x00\xb6\xd0h>\x80/\x0c\xa9\xfedSiz'
    # experimental aes pw support

    def check_user_password(self, password, docid, param):
        V = int_value(param.get('V', 0))
        if V < 5:
            return self.check_user_password_V4(password, docid, param)
        else:
            return self.check_user_password_V5(password, param)

    def check_owner_password(self, password, docid, param):
        V = int_value(param.get('V', 0))
        if V < 5:
            return self.check_owner_password_V4(password, docid, param)
        else:
            return self.check_owner_password_V5(password, param)

    def check_user_password_V5(self, password, param):
        U = str_value(param['U'])
        userdata = U[:32]
        salt = U[32:32+8]
        # Truncate password:
        password = password[:min(127, len(password))]
        if self.hash_V5(password, salt, b"", param) == userdata:
            return True
        return None

    def check_owner_password_V5(self, password, param):
        U = str_value(param['U'])
        O = str_value(param['O'])
        userdata = U[:48]
        ownerdata = O[:32]
        salt = O[32:32+8]
        # Truncate password:
        password = password[:min(127, len(password))]
        if self.hash_V5(password, salt, userdata, param) == ownerdata:
            return True
        return None

    def recover_encryption_key_with_password(self, password, docid, param):
        # Truncate password:
        key_password = password[:min(127, len(password))]

        if self.check_owner_password_V5(key_password, param):
            O = str_value(param['O'])
            U = str_value(param['U'])
            OE = str_value(param['OE'])
            key_salt = O[40:40+8]
            user_data = U[:48]
            encrypted_file_key = OE[:32]
        elif self.check_user_password_V5(key_password, param):
            U = str_value(param['U'])
            UE = str_value(param['UE'])
            key_salt = U[40:40+8]
            user_data = b""
            encrypted_file_key = UE[:32]
        else:
            raise Exception("Trying to recover key, but neither user nor owner pass is correct.")

        intermediate_key = self.hash_V5(key_password, key_salt, user_data, param)

        file_key = self.process_with_aes(intermediate_key, False, encrypted_file_key)

        return file_key


    def process_with_aes(self, key, encrypt, data, repetitions = 1, iv = None):
        if iv is None:
            keylen = len(key)
            iv = bytes([0x00]*keylen)

        if not encrypt:
            plaintext = AES.new(key,AES.MODE_CBC,iv, True).decrypt(data)
            return plaintext
        else:
            aes = AES.new(key, AES.MODE_CBC, iv, False)
            new_data = bytes(data * repetitions)
            crypt = aes.encrypt(new_data)
            return crypt


    def hash_V5(self, password, salt, userdata, param):
        R = int_value(param['R'])
        K = SHA256(password + salt + userdata)
        if R < 6:
            return K
        elif R == 6:
            round_number = 0
            done = False
            while (not done):
                round_number = round_number + 1
                K1 = password + K + userdata
                if len(K1) < 32:
                    raise Exception("K1 < 32 ...")
                #def process_with_aes(self, key: bytes, encrypt: bool, data: bytes, repetitions: int = 1, iv: bytes = None):
                E = self.process_with_aes(K[:16], True, K1, 64, K[16:32])
                K = (hashlib.sha256, hashlib.sha384, hashlib.sha512)[sum(E) % 3](E).digest()

                if round_number >= 64:
                    ch = int.from_bytes(E[-1:], "big", signed=False)
                    if ch <= round_number - 32:
                        done = True

            result = K[0:32]
            return result
        else:
            raise NotImplementedError("Revision > 6 not supported.")


    def check_owner_password_V4(self, password, docid, param):

        # compute_O_rc4_key:
        V = int_value(param.get('V', 0))
        if V >= 5:
            raise Exception("compute_O_rc4_key not possible with V>= 5")

        R = int_value(param.get('R', 0))

        length = int_value(param.get('Length', 40)) # Key length (bits)
        password = (password+self.PASSWORD_PADDING)[:32]
        hash = hashlib.md5(password)
        if R >= 3:
            for _ in range(50):
                hash = hashlib.md5(hash.digest()[:length//8])
        hash = hash.digest()[:length//8]

        # "hash" is the return value of compute_O_rc4_key

        Odata = str_value(param.get('O'))
        # now call iterate_rc4 ...
        x = ARC4.new(hash).decrypt(Odata) # 4
        if R >= 3:
            for i in range(1,19+1):
                k = b''.join(bytes([c ^ i]) for c in hash )
                x = ARC4.new(k).decrypt(x)


        # "x" is now the padded user password.

        # If we wanted to recover / extract the user password,
        # we'd need to trim off the padding string from the end.
        # As we just want to get access to the encryption key,
        # we can just hand the password into the check_user_password
        # as it is, as that function would be adding padding anyways.
        # This trick only works with V4 and lower.

        enc_key = self.check_user_password(x, docid, param)
        if enc_key is not None:
            return enc_key

        return False




    def check_user_password_V4(self, password, docid, param):

        V = int_value(param.get('V', 0))
        length = int_value(param.get('Length', 40)) # Key length (bits)
        O = str_value(param['O'])
        R = int_value(param['R']) # Revision
        U = str_value(param['U'])
        P = int_value(param['P'])

        # Algorithm 3.2
        password = (password+self.PASSWORD_PADDING)[:32] # 1
        hash = hashlib.md5(password) # 2
        hash.update(O) # 3
        hash.update(struct.pack('<l', P)) # 4
        hash.update(docid[0]) # 5
        # aes special handling if metadata isn't encrypted
        try:
            EncMetadata = str_value(param['EncryptMetadata'])
        except:
            EncMetadata = b'True'
        if (EncMetadata == ('False' or 'false') or V < 4) and R >= 4:
            hash.update(codecs.decode(b'ffffffff','hex'))
        if R >= 3:
            # 8
            for _ in range(50):
                hash = hashlib.md5(hash.digest()[:length//8])
        key = hash.digest()[:length//8]
        if R == 2:
            # Algorithm 3.4
            u1 = ARC4.new(key).decrypt(password)
        elif R >= 3:
            # Algorithm 3.5
            hash = hashlib.md5(self.PASSWORD_PADDING) # 2
            hash.update(docid[0]) # 3
            x = ARC4.new(key).decrypt(hash.digest()[:16]) # 4
            for i in range(1,19+1):
                k = b''.join(bytes([c ^ i]) for c in key )
                x = ARC4.new(k).decrypt(x)
            u1 = x+x # 32bytes total
        if R == 2:
            is_authenticated = (u1 == U)
        else:
            is_authenticated = (u1[:16] == U[:16])

        if is_authenticated:
            return key

        return None

    def initialize_standard(self, password, docid, param):

        self.decrypt_key = None


        # copy from a global variable
        V = int_value(param.get('V', 0))
        if (V <=0 or V > 5):
            raise PDFEncryptionError('Unknown algorithm: %r' % V)
        R = int_value(param['R']) # Revision
        if R >= 7:
            raise PDFEncryptionError('Unknown revision: %r' % R)

        # check owner pass:
        retval = self.check_owner_password(password, docid, param)
        if retval is True or retval is not None:
            #print("Owner pass is valid - " + str(retval))
            if retval is True:
                self.decrypt_key = self.recover_encryption_key_with_password(password, docid, param)
            else:
                self.decrypt_key = retval

        if self.decrypt_key is None or self.decrypt_key is True or self.decrypt_key is False:
            # That's not the owner password. Check if it's the user password.
            retval = self.check_user_password(password, docid, param)
            if retval is True or retval is not None:
                #print("User pass is valid")
                if retval is True:
                    self.decrypt_key = self.recover_encryption_key_with_password(password, docid, param)
                else:
                    self.decrypt_key = retval

        if self.decrypt_key is None or self.decrypt_key is True or self.decrypt_key is False:
            raise ADEPTInvalidPasswordError("Password invalid.")


        P = int_value(param['P'])

        self.is_printable = bool(P & 4)
        self.is_modifiable = bool(P & 8)
        self.is_extractable = bool(P & 16)
        self.is_annotationable = bool(P & 32)
        self.is_formsenabled = bool(P & 256)
        self.is_textextractable = bool(P & 512)
        self.is_assemblable = bool(P & 1024)
        self.is_formprintable = bool(P & 2048)


        # genkey method
        if V == 1 or V == 2 or V == 4:
            self.genkey = self.genkey_v2
        elif V == 3:
            self.genkey = self.genkey_v3
        elif V >= 5:
            self.genkey = self.genkey_v5

        set_decipher = False

        if V >= 4:
            # Check if we need new genkey_v4 - only if we're using AES.
            try:
                for key in param['CF']:
                    algo = str(param["CF"][key]["CFM"])
                    if algo == "/AESV2":
                        if V == 4:
                            self.genkey = self.genkey_v4
                        set_decipher = True
                        self.decipher = self.decrypt_aes
                    elif algo == "/AESV3":
                        if V == 4:
                            self.genkey = self.genkey_v4
                        set_decipher = True
                        self.decipher = self.decrypt_aes
                    elif algo == "/V2":
                        set_decipher = True
                        self.decipher = self.decrypt_rc4
            except:
                pass

        # rc4
        if V < 4:
            self.decipher = self.decrypt_rc4  # XXX may be AES
        # aes
        if not set_decipher:
            # This should usually already be set by now.
            # If it's not, assume that V4 and newer are using AES
            if V >= 4:
                self.decipher = self.decrypt_aes
        self.ready = True
        return


    def initialize_ebx_ignoble(self, keyb64, docid, param):
        self.is_printable = self.is_modifiable = self.is_extractable = True
        key = keyb64.decode('base64')[:16]

        length = int_value(param.get('Length', 0)) / 8
        rights = codecs.decode(str_value(param.get('ADEPT_LICENSE')), "base64")
        rights = zlib.decompress(rights, -15)
        rights = etree.fromstring(rights)
        expr = './/{http://ns.adobe.com/adept}encryptedKey'
        bookkey = ''.join(rights.findtext(expr))
        bookkey = base64.b64decode(bookkey)
        bookkey = AES.new(key, AES.MODE_CBC, b'\x00'*16).decrypt(bookkey)
        bookkey = unpad(bookkey, 16) # PKCS#7
        if len(bookkey) > 16:
            bookkey = bookkey[-16:]
        ebx_V = int_value(param.get('V', 4))
        ebx_type = int_value(param.get('EBX_ENCRYPTIONTYPE', 6))
        # added because of improper booktype / decryption book session key errors
        if length > 0:
            if len(bookkey) == length:
                if ebx_V == 3:
                    V = 3
                else:
                    V = 2
            elif len(bookkey) == length + 1:
                V = bookkey[0]
                bookkey = bookkey[1:]
            else:
                print("ebx_V is %d  and ebx_type is %d" % (ebx_V, ebx_type))
                print("length is %d and len(bookkey) is %d" % (length, len(bookkey)))
                print("bookkey[0] is %d" % bookkey[0])
                raise ADEPTError('error decrypting book session key - mismatched length')
        else:
            # proper length unknown try with whatever you have
            print("ebx_V is %d  and ebx_type is %d" % (ebx_V, ebx_type))
            print("length is %d and len(bookkey) is %d" % (length, len(bookkey)))
            print("bookkey[0] is %d" % ord(bookkey[0]))
            if ebx_V == 3:
                V = 3
            else:
                V = 2
        self.decrypt_key = bookkey
        self.genkey = self.genkey_v3 if V == 3 else self.genkey_v2
        self.decipher = self.decrypt_rc4
        self.ready = True
        return

    @staticmethod
    def removeHardening(rights, keytype, keydata):
        adept = lambda tag: '{%s}%s' % ('http://ns.adobe.com/adept', tag)
        textGetter = lambda name: ''.join(rights.findtext('.//%s' % (adept(name),)))

        # Gather what we need, and generate the IV
        resourceuuid = UUID(textGetter("resource"))
        deviceuuid = UUID(textGetter("device"))
        fullfillmentuuid = UUID(textGetter("fulfillment")[:36])
        kekiv = UUID(int=resourceuuid.int ^ deviceuuid.int ^ fullfillmentuuid.int).bytes

        # Derive kek from just "keytype"
        rem = int(keytype, 10) % 16
        H = SHA256(keytype.encode("ascii"))
        kek = H[2*rem : 16 + rem] + H[rem : 2*rem]

        return unpad(AES.new(kek, AES.MODE_CBC, kekiv).decrypt(keydata), 16)

    def initialize_ebx_inept(self, password, docid, param):
        self.is_printable = self.is_modifiable = self.is_extractable = True
        rsakey = RSA.import_key(password) # parses the ASN1 structure
        length = int_value(param.get('Length', 0)) // 8
        rights = codecs.decode(param.get('ADEPT_LICENSE'), 'base64')
        rights = zlib.decompress(rights, -15)
        rights = etree.fromstring(rights)
        expr = './/{http://ns.adobe.com/adept}encryptedKey'
        bookkeyelem = rights.find(expr)
        bookkey = codecs.decode(bookkeyelem.text.encode('utf-8'),'base64')
        keytype = bookkeyelem.attrib.get('keyType', '0')

        if int(keytype, 10) > 2:
            bookkey = PDFDocument.removeHardening(rights, keytype, bookkey)
        try:
            bookkey = PKCS1_v1_5.new(rsakey).decrypt(bookkey, None) # automatically unpads
        except ValueError:
            bookkey = None

        if bookkey is None:
            raise ADEPTError('error decrypting book session key')

        ebx_V = int_value(param.get('V', 4))
        ebx_type = int_value(param.get('EBX_ENCRYPTIONTYPE', 6))
        # added because of improper booktype / decryption book session key errors
        if length > 0:
            if len(bookkey) == length:
                if ebx_V == 3:
                    V = 3
                else:
                    V = 2
            elif len(bookkey) == length + 1:
                V = bookkey[0]
                bookkey = bookkey[1:]
            else:
                print("ebx_V is %d  and ebx_type is %d" % (ebx_V, ebx_type))
                print("length is %d and len(bookkey) is %d" % (length, len(bookkey)))
                print("bookkey[0] is %d" % bookkey[0])
                raise ADEPTError('error decrypting book session key - mismatched length')
        else:
            # proper length unknown try with whatever you have
            print("ebx_V is %d  and ebx_type is %d" % (ebx_V, ebx_type))
            print("length is %d and len(bookkey) is %d" % (length, len(bookkey)))
            print("bookkey[0] is %d" % bookkey[0])
            if ebx_V == 3:
                V = 3
            else:
                V = 2
        self.decrypt_key = bookkey
        self.genkey = self.genkey_v3 if V == 3 else self.genkey_v2
        self.decipher = self.decrypt_rc4
        self.ready = True
        return

    # genkey functions
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
        key += bytes([objid[0], genno[0], objid[1], genno[1], objid[2]]) + b'sAlT'
        hash = hashlib.md5(key)
        key = hash.digest()[:min(len(self.decrypt_key) + 5, 16)]
        return key

    # aes v2 and v4 algorithm
    def genkey_v4(self, objid, genno):
        objid = struct.pack('<L', objid)[:3]
        genno = struct.pack('<L', genno)[:2]
        key = self.decrypt_key + objid + genno + b'sAlT'
        hash = hashlib.md5(key)
        key = hash.digest()[:min(len(self.decrypt_key) + 5, 16)]
        return key

    def genkey_v5(self, objid, genno):
        # Looks like they stopped this useless obfuscation.
        return self.decrypt_key

    def decrypt_aes(self, objid, genno, data):
        key = self.genkey(objid, genno)
        ivector = data[:16]
        data = data[16:]
        plaintext = AES.new(key,AES.MODE_CBC,ivector).decrypt(data)
        # remove pkcs#5 aes padding
        cutter = -1 * plaintext[-1]
        plaintext = plaintext[:cutter]
        return plaintext

    def decrypt_rc4(self, objid, genno, data):
        key = self.genkey(objid, genno)
        return ARC4.new(key).decrypt(data)


    KEYWORD_OBJ = KWD(b'obj')

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
                #if STRICT:
                #    raise PDFSyntaxError('Cannot locate objid=%r' % objid)
                return None
            if stmid:
                if gen_xref_stm:
                    return PDFObjStmRef(objid, stmid, index)
                # Stuff from pdfminer: extract objects from object stream
                stream = stream_value(self.getobj(stmid))
                if stream.dic.get('Type') is not LITERAL_OBJSTM:
                    if STRICT:
                        raise PDFSyntaxError('Not a stream object: %r' % stream)
                try:
                    n = stream.dic['N']
                except KeyError:
                    if STRICT:
                        raise PDFSyntaxError('N is not defined: %r' % stream)
                    n = 0

                if stmid in self.parsed_objs:
                    objs = self.parsed_objs[stmid]
                else:
                    parser = PDFObjStrmParser(stream.get_data(), self)
                    objs = []
                    try:
                        while 1:
                            (_,obj) = parser.nextobject()
                            objs.append(obj)
                    except PSEOF:
                        pass
                    self.parsed_objs[stmid] = objs
                genno = 0
                i = n*2+index
                try:
                    obj = objs[i]
                except IndexError:
                    raise PDFSyntaxError('Invalid object number: objid=%r' % (objid))
                if isinstance(obj, PDFStream):
                    obj.set_objid(objid, 0)
            else:
                self.parser.seek(index)
                (_,objid1) = self.parser.nexttoken() # objid
                (_,genno) = self.parser.nexttoken() # genno
                #assert objid1 == objid, (objid, objid1)
                (_,kwd) = self.parser.nexttoken()
        # #### hack around malformed pdf files
        #        assert objid1 == objid, (objid, objid1)
##                if objid1 != objid:
##                    x = []
##                    while kwd is not self.KEYWORD_OBJ:
##                        (_,kwd) = self.parser.nexttoken()
##                        x.append(kwd)
##                    if x:
##                        objid1 = x[-2]
##                        genno = x[-1]
##
                if kwd is not self.KEYWORD_OBJ:
                    raise PDFSyntaxError(
                        'Invalid object spec: offset=%r' % index)
                (_,obj) = self.parser.nextobject()
                if isinstance(obj, PDFStream):
                    obj.set_objid(objid, genno)
                if self.decipher:
                    obj = decipher_all(self.decipher, objid, genno, obj)
            self.objs[objid] = obj
        return obj


class PDFObjStmRef(object):
    maxindex = 0
    def __init__(self, objid, stmid, index):
        self.objid = objid
        self.stmid = stmid
        self.index = index
        if index > PDFObjStmRef.maxindex:
            PDFObjStmRef.maxindex = index


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

    KEYWORD_R = KWD(b'R')
    KEYWORD_ENDOBJ = KWD(b'endobj')
    KEYWORD_STREAM = KWD(b'stream')
    KEYWORD_XREF = KWD(b'xref')
    KEYWORD_STARTXREF = KWD(b'startxref')
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
                if b'endstream' in line:
                    i = line.index(b'endstream')
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
            if line == b'startxref': break
            if line:
                prev = line
        else:
            raise PDFNoValidXRef('Unexpected EOF')
        return int(prev)

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
            if GEN_XREF_STM == 1:
                global gen_xref_stm
                gen_xref_stm = True
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
        trailerpos = None
        try:
            pos = self.find_xref()
            self.read_xref_from(pos, xrefs)
        except PDFNoValidXRef:
            # fallback
            self.seek(0)
            pat = re.compile(b'^(\\d+)\\s+(\\d+)\\s+obj\\b')
            offsets = {}
            xref = PDFXRef()
            while 1:
                try:
                    (pos, line) = self.nextline()
                except PSEOF:
                    break
                if line.startswith(b'trailer'):
                    trailerpos = pos # remember last trailer
                m = pat.match(line)
                if not m: continue
                (objid, genno) = m.groups()
                offsets[int(objid)] = (0, pos)
            if not offsets: raise
            xref.offsets = offsets
            if trailerpos:
                self.seek(trailerpos)
                xref.load_trailer(self)
                xrefs.append(xref)
        return xrefs

##  PDFObjStrmParser
##
class PDFObjStrmParser(PDFParser):

    def __init__(self, data, doc):
        PSStackParser.__init__(self, BytesIO(data))
        self.doc = doc
        return

    def flush(self):
        self.add_results(*self.popall())
        return

    KEYWORD_R = KWD(b'R')
    def do_keyword(self, pos, token):
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
        # others
        self.push((pos, token))
        return


# Takes a PDF file name as input, and if this is an ADE-protected PDF,
# returns the UUID of the user that's licensed to open this file.
def adeptGetUserUUID(inf):
    try:
        doc = PDFDocument()
        inf = open(inf, 'rb')
        pars = PDFParser(doc, inf)

        (docid, param) = doc.encryption
        type = literal_name(param['Filter'])
        if type != 'EBX_HANDLER':
            # No EBX_HANDLER, no idea which user key can decrypt this.
            inf.close()
            return None

        rights = codecs.decode(param.get('ADEPT_LICENSE'), 'base64')
        inf.close()

        rights = zlib.decompress(rights, -15)
        rights = etree.fromstring(rights)
        expr = './/{http://ns.adobe.com/adept}user'
        user_uuid = ''.join(rights.findtext(expr))
        if user_uuid[:9] != "urn:uuid:":
            return None
        return user_uuid[9:]

    except:
        return None

###
### My own code, for which there is none else to blame

class PDFSerializer(object):
    def __init__(self, inf, userkey, inept=True):
        global GEN_XREF_STM, gen_xref_stm
        gen_xref_stm = GEN_XREF_STM > 1
        self.version = inf.read(8)
        inf.seek(0)
        self.doc = doc = PDFDocument()
        parser = PDFParser(doc, inf)
        doc.initialize(userkey, inept)
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
        self.write(b'\n%\xe2\xe3\xcf\xd3\n')
        doc = self.doc
        objids = self.objids
        xrefs = {}
        maxobj = max(objids)
        trailer = dict(self.trailer)
        trailer['Size'] = maxobj + 1
        for objid in objids:
            obj = doc.getobj(objid)
            if isinstance(obj, PDFObjStmRef):
                xrefs[objid] = obj
                continue
            if obj is not None:
                try:
                    genno = obj.genno
                except AttributeError:
                    genno = 0
                xrefs[objid] = (self.tell(), genno)
                self.serialize_indirect(objid, obj)
        startxref = self.tell()

        if not gen_xref_stm:
            self.write(b'xref\n')
            self.write(b'0 %d\n' % (maxobj + 1,))
            for objid in range(0, maxobj + 1):
                if objid in xrefs:
                    # force the genno to be 0
                    self.write(b"%010d 00000 n \n" % xrefs[objid][0])
                else:
                    self.write(b"%010d %05d f \n" % (0, 65535))

            self.write(b'trailer\n')
            self.serialize_object(trailer)
            self.write(b'\nstartxref\n%d\n%%%%EOF' % startxref)

        else: # Generate crossref stream.

            # Calculate size of entries
            maxoffset = max(startxref, maxobj)
            maxindex = PDFObjStmRef.maxindex
            fl2 = 2
            power = 65536
            while maxoffset >= power:
                fl2 += 1
                power *= 256
            fl3 = 1
            power = 256
            while maxindex >= power:
                fl3 += 1
                power *= 256

            index = []
            first = None
            prev = None
            data = []
            # Put the xrefstream's reference in itself
            startxref = self.tell()
            maxobj += 1
            xrefs[maxobj] = (startxref, 0)
            for objid in sorted(xrefs):
                if first is None:
                    first = objid
                elif objid != prev + 1:
                    index.extend((first, prev - first + 1))
                    first = objid
                prev = objid
                objref = xrefs[objid]
                if isinstance(objref, PDFObjStmRef):
                    f1 = 2
                    f2 = objref.stmid
                    f3 = objref.index
                else:
                    f1 = 1
                    f2 = objref[0]
                    # we force all generation numbers to be 0
                    # f3 = objref[1]
                    f3 = 0

                data.append(struct.pack('>B', f1))
                data.append(struct.pack('>L', f2)[-fl2:])
                data.append(struct.pack('>L', f3)[-fl3:])
            index.extend((first, prev - first + 1))
            data = zlib.compress(b''.join(data))
            dic = {'Type': LITERAL_XREF, 'Size': prev + 1, 'Index': index,
                   'W': [1, fl2, fl3], 'Length': len(data),
                   'Filter': LITERALS_FLATE_DECODE[0],
                   'Root': trailer['Root'],}
            if 'Info' in trailer:
                dic['Info'] = trailer['Info']
            xrefstm = PDFStream(dic, data)
            self.serialize_indirect(maxobj, xrefstm)
            self.write(b'startxref\n%d\n%%%%EOF' % startxref)
    def write(self, data):
        self.outf.write(data)
        self.last = data[-1:]

    def tell(self):
        return self.outf.tell()

    def escape_string(self, string):
        string = string.replace(b'\\', b'\\\\')
        string = string.replace(b'\n', b'\\n')
        string = string.replace(b'(', b'\\(')
        string = string.replace(b')', b'\\)')
        return string

    def serialize_object(self, obj):
        if isinstance(obj, dict):
            # Correct malformed Mac OS resource forks for Stanza
            if 'ResFork' in obj and 'Type' in obj and 'Subtype' not in obj \
                   and isinstance(obj['Type'], int):
                obj['Subtype'] = obj['Type']
                del obj['Type']
            # end - hope this doesn't have bad effects
            self.write(b'<<')
            for key, val in obj.items():
                self.write(str(LIT(key.encode('utf-8'))).encode('utf-8'))
                self.serialize_object(val)
            self.write(b'>>')
        elif isinstance(obj, list):
            self.write(b'[')
            for val in obj:
                self.serialize_object(val)
            self.write(b']')
        elif isinstance(obj, bytearray):
            self.write(b'(%s)' % self.escape_string(obj))
        elif isinstance(obj, bytes):
            self.write(b'(%s)' % self.escape_string(obj))
        elif isinstance(obj, str):
            self.write(b'(%s)' % self.escape_string(obj.encode('utf-8')))
        elif isinstance(obj, bool):
            if self.last.isalnum():
                self.write(b' ')
            self.write(str(obj).lower().encode('utf-8'))
        elif isinstance(obj, int):
            if self.last.isalnum():
                self.write(b' ')
            self.write(str(obj).encode('utf-8'))
        elif isinstance(obj, Decimal):
            if self.last.isalnum():
                self.write(b' ')
            self.write(str(obj).encode('utf-8'))
        elif isinstance(obj, PDFObjRef):
            if self.last.isalnum():
                self.write(b' ')
            self.write(b'%d %d R' % (obj.objid, 0))
        elif isinstance(obj, PDFStream):
            ### If we don't generate cross ref streams the object streams
            ### are no longer useful, as we have extracted all objects from
            ### them. Therefore leave them out from the output.
            if obj.dic.get('Type') == LITERAL_OBJSTM and not gen_xref_stm:
                self.write(b'(deleted)')
            else:
                data = obj.get_decdata()
                self.serialize_object(obj.dic)
                self.write(b'stream\n')
                self.write(data)
                self.write(b'\nendstream')
        else:
            data = str(obj).encode('utf-8')
            if bytes([data[0]]).isalnum() and self.last.isalnum():
                self.write(b' ')
            self.write(data)

    def serialize_indirect(self, objid, obj):
        self.write(b'%d 0 obj' % (objid,))
        self.serialize_object(obj)
        if self.last.isalnum():
            self.write(b'\n')
        self.write(b'endobj\n')




def decryptBook(userkey, inpath, outpath, inept=True):
    with open(inpath, 'rb') as inf:
        serializer = PDFSerializer(inf, userkey, inept)
        with open(outpath, 'wb') as outf:
            # help construct to make sure the method runs to the end
            try:
                serializer.dump(outf)
            except Exception as e:
                print("error writing pdf: {0}".format(e))
                traceback.print_exc()
                return 2
    return 0


def getPDFencryptionType(inpath):
    with open(inpath, 'rb') as inf:
        doc = doc = PDFDocument()
        parser = PDFParser(doc, inf)
        filter = doc.initialize_and_return_filter()
        return filter



def cli_main():
    sys.stdout=SafeUnbuffered(sys.stdout)
    sys.stderr=SafeUnbuffered(sys.stderr)
    argv=unicode_argv()
    progname = os.path.basename(argv[0])
    if len(argv) != 4:
        print("usage: {0} <keyfile.der> <inbook.pdf> <outbook.pdf>".format(progname))
        return 1
    keypath, inpath, outpath = argv[1:]
    userkey = open(keypath,'rb').read()
    result = decryptBook(userkey, inpath, outpath)
    if result == 0:
        print("Successfully decrypted {0:s} as {1:s}".format(os.path.basename(inpath),os.path.basename(outpath)))
    return result


def gui_main():
    try:
        import tkinter
        import tkinter.constants
        import tkinter.filedialog
        import tkinter.messagebox
        import traceback
    except:
        return cli_main()

    class DecryptionDialog(tkinter.Frame):
        def __init__(self, root):
            tkinter.Frame.__init__(self, root, border=5)
            self.status = tkinter.Label(self, text="Select files for decryption")
            self.status.pack(fill=tkinter.constants.X, expand=1)
            body = tkinter.Frame(self)
            body.pack(fill=tkinter.constants.X, expand=1)
            sticky = tkinter.constants.E + tkinter.constants.W
            body.grid_columnconfigure(1, weight=2)
            tkinter.Label(body, text="Key file").grid(row=0)
            self.keypath = tkinter.Entry(body, width=30)
            self.keypath.grid(row=0, column=1, sticky=sticky)
            if os.path.exists("adeptkey.der"):
                self.keypath.insert(0, "adeptkey.der")
            button = tkinter.Button(body, text="...", command=self.get_keypath)
            button.grid(row=0, column=2)
            tkinter.Label(body, text="Input file").grid(row=1)
            self.inpath = tkinter.Entry(body, width=30)
            self.inpath.grid(row=1, column=1, sticky=sticky)
            button = tkinter.Button(body, text="...", command=self.get_inpath)
            button.grid(row=1, column=2)
            tkinter.Label(body, text="Output file").grid(row=2)
            self.outpath = tkinter.Entry(body, width=30)
            self.outpath.grid(row=2, column=1, sticky=sticky)
            button = tkinter.Button(body, text="...", command=self.get_outpath)
            button.grid(row=2, column=2)
            buttons = tkinter.Frame(self)
            buttons.pack()
            botton = tkinter.Button(
                buttons, text="Decrypt", width=10, command=self.decrypt)
            botton.pack(side=tkinter.constants.LEFT)
            tkinter.Frame(buttons, width=10).pack(side=tkinter.constants.LEFT)
            button = tkinter.Button(
                buttons, text="Quit", width=10, command=self.quit)
            button.pack(side=tkinter.constants.RIGHT)

        def get_keypath(self):
            keypath = tkinter.filedialog.askopenfilename(
                parent=None, title="Select Adobe Adept \'.der\' key file",
                defaultextension=".der",
                filetypes=[('Adobe Adept DER-encoded files', '.der'),
                           ('All Files', '.*')])
            if keypath:
                keypath = os.path.normpath(keypath)
                self.keypath.delete(0, tkinter.constants.END)
                self.keypath.insert(0, keypath)
            return

        def get_inpath(self):
            inpath = tkinter.filedialog.askopenfilename(
                parent=None, title="Select ADEPT-encrypted PDF file to decrypt",
                defaultextension=".pdf", filetypes=[('PDF files', '.pdf')])
            if inpath:
                inpath = os.path.normpath(inpath)
                self.inpath.delete(0, tkinter.constants.END)
                self.inpath.insert(0, inpath)
            return

        def get_outpath(self):
            outpath = tkinter.filedialog.asksaveasfilename(
                parent=None, title="Select unencrypted PDF file to produce",
                defaultextension=".pdf", filetypes=[('PDF files', '.pdf')])
            if outpath:
                outpath = os.path.normpath(outpath)
                self.outpath.delete(0, tkinter.constants.END)
                self.outpath.insert(0, outpath)
            return

        def decrypt(self):
            keypath = self.keypath.get()
            inpath = self.inpath.get()
            outpath = self.outpath.get()
            if not keypath or not os.path.exists(keypath):
                self.status['text'] = "Specified key file does not exist"
                return
            if not inpath or not os.path.exists(inpath):
                self.status['text'] = "Specified input file does not exist"
                return
            if not outpath:
                self.status['text'] = "Output file not specified"
                return
            if inpath == outpath:
                self.status['text'] = "Must have different input and output files"
                return
            userkey = open(keypath,'rb').read()
            self.status['text'] = "Decrypting..."
            try:
                decrypt_status = decryptBook(userkey, inpath, outpath)
            except Exception as e:
                self.status['text'] = "Error; {0}".format(e.args[0])
                return
            if decrypt_status == 0:
                self.status['text'] = "File successfully decrypted"
            else:
                self.status['text'] = "The was an error decrypting the file."


    root = tkinter.Tk()
    root.title("Adobe Adept PDF Decrypter v.{0}".format(__version__))
    root.resizable(True, False)
    root.minsize(370, 0)
    DecryptionDialog(root).pack(fill=tkinter.constants.X, expand=1)
    root.mainloop()
    return 0


if __name__ == '__main__':
    if len(sys.argv) > 1:
        sys.exit(cli_main())
    sys.exit(gui_main())
