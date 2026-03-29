"""Minimal Qt preview widget wiring for Phase 2 viewer interactions."""

from __future__ import annotations

import importlib
from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter
from typing import Any

from foliaseal.application.coordinate_transform import (
    PdfRect,
    ViewRect,
    ViewTransform,
    pdf_rect_to_view_rect,
)
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.domain.models import SignatureRect


class QtViewerBindingsUnavailable(RuntimeError):
    """Raised when PySide6 widget bindings are unavailable."""


@dataclass(frozen=True)
class QtWidgetBindings:
    """Dynamically imported PySide6 symbols used by the widget."""

    q_widget: type[Any]
    q_scroll_area: type[Any]
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
        on_interaction: Callable[[str], None] | None = None,
    ) -> Any:
        bindings = self._bindings

        class PdfPreviewWidget(bindings.q_widget):  # type: ignore[misc,valid-type]
            def __init__(self) -> None:
                super().__init__()
                self._workflow = workflow
                self._on_selection = on_selection
                self._on_error = on_error
                self._on_interaction = on_interaction
                self._pixmap: Any | None = None
                self._scroll_container: Any | None = None
                self._drag_origin: Any | None = None
                self._selection_rect: Any | None = None
                self._pan_origin: Any | None = None
                self._pan_start_x = 0
                self._pan_start_y = 0
                self._overlay_signature_rect: SignatureRect | None = None
                self._overlay_drag_handle: str | None = None
                self._overlay_drag_view_rect: ViewRect | None = None
                self._overlay_drag_start_view_rect: ViewRect | None = None
                self._overlay_handle_half_size = 4.0
                self._overlay_min_span_px = 8.0

            def refresh(self, *, elapsed_ms: float | None = None, navigation: bool = False) -> None:
                start_time = perf_counter() if elapsed_ms is None else None
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
                if start_time is not None:
                    measured_ms = (perf_counter() - start_time) * 1000.0
                    self._record_timing(measured_ms=measured_ms, navigation=navigation)
                self._apply_render_result(result)

            def paintEvent(self, event: Any) -> None:  # noqa: N802 (Qt API name)
                painter = bindings.q_painter(self)
                if self._pixmap is not None:
                    painter.drawPixmap(0, 0, self._pixmap)

                if self._selection_rect is not None:
                    painter.setPen(bindings.q_pen(bindings.q_color(0, 153, 255), 2))
                    painter.drawRect(self._selection_rect.normalized())

                overlay_rect = self._current_overlay_qrect()
                if overlay_rect is not None:
                    self._draw_overlay(painter, overlay_rect)

                painter.end()
                super().paintEvent(event)

            def wheelEvent(self, event: Any) -> None:  # noqa: N802 (Qt API name)
                delta = event.angleDelta().y()
                if delta > 0:
                    self._emit_interaction("wheel_zoom_in")
                    self._workflow.zoom_in()
                elif delta < 0:
                    self._emit_interaction("wheel_zoom_out")
                    self._workflow.zoom_out()
                self.refresh(navigation=False)
                event.accept()

            def keyPressEvent(self, event: Any) -> None:  # noqa: N802 (Qt API name)
                key = event.key()

                if key in (
                    bindings.qt.Key_Plus,
                    bindings.qt.Key_Equal,
                ):
                    self._emit_interaction("key_zoom_in")
                    self._workflow.zoom_in()
                    self.refresh(navigation=False)
                    event.accept()
                    return

                if key in (
                    bindings.qt.Key_Minus,
                    bindings.qt.Key_Underscore,
                ):
                    self._emit_interaction("key_zoom_out")
                    self._workflow.zoom_out()
                    self.refresh(navigation=False)
                    event.accept()
                    return

                if key == bindings.qt.Key_0:
                    self._emit_interaction("key_zoom_reset")
                    self._workflow.reset_zoom()
                    self.refresh(navigation=False)
                    event.accept()
                    return

                if key in (
                    bindings.qt.Key_PageDown,
                    bindings.qt.Key_Down,
                    bindings.qt.Key_Right,
                ):
                    self._emit_interaction("key_page_next")
                    self._navigate(
                        action=self._workflow.go_next_page,
                        summary=(
                            "Unable to render PDF preview after navigating to the next page. "
                            "Please verify PDF backend availability and retry."
                        ),
                    )
                    event.accept()
                    return

                if key in (
                    bindings.qt.Key_PageUp,
                    bindings.qt.Key_Up,
                    bindings.qt.Key_Left,
                ):
                    self._emit_interaction("key_page_previous")
                    self._navigate(
                        action=self._workflow.go_previous_page,
                        summary=(
                            "Unable to render PDF preview after navigating to the previous page. "
                            "Please verify PDF backend availability and retry."
                        ),
                    )
                    event.accept()
                    return

                if key == bindings.qt.Key_Home:
                    self._emit_interaction("key_jump_home")
                    self._navigate(
                        action=lambda: self._workflow.jump_to_page(0),
                        summary=(
                            "Unable to render PDF preview after jumping to the first page. "
                            "Please verify PDF backend availability and retry."
                        ),
                    )
                    event.accept()
                    return

                if key == bindings.qt.Key_End:
                    self._emit_interaction("key_jump_end")
                    self._navigate(
                        action=lambda: self._workflow.jump_to_page(
                            self._workflow.session.page_count - 1
                        ),
                        summary=(
                            "Unable to render PDF preview after jumping to the last page. "
                            "Please verify PDF backend availability and retry."
                        ),
                    )
                    event.accept()
                    return

                super().keyPressEvent(event)

            def mousePressEvent(self, event: Any) -> None:  # noqa: N802 (Qt API name)
                if self._is_pan_press(event):
                    if self._scroll_container is None:
                        return super().mousePressEvent(event)
                    self._pan_origin = event.position().toPoint()
                    self._pan_start_x = self._horizontal_scroll_bar().value()
                    self._pan_start_y = self._vertical_scroll_bar().value()
                    self.grabMouse()
                    event.accept()
                    return
                if event.button() != bindings.qt.LeftButton:
                    return super().mousePressEvent(event)
                point = event.position()
                overlay_rect = self._current_overlay_view_rect()
                if overlay_rect is not None:
                    handle = self._hit_test_overlay_handle(overlay_rect, point)
                    if handle is not None:
                        self._overlay_drag_handle = handle
                        self._overlay_drag_start_view_rect = overlay_rect
                        self._overlay_drag_view_rect = self._overlay_resize_view_rect(
                            overlay_rect=overlay_rect,
                            handle=handle,
                            current_x=float(point.x()),
                            current_y=float(point.y()),
                        )
                        self._selection_rect = None
                        self.grabMouse()
                        self.update()
                        event.accept()
                        return
                self._drag_origin = point
                self._selection_rect = bindings.q_rect(self._drag_origin, self._drag_origin)
                self.update()

            def mouseMoveEvent(self, event: Any) -> None:  # noqa: N802 (Qt API name)
                if self._pan_origin is not None:
                    current = event.position().toPoint()
                    delta_x = current.x() - self._pan_origin.x()
                    delta_y = current.y() - self._pan_origin.y()
                    self._horizontal_scroll_bar().setValue(self._pan_start_x - delta_x)
                    self._vertical_scroll_bar().setValue(self._pan_start_y - delta_y)
                    self._sync_pan_from_scrollbars()
                    event.accept()
                    return
                if self._overlay_drag_handle is not None:
                    current = event.position()
                    if self._overlay_drag_start_view_rect is None:
                        return super().mouseMoveEvent(event)
                    self._overlay_drag_view_rect = self._overlay_resize_view_rect(
                        overlay_rect=self._overlay_drag_start_view_rect,
                        handle=self._overlay_drag_handle,
                        current_x=float(current.x()),
                        current_y=float(current.y()),
                    )
                    self._selection_rect = None
                    self.update()
                    event.accept()
                    return
                if self._drag_origin is None:
                    return super().mouseMoveEvent(event)
                current = event.position().toPoint()
                self._selection_rect = bindings.q_rect(self._drag_origin, current)
                self.update()

            def mouseReleaseEvent(self, event: Any) -> None:  # noqa: N802 (Qt API name)
                if self._pan_origin is not None and self._is_pan_release(event):
                    self._pan_origin = None
                    self.releaseMouse()
                    event.accept()
                    return
                if (
                    self._overlay_drag_handle is not None
                    and event.button() == bindings.qt.LeftButton
                ):
                    current = event.position()
                    if self._overlay_drag_start_view_rect is None:
                        self._reset_overlay_drag_state()
                        event.accept()
                        return
                    self._overlay_drag_view_rect = self._overlay_resize_view_rect(
                        overlay_rect=self._overlay_drag_start_view_rect,
                        handle=self._overlay_drag_handle,
                        current_x=float(current.x()),
                        current_y=float(current.y()),
                    )
                    self._apply_overlay_drag_selection()
                    self._reset_overlay_drag_state()
                    event.accept()
                    return
                if self._drag_origin is None or event.button() != bindings.qt.LeftButton:
                    return super().mouseReleaseEvent(event)

                current = event.position().toPoint()
                if not self._is_selection_drag(self._drag_origin, current):
                    self._selection_rect = None
                    self._drag_origin = None
                    self.update()
                    event.accept()
                    return
                rect = bindings.q_rect(self._drag_origin, current).normalized()
                self._selection_rect = None
                self._drag_origin = None

                try:
                    self._sync_pan_from_scrollbars()
                    selection = self._selection_in_viewport_coords(rect)
                    pdf_rect = self._workflow.selection_to_pdf_rect(
                        selection=selection
                    )
                except (RuntimeError, ValueError) as exc:
                    self._emit_interaction("selection_error")
                    self._emit_error(
                        "Selection could not be placed on the PDF page. "
                        "Please keep the selection inside page bounds.",
                        exc,
                    )
                    self.update()
                    return
                if self._on_selection is not None:
                    self._emit_interaction("selection_success")
                    self._on_selection(pdf_rect)
                self.update()

            def set_signature_overlay(self, signature_rect: SignatureRect | None) -> None:
                self._overlay_signature_rect = signature_rect
                self.update()

            def clear_signature_overlay(self) -> None:
                self._overlay_signature_rect = None
                self.update()

            def attach_scroll_container(self, scroll_container: Any) -> None:
                self._scroll_container = scroll_container
                self._sync_pan_from_scrollbars()

            def hideEvent(self, event: Any) -> None:  # noqa: N802 (Qt API name)
                if self._pan_origin is not None:
                    self._pan_origin = None
                    self.releaseMouse()
                super().hideEvent(event)

            def _emit_error(self, summary: str, exc: Exception | None = None) -> None:
                if self._on_error is not None:
                    if exc is None:
                        self._on_error(summary)
                        return
                    self._on_error(f"{summary} (details: {exc})")

            def _apply_render_result(self, result: Any) -> None:
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

            def _navigate(self, *, action: Callable[[], Any], summary: str) -> None:
                start_time = perf_counter()
                try:
                    result = action()
                except Exception as exc:  # pragma: no cover - integration behavior
                    self._emit_error(summary, exc)
                    if self._on_error is None:
                        raise
                    return
                measured_ms = (perf_counter() - start_time) * 1000.0
                self._record_timing(measured_ms=measured_ms, navigation=True)
                self._apply_render_result(result)

            def go_to_next_page(self) -> None:
                self._navigate(
                    action=self._workflow.go_next_page,
                    summary=(
                        "Unable to render PDF preview after navigating to the next page. "
                        "Please verify PDF backend availability and retry."
                    ),
                )

            def go_to_previous_page(self) -> None:
                self._navigate(
                    action=self._workflow.go_previous_page,
                    summary=(
                        "Unable to render PDF preview after navigating to the previous page. "
                        "Please verify PDF backend availability and retry."
                    ),
                )

            def reset_zoom_view(self) -> None:
                self._workflow.reset_zoom()
                self.refresh(navigation=False)

            def _horizontal_scroll_bar(self) -> Any:
                if self._scroll_container is None:
                    raise RuntimeError("Scroll container is not attached.")
                return self._scroll_container.horizontalScrollBar()

            def _vertical_scroll_bar(self) -> Any:
                if self._scroll_container is None:
                    raise RuntimeError("Scroll container is not attached.")
                return self._scroll_container.verticalScrollBar()

            def _is_pan_press(self, event: Any) -> bool:
                return event.button() == bindings.qt.MiddleButton or (
                    event.button() == bindings.qt.LeftButton
                    and self._has_shift_modifier(event)
                )

            def _is_pan_release(self, event: Any) -> bool:
                return event.button() in (
                    bindings.qt.MiddleButton,
                    bindings.qt.LeftButton,
                )

            def _has_shift_modifier(self, event: Any) -> bool:
                modifiers = event.modifiers()
                shift_mask = bindings.qt.KeyboardModifier.ShiftModifier
                return bool(modifiers & shift_mask)

            @staticmethod
            def _is_selection_drag(origin: Any, current: Any) -> bool:
                return origin.x() != current.x() or origin.y() != current.y()

            def _selection_in_viewport_coords(self, rect: Any) -> ViewRect:
                pan_x, pan_y = self._current_pan_offsets()
                return ViewRect(
                    x1=float(rect.left()) - pan_x,
                    y1=float(rect.top()) - pan_y,
                    x2=float(rect.right()) - pan_x,
                    y2=float(rect.bottom()) - pan_y,
                )

            def _sync_pan_from_scrollbars(self) -> None:
                setter = getattr(self._workflow, "set_pan", None)
                if not callable(setter):
                    return
                pan_x, pan_y = self._current_pan_offsets()
                setter(pan_x=-pan_x, pan_y=-pan_y)

            def _current_pan_offsets(self) -> tuple[float, float]:
                if self._scroll_container is None:
                    return 0.0, 0.0
                return (
                    float(self._horizontal_scroll_bar().value()),
                    float(self._vertical_scroll_bar().value()),
                )

            def _current_overlay_qrect(self) -> Any | None:
                view_rect = self._overlay_drag_view_rect or self._current_overlay_view_rect()
                if view_rect is None:
                    return None
                return bindings.q_rect(
                    bindings.q_point(int(view_rect.x1), int(view_rect.y1)),
                    bindings.q_point(int(view_rect.x2), int(view_rect.y2)),
                )

            def _current_page_view_bounds(self) -> ViewRect | None:
                snapshot = getattr(self._workflow, "snapshot", None)
                if snapshot is None:
                    return None
                return pdf_rect_to_view_rect(
                    pdf_rect=PdfRect(
                        x1=snapshot.page_box.left,
                        y1=snapshot.page_box.bottom,
                        x2=snapshot.page_box.right,
                        y2=snapshot.page_box.top,
                    ),
                    transform=ViewTransform(
                        zoom=snapshot.zoom,
                        pan_x=snapshot.pan_x,
                        pan_y=snapshot.pan_y,
                    ),
                    page_box=snapshot.page_box,
                    rotation=snapshot.rotation,
                )

            def _current_overlay_view_rect(self) -> ViewRect | None:
                overlay = self._overlay_signature_rect
                snapshot = getattr(self._workflow, "snapshot", None)
                if overlay is None or snapshot is None:
                    return None
                if overlay.page_index != snapshot.page_index:
                    return None
                pdf_rect = PdfRect(
                    x1=overlay.left_pt,
                    y1=overlay.bottom_pt,
                    x2=overlay.left_pt + overlay.width_pt,
                    y2=overlay.bottom_pt + overlay.height_pt,
                )
                return pdf_rect_to_view_rect(
                    pdf_rect=pdf_rect,
                    transform=ViewTransform(
                        zoom=snapshot.zoom,
                        pan_x=snapshot.pan_x,
                        pan_y=snapshot.pan_y,
                    ),
                    page_box=snapshot.page_box,
                    rotation=snapshot.rotation,
                )

            def _draw_overlay(self, painter: Any, overlay_rect: Any) -> None:
                painter.setPen(bindings.q_pen(bindings.q_color(255, 102, 0), 2))
                painter.drawRect(overlay_rect.normalized())
                for handle_point in self._overlay_handle_points(overlay_rect):
                    painter.drawRect(
                        bindings.q_rect(
                            bindings.q_point(
                                int(handle_point.x() - self._overlay_handle_half_size),
                                int(handle_point.y() - self._overlay_handle_half_size),
                            ),
                            bindings.q_point(
                                int(handle_point.x() + self._overlay_handle_half_size),
                                int(handle_point.y() + self._overlay_handle_half_size),
                            ),
                        )
                    )

            def _overlay_handle_points(self, overlay_rect: ViewRect) -> tuple[Any, ...]:
                return (
                    bindings.q_point(int(overlay_rect.x1), int(overlay_rect.y1)),
                    bindings.q_point(int(overlay_rect.x2), int(overlay_rect.y1)),
                    bindings.q_point(int(overlay_rect.x1), int(overlay_rect.y2)),
                    bindings.q_point(int(overlay_rect.x2), int(overlay_rect.y2)),
                )

            def _hit_test_overlay_handle(
                self,
                overlay_rect: ViewRect,
                point: Any,
            ) -> str | None:
                half_size = self._overlay_handle_half_size
                handle_targets = {
                    "top_left": (overlay_rect.x1, overlay_rect.y1),
                    "top_right": (overlay_rect.x2, overlay_rect.y1),
                    "bottom_left": (overlay_rect.x1, overlay_rect.y2),
                    "bottom_right": (overlay_rect.x2, overlay_rect.y2),
                }
                for handle_name, (x_coord, y_coord) in handle_targets.items():
                    if abs(float(point.x()) - float(x_coord)) <= half_size and abs(
                        float(point.y()) - float(y_coord)
                    ) <= half_size:
                        return handle_name
                return None

            def _overlay_resize_view_rect(
                self,
                *,
                overlay_rect: ViewRect,
                handle: str,
                current_x: float,
                current_y: float,
            ) -> ViewRect:
                left = float(overlay_rect.x1)
                right = float(overlay_rect.x2)
                top = float(overlay_rect.y1)
                bottom = float(overlay_rect.y2)
                page_bounds = self._current_page_view_bounds()
                if page_bounds is not None:
                    min_x = min(page_bounds.x1, page_bounds.x2)
                    max_x = max(page_bounds.x1, page_bounds.x2)
                    min_y = min(page_bounds.y1, page_bounds.y2)
                    max_y = max(page_bounds.y1, page_bounds.y2)
                    current_x = min(max(current_x, min_x), max_x)
                    current_y = min(max(current_y, min_y), max_y)
                min_span = self._overlay_min_span_px

                if handle == "top_left":
                    left = min(current_x, right - min_span)
                    top = min(current_y, bottom - min_span)
                elif handle == "top_right":
                    right = max(current_x, left + min_span)
                    top = min(current_y, bottom - min_span)
                elif handle == "bottom_left":
                    left = min(current_x, right - min_span)
                    bottom = max(current_y, top + min_span)
                elif handle == "bottom_right":
                    right = max(current_x, left + min_span)
                    bottom = max(current_y, top + min_span)
                return ViewRect(x1=left, y1=top, x2=right, y2=bottom)

            def _apply_overlay_drag_selection(self) -> None:
                if self._overlay_drag_view_rect is None:
                    return
                try:
                    pdf_rect = self._workflow.selection_to_pdf_rect(
                        selection=self._overlay_drag_view_rect
                    )
                except (RuntimeError, ValueError) as exc:
                    self._emit_interaction("selection_error")
                    self._emit_error(
                        "Selection could not be placed on the PDF page. "
                        "Please keep the selection inside page bounds.",
                        exc,
                    )
                    self.update()
                    return
                if self._on_selection is not None:
                    self._emit_interaction("selection_success")
                    self._on_selection(pdf_rect)
                self.update()

            def _reset_overlay_drag_state(self) -> None:
                self._overlay_drag_handle = None
                self._overlay_drag_view_rect = None
                self._overlay_drag_start_view_rect = None
                self._selection_rect = None
                self.releaseMouse()
                self.update()

            def _record_timing(self, *, measured_ms: float, navigation: bool) -> None:
                tracker = getattr(self._workflow, "timing_tracker", None)
                if tracker is None:
                    return
                if navigation:
                    tracker.record_navigation(measured_ms)
                else:
                    tracker.record_first_render(measured_ms)

            def _emit_interaction(self, name: str) -> None:
                if self._on_interaction is not None:
                    self._on_interaction(name)

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
            q_scroll_area=getattr(qt_widgets, "QScrollArea"),
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
    on_interaction: Callable[[str], None] | None = None,
) -> Any:
    """Build a QWidget instance wired to the application viewer workflow."""

    adapter = PdfViewerWidgetAdapter()
    preview_widget = adapter.create(
        workflow=workflow,
        on_selection=on_selection,
        on_error=on_error,
        on_interaction=on_interaction,
    )

    class ScrollablePdfViewer(adapter._bindings.q_scroll_area):  # type: ignore[misc,valid-type]
        def __init__(self) -> None:
            super().__init__()
            self.setWidget(preview_widget)
            self.setWidgetResizable(False)
            self.setFocusProxy(preview_widget)
            preview_widget.attach_scroll_container(self)

        def refresh(self, *, elapsed_ms: float | None = None, navigation: bool = False) -> None:
            preview_widget.refresh(elapsed_ms=elapsed_ms, navigation=navigation)

        def go_to_next_page(self) -> None:
            preview_widget.go_to_next_page()

        def go_to_previous_page(self) -> None:
            preview_widget.go_to_previous_page()

        def reset_zoom_view(self) -> None:
            preview_widget.reset_zoom_view()

        def set_signature_overlay(self, signature_rect: SignatureRect | None) -> None:
            preview_widget.set_signature_overlay(signature_rect)

        def clear_signature_overlay(self) -> None:
            preview_widget.clear_signature_overlay()

    return ScrollablePdfViewer()
