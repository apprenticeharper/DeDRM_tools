#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# Python 3 for calibre 5.0
from __future__ import print_function

#@@CALIBRE_COMPAT_CODE@@

from .utilities import SafeUnbuffered

import sys
import csv
import os
import getopt
from struct import pack
from struct import unpack

#@@CALIBRE_COMPAT_CODE@@


class TpzDRMError(Exception):
    pass

# local support routines
import convert2xml
import flatxml2html
import flatxml2svg
import stylexml2css

# global switch
buildXML = False

# Get a 7 bit encoded number from a file
def readEncodedNumber(file):
    flag = False
    c = file.read(1)
    if (len(c) == 0):
        return None
    data = ord(c)
    if data == 0xFF:
        flag = True
        c = file.read(1)
        if (len(c) == 0):
            return None
        data = ord(c)
    if data >= 0x80:
        datax = (data & 0x7F)
        while data >= 0x80 :
            c = file.read(1)
            if (len(c) == 0):
                return None
            data = ord(c)
            datax = (datax <<7) + (data & 0x7F)
        data = datax
    if flag:
        data = -data
    return data

# Get a length prefixed string from the file
def lengthPrefixString(data):
    return encodeNumber(len(data))+data

def readString(file):
    stringLength = readEncodedNumber(file)
    if (stringLength == None):
        return None
    sv = file.read(stringLength)
    if (len(sv)  != stringLength):
        return ""
    return unpack(str(stringLength)+"s",sv)[0]

def getMetaArray(metaFile):
    # parse the meta file
    result = {}
    fo = open(metaFile,'rb')
    size = readEncodedNumber(fo)
    for i in range(size):
        tag = readString(fo)
        value = readString(fo)
        result[tag] = value
        # print(tag, value)
    fo.close()
    return result


# dictionary of all text strings by index value
class Dictionary(object):
    def __init__(self, dictFile):
        self.filename = dictFile
        self.size = 0
        self.fo = open(dictFile,'rb')
        self.stable = []
        self.size = readEncodedNumber(self.fo)
        for i in range(self.size):
            self.stable.append(self.escapestr(readString(self.fo)))
        self.pos = 0
    def escapestr(self, str):
        str = str.replace(b'&',b'&amp;')
        str = str.replace(b'<',b'&lt;')
        str = str.replace(b'>',b'&gt;')
        str = str.replace(b'=',b'&#61;')
        return str
    def lookup(self,val):
        if ((val >= 0) and (val < self.size)) :
            self.pos = val
            return self.stable[self.pos]
        else:
            print("Error: %d outside of string table limits" % val)
            raise TpzDRMError('outside or string table limits')
            # sys.exit(-1)
    def getSize(self):
        return self.size
    def getPos(self):
        return self.pos


class PageDimParser(object):
    def __init__(self, flatxml):
        self.flatdoc = flatxml.split(b'\n')
    # find tag if within pos to end inclusive
    def findinDoc(self, tagpath, pos, end) :
        result = None
        docList = self.flatdoc
        cnt = len(docList)
        if end == -1 :
            end = cnt
        else:
            end = min(cnt,end)
        foundat = -1
        for j in range(pos, end):
            item = docList[j]
            if item.find(b'=') >= 0:
                (name, argres) = item.split(b'=')
            else :
                name = item
                argres = ''
            if name.endswith(tagpath) :
                result = argres
                foundat = j
                break
        return foundat, result
    def process(self):
        (pos, sph) = self.findinDoc(b'page.h',0,-1)
        (pos, spw) = self.findinDoc(b'page.w',0,-1)
        if (sph == None): sph = '-1'
        if (spw == None): spw = '-1'
        return sph, spw

def getPageDim(flatxml):
    # create a document parser
    dp = PageDimParser(flatxml)
    (ph, pw) = dp.process()
    return ph, pw

