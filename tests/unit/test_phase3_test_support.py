from pathlib import Path

import pytest

from foliaseal.domain.models import (
    SignatureFieldBinding,
    SignatureFieldSource,
    SignaturePlacementDefaults,
)
from tests.support.phase3_builders import (
    build_signature_appearance,
    build_signature_preset,
    build_signature_preset_catalog,
    build_signature_rect,
    build_signing_request,
    invalid_signature_field_binding_hidden_visible_kwargs,
)


def test_phase3_builders_produce_consistent_valid_contracts(tmp_path: Path) -> None:
    appearance = build_signature_appearance()
    preset = build_signature_preset(appearance=appearance)
    catalog = build_signature_preset_catalog(
        profiles=(preset,),
    )
    rect = build_signature_rect(page_index=3)
    request = build_signing_request(
        tmp_path,
        signature_rect=rect,
        signature_appearance=appearance,
    )

    assert preset.appearance == appearance
    assert preset.placement_defaults == SignaturePlacementDefaults(
        width_pt=220.0,
        height_pt=80.0,
    )
    assert catalog.preset_names() == ("default",)
    assert request.signature_rect == rect
    assert request.signature_appearance == appearance


def test_phase3_invalid_builder_kwargs_remain_reusable_for_negative_cases() -> None:
    with pytest.raises(ValueError, match="Hidden fields cannot be shown"):
        SignatureFieldBinding(**invalid_signature_field_binding_hidden_visible_kwargs())

    assert SignatureFieldSource.HIDDEN.value == "hidden"
