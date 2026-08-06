from __future__ import annotations

import dataclasses
import subprocess
import sys
from dataclasses import replace
from types import SimpleNamespace

import pytest

from foliaseal.presentation.qt.phase3_harness_scenario_policy import (
    Phase3HarnessResolvedScenario,
    Phase3HarnessScenarioResolver,
)
from tests.support.signing_builders import build_signature_appearance, build_signature_rect


class _ProfileStore:
    def __init__(self, appearance):
        self._appearance = appearance

    def load_catalog(self):
        return SimpleNamespace(
            preset_named=lambda _name: SimpleNamespace(appearance=self._appearance),
        )


def _resolver() -> Phase3HarnessScenarioResolver:
    return Phase3HarnessScenarioResolver(profile_store=_ProfileStore(build_signature_appearance()))


def test_resolver_applies_common_preview_controls_and_preserves_effects() -> None:
    rect = build_signature_rect(page_index=2)
    resolved = _resolver().resolve(
        profile_name=None,
        appearance_overrides={
            "layout_template": "single_line",
            "stamp_position": "bottom",
            "image_stamp_path": "/tmp/stamp.png",
            "box_style": {
                "border_width_pt": 3.5,
                "background_color_hex": "#EEEEEE",
            },
            "text_style": {"font_size_pt": 8.5, "italic": True},
        },
        timestamp_required=True,
        signature_rect=rect,
        fallback=build_signature_appearance(),
    )

    assert isinstance(resolved, Phase3HarnessResolvedScenario)
    assert resolved.appearance.layout_template.value == "single_line"
    assert resolved.appearance.stamp_position.value == "bottom"
    assert resolved.appearance.image_stamp_path == "/tmp/stamp.png"
    assert resolved.appearance.box_style.border_width_pt == 3.5
    assert resolved.appearance.text_style.italic is True
    assert resolved.timestamp_required is True
    assert resolved.signature_rect == rect


def test_resolver_applies_fixture_profile_and_visible_fields() -> None:
    appearance = build_signature_appearance()
    resolved = _resolver().resolve(
        profile_name=None,
        appearance_overrides={
            "fixture_profile": "stress_visible_appearance_v1",
            "visible_fields": ["common_name", "signing_time"],
        },
        timestamp_required=None,
        signature_rect=None,
        fallback=appearance,
    )

    assert resolved.appearance.common_name.show_in_visible_appearance is True
    assert resolved.appearance.signing_time.show_in_visible_appearance is True
    assert resolved.appearance.distinguished_name.source.value == "hidden"
    assert resolved.appearance.common_name.override_text == "Morgan Ellery"


def test_resolver_uses_named_profile_as_base() -> None:
    profile_appearance = build_signature_appearance()
    profile_appearance = replace(profile_appearance, signer_label_prefix="Profile")
    resolved = Phase3HarnessScenarioResolver(
        profile_store=_ProfileStore(profile_appearance),
    ).resolve(
        profile_name="named",
        appearance_overrides=None,
        timestamp_required=False,
        signature_rect=None,
        fallback=build_signature_appearance(),
    )

    assert resolved.appearance.signer_label_prefix == "Profile"
    assert resolved.timestamp_required is False


def test_resolver_preserves_validation_errors() -> None:
    with pytest.raises(ValueError, match="appearance_overrides.*object"):
        _resolver().resolve(
            profile_name=None,
            appearance_overrides=[],
            timestamp_required=None,
            signature_rect=None,
            fallback=build_signature_appearance(),
        )
    with pytest.raises(ValueError, match="visible_fields.*non-empty"):
        _resolver().resolve(
            profile_name=None,
            appearance_overrides={"visible_fields": []},
            timestamp_required=None,
            signature_rect=None,
            fallback=build_signature_appearance(),
        )
    with pytest.raises(ValueError):
        _resolver().resolve(
            profile_name=None,
            appearance_overrides={"visible_fields": ["not_a_field"]},
            timestamp_required=None,
            signature_rect=None,
            fallback=build_signature_appearance(),
        )


def test_resolved_scenario_is_immutable() -> None:
    resolved = _resolver().resolve(
        profile_name=None,
        appearance_overrides=None,
        timestamp_required=None,
        signature_rect=None,
        fallback=build_signature_appearance(),
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        resolved.timestamp_required = True  # type: ignore[misc]


def test_policy_module_import_is_free_of_optional_runtime_dependencies() -> None:
    code = (
        "import sys; "
        "import foliaseal.presentation.qt.phase3_harness_scenario_policy; "
        "print(any(name.startswith('PySide6') or name in {'PIL', 'pyhanko'} "
        "for name in sys.modules))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "False"
