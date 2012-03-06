#!/usr/bin/env python

from __future__ import with_statement

from calibre.customize import FileTypePlugin
from calibre.gui2 import is_ok_to_use_qt
from calibre.utils.config import config_dir
from calibre.constants import iswindows, isosx
# from calibre.ptempfile import PersistentTemporaryDirectory


import sys
import os
import re
from zipfile import ZipFile

class K4DeDRM(FileTypePlugin):
    name                = 'K4PC, K4Mac, Kindle Mobi and Topaz DeDRM' # Name of the plugin
    description         = 'Removes DRM from Mobipocket, Kindle/Mobi, Kindle/Topaz and Kindle/Print Replica files. Provided by the work of many including DiapDealer, SomeUpdates, IHeartCabbages, CMBDTC, Skindle, DarkReverser, ApprenticeAlf, etc.'
    supported_platforms = ['osx', 'windows', 'linux'] # Platforms this plugin will run on
    author              = 'DiapDealer, SomeUpdates' # The author of this plugin
    version             = (0, 4, 1)   # The version number of this plugin
    file_types          = set(['prc','mobi','azw','azw1','azw4','tpz']) # The file types that this plugin will be applied to
    on_import           = True # Run this plugin during the import
    priority            = 210  # run this plugin before mobidedrm, k4pcdedrm, k4dedrm
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
            names = ['alfcrypto.dll','alfcrypto64.dll']
        elif isosx:
            names = ['libalfcrypto.dylib']
        else:
            names = ['libalfcrypto32.so','libalfcrypto64.so']
        lib_dict = self.load_resources(names)
        self.alfdir = os.path.join(config_dir, 'alfcrypto')
        if not os.path.exists(self.alfdir):
            os.mkdir(self.alfdir)
        for entry, data in lib_dict.items():
            file_path = os.path.join(self.alfdir, entry)
            with open(file_path,'wb') as f:
                f.write(data)

    def run(self, path_to_ebook):
        # add the alfcrypto directory to sys.path so alfcrypto.py 
        # will be able to locate the custom lib(s) for CDLL import.
        sys.path.insert(0, self.alfdir)
        # Had to move these imports here so the custom libs can be
        # extracted to the appropriate places beforehand these routines
        # look for them.
        from calibre_plugins.k4mobidedrm import kgenpids
        from calibre_plugins.k4mobidedrm import topazextract
        from calibre_plugins.k4mobidedrm import mobidedrm

        plug_ver = '.'.join(str(self.version).strip('()').replace(' ', '').split(','))
        k4 = True
        if sys.platform.startswith('linux'):
            k4 = False
        pids = []
        serials = []
        kInfoFiles = []
        # Get supplied list of PIDs to try from plugin customization.
        customvalues = self.site_customization.split(',')
        for customvalue in customvalues:
            customvalue = str(customvalue)
            customvalue = customvalue.strip()
            if len(customvalue) == 10 or len(customvalue) == 8:
                pids.append(customvalue)
            else :
                if len(customvalue) == 16 and customvalue[0] == 'B':
                    serials.append(customvalue)
                else:
                    print "%s is not a valid Kindle serial number or PID." % str(customvalue)

        # Load any kindle info files (*.info) included Calibre's config directory.
        try:
            # Find Calibre's configuration directory.
            confpath = os.path.split(os.path.split(self.plugin_path)[0])[0]
            print 'K4MobiDeDRM v%s: Calibre configuration directory = %s' % (plug_ver, confpath)
            files = os.listdir(confpath)
            filefilter = re.compile("\.info$|\.kinf$", re.IGNORECASE)
            files = filter(filefilter.search, files)
            if files:
                for filename in files:
                    fpath = os.path.join(confpath, filename)
                    kInfoFiles.append(fpath)
                print 'K4MobiDeDRM v%s: Kindle info/kinf file %s found in config folder.' % (plug_ver, filename)
        except IOError:
            print 'K4MobiDeDRM v%s: Error reading kindle info/kinf files from config directory.' % plug_ver
            pass

        mobi = True
        magic3 = file(path_to_ebook,'rb').read(3)
        if magic3 == 'TPZ':
            mobi = False

        bookname = os.path.splitext(os.path.basename(path_to_ebook))[0]

        if mobi:
            mb = mobidedrm.MobiBook(path_to_ebook)
        else:
            mb = topazextract.TopazBook(path_to_ebook)

        title = mb.getBookTitle()
        md1, md2 = mb.getPIDMetaInfo()
        pidlst = kgenpids.getPidList(md1, md2, k4, pids, serials, kInfoFiles)

        try:
            mb.processBook(pidlst)

        except mobidedrm.DrmException, e:
            #if you reached here then no luck raise and exception
            if is_ok_to_use_qt():
                from PyQt4.Qt import QMessageBox
                d = QMessageBox(QMessageBox.Warning, "K4MobiDeDRM v%s Plugin" % plug_ver, "Error: " + str(e) + "... %s\n" %  path_to_ebook)
                d.show()
                d.raise_()
                d.exec_()
            raise Exception("K4MobiDeDRM plugin v%s Error: %s" % (plug_ver, str(e)))
        except topazextract.TpzDRMError, e:
            #if you reached here then no luck raise and exception
            if is_ok_to_use_qt():
                from PyQt4.Qt import QMessageBox
                d = QMessageBox(QMessageBox.Warning, "K4MobiDeDRM v%s Plugin" % plug_ver, "Error: " + str(e) + "... %s\n" % path_to_ebook)
                d.show()
                d.raise_()
                d.exec_()
            raise Exception("K4MobiDeDRM plugin v%s Error: %s" % (plug_ver, str(e)))

        print "Success!"
        if mobi:
            if mb.getPrintReplica():
                of = self.temporary_file(bookname+'.azw4')
                print 'K4MobiDeDRM v%s: Print Replica format detected.' % plug_ver
            else:
                of = self.temporary_file(bookname+'.mobi')
            mb.getMobiFile(of.name)
        else:
            of = self.temporary_file(bookname+'.htmlz')
            mb.getHTMLZip(of.name)
            mb.cleanup()
        return of.name

    def customization_help(self, gui=False):
        return 'Enter 10 character PIDs and/or Kindle serial numbers, use a comma (no spaces) to separate each PID or SerialNumber from the next.'

    def load_resources(self, names):
        ans = {}
        with ZipFile(self.plugin_path, 'r') as zf:
            for candidate in zf.namelist():
                if candidate in names:
                    ans[candidate] = zf.read(candidate)
        return ans