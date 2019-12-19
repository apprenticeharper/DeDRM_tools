#!/usr/bin/env python
# -*- coding: utf-8 -*-

import struct, locale, imghdr, os

#################################################################################
#                                                                               #
#                             MOBI HDImage Merger                               #
#                                                                               #
#                       2019 Choryu Park (Kyoungkyu Park)                       #
#                                                                               #
#################################################################################

# This source code is based on these documents, and source codes;
#   https://wiki.mobileread.com/wiki/MOBI
#   https://wiki.mobileread.com/wiki/PDB
#   https://www.mobileread.com/forums/showpost.php?p=3114050&postcount=1145
#
# Thanks to author of 'DumpAZW6'. It many helps to write this source code.

#################################################################################
# * Important; In this source code, First record is 0. not 1.
#   So, Last record is Record count - 1.
#
# AZW.RES (HDContainer) Structure ->
# HDContainer is including HD images. each images have own record, and it's Starts with 'CRES'.
# Images is following main book's image ordering, but not include thumbnail.
# and if image not need to HD resolution (like logo, special character), that record marked as 'Placeholder' for matching image count.
#
# -------------------------------
# | Book        | HDContainer   | Starts with |
# |-------------|-------------- |
# | Image 1 (SD)| HDImage 1     | <- b'CRES'
# | Image 2     | Placeholder   | <- b'\xA0\xA0\xA0\xA0'
# | Image 3 (SD)| HDImage 3     | <- b'CRES'
# | Image 4 (SD)| HDImage 4     | <- b'CRES'
# | Thumbnail   | *Not exist    |
# -------------------------------
# * This structure is sample. Originally, there is no index number.

## Header offsets for Book file
# 2-byte unsigned short
BHDR_OFFSET_NUM_OF_RECORD = 76

# 4-byte unsigned long
BHDR_OFFSET_FILE_IDENT = 60
BHDR_RECORD0_OFFSET_TEXT_ENCODING = 28
BHDR_RECORD0_OFFSET_FULL_NAME_OFFSET = 84
BHDR_RECORD0_OFFSET_FULL_NAME_LENGTH = 88
BHDR_RECORD0_OFFSET_FIRST_IMAGE_INDEX = 108

# 8-byte Record info structure
#  - [record Data Offset] 4-byte unsinged long
#  - [unused] 4-byte
BHDR_OFFSET_RECORD_INFO_LIST = 78

## Header offsets for HDContainer file
CHDR_OFFSET_FILE_IDENT = 60
CHDR_RECORD0_OFFSET_TEXT_ENCODING = 12
CHDR_RECORD0_OFFSET_FULL_NAME_OFFSET = 40
CHDR_RECORD0_OFFSET_FULL_NAME_LENGTH = 44

TEXT_ENCODING_MAP = {
    65001                   : "UTF-8",
    1252                    : "windows-1252"
}

CONTAINER_CONTENT_TYPE_IMAGE = "IMAGE"
CONTAINER_CONTENT_TYPE_PLACEHOLDER = "PLACEHOLDER"

CONTAINER_NEEDED_TYPES = {
    b"CRES"                 : CONTAINER_CONTENT_TYPE_IMAGE,
    b"\xa0\xa0\xa0\xa0"     : CONTAINER_CONTENT_TYPE_PLACEHOLDER
}

# Actually, this function is grabbed from 'DumpAZW6'. That script can getting from URL where in header of this code.
def get_image_type(imgdata):
    imgtype = imghdr.what(None, imgdata)

    # horrible hack since imghdr detects jxr/wdp as tiffs
    if imgtype is not None and imgtype == "tiff":
        imgtype = "wdp"

    # imghdr only checks for JFIF or Exif JPEG files. Apparently, there are some
    # with only the magic JPEG bytes out there...
    # ImageMagick handles those, so, do it too.
    if imgtype is None:
        if imgdata[0:2] == b'\xFF\xD8':
            # Get last non-null bytes
            last = len(imgdata)
            while (imgdata[last-1:last] == b'\x00'):
                last-=1
            # Be extra safe, check the trailing bytes, too.
            if imgdata[last-2:last] == b'\xFF\xD9':
                imgtype = "jpeg"
    return imgtype

def get_charset(data, offset):
    charset_id, = struct.unpack_from(">L", data, offset)

    if charset_id in TEXT_ENCODING_MAP:
        return TEXT_ENCODING_MAP[charset_id]
    else:
        print u"Unknown Charset %d" % charset_id
        raise

def get_book_title(data, base_offset, name_offset, length_offset, charset):
    name_offset, = struct.unpack_from(">L", data, base_offset + name_offset)
    name_length, = struct.unpack_from(">L", data, base_offset + length_offset)
    name_offset += base_offset

    return data[name_offset:name_offset + name_length].decode(charset)

