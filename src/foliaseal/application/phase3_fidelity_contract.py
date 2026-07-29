"""Versioned release-fidelity manifest contract for Phase 3 evidence."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

RELEASE_FIDELITY_MANIFEST_VERSION = 1
RELEASE_FIDELITY_CONTRACT_VERSION = "phase3_fidelity_v1"
RELEASE_FIDELITY_CRITICAL_ZERO_COUNTERS = (
    "expected_outcome_mismatch_count",
    "cryptographic_validation_failure_count",
    "preview_output_comparison_failure_count",
    "annotation_rect_mismatch_count",
)


def validate_release_fidelity_contract(payload: Mapping[str, Any]) -> None:
    """Validate the versioned fields used by the tracked release corpus."""

    if payload.get("manifest_version") != RELEASE_FIDELITY_MANIFEST_VERSION:
        raise ValueError(
            "Release fidelity manifest_version must be "
            f"{RELEASE_FIDELITY_MANIFEST_VERSION}."
        )
    contract = payload.get("comparison_contract")
    if not isinstance(contract, Mapping):
        raise ValueError("Release fidelity comparison_contract must be a JSON object.")
    if contract.get("version") != RELEASE_FIDELITY_CONTRACT_VERSION:
        raise ValueError(
            "Release fidelity comparison_contract.version must be "
            f"{RELEASE_FIDELITY_CONTRACT_VERSION!r}."
        )
    counters = contract.get("critical_zero_counters")
    if tuple(counters or ()) != RELEASE_FIDELITY_CRITICAL_ZERO_COUNTERS:
        raise ValueError(
            "Release fidelity critical_zero_counters must match the Phase 3 evidence contract."
        )
    tolerances = contract.get("tolerances")
    if not isinstance(tolerances, Mapping) or tolerances.get("preview_vs_output") != 0:
        raise ValueError("Release fidelity preview_vs_output tolerance must be zero.")

    scenarios = payload.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError("Release fidelity manifest must contain non-empty scenarios.")
    for index, scenario in enumerate(scenarios):
        if not isinstance(scenario, Mapping):
            raise ValueError(f"Release fidelity scenario {index} must be a JSON object.")
        expected_outcome = scenario.get("expected_outcome")
        if expected_outcome not in {"success", "validation_rejection"}:
            raise ValueError(
                f"Release fidelity scenario {index} must define expected_outcome as "
                "'success' or 'validation_rejection'."
            )
        diagnostics = scenario.get("expected_diagnostics")
        if not isinstance(diagnostics, Mapping):
            raise ValueError(
                f"Release fidelity scenario {index} must define expected_diagnostics."
            )
