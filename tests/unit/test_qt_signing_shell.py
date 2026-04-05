from pathlib import Path

from foliaseal.application import (
    SigningDraftValidationIssue,
    SigningDraftValidationSeverity,
    SigningDraftWorkflow,
)
from foliaseal.application.coordinate_transform import PdfRect
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
from foliaseal.infra.config.profile_storage import (
    PROFILE_DIRECTORY_NAME,
    SignaturePresetCatalogStore,
)
from foliaseal.infra.render import PdfPageGeometry, RenderPageRequest, RenderPageResult
from foliaseal.presentation.qt import build_qt_signing_shell
from foliaseal.presentation.qt import signing_shell as signing_shell_module
from foliaseal.presentation.qt.signing_shell import QtSigningWidgetBindings
from tests.support.phase3_builders import (
    build_signature_appearance,
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

    def setLayout(self, layout):  # noqa: N802
        self.layout = layout

    def setEnabled(self, value):  # noqa: N802
        self.enabled = value

    def setVisible(self, value):  # noqa: N802
        self.visible = bool(value)

    def setStyleSheet(self, style):  # noqa: N802
        self.style = style

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


class _FakeSigningExecutor:
    def __init__(self, result: SigningResult) -> None:
        self.result = result
        self.calls = []

    def execute(self, request):
        self.calls.append(request)
        return self.result


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
    assert requests == [request]
    assert request.signature_rect is not None


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

    widget._signing_workspace._viewer_workflow.session.jump_to_page(2)
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
            timestamp_present=True,
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
    assert widget._signing_workspace.last_signing_result is not None
    assert widget._signing_workspace.last_signing_result.success is True
    assert (
        widget.sign_result_label.text()
        == f"Signing completed successfully. Output: {request.output_pdf_path}"
    )


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
    assert widget._signing_workspace.last_signing_result is not None
    assert widget._signing_workspace.last_signing_result.success is False
    assert errors == ["Post-sign verification failed."]
    assert widget.sign_result_label.text() == "Post-sign verification failed."


def test_signing_shell_uses_split_layout_without_stage_box(monkeypatch, tmp_path: Path) -> None:
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

    assert not hasattr(widget._signing_workspace, "_flow_summary_box")
    assert widget.properties_scroll.widget is widget.properties_panel.container
    assert widget.properties_scroll.widget_resizable is True
    assert len(widget.properties_panel._appearance_controls.container.layout.items) == 2
    assert len(
        widget.properties_panel._appearance_controls.container.layout.items[0][0].layout.rows
    ) == 5
    assert len(
        widget.properties_panel._appearance_controls.container.layout.items[1][0].layout.rows
    ) == 2
    assert len(widget.properties_panel._placement_controls.container.layout.rows) == 3
    assert (
        widget.properties_panel._appearance_controls.timezone_display_mode.currentText()
        == "UTC"
    )
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

    assert widget._signing_workspace._viewer_workflow.session.current_page == 1
    assert widget._signing_workspace._draft_workflow.signature_rect is not None
    assert widget._signing_workspace._draft_workflow.signature_rect.page_index == 1
    assert widget._signing_workspace._draft_workflow.signature_rect.width_pt == 40.0
    assert widget._signing_workspace._draft_workflow.signature_rect.height_pt == 20.0
    assert widget._signing_workspace._sign_button._enabled is True


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
    widget.properties_panel.set_signature_rect(
        widget._signing_workspace._draft_workflow.signature_rect
        or widget._signing_workspace._draft_workflow.update_signature_rect(
            page_index=0,
            left_pt=24.0,
            bottom_pt=18.0,
            width_pt=40.0,
            height_pt=20.0,
        )
    )

    preview_text = widget.properties_panel.preview_text()
    preview_controls = widget.properties_panel.preview_controls

    assert len(widget.properties_panel._appearance_controls.container.layout.items) == 2
    assert len(
        widget.properties_panel._appearance_controls.container.layout.items[0][0].layout.rows
    ) == 5
    assert len(
        widget.properties_panel._appearance_controls.container.layout.items[1][0].layout.rows
    ) == 2
    assert preview_controls.multi_body_container.layout.items[0][0].pixmap() is not None
    assert (
        preview_controls.multi_body_container.layout.items[0][0].pixmap().path
        == "/tmp/stamp.png"
    )
    assert preview_controls.multi_body_container.layout.items[0][0].text() == ""
    assert preview_controls.multi_body_container.layout.items[0][0].fixed_size is not None
    width, height = preview_controls.multi_body_container.layout.items[0][0].fixed_size
    assert 0 < width < 154
    assert 0 < height < 108
    assert preview_controls.multi_body_container.layout.items[0][0].visible is True
    assert preview_controls.multi_body_container.layout.items[0][0].alignment == _FakeQt.AlignCenter
    available_width = signing_shell_module._preview_available_width(
        widget.properties_panel.preview,
        container=preview_controls.container,
    )
    expected_width, expected_height = signing_shell_module._preview_body_size(
        widget.properties_panel.preview,
        available_width_px=available_width,
    )
    expected_padding = signing_shell_module._preview_card_padding_px(
        widget.properties_panel.preview
    )
    expected_inner_width = max(
        1,
        expected_width - int(round(expected_padding * 2)),
    )
    expected_inner_height = max(
        1,
        expected_height - int(round(expected_padding * 2)),
    )
    expected_title_height = preview_controls.title_label.sizeHint().height()
    expected_card_spacing = preview_controls.card_container.layout.spacing
    assert preview_controls.container.fixed_width is None
    assert preview_controls.card_container.fixed_size == (expected_width, expected_height)
    assert preview_controls.single_body_container.fixed_size == (
        expected_inner_width,
        expected_inner_height - expected_title_height - expected_card_spacing,
    )
    assert preview_controls.title_label.fixed_width == expected_width
    assert preview_controls.detail_label.fixed_width == expected_width
    assert preview_controls.multi_content_container.fixed_width <= expected_width
    assert preview_controls.multi_detail_label.fixed_width <= expected_width
    assert preview_controls.title_label.text() == "Digitally signed by"
    assert preview_controls.title_label.visible is True
    detail_text = preview_controls.multi_detail_label.text()
    detail_lines = detail_text.splitlines()
    assert detail_lines[0] == "Distinguished name: Distinguished name"
    assert detail_lines[1] == "Common name: Common name"
    assert detail_lines[2] == "Email: alice@example.com"
    assert detail_lines[3] == "Title: Director"
    assert detail_lines[4] == "Company: FoliaSeal"
    assert detail_lines[5].startswith("Signing time:")
    assert detail_lines[6] == "Reason: Approved"
    assert len(detail_lines) == 7
    assert preview_controls.footer_label.text() == ""
    assert len(preview_controls.card_container.layout.items) == 3
    assert preview_controls.card_container.layout.items[0][0] is preview_controls.title_label
    assert len(preview_controls.multi_content_container.layout.items) == 1
    assert preview_controls.multi_content_container.layout.items[0][0] is (
        preview_controls.multi_detail_label
    )
    assert (
        widget._signing_workspace.properties_panel._appearance_controls.font_family._items[:3]
        == ["Sans Serif", "Serif", "Monospace"]
    )
    assert (
        widget._signing_workspace.properties_panel._appearance_controls.font_family.currentText()
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
    widget.properties_panel.set_signature_rect(
        widget._signing_workspace._draft_workflow.update_signature_rect(
            page_index=0,
            left_pt=24.0,
            bottom_pt=18.0,
            width_pt=88.0,
            height_pt=28.0,
        )
    )

    preview_controls = widget.properties_panel.preview_controls

    available_width = signing_shell_module._preview_available_width(
        widget.properties_panel.preview,
        container=preview_controls.container,
    )
    expected_width, expected_height = signing_shell_module._preview_body_size(
        widget.properties_panel.preview,
        available_width_px=available_width,
    )
    expected_padding = signing_shell_module._preview_card_padding_px(
        widget.properties_panel.preview
    )
    expected_inner_width = max(
        1,
        expected_width - int(round(expected_padding * 2)),
    )
    expected_inner_height = max(
        1,
        expected_height - int(round(expected_padding * 2)),
    )
    expected_title_height = preview_controls.title_label.sizeHint().height()
    expected_card_spacing = preview_controls.card_container.layout.spacing
    assert preview_controls.container.fixed_width is None
    assert preview_controls.card_container.fixed_size == (expected_width, expected_height)
    assert preview_controls.single_body_container.fixed_size == (
        expected_inner_width,
        expected_inner_height - expected_title_height - expected_card_spacing,
    )
    assert preview_controls.title_label.fixed_width == expected_width
    assert preview_controls.detail_label.fixed_width == expected_width
    assert preview_controls.footer_label.fixed_width == expected_width
    assert preview_controls.multi_content_container.fixed_width <= expected_width
    assert preview_controls.multi_detail_label.fixed_width <= expected_width
    assert preview_controls.multi_body_container.visible is False
    assert preview_controls.single_body_container.visible is True
    assert preview_controls.title_label.visible is True
    assert preview_controls.title_label.text().startswith("A very long prefix")
    assert "A very long prefix" not in preview_controls.detail_label.text()
    assert len(preview_controls.single_body_container.layout.items) == 2
    assert preview_controls.single_body_container.layout.items[0][1] == (0, _FakeQt.AlignLeft)


def test_signing_shell_preview_available_width_uses_parent_width_not_stale_preview_width(
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
    preview_controls.container.fixed_width = 198

    available_width = signing_shell_module._preview_available_width(
        panel.preview,
        container=preview_controls.container,
    )

    assert available_width == 428


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
    panel.set_signature_rect(
        widget._signing_workspace._draft_workflow.update_signature_rect(
            page_index=0,
            left_pt=24.0,
            bottom_pt=18.0,
            width_pt=40.0,
            height_pt=20.0,
        )
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


def test_signing_shell_preview_available_width_uses_tightest_ancestor_width(
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

    panel.container._width_value = 638
    widget.properties_scroll._width_value = 550
    preview_controls.container.fixed_width = 622

    available_width = signing_shell_module._preview_available_width(
        panel.preview,
        container=preview_controls.container,
    )

    assert available_width == 498


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
    panel.set_signature_rect(
        widget._signing_workspace._draft_workflow.update_signature_rect(
            page_index=0,
            left_pt=35.0,
            bottom_pt=429.0,
            width_pt=260.0,
            height_pt=22.0,
        )
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
    widget.properties_panel.set_signature_rect(
        widget._signing_workspace._draft_workflow.update_signature_rect(
            page_index=0,
            left_pt=24.0,
            bottom_pt=18.0,
            width_pt=120.0,
            height_pt=60.0,
        )
    )

    preview_controls = widget.properties_panel.preview_controls

    assert preview_controls.single_body_container.visible is True
    assert preview_controls.multi_body_container.visible is False
    assert preview_controls.stamp_label.visible is True
    assert preview_controls.detail_label.visible is True
    assert " | " in widget.properties_panel.preview_text()


def test_signing_shell_stamp_position_right_places_stamp_to_the_right(
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
        stamp_position=SignatureStampPosition.RIGHT,
        image_stamp_path="/tmp/stamp.png",
    )
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
    )
    widget.properties_panel.set_signature_appearance(appearance)
    widget.properties_panel.set_signature_rect(
        widget._signing_workspace._draft_workflow.update_signature_rect(
            page_index=0,
            left_pt=24.0,
            bottom_pt=18.0,
            width_pt=120.0,
            height_pt=60.0,
        )
    )

    preview_controls = widget.properties_panel.preview_controls

    assert preview_controls.single_body_container.visible is False
    assert preview_controls.multi_body_container.visible is True
    assert preview_controls.multi_body_container.layout.items[0][0] is (
        preview_controls.multi_content_container
    )
    assert preview_controls.multi_body_container.layout.items[0][1] == (0, _FakeQt.AlignCenter)
    assert preview_controls.multi_body_container.layout.items[1][0] is (
        preview_controls.multi_stamp_label
    )
    assert preview_controls.multi_body_container.layout.items[1][1] == (0, _FakeQt.AlignCenter)
    assert preview_controls.multi_stamp_label.visible is True
    assert preview_controls.multi_detail_label.visible is True


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
    widget.properties_panel.set_signature_rect(
        widget._signing_workspace._draft_workflow.update_signature_rect(
            page_index=0,
            left_pt=24.0,
            bottom_pt=18.0,
            width_pt=120.0,
            height_pt=60.0,
        )
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

    assert (
        widget._signing_workspace._draft_workflow.signature_appearance.stamp_position
        == SignatureStampPosition.RIGHT
    )
    assert panel.preview.stamp_position == SignatureStampPosition.RIGHT
    assert "Stamp position: right" in signing_shell_module._format_appearance_summary(
        widget._signing_workspace._draft_workflow.signature_appearance
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
    widget.properties_panel.set_signature_rect(
        widget._signing_workspace._draft_workflow.update_signature_rect(
            page_index=0,
            left_pt=24.0,
            bottom_pt=18.0,
            width_pt=40.0,
            height_pt=20.0,
        )
    )

    assert "font-size: 6.5pt;" in widget.properties_panel.preview_controls.title_label.style
    assert "font-size: 6.5pt;" in widget.properties_panel.preview_controls.detail_label.style


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
    widget.properties_panel.set_signature_rect(
        widget._signing_workspace._draft_workflow.update_signature_rect(
            page_index=0,
            left_pt=24.0,
            bottom_pt=18.0,
            width_pt=40.0,
            height_pt=20.0,
        )
    )

    preview = widget.properties_panel.preview
    expected_detail_text = signing_shell_module._preview_detail_text(preview)
    assert widget.properties_panel._appearance_controls.show_field_names.isChecked() is False
    assert widget.properties_panel.preview_controls.title_label.text() == (preview.title or "")
    assert widget.properties_panel.preview_controls.title_label.visible is True
    assert widget.properties_panel.preview_controls.detail_label.text() == expected_detail_text


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

    signing_time_controls = widget.properties_panel.field_controls[
        SignatureFieldKey.SIGNING_TIME
    ]
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
    widget.properties_panel.set_signature_rect(
        widget._signing_workspace._draft_workflow.update_signature_rect(
            page_index=0,
            left_pt=24.0,
            bottom_pt=18.0,
            width_pt=40.0,
            height_pt=20.0,
        )
    )

    detail_lines = widget.properties_panel.preview_controls.multi_detail_label.text().splitlines()

    assert len(detail_lines) == 3
    assert detail_lines[0].startswith("Distinguished name:")
    assert detail_lines[1].startswith("Common name:")
    assert "Email: alice@example.com" in detail_lines[2]
    assert "Title: Director" in detail_lines[2]
    assert "Company: FoliaSeal" in detail_lines[2]
    assert "Signing time:" in detail_lines[2]
    assert "Reason: Approved" in detail_lines[2]


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
    widget.properties_panel.set_signature_rect(
        widget._signing_workspace._draft_workflow.update_signature_rect(
            page_index=0,
            left_pt=24.0,
            bottom_pt=18.0,
            width_pt=40.0,
            height_pt=20.0,
        )
    )

    detail_lines = widget.properties_panel.preview_controls.multi_detail_label.text().splitlines()

    assert len(detail_lines) == 3
    assert detail_lines[0] == "Distinguished name"
    assert detail_lines[1] == "Common name"
    assert "alice@example.com" in detail_lines[2]
    assert "Director" in detail_lines[2]
    assert "FoliaSeal" in detail_lines[2]
    assert "Approved" in detail_lines[2]
    assert "Email:" not in detail_lines[2]
    assert "Title:" not in detail_lines[2]
    assert "Company:" not in detail_lines[2]
    assert "Reason:" not in detail_lines[2]


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


def test_signing_shell_named_profile_save_and_reload_round_trip(
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
    widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
        preset_catalog_store=store,
    )

    panel = widget.properties_panel
    panel._profile_controls.profile_name.setText("My Profile")
    panel._appearance_controls.signer_label_prefix.setText("Signed by Me")
    panel._appearance_controls.show_field_names.setChecked(True)
    panel._placement_controls.width_spin.setValue(144.0)
    panel._placement_controls.height_spin.setValue(36.0)
    panel._profile_controls.save_button.click()

    assert panel._profile_catalog.profile_names()[-1] == "My Profile"
    assert panel._profile_controls.profile_combo.currentText() == "My Profile"
    assert panel._profile_controls.profile_name.text() == "My Profile"
    assert panel._profile_catalog.profile_named("My Profile").placement_defaults == (
        SignaturePlacementDefaults(
            width_pt=144.0,
            height_pt=36.0,
        )
    )

    panel._appearance_controls.signer_label_prefix.setText("Temporary Draft")
    assert panel._profile_controls.profile_combo.currentText() == "Current draft"

    panel._profile_controls.profile_combo.setCurrentText("My Profile")

    assert panel._appearance_controls.signer_label_prefix.text() == "Signed by Me"
    assert panel._appearance_controls.show_field_names.isChecked() is True
    assert panel._placement_controls.width_spin.value() == 144.0
    assert panel._placement_controls.height_spin.value() == 36.0

    relaunch_widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
        preset_catalog_store=store,
    )
    relaunch_panel = relaunch_widget.properties_panel

    assert relaunch_panel._profile_catalog.profile_names() == ("Default", "Compact", "My Profile")
    assert relaunch_panel._profile_controls.profile_combo.findText("My Profile") != -1
    assert relaunch_panel._profile_controls.profile_combo.currentText() == "Current draft"


def test_signing_shell_named_profile_save_without_name_reports_error(
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
    panel._profile_controls.profile_name.setText("")

    result = panel.save_current_profile()

    assert result is None
    assert errors == []
    assert store.load_catalog().profile_names() == ()
    assert fake_bindings.q_message_box.calls[-1][1:] == (
        "Profile error",
        "Profile name is required before saving.",
    )


def test_signing_shell_named_profile_selection_restores_placement_defaults_without_forcing_rect(
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
    assert widget._signing_workspace._draft_workflow.signature_rect is None

    panel._profile_controls.profile_combo.setCurrentText("Compact")

    assert panel._profile_controls.profile_name.text() == "Compact"
    assert panel._placement_controls.width_spin.value() == 144.0
    assert panel._placement_controls.height_spin.value() == 36.0
    assert widget._signing_workspace._draft_workflow.signature_rect is None


def test_signing_shell_named_profile_delete_can_be_canceled_and_keeps_profile(
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
    panel._profile_controls.profile_combo.setCurrentText("Compact")
    fake_bindings.q_message_box.next_result = fake_bindings.q_message_box.No

    result = panel.delete_current_profile()

    assert result is None
    assert store.load_catalog().profile_names() == ("Default", "Compact")
    assert panel._profile_controls.profile_combo.currentText() == "Compact"
    assert panel._profile_catalog.profile_names() == ("Default", "Compact")


def test_signing_shell_named_profile_delete_requires_confirmation_and_refreshes_catalog(
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
    panel._profile_controls.profile_combo.setCurrentText("Compact")
    fake_bindings.q_message_box.next_result = fake_bindings.q_message_box.Yes

    result = panel.delete_current_profile()

    assert result is not None
    assert result.profile_names() == ("Default",)
    assert store.load_catalog().profile_names() == ("Default",)
    assert panel._profile_controls.profile_combo.currentText() == "Current draft"
    assert panel._profile_catalog.profile_names() == ("Default",)
    assert panel._profile_controls.profile_combo.findText("Compact") == -1

    relaunched_widget = build_qt_signing_shell(
        viewer_workflow=_viewer_workflow(),
        signing_workflow=_workflow(tmp_path),
        preset_catalog_store=store,
    )
    relaunched_panel = relaunched_widget.properties_panel

    assert relaunched_panel._profile_catalog.profile_names() == ("Default",)
    assert relaunched_panel._profile_controls.profile_combo.findText("Compact") == -1


def test_signing_shell_named_profile_overwrite_requires_confirmation(
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
    panel._profile_controls.profile_name.setText("Team Standard")

    fake_bindings.q_message_box.next_result = fake_bindings.q_message_box.No
    result = panel.save_current_profile()

    assert result is None
    assert fake_bindings.q_message_box.calls
    assert panel._profile_catalog.profile_named("Team Standard").appearance == existing.appearance

    fake_bindings.q_message_box.next_result = fake_bindings.q_message_box.Yes
    result = panel.save_current_profile()

    assert result is not None
    assert result.name == "Team Standard"
    assert panel._profile_catalog.profile_named("Team Standard").appearance.signer_label_prefix == (
        "Signed by Current Draft"
    )
    assert panel._profile_controls.profile_combo.currentText() == "Team Standard"


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
    widget.properties_panel.set_signature_rect(
        widget._signing_workspace._draft_workflow.update_signature_rect(
            page_index=0,
            left_pt=24.0,
            bottom_pt=18.0,
            width_pt=40.0,
            height_pt=20.0,
        )
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
    assert widget._signing_workspace._sign_button._enabled is True
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
    assert widget._signing_workspace._sign_button._enabled is True


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
    widget.properties_panel.set_signature_rect(
        widget._signing_workspace._draft_workflow.update_signature_rect(
            page_index=0,
            left_pt=24.0,
            bottom_pt=18.0,
            width_pt=40.0,
            height_pt=20.0,
        )
    )

    preview = widget.properties_panel.preview
    expected = signing_shell_module._preview_detail_text(preview)
    assert widget.properties_panel.preview_controls.title_label.text() == (preview.title or "")
    assert widget.properties_panel.preview_controls.title_label.visible is True
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
    widget.properties_panel.set_signature_rect(
        widget._signing_workspace._draft_workflow.update_signature_rect(
            page_index=0,
            left_pt=24.0,
            bottom_pt=18.0,
            width_pt=180.0,
            height_pt=36.0,
        )
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
    widget.properties_panel.set_signature_rect(
        widget._signing_workspace._draft_workflow.update_signature_rect(
            page_index=0,
            left_pt=24.0,
            bottom_pt=18.0,
            width_pt=180.0,
            height_pt=36.0,
        )
    )

    preview = widget.properties_panel.preview
    expected = signing_shell_module._preview_detail_text(preview)
    available_width = signing_shell_module._preview_available_width(
        preview,
        container=widget.properties_panel.preview_controls.container,
    )

    assert widget.properties_panel.preview_controls.multi_detail_label.text() == expected
    assert widget.properties_panel.preview_controls.multi_content_container.fixed_width == (
        signing_shell_module._preview_text_width_limit(
            preview,
            title_line=preview.signer_label_prefix or preview.title,
            detail_text=expected,
            available_width_px=available_width,
        )
    )


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
        widget.properties_panel.set_signature_rect(
            widget._signing_workspace._draft_workflow.update_signature_rect(
                page_index=0,
                left_pt=24.0,
                bottom_pt=18.0,
                width_pt=180.0,
                height_pt=36.0,
            )
        )

        assert (
            widget.properties_panel.preview_controls.multi_body_container.layout.items[
                0 if stamp_position == SignatureStampPosition.LEFT else 1
            ][0].alignment
            == _FakeQt.AlignCenter
        )


def test_fit_vertical_preview_band_geometry_prefers_text_hint_and_reduces_separator() -> None:
    fitted = signing_shell_module._fit_vertical_preview_band_geometry(
        text_height=15,
        stamp_height=13,
        separator_height=10,
        inner_body_height_px=38,
        detail_hint_height_px=30,
        stamp_visible=True,
    )

    assert fitted == (17, 21, 0)


def test_fit_vertical_preview_band_geometry_preserves_band_split_when_roomy() -> None:
    fitted = signing_shell_module._fit_vertical_preview_band_geometry(
        text_height=18,
        stamp_height=16,
        separator_height=6,
        inner_body_height_px=56,
        detail_hint_height_px=16,
        stamp_visible=True,
    )

    assert fitted == (18, 32, 6)


def test_reset_widget_size_constraints_clears_fake_geometry() -> None:
    label = _FakeLabel("Preview")
    label.fixed_size = (140, 32)
    label.fixed_width = 140
    label.maximum_width = 140
    label.minimum_width = 80

    signing_shell_module._reset_widget_size_constraints(label)

    assert label.fixed_size is None
    assert label.fixed_width is None
    assert label.maximum_width is None
    assert label.minimum_width is None


def test_signing_shell_horizontal_preview_reduces_text_width_for_thick_borders(
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
    widget.properties_panel.set_signature_rect(
        widget._signing_workspace._draft_workflow.update_signature_rect(
            page_index=0,
            left_pt=24.0,
            bottom_pt=18.0,
            width_pt=180.0,
            height_pt=36.0,
        )
    )

    preview = widget.properties_panel.preview
    detail = widget.properties_panel.preview_controls.multi_detail_label.text()
    available_width = signing_shell_module._preview_available_width(
        preview,
        container=widget.properties_panel.preview_controls.container,
    )

    default_width = signing_shell_module._preview_text_width_limit(
        preview,
        title_line=preview.signer_label_prefix or preview.title,
        detail_text=detail,
        available_width_px=available_width,
    )
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

    thick_preview = widget.properties_panel.preview
    thick_detail = widget.properties_panel.preview_controls.multi_detail_label.text()
    thick_available_width = signing_shell_module._preview_available_width(
        thick_preview,
        container=widget.properties_panel.preview_controls.container,
    )
    thick_width = signing_shell_module._preview_text_width_limit(
        thick_preview,
        title_line=thick_preview.signer_label_prefix or thick_preview.title,
        detail_text=thick_detail,
        available_width_px=thick_available_width,
    )

    assert thick_width < default_width
    assert (
        widget.properties_panel.preview_controls.multi_content_container.fixed_width == thick_width
    )


def test_signing_shell_preview_uses_border_aware_padding_for_thick_borders(
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
    widget.properties_panel.set_signature_rect(
        widget._signing_workspace._draft_workflow.update_signature_rect(
            page_index=0,
            left_pt=24.0,
            bottom_pt=18.0,
            width_pt=180.0,
            height_pt=28.0,
        )
    )

    expected_padding = signing_shell_module._preview_card_padding_px(
        widget.properties_panel.preview
    )

    assert (
        f"padding: {expected_padding:.1f}px;"
        in widget.properties_panel.preview_controls.card_container.style
    )
