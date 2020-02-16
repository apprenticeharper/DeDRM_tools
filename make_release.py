#!/usr/bin/env python
# code: utf-8

'''
A wrapper script to generate zip files for GitHub releases.

This script tends to be compatible with both Python 2 and Python 3.
'''

from __future__ import print_function

import os
import shutil


DEDRM_SRC_DIR = 'DeDRM_Plugin'
DEDRM_README= 'DeDRM_Plugin_ReadMe.txt'
OBOK_SRC_DIR = 'Obok_plugin'
OBOK_README = 'Obok_plugin_ReadMe.txt'
RELEASE_DIR = 'release'

def make_calibre_plugin():

    shutil.make_archive(core_dir, 'zip', core_dir)
    shutil.rmtree(core_dir)


def make_obok_plugin():
    obok_plugin_dir = os.path.join(SHELLS_BASE, 'Obok_calibre_plugin')
    core_dir = os.path.join(obok_plugin_dir, 'obok_plugin')

    shutil.copytree(OBOK_SRC_DIR, core_dir)
    shutil.make_archive(core_dir, 'zip')
    shutil.rmtree(core_dir)

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
