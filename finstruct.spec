# -*- mode: python ; coding: utf-8 -*-
# FinStruct PyInstaller spec

import os
from pathlib import Path

block_cipher = None

# Sentence-transformers model path (bundled if present)
APPDATA = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
MODEL_DIR = APPDATA / "FinStruct" / "models" / "all-MiniLM-L6-v2"

datas = []
if MODEL_DIR.exists():
    datas.append((str(MODEL_DIR), "models/all-MiniLM-L6-v2"))

a = Analysis(
    ["finstruct_app.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # sqlite3 C extension — PyInstaller sometimes misses it on Windows
        "_sqlite3",
        "sqlite3",
        # cryptography / encryption
        "cryptography",
        "cryptography.fernet",
        "cryptography.hazmat.primitives.ciphers",
        "cryptography.hazmat.primitives.ciphers.algorithms",
        "cryptography.hazmat.primitives.ciphers.modes",
        "cryptography.hazmat.backends",
        "cryptography.hazmat.backends.openssl",
        # keyring — platform backends must be explicit
        "keyring",
        "keyring.backends",
        "keyring.backends.Windows",
        "keyring.backends.SecretService",
        "keyring.backends.macOS",
        "keyring.backends.fail",
        "keyring.core",
        # tkinter
        "tkinter",
        "tkinter.ttk",
        "tkinter.filedialog",
        "tkinter.messagebox",
        "tkinter.simpledialog",
        # Office / export
        "openpyxl",
        "openpyxl.styles",
        "openpyxl.utils",
        "reportlab",
        "reportlab.pdfgen",
        "reportlab.lib",
        "reportlab.lib.pagesizes",
        "reportlab.platypus",
        "docx",
        "docx.shared",
        "docx.enum.text",
        "lxml",
        "lxml.etree",
        # Optional AI / ML (skip gracefully if absent at build time)
        "anthropic",
        "openai",
        "google.generativeai",
        "sentence_transformers",
        "sklearn.utils._cython_blas",
        "sklearn.neighbors.typedefs",
        "sklearn.neighbors.quad_tree",
        "sklearn.tree._utils",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["matplotlib", "numpy.random._examples", "test"],
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
    name="FinStruct",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="FinStruct",
)
