from pathlib import Path

from foliaseal.application import CertificateLifecycleService
from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
from foliaseal.presentation.qt.app_frame_certificate_management import (
    AppFrameCertificateDialogService,
)
from tests.support.phase3_builders import (
    build_certificate_catalog,
    build_certificate_configuration,
    build_managed_certificate,
)
from tests.unit.test_certificate_import import _write_test_pkcs12
from tests.unit.test_qt_app_frame import _fake_bindings, _FakeSecretStore


def _build_service(
    tmp_path: Path,
    *,
    secret_store: _FakeSecretStore | None = None,
    refresh_calls: list[str] | None = None,
    certificate_store: CertificateCatalogStore | None = None,
):
    bindings = _fake_bindings()
    store = certificate_store or CertificateCatalogStore(
        storage_dir=tmp_path / "Certificates"
    )
    secrets = secret_store or _FakeSecretStore()
    refresh_log = refresh_calls if refresh_calls is not None else []
    service = AppFrameCertificateDialogService(
        bindings=bindings,
        parent=bindings.q_main_window(),
        lifecycle_service=CertificateLifecycleService(
            store=store,
            secret_store=secrets,
        ),
        refresh_shell_certificate_configurations=lambda: refresh_log.append("refresh"),
    )
    return bindings, store, secrets, refresh_log, service


def test_certificate_creation_dialog_creates_and_refreshes(tmp_path: Path) -> None:
    bindings, certificate_store, _, refresh_log, service = _build_service(tmp_path)

    outcome = service.show_creation_dialog()
    dialog = outcome.compatibility.creation_dialog
    dialog.controls.display_name.setText("Alice Signing")
    dialog.controls.passphrase.setText("correct horse")
    result = dialog.create_certificate()

    assert result is not None
    catalog = certificate_store.load_catalog()
    configuration = catalog.configuration_named("Alice Signing")
    managed_certificate = catalog.managed_certificate_by_id(
        configuration.managed_certificate_id
    )
    assert managed_certificate.source_kind == "created"
    assert managed_certificate.subject_summary.common_name == "Alice Signing"
    assert (
        certificate_store.managed_certificate_dir / managed_certificate.storage_filename
    ).exists()
    assert configuration.save_password is False
    assert configuration.password_secret_ref is None
    assert refresh_log == ["refresh"]
    assert bindings.q_message_box.information_calls[-1][1] == "Certificate created"


def test_certificate_creation_dialog_saves_password_outside_catalog(
    tmp_path: Path,
) -> None:
    secret_store = _FakeSecretStore()
    _, certificate_store, _, _, service = _build_service(
        tmp_path,
        secret_store=secret_store,
    )

    dialog = service.show_creation_dialog().compatibility.creation_dialog
    dialog.controls.display_name.setText("Alice Signing")
    dialog.controls.passphrase.setText("correct horse")
    dialog.controls.save_password.setChecked(True)
    result = dialog.create_certificate()

    assert result is not None
    configuration = certificate_store.load_catalog().configuration_named(
        "Alice Signing"
    )
    assert configuration.save_password is True
    assert configuration.password_secret_ref == "secret://test/" + (
        configuration.certificate_configuration_id
    )
    assert secret_store.secrets[configuration.password_secret_ref] == "correct horse"
    assert "correct horse" not in certificate_store.catalog_path.read_text(
        encoding="utf-8"
    )


def test_certificate_creation_dialog_reports_secure_storage_unavailable(
    tmp_path: Path,
) -> None:
    bindings, certificate_store, _, _, service = _build_service(
        tmp_path,
        secret_store=_FakeSecretStore(available=False),
    )

    dialog = service.show_creation_dialog().compatibility.creation_dialog
    dialog.controls.display_name.setText("Alice Signing")
    dialog.controls.passphrase.setText("correct horse")
    dialog.controls.save_password.setChecked(True)
    result = dialog.create_certificate()

    assert result is None
    assert certificate_store.load_catalog().certificate_configurations == ()
    assert bindings.q_message_box.warning_calls[-1][1] == "Certificate creation error"


