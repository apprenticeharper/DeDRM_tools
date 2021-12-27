#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# epubwatermark.py
# Copyright © 2021 NoDRM

# Revision history:
#  1.0   - Initial version

# Released under the terms of the GNU General Public Licence, version 3
# <http://www.gnu.org/licenses/>

"""
Removes various watermarks from EPUB files
"""

import traceback
from zipfile import ZipInfo, ZipFile, ZIP_STORED, ZIP_DEFLATED
from contextlib import closing
from lxml import etree
import re

# Runs a RegEx over all HTML/XHTML files to remove watermakrs.
def removeHTMLwatermarks(object, path_to_ebook):
    try: 
        inf = ZipFile(open(path_to_ebook, 'rb'))
        namelist = inf.namelist()

        modded_names = []
        modded_contents = []

        count_adept = 0
        count_pocketbook = 0
        count_lemonink_invisible = 0
        count_lemonink_visible = 0
        lemonink_trackingID = None

        for file in namelist:
            if not (file.endswith('.html') or file.endswith('.xhtml') or file.endswith('.xml')):
                continue

            try:
                file_str = inf.read(file).decode("utf-8")
                str_new = file_str

                # Remove Adobe ADEPT watermarks
                # Match optional newline at the beginning, then a "meta" tag with name = "Adept.expected.resource" or "Adept.resource"
                # and either a "value" or a "content" element with an Adobe UUID
                pre_remove = str_new
                str_new = re.sub(r'((\r\n|\r|\n)\s*)?\<meta\s+name=\"(Adept\.resource|Adept\.expected\.resource)\"\s+(content|value)=\"urn:uuid:[0-9a-fA-F\-]+\"\s*\/>', '', str_new)
                str_new = re.sub(r'((\r\n|\r|\n)\s*)?\<meta\s+(content|value)=\"urn:uuid:[0-9a-fA-F\-]+\"\s+name=\"(Adept\.resource|Adept\.expected\.resource)\"\s*\/>', '', str_new)

                if (str_new != pre_remove):
                    count_adept += 1

                # Remove Pocketbook watermarks
                pre_remove = str_new
                str_new = re.sub(r'\<div style\=\"padding\:0\;border\:0\;text\-indent\:0\;line\-height\:normal\;margin\:0 1cm 0.5cm 1cm\;[^\"]*opacity:0.0\;[^\"]*text\-decoration\:none\;[^\"]*background\:none\;[^\"]*\"\>(.*?)\<\/div\>', '', str_new)

                if (str_new != pre_remove):
                    count_pocketbook += 1


                # Remove eLibri / LemonInk watermark
                # Run this in a loop, as it is possible a file has been watermarked twice ...
                while True: 
                    pre_remove = str_new
                    unique_id = re.search(r'<body[^>]+class="[^"]*(t0x[0-9a-fA-F]{25})[^"]*"[^>]*>', str_new)
                    if (unique_id):
                        lemonink_trackingID = unique_id.groups()[0]
                        count_lemonink_invisible += 1
                        str_new = re.sub(lemonink_trackingID, '', str_new)
                        pre_remove = str_new
                        pm = r'(<body[^>]+class="[^"]*"[^>]*>)'
                        pm += r'\<div style\=\'padding\:0\;border\:0\;text\-indent\:0\;line\-height\:normal\;margin\:0 1cm 0.5cm 1cm\;[^\']*text\-decoration\:none\;[^\']*background\:none\;[^\']*\'\>(.*?)</div>'
                        pm += r'\<div style\=\'padding\:0\;border\:0\;text\-indent\:0\;line\-height\:normal\;margin\:0 1cm 0.5cm 1cm\;[^\']*text\-decoration\:none\;[^\']*background\:none\;[^\']*\'\>(.*?)</div>'
                        str_new = re.sub(pm, r'\1', str_new)

                        if (str_new != pre_remove):
                            count_lemonink_visible += 1
                    else: 
                        break

            except:
                traceback.print_exc()
                continue

            if (file_str == str_new):
                continue

            modded_names.append(file)
            modded_contents.append(str_new)

        
        if len(modded_names) == 0:
            # No file modified, return original
            return path_to_ebook

        if len(modded_names) != len(modded_contents):
            # Something went terribly wrong, return original
            print("Watermark: Error during watermark removal")
            return path_to_ebook

        # Re-package with modified files:
        namelist.remove("mimetype")

        try: 
            output = object.temporary_file(".epub").name
            kwds = dict(compression=ZIP_DEFLATED, allowZip64=False)
            with closing(ZipFile(open(output, 'wb'), 'w', **kwds)) as outf:
                for path in (["mimetype"] + namelist):

                    data = inf.read(path)
                    
                    try: 
                        modded_index = None
                        modded_index = modded_names.index(path)
                    except:
                        pass

                    if modded_index is not None:
                        # Found modified file - replace contents
                        data = modded_contents[modded_index]

                    zi = ZipInfo(path)
                    oldzi = inf.getinfo(path)
                    try: 
                        zi.compress_type = oldzi.compress_type
                        if path == "mimetype":
                            zi.compress_type = ZIP_STORED
                        zi.date_time = oldzi.date_time
                        zi.comment = oldzi.comment
                        zi.extra = oldzi.extra
                        zi.internal_attr = oldzi.internal_attr
                        zi.external_attr = oldzi.external_attr
                        zi.create_system = oldzi.create_system
                        if any(ord(c) >= 128 for c in path) or any(ord(c) >= 128 for c in zi.comment):
                            # If the file name or the comment contains any non-ASCII char, set the UTF8-flag
                            zi.flag_bits |= 0x800
                    except:
                        pass

                    outf.writestr(zi, data)
        except:
            traceback.print_exc()
            return path_to_ebook

        if (count_adept > 0):
            print("Watermark: Successfully stripped {0} ADEPT watermark(s) from ebook.".format(count_adept))
        
        if (count_lemonink_invisible > 0 or count_lemonink_visible > 0):
            print("Watermark: Successfully stripped {0} visible and {1} invisible LemonInk watermark(s) (\"{2}\") from ebook."
                .format(count_lemonink_visible, count_lemonink_invisible, lemonink_trackingID))
            
        if (count_pocketbook > 0):
            print("Watermark: Successfully stripped {0} Pocketbook watermark(s) from ebook.".format(count_pocketbook))

        return output

    except:
        traceback.print_exc()
        return path_to_ebook
        



