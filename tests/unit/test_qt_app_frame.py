from pathlib import Path

import pytest

from foliaseal.application.certificate_models import CertificateCatalog
from foliaseal.application.reusable_signing_models import SignaturePresetCatalog
from foliaseal.application.reusable_signing_objects import (
    InMemoryCatalogRepository,
    ReusableSigningObjects,
)
from foliaseal.application.signing_executor import LazySigningRequestExecutor
from foliaseal.domain.models import SignatureRect
from foliaseal.infra.config.app_settings_storage import AppSettingsStore
from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
from foliaseal.infra.config.schemas import AppSettings
from foliaseal.infra.render import PopplerPdfRenderBackend
from foliaseal.presentation.qt import app_frame as app_frame_module
from foliaseal.presentation.qt import signing_shell_port as signing_shell_port_module
from foliaseal.presentation.qt.app_frame import (
    FoliaSealAppFrame,
    QtAppFrameBindings,
)
from foliaseal.presentation.qt.app_frame_command_model import (
    EDIT_COMMAND_DEFINITIONS,
    FILE_COMMAND_DEFINITIONS,
    SETTINGS_COMMAND_DEFINITIONS,
    SIGNING_COMMAND_DEFINITIONS,
    VIEW_COMMAND_DEFINITIONS,
    AppFrameCommandId,
)
from foliaseal.presentation.qt.signing_shell_port import (
    QtSigningWorkspacePort,
    QtSigningWorkspaceSessionPort,
    QtWorkspaceView,
    SigningWorkspaceBootstrap,
    SigningWorkspaceBundle,
)
from foliaseal.presentation.qt.single_instance import OpenRequest


def test_app_frame_uses_poppler_raster_backend_by_default() -> None:
    defaults = FoliaSealAppFrame.__init__.__kwdefaults__
    assert defaults is not None
    assert defaults["render_backend_factory"] is PopplerPdfRenderBackend


def test_app_frame_builds_a_lazy_signing_executor_by_default(tmp_path: Path) -> None:
    frame = FoliaSealAppFrame(
        bindings=_fake_bindings(),
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        shell_factory=_FakeShellFactory(_FakeShell()),
        render_backend_factory=lambda: object(),
    )

    assert isinstance(frame._sign_executor, LazySigningRequestExecutor)  # noqa: SLF001


def test_text_commands_are_typed_and_owned_by_normative_menus() -> None:
    assert [definition.command_id for definition in EDIT_COMMAND_DEFINITIONS] == [
        AppFrameCommandId.COPY
    ]
    assert [definition.command_id for definition in VIEW_COMMAND_DEFINITIONS] == [
        AppFrameCommandId.PREVIOUS_PAGE,
        AppFrameCommandId.NEXT_PAGE,
        AppFrameCommandId.BACK,
        AppFrameCommandId.FORWARD,
        AppFrameCommandId.SELECT_TEXT,
        AppFrameCommandId.ZOOM_IN,
        AppFrameCommandId.ZOOM_OUT,
        AppFrameCommandId.RESET_ZOOM,
        AppFrameCommandId.FIT_PAGE,
        AppFrameCommandId.FIT_WIDTH,
        AppFrameCommandId.FIND,
        AppFrameCommandId.DOCUMENT_SIGNATURES,
    ]
    assert EDIT_COMMAND_DEFINITIONS[0].menu == "Edit"
    assert EDIT_COMMAND_DEFINITIONS[0].shortcut == "Ctrl+C"
    assert VIEW_COMMAND_DEFINITIONS[-1].menu == "View"


def test_view_fit_commands_are_typed_and_use_conventional_shortcuts() -> None:
    assert [definition.command_id for definition in VIEW_COMMAND_DEFINITIONS] == [
        AppFrameCommandId.PREVIOUS_PAGE,
        AppFrameCommandId.NEXT_PAGE,
        AppFrameCommandId.BACK,
        AppFrameCommandId.FORWARD,
        AppFrameCommandId.SELECT_TEXT,
        AppFrameCommandId.ZOOM_IN,
        AppFrameCommandId.ZOOM_OUT,
        AppFrameCommandId.RESET_ZOOM,
        AppFrameCommandId.FIT_PAGE,
        AppFrameCommandId.FIT_WIDTH,
        AppFrameCommandId.FIND,
        AppFrameCommandId.DOCUMENT_SIGNATURES,
    ]
    assert [definition.shortcut for definition in VIEW_COMMAND_DEFINITIONS[-3:]] == [
        "Ctrl+Shift+0",
        "Ctrl+F",
        None,
    ]
    assert [definition.shortcut for definition in VIEW_COMMAND_DEFINITIONS[5:8]] == [
        "Ctrl++",
        "Ctrl+-",
        None,
    ]


def test_signing_commands_are_typed_and_keep_unsupported_placement_actions_absent() -> None:
    assert [definition.command_id for definition in SIGNING_COMMAND_DEFINITIONS] == [
        AppFrameCommandId.SIGNATURE_LIBRARY,
        AppFrameCommandId.SIGN_AND_SAVE,
    ]
    assert [definition.text for definition in SIGNING_COMMAND_DEFINITIONS] == [
        "Signature Library",
        "Sign and save",
    ]
    assert [definition.shortcut for definition in SIGNING_COMMAND_DEFINITIONS] == [None, None]
    assert all(definition.menu == "Signing" for definition in SIGNING_COMMAND_DEFINITIONS)


def test_app_frame_applies_window_baseline_and_normalizes_appearance_mode(tmp_path: Path) -> None:
    settings = AppSettings(
        schema_version=1,
        default_output_directory=str(tmp_path / "signed"),
        default_open_directory=str(tmp_path / "source"),
        linux_packaging_channel="unknown",
        ui={"appearance_mode": "DARK"},
    )
    bindings = _fake_bindings()
    frame = FoliaSealAppFrame(
        bindings=bindings,
        app_settings=settings,
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        shell_factory=_FakeShellFactory(_FakeShell()),
        render_backend_factory=lambda: object(),
    )

    assert frame.window.minimum_size == (1100, 700)
    assert frame.appearance_mode == "dark"


class _FakeSignal:
    def __init__(self) -> None:
        self._callbacks = []

    def connect(self, callback):
        self._callbacks.append(callback)

    def emit(self, *args):
        for callback in list(self._callbacks):
            callback(*args)


class _FakeAction:
    def __init__(self, text, parent=None) -> None:
        self.text = text
        self.parent = parent
        self.triggered = _FakeSignal()
        self.shortcut = None
        self.enabled = True
        self.checkable = False
        self.checked = False
        self.icon = None
        self.object_name = None
        self.tool_tip = None
        self.status_tip = None

    def setShortcut(self, shortcut):  # noqa: N802
        self.shortcut = shortcut

    def setEnabled(self, enabled):  # noqa: N802
        self.enabled = bool(enabled)

    def setIcon(self, icon):  # noqa: N802
        self.icon = icon

    def setCheckable(self, checkable):  # noqa: N802
        self.checkable = bool(checkable)

    def setObjectName(self, name):  # noqa: N802
        self.object_name = name

    def setToolTip(self, text):  # noqa: N802
        self.tool_tip = text

    def setStatusTip(self, text):  # noqa: N802
        self.status_tip = text

    def setChecked(self, checked):  # noqa: N802
        self.checked = bool(checked)

    def isChecked(self):  # noqa: N802
        return self.checked

    def trigger(self) -> None:
        if self.checkable:
            self.checked = not self.checked
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
        self.minimum_size = None
        self.raise_calls = 0
        self.activate_calls = 0
        self.geometry_value = _FakeRect(0, 0, 1100, 700)
        self.maximized = False
        self.geometry_set_calls = []
        self.maximize_calls = 0

    def setWindowTitle(self, title):  # noqa: N802
        self.title = title

    def setMinimumSize(self, width, height):  # noqa: N802
        self.minimum_size = (width, height)

    def setGeometry(self, x, y, width, height):  # noqa: N802
        self.geometry_set_calls.append((x, y, width, height))
        self.geometry_value = _FakeRect(x, y, width, height)

    def geometry(self):
        return self.geometry_value

    def isMaximized(self):  # noqa: N802
        return self.maximized

    def showMaximized(self):  # noqa: N802
        self.maximized = True
        self.maximize_calls += 1

    def menuBar(self):  # noqa: N802
        return self.menu_bar

    def setCentralWidget(self, widget):  # noqa: N802
        self.central_widget = widget

    def show(self) -> None:
        self.show_calls += 1

    def raise_(self) -> None:
        self.raise_calls += 1

    def activateWindow(self) -> None:  # noqa: N802
        self.activate_calls += 1


