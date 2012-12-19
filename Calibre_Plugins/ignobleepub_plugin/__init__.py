#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement
__license__   = 'GPL v3'
__docformat__ = 'restructuredtext en'


# Released under the terms of the GNU General Public Licence, version 3
# <http://www.gnu.org/licenses/>
#
# Requires Calibre version 0.7.55 or higher.
#
# All credit given to i♥cabbages for the original standalone scripts.
# I had the much easier job of converting them to a calibre plugin.
#
# This plugin is meant to decrypt Barnes & Noble Epubs that are protected
# with a version of Adobe's Adept encryption. It is meant to function without having to
# install any dependencies... other than having calibre installed, of course. It will still
# work if you have Python and PyCrypto already installed, but they aren't necessary.
#
# Configuration:
# Check out the plugin's configuration settings by clicking the "Customize plugin"
# button when you have the "BnN ePub DeDRM" plugin highlighted (under Preferences->
# Plugins->File type plugins). Once you have the configuration dialog open, you'll
# see a Help link on the top right-hand side.
#
# Revision history:
#   0.1.0 - Initial release
#   0.1.1 - Allow Windows users to make use of openssl if they have it installed.
#          - Incorporated SomeUpdates zipfix routine.
#   0.1.2 - bug fix for non-ascii file names in encryption.xml
#   0.1.3 - Try PyCrypto on Windows first
#   0.1.4 - update zipfix to deal with mimetype not in correct place
#   0.1.5 - update zipfix to deal with completely missing mimetype files
#   0.1.6 - update for the new calibre plugin interface
#   0.1.7 - Fix for potential problem with PyCrypto
#   0.1.8 - an updated/modified zipfix.py and included zipfilerugged.py
#   0.2.0 - Completely overhauled plugin configuration dialog and key management/storage
#   0.2.1 - added zipfix.py and included zipfilerugged.py from 0.1.8
#   0.2.2 - added in potential fixes from 0.1.7 that had been missed.
#   0.2.3 - fixed possible output/unicode problem
#   0.2.4 - ditched nearly hopeless caselessStrCmp method in favor of uStrCmp.
#         - added ability to rename existing keys.
#   0.2.5 - Major code change to use unaltered ignobleepub.py 3.6 and
#         - ignoblekeygen 2.4 and later.

"""
Decrypt Barnes & Noble ADEPT encrypted EPUB books.
"""

PLUGIN_NAME = u"Ignoble Epub DeDRM"
PLUGIN_VERSION_TUPLE = (0, 2, 5)
PLUGIN_VERSION = '.'.join([str(x) for x in PLUGIN_VERSION_TUPLE])
# Include an html helpfile in the plugin's zipfile with the following name.
RESOURCE_NAME = PLUGIN_NAME + '_Help.htm'

import sys, os, re
import zipfile
from zipfile import ZipFile

class IGNOBLEError(Exception):
    pass

from calibre.customize import FileTypePlugin
from calibre.constants import iswindows, isosx
from calibre.gui2 import is_ok_to_use_qt

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


