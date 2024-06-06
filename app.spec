# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import copy_metadata

datas = [
    ('templates/*', 'templates'),
    ('static/*', 'static')
]
datas += copy_metadata('img2pdf')
datas += copy_metadata('pypdf')
datas += copy_metadata('flask')
datas += copy_metadata('docx2pdf')
datas += copy_metadata('comtypes')
datas += copy_metadata('cryptography')
datas += copy_metadata('waitress')

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['flask', 'img2pdf', 'pypdf', 'docx2pdf', 'comtypes', 'cryptography', 'waitress'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Stitch It',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
