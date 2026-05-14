"""One-command signed acceptance evidence orchestration."""

from __future__ import annotations

import logging
import sys
from collections.abc import Callable
from contextlib import contextmanager, nullcontext
from pathlib import Path
from typing import Any

from foliaseal.application.qa_signed_acceptance_assets import (
    SIGNED_ACCEPTANCE_SCENARIO_MANIFEST,
    SIGNED_FIT_REJECTION_SCENARIO_MANIFEST,
    SIGNED_PREVIEW_PARITY_SCENARIO_MANIFEST,
)
from foliaseal.application.qa_signed_acceptance_generation import (
    SIGNED_ACCEPTANCE_IDENTITY_PASSPHRASE,
    GeneratedSignedAcceptanceAssets,
    generate_signed_acceptance_assets,
)
from foliaseal.presentation.qt.phase3_harness import run_phase3_signed_acceptance_matrix

DEFAULT_SIGNED_ACCEPTANCE_EVIDENCE_SUMMARY_PATH = (
    "artifacts/phase3_signed_acceptance_evidence_summary.md"
)

CRITICAL_ZERO_COUNTERS = (
    "expected_outcome_mismatch_count",
    "cryptographic_validation_failure_count",
    "preview_output_comparison_failure_count",
    "annotation_rect_mismatch_count",
)

MatrixRunner = Callable[..., dict[str, Any]]
AssetGenerator = Callable[..., GeneratedSignedAcceptanceAssets]

_PYHANKO_DUMMY_TSA_LOGGER = "pyhanko.sign.validation.generic_cms"
_PYHANKO_LAYOUT_LOGGER = "pyhanko.pdf_utils.layout"
_DUMMY_TSA_SUBJECT_FRAGMENT = (
    "Common Name: FoliaSeal TSA, Organization: FoliaSeal, Country: US"
)
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
            and
            record.name == _PYHANKO_LAYOUT_LOGGER
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


def _default_summary_path(root: Path) -> Path:
    return root / DEFAULT_SIGNED_ACCEPTANCE_EVIDENCE_SUMMARY_PATH


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


def _matrix_summary_row(name: str, summary: dict[str, Any], errors: list[str]) -> dict[str, Any]:
    counters = {
        "scenario_count": summary.get("scenario_count"),
        "successful_signing_run_count": summary.get("successful_signing_run_count"),
        "expected_outcome_mismatch_count": summary.get("expected_outcome_mismatch_count"),
        "cryptographic_validation_failure_count": summary.get(
            "cryptographic_validation_failure_count"
        ),
        "preview_output_comparison_failure_count": summary.get(
            "preview_output_comparison_failure_count"
        ),
        "annotation_rect_mismatch_count": summary.get("annotation_rect_mismatch_count"),
        "matched_expected_intentional_rejection_count": summary.get(
            "matched_expected_intentional_rejection_count"
        ),
    }
    artifacts_dir = str(summary.get("artifacts_dir", ""))
    return {
        "name": name,
        "passed": not errors,
        "errors": errors,
        "artifacts_dir": artifacts_dir,
        "summary_json_path": str(Path(artifacts_dir) / "summary.json") if artifacts_dir else "",
        "counters": counters,
    }


def _matrix_exception_row(name: str, artifacts_dir: str, exc: Exception) -> dict[str, Any]:
    return {
        "name": name,
        "passed": False,
        "errors": [f"{name}: matrix runner failed before returning a summary: {exc}"],
        "artifacts_dir": artifacts_dir,
        "summary_json_path": str(Path(artifacts_dir) / "summary.json") if artifacts_dir else "",
        "counters": {
            "scenario_count": None,
            "successful_signing_run_count": None,
            "expected_outcome_mismatch_count": None,
            "cryptographic_validation_failure_count": None,
            "preview_output_comparison_failure_count": None,
            "annotation_rect_mismatch_count": None,
            "matched_expected_intentional_rejection_count": None,
        },
    }


