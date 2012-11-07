#! /usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import with_statement

# ineptkey.pyw, version 5.6
# Copyright © 2009-2010 i♥cabbages

# Released under the terms of the GNU General Public Licence, version 3 or
# later.  <http://www.gnu.org/licenses/>

# Windows users: Before running this program, you must first install Python 2.6
#   from <http://www.python.org/download/> and PyCrypto from
#   <http://www.voidspace.org.uk/python/modules.shtml#pycrypto> (make certain
#   to install the version for Python 2.6).  Then save this script file as
#   ineptkey.pyw and double-click on it to run it.  It will create a file named
#   adeptkey.der in the same directory.  This is your ADEPT user key.
#
# Mac OS X users: Save this script file as ineptkey.pyw.  You can run this
#   program from the command line (pythonw ineptkey.pyw) or by double-clicking
#   it when it has been associated with PythonLauncher.  It will create a file
#   named adeptkey.der in the same directory.  This is your ADEPT user key.

# Revision history:
#   1 - Initial release, for Adobe Digital Editions 1.7
#   2 - Better algorithm for finding pLK; improved error handling
#   3 - Rename to INEPT
#   4 - Series of changes by joblack (and others?) --
#   4.1 - quick beta fix for ADE 1.7.2 (anon)
#   4.2 - added old 1.7.1 processing
#   4.3 - better key search
#   4.4 - Make it working on 64-bit Python
#   5 - Clean up and improve 4.x changes;
#       Clean up and merge OS X support by unknown
#   5.1 - add support for using OpenSSL on Windows in place of PyCrypto
#   5.2 - added support for output of key to a particular file
#   5.3 - On Windows try PyCrypto first, OpenSSL next
#   5.4 - Modify interface to allow use of import
#   5.5 - Fix for potential problem with PyCrypto
#   5.6 - Revise to allow use in Plugins to eliminate need for duplicate code

"""
Retrieve Adobe ADEPT user key.
"""

__license__ = 'GPL v3'

import sys
import os
import struct

try:
    from calibre.constants import iswindows, isosx
except:
    iswindows = sys.platform.startswith('win')
    isosx = sys.platform.startswith('darwin')

class ADEPTError(Exception):
    pass

