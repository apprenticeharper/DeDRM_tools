#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import sys
sys.path.append('lib')

import os, os.path, urllib
import subprocess
from subprocess import Popen, PIPE, STDOUT
import Tkinter
import Tkconstants
import tkFileDialog
import tkMessageBox
import subasyncio
from subasyncio import Process
from scrolltextwidget import ScrolledText

class MainDialog(Tkinter.Frame):
    def __init__(self, root):
        Tkinter.Frame.__init__(self, root, border=5)
        self.root = root
        self.interval = 2000
        self.p2 = None
        self.status = Tkinter.Label(self, text='Extract Contents of Topaz eBook to a Directory')
        self.status.pack(fill=Tkconstants.X, expand=1)
        body = Tkinter.Frame(self)
        body.pack(fill=Tkconstants.X, expand=1)
        sticky = Tkconstants.E + Tkconstants.W
        body.grid_columnconfigure(1, weight=2)

        Tkinter.Label(body, text='Topaz eBook input file').grid(row=0, sticky=Tkconstants.E)
        self.tpzpath = Tkinter.Entry(body, width=50)
        self.tpzpath.grid(row=0, column=1, sticky=sticky)
        self.tpzpath.insert(0, os.getcwd())
        button = Tkinter.Button(body, text="...", command=self.get_tpzpath)
        button.grid(row=0, column=2)

        Tkinter.Label(body, text='Output Directory').grid(row=1, sticky=Tkconstants.E)
        self.outpath = Tkinter.Entry(body, width=50)
        self.outpath.grid(row=1, column=1, sticky=sticky)
        self.outpath.insert(0, os.getcwd())
        button = Tkinter.Button(body, text="...", command=self.get_outpath)
        button.grid(row=1, column=2)

        Tkinter.Label(body, text='First 8 char of PID (optional)').grid(row=3, sticky=Tkconstants.E)
        self.pidnum = Tkinter.StringVar()
        self.ccinfo = Tkinter.Entry(body, width=10, textvariable=self.pidnum)
        self.ccinfo.grid(row=3, column=1, sticky=sticky)

        msg1 = 'Conversion Log \n\n'
        self.stext = ScrolledText(body, bd=5, relief=Tkconstants.RIDGE, height=15, width=60, wrap=Tkconstants.WORD)
        self.stext.grid(row=4, column=0, columnspan=2,sticky=sticky)
        self.stext.insert(Tkconstants.END,msg1)

        buttons = Tkinter.Frame(self)
        buttons.pack()
        self.sbotton = Tkinter.Button(
            buttons, text="Start", width=10, command=self.convertit)
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
            msg = text + '\n\n' + 'Files successfully extracted\n'
            if poll != 0:
                msg = text + '\n\n' + 'Error: File Extraction Failed\n'
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
            self.stext.insert(Tkconstants.END,msg)
            self.stext.yview_pickplace(Tkconstants.END)
        return

    # run as a subprocess via pipes and collect stdout
    def topazrdr(self, infile, outdir, pidnum):
        # os.putenv('PYTHONUNBUFFERED', '1')
        pidoption = ''
        if pidnum and pidnum != '':
            pidoption = ' -p "' + pidnum + '" '
        outoption = ' -o "' + outdir + '" '
        cmdline = 'python ./lib/cmbtc_dump.py -v -d ' + pidoption + outoption + '"' + infile + '"'
        if sys.platform[0:3] == 'win':
            search_path = os.environ['PATH']
            search_path = search_path.lower()
            if search_path.find('python') >= 0: 
                cmdline = 'python lib\cmbtc_dump.py -v -d ' + pidoption + outoption + '"' + infile + '"'
            else :
                cmdline = 'lib\cmbtc_dump.py -v -d ' + pidoption + outoption + '"' + infile + '"'

        p2 = Process(cmdline, shell=True, bufsize=1, stdin=None, stdout=PIPE, stderr=PIPE, close_fds=False)
        return p2


    def get_tpzpath(self):
        tpzpath = tkFileDialog.askopenfilename(
            parent=None, title='Select Topaz File',
            defaultextension='.prc', filetypes=[('Topaz azw1', '.azw1'), ('Topaz prc', '.prc'),
                                                ('All Files', '.*')])
        if tpzpath:
            tpzpath = os.path.normpath(tpzpath)
            self.tpzpath.delete(0, Tkconstants.END)
            self.tpzpath.insert(0, tpzpath)
        return

    def get_outpath(self):
        outpath = tkFileDialog.askdirectory(
            parent=None, title='Directory to Extract Files into',
            initialdir=os.getcwd(), initialfile=None)
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
    def convertit(self):
        # now disable the button to prevent multiple launches
        self.sbotton.configure(state='disabled')
        tpzpath = self.tpzpath.get()
        outpath = self.outpath.get()
        if not tpzpath or not os.path.exists(tpzpath):
            self.status['text'] = 'Specified Topaz eBook file does not exist'
            self.sbotton.configure(state='normal')
            return
        if not outpath:
            self.status['text'] = 'No output directory specified'
            self.sbotton.configure(state='normal')
            return
        if not os.path.exists(outpath):
            os.makedirs(outpath)
        pidnum = self.pidnum.get()
        # if not pidnum or pidnum == '':
        #     self.status['text'] = 'You have not entered a PID '
        #     self.sbotton.configure(state='normal')
        #     return

        log = 'Command = "python cmbtc_dump.py"\n'
        log += 'Topaz Path Path = "'+ tpzpath + '"\n'
        log += 'Output Directory = "' + outpath + '"\n'
        log += 'First 8 chars of PID = "' + pidnum + '"\n'
        log += '\n\n'
        log += 'Please Wait ...\n'
        self.stext.insert(Tkconstants.END,log)
        self.p2 = self.topazrdr(tpzpath, outpath, pidnum)

        # python does not seem to allow you to create
        # your own eventloop which every other gui does - strange 
        # so need to use the widget "after" command to force
        # event loop to run non-gui events every interval
        self.stext.after(self.interval,self.processPipe)
        return


def main(argv=None):
    root = Tkinter.Tk()
    root.title('Topaz eBook File Extraction')
    root.resizable(True, False)
    root.minsize(300, 0)
    MainDialog(root).pack(fill=Tkconstants.X, expand=1)
    root.mainloop()
    return 0
    

if __name__ == "__main__":
    sys.exit(main())
