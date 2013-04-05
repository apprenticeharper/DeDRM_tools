#!/usr/bin/env python
# -*- coding: utf-8 -*-

# erdr2pml.py
# Copyright © 2008 The Dark Reverser
#
# Modified 2008–2012 by some_updates, DiapDealer and Apprentice Alf

# This is a python script. You need a Python interpreter to run it.
# For example, ActiveState Python, which exists for windows.
# Changelog
#
#  Based on ereader2html version 0.08 plus some later small fixes
#
#  0.01 - Initial version
#  0.02 - Support more eReader files. Support bold text and links. Fix PML decoder parsing bug.
#  0.03 - Fix incorrect variable usage at one place.
#  0.03b - enhancement by DeBockle (version 259 support)
# Custom version 0.03 - no change to eReader support, only usability changes
#   - start of pep-8 indentation (spaces not tab), fix trailing blanks
#   - version variable, only one place to change
#   - added main routine, now callable as a library/module,
#     means tools can add optional support for ereader2html
#   - outdir is no longer a mandatory parameter (defaults based on input name if missing)
#   - time taken output to stdout
#   - Psyco support - reduces runtime by a factor of (over) 3!
#     E.g. (~600Kb file) 90 secs down to 24 secs
#       - newstyle classes
#       - changed map call to list comprehension
#         may not work with python 2.3
#         without Psyco this reduces runtime to 90%
#         E.g. 90 secs down to 77 secs
#         Psyco with map calls takes longer, do not run with map in Psyco JIT!
#       - izip calls used instead of zip (if available), further reduction
#         in run time (factor of 4.5).
#         E.g. (~600Kb file) 90 secs down to 20 secs
#   - Python 2.6+ support, avoid DeprecationWarning with sha/sha1
#  0.04 - Footnote support, PML output, correct charset in html, support more PML tags
#   - Feature change, dump out PML file
#   - Added supprt for footnote tags. NOTE footnote ids appear to be bad (not usable)
#       in some pdb files :-( due to the same id being used multiple times
#   - Added correct charset encoding (pml is based on cp1252)
#   - Added logging support.
#  0.05 - Improved type 272 support for sidebars, links, chapters, metainfo, etc
#  0.06 - Merge of 0.04 and 0.05. Improved HTML output
#         Placed images in subfolder, so that it's possible to just
#         drop the book.pml file onto DropBook to make an unencrypted
#         copy of the eReader file.
#         Using that with Calibre works a lot better than the HTML
#         conversion in this code.
#  0.07 - Further Improved type 272 support for sidebars with all earlier fixes
#  0.08 - fixed typos, removed extraneous things
#  0.09 - fixed typos in first_pages to first_page to again support older formats
#  0.10 - minor cleanups
#  0.11 - fixups for using correct xml for footnotes and sidebars for use with Dropbook
#  0.12 - Fix added to prevent lowercasing of image names when the pml code itself uses a different case in the link name.
#  0.13 - change to unbuffered stdout for use with gui front ends
#  0.14 - contributed enhancement to support --make-pmlz switch
#  0.15 - enabled high-ascii to pml character encoding. DropBook now works on Mac.
#  0.16 - convert to use openssl DES (very very fast) or pure python DES if openssl's libcrypto is not available
#  0.17 - added support for pycrypto's DES as well
#  0.18 - on Windows try PyCrypto first and OpenSSL next
#  0.19 - Modify the interface to allow use of import
#  0.20 - modify to allow use inside new interface for calibre plugins
#  0.21 - Support eReader (drm) version 11.
#       - Don't reject dictionary format.
#       - Ignore sidebars for dictionaries (different format?)
#  0.22 - Unicode and plugin support, different image folders for PMLZ and source
#  0.23 - moved unicode_argv call inside main for Windows DeDRM compatibility

__version__='0.23'

import sys, re
import struct, binascii, getopt, zlib, os, os.path, urllib, tempfile, traceback

if 'calibre' in sys.modules:
    inCalibre = True
