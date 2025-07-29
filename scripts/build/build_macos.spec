# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

# Get project root from current working directory
project_root = Path(os.getcwd())

# Add src to path for imports
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

block_cipher = None

# Collect data files that exist
datas = []

# Add config files
config_path = project_root / 'config' / 'default_config.yaml'
if config_path.exists():
    datas.append((str(config_path), 'config'))

# Add template files
templates_dir = project_root / 'assets' / 'templates'
if templates_dir.exists():
    for template_file in templates_dir.glob('*.yaml'):
        datas.append((str(template_file), 'assets/templates'))

# Add localization files
localization_dir = project_root / 'src' / 'multichannel_messaging' / 'localization'
if localization_dir.exists():
    for lang_file in localization_dir.glob('*.json'):
        datas.append((str(lang_file), 'multichannel_messaging/localization'))

# Add icon files if they exist
icons_dir = project_root / 'assets' / 'icons'
if icons_dir.exists() and list(icons_dir.iterdir()):
    for icon_file in icons_dir.iterdir():
        if icon_file.is_file():
            datas.append((str(icon_file), 'assets/icons'))

a = Analysis(
    [str(project_root / 'src' / 'multichannel_messaging' / 'main.py')],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'multichannel_messaging.gui.main_window',
        'multichannel_messaging.core.config_manager',
        'multichannel_messaging.core.csv_processor',
        'multichannel_messaging.core.models',
        'multichannel_messaging.core.i18n_manager',
        'multichannel_messaging.services.outlook_macos',
        'multichannel_messaging.utils.logger',
        'multichannel_messaging.utils.exceptions',
        'multichannel_messaging.utils.platform_utils',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'pandas',
        'yaml',
        'chardet',
        'colorlog',
        'cerberus',
        'babel',
        'ScriptingBridge',
        'Foundation',
    ],
    hookspath=[str(project_root / 'scripts' / 'build')],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'numpy.distutils',
        'test',
        'unittest',
        'pydoc',
        'doctest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CSC-Reach',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CSC-Reach',
)

app = BUNDLE(
    coll,
    name='CSC-Reach.app',
    icon=str(project_root / 'assets' / 'icons' / 'csc-reach.icns'),
    bundle_identifier='com.csc-reach.app',
    version='1.0.0',
    info_plist={
        'CFBundleName': 'CSC-Reach',
        'CFBundleDisplayName': 'CSC-Reach',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleIdentifier': 'com.csc-reach.app',
        'NSHighResolutionCapable': True,
        'NSAppleEventsUsageDescription': 'CSC-Reach needs to control Microsoft Outlook to send emails.',
        'NSSystemAdministrationUsageDescription': 'CSC-Reach needs system access to integrate with Outlook.',
    },
)
