"""One-command signed acceptance evidence orchestration."""

from __future__ import annotations

import logging
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from foliaseal.application.evidence_ports import AssetGeneratorPort, MatrixRunnerPort
from foliaseal.application.evidence_service import (
    EvidenceService,
)
from foliaseal.application.phase3_evidence_core import (
    validate_signed_acceptance_matrix_summary,
)
from foliaseal.application.qa_evidence_contract import (
    evaluate_phase3_evidence_contract,
)
from foliaseal.presentation.qt.evidence_runner_factories import (
    build_interactive_evidence_operation,
    build_preview_evidence_operation,
    build_signed_acceptance_evidence_operation,
)

DEFAULT_SIGNED_ACCEPTANCE_EVIDENCE_SUMMARY_PATH = (
    "artifacts/phase3_signed_acceptance_evidence_summary.md"
)

__all__ = [
    "DEFAULT_SIGNED_ACCEPTANCE_EVIDENCE_SUMMARY_PATH",
    "build_default_evidence_service",
    "validate_signed_acceptance_matrix_summary",
]

_PYHANKO_DUMMY_TSA_LOGGER = "pyhanko.sign.validation.generic_cms"
_PYHANKO_LAYOUT_LOGGER = "pyhanko.pdf_utils.layout"
_DUMMY_TSA_SUBJECT_FRAGMENT = "Common Name: FoliaSeal TSA, Organization: FoliaSeal, Country: US"
_DUMMY_TSA_SELF_SIGNED_FRAGMENT = "The X.509 certificate provided is self-signed"
_BENIGN_PYHANKO_LAYOUT_FRAGMENT = "post_margin will be ignored"
_BENIGN_QT_OFFSCREEN_MESSAGE = "This plugin does not support propagateSizeHints()"


class _SignedEvidenceRuntimeNoiseFilter(logging.Filter):
    def __init__(self, *, suppress_layout_warnings: bool) -> None:
        super().__init__()
        self._suppress_layout_warnings = suppress_layout_warnings

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        if (
            "Validation error [cert context:" in message
            and _DUMMY_TSA_SUBJECT_FRAGMENT in message
            and _DUMMY_TSA_SELF_SIGNED_FRAGMENT in message
        ):
            return False
        if (
            self._suppress_layout_warnings
            and record.name == _PYHANKO_LAYOUT_LOGGER
            and message.startswith("Content box width/height ")
            and _BENIGN_PYHANKO_LAYOUT_FRAGMENT in message
        ):
            return False
        return True


@contextmanager
def _suppress_known_signed_evidence_runtime_chatter(*, suppress_layout_warnings: bool):
    noise_filter = _SignedEvidenceRuntimeNoiseFilter(
        suppress_layout_warnings=suppress_layout_warnings
    )
    loggers = [
        logging.getLogger(_PYHANKO_DUMMY_TSA_LOGGER),
        logging.getLogger(_PYHANKO_LAYOUT_LOGGER),
    ]
    for logger in loggers:
        logger.addFilter(noise_filter)
    with _suppress_known_qt_runtime_chatter():
        try:
            yield
        finally:
            for logger in loggers:
                logger.removeFilter(noise_filter)


@contextmanager
def _suppress_known_qt_runtime_chatter():
    try:
        from PySide6 import QtCore
    except Exception:
        yield
        return

    previous_handler = QtCore.qInstallMessageHandler(None)

    def handler(mode: Any, context: Any, message: str) -> None:
        if message == _BENIGN_QT_OFFSCREEN_MESSAGE:
            return
        if previous_handler is not None:
            previous_handler(mode, context, message)
            return
        print(message, file=sys.stderr)

    QtCore.qInstallMessageHandler(handler)
    try:
        yield
    finally:
        QtCore.qInstallMessageHandler(previous_handler)


def _write_evidence_markdown(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_default_evidence_service(
    *,
    asset_generator: AssetGeneratorPort | None = None,
    matrix_runner: MatrixRunnerPort | None = None,
) -> EvidenceService:
    if asset_generator is None:
        def deferred_asset_generator(*, root: Path):
            from foliaseal.application.qa_signed_acceptance_generation import (
                generate_signed_acceptance_assets,
            )

            return generate_signed_acceptance_assets(root=root)

        asset_generator = deferred_asset_generator
    def matrix_runtime_context(name: str):
        return _suppress_known_signed_evidence_runtime_chatter(
            suppress_layout_warnings=name == "signed_fit_rejection_matrix"
        )

    return EvidenceService(
        harness_runner=build_interactive_evidence_operation(),
        preview_matrix_runner=build_preview_evidence_operation(),
        signed_acceptance_matrix_runner=(
            matrix_runner or build_signed_acceptance_evidence_operation()
        ),
        asset_generator=asset_generator,
        capture_contract_evaluator=evaluate_phase3_evidence_contract,
        text_writer=_write_evidence_markdown,
        matrix_runtime_context_factory=matrix_runtime_context,
    )
