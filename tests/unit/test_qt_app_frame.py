from pathlib import Path

from foliaseal.infra.config.app_settings_storage import AppSettingsStore
from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
from foliaseal.infra.config.schemas import AppSettings
from foliaseal.presentation.qt import app_frame as app_frame_module
from foliaseal.presentation.qt.app_frame import FoliaSealAppFrame, QtAppFrameBindings
from tests.support.phase3_builders import (
    build_certificate_catalog,
    build_certificate_configuration,
    build_managed_certificate,
)
from tests.unit.test_certificate_import import _write_test_pkcs12


class _FakeSignal:
    def __init__(self) -> None:
        self._callbacks = []

    def connect(self, callback):
        self._callbacks.append(callback)

    def emit(self):
        for callback in list(self._callbacks):
            callback()


class _FakeAction:
    def __init__(self, text, parent=None) -> None:
        self.text = text
        self.parent = parent
        self.triggered = _FakeSignal()

    def trigger(self) -> None:
        self.triggered.emit()


class _FakeMenu:
    def __init__(self, title) -> None:
        self.title = title
        self.actions = []

    def addAction(self, action):  # noqa: N802
        self.actions.append(action)


class _FakeMenuBar:
    def __init__(self) -> None:
        self.menus = []

    def addMenu(self, title):  # noqa: N802
        menu = _FakeMenu(title)
        self.menus.append(menu)
        return menu


class _FakeMainWindow:
    def __init__(self) -> None:
        self.title = ""
        self.central_widget = None
        self.menu_bar = _FakeMenuBar()

    def setWindowTitle(self, title):  # noqa: N802
        self.title = title

    def menuBar(self):  # noqa: N802
        return self.menu_bar

    def setCentralWidget(self, widget):  # noqa: N802
        self.central_widget = widget


class _FakeLabel:
    def __init__(self, text="") -> None:
        self.text = text
        self.word_wrap = False

    def setWordWrap(self, value):  # noqa: N802
        self.word_wrap = bool(value)


class _FakeDialog:
    Accepted = 1
    Rejected = 0

    def __init__(self, parent=None) -> None:
        self.parent = parent
        self.title = ""
        self.result = self.Rejected
        self.layout = None

    def setWindowTitle(self, title):  # noqa: N802
        self.title = title

    def setLayout(self, layout):  # noqa: N802
        self.layout = layout

    def exec(self):
        return self.result

    def accept(self) -> None:
        self.result = self.Accepted

    def reject(self) -> None:
        self.result = self.Rejected


class _FakeFormLayout:
    def __init__(self, parent=None) -> None:
        self.parent = parent
        self.rows = []
        if parent is not None and hasattr(parent, "setLayout"):
            parent.setLayout(self)

    def addRow(self, *args):  # noqa: N802
        self.rows.append(args)


class _FakeLineEdit:
    def __init__(self, text="") -> None:
        self._text = text

    def setText(self, text):  # noqa: N802
        self._text = text

    def text(self):
        return self._text


class _FakeComboBox:
    def __init__(self) -> None:
        self.items = []
        self.current_index = -1
        self.currentIndexChanged = _FakeSignal()

    def addItem(self, text, user_data=None):  # noqa: N802
        self.items.append((text, user_data))
        if self.current_index < 0:
            self.current_index = 0

    def clear(self) -> None:
        self.items = []
        self.current_index = -1

    def currentData(self):  # noqa: N802
        if self.current_index < 0:
            return None
        return self.items[self.current_index][1]

    def currentIndex(self):  # noqa: N802
        return self.current_index

    def setCurrentIndex(self, index):  # noqa: N802
        self.current_index = index
        self.currentIndexChanged.emit()

    def itemData(self, index):  # noqa: N802
        return self.items[index][1]

    def count(self):
        return len(self.items)


class _FakePushButton:
    def __init__(self, text="") -> None:
        self.text = text
        self.clicked = _FakeSignal()

    def click(self) -> None:
        self.clicked.emit()


class _FakeFileDialog:
    def __init__(self) -> None:
        self.open_calls = []
        self.next_open_file_name = ""

    def getOpenFileName(self, parent, title, directory, file_filter):  # noqa: N802
        self.open_calls.append((parent, title, directory, file_filter))
        return (self.next_open_file_name, file_filter)


