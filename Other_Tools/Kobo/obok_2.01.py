#!/usr/bin/env python
#
# Updated September 2013 by Anon
# Version 2.01
# Incorporated minor fixes posted at Apprentice Alf's.
#
# Updates July 2012 by Michael Newton
# PWSD ID is no longer a MAC address, but should always
# be stored in the registry. Script now works with OS X
# and checks plist for values instead of registry. Must
# have biplist installed for OS X support.
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
"""
Decrypt Kobo encrypted EPUB books.
"""

import os
import sys
if sys.platform.startswith('win'):
    import _winreg
elif sys.platform.startswith('darwin'):
    from biplist import readPlist
import re
import string
import hashlib
import sqlite3
import base64
import binascii
import zipfile
from Crypto.Cipher import AES

def SHA256(raw):
    return hashlib.sha256(raw).hexdigest()

def RemoveAESPadding(contents):
    lastchar = binascii.b2a_hex(contents[-1:])
    strlen = int(lastchar, 16)
    padding = strlen
    if(strlen == 1):
        return contents[:-1]
    if(strlen < 16):
        for i in range(strlen):
            testchar = binascii.b2a_hex(contents[-strlen:-(strlen-1)])
            if(testchar != lastchar):
                padding = 0
    if(padding > 0):
        contents = contents[:-padding]
    return contents

def GetVolumeKeys(dbase, enc):
    volumekeys = {}
    for row in dbase.execute("SELECT * from content_keys"):
        if(row[0] not in volumekeys):
            volumekeys[row[0]] = {}
        volumekeys[row[0]][row[1]] = {}
        volumekeys[row[0]][row[1]]["encryptedkey"] = base64.b64decode(row[2])
        volumekeys[row[0]][row[1]]["decryptedkey"] = enc.decrypt(volumekeys[row[0]][row[1]]["encryptedkey"])
    # get book name
    for key in volumekeys.keys():
        volumekeys[key]["title"] = dbase.execute("SELECT Title from content where ContentID = '%s'" % (key)).fetchone()[0]
    return volumekeys

def ByteArrayToString(bytearr):
    wincheck = re.match("@ByteArray\\((.+)\\)", bytearr)
    if wincheck:
        return wincheck.group(1)
    return bytearr

def GetUserHexKey(prefs = ""):
    "find wsuid and pwsdid"
    wsuid = ""
    pwsdid = ""
    if sys.platform.startswith('win'):
        regkey_browser = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, "Software\\Kobo\\Kobo Desktop Edition\\Browser")
        cookies = _winreg.QueryValueEx(regkey_browser, "cookies")
        bytearrays = cookies[0]
    elif sys.platform.startswith('darwin'):
        cookies = readPlist(prefs)
        bytearrays = cookies["Browser.cookies"]
    for bytearr in bytearrays:
        cookie = ByteArrayToString(bytearr)
        print cookie
        wsuidcheck = re.match("^wsuid=([0-9a-f-]+)", cookie)
        if(wsuidcheck):
            wsuid = wsuidcheck.group(1)
        pwsdidcheck = re.match("^pwsdid=([0-9a-f-]+)", cookie)
        if (pwsdidcheck):
            pwsdid = pwsdidcheck.group(1)

    if(wsuid == "" or pwsdid == ""):
        print "wsuid or pwsdid key not found :/"
        exit()
    preuserkey = string.join((pwsdid, wsuid), "")
    print SHA256(pwsdid)
    userkey = SHA256(preuserkey)
    return userkey[32:]

# get dirs
if sys.platform.startswith('win'):
    delim = "\\"
    if (sys.getwindowsversion().major > 5):
        kobodir = string.join((os.environ['LOCALAPPDATA'], "Kobo\\Kobo Desktop Edition"), delim)
    else:
        kobodir = string.join((os.environ['USERPROFILE'], "Local Settings\\Application Data\\Kobo\\Kobo Desktop Edition"), delim)
    prefs = ""
elif sys.platform.startswith('darwin'):
    delim = "/"
    kobodir = string.join((os.environ['HOME'], "Library/Application Support/Kobo/Kobo Desktop Edition"), delim)
    prefs = string.join((os.environ['HOME'], "Library/Preferences/com.kobo.Kobo Desktop Edition.plist"), delim)
sqlitefile = string.join((kobodir, "Kobo.sqlite"), delim)
bookdir = string.join((kobodir, "kepub"), delim)

# get key
userkeyhex = GetUserHexKey(prefs)
# load into AES
userkey = binascii.a2b_hex(userkeyhex)
enc = AES.new(userkey, AES.MODE_ECB)

# open sqlite
conn = sqlite3.connect(sqlitefile)
dbcursor = conn.cursor()
# get volume keys
volumekeys = GetVolumeKeys(dbcursor, enc)

# choose a volumeID

volumeid = ""
print "Choose a book to decrypt:"
i = 1
for key in volumekeys.keys():
    print "%d: %s" % (i, volumekeys[key]["title"])
    i += 1

num = input("...")

i = 1
for key in volumekeys.keys():
    if(i == num):
        volumeid = key
    i += 1

if(volumeid == ""):
    exit()

zippath = string.join((bookdir, volumeid), delim)

z = zipfile.ZipFile(zippath, "r")
# make filename out of Unicode alphanumeric and whitespace equivalents from title
outname = "%s.epub" % (re.sub("[^\s\w]", "", volumekeys[volumeid]["title"], 0, re.UNICODE))
zout = zipfile.ZipFile(outname, "w", zipfile.ZIP_DEFLATED)
for filename in z.namelist():
    #print filename
    # read in and decrypt
    if(filename in volumekeys[volumeid]):
        # do decrypted version
        pagekey = volumekeys[volumeid][filename]["decryptedkey"]
        penc = AES.new(pagekey, AES.MODE_ECB)
        contents = RemoveAESPadding(penc.decrypt(z.read(filename)))
        # need to fix padding
        zout.writestr(filename, contents)
    else:
        zout.writestr(filename, z.read(filename))

print "Book saved as %s%s%s" % (os.getcwd(), delim, outname)