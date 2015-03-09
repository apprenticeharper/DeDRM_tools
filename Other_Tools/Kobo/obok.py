#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Version 3.1.2 January 2015
# Add coding, version number and version announcement
#
# Version 3.05 October 2014
# Identifies DRM-free books in the dialog
#
# Version 3.04 September 2014
# Handles DRM-free books as well (sometimes Kobo Library doesn't
# show download link for DRM-free books)
#
# Version 3.03 August 2014
# If PyCrypto is unavailable try to use libcrypto for AES_ECB.
#
# Version 3.02 August 2014
# Relax checking of application/xhtml+xml  and image/jpeg content.
#
# Version 3.01 June 2014
# Check image/jpeg as well as application/xhtml+xml content. Fix typo
# in Windows ipconfig parsing.
#
# Version 3.0 June 2014
# Made portable for Mac and Windows, and the only module dependency
# not part of python core is PyCrypto. Major code cleanup/rewrite.
# No longer tries the first MAC address; tries them all if it detects
# the decryption failed.
#
# Updated September 2013 by Anon
# Version 2.02
# Incorporated minor fixes posted at Apprentice Alf's.
#
# Updates July 2012 by Michael Newton
# PWSD ID is no longer a MAC address, but should always
# be stored in the registry. Script now works with OS X
# and checks plist for values instead of registry. Must
# have biplist installed for OS X support.
#
# Original comments left below; note the "AUTOPSY" is inaccurate. See
# KoboLibrary.userkeys and KoboFile.decrypt()
#
##########################################################
#                    KOBO DRM CRACK BY                   #
#                      PHYSISTICATED                     #
##########################################################
# This app was made for Python 2.7 on Windows 32-bit
#
# This app needs pycrypto - get from here:
# http://www.voidspace.org.uk/python/modules.shtml
#
# Usage: obok.py
# Choose the book you want to decrypt
#
# Shouts to my krew - you know who you are - and one in
# particular who gave me a lot of help with this - thank
# you so much!
#
# Kopimi /K\
# Keep sharing, keep copying, but remember that nothing is
# for free - make sure you compensate your favorite
# authors - and cut out the middle man whenever possible
# ;) ;) ;)
#
# DRM AUTOPSY
# The Kobo DRM was incredibly easy to crack, but it took
# me months to get around to making this. Here's the
# basics of how it works:
# 1: Get MAC address of first NIC in ipconfig (sometimes
# stored in registry as pwsdid)
# 2: Get user ID (stored in tons of places, this gets it
# from HKEY_CURRENT_USER\Software\Kobo\Kobo Desktop
# Edition\Browser\cookies)
# 3: Concatenate and SHA256, take the second half - this
# is your master key
# 4: Open %LOCALAPPDATA%\Kobo Desktop Editions\Kobo.sqlite
# and dump content_keys
# 5: Unbase64 the keys, then decode these with the master
# key - these are your page keys
# 6: Unzip EPUB of your choice, decrypt each page with its
# page key, then zip back up again
#
# WHY USE THIS WHEN INEPT WORKS FINE? (adobe DRM stripper)
# Inept works very well, but authors on Kobo can choose
# what DRM they want to use - and some have chosen not to
# let people download them with Adobe Digital Editions -
# they would rather lock you into a single platform.
#
# With Obok, you can sync Kobo Desktop, decrypt all your
# ebooks, and then use them on whatever device you want
# - you bought them, you own them, you can do what you
# like with them.
#
# Obok is Kobo backwards, but it is also means "next to"
# in Polish.
# When you buy a real book, it is right next to you. You
# can read it at home, at work, on a train, you can lend
# it to a friend, you can scribble on it, and add your own
# explanations/translations.
#
# Obok gives you this power over your ebooks - no longer
# are you restricted to one device. This allows you to
# embed foreign fonts into your books, as older Kobo's
# can't display them properly. You can read your books
# on your phones, in different PC readers, and different
# ereader devices. You can share them with your friends
# too, if you like - you can do that with a real book
# after all.
#
"""Manage all Kobo books, either encrypted or DRM-free."""

__version__ = '3.1.1'

import sys
import os
import subprocess
import sqlite3
import base64
import binascii
import re
import zipfile
import hashlib
import xml.etree.ElementTree as ET
import string
import shutil

class ENCRYPTIONError(Exception):
    pass

