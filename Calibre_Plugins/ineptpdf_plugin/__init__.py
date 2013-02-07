#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement
__license__   = 'GPL v3'

# Released under the terms of the GNU General Public Licence, version 3
# <http://www.gnu.org/licenses/>

# PLEASE DO NOT PIRATE EBOOKS!

# We want all authors and publishers, and eBook stores to live
# long and prosperous lives but at the same time  we just want to
# be able to read OUR books on whatever device we want and to keep
# readable for a long, long time

# Requires Calibre version 0.7.55 or higher.
#
# All credit given to i♥cabbages for the original standalone scripts.
# I had the much easier job of converting them to a Calibre plugin.
#
# This plugin is meant to decrypt Adobe Digital Edition PDFs that are protected
# with Adobe's Adept encryption. It is meant to function without having to install
# any dependencies... other than having Calibre installed, of course. It will still
# work if you have Python and PyCrypto already installed, but they aren't necessary.
#
# Configuration:
# When first run, the plugin will attempt to find your Adobe Digital Editions installation
# (on Windows and Mac OS's). If successful, it will create one or more
# 'calibre-adeptkey<n>.der' files and save them in calibre's configuration directory.
# It will use those files on subsequent runs. If there is already a 'calibre-adeptkey*.der'
# file in the directory, the plugin won't attempt to find the ADE installation.
# So if you have ADE installed on the same machine as calibre you are ready to go.
#
# If you already have keyfiles generated with i♥cabbages' ineptkey.pyw script,
# you can put those keyfiles in Calibre's configuration directory. The easiest
# way to find the correct directory is to go to Calibre's Preferences page... click
# on the 'Miscellaneous' button (looks like a gear),  and then click the 'Open Calibre
# configuration directory' button. Paste your keyfiles in there. Just make sure that
# they have different names and are saved with the '.der' extension (like the ineptkey
# script produces). This directory isn't touched when upgrading Calibre, so it's quite
# safe to leave them there.
#
# Since there is no Linux version of Adobe Digital Editions, Linux users will have to
# obtain a keyfile through other methods and put the file in Calibre's configuration directory.
#
# All keyfiles with a '.der' extension found in Calibre's configuration directory will
# be used to attempt to decrypt a book.
#
# ** NOTE ** There is no plugin customization data for the Inept PDF DeDRM plugin.
#
# Revision history:
#   0.1   - Initial release
#   0.1.1 - back port ineptpdf 8.4.X support for increased number of encryption methods
#   0.1.2 - back port ineptpdf 8.4.X bug fixes
#   0.1.3 - add in fix for improper rejection of session bookkeys with len(bookkey) = length + 1
#   0.1.4 - update to the new calibre plugin interface
#   0.1.5 - synced to ineptpdf 7.11
#   0.1.6 - Fix for potential problem with PyCrypto
#   0.1.7 - Fix for potential problem with ADE keys and fix possible output/unicode problem
#   0.1.8 - Fix for code copying error
#   0.1.9 - Major code change to use unaltered ineptpdf.py
#   0.2.0 - Fix erroneous dependency on ineptepub plugin

"""
Decrypts Adobe ADEPT-encrypted PDF files.
"""

PLUGIN_NAME = u"Inept PDF DeDRM"
PLUGIN_VERSION_TUPLE = (0, 2, 0)
PLUGIN_VERSION = u'.'.join([str(x) for x in PLUGIN_VERSION_TUPLE])

import sys
import os
import re

class ADEPTError(Exception):
    pass

from calibre.customize import FileTypePlugin
from calibre.constants import iswindows, isosx

# Wrap a stream so that output gets flushed immediately
# and also make sure that any unicode strings get
# encoded using "replace" before writing them.
class SafeUnbuffered:
    def __init__(self, stream):
        self.stream = stream
        self.encoding = stream.encoding
        if self.encoding == None:
            self.encoding = "utf-8"
    def write(self, data):
        if isinstance(data,unicode):
            data = data.encode(self.encoding,"replace")
        self.stream.write(data)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)


class ADEPTError(Exception):
    pass

