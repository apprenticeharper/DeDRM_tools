#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ignoblekeyNookStudy.py
# Copyright © 2015-2020 Apprentice Alf, Apprentice Harper et al.

# Based on kindlekey.py, Copyright © 2010-2013 by some_updates and Apprentice Alf

# Released under the terms of the GNU General Public Licence, version 3
# <http://www.gnu.org/licenses/>

# Revision history:
#   1.0 - Initial release
#   1.1 - remove duplicates and return last key as single key
#   2.0 - Python 3 for calibre 5.0

"""
Get Barnes & Noble EPUB user key from nook Studio log file
"""

__license__ = 'GPL v3'
__version__ = "2.0"

import sys
import os
import hashlib
import getopt
import re

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
        return ["ignoblekey.py"]
    else:
        argvencoding = sys.stdin.encoding or "utf-8"
        return [arg if (isinstance(arg, str) or isinstance(arg,unicode)) else str(arg, argvencoding) for arg in sys.argv]

class DrmException(Exception):
    pass

# Locate all of the nookStudy/nook for PC/Mac log file and return as list
def getNookLogFiles():
    logFiles = []
    found = False
    if iswindows:
        try:
            import winreg
        except ImportError:
            import _winreg as winreg

        # some 64 bit machines do not have the proper registry key for some reason
        # or the python interface to the 32 vs 64 bit registry is broken
        paths = set()
        if 'LOCALAPPDATA' in os.environ.keys():
            # Python 2.x does not return unicode env. Use Python 3.x
            path = winreg.ExpandEnvironmentStrings("%LOCALAPPDATA%")
            if os.path.isdir(path):
                paths.add(path)
        if 'USERPROFILE' in os.environ.keys():
            # Python 2.x does not return unicode env. Use Python 3.x
            path = winreg.ExpandEnvironmentStrings("%USERPROFILE%")+"\\AppData\\Local"
            if os.path.isdir(path):
                paths.add(path)
            path = winreg.ExpandEnvironmentStrings("%USERPROFILE%")+"\\AppData\\Roaming"
            if os.path.isdir(path):
                paths.add(path)
        # User Shell Folders show take precedent over Shell Folders if present
        try:
            regkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\User Shell Folders\\")
            path = winreg.QueryValueEx(regkey, 'Local AppData')[0]
            if os.path.isdir(path):
                paths.add(path)
        except WindowsError:
            pass
        try:
            regkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\User Shell Folders\\")
            path = winreg.QueryValueEx(regkey, 'AppData')[0]
            if os.path.isdir(path):
                paths.add(path)
        except WindowsError:
            pass
        try:
            regkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Folders\\")
            path = winreg.QueryValueEx(regkey, 'Local AppData')[0]
            if os.path.isdir(path):
                paths.add(path)
        except WindowsError:
            pass
        try:
            regkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Folders\\")
            path = winreg.QueryValueEx(regkey, 'AppData')[0]
            if os.path.isdir(path):
                paths.add(path)
        except WindowsError:
            pass

        for path in paths:
            # look for nookStudy log file
            logpath = path +'\\Barnes & Noble\\NOOKstudy\\logs\\BNClientLog.txt'
            if os.path.isfile(logpath):
                found = True
                print('Found nookStudy log file: ' + logpath, file=sys.stderr)
                logFiles.append(logpath)
    else:
        home = os.getenv('HOME')
        # check for BNClientLog.txt in various locations
        testpath = home + '/Library/Application Support/Barnes & Noble/DesktopReader/logs/BNClientLog.txt'
        if os.path.isfile(testpath):
            logFiles.append(testpath)
            print('Found nookStudy log file: ' + testpath, file=sys.stderr)
            found = True
        testpath = home + '/Library/Application Support/Barnes & Noble/DesktopReader/indices/BNClientLog.txt'
        if os.path.isfile(testpath):
            logFiles.append(testpath)
            print('Found nookStudy log file: ' + testpath, file=sys.stderr)
            found = True
        testpath = home + '/Library/Application Support/Barnes & Noble/BNDesktopReader/logs/BNClientLog.txt'
        if os.path.isfile(testpath):
            logFiles.append(testpath)
            print('Found nookStudy log file: ' + testpath, file=sys.stderr)
            found = True
        testpath = home + '/Library/Application Support/Barnes & Noble/BNDesktopReader/indices/BNClientLog.txt'
        if os.path.isfile(testpath):
            logFiles.append(testpath)
            print('Found nookStudy log file: ' + testpath, file=sys.stderr)
            found = True

    if not found:
        print('No nook Study log files have been found.', file=sys.stderr)
    return logFiles


