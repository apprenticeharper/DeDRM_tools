# -*- coding: utf-8 -*-
#
# Adapted and simplified from the kitchen project
#
# Kitchen Project Copyright (c) 2012 Red Hat, Inc.
#
# kitchen is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# kitchen is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with kitchen; if not, see <http://www.gnu.org/licenses/>
#
# Authors:
#   Toshio Kuratomi <toshio@fedoraproject.org>
#   Seth Vidal
#
# Portions of code taken from yum/i18n.py and
# python-fedora: fedora/textutils.py

import codecs

# returns a char string unchanged
# returns a unicode string converted to a char string of the passed encoding
# return the empty string for anything else
def getwriter(encoding):
    class _StreamWriter(codecs.StreamWriter):
        def __init__(self, stream):
            codecs.StreamWriter.__init__(self, stream, 'replace')

        def encode(self, msg, errors='replace'):
            if isinstance(msg, basestring):
                if isinstance(msg, str):
                    return (msg, len(msg))
                return (msg.encode(self.encoding, 'replace'), len(msg))
            return ('',0)

    _StreamWriter.encoding = encoding
    return _StreamWriter
