#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# CLI interface for the DeDRM plugin (useable without Calibre, too)

from __future__ import absolute_import, print_function

# Copyright © 2021 NoDRM

"""

NOTE: This code is not functional (yet). I started working on it a while ago
to make a standalone version of the plugins that could work without Calibre, 
too, but for now there's only a rough code structure and no working code yet.

Currently, to use these plugins, you will need to use Calibre. Hopwfully that'll
change in the future. 

"""


OPT_SHORT_TO_LONG = [
    ["c", "config"],
    ["e", "extract"],
    ["f", "force"], 
    ["h", "help"], 
    ["i", "import"],
    ["o", "output"],
    ["p", "password"],
    ["q", "quiet"],
    ["t", "test"], 
    ["u", "username"],
    ["v", "verbose"],
]

#@@CALIBRE_COMPAT_CODE@@

import os, sys


global _additional_data
global _additional_params
global _function
_additional_data = []
_additional_params = []
_function = None

global config_file_path
config_file_path = "dedrm.json"

def print_fname(f, info):
    print("  " + f.ljust(15) + " " + info)

def print_opt(short, long, info):
    if short is None:
        short = "    "
    else: 
        short = "  -" + short
    
    if long is None: 
        long = "            "
    else:
        long = "--" + long.ljust(16)

    print(short + "  " + long + "  " + info, file=sys.stderr)

def print_std_usage(name, param_string):
    print("Usage: ", file=sys.stderr)
    if "calibre" in sys.modules:
        print("  calibre-debug -r \"DeDRM\" -- "+name+" " + param_string, file=sys.stderr)
    else:
        print("  python3 DeDRM_plugin.zip "+name+" "+param_string, file=sys.stderr)

def print_err_header():
    from __init__ import PLUGIN_NAME, PLUGIN_VERSION # type: ignore

    print(PLUGIN_NAME + " v" + PLUGIN_VERSION + " - DRM removal plugin by noDRM")
    print()

def print_help():
    from __version import PLUGIN_NAME, PLUGIN_VERSION
    print(PLUGIN_NAME + " v" + PLUGIN_VERSION + " - DRM removal plugin by noDRM")
    print("Based on DeDRM Calibre plugin by Apprentice Harper, Apprentice Alf and others.")
    print("See https://github.com/noDRM/DeDRM_tools for more information.")
    print()
    if "calibre" in sys.modules:
        print("This plugin can be run through Calibre - like you are doing right now - ")
        print("but it can also be executed with a standalone Python interpreter.")
    else:
        print("This plugin can either be imported into Calibre, or be executed directly")
        print("through Python like you are doing right now.")
    print()
    print("Available functions:")
    print_fname("passhash", "Manage Adobe PassHashes")
    print_fname("remove_drm", "Remove DRM from one or multiple books")
    print()
    
    # TODO: All parameters that are global should be listed here.

def print_credits():
    from __version import PLUGIN_NAME, PLUGIN_VERSION
    print(PLUGIN_NAME + " v" + PLUGIN_VERSION + " - Calibre DRM removal plugin by noDRM")
    print("Based on DeDRM Calibre plugin by Apprentice Harper, Apprentice Alf and others.")
    print("See https://github.com/noDRM/DeDRM_tools for more information.")
    print()
    print("Credits:")
    print(" - noDRM for the current release of the DeDRM plugin")
    print(" - Apprentice Alf and Apprentice Harper for the previous versions of the DeDRM plugin")
    print(" - The Dark Reverser for the Mobipocket and eReader script")
    print(" - i ♥ cabbages for the Adobe Digital Editions scripts")
    print(" - Skindle aka Bart Simpson for the Amazon Kindle for PC script")
    print(" - CMBDTC for Amazon Topaz DRM removal script")
    print(" - some_updates, clarknova and Bart Simpson for Amazon Topaz conversion scripts")
    print(" - DiapDealer for the first calibre plugin versions of the tools")
    print(" - some_updates, DiapDealer, Apprentice Alf and mdlnx for Amazon Kindle/Mobipocket tools")
    print(" - some_updates for the DeDRM all-in-one Python tool")
    print(" - Apprentice Alf for the DeDRM all-in-one AppleScript tool")


