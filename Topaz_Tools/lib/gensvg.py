#! /usr/bin/python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import os, sys, getopt

# local routines
import convert2xml
import flatxml2html
import decode_meta


class GParser(object):
   def __init__(self, flatxml):
       self.flatdoc = flatxml.split('\n')
       self.dpi = 1440
       self.gh = self.getData('info.glyph.h')
       self.gw = self.getData('info.glyph.w')
       self.guse = self.getData('info.glyph.use')
       self.count = len(self.guse)
       self.gvtx = self.getData('info.glyph.vtx')
       self.glen = self.getData('info.glyph.len')
       self.gdpi = self.getData('info.glyph.dpi')
       self.vx = self.getData('info.vtx.x')
       self.vy = self.getData('info.vtx.y')
       self.vlen = self.getData('info.len.n')
       self.glen.append(len(self.vlen))
       self.gvtx.append(len(self.vx))

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

   def getPath(self, gly):
       path = ''
       if (gly < 0) or (gly >= self.count):
           return path
       tx = self.vx[self.gvtx[gly]:self.gvtx[gly+1]-1]
       ty = self.vy[self.gvtx[gly]:self.gvtx[gly+1]-1]
       p = 0
       for k in xrange(self.glen[gly], self.glen[gly+1]):
           if (p == 0):
               zx = tx[0:self.vlen[k]+1]
               zy = ty[0:self.vlen[k]+1]
           else:
               zx = tx[self.vlen[k-1]+1:self.vlen[k]+1]
               zy = ty[self.vlen[k-1]+1:self.vlen[k]+1]
           p += 1
           for j in xrange(0, len(zx)):
               if (j == 0):
                   path += 'M %d %d ' % (zx[j] * self.dpi / self.gdpi[gly], zy[j] * self.dpi / self.gdpi[gly])
               else:
                   path += 'L %d %d ' % (zx[j] * self.dpi / self.gdpi[gly], zy[j] * self.dpi / self.gdpi[gly])
       path += 'z'
       return path

class PParser(object):
   def __init__(self, flatxml):
       self.flatdoc = flatxml.split('\n')
       self.temp = []
       self.ph = self.getData('page.h')[0]
       self.pw = self.getData('page.w')[0]
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
       while (self.getDataTemp('region.img') != None):
           h = self.getDataTemp('region.img.h')[0]
           w = self.getDataTemp('region.img.w')[0]
           x = self.getDataTemp('region.img.x')[0]
           y = self.getDataTemp('region.img.y')[0]
           src = self.getDataTemp('region.img.src')[0]
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
   print '   gensvg.py unencryptedBookDir'
   print '  '


def main(argv):
   bookDir = ''

   if len(argv) == 0:
       argv = sys.argv
   else :
       argv = argv.split()

   try:
       opts, args = getopt.getopt(argv[1:], "h:")

   except getopt.GetoptError, err:
       print str(err)
       usage()
       sys.exit(2)

   if len(opts) == 0 and len(args) == 0 :
       usage()
       sys.exit(2) 

   for o, a in opts:
       if o =="-h":
           usage()
           sys.exit(0)

   bookDir = args[0]

   if not os.path.exists(bookDir) :
       print "Can not find directory with unencrypted book"
       sys.exit(-1)

   dictFile = os.path.join(bookDir,'dict0000.dat')

   if not os.path.exists(dictFile) :
       print "Can not find dict0000.dat file"
       sys.exit(-1)

   pageDir = os.path.join(bookDir,'page')
   if not os.path.exists(pageDir) :
       print "Can not find page directory in unencrypted book"
       sys.exit(-1)

   imgDir = os.path.join(bookDir,'img')
   if not os.path.exists(imgDir) :
       print "Can not find image directory in unencrypted book"
       sys.exit(-1)

   glyphsDir = os.path.join(bookDir,'glyphs')
   if not os.path.exists(glyphsDir) :
       print "Can not find glyphs directory in unencrypted book"
       sys.exit(-1)

   metaFile = os.path.join(bookDir,'metadata0000.dat')
   if not os.path.exists(metaFile) :
       print "Can not find metadata0000.dat in unencrypted book"
       sys.exit(-1)

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
       flat_xml = convert2xml.main('convert2xml.py --flat-xml ' + dictFile + ' ' + fname) 
       gp = GParser(flat_xml)
       for i in xrange(0, gp.count):
           path = gp.getPath(i)
           glyfile.write('<path id="gl%d" d="%s" fill="black" />\n' % (counter * 256 + i, path))
       counter += 1
   glyfile.write('</defs>\n')
   glyfile.write('</svg>\n')
   glyfile.close()

   print 'Processing Pages ... '

   scaledpi = 720
   filenames = os.listdir(pageDir)
   filenames = sorted(filenames)
   counter = 0
   for filename in filenames:
       print '     ', filename
       fname = os.path.join(pageDir,filename)
       flat_xml = convert2xml.main('convert2xml.py --flat-xml ' + dictFile + ' ' + fname) 
       pp = PParser(flat_xml)
       pfile = open(os.path.join(svgDir,filename.replace('.dat','.svg')), 'w')
       pfile.write('<?xml version="1.0" standalone="no"?>\n')
       pfile.write('<!DOCTYPE svg PUBLIC "-//W3C/DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n')
       pfile.write('<svg width="%fin" height="%fin" viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1">\n' % (pp.pw / scaledpi, pp.ph / scaledpi, pp.pw -1, pp.ph -1))
       pfile.write('<title>Page %d - %s by %s</title>\n' % (counter, metadata['Title'],metadata['Authors']))
       if (pp.gid != None): 
           pfile.write('<defs>\n')
           gdefs = pp.getGlyphs(glyfname)
           for j in xrange(0,len(gdefs)):
               pfile.write(gdefs[j])
           pfile.write('</defs>\n')
           for j in xrange(0,len(pp.gid)):
               pfile.write('<use xlink:href="#gl%d" x="%d" y="%d" />\n' % (pp.gid[j], pp.gx[j], pp.gy[j]))
       img = pp.getImages()
       if (img != None):
           for j in xrange(0,len(img)):
               pfile.write(img[j])
       pfile.write('</svg>')
       pfile.close()
       counter += 1

   print 'Processing Complete'

   return 0

if __name__ == '__main__':
   sys.exit(main(''))
