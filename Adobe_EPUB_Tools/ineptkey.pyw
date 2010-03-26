#! /usr/bin/python

# ineptkey.pyw, version 4.4
# ineptkeyv44

# To run this program install Python 2.6 from http://www.python.org/download/
# and PyCrypto from http://www.voidspace.org.uk/python/modules.shtml#pycrypto
# (make sure to install the version for Python 2.6).  Save this script file as
# ineptkey.pyw and double-click on it to run it.  It will create a file named
# adeptkey.der in the same directory.  These are your ADEPT user keys.

# Revision history:
#   1 - Initial release, for Adobe Digital Editions 1.7
#   2 - Better algorithm for finding pLK; improved error handling
#   3 - Rename to INEPT
#   4.1 - quick beta fix for ADE 1.7.2 (anon)
#   4.2 - added old 1.7.1 processing
#   4.3 - better key search
#   4.4 - Make it working on 64-bit Python

"""
Retrieve Adobe ADEPT user key under Windows.
"""

from __future__ import with_statement

__license__ = 'GPL v3'

import sys
import os
from struct import pack
from ctypes import windll, c_char_p, c_wchar_p, c_uint, POINTER, byref, \
    create_unicode_buffer, create_string_buffer, CFUNCTYPE, addressof, \
    string_at, Structure, c_void_p, cast, c_ulonglong, \
    sizeof, c_void_p, c_size_t

import _winreg as winreg
import Tkinter
import Tkconstants
import tkMessageBox
import traceback
import hashlib
import pickle


try:
    from Crypto.Cipher import AES
except ImportError:
    AES = None


DEVICE_KEY = 'Software\\Adobe\\Adept\\Device'
PRIVATE_LICENCE_KEY = 'Software\\Adobe\\Adept\\Activation\\%04d'
PRIVATE_LICENCE_KEY_KEY = 'Software\\Adobe\\Adept\\Activation\\%04d\\%04d'
ACTIVATION = 'Software\\Adobe\\Adept\\Activation\\'

MAX_PATH = 255

kernel32 = windll.kernel32
advapi32 = windll.advapi32
crypt32 = windll.crypt32


class ADEPTError(Exception):
    pass


def GetSystemDirectory():
    GetSystemDirectoryW = kernel32.GetSystemDirectoryW
    GetSystemDirectoryW.argtypes = [c_wchar_p, c_uint]
    GetSystemDirectoryW.restype = c_uint
    def GetSystemDirectory():
        buffer = create_unicode_buffer(MAX_PATH + 1)
        GetSystemDirectoryW(buffer, len(buffer))
        return buffer.value
    return GetSystemDirectory
GetSystemDirectory = GetSystemDirectory()


def GetVolumeSerialNumber():
    GetVolumeInformationW = kernel32.GetVolumeInformationW
    GetVolumeInformationW.argtypes = [c_wchar_p, c_wchar_p, c_uint,
                                      POINTER(c_uint), POINTER(c_uint),
                                      POINTER(c_uint), c_wchar_p, c_uint]
    GetVolumeInformationW.restype = c_uint
    def GetVolumeSerialNumber(path):
        vsn = c_uint(0)
        GetVolumeInformationW(path, None, 0, byref(vsn), None, None, None, 0)
        return vsn.value
    return GetVolumeSerialNumber
GetVolumeSerialNumber = GetVolumeSerialNumber()


def GetUserName():
    GetUserNameW = advapi32.GetUserNameW
    GetUserNameW.argtypes = [c_wchar_p, POINTER(c_uint)]
    GetUserNameW.restype = c_uint
    def GetUserName():
        buffer = create_unicode_buffer(32)
        size = c_uint(len(buffer))
        while not GetUserNameW(buffer, byref(size)):
            buffer = create_unicode_buffer(len(buffer) * 2)
            size.value = len(buffer)
        return buffer.value.encode('utf-16-le')[::2]
    return GetUserName
GetUserName = GetUserName()

