#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#@@CALIBRE_COMPAT_CODE@@

PLUGIN_NAME = "DeDRM"
__version__ = '10.0.9'

PLUGIN_VERSION_TUPLE = tuple([int(x) for x in __version__.split(".")])
PLUGIN_VERSION = ".".join([str(x)for x in PLUGIN_VERSION_TUPLE])
# Include an html helpfile in the plugin's zipfile with the following name.
RESOURCE_NAME = PLUGIN_NAME + '_Help.htm'