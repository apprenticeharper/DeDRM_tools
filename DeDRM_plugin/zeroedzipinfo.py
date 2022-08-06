#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
Python 3's "zipfile" has an annoying bug where the `external_attr` field 
of a ZIP file cannot be set to 0. However, if the original DRMed ZIP has 
that set to 0 then we want the DRM-free ZIP to have that as 0, too. 
See https://github.com/python/cpython/issues/87713

We cannot just set the "external_attr" to 0 as the code to save the ZIP
resets that variable. 

So, here's a class that inherits from ZipInfo and ensures that EVERY 
read access to that variable will return a 0 ...

"""

import zipfile

class ZeroedZipInfo(zipfile.ZipInfo):
    def __init__(self, zinfo):
        for k in self.__slots__:
            if hasattr(zinfo, k):
                setattr(self, k, getattr(zinfo, k))

    def __getattribute__(self, name):
        if name == "external_attr":
            return 0
        return object.__getattribute__(self, name)
