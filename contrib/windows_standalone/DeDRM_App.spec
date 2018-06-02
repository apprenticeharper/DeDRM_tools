# -*- mode: python -*-
import os
from os.path import dirname

from PyInstaller.building.api import PYZ, EXE, COLLECT
from PyInstaller.building.build_main import Analysis

block_cipher = None


a = Analysis(['../windows/DeDRM_App/DeDRM_lib/DeDRM_App.pyw'],
             pathex=['src'],
             binaries=[],
             datas=[
                 ('../../src/alfcrypto.dll', '.'),
                 ('../../src/alfcrypto64.dll', '.'),
             ],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='DeDRM_App',
          debug=False,
          strip=False,
          upx=False,
          console=True,
          icon='contrib\\windows_standalone\\DeDRM.ico',
          )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='DeDRM_App')
