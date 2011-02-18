#!/usr/bin/env python

from __future__ import with_statement

# engine to remove drm from Kindle for Mac and Kindle for PC books
# for personal use for archiving and converting your ebooks

# PLEASE DO NOT PIRATE EBOOKS! 

# We want all authors and publishers, and eBook stores to live
# long and prosperous lives but at the same time  we just want to 
# be able to read OUR books on whatever device we want and to keep 
# readable for a long, long time

#  This borrows very heavily from works by CMBDTC, IHeartCabbages, skindle, 
#    unswindle, DarkReverser, ApprenticeAlf, DiapDealer, some_updates 
#    and many many others

# It can run standalone to convert K4M/K4PC/Mobi files, or it can be installed as a
# plugin for Calibre (http://calibre-ebook.com/about) so that importing
# K4 or Mobi with DRM is no londer a multi-step process.
#
# ***NOTE*** If you are using this script as a calibre plugin for a K4M or K4PC ebook
# then calibre must be installed on the same machine and in the same account as K4PC or K4M
# for the plugin version to function properly.
#
# To create a Calibre plugin, rename this file so that the filename
# ends in '_plugin.py', put it into a ZIP file with all its supporting python routines
# and import that ZIP into Calibre using its plugin configuration GUI.


__version__ = '2.6'

class Unbuffered:
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

import sys
import os, csv, getopt
import string
import binascii
import zlib
import re
import zlib, zipfile, tempfile, shutil
from struct import pack, unpack, unpack_from

class DrmException(Exception):
    pass

if 'calibre' in sys.modules:
    inCalibre = True
else:
    inCalibre = False

def zipUpDir(myzip, tempdir,localname):
    currentdir = tempdir
    if localname != "":
        currentdir = os.path.join(currentdir,localname)
    list = os.listdir(currentdir)
    for file in list:
        afilename = file
        localfilePath = os.path.join(localname, afilename)
        realfilePath = os.path.join(currentdir,file)
        if os.path.isfile(realfilePath):
            myzip.write(realfilePath, localfilePath)
        elif os.path.isdir(realfilePath):
            zipUpDir(myzip, tempdir, localfilePath)

# cleanup bytestring filenames
# borrowed from calibre from calibre/src/calibre/__init__.py
# added in removal of non-printing chars
# and removal of . at start
# convert spaces to underscores
def cleanup_name(name):
    _filename_sanitize = re.compile(r'[\xae\0\\|\?\*<":>\+/]')
    substitute='_'
    one = ''.join(char for char in name if char in string.printable)
    one = _filename_sanitize.sub(substitute, one)
    one = re.sub(r'\s', ' ', one).strip()
    one = re.sub(r'^\.+$', '_', one)
    one = one.replace('..', substitute)
    # Windows doesn't like path components that end with a period
    if one.endswith('.'):
        one = one[:-1]+substitute
    # Mac and Unix don't like file names that begin with a full stop
    if len(one) > 0 and one[0] == '.':
        one = substitute+one[1:]
    one = one.replace(' ','_')
    return one