# Extract CCHash key(s) from log file
def getKeysFromLog(kLogFile):
    keys = []
    regex = re.compile("ccHash: \"(.{28})\"");
    for line in open(kLogFile):
        for m in regex.findall(line):
            keys.append(m)
    return keys

# interface for calibre plugin
def nookkeys(files = []):
    keys = []
    if files == []:
        files = getNookLogFiles()
    for file in files:
        fileKeys = getKeysFromLog(file)
        if fileKeys:
            print("Found {0} keys in the Nook Study log files".format(len(fileKeys)), file=sys.stderr)
            keys.extend(fileKeys)
    return list(set(keys))

# interface for Python DeDRM
# returns single key or multiple keys, depending on path or file passed in
def getkey(outpath, files=[]):
    keys = nookkeys(files)
    if len(keys) > 0:
        if not os.path.isdir(outpath):
            outfile = outpath
            with open(outfile, 'w') as keyfileout:
                keyfileout.write(keys[-1])
            print("Saved a key to {0}".format(outfile), file=sys.stderr)
        else:
            keycount = 0
            for key in keys:
                while True:
                    keycount += 1
                    outfile = os.path.join(outpath,"nookkey{0:d}.b64".format(keycount))
                    if not os.path.exists(outfile):
                        break
                with open(outfile, 'w') as keyfileout:
                    keyfileout.write(key)
                print("Saved a key to {0}".format(outfile), file=sys.stderr)
        return True
    return False

def usage(progname):
    print("Finds the nook Study encryption keys.")
    print("Keys are saved to the current directory, or a specified output directory.")
    print("If a file name is passed instead of a directory, only the first key is saved, in that file.")
    print("Usage:")
    print("    {0:s} [-h] [-k <logFile>] [<outpath>]".format(progname))


def cli_main():
    sys.stdout=SafeUnbuffered(sys.stdout)
    sys.stderr=SafeUnbuffered(sys.stderr)
    argv=unicode_argv()
    progname = os.path.basename(argv[0])
    print("{0} v{1}\nCopyright © 2015 Apprentice Alf".format(progname,__version__))

    try:
        opts, args = getopt.getopt(argv[1:], "hk:")
    except getopt.GetoptError as err:
        print("Error in options or arguments: {0}".format(err.args[0]))
        usage(progname)
        sys.exit(2)

    files = []
    for o, a in opts:
        if o == "-h":
            usage(progname)
            sys.exit(0)
        if o == "-k":
            files = [a]

    if len(args) > 1:
        usage(progname)
        sys.exit(2)

    if len(args) == 1:
        # save to the specified file or directory
        outpath = args[0]
        if not os.path.isabs(outpath):
           outpath = os.path.abspath(outpath)
    else:
        # save to the same directory as the script
        outpath = os.path.dirname(argv[0])

    # make sure the outpath is the
    outpath = os.path.realpath(os.path.normpath(outpath))

    if not getkey(outpath, files):
        print("Could not retrieve nook Study key.")
    return 0


def gui_main():
    try:
        import tkinter
        import tkinter.constants
        import tkinter.messagebox
        import traceback
    except:
        return cli_main()

    class ExceptionDialog(tkinter.Frame):
        def __init__(self, root, text):
            tkinter.Frame.__init__(self, root, border=5)
            label = tkinter.Label(self, text="Unexpected error:",
                                  anchor=tkinter.constants.W, justify=tkinter.constants.LEFT)
            label.pack(fill=tkinter.constants.X, expand=0)
            self.text = tkinter.Text(self)
            self.text.pack(fill=tkinter.constants.BOTH, expand=1)

            self.text.insert(tkinter.constants.END, text)


    argv=unicode_argv()
    root = tkinter.Tk()
    root.withdraw()
    progpath, progname = os.path.split(argv[0])
    success = False
    try:
        keys = nookkeys()
        keycount = 0
        for key in keys:
            print(key)
            while True:
                keycount += 1
                outfile = os.path.join(progpath,"nookkey{0:d}.b64".format(keycount))
                if not os.path.exists(outfile):
                    break

            with open(outfile, 'w') as keyfileout:
                keyfileout.write(key)
            success = True
            tkinter.messagebox.showinfo(progname, "Key successfully retrieved to {0}".format(outfile))
    except DrmException as e:
        tkinter.messagebox.showerror(progname, "Error: {0}".format(str(e)))
    except Exception:
        root.wm_state('normal')
        root.title(progname)
        text = traceback.format_exc()
        ExceptionDialog(root, text).pack(fill=tkinter.constants.BOTH, expand=1)
        root.mainloop()
    if not success:
        return 1
    return 0

if __name__ == '__main__':
    if len(sys.argv) > 1:
        sys.exit(cli_main())
    sys.exit(gui_main())
