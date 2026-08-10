"""Offscreen Qt transport coverage for the single-owner open-request boundary."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from foliaseal.presentation.qt.single_instance import (
    OpenRequest,
    QtLocalInstanceCoordinator,
    SingleInstanceUnavailable,
)


def test_second_invocation_forwards_to_existing_qt_owner(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtNetwork import QLocalServer, QLocalSocket
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    created_app = app is None
    if app is None:
        app = QApplication(["foliaseal-single-instance-test"])

    endpoint = str(tmp_path / "foliaseal-instance.sock")
    received: list[OpenRequest] = []
    owner = QtLocalInstanceCoordinator(
        endpoint=endpoint,
        q_local_server=QLocalServer,
        q_local_socket=QLocalSocket,
    )
    secondary = QtLocalInstanceCoordinator(
        endpoint=endpoint,
        q_local_server=QLocalServer,
        q_local_socket=QLocalSocket,
    )
    request = OpenRequest(pdf_path=str((tmp_path / "contract.pdf").resolve()))
    owner.set_request_handler(received.append)

    try:
        try:
            owner_started = owner.start_or_forward(OpenRequest(None))
        except SingleInstanceUnavailable as exc:
            pytest.skip(f"QLocalServer unavailable in this environment: {exc}")
        assert owner_started is True
        assert secondary.start_or_forward(request) is False
        deadline = time.monotonic() + 1.0
        while not received and time.monotonic() < deadline:
            app.processEvents()
            time.sleep(0.01)
        assert received == [request]
    finally:
        secondary.close()
        owner.close()
        QLocalServer.removeServer(endpoint)
        if created_app:
            app.quit()
