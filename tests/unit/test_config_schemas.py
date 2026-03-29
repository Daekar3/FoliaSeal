import pytest

from foliaseal.infra.config.schemas import (
    ConfigValidationError,
    SignaturePreset,
    SignaturePresetCatalog,
    TimestampPolicy,
    TrustProfile,
)
from tests.support.phase3_builders import (
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


def test_signature_preset_round_trip() -> None:
    original = build_signature_preset()

    payload = original.to_dict()
    reconstructed = SignaturePreset.from_dict(payload)

    assert reconstructed == original
    assert payload["appearance"]["layout_template"] == "multi_line"
    assert payload["appearance"]["show_field_names"] is False
    assert payload["placement_defaults"]["anchor"] == "bottom_right"


def test_signature_preset_rejects_blank_name() -> None:
    with pytest.raises(ConfigValidationError, match="Field 'name' must be a non-empty str"):
        SignaturePreset(
            schema_version=1,
            name=" ",
            appearance=build_signature_appearance(),
        )


def test_signature_preset_catalog_round_trip() -> None:
    original = build_signature_preset_catalog()

    payload = original.to_dict()
    reconstructed = SignaturePresetCatalog.from_dict(payload)

    assert reconstructed == original
    assert original.profile_names() == ("Default", "Compact")
    assert original.profile_named("Compact").name == "Compact"
    assert payload["profiles"][0]["name"] == "Default"


def test_signature_preset_catalog_upserts_by_name() -> None:
    original = SignaturePresetCatalog(
        schema_version=1,
        profiles=(build_signature_preset(name="Default"),),
    )
    replacement = build_signature_preset(
        name="Default",
        appearance=build_signature_appearance(
            signer_label_prefix="Signed by",
        ),
    )

    updated = original.upsert_profile(replacement)

    assert updated.profiles == (replacement,)
    assert updated.profile_names() == ("Default",)


def test_signature_preset_catalog_removes_by_name() -> None:
    original = SignaturePresetCatalog(
        schema_version=1,
        profiles=(
            build_signature_preset(name="Default"),
            build_signature_preset(name="Compact"),
        ),
    )

    updated = original.remove_profile("Default")

    assert updated.profile_names() == ("Compact",)


def test_signature_preset_catalog_rejects_duplicate_names() -> None:
    with pytest.raises(ConfigValidationError, match="must not contain duplicate names"):
        SignaturePresetCatalog(
            schema_version=1,
            profiles=(
                build_signature_preset(name="Default"),
                build_signature_preset(name="Default"),
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