if iswindows:
    from ctypes import windll, c_char_p, c_wchar_p, c_uint, POINTER, byref, \
        create_unicode_buffer, create_string_buffer, CFUNCTYPE, addressof, \
        string_at, Structure, c_void_p, cast, c_size_t, memmove, CDLL, c_int, \
        c_long, c_ulong

    from ctypes.wintypes import LPVOID, DWORD, BOOL
    import _winreg as winreg

    def _load_crypto_libcrypto():
        from ctypes.util import find_library
        libcrypto = find_library('libeay32')
        if libcrypto is None:
            raise ADEPTError('libcrypto not found')
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
    
        AES_set_decrypt_key = F(c_int, 'AES_set_decrypt_key',
                                [c_char_p, c_int, AES_KEY_p])
        AES_cbc_encrypt = F(None, 'AES_cbc_encrypt',
                            [c_char_p, c_char_p, c_ulong, AES_KEY_p, c_char_p,
                             c_int])
        class AES(object):
            def __init__(self, userkey):
                self._blocksize = len(userkey)
                if (self._blocksize != 16) and (self._blocksize != 24) and (self._blocksize != 32) :
                    raise ADEPTError('AES improper key used')
                key = self._key = AES_KEY()
                rv = AES_set_decrypt_key(userkey, len(userkey) * 8, key)
                if rv < 0:
                    raise ADEPTError('Failed to initialize AES key')
            def decrypt(self, data):
                out = create_string_buffer(len(data))
                iv = ("\x00" * self._blocksize)
                rv = AES_cbc_encrypt(data, out, len(data), self._key, iv, 0)
                if rv == 0:
                    raise ADEPTError('AES decryption failed')
                return out.raw
        return AES

    def _load_crypto_pycrypto():
        from Crypto.Cipher import AES as _AES
        class AES(object):
            def __init__(self, key):
                self._aes = _AES.new(key, _AES.MODE_CBC, '\x00'*16)
            def decrypt(self, data):
                return self._aes.decrypt(data)
        return AES

    def _load_crypto():
        AES = None
        for loader in (_load_crypto_pycrypto, _load_crypto_libcrypto):
            try:
                AES = loader()
                break
            except (ImportError, ADEPTError):
                pass
        return AES

    AES = _load_crypto()


    DEVICE_KEY_PATH = r'Software\Adobe\Adept\Device'
    PRIVATE_LICENCE_KEY_PATH = r'Software\Adobe\Adept\Activation'

    MAX_PATH = 255

    kernel32 = windll.kernel32
    advapi32 = windll.advapi32
    crypt32 = windll.crypt32

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
            GetVolumeInformationW(
                path, None, 0, byref(vsn), None, None, None, 0)
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

    PAGE_EXECUTE_READWRITE = 0x40
    MEM_COMMIT  = 0x1000
    MEM_RESERVE = 0x2000

    def VirtualAlloc():
        _VirtualAlloc = kernel32.VirtualAlloc
        _VirtualAlloc.argtypes = [LPVOID, c_size_t, DWORD, DWORD]
        _VirtualAlloc.restype = LPVOID
        def VirtualAlloc(addr, size, alloctype=(MEM_COMMIT | MEM_RESERVE),
                         protect=PAGE_EXECUTE_READWRITE):
            return _VirtualAlloc(addr, size, alloctype, protect)
        return VirtualAlloc
    VirtualAlloc = VirtualAlloc()

    MEM_RELEASE = 0x8000

    def VirtualFree():
        _VirtualFree = kernel32.VirtualFree
        _VirtualFree.argtypes = [LPVOID, c_size_t, DWORD]
        _VirtualFree.restype = BOOL
        def VirtualFree(addr, size=0, freetype=MEM_RELEASE):
            return _VirtualFree(addr, size, freetype)
        return VirtualFree
    VirtualFree = VirtualFree()

    class NativeFunction(object):
        def __init__(self, restype, argtypes, insns):
            self._buf = buf = VirtualAlloc(None, len(insns))
            memmove(buf, insns, len(insns))
            ftype = CFUNCTYPE(restype, *argtypes)
            self._native = ftype(buf)

        def __call__(self, *args):
            return self._native(*args)

        def __del__(self):
            if self._buf is not None:
                VirtualFree(self._buf)
                self._buf = None

    if struct.calcsize("P") == 4:
        CPUID0_INSNS = (
            "\x53"             # push   %ebx
            "\x31\xc0"         # xor    %eax,%eax
            "\x0f\xa2"         # cpuid
            "\x8b\x44\x24\x08" # mov    0x8(%esp),%eax
            "\x89\x18"         # mov    %ebx,0x0(%eax)
            "\x89\x50\x04"     # mov    %edx,0x4(%eax)
            "\x89\x48\x08"     # mov    %ecx,0x8(%eax)
            "\x5b"             # pop    %ebx
            "\xc3"             # ret
        )
        CPUID1_INSNS = (
            "\x53"             # push   %ebx
            "\x31\xc0"         # xor    %eax,%eax
            "\x40"             # inc    %eax
            "\x0f\xa2"         # cpuid
            "\x5b"             # pop    %ebx
            "\xc3"             # ret
        )
    else:
        CPUID0_INSNS = (
            "\x49\x89\xd8"     # mov    %rbx,%r8
            "\x49\x89\xc9"     # mov    %rcx,%r9
            "\x48\x31\xc0"     # xor    %rax,%rax
            "\x0f\xa2"         # cpuid
            "\x4c\x89\xc8"     # mov    %r9,%rax
            "\x89\x18"         # mov    %ebx,0x0(%rax)
            "\x89\x50\x04"     # mov    %edx,0x4(%rax)
            "\x89\x48\x08"     # mov    %ecx,0x8(%rax)
            "\x4c\x89\xc3"     # mov    %r8,%rbx
            "\xc3"             # retq
        )
        CPUID1_INSNS = (
            "\x53"             # push   %rbx
            "\x48\x31\xc0"     # xor    %rax,%rax
            "\x48\xff\xc0"     # inc    %rax
            "\x0f\xa2"         # cpuid
            "\x5b"             # pop    %rbx
            "\xc3"             # retq
        )

    def cpuid0():
        _cpuid0 = NativeFunction(None, [c_char_p], CPUID0_INSNS)
        buf = create_string_buffer(12)
        def cpuid0():
            _cpuid0(buf)
            return buf.raw
        return cpuid0
    cpuid0 = cpuid0()

    cpuid1 = NativeFunction(c_uint, [], CPUID1_INSNS)

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

    def retrieve_keys():
        if AES is None:
            raise ADEPTError("PyCrypto or OpenSSL must be installed")
        root = GetSystemDirectory().split('\\')[0] + '\\'
        serial = GetVolumeSerialNumber(root)
        vendor = cpuid0()
        signature = struct.pack('>I', cpuid1())[1:]
        user = GetUserName()
        entropy = struct.pack('>I12s3s13s', serial, vendor, signature, user)
        cuser = winreg.HKEY_CURRENT_USER
        try:
            regkey = winreg.OpenKey(cuser, DEVICE_KEY_PATH)
        except WindowsError:
            raise ADEPTError("Adobe Digital Editions not activated")
        device = winreg.QueryValueEx(regkey, 'key')[0]
        keykey = CryptUnprotectData(device, entropy)
        userkey = None
        keys = []
        try:
            plkroot = winreg.OpenKey(cuser, PRIVATE_LICENCE_KEY_PATH)
        except WindowsError:
            raise ADEPTError("Could not locate ADE activation")
        for i in xrange(0, 16):
            try:
                plkparent = winreg.OpenKey(plkroot, "%04d" % (i,))
            except WindowsError:
                break
            ktype = winreg.QueryValueEx(plkparent, None)[0]
            if ktype != 'credentials':
                continue
            for j in xrange(0, 16):
                try:
                    plkkey = winreg.OpenKey(plkparent, "%04d" % (j,))
                except WindowsError:
                    break
                ktype = winreg.QueryValueEx(plkkey, None)[0]
                if ktype != 'privateLicenseKey':
                    continue
                userkey = winreg.QueryValueEx(plkkey, 'value')[0]
                userkey = userkey.decode('base64')
                aes = AES(keykey)
                userkey = aes.decrypt(userkey)
                userkey = userkey[26:-ord(userkey[-1])]
                keys.append(userkey)
        if len(keys) == 0:
            raise ADEPTError('Could not locate privateLicenseKey')
        return keys
        

