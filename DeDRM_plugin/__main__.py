#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# __main__.py for DeDRM_plugin
# (CLI interface without Calibre)
# Copyright © 2021 NoDRM

"""

NOTE: This code is not functional (yet). I started working on it a while ago
to make a standalone version of the plugins that could work without Calibre, 
too, but for now there's only a rough code structure and no working code yet.

Currently, to use these plugins, you will need to use Calibre. Hopwfully that'll
change in the future. 

"""

__license__   = 'GPL v3'
__docformat__ = 'restructuredtext en'

# For revision history see CHANGELOG.md

"""
Run DeDRM plugin without Calibre.
"""

# Import __init__.py from the standalone folder so we can have all the 
# standalone / non-Calibre code in that subfolder.

import standalone.__init__ as mdata
import sys

mdata.main(sys.argv)