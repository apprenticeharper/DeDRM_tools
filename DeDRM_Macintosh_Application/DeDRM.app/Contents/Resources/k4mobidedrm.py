#!/usr/bin/env python

from __future__ import with_statement

# engine to remove drm from Kindle for Mac and Kindle for PC books
# for personal use for archiving and converting your ebooks

# PLEASE DO NOT PIRATE EBOOKS!

# We want all authors and publishers, and eBook stores to live
# long and prosperous lives but at the same time  we just want to
# be able to read OUR books on whatever device we want and to keep
# readable for a long, long time

#  This borrows very heavily from works by CMBDTC, IHeartCabbages, skindle,
#    unswindle, DarkReverser, ApprenticeAlf, DiapDealer, some_updates
#    and many many others


__version__ = '4.4'

class Unbuffered:
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

import sys
import os, csv, getopt
import string
import re
import traceback
import time

buildXML = False

class DrmException(Exception):
    pass

if 'calibre' in sys.modules:
    inCalibre = True
else:
    inCalibre = False

if inCalibre:
    from calibre_plugins.k4mobidedrm import mobidedrm
    from calibre_plugins.k4mobidedrm import topazextract
    from calibre_plugins.k4mobidedrm import kgenpids
else:
    import mobidedrm
    import topazextract
    import kgenpids


# cleanup bytestring filenames
# borrowed from calibre from calibre/src/calibre/__init__.py
# added in removal of non-printing chars
# and removal of . at start
# convert underscores to spaces (we're OK with spaces in file names)
def cleanup_name(name):
    _filename_sanitize = re.compile(r'[\xae\0\\|\?\*<":>\+/]')
    substitute='_'
    one = ''.join(char for char in name if char in string.printable)
    one = _filename_sanitize.sub(substitute, one)
    one = re.sub(r'\s', ' ', one).strip()
    one = re.sub(r'^\.+$', '_', one)
    one = one.replace('..', substitute)
    # Windows doesn't like path components that end with a period
    if one.endswith('.'):
        one = one[:-1]+substitute
    # Mac and Unix don't like file names that begin with a full stop
    if len(one) > 0 and one[0] == '.':
        one = substitute+one[1:]
    one = one.replace('_',' ')
    return one

