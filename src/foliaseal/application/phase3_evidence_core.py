"""Qt-free Phase 3 evidence result models and decision logic."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from foliaseal.application.qa_evidence_contract import EvidenceContractEvaluation

CRITICAL_ZERO_COUNTERS = (
    "expected_outcome_mismatch_count",
    "cryptographic_validation_failure_count",
    "preview_output_comparison_failure_count",
    "annotation_rect_mismatch_count",
)


class Phase3MatrixKind(StrEnum):
    """Stable names for the two batch evidence matrix modes."""

    PREVIEW = "preview"
    SIGNED_ACCEPTANCE = "signed_acceptance"


@dataclass(frozen=True)
class Phase3MatrixResult:
    """Typed matrix result over the stable serialized summary contract."""

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
            "cryptographic_validation_failure_count": self.cryptographic_validation_failure_count,
            "preview_output_comparison_failure_count": self.preview_output_comparison_failure_count,
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


def normalize_matrix_result(
    *, kind: Phase3MatrixKind, summary: Mapping[str, Any]
) -> Phase3MatrixResult:
    summary_mapping = dict(summary)
    artifacts_dir = str(summary_mapping.get("artifacts_dir", ""))
    summary_json_path = str(
        summary_mapping.get("summary_json_path") or Path(artifacts_dir) / "summary.json"
    )
    if kind is Phase3MatrixKind.PREVIEW:
        errors = string_values(summary_mapping.get("errors"))
        passed = summary_mapping.get("error_scenario_count", 0) == 0 and not errors
        successful_run_count = optional_int(summary_mapping.get("successful_scenario_count"))
    else:
        errors = string_values(summary_mapping.get("acceptance_expectation_errors"))
        errors += nonzero_counter_errors(summary_mapping, CRITICAL_ZERO_COUNTERS)
        errors += nonzero_counter_errors(summary_mapping, ("error_scenario_count",))
        passed = summary_mapping.get("acceptance_expectations_passed") is True and not errors
        successful_run_count = optional_int(summary_mapping.get("successful_signing_run_count"))
    return Phase3MatrixResult(
        kind=kind,
        summary=summary_mapping,
        passed=passed,
        artifacts_dir=artifacts_dir,
        summary_json_path=summary_json_path,
        scenario_count=optional_int(summary_mapping.get("scenario_count")),
        successful_run_count=successful_run_count,
        errors=errors,
        warnings=string_values(summary_mapping.get("warnings")),
    )


def validate_signed_acceptance_matrix_summary(
    *, name: str, summary: Mapping[str, Any]
) -> list[str]:
    errors: list[str] = []
    if summary.get("acceptance_expectations_passed") is not True:
        errors.append(f"{name}: acceptance expectations did not pass.")
        expectation_errors = summary.get("acceptance_expectation_errors")
        if isinstance(expectation_errors, list):
            errors.extend(
                f"{name}: {error}"
                for error in expectation_errors
                if isinstance(error, str) and error
            )
    for key in CRITICAL_ZERO_COUNTERS + ("error_scenario_count",):
        try:
            observed = summary_int(summary, key)
        except ValueError as exc:
            errors.append(f"{name}: {exc}")
            continue
        if observed != 0:
            errors.append(f"{name}: expected {key}=0, observed {observed}.")
    return errors


def matrix_summary_row(
    name: str, summary: Mapping[str, Any], errors: list[str]
) -> Phase3SignedAcceptanceMatrixResult:
    counters = Phase3SignedAcceptanceMatrixCounters(
        scenario_count=summary_or_none(summary, "scenario_count"),
        successful_signing_run_count=summary_or_none(summary, "successful_signing_run_count"),
        expected_outcome_mismatch_count=summary_or_none(summary, "expected_outcome_mismatch_count"),
        cryptographic_validation_failure_count=summary_or_none(
            summary, "cryptographic_validation_failure_count"
        ),
        preview_output_comparison_failure_count=summary_or_none(
            summary, "preview_output_comparison_failure_count"
        ),
        annotation_rect_mismatch_count=summary_or_none(summary, "annotation_rect_mismatch_count"),
        matched_expected_intentional_rejection_count=summary_or_none(
            summary, "matched_expected_intentional_rejection_count"
        ),
    )
    artifacts_dir = str(summary.get("artifacts_dir", ""))
    summary_json_path = str(
        summary.get("summary_json_path")
        or (Path(artifacts_dir) / "summary.json" if artifacts_dir else "")
    )
    return Phase3SignedAcceptanceMatrixResult(
        name=name,
        passed=not errors,
        errors=tuple(errors),
        artifacts_dir=artifacts_dir,
        summary_json_path=summary_json_path,
        counters=counters,
    )


def matrix_exception_row(
    name: str, artifacts_dir: str, exc: Exception
) -> Phase3SignedAcceptanceMatrixResult:
    return Phase3SignedAcceptanceMatrixResult(
        name=name,
        passed=False,
        errors=(f"{name}: matrix runner failed before returning a summary: {exc}",),
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


def render_evidence_markdown(evidence: Phase3SignedAcceptanceEvidenceResult) -> str:
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
                f"- Successful signings: {counters.successful_signing_run_count}",
                "- Matched intentional rejections: "
                f"{counters.matched_expected_intentional_rejection_count}",
                f"- Expected outcome mismatches: {counters.expected_outcome_mismatch_count}",
                "- Cryptographic validation failures: "
                f"{counters.cryptographic_validation_failure_count}",
                "- Preview/output comparison failures: "
                f"{counters.preview_output_comparison_failure_count}",
                f"- Annotation rect mismatches: {counters.annotation_rect_mismatch_count}",
                f"- Artifacts directory: {result.artifacts_dir}",
                f"- Summary JSON: {result.summary_json_path}",
                "",
            ]
        )
        lines.extend(f"- Error: {error}" for error in result.errors)
        if result.errors:
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def load_capture_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def string_values(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(item for item in value if isinstance(item, str) and item)


def optional_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def nonzero_counter_errors(
    summary: Mapping[str, Any], counters: tuple[str, ...]
) -> tuple[str, ...]:
    return tuple(
        f"{key}={value}"
        for key in counters
        if isinstance(value := summary.get(key), int) and value != 0
    )


def summary_int(summary: Mapping[str, Any], key: str) -> int:
    value = summary.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Matrix summary missing integer counter {key!r}.")
    return value


def summary_or_none(summary: Mapping[str, Any], key: str) -> int | None:
    value = summary.get(key)
    return None if value is None or isinstance(value, bool) or not isinstance(value, int) else value


def evaluate_capture_contract(
    payload: Mapping[str, Any],
    evaluator: Any,
) -> EvidenceContractEvaluation:
    """Keep the contract evaluator injectable while isolating payload loading."""

    return evaluator(dict(payload))
