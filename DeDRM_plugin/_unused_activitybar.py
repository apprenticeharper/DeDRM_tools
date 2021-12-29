# I think this file is unused?

import sys
import tkinter
import tkinter.constants

class ActivityBar(tkinter.Frame):

    def __init__(self, master, length=300, height=20, barwidth=15, interval=50, bg='white', fillcolor='orchid1',\
                 bd=2, relief=tkinter.constants.GROOVE, *args, **kw):
        tkinter.Frame.__init__(self, master, bg=bg, width=length, height=height, *args, **kw)
        self._master = master
        self._interval = interval
        self._maximum = length
        self._startx = 0
        self._barwidth = barwidth
        self._bardiv = length / barwidth
        if self._bardiv < 10:
            self._bardiv = 10
        stopx = self._startx + self._barwidth
        if stopx > self._maximum:
            stopx = self._maximum
        # self._canv = Tkinter.Canvas(self, bg=self['bg'], width=self['width'], height=self['height'],\
        #                             highlightthickness=0, relief='flat', bd=0)
        self._canv = tkinter.Canvas(self, bg=self['bg'], width=self['width'], height=self['height'],\
                                    highlightthickness=0, relief=relief, bd=bd)
        self._canv.pack(fill='both', expand=1)
        self._rect = self._canv.create_rectangle(0, 0, self._canv.winfo_reqwidth(), self._canv.winfo_reqheight(), fill=fillcolor, width=0)

        self._set()
        self.bind('<Configure>', self._update_coords)
        self._running = False

    def _update_coords(self, event):
        '''Updates the position of the rectangle inside the canvas when the size of
        the widget gets changed.'''
        # looks like we have to call update_idletasks() twice to make sure
        # to get the results we expect
        self._canv.update_idletasks()
        self._maximum = self._canv.winfo_width()
        self._startx = 0
        self._barwidth = self._maximum / self._bardiv
        if self._barwidth < 2:
            self._barwidth = 2
        stopx = self._startx + self._barwidth
        if stopx > self._maximum:
            stopx = self._maximum
        self._canv.coords(self._rect, 0, 0, stopx, self._canv.winfo_height())
        self._canv.update_idletasks()

    def _set(self):
        if self._startx < 0:
            self._startx = 0
        if self._startx > self._maximum:
            self._startx = self._startx % self._maximum
        stopx = self._startx + self._barwidth
        if stopx > self._maximum:
            stopx = self._maximum
        self._canv.coords(self._rect, self._startx, 0, stopx, self._canv.winfo_height())
        self._canv.update_idletasks()

    def start(self):
        self._running = True
        self.after(self._interval, self._step)

    def stop(self):
        self._running = False
        self._set()

    def _step(self):
        if self._running:
            stepsize = self._barwidth / 4
            if stepsize < 2:
                stepsize = 2
            self._startx += stepsize
            self._set()
            self.after(self._interval, self._step)
