#!/usr/bin/env python

# This is a simple tool to identify all Amazon Topaz ebooks in a specific directory.
# There always seems to be confusion since Topaz books downloaded to K4PC/Mac can have
# almost any extension (.azw, .azw1, .prc, tpz). While the .azw1 and .tpz extensions
# are fairly easy to indentify, the others are not (without opening the files in an editor).

# To run the tool with the GUI frontend, just double-click on the 'FindTopazFiles.pyw' file
# and select the folder where all of the ebooks in question are located. Then click 'Search'.
# The program will list the file names of the ebooks that are indentified as being Topaz.
# You can then isolate those books and use the Topaz tools to decrypt and convert them.

# You can also run the script from a command line... supplying the folder to search
# as a parameter: python FindTopazEbooks.pyw "C:\My Folder" (change appropriately for
# your particular O.S.)

# ** NOTE: This program does NOT decrypt or modify Topaz files in any way. It simply identifies them.

# PLEASE DO NOT PIRATE EBOOKS!

# We want all authors and publishers, and eBook stores to live
# long and prosperous lives but at the same time  we just want to
# be able to read OUR books on whatever device we want and to keep
# readable for a long, long time

#  This borrows very heavily from works by CMBDTC, IHeartCabbages, skindle,
#    unswindle, DarkReverser, ApprenticeAlf, DiapDealer, some_updates
#    and many many others

# Revision history:
#   1 - Initial release.

from __future__ import with_statement

__license__ = 'GPL v3'

import sys
import os
os.environ['PYTHONIOENCODING'] = "utf-8"
import re
import shutil
import Tkinter
import Tkconstants
import tkFileDialog
import tkMessageBox


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


def cli_main(argv=sys.argv, obj=None):
    progname = os.path.basename(argv[0])
    if len(argv) != 2:
        print "usage: %s DIRECTORY" % (progname,)
        return 1

    if obj == None:
        print "\nTopaz search results:\n"
    else:
        obj.stext.insert(Tkconstants.END,"Topaz search results:\n\n")

    inpath = argv[1]
    files = os.listdir(inpath)
    filefilter = re.compile("(\.azw$)|(\.azw1$)|(\.prc$)|(\.tpz$)", re.IGNORECASE)
    files = filter(filefilter.search, files)

    if files:
        topazcount = 0
        totalcount = 0
        for filename in files:
            with open(os.path.join(inpath, filename), 'rb') as f:
                try:
                    if f.read().startswith('TPZ'):
                        f.close()
                        basename, extension = os.path.splitext(filename)
                        if obj == None:
                            print "   %s is a Topaz formatted ebook." % filename
                            """
                            if extension == '.azw' or extension == '.prc':
                                print "   renaming to %s" % (basename + '.tpz')
                                shutil.move(os.path.join(inpath, filename),
                                            os.path.join(inpath, basename + '.tpz'))
                            """
                        else:
                            msg1 = "   %s is a Topaz formatted ebook.\n" % filename
                            obj.stext.insert(Tkconstants.END,msg1)
                            """
                            if extension == '.azw' or extension == '.prc':
                                msg2 = "   renaming to %s\n" % (basename + '.tpz')
                                obj.stext.insert(Tkconstants.END,msg2)
                                shutil.move(os.path.join(inpath, filename),
                                            os.path.join(inpath, basename + '.tpz'))
                            """
                        topazcount += 1
                except:
                    if obj == None:
                        print "   Error reading %s." % filename
                    else:
                        msg = "   Error reading or %s.\n" % filename
                        obj.stext.insert(Tkconstants.END,msg)
                    pass
            totalcount += 1
        if topazcount == 0:
            if obj == None:
                print "\nNo Topaz books found in %s." % inpath
            else:
                msg = "\nNo Topaz books found in %s.\n\n" % inpath
                obj.stext.insert(Tkconstants.END,msg)
        else:
            if obj == None:
                print "\n%i Topaz books found in %s\n%i total books checked.\n" % (topazcount, inpath, totalcount)
            else:
                msg = "\n%i Topaz books found in %s\n%i total books checked.\n\n" %(topazcount, inpath, totalcount)
                obj.stext.insert(Tkconstants.END,msg)
    else:
        if obj == None:
            print "No typical Topaz file extensions found in %s.\n" % inpath
        else:
            msg = "No typical Topaz file extensions found in %s.\n\n" % inpath
            obj.stext.insert(Tkconstants.END,msg)

    return 0


class DecryptionDialog(Tkinter.Frame):
    def __init__(self, root):
        Tkinter.Frame.__init__(self, root, border=5)
        ltext='Search a directory for Topaz eBooks\n'
        self.status = Tkinter.Label(self, text=ltext)
        self.status.pack(fill=Tkconstants.X, expand=1)
        body = Tkinter.Frame(self)
        body.pack(fill=Tkconstants.X, expand=1)
        sticky = Tkconstants.E + Tkconstants.W
        body.grid_columnconfigure(1, weight=2)
        Tkinter.Label(body, text='Directory to Search').grid(row=1)
        self.inpath = Tkinter.Entry(body, width=30)
        self.inpath.grid(row=1, column=1, sticky=sticky)
        button = Tkinter.Button(body, text="...", command=self.get_inpath)
        button.grid(row=1, column=2)
        msg1 = 'Topaz search results \n\n'
        self.stext = ScrolledText(body, bd=5, relief=Tkconstants.RIDGE,
                                  height=15, width=60, wrap=Tkconstants.WORD)
        self.stext.grid(row=4, column=0, columnspan=2,sticky=sticky)
        #self.stext.insert(Tkconstants.END,msg1)
        buttons = Tkinter.Frame(self)
        buttons.pack()


        self.botton = Tkinter.Button(
            buttons, text="Search", width=10, command=self.search)
        self.botton.pack(side=Tkconstants.LEFT)
        Tkinter.Frame(buttons, width=10).pack(side=Tkconstants.LEFT)
        self.button = Tkinter.Button(
            buttons, text="Quit", width=10, command=self.quit)
        self.button.pack(side=Tkconstants.RIGHT)

    def get_inpath(self):
        cwd = os.getcwdu()
        cwd = cwd.encode('utf-8')
        inpath = tkFileDialog.askdirectory(
            parent=None, title='Directory to search',
            initialdir=cwd, initialfile=None)
        if inpath:
            inpath = os.path.normpath(inpath)
            self.inpath.delete(0, Tkconstants.END)
            self.inpath.insert(0, inpath)
        return


    def search(self):
        inpath = self.inpath.get()
        if not inpath or not os.path.exists(inpath):
            self.status['text'] = 'Specified directory does not exist'
            return
        argv = [sys.argv[0], inpath]
        self.status['text'] = 'Searching...'
        self.botton.configure(state='disabled')
        cli_main(argv, self)
        self.status['text'] = 'Search a directory for Topaz files'
        self.botton.configure(state='normal')

        return


def gui_main():
    root = Tkinter.Tk()
    root.title('Topaz eBook Finder')
    root.resizable(True, False)
    root.minsize(370, 0)
    DecryptionDialog(root).pack(fill=Tkconstants.X, expand=1)
    root.mainloop()
    return 0


if __name__ == '__main__':
    if len(sys.argv) > 1:
        sys.exit(cli_main())
    sys.exit(gui_main())
