#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

from __future__ import print_function
import sys
import os
import re
import ineptepub
import ignobleepub
import epubtest
import zipfix
import ineptpdf
import erdr2pml
import k4mobidedrm
import traceback

def decryptepub(infile, outdir, rscpath):
    errlog = ''

    # first fix the epub to make sure we do not get errors
    name, ext = os.path.splitext(os.path.basename(infile))
    bpath = os.path.dirname(infile)
    zippath = os.path.join(bpath,name + '_temp.zip')
    rv = zipfix.repairBook(infile, zippath)
    if rv != 0:
        print("Error while trying to fix epub")
        return rv

    # determine a good name for the output file
    outfile = os.path.join(outdir, name + '_nodrm.epub')

    rv = 1
    # first try with the Adobe adept epub
    if  ineptepub.adeptBook(zippath):
        # try with any keyfiles (*.der) in the rscpath
        files = os.listdir(rscpath)
        filefilter = re.compile("\.der$", re.IGNORECASE)
        files = filter(filefilter.search, files)
        if files:
            for filename in files:
                keypath = os.path.join(rscpath, filename)
                userkey = open(keypath,'rb').read()
                try:
                    rv = ineptepub.decryptBook(userkey, zippath, outfile)
                    if rv == 0:
                        print("Decrypted Adobe ePub with key file {0}".format(filename))
                        break
                except Exception, e:
                    errlog += traceback.format_exc()
                    errlog += str(e)
                    rv = 1
    # now try with ignoble epub
    elif  ignobleepub.ignobleBook(zippath):
        # try with any keyfiles (*.b64) in the rscpath
        files = os.listdir(rscpath)
        filefilter = re.compile("\.b64$", re.IGNORECASE)
        files = filter(filefilter.search, files)
        if files:
            for filename in files:
                keypath = os.path.join(rscpath, filename)
                userkey = open(keypath,'r').read()
                #print userkey
                try:
                    rv = ignobleepub.decryptBook(userkey, zippath, outfile)
                    if rv == 0:
                        print("Decrypted B&N ePub with key file {0}".format(filename))
                        break
                except Exception, e:
                    errlog += traceback.format_exc()
                    errlog += str(e)
                    rv = 1
    else:
        encryption = epubtest.encryption(zippath)
        if encryption == "Unencrypted":
            print("{0} is not DRMed.".format(name))
            rv = 0
        else:
            print("{0} has an unknown encryption.".format(name))

    os.remove(zippath)
    if rv != 0:
        print(errlog)
    return rv


def decryptpdf(infile, outdir, rscpath):
    errlog = ''
    rv = 1

    # determine a good name for the output file
    name, ext = os.path.splitext(os.path.basename(infile))
    outfile = os.path.join(outdir, name + '_nodrm.pdf')

    # try with any keyfiles (*.der) in the rscpath
    files = os.listdir(rscpath)
    filefilter = re.compile("\.der$", re.IGNORECASE)
    files = filter(filefilter.search, files)
    if files:
        for filename in files:
            keypath = os.path.join(rscpath, filename)
            userkey = open(keypath,'rb').read()
            try:
                rv = ineptpdf.decryptBook(userkey, infile, outfile)
                if rv == 0:
                    break
            except Exception, e:
                errlog += traceback.format_exc()
                errlog += str(e)
                rv = 1

    if rv != 0:
        print(errlog)
    return rv


def decryptpdb(infile, outdir, rscpath):
    errlog = ''
    outname = os.path.splitext(os.path.basename(infile))[0] + ".pmlz"
    outpath = os.path.join(outdir, outname)
    rv = 1
    socialpath = os.path.join(rscpath,'sdrmlist.txt')
    if os.path.exists(socialpath):
        keydata = file(socialpath,'r').read()
        keydata = keydata.rstrip(os.linesep)
        ar = keydata.split(',')
        for i in ar:
            try:
                name, cc8 = i.split(':')
            except ValueError:
                print('   Error parsing user supplied social drm data.')
                return 1
            try:
                rv = erdr2pml.decryptBook(infile, outpath, True, erdr2pml.getuser_key(name, cc8))
            except Exception, e:
                errlog += traceback.format_exc()
                errlog += str(e)
                rv = 1

            if rv == 0:
                break
    return rv


def decryptk4mobi(infile, outdir, rscpath):
    errlog = ''
    rv = 1
    pidnums = []
    pidspath = os.path.join(rscpath,'pidlist.txt')
    if os.path.exists(pidspath):
        pidstr = file(pidspath,'r').read()
        pidstr = pidstr.rstrip(os.linesep)
        pidstr = pidstr.strip()
        if pidstr != '':
            pidnums = pidstr.split(',')
    serialnums = []
    serialnumspath = os.path.join(rscpath,'seriallist.txt')
    if os.path.exists(serialnumspath):
        serialstr = file(serialnumspath,'r').read()
        serialstr = serialstr.rstrip(os.linesep)
        serialstr = serialstr.strip()
        if serialstr != '':
            serialnums = serialstr.split(',')
    kDatabaseFiles = []
    files = os.listdir(rscpath)
    filefilter = re.compile("\.k4i$", re.IGNORECASE)
    files = filter(filefilter.search, files)
    if files:
        for filename in files:
            dpath = os.path.join(rscpath,filename)
            kDatabaseFiles.append(dpath)
    androidFiles = []
    files = os.listdir(rscpath)
    filefilter = re.compile("\.ab$", re.IGNORECASE)
    files = filter(filefilter.search, files)
    if files:
        for filename in files:
            dpath = os.path.join(rscpath,filename)
            androidFiles.append(dpath)
    files = os.listdir(rscpath)
    filefilter = re.compile("\.db$", re.IGNORECASE)
    files = filter(filefilter.search, files)
    if files:
        for filename in files:
            dpath = os.path.join(rscpath,filename)
            androidFiles.append(dpath)
    files = os.listdir(rscpath)
    filefilter = re.compile("\.xml$", re.IGNORECASE)
    files = filter(filefilter.search, files)
    if files:
        for filename in files:
            dpath = os.path.join(rscpath,filename)
            androidFiles.append(dpath)
    try:
        rv = k4mobidedrm.decryptBook(infile, outdir, kDatabaseFiles, androidFiles, serialnums, pidnums)
    except Exception, e:
        errlog += traceback.format_exc()
        errlog += str(e)
        rv = 1

    return rv
