###########################################################################
# 
#  Psyco logger.
#   Copyright (C) 2001-2002  Armin Rigo et.al.

"""Psyco logger.

See log() in core.py.
"""
###########################################################################


import _psyco
from time import time, localtime, strftime


current = None
print_charges = 10
dump_delay = 0.2
dump_last = 0.0

def write(s, level):
    t = time()
    f = t-int(t)
    try:
        current.write("%s.%02d  %-*s%s\n" % (
            strftime("%X", localtime(int(t))),
            int(f*100.0), 63-level, s,
            "%"*level))
        current.flush()
    except (OSError, IOError):
        pass

def psycowrite(s):
    t = time()
    f = t-int(t)
    try:
        current.write("%s.%02d  %-*s%s\n" % (
            strftime("%X", localtime(int(t))),
            int(f*100.0), 60, s.strip(),
            "% %"))
        current.flush()
    except (OSError, IOError):
        pass

##def writelines(lines, level=0):
##    if lines:
##        t = time()
##        f = t-int(t)
##        timedesc = strftime("%x %X", localtime(int(t)))
##        print >> current, "%s.%03d  %-*s %s" % (
##            timedesc, int(f*1000),
##            50-level, lines[0],
##            "+"*level)
##        timedesc = " " * (len(timedesc)+5)
##        for line in lines[1:]:
##            print >> current, timedesc, line

def writememory():
    write("memory usage: %d+ kb" % _psyco.memory(), 1)

def dumpcharges():
    global dump_last
    if print_charges:
        t = time()
        if not (dump_last <= t < dump_last+dump_delay):
            if t <= dump_last+1.5*dump_delay:
                dump_last += dump_delay
            else:
                dump_last = t
            #write("%s: charges:" % who, 0)
            lst = _psyco.stattop(print_charges)
            if lst:
                f = t-int(t)
                lines = ["%s.%02d   ______\n" % (
                    strftime("%X", localtime(int(t))),
                    int(f*100.0))]
                i = 1
                for co, charge in lst:
                    detail = co.co_filename
                    if len(detail) > 19:
                        detail = '...' + detail[-17:]
                    lines.append("        #%-3d |%4.1f %%|  %-26s%20s:%d\n" %
                                 (i, charge*100.0, co.co_name, detail,
                                  co.co_firstlineno))
                    i += 1
                current.writelines(lines)
                current.flush()

def writefinalstats():
    dumpcharges()
    writememory()
    writedate("program exit")

def writedate(msg):
    write('%s, %s' % (msg, strftime("%x")), 20)
