"""Helpers to format Phase 2 runtime/timing evidence notes."""

from __future__ import annotations

import platform
import re
from dataclasses import dataclass
from pathlib import Path

from pdf_signer.application.performance_timing import ViewerTimingSnapshot
from pdf_signer.application.runtime_metrics import (
    RuntimeFootprintSnapshot,
    build_runtime_footprint_quick_check,
)


@dataclass(frozen=True)
class RuntimeEnvironmentSnapshot:
    """Minimal runtime environment context for QA evidence."""

    os_name: str
    os_version: str
    machine: str
    processor: str
    python_version: str

    @classmethod
    def collect(cls) -> RuntimeEnvironmentSnapshot:
        """Collect local host details for Phase 2 evidence notes."""

        return cls(
            os_name=platform.system() or "unknown",
            os_version=platform.version() or "unknown",
            machine=platform.machine() or "unknown",
            processor=platform.processor() or "unknown",
            python_version=platform.python_version() or "unknown",
        )


@dataclass(frozen=True)
class RuntimeValidationSnapshot:
    """Manual runtime validation sweep summary for Phase 2 review notes."""

    passed_checks: int
    total_checks: int
    issues: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.total_checks < 1:
            raise ValueError("total_checks must be at least 1.")
        if self.passed_checks < 0:
            raise ValueError("passed_checks must be greater than or equal to zero.")
        if self.passed_checks > self.total_checks:
            raise ValueError("passed_checks cannot exceed total_checks.")

    def to_markdown(self) -> str:
        """Render markdown summary for runtime validation checklist execution."""

        status = "✅" if self.passed_checks == self.total_checks else "⚠️"
        lines = [
            "### Runtime validation sweep",
            (
                f"- {status} Checklist status: "
                f"{self.passed_checks}/{self.total_checks} checks passed"
            ),
        ]
        if self.issues:
            lines.append("- Open issues:")
            lines.extend(f"  - {issue}" for issue in self.issues)
        else:
            lines.append("- Open issues: none recorded")
        return "\n".join(lines)


def parse_checklist_markdown(*, checklist_path: str) -> RuntimeValidationSnapshot:
    """Build runtime validation counts from a markdown checklist file."""

    path = Path(checklist_path)
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"Unable to read checklist file: {checklist_path}") from exc

    checked_pattern = re.compile(r"^\s*-\s*\[[xX]\]\s+(.+)$")
    unchecked_pattern = re.compile(r"^\s*-\s*\[\s\]\s+(.+)$")

    passed = 0
    total = 0
    issues: list[str] = []
    for raw_line in content.splitlines():
        checked_match = checked_pattern.match(raw_line)
        if checked_match:
            passed += 1
            total += 1
            continue

        unchecked_match = unchecked_pattern.match(raw_line)
        if unchecked_match:
            total += 1
            issues.append(unchecked_match.group(1).strip())

    if total < 1:
        raise ValueError(
            "Checklist file did not contain markdown checkbox items (- [ ] or - [x])."
        )

    return RuntimeValidationSnapshot(
        passed_checks=passed,
        total_checks=total,
        issues=tuple(issues),
    )


def build_phase2_timing_evidence(
    *,
    timing: ViewerTimingSnapshot,
    environment: RuntimeEnvironmentSnapshot,
    minimum_navigation_samples: int = 10,
    runtime_footprint: RuntimeFootprintSnapshot | None = None,
    runtime_validation: RuntimeValidationSnapshot | None = None,
) -> str:
    """Build markdown evidence block for Phase 2 runtime/timing sign-off."""

    if minimum_navigation_samples < 1:
        raise ValueError("minimum_navigation_samples must be at least 1.")

    lines = [
        "## Phase 2 runtime evidence",
        timing.to_markdown(),
        "",
        "### Runtime environment",
        f"- OS: {environment.os_name} ({environment.os_version})",
        f"- Machine: {environment.machine}",
        f"- Processor: {environment.processor}",
        f"- Python: {environment.python_version}",
        "",
        "### Exit criteria quick-check",
    ]
    first_render_status = "✅" if timing.first_render_ms is not None else "⚠️"
    navigation_status = (
        "✅" if timing.sample_count >= minimum_navigation_samples else "⚠️"
    )
    lines.extend(
        [
            f"- {first_render_status} First-render timing recorded",
            (
                f"- {navigation_status} Navigation sample count "
                f"({timing.sample_count}/{minimum_navigation_samples})"
            ),
        ]
    )

    if runtime_footprint is not None:
        lines.extend(
            [
                "",
                runtime_footprint.to_markdown(),
                "",
                build_runtime_footprint_quick_check(footprint=runtime_footprint),
            ]
        )

    if runtime_validation is not None:
        lines.extend(
            [
                "",
                runtime_validation.to_markdown(),
            ]
        )

    return "\n".join(lines)
