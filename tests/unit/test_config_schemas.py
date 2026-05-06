import pytest

from foliaseal.domain.models import SignatureStampPosition, TimestampTrustPolicy
from foliaseal.infra.config.schemas import (
    AppearanceProfile,
    CertificateCatalog,
    CertificateConfiguration,
    ConfigValidationError,
    ManagedCertificate,
    ManagedCertificateSubjectSummary,
    PlacementProfile,
    SignaturePreset,
    SignaturePresetCatalog,
    TimestampPolicy,
    TrustProfile,
)
from tests.support.phase3_builders import (
    build_appearance_profile,
    build_certificate_catalog,
    build_certificate_configuration,
    build_managed_certificate,
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


def test_managed_certificate_round_trip() -> None:
    original = build_managed_certificate()

    payload = original.to_dict()
    reconstructed = ManagedCertificate.from_dict(payload)

    assert reconstructed == original
    assert payload["managed_certificate_id"] == "managed-cert-default"
    assert payload["storage_filename"] == "cert_default.p12"
    assert payload["subject_summary"]["common_name"] == "Morgan Ellery"


def test_managed_certificate_subject_summary_round_trip_allows_missing_fields() -> None:
    original = ManagedCertificateSubjectSummary(
        common_name="Morgan Ellery",
        email=None,
        title=None,
        company="Northwind Ledger Holdings",
    )

    payload = original.to_dict()
    reconstructed = ManagedCertificateSubjectSummary.from_dict(payload)

    assert reconstructed == original
    assert payload["email"] is None
    assert payload["title"] is None


def test_managed_certificate_rejects_path_like_storage_filename() -> None:
    with pytest.raises(ConfigValidationError, match="storage_filename"):
        build_managed_certificate(storage_filename="../secret.p12")


def test_certificate_configuration_round_trip_without_plain_password() -> None:
    original = build_certificate_configuration(
        save_password=True,
        password_secret_ref="secret://foliaseal/cert-config-default",
    )

    payload = original.to_dict()
    reconstructed = CertificateConfiguration.from_dict(payload)

    assert reconstructed == original
    assert payload["save_password"] is True
    assert payload["password_secret_ref"] == "secret://foliaseal/cert-config-default"
    assert "password" not in payload
    assert "passphrase" not in payload


def test_certificate_configuration_rejects_saved_password_without_secret_ref() -> None:
    with pytest.raises(ConfigValidationError, match="password_secret_ref"):
        build_certificate_configuration(save_password=True, password_secret_ref=None)


def test_certificate_catalog_round_trip_and_lookup() -> None:
    original = build_certificate_catalog()

    payload = original.to_dict()
    reconstructed = CertificateCatalog.from_dict(payload)

    assert reconstructed == original
    assert payload["managed_certificates"][0]["display_name"] == "Board Secretary 2026"
    assert payload["certificate_configurations"][0]["display_name"] == (
        "Corporate Records Signing"
    )
    configuration = reconstructed.configuration_named("Corporate Records Signing")
    assert configuration.managed_certificate_id == "managed-cert-default"
    assert reconstructed.managed_certificate_by_id("managed-cert-default").storage_filename == (
        "cert_default.p12"
    )


def test_certificate_catalog_rejects_duplicate_configuration_names() -> None:
    with pytest.raises(ConfigValidationError, match="duplicate names"):
        CertificateCatalog(
            schema_version=1,
            managed_certificates=(build_managed_certificate(),),
            certificate_configurations=(
                build_certificate_configuration(
                    certificate_configuration_id="cert-config-a",
                    display_name="Corporate Records Signing",
                ),
                build_certificate_configuration(
                    certificate_configuration_id="cert-config-b",
                    display_name="Corporate Records Signing",
                ),
            ),
        )


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
    assert original.preset_names() == ("Default", "Compact")
    assert original.preset_named("Compact").name == "Compact"
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

    updated = original.upsert_preset(replacement)

    assert updated.preset_names() == ("Default",)
    assert updated.preset_named("Default").appearance == replacement.appearance
    assert updated.preset_names() == ("Default",)


def test_signature_preset_catalog_removes_by_name() -> None:
    original = build_signature_preset_catalog(
        profiles=(
            build_signature_preset(name="Default"),
            build_signature_preset(name="Compact"),
        )
    )

    updated = original.remove_preset("Default")

    assert updated.preset_names() == ("Compact",)


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
