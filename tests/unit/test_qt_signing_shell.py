from pathlib import Path

from PIL import Image

from foliaseal.application import (
    SigningDraftValidationIssue,
    SigningDraftValidationSeverity,
    SigningDraftWorkflow,
)
from foliaseal.application.coordinate_transform import PdfRect
from foliaseal.application.document_review import (
    DocumentReviewSummary,
    DocumentSignatureReviewItem,
)
from foliaseal.application.document_text_search import DocumentTextMatch
from foliaseal.application.document_text_selection import DocumentTextSelection
from foliaseal.application.viewer_session import ViewerSession
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.domain.errors import FailureCode
from foliaseal.domain.models import (
    SignatureBoxStyle,
    SignatureFieldKey,
    SignatureLayoutTemplate,
    SignaturePlacementDefaults,
    SignatureStampPosition,
    SignatureTextStyle,
    SigningResult,
)
from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
from foliaseal.infra.config.profile_storage import (
    PROFILE_DIRECTORY_NAME,
    SignaturePresetCatalogStore,
)
from foliaseal.infra.config.schemas import AppSettings, CertificateCatalog
from foliaseal.infra.render import PdfPageGeometry, RenderPageRequest, RenderPageResult
from foliaseal.presentation.qt import build_qt_signing_shell
from foliaseal.presentation.qt import signature_preview_lifecycle as preview_lifecycle_module
from foliaseal.presentation.qt import signing_shell as signing_shell_module
from foliaseal.presentation.qt.signing_shell import QtSigningWidgetBindings
from tests.support.phase3_builders import (
    build_certificate_catalog,
    build_certificate_configuration,
    build_managed_certificate,
    build_signature_appearance,
    build_signature_field_binding,
    build_signature_preset,
    build_signature_preset_catalog,
)


class _FakeSignal:
    def __init__(self) -> None:
        self._callbacks = []

    def connect(self, callback):
        self._callbacks.append(callback)

    def emit(self, *args):
        for callback in list(self._callbacks):
            callback(*args)


class _FakeWidget:
    def __init__(self, *args, **kwargs) -> None:
        self.enabled = True
        self.layout = None
        self.children = []
        self.parent = None
        self.style = None
        self.visible = True
        self.fixed_size = None
        self.fixed_width = None
        self.maximum_width = None
        self.minimum_width = None
        self._width_value = 480
        self.word_wrap = None
        self.destroyed = _FakeSignal()

    def setLayout(self, layout):  # noqa: N802
        self.layout = layout

    def setEnabled(self, value):  # noqa: N802
        self.enabled = value

    def setVisible(self, value):  # noqa: N802
        self.visible = bool(value)

    def setStyleSheet(self, style):  # noqa: N802
        self.style = style

    def setWordWrap(self, value):  # noqa: N802
        self.word_wrap = bool(value)

    def setFixedSize(self, width, height):  # noqa: N802
        self.fixed_size = (width, height)

    def setFixedWidth(self, width):  # noqa: N802
        self.fixed_width = width

    def setMaximumWidth(self, width):  # noqa: N802
        self.maximum_width = width

    def setMinimumWidth(self, width):  # noqa: N802
        self.minimum_width = width

    def width(self):
        if self.fixed_width is not None:
            return self.fixed_width
        if self.maximum_width is not None:
            return self.maximum_width
        return self._width_value

    def parentWidget(self):  # noqa: N802
        return self.parent

    def sizeHint(self):  # noqa: N802
        width = self.fixed_width
        if width is None:
            width = self.maximum_width
        if width is None and self.fixed_size is not None:
            width = self.fixed_size[0]
        if width is None:
            width = self._width_value

        height = self.fixed_size[1] if self.fixed_size is not None else 24

        class _Hint:
            def __init__(self, width_value, height_value) -> None:
                self._width = width_value
                self._height = height_value

            def width(self):
                return self._width

            def height(self):
                return self._height

        return _Hint(width, height)

    def close(self):
        close_event = getattr(self, "closeEvent", None)
        if callable(close_event):
            close_event(None)


class _FakeLayout:
    def __init__(self, parent=None) -> None:
        self.parent = parent
        self.rows = []
        self.items = []
        self.margins = None
        self.spacing = None
        if parent is not None and hasattr(parent, "setLayout"):
            parent.setLayout(self)

    def addWidget(self, widget, *args):  # noqa: N802
        if hasattr(widget, "parent"):
            widget.parent = self.parent
        self.items.append((widget, args))

    def addLayout(self, layout, *args):  # noqa: N802
        self.items.append((layout, args))

    def addRow(self, *args):  # noqa: N802
        for item in args:
            if hasattr(item, "parent"):
                item.parent = self.parent
        self.rows.append(args)

    def setContentsMargins(self, *args):  # noqa: N802
        self.margins = args

    def setSpacing(self, value):  # noqa: N802
        self.spacing = value


class _FakeLabel(_FakeWidget):
    def __init__(self, text="") -> None:
        super().__init__()
        self._text = text
        self._pixmap = None
        self.alignment = None
        self.fixed_size = None
        self.visible = True

    def setText(self, text):  # noqa: N802
        self._text = text

    def text(self):
        return self._text

    def setPixmap(self, pixmap):  # noqa: N802
        self._pixmap = pixmap

    def pixmap(self):
        return self._pixmap

    def setAlignment(self, alignment):  # noqa: N802
        self.alignment = alignment

    def setFixedSize(self, width, height):  # noqa: N802
        self.fixed_size = (width, height)

    def setVisible(self, value):  # noqa: N802
        self.visible = bool(value)

    def sizeHint(self):  # noqa: N802
        width = self.fixed_width
        if width is None:
            width = self.maximum_width
        if width is None and self.fixed_size is not None:
            width = self.fixed_size[0]
        if width is None:
            width = max(24, len(self._text) * 7)

        if self.fixed_size is not None:
            height = self.fixed_size[1]
        else:
            lines = max(1, len(self._text.splitlines()) if self._text else 1)
            height = 18 * lines

        class _Hint:
            def __init__(self, width_value, height_value) -> None:
                self._width = width_value
                self._height = height_value

            def width(self):
                return self._width

            def height(self):
                return self._height

        return _Hint(width, height)


class _FakeLineEdit(_FakeWidget):
    def __init__(self, text="") -> None:
        super().__init__()
        self._text = text
        self.textChanged = _FakeSignal()
        self.placeholder = ""

    def setText(self, text):  # noqa: N802
        self._text = text
        self.textChanged.emit(text)

    def text(self):
        return self._text

    def setPlaceholderText(self, text):  # noqa: N802
        self.placeholder = text


class _FakeCheckBox(_FakeWidget):
    def __init__(self, text="") -> None:
        super().__init__()
        self._text = text
        self._checked = False
        self.stateChanged = _FakeSignal()

    def setChecked(self, value):  # noqa: N802
        self._checked = bool(value)
        self.stateChanged.emit(int(self._checked))

    def isChecked(self):
        return self._checked


class _FakeComboBox(_FakeWidget):
    def __init__(self) -> None:
        super().__init__()
        self._items = []
        self._current = ""
        self.currentTextChanged = _FakeSignal()
        self.currentIndexChanged = _FakeSignal()

    def clear(self):  # noqa: N802
        self._items = []
        self._current = ""

    def addItems(self, items):  # noqa: N802
        self._items.extend(items)
        if not self._current and self._items:
            self._current = self._items[0]

    def addItem(self, item):  # noqa: N802
        self._items.append(item)
        if not self._current:
            self._current = item

    def setCurrentText(self, text):  # noqa: N802
        self._current = text
        self.currentTextChanged.emit(text)
        found = self.findText(text)
        if found >= 0:
            self.currentIndexChanged.emit(found)

    def currentText(self):
        return self._current

    def findText(self, text):  # noqa: N802
        try:
            return self._items.index(text)
        except ValueError:
            return -1

    def setCurrentIndex(self, index):  # noqa: N802
        self._current = self._items[index]
        self.currentTextChanged.emit(self._current)
        self.currentIndexChanged.emit(index)

    def count(self):  # noqa: N802
        return len(self._items)

    def itemText(self, index):  # noqa: N802
        return self._items[index]


class _FakeMessageBox:
    Yes = 1
    No = 0

    def __init__(self) -> None:
        self.calls = []
        self.next_result = self.Yes

    def question(self, parent, title, text):  # noqa: N802
        self.calls.append((parent, title, text))
        return self.next_result

    def warning(self, parent, title, text):  # noqa: N802
        self.calls.append((parent, title, text))
        return self.Yes


class _FakeFileDialog:
    def __init__(self) -> None:
        self.save_calls = []
        self.next_save_file_name = ""

    def getSaveFileName(self, parent, title, directory, file_filter):  # noqa: N802
        self.save_calls.append((parent, title, directory, file_filter))
        return (self.next_save_file_name, file_filter)


class _FakeSpinBox(_FakeWidget):
    def __init__(self) -> None:
        super().__init__()
        self._value = 0
        self.valueChanged = _FakeSignal()
        self.range = None

    def setRange(self, minimum, maximum):  # noqa: N802
        self.range = (minimum, maximum)

    def setDecimals(self, decimals):  # noqa: N802
        self.decimals = decimals

    def setSingleStep(self, step):  # noqa: N802
        self.step = step

    def setValue(self, value):  # noqa: N802
        self._value = value
        self.valueChanged.emit(value)

    def value(self):
        return self._value


class _FakeDoubleSpinBox(_FakeSpinBox):
    pass


class _FakePushButton(_FakeWidget):
    def __init__(self, text="") -> None:
        super().__init__()
        self._text = text
        self._enabled = True
        self.clicked = _FakeSignal()

    def setEnabled(self, value):  # noqa: N802
        self._enabled = bool(value)

    def click(self):
        self.clicked.emit()


class _FakePixmap:
    def __init__(self, path: str = "", width: int = 120, height: int = 80) -> None:
        self.path = path
        self.width = width
        self.height = height

    def isNull(self):  # noqa: N802
        return not self.path

    def scaled(self, width, height, *_args):  # noqa: N802
        if not self.path:
            return _FakePixmap("")
        aspect = self.width / self.height if self.height else 1.0
        if width / height > aspect:
            scaled_height = height
            scaled_width = max(1, int(height * aspect))
        else:
            scaled_width = width
            scaled_height = max(1, int(width / aspect))
        return _FakePixmap(self.path, scaled_width, scaled_height)


class _FakeScrollArea(_FakeWidget):
    def __init__(self) -> None:
        super().__init__()
        self.widget = None
        self.widget_resizable = False

    def setWidgetResizable(self, value):  # noqa: N802
        self.widget_resizable = bool(value)

    def setWidget(self, widget):  # noqa: N802
        self.widget = widget
        if hasattr(widget, "parent"):
            widget.parent = self


