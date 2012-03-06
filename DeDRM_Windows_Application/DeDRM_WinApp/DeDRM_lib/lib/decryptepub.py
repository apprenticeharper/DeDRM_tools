#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

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
import os

import ineptepub
import ignobleepub
import zipfix
import re

def main(argv=sys.argv):
    args = argv[1:]
    if len(args) != 3:
        return -1
    infile = args[0]
    outdir = args[1]
    rscpath = args[2]
    errlog = ''

    # first fix the epub to make sure we do not get errors
    name, ext = os.path.splitext(os.path.basename(infile))
    bpath = os.path.dirname(infile)
    zippath = os.path.join(bpath,name + '_temp.zip')
    rv = zipfix.repairBook(infile, zippath)
    if rv != 0:
        print "Error while trying to fix epub"
        return rv

    # determine a good name for the output file
    outfile = os.path.join(outdir, name + '_nodrm.epub')

    rv = 1
    # first try with the Adobe adept epub
    # try with any keyfiles (*.der) in the rscpath
    files = os.listdir(rscpath)
    filefilter = re.compile("\.der$", re.IGNORECASE)
    files = filter(filefilter.search, files)
    if files:
        for filename in files:
            keypath = os.path.join(rscpath, filename)
            try:
                rv = ineptepub.decryptBook(keypath, zippath, outfile)
                if rv == 0:
                    break
            except Exception, e:
                errlog += str(e)
                rv = 1
                pass
    if rv == 0:
        os.remove(zippath)
        return 0

    # still no luck
    # now try with ignoble epub
    # try with any keyfiles (*.b64) in the rscpath
    files = os.listdir(rscpath)
    filefilter = re.compile("\.b64$", re.IGNORECASE)
    files = filter(filefilter.search, files)
    if files:
        for filename in files:
            keypath = os.path.join(rscpath, filename)
            try:
                rv = ignobleepub.decryptBook(keypath, zippath, outfile)
                if rv == 0:
                    break
            except Exception, e:
                errlog += str(e)
                rv = 1
                pass
    os.remove(zippath)
    if rv != 0:
        print errlog
    return rv


if __name__ == "__main__":
    sys.exit(main())
