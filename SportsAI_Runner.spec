# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['/home/kepler/Documentos/APPS/PYTHON/FUTBOL_WIN/sports-ai/WINDOWS/runner.py'],
    pathex=['/home/kepler/Documentos/APPS/PYTHON/FUTBOL_WIN/sports-ai'],
    binaries=[],
    datas=[('/home/kepler/Documentos/APPS/PYTHON/FUTBOL_WIN/sports-ai/backend', 'backend'), ('/home/kepler/Documentos/APPS/PYTHON/FUTBOL_WIN/sports-ai/WINDOWS/loro.png', '.')],
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
    [],
    exclude_binaries=True,
    name='SportsAI_Runner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SportsAI_Runner',
)
