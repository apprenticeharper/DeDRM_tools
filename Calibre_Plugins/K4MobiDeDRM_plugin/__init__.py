#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai

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
    name                = 'Kindle and Mobipocket DeDRM' # Name of the plugin
    description         = 'Removes DRM from eInk Kindle, Kindle 4 Mac and Kindle 4 PC ebooks, and from Mobipocket ebooks. Provided by the work of many including DiapDealer, SomeUpdates, IHeartCabbages, CMBDTC, Skindle, DarkReverser, mdlnx, ApprenticeAlf, etc.'
    supported_platforms = ['osx', 'windows', 'linux'] # Platforms this plugin will run on
    author              = 'DiapDealer, SomeUpdates, mdlnx, Apprentice Alf' # The author of this plugin
    version             = (0, 4, 6)   # The version number of this plugin
    file_types          = set(['prc','mobi','azw','azw1','azw3','azw4','tpz']) # The file types that this plugin will be applied to
    on_import           = True # Run this plugin during the import
    priority            = 520  # run this plugin before earlier versions
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
            names = ['libalfcrypto32.so','libalfcrypto64.so','alfcrypto.py','alfcrypto.dll','alfcrypto64.dll','getk4pcpids.py','mobidedrm.py','kgenpids.py','k4pcutils.py','topazextract.py','outputfix.py']
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
        from calibre_plugins.k4mobidedrm import kgenpids, topazextract, mobidedrm, outputfix

        if sys.stdout.encoding == None:
            sys.stdout = outputfix.getwriter('utf-8')(sys.stdout)
        else:
            sys.stdout = outputfix.getwriter(sys.stdout.encoding)(sys.stdout)
        if sys.stderr.encoding == None:
            sys.stderr = outputfix.getwriter('utf-8')(sys.stderr)
        else:
            sys.stderr = outputfix.getwriter(sys.stderr.encoding)(sys.stderr)

        plug_ver = '.'.join(str(self.version).strip('()').replace(' ', '').split(','))
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
                    print "'%s' is not a valid Mobipocket PID." % pid
                        
        # For linux, get PIDs by calling the right routines under WINE
        if sys.platform.startswith('linux'):
            k4 = False
            pids.extend(self.WINEgetPIDs(path_to_ebook))
            
        # Get supplied list of Kindle serial numbers to try from plugin customization.
        serialstringlistt = self.serials_string.split(',')
        for serial in serialstringlistt:
            serial = str(serial).strip()
            if len(serial) == 16 and serial[0] == 'B':
                serials.append(serial)
            else:
                if len(serial) > 0:
                    print "'%s' is not a valid Kindle serial number." % serial
                    
        # Load any kindle info files (*.info) included Calibre's config directory.
        try:
            print 'K4MobiDeDRM v%s: Calibre configuration directory = %s' % (plug_ver, config_dir)
            files = os.listdir(config_dir)
            filefilter = re.compile("\.info$|\.kinf$", re.IGNORECASE)
            files = filter(filefilter.search, files)
            if files:
                for filename in files:
                    fpath = os.path.join(config_dir, filename)
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
            elif mb.getMobiVersion() >= 8:
                print 'K4MobiDeDRM v%s: Stand-alone KF8 format detected.' % plug_ver
                of = self.temporary_file(bookname+'.azw3')
            else:
                of = self.temporary_file(bookname+'.mobi')
            mb.getMobiFile(of.name)
        else:
            of = self.temporary_file(bookname+'.htmlz')
            mb.getHTMLZip(of.name)
            mb.cleanup()
        return of.name

    def WINEgetPIDs(self, infile):

        import subprocess
        from subprocess import Popen, PIPE, STDOUT

        import subasyncio
        from subasyncio import Process

        print "   Getting PIDs from WINE"

        outfile = os.path.join(self.alfdir + 'winepids.txt')
        # Remove any previous winepids.txt file.
        if os.path.exists(outfile):
            os.remove(outfile)

        cmdline = 'wine python.exe ' \
                  + '"'+self.alfdir + '/getk4pcpids.py"' \
                  + ' "' + infile + '"' \
                  + ' "' + outfile + '"'

        env = os.environ
        
        print "My wine_prefix from tweaks is ", self.wine_prefix

        if ("WINEPREFIX" in env):
            print "Using WINEPREFIX from the environment: ", env["WINEPREFIX"]
        elif (self.wine_prefix is not None):
            env['WINEPREFIX'] = self.wine_prefix
            print "Using WINEPREFIX from tweaks: ", self.wine_prefix
        else:
            print "No wine prefix used"

        print cmdline

        try:
            cmdline = cmdline.encode(sys.getfilesystemencoding())
            p2 = Process(cmdline, shell=True, bufsize=1, stdin=None, stdout=sys.stdout, stderr=STDOUT, close_fds=False)
            result = p2.wait("wait")
        except Exception, e:
            print "WINE subprocess error ", str(e)
            return []
        print "WINE subprocess returned ", result
        
        WINEpids = []
        if os.path.exists(outfile):
            try:
                customvalues = file(outfile, 'r').readline().split(',')
                for customvalue in customvalues:
                    customvalue = str(customvalue)
                    customvalue = customvalue.strip()
                    if len(customvalue) == 10 or len(customvalue) == 8:
                        WINEpids.append(customvalue)
                    else:
                        print "'%s' is not a valid PID." % customvalue
            except Exception, e:
                print "Error parsing winepids.txt: ", str(e)
                return []
        else:
            print "No PIDs generated by Wine Python subprocess."
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