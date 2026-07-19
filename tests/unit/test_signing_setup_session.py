from pathlib import Path
from types import SimpleNamespace

from foliaseal.application.signature_properties_coordinator import (
    DefaultSignaturePropertiesCoordinator,
    SignaturePropertiesCoordinatorError,
    SignaturePropertiesViewState,
    VisibleSignaturePlacementDraft,
    VisibleSignatureSetupDraft,
)
from foliaseal.application.signing_setup_session import SigningSetupSession
from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
from tests.support.phase3_builders import (
    build_certificate_catalog,
    build_certificate_configuration,
    build_managed_certificate,
    build_signature_appearance,
    build_signature_preset,
    build_signature_preset_catalog,
)
from tests.unit.test_signature_properties_coordinator import (
    _FakeSecretProvider,
    _ready_workflow,
    _workflow,
)


class _FakePrompter:
    def __init__(self, responses: list[str | None]) -> None:
        self._responses = list(responses)
        self.calls: list[str] = []

    def prompt(self, label: str) -> str | None:
        self.calls.append(label)
        return self._responses.pop(0) if self._responses else None


class _WorkflowAccessExplodes:
    def set_signature_appearance(self, _signature_appearance) -> None:
        raise AssertionError("SigningSetupSession should not mutate coordinator.workflow directly.")


class _FakeCoordinatorForAppearanceDelegation:
    def __init__(self, returned_state: SignaturePropertiesViewState) -> None:
        self.workflow = _WorkflowAccessExplodes()
        self.returned_state = returned_state
        self.calls: list[tuple[object, object | None]] = []

    def set_signature_appearance(
        self,
        signature_appearance,
        *,
        control_issue=None,
    ) -> SignaturePropertiesViewState:
        self.calls.append((signature_appearance, control_issue))
        return self.returned_state


def test_signing_setup_session_retries_certificate_selection_and_caches_passphrase(
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
        workflow=_workflow(tmp_path),
        certificate_catalog_store=store,
        preset_catalog=build_signature_preset_catalog(),
    )
    prompter = _FakePrompter(["typed-secret"])
    session = SigningSetupSession(
        coordinator=coordinator,
        passphrase_prompter=prompter,
    )

    first_state = session.select_certificate_configuration("Corporate Records Signing")
    second_state = session.select_certificate_configuration("Corporate Records Signing")

    assert first_state.applied is True
    assert second_state.applied is True
    assert first_state.state.selected_certificate_configuration_name == "Corporate Records Signing"
    assert coordinator.workflow.selected_certificate_configuration_id == "cert-config-default"
    assert coordinator.workflow.certificate_path == str(cert_file)
    assert coordinator.workflow.passphrase == "typed-secret"
    assert prompter.calls == ["Enter the certificate password for 'Corporate Records Signing'."]


def test_signing_setup_session_returns_none_when_certificate_prompt_is_canceled(
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
        workflow=_workflow(tmp_path),
        certificate_catalog_store=store,
        preset_catalog=build_signature_preset_catalog(),
    )
    session = SigningSetupSession(
        coordinator=coordinator,
        passphrase_prompter=_FakePrompter([None]),
    )

    state = session.select_certificate_configuration("Corporate Records Signing")

    assert state.applied is False
    assert state.state.selected_certificate_configuration_name is None
    assert coordinator.workflow.selected_certificate_configuration_id is None


def test_signing_setup_session_uses_saved_secret_without_prompt(
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
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=_workflow(tmp_path),
        certificate_catalog_store=store,
        certificate_secret_provider=_FakeSecretProvider({"secret-ref-1": "stored-secret"}),
        preset_catalog=build_signature_preset_catalog(),
    )
    prompter = _FakePrompter([])
    session = SigningSetupSession(
        coordinator=coordinator,
        passphrase_prompter=prompter,
    )

    state = session.select_certificate_configuration("Corporate Records Signing")

    assert state.applied is True
    assert state.state.selected_certificate_configuration_name == "Corporate Records Signing"
    assert coordinator.workflow.passphrase == "stored-secret"
    assert prompter.calls == []


