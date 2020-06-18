#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement

# __init__.py for DeDRM_plugin
# Copyright © 2008-2020 Apprentice Harper et al.

__license__   = 'GPL v3'
__version__ = '6.8.0'
__docformat__ = 'restructuredtext en'


# Released under the terms of the GNU General Public Licence, version 3
# <http://www.gnu.org/licenses/>
#
# All credit given to i♥cabbages and The Dark Reverser for the original standalone scripts.
# We had the much easier job of converting them to a calibre plugin.
#
# This plugin is meant to decrypt eReader PDBs, Adobe Adept ePubs, Barnes & Noble ePubs,
# Adobe Adept PDFs, Amazon Kindle and Mobipocket files without having
# to install any dependencies... other than having calibre installed, of course.
#
# Configuration:
# Check out the plugin's configuration settings by clicking the "Customize plugin"
# button when you have the "DeDRM" plugin highlighted (under Preferences->
# Plugins->File type plugins). Once you have the configuration dialog open, you'll
# see a Help link on the top right-hand side.
#
# Revision history:
#   6.0.0 - Initial release
#   6.0.1 - Bug Fixes for Windows App, Kindle for Mac and Windows Adobe Digital Editions
#   6.0.2 - Restored call to Wine to get Kindle for PC keys, added for ADE
#   6.0.3 - Fixes for Kindle for Mac and Windows non-ascii user names
#   6.0.4 - Fixes for stand-alone scripts and applications
#           and pdb files in plugin and initial conversion of prefs.
#   6.0.5 - Fix a key issue
#   6.0.6 - Fix up an incorrect function call
#   6.0.7 - Error handling for incomplete PDF metadata
#   6.0.8 - Fixes a Wine key issue and topaz support
#   6.0.9 - Ported to work with newer versions of Calibre (moved to Qt5). Still supports older Qt4 versions.
#   6.1.0 - Fixed multiple books import problem and PDF import with no key problem
#   6.2.0 - Support for getting B&N key from nook Study log. Fix for UTF-8 filenames in Adobe ePubs.
#           Fix for not copying needed files. Fix for getting default Adobe key for PDFs
#   6.2.1 - Fix for non-ascii Windows user names
#   6.2.2 - Added URL method for B&N/nook books
#   6.3.0 - Added in Kindle for Android serial number solution
#   6.3.1 - Version number bump for clarity
#   6.3.2 - Fixed Kindle for Android help file
#   6.3.3 - Bug fix for Kindle for PC support
#   6.3.4 - Fixes for Kindle for Android, Linux, and Kobo 3.17
#   6.3.5 - Fixes for Linux, and Kobo 3.19 and more logging
#   6.3.6 - Fixes for ADE ePub and PDF introduced in 6.3.5
#   6.4.0 - Updated for new Kindle for PC encryption
#   6.4.1 - Fix for some new tags in Topaz ebooks.
#   6.4.2 - Fix for more new tags in Topaz ebooks and very small Topaz ebooks
#   6.4.3 - Fix for error that only appears when not in debug mode
#           Also includes fix for Macs with bonded ethernet ports
#   6.5.0 - Big update to Macintosh app
#           Fix for some more 'new' tags in Topaz ebooks.
#           Fix an error in wineutils.py
#   6.5.1 - Updated version number, added PDF check for DRM-free documents
#   6.5.2 - Another Topaz fix
#   6.5.3 - Warn about KFX files explicitly
#   6.5.4 - Mac App Fix, improve PDF decryption, handle latest tcl changes in ActivePython
#   6.5.5 - Finally a fix for the Windows non-ASCII user names.
#   6.6.0 - Add kfx and kfx-zip as supported file types (also invoke this plugin if the original
#           imported format was azw8 since that may be converted to kfx)
#   6.6.1 - Thanks to wzyboy for a fix for stand-alone tools, and the new folder structure.
#   6.6.2 - revamp of folders to get Mac OS X app working. Updated to 64-bit app. Various fixes.
#   6.6.3 - More cleanup of kindle book names and start of support for .kinf2018
#   6.7.0 - Handle new library in calibre.
#   6.8.0 - Full support for .kinf2018 and new KFX encryption (Kindle for PC/Mac 2.5+)

"""
Decrypt DRMed ebooks.
"""

