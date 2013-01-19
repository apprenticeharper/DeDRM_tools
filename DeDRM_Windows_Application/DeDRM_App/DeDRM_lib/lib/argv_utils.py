#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
import locale
import codecs

# get sys.argv arguments and encode them into utf-8
def utf8_argv():
    if sys.platform.startswith('win'):
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
            return [argv[i].encode('utf-8') for i in
                    xrange(start, argc.value)]
        # this should never happen
        return None
    else:
        argv = []
        argvencoding = sys.stdin.encoding
        if argvencoding == None:
            argvencoding = sys.getfilesystemencoding()
        if argvencoding == None:
            argvencoding = 'utf-8'
        for arg in sys.argv:
            if type(arg) == unicode:
                argv.append(arg.encode('utf-8'))
            else:
                argv.append(arg.decode(argvencoding).encode('utf-8'))
        return argv


def add_cp65001_codec():
  try:
    codecs.lookup('cp65001')
  except LookupError:
    codecs.register(
        lambda name: name == 'cp65001' and codecs.lookup('utf-8') or None)
  return


def set_utf8_default_encoding():
  if sys.getdefaultencoding() == 'utf-8':
    return

  # Regenerate setdefaultencoding.
  reload(sys)
  sys.setdefaultencoding('utf-8')

  for attr in dir(locale):
    if attr[0:3] != 'LC_':
      continue
    aref = getattr(locale, attr)
    try:
      locale.setlocale(aref, '')
    except locale.Error:
      continue
    try:
      lang = locale.getlocale(aref)[0]
    except (TypeError, ValueError):
      continue
    if lang:
      try:
        locale.setlocale(aref, (lang, 'UTF-8'))
      except locale.Error:
        os.environ[attr] = lang + '.UTF-8'
  try:
    locale.setlocale(locale.LC_ALL, '')
  except locale.Error:
    pass
  return


