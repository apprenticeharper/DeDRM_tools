#!/usr/bin/python
#
# This is a python script. You need a Python interpreter to run it.
# For example, ActiveState Python, which exists for windows.
#
# Changelog drmcheck
#  1.00 - Initial version, with code from various other scripts
#  1.01 - Moved authorship announcement to usage section.
#
# Changelog epubtest
#  1.00 - Cut to epubtest.py, testing ePub files only by Apprentice Alf
#  1.01 - Added routine for use by Windows DeDRM
#
# Written in 2011 by Paul Durrant
# Released with unlicense. See http://unlicense.org/
#
#############################################################################
#
# This is free and unencumbered software released into the public domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
#
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
#############################################################################
#
# It's still polite to give attribution if you do reuse this code.
#

from __future__ import with_statement
from __future__ import print_function

__version__ = '1.01'

import sys, struct, os, traceback
import zlib
import zipfile
import xml.etree.ElementTree as etree

NSMAP = {'adept': 'http://ns.adobe.com/adept',
         'enc': 'http://www.w3.org/2001/04/xmlenc#'}

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
        if isinstance(data,unicode):
            data = data.encode(self.encoding,"replace")
        self.stream.write(data)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

try:
    from calibre.constants import iswindows, isosx
except:
    iswindows = sys.platform.startswith('win')
    isosx = sys.platform.startswith('darwin')

def unicode_argv():
    if iswindows:
        # Uses shell32.GetCommandLineArgvW to get sys.argv as a list of Unicode
        # strings.

        # Versions 2.x of Python don't support Unicode in sys.argv on
        # Windows, with the underlying Windows API instead replacing multi-byte
        # characters with '?'.  So use shell32.GetCommandLineArgvW to get sys.argv
        # as a list of Unicode strings and encode them as utf-8

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
                    xrange(start, argc.value)]
        # if we don't have any arguments at all, just pass back script name
        # this should never happen
        return [u"epubtest.py"]
    else:
        argvencoding = sys.stdin.encoding
        if argvencoding == None:
            argvencoding = "utf-8"
        return [arg if (type(arg) == unicode) else unicode(arg,argvencoding) for arg in sys.argv]

_FILENAME_LEN_OFFSET = 26
_EXTRA_LEN_OFFSET = 28
_FILENAME_OFFSET = 30
_MAX_SIZE = 64 * 1024


def uncompress(cmpdata):
    dc = zlib.decompressobj(-15)
    data = ''
    while len(cmpdata) > 0:
        if len(cmpdata) > _MAX_SIZE :
            newdata = cmpdata[0:_MAX_SIZE]
            cmpdata = cmpdata[_MAX_SIZE:]
        else:
            newdata = cmpdata
            cmpdata = ''
        newdata = dc.decompress(newdata)
        unprocessed = dc.unconsumed_tail
        if len(unprocessed) == 0:
            newdata += dc.flush()
        data += newdata
        cmpdata += unprocessed
        unprocessed = ''
    return data

def getfiledata(file, zi):
    # get file name length and exta data length to find start of file data
    local_header_offset = zi.header_offset

    file.seek(local_header_offset + _FILENAME_LEN_OFFSET)
    leninfo = file.read(2)
    local_name_length, = struct.unpack('<H', leninfo)

    file.seek(local_header_offset + _EXTRA_LEN_OFFSET)
    exinfo = file.read(2)
    extra_field_length, = struct.unpack('<H', exinfo)

    file.seek(local_header_offset + _FILENAME_OFFSET + local_name_length + extra_field_length)
    data = None

    # if not compressed we are good to go
    if zi.compress_type == zipfile.ZIP_STORED:
        data = file.read(zi.file_size)

    # if compressed we must decompress it using zlib
    if zi.compress_type == zipfile.ZIP_DEFLATED:
        cmpdata = file.read(zi.compress_size)
        data = uncompress(cmpdata)

    return data

def encryption(infile):
    # returns encryption: one of Unencrypted, Adobe, B&N and Unknown
    encryption = "Unknown"
    try:
        with open(infile,'rb') as infileobject:
            bookdata = infileobject.read(58)
            # Check for Zip
            if bookdata[0:0+2] == "PK":
                foundrights = False
                foundencryption = False
                inzip = zipfile.ZipFile(infile,'r')
                namelist = set(inzip.namelist())
                if 'META-INF/rights.xml' not in namelist or 'META-INF/encryption.xml' not in namelist:
                    encryption = "Unencrypted"
                else:
                    rights = etree.fromstring(inzip.read('META-INF/rights.xml'))
                    adept = lambda tag: '{%s}%s' % (NSMAP['adept'], tag)
                    expr = './/%s' % (adept('encryptedKey'),)
                    bookkey = ''.join(rights.findtext(expr))
                    if len(bookkey) == 172:
                        encryption = "Adobe"
                    elif len(bookkey) == 64:
                        encryption = "B&N"
                    else:
                        encryption = "Unknown"
    except:
        traceback.print_exc()
    return encryption

def main():
    argv=unicode_argv()
    print(encryption(argv[1]))
    return 0

if __name__ == "__main__":
    sys.stdout=SafeUnbuffered(sys.stdout)
    sys.stderr=SafeUnbuffered(sys.stderr)
    sys.exit(main())
