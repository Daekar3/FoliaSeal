"""Lazy, explicit gateways for the interactive and matrix evidence lifecycles."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any

from foliaseal.application.phase3_evidence_service import (
    Phase3HarnessCaptureRequest,
    Phase3MatrixRequest,
)

if TYPE_CHECKING:
    from foliaseal.presentation.qt.phase3_interactive_capture import Phase3HarnessCapture
else:
    Phase3HarnessCapture = Any

MatrixSummary = Mapping[str, Any]


class InteractiveEvidenceGateway:
    """Build and run the interactive capture lifecycle on first use."""

    def __init__(
        self,
        factory: Callable[
            [], Callable[[Phase3HarnessCaptureRequest], Phase3HarnessCapture]
        ],
    ) -> None:
        self._factory = factory
        self._runner: Callable[[Phase3HarnessCaptureRequest], Phase3HarnessCapture] | None = None

    def run(self, request: Phase3HarnessCaptureRequest) -> Phase3HarnessCapture:
        if self._runner is None:
            self._runner = self._factory()
        return self._runner(request)


class PreviewEvidenceGateway:
    """Build and run the headless preview matrix lifecycle on first use."""

    def __init__(
        self,
        factory: Callable[[], Callable[[Phase3MatrixRequest], MatrixSummary]],
    ) -> None:
        self._factory = factory
        self._runner: Callable[[Phase3MatrixRequest], MatrixSummary] | None = None

    def run(self, request: Phase3MatrixRequest) -> MatrixSummary:
        if self._runner is None:
            self._runner = self._factory()
        return self._runner(request)


class SignedAcceptanceEvidenceGateway:
    """Build and run the signed-acceptance matrix lifecycle on first use."""

    def __init__(
        self,
        factory: Callable[[], Callable[[Phase3MatrixRequest], MatrixSummary]],
    ) -> None:
        self._factory = factory
        self._runner: Callable[[Phase3MatrixRequest], MatrixSummary] | None = None

    def run(self, request: Phase3MatrixRequest) -> MatrixSummary:
        if self._runner is None:
            self._runner = self._factory()
        return self._runner(request)


def build_interactive_evidence_gateway() -> InteractiveEvidenceGateway:
    """Return a gateway whose Qt harness graph is imported only when run."""

    def factory() -> Callable[[Phase3HarnessCaptureRequest], Phase3HarnessCapture]:
        from foliaseal.presentation.qt.phase3_harness import (
            _build_interactive_evidence_runner,
        )

        return _build_interactive_evidence_runner().run

    return InteractiveEvidenceGateway(factory)


def build_preview_evidence_gateway() -> PreviewEvidenceGateway:
    """Return a gateway whose preview runner is built only when run."""

    def factory() -> Callable[[Phase3MatrixRequest], MatrixSummary]:
        from foliaseal.presentation.qt.phase3_harness import (
            _build_phase3_preview_matrix_runner,
        )

        runner = _build_phase3_preview_matrix_runner()

        def run(request: Phase3MatrixRequest) -> MatrixSummary:
            return runner.run(
                pdf_path=request.pdf_path,
                certificate_path=request.certificate_path,
                passphrase=request.passphrase,
                scenario_manifest_path=request.scenario_manifest_path,
                artifacts_dir=request.artifacts_dir,
            )

        return run

    return PreviewEvidenceGateway(factory)


def build_signed_acceptance_evidence_gateway() -> SignedAcceptanceEvidenceGateway:
    """Return a gateway whose signed matrix runner is built only when run."""

    def factory() -> Callable[[Phase3MatrixRequest], MatrixSummary]:
        from foliaseal.presentation.qt.phase3_harness import (
            _build_phase3_signed_acceptance_matrix_runner,
        )

        runner = _build_phase3_signed_acceptance_matrix_runner()

        def run(request: Phase3MatrixRequest) -> MatrixSummary:
            return runner.run(
                pdf_path=request.pdf_path,
                certificate_path=request.certificate_path,
                passphrase=request.passphrase,
                scenario_manifest_path=request.scenario_manifest_path,
                artifacts_dir=request.artifacts_dir,
            )

        return run

    return SignedAcceptanceEvidenceGateway(factory)
