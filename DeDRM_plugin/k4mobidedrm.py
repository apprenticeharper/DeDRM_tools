#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# k4mobidedrm.py
# Copyright © 2008-2020 by Apprentice Harper et al.

__license__ = 'GPL v3'
__version__ = '6.0'

# Engine to remove drm from Kindle and Mobipocket ebooks
# for personal use for archiving and converting your ebooks

# PLEASE DO NOT PIRATE EBOOKS!

# We want all authors and publishers, and ebook stores to live
# long and prosperous lives but at the same time  we just want to
# be able to read OUR books on whatever device we want and to keep
# readable for a long, long time

# This borrows very heavily from works by CMBDTC, IHeartCabbages, skindle,
#    unswindle, DarkReverser, ApprenticeAlf, and many many others

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
#  5.3 - Changed Android support to allow passing of backup .ab files
#  5.4 - Recognise KFX files masquerading as azw, even if we can't decrypt them yet.
#  5.5 - Added GPL v3 licence explicitly.
#  5.6 - Invoke KFXZipBook to handle zipped KFX files
#  5.7 - Revamp cleanup_name
#  6.0 - Added Python 3 compatibility for calibre 5.0


import sys, os, re
import csv
import getopt
import re
import traceback
import time
import html.entities
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
    from calibre_plugins.dedrm import androidkindlekey
    from calibre_plugins.dedrm import kfxdedrm
else:
    import mobidedrm
    import topazextract
    import kgenpids
    import androidkindlekey
    import kfxdedrm

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
        if isinstance(data, str):
            data = data.encode(self.encoding,"replace")
        self.stream.buffer.write(data)
        self.stream.buffer.flush()

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
                    range(start, argc.value)]
        # if we don't have any arguments at all, just pass back script name
        # this should never happen
        return ["mobidedrm.py"]
    else:
        argvencoding = sys.stdin.encoding or "utf-8"
        return [arg if isinstance(arg, str) else str(arg, argvencoding) for arg in sys.argv]

# cleanup unicode filenames
# borrowed from calibre from calibre/src/calibre/__init__.py
# added in removal of control (<32) chars
# and removal of . at start and end
# and with some (heavily edited) code from Paul Durrant's kindlenamer.py
# and some improvements suggested by jhaisley
def cleanup_name(name):
    # substitute filename unfriendly characters
    name = name.replace("<","[").replace(">","]").replace(" : "," – ").replace(": "," – ").replace(":","—").replace("/","_").replace("\\","_").replace("|","_").replace("\"","\'").replace("*","_").replace("?","")
    # white space to single space, delete leading and trailing while space
    name = re.sub(r"\s", " ", name).strip()
    # delete control characters
    name = "".join(char for char in name if ord(char)>=32)
    # delete non-ascii characters
    name = "".join(char for char in name if ord(char)<=126)
    # remove leading dots
    while len(name)>0 and name[0] == ".":
        name = name[1:]
    # remove trailing dots (Windows doesn't like them)
    while name.endswith("."):
        name = name[:-1]
    if len(name)==0:
        name="DecryptedBook"
    return name

