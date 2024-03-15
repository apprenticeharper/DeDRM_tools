#! /usr/bin/python

# ineptpdf

# To run this program install Python 2.7 from http://www.python.org/download/
#
# PyCrypto from http://www.voidspace.org.uk/python/modules.shtml#pycrypto
#
# and PyWin Extension (Win32API module) from
# http://sourceforge.net/projects/pywin32/files/
#
# Make sure to install the dedicated versions for Python 2.7.
#
# It's recommended to use the 32-Bit Python Windows versions (even with a 64-bit
# Windows system).
#
# Save this script file as
# ineptpdf8.4.51.pyw and double-click on it to run it.

# Revision history:
#   1 - Initial release
#   2 - Improved determination of key-generation algorithm
#   3 - Correctly handle PDF >=1.5 cross-reference streams
#   4 - Removal of ciando's personal ID (anon)
#   5 - removing small bug with V3 ebooks (anon)
#   6 - changed to adeptkey4.der format for 1.7.2 support (anon)
#   6.1 - backward compatibility for 1.7.1 and old adeptkey.der (anon)
#   7 - Get cross reference streams and object streams working for input.
#       Not yet supported on output but this only effects file size,
#       not functionality. (anon2)
#   7.1 - Correct a problem when an old trailer is not followed by startxref (anon2)
#   7.2 - Correct malformed Mac OS resource forks for Stanza
#       - Support for cross ref streams on output (decreases file size) (anon2)
#   7.3 - Correct bug in trailer with cross ref stream that caused the error (anon2)
#         "The root object is missing or invalid" in Adobe Reader.
#   7.4 - Force all generation numbers in output file to be 0, like in v6.
#         Fallback code for wrong xref improved (search till last trailer
#         instead of first) (anon2)
#   8 - fileopen user machine identifier support (Tetrachroma)
#   8.1 - fileopen user cookies support (Tetrachroma)
#   8.2 - fileopen user name/password support (Tetrachroma)
#   8.3 - fileopen session cookie support (Tetrachroma)
#   8.3.1 - fix for the "specified key file does not exist" error (Tetrachroma)
#   8.3.2 - improved server result parsing (Tetrachroma)
#   8.4 - Ident4D and encrypted Uuid support (Tetrachroma)
#   8.4.1 - improved MAC address processing (Tetrachroma)
#   8.4.2 - FowP3Uuid fallback file processing (Tetrachroma)
#   8.4.3 - improved user/password pdf file detection (Tetrachroma)
#   8.4.4 - small bugfix (Tetrachroma)
#   8.4.5 - improved cookie host searching (Tetrachroma)
#   8.4.6 - STRICT parsing disabled (non-standard pdf processing) (Tetrachroma)
#   8.4.7 - UTF-8 input file conversion (Tetrachroma)
#   8.4.8 - fix for more rare utf8 problems (Tetrachroma)
#   8.4.9 - solution for utf8 in comination with
#           ident4id method (Tetrachroma)
#   8.4.10 - line feed processing, non c system drive patch, nrbook support (Tetrachroma)
#   8.4.11 - alternative ident4id calculation (Tetrachroma)
#   8.4.12 - fix for capital username characters and
#            other unusual user login names (Tetrachroma & ZeroPoint)
#   8.4.13 - small bug fixes (Tetrachroma)
#   8.4.14 - fix for non-standard-conform fileopen pdfs (Tetrachroma)
#   8.4.15 - 'bad file descriptor'-fix (Tetrachroma)
#   8.4.16 - improves user/pass detection (Tetrachroma)
#   8.4.17 - fix for several '=' chars in a DPRM entity (Tetrachroma)
#   8.4.18 - follow up bug fix for the DPRM problem,
#            more readable error messages (Tetrachroma)
#   8.4.19 - 2nd fix for 'bad file descriptor' problem (Tetrachroma)
#   8.4.20 - follow up patch (Tetrachroma)
#   8.4.21 - 3rd patch for 'bad file descriptor' (Tetrachroma)
#   8.4.22 - disable prints for exception prevention (Tetrachroma)
#   8.4.23 - check for additional security attributes (Tetrachroma)
#   8.4.24 - improved cookie session support (Tetrachroma)
#   8.4.25 - more compatibility with unicode files (Tetrachroma)
#   8.4.26 - automated session/user cookie request function (works
#            only with Firefox 3.x+) (Tetrachroma)
#   8.4.27 - user/password fallback
#   8.4.28 - AES decryption, improved misconfigured pdf handling,
#            limited experimental APS support (Tetrachroma & Neisklar)
#   8.4.29 - backport for bad formatted rc4 encrypted pdfs (Tetrachroma)
#   8.4.30 - extended authorization attributes support (Tetrachroma)
#   8.4.31 - improved session cookie and better server response error
#            handling (Tetrachroma)
#   8.4.33 - small cookie optimizations (Tetrachroma)
#   8.4.33 - debug output option (Tetrachroma)
#   8.4.34 - better user/password management
#            handles the 'AskUnp' response) (Tetrachroma)
#   8.4.35 - special handling for non-standard systems (Tetrachroma)
#   8.4.36 - previous machine/disk handling [PrevMach/PrevDisk] (Tetrachroma)
#   8.4.36 - FOPN_flock support (Tetrachroma)
#   8.4.37 - patch for unicode paths/filenames (Tetrachroma)
#   8.4.38 - small fix for user/password dialog (Tetrachroma)
#   8.4.39 - sophisticated request mode differentiation, forced
#            uuid calculation (Tetrachroma)
#   8.4.40 - fix for non standard server responses (Tetrachroma)
#   8.4.41 - improved user/password request windows,
#            better server response tolerance (Tetrachroma)
#   8.4.42 - improved nl/cr server response parsing (Tetrachroma)
#   8.4.43 - fix for user names longer than 13 characters and special
#            uuid encryption (Tetrachroma)
#   8.4.44 - another fix for ident4d problem (Tetrachroma)
#   8.4.45 - 2nd fix for ident4d problem (Tetrachroma)
#   8.4.46 - script cleanup and optimizations (Tetrachroma)
#   8.4.47 - script identification change to Adobe Reader (Tetrachroma)
#   8.4.48 - improved tolerance for false file/registry entries (Tetrachroma)
#   8.4.49 - improved username encryption (Tetrachroma)
#   8.4.50 - improved (experimental) APS support (Tetrachroma & Neisklar)
#   8.4.51 - automatic APS offline key retrieval (works only for
#            Onleihe right now) (80ka80 & Tetrachroma)

#   8.5.0  - First update by noDRM - trying to update the script to include
#            improvements from ineptpdf.

