"""CLI entry points for development checks and evidence helpers."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from foliaseal.application.performance_timing import ViewerPerformanceTracker
from foliaseal.application.phase2_evidence import (
    QtRuntimeReadinessSnapshot,
    RuntimeEnvironmentSnapshot,
    RuntimeValidationSnapshot,
    build_phase2_timing_evidence,
    parse_checklist_markdown,
)
from foliaseal.application.phase3_evidence_service import (
    Phase3HarnessCaptureRequest,
    Phase3HarnessValidationRequest,
    Phase3MatrixRequest,
    Phase3SignedAcceptanceEvidenceRequest,
)
from foliaseal.application.qa_signed_acceptance_generation import (
    SIGNED_ACCEPTANCE_IDENTITY_PASSPHRASE,
)
from foliaseal.application.runtime_metrics import (
    RuntimeFootprintSnapshot,
    collect_runtime_footprint_snapshot,
    measure_startup_latency_ms,
)
from foliaseal.presentation.qt.app_frame import launch_qt_app_frame
from foliaseal.presentation.qt.phase2_harness import (
    DEFAULT_CHECKLIST_RESULTS_PATH,
    DEFAULT_CHECKLIST_TEMPLATE_PATH,
    run_phase2_viewer_harness,
)
from foliaseal.presentation.qt.phase3_harness import (
    DEFAULT_PHASE3_CHECKLIST_RESULTS_PATH,
    DEFAULT_PHASE3_CHECKLIST_TEMPLATE_PATH,
)
from foliaseal.presentation.qt.phase3_signed_acceptance_evidence import (
    DEFAULT_SIGNED_ACCEPTANCE_EVIDENCE_SUMMARY_PATH,
    build_default_phase3_evidence_service,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="foliaseal")
    subparsers = parser.add_subparsers(dest="command")

    evidence = subparsers.add_parser(
        "phase2-evidence",
        help="Render a markdown evidence snippet for Phase 2 timing sign-off.",
    )
    evidence.add_argument(
        "--first-render-ms",
        type=float,
        default=None,
        help="First render latency in milliseconds.",
    )
    evidence.add_argument(
        "--navigation-ms",
        dest="navigation_ms",
        action="append",
        type=float,
        default=[],
        help="Navigation latency sample in milliseconds. Repeat for multiple samples.",
    )
    evidence.add_argument(
        "--minimum-navigation-samples",
        type=int,
        default=10,
        help="Minimum sample threshold used for quick-check status.",
    )
    evidence.add_argument(
        "--startup-ms",
        type=float,
        default=None,
        help="Application startup latency in milliseconds.",
    )
    evidence.add_argument(
        "--measure-startup-command",
        nargs="+",
        default=None,
        help=(
            "Command to execute for startup-latency measurement (for example, "
            "a PyInstaller one-dir executable path). Measured value is used only "
            "when --startup-ms is not supplied."
        ),
    )
    evidence.add_argument(
        "--startup-timeout-seconds",
        type=float,
        default=30.0,
        help="Timeout used with --measure-startup-command.",
    )
    evidence.add_argument(
        "--startup-ready-after-seconds",
        type=float,
        default=0.5,
        help=(
            "Readiness window used with --measure-startup-command. "
            "Long-running GUI commands are treated as started once they stay alive "
            "for this many seconds."
        ),
    )
    evidence.add_argument(
        "--idle-memory-mib",
        type=float,
        default=None,
        help="Steady-state idle memory in MiB.",
    )
    evidence.add_argument(
        "--bundle-size-mib",
        type=float,
        default=None,
        help="PyInstaller one-dir bundle size in MiB.",
    )
    evidence.add_argument(
        "--collect-runtime-footprint",
        action="store_true",
        help=(
            "Collect idle memory from the local process and optionally measure "
            "bundle size from --bundle-dir when explicit metrics are not supplied."
        ),
    )
    evidence.add_argument(
        "--bundle-dir",
        type=str,
        default=None,
        help="Path to a PyInstaller one-dir output folder for auto bundle-size measurement.",
    )
    evidence.add_argument(
        "--qa-passed-checks",
        type=int,
        default=None,
        help="Manual QA checklist pass count for runtime validation summary.",
    )
    evidence.add_argument(
        "--qa-total-checks",
        type=int,
        default=None,
        help="Manual QA checklist total check count for runtime validation summary.",
    )
    evidence.add_argument(
        "--qa-issue",
        dest="qa_issues",
        action="append",
        default=[],
        help="Runtime QA issue/repro note. Repeat for multiple issues.",
    )
    evidence.add_argument(
        "--qa-checklist-file",
        type=str,
        default=None,
        help=(
            "Path to a markdown checklist file with - [x]/- [ ] items. "
            "When supplied, pass/total counts are derived automatically."
        ),
    )
    evidence.add_argument(
        "--write-markdown-file",
        type=str,
        default=None,
        help=(
            "Optional file path where the generated evidence markdown should be written. "
            "Parent directories are created when needed."
        ),
    )
    evidence.add_argument(
        "--check-qt-runtime",
        action="store_true",
        help=(
            "Append Qt dependency readiness diagnostics "
            "(PySide6 + PySide6.QtPdf import availability)."
        ),
    )

    harness = subparsers.add_parser(
        "phase2-viewer-harness",
        help="Launch the interactive Qt viewer harness for Phase 2 manual validation.",
    )
    harness.add_argument(
        "--pdf-path",
        required=True,
        help="Path to the PDF to open in the interactive validation harness.",
    )
    harness.add_argument(
        "--summary-json-path",
        default=None,
        help="Optional file path where the harness capture JSON should be written.",
    )
    harness.add_argument(
        "--evidence-command-path",
        default=None,
        help="Optional file path where the generated phase2-evidence command should be written.",
    )
    harness.add_argument(
        "--checklist-results-path",
        default=DEFAULT_CHECKLIST_RESULTS_PATH,
        help=(
            "File path where the run-specific manual QA checklist results should be "
            "written for later use with --qa-checklist-file."
        ),
    )
    harness.add_argument(
        "--checklist-template-path",
        default=DEFAULT_CHECKLIST_TEMPLATE_PATH,
        help="Template checklist used to seed the run-specific checklist results file.",
    )

    phase3_harness = subparsers.add_parser(
        "phase3-signing-harness",
        help="Launch the interactive Qt signing harness for Phase 3 acceptance.",
    )
    phase3_harness.add_argument(
        "--pdf-path",
        required=True,
        help="Path to the PDF to open in the interactive signing harness.",
    )
    phase3_harness.add_argument(
        "--certificate-path",
        default="demo-cert.p12",
        help="PKCS#12 certificate file used by the harness signing flow.",
    )
    phase3_harness.add_argument(
        "--passphrase",
        default="demo-passphrase",
        help="Passphrase for the PKCS#12 certificate file used by the harness.",
    )
    phase3_harness.add_argument(
        "--summary-json-path",
        default=None,
        help="Optional file path where the harness capture JSON should be written.",
    )
    phase3_harness.add_argument(
        "--checklist-results-path",
        default=DEFAULT_PHASE3_CHECKLIST_RESULTS_PATH,
        help=(
            "File path where the run-specific Phase 3 acceptance results should be "
            "written."
        ),
    )
    phase3_harness.add_argument(
        "--checklist-template-path",
        default=DEFAULT_PHASE3_CHECKLIST_TEMPLATE_PATH,
        help="Template checklist used to seed the run-specific Phase 3 results file.",
    )
    phase3_harness.add_argument(
        "--artifacts-dir",
        default=None,
        help=(
            "Optional directory where preview capture artifacts such as preview-card PNGs "
            "should be written."
        ),
    )

    gui = subparsers.add_parser(
        "gui",
        help="Launch the FoliaSeal main GUI.",
    )
    gui.add_argument(
        "--pdf-path",
        default=None,
        help="Optional PDF to open immediately after the main window launches.",
    )

    phase3_matrix = subparsers.add_parser(
        "phase3-signing-preview-matrix",
        help="Run a repeatable Phase 3 preview scenario sweep and capture per-scenario artifacts.",
    )
    phase3_matrix.add_argument(
        "--pdf-path",
        required=True,
        help="Path to the PDF to open in the preview matrix runner.",
    )
    phase3_matrix.add_argument(
        "--certificate-path",
        required=True,
        help="PKCS#12 certificate file used to derive preview field values.",
    )
    phase3_matrix.add_argument(
        "--passphrase",
        required=True,
        help="Passphrase for the PKCS#12 certificate file used by the preview matrix.",
    )
    phase3_matrix.add_argument(
        "--scenario-manifest-path",
        required=True,
        help="JSON manifest describing the preview scenarios to execute.",
    )
    phase3_matrix.add_argument(
        "--artifacts-dir",
        required=True,
        help="Directory where per-scenario preview PNGs and the summary JSON should be written.",
    )

    phase3_signed_matrix = subparsers.add_parser(
        "phase3-signing-acceptance-matrix",
        help="Run a representative signed-output acceptance sweep and capture artifacts.",
    )
    phase3_signed_matrix.add_argument(
        "--pdf-path",
        required=True,
        help="Path to the PDF to open and sign in the signed acceptance matrix runner.",
    )
    phase3_signed_matrix.add_argument(
        "--certificate-path",
        required=True,
        help="PKCS#12 certificate file used to sign acceptance matrix scenarios.",
    )
    phase3_signed_matrix.add_argument(
        "--passphrase",
        required=True,
        help="Passphrase for the PKCS#12 certificate file used by the signed matrix.",
    )
    phase3_signed_matrix.add_argument(
        "--scenario-manifest-path",
        required=True,
        help="JSON manifest describing the signed acceptance scenarios to execute.",
    )
    phase3_signed_matrix.add_argument(
        "--artifacts-dir",
        required=True,
        help=(
            "Directory where per-scenario signed-output artifacts and the summary "
            "JSON should be written."
        ),
    )

    phase3_signed_evidence = subparsers.add_parser(
        "phase3-signing-acceptance-evidence",
        help="Regenerate signed acceptance assets and run all signed evidence matrices.",
    )
    phase3_signed_evidence.add_argument(
        "--artifacts-root",
        default=".",
        help=(
            "Repository or workspace root under which ignored artifacts should be "
            "generated."
        ),
    )
    phase3_signed_evidence.add_argument(
        "--summary-markdown-path",
        default=None,
        help=(
            "Markdown file for the concise evidence summary. Defaults to "
            f"{DEFAULT_SIGNED_ACCEPTANCE_EVIDENCE_SUMMARY_PATH} under --artifacts-root."
        ),
    )

    phase3_validate = subparsers.add_parser(
        "phase3-signing-harness-validate",
        help="Validate an existing Phase 3 harness capture JSON without launching the GUI.",
    )
    phase3_validate.add_argument(
        "--summary-json-path",
        required=True,
        help="Path to an existing Phase 3 harness capture JSON file.",
    )

    return parser


def _run_phase2_evidence(args: argparse.Namespace) -> None:
    tracker = ViewerPerformanceTracker()

    if args.first_render_ms is not None:
        tracker.record_first_render(args.first_render_ms)
    for sample in args.navigation_ms:
        tracker.record_navigation(sample)

    startup_ms = args.startup_ms
    if startup_ms is None and args.measure_startup_command is not None:
        startup_ms = measure_startup_latency_ms(
            command=args.measure_startup_command,
            timeout_seconds=args.startup_timeout_seconds,
            ready_after_seconds=args.startup_ready_after_seconds,
        )

    runtime_footprint = RuntimeFootprintSnapshot(
        startup_ms=startup_ms,
        idle_memory_mib=args.idle_memory_mib,
        bundle_size_mib=args.bundle_size_mib,
    )
    if args.collect_runtime_footprint:
        auto_snapshot = collect_runtime_footprint_snapshot(
            startup_ms=startup_ms,
            bundle_dir=args.bundle_dir,
        )
        runtime_footprint = RuntimeFootprintSnapshot(
            startup_ms=startup_ms,
            idle_memory_mib=(
                args.idle_memory_mib
                if args.idle_memory_mib is not None
                else auto_snapshot.idle_memory_mib
            ),
            bundle_size_mib=(
                args.bundle_size_mib
                if args.bundle_size_mib is not None
                else auto_snapshot.bundle_size_mib
            ),
        )

    runtime_validation = None
    if args.qa_checklist_file is not None:
        runtime_validation = parse_checklist_markdown(
            checklist_path=args.qa_checklist_file
        )

    if args.qa_passed_checks is not None or args.qa_total_checks is not None:
        if args.qa_passed_checks is None or args.qa_total_checks is None:
            raise ValueError(
                "--qa-passed-checks and --qa-total-checks must be provided together."
            )
        manual_validation = RuntimeValidationSnapshot(
            passed_checks=args.qa_passed_checks,
            total_checks=args.qa_total_checks,
            issues=tuple(args.qa_issues),
        )
        runtime_validation = manual_validation
    elif runtime_validation is not None and args.qa_issues:
        runtime_validation = RuntimeValidationSnapshot(
            passed_checks=runtime_validation.passed_checks,
            total_checks=runtime_validation.total_checks,
            issues=runtime_validation.issues + tuple(args.qa_issues),
        )
    qt_runtime_readiness = (
        QtRuntimeReadinessSnapshot.collect() if args.check_qt_runtime else None
    )

    report = build_phase2_timing_evidence(
        timing=tracker.snapshot(),
        environment=RuntimeEnvironmentSnapshot.collect(),
        minimum_navigation_samples=args.minimum_navigation_samples,
        runtime_footprint=runtime_footprint,
        runtime_validation=runtime_validation,
        qt_runtime_readiness=qt_runtime_readiness,
    )
    print(report)
    if args.write_markdown_file is not None:
        output_path = Path(args.write_markdown_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report + "\n", encoding="utf-8")


def _run_phase3_harness_validate(args: argparse.Namespace) -> None:
    evaluation = _build_phase3_evidence_service().validate_harness_capture(
        Phase3HarnessValidationRequest(summary_json_path=args.summary_json_path)
    )
    print("Phase 3 evidence contract")
    print(f"- acceptance tier: {evaluation.acceptance_tier}")
    print(f"- gate verdict: {evaluation.gate_verdict}")
    print(f"- validation passed: {'yes' if evaluation.passed else 'no'}")
    print(f"- contract version: {evaluation.contract_version}")
    if evaluation.errors:
        print(f"- errors: {list(evaluation.errors)}")
    if evaluation.warnings:
        print(f"- warnings: {list(evaluation.warnings)}")
    if not evaluation.passed:
        raise ValueError("Phase 3 harness capture failed evidence contract validation.")


def _build_phase3_evidence_service():
    return build_default_phase3_evidence_service()


def _build_phase3_harness_capture_request(
    args: argparse.Namespace,
) -> Phase3HarnessCaptureRequest:
    return Phase3HarnessCaptureRequest(
        pdf_path=args.pdf_path,
        certificate_path=args.certificate_path,
        passphrase=args.passphrase,
        summary_json_path=args.summary_json_path,
        checklist_results_path=args.checklist_results_path,
        checklist_template_path=args.checklist_template_path,
        artifacts_dir=args.artifacts_dir,
    )


def _build_phase3_matrix_request(args: argparse.Namespace) -> Phase3MatrixRequest:
    return Phase3MatrixRequest(
        pdf_path=args.pdf_path,
        certificate_path=args.certificate_path,
        passphrase=args.passphrase,
        scenario_manifest_path=args.scenario_manifest_path,
        artifacts_dir=args.artifacts_dir,
    )


def _build_phase3_signed_acceptance_evidence_request(
    args: argparse.Namespace,
) -> Phase3SignedAcceptanceEvidenceRequest:
    return Phase3SignedAcceptanceEvidenceRequest(
        artifacts_root=args.artifacts_root,
        summary_markdown_path=args.summary_markdown_path,
        passphrase=SIGNED_ACCEPTANCE_IDENTITY_PASSPHRASE.decode("utf-8"),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run command-line helpers for local development workflows."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "phase2-evidence":
        _run_phase2_evidence(args)
        return 0
    if args.command == "phase2-viewer-harness":
        run_phase2_viewer_harness(
            pdf_path=args.pdf_path,
            summary_json_path=args.summary_json_path,
            evidence_command_path=args.evidence_command_path,
            checklist_results_path=args.checklist_results_path,
            checklist_template_path=args.checklist_template_path,
        )
        return 0
    if args.command == "phase3-signing-harness":
        _build_phase3_evidence_service().capture_harness(
            _build_phase3_harness_capture_request(args)
        )
        return 0
    if args.command == "gui":
        return launch_qt_app_frame(
            argv=argv if argv is not None else sys.argv,
            initial_pdf_path=args.pdf_path,
        )

    if args.command == "phase3-signing-preview-matrix":
        summary = _build_phase3_evidence_service().run_preview_matrix(
            _build_phase3_matrix_request(args)
        )
        print("Phase 3 preview matrix")
        print(f"- scenarios executed: {summary['scenario_count']}")
        print(f"- artifacts directory: {summary['artifacts_dir']}")
        print(f"- summary json: {Path(summary['artifacts_dir']) / 'summary.json'}")
        return 0
    if args.command == "phase3-signing-acceptance-matrix":
        summary = _build_phase3_evidence_service().run_signed_acceptance_matrix(
            _build_phase3_matrix_request(args)
        )
        print("Phase 3 signed acceptance matrix")
        print(f"- scenarios executed: {summary['scenario_count']}")
        print(f"- successful signings: {summary['successful_signing_run_count']}")
        print(f"- artifacts directory: {summary['artifacts_dir']}")
        print(f"- summary json: {Path(summary['artifacts_dir']) / 'summary.json'}")
        return 0
    if args.command == "phase3-signing-acceptance-evidence":
        evidence = _build_phase3_evidence_service().run_signed_acceptance_evidence(
            _build_phase3_signed_acceptance_evidence_request(args)
        )
        print("Phase 3 signed acceptance evidence")
        print(f"- summary markdown: {evidence.summary_markdown_path}")
        for result in evidence.matrix_results:
            counters = result.counters
            print(
                f"- {result.name}: PASS "
                f"({counters.scenario_count} scenarios, "
                f"{counters.successful_signing_run_count} successful signings)"
            )
        return 0
    if args.command == "phase3-signing-harness-validate":
        _run_phase3_harness_validate(args)
        return 0

    print("FoliaSeal phase 0 skeleton ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
