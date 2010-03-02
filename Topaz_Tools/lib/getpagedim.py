#! /usr/bin/python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# For use with Topaz Scripts Version 2.6

import csv
import sys
import os
import getopt
from struct import pack
from struct import unpack


class DocParser(object):
    def __init__(self, flatxml):
        self.flatdoc = flatxml.split('\n')


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

    def process(self):
        (pos, sph) = self.findinDoc('page.h',0,-1)
        (pos, spw) = self.findinDoc('page.w',0,-1)
        if (sph == None): sph = '-1'
        if (spw == None): spw = '-1'
        return sph, spw


def getPageDim(flatxml):
    # create a document parser
    dp = DocParser(flatxml)
    (ph, pw) = dp.process()
    return ph, pw
