from pathlib import Path

import pytest

from foliaseal.application import (
    SigningDraftValidationIssue,
    SigningDraftValidationSeverity,
    SigningDraftWorkflow,
)
from foliaseal.application.signature_properties_coordinator import (
    ApplyCertificateConfiguration,
    ApplySignaturePreset,
    ApplyVisibleSignatureSetup,
    DefaultSignaturePropertiesCoordinator,
    DeletePreset,
    RefreshCatalogs,
    SaveCurrentAppearanceProfile,
    SaveCurrentPlacementProfile,
    SaveCurrentPreset,
    SetSignatureAppearance,
    SignaturePropertiesCoordinatorError,
    VisibleSignaturePlacementDraft,
    VisibleSignatureSetupDraft,
)
from foliaseal.domain.models import SignaturePlacementDefaults, SignatureRect
from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
from foliaseal.infra.config.profile_storage import (
    PROFILE_DIRECTORY_NAME,
    SignaturePresetCatalogStore,
)
from foliaseal.infra.config.schemas import CertificateCatalog, SignaturePresetCatalog
from tests.support.signing_builders import (
    build_certificate_catalog,
    build_certificate_configuration,
    build_managed_certificate,
    build_signature_appearance,
    build_signature_preset,
    build_signature_preset_catalog,
)


class _FakeSecretProvider:
    def __init__(self, secrets: dict[str, str] | None = None, *, available: bool = True) -> None:
        self._secrets = secrets or {}
        self._available = available

    def is_available(self) -> bool:
        return self._available

    def get_secret(self, secret_ref: str) -> str | None:
        return self._secrets.get(secret_ref)


def _workflow(tmp_path: Path) -> SigningDraftWorkflow:
    return SigningDraftWorkflow(
        input_pdf_path=str(tmp_path / "input.pdf"),
        output_pdf_path=str(tmp_path / "output.pdf"),
        certificate_path=str(tmp_path / "cert.p12"),
        passphrase="secret",
        tsa_url="https://tsa.example.com",
        timestamp_required=True,
        certificate_alias="signing-cert",
    )


def _ready_workflow(tmp_path: Path) -> SigningDraftWorkflow:
    workflow = _workflow(tmp_path)
    workflow.set_signature_appearance(build_signature_appearance())
    workflow.set_signature_rect(
        SignatureRect(
            page_index=0,
            left_pt=24.0,
            bottom_pt=18.0,
            width_pt=180.0,
            height_pt=48.0,
        )
    )
    return workflow


def test_coordinator_load_reports_catalog_names_and_initial_readiness(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    workflow.set_signature_appearance(build_signature_appearance())
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=workflow,
        certificate_catalog=build_certificate_catalog(),
        preset_catalog=build_signature_preset_catalog(),
    )

    state = coordinator.load()

    assert state.certificate_configuration_names == ("Corporate Records Signing",)
    assert state.signature_preset_names == ("Default", "Compact")
    assert state.selected_certificate_configuration_name is None
    assert state.selected_signature_preset_name is None
    assert state.ready_to_sign is False
    assert state.validation_text == "Place a signature on the page to continue."
    assert state.visible_signature_setup_draft.placement.enabled is False
    assert state.visible_signature_setup_draft.placement.width_pt == 72.0
    assert state.visible_signature_setup_draft.placement.height_pt == 24.0


def test_coordinator_load_reports_visible_signature_setup_draft(tmp_path: Path) -> None:
    workflow = _ready_workflow(tmp_path)
    appearance = build_signature_appearance(
        signer_label_prefix="Signed by Team",
        show_field_names=True,
    )
    workflow.set_signature_appearance(appearance)
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=workflow,
        certificate_catalog=build_certificate_catalog(),
        preset_catalog=build_signature_preset_catalog(),
    )

    state = coordinator.load()

    assert state.visible_signature_setup_draft.appearance == appearance
    assert state.visible_signature_setup_draft.placement == VisibleSignaturePlacementDraft(
        page_number=1,
        left_pt=24.0,
        bottom_pt=18.0,
        width_pt=180.0,
        height_pt=48.0,
        enabled=True,
    )