class _FakeRect:
    def __init__(self, x, y, width, height) -> None:
        self._x = x
        self._y = y
        self._width = width
        self._height = height

    def x(self):
        return self._x

    def y(self):
        return self._y

    def width(self):
        return self._width

    def height(self):
        return self._height


class _FakeCloseEvent:
    def __init__(self) -> None:
        self.accepted = False
        self.ignored = False

    def accept(self) -> None:
        self.accepted = True

    def ignore(self) -> None:
        self.ignored = True


class _FakeLabel:
    def __init__(self, text="") -> None:
        self.text = text
        self.word_wrap = False
        self.layout = None
        self.visible = True

    def setText(self, text):  # noqa: N802
        self.text = text

    def setWordWrap(self, value):  # noqa: N802
        self.word_wrap = bool(value)

    def setLayout(self, layout):  # noqa: N802
        self.layout = layout

    def setVisible(self, visible):  # noqa: N802
        self.visible = bool(visible)

    def deleteLater(self) -> None:  # noqa: N802
        self.deleted = True


class _FakeDialog:
    Accepted = 1
    Rejected = 0

    def __init__(self, parent=None) -> None:
        self.parent = parent
        self.title = ""
        self.result = self.Rejected
        self.layout = None
        self.visible = False
        self.show_calls = 0

    def setWindowTitle(self, title):  # noqa: N802
        self.title = title

    def setLayout(self, layout):  # noqa: N802
        self.layout = layout

    def exec(self):
        return self.result

    def show(self) -> None:
        self.show_calls += 1
        self.visible = True

    def raise_(self) -> None:
        return None

    def activateWindow(self) -> None:  # noqa: N802
        return None

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

    def addWidget(self, widget, *args):  # noqa: N802
        self.rows.append((widget, *args))

    def addStretch(self, *args):  # noqa: N802
        self.rows.append(("stretch", *args))

    def setContentsMargins(self, *args):  # noqa: N802
        return None

    def setSpacing(self, *args):  # noqa: N802
        return None


class _FakeLineEdit:
    def __init__(self, text="") -> None:
        self._text = text
        self.textChanged = _FakeSignal()

    def setText(self, text):  # noqa: N802
        self._text = text
        self.textChanged.emit(text)

    def text(self):
        return self._text

    def setPlaceholderText(self, text):  # noqa: N802
        self.placeholder_text = text


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
        self.currentTextChanged = _FakeSignal()

    def addItem(self, text, user_data=None):  # noqa: N802
        self.items.append((text, user_data))
        if self.current_index < 0:
            self.current_index = 0

    def addItems(self, items):  # noqa: N802
        for item in items:
            self.addItem(item)

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

    def setItemData(self, index, value):  # noqa: N802
        text, _ = self.items[index]
        self.items[index] = (text, value)

    def currentText(self):  # noqa: N802
        if self.current_index < 0:
            return ""
        return self.items[self.current_index][0]

    def count(self):
        return len(self.items)


class _FakePushButton:
    def __init__(self, text="") -> None:
        self.text = text
        self.clicked = _FakeSignal()
        self.icon = None
        self.tooltip = None

    def click(self) -> None:
        self.clicked.emit()

    def setIcon(self, icon):  # noqa: N802
        self.icon = icon

    def setToolTip(self, text):  # noqa: N802
        self.tooltip = text


class _FakeIcon:
    def __init__(self, path="") -> None:
        self.path = path


class _FakeFileDialog:
    def __init__(self) -> None:
        self.open_calls = []
        self.save_calls = []
        self.directory_calls = []
        self.next_open_file_name = ""
        self.next_save_file_name = ""
        self.next_directory = ""

    def getOpenFileName(self, parent, title, directory, file_filter):  # noqa: N802
        self.open_calls.append((parent, title, directory, file_filter))
        return (self.next_open_file_name, file_filter)

    def getSaveFileName(self, parent, title, directory, file_filter):  # noqa: N802
        self.save_calls.append((parent, title, directory, file_filter))
        return (self.next_save_file_name, file_filter)

    def getExistingDirectory(self, parent, title, directory):  # noqa: N802
        self.directory_calls.append((parent, title, directory))
        return self.next_directory


class _FakeMessageBox:
    Discard = 1
    Yes = Discard
    Cancel = 2
    No = Cancel
    Save = 3

    def __init__(self) -> None:
        self.warning_calls = []
        self.information_calls = []
        self.question_calls = []
        self.next_question_result = self.No

    def warning(self, parent, title, text):
        self.warning_calls.append((parent, title, text))

    def information(self, parent, title, text):
        self.information_calls.append((parent, title, text))

    def question(self, parent, title, text):
        self.question_calls.append((parent, title, text))
        return self.next_question_result


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
    quit_calls = 0

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

    @classmethod
    def quit(cls):
        cls.quit_calls += 1


