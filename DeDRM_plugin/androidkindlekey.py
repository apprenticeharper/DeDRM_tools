#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# androidkindlekey.py
# Copyright © 2010-20 by Thom, Apprentice Harper et al.

# Revision history:
#  1.0   - AmazonSecureStorage.xml decryption to serial number
#  1.1   - map_data_storage.db decryption to serial number
#  1.2   - Changed to be callable from AppleScript by returning only serial number
#        - and changed name to androidkindlekey.py
#        - and added in unicode command line support
#  1.3   - added in TkInter interface, output to a file
#  1.4   - Fix some problems identified by Aldo Bleeker
#  1.5   - Fix another problem identified by Aldo Bleeker
#  2.0   - Python 3 compatibility

"""
Retrieve Kindle for Android Serial Number.
"""

__license__ = 'GPL v3'
__version__ = '2.0'

import os
import sys
import traceback
import getopt
import tempfile
import zlib
import tarfile
from hashlib import md5
from io import BytesIO
from binascii import a2b_hex, b2a_hex

# Routines common to Mac and PC

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
        if isinstance(data,str):
            data = data.encode(self.encoding,"replace")
        self.stream.buffer.write(data)
        self.stream.buffer.flush()

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
        return ["kindlekey.py"]
    else:
        argvencoding = sys.stdin.encoding or "utf-8"
        return [arg if isinstance(arg, str) else str(arg, argvencoding) for arg in sys.argv]

class DrmException(Exception):
    pass

STORAGE  = "backup.ab"
STORAGE1 = "AmazonSecureStorage.xml"
STORAGE2 = "map_data_storage.db"

class AndroidObfuscation(object):
    '''AndroidObfuscation
    For the key, it's written in java, and run in android dalvikvm
    '''

    key = a2b_hex('0176e04c9408b1702d90be333fd53523')

    def encrypt(self, plaintext):
        cipher = self._get_cipher()
        padding = len(self.key) - len(plaintext) % len(self.key)
        plaintext += chr(padding) * padding
        return b2a_hex(cipher.encrypt(plaintext.encode('utf-8')))

    def decrypt(self, ciphertext):
        cipher = self._get_cipher()
        plaintext = cipher.decrypt(a2b_hex(ciphertext))
        return plaintext[:-ord(plaintext[-1])]

    def _get_cipher(self):
        try:
            from Crypto.Cipher import AES
            return AES.new(self.key)
        except ImportError:
            from aescbc import AES, noPadding
            return AES(self.key, padding=noPadding())

class AndroidObfuscationV2(AndroidObfuscation):
    '''AndroidObfuscationV2
    '''

    count = 503
    password = b'Thomsun was here!'

    def __init__(self, salt):
        key = self.password + salt
        for _ in range(self.count):
            key = md5(key).digest()
        self.key = key[:8]
        self.iv = key[8:16]

    def _get_cipher(self):
        try :
            from Crypto.Cipher import DES
            return DES.new(self.key, DES.MODE_CBC, self.iv)
        except ImportError:
            from python_des import Des, CBC
            return Des(self.key, CBC, self.iv)

def parse_preference(path):
    ''' parse android's shared preference xml '''
    storage = {}
    read = open(path)
    for line in read:
        line = line.strip()
        # <string name="key">value</string>
        if line.startswith('<string name="'):
            index = line.find('"', 14)
            key = line[14:index]
            value = line[index+2:-9]
            storage[key] = value
    read.close()
    return storage

def get_serials1(path=STORAGE1):
    ''' get serials from android's shared preference xml '''

    if not os.path.isfile(path):
        return []

    storage = parse_preference(path)
    salt = storage.get('AmazonSaltKey')
    if salt and len(salt) == 16:
        obfuscation = AndroidObfuscationV2(a2b_hex(salt))
    else:
        obfuscation = AndroidObfuscation()

    def get_value(key):
        encrypted_key = obfuscation.encrypt(key)
        encrypted_value = storage.get(encrypted_key)
        if encrypted_value:
            return obfuscation.decrypt(encrypted_value)
        return ''

    # also see getK4Pids in kgenpids.py
    try:
        dsnid = get_value('DsnId')
    except:
        sys.stderr.write('cannot get DsnId\n')
        return []

    try:
        tokens = set(get_value('kindle.account.tokens').split(','))
    except:
        sys.stderr.write('cannot get kindle account tokens\n')
        return []

    serials = []
    if dsnid:
        serials.append(dsnid)
    for token in tokens:
        if token:
            serials.append('%s%s' % (dsnid, token))
            serials.append(token)
    return serials

