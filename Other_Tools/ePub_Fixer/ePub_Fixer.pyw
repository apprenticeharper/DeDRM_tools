#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import sys
sys.path.append('lib')
import os, os.path, urllib
os.environ['PYTHONIOENCODING'] = "utf-8"

import subprocess
from subprocess import Popen, PIPE, STDOUT
import subasyncio
from subasyncio import Process
import Tkinter
import Tkconstants
import tkFileDialog
import tkMessageBox
from scrolltextwidget import ScrolledText

class MainDialog(Tkinter.Frame):
    def __init__(self, root):
        Tkinter.Frame.__init__(self, root, border=5)
        self.root = root
        self.interval = 2000
        self.p2 = None
        self.status = Tkinter.Label(self, text='Fix Improper ePubs')
        self.status.pack(fill=Tkconstants.X, expand=1)
        body = Tkinter.Frame(self)
        body.pack(fill=Tkconstants.X, expand=1)
        sticky = Tkconstants.E + Tkconstants.W
        body.grid_columnconfigure(1, weight=2)

        Tkinter.Label(body, text='ePub input file').grid(row=0, sticky=Tkconstants.E)
        self.epubpath = Tkinter.Entry(body, width=50)
        self.epubpath.grid(row=0, column=1, sticky=sticky)
        cwd = os.getcwdu()
        cwd = cwd.encode('utf-8')
        self.epubpath.insert(0, cwd)
        button = Tkinter.Button(body, text="...", command=self.get_epubpath)
        button.grid(row=0, column=2)

        Tkinter.Label(body, text='Directory to store fixed ePub in').grid(row=1, sticky=Tkconstants.E)
        self.outpath = Tkinter.Entry(body, width=50)
        self.outpath.grid(row=1, column=1, sticky=sticky)
        cwd = os.getcwdu()
        cwd = cwd.encode('utf-8')
        outname = cwd
        self.outpath.insert(0, outname)
        button = Tkinter.Button(body, text="...", command=self.get_outpath)
        button.grid(row=1, column=2)

        msg1 = 'Log \n\n'
        self.stext = ScrolledText(body, bd=5, relief=Tkconstants.RIDGE, height=15, width=60, wrap=Tkconstants.WORD)
        self.stext.grid(row=2, column=0, columnspan=2,sticky=sticky)
        self.stext.insert(Tkconstants.END,msg1)

        buttons = Tkinter.Frame(self)
        buttons.pack()
        self.sbotton = Tkinter.Button(
            buttons, text="Start", width=10, command=self.fixit)
        self.sbotton.pack(side=Tkconstants.LEFT)

        Tkinter.Frame(buttons, width=10).pack(side=Tkconstants.LEFT)
        self.qbutton = Tkinter.Button(
            buttons, text="Quit", width=10, command=self.quitting)
        self.qbutton.pack(side=Tkconstants.RIGHT)

    # read from subprocess pipe without blocking
    # invoked every interval via the widget "after"
    # option being used, so need to reset it for the next time
    def processPipe(self):
        poll = self.p2.wait('nowait')
        if poll != None: 
            text = self.p2.readerr()
            text += self.p2.read()
            msg = text + '\n\n' + 'ePub successfully fixed\n'
            if poll != 0:
                msg = text + '\n\n' + 'Error: ePub Fixing Failed\n'
            self.showCmdOutput(msg)
            self.p2 = None
            self.sbotton.configure(state='normal')
            return
        text = self.p2.readerr()
        text += self.p2.read()
        self.showCmdOutput(text)
        # make sure we get invoked again by event loop after interval 
        self.stext.after(self.interval,self.processPipe)
        return

    # post output from subprocess in scrolled text widget
    def showCmdOutput(self, msg):
        if msg and msg !='':
            if sys.platform.startswith('win'):
                msg = msg.replace('\r\n','\n')
            self.stext.insert(Tkconstants.END,msg)
            self.stext.yview_pickplace(Tkconstants.END)
        return

    # run as a subprocess via pipes and collect stdout
    def zipfixrdr(self, infile, outfile):
        # os.putenv('PYTHONUNBUFFERED', '1')
        pengine = sys.executable
        if pengine is None or pengine == '':
            pengine = "python"
        pengine = os.path.normpath(pengine)
        cmdline = pengine + ' ./lib/zipfix.py "' + infile + '" "' + outfile + '"'
        if sys.platform[0:3] == 'win':
            # search_path = os.environ['PATH']
            # search_path = search_path.lower()
            # if search_path.find('python') >= 0: 
            #     cmdline = 'python lib\zipfix.py "' + infile + '" "' + outfile + '"'
            # else :
            #     cmdline = 'lib\zipfix.py "' + infile + '" "' + outfile + '"'
            cmdline = pengine + ' lib\\zipfix.py "' + infile + '" "' + outfile + '"'

        cmdline = cmdline.encode(sys.getfilesystemencoding())
        p2 = Process(cmdline, shell=True, bufsize=1, stdin=None, stdout=PIPE, stderr=PIPE, close_fds=False)
        return p2


    def get_epubpath(self):
        epubpath = tkFileDialog.askopenfilename(
            parent=None, title='Select ePub to be Fixed',
            defaultextension='.epub', filetypes=[('ePub eBook File', '.epub'), ('Zip File', '.zip'),('All Files', '.*')])
        if epubpath:
            epubpath = os.path.normpath(epubpath)
            self.epubpath.delete(0, Tkconstants.END)
            self.epubpath.insert(0, epubpath)
        return

    def get_outpath(self):
        cwd = os.getcwdu()
        cwd = cwd.encode('utf-8')
        outpath = tkFileDialog.askdirectory(
            parent=None, title='Directory to Store Fixed ePub into',
            initialdir=cwd, initialfile=None)
        if outpath:
            outpath = os.path.normpath(outpath)
            self.outpath.delete(0, Tkconstants.END)
            self.outpath.insert(0, outpath)
        return

    def quitting(self):
        # kill any still running subprocess
        if self.p2 != None:
            if (self.p2.wait('nowait') == None):
                self.p2.terminate()
        self.root.destroy()

    # actually ready to run the subprocess and get its output
    def fixit(self):
        # now disable the button to prevent multiple launches
        self.sbotton.configure(state='disabled')
        epubpath = self.epubpath.get()
        outpath = self.outpath.get()
        if not epubpath or not os.path.exists(epubpath):
            self.status['text'] = 'Specified ePub eBook file does not exist'
            self.sbotton.configure(state='normal')
            return
        if not outpath:
            self.status['text'] = 'Error specified output directory does not exist'
            self.sbotton.configure(state='normal')
            return

        # default output file name to be input file name + '_fixed.epub'
        initname = os.path.splitext(os.path.basename(epubpath))[0]
        initname += '_fixed.epub' 
        outpath += os.sep + initname

        log = 'Command = "python zipfix.py"\n'
        log += 'ePub Path = "'+ epubpath + '"\n'
        log += 'Output File = "' + outpath + '"\n'
        log += '\n\n'
        log += 'Please Wait ...\n\n'
        self.stext.insert(Tkconstants.END,log)
        self.p2 = self.zipfixrdr(epubpath, outpath)

        # python does not seem to allow you to create
        # your own eventloop which every other gui does - strange 
        # so need to use the widget "after" command to force
        # event loop to run non-gui events every interval
        self.stext.after(self.interval,self.processPipe)
        return


def main(argv=None):
    root = Tkinter.Tk()
    root.title('Fix Incorrect ePubs')
    root.resizable(True, False)
    root.minsize(300, 0)
    MainDialog(root).pack(fill=Tkconstants.X, expand=1)
    root.mainloop()
    return 0
    

if __name__ == "__main__":
    sys.exit(main())
