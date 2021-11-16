#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Mobipocket PID calculator v0.4 for Amazon Kindle.
# Copyright (c) 2007, 2009 Igor Skochinsky <skochinsky@mail.ru>
# History:
#  0.1 Initial release
#  0.2 Added support for generating PID for iPhone (thanks to mbp)
#  0.3 changed to autoflush stdout, fixed return code usage
#  0.3 updated for unicode
#  0.4 Added support for serial numbers starting with '9', fixed unicode bugs.
#  0.5 moved unicode_argv call inside main for Windows DeDRM compatibility
#  1.0 Python 3 for calibre 5.0


import sys
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
                    range(start, argc.value)]
        # if we don't have any arguments at all, just pass back script name
        # this should never happen
        return ["kindlepid.py"]
    else:
        argvencoding = sys.stdin.encoding or "utf-8"
        return [arg if (isinstance(arg, str) or isinstance(arg,unicode)) else str(arg, argvencoding) for arg in sys.argv]

letters = 'ABCDEFGHIJKLMNPQRSTUVWXYZ123456789'

def crc32(s):
    return (~binascii.crc32(s,-1))&0xFFFFFFFF

def checksumPid(s):
    crc = crc32(s.encode('ascii'))
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
    for i in range(len(s)):
        arr1[i%l] ^= s[i]

    crc_bytes = [crc >> 24 & 0xff, crc >> 16 & 0xff, crc >> 8 & 0xff, crc & 0xff]
    for i in range(l):
        arr1[i] ^= crc_bytes[i&3]

    pid = ''
    for i in range(l):
        b = arr1[i] & 0xff
        pid+=letters[(b >> 7) + ((b >> 5 & 3) ^ (b & 0x1f))]

    return pid

def cli_main():
    print("Mobipocket PID calculator for Amazon Kindle. Copyright © 2007, 2009 Igor Skochinsky")
    argv=unicode_argv()
    if len(argv)==2:
        serial = argv[1]
    else:
        print("Usage: kindlepid.py <Kindle Serial Number>/<iPhone/iPod Touch UDID>")
        return 1
    if len(serial)==16:
        if serial.startswith("B") or serial.startswith("9"):
            print("Kindle serial number detected")
        else:
            print("Warning: unrecognized serial number. Please recheck input.")
            return 1
        pid = pidFromSerial(serial.encode("utf-8"),7)+'*'
        print("Mobipocket PID for Kindle serial#{0} is {1}".format(serial,checksumPid(pid)))
        return 0
    elif len(serial)==40:
        print("iPhone serial number (UDID) detected")
        pid = pidFromSerial(serial.encode("utf-8"),8)
        print("Mobipocket PID for iPhone serial#{0} is {1}".format(serial,checksumPid(pid)))
        return 0
    print("Warning: unrecognized serial number. Please recheck input.")
    return 1


if __name__ == "__main__":
    sys.stdout=SafeUnbuffered(sys.stdout)
    sys.stderr=SafeUnbuffered(sys.stderr)
    sys.exit(cli_main())