def get_serials2(path=STORAGE2):
    ''' get serials from android's sql database '''
    if not os.path.isfile(path):
        return []

    import sqlite3
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    cursor.execute('''select device_data_value from device_data where device_data_key like '%serial.number%' ''')
    device_data_keys = cursor.fetchall()
    dsns = []
    for device_data_row in device_data_keys:
        try:
            if device_data_row and device_data_row[0]:
                if len(device_data_row[0]) > 0:
                    dsns.append(device_data_row[0])
        except:
            print("Error getting one of the device serial name keys")
            traceback.print_exc()
            pass
    dsns = list(set(dsns))

    cursor.execute('''select userdata_value from userdata where userdata_key like '%/%kindle.account.tokens%' ''')
    userdata_keys = cursor.fetchall()
    tokens = []
    for userdata_row in userdata_keys:
        try:
            if userdata_row and userdata_row[0]:
                if len(userdata_row[0]) > 0:
                    if ',' in userdata_row[0]:
                        splits = userdata_row[0].split(',')
                        for split in splits:
                            tokens.append(split)
                    tokens.append(userdata_row[0])
        except:
            print("Error getting one of the account token keys")
            traceback.print_exc()
            pass
    tokens = list(set(tokens))

    serials = []
    for x in dsns:
        serials.append(x)
        for y in tokens:
            serials.append(y)
            serials.append(x+y)
    return serials

def get_serials(path=STORAGE):
    '''get serials from files in from android backup.ab
    backup.ab can be get using adb command:
    shell> adb backup com.amazon.kindle
    or from individual files if they're passed.
    '''
    if not os.path.isfile(path):
        return []

    basename = os.path.basename(path)
    if basename == STORAGE1:
        return get_serials1(path)
    elif basename == STORAGE2:
        return get_serials2(path)

    output = None
    try :
        read = open(path, 'rb')
        head = read.read(24)
        if head[:14] == b'ANDROID BACKUP':
            output = BytesIO(zlib.decompress(read.read()))
    except Exception:
        pass
    finally:
        read.close()

    if not output:
        return []

    serials = []
    tar = tarfile.open(fileobj=output)
    for member in tar.getmembers():
        if member.name.strip().endswith(STORAGE1):
            write = tempfile.NamedTemporaryFile(mode='wb', delete=False)
            write.write(tar.extractfile(member).read())
            write.close()
            write_path = os.path.abspath(write.name)
            serials.extend(get_serials1(write_path))
            os.remove(write_path)
        elif member.name.strip().endswith(STORAGE2):
            write = tempfile.NamedTemporaryFile(mode='wb', delete=False)
            write.write(tar.extractfile(member).read())
            write.close()
            write_path = os.path.abspath(write.name)
            serials.extend(get_serials2(write_path))
            os.remove(write_path)
    return list(set(serials))

__all__ = [ 'get_serials', 'getkey']

# procedure for CLI and GUI interfaces
# returns single or multiple keys (one per line) in the specified file
def getkey(outfile, inpath):
    keys = get_serials(inpath)
    if len(keys) > 0:
        with open(outfile, 'w') as keyfileout:
            for key in keys:
                keyfileout.write(key)
                keyfileout.write("\n")
        return True
    return False


def usage(progname):
    print("Decrypts the serial number(s) of Kindle For Android from Android backup or file")
    print("Get backup.ab file using adb backup com.amazon.kindle for Android 4.0+.")
    print("Otherwise extract AmazonSecureStorage.xml from /data/data/com.amazon.kindle/shared_prefs/AmazonSecureStorage.xml")
    print("Or map_data_storage.db from /data/data/com.amazon.kindle/databases/map_data_storage.db")
    print("")
    print("Usage:")
    print("    {0:s} [-h] [-b <backup.ab>] [<outfile.k4a>]".format(progname))


