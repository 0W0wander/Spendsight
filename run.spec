# -*- mode: python ; coding: utf-8 -*-
import certifi

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('frontend/templates', 'frontend/templates'),
        ('frontend/static', 'frontend/static'),
        # NOTE: 'data' folder is NOT bundled - it contains user's personal rules,
        # notes, and uploaded files. The app creates these directories automatically
        # via Config.init_app() when it starts. Users create their own data.
        ('spendsighticon.ico', '.'),  # Include ICO icon in root for tray
        ('spendsighticon.png', '.'),  # Include PNG icon as fallback
        (certifi.where(), 'certifi'),  # Include SSL certificates
    ],
    hiddenimports=[
        'numpy',
        'pandas',
        'pystray',
        'pystray._win32',  # Windows-specific pystray backend
        'PIL',
        'PIL.Image',
        'certifi',
        'ssl',
    ],
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
    name='Spendsight',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Hide console window - app runs in system tray
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='spendsighticon.ico',  # Use ICO for app icon (better Windows support)
)
