###########################################################################
# 
#  Psyco class support module.
#   Copyright (C) 2001-2002  Armin Rigo et.al.

"""Psyco class support module.

'psyco.classes.psyobj' is an alternate Psyco-optimized root for classes.
Any class inheriting from it or using the metaclass '__metaclass__' might
get optimized specifically for Psyco. It is equivalent to call
psyco.bind() on the class object after its creation.

Importing everything from psyco.classes in a module will import the
'__metaclass__' name, so all classes defined after a

       from psyco.classes import *

will automatically use the Psyco-optimized metaclass.
"""
###########################################################################

__all__ = ['psyobj', 'psymetaclass', '__metaclass__']


from _psyco import compacttype
import core
from types import FunctionType

class psymetaclass(compacttype):
    "Psyco-optimized meta-class. Turns all methods into Psyco proxies."

    def __new__(cls, name, bases, dict):
        bindlist = dict.get('__psyco__bind__')
        if bindlist is None:
            bindlist = [key for key, value in dict.items()
                        if isinstance(value, FunctionType)]
        for attr in bindlist:
            dict[attr] = core.proxy(dict[attr])
        return super(psymetaclass, cls).__new__(cls, name, bases, dict)

psyobj = psymetaclass("psyobj", (), {})
__metaclass__ = psymetaclass
