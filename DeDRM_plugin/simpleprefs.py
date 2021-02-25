#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import sys
import os, os.path
import shutil

class SimplePrefsError(Exception):
    pass

class SimplePrefs(object):
    def __init__(self, target, description):
        self.prefs = {}
        self.key2file={}
        self.file2key={}
        for keyfilemap in description:
            [key, filename] = keyfilemap
            self.key2file[key] = filename
            self.file2key[filename] = key
        self.target = target + 'Prefs'
        if sys.platform.startswith('win'):
            try:
                import winreg
            except ImportError:
                import _winreg as winreg
            regkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Folders\\")
            path = winreg.QueryValueEx(regkey, 'Local AppData')[0]
            prefdir = path + os.sep + self.target
        elif sys.platform.startswith('darwin'):
            home = os.getenv('HOME')
            prefdir = os.path.join(home,'Library','Preferences','org.' + self.target)
        else:
            # linux and various flavors of unix
            home = os.getenv('HOME')
            prefdir = os.path.join(home,'.' + self.target)
        if not os.path.exists(prefdir):
            os.makedirs(prefdir)
        self.prefdir = prefdir
        self.prefs['dir'] = self.prefdir
        self._loadPreferences()

    def _loadPreferences(self):
        filenames = os.listdir(self.prefdir)
        for filename in filenames:
            if filename in self.file2key:
                key = self.file2key[filename]
                filepath = os.path.join(self.prefdir,filename)
                if os.path.isfile(filepath):
                    try :
                        data = file(filepath,'rb').read()
                        self.prefs[key] = data
                    except Exception as e:
                        pass

    def getPreferences(self):
        return self.prefs

    def setPreferences(self, newprefs={}):
        if 'dir' not in newprefs:
            raise SimplePrefsError('Error: Attempt to Set Preferences in unspecified directory')
        if newprefs['dir'] != self.prefs['dir']:
            raise SimplePrefsError('Error: Attempt to Set Preferences in unspecified directory')
        for key in newprefs:
            if key != 'dir':
                if key in self.key2file:
                    filename = self.key2file[key]
                    filepath = os.path.join(self.prefdir,filename)
                    data = newprefs[key]
                    if data != None:
                        data = str(data)
                    if data == None or data == '':
                        if os.path.exists(filepath):
                            os.remove(filepath)
                    else:
                        try:
                            file(filepath,'wb').write(data)
                        except Exception as e:
                            pass
        self.prefs = newprefs
        return
