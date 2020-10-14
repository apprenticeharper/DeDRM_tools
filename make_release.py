#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
A wrapper script to generate zip files for GitHub releases.

This script tends to be compatible with both Python 2 and Python 3.
'''

from __future__ import print_function

import os
import shutil


DEDRM_SRC_DIR = 'DeDRM_plugin'
DEDRM_README= 'DeDRM_plugin_ReadMe.txt'
OBOK_SRC_DIR = 'Obok_plugin'
OBOK_README = 'obok_plugin_ReadMe.txt'
RELEASE_DIR = 'release'


def make_release(version):
    try:
        shutil.rmtree(RELEASE_DIR)
    except:
        pass
    os.mkdir(RELEASE_DIR)
    shutil.make_archive(DEDRM_SRC_DIR, 'zip', DEDRM_SRC_DIR)
    shutil.make_archive(OBOK_SRC_DIR, 'zip', OBOK_SRC_DIR)
    shutil.move(DEDRM_SRC_DIR+'.zip', RELEASE_DIR)
    shutil.move(OBOK_SRC_DIR+'.zip', RELEASE_DIR)
    shutil.copy(DEDRM_README, RELEASE_DIR)
    shutil.copy(OBOK_README, RELEASE_DIR)
    shutil.copy("ReadMe_Overview.txt", RELEASE_DIR)

    release_name = 'DeDRM_tools_{}'.format(version)
    result = shutil.make_archive(release_name, 'zip', RELEASE_DIR)
    try:
        shutil.rmtree(RELEASE_DIR)
    except:
        pass
    return result


if __name__ == '__main__':
    import sys
    try:
        version = sys.argv[1]
    except IndexError:
        raise SystemExit('Usage: {} version'.format(__file__))

    print(make_release(version))
