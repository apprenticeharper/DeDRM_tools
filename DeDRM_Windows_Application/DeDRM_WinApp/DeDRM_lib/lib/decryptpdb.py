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

import erdr2pml

def main(argv=sys.argv):
    args = argv[1:]
    if len(args) != 3:
        return -1
    infile = args[0]
    outdir = args[1]
    rscpath = args[2]
    rv = 1
    socialpath = os.path.join(rscpath,'sdrmlist.txt')
    if os.path.exists(socialpath):
        keydata = file(socialpath,'r').read()
        keydata = keydata.rstrip(os.linesep)
        ar = keydata.split(',')
        for i in ar:
            try:
                name, cc8 = i.split(':')
            except ValueError:
                print '   Error parsing user supplied social drm data.'
                return 1
            rv = erdr2pml.decryptBook(infile, outdir, name, cc8, True)
            if rv == 0:
                break
    return rv


if __name__ == "__main__":
    sys.exit(main())