def _load_crypto_libcrypto():
    from ctypes import CDLL, POINTER, c_void_p, c_char_p, c_int, c_long, \
        Structure, c_ulong, create_string_buffer, cast
    from ctypes.util import find_library

    if sys.platform.startswith('win'):
        libcrypto = find_library('libeay32')
    else:
        libcrypto = find_library('crypto')

    if libcrypto is None:
        raise ENCRYPTIONError('libcrypto not found')
    libcrypto = CDLL(libcrypto)

    AES_MAXNR = 14

    c_char_pp = POINTER(c_char_p)
    c_int_p = POINTER(c_int)

    class AES_KEY(Structure):
        _fields_ = [('rd_key', c_long * (4 * (AES_MAXNR + 1))),
                    ('rounds', c_int)]
    AES_KEY_p = POINTER(AES_KEY)

    def F(restype, name, argtypes):
        func = getattr(libcrypto, name)
        func.restype = restype
        func.argtypes = argtypes
        return func

    AES_set_decrypt_key = F(c_int, 'AES_set_decrypt_key',
                            [c_char_p, c_int, AES_KEY_p])
    AES_ecb_encrypt = F(None, 'AES_ecb_encrypt',
                        [c_char_p, c_char_p, AES_KEY_p, c_int])

    class AES(object):
        def __init__(self, userkey):
            self._blocksize = len(userkey)
            if (self._blocksize != 16) and (self._blocksize != 24) and (self._blocksize != 32) :
                raise ENCRYPTIONError(_('AES improper key used'))
                return
            key = self._key = AES_KEY()
            rv = AES_set_decrypt_key(userkey, len(userkey) * 8, key)
            if rv < 0:
                raise ENCRYPTIONError(_('Failed to initialize AES key'))

        def decrypt(self, data):
            clear = ''
            for i in range(0, len(data), 16):
                out = create_string_buffer(16)
                rv = AES_ecb_encrypt(data[i:i+16], out, self._key, 0)
                if rv == 0:
                    raise ENCRYPTIONError(_('AES decryption failed'))
                clear += out.raw
            return clear

    return AES

def _load_crypto_pycrypto():
    from Crypto.Cipher import AES as _AES
    class AES(object):
        def __init__(self, key):
            self._aes = _AES.new(key, _AES.MODE_ECB)

        def decrypt(self, data):
            return self._aes.decrypt(data)

    return AES

def _load_crypto():
    AES = None
    cryptolist = (_load_crypto_pycrypto, _load_crypto_libcrypto)
    for loader in cryptolist:
        try:
            AES = loader()
            break
        except (ImportError, ENCRYPTIONError):
            pass
    return AES

AES = _load_crypto()