def test_coordinator_load_uses_placement_defaults_when_rect_missing(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    workflow.set_signature_appearance(build_signature_appearance())
    workflow.signature_placement_defaults = SignaturePlacementDefaults(
        width_pt=96.0,
        height_pt=36.0,
    )
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=workflow,
        certificate_catalog=build_certificate_catalog(),
        preset_catalog=build_signature_preset_catalog(),
    )

    state = coordinator.load()

    assert state.visible_signature_setup_draft.placement == VisibleSignaturePlacementDraft(
        page_number=1,
        left_pt=24.0,
        bottom_pt=18.0,
        width_pt=96.0,
        height_pt=36.0,
        enabled=False,
    )


def test_coordinator_load_keeps_warning_only_control_issue_ready(tmp_path: Path) -> None:
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=_ready_workflow(tmp_path),
        certificate_catalog=build_certificate_catalog(),
        preset_catalog=build_signature_preset_catalog(),
    )

    state = coordinator.load(
        control_issue=SigningDraftValidationIssue(
            code="preview_warning",
            message="Preview is stale but still usable.",
            field_name="signature_appearance",
            severity=SigningDraftValidationSeverity.WARNING,
        )
    )

    assert state.ready_to_sign is True
    assert state.validation_text == "Ready to sign."


def test_coordinator_apply_visible_signature_setup_updates_workflow_and_clears_preset(
    tmp_path: Path,
) -> None:
    workflow = _ready_workflow(tmp_path)
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=workflow,
        certificate_catalog=build_certificate_catalog(),
        preset_catalog=build_signature_preset_catalog(),
    )
    coordinator.reconcile(ApplySignaturePreset(selected_name="Compact"))
    updated_appearance = build_signature_appearance(
        signer_label_prefix="Signed by Current Draft",
        show_field_names=True,
    )

    state = coordinator.reconcile(
        ApplyVisibleSignatureSetup(
            draft=VisibleSignatureSetupDraft(
                appearance=updated_appearance,
                placement=VisibleSignaturePlacementDraft(
                    page_number=2,
                    left_pt=40.0,
                    bottom_pt=22.0,
                    width_pt=200.0,
                    height_pt=54.0,
                    enabled=True,
                ),
            )
        )
    )

    assert workflow.signature_appearance == updated_appearance
    assert workflow.signature_rect == SignatureRect(
        page_index=1,
        left_pt=40.0,
        bottom_pt=22.0,
        width_pt=200.0,
        height_pt=54.0,
    )
    assert workflow.selected_signature_preset_id is None
    assert state.selected_signature_preset_name is None
    assert state.visible_signature_setup_draft.placement.enabled is True


def test_coordinator_set_signature_appearance_updates_workflow_and_clears_preset(
    tmp_path: Path,
) -> None:
    workflow = _ready_workflow(tmp_path)
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=workflow,
        certificate_catalog=build_certificate_catalog(),
        preset_catalog=build_signature_preset_catalog(),
    )
    coordinator.reconcile(ApplySignaturePreset(selected_name="Compact"))
    updated_appearance = build_signature_appearance(
        signer_label_prefix="Programmatic Boundary",
        show_field_names=True,
    )

    state = coordinator.set_signature_appearance(updated_appearance)

    assert workflow.signature_appearance == updated_appearance
    assert workflow.selected_signature_preset_id is None
    assert state.selected_signature_preset_name is None
    assert state.visible_signature_setup_draft.appearance == updated_appearance


def test_coordinator_reconcile_set_signature_appearance_updates_workflow_and_clears_preset(
    tmp_path: Path,
) -> None:
    workflow = _ready_workflow(tmp_path)
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=workflow,
        certificate_catalog=build_certificate_catalog(),
        preset_catalog=build_signature_preset_catalog(),
    )
    coordinator.reconcile(ApplySignaturePreset(selected_name="Compact"))
    updated_appearance = build_signature_appearance(
        signer_label_prefix="Command Path",
        show_field_names=False,
    )

    state = coordinator.reconcile(
        SetSignatureAppearance(signature_appearance=updated_appearance)
    )

    assert workflow.signature_appearance == updated_appearance
    assert workflow.selected_signature_preset_id is None
    assert state.selected_signature_preset_name is None
    assert state.visible_signature_setup_draft.appearance == updated_appearance


def test_coordinator_set_signature_appearance_preserves_control_issue_folding(
    tmp_path: Path,
) -> None:
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=_ready_workflow(tmp_path),
        certificate_catalog=build_certificate_catalog(),
        preset_catalog=build_signature_preset_catalog(),
    )

    state = coordinator.set_signature_appearance(
        build_signature_appearance(
            signer_label_prefix="Control Issue",
            show_field_names=True,
        ),
        control_issue=SigningDraftValidationIssue(
            code="preview_warning",
            message="Preview is stale but still usable.",
            field_name="signature_appearance",
            severity=SigningDraftValidationSeverity.WARNING,
        ),
    )

    assert state.ready_to_sign is True
    assert state.validation_text == "Ready to sign."