# Finds the main OPF file, then uses RegEx to remove watermarks
def removeOPFwatermarks(object, path_to_ebook):
    contNS = lambda tag: '{%s}%s' % ('urn:oasis:names:tc:opendocument:xmlns:container', tag)
    opf_path = None

    try:
        inf = ZipFile(open(path_to_ebook, 'rb'))
        container = etree.fromstring(inf.read("META-INF/container.xml"))
        rootfiles = container.find(contNS("rootfiles")).findall(contNS("rootfile"))
        for rootfile in rootfiles: 
            opf_path = rootfile.get("full-path", None)
            if (opf_path is not None):
                break
    except: 
        traceback.print_exc()
        return path_to_ebook

    # If path is None, we didn't find an OPF, so we probably don't have a font key.
    # If path is set, it's the path to the main content OPF file.

    if (opf_path is None):
        # No OPF found - no watermark
        return path_to_ebook
    else:
        try:
            container_str = inf.read(opf_path).decode("utf-8")
            container_str_new = container_str

            had_amazon = False
            had_elibri = False

            # Remove Amazon hex watermarks
            # Match optional newline at the beginning, then spaces, then a "meta" tag with name = "Watermark" or "Watermark_(hex)" and a "content" element.
            # This regex also matches DuMont watermarks with meta name="watermark", with the case-insensitive match on the "w" in watermark.
            pre_remove = container_str_new
            container_str_new = re.sub(r'((\r\n|\r|\n)\s*)?\<meta\s+name=\"[Ww]atermark(_\(hex\))?\"\s+content=\"[0-9a-fA-F]+\"\s*\/>', '', container_str_new)
            container_str_new = re.sub(r'((\r\n|\r|\n)\s*)?\<meta\s+content=\"[0-9a-fA-F]+\"\s+name=\"[Ww]atermark(_\(hex\))?\"\s*\/>', '', container_str_new)
            if pre_remove != container_str_new:
                had_amazon = True

            # Remove elibri / lemonink watermark
            # Lemonink replaces all "id" fields in the opf with "idX_Y", with X being the watermark and Y being a number for that particular ID.
            # This regex replaces all "idX_Y" IDs with "id_Y", removing the watermark IDs.
            pre_remove = container_str_new
            container_str_new = re.sub(r'((\r\n|\r|\n)\s*)?\<\!\-\-\s*Wygenerowane przez elibri dla zamówienia numer [0-9a-fA-F]+\s*\-\-\>', '', container_str_new)
            if pre_remove != container_str_new:
                # To prevent this Regex from applying to books without that watermark, only do that if the watermark above was found.
                container_str_new = re.sub(r'\=\"id[0-9]+_([0-9]+)\"', r'="id_\1"', container_str_new)
            if pre_remove != container_str_new:
                had_elibri = True

        except:
            traceback.print_exc()
            return path_to_ebook

        if (container_str == container_str_new):
            # container didn't change - no watermark
            return path_to_ebook

        # Re-package without watermark
        namelist = inf.namelist()
        namelist.remove("mimetype")

        try: 
            output = object.temporary_file(".epub").name
            kwds = dict(compression=ZIP_DEFLATED, allowZip64=False)
            with closing(ZipFile(open(output, 'wb'), 'w', **kwds)) as outf:
                for path in (["mimetype"] + namelist):

                    data = inf.read(path)
                    if path == opf_path:
                        # Found OPF, replacing ...
                        data = container_str_new

                    zi = ZipInfo(path)
                    oldzi = inf.getinfo(path)
                    try: 
                        zi.compress_type = oldzi.compress_type
                        if path == "mimetype":
                            zi.compress_type = ZIP_STORED
                        zi.date_time = oldzi.date_time
                        zi.comment = oldzi.comment
                        zi.extra = oldzi.extra
                        zi.internal_attr = oldzi.internal_attr
                        zi.external_attr = oldzi.external_attr
                        zi.create_system = oldzi.create_system
                        if any(ord(c) >= 128 for c in path) or any(ord(c) >= 128 for c in zi.comment):
                            # If the file name or the comment contains any non-ASCII char, set the UTF8-flag
                            zi.flag_bits |= 0x800
                    except:
                        pass

                    outf.writestr(zi, data)
        except:
            traceback.print_exc()
            return path_to_ebook
        
        if had_elibri:
            print("Watermark: Successfully stripped eLibri watermark from OPF file.")
        if had_amazon:
            print("Watermark: Successfully stripped Amazon watermark from OPF file.")

        return output



