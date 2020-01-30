#! /usr/bin/python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# For use with Topaz Scripts Version 2.6

from __future__ import print_function
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
        self.flatdoc = flatxml.split('\n')
        self.fontsize = int(fontsize)
        self.ph = int(ph) * 1.0
        self.pw = int(pw) * 1.0

    stags = {
        'paragraph' : 'p',
        'graphic'   : '.graphic'
    }

    attr_val_map = {
        'hang'            : 'text-indent: ',
        'indent'          : 'text-indent: ',
        'line-space'      : 'line-height: ',
        'margin-bottom'   : 'margin-bottom: ',
        'margin-left'     : 'margin-left: ',
        'margin-right'    : 'margin-right: ',
        'margin-top'      : 'margin-top: ',
        'space-after'     : 'padding-bottom: ',
    }

    attr_str_map = {
        'align-center' : 'text-align: center; margin-left: auto; margin-right: auto;',
        'align-left'   : 'text-align: left;',
        'align-right'  : 'text-align: right;',
        'align-justify' : 'text-align: justify;',
        'display-inline' : 'display: inline;',
        'pos-left' : 'text-align: left;',
        'pos-right' : 'text-align: right;',
        'pos-center' : 'text-align: center; margin-left: auto; margin-right: auto;',
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
        for j in xrange(pos, end):
            item = docList[j]
            if item.find('=') >= 0:
                (name, argres) = item.split('=',1)
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

    # returns a vector of integers for the tagpath
    def getData(self, tagpath, pos, end, clean=False):
        if clean:
            digits_only = re.compile(r'''([0-9]+)''')
        argres=[]
        (foundat, argt) = self.findinDoc(tagpath, pos, end)
        if (argt != None) and (len(argt) > 0) :
            argList = argt.split('|')
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
        styleList= self.posinDoc('book.stylesheet.style')
        stylecnt = len(styleList)
        styleList.append(-1)

        # process each style converting what you can

        if debug: print('          ', 'Processing styles.')
        for j in xrange(stylecnt):
            if debug: print('          ', 'Processing style %d' %(j))
            start = styleList[j]
            end = styleList[j+1]

            (pos, tag) = self.findinDoc('style._tag',start,end)
            if tag == None :
                (pos, tag) = self.findinDoc('style.type',start,end)

            # Is this something we know how to convert to css
            if tag in self.stags :

                # get the style class
                (pos, sclass) = self.findinDoc('style.class',start,end)
                if sclass != None:
                    sclass = sclass.replace(' ','-')
                    sclass = '.cl-' + sclass.lower()
                else :
                    sclass = ''

                if debug: print('sclass', sclass)

                # check for any "after class" specifiers
                (pos, aftclass) = self.findinDoc('style._after_class',start,end)
                if aftclass != None:
                    aftclass = aftclass.replace(' ','-')
                    aftclass = '.cl-' + aftclass.lower()
                else :
                    aftclass = ''

                if debug: print('aftclass', aftclass)

                cssargs = {}

                while True :

                    (pos1, attr) = self.findinDoc('style.rule.attr', start, end)
                    (pos2, val) = self.findinDoc('style.rule.value', start, end)

                    if debug: print('attr', attr)
                    if debug: print('val', val)

                    if attr == None : break

                    if (attr == 'display') or (attr == 'pos') or (attr == 'align'):
                        # handle text based attributess
                        attr = attr + '-' + val
                        if attr in self.attr_str_map :
                            cssargs[attr] = (self.attr_str_map[attr], '')
                    else :
                        # handle value based attributes
                        if attr in self.attr_val_map :
                            name = self.attr_val_map[attr]
                            if attr in ('margin-bottom', 'margin-top', 'space-after') :
                                scale = self.ph
                            elif attr in ('margin-right', 'indent', 'margin-left', 'hang') :
                                scale = self.pw
                            elif attr == 'line-space':
                                scale = self.fontsize * 2.0

                            if val == "":
                                val = 0

                            if not ((attr == 'hang') and (int(val) == 0)):
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
                    if 'line-space' in cssargs:
                        seg = cssargs['line-space'][0]
                        val = cssargs['line-space'][1]
                        if val < 1.0: val = 1.0
                        if val > 3.0: val = 3.0
                        del cssargs['line-space']
                        cssargs['line-space'] = (self.attr_val_map['line-space'], val)


                    # handle modifications for css style hanging indents
                    if 'hang' in cssargs:
                        hseg = cssargs['hang'][0]
                        hval = cssargs['hang'][1]
                        del cssargs['hang']
                        cssargs['hang'] = (self.attr_val_map['hang'], -hval)
                        mval = 0
                        mseg = 'margin-left: '
                        mval = hval
                        if 'margin-left' in cssargs:
                            mseg = cssargs['margin-left'][0]
                            mval = cssargs['margin-left'][1]
                            if mval < 0: mval = 0
                            mval = hval + mval
                        cssargs['margin-left'] = (mseg, mval)
                        if 'indent' in cssargs:
                            del cssargs['indent']

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
