#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import Tkinter
import Tkconstants

# basic scrolled text widget
class ScrolledText(Tkinter.Text):
    def __init__(self, master=None, **kw):
        self.frame = Tkinter.Frame(master)
        self.vbar = Tkinter.Scrollbar(self.frame)
        self.vbar.pack(side=Tkconstants.RIGHT, fill=Tkconstants.Y)
        kw.update({'yscrollcommand': self.vbar.set})
        Tkinter.Text.__init__(self, self.frame, **kw)
        self.pack(side=Tkconstants.LEFT, fill=Tkconstants.BOTH, expand=True)
        self.vbar['command'] = self.yview
        # Copy geometry methods of self.frame without overriding Text
        # methods = hack!
        text_meths = vars(Tkinter.Text).keys()
        methods = vars(Tkinter.Pack).keys() + vars(Tkinter.Grid).keys() + vars(Tkinter.Place).keys()
        methods = set(methods).difference(text_meths)
        for m in methods:
            if m[0] != '_' and m != 'config' and m != 'configure':
                setattr(self, m, getattr(self.frame, m))

    def __str__(self):
        return str(self.frame)
