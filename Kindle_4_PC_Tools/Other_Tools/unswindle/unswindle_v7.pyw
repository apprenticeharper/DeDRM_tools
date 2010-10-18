#! /usr/bin/python
# -*- coding: utf-8 -*-

# unswindle.pyw, version 7
# Copyright © 2009-2010 i♥cabbages

# Released under the terms of the GNU General Public Licence, version 3 or
# later.  <http://www.gnu.org/licenses/>

# Before running this program, you must first install Python 2.6 from
# <http://www.python.org/download/>.  Save this script file as unswindle.pyw.
# Find and save in the same directory a copy of mobidedrm.py.  Double-click on
# unswindle.pyw.  It will run Kindle For PC.  Open the book you want to
# decrypt.  Close Kindle For PC.  A dialog will open allowing you to select the
# output file.  And you're done!

# Revision history:
#   1 - Initial release
#   2 - Fixes to work properly on Windows versions >XP
#   3 - Fix minor bug in path extraction
#   4 - Fix error opening threads; detect Topaz books;
#       detect unsupported versions of K4PC
#   5 - Work with new (20091222) version of K4PC
#   6 - Detect and just copy DRM-free books
#   7 - Work with new (20100629) version of K4PC

"""
Decrypt Kindle For PC encrypted Mobipocket books.
"""

from __future__ import with_statement

__license__ = 'GPL v3'

import sys
import os
import re
import tempfile
import shutil
import subprocess
import struct
import hashlib
import ctypes
from ctypes import *
from ctypes.wintypes import *
import binascii
import _winreg as winreg
import Tkinter
import Tkconstants
import tkMessageBox
import tkFileDialog
import traceback

#
# _extrawintypes.py

UBYTE = c_ubyte
ULONG_PTR = POINTER(ULONG)
PULONG = ULONG_PTR
PVOID = LPVOID
LPCTSTR = LPTSTR = c_wchar_p
LPBYTE = c_char_p
SIZE_T = c_uint
SIZE_T_p = POINTER(SIZE_T)

#
# _ntdll.py

NTSTATUS = DWORD

ntdll = windll.ntdll

class PROCESS_BASIC_INFORMATION(Structure):
    _fields_ = [('Reserved1', PVOID),
                ('PebBaseAddress', PVOID),
                ('Reserved2', PVOID * 2),
                ('UniqueProcessId', ULONG_PTR),
                ('Reserved3', PVOID)]

# NTSTATUS WINAPI NtQueryInformationProcess(
#   __in       HANDLE ProcessHandle,
#   __in       PROCESSINFOCLASS ProcessInformationClass,
#   __out      PVOID ProcessInformation,
#   __in       ULONG ProcessInformationLength,
#   __out_opt  PULONG ReturnLength
# );
NtQueryInformationProcess = ntdll.NtQueryInformationProcess
NtQueryInformationProcess.argtypes = [HANDLE, DWORD, PVOID, ULONG, PULONG]
NtQueryInformationProcess.restype = NTSTATUS

#
# _kernel32.py

INFINITE = 0xffffffff

CREATE_UNICODE_ENVIRONMENT = 0x00000400
DEBUG_ONLY_THIS_PROCESS = 0x00000002
DEBUG_PROCESS = 0x00000001

THREAD_GET_CONTEXT = 0x0008
THREAD_QUERY_INFORMATION = 0x0040
THREAD_SET_CONTEXT = 0x0010
THREAD_SET_INFORMATION = 0x0020

EXCEPTION_BREAKPOINT = 0x80000003
EXCEPTION_SINGLE_STEP = 0x80000004
EXCEPTION_ACCESS_VIOLATION = 0xC0000005

DBG_CONTINUE = 0x00010002L
DBG_EXCEPTION_NOT_HANDLED = 0x80010001L

EXCEPTION_DEBUG_EVENT = 1
CREATE_THREAD_DEBUG_EVENT = 2
CREATE_PROCESS_DEBUG_EVENT = 3
EXIT_THREAD_DEBUG_EVENT = 4
EXIT_PROCESS_DEBUG_EVENT = 5
LOAD_DLL_DEBUG_EVENT = 6
UNLOAD_DLL_DEBUG_EVENT = 7
OUTPUT_DEBUG_STRING_EVENT = 8
RIP_EVENT = 9

