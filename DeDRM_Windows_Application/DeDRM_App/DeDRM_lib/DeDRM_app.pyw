#!/usr/bin/env python
# -*- coding: utf-8 -*-

# DeDRM.pyw, version 6.0.1
# Copyright 2010-2013 some_updates and Apprentice Alf

# Revision history:
#   6.0.0 - Release along with unified plugin
#   6.0.1 - Bug Fixes for Windows App
#   6.0.2 - Fixed problem with spaces in paths and the bat file
#   6.0.3 - Fix for Windows non-ascii user names
#   6.0.4 - Fix for other potential unicode problems

__version__ = '6.0.4'

import sys
import os, os.path
sys.path.append(os.path.join(sys.path[0],"lib"))
import sys, os
import codecs

from argv_utils import add_cp65001_codec, set_utf8_default_encoding, unicode_argv
add_cp65001_codec()
set_utf8_default_encoding()


import shutil
import Tkinter
from Tkinter import *
import Tkconstants
import tkFileDialog
from scrolltextwidget import ScrolledText
from activitybar import ActivityBar
if sys.platform.startswith("win"):
    from askfolder_ed import AskFolder
import re
import simpleprefs
import traceback

from Queue import Full
from Queue import Empty
from multiprocessing import Process, Queue

from scriptinterface import decryptepub, decryptpdb, decryptpdf, decryptk4mobi


# Wrap a stream so that output gets flushed immediately
# and appended to shared queue
class QueuedUTF8Stream:
    def __init__(self, stream, q):
        self.stream = stream
        self.encoding = 'utf-8'
        self.q = q
    def write(self, data):
        if isinstance(data,unicode):
            data = data.encode('utf-8',"replace")
        self.q.put(data)
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

class DrmException(Exception):
    pass

class MainApp(Tk):
    def __init__(self, apphome, dnd=False, filenames=[]):
        Tk.__init__(self)
        self.withdraw()
        self.dnd = dnd
        self.apphome = apphome

        # preference settings
        # [dictionary key, file in preferences directory where info is stored]
        description = [ ['pids'   , 'pidlist.txt'   ],
                        ['serials', 'seriallist.txt'],
                        ['sdrms'  , 'sdrmlist.txt'  ],
                        ['outdir' , 'outdir.txt'    ]]
        self.po = simpleprefs.SimplePrefs("DeDRM",description)
        if self.dnd:
            self.cd = ConvDialog(self)
            prefs = self.getPreferences()
            self.cd.doit(prefs, filenames)
        else:
            prefs = self.getPreferences()
            self.pd = PrefsDialog(self, prefs)
            self.cd = ConvDialog(self)
            self.pd.show()

    def getPreferences(self):
        prefs = self.po.getPreferences()
        prefdir = prefs['dir']
        adeptkeyfile = os.path.join(prefdir,'adeptkey.der')
        if not os.path.exists(adeptkeyfile):
            import adobekey
            try:
                adobekey.getkey(adeptkeyfile)
            except:
                pass
        kindlekeyfile = os.path.join(prefdir,'kindlekey.k4i')
        if not os.path.exists(kindlekeyfile):
            import kindlekey
            try:
                kindlekey.getkey(kindlekeyfile)
            except:
                traceback.print_exc()
                pass
        return prefs

    def setPreferences(self, newprefs):
        prefdir = self.po.prefdir
        if 'adkfile' in newprefs:
            dfile = newprefs['adkfile']
            fname = os.path.basename(dfile)
            nfile = os.path.join(prefdir,fname)
            if os.path.isfile(dfile):
                shutil.copyfile(dfile,nfile)
        if 'bnkfile' in newprefs:
            dfile = newprefs['bnkfile']
            fname = os.path.basename(dfile)
            nfile = os.path.join(prefdir,fname)
            if os.path.isfile(dfile):
                shutil.copyfile(dfile,nfile)
        if 'kinfofile' in newprefs:
            dfile = newprefs['kinfofile']
            fname = os.path.basename(dfile)
            nfile = os.path.join(prefdir,fname)
            if os.path.isfile(dfile):
                shutil.copyfile(dfile,nfile)
        self.po.setPreferences(newprefs)
        return

    def alldone(self):
        if not self.dnd:
            self.pd.enablebuttons()
        else:
            self.destroy()

