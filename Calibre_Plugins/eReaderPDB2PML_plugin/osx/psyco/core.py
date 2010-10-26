###########################################################################
# 
#  Psyco main functions.
#   Copyright (C) 2001-2002  Armin Rigo et.al.

"""Psyco main functions.

Here are the routines that you can use from your applications.
These are mostly interfaces to the C core, but they depend on
the Python version.

You can use these functions from the 'psyco' module instead of
'psyco.core', e.g.

    import psyco
    psyco.log('/tmp/psyco.log')
    psyco.profile()
"""
###########################################################################

import _psyco
import types
from support import *

newfunction = types.FunctionType
newinstancemethod = types.MethodType


# Default charge profiler values
default_watermark     = 0.09     # between 0.0 (0%) and 1.0 (100%)
default_halflife      = 0.5      # seconds
default_pollfreq_profile    = 20       # Hz
default_pollfreq_background = 100      # Hz -- a maximum for sleep's resolution
default_parentframe   = 0.25     # should not be more than 0.5 (50%)


def full(memory=None, time=None, memorymax=None, timemax=None):
    """Compile as much as possible.

Typical use is for small scripts performing intensive computations
or string handling."""
    import profiler
    p = profiler.FullCompiler()
    p.run(memory, time, memorymax, timemax)


def profile(watermark   = default_watermark,
            halflife    = default_halflife,
            pollfreq    = default_pollfreq_profile,
            parentframe = default_parentframe,
            memory=None, time=None, memorymax=None, timemax=None):
    """Turn on profiling.

The 'watermark' parameter controls how easily running functions will
be compiled. The smaller the value, the more functions are compiled."""
    import profiler
    p = profiler.ActivePassiveProfiler(watermark, halflife,
                                       pollfreq, parentframe)
    p.run(memory, time, memorymax, timemax)


def background(watermark   = default_watermark,
               halflife    = default_halflife,
               pollfreq    = default_pollfreq_background,
               parentframe = default_parentframe,
               memory=None, time=None, memorymax=None, timemax=None):
    """Turn on passive profiling.

This is a very lightweight mode in which only intensively computing
functions can be detected. The smaller the 'watermark', the more functions
are compiled."""
    import profiler
    p = profiler.PassiveProfiler(watermark, halflife, pollfreq, parentframe)
    p.run(memory, time, memorymax, timemax)


def runonly(memory=None, time=None, memorymax=None, timemax=None):
    """Nonprofiler.

XXX check if this is useful and document."""
    import profiler
    p = profiler.RunOnly()
    p.run(memory, time, memorymax, timemax)


def stop():
    """Turn off all automatic compilation.  bind() calls remain in effect."""
    import profiler
    profiler.go([])


def log(logfile='', mode='w', top=10):
    """Enable logging to the given file.

If the file name is unspecified, a default name is built by appending
a 'log-psyco' extension to the main script name.

Mode is 'a' to append to a possibly existing file or 'w' to overwrite
an existing file. Note that the log file may grow quickly in 'a' mode."""
    import profiler, logger
    if not logfile:
        import os
        logfile, dummy = os.path.splitext(sys.argv[0])
        if os.path.basename(logfile):
            logfile += '.'
        logfile += 'log-psyco'
    if hasattr(_psyco, 'VERBOSE_LEVEL'):
        print >> sys.stderr, 'psyco: logging to', logfile
    # logger.current should be a real file object; subtle problems
    # will show up if its write() and flush() methods are written
    # in Python, as Psyco will invoke them while compiling.
    logger.current = open(logfile, mode)
    logger.print_charges = top
    profiler.logger = logger
    logger.writedate('Logging started')
    cannotcompile(logger.psycowrite)
    _psyco.statwrite(logger=logger.psycowrite)


def bind(x, rec=None):
    """Enable compilation of the given function, method, or class object.

If C is a class (or anything with a '__dict__' attribute), bind(C) will
rebind all functions and methods found in C.__dict__ (which means, for
classes, all methods defined in the class but not in its parents).

The optional second argument specifies the number of recursive
compilation levels: all functions called by func are compiled
up to the given depth of indirection."""
    if isinstance(x, types.MethodType):
        x = x.im_func
    if isinstance(x, types.FunctionType):
        if rec is None:
            x.func_code = _psyco.proxycode(x)
        else:
            x.func_code = _psyco.proxycode(x, rec)
        return
    if hasattr(x, '__dict__'):
        funcs = [o for o in x.__dict__.values()
                 if isinstance(o, types.MethodType)
                 or isinstance(o, types.FunctionType)]
        if not funcs:
            raise error, ("nothing bindable found in %s object" %
                          type(x).__name__)
        for o in funcs:
            bind(o, rec)
        return
    raise TypeError, "cannot bind %s objects" % type(x).__name__


def unbind(x):
    """Reverse of bind()."""
    if isinstance(x, types.MethodType):
        x = x.im_func
    if isinstance(x, types.FunctionType):
        try:
            f = _psyco.unproxycode(x.func_code)
        except error:
            pass
        else:
            x.func_code = f.func_code
        return
    if hasattr(x, '__dict__'):
        for o in x.__dict__.values():
            if (isinstance(o, types.MethodType)
             or isinstance(o, types.FunctionType)):
                unbind(o)
        return
    raise TypeError, "cannot unbind %s objects" % type(x).__name__


def proxy(x, rec=None):
    """Return a Psyco-enabled copy of the function.

The original function is still available for non-compiled calls.
The optional second argument specifies the number of recursive
compilation levels: all functions called by func are compiled
up to the given depth of indirection."""
    if isinstance(x, types.FunctionType):
        if rec is None:
            code = _psyco.proxycode(x)
        else:
            code = _psyco.proxycode(x, rec)
        return newfunction(code, x.func_globals, x.func_name)
    if isinstance(x, types.MethodType):
        p = proxy(x.im_func, rec)
        return newinstancemethod(p, x.im_self, x.im_class)
    raise TypeError, "cannot proxy %s objects" % type(x).__name__


def unproxy(proxy):
    """Return a new copy of the original function of method behind a proxy.
The result behaves like the original function in that calling it
does not trigger compilation nor execution of any compiled code."""
    if isinstance(proxy, types.FunctionType):
        return _psyco.unproxycode(proxy.func_code)
    if isinstance(proxy, types.MethodType):
        f = unproxy(proxy.im_func)
        return newinstancemethod(f, proxy.im_self, proxy.im_class)
    raise TypeError, "%s objects cannot be proxies" % type(proxy).__name__


def cannotcompile(x):
    """Instruct Psyco never to compile the given function, method
or code object."""
    if isinstance(x, types.MethodType):
        x = x.im_func
    if isinstance(x, types.FunctionType):
        x = x.func_code
    if isinstance(x, types.CodeType):
        _psyco.cannotcompile(x)
    else:
        raise TypeError, "unexpected %s object" % type(x).__name__


def dumpcodebuf():
    """Write in file psyco.dump a copy of the emitted machine code,
provided Psyco was compiled with a non-zero CODE_DUMP.
See py-utils/httpxam.py to examine psyco.dump."""
    if hasattr(_psyco, 'dumpcodebuf'):
        _psyco.dumpcodebuf()


###########################################################################
# Psyco variables
#   error         * the error raised by Psyco
#   warning       * the warning raised by Psyco
#   __in_psyco__  * a new built-in variable which is always zero, but which
#                     Psyco special-cases by returning 1 instead. So
#                     __in_psyco__ can be used in a function to know if
#                     that function is being executed by Psyco or not.