def test_signing_setup_session_applies_partial_preset_without_prompting_or_changing_certificate(
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
        workflow=_workflow(tmp_path),
        certificate_catalog_store=store,
        preset_catalog=build_signature_preset_catalog(
            profiles=(build_signature_preset(name="Compact"),)
        ),
    )
    prompter = _FakePrompter(["typed-secret"])
    session = SigningSetupSession(
        coordinator=coordinator,
        passphrase_prompter=prompter,
    )
    initial_state = session.select_certificate_configuration("Corporate Records Signing")

    state = session.select_signature_preset("Compact")

    assert initial_state.applied is True
    assert state.applied is True
    assert state.state.selected_signature_preset_name == "Compact"
    assert coordinator.workflow.selected_certificate_configuration_id == "cert-config-default"
    assert coordinator.workflow.certificate_path == str(cert_file)
    assert prompter.calls == ["Enter the certificate password for 'Corporate Records Signing'."]


def test_signing_setup_session_retries_preset_certificate_selection_and_caches_passphrase(
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
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    store.save_catalog(
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
    default_path = store.managed_certificate_dir / "default.p12"
    alternate_path = store.managed_certificate_dir / "alternate.p12"
    default_path.parent.mkdir(parents=True, exist_ok=True)
    default_path.write_bytes(b"default-pkcs12")
    alternate_path.write_bytes(b"alternate-pkcs12")
    preset = build_signature_preset(
        name="Alternate Preset",
        certificate_configuration_id="cert-config-alt",
    )
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=_workflow(tmp_path),
        certificate_catalog_store=store,
        preset_catalog=build_signature_preset_catalog(profiles=(preset,)),
    )
    prompter = _FakePrompter(["alternate-secret"])
    session = SigningSetupSession(
        coordinator=coordinator,
        passphrase_prompter=prompter,
    )

    first_state = session.select_signature_preset("Alternate Preset")
    second_state = session.select_signature_preset("Alternate Preset")

    assert first_state.applied is True
    assert second_state.applied is True
    assert first_state.state.selected_signature_preset_name == "Alternate Preset"
    assert first_state.state.selected_certificate_configuration_name == "Alternate Signing"
    assert coordinator.workflow.selected_certificate_configuration_id == "cert-config-alt"
    assert coordinator.workflow.certificate_path == str(alternate_path)
    assert coordinator.workflow.passphrase == "alternate-secret"
    assert prompter.calls == ["Enter the certificate password for 'Alternate Signing'."]


def test_signing_setup_session_returns_explicit_noop_when_preset_prompt_is_canceled(
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
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    store.save_catalog(
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
    default_path = store.managed_certificate_dir / "default.p12"
    alternate_path = store.managed_certificate_dir / "alternate.p12"
    default_path.parent.mkdir(parents=True, exist_ok=True)
    default_path.write_bytes(b"default-pkcs12")
    alternate_path.write_bytes(b"alternate-pkcs12")
    preset = build_signature_preset(
        name="Alternate Preset",
        certificate_configuration_id="cert-config-alt",
    )
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=_workflow(tmp_path),
        certificate_catalog_store=store,
        preset_catalog=build_signature_preset_catalog(profiles=(preset,)),
    )
    session = SigningSetupSession(
        coordinator=coordinator,
        passphrase_prompter=_FakePrompter([None]),
    )

    outcome = session.select_signature_preset("Alternate Preset")

    assert outcome.applied is False
    assert outcome.state.selected_signature_preset_name is None
    assert outcome.state.selected_certificate_configuration_name is None
    assert coordinator.workflow.selected_certificate_configuration_id is None
    assert coordinator.workflow.certificate_path == str(tmp_path / "cert.p12")


def test_signing_setup_session_applies_visible_setup_and_clears_selected_preset(
    tmp_path: Path,
) -> None:
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=_ready_workflow(tmp_path),
        certificate_catalog=build_certificate_catalog(),
        preset_catalog=build_signature_preset_catalog(),
    )
    session = SigningSetupSession(
        coordinator=coordinator,
        passphrase_prompter=_FakePrompter([]),
    )
    session.select_signature_preset("Compact")
    updated_appearance = build_signature_appearance(
        signer_label_prefix="Signed by Session",
        show_field_names=True,
    )

    state = session.apply_visible_setup(
        VisibleSignatureSetupDraft(
            appearance=updated_appearance,
            placement=VisibleSignaturePlacementDraft(
                page_number=2,
                left_pt=44.0,
                bottom_pt=28.0,
                width_pt=190.0,
                height_pt=52.0,
                enabled=True,
            ),
        )
    )

    assert state.selected_signature_preset_name is None
    assert coordinator.workflow.signature_appearance == updated_appearance


def test_signing_setup_session_set_signature_appearance_clears_selected_preset(
    tmp_path: Path,
) -> None:
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=_ready_workflow(tmp_path),
        certificate_catalog=build_certificate_catalog(),
        preset_catalog=build_signature_preset_catalog(),
    )
    session = SigningSetupSession(
        coordinator=coordinator,
        passphrase_prompter=_FakePrompter([]),
    )
    session.select_signature_preset("Compact")
    updated_appearance = build_signature_appearance(
        signer_label_prefix="Programmatic Session",
        show_field_names=False,
    )

    state = session.set_signature_appearance(updated_appearance)

    assert state.selected_signature_preset_name is None
    assert coordinator.workflow.signature_appearance == updated_appearance


