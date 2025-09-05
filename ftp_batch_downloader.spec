# -*- mode: python ; coding: utf-8 -*-

import os

# Include data files that the application needs
datas = [
    # Essential data files
    ('servers.json', '.'),              # Server bookmarks
    ('config.json', '.'),               # Application config
    ('resources/icons/favicon.ico', 'resources/icons/'),  # Application icon
    ('requirements.txt', '.'),          # Dependencies info
    
    # Include entire directories if they exist
]

# Add cache directory if it exists
if os.path.exists('cache'):
    datas.append(('cache', 'cache'))

# Add data directory if it exists  
if os.path.exists('data'):
    datas.append(('data', 'data'))

# Hidden imports for PyQt5 and other dependencies
hiddenimports = [
    'PyQt5.QtCore',
    'PyQt5.QtGui', 
    'PyQt5.QtWidgets',
    'PyQt5.QtWebEngineWidgets',
    'PyQt5.QtWebEngine',
    'PyQt5.QtWebEngineCore',
    'PyQt5.QtNetwork',
    'PyQt5.QtPrintSupport',
    'requests',
    'urllib3',
    'certifi',
    'charset_normalizer',
    'idna',
    'sip',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='FTP_Batch_Downloader_With_Bookmarks',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icons/favicon.ico',
)