# must be passed unicode
def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return chr(int(text[3:-1], 16))
                else:
                    return chr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = chr(html.entities.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\\w+;", fixup, text)

def GetDecryptedBook(infile, kDatabases, androidFiles, serials, pids, starttime = time.time()):
    # handle the obvious cases at the beginning
    if not os.path.isfile(infile):
        raise DrmException("Input file does not exist.")

    mobi = True
    magic8 = open(infile,'rb').read(8)
    if magic8 == b'\xeaDRMION\xee':
        raise DrmException("The .kfx DRMION file cannot be decrypted by itself. A .kfx-zip archive containing a DRM voucher is required.")

    magic3 = magic8[:3]
    if magic3 == b'TPZ':
        mobi = False

    if magic8[:4] == b'PK\x03\x04':
        mb = kfxdedrm.KFXZipBook(infile)
    elif mobi:
        mb = mobidedrm.MobiBook(infile)
    else:
        mb = topazextract.TopazBook(infile)

    bookname = unescape(mb.getBookTitle())
    print("Decrypting {1} ebook: {0}".format(bookname, mb.getBookType()))

    # copy list of pids
    totalpids = list(pids)
    # extend list of serials with serials from android databases
    for aFile in androidFiles:
        serials.extend(androidkindlekey.get_serials(aFile))
    # extend PID list with book-specific PIDs from seriala and kDatabases
    md1, md2 = mb.getPIDMetaInfo()
    totalpids.extend(kgenpids.getPidList(md1, md2, serials, kDatabases))
    # remove any duplicates
    totalpids = list(set(totalpids))
    print("Found {1:d} keys to try after {0:.1f} seconds".format(time.time()-starttime, len(totalpids)))
    #print totalpids

    try:
        mb.processBook(totalpids)
    except:
        mb.cleanup
        raise

    print("Decryption succeeded after {0:.1f} seconds".format(time.time()-starttime))
    return mb


# kDatabaseFiles is a list of files created by kindlekey
def decryptBook(infile, outdir, kDatabaseFiles, androidFiles, serials, pids):
    starttime = time.time()
    kDatabases = []
    for dbfile in kDatabaseFiles:
        kindleDatabase = {}
        try:
            with open(dbfile, 'r') as keyfilein:
                kindleDatabase = json.loads(keyfilein.read())
            kDatabases.append([dbfile,kindleDatabase])
        except Exception as e:
            print("Error getting database from file {0:s}: {1:s}".format(dbfile,e))
            traceback.print_exc()



    try:
        book = GetDecryptedBook(infile, kDatabases, androidFiles, serials, pids, starttime)
    except Exception as e:
        print("Error decrypting book after {1:.1f} seconds: {0}".format(e.args[0],time.time()-starttime))
        traceback.print_exc()
        return 1

    # Try to infer a reasonable name
    orig_fn_root = os.path.splitext(os.path.basename(infile))[0]
    if (
        re.match('^B[A-Z0-9]{9}(_EBOK|_EBSP|_sample)?$', orig_fn_root) or
        re.match('^{0-9A-F-}{36}$', orig_fn_root)
    ):  # Kindle for PC / Mac / Android / Fire / iOS
        clean_title = cleanup_name(book.getBookTitle())
        outfilename = "{}_{}".format(orig_fn_root, clean_title)
    else:  # E Ink Kindle, which already uses a reasonable name
        outfilename = orig_fn_root

    # avoid excessively long file names
    if len(outfilename)>150:
        outfilename = outfilename[:99]+"--"+outfilename[-49:]

    outfilename = outfilename+"_nodrm"
    outfile = os.path.join(outdir, outfilename + book.getBookExtension())

    book.getFile(outfile)
    print("Saved decrypted book {1:s} after {0:.1f} seconds".format(time.time()-starttime, outfilename))

    if book.getBookType()=="Topaz":
        zipname = os.path.join(outdir, outfilename + "_SVG.zip")
        book.getSVGZip(zipname)
        print("Saved SVG ZIP Archive for {1:s} after {0:.1f} seconds".format(time.time()-starttime, outfilename))

    # remove internal temporary directory of Topaz pieces
    book.cleanup()
    return 0


def usage(progname):
    print("Removes DRM protection from Mobipocket, Amazon KF8, Amazon Print Replica and Amazon Topaz ebooks")
    print("Usage:")
    print("    {0} [-k <kindle.k4i>] [-p <comma separated PIDs>] [-s <comma separated Kindle serial numbers>] [ -a <AmazonSecureStorage.xml|backup.ab> ] <infile> <outdir>".format(progname))

#
# Main
#
def cli_main():
    argv=unicode_argv()
    progname = os.path.basename(argv[0])
    print("K4MobiDeDrm v{0}.\nCopyright © 2008-2020 Apprentice Harper et al.".format(__version__))

    try:
        opts, args = getopt.getopt(argv[1:], "k:p:s:a:h")
    except getopt.GetoptError as err:
        print("Error in options or arguments: {0}".format(err.args[0]))
        usage(progname)
        sys.exit(2)
    if len(args)<2:
        usage(progname)
        sys.exit(2)

    infile = args[0]
    outdir = args[1]
    kDatabaseFiles = []
    androidFiles = []
    serials = []
    pids = []

    for o, a in opts:
        if o == "-h":
            usage(progname)
            sys.exit(0)
        if o == "-k":
            if a == None :
                raise DrmException("Invalid parameter for -k")
            kDatabaseFiles.append(a)
        if o == "-p":
            if a == None :
                raise DrmException("Invalid parameter for -p")
            pids = a.encode('utf-8').split(b',')
        if o == "-s":
            if a == None :
                raise DrmException("Invalid parameter for -s")
            serials = a.split(',')
        if o == '-a':
            if a == None:
                raise DrmException("Invalid parameter for -a")
            androidFiles.append(a)

    return decryptBook(infile, outdir, kDatabaseFiles, androidFiles, serials, pids)


if __name__ == '__main__':
    sys.stdout=SafeUnbuffered(sys.stdout)
    sys.stderr=SafeUnbuffered(sys.stderr)
    sys.exit(cli_main())