class _FakeMessageBox:
    def __init__(self) -> None:
        self.warning_calls = []
        self.information_calls = []

    def warning(self, parent, title, text):
        self.warning_calls.append((parent, title, text))

    def information(self, parent, title, text):
        self.information_calls.append((parent, title, text))


class _FakeQPdfDocument:
    class Error:
        None_ = 0
        Failed = 1

    next_status = 0
    next_page_count = 3
    load_calls = []

    def load(self, path):
        self.load_calls.append(path)
        return self.next_status

    def pageCount(self):  # noqa: N802
        return self.next_page_count


class _FakeShell:
    def __init__(self) -> None:
        self.refresh_certificate_configurations_calls = 0

    def refresh_certificate_configurations(self) -> None:
        self.refresh_certificate_configurations_calls += 1


def _fake_bindings() -> QtAppFrameBindings:
    file_dialog = _FakeFileDialog()
    message_box = _FakeMessageBox()
    _FakeQPdfDocument.next_status = _FakeQPdfDocument.Error.None_
    _FakeQPdfDocument.next_page_count = 3
    _FakeQPdfDocument.load_calls = []
    return QtAppFrameBindings(
        q_main_window=_FakeMainWindow,
        q_dialog=_FakeDialog,
        q_form_layout=_FakeFormLayout,
        q_label=_FakeLabel,
        q_line_edit=_FakeLineEdit,
        q_combo_box=_FakeComboBox,
        q_push_button=_FakePushButton,
        q_file_dialog=file_dialog,
        q_message_box=message_box,
        q_action=_FakeAction,
        qpdf_document=_FakeQPdfDocument,
    )


def _settings(tmp_path: Path) -> AppSettings:
    return AppSettings(
        schema_version=1,
        default_output_directory=str(tmp_path / "signed"),
        default_open_directory=str(tmp_path / "source"),
        linux_packaging_channel="unknown",
        ui={},
    )


def test_app_frame_open_file_uses_settings_defaults_and_builds_signing_shell(
    tmp_path: Path,
) -> None:
    bindings = _fake_bindings()
    selected_pdf = tmp_path / "source" / "contract.pdf"
    bindings.q_file_dialog.next_open_file_name = str(selected_pdf)
    shell = _FakeShell()
    shell_calls = []

    def shell_builder(**kwargs):
        shell_calls.append(kwargs)
        return shell

    frame = FoliaSealAppFrame(
        bindings=bindings,
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        shell_builder=shell_builder,
        render_backend_factory=lambda: object(),
    )

    result = frame.choose_open_pdf()

    assert result == str(selected_pdf)
    assert bindings.q_file_dialog.open_calls == [
        (
            frame.window,
            "Open PDF",
            str(tmp_path / "source"),
            "PDF files (*.pdf)",
        )
    ]
    assert _FakeQPdfDocument.load_calls == [str(selected_pdf)]
    assert frame.window.central_widget is shell
    assert frame.window.current_shell is shell
    assert shell_calls[0]["viewer_workflow"].session.page_count == 3
    assert shell_calls[0]["viewer_workflow"]._document_path == str(selected_pdf)
    assert shell_calls[0]["signing_workflow"].input_pdf_path == str(selected_pdf)
    assert shell_calls[0]["signing_workflow"].output_pdf_path == str(
        tmp_path / "signed" / "contract-signed.pdf"
    )
    assert shell_calls[0]["app_settings"] == _settings(tmp_path)


def test_app_frame_installs_file_and_settings_menu_actions(tmp_path: Path) -> None:
    bindings = _fake_bindings()
    frame = FoliaSealAppFrame(
        bindings=bindings,
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        shell_builder=lambda **_kwargs: _FakeShell(),
        render_backend_factory=lambda: object(),
    )

    assert [menu.title for menu in frame.window.menu_bar.menus] == ["File", "Settings"]
    assert frame.window.menu_bar.menus[0].actions[0].text == "Open file"
    assert [action.text for action in frame.window.menu_bar.menus[1].actions] == [
        "Application settings",
        "Import certificate...",
        "Manage certificate configurations...",
    ]

    frame.window.menu_bar.menus[1].actions[0].trigger()

    assert frame.window.settings_dialog.controls.dialog.title == "Application settings"
    assert (
        frame.window.settings_dialog.controls.default_open_directory.text()
        == str(tmp_path / "source")
    )