else:
    inCalibre = False

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

iswindows = sys.platform.startswith('win')
isosx = sys.platform.startswith('darwin')

def unicode_argv():
    if iswindows:
        # Uses shell32.GetCommandLineArgvW to get sys.argv as a list of Unicode
        # strings.

        # Versions 2.x of Python don't support Unicode in sys.argv on
        # Windows, with the underlying Windows API instead replacing multi-byte
        # characters with '?'.


        from ctypes import POINTER, byref, cdll, c_int, windll
        from ctypes.wintypes import LPCWSTR, LPWSTR

        GetCommandLineW = cdll.kernel32.GetCommandLineW
        GetCommandLineW.argtypes = []
        GetCommandLineW.restype = LPCWSTR

        CommandLineToArgvW = windll.shell32.CommandLineToArgvW
        CommandLineToArgvW.argtypes = [LPCWSTR, POINTER(c_int)]
        CommandLineToArgvW.restype = POINTER(LPWSTR)

        cmd = GetCommandLineW()
        argc = c_int(0)
        argv = CommandLineToArgvW(cmd, byref(argc))
        if argc.value > 0:
            # Remove Python executable and commands if present
            start = argc.value - len(sys.argv)
            return [argv[i] for i in
                    xrange(start, argc.value)]
        # if we don't have any arguments at all, just pass back script name
        # this should never happen
        return [u"mobidedrm.py"]
    else:
        argvencoding = sys.stdin.encoding
        if argvencoding == None:
            argvencoding = "utf-8"
        return [arg if (type(arg) == unicode) else unicode(arg,argvencoding) for arg in sys.argv]

Des = None
if iswindows:
    # first try with pycrypto
    if inCalibre:
        from calibre_plugins.dedrm import pycrypto_des
    else:
        import pycrypto_des
    Des = pycrypto_des.load_pycrypto()
    if Des == None:
        # they try with openssl
        if inCalibre:
            from calibre_plugins.dedrm import openssl_des
        else:
            import openssl_des
        Des = openssl_des.load_libcrypto()
else:
    # first try with openssl
    if inCalibre:
        from calibre_plugins.dedrm import openssl_des
    else:
        import openssl_des
    Des = openssl_des.load_libcrypto()
    if Des == None:
        # then try with pycrypto
        if inCalibre:
            from calibre_plugins.dedrm import pycrypto_des
        else:
            import pycrypto_des
        Des = pycrypto_des.load_pycrypto()

# if that did not work then use pure python implementation
# of DES and try to speed it up with Psycho
if Des == None:
    if inCalibre:
        from calibre_plugins.dedrm import python_des
    else:
        import python_des
    Des = python_des.Des
    # Import Psyco if available
    try:
        # http://psyco.sourceforge.net
        import psyco
        psyco.full()
    except ImportError:
        pass

try:
    from hashlib import sha1
except ImportError:
    # older Python release
    import sha
    sha1 = lambda s: sha.new(s)

import cgi
import logging

logging.basicConfig()
#logging.basicConfig(level=logging.DEBUG)


class Sectionizer(object):
    bkType = "Book"

    def __init__(self, filename, ident):
        self.contents = file(filename, 'rb').read()
        self.header = self.contents[0:72]
        self.num_sections, = struct.unpack('>H', self.contents[76:78])
        # Dictionary or normal content (TODO: Not hard-coded)
        if self.header[0x3C:0x3C+8] != ident:
            if self.header[0x3C:0x3C+8] == "PDctPPrs":
                self.bkType = "Dict"
            else:
                raise ValueError('Invalid file format')
        self.sections = []
        for i in xrange(self.num_sections):
            offset, a1,a2,a3,a4 = struct.unpack('>LBBBB', self.contents[78+i*8:78+i*8+8])
            flags, val = a1, a2<<16|a3<<8|a4
            self.sections.append( (offset, flags, val) )
    def loadSection(self, section):
        if section + 1 == self.num_sections:
            end_off = len(self.contents)
        else:
            end_off = self.sections[section + 1][0]
        off = self.sections[section][0]
        return self.contents[off:end_off]

