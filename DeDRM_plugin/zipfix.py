#!/usr/bin/env python
# -*- coding: utf-8 -*-

# zipfix.py, version 1.1
# Copyright © 2010-2013 by some_updates, DiapDealer and Apprentice Alf

# Released under the terms of the GNU General Public Licence, version 3
# <http://www.gnu.org/licenses/>

# Revision history:
#   1.0 - Initial release
#   1.1 - Updated to handle zip file metadata correctly

"""
Re-write zip (or ePub) fixing problems with file names (and mimetype entry).
"""
from __future__ import print_function

__license__ = 'GPL v3'
__version__ = "1.1"

import sys
import zlib
import zipfilerugged
import os
import os.path
import getopt
from struct import unpack


_FILENAME_LEN_OFFSET = 26
_EXTRA_LEN_OFFSET = 28
_FILENAME_OFFSET = 30
_MAX_SIZE = 64 * 1024
_MIMETYPE = 'application/epub+zip'

class ZipInfo(zipfilerugged.ZipInfo):
    def __init__(self, *args, **kwargs):
        if 'compress_type' in kwargs:
            compress_type = kwargs.pop('compress_type')
        super(ZipInfo, self).__init__(*args, **kwargs)
        self.compress_type = compress_type

class fixZip:
    def __init__(self, zinput, zoutput):
        self.ztype = 'zip'
        if zinput.lower().find('.epub') >= 0 :
            self.ztype = 'epub'
        self.inzip = zipfilerugged.ZipFile(zinput,'r')
        self.outzip = zipfilerugged.ZipFile(zoutput,'w')
        # open the input zip for reading only as a raw file
        self.bzf = file(zinput,'rb')

    def getlocalname(self, zi):
        local_header_offset = zi.header_offset
        self.bzf.seek(local_header_offset + _FILENAME_LEN_OFFSET)
        leninfo = self.bzf.read(2)
        local_name_length, = unpack('<H', leninfo)
        self.bzf.seek(local_header_offset + _FILENAME_OFFSET)
        local_name = self.bzf.read(local_name_length)
        return local_name

    def uncompress(self, cmpdata):
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

    def getfiledata(self, zi):
        # get file name length and exta data length to find start of file data
        local_header_offset = zi.header_offset

        self.bzf.seek(local_header_offset + _FILENAME_LEN_OFFSET)
        leninfo = self.bzf.read(2)
        local_name_length, = unpack('<H', leninfo)

        self.bzf.seek(local_header_offset + _EXTRA_LEN_OFFSET)
        exinfo = self.bzf.read(2)
        extra_field_length, = unpack('<H', exinfo)

        self.bzf.seek(local_header_offset + _FILENAME_OFFSET + local_name_length + extra_field_length)
        data = None

        # if not compressed we are good to go
        if zi.compress_type == zipfilerugged.ZIP_STORED:
            data = self.bzf.read(zi.file_size)

        # if compressed we must decompress it using zlib
        if zi.compress_type == zipfilerugged.ZIP_DEFLATED:
            cmpdata = self.bzf.read(zi.compress_size)
            data = self.uncompress(cmpdata)

        return data



    def fix(self):
        # get the zipinfo for each member of the input archive
        # and copy member over to output archive
        # if problems exist with local vs central filename, fix them

        # if epub write mimetype file first, with no compression
        if self.ztype == 'epub':
            # first get a ZipInfo with current time and no compression
            mimeinfo = ZipInfo('mimetype',compress_type=zipfilerugged.ZIP_STORED)
            mimeinfo.internal_attr = 1 # text file
            try:
                # if the mimetype is present, get its info, including time-stamp
                oldmimeinfo = self.inzip.getinfo('mimetype')
                # copy across useful fields
                mimeinfo.date_time = oldmimeinfo.date_time
                mimeinfo.comment = oldmimeinfo.comment
                mimeinfo.extra = oldmimeinfo.extra
                mimeinfo.internal_attr = oldmimeinfo.internal_attr
                mimeinfo.external_attr = oldmimeinfo.external_attr
                mimeinfo.create_system = oldmimeinfo.create_system
            except:
                pass
            self.outzip.writestr(mimeinfo, _MIMETYPE)

        # write the rest of the files
        for zinfo in self.inzip.infolist():
            if zinfo.filename != "mimetype" or self.ztype != 'epub':
                data = None
                try:
                    data = self.inzip.read(zinfo.filename)
                except zipfilerugged.BadZipfile or zipfilerugged.error:
                    local_name = self.getlocalname(zinfo)
                    data = self.getfiledata(zinfo)
                    zinfo.filename = local_name

                # create new ZipInfo with only the useful attributes from the old info
                nzinfo = ZipInfo(zinfo.filename, zinfo.date_time, compress_type=zinfo.compress_type)
                nzinfo.comment=zinfo.comment
                nzinfo.extra=zinfo.extra
                nzinfo.internal_attr=zinfo.internal_attr
                nzinfo.external_attr=zinfo.external_attr
                nzinfo.create_system=zinfo.create_system
                self.outzip.writestr(nzinfo,data)

        self.bzf.close()
        self.inzip.close()
        self.outzip.close()


def usage():
    print("""usage: zipfix.py inputzip outputzip
     inputzip is the source zipfile to fix
     outputzip is the fixed zip archive
    """)


def repairBook(infile, outfile):
    if not os.path.exists(infile):
        print("Error: Input Zip File does not exist")
        return 1
    try:
        fr = fixZip(infile, outfile)
        fr.fix()
        return 0
    except Exception, e:
        print("Error Occurred ", e)
        return 2


def main(argv=sys.argv):
    if len(argv)!=3:
        usage()
        return 1
    infile = argv[1]
    outfile = argv[2]
    return repairBook(infile, outfile)


if __name__ == '__main__' :
    sys.exit(main())
