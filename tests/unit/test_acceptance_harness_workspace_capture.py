from __future__ import annotations

import dataclasses
import subprocess
import sys

import pytest

from foliaseal.presentation.qt.acceptance_harness_workspace_capture import (
    AcceptanceHarnessWorkspaceCaptureInput,
    AcceptanceHarnessWorkspaceCaptureService,
    AcceptanceHarnessWorkspaceSnapshot,
)


def _capture_input(*, label: str | None = None) -> AcceptanceHarnessWorkspaceCaptureInput:
    return AcceptanceHarnessWorkspaceCaptureInput(
        current_request=None,
        last_signing_result=None,
        capture_index=3,
        capture_kind="preview",
        capture_label=label,
        preview_snapshot={"render": "ok"},
        preview_text="Ready",
        validation_text="Valid",
        sign_request_snapshot=None,
        backend_reservation_snapshot={"fits": True},
        backend_reservation_error=None,
    )


def test_capture_service_preserves_mapping_and_optional_label() -> None:
    snapshot = AcceptanceHarnessWorkspaceCaptureService().build_snapshot(
        _capture_input(label="Preview 3")
    )

    assert isinstance(snapshot, AcceptanceHarnessWorkspaceSnapshot)
    assert snapshot.as_mapping() == {
        "capture_index": 3,
        "capture_kind": "preview",
        "capture_label": "Preview 3",
        "preview_snapshot": {"render": "ok"},
        "preview_text": "Ready",
        "validation_text": "Valid",
        "sign_request_snapshot": None,
        "backend_reservation_snapshot": {"fits": True},
        "backend_reservation_error": None,
    }


def test_capture_service_omits_empty_label_without_changing_fields() -> None:
    snapshot = AcceptanceHarnessWorkspaceCaptureService().build_snapshot(_capture_input())

    assert "capture_label" not in snapshot.as_mapping()
    assert snapshot.backend_reservation_snapshot == {"fits": True}


def test_capture_input_is_immutable() -> None:
    data = _capture_input()

    with pytest.raises(dataclasses.FrozenInstanceError):
        data.capture_index = 4  # type: ignore[misc]


def test_capture_module_import_is_free_of_optional_runtime_dependencies() -> None:
    code = (
        "import sys; "
        "import foliaseal.presentation.qt.acceptance_harness_workspace_capture; "
        "print(any(name.startswith('PySide6') or name in {'PIL', 'pyhanko'} "
        "for name in sys.modules))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "False"