class KoboLibrary(object):
    """The Kobo library.

    This class represents all the information available from the data
    written by the Kobo Desktop Edition application, including the list
    of books, their titles, and the user's encryption key(s)."""

    def __init__ (self):
        print u"Obok v{0}\nCopyright © 2012-2014 Physisticated et al.".format(__version__)
        if sys.platform.startswith('win'):
            if sys.getwindowsversion().major > 5:
                self.kobodir = os.environ['LOCALAPPDATA']
            else:
                self.kobodir = os.path.join(os.environ['USERPROFILE'], 'Local Settings', 'Application Data')
            self.kobodir = os.path.join(self.kobodir, 'Kobo', 'Kobo Desktop Edition')
        elif sys.platform.startswith('darwin'):
            self.kobodir = os.path.join(os.environ['HOME'], 'Library', 'Application Support', 'Kobo', 'Kobo Desktop Edition')
        self.bookdir = os.path.join(self.kobodir, 'kepub')
        kobodb = os.path.join(self.kobodir, 'Kobo.sqlite')
        self.__sqlite = sqlite3.connect(kobodb)
        self.__cursor = self.__sqlite.cursor()
        self._userkeys = []
        self._books = []
        self._volumeID = []

    def close (self):
        """Closes the database used by the library."""
        self.__cursor.close()
        self.__sqlite.close()

    @property
    def userkeys (self):
        """The list of potential userkeys being used by this library.
        Only one of these will be valid.
        """
        if len(self._userkeys) != 0:
            return self._userkeys
        userid = self.__getuserid()
        for macaddr in self.__getmacaddrs():
            self._userkeys.append(self.__getuserkey(macaddr, userid))
        return self._userkeys

    @property
    def books (self):
        """The list of KoboBook objects in the library."""
        if len(self._books) != 0:
            return self._books
        """Drm-ed kepub"""
        for row in self.__cursor.execute('SELECT DISTINCT volumeid, Title, Attribution, Series FROM content_keys, content WHERE contentid = volumeid'):
            self._books.append(KoboBook(row[0], row[1], self.__bookfile(row[0]), 'kepub', self.__cursor, author=row[2], series=row[3]))
            self._volumeID.append(row[0])
        """Drm-free"""
        for f in os.listdir(self.bookdir):
            if(f not in self._volumeID):
                row = self.__cursor.execute("SELECT Title, Attribution, Series FROM content WHERE ContentID = '" + f + "'").fetchone()
                if row is not None:
                    fTitle = row[0]
                    self._books.append(KoboBook(f, fTitle, self.__bookfile(f), 'drm-free', self.__cursor, author=row[1], series=row[2]))
                    self._volumeID.append(f)
        """Sort"""
        self._books.sort(key=lambda x: x.title)
        return self._books

    def __bookfile (self, volumeid):
        """The filename needed to open a given book."""
        return os.path.join(self.kobodir, 'kepub', volumeid)

    def __getmacaddrs (self):
        """The list of all MAC addresses on this machine."""
        macaddrs = []
        if sys.platform.startswith('win'):
            c = re.compile('\s(' + '[0-9a-f]{2}-' * 5 + '[0-9a-f]{2})(\s|$)', re.IGNORECASE)
            for line in os.popen('ipconfig /all'):
                m = c.search(line)
                if m:
                    macaddrs.append(re.sub("-", ":", m.group(1)).upper())
        elif sys.platform.startswith('darwin'):
            c = re.compile('\s(' + '[0-9a-f]{2}:' * 5 + '[0-9a-f]{2})(\s|$)', re.IGNORECASE)
            output = subprocess.check_output('/sbin/ifconfig -a', shell=True)
            matches = c.findall(output)
            for m in matches:
                # print "m:",m[0]
                macaddrs.append(m[0].upper())
        return macaddrs

    def __getuserid (self):
        return self.__cursor.execute('SELECT UserID FROM user WHERE HasMadePurchase = "true"').fetchone()[0]

    def __getuserkey (self, macaddr, userid):
        deviceid = hashlib.sha256('NoCanLook' + macaddr).hexdigest()
        userkey = hashlib.sha256(deviceid + userid).hexdigest()
        return binascii.a2b_hex(userkey[32:])

class KoboBook(object):
    """A Kobo book.

    A Kobo book contains a number of unencrypted and encrypted files.
    This class provides a list of the encrypted files.

    Each book has the following instance variables:
    volumeid - a UUID which uniquely refers to the book in this library.
    title - the human-readable book title.
    filename - the complete path and filename of the book.
    type - either kepub or drm-free"""
    def __init__ (self, volumeid, title, filename, type, cursor, author=None, series=None):
        self.volumeid = volumeid
        self.title = title
        self.author = author
        self.series = series
        self.series_index = None
        self.filename = filename
        self.type = type
        self.__cursor = cursor
        self._encryptedfiles = {}

    @property
    def encryptedfiles (self):
        """A dictionary of KoboFiles inside the book.

        The dictionary keys are the relative pathnames, which are
        the same as the pathnames inside the book 'zip' file."""
        if (self.type == 'drm-free'):
            return self._encryptedfiles
        if len(self._encryptedfiles) != 0:
            return self._encryptedfiles
        # Read the list of encrypted files from the DB
        for row in self.__cursor.execute('SELECT elementid,elementkey FROM content_keys,content WHERE volumeid = ? AND volumeid = contentid',(self.volumeid,)):
            self._encryptedfiles[row[0]] = KoboFile(row[0], None, base64.b64decode(row[1]))

        # Read the list of files from the kepub OPF manifest so that
        # we can get their proper MIME type.
        # NOTE: this requires that the OPF file is unencrypted!
        zin = zipfile.ZipFile(self.filename, "r")
        xmlns = {
            'ocf': 'urn:oasis:names:tc:opendocument:xmlns:container',
            'opf': 'http://www.idpf.org/2007/opf'
        }
        ocf = ET.fromstring(zin.read('META-INF/container.xml'))
        opffile = ocf.find('.//ocf:rootfile', xmlns).attrib['full-path']
        basedir = re.sub('[^/]+$', '', opffile)
        opf = ET.fromstring(zin.read(opffile))
        zin.close()

        c = re.compile('/')
        for item in opf.findall('.//opf:item', xmlns):
            mimetype = item.attrib['media-type']

            # Convert relative URIs
            href = item.attrib['href']
            if not c.match(href):
                href = string.join((basedir, href), '')

            # Update books we've found from the DB.
            if href in self._encryptedfiles:
                self._encryptedfiles[href].mimetype = mimetype
        return self._encryptedfiles

    @property
    def has_drm (self):
        return not self.type == 'drm-free'