class GParser(object):
    def __init__(self, flatxml):
        self.flatdoc = flatxml.split(b'\n')
        self.dpi = 1440
        self.gh = self.getData(b'info.glyph.h')
        self.gw = self.getData(b'info.glyph.w')
        self.guse = self.getData(b'info.glyph.use')
        if self.guse :
            self.count = len(self.guse)
        else :
            self.count = 0
        self.gvtx = self.getData(b'info.glyph.vtx')
        self.glen = self.getData(b'info.glyph.len')
        self.gdpi = self.getData(b'info.glyph.dpi')
        self.vx = self.getData(b'info.vtx.x')
        self.vy = self.getData(b'info.vtx.y')
        self.vlen = self.getData(b'info.len.n')
        if self.vlen :
            self.glen.append(len(self.vlen))
        elif self.glen:
            self.glen.append(0)
        if self.vx :
            self.gvtx.append(len(self.vx))
        elif self.gvtx :
            self.gvtx.append(0)
    def getData(self, path):
        result = None
        cnt = len(self.flatdoc)
        for j in range(cnt):
            item = self.flatdoc[j]
            if item.find(b'=') >= 0:
                (name, argt) = item.split(b'=')
                argres = argt.split(b'|')
            else:
                name = item
                argres = []
            if (name == path):
                result = argres
                break
        if (len(argres) > 0) :
            for j in range(0,len(argres)):
                argres[j] = int(argres[j])
        return result
    def getGlyphDim(self, gly):
        if self.gdpi[gly] == 0:
            return 0, 0
        maxh = (self.gh[gly] * self.dpi) / self.gdpi[gly]
        maxw = (self.gw[gly] * self.dpi) / self.gdpi[gly]
        return maxh, maxw
    def getPath(self, gly):
        path = ''
        if (gly < 0) or (gly >= self.count):
            return path
        tx = self.vx[self.gvtx[gly]:self.gvtx[gly+1]]
        ty = self.vy[self.gvtx[gly]:self.gvtx[gly+1]]
        p = 0
        for k in range(self.glen[gly], self.glen[gly+1]):
            if (p == 0):
                zx = tx[0:self.vlen[k]+1]
                zy = ty[0:self.vlen[k]+1]
            else:
                zx = tx[self.vlen[k-1]+1:self.vlen[k]+1]
                zy = ty[self.vlen[k-1]+1:self.vlen[k]+1]
            p += 1
            j = 0
            while ( j  < len(zx) ):
                if (j == 0):
                    # Start Position.
                    path += 'M %d %d ' % (zx[j] * self.dpi / self.gdpi[gly], zy[j] * self.dpi / self.gdpi[gly])
                elif (j <= len(zx)-3):
                    # Cubic Bezier Curve
                    path += 'C %d %d %d %d %d %d ' % (zx[j] * self.dpi / self.gdpi[gly], zy[j] * self.dpi / self.gdpi[gly], zx[j+1] * self.dpi / self.gdpi[gly], zy[j+1] * self.dpi / self.gdpi[gly], zx[j+2] * self.dpi / self.gdpi[gly], zy[j+2] * self.dpi / self.gdpi[gly])
                    j += 2
                elif (j == len(zx)-2):
                    # Cubic Bezier Curve to Start Position
                    path += 'C %d %d %d %d %d %d ' % (zx[j] * self.dpi / self.gdpi[gly], zy[j] * self.dpi / self.gdpi[gly], zx[j+1] * self.dpi / self.gdpi[gly], zy[j+1] * self.dpi / self.gdpi[gly], zx[0] * self.dpi / self.gdpi[gly], zy[0] * self.dpi / self.gdpi[gly])
                    j += 1
                elif (j == len(zx)-1):
                    # Quadratic Bezier Curve to Start Position
                    path += 'Q %d %d %d %d ' % (zx[j] * self.dpi / self.gdpi[gly], zy[j] * self.dpi / self.gdpi[gly], zx[0] * self.dpi / self.gdpi[gly], zy[0] * self.dpi / self.gdpi[gly])

                j += 1
        path += 'z'
        return path



# dictionary of all text strings by index value
class GlyphDict(object):
    def __init__(self):
        self.gdict = {}
    def lookup(self, id):
        # id='id="gl%d"' % val
        if id in self.gdict:
            return self.gdict[id]
        return None
    def addGlyph(self, val, path):
        id='id="gl%d"' % val
        self.gdict[id] = path


