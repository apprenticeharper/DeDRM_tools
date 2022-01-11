#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# lcpdedrm.py
# Copyright © 2021-2022 NoDRM

# Released under the terms of the GNU General Public Licence, version 3
# <http://www.gnu.org/licenses/>


# Revision history:
#   1 - Initial release
#   2 - LCP DRM code removed due to a DMCA takedown.

"""
This file used to contain code to remove the Readium LCP DRM
from eBooks. Unfortunately, Readium has issued a DMCA takedown 
request, so I was forced to remove that code: 

https://github.com/github/dmca/blob/master/2022/01/2022-01-04-readium.md

This file now just returns an error message when asked to remove LCP DRM.
For more information, see this issue: 
https://github.com/noDRM/DeDRM_tools/issues/18 
"""

__license__ = 'GPL v3'
__version__ = "2"

import json
from zipfile import ZipFile
from contextlib import closing


class LCPError(Exception):
    pass

# Check file to see if this is an LCP-protected file
def isLCPbook(inpath):
    try: 
        with closing(ZipFile(open(inpath, 'rb'))) as lcpbook:
            if ("META-INF/license.lcpl" not in lcpbook.namelist() or
                "META-INF/encryption.xml" not in lcpbook.namelist() or
                b"EncryptedContentKey" not in lcpbook.read("META-INF/encryption.xml")):
                return False

            license = json.loads(lcpbook.read('META-INF/license.lcpl'))

            if "id" in license and "encryption" in license and "profile" in license["encryption"]:
                return True

    except: 
        return False
    
    return False


# Takes a file and a list of passphrases
def decryptLCPbook(inpath, passphrases, parent_object):

    if not isLCPbook(inpath):
        raise LCPError("This is not an LCP-encrypted book")

    print("LCP: LCP DRM removal no longer supported due to a DMCA takedown request.")
    print("LCP: The takedown request can be found here: ")
    print("LCP: https://github.com/github/dmca/blob/master/2022/01/2022-01-04-readium.md ")
    print("LCP: More information can be found in the Github repository: ")
    print("LCP: https://github.com/noDRM/DeDRM_tools/issues/18 ")

    raise LCPError("LCP DRM removal no longer supported")
