#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# CLI interface for the DeDRM plugin (useable without Calibre, too)
# Config implementation

from __future__ import absolute_import, print_function

# Taken from Calibre code - Copyright © 2008, Kovid Goyal kovid@kovidgoyal.net, GPLv3

"""

NOTE: This code is not functional (yet). I started working on it a while ago
to make a standalone version of the plugins that could work without Calibre, 
too, but for now there's only a rough code structure and no working code yet.

Currently, to use these plugins, you will need to use Calibre. Hopwfully that'll
change in the future. 

"""

#@@CALIBRE_COMPAT_CODE@@

import sys, os, codecs, json

config_dir = "/"
CONFIG_DIR_MODE = 0o700
iswindows = sys.platform.startswith('win')


filesystem_encoding = sys.getfilesystemencoding()
if filesystem_encoding is None:
    filesystem_encoding = 'utf-8'
else:
    try:
        if codecs.lookup(filesystem_encoding).name == 'ascii':
            filesystem_encoding = 'utf-8'
            # On linux, unicode arguments to os file functions are coerced to an ascii
            # bytestring if sys.getfilesystemencoding() == 'ascii', which is
            # just plain dumb. This is fixed by the icu.py module which, when
            # imported changes ascii to utf-8
    except Exception:
        filesystem_encoding = 'utf-8'


class JSONConfig(dict):

    EXTENSION = '.json'


    def __init__(self, rel_path_to_cf_file, base_path=config_dir):
        dict.__init__(self)
        self.no_commit = False
        self.defaults = {}
        self.file_path = os.path.join(base_path,
                *(rel_path_to_cf_file.split('/')))
        self.file_path = os.path.abspath(self.file_path)
        if not self.file_path.endswith(self.EXTENSION):
            self.file_path += self.EXTENSION

        self.refresh()

    def mtime(self):
        try:
            return os.path.getmtime(self.file_path)
        except OSError:
            return 0

    def touch(self):
        try:
            os.utime(self.file_path, None)
        except OSError:
            pass


    def decouple(self, prefix):
        self.file_path = os.path.join(os.path.dirname(self.file_path), prefix + os.path.basename(self.file_path))
        self.refresh()

    def refresh(self, clear_current=True):
        d = {}
        if os.path.exists(self.file_path):
            with open(self.file_path, "rb") as f:
                raw = f.read()
                try:
                    d = self.raw_to_object(raw) if raw.strip() else {}
                except SystemError:
                    pass
                except:
                    import traceback
                    traceback.print_exc()
                    d = {}
        if clear_current:
            self.clear()
        self.update(d)

    def has_key(self, key):
        return dict.__contains__(self, key)

    def set(self, key, val):
        self.__setitem__(key, val)

    def __delitem__(self, key):
        try:
            dict.__delitem__(self, key)
        except KeyError:
            pass  # ignore missing keys
        else:
            self.commit()

    def commit(self):
        if self.no_commit:
            return
        if hasattr(self, 'file_path') and self.file_path:
            dpath = os.path.dirname(self.file_path)
            if not os.path.exists(dpath):
                os.makedirs(dpath, mode=CONFIG_DIR_MODE)
            with open(self.file_path, "w") as f:
                raw = self.to_raw()
                f.seek(0)
                f.truncate()
                f.write(raw)

    def __enter__(self):
        self.no_commit = True

    def __exit__(self, *args):
        self.no_commit = False
        self.commit()

    def raw_to_object(self, raw):
        return json.loads(raw)

    def to_raw(self):
        return json.dumps(self, ensure_ascii=False)

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            return self.defaults[key]

    def get(self, key, default=None):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            return self.defaults.get(key, default)

    def __setitem__(self, key, val):
        dict.__setitem__(self, key, val)
        self.commit()