"""
Decrypts Adobe ADEPT-encrypted and Fileopen PDF files.
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
# added for fileopen support
import urllib
import urlparse
import time
import socket
import string
import uuid
import subprocess
import time
import getpass
from ctypes import *
import traceback
import inspect
import tempfile
import sqlite3
import httplib
import binascii

from decimal import Decimal
import itertools

try:
    from Crypto.Cipher import ARC4
    # needed for newer pdfs
    from Crypto.Cipher import AES
    from Crypto.Hash import SHA256
    from Crypto.PublicKey import RSA

except ImportError:
    ARC4 = None
    RSA = None

from io import BytesIO

class ADEPTError(Exception):
    pass

# global variable (needed for fileopen and password decryption)
INPUTFILEPATH = ''
KEYFILEPATH = ''
PASSWORD = ''
DEBUG_MODE = False
IVERSION = '8.4.51'

# Do we generate cross reference streams on output?
# 0 = never
# 1 = only if present in input
# 2 = always

GEN_XREF_STM = 1

# This is the value for the current document
gen_xref_stm = False # will be set in PDFSerializer

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
        if sys.version_info[0] == 2:
            return struct.unpack('>L', '\x00'+s)[0]
        else: 
            return struct.unpack('>L', bytes([0]) + s)[0]
    elif l == 4:
        return struct.unpack('>L', s)[0]
    else:
        return TypeError('invalid length: %d' % l)


STRICT = 0


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

class EmptyArrayValue(object):
    def __str__(self):
        return "<>"


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
        ##print >>sys.stderr, 'poll(%d): %r' % (pos, self.fp.read(n))
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
            if sys.version_info[0] == 2: 
                self.token += chr(int(self.hex, 16))
            else: 
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
            if sys.version_info[0] == 2:
                self.token += chr(int(self.oct, 8))
            else: 
                self.token += bytes([int(self.oct, 8)])  
            return (self.parse_string, i)
        if c in ESC_STRING:

            if sys.version_info[0] == 2:
                self.token += chr(ESC_STRING[c])
            else: 
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
        if c == b'>':
            # Empty array without any contents. Why though?
            # We need to add some dummy python object that will serialize to 
            # nothing, otherwise the code removes the whole array.
            self.add_token(EmptyArrayValue())
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
        m = END_HEX_STRING.search(s, i)
        if not m:
            self.token += s[i:]
            return (self.parse_hexstring, len(s))
        j = m.start(0)
        self.token += s[i:j]
        if sys.version_info[0] == 2:
            token = HEX_PAIR.sub(lambda m: chr(int(m.group(0), 16)),
                                                 SPC.sub('', self.token))
        else: 
            token = HEX_PAIR.sub(lambda m: bytes([int(m.group(0), 16)]),
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
                if sys.version_info[0] == 2: 
                    c = self.buf[self.charpos]
                else: 
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
                if sys.version_info[0] == 2:
                    if linebuf[-1] == b'\r':
                        eol = True
                    else:
                        break
                else: 
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
        for (k,v) in x.iteritems():
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
            raise PDFTypeError('Int or Decimal required: %r' % x)
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
            ##print self.dict
            return
        filters = self.dic['Filter']
        if not isinstance(filters, list):
            filters = [ filters ]
        for f in filters:
            if f in LITERALS_FLATE_DECODE:
                # will get errors if the document is encrypted.
                data = zlib.decompress(data)
            elif f in LITERALS_LZW_DECODE:
                data = ''.join(LZWDecoder(BytesIO(data)).run())
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
                        if sys.version_info[0] == 2:
                            if pred == '\x02':
                                ent1 = ''.join(chr((ord(a)+ord(b)) & 255) \
                                               for (a,b) in zip(ent0,ent1))
                        else: 
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

    KEYWORD_TRAILER = PSKeywordTable.intern(b'trailer')
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
        # dictionaries for fileopen
        self.fileopen = {}
        self.urlresult = {}
        self.ready = False
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
    def initialize(self, password=''):
        if not self.encryption:
            self.is_printable = self.is_modifiable = self.is_extractable = True
            self.ready = True
            return
        (docid, param) = self.encryption
        type = literal_name(param['Filter'])
        if type == 'Adobe.APS' or type == "Standard" or type == "EBX_HANDLER":
            print("This script is just for FOPN encryption.")
            print("For standard password PDFs or Adobe PDFs, use ineptpdy.py")
            raise PDFEncryptionError("Not a FileOpen-encrypted file")
        if type == 'FOPN_fLock':
            # remove of unnecessairy password attribute
            return self.initialize_fopn_flock(docid, param)
        if type == 'FOPN_foweb':
            # remove of unnecessairy password attribute
            return self.initialize_fopn(docid, param)
        raise PDFEncryptionError('Unknown filter: param=%r' % param)
    
    def initialize_and_return_filter(self):
        if not self.encryption:
            self.is_printable = self.is_modifiable = self.is_extractable = True
            self.ready = True
            return None

        (docid, param) = self.encryption
        type = literal_name(param['Filter'])
        return type


    PASSWORD_PADDING = b'(\xbfN^Nu\x8aAd\x00NV\xff\xfa\x01\x08..' \
                       b'\x00\xb6\xd0h>\x80/\x0c\xa9\xfedSiz'
    


    # fileopen support
    def initialize_fopn_flock(self, docid, param):
        raise ADEPTError('FOPN_fLock not supported, yet ...')
        # debug mode processing
        global DEBUG_MODE
        global IVERSION
        if DEBUG_MODE == True:
            if os.access('.',os.W_OK) == True:
                debugfile = open('ineptpdf-'+IVERSION+'-debug.txt','w')
            else:
                raise ADEPTError('Cannot write debug file, current directory is not writable')
        self.is_printable = self.is_modifiable = self.is_extractable = True
        # get parameters and add it to the fo dictionary
        self.fileopen['V'] = int_value(param.get('V',2))
        # crypt base
        (docid, param) = self.encryption
        #rights = dict_value(param['Info'])
        rights = param['Info']
        #print rights
        if DEBUG_MODE == True: debugfile.write(rights + '\n\n')
##        for pair in rights.split(';'):
##            try:
##                key, value = pair.split('=',1)
##                self.fileopen[key] = value
##            # fix for some misconfigured INFO variables
##            except:
##                pass
##        kattr = { 'SVID': 'ServiceID', 'DUID': 'DocumentID', 'I3ID': 'Ident3ID', \
##                  'I4ID': 'Ident4ID', 'VERS': 'EncrVer', 'PRID': 'USR'}
##        for keys in  kattr:
##            try:
##                self.fileopen[kattr[keys]] = self.fileopen[keys]
##                del self.fileopen[keys]
##            except:
##                continue
        # differentiate OS types
##        sysplatform = sys.platform
##        # if ostype is Windows
##        if sysplatform=='win32':
##            self.osuseragent = 'Windows NT 6.0'
##            self.get_macaddress = self.get_win_macaddress
##            self.fo_sethwids = self.fo_win_sethwids
##            self.BrowserCookie = WinBrowserCookie
##        elif sysplatform=='linux2':
##            adeptout = 'Linux is not supported, yet.\n'
##            raise ADEPTError(adeptout)
##            self.osuseragent = 'Linux i686'
##            self.get_macaddress = self.get_linux_macaddress
##            self.fo_sethwids = self.fo_linux_sethwids
##        else:
##            adeptout = ''
##            adeptout = adeptout + 'Due to various privacy violations from Apple\n'
##            adeptout = adeptout + 'Mac OS X support is disabled by default.'
##            raise ADEPTError(adeptout)
##        # add static arguments for http/https request
##        self.fo_setattributes()
##        # add hardware specific arguments for http/https request
##        self.fo_sethwids()
##
##        if 'Code' in self.urlresult:
##            if self.fileopen['Length'] == len(self.urlresult['Code']):
##                self.decrypt_key = self.urlresult['Code']
##            else:
##                self.decrypt_key = self.urlresult['Code'].decode('hex')
##        else:
##            raise ADEPTError('Cannot find decryption key.')
        self.decrypt_key = 'stuff'
        self.genkey = self.genkey_v2
        self.decipher = self.decrypt_rc4
        self.ready = True
        return

    def initialize_fopn(self, docid, param):
        # debug mode processing
        global DEBUG_MODE
        global IVERSION
        if DEBUG_MODE == True:
            if os.access('.',os.W_OK) == True:
                debugfile = open('ineptpdf-'+IVERSION+'-debug.txt','w')
            else:
                raise ADEPTError('Cannot write debug file, current directory is not writable')
        self.is_printable = self.is_modifiable = self.is_extractable = True
        # get parameters and add it to the fo dictionary
        self.fileopen['Length'] = int_value(param.get('Length', 0)) / 8
        self.fileopen['VEID'] = str_value(param.get('VEID'))
        self.fileopen['BUILD'] = str_value(param.get('BUILD'))
        self.fileopen['SVID'] = str_value(param.get('SVID'))
        self.fileopen['DUID'] = str_value(param.get('DUID'))
        self.fileopen['V'] = int_value(param.get('V',2))
        # crypt base
        rights = str_value(param.get('INFO')).decode('base64')
        rights = self.genkey_fileopeninfo(rights)
        if DEBUG_MODE == True: debugfile.write(rights + '\n\n')
        for pair in rights.split(';'):
            try:
                key, value = pair.split('=',1)
                self.fileopen[key] = value
            # fix for some misconfigured INFO variables
            except:
                pass
        kattr = { 'SVID': 'ServiceID', 'DUID': 'DocumentID', 'I3ID': 'Ident3ID', \
                  'I4ID': 'Ident4ID', 'VERS': 'EncrVer', 'PRID': 'USR'}
        for keys in  kattr:
            # fishing some misconfigured slashs out of it
            try:
                self.fileopen[kattr[keys]] = urllib.quote(self.fileopen[keys],safe='')
                del self.fileopen[keys]
            except:
                continue
        # differentiate OS types
        sysplatform = sys.platform
        # if ostype is Windows
        if sysplatform=='win32':
            self.osuseragent = 'Windows NT 6.0'
            self.get_macaddress = self.get_win_macaddress
            self.fo_sethwids = self.fo_win_sethwids
            self.BrowserCookie = WinBrowserCookie
        elif sysplatform=='linux2':
            adeptout = 'Linux is not supported, yet.\n'
            raise ADEPTError(adeptout)
            self.osuseragent = 'Linux i686'
            self.get_macaddress = self.get_linux_macaddress
            self.fo_sethwids = self.fo_linux_sethwids
        else:
            adeptout = ''
            adeptout = adeptout + 'Mac OS X is not supported, yet.'
            adeptout = adeptout + 'Read the blogs FAQs for more information'
            raise ADEPTError(adeptout)
        # add static arguments for http/https request
        self.fo_setattributes()
        # add hardware specific arguments for http/https request
        self.fo_sethwids()
        #if DEBUG_MODE == True: debugfile.write(self.fileopen)
        if 'UURL' in self.fileopen:
            buildurl = self.fileopen['UURL']
        else:
            buildurl = self.fileopen['PURL']
        # fix for bad DPRM structure
        if self.fileopen['DPRM'][0] != r'/':
            self.fileopen['DPRM'] = r'/' + self.fileopen['DPRM']
        # genius fix for bad server urls (IMHO)
        if '?' in self.fileopen['DPRM']:
            buildurl = buildurl + self.fileopen['DPRM'] + '&'
        else:
            buildurl = buildurl + self.fileopen['DPRM'] + '?'

        # debug customization
        #self.fileopen['Machine'] = ''
        #self.fileopen['Disk'] = ''


        surl = ( 'Stamp', 'Mode', 'USR', 'ServiceID', 'DocumentID',\
                 'Ident3ID', 'Ident4ID','DocStrFmt', 'OSType', 'OSName', 'OSData', 'Language',\
                 'LngLCID', 'LngRFC1766', 'LngISO4Char', 'Build', 'ProdVer', 'EncrVer',\
                 'Machine', 'Disk', 'Uuid', 'PrevMach', 'PrevDisk',\
                 'FormHFT',\
                 'SelServer', 'AcroVersion', 'AcroProduct', 'AcroReader',\
                 'AcroCanEdit', 'AcroPrefIDib', 'InBrowser', 'CliAppName',\
                 'DocIsLocal', 'DocPathUrl', 'VolName', 'VolType', 'VolSN',\
                 'FSName',  'FowpKbd', 'OSBuild',\
                  'RequestSchema')

        #settings request and special modes
        if 'EVER' in self.fileopen and float(self.fileopen['EVER']) < 3.8:
            self.fileopen['Mode'] = 'ICx'

        origurl = buildurl
        buildurl = buildurl + 'Request=Setting'
        for keys in surl:
            try:
                buildurl = buildurl + '&' + keys + '=' + self.fileopen[keys]
            except:
                continue
        if DEBUG_MODE == True: debugfile.write( 'settings url:\n')
        if DEBUG_MODE == True: debugfile.write( buildurl+'\n\n')
        # custom user agent identification?
        if 'AGEN' in self.fileopen:
            useragent = self.fileopen['AGEN']
            urllib.URLopener.version = useragent
        # attribute doesn't exist - take the default user agent
        else:
            urllib.URLopener.version = self.osuseragent
        # try to open the url
        try:
            u = urllib.urlopen(buildurl)
            u.geturl()
            result = u.read()
        except:
            raise ADEPTError('No internet connection or a blocking firewall!')
##        finally:
##            u.close()
        # getting rid of the line feed
        if DEBUG_MODE == True: debugfile.write('Settings'+'\n')
        if DEBUG_MODE == True: debugfile.write(result+'\n\n')
        #get rid of unnecessary characters
        result = result.rstrip('\n')
        result = result.rstrip(chr(13))
        result = result.lstrip('\n')
        result = result.lstrip(chr(13))
        self.surlresult = {}
        for pair in result.split('&'):
            try:
                key, value = pair.split('=',1)
                # fix for bad server response
                if key not in self.surlresult:
                    self.surlresult[key] = value
            except:
                pass
        if 'RequestSchema' in self.surlresult:
            self.fileopen['RequestSchema'] = self.surlresult['RequestSchema']
        if 'ServerSessionData' in self.surlresult:
            self.fileopen['ServerSessionData'] = self.surlresult['ServerSessionData']
        if 'SetScope' in self.surlresult:
            self.fileopen['RequestSchema'] = self.surlresult['SetScope']
        #print self.surlresult
        if 'RetVal' in self.surlresult and 'SEMO' not in self.fileopen and(('Reason' in self.surlresult and \
           self.surlresult['Reason'] == 'AskUnp') or ('SetTarget' in self.surlresult and\
                                               self.surlresult['SetTarget'] == 'UnpDlg')):
            # get user and password dialog
            try:
                self.gen_pw_dialog(self.surlresult['UnpUiName'], self.surlresult['UnpUiPass'],\
                                   self.surlresult['UnpUiTitle'], self.surlresult['UnpUiOk'],\
                                   self.surlresult['UnpUiSunk'], self.surlresult['UnpUiComm'])
            except:
                self.gen_pw_dialog()

        # the fileopen check might not be always right because of strange server responses
        if 'SEMO' in self.fileopen and (self.fileopen['SEMO'] == '1'\
            or self.fileopen['SEMO'] == '2') and ('CSES' in self.fileopen and\
                                                  self.fileopen['CSES'] != 'fileopen'):
            # get the url name for the cookie(s)
            if 'CURL' in self.fileopen:
                self.surl = self.fileopen['CURL']
            if 'CSES' in self.fileopen:
                self.cses = self.fileopen['CSES']
            elif 'PHOS' in self.fileopen:
                self.surl = self.fileopen['PHOS']
            elif 'LHOS' in self.fileopen:
                self.surl = self.fileopen['LHOS']
            else:
                raise ADEPTError('unknown Cookie name.\n Check ineptpdf forum for further assistance')
            self.pwfieldreq = 1
            # session cookie processing
            if self.fileopen['SEMO'] == '1':
                cookies = self.BrowserCookie()
                #print self.cses
                #print self.surl
                csession = cookies.getcookie(self.cses,self.surl)
                if csession != None:
                    self.fileopen['Session'] = csession
                    self.gui = False
                # fallback
                else:
                    self.pwtk = Tkinter.Tk()
                    self.pwtk.title('Ineptpdf8')
                    self.pwtk.minsize(150, 0)
                    infotxt1 = 'Get the session cookie key manually (Firefox step-by-step:\n'+\
                               'Start Firefox -> Tools -> Options -> Privacy -> Show Cookies\n'+\
                               '-> Search for a cookie from ' + self.surl +' with the\n'+\
                               'name ' + self.cses +' and copy paste the content field in the\n'+\
                               'Session Content field. Remove possible spaces or new lines at the '+\
                               'end\n (cursor must be blinking right behind the last character)'
                    self.label0 = Tkinter.Label(self.pwtk, text=infotxt1)
                    self.label0.pack()
                    self.label1 = Tkinter.Label(self.pwtk, text="Session Content")
                    self.pwfieldreq = 0
                    self.gui = True
            # user cookie processing
            elif self.fileopen['SEMO'] == '2':
                cookies = self.BrowserCookie()
                #print self.cses
                #print self.surl
                name = cookies.getcookie('name',self.surl)
                passw = cookies.getcookie('pass',self.surl)
                if name != None or passw != None:
                    self.fileopen['UserName'] = urllib.quote(name)
                    self.fileopen['UserPass'] = urllib.quote(passw)
                    self.gui = False
                # fallback
                else:
                    self.pwtk = Tkinter.Tk()
                    self.pwtk.title('Ineptpdf8')
                    self.pwtk.minsize(150, 0)
                    self.label1 = Tkinter.Label(self.pwtk, text="Username")
                    infotxt1 = 'Get the user cookie keys manually (Firefox step-by-step:\n'+\
                               'Start Firefox -> Tools -> Options -> Privacy -> Show Cookies\n'+\
                               '-> Search for cookies from ' + self.surl +' with the\n'+\
                               'name name in the user field and copy paste the content field in the\n'+\
                               'username field. Do the same with the name pass in the password field).'
                    self.label0 = Tkinter.Label(self.pwtk, text=infotxt1)
                    self.label0.pack()
                    self.pwfieldreq = 1
                    self.gui = True
##            else:
##                self.pwtk = Tkinter.Tk()
##                self.pwtk.title('Ineptpdf8')
##                self.pwtk.minsize(150, 0)
##                self.pwfieldreq = 0
##                self.label1 = Tkinter.Label(self.pwtk, text="Username")
##                self.pwfieldreq = 1
##                self.gui = True
            if self.gui == True:
                self.un_entry = Tkinter.Entry(self.pwtk)
                # cursor here
                self.un_entry.focus()
                self.label2 = Tkinter.Label(self.pwtk, text="Password")
                self.pw_entry = Tkinter.Entry(self.pwtk, show="*")
                self.button = Tkinter.Button(self.pwtk, text='Go for it!', command=self.fo_save_values)
                # widget layout, stack vertical
                self.label1.pack()
                self.un_entry.pack()
                # create a password label and field
                if self.pwfieldreq == 1:
                    self.label2.pack()
                    self.pw_entry.pack()
                self.button.pack()
                self.pwtk.update()
                # start the event loop
                self.pwtk.mainloop()

        # original request
        # drive through tupple for building the permission url
        burl = ( 'Stamp', 'Mode', 'USR', 'ServiceID', 'DocumentID',\
                 'Ident3ID', 'Ident4ID','DocStrFmt', 'OSType', 'Language',\
                 'LngLCID', 'LngRFC1766', 'LngISO4Char', 'Build', 'ProdVer', 'EncrVer',\
                 'Machine', 'Disk', 'Uuid', 'PrevMach', 'PrevDisk', 'User', 'SaUser', 'SaSID',\
                 # special security measures
                 'HostIsDomain', 'PhysHostname', 'LogiHostname', 'SaRefDomain',\
                 'FormHFT', 'UserName', 'UserPass', 'Session', \
                 'SelServer', 'AcroVersion', 'AcroProduct', 'AcroReader',\
                 'AcroCanEdit', 'AcroPrefIDib', 'InBrowser', 'CliAppName',\
                 'DocIsLocal', 'DocPathUrl', 'VolName', 'VolType', 'VolSN',\
                 'FSName', 'ServerSessionData', 'FowpKbd', 'OSBuild', \
                 'DocumentSessionData', 'RequestSchema')

        buildurl = origurl
        buildurl = buildurl + 'Request=DocPerm'
        for keys in burl:
            try:
                buildurl = buildurl + '&' + keys + '=' + self.fileopen[keys]
            except:
                continue
        if DEBUG_MODE == True: debugfile.write('1st url:'+'\n')
        if DEBUG_MODE == True: debugfile.write(buildurl+'\n\n')
        # custom user agent identification?
        if 'AGEN' in self.fileopen:
            useragent = self.fileopen['AGEN']
            urllib.URLopener.version = useragent
        # attribute doesn't exist - take the default user agent
        else:
            urllib.URLopener.version = self.osuseragent
        # try to open the url
        try:
            u = urllib.urlopen(buildurl)
            u.geturl()
            result = u.read()
        except:
            raise ADEPTError('No internet connection or a blocking firewall!')
##        finally:
##            u.close()
        # getting rid of the line feed
        if DEBUG_MODE == True: debugfile.write('1st preresult'+'\n')
        if DEBUG_MODE == True: debugfile.write(result+'\n\n')
        #get rid of unnecessary characters
        result = result.rstrip('\n')
        result = result.rstrip(chr(13))
        result = result.lstrip('\n')
        result = result.lstrip(chr(13))
        self.urlresult = {}
        for pair in result.split('&'):
            try:
                key, value = pair.split('=',1)
                self.urlresult[key] = value
            except:
                pass
##        if 'RequestSchema' in self.surlresult:
##            self.fileopen['RequestSchema'] = self.urlresult['RequestSchema']
         #self.urlresult
        #result[0:8] == 'RetVal=1') or (result[0:8] == 'RetVal=2'):
        if ('RetVal' in self.urlresult and (self.urlresult['RetVal'] != '1' and \
                                            self.urlresult['RetVal'] != '2' and \
                                            self.urlresult['RetVal'] != 'Update' and \
                                            self.urlresult['RetVal'] != 'Answer')):

            if ('Reason' in self.urlresult and (self.urlresult['Reason'] == 'BadUserPwd'\
                or self.urlresult['Reason'] == 'AskUnp')) or ('SwitchTo' in self.urlresult\
                    and (self.urlresult['SwitchTo'] == 'Dialog')):
                if 'ServerSessionData' in self.urlresult:
                    self.fileopen['ServerSessionData'] = self.urlresult['ServerSessionData']
                if 'DocumentSessionData' in self.urlresult:
                    self.fileopen['DocumentSessionData'] = self.urlresult['DocumentSessionData']
                buildurl = origurl
                buildurl = buildurl + 'Request=DocPerm'
                self.gen_pw_dialog()
                # password not found - fallback
                for keys in burl:
                    try:
                        buildurl = buildurl + '&' + keys + '=' + self.fileopen[keys]
                    except:
                        continue
                if DEBUG_MODE == True: debugfile.write( '2ndurl:')
                if DEBUG_MODE == True: debugfile.write( buildurl+'\n\n')
                # try to open the url
                try:
                    u = urllib.urlopen(buildurl)
                    u.geturl()
                    result = u.read()
                except:
                    raise ADEPTError('No internet connection or a blocking firewall!')
                # getting rid of the line feed
                if DEBUG_MODE == True: debugfile.write( '2nd preresult')
                if DEBUG_MODE == True: debugfile.write( result+'\n\n')
                #get rid of unnecessary characters
                result = result.rstrip('\n')
                result = result.rstrip(chr(13))
                result = result.lstrip('\n')
                result = result.lstrip(chr(13))
                self.urlresult = {}
                for pair in result.split('&'):
                    try:
                        key, value = pair.split('=',1)
                        self.urlresult[key] = value
                    except:
                        pass
        # did it work?
        if ('RetVal' in self.urlresult and (self.urlresult['RetVal'] != '1' and \
                                                    self.urlresult['RetVal'] != '2' and
                                                    self.urlresult['RetVal'] != 'Update' and \
                                                    self.urlresult['RetVal'] != 'Answer')):
            raise ADEPTError('Decryption was not successfull.\nReason: ' + self.urlresult['Error'])
        # fix for non-standard-conform fileopen pdfs
##        if self.fileopen['Length'] != 5 and self.fileopen['Length'] != 16:
##            if self.fileopen['V'] == 1:
##                self.fileopen['Length'] = 5
##            else:
##                self.fileopen['Length'] = 16
        # patch for malformed pdfs
        #print len(self.urlresult['Code'])
        #print self.urlresult['Code'].encode('hex')
        if 'code' in self.urlresult:
            self.urlresult['Code'] = self.urlresult['code']
        if 'Code' in self.urlresult:
            if len(self.urlresult['Code']) == 5 or len(self.urlresult['Code']) == 16:
                self.decrypt_key = self.urlresult['Code']
            else:
                self.decrypt_key = self.urlresult['Code'].decode('hex')
        else:
            raise ADEPTError('Cannot find decryption key.')
        


        V = int_value(param.get('V',2))
        R = int_value(param.get('R'))


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

    def gen_pw_dialog(self, Username='Username', Password='Password', Title='User/Password Authentication',\
                      OK='Proceed', Text1='Authorization', Text2='Enter Required Data'):
        self.pwtk = Tkinter.Tk()
        self.pwtk.title(Title)
        self.pwtk.minsize(150, 0)
        self.label1 = Tkinter.Label(self.pwtk, text=Text1)
        self.label2 = Tkinter.Label(self.pwtk, text=Text2)
        self.label3 = Tkinter.Label(self.pwtk, text=Username)
        self.pwfieldreq = 1
        self.gui = True
        self.un_entry = Tkinter.Entry(self.pwtk)
        # cursor here
        self.un_entry.focus()
        self.label4 = Tkinter.Label(self.pwtk, text=Password)
        self.pw_entry = Tkinter.Entry(self.pwtk, show="*")
        self.button = Tkinter.Button(self.pwtk, text=OK, command=self.fo_save_values)
        # widget layout, stack vertical
        self.label1.pack()
        self.label2.pack()
        self.label3.pack()
        self.un_entry.pack()
        # create a password label and field
        if self.pwfieldreq == 1:
            self.label4.pack()
            self.pw_entry.pack()
        self.button.pack()
        self.pwtk.update()
        # start the event loop
        self.pwtk.mainloop()

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
        if sys.version_info[0] == 2: 
            cutter = -1 * ord(plaintext[-1])
        else: 
            cutter = -1 * plaintext[-1]

        plaintext = plaintext[:cutter]
        return plaintext

    def decrypt_rc4(self, objid, genno, data):
        key = self.genkey(objid, genno)
        return ARC4.new(key).decrypt(data)

    # fileopen user/password dialog
    def fo_save_values(self):
        getout = 0
        username = 0
        password = 0
        username = self.un_entry.get()
        if self.pwfieldreq == 1:
            password = self.pw_entry.get()
        un_length = len(username)
        if self.pwfieldreq == 1:
            pw_length = len(password)
        if (un_length != 0):
            if self.pwfieldreq == 1:
                if (pw_length != 0):
                    getout = 1
            else:
                getout = 1
        if getout == 1:
            if 'SEMO' in self.fileopen and self.fileopen['SEMO'] == '1':
                self.fileopen['Session'] = urllib.quote(username)
            else:
                self.fileopen['UserName'] = urllib.quote(username)
            if self.pwfieldreq == 1:
                self.fileopen['UserPass'] = urllib.quote(password)
            else:
                pass
                #self.fileopen['UserPass'] = self.fileopen['UserName']
            # doesn't always close the password window, who
            # knows why (Tkinter secrets ;=))
            self.pwtk.quit()


    def fo_setattributes(self):
        self.fileopen['Request']='DocPerm'
        self.fileopen['Mode']='CNR'
        self.fileopen['DocStrFmt']='ASCII'
        self.fileopen['Language']='ENU'
        self.fileopen['LngLCID']='ENU'
        self.fileopen['LngRFC1766']='en'
        self.fileopen['LngISO4Char']='en-us'
        self.fileopen['ProdVer']='1.8.7.9'
        self.fileopen['FormHFT']='Yes'
        self.fileopen['SelServer']='Yes'
        self.fileopen['AcroCanEdit']='Yes'
        self.fileopen['AcroPrefIDib']='Yes'
        self.fileopen['InBrowser']='Unk'
        self.fileopen['CliAppName']=''
        self.fileopen['DocIsLocal']='Yes'
        self.fileopen['FowpKbd']='Yes'
        self.fileopen['RequestSchema']='Default'

    # get nic mac address
    def get_linux_macaddress(self):
        try:
            for line in os.popen("/sbin/ifconfig"):
                if line.find('Ether') > -1:
                    mac = line.split()[4]
                    break
            return mac.replace(':','')
        except:
            raise ADEPTError('Cannot find MAC address. Get forum help.')

    def get_win_macaddress(self):
        try:
            gasize = c_ulong(5000)
            p = create_string_buffer(5000)
            GetAdaptersInfo = windll.iphlpapi.GetAdaptersInfo
            GetAdaptersInfo(byref(p),byref(gasize))
            return p[0x194:0x19a].encode('hex')
        except:
            raise ADEPTError('Cannot find MAC address. Get forum help.')

    # custom conversion 5 bytes to 8 chars method
    def fo_convert5to8(self, edisk):
        # byte to number/char mapping table
        darray=[0x32,0x33,0x34,0x35,0x36,0x37,0x38,0x39,0x41,0x42,0x43,0x44,0x45,\
                0x46,0x47,0x48,0x4A,0x4B,0x4C,0x4D,0x4E,0x50,0x51,0x52,0x53,0x54,\
                0x55,0x56,0x57,0x58,0x59,0x5A]
        pdid = struct.pack('<I', int(edisk[0:4].encode("hex"),16))
        pdid = int(pdid.encode("hex"),16)
        outputhw = ''
        # disk id processing
        for i in range(0,6):
            index = pdid & 0x1f
            # shift the disk id 5 bits to the right
            pdid = pdid >> 5
            outputhw = outputhw + chr(darray[index])
        pdid = (ord(edisk[4]) << 2)|pdid
        # get the last 2 bits from the hwid + low part of the cpuid
        for i in range(0,2):
            index = pdid & 0x1f
            # shift the disk id 5 bits to the right
            pdid = pdid >> 5
            outputhw = outputhw + chr(darray[index])
        return outputhw

    # Linux processing
    def fo_linux_sethwids(self):
        # linux specific attributes
        self.fileopen['OSType']='Linux'
        self.fileopen['AcroProduct']='AcroReader'
        self.fileopen['AcroReader']='Yes'
        self.fileopen['AcroVersion']='9.101'
        self.fileopen['FSName']='ext3'
        self.fileopen['Build']='878'
        self.fileopen['ProdVer']='1.8.5.1'
        self.fileopen['OSBuild']='2.6.33'
        # write hardware keys
        hwkey = 0
        pmac = self.get_macaddress().decode("hex");
        self.fileopen['Disk'] = self.fo_convert5to8(pmac[1:])
        # get primary used default mac address
        self.fileopen['Machine'] = self.fo_convert5to8(pmac[1:])
        # get uuid
        # check for reversed offline handler 6AB83F4Ah + AFh 6AB83F4Ah
        if 'LILA' in self.fileopen:
            pass
        if 'Ident4ID' in self.fileopen:
            self.fileopen['User'] = getpass.getuser()
            self.fileopen['SaUser'] = getpass.getuser()
            try:
                cuser = winreg.HKEY_CURRENT_USER
                FOW3_UUID = 'Software\\Fileopen'
                regkey = winreg.OpenKey(cuser, FOW3_UUID)
                userkey = winreg.QueryValueEx(regkey, 'Fowp3Uuid')[0]
#                if self.genkey_cryptmach(userkey)[0:4] != 'ec20':
                self.fileopen['Uuid'] = self.genkey_cryptmach(userkey)[4:]
##                elif self.genkey_cryptmach(userkey)[0:4] != 'ec20':
##                    self.fileopen['Uuid'] = self.genkey_cryptmach(userkey,1)[4:]
##                else:
            except:
                raise ADEPTError('Cannot find FowP3Uuid file - reason might be Adobe (Reader) X.'\
                                 'Read the FAQs for more information how to solve the problem.')
        else:
            self.fileopen['Uuid'] = str(uuid.uuid1())
        # get time stamp
        self.fileopen['Stamp'] = str(time.time())[:-3]
        # get fileopen input pdf name + path
        self.fileopen['DocPathUrl'] = 'file%3a%2f%2f%2f'\
                                      + urllib.quote(os.path.normpath(INPUTFILEPATH))
        # clear the link
        #INPUTFILEPATH = ''
##        # get volume name (urllib quote necessairy?) urllib.quote(
##        self.fileopen['VolName'] = win32api.GetVolumeInformation("C:\\")[0]
##        # get volume serial number
##        self.fileopen['VolSN'] = str(win32api.GetVolumeInformation("C:\\")[1])
        return

    # Windows processing
    def fo_win_sethwids(self):
        # Windows specific attributes
        self.fileopen['OSType']='Windows'
        self.fileopen['OSName']='Vista'
        self.fileopen['OSData']='Service%20Pack%204'
        self.fileopen['AcroProduct']='Reader'
        self.fileopen['AcroReader']='Yes'
        self.fileopen['OSBuild']='7600'
        self.fileopen['AcroVersion']='9.1024'
        self.fileopen['Build']='879'
        # write hardware keys
        hwkey = 0
        # get the os type and save it in ostype
        try:
            import win32api
            import win32security
            import win32file
        except:
            raise ADEPTError('PyWin Extension (Win32API module) needed.\n'+\
                             'Download from http://sourceforge.net/projects/pywin32/files/ ')
        try:
            import winreg
        except ImportError:
            import _winreg as winreg
        try:
            v0 = win32api.GetVolumeInformation('C:\\')
            v1 = win32api.GetSystemInfo()[6]
            # fix for possible negative integer (Python problem)
            volserial = v0[1] & 0xffffffff
            lowcpu = v1 & 255
            highcpu = (v1 >> 8) & 255
            # changed to int
            volserial = struct.pack('<I', int(volserial))
            lowcpu   = struct.pack('B', lowcpu)
            highcpu = struct.pack('B', highcpu)
            encrypteddisk = volserial + lowcpu + highcpu
            self.fileopen['Disk'] = self.fo_convert5to8(encrypteddisk)
        except:
            # no c system drive available empty disk attribute
            self.fileopen['Disk'] = ''
        # get primary used default mac address
        pmac = self.get_macaddress().decode("hex");
        self.fileopen['Machine'] = self.fo_convert5to8(pmac[1:])
        if 'LIFF' in self.fileopen:
            if 'Yes' in self.fileopen['LIFF']:
                hostname = socket.gethostname()
                self.fileopen['HostIsDomain']='Yes'
                if '1' in self.fileopen['LIFF']:
                    self.fileopen['PhysHostname']= hostname
                    self.fileopen['LogiHostname']= hostname
                    self.fileopen['SaRefDomain']= hostname
        # default users
        self.user = win32api.GetUserName().lower()
        self.sauser = win32api.GetUserName()
        # get uuid
        # check for reversed offline handler
        if 'LILA' in self.fileopen and self.fileopen['LILA'] == 'Yes':
##            self.fileopen['User'] = win32api.GetUserName().lower()
##            self.fileopen['SaUser'] = win32api.GetUserName()

            # get sid / sasid
            try:
                psid = win32security.LookupAccountName("",self.sauser)[0]
                psid = win32security.ConvertSidToStringSid(psid)
                self.fileopen['SaSID'] = psid
                self.fileopen['User'] = urllib.quote(self.user)
                self.fileopen['SaUser'] = urllib.quote(self.sauser)
            # didn't work use a generic one
            except:
                self.fileopen['SaSID'] = 'S-1-5-21-1380067357-584463869-1343024091-1000'
        #if 'Ident4d' in self.fileopen or 'LILA' in self.fileopen:
        # always calculate the right uuid
        userkey = []
        try:
            cuser = winreg.HKEY_CURRENT_USER
            FOW3_UUID = 'Software\\Fileopen'
            regkey = winreg.OpenKey(cuser, FOW3_UUID)
            userkey.append(winreg.QueryValueEx(regkey, 'Fowp3Uuid')[0])
        except:
            pass
        try:
            fopath = os.environ['AppData']+'\\FileOpen\\'
            fofilename = 'Fowpmadi.txt'
            f = open(fopath+fofilename, 'rb')
            userkey.append(f.read()[0:40])
            f.close()
        except:
            pass
        if not userkey:
            raise ADEPTError('Cannot find FowP3Uuid in registry or file.\n'\
                                 +'Did Adobe (Reader) open the pdf file?')
        cresult = self.genkey_cryptmach(userkey)
        if cresult != False:
            self.fileopen['Uuid'] = cresult
        # kind of a long shot we'll see about it
        else:
            self.fileopen['Uuid'] = str(uuid.uuid1())
##        else:
##            self.fileopen['Uuid'] = str(uuid.uuid1())
        # get time stamp
        self.fileopen['Stamp'] = str(time.time())[:-3]
        # get fileopen input pdf name + path
        # print INPUTFILEPATH
        self.fileopen['DocPathUrl'] = 'file%3a%2f%2f%2f'\
                                      + urllib.quote(INPUTFILEPATH)
        # determine voltype
        voltype = ('Unknown', 'Invalid', 'Removable', 'Fixed', 'Remote', 'CDRom', 'RamDisk')
        dletter = os.path.splitdrive(INPUTFILEPATH)[0] + '\\'
        self.fileopen['VolType'] = voltype[win32file.GetDriveType(dletter)]
        # get volume name (urllib quote necessairy?) urllib.quote(
        self.fileopen['VolName'] = urllib.quote(win32api.GetVolumeInformation(dletter)[0])
        # get volume serial number (fix for possible negative numbers)
        self.fileopen['VolSN'] = str(win32api.GetVolumeInformation(dletter)[1])
        # no c volume so skip it
        self.fileopen['FSName'] = win32api.GetVolumeInformation(dletter)[4]
        # get previous mac address or disk handling
        userkey = []
        try:
            cuser = winreg.HKEY_CURRENT_USER
            FOW3_UUID = 'Software\\Fileopen'
            regkey = winreg.OpenKey(cuser, FOW3_UUID)
            userkey.append(winreg.QueryValueEx(regkey, 'Fowp3Madi')[0])
        except:
            pass
        try:
            fopath = os.environ['AppData']+'\\FileOpen\\'
            fofilename = 'Fowpmadi.txt'
            f = open(fopath+fofilename, 'rb')
            userkey.append(f.read()[40:])
            f.close()
        except:
            pass
        if not userkey:
            raise ADEPTError('Cannot find FowP3Madi in registry or file.\n'\
                             +'Did Adobe Reader open the pdf file?')
        cresult = self.genkey_cryptmach(userkey)
        if cresult != False:
            machdisk = self.genkey_cryptmach(userkey)
            machine = machdisk[:8]
            disk = machdisk[8:]
        # did not find the required information, false it
        else:
            machdisk = False
            machine = False
            disk = False
        if machine != self.fileopen['Machine'] and machdisk != False:
            self.fileopen['PrevMach'] = machine
        if disk != self.fileopen['Disk'] and machdisk != False:
            self.fileopen['PrevDisk'] = disk
        return

    # decryption routine for the INFO area
    def genkey_fileopeninfo(self, data):
        input1 = struct.pack('L', 0xa4da49de)
        seed   = struct.pack('B', 0x82)
        key = input1[3] + input1[2] +input1[1] +input1[0] + seed
        hash = hashlib.md5()
        key = hash.update(key)
        spointer4 = struct.pack('<L', 0xec8d6c58)
        seed = struct.pack('B', 0x07)
        key = spointer4[3] + spointer4[2] + spointer4[1] + spointer4[0] + seed
        key = hash.update(key)
        md5 = hash.digest()
        key = md5[0:10]
        return ARC4.new(key).decrypt(data)

    def genkey_cryptmach(self, data):
        # nested subfunction
        def genkeysub(uname, mode=False):
            key_string = '37A4DA49DE82064939A60B1D8D7B5F0F8873B6D93E'.decode('hex')
            m = hashlib.md5()
            m.update(key_string[:3])
            m.update(uname[:13]) # max 13 characters 13 - sizeof(username)
            if (13 - len(uname)) > 0 and mode == True:
                m.update(key_string[:(13-len(uname))])
            md5sum = m.digest()[0:16]
            # print md5sum.encode('hex')
            # normal ident4id calculation
            retval = []
            for sdata in data:
                retval.append(ARC4.new(md5sum).decrypt(sdata))
            for rval in retval:
                if rval[:4] == 'ec20':
                    return rval[4:]
            return False
        # start normal execution
        # list for username variants
        unamevars = []
        # fill username variants list
        unamevars.append(self.user)
        unamevars.append(self.user + chr(0))
        unamevars.append(self.user.lower())
        unamevars.append(self.user.lower() + chr(0))
        unamevars.append(self.user.upper())
        unamevars.append(self.user.upper() + chr(0))
        # go through it
        for uname in unamevars:
            result = genkeysub(uname, True)
            if result != False:
              return result
            result = genkeysub(uname)
            if result != False:
              return result
        # didn't find it, return false
        return False
##        raise ADEPTError('Unsupported Ident4D Decryption,\n'+\
##                             'report the bug to the ineptpdf script forum')

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
###
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

# helper class for cookie retrival
class WinBrowserCookie():
    def __init__(self):
        pass
    def getcookie(self, cname, chost):
        # check firefox db
        fprofile =  os.environ['AppData']+r'\Mozilla\Firefox'
        pinifile = 'profiles.ini'
        fini = os.path.normpath(fprofile + '\\' + pinifile)
        try:
            with open(fini,'r') as ffini:
                firefoxini =  ffini.read()
        # Firefox not installed or on an USB stick
        except:
            return None
        for pair in firefoxini.split('\n'):
            try:
                key, value = pair.split('=',1)
                if key == 'Path':
                    fprofile = os.path.normpath(fprofile+'//'+value+'//'+'cookies.sqlite')
                    break
            # asdf
            except:
                continue
        if os.path.isfile(fprofile):
            try:
                con = sqlite3.connect(fprofile,1)
            except:
                raise ADEPTError('Firefox Cookie data base locked. Close Firefox and try again')
            cur = con.cursor()
            try:
                cur.execute("select value from moz_cookies where name=? and host=?", (cname, chost))
            except Exception:
                raise ADEPTError('Firefox Cookie database is locked. Close Firefox and try again')
            try:
                return cur.fetchone()[0]
            except Exception:
                # sometimes is a dot in front of the host
                chost = '.'+chost
                cur.execute("select value from moz_cookies where name=? and host=?", (cname, chost))
                try:
                    return cur.fetchone()[0]
                except:
                    return None

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
            pat = re.compile(br'^(\\d+)\\s+(\\d+)\\s+obj\\b')
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

###
### My own code, for which there is none else to blame

class PDFSerializer(object):
    def __init__(self, inf, keypath):
        global GEN_XREF_STM, gen_xref_stm
        gen_xref_stm = GEN_XREF_STM > 1
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
            data = zlib.compress(''.join(data))
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
            self.write(b'<%s>' % binascii.hexlify(obj).upper())
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

                # Fix length:
                # We've decompressed and then recompressed the PDF stream.
                # Depending on the algorithm, the implementation, and the compression level, 
                # the resulting recompressed stream is unlikely to have the same length as the original.
                # So we need to update the PDF object to contain the new proper length.

                # Without this change, all PDFs exported by this plugin are slightly corrupted - 
                # even though most if not all PDF readers can correct that on-the-fly.

                if 'Length' in obj.dic: 
                    obj.dic['Length'] = len(data)


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
        # hope this will fix the 'bad file descriptor' problem
        with open(outpath, 'wb') as outf:
        # help construct to make sure the method runs to the end
            serializer.dump(outf)
    return 0


class DecryptionDialog(Tkinter.Frame):
    def __init__(self, root):
        # debug mode debugging
        global DEBUG_MODE
        Tkinter.Frame.__init__(self, root, border=5)
        ltext='Select file for decryption\n(Ignore Password / Key file option for Fileopen/APS PDFs)'
        self.status = Tkinter.Label(self, text=ltext)
        self.status.pack(fill=Tkconstants.X, expand=1)
        body = Tkinter.Frame(self)
        body.pack(fill=Tkconstants.X, expand=1)
        sticky = Tkconstants.E + Tkconstants.W
        body.grid_columnconfigure(1, weight=2)
        Tkinter.Label(body, text='Password\nor Key file').grid(row=0)
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
        debugmode = Tkinter.Checkbutton(self, text = "Debug Mode (writable directory required)", command=self.debug_toggle, height=2, \
                 width = 40)
        debugmode.pack()
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
            keypath = os.path.normpath(os.path.realpath(keypath))
            self.keypath.delete(0, Tkconstants.END)
            self.keypath.insert(0, keypath)
        return

    def get_inpath(self):
        inpath = tkFileDialog.askopenfilename(
            parent=None, title='Select ADEPT or FileOpen-encrypted PDF file to decrypt',
            defaultextension='.pdf', filetypes=[('PDF files', '.pdf'),
                                                 ('All files', '.*')])
        if inpath:
            inpath = os.path.normpath(os.path.realpath(inpath))
            self.inpath.delete(0, Tkconstants.END)
            self.inpath.insert(0, inpath)
        return

    def debug_toggle(self):
        global DEBUG_MODE
        if DEBUG_MODE == False:
            DEBUG_MODE = True
        else:
            DEBUG_MODE = False

    def get_outpath(self):
        outpath = tkFileDialog.asksaveasfilename(
            parent=None, title='Select unencrypted PDF file to produce',
            defaultextension='.pdf', filetypes=[('PDF files', '.pdf'),
                                                 ('All files', '.*')])
        if outpath:
            outpath = os.path.normpath(os.path.realpath(outpath))
            self.outpath.delete(0, Tkconstants.END)
            self.outpath.insert(0, outpath)
        return

    def decrypt(self):
        global INPUTFILEPATH
        global KEYFILEPATH
        global PASSWORD
        keypath = self.keypath.get()
        inpath = self.inpath.get()
        outpath = self.outpath.get()
        if not keypath or not os.path.exists(keypath):
            # keyfile doesn't exist
            KEYFILEPATH = False
            PASSWORD = keypath
        if not inpath or not os.path.exists(inpath):
            self.status['text'] = 'Specified input file does not exist'
            return
        if not outpath:
            self.status['text'] = 'Output file not specified'
            return
        if inpath == outpath:
            self.status['text'] = 'Must have different input and output files'
            return
        # patch for non-ascii characters
        INPUTFILEPATH = inpath.encode('utf-8')
        argv = [sys.argv[0], keypath, inpath, outpath]
        self.status['text'] = 'Processing ...'
        try:
            cli_main(argv)
        except Exception, a:
            self.status['text'] = 'Error: ' + str(a)
            return
        self.status['text'] = 'File successfully decrypted.\n'+\
                              'Close this window or decrypt another pdf file.'
        return

def gui_main():
    root = Tkinter.Tk()
    if RSA is None:
        root.withdraw()
        tkMessageBox.showerror(
            "PDF FileOpen Decrypter",
            "This script requires PyCrypto, which must be installed "
            "separately.  Read the top-of-script comment for details.")
        return 1
    root.title('FileOpen PDF Decrypter 8.5.0')
    root.resizable(True, False)
    root.minsize(370, 0)
    DecryptionDialog(root).pack(fill=Tkconstants.X, expand=1)
    root.mainloop()
    return 0


if __name__ == '__main__':
    if len(sys.argv) > 1:
        sys.exit(cli_main())
    sys.exit(gui_main())