elif isosx:
    import xml.etree.ElementTree as etree
    import subprocess

    NSMAP = {'adept': 'http://ns.adobe.com/adept',
             'enc': 'http://www.w3.org/2001/04/xmlenc#'}

    def findActivationDat():
        home = os.getenv('HOME')
        cmdline = 'find "' + home + '/Library/Application Support/Adobe/Digital Editions" -name "activation.dat"'
        cmdline = cmdline.encode(sys.getfilesystemencoding())
        p2 = subprocess.Popen(cmdline, shell=True, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=False)
        out1, out2 = p2.communicate()
        reslst = out1.split('\n')
        cnt = len(reslst)
        for j in xrange(cnt):
            resline = reslst[j]
            pp = resline.find('activation.dat')
            if pp >= 0:
                ActDatPath = resline
                break
        if os.path.exists(ActDatPath):
            return ActDatPath
        return None

    def retrieve_keys():
        actpath = findActivationDat()
        if actpath is None:
            raise ADEPTError("Could not locate ADE activation")
        tree = etree.parse(actpath)
        adept = lambda tag: '{%s}%s' % (NSMAP['adept'], tag)
        expr = '//%s/%s' % (adept('credentials'), adept('privateLicenseKey'))
        userkey = tree.findtext(expr)
        userkey = userkey.decode('base64')
        userkey = userkey[26:]
        return [userkey]

else:
    def retrieve_keys(keypath):
        raise ADEPTError("This script only supports Windows and Mac OS X.")
        return []
        
def retrieve_key(keypath):
    keys = retrieve_keys()
    with open(keypath, 'wb') as f:
        f.write(keys[0])
    return True

def extractKeyfile(keypath):
    try:
        success = retrieve_key(keypath)
    except ADEPTError, e:
        print "Key generation Error: " + str(e)
        return 1
    except Exception, e:
        print "General Error: " + str(e)
        return 1
    if not success:
        return 1
    return 0


def cli_main(argv=sys.argv):
    keypath = argv[1]
    return extractKeyfile(keypath)


def main(argv=sys.argv):
    import Tkinter
    import Tkconstants
    import tkMessageBox
    import traceback

    class ExceptionDialog(Tkinter.Frame):
        def __init__(self, root, text):
            Tkinter.Frame.__init__(self, root, border=5)
            label = Tkinter.Label(self, text="Unexpected error:",
                                  anchor=Tkconstants.W, justify=Tkconstants.LEFT)
            label.pack(fill=Tkconstants.X, expand=0)
            self.text = Tkinter.Text(self)
            self.text.pack(fill=Tkconstants.BOTH, expand=1)
    
            self.text.insert(Tkconstants.END, text)


    root = Tkinter.Tk()
    root.withdraw()
    progname = os.path.basename(argv[0])
    keypath = os.path.abspath("adeptkey.der")
    success = False
    try:
        success = retrieve_key(keypath)
    except ADEPTError, e:
        tkMessageBox.showerror("ADEPT Key", "Error: " + str(e))
    except Exception:
        root.wm_state('normal')
        root.title('ADEPT Key')
        text = traceback.format_exc()
        ExceptionDialog(root, text).pack(fill=Tkconstants.BOTH, expand=1)
        root.mainloop()
    if not success:
        return 1
    tkMessageBox.showinfo(
        "ADEPT Key", "Key successfully retrieved to %s" % (keypath))
    return 0

if __name__ == '__main__':
    if len(sys.argv) > 1:
        sys.exit(cli_main())
    sys.exit(main())
