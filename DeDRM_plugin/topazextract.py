#!/usr/bin/env python
# -*- coding: utf-8 -*-

# topazextract.py
# Mostly written by some_updates based on code from many others

# Changelog
#  4.9  - moved unicode_argv call inside main for Windows DeDRM compatibility
#  5.0  - Fixed potential unicode problem with command line interface

from __future__ import print_function
__version__ = '5.0'

import sys
import os, csv, getopt
import zlib, zipfile, tempfile, shutil
import traceback
from struct import pack
from struct import unpack
from alfcrypto import Topaz_Cipher

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
                    xrange(start, argc.value)]
        # if we don't have any arguments at all, just pass back script name
        # this should never happen
        return [u"mobidedrm.py"]
    else:
        argvencoding = sys.stdin.encoding
        if argvencoding == None:
            argvencoding = 'utf-8'
        return [arg if (type(arg) == unicode) else unicode(arg,argvencoding) for arg in sys.argv]

#global switch
debug = False

if 'calibre' in sys.modules:
    inCalibre = True
    from calibre_plugins.dedrm import kgenpids
else:
    inCalibre = False
    import kgenpids


class DrmException(Exception):
    pass


# recursive zip creation support routine
def zipUpDir(myzip, tdir, localname):
    currentdir = tdir
    if localname != u"":
        currentdir = os.path.join(currentdir,localname)
    list = os.listdir(currentdir)
    for file in list:
        afilename = file
        localfilePath = os.path.join(localname, afilename)
        realfilePath = os.path.join(currentdir,file)
        if os.path.isfile(realfilePath):
            myzip.write(realfilePath, localfilePath)
        elif os.path.isdir(realfilePath):
            zipUpDir(myzip, tdir, localfilePath)

#
# Utility routines
#

# Get a 7 bit encoded number from file
def bookReadEncodedNumber(fo):
    flag = False
    data = ord(fo.read(1))
    if data == 0xFF:
        flag = True
        data = ord(fo.read(1))
    if data >= 0x80:
        datax = (data & 0x7F)
        while data >= 0x80 :
            data = ord(fo.read(1))
            datax = (datax <<7) + (data & 0x7F)
        data = datax
    if flag:
        data = -data
    return data

# Get a length prefixed string from file
def bookReadString(fo):
    stringLength = bookReadEncodedNumber(fo)
    return unpack(str(stringLength)+'s',fo.read(stringLength))[0]

#
# crypto routines
#

# Context initialisation for the Topaz Crypto
def topazCryptoInit(key):
    return Topaz_Cipher().ctx_init(key)

#     ctx1 = 0x0CAFFE19E
#     for keyChar in key:
#         keyByte = ord(keyChar)
#         ctx2 = ctx1
#         ctx1 = ((((ctx1 >>2) * (ctx1 >>7))&0xFFFFFFFF) ^ (keyByte * keyByte * 0x0F902007)& 0xFFFFFFFF )
#     return [ctx1,ctx2]

# decrypt data with the context prepared by topazCryptoInit()
def topazCryptoDecrypt(data, ctx):
    return Topaz_Cipher().decrypt(data, ctx)
#     ctx1 = ctx[0]
#     ctx2 = ctx[1]
#     plainText = ""
#     for dataChar in data:
#         dataByte = ord(dataChar)
#         m = (dataByte ^ ((ctx1 >> 3) &0xFF) ^ ((ctx2<<3) & 0xFF)) &0xFF
#         ctx2 = ctx1
#         ctx1 = (((ctx1 >> 2) * (ctx1 >> 7)) &0xFFFFFFFF) ^((m * m * 0x0F902007) &0xFFFFFFFF)
#         plainText += chr(m)
#     return plainText

# Decrypt data with the PID
def decryptRecord(data,PID):
    ctx = topazCryptoInit(PID)
    return topazCryptoDecrypt(data, ctx)

# Try to decrypt a dkey record (contains the bookPID)
def decryptDkeyRecord(data,PID):
    record = decryptRecord(data,PID)
    fields = unpack('3sB8sB8s3s',record)
    if fields[0] != 'PID' or fields[5] != 'pid' :
        raise DrmException(u"Didn't find PID magic numbers in record")
    elif fields[1] != 8 or fields[3] != 8 :
        raise DrmException(u"Record didn't contain correct length fields")
    elif fields[2] != PID :
        raise DrmException(u"Record didn't contain PID")
    return fields[4]

