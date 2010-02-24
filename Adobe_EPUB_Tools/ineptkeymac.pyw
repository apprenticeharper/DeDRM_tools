#! /usr/bin/env python

# ineptkeymac.py, version 1

# This program runs on Mac OS X, version 10.6.2 and probably several other
# versions. It uses Python 2.6, but it probably also runs on all versions
# 2.x with x >= 5.

# This program extracts the private RSA key for your ADE account in a
# standard binary form (DER format) in a file of your choosing. Its purpose
# is to make a backup of that key so that your legally bought ADE encoded
# ebooks can be salvaged in case they would no longer be supported by ADE
# software. No other usages are intended. 

# It has been tested with the key storage structure of ADE 1.7.1 and 1.7.2
# and Sony Reader Library.

# This software does not contain any encryption code. Its only use of
# external encryption software is the use of openssl for the conversion of
# the private key from pem to der format. It doesn't use encryption or
# decryption, however.

# You can run this program from the command line (python ineptkeymac.py
# filename), or by doubleclicking when it has been associated with
# Pythonlauncher. When no filename is given it will show a dialog to obtain one.

from __future__ import with_statement

__license__ = 'GPL v3'

import sys
import os
import xml.etree.ElementTree as etree
from contextlib import closing
import Tkinter
import Tkconstants
import tkFileDialog
from tkMessageBox import showerror
from subprocess import Popen, PIPE
import textwrap

NS = 'http://ns.adobe.com/adept'
ACTFILE = '~/Library/Application Support/Adobe/Digital Editions/activation.dat'
HEADER = '-----BEGIN PRIVATE KEY-----\n'
FOOTER = '\n-----END PRIVATE KEY-----\n'

Gui = False

def get_key():
    '''Returns the private key as a binary string (DER format)'''
    try:
        filename = os.path.expanduser(ACTFILE)
        tree = etree.parse(filename)
        xpath = '//{%s}credentials/{%s}privateLicenseKey' % (NS, NS)
        b64key = tree.findtext(xpath)
        pemkey = HEADER + textwrap.fill(b64key, 64) + FOOTER
        
        cmd = ['openssl', 'rsa', '-outform', 'der']
        proc = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate(pemkey)

        if proc.returncode != 0:
            error("openssl error: " + stderr)
            return None
        return stdout
            
    except IOError:
        error("Can find keyfile. Maybe you should activate your Adobe ID.")
        sys.exit(1)
        
def store_key(key, keypath):
    '''Store the key in the file given as keypath. If no keypath is given a
    dialog will ask for one.'''
    
    try:
        if keypath is None:
            keypath = get_keypath()
            if not keypath: # Cancelled
                return
            
        with closing(open(keypath, 'wb')) as outf:
            outf.write(key)
            
    except IOError, e:
        error("Can write keyfile: " + str(e))

def get_keypath():
    keypath = tkFileDialog.asksaveasfilename(
        parent = None, title = 'Select file to store ADEPT key',
        initialdir = os.path.expanduser('~/Desktop'),
        initialfile = 'adeptkey.der',
        defaultextension = '.der', filetypes = [('DER-encoded files', '.der'),
                                                ('All Files', '.*')])
    if keypath:
        keypath = os.path.normpath(keypath)
    return keypath

def error(text):
    print text
    if Gui: showerror('Error!', text)
    
def gui_main():
    root = Tkinter.Tk()
    root.iconify() 
    global Gui
    Gui = True
    store_key(get_key(), None)

    return 0
    
def main(argv=sys.argv):
    progname = os.path.basename(argv[0])
    
    if len(argv) == 1: # assume GUI if no argument given
        return gui_main()
    if len(argv) != 2:
        print "usage: %s KEYFILE" % (progname,)
        return 1
    
    store_key(get_key(), argv[1])

if __name__ == '__main__':
    sys.exit(main())
