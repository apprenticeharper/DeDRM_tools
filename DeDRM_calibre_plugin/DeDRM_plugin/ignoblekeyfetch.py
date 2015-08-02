#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement

# ignoblekeyfetch.pyw, version 1.1
# Copyright © 2015 Apprentice Harper

# Released under the terms of the GNU General Public Licence, version 3
# <http://www.gnu.org/licenses/>

# Based on discoveries by "Nobody You Know"
# Code partly based on ignoblekeygen.py by several people.

# Windows users: Before running this program, you must first install Python.
#   We recommend ActiveState Python 2.7.X for Windows from
#   http://www.activestate.com/activepython/downloads.
#   Then save this script file as ignoblekeyfetch.pyw and double-click on it to run it.
#
# Mac OS X users: Save this script file as ignoblekeyfetch.pyw.  You can run this
#   program from the command line (python ignoblekeyfetch.pyw) or by double-clicking
#   it when it has been associated with PythonLauncher.

# Revision history:
#   1.0 - Initial  version
#   1.1 - Try second URL if first one fails

"""
Fetch Barnes & Noble EPUB user key from B&N servers using email and password
"""

__license__ = 'GPL v3'
__version__ = "1.1"

import sys
import os

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

try:
    from calibre.constants import iswindows, isosx
except:
    iswindows = sys.platform.startswith('win')
    isosx = sys.platform.startswith('darwin')

def unicode_argv():
    if iswindows:
        # Uses shell32.GetCommandLineArgvW to get sys.argv as a list of Unicode
        # strings.

        # Versions 2.x of Python don't support Unicode in sys.argv on
        # Windows, with the underlying Windows API instead replacing multi-byte
        # characters with '?'.  So use shell32.GetCommandLineArgvW to get sys.argv
        # as a list of Unicode strings and encode them as utf-8

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
        return [u"ignoblekeyfetch.py"]
    else:
        argvencoding = sys.stdin.encoding
        if argvencoding == None:
            argvencoding = "utf-8"
        return [arg if (type(arg) == unicode) else unicode(arg,argvencoding) for arg in sys.argv]


class IGNOBLEError(Exception):
    pass

def fetch_key(email, password):
    # change email and password to utf-8 if unicode
    if type(email)==unicode:
        email = email.encode('utf-8')
    if type(password)==unicode:
        password = password.encode('utf-8')

    import random
    random = "%030x" % random.randrange(16**30)

    import urllib, urllib2, re

    # try the URL from nook for PC
    fetch_url = "https://cart4.barnesandnoble.com/services/service.aspx?Version=2&acctPassword="
    fetch_url += urllib.quote(password,'')+"&devID=PC_BN_2.5.6.9575_"+random+"&emailAddress="
    fetch_url += urllib.quote(email,"")+"&outFormat=5&schema=1&service=1&stage=deviceHashB"
    #print fetch_url

    found = ''
    try:
        req = urllib2.Request(fetch_url)
        response = urllib2.urlopen(req)
        the_page = response.read()
        #print the_page
        found = re.search('ccHash>(.+?)</ccHash', the_page).group(1)
    except:
        found = ''
    if len(found)!=28:
        # try the URL from android devices
        fetch_url = "https://cart4.barnesandnoble.com/services/service.aspx?Version=2&acctPassword="
        fetch_url += urllib.quote(password,'')+"&devID=hobbes_9.3.50818_"+random+"&emailAddress="
        fetch_url += urllib.quote(email,"")+"&outFormat=5&schema=1&service=1&stage=deviceHashB"
        #print fetch_url

        found = ''
        try:
            req = urllib2.Request(fetch_url)
            response = urllib2.urlopen(req)
            the_page = response.read()
            #print the_page
            found = re.search('ccHash>(.+?)</ccHash', the_page).group(1)
        except:
            found = ''

    return found




def cli_main():
    sys.stdout=SafeUnbuffered(sys.stdout)
    sys.stderr=SafeUnbuffered(sys.stderr)
    argv=unicode_argv()
    progname = os.path.basename(argv[0])
    if len(argv) != 4:
        print u"usage: {0} <email> <password> <keyfileout.b64>".format(progname)
        return 1
    email, password, keypath = argv[1:]
    userkey = fetch_key(email, password)
    if len(userkey) == 28:
        open(keypath,'wb').write(userkey)
        return 0
    print u"Failed to fetch key."
    return 1


def gui_main():
    try:
        import Tkinter
        import tkFileDialog
        import Tkconstants
        import tkMessageBox
        import traceback
    except:
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
            Tkinter.Label(body, text=u"Account email address").grid(row=0)
            self.name = Tkinter.Entry(body, width=40)
            self.name.grid(row=0, column=1, sticky=sticky)
            Tkinter.Label(body, text=u"Account password").grid(row=1)
            self.ccn = Tkinter.Entry(body, width=40)
            self.ccn.grid(row=1, column=1, sticky=sticky)
            Tkinter.Label(body, text=u"Output file").grid(row=2)
            self.keypath = Tkinter.Entry(body, width=40)
            self.keypath.grid(row=2, column=1, sticky=sticky)
            self.keypath.insert(2, u"bnepubkey.b64")
            button = Tkinter.Button(body, text=u"...", command=self.get_keypath)
            button.grid(row=2, column=2)
            buttons = Tkinter.Frame(self)
            buttons.pack()
            botton = Tkinter.Button(
                buttons, text=u"Fetch", width=10, command=self.generate)
            botton.pack(side=Tkconstants.LEFT)
            Tkinter.Frame(buttons, width=10).pack(side=Tkconstants.LEFT)
            button = Tkinter.Button(
                buttons, text=u"Quit", width=10, command=self.quit)
            button.pack(side=Tkconstants.RIGHT)

        def get_keypath(self):
            keypath = tkFileDialog.asksaveasfilename(
                parent=None, title=u"Select B&N ePub key file to produce",
                defaultextension=u".b64",
                filetypes=[('base64-encoded files', '.b64'),
                           ('All Files', '.*')])
            if keypath:
                keypath = os.path.normpath(keypath)
                self.keypath.delete(0, Tkconstants.END)
                self.keypath.insert(0, keypath)
            return

        def generate(self):
            email = self.name.get()
            password = self.ccn.get()
            keypath = self.keypath.get()
            if not email:
                self.status['text'] = u"Email address not given"
                return
            if not password:
                self.status['text'] = u"Account password not given"
                return
            if not keypath:
                self.status['text'] = u"Output keyfile path not set"
                return
            self.status['text'] = u"Fetching..."
            try:
                userkey = fetch_key(email, password)
            except Exception, e:
                self.status['text'] = u"Error: {0}".format(e.args[0])
                return
            if len(userkey) == 28:
                open(keypath,'wb').write(userkey)
                self.status['text'] = u"Keyfile fetched successfully"
            else:
                self.status['text'] = u"Keyfile fetch failed."

    root = Tkinter.Tk()
    root.title(u"Barnes & Noble ePub Keyfile Fetch v.{0}".format(__version__))
    root.resizable(True, False)
    root.minsize(300, 0)
    DecryptionDialog(root).pack(fill=Tkconstants.X, expand=1)
    root.mainloop()
    return 0

if __name__ == '__main__':
    if len(sys.argv) > 1:
        sys.exit(cli_main())
    sys.exit(gui_main())
