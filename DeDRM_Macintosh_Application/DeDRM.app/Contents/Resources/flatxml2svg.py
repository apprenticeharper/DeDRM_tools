#! /usr/bin/python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import sys
import csv
import os
import getopt
from struct import pack
from struct import unpack


class PParser(object):
    def __init__(self, gd, flatxml):
        self.gd = gd
        self.flatdoc = flatxml.split('\n')
        self.temp = []
        foo = self.getData('page.h') or self.getData('book.h')
        self.ph = foo[0]
        foo = self.getData('page.w') or self.getData('book.w')
        self.pw = foo[0]
        self.gx = self.getData('info.glyph.x')
        self.gy = self.getData('info.glyph.y')
        self.gid = self.getData('info.glyph.glyphID')
    def getData(self, path):
        result = None
        cnt = len(self.flatdoc)
        for j in xrange(cnt):
            item = self.flatdoc[j]
            if item.find('=') >= 0:
                (name, argt) = item.split('=')
                argres = argt.split('|')
            else:
                name = item
                argres = []
            if (name.endswith(path)):
                result = argres
                break
        if (len(argres) > 0) :
            for j in xrange(0,len(argres)):
                argres[j] = int(argres[j])
        return result
    def getDataTemp(self, path):
        result = None
        cnt = len(self.temp)
        for j in xrange(cnt):
            item = self.temp[j]
            if item.find('=') >= 0:
                (name, argt) = item.split('=')
                argres = argt.split('|')
            else:
                name = item
                argres = []
            if (name.endswith(path)):
                result = argres
                self.temp.pop(j)
                break
        if (len(argres) > 0) :
            for j in xrange(0,len(argres)):
                argres[j] = int(argres[j])
        return result
    def getImages(self):
        result = []
        self.temp = self.flatdoc
        while (self.getDataTemp('img') != None):
            h = self.getDataTemp('img.h')[0]
            w = self.getDataTemp('img.w')[0]
            x = self.getDataTemp('img.x')[0]
            y = self.getDataTemp('img.y')[0]
            src = self.getDataTemp('img.src')[0]
            result.append('<image xlink:href="../img/img%04d.jpg" x="%d" y="%d" width="%d" height="%d" />\n' % (src, x, y, w, h))
        return result
    def getGlyphs(self):
        result = []
        if (self.gid != None) and (len(self.gid) > 0):
            glyphs = []
            for j in set(self.gid):
                glyphs.append(j)
            glyphs.sort()
            for gid in glyphs:
                id='id="gl%d"' % gid
                path = self.gd.lookup(id)
                if path:
                    result.append(id + ' ' + path)
        return result