# cleanup unicode filenames
# borrowed from calibre from calibre/src/calibre/__init__.py
# added in removal of control (<32) chars
# and removal of . at start and end
# and with some (heavily edited) code from Paul Durrant's kindlenamer.py
def sanitizeFileName(name):
    # substitute filename unfriendly characters
    name = name.replace(u"<",u"[").replace(u">",u"]").replace(u" : ",u" – ").replace(u": ",u" – ").replace(u":",u"—").replace(u"/",u"_").replace(u"\\",u"_").replace(u"|",u"_").replace(u"\"",u"\'")
    # delete control characters
    name = u"".join(char for char in name if ord(char)>=32)
    # white space to single space, delete leading and trailing while space
    name = re.sub(ur"\s", u" ", name).strip()
    # remove leading dots
    while len(name)>0 and name[0] == u".":
        name = name[1:]
    # remove trailing dots (Windows doesn't like them)
    if name.endswith(u'.'):
        name = name[:-1]
    return name

def fixKey(key):
    def fixByte(b):
        return b ^ ((b ^ (b<<1) ^ (b<<2) ^ (b<<3) ^ (b<<4) ^ (b<<5) ^ (b<<6) ^ (b<<7) ^ 0x80) & 0x80)
    return     "".join([chr(fixByte(ord(a))) for a in key])

def deXOR(text, sp, table):
    r=''
    j = sp
    for i in xrange(len(text)):
        r += chr(ord(table[j]) ^ ord(text[i]))
        j = j + 1
        if j == len(table):
            j = 0
    return r

