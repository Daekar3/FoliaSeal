from pathlib import Path

from foliaseal.infra.config.app_settings_storage import AppSettingsStore
from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
from foliaseal.infra.config.schemas import AppSettings, CertificateCatalog
from foliaseal.presentation.qt import app_frame as app_frame_module
from foliaseal.presentation.qt import signing_shell_port as signing_shell_port_module
from foliaseal.presentation.qt.app_frame import (
    FoliaSealAppFrame,
    QtAppFrameBindings,
)
from foliaseal.presentation.qt.signing_shell_port import (
    QtSigningWorkspacePort,
    SigningWorkspaceBootstrap,
)


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
        self.shortcut = None
        self.enabled = True

    def setShortcut(self, shortcut):  # noqa: N802
        self.shortcut = shortcut

    def setEnabled(self, enabled):  # noqa: N802
        self.enabled = bool(enabled)

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
        self.show_calls = 0

    def setWindowTitle(self, title):  # noqa: N802
        self.title = title

    def menuBar(self):  # noqa: N802
        return self.menu_bar

    def setCentralWidget(self, widget):  # noqa: N802
        self.central_widget = widget

    def show(self) -> None:
        self.show_calls += 1


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


class _FakeCheckBox:
    def __init__(self, text="") -> None:
        self.text = text
        self._checked = False

    def setChecked(self, checked):  # noqa: N802
        self._checked = bool(checked)

    def isChecked(self):  # noqa: N802
        return self._checked


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
        self.save_calls = []
        self.next_open_file_name = ""
        self.next_save_file_name = ""

    def getOpenFileName(self, parent, title, directory, file_filter):  # noqa: N802
        self.open_calls.append((parent, title, directory, file_filter))
        return (self.next_open_file_name, file_filter)

    def getSaveFileName(self, parent, title, directory, file_filter):  # noqa: N802
        self.save_calls.append((parent, title, directory, file_filter))
        return (self.next_save_file_name, file_filter)


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


class _FakeQApplication:
    _instance = None
    created_argv = []
    exec_result = 0
    exec_calls = 0

    def __init__(self, argv) -> None:
        self.argv = list(argv)
        type(self).created_argv.append(self.argv)
        type(self)._instance = self

    @classmethod
    def instance(cls):
        return cls._instance

    def exec(self):
        type(self).exec_calls += 1
        return type(self).exec_result


class _FakeShell:
    def __init__(self) -> None:
        self.refresh_certificate_configurations_calls = 0
        self.applied_settings = []
        self.output_dialog_defaults = []
        self.choose_output_pdf_path_calls = 0
        self.certificate_catalog = CertificateCatalog(schema_version=1)

    def apply_app_settings(self, settings) -> None:
        self.app_settings = settings
        self.applied_settings.append(settings)
        self.output_dialog_defaults.append(settings.default_output_directory)

    def refresh_certificate_configurations(self) -> CertificateCatalog:
        self.refresh_certificate_configurations_calls += 1
        return self.certificate_catalog

    def choose_output_pdf_path(self):
        self.choose_output_pdf_path_calls += 1
        return "/tmp/signed-output.pdf"


class _FakeShellPort:
    def __init__(self, shell_widget) -> None:
        self.shell_widget = shell_widget

    def widget(self):
        return self.shell_widget

    def choose_output_pdf_path(self):
        return self.shell_widget.choose_output_pdf_path()

    def apply_app_settings(self, settings) -> None:
        self.shell_widget.apply_app_settings(settings)

    def refresh_certificate_configurations(self) -> CertificateCatalog:
        return self.shell_widget.refresh_certificate_configurations()


class _FakeShellFactory:
    def __init__(self, shell_widget, *, bootstrap_calls=None) -> None:
        self.shell_widget = shell_widget
        self.bootstrap_calls = bootstrap_calls if bootstrap_calls is not None else []

    def create(self, bootstrap: SigningWorkspaceBootstrap):
        self.bootstrap_calls.append(bootstrap)
        return _FakeShellPort(self.shell_widget)


