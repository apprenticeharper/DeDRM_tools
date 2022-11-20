#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
#  2.00 - Python 3, September 2020
#  2.01 - Add new Adobe DRM, add Readium LCP
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

__version__ = '2.0'

import sys, struct, os, traceback
import zlib
import zipfile
import xml.etree.ElementTree as etree
from argv_utils import unicode_argv

NSMAP = {'adept': 'http://ns.adobe.com/adept',
         'enc': 'http://www.w3.org/2001/04/xmlenc#'}

from utilities import SafeUnbuffered


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
    # Supports Adobe (old & new), B&N, Kobo, Apple, Readium LCP.
    encryption = "Error"
    try:
        with open(infile,'rb') as infileobject:
            bookdata = infileobject.read(58)
            # Check for Zip
            if bookdata[0:0+2] == b"PK":
                inzip = zipfile.ZipFile(infile,'r')
                namelist = set(inzip.namelist())
                if (
                    'META-INF/encryption.xml' in namelist and
                    'META-INF/license.lcpl' in namelist and
                    b"EncryptedContentKey" in inzip.read("META-INF/encryption.xml")):
                    encryption = "Readium LCP"

                elif 'META-INF/sinf.xml' in namelist and b"fairplay" in inzip.read("META-INF/sinf.xml"):
                    # Untested, just found this info on Google
                    encryption = "Apple"

                elif 'META-INF/rights.xml' in namelist and b"<kdrm>" in inzip.read("META-INF/rights.xml"):
                    # Untested, just found this info on Google
                    encryption = "Kobo"
                
                elif 'META-INF/rights.xml' not in namelist or 'META-INF/encryption.xml' not in namelist:
                    encryption = "Unencrypted"
                else:
                    try: 
                        rights = etree.fromstring(inzip.read('META-INF/rights.xml'))
                        adept = lambda tag: '{%s}%s' % (NSMAP['adept'], tag)
                        expr = './/%s' % (adept('encryptedKey'),)
                        bookkey = ''.join(rights.findtext(expr))
                        if len(bookkey) >= 172:
                            encryption = "Adobe"
                        elif len(bookkey) == 64:
                            encryption = "B&N"
                        else:
                            encryption = "Unknown (key len " + str(len(bookkey)) + ")"
                    except: 
                        encryption = "Unknown"
    except:
        traceback.print_exc()
    return encryption

def main():
    argv=unicode_argv("epubtest.py")
    if len(argv) < 2:
        print("Give an ePub file as a parameter.")
    else:
        print(encryption(argv[1]))
    return 0

if __name__ == "__main__":
    sys.stdout=SafeUnbuffered(sys.stdout)
    sys.stderr=SafeUnbuffered(sys.stderr)
    sys.exit(main())