class _FakeQt:
    AlignLeft = 1
    AlignRight = 2
    AlignCenter = 4
    AlignTop = 8
    AlignBottom = 16
    KeepAspectRatio = 1
    SmoothTransformation = 2


class _FakeRenderBackend:
    def render_page(self, request: RenderPageRequest) -> RenderPageResult:
        return RenderPageResult(
            width_px=200,
            height_px=100,
            rgba_bytes=b"\x00" * (200 * 100 * 4),
        )

    def get_page_geometry(self, document_path: str, page_index: int) -> PdfPageGeometry:
        return PdfPageGeometry(
            media_box=(0.0, 0.0, 100.0, 50.0),
            crop_box=(0.0, 0.0, 100.0, 50.0),
            rotation=0,
        )

    def diagnostics(self):  # pragma: no cover - not needed here
        raise NotImplementedError


class _FakeViewerWidget(_FakeWidget):
    def __init__(self, workflow, on_selection=None, on_error=None, on_interaction=None) -> None:
        super().__init__()
        self.workflow = workflow
        self.on_selection = on_selection
        self.on_error = on_error
        self.on_interaction = on_interaction
        self.refresh_calls = []
        self.overlay_signature_rect = None
        self.text_highlight_page_index = None
        self.text_highlight_rects = ()
        self.interaction_mode = "signature"

    def refresh(self, *, elapsed_ms=None, navigation=False):
        self.refresh_calls.append((elapsed_ms, navigation))
        return self.workflow.render_current_page(elapsed_ms=elapsed_ms, navigation=navigation)

    def emit_selection(self, pdf_rect):
        if self.on_selection is not None:
            self.on_selection(pdf_rect)

    def set_signature_overlay(self, signature_rect):
        self.overlay_signature_rect = signature_rect

    def clear_signature_overlay(self):
        self.overlay_signature_rect = None

    def set_text_highlight_overlay(self, *, page_index, highlight_rects):
        self.text_highlight_page_index = page_index
        self.text_highlight_rects = tuple(highlight_rects)

    def clear_text_highlight_overlay(self):
        self.text_highlight_page_index = None
        self.text_highlight_rects = ()

    def set_interaction_mode(self, mode):
        self.interaction_mode = mode


class _FakeSigningExecutor:
    def __init__(self, result: SigningResult) -> None:
        self.result = result
        self.calls = []

    def execute(self, request):
        self.calls.append(request)
        return self.result


class _FakeDocumentReviewInspector:
    def __init__(self, summary: DocumentReviewSummary) -> None:
        self.summary = summary
        self.calls = []

    def inspect(self, input_pdf_path: str) -> DocumentReviewSummary:
        self.calls.append(input_pdf_path)
        return self.summary


class _FakeDocumentTextSearchEngine:
    def __init__(
        self,
        matches_by_query: dict[str, tuple[DocumentTextMatch, ...]] | None = None,
    ) -> None:
        self.matches_by_query = matches_by_query or {}
        self.calls = []

    def search(self, input_pdf_path: str, query: str) -> tuple[DocumentTextMatch, ...]:
        self.calls.append((input_pdf_path, query))
        return self.matches_by_query.get(query, ())


class _FakeDocumentTextSelectionEngine:
    def __init__(
        self,
        *,
        selection: DocumentTextSelection | None = None,
    ) -> None:
        self.selection = selection
        self.calls = []

    def select(self, input_pdf_path: str, *, page_index: int, selection_rect: PdfRect):
        self.calls.append((input_pdf_path, page_index, selection_rect))
        return self.selection


class _FakeClipboard:
    def __init__(self) -> None:
        self.values = []

    def setText(self, value):  # noqa: N802
        self.values.append(value)


def _fake_bindings() -> QtSigningWidgetBindings:
    return QtSigningWidgetBindings(
        q_widget=_FakeWidget,
        q_vbox_layout=_FakeLayout,
        q_hbox_layout=_FakeLayout,
        q_form_layout=_FakeLayout,
        q_scroll_area=_FakeScrollArea,
        q_group_box=_FakeWidget,
        q_label=_FakeLabel,
        q_line_edit=_FakeLineEdit,
        q_check_box=_FakeCheckBox,
        q_combo_box=_FakeComboBox,
        q_file_dialog=_FakeFileDialog(),
        q_message_box=_FakeMessageBox(),
        q_double_spin_box=_FakeDoubleSpinBox,
        q_spin_box=_FakeSpinBox,
        q_push_button=_FakePushButton,
        q_pixmap=_FakePixmap,
        qt=_FakeQt,
    )


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


def _viewer_workflow() -> ViewerWorkflow:
    return ViewerWorkflow(
        document_path="/tmp/sample.pdf",
        render_backend=_FakeRenderBackend(),
        session=ViewerSession(page_count=3),
    )


def test_signing_shell_output_dialog_uses_app_settings_default_directory(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    bindings = _fake_bindings()
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: bindings,
    )
    default_output_dir = tmp_path / "chosen-default"
    selected_path = default_output_dir / "signed.pdf"
    bindings.q_file_dialog.next_save_file_name = str(selected_path)
    workflow = _workflow(tmp_path)

    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=workflow,
        app_settings=AppSettings(
            schema_version=1,
            default_output_directory=str(default_output_dir),
            default_open_directory=str(tmp_path / "open"),
            linux_packaging_channel="unknown",
            ui={},
        ),
    )

    result = widget.choose_output_pdf_path()

    assert result == str(selected_path)
    assert workflow.output_pdf_path == str(selected_path)
    assert bindings.q_file_dialog.save_calls == [
        (
            widget,
            "Save signed PDF",
            str(default_output_dir / "output.pdf"),
            "PDF files (*.pdf)",
        )
    ]
    assert bindings.q_message_box.calls == []
    assert not hasattr(widget.properties_panel, "_app_settings_controls")


def test_signing_shell_output_path_overwrite_cancel_keeps_existing_state(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    bindings = _fake_bindings()
    bindings.q_message_box.next_result = bindings.q_message_box.No
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: bindings,
    )
    workflow = _workflow(tmp_path)
    existing_output_path = tmp_path / "already-signed.pdf"
    existing_output_path.write_bytes(b"existing signed pdf")
    bindings.q_file_dialog.next_save_file_name = str(existing_output_path)
    executor = _FakeSigningExecutor(
        SigningResult(
            success=True,
            failure_code=None,
            message="Signing completed successfully.",
            timestamp_present=False,
        )
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=workflow,
        sign_executor=executor,
    )
    widget.viewer_widget.emit_selection(PdfRect(x1=10.0, y1=10.0, x2=30.0, y2=20.0))
    widget.submit_sign_request()
    original_output_path = workflow.output_pdf_path
    original_result_label = widget.sign_result_label.text()

    result = widget.choose_output_pdf_path()

    assert result is None
    assert workflow.output_pdf_path == original_output_path
    assert widget.last_signing_result is not None
    assert widget.last_signing_result is not None
    assert widget.sign_result_label.text() == original_result_label
    assert bindings.q_message_box.calls == [
        (
            widget,
            "Overwrite signed PDF?",
            f"Replace existing signed PDF at {existing_output_path}?",
        )
    ]


def test_signing_shell_output_path_overwrite_cancel_prompts_for_current_path(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    bindings = _fake_bindings()
    bindings.q_message_box.next_result = bindings.q_message_box.No
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: bindings,
    )
    workflow = _workflow(tmp_path)
    current_output_path = Path(workflow.output_pdf_path)
    current_output_path.write_bytes(b"existing signed pdf")
    bindings.q_file_dialog.next_save_file_name = str(current_output_path)
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=workflow,
    )

    result = widget.choose_output_pdf_path()

    assert result is None
    assert workflow.output_pdf_path == str(current_output_path)
    assert bindings.q_message_box.calls == [
        (
            widget,
            "Overwrite signed PDF?",
            f"Replace existing signed PDF at {current_output_path}?",
        )
    ]


def test_signing_shell_output_path_overwrite_confirm_updates_and_clears_result(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    bindings = _fake_bindings()
    bindings.q_message_box.next_result = bindings.q_message_box.Yes
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: bindings,
    )
    workflow = _workflow(tmp_path)
    existing_output_path = tmp_path / "already-signed.pdf"
    existing_output_path.write_bytes(b"existing signed pdf")
    bindings.q_file_dialog.next_save_file_name = str(existing_output_path)
    executor = _FakeSigningExecutor(
        SigningResult(
            success=True,
            failure_code=None,
            message="Signing completed successfully.",
            timestamp_present=False,
        )
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=workflow,
        sign_executor=executor,
    )
    widget.viewer_widget.emit_selection(PdfRect(x1=10.0, y1=10.0, x2=30.0, y2=20.0))
    widget.submit_sign_request()

    result = widget.choose_output_pdf_path()

    assert result == str(existing_output_path)
    assert workflow.output_pdf_path == str(existing_output_path)
    assert widget.last_signing_result is None
    assert widget.last_signing_result is None
    assert widget.sign_result_label.text() == (f"Output will be saved to: {existing_output_path}")
    assert bindings.q_message_box.calls == [
        (
            widget,
            "Overwrite signed PDF?",
            f"Replace existing signed PDF at {existing_output_path}?",
        )
    ]


def test_signing_shell_selection_updates_request(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    requests = []
    errors = []
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
        on_sign_request=requests.append,
        on_error=errors.append,
    )

    assert widget.properties_panel.preview.can_submit is False

    widget.viewer_widget.emit_selection(PdfRect(x1=10.0, y1=10.0, x2=30.0, y2=20.0))
    request = widget.submit_sign_request()

    assert errors == []
    assert request is not None


def test_signing_shell_applies_selected_certificate_configuration(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    catalog = build_certificate_catalog()
    store.save_catalog(catalog)
    managed_cert = catalog.managed_certificates[0]
    cert_file = store.managed_certificate_dir / managed_cert.storage_filename
    cert_file.write_bytes(b"pkcs12-bytes")
    workflow = _workflow(tmp_path)
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=workflow,
        certificate_catalog_store=store,
    )

    panel = widget.properties_panel
    panel._certificate_controls.configuration_combo.setCurrentText("Corporate Records Signing")
    panel._certificate_controls.password_input.setText("typed-secret")

    assert panel.apply_selected_certificate_configuration() is True

    assert workflow.selected_certificate_configuration_id == "cert-config-default"
    assert workflow.certificate_path == str(cert_file)
    assert workflow.passphrase == "typed-secret"


def test_signing_shell_reports_certificate_configuration_resolution_errors(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    bindings = _fake_bindings()
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: bindings,
    )
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    store.save_catalog(build_certificate_catalog())
    errors: list[str] = []
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
        certificate_catalog_store=store,
        on_error=errors.append,
    )

    panel = widget.properties_panel
    panel._certificate_controls.configuration_combo.setCurrentText("Corporate Records Signing")

    assert panel.apply_selected_certificate_configuration() is False
    assert errors
    assert "managed certificate file is missing" in errors[-1]
    assert bindings.q_message_box.calls[-1][1] == "Certificate configuration error"


