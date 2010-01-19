#! /usr/bin/python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

from __future__ import with_statement
import csv
import sys
import os
import getopt
from struct import pack
from struct import unpack


class DocParser(object):
    def __init__(self, flatxml, classlst, fileid):
        self.id = os.path.basename(fileid).replace('.dat','')
        self.flatdoc = flatxml.split('\n')
        self.classList = {}
        tmpList = classlst.split('\n')
        for pclass in tmpList:
            if pclass != '':
                # remove the leading period from the css name
                cname = pclass[1:]
            self.classList[cname] = True
        self.ocrtext = []
        self.link_id = []
        self.link_title = []
        self.link_page = []
        self.dehyphen_rootid = []
        self.paracont_stemid = []
        self.parastems_stemid = []

    # find tag if within pos to end inclusive
    def lineinDoc(self, pos) :
        docList = self.flatdoc
        cnt = len(docList)
        if (pos >= 0) and (pos < cnt) :
            item = docList[pos]
            if item.find('=') >= 0:
                (name, argres) = item.split('=',1)
            else : 
                name = item
                argres = ''
        return name, argres

        
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
        for j in xrange(pos, end):
            item = docList[j]
            if item.find('=') >= 0:
                (name, argres) = item.split('=')
            else : 
                name = item
                argres = ''
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


    # build a description of the paragraph
    def getParaDescription(self, start, end):

        result = []

        # normal paragraph
        (pos, pclass) = self.findinDoc('paragraph.class',start,end) 

        # class names are an issue given topaz may start them with numerals (not allowed),
        # use a mix of cases (which cause some browsers problems), and actually
        # attach numbers after "_reclustered*" to the end to deal with reflow issues
        # but then not actually provide all of these _reclustereed classes in the stylesheet!

        # so we clean this up by lowercasing, prepend 'cl_', and if not in the class
        # list from the stylesheet, trying once more with "_reclustered*" removed
        # if still not in stylesheet, let it pass as is
        pclass = pclass.lower()
        pclass = 'cl_' + pclass
        if pclass not in self.classList:
            p = pclass.find('_reclustered')
            if p > 0 : 
                baseclass = pclass[0:p]
                if baseclass in self.classList:
                    pclass = baseclass

        # build up a description of the paragraph in result and return it
        # first check for the  basic - all words paragraph
        (pos, sfirst) = self.findinDoc('paragraph.firstWord',start,end)
        (pos, slast) = self.findinDoc('paragraph.lastWord',start,end)
        if (sfirst != None) and (slast != None) :
            first = int(sfirst)
            last = int(slast)
            for wordnum in xrange(first, last):
                result.append(('ocr', wordnum))
            return pclass, result

        # this type of paragrph may be made up of multiple _spans, inline 
        # word monograms (images) and words with semantic meaning
        
        # need to parse this type line by line
        line = start + 1
        word_class = ''

        while (line < end) :

            (name, argres) = self.lineinDoc(line)

            if name.endswith('_span.firstWord') :
                first = int(argres)
                (name, argres) = self.lineinDoc(line+1)
                if not name.endswith('_span.lastWord'):
                    print 'Error: - incorrect _span ordering inside paragraph'
                last = int(argres)
                for wordnum in xrange(first, last):
                    result.append(('ocr', wordnum))
                line += 1

            elif name.endswith('word.class'):
               (cname, space) = argres.split('-',1)
               if cname == 'spaceafter':
                   word_class = 'sa'

            elif name.endswith('word.img.src'):
                result.append(('img' + word_class, int(argres)))
                word_class = ''

            elif name.endswith('word_semantic.firstWord'):
                first = int(argres)
                (name, argres) = self.lineinDoc(line+1)
                if not name.endswith('word_semantic.lastWord'):
                    print 'Error: - incorrect word_semantic ordering inside paragraph'
                last = int(argres)
                for wordnum in xrange(first, last):
                    result.append(('ocr', wordnum))
                line += 1
                              
            line += 1

        return pclass, result
                            

    def buildParagraph(self, cname, pdesc, type, regtype) :
        parares = ''
        sep =''

        br_lb = False
        if (regtype == 'fixed') or (regtype == 'chapterheading') :
            br_lb = True

        handle_links = False
        if len(self.link_id) > 0:
            handle_links = True

        if (type == 'full') or (type == 'begin') :
            parares += '<p class="' + cname + '">'

        if (type == 'end'):
            parares += ' '

        cnt = len(pdesc)

        for j in xrange( 0, cnt) :

            (wtype, num) = pdesc[j]

            if wtype == 'ocr' :
                word = self.ocrtext[num]
                sep = ' '

                if handle_links:
                    link = self.link_id[num]
                    if (link > 0): 
                        title = self.link_title[link-1]
                        if title == "": title='_link_'
                        ptarget = self.link_page[link-1] - 1
                        linkhtml = '<a href="#page%04d">' % ptarget
                        linkhtml += title + '</a>'
                        pos = parares.rfind(title)
                        if pos >= 0:
                            parares = parares[0:pos] + linkhtml + parares[pos+len(title):]
                        else :
                            parares += linkhtml
                        if word == '_link_' : word = ''
                    elif (link < 0) :
                        if word == '_link_' : word = ''

                if word == '_lb_':
                    if (num-1) in self.dehyphen_rootid :
                        word = ''
                        sep = ''
                    elif handle_links :
                        word = ''
                        sep = ''
                    elif br_lb :
                        word = '<br />\n'
                        sep = ''
                    else :
                        word = '\n'
                        sep = ''

                if num in self.dehyphen_rootid :
                    word = word[0:-1]
                    sep = ''

                parares += word + sep

            elif wtype == 'img' :
                sep = ''
                parares += '<img src="img/img%04d.jpg" alt="" />' % num
                parares += sep

            elif wtype == 'imgsa' :
                sep = ' '
                parares += '<img src="img/img%04d.jpg" alt="" />' % num
                parares += sep

        if len(sep) > 0 : parares = parares[0:-1]
        if (type == 'full') or (type == 'end') :
            parares += '</p>'
        return parares


    
    # walk the document tree collecting the information needed
    # to build an html page using the ocrText

    def process(self):

        htmlpage = ''

        # first collect information from the xml doc that describes this page
        (pos, argres) = self.findinDoc('info.word.ocrText',0,-1)
        if argres :  self.ocrtext = argres.split('|')

        (pos, argres) = self.findinDoc('info.dehyphen.rootID',0,-1)
        if argres: 
            argList = argres.split('|')
            self.dehyphen_rootid = [ int(strval) for strval in argList]

        (pos, self.parastems_stemid) = self.findinDoc('info.paraStems.stemID',0,-1)
        if self.parastems_stemid == None : self.parastems_stemid = []
 
        (pos, self.paracont_stemid) = self.findinDoc('info.paraCont.stemID',0,-1)
        if self.paracont_stemid == None : self.paracont_stemid = []


        (pos, argres) = self.findinDoc('info.word.link_id',0,-1)
        if argres:
            argList = argres.split('|')
            self.link_id = [ int(strval) for strval in argList]

        (pos, argres) = self.findinDoc('info.links.page',0,-1)
        if argres :
            argList = argres.split('|')
            self.link_page = [ int(strval) for strval in argList]

        (pos, argres) = self.findinDoc('info.links.title',0,-1)
        if argres :
            self.link_title = argres.split('|')
        else:
            self.link_title.append('')

        (pos, pagetype) = self.findinDoc('page.type',0,-1)


        # generate a list of each region starting point
        # each region has one paragraph,, or one image, or one chapterheading
        regionList= self.posinDoc('region')
        regcnt = len(regionList)
        regionList.append(-1)

        anchorSet = False
        breakSet = False

        # process each region tag and convert what you can to html

        for j in xrange(regcnt):
            start = regionList[j]
            end = regionList[j+1]

            (pos, regtype) = self.findinDoc('region.type',start,end)

            if regtype == 'graphic' :
                if not anchorSet:
                    htmlpage += '<div id="' + self.id + '" class="page_' + pagetype + '">&nbsp</div>\n'
                    anchorSet = True
                (pos, simgsrc) = self.findinDoc('img.src',start,end)
                if simgsrc:
                    htmlpage += '<div class="graphic"><img src="img/img%04d.jpg" alt="" /></div>' % int(simgsrc)
            
            elif regtype == 'chapterheading' :
                (pclass, pdesc) = self.getParaDescription(start,end)
                if not breakSet:
                    htmlpage += '<div style="page-break-after: always;">&nbsp;</div>\n'
                    breakSet = True
                if not anchorSet:
                    htmlpage += '<div id="' + self.id + '" class="page_' + pagetype + '">&nbsp</div>\n'
                    anchorSet = True
                tag = 'h1'
                if pclass[3:7] == 'ch1-' : tag = 'h1'
                if pclass[3:7] == 'ch2-' : tag = 'h2'
                if pclass[3:7] == 'ch3-' : tag = 'h3'
                htmlpage += '<' + tag + ' class="' + pclass + '">'
                htmlpage += self.buildParagraph(pclass, pdesc, 'middle', regtype)
                htmlpage += '</' + tag + '>'

            elif (regtype == 'text') or (regtype == 'fixed') or (regtype == 'insert') :
                ptype = 'full'
                # check to see if this is a continution from the previous page
                if (len(self.parastems_stemid) > 0):
                    ptype = 'end'
                    self.parastems_stemid=[]
                else:
                    if not anchorSet:
                        htmlpage += '<div id="' + self.id + '" class="page_' + pagetype + '">&nbsp</div>\n'
                        anchorSet = True
                (pclass, pdesc) = self.getParaDescription(start,end)
                if ptype == 'full' :
                    tag = 'p'
                    if pclass[3:6] == 'h1-' : tag = 'h4'
                    if pclass[3:6] == 'h2-' : tag = 'h5'
                    if pclass[3:6] == 'h3-' : tag = 'h6'
                    htmlpage += '<' + tag + ' class="' + pclass + '">'
                    htmlpage += self.buildParagraph(pclass, pdesc, 'middle', regtype)
                    htmlpage += '</' + tag + '>'
                else :
                    htmlpage += self.buildParagraph(pclass, pdesc, ptype, regtype)


            elif (regtype == 'tocentry') :
                ptype = 'full'
                # check to see if this is a continution from the previous page
                if (len(self.parastems_stemid) > 0) and (j == 0):
                    # process the first paragraph as a continuation from the last page
                    ptype = 'end'
                    self.parastems_stemid = []
                else:
                    if not anchorSet:
                        htmlpage += '<div id="' + self.id + '" class="page_' + pagetype + '">&nbsp</div>\n'
                        anchorSet = True
                (pclass, pdesc) = self.getParaDescription(start,end)
                htmlpage += self.buildParagraph(pclass, pdesc, ptype, regtype)

            elif regtype == 'synth_fcvr.center' :
                if not anchorSet:
                    htmlpage += '<div id="' + self.id + '" class="page_' + pagetype + '">&nbsp</div>\n'
                    anchorSet = True
                (pos, simgsrc) = self.findinDoc('img.src',start,end)
                if simgsrc:
                    htmlpage += '<div class="graphic"><img src="img/img%04d.jpg" alt="" /></div>' % int(simgsrc)

            else :
                print 'Warning: Unknown region type', regtype
                print 'Treating this like a "fixed" region'
                regtype = 'fixed'
                ptype = 'full'
                # check to see if this is a continution from the previous page
                if (len(self.parastems_stemid) > 0):
                    ptype = 'end'
                    self.parastems_stemid=[]
                else:
                    if not anchorSet:
                        htmlpage += '<div id="' + self.id + '" class="page_' + pagetype + '">&nbsp</div>\n'
                        anchorSet = True
                (pclass, desc) = self.getParaDescription(start,end)
                if ptype == 'full' :
                    tag = 'p'
                    if pclass[3:6] == 'h1-' : tag = 'h4'
                    if pclass[3:6] == 'h2-' : tag = 'h5'
                    if pclass[3:6] == 'h3-' : tag = 'h6'
                    htmlpage += '<' + tag + ' class="' + pclass + '">'
                    htmlpage += self.buildParagraph(pclass, pdesc, 'middle', regtype)
                    htmlpage += '</' + tag + '>'
                else :
                    htmlpage += self.buildParagraph(pclass, pdesc, ptype, regtype)



        if len(self.paracont_stemid) > 0 :
            if htmlpage[-4:] == '</p>':
                htmlpage = htmlpage[0:-4]    

        return htmlpage


        return self.convert2HTML()



def convert2HTML(flatxml, classlst, fileid):

    # create a document parser
    dp = DocParser(flatxml, classlst, fileid)

    htmlpage = dp.process()

    return htmlpage