def test_signing_setup_session_set_signature_appearance_delegates_to_coordinator_boundary(
) -> None:
    returned_state = SignaturePropertiesViewState(
        selected_certificate_configuration_name="Corporate Records Signing",
        selected_signature_preset_name=None,
        certificate_configuration_names=("Corporate Records Signing",),
        signature_preset_names=("Default", "Compact"),
        appearance_profile_names=(),
        placement_profile_names=(),
        visible_signature_setup_draft=VisibleSignatureSetupDraft(
            appearance=build_signature_appearance(
                signer_label_prefix="Delegated",
                show_field_names=True,
            ),
            placement=VisibleSignaturePlacementDraft(
                page_number=1,
                left_pt=24.0,
                bottom_pt=18.0,
                width_pt=180.0,
                height_pt=48.0,
                enabled=True,
            ),
        ),
        validation_text="Ready to sign.",
        ready_to_sign=True,
        preview=_ready_workflow(Path("/tmp")).preview(),
    )
    coordinator = _FakeCoordinatorForAppearanceDelegation(returned_state)
    session = SigningSetupSession(
        coordinator=coordinator,  # type: ignore[arg-type]
        passphrase_prompter=_FakePrompter([]),
    )
    updated_appearance = build_signature_appearance(
        signer_label_prefix="Delegated",
        show_field_names=True,
    )
    control_issue = SimpleNamespace(code="issue")

    state = session.set_signature_appearance(
        updated_appearance,
        control_issue=control_issue,  # type: ignore[arg-type]
    )

    assert state is returned_state
    assert coordinator.calls == [(updated_appearance, control_issue)]


def test_signing_setup_session_save_preset_persists_and_selects_it(
    tmp_path: Path,
) -> None:
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=_ready_workflow(tmp_path),
        certificate_catalog=build_certificate_catalog(),
        preset_catalog=build_signature_preset_catalog(),
    )
    session = SigningSetupSession(
        coordinator=coordinator,
        passphrase_prompter=_FakePrompter([]),
    )

    state = session.save_preset("Team Standard")

    assert state.selected_signature_preset_name == "Team Standard"
    assert coordinator.preset_catalog.preset_named("Team Standard").name == "Team Standard"


def test_signing_setup_session_delete_preset_removes_it_and_clears_selection(
    tmp_path: Path,
) -> None:
    coordinator = DefaultSignaturePropertiesCoordinator(
        workflow=_workflow(tmp_path),
        certificate_catalog=build_certificate_catalog(),
        preset_catalog=build_signature_preset_catalog(),
    )
    session = SigningSetupSession(
        coordinator=coordinator,
        passphrase_prompter=_FakePrompter([]),
    )
    session.select_signature_preset("Compact")

    state = session.delete_preset("Compact")

    assert state.selected_signature_preset_name is None
    assert state.signature_preset_names == ("Default",)


def test_signing_setup_session_surfaces_non_promptable_errors(
    tmp_path: Path,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    store.save_catalog(build_certificate_catalog())
    session = SigningSetupSession(
        coordinator=DefaultSignaturePropertiesCoordinator(
            workflow=_workflow(tmp_path),
            certificate_catalog_store=store,
            preset_catalog=build_signature_preset_catalog(),
        ),
        passphrase_prompter=_FakePrompter(["typed-secret"]),
    )

    try:
        session.select_certificate_configuration("Corporate Records Signing")
    except SignaturePropertiesCoordinatorError as exc:
        assert "managed certificate file is missing" in str(exc)
    else:  # pragma: no cover - defensive branch
        raise AssertionError("Expected missing managed certificate file error.")