class _FakeShell:
    def __init__(self) -> None:
        self.refresh_certificate_configurations_calls = 0
        self.refresh_signature_profiles_calls = 0
        self.applied_settings = []
        self.output_dialog_defaults = []
        self.choose_output_pdf_path_calls = 0
        self.submit_sign_request_calls = 0
        self.can_submit_sign_request_value = False
        self.explicit_output_pdf_path = False
        self.set_document_text_selection_mode_calls = []
        self.document_text_selection_mode = False
        self.can_copy_selected_text = False
        self.copy_selected_document_text_calls = 0
        self.focus_document_search_calls = 0
        self.certificate_catalog = CertificateCatalog(schema_version=1)
        self.testing_adapter = object()
        self.close_calls = 0
        self.delete_later_calls = 0
        self.go_to_previous_page_calls = 0
        self.go_to_next_page_calls = 0
        self.go_back_link_calls = 0
        self.go_forward_link_calls = 0
        self.back_link_available = False
        self.forward_link_available = False
        self.zoom_in_view_calls = 0
        self.zoom_out_view_calls = 0
        self.reset_zoom_view_calls = 0
        self.current_page = 0
        self.page_count = 1
        self.status_callback = None
        self.unsaved_changes = False
        self.discard_draft_calls = 0
        self.clear_session_secrets_calls = 0

    def apply_app_settings(self, settings) -> None:
        self.app_settings = settings
        self.applied_settings.append(settings)
        self.output_dialog_defaults.append(settings.default_output_directory)

    def refresh_certificate_configurations(self) -> CertificateCatalog:
        self.refresh_certificate_configurations_calls += 1
        return self.certificate_catalog

    def refresh_signature_profiles(self) -> None:
        self.refresh_signature_profiles_calls += 1

    def choose_output_pdf_path(self):
        self.choose_output_pdf_path_calls += 1
        self.explicit_output_pdf_path = True
        return "/tmp/signed-output.pdf"

    def has_explicit_output_pdf_path(self):
        return self.explicit_output_pdf_path

    def has_unsaved_changes(self):
        return self.unsaved_changes

    def discard_draft(self) -> None:
        self.discard_draft_calls += 1
        self.unsaved_changes = False
        self.clear_session_secrets()

    def clear_session_secrets(self) -> None:
        self.clear_session_secrets_calls += 1

    def submit_sign_request(self):
        self.submit_sign_request_calls += 1
        return None

    def can_submit_sign_request(self) -> bool:
        return self.can_submit_sign_request_value

    def set_document_text_selection_mode(self, enabled: bool) -> bool:
        self.set_document_text_selection_mode_calls.append(bool(enabled))
        self.document_text_selection_mode = bool(enabled)
        return bool(enabled)

    def document_text_selection_mode_enabled(self) -> bool:
        return self.document_text_selection_mode

    def can_copy_selected_document_text(self) -> bool:
        return self.can_copy_selected_text

    def copy_selected_document_text(self) -> str | None:
        self.copy_selected_document_text_calls += 1
        return "Alice Example"

    def go_to_previous_page(self) -> None:
        self.go_to_previous_page_calls += 1
        self.current_page = max(self.current_page - 1, 0)
        if callable(self.status_callback):
            self.status_callback("navigation_changed")

    def go_to_next_page(self) -> None:
        self.go_to_next_page_calls += 1
        self.current_page = min(self.current_page + 1, self.page_count - 1)
        if callable(self.status_callback):
            self.status_callback("navigation_changed")

    def can_go_previous_page(self) -> bool:
        return self.current_page > 0

    def can_go_next_page(self) -> bool:
        return self.current_page < self.page_count - 1

    def go_back_link(self) -> None:
        self.go_back_link_calls += 1
        if self.back_link_available:
            self.back_link_available = False
            self.forward_link_available = True
        if callable(self.status_callback):
            self.status_callback("link_history_back")

    def go_forward_link(self) -> None:
        self.go_forward_link_calls += 1
        if self.forward_link_available:
            self.forward_link_available = False
            self.back_link_available = True
        if callable(self.status_callback):
            self.status_callback("link_history_forward")

    def can_go_back_link(self) -> bool:
        return self.back_link_available

    def can_go_forward_link(self) -> bool:
        return self.forward_link_available

    def reset_zoom_view(self) -> None:
        self.reset_zoom_view_calls += 1

    def zoom_in_view(self) -> None:
        self.zoom_in_view_calls += 1

    def zoom_out_view(self) -> None:
        self.zoom_out_view_calls += 1

    def fit_page_view(self) -> None:
        self.fit_page_view_calls = getattr(self, "fit_page_view_calls", 0) + 1

    def fit_width_view(self) -> None:
        self.fit_width_view_calls = getattr(self, "fit_width_view_calls", 0) + 1

    def focus_document_search(self) -> None:
        self.focus_document_search_calls += 1

    def close(self) -> None:
        self.close_calls += 1

    def deleteLater(self) -> None:  # noqa: N802
        self.delete_later_calls += 1


class _FakeShellPort:
    def __init__(self, shell_widget) -> None:
        self.shell_widget = shell_widget

    def widget(self):
        return self.shell_widget

    def choose_output_pdf_path(self):
        return self.shell_widget.choose_output_pdf_path()

    def has_explicit_output_pdf_path(self):
        return self.shell_widget.has_explicit_output_pdf_path()

    def has_unsaved_changes(self):
        return self.shell_widget.has_unsaved_changes()

    def discard_draft(self) -> None:
        self.shell_widget.discard_draft()

    def clear_session_secrets(self) -> None:
        self.shell_widget.clear_session_secrets()

    def apply_app_settings(self, settings) -> None:
        self.shell_widget.apply_app_settings(settings)

    def refresh_certificate_configurations(self) -> CertificateCatalog:
        return self.shell_widget.refresh_certificate_configurations()

    def refresh_signature_profiles(self) -> None:
        self.shell_widget.refresh_signature_profiles()

    def set_document_text_selection_mode(self, enabled: bool) -> bool:
        return self.shell_widget.set_document_text_selection_mode(enabled)

    def document_text_selection_mode_enabled(self) -> bool:
        return self.shell_widget.document_text_selection_mode_enabled()

    def can_copy_selected_document_text(self) -> bool:
        return self.shell_widget.can_copy_selected_document_text()

    def copy_selected_document_text(self) -> str | None:
        return self.shell_widget.copy_selected_document_text()


class _FakeShellFactory:
    def __init__(self, shell_widget, *, bootstrap_calls=None) -> None:
        self.shell_widget = shell_widget
        self.bootstrap_calls = bootstrap_calls if bootstrap_calls is not None else []

    def create(self, bootstrap: SigningWorkspaceBootstrap):
        self.bootstrap_calls.append(bootstrap)
        self.shell_widget.status_callback = bootstrap.on_status_change
        return SigningWorkspaceBundle(
            maintenance=_FakeShellPort(self.shell_widget),
            session=QtSigningWorkspaceSessionPort(self.shell_widget),
            testing=self.shell_widget.testing_adapter,
            view=QtWorkspaceView(self.shell_widget),
        )


class _FakeInstanceCoordinator:
    def __init__(self, *, primary: bool, queued_request: OpenRequest | None = None) -> None:
        self.primary = primary
        self.queued_request = queued_request
        self.handler = None
        self.requests = []
        self.close_calls = 0

    def set_request_handler(self, handler) -> None:
        self.handler = handler

    def start_or_forward(self, request: OpenRequest) -> bool:
        self.requests.append(request)
        if self.primary and self.queued_request is not None:
            self.handler(self.queued_request)
        return self.primary

    def close(self) -> None:
        self.close_calls += 1


class _SequenceShellFactory:
    def __init__(self, *shells) -> None:
        self.shells = list(shells)
        self.bootstrap_calls: list[SigningWorkspaceBootstrap] = []

    def create(self, bootstrap: SigningWorkspaceBootstrap):
        self.bootstrap_calls.append(bootstrap)
        shell = self.shells.pop(0)
        return SigningWorkspaceBundle(
            maintenance=_FakeShellPort(shell),
            session=QtSigningWorkspaceSessionPort(shell),
            testing=shell.testing_adapter,
            view=QtWorkspaceView(shell),
        )


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
    _FakeQApplication.quit_calls = 0
    return QtAppFrameBindings(
        q_main_window=_FakeMainWindow,
        q_dialog=_FakeDialog,
        q_form_layout=_FakeFormLayout,
        q_group_box=_FakeLabel,
        q_label=_FakeLabel,
        q_line_edit=_FakeLineEdit,
        q_check_box=_FakeCheckBox,
        q_combo_box=_FakeComboBox,
        q_push_button=_FakePushButton,
        q_file_dialog=file_dialog,
        q_message_box=message_box,
        q_action=_FakeAction,
        q_icon=_FakeIcon,
        q_application=_FakeQApplication,
        qpdf_document=_FakeQPdfDocument,
        q_widget=_FakeLabel,
        q_hbox_layout=_FakeFormLayout,
        q_vbox_layout=_FakeFormLayout,
    )


def _settings(tmp_path: Path) -> AppSettings:
    return AppSettings(
        schema_version=1,
        default_output_directory=str(tmp_path / "signed"),
        default_open_directory=str(tmp_path / "source"),
        linux_packaging_channel="unknown",
        ui={},
    )


def test_qt_signing_workspace_factory_delegates_typed_bootstrap_to_shell_adapter(
    tmp_path: Path, monkeypatch
) -> None:
    captured = {}
    shell = _FakeShell()

    class _FakeShellAdapter:
        def create_from_bootstrap(self, bootstrap):
            captured["bootstrap"] = bootstrap
            return shell

    monkeypatch.setattr(
        signing_shell_port_module,
        "SigningShellAdapter",
        _FakeShellAdapter,
    )
    bootstrap = SigningWorkspaceBootstrap(
        viewer_workflow=object(),
        signing_workflow=object(),
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        certificate_catalog_store=CertificateCatalogStore(
            storage_dir=tmp_path / "Certificates"
        ),
        certificate_material_port=object(),
        reusable_objects=ReusableSigningObjects(
            InMemoryCatalogRepository(SignaturePresetCatalog(schema_version=1))
        ),
        sign_executor=object(),
        on_sign_request=lambda request: None,
        on_open_signed_output=lambda path: None,
        on_error=lambda message: None,
        on_status_change=lambda status: None,
    )

    bundle = signing_shell_port_module.QtSigningWorkspaceFactory().create(bootstrap)

    assert bundle.view.mount_target() is shell
    assert bundle.testing is shell.testing_adapter
    assert captured == {"bootstrap": bootstrap}


