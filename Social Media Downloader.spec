# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['customtkinter', 'yt_dlp', 'PIL', 'PIL._tkinter_finder', 'PIL._imaging', 'PIL.Image', 'PIL.ImageTk', 'tkinter', 'json', 'csv', 'threading', 'shutil', 'os', 'sys', 'datetime', 're', 'platform', 'subprocess', 'src.ui', 'src.downloader', 'src.utils', 'packaging', 'packaging.version']
hiddenimports += collect_submodules('PIL')
hiddenimports += collect_submodules('src')


a = Analysis(
    ['d:\\Code_app\\Social_Downloader\\src\\main.py'],
    pathex=[],
    binaries=[('assets/ffmpeg.exe', 'assets'), ('assets/ffprobe.exe', 'assets'), ('assets/ffplay.exe', 'assets')],
    datas=[('d:\\Code_app\\Social_Downloader\\assets', 'assets'), ('d:\\Code_app\\Social_Downloader\\data', 'data'), ('d:\\Code_app\\Social_Downloader\\src', 'src')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Social Media Downloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['d:\\Code_app\\Social_Downloader\\assets\\CH.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Social Media Downloader',
)