def test_certificate_import_dialog_imports_and_refreshes(tmp_path: Path) -> None:
    source = tmp_path / "alice.p12"
    passphrase = "correct horse"
    _write_test_pkcs12(source, passphrase=passphrase, common_name="Alice Example")
    bindings, certificate_store, _, refresh_log, service = _build_service(tmp_path)

    dialog = service.show_import_dialog().compatibility.import_dialog
    dialog.controls.certificate_path.setText(str(source))
    dialog.controls.display_name.setText("Alice Signing")
    dialog.controls.passphrase.setText(passphrase)
    result = dialog.import_certificate()

    assert result is not None
    catalog = certificate_store.load_catalog()
    configuration = catalog.configuration_named("Alice Signing")
    managed_certificate = catalog.managed_certificate_by_id(
        configuration.managed_certificate_id
    )
    assert managed_certificate.subject_summary.common_name == "Alice Example"
    managed_file = certificate_store.managed_certificate_dir / (
        managed_certificate.storage_filename
    )
    assert managed_file.exists()
    assert configuration.save_password is False
    assert configuration.password_secret_ref is None
    assert refresh_log == ["refresh"]
    assert bindings.q_message_box.information_calls[-1][1] == "Certificate imported"


def test_certificate_import_dialog_saves_password_outside_catalog(
    tmp_path: Path,
) -> None:
    source = tmp_path / "alice.p12"
    passphrase = "correct horse"
    _write_test_pkcs12(source, passphrase=passphrase, common_name="Alice Example")
    secret_store = _FakeSecretStore()
    _, certificate_store, _, _, service = _build_service(
        tmp_path,
        secret_store=secret_store,
    )

    dialog = service.show_import_dialog().compatibility.import_dialog
    dialog.controls.certificate_path.setText(str(source))
    dialog.controls.display_name.setText("Alice Signing")
    dialog.controls.passphrase.setText(passphrase)
    dialog.controls.save_password.setChecked(True)
    result = dialog.import_certificate()

    assert result is not None
    configuration = certificate_store.load_catalog().configuration_named(
        "Alice Signing"
    )
    assert configuration.save_password is True
    assert configuration.password_secret_ref == "secret://test/" + (
        configuration.certificate_configuration_id
    )
    assert secret_store.secrets[configuration.password_secret_ref] == passphrase
    assert passphrase not in certificate_store.catalog_path.read_text(encoding="utf-8")


def test_certificate_import_choose_button_prefills_path_and_name(
    tmp_path: Path,
) -> None:
    source = tmp_path / "board-secretary.pfx"
    bindings, _, _, _, service = _build_service(tmp_path)
    bindings.q_file_dialog.next_open_file_name = str(source)

    dialog = service.show_import_dialog().compatibility.import_dialog
    selected = dialog.choose_certificate_file()

    assert selected == str(source)
    assert dialog.controls.certificate_path.text() == str(source)
    assert dialog.controls.display_name.text() == "board-secretary"
    assert bindings.q_file_dialog.open_calls[-1] == (
        dialog.controls.dialog,
        "Import certificate",
        "",
        "PKCS#12 files (*.p12 *.pfx);;All files (*)",
    )