class DataBlob(Structure):
    _fields_ = [('cbData', c_uint),
                ('pbData', c_void_p)]
DataBlob_p = POINTER(DataBlob)

class SECURITY_ATTRIBUTES(Structure):
    _fields_ = [('nLength', DWORD),
                ('lpSecurityDescriptor', LPVOID),
                ('bInheritHandle', BOOL)]
LPSECURITY_ATTRIBUTES = POINTER(SECURITY_ATTRIBUTES)

class STARTUPINFO(Structure):
    _fields_ = [('cb', DWORD),
                ('lpReserved', LPTSTR),
                ('lpDesktop', LPTSTR),
                ('lpTitle', LPTSTR),
                ('dwX', DWORD),
                ('dwY', DWORD),
                ('dwXSize', DWORD),
                ('dwYSize', DWORD),
                ('dwXCountChars', DWORD),
                ('dwYCountChars', DWORD),
                ('dwFillAttribute', DWORD),
                ('dwFlags', DWORD),
                ('wShowWindow', WORD),
                ('cbReserved2', WORD),
                ('lpReserved2', LPBYTE),
                ('hStdInput', HANDLE),
                ('hStdOutput', HANDLE),
                ('hStdError', HANDLE)]
LPSTARTUPINFO = POINTER(STARTUPINFO)

class PROCESS_INFORMATION(Structure):
    _fields_ = [('hProcess', HANDLE),
                ('hThread', HANDLE),
                ('dwProcessId', DWORD),
                ('dwThreadId', DWORD)]
LPPROCESS_INFORMATION = POINTER(PROCESS_INFORMATION)

EXCEPTION_MAXIMUM_PARAMETERS = 15
class EXCEPTION_RECORD(Structure):
    pass
EXCEPTION_RECORD._fields_ = [
    ('ExceptionCode', DWORD),
    ('ExceptionFlags', DWORD),
    ('ExceptionRecord', POINTER(EXCEPTION_RECORD)),
    ('ExceptionAddress', LPVOID),
    ('NumberParameters', DWORD),
    ('ExceptionInformation', ULONG_PTR * EXCEPTION_MAXIMUM_PARAMETERS)]

class EXCEPTION_DEBUG_INFO(Structure):
    _fields_ = [('ExceptionRecord', EXCEPTION_RECORD),
                ('dwFirstChance', DWORD)]

class CREATE_THREAD_DEBUG_INFO(Structure):
    _fields_ = [('hThread', HANDLE),
                ('lpThreadLocalBase', LPVOID),
                ('lpStartAddress', LPVOID)]

class CREATE_PROCESS_DEBUG_INFO(Structure):
    _fields_ = [('hFile', HANDLE),
                ('hProcess', HANDLE),
                ('hThread', HANDLE),
                ('dwDebugInfoFileOffset', DWORD),
                ('nDebugInfoSize', DWORD),
                ('lpThreadLocalBase', LPVOID),
                ('lpStartAddress', LPVOID),
                ('lpImageName', LPVOID),
                ('fUnicode', WORD)]

class EXIT_THREAD_DEBUG_INFO(Structure):
    _fields_ = [('dwExitCode', DWORD)]

class EXIT_PROCESS_DEBUG_INFO(Structure):
    _fields_ = [('dwExitCode', DWORD)]

class LOAD_DLL_DEBUG_INFO(Structure):
    _fields_ = [('hFile', HANDLE),
                ('lpBaseOfDll', LPVOID),
                ('dwDebugInfoFileOffset', DWORD),
                ('nDebugInfoSize', DWORD),
                ('lpImageName', LPVOID),
                ('fUnicode', WORD)]

class UNLOAD_DLL_DEBUG_INFO(Structure):
    _fields_ = [('lpBaseOfDll', LPVOID)]

class OUTPUT_DEBUG_STRING_INFO(Structure):
    _fields_ = [('lpDebugStringData', LPSTR),
                ('fUnicode', WORD),
                ('nDebugStringLength', WORD)]

class RIP_INFO(Structure):
    _fields_ = [('dwError', DWORD),
                ('dwType', DWORD)]

