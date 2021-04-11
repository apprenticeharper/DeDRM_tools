#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Engine to remove drm from Kindle KFX ebooks

#  2.0   - Python 3 for calibre 5.0
#  2.1   - Some fixes for debugging
#  2.1.1 - Whitespace!


import os
import shutil
import traceback
import zipfile

from io import BytesIO
try:
    from ion import DrmIon, DrmIonVoucher
except:
    from calibre_plugins.dedrm.ion import DrmIon, DrmIonVoucher


__license__ = 'GPL v3'
__version__ = '2.0'


class KFXZipBook:
    def __init__(self, infile):
        self.infile = infile
        self.voucher = None
        self.decrypted = {}

    def getPIDMetaInfo(self):
        return (None, None)

    def processBook(self, totalpids):
        with zipfile.ZipFile(self.infile, 'r') as zf:
            for filename in zf.namelist():
                with zf.open(filename) as fh:
                    data = fh.read(8)
                    if data != b'\xeaDRMION\xee':
                        continue
                    data += fh.read()
                    if self.voucher is None:
                        self.decrypt_voucher(totalpids)
                    print("Decrypting KFX DRMION: {0}".format(filename))
                    outfile = BytesIO()
                    DrmIon(BytesIO(data[8:-8]), lambda name: self.voucher).parse(outfile)
                    self.decrypted[filename] = outfile.getvalue()

        if not self.decrypted:
            print("The .kfx-zip archive does not contain an encrypted DRMION file")

    def decrypt_voucher(self, totalpids):
        with zipfile.ZipFile(self.infile, 'r') as zf:
            for info in zf.infolist():
                with zf.open(info.filename) as fh:
                    data = fh.read(4)
                    if data != b'\xe0\x01\x00\xea':
                        continue

                    data += fh.read()
                    if b'ProtectedData' in data:
                        break   # found DRM voucher
            else:
                raise Exception("The .kfx-zip archive contains an encrypted DRMION file without a DRM voucher")

        print("Decrypting KFX DRM voucher: {0}".format(info.filename))

        for pid in [''] + totalpids:
            # Belt and braces. PIDs should be unicode strings, but just in case...
            if isinstance(pid, bytes):
                pid = pid.decode('ascii')
            for dsn_len,secret_len in [(0,0), (16,0), (16,40), (32,40), (40,0), (40,40)]:
                if len(pid) == dsn_len + secret_len:
                    break       # split pid into DSN and account secret
            else:
                continue

            try:
                voucher = DrmIonVoucher(BytesIO(data), pid[:dsn_len], pid[dsn_len:])
                voucher.parse()
                voucher.decryptvoucher()
                break
            except:
                traceback.print_exc()
                pass
        else:
            raise Exception("Failed to decrypt KFX DRM voucher with any key")

        print("KFX DRM voucher successfully decrypted")

        license_type = voucher.getlicensetype()
        if license_type != "Purchase":
            raise Exception(("This book is licensed as {0}. "
                    'These tools are intended for use on purchased books.').format(license_type))

        self.voucher = voucher

    def getBookTitle(self):
        return os.path.splitext(os.path.split(self.infile)[1])[0]

    def getBookExtension(self):
        return '.kfx-zip'

    def getBookType(self):
        return 'KFX-ZIP'

    def cleanup(self):
        pass

    def getFile(self, outpath):
        if not self.decrypted:
            shutil.copyfile(self.infile, outpath)
        else:
            with zipfile.ZipFile(self.infile, 'r') as zif:
                with zipfile.ZipFile(outpath, 'w') as zof:
                    for info in zif.infolist():
                        zof.writestr(info, self.decrypted.get(info.filename, zif.read(info.filename)))