class EreaderProcessor(object):
    def __init__(self, sect, user_key):
        self.section_reader = sect.loadSection
        data = self.section_reader(0)
        version,  = struct.unpack('>H', data[0:2])
        self.version = version
        logging.info('eReader file format version %s', version)
        if version != 272 and version != 260 and version != 259:
            raise ValueError('incorrect eReader version %d (error 1)' % version)
        data = self.section_reader(1)
        self.data = data
        des = Des(fixKey(data[0:8]))
        cookie_shuf, cookie_size = struct.unpack('>LL', des.decrypt(data[-8:]))
        if cookie_shuf < 3 or cookie_shuf > 0x14 or cookie_size < 0xf0 or cookie_size > 0x200:
            raise ValueError('incorrect eReader version (error 2)')
        input = des.decrypt(data[-cookie_size:])
        def unshuff(data, shuf):
            r = [''] * len(data)
            j = 0
            for i in xrange(len(data)):
                j = (j + shuf) % len(data)
                r[j] = data[i]
            assert    len("".join(r)) == len(data)
            return "".join(r)
        r = unshuff(input[0:-8], cookie_shuf)

        drm_sub_version = struct.unpack('>H', r[0:2])[0]
        self.num_text_pages = struct.unpack('>H', r[2:4])[0] - 1
        self.num_image_pages = struct.unpack('>H', r[26:26+2])[0]
        self.first_image_page = struct.unpack('>H', r[24:24+2])[0]
        # Default values
        self.num_footnote_pages = 0
        self.num_sidebar_pages = 0
        self.first_footnote_page = -1
        self.first_sidebar_page = -1
        if self.version == 272:
            self.num_footnote_pages = struct.unpack('>H', r[46:46+2])[0]
            self.first_footnote_page = struct.unpack('>H', r[44:44+2])[0]
            if (sect.bkType == "Book"):
                self.num_sidebar_pages = struct.unpack('>H', r[38:38+2])[0]
                self.first_sidebar_page = struct.unpack('>H', r[36:36+2])[0]
            # self.num_bookinfo_pages = struct.unpack('>H', r[34:34+2])[0]
            # self.first_bookinfo_page = struct.unpack('>H', r[32:32+2])[0]
            # self.num_chapter_pages = struct.unpack('>H', r[22:22+2])[0]
            # self.first_chapter_page = struct.unpack('>H', r[20:20+2])[0]
            # self.num_link_pages = struct.unpack('>H', r[30:30+2])[0]
            # self.first_link_page = struct.unpack('>H', r[28:28+2])[0]
            # self.num_xtextsize_pages = struct.unpack('>H', r[54:54+2])[0]
            # self.first_xtextsize_page = struct.unpack('>H', r[52:52+2])[0]

            # **before** data record 1 was decrypted and unshuffled, it contained data
            # to create an XOR table and which is used to fix footnote record 0, link records, chapter records, etc
            self.xortable_offset  = struct.unpack('>H', r[40:40+2])[0]
            self.xortable_size = struct.unpack('>H', r[42:42+2])[0]
            self.xortable = self.data[self.xortable_offset:self.xortable_offset + self.xortable_size]
        else:
            # Nothing needs to be done
            pass
            # self.num_bookinfo_pages = 0
            # self.num_chapter_pages = 0
            # self.num_link_pages = 0
            # self.num_xtextsize_pages = 0
            # self.first_bookinfo_page = -1
            # self.first_chapter_page = -1
            # self.first_link_page = -1
            # self.first_xtextsize_page = -1

        logging.debug('self.num_text_pages %d', self.num_text_pages)
        logging.debug('self.num_footnote_pages %d, self.first_footnote_page %d', self.num_footnote_pages , self.first_footnote_page)
        logging.debug('self.num_sidebar_pages %d, self.first_sidebar_page %d', self.num_sidebar_pages , self.first_sidebar_page)
        self.flags = struct.unpack('>L', r[4:8])[0]
        reqd_flags = (1<<9) | (1<<7) | (1<<10)
        if (self.flags & reqd_flags) != reqd_flags:
            print "Flags: 0x%X" % self.flags
            raise ValueError('incompatible eReader file')
        des = Des(fixKey(user_key))
        if version == 259:
            if drm_sub_version != 7:
                raise ValueError('incorrect eReader version %d (error 3)' % drm_sub_version)
            encrypted_key_sha = r[44:44+20]
            encrypted_key = r[64:64+8]
        elif version == 260:
            if drm_sub_version != 13 and drm_sub_version != 11:
                raise ValueError('incorrect eReader version %d (error 3)' % drm_sub_version)
            if drm_sub_version == 13:
                encrypted_key = r[44:44+8]
                encrypted_key_sha = r[52:52+20]
            else:
                encrypted_key = r[64:64+8]
                encrypted_key_sha = r[44:44+20]
        elif version == 272:
            encrypted_key = r[172:172+8]
            encrypted_key_sha = r[56:56+20]
        self.content_key = des.decrypt(encrypted_key)
        if sha1(self.content_key).digest() != encrypted_key_sha:
            raise ValueError('Incorrect Name and/or Credit Card')

    def getNumImages(self):
        return self.num_image_pages

    def getImage(self, i):
        sect = self.section_reader(self.first_image_page + i)
        name = sect[4:4+32].strip('\0')
        data = sect[62:]
        return sanitizeFileName(unicode(name,'windows-1252')), data


    # def getChapterNamePMLOffsetData(self):
    #     cv = ''
    #     if self.num_chapter_pages > 0:
    #         for i in xrange(self.num_chapter_pages):
    #             chaps = self.section_reader(self.first_chapter_page + i)
    #             j = i % self.xortable_size
    #             offname = deXOR(chaps, j, self.xortable)
    #             offset = struct.unpack('>L', offname[0:4])[0]
    #             name = offname[4:].strip('\0')
    #             cv += '%d|%s\n' % (offset, name)
    #     return cv

    # def getLinkNamePMLOffsetData(self):
    #     lv = ''
    #     if self.num_link_pages > 0:
    #         for i in xrange(self.num_link_pages):
    #             links = self.section_reader(self.first_link_page + i)
    #             j = i % self.xortable_size
    #             offname = deXOR(links, j, self.xortable)
    #             offset = struct.unpack('>L', offname[0:4])[0]
    #             name = offname[4:].strip('\0')
    #             lv += '%d|%s\n' % (offset, name)
    #     return lv

    # def getExpandedTextSizesData(self):
    #      ts = ''
    #      if self.num_xtextsize_pages > 0:
    #          tsize = deXOR(self.section_reader(self.first_xtextsize_page), 0, self.xortable)
    #          for i in xrange(self.num_text_pages):
    #              xsize = struct.unpack('>H', tsize[0:2])[0]
    #              ts += "%d\n" % xsize
    #              tsize = tsize[2:]
    #      return ts

    # def getBookInfo(self):
    #     bkinfo = ''
    #     if self.num_bookinfo_pages > 0:
    #         info = self.section_reader(self.first_bookinfo_page)
    #         bkinfo = deXOR(info, 0, self.xortable)
    #         bkinfo = bkinfo.replace('\0','|')
    #         bkinfo += '\n'
    #     return bkinfo

    def getText(self):
        des = Des(fixKey(self.content_key))
        r = ''
        for i in xrange(self.num_text_pages):
            logging.debug('get page %d', i)
            r += zlib.decompress(des.decrypt(self.section_reader(1 + i)))

        # now handle footnotes pages
        if self.num_footnote_pages > 0:
            r += '\n'
            # the record 0 of the footnote section must pass through the Xor Table to make it useful
            sect = self.section_reader(self.first_footnote_page)
            fnote_ids = deXOR(sect, 0, self.xortable)
            # the remaining records of the footnote sections need to be decoded with the content_key and zlib inflated
            des = Des(fixKey(self.content_key))
            for i in xrange(1,self.num_footnote_pages):
                logging.debug('get footnotepage %d', i)
                id_len = ord(fnote_ids[2])
                id = fnote_ids[3:3+id_len]
                fmarker = '<footnote id="%s">\n' % id
                fmarker += zlib.decompress(des.decrypt(self.section_reader(self.first_footnote_page + i)))
                fmarker += '\n</footnote>\n'
                r += fmarker
                fnote_ids = fnote_ids[id_len+4:]

        # TODO: Handle dictionary index (?) pages - which are also marked as
        # sidebar_pages (?). For now dictionary sidebars are ignored
        # For dictionaries - record 0 is null terminated strings, followed by
        # blocks of around 62000 bytes and a final block. Not sure of the
        # encoding

        # now handle sidebar pages
        if self.num_sidebar_pages > 0:
            r += '\n'
            # the record 0 of the sidebar section must pass through the Xor Table to make it useful
            sect = self.section_reader(self.first_sidebar_page)
            sbar_ids = deXOR(sect, 0, self.xortable)
            # the remaining records of the sidebar sections need to be decoded with the content_key and zlib inflated
            des = Des(fixKey(self.content_key))
            for i in xrange(1,self.num_sidebar_pages):
                id_len = ord(sbar_ids[2])
                id = sbar_ids[3:3+id_len]
                smarker = '<sidebar id="%s">\n' % id
                smarker += zlib.decompress(des.decrypt(self.section_reader(self.first_sidebar_page + i)))
                smarker += '\n</sidebar>\n'
                r += smarker
                sbar_ids = sbar_ids[id_len+4:]

        return r

