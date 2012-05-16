#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import sys
sys.path.append('lib')
import os, os.path, urllib
os.environ['PYTHONIOENCODING'] = "utf-8"

import Tkinter
import Tkconstants
import tkFileDialog
import tkMessageBox
from scrolltextwidget import ScrolledText
import subprocess
from subprocess import Popen, PIPE, STDOUT
import subasyncio
from subasyncio import Process

class MainDialog(Tkinter.Frame):
    def __init__(self, root):
        Tkinter.Frame.__init__(self, root, border=5)
        self.root = root
        self.interval = 1000
        self.p2 = None
        self.status = Tkinter.Label(self, text='Remove Encryption from a Kindle/Mobi/Topaz eBook')
        self.status.pack(fill=Tkconstants.X, expand=1)
        body = Tkinter.Frame(self)
        body.pack(fill=Tkconstants.X, expand=1)
        sticky = Tkconstants.E + Tkconstants.W
        body.grid_columnconfigure(1, weight=2)

        Tkinter.Label(body, text='Kindle/Mobi/Topaz eBook input file').grid(row=0, sticky=Tkconstants.E)
        self.mobipath = Tkinter.Entry(body, width=50)
        self.mobipath.grid(row=0, column=1, sticky=sticky)
        cwd = os.getcwdu()
        cwd = cwd.encode('utf-8')
        self.mobipath.insert(0, cwd)
        button = Tkinter.Button(body, text="...", command=self.get_mobipath)
        button.grid(row=0, column=2)

        Tkinter.Label(body, text='Directory for the Unencrypted Output File(s)').grid(row=1, sticky=Tkconstants.E)
        self.outpath = Tkinter.Entry(body, width=50)
        self.outpath.grid(row=1, column=1, sticky=sticky)
        cwd = os.getcwdu()
        cwd = cwd.encode('utf-8')
        outname = cwd
        self.outpath.insert(0, outname)
        button = Tkinter.Button(body, text="...", command=self.get_outpath)
        button.grid(row=1, column=2)

        Tkinter.Label(body, text='Optional Alternative Kindle.info file').grid(row=2, sticky=Tkconstants.E)
        self.altinfopath = Tkinter.Entry(body, width=50)
        self.altinfopath.grid(row=2, column=1, sticky=sticky)
        #cwd = os.getcwdu()
        #cwd = cwd.encode('utf-8')
        #self.altinfopath.insert(0, cwd)
        button = Tkinter.Button(body, text="...", command=self.get_altinfopath)
        button.grid(row=2, column=2)

        Tkinter.Label(body, text='Optional Comma Separated List of 10 Character PIDs (no spaces)').grid(row=3, sticky=Tkconstants.E)
        self.pidnums = Tkinter.StringVar()
        self.pidinfo = Tkinter.Entry(body, width=50, textvariable=self.pidnums)
        self.pidinfo.grid(row=3, column=1, sticky=sticky)

        Tkinter.Label(body, text='Optional Comma Separated List of 16 Character Kindle Serial Numbers (no spaces)').grid(row=4, sticky=Tkconstants.E)
        self.sernums = Tkinter.StringVar()
        self.serinfo = Tkinter.Entry(body, width=50, textvariable=self.sernums)
        self.serinfo.grid(row=4, column=1, sticky=sticky)


        msg1 = 'Conversion Log \n\n'
        self.stext = ScrolledText(body, bd=5, relief=Tkconstants.RIDGE, height=15, width=60, wrap=Tkconstants.WORD)
        self.stext.grid(row=6, column=0, columnspan=2,sticky=sticky)
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
            msg = text + '\n\n' + 'Encryption successfully removed\n'
            if poll == 1:
                msg = text + '\n\n' + 'Error: Encryption Removal Failed\n'
            if poll == 2:
                msg = text + '\n\n' + 'Input File was Not Encrypted - No Output File Needed\n'
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
    def mobirdr(self, infile, outfile, altinfopath, pidnums, sernums):
        # os.putenv('PYTHONUNBUFFERED', '1')
        tool = 'k4mobidedrm.py'
        pidoption = ''
        if pidnums and pidnums != '':
            pidoption = ' -p "' + pidnums + '" '
        seroption = ''
        if sernums and sernums != '':
            seroption = ' -s "' + sernums + '" '
        infooption = ''
        if altinfopath and altinfopath != '':
            infooption = ' -k "' + altinfopath + '" '
        pengine = sys.executable
        if pengine is None or pengine == '':
            pengine = "python"
        pengine = os.path.normpath(pengine)
        cmdline = pengine + ' ./lib/' + tool + ' ' + pidoption + seroption + infooption + '"' + infile + '" "' + outfile + '"'
        if sys.platform.startswith('win'):
                cmdline = pengine + ' lib\\' + tool + ' ' + pidoption + seroption + infooption + '"' + infile + '" "' + outfile + '"'
        print cmdline
        cmdline = cmdline.encode(sys.getfilesystemencoding())
        p2 = Process(cmdline, shell=True, bufsize=1, stdin=None, stdout=PIPE, stderr=PIPE, close_fds=False)
        return p2


    def get_mobipath(self):
        cpath = self.mobipath.get()
        mobipath = tkFileDialog.askopenfilename(
            initialdir = cpath,
            parent=None, title='Select Kindle/Mobi/Topaz  eBook File',
            defaultextension='.prc', filetypes=[('Mobi eBook File', '.prc'), ('Mobi eBook File', '.azw'),('Mobi eBook File', '.mobi'),('Mobi eBook File', '.tpz'),('Mobi eBook File', '.azw1'),('Mobi azw4 eBook File', '.azw4'),('All Files', '.*')])
        if mobipath:
            mobipath = os.path.normpath(mobipath)
            self.mobipath.delete(0, Tkconstants.END)
            self.mobipath.insert(0, mobipath)
        return

    def get_outpath(self):
        cwd = os.getcwdu()
        cwd = cwd.encode('utf-8')
        outpath = tkFileDialog.askdirectory(
            parent=None, title='Directory to Store Unencrypted file(s) into',
            initialdir=cwd, initialfile=None)
        if outpath:
            outpath = os.path.normpath(outpath)
            self.outpath.delete(0, Tkconstants.END)
            self.outpath.insert(0, outpath)
        return

    def get_altinfopath(self):
        cwd = os.getcwdu()
        cwd = cwd.encode('utf-8')
        altinfopath = tkFileDialog.askopenfilename(
            parent=None, title='Select Alternative kindle.info File',
            defaultextension='.prc', filetypes=[('Kindle Info', '.info'),
                                                ('All Files', '.*')],
            initialdir=cwd)
        if altinfopath:
            altinfopath = os.path.normpath(altinfopath)
            self.altinfopath.delete(0, Tkconstants.END)
            self.altinfopath.insert(0, altinfopath)
        return

    def quitting(self):
        # kill any still running subprocess
        if self.p2 != None:
            if (self.p2.wait('nowait') == None):
                self.p2.terminate()
        self.root.destroy()

    # actually ready to run the subprocess and get its output
    def convertit(self):
        self.status['text'] = ''
        # now disable the button to prevent multiple launches
        self.sbotton.configure(state='disabled')
        mobipath = self.mobipath.get()
        outpath = self.outpath.get()
        altinfopath = self.altinfopath.get()
        pidnums = self.pidinfo.get()
        sernums = self.serinfo.get()

        if not mobipath or not os.path.exists(mobipath) or not os.path.isfile(mobipath):
            self.status['text'] = 'Specified Kindle Mobi eBook file does not exist'
            self.sbotton.configure(state='normal')
            return

        tpz = False
        # Identify any Topaz Files
        f = file(mobipath, 'rb')
        raw = f.read(3)
        if raw.startswith('TPZ'):
            tpz = True
        f.close()
        if not outpath:
            self.status['text'] = 'No output directory specified'
            self.sbotton.configure(state='normal')
            return
        if not os.path.isdir(outpath):
            self.status['text'] = 'Error specified output directory does not exist'
            self.sbotton.configure(state='normal')
            return
        if altinfopath and not os.path.exists(altinfopath):
            self.status['text'] = 'Specified kindle.info file does not exist'
            self.sbotton.configure(state='normal')
            return

        log = 'Command = "python k4mobidedrm.py"\n'
        if not tpz:
            log += 'Kindle/Mobi Path = "'+ mobipath + '"\n'
        else:
            log += 'Topaz Path = "'+ mobipath + '"\n'
        log += 'Output Directory = "' + outpath + '"\n'
        log += 'Kindle.info file = "' + altinfopath + '"\n'
        log += 'PID list = "' + pidnums + '"\n'
        log += 'Serial Number list = "' + sernums + '"\n'
        log += '\n\n'
        log += 'Please Wait ...\n\n'
        log = log.encode('utf-8')
        self.stext.insert(Tkconstants.END,log)
        self.p2 = self.mobirdr(mobipath, outpath, altinfopath, pidnums, sernums)

        # python does not seem to allow you to create
        # your own eventloop which every other gui does - strange
        # so need to use the widget "after" command to force
        # event loop to run non-gui events every interval
        self.stext.after(self.interval,self.processPipe)
        return


def main(argv=None):
    root = Tkinter.Tk()
    root.title('Kindle/Mobi/Topaz eBook Encryption Removal')
    root.resizable(True, False)
    root.minsize(300, 0)
    MainDialog(root).pack(fill=Tkconstants.X, expand=1)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
