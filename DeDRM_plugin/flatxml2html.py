#! /usr/bin/python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# For use with Topaz Scripts Version 2.6

import sys
import csv
import os
import math
import getopt
import functools
from struct import pack
from struct import unpack


class DocParser(object):
    def __init__(self, flatxml, classlst, fileid, bookDir, gdict, fixedimage):
        self.id = os.path.basename(fileid).replace('.dat','')
        self.svgcount = 0
        self.docList = flatxml.split(b'\n')
        self.docSize = len(self.docList)
        self.classList = {}
        self.bookDir = bookDir
        self.gdict = gdict
        tmpList = classlst.split('\n')
        for pclass in tmpList:
            if pclass != b'':
                # remove the leading period from the css name
                cname = pclass[1:]
            self.classList[cname] = True
        self.fixedimage = fixedimage
        self.ocrtext = []
        self.link_id = []
        self.link_title = []
        self.link_page = []
        self.link_href = []
        self.link_type = []
        self.dehyphen_rootid = []
        self.paracont_stemid = []
        self.parastems_stemid = []


    def getGlyph(self, gid):
        result = ''
        id='id="gl%d"' % gid
        return self.gdict.lookup(id)

    def glyphs_to_image(self, glyphList):

        def extract(path, key):
            b = path.find(key) + len(key)
            e = path.find(' ',b)
            return int(path[b:e])

        svgDir = os.path.join(self.bookDir,'svg')

        imgDir = os.path.join(self.bookDir,'img')
        imgname = self.id + '_%04d.svg' % self.svgcount
        imgfile = os.path.join(imgDir,imgname)

        # get glyph information
        gxList = self.getData(b'info.glyph.x',0,-1)
        gyList = self.getData(b'info.glyph.y',0,-1)
        gidList = self.getData(b'info.glyph.glyphID',0,-1)

        gids = []
        maxws = []
        maxhs = []
        xs = []
        ys = []
        gdefs = []

        # get path defintions, positions, dimensions for each glyph
        # that makes up the image, and find min x and min y to reposition origin
        minx = -1
        miny = -1
        for j in glyphList:
            gid = gidList[j]
            gids.append(gid)

            xs.append(gxList[j])
            if minx == -1: minx = gxList[j]
            else : minx = min(minx, gxList[j])

            ys.append(gyList[j])
            if miny == -1: miny = gyList[j]
            else : miny = min(miny, gyList[j])

            path = self.getGlyph(gid)
            gdefs.append(path)

            maxws.append(extract(path,'width='))
            maxhs.append(extract(path,'height='))


        # change the origin to minx, miny and calc max height and width
        maxw = maxws[0] + xs[0] - minx
        maxh = maxhs[0] + ys[0] - miny
        for j in range(0, len(xs)):
            xs[j] = xs[j] - minx
            ys[j] = ys[j] - miny
            maxw = max( maxw, (maxws[j] + xs[j]) )
            maxh = max( maxh, (maxhs[j] + ys[j]) )

        # open the image file for output
        ifile = open(imgfile,'w')
        ifile.write('<?xml version="1.0" standalone="no"?>\n')
        ifile.write('<!DOCTYPE svg PUBLIC "-//W3C/DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n')
        ifile.write('<svg width="%dpx" height="%dpx" viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1">\n' % (math.floor(maxw/10), math.floor(maxh/10), maxw, maxh))
        ifile.write('<defs>\n')
        for j in range(0,len(gdefs)):
            ifile.write(gdefs[j])
        ifile.write('</defs>\n')
        for j in range(0,len(gids)):
            ifile.write('<use xlink:href="#gl%d" x="%d" y="%d" />\n' % (gids[j], xs[j], ys[j]))
        ifile.write('</svg>')
        ifile.close()

        return 0



    # return tag at line pos in document
    def lineinDoc(self, pos) :
        if (pos >= 0) and (pos < self.docSize) :
            item = self.docList[pos]
            if item.find(b'=') >= 0:
                (name, argres) = item.split(b'=',1)
            else :
                name = item
                argres = b''
        return name, argres


    # find tag in doc if within pos to end inclusive
    def findinDoc(self, tagpath, pos, end) :
        result = None
        if end == -1 :
            end = self.docSize
        else:
            end = min(self.docSize, end)
        foundat = -1
        for j in range(pos, end):
            item = self.docList[j]
            if item.find(b'=') >= 0:
                (name, argres) = item.split(b'=',1)
            else :
                name = item
                argres = ''
            if (isinstance(tagpath,str)):
                tagpath = tagpath.encode('utf-8')
            if name.endswith(tagpath) :
                result = argres
                foundat = j
                break
        return foundat, result


    # return list of start positions for the tagpath
    def posinDoc(self, tagpath):
        startpos = []
        pos = 0
        res = ""
        while res != None :
            (foundpos, res) = self.findinDoc(tagpath, pos, -1)
            if res != None :
                startpos.append(foundpos)
            pos = foundpos + 1
        return startpos


    # returns a vector of integers for the tagpath
    def getData(self, tagpath, pos, end):
        argres=[]
        (foundat, argt) = self.findinDoc(tagpath, pos, end)
        if (argt != None) and (len(argt) > 0) :
            argList = argt.split(b'|')
            argres = [ int(strval) for strval in argList]
        return argres


    # get the class
    def getClass(self, pclass):
        nclass = pclass

        # class names are an issue given topaz may start them with numerals (not allowed),
        # use a mix of cases (which cause some browsers problems), and actually
        # attach numbers after "_reclustered*" to the end to deal classeses that inherit
        # from a base class (but then not actually provide all of these _reclustereed
        # classes in the stylesheet!

        # so we clean this up by lowercasing, prepend 'cl-', and getting any baseclass
        # that exists in the stylesheet first, and then adding this specific class
        # after

        # also some class names have spaces in them so need to convert to dashes
        if nclass != None :
            nclass = nclass.replace(b' ',b'-')
            classres = b''
            nclass = nclass.lower()
            nclass = b'cl-' + nclass
            baseclass = b''
            # graphic is the base class for captions
            if nclass.find(b'cl-cap-') >=0 :
                classres = b'graphic' + b' '
            else :
                # strip to find baseclass
                p = nclass.find(b'_')
                if p > 0 :
                    baseclass = nclass[0:p]
                    if baseclass in self.classList:
                        classres += baseclass + b' '
            classres += nclass
            nclass = classres
        return nclass


    # develop a sorted description of the starting positions of
    # groups and regions on the page, as well as the page type
    def PageDescription(self):

        def compare(x, y):
            (xtype, xval) = x
            (ytype, yval) = y
            if xval > yval:
                return 1
            if xval == yval:
                return 0
            return -1

        result = []
        (pos, pagetype) = self.findinDoc(b'page.type',0,-1)

        groupList = self.posinDoc(b'page.group')
        groupregionList = self.posinDoc(b'page.group.region')
        pageregionList = self.posinDoc(b'page.region')
        # integrate into one list
        for j in groupList:
            result.append(('grpbeg',j))
        for j in groupregionList:
            result.append(('gregion',j))
        for j in pageregionList:
            result.append(('pregion',j))
        result.sort(key=functools.cmp_to_key(compare))

        # insert group end and page end indicators
        inGroup = False
        j = 0
        while True:
            if j == len(result): break
            rtype = result[j][0]
            rval = result[j][1]
            if not inGroup and (rtype == 'grpbeg') :
                inGroup = True
                j = j + 1
            elif inGroup and (rtype in ('grpbeg', 'pregion')):
                result.insert(j,('grpend',rval))
                inGroup = False
            else:
                j = j + 1
        if inGroup:
            result.append(('grpend',-1))
        result.append(('pageend', -1))
        return pagetype, result



    # build a description of the paragraph
    def getParaDescription(self, start, end, regtype):

        result = []

        # paragraph
        (pos, pclass) = self.findinDoc(b'paragraph.class',start,end)

        pclass = self.getClass(pclass)

        # if paragraph uses extratokens (extra glyphs) then make it fixed
        (pos, extraglyphs) = self.findinDoc(b'paragraph.extratokens',start,end)

        # build up a description of the paragraph in result and return it
        # first check for the  basic - all words paragraph
        (pos, sfirst) = self.findinDoc(b'paragraph.firstWord',start,end)
        (pos, slast) = self.findinDoc(b'paragraph.lastWord',start,end)
        if (sfirst != None) and (slast != None) :
            first = int(sfirst)
            last = int(slast)

            makeImage = (regtype == b'vertical') or (regtype == b'table')
            makeImage = makeImage or (extraglyphs != None)
            if self.fixedimage:
                makeImage = makeImage or (regtype == b'fixed')

            if (pclass != None):
                makeImage = makeImage or (pclass.find(b'.inverted') >= 0)
                if self.fixedimage :
                    makeImage = makeImage or (pclass.find(b'cl-f-') >= 0)

            # before creating an image make sure glyph info exists
            gidList = self.getData(b'info.glyph.glyphID',0,-1)

            makeImage = makeImage & (len(gidList) > 0)

            if not makeImage :
                # standard all word paragraph
                for wordnum in range(first, last):
                    result.append(('ocr', wordnum))
                return pclass, result

            # convert paragraph to svg image
            # translate first and last word into first and last glyphs
            # and generate inline image and include it
            glyphList = []
            firstglyphList = self.getData(b'word.firstGlyph',0,-1)
            gidList = self.getData(b'info.glyph.glyphID',0,-1)
            firstGlyph = firstglyphList[first]
            if last < len(firstglyphList):
                lastGlyph = firstglyphList[last]
            else :
                lastGlyph = len(gidList)

            # handle case of white sapce paragraphs with no actual glyphs in them
            # by reverting to text based paragraph
            if firstGlyph >= lastGlyph:
                # revert to standard text based paragraph
                for wordnum in range(first, last):
                    result.append(('ocr', wordnum))
                return pclass, result

            for glyphnum in range(firstGlyph, lastGlyph):
                glyphList.append(glyphnum)
            # include any extratokens if they exist
            (pos, sfg) = self.findinDoc(b'extratokens.firstGlyph',start,end)
            (pos, slg) = self.findinDoc(b'extratokens.lastGlyph',start,end)
            if (sfg != None) and (slg != None):
                for glyphnum in range(int(sfg), int(slg)):
                    glyphList.append(glyphnum)
            num = self.svgcount
            self.glyphs_to_image(glyphList)
            self.svgcount += 1
            result.append(('svg', num))
            return pclass, result

        # this type of paragraph may be made up of multiple spans, inline
        # word monograms (images), and words with semantic meaning,
        # plus glyphs used to form starting letter of first word

        # need to parse this type line by line
        line = start + 1
        word_class = ''

        # if end is -1 then we must search to end of document
        if end == -1 :
            end = self.docSize

        # seems some xml has last* coming before first* so we have to
        # handle any order
        sp_first = -1
        sp_last = -1

        gl_first = -1
        gl_last = -1

        ws_first = -1
        ws_last = -1

        word_class = ''

        word_semantic_type = ''

        while (line < end) :

            (name, argres) = self.lineinDoc(line)

            if name.endswith(b'span.firstWord') :
                sp_first = int(argres)

            elif name.endswith(b'span.lastWord') :
                sp_last = int(argres)

            elif name.endswith(b'word.firstGlyph') :
                gl_first = int(argres)

            elif name.endswith(b'word.lastGlyph') :
                gl_last = int(argres)

            elif name.endswith(b'word_semantic.firstWord'):
                ws_first = int(argres)

            elif name.endswith(b'word_semantic.lastWord'):
                ws_last = int(argres)

            elif name.endswith(b'word.class'):
                # we only handle spaceafter word class
                try:
                    (cname, space) = argres.split(b'-',1)
                    if space == b'' : space = b'0'
                    if (cname == b'spaceafter') and (int(space) > 0) :
                        word_class = 'sa'
                except:
                    pass

            elif name.endswith(b'word.img.src'):
                result.append(('img' + word_class, int(argres)))
                word_class = ''

            elif name.endswith(b'region.img.src'):
                result.append(('img' + word_class, int(argres)))

            if (sp_first != -1) and (sp_last != -1):
                for wordnum in range(sp_first, sp_last):
                    result.append(('ocr', wordnum))
                sp_first = -1
                sp_last = -1

            if (gl_first != -1) and (gl_last != -1):
                glyphList = []
                for glyphnum in range(gl_first, gl_last):
                    glyphList.append(glyphnum)
                num = self.svgcount
                self.glyphs_to_image(glyphList)
                self.svgcount += 1
                result.append(('svg', num))
                gl_first = -1
                gl_last = -1

            if (ws_first != -1) and (ws_last != -1):
                for wordnum in range(ws_first, ws_last):
                    result.append(('ocr', wordnum))
                ws_first = -1
                ws_last = -1

            line += 1

        return pclass, result


    def buildParagraph(self, pclass, pdesc, type, regtype) :
        parares = ''
        sep =''

        classres = ''
        if pclass :
            classres = ' class="' + pclass.decode('utf-8') + '"'

        br_lb = (regtype == 'fixed') or (regtype == 'chapterheading') or (regtype == 'vertical')

        handle_links = len(self.link_id) > 0

        if (type == 'full') or (type == 'begin') :
            parares += '<p' + classres + '>'

        if (type == 'end'):
            parares += ' '

        lstart = len(parares)

        cnt = len(pdesc)

        for j in range( 0, cnt) :

            (wtype, num) = pdesc[j]

            if wtype == 'ocr' :
                try:
                    word = self.ocrtext[num]
                except:
                    word = ""

                sep = ' '

                if handle_links:
                    link = self.link_id[num]
                    if (link > 0):
                        linktype = self.link_type[link-1]
                        title = self.link_title[link-1]
                        if isinstance(title, bytes):
                            title = title.decode('utf-8')
                        if (title == "") or (parares.rfind(title) < 0):
                            title=parares[lstart:]
                        if linktype == 'external' :
                            linkhref = self.link_href[link-1]
                            linkhtml = '<a href="%s">' % linkhref
                        else :
                            if len(self.link_page) >= link :
                                ptarget = self.link_page[link-1] - 1
                                linkhtml = '<a href="#page%04d">' % ptarget
                            else :
                                # just link to the current page
                                linkhtml = '<a href="#' + self.id + '">'
                        linkhtml += title
                        linkhtml += '</a>'
                        pos = parares.rfind(title)
                        if pos >= 0:
                            parares = parares[0:pos] + linkhtml + parares[pos+len(title):]
                        else :
                            parares += linkhtml
                        lstart = len(parares)
                        if word == b'_link_' : word = b''
                    elif (link < 0) :
                        if word == b'_link_' : word = b''

                if word == b'_lb_':
                    if ((num-1) in self.dehyphen_rootid ) or handle_links:
                        word = b''
                        sep = ''
                    elif br_lb :
                        word = b'<br />\n'
                        sep = ''
                    else :
                        word = b'\n'
                        sep = ''

                if num in self.dehyphen_rootid :
                    word = word[0:-1]
                    sep = ''

                parares += word.decode('utf-8') + sep

            elif wtype == 'img' :
                sep = ''
                parares += '<img src="img/img%04d.jpg" alt="" />' % num
                parares += sep

            elif wtype == 'imgsa' :
                sep = ' '
                parares += '<img src="img/img%04d.jpg" alt="" />' % num
                parares += sep

            elif wtype == 'svg' :
                sep = ''
                parares += '<img src="img/'
                parares += self.id
                parares += '_%04d.svg" alt="" />' % num
                parares += sep

        if len(sep) > 0 : parares = parares[0:-1]
        if (type == 'full') or (type == 'end') :
            parares += '</p>'
        return parares


    def buildTOCEntry(self, pdesc) :
        parares = ''
        sep =''
        tocentry = ''
        handle_links = len(self.link_id) > 0

        lstart = 0

        cnt = len(pdesc)
        for j in range( 0, cnt) :

            (wtype, num) = pdesc[j]

            if wtype == 'ocr' :
                word = self.ocrtext[num].decode('utf-8')
                sep = ' '

                if handle_links:
                    link = self.link_id[num]
                    if (link > 0):
                        linktype = self.link_type[link-1]
                        title = self.link_title[link-1]
                        title = title.rstrip(b'. ').decode('utf-8')
                        alt_title = parares[lstart:]
                        alt_title = alt_title.strip()
                        # now strip off the actual printed page number
                        alt_title = alt_title.rstrip('01234567890ivxldIVXLD-.')
                        alt_title = alt_title.rstrip('. ')
                        # skip over any external links - can't have them in a books toc
                        if linktype == 'external' :
                            title = ''
                            alt_title = ''
                            linkpage = ''
                        else :
                            if len(self.link_page) >= link :
                                ptarget = self.link_page[link-1] - 1
                                linkpage = '%04d' % ptarget
                            else :
                                # just link to the current page
                                linkpage = self.id[4:]
                        if len(alt_title) >= len(title):
                            title = alt_title
                        if title != '' and linkpage != '':
                            tocentry += title + '|' + linkpage + '\n'
                        lstart = len(parares)
                        if word == '_link_' : word = ''
                    elif (link < 0) :
                        if word == '_link_' : word = ''

                if word == '_lb_':
                    word = ''
                    sep = ''

                if num in self.dehyphen_rootid :
                    word = word[0:-1]
                    sep = ''

                parares += word + sep

            else :
                continue

        return tocentry




    # walk the document tree collecting the information needed
    # to build an html page using the ocrText

    def process(self):

        tocinfo = ''
        hlst = []

        # get the ocr text
        (pos, argres) = self.findinDoc(b'info.word.ocrText',0,-1)
        if argres :  self.ocrtext = argres.split(b'|')

        # get information to dehyphenate the text
        self.dehyphen_rootid = self.getData(b'info.dehyphen.rootID',0,-1)

        # determine if first paragraph is continued from previous page
        (pos, self.parastems_stemid) = self.findinDoc(b'info.paraStems.stemID',0,-1)
        first_para_continued = (self.parastems_stemid  != None)

        # determine if last paragraph is continued onto the next page
        (pos, self.paracont_stemid) = self.findinDoc(b'info.paraCont.stemID',0,-1)
        last_para_continued = (self.paracont_stemid != None)

        # collect link ids
        self.link_id = self.getData(b'info.word.link_id',0,-1)

        # collect link destination page numbers
        self.link_page = self.getData(b'info.links.page',0,-1)

        # collect link types (container versus external)
        (pos, argres) = self.findinDoc(b'info.links.type',0,-1)
        if argres :  self.link_type = argres.split(b'|')

        # collect link destinations
        (pos, argres) = self.findinDoc(b'info.links.href',0,-1)
        if argres :  self.link_href = argres.split(b'|')

        # collect link titles
        (pos, argres) = self.findinDoc(b'info.links.title',0,-1)
        if argres :
            self.link_title = argres.split(b'|')
        else:
            self.link_title.append('')

        # get a descriptions of the starting points of the regions
        # and groups on the page
        (pagetype, pageDesc) = self.PageDescription()
        regcnt = len(pageDesc) - 1

        anchorSet = False
        breakSet = False
        inGroup = False

        # process each region on the page and convert what you can to html

        for j in range(regcnt):

            (etype, start) = pageDesc[j]
            (ntype, end) = pageDesc[j+1]


            # set anchor for link target on this page
            if not anchorSet and not first_para_continued:
                hlst.append('<div style="visibility: hidden; height: 0; width: 0;" id="')
                hlst.append(self.id + '" title="pagetype_' + pagetype.decode('utf-8') + '"></div>\n')
                anchorSet = True

            # handle groups of graphics with text captions
            if (etype == b'grpbeg'):
                (pos, grptype) = self.findinDoc(b'group.type', start, end)
                if grptype != None:
                    if grptype == b'graphic':
                        gcstr = ' class="' + grptype.decode('utf-8') + '"'
                        hlst.append('<div' + gcstr + '>')
                        inGroup = True

            elif (etype == b'grpend'):
                if inGroup:
                    hlst.append('</div>\n')
                    inGroup = False

            else:
                (pos, regtype) = self.findinDoc(b'region.type',start,end)

                if regtype == b'graphic' :
                    (pos, simgsrc) = self.findinDoc(b'img.src',start,end)
                    if simgsrc:
                        if inGroup:
                            hlst.append('<img src="img/img%04d.jpg" alt="" />' % int(simgsrc))
                        else:
                            hlst.append('<div class="graphic"><img src="img/img%04d.jpg" alt="" /></div>' % int(simgsrc))

                elif regtype == b'chapterheading' :
                    (pclass, pdesc) = self.getParaDescription(start,end, regtype)
                    if not breakSet:
                        hlst.append('<div style="page-break-after: always;">&nbsp;</div>\n')
                        breakSet = True
                    tag = 'h1'
                    if pclass and (len(pclass) >= 7):
                        if pclass[3:7] == b'ch1-' : tag = 'h1'
                        if pclass[3:7] == b'ch2-' : tag = 'h2'
                        if pclass[3:7] == b'ch3-' : tag = 'h3'
                        hlst.append('<' + tag + ' class="' + pclass.decode('utf-8') + '">')
                    else:
                        hlst.append('<' + tag + '>')
                    hlst.append(self.buildParagraph(pclass, pdesc, 'middle', regtype))
                    hlst.append('</' + tag + '>')

                elif (regtype == b'text') or (regtype == b'fixed') or (regtype == b'insert') or (regtype == b'listitem'):
                    ptype = 'full'
                    # check to see if this is a continution from the previous page
                    if first_para_continued :
                        ptype = 'end'
                        first_para_continued = False
                    (pclass, pdesc) = self.getParaDescription(start,end, regtype)
                    if pclass and (len(pclass) >= 6) and (ptype == 'full'):
                        tag = 'p'
                        if pclass[3:6] == b'h1-' : tag = 'h4'
                        if pclass[3:6] == b'h2-' : tag = 'h5'
                        if pclass[3:6] == b'h3-' : tag = 'h6'
                        hlst.append('<' + tag + ' class="' + pclass.decode('utf-8') + '">')
                        hlst.append(self.buildParagraph(pclass, pdesc, 'middle', regtype))
                        hlst.append('</' + tag + '>')
                    else :
                        hlst.append(self.buildParagraph(pclass, pdesc, ptype, regtype))

                elif (regtype == b'tocentry') :
                    ptype = 'full'
                    if first_para_continued :
                        ptype = 'end'
                        first_para_continued = False
                    (pclass, pdesc) = self.getParaDescription(start,end, regtype)
                    tocinfo += self.buildTOCEntry(pdesc)
                    hlst.append(self.buildParagraph(pclass, pdesc, ptype, regtype))

                elif (regtype == b'vertical') or (regtype == b'table') :
                    ptype = 'full'
                    if inGroup:
                        ptype = 'middle'
                    if first_para_continued :
                        ptype = 'end'
                        first_para_continued = False
                    (pclass, pdesc) = self.getParaDescription(start, end, regtype)
                    hlst.append(self.buildParagraph(pclass, pdesc, ptype, regtype))


                elif (regtype == b'synth_fcvr.center'):
                    (pos, simgsrc) = self.findinDoc(b'img.src',start,end)
                    if simgsrc:
                        hlst.append('<div class="graphic"><img src="img/img%04d.jpg" alt="" /></div>' % int(simgsrc))

                else :
                    print('          Making region type', regtype, end=' ')
                    (pos, temp) = self.findinDoc(b'paragraph',start,end)
                    (pos2, temp) = self.findinDoc(b'span',start,end)
                    if pos != -1 or pos2 != -1:
                        print(' a "text" region')
                        orig_regtype = regtype
                        regtype = b'fixed'
                        ptype = 'full'
                        # check to see if this is a continution from the previous page
                        if first_para_continued :
                            ptype = 'end'
                            first_para_continued = False
                        (pclass, pdesc) = self.getParaDescription(start,end, regtype)
                        if not pclass:
                            if orig_regtype.endswith(b'.right')     : pclass = b'cl-right'
                            elif orig_regtype.endswith(b'.center')  : pclass = b'cl-center'
                            elif orig_regtype.endswith(b'.left')    : pclass = b'cl-left'
                            elif orig_regtype.endswith(b'.justify') : pclass = b'cl-justify'
                        if pclass and (ptype == 'full') and (len(pclass) >= 6):
                            tag = 'p'
                            if pclass[3:6] == b'h1-' : tag = 'h4'
                            if pclass[3:6] == b'h2-' : tag = 'h5'
                            if pclass[3:6] == b'h3-' : tag = 'h6'
                            hlst.append('<' + tag + ' class="' + pclass.decode('utf-8') + '">')
                            hlst.append(self.buildParagraph(pclass, pdesc, 'middle', regtype))
                            hlst.append('</' + tag + '>')
                        else :
                            hlst.append(self.buildParagraph(pclass, pdesc, ptype, regtype))
                    else :
                        print(' a "graphic" region')
                        (pos, simgsrc) = self.findinDoc(b'img.src',start,end)
                        if simgsrc:
                            hlst.append('<div class="graphic"><img src="img/img%04d.jpg" alt="" /></div>' % int(simgsrc))


        htmlpage = "".join(hlst)
        if last_para_continued :
            if htmlpage[-4:] == '</p>':
                htmlpage = htmlpage[0:-4]
            last_para_continued = False

        return htmlpage, tocinfo


def convert2HTML(flatxml, classlst, fileid, bookDir, gdict, fixedimage):
    # create a document parser
    dp = DocParser(flatxml, classlst, fileid, bookDir, gdict, fixedimage)
    htmlpage, tocinfo = dp.process()
    return htmlpage, tocinfo