def decryptBook(infile, outdir, k4, kInfoFiles, serials, pids):
    import mobidedrm
    import topazextract
    import kgenpids

    # handle the obvious cases at the beginning
    if not os.path.isfile(infile):
        print "Error: Input file does not exist"
        return 1

    mobi = True
    magic3 = file(infile,'rb').read(3)
    if magic3 == 'TPZ':
        mobi = False

    bookname = os.path.splitext(os.path.basename(infile))[0]

    if mobi:
        mb = mobidedrm.MobiBook(infile)
    else:
        tempdir = tempfile.mkdtemp()
        mb = topazextract.TopazBook(infile, tempdir)

    title = mb.getBookTitle()
    print "Processing Book: ", title
    filenametitle = cleanup_name(title)
    outfilename = bookname
    if len(bookname)>4 and len(filenametitle)>4 and bookname[:4] != filenametitle[:4]:
        outfilename = outfilename + "_" + filenametitle

    # build pid list
    md1, md2 = mb.getPIDMetaInfo()
    pidlst = kgenpids.getPidList(md1, md2, k4, pids, serials, kInfoFiles) 

    try:
        if mobi:
            unlocked_file = mb.processBook(pidlst)
        else:
            mb.processBook(pidlst)

    except mobidedrm.DrmException, e:
        print "Error: " + str(e) + "\nDRM Removal Failed.\n"
        return 1
    except Exception, e:
        if not mobi:
            print "Error: " + str(e) + "\nDRM Removal Failed.\n"
            print "   Creating DeBug Full Zip Archive of Book"
            zipname = os.path.join(outdir, bookname + '_debug' + '.zip')
            myzip = zipfile.ZipFile(zipname,'w',zipfile.ZIP_DEFLATED, False)
            zipUpDir(myzip, tempdir, '')
            myzip.close()
            shutil.rmtree(tempdir, True)
            return 1
        pass

    if mobi:
        outfile = os.path.join(outdir,outfilename + '_nodrm' + '.mobi')
        file(outfile, 'wb').write(unlocked_file)
        return 0            

    # topaz:  build up zip archives of results
    print "   Creating HTML ZIP Archive"
    zipname = os.path.join(outdir, outfilename + '_nodrm' + '.zip')
    myzip1 = zipfile.ZipFile(zipname,'w',zipfile.ZIP_DEFLATED, False)
    myzip1.write(os.path.join(tempdir,'book.html'),'book.html')
    myzip1.write(os.path.join(tempdir,'book.opf'),'book.opf')
    if os.path.isfile(os.path.join(tempdir,'cover.jpg')):
        myzip1.write(os.path.join(tempdir,'cover.jpg'),'cover.jpg')
    myzip1.write(os.path.join(tempdir,'style.css'),'style.css')
    zipUpDir(myzip1, tempdir, 'img')
    myzip1.close()

    print "   Creating SVG ZIP Archive"
    zipname = os.path.join(outdir, outfilename + '_SVG' + '.zip')
    myzip2 = zipfile.ZipFile(zipname,'w',zipfile.ZIP_DEFLATED, False)
    myzip2.write(os.path.join(tempdir,'index_svg.xhtml'),'index_svg.xhtml')
    zipUpDir(myzip2, tempdir, 'svg')
    zipUpDir(myzip2, tempdir, 'img')
    myzip2.close()

    print "   Creating XML ZIP Archive"
    zipname = os.path.join(outdir, outfilename + '_XML' + '.zip')
    myzip3 = zipfile.ZipFile(zipname,'w',zipfile.ZIP_DEFLATED, False)
    targetdir = os.path.join(tempdir,'xml')
    zipUpDir(myzip3, targetdir, '')
    zipUpDir(myzip3, tempdir, 'img')
    myzip3.close()

    shutil.rmtree(tempdir, True)
    return 0


def usage(progname):
    print "Removes DRM protection from K4PC/M, Kindle, Mobi and Topaz ebooks"
    print "Usage:"
    print "    %s [-k <kindle.info>] [-p <pidnums>] [-s <kindleSerialNumbers>] <infile> <outdir>  " % progname

#
# Main
#   
def main(argv=sys.argv):
    progname = os.path.basename(argv[0])

    k4 = False
    kInfoFiles = []
    serials = []
    pids = []
    
    print ('K4MobiDeDrm v%(__version__)s '
	   'provided by the work of many including DiapDealer, SomeUpdates, IHeartCabbages, CMBDTC, Skindle, DarkReverser, ApprenticeAlf, etc .' % globals())

    print ' '
    try:
        opts, args = getopt.getopt(sys.argv[1:], "k:p:s:")
    except getopt.GetoptError, err:
        print str(err)
        usage(progname)
        sys.exit(2)
    if len(args)<2:
        usage(progname)
        sys.exit(2)
        
    for o, a in opts:
        if o == "-k":
            if a == None :
                raise DrmException("Invalid parameter for -k")
            kInfoFiles.append(a)
        if o == "-p":
            if a == None :
                raise DrmException("Invalid parameter for -p")
            pids = a.split(',')
        if o == "-s":
            if a == None :
                raise DrmException("Invalid parameter for -s")
            serials = a.split(',')

    # try with built in Kindle Info files
    k4 = True
    infile = args[0]
    outdir = args[1]

    return decryptBook(infile, outdir, k4, kInfoFiles, serials, pids)


if __name__ == '__main__':
    sys.stdout=Unbuffered(sys.stdout)
    sys.exit(main())

