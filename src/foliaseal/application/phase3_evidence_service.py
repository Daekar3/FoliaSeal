"""Service boundary for Phase 3 evidence workflows."""

from __future__ import annotations

from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from foliaseal.application.phase3_evidence_core import (
    Phase3MatrixKind,
    Phase3MatrixResult,
    Phase3SignedAcceptanceEvidenceResult,
    Phase3SignedAcceptanceMatrixResult,
)
from foliaseal.application.phase3_evidence_core import (
    load_capture_json as core_load_capture_json,
)
from foliaseal.application.phase3_evidence_core import (
    matrix_exception_row as core_matrix_exception_row,
)
from foliaseal.application.phase3_evidence_core import (
    matrix_summary_row as core_matrix_summary_row,
)
from foliaseal.application.phase3_evidence_core import (
    normalize_matrix_result as core_normalize_matrix_result,
)
from foliaseal.application.phase3_evidence_core import (
    render_evidence_markdown as core_render_evidence_markdown,
)
from foliaseal.application.phase3_evidence_core import (
    validate_signed_acceptance_matrix_summary as core_validate_signed_acceptance_matrix_summary,
)
from foliaseal.application.phase3_evidence_ports import (
    AssetGeneratorPort,
    CaptureContractEvaluatorPort,
    CaptureLoaderPort,
    CaptureResultPort,
    CaptureRunnerPort,
    MatrixRunnerPort,
    MatrixRuntimeContextPort,
    TextWriterPort,
)
from foliaseal.application.qa_evidence_contract import EvidenceContractEvaluation

if TYPE_CHECKING:
    from foliaseal.application.phase3_evidence_orchestrator import Phase3EvidenceSession
    from foliaseal.application.qa_signed_acceptance_generation import (
        GeneratedSignedAcceptanceAssets,
    )

HarnessCaptureRunner = CaptureRunnerPort
MatrixRunner = MatrixRunnerPort
AssetGenerator = AssetGeneratorPort
CaptureContractEvaluator = CaptureContractEvaluatorPort
TextWriter = TextWriterPort
MatrixRuntimeContextFactory = MatrixRuntimeContextPort
CaptureLoader = CaptureLoaderPort


@dataclass(frozen=True)
class Phase3HarnessCaptureRequest:
    pdf_path: str
    certificate_path: str
    passphrase: str
    summary_json_path: str | None
    checklist_results_path: str
    checklist_template_path: str
    artifacts_dir: str | None = None


@dataclass(frozen=True)
class Phase3MatrixRequest:
    pdf_path: str
    certificate_path: str
    passphrase: str
    scenario_manifest_path: str
    artifacts_dir: str


@dataclass(frozen=True)
class Phase3SignedAcceptanceEvidenceRequest:
    artifacts_root: str | Path = "."
    summary_markdown_path: str | Path | None = None
    passphrase: str = ""
    suppress_known_runtime_chatter: bool = True
    required_manifests: tuple[str, ...] = ()
    default_summary_relative_path: str = "artifacts/phase3_signed_acceptance_evidence_summary.md"


@dataclass(frozen=True)
class Phase3HarnessValidationRequest:
    summary_json_path: str | Path


