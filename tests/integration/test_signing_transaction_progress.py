"""Real offscreen Qt proof for non-blocking signing transaction feedback."""

from __future__ import annotations

import os
from pathlib import Path
from threading import Event

import pytest

from foliaseal.application import SigningDraftWorkflow
from foliaseal.application.signing_readiness import (
    SigningReadinessInputs,
    project_signing_readiness,
)
from foliaseal.domain.models import SigningResult
from foliaseal.presentation.qt.signing_action_boundary import SigningActionBoundary
from foliaseal.presentation.qt.signing_action_coordinator import SigningActionCoordinator
from foliaseal.presentation.qt.signing_transaction_runner import ThreadSigningTransactionRunner
from tests.support.signing_builders import build_signature_appearance, build_signature_rect


def test_real_offscreen_transaction_polls_without_blocking_qt(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    created_app = app is None
    if app is None:
        app = QApplication(["foliaseal-signing-transaction-test"])

    workflow = SigningDraftWorkflow(
        input_pdf_path=str(tmp_path / "input.pdf"),
        output_pdf_path=str(tmp_path / "output.pdf"),
        certificate_path=str(tmp_path / "certificate.p12"),
        passphrase="secret",
        tsa_url="https://tsa.example.com",
        timestamp_required=False,
        certificate_alias="test-certificate",
        signature_appearance=build_signature_appearance(),
        signature_rect=build_signature_rect(page_index=0),
    )
    started = Event()
    release = Event()
    result = SigningResult(
        success=True,
        failure_code=None,
        message="Signing completed successfully.",
    )

    def execute(_request):
        started.set()
        release.wait(timeout=3)
        return result

    def readiness():
        return project_signing_readiness(
            SigningReadinessInputs(
                selected_preset_name="Approval",
                has_saved_presets=True,
                certificate_selected=True,
                certificate_blocking=False,
                certificate_detail="",
                certificate_warning=False,
                placement_present=True,
                validation_text="Ready to sign.",
                ready_to_sign=True,
            )
        )
    coordinator = SigningActionCoordinator(
        workflow=workflow,
        apply_changes=lambda: None,
        readiness=readiness,
        sign_executor=execute,
    )
    runner = ThreadSigningTransactionRunner(execute)
    boundary = SigningActionBoundary(coordinator=coordinator, transaction_runner=runner)
    observed_elapsed: list[float] = []
    completions = []
    pump = QTimer()

    def poll() -> None:
        state = coordinator.load()
        observed_elapsed.append(state.transaction_elapsed_seconds)
        completion = boundary.poll_transaction()
        if completion is not None:
            completions.append(completion)
            pump.stop()
            app.quit()

    pump.timeout.connect(poll)
    try:
        started_transition = boundary.begin_transaction()
        assert started_transition.request is not None
        assert started.wait(timeout=1)
        pump.start(50)
        QTimer.singleShot(1100, release.set)
        QTimer.singleShot(2500, app.quit)
        app.exec()
        assert any(elapsed >= 1.0 for elapsed in observed_elapsed)
        assert completions
        assert completions[-1].state.last_signing_result == result
        assert completions[-1].state.transaction_active is False
    finally:
        pump.stop()
        boundary.close_transaction()
        if created_app:
            app.quit()
