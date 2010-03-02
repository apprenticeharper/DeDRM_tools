#! /usr/bin/python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# For use with Topaz Scripts Version 2.6

class Unbuffered:
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

import sys
sys.stdout=Unbuffered(sys.stdout)

import os, getopt

# local routines
import convert2xml
import decode_meta


class GParser(object):
 def __init__(self, flatxml):
     self.flatdoc = flatxml.split('\n')
     self.dpi = 1440
     self.gh = self.getData('info.glyph.h')
     self.gw = self.getData('info.glyph.w')
     self.guse = self.getData('info.glyph.use')
     if self.guse :
         self.count = len(self.guse)
     else :
         self.count = 0
     self.gvtx = self.getData('info.glyph.vtx')
     self.glen = self.getData('info.glyph.len')
     self.gdpi = self.getData('info.glyph.dpi')
     self.vx = self.getData('info.vtx.x')
     self.vy = self.getData('info.vtx.y')
     self.vlen = self.getData('info.len.n')
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
     for j in xrange(cnt):
         item = self.flatdoc[j]
         if item.find('=') >= 0:
             (name, argt) = item.split('=')
             argres = argt.split('|')
         else:
             name = item
             argres = []
         if (name == path):
             result = argres
             break
     if (len(argres) > 0) :
         for j in xrange(0,len(argres)):
             argres[j] = int(argres[j])
     return result


 def getGlyphDim(self, gly):
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
     for k in xrange(self.glen[gly], self.glen[gly+1]):
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

class PParser(object):
 def __init__(self, flatxml):
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

 def getGlyphs(self,glyfname):
     result = []
     if (self.gid != None) and (len(self.gid) > 0):
         glyphs = []
         for j in set(self.gid):
             glyphs.append(j)
         glyphs.sort()
         gfile = open(glyfname, 'r')
         j = 0
         while True :
             inp = gfile.readline()
             if (inp == ''):
                 break
             id='id="gl%d"' % glyphs[j]
             if (inp.find(id) > 0):
                 result.append(inp)
                 j += 1
                 if (j == len(glyphs)):
                     break
         gfile.close()
     return result




def usage():
 print 'Usage: '
 print ' '
 print '   gensvg.py [options] unencryptedBookDir'
 print '  '
 print '   -x : output browseable XHTML+SVG pages (default)'
 print '   -r : output raw SVG images'


