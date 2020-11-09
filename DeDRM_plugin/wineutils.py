#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__license__ = 'GPL v3'

# Standard Python modules.
import os, sys, re, hashlib, traceback
from calibre_plugins.dedrm.__init__ import PLUGIN_NAME, PLUGIN_VERSION


class NoWinePython3Exception(Exception):
    pass


class WinePythonCLI:
    py3_test = "import sys; sys.exit(0 if (sys.version_info.major==3) else 1)"
    def __init__(self, wineprefix=""):
        import subprocess

        if wineprefix != "":
            wineprefix = os.path.abspath(os.path.expanduser(os.path.expandvars(wineprefix)))

        if wineprefix != "" and os.path.exists(wineprefix):
            self.wineprefix = wineprefix
        else:
            self.wineprefix = None

        candidate_execs = [
            ["wine", "py.exe", "-3"],
            ["wine", "python3.exe"],
            ["wine", "python.exe"],
            ["wine", "C:\\Python27\\python.exe"], # Should likely be removed
        ]
        for e in candidate_execs:
            self.python_exec = e
            try:
                self.check_call(["-c", self.py3_test])
                print("{0} v{1}: Python3 exec found as {2}".format(
                    PLUGIN_NAME, PLUGIN_VERSION, " ".join(self.python_exec)
                ))
                return None
            except subprocess.CalledProcessError as e:
                if e.returncode == 1:
                    print("{0} v{1}: {2} is not python3".format(
                        PLUGIN_NAME, PLUGIN_VERSION, " ".join(self.python_exec)
                    ))
                elif e.returncode == 53:
                    print("{0} v{1}: {2} does not exist".format(
                        PLUGIN_NAME, PLUGIN_VERSION, " ".join(self.python_exec)
                    ))
        raise NoWinePython3Exception("Could not find python3 executable on specified wine prefix")


    def check_call(self, cli_args):
        import subprocess

        env_dict = os.environ
        env_dict["PYTHONPATH"] = ""
        if self.wineprefix is not None:
            env_dict["WINEPREFIX"] = self.wineprefix

        subprocess.check_call(self.python_exec + cli_args, env=env_dict,
                              stdin=None, stdout=sys.stdout,
                              stderr=subprocess.STDOUT, close_fds=False,
                              bufsize=1)


def WineGetKeys(scriptpath, extension, wineprefix=""):

    if extension == ".k4i":
        import json

    try:
        pyexec = WinePythonCLI(wineprefix)
    except NoWinePython3Exception:
        print('{0} v{1}: Unable to find python3 executable in WINEPREFIX="{2}"'.format(PLUGIN_NAME, PLUGIN_VERSION, wineprefix))
        return []

    basepath, script = os.path.split(scriptpath)
    print("{0} v{1}: Running {2} under Wine".format(PLUGIN_NAME, PLUGIN_VERSION, script))

    outdirpath = os.path.join(basepath, "winekeysdir")
    if not os.path.exists(outdirpath):
        os.makedirs(outdirpath)

    if wineprefix != "":
        wineprefix = os.path.abspath(os.path.expanduser(os.path.expandvars(wineprefix)))

    try:
        result = pyexec.check_call([scriptpath, outdirpath])
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