class Phase3EvidenceService:
    def __init__(
        self,
        *,
        harness_runner: HarnessCaptureRunner,
        preview_matrix_runner: MatrixRunner,
        signed_acceptance_matrix_runner: MatrixRunner,
        asset_generator: AssetGenerator,
        capture_contract_evaluator: CaptureContractEvaluator,
        text_writer: TextWriter,
        matrix_runtime_context_factory: MatrixRuntimeContextFactory | None = None,
        capture_loader: CaptureLoader | None = None,
    ) -> None:
        self._harness_runner = harness_runner
        self._preview_matrix_runner = preview_matrix_runner
        self._signed_acceptance_matrix_runner = signed_acceptance_matrix_runner
        self._asset_generator = asset_generator
        self._capture_contract_evaluator = capture_contract_evaluator
        self._text_writer = text_writer
        self._matrix_runtime_context_factory = matrix_runtime_context_factory or (
            lambda _name: nullcontext()
        )
        self._capture_loader = capture_loader or core_load_capture_json

    def for_pdf(
        self,
        pdf_path: str | Path,
        *,
        certificate_path: str,
        passphrase: str,
        artifacts_dir: str = "artifacts/phase3",
    ) -> Phase3EvidenceSession:
        """Return a reusable session bound to one PDF and its credentials."""

        from foliaseal.application.phase3_evidence_orchestrator import orchestrator_for_service

        return orchestrator_for_service(self).for_pdf(
            pdf_path,
            certificate_path=certificate_path,
            passphrase=passphrase,
            artifacts_dir=artifacts_dir,
        )

    def capture_harness(self, request: Phase3HarnessCaptureRequest) -> CaptureResultPort:
        return self._harness_runner(request)

    def preview_matrix_result(self, request: Phase3MatrixRequest) -> Phase3MatrixResult:
        """Run and normalize a preview matrix through the injected runner."""

        return core_normalize_matrix_result(
            kind=Phase3MatrixKind.PREVIEW,
            summary=self._preview_matrix_runner(request),
        )

    def signed_acceptance_matrix_result(
        self,
        request: Phase3MatrixRequest,
    ) -> Phase3MatrixResult:
        """Return a typed signed-acceptance result over the stable summary contract."""

        return core_normalize_matrix_result(
            kind=Phase3MatrixKind.SIGNED_ACCEPTANCE,
            summary=self._signed_acceptance_matrix_runner(request),
        )

    def validate_harness_capture(
        self,
        request: Phase3HarnessValidationRequest,
    ) -> EvidenceContractEvaluation:
        payload = self._capture_loader(Path(request.summary_json_path))
        return self._capture_contract_evaluator(payload)

    def run_signed_acceptance_evidence(
        self,
        request: Phase3SignedAcceptanceEvidenceRequest,
    ) -> Phase3SignedAcceptanceEvidenceResult:
        root = Path(request.artifacts_root)
        summary_path = (
            Path(request.summary_markdown_path)
            if request.summary_markdown_path is not None
            else root / request.default_summary_relative_path
        )
        assets = self._asset_generator(root=root)

        matrix_results: list[Phase3SignedAcceptanceMatrixResult] = []
        all_errors: list[str] = []
        for spec in _matrix_specs(root, assets):
            chatter_context = (
                self._matrix_runtime_context_factory(spec["name"])
                if request.suppress_known_runtime_chatter
                else nullcontext()
            )
            try:
                with chatter_context:
                    summary = self._signed_acceptance_matrix_runner(
                        Phase3MatrixRequest(
                            pdf_path=str(assets.fixture_pdf),
                            certificate_path=str(assets.identity_p12),
                            passphrase=request.passphrase,
                            scenario_manifest_path=spec["manifest_path"],
                            artifacts_dir=spec["artifacts_dir"],
                        )
                    )
            except Exception as exc:
                row = core_matrix_exception_row(spec["name"], spec["artifacts_dir"], exc)
                all_errors.extend(row.errors)
                matrix_results.append(row)
                continue

            errors = core_validate_signed_acceptance_matrix_summary(
                name=spec["name"],
                summary=summary,
            )
            all_errors.extend(errors)
            matrix_results.append(core_matrix_summary_row(spec["name"], summary, errors))

        evidence = Phase3SignedAcceptanceEvidenceResult(
            passed=not all_errors,
            summary_markdown_path=str(summary_path),
            generated_assets={key: str(value) for key, value in assets.as_dict().items()},
            matrix_results=tuple(matrix_results),
            errors=tuple(all_errors),
            required_manifests=request.required_manifests,
        )
        self._text_writer(summary_path, core_render_evidence_markdown(evidence))
        if all_errors:
            raise RuntimeError(
                "Signed acceptance evidence failed:\n"
                + "\n".join(f"- {error}" for error in all_errors)
            )
        return evidence


def _matrix_specs(
    root: Path,
    assets: GeneratedSignedAcceptanceAssets,
) -> tuple[dict[str, str], ...]:
    base_dir = root / "artifacts" / "signed_acceptance_evidence"
    return (
        {
            "name": "signed_acceptance_matrix",
            "manifest_path": str(assets.signed_acceptance_manifest),
            "artifacts_dir": str(base_dir / "signed_acceptance_matrix"),
        },
        {
            "name": "signed_preview_parity_matrix",
            "manifest_path": str(assets.signed_preview_parity_manifest),
            "artifacts_dir": str(base_dir / "signed_preview_parity_matrix"),
        },
        {
            "name": "signed_fit_rejection_matrix",
            "manifest_path": str(assets.signed_fit_rejection_manifest),
            "artifacts_dir": str(base_dir / "signed_fit_rejection_matrix"),
        },
    )
