#! /usr/bin/python

from __future__ import with_statement

# ignoblekeygen.pyw, version 2.4

# To run this program install Python 2.6 from <http://www.python.org/download/>
# and OpenSSL or PyCrypto from http://www.voidspace.org.uk/python/modules.shtml#pycrypto
# (make sure to install the version for Python 2.6).  Save this script file as
# ignoblekeygen.pyw and double-click on it to run it.

# Revision history:
#   1 - Initial release
#   2 - Add OS X support by using OpenSSL when available (taken/modified from ineptepub v5)
#   2.1 - Allow Windows versions of libcrypto to be found
#   2.2 - On Windows try PyCrypto first and then OpenSSL next
#   2.3 - Modify interface to allow use of import
#   2.4 - Improvements to UI and now works in plugins

"""
Generate Barnes & Noble EPUB user key from name and credit card number.
"""

__license__ = 'GPL v3'

import sys
import os
import hashlib



# use openssl's libcrypt if it exists in place of pycrypto
# code extracted from the Adobe Adept DRM removal code also by I HeartCabbages
class IGNOBLEError(Exception):
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
        print 'libcrypto not found'
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


def generate_keyfile(name, ccn, outpath):
    # remove spaces and case from name and CC numbers.
    name = normalize_name(name) + '\x00'
    ccn = normalize_name(ccn) + '\x00'
    
    name_sha = hashlib.sha1(name).digest()[:16]
    ccn_sha = hashlib.sha1(ccn).digest()[:16]
    both_sha = hashlib.sha1(name + ccn).digest()
    aes = AES(ccn_sha, name_sha)
    crypt = aes.encrypt(both_sha + ('\x0c' * 0x0c))
    userkey = hashlib.sha1(crypt).digest()
    with open(outpath, 'wb') as f:
        f.write(userkey.encode('base64'))
    return userkey




def cli_main(argv=sys.argv):
    progname = os.path.basename(argv[0])
    if AES is None:
        print "%s: This script requires OpenSSL or PyCrypto, which must be installed " \
              "separately.  Read the top-of-script comment for details." % \
              (progname,)
        return 1
    if len(argv) != 4:
        print "usage: %s NAME CC# OUTFILE" % (progname,)
        return 1
    name, ccn, outpath = argv[1:]
    generate_keyfile(name, ccn, outpath)
    return 0


def gui_main():
    import Tkinter
    import Tkconstants
    import tkFileDialog
    import tkMessageBox

    class DecryptionDialog(Tkinter.Frame):
        def __init__(self, root):
            Tkinter.Frame.__init__(self, root, border=5)
            self.status = Tkinter.Label(self, text='Enter parameters')
            self.status.pack(fill=Tkconstants.X, expand=1)
            body = Tkinter.Frame(self)
            body.pack(fill=Tkconstants.X, expand=1)
            sticky = Tkconstants.E + Tkconstants.W
            body.grid_columnconfigure(1, weight=2)
            Tkinter.Label(body, text='Account Name').grid(row=0)
            self.name = Tkinter.Entry(body, width=40)
            self.name.grid(row=0, column=1, sticky=sticky)
            Tkinter.Label(body, text='CC#').grid(row=1)
            self.ccn = Tkinter.Entry(body, width=40)
            self.ccn.grid(row=1, column=1, sticky=sticky)
            Tkinter.Label(body, text='Output file').grid(row=2)
            self.keypath = Tkinter.Entry(body, width=40)
            self.keypath.grid(row=2, column=1, sticky=sticky)
            self.keypath.insert(2, 'bnepubkey.b64')
            button = Tkinter.Button(body, text="...", command=self.get_keypath)
            button.grid(row=2, column=2)
            buttons = Tkinter.Frame(self)
            buttons.pack()
            botton = Tkinter.Button(
                buttons, text="Generate", width=10, command=self.generate)
            botton.pack(side=Tkconstants.LEFT)
            Tkinter.Frame(buttons, width=10).pack(side=Tkconstants.LEFT)
            button = Tkinter.Button(
                buttons, text="Quit", width=10, command=self.quit)
            button.pack(side=Tkconstants.RIGHT)
    
        def get_keypath(self):
            keypath = tkFileDialog.asksaveasfilename(
                parent=None, title='Select B&N EPUB key file to produce',
                defaultextension='.b64',
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
                self.status['text'] = 'Name not specified'
                return
            if not ccn:
                self.status['text'] = 'Credit card number not specified'
                return
            if not keypath:
                self.status['text'] = 'Output keyfile path not specified'
                return
            self.status['text'] = 'Generating...'
            try:
                generate_keyfile(name, ccn, keypath)
            except Exception, e:
                self.status['text'] = 'Error: ' + str(e)
                return
            self.status['text'] = 'Keyfile successfully generated'

    root = Tkinter.Tk()
    if AES is None:
        root.withdraw()
        tkMessageBox.showerror(
            "Ignoble EPUB Keyfile Generator",
            "This script requires OpenSSL or PyCrypto, which must be installed "
            "separately.  Read the top-of-script comment for details.")
        return 1
    root.title('Ignoble EPUB Keyfile Generator')
    root.resizable(True, False)
    root.minsize(300, 0)
    DecryptionDialog(root).pack(fill=Tkconstants.X, expand=1)
    root.mainloop()
    return 0

if __name__ == '__main__':
    if len(sys.argv) > 1:
        sys.exit(cli_main())
    sys.exit(gui_main())
