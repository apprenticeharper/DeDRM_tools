#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# epubfontdecrypt.py
# Copyright © 2021 by noDRM

# Released under the terms of the GNU General Public Licence, version 3
# <http://www.gnu.org/licenses/>


# Revision history:
#   1 - Initial release

"""
Decrypts / deobfuscates font files in EPUB files
"""

from __future__ import print_function

__license__ = 'GPL v3'
__version__ = "1"

import os
import traceback
import zlib
import zipfile
from zipfile import ZipInfo, ZipFile, ZIP_STORED, ZIP_DEFLATED
from contextlib import closing
from lxml import etree
import itertools
import hashlib
import binascii


class Decryptor(object):
    def __init__(self, obfuscationkeyIETF, obfuscationkeyAdobe, encryption):
        enc = lambda tag: '{%s}%s' % ('http://www.w3.org/2001/04/xmlenc#', tag)
        dsig = lambda tag: '{%s}%s' % ('http://www.w3.org/2000/09/xmldsig#', tag)
        self.obfuscation_key_Adobe = obfuscationkeyAdobe
        self.obfuscation_key_IETF = obfuscationkeyIETF
        
        self._encryption = etree.fromstring(encryption)
        # This loops through all entries in the "encryption.xml" file
        # to figure out which files need to be decrypted.
        self._obfuscatedIETF = obfuscatedIETF = set()
        self._obfuscatedAdobe = obfuscatedAdobe = set()
        self._other = other = set()

        self._json_elements_to_remove = json_elements_to_remove = set()
        self._has_remaining_xml = False
        expr = './%s/%s/%s' % (enc('EncryptedData'), enc('CipherData'),
                               enc('CipherReference'))
        for elem in self._encryption.findall(expr):
            path = elem.get('URI', None)
            encryption_type_url = (elem.getparent().getparent().find("./%s" % (enc('EncryptionMethod'))).get('Algorithm', None))
            if path is not None:

                if encryption_type_url == "http://www.idpf.org/2008/embedding":
                    # Font files obfuscated with the IETF algorithm
                    path = path.encode('utf-8')
                    obfuscatedIETF.add(path)
                    if (self.obfuscation_key_IETF is None):
                        self._has_remaining_xml = True
                    else:
                        json_elements_to_remove.add(elem.getparent().getparent())

                elif encryption_type_url == "http://ns.adobe.com/pdf/enc#RC":
                    # Font files obfuscated with the Adobe algorithm.
                    path = path.encode('utf-8')
                    obfuscatedAdobe.add(path)
                    if (self.obfuscation_key_Adobe is None):
                        self._has_remaining_xml = True
                    else:
                        json_elements_to_remove.add(elem.getparent().getparent())

                else: 
                    path = path.encode('utf-8')
                    other.add(path)
                    self._has_remaining_xml = True
                    # Other unsupported type.
        
        for elem in json_elements_to_remove:
            elem.getparent().remove(elem)

    def check_if_remaining(self):
        return self._has_remaining_xml

    def get_xml(self):
        return "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" + etree.tostring(self._encryption, encoding="utf-8", pretty_print=True, xml_declaration=False).decode("utf-8")

    def decompress(self, bytes):
        dc = zlib.decompressobj(-15)
        try:
            decompressed_bytes = dc.decompress(bytes)
            ex = dc.decompress(b'Z') + dc.flush()
            if ex:
                decompressed_bytes = decompressed_bytes + ex
        except:
            # possibly not compressed by zip - just return bytes
            return bytes, False
        return decompressed_bytes , True
    
    def decrypt(self, path, data):
        if path.encode('utf-8') in self._obfuscatedIETF and self.obfuscation_key_IETF is not None:
            # de-obfuscate according to the IETF standard
            data, was_decomp = self.decompress(data)

            if len(data) <= 1040:
                # de-obfuscate whole file
                out = self.deobfuscate_single_data(self.obfuscation_key_IETF, data)
            else: 
                out = self.deobfuscate_single_data(self.obfuscation_key_IETF, data[:1040]) + data[1040:]

            if (not was_decomp):
                out, was_decomp = self.decompress(out)
            return out

        elif path.encode('utf-8') in self._obfuscatedAdobe and self.obfuscation_key_Adobe is not None:
            # de-obfuscate according to the Adobe standard
            data, was_decomp = self.decompress(data)

            if len(data) <= 1024:
                # de-obfuscate whole file
                out = self.deobfuscate_single_data(self.obfuscation_key_Adobe, data)
            else: 
                out = self.deobfuscate_single_data(self.obfuscation_key_Adobe, data[:1024]) + data[1024:]

            if (not was_decomp):
                out, was_decomp = self.decompress(out)
            return out

        else: 
            # Not encrypted or obfuscated
            return data

    def deobfuscate_single_data(self, key, data):
        try: 
            msg = bytes([c^k for c,k in zip(data, itertools.cycle(key))])
        except TypeError:
            # Python 2
            msg = ''.join(chr(ord(c)^ord(k)) for c,k in itertools.izip(data, itertools.cycle(key)))
        return msg