class PrefsDialog(Toplevel):
    def __init__(self, mainapp, prefs_array):
        Toplevel.__init__(self, mainapp)
        self.withdraw()
        self.protocol("WM_DELETE_WINDOW", self.withdraw)
        self.title("DeDRM " + __version__)
        self.prefs_array = prefs_array
        self.status = Tkinter.Label(self, text='Setting Preferences')
        self.status.pack(fill=Tkconstants.X, expand=1)
        body = Tkinter.Frame(self)
        self.body = body
        body.pack(fill=Tkconstants.X, expand=1)
        sticky = Tkconstants.E + Tkconstants.W
        body.grid_columnconfigure(1, weight=2)

        Tkinter.Label(body, text='Adobe Key file (adeptkey.der)').grid(row=0, sticky=Tkconstants.E)
        self.adkpath = Tkinter.Entry(body, width=50)
        self.adkpath.grid(row=0, column=1, sticky=sticky)
        prefdir = self.prefs_array['dir']
        keyfile = os.path.join(prefdir,'adeptkey.der')
        if os.path.isfile(keyfile):
            path = keyfile
            self.adkpath.insert(0, path)
        button = Tkinter.Button(body, text="...", command=self.get_adkpath)
        button.grid(row=0, column=2)

        Tkinter.Label(body, text='Kindle Key file (kindlekey.k4i)').grid(row=1, sticky=Tkconstants.E)
        self.kkpath = Tkinter.Entry(body, width=50)
        self.kkpath.grid(row=1, column=1, sticky=sticky)
        prefdir = self.prefs_array['dir']
        keyfile = os.path.join(prefdir,'kindlekey.k4i')
        if os.path.isfile(keyfile):
            path = keyfile
            self.kkpath.insert(1, path)
        button = Tkinter.Button(body, text="...", command=self.get_kkpath)
        button.grid(row=1, column=2)

        Tkinter.Label(body, text='Barnes and Noble Key file (bnepubkey.b64)').grid(row=2, sticky=Tkconstants.E)
        self.bnkpath = Tkinter.Entry(body, width=50)
        self.bnkpath.grid(row=2, column=1, sticky=sticky)
        prefdir = self.prefs_array['dir']
        keyfile = os.path.join(prefdir,'bnepubkey.b64')
        if os.path.isfile(keyfile):
            path = keyfile
            self.bnkpath.insert(2, path)
        button = Tkinter.Button(body, text="...", command=self.get_bnkpath)
        button.grid(row=2, column=2)

        Tkinter.Label(body, text='Mobipocket PID list\n(8 or 10 characters, comma separated)').grid(row=3, sticky=Tkconstants.E)
        self.pidnums = Tkinter.StringVar()
        self.pidinfo = Tkinter.Entry(body, width=50, textvariable=self.pidnums)
        if 'pids' in self.prefs_array:
            self.pidnums.set(self.prefs_array['pids'])
        self.pidinfo.grid(row=3, column=1, sticky=sticky)

        Tkinter.Label(body, text='eInk Kindle Serial Number list\n(16 characters, comma separated)').grid(row=4, sticky=Tkconstants.E)
        self.sernums = Tkinter.StringVar()
        self.serinfo = Tkinter.Entry(body, width=50, textvariable=self.sernums)
        if 'serials' in self.prefs_array:
            self.sernums.set(self.prefs_array['serials'])
        self.serinfo.grid(row=4, column=1, sticky=sticky)

        Tkinter.Label(body, text='eReader data list\n(name:last 8 digits on credit card, comma separated)').grid(row=5, sticky=Tkconstants.E)
        self.sdrmnums = Tkinter.StringVar()
        self.sdrminfo = Tkinter.Entry(body, width=50, textvariable=self.sdrmnums)
        if 'sdrms' in self.prefs_array:
            self.sdrmnums.set(self.prefs_array['sdrms'])
        self.sdrminfo.grid(row=5, column=1, sticky=sticky)

        Tkinter.Label(body, text="Output Folder (if blank, use input ebook's folder)").grid(row=6, sticky=Tkconstants.E)
        self.outpath = Tkinter.Entry(body, width=50)
        self.outpath.grid(row=6, column=1, sticky=sticky)
        if 'outdir' in self.prefs_array:
            dpath = self.prefs_array['outdir']
            self.outpath.insert(0, dpath)
        button = Tkinter.Button(body, text="...", command=self.get_outpath)
        button.grid(row=6, column=2)

        Tkinter.Label(body, text='').grid(row=7, column=0, columnspan=2, sticky=Tkconstants.N)

        Tkinter.Label(body, text='Alternatively Process an eBook').grid(row=8, column=0, columnspan=2, sticky=Tkconstants.N)

        Tkinter.Label(body, text='Select an eBook to Process*').grid(row=9, sticky=Tkconstants.E)
        self.bookpath = Tkinter.Entry(body, width=50)
        self.bookpath.grid(row=9, column=1, sticky=sticky)
        button = Tkinter.Button(body, text="...", command=self.get_bookpath)
        button.grid(row=9, column=2)

        Tkinter.Label(body, font=("Helvetica", "10", "italic"), text='*To DeDRM multiple ebooks simultaneously, set your preferences and quit.\nThen drag and drop ebooks or folders onto the DeDRM_Drop_Target').grid(row=10, column=1, sticky=Tkconstants.E)

        Tkinter.Label(body, text='').grid(row=11, column=0, columnspan=2, sticky=Tkconstants.E)

        buttons = Tkinter.Frame(self)
        buttons.pack()
        self.sbotton = Tkinter.Button(buttons, text="Set Prefs", width=14, command=self.setprefs)
        self.sbotton.pack(side=Tkconstants.LEFT)

        buttons.pack()
        self.pbotton = Tkinter.Button(buttons, text="Process eBook", width=14, command=self.doit)
        self.pbotton.pack(side=Tkconstants.LEFT)
        buttons.pack()
        self.qbotton = Tkinter.Button(buttons, text="Quit", width=14, command=self.quitting)
        self.qbotton.pack(side=Tkconstants.RIGHT)
        buttons.pack()

    def disablebuttons(self):
        self.sbotton.configure(state='disabled')
        self.pbotton.configure(state='disabled')
        self.qbotton.configure(state='disabled')

    def enablebuttons(self):
        self.sbotton.configure(state='normal')
        self.pbotton.configure(state='normal')
        self.qbotton.configure(state='normal')

    def show(self):
        self.deiconify()
        self.tkraise()

    def hide(self):
        self.withdraw()

    def get_outpath(self):
        cpath = self.outpath.get()
        if sys.platform.startswith("win"):
            # tk_chooseDirectory is horribly broken for unicode paths
            # on windows - bug has been reported but not fixed for years
            # workaround by using our own unicode aware version
            outpath = AskFolder(message="Choose the folder for DRM-free ebooks",
                defaultLocation=cpath)
        else:
            outpath = tkFileDialog.askdirectory(
                parent=None, title='Choose the folder for DRM-free ebooks',
                initialdir=cpath, initialfile=None)
        if outpath:
            outpath = os.path.normpath(outpath)
            self.outpath.delete(0, Tkconstants.END)
            self.outpath.insert(0, outpath)
        return

    def get_adkpath(self):
        cpath = self.adkpath.get()
        adkpath = tkFileDialog.askopenfilename(initialdir = cpath, parent=None, title='Select Adept Key file',
            defaultextension='.der', filetypes=[('Adept Key file', '.der'), ('All Files', '.*')])
        if adkpath:
            adkpath = os.path.normpath(adkpath)
            self.adkpath.delete(0, Tkconstants.END)
            self.adkpath.insert(0, adkpath)
        return

    def get_kkpath(self):
        cpath = self.kkpath.get()
        kkpath = tkFileDialog.askopenfilename(initialdir = cpath, parent=None, title='Select Kindle Key file',
            defaultextension='.k4i', filetypes=[('Kindle Key file', '.k4i'), ('All Files', '.*')])
        if kkpath:
            kkpath = os.path.normpath(kkpath)
            self.kkpath.delete(0, Tkconstants.END)
            self.kkpath.insert(0, kkpath)
        return

    def get_bnkpath(self):
        cpath = self.bnkpath.get()
        bnkpath = tkFileDialog.askopenfilename(initialdir = cpath, parent=None, title='Select Barnes and Noble Key file',
            defaultextension='.b64', filetypes=[('Barnes and Noble Key file', '.b64'), ('All Files', '.*')])
        if bnkpath:
            bnkpath = os.path.normpath(bnkpath)
            self.bnkpath.delete(0, Tkconstants.END)
            self.bnkpath.insert(0, bnkpath)
        return

    def get_bookpath(self):
        cpath = self.bookpath.get()
        bookpath = tkFileDialog.askopenfilename(parent=None, title='Select eBook for DRM Removal',
            filetypes=[('All Files', '.*'),
                    ('ePub Files','.epub'),
                    ('Kindle','.azw'),
                    ('Kindle','.azw1'),
                    ('Kindle','.azw3'),
                    ('Kindle','.azw4'),
                    ('Kindle','.tpz'),
                    ('Kindle','.mobi'),
                    ('Kindle','.prc'),
                    ('eReader','.pdb'),
                    ('PDF','.pdf')],
            initialdir=cpath)
        if bookpath:
            bookpath = os.path.normpath(bookpath)
            self.bookpath.delete(0, Tkconstants.END)
            self.bookpath.insert(0, bookpath)
        return

    def quitting(self):
        self.master.destroy()

    def setprefs(self):
        # setting new prefereces
        new_prefs = {}
        prefdir = self.prefs_array['dir']
        new_prefs['dir'] = prefdir
        new_prefs['pids'] = self.pidinfo.get().replace(" ","")
        new_prefs['serials'] = self.serinfo.get().replace(" ","")
        new_prefs['sdrms'] = self.sdrminfo.get().strip().replace(", ",",")
        new_prefs['outdir'] = self.outpath.get().strip()
        adkpath = self.adkpath.get()
        if os.path.dirname(adkpath) != prefdir:
            new_prefs['adkfile'] = adkpath
        bnkpath = self.bnkpath.get()
        if os.path.dirname(bnkpath) != prefdir:
            new_prefs['bnkfile'] = bnkpath
        kkpath = self.kkpath.get()
        if os.path.dirname(kkpath) != prefdir:
            new_prefs['kindlefile'] = kkpath
        self.master.setPreferences(new_prefs)
        # and update internal copies
        self.prefs_array['pids'] = new_prefs['pids']
        self.prefs_array['serials'] = new_prefs['serials']
        self.prefs_array['sdrms'] = new_prefs['sdrms']
        self.prefs_array['outdir'] = new_prefs['outdir']

    def doit(self):
        self.disablebuttons()
        filenames=[]
        bookpath = self.bookpath.get()
        bookpath = os.path.abspath(bookpath)
        filenames.append(bookpath)
        self.master.cd.doit(self.prefs_array,filenames)