def test_certificate_management_dialog_saves_and_refreshes(tmp_path: Path) -> None:
    certificate_store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    certificate_store.save_catalog(build_certificate_catalog())
    bindings, _, _, refresh_log, service = _build_service(
        tmp_path,
        certificate_store=certificate_store,
    )

    dialog = service.show_management_dialog().compatibility.management_dialog
    assert dialog.controls.configuration_selector.items == [
        ("Corporate Records Signing", "cert-config-default")
    ]
    assert dialog.controls.managed_certificate_selector.items == [
        ("Board Secretary 2026", "managed-cert-default")
    ]
    assert "reusable signing identities" in dialog.controls.introduction_label.text
    assert (
        dialog.controls.configuration_helper_label.text
        == "Certificate configurations are the saved signing identities shown "
        "in the main window."
    )
    assert (
        dialog.controls.managed_certificate_helper_label.text
        == "Managed certificates are the stored certificate files used by "
        "those configurations."
    )
    assert dialog.controls.display_name.text() == "Corporate Records Signing"
    assert dialog.controls.notes.text() == "Default signing identity"
    dialog.controls.display_name.setText("Board Records Signing")
    dialog.controls.notes.setText("Used for board packets.")
    saved = dialog.save_selected_configuration()

    assert saved.display_name == "Board Records Signing"
    assert saved.notes == "Used for board packets."
    reloaded = certificate_store.load_catalog().configuration_by_id(
        "cert-config-default"
    )
    assert reloaded.display_name == "Board Records Signing"
    assert reloaded.notes == "Used for board packets."
    assert refresh_log == ["refresh"]
    assert bindings.q_message_box.information_calls[-1] == (
        dialog.controls.dialog,
        "Certificate configuration",
        "Certificate configuration saved.",
    )


def test_certificate_management_dialog_deletes_configuration_only(
    tmp_path: Path,
) -> None:
    certificate_store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    certificate_store.save_catalog(
        build_certificate_catalog(
            managed_certificates=(
                build_managed_certificate(),
                build_managed_certificate(
                    managed_certificate_id="managed-cert-alt",
                    display_name="Alternate Signing Certificate",
                    storage_filename="cert_alt.p12",
                ),
            ),
            certificate_configurations=(
                build_certificate_configuration(),
                build_certificate_configuration(
                    certificate_configuration_id="cert-config-alt",
                    display_name="Alternate Signing",
                    managed_certificate_id="managed-cert-alt",
                ),
            ),
        )
    )
    _, _, _, refresh_log, service = _build_service(
        tmp_path,
        certificate_store=certificate_store,
    )

    dialog = service.show_management_dialog().compatibility.management_dialog
    deleted = dialog.delete_selected_configuration()

    catalog = certificate_store.load_catalog()
    assert deleted is True
    assert tuple(
        certificate.managed_certificate_id for certificate in catalog.managed_certificates
    ) == ("managed-cert-default", "managed-cert-alt")
    assert tuple(
        configuration.certificate_configuration_id
        for configuration in catalog.certificate_configurations
    ) == ("cert-config-alt",)
    assert refresh_log == ["refresh"]


def test_certificate_management_dialog_blocks_referenced_certificate_delete(
    tmp_path: Path,
) -> None:
    certificate_store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    managed_file = certificate_store.managed_certificate_dir / "cert_default.p12"
    certificate_store.managed_certificate_dir.mkdir(parents=True)
    managed_file.write_bytes(b"default-pkcs12")
    certificate_store.save_catalog(build_certificate_catalog())
    bindings, _, _, _, service = _build_service(
        tmp_path,
        certificate_store=certificate_store,
    )

    dialog = service.show_management_dialog().compatibility.management_dialog
    deleted = dialog.delete_selected_managed_certificate()

    assert deleted is False
    assert managed_file.exists()
    assert certificate_store.load_catalog().managed_certificate_by_id(
        "managed-cert-default"
    )
    assert bindings.q_message_box.warning_calls[-1] == (
        dialog.controls.dialog,
        "Certificate configuration error",
        "Managed certificate is still used by a certificate configuration; "
        "delete the configuration first.",
    )