def test_signing_shell_refreshes_certificate_configurations_from_store(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    store.save_catalog(CertificateCatalog(schema_version=1))
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
        certificate_catalog_store=store,
    )

    panel = widget.properties_panel
    assert (
        panel._certificate_controls.configuration_combo.findText("Corporate Records Signing") == -1
    )

    store.save_catalog(build_certificate_catalog())
    catalog = widget.refresh_certificate_configurations()

    assert catalog.configuration_named("Corporate Records Signing")
    assert (
        panel._certificate_controls.configuration_combo.findText("Corporate Records Signing") >= 0
    )


def test_signing_shell_selection_uses_rendered_snapshot_page_for_validation(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )

    widget.set_logical_page_index(2)
    widget.viewer_widget.emit_selection(PdfRect(x1=10.0, y1=10.0, x2=30.0, y2=20.0))

    preview = widget.properties_panel.preview

    assert preview.signature_rect is not None
    assert preview.signature_rect.page_index == 0
    assert widget.properties_panel.validation_text() != (
        "ERROR signature_rect_page_mismatch: "
        "Signature rectangle page does not match the active placement page."
    )
    assert widget.viewer_widget.overlay_signature_rect is not None
    assert widget.viewer_widget.overlay_signature_rect.page_index == 0


def test_signing_shell_executes_real_sign_flow_when_executor_is_supplied(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    executor = _FakeSigningExecutor(
        SigningResult(
            success=True,
            failure_code=None,
            message="Signing completed successfully.",
            output_pdf_version="1.7",
            signature_subfilter="adbe.pkcs7.detached",
            timestamp_present=False,
            standards_summary="PDF 1.7, detached signature, no timestamp.",
        )
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
        sign_executor=executor,
    )

    widget.viewer_widget.emit_selection(PdfRect(x1=10.0, y1=10.0, x2=30.0, y2=20.0))
    request = widget.submit_sign_request()

    assert request is not None
    assert executor.calls == [request]
    assert widget.last_signing_result is not None
    assert widget.last_signing_result.success is True
    assert "Signing completed successfully." in widget.sign_result_label.text()
    assert f"Saved to: {request.output_pdf_path}" in widget.sign_result_label.text()
    assert (
        "Verified locally: PDF 1.7, detached signature, no timestamp."
        in widget.sign_result_label.text()
    )
    assert "No timestamp token was found." in widget.sign_result_label.text()
    assert widget.flow_stage_label.text() == "Signed"
    assert "Open or verify the signed PDF" in widget.flow_detail_label.text()
    assert widget.open_signed_output_button._enabled is False


def test_signing_shell_shows_document_review_summary_from_injected_inspector(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )
    inspector = _FakeDocumentReviewInspector(
        DocumentReviewSummary(
            headline="Signature review",
            detail=(
                "Found 1 embedded signature. Latest signer: CN=Alice Example. "
                "Latest signature verified locally."
            ),
            signature_count=1,
            signer_subject="CN=Alice Example",
            cryptographic_validation_passed=True,
        )
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
        document_review_inspector=inspector,
    )

    assert inspector.calls == ["/tmp/sample.pdf"]
    assert widget.document_review_headline_label.text() == "Signature review"
    assert "Found 1 embedded signature." in widget.document_review_detail_label.text()
    assert "Latest signer: CN=Alice Example." in widget.document_review_detail_label.text()


def test_signing_shell_renders_per_signature_review_items(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )
    inspector = _FakeDocumentReviewInspector(
        DocumentReviewSummary(
            headline="Signature review",
            detail=(
                "Found 2 embedded signatures. Latest signer: CN=Alice Example. "
                "Latest signature needs attention: local verification failed."
            ),
            signature_count=2,
            signature_items=(
                DocumentSignatureReviewItem(
                    label="Signature 1",
                    signer_subject="CN=Bob Example",
                    cryptographic_validation_passed=True,
                    detail="CN=Bob Example: verified locally.",
                    drill_in_detail=(
                        "Signer: CN=Bob Example.\n"
                        "Local verification: verified locally.\n"
                        "Document permissions: Certification permits form filling "
                        "and additional signing changes."
                    ),
                ),
                DocumentSignatureReviewItem(
                    label="Signature 2 (latest)",
                    signer_subject="CN=Alice Example",
                    cryptographic_validation_passed=False,
                    detail="CN=Alice Example: needs local verification attention.",
                    drill_in_detail=(
                        "Signer: CN=Alice Example.\n"
                        "Local verification: needs local verification attention.\n"
                        "Document permissions: Certification permits form filling "
                        "and additional signing changes.\n"
                        "Recommended next step: reopen the signed PDF and review "
                        "the selected signature details carefully before relying on it."
                    ),
                ),
            ),
            signer_subject="CN=Alice Example",
            cryptographic_validation_passed=False,
        )
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
        document_review_inspector=inspector,
    )

    rendered = widget.document_review_signature_items_label.text()
    assert "Signature 1: CN=Bob Example: verified locally." in rendered
    assert (
        "Signature 2 (latest): "
        "CN=Alice Example: needs local verification attention."
    ) in rendered


def test_signing_shell_updates_drill_in_detail_for_selected_signature(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )
    inspector = _FakeDocumentReviewInspector(
        DocumentReviewSummary(
            headline="Signature review",
            detail=(
                "Found 2 embedded signatures. Latest signer: CN=Alice Example. "
                "Latest signature needs attention: local verification failed."
            ),
            signature_count=2,
            signature_items=(
                DocumentSignatureReviewItem(
                    label="Signature 1",
                    signer_subject="CN=Bob Example",
                    cryptographic_validation_passed=True,
                    detail="CN=Bob Example: verified locally.",
                    drill_in_detail=(
                        "Signer: CN=Bob Example.\n"
                        "Local verification: verified locally.\n"
                        "Document permissions: Certification permits form filling "
                        "and additional signing changes."
                    ),
                ),
                DocumentSignatureReviewItem(
                    label="Signature 2 (latest)",
                    signer_subject="CN=Alice Example",
                    cryptographic_validation_passed=False,
                    detail="CN=Alice Example: needs local verification attention.",
                    drill_in_detail=(
                        "Signer: CN=Alice Example.\n"
                        "Local verification: needs local verification attention.\n"
                        "Document permissions: Certification permits form filling "
                        "and additional signing changes.\n"
                        "Recommended next step: reopen the signed PDF and review "
                        "the selected signature details carefully before relying on it."
                    ),
                ),
            ),
            signer_subject="CN=Alice Example",
            cryptographic_validation_passed=False,
        )
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
        document_review_inspector=inspector,
    )

    assert widget.document_review_signature_selector.count() == 2
    assert widget.document_review_signature_selector.currentText() == "Signature 2 (latest)"
    assert "Signer: CN=Alice Example." in widget.document_review_signature_detail_label.text()
    assert (
        "Recommended next step: reopen the signed PDF and review "
        "the selected signature details carefully before relying on it."
        in widget.document_review_signature_detail_label.text()
    )

    widget.document_review_signature_selector.setCurrentIndex(0)

    assert widget.document_review_signature_selector.currentText() == "Signature 1"
    assert "Signer: CN=Bob Example." in widget.document_review_signature_detail_label.text()
    assert (
        "Local verification: verified locally."
        in widget.document_review_signature_detail_label.text()
    )


def test_signing_shell_disables_review_selector_for_single_signature_detail(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )
    inspector = _FakeDocumentReviewInspector(
        DocumentReviewSummary(
            headline="Signature review",
            detail=(
                "Found 1 embedded signature. Latest signer: CN=Alice Example. "
                "Latest signature verified locally."
            ),
            signature_count=1,
            signature_items=(
                DocumentSignatureReviewItem(
                    label="Signature 1 (latest)",
                    signer_subject="CN=Alice Example",
                    cryptographic_validation_passed=True,
                    detail="CN=Alice Example: verified locally.",
                    drill_in_detail=(
                        "Signer: CN=Alice Example.\n"
                        "Local verification: verified locally.\n"
                        "Document permissions: No certification restriction was detected."
                    ),
                ),
            ),
            signer_subject="CN=Alice Example",
            cryptographic_validation_passed=True,
        )
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
        document_review_inspector=inspector,
    )

    assert widget.document_review_signature_selector.count() == 1
    assert widget.document_review_signature_selector.enabled is False
    assert "Signer: CN=Alice Example." in widget.document_review_signature_detail_label.text()


def test_signing_shell_renders_next_action_guidance_for_not_evaluated_signature(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )
    inspector = _FakeDocumentReviewInspector(
        DocumentReviewSummary(
            headline="Signature review",
            detail=(
                "Found 1 embedded signature. "
                "Latest signature validity was not evaluated locally."
            ),
            signature_count=1,
            signature_items=(
                DocumentSignatureReviewItem(
                    label="Signature 1 (latest)",
                    signer_subject=None,
                    cryptographic_validation_passed=None,
                    detail="Signer not available: local verification not evaluated.",
                    drill_in_detail=(
                        "Signer: Signer not available.\n"
                        "Local verification: local verification not evaluated.\n"
                        "Document permissions: No certification restriction was detected.\n"
                        "Recommended next step: reopen the signed PDF and review the embedded "
                        "signer details before relying on this signature."
                    ),
                ),
            ),
            signer_subject=None,
            cryptographic_validation_passed=None,
        )
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
        document_review_inspector=inspector,
    )

    assert (
        "Recommended next step: reopen the signed PDF and review the embedded "
        "signer details before relying on this signature."
        in widget.document_review_signature_detail_label.text()
    )


def test_signing_shell_renders_restricted_next_action_guidance(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )
    inspector = _FakeDocumentReviewInspector(
        DocumentReviewSummary(
            headline="Signature review: restricted",
            detail=(
                "Found 1 embedded signature. Latest signer: CN=Alice Example. "
                "Latest signature needs attention: local verification failed."
            ),
            signature_count=1,
            signature_items=(
                DocumentSignatureReviewItem(
                    label="Signature 1 (latest)",
                    signer_subject="CN=Alice Example",
                    cryptographic_validation_passed=False,
                    detail="CN=Alice Example: needs local verification attention.",
                    drill_in_detail=(
                        "Signer: CN=Alice Example.\n"
                        "Local verification: needs local verification attention.\n"
                        "Document restrictions: Certification-restricted PDF: DocMDP "
                        "NO_CHANGES forbids signing.\n"
                        "Recommended next step: reopen the signed PDF, review the "
                        "selected signature details carefully, and expect that further "
                        "changes may be blocked."
                    ),
                ),
            ),
            signer_subject="CN=Alice Example",
            cryptographic_validation_passed=False,
            certification_restricted=True,
            restriction_reason="Certification-restricted PDF: DocMDP NO_CHANGES forbids signing.",
        )
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
        document_review_inspector=inspector,
    )

    assert (
        "Recommended next step: reopen the signed PDF, review the selected signature "
        "details carefully, and expect that further changes may be blocked."
        in widget.document_review_signature_detail_label.text()
    )


def test_signing_shell_preserves_selected_signature_on_review_refresh(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )
    inspector = _FakeDocumentReviewInspector(
        DocumentReviewSummary(
            headline="Signature review",
            detail="Found 2 embedded signatures.",
            signature_count=2,
            signature_items=(
                DocumentSignatureReviewItem(
                    label="Signature 1",
                    signer_subject="CN=Bob Example",
                    cryptographic_validation_passed=True,
                    detail="CN=Bob Example: verified locally.",
                    drill_in_detail=(
                        "Signer: CN=Bob Example.\n"
                        "Local verification: verified locally."
                    ),
                ),
                DocumentSignatureReviewItem(
                    label="Signature 2 (latest)",
                    signer_subject="CN=Alice Example",
                    cryptographic_validation_passed=False,
                    detail="CN=Alice Example: needs local verification attention.",
                    drill_in_detail=(
                        "Signer: CN=Alice Example.\n"
                        "Local verification: needs local verification attention."
                    ),
                ),
            ),
            signer_subject="CN=Alice Example",
            cryptographic_validation_passed=False,
        )
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
        document_review_inspector=inspector,
    )

    widget.document_review_signature_selector.setCurrentIndex(0)
    inspector.summary = DocumentReviewSummary(
        headline="Signature review",
        detail="Found 2 embedded signatures.",
        signature_count=2,
        signature_items=(
            DocumentSignatureReviewItem(
                label="Signature 1",
                signer_subject="CN=Bob Example",
                cryptographic_validation_passed=True,
                detail="CN=Bob Example: verified locally.",
                drill_in_detail=(
                    "Signer: CN=Bob Example.\n"
                    "Local verification: verified locally.\n"
                    "Document permissions: No certification restriction was detected."
                ),
            ),
            DocumentSignatureReviewItem(
                label="Signature 2 (latest)",
                signer_subject="CN=Alice Example",
                cryptographic_validation_passed=False,
                detail="CN=Alice Example: needs local verification attention.",
                drill_in_detail=(
                    "Signer: CN=Alice Example.\n"
                    "Local verification: needs local verification attention."
                ),
            ),
        ),
        signer_subject="CN=Alice Example",
        cryptographic_validation_passed=False,
    )

    widget.refresh_document_review()

    assert widget.document_review_signature_selector.currentText() == "Signature 1"
    assert (
        "Document permissions: No certification restriction was detected."
        in widget.document_review_signature_detail_label.text()
    )


def test_signing_shell_document_text_search_jumps_pages_and_copies_current_hit(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )
    search_engine = _FakeDocumentTextSearchEngine(
        {
            "Alice": (
                DocumentTextMatch(
                    page_index=1,
                    start_index=5,
                    end_index=10,
                    text="Alice",
                    context="Signed by Alice Example on page two",
                ),
                DocumentTextMatch(
                    page_index=2,
                    start_index=0,
                    end_index=5,
                    text="Alice",
                    context="Alice appears again on page three",
                ),
            ),
        }
    )
    copied_text = []
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
        document_text_search_engine=search_engine,
        on_copy_text=copied_text.append,
    )
    initial_refresh_count = len(widget.viewer_widget.refresh_calls)

    widget.document_text_query_input.setText("Alice")
    widget.document_text_find_button.click()

    assert search_engine.calls == [("/tmp/sample.pdf", "Alice")]
    assert widget.logical_page_index() == 1
    assert len(widget.viewer_widget.refresh_calls) == initial_refresh_count + 1
    assert widget.viewer_widget.refresh_calls[-1] == (None, True)
    assert widget.document_text_status_label.text() == "Found 2 matches for 'Alice'."
    assert "Showing 1 of 2 on page 2" in widget.document_text_detail_label.text()

    widget.document_text_next_button.click()

    assert widget.logical_page_index() == 2
    assert "Showing 2 of 2 on page 3" in widget.document_text_detail_label.text()

    widget.document_text_copy_button.click()

    assert copied_text == ["Alice"]


