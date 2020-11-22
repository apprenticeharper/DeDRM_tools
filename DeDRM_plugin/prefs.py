#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai

__license__ = 'GPL v3'

# Standard Python modules.
import os, sys, re, hashlib
import codecs, json
import traceback

from calibre.utils.config import dynamic, config_dir, JSONConfig
from calibre_plugins.dedrm.__init__ import PLUGIN_NAME, PLUGIN_VERSION
from calibre.constants import iswindows, isosx

class DeDRM_Prefs():
    def __init__(self):
        JSON_PATH = os.path.join("plugins", PLUGIN_NAME.strip().lower().replace(' ', '_') + '.json')
        self.dedrmprefs = JSONConfig(JSON_PATH)

        self.dedrmprefs.defaults['configured'] = False
        self.dedrmprefs.defaults['bandnkeys'] = {}
        self.dedrmprefs.defaults['adeptkeys'] = {}
        self.dedrmprefs.defaults['ereaderkeys'] = {}
        self.dedrmprefs.defaults['kindlekeys'] = {}
        self.dedrmprefs.defaults['androidkeys'] = {}
        self.dedrmprefs.defaults['pids'] = []
        self.dedrmprefs.defaults['serials'] = []
        self.dedrmprefs.defaults['adobewineprefix'] = ""
        self.dedrmprefs.defaults['kindlewineprefix'] = ""

        # initialise
        # we must actually set the prefs that are dictionaries and lists
        # to empty dictionaries and lists, otherwise we are unable to add to them
        # as then it just adds to the (memory only) dedrmprefs.defaults versions!
        if self.dedrmprefs['bandnkeys'] == {}:
            self.dedrmprefs['bandnkeys'] = {}
        if self.dedrmprefs['adeptkeys'] == {}:
            self.dedrmprefs['adeptkeys'] = {}
        if self.dedrmprefs['ereaderkeys'] == {}:
            self.dedrmprefs['ereaderkeys'] = {}
        if self.dedrmprefs['kindlekeys'] == {}:
            self.dedrmprefs['kindlekeys'] = {}
        if self.dedrmprefs['androidkeys'] == {}:
            self.dedrmprefs['androidkeys'] = {}
        if self.dedrmprefs['pids'] == []:
            self.dedrmprefs['pids'] = []
        if self.dedrmprefs['serials'] == []:
            self.dedrmprefs['serials'] = []

    def __getitem__(self,kind = None):
        if kind is not None:
            return self.dedrmprefs[kind]
        return self.dedrmprefs

    def set(self, kind, value):
        self.dedrmprefs[kind] = value

    def writeprefs(self,value = True):
        self.dedrmprefs['configured'] = value

    def addnamedvaluetoprefs(self, prefkind, keyname, keyvalue):
        try:
            if keyvalue not in self.dedrmprefs[prefkind].values():
                # ensure that the keyname is unique
                # by adding a number (starting with 2) to the name if it is not
                namecount = 1
                newname = keyname
                while newname in self.dedrmprefs[prefkind]:
                    namecount += 1
                    newname = "{0:s}_{1:d}".format(keyname,namecount)
                # add to the preferences
                self.dedrmprefs[prefkind][newname] = keyvalue
                return (True, newname)
        except:
            traceback.print_exc()
            pass
        return (False, keyname)

    def addvaluetoprefs(self, prefkind, prefsvalue):
        # ensure the keyvalue isn't already in the preferences
        try:
            if prefsvalue not in self.dedrmprefs[prefkind]:
                self.dedrmprefs[prefkind].append(prefsvalue)
                return True
        except:
            traceback.print_exc()
        return False


