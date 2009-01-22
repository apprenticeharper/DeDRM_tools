#! /usr/bin/python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import os, sys, getopt

# local routines
import convert2xml
import flatxml2html
import decode_meta
import stylexml2css
import getpagedim

def usage():
    print 'Usage: '
    print ' '
    print '   genhtml.py unencryptedBookDir'
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

    otherFile = os.path.join(bookDir,'other0000.dat')
    if not os.path.exists(otherFile) :
        print "Can not find other0000.dat in unencrypted book"
        sys.exit(-1)

    metaFile = os.path.join(bookDir,'metadata0000.dat')
    if not os.path.exists(metaFile) :
        print "Can not find metadata0000.dat in unencrypted book"
        sys.exit(-1)


    htmlFileName = "book.html"
    htmlstr = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
    htmlstr += '<html>\n'

    filenames = os.listdir(pageDir)
    filenames = sorted(filenames)

    print 'Processing ... '

    htmlstr += '<head>\n'
    htmlstr += '<meta http-equiv="content-type" content="text/html; charset=utf-8"/>\n'

    # process metadata and retrieve fontSize info
    print '     ', 'metadata0000.dat'
    fname = os.path.join(bookDir,'metadata0000.dat')
    xname = os.path.join(bookDir, 'metadata.txt')
    metastr = decode_meta.getMetaData(fname)
    file(xname, 'wb').write(metastr)
    meta_array = decode_meta.getMetaArray(fname)

    htmlstr += '<title>' + meta_array['Title'] + ' by ' + meta_array['Authors'] + '</title>\n' 
    htmlstr += '<meta name="Author" content="' + meta_array['Authors'] + '" />\n'
    htmlstr += '<meta name="Title" content="' + meta_array['Title'] + '" />\n'

    # get some scaling info from metadata to use while processing styles
    fontsize = '135'
    if 'fontSize' in meta_array:
        fontsize = meta_array['fontSize']

    # also get the size of a normal text page
    spage = '1'
    if 'firstTextPage' in meta_array:
        spage = meta_array['firstTextPage']
    pnum = int(spage)

    # get page height and width from first text page for use in stylesheet scaling
    pname = 'page%04d.dat' % pnum
    fname = os.path.join(pageDir,pname)
    flat_xml = convert2xml.main('convert2xml.py --flat-xml ' + dictFile + ' ' + fname)
    (ph, pw) = getpagedim.getPageDim(flat_xml)
    if (ph == '-1') : ph = 11000
    if (pw == '-1') : pw = 8500

    # now build up the style sheet
    print '     ', 'other0000.dat'
    fname = os.path.join(bookDir,'other0000.dat')
    xname = os.path.join(bookDir, 'style.css')
    xmlstr = convert2xml.main('convert2xml.py --flat-xml ' + dictFile + ' ' + fname)
    cssstr , classlst = stylexml2css.convert2CSS(xmlstr, fontsize, ph, pw)
    file(xname, 'wb').write(cssstr)
    htmlstr += '<link href="style.css" rel="stylesheet" type="text/css" />\n'
    htmlstr += '</head>\n<body>\n'

    for filename in filenames:
        print '     ', filename
        fname = os.path.join(pageDir,filename)
        flat_xml = convert2xml.main('convert2xml.py --flat-xml ' + dictFile + ' ' + fname) 
        htmlstr += flatxml2html.convert2HTML(flat_xml, classlst, fname)

    htmlstr += '</body>\n</html>\n'

    file(os.path.join(bookDir, htmlFileName), 'wb').write(htmlstr)
    print 'Processing Complete'

    return 0

if __name__ == '__main__':
    sys.exit(main(''))


