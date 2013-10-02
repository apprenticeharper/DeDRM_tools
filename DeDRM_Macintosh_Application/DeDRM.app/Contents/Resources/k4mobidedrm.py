#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement

# ignobleepub.pyw, version 3.6
# Copyright © 2009-2012 by DiapDealer et al.

# engine to remove drm from Kindle for Mac and Kindle for PC books
# for personal use for archiving and converting your ebooks

# PLEASE DO NOT PIRATE EBOOKS!

# We want all authors and publishers, and eBook stores to live
# long and prosperous lives but at the same time  we just want to
# be able to read OUR books on whatever device we want and to keep
# readable for a long, long time

# This borrows very heavily from works by CMBDTC, IHeartCabbages, skindle,
#    unswindle, DarkReverser, ApprenticeAlf, DiapDealer, some_updates
#    and many many others
# Special thanks to The Dark Reverser for MobiDeDrm and CMBDTC for cmbdtc_dump
# from which this script borrows most unashamedly.


# Changelog
#  1.0 - Name change to k4mobidedrm. Adds Mac support, Adds plugin code
#  1.1 - Adds support for additional kindle.info files
#  1.2 - Better error handling for older Mobipocket
#  1.3 - Don't try to decrypt Topaz books
#  1.7 - Add support for Topaz books and Kindle serial numbers. Split code.
#  1.9 - Tidy up after Topaz, minor exception changes
#  2.1 - Topaz fix and filename sanitizing
#  2.2 - Topaz Fix and minor Mac code fix
#  2.3 - More Topaz fixes
#  2.4 - K4PC/Mac key generation fix
#  2.6 - Better handling of non-K4PC/Mac ebooks
#  2.7 - Better trailing bytes handling in mobidedrm
#  2.8 - Moved parsing of kindle.info files to mac & pc util files.
#  3.1 - Updated for new calibre interface. Now __init__ in plugin.
#  3.5 - Now support Kindle for PC/Mac 1.6
#  3.6 - Even better trailing bytes handling in mobidedrm
#  3.7 - Add support for Amazon Print Replica ebooks.
#  3.8 - Improved Topaz support
#  4.1 - Improved Topaz support and faster decryption with alfcrypto
#  4.2 - Added support for Amazon's KF8 format ebooks
#  4.4 - Linux calls to Wine added, and improved configuration dialog
#  4.5 - Linux works again without Wine. Some Mac key file search changes
#  4.6 - First attempt to handle unicode properly
#  4.7 - Added timing reports, and changed search for Mac key files
#  4.8 - Much better unicode handling, matching the updated inept and ignoble scripts
#      - Moved back into plugin, __init__ in plugin now only contains plugin code.
#  4.9 - Missed some invalid characters in cleanup_name
#  5.0 - Extraction of info from Kindle for PC/Mac moved into kindlekey.py
#      - tweaked GetDecryptedBook interface to leave passed parameters unchanged
#  5.1 - moved unicode_argv call inside main for Windows DeDRM compatibility
#  5.2 - Fixed error in command line processing of unicode arguments

__version__ = '5.2'


import sys, os, re
import csv
import getopt
import re
import traceback
import time
import htmlentitydefs
import json

class DrmException(Exception):
    pass

if 'calibre' in sys.modules:
    inCalibre = True
else:
    inCalibre = False

if inCalibre:
    from calibre_plugins.dedrm import mobidedrm
    from calibre_plugins.dedrm import topazextract
    from calibre_plugins.dedrm import kgenpids
    from calibre_plugins.dedrm import android
else:
    import mobidedrm
    import topazextract
    import kgenpids
    import android

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

# cleanup unicode filenames
# borrowed from calibre from calibre/src/calibre/__init__.py
# added in removal of control (<32) chars
# and removal of . at start and end
# and with some (heavily edited) code from Paul Durrant's kindlenamer.py
def cleanup_name(name):
    # substitute filename unfriendly characters
    name = name.replace(u"<",u"[").replace(u">",u"]").replace(u" : ",u" – ").replace(u": ",u" – ").replace(u":",u"—").replace(u"/",u"_").replace(u"\\",u"_").replace(u"|",u"_").replace(u"\"",u"\'").replace(u"*",u"_").replace(u"?",u"")
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

# must be passed unicode
def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == u"&#":
            # character reference
            try:
                if text[:3] == u"&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub(u"&#?\w+;", fixup, text)

