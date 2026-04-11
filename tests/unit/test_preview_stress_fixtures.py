from foliaseal.application.qa_preview_stress_fixtures import (
    STRESS_VISIBLE_APPEARANCE_PROFILE,
    STRESS_VISIBLE_APPEARANCE_VALUES,
    apply_preview_stress_fixture_profile,
)
from foliaseal.domain.models import SignatureFieldSource
from tests.support.phase3_builders import build_signature_appearance


def test_apply_preview_stress_fixture_profile_sets_expected_override_texts() -> None:
    stressed = apply_preview_stress_fixture_profile(
        appearance=build_signature_appearance(),
        profile_name=STRESS_VISIBLE_APPEARANCE_PROFILE,
    )

    for field_key, value in STRESS_VISIBLE_APPEARANCE_VALUES.items():
        binding = stressed.binding_for(field_key)
        assert binding.source == SignatureFieldSource.OVERRIDE
        assert binding.show_in_visible_appearance is True
        assert binding.override_text == value


def test_apply_preview_stress_fixture_profile_rejects_unknown_profile() -> None:
    try:
        apply_preview_stress_fixture_profile(
            appearance=build_signature_appearance(),
            profile_name="unknown_fixture_profile",
        )
    except ValueError as exc:
        assert "Unknown preview stress fixture profile" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown fixture profile")