def handle_single_argument(arg, next):
    used_up = 0
    global _additional_params
    global config_file_path
    
    if arg in ["--username", "--password", "--output", "--outputdir"]: 
        used_up = 1
        _additional_params.append(arg)
        if next is None or len(next) == 0: 
            print_err_header()
            print("Missing parameter for argument " + arg, file=sys.stderr)
            sys.exit(1)
        else:
            _additional_params.append(next[0])
    
    elif arg == "--config":
        if next is None or len(next) == 0: 
            print_err_header()
            print("Missing parameter for argument " + arg, file=sys.stderr)
            sys.exit(1)

        config_file_path = next[0]
        used_up = 1

    elif arg in ["--help", "--credits", "--verbose", "--quiet", "--extract", "--import", "--overwrite", "--force"]:
        _additional_params.append(arg)

        
    else:
        print_err_header()
        print("Unknown argument: " + arg, file=sys.stderr)
        sys.exit(1)
    
    
    # Used up 0 additional arguments
    return used_up



def handle_data(data):
    global _function
    global _additional_data

    if _function is None: 
        _function = str(data)
    else:
        _additional_data.append(str(data))

def execute_action(action, filenames, params):
    print("Executing '{0}' on file(s) {1} with parameters {2}".format(action, str(filenames), str(params)), file=sys.stderr)

    if action == "help":
        print_help()
        sys.exit(0)
    
    elif action == "passhash": 
        from standalone.passhash import perform_action
        perform_action(params, filenames)

    elif action == "remove_drm":
        if not os.path.isfile(os.path.abspath(config_file_path)):
            print("Config file missing ...")
        
        from standalone.remove_drm import perform_action
        perform_action(params, filenames)
        
    elif action == "config":
        import prefs
        config = prefs.DeDRM_Prefs(os.path.abspath(config_file_path))
        print(config["adeptkeys"])
    
    else:
        print("Command '"+action+"' is unknown.", file=sys.stderr)


def main(argv):
    arguments = argv
    skip_opts = False

    # First element is always the ZIP name, remove that. 
    if not arguments[0].lower().endswith(".zip") and not "calibre" in sys.modules:
        print("Warning: File name does not end in .zip ...")
        print(arguments)
    arguments.pop(0)

    while len(arguments) > 0:
        arg = arguments.pop(0)

        if arg == "--":
            skip_opts = True
            continue

        if not skip_opts:
            if arg.startswith("--"):
                # Give the current arg, plus all remaining ones. 
                # Return the number of additional args we used.
                used = handle_single_argument(arg, arguments)
                for _ in range(used):
                    # Function returns number of additional arguments that were
                    # "used up" by that argument. 
                    # Remove that amount of arguments from the list.
                    try: 
                        arguments.pop(0)
                    except:
                        pass
                continue
            elif arg.startswith("-"):
                single_args = list(arg[1:])
                # single_args is now a list of single chars, for when you call the program like "ls -alR"
                # with multiple single-letter options combined.
                while len(single_args) > 0:
                    c = single_args.pop(0)
                
                    # See if we have a long name for that option.
                    for wrapper in OPT_SHORT_TO_LONG:
                        if wrapper[0] == c:
                            c = "--" + wrapper[1]
                            break
                    else: 
                        c = "-" + c
                    # c is now the long term (unless there is no long version, then it's the short version).

                    if len(single_args) > 0:
                        # If we have more short arguments, the argument for this one must be None.
                        handle_single_argument(c, None)
                        used = 0
                    else: 
                        # If not, then there might be parameters for this short argument.
                        used = handle_single_argument(c, arguments)

                    for _ in range(used):
                        # Function returns number of additional arguments that were
                        # "used up" by that argument. 
                        # Remove that amount of arguments from the list.
                        try: 
                            arguments.pop(0)
                        except: 
                            pass
                
                continue
        
        handle_data(arg)
        

    if _function is None and "--credits" in _additional_params:
        print_credits()
        sys.exit(0)

    if _function is None and "--help" in _additional_params:
        print_help()
        sys.exit(0)
    
    if _function is None:
        print_help()
        sys.exit(1)
    
    # Okay, now actually begin doing stuff.
    # This function gets told what to do and gets additional data (filenames).
    # It also receives additional parameters.
    # The rest of the code will be in different Python files.
    execute_action(_function.lower(), _additional_data, _additional_params)
        

    


if __name__ == "__main__":
    # NOTE: This MUST not do anything else other than calling main()
    # All the code must be in main(), not in here.
    import sys
    main(sys.argv)