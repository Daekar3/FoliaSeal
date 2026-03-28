"""CLI entry points for development checks and evidence helpers."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from pdf_signer.application.performance_timing import ViewerPerformanceTracker
from pdf_signer.application.phase2_evidence import (
    RuntimeEnvironmentSnapshot,
    build_phase2_timing_evidence,
)
from pdf_signer.application.runtime_metrics import (
    RuntimeFootprintSnapshot,
    collect_runtime_footprint_snapshot,
    measure_startup_latency_ms,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pdf-signer")
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

    report = build_phase2_timing_evidence(
        timing=tracker.snapshot(),
        environment=RuntimeEnvironmentSnapshot.collect(),
        minimum_navigation_samples=args.minimum_navigation_samples,
        runtime_footprint=runtime_footprint,
    )
    print(report)


def main(argv: Sequence[str] | None = None) -> None:
    """Run command-line helpers for local development workflows."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "phase2-evidence":
        _run_phase2_evidence(args)
        return

    print("pdf-signer phase 0 skeleton ready")


if __name__ == "__main__":
    main()
