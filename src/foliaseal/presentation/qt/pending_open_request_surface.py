"""Condition-only app-chrome surface for a deferred PDF open request."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any


class PendingOpenRequestSurface:
    """Show the newest queued PDF and let the user discard that request."""

    def __init__(
        self,
        *,
        bindings: Any,
        parent: Any,
        on_cancel: Callable[[], Any],
    ) -> None:
        status_bar_type = getattr(bindings, "q_status_bar", None)
        if status_bar_type is None:
            raise RuntimeError("The pending-open surface requires QStatusBar bindings.")
        self.status_bar = status_bar_type(parent)
        self.status_bar.setSizeGripEnabled(False)
        widget_type = getattr(bindings, "q_widget", None)
        if widget_type is None:
            raise RuntimeError("The pending-open surface requires QWidget bindings.")
        self.container = widget_type(self.status_bar)
        layout_type = getattr(bindings, "q_hbox_layout", None)
        if layout_type is None:
            raise RuntimeError("The pending-open surface requires QHBoxLayout bindings.")
        layout = layout_type(self.container)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(8)

        self.filename_label = bindings.q_label("")
        self.filename_label.setObjectName("pendingOpenRequestFilename")
        self.filename_label.setAccessibleName("Queued PDF open request")
        self.cancel_button = bindings.q_push_button("Cancel pending open")
        self.cancel_button.setObjectName("cancelPendingOpenButton")
        self.cancel_button.setAccessibleName("Cancel pending open")
        self.cancel_button.setToolTip("Keep the current document and discard the queued PDF")
        self.cancel_button.clicked.connect(on_cancel)
        layout.addWidget(self.filename_label, 1)
        layout.addWidget(self.cancel_button)
        self.status_bar.addPermanentWidget(self.container, 1)
        self.clear()

    @property
    def visible(self) -> bool:
        is_visible = getattr(self.status_bar, "isVisible", None)
        return bool(is_visible()) if callable(is_visible) else False

    def show_request(self, pdf_path: str) -> None:
        """Publish a queued basename and make the condition-only surface visible."""

        self.filename_label.setText(
            f"Opening {Path(pdf_path).name} will be available after signing finishes."
        )
        self.status_bar.show()
        self.container.show()

    def clear(self) -> None:
        """Hide the surface and remove the queued filename from the UI."""

        self.filename_label.setText("")
        self.container.hide()
        self.status_bar.hide()
