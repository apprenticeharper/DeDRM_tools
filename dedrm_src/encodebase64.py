#!/usr/bin/env python
# -*- coding: utf-8 -*-

# base64.py, version 1.0
# Copyright © 2010 Apprentice Alf

# Released under the terms of the GNU General Public Licence, version 3 or
# later.  <http://www.gnu.org/licenses/>

# Revision history:
#   1 - Initial release. To allow Applescript to do base64 encoding

"""
Provide base64 encoding.
"""

from __future__ import with_statement
from __future__ import print_function

__license__ = 'GPL v3'

import sys
import os
import base64

def usage(progname):
    print("Applies base64 encoding to the supplied file, sending to standard output")
    print("Usage:")
    print("    %s <infile>" % progname)

def cli_main(argv=sys.argv):
    progname = os.path.basename(argv[0])

    if len(argv)<2:
        usage(progname)
        sys.exit(2)

    keypath = argv[1]
    with open(keypath, 'rb') as f:
        keyder = f.read()
        print(keyder.encode('base64'))
    return 0


if __name__ == '__main__':
    sys.exit(cli_main())
