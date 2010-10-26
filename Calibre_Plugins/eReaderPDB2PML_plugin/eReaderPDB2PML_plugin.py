#!/usr/bin/env python

# eReaderPDB2PML_v01_plugin.py
# Released under the terms of the GNU General Public Licence, version 3 or
# later.  <http://www.gnu.org/licenses/>
#
# All credit given to The Dark Reverser for the original standalone script.
# I had the much easier job of converting it to Calibre a plugin.
#
# This plugin is meant to convert secure Ereader files (PDB) to unsecured PMLZ files.
# Calibre can then convert it to whatever format you desire.
# It is meant to function without having to install any dependencies...
# other than having Calibre installed, of course. I've included the psyco libraries
# (compiled for each platform) for speed. If your system can use them, great!
# Otherwise, they won't be used and things will just work slower.
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
#   0.1 - Initial release

import sys, os

from calibre.customize import FileTypePlugin

class eRdrDeDRM(FileTypePlugin):
    name                = 'eReader PDB 2 PML' # Name of the plugin
    description         = 'Removes DRM from secure pdb files. \
                            Credit given to The Dark Reverser for the original standalone script.'
    supported_platforms = ['linux', 'osx', 'windows'] # Platforms this plugin will run on
    author              = 'DiapDealer' # The author of this plugin
    version             = (0, 0, 1)   # The version number of this plugin
    file_types          = set(['pdb']) # The file types that this plugin will be applied to
    on_import           = True # Run this plugin during the import

    def run(self, path_to_ebook):
        from calibre.ptempfile import PersistentTemporaryDirectory
        from calibre.constants import iswindows, isosx
        pdir = 'windows' if iswindows else 'osx' if isosx else 'linux'
        ppath = os.path.join(self.sys_insertion_path, pdir)
        sys.path.insert(0, ppath)
        #sys.path.append(ppath)
        
        global bookname, erdr2pml
        import erdr2pml
        
        if 'psyco' in sys.modules:
            print 'Using psyco acceleration for %s.' % pdir
        else:
            print 'NOT using psyco acceleration for %s. Conversion may be slow.' % pdir
        
        infile = path_to_ebook
        bookname = os.path.splitext(os.path.basename(infile))[0]
        outdir = PersistentTemporaryDirectory()
        pmlzfile = self.temporary_file(bookname + '.pmlz')
        
        if self.site_customization:
            keydata = self.site_customization
            ar = keydata.split(':')
            for i in ar:
                try:
                    name, cc = i.split(',')
                except ValueError:
                    sys.path.remove(ppath)
                    print '   Error parsing user supplied data.'
                    return path_to_ebook

                try:
                    print "Processing..."
                    import time
                    start_time = time.time()
                    pmlfilepath = self.convertEreaderToPml(infile, name, cc, outdir)
                    
                    if pmlfilepath and pmlfilepath != 1:
                        import zipfile
                        import shutil
                        print "   Creating PMLZ file"
                        myZipFile = zipfile.ZipFile(pmlzfile.name,'w',zipfile.ZIP_STORED, False)
                        list = os.listdir(outdir)
                        for file in list:
                            localname = file
                            filePath = os.path.join(outdir,file)
                            if os.path.isfile(filePath):
                                myZipFile.write(filePath, localname)
                            elif os.path.isdir(filePath):
                                imageList = os.listdir(filePath)
                                localimgdir = os.path.basename(filePath)
                                for image in imageList:
                                    localname = os.path.join(localimgdir,image)
                                    imagePath = os.path.join(filePath,image)
                                    if os.path.isfile(imagePath):
                                        myZipFile.write(imagePath, localname)
                        myZipFile.close()
                        end_time = time.time()
                        search_time = end_time - start_time
                        print 'elapsed time: %.2f seconds' % (search_time, ) 
                        print "done"
                        return pmlzfile.name
                    else:
                        raise ValueError('Error Creating PML file.')
                except ValueError, e:
                        print "Error: %s" % e
                        pass
            raise Exception('Couldn\'t decrypt pdb file.')
        else:
            raise Exception('No name and CC# provided.')
        
    def convertEreaderToPml(self, infile, name, cc, outdir):

        print "   Decoding File"
        sect = erdr2pml.Sectionizer(infile, 'PNRdPPrs')
        er = erdr2pml.EreaderProcessor(sect.loadSection, name, cc)

        if er.getNumImages() > 0:
            print "   Extracting images"
            #imagedir = bookname + '_img/'
            imagedir = 'images/'
            imagedirpath = os.path.join(outdir,imagedir)
            if not os.path.exists(imagedirpath):
                os.makedirs(imagedirpath)
            for i in xrange(er.getNumImages()):
                name, contents = er.getImage(i)
                file(os.path.join(imagedirpath, name), 'wb').write(contents)

        print "   Extracting pml"
        pml_string = er.getText()
        pmlfilename = bookname + ".pml"
        try:
            file(os.path.join(outdir, pmlfilename),'wb').write(erdr2pml.cleanPML(pml_string))
            return os.path.join(outdir, pmlfilename)
        except:
            return 1
 
    def customization_help(self, gui=False):
        return 'Enter Account Name & Last 8 digits of Credit Card number (separate with a comma)'
