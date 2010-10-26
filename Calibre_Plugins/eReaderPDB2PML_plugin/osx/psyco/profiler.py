###########################################################################
# 
#  Psyco profiler (Python part).
#   Copyright (C) 2001-2002  Armin Rigo et.al.

"""Psyco profiler (Python part).

The implementation of the non-time-critical parts of the profiler.
See profile() and full() in core.py for the easy interface.
"""
###########################################################################

import _psyco
from support import *
import math, time, types, atexit
now = time.time
try:
    import thread
except ImportError:
    import dummy_thread as thread


# current profiler instance
current = None

# enabled profilers, in order of priority
profilers = []

# logger module (when enabled by core.log())
logger = None

# a lock for a thread-safe go()
go_lock = thread.allocate_lock()

def go(stop=0):
    # run the highest-priority profiler in 'profilers'
    global current
    go_lock.acquire()
    try:
        prev = current
        if stop:
            del profilers[:]
        if prev:
            if profilers and profilers[0] is prev:
                return    # best profiler already running
            prev.stop()
            current = None
        for p in profilers[:]:
            if p.start():
                current = p
                if logger: # and p is not prev:
                    logger.write("%s: starting" % p.__class__.__name__, 5)
                return
    finally:
        go_lock.release()
    # no profiler is running now
    if stop:
        if logger:
            logger.writefinalstats()
    else:
        tag2bind()

atexit.register(go, 1)


def buildfncache(globals, cache):
    if hasattr(types.IntType, '__dict__'):
        clstypes = (types.ClassType, types.TypeType)
    else:
        clstypes = types.ClassType
    for x in globals.values():
        if isinstance(x, types.MethodType):
            x = x.im_func
        if isinstance(x, types.FunctionType):
            cache[x.func_code] = x, ''
        elif isinstance(x, clstypes):
            for y in x.__dict__.values():
                if isinstance(y, types.MethodType):
                    y = y.im_func
                if isinstance(y, types.FunctionType):
                    cache[y.func_code] = y, x.__name__

# code-to-function mapping (cache)
function_cache = {}

def trytobind(co, globals, log=1):
    try:
        f, clsname = function_cache[co]
    except KeyError:
        buildfncache(globals, function_cache)
        try:
            f, clsname = function_cache[co]
        except KeyError:
            if logger:
                logger.write('warning: cannot find function %s in %s' %
                             (co.co_name, globals.get('__name__', '?')), 3)
            return  # give up
    if logger and log:
        modulename = globals.get('__name__', '?')
        if clsname:
            modulename += '.' + clsname
        logger.write('bind function: %s.%s' % (modulename, co.co_name), 1)
    f.func_code = _psyco.proxycode(f)


# the list of code objects that have been tagged
tagged_codes = []

def tag(co, globals):
    if logger:
        try:
            f, clsname = function_cache[co]
        except KeyError:
            buildfncache(globals, function_cache)
            try:
                f, clsname = function_cache[co]
            except KeyError:
                clsname = ''  # give up
        modulename = globals.get('__name__', '?')
        if clsname:
            modulename += '.' + clsname
        logger.write('tag function: %s.%s' % (modulename, co.co_name), 1)
    tagged_codes.append((co, globals))
    _psyco.turbo_frame(co)
    _psyco.turbo_code(co)

def tag2bind():
    if tagged_codes:
        if logger:
            logger.write('profiling stopped, binding %d functions' %
                         len(tagged_codes), 2)
        for co, globals in tagged_codes:
            trytobind(co, globals, 0)
        function_cache.clear()
        del tagged_codes[:]


class Profiler:
    MemoryTimerResolution = 0.103

    def run(self, memory, time, memorymax, timemax):
        self.memory = memory
        self.memorymax = memorymax
        self.time = time
        if timemax is None:
            self.endtime = None
        else:
            self.endtime = now() + timemax
        self.alarms = []
        profilers.append(self)
        go()
    
    def start(self):
        curmem = _psyco.memory()
        memlimits = []
        if self.memorymax is not None:
            if curmem >= self.memorymax:
                if logger:
                    logger.writememory()
                return self.limitreached('memorymax')
            memlimits.append(self.memorymax)
        if self.memory is not None:
            if self.memory <= 0:
                if logger:
                    logger.writememory()
                return self.limitreached('memory')
            memlimits.append(curmem + self.memory)
            self.memory_at_start = curmem

        curtime = now()
        timelimits = []
        if self.endtime is not None:
            if curtime >= self.endtime:
                return self.limitreached('timemax')
            timelimits.append(self.endtime - curtime)
        if self.time is not None:
            if self.time <= 0.0:
                return self.limitreached('time')
            timelimits.append(self.time)
            self.time_at_start = curtime
        
        try:
            self.do_start()
        except error, e:
            if logger:
                logger.write('%s: disabled by psyco.error:' % (
                    self.__class__.__name__), 4)
                logger.write('    %s' % str(e), 3)
            return 0
        
        if memlimits:
            self.memlimits_args = (time.sleep, (self.MemoryTimerResolution,),
                                   self.check_memory, (min(memlimits),))
            self.alarms.append(_psyco.alarm(*self.memlimits_args))
        if timelimits:
            self.alarms.append(_psyco.alarm(time.sleep, (min(timelimits),),
                                            self.time_out))
        return 1
    
    def stop(self):
        for alarm in self.alarms:
            alarm.stop(0)
        for alarm in self.alarms:
            alarm.stop(1)   # wait for parallel threads to stop
        del self.alarms[:]
        if self.time is not None:
            self.time -= now() - self.time_at_start
        if self.memory is not None:
            self.memory -= _psyco.memory() - self.memory_at_start

        try:
            self.do_stop()
        except error:
            return 0
        return 1

    def check_memory(self, limit):
        if _psyco.memory() < limit:
            return self.memlimits_args
        go()

    def time_out(self):
        self.time = 0.0
        go()

    def limitreached(self, limitname):
        try:
            profilers.remove(self)
        except ValueError:
            pass
        if logger:
            logger.write('%s: disabled (%s limit reached)' % (
                self.__class__.__name__, limitname), 4)
        return 0