def cleanPML(pml):
    # Convert special characters to proper PML code.  High ASCII start at (\x80, \a128) and go up to (\xff, \a255)
    pml2 = pml
    for k in xrange(128,256):
        badChar = chr(k)
        pml2 = pml2.replace(badChar, '\\a%03d' % k)
    return pml2

def decryptBook(infile, outpath, make_pmlz, user_key):
    bookname = os.path.splitext(os.path.basename(infile))[0]
    if make_pmlz:
        # outpath is actually pmlz name
        pmlzname = outpath
        outdir = tempfile.mkdtemp()
        imagedirpath = os.path.join(outdir,u"images")
    else:
        pmlzname = None
        outdir = outpath
        imagedirpath = os.path.join(outdir,bookname + u"_img")

    try:
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        print u"Decoding File"
        sect = Sectionizer(infile, 'PNRdPPrs')
        er = EreaderProcessor(sect, user_key)

        if er.getNumImages() > 0:
            print u"Extracting images"
            if not os.path.exists(imagedirpath):
                os.makedirs(imagedirpath)
            for i in xrange(er.getNumImages()):
                name, contents = er.getImage(i)
                file(os.path.join(imagedirpath, name), 'wb').write(contents)

        print u"Extracting pml"
        pml_string = er.getText()
        pmlfilename = bookname + ".pml"
        file(os.path.join(outdir, pmlfilename),'wb').write(cleanPML(pml_string))
        if pmlzname is not None:
            import zipfile
            import shutil
            print u"Creating PMLZ file {0}".format(os.path.basename(pmlzname))
            myZipFile = zipfile.ZipFile(pmlzname,'w',zipfile.ZIP_STORED, False)
            list = os.listdir(outdir)
            for filename in list:
                localname = filename
                filePath = os.path.join(outdir,filename)
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
            # remove temporary directory
            shutil.rmtree(outdir, True)
            print u"Output is {0}".format(pmlzname)
        else :
            print u"Output is in {0}".format(outdir)
        print "done"
    except ValueError, e:
        print u"Error: {0}".format(e)
        traceback.print_exc()
        return 1
    return 0


