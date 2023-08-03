#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

# __init__.py for DeDRM_plugin
# Copyright © 2008-2020 Apprentice Harper et al.
# Copyright © 2021-2023 NoDRM

__license__   = 'GPL v3'
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
#   6.8.1 - Kindle key fix for Mac OS X Big Sur
#   7.0.0 - Switched to Python 3 for calibre 5.0. Thanks to all who contributed
#   7.0.1 - More Python 3 changes. Adobe PDF decryption should now work in some cases
#   7.0.2 - More Python 3 changes. Adobe PDF decryption should now work on PC too.
#   7.0.3 - More Python 3 changes. Integer division in ineptpdf.py
#   7.1.0 - Full release for calibre 5.x
#   7.2.0 - Update for latest KFX changes, and Python 3 Obok fixes.
#   7.2.1 - Whitespace!
#  10.0.0 - First forked version by NoDRM. See CHANGELOG.md for details.
#  10.0.1 - Fixes a bug in the watermark code.
#  10.0.2 - Fix Kindle for Mac & update Adobe key retrieval
#  For changes made in 10.0.3 and above, see the CHANGELOG.md file

"""
Decrypt DRMed ebooks.
"""

import codecs
import sys, os
import time
import traceback

#@@CALIBRE_COMPAT_CODE@@

try: 
    try: 
        from . import __version
    except:
        import __version
except: 
    print("#############################")
    print("Failed to load the DeDRM plugin")
    print("Did you bundle this from source code yourself? If so, you'll need to run make_release.py instead to generate a valid plugin file.")
    print("If you have no idea what the above means, please redownload the most recent version of the plugin from the Github Releases page.")
    print("If you still receive this error with the released version, please open a bug report and attach the following information:")
    print("#############################")
    print("Debug information:")
    print("__version not found, path is:")
    print(sys.path)
    print("I'm at:")
    print(__file__)
    print("#############################")
    raise


class DeDRMError(Exception):
    pass

try: 
    from calibre.customize import FileTypePlugin
except: 
    # Allow import without Calibre.
    class FileTypePlugin:
        pass

try:
    from calibre.constants import iswindows, isosx
except:
    iswindows = sys.platform.startswith('win')
    isosx = sys.platform.startswith('darwin')

try: 
    from calibre.utils.config import config_dir
except:
    config_dir = ""

try: 
    from . import utilities
except: 
    import utilities


PLUGIN_NAME = __version.PLUGIN_NAME
PLUGIN_VERSION = __version.PLUGIN_VERSION
PLUGIN_VERSION_TUPLE = __version.PLUGIN_VERSION_TUPLE

