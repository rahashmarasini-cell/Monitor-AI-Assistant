# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules, collect_dynamic_libs
import glob, os

block_cipher = None

# Explicitly collect llama_cpp native DLLs (loaded via ctypes, not import)
_llama_lib = os.path.join('.venv-1', 'Lib', 'site-packages', 'llama_cpp', 'lib')
llama_binaries = [(dll, 'llama_cpp/lib') for dll in glob.glob(os.path.join(_llama_lib, '*.dll'))]

hidden_imports = [
    'llama_cpp',
    'llama_cpp.llama',
    'screeninfo',
    'screeninfo.screeninfo',
    'mss',
    'mss.windows',
    'PIL',
    'PIL.Image',
    'PIL.ImageOps',
    'PIL.ImageFilter',
    'cv2',
    'numpy',
    'tkinter',
    'tkinter.scrolledtext',
    'pytesseract',
    'pytesseract.pytesseract',
    'packaging',
    'packaging.version',
    'packaging.specifiers',
    'packaging.requirements',
    'src',
    'src.main',
    'src.config',
    'src.screen_capture',
    'src.ocr_processor',
    'src.ai_processor',
    'src.local_llm',
    'src.answer_window',
    'src.graph_analyzer',
    'src.vision_llm',
]
hidden_imports.extend(collect_submodules('llama_cpp'))
hidden_imports.extend(collect_submodules('pytesseract'))

# Heavy packages in the venv that are NOT used — exclude to keep build lean
excludes = [
    'paddleocr',
    'paddle',
    'modelscope',
    'torch',
    'torchvision',
    'torchaudio',
    'tensorflow',
    'openai',
    'matplotlib',
    'scipy',
    'sklearn',
    'IPython',
    'jupyter',
    'notebook',
]

a = Analysis(
    ['run.py'],
    pathex=['.'],
    binaries=llama_binaries,
    datas=[],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MonitorAI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if __import__('os').path.exists('icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='MonitorAI',
)