if sizeof(c_void_p) == 4:
    ## 32-bit Python
    CPUID0_INSNS = create_string_buffer("\x53\x31\xc0\x0f\xa2\x8b\x44\x24\x08\x89"
                                        "\x18\x89\x50\x04\x89\x48\x08\x5b\xc3")
    def cpuid0():
        buffer = create_string_buffer(12)
        cpuid0__ = CFUNCTYPE(c_char_p)(addressof(CPUID0_INSNS))
        def cpuid0():
            cpuid0__(buffer)
            return buffer.raw
        return cpuid0
    cpuid0 = cpuid0()

    CPUID1_INSNS = create_string_buffer("\x53\x31\xc0\x40\x0f\xa2\x5b\xc3")
    cpuid1 = CFUNCTYPE(c_uint)(addressof(CPUID1_INSNS))
else:
    ## 64 bit Python

    # In 64-bit we cannot execute instructions stored in a string because
    # the O.S. prevents that to defend against buffer overrun attacks.
    # Therefore we have to allocate a block of memory with the execute
    # permission and copy our code into it.
    
    NULL = c_void_p(0)
    PAGE_EXECUTE_READWRITE = 0x40
    MEM_COMMIT  = 0x1000
    MEM_RESERVE = 0x2000

    VirtualAlloc = windll.kernel32.VirtualAlloc
    VirtualAlloc.restype = c_void_p
    VirtualAlloc.argtypes = (c_void_p, c_size_t, c_uint, c_uint)

    from ctypes import memmove
    memmove.restype = c_void_p
    memmove.argtypes = (c_void_p, c_void_p, c_size_t)

    CPUID0_INSNS = (b"\x55"             # push   %rbp
                    "\x48\x89\xe5"      # mov    %rsp,%rbp
                    "\x48\x89\x4d\xf8"  # mov    %rcx,-0x8(%rbp)
                    "\x31\xc0"          # xor    %eax,%eax
                    "\x0f\xa2"          # cpuid  
                    "\x48\x8b\x45\xf8"  # mov    -0x8(%rbp),%rax
                    "\x89\x18"          # mov    %ebx,(%rax)
                    "\x89\x50\x04"      # mov    %edx,0x4(%rax)
                    "\x89\x48\x08"      # mov    %ecx,0x8(%rax)
                    "\x48\x8b\x45\xf8"  # mov    -0x8(%rbp),%rax
                    "\xc9"              # leave
                    "\xc3"              # ret
                    )

    CPUID1_INSNS = (b"\x31\xc0"         # xor    %eax,%eax
                    "\xff\xc0"          # inc    %eax
                    "\x0f\xa2"          # cpuid  
                    "\xc3"              # ret
                    )

    insnlen0 = len(CPUID0_INSNS)
    insnlen1 = len(CPUID1_INSNS)
    insnlen = insnlen0 + insnlen1

    code_addr = (VirtualAlloc(NULL, insnlen,
                    MEM_RESERVE|MEM_COMMIT, PAGE_EXECUTE_READWRITE))

    if code_addr is None:
        raise ADEPTError("Failed to allocate memory")

    memmove(code_addr, CPUID0_INSNS + CPUID1_INSNS, insnlen)

    def cpuid0():
        buffer = create_string_buffer(12)
        cpuid0__ = CFUNCTYPE(c_ulonglong, c_char_p)(code_addr)
        def cpuid0():
            cpuid0__(buffer)
            return buffer.raw
        return cpuid0
    cpuid0 = cpuid0()

    cpuid1 =  CFUNCTYPE(c_ulonglong)(code_addr + insnlen0)

class DataBlob(Structure):
    _fields_ = [('cbData', c_uint),
                ('pbData', c_void_p)]
DataBlob_p = POINTER(DataBlob)

def CryptUnprotectData():
    _CryptUnprotectData = crypt32.CryptUnprotectData
    _CryptUnprotectData.argtypes = [DataBlob_p, c_wchar_p, DataBlob_p,
                                   c_void_p, c_void_p, c_uint, DataBlob_p]
    _CryptUnprotectData.restype = c_uint
    def CryptUnprotectData(indata, entropy):
        indatab = create_string_buffer(indata)
        indata = DataBlob(len(indata), cast(indatab, c_void_p))
        entropyb = create_string_buffer(entropy)
        entropy = DataBlob(len(entropy), cast(entropyb, c_void_p))
        outdata = DataBlob()
        if not _CryptUnprotectData(byref(indata), None, byref(entropy),
                                   None, None, 0, byref(outdata)):
            raise ADEPTError("Failed to decrypt user key key (sic)")
        return string_at(outdata.pbData, outdata.cbData)
    return CryptUnprotectData