class IneptPDFDeDRM(FileTypePlugin):
    name                    = PLUGIN_NAME
    description             = u"Removes DRM from secure Adobe pdf files. Credit given to i♥cabbages for the original stand-alone scripts."
    supported_platforms     = ['linux', 'osx', 'windows']
    author                  = u"DiapDealer, Apprentice Alf and i♥cabbages"
    version                 = PLUGIN_VERSION_TUPLE
    minimum_calibre_version = (0, 7, 55)  # for the new plugin interface
    file_types              = set(['pdf'])
    on_import               = True
    priority                = 100

    def run(self, path_to_ebook):

        # make sure any unicode output gets converted safely with 'replace'
        sys.stdout=SafeUnbuffered(sys.stdout)
        sys.stderr=SafeUnbuffered(sys.stderr)

        print u"{0} v{1}: Trying to decrypt {2}.".format(PLUGIN_NAME, PLUGIN_VERSION, os.path.basename(path_to_ebook))

        # Load any keyfiles (*.der) included Calibre's config directory.
        userkeys = []
        # Find Calibre's configuration directory.
        # self.plugin_path is passed in unicode because we defined our name in unicode
        confpath = os.path.split(os.path.split(self.plugin_path)[0])[0]
        print u"{0} v{1}: Calibre configuration directory = {2}".format(PLUGIN_NAME, PLUGIN_VERSION, confpath)
        files = os.listdir(confpath)
        filefilter = re.compile(u"\.der$", re.IGNORECASE)
        files = filter(filefilter.search, files)
        foundDefault = False
        if files:
            try:
                for filename in files:
                    if filename[:16] == u"calibre-adeptkey":
                        foundDefault = True
                    fpath = os.path.join(confpath, filename)
                    with open(fpath, 'rb') as f:
                        userkeys.append([f.read(), filename])
                    print u"{0} v{1}: Keyfile {2} found in config folder.".format(PLUGIN_NAME, PLUGIN_VERSION, filename)
            except IOError:
                print u"{0} v{1}: Error reading keyfiles from config directory.".format(PLUGIN_NAME, PLUGIN_VERSION)
                pass

        if not foundDefault:
            # Try to find key from ADE install and save the key in
            # Calibre's configuration directory for future use.
            if iswindows or isosx:
                #ignore annoying future warning from key generation
                import warnings
                warnings.filterwarnings('ignore', category=FutureWarning)

                # ADE key retrieval script included in respective OS folder.
                from calibre_plugins.ineptpdf.ineptkey import retrieve_keys
                try:
                    keys = retrieve_keys()
                    for i,key in enumerate(keys):
                        keyname = u"calibre-adeptkey{0:d}.der".format(i)
                        userkeys.append([key,keyname])
                        keypath = os.path.join(confpath, keyname)
                        open(keypath, 'wb').write(key)
                        print u"{0} v{1}: Created keyfile {2} from ADE install.".format(PLUGIN_NAME, PLUGIN_VERSION, keyname)
                except:
                   print u"{0} v{1}: Couldn\'t Retrieve key from ADE install.".format(PLUGIN_NAME, PLUGIN_VERSION)
                   pass

        if not userkeys:
            # No user keys found... bail out.
            raise ADEPTError(u"{0} v{1}: No keys found. Check keyfile(s)/ADE install".format(PLUGIN_NAME, PLUGIN_VERSION))
            return

        # Attempt to decrypt pdf with each encryption key found.
        from calibre_plugins.ineptpdf import ineptpdf
        for userkeyinfo in userkeys:
            print u"{0} v{1}: Trying Encryption key {2:s}".format(PLUGIN_NAME, PLUGIN_VERSION, userkeyinfo[1])
            # Create a TemporaryPersistent file to work with.
            of = self.temporary_file('.pdf')

            # Give the user keyfile, ebook and TemporaryPersistent file to the decryptBook function.
            result = ineptpdf.decryptBook(userkeyinfo[0], path_to_ebook, of.name)

            # Decryption was successful return the modified PersistentTemporary
            # file to Calibre's import process.
            if  result == 0:
                print u"{0} v{1}: Encryption successfully removed.".format(PLUGIN_NAME, PLUGIN_VERSION)
                of.close()
                return of.name
                break

            print u"{0} v{1}: Encryption key incorrect.".format(PLUGIN_NAME, PLUGIN_VERSION)
            of.close()

        # Something went wrong with decryption.
        raise ADEPTError(u"{0} v{1}: Ultimately failed to decrypt".format(PLUGIN_NAME, PLUGIN_VERSION))
        return