def test_coordinator_reports_certificate_configuration_name_for_preset(
    tmp_path: Path,
) -> None:
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=_ready_workflow(tmp_path),
        certificate_catalog=build_certificate_catalog(),
        preset_catalog=build_signature_preset_catalog(
            profiles=(
                build_signature_preset(
                    name="Certificate Backed",
                    certificate_configuration_id="cert-config-default",
                ),
                build_signature_preset(name="Compact"),
                build_signature_preset(
                    name="Broken Certificate Link",
                    certificate_configuration_id="cert-config-missing",
                ),
            )
        ),
    )

    assert coordinator.certificate_configuration_name_for_preset("Certificate Backed") == (
        "Corporate Records Signing"
    )
    assert coordinator.certificate_configuration_name_for_preset("Compact") is None
    assert coordinator.certificate_configuration_name_for_preset("Broken Certificate Link") is None
    assert coordinator.certificate_configuration_name_for_preset("Missing") is None


def test_coordinator_apply_visible_setup_wrapper_updates_workflow_and_state(
    tmp_path: Path,
) -> None:
    workflow = _ready_workflow(tmp_path)
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=workflow,
        certificate_catalog=build_certificate_catalog(),
        preset_catalog=build_signature_preset_catalog(),
    )
    coordinator.reconcile(ApplySignaturePreset(selected_name="Compact"))
    updated_appearance = build_signature_appearance(
        signer_label_prefix="Signed by Wrapper",
        show_field_names=True,
    )

    state = coordinator.apply_visible_setup(
        VisibleSignatureSetupDraft(
            appearance=updated_appearance,
            placement=VisibleSignaturePlacementDraft(
                page_number=3,
                left_pt=44.0,
                bottom_pt=28.0,
                width_pt=190.0,
                height_pt=52.0,
                enabled=True,
            ),
        )
    )

    assert workflow.signature_appearance == updated_appearance
    assert workflow.signature_rect == SignatureRect(
        page_index=2,
        left_pt=44.0,
        bottom_pt=28.0,
        width_pt=190.0,
        height_pt=52.0,
    )
    assert workflow.selected_signature_preset_id is None
    assert state.selected_signature_preset_name is None
    assert state.visible_signature_setup_draft.placement == VisibleSignaturePlacementDraft(
        page_number=3,
        left_pt=44.0,
        bottom_pt=28.0,
        width_pt=190.0,
        height_pt=52.0,
        enabled=True,
    )


def test_coordinator_apply_visible_setup_wrapper_preserves_control_issue_folding(
    tmp_path: Path,
) -> None:
    workflow = _ready_workflow(tmp_path)
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=workflow,
        certificate_catalog=build_certificate_catalog(),
        preset_catalog=build_signature_preset_catalog(),
    )

    state = coordinator.apply_visible_setup(
        VisibleSignatureSetupDraft(
            appearance=build_signature_appearance(),
            placement=VisibleSignaturePlacementDraft(
                page_number=1,
                left_pt=24.0,
                bottom_pt=18.0,
                width_pt=180.0,
                height_pt=48.0,
                enabled=True,
            ),
        ),
        control_issue=SigningDraftValidationIssue(
            code="preview_warning",
            message="Preview is stale but still usable.",
            field_name="signature_appearance",
            severity=SigningDraftValidationSeverity.WARNING,
        ),
    )

    assert state.ready_to_sign is True
    assert state.validation_text == "Ready to sign."


def test_coordinator_apply_visible_signature_setup_keeps_rect_empty_when_disabled(
    tmp_path: Path,
) -> None:
    workflow = _workflow(tmp_path)
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=workflow,
        certificate_catalog=build_certificate_catalog(),
        preset_catalog=build_signature_preset_catalog(),
    )
    draft = VisibleSignatureSetupDraft(
        appearance=build_signature_appearance(),
        placement=VisibleSignaturePlacementDraft(
            page_number=3,
            left_pt=50.0,
            bottom_pt=30.0,
            width_pt=120.0,
            height_pt=40.0,
            enabled=False,
        ),
    )

    state = coordinator.reconcile(ApplyVisibleSignatureSetup(draft=draft))

    assert workflow.signature_appearance == draft.appearance
    assert workflow.signature_rect is None
    assert state.visible_signature_setup_draft.placement.enabled is False
    assert state.ready_to_sign is False