class ConvDialog(Toplevel):
    def __init__(self, master, prefs_array={}, filenames=[]):
        Toplevel.__init__(self, master)
        self.withdraw()
        self.protocol("WM_DELETE_WINDOW", self.withdraw)
        self.title("DeDRM Processing")
        self.master = master
        self.apphome = self.master.apphome
        self.prefs_array = prefs_array
        self.filenames = filenames
        self.interval = 50
        self.p2 = None
        self.q = Queue()
        self.running = 'inactive'
        self.numgood = 0
        self.numbad = 0
        self.status = Tkinter.Label(self, text='DeDRM processing...')
        self.status.pack(fill=Tkconstants.X, expand=1)
        body = Tkinter.Frame(self)
        body.pack(fill=Tkconstants.X, expand=1)
        sticky = Tkconstants.E + Tkconstants.W
        body.grid_columnconfigure(1, weight=2)

        Tkinter.Label(body, text='Activity Bar').grid(row=0, sticky=Tkconstants.E)
        self.bar = ActivityBar(body, length=80, height=15, barwidth=5)
        self.bar.grid(row=0, column=1, sticky=sticky)

        msg1 = ''
        self.stext = ScrolledText(body, bd=5, relief=Tkconstants.RIDGE, height=4, width=80, wrap=Tkconstants.WORD)
        self.stext.grid(row=2, column=0, columnspan=2,sticky=sticky)
        self.stext.insert(Tkconstants.END,msg1)

        buttons = Tkinter.Frame(self)
        buttons.pack()
        self.qbutton = Tkinter.Button(buttons, text="Quit", width=14, command=self.quitting)
        self.qbutton.pack(side=Tkconstants.BOTTOM)
        self.status['text'] = ''

        self.logfile = open(os.path.join(os.path.expanduser('~'),'DeDRM.log'),'w')

    def show(self):
        self.deiconify()
        self.tkraise()

    def hide(self):
        self.withdraw()

    def doit(self, prefs, filenames):
        self.running = 'inactive'
        self.prefs_array = prefs
        self.filenames = filenames
        self.show()
        self.processBooks()

    def conversion_done(self):
        self.hide()
        self.master.alldone()

    def processBooks(self):
        while self.running == 'inactive':
            rscpath = self.prefs_array['dir']
            filename = None
            if len(self.filenames) > 0:
                filename = self.filenames.pop(0)
            if filename == None:
                msg = 'Complete:  '
                msg += 'Successes: %d, ' % self.numgood
                msg += 'Failures: %d\n' % self.numbad
                self.showCmdOutput(msg)
                if self.numbad == 0:
                    self.after(2000,self.conversion_done())
                self.logfile.write("DeDRM v{0}: {1}".format(__version__,msg))
                self.logfile.close()
                return
            infile = filename
            bname = os.path.basename(infile)
            msg = 'Processing: ' + bname + '...'
            self.logfile.write("DeDRM v{0}: {1}\n".format(__version__,msg))
            self.showCmdOutput(msg)
            outdir = os.path.dirname(filename)
            if 'outdir' in self.prefs_array:
                dpath = self.prefs_array['outdir']
                if dpath.strip() != '':
                    outdir = dpath
            rv = self.decrypt_ebook(infile, outdir, rscpath)
            if rv == 0:
                self.bar.start()
                self.running = 'active'
                self.processQueue()
            else:
                msg = 'Unknown File: ' + bname + '\n'
                self.logfile.write("DeDRM v{0}: {1}".format(__version__,msg))
                self.showCmdOutput(msg)
                self.numbad += 1

    def quitting(self):
        # kill any still running subprocess
        self.running = 'stopped'
        if self.p2 != None:
            if (self.p2.exitcode == None):
                self.p2.terminate()
        self.conversion_done()

    # post output from subprocess in scrolled text widget
    def showCmdOutput(self, msg):
        if msg and msg !='':
            if sys.platform.startswith('win'):
                msg = msg.replace('\r\n','\n')
            self.stext.insert(Tkconstants.END,msg)
            self.stext.yview_pickplace(Tkconstants.END)
        return

    # read from subprocess pipe without blocking
    # invoked every interval via the widget "after"
    # option being used, so need to reset it for the next time
    def processQueue(self):
        if self.p2 == None:
            # nothing to wait for so just return
            return
        poll = self.p2.exitcode
        #print "processing", poll
        done = False
        text = ''
        while not done:
            try:
                data = self.q.get_nowait()
                text += data
            except Empty:
                done = True
        if text != '':
            self.logfile.write(text)
        if poll != None:
            self.bar.stop()
            if poll == 0:
                msg = 'Success\n'
                self.numgood += 1
            else:
                msg = 'Failed\n'
                self.numbad += 1
            self.p2.join()
            self.logfile.write("DeDRM v{0}: {1}\n".format(__version__,msg))
            self.showCmdOutput(msg)
            self.p2 = None
            self.running = 'inactive'
            self.after(50,self.processBooks)
            return
        # make sure we get invoked again by event loop after interval
        self.stext.after(self.interval,self.processQueue)
        return

    def decrypt_ebook(self, infile, outdir, rscpath):
        q = self.q
        rv = 1
        name, ext = os.path.splitext(os.path.basename(infile))
        ext = ext.lower()
        if ext == '.epub':
            self.p2 = Process(target=processEPUB, args=(q, infile, outdir, rscpath))
            self.p2.start()
            return 0
        if ext == '.pdb':
            self.p2 = Process(target=processPDB, args=(q, infile, outdir, rscpath))
            self.p2.start()
            return 0
        if ext in ['.azw', '.azw1', '.azw3', '.azw4', '.prc', '.mobi', '.tpz']:
            self.p2 = Process(target=processK4MOBI,args=(q, infile, outdir, rscpath))
            self.p2.start()
            return 0
        if ext == '.pdf':
            self.p2 = Process(target=processPDF, args=(q, infile, outdir, rscpath))
            self.p2.start()
            return 0
        return rv