def convert2SVG(gdict, flat_xml, counter, numfiles, svgDir, raw, meta_array, scaledpi):
    ml = ''
    pp = PParser(gdict, flat_xml)
    ml += '<?xml version="1.0" standalone="no"?>\n'
    if (raw):
        ml += '<!DOCTYPE svg PUBLIC "-//W3C/DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n'
        ml += '<svg width="%fin" height="%fin" viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1">\n' % (pp.pw / scaledpi, pp.ph / scaledpi, pp.pw -1, pp.ph -1)
        ml += '<title>Page %d - %s by %s</title>\n' % (counter, meta_array['Title'],meta_array['Authors'])
    else:
        ml += '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">\n'
        ml += '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" ><head>\n'
        ml += '<title>Page %d - %s by %s</title>\n' % (counter, meta_array['Title'],meta_array['Authors'])
        ml += '<script><![CDATA[\n'
        ml += 'function gd(){var p=window.location.href.replace(/^.*\?dpi=(\d+).*$/i,"$1");return p;}\n'
        ml += 'var dpi=%d;\n' % scaledpi
        if (counter) :
            ml += 'var prevpage="page%04d.xhtml";\n' % (counter - 1)
        if (counter < numfiles-1) :
            ml += 'var nextpage="page%04d.xhtml";\n' % (counter + 1)
        ml += 'var pw=%d;var ph=%d;' % (pp.pw, pp.ph)
        ml += 'function zoomin(){dpi=dpi*(0.8);setsize();}\n'
        ml += 'function zoomout(){dpi=dpi*1.25;setsize();}\n'
        ml += 'function setsize(){var svg=document.getElementById("svgimg");var prev=document.getElementById("prevsvg");var next=document.getElementById("nextsvg");var width=(pw/dpi)+"in";var height=(ph/dpi)+"in";svg.setAttribute("width",width);svg.setAttribute("height",height);prev.setAttribute("height",height);prev.setAttribute("width","50px");next.setAttribute("height",height);next.setAttribute("width","50px");}\n'
        ml += 'function ppage(){window.location.href=prevpage+"?dpi="+Math.round(dpi);}\n'
        ml += 'function npage(){window.location.href=nextpage+"?dpi="+Math.round(dpi);}\n'
        ml += 'var gt=gd();if(gt>0){dpi=gt;}\n'
        ml += 'window.onload=setsize;\n'
        ml += ']]></script>\n'
        ml += '</head>\n'
        ml += '<body onLoad="setsize();" style="background-color:#777;text-align:center;">\n'
        ml += '<div style="white-space:nowrap;">\n'
        if (counter == 0) :
            ml += '<a href="javascript:ppage();"><svg id="prevsvg" viewBox="0 0 100 300" xmlns="http://www.w3.org/2000/svg" version="1.1" style="background-color:#777"></svg></a>\n'
        else:
            ml += '<a href="javascript:ppage();"><svg id="prevsvg" viewBox="0 0 100 300" xmlns="http://www.w3.org/2000/svg" version="1.1" style="background-color:#777"><polygon points="5,150,95,5,95,295" fill="#AAAAAA" /></svg></a>\n'
        ml += '<a href="javascript:npage();"><svg id="svgimg" viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" style="background-color:#FFF;border:1px solid black;">' % (pp.pw, pp.ph)
    if (pp.gid != None): 
        ml += '<defs>\n'
        gdefs = pp.getGlyphs()
        for j in xrange(0,len(gdefs)):
            ml += gdefs[j]
        ml += '</defs>\n'
    img = pp.getImages()
    if (img != None):
        for j in xrange(0,len(img)):
            ml += img[j]
    if (pp.gid != None): 
        for j in xrange(0,len(pp.gid)):
            ml += '<use xlink:href="#gl%d" x="%d" y="%d" />\n' % (pp.gid[j], pp.gx[j], pp.gy[j])
    if (img == None or len(img) == 0) and (pp.gid == None or len(pp.gid) == 0):
        ml += '<text x="10" y="10" font-family="Helvetica" font-size="100" stroke="black">This page intentionally left blank.</text>\n<text x="10" y="110" font-family="Helvetica" font-size="50" stroke="black">Until this notice unintentionally gave it content.  (gensvg.py)</text>\n'
    if (raw) :
        ml += '</svg>'
    else :
        ml += '</svg></a>\n'
        if (counter == numfiles - 1) :
            ml += '<a href="javascript:npage();"><svg id="nextsvg" viewBox="0 0 100 300" xmlns="http://www.w3.org/2000/svg" version="1.1" style="background-color:#777"></svg></a>\n'
        else :
            ml += '<a href="javascript:npage();"><svg id="nextsvg" viewBox="0 0 100 300" xmlns="http://www.w3.org/2000/svg" version="1.1" style="background-color:#777"><polygon points="5,5,5,295,95,150" fill="#AAAAAA" /></svg></a>\n'
        ml += '</div>\n'
        ml += '<div><a href="javascript:zoomin();">zoom in</a> - <a href="javascript:zoomout();">zoom out</a></div>\n'
        ml += '</body>\n'
        ml += '</html>\n'
    return ml

