#!/usr/bin/env python
# -*- coding: utf-8 -*-


# ignoblekeygen.pyw, version 2.5
# Copyright © 2009-2010 i♥cabbages

# Released under the terms of the GNU General Public Licence, version 3
# <http://www.gnu.org/licenses/>

# Modified 2010–2013 by some_updates, DiapDealer and Apprentice Alf

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

"""
Generate Barnes & Noble EPUB user key from name and credit card number.
"""
from __future__ import print_function

__license__ = 'GPL v3'
__version__ = "2.8"

import sys
import os
import hashlib

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
        return [u"ignoblekeygen.py"]
    else:
        argvencoding = sys.stdin.encoding
        if argvencoding == None:
            argvencoding = "utf-8"
        return [arg if (type(arg) == unicode) else unicode(arg,argvencoding) for arg in sys.argv]


class IGNOBLEError(Exception):
    pass

def _load_crypto_libcrypto():
    from ctypes import CDLL, POINTER, c_void_p, c_char_p, c_int, c_long, \
        Structure, c_ulong, create_string_buffer, cast
    from ctypes.util import find_library

    if iswindows:
        libcrypto = find_library('libeay32')
    else:
        libcrypto = find_library('crypto')

    if libcrypto is None:
        raise IGNOBLEError('libcrypto not found')
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

    AES_set_encrypt_key = F(c_int, 'AES_set_encrypt_key',
                            [c_char_p, c_int, AES_KEY_p])
    AES_cbc_encrypt = F(None, 'AES_cbc_encrypt',
                        [c_char_p, c_char_p, c_ulong, AES_KEY_p, c_char_p,
                         c_int])

    class AES(object):
        def __init__(self, userkey, iv):
            self._blocksize = len(userkey)
            self._iv = iv
            key = self._key = AES_KEY()
            rv = AES_set_encrypt_key(userkey, len(userkey) * 8, key)
            if rv < 0:
                raise IGNOBLEError('Failed to initialize AES Encrypt key')

        def encrypt(self, data):
            out = create_string_buffer(len(data))
            rv = AES_cbc_encrypt(data, out, len(data), self._key, self._iv, 1)
            if rv == 0:
                raise IGNOBLEError('AES encryption failed')
            return out.raw

    return AES

def _load_crypto_pycrypto():
    from Crypto.Cipher import AES as _AES

    class AES(object):
        def __init__(self, key, iv):
            self._aes = _AES.new(key, _AES.MODE_CBC, iv)

        def encrypt(self, data):
            return self._aes.encrypt(data)

    return AES

def _load_crypto():
    AES = None
    cryptolist = (_load_crypto_libcrypto, _load_crypto_pycrypto)
    if sys.platform.startswith('win'):
        cryptolist = (_load_crypto_pycrypto, _load_crypto_libcrypto)
    for loader in cryptolist:
        try:
            AES = loader()
            break
        except (ImportError, IGNOBLEError):
            pass
    return AES

AES = _load_crypto()

def normalize_name(name):
    return ''.join(x for x in name.lower() if x != ' ')


def generate_key(name, ccn):
    # remove spaces and case from name and CC numbers.
    if type(name)==unicode:
        name = name.encode('utf-8')
    if type(ccn)==unicode:
        ccn = ccn.encode('utf-8')

    name = normalize_name(name) + '\x00'
    ccn = normalize_name(ccn) + '\x00'

    name_sha = hashlib.sha1(name).digest()[:16]
    ccn_sha = hashlib.sha1(ccn).digest()[:16]
    both_sha = hashlib.sha1(name + ccn).digest()
    aes = AES(ccn_sha, name_sha)
    crypt = aes.encrypt(both_sha + ('\x0c' * 0x0c))
    userkey = hashlib.sha1(crypt).digest()
    return userkey.encode('base64')




def cli_main():
    sys.stdout=SafeUnbuffered(sys.stdout)
    sys.stderr=SafeUnbuffered(sys.stderr)
    argv=unicode_argv()
    progname = os.path.basename(argv[0])
    if AES is None:
        print("%s: This script requires OpenSSL or PyCrypto, which must be installed " \
              "separately.  Read the top-of-script comment for details." % \
              (progname,))
        return 1
    if len(argv) != 4:
        print(u"usage: {0} <Name> <CC#> <keyfileout.b64>".format(progname))
        return 1
    name, ccn, keypath = argv[1:]
    userkey = generate_key(name, ccn)
    open(keypath,'wb').write(userkey)
    return 0


def gui_main():
    try:
        import Tkinter
        import Tkconstants
        import tkMessageBox
        import tkFileDialog
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
            Tkinter.Label(body, text=u"Account Name").grid(row=0)
            self.name = Tkinter.Entry(body, width=40)
            self.name.grid(row=0, column=1, sticky=sticky)
            Tkinter.Label(body, text=u"CC#").grid(row=1)
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
                buttons, text=u"Generate", width=10, command=self.generate)
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
            name = self.name.get()
            ccn = self.ccn.get()
            keypath = self.keypath.get()
            if not name:
                self.status['text'] = u"Name not specified"
                return
            if not ccn:
                self.status['text'] = u"Credit card number not specified"
                return
            if not keypath:
                self.status['text'] = u"Output keyfile path not specified"
                return
            self.status['text'] = u"Generating..."
            try:
                userkey = generate_key(name, ccn)
            except Exception, e:
                self.status['text'] = u"Error: (0}".format(e.args[0])
                return
            open(keypath,'wb').write(userkey)
            self.status['text'] = u"Keyfile successfully generated"

    root = Tkinter.Tk()
    if AES is None:
        root.withdraw()
        tkMessageBox.showerror(
            "Ignoble EPUB Keyfile Generator",
            "This script requires OpenSSL or PyCrypto, which must be installed "
            "separately.  Read the top-of-script comment for details.")
        return 1
    root.title(u"Barnes & Noble ePub Keyfile Generator v.{0}".format(__version__))
    root.resizable(True, False)
    root.minsize(300, 0)
    DecryptionDialog(root).pack(fill=Tkconstants.X, expand=1)
    root.mainloop()
    return 0

if __name__ == '__main__':
    if len(sys.argv) > 1:
        sys.exit(cli_main())
    sys.exit(gui_main())