# child process starts here
def processK4MOBI(q, infile, outdir, rscpath):
    add_cp65001_codec()
    set_utf8_default_encoding()
    sys.stdout = QueuedUTF8Stream(sys.stdout, q)
    sys.stderr = QueuedUTF8Stream(sys.stderr, q)
    rv = decryptk4mobi(infile, outdir, rscpath)
    sys.exit(rv)

# child process starts here
def processPDF(q, infile, outdir, rscpath):
    add_cp65001_codec()
    set_utf8_default_encoding()
    sys.stdout = QueuedUTF8Stream(sys.stdout, q)
    sys.stderr = QueuedUTF8Stream(sys.stderr, q)
    rv = decryptpdf(infile, outdir, rscpath)
    sys.exit(rv)

# child process starts here
def processEPUB(q, infile, outdir, rscpath):
    add_cp65001_codec()
    set_utf8_default_encoding()
    sys.stdout = QueuedUTF8Stream(sys.stdout, q)
    sys.stderr = QueuedUTF8Stream(sys.stderr, q)
    rv = decryptepub(infile, outdir, rscpath)
    sys.exit(rv)

# child process starts here
def processPDB(q, infile, outdir, rscpath):
    add_cp65001_codec()
    set_utf8_default_encoding()
    sys.stdout = QueuedUTF8Stream(sys.stdout, q)
    sys.stderr = QueuedUTF8Stream(sys.stderr, q)
    rv = decryptpdb(infile, outdir, rscpath)
    sys.exit(rv)


