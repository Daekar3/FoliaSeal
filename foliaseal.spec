"""PyInstaller one-dir build for the FoliaSeal development CLI."""

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

# PyInstaller executes spec files as code without defining ``__file__``.
# ``SPECPATH`` is the stable spec-directory variable supplied by PyInstaller.
PROJECT_ROOT = Path(SPECPATH).resolve()  # noqa: F821
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from foliaseal.build.pyinstaller_support import collect_runtime_assets  # noqa: E402

hiddenimports = collect_submodules("foliaseal") + [
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtNetwork",
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    "PySide6.QtPrintSupport",
    "PySide6.QtSvg",
    "PySide6.QtWidgets",
]
runtime_assets = collect_runtime_assets(PROJECT_ROOT)


a = Analysis(  # noqa: F821
    ["src/foliaseal/__main__.py"],
    pathex=["src"],
    binaries=[],
    datas=runtime_assets,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    [],
    name="foliaseal",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    exclude_binaries=True,
)

coll = COLLECT(  # noqa: F821
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="foliaseal",
)
