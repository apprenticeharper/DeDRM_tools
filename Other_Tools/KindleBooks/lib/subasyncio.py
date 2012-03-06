#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import os, sys
import signal
import threading
import subprocess
from subprocess import Popen, PIPE, STDOUT

# **heavily** chopped up and modfied version of asyncproc.py
# to make it actually work on Windows as well as Mac/Linux
# For the original see:
# "http://www.lysator.liu.se/~bellman/download/"
# author is  "Thomas Bellman <bellman@lysator.liu.se>"
# available under GPL version 3 or Later

# create an asynchronous subprocess whose output can be collected in
# a non-blocking manner

# What a mess!  Have to use threads just to get non-blocking io
# in a cross-platform manner

# luckily all thread use is hidden within this class

class Process(object):
    def __init__(self, *params, **kwparams):
        if len(params) <= 3:
            kwparams.setdefault('stdin', subprocess.PIPE)
        if len(params) <= 4:
            kwparams.setdefault('stdout', subprocess.PIPE)
        if len(params) <= 5:
            kwparams.setdefault('stderr', subprocess.PIPE)
        self.__pending_input = []
        self.__collected_outdata = []
        self.__collected_errdata = []
        self.__exitstatus = None
        self.__lock = threading.Lock()
        self.__inputsem = threading.Semaphore(0)
        self.__quit = False

        self.__process = subprocess.Popen(*params, **kwparams)

        if self.__process.stdin:
            self.__stdin_thread = threading.Thread(
                name="stdin-thread",
                target=self.__feeder, args=(self.__pending_input,
                                            self.__process.stdin))
            self.__stdin_thread.setDaemon(True)
            self.__stdin_thread.start()

        if self.__process.stdout:
            self.__stdout_thread = threading.Thread(
                name="stdout-thread",
                target=self.__reader, args=(self.__collected_outdata,
                                            self.__process.stdout))
            self.__stdout_thread.setDaemon(True)
            self.__stdout_thread.start()

        if self.__process.stderr:
            self.__stderr_thread = threading.Thread(
                name="stderr-thread",
                target=self.__reader, args=(self.__collected_errdata,
                                            self.__process.stderr))
            self.__stderr_thread.setDaemon(True)
            self.__stderr_thread.start()

    def pid(self):
        return self.__process.pid

    def kill(self, signal):
        self.__process.send_signal(signal)

    # check on subprocess (pass in 'nowait') to act like poll
    def wait(self, flag):
        if flag.lower() == 'nowait':
            rc = self.__process.poll()
        else:
            rc = self.__process.wait()
        if rc != None:
            if self.__process.stdin:
                self.closeinput()
            if self.__process.stdout:
                self.__stdout_thread.join()
            if self.__process.stderr:
                self.__stderr_thread.join()
        return self.__process.returncode

    def terminate(self):
        if self.__process.stdin:
            self.closeinput()
        self.__process.terminate()

    # thread gets data from subprocess stdout
    def __reader(self, collector, source):
        while True:
            data = os.read(source.fileno(), 65536)
            self.__lock.acquire()
            collector.append(data)
            self.__lock.release()
            if data == "":
                source.close()
                break
        return

    # thread feeds data to subprocess stdin
    def __feeder(self, pending, drain):
        while True:
            self.__inputsem.acquire()
            self.__lock.acquire()
            if not pending  and self.__quit:
                drain.close()
                self.__lock.release()
                break
            data = pending.pop(0)
            self.__lock.release()
            drain.write(data)

    # non-blocking read of data from subprocess stdout
    def read(self):
        self.__lock.acquire()
        outdata = "".join(self.__collected_outdata)
        del self.__collected_outdata[:]
        self.__lock.release()
        return outdata

    # non-blocking read of data from subprocess stderr
    def readerr(self):
        self.__lock.acquire()
        errdata = "".join(self.__collected_errdata)
        del self.__collected_errdata[:]
        self.__lock.release()
        return errdata

    # non-blocking write to stdin of subprocess
    def write(self, data):
        if self.__process.stdin is None:
            raise ValueError("Writing to process with stdin not a pipe")
        self.__lock.acquire()
        self.__pending_input.append(data)
        self.__inputsem.release()
        self.__lock.release()

    # close stdinput of subprocess
    def closeinput(self):
        self.__lock.acquire()
        self.__quit = True
        self.__inputsem.release()
        self.__lock.release()