def decryptBook(infile, outdir, k4, kInfoFiles, serials, pids):
    global buildXML


    # handle the obvious cases at the beginning
    if not os.path.isfile(infile):
        print >>sys.stderr, ('K4MobiDeDrm v%(__version__)s\n' % globals()) + "Error: Input file does not exist"
        return 1

    starttime = time.time()
    print "Starting decryptBook routine."


    mobi = True
    magic3 = file(infile,'rb').read(3)
    if magic3 == 'TPZ':
        mobi = False

    bookname = os.path.splitext(os.path.basename(infile))[0]

    if mobi:
        mb = mobidedrm.MobiBook(infile)
    else:
        mb = topazextract.TopazBook(infile)

    title = mb.getBookTitle()
    print "Processing Book: ", title
    filenametitle = cleanup_name(title)
    outfilename = cleanup_name(bookname)

    # generate 'sensible' filename, that will sort with the original name,
    # but is close to the name from the file.
    outlength = len(outfilename)
    comparelength = min(8,min(outlength,len(filenametitle)))
    copylength = min(max(outfilename.find(' '),8),len(outfilename))
    if outlength==0:
        outfilename = filenametitle
    elif comparelength > 0:
    	if outfilename[:comparelength] == filenametitle[:comparelength]:
        	outfilename = filenametitle
        else:
        	outfilename = outfilename[:copylength] + " " + filenametitle

    # avoid excessively long file names
    if len(outfilename)>150:
        outfilename = outfilename[:150]

    # build pid list
    md1, md2 = mb.getPIDMetaInfo()
    pids.extend(kgenpids.getPidList(md1, md2, k4, serials, kInfoFiles))

    print "Found {1:d} keys to try after {0:.1f} seconds".format(time.time()-starttime, len(pids))


    try:
        mb.processBook(pids)

    except mobidedrm.DrmException, e:
        print >>sys.stderr, ('K4MobiDeDrm v%(__version__)s\n' % globals()) + "Error: " + str(e) + "\nDRM Removal Failed.\n"
        print "Failed to decrypted book after {0:.1f} seconds".format(time.time()-starttime)
        return 1
    except topazextract.TpzDRMError, e:
        print >>sys.stderr, ('K4MobiDeDrm v%(__version__)s\n' % globals()) + "Error: " + str(e) + "\nDRM Removal Failed.\n"
        print "Failed to decrypted book after {0:.1f} seconds".format(time.time()-starttime)
        return 1
    except Exception, e:
        print >>sys.stderr, ('K4MobiDeDrm v%(__version__)s\n' % globals()) + "Error: " + str(e) + "\nDRM Removal Failed.\n"
        print "Failed to decrypted book after {0:.1f} seconds".format(time.time()-starttime)
        return 1

    print "Successfully decrypted book after {0:.1f} seconds".format(time.time()-starttime)

    if mobi:
        if mb.getPrintReplica():
            outfile = os.path.join(outdir, outfilename + '_nodrm' + '.azw4')
        elif mb.getMobiVersion() >= 8:
            outfile = os.path.join(outdir, outfilename + '_nodrm' + '.azw3')
        else:
            outfile = os.path.join(outdir, outfilename + '_nodrm' + '.mobi')
        mb.getMobiFile(outfile)
        print "Saved decrypted book {1:s} after {0:.1f} seconds".format(time.time()-starttime, outfilename + '_nodrm')
        return 0

    # topaz:
    print "   Creating NoDRM HTMLZ Archive"
    zipname = os.path.join(outdir, outfilename + '_nodrm' + '.htmlz')
    mb.getHTMLZip(zipname)

    print "   Creating SVG ZIP Archive"
    zipname = os.path.join(outdir, outfilename + '_SVG' + '.zip')
    mb.getSVGZip(zipname)

    if buildXML:
        print "   Creating XML ZIP Archive"
        zipname = os.path.join(outdir, outfilename + '_XML' + '.zip')
        mb.getXMLZip(zipname)

    # remove internal temporary directory of Topaz pieces
    mb.cleanup()
    print "Saved decrypted Topaz book parts after {0:.1f} seconds".format(time.time()-starttime)
    return 0


def usage(progname):
    print "Removes DRM protection from K4PC/M, Kindle, Mobi and Topaz ebooks"
    print "Usage:"
    print "    %s [-k <kindle.info>] [-p <pidnums>] [-s <kindleSerialNumbers>] <infile> <outdir>  " % progname

#
# Main
#
def main(argv=sys.argv):
    progname = os.path.basename(argv[0])

    k4 = False
    kInfoFiles = []
    serials = []
    pids = []

    print ('K4MobiDeDrm v%(__version__)s '
           'provided by the work of many including DiapDealer, SomeUpdates, IHeartCabbages, CMBDTC, Skindle, DarkReverser, ApprenticeAlf, etc .' % globals())

    try:
        opts, args = getopt.getopt(sys.argv[1:], "k:p:s:")
    except getopt.GetoptError, err:
        print str(err)
        usage(progname)
        sys.exit(2)
    if len(args)<2:
        usage(progname)
        sys.exit(2)

    for o, a in opts:
        if o == "-k":
            if a == None :
                raise DrmException("Invalid parameter for -k")
            kInfoFiles.append(a)
        if o == "-p":
            if a == None :
                raise DrmException("Invalid parameter for -p")
            pids = a.split(',')
        if o == "-s":
            if a == None :
                raise DrmException("Invalid parameter for -s")
            serials = a.split(',')

    # try with built in Kindle Info files
    k4 = True
    if sys.platform.startswith('linux'):
        k4 = False
        kInfoFiles = None
    infile = args[0]
    outdir = args[1]
    return decryptBook(infile, outdir, k4, kInfoFiles, serials, pids)


if __name__ == '__main__':
    sys.stdout=Unbuffered(sys.stdout)
    sys.exit(main())