def test_app_frame_certificate_import_dialog_imports_and_refreshes_loaded_shell(
    tmp_path: Path,
) -> None:
    bindings = _fake_bindings()
    source = tmp_path / "alice.p12"
    _write_test_pkcs12(source, passphrase="secret", common_name="Alice Example")
    certificate_store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    shell = _FakeShell()
    frame = FoliaSealAppFrame(
        bindings=bindings,
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        certificate_catalog_store=certificate_store,
        shell_builder=lambda **_kwargs: shell,
        render_backend_factory=lambda: object(),
    )
    frame.open_pdf_path(tmp_path / "source" / "contract.pdf")

    frame.window.menu_bar.menus[1].actions[1].trigger()
    dialog = frame.window.certificate_import_dialog
    dialog.controls.certificate_path.setText(str(source))
    dialog.controls.display_name.setText("Alice Signing")
    dialog.controls.passphrase.setText("secret")
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
    assert shell.refresh_certificate_configurations_calls == 1
    assert bindings.q_message_box.information_calls[-1][1] == "Certificate imported"


def test_app_frame_certificate_management_dialog_saves_and_refreshes_loaded_shell(
    tmp_path: Path,
) -> None:
    bindings = _fake_bindings()
    certificate_store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    certificate_store.save_catalog(build_certificate_catalog())
    shell = _FakeShell()
    frame = FoliaSealAppFrame(
        bindings=bindings,
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        certificate_catalog_store=certificate_store,
        shell_builder=lambda **_kwargs: shell,
        render_backend_factory=lambda: object(),
    )
    frame.open_pdf_path(tmp_path / "source" / "contract.pdf")

    frame.window.menu_bar.menus[1].actions[2].trigger()
    dialog = frame.window.certificate_management_dialog
    assert dialog.controls.configuration_selector.items == [
        ("Corporate Records Signing", "cert-config-default")
    ]
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
    assert shell.refresh_certificate_configurations_calls == 1
    assert bindings.q_message_box.information_calls[-1] == (
        dialog.controls.dialog,
        "Certificate configuration",
        "Certificate configuration saved.",
    )


def test_app_frame_certificate_management_dialog_deletes_configuration_only(
    tmp_path: Path,
) -> None:
    bindings = _fake_bindings()
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
            )
        )
    )
    shell = _FakeShell()
    frame = FoliaSealAppFrame(
        bindings=bindings,
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        certificate_catalog_store=certificate_store,
        shell_builder=lambda **_kwargs: shell,
        render_backend_factory=lambda: object(),
    )
    frame.open_pdf_path(tmp_path / "source" / "contract.pdf")

    frame.show_certificate_management()
    dialog = frame.window.certificate_management_dialog
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
    assert shell.refresh_certificate_configurations_calls == 1


def test_app_frame_certificate_management_dialog_handles_empty_catalog(
    tmp_path: Path,
) -> None:
    bindings = _fake_bindings()
    frame = FoliaSealAppFrame(
        bindings=bindings,
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        certificate_catalog_store=CertificateCatalogStore(
            storage_dir=tmp_path / "Certificates"
        ),
        shell_builder=lambda **_kwargs: _FakeShell(),
        render_backend_factory=lambda: object(),
    )

    frame.show_certificate_management()
    dialog = frame.window.certificate_management_dialog
    saved = dialog.save_selected_configuration()
    deleted = dialog.delete_selected_configuration()

    assert saved is None
    assert deleted is False
    assert bindings.q_message_box.warning_calls[-2:] == [
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
    ]


