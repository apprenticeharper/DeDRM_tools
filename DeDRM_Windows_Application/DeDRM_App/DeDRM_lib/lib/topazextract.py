#!/usr/bin/env python

class Unbuffered:
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

import sys

if 'calibre' in sys.modules:
    inCalibre = True
else:
    inCalibre = False

buildXML = False

import os, csv, getopt
import zlib, zipfile, tempfile, shutil
from struct import pack
from struct import unpack
from alfcrypto import Topaz_Cipher

class TpzDRMError(Exception):
    pass


# local support routines
if inCalibre:
    from calibre_plugins.k4mobidedrm import kgenpids
else:
    import kgenpids

# recursive zip creation support routine
def zipUpDir(myzip, tdir, localname):
    currentdir = tdir
    if localname != "":
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
    return unpack(str(stringLength)+"s",fo.read(stringLength))[0]

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
    fields = unpack("3sB8sB8s3s",record)
    if fields[0] != "PID" or fields[5] != "pid" :
        raise TpzDRMError("Didn't find PID magic numbers in record")
    elif fields[1] != 8 or fields[3] != 8 :
        raise TpzDRMError("Record didn't contain correct length fields")
    elif fields[2] != PID :
        raise TpzDRMError("Record didn't contain PID")
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
        except TpzDRMError:
            pass
        data = data[1+length:]
    if len(records) == 0:
        raise TpzDRMError("BookKey Not Found")
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
        magic = unpack("4s",self.fo.read(4))[0]
        if magic != 'TPZ0':
            raise TpzDRMError("Parse Error : Invalid Header, not a Topaz file")
        self.parseTopazHeaders()
        self.parseMetadata()

    def parseTopazHeaders(self):
        def bookReadHeaderRecordData():
            # Read and return the data of one header record at the current book file position
            # [[offset,decompressedLength,compressedLength],...]
            nbValues = bookReadEncodedNumber(self.fo)
            values = []
            for i in range (0,nbValues):
                values.append([bookReadEncodedNumber(self.fo),bookReadEncodedNumber(self.fo),bookReadEncodedNumber(self.fo)])
            return values
        def parseTopazHeaderRecord():
            # Read and parse one header record at the current book file position and return the associated data
            # [[offset,decompressedLength,compressedLength],...]
            if ord(self.fo.read(1)) != 0x63:
                raise TpzDRMError("Parse Error : Invalid Header")
            tag = bookReadString(self.fo)
            record = bookReadHeaderRecordData()
            return [tag,record]
        nbRecords = bookReadEncodedNumber(self.fo)
        for i in range (0,nbRecords):
            result = parseTopazHeaderRecord()
            # print result[0], result[1]
            self.bookHeaderRecords[result[0]] = result[1]
        if ord(self.fo.read(1))  != 0x64 :
            raise TpzDRMError("Parse Error : Invalid Header")
        self.bookPayloadOffset = self.fo.tell()

    def parseMetadata(self):
        # Parse the metadata record from the book payload and return a list of [key,values]
        self.fo.seek(self.bookPayloadOffset + self.bookHeaderRecords["metadata"][0][0])
        tag = bookReadString(self.fo)
        if tag != "metadata" :
            raise TpzDRMError("Parse Error : Record Names Don't Match")
        flags = ord(self.fo.read(1))
        nbRecords = ord(self.fo.read(1))
        # print nbRecords
        for i in range (0,nbRecords) :
            keyval = bookReadString(self.fo)
            content = bookReadString(self.fo)
            # print keyval
            # print content
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
        return title

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
            raise TpzDRMError("Parse Error : Invalid Record, record not found")

        self.fo.seek(self.bookPayloadOffset + recordOffset)

        tag = bookReadString(self.fo)
        if tag != name :
            raise TpzDRMError("Parse Error : Invalid Record, record name doesn't match")

        recordIndex = bookReadEncodedNumber(self.fo)
        if recordIndex < 0 :
            encrypted = True
            recordIndex = -recordIndex -1

        if recordIndex != index :
            raise TpzDRMError("Parse Error : Invalid Record, index doesn't match")

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
                raise TpzDRMError("Error: Attempt to decrypt without bookKey")

        if compressed:
            record = zlib.decompress(record)

        return record

    def processBook(self, pidlst):
        raw = 0
        fixedimage=True
        try:
            keydata = self.getBookPayloadRecord('dkey', 0)
        except TpzDRMError, e:
            print "no dkey record found, book may not be encrypted"
            print "attempting to extrct files without a book key"
            self.createBookDirectory()
            self.extractFiles()
            print "Successfully Extracted Topaz contents"
            if inCalibre:
                from calibre_plugins.k4mobidedrm import genbook
            else:
                import genbook

            rv = genbook.generateBook(self.outdir, raw, fixedimage)
            if rv == 0:
                print "\nBook Successfully generated"
            return rv

        # try each pid to decode the file
        bookKey = None
        for pid in pidlst:
            # use 8 digit pids here
            pid = pid[0:8]
            print "\nTrying: ", pid
            bookKeys = []
            data = keydata
            try:
                bookKeys+=decryptDkeyRecords(data,pid)
            except TpzDRMError, e:
                pass
            else:
                bookKey = bookKeys[0]
                print "Book Key Found!"
                break

        if not bookKey:
            raise TpzDRMError("Topaz Book. No key found in " + str(len(pidlst)) + " keys tried. Read the FAQs at Alf's blog. Only if none apply, report this failure for help.")

        self.setBookKey(bookKey)
        self.createBookDirectory()
        self.extractFiles()
        print "Successfully Extracted Topaz contents"
        if inCalibre:
            from calibre_plugins.k4mobidedrm import genbook
        else:
            import genbook

        rv = genbook.generateBook(self.outdir, raw, fixedimage)
        if rv == 0:
            print "\nBook Successfully generated"
        return rv

    def createBookDirectory(self):
        outdir = self.outdir
        # create output directory structure
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        destdir =  os.path.join(outdir,'img')
        if not os.path.exists(destdir):
            os.makedirs(destdir)
        destdir =  os.path.join(outdir,'color_img')
        if not os.path.exists(destdir):
            os.makedirs(destdir)
        destdir =  os.path.join(outdir,'page')
        if not os.path.exists(destdir):
            os.makedirs(destdir)
        destdir =  os.path.join(outdir,'glyphs')
        if not os.path.exists(destdir):
            os.makedirs(destdir)

    def extractFiles(self):
        outdir = self.outdir
        for headerRecord in self.bookHeaderRecords:
            name = headerRecord
            if name != "dkey" :
                ext = '.dat'
                if name == 'img' : ext = '.jpg'
                if name == 'color' : ext = '.jpg'
                print "\nProcessing Section: %s " % name
                for index in range (0,len(self.bookHeaderRecords[name])) :
                    fnum = "%04d" % index
                    fname = name + fnum + ext
                    destdir = outdir
                    if name == 'img':
                        destdir =  os.path.join(outdir,'img')
                    if name == 'color':
                        destdir =  os.path.join(outdir,'color_img')
                    if name == 'page':
                        destdir =  os.path.join(outdir,'page')
                    if name == 'glyphs':
                        destdir =  os.path.join(outdir,'glyphs')
                    outputFile = os.path.join(destdir,fname)
                    print ".",
                    record = self.getBookPayloadRecord(name,index)
                    if record != '':
                        file(outputFile, 'wb').write(record)
        print " "

    def getHTMLZip(self, zipname):
        htmlzip = zipfile.ZipFile(zipname,'w',zipfile.ZIP_DEFLATED, False)
        htmlzip.write(os.path.join(self.outdir,'book.html'),'book.html')
        htmlzip.write(os.path.join(self.outdir,'book.opf'),'book.opf')
        if os.path.isfile(os.path.join(self.outdir,'cover.jpg')):
            htmlzip.write(os.path.join(self.outdir,'cover.jpg'),'cover.jpg')
        htmlzip.write(os.path.join(self.outdir,'style.css'),'style.css')
        zipUpDir(htmlzip, self.outdir, 'img')
        htmlzip.close()

    def getSVGZip(self, zipname):
        svgzip = zipfile.ZipFile(zipname,'w',zipfile.ZIP_DEFLATED, False)
        svgzip.write(os.path.join(self.outdir,'index_svg.xhtml'),'index_svg.xhtml')
        zipUpDir(svgzip, self.outdir, 'svg')
        zipUpDir(svgzip, self.outdir, 'img')
        svgzip.close()

    def getXMLZip(self, zipname):
        xmlzip = zipfile.ZipFile(zipname,'w',zipfile.ZIP_DEFLATED, False)
        targetdir = os.path.join(self.outdir,'xml')
        zipUpDir(xmlzip, targetdir, '')
        zipUpDir(xmlzip, self.outdir, 'img')
        xmlzip.close()

    def cleanup(self):
        if os.path.isdir(self.outdir):
            shutil.rmtree(self.outdir, True)

