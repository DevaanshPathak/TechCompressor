# -*- mode: python ; coding: utf-8 -*-
"""
TechCompressor PyInstaller Build Specification

This spec file is optimized to reduce antivirus false positives by:
1. Disabling UPX compression (primary trigger for AV heuristics)
2. Using onedir mode for transparency (no self-extraction)
3. Adding Windows version metadata for legitimacy
4. Properly handling cryptography library binaries
5. Excluding unnecessary modules to reduce attack surface
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all techcompressor modules
techcompressor_modules = collect_submodules('techcompressor')

# Version information for Windows executable
version_info = {
    'version': '1.2.0.0',
    'company_name': 'Devaansh Pathak',
    'file_description': 'TechCompressor - Multi-algorithm Compression Tool',
    'internal_name': 'TechCompressor',
    'legal_copyright': 'Copyright (c) 2025 Devaansh Pathak',
    'original_filename': 'TechCompressor.exe',
    'product_name': 'TechCompressor',
    'product_version': '1.2.0.0'
}

a = Analysis(
    ['techcompressor/gui.py'],  # Main entry point (GUI includes CLI functionality)
    pathex=[],
    binaries=[],
    datas=[
        ('README.md', '.'),
        ('LICENSE', '.'),
        ('CHANGELOG.md', '.'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'tqdm',
        'cryptography',
        'cryptography.hazmat',
        'cryptography.hazmat.primitives',
        'cryptography.hazmat.primitives.ciphers',
        'cryptography.hazmat.primitives.kdf',
        'cryptography.hazmat.backends',
    ] + techcompressor_modules,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude test and development modules
        'pytest',
        'unittest',
        'test',
        '_pytest',
        # Exclude unnecessary standard library modules
        'pydoc',
        'doctest',
        'pdb',
        'distutils',
        'setuptools',
        'pip',
        # Exclude GUI frameworks we don't use
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'wx',
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
    exclude_binaries=True,  # Use onedir mode, not onefile
    name='TechCompressor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # CRITICAL: Disable UPX to prevent false positives
    console=False,  # GUI application (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Windows-specific settings
    version='file_version_info.txt' if sys.platform == 'win32' else None,
    icon=None,  # Icon file not included in repository
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,  # CRITICAL: Disable UPX for all binaries
    upx_exclude=[],  # Empty since UPX is disabled
    name='TechCompressor',
)
