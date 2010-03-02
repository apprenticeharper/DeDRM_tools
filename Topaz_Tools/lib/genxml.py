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
import flatxml2html
import decode_meta


def usage():
    print 'Usage: '
    print ' '
    print '   genxml.py dict0000.dat unencryptedBookDir'
    print '  '



def main(argv):
    bookDir = ''

    if len(argv) == 0:
        argv = sys.argv

    try:
        opts, args = getopt.getopt(argv[1:], "h:")

    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(1)
    
    if len(opts) == 0 and len(args) == 0 :
        usage()
        sys.exit(1) 
       
    for o, a in opts:
        if o =="-h":
            usage()
            sys.exit(0)

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

    glyphsDir = os.path.join(bookDir,'glyphs')
    if not os.path.exists(glyphsDir) :
        print "Can not find glyphs directory in unencrypted book"
        sys.exit(1)

    otherFile = os.path.join(bookDir,'other0000.dat')
    if not os.path.exists(otherFile) :
        print "Can not find other0000.dat in unencrypted book"
        sys.exit(1)

    metaFile = os.path.join(bookDir,'metadata0000.dat')
    if not os.path.exists(metaFile) :
        print "Can not find metadata0000.dat in unencrypted book"
        sys.exit(1)

    xmlDir = os.path.join(bookDir,'xml')
    if not os.path.exists(xmlDir):
        os.makedirs(xmlDir)


    print 'Processing ... '

    print '     ', 'metadata0000.dat'
    fname = os.path.join(bookDir,'metadata0000.dat')
    xname = os.path.join(xmlDir, 'metadata.txt')
    metastr = decode_meta.getMetaData(fname)
    file(xname, 'wb').write(metastr)

    print '     ', 'other0000.dat'
    fname = os.path.join(bookDir,'other0000.dat')
    xname = os.path.join(xmlDir, 'stylesheet.xml')
    pargv=[]
    pargv.append('convert2xml.py')
    pargv.append(dictFile)
    pargv.append(fname)
    xmlstr = convert2xml.main(pargv)
    file(xname, 'wb').write(xmlstr)
    
    filenames = os.listdir(pageDir)
    filenames = sorted(filenames)

    for filename in filenames:
        print '     ', filename
        fname = os.path.join(pageDir,filename)
        xname = os.path.join(xmlDir, filename.replace('.dat','.xml'))
        pargv=[]
        pargv.append('convert2xml.py')
        pargv.append(dictFile)
        pargv.append(fname)
        xmlstr = convert2xml.main(pargv)
        file(xname, 'wb').write(xmlstr)

    filenames = os.listdir(glyphsDir)
    filenames = sorted(filenames)

    for filename in filenames:
        print '     ', filename
        fname = os.path.join(glyphsDir,filename)
        xname = os.path.join(xmlDir, filename.replace('.dat','.xml'))
        pargv=[]
        pargv.append('convert2xml.py')
        pargv.append(dictFile)
        pargv.append(fname)
        xmlstr = convert2xml.main(pargv)
        file(xname, 'wb').write(xmlstr)
 

    print 'Processing Complete'

    return 0

if __name__ == '__main__':
    sys.exit(main(''))
