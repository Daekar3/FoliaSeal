import pytest

from foliaseal.domain.models import SignatureStampPosition, TimestampTrustPolicy
from foliaseal.infra.config.schemas import (
    AppearanceProfile,
    ConfigValidationError,
    PlacementProfile,
    SignaturePreset,
    SignaturePresetCatalog,
    TimestampPolicy,
    TrustProfile,
)
from tests.support.phase3_builders import (
    build_appearance_profile,
    build_placement_profile,
    build_reference_signature_preset,
    build_signature_appearance,
    build_signature_preset,
    build_signature_preset_catalog,
)


def test_trust_profile_round_trip() -> None:
    original = TrustProfile(
        schema_version=1,
        use_system_store=True,
        extra_ca_bundle_path="/tmp/custom-ca.pem",
        revocation_mode="online",
    )

    payload = original.to_dict()
    reconstructed = TrustProfile.from_dict(payload)

    assert reconstructed == original


def test_trust_profile_converts_to_timestamp_trust_policy() -> None:
    original = TrustProfile(
        schema_version=1,
        use_system_store=False,
        extra_ca_bundle_path="/tmp/custom-ca.pem",
        revocation_mode="hard-fail",
    )

    converted = original.to_timestamp_trust_policy()

    assert converted == TimestampTrustPolicy(
        use_system_store=False,
        extra_ca_bundle_path="/tmp/custom-ca.pem",
        revocation_mode="hard-fail",
    )


def test_timestamp_policy_round_trip() -> None:
    original = TimestampPolicy(
        schema_version=1,
        required=True,
        tsa_url="https://tsa.example.com",
        timeout_seconds=10,
    )

    payload = original.to_dict()
    reconstructed = TimestampPolicy.from_dict(payload)

    assert reconstructed == original


def test_appearance_profile_round_trip() -> None:
    original = build_appearance_profile()

    payload = original.to_dict()
    reconstructed = AppearanceProfile.from_dict(payload)

    assert reconstructed == original
    assert payload["appearance"]["layout_template"] == "multi_line"
    assert payload["appearance"]["stamp_position"] == "left"
    assert payload["appearance"]["show_field_names"] is False


def test_appearance_profile_round_trip_allows_blank_signer_label_prefix() -> None:
    original = build_appearance_profile(
        appearance=build_signature_appearance(signer_label_prefix=""),
    )

    payload = original.to_dict()
    reconstructed = AppearanceProfile.from_dict(payload)

    assert reconstructed == original
    assert payload["appearance"]["signer_label_prefix"] == ""


def test_appearance_profile_round_trip_allows_stamp_position_variants() -> None:
    original = build_appearance_profile(
        appearance=build_signature_appearance(stamp_position=SignatureStampPosition.RIGHT)
    )

    payload = original.to_dict()
    reconstructed = AppearanceProfile.from_dict(payload)

    assert reconstructed == original
    assert payload["appearance"]["stamp_position"] == "right"


def test_appearance_profile_from_dict_defaults_missing_stamp_position_to_top() -> None:
    payload = build_appearance_profile().to_dict()
    payload["appearance"].pop("stamp_position")

    reconstructed = AppearanceProfile.from_dict(payload)

    assert reconstructed.appearance.stamp_position == SignatureStampPosition.TOP


def test_appearance_profile_rejects_blank_display_name() -> None:
    with pytest.raises(
        ConfigValidationError,
        match="Field 'display_name' must be a non-empty str",
    ):
        AppearanceProfile(
            schema_version=1,
            appearance_profile_id="appearance-empty",
            display_name=" ",
            appearance=build_signature_appearance(),
        )


def test_placement_profile_round_trip() -> None:
    original = build_placement_profile()

    payload = original.to_dict()
    reconstructed = PlacementProfile.from_dict(payload)

    assert reconstructed == original
    assert payload["rect"]["width_pt"] == 220.0
    assert payload["rect"]["height_pt"] == 80.0


def test_signature_preset_round_trip_is_reference_only() -> None:
    original = build_reference_signature_preset()

    payload = original.to_dict()
    reconstructed = SignaturePreset.from_dict(payload)

    assert reconstructed == original
    assert payload["appearance_profile_id"] == "appearance-default"
    assert payload["placement_profile_id"] == "placement-default"
    assert "appearance" not in payload
    assert "placement_defaults" not in payload


def test_signature_preset_catalog_round_trip() -> None:
    original = build_signature_preset_catalog()

    payload = original.to_dict()
    reconstructed = SignaturePresetCatalog.from_dict(payload)

    assert reconstructed == original
    assert original.profile_names() == ("Default", "Compact")
    assert original.profile_named("Compact").name == "Compact"
    assert payload["signature_presets"][0]["display_name"] == "Default"
    assert payload["appearance_profiles"][0]["display_name"] == "Default"
    assert payload["placement_profiles"][0]["display_name"] == "Default"


def test_signature_preset_catalog_upserts_by_name() -> None:
    original = build_signature_preset_catalog(profiles=(build_signature_preset(name="Default"),))
    replacement = build_signature_preset(
        name="Default",
        appearance=build_signature_appearance(
            signer_label_prefix="Signed by",
        ),
    )

    updated = original.upsert_profile(replacement)

    assert updated.profile_names() == ("Default",)
    assert updated.profile_named("Default").appearance == replacement.appearance
    assert updated.profile_names() == ("Default",)


def test_signature_preset_catalog_removes_by_name() -> None:
    original = build_signature_preset_catalog(
        profiles=(
            build_signature_preset(name="Default"),
            build_signature_preset(name="Compact"),
        )
    )

    updated = original.remove_profile("Default")

    assert updated.profile_names() == ("Compact",)


def test_signature_preset_catalog_rejects_duplicate_names() -> None:
    with pytest.raises(ConfigValidationError, match="must not contain duplicate names"):
        SignaturePresetCatalog(
            schema_version=1,
            signature_presets=(
                build_reference_signature_preset(
                    signature_preset_id="preset-default-1",
                    display_name="Default",
                ),
                build_reference_signature_preset(
                    signature_preset_id="preset-default-2",
                    display_name="Default",
                ),
            ),
        )


def test_bool_fields_do_not_accept_string_values() -> None:
    payload = {
        "schema_version": 1,
        "required": "false",
        "tsa_url": "https://tsa.example.com",
        "timeout_seconds": 10,
    }

    with pytest.raises(ConfigValidationError):
        TimestampPolicy.from_dict(payload)


def test_optional_str_rejects_non_string_values() -> None:
    payload = {
        "schema_version": 1,
        "use_system_store": True,
        "extra_ca_bundle_path": 123,
        "revocation_mode": "offline",
    }

    with pytest.raises(ConfigValidationError):
        TrustProfile.from_dict(payload)


def test_missing_required_field_raises_config_validation_error() -> None:
    payload = {
        "schema_version": 1,
        "required": True,
        "timeout_seconds": 10,
    }

    with pytest.raises(ConfigValidationError, match=r"Field 'tsa_url' is required\."):
        TimestampPolicy.from_dict(payload)