def test_coordinator_applies_certificate_configuration_and_updates_workflow(
    tmp_path: Path,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    catalog = build_certificate_catalog()
    store.save_catalog(catalog)
    managed_cert = catalog.managed_certificates[0]
    cert_file = store.managed_certificate_dir / managed_cert.storage_filename
    cert_file.parent.mkdir(parents=True, exist_ok=True)
    cert_file.write_bytes(b"pkcs12-bytes")
    workflow = _workflow(tmp_path)
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=workflow,
        certificate_catalog_store=store,
        preset_catalog=build_signature_preset_catalog(),
    )

    state = coordinator.reconcile(
        ApplyCertificateConfiguration(
            selected_name="Corporate Records Signing",
            passphrase="typed-secret",
        )
    )

    assert state.selected_certificate_configuration_name == "Corporate Records Signing"
    assert workflow.selected_certificate_configuration_id == "cert-config-default"
    assert workflow.certificate_path == str(cert_file)
    assert workflow.passphrase == "typed-secret"


def test_coordinator_apply_certificate_configuration_wrapper_updates_workflow(
    tmp_path: Path,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    catalog = build_certificate_catalog()
    store.save_catalog(catalog)
    managed_cert = catalog.managed_certificates[0]
    cert_file = store.managed_certificate_dir / managed_cert.storage_filename
    cert_file.parent.mkdir(parents=True, exist_ok=True)
    cert_file.write_bytes(b"pkcs12-bytes")
    workflow = _workflow(tmp_path)
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=workflow,
        certificate_catalog_store=store,
        preset_catalog=build_signature_preset_catalog(),
    )

    state = coordinator.apply_certificate_configuration(
        "Corporate Records Signing",
        passphrase="typed-secret",
    )

    assert state.selected_certificate_configuration_name == "Corporate Records Signing"
    assert workflow.selected_certificate_configuration_id == "cert-config-default"
    assert workflow.certificate_path == str(cert_file)
    assert workflow.passphrase == "typed-secret"


def test_coordinator_applies_certificate_configuration_with_saved_password(
    tmp_path: Path,
) -> None:
    configuration = build_certificate_configuration(
        save_password=True,
        password_secret_ref="secret-ref-1",
    )
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    catalog = build_certificate_catalog(certificate_configurations=(configuration,))
    store.save_catalog(catalog)
    managed_cert = catalog.managed_certificates[0]
    cert_file = store.managed_certificate_dir / managed_cert.storage_filename
    cert_file.parent.mkdir(parents=True, exist_ok=True)
    cert_file.write_bytes(b"pkcs12-bytes")
    workflow = _workflow(tmp_path)
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=workflow,
        certificate_catalog_store=store,
        certificate_secret_provider=_FakeSecretProvider({"secret-ref-1": "stored-secret"}),
        preset_catalog=build_signature_preset_catalog(),
    )

    state = coordinator.reconcile(
        ApplyCertificateConfiguration(selected_name="Corporate Records Signing")
    )

    assert state.selected_certificate_configuration_name == "Corporate Records Signing"
    assert workflow.selected_certificate_configuration_id == "cert-config-default"
    assert workflow.certificate_path == str(cert_file)
    assert workflow.passphrase == "stored-secret"


def test_coordinator_apply_certificate_configuration_wrapper_uses_saved_password(
    tmp_path: Path,
) -> None:
    configuration = build_certificate_configuration(
        save_password=True,
        password_secret_ref="secret-ref-1",
    )
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    catalog = build_certificate_catalog(certificate_configurations=(configuration,))
    store.save_catalog(catalog)
    managed_cert = catalog.managed_certificates[0]
    cert_file = store.managed_certificate_dir / managed_cert.storage_filename
    cert_file.parent.mkdir(parents=True, exist_ok=True)
    cert_file.write_bytes(b"pkcs12-bytes")
    workflow = _workflow(tmp_path)
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=workflow,
        certificate_catalog_store=store,
        certificate_secret_provider=_FakeSecretProvider({"secret-ref-1": "stored-secret"}),
        preset_catalog=build_signature_preset_catalog(),
    )

    state = coordinator.apply_certificate_configuration("Corporate Records Signing")

    assert state.selected_certificate_configuration_name == "Corporate Records Signing"
    assert workflow.selected_certificate_configuration_id == "cert-config-default"
    assert workflow.certificate_path == str(cert_file)
    assert workflow.passphrase == "stored-secret"