def convertprefs(always = False):

    def parseIgnobleString(keystuff):
        from calibre_plugins.dedrm.ignoblekeygen import generate_key
        userkeys = []
        ar = keystuff.split(':')
        for keystring in ar:
            try:
                name, ccn = keystring.split(',')
                # Generate Barnes & Noble EPUB user key from name and credit card number.
                keyname = "{0}_{1}".format(name.strip(),ccn.strip()[-4:])
                keyvalue = generate_key(name, ccn)
                userkeys.append([keyname,keyvalue])
            except Exception as e:
                traceback.print_exc()
                print(e.args[0])
                pass
        return userkeys

    def parseeReaderString(keystuff):
        from calibre_plugins.dedrm.erdr2pml import getuser_key
        userkeys = []
        ar = keystuff.split(':')
        for keystring in ar:
            try:
                name, cc = keystring.split(',')
                # Generate eReader user key from name and credit card number.
                keyname = "{0}_{1}".format(name.strip(),cc.strip()[-4:])
                keyvalue = codecs.encode(getuser_key(name,cc),'hex')
                userkeys.append([keyname,keyvalue])
            except Exception as e:
                traceback.print_exc()
                print(e.args[0])
                pass
        return userkeys

    def parseKindleString(keystuff):
        pids = []
        serials = []
        ar = keystuff.split(',')
        for keystring in ar:
            keystring = str(keystring).strip().replace(" ","")
            if len(keystring) == 10 or len(keystring) == 8 and keystring not in pids:
                pids.append(keystring)
            elif len(keystring) == 16 and keystring[0] == 'B' and keystring not in serials:
                serials.append(keystring)
        return (pids,serials)

    def getConfigFiles(extension, encoding = None):
        # get any files with extension 'extension' in the config dir
        userkeys = []
        files = [f for f in os.listdir(config_dir) if f.endswith(extension)]
        for filename in files:
            try:
                fpath = os.path.join(config_dir, filename)
                key = os.path.splitext(filename)[0]
                value = open(fpath, 'rb').read()
                if encoding is not None:
                    value = codecs.encode(value,encoding)
                userkeys.append([key,value])
            except:
                traceback.print_exc()
                pass
        return userkeys

    dedrmprefs = DeDRM_Prefs()

    if (not always) and dedrmprefs['configured']:
        # We've already converted old preferences,
        # and we're not being forced to do it again, so just return
        return


    print("{0} v{1}: Importing configuration data from old DeDRM plugins".format(PLUGIN_NAME, PLUGIN_VERSION))

    IGNOBLEPLUGINNAME = "Ignoble Epub DeDRM"
    EREADERPLUGINNAME = "eReader PDB 2 PML"
    OLDKINDLEPLUGINNAME = "K4PC, K4Mac, Kindle Mobi and Topaz DeDRM"

    # get prefs from older tools
    kindleprefs = JSONConfig(os.path.join("plugins", "K4MobiDeDRM"))
    ignobleprefs = JSONConfig(os.path.join("plugins", "ignoble_epub_dedrm"))

    # Handle the old ignoble plugin's customization string by converting the
    # old string to stored keys... get that personal data out of plain sight.
    from calibre.customize.ui import config
    sc = config['plugin_customization']
    val = sc.pop(IGNOBLEPLUGINNAME, None)
    if val is not None:
        print("{0} v{1}: Converting old Ignoble plugin configuration string.".format(PLUGIN_NAME, PLUGIN_VERSION))
        priorkeycount = len(dedrmprefs['bandnkeys'])
        userkeys = parseIgnobleString(str(val))
        for keypair in userkeys:
            name = keypair[0]
            value = keypair[1]
            dedrmprefs.addnamedvaluetoprefs('bandnkeys', name, value)
        addedkeycount = len(dedrmprefs['bandnkeys'])-priorkeycount
        print("{0} v{1}: {2:d} Barnes and Noble {3} imported from old Ignoble plugin configuration string".format(PLUGIN_NAME, PLUGIN_VERSION, addedkeycount, "key" if addedkeycount==1 else "keys"))
    # Make the json write all the prefs to disk
    dedrmprefs.writeprefs(False)

    # Handle the old eReader plugin's customization string by converting the
    # old string to stored keys... get that personal data out of plain sight.
    val = sc.pop(EREADERPLUGINNAME, None)
    if val is not None:
        print("{0} v{1}: Converting old eReader plugin configuration string.".format(PLUGIN_NAME, PLUGIN_VERSION))
        priorkeycount = len(dedrmprefs['ereaderkeys'])
        userkeys = parseeReaderString(str(val))
        for keypair in userkeys:
            name = keypair[0]
            value = keypair[1]
            dedrmprefs.addnamedvaluetoprefs('ereaderkeys', name, value)
        addedkeycount = len(dedrmprefs['ereaderkeys'])-priorkeycount
        print("{0} v{1}: {2:d} eReader {3} imported from old eReader plugin configuration string".format(PLUGIN_NAME, PLUGIN_VERSION, addedkeycount, "key" if addedkeycount==1 else "keys"))
    # Make the json write all the prefs to disk
    dedrmprefs.writeprefs(False)

    # get old Kindle plugin configuration string
    val = sc.pop(OLDKINDLEPLUGINNAME, None)
    if val is not None:
        print("{0} v{1}: Converting old Kindle plugin configuration string.".format(PLUGIN_NAME, PLUGIN_VERSION))
        priorpidcount = len(dedrmprefs['pids'])
        priorserialcount = len(dedrmprefs['serials'])
        pids, serials = parseKindleString(val)
        for pid in pids:
            dedrmprefs.addvaluetoprefs('pids',pid)
        for serial in serials:
            dedrmprefs.addvaluetoprefs('serials',serial)
        addedpidcount = len(dedrmprefs['pids']) - priorpidcount
        addedserialcount = len(dedrmprefs['serials']) - priorserialcount
        print("{0} v{1}: {2:d} {3} and {4:d} {5} imported from old Kindle plugin configuration string.".format(PLUGIN_NAME, PLUGIN_VERSION, addedpidcount, "PID" if addedpidcount==1 else "PIDs", addedserialcount, "serial number" if addedserialcount==1 else "serial numbers"))
    # Make the json write all the prefs to disk
    dedrmprefs.writeprefs(False)

    # copy the customisations back into calibre preferences, as we've now removed the nasty plaintext
    config['plugin_customization'] = sc

    # get any .b64 files in the config dir
    priorkeycount = len(dedrmprefs['bandnkeys'])
    bandnfilekeys = getConfigFiles('.b64')
    for keypair in bandnfilekeys:
        name = keypair[0]
        value = keypair[1]
        dedrmprefs.addnamedvaluetoprefs('bandnkeys', name, value)
    addedkeycount = len(dedrmprefs['bandnkeys'])-priorkeycount
    if addedkeycount > 0:
        print("{0} v{1}: {2:d} Barnes and Noble {3} imported from config folder.".format(PLUGIN_NAME, PLUGIN_VERSION, addedkeycount, "key file" if addedkeycount==1 else "key files"))
    # Make the json write all the prefs to disk
    dedrmprefs.writeprefs(False)

    # get any .der files in the config dir
    priorkeycount = len(dedrmprefs['adeptkeys'])
    adeptfilekeys = getConfigFiles('.der','hex')
    for keypair in adeptfilekeys:
        name = keypair[0]
        value = keypair[1]
        dedrmprefs.addnamedvaluetoprefs('adeptkeys', name, value)
    addedkeycount = len(dedrmprefs['adeptkeys'])-priorkeycount
    if addedkeycount > 0:
        print("{0} v{1}: {2:d} Adobe Adept {3} imported from config folder.".format(PLUGIN_NAME, PLUGIN_VERSION, addedkeycount, "keyfile" if addedkeycount==1 else "keyfiles"))
    # Make the json write all the prefs to disk
    dedrmprefs.writeprefs(False)

    # get ignoble json prefs
    if 'keys' in ignobleprefs:
        priorkeycount = len(dedrmprefs['bandnkeys'])
        for name in ignobleprefs['keys']:
            value = ignobleprefs['keys'][name]
            dedrmprefs.addnamedvaluetoprefs('bandnkeys', name, value)
        addedkeycount = len(dedrmprefs['bandnkeys']) - priorkeycount
        # no need to delete old prefs, since they contain no recoverable private data
        if addedkeycount > 0:
            print("{0} v{1}: {2:d} Barnes and Noble {3} imported from Ignoble plugin preferences.".format(PLUGIN_NAME, PLUGIN_VERSION, addedkeycount, "key" if addedkeycount==1 else "keys"))
    # Make the json write all the prefs to disk
    dedrmprefs.writeprefs(False)

    # get kindle json prefs
    priorpidcount = len(dedrmprefs['pids'])
    priorserialcount = len(dedrmprefs['serials'])
    if 'pids' in kindleprefs:
        pids, serials = parseKindleString(kindleprefs['pids'])
        for pid in pids:
            dedrmprefs.addvaluetoprefs('pids',pid)
    if 'serials' in kindleprefs:
        pids, serials = parseKindleString(kindleprefs['serials'])
        for serial in serials:
            dedrmprefs.addvaluetoprefs('serials',serial)
    addedpidcount = len(dedrmprefs['pids']) - priorpidcount
    if addedpidcount > 0:
        print("{0} v{1}: {2:d} {3} imported from Kindle plugin preferences".format(PLUGIN_NAME, PLUGIN_VERSION, addedpidcount, "PID" if addedpidcount==1 else "PIDs"))
    addedserialcount = len(dedrmprefs['serials']) - priorserialcount
    if addedserialcount > 0:
        print("{0} v{1}: {2:d} {3} imported from Kindle plugin preferences".format(PLUGIN_NAME, PLUGIN_VERSION, addedserialcount, "serial number" if addedserialcount==1 else "serial numbers"))
    try:
        if 'wineprefix' in kindleprefs and kindleprefs['wineprefix'] != "":
            dedrmprefs.set('adobewineprefix',kindleprefs['wineprefix'])
            dedrmprefs.set('kindlewineprefix',kindleprefs['wineprefix'])
            print("{0} v{1}: WINEPREFIX ‘(2)’ imported from Kindle plugin preferences".format(PLUGIN_NAME, PLUGIN_VERSION, kindleprefs['wineprefix']))
    except:
        traceback.print_exc()


    # Make the json write all the prefs to disk
    dedrmprefs.writeprefs()
    print("{0} v{1}: Finished setting up configuration data.".format(PLUGIN_NAME, PLUGIN_VERSION))
