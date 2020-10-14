#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# to work around tk_chooseDirectory not properly returning unicode paths on Windows
# need to use a dialog that can be hacked up to actually return full unicode paths
# originally based on AskFolder from EasyDialogs for Windows but modified to fix it
# to actually use unicode for path

# The original license for EasyDialogs is as follows
#
# Copyright (c) 2003-2005 Jimmy Retzlaff
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

# Adjusted for Python 3, September 2020

"""
AskFolder(...) -- Ask the user to select a folder Windows specific
"""

import os

import ctypes
from ctypes import POINTER, byref, cdll, c_int, windll
from ctypes.wintypes import LPCWSTR, LPWSTR
import ctypes.wintypes as wintypes


__all__ = ['AskFolder']

# Load required Windows DLLs
ole32 = ctypes.windll.ole32
shell32 = ctypes.windll.shell32
user32 = ctypes.windll.user32


# Windows Constants
BFFM_INITIALIZED = 1
BFFM_SETOKTEXT = 1129
BFFM_SETSELECTIONA = 1126
BFFM_SETSELECTIONW = 1127
BIF_EDITBOX = 16
BS_DEFPUSHBUTTON = 1
CB_ADDSTRING = 323
CB_GETCURSEL = 327
CB_SETCURSEL = 334
CDM_SETCONTROLTEXT = 1128
EM_GETLINECOUNT = 186
EM_GETMARGINS = 212
EM_POSFROMCHAR = 214
EM_SETSEL = 177
GWL_STYLE = -16
IDC_STATIC = -1
IDCANCEL = 2
IDNO = 7
IDOK = 1
IDYES = 6
MAX_PATH = 260
OFN_ALLOWMULTISELECT = 512
OFN_ENABLEHOOK = 32
OFN_ENABLESIZING = 8388608
OFN_ENABLETEMPLATEHANDLE = 128
OFN_EXPLORER = 524288
OFN_OVERWRITEPROMPT = 2
OPENFILENAME_SIZE_VERSION_400 = 76
PBM_GETPOS = 1032
PBM_SETMARQUEE = 1034
PBM_SETPOS = 1026
PBM_SETRANGE = 1025
PBM_SETRANGE32 = 1030
PBS_MARQUEE = 8
PM_REMOVE = 1
SW_HIDE = 0
SW_SHOW = 5
SW_SHOWNORMAL = 1
SWP_NOACTIVATE = 16
SWP_NOMOVE = 2
SWP_NOSIZE = 1
SWP_NOZORDER = 4
VER_PLATFORM_WIN32_NT = 2
WM_COMMAND = 273
WM_GETTEXT = 13
WM_GETTEXTLENGTH = 14
WM_INITDIALOG = 272
WM_NOTIFY = 78

# Windows function prototypes
BrowseCallbackProc = ctypes.WINFUNCTYPE(ctypes.c_int, wintypes.HWND, ctypes.c_uint, wintypes.LPARAM, wintypes.LPARAM)

# Windows types
LPCTSTR = ctypes.c_char_p
LPTSTR = ctypes.c_char_p
LPVOID = ctypes.c_voidp
TCHAR = ctypes.c_char

class BROWSEINFO(ctypes.Structure):
    _fields_ = [
                ("hwndOwner", wintypes.HWND),
                ("pidlRoot", LPVOID),
                ("pszDisplayName", LPTSTR),
                ("lpszTitle", LPCTSTR),
                ("ulFlags", ctypes.c_uint),
                ("lpfn", BrowseCallbackProc),
                ("lParam", wintypes.LPARAM),
                ("iImage", ctypes.c_int)
               ]


# Utilities
def CenterWindow(hwnd):
    desktopRect = GetWindowRect(user32.GetDesktopWindow())
    myRect = GetWindowRect(hwnd)
    x = width(desktopRect) // 2 - width(myRect) // 2
    y = height(desktopRect) // 2 - height(myRect) // 2
    user32.SetWindowPos(hwnd, 0,
                        desktopRect.left + x,
                        desktopRect.top + y,
                        0, 0,
                        SWP_NOACTIVATE | SWP_NOSIZE | SWP_NOZORDER
                       )


def GetWindowRect(hwnd):
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return rect

def width(rect):
    return rect.right-rect.left

def height(rect):
    return rect.bottom-rect.top


def AskFolder(
        message=None,
        version=None,
        defaultLocation=None,
        location=None,
        windowTitle=None,
        actionButtonLabel=None,
        cancelButtonLabel=None,
        multiple=None):
    """Display a dialog asking the user for select a folder.
       modified to use unicode strings as much as possible
       returns unicode path
    """

    def BrowseCallback(hwnd, uMsg, lParam, lpData):
        if uMsg == BFFM_INITIALIZED:
            if actionButtonLabel:
                label = str(actionButtonLabel, errors='replace')
                user32.SendMessageW(hwnd, BFFM_SETOKTEXT, 0, label)
            if cancelButtonLabel:
                label = str(cancelButtonLabel, errors='replace')
                cancelButton = user32.GetDlgItem(hwnd, IDCANCEL)
                if cancelButton:
                    user32.SetWindowTextW(cancelButton, label)
            if windowTitle:
                title = str(windowTitle, errors='replace')
                user32.SetWindowTextW(hwnd, title)
            if defaultLocation:
                user32.SendMessageW(hwnd, BFFM_SETSELECTIONW, 1, defaultLocation.replace('/', '\\'))
            if location:
                x, y = location
                desktopRect = wintypes.RECT()
                user32.GetWindowRect(0, ctypes.byref(desktopRect))
                user32.SetWindowPos(hwnd, 0,
                                  desktopRect.left + x,
                                  desktopRect.top + y, 0, 0,
                                  SWP_NOACTIVATE | SWP_NOSIZE | SWP_NOZORDER)
            else:
                CenterWindow(hwnd)
        return 0

    # This next line is needed to prevent gc of the callback
    callback = BrowseCallbackProc(BrowseCallback)

    browseInfo = BROWSEINFO()
    browseInfo.pszDisplayName = ctypes.c_char_p('\0' * (MAX_PATH+1))
    browseInfo.lpszTitle = message
    browseInfo.lpfn = callback

    pidl = shell32.SHBrowseForFolder(ctypes.byref(browseInfo))
    if not pidl:
        result = None
    else:
        path = LPCWSTR(" " * (MAX_PATH+1))
        shell32.SHGetPathFromIDListW(pidl, path)
        ole32.CoTaskMemFree(pidl)
        result = path.value
    return result