def test_coordinator_apply_certificate_configuration_wrapper_preserves_control_issue_folding(
    tmp_path: Path,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    catalog = build_certificate_catalog()
    store.save_catalog(catalog)
    managed_cert = catalog.managed_certificates[0]
    cert_file = store.managed_certificate_dir / managed_cert.storage_filename
    cert_file.parent.mkdir(parents=True, exist_ok=True)
    cert_file.write_bytes(b"pkcs12-bytes")
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=_ready_workflow(tmp_path),
        certificate_catalog_store=store,
        preset_catalog=build_signature_preset_catalog(),
    )

    state = coordinator.apply_certificate_configuration(
        "Corporate Records Signing",
        passphrase="typed-secret",
        control_issue=SigningDraftValidationIssue(
            code="preview_warning",
            message="Preview is stale but still usable.",
            field_name="signature_appearance",
            severity=SigningDraftValidationSeverity.WARNING,
        ),
    )

    assert state.selected_certificate_configuration_name == "Corporate Records Signing"
    assert state.ready_to_sign is False
    assert "preview_warning" not in state.validation_text


def test_coordinator_apply_certificate_configuration_reports_missing_file(
    tmp_path: Path,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    store.save_catalog(build_certificate_catalog())
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=_workflow(tmp_path),
        certificate_catalog_store=store,
        preset_catalog=build_signature_preset_catalog(),
    )

    with pytest.raises(
        SignaturePropertiesCoordinatorError,
        match="managed certificate file is missing",
    ):
        coordinator.reconcile(
            ApplyCertificateConfiguration(
                selected_name="Corporate Records Signing",
                passphrase="typed-secret",
            )
        )


def test_coordinator_apply_certificate_configuration_wrapper_reports_missing_file(
    tmp_path: Path,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    store.save_catalog(build_certificate_catalog())
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=_workflow(tmp_path),
        certificate_catalog_store=store,
        preset_catalog=build_signature_preset_catalog(),
    )

    with pytest.raises(
        SignaturePropertiesCoordinatorError,
        match="managed certificate file is missing",
    ):
        coordinator.apply_certificate_configuration(
            "Corporate Records Signing",
            passphrase="typed-secret",
        )


def test_coordinator_applies_preset_without_certificate_and_preserves_active_certificate(
    tmp_path: Path,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    catalog = build_certificate_catalog()
    store.save_catalog(catalog)
    managed_cert = catalog.managed_certificates[0]
    cert_file = store.managed_certificate_dir / managed_cert.storage_filename
    cert_file.parent.mkdir(parents=True, exist_ok=True)
    cert_file.write_bytes(b"pkcs12-bytes")
    workflow = _workflow(tmp_path)
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=workflow,
        certificate_catalog_store=store,
        preset_catalog=build_signature_preset_catalog(
            profiles=(
                build_signature_preset(name="Compact"),
            )
        ),
    )
    coordinator.reconcile(
        ApplyCertificateConfiguration(
            selected_name="Corporate Records Signing",
            passphrase="typed-secret",
        )
    )

    state = coordinator.reconcile(
        ApplySignaturePreset(
            selected_name="Compact",
            passphrase="should-not-be-used",
        )
    )

    assert state.selected_signature_preset_name == "Compact"
    assert workflow.selected_certificate_configuration_id == "cert-config-default"
    assert workflow.certificate_path == str(cert_file)
    assert workflow.passphrase == "typed-secret"


def test_coordinator_apply_signature_preset_wrapper_preserves_active_certificate(
    tmp_path: Path,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    catalog = build_certificate_catalog()
    store.save_catalog(catalog)
    managed_cert = catalog.managed_certificates[0]
    cert_file = store.managed_certificate_dir / managed_cert.storage_filename
    cert_file.parent.mkdir(parents=True, exist_ok=True)
    cert_file.write_bytes(b"pkcs12-bytes")
    workflow = _workflow(tmp_path)
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=workflow,
        certificate_catalog_store=store,
        preset_catalog=build_signature_preset_catalog(
            profiles=(build_signature_preset(name="Compact"),)
        ),
    )
    coordinator.reconcile(
        ApplyCertificateConfiguration(
            selected_name="Corporate Records Signing",
            passphrase="typed-secret",
        )
    )

    state = coordinator.apply_signature_preset(
        "Compact",
        passphrase="should-not-be-used",
    )

    assert state.selected_signature_preset_name == "Compact"
    assert workflow.selected_certificate_configuration_id == "cert-config-default"
    assert workflow.certificate_path == str(cert_file)
    assert workflow.passphrase == "typed-secret"


