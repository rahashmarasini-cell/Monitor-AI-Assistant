# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Monitor-AI Assistant
# Usage: pyinstaller MonitorAI.spec

from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import sys
import os

# Collect data files from packages that include models/resources
paddleocr_datas = collect_data_files('paddleocr')
screeninfo_datas = collect_data_files('screeninfo')

# Collect hidden imports that PyInstaller might miss
hidden_imports = [
    'paddleocr',
    'paddleocr.paddle_ocr',
    'paddleocr.tools',
    'llama_cpp',
    'llama_cpp.llama',
    'screeninfo',
    'screeninfo.screeninfo',
    'mss',
    'PIL',
    'cv2',
    'numpy',
    'tkinter',
]

# Add all submodules from key packages
hidden_imports.extend(collect_submodules('paddleocr'))
hidden_imports.extend(collect_submodules('llama_cpp'))

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=paddleocr_datas + screeninfo_datas + [
        ('models', 'models'),           # Include GGML model file
        ('hooks', 'hooks'),              # Include PyInstaller hooks
    ],
    hiddenimports=hidden_imports,
    hookspath=['hooks'],                # Use our custom hooks
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MonitorAI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                      # No console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)

# Optional: Create a directory of loose files instead of one-file exe
# This is useful for debugging and smaller updates
# Uncomment to use:
#
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='MonitorAI'
# )
