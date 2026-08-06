import pytest

from foliaseal.application.reusable_signing_models import (
    AppearanceProfile,
    PlacementProfile,
    SignaturePreset,
    SignaturePresetCatalog,
)
from foliaseal.domain.models import SignatureStampPosition, TimestampTrustPolicy
from foliaseal.infra.config.schemas import (
    AppSettings,
    CertificateCatalog,
    CertificateConfiguration,
    ConfigValidationError,
    ManagedCertificate,
    ManagedCertificateSubjectSummary,
    TimestampPolicy,
    TrustProfile,
)
from tests.support.signing_builders import (
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


def test_app_settings_defaults_to_home_directories(tmp_path) -> None:
    settings = AppSettings.default(home_directory=tmp_path)

    assert settings.schema_version == 1
    assert settings.default_output_directory == str(tmp_path)
    assert settings.default_open_directory == str(tmp_path)
    assert settings.linux_packaging_channel == "primary"
    assert settings.ui == {}


def test_app_settings_round_trip_preserves_ui_mapping() -> None:
    original = AppSettings(
        schema_version=1,
        default_output_directory="/home/user/out",
        default_open_directory="/home/user/in",
        linux_packaging_channel="primary",
        ui={"last_window_layout": "compact"},
    )

    payload = original.to_dict()
    reconstructed = AppSettings.from_dict(payload)

    assert reconstructed == original
    assert payload == {
        "schema_version": 1,
        "default_output_directory": "/home/user/out",
        "default_open_directory": "/home/user/in",
        "linux_packaging_channel": "primary",
        "ui": {"last_window_layout": "compact"},
    }


def test_app_settings_rejects_blank_directories() -> None:
    with pytest.raises(ConfigValidationError, match="default_output_directory"):
        AppSettings(
            schema_version=1,
            default_output_directory=" ",
            default_open_directory="/home/user",
            linux_packaging_channel="primary",
            ui={},
        )


def test_app_settings_rejects_non_mapping_ui() -> None:
    payload = AppSettings.default(home_directory="/home/user").to_dict()
    payload["ui"] = "not-an-object"

    with pytest.raises(ConfigValidationError, match="ui"):
        AppSettings.from_dict(payload)


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
            managed_certificates=(
                build_managed_certificate(),
                build_managed_certificate(
                    managed_certificate_id="managed-cert-alt",
                    display_name="Alternate Signing Certificate",
                    storage_filename="cert_alt.p12",
                ),
            ),
            certificate_configurations=(
                build_certificate_configuration(
                    certificate_configuration_id="cert-config-a",
                    display_name="Corporate Records Signing",
                ),
                build_certificate_configuration(
                    certificate_configuration_id="cert-config-b",
                    display_name="Corporate Records Signing",
                    managed_certificate_id="managed-cert-alt",
                ),
            ),
        )


def test_certificate_catalog_rejects_duplicate_managed_certificate_references() -> None:
    with pytest.raises(ConfigValidationError, match="duplicate managed certificate"):
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
                    display_name="Alternate Signing",
                ),
            ),
        )


def test_certificate_catalog_removes_unreferenced_managed_certificate() -> None:
    catalog = build_certificate_catalog(
        managed_certificates=(
            build_managed_certificate(),
            build_managed_certificate(
                managed_certificate_id="managed-cert-alt",
                display_name="Alternate Signing Certificate",
                storage_filename="cert_alt.p12",
            ),
        )
    )

    updated = catalog.remove_managed_certificate_by_id("managed-cert-alt")

    assert tuple(
        certificate.managed_certificate_id
        for certificate in updated.managed_certificates
    ) == ("managed-cert-default",)
    with pytest.raises(KeyError):
        catalog.remove_managed_certificate_by_id("missing-cert")


def test_certificate_catalog_blocks_referenced_managed_certificate_removal() -> None:
    catalog = build_certificate_catalog()

    with pytest.raises(ConfigValidationError, match="delete the configuration first"):
        catalog.remove_managed_certificate_by_id("managed-cert-default")


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
    original = build_reference_signature_preset(
        certificate_configuration_id="cert-config-default",
    )

    payload = original.to_dict()
    reconstructed = SignaturePreset.from_dict(payload)

    assert reconstructed == original
    assert payload["certificate_configuration_id"] == "cert-config-default"
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