# Decrypt all dkey records (contain the book PID)
def decryptDkeyRecords(data,PID):
    nbKeyRecords = ord(data[0])
    records = []
    data = data[1:]
    for i in range (0,nbKeyRecords):
        length = ord(data[0])
        try:
            key = decryptDkeyRecord(data[1:length+1],PID)
            records.append(key)
        except DrmException:
            pass
        data = data[1+length:]
    if len(records) == 0:
        raise DrmException(u"BookKey Not Found")
    return records


class TopazBook:
    def __init__(self, filename):
        self.fo = file(filename, 'rb')
        self.outdir = tempfile.mkdtemp()
        # self.outdir = 'rawdat'
        self.bookPayloadOffset = 0
        self.bookHeaderRecords = {}
        self.bookMetadata = {}
        self.bookKey = None
        magic = unpack('4s',self.fo.read(4))[0]
        if magic != 'TPZ0':
            raise DrmException(u"Parse Error : Invalid Header, not a Topaz file")
        self.parseTopazHeaders()
        self.parseMetadata()

    def parseTopazHeaders(self):
        def bookReadHeaderRecordData():
            # Read and return the data of one header record at the current book file position
            # [[offset,decompressedLength,compressedLength],...]
            nbValues = bookReadEncodedNumber(self.fo)
            if debug: print("%d records in header " % nbValues, end=' ')
            values = []
            for i in range (0,nbValues):
                values.append([bookReadEncodedNumber(self.fo),bookReadEncodedNumber(self.fo),bookReadEncodedNumber(self.fo)])
            return values
        def parseTopazHeaderRecord():
            # Read and parse one header record at the current book file position and return the associated data
            # [[offset,decompressedLength,compressedLength],...]
            if ord(self.fo.read(1)) != 0x63:
                raise DrmException(u"Parse Error : Invalid Header")
            tag = bookReadString(self.fo)
            record = bookReadHeaderRecordData()
            return [tag,record]
        nbRecords = bookReadEncodedNumber(self.fo)
        if debug: print("Headers: %d" % nbRecords)
        for i in range (0,nbRecords):
            result = parseTopazHeaderRecord()
            if debug: print(result[0], ": ", result[1])
            self.bookHeaderRecords[result[0]] = result[1]
        if ord(self.fo.read(1))  != 0x64 :
            raise DrmException(u"Parse Error : Invalid Header")
        self.bookPayloadOffset = self.fo.tell()

    def parseMetadata(self):
        # Parse the metadata record from the book payload and return a list of [key,values]
        self.fo.seek(self.bookPayloadOffset + self.bookHeaderRecords['metadata'][0][0])
        tag = bookReadString(self.fo)
        if tag != 'metadata' :
            raise DrmException(u"Parse Error : Record Names Don't Match")
        flags = ord(self.fo.read(1))
        nbRecords = ord(self.fo.read(1))
        if debug: print("Metadata Records: %d" % nbRecords)
        for i in range (0,nbRecords) :
            keyval = bookReadString(self.fo)
            content = bookReadString(self.fo)
            if debug: print(keyval)
            if debug: print(content)
            self.bookMetadata[keyval] = content
        return self.bookMetadata

    def getPIDMetaInfo(self):
        keysRecord = self.bookMetadata.get('keys','')
        keysRecordRecord = ''
        if keysRecord != '':
            keylst = keysRecord.split(',')
            for keyval in keylst:
                keysRecordRecord += self.bookMetadata.get(keyval,'')
        return keysRecord, keysRecordRecord

    def getBookTitle(self):
        title = ''
        if 'Title' in self.bookMetadata:
            title = self.bookMetadata['Title']
        return title.decode('utf-8')

    def setBookKey(self, key):
        self.bookKey = key

    def getBookPayloadRecord(self, name, index):
        # Get a record in the book payload, given its name and index.
        # decrypted and decompressed if necessary
        encrypted = False
        compressed = False
        try:
            recordOffset = self.bookHeaderRecords[name][index][0]
        except:
            raise DrmException("Parse Error : Invalid Record, record not found")

        self.fo.seek(self.bookPayloadOffset + recordOffset)

        tag = bookReadString(self.fo)
        if tag != name :
            raise DrmException("Parse Error : Invalid Record, record name doesn't match")

        recordIndex = bookReadEncodedNumber(self.fo)
        if recordIndex < 0 :
            encrypted = True
            recordIndex = -recordIndex -1

        if recordIndex != index :
            raise DrmException("Parse Error : Invalid Record, index doesn't match")

        if (self.bookHeaderRecords[name][index][2] > 0):
            compressed = True
            record = self.fo.read(self.bookHeaderRecords[name][index][2])
        else:
            record = self.fo.read(self.bookHeaderRecords[name][index][1])

        if encrypted:
            if self.bookKey:
                ctx = topazCryptoInit(self.bookKey)
                record = topazCryptoDecrypt(record,ctx)
            else :
                raise DrmException("Error: Attempt to decrypt without bookKey")

        if compressed:
            record = zlib.decompress(record)

        return record

    def processBook(self, pidlst):
        raw = 0
        fixedimage=True
        try:
            keydata = self.getBookPayloadRecord('dkey', 0)
        except DrmException, e:
            print(u"no dkey record found, book may not be encrypted")
            print(u"attempting to extrct files without a book key")
            self.createBookDirectory()
            self.extractFiles()
            print(u"Successfully Extracted Topaz contents")
            if inCalibre:
                from calibre_plugins.dedrm import genbook
            else:
                import genbook

            rv = genbook.generateBook(self.outdir, raw, fixedimage)
            if rv == 0:
                print(u"Book Successfully generated.")
            return rv

        # try each pid to decode the file
        bookKey = None
        for pid in pidlst:
            # use 8 digit pids here
            pid = pid[0:8]
            print(u"Trying: {0}".format(pid))
            bookKeys = []
            data = keydata
            try:
                bookKeys+=decryptDkeyRecords(data,pid)
            except DrmException, e:
                pass
            else:
                bookKey = bookKeys[0]
                print(u"Book Key Found! ({0})".format(bookKey.encode('hex')))
                break

        if not bookKey:
            raise DrmException(u"No key found in {0:d} keys tried. Read the FAQs at Harper's repository: https://github.com/apprenticeharper/DeDRM_tools/blob/master/FAQs.md".format(len(pidlst)))

        self.setBookKey(bookKey)
        self.createBookDirectory()
        self.extractFiles() 
        print(u"Successfully Extracted Topaz contents")
        if inCalibre:
            from calibre_plugins.dedrm import genbook
        else:
            import genbook

        rv = genbook.generateBook(self.outdir, raw, fixedimage)
        if rv == 0:
            print(u"Book Successfully generated")
        return rv

    def createBookDirectory(self):
        outdir = self.outdir
        # create output directory structure
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        destdir =  os.path.join(outdir,u"img")
        if not os.path.exists(destdir):
            os.makedirs(destdir)
        destdir =  os.path.join(outdir,u"color_img")
        if not os.path.exists(destdir):
            os.makedirs(destdir)
        destdir =  os.path.join(outdir,u"page")
        if not os.path.exists(destdir):
            os.makedirs(destdir)
        destdir =  os.path.join(outdir,u"glyphs")
        if not os.path.exists(destdir):
            os.makedirs(destdir)

    def extractFiles(self):
        outdir = self.outdir
        for headerRecord in self.bookHeaderRecords:
            name = headerRecord
            if name != 'dkey':
                ext = u".dat"
                if name == 'img': ext = u".jpg"
                if name == 'color' : ext = u".jpg"
                print(u"Processing Section: {0}\n. . .".format(name), end=' ')
                for index in range (0,len(self.bookHeaderRecords[name])) :
                    fname = u"{0}{1:04d}{2}".format(name,index,ext)
                    destdir = outdir
                    if name == 'img':
                        destdir =  os.path.join(outdir,u"img")
                    if name == 'color':
                        destdir =  os.path.join(outdir,u"color_img")
                    if name == 'page':
                        destdir =  os.path.join(outdir,u"page")
                    if name == 'glyphs':
                        destdir =  os.path.join(outdir,u"glyphs")
                    outputFile = os.path.join(destdir,fname)
                    print(u".", end=' ')
                    record = self.getBookPayloadRecord(name,index)
                    if record != '':
                        file(outputFile, 'wb').write(record)
                print(u" ")

    def getFile(self, zipname):
        htmlzip = zipfile.ZipFile(zipname,'w',zipfile.ZIP_DEFLATED, False)
        htmlzip.write(os.path.join(self.outdir,u"book.html"),u"book.html")
        htmlzip.write(os.path.join(self.outdir,u"book.opf"),u"book.opf")
        if os.path.isfile(os.path.join(self.outdir,u"cover.jpg")):
            htmlzip.write(os.path.join(self.outdir,u"cover.jpg"),u"cover.jpg")
        htmlzip.write(os.path.join(self.outdir,u"style.css"),u"style.css")
        zipUpDir(htmlzip, self.outdir, u"img")
        htmlzip.close()

    def getBookType(self):
        return u"Topaz"

    def getBookExtension(self):
        return u".htmlz"

    def getSVGZip(self, zipname):
        svgzip = zipfile.ZipFile(zipname,'w',zipfile.ZIP_DEFLATED, False)
        svgzip.write(os.path.join(self.outdir,u"index_svg.xhtml"),u"index_svg.xhtml")
        zipUpDir(svgzip, self.outdir, u"svg")
        zipUpDir(svgzip, self.outdir, u"img")
        svgzip.close()

    def cleanup(self):
        if os.path.isdir(self.outdir):
            shutil.rmtree(self.outdir, True)