def test_coordinator_apply_signature_preset_wrapper_preserves_control_issue_folding(
    tmp_path: Path,
) -> None:
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=_ready_workflow(tmp_path),
        certificate_catalog=build_certificate_catalog(),
        preset_catalog=build_signature_preset_catalog(),
    )

    state = coordinator.apply_signature_preset(
        "Compact",
        control_issue=SigningDraftValidationIssue(
            code="preview_warning",
            message="Preview is stale but still usable.",
            field_name="signature_appearance",
            severity=SigningDraftValidationSeverity.WARNING,
        ),
    )

    assert state.selected_signature_preset_name == "Compact"
    assert state.ready_to_sign is True
    assert state.validation_text == (
        "Selected preset 'Compact' does not define a certificate; "
        "choose a certificate configuration before signing.\nReady to sign."
    )


def test_coordinator_apply_signature_preset_wrapper_applies_certificate_material(
    tmp_path: Path,
) -> None:
    default_certificate = build_managed_certificate(
        managed_certificate_id="managed-cert-default",
        display_name="Default Certificate",
        storage_filename="default.p12",
    )
    alternate_certificate = build_managed_certificate(
        managed_certificate_id="managed-cert-alt",
        display_name="Alternate Certificate",
        storage_filename="alternate.p12",
    )
    certificate_store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    certificate_store.save_catalog(
        build_certificate_catalog(
            managed_certificates=(default_certificate, alternate_certificate),
            certificate_configurations=(
                build_certificate_configuration(
                    certificate_configuration_id="cert-config-default",
                    display_name="Default Signing",
                    managed_certificate_id="managed-cert-default",
                ),
                build_certificate_configuration(
                    certificate_configuration_id="cert-config-alt",
                    display_name="Alternate Signing",
                    managed_certificate_id="managed-cert-alt",
                ),
            ),
        )
    )
    default_path = certificate_store.managed_certificate_dir / "default.p12"
    alternate_path = certificate_store.managed_certificate_dir / "alternate.p12"
    default_path.parent.mkdir(parents=True, exist_ok=True)
    default_path.write_bytes(b"default-pkcs12")
    alternate_path.write_bytes(b"alternate-pkcs12")

    preset = build_signature_preset(
        name="Alternate Preset",
        certificate_configuration_id="cert-config-alt",
    )
    workflow = _workflow(tmp_path)
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=workflow,
        certificate_catalog_store=certificate_store,
        preset_catalog=build_signature_preset_catalog(profiles=(preset,)),
    )
    coordinator.reconcile(
        ApplyCertificateConfiguration(
            selected_name="Default Signing",
            passphrase="default-secret",
        )
    )

    state = coordinator.apply_signature_preset(
        "Alternate Preset",
        passphrase="alternate-secret",
    )

    assert state.selected_signature_preset_name == "Alternate Preset"
    assert state.selected_certificate_configuration_name == "Alternate Signing"
    assert workflow.selected_certificate_configuration_id == "cert-config-alt"
    assert workflow.certificate_path == str(alternate_path)
    assert workflow.passphrase == "alternate-secret"
    assert workflow.selected_signature_preset_id == "preset-alternate-preset"
    assert workflow.selected_appearance_profile_id == "appearance-alternate-preset"
    assert workflow.selected_placement_profile_id == "placement-alternate-preset"


