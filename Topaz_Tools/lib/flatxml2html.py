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
    def __init__(self, flatxml, fileid):
        self.id = os.path.basename(fileid).replace('.dat','')
        self.flatdoc = flatxml.split('\n')
        self.ocrtext = []
        self.link_id = []
        self.link_title = []
        self.link_page = []
        self.dehyphen_rootid = []
        self.paracont_stemid = []
        self.parastems_stemid = []


        
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


    # get a description of the paragraph
    def getParaDescription(self, start, end):
        # normal paragraph
        (pos, pclass) = self.findinDoc('paragraph.class',start,end) 

        # class names are an issue given topaz starts them with numerals (not allowed)
        # use a mix of cases, (which cause some browsers problems), and actually
        # attach numbers after "reclustered*" to the end to deal with reflow issues
        # so we clean this up by lowercasing, prepend 'cl_', and remove all end pieces after reclustered
        pclass = pclass.lower()
        pclass = 'cl_' + pclass
        p = pclass.find('reclustered')
        if p > 0 : pclass = pclass[0:p+11]

        (pos, sfirst) = self.findinDoc('paragraph.firstWord',start,end)
        (pos, slast) = self.findinDoc('paragraph.lastWord',start,end)
        if (sfirst != None) and (slast != None) :
            return pclass, int(sfirst), int(slast)

        # some paragraphs are instead split into multiple spans and some even have word_semantic tags as well
        # so walk through this region keeping track of the first firstword, and the last lastWord
        # on any items that have it
        (pos, sfirst) = self.findinDoc('firstWord',start, end)
        first = int(sfirst)
        last = -1
        for i in xrange(pos+1,end):
            (pos, slast) = self.findinDoc('lastWord',i,i+1)
            if slast != None:
                last = int(slast)
        return pclass, first, last


    def buildParagraph(self, cname, first, last, type, regtype) :
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
        for j in xrange(first, last) :
            word = self.ocrtext[j]
            sep = ' '

            if handle_links:
                link = self.link_id[j]
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
                if (j-1) in self.dehyphen_rootid :
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

            if j in self.dehyphen_rootid :
                word = word[0:-1]
                sep = ''

            parares += word + sep

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
                (pclass, first, last) = self.getParaDescription(start,end)
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
                htmlpage += self.buildParagraph(pclass,first,last,'middle', regtype)
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
                (pclass, first, last) = self.getParaDescription(start,end)
                if ptype == 'full' :
                    tag = 'p'
                    if pclass[3:6] == 'h1-' : tag = 'h4'
                    if pclass[3:6] == 'h2-' : tag = 'h5'
                    if pclass[3:6] == 'h3-' : tag = 'h6'
                    htmlpage += '<' + tag + ' class="' + pclass + '">'
                    htmlpage += self.buildParagraph(pclass, first, last, 'middle', regtype)
                    htmlpage += '</' + tag + '>'
                else :
                    htmlpage += self.buildParagraph(pclass, first, last, ptype, regtype)


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
                (pclass, first, last) = self.getParaDescription(start,end)
                htmlpage += self.buildParagraph(pclass, first, last, ptype, regtype)

            else :
                print 'Unknown region type', regtype
                print 'Warning: skipping this region'

        if len(self.paracont_stemid) > 0 :
            if htmlpage[-4:] == '</p>':
                htmlpage = htmlpage[0:-4]    

        return htmlpage


        return self.convert2HTML()



def convert2HTML(flatxml, fileid):

    # create a document parser
    dp = DocParser(flatxml, fileid)

    htmlpage = dp.process()

    return htmlpage
