#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__license__ = 'GPL v3'

# Standard Python modules.
import os, sys, re, hashlib, traceback
from calibre_plugins.dedrm.__init__ import PLUGIN_NAME, PLUGIN_VERSION

def WineGetKeys(scriptpath, extension, wineprefix=""):
    import subprocess
    from subprocess import Popen, PIPE, STDOUT

    from . import subasyncio
    from .subasyncio import Process

    if extension == ".k4i":
        import json

    basepath, script = os.path.split(scriptpath)
    print("{0} v{1}: Running {2} under Wine".format(PLUGIN_NAME, PLUGIN_VERSION, script))

    outdirpath = os.path.join(basepath, "winekeysdir")
    if not os.path.exists(outdirpath):
        os.makedirs(outdirpath)

    if wineprefix != "":
        wineprefix = os.path.abspath(os.path.expanduser(os.path.expandvars(wineprefix)))

    if wineprefix != "" and os.path.exists(wineprefix):
         cmdline = "WINEPREFIX=\"{2}\" wine python.exe \"{0}\" \"{1}\"".format(scriptpath,outdirpath,wineprefix)
    else:
        cmdline = "wine python.exe \"{0}\" \"{1}\"".format(scriptpath,outdirpath)
    print("{0} v{1}: Command line: '{2}'".format(PLUGIN_NAME, PLUGIN_VERSION, cmdline))

    try:
        cmdline = cmdline.encode(sys.getfilesystemencoding())
        p2 = Process(cmdline, shell=True, bufsize=1, stdin=None, stdout=sys.stdout, stderr=STDOUT, close_fds=False)
        result = p2.wait("wait")
    except Exception as e:
        print("{0} v{1}: Wine subprocess call error: {2}".format(PLUGIN_NAME, PLUGIN_VERSION, e.args[0]))
        if wineprefix != "" and os.path.exists(wineprefix):
            cmdline = "WINEPREFIX=\"{2}\" wine C:\\Python27\\python.exe \"{0}\" \"{1}\"".format(scriptpath,outdirpath,wineprefix)
        else:
           cmdline = "wine C:\\Python27\\python.exe \"{0}\" \"{1}\"".format(scriptpath,outdirpath)
        print("{0} v{1}: Command line: “{2}”".format(PLUGIN_NAME, PLUGIN_VERSION, cmdline))

        try:
           cmdline = cmdline.encode(sys.getfilesystemencoding())
           p2 = Process(cmdline, shell=True, bufsize=1, stdin=None, stdout=sys.stdout, stderr=STDOUT, close_fds=False)
           result = p2.wait("wait")
        except Exception as e:
           print("{0} v{1}: Wine subprocess call error: {2}".format(PLUGIN_NAME, PLUGIN_VERSION, e.args[0]))

    # try finding winekeys anyway, even if above code errored
    winekeys = []
    # get any files with extension in the output dir
    files = [f for f in os.listdir(outdirpath) if f.endswith(extension)]
    for filename in files:
        try:
            fpath = os.path.join(outdirpath, filename)
            with open(fpath, 'rb') as keyfile:
                if extension == ".k4i":
                    new_key_value = json.loads(keyfile.read())
                else:
                    new_key_value = keyfile.read()
            winekeys.append(new_key_value)
        except:
            print("{0} v{1}: Error loading file {2}".format(PLUGIN_NAME, PLUGIN_VERSION, filename))
            traceback.print_exc()
        os.remove(fpath)
    print("{0} v{1}: Found and decrypted {2} {3}".format(PLUGIN_NAME, PLUGIN_VERSION, len(winekeys), "key file" if len(winekeys) == 1 else "key files"))
    return winekeys