def main():
    argv=unicode_argv()
    apphome = os.path.dirname(argv[0])
    apphome = os.path.abspath(apphome)

    # windows may pass a spurious quoted null string as argv[1] from bat file
    # simply work around this until we can figure out a better way to handle things
    if sys.platform.startswith('win') and len(argv) == 2:
        temp = argv[1]
        temp = temp.strip('"')
        temp = temp.strip()
        if temp == '':
            argv.pop()

    if len(argv) == 1:
        filenames = []
        dnd = False

    else : # processing books via drag and drop
        dnd = True
        # build a list of the files to be processed
        # note all filenames and paths have been utf-8 encoded
        infilelst = argv[1:]
        filenames = []
        for infile in infilelst:
            infile = infile.replace('"','')
            infile = os.path.abspath(infile)
            if os.path.isdir(infile):
                bpath = infile
                filelst = os.listdir(infile)
                for afile in filelst:
                    if not afile.startswith('.'):
                        filepath = os.path.join(bpath,afile)
                        if os.path.isfile(filepath):
                            filenames.append(filepath)
            else :
                afile = os.path.basename(infile)
                if not afile.startswith('.'):
                    if os.path.isfile(infile):
                        filenames.append(infile)

    # start up gui app
    app = MainApp(apphome, dnd, filenames)
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