def main(argv):
 bookDir = ''

 if len(argv) == 0:
     argv = sys.argv

 try:
     opts, args = getopt.getopt(argv[1:], "xrh")

 except getopt.GetoptError, err:
     print str(err)
     usage()
     sys.exit(1)

 if len(opts) == 0 and len(args) == 0 :
     usage()
     sys.exit(1) 

 raw = 0
 for o, a in opts:
     if o =="-h":
         usage()
         sys.exit(0)
     if o =="-x":
         raw = 0
     if o =="-r":
         raw = 1

 bookDir = args[0]

 if not os.path.exists(bookDir) :
     print "Can not find directory with unencrypted book"
     sys.exit(1)

 dictFile = os.path.join(bookDir,'dict0000.dat')

 if not os.path.exists(dictFile) :
     print "Can not find dict0000.dat file"
     sys.exit(1)

 pageDir = os.path.join(bookDir,'page')
 if not os.path.exists(pageDir) :
     print "Can not find page directory in unencrypted book"
     sys.exit(1)

 imgDir = os.path.join(bookDir,'img')
 if not os.path.exists(imgDir) :
     print "Can not find image directory in unencrypted book"
     sys.exit(1)

 glyphsDir = os.path.join(bookDir,'glyphs')
 if not os.path.exists(glyphsDir) :
     print "Can not find glyphs directory in unencrypted book"
     sys.exit(1)

 metaFile = os.path.join(bookDir,'metadata0000.dat')
 if not os.path.exists(metaFile) :
     print "Can not find metadata0000.dat in unencrypted book"
     sys.exit(1)

 svgDir = os.path.join(bookDir,'svg')
 if not os.path.exists(svgDir) :
     os.makedirs(svgDir)


 print 'Processing Meta Data ... '

 print '     ', 'metadata0000.dat'
 fname = os.path.join(bookDir,'metadata0000.dat')
 metadata = decode_meta.getMetaArray(fname)

 print 'Processing Glyphs ... '

 filenames = os.listdir(glyphsDir)
 filenames = sorted(filenames)

 glyfname = os.path.join(svgDir,'glyphs.svg')
 glyfile = open(glyfname, 'w')
 glyfile.write('<?xml version="1.0" standalone="no"?>\n')
 glyfile.write('<!DOCTYPE svg PUBLIC "-//W3C/DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n')
 glyfile.write('<svg width="512" height="512" viewBox="0 0 511 511" xmlns="http://www.w3.org/2000/svg" version="1.1">\n')
 glyfile.write('<title>Glyphs for %s</title>\n' % metadata['Title'])
 glyfile.write('<defs>\n')
 counter = 0
 for filename in filenames:
     print '     ', filename
     fname = os.path.join(glyphsDir,filename)
     pargv=[]
     pargv.append('convert2xml.py')
     pargv.append('--flat-xml')
     pargv.append(dictFile)
     pargv.append(fname)
     flat_xml = convert2xml.main(pargv)
     gp = GParser(flat_xml)
     for i in xrange(0, gp.count):
         path = gp.getPath(i)
         maxh, maxw = gp.getGlyphDim(i)
         # glyfile.write('<path id="gl%d" d="%s" fill="black" />\n' % (counter * 256 + i, path))
         glyfile.write('<path id="gl%d" d="%s" fill="black" /><!-- width=%d height=%d -->\n' % (counter * 256 + i, path, maxw, maxh ))
     counter += 1
 glyfile.write('</defs>\n')
 glyfile.write('</svg>\n')
 glyfile.close()

 print 'Processing Pages ... '

 # Books are at 1440 DPI.  This is rendering at twice that size for
 # readability when rendering to the screen.  
 scaledpi = 1440
 filenames = os.listdir(pageDir)
 filenames = sorted(filenames)
 counter = 0
 for filename in filenames:
     print '     ', filename
     fname = os.path.join(pageDir,filename)
     pargv=[]
     pargv.append('convert2xml.py')
     pargv.append('--flat-xml')
     pargv.append(dictFile)
     pargv.append(fname)
     flat_xml = convert2xml.main(pargv)
     pp = PParser(flat_xml)
     if (raw) :
         pfile = open(os.path.join(svgDir,filename.replace('.dat','.svg')), 'w')
     else :
         pfile = open(os.path.join(svgDir,'page%04d.xhtml' % counter), 'w')

     pfile.write('<?xml version="1.0" standalone="no"?>\n')
     if (raw):
         pfile.write('<!DOCTYPE svg PUBLIC "-//W3C/DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n')
         pfile.write('<svg width="%fin" height="%fin" viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1">\n' % (pp.pw / scaledpi, pp.ph / scaledpi, pp.pw -1, pp.ph -1))
         pfile.write('<title>Page %d - %s by %s</title>\n' % (counter, metadata['Title'],metadata['Authors']))
     else:
         pfile.write('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">\n');
         pfile.write('<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" ><head>\n');
         pfile.write('<title>Page %d - %s by %s</title>\n' % (counter, metadata['Title'],metadata['Authors']))
         pfile.write('<script><![CDATA[\n');
         pfile.write('function gd(){var p=window.location.href.replace(/^.*\?dpi=(\d+).*$/i,"$1");return p;}\n');
         pfile.write('var dpi=%d;\n' % scaledpi);
         if (counter) :
            pfile.write('var prevpage="page%04d.xhtml";\n' % (counter - 1))
         if (counter < len(filenames)-1) :
            pfile.write('var nextpage="page%04d.xhtml";\n' % (counter + 1))
         pfile.write('var pw=%d;var ph=%d;' % (pp.pw, pp.ph))
         pfile.write('function zoomin(){dpi=dpi*(2/3);setsize();}\n')
         pfile.write('function zoomout(){dpi=dpi*1.5;setsize();}\n')
         pfile.write('function setsize(){var svg=document.getElementById("svgimg");var prev=document.getElementById("prevsvg");var next=document.getElementById("nextsvg");var width=(pw/dpi)+"in";var height=(ph/dpi)+"in";svg.setAttribute("width",width);svg.setAttribute("height",height);prev.setAttribute("height",height);prev.setAttribute("width","50px");next.setAttribute("height",height);next.setAttribute("width","50px");}\n')
         pfile.write('function ppage(){window.location.href=prevpage+"?dpi="+Math.round(dpi);}\n')
         pfile.write('function npage(){window.location.href=nextpage+"?dpi="+Math.round(dpi);}\n')
         pfile.write('var gt=gd();if(gt>0){dpi=gt;}\n')
         pfile.write('window.onload=setsize;\n')
         pfile.write(']]></script>\n')
         pfile.write('</head>\n')
         pfile.write('<body onLoad="setsize();" style="background-color:#777;text-align:center;">\n')
         pfile.write('<div style="white-space:nowrap;">\n')
         if (counter == 0) :
             pfile.write('<a href="javascript:ppage();"><svg id="prevsvg" viewBox="0 0 100 300" xmlns="http://www.w3.org/2000/svg" version="1.1" style="background-color:#777"></svg></a>\n')
         else:
             pfile.write('<a href="javascript:ppage();"><svg id="prevsvg" viewBox="0 0 100 300" xmlns="http://www.w3.org/2000/svg" version="1.1" style="background-color:#777"><polygon points="5,150,95,5,95,295" fill="#AAAAAA" /></svg></a>\n')
         pfile.write('<a href="javascript:npage();"><svg id="svgimg" viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" style="background-color:#FFF;border:1px solid black;">' % (pp.pw, pp.ph))

     if (pp.gid != None): 
         pfile.write('<defs>\n')
         gdefs = pp.getGlyphs(glyfname)
         for j in xrange(0,len(gdefs)):
             pfile.write(gdefs[j])
         pfile.write('</defs>\n')
     img = pp.getImages()
     if (img != None):
         for j in xrange(0,len(img)):
             pfile.write(img[j])
     if (pp.gid != None): 
         for j in xrange(0,len(pp.gid)):
             pfile.write('<use xlink:href="#gl%d" x="%d" y="%d" />\n' % (pp.gid[j], pp.gx[j], pp.gy[j]))
     if (img == None or len(img) == 0) and (pp.gid == None or len(pp.gid) == 0):
         pfile.write('<text x="10" y="10" font-family="Helvetica" font-size="100" stroke="black">This page intentionally left blank.</text>\n<text x="10" y="110" font-family="Helvetica" font-size="50" stroke="black">Until this notice unintentionally gave it content.  (gensvg.py)</text>\n');
     if (raw) :
         pfile.write('</svg>')
     else :
         pfile.write('</svg></a>\n')
         if (counter == len(filenames) - 1) :
             pfile.write('<a href="javascript:npage();"><svg id="nextsvg" viewBox="0 0 100 300" xmlns="http://www.w3.org/2000/svg" version="1.1" style="background-color:#777"></svg></a>\n')
         else :
             pfile.write('<a href="javascript:npage();"><svg id="nextsvg" viewBox="0 0 100 300" xmlns="http://www.w3.org/2000/svg" version="1.1" style="background-color:#777"><polygon points="5,5,5,295,95,150" fill="#AAAAAA" /></svg></a>\n')
         pfile.write('</div>\n')
         pfile.write('<div><a href="javascript:zoomin();">zoom in</a> - <a href="javascript:zoomout();">zoom out</a></div>\n')
         pfile.write('</body>\n')
         pfile.write('</html>\n')
     pfile.close()
     counter += 1

 print 'Processing Complete'

 return 0

if __name__ == '__main__':
 sys.exit(main(''))
