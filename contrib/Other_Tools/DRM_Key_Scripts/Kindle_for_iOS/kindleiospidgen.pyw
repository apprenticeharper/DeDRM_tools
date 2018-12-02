#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement

# kindleforios4key.py
# Copyright © 2013 by Apprentice Alf
# Portions Copyright © 2007, 2009 Igor Skochinsky <skochinsky@mail.ru>

# Revision history:
#  1.0   - Generates fixed PID for Kindle for iOS 3.1.1 running on iOS 4.x


"""
Generate fixed PID for Kindle for iOS 3.1.1
"""

__license__ = 'GPL v3'
__version__ = '1.0'

import sys, os
import getopt
import binascii

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

import hashlib

def SHA256(message):
    ctx = hashlib.sha256()
    ctx.update(message)
    return ctx.digest()

def crc32(s):
    return (~binascii.crc32(s,-1))&0xFFFFFFFF

letters = 'ABCDEFGHIJKLMNPQRSTUVWXYZ123456789'

def checksumPid(s):
    crc = crc32(s)
    crc = crc ^ (crc >> 16)
    res = s
    l = len(letters)
    for i in (0,1):
        b = crc & 0xff
        pos = (b // l) ^ (b % l)
        res += letters[pos%l]
        crc >>= 8

    return res

def pidFromSerial(s, l):
    crc = crc32(s)

    arr1 = [0]*l
    for i in xrange(len(s)):
        arr1[i%l] ^= ord(s[i])

    crc_bytes = [crc >> 24 & 0xff, crc >> 16 & 0xff, crc >> 8 & 0xff, crc & 0xff]
    for i in xrange(l):
        arr1[i] ^= crc_bytes[i&3]

    pid = ''
    for i in xrange(l):
        b = arr1[i] & 0xff
        pid+=letters[(b >> 7) + ((b >> 5 & 3) ^ (b & 0x1f))]

    return pid

def generatekeys(email, mac):
    keys = []
    email = email.encode('utf-8').lower()
    mac = mac.encode('utf-8').lower()
    cleanmac = "".join(c if (c in "0123456789abcdef") else "" for c in mac)
    lowermac = cleanmac.lower()
    #print lowermac
    keyseed = lowermac + email.encode('utf-8')
    #print keyseed
    keysha256 = SHA256(keyseed)
    keybase64 = keysha256.encode('base64')
    #print keybase64
    cleankeybase64 = "".join(c if (c in "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ") else "0" for c in keybase64)
    #print cleankeybase64
    pseudoudid = cleankeybase64[:40]
    #print pseudoudid
    keys.append(pidFromSerial(pseudoudid.encode("utf-8"),8))
    return keys

# interface for Python DeDRM
# returns single key or multiple keys, depending on path or file passed in
def getkey(email, mac, outpath):
    keys = generatekeys(email,mac)
    if len(keys) > 0:
        if not os.path.isdir(outpath):
            outfile = outpath
            with file(outfile, 'w') as keyfileout:
                keyfileout.write(keys[0])
            print u"Saved a key to {0}".format(outfile)
        else:
            keycount = 0
            for key in keys:
                while True:
                    keycount += 1
                    outfile = os.path.join(outpath,u"kindleios{0:d}.pid".format(keycount))
                    if not os.path.exists(outfile):
                        break
                with file(outfile, 'w') as keyfileout:
                    keyfileout.write(key)
                print u"Saved a key to {0}".format(outfile)
        return True
    return False

def usage(progname):
    print u"Generates the key for Kindle for iOS 3.1.1"
    print u"Requires email address of Amazon acccount"
    print u"And MAC address for iOS device’s wifi"
    print u"Outputs to a file or to stdout"
    print u"Usage:"
    print u"    {0:s} [-h] <email address> <MAC address> [<outfile>]".format(progname)


def cli_main():
    sys.stdout=SafeUnbuffered(sys.stdout)
    sys.stderr=SafeUnbuffered(sys.stderr)
    argv=unicode_argv()
    progname = os.path.basename(argv[0])
    print u"{0} v{1}\nCopyright © 2013 Apprentice Alf".format(progname,__version__)

    try:
        opts, args = getopt.getopt(argv[1:], "h")
    except getopt.GetoptError, err:
        print u"Error in options or arguments: {0}".format(err.args[0])
        usage(progname)
        sys.exit(2)

    for o, a in opts:
        if o == "-h":
            usage(progname)
            sys.exit(0)


    if len(args) < 2 or len(args) > 3:
        usage(progname)
        sys.exit(2)

    if len(args) == 3:
        # save to the specified file or folder
        getkey(args[0],args[1],args[2])
    else:
        keys = generatekeys(args[0],args[1])
        for key in keys:
            print key

    return 0


def gui_main():
    try:
        import Tkinter
        import Tkconstants
        import tkMessageBox
    except:
        print "Tkinter not installed"
        return cli_main()

    class DecryptionDialog(Tkinter.Frame):
        def __init__(self, root):
            Tkinter.Frame.__init__(self, root, border=5)
            self.status = Tkinter.Label(self, text=u"Enter parameters")
            self.status.pack(fill=Tkconstants.X, expand=1)
            body = Tkinter.Frame(self)
            body.pack(fill=Tkconstants.X, expand=1)
            sticky = Tkconstants.E + Tkconstants.W
            body.grid_columnconfigure(1, weight=2)
            Tkinter.Label(body, text=u"Amazon email address").grid(row=0)
            self.email = Tkinter.Entry(body, width=40)
            self.email.grid(row=0, column=1, sticky=sticky)
            Tkinter.Label(body, text=u"iOS  MAC address").grid(row=1)
            self.mac = Tkinter.Entry(body, width=40)
            self.mac.grid(row=1, column=1, sticky=sticky)
            buttons = Tkinter.Frame(self)
            buttons.pack()
            button = Tkinter.Button(
                buttons, text=u"Generate", width=10, command=self.generate)
            button.pack(side=Tkconstants.LEFT)
            Tkinter.Frame(buttons, width=10).pack(side=Tkconstants.LEFT)
            button = Tkinter.Button(
                buttons, text=u"Quit", width=10, command=self.quit)
            button.pack(side=Tkconstants.RIGHT)

        def generate(self):
            email = self.email.get()
            mac = self.mac.get()
            if not email:
                self.status['text'] = u"Email not specified"
                return
            if not mac:
                self.status['text'] = u"MAC not specified"
                return
            self.status['text'] = u"Generating..."
            try:
                keys = generatekeys(email, mac)
            except Exception, e:
                self.status['text'] = u"Error: (0}".format(e.args[0])
                return
            self.status['text'] = ", ".join(key for key in keys)

    root = Tkinter.Tk()
    root.title(u"Kindle for iOS PID Generator v.{0}".format(__version__))
    root.resizable(True, False)
    root.minsize(300, 0)
    DecryptionDialog(root).pack(fill=Tkconstants.X, expand=1)
    root.mainloop()
    return 0

if __name__ == '__main__':
    if len(sys.argv) > 1:
        sys.exit(cli_main())
    sys.exit(gui_main())
