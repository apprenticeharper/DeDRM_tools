###########################################################################
# 
#  Psyco general support module.
#   Copyright (C) 2001-2002  Armin Rigo et.al.

"""Psyco general support module.

For internal use.
"""
###########################################################################

import sys, _psyco, __builtin__

error = _psyco.error
class warning(Warning):
    pass

_psyco.NoLocalsWarning = warning

def warn(msg):
    from warnings import warn
    warn(msg, warning, stacklevel=2)

#
# Version checks
#
__version__ = 0x010600f0
if _psyco.PSYVER != __version__:
    raise error, "version mismatch between Psyco parts, reinstall it"

version_info = (__version__ >> 24,
                (__version__ >> 16) & 0xff,
                (__version__ >> 8) & 0xff,
                {0xa0: 'alpha',
                 0xb0: 'beta',
                 0xc0: 'candidate',
                 0xf0: 'final'}[__version__ & 0xf0],
                __version__ & 0xf)


VERSION_LIMITS = [0x02020200,   # 2.2.2
                  0x02030000,   # 2.3
                  0x02040000]   # 2.4

if ([v for v in VERSION_LIMITS if v <= sys.hexversion] !=
    [v for v in VERSION_LIMITS if v <= _psyco.PYVER  ]):
    if sys.hexversion < VERSION_LIMITS[0]:
        warn("Psyco requires Python version 2.2.2 or later")
    else:
        warn("Psyco version does not match Python version. "
             "Psyco must be updated or recompiled")


if hasattr(_psyco, 'ALL_CHECKS') and hasattr(_psyco, 'VERBOSE_LEVEL'):
    print >> sys.stderr, ('psyco: running in debugging mode on %s' %
                          _psyco.PROCESSOR)


###########################################################################
# sys._getframe() gives strange results on a mixed Psyco- and Python-style
# stack frame. Psyco provides a replacement that partially emulates Python
# frames from Psyco frames. The new sys._getframe() may return objects of
# a custom "Psyco frame" type, which is a subtype of the normal frame type.
#
# The same problems require some other built-in functions to be replaced
# as well. Note that the local variables are not available in any
# dictionary with Psyco.


class Frame:
    pass


class PythonFrame(Frame):

    def __init__(self, frame):
        self.__dict__.update({
            '_frame': frame,
            })

    def __getattr__(self, attr):
        if attr == 'f_back':
            try:
                result = embedframe(_psyco.getframe(self._frame))
            except ValueError:
                result = None
            except error:
                warn("f_back is skipping dead Psyco frames")
                result = self._frame.f_back
            self.__dict__['f_back'] = result
            return result
        else:
            return getattr(self._frame, attr)

    def __setattr__(self, attr, value):
        setattr(self._frame, attr, value)

    def __delattr__(self, attr):
        delattr(self._frame, attr)


class PsycoFrame(Frame):

    def __init__(self, tag):
        self.__dict__.update({
            '_tag'     : tag,
            'f_code'   : tag[0],
            'f_globals': tag[1],
            })

    def __getattr__(self, attr):
        if attr == 'f_back':
            try:
                result = embedframe(_psyco.getframe(self._tag))
            except ValueError:
                result = None
        elif attr == 'f_lineno':
            result = self.f_code.co_firstlineno  # better than nothing
        elif attr == 'f_builtins':
            result = self.f_globals['__builtins__']
        elif attr == 'f_restricted':
            result = self.f_builtins is not __builtins__
        elif attr == 'f_locals':
            raise AttributeError, ("local variables of functions run by Psyco "
                                   "cannot be accessed in any way, sorry")
        else:
            raise AttributeError, ("emulated Psyco frames have "
                                   "no '%s' attribute" % attr)
        self.__dict__[attr] = result
        return result

    def __setattr__(self, attr, value):
        raise AttributeError, "Psyco frame objects are read-only"

    def __delattr__(self, attr):
        if attr == 'f_trace':
            # for bdb which relies on CPython frames exhibiting a slightly
            # buggy behavior: you can 'del f.f_trace' as often as you like
            # even without having set it previously.
            return
        raise AttributeError, "Psyco frame objects are read-only"


def embedframe(result):
    if type(result) is type(()):
        return PsycoFrame(result)
    else:
        return PythonFrame(result)

def _getframe(depth=0):
    """Return a frame object from the call stack. This is a replacement for
sys._getframe() which is aware of Psyco frames.

The returned objects are instances of either PythonFrame or PsycoFrame
instead of being real Python-level frame object, so that they can emulate
the common attributes of frame objects.

The original sys._getframe() ignoring Psyco frames altogether is stored in
psyco._getrealframe(). See also psyco._getemulframe()."""
    # 'depth+1' to account for this _getframe() Python function
    return embedframe(_psyco.getframe(depth+1))

def _getemulframe(depth=0):
    """As _getframe(), but the returned objects are real Python frame objects
emulating Psyco frames. Some of their attributes can be wrong or missing,
however."""
    # 'depth+1' to account for this _getemulframe() Python function
    return _psyco.getframe(depth+1, 1)

def patch(name, module=__builtin__):
    f = getattr(_psyco, name)
    org = getattr(module, name)
    if org is not f:
        setattr(module, name, f)
        setattr(_psyco, 'original_' + name, org)

_getrealframe = sys._getframe
sys._getframe = _getframe
patch('globals')
patch('eval')
patch('execfile')
patch('locals')
patch('vars')
patch('dir')
patch('input')
_psyco.original_raw_input = raw_input
__builtin__.__in_psyco__ = 0==1   # False

if hasattr(_psyco, 'compact'):
    import kdictproxy
    _psyco.compactdictproxy = kdictproxy.compactdictproxy
