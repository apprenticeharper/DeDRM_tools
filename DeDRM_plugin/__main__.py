#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# __main__.py for DeDRM_plugin
# (CLI interface without Calibre)
# Copyright © 2021 NoDRM

__license__   = 'GPL v3'
__docformat__ = 'restructuredtext en'

# For revision history see __init__.py

"""
Run DeDRM plugin without Calibre.
"""

# Import __init__.py from the standalone folder so we can have all the 
# standalone / non-Calibre code in that subfolder.

import standalone.__init__ as mdata
import sys

mdata.main(sys.argv)