class MobiMergeHDImage:
    hdimage_dict = None

    def __init__(self, mobi_data):
        self.mobi = mobi_data
        self.record_dict = self.get_record_dict(self.mobi)
        if self.mobi[BHDR_OFFSET_FILE_IDENT:BHDR_OFFSET_FILE_IDENT+8] != b'BOOKMOBI':
            print u"This eBook is not a Mobi."
            raise
        self.charset = get_charset(self.mobi, self.record_dict[0]["OFFSET"] + BHDR_RECORD0_OFFSET_TEXT_ENCODING)
        self.book_title = get_book_title(self.mobi, self.record_dict[0]["OFFSET"], BHDR_RECORD0_OFFSET_FULL_NAME_OFFSET, BHDR_RECORD0_OFFSET_FULL_NAME_LENGTH, self.charset)

    def get_record_dict(self, data):
        current_offset = BHDR_OFFSET_NUM_OF_RECORD
        record_count, = struct.unpack_from(">H", data, current_offset)
        record_dict = dict()

        record_dict["COUNT"] = record_count

        for index in range(0, record_count):
            record_dict[index] = dict()

            offset = BHDR_OFFSET_RECORD_INFO_LIST + index * 8

            record_dict[index]["INFO_OFFSET"] = offset
            record_dict[index]["OFFSET"], = struct.unpack_from(">L", data, offset)

        return record_dict

    def load_azwres(self, res_file):
        with open(res_file, 'rb') as azwresfile:
            azwres = azwresfile.read()
        if azwres[CHDR_OFFSET_FILE_IDENT:CHDR_OFFSET_FILE_IDENT + 8] != b'RBINCONT':
            print u"%s is not a HDImage container." % os.path.basename(res_file)
            raise
        
        azwres_dict = self.get_record_dict(azwres)

        azwres_title = get_book_title(azwres, azwres_dict[0]["OFFSET"], CHDR_RECORD0_OFFSET_FULL_NAME_OFFSET, CHDR_RECORD0_OFFSET_FULL_NAME_LENGTH, self.charset)

        if self.book_title != azwres_title:
            print u"Book mismatch. Book title and HDImage container title is not same. "
            print u"Book: %s, Container: %s" % (self.book_title, azwres_title)
            raise

        self.hdimage_dict = dict()
        
        image_index = 0
        for index, val in sorted(azwres_dict.items()):
            if index != "COUNT" and azwres[val["OFFSET"]:val["OFFSET"] + 2] != b"\xe9\x8e":
                if azwres[val["OFFSET"]:val["OFFSET"] + 4] in CONTAINER_NEEDED_TYPES:
                    self.hdimage_dict[image_index] = dict()
                    self.hdimage_dict[image_index]["INDEX"] = index
                    self.hdimage_dict[image_index]["TYPE"] = CONTAINER_NEEDED_TYPES[azwres[val["OFFSET"]:val["OFFSET"] + 4]]
                    if self.hdimage_dict[image_index]["TYPE"] == CONTAINER_CONTENT_TYPE_IMAGE:
                        self.hdimage_dict[image_index]["CONTENT"] = azwres[val["OFFSET"] + 12:azwres_dict[index + 1]["OFFSET"]]
                    
                    image_index += 1

    def record_offset_update(self, record_index, modified_offset_size):
        for target_record_index in range(record_index + 1, self.record_dict["COUNT"]):
            self.record_dict[target_record_index]["OFFSET"] = self.record_dict[target_record_index]["OFFSET"] + modified_offset_size
            self.mobi = "".join(
                (
                    self.mobi[:self.record_dict[target_record_index]["INFO_OFFSET"]],
                    struct.pack(">L", self.record_dict[target_record_index]["OFFSET"]),
                    self.mobi[self.record_dict[target_record_index]["INFO_OFFSET"] + 4:]
                )
            )

    def merge(self):
        if self.hdimage_dict is None:
            print u"'azw.res' file is not loaded yet."
            raise

        first_record_offset = self.record_dict[0]['OFFSET']

        # Find original book's image
        first_image_index, = struct.unpack_from(">L", self.mobi, first_record_offset + 108)

        images_dict = dict()
        image_index = 0
        for record_index in range(first_image_index, self.record_dict["COUNT"]):
            if record_index + 1 == self.record_dict["COUNT"]:
                img = self.mobi[self.record_dict[record_index]["OFFSET"]:]
            else:    
                img = self.mobi[self.record_dict[record_index]["OFFSET"]:self.record_dict[record_index + 1]["OFFSET"]]
            
            if get_image_type(img) is not None:
                images_dict[image_index] = dict()
                images_dict[image_index]["INDEX"] = record_index
                images_dict[image_index]["CONTENT"] = img
                image_index += 1

        # Merge
        for index, hdimage in self.hdimage_dict.items():
            if hdimage["TYPE"] == CONTAINER_CONTENT_TYPE_IMAGE:
                # If HDImage type is IMAGE, do merge.
                image_offset = self.record_dict[images_dict[index]["INDEX"]]["OFFSET"]

                if self.mobi.find(images_dict[index]["CONTENT"]) != -1:
                    size_difference = len(hdimage["CONTENT"]) - len(images_dict[index]["CONTENT"])

                    self.mobi = self.mobi.replace(images_dict[index]["CONTENT"], hdimage["CONTENT"])

                    self.record_offset_update(images_dict[index]["INDEX"], size_difference)

            else:
                # Skip if it's not a image (Maybe PLACEHOLDER)
                pass

        return self.mobi
        