def test_signing_shell_document_text_search_uses_default_qt_clipboard_callback(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )
    clipboard = _FakeClipboard()

    class _FakeQGuiApplication:
        @staticmethod
        def clipboard():
            return clipboard

    class _FakeQtGuiModule:
        QGuiApplication = _FakeQGuiApplication

    real_import_module = signing_shell_module.importlib.import_module

    def _fake_import_module(name: str):
        if name == "PySide6.QtGui":
            return _FakeQtGuiModule
        return real_import_module(name)

    monkeypatch.setattr(signing_shell_module.importlib, "import_module", _fake_import_module)
    search_engine = _FakeDocumentTextSearchEngine(
        {
            "Alice": (
                DocumentTextMatch(
                    page_index=0,
                    start_index=0,
                    end_index=5,
                    text="Alice",
                    context="Alice Example",
                ),
            ),
        }
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
        document_text_search_engine=search_engine,
    )

    widget.document_text_query_input.setText("Alice")
    widget.document_text_find_button.click()
    widget.document_text_copy_button.click()

    assert clipboard.values == ["Alice"]


def test_signing_shell_document_text_selection_mode_copies_and_clears_selection(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )
    selection_engine = _FakeDocumentTextSelectionEngine(
        selection=DocumentTextSelection(
            page_index=0,
            text="Alice Example",
            highlight_rects=(PdfRect(x1=10.0, y1=10.0, x2=30.0, y2=16.0),),
        )
    )
    copied_text = []
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
        document_text_selection_engine=selection_engine,
        on_copy_text=copied_text.append,
    )

    widget.document_text_select_mode_checkbox.setChecked(True)

    assert widget.viewer_widget.interaction_mode == "text"

    widget.viewer_widget.emit_selection(PdfRect(x1=10.0, y1=10.0, x2=30.0, y2=16.0))

    assert selection_engine.calls == [
        ("/tmp/sample.pdf", 0, PdfRect(x1=10.0, y1=10.0, x2=30.0, y2=16.0))
    ]
    assert widget.document_text_status_label.text() == "Selected text on page 1."
    assert widget.document_text_detail_label.text() == "Alice Example"
    assert widget.viewer_widget.text_highlight_page_index == 0
    assert widget.viewer_widget.text_highlight_rects == (
        PdfRect(x1=10.0, y1=10.0, x2=30.0, y2=16.0),
    )

    widget.document_text_copy_selection_button.click()

    assert copied_text == ["Alice Example"]

    widget.document_text_clear_selection_button.click()

    assert widget.viewer_widget.text_highlight_page_index is None
    assert widget.viewer_widget.text_highlight_rects == ()
    assert widget.document_text_copy_selection_button._enabled is False

    widget.document_text_select_mode_checkbox.setChecked(False)
    widget.viewer_widget.emit_selection(PdfRect(x1=1.0, y1=2.0, x2=3.0, y2=4.0))

    assert widget.viewer_widget.interaction_mode == "signature"
    assert widget.signature_rect() is not None
    assert widget.signature_rect().left_pt == 1.0


def test_signing_shell_restores_search_state_when_text_selection_mode_is_disabled(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )
    search_engine = _FakeDocumentTextSearchEngine(
        {
            "Alice": (
                DocumentTextMatch(
                    page_index=1,
                    start_index=5,
                    end_index=10,
                    text="Alice",
                    context="Signed by Alice Example on page two",
                ),
            ),
        }
    )
    selection_engine = _FakeDocumentTextSelectionEngine(
        selection=DocumentTextSelection(
            page_index=1,
            text="Alice Example",
            highlight_rects=(PdfRect(x1=10.0, y1=10.0, x2=30.0, y2=16.0),),
        )
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
        document_text_search_engine=search_engine,
        document_text_selection_engine=selection_engine,
    )

    widget.document_text_query_input.setText("Alice")
    widget.document_text_find_button.click()
    widget.document_text_select_mode_checkbox.setChecked(True)
    widget.viewer_widget.emit_selection(PdfRect(x1=10.0, y1=10.0, x2=30.0, y2=16.0))

    assert widget.document_text_status_label.text() == "Selected text on page 2."

    widget.document_text_select_mode_checkbox.setChecked(False)

    assert widget.document_text_status_label.text() == "Found 1 matches for 'Alice'."
    assert "Showing 1 of 1 on page 2" in widget.document_text_detail_label.text()
    assert widget.viewer_widget.text_highlight_rects == ()


def test_signing_shell_flow_summary_returns_to_confirm_after_signed_draft_changes(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )
    executor = _FakeSigningExecutor(
        SigningResult(
            success=True,
            failure_code=None,
            message="Signing completed successfully.",
            timestamp_present=False,
        )
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
        sign_executor=executor,
    )
    widget.viewer_widget.emit_selection(PdfRect(x1=10.0, y1=10.0, x2=30.0, y2=20.0))
    widget.submit_sign_request()

    widget.viewer_widget.emit_selection(PdfRect(x1=12.0, y1=12.0, x2=34.0, y2=24.0))

    assert widget.flow_stage_label.text() == "Confirm/sign"
    assert widget.last_signing_result is None
    assert widget.last_signing_result is None
    assert widget.sign_result_label.text() == ""


def test_signing_shell_flow_summary_replaces_signed_result_after_output_path_change(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    bindings = _fake_bindings()
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: bindings,
    )
    executor = _FakeSigningExecutor(
        SigningResult(
            success=True,
            failure_code=None,
            message="Signing completed successfully.",
            timestamp_present=False,
        )
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
        sign_executor=executor,
    )
    widget.viewer_widget.emit_selection(PdfRect(x1=10.0, y1=10.0, x2=30.0, y2=20.0))
    widget.submit_sign_request()

    selected_path = tmp_path / "changed-output.pdf"
    bindings.q_file_dialog.next_save_file_name = str(selected_path)
    widget.choose_output_pdf_path()

    assert widget.flow_stage_label.text() == "Confirm/sign"
    assert widget.last_signing_result is None
    assert widget.last_signing_result is None
    assert "Signing completed successfully." not in widget.sign_result_label.text()
    assert widget.sign_result_label.text() == f"Output will be saved to: {selected_path}"


def test_signing_shell_flow_summary_clears_signed_result_after_page_change(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )
    executor = _FakeSigningExecutor(
        SigningResult(
            success=True,
            failure_code=None,
            message="Signing completed successfully.",
            timestamp_present=False,
        )
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
        sign_executor=executor,
    )
    widget.viewer_widget.emit_selection(PdfRect(x1=10.0, y1=10.0, x2=30.0, y2=20.0))
    widget.submit_sign_request()

    widget.properties_panel._placement_controls.page_spin.setValue(2)

    assert widget.flow_stage_label.text() == "Confirm/sign"
    assert widget.last_signing_result is None
    assert widget.last_signing_result is None
    assert widget.sign_result_label.text() == ""