def cli_main():
    sys.stdout=SafeUnbuffered(sys.stdout)
    sys.stderr=SafeUnbuffered(sys.stderr)
    argv=unicode_argv()
    progname = os.path.basename(argv[0])
    print("{0} v{1}\nCopyright © 2010-2020 Thom, Apprentice Harper et al.".format(progname,__version__))

    try:
        opts, args = getopt.getopt(argv[1:], "hb:")
    except getopt.GetoptError as err:
        usage(progname)
        print("\nError in options or arguments: {0}".format(err.args[0]))
        return 2

    inpath = ""
    for o, a in opts:
        if o == "-h":
            usage(progname)
            return 0
        if o == "-b":
            inpath = a

    if len(args) > 1:
        usage(progname)
        return 2

    if len(args) == 1:
        # save to the specified file or directory
        outfile = args[0]
        if not os.path.isabs(outfile):
           outfile = os.path.join(os.path.dirname(argv[0]),outfile)
           outfile = os.path.abspath(outfile)
        if os.path.isdir(outfile):
           outfile = os.path.join(os.path.dirname(argv[0]),"androidkindlekey.k4a")
    else:
        # save to the same directory as the script
        outfile = os.path.join(os.path.dirname(argv[0]),"androidkindlekey.k4a")

    # make sure the outpath is OK
    outfile = os.path.realpath(os.path.normpath(outfile))

    if not os.path.isfile(inpath):
        usage(progname)
        print("\n{0:s} file not found".format(inpath))
        return 2

    if getkey(outfile, inpath):
        print("\nSaved Kindle for Android key to {0}".format(outfile))
    else:
        print("\nCould not retrieve Kindle for Android key.")
    return 0


def gui_main():
    try:
        import tkinter
        import tkinter.constants
        import tkinter.messagebox
        import tkinter.filedialog
    except:
        print("tkinter not installed")
        return 0

    class DecryptionDialog(tkinter.Frame):
        def __init__(self, root):
            tkinter.Frame.__init__(self, root, border=5)
            self.status = tkinter.Label(self, text="Select backup.ab file")
            self.status.pack(fill=tkinter.constants.X, expand=1)
            body = tkinter.Frame(self)
            body.pack(fill=tkinter.constants.X, expand=1)
            sticky = tkinter.constants.E + tkinter.constants.W
            body.grid_columnconfigure(1, weight=2)
            tkinter.Label(body, text="Backup file").grid(row=0, column=0)
            self.keypath = tkinter.Entry(body, width=40)
            self.keypath.grid(row=0, column=1, sticky=sticky)
            self.keypath.insert(2, "backup.ab")
            button = tkinter.Button(body, text="...", command=self.get_keypath)
            button.grid(row=0, column=2)
            buttons = tkinter.Frame(self)
            buttons.pack()
            button2 = tkinter.Button(
                buttons, text="Extract", width=10, command=self.generate)
            button2.pack(side=tkinter.constants.LEFT)
            tkinter.Frame(buttons, width=10).pack(side=tkinter.constants.LEFT)
            button3 = tkinter.Button(
                buttons, text="Quit", width=10, command=self.quit)
            button3.pack(side=tkinter.constants.RIGHT)

        def get_keypath(self):
            keypath = tkinter.filedialog.askopenfilename(
                parent=None, title="Select backup.ab file",
                defaultextension=".ab",
                filetypes=[('adb backup com.amazon.kindle', '.ab'),
                           ('All Files', '.*')])
            if keypath:
                keypath = os.path.normpath(keypath)
                self.keypath.delete(0, tkinter.constants.END)
                self.keypath.insert(0, keypath)
            return

        def generate(self):
            inpath = self.keypath.get()
            self.status['text'] = "Getting key..."
            try:
                keys = get_serials(inpath)
                keycount = 0
                for key in keys:
                    while True:
                        keycount += 1
                        outfile = os.path.join(progpath,"kindlekey{0:d}.k4a".format(keycount))
                        if not os.path.exists(outfile):
                            break

                    with open(outfile, 'w') as keyfileout:
                        keyfileout.write(key)
                    success = True
                    tkinter.messagebox.showinfo(progname, "Key successfully retrieved to {0}".format(outfile))
            except Exception as e:
                self.status['text'] = "Error: {0}".format(e.args[0])
                return
            self.status['text'] = "Select backup.ab file"

    argv=unicode_argv()
    progpath, progname = os.path.split(argv[0])
    root = tkinter.Tk()
    root.title("Kindle for Android Key Extraction v.{0}".format(__version__))
    root.resizable(True, False)
    root.minsize(300, 0)
    DecryptionDialog(root).pack(fill=tkinter.constants.X, expand=1)
    root.mainloop()
    return 0

if __name__ == '__main__':
    if len(sys.argv) > 1:
        sys.exit(cli_main())
    sys.exit(gui_main())
