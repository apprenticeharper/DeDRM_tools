#!/usr/bin/env python

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
        print "opening input"
        self.inzip = zipfilerugged.ZipFile(zinput,'r')
        print "opening outout"
        self.outzip = zipfilerugged.ZipFile(zoutput,'w')
        print "opening input as raw file"
        # open the input zip for reading only as a raw file
        self.bzf = file(zinput,'rb')
        print "finished initialising"

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
            nzinfo = ZipInfo('mimetype', compress_type=zipfilerugged.ZIP_STORED)
            self.outzip.writestr(nzinfo, _MIMETYPE)

        # write the rest of the files
        for zinfo in self.inzip.infolist():
            if zinfo.filename != "mimetype" or self.ztype == '.zip':
                data = None
                nzinfo = zinfo
                try:
                    data = self.inzip.read(zinfo.filename)
                except zipfilerugged.BadZipfile or zipfilerugged.error:
                    local_name = self.getlocalname(zinfo)
                    data = self.getfiledata(zinfo)
                    nzinfo.filename = local_name

                nzinfo.date_time = zinfo.date_time
                nzinfo.compress_type = zinfo.compress_type
                nzinfo.flag_bits = 0
                nzinfo.internal_attr = 0
                self.outzip.writestr(nzinfo,data)

        self.bzf.close()
        self.inzip.close()
        self.outzip.close()


def usage():
    print """usage: zipfix.py inputzip outputzip
     inputzip is the source zipfile to fix
     outputzip is the fixed zip archive
    """


def repairBook(infile, outfile):
    if not os.path.exists(infile):
        print "Error: Input Zip File does not exist"
        return 1
    try:
        fr = fixZip(infile, outfile)
        fr.fix()
        return 0
    except Exception, e:
        print "Error Occurred ", e
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
