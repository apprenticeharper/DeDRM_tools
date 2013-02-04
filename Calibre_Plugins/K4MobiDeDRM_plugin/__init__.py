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
# All credit given to The Dark Reverser for the original mobidedrm script.
# Thanks to all those who've worked on the scripts since 2008 to improve
# the support for formats and sources.
#
# Revision history:
#   0.4.8  - Major code change to use unaltered k4mobidedrm.py 4.8 and later
#   0.4.9  - typo fix
#   0.4.10 - Another Topaz Fix (class added to page and group and region)
#   0.4.11 - Fixed Linux support of K4PC
#   0.4.12 - More Linux Wine fixes
#   0.4.13 - Ancient Mobipocket files fix
#   0.4.14 - Error on invalid character in book names fix
#   0.4.15 - Another Topaz fix
#   0.4.16 - Yet another Topaz fix
#   0.4.17 - Manage to include the actual fix.
#   0.4.18 - More Topaz fixes
#   0.4.19 - MobiDeDRM PalmDoc fix

"""
Decrypt Amazon Kindle and Mobipocket encrypted ebooks.
"""

PLUGIN_NAME = u"Kindle and Mobipocket DeDRM"
PLUGIN_VERSION_TUPLE = (0, 4, 19)
PLUGIN_VERSION = '.'.join([str(x) for x in PLUGIN_VERSION_TUPLE])

import sys, os, re
import time
from zipfile import ZipFile

from calibre.customize import FileTypePlugin
from calibre.constants import iswindows, isosx
from calibre.gui2 import is_ok_to_use_qt
from calibre.utils.config import config_dir

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


