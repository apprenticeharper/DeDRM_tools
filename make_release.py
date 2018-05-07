#!/usr/bin/env python
# code: utf-8

'''
A wrapper script to generate zip files for GitHub releases.

This script tends to be compatible with both Python 2 and Python 3.
'''

from __future__ import print_function

import os
import shutil


SRC_DIR = 'src'
CONTRIB_BASE = 'contrib'
BUILD_BASE = 'build'
DIST_BASE = 'dist'


def make_calibre_plugin():

    contrib_dir = os.path.join(CONTRIB_BASE, 'calibre')

    build_dir = os.path.join(BUILD_BASE, 'DeDRM_calibre_plugin')
    dist_name = os.path.join(DIST_BASE, 'DeDRM_calibre_plugin')
    core_dir = os.path.join(build_dir, 'DeDRM_plugin')
    plugin_name = os.path.join(build_dir, 'DeDRM_plugin')

    shutil.copytree(contrib_dir, build_dir)
    shutil.copytree(SRC_DIR, core_dir)

    shutil.make_archive(plugin_name, 'zip', core_dir)
    shutil.rmtree(core_dir)
    return shutil.make_archive(dist_name, 'zip', build_dir)


def make_windows_app():

    contrib_dir = os.path.join(CONTRIB_BASE, 'windows')

    build_dir = os.path.join(BUILD_BASE, 'DeDRM_Windows_Application')
    dist_name = os.path.join(DIST_BASE, 'DeDRM_Windows_Application')
    core_dir = os.path.join(build_dir, 'DeDRM_App', 'DeDRM_lib', 'lib')

    shutil.copytree(contrib_dir, build_dir)
    shutil.copytree(SRC_DIR, core_dir)

    return shutil.make_archive(dist_name, 'zip', build_dir)


def make_macos_app():

    contrib_dir = os.path.join(CONTRIB_BASE, 'macos')
    build_dir = os.path.join(BUILD_BASE, 'DeDRM_Macintosh_Application')
    dist_name = os.path.join(DIST_BASE, 'DeDRM_Macintosh_Application')
    core_dir = os.path.join(build_dir, 'DeDRM.app', 'Contents', 'Resources')

    shutil.copytree(contrib_dir, build_dir)

    _, dirs, files = next(os.walk(SRC_DIR))
    for name in dirs:
        shutil.copyfile(
            os.path.join(SRC_DIR, name),
            os.path.join(core_dir, name)
        )
    for name in files:
        shutil.copy2(
            os.path.join(SRC_DIR, name),
            os.path.join(core_dir, name)
        )

    return shutil.make_archive(dist_name, 'zip', build_dir)


def make_all():

    try:
        shutil.rmtree(BUILD_BASE)
    except OSError:
        pass

    print(make_calibre_plugin())
    print(make_windows_app())
    print(make_macos_app())


if __name__ == '__main__':
    make_all()