def test_qt_signing_workspace_port_forwards_public_shell_contract(tmp_path: Path) -> None:
    shell = _FakeShell()
    port = QtSigningWorkspacePort(shell_widget=shell)
    settings = _settings(tmp_path)

    assert port.choose_output_pdf_path() == "/tmp/signed-output.pdf"

    port.apply_app_settings(settings)

    assert shell.applied_settings == [settings]
    assert shell.output_dialog_defaults == [settings.default_output_directory]
    assert shell.app_settings == settings

    catalog = port.refresh_certificate_configurations()

    assert catalog is shell.certificate_catalog
    assert shell.refresh_certificate_configurations_calls == 1
    port.refresh_signature_profiles()
    assert shell.refresh_signature_profiles_calls == 1
    assert port.set_document_text_selection_mode(True) is True
    assert shell.set_document_text_selection_mode_calls == [True]
    assert port.copy_selected_document_text() == "Alice Example"
    assert shell.copy_selected_document_text_calls == 1

    shell.unsaved_changes = True
    assert port.has_unsaved_changes() is True
    port.clear_session_secrets()
    assert shell.clear_session_secrets_calls == 1
    port.discard_draft()
    assert shell.discard_draft_calls == 1
    assert port.has_unsaved_changes() is False


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


def test_app_frame_source_reload_and_ignore_preserve_the_authored_draft(
    tmp_path: Path,
) -> None:
    bindings = _fake_bindings()
    first = _FakeShell()
    second = _FakeShell()
    frame = FoliaSealAppFrame(
        bindings=bindings,
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        shell_factory=_SequenceShellFactory(first, second),
        render_backend_factory=lambda: object(),
    )
    source = tmp_path / "source" / "contract.pdf"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"original")
    frame.open_pdf_path(source)
    workflow = frame.current_signing_workflow
    assert workflow is not None
    workflow.passphrase = "keep-this-secret"
    workflow.set_signature_rect(
        SignatureRect(page_index=0, left_pt=20.0, bottom_pt=20.0, width_pt=180.0, height_pt=60.0)
    )
    snapshot = workflow.snapshot_for_source_transfer()
    source.write_bytes(b"changed")

    # The real frame owns the callback through the typed bootstrap seam.
    callback = frame._workspace_host._environment.on_source_reload  # noqa: SLF001
    assert callback is not None
    reloaded = callback()

    assert reloaded is second
    assert frame.current_shell is second
    assert first.close_calls == 1
    assert frame.current_signing_workflow is not workflow
    assert frame.current_signing_workflow is not None
    assert frame.current_signing_workflow.passphrase == snapshot.passphrase
    assert frame.current_signing_workflow.signature_rect == snapshot.signature_rect
    assert frame.current_signing_workflow.has_unsaved_changes is True
    assert frame.current_signing_workflow.document_safety_decision().status.value == "unchanged"


def test_app_frame_locates_missing_source_before_replacing_workspace(tmp_path: Path) -> None:
    bindings = _fake_bindings()
    first = _FakeShell()
    second = _FakeShell()
    frame = FoliaSealAppFrame(
        bindings=bindings,
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        shell_factory=_SequenceShellFactory(first, second),
        render_backend_factory=lambda: object(),
    )
    source = tmp_path / "source" / "missing.pdf"
    replacement = tmp_path / "source" / "replacement.pdf"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"source")
    replacement.write_bytes(b"replacement")
    frame.open_pdf_path(source)
    workflow = frame.current_signing_workflow
    assert workflow is not None
    workflow.passphrase = "preserve-me"
    source.unlink()
    bindings.q_file_dialog.next_open_file_name = str(replacement)

    callback = frame._workspace_host._environment.on_source_locate  # noqa: SLF001
    assert callback is not None
    located = callback()

    assert located is second
    assert frame.current_workspace is not None
    assert frame.current_workspace.source_pdf == replacement
    assert frame.current_signing_workflow is not None
    assert frame.current_signing_workflow.passphrase == "preserve-me"
    assert bindings.q_file_dialog.open_calls[-1][1] == "Locate source PDF"

    source.write_bytes(b"changed-again")
    current_shell = frame.current_shell
    ignore = frame._workspace_host._environment.on_source_ignore  # noqa: SLF001
    assert ignore is not None
    assert ignore() is True
    assert frame.current_shell is current_shell
    assert frame.current_signing_workflow.document_safety_decision().status.value == "unchanged"


def test_app_frame_replacing_workspace_closes_previous_shell(
    tmp_path: Path,
) -> None:
    bindings = _fake_bindings()
    first = _FakeShell()
    second = _FakeShell()
    frame = FoliaSealAppFrame(
        bindings=bindings,
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        shell_factory=_SequenceShellFactory(first, second),
        render_backend_factory=lambda: object(),
    )

    frame.open_pdf_path(tmp_path / "source" / "first.pdf")
    frame.open_pdf_path(tmp_path / "source" / "second.pdf")

    assert frame.window.central_widget is second
    assert frame.current_shell is second
    assert first.close_calls == 1
    assert first.delete_later_calls == 1
    assert second.close_calls == 0


def test_app_frame_failed_replacement_preserves_previous_shell(
    tmp_path: Path,
) -> None:
    bindings = _fake_bindings()
    first = _FakeShell()
    frame = FoliaSealAppFrame(
        bindings=bindings,
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        shell_factory=_FakeShellFactory(first),
        render_backend_factory=lambda: object(),
    )
    frame.open_pdf_path(tmp_path / "source" / "first.pdf")
    prior_action_state = frame.workspace_action_state
    _FakeQPdfDocument.next_status = _FakeQPdfDocument.Error.Failed

    result = frame.open_pdf_path(tmp_path / "source" / "broken.pdf")

    assert result is None
    assert frame.window.central_widget is first
    assert frame.current_shell is first
    assert frame.workspace_action_state is prior_action_state
    assert first.close_calls == 0
    assert len(bindings.q_message_box.warning_calls) == 1


def test_app_frame_failed_replacement_mount_preserves_action_state(
    monkeypatch,
    tmp_path: Path,
) -> None:
    bindings = _fake_bindings()
    frame = FoliaSealAppFrame(
        bindings=bindings,
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        shell_factory=_SequenceShellFactory(_FakeShell(), _FakeShell()),
        render_backend_factory=lambda: object(),
    )
    frame.open_pdf_path(tmp_path / "source" / "first.pdf")
    prior_action_state = frame.workspace_action_state

    def fail_mount(_mount, widget) -> None:
        raise RuntimeError("mount failed")

    monkeypatch.setattr(type(frame._workspace_mount), "mount", fail_mount)
    result = frame.open_pdf_path(tmp_path / "source" / "second.pdf")

    assert result is None
    assert frame.workspace_action_state is prior_action_state
    assert frame.current_workspace is not None
    assert len(bindings.q_message_box.warning_calls) == 1