def test_coordinator_applies_preset_with_certificate_material(tmp_path: Path) -> None:
    default_certificate = build_managed_certificate(
        managed_certificate_id="managed-cert-default",
        display_name="Default Certificate",
        storage_filename="default.p12",
    )
    alternate_certificate = build_managed_certificate(
        managed_certificate_id="managed-cert-alt",
        display_name="Alternate Certificate",
        storage_filename="alternate.p12",
    )
    certificate_store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    certificate_store.save_catalog(
        build_certificate_catalog(
            managed_certificates=(default_certificate, alternate_certificate),
            certificate_configurations=(
                build_certificate_configuration(
                    certificate_configuration_id="cert-config-default",
                    display_name="Default Signing",
                    managed_certificate_id="managed-cert-default",
                ),
                build_certificate_configuration(
                    certificate_configuration_id="cert-config-alt",
                    display_name="Alternate Signing",
                    managed_certificate_id="managed-cert-alt",
                ),
            ),
        )
    )
    default_path = certificate_store.managed_certificate_dir / "default.p12"
    alternate_path = certificate_store.managed_certificate_dir / "alternate.p12"
    default_path.parent.mkdir(parents=True, exist_ok=True)
    default_path.write_bytes(b"default-pkcs12")
    alternate_path.write_bytes(b"alternate-pkcs12")

    preset = build_signature_preset(
        name="Alternate Preset",
        certificate_configuration_id="cert-config-alt",
    )
    workflow = _workflow(tmp_path)
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=workflow,
        certificate_catalog_store=certificate_store,
        preset_catalog=build_signature_preset_catalog(profiles=(preset,)),
    )
    coordinator.reconcile(
        ApplyCertificateConfiguration(
            selected_name="Default Signing",
            passphrase="default-secret",
        )
    )

    state = coordinator.reconcile(
        ApplySignaturePreset(
            selected_name="Alternate Preset",
            passphrase="alternate-secret",
        )
    )

    assert state.selected_signature_preset_name == "Alternate Preset"
    assert state.selected_certificate_configuration_name == "Alternate Signing"
    assert workflow.selected_certificate_configuration_id == "cert-config-alt"
    assert workflow.certificate_path == str(alternate_path)
    assert workflow.passphrase == "alternate-secret"


def test_coordinator_save_current_preset_persists_and_selects_it(
    tmp_path: Path,
) -> None:
    class _NoSavePresetStore(SignaturePresetCatalogStore):
        def save_preset(self, _preset):  # type: ignore[override]
            raise AssertionError("coordinator save path should not call store save_preset helper")

    store = _NoSavePresetStore(storage_dir=tmp_path / PROFILE_DIRECTORY_NAME)
    workflow = _ready_workflow(tmp_path)
    workflow.selected_certificate_configuration_id = "cert-config-default"

    def _fail_capture(_name: str, **_kwargs) -> None:
        raise AssertionError("coordinator save path should not call workflow capture helper")

    workflow.capture_current_signature_setup = _fail_capture  # type: ignore[method-assign]
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=workflow,
        certificate_catalog=CertificateCatalog(schema_version=1),
        preset_catalog_store=store,
    )

    state = coordinator.reconcile(SaveCurrentPreset(name="Team Standard"))
    saved = store.load_catalog().preset_named("Team Standard")

    assert state.selected_signature_preset_name == "Team Standard"
    assert "Team Standard" in store.load_catalog().preset_names()
    assert saved.appearance == workflow.current_signature_appearance
    assert saved.placement_defaults == SignaturePlacementDefaults(
        width_pt=180.0,
        height_pt=48.0,
    )
    assert saved.preset.certificate_configuration_id == "cert-config-default"


def test_coordinator_save_current_appearance_profile_persists_without_mutating_workflow(
    tmp_path: Path,
) -> None:
    store = SignaturePresetCatalogStore(storage_dir=tmp_path / PROFILE_DIRECTORY_NAME)
    workflow = _ready_workflow(tmp_path)
    original_rect = workflow.signature_rect
    original_certificate_id = workflow.selected_certificate_configuration_id
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=workflow,
        certificate_catalog=CertificateCatalog(schema_version=1),
        preset_catalog_store=store,
    )

    state = coordinator.reconcile(
        SaveCurrentAppearanceProfile(name="Contract approval")
    )

    saved = store.load_catalog().appearance_profile_named("Contract approval")
    assert saved.appearance == workflow.current_signature_appearance
    assert workflow.signature_rect == original_rect
    assert workflow.selected_certificate_configuration_id == original_certificate_id
    assert state.selected_signature_preset_name is None


def test_coordinator_save_current_appearance_profile_rejects_blank_and_duplicate_names(
    tmp_path: Path,
) -> None:
    store = SignaturePresetCatalogStore(storage_dir=tmp_path / PROFILE_DIRECTORY_NAME)
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=_ready_workflow(tmp_path),
        certificate_catalog=CertificateCatalog(schema_version=1),
        preset_catalog_store=store,
    )

    with pytest.raises(SignaturePropertiesCoordinatorError, match="name is required"):
        coordinator.reconcile(SaveCurrentAppearanceProfile(name="  "))

    coordinator.reconcile(SaveCurrentAppearanceProfile(name="Contract approval"))
    with pytest.raises(SignaturePropertiesCoordinatorError, match="already exists"):
        coordinator.reconcile(SaveCurrentAppearanceProfile(name="Contract approval"))


