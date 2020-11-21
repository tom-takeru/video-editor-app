# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['videdi.py'],
             pathex=['/Users/takeruyoshimura/Desktop/Study/PythonLesson/Tkinter/videdi'],
             binaries=[ ('/usr/local/bin/ffmpeg', '.'), ('/usr/local/bin/ffprobe', '.')],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='videdi',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          icon='videdi_icon.icns' )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='videdi')
app = BUNDLE(coll,
             name='videdi.app',
             icon='videdi_icon.icns',
             info_plist={ 'NSHighResolutionCapable': 'True'}, #<-- Option for High Resolution
             bundle_identifier=None)
