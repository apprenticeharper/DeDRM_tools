#! /usr/bin/python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# For use with Topaz Scripts Version 2.6


import csv
import sys
import os
import getopt
import re
from struct import pack
from struct import unpack

debug = False

class DocParser(object):
    def __init__(self, flatxml, fontsize, ph, pw):
        self.flatdoc = flatxml.split(b'\n')
        self.fontsize = int(fontsize)
        self.ph = int(ph) * 1.0
        self.pw = int(pw) * 1.0

    stags = {
        b'paragraph' : 'p',
        b'graphic'   : '.graphic'
    }

    attr_val_map = {
        b'hang'            : 'text-indent: ',
        b'indent'          : 'text-indent: ',
        b'line-space'      : 'line-height: ',
        b'margin-bottom'   : 'margin-bottom: ',
        b'margin-left'     : 'margin-left: ',
        b'margin-right'    : 'margin-right: ',
        b'margin-top'      : 'margin-top: ',
        b'space-after'     : 'padding-bottom: ',
    }

    attr_str_map = {
        b'align-center' : 'text-align: center; margin-left: auto; margin-right: auto;',
        b'align-left'   : 'text-align: left;',
        b'align-right'  : 'text-align: right;',
        b'align-justify' : 'text-align: justify;',
        b'display-inline' : 'display: inline;',
        b'pos-left' : 'text-align: left;',
        b'pos-right' : 'text-align: right;',
        b'pos-center' : 'text-align: center; margin-left: auto; margin-right: auto;',
    }


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
                (name, argres) = item.split(b'=',1)
            else :
                name = item
                argres = b''
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
        res = b""
        while res != None :
            (foundpos, res) = self.findinDoc(tagpath, pos, -1)
            if res != None :
                startpos.append(foundpos)
            pos = foundpos + 1
        return startpos

    # returns a vector of integers for the tagpath
    def getData(self, tagpath, pos, end, clean=False):
        if clean:
            digits_only = re.compile(rb'''([0-9]+)''')
        argres=[]
        (foundat, argt) = self.findinDoc(tagpath, pos, end)
        if (argt != None) and (len(argt) > 0) :
            argList = argt.split(b'|')
            for strval in argList:
                if clean:
                    m = re.search(digits_only, strval)
                    if m != None:
                        strval = m.group()
                argres.append(int(strval))
        return argres

    def process(self):

        classlst = ''
        csspage = '.cl-center { text-align: center; margin-left: auto; margin-right: auto; }\n'
        csspage += '.cl-right { text-align: right; }\n'
        csspage += '.cl-left { text-align: left; }\n'
        csspage += '.cl-justify { text-align: justify; }\n'

        # generate a list of each <style> starting point in the stylesheet
        styleList= self.posinDoc(b'book.stylesheet.style')
        stylecnt = len(styleList)
        styleList.append(-1)

        # process each style converting what you can

        if debug: print('          ', 'Processing styles.')
        for j in range(stylecnt):
            if debug: print('          ', 'Processing style %d' %(j))
            start = styleList[j]
            end = styleList[j+1]

            (pos, tag) = self.findinDoc(b'style._tag',start,end)
            if tag == None :
                (pos, tag) = self.findinDoc(b'style.type',start,end)

            # Is this something we know how to convert to css
            if tag in self.stags :

                # get the style class
                (pos, sclass) = self.findinDoc(b'style.class',start,end)
                if sclass != None:
                    sclass = sclass.replace(b' ',b'-')
                    sclass = b'.cl-' + sclass.lower()
                else :
                    sclass = b''

                if debug: print('sclass', sclass)

                # check for any "after class" specifiers
                (pos, aftclass) = self.findinDoc(b'style._after_class',start,end)
                if aftclass != None:
                    aftclass = aftclass.replace(b' ',b'-')
                    aftclass = b'.cl-' + aftclass.lower()
                else :
                    aftclass = b''

                if debug: print('aftclass', aftclass)

                cssargs = {}

                while True :

                    (pos1, attr) = self.findinDoc(b'style.rule.attr', start, end)
                    (pos2, val) = self.findinDoc(b'style.rule.value', start, end)

                    if debug: print('attr', attr)
                    if debug: print('val', val)

                    if attr == None : break

                    if (attr == b'display') or (attr == b'pos') or (attr == b'align'):
                        # handle text based attributess
                        attr = attr + b'-' + val
                        if attr in self.attr_str_map :
                            cssargs[attr] = (self.attr_str_map[attr], b'')
                    else :
                        # handle value based attributes
                        if attr in self.attr_val_map :
                            name = self.attr_val_map[attr]
                            if attr in (b'margin-bottom', b'margin-top', b'space-after') :
                                scale = self.ph
                            elif attr in (b'margin-right', b'indent', b'margin-left', b'hang') :
                                scale = self.pw
                            elif attr == b'line-space':
                                scale = self.fontsize * 2.0
                            else:
                                print("Scale not defined!")
                                scale = 1.0

                            if val == "":
                                val = 0

                            if not ((attr == b'hang') and (int(val) == 0)):
                                try:
                                    f = float(val)
                                except:
                                    print("Warning: unrecognised val, ignoring")
                                    val = 0
                                pv = float(val)/scale
                                cssargs[attr] = (self.attr_val_map[attr], pv)
                                keep = True

                    start = max(pos1, pos2) + 1

                # disable all of the after class tags until I figure out how to handle them
                if aftclass != "" : keep = False

                if keep :
                    if debug: print('keeping style')
                    # make sure line-space does not go below 100% or above 300% since
                    # it can be wacky in some styles
                    if b'line-space' in cssargs:
                        seg = cssargs[b'line-space'][0]
                        val = cssargs[b'line-space'][1]
                        if val < 1.0: val = 1.0
                        if val > 3.0: val = 3.0
                        del cssargs[b'line-space']
                        cssargs[b'line-space'] = (self.attr_val_map[b'line-space'], val)


                    # handle modifications for css style hanging indents
                    if b'hang' in cssargs:
                        hseg = cssargs[b'hang'][0]
                        hval = cssargs[b'hang'][1]
                        del cssargs[b'hang']
                        cssargs[b'hang'] = (self.attr_val_map[b'hang'], -hval)
                        mval = 0
                        mseg = 'margin-left: '
                        mval = hval
                        if b'margin-left' in cssargs:
                            mseg = cssargs[b'margin-left'][0]
                            mval = cssargs[b'margin-left'][1]
                            if mval < 0: mval = 0
                            mval = hval + mval
                        cssargs[b'margin-left'] = (mseg, mval)
                        if b'indent' in cssargs:
                            del cssargs[b'indent']

                    cssline = sclass + ' { '
                    for key in iter(cssargs):
                        mseg = cssargs[key][0]
                        mval = cssargs[key][1]
                        if mval == '':
                            cssline += mseg + ' '
                        else :
                            aseg = mseg + '%.1f%%;' % (mval * 100.0)
                            cssline += aseg + ' '

                    cssline += '}'

                    if sclass != '' :
                        classlst += sclass + '\n'

                    # handle special case of paragraph class used inside chapter heading
                    # and non-chapter headings
                    if sclass != '' :
                        ctype = sclass[4:7]
                        if ctype == 'ch1' :
                            csspage += 'h1' + cssline + '\n'
                        if ctype == 'ch2' :
                            csspage += 'h2' + cssline + '\n'
                        if ctype == 'ch3' :
                            csspage += 'h3' + cssline + '\n'
                        if ctype == 'h1-' :
                            csspage += 'h4' + cssline + '\n'
                        if ctype == 'h2-' :
                            csspage += 'h5' + cssline + '\n'
                        if ctype == 'h3_' :
                            csspage += 'h6' + cssline + '\n'

                    if cssline != ' { }':
                        csspage += self.stags[tag] + cssline + '\n'


        return csspage, classlst



def convert2CSS(flatxml, fontsize, ph, pw):

    print('          ', 'Using font size:',fontsize)
    print('          ', 'Using page height:', ph)
    print('          ', 'Using page width:', pw)

    # create a document parser
    dp = DocParser(flatxml, fontsize, ph, pw)
    if debug: print('          ', 'Created DocParser.')
    csspage = dp.process()
    if debug: print('          ', 'Processed DocParser.')
    return csspage


def getpageIDMap(flatxml):
    dp = DocParser(flatxml, 0, 0, 0)
    pageidnumbers = dp.getData('info.original.pid', 0, -1, True)
    return pageidnumbers