class FullCompiler(Profiler):

    def do_start(self):
        _psyco.profiling('f')

    def do_stop(self):
        _psyco.profiling('.')


class RunOnly(Profiler):

    def do_start(self):
        _psyco.profiling('n')

    def do_stop(self):
        _psyco.profiling('.')


class ChargeProfiler(Profiler):

    def __init__(self, watermark, parentframe):
        self.watermark = watermark
        self.parent2 = parentframe * 2.0
        self.lock = thread.allocate_lock()

    def init_charges(self):
        _psyco.statwrite(watermark = self.watermark,
                         parent2   = self.parent2)

    def do_stop(self):
        _psyco.profiling('.')
        _psyco.statwrite(callback = None)


class ActiveProfiler(ChargeProfiler):

    def active_start(self):
        _psyco.profiling('p')

    def do_start(self):
        self.init_charges()
        self.active_start()
        _psyco.statwrite(callback = self.charge_callback)

    def charge_callback(self, frame, charge):
        tag(frame.f_code, frame.f_globals)


class PassiveProfiler(ChargeProfiler):

    initial_charge_unit   = _psyco.statread('unit')
    reset_stats_after     = 120      # half-lives (maximum 200!)
    reset_limit           = initial_charge_unit * (2.0 ** reset_stats_after)

    def __init__(self, watermark, halflife, pollfreq, parentframe):
        ChargeProfiler.__init__(self, watermark, parentframe)
        self.pollfreq = pollfreq
        # self.progress is slightly more than 1.0, and computed so that
        # do_profile() will double the change_unit every 'halflife' seconds.
        self.progress = 2.0 ** (1.0 / (halflife * pollfreq))

    def reset(self):
        _psyco.statwrite(unit = self.initial_charge_unit, callback = None)
        _psyco.statreset()
        if logger:
            logger.write("%s: resetting stats" % self.__class__.__name__, 1)

    def passive_start(self):
        self.passivealarm_args = (time.sleep, (1.0 / self.pollfreq,),
                                  self.do_profile)
        self.alarms.append(_psyco.alarm(*self.passivealarm_args))

    def do_start(self):
        tag2bind()
        self.init_charges()
        self.passive_start()

    def do_profile(self):
        _psyco.statcollect()
        if logger:
            logger.dumpcharges()
        nunit = _psyco.statread('unit') * self.progress
        if nunit > self.reset_limit:
            self.reset()
        else:
            _psyco.statwrite(unit = nunit, callback = self.charge_callback)
        return self.passivealarm_args

    def charge_callback(self, frame, charge):
        trytobind(frame.f_code, frame.f_globals)


class ActivePassiveProfiler(PassiveProfiler, ActiveProfiler):

    def do_start(self):
        self.init_charges()
        self.active_start()
        self.passive_start()

    def charge_callback(self, frame, charge):
        tag(frame.f_code, frame.f_globals)



#
# we register our own version of sys.settrace(), sys.setprofile()
# and thread.start_new_thread().
#

def psyco_settrace(*args, **kw):
    "This is the Psyco-aware version of sys.settrace()."
    result = original_settrace(*args, **kw)
    go()
    return result

def psyco_setprofile(*args, **kw):
    "This is the Psyco-aware version of sys.setprofile()."
    result = original_setprofile(*args, **kw)
    go()
    return result

def psyco_thread_stub(callable, args, kw):
    _psyco.statcollect()
    if kw is None:
        return callable(*args)
    else:
        return callable(*args, **kw)

def psyco_start_new_thread(callable, args, kw=None):
    "This is the Psyco-aware version of thread.start_new_thread()."
    return original_start_new_thread(psyco_thread_stub, (callable, args, kw))

original_settrace         = sys.settrace
original_setprofile       = sys.setprofile
original_start_new_thread = thread.start_new_thread
sys.settrace            = psyco_settrace
sys.setprofile          = psyco_setprofile
thread.start_new_thread = psyco_start_new_thread
# hack to patch threading._start_new_thread if the module is
# already loaded
if ('threading' in sys.modules and
    hasattr(sys.modules['threading'], '_start_new_thread')):
    sys.modules['threading']._start_new_thread = psyco_start_new_thread