def test_signing_shell_open_signed_output_uses_success_callback(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    opened_paths = []
    executor = _FakeSigningExecutor(
        SigningResult(
            success=True,
            failure_code=None,
            message="Signing completed successfully.",
            timestamp_present=False,
        )
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
        sign_executor=executor,
        on_open_signed_output=opened_paths.append,
    )

    widget.viewer_widget.emit_selection(PdfRect(x1=10.0, y1=10.0, x2=30.0, y2=20.0))
    request = widget.submit_sign_request()
    opened = widget.open_signed_output()

    assert request is not None
    assert opened == request.output_pdf_path
    assert opened_paths == [request.output_pdf_path]
    assert widget.open_signed_output_button._enabled is True
    assert widget.document_review_verify_button._enabled is True


def test_signing_shell_review_verify_button_reuses_open_signed_output_path(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    opened_paths = []
    executor = _FakeSigningExecutor(
        SigningResult(
            success=True,
            failure_code=None,
            message="Signing completed successfully.",
            timestamp_present=False,
        )
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
        sign_executor=executor,
        on_open_signed_output=opened_paths.append,
    )

    widget.viewer_widget.emit_selection(PdfRect(x1=10.0, y1=10.0, x2=30.0, y2=20.0))
    request = widget.submit_sign_request()
    widget.document_review_verify_button.click()

    assert request is not None
    assert opened_paths == [request.output_pdf_path]


def test_signing_shell_disables_open_signed_output_after_sign_failure(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    opened_paths = []
    executor = _FakeSigningExecutor(
        SigningResult(
            success=False,
            failure_code=FailureCode.POST_VERIFY_FAILED,
            message="Post-sign verification failed.",
        )
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
        sign_executor=executor,
        on_open_signed_output=opened_paths.append,
        on_error=lambda _message: None,
    )

    widget.viewer_widget.emit_selection(PdfRect(x1=10.0, y1=10.0, x2=30.0, y2=20.0))
    request = widget.submit_sign_request()
    opened = widget.open_signed_output()

    assert request is not None
    assert opened is None
    assert opened_paths == []
    assert widget.open_signed_output_button._enabled is False


def test_signing_shell_reports_sign_failure_when_executor_returns_failure(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    errors = []
    executor = _FakeSigningExecutor(
        SigningResult(
            success=False,
            failure_code=FailureCode.POST_VERIFY_FAILED,
            message="Post-sign verification failed.",
        )
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
        sign_executor=executor,
        on_error=errors.append,
    )

    widget.viewer_widget.emit_selection(PdfRect(x1=10.0, y1=10.0, x2=30.0, y2=20.0))
    request = widget.submit_sign_request()

    assert request is not None
    assert executor.calls == [request]
    assert widget.last_signing_result is not None
    assert widget.last_signing_result.success is False
    assert errors == ["Post-sign verification failed."]
    assert widget.sign_result_label.text() == "Post-sign verification failed."


def test_signing_shell_shows_state_driven_flow_summary(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )

    assert widget.flow_stage_label.text() == "Place signature"
    assert "Drag on the page" in widget.flow_detail_label.text()
    assert len(widget.layout.items) == 1
    assert len(widget.layout.items[0][0].items) == 2
    assert widget.properties_scroll.parent is widget.sidebar
    assert widget.choose_output_button.parent is widget.sidebar
    assert widget.properties_scroll.widget is widget.properties_panel.container
    assert widget.properties_scroll.widget_resizable is True
    assert len(widget.properties_panel._appearance_controls.container.layout.items) == 2
    assert (
        len(widget.properties_panel._appearance_controls.container.layout.items[0][0].layout.rows)
        == 5
    )
    assert (
        len(widget.properties_panel._appearance_controls.container.layout.items[1][0].layout.rows)
        == 2
    )
    assert len(widget.properties_panel._placement_controls.container.layout.rows) == 3
    assert widget.properties_panel._appearance_controls.timezone_display_mode.currentText() == "UTC"
    assert widget.properties_panel._appearance_controls.stamp_position.currentText() == "Top"
    assert widget.properties_panel.validation_text() == "Place a signature on the page to continue."
    assert list(widget.properties_panel.field_controls.keys()) == [
        SignatureFieldKey.DISTINGUISHED_NAME,
        SignatureFieldKey.COMMON_NAME,
        SignatureFieldKey.EMAIL,
        SignatureFieldKey.TITLE,
        SignatureFieldKey.COMPANY,
        SignatureFieldKey.SIGNING_TIME,
        SignatureFieldKey.REASON,
        SignatureFieldKey.LOCATION,
    ]


def test_signing_shell_flow_summary_advances_after_signature_placement(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )

    widget.viewer_widget.emit_selection(PdfRect(x1=10.0, y1=10.0, x2=30.0, y2=20.0))

    assert widget.flow_stage_label.text() == "Confirm/sign"
    assert "Confirm the output path" in widget.flow_detail_label.text()
    assert widget.is_sign_action_enabled() is True


def test_signing_shell_normalizes_selection_rectangles(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )

    widget.viewer_widget.emit_selection(PdfRect(x1=40.0, y1=30.0, x2=10.0, y2=12.0))
    request = widget.submit_sign_request()

    assert request is not None
    assert request.signature_rect is not None
    assert request.signature_rect.left_pt == 10.0
    assert request.signature_rect.bottom_pt == 12.0
    assert request.signature_rect.width_pt == 30.0
    assert request.signature_rect.height_pt == 18.0


def test_signing_shell_page_selection_and_resize_controls_update_workflow(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )

    panel = widget.properties_panel
    panel._placement_controls.page_spin.setValue(2)
    panel._placement_controls.width_spin.setValue(40.0)
    panel._placement_controls.height_spin.setValue(20.0)

    signature_rect = widget.signature_rect()
    assert widget.logical_page_index() == 1
    assert signature_rect is not None
    assert signature_rect.page_index == 1
    assert signature_rect.width_pt == 40.0
    assert signature_rect.height_pt == 20.0
    assert widget.is_sign_action_enabled() is True


def test_signing_shell_preview_surfaces_datetime_format_and_image_stamp(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    appearance = build_signature_appearance(
        datetime_format="%d/%m/%Y %H:%M",
        image_stamp_path="/tmp/stamp.png",
        stamp_position=SignatureStampPosition.LEFT,
        show_field_names=True,
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )
    widget.properties_panel.set_signature_appearance(appearance)
    widget.set_signature_rect(
        page_index=0,
        left_pt=24.0,
        bottom_pt=18.0,
        width_pt=40.0,
        height_pt=20.0,
    )

    preview_text = widget.properties_panel.preview_text()
    preview_controls = widget.properties_panel.preview_controls

    assert len(widget.properties_panel._appearance_controls.container.layout.items) == 2
    assert (
        len(widget.properties_panel._appearance_controls.container.layout.items[0][0].layout.rows)
        == 5
    )
    assert (
        len(widget.properties_panel._appearance_controls.container.layout.items[1][0].layout.rows)
        == 2
    )
    assert preview_controls.multi_body_container.layout.items[0][0].pixmap() is not None
    assert (
        preview_controls.multi_body_container.layout.items[0][0].pixmap().path == "/tmp/stamp.png"
    )
    assert preview_controls.multi_body_container.layout.items[0][0].visible is True
    assert preview_controls.multi_body_container.layout.items[0][0].alignment == _FakeQt.AlignCenter
    assert preview_controls.title_label.text() == ""
    assert preview_controls.title_label.visible is False
    detail_text = preview_controls.multi_detail_label.text()
    detail_lines = detail_text.splitlines()
    assert detail_lines[0] == "Digitally signed by"
    assert detail_lines[1] == "Distinguished name: Distinguished name"
    assert detail_lines[2] == "Common name: Common name"
    assert detail_lines[3] == "Email: alice@example.com"
    assert detail_lines[4] == "Title: Director"
    assert detail_lines[5] == "Company: FoliaSeal"
    assert detail_lines[6].startswith("Signing time:")
    assert detail_lines[7] == "Reason: Approved"
    assert len(detail_lines) == 8
    assert preview_controls.footer_label.text() == ""
    assert widget.properties_panel._appearance_controls.font_family._items[
        :3
    ] == ["Sans Serif", "Serif", "Monospace"]
    assert (
        widget.properties_panel._appearance_controls.font_family.currentText()
        == "Source Sans 3"
    )
    assert "Digitally signed by" in preview_text
    assert "alice@example.com" in preview_text
    assert "Single line" not in preview_text
    assert "UTC" not in preview_text


def test_signing_shell_preview_keeps_fixed_width_for_oversized_text(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    appearance = build_signature_appearance(
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.TOP,
        signer_label_prefix="A very long prefix that should not widen the preview panel",
        show_field_names=True,
        image_stamp_path="/tmp/stamp.png",
        text_style=SignatureTextStyle(
            font_family="Source Sans 3",
            font_size_pt=12.0,
            bold=False,
            italic=False,
            text_color_hex="#123456",
        ),
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )
    widget.properties_panel.set_signature_appearance(appearance)
    widget.set_signature_rect(
        page_index=0,
        left_pt=24.0,
        bottom_pt=18.0,
        width_pt=88.0,
        height_pt=28.0,
    )

    preview_controls = widget.properties_panel.preview_controls

    assert preview_controls.single_body_container.style == (
        "background: transparent; border: none; padding: 0px;"
    )
    assert preview_controls.multi_body_container.style == (
        "background: transparent; border: none; padding: 0px;"
    )
    assert preview_controls.single_render_label.style == (
        "background: transparent; border: none; padding: 0px;"
    )
    assert preview_controls.multi_render_label.style == (
        "background: transparent; border: none; padding: 0px;"
    )
    assert preview_controls.multi_body_container.visible is False
    assert preview_controls.single_body_container.visible is True
    assert preview_controls.title_label.visible is False
    assert preview_controls.title_label.text() == ""
    assert preview_controls.detail_label.text().startswith("A very long prefix")


def test_signing_shell_validation_label_is_width_limited_to_panel(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )

    panel = widget.properties_panel
    widget.set_signature_rect(
        page_index=0,
        left_pt=24.0,
        bottom_pt=18.0,
        width_pt=40.0,
        height_pt=20.0,
    )
    panel._control_issue = SigningDraftValidationIssue(
        code="visible_signature_layout_unavailable",
        message=(
            "Visible signature content does not fit inside the selected rectangle "
            "for the single_line template. Enlarge the signature box or choose "
            "a more compact appearance."
        ),
        field_name="signature_appearance",
        severity=SigningDraftValidationSeverity.ERROR,
    )

    panel.refresh_preview()

    assert panel._validation_label.fixed_width == 464
    assert panel.validation_text().startswith("Will fail to sign:")


def test_signing_shell_card_size_tracks_selected_rectangle_aspect_ratio(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )
    panel = widget.properties_panel
    preview_controls = panel.preview_controls
    widget.set_signature_rect(
        page_index=0,
        left_pt=35.0,
        bottom_pt=429.0,
        width_pt=260.0,
        height_pt=22.0,
    )

    card_width, card_height = preview_controls.card_container.fixed_size
    rect_ratio = 260.0 / 22.0
    card_ratio = card_width / card_height

    assert abs(card_ratio - rect_ratio) < 0.5


def test_signing_shell_stamp_position_bottom_places_stamp_after_text(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    appearance = build_signature_appearance(
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.BOTTOM,
        image_stamp_path="/tmp/stamp.png",
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )
    widget.properties_panel.set_signature_appearance(appearance)
    widget.set_signature_rect(
        page_index=0,
        left_pt=24.0,
        bottom_pt=18.0,
        width_pt=120.0,
        height_pt=60.0,
    )

    preview_controls = widget.properties_panel.preview_controls

    assert preview_controls.single_body_container.visible is True
    assert preview_controls.multi_body_container.visible is False
    assert preview_controls.stamp_label.visible is True
    assert preview_controls.stamp_label.alignment == (_FakeQt.AlignLeft | _FakeQt.AlignTop)
    assert preview_controls.stamp_label.pixmap().height < preview_controls.stamp_label.fixed_size[1]
    assert preview_controls.detail_label.visible is True
    assert " | " in widget.properties_panel.preview_text()


def test_signing_shell_stamp_position_left_centers_text_beside_stamp(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    appearance = build_signature_appearance(
        layout_template=SignatureLayoutTemplate.MULTI_LINE,
        stamp_position=SignatureStampPosition.LEFT,
        image_stamp_path="/tmp/stamp.png",
        signer_label_prefix="",
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )
    widget.properties_panel.set_signature_appearance(appearance)
    widget.set_signature_rect(
        page_index=0,
        left_pt=24.0,
        bottom_pt=18.0,
        width_pt=120.0,
        height_pt=60.0,
    )

    preview_controls = widget.properties_panel.preview_controls

    assert preview_controls.title_label.visible is False
    assert preview_controls.single_body_container.visible is False
    assert preview_controls.multi_body_container.visible is True
    assert preview_controls.multi_body_container.layout.items[0][0] is (
        preview_controls.multi_stamp_label
    )
    assert preview_controls.multi_body_container.layout.items[0][1] == (0, _FakeQt.AlignCenter)
    assert preview_controls.multi_body_container.layout.items[1][0] is (
        preview_controls.multi_content_container
    )
    assert preview_controls.multi_body_container.layout.items[1][1] == (0, _FakeQt.AlignCenter)


def test_signing_shell_stamp_position_control_updates_workflow(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )

    panel = widget.properties_panel
    panel._appearance_controls.stamp_position.setCurrentText("Right")

    appearance = widget.signature_appearance()
    assert appearance is not None
    assert appearance.stamp_position == SignatureStampPosition.RIGHT
    assert panel.preview.stamp_position == SignatureStampPosition.RIGHT
    assert "Stamp position: right" in signing_shell_module._format_appearance_summary(
        appearance
    )


def test_signing_shell_preview_respects_small_font_sizes(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    appearance = build_signature_appearance(
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        text_style=SignatureTextStyle(
            font_family="Source Sans 3",
            font_size_pt=6.5,
            bold=False,
            italic=False,
            text_color_hex="#123456",
        ),
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )
    widget.properties_panel.set_signature_appearance(appearance)
    widget.set_signature_rect(
        page_index=0,
        left_pt=24.0,
        bottom_pt=18.0,
        width_pt=40.0,
        height_pt=20.0,
    )

    assert "font-size: 6.5pt;" in widget.properties_panel.preview_controls.title_label.style
    assert "font-size: 6.5pt;" in widget.properties_panel.preview_controls.detail_label.style


def test_signing_shell_preview_updates_style_when_font_size_changes(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )
    widget.properties_panel.set_signature_appearance(
        build_signature_appearance(
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            text_style=SignatureTextStyle(
                font_family="Source Sans 3",
                font_size_pt=8.5,
                bold=False,
                italic=False,
                text_color_hex="#123456",
            ),
        )
    )
    widget.set_signature_rect(
        page_index=0,
        left_pt=24.0,
        bottom_pt=18.0,
        width_pt=40.0,
        height_pt=20.0,
    )
    initial_style = widget.properties_panel.preview_controls.detail_label.style

    widget.properties_panel.set_signature_appearance(
        build_signature_appearance(
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            text_style=SignatureTextStyle(
                font_family="Source Sans 3",
                font_size_pt=8.0,
                bold=False,
                italic=False,
                text_color_hex="#123456",
            ),
        )
    )

    assert "font-size: 8.5pt;" in initial_style
    assert "font-size: 8.0pt;" in widget.properties_panel.preview_controls.detail_label.style


def test_signing_shell_preview_keeps_text_size_invariant_across_layout_modes(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )
    rect = widget.set_signature_rect(
        page_index=0,
        left_pt=24.0,
        bottom_pt=18.0,
        width_pt=96.0,
        height_pt=88.0,
    )
    for layout_template in (
        SignatureLayoutTemplate.SINGLE_LINE,
        SignatureLayoutTemplate.MULTI_LINE,
        SignatureLayoutTemplate.WRAPPED_BLOCK,
    ):
        widget.properties_panel.set_signature_appearance(
            build_signature_appearance(
                layout_template=layout_template,
                text_style=SignatureTextStyle(
                    font_family="Serif",
                    font_size_pt=8.5,
                    bold=False,
                    italic=True,
                    text_color_hex="#123456",
                ),
            )
        )
        widget.properties_panel.set_signature_rect(rect)
        detail_style = widget.properties_panel.preview_controls.detail_label.style
        multi_detail_style = widget.properties_panel.preview_controls.multi_detail_label.style

        assert "font-size: 8.5pt;" in detail_style or "font-size: 8.5pt;" in multi_detail_style


def test_signing_shell_single_line_preview_disables_word_wrap_even_without_rect(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    appearance = build_signature_appearance(
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )
    widget.properties_panel.set_signature_appearance(appearance)

    assert widget.properties_panel.preview_controls.title_label.word_wrap is False
    assert widget.properties_panel.preview_controls.detail_label.word_wrap is False
    assert widget.properties_panel.preview_controls.multi_detail_label.word_wrap is False


def test_signing_shell_fresh_workflow_uses_signer_first_default_preview_order(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )
    widget.set_signature_rect(
        page_index=0,
        left_pt=24.0,
        bottom_pt=18.0,
        width_pt=40.0,
        height_pt=20.0,
    )

    preview = widget.properties_panel.preview
    expected_stamp_text = signing_shell_module._preview_stamp_text(preview)
    assert widget.properties_panel._appearance_controls.show_field_names.isChecked() is False
    assert widget.properties_panel.preview_controls.title_label.text() == ""
    assert widget.properties_panel.preview_controls.title_label.visible is False
    detail_text = widget.properties_panel.preview_controls.detail_label.text()
    assert detail_text.startswith(
        "Digitally signed by\nDistinguished name | Common name | Email | Title | Company | "
    )
    assert detail_text.endswith(" UTC | Reason | Location")
    assert expected_stamp_text.startswith("Digitally signed by\nDistinguished name | Common name")


def test_signing_shell_visible_fields_use_source_as_single_visibility_control(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )

    distinguished_name_controls = widget.properties_panel.field_controls[
        SignatureFieldKey.DISTINGUISHED_NAME
    ]
    source_combo = distinguished_name_controls.source_combo

    assert not hasattr(distinguished_name_controls, "visible_check")
    assert source_combo.findText("Hidden") != -1
    source_combo.setCurrentText("Hidden")
    widget.properties_panel.refresh_preview()

    assert widget.properties_panel.preview.fields[0].visible is False


def test_signing_shell_signing_time_hidden_source_hides_preview_field(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )

    signing_time_controls = widget.properties_panel.field_controls[SignatureFieldKey.SIGNING_TIME]
    signing_time_controls.source_combo.setCurrentText("Hidden")
    widget.properties_panel.refresh_preview()

    preview_field = next(
        field
        for field in widget.properties_panel.preview.fields
        if field.field_key == SignatureFieldKey.SIGNING_TIME
    )
    assert preview_field.visible is False


def test_signing_shell_wrapped_block_preview_groups_tail_fields(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    appearance = build_signature_appearance(
        layout_template=signing_shell_module.SignatureLayoutTemplate.WRAPPED_BLOCK,
        stamp_position=SignatureStampPosition.LEFT,
        show_field_names=True,
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )
    widget.properties_panel.set_signature_appearance(appearance)
    widget.set_signature_rect(
        page_index=0,
        left_pt=24.0,
        bottom_pt=18.0,
        width_pt=40.0,
        height_pt=20.0,
    )

    detail_lines = widget.properties_panel.preview_controls.multi_detail_label.text().splitlines()

    assert len(detail_lines) == 4
    assert detail_lines[0] == "Digitally signed by"
    assert detail_lines[1].startswith("Distinguished name:")
    assert detail_lines[2].startswith("Common name:")
    assert "Email: alice@example.com" in detail_lines[3]
    assert "Title: Director" in detail_lines[3]
    assert "Company: FoliaSeal" in detail_lines[3]
    assert "Signing time:" in detail_lines[3]
    assert "Reason: Approved" in detail_lines[3]


def test_signing_shell_wrapped_block_preview_uses_value_only_text_by_default(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    appearance = build_signature_appearance(
        layout_template=signing_shell_module.SignatureLayoutTemplate.WRAPPED_BLOCK,
        stamp_position=SignatureStampPosition.LEFT,
        show_field_names=False,
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )
    widget.properties_panel.set_signature_appearance(appearance)
    widget.set_signature_rect(
        page_index=0,
        left_pt=24.0,
        bottom_pt=18.0,
        width_pt=40.0,
        height_pt=20.0,
    )

    detail_lines = widget.properties_panel.preview_controls.multi_detail_label.text().splitlines()

    assert len(detail_lines) == 4
    assert detail_lines[0] == "Digitally signed by"
    assert detail_lines[1] == "Distinguished name"
    assert detail_lines[2] == "Common name"
    assert "alice@example.com" in detail_lines[3]
    assert "Director" in detail_lines[3]
    assert "FoliaSeal" in detail_lines[3]
    assert "Approved" in detail_lines[3]
    assert "Email:" not in detail_lines[3]
    assert "Title:" not in detail_lines[3]
    assert "Company:" not in detail_lines[3]
    assert "Reason:" not in detail_lines[3]


def test_signing_shell_preview_text_uses_active_vertical_label_for_wrapped_block(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    appearance = build_signature_appearance(
        layout_template=SignatureLayoutTemplate.WRAPPED_BLOCK,
        stamp_position=SignatureStampPosition.TOP,
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )
    widget.properties_panel.set_signature_appearance(appearance)
    widget.set_signature_rect(
        page_index=0,
        left_pt=24.0,
        bottom_pt=18.0,
        width_pt=180.0,
        height_pt=54.0,
    )

    detail = widget.properties_panel.preview_controls.detail_label.text()

    assert widget.properties_panel.preview_controls.single_body_container.visible is True
    assert detail
    assert widget.properties_panel.preview_text() == detail.strip()


def test_signing_shell_repeated_custom_combo_value_loads_do_not_duplicate_items(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    appearance = build_signature_appearance(
        datetime_format="custom-format",
        text_style=SignatureTextStyle(
            font_family="Custom Font",
            font_size_pt=9.5,
            bold=True,
            italic=False,
            text_color_hex="#123456",
        ),
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )

    widget.properties_panel.set_signature_appearance(appearance)
    widget.properties_panel.load_from_workflow()
    widget.properties_panel.load_from_workflow()

    datetime_combo = widget.properties_panel._appearance_controls.datetime_format
    font_combo = widget.properties_panel._appearance_controls.font_family

    assert datetime_combo._items.count("custom-format") == 1
    assert font_combo._items.count("Custom Font") == 1


def test_signing_shell_signature_preset_save_and_reload_round_trip(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    store = SignaturePresetCatalogStore(storage_dir=tmp_path / PROFILE_DIRECTORY_NAME)
    store.save_catalog(build_signature_preset_catalog())
    certificate_store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    certificate_catalog = build_certificate_catalog()
    certificate_store.save_catalog(certificate_catalog)
    managed_cert = certificate_catalog.managed_certificates[0]
    (certificate_store.managed_certificate_dir / managed_cert.storage_filename).write_bytes(
        b"pkcs12-bytes"
    )
    workflow = _workflow(tmp_path)
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=workflow,
        certificate_catalog_store=certificate_store,
        preset_catalog_store=store,
    )

    panel = widget.properties_panel
    panel._certificate_controls.configuration_combo.setCurrentText("Corporate Records Signing")
    panel._certificate_controls.password_input.setText("typed-secret")
    assert panel.apply_selected_certificate_configuration() is True
    panel._signature_preset_controls.preset_name.setText("My Preset")
    panel._appearance_controls.signer_label_prefix.setText("Signed by Me")
    panel._appearance_controls.show_field_names.setChecked(True)
    panel._placement_controls.width_spin.setValue(144.0)
    panel._placement_controls.height_spin.setValue(36.0)
    panel._signature_preset_controls.save_button.click()

    assert panel._preset_catalog.preset_names()[-1] == "My Preset"
    assert panel._signature_preset_controls.preset_combo.currentText() == "My Preset"
    assert panel._signature_preset_controls.preset_name.text() == "My Preset"
    assert panel._preset_catalog.preset_named("My Preset").placement_defaults == (
        SignaturePlacementDefaults(
            width_pt=144.0,
            height_pt=36.0,
        )
    )
    assert (
        store.load_catalog().preset_named("My Preset").preset.certificate_configuration_id
        == "cert-config-default"
    )

    panel._appearance_controls.signer_label_prefix.setText("Temporary Draft")
    assert panel._signature_preset_controls.preset_combo.currentText() == "Current signature setup"
    workflow.selected_certificate_configuration_id = None

    panel._signature_preset_controls.preset_combo.setCurrentText("My Preset")

    assert panel._appearance_controls.signer_label_prefix.text() == "Signed by Me"
    assert panel._appearance_controls.show_field_names.isChecked() is True
    assert panel._placement_controls.width_spin.value() == 144.0
    assert panel._placement_controls.height_spin.value() == 36.0
    assert workflow.selected_certificate_configuration_id == "cert-config-default"

    relaunch_widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
        preset_catalog_store=store,
    )
    relaunch_panel = relaunch_widget.properties_panel

    assert relaunch_panel._preset_catalog.preset_names() == (
        "Default",
        "Compact",
        "My Preset",
    )
    assert relaunch_panel._signature_preset_controls.preset_combo.findText("My Preset") != -1
    assert (
        relaunch_panel._signature_preset_controls.preset_combo.currentText()
        == "Current signature setup"
    )


def test_signing_shell_signature_preset_save_without_name_reports_error(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    errors: list[str] = []
    fake_bindings = _fake_bindings()
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: fake_bindings,
    )
    store = SignaturePresetCatalogStore(storage_dir=tmp_path / PROFILE_DIRECTORY_NAME)
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
        preset_catalog_store=store,
        on_error=errors.append,
    )

    panel = widget.properties_panel
    panel._signature_preset_controls.preset_name.setText("")

    result = panel.save_current_signature_preset()

    assert result is None
    assert errors == []
    assert store.load_catalog().preset_names() == ()
    assert fake_bindings.q_message_box.calls[-1][1:] == (
        "Signature preset error",
        "Preset name is required before saving.",
    )


def test_signing_shell_signature_preset_selection_restores_placement_defaults_without_forcing_rect(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    preset = build_signature_preset(
        name="Compact",
        placement_defaults=SignaturePlacementDefaults(
            width_pt=144.0,
            height_pt=36.0,
        ),
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
        preset_catalog=build_signature_preset_catalog(profiles=(preset,)),
    )

    panel = widget.properties_panel
    assert widget.signature_rect() is None
    widget.set_selected_certificate_configuration_id("cert-config-current")

    panel._signature_preset_controls.preset_combo.setCurrentText("Compact")

    assert panel._signature_preset_controls.preset_name.text() == "Compact"
    assert panel._placement_controls.width_spin.value() == 144.0
    assert panel._placement_controls.height_spin.value() == 36.0
    assert widget.signature_rect() is None
    assert widget.selected_certificate_configuration_id() == "cert-config-current"


def test_signing_shell_signature_preset_selection_applies_certificate_material(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

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
    default_path.write_bytes(b"default-pkcs12")
    alternate_path.write_bytes(b"alternate-pkcs12")

    preset = build_signature_preset(
        name="Alternate Preset",
        certificate_configuration_id="cert-config-alt",
    )
    workflow = _workflow(tmp_path)
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=workflow,
        certificate_catalog_store=certificate_store,
        preset_catalog=build_signature_preset_catalog(profiles=(preset,)),
    )
    panel = widget.properties_panel
    panel._certificate_controls.configuration_combo.setCurrentText("Default Signing")
    panel._certificate_controls.password_input.setText("default-secret")

    assert panel.apply_selected_certificate_configuration() is True
    assert workflow.selected_certificate_configuration_id == "cert-config-default"
    assert workflow.certificate_path == str(default_path)
    assert workflow.passphrase == "default-secret"

    panel._certificate_controls.password_input.setText("alternate-secret")
    panel._signature_preset_controls.preset_combo.setCurrentText("Alternate Preset")

    assert workflow.selected_certificate_configuration_id == "cert-config-alt"
    assert workflow.certificate_path == str(alternate_path)
    assert workflow.passphrase == "alternate-secret"
    assert panel._certificate_controls.configuration_combo.currentText() == "Alternate Signing"


def test_signing_shell_signature_preset_delete_can_be_canceled_and_keeps_preset(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    fake_bindings = _fake_bindings()
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: fake_bindings,
    )

    store = SignaturePresetCatalogStore(storage_dir=tmp_path / PROFILE_DIRECTORY_NAME)
    store.save_catalog(build_signature_preset_catalog())
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
        preset_catalog_store=store,
    )

    panel = widget.properties_panel
    panel._signature_preset_controls.preset_combo.setCurrentText("Compact")
    fake_bindings.q_message_box.next_result = fake_bindings.q_message_box.No

    result = panel.delete_current_signature_preset()

    assert result is None
    assert store.load_catalog().preset_names() == ("Default", "Compact")
    assert panel._signature_preset_controls.preset_combo.currentText() == "Compact"
    assert panel._preset_catalog.preset_names() == ("Default", "Compact")


def test_signing_shell_signature_preset_delete_requires_confirmation_and_refreshes_catalog(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    fake_bindings = _fake_bindings()
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: fake_bindings,
    )

    store = SignaturePresetCatalogStore(storage_dir=tmp_path / PROFILE_DIRECTORY_NAME)
    store.save_catalog(build_signature_preset_catalog())
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
        preset_catalog_store=store,
    )

    panel = widget.properties_panel
    panel._signature_preset_controls.preset_combo.setCurrentText("Compact")
    fake_bindings.q_message_box.next_result = fake_bindings.q_message_box.Yes

    result = panel.delete_current_signature_preset()

    assert result is not None
    assert result.preset_names() == ("Default",)
    assert store.load_catalog().preset_names() == ("Default",)
    assert panel._signature_preset_controls.preset_combo.currentText() == "Current signature setup"
    assert panel._preset_catalog.preset_names() == ("Default",)
    assert panel._signature_preset_controls.preset_combo.findText("Compact") == -1

    relaunched_widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
        preset_catalog_store=store,
    )
    relaunched_panel = relaunched_widget.properties_panel

    assert relaunched_panel._preset_catalog.preset_names() == ("Default",)
    assert relaunched_panel._signature_preset_controls.preset_combo.findText("Compact") == -1


def test_signing_shell_signature_preset_overwrite_requires_confirmation(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    fake_bindings = _fake_bindings()
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: fake_bindings,
    )

    existing = build_signature_preset(
        name="Team Standard",
        appearance=build_signature_appearance(signer_label_prefix="Signed by Team"),
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
        preset_catalog=build_signature_preset_catalog(profiles=(existing,)),
    )

    panel = widget.properties_panel
    panel._appearance_controls.signer_label_prefix.setText("Signed by Current Draft")
    panel._signature_preset_controls.preset_name.setText("Team Standard")

    fake_bindings.q_message_box.next_result = fake_bindings.q_message_box.No
    result = panel.save_current_signature_preset()

    assert result is None
    assert fake_bindings.q_message_box.calls
    assert panel._preset_catalog.preset_named("Team Standard").appearance == existing.appearance

    fake_bindings.q_message_box.next_result = fake_bindings.q_message_box.Yes
    result = panel.save_current_signature_preset()

    assert result is not None
    assert result.name == "Team Standard"
    assert panel._preset_catalog.preset_named("Team Standard").appearance.signer_label_prefix == (
        "Signed by Current Draft"
    )
    assert panel._signature_preset_controls.preset_combo.currentText() == "Team Standard"


def test_signing_shell_warning_only_issue_keeps_readiness_enabled(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )
    widget.set_signature_rect(
        page_index=0,
        left_pt=24.0,
        bottom_pt=18.0,
        width_pt=40.0,
        height_pt=20.0,
    )
    widget.properties_panel._control_issue = SigningDraftValidationIssue(
        code="preview_warning",
        message="Preview is stale but still usable.",
        field_name="signature_appearance",
        severity=SigningDraftValidationSeverity.WARNING,
    )
    widget.properties_panel.refresh_preview()

    assert widget.properties_panel.preview.can_submit is True
    assert widget.properties_panel.is_ready_to_sign() is True
    assert widget.is_sign_action_enabled() is True
    assert widget.properties_panel.validation_text() == "Ready to sign."


def test_signing_shell_allows_blank_signer_label_prefix_and_frees_title_line(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    errors = []
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
        on_error=errors.append,
    )

    widget.viewer_widget.emit_selection(PdfRect(x1=10.0, y1=10.0, x2=30.0, y2=20.0))
    widget.properties_panel._appearance_controls.signer_label_prefix.setText("")

    assert widget.properties_panel.preview.can_submit is True
    assert widget.properties_panel.preview.signer_label_prefix == ""
    assert widget.properties_panel.preview.title == ""
    assert widget.properties_panel.preview_controls.title_label.visible is False
    assert widget.properties_panel.validation_text().startswith("Ready to sign.")

    request = widget.submit_sign_request()

    assert request is not None
    assert errors == []
    assert widget.is_sign_action_enabled() is True


def test_signing_shell_single_line_preview_matches_backend_wrapping(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    appearance = build_signature_appearance(
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )
    widget.properties_panel.set_signature_appearance(appearance)
    widget.set_signature_rect(
        page_index=0,
        left_pt=24.0,
        bottom_pt=18.0,
        width_pt=40.0,
        height_pt=20.0,
    )

    preview = widget.properties_panel.preview
    expected = signing_shell_module._preview_stamp_text(preview)
    assert widget.properties_panel.preview_controls.title_label.text() == ""
    assert widget.properties_panel.preview_controls.title_label.visible is False
    assert widget.properties_panel.preview_controls.detail_label.text() == expected


def test_signing_shell_single_line_horizontal_preview_text_uses_active_detail_label(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    appearance = build_signature_appearance(
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.RIGHT,
        image_stamp_path="/tmp/stamp.png",
        signer_label_prefix="",
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )
    widget.properties_panel.set_signature_appearance(appearance)
    widget.set_signature_rect(
        page_index=0,
        left_pt=24.0,
        bottom_pt=18.0,
        width_pt=180.0,
        height_pt=36.0,
    )

    detail = widget.properties_panel._preview_controls.multi_detail_label.text()

    assert widget.properties_panel.preview_controls.single_body_container.visible is False
    assert widget.properties_panel.preview_controls.multi_body_container.visible is True
    assert detail
    assert widget.properties_panel.preview_text() == detail.strip()


def test_signing_shell_single_line_horizontal_preview_reserves_width_for_stamp(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    appearance = build_signature_appearance(
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.RIGHT,
        image_stamp_path="/tmp/stamp.png",
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )
    widget.properties_panel.set_signature_appearance(appearance)
    widget.set_signature_rect(
        page_index=0,
        left_pt=24.0,
        bottom_pt=18.0,
        width_pt=180.0,
        height_pt=36.0,
    )

    preview = widget.properties_panel.preview
    actual_text = widget.properties_panel.preview_controls.multi_detail_label.text()

    for fragment in (
        "Digitally signed by",
        "Director",
        "FoliaSeal",
        "Approved",
    ):
        assert fragment in actual_text
    assert preview.layout_template == SignatureLayoutTemplate.SINGLE_LINE
    assert widget.properties_panel.preview_controls.multi_body_container.visible is True


def test_signing_shell_multi_line_horizontal_preview_uses_reserved_text_height(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    appearance = build_signature_appearance(
        layout_template=SignatureLayoutTemplate.MULTI_LINE,
        stamp_position=SignatureStampPosition.LEFT,
        image_stamp_path="/tmp/stamp.png",
        signer_label_prefix="",
        title=build_signature_field_binding(show_in_visible_appearance=False),
        reason=build_signature_field_binding(show_in_visible_appearance=False),
        location=build_signature_field_binding(
            source=signing_shell_module.SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
    )

    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )
    widget.properties_panel.set_signature_appearance(appearance)
    widget.set_signature_rect(
        page_index=0,
        left_pt=35.84,
        bottom_pt=429.12,
        width_pt=202.24,
        height_pt=23.04,
    )

    preview = widget.properties_panel.preview

    assert preview.layout_template == SignatureLayoutTemplate.MULTI_LINE
    assert widget.properties_panel.preview_controls.multi_body_container.visible is True
    assert widget.properties_panel.preview_controls.multi_detail_label.text()


def test_signing_shell_single_line_horizontal_preview_centers_stamp_within_side_band(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    for stamp_position in (
        SignatureStampPosition.LEFT,
        SignatureStampPosition.RIGHT,
    ):
        appearance = build_signature_appearance(
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=stamp_position,
            image_stamp_path="/tmp/stamp.png",
        )
        widget = build_qt_signing_shell(
            viewer_workflow=_viewer_workflow(),
            signing_workflow=_workflow(tmp_path),
        )
        widget.properties_panel.set_signature_appearance(appearance)
        widget.set_signature_rect(
            page_index=0,
            left_pt=24.0,
            bottom_pt=18.0,
            width_pt=180.0,
            height_pt=36.0,
        )

        assert (
            widget.properties_panel.preview_controls.multi_body_container.layout.items[
                0 if stamp_position == SignatureStampPosition.LEFT else 1
            ][0].alignment
            == _FakeQt.AlignCenter
        )


def test_signing_shell_horizontal_preview_updates_text_width_for_thick_borders(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    appearance = build_signature_appearance(
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.RIGHT,
        image_stamp_path="/tmp/stamp.png",
        box_style=SignatureBoxStyle(
            show_border=True,
            border_color_hex="#000000",
            border_width_pt=7.0,
            background_color_hex="#FFFFFF",
        ),
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )
    widget.properties_panel.set_signature_appearance(appearance)
    widget.set_signature_rect(
        page_index=0,
        left_pt=24.0,
        bottom_pt=18.0,
        width_pt=180.0,
        height_pt=36.0,
    )

    default_width = widget.properties_panel.preview_controls.multi_content_container.fixed_width
    thick_border_appearance = build_signature_appearance(
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.RIGHT,
        image_stamp_path="/tmp/stamp.png",
        box_style=SignatureBoxStyle(
            show_border=True,
            border_color_hex="#000000",
            border_width_pt=10.0,
            background_color_hex="#FFFFFF",
        ),
    )
    widget.properties_panel.set_signature_appearance(thick_border_appearance)

    thick_width = widget.properties_panel.preview_controls.multi_content_container.fixed_width

    assert thick_width != default_width
    assert thick_width is not None


def test_signing_shell_uses_canonical_preview_snapshot_when_assets_are_renderable(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    stamp_path = tmp_path / "stamp.png"
    Image.new("RGBA", (96, 32), color=(0, 0, 0, 255)).save(stamp_path)
    appearance = build_signature_appearance(
        layout_template=SignatureLayoutTemplate.MULTI_LINE,
        stamp_position=SignatureStampPosition.LEFT,
        image_stamp_path=str(stamp_path),
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )
    widget.properties_panel.set_signature_appearance(appearance)
    widget.set_signature_rect(
        page_index=0,
        left_pt=24.0,
        bottom_pt=18.0,
        width_pt=180.0,
        height_pt=48.0,
    )

    snapshot = widget.properties_panel.preview_controls.card_container._canonical_preview_snapshot

    assert snapshot is not None
    assert Path(snapshot.image_path).exists()
    assert snapshot.text_bounds_px is not None
    assert snapshot.stamp_bounds_px is not None


def test_signing_shell_disposes_canonical_preview_snapshot_on_widget_close(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )
    widget.set_signature_rect(
        page_index=0,
        left_pt=24.0,
        bottom_pt=18.0,
        width_pt=180.0,
        height_pt=48.0,
    )

    snapshot = widget.properties_panel.preview_controls.card_container._canonical_preview_snapshot
    assert snapshot is not None
    snapshot_dir = Path(snapshot.image_path).parent
    assert snapshot_dir.exists()

    widget.close()

    snapshot = widget.properties_panel.preview_controls.card_container._canonical_preview_snapshot
    assert snapshot is None
    assert not snapshot_dir.exists()


def test_signing_shell_sizes_canonical_render_label_to_scaled_pixmap(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    preview_path = tmp_path / "preview.png"
    Image.new("RGBA", (120, 60), color=(255, 255, 255, 255)).save(preview_path)

    def _fake_render(preview, **kwargs):
        return preview_lifecycle_module.CanonicalSignaturePreviewSnapshot(
            image_path=str(preview_path),
            width_px=120,
            height_px=60,
            text_area_bounds_px={"x": 0, "y": 0, "width": 120, "height": 60},
            stamp_area_bounds_px=None,
            text_bounds_px={"x": 0, "y": 0, "width": 120, "height": 60},
            stamp_bounds_px=None,
        )

    monkeypatch.setattr(
        preview_lifecycle_module,
        "render_canonical_signature_preview",
        _fake_render,
    )
    monkeypatch.setattr(
        signing_shell_module.QtCanonicalPreviewLifecycle,
        "_load_canonical_preview_pixmap",
        lambda self, **kwargs: _FakePixmap("preview", width=91, height=37),
        raising=False,
    )

    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )
    widget.properties_panel.refresh_preview()

    assert widget.properties_panel.preview_controls.single_render_label.fixed_size == (91, 37)
    assert widget.properties_panel.preview_controls.single_body_container.fixed_size == (91, 37)


def test_signing_shell_suppresses_outer_card_chrome_when_canonical_preview_is_active(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        signing_shell_module,
        "build_qt_pdf_viewer_widget",
        lambda **kwargs: _FakeViewerWidget(**kwargs),
    )
    monkeypatch.setattr(
        signing_shell_module.SigningShellAdapter,
        "_load_bindings",
        lambda self: _fake_bindings(),
    )

    preview_path = tmp_path / "preview.png"
    Image.new("RGBA", (120, 60), color=(255, 255, 255, 255)).save(preview_path)

    def _fake_render(preview, **kwargs):
        return preview_lifecycle_module.CanonicalSignaturePreviewSnapshot(
            image_path=str(preview_path),
            width_px=120,
            height_px=60,
            text_area_bounds_px={"x": 0, "y": 0, "width": 120, "height": 60},
            stamp_area_bounds_px=None,
            text_bounds_px={"x": 0, "y": 0, "width": 120, "height": 60},
            stamp_bounds_px=None,
        )

    monkeypatch.setattr(
        preview_lifecycle_module,
        "render_canonical_signature_preview",
        _fake_render,
    )

    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )
    widget.properties_panel.refresh_preview()

    assert widget.properties_panel.preview_controls.card_container.style == (
        "QGroupBox { border: none; background: transparent; padding: 0px; }"
    )