def test_app_frame_placeholder_mount_failure_preserves_action_state(
    monkeypatch,
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
    frame.open_pdf_path(tmp_path / "source" / "first.pdf")
    prior_action_state = frame.workspace_action_state

    def fail_mount(_mount, widget) -> None:
        raise RuntimeError("placeholder mount failed")

    monkeypatch.setattr(type(frame._workspace_mount), "mount", fail_mount)
    with pytest.raises(RuntimeError, match="placeholder mount failed"):
        frame.close_workspace()

    assert frame.current_workspace is None
    assert frame.workspace_action_state is prior_action_state


def test_app_frame_close_workspace_is_idempotent_and_restores_placeholder(
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
    frame.open_pdf_path(tmp_path / "source" / "first.pdf")

    frame.close_workspace()
    frame.close_workspace()

    assert frame.current_shell is None
    assert frame.current_workspace is None
    assert shell.close_calls == 1
    assert shell.delete_later_calls == 1
    assert bindings.q_message_box.warning_calls == []
    assert frame.window.menu_bar.menus[0].actions[1].enabled is False
    assert frame.window.menu_bar.menus[1].actions[0].enabled is False
    assert frame.window.menu_bar.menus[2].actions[4].enabled is False


def test_app_frame_no_document_placeholder_exposes_open_and_library_actions(
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

    placeholder = frame.window.central_widget

    assert placeholder.layout is not None
    assert [row[0].text for row in placeholder.layout.rows] == [
        "No document open. Open a PDF to begin signing, or manage reusable signing objects.",
        "Open a PDF…",
        "Manage Signature Library…",
    ]
    assert frame._placeholder_open_button.text == "Open a PDF…"
    assert frame._placeholder_library_button.text == "Manage Signature Library…"
    assert frame.workspace_action_state.workspace_open is False


def test_app_frame_library_action_is_modeless_and_reused(tmp_path: Path) -> None:
    bindings = _fake_bindings()
    frame = FoliaSealAppFrame(
        bindings=bindings,
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        shell_factory=_FakeShellFactory(_FakeShell()),
        render_backend_factory=lambda: object(),
    )

    first = frame.show_reusable_object_library()
    second = frame.show_reusable_object_library()

    assert second is first
    assert first.controls.dialog.show_calls == 2
    assert first.controls.dialog.visible is True


def test_signing_menu_routes_library_and_sign_save_through_existing_boundaries(
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

    actions = frame.command_actions()
    library_action = actions[AppFrameCommandId.SIGNATURE_LIBRARY]
    sign_action = actions[AppFrameCommandId.SIGN_AND_SAVE]
    assert library_action.enabled is True
    assert sign_action.enabled is False

    library_action.trigger()
    assert frame.reusable_object_library_dialog is not None

    frame.open_pdf_path(tmp_path / "source" / "contract.pdf")
    assert sign_action.enabled is False
    frame.command_actions()[AppFrameCommandId.SELECT_TEXT].trigger()
    frame._handle_status_change("document_text_mode_changed")
    assert sign_action.enabled is False
    shell.can_submit_sign_request_value = True
    shell.status_callback("signing_readiness_changed")
    assert sign_action.enabled is True
    frame._handle_status_change("sign_started")
    assert sign_action.enabled is False
    frame._handle_status_change("sign_failure")
    shell.can_submit_sign_request_value = True
    frame._handle_status_change("signing_readiness_changed")
    assert sign_action.enabled is True
    sign_action.trigger()
    assert shell.choose_output_pdf_path_calls == 1
    assert shell.submit_sign_request_calls == 1


def test_first_use_library_is_presets_first_and_refreshes_active_shell_without_selection(
    tmp_path: Path,
) -> None:
    from foliaseal.application.signature_library_session import LibraryCatalog
    from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
    from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
    from foliaseal.presentation.qt.app_frame_profile_library import ReusableObjectLibraryDialog
    from tests.unit.test_qt_signing_shell import _fake_bindings as shell_fake_bindings

    bindings = _fake_bindings()
    shell = _FakeShell()
    frame = FoliaSealAppFrame(
        bindings=bindings,
        app_settings=AppSettings(
            schema_version=1,
            default_output_directory=str(tmp_path / "signed"),
            default_open_directory=str(tmp_path / "source"),
            linux_packaging_channel="unknown",
            ui={"library_last_catalog": "appearances"},
        ),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        certificate_catalog_store=CertificateCatalogStore(storage_dir=tmp_path / "certificates"),
        preset_catalog_store=SignaturePresetCatalogStore(storage_dir=tmp_path / "profiles"),
        shell_factory=_FakeShellFactory(shell),
        render_backend_factory=lambda: object(),
    )
    frame.open_pdf_path(tmp_path / "source" / "contract.pdf")

    library = frame.show_first_use_preset_library()
    assert library._session.catalog is LibraryCatalog.PRESETS  # noqa: SLF001
    assert frame.app_settings.ui_settings.library_last_catalog == "appearances"
    library = ReusableObjectLibraryDialog(
        bindings=shell_fake_bindings(),
        parent=None,
        library=frame._reusable_objects,  # noqa: SLF001
        certificate_catalog=frame._certificate_catalog_store.load_catalog(),  # noqa: SLF001
        on_reusable_objects_changed=frame._refresh_shell_signature_profiles,  # noqa: SLF001
    )
    library.controls.create_button.click()
    preset_editor = library.controls.preset_editor
    assert preset_editor is not None
    preset_editor.controls.name_input.setText("First-use preset")
    preset_editor.controls.create_appearance_button.click()
    appearance_editor = preset_editor.appearance_child
    assert appearance_editor is not None
    appearance_editor.controls.name_input.setText("First-use appearance")
    appearance_editor.controls.save_button.click()
    preset_editor.controls.save_button.click()

    assert shell.refresh_signature_profiles_calls == 2
    assert frame.current_signing_workflow.selected_signature_preset_id is None


def test_app_frame_installs_file_and_settings_menu_actions(tmp_path: Path) -> None:
    bindings = _fake_bindings()
    frame = FoliaSealAppFrame(
        bindings=bindings,
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        shell_factory=_FakeShellFactory(_FakeShell()),
        render_backend_factory=lambda: object(),
    )

    assert [menu.title for menu in frame.window.menu_bar.menus] == [
        "File",
        "Edit",
        "View",
        "Signing",
        "Settings",
    ]
    assert [action.text for action in frame.window.menu_bar.menus[0].actions] == [
        "&Open",
        "&Save",
        "Save &As",
        "&Close",
        "E&xit",
    ]
    assert frame.window.menu_bar.menus[0].actions[0].shortcut == "Ctrl+O"
    assert [action.shortcut for action in frame.window.menu_bar.menus[0].actions] == [
        "Ctrl+O",
        "Ctrl+S",
        "Ctrl+Shift+S",
        "Ctrl+W",
        "Ctrl+Q",
    ]
    assert [action.enabled for action in frame.window.menu_bar.menus[0].actions] == [
        True,
        False,
        False,
        False,
        True,
    ]
    assert [action.object_name for action in frame.window.menu_bar.menus[0].actions] == [
        definition.command_id.value for definition in FILE_COMMAND_DEFINITIONS
    ]
    assert [action.tool_tip for action in frame.window.menu_bar.menus[0].actions] == [
        definition.accessible_name for definition in FILE_COMMAND_DEFINITIONS
    ]
    assert [action.status_tip for action in frame.window.menu_bar.menus[0].actions] == [
        definition.accessible_name for definition in FILE_COMMAND_DEFINITIONS
    ]
    assert [action.text for action in frame.window.menu_bar.menus[1].actions] == ["&Copy"]
    assert frame.window.menu_bar.menus[1].actions[0].checkable is False
    assert frame.window.menu_bar.menus[1].actions[0].enabled is False
    assert frame.window.menu_bar.menus[1].actions[0].icon.path.endswith("copy.svg")
    assert [action.text for action in frame.window.menu_bar.menus[2].actions] == [
        "Previous &Page",
        "Next P&age",
        "&Back",
        "&Forward",
        "&Select Text",
        "Zoom &In",
        "Zoom &Out",
        "Reset &Zoom",
        "Fit &Page",
        "Fit &Width",
        "&Find",
        "Document &Signatures",
    ]
    assert [action.shortcut for action in frame.window.menu_bar.menus[2].actions] == [
        "Page Up",
        "Page Down",
        "Alt+Left",
        "Alt+Right",
        None,
        "Ctrl++",
        "Ctrl+-",
        None,
        "Ctrl+0",
        "Ctrl+Shift+0",
        "Ctrl+F",
        None,
    ]
    assert [action.enabled for action in frame.window.menu_bar.menus[2].actions] == [
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
    ]
    assert frame.window.menu_bar.menus[2].actions[4].checkable is True
    assert frame.window.menu_bar.menus[2].actions[4].icon.path.endswith("text-select.svg")
    assert [action.text for action in frame.window.menu_bar.menus[3].actions] == [
        definition.mnemonic_text for definition in SIGNING_COMMAND_DEFINITIONS
    ]
    assert [action.shortcut for action in frame.window.menu_bar.menus[3].actions] == [
        definition.shortcut for definition in SIGNING_COMMAND_DEFINITIONS
    ]
    assert [action.tool_tip for action in frame.window.menu_bar.menus[3].actions] == [
        definition.accessible_name for definition in SIGNING_COMMAND_DEFINITIONS
    ]
    assert [action.enabled for action in frame.window.menu_bar.menus[3].actions] == [True, False]
    assert [action.text for action in frame.window.menu_bar.menus[4].actions] == [
        definition.mnemonic_text for definition in SETTINGS_COMMAND_DEFINITIONS
    ]
    assert [action.shortcut for action in frame.window.menu_bar.menus[4].actions] == [
        definition.shortcut for definition in SETTINGS_COMMAND_DEFINITIONS
    ]
    assert [action.object_name for action in frame.window.menu_bar.menus[4].actions] == [
        definition.command_id.value for definition in SETTINGS_COMMAND_DEFINITIONS
    ]
    assert [action.tool_tip for action in frame.window.menu_bar.menus[4].actions] == [
        definition.accessible_name for definition in SETTINGS_COMMAND_DEFINITIONS
    ]
    assert [action.status_tip for action in frame.window.menu_bar.menus[4].actions] == [
        definition.accessible_name for definition in SETTINGS_COMMAND_DEFINITIONS
    ]
    settings_mnemonics = [
        action.text.replace("&", "").lower()
        for action in frame.window.menu_bar.menus[4].actions
    ]
    mnemonic_letters = [
        action.text[action.text.index("&") + 1].lower()
        for action in frame.window.menu_bar.menus[4].actions
        if "&" in action.text
    ]
    assert len(mnemonic_letters) == len(set(mnemonic_letters))
    assert settings_mnemonics == [
        definition.mnemonic_text.replace("&", "").lower()
        for definition in SETTINGS_COMMAND_DEFINITIONS
    ]
    assert not hasattr(frame.window, "_foliaseal_app_frame")
    assert not hasattr(frame.window, "app_settings")
    assert not hasattr(frame.window, "open_file")
    assert not hasattr(frame.window, "open_pdf_path")
    assert not hasattr(frame.window, "show_app_settings")
    assert not hasattr(frame.window, "show_certificate_creation")
    assert not hasattr(frame.window, "show_certificate_import")
    assert not hasattr(frame.window, "show_certificate_management")

    frame.window.menu_bar.menus[4].actions[0].trigger()

    assert frame.settings_dialog.controls.dialog.title == "Application settings"
    assert (
        frame.settings_dialog.controls.default_open_directory.text()
        == str(tmp_path / "source")
    )

    frame.window.menu_bar.menus[4].actions[1].trigger()
    assert frame.reusable_object_library_dialog is not None
    frame.window.menu_bar.menus[4].actions[2].trigger()
    assert frame.certificate_creation_dialog is not None
    frame.window.menu_bar.menus[4].actions[3].trigger()
    assert frame.certificate_import_dialog is not None
    frame.window.menu_bar.menus[4].actions[4].trigger()
    assert frame.certificate_management_dialog is not None


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

    save_action = frame.window.menu_bar.menus[0].actions[1]
    save_as_action = frame.window.menu_bar.menus[0].actions[2]
    close_action = frame.window.menu_bar.menus[0].actions[3]
    copy_selection_action = frame.window.menu_bar.menus[1].actions[0]
    text_selection_action = frame.window.menu_bar.menus[2].actions[4]

    assert save_action.enabled is False
    assert save_as_action.enabled is False
    assert close_action.enabled is False
    assert text_selection_action.enabled is False
    assert text_selection_action.checked is False
    assert copy_selection_action.enabled is False
    assert frame.workspace_action_state.workspace_open is False

    frame.open_pdf_path(tmp_path / "source" / "contract.pdf")

    assert save_action.enabled is True
    assert save_as_action.enabled is True
    assert close_action.enabled is True
    assert text_selection_action.enabled is True
    assert text_selection_action.checked is False
    assert copy_selection_action.enabled is False
    assert frame.workspace_action_state.workspace_open is True

    save_as_action.trigger()
    text_selection_action.trigger()
    shell.can_copy_selected_text = True
    frame._handle_status_change("document_text_selection_changed")
    copy_selection_action.trigger()

    assert shell.choose_output_pdf_path_calls == 1
    assert shell.set_document_text_selection_mode_calls == [True]
    assert shell.copy_selected_document_text_calls == 1
    assert text_selection_action.checked is True
    assert frame.workspace_action_state.text_selection_checked is True
    assert frame.workspace_action_state.copy_selected_text_enabled is True


def test_app_frame_file_lifecycle_routes_save_close_and_exit(tmp_path: Path) -> None:
    bindings = _fake_bindings()
    shell = _FakeShell()
    frame = FoliaSealAppFrame(
        bindings=bindings,
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        shell_factory=_FakeShellFactory(shell),
        render_backend_factory=lambda: object(),
    )

    file_actions = frame.window.menu_bar.menus[0].actions
    save_action, close_action, exit_action = file_actions[1], file_actions[3], file_actions[4]
    frame.open_pdf_path(tmp_path / "source" / "contract.pdf")

    save_action.trigger()
    assert shell.choose_output_pdf_path_calls == 1
    assert shell.submit_sign_request_calls == 1

    close_action.trigger()
    assert frame.current_workspace is None
    assert close_action.enabled is False

    exit_action.trigger()
    assert _FakeQApplication.quit_calls == 1


def test_app_frame_dirty_lifecycle_requires_confirmation_and_routes_native_close(
    tmp_path: Path,
) -> None:
    bindings = _fake_bindings()
    first = _FakeShell()
    canceled_candidate = _FakeShell()
    second = _FakeShell()
    third = _FakeShell()
    frame = FoliaSealAppFrame(
        bindings=bindings,
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        shell_factory=_SequenceShellFactory(first, canceled_candidate, second, third),
        render_backend_factory=lambda: object(),
    )

    frame.open_pdf_path(tmp_path / "source" / "first.pdf")
    first.unsaved_changes = True
    assert frame.open_pdf_path(tmp_path / "source" / "second.pdf") is None
    assert frame.current_shell is first
    assert first.discard_draft_calls == 0
    assert canceled_candidate.close_calls == 1
    assert len(bindings.q_message_box.question_calls) == 1
    _, prompt_title, prompt_text = bindings.q_message_box.question_calls[0]
    assert prompt_title == "Discard unsigned signing draft?"
    assert "Continue editing" in prompt_text
    assert "open another PDF without saving" in prompt_text

    bindings.q_message_box.next_question_result = _FakeMessageBox.Yes
    assert frame.open_pdf_path(tmp_path / "source" / "second.pdf") is second
    assert first.discard_draft_calls == 1
    assert first.close_calls == 1

    second.unsaved_changes = True
    bindings.q_message_box.next_question_result = _FakeMessageBox.No
    assert frame.close_workspace() is False
    assert frame.current_shell is second
    assert second.discard_draft_calls == 0

    bindings.q_message_box.next_question_result = _FakeMessageBox.Yes
    assert frame.close_workspace() is True
    assert frame.current_workspace is None
    assert second.discard_draft_calls == 1

    frame.open_pdf_path(tmp_path / "source" / "third.pdf")
    third.unsaved_changes = True
    event = _FakeCloseEvent()
    bindings.q_message_box.next_question_result = _FakeMessageBox.No
    frame._handle_window_close_event(event)
    assert event.ignored is True
    assert event.accepted is False
    assert frame.current_shell is third

    bindings.q_message_box.next_question_result = _FakeMessageBox.Yes
    frame._handle_window_close_event(event)
    assert event.accepted is True
    assert third.discard_draft_calls == 1
    assert frame.current_workspace is None


def test_app_frame_failed_candidate_does_not_discard_dirty_workspace(tmp_path: Path) -> None:
    bindings = _fake_bindings()
    shell = _FakeShell()
    frame = FoliaSealAppFrame(
        bindings=bindings,
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        shell_factory=_FakeShellFactory(shell),
        render_backend_factory=lambda: object(),
    )
    frame.open_pdf_path(tmp_path / "source" / "first.pdf")
    shell.unsaved_changes = True
    _FakeQPdfDocument.next_status = _FakeQPdfDocument.Error.Failed

    assert frame.open_pdf_path(tmp_path / "source" / "invalid.pdf") is None
    assert frame.current_shell is shell
    assert shell.unsaved_changes is True
    assert shell.discard_draft_calls == 0
    assert bindings.q_message_box.question_calls == []


def test_app_frame_ready_dirty_prompt_offers_sign_and_save(tmp_path: Path, monkeypatch) -> None:
    bindings = _fake_bindings()
    first = _FakeShell()
    second = _FakeShell()
    frame = FoliaSealAppFrame(
        bindings=bindings,
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        shell_factory=_SequenceShellFactory(first, second),
        render_backend_factory=lambda: object(),
    )
    frame.open_pdf_path(tmp_path / "source" / "first.pdf")
    first.unsaved_changes = True
    monkeypatch.setattr(frame, "_workspace_ready_to_sign", lambda workspace: True)
    monkeypatch.setattr(frame, "_sign_and_save_current_workspace", lambda workspace: True)
    bindings.q_message_box.next_question_result = _FakeMessageBox.Save

    assert frame.open_pdf_path(tmp_path / "source" / "second.pdf") is second
    _, _, prompt_text = bindings.q_message_box.question_calls[0]
    assert "Sign and save it before open another PDF" in prompt_text
    assert first.discard_draft_calls == 0


def test_file_command_registry_is_typed_and_normative() -> None:
    assert [definition.command_id for definition in FILE_COMMAND_DEFINITIONS] == list(
        (
            AppFrameCommandId.OPEN,
            AppFrameCommandId.SAVE,
            AppFrameCommandId.SAVE_AS,
            AppFrameCommandId.CLOSE,
            AppFrameCommandId.EXIT,
        )
    )
    assert [definition.text for definition in FILE_COMMAND_DEFINITIONS] == [
        "Open",
        "Save",
        "Save As",
        "Close",
        "Exit",
    ]
    assert [definition.mnemonic_text for definition in FILE_COMMAND_DEFINITIONS] == [
        "&Open",
        "&Save",
        "Save &As",
        "&Close",
        "E&xit",
    ]


def test_view_command_registry_is_typed_and_normative() -> None:
    assert [definition.command_id for definition in VIEW_COMMAND_DEFINITIONS] == [
        AppFrameCommandId.PREVIOUS_PAGE,
        AppFrameCommandId.NEXT_PAGE,
        AppFrameCommandId.BACK,
        AppFrameCommandId.FORWARD,
        AppFrameCommandId.SELECT_TEXT,
        AppFrameCommandId.ZOOM_IN,
        AppFrameCommandId.ZOOM_OUT,
        AppFrameCommandId.RESET_ZOOM,
        AppFrameCommandId.FIT_PAGE,
        AppFrameCommandId.FIT_WIDTH,
        AppFrameCommandId.FIND,
        AppFrameCommandId.DOCUMENT_SIGNATURES,
    ]
    assert [definition.text for definition in VIEW_COMMAND_DEFINITIONS] == [
        "Previous Page",
        "Next Page",
        "Back",
        "Forward",
        "Select Text",
        "Zoom In",
        "Zoom Out",
        "Reset Zoom",
        "Fit Page",
        "Fit Width",
        "Find",
        "Document Signatures",
    ]
    assert [definition.shortcut for definition in VIEW_COMMAND_DEFINITIONS] == [
        "Page Up",
        "Page Down",
        "Alt+Left",
        "Alt+Right",
        None,
        "Ctrl++",
        "Ctrl+-",
        None,
        "Ctrl+0",
        "Ctrl+Shift+0",
        "Ctrl+F",
        None,
    ]


def test_view_page_commands_route_through_the_session_port(tmp_path: Path) -> None:
    bindings = _fake_bindings()
    shell = _FakeShell()
    shell.page_count = 3
    frame = FoliaSealAppFrame(
        bindings=bindings,
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        shell_factory=_FakeShellFactory(shell),
        render_backend_factory=lambda: object(),
    )

    view_actions = frame.window.menu_bar.menus[2].actions
    assert [action.enabled for action in view_actions] == [False] * 12
    frame.open_pdf_path(tmp_path / "source" / "contract.pdf")
    assert [action.enabled for action in view_actions] == [False, True, False, False] + [True] * 8

    view_actions[1].trigger()
    assert [action.enabled for action in view_actions] == [True, True, False, False] + [True] * 8
    view_actions[1].trigger()
    assert [action.enabled for action in view_actions] == [True, False, False, False] + [True] * 8
    view_actions[0].trigger()
    assert [action.enabled for action in view_actions] == [True, True, False, False] + [True] * 8
    view_actions[0].trigger()
    assert [action.enabled for action in view_actions] == [False, True, False, False] + [True] * 8

    shell.go_to_next_page()
    assert [action.enabled for action in view_actions] == [True, True, False, False] + [True] * 8
    shell.go_to_next_page()
    assert [action.enabled for action in view_actions] == [True, False, False, False] + [True] * 8
    shell.go_to_previous_page()
    assert [action.enabled for action in view_actions] == [True, True, False, False] + [True] * 8

    view_actions[5].trigger()
    view_actions[6].trigger()
    view_actions[7].trigger()
    assert shell.zoom_in_view_calls == 1
    assert shell.zoom_out_view_calls == 1
    assert shell.reset_zoom_view_calls == 1
    view_actions[8].trigger()
    view_actions[9].trigger()
    assert shell.fit_page_view_calls == 1
    assert shell.fit_width_view_calls == 1
    view_actions[10].trigger()
    assert shell.focus_document_search_calls == 1

    assert shell.go_to_previous_page_calls == 3
    assert shell.go_to_next_page_calls == 4


def test_view_internal_link_history_commands_route_and_follow_capabilities(tmp_path: Path) -> None:
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
    actions = frame.command_actions()
    back_action = actions[AppFrameCommandId.BACK]
    forward_action = actions[AppFrameCommandId.FORWARD]
    assert back_action.enabled is False
    assert forward_action.enabled is False

    shell.back_link_available = True
    shell.status_callback("link_internal_navigation")
    assert back_action.enabled is True
    assert forward_action.enabled is False

    back_action.trigger()
    assert shell.go_back_link_calls == 1
    assert back_action.enabled is False
    assert forward_action.enabled is True

    forward_action.trigger()
    assert shell.go_forward_link_calls == 1
    assert back_action.enabled is True
    assert forward_action.enabled is False

    shell.back_link_available = True
    shell.forward_link_available = False
    shell.status_callback("link_internal_navigation")
    assert back_action.enabled is True
    assert forward_action.enabled is False


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
    dialog.controls.appearance_mode.setCurrentIndex(2)
    saved = dialog.save()
    frame.show_app_settings()

    assert saved == AppSettings(
        schema_version=1,
        default_open_directory=str(next_open_dir),
        default_output_directory=str(next_output_dir),
        linux_packaging_channel="unknown",
        ui={"appearance_mode": "dark"},
    )
    assert settings_store.load_settings() == saved
    assert frame.app_settings == saved
    assert not hasattr(frame.window, "app_settings")
    bindings.q_file_dialog.next_open_file_name = ""
    frame.choose_open_pdf()
    assert bindings.q_file_dialog.open_calls[-1][2] == str(next_open_dir)


def test_app_frame_settings_dialog_browse_buttons_choose_directories(
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

    frame.show_app_settings()
    dialog = frame.settings_dialog
    bindings.q_file_dialog.next_directory = str(tmp_path / "browse-open")
    dialog.controls.default_open_directory_browse_button.click()
    bindings.q_file_dialog.next_directory = str(tmp_path / "browse-output")
    dialog.controls.default_output_directory_browse_button.click()

    assert dialog.controls.default_open_directory.text() == str(tmp_path / "browse-open")
    assert dialog.controls.default_output_directory.text() == str(
        tmp_path / "browse-output"
    )
    assert bindings.q_file_dialog.directory_calls == [
        (
            dialog.controls.dialog,
            "Choose default open folder",
            str(tmp_path / "source"),
        ),
        (
            dialog.controls.dialog,
            "Choose default output folder",
            str(tmp_path / "signed"),
        ),
    ]


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


def test_qt_app_frame_module_no_longer_exposes_raw_window_helper() -> None:
    assert not hasattr(app_frame_module, "build_qt_app_frame")


def test_qt_app_frame_adapter_create_frame_returns_frame_host(
    monkeypatch,
    tmp_path: Path,
) -> None:
    bindings = _fake_bindings()
    monkeypatch.setattr(
        app_frame_module.QtAppFrameAdapter,
        "_load_bindings",
        lambda self: bindings,
    )

    frame = app_frame_module.QtAppFrameAdapter().create_frame(
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
    )

    assert isinstance(frame, FoliaSealAppFrame)
    assert isinstance(frame.container, _FakeMainWindow)
    assert frame.container is frame.window
    assert frame.window.title == "FoliaSeal"


def test_app_frame_restores_and_captures_main_window_geometry(tmp_path: Path) -> None:
    settings = AppSettings(
        schema_version=1,
        default_output_directory=str(tmp_path / "out"),
        default_open_directory=str(tmp_path / "in"),
        linux_packaging_channel="primary",
        ui={
            "appearance_mode": "system",
            "main_window_geometry": {
                "x": 40,
                "y": 50,
                "width": 1200,
                "height": 800,
                "maximized": True,
            },
        },
    )
    frame = FoliaSealAppFrame(
        bindings=_fake_bindings(),
        app_settings=settings,
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
    )

    assert frame.restore_window_geometry() is True
    assert frame.window.geometry_set_calls == [(40, 50, 1200, 800)]
    frame.window.show()
    frame.apply_restored_window_state()
    assert frame.window.maximize_calls == 1

    frame.window.geometry_value = _FakeRect(70, 80, 1300, 900)
    frame.window.maximized = False
    captured = frame.capture_window_geometry()

    assert captured.ui_settings.main_window_geometry is not None
    assert captured.ui_settings.main_window_geometry.to_mapping() == {
        "x": 70,
        "y": 80,
        "width": 1300,
        "height": 900,
        "maximized": False,
    }


def test_app_frame_capture_enforces_minimum_geometry(tmp_path: Path) -> None:
    frame = FoliaSealAppFrame(
        bindings=_fake_bindings(),
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
    )
    frame.window.geometry_value = _FakeRect(-20, -10, 400, 300)

    captured = frame.capture_window_geometry()

    assert captured.ui_settings.main_window_geometry.to_mapping() == {
        "x": -20,
        "y": -10,
        "width": 1100,
        "height": 700,
        "maximized": False,
    }


def test_app_frame_ignores_malformed_persisted_geometry(tmp_path: Path) -> None:
    settings = AppSettings(
        schema_version=1,
        default_output_directory=str(tmp_path / "out"),
        default_open_directory=str(tmp_path / "in"),
        linux_packaging_channel="primary",
        ui={
            "main_window_geometry": {
                "x": 10,
                "y": 20,
                "width": 400,
                "height": 300,
                "maximized": True,
            }
        },
    )
    frame = FoliaSealAppFrame(
        bindings=_fake_bindings(),
        app_settings=settings,
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
    )

    assert frame.restore_window_geometry() is False
    assert frame.window.geometry_set_calls == []
    frame.apply_restored_window_state()
    assert frame.window.maximize_calls == 0


def test_qt_app_frame_adapter_no_longer_exposes_raw_window_create() -> None:
    assert not hasattr(app_frame_module.QtAppFrameAdapter, "create")


def test_build_qt_app_frame_host_returns_frame_host(monkeypatch, tmp_path: Path) -> None:
    bindings = _fake_bindings()
    monkeypatch.setattr(
        app_frame_module.QtAppFrameAdapter,
        "_load_bindings",
        lambda self: bindings,
    )

    frame = app_frame_module.build_qt_app_frame_host(
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
    )

    assert isinstance(frame, FoliaSealAppFrame)
    assert isinstance(frame.window, _FakeMainWindow)
    assert frame.container is frame.window
    assert frame.window.title == "FoliaSeal"


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


def test_launch_qt_app_frame_restores_before_show_and_persists_after_exec(
    monkeypatch,
    tmp_path: Path,
) -> None:
    bindings = _fake_bindings()
    events = []
    _FakeQApplication.exec_result = 4

    class _FakeLaunchFrame:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs
            self.window = _FakeMainWindow()

        def restore_window_geometry(self) -> None:
            events.append("restore")

        def apply_restored_window_state(self) -> None:
            events.append("maximize")

        def capture_window_geometry(self) -> None:
            events.append("capture")

        def persist_captured_window_geometry(self) -> None:
            events.append("persist")

    original_show = _FakeMainWindow.show

    def show(self) -> None:
        events.append("show")
        original_show(self)

    monkeypatch.setattr(_FakeMainWindow, "show", show)
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

    assert exit_code == 4
    assert events == ["restore", "show", "maximize", "capture", "persist"]


def test_launch_qt_app_frame_forwards_secondary_request_without_creating_window(
    monkeypatch,
    tmp_path: Path,
) -> None:
    bindings = _fake_bindings()
    coordinator = _FakeInstanceCoordinator(primary=False)
    monkeypatch.setattr(
        app_frame_module.QtAppFrameAdapter,
        "_load_bindings",
        lambda self: bindings,
    )

    exit_code = app_frame_module.launch_qt_app_frame(
        argv=["foliaseal", "gui"],
        initial_pdf_path=tmp_path / "contract.pdf",
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        instance_coordinator=coordinator,
    )

    assert exit_code == 0
    assert coordinator.requests == [
        OpenRequest(pdf_path=str((tmp_path / "contract.pdf").resolve()))
    ]
    assert coordinator.close_calls == 1


def test_launch_qt_app_frame_delivers_queued_request_to_primary_frame(
    monkeypatch,
    tmp_path: Path,
) -> None:
    bindings = _fake_bindings()
    coordinator = _FakeInstanceCoordinator(
        primary=True,
        queued_request=OpenRequest(pdf_path=str((tmp_path / "queued.pdf").resolve())),
    )

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
        argv=["foliaseal", "gui"],
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        instance_coordinator=coordinator,
    )

    frame = _FakeLaunchFrame.instances[0]
    assert exit_code == 0
    assert frame.opened_paths == [str((tmp_path / "queued.pdf").resolve())]
    assert frame.window.raise_calls == 1
    assert frame.window.activate_calls == 1
    assert coordinator.close_calls == 1


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