class _U(Union):
    _fields_ = [('Exception', EXCEPTION_DEBUG_INFO),
                ('CreateThread', CREATE_THREAD_DEBUG_INFO),
                ('CreateProcessInfo', CREATE_PROCESS_DEBUG_INFO),
                ('ExitThread', EXIT_THREAD_DEBUG_INFO),
                ('ExitProcess', EXIT_PROCESS_DEBUG_INFO),
                ('LoadDll', LOAD_DLL_DEBUG_INFO),
                ('UnloadDll', UNLOAD_DLL_DEBUG_INFO),
                ('DebugString', OUTPUT_DEBUG_STRING_INFO),
                ('RipInfo', RIP_INFO)]

class DEBUG_EVENT(Structure):
    _anonymous_ = ('u',)
    _fields_ = [('dwDebugEventCode', DWORD),
                ('dwProcessId', DWORD),
                ('dwThreadId', DWORD),
                ('u', _U)]
LPDEBUG_EVENT = POINTER(DEBUG_EVENT)

CONTEXT_X86 = 0x00010000
CONTEXT_i386 = CONTEXT_X86
CONTEXT_i486 = CONTEXT_X86

CONTEXT_CONTROL = (CONTEXT_i386 | 0x0001) # SS:SP, CS:IP, FLAGS, BP
CONTEXT_INTEGER = (CONTEXT_i386 | 0x0002) # AX, BX, CX, DX, SI, DI
CONTEXT_SEGMENTS = (CONTEXT_i386 | 0x0004) # DS, ES, FS, GS
CONTEXT_FLOATING_POINT = (CONTEXT_i386 | 0x0008L) # 387 state
CONTEXT_DEBUG_REGISTERS =  (CONTEXT_i386 | 0x0010L) # DB 0-3,6,7
CONTEXT_EXTENDED_REGISTERS =  (CONTEXT_i386 | 0x0020L)
CONTEXT_FULL = (CONTEXT_CONTROL | CONTEXT_INTEGER | CONTEXT_SEGMENTS)
CONTEXT_ALL = (CONTEXT_CONTROL | CONTEXT_INTEGER | CONTEXT_SEGMENTS |
               CONTEXT_FLOATING_POINT | CONTEXT_DEBUG_REGISTERS |
               CONTEXT_EXTENDED_REGISTERS)

SIZE_OF_80387_REGISTERS = 80
class FLOATING_SAVE_AREA(Structure):
    _fields_ = [('ControlWord', DWORD),
                ('StatusWord', DWORD),
                ('TagWord', DWORD),
                ('ErrorOffset', DWORD),
                ('ErrorSelector', DWORD),
                ('DataOffset', DWORD),
                ('DataSelector', DWORD),
                ('RegisterArea', BYTE * SIZE_OF_80387_REGISTERS),
                ('Cr0NpxState', DWORD)]

MAXIMUM_SUPPORTED_EXTENSION = 512
class CONTEXT(Structure):
    _fields_ = [('ContextFlags', DWORD),
                ('Dr0', DWORD),
                ('Dr1', DWORD),
                ('Dr2', DWORD),
                ('Dr3', DWORD),
                ('Dr6', DWORD),
                ('Dr7', DWORD),
                ('FloatSave', FLOATING_SAVE_AREA),
                ('SegGs', DWORD),
                ('SegFs', DWORD),
                ('SegEs', DWORD),
                ('SegDs', DWORD),
                ('Edi', DWORD),
                ('Esi', DWORD),
                ('Ebx', DWORD),
                ('Edx', DWORD),
                ('Ecx', DWORD),
                ('Eax', DWORD),
                ('Ebp', DWORD),
                ('Eip', DWORD),
                ('SegCs', DWORD),
                ('EFlags', DWORD),
                ('Esp', DWORD),
                ('SegSs', DWORD),
                ('ExtendedRegisters', BYTE * MAXIMUM_SUPPORTED_EXTENSION)]
LPCONTEXT = POINTER(CONTEXT)

class LDT_ENTRY(Structure):
    _fields_ = [('LimitLow', WORD),
                ('BaseLow',  WORD),
                ('BaseMid', UBYTE),
                ('Flags1', UBYTE),
                ('Flags2', UBYTE),
                ('BaseHi', UBYTE)]
LPLDT_ENTRY = POINTER(LDT_ENTRY)

kernel32 = windll.kernel32

# BOOL WINAPI CloseHandle(
#   __in  HANDLE hObject
# );
CloseHandle = kernel32.CloseHandle
CloseHandle.argtypes = [HANDLE]
CloseHandle.restype = BOOL