def test_app_frame_certificate_import_choose_button_prefills_path_and_name(
    tmp_path: Path,
) -> None:
    bindings = _fake_bindings()
    source = tmp_path / "board-secretary.pfx"
    bindings.q_file_dialog.next_open_file_name = str(source)
    frame = FoliaSealAppFrame(
        bindings=bindings,
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        certificate_catalog_store=CertificateCatalogStore(
            storage_dir=tmp_path / "Certificates"
        ),
        shell_builder=lambda **_kwargs: _FakeShell(),
        render_backend_factory=lambda: object(),
    )

    frame.show_certificate_import()
    selected = frame.window.certificate_import_dialog.choose_certificate_file()

    assert selected == str(source)
    assert frame.window.certificate_import_dialog.controls.certificate_path.text() == (
        str(source)
    )
    assert frame.window.certificate_import_dialog.controls.display_name.text() == (
        "board-secretary"
    )
    assert bindings.q_file_dialog.open_calls[-1] == (
        frame.window.certificate_import_dialog.controls.dialog,
        "Import certificate",
        "",
        "PKCS#12 files (*.p12 *.pfx);;All files (*)",
    )


def test_app_frame_settings_dialog_saves_defaults_and_updates_open_dialog(
    tmp_path: Path,
) -> None:
    bindings = _fake_bindings()
    settings_store = AppSettingsStore(storage_dir=tmp_path / "config")
    frame = FoliaSealAppFrame(
        bindings=bindings,
        app_settings=_settings(tmp_path),
        app_settings_store=settings_store,
        shell_builder=lambda **_kwargs: _FakeShell(),
        render_backend_factory=lambda: object(),
    )
    next_open_dir = tmp_path / "next-source"
    next_output_dir = tmp_path / "next-signed"

    frame.show_app_settings()
    dialog = frame.window.settings_dialog
    dialog.controls.default_open_directory.setText(str(next_open_dir))
    dialog.controls.default_output_directory.setText(str(next_output_dir))
    saved = dialog.save()
    frame.show_app_settings()

    assert saved == AppSettings(
        schema_version=1,
        default_open_directory=str(next_open_dir),
        default_output_directory=str(next_output_dir),
        linux_packaging_channel="unknown",
        ui={},
    )
    assert settings_store.load_settings() == saved
    assert frame.app_settings == saved
    assert frame.window.app_settings == saved
    bindings.q_file_dialog.next_open_file_name = ""
    frame.choose_open_pdf()
    assert bindings.q_file_dialog.open_calls[-1][2] == str(next_open_dir)


def test_app_frame_settings_dialog_refreshes_loaded_shell_settings(
    tmp_path: Path,
) -> None:
    bindings = _fake_bindings()
    shell = _FakeShell()
    seen_settings = []

    class _Workspace:
        def _handle_app_settings_change(self, settings):
            seen_settings.append(settings)

    shell._signing_workspace = _Workspace()
    frame = FoliaSealAppFrame(
        bindings=bindings,
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        shell_builder=lambda **_kwargs: shell,
        render_backend_factory=lambda: object(),
    )
    frame.open_pdf_path(tmp_path / "source" / "contract.pdf")

    frame.show_app_settings()
    dialog = frame.window.settings_dialog
    dialog.controls.default_open_directory.setText(str(tmp_path / "updated-open"))
    dialog.controls.default_output_directory.setText(str(tmp_path / "updated-output"))
    saved = dialog.save()
    frame.show_app_settings()

    assert shell.app_settings == saved
    assert seen_settings == [saved]


def test_app_frame_reports_open_errors(tmp_path: Path) -> None:
    bindings = _fake_bindings()
    bindings.qpdf_document.next_status = bindings.qpdf_document.Error.Failed
    errors = []
    frame = FoliaSealAppFrame(
        bindings=bindings,
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        shell_builder=lambda **_kwargs: _FakeShell(),
        render_backend_factory=lambda: object(),
        on_error=errors.append,
    )

    result = frame.open_pdf_path(tmp_path / "broken.pdf")

    assert result is None
    assert errors and errors[0].startswith("Unable to open PDF:")
    assert bindings.q_message_box.warning_calls
    assert frame.window.current_shell is None


def test_build_qt_app_frame_uses_adapter_bindings(monkeypatch, tmp_path: Path) -> None:
    bindings = _fake_bindings()
    monkeypatch.setattr(
        app_frame_module.QtAppFrameAdapter,
        "_load_bindings",
        lambda self: bindings,
    )

    window = app_frame_module.build_qt_app_frame(
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
    )

    assert isinstance(window, _FakeMainWindow)
    assert window.title == "FoliaSeal"
