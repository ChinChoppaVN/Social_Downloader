# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['customtkinter', 'yt_dlp', 'PIL', 'PIL._tkinter_finder', 'PIL._imaging', 'PIL.Image', 'PIL.ImageTk', 'tkinter', 'json', 'csv', 'threading', 'shutil', 'os', 'sys', 'datetime', 're', 'platform', 'subprocess', 'src.ui', 'src.downloader', 'src.utils']
hiddenimports += collect_submodules('PIL')
hiddenimports += collect_submodules('src')


a = Analysis(
    ['D:\\Code_app\\Social_Downloader\\src\\Main.py'],
    pathex=[],
    binaries=[('assets/ffmpeg.exe', '.'), ('assets/ffprobe.exe', '.'), ('assets/ffplay.exe', '.')],
    datas=[('D:\\Code_app\\Social_Downloader\\assets', 'assets'), ('D:\\Code_app\\Social_Downloader\\data', 'data'), ('D:\\Code_app\\Social_Downloader\\src', 'src')],
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
    a.binaries,
    a.datas,
    [],
    name='Social Media Downloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['D:\\Code_app\\Social_Downloader\\assets\\CH.ico'],
)