def test_certificate_management_dialog_deletes_unreferenced_certificate(
    tmp_path: Path,
) -> None:
    certificate_store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    default_file = certificate_store.managed_certificate_dir / "cert_default.p12"
    alt_file = certificate_store.managed_certificate_dir / "cert_alt.p12"
    certificate_store.managed_certificate_dir.mkdir(parents=True)
    default_file.write_bytes(b"default-pkcs12")
    alt_file.write_bytes(b"alt-pkcs12")
    certificate_store.save_catalog(
        build_certificate_catalog(
            managed_certificates=(
                build_managed_certificate(),
                build_managed_certificate(
                    managed_certificate_id="managed-cert-alt",
                    display_name="Alternate Signing Certificate",
                    storage_filename="cert_alt.p12",
                ),
            )
        )
    )
    bindings, _, _, refresh_log, service = _build_service(
        tmp_path,
        certificate_store=certificate_store,
    )

    dialog = service.show_management_dialog().compatibility.management_dialog
    dialog.controls.managed_certificate_selector.setCurrentIndex(1)
    deleted = dialog.delete_selected_managed_certificate()

    catalog = certificate_store.load_catalog()
    assert deleted is True
    assert default_file.exists()
    assert not alt_file.exists()
    assert tuple(
        certificate.managed_certificate_id for certificate in catalog.managed_certificates
    ) == ("managed-cert-default",)
    assert dialog.controls.managed_certificate_selector.items == [
        ("Board Secretary 2026", "managed-cert-default")
    ]
    assert refresh_log == ["refresh"]
    assert bindings.q_message_box.information_calls[-1] == (
        dialog.controls.dialog,
        "Certificate configuration",
        "Managed certificate deleted.",
    )


def test_certificate_management_dialog_exports_selected_certificate(
    tmp_path: Path,
) -> None:
    certificate_store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    source = certificate_store.managed_certificate_dir / "cert_default.p12"
    destination = tmp_path / "backup" / "board-secretary.p12"
    certificate_store.managed_certificate_dir.mkdir(parents=True)
    source.write_bytes(b"managed-pkcs12")
    certificate_store.save_catalog(build_certificate_catalog())
    bindings, _, _, refresh_log, service = _build_service(
        tmp_path,
        certificate_store=certificate_store,
    )
    bindings.q_file_dialog.next_save_file_name = str(destination)

    dialog = service.show_management_dialog().compatibility.management_dialog
    exported = dialog.export_selected_managed_certificate()

    assert exported == destination
    assert destination.read_bytes() == b"managed-pkcs12"
    assert refresh_log == []
    assert bindings.q_file_dialog.save_calls[-1] == (
        dialog.controls.dialog,
        "Export managed certificate",
        "cert_default.p12",
        "PKCS#12 files (*.p12 *.pfx);;All files (*)",
    )
    assert bindings.q_message_box.information_calls[-1] == (
        dialog.controls.dialog,
        "Certificate configuration",
        f"Managed certificate exported to {destination}.",
    )


def test_certificate_management_dialog_handles_empty_catalog(tmp_path: Path) -> None:
    bindings, _, _, _, service = _build_service(tmp_path)

    dialog = service.show_management_dialog().compatibility.management_dialog
    assert (
        dialog.controls.configuration_helper_label.text
        == "No certificate configurations yet. Create or import a certificate "
        "to make one available for signing."
    )
    assert (
        dialog.controls.managed_certificate_helper_label.text
        == "No managed certificates are stored yet. Import or create one to "
        "back a certificate configuration."
    )
    saved = dialog.save_selected_configuration()
    deleted = dialog.delete_selected_configuration()
    exported = dialog.export_selected_managed_certificate()
    certificate_deleted = dialog.delete_selected_managed_certificate()

    assert saved is None
    assert deleted is False
    assert exported is None
    assert certificate_deleted is False
    assert bindings.q_message_box.warning_calls[-4:] == [
        (
            dialog.controls.dialog,
            "Certificate configuration error",
            "Select a certificate configuration to save.",
        ),
        (
            dialog.controls.dialog,
            "Certificate configuration error",
            "Select a certificate configuration to delete.",
        ),
        (
            dialog.controls.dialog,
            "Certificate configuration error",
            "Select a managed certificate to export.",
        ),
        (
            dialog.controls.dialog,
            "Certificate configuration error",
            "Select a managed certificate to delete.",
        ),
    ]
