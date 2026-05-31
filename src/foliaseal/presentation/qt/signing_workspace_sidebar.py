"""Qt sidebar composition for the production signing workspace."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from foliaseal.presentation.qt.signing_action_coordinator import SigningActionState


@dataclass(frozen=True)
class SigningActionControls:
    """Widgets used for the primary signing action/status panel."""

    container: Any
    stage_label: Any
    detail_label: Any
    choose_output_button: Any
    sign_button: Any
    open_signed_output_button: Any
    result_label: Any


@dataclass(frozen=True)
class DocumentReviewControls:
    """Read-only labels that summarize the current PDF review state."""

    container: Any
    headline_label: Any
    detail_label: Any
    signature_items_label: Any
    signature_selector: Any
    signature_detail_label: Any


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

        self.signing_action_controls = self._build_signing_action_controls(
            on_choose_output=on_choose_output,
            on_sign=on_sign,
            on_open_signed_output=on_open_signed_output,
        )
        self.document_review_controls = self._build_document_review_controls()
        self.document_text_controls = self._build_document_text_controls(
            on_find_text=on_find_text,
            on_previous_text_match=on_previous_text_match,
            on_next_text_match=on_next_text_match,
            on_copy_text_match=on_copy_text_match,
            on_text_selection_mode_changed=on_text_selection_mode_changed,
            on_copy_selected_text=on_copy_selected_text,
            on_clear_selected_text=on_clear_selected_text,
        )
        self.choose_output_button = self.signing_action_controls.choose_output_button
        self.sign_button = self.signing_action_controls.sign_button
        self.open_signed_output_button = (
            self.signing_action_controls.open_signed_output_button
        )
        self.result_label = self.signing_action_controls.result_label

        self._layout.addWidget(self.properties_scroll)
        self._layout.addWidget(self.signing_action_controls.container)
        self._layout.addWidget(self.document_review_controls.container)
        self._layout.addWidget(self.document_text_controls.container)

    def apply_signing_action_state(self, state: SigningActionState) -> None:
        self.sign_button.setEnabled(state.can_sign)
        self.open_signed_output_button.setEnabled(state.can_open_signed_output)
        self.signing_action_controls.stage_label.setText(state.stage_text)
        self.signing_action_controls.detail_label.setText(state.detail_text)
        _set_widget_width_limit(
            self.signing_action_controls.detail_label,
            _panel_available_width(self.container),
        )
        self.result_label.setText(state.result_text)
        if hasattr(self.result_label, "setStyleSheet"):
            if state.result_kind == "success":
                self.result_label.setStyleSheet(
                    "color: #1f6f2a; font-weight: 600;"
                )
            elif state.result_kind == "error":
                self.result_label.setStyleSheet(
                    "color: #9f1d1d; font-weight: 600;"
                )
            else:
                self.result_label.setStyleSheet("color: #444;")

    def _build_signing_action_controls(
        self,
        *,
        on_choose_output: Callable[[], Any],
        on_sign: Callable[[], Any],
        on_open_signed_output: Callable[[], Any],
    ) -> SigningActionControls:
        container = self._bindings.q_group_box("Sign PDF")
        _style_panel(container)
        layout = self._bindings.q_vbox_layout(container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)
        stage_label = self._bindings.q_label("")
        detail_label = self._bindings.q_label("")
        choose_output_button = self._bindings.q_push_button("Choose output...")
        sign_button = self._bindings.q_push_button("Confirm and sign")
        open_signed_output_button = self._bindings.q_push_button("Open signed PDF")
        open_signed_output_button.setEnabled(False)
        result_label = self._bindings.q_label("")
        for label in (stage_label, detail_label):
            if hasattr(label, "setWordWrap"):
                label.setWordWrap(True)
        if hasattr(result_label, "setWordWrap"):
            result_label.setWordWrap(True)
        if hasattr(stage_label, "setStyleSheet"):
            stage_label.setStyleSheet("font-weight: 700; color: #111827;")
        if hasattr(detail_label, "setStyleSheet"):
            detail_label.setStyleSheet("color: #374151;")
        if hasattr(result_label, "setStyleSheet"):
            result_label.setStyleSheet("color: #444;")
        choose_output_button.clicked.connect(on_choose_output)  # type: ignore[attr-defined]
        sign_button.clicked.connect(on_sign)  # type: ignore[attr-defined]
        open_signed_output_button.clicked.connect(on_open_signed_output)  # type: ignore[attr-defined]
        layout.addWidget(stage_label)
        layout.addWidget(detail_label)
        layout.addWidget(choose_output_button)
        layout.addWidget(sign_button)
        layout.addWidget(open_signed_output_button)
        layout.addWidget(result_label)
        return SigningActionControls(
            container=container,
            stage_label=stage_label,
            detail_label=detail_label,
            choose_output_button=choose_output_button,
            sign_button=sign_button,
            open_signed_output_button=open_signed_output_button,
            result_label=result_label,
        )

    def _build_document_review_controls(
        self,
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
        layout.addWidget(headline_label)
        layout.addWidget(detail_label)
        layout.addWidget(signature_items_label)
        layout.addWidget(signature_selector)
        layout.addWidget(signature_detail_label)
        return DocumentReviewControls(
            container=container,
            headline_label=headline_label,
            detail_label=detail_label,
            signature_items_label=signature_items_label,
            signature_selector=signature_selector,
            signature_detail_label=signature_detail_label,
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


def _set_widget_width_limit(widget: Any, width: int) -> None:
    fixed_width = getattr(widget, "setFixedWidth", None)
    if callable(fixed_width):
        fixed_width(width)
        return
    max_width = getattr(widget, "setMaximumWidth", None)
    if callable(max_width):
        max_width(width)


def _panel_available_width(widget: Any) -> int:
    width_getter = getattr(widget, "width", None)
    if not callable(width_getter):
        return 520
    try:
        width = int(width_getter())
    except TypeError:
        return 520
    if width > 0:
        return max(1, width - 16)
    return 520