class DeDRM(FileTypePlugin):
    name                    = PLUGIN_NAME
    description             = "Removes DRM from Adobe Adept (including Kobo), Barnes & Noble, Amazon Kindle, Mobipocket and eReader ebooks. Credit given to i♥cabbages and The Dark Reverser for the original stand-alone scripts."
    supported_platforms     = ['linux', 'osx', 'windows']
    author                  = "Apprentice Alf, Apprentice Harper, NoDRM, The Dark Reverser and i♥cabbages"
    version                 = PLUGIN_VERSION_TUPLE
    #minimum_calibre_version = (5, 0, 0)  # Python 3.
    minimum_calibre_version = (2, 0, 0)  # Needs Calibre 1.0 minimum. 1.X untested.
    file_types              = set(['epub','pdf','pdb','prc','mobi','pobi','azw','azw1','azw3','azw4','azw8','tpz','kfx','kfx-zip'])
    on_import               = True
    on_preprocess           = True
    priority                = 600


    def cli_main(self, data):
        from .standalone import main
        main(data)
    
    def initialize(self):
        """
        Extracting a couple Python scripts if running on Linux, 
        just in case we need to run them in Wine.

        The extraction only happens once per version of the plugin
        Also perform upgrade of preferences once per version
        """

        try:
            self.pluginsdir = os.path.join(config_dir,"plugins")
            if not os.path.exists(self.pluginsdir):
                os.mkdir(self.pluginsdir)
            self.maindir = os.path.join(self.pluginsdir,"DeDRM")
            if not os.path.exists(self.maindir):
                os.mkdir(self.maindir)
            self.helpdir = os.path.join(self.maindir,"help")
            if not os.path.exists(self.helpdir):
                os.mkdir(self.helpdir)
            self.alfdir = os.path.join(self.maindir,"libraryfiles")
            if not os.path.exists(self.alfdir):
                os.mkdir(self.alfdir)
            # only continue if we've never run this version of the plugin before
            self.verdir = os.path.join(self.maindir,PLUGIN_VERSION)
            if not os.path.exists(self.verdir) and not iswindows and not isosx:

                names = ["kindlekey.py","adobekey.py","ignoblekeyNookStudy.py","utilities.py","argv_utils.py"]

                lib_dict = self.load_resources(names)
                print("{0} v{1}: Copying needed Python scripts from plugin's zip".format(PLUGIN_NAME, PLUGIN_VERSION))

                for entry, data in lib_dict.items():
                    file_path = os.path.join(self.alfdir, entry)
                    try:
                        os.remove(file_path)
                    except:
                        pass

                    try:
                        open(file_path,'wb').write(data)
                    except:
                        print("{0} v{1}: Exception when copying needed python scripts".format(PLUGIN_NAME, PLUGIN_VERSION))
                        traceback.print_exc()
                        pass

                # mark that this version has been initialized
                os.mkdir(self.verdir)
        except Exception as e:
            traceback.print_exc()
            raise

    def postProcessEPUB(self, path_to_ebook):
        # This is called after the DRM is removed (or if no DRM was present)
        # It does stuff like de-obfuscating fonts (by calling checkFonts) 
        # or removing watermarks. 

        postProcessStart = time.time()

        try: 
            import prefs
            dedrmprefs = prefs.DeDRM_Prefs()

            if dedrmprefs["deobfuscate_fonts"] is True:
                # Deobfuscate fonts
                path_to_ebook = self.checkFonts(path_to_ebook) or path_to_ebook

            if dedrmprefs["remove_watermarks"] is True:
                import epubwatermark as watermark

                # Remove Tolino's CDP watermark file
                path_to_ebook = watermark.removeCDPwatermark(self, path_to_ebook) or path_to_ebook

                # Remove watermarks (Amazon or LemonInk) from the OPF file
                path_to_ebook = watermark.removeOPFwatermarks(self, path_to_ebook) or path_to_ebook

                # Remove watermarks (Adobe, Pocketbook or LemonInk) from all HTML and XHTML files
                path_to_ebook = watermark.removeHTMLwatermarks(self, path_to_ebook) or path_to_ebook

            
            
            postProcessEnd = time.time()
            print("{0} v{1}: Post-processing took {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, postProcessEnd-postProcessStart))

            return path_to_ebook

        except: 
            print("Error while checking settings")
            return path_to_ebook

    def checkFonts(self, path_to_ebook):
        # This is called after the normal DRM removal is done. 
        # It checks if there's fonts that need to be deobfuscated

        try: 
            import epubfontdecrypt

            output = self.temporary_file(".epub").name
            ret = epubfontdecrypt.decryptFontsBook(path_to_ebook, output)

            if (ret == 0):
                return output
            elif (ret == 1):
                return path_to_ebook
            else:
                print("{0} v{1}: Error during font deobfuscation".format(PLUGIN_NAME, PLUGIN_VERSION))
                raise DeDRMError("Font deobfuscation failed")
 
        except: 
            print("{0} v{1}: Error during font deobfuscation".format(PLUGIN_NAME, PLUGIN_VERSION))
            traceback.print_exc()
            return path_to_ebook

    def ePubDecrypt(self,path_to_ebook):
        # Create a TemporaryPersistent file to work with.
        # Check original epub archive for zip errors.
        import zipfix

        inf = self.temporary_file(".epub")
        try:
            print("{0} v{1}: Verifying zip archive integrity".format(PLUGIN_NAME, PLUGIN_VERSION))
            fr = zipfix.fixZip(path_to_ebook, inf.name)
            fr.fix()
        except Exception as e:
            print("{0} v{1}: Error \'{2}\' when checking zip archive".format(PLUGIN_NAME, PLUGIN_VERSION, e.args[0]))
            raise

        # import the decryption keys
        import prefs
        dedrmprefs = prefs.DeDRM_Prefs()


        # import the LCP handler
        import lcpdedrm

        if (lcpdedrm.isLCPbook(path_to_ebook)):
            try: 
                retval = lcpdedrm.decryptLCPbook(path_to_ebook, dedrmprefs['lcp_passphrases'], self)
            except:
                print("Looks like that didn't work:")
                raise

            return self.postProcessEPUB(retval)
        

        # Not an LCP book, do the normal EPUB (Adobe) handling.

        # import the Adobe ePub handler
        import ineptepub

        if ineptepub.adeptBook(inf.name):

            if ineptepub.isPassHashBook(inf.name): 
                # This is an Adobe PassHash / B&N encrypted eBook
                print("{0} v{1}: “{2}” is a secure PassHash-protected (B&N) ePub".format(PLUGIN_NAME, PLUGIN_VERSION, os.path.basename(path_to_ebook)))

                # Attempt to decrypt epub with each encryption key (generated or provided).
                for keyname, userkey in dedrmprefs['bandnkeys'].items():
                    print("{0} v{1}: Trying Encryption key {2:s}".format(PLUGIN_NAME, PLUGIN_VERSION, keyname))
                    of = self.temporary_file(".epub")

                    # Give the user key, ebook and TemporaryPersistent file to the decryption function.
                    try:
                        result = ineptepub.decryptBook(userkey, inf.name, of.name)
                    except:
                        print("{0} v{1}: Exception when trying to decrypt after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))
                        traceback.print_exc()
                        result = 1

                    of.close()

                    if  result == 0:
                        # Decryption was successful.
                        # Return the modified PersistentTemporary file to calibre.
                        return self.postProcessEPUB(of.name)

                    print("{0} v{1}: Failed to decrypt with key {2:s} after {3:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,keyname,time.time()-self.starttime))

                # perhaps we should see if we can get a key from a log file
                print("{0} v{1}: Looking for new NOOK Keys after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))

                # get the default NOOK keys
                defaultkeys = []

                ###### Add keys from the NOOK Study application (ignoblekeyNookStudy.py)

                try:
                    defaultkeys_study = []
                    if iswindows or isosx:
                        from ignoblekeyNookStudy import nookkeys

                        defaultkeys_study = nookkeys()
                    else: # linux
                        from wineutils import WineGetKeys

                        scriptpath = os.path.join(self.alfdir,"ignoblekeyNookStudy.py")
                        defaultkeys_study, defaultnames_study = WineGetKeys(scriptpath, ".b64",dedrmprefs['adobewineprefix'])

                except:
                    print("{0} v{1}: Exception when getting default NOOK Study Key after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))
                    traceback.print_exc()
                

                ###### Add keys from the NOOK Microsoft Store application (ignoblekeyNookStudy.py)

                try:
                    defaultkeys_store = []
                    if iswindows:
                        # That's a Windows store app, it won't run on Linux or MacOS anyways.
                        # No need to waste time running Wine.
                        from ignoblekeyWindowsStore import dump_keys as dump_nook_keys
                        defaultkeys_store = dump_nook_keys(False)

                except:
                    print("{0} v{1}: Exception when getting default NOOK Microsoft App keys after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))
                    traceback.print_exc()

                ###### Add keys from Adobe PassHash ADE activation data (adobekey_get_passhash.py)

                try: 
                    defaultkeys_ade = []
                    if iswindows:
                        # Right now this is only implemented for Windows. MacOS support still needs to be added.
                        from adobekey_get_passhash import passhash_keys, ADEPTError
                        try: 
                            defaultkeys_ade, names = passhash_keys()
                        except ADEPTError:
                            defaultkeys_ade = []
                    if isosx:
                        print("{0} v{1}: Dumping ADE PassHash data is not yet supported on MacOS.".format(PLUGIN_NAME, PLUGIN_VERSION))
                        defaultkeys_ade = []
                except:
                    print("{0} v{1}: Exception when getting PassHashes from ADE after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))
                    traceback.print_exc()


                ###### Check if one of the new keys decrypts the book:

                newkeys = []
                for keyvalue in defaultkeys_study:
                    if keyvalue not in dedrmprefs['bandnkeys'].values() and keyvalue not in newkeys:
                        newkeys.append(keyvalue)

                if iswindows:
                    for keyvalue in defaultkeys_store:
                        if keyvalue not in dedrmprefs['bandnkeys'].values() and keyvalue not in newkeys:
                            newkeys.append(keyvalue)

                    for keyvalue in defaultkeys_ade:
                        if keyvalue not in dedrmprefs['bandnkeys'].values() and keyvalue not in newkeys:
                            newkeys.append(keyvalue)

                if len(newkeys) > 0:
                    try:
                        for i,userkey in enumerate(newkeys):

                            if len(userkey) == 0:
                                print("{0} v{1}: Skipping empty key.".format(PLUGIN_NAME, PLUGIN_VERSION))    
                                continue

                            print("{0} v{1}: Trying a new default key".format(PLUGIN_NAME, PLUGIN_VERSION))

                            of = self.temporary_file(".epub")

                            # Give the user key, ebook and TemporaryPersistent file to the decryption function.
                            try:
                                result = ineptepub.decryptBook(userkey, inf.name, of.name)
                            except:
                                print("{0} v{1}: Exception when trying to decrypt after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))
                                traceback.print_exc()
                                result = 1

                            of.close()

                            if result == 0:
                                # Decryption was a success
                                # Store the new successful key in the defaults
                                print("{0} v{1}: Saving a new default key".format(PLUGIN_NAME, PLUGIN_VERSION))
                                try:
                                    if userkey in defaultkeys_ade:
                                        dedrmprefs.addnamedvaluetoprefs('bandnkeys','ade_passhash_'+str(int(time.time())),keyvalue)
                                    else:
                                        dedrmprefs.addnamedvaluetoprefs('bandnkeys','nook_key_'+str(int(time.time())),keyvalue)
                                    dedrmprefs.writeprefs()
                                    print("{0} v{1}: Saved a new default key after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,time.time()-self.starttime))
                                except:
                                    print("{0} v{1}: Exception saving a new default key after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))
                                    traceback.print_exc()
                                # Return the modified PersistentTemporary file to calibre.
                                return self.postProcessEPUB(of.name)

                            print("{0} v{1}: Failed to decrypt with new default key after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,time.time()-self.starttime))
                            return inf.name
                    
                    except:
                        pass

                # Looks like we were unable to decrypt the book ...
                return inf.name

            else: 
                # This is a "normal" Adobe eBook.

                book_uuid = None
                try: 
                    # This tries to figure out which Adobe account UUID the book is licensed for. 
                    # If we know that we can directly use the correct key instead of having to
                    # try them all.
                    book_uuid = ineptepub.adeptGetUserUUID(inf.name)
                except: 
                    pass

                if book_uuid is None: 
                    print("{0} v{1}: {2} is a secure Adobe Adept ePub".format(PLUGIN_NAME, PLUGIN_VERSION, os.path.basename(path_to_ebook)))
                else: 
                    print("{0} v{1}: {2} is a secure Adobe Adept ePub for UUID {3}".format(PLUGIN_NAME, PLUGIN_VERSION, os.path.basename(path_to_ebook), book_uuid))


                if book_uuid is not None: 
                    # Check if we have a key with that UUID in its name: 
                    for keyname, userkeyhex in dedrmprefs['adeptkeys'].items():
                        if not book_uuid.lower() in keyname.lower(): 
                            continue

                        # Found matching key
                        print("{0} v{1}: Trying UUID-matched encryption key {2:s}".format(PLUGIN_NAME, PLUGIN_VERSION, keyname))
                        of = self.temporary_file(".epub")
                        try: 
                            userkey = codecs.decode(userkeyhex, 'hex')
                            result = ineptepub.decryptBook(userkey, inf.name, of.name)
                            of.close()
                            if result == 0:
                                print("{0} v{1}: Decrypted with key {2:s} after {3:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,keyname,time.time()-self.starttime))
                                return self.postProcessEPUB(of.name)
                        except ineptepub.ADEPTNewVersionError:
                            print("{0} v{1}: Book uses unsupported (too new) Adobe DRM.".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))
                            return self.postProcessEPUB(path_to_ebook)

                        except:
                            print("{0} v{1}: Exception when decrypting after {2:.1f} seconds - trying other keys".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))
                            traceback.print_exc()


                # Attempt to decrypt epub with each encryption key (generated or provided).
                for keyname, userkeyhex in dedrmprefs['adeptkeys'].items():
                    
                    print("{0} v{1}: Trying Encryption key {2:s}".format(PLUGIN_NAME, PLUGIN_VERSION, keyname))
                    of = self.temporary_file(".epub")

                    # Give the user key, ebook and TemporaryPersistent file to the decryption function.
                    try:
                        userkey = codecs.decode(userkeyhex, 'hex')
                        result = ineptepub.decryptBook(userkey, inf.name, of.name)
                    except ineptepub.ADEPTNewVersionError:
                        print("{0} v{1}: Book uses unsupported (too new) Adobe DRM.".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))
                        return self.postProcessEPUB(path_to_ebook)
                    except:
                        print("{0} v{1}: Exception when decrypting after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))
                        traceback.print_exc()
                        result = 1

                    try:
                        of.close()
                    except:
                        print("{0} v{1}: Exception closing temporary file after {2:.1f} seconds. Ignored.".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))

                    if  result == 0:
                        # Decryption was successful.
                        # Return the modified PersistentTemporary file to calibre.
                        print("{0} v{1}: Decrypted with key {2:s} after {3:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,keyname,time.time()-self.starttime))
                        return self.postProcessEPUB(of.name)

                    print("{0} v{1}: Failed to decrypt with key {2:s} after {3:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,keyname,time.time()-self.starttime))

                # perhaps we need to get a new default ADE key
                print("{0} v{1}: Looking for new default Adobe Digital Editions Keys after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))

                # get the default Adobe keys
                defaultkeys = []

                try:
                    if iswindows or isosx:
                        from adobekey import adeptkeys

                        defaultkeys, defaultnames = adeptkeys()
                    else: # linux
                        from wineutils import WineGetKeys

                        scriptpath = os.path.join(self.alfdir,"adobekey.py")
                        defaultkeys, defaultnames = WineGetKeys(scriptpath, ".der",dedrmprefs['adobewineprefix'])

                except:
                    print("{0} v{1}: Exception when getting default Adobe Key after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))
                    traceback.print_exc()

                newkeys = []
                newnames = []
                idx = 0
                for keyvalue in defaultkeys:
                    if codecs.encode(keyvalue, 'hex').decode('ascii') not in dedrmprefs['adeptkeys'].values():
                        newkeys.append(keyvalue)
                        newnames.append("default_ade_key_uuid_" + defaultnames[idx])
                    idx += 1

                # Check for DeACSM keys:
                try: 
                    from config import checkForDeACSMkeys

                    newkey, newname = checkForDeACSMkeys()

                    if newkey is not None: 
                        if codecs.encode(newkey, 'hex').decode('ascii') not in dedrmprefs['adeptkeys'].values():
                            print("{0} v{1}: Found new key '{2}' in DeACSM plugin".format(PLUGIN_NAME, PLUGIN_VERSION, newname))
                            newkeys.append(newkey)
                            newnames.append(newname)
                except:
                    traceback.print_exc()
                    pass

                if len(newkeys) > 0:
                    try:
                        for i,userkey in enumerate(newkeys):
                            print("{0} v{1}: Trying a new default key".format(PLUGIN_NAME, PLUGIN_VERSION))
                            of = self.temporary_file(".epub")

                            # Give the user key, ebook and TemporaryPersistent file to the decryption function.
                            try:
                                result = ineptepub.decryptBook(userkey, inf.name, of.name)
                            except:
                                print("{0} v{1}: Exception when decrypting after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))
                                traceback.print_exc()
                                result = 1

                            of.close()

                            if  result == 0:
                                # Decryption was a success
                                # Store the new successful key in the defaults
                                print("{0} v{1}: Saving a new default key".format(PLUGIN_NAME, PLUGIN_VERSION))
                                try:
                                    dedrmprefs.addnamedvaluetoprefs('adeptkeys', newnames[i], codecs.encode(userkey, 'hex').decode('ascii'))
                                    dedrmprefs.writeprefs()
                                    print("{0} v{1}: Saved a new default key after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,time.time()-self.starttime))
                                except:
                                    print("{0} v{1}: Exception when saving a new default key after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))
                                    traceback.print_exc()
                                print("{0} v{1}: Decrypted with new default key after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,time.time()-self.starttime))
                                # Return the modified PersistentTemporary file to calibre.
                                return self.postProcessEPUB(of.name)

                            print("{0} v{1}: Failed to decrypt with new default key after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,time.time()-self.starttime))
                    except Exception as e:
                        print("{0} v{1}: Unexpected Exception trying a new default key after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))
                        traceback.print_exc()
                        pass

                # Something went wrong with decryption.
                print("{0} v{1}: Ultimately failed to decrypt after {2:.1f} seconds. Read the FAQs at noDRM's repository: https://github.com/noDRM/DeDRM_tools/blob/master/FAQs.md".format(PLUGIN_NAME, PLUGIN_VERSION,time.time()-self.starttime))
                raise DeDRMError("{0} v{1}: Ultimately failed to decrypt after {2:.1f} seconds. Read the FAQs at noDRM's repository: https://github.com/noDRM/DeDRM_tools/blob/master/FAQs.md".format(PLUGIN_NAME, PLUGIN_VERSION,time.time()-self.starttime))



        # Not a Barnes & Noble nor an Adobe Adept
        # Probably a DRM-free EPUB, but we should still check for fonts.
        return self.postProcessEPUB(inf.name)

    
    def PDFIneptDecrypt(self, path_to_ebook):
        # Sub function to prevent PDFDecrypt from becoming too large ...
        import prefs
        import ineptpdf
        dedrmprefs = prefs.DeDRM_Prefs()

        book_uuid = None
        try: 
            # Try to figure out which Adobe account this book is licensed for.
            book_uuid = ineptpdf.adeptGetUserUUID(path_to_ebook)
        except:
            pass

        if book_uuid is not None: 
            print("{0} v{1}: {2} is a PDF ebook (EBX) for UUID {3}".format(PLUGIN_NAME, PLUGIN_VERSION, os.path.basename(path_to_ebook), book_uuid))
            # Check if we have a key for that UUID
            for keyname, userkeyhex in dedrmprefs['adeptkeys'].items():
                if not book_uuid.lower() in keyname.lower():
                    continue
            
                # Found matching key
                print("{0} v{1}: Trying UUID-matched encryption key {2:s}".format(PLUGIN_NAME, PLUGIN_VERSION, keyname))
                of = self.temporary_file(".pdf")

                try: 
                    userkey = codecs.decode(userkeyhex, 'hex')
                    result = ineptpdf.decryptBook(userkey, path_to_ebook, of.name)
                    of.close()
                    if result == 0:
                        print("{0} v{1}: Decrypted with key {2:s} after {3:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,keyname,time.time()-self.starttime))
                        return of.name
                       
                except ineptpdf.ADEPTNewVersionError:
                    print("{0} v{1}: Book uses unsupported (too new) Adobe DRM.".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))
                    return path_to_ebook
                except:
                    print("{0} v{1}: Exception when decrypting after {2:.1f} seconds - trying other keys".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))
                    traceback.print_exc()


        # If we end up here, we didn't find a key with a matching UUID, so lets just try all of them.

        # Attempt to decrypt PDF with each encryption key (generated or provided).        
        for keyname, userkeyhex in dedrmprefs['adeptkeys'].items():
            userkey = codecs.decode(userkeyhex,'hex')
            print("{0} v{1}: Trying encryption key {2:s}".format(PLUGIN_NAME, PLUGIN_VERSION, keyname))
            of = self.temporary_file(".pdf")

            # Give the user key, ebook and TemporaryPersistent file to the decryption function.
            try:
                result = ineptpdf.decryptBook(userkey, path_to_ebook, of.name)
            except ineptpdf.ADEPTNewVersionError:
                print("{0} v{1}: Book uses unsupported (too new) Adobe DRM.".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))
                return path_to_ebook
            except:
                print("{0} v{1}: Exception when decrypting after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))
                traceback.print_exc()
                result = 1

            of.close()

            if  result == 0:
                # Decryption was successful.
                # Return the modified PersistentTemporary file to calibre.
                print("{0} v{1}: Decrypted with key {2:s} after {3:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,keyname,time.time()-self.starttime))
                return of.name

            print("{0} v{1}: Failed to decrypt with key {2:s} after {3:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,keyname,time.time()-self.starttime))

        # perhaps we need to get a new default ADE key
        print("{0} v{1}: Looking for new default Adobe Digital Editions Keys after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))

        # get the default Adobe keys
        defaultkeys = []

        try:
            if iswindows or isosx:
                from adobekey import adeptkeys

                defaultkeys, defaultnames = adeptkeys()
            else: # linux
                from wineutils import WineGetKeys

                scriptpath = os.path.join(self.alfdir,"adobekey.py")
                defaultkeys, defaultnames = WineGetKeys(scriptpath, ".der",dedrmprefs['adobewineprefix'])

        except:
            print("{0} v{1}: Exception when getting default Adobe Key after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))
            traceback.print_exc()

        newkeys = []
        newnames = []
        idx = 0
        for keyvalue in defaultkeys:
            if codecs.encode(keyvalue,'hex') not in dedrmprefs['adeptkeys'].values():
                newkeys.append(keyvalue)
                newnames.append("default_ade_key_uuid_" + defaultnames[idx])
            idx += 1

        # Check for DeACSM keys:
        try: 
            from config import checkForDeACSMkeys

            newkey, newname = checkForDeACSMkeys()

            if newkey is not None: 
                if codecs.encode(newkey, 'hex').decode('ascii') not in dedrmprefs['adeptkeys'].values():
                    print("{0} v{1}: Found new key '{2}' in DeACSM plugin".format(PLUGIN_NAME, PLUGIN_VERSION, newname))
                    newkeys.append(newkey)
                    newnames.append(newname)
        except:
            traceback.print_exc()

        if len(newkeys) > 0:
            try:
                for i,userkey in enumerate(newkeys):
                    print("{0} v{1}: Trying a new default key".format(PLUGIN_NAME, PLUGIN_VERSION))
                    of = self.temporary_file(".pdf")

                    # Give the user key, ebook and TemporaryPersistent file to the decryption function.
                    try:
                        result = ineptpdf.decryptBook(userkey, path_to_ebook, of.name)
                    except:
                        print("{0} v{1}: Exception when decrypting after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))
                        traceback.print_exc()
                        result = 1

                    of.close()

                    if  result == 0:
                        # Decryption was a success
                        # Store the new successful key in the defaults
                        print("{0} v{1}: Saving a new default key".format(PLUGIN_NAME, PLUGIN_VERSION))
                        try:
                            dedrmprefs.addnamedvaluetoprefs('adeptkeys', newnames[i], codecs.encode(userkey,'hex').decode('ascii'))
                            dedrmprefs.writeprefs()
                            print("{0} v{1}: Saved a new default key after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,time.time()-self.starttime))
                        except:
                            print("{0} v{1}: Exception when saving a new default key after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))
                            traceback.print_exc()
                        # Return the modified PersistentTemporary file to calibre.
                        return of.name

                    print("{0} v{1}: Failed to decrypt with new default key after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,time.time()-self.starttime))
            except Exception as e:
                traceback.print_exc()


        # Unable to decrypt the PDF with any of the existing keys. Is it a B&N PDF?
        # Attempt to decrypt PDF with each encryption key (generated or provided).        
        for keyname, userkey in dedrmprefs['bandnkeys'].items():
            print("{0} v{1}: Trying Encryption key {2:s}".format(PLUGIN_NAME, PLUGIN_VERSION, keyname))
            of = self.temporary_file(".pdf")

            # Give the user key, ebook and TemporaryPersistent file to the decryption function.
            try:
                result = ineptpdf.decryptBook(userkey, path_to_ebook, of.name, False)
            except ineptpdf.ADEPTNewVersionError:
                print("{0} v{1}: Book uses unsupported (too new) Adobe DRM.".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))
                return path_to_ebook
            except:
                print("{0} v{1}: Exception when decrypting after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))
                traceback.print_exc()
                result = 1

            of.close()

            if  result == 0:
                # Decryption was successful.
                # Return the modified PersistentTemporary file to calibre.
                print("{0} v{1}: Decrypted with key {2:s} after {3:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,keyname,time.time()-self.starttime))
                return of.name

            print("{0} v{1}: Failed to decrypt with key {2:s} after {3:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,keyname,time.time()-self.starttime))

    def PDFStandardDecrypt(self, path_to_ebook):
        # Sub function to prevent PDFDecrypt from becoming too large ...
        import prefs
        import ineptpdf
        dedrmprefs = prefs.DeDRM_Prefs()

        # Attempt to decrypt PDF with each encryption key (generated or provided).  
        i = -1
        for userpassword in [""] + dedrmprefs['adobe_pdf_passphrases']:
            # Try the empty password, too.
            i = i + 1
            userpassword = bytearray(userpassword, "utf-8")
            if i == 0:
                print("{0} v{1}: Trying empty password ... ".format(PLUGIN_NAME, PLUGIN_VERSION), end="")
            else:
                print("{0} v{1}: Trying password {2} ... ".format(PLUGIN_NAME, PLUGIN_VERSION, i), end="")
            of = self.temporary_file(".pdf")

            # Give the user password, ebook and TemporaryPersistent file to the decryption function.
            msg = False
            try:
                result = ineptpdf.decryptBook(userpassword, path_to_ebook, of.name)
                print("done")
                msg = True
            except ineptpdf.ADEPTInvalidPasswordError:
                print("invalid password".format(PLUGIN_NAME, PLUGIN_VERSION))
                msg = True
                result = 1
            except:
                print("exception\n{0} v{1}: Exception when decrypting after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))
                msg = True
                traceback.print_exc()
                result = 1
            if not msg:
                print("error\n{0} v{1}: Failed to decrypt after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,time.time()-self.starttime))

            of.close()

            if  result == 0:
                # Decryption was successful.
                # Return the modified PersistentTemporary file to calibre.
                print("{0} v{1}: Successfully decrypted with password {3} after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,time.time()-self.starttime, i))
                return of.name
        
        print("{0} v{1}: Didn't manage to decrypt PDF. Make sure the correct password is entered in the settings.".format(PLUGIN_NAME, PLUGIN_VERSION))

        
    
    def PDFDecrypt(self,path_to_ebook):
        import prefs
        import ineptpdf
        import lcpdedrm
        dedrmprefs = prefs.DeDRM_Prefs()

        if (lcpdedrm.isLCPbook(path_to_ebook)):
            try: 
                retval = lcpdedrm.decryptLCPbook(path_to_ebook, dedrmprefs['lcp_passphrases'], self)
            except:
                print("Looks like that didn't work:")
                raise

            return retval
        
        # Not an LCP book, do the normal Adobe handling.

        pdf_encryption = ineptpdf.getPDFencryptionType(path_to_ebook)
        if pdf_encryption is None:
            print("{0} v{1}: {2} is an unencrypted PDF file - returning as is.".format(PLUGIN_NAME, PLUGIN_VERSION, os.path.basename(path_to_ebook)))
            return path_to_ebook

        print("{0} v{1}: {2} is a PDF ebook with encryption {3}".format(PLUGIN_NAME, PLUGIN_VERSION, os.path.basename(path_to_ebook), pdf_encryption))

        if pdf_encryption == "EBX_HANDLER":
            # Adobe eBook / ADEPT (normal or B&N)
            return self.PDFIneptDecrypt(path_to_ebook)
        elif pdf_encryption == "Standard" or pdf_encryption == "Adobe.APS":
            return self.PDFStandardDecrypt(path_to_ebook)
        elif pdf_encryption == "FOPN_fLock" or pdf_encryption == "FOPN_foweb":
            print("{0} v{1}: FileOpen encryption '{2}' is unsupported.".format(PLUGIN_NAME, PLUGIN_VERSION, pdf_encryption))
            print("{0} v{1}: Try the standalone script from the 'Tetrachroma_FileOpen_ineptpdf' folder in the Github repo.".format(PLUGIN_NAME, PLUGIN_VERSION))
            return path_to_ebook
        else:
            print("{0} v{1}: Encryption '{2}' is unsupported.".format(PLUGIN_NAME, PLUGIN_VERSION, pdf_encryption))
            return path_to_ebook


    def KindleMobiDecrypt(self,path_to_ebook):

        # add the alfcrypto directory to sys.path so alfcrypto.py
        # will be able to locate the custom lib(s) for CDLL import.
        sys.path.insert(0, self.alfdir)
        # Had to move this import here so the custom libs can be
        # extracted to the appropriate places beforehand these routines
        # look for them.
        import prefs
        import k4mobidedrm

        dedrmprefs = prefs.DeDRM_Prefs()
        pids = dedrmprefs['pids']
        serials = dedrmprefs['serials']
        for android_serials_list in dedrmprefs['androidkeys'].values():
            #print android_serials_list
            serials.extend(android_serials_list)
        #print serials
        androidFiles = []
        kindleDatabases = list(dedrmprefs['kindlekeys'].items())

        try:
            book = k4mobidedrm.GetDecryptedBook(path_to_ebook,kindleDatabases,androidFiles,serials,pids,self.starttime)
        except Exception as e:
            decoded = False
            # perhaps we need to get a new default Kindle for Mac/PC key
            defaultkeys = []
            print("{0} v{1}: Failed to decrypt with error: {2}".format(PLUGIN_NAME, PLUGIN_VERSION,e.args[0]))

            traceback.print_exc()

            print("{0} v{1}: Looking for new default Kindle Key after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))

            try:
                if iswindows or isosx:
                    from kindlekey import kindlekeys

                    defaultkeys = kindlekeys()
                    defaultnames = []
                else: # linux
                    from wineutils import WineGetKeys

                    scriptpath = os.path.join(self.alfdir,"kindlekey.py")
                    defaultkeys, defaultnames = WineGetKeys(scriptpath, ".k4i",dedrmprefs['kindlewineprefix'])
            except:
                print("{0} v{1}: Exception when getting default Kindle Key after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))
                traceback.print_exc()
                pass

            newkeys = {}
            newnames = []

            for i,keyvalue in enumerate(defaultkeys):
                if keyvalue not in dedrmprefs['kindlekeys'].values():
                    newkeys["key_{0:d}".format(i)] = keyvalue

            if len(newkeys) > 0:
                print("{0} v{1}: Found {2} new {3}".format(PLUGIN_NAME, PLUGIN_VERSION, len(newkeys), "key" if len(newkeys)==1 else "keys"))
                try:
                    book = k4mobidedrm.GetDecryptedBook(path_to_ebook,newkeys.items(),[],[],[],self.starttime)
                    decoded = True
                    # store the new successful keys in the defaults
                    print("{0} v{1}: Saving {2} new {3}".format(PLUGIN_NAME, PLUGIN_VERSION, len(newkeys), "key" if len(newkeys)==1 else "keys"))
                    i = 1
                    for keyvalue in newkeys.values():
                        while "kindle_key_{0:d}_{1:d}".format(int(time.time()), i) in dedrmprefs['kindlekeys']:
                            i = i + 1
                        dedrmprefs.addnamedvaluetoprefs('kindlekeys',"kindle_key_{0:d}_{1:d}".format(int(time.time()), i),keyvalue)
                    dedrmprefs.writeprefs()
                except Exception as e:
                    traceback.print_exc()
                    pass
            if not decoded:
                #if you reached here then no luck raise and exception
                print("{0} v{1}: Ultimately failed to decrypt after {2:.1f} seconds. Read the FAQs at noDRM's repository: https://github.com/noDRM/DeDRM_tools/blob/master/FAQs.md".format(PLUGIN_NAME, PLUGIN_VERSION,time.time()-self.starttime))
                raise DeDRMError("{0} v{1}: Ultimately failed to decrypt after {2:.1f} seconds. Read the FAQs at noDRM's repository: https://github.com/noDRM/DeDRM_tools/blob/master/FAQs.md".format(PLUGIN_NAME, PLUGIN_VERSION,time.time()-self.starttime))

        of = self.temporary_file(book.getBookExtension())
        book.getFile(of.name)
        of.close()
        book.cleanup()
        return of.name


    def eReaderDecrypt(self,path_to_ebook):

        import prefs
        import erdr2pml

        dedrmprefs = prefs.DeDRM_Prefs()
        # Attempt to decrypt epub with each encryption key (generated or provided).
        for keyname, userkey in dedrmprefs['ereaderkeys'].items():
            print("{0} v{1}: Trying Encryption key {2:s}".format(PLUGIN_NAME, PLUGIN_VERSION, keyname))
            of = self.temporary_file(".pmlz")

            # Give the userkey, ebook and TemporaryPersistent file to the decryption function.
            result = erdr2pml.decryptBook(path_to_ebook, of.name, True, codecs.decode(userkey,'hex'))

            of.close()

            # Decryption was successful return the modified PersistentTemporary
            # file to Calibre's import process.
            if  result == 0:
                print("{0} v{1}: Successfully decrypted with key {2:s} after {3:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,keyname,time.time()-self.starttime))
                return of.name

            print("{0} v{1}: Failed to decrypt with key {2:s} after {3:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,keyname,time.time()-self.starttime))

        print("{0} v{1}: Ultimately failed to decrypt after {2:.1f} seconds. Read the FAQs at noDRM's repository: https://github.com/noDRM/DeDRM_tools/blob/master/FAQs.md".format(PLUGIN_NAME, PLUGIN_VERSION,time.time()-self.starttime))
        raise DeDRMError("{0} v{1}: Ultimately failed to decrypt after {2:.1f} seconds. Read the FAQs at noDRM's repository: https://github.com/noDRM/DeDRM_tools/blob/master/FAQs.md".format(PLUGIN_NAME, PLUGIN_VERSION, time.time()-self.starttime))


    def run(self, path_to_ebook):

        # make sure any unicode output gets converted safely with 'replace'
        sys.stdout=utilities.SafeUnbuffered(sys.stdout)
        sys.stderr=utilities.SafeUnbuffered(sys.stderr)

        print("{0} v{1}: Trying to decrypt {2}".format(PLUGIN_NAME, PLUGIN_VERSION, os.path.basename(path_to_ebook)))
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
            # Adobe PDF (hopefully) or LCP PDF
            decrypted_ebook = self.PDFDecrypt(path_to_ebook)
            pass
        elif booktype == 'epub':
            # Adobe Adept, PassHash (B&N) or LCP ePub
            decrypted_ebook = self.ePubDecrypt(path_to_ebook)
        else:
            print("Unknown booktype {0}. Passing back to calibre unchanged".format(booktype))
            return path_to_ebook
        print("{0} v{1}: Finished after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,time.time()-self.starttime))
        return decrypted_ebook

    def is_customizable(self):
        # return true to allow customization via the Plugin->Preferences.
        return True

    def config_widget(self):
        import config
        return config.ConfigWidget(self.plugin_path, self.alfdir)

    def save_settings(self, config_widget):
        config_widget.save_settings()
