#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import sys
sys.path.append('lib')
import os, os.path, urllib
import subprocess
from subprocess import Popen, PIPE, STDOUT
import subasyncio
from subasyncio import Process
import Tkinter
import Tkconstants
import tkFileDialog
import tkMessageBox
from scrolltextwidget import ScrolledText
import binascii
import hashlib


#
# Returns the SHA1 digest of "message"
#
def SHA1(message):
    ctx = hashlib.sha1()
    ctx.update(message)
    return ctx.hexdigest()


class MainDialog(Tkinter.Frame):
    def __init__(self, root):
        Tkinter.Frame.__init__(self, root, border=5)
        self.root = root
        self.interval = 2000
        self.p2 = None
        self.status = Tkinter.Label(self, text='Remove Encryption from Kindle for Mac Mobi eBook')
        self.status.pack(fill=Tkconstants.X, expand=1)
        body = Tkinter.Frame(self)
        body.pack(fill=Tkconstants.X, expand=1)
        sticky = Tkconstants.E + Tkconstants.W
        body.grid_columnconfigure(1, weight=2)

        Tkinter.Label(body, text='Locate your Kindle Applications').grid(row=0, sticky=Tkconstants.E)
        self.k4mpath = Tkinter.Entry(body, width=50)
        self.k4mpath.grid(row=0, column=1, sticky=sticky)
        self.appname = '/Applications/Kindle for Mac.app'
        if not os.path.exists(self.appname):
            self.appname = '/Applications/Kindle.app'
        cwd = self.appname
        cwd = cwd.encode('utf-8')
        self.k4mpath.insert(0, cwd)
        button = Tkinter.Button(body, text="...", command=self.get_k4mpath)
        button.grid(row=0, column=2)

        Tkinter.Label(body, text='Directory for Unencrypted Output File').grid(row=1, sticky=Tkconstants.E)
        self.outpath = Tkinter.Entry(body, width=50)
        self.outpath.grid(row=1, column=1, sticky=sticky)
        desktoppath = os.getenv('HOME') + '/Desktop/'
        desktoppath = desktoppath.encode('utf-8')
        self.outpath.insert(0, desktoppath)
        button = Tkinter.Button(body, text="...", command=self.get_outpath)
        button.grid(row=1, column=2)

        msg1 = 'Conversion Log \n\n'
        self.stext = ScrolledText(body, bd=5, relief=Tkconstants.RIDGE, height=15, width=60, wrap=Tkconstants.WORD)
        self.stext.grid(row=3, column=0, columnspan=2,sticky=sticky)
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
            if poll != 0:
                msg = text + '\n\n' + 'Error: Encryption Removal Failed\n'
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
            msg = msg.encode('utf-8')
            self.stext.insert(Tkconstants.END,msg)
            self.stext.yview_pickplace(Tkconstants.END)
        return

    # run as a subprocess via pipes and collect stdout
    def mobirdr(self, infile, outfile, pidnum):
        cmdline = 'python ./lib/mobidedrm.py "' + infile + '" "' + outfile + '" "' + pidnum + '"'
        cmdline = cmdline.encode(sys.getfilesystemencoding())
        p2 = Process(cmdline, shell=True, bufsize=1, stdin=None, stdout=PIPE, stderr=PIPE, close_fds=False)
        return p2

    def get_k4mpath(self):
        k4mpath = tkFileDialog.askopenfilename(
            parent=None, title='Select Your Kindle Application',
            defaultextension='.app', filetypes=[('Kindle for Mac Application', '.app')])

        if k4mpath:
            k4mpath = os.path.normpath(k4mpath)
            self.k4mpath.delete(0, Tkconstants.END)
            self.k4mpath.insert(0, k4mpath)
        return

    def get_outpath(self):
        cwd = os.getcwdu()
        cwd = cwd.encode('utf-8')
        outpath = tkFileDialog.askdirectory(
            parent=None, title='Directory to Put Non-DRM eBook into',
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

    # run as a gdb subprocess via pipes and collect stdout
    def gdbrdr(self, k4mappfile, gdbcmds):
        cmdline = '/usr/bin/gdb -q -silent -readnow -batch -x ' +  gdbcmds + ' "' + k4mappfile + '"'
        cmdline = cmdline.encode(sys.getfilesystemencoding())
        p3 = Process(cmdline, shell=True, bufsize=1, stdin=None, stdout=PIPE, stderr=PIPE, close_fds=False)
        poll = p3.wait('wait')
        results = p3.read()
        pidnum = 'NOTAPID+'
        topazbook = 0
        bookpath = 'book not found'
        # parse the gdb results to get the last pid and the last azw/prc file name in the gdb listing
        reslst = results.split('\n')
        cnt = len(reslst)
        for j in xrange(cnt):
            resline = reslst[j]
            pp = resline.find('PID is ')
            if pp == 0:
                pidnum = resline[7:]
                topazbook = 0
            if pp > 0:
                pidnum = resline[13:]
                topazbook = 1
            fp = resline.find('File is ')
            if fp >= 0:
                tp1 = resline.find('.azw')
                tp2 = resline.find('.prc')
                tp3 = resline.find('.mbp')
                if tp1 >= 0 or tp2 >= 0:
                    bookpath = resline[8:]
                if tp3 >= 0 and topazbook == 1:
                    bookpath = resline[8:-3]
                    bookpath += 'azw'
        # put code here to get pid and file name
        return pidnum, bookpath, topazbook

    # convert from 8 digit PID to proper 10 digit PID
    def checksumPid(self, s):
        letters = "ABCDEFGHIJKLMNPQRSTUVWXYZ123456789"
        crc = (~binascii.crc32(s,-1))&0xFFFFFFFF
        crc = crc ^ (crc >> 16)
        res = s
        l = len(letters)
        for i in (0,1):
            b = crc & 0xff
            pos = (b // l) ^ (b % l)
            res += letters[pos%l]
            crc >>= 8
        return res

    # start the process
    def convertit(self):
        # dictionary of all known Kindle for Mac Binaries
        sha1_app_digests = {
            'e197ed2171ceb44a35c24bd30263b7253331694f' : 'gdb_kindle_cmds_r1.txt',
            '4f702436171f84acc13bdf9f94fae91525aecef5' : 'gdb_kindle_cmds_r2.txt',
            '4981b7eb37ccf0b8f63f56e8024b5ab593e8a97c' : 'gdb_kindle_cmds_r3.txt',
            '82909f0545688f09343e2c8fd8521eeee37d2de6' : 'gdb_kindle_cmds_r4.txt',
            'e260e3515cd525cd085c70baa6e42e08079edbcd' : 'gdb_kindle_cmds_r4.txt',
            'no_sha1_digest_key_here_________________' : 'no_gdb_kindle_cmds.txt',
        }
        # now disable the button to prevent multiple launches
        self.sbotton.configure(state='disabled')

        k4mpath = self.k4mpath.get()
        outpath = self.outpath.get()

        # basic error checking
        if not k4mpath or not os.path.exists(k4mpath):
            self.status['text'] = 'Error: Specified Kindle for Mac Application does not exist'
            self.sbotton.configure(state='normal')
            return
        if not outpath:
            self.status['text'] = 'Error: No output directory specified'
            self.sbotton.configure(state='normal')
            return
        if not os.path.isdir(outpath):
            self.status['text'] = 'Error specified outputdirectory does not exist'
            self.sbotton.configure(state='normal')
            return
        if not os.path.isfile('/usr/bin/gdb'):
            self.status['text'] = 'Error: gdb does not exist, install the XCode Develoepr Tools'
            self.sbotton.configure(state='normal')
            return


        # now check if the K4M app binary is known and if so which gdbcmds to use
        binary_app_file = k4mpath + '/Contents/MacOS/Kindle for Mac'
        if not os.path.exists(binary_app_file):
            binary_app_file = k4mpath + '/Contents/MacOS/Kindle'

        k4mpath = binary_app_file

        digest = SHA1(file(binary_app_file, 'rb').read())

        # print digest
        gdbcmds = None
        if digest in sha1_app_digests:
            gdbcmds = sha1_app_digests[digest]
        else :
            self.status['text'] = 'Error: Kindle Application does not match any known version, sha1sum is ' + digest
            self.sbotton.configure(state='normal')
            return

        # run Kindle for Mac in gdb to get what we need
        (pidnum, bookpath, topazbook) = self.gdbrdr(k4mpath, gdbcmds)

        if topazbook == 1:
            log = 'Warning: ' + bookpath + ' is a Topaz book\n'
            log += '\n\n'
            log += 'To convert this book please use the Topaz Tools\n'
            log += 'With the 8 digit PID: "' + pidnum + '"\n'
            log += '\n\n'
            log = log.encode('utf-8')
            self.stext.insert(Tkconstants.END,log)
            self.sbotton.configure(state='normal')
            return

        pidnum = self.checksumPid(pidnum)

        # default output file name to be input file name + '_nodrm.mobi'
        initname = os.path.splitext(os.path.basename(bookpath))[0]
        initname += '_nodrm.mobi' 
        outpath += '/' + initname

        log = 'Command = "python mobidedrm.py"\n'
        log += 'Mobi Path = "'+ bookpath + '"\n'
        log += 'Output file = "' + outpath + '"\n'
        log += 'PID = "' + pidnum + '"\n'
        log += '\n\n'
        log += 'Please Wait ...\n\n'
        log = log.encode('utf-8')
        self.stext.insert(Tkconstants.END,log)
        self.p2 = self.mobirdr(bookpath, outpath, pidnum)

        # python does not seem to allow you to create
        # your own eventloop which every other gui does - strange 
        # so need to use the widget "after" command to force
        # event loop to run non-gui events every interval
        self.stext.after(self.interval,self.processPipe)
        return


def main(argv=None):
    root = Tkinter.Tk()
    root.title('Kindle for Mac eBook Encryption Removal')
    root.resizable(True, False)
    root.minsize(300, 0)
    MainDialog(root).pack(fill=Tkconstants.X, expand=1)
    root.mainloop()
    return 0
    

if __name__ == "__main__":
    sys.exit(main())
