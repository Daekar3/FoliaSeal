from pathlib import Path

from foliaseal.infra.config.app_settings_storage import AppSettingsStore
from foliaseal.infra.config.schemas import AppSettings
from foliaseal.presentation.qt import app_frame as app_frame_module
from foliaseal.presentation.qt.app_frame import FoliaSealAppFrame, QtAppFrameBindings


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
    pass


def _fake_bindings() -> QtAppFrameBindings:
    file_dialog = _FakeFileDialog()
    message_box = _FakeMessageBox()
    _FakeQPdfDocument.next_status = _FakeQPdfDocument.Error.None_
    _FakeQPdfDocument.next_page_count = 3
    _FakeQPdfDocument.load_calls = []
    return QtAppFrameBindings(
        q_main_window=_FakeMainWindow,
        q_label=_FakeLabel,
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
    assert frame.window.menu_bar.menus[1].actions[0].text == "Application settings"

    frame.window.menu_bar.menus[1].actions[0].trigger()

    assert bindings.q_message_box.information_calls
    assert "Default open folder" in bindings.q_message_box.information_calls[0][2]


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