if not __name__ == "__main__" and inCalibre:
    from calibre.customize import FileTypePlugin

    class K4DeDRM(FileTypePlugin):
        name                = 'K4PC, K4Mac, Kindle Mobi and Topaz DeDRM' # Name of the plugin
        description         = 'Removes DRM from K4PC and Mac, Kindle Mobi and Topaz files. \
                                Provided by the work of many including DiapDealer, SomeUpdates, IHeartCabbages, CMBDTC, Skindle, DarkReverser, ApprenticeAlf, etc.'
        supported_platforms = ['osx', 'windows', 'linux'] # Platforms this plugin will run on
        author              = 'DiapDealer, SomeUpdates' # The author of this plugin
        version             = (0, 2, 6)   # The version number of this plugin
        file_types          = set(['prc','mobi','azw','azw1','tpz']) # The file types that this plugin will be applied to
        on_import           = True # Run this plugin during the import
        priority            = 210  # run this plugin before mobidedrm, k4pcdedrm, k4dedrm

        def run(self, path_to_ebook):
            from calibre.gui2 import is_ok_to_use_qt
            from PyQt4.Qt import QMessageBox
            from calibre.ptempfile import PersistentTemporaryDirectory

            import kgenpids
            import zlib
            import zipfile
            import topazextract
            import mobidedrm

            k4 = True
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
                print 'K4MobiDeDRM: Calibre configuration directory = %s' % confpath
                files = os.listdir(confpath)
                filefilter = re.compile("\.info$", re.IGNORECASE)
                files = filter(filefilter.search, files)
    
                if files:
                    for filename in files:
                        fpath = os.path.join(confpath, filename)
                        kInfoFiles.append(fpath)
                        print 'K4MobiDeDRM: Kindle info file %s found in config folder.' % filename
            except IOError:
                print 'K4MobiDeDRM: Error reading kindle info files from config directory.'
                pass


            mobi = True
            magic3 = file(path_to_ebook,'rb').read(3)
            if magic3 == 'TPZ':
                mobi = False

            bookname = os.path.splitext(os.path.basename(path_to_ebook))[0]

            if mobi:
                mb = mobidedrm.MobiBook(path_to_ebook)
            else:
                tempdir = PersistentTemporaryDirectory()
                mb = topazextract.TopazBook(path_to_ebook, tempdir)

            title = mb.getBookTitle()
            md1, md2 = mb.getPIDMetaInfo()
            pidlst = kgenpids.getPidList(md1, md2, k4, pids, serials, kInfoFiles) 

            try:
                if mobi:
                    unlocked_file = mb.processBook(pidlst)
                else:
                    mb.processBook(pidlst)

            except mobidedrm.DrmException:
                #if you reached here then no luck raise and exception
                if is_ok_to_use_qt():
                    d = QMessageBox(QMessageBox.Warning, "K4MobiDeDRM Plugin", "Error decoding: %s\n" % path_to_ebook)
                    d.show()
                    d.raise_()
                    d.exec_()
                raise Exception("K4MobiDeDRM plugin could not decode the file")
                return ""
            except topazextract.TpzDRMError:
                #if you reached here then no luck raise and exception
                if is_ok_to_use_qt():
                    d = QMessageBox(QMessageBox.Warning, "K4MobiDeDRM Plugin", "Error decoding: %s\n" % path_to_ebook)
                    d.show()
                    d.raise_()
                    d.exec_()
                raise Exception("K4MobiDeDRM plugin could not decode the file")
                return ""

            print "Success!"
            if mobi:
                of = self.temporary_file(bookname+'.mobi')
                of.write(unlocked_file)
                of.close()
                return of.name

            # topaz:  build up zip archives of results
            print "   Creating HTML ZIP Archive"
            of = self.temporary_file(bookname + '.zip')
            myzip = zipfile.ZipFile(of.name,'w',zipfile.ZIP_DEFLATED, False)
            myzip.write(os.path.join(tempdir,'book.html'),'book.html')
            myzip.write(os.path.join(tempdir,'book.opf'),'book.opf')
            if os.path.isfile(os.path.join(tempdir,'cover.jpg')):
                myzip.write(os.path.join(tempdir,'cover.jpg'),'cover.jpg')
            myzip.write(os.path.join(tempdir,'style.css'),'style.css')
            zipUpDir(myzip, tempdir, 'img')
            myzip.close()
            return of.name

        def customization_help(self, gui=False):
            return 'Enter 10 character PIDs and/or Kindle serial numbers, separated by commas.'