def decryptFontsBook(inpath, outpath):

    with closing(ZipFile(open(inpath, 'rb'))) as inf:
        namelist = inf.namelist()
        if 'META-INF/encryption.xml' not in namelist:
            return 1

        # Font key handling:

        font_master_key = None
        adobe_master_encryption_key = None

        contNS = lambda tag: '{%s}%s' % ('urn:oasis:names:tc:opendocument:xmlns:container', tag)
        path = None

        try:
            container = etree.fromstring(inf.read("META-INF/container.xml"))
            rootfiles = container.find(contNS("rootfiles")).findall(contNS("rootfile"))
            for rootfile in rootfiles: 
                path = rootfile.get("full-path", None)
                if (path is not None):
                    break
        except: 
            pass

        # If path is None, we didn't find an OPF, so we probably don't have a font key.
        # If path is set, it's the path to the main content OPF file.

        if (path is None):
            print("FontDecrypt: No OPF for font obfuscation found")
            return 1
        else:
            packageNS = lambda tag: '{%s}%s' % ('http://www.idpf.org/2007/opf', tag)
            metadataDCNS = lambda tag: '{%s}%s' % ('http://purl.org/dc/elements/1.1/', tag) 

            try:
                container = etree.fromstring(inf.read(path))
            except: 
                container = []

            ## IETF font key algorithm:
            print("FontDecrypt: Checking {0} for IETF font obfuscation keys ... ".format(path), end='')
            secret_key_name = None
            try:
                secret_key_name = container.get("unique-identifier")
            except: 
                pass

            try: 
                identify_element = container.find(packageNS("metadata")).find(metadataDCNS("identifier"))
                if (secret_key_name is None or secret_key_name == identify_element.get("id")):
                    font_master_key = identify_element.text
            except: 
                pass

            if (font_master_key is not None):
                if (secret_key_name is None):
                    print("found '%s'" % (font_master_key))
                else:
                    print("found '%s' (%s)" % (font_master_key, secret_key_name))

                # Trim / remove forbidden characters from the key, then hash it:
                font_master_key = font_master_key.replace(' ', '')
                font_master_key = font_master_key.replace('\t', '')
                font_master_key = font_master_key.replace('\r', '')
                font_master_key = font_master_key.replace('\n', '')
                font_master_key = font_master_key.encode('utf-8')
                font_master_key = hashlib.sha1(font_master_key).digest()
            else:
                print("not found")

            ## Adobe font key algorithm
            print("FontDecrypt: Checking {0} for Adobe font obfuscation keys ... ".format(path), end='')

            try: 
                metadata = container.find(packageNS("metadata"))
                identifiers = metadata.findall(metadataDCNS("identifier"))

                uid = None
                uidMalformed = False

                for identifier in identifiers: 
                    if identifier.get(packageNS("scheme")) == "UUID":
                        if identifier.text[:9] == "urn:uuid:":
                            uid = identifier.text[9:]
                        else: 
                            uid = identifier.text
                        break
                    if identifier.text[:9] == "urn:uuid:":
                        uid = identifier.text[9:]
                        break

                
                if uid is not None:
                    uid = uid.replace(chr(0x20),'').replace(chr(0x09),'')
                    uid = uid.replace(chr(0x0D),'').replace(chr(0x0A),'').replace('-','')

                    if len(uid) < 16:
                        uidMalformed = True
                    if not all(c in "0123456789abcdefABCDEF" for c in uid):
                        uidMalformed = True
                    
                    
                    if not uidMalformed:
                        print("found '{0}'".format(uid))
                        uid = uid + uid
                        adobe_master_encryption_key = binascii.unhexlify(uid[:32])
                
                if adobe_master_encryption_key is None:
                    print("not found")

            except:
                print("exception")
                pass

        # Begin decrypting.

        try:
            encryption = inf.read('META-INF/encryption.xml')
            decryptor = Decryptor(font_master_key, adobe_master_encryption_key, encryption)
            kwds = dict(compression=ZIP_DEFLATED, allowZip64=False)
            with closing(ZipFile(open(outpath, 'wb'), 'w', **kwds)) as outf:

                # Mimetype needs to be the first entry, so remove it from the list
                # whereever it is, then add it at the beginning. 
                namelist.remove("mimetype")

                for path in (["mimetype"] + namelist):
                    data = inf.read(path)
                    zi = ZipInfo(path)
                    zi.compress_type=ZIP_DEFLATED

                    if path == "mimetype":
                        # mimetype must not be compressed
                        zi.compress_type = ZIP_STORED
                    
                    elif path == "META-INF/encryption.xml":
                        # Check if there's still other entries not related to fonts
                        if (decryptor.check_if_remaining()):
                            data = decryptor.get_xml()
                            print("FontDecrypt: There's remaining entries in encryption.xml, adding file ...")
                        else: 
                            # No remaining entries, no need for that file.
                            continue

                    try:
                        # get the file info, including time-stamp
                        oldzi = inf.getinfo(path)
                        # copy across useful fields
                        zi.date_time = oldzi.date_time
                        zi.comment = oldzi.comment
                        zi.extra = oldzi.extra
                        zi.internal_attr = oldzi.internal_attr
                        # external attributes are dependent on the create system, so copy both.
                        zi.external_attr = oldzi.external_attr
                        zi.create_system = oldzi.create_system
                        if any(ord(c) >= 128 for c in path) or any(ord(c) >= 128 for c in zi.comment):
                            # If the file name or the comment contains any non-ASCII char, set the UTF8-flag
                            zi.flag_bits |= 0x800
                    except:
                        pass

                    if path == "mimetype":
                        outf.writestr(zi, inf.read('mimetype'))
                    elif path == "META-INF/encryption.xml":
                        outf.writestr(zi, data)
                    else: 
                        outf.writestr(zi, decryptor.decrypt(path, data))
        except:
            print("FontDecrypt: Could not decrypt fonts in {0:s} because of an exception:\n{1:s}".format(os.path.basename(inpath), traceback.format_exc()))
            traceback.print_exc()
            return 2
    return 0

