#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ignoblekeyfetch.py
# Copyright © 2015-2020 Apprentice Harper et al.

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
#   2.0 - Python 3 for calibre 5.0

"""
Fetch Barnes & Noble EPUB user key from B&N servers using email and password
"""

__license__ = 'GPL v3'
__version__ = "2.0"

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
        if isinstance(data,bytes):
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
                    range(start, argc.value)]
        # if we don't have any arguments at all, just pass back script name
        # this should never happen
        return ["ignoblekeyfetch.py"]
    else:
        argvencoding = sys.stdin.encoding or "utf-8"
        return [arg if isinstance(arg, str) else str(arg, argvencoding) for arg in sys.argv]


class IGNOBLEError(Exception):
    pass

def fetch_key(email, password):
    # change email and password to utf-8 if unicode
    if type(email)==bytes:
        email = email.encode('utf-8')
    if type(password)==bytes:
        password = password.encode('utf-8')

    import random
    random = "%030x" % random.randrange(16**30)

    import urllib.parse, urllib.request, re

    # try the URL from nook for PC
    fetch_url = "https://cart4.barnesandnoble.com/services/service.aspx?Version=2&acctPassword="
    fetch_url += urllib.parse.quote(password,'')+"&devID=PC_BN_2.5.6.9575_"+random+"&emailAddress="
    fetch_url += urllib.parse.quote(email,"")+"&outFormat=5&schema=1&service=1&stage=deviceHashB"
    #print(fetch_url)

    found = ''
    try:
        response = urllib.request.urlopen(fetch_url)
        the_page = response.read()
        #print(the_page)
        found = re.search('ccHash>(.+?)</ccHash', the_page).group(1)
    except:
        found = ''
    if len(found)!=28:
        # try the URL from android devices
        fetch_url = "https://cart4.barnesandnoble.com/services/service.aspx?Version=2&acctPassword="
        fetch_url += urllib.parse.quote(password,'')+"&devID=hobbes_9.3.50818_"+random+"&emailAddress="
        fetch_url += urllib.parse.quote(email,"")+"&outFormat=5&schema=1&service=1&stage=deviceHashB"
        #print(fetch_url)

        found = ''
        try:
            response = urllib.request.urlopen(fetch_url)
            the_page = response.read()
            #print(the_page)
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
        print("usage: {0} <email> <password> <keyfileout.b64>".format(progname))
        return 1
    email, password, keypath = argv[1:]
    userkey = fetch_key(email, password)
    if len(userkey) == 28:
        open(keypath,'wb').write(userkey)
        return 0
    print("Failed to fetch key.")
    return 1


def gui_main():
    try:
        import tkinter
        import tkinter.filedialog
        import tkinter.constants
        import tkinter.messagebox
        import traceback
    except:
        return cli_main()

    class DecryptionDialog(tkinter.Frame):
        def __init__(self, root):
            tkinter.Frame.__init__(self, root, border=5)
            self.status = tkinter.Label(self, text="Enter parameters")
            self.status.pack(fill=tkinter.constants.X, expand=1)
            body = tkinter.Frame(self)
            body.pack(fill=tkinter.constants.X, expand=1)
            sticky = tkinter.constants.E + tkinter.constants.W
            body.grid_columnconfigure(1, weight=2)
            tkinter.Label(body, text="Account email address").grid(row=0)
            self.name = tkinter.Entry(body, width=40)
            self.name.grid(row=0, column=1, sticky=sticky)
            tkinter.Label(body, text="Account password").grid(row=1)
            self.ccn = tkinter.Entry(body, width=40)
            self.ccn.grid(row=1, column=1, sticky=sticky)
            tkinter.Label(body, text="Output file").grid(row=2)
            self.keypath = tkinter.Entry(body, width=40)
            self.keypath.grid(row=2, column=1, sticky=sticky)
            self.keypath.insert(2, "bnepubkey.b64")
            button = tkinter.Button(body, text="...", command=self.get_keypath)
            button.grid(row=2, column=2)
            buttons = tkinter.Frame(self)
            buttons.pack()
            botton = tkinter.Button(
                buttons, text="Fetch", width=10, command=self.generate)
            botton.pack(side=tkinter.constants.LEFT)
            tkinter.Frame(buttons, width=10).pack(side=tkinter.constants.LEFT)
            button = tkinter.Button(
                buttons, text="Quit", width=10, command=self.quit)
            button.pack(side=tkinter.constants.RIGHT)

        def get_keypath(self):
            keypath = tkinter.filedialog.asksaveasfilename(
                parent=None, title="Select B&N ePub key file to produce",
                defaultextension=".b64",
                filetypes=[('base64-encoded files', '.b64'),
                           ('All Files', '.*')])
            if keypath:
                keypath = os.path.normpath(keypath)
                self.keypath.delete(0, tkinter.constants.END)
                self.keypath.insert(0, keypath)
            return

        def generate(self):
            email = self.name.get()
            password = self.ccn.get()
            keypath = self.keypath.get()
            if not email:
                self.status['text'] = "Email address not given"
                return
            if not password:
                self.status['text'] = "Account password not given"
                return
            if not keypath:
                self.status['text'] = "Output keyfile path not set"
                return
            self.status['text'] = "Fetching..."
            try:
                userkey = fetch_key(email, password)
            except Exception as e:
                self.status['text'] = "Error: {0}".format(e.args[0])
                return
            if len(userkey) == 28:
                open(keypath,'wb').write(userkey)
                self.status['text'] = "Keyfile fetched successfully"
            else:
                self.status['text'] = "Keyfile fetch failed."

    root = tkinter.Tk()
    root.title("Barnes & Noble ePub Keyfile Fetch v.{0}".format(__version__))
    root.resizable(True, False)
    root.minsize(300, 0)
    DecryptionDialog(root).pack(fill=tkinter.constants.X, expand=1)
    root.mainloop()
    return 0

if __name__ == '__main__':
    if len(sys.argv) > 1:
        sys.exit(cli_main())
    sys.exit(gui_main())