# BOOL WINAPI CreateProcess(
#   __in_opt     LPCTSTR lpApplicationName,
#   __inout_opt  LPTSTR lpCommandLine,
#   __in_opt     LPSECURITY_ATTRIBUTES lpProcessAttributes,
#   __in_opt     LPSECURITY_ATTRIBUTES lpThreadAttributes,
#   __in         BOOL bInheritHandles,
#   __in         DWORD dwCreationFlags,
#   __in_opt     LPVOID lpEnvironment,
#   __in_opt     LPCTSTR lpCurrentDirectory,
#   __in         LPSTARTUPINFO lpStartupInfo,
#   __out        LPPROCESS_INFORMATION lpProcessInformation
# );
CreateProcess = kernel32.CreateProcessW
CreateProcess.argtypes = [LPCTSTR, LPTSTR, LPSECURITY_ATTRIBUTES,
                          LPSECURITY_ATTRIBUTES, BOOL, DWORD, LPVOID, LPCTSTR,
                          LPSTARTUPINFO, LPPROCESS_INFORMATION]
CreateProcess.restype = BOOL

# HANDLE WINAPI OpenThread(
#   __in  DWORD dwDesiredAccess,
#   __in  BOOL bInheritHandle,
#   __in  DWORD dwThreadId
# );
OpenThread = kernel32.OpenThread
OpenThread.argtypes = [DWORD, BOOL, DWORD]
OpenThread.restype = HANDLE

# BOOL WINAPI ContinueDebugEvent(
#   __in  DWORD dwProcessId,
#   __in  DWORD dwThreadId,
#   __in  DWORD dwContinueStatus
# );
ContinueDebugEvent = kernel32.ContinueDebugEvent
ContinueDebugEvent.argtypes = [DWORD, DWORD, DWORD]
ContinueDebugEvent.restype = BOOL

# BOOL WINAPI DebugActiveProcess(
#   __in  DWORD dwProcessId
# );
DebugActiveProcess = kernel32.DebugActiveProcess
DebugActiveProcess.argtypes = [DWORD]
DebugActiveProcess.restype = BOOL

# BOOL WINAPI GetThreadContext(
#   __in     HANDLE hThread,
#   __inout  LPCONTEXT lpContext
# );
GetThreadContext = kernel32.GetThreadContext
GetThreadContext.argtypes = [HANDLE, LPCONTEXT]
GetThreadContext.restype = BOOL

# BOOL WINAPI GetThreadSelectorEntry(
#   __in   HANDLE hThread,
#   __in   DWORD dwSelector,
#   __out  LPLDT_ENTRY lpSelectorEntry
# );
GetThreadSelectorEntry = kernel32.GetThreadSelectorEntry
GetThreadSelectorEntry.argtypes = [HANDLE, DWORD, LPLDT_ENTRY]
GetThreadSelectorEntry.restype = BOOL

# BOOL WINAPI ReadProcessMemory(
#   __in   HANDLE hProcess,
#   __in   LPCVOID lpBaseAddress,
#   __out  LPVOID lpBuffer,
#   __in   SIZE_T nSize,
#   __out  SIZE_T *lpNumberOfBytesRead
# );
ReadProcessMemory = kernel32.ReadProcessMemory
ReadProcessMemory.argtypes = [HANDLE, LPCVOID, LPVOID, SIZE_T, SIZE_T_p]
ReadProcessMemory.restype = BOOL

# BOOL WINAPI SetThreadContext(
#   __in  HANDLE hThread,
#   __in  const CONTEXT *lpContext
# );
SetThreadContext = kernel32.SetThreadContext
SetThreadContext.argtypes = [HANDLE, LPCONTEXT]
SetThreadContext.restype = BOOL

# BOOL WINAPI WaitForDebugEvent(
#   __out  LPDEBUG_EVENT lpDebugEvent,
#   __in   DWORD dwMilliseconds
# );
WaitForDebugEvent = kernel32.WaitForDebugEvent
WaitForDebugEvent.argtypes = [LPDEBUG_EVENT, DWORD]
WaitForDebugEvent.restype = BOOL

