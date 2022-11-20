# This is based on https://github.com/DanielStutzbach/winreg_unicode
# The original _winreg in Python2 doesn't support unicode.
# This causes issues if there's unicode chars in the username needed to decrypt the key.

'''
Copyright 2010 Stutzbach Enterprises, LLC (daniel@stutzbachenterprises.com)

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

   1. Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
   2. Redistributions in binary form must reproduce the above
      copyright notice, this list of conditions and the following
      disclaimer in the documentation and/or other materials provided
      with the distribution.
   3. The name of the author may not be used to endorse or promote
      products derived from this software without specific prior written
      permission.

THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT,
INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
'''

import ctypes, ctypes.wintypes

ERROR_SUCCESS = 0
ERROR_MORE_DATA = 234

KEY_READ = 0x20019

REG_NONE = 0
REG_SZ = 1
REG_EXPAND_SZ = 2
REG_BINARY = 3
REG_DWORD = 4
REG_DWORD_BIG_ENDIAN = 5
REG_DWORD_LITTLE_ENDIAN = 4
REG_LINK = 6
REG_MULTI_SZ = 7
REG_RESOURCE_LIST = 8
REG_FULL_RESOURCE_DESCRIPTOR = 9
REG_RESOURCE_REQUIREMENTS_LIST = 10

c_HKEY = ctypes.c_void_p
DWORD = ctypes.wintypes.DWORD
BYTE = ctypes.wintypes.BYTE
LPDWORD = ctypes.POINTER(DWORD)
LPBYTE = ctypes.POINTER(BYTE)

advapi32 = ctypes.windll.advapi32

class FILETIME(ctypes.Structure):
    _fields_ = [("dwLowDateTime", DWORD),
                ("dwHighDateTime", DWORD)]

RegCloseKey = advapi32.RegCloseKey
RegCloseKey.restype = ctypes.c_long
RegCloseKey.argtypes = [c_HKEY]

RegOpenKeyEx = advapi32.RegOpenKeyExW
RegOpenKeyEx.restype = ctypes.c_long
RegOpenKeyEx.argtypes = [c_HKEY, ctypes.c_wchar_p, ctypes.c_ulong,
                         ctypes.c_ulong, ctypes.POINTER(c_HKEY)]

RegQueryInfoKey = advapi32.RegQueryInfoKeyW
RegQueryInfoKey.restype = ctypes.c_long
RegQueryInfoKey.argtypes = [c_HKEY, ctypes.c_wchar_p, LPDWORD, LPDWORD,
                            LPDWORD, LPDWORD, LPDWORD, LPDWORD,
                            LPDWORD, LPDWORD, LPDWORD,
                            ctypes.POINTER(FILETIME)]

RegEnumValue = advapi32.RegEnumValueW
RegEnumValue.restype = ctypes.c_long
RegEnumValue.argtypes = [c_HKEY, DWORD, ctypes.c_wchar_p, LPDWORD,
                         LPDWORD, LPDWORD, LPBYTE, LPDWORD]

RegEnumKeyEx = advapi32.RegEnumKeyExW
RegEnumKeyEx.restype = ctypes.c_long
RegEnumKeyEx.argtypes = [c_HKEY, DWORD, ctypes.c_wchar_p, LPDWORD,
                         LPDWORD, ctypes.c_wchar_p, LPDWORD,
                         ctypes.POINTER(FILETIME)]

RegQueryValueEx = advapi32.RegQueryValueExW
RegQueryValueEx.restype = ctypes.c_long
RegQueryValueEx.argtypes = [c_HKEY, ctypes.c_wchar_p, LPDWORD, LPDWORD,
                            LPBYTE, LPDWORD]

def check_code(code):
    if code == ERROR_SUCCESS:
        return
    raise ctypes.WinError(2)

class HKEY(object):
    def __init__(self):
        self.hkey = c_HKEY()

    def __enter__(self):
        return self

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        self.Close()
        return False

    def Detach(self):
        rv = self.cast(self.hkey, self.c_ulong).value
        self.hkey = c_HKEY()
        return rv

    def __nonzero__(self):
        return bool(self.hkey)

    def Close(self):
        if not self.hkey:
            return
        if RegCloseKey is None or check_code is None or c_HKEY is None:
            return # globals become None during exit
        rc = RegCloseKey(self.hkey)
        self.hkey = c_HKEY()
        check_code(rc)

    def __del__(self):
        self.Close()

class RootHKEY(ctypes.Structure):
    def __init__(self, value):
        self.hkey = c_HKEY(value)

    def Close(self):
        pass

HKEY_CLASSES_ROOT = RootHKEY(0x80000000)
HKEY_CURRENT_USER = RootHKEY(0x80000001)
HKEY_LOCAL_MACHINE = RootHKEY(0x80000002)
HKEY_USERS = RootHKEY(0x80000003)
HKEY_PERFORMANCE_DATA = RootHKEY(0x80000004)
HKEY_CURRENT_CONFIG = RootHKEY(0x80000005)
HKEY_DYN_DATA = RootHKEY(0x80000006)

