# -*- mode: python ; coding: utf-8 -*-

import os

project_root = os.path.dirname(os.path.abspath(SPECPATH))


a = Analysis(
    [os.path.join(project_root, 'HMI', 'rdma_gui.py')],
    pathex=[project_root],
    binaries=[],
    datas=[(os.path.join(project_root, 'data', 'Simple_c1.dsf'), 'data')],
    hiddenimports=[],
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
    name='RDMA_GUI',
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
)