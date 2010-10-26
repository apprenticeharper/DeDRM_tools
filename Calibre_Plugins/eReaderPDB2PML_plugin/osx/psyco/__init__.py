###########################################################################
# 
#  Psyco top-level file of the Psyco package.
#   Copyright (C) 2001-2002  Armin Rigo et.al.

"""Psyco -- the Python Specializing Compiler.

Typical usage: add the following lines to your application's main module,
preferably after the other imports:

try:
    import psyco
    psyco.full()
except ImportError:
    print 'Psyco not installed, the program will just run slower'
"""
###########################################################################


#
# This module is present to make 'psyco' a package and to
# publish the main functions and variables.
#
# More documentation can be found in core.py.
#


# Try to import the dynamic-loading _psyco and report errors
try:
    import _psyco
except ImportError, e:
    extramsg = ''
    import sys, imp
    try:
        file, filename, (suffix, mode, type) = imp.find_module('_psyco', __path__)
    except ImportError:
        ext = [suffix for suffix, mode, type in imp.get_suffixes()
               if type == imp.C_EXTENSION]
        if ext:
            extramsg = (" (cannot locate the compiled extension '_psyco%s' "
                        "in the package path '%s')" % (ext[0], '; '.join(__path__)))
    else:
        extramsg = (" (check that the compiled extension '%s' is for "
                    "the correct Python version; this is Python %s)" %
                    (filename, sys.version.split()[0]))
    raise ImportError, str(e) + extramsg

# Publish important data by importing them in the package
from support import __version__, error, warning, _getrealframe, _getemulframe
from support import version_info, __version__ as hexversion
from core import full, profile, background, runonly, stop, cannotcompile
from core import log, bind, unbind, proxy, unproxy, dumpcodebuf
from _psyco import setfilter
from _psyco import compact, compacttype
