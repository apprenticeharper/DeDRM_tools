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
import re
import ineptpdf

def main(argv=sys.argv):
    args = argv[1:]
    if len(args) != 3:
        return -1
    infile = args[0]
    outdir = args[1]
    rscpath = args[2]
    errlog = ''
    rv = 1

    # determine a good name for the output file
    name, ext = os.path.splitext(os.path.basename(infile))
    outfile = os.path.join(outdir, name + '_nodrm.pdf')

    # try with any keyfiles (*.der) in the rscpath
    files = os.listdir(rscpath)
    filefilter = re.compile("\.der$", re.IGNORECASE)
    files = filter(filefilter.search, files)
    if files:
        for filename in files:
            keypath = os.path.join(rscpath, filename)
            try:
                rv = ineptpdf.decryptBook(keypath, infile, outfile)
                if rv == 0:
                    break
            except Exception, e:
                errlog += str(e)
                rv = 1
                pass
    if rv != 0:
        print errlog
    return rv


if __name__ == "__main__":
    sys.exit(main())
