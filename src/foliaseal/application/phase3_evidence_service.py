"""Service boundary for Phase 3 evidence workflows."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from foliaseal.application.qa_evidence_contract import EvidenceContractEvaluation
from foliaseal.application.qa_signed_acceptance_generation import (
    GeneratedSignedAcceptanceAssets,
)

CRITICAL_ZERO_COUNTERS = (
    "expected_outcome_mismatch_count",
    "cryptographic_validation_failure_count",
    "preview_output_comparison_failure_count",
    "annotation_rect_mismatch_count",
)

HarnessCaptureRunner = Callable[["Phase3HarnessCaptureRequest"], Any]
MatrixRunner = Callable[["Phase3MatrixRequest"], dict[str, Any]]
AssetGenerator = Callable[..., GeneratedSignedAcceptanceAssets]
CaptureContractEvaluator = Callable[[dict[str, Any]], EvidenceContractEvaluation]
TextWriter = Callable[[Path, str], None]
MatrixRuntimeContextFactory = Callable[[str], AbstractContextManager[None]]
CaptureLoader = Callable[[Path], dict[str, Any]]


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


class Phase3MatrixKind(StrEnum):
    """Stable names for the two batch evidence matrix modes."""

    PREVIEW = "preview"
    SIGNED_ACCEPTANCE = "signed_acceptance"


@dataclass(frozen=True)
class Phase3MatrixResult:
    """Typed view over an existing Phase 3 matrix summary mapping."""

    kind: Phase3MatrixKind
    summary: Mapping[str, Any]
    passed: bool
    artifacts_dir: str
    summary_json_path: str
    scenario_count: int | None
    successful_run_count: int | None
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class Phase3SignedAcceptanceEvidenceRequest:
    artifacts_root: str | Path = "."
    summary_markdown_path: str | Path | None = None
    passphrase: str = ""
    suppress_known_runtime_chatter: bool = True
    required_manifests: tuple[str, ...] = ()
    default_summary_relative_path: str = (
        "artifacts/phase3_signed_acceptance_evidence_summary.md"
    )


@dataclass(frozen=True)
class Phase3HarnessValidationRequest:
    summary_json_path: str | Path


@dataclass(frozen=True)
class Phase3SignedAcceptanceMatrixCounters:
    scenario_count: int | None
    successful_signing_run_count: int | None
    expected_outcome_mismatch_count: int | None
    cryptographic_validation_failure_count: int | None
    preview_output_comparison_failure_count: int | None
    annotation_rect_mismatch_count: int | None
    matched_expected_intentional_rejection_count: int | None

    def as_dict(self) -> dict[str, int | None]:
        return {
            "scenario_count": self.scenario_count,
            "successful_signing_run_count": self.successful_signing_run_count,
            "expected_outcome_mismatch_count": self.expected_outcome_mismatch_count,
            "cryptographic_validation_failure_count": (
                self.cryptographic_validation_failure_count
            ),
            "preview_output_comparison_failure_count": (
                self.preview_output_comparison_failure_count
            ),
            "annotation_rect_mismatch_count": self.annotation_rect_mismatch_count,
            "matched_expected_intentional_rejection_count": (
                self.matched_expected_intentional_rejection_count
            ),
        }


@dataclass(frozen=True)
class Phase3SignedAcceptanceMatrixResult:
    name: str
    passed: bool
    errors: tuple[str, ...]
    artifacts_dir: str
    summary_json_path: str
    counters: Phase3SignedAcceptanceMatrixCounters

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "passed": self.passed,
            "errors": list(self.errors),
            "artifacts_dir": self.artifacts_dir,
            "summary_json_path": self.summary_json_path,
            "counters": self.counters.as_dict(),
        }


@dataclass(frozen=True)
class Phase3SignedAcceptanceEvidenceResult:
    passed: bool
    summary_markdown_path: str
    generated_assets: dict[str, str]
    matrix_results: tuple[Phase3SignedAcceptanceMatrixResult, ...]
    errors: tuple[str, ...]
    required_manifests: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "passed": self.passed,
            "summary_markdown_path": self.summary_markdown_path,
            "generated_assets": dict(self.generated_assets),
            "matrix_results": [result.as_dict() for result in self.matrix_results],
            "errors": list(self.errors),
            "required_manifests": list(self.required_manifests),
        }


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
        self._matrix_runtime_context_factory = (
            matrix_runtime_context_factory or (lambda _name: nullcontext())
        )
        self._capture_loader = capture_loader or _load_capture_json

    def capture_harness(self, request: Phase3HarnessCaptureRequest) -> Any:
        return self._harness_runner(request)

    def run_preview_matrix(self, request: Phase3MatrixRequest) -> dict[str, Any]:
        return self._preview_matrix_runner(request)

    def run_signed_acceptance_matrix(
        self,
        request: Phase3MatrixRequest,
    ) -> dict[str, Any]:
        return self._signed_acceptance_matrix_runner(request)

    def preview_matrix_result(self, request: Phase3MatrixRequest) -> Phase3MatrixResult:
        """Return a typed result while preserving the legacy raw summary method."""

        return _normalize_matrix_result(
            kind=Phase3MatrixKind.PREVIEW,
            summary=self.run_preview_matrix(request),
        )

    def signed_acceptance_matrix_result(
        self,
        request: Phase3MatrixRequest,
    ) -> Phase3MatrixResult:
        """Return a typed signed-acceptance result over the stable summary contract."""

        return _normalize_matrix_result(
            kind=Phase3MatrixKind.SIGNED_ACCEPTANCE,
            summary=self.run_signed_acceptance_matrix(request),
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
                row = _matrix_exception_row(spec["name"], spec["artifacts_dir"], exc)
                all_errors.extend(row.errors)
                matrix_results.append(row)
                continue

            errors = validate_signed_acceptance_matrix_summary(
                name=spec["name"],
                summary=summary,
            )
            all_errors.extend(errors)
            matrix_results.append(_matrix_summary_row(spec["name"], summary, errors))

        evidence = Phase3SignedAcceptanceEvidenceResult(
            passed=not all_errors,
            summary_markdown_path=str(summary_path),
            generated_assets={key: str(value) for key, value in assets.as_dict().items()},
            matrix_results=tuple(matrix_results),
            errors=tuple(all_errors),
            required_manifests=request.required_manifests,
        )
        self._text_writer(summary_path, _render_evidence_markdown(evidence))
        if all_errors:
            raise RuntimeError(
                "Signed acceptance evidence failed:\n"
                + "\n".join(f"- {error}" for error in all_errors)
            )
        return evidence


def _normalize_matrix_result(
    *,
    kind: Phase3MatrixKind,
    summary: Mapping[str, Any],
) -> Phase3MatrixResult:
    """Normalize one runner summary without changing its serialized shape."""

    summary_mapping = dict(summary)
    artifacts_dir = str(summary_mapping.get("artifacts_dir", ""))
    summary_json_path = str(
        summary_mapping.get("summary_json_path")
        or Path(artifacts_dir) / "summary.json"
    )
    if kind is Phase3MatrixKind.PREVIEW:
        errors = tuple(_string_values(summary_mapping.get("errors")))
        passed = summary_mapping.get("error_scenario_count", 0) == 0 and not errors
        successful_run_count = _optional_int(
            summary_mapping.get("successful_scenario_count")
        )
    else:
        errors = tuple(_string_values(summary_mapping.get("acceptance_expectation_errors")))
        errors += tuple(
            _nonzero_counter_errors(summary_mapping, CRITICAL_ZERO_COUNTERS)
        )
        passed = summary_mapping.get("acceptance_expectations_passed") is True and not errors
        successful_run_count = _optional_int(
            summary_mapping.get("successful_signing_run_count")
        )
    return Phase3MatrixResult(
        kind=kind,
        summary=summary_mapping,
        passed=passed,
        artifacts_dir=artifacts_dir,
        summary_json_path=summary_json_path,
        scenario_count=_optional_int(summary_mapping.get("scenario_count")),
        successful_run_count=successful_run_count,
        errors=errors,
        warnings=tuple(_string_values(summary_mapping.get("warnings"))),
    )


def _string_values(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(item for item in value if isinstance(item, str) and item)


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _nonzero_counter_errors(
    summary: Mapping[str, Any],
    counters: tuple[str, ...],
) -> tuple[str, ...]:
    errors: list[str] = []
    for key in counters:
        value = summary.get(key)
        if isinstance(value, int) and value != 0:
            errors.append(f"{key}={value}")
    return tuple(errors)


def validate_signed_acceptance_matrix_summary(
    *,
    name: str,
    summary: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    if summary.get("acceptance_expectations_passed") is not True:
        errors.append(f"{name}: acceptance expectations did not pass.")
        expectation_errors = summary.get("acceptance_expectation_errors")
        if isinstance(expectation_errors, list):
            for error in expectation_errors:
                if isinstance(error, str) and error:
                    errors.append(f"{name}: {error}")
    for key in CRITICAL_ZERO_COUNTERS:
        try:
            observed = _summary_int(summary, key)
        except ValueError as exc:
            errors.append(f"{name}: {exc}")
            continue
        if observed != 0:
            errors.append(f"{name}: expected {key}=0, observed {observed}.")
    return errors


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


def _summary_int(summary: dict[str, Any], key: str) -> int:
    value = summary.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Matrix summary missing integer counter {key!r}.")
    return value


def _matrix_summary_row(
    name: str,
    summary: dict[str, Any],
    errors: list[str],
) -> Phase3SignedAcceptanceMatrixResult:
    counters = Phase3SignedAcceptanceMatrixCounters(
        scenario_count=_summary_or_none(summary, "scenario_count"),
        successful_signing_run_count=_summary_or_none(
            summary,
            "successful_signing_run_count",
        ),
        expected_outcome_mismatch_count=_summary_or_none(
            summary,
            "expected_outcome_mismatch_count",
        ),
        cryptographic_validation_failure_count=_summary_or_none(
            summary,
            "cryptographic_validation_failure_count",
        ),
        preview_output_comparison_failure_count=_summary_or_none(
            summary,
            "preview_output_comparison_failure_count",
        ),
        annotation_rect_mismatch_count=_summary_or_none(
            summary,
            "annotation_rect_mismatch_count",
        ),
        matched_expected_intentional_rejection_count=_summary_or_none(
            summary,
            "matched_expected_intentional_rejection_count",
        ),
    )
    artifacts_dir = str(summary.get("artifacts_dir", ""))
    return Phase3SignedAcceptanceMatrixResult(
        name=name,
        passed=not errors,
        errors=tuple(errors),
        artifacts_dir=artifacts_dir,
        summary_json_path=(
            str(Path(artifacts_dir) / "summary.json") if artifacts_dir else ""
        ),
        counters=counters,
    )


def _matrix_exception_row(
    name: str,
    artifacts_dir: str,
    exc: Exception,
) -> Phase3SignedAcceptanceMatrixResult:
    return Phase3SignedAcceptanceMatrixResult(
        name=name,
        passed=False,
        errors=(
            f"{name}: matrix runner failed before returning a summary: {exc}",
        ),
        artifacts_dir=artifacts_dir,
        summary_json_path=str(Path(artifacts_dir) / "summary.json") if artifacts_dir else "",
        counters=Phase3SignedAcceptanceMatrixCounters(
            scenario_count=None,
            successful_signing_run_count=None,
            expected_outcome_mismatch_count=None,
            cryptographic_validation_failure_count=None,
            preview_output_comparison_failure_count=None,
            annotation_rect_mismatch_count=None,
            matched_expected_intentional_rejection_count=None,
        ),
    )


def _summary_or_none(summary: dict[str, Any], key: str) -> int | None:
    value = summary.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _render_evidence_markdown(
    evidence: Phase3SignedAcceptanceEvidenceResult,
) -> str:
    lines = [
        "# Phase 3 Signed Acceptance Evidence",
        "",
        f"- Overall result: {'PASS' if evidence.passed else 'FAIL'}",
        f"- Generated fixture PDF: {evidence.generated_assets['fixture_pdf']}",
        f"- Generated identity: {evidence.generated_assets['identity_p12']}",
        f"- Generated stamp image: {evidence.generated_assets['stamp_image']}",
        "",
        "## Matrix Results",
        "",
    ]
    for result in evidence.matrix_results:
        counters = result.counters
        lines.extend(
            [
                f"### {result.name}",
                "",
                f"- Result: {'PASS' if result.passed else 'FAIL'}",
                f"- Scenarios: {counters.scenario_count}",
                (
                    "- Successful signings: "
                    f"{counters.successful_signing_run_count}"
                ),
                (
                    "- Matched intentional rejections: "
                    f"{counters.matched_expected_intentional_rejection_count}"
                ),
                (
                    "- Expected outcome mismatches: "
                    f"{counters.expected_outcome_mismatch_count}"
                ),
                (
                    "- Cryptographic validation failures: "
                    f"{counters.cryptographic_validation_failure_count}"
                ),
                (
                    "- Preview/output comparison failures: "
                    f"{counters.preview_output_comparison_failure_count}"
                ),
                (
                    "- Annotation rect mismatches: "
                    f"{counters.annotation_rect_mismatch_count}"
                ),
                f"- Artifacts directory: {result.artifacts_dir}",
                f"- Summary JSON: {result.summary_json_path}",
                "",
            ]
        )
        for error in result.errors:
            lines.append(f"- Error: {error}")
        if result.errors:
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _load_capture_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