# BOOL WINAPI WriteProcessMemory(
#   __in   HANDLE hProcess,
#   __in   LPVOID lpBaseAddress,
#   __in   LPCVOID lpBuffer,
#   __in   SIZE_T nSize,
#   __out  SIZE_T *lpNumberOfBytesWritten
# );
WriteProcessMemory = kernel32.WriteProcessMemory
WriteProcessMemory.argtypes = [HANDLE, LPVOID, LPCVOID, SIZE_T, SIZE_T_p]
WriteProcessMemory.restype = BOOL

# BOOL WINAPI FlushInstructionCache(
#   __in  HANDLE hProcess,
#   __in  LPCVOID lpBaseAddress,
#   __in  SIZE_T dwSize
# );
FlushInstructionCache = kernel32.FlushInstructionCache
FlushInstructionCache.argtypes = [HANDLE, LPCVOID, SIZE_T]
FlushInstructionCache.restype = BOOL


#
# debugger.py

FLAG_TRACE_BIT = 0x100

class DebuggerError(Exception):
    pass

class Debugger(object):
    def __init__(self, process_info):
        self.process_info = process_info
        self.pid = process_info.dwProcessId
        self.tid = process_info.dwThreadId
        self.hprocess = process_info.hProcess
        self.hthread = process_info.hThread
        self._threads = {self.tid: self.hthread}
        self._processes = {self.pid: self.hprocess}
        self._bps = {}
        self._inactive = {}

    def read_process_memory(self, addr, size=None, type=str):
        if issubclass(type, basestring):
            buf = ctypes.create_string_buffer(size)
            ref = buf
        else:
            size = ctypes.sizeof(type)
            buf = type()
            ref = byref(buf)
        copied = SIZE_T(0)
        rv = ReadProcessMemory(self.hprocess, addr, ref, size, byref(copied))
        if not rv:
            addr = getattr(addr, 'value', addr)
            raise DebuggerError("could not read memory @ 0x%08x" % (addr,))
        if copied.value != size:
            raise DebuggerError("insufficient memory read")
        if issubclass(type, basestring):
            return buf.raw
        return buf

    def set_bp(self, addr, callback, bytev=None):
        hprocess = self.hprocess
        if bytev is None:
            byte = self.read_process_memory(addr, type=ctypes.c_byte)
            bytev = byte.value
        else:
            byte = ctypes.c_byte(0)
        self._bps[addr] = (bytev, callback)
        byte.value = 0xcc
        copied = SIZE_T(0)
        rv = WriteProcessMemory(hprocess, addr, byref(byte), 1, byref(copied))
        if not rv:
            addr = getattr(addr, 'value', addr)
            raise DebuggerError("could not write memory @ 0x%08x" % (addr,))
        if copied.value != 1:
            raise DebuggerError("insufficient memory written")
        rv = FlushInstructionCache(hprocess, None, 0)
        if not rv:
            raise DebuggerError("could not flush instruction cache")
        return

    def _restore_bps(self):
        for addr, (bytev, callback) in self._inactive.items():
            self.set_bp(addr, callback, bytev=bytev)
        self._inactive.clear()

    def _handle_bp(self, addr):
        hprocess = self.hprocess
        hthread = self.hthread
        bytev, callback = self._inactive[addr] = self._bps.pop(addr)
        byte = ctypes.c_byte(bytev)
        copied = SIZE_T(0)
        rv = WriteProcessMemory(hprocess, addr, byref(byte), 1, byref(copied))
        if not rv:
            raise DebuggerError("could not write memory")
        if copied.value != 1:
            raise DebuggerError("insufficient memory written")
        rv = FlushInstructionCache(hprocess, None, 0)
        if not rv:
            raise DebuggerError("could not flush instruction cache")
        context = CONTEXT(ContextFlags=CONTEXT_FULL)
        rv = GetThreadContext(hthread, byref(context))
        if not rv:
            raise DebuggerError("could not get thread context")
        context.Eip = addr
        callback(self, context)
        context.EFlags |= FLAG_TRACE_BIT
        rv = SetThreadContext(hthread, byref(context))
        if not rv:
            raise DebuggerError("could not set thread context")
        return

    def _get_peb_address(self):
        hthread = self.hthread
        hprocess = self.hprocess
        try:
            pbi = PROCESS_BASIC_INFORMATION()
            rv = NtQueryInformationProcess(hprocess, 0, byref(pbi),
                                           sizeof(pbi), None)
            if rv != 0:
                raise DebuggerError("could not query process information")
            return pbi.PebBaseAddress
        except DebuggerError:
            pass
        try:
            context = CONTEXT(ContextFlags=CONTEXT_FULL)
            rv = GetThreadContext(hthread, byref(context))
            if not rv:
                raise DebuggerError("could not get thread context")
            entry = LDT_ENTRY()
            rv = GetThreadSelectorEntry(hthread, context.SegFs, byref(entry))
            if not rv:
                raise DebuggerError("could not get selector entry")
            low, mid, high = entry.BaseLow, entry.BaseMid, entry.BaseHi
            fsbase = low | (mid << 16) | (high << 24)
            pebaddr = self.read_process_memory(fsbase + 0x30, type=c_voidp)
            return pebaddr.value
        except DebuggerError:
            pass
        return 0x7ffdf000

    def get_base_address(self):
        addr = self._get_peb_address() + (2 * 4)
        baseaddr = self.read_process_memory(addr, type=c_voidp)
        return baseaddr.value

    def main_loop(self):
        event = DEBUG_EVENT()
        finished = False
        while not finished:
            rv = WaitForDebugEvent(byref(event), INFINITE)
            if not rv:
                raise DebuggerError("could not get debug event")
            self.pid = pid = event.dwProcessId
            self.tid = tid = event.dwThreadId
            self.hprocess = self._processes.get(pid, None)
            self.hthread = self._threads.get(tid, None)
            status = DBG_CONTINUE
            evid = event.dwDebugEventCode
            if evid == EXCEPTION_DEBUG_EVENT:
                first = event.Exception.dwFirstChance
                record = event.Exception.ExceptionRecord
                exid = record.ExceptionCode
                flags = record.ExceptionFlags
                addr = record.ExceptionAddress
                if exid == EXCEPTION_BREAKPOINT:
                    if addr in self._bps:
                        self._handle_bp(addr)
                elif exid == EXCEPTION_SINGLE_STEP:
                    self._restore_bps()
                else:
                    status = DBG_EXCEPTION_NOT_HANDLED
            elif evid == LOAD_DLL_DEBUG_EVENT:
                hfile = event.LoadDll.hFile
                if hfile is not None:
                    rv = CloseHandle(hfile)
                    if not rv:
                        raise DebuggerError("error closing file handle")
            elif evid == CREATE_THREAD_DEBUG_EVENT:
                info = event.CreateThread
                self.hthread = info.hThread
                self._threads[tid] = self.hthread
            elif evid == EXIT_THREAD_DEBUG_EVENT:
                hthread = self._threads.pop(tid, None)
                if hthread is not None:
                    rv = CloseHandle(hthread)
                    if not rv:
                        raise DebuggerError("error closing thread handle")
            elif evid == CREATE_PROCESS_DEBUG_EVENT:
                info = event.CreateProcessInfo
                self.hprocess = info.hProcess
                self._processes[pid] = self.hprocess
            elif evid == EXIT_PROCESS_DEBUG_EVENT:
                hprocess = self._processes.pop(pid, None)
                if hprocess is not None:
                    rv = CloseHandle(hprocess)
                    if not rv:
                        raise DebuggerError("error closing process handle")
                if pid == self.process_info.dwProcessId:
                    finished = True
            rv = ContinueDebugEvent(pid, tid, status)
            if not rv:
                raise DebuggerError("could not continue debug")
        return True


