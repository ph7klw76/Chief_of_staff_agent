# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Chief of Staff Agent CLI — single-file Windows .exe"""

a = Analysis(
    ['chief_of_staff_agent.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('chief_of_staff_core.py', '.'),
    ],
    hiddenimports=['json', 'pathlib', 'datetime', 'collections', 'uuid', 'argparse', 're', 'statistics', 'csv', 'hashlib'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'tkinter.ttk', 'tkinter.scrolledtext', 'tkinter.messagebox', 'tkinter.filedialog'],
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
    name='ChiefOfStaff-CLI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