def test_coordinator_save_current_placement_profile_persists_rectangle_as_current_page(
    tmp_path: Path,
) -> None:
    store = SignaturePresetCatalogStore(storage_dir=tmp_path / PROFILE_DIRECTORY_NAME)
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=_ready_workflow(tmp_path),
        certificate_catalog=CertificateCatalog(schema_version=1),
        preset_catalog_store=store,
    )

    coordinator.reconcile(
        SaveCurrentPlacementProfile(
            name="Bottom right",
            placement=VisibleSignaturePlacementDraft(
                page_number=9,
                left_pt=11.0,
                bottom_pt=12.0,
                width_pt=130.0,
                height_pt=44.0,
                enabled=True,
            ),
        )
    )

    saved = store.load_catalog().placement_profile_named("Bottom right")
    assert saved.page_selection_mode == "current_page"
    assert saved.rect.left_pt == 11.0
    assert saved.rect.bottom_pt == 12.0
    assert saved.rect.width_pt == 130.0
    assert saved.rect.height_pt == 44.0


def test_coordinator_save_current_placement_profile_rejects_disabled_placement(
    tmp_path: Path,
) -> None:
    store = SignaturePresetCatalogStore(storage_dir=tmp_path / PROFILE_DIRECTORY_NAME)
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=_workflow(tmp_path),
        certificate_catalog=CertificateCatalog(schema_version=1),
        preset_catalog_store=store,
    )

    with pytest.raises(SignaturePropertiesCoordinatorError, match="Place a signature"):
        coordinator.reconcile(
            SaveCurrentPlacementProfile(
                name="Bottom right",
                placement=VisibleSignaturePlacementDraft(
                    page_number=1,
                    left_pt=11.0,
                    bottom_pt=12.0,
                    width_pt=130.0,
                    height_pt=44.0,
                    enabled=False,
                ),
            )
        )


def test_coordinator_delete_preset_removes_it_and_clears_selection(tmp_path: Path) -> None:
    store = SignaturePresetCatalogStore(storage_dir=tmp_path / PROFILE_DIRECTORY_NAME)
    store.save_catalog(build_signature_preset_catalog())
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=_workflow(tmp_path),
        certificate_catalog=CertificateCatalog(schema_version=1),
        preset_catalog_store=store,
    )
    coordinator.reconcile(ApplySignaturePreset(selected_name="Compact"))

    state = coordinator.reconcile(DeletePreset(name="Compact"))

    assert state.selected_signature_preset_name is None
    assert state.signature_preset_names == ("Default",)
    assert store.load_catalog().preset_names() == ("Default",)


def test_coordinator_refresh_catalogs_drops_stale_selection(tmp_path: Path) -> None:
    certificate_store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    certificate_catalog = build_certificate_catalog()
    certificate_store.save_catalog(certificate_catalog)
    managed_cert = certificate_catalog.managed_certificates[0]
    cert_file = certificate_store.managed_certificate_dir / managed_cert.storage_filename
    cert_file.parent.mkdir(parents=True, exist_ok=True)
    cert_file.write_bytes(b"pkcs12-bytes")
    preset_store = SignaturePresetCatalogStore(storage_dir=tmp_path / PROFILE_DIRECTORY_NAME)
    preset_store.save_catalog(build_signature_preset_catalog())
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=_workflow(tmp_path),
        certificate_catalog_store=certificate_store,
        preset_catalog_store=preset_store,
    )
    coordinator.reconcile(
        ApplyCertificateConfiguration(
            selected_name="Corporate Records Signing",
            passphrase="typed-secret",
        )
    )
    coordinator.reconcile(ApplySignaturePreset(selected_name="Compact"))

    certificate_store.save_catalog(CertificateCatalog(schema_version=1))
    preset_store.save_catalog(SignaturePresetCatalog(schema_version=1))

    state = coordinator.reconcile(RefreshCatalogs())

    assert state.selected_certificate_configuration_name is None
    assert state.selected_signature_preset_name is None
    assert state.certificate_configuration_names == ()
    assert state.signature_preset_names == ()
