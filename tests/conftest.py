"""Shared test cleanup for FoliaSeal-owned temporary resources."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def cleanup_new_canonical_preview_roots():
    """Remove only canonical-preview roots created by the current test."""

    temp_root = Path(tempfile.gettempdir())
    before = {
        path
        for path in temp_root.iterdir()
        if path.is_dir() and path.name.startswith("foliaseal-canonical-preview-")
    }
    yield
    after = {
        path
        for path in temp_root.iterdir()
        if path.is_dir() and path.name.startswith("foliaseal-canonical-preview-")
    }
    for path in after - before:
        shutil.rmtree(path, ignore_errors=True)