CryptUnprotectData = CryptUnprotectData()


def retrieve_key(keypath):
    root = GetSystemDirectory().split('\\')[0] + '\\'
    serial = GetVolumeSerialNumber(root)
    vendor = cpuid0()
    signature = pack('>I', cpuid1())[1:]
    user = GetUserName()
    entropy = pack('>I12s3s13s', serial, vendor, signature, user)
    cuser = winreg.HKEY_CURRENT_USER
    try:
        regkey = winreg.OpenKey(cuser, DEVICE_KEY)
    except WindowsError:
        raise ADEPTError("Adobe Digital Editions not activated")
    device = winreg.QueryValueEx(regkey, 'key')[0]
    keykey = CryptUnprotectData(device, entropy)
    userkey = None
    pkcs = None
    keys = {}
    counter = 0
    for i in xrange(0, 16):
        skey = PRIVATE_LICENCE_KEY % i
        try:
            regkey = winreg.OpenKey(cuser, skey)
        except WindowsError:
            break
        type = winreg.QueryValueEx(regkey, None)[0]
        # obfuscation technique
        if type != 'credentials':
            continue
        for j in xrange(0, 16):
            plkkey = PRIVATE_LICENCE_KEY_KEY  % (i, j)
            try:
                regkey = winreg.OpenKey(cuser, plkkey)                
            except WindowsError:
                break
            type = winreg.QueryValueEx(regkey, None)[0]            
            if type != 'privateLicenseKey':
                continue
            userkey = winreg.QueryValueEx(regkey, 'value')[0]
            break
        for j in xrange(0, 16):
            plkkey = PRIVATE_LICENCE_KEY_KEY  % (i, j)
            try:
                pkcs = winreg.OpenKey(cuser, plkkey)   
            except WindowsError:
                break
            type = winreg.QueryValueEx(pkcs, None)[0]
            if type != 'pkcs12':
                continue
            pkcs = winreg.QueryValueEx(pkcs, 'value')[0]
            break
    if pkcs is None:       
        raise ADEPTError('Could not locate PKCS specification')
    if userkey is None:
        raise ADEPTError('Could not locate privateLicenseKey')
    userkey = userkey.decode('base64')
    userkey = AES.new(keykey, AES.MODE_CBC).decrypt(userkey)
    userkey = userkey[26:-ord(userkey[-1])]
    with open(keypath, 'wb') as f:
        f.write(userkey)
    return

class ExceptionDialog(Tkinter.Frame):
    def __init__(self, root, text):
        Tkinter.Frame.__init__(self, root, border=5)
        label = Tkinter.Label(self, text="Unexpected error:",
                              anchor=Tkconstants.W, justify=Tkconstants.LEFT)
        label.pack(fill=Tkconstants.X, expand=0)
        self.text = Tkinter.Text(self)
        self.text.pack(fill=Tkconstants.BOTH, expand=1)
        self.text.insert(Tkconstants.END, text)


def main(argv=sys.argv):
    root = Tkinter.Tk()
    root.withdraw()
    progname = os.path.basename(argv[0])
    if AES is None:
        tkMessageBox.showerror(
            "ADEPT Key",
            "This script requires PyCrypto, which must be installed "
            "separately.  Read the top-of-script comment for details.")
        return 1
    keypath = 'adeptkey.der'
    try:
        retrieve_key(keypath)
    except ADEPTError, e:
        tkMessageBox.showerror("ADEPT Key", "Error: " + str(e))
        return 1
    except Exception:
        root.wm_state('normal')
        root.title('ADEPT Key')
        text = traceback.format_exc()
        ExceptionDialog(root, text).pack(fill=Tkconstants.BOTH, expand=1)
        root.mainloop()
        return 1
    tkMessageBox.showinfo(
        "ADEPT Key", "Key successfully retrieved to %s" % (keypath))
    return 0

if __name__ == '__main__':
    sys.exit(main())