def _write_evidence_markdown(path: Path, evidence: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 3 Signed Acceptance Evidence",
        "",
        f"- Overall result: {'PASS' if evidence['passed'] else 'FAIL'}",
        f"- Generated fixture PDF: {evidence['generated_assets']['fixture_pdf']}",
        f"- Generated identity: {evidence['generated_assets']['identity_p12']}",
        f"- Generated stamp image: {evidence['generated_assets']['stamp_image']}",
        "",
        "## Matrix Results",
        "",
    ]
    for result in evidence["matrix_results"]:
        counters = result["counters"]
        lines.extend(
            [
                f"### {result['name']}",
                "",
                f"- Result: {'PASS' if result['passed'] else 'FAIL'}",
                f"- Scenarios: {counters['scenario_count']}",
                f"- Successful signings: {counters['successful_signing_run_count']}",
                (
                    "- Matched intentional rejections: "
                    f"{counters['matched_expected_intentional_rejection_count']}"
                ),
                f"- Expected outcome mismatches: {counters['expected_outcome_mismatch_count']}",
                (
                    "- Cryptographic validation failures: "
                    f"{counters['cryptographic_validation_failure_count']}"
                ),
                (
                    "- Preview/output comparison failures: "
                    f"{counters['preview_output_comparison_failure_count']}"
                ),
                f"- Annotation rect mismatches: {counters['annotation_rect_mismatch_count']}",
                f"- Artifacts directory: {result['artifacts_dir']}",
                f"- Summary JSON: {result['summary_json_path']}",
                "",
            ]
        )
        for error in result["errors"]:
            lines.append(f"- Error: {error}")
        if result["errors"]:
            lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def run_signed_acceptance_evidence(
    *,
    artifacts_root: str | Path = ".",
    summary_markdown_path: str | Path | None = None,
    suppress_known_runtime_chatter: bool = True,
    asset_generator: AssetGenerator = generate_signed_acceptance_assets,
    matrix_runner: MatrixRunner = run_phase3_signed_acceptance_matrix,
) -> dict[str, Any]:
    root = Path(artifacts_root)
    summary_path = (
        Path(summary_markdown_path)
        if summary_markdown_path is not None
        else _default_summary_path(root)
    )
    assets = asset_generator(root=root)
    passphrase = SIGNED_ACCEPTANCE_IDENTITY_PASSPHRASE.decode("utf-8")

    matrix_results: list[dict[str, Any]] = []
    all_errors: list[str] = []
    for spec in _matrix_specs(root, assets):
        chatter_context = (
            _suppress_known_signed_evidence_runtime_chatter(
                suppress_layout_warnings=spec["name"] == "signed_fit_rejection_matrix"
            )
            if suppress_known_runtime_chatter
            else nullcontext()
        )
        try:
            with chatter_context:
                summary = matrix_runner(
                    pdf_path=str(assets.fixture_pdf),
                    certificate_path=str(assets.identity_p12),
                    passphrase=passphrase,
                    scenario_manifest_path=spec["manifest_path"],
                    artifacts_dir=spec["artifacts_dir"],
                )
        except Exception as exc:
            row = _matrix_exception_row(spec["name"], spec["artifacts_dir"], exc)
            errors = list(row["errors"])
            all_errors.extend(errors)
            matrix_results.append(row)
            continue
        errors = validate_signed_acceptance_matrix_summary(
            name=spec["name"],
            summary=summary,
        )
        all_errors.extend(errors)
        matrix_results.append(_matrix_summary_row(spec["name"], summary, errors))

    evidence = {
        "passed": not all_errors,
        "summary_markdown_path": str(summary_path),
        "generated_assets": {key: str(value) for key, value in assets.as_dict().items()},
        "matrix_results": matrix_results,
        "errors": all_errors,
        "required_manifests": [
            SIGNED_ACCEPTANCE_SCENARIO_MANIFEST,
            SIGNED_PREVIEW_PARITY_SCENARIO_MANIFEST,
            SIGNED_FIT_REJECTION_SCENARIO_MANIFEST,
        ],
    }
    _write_evidence_markdown(summary_path, evidence)
    if all_errors:
        raise RuntimeError(
            "Signed acceptance evidence failed:\n" + "\n".join(f"- {e}" for e in all_errors)
        )
    return evidence
