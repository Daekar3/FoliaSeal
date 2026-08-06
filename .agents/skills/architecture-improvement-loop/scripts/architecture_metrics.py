#!/usr/bin/env python3
"""Deterministic arithmetic helper for architecture-improvement-loop.

The script does not judge architecture. Agents supply evidence-backed scores or
before/after measurements; this helper validates ranges and performs the fixed
calculations from REFERENCE.md.

Usage:
    architecture_metrics.py candidate [input.json|-]
    architecture_metrics.py shape [input.json|-]
    architecture_metrics.py improvement [input.json|-]

If no input path is supplied, JSON is read from stdin.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping


CANDIDATE_DIMENSIONS = (
    "navigation_friction",
    "change_amplification",
    "seam_risk",
    "testability_gain",
    "interface_compression",
    "conceptual_cohesion",
    "migration_risk",
    "behavioral_uncertainty",
)

SHAPE_DIMENSIONS = (
    "interface_depth",
    "caller_simplicity",
    "behavioral_testability",
    "dependency_isolation",
    "ownership_clarity",
    "migration_feasibility",
    "requirement_compatibility",
)

IMPROVEMENT_WEIGHTS = {
    "navigation_reduction": 0.20,
    "change_amplification_reduction": 0.15,
    "seam_reduction": 0.15,
    "boundary_test_improvement": 0.20,
    "interface_compression": 0.15,
    "boundary_isolation_improvement": 0.15,
}


class InputError(ValueError):
    """Raised when an input document does not satisfy the scoring contract."""


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def require_number(value: Any, label: str, low: float, high: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputError(f"{label} must be a number")
    number = float(value)
    if not math.isfinite(number):
        raise InputError(f"{label} must be finite")
    if number < low or number > high:
        raise InputError(f"{label} must be between {low} and {high}; got {number}")
    return number


def require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise InputError(f"{label} must be a JSON object")
    return value


def require_sequence(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise InputError(f"{label} must be a JSON array")
    return value


def read_json(path: str | None) -> Mapping[str, Any]:
    if path in (None, "-"):
        raw = sys.stdin.read()
    else:
        raw = Path(path).read_text(encoding="utf-8")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise InputError(f"invalid JSON: {exc}") from exc
    return require_mapping(parsed, "root")


def rounded(value: float) -> float:
    return round(value, 6)


def median_scores(records: Iterable[Mapping[str, Any]], dimensions: tuple[str, ...], label: str) -> tuple[dict[str, float], dict[str, float]]:
    records_list = list(records)
    if len(records_list) < 2:
        raise InputError(f"{label} requires at least two independent score records")

    medians: dict[str, float] = {}
    ranges: dict[str, float] = {}
    for dimension in dimensions:
        values = [
            require_number(record.get(dimension), f"{label}[{index}].{dimension}", 0, 5)
            for index, record in enumerate(records_list)
        ]
        medians[dimension] = float(statistics.median(values))
        ranges[dimension] = max(values) - min(values)
    return medians, ranges


def score_candidate(data: Mapping[str, Any]) -> dict[str, Any]:
    explorers = require_sequence(data.get("explorers"), "explorers")
    explorer_maps = [require_mapping(item, f"explorers[{i}]") for i, item in enumerate(explorers)]
    medians, ranges = median_scores(explorer_maps, CANDIDATE_DIMENSIONS, "explorers")

    evidence_coverage = require_number(data.get("evidence_coverage"), "evidence_coverage", 0, 1)
    normalized_ranges = [ranges[name] / 5.0 for name in CANDIDATE_DIMENSIONS]
    agreement = 1.0 - statistics.mean(normalized_ranges)
    confidence = clamp(0.70 * agreement + 0.30 * evidence_coverage, 0, 1)

    benefit = (
        0.20 * medians["navigation_friction"]
        + 0.15 * medians["change_amplification"]
        + 0.15 * medians["seam_risk"]
        + 0.20 * medians["testability_gain"]
        + 0.15 * medians["interface_compression"]
        + 0.15 * medians["conceptual_cohesion"]
    )
    penalty = (
        0.60 * medians["migration_risk"]
        + 0.40 * medians["behavioral_uncertainty"]
    )
    priority = clamp(
        100.0 * (0.75 * benefit + 0.25 * benefit * confidence - 0.30 * penalty) / 5.0,
        0,
        100,
    )

    return {
        "median_scores": {key: rounded(value) for key, value in medians.items()},
        "score_ranges": {key: rounded(value) for key, value in ranges.items()},
        "agreement": rounded(agreement),
        "evidence_coverage": rounded(evidence_coverage),
        "confidence": rounded(confidence),
        "benefit": rounded(benefit),
        "penalty": rounded(penalty),
        "candidate_priority": rounded(priority),
        "credible_by_confidence": confidence >= 0.60,
        "meets_continuation_threshold": confidence >= 0.60 and priority >= 60.0,
    }


def score_shape(data: Mapping[str, Any]) -> dict[str, Any]:
    reviewers = require_sequence(data.get("reviewers"), "reviewers")
    reviewer_maps = [require_mapping(item, f"reviewers[{i}]") for i, item in enumerate(reviewers)]
    medians, ranges = median_scores(reviewer_maps, SHAPE_DIMENSIONS, "reviewers")

    penalty_points = require_number(data.get("penalty_points", 0), "penalty_points", 0, 100)
    penalty_reasons_raw = data.get("penalty_reasons", [])
    penalty_reasons = require_sequence(penalty_reasons_raw, "penalty_reasons")
    if any(not isinstance(item, str) for item in penalty_reasons):
        raise InputError("every penalty_reasons item must be a string")

    base = 20.0 * (
        0.25 * medians["interface_depth"]
        + 0.15 * medians["caller_simplicity"]
        + 0.20 * medians["behavioral_testability"]
        + 0.15 * medians["dependency_isolation"]
        + 0.10 * medians["ownership_clarity"]
        + 0.10 * medians["migration_feasibility"]
        + 0.05 * medians["requirement_compatibility"]
    )
    final = clamp(base - penalty_points, 0, 100)

    return {
        "median_scores": {key: rounded(value) for key, value in medians.items()},
        "score_ranges": {key: rounded(value) for key, value in ranges.items()},
        "base_shape_score": rounded(base),
        "penalty_points": rounded(penalty_points),
        "penalty_reasons": penalty_reasons,
        "refactor_shape_score": rounded(final),
    }


def reduction(before: float, after: float) -> float:
    if before == 0:
        return 0.0 if after == 0 else -1.0
    return clamp((before - after) / max(before, 1.0), -1, 1)


def require_nonnegative(value: Any, label: str) -> float:
    return require_number(value, label, 0, float("inf"))


def score_improvement(data: Mapping[str, Any]) -> dict[str, Any]:
    baseline = require_mapping(data.get("baseline"), "baseline")
    post = require_mapping(data.get("post"), "post")

    count_fields = {
        "navigation_units": "navigation_reduction",
        "change_amplification_units": "change_amplification_reduction",
        "seam_count": "seam_reduction",
        "public_surface_units": "interface_compression",
        "boundary_bypass_count": "boundary_isolation_improvement",
    }

    components: dict[str, float] = {}
    for field, component in count_fields.items():
        before = require_nonnegative(baseline.get(field), f"baseline.{field}")
        after = require_nonnegative(post.get(field), f"post.{field}")
        components[component] = reduction(before, after)

    before_coverage = require_number(
        baseline.get("boundary_behavior_coverage"),
        "baseline.boundary_behavior_coverage",
        0,
        1,
    )
    after_coverage = require_number(
        post.get("boundary_behavior_coverage"),
        "post.boundary_behavior_coverage",
        0,
        1,
    )
    components["boundary_test_improvement"] = clamp(after_coverage - before_coverage, -1, 1)

    actual = sum(IMPROVEMENT_WEIGHTS[name] * components[name] for name in IMPROVEMENT_WEIGHTS)
    worst_component = min(components.values())

    result: dict[str, Any] = {
        "components": {key: rounded(value) for key, value in components.items()},
        "actual_improvement": rounded(actual),
        "worst_component": rounded(worst_component),
        "meets_minimum_improvement": actual >= 0.15,
        "component_regression_within_limit": worst_component >= -0.10,
    }

    predicted_raw = data.get("predicted_components")
    if predicted_raw is not None:
        predicted_map = require_mapping(predicted_raw, "predicted_components")
        predicted_components = {
            name: require_number(predicted_map.get(name), f"predicted_components.{name}", -1, 1)
            for name in IMPROVEMENT_WEIGHTS
        }
        predicted = sum(
            IMPROVEMENT_WEIGHTS[name] * predicted_components[name]
            for name in IMPROVEMENT_WEIGHTS
        )
        result["predicted_components"] = {
            key: rounded(value) for key, value in predicted_components.items()
        }
        result["predicted_improvement"] = rounded(predicted)
        result["prediction_accuracy"] = (
            None if predicted <= 0 else rounded(actual / predicted)
        )
        result["achieved_half_predicted"] = predicted > 0 and actual >= 0.5 * predicted

    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("candidate", "shape", "improvement"))
    parser.add_argument("input", nargs="?", help="JSON file path, or '-' for stdin")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        data = read_json(args.input)
        if args.mode == "candidate":
            result = score_candidate(data)
        elif args.mode == "shape":
            result = score_shape(data)
        else:
            result = score_improvement(data)
    except (InputError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, indent=2), file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
