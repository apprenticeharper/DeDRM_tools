#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# CLI interface for the DeDRM plugin (useable without Calibre, too)
# DRM removal

from __future__ import absolute_import, print_function

# Copyright © 2021 NoDRM

"""

NOTE: This code is not functional (yet). I started working on it a while ago
to make a standalone version of the plugins that could work without Calibre, 
too, but for now there's only a rough code structure and no working code yet.

Currently, to use these plugins, you will need to use Calibre. Hopwfully that'll
change in the future. 

"""

#@@CALIBRE_COMPAT_CODE@@

import os, sys

from zipfile import ZipInfo, ZipFile, ZIP_STORED, ZIP_DEFLATED
from contextlib import closing

from standalone.__init__ import print_opt, print_std_usage

iswindows = sys.platform.startswith('win')
isosx = sys.platform.startswith('darwin')

def print_removedrm_help():
    from __init__ import PLUGIN_NAME, PLUGIN_VERSION
    print(PLUGIN_NAME + " v" + PLUGIN_VERSION + " - Calibre DRM removal plugin by noDRM")
    print()
    print("remove_drm: Remove DRM from one or multiple files")
    print()
    print_std_usage("remove_drm", "<filename> ... [ -o <filename> ] [ -f ]")
    
    print()
    print("Options: ")
    print_opt(None, "outputdir", "Folder to export the file(s) to")
    print_opt("o", "output", "File name to export the file to")
    print_opt("f", "force", "Overwrite output file if it already exists")
    print_opt(None, "overwrite", "Replace DRMed file with DRM-free file (implies --force)")


def determine_file_type(file):
    # Returns a file type:
    # "PDF", "PDB", "MOBI", "TPZ", "LCP", "ADEPT", "ADEPT-PassHash", "KFX-ZIP", "ZIP" or None

    f = open(file, "rb")
    fdata = f.read(100)
    f.close()

    if fdata.startswith(b"PK\x03\x04"):
        pass
        # Either LCP, Adobe, or Amazon
    elif fdata.startswith(b"%PDF"):
        return "PDF"
    elif fdata[0x3c:0x3c+8] == b"PNRdPPrs" or fdata[0x3c:0x3c+8] == b"PDctPPrs":
        return "PDB"
    elif fdata[0x3c:0x3c+8] == b"BOOKMOBI" or fdata[0x3c:0x3c+8] == b"TEXtREAd":
        return "MOBI"
    elif fdata.startswith(b"TPZ"):
        return "TPZ"
    else: 
        return None
        # Unknown file type

    
    # If it's a ZIP, determine the type. 

    from lcpdedrm import isLCPbook
    if isLCPbook(file):
        return "LCP"

    from ineptepub import adeptBook, isPassHashBook
    if adeptBook(file):
        if isPassHashBook(file):
            return "ADEPT-PassHash"
        else:
            return "ADEPT"

    try: 
        # Amazon / KFX-ZIP has a file that starts with b'\xeaDRMION\xee' in the ZIP.
        with closing(ZipFile(open(file, "rb"))) as book:
            for subfilename in book.namelist():
                with book.open(subfilename) as subfile:
                    data = subfile.read(8)
                    if data == b'\xeaDRMION\xee':
                        return "KFX-ZIP"
    except:
        pass

    return "ZIP"

     


def dedrm_single_file(input_file, output_file):
    # When this runs, all the stupid file handling is done. 
    # Just take the file at the absolute path "input_file"
    # and export it, DRM-free, to "output_file". 

    # Use a temp file as input_file and output_file
    # might be identical.

    # The output directory might not exist yet.

    print("File " + input_file + " to " + output_file)

    # Okay, first check the file type and don't rely on the extension. 
    try: 
        ftype = determine_file_type(input_file)
    except: 
        print("Can't determine file type for this file.")
        ftype = None
    
    if ftype is None: 
        return

    
    
    

def perform_action(params, files):
    output = None
    outputdir = None
    force = False
    overwrite_original = False


    if len(files) == 0:
        print_removedrm_help()
        return 0

    while len(params) > 0:
        p = params.pop(0)
        if p == "--output":
            output = params.pop(0)
        elif p == "--outputdir":
            outputdir = params.pop(0)
        elif p == "--force":
            force = True
        elif p == "--overwrite":
            overwrite_original = True
            force = True
        elif p == "--help":
            print_removedrm_help()
            return 0

    if overwrite_original and (output is not None or outputdir is not None):
        print("Can't use --overwrite together with --output or --outputdir.", file=sys.stderr)
        return 1

    if output is not None and os.path.isfile(output) and not force:
        print("Output file already exists. Use --force to overwrite.", file=sys.stderr)
        return 1


    if output is not None and len(files) > 1:
        print("Cannot set output file name if there's multiple input files.", file=sys.stderr)
        return 1
    
    if outputdir is not None and output is not None and os.path.isabs(output): 
        print("--output parameter is absolute path despite --outputdir being set.", file=sys.stderr)
        print("Remove --outputdir, or give a relative path to --output.", file=sys.stderr)
        return 1



    for file in files:

        file = os.path.abspath(file)

        if not os.path.isfile(file):
            print("Skipping file " + file + " - not found.", file=sys.stderr)
            continue

        if overwrite_original:
            output_filename = file
        else:
            if output is not None:
                # Due to the check above, we DO only have one file here.
                if outputdir is not None and not os.path.isabs(output):
                    output_filename = os.path.join(outputdir, output)
                else:    
                    output_filename = os.path.abspath(output)
            else:
                if outputdir is None:
                    outputdir = os.getcwd()
                output_filename = os.path.join(outputdir, os.path.basename(file))
                output_filename = os.path.abspath(output_filename)

                if output_filename == file:
                    # If we export to the import folder, add a suffix to the file name.
                    fn, f_ext = os.path.splitext(output_filename)
                    output_filename = fn + "_nodrm" + f_ext


        
        if os.path.isfile(output_filename) and not force:
            print("Skipping file " + file + " because output file already exists (use --force).", file=sys.stderr)
            continue

        

        dedrm_single_file(file, output_filename)

       


    return 0
    

if __name__ == "__main__":
    print("This code is not intended to be executed directly!", file=sys.stderr)