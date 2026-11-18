# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:/zcodetest/mediahub/tools/installer/setup_main.py'],
    pathex=[],
    binaries=[],
    datas=[('D:/zcodetest/mediahub/installer_build/payload.zip', 'payload'), ('D:/zcodetest/mediahub/installer_build/uninstall.exe', 'payload')],
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
    name='setup',
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
    icon=['D:/zcodetest/mediahub/app/resources/icon.ico'],
)