def usage(progname):
    print(u"Removes DRM protection from Topaz ebooks and extracts the contents")
    print(u"Usage:")
    print(u"    {0} [-k <kindle.k4i>] [-p <comma separated PIDs>] [-s <comma separated Kindle serial numbers>] <infile> <outdir>".format(progname))

# Main
def cli_main():
    argv=unicode_argv()
    progname = os.path.basename(argv[0])
    print(u"TopazExtract v{0}.".format(__version__))

    try:
        opts, args = getopt.getopt(argv[1:], "k:p:s:x")
    except getopt.GetoptError, err:
        print(u"Error in options or arguments: {0}".format(err.args[0]))
        usage(progname)
        return 1
    if len(args)<2:
        usage(progname)
        return 1

    infile = args[0]
    outdir = args[1]
    if not os.path.isfile(infile):
        print(u"Input File {0} Does Not Exist.".format(infile))
        return 1

    if not os.path.exists(outdir):
        print(u"Output Directory {0} Does Not Exist.".format(outdir))
        return 1

    kDatabaseFiles = []
    serials = []
    pids = []

    for o, a in opts:
        if o == '-k':
            if a == None :
                raise DrmException("Invalid parameter for -k")
            kDatabaseFiles.append(a)
        if o == '-p':
            if a == None :
                raise DrmException("Invalid parameter for -p")
            pids = a.split(',')
        if o == '-s':
            if a == None :
                raise DrmException("Invalid parameter for -s")
            serials = [serial.replace(" ","") for serial in a.split(',')]

    bookname = os.path.splitext(os.path.basename(infile))[0]

    tb = TopazBook(infile)
    title = tb.getBookTitle()
    print(u"Processing Book: {0}".format(title))
    md1, md2 = tb.getPIDMetaInfo()
    pids.extend(kgenpids.getPidList(md1, md2, serials, kDatabaseFiles))

    try:
        print(u"Decrypting Book")
        tb.processBook(pids)

        print(u"   Creating HTML ZIP Archive")
        zipname = os.path.join(outdir, bookname + u"_nodrm.htmlz")
        tb.getFile(zipname)

        print(u"   Creating SVG ZIP Archive")
        zipname = os.path.join(outdir, bookname + u"_SVG.zip")
        tb.getSVGZip(zipname)

        # removing internal temporary directory of pieces
        tb.cleanup()

    except DrmException, e:
        print(u"Decryption failed\n{0}".format(traceback.format_exc()))

        try:
            tb.cleanup()
        except:
            pass
        return 1

    except Exception, e:
        print(u"Decryption failed\m{0}".format(traceback.format_exc()))
        try:
            tb.cleanup()
        except:
            pass
        return 1

    return 0


if __name__ == '__main__':
    sys.stdout=SafeUnbuffered(sys.stdout)
    sys.stderr=SafeUnbuffered(sys.stderr)
    sys.exit(cli_main())
