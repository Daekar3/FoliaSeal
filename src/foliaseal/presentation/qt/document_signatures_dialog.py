"""Modeless Document Signatures review surface."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from foliaseal.application.document_review import DocumentSignatureReviewItem
from foliaseal.application.document_review_workspace import DocumentReviewWorkspaceState


@dataclass(frozen=True)
class DocumentSignaturesDialogControls:
    """Public controls used by the modeless review surface and its tests."""

    dialog: Any
    item_list: Any
    detail_text: Any
    use_button: Any
    close_button: Any


class DocumentSignaturesDialog:
    """Show signed signatures and empty signature fields without blocking the frame."""

    def __init__(
        self,
        *,
        bindings: Any,
        parent: Any,
        state: DocumentReviewWorkspaceState,
        on_select: Callable[[str], Any],
        on_use_unsigned_field: Callable[[str], Any] | None = None,
        on_close: Callable[[], Any] | None = None,
    ) -> None:
        self._bindings = bindings
        self._on_select = on_select
        self._on_use_unsigned_field = on_use_unsigned_field
        self._on_close = on_close
        self._items: tuple[DocumentSignatureReviewItem, ...] = ()
        self._updating = False
        self._close_notified = False
        self.controls = self._build_controls(parent)
        self.refresh(state)

    def show(self) -> DocumentSignaturesDialog:
        show = getattr(self.controls.dialog, "show", None)
        if callable(show):
            show()
        raise_window = getattr(self.controls.dialog, "raise_", None)
        if callable(raise_window):
            raise_window()
        activate = getattr(self.controls.dialog, "activateWindow", None)
        if callable(activate):
            activate()
        return self

    def refresh(self, state: DocumentReviewWorkspaceState) -> None:
        selected_id = self._selected_id()
        self._items = tuple(state.review.review_summary.signature_items)
        self._updating = True
        try:
            self.controls.item_list.clear()
            self.controls.item_list.addItems([self._display_label(item) for item in self._items])
            target_row = next(
                (
                    index
                    for index, item in enumerate(self._items)
                    if (item.signature_id or item.label) == selected_id
                ),
                0 if self._items else -1,
            )
            self.controls.item_list.setCurrentRow(target_row)
        finally:
            self._updating = False
        self._render_detail(target_row)
        self._sync_use_button(target_row)

    def close(self) -> None:
        close = getattr(self.controls.dialog, "close", None)
        if callable(close):
            close()

    def _build_controls(self, parent: Any) -> DocumentSignaturesDialogControls:
        q_widget = self._require_binding("q_widget")
        q_hbox_layout = self._require_binding("q_hbox_layout")
        q_vbox_layout = self._require_binding("q_vbox_layout")
        q_list_widget = self._require_binding("q_list_widget")
        q_text_edit = self._require_binding("q_text_edit")
        dialog = self._bindings.q_dialog(parent)
        dialog.setWindowTitle("Document Signatures")
        dialog.setMinimumSize(900, 550)
        root = q_hbox_layout(dialog)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        catalog_column = q_widget()
        catalog_layout = q_vbox_layout(catalog_column)
        catalog_layout.addWidget(self._bindings.q_label("Signatures and fields"))
        item_list = q_list_widget()
        item_list.setAccessibleName("Document signatures and unsigned fields")
        catalog_layout.addWidget(item_list)

        detail_column = q_widget()
        detail_layout = q_vbox_layout(detail_column)
        detail_layout.addWidget(self._bindings.q_label("Integrity and details"))
        detail_text = q_text_edit()
        detail_text.setReadOnly(True)
        detail_text.setAccessibleName("Selected document signature details")
        detail_layout.addWidget(detail_text, 1)
        use_button = self._bindings.q_push_button("Use for new signature")
        use_button.setAccessibleName("Use selected unsigned field for new signature")
        detail_layout.addWidget(use_button)
        close_button = self._bindings.q_push_button("Close")
        close_button.setAccessibleName("Close Document Signatures")
        detail_layout.addWidget(close_button)

        root.addWidget(catalog_column, 1)
        root.addWidget(detail_column, 2)
        item_list.currentRowChanged.connect(self._handle_row_changed)
        use_button.clicked.connect(self._handle_use_unsigned_field)
        close_button.clicked.connect(self.close)
        finished = getattr(dialog, "finished", None)
        if hasattr(finished, "connect"):
            finished.connect(lambda _code: self._clear_review_highlight_on_close())
        return DocumentSignaturesDialogControls(
            dialog=dialog,
            item_list=item_list,
            detail_text=detail_text,
            use_button=use_button,
            close_button=close_button,
        )

    def _handle_row_changed(self, row: int) -> None:
        if self._updating or not (0 <= row < len(self._items)):
            self._render_detail(row)
            self._sync_use_button(row)
            return
        item = self._items[row]
        self._on_select(item.signature_id or item.label)
        self._render_detail(row)
        self._sync_use_button(row)

    def _handle_use_unsigned_field(self) -> None:
        row = self.controls.item_list.currentRow()
        if not (0 <= row < len(self._items)):
            return
        item = self._items[row]
        if item.kind != "unsigned_field" or item.field_name is None:
            return
        if self._on_use_unsigned_field is not None:
            self._on_use_unsigned_field(item.field_name)

    def _sync_use_button(self, row: int) -> None:
        enabled = (
            0 <= row < len(self._items)
            and self._items[row].kind == "unsigned_field"
            and self._items[row].field_name is not None
            and self._on_use_unsigned_field is not None
        )
        setter = getattr(self.controls.use_button, "setEnabled", None)
        if callable(setter):
            setter(enabled)

    def _render_detail(self, row: int) -> None:
        if not (0 <= row < len(self._items)):
            self.controls.detail_text.setPlainText("No signature or unsigned field is available.")
            return
        item = self._items[row]
        lines = [item.detail, "", item.drill_in_detail]
        if item.kind == "unsigned_field":
            lines.extend(("", "This field is unsigned; no signer or integrity result exists."))
        elif item.kind == "signed_invisible":
            lines.extend(("", "This signature has no visible page rectangle."))
        self.controls.detail_text.setPlainText("\n".join(line for line in lines if line))

    def _selected_id(self) -> str | None:
        row = self.controls.item_list.currentRow()
        if 0 <= row < len(self._items):
            item = self._items[row]
            return item.signature_id or item.label
        return None

    @staticmethod
    def _display_label(item: DocumentSignatureReviewItem) -> str:
        if item.kind == "unsigned_field":
            return f"{item.label} — unsigned"
        if item.kind == "signed_invisible":
            return f"{item.label} — invisible"
        return item.label

    def _clear_review_highlight_on_close(self) -> None:
        if self._close_notified:
            return
        self._close_notified = True
        if self._on_close is not None:
            self._on_close()

    def _require_binding(self, name: str) -> Any:
        value = getattr(self._bindings, name, None)
        if value is None:
            raise RuntimeError(f"Document Signatures requires Qt binding {name}.")
        return value
