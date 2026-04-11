"""Generate checked-in stress manifests from the baseline preview matrices."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from foliaseal.application.qa_preview_stress_fixtures import STRESS_VISIBLE_APPEARANCE_PROFILE

ASSETS_DIR = Path("artifacts/preview_sweep_assets")

SINGLE_LINE_FIELD_VARIANTS = (
    ("sparse", ["common_name", "signing_time"]),
    ("medium", ["common_name", "company", "signing_time"]),
    ("dense", ["common_name", "email", "title", "company", "signing_time"]),
)

STACKED_FIELD_VARIANTS = (
    ("sparse", ["common_name", "email", "signing_time"]),
    ("medium", ["common_name", "title", "company", "signing_time"]),
    (
        "dense",
        ["common_name", "email", "title", "company", "signing_time", "location", "reason"],
    ),
)

WRAPPED_FIELD_VARIANTS = (
    ("sparse", ["common_name", "email", "signing_time"]),
    ("medium", ["common_name", "title", "company", "signing_time", "location"]),
    (
        "dense",
        ["common_name", "email", "title", "company", "signing_time", "location", "reason"],
    ),
)

LABEL_VARIANTS = (
    ("label", "Digitally signed by"),
    ("nolabel", ""),
)

NAMED_VARIANTS = (
    ("named", True),
    ("plain", False),
)


def _load_manifest(name: str) -> list[dict]:
    payload = json.loads((ASSETS_DIR / name).read_text(encoding="utf-8"))
    return payload["scenarios"]


def _geometry_key(scenario: dict) -> tuple:
    appearance = scenario["appearance_overrides"]
    rect = scenario["signature_rect"]
    return (
        appearance["layout_template"],
        appearance["stamp_position"],
        appearance["image_stamp_path"],
        appearance["box_style"]["border_width_pt"],
        appearance["text_style"]["font_size_pt"],
        appearance["text_style"].get("italic"),
        rect["page_index"],
        rect["left_pt"],
        rect["bottom_pt"],
        rect["width_pt"],
        rect["height_pt"],
    )


def _base_geometry_scenarios(name: str) -> list[dict]:
    scenarios = _load_manifest(name)
    seen: set[tuple] = set()
    unique: list[dict] = []
    for scenario in scenarios:
        key = _geometry_key(scenario)
        if key in seen:
            continue
        seen.add(key)
        unique.append(deepcopy(scenario))
    return unique


def _stress_base_name(*, source_name: str, scenario_name: str) -> str:
    if source_name == "single_line_full_matrix.json":
        return scenario_name
    if source_name == "multi_line_full_matrix.json":
        for suffix in ("_label_sparse", "_label_dense", "_nolabel_sparse", "_nolabel_dense"):
            if scenario_name.endswith(suffix):
                return scenario_name[: -len(suffix)]
    if source_name == "wrapped_block_full_matrix.json":
        for suffix in (
            "_label_dense_named",
            "_label_dense",
            "_nolabel_dense_named",
            "_nolabel_dense",
        ):
            if scenario_name.endswith(suffix):
                return scenario_name[: -len(suffix)]
    return scenario_name


def _single_line_stress_scenarios() -> list[dict]:
    generated: list[dict] = []
    source_name = "single_line_full_matrix.json"
    for scenario in _base_geometry_scenarios(source_name):
        base_name = _stress_base_name(source_name=source_name, scenario_name=scenario["name"])
        for label_tag, label_prefix in LABEL_VARIANTS:
            for density_tag, visible_fields in SINGLE_LINE_FIELD_VARIANTS:
                clone = deepcopy(scenario)
                clone["name"] = f"{base_name}_{label_tag}_{density_tag}"
                clone["appearance_overrides"]["fixture_profile"] = (
                    STRESS_VISIBLE_APPEARANCE_PROFILE
                )
                clone["appearance_overrides"]["signer_label_prefix"] = label_prefix
                clone["appearance_overrides"]["visible_fields"] = visible_fields
                generated.append(clone)
    return generated


def _stacked_stress_scenarios(
    *,
    source_name: str,
    field_variants: tuple[tuple[str, list[str]], ...],
    include_named_variants: bool,
) -> list[dict]:
    generated: list[dict] = []
    for scenario in _base_geometry_scenarios(source_name):
        base_name = _stress_base_name(source_name=source_name, scenario_name=scenario["name"])
        for label_tag, label_prefix in LABEL_VARIANTS:
            for density_tag, visible_fields in field_variants:
                named_variants = NAMED_VARIANTS if include_named_variants else (("plain", False),)
                for named_tag, show_field_names in named_variants:
                    clone = deepcopy(scenario)
                    name = f"{base_name}_{label_tag}_{density_tag}"
                    if include_named_variants:
                        name = f"{name}_{named_tag}"
                    clone["name"] = name
                    clone["appearance_overrides"]["fixture_profile"] = (
                        STRESS_VISIBLE_APPEARANCE_PROFILE
                    )
                    clone["appearance_overrides"]["signer_label_prefix"] = label_prefix
                    clone["appearance_overrides"]["visible_fields"] = visible_fields
                    clone["appearance_overrides"]["show_field_names"] = show_field_names
                    generated.append(clone)
    return generated


def _write_manifest(
    *,
    output_name: str,
    scenarios: list[dict],
    source_manifest: str,
) -> None:
    payload = {
        "fixture_profile": STRESS_VISIBLE_APPEARANCE_PROFILE,
        "source_manifest": source_manifest,
        "scenarios": scenarios,
    }
    (ASSETS_DIR / output_name).write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    _write_manifest(
        output_name="single_line_full_matrix_stress.json",
        scenarios=_single_line_stress_scenarios(),
        source_manifest="single_line_full_matrix.json",
    )
    _write_manifest(
        output_name="multi_line_full_matrix_stress.json",
        scenarios=_stacked_stress_scenarios(
            source_name="multi_line_full_matrix.json",
            field_variants=STACKED_FIELD_VARIANTS,
            include_named_variants=False,
        ),
        source_manifest="multi_line_full_matrix.json",
    )
    _write_manifest(
        output_name="wrapped_block_full_matrix_stress.json",
        scenarios=_stacked_stress_scenarios(
            source_name="wrapped_block_full_matrix.json",
            field_variants=WRAPPED_FIELD_VARIANTS,
            include_named_variants=True,
        ),
        source_manifest="wrapped_block_full_matrix.json",
    )


if __name__ == "__main__":
    main()