#
# unswindle.py

KINDLE_REG_KEY = \
    r'Software\Classes\Amazon.KindleForPC.content\shell\open\command'

class UnswindleError(Exception):
    pass

class PC1KeyGrabber(object):
    HOOKS = {
        'b9f7e422094b8c8966a0e881e6358116e03e5b7b': {
            0x004a719d: '_no_debugger_here',
            0x005a795b: '_no_debugger_here',
            0x0054f7e0: '_get_pc1_pid',
            0x004f9c79: '_get_book_path',
        },
        'd5124ee20dab10e44b41a039363f6143725a5417': {
            0x0041150d: '_i_like_wine',
            0x004a681d: '_no_debugger_here',
            0x005a438b: '_no_debugger_here',
            0x0054c9e0: '_get_pc1_pid',
            0x004f8ac9: '_get_book_path',
        },
        'd791f52dd2ecc68722212d801ad52cb79d1b6fc9': {
            0x0041724d: '_i_like_wine',
            0x004bfe3d: '_no_debugger_here',
            0x005bd9db: '_no_debugger_here',
            0x00565920: '_get_pc1_pid',
            0x0050fde9: '_get_book_path',
        },
    }

    MOBI_EXTENSIONS = set(['.prc', '.pdb', '.mobi', '.azw', '.az1', '.azw1'])

    @classmethod
    def supported_version(cls, hexdigest):
        return (hexdigest in cls.HOOKS)

    def _taddr(self, addr):
        return (addr - 0x00400000) + self.baseaddr

    def __init__(self, debugger, hexdigest):
        self.book_path = None
        self.book_pid = None
        self.baseaddr = debugger.get_base_address()
        hooks = self.HOOKS[hexdigest]
        for addr, mname in hooks.items():
            debugger.set_bp(self._taddr(addr), getattr(self, mname))

    def _i_like_wine(self, debugger, context):
        context.Eax = 1
        return

    def _no_debugger_here(self, debugger, context):
        context.Eip += 2
        context.Eax = 0
        return

    def _get_book_path(self, debugger, context):
        addr = debugger.read_process_memory(context.Esp, type=ctypes.c_voidp)
        try:
            path = debugger.read_process_memory(addr, 4096)
        except DebuggerError:
            pgrest = 0x1000 - (addr.value & 0xfff)
            path = debugger.read_process_memory(addr, pgrest)
        path = path.decode('utf-16', 'ignore')
        if u'\0' in path:
            path = path[:path.index(u'\0')]
        root, ext = os.path.splitext(path)
        if ext.lower() not in self.MOBI_EXTENSIONS:
            return
        self.book_path = path

    def _get_pc1_pid(self, debugger, context):
        addr = context.Esp + ctypes.sizeof(ctypes.c_voidp)
        addr = debugger.read_process_memory(addr, type=ctypes.c_char_p)
        pid = debugger.read_process_memory(addr, 8)
        pid = self._checksum_pid(pid)
        self.book_pid = pid

    def _checksum_pid(self, s):
        letters = "ABCDEFGHIJKLMNPQRSTUVWXYZ123456789"
        crc = (~binascii.crc32(s,-1))&0xFFFFFFFF
        crc = crc ^ (crc >> 16)
        res = s
        l = len(letters)
        for i in (0,1):
            b = crc & 0xff
            pos = (b // l) ^ (b % l)
            res += letters[pos%l]
            crc >>= 8
        return res

class MobiParser(object):
    def __init__(self, data):
        self.data = data
        header = data[0:72]
        if header[0x3C:0x3C+8] != 'BOOKMOBI':
            raise UnswindleError("invalid file format")
        self.nsections = nsections = struct.unpack('>H', data[76:78])[0]
        self.sections = sections = []
        for i in xrange(nsections):
            offset, a1, a2, a3, a4 = \
                struct.unpack('>LBBBB', data[78+i*8:78+i*8+8])
            flags, val = a1, ((a2 << 16) | (a3 << 8) | a4)
            sections.append((offset, flags, val))
        sect = self.load_section(0)
        self.crypto_type = struct.unpack('>H', sect[0x0c:0x0c+2])[0]

    def load_section(self, snum):
        if (snum + 1) == self.nsections:
            endoff = len(self.data)
        else:
            endoff = self.sections[snum + 1][0]
        off = self.sections[snum][0]
        return self.data[off:endoff]

class Unswindler(object):
    def __init__(self):
        self._exepath = self._get_exe_path()
        self._hexdigest = self._get_hexdigest()
        self._exedir = os.path.dirname(self._exepath)
        self._mobidedrmpath = self._get_mobidedrm_path()

    def _get_mobidedrm_path(self):
        basedir = sys.modules[self.__module__].__file__
        basedir = os.path.dirname(basedir)
        for basename in ('mobidedrm', 'mobidedrm.py', 'mobidedrm.pyw'):
            path = os.path.join(basedir, basename)
            if os.path.isfile(path):
                return path
        raise UnswindleError("could not locate MobiDeDRM script")

    def _get_exe_path(self):
        path = None
        for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                regkey = winreg.OpenKey(root, KINDLE_REG_KEY)
                path = winreg.QueryValue(regkey, None)
                break
            except WindowsError:
                pass
        else:
            raise UnswindleError("Kindle For PC installation not found")
        if '"' in path:
            path = re.search(r'"(.*?)"', path).group(1)
        return path

    def _get_hexdigest(self):
        path = self._exepath
        sha1 = hashlib.sha1()
        with open(path, 'rb') as f:
            data = f.read(4096)
            while data:
                sha1.update(data)
                data = f.read(4096)
        hexdigest = sha1.hexdigest()
        if not PC1KeyGrabber.supported_version(hexdigest):
            raise UnswindleError("Unsupported version of Kindle For PC")
        return hexdigest

    def _check_topaz(self, path):
        with open(path, 'rb') as f:
            magic = f.read(4)
        if magic == 'TPZ0':
            return True
        return False

    def _check_drm_free(self, path):
        with open(path, 'rb') as f:
            crypto = MobiParser(f.read()).crypto_type
        return (crypto == 0)

    def get_book(self):
        creation_flags = (CREATE_UNICODE_ENVIRONMENT |
                          DEBUG_PROCESS |
                          DEBUG_ONLY_THIS_PROCESS)
        startup_info = STARTUPINFO()
        process_info = PROCESS_INFORMATION()
        path = pid = None
        try:
            rv = CreateProcess(self._exepath, None, None, None, False,
                               creation_flags, None, self._exedir,
                               byref(startup_info), byref(process_info))
            if not rv:
                raise UnswindleError("failed to launch Kindle For PC")
            debugger = Debugger(process_info)
            grabber = PC1KeyGrabber(debugger, self._hexdigest)
            debugger.main_loop()
            path = grabber.book_path
            pid = grabber.book_pid
        finally:
            if process_info.hThread is not None:
                CloseHandle(process_info.hThread)
            if process_info.hProcess is not None:
                CloseHandle(process_info.hProcess)
        if path is None:
            raise UnswindleError("failed to determine book path")
        if self._check_topaz(path):
            raise UnswindleError("cannot decrypt Topaz format book")
        return (path, pid)

    def decrypt_book(self, inpath, outpath, pid):
        if self._check_drm_free(inpath):
            shutil.copy(inpath, outpath)
        else:
            self._mobidedrm(inpath, outpath, pid)
        return

    def _mobidedrm(self, inpath, outpath, pid):
        # darkreverser didn't protect mobidedrm's script execution to allow
        # importing, so we have to just run it in a subprocess
        if pid is None:
            raise UnswindleError("failed to determine book PID")
        with tempfile.NamedTemporaryFile(delete=False) as tmpf:
            tmppath = tmpf.name
        args = [sys.executable, self._mobidedrmpath, inpath, tmppath, pid]
        mobidedrm = subprocess.Popen(args, stderr=subprocess.STDOUT,
                                     stdout=subprocess.PIPE,
                                     universal_newlines=True)
        output = mobidedrm.communicate()[0]
        if not output.endswith("done\n"):
            try:
                os.remove(tmppath)
            except OSError:
                pass
            raise UnswindleError("problem running MobiDeDRM:\n" + output)
        shutil.move(tmppath, outpath)
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

def gui_main(argv=sys.argv):
    root = Tkinter.Tk()
    root.withdraw()
    progname = os.path.basename(argv[0])
    try:
        unswindler = Unswindler()
        inpath, pid = unswindler.get_book()
        outpath = tkFileDialog.asksaveasfilename(
            parent=None, title='Select unencrypted Mobipocket file to produce',
            defaultextension='.mobi', filetypes=[('MOBI files', '.mobi'),
                                                 ('All files', '.*')])
        if not outpath:
            return 0
        unswindler.decrypt_book(inpath, outpath, pid)
    except UnswindleError, e:
        tkMessageBox.showerror("Unswindle For PC", "Error: " + str(e))
        return 1
    except Exception:
        root.wm_state('normal')
        root.title('Unswindle For PC')
        text = traceback.format_exc()
        ExceptionDialog(root, text).pack(fill=Tkconstants.BOTH, expand=1)
        root.mainloop()
        return 1

def cli_main(argv=sys.argv):
    progname = os.path.basename(argv[0])
    args = argv[1:]
    if len(args) != 1:
        sys.stderr.write("usage: %s OUTFILE\n" % (progname,))
        return 1
    outpath = args[0]
    unswindler = Unswindler()
    inpath, pid = unswindler.get_book()
    unswindler.decrypt_book(inpath, outpath, pid)
    return 0

if __name__ == '__main__':
    sys.exit(gui_main())