def removeCDPwatermark(object, path_to_ebook):
    # "META-INF/cdp.info" is a watermark file used by some Tolino vendors. 
    # We don't want that in our eBooks, so lets remove that file.
    try: 
        infile = ZipFile(open(path_to_ebook, 'rb'))
        namelist = infile.namelist()
        if 'META-INF/cdp.info' not in namelist:
            return path_to_ebook

        namelist.remove("mimetype")
        namelist.remove("META-INF/cdp.info")

        output = object.temporary_file(".epub").name

        kwds = dict(compression=ZIP_DEFLATED, allowZip64=False)
        with closing(ZipFile(open(output, 'wb'), 'w', **kwds)) as outf:
            for path in (["mimetype"] + namelist):

                data = infile.read(path)
                
                zi = ZipInfo(path)
                oldzi = infile.getinfo(path)
                try: 
                    zi.compress_type = oldzi.compress_type
                    if path == "mimetype":
                        zi.compress_type = ZIP_STORED
                    zi.date_time = oldzi.date_time
                    zi.comment = oldzi.comment
                    zi.extra = oldzi.extra
                    zi.internal_attr = oldzi.internal_attr
                    zi.external_attr = oldzi.external_attr
                    zi.create_system = oldzi.create_system
                    if any(ord(c) >= 128 for c in path) or any(ord(c) >= 128 for c in zi.comment):
                        # If the file name or the comment contains any non-ASCII char, set the UTF8-flag
                        zi.flag_bits |= 0x800
                except:
                    pass

                outf.writestr(zi, data)
        
        print("Watermark: Successfully removed cdp.info watermark")
        return output

    except: 
        traceback.print_exc()
        return path_to_ebook