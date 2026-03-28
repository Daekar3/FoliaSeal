"""Minimal Qt preview widget wiring for Phase 2 viewer interactions."""

from __future__ import annotations

import importlib
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pdf_signer.application.coordinate_transform import ViewRect
from pdf_signer.application.viewer_workflow import ViewerWorkflow


class QtViewerBindingsUnavailable(RuntimeError):
    """Raised when PySide6 widget bindings are unavailable."""


@dataclass(frozen=True)
class QtWidgetBindings:
    """Dynamically imported PySide6 symbols used by the widget."""

    q_widget: type[Any]
    q_painter: type[Any]
    q_color: type[Any]
    q_pen: type[Any]
    q_pixmap: type[Any]
    q_image: type[Any]
    q_rect: type[Any]
    q_point: type[Any]
    qt: Any


class PdfViewerWidgetAdapter:
    """Factory wrapper that builds a concrete QWidget subclass lazily."""

    def __init__(self) -> None:
        self._bindings = self._load_bindings()

    def create(
        self,
        *,
        workflow: ViewerWorkflow,
        on_selection: Callable[[object], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ) -> Any:
        bindings = self._bindings

        class PdfPreviewWidget(bindings.q_widget):  # type: ignore[misc,valid-type]
            def __init__(self) -> None:
                super().__init__()
                self._workflow = workflow
                self._on_selection = on_selection
                self._on_error = on_error
                self._pixmap: Any | None = None
                self._drag_origin: Any | None = None
                self._selection_rect: Any | None = None

            def refresh(self, *, elapsed_ms: float | None = None, navigation: bool = False) -> None:
                try:
                    result = self._workflow.render_current_page(
                        elapsed_ms=elapsed_ms,
                        navigation=navigation,
                    )
                except Exception as exc:  # pragma: no cover - integration behavior
                    self._emit_error(
                        "Unable to render PDF preview. "
                        "Please verify PDF backend availability and retry.",
                        exc,
                    )
                    if self._on_error is None:
                        raise
                    return
                image = bindings.q_image(
                    result.rgba_bytes,
                    result.width_px,
                    result.height_px,
                    result.width_px * 4,
                    bindings.q_image.Format_RGBA8888,
                )
                self._pixmap = bindings.q_pixmap.fromImage(image.copy())
                self.setMinimumSize(result.width_px, result.height_px)
                self.update()

            def paintEvent(self, event: Any) -> None:  # noqa: N802 (Qt API name)
                painter = bindings.q_painter(self)
                if self._pixmap is not None:
                    painter.drawPixmap(0, 0, self._pixmap)

                if self._selection_rect is not None:
                    painter.setPen(bindings.q_pen(bindings.q_color(0, 153, 255), 2))
                    painter.drawRect(self._selection_rect.normalized())

                painter.end()
                super().paintEvent(event)

            def wheelEvent(self, event: Any) -> None:  # noqa: N802 (Qt API name)
                delta = event.angleDelta().y()
                if delta > 0:
                    self._workflow.zoom_in()
                elif delta < 0:
                    self._workflow.zoom_out()
                self.refresh(navigation=False)
                event.accept()

            def keyPressEvent(self, event: Any) -> None:  # noqa: N802 (Qt API name)
                key = event.key()

                if key in (
                    bindings.qt.Key_Plus,
                    bindings.qt.Key_Equal,
                ):
                    self._workflow.zoom_in()
                    self.refresh(navigation=False)
                    event.accept()
                    return

                if key in (
                    bindings.qt.Key_Minus,
                    bindings.qt.Key_Underscore,
                ):
                    self._workflow.zoom_out()
                    self.refresh(navigation=False)
                    event.accept()
                    return

                if key == bindings.qt.Key_0:
                    self._workflow.reset_zoom()
                    self.refresh(navigation=False)
                    event.accept()
                    return

                if key in (
                    bindings.qt.Key_PageDown,
                    bindings.qt.Key_Down,
                    bindings.qt.Key_Right,
                ):
                    self._workflow.go_next_page()
                    self.refresh(navigation=True)
                    event.accept()
                    return

                if key in (
                    bindings.qt.Key_PageUp,
                    bindings.qt.Key_Up,
                    bindings.qt.Key_Left,
                ):
                    self._workflow.go_previous_page()
                    self.refresh(navigation=True)
                    event.accept()
                    return

                if key == bindings.qt.Key_Home:
                    self._workflow.jump_to_page(0)
                    self.refresh(navigation=True)
                    event.accept()
                    return

                if key == bindings.qt.Key_End:
                    self._workflow.jump_to_page(self._workflow.session.page_count - 1)
                    self.refresh(navigation=True)
                    event.accept()
                    return

                super().keyPressEvent(event)

            def mousePressEvent(self, event: Any) -> None:  # noqa: N802 (Qt API name)
                if event.button() != bindings.qt.LeftButton:
                    return super().mousePressEvent(event)
                self._drag_origin = event.position().toPoint()
                self._selection_rect = bindings.q_rect(self._drag_origin, self._drag_origin)
                self.update()

            def mouseMoveEvent(self, event: Any) -> None:  # noqa: N802 (Qt API name)
                if self._drag_origin is None:
                    return super().mouseMoveEvent(event)
                current = event.position().toPoint()
                self._selection_rect = bindings.q_rect(self._drag_origin, current)
                self.update()

            def mouseReleaseEvent(self, event: Any) -> None:  # noqa: N802 (Qt API name)
                if self._drag_origin is None or event.button() != bindings.qt.LeftButton:
                    return super().mouseReleaseEvent(event)

                current = event.position().toPoint()
                rect = bindings.q_rect(self._drag_origin, current).normalized()
                self._selection_rect = None
                self._drag_origin = None

                try:
                    pdf_rect = self._workflow.selection_to_pdf_rect(
                        selection=ViewRect(
                            x1=float(rect.left()),
                            y1=float(rect.top()),
                            x2=float(rect.right()),
                            y2=float(rect.bottom()),
                        )
                    )
                except (RuntimeError, ValueError) as exc:
                    self._emit_error(
                        "Selection could not be placed on the PDF page. "
                        "Please keep the selection inside page bounds.",
                        exc,
                    )
                    self.update()
                    return
                if self._on_selection is not None:
                    self._on_selection(pdf_rect)
                self.update()

            def _emit_error(self, summary: str, exc: Exception | None = None) -> None:
                if self._on_error is not None:
                    if exc is None:
                        self._on_error(summary)
                        return
                    self._on_error(f"{summary} (details: {exc})")

        return PdfPreviewWidget()

    def _load_bindings(self) -> QtWidgetBindings:
        try:
            qt_widgets = importlib.import_module("PySide6.QtWidgets")
            qt_gui = importlib.import_module("PySide6.QtGui")
            qt_core = importlib.import_module("PySide6.QtCore")
        except Exception as exc:  # pragma: no cover - environment dependent
            raise QtViewerBindingsUnavailable(
                "PySide6 QtWidgets/QtGui/QtCore are required for the Qt preview widget. "
                f"Details: {exc}"
            ) from exc

        return QtWidgetBindings(
            q_widget=getattr(qt_widgets, "QWidget"),
            q_painter=getattr(qt_gui, "QPainter"),
            q_color=getattr(qt_gui, "QColor"),
            q_pen=getattr(qt_gui, "QPen"),
            q_pixmap=getattr(qt_gui, "QPixmap"),
            q_image=getattr(qt_gui, "QImage"),
            q_rect=getattr(qt_core, "QRect"),
            q_point=getattr(qt_core, "QPoint"),
            qt=getattr(qt_core, "Qt"),
        )


def build_qt_pdf_viewer_widget(
    *,
    workflow: ViewerWorkflow,
    on_selection: Callable[[object], None] | None = None,
    on_error: Callable[[str], None] | None = None,
) -> Any:
    """Build a QWidget instance wired to the application viewer workflow."""

    return PdfViewerWidgetAdapter().create(
        workflow=workflow,
        on_selection=on_selection,
        on_error=on_error,
    )
