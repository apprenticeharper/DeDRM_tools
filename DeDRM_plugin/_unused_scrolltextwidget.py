#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# I think this file is unused?


import tkinter
import tkinter.constants

# basic scrolled text widget
class ScrolledText(tkinter.Text):
    def __init__(self, master=None, **kw):
        self.frame = tkinter.Frame(master)
        self.vbar = tkinter.Scrollbar(self.frame)
        self.vbar.pack(side=tkinter.constants.RIGHT, fill=tkinter.constants.Y)
        kw.update({'yscrollcommand': self.vbar.set})
        tkinter.Text.__init__(self, self.frame, **kw)
        self.pack(side=tkinter.constants.LEFT, fill=tkinter.constants.BOTH, expand=True)
        self.vbar['command'] = self.yview
        # Copy geometry methods of self.frame without overriding Text
        # methods = hack!
        text_meths = list(vars(tkinter.Text).keys())
        methods = list(vars(tkinter.Pack).keys()) + list(vars(tkinter.Grid).keys()) + list(vars(tkinter.Place).keys())
        methods = set(methods).difference(text_meths)
        for m in methods:
            if m[0] != '_' and m != 'config' and m != 'configure':
                setattr(self, m, getattr(self.frame, m))

    def __str__(self):
        return str(self.frame)