def generateBook(bookDir, raw, fixedimage):
    # sanity check Topaz file extraction
    if not os.path.exists(bookDir) :
        print("Can not find directory with unencrypted book")
        return 1

    dictFile = os.path.join(bookDir,'dict0000.dat')
    if not os.path.exists(dictFile) :
        print("Can not find dict0000.dat file")
        return 1

    pageDir = os.path.join(bookDir,'page')
    if not os.path.exists(pageDir) :
        print("Can not find page directory in unencrypted book")
        return 1

    imgDir = os.path.join(bookDir,'img')
    if not os.path.exists(imgDir) :
        print("Can not find image directory in unencrypted book")
        return 1

    glyphsDir = os.path.join(bookDir,'glyphs')
    if not os.path.exists(glyphsDir) :
        print("Can not find glyphs directory in unencrypted book")
        return 1

    metaFile = os.path.join(bookDir,'metadata0000.dat')
    if not os.path.exists(metaFile) :
        print("Can not find metadata0000.dat in unencrypted book")
        return 1

    svgDir = os.path.join(bookDir,'svg')
    if not os.path.exists(svgDir) :
        os.makedirs(svgDir)

    if buildXML:
        xmlDir = os.path.join(bookDir,'xml')
        if not os.path.exists(xmlDir) :
            os.makedirs(xmlDir)

    otherFile = os.path.join(bookDir,'other0000.dat')
    if not os.path.exists(otherFile) :
        print("Can not find other0000.dat in unencrypted book")
        return 1

    print("Updating to color images if available")
    spath = os.path.join(bookDir,'color_img')
    dpath = os.path.join(bookDir,'img')
    filenames = os.listdir(spath)
    filenames = sorted(filenames)
    for filename in filenames:
        imgname = filename.replace('color','img')
        sfile = os.path.join(spath,filename)
        dfile = os.path.join(dpath,imgname)
        imgdata = open(sfile,'rb').read()
        open(dfile,'wb').write(imgdata)

    print("Creating cover.jpg")
    isCover = False
    cpath = os.path.join(bookDir,'img')
    cpath = os.path.join(cpath,'img0000.jpg')
    if os.path.isfile(cpath):
        cover = open(cpath, 'rb').read()
        cpath = os.path.join(bookDir,'cover.jpg')
        open(cpath, 'wb').write(cover)
        isCover = True


    print('Processing Dictionary')
    dict = Dictionary(dictFile)

    print('Processing Meta Data and creating OPF')
    meta_array = getMetaArray(metaFile)

    # replace special chars in title and authors like & < >
    title = meta_array.get('Title','No Title Provided')
    title = title.replace('&','&amp;')
    title = title.replace('<','&lt;')
    title = title.replace('>','&gt;')
    meta_array['Title'] = title
    authors = meta_array.get('Authors','No Authors Provided')
    authors = authors.replace('&','&amp;')
    authors = authors.replace('<','&lt;')
    authors = authors.replace('>','&gt;')
    meta_array['Authors'] = authors

    if buildXML:
        xname = os.path.join(xmlDir, 'metadata.xml')
        mlst = []
        for key in meta_array:
            mlst.append('<meta name="' + key + '" content="' + meta_array[key] + '" />\n')
        metastr = "".join(mlst)
        mlst = None
        open(xname, 'wb').write(metastr)

    print('Processing StyleSheet')

    # get some scaling info from metadata to use while processing styles
    # and first page info

    fontsize = '135'
    if 'fontSize' in meta_array:
        fontsize = meta_array['fontSize']

    # also get the size of a normal text page
    # get the total number of pages unpacked as a safety check
    filenames = os.listdir(pageDir)
    numfiles = len(filenames)

    spage = '1'
    if 'firstTextPage' in meta_array:
        spage = meta_array['firstTextPage']
    pnum = int(spage)
    if pnum >= numfiles or pnum < 0:
        # metadata is wrong so just select a page near the front
        # 10% of the book to get a normal text page
        pnum = int(0.10 * numfiles)
    # print "first normal text page is", spage

    # get page height and width from first text page for use in stylesheet scaling
    pname = 'page%04d.dat' % (pnum - 1)
    fname = os.path.join(pageDir,pname)
    flat_xml = convert2xml.fromData(dict, fname)

    (ph, pw) = getPageDim(flat_xml)
    if (ph == '-1') or (ph == '0') : ph = '11000'
    if (pw == '-1') or (pw == '0') : pw = '8500'
    meta_array['pageHeight'] = ph
    meta_array['pageWidth'] = pw
    if 'fontSize' not in meta_array.keys():
        meta_array['fontSize'] = fontsize

    # process other.dat for css info and for map of page files to svg images
    # this map is needed because some pages actually are made up of multiple
    # pageXXXX.xml files
    xname = os.path.join(bookDir, 'style.css')
    flat_xml = convert2xml.fromData(dict, otherFile)

    # extract info.original.pid to get original page information
    pageIDMap = {}
    pageidnums = stylexml2css.getpageIDMap(flat_xml)
    if len(pageidnums) == 0:
        filenames = os.listdir(pageDir)
        numfiles = len(filenames)
        for k in range(numfiles):
            pageidnums.append(k)
    # create a map from page ids to list of page file nums to process for that page
    for i in range(len(pageidnums)):
        id = pageidnums[i]
        if id in pageIDMap.keys():
            pageIDMap[id].append(i)
        else:
            pageIDMap[id] = [i]

    # now get the css info
    cssstr , classlst = stylexml2css.convert2CSS(flat_xml, fontsize, ph, pw)
    open(xname, 'w').write(cssstr)
    if buildXML:
        xname = os.path.join(xmlDir, 'other0000.xml')
        open(xname, 'wb').write(convert2xml.getXML(dict, otherFile))

    print('Processing Glyphs')
    gd = GlyphDict()
    filenames = os.listdir(glyphsDir)
    filenames = sorted(filenames)
    glyfname = os.path.join(svgDir,'glyphs.svg')
    glyfile = open(glyfname, 'w')
    glyfile.write('<?xml version="1.0" standalone="no"?>\n')
    glyfile.write('<!DOCTYPE svg PUBLIC "-//W3C/DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n')
    glyfile.write('<svg width="512" height="512" viewBox="0 0 511 511" xmlns="http://www.w3.org/2000/svg" version="1.1">\n')
    glyfile.write('<title>Glyphs for %s</title>\n' % meta_array['Title'])
    glyfile.write('<defs>\n')
    counter = 0
    for filename in filenames:
        # print '     ', filename
        print('.', end=' ')
        fname = os.path.join(glyphsDir,filename)
        flat_xml = convert2xml.fromData(dict, fname)

        if buildXML:
            xname = os.path.join(xmlDir, filename.replace('.dat','.xml'))
            open(xname, 'wb').write(convert2xml.getXML(dict, fname))

        gp = GParser(flat_xml)
        for i in range(0, gp.count):
            path = gp.getPath(i)
            maxh, maxw = gp.getGlyphDim(i)
            fullpath = '<path id="gl%d" d="%s" fill="black" /><!-- width=%d height=%d -->\n' % (counter * 256 + i, path, maxw, maxh)
            glyfile.write(fullpath)
            gd.addGlyph(counter * 256 + i, fullpath)
        counter += 1
    glyfile.write('</defs>\n')
    glyfile.write('</svg>\n')
    glyfile.close()
    print(" ")


    # start up the html
    # also build up tocentries while processing html
    htmlFileName = "book.html"
    hlst = []
    hlst.append('<?xml version="1.0" encoding="utf-8"?>\n')
    hlst.append('<!DOCTYPE HTML PUBLIC "-//W3C//DTD XHTML 1.1 Strict//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11-strict.dtd">\n')
    hlst.append('<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">\n')
    hlst.append('<head>\n')
    hlst.append('<meta http-equiv="content-type" content="text/html; charset=utf-8"/>\n')
    hlst.append('<title>' + meta_array['Title'] + ' by ' + meta_array['Authors'] + '</title>\n')
    hlst.append('<meta name="Author" content="' + meta_array['Authors'] + '" />\n')
    hlst.append('<meta name="Title" content="' + meta_array['Title'] + '" />\n')
    if 'ASIN' in meta_array:
        hlst.append('<meta name="ASIN" content="' + meta_array['ASIN'] + '" />\n')
    if 'GUID' in meta_array:
        hlst.append('<meta name="GUID" content="' + meta_array['GUID'] + '" />\n')
    hlst.append('<link href="style.css" rel="stylesheet" type="text/css" />\n')
    hlst.append('</head>\n<body>\n')

    print('Processing Pages')
    # Books are at 1440 DPI.  This is rendering at twice that size for
    # readability when rendering to the screen.
    scaledpi = 1440.0

    filenames = os.listdir(pageDir)
    filenames = sorted(filenames)
    numfiles = len(filenames)

    xmllst = []
    elst = []

    for filename in filenames:
        # print '     ', filename
        print(".", end=' ')
        fname = os.path.join(pageDir,filename)
        flat_xml = convert2xml.fromData(dict, fname)

        # keep flat_xml for later svg processing
        xmllst.append(flat_xml)

        if buildXML:
            xname = os.path.join(xmlDir, filename.replace('.dat','.xml'))
            open(xname, 'wb').write(convert2xml.getXML(dict, fname))

        # first get the html
        pagehtml, tocinfo = flatxml2html.convert2HTML(flat_xml, classlst, fname, bookDir, gd, fixedimage)
        elst.append(tocinfo)
        hlst.append(pagehtml)

    # finish up the html string and output it
    hlst.append('</body>\n</html>\n')
    htmlstr = "".join(hlst)
    hlst = None
    open(os.path.join(bookDir, htmlFileName), 'w').write(htmlstr)

    print(" ")
    print('Extracting Table of Contents from Amazon OCR')

    # first create a table of contents file for the svg images
    tlst = []
    tlst.append('<?xml version="1.0" encoding="utf-8"?>\n')
    tlst.append('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">\n')
    tlst.append('<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" >')
    tlst.append('<head>\n')
    tlst.append('<title>' + meta_array['Title'] + '</title>\n')
    tlst.append('<meta name="Author" content="' + meta_array['Authors'] + '" />\n')
    tlst.append('<meta name="Title" content="' + meta_array['Title'] + '" />\n')
    if 'ASIN' in meta_array:
        tlst.append('<meta name="ASIN" content="' + meta_array['ASIN'] + '" />\n')
    if 'GUID' in meta_array:
        tlst.append('<meta name="GUID" content="' + meta_array['GUID'] + '" />\n')
    tlst.append('</head>\n')
    tlst.append('<body>\n')

    tlst.append('<h2>Table of Contents</h2>\n')
    start = pageidnums[0]
    if (raw):
        startname = 'page%04d.svg' % start
    else:
        startname = 'page%04d.xhtml' % start

    tlst.append('<h3><a href="' + startname + '">Start of Book</a></h3>\n')
    # build up a table of contents for the svg xhtml output
    tocentries = "".join(elst)
    elst = None
    toclst = tocentries.split('\n')
    toclst.pop()
    for entry in toclst:
        print(entry)
        title, pagenum = entry.split('|')
        id = pageidnums[int(pagenum)]
        if (raw):
            fname = 'page%04d.svg' % id
        else:
            fname = 'page%04d.xhtml' % id
        tlst.append('<h3><a href="'+ fname + '">' + title + '</a></h3>\n')
    tlst.append('</body>\n')
    tlst.append('</html>\n')
    tochtml = "".join(tlst)
    open(os.path.join(svgDir, 'toc.xhtml'), 'w').write(tochtml)


    # now create index_svg.xhtml that points to all required files
    slst = []
    slst.append('<?xml version="1.0" encoding="utf-8"?>\n')
    slst.append('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">\n')
    slst.append('<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" >')
    slst.append('<head>\n')
    slst.append('<title>' + meta_array['Title'] + '</title>\n')
    slst.append('<meta name="Author" content="' + meta_array['Authors'] + '" />\n')
    slst.append('<meta name="Title" content="' + meta_array['Title'] + '" />\n')
    if 'ASIN' in meta_array:
        slst.append('<meta name="ASIN" content="' + meta_array['ASIN'] + '" />\n')
    if 'GUID' in meta_array:
        slst.append('<meta name="GUID" content="' + meta_array['GUID'] + '" />\n')
    slst.append('</head>\n')
    slst.append('<body>\n')

    print("Building svg images of each book page")
    slst.append('<h2>List of Pages</h2>\n')
    slst.append('<div>\n')
    idlst = sorted(pageIDMap.keys())
    numids = len(idlst)
    cnt = len(idlst)
    previd = None
    for j in range(cnt):
        pageid = idlst[j]
        if j < cnt - 1:
            nextid = idlst[j+1]
        else:
            nextid = None
        print('.', end=' ')
        pagelst = pageIDMap[pageid]
        flst = []
        for page in pagelst:
            flst.append(xmllst[page])
        flat_svg = b"".join(flst)
        flst=None
        svgxml = flatxml2svg.convert2SVG(gd, flat_svg, pageid, previd, nextid, svgDir, raw, meta_array, scaledpi)
        if (raw) :
            pfile = open(os.path.join(svgDir,'page%04d.svg' % pageid),'w')
            slst.append('<a href="svg/page%04d.svg">Page %d</a>\n' % (pageid, pageid))
        else :
            pfile = open(os.path.join(svgDir,'page%04d.xhtml' % pageid), 'w')
            slst.append('<a href="svg/page%04d.xhtml">Page %d</a>\n' % (pageid, pageid))
        previd = pageid
        pfile.write(svgxml)
        pfile.close()
        counter += 1
    slst.append('</div>\n')
    slst.append('<h2><a href="svg/toc.xhtml">Table of Contents</a></h2>\n')
    slst.append('</body>\n</html>\n')
    svgindex = "".join(slst)
    slst = None
    open(os.path.join(bookDir, 'index_svg.xhtml'), 'w').write(svgindex)

    print(" ")

    # build the opf file
    opfname = os.path.join(bookDir, 'book.opf')
    olst = []
    olst.append('<?xml version="1.0" encoding="utf-8"?>\n')
    olst.append('<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="guid_id">\n')
    # adding metadata
    olst.append('   <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">\n')
    if b'GUID' in meta_array:
        olst.append('      <dc:identifier opf:scheme="GUID" id="guid_id">' + meta_array[b'GUID'].decode('utf-8') + '</dc:identifier>\n')
    if b'ASIN' in meta_array:
        olst.append('      <dc:identifier opf:scheme="ASIN">' + meta_array[b'ASIN'].decode('utf-8') + '</dc:identifier>\n')
    if b'oASIN' in meta_array:
        olst.append('      <dc:identifier opf:scheme="oASIN">' + meta_array[b'oASIN'].decode('utf-8') + '</dc:identifier>\n')
    olst.append('      <dc:title>' + meta_array[b'Title'].decode('utf-8') + '</dc:title>\n')
    olst.append('      <dc:creator opf:role="aut">' + meta_array[b'Authors'].decode('utf-8') + '</dc:creator>\n')
    olst.append('      <dc:language>en</dc:language>\n')
    olst.append('      <dc:date>' + meta_array[b'UpdateTime'].decode('utf-8') + '</dc:date>\n')
    if isCover:
        olst.append('      <meta name="cover" content="bookcover"/>\n')
    olst.append('   </metadata>\n')
    olst.append('<manifest>\n')
    olst.append('   <item id="book" href="book.html" media-type="application/xhtml+xml"/>\n')
    olst.append('   <item id="stylesheet" href="style.css" media-type="text/css"/>\n')
    # adding image files to manifest
    filenames = os.listdir(imgDir)
    filenames = sorted(filenames)
    for filename in filenames:
        imgname, imgext = os.path.splitext(filename)
        if imgext == '.jpg':
            imgext = 'jpeg'
        if imgext == '.svg':
            imgext = 'svg+xml'
        olst.append('   <item id="' + imgname + '" href="img/' + filename + '" media-type="image/' + imgext + '"/>\n')
    if isCover:
        olst.append('   <item id="bookcover" href="cover.jpg" media-type="image/jpeg" />\n')
    olst.append('</manifest>\n')
    # adding spine
    olst.append('<spine>\n   <itemref idref="book" />\n</spine>\n')
    if isCover:
        olst.append('   <guide>\n')
        olst.append('      <reference href="cover.jpg" type="cover" title="Cover"/>\n')
        olst.append('   </guide>\n')
    olst.append('</package>\n')
    opfstr = "".join(olst)
    olst = None
    open(opfname, 'w').write(opfstr)

    print('Processing Complete')

    return 0

