# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:\\Code_app\\Social_downloader\\src\\Main.py'],
    pathex=[],
    binaries=[('assets/ffmpeg.exe', '.'), ('assets/ffprobe.exe', '.'), ('assets/ffplay.exe', '.')],
    datas=[('D:\\Code_app\\Social_downloader\\assets', 'assets'), ('D:\\Code_app\\Social_downloader\\config', 'config'), ('D:\\Code_app\\Social_downloader\\data', 'data'), ('D:\\Code_app\\Social_downloader\\src', 'src')],
    hiddenimports=['customtkinter', 'yt_dlp', 'PIL', 'tkinter', 'json', 'threading', 'shutil', 'os', 'sys', 'datetime', 're', 'src.ui', 'src.downloader', 'src.utils'],
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
    icon=['D:\\Code_app\\Social_downloader\\assets\\CH.ico'],
)