def OpenKey(key, sub_key):
    new_key = HKEY()
    rc = RegOpenKeyEx(key.hkey, sub_key, 0, KEY_READ,
                      ctypes.cast(ctypes.byref(new_key.hkey),
                                  ctypes.POINTER(c_HKEY)))
    check_code(rc)
    return new_key

def QueryInfoKey(key):
    null = LPDWORD()
    num_sub_keys = DWORD()
    num_values = DWORD()
    ft = FILETIME()
    rc = RegQueryInfoKey(key.hkey, ctypes.c_wchar_p(), null, null,
                         ctypes.byref(num_sub_keys), null, null,
                         ctypes.byref(num_values), null, null, null,
                         ctypes.byref(ft))
    check_code(rc)
    return (num_sub_keys.value, num_values.value,
            ft.dwLowDateTime | (ft.dwHighDateTime << 32))

def EnumValue(key, index):
    null = LPDWORD()
    value_size = DWORD()
    data_size = DWORD()
    rc = RegQueryInfoKey(key.hkey, ctypes.c_wchar_p(), null, null, null,
                         null, null, null,
                         ctypes.byref(value_size), ctypes.byref(data_size),
                         null, ctypes.POINTER(FILETIME)())
    check_code(rc)
    value_size.value += 1
    data_size.value += 1

    value = ctypes.create_unicode_buffer(value_size.value)

    while True:
        data = ctypes.create_string_buffer(data_size.value)

        tmp_value_size = DWORD(value_size.value)
        tmp_data_size = DWORD(data_size.value)
        typ = DWORD()
        rc = RegEnumValue(key.hkey, index,
                          ctypes.cast(value, ctypes.c_wchar_p),
                          ctypes.byref(tmp_value_size), null,
                          ctypes.byref(typ),
                          ctypes.cast(data, LPBYTE),
                          ctypes.byref(tmp_data_size))

        if rc != ERROR_MORE_DATA:
            break

        data_size.value *= 2

    check_code(rc)
    return (value.value, Reg2Py(data, tmp_data_size.value, typ.value),
            typ.value)

def split_multi_sz(data, size):
    if size == 0:
        return []
    Q = size
    P = 0
    rv = []
    while P < Q and data[P].value != u'\0':
        rv.append[P]
        while P < Q and data[P].value != u'\0':
            P += 1
        P += 1
    rv.append(size)
    return [ctypes.wstring_at(ctypes.pointer(data[rv[i]]),
                              rv[i+1] - rv[i]).rstrip(u'\x00')
            for i in range(len(rv)-1)]

def Reg2Py(data, size, typ):
    if typ == REG_DWORD:
        if size == 0:
            return 0
        return ctypes.cast(data, ctypes.POINTER(ctypes.c_int)).contents.value
    elif typ == REG_SZ or typ == REG_EXPAND_SZ:
        return ctypes.wstring_at(data, size // 2).rstrip(u'\x00')
    elif typ == REG_MULTI_SZ:
        return split_multi_sz(ctypes.cast(data, ctypes.c_wchar_p), size // 2)
    else:
        if size == 0:
            return None
        return ctypes.string_at(data, size)

def EnumKey(key, index):
    tmpbuf = ctypes.create_unicode_buffer(257)
    length = DWORD(257)
    rc = RegEnumKeyEx(key.hkey, index,
                      ctypes.cast(tmpbuf, ctypes.c_wchar_p),
                      ctypes.byref(length),
                      LPDWORD(), ctypes.c_wchar_p(), LPDWORD(),
                      ctypes.POINTER(FILETIME)())
    check_code(rc)
    return ctypes.wstring_at(tmpbuf, length.value).rstrip(u'\x00')

def QueryValueEx(key, value_name):
    size = 256
    typ = DWORD()
    while True:
        tmp_size = DWORD(size)
        buf = ctypes.create_string_buffer(size)
        rc = RegQueryValueEx(key.hkey, value_name, LPDWORD(),
                             ctypes.byref(typ),
                             ctypes.cast(buf, LPBYTE), ctypes.byref(tmp_size))
        if rc != ERROR_MORE_DATA:
            break

        size *= 2
    check_code(rc)
    return (Reg2Py(buf, tmp_size.value, typ.value), typ.value)

__all__ = ['OpenKey', 'QueryInfoKey', 'EnumValue', 'EnumKey', 'QueryValueEx',
           'HKEY_CLASSES_ROOT', 'HKEY_CURRENT_USER', 'HKEY_LOCAL_MACHINE',
           'HKEY_USERS', 'HKEY_PERFORMANCE_DATA', 'HKEY_CURRENT_CONFIG',
           'HKEY_DYN_DATA', 'REG_NONE', 'REG_SZ', 'REG_EXPAND_SZ',
           'REG_BINARY', 'REG_DWORD', 'REG_DWORD_BIG_ENDIAN',
           'REG_DWORD_LITTLE_ENDIAN', 'REG_LINK', 'REG_MULTI_SZ',
           'REG_RESOURCE_LIST', 'REG_FULL_RESOURCE_DESCRIPTOR',
           'REG_RESOURCE_REQUIREMENTS_LIST']