class IgnobleDeDRM(FileTypePlugin):
    name                    = PLUGIN_NAME
    description             = u"Removes DRM from secure Barnes & Noble epub files. Credit given to i♥cabbages for the original stand-alone scripts."
    supported_platforms     = ['linux', 'osx', 'windows']
    author                  = u"DiapDealer, Apprentice Alf and i♥cabbages"
    version                 = PLUGIN_VERSION_TUPLE
    minimum_calibre_version = (0, 7, 55)  # Compiled python libraries cannot be imported in earlier versions.
    file_types              = set(['epub'])
    on_import               = True
    priority                = 101

    def run(self, path_to_ebook):

        # make sure any unicode output gets converted safely with 'replace'
        sys.stdout=SafeUnbuffered(sys.stdout)
        sys.stderr=SafeUnbuffered(sys.stderr)

        print u"{0} v{1}: Trying to decrypt {2}.".format(PLUGIN_NAME, PLUGIN_VERSION, os.path.basename(path_to_ebook))

        # First time use or first time after upgrade to new key-handling/storage method
        # or no keys configured. Give a visual prompt to configure.
        import calibre_plugins.ignobleepub.config as cfg
        if not cfg.prefs['configured']:
            titlemsg = '%s v%s' % (PLUGIN_NAME, PLUGIN_VERSION)
            errmsg = titlemsg + ' not (properly) configured!\n' + \
                    '\nThis may be the first time you\'ve used this plugin' + \
                    ' (or the first time since upgrading this plugin).' + \
                    ' You\'ll need to open the customization dialog (Preferences->Plugins->File type plugins)' + \
                    ' and follow the instructions there.\n' + \
                    '\nIf you don\'t use the ' + PLUGIN_NAME + ' plugin, you should disable or uninstall it.'
            if is_ok_to_use_qt():
                from PyQt4.Qt import QMessageBox
                d = QMessageBox(QMessageBox.Warning, titlemsg, errmsg )
                d.show()
                d.raise_()
                d.exec_()
            raise Exception('%s Plugin v%s: Plugin not configured.' % (PLUGIN_NAME, PLUGIN_VERSION))

        # Create a TemporaryPersistent file to work with.
        # Check original epub archive for zip errors.
        from calibre_plugins.ignobleepub import zipfix
        inf = self.temporary_file(u".epub")
        try:
            print u"{0} v{1}: Verifying zip archive integrity.".format(PLUGIN_NAME, PLUGIN_VERSION)
            fr = zipfix.fixZip(path_to_ebook, inf.name)
            fr.fix()
        except Exception, e:
            print u"{0} v{1}: Error \'{2}\' when checking zip archive.".format(PLUGIN_NAME, PLUGIN_VERSION, e.args[0])
            raise Exception(e)
            return

        #check the book
        from calibre_plugins.ignobleepub import ignobleepub
        if not ignobleepub.ignobleBook(inf.name):
            print u"{0} v{1}: {2} is not a secure Barnes & Noble ePub.".format(PLUGIN_NAME, PLUGIN_VERSION, os.path.basename(path_to_ebook))
            # return the original file, so that no error message is generated in the GUI
            return path_to_ebook


        # Attempt to decrypt epub with each encryption key (generated or provided).
        for keyname, userkey in cfg.prefs['keys'].items():
            keyname_masked = u"".join((u'X' if (x.isdigit()) else x) for x in keyname)
            print u"{0} v{1}: Trying Encryption key {2:s}".format(PLUGIN_NAME, PLUGIN_VERSION, keyname_masked)
            of = self.temporary_file(u".epub")

            # Give the user key, ebook and TemporaryPersistent file to the decryption function.
            result = ignobleepub.decryptBook(userkey, inf.name, of.name)

            # Ebook is not a B&N epub... do nothing and pass it on.
            # This allows a non-encrypted epub to be imported without error messages.
            if  result[0] == 1:
                print u"{0} v{1}: {2}".format(PLUGIN_NAME, PLUGIN_VERSION, result[1])
                of.close()
                return path_to_ebook
                break

            # Decryption was successful return the modified PersistentTemporary
            # file to Calibre's import process.
            if  result[0] == 0:
                print u"{0} v{1}: Encryption successfully removed.".format(PLUGIN_NAME, PLUGIN_VERSION)
                of.close()
                return of.name
                break

            print u"{0} v{1}: {2}".format(PLUGIN_NAME, PLUGIN_VERSION, result[1])
            of.close()


        # Something went wrong with decryption.
        # Import the original unmolested epub.
        print(u"{0} v{1}: Ultimately failed to decrypt".format(PLUGIN_NAME, PLUGIN_VERSION))
        return path_to_ebook

    def is_customizable(self):
        # return true to allow customization via the Plugin->Preferences.
        return True

    def config_widget(self):
        from calibre_plugins.ignobleepub.config import ConfigWidget
        # Extract the helpfile contents from in the plugin's zipfile.
        # The helpfile must be named <plugin name variable> + '_Help.htm'
        return ConfigWidget(self.load_resources(RESOURCE_NAME)[RESOURCE_NAME])

    def load_resources(self, names):
        ans = {}
        with ZipFile(self.plugin_path, 'r') as zf:
            for candidate in zf.namelist():
                if candidate in names:
                    ans[candidate] = zf.read(candidate)
        return ans

    def save_settings(self, config_widget):
        config_widget.save_settings()