class _FakeSecretStore:
    def __init__(
        self,
        *,
        available: bool = True,
        fail_set: bool = False,
    ) -> None:
        self.available = available
        self.fail_set = fail_set
        self.secrets: dict[str, str] = {}
        self.deleted: list[str] = []

    def is_available(self) -> bool:
        return self.available

    def secret_ref_for_configuration(self, configuration_id: str) -> str:
        return f"secret://test/{configuration_id}"

    def set_secret(self, secret_ref: str, secret: str) -> None:
        if self.fail_set:
            raise OSError("secure storage restore failed")
        self.secrets[secret_ref] = secret

    def get_secret(self, secret_ref: str) -> str | None:
        return self.secrets.get(secret_ref)

    def delete_secret(self, secret_ref: str) -> None:
        self.deleted.append(secret_ref)
        self.secrets.pop(secret_ref, None)


def _fake_bindings() -> QtAppFrameBindings:
    file_dialog = _FakeFileDialog()
    message_box = _FakeMessageBox()
    _FakeQPdfDocument.next_status = _FakeQPdfDocument.Error.None_
    _FakeQPdfDocument.next_page_count = 3
    _FakeQPdfDocument.load_calls = []
    _FakeQApplication._instance = None
    _FakeQApplication.created_argv = []
    _FakeQApplication.exec_result = 0
    _FakeQApplication.exec_calls = 0
    return QtAppFrameBindings(
        q_main_window=_FakeMainWindow,
        q_dialog=_FakeDialog,
        q_form_layout=_FakeFormLayout,
        q_label=_FakeLabel,
        q_line_edit=_FakeLineEdit,
        q_check_box=_FakeCheckBox,
        q_combo_box=_FakeComboBox,
        q_push_button=_FakePushButton,
        q_file_dialog=file_dialog,
        q_message_box=message_box,
        q_action=_FakeAction,
        q_application=_FakeQApplication,
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


def test_qt_signing_workspace_factory_wraps_build_qt_signing_shell(
    tmp_path: Path, monkeypatch
) -> None:
    captured = {}
    shell = _FakeShell()

    def _fake_build_qt_signing_shell(**kwargs):
        captured.update(kwargs)
        return shell

    monkeypatch.setattr(
        signing_shell_port_module,
        "build_qt_signing_shell",
        _fake_build_qt_signing_shell,
    )
    bootstrap = SigningWorkspaceBootstrap(
        viewer_workflow=object(),
        signing_workflow=object(),
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        certificate_catalog_store=CertificateCatalogStore(
            storage_dir=tmp_path / "Certificates"
        ),
        certificate_secret_provider=object(),
        preset_catalog_store=object(),
        sign_executor=object(),
        on_sign_request=lambda request: None,
        on_open_signed_output=lambda path: None,
        on_error=lambda message: None,
        on_status_change=lambda status: None,
    )

    port = signing_shell_port_module.QtSigningWorkspaceFactory().create(bootstrap)

    assert port.widget() is shell
    assert captured == {
        "viewer_workflow": bootstrap.viewer_workflow,
        "signing_workflow": bootstrap.signing_workflow,
        "certificate_catalog_store": bootstrap.certificate_catalog_store,
        "certificate_secret_provider": bootstrap.certificate_secret_provider,
        "preset_catalog_store": bootstrap.preset_catalog_store,
        "app_settings": bootstrap.app_settings,
        "app_settings_store": bootstrap.app_settings_store,
        "sign_executor": bootstrap.sign_executor,
        "on_sign_request": bootstrap.on_sign_request,
        "on_open_signed_output": bootstrap.on_open_signed_output,
        "on_error": bootstrap.on_error,
        "on_status_change": bootstrap.on_status_change,
    }


def test_qt_signing_workspace_port_forwards_public_shell_contract(tmp_path: Path) -> None:
    shell = _FakeShell()
    port = QtSigningWorkspacePort(shell_widget=shell)
    settings = _settings(tmp_path)

    assert port.widget() is shell
    assert port.choose_output_pdf_path() == "/tmp/signed-output.pdf"

    port.apply_app_settings(settings)

    assert shell.applied_settings == [settings]
    assert shell.output_dialog_defaults == [settings.default_output_directory]
    assert shell.app_settings == settings

    catalog = port.refresh_certificate_configurations()

    assert catalog is shell.certificate_catalog
    assert shell.refresh_certificate_configurations_calls == 1


def test_app_frame_open_file_uses_settings_defaults_and_installs_workspace(
    tmp_path: Path,
) -> None:
    bindings = _fake_bindings()
    selected_pdf = tmp_path / "source" / "contract.pdf"
    bindings.q_file_dialog.next_open_file_name = str(selected_pdf)
    shell = _FakeShell()

    frame = FoliaSealAppFrame(
        bindings=bindings,
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        shell_factory=_FakeShellFactory(shell),
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
    assert frame.current_shell is shell
    assert frame.current_workspace is not None
    assert frame.current_viewer_workflow.session.page_count == 3
    assert frame.current_viewer_workflow.document_path == str(selected_pdf)
    assert frame.current_signing_workflow.input_pdf_path == str(selected_pdf)
    assert frame.current_signing_workflow.output_pdf_path == str(
        tmp_path / "signed" / "contract-signed.pdf"
    )
    assert frame.window.menu_bar.menus[0].actions[1].enabled is True


def test_app_frame_reopens_signed_output_from_shell_callback(tmp_path: Path) -> None:
    bindings = _fake_bindings()
    opened_paths = []
    bootstrap_calls = []
    shell = _FakeShell()

    frame = FoliaSealAppFrame(
        bindings=bindings,
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        shell_factory=_FakeShellFactory(shell, bootstrap_calls=bootstrap_calls),
        render_backend_factory=lambda: object(),
    )
    frame.open_pdf_path(tmp_path / "source" / "contract.pdf")
    opened_paths.append(bootstrap_calls[0].viewer_workflow._document_path)
    shell_callback = bootstrap_calls[0].on_open_signed_output

    reopened = shell_callback(tmp_path / "signed" / "contract-signed.pdf")
    opened_paths.append(bootstrap_calls[1].viewer_workflow._document_path)

    assert reopened is frame.current_shell
    assert opened_paths == [
        str(tmp_path / "source" / "contract.pdf"),
        str(tmp_path / "signed" / "contract-signed.pdf"),
    ]


def test_app_frame_installs_file_and_settings_menu_actions(tmp_path: Path) -> None:
    bindings = _fake_bindings()
    frame = FoliaSealAppFrame(
        bindings=bindings,
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        shell_factory=_FakeShellFactory(_FakeShell()),
        render_backend_factory=lambda: object(),
    )

    assert [menu.title for menu in frame.window.menu_bar.menus] == ["File", "Settings"]
    assert [action.text for action in frame.window.menu_bar.menus[0].actions] == [
        "Open file",
        "Save As...",
    ]
    assert frame.window.menu_bar.menus[0].actions[0].shortcut == "Ctrl+O"
    assert frame.window.menu_bar.menus[0].actions[1].shortcut == "Ctrl+Shift+S"
    assert frame.window.menu_bar.menus[0].actions[1].enabled is False
    assert [action.text for action in frame.window.menu_bar.menus[1].actions] == [
        "Application settings",
        "Create certificate...",
        "Import certificate...",
        "Manage certificate configurations...",
    ]
    assert not hasattr(frame.window, "_foliaseal_app_frame")
    assert not hasattr(frame.window, "app_settings")
    assert not hasattr(frame.window, "open_file")
    assert not hasattr(frame.window, "open_pdf_path")
    assert not hasattr(frame.window, "show_app_settings")
    assert not hasattr(frame.window, "show_certificate_creation")
    assert not hasattr(frame.window, "show_certificate_import")
    assert not hasattr(frame.window, "show_certificate_management")

    frame.window.menu_bar.menus[1].actions[0].trigger()

    assert frame.settings_dialog.controls.dialog.title == "Application settings"
    assert (
        frame.settings_dialog.controls.default_open_directory.text()
        == str(tmp_path / "source")
    )


def test_app_frame_save_as_action_enables_after_open_and_routes_to_current_shell(
    tmp_path: Path,
) -> None:
    bindings = _fake_bindings()
    shell = _FakeShell()
    frame = FoliaSealAppFrame(
        bindings=bindings,
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        shell_factory=_FakeShellFactory(shell),
        render_backend_factory=lambda: object(),
    )

    save_as_action = frame.window.menu_bar.menus[0].actions[1]

    assert save_as_action.enabled is False

    frame.open_pdf_path(tmp_path / "source" / "contract.pdf")

    assert save_as_action.enabled is True

    save_as_action.trigger()

    assert shell.choose_output_pdf_path_calls == 1


def test_app_frame_certificate_creation_routes_to_dialog_port(
    tmp_path: Path,
) -> None:
    bindings = _fake_bindings()
    frame = FoliaSealAppFrame(
        bindings=bindings,
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        shell_factory=_FakeShellFactory(_FakeShell()),
        render_backend_factory=lambda: object(),
    )

    result = frame.show_certificate_creation()

    assert result is None
    assert frame.certificate_creation_dialog is not None
    assert frame.certificate_creation_dialog.controls.dialog.parent is frame.window


def test_app_frame_certificate_import_routes_to_dialog_port(
    tmp_path: Path,
) -> None:
    bindings = _fake_bindings()
    frame = FoliaSealAppFrame(
        bindings=bindings,
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        shell_factory=_FakeShellFactory(_FakeShell()),
        render_backend_factory=lambda: object(),
    )

    result = frame.show_certificate_import()

    assert result is None
    assert frame.certificate_import_dialog is not None
    assert frame.certificate_import_dialog.controls.dialog.parent is frame.window


def test_app_frame_certificate_management_routes_to_dialog_port(
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
        shell_factory=_FakeShellFactory(_FakeShell()),
        render_backend_factory=lambda: object(),
    )

    result = frame.show_certificate_management()

    assert result == _FakeDialog.Rejected
    assert frame.certificate_management_dialog is not None
    assert frame.certificate_management_dialog.controls.dialog.parent is frame.window


def test_app_frame_settings_dialog_saves_defaults_and_updates_open_dialog(
    tmp_path: Path,
) -> None:
    bindings = _fake_bindings()
    settings_store = AppSettingsStore(storage_dir=tmp_path / "config")
    frame = FoliaSealAppFrame(
        bindings=bindings,
        app_settings=_settings(tmp_path),
        app_settings_store=settings_store,
        shell_factory=_FakeShellFactory(_FakeShell()),
        render_backend_factory=lambda: object(),
    )
    next_open_dir = tmp_path / "next-source"
    next_output_dir = tmp_path / "next-signed"

    frame.show_app_settings()
    dialog = frame.settings_dialog
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
    assert not hasattr(frame.window, "app_settings")
    bindings.q_file_dialog.next_open_file_name = ""
    frame.choose_open_pdf()
    assert bindings.q_file_dialog.open_calls[-1][2] == str(next_open_dir)


def test_app_frame_settings_dialog_refreshes_loaded_shell_settings(
    tmp_path: Path,
) -> None:
    bindings = _fake_bindings()
    shell = _FakeShell()
    frame = FoliaSealAppFrame(
        bindings=bindings,
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        shell_factory=_FakeShellFactory(shell),
        render_backend_factory=lambda: object(),
    )
    frame.open_pdf_path(tmp_path / "source" / "contract.pdf")

    frame.show_app_settings()
    dialog = frame.settings_dialog
    dialog.controls.default_open_directory.setText(str(tmp_path / "updated-open"))
    dialog.controls.default_output_directory.setText(str(tmp_path / "updated-output"))
    saved = dialog.save()
    frame.show_app_settings()

    assert shell.app_settings == saved
    assert shell.applied_settings == [saved]
    assert shell.output_dialog_defaults == [str(tmp_path / "updated-output")]


def test_app_frame_reports_open_errors(tmp_path: Path) -> None:
    bindings = _fake_bindings()
    bindings.qpdf_document.next_status = bindings.qpdf_document.Error.Failed
    errors = []
    frame = FoliaSealAppFrame(
        bindings=bindings,
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        shell_factory=_FakeShellFactory(_FakeShell()),
        render_backend_factory=lambda: object(),
        on_error=errors.append,
    )

    result = frame.open_pdf_path(tmp_path / "broken.pdf")

    assert result is None
    assert errors and errors[0].startswith("Unable to open PDF:")
    assert bindings.q_message_box.warning_calls
    assert frame.current_shell is None


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
    assert not hasattr(window, "app_settings")
    assert not hasattr(window, "open_file")
    assert not hasattr(window, "open_pdf_path")
    assert not hasattr(window, "show_app_settings")


def test_launch_qt_app_frame_creates_application_shows_window_and_opens_initial_pdf(
    monkeypatch,
    tmp_path: Path,
) -> None:
    bindings = _fake_bindings()
    _FakeQApplication.exec_result = 7

    class _FakeLaunchFrame:
        instances = []

        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs
            self.window = _FakeMainWindow()
            self.opened_paths = []
            type(self).instances.append(self)

        def open_pdf_path(self, path) -> None:
            self.opened_paths.append(path)

    monkeypatch.setattr(
        app_frame_module.QtAppFrameAdapter,
        "_load_bindings",
        lambda self: bindings,
    )
    monkeypatch.setattr(app_frame_module, "FoliaSealAppFrame", _FakeLaunchFrame)

    exit_code = app_frame_module.launch_qt_app_frame(
        argv=["foliaseal", "gui", "--pdf-path", "/tmp/sample.pdf"],
        initial_pdf_path="/tmp/sample.pdf",
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
    )

    assert exit_code == 7
    assert _FakeQApplication.created_argv == [
        ["foliaseal", "gui", "--pdf-path", "/tmp/sample.pdf"]
    ]
    assert _FakeQApplication.exec_calls == 1
    frame = _FakeLaunchFrame.instances[0]
    assert frame.window.show_calls == 1
    assert frame.opened_paths == ["/tmp/sample.pdf"]


def test_launch_qt_app_frame_reuses_existing_application(monkeypatch, tmp_path: Path) -> None:
    bindings = _fake_bindings()
    existing_app = _FakeQApplication(["existing-app"])
    _FakeQApplication.created_argv = []
    _FakeQApplication.exec_result = 3
    _FakeQApplication.exec_calls = 0

    class _FakeLaunchFrame:
        instances = []

        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs
            self.window = _FakeMainWindow()
            type(self).instances.append(self)

    monkeypatch.setattr(
        app_frame_module.QtAppFrameAdapter,
        "_load_bindings",
        lambda self: bindings,
    )
    monkeypatch.setattr(app_frame_module, "FoliaSealAppFrame", _FakeLaunchFrame)

    exit_code = app_frame_module.launch_qt_app_frame(
        argv=["foliaseal", "gui"],
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
    )

    assert exit_code == 3
    assert _FakeQApplication.instance() is existing_app
    assert _FakeQApplication.created_argv == []
    assert _FakeQApplication.exec_calls == 1
    assert _FakeLaunchFrame.instances[0].window.show_calls == 1


def test_launch_qt_app_frame_uses_process_argv_when_none_is_supplied(
    monkeypatch,
    tmp_path: Path,
) -> None:
    bindings = _fake_bindings()
    _FakeQApplication.exec_result = 0

    class _FakeLaunchFrame:
        def __init__(self, **kwargs) -> None:
            self.window = _FakeMainWindow()

    monkeypatch.setattr(
        app_frame_module.QtAppFrameAdapter,
        "_load_bindings",
        lambda self: bindings,
    )
    monkeypatch.setattr(app_frame_module, "FoliaSealAppFrame", _FakeLaunchFrame)
    monkeypatch.setattr(
        app_frame_module.sys,
        "argv",
        ["foliaseal", "gui", "--pdf-path", "/tmp/live.pdf"],
    )

    app_frame_module.launch_qt_app_frame(
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
    )

    assert _FakeQApplication.created_argv == [
        ["foliaseal", "gui", "--pdf-path", "/tmp/live.pdf"]
    ]