def GetDecryptedBook(infile, kDatabases, serials, pids, starttime = time.time()):
    # handle the obvious cases at the beginning
    if not os.path.isfile(infile):
        raise DrmException(u"Input file does not exist.")

    mobi = True
    magic3 = open(infile,'rb').read(3)
    if magic3 == 'TPZ':
        mobi = False

    if mobi:
        mb = mobidedrm.MobiBook(infile)
    else:
        mb = topazextract.TopazBook(infile)

    bookname = unescape(mb.getBookTitle())
    print u"Decrypting {1} ebook: {0}".format(bookname, mb.getBookType())

    # copy list of pids
    totalpids = list(pids)
    # extend PID list with book-specific PIDs
    md1, md2 = mb.getPIDMetaInfo()
    totalpids.extend(kgenpids.getPidList(md1, md2, serials, kDatabases))
    print u"Found {1:d} keys to try after {0:.1f} seconds".format(time.time()-starttime, len(totalpids))

    try:
        mb.processBook(totalpids)
    except:
        mb.cleanup
        raise

    print u"Decryption succeeded after {0:.1f} seconds".format(time.time()-starttime)
    return mb


# kDatabaseFiles is a list of files created by kindlekey
def decryptBook(infile, outdir, kDatabaseFiles, serials, pids):
    starttime = time.time()
    kDatabases = []
    for dbfile in kDatabaseFiles:
        kindleDatabase = {}
        try:
            with open(dbfile, 'r') as keyfilein:
                kindleDatabase = json.loads(keyfilein.read())
            kDatabases.append([dbfile,kindleDatabase])
        except Exception, e:
            print u"Error getting database from file {0:s}: {1:s}".format(dbfile,e)
            traceback.print_exc()



    try:
        book = GetDecryptedBook(infile, kDatabases, serials, pids, starttime)
    except Exception, e:
        print u"Error decrypting book after {1:.1f} seconds: {0}".format(e.args[0],time.time()-starttime)
        traceback.print_exc()
        return 1

    # if we're saving to the same folder as the original, use file name_
    # if to a different folder, use book name
    if os.path.normcase(os.path.normpath(outdir)) == os.path.normcase(os.path.normpath(os.path.dirname(infile))):
        outfilename = os.path.splitext(os.path.basename(infile))[0]
    else:
        outfilename = cleanup_name(book.getBookTitle())

    # avoid excessively long file names
    if len(outfilename)>150:
        outfilename = outfilename[:150]

    outfilename = outfilename+u"_nodrm"
    outfile = os.path.join(outdir, outfilename + book.getBookExtension())

    book.getFile(outfile)
    print u"Saved decrypted book {1:s} after {0:.1f} seconds".format(time.time()-starttime, outfilename)

    if book.getBookType()==u"Topaz":
        zipname = os.path.join(outdir, outfilename + u"_SVG.zip")
        book.getSVGZip(zipname)
        print u"Saved SVG ZIP Archive for {1:s} after {0:.1f} seconds".format(time.time()-starttime, outfilename)

    # remove internal temporary directory of Topaz pieces
    book.cleanup()
    return 0


def usage(progname):
    print u"Removes DRM protection from Mobipocket, Amazon KF8, Amazon Print Replica and Amazon Topaz ebooks"
    print u"Usage:"
    print u"    {0} [-k <kindle.k4i>] [-p <comma separated PIDs>] [-s <comma separated Kindle serial numbers>] [ -a <AmazonSecureStorage.xml> ] <infile> <outdir>".format(progname)

#
# Main
#
def cli_main():
    argv=unicode_argv()
    progname = os.path.basename(argv[0])
    print u"K4MobiDeDrm v{0}.\nCopyright © 2008-2013 The Dark Reverser et al.".format(__version__)

    try:
        opts, args = getopt.getopt(argv[1:], "k:p:s:a:")
    except getopt.GetoptError, err:
        print u"Error in options or arguments: {0}".format(err.args[0])
        usage(progname)
        sys.exit(2)
    if len(args)<2:
        usage(progname)
        sys.exit(2)

    infile = args[0]
    outdir = args[1]
    kDatabaseFiles = []
    serials = []
    pids = []

    for o, a in opts:
        if o == "-k":
            if a == None :
                raise DrmException("Invalid parameter for -k")
            kDatabaseFiles.append(a)
        if o == "-p":
            if a == None :
                raise DrmException("Invalid parameter for -p")
            pids = a.split(',')
        if o == "-s":
            if a == None :
                raise DrmException("Invalid parameter for -s")
            serials = a.split(',')
        if o == '-a':
            if a == None:
                continue
            serials.extend(android.get_serials(a))
    serials.extend(android.get_serials())

    # try with built in Kindle Info files if not on Linux
    k4 = not sys.platform.startswith('linux')

    return decryptBook(infile, outdir, kDatabaseFiles, serials, pids)


if __name__ == '__main__':
    sys.stdout=SafeUnbuffered(sys.stdout)
    sys.stderr=SafeUnbuffered(sys.stderr)
    sys.exit(cli_main())