def usage():
    print("genbook.py generates a book from the extract Topaz Files")
    print("Usage:")
    print("    genbook.py [-r] [-h [--fixed-image] <bookDir>  ")
    print("  ")
    print("Options:")
    print("  -h            :  help - print this usage message")
    print("  -r            :  generate raw svg files (not wrapped in xhtml)")
    print("  --fixed-image :  genearate any Fixed Area as an svg image in the html")
    print("  ")


def main(argv):
    sys.stdout=SafeUnbuffered(sys.stdout)
    sys.stderr=SafeUnbuffered(sys.stderr)
    bookDir = ''
    if len(argv) == 0:
        argv = sys.argv

    try:
        opts, args = getopt.getopt(argv[1:], "rh:",["fixed-image"])

    except getopt.GetoptError as err:
        print(str(err))
        usage()
        return 1

    if len(opts) == 0 and len(args) == 0 :
        usage()
        return 1

    raw = 0
    fixedimage = True
    for o, a in opts:
        if o =="-h":
            usage()
            return 0
        if o =="-r":
            raw = 1
        if o =="--fixed-image":
            fixedimage = True

    bookDir = args[0]

    rv = generateBook(bookDir, raw, fixedimage)
    return rv


if __name__ == '__main__':
    sys.exit(main(''))
