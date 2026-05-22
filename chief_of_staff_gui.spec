# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Chief of Staff Agent GUI — single-file Windows .exe"""

a = Analysis(
    ['chief_of_staff_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('chief_of_staff_core.py', '.'),
    ],
    hiddenimports=['tkinter', 'tkinter.ttk', 'tkinter.scrolledtext', 'tkinter.messagebox', 'tkinter.filedialog',
                   'json', 'pathlib', 'datetime', 'collections', 'uuid', 're', 'statistics', 'csv', 'hashlib', 'subprocess'],
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
    name='ChiefOfStaff',
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
    icon=None,
)
