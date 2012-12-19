#!/usr/bin/env python
# -*- coding: utf-8 -*-

# eReaderPDB2PML_plugin.py
# Released under the terms of the GNU General Public Licence, version 3
# <http://www.gnu.org/licenses/>
#
# All credit given to The Dark Reverser for the original standalone script.
# I had the much easier job of converting it to Calibre a plugin.
#
# This plugin is meant to convert secure Ereader files (PDB) to unsecured PMLZ files.
# Calibre can then convert it to whatever format you desire.
# It is meant to function without having to install any dependencies...
# other than having Calibre installed, of course.
#
# Installation:
# Go to Calibre's Preferences page... click on the Plugins button. Use the file
# dialog button to select the plugin's zip file (eReaderPDB2PML_vXX_plugin.zip) and
# click the 'Add' button. You're done.
#
# Configuration:
# Highlight the plugin (eReader PDB 2 PML) and click the
# "Customize Plugin" button on Calibre's Preferences->Plugins page.
# Enter your name and the last 8 digits of the credit card number separated by
# a comma: Your Name,12341234
#
# If you've purchased books with more than one credit card, separate the info with
# a colon: Your Name,12341234:Other Name,23452345
# NOTE: Do NOT put quotes around your name like you do with the original script!!
#
# Revision history:
#   0.0.1 - Initial release
#   0.0.2 - updated to distinguish it from earlier non-openssl version
#   0.0.3 - removed added psyco code as it is not supported under Calibre's Python 2.7
#   0.0.4 - minor typos fixed
#   0.0.5 - updated to the new calibre plugin interface
#   0.0.6 - unknown changes
#   0.0.7 - improved config dialog processing and fix possible output/unicode problem
#   0.0.8 - Proper fix for unicode problems, separate out erdr2pml from plugin

PLUGIN_NAME = u"eReader PDB 2 PML"
PLUGIN_VERSION_TUPLE = (0, 0, 8)
PLUGIN_VERSION = '.'.join([str(x) for x in PLUGIN_VERSION_TUPLE])

import sys, os

from calibre.customize import FileTypePlugin
from calibre.ptempfile import PersistentTemporaryDirectory
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


class eRdrDeDRM(FileTypePlugin):
    name                = PLUGIN_NAME
    description         = u"Removes DRM from secure pdb files. Credit given to The Dark Reverser for the original standalone script."
    supported_platforms = ['linux', 'osx', 'windows'] # Platforms this plugin will run on
    author              = u"DiapDealer, Apprentice Alf and The Dark Reverser"
    version             = PLUGIN_VERSION_TUPLE
    file_types          = set(['pdb']) # The file types that this plugin will be applied to
    on_import           = True # Run this plugin during the import
    minimum_calibre_version = (0, 7, 55)
    priority            = 100

    def run(self, path_to_ebook):

        # make sure any unicode output gets converted safely with 'replace'
        sys.stdout=SafeUnbuffered(sys.stdout)
        sys.stderr=SafeUnbuffered(sys.stderr)

        print u"{0} v{1}: Trying to decrypt {2}.".format(PLUGIN_NAME, PLUGIN_VERSION, os.path.basename(path_to_ebook))

        infile = path_to_ebook
        bookname = os.path.splitext(os.path.basename(infile))[0]
        outdir = PersistentTemporaryDirectory()
        pmlzfile = self.temporary_file(bookname + '.pmlz')

        if self.site_customization:
            from calibre_plugins.erdrpdb2pml import erdr2pml

            keydata = self.site_customization
            ar = keydata.split(':')
            for i in ar:
                try:
                    name, cc = i.split(',')
                    user_key = erdr2pml.getuser_key(name,cc)
                except ValueError:
                    print u"{0} v{1}: Error parsing user supplied data.".format(PLUGIN_NAME, PLUGIN_VERSION)
                    return path_to_ebook

                try:
                    print u"{0} v{1}: Processing...".format(PLUGIN_NAME, PLUGIN_VERSION)
                    import time
                    start_time = time.time()
                    if erdr2pml.decryptBook(infile,pmlzfile.name,True,user_key) == 0:
                        print u"{0} v{1}: Elapsed time: {2:.2f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,time.time()-start_time)
                        return pmlzfile.name
                    else:
                        raise ValueError(u"{0} v{1}: Error Creating PML file.".format(PLUGIN_NAME, PLUGIN_VERSION))
                except ValueError, e:
                        print u"{0} v{1}: Error: {2}".format(PLUGIN_NAME, PLUGIN_VERSION,e.args[0])
                        pass
            raise Exception(u"{0} v{1}: Couldn\'t decrypt pdb file. See Apprentice Alf's blog for help.".format(PLUGIN_NAME, PLUGIN_VERSION))
        else:
            raise Exception(u"{0} v{1}: No name and CC# provided.".format(PLUGIN_NAME, PLUGIN_VERSION))


    def customization_help(self, gui=False):
        return u"Enter Account Name & Last 8 digits of Credit Card number (separate with a comma, multiple pairs with a colon)"
