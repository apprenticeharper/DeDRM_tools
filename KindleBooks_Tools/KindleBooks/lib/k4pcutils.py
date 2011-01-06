# K4PC Windows specific routines

from __future__ import with_statement

import sys, os

from ctypes import windll, c_char_p, c_wchar_p, c_uint, POINTER, byref, \
    create_unicode_buffer, create_string_buffer, CFUNCTYPE, addressof, \
    string_at, Structure, c_void_p, cast

import _winreg as winreg

import traceback

MAX_PATH = 255

kernel32 = windll.kernel32
advapi32 = windll.advapi32
crypt32 = windll.crypt32


# Various character maps used to decrypt books. Probably supposed to act as obfuscation
charMap1 = "n5Pr6St7Uv8Wx9YzAb0Cd1Ef2Gh3Jk4M"
charMap2 = "AaZzB0bYyCc1XxDdW2wEeVv3FfUuG4g-TtHh5SsIiR6rJjQq7KkPpL8lOoMm9Nn_"
charMap3 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
charMap4 = "ABCDEFGHIJKLMNPQRSTUVWXYZ123456789"

class DrmException(Exception):
    pass
    

class DataBlob(Structure):
    _fields_ = [('cbData', c_uint),
                ('pbData', c_void_p)]
DataBlob_p = POINTER(DataBlob)


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
    def GetVolumeSerialNumber(path = GetSystemDirectory().split('\\')[0] + '\\'):
        vsn = c_uint(0)
        GetVolumeInformationW(path, None, 0, byref(vsn), None, None, None, 0)
        return str(vsn.value)
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
            raise DrmException("Failed to Unprotect Data")
        return string_at(outdata.pbData, outdata.cbData)
    return CryptUnprotectData
CryptUnprotectData = CryptUnprotectData()

#
# Locate and open the Kindle.info file.
#
def openKindleInfo(kInfoFile=None):
    if kInfoFile == None:
        regkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Folders\\")
        path = winreg.QueryValueEx(regkey, 'Local AppData')[0]
        kinfopath = path +'\\Amazon\\Kindle For PC\\{AMAwzsaPaaZAzmZzZQzgZCAkZ3AjA_AY}\\kindle.info'
        if not os.path.isfile(kinfopath):
            raise DrmException('Error: kindle.info file can not be found')
        return open(kinfopath,'r')
    else:
        if not os.path.isfile(kInfoFile):
            raise DrmException('Error: kindle.info file can not be found')
        return open(kInfoFile, 'r')