PLUGIN_NAME = u"DeDRM"
PLUGIN_VERSION_TUPLE = (6, 8, 0)
PLUGIN_VERSION = u".".join([unicode(str(x)) for x in PLUGIN_VERSION_TUPLE])
# Include an html helpfile in the plugin's zipfile with the following name.
RESOURCE_NAME = PLUGIN_NAME + '_Help.htm'

import sys, os, re
import time
import zipfile
import traceback
from zipfile import ZipFile

class DeDRMError(Exception):
    pass

from calibre.customize import FileTypePlugin
from calibre.constants import iswindows, isosx
from calibre.gui2 import is_ok_to_use_qt
from calibre.utils.config import config_dir


# Wrap a stream so that output gets flushed immediately
# and also make sure that any unicode strings get safely
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
        try:
            self.stream.write(data)
            self.stream.flush()
        except:
            # We can do nothing if a write fails
            pass
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

class DeDRM(FileTypePlugin):
    name                    = PLUGIN_NAME
    description             = u"Removes DRM from Amazon Kindle, Adobe Adept (including Kobo), Barnes & Noble, Mobipocket and eReader ebooks. Credit given to i♥cabbages and The Dark Reverser for the original stand-alone scripts."
    supported_platforms     = ['linux', 'osx', 'windows']
    author                  = u"Apprentice Alf, Aprentice Harper, The Dark Reverser and i♥cabbages"
    version                 = PLUGIN_VERSION_TUPLE
    minimum_calibre_version = (1, 0, 0)  # Compiled python libraries cannot be imported in earlier versions.
    file_types              = set(['epub','pdf','pdb','prc','mobi','pobi','azw','azw1','azw3','azw4','azw8','tpz','kfx','kfx-zip'])
    on_import               = True
    priority                = 600


    def initialize(self):
        """
        Dynamic modules can't be imported/loaded from a zipfile.
        So this routine will extract the appropriate
        library for the target OS and copy it to the 'alfcrypto' subdirectory of
        calibre's configuration directory. That 'alfcrypto' directory is then
        inserted into the syspath (as the very first entry) in the run function
        so the CDLL stuff will work in the alfcrypto.py script.

        The extraction only happens once per version of the plugin
        Also perform upgrade of preferences once per version
        """
        try:
            self.pluginsdir = os.path.join(config_dir,u"plugins")
            if not os.path.exists(self.pluginsdir):
                os.mkdir(self.pluginsdir)
            self.maindir = os.path.join(self.pluginsdir,u"DeDRM")
            if not os.path.exists(self.maindir):
                os.mkdir(self.maindir)
            self.helpdir = os.path.join(self.maindir,u"help")
            if not os.path.exists(self.helpdir):
                os.mkdir(self.helpdir)
            self.alfdir = os.path.join(self.maindir,u"libraryfiles")
            if not os.path.exists(self.alfdir):
                os.mkdir(self.alfdir)
            # only continue if we've never run this version of the plugin before
            self.verdir = os.path.join(self.maindir,PLUGIN_VERSION)
            if not os.path.exists(self.verdir):
                if iswindows:
                    names = [u"alfcrypto.dll",u"alfcrypto64.dll"]
                elif isosx:
                    names = [u"libalfcrypto.dylib"]
                else:
                    names = [u"libalfcrypto32.so",u"libalfcrypto64.so",u"kindlekey.py",u"adobekey.py",u"subasyncio.py"]
                lib_dict = self.load_resources(names)
                print u"{0} v{1}: Copying needed library files from plugin's zip".format(PLUGIN_NAME, PLUGIN_VERSION)

                for entry, data in lib_dict.items():
                    file_path = os.path.join(self.alfdir, entry)
                    try:
                        os.remove(file_path)
                    except:
                        pass

                    try:
                        open(file_path,'wb').write(data)
                    except:
                        print u"{0} v{1}: Exception when copying needed library files".format(PLUGIN_NAME, PLUGIN_VERSION)
                        traceback.print_exc()
                        pass

                # convert old preferences, if necessary.
                from calibre_plugins.dedrm.prefs import convertprefs
                convertprefs()

                # mark that this version has been initialized
                os.mkdir(self.verdir)
        except Exception, e:
            traceback.print_exc()
            raise

    def ePubDecrypt(self,path_to_ebook):
        # Create a TemporaryPersistent file to work with.
        # Check original epub archive for zip errors.
        import calibre_plugins.dedrm.zipfix

        inf = self.temporary_file(u".epub")
        try:
            print u"{0} v{1}: Verifying zip archive integrity".format(PLUGIN_NAME, PLUGIN_VERSION)
            fr = zipfix.fixZip(path_to_ebook, inf.name)
            fr.fix()
        except Exception, e:
            print u"{0} v{1}: Error \'{2}\' when checking zip archive".format(PLUGIN_NAME, PLUGIN_VERSION, e.args[0])
            raise Exception(e)

        # import the decryption keys
        import calibre_plugins.dedrm.prefs as prefs
        dedrmprefs = prefs.DeDRM_Prefs()

        # import the Barnes & Noble ePub handler
        import calibre_plugins.dedrm.ignobleepub as ignobleepub


        #check the book
        if  ignobleepub.ignobleBook(inf.name):
            print u"{0} v{1}: “{2}” is a secure Barnes & Noble ePub".format(PLUGIN_NAME, PLUGIN_VERSION, os.path.basename(path_to_ebook))

            # Attempt to decrypt epub with each encryption key (generated or provided).
            for keyname, userkey in dedrmprefs['bandnkeys'].items():
                keyname_masked = u"".join((u'X' if (x.isdigit()) else x) for x in keyname)
                print u"{0} v{1}: Trying Encryption key {2:s}".format(PLUGIN_NAME, PLUGIN_VERSION, keyname_masked)
                of = self.temporary_file(u".epub")

                # Give the user key, ebook and TemporaryPersistent file to the decryption function.
                try:
                    result = ignobleepub.decryptBook(userkey, inf.name, of.name)
                except:
                    print u"{0} v{1}: Exception when trying to decrypt after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime)
                    traceback.print_exc()
                    result = 1

                of.close()

                if  result == 0:
                    # Decryption was successful.
                    # Return the modified PersistentTemporary file to calibre.
                    return of.name

                print u"{0} v{1}: Failed to decrypt with key {2:s} after {3:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,keyname_masked,time.time()-self.starttime)

            # perhaps we should see if we can get a key from a log file
            print u"{0} v{1}: Looking for new NOOK Study Keys after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime)

            # get the default NOOK Study keys
            defaultkeys = []

            try:
                if iswindows or isosx:
                    from calibre_plugins.dedrm.ignoblekey import nookkeys

                    defaultkeys = nookkeys()
                else: # linux
                    from wineutils import WineGetKeys

                    scriptpath = os.path.join(self.alfdir,u"ignoblekey.py")
                    defaultkeys = WineGetKeys(scriptpath, u".b64",dedrmprefs['adobewineprefix'])

            except:
                print u"{0} v{1}: Exception when getting default NOOK Study Key after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime)
                traceback.print_exc()

            newkeys = []
            for keyvalue in defaultkeys:
                if keyvalue not in dedrmprefs['bandnkeys'].values():
                    newkeys.append(keyvalue)

            if len(newkeys) > 0:
                try:
                    for i,userkey in enumerate(newkeys):
                        print u"{0} v{1}: Trying a new default key".format(PLUGIN_NAME, PLUGIN_VERSION)

                        of = self.temporary_file(u".epub")

                        # Give the user key, ebook and TemporaryPersistent file to the decryption function.
                        try:
                            result = ignobleepub.decryptBook(userkey, inf.name, of.name)
                        except:
                           print u"{0} v{1}: Exception when trying to decrypt after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime)
                           traceback.print_exc()
                           result = 1

                        of.close()

                        if result == 0:
                            # Decryption was a success
                            # Store the new successful key in the defaults
                            print u"{0} v{1}: Saving a new default key".format(PLUGIN_NAME, PLUGIN_VERSION)
                            try:
                                dedrmprefs.addnamedvaluetoprefs('bandnkeys','nook_Study_key',keyvalue)
                                dedrmprefs.writeprefs()
                                print u"{0} v{1}: Saved a new default key after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,time.time()-self.starttime)
                            except:
                                print u"{0} v{1}: Exception saving a new default key after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime)
                                traceback.print_exc()
                            # Return the modified PersistentTemporary file to calibre.
                            return of.name

                        print u"{0} v{1}: Failed to decrypt with new default key after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,time.time()-self.starttime)
                except Exception, e:
                    pass

            print u"{0} v{1}: Ultimately failed to decrypt after {2:.1f} seconds. Read the FAQs at Harper's repository: https://github.com/apprenticeharper/DeDRM_tools/blob/master/FAQs.md".format(PLUGIN_NAME, PLUGIN_VERSION,time.time()-self.starttime)
            raise DeDRMError(u"{0} v{1}: Ultimately failed to decrypt after {2:.1f} seconds. Read the FAQs at Harper's repository: https://github.com/apprenticeharper/DeDRM_tools/blob/master/FAQs.md".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))

        # import the Adobe Adept ePub handler
        import calibre_plugins.dedrm.ineptepub as ineptepub

        if ineptepub.adeptBook(inf.name):
            print u"{0} v{1}: {2} is a secure Adobe Adept ePub".format(PLUGIN_NAME, PLUGIN_VERSION, os.path.basename(path_to_ebook))

            # Attempt to decrypt epub with each encryption key (generated or provided).
            for keyname, userkeyhex in dedrmprefs['adeptkeys'].items():
                userkey = userkeyhex.decode('hex')
                print u"{0} v{1}: Trying Encryption key {2:s}".format(PLUGIN_NAME, PLUGIN_VERSION, keyname)
                of = self.temporary_file(u".epub")

                # Give the user key, ebook and TemporaryPersistent file to the decryption function.
                try:
                    result = ineptepub.decryptBook(userkey, inf.name, of.name)
                except:
                    print u"{0} v{1}: Exception when decrypting after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime)
                    traceback.print_exc()
                    result = 1

                try:
                    of.close()
                except:
                    print u"{0} v{1}: Exception closing temporary file after {2:.1f} seconds. Ignored.".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime)

                if  result == 0:
                    # Decryption was successful.
                    # Return the modified PersistentTemporary file to calibre.
                    print u"{0} v{1}: Decrypted with key {2:s} after {3:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,keyname,time.time()-self.starttime)
                    return of.name

                print u"{0} v{1}: Failed to decrypt with key {2:s} after {3:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,keyname,time.time()-self.starttime)

            # perhaps we need to get a new default ADE key
            print u"{0} v{1}: Looking for new default Adobe Digital Editions Keys after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime)

            # get the default Adobe keys
            defaultkeys = []

            try:
                if iswindows or isosx:
                    from calibre_plugins.dedrm.adobekey import adeptkeys

                    defaultkeys = adeptkeys()
                else: # linux
                    from wineutils import WineGetKeys

                    scriptpath = os.path.join(self.alfdir,u"adobekey.py")
                    defaultkeys = WineGetKeys(scriptpath, u".der",dedrmprefs['adobewineprefix'])

                self.default_key = defaultkeys[0]
            except:
                print u"{0} v{1}: Exception when getting default Adobe Key after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime)
                traceback.print_exc()
                self.default_key = u""

            newkeys = []
            for keyvalue in defaultkeys:
                if keyvalue.encode('hex') not in dedrmprefs['adeptkeys'].values():
                    newkeys.append(keyvalue)

            if len(newkeys) > 0:
                try:
                    for i,userkey in enumerate(newkeys):
                        print u"{0} v{1}: Trying a new default key".format(PLUGIN_NAME, PLUGIN_VERSION)
                        of = self.temporary_file(u".epub")

                        # Give the user key, ebook and TemporaryPersistent file to the decryption function.
                        try:
                            result = ineptepub.decryptBook(userkey, inf.name, of.name)
                        except:
                            print u"{0} v{1}: Exception when decrypting after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime)
                            traceback.print_exc()
                            result = 1

                        of.close()

                        if  result == 0:
                            # Decryption was a success
                            # Store the new successful key in the defaults
                            print u"{0} v{1}: Saving a new default key".format(PLUGIN_NAME, PLUGIN_VERSION)
                            try:
                                dedrmprefs.addnamedvaluetoprefs('adeptkeys','default_key',keyvalue.encode('hex'))
                                dedrmprefs.writeprefs()
                                print u"{0} v{1}: Saved a new default key after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,time.time()-self.starttime)
                            except:
                                print u"{0} v{1}: Exception when saving a new default key after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime)
                                traceback.print_exc()
                            print u"{0} v{1}: Decrypted with new default key after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,time.time()-self.starttime)
                            # Return the modified PersistentTemporary file to calibre.
                            return of.name

                        print u"{0} v{1}: Failed to decrypt with new default key after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,time.time()-self.starttime)
                except Exception, e:
                    print u"{0} v{1}: Unexpected Exception trying a new default key after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime)
                    traceback.print_exc()
                    pass

            # Something went wrong with decryption.
            print u"{0} v{1}: Ultimately failed to decrypt after {2:.1f} seconds. Read the FAQs at Harper's repository: https://github.com/apprenticeharper/DeDRM_tools/blob/master/FAQs.md".format(PLUGIN_NAME, PLUGIN_VERSION,time.time()-self.starttime)
            raise DeDRMError(u"{0} v{1}: Ultimately failed to decrypt after {2:.1f} seconds. Read the FAQs at Harper's repository: https://github.com/apprenticeharper/DeDRM_tools/blob/master/FAQs.md".format(PLUGIN_NAME, PLUGIN_VERSION,time.time()-self.starttime))

        # Not a Barnes & Noble nor an Adobe Adept
        # Import the fixed epub.
        print u"{0} v{1}: “{2}” is neither an Adobe Adept nor a Barnes & Noble encrypted ePub".format(PLUGIN_NAME, PLUGIN_VERSION, os.path.basename(path_to_ebook))
        raise DeDRMError(u"{0} v{1}: Couldn't decrypt after {2:.1f} seconds. DRM free perhaps?".format(PLUGIN_NAME, PLUGIN_VERSION,time.time()-self.starttime))

    def PDFDecrypt(self,path_to_ebook):
        import calibre_plugins.dedrm.prefs as prefs
        import calibre_plugins.dedrm.ineptpdf

        dedrmprefs = prefs.DeDRM_Prefs()
        # Attempt to decrypt epub with each encryption key (generated or provided).
        print u"{0} v{1}: {2} is a PDF ebook".format(PLUGIN_NAME, PLUGIN_VERSION, os.path.basename(path_to_ebook))
        for keyname, userkeyhex in dedrmprefs['adeptkeys'].items():
            userkey = userkeyhex.decode('hex')
            print u"{0} v{1}: Trying Encryption key {2:s}".format(PLUGIN_NAME, PLUGIN_VERSION, keyname)
            of = self.temporary_file(u".pdf")

            # Give the user key, ebook and TemporaryPersistent file to the decryption function.
            try:
                result = ineptpdf.decryptBook(userkey, path_to_ebook, of.name)
            except:
                print u"{0} v{1}: Exception when decrypting after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime)
                traceback.print_exc()
                result = 1

            of.close()

            if  result == 0:
                # Decryption was successful.
                # Return the modified PersistentTemporary file to calibre.
                return of.name

            print u"{0} v{1}: Failed to decrypt with key {2:s} after {3:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,keyname,time.time()-self.starttime)

        # perhaps we need to get a new default ADE key
        print u"{0} v{1}: Looking for new default Adobe Digital Editions Keys after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime)

        # get the default Adobe keys
        defaultkeys = []

        try:
            if iswindows or isosx:
                from calibre_plugins.dedrm.adobekey import adeptkeys

                defaultkeys = adeptkeys()
            else: # linux
                from wineutils import WineGetKeys

                scriptpath = os.path.join(self.alfdir,u"adobekey.py")
                defaultkeys = WineGetKeys(scriptpath, u".der",dedrmprefs['adobewineprefix'])

            self.default_key = defaultkeys[0]
        except:
            print u"{0} v{1}: Exception when getting default Adobe Key after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime)
            traceback.print_exc()
            self.default_key = u""

        newkeys = []
        for keyvalue in defaultkeys:
            if keyvalue.encode('hex') not in dedrmprefs['adeptkeys'].values():
                newkeys.append(keyvalue)

        if len(newkeys) > 0:
            try:
                for i,userkey in enumerate(newkeys):
                    print u"{0} v{1}: Trying a new default key".format(PLUGIN_NAME, PLUGIN_VERSION)
                    of = self.temporary_file(u".pdf")

                    # Give the user key, ebook and TemporaryPersistent file to the decryption function.
                    try:
                        result = ineptpdf.decryptBook(userkey, path_to_ebook, of.name)
                    except:
                        print u"{0} v{1}: Exception when decrypting after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime)
                        traceback.print_exc()
                        result = 1

                    of.close()

                    if  result == 0:
                        # Decryption was a success
                        # Store the new successful key in the defaults
                        print u"{0} v{1}: Saving a new default key".format(PLUGIN_NAME, PLUGIN_VERSION)
                        try:
                            dedrmprefs.addnamedvaluetoprefs('adeptkeys','default_key',keyvalue.encode('hex'))
                            dedrmprefs.writeprefs()
                            print u"{0} v{1}: Saved a new default key after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,time.time()-self.starttime)
                        except:
                            print u"{0} v{1}: Exception when saving a new default key after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime)
                            traceback.print_exc()
                        # Return the modified PersistentTemporary file to calibre.
                        return of.name

                    print u"{0} v{1}: Failed to decrypt with new default key after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,time.time()-self.starttime)
            except Exception, e:
                pass

        # Something went wrong with decryption.
        print u"{0} v{1}: Ultimately failed to decrypt after {2:.1f} seconds. Read the FAQs at Harper's repository: https://github.com/apprenticeharper/DeDRM_tools/blob/master/FAQs.md".format(PLUGIN_NAME, PLUGIN_VERSION,time.time()-self.starttime)
        raise DeDRMError(u"{0} v{1}: Ultimately failed to decrypt after {2:.1f} seconds. Read the FAQs at Harper's repository: https://github.com/apprenticeharper/DeDRM_tools/blob/master/FAQs.md".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))


    def KindleMobiDecrypt(self,path_to_ebook):

        # add the alfcrypto directory to sys.path so alfcrypto.py
        # will be able to locate the custom lib(s) for CDLL import.
        sys.path.insert(0, self.alfdir)
        # Had to move this import here so the custom libs can be
        # extracted to the appropriate places beforehand these routines
        # look for them.
        import calibre_plugins.dedrm.prefs as prefs
        import calibre_plugins.dedrm.k4mobidedrm

        dedrmprefs = prefs.DeDRM_Prefs()
        pids = dedrmprefs['pids']
        serials = dedrmprefs['serials']
        for android_serials_list in dedrmprefs['androidkeys'].values():
            #print android_serials_list
            serials.extend(android_serials_list)
        #print serials
        androidFiles = []
        kindleDatabases = dedrmprefs['kindlekeys'].items()

        try:
            book = k4mobidedrm.GetDecryptedBook(path_to_ebook,kindleDatabases,androidFiles,serials,pids,self.starttime)
        except Exception, e:
            decoded = False
            # perhaps we need to get a new default Kindle for Mac/PC key
            defaultkeys = []
            print u"{0} v{1}: Failed to decrypt with error: {2}".format(PLUGIN_NAME, PLUGIN_VERSION,e.args[0])
            print u"{0} v{1}: Looking for new default Kindle Key after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime)

            try:
                if iswindows or isosx:
                    from calibre_plugins.dedrm.kindlekey import kindlekeys

                    defaultkeys = kindlekeys()
                else: # linux
                    from wineutils import WineGetKeys

                    scriptpath = os.path.join(self.alfdir,u"kindlekey.py")
                    defaultkeys = WineGetKeys(scriptpath, u".k4i",dedrmprefs['kindlewineprefix'])
            except:
                print u"{0} v{1}: Exception when getting default Kindle Key after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime)
                traceback.print_exc()
                pass

            newkeys = {}
            for i,keyvalue in enumerate(defaultkeys):
                keyname = u"default_key_{0:d}".format(i+1)
                if keyvalue not in dedrmprefs['kindlekeys'].values():
                    newkeys[keyname] = keyvalue
            if len(newkeys) > 0:
                print u"{0} v{1}: Found {2} new {3}".format(PLUGIN_NAME, PLUGIN_VERSION, len(newkeys), u"key" if len(newkeys)==1 else u"keys")
                try:
                    book = k4mobidedrm.GetDecryptedBook(path_to_ebook,newkeys.items(),[],[],[],self.starttime)
                    decoded = True
                    # store the new successful keys in the defaults
                    print u"{0} v{1}: Saving {2} new {3}".format(PLUGIN_NAME, PLUGIN_VERSION, len(newkeys), u"key" if len(newkeys)==1 else u"keys")
                    for keyvalue in newkeys.values():
                        dedrmprefs.addnamedvaluetoprefs('kindlekeys','default_key',keyvalue)
                    dedrmprefs.writeprefs()
                except Exception, e:
                    pass
            if not decoded:
                #if you reached here then no luck raise and exception
                print u"{0} v{1}: Ultimately failed to decrypt after {2:.1f} seconds. Read the FAQs at Harper's repository: https://github.com/apprenticeharper/DeDRM_tools/blob/master/FAQs.md".format(PLUGIN_NAME, PLUGIN_VERSION,time.time()-self.starttime)
                raise DeDRMError(u"{0} v{1}: Ultimately failed to decrypt after {2:.1f} seconds. Read the FAQs at Harper's repository: https://github.com/apprenticeharper/DeDRM_tools/blob/master/FAQs.md".format(PLUGIN_NAME, PLUGIN_VERSION,time.time()-self.starttime))

        of = self.temporary_file(book.getBookExtension())
        book.getFile(of.name)
        of.close()
        book.cleanup()
        return of.name


    def eReaderDecrypt(self,path_to_ebook):

        import calibre_plugins.dedrm.prefs as prefs
        import calibre_plugins.dedrm.erdr2pml

        dedrmprefs = prefs.DeDRM_Prefs()
        # Attempt to decrypt epub with each encryption key (generated or provided).
        for keyname, userkey in dedrmprefs['ereaderkeys'].items():
            keyname_masked = u"".join((u'X' if (x.isdigit()) else x) for x in keyname)
            print u"{0} v{1}: Trying Encryption key {2:s}".format(PLUGIN_NAME, PLUGIN_VERSION, keyname_masked)
            of = self.temporary_file(u".pmlz")

            # Give the userkey, ebook and TemporaryPersistent file to the decryption function.
            result = erdr2pml.decryptBook(path_to_ebook, of.name, True, userkey.decode('hex'))

            of.close()

            # Decryption was successful return the modified PersistentTemporary
            # file to Calibre's import process.
            if  result == 0:
                print u"{0} v{1}: Successfully decrypted with key {2:s} after {3:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,keyname_masked,time.time()-self.starttime)
                return of.name

            print u"{0} v{1}: Failed to decrypt with key {2:s} after {3:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,keyname_masked,time.time()-self.starttime)

        print u"{0} v{1}: Ultimately failed to decrypt after {2:.1f} seconds. Read the FAQs at Harper's repository: https://github.com/apprenticeharper/DeDRM_tools/blob/master/FAQs.md".format(PLUGIN_NAME, PLUGIN_VERSION,time.time()-self.starttime)
        raise DeDRMError(u"{0} v{1}: Ultimately failed to decrypt after {2:.1f} seconds. Read the FAQs at Harper's repository: https://github.com/apprenticeharper/DeDRM_tools/blob/master/FAQs.md".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))


    def run(self, path_to_ebook):

        # make sure any unicode output gets converted safely with 'replace'
        sys.stdout=SafeUnbuffered(sys.stdout)
        sys.stderr=SafeUnbuffered(sys.stderr)

        print u"{0} v{1}: Trying to decrypt {2}".format(PLUGIN_NAME, PLUGIN_VERSION, os.path.basename(path_to_ebook))
        self.starttime = time.time()

        booktype = os.path.splitext(path_to_ebook)[1].lower()[1:]
        if booktype in ['prc','mobi','pobi','azw','azw1','azw3','azw4','tpz','kfx-zip']:
            # Kindle/Mobipocket
            decrypted_ebook = self.KindleMobiDecrypt(path_to_ebook)
        elif booktype == 'pdb':
            # eReader
            decrypted_ebook = self.eReaderDecrypt(path_to_ebook)
            pass
        elif booktype == 'pdf':
            # Adobe Adept PDF (hopefully)
            decrypted_ebook = self.PDFDecrypt(path_to_ebook)
            pass
        elif booktype == 'epub':
            # Adobe Adept or B&N ePub
            decrypted_ebook = self.ePubDecrypt(path_to_ebook)
        else:
            print u"Unknown booktype {0}. Passing back to calibre unchanged".format(booktype)
            return path_to_ebook
        print u"{0} v{1}: Finished after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,time.time()-self.starttime)
        return decrypted_ebook

    def is_customizable(self):
        # return true to allow customization via the Plugin->Preferences.
        return True

    def config_widget(self):
        import calibre_plugins.dedrm.config as config
        return config.ConfigWidget(self.plugin_path, self.alfdir)

    def save_settings(self, config_widget):
        config_widget.save_settings()