class KoboFile(object):
    """An encrypted file in a KoboBook.

    Each file has the following instance variables:
    filename - the relative pathname inside the book zip file.
    mimetype - the file's MIME type, e.g. 'image/jpeg'
    key - the encrypted page key."""

    def __init__ (self, filename, mimetype, key):
        self.filename = filename
        self.mimetype = mimetype
        self.key = key
    def decrypt (self, userkey, contents):
        """
        Decrypt the contents using the provided user key and the
        file page key. The caller must determine if the decrypted
        data is correct."""
        # The userkey decrypts the page key (self.key)
        keyenc = AES(userkey)
        decryptedkey = keyenc.decrypt(self.key)
        # The decrypted page key decrypts the content
        pageenc = AES(decryptedkey)
        return self.__removeaespadding(pageenc.decrypt(contents))

    def check (self, contents):
        """
        If the contents uses some known MIME types, check if it
        conforms to the type. Throw a ValueError exception if not.
        If the contents uses an uncheckable MIME type, don't check
        it and don't throw an exception.
        Returns True if the content was checked, False if it was not
        checked."""
        if self.mimetype == 'application/xhtml+xml':
            if contents[:5]=="<?xml":
                return True
            else:
                print "Bad XML: ",contents[:5]
                raise ValueError
        if self.mimetype == 'image/jpeg':
            if contents[:3] == '\xff\xd8\xff':
                return True
            else:
                print "Bad JPEG: ", contents[:3].encode('hex')
                raise ValueError()
        return False

    def __removeaespadding (self, contents):
        """
        Remove the trailing padding, using what appears to be the CMS
        algorithm from RFC 5652 6.3"""
        lastchar = binascii.b2a_hex(contents[-1:])
        strlen = int(lastchar, 16)
        padding = strlen
        if strlen == 1:
            return contents[:-1]
        if strlen < 16:
            for i in range(strlen):
                testchar = binascii.b2a_hex(contents[-strlen:-(strlen-1)])
                if testchar != lastchar:
                    padding = 0
        if padding > 0:
            contents = contents[:-padding]
        return contents

if __name__ == '__main__':

    lib = KoboLibrary()

    for i, book in enumerate(lib.books):
        print ('%d: %s' % (i + 1, book.title)).encode('ascii', 'ignore')

    num_string = raw_input("Convert book number... ")
    try:
        num = int(num_string)
        book = lib.books[num - 1]
    except (ValueError, IndexError):
        exit()

    print "Converting", book.title

    zin = zipfile.ZipFile(book.filename, "r")
    # make filename out of Unicode alphanumeric and whitespace equivalents from title
    outname = "%s.epub" % (re.sub('[^\s\w]', '', book.title, 0, re.UNICODE))

    if (book.type == 'drm-free'):
        print "DRM-free book, conversion is not needed"
        shutil.copyfile(book.filename, outname)
        print "Book saved as", os.path.join(os.getcwd(), outname)
        exit(0)

    result = 1
    for userkey in lib.userkeys:
        # print "Trying key: ",userkey.encode('hex_codec')
        confirmedGood = False
        try:
            zout = zipfile.ZipFile(outname, "w", zipfile.ZIP_DEFLATED)
            for filename in zin.namelist():
                contents = zin.read(filename)
                if filename in book.encryptedfiles:
                    file = book.encryptedfiles[filename]
                    contents = file.decrypt(userkey, contents)
                    # Parse failures mean the key is probably wrong.
                    if not confirmedGood:
                        confirmedGood = file.check(contents)
                zout.writestr(filename, contents)
            zout.close()
            print "Book saved as", os.path.join(os.getcwd(), outname)
            result = 0
            break
        except ValueError:
            print "Decryption failed, trying next key"
            zout.close()
            os.remove(outname)

    zin.close()
    lib.close()
    exit(result)
