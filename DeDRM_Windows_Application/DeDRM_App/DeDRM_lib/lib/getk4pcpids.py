#!/usr/bin/python
#
# This is a python script. You need a Python interpreter to run it.
# For example, ActiveState Python, which exists for windows.
#
# Changelog
#  1.00 - Initial version
#  1.01 - getPidList interface change

__version__ = '1.01'

import sys

class Unbuffered:
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)
sys.stdout=Unbuffered(sys.stdout)

import os
import struct
import binascii
import kgenpids
import topazextract
import mobidedrm
from alfcrypto import Pukall_Cipher

class DrmException(Exception):
    pass

def getK4PCpids(path_to_ebook):
    # Return Kindle4PC PIDs. Assumes that the caller checked that we are not on Linux, which will raise an exception

    mobi = True
    magic3 = file(path_to_ebook,'rb').read(3)
    if magic3 == 'TPZ':
        mobi = False

    if mobi:
        mb = mobidedrm.MobiBook(path_to_ebook,False)
    else:
        mb = topazextract.TopazBook(path_to_ebook)

    md1, md2 = mb.getPIDMetaInfo()

    return kgenpids.getPidList(md1, md2)


def main(argv=sys.argv):
    print ('getk4pcpids.py v%(__version__)s. '
        'Copyright 2012 Apprentice Alf' % globals())

    if len(argv)<2 or len(argv)>3:
        print "Gets the possible book-specific PIDs from K4PC for a particular book"
        print "Usage:"
        print "    %s <bookfile> [<outfile>]" % sys.argv[0]
        return 1
    else:
        infile = argv[1]
        try:
            pidlist = getK4PCpids(infile)
        except DrmException, e:
            print "Error: %s" % e
            return 1
        pidstring = ','.join(pidlist)
        print "Possible PIDs are: ", pidstring
        if len(argv) is 3:
            outfile = argv[2]
            file(outfile, 'w').write(pidstring)

    return 0

if __name__ == "__main__":
    sys.exit(main())
