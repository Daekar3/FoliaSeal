"""CLI entry points for development checks and evidence helpers."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from pdf_signer.application.performance_timing import ViewerPerformanceTracker
from pdf_signer.application.phase2_evidence import (
    RuntimeEnvironmentSnapshot,
    build_phase2_timing_evidence,
)
from pdf_signer.application.runtime_metrics import RuntimeFootprintSnapshot


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

    return parser


def _run_phase2_evidence(args: argparse.Namespace) -> None:
    tracker = ViewerPerformanceTracker()

    if args.first_render_ms is not None:
        tracker.record_first_render(args.first_render_ms)
    for sample in args.navigation_ms:
        tracker.record_navigation(sample)

    report = build_phase2_timing_evidence(
        timing=tracker.snapshot(),
        environment=RuntimeEnvironmentSnapshot.collect(),
        minimum_navigation_samples=args.minimum_navigation_samples,
        runtime_footprint=RuntimeFootprintSnapshot(
            startup_ms=args.startup_ms,
            idle_memory_mib=args.idle_memory_mib,
            bundle_size_mib=args.bundle_size_mib,
        ),
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
