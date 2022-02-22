#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ignoblekeyGenPassHash.py
# Copyright © 2009-2022 i♥cabbages, Apprentice Harper et al.

# Released under the terms of the GNU General Public Licence, version 3
# <http://www.gnu.org/licenses/>

# Windows users: Before running this program, you must first install Python.
#   We recommend ActiveState Python 2.7.X for Windows (x86) from
#   http://www.activestate.com/activepython/downloads.
#   You must also install PyCrypto from
#   http://www.voidspace.org.uk/python/modules.shtml#pycrypto
#   (make certain to install the version for Python 2.7).
#   Then save this script file as ignoblekeygen.pyw and double-click on it to run it.
#
# Mac OS X users: Save this script file as ignoblekeygen.pyw.  You can run this
#   program from the command line (python ignoblekeygen.pyw) or by double-clicking
#   it when it has been associated with PythonLauncher.

# Revision history:
#   1 - Initial release
#   2 - Add OS X support by using OpenSSL when available (taken/modified from ineptepub v5)
#   2.1 - Allow Windows versions of libcrypto to be found
#   2.2 - On Windows try PyCrypto first and then OpenSSL next
#   2.3 - Modify interface to allow use of import
#   2.4 - Improvements to UI and now works in plugins
#   2.5 - Additional improvement for unicode and plugin support
#   2.6 - moved unicode_argv call inside main for Windows DeDRM compatibility
#   2.7 - Work if TkInter is missing
#   2.8 - Fix bug in stand-alone use (import tkFileDialog)
#   3.0 - Added Python 3 compatibility for calibre 5.0
#   3.1 - Remove OpenSSL support, only PyCryptodome is supported now

"""
Generate Barnes & Noble EPUB user key from name and credit card number.
"""

__license__ = 'GPL v3'
__version__ = "3.1"

import sys
import os
import hashlib
import base64

try:
    from Cryptodome.Cipher import AES
except ImportError:
    from Crypto.Cipher import AES

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
        if isinstance(data,str) or isinstance(data,unicode):
            # str for Python3, unicode for Python2
            data = data.encode(self.encoding,"replace")
        try:
            buffer = getattr(self.stream, 'buffer', self.stream)
            # self.stream.buffer for Python3, self.stream for Python2
            buffer.write(data)
            buffer.flush()
        except:
            # We can do nothing if a write fails
            raise
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
        return ["ignoblekeygen.py"]
    else:
        argvencoding = sys.stdin.encoding or "utf-8"
        return [arg if (isinstance(arg, str) or isinstance(arg,unicode)) else str(arg, argvencoding) for arg in sys.argv]


class IGNOBLEError(Exception):
    pass

def normalize_name(name):
    return ''.join(x for x in name.lower() if x != ' ')


def generate_key(name, ccn):
    # remove spaces and case from name and CC numbers.
    name = normalize_name(name)
    ccn = normalize_name(ccn)

    if type(name)==str:
        name = name.encode('utf-8')
    if type(ccn)==str:
        ccn = ccn.encode('utf-8')

    name = name + b'\x00'
    ccn = ccn + b'\x00'

    name_sha = hashlib.sha1(name).digest()[:16]
    ccn_sha = hashlib.sha1(ccn).digest()[:16]
    both_sha = hashlib.sha1(name + ccn).digest()
    crypt = AES.new(ccn_sha, AES.MODE_CBC, name_sha).encrypt(both_sha + (b'\x0c' * 0x0c))
    userkey = hashlib.sha1(crypt).digest()
    return base64.b64encode(userkey)


def cli_main():
    sys.stdout=SafeUnbuffered(sys.stdout)
    sys.stderr=SafeUnbuffered(sys.stderr)
    argv=unicode_argv()
    progname = os.path.basename(argv[0])
    if len(argv) != 4:
        print("usage: {0} <Name> <CC#> <keyfileout.b64>".format(progname))
        return 1
    name, ccn, keypath = argv[1:]
    userkey = generate_key(name, ccn)
    open(keypath,'wb').write(userkey)
    return 0


def gui_main():
    try:
        import tkinter
        import tkinter.constants
        import tkinter.messagebox
        import tkinter.filedialog
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
            tkinter.Label(body, text="Account Name").grid(row=0)
            self.name = tkinter.Entry(body, width=40)
            self.name.grid(row=0, column=1, sticky=sticky)
            tkinter.Label(body, text="CC#").grid(row=1)
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
                buttons, text="Generate", width=10, command=self.generate)
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
            name = self.name.get()
            ccn = self.ccn.get()
            keypath = self.keypath.get()
            if not name:
                self.status['text'] = "Name not specified"
                return
            if not ccn:
                self.status['text'] = "Credit card number not specified"
                return
            if not keypath:
                self.status['text'] = "Output keyfile path not specified"
                return
            self.status['text'] = "Generating..."
            try:
                userkey = generate_key(name, ccn)
            except Exception as e:
                self.status['text'] = "Error: (0}".format(e.args[0])
                return
            open(keypath,'wb').write(userkey)
            self.status['text'] = "Keyfile successfully generated"

    root = tkinter.Tk()
    root.title("Barnes & Noble ePub Keyfile Generator v.{0}".format(__version__))
    root.resizable(True, False)
    root.minsize(300, 0)
    DecryptionDialog(root).pack(fill=tkinter.constants.X, expand=1)
    root.mainloop()
    return 0

if __name__ == '__main__':
    if len(sys.argv) > 1:
        sys.exit(cli_main())
    sys.exit(gui_main())
