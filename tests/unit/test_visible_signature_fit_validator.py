from __future__ import annotations

import inspect
import os
import subprocess
import sys
from pathlib import Path

from foliaseal.application import signing_draft_workflow
from foliaseal.application.visible_signature_fit_validator import (
    BackendVisibleSignatureFitValidator,
)


def test_adapter_import_does_not_load_backend_or_heavy_runtime() -> None:
    script = """
import sys
import foliaseal.application.visible_signature_fit_validator
blocked = ('foliaseal.application.phase3_signing_backend', 'pyhanko', 'PIL', 'PyQt', 'PySide6')
loaded = sorted(
    name for name in sys.modules
    if any(name == prefix or name.startswith(prefix + '.') for prefix in blocked)
)
assert not loaded, loaded
"""
    environment = os.environ.copy()
    source_root = str(Path(__file__).resolve().parents[2] / "src")
    environment["PYTHONPATH"] = os.pathsep.join(
        (source_root, environment.get("PYTHONPATH", ""))
    ).rstrip(os.pathsep)
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_missing_certificate_preserves_no_fit_issue_behavior(tmp_path: Path) -> None:
    validator = BackendVisibleSignatureFitValidator(
        certificate_path=str(tmp_path / "missing.p12"),
    )
    # The adapter short-circuits before touching appearance conversion or backend imports.
    assert validator.validate(object()) == ()  # type: ignore[arg-type]


def test_workflow_uses_typed_validator_without_backend_import() -> None:
    source = inspect.getsource(signing_draft_workflow)
    assert "phase3_signing_backend" not in source
    assert "BackendVisibleSignatureFitValidator" in source