def usage(progname):
    print "Removes DRM protection from Topaz ebooks and extract the contents"
    print "Usage:"
    print "    %s [-k <kindle.info>] [-p <pidnums>] [-s <kindleSerialNumbers>] <infile> <outdir>  " % progname


# Main
def main(argv=sys.argv):
    global buildXML
    progname = os.path.basename(argv[0])
    k4 = False
    pids = []
    serials = []
    kInfoFiles = []

    try:
        opts, args = getopt.getopt(sys.argv[1:], "k:p:s:")
    except getopt.GetoptError, err:
        print str(err)
        usage(progname)
        return 1
    if len(args)<2:
        usage(progname)
        return 1

    for o, a in opts:
        if o == "-k":
            if a == None :
                print "Invalid parameter for -k"
                return 1
            kInfoFiles.append(a)
        if o == "-p":
            if a == None :
                print "Invalid parameter for -p"
                return 1
            pids = a.split(',')
        if o == "-s":
            if a == None :
                print "Invalid parameter for -s"
                return 1
            serials = a.split(',')
    k4 = True

    infile = args[0]
    outdir = args[1]

    if not os.path.isfile(infile):
        print "Input File Does Not Exist"
        return 1

    bookname = os.path.splitext(os.path.basename(infile))[0]

    tb = TopazBook(infile)
    title = tb.getBookTitle()
    print "Processing Book: ", title
    keysRecord, keysRecordRecord = tb.getPIDMetaInfo()
    pids.extend(kgenpids.getPidList(keysRecord, keysRecordRecord, k4, serials, kInfoFiles))

    try:
        print "Decrypting Book"
        tb.processBook(pids)

        print "   Creating HTML ZIP Archive"
        zipname = os.path.join(outdir, bookname + '_nodrm' + '.htmlz')
        tb.getHTMLZip(zipname)

        print "   Creating SVG ZIP Archive"
        zipname = os.path.join(outdir, bookname + '_SVG' + '.zip')
        tb.getSVGZip(zipname)

        if buildXML:
            print "   Creating XML ZIP Archive"
            zipname = os.path.join(outdir, bookname + '_XML' + '.zip')
            tb.getXMLZip(zipname)

        # removing internal temporary directory of pieces
        tb.cleanup()

    except TpzDRMError, e:
        print str(e)
        # tb.cleanup()
        return 1

    except Exception, e:
        print str(e)
        # tb.cleanup
        return 1

    return 0


if __name__ == '__main__':
    sys.stdout=Unbuffered(sys.stdout)
    sys.exit(main())
