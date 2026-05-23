"""Qt sidebar composition for the production signing workspace."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SigningFlowSummaryControls:
    """Read-only labels that show the current signing-flow stage."""

    container: Any
    stage_label: Any
    detail_label: Any


@dataclass(frozen=True)
class DocumentReviewControls:
    """Read-only labels that summarize the current PDF review state."""

    container: Any
    headline_label: Any
    detail_label: Any
    signature_items_label: Any
    signature_selector: Any
    signature_detail_label: Any
    verify_button: Any


@dataclass(frozen=True)
class DocumentTextControls:
    """Read-only widgets that expose document text review actions."""

    container: Any
    query_input: Any
    find_button: Any
    previous_button: Any
    next_button: Any
    copy_button: Any
    select_mode_checkbox: Any
    copy_selection_button: Any
    clear_selection_button: Any
    status_label: Any
    detail_label: Any


def format_document_signature_items(signature_items: tuple[Any, ...]) -> str:
    """Render compact per-signature summary lines for the review card."""

    if not signature_items:
        return ""
    return "\n".join(f"{item.label}: {item.detail}" for item in signature_items)


class SigningWorkspaceSidebar:
    """Build the production sidebar used by the signing workspace."""

    def __init__(
        self,
        *,
        bindings: Any,
        properties_widget: Any,
        on_choose_output: Callable[[], Any],
        on_sign: Callable[[], Any],
        on_open_signed_output: Callable[[], Any],
        on_find_text: Callable[[], Any],
        on_previous_text_match: Callable[[], Any],
        on_next_text_match: Callable[[], Any],
        on_copy_text_match: Callable[[], Any],
        on_text_selection_mode_changed: Callable[[bool], Any],
        on_copy_selected_text: Callable[[], Any],
        on_clear_selected_text: Callable[[], Any],
    ) -> None:
        self._bindings = bindings
        self.container = bindings.q_widget()
        self._layout = bindings.q_vbox_layout(self.container)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(8)

        self.properties_scroll = bindings.q_scroll_area()
        scroll_setter = getattr(self.properties_scroll, "setWidgetResizable", None)
        if callable(scroll_setter):
            scroll_setter(True)
        widget_setter = getattr(self.properties_scroll, "setWidget", None)
        if callable(widget_setter):
            widget_setter(properties_widget)

        self.flow_summary_controls = self._build_flow_summary_controls()
        self.document_review_controls = self._build_document_review_controls(
            on_open_signed_output=on_open_signed_output
        )
        self.document_text_controls = self._build_document_text_controls(
            on_find_text=on_find_text,
            on_previous_text_match=on_previous_text_match,
            on_next_text_match=on_next_text_match,
            on_copy_text_match=on_copy_text_match,
            on_text_selection_mode_changed=on_text_selection_mode_changed,
            on_copy_selected_text=on_copy_selected_text,
            on_clear_selected_text=on_clear_selected_text,
        )
        self.choose_output_button = bindings.q_push_button("Choose output...")
        self.choose_output_button.clicked.connect(on_choose_output)  # type: ignore[attr-defined]
        self.sign_button = bindings.q_push_button("Confirm and sign")
        self.sign_button.clicked.connect(on_sign)  # type: ignore[attr-defined]
        self.open_signed_output_button = bindings.q_push_button("Open signed PDF")
        self.open_signed_output_button.setEnabled(False)
        self.open_signed_output_button.clicked.connect(on_open_signed_output)  # type: ignore[attr-defined]
        self.result_label = bindings.q_label("")
        if hasattr(self.result_label, "setWordWrap"):
            self.result_label.setWordWrap(True)
        if hasattr(self.result_label, "setStyleSheet"):
            self.result_label.setStyleSheet("color: #444;")

        self._layout.addWidget(self.properties_scroll)
        self._layout.addWidget(self.flow_summary_controls.container)
        self._layout.addWidget(self.choose_output_button)
        self._layout.addWidget(self.sign_button)
        self._layout.addWidget(self.open_signed_output_button)
        self._layout.addWidget(self.result_label)
        self._layout.addWidget(self.document_review_controls.container)
        self._layout.addWidget(self.document_text_controls.container)

    def _build_flow_summary_controls(self) -> SigningFlowSummaryControls:
        container = self._bindings.q_group_box("Sign document")
        _style_panel(container)
        layout = self._bindings.q_vbox_layout(container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(3)
        stage_label = self._bindings.q_label("")
        detail_label = self._bindings.q_label("")
        for label in (stage_label, detail_label):
            if hasattr(label, "setWordWrap"):
                label.setWordWrap(True)
        if hasattr(stage_label, "setStyleSheet"):
            stage_label.setStyleSheet("font-weight: 700; color: #111827;")
        if hasattr(detail_label, "setStyleSheet"):
            detail_label.setStyleSheet("color: #374151;")
        layout.addWidget(stage_label)
        layout.addWidget(detail_label)
        return SigningFlowSummaryControls(
            container=container,
            stage_label=stage_label,
            detail_label=detail_label,
        )

    def _build_document_review_controls(
        self,
        *,
        on_open_signed_output: Callable[[], Any],
    ) -> DocumentReviewControls:
        container = self._bindings.q_group_box("Document review")
        _style_panel(container)
        layout = self._bindings.q_vbox_layout(container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(3)
        headline_label = self._bindings.q_label("")
        detail_label = self._bindings.q_label("")
        signature_items_label = self._bindings.q_label("")
        signature_selector = self._bindings.q_combo_box()
        signature_selector.setEnabled(False)
        signature_detail_label = self._bindings.q_label("")
        verify_button = self._bindings.q_push_button("Verify signed PDF")
        verify_button.setEnabled(False)
        for label in (
            headline_label,
            detail_label,
            signature_items_label,
            signature_detail_label,
        ):
            if hasattr(label, "setWordWrap"):
                label.setWordWrap(True)
        if hasattr(headline_label, "setStyleSheet"):
            headline_label.setStyleSheet("font-weight: 700; color: #111827;")
        if hasattr(detail_label, "setStyleSheet"):
            detail_label.setStyleSheet("color: #374151;")
        if hasattr(signature_items_label, "setStyleSheet"):
            signature_items_label.setStyleSheet("color: #1f2937;")
        if hasattr(signature_detail_label, "setStyleSheet"):
            signature_detail_label.setStyleSheet("color: #374151;")
        verify_button.clicked.connect(on_open_signed_output)  # type: ignore[attr-defined]
        layout.addWidget(headline_label)
        layout.addWidget(detail_label)
        layout.addWidget(signature_items_label)
        layout.addWidget(signature_selector)
        layout.addWidget(signature_detail_label)
        layout.addWidget(verify_button)
        return DocumentReviewControls(
            container=container,
            headline_label=headline_label,
            detail_label=detail_label,
            signature_items_label=signature_items_label,
            signature_selector=signature_selector,
            signature_detail_label=signature_detail_label,
            verify_button=verify_button,
        )

    def _build_document_text_controls(
        self,
        *,
        on_find_text: Callable[[], Any],
        on_previous_text_match: Callable[[], Any],
        on_next_text_match: Callable[[], Any],
        on_copy_text_match: Callable[[], Any],
        on_text_selection_mode_changed: Callable[[bool], Any],
        on_copy_selected_text: Callable[[], Any],
        on_clear_selected_text: Callable[[], Any],
    ) -> DocumentTextControls:
        container = self._bindings.q_group_box("Document text")
        _style_panel(container)
        layout = self._bindings.q_vbox_layout(container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)
        query_input = self._bindings.q_line_edit()
        query_input.setPlaceholderText("Search document text")
        find_button = self._bindings.q_push_button("Find")
        previous_button = self._bindings.q_push_button("Previous")
        next_button = self._bindings.q_push_button("Next")
        copy_button = self._bindings.q_push_button("Copy result")
        select_mode_checkbox = self._bindings.q_check_box("Select text")
        copy_selection_button = self._bindings.q_push_button("Copy selection")
        clear_selection_button = self._bindings.q_push_button("Clear selection")
        previous_button.setEnabled(False)
        next_button.setEnabled(False)
        copy_button.setEnabled(False)
        copy_selection_button.setEnabled(False)
        clear_selection_button.setEnabled(False)
        controls_row = _compose_row(
            self._bindings,
            query_input,
            find_button,
            previous_button,
            next_button,
            copy_button,
        )
        selection_row = _compose_row(
            self._bindings,
            select_mode_checkbox,
            copy_selection_button,
            clear_selection_button,
        )
        status_label = self._bindings.q_label("")
        detail_label = self._bindings.q_label("")
        for label in (status_label, detail_label):
            if hasattr(label, "setWordWrap"):
                label.setWordWrap(True)
        if hasattr(status_label, "setStyleSheet"):
            status_label.setStyleSheet("font-weight: 700; color: #111827;")
        if hasattr(detail_label, "setStyleSheet"):
            detail_label.setStyleSheet("color: #374151;")
        find_button.clicked.connect(on_find_text)  # type: ignore[attr-defined]
        previous_button.clicked.connect(on_previous_text_match)  # type: ignore[attr-defined]
        next_button.clicked.connect(on_next_text_match)  # type: ignore[attr-defined]
        copy_button.clicked.connect(on_copy_text_match)  # type: ignore[attr-defined]
        select_mode_checkbox.stateChanged.connect(  # type: ignore[attr-defined]
            lambda state: on_text_selection_mode_changed(bool(state))
        )
        copy_selection_button.clicked.connect(on_copy_selected_text)  # type: ignore[attr-defined]
        clear_selection_button.clicked.connect(on_clear_selected_text)  # type: ignore[attr-defined]
        layout.addWidget(controls_row)
        layout.addWidget(selection_row)
        layout.addWidget(status_label)
        layout.addWidget(detail_label)
        return DocumentTextControls(
            container=container,
            query_input=query_input,
            find_button=find_button,
            previous_button=previous_button,
            next_button=next_button,
            copy_button=copy_button,
            select_mode_checkbox=select_mode_checkbox,
            copy_selection_button=copy_selection_button,
            clear_selection_button=clear_selection_button,
            status_label=status_label,
            detail_label=detail_label,
        )


def _compose_row(bindings: Any, *widgets: Any) -> Any:
    container = bindings.q_widget()
    layout = bindings.q_hbox_layout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    for widget in widgets:
        layout.addWidget(widget)
    return container


def _style_panel(container: Any) -> None:
    if hasattr(container, "setStyleSheet"):
        container.setStyleSheet(
            "QGroupBox {"
            " border: 1px solid #d0d7de;"
            " border-radius: 6px;"
            " padding: 6px;"
            " background: #f6f8fa;"
            "}"
        )