class K4DeDRM(FileTypePlugin):
    name                = PLUGIN_NAME
    description         = u"Removes DRM from eInk Kindle, Kindle 4 Mac and Kindle 4 PC ebooks, and from Mobipocket ebooks. Provided by the work of many including The Dark Reverser, DiapDealer, SomeUpdates, i♥cabbages, CMBDTC, Skindle, mdlnx, ApprenticeAlf, and probably others."
    supported_platforms = ['osx', 'windows', 'linux'] # Platforms this plugin will run on
    author              = u"DiapDealer, SomeUpdates, mdlnx, Apprentice Alf and The Dark Reverser"
    version             = PLUGIN_VERSION_TUPLE
    file_types          = set(['prc','mobi','azw','azw1','azw3','azw4','tpz']) # The file types that this plugin will be applied to
    on_import           = True # Run this plugin during the import
    priority            = 521  # run this plugin before earlier versions
    minimum_calibre_version = (0, 7, 55)

    def initialize(self):
        """
        Dynamic modules can't be imported/loaded from a zipfile... so this routine
        runs whenever the plugin gets initialized. This will extract the appropriate
        library for the target OS and copy it to the 'alfcrypto' subdirectory of
        calibre's configuration directory. That 'alfcrypto' directory is then
        inserted into the syspath (as the very first entry) in the run function
        so the CDLL stuff will work in the alfcrypto.py script.
        """
        if iswindows:
            names = [u"alfcrypto.dll",u"alfcrypto64.dll"]
        elif isosx:
            names = [u"libalfcrypto.dylib"]
        else:
            names = [u"libalfcrypto32.so",u"libalfcrypto64.so",u"alfcrypto.py",u"alfcrypto.dll",u"alfcrypto64.dll",u"getk4pcpids.py",u"k4mobidedrm.py",u"mobidedrm.py",u"kgenpids.py",u"k4pcutils.py",u"topazextract.py"]
        lib_dict = self.load_resources(names)
        self.alfdir = os.path.join(config_dir,u"alfcrypto")
        if not os.path.exists(self.alfdir):
            os.mkdir(self.alfdir)
        for entry, data in lib_dict.items():
            file_path = os.path.join(self.alfdir, entry)
            open(file_path,'wb').write(data)

    def run(self, path_to_ebook):
        # make sure any unicode output gets converted safely with 'replace'
        sys.stdout=SafeUnbuffered(sys.stdout)
        sys.stderr=SafeUnbuffered(sys.stderr)

        starttime = time.time()
        print u"{0} v{1}: Trying to decrypt {2}.".format(PLUGIN_NAME, PLUGIN_VERSION, os.path.basename(path_to_ebook))

        # add the alfcrypto directory to sys.path so alfcrypto.py
        # will be able to locate the custom lib(s) for CDLL import.
        sys.path.insert(0, self.alfdir)
        # Had to move these imports here so the custom libs can be
        # extracted to the appropriate places beforehand these routines
        # look for them.
        from calibre_plugins.k4mobidedrm import k4mobidedrm

        k4 = True
        pids = []
        serials = []
        kInfoFiles = []

        self.config()

        # Get supplied list of PIDs to try from plugin customization.
        pidstringlistt = self.pids_string.split(',')
        for pid in pidstringlistt:
            pid = str(pid).strip()
            if len(pid) == 10 or len(pid) == 8:
                pids.append(pid)
            else:
                if len(pid) > 0:
                    print u"{0} v{1}: \'{2}\' is not a valid Mobipocket PID.".format(PLUGIN_NAME, PLUGIN_VERSION, pid)

        # For linux, get PIDs by calling the right routines under WINE
        if sys.platform.startswith('linux'):
            k4 = False
            pids.extend(self.WINEgetPIDs(path_to_ebook))

        # Get supplied list of Kindle serial numbers to try from plugin customization.
        serialstringlistt = self.serials_string.split(',')
        for serial in serialstringlistt:
            serial = str(serial).replace(" ","")
            if len(serial) == 16 and serial[0] in ['B','9']:
                serials.append(serial)
            else:
                if len(serial) > 0:
                    print u"{0} v{1}: \'{2}\' is not a valid eInk Kindle serial number.".format(PLUGIN_NAME, PLUGIN_VERSION, serial)

        # Load any kindle info files (*.info) included Calibre's config directory.
        try:
            print u"{0} v{1}: Calibre configuration directory is {2}".format(PLUGIN_NAME, PLUGIN_VERSION, config_dir)
            files = os.listdir(config_dir)
            filefilter = re.compile("\.info$|\.kinf$", re.IGNORECASE)
            files = filter(filefilter.search, files)
            if files:
                for filename in files:
                    fpath = os.path.join(config_dir, filename)
                    kInfoFiles.append(fpath)
                print u"{0} v{1}: Kindle info/kinf file {2} found in config folder.".format(PLUGIN_NAME, PLUGIN_VERSION, filename)
        except IOError, e:
            print u"{0} v{1}: Error \'{2}\' reading kindle info/kinf files from config directory.".format(PLUGIN_NAME, PLUGIN_VERSION, e.args[0])
            pass

        try:
            book = k4mobidedrm.GetDecryptedBook(path_to_ebook,kInfoFiles,serials,pids,starttime)
        except Exception, e:
            #if you reached here then no luck raise and exception
            if is_ok_to_use_qt():
                from PyQt4.Qt import QMessageBox
                d = QMessageBox(QMessageBox.Warning, u"{0} v{1}".format(PLUGIN_NAME, PLUGIN_VERSION), u"Error after {1:.1f} seconds: {0}".format(e.args[0],time.time()-starttime))
                d.show()
                d.raise_()
                d.exec_()
            raise Exception(u"{0} v{1}: Error after {3:.1f} seconds: {2}".format(PLUGIN_NAME, PLUGIN_VERSION, e.args[0],time.time()-starttime))


        print u"{0} v{1}: Successfully decrypted book after {2:.1f} seconds".format(PLUGIN_NAME, PLUGIN_VERSION,time.time()-starttime)

        of = self.temporary_file(u"decrypted_ebook.{0}".format(book.getBookExtension()))
        book.getFile(of.name)
        book.cleanup()
        return of.name

    def WINEgetPIDs(self, infile):

        import subprocess
        from subprocess import Popen, PIPE, STDOUT

        import subasyncio
        from subasyncio import Process

        print u"   Getting PIDs from Wine"

        outfile = os.path.join(self.alfdir + u"winepids.txt")
        # Remove any previous winepids.txt file.
        if os.path.exists(outfile):
            os.remove(outfile)

        cmdline = u"wine python.exe \"{0}/getk4pcpids.py\" \"{1}\" \"{2}\"".format(self.alfdir,infile,outfile)
        env = os.environ

        print u"wine_prefix from tweaks is \'{0}\'".format(self.wine_prefix)

        if ("WINEPREFIX" in env):
            print u"Using WINEPREFIX from the environment instead: \'{0}\'".format(env["WINEPREFIX"])
        elif (self.wine_prefix is not None):
            env["WINEPREFIX"] = self.wine_prefix
            print u"Using WINEPREFIX from tweaks \'{0}\'".format(self.wine_prefix)
        else:
            print u"No wine prefix used."

        print u"Trying command: {0}".format(cmdline)

        try:
            cmdline = cmdline.encode(sys.getfilesystemencoding())
            p2 = Process(cmdline, shell=True, bufsize=1, stdin=None, stdout=sys.stdout, stderr=STDOUT, close_fds=False)
            result = p2.wait("wait")
        except Exception, e:
            print u"WINE subprocess error: {0}".format(e.args[0])
            return []
        print u"WINE subprocess returned {0}".format(result)

        WINEpids = []
        if os.path.exists(outfile):
            try:
                customvalues = file(outfile, 'r').readline().split(',')
                for customvalue in customvalues:
                    customvalue = str(customvalue)
                    customvalue = customvalue.strip()
                    if len(customvalue) == 10 or len(customvalue) == 8:
                        WINEpids.append(customvalue)
                        print u"Found PID '{0}'".format(customvalue)
                    else:
                        print u"'{0}' is not a valid PID.".format(customvalue)
            except Exception, e:
                print u"Error parsing winepids.txt: {0}".format(e.args[0])
                return []
        if len(WINEpids) == 0:
            print u"No PIDs generated by Wine Python subprocess."
        return WINEpids

    def is_customizable(self):
        # return true to allow customization via the Plugin->Preferences.
        return True

    def config_widget(self):
        # It is important to put this import statement here rather than at the
        # top of the module as importing the config class will also cause the
        # GUI libraries to be loaded, which we do not want when using calibre
        # from the command line
        from calibre_plugins.k4mobidedrm.config import ConfigWidget
        return config.ConfigWidget()

    def config(self):
        from calibre_plugins.k4mobidedrm.config import prefs

        self.pids_string = prefs['pids']
        self.serials_string = prefs['serials']
        self.wine_prefix = prefs['WINEPREFIX']

    def save_settings(self, config_widget):
        '''
        Save the settings specified by the user with config_widget.
        '''
        config_widget.save_settings()
        self.config()

    def load_resources(self, names):
        ans = {}
        with ZipFile(self.plugin_path, 'r') as zf:
            for candidate in zf.namelist():
                if candidate in names:
                    ans[candidate] = zf.read(candidate)
        return ans
