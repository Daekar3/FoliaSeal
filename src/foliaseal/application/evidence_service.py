"""Application service for evidence workflows."""

from __future__ import annotations

from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from foliaseal.application.evidence_core import (
    EvidenceMatrixKind,
    EvidenceMatrixResult,
    SignedAcceptanceEvidenceResult,
    SignedAcceptanceMatrixResult,
)
from foliaseal.application.evidence_core import (
    load_capture_json as core_load_capture_json,
)
from foliaseal.application.evidence_core import (
    matrix_exception_row as core_matrix_exception_row,
)
from foliaseal.application.evidence_core import (
    matrix_summary_row as core_matrix_summary_row,
)
from foliaseal.application.evidence_core import (
    normalize_matrix_result as core_normalize_matrix_result,
)
from foliaseal.application.evidence_core import (
    render_evidence_markdown as core_render_evidence_markdown,
)
from foliaseal.application.evidence_core import (
    validate_signed_acceptance_matrix_summary as core_validate_signed_acceptance_matrix_summary,
)
from foliaseal.application.evidence_ports import (
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
    from foliaseal.application.evidence_program import EvidenceSession
    from foliaseal.application.qa_signed_acceptance_generation import (
        GeneratedSignedAcceptanceAssets,
    )

@dataclass(frozen=True)
class EvidenceCaptureRequest:
    pdf_path: str
    certificate_path: str
    passphrase: str
    summary_json_path: str | None
    checklist_results_path: str
    checklist_template_path: str
    artifacts_dir: str | None = None


@dataclass(frozen=True)
class EvidenceMatrixRequest:
    pdf_path: str
    certificate_path: str
    passphrase: str
    scenario_manifest_path: str
    artifacts_dir: str


@dataclass(frozen=True)
class SignedAcceptanceEvidenceRequest:
    artifacts_root: str | Path = "."
    summary_markdown_path: str | Path | None = None
    passphrase: str = ""
    suppress_known_runtime_chatter: bool = True
    required_manifests: tuple[str, ...] = ()
    default_summary_relative_path: str = "artifacts/signed_acceptance_evidence_summary.md"


@dataclass(frozen=True)
class EvidenceServiceValidationRequest:
    summary_json_path: str | Path


class EvidenceService:
    def __init__(
        self,
        *,
        harness_runner: CaptureRunnerPort,
        preview_matrix_runner: MatrixRunnerPort,
        signed_acceptance_matrix_runner: MatrixRunnerPort,
        asset_generator: AssetGeneratorPort,
        capture_contract_evaluator: CaptureContractEvaluatorPort,
        text_writer: TextWriterPort,
        matrix_runtime_context_factory: MatrixRuntimeContextPort | None = None,
        capture_loader: CaptureLoaderPort | None = None,
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
        artifacts_dir: str = "artifacts/acceptance",
    ) -> EvidenceSession:
        """Return a reusable session bound to one PDF and its credentials."""

        from foliaseal.application.evidence_program import program_for_service

        return program_for_service(self).for_pdf(
            pdf_path,
            certificate_path=certificate_path,
            passphrase=passphrase,
            artifacts_dir=artifacts_dir,
        )

    def capture(self, request: EvidenceCaptureRequest) -> CaptureResultPort:
        return self._harness_runner(request)

    def preview_matrix(self, request: EvidenceMatrixRequest) -> EvidenceMatrixResult:
        """Run and normalize a preview matrix through the injected runner."""

        return core_normalize_matrix_result(
            kind=EvidenceMatrixKind.PREVIEW,
            summary=self._preview_matrix_runner(request),
        )

    def signed_acceptance_matrix(
        self,
        request: EvidenceMatrixRequest,
    ) -> EvidenceMatrixResult:
        """Return a typed signed-acceptance result over the stable summary contract."""

        return core_normalize_matrix_result(
            kind=EvidenceMatrixKind.SIGNED_ACCEPTANCE,
            summary=self._signed_acceptance_matrix_runner(request),
        )

    def validate(
        self,
        request: EvidenceServiceValidationRequest,
    ) -> EvidenceContractEvaluation:
        payload = self._capture_loader(Path(request.summary_json_path))
        return self._capture_contract_evaluator(payload)

    def signed_acceptance_evidence(
        self,
        request: SignedAcceptanceEvidenceRequest,
    ) -> SignedAcceptanceEvidenceResult:
        root = Path(request.artifacts_root)
        summary_path = (
            Path(request.summary_markdown_path)
            if request.summary_markdown_path is not None
            else root / request.default_summary_relative_path
        )
        assets = self._asset_generator(root=root)

        matrix_results: list[SignedAcceptanceMatrixResult] = []
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
                        EvidenceMatrixRequest(
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

        evidence = SignedAcceptanceEvidenceResult(
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
    # The mixed signed_acceptance manifest remains available to the standalone matrix command,
    # but strict release evidence must keep successful parity and intentional rejection coverage
    # as independent gates.  A mixed manifest can contain expected rejections and therefore must
    # not be allowed to turn the strict parity/rejection summary red.
    return (
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
