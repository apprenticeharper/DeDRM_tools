#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# CLI interface for the DeDRM plugin (useable without Calibre, too)
# Adobe PassHash implementation

from __future__ import absolute_import, print_function

# Copyright © 2021 NoDRM

#@@CALIBRE_COMPAT_CODE@@

import os, sys

from standalone.__init__ import print_opt, print_std_usage

iswindows = sys.platform.startswith('win')
isosx = sys.platform.startswith('darwin')

def print_passhash_help():
    from __init__ import PLUGIN_NAME, PLUGIN_VERSION
    print(PLUGIN_NAME + " v" + PLUGIN_VERSION + " - Calibre DRM removal plugin by noDRM")
    print()
    print("passhash: Manage Adobe PassHashes")
    print()
    print_std_usage("passhash", "[ -u username -p password | -e ]")
    
    print()
    print("Options: ")
    print_opt("u", "username", "Generate a PassHash with the given username")
    print_opt("p", "password", "Generate a PassHash with the given username")
    print_opt("e", "extract", "Extract PassHashes found on this machine")

def perform_action(params, files):
    user = None
    pwd = None

    if len(params) == 0:
        print_passhash_help()
        return 0

    extract = False

    while len(params) > 0:
        p = params.pop(0)
        if p == "--username":
            user = params.pop(0)
        elif p == "--password":
            pwd = params.pop(0)
        elif p == "--extract":
            extract = True
        elif p == "--help":
            print_passhash_help()
            return 0

    if not extract:   
        if user is None: 
            print("Missing parameter: --username", file=sys.stderr)
        if pwd is None: 
            print("Missing parameter: --password", file=sys.stderr)
        if user is None or pwd is None: 
            return 1

    if user is not None and pwd is not None:
        from ignoblekeyGenPassHash import generate_key
        key = generate_key(user, pwd)
        print(key.decode("utf-8"))
    
    if extract:
        if not iswindows and not isosx:
            print("Extracting PassHash keys not supported on Linux.", file=sys.stderr)
            return 1
        
        keys = []

        from ignoblekeyNookStudy import nookkeys
        keys.extend(nookkeys())
        
        if iswindows:
            from ignoblekeyWindowsStore import dump_keys
            keys.extend(dump_keys())

            from adobekey_get_passhash import passhash_keys
            ade_keys, ade_names = passhash_keys()
            keys.extend(ade_keys)

        # Trim duplicates
        newkeys = []
        for k in keys:
            if not k in newkeys:
                newkeys.append(k)

        # Print all found keys
        for k in newkeys:
            print(k)


    return 0
    

if __name__ == "__main__":
    print("This code is not intended to be executed directly!")