def usage():
    print u"Converts DRMed eReader books to PML Source"
    print u"Usage:"
    print u"  erdr2pml [options] infile.pdb [outpath] \"your name\" credit_card_number"
    print u" "
    print u"Options: "
    print u"  -h             prints this message"
    print u"  -p             create PMLZ instead of source folder"
    print u"  --make-pmlz    create PMLZ instead of source folder"
    print u" "
    print u"Note:"
    print u"  if outpath is ommitted, creates source in 'infile_Source' folder"
    print u"  if outpath is ommitted and pmlz option, creates PMLZ 'infile.pmlz'"
    print u"  if source folder created, images are in infile_img folder"
    print u"  if pmlz file created, images are in images folder"
    print u"  It's enough to enter the last 8 digits of the credit card number"
    return

def getuser_key(name,cc):
    newname = "".join(c for c in name.lower() if c >= 'a' and c <= 'z' or c >= '0' and c <= '9')
    cc = cc.replace(" ","")
    return struct.pack('>LL', binascii.crc32(newname) & 0xffffffff,binascii.crc32(cc[-8:])& 0xffffffff)

def cli_main():
    print u"eRdr2Pml v{0}. Copyright © 2009–2012 The Dark Reverser et al.".format(__version__)

    argv=unicode_argv()
    try:
        opts, args = getopt.getopt(argv[1:], "hp", ["make-pmlz"])
    except getopt.GetoptError, err:
        print err.args[0]
        usage()
        return 1
    make_pmlz = False
    for o, a in opts:
        if o == "-h":
            usage()
            return 0
        elif o == "-p":
            make_pmlz = True
        elif o == "--make-pmlz":
            make_pmlz = True

    if len(args)!=3 and len(args)!=4:
        usage()
        return 1

    if len(args)==3:
        infile, name, cc = args
        if make_pmlz:
            outpath = os.path.splitext(infile)[0] + u".pmlz"
        else:
            outpath = os.path.splitext(infile)[0] + u"_Source"
    elif len(args)==4:
        infile, outpath, name, cc = args

    print getuser_key(name,cc).encode('hex')

    return decryptBook(infile, outpath, make_pmlz, getuser_key(name,cc))


if __name__ == "__main__":
    sys.stdout=SafeUnbuffered(sys.stdout)
    sys.stderr=SafeUnbuffered(sys.stderr)
    sys.exit(cli_main())

