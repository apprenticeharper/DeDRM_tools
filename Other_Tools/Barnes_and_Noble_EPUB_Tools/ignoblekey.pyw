#! /usr/bin/python

# ignoblekey.pyw, version 2

# To run this program install Python 2.6 from <http://www.python.org/download/>
# Save this script file as ignoblekey.pyw and double-click on it to run it.

# Revision history:
#   1 - Initial release
#   2 - Add some missing code

"""
Retrieve B&N DesktopReader EPUB user AES key.
"""

from __future__ import with_statement

__license__ = 'GPL v3'

import sys
import os
import binascii
import glob
import Tkinter
import Tkconstants
import tkMessageBox
import traceback

BN_KEY_KEY = 'uhk00000000'
BN_APPDATA_DIR = r'Barnes & Noble\DesktopReader'

class IgnobleError(Exception):
    pass

def retrieve_key(inpath, outpath):
    # The B&N DesktopReader 'ClientAPI' file is just a sqlite3 DB.  Requiring
    # users to install sqlite3 and bindings seems like overkill for retrieving
    # one value, so we go in hot and dirty.
    with open(inpath, 'rb') as f:
        data = f.read()
    if BN_KEY_KEY not in data:
        raise IgnobleError('B&N user key not found; unexpected DB format?')
    index = data.rindex(BN_KEY_KEY) + len(BN_KEY_KEY) + 1
    data = data[index:index + 40]
    for i in xrange(20, len(data)):
        try:
            keyb64 = data[:i]
            if len(keyb64.decode('base64')) == 20:
                break
        except binascii.Error:
            pass
    else:
        raise IgnobleError('Problem decoding key; unexpected DB format?')
    with open(outpath, 'wb') as f:
        f.write(keyb64 + '\n')

def cli_main(argv=sys.argv):
    progname = os.path.basename(argv[0])
    args = argv[1:]
    if len(args) != 2:
        sys.stderr.write("USAGE: %s CLIENTDB KEYFILE" % (progname,))
        return 1
    inpath, outpath = args
    retrieve_key(inpath, outpath)
    return 0

def find_bnclientdb_path():
    appdata = os.environ['APPDATA']
    bndir = os.path.join(appdata, BN_APPDATA_DIR)
    if not os.path.isdir(bndir):
        raise IgnobleError('Could not locate B&N Reader installation')
    dbpath = glob.glob(os.path.join(bndir, 'ClientAPI_*.db'))
    if len(dbpath) == 0:
        raise IgnobleError('Problem locating B&N Reader DB')
    return sorted(dbpath)[-1]

class ExceptionDialog(Tkinter.Frame):
    def __init__(self, root, text):
        Tkinter.Frame.__init__(self, root, border=5)
        label = Tkinter.Label(self, text="Unexpected error:",
                              anchor=Tkconstants.W, justify=Tkconstants.LEFT)
        label.pack(fill=Tkconstants.X, expand=0)
        self.text = Tkinter.Text(self)
        self.text.pack(fill=Tkconstants.BOTH, expand=1)
        self.text.insert(Tkconstants.END, text)

def gui_main(argv=sys.argv):
    root = Tkinter.Tk()
    root.withdraw()
    progname = os.path.basename(argv[0])
    keypath = 'bnepubkey.b64'
    try:
        dbpath = find_bnclientdb_path()
        retrieve_key(dbpath, keypath)
    except IgnobleError, e:
        tkMessageBox.showerror("Ignoble Key", "Error: " + str(e))
        return 1
    except Exception:
        root.wm_state('normal')
        root.title('Ignoble Key')
        text = traceback.format_exc()
        ExceptionDialog(root, text).pack(fill=Tkconstants.BOTH, expand=1)
        root.mainloop()
        return 1
    tkMessageBox.showinfo(
        "Ignoble Key", "Key successfully retrieved to %s" % (keypath))
    return 0

if __name__ == '__main__':
    if len(sys.argv) > 1:
        sys.exit(cli_main())
    sys.exit(gui_main())
