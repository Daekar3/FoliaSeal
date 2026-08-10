"""Qt sidebar composition for the production signing workspace."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from foliaseal.application.document_review_workspace import (
    DocumentReviewWorkspaceState,
)
from foliaseal.presentation.qt.signing_action_coordinator import SigningActionState


@dataclass(frozen=True)
class SigningActionControls:
    """Widgets used for the interactive action group and read-only status group."""

    container: Any
    status_container: Any
    journey_label: Any
    stage_label: Any
    detail_label: Any
    choose_output_button: Any
    sign_button: Any
    open_signed_output_button: Any
    verify_again_button: Any
    return_to_draft_button: Any
    open_preserved_copy_button: Any
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


@dataclass(frozen=True)
class SigningWorkspaceSidebarSurface:
    """Grouped shell-facing surface for sidebar-owned controls."""

    container: Any
    properties_scroll: Any
    signing_action_panel: Any
    status_region: Any
    choose_output_button: Any
    sign_button: Any
    open_signed_output_button: Any
    verify_again_button: Any
    return_to_draft_button: Any
    open_preserved_copy_button: Any
    sign_result_label: Any
    flow_journey_label: Any
    flow_stage_label: Any
    flow_detail_label: Any
    document_review_headline_label: Any
    document_review_detail_label: Any
    document_review_signature_items_label: Any
    document_review_signature_selector: Any
    document_review_signature_detail_label: Any
    document_text_query_input: Any
    document_text_find_button: Any
    document_text_previous_button: Any
    document_text_next_button: Any
    document_text_copy_button: Any
    document_text_select_mode_checkbox: Any
    document_text_copy_selection_button: Any
    document_text_clear_selection_button: Any
    document_text_status_label: Any
    document_text_detail_label: Any


def format_document_signature_items(signature_items: tuple[Any, ...]) -> str:
    """Render compact per-signature summary lines for the review card."""

    if not signature_items:
        return ""
    return "\n".join(f"{item.label}: {item.detail}" for item in signature_items)


class SigningWorkspaceSidebar:
    """Build the production sidebar used by the signing workspace."""

    RAIL_WIDTH = 320
    STATUS_REGION_MINIMUM_HEIGHT = 200

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
        on_review_signature_selected: Callable[[int], Any],
        on_text_selection_mode_changed: Callable[[bool], Any],
        on_copy_selected_text: Callable[[], Any],
        on_clear_selected_text: Callable[[], Any],
        on_verify_again: Callable[[], Any] | None = None,
        on_return_to_draft: Callable[[], Any] | None = None,
        on_open_preserved_copy: Callable[[], Any] | None = None,
    ) -> None:
        self._bindings = bindings
        self._updating_document_review_selector = False
        self._updating_text_selection_mode_checkbox = False
        self.container = bindings.q_widget()
        set_fixed_width = getattr(self.container, "setFixedWidth", None)
        if callable(set_fixed_width):
            set_fixed_width(self.RAIL_WIDTH)
        else:
            set_minimum_width = getattr(self.container, "setMinimumWidth", None)
            set_maximum_width = getattr(self.container, "setMaximumWidth", None)
            if callable(set_minimum_width):
                set_minimum_width(self.RAIL_WIDTH)
            if callable(set_maximum_width):
                set_maximum_width(self.RAIL_WIDTH)
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
            on_verify_again=on_verify_again or (lambda: None),
            on_return_to_draft=on_return_to_draft or (lambda: None),
            on_open_preserved_copy=on_open_preserved_copy or (lambda: None),
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
        self.status_region = self.signing_action_controls.status_container
        set_minimum_height = getattr(self.status_region, "setMinimumHeight", None)
        if callable(set_minimum_height):
            set_minimum_height(self.STATUS_REGION_MINIMUM_HEIGHT)
        index_changed = getattr(
            self.document_review_controls.signature_selector,
            "currentIndexChanged",
            None,
        )
        if hasattr(index_changed, "connect"):
            index_changed.connect(  # type: ignore[attr-defined]
                lambda index: self._handle_review_signature_selected(
                    index,
                    on_review_signature_selected=on_review_signature_selected,
                )
            )
        self.choose_output_button = self.signing_action_controls.choose_output_button
        self.sign_button = self.signing_action_controls.sign_button
        self.open_signed_output_button = (
            self.signing_action_controls.open_signed_output_button
        )
        self.verify_again_button = self.signing_action_controls.verify_again_button
        self.return_to_draft_button = self.signing_action_controls.return_to_draft_button
        self.open_preserved_copy_button = self.signing_action_controls.open_preserved_copy_button
        self.result_label = self.signing_action_controls.result_label
        self.surface = SigningWorkspaceSidebarSurface(
            container=self.container,
            properties_scroll=self.properties_scroll,
            signing_action_panel=self.signing_action_controls.container,
            status_region=self.status_region,
            choose_output_button=self.choose_output_button,
            sign_button=self.sign_button,
            open_signed_output_button=self.open_signed_output_button,
            verify_again_button=self.verify_again_button,
            return_to_draft_button=self.return_to_draft_button,
            open_preserved_copy_button=self.open_preserved_copy_button,
            sign_result_label=self.result_label,
            flow_journey_label=self.signing_action_controls.journey_label,
            flow_stage_label=self.signing_action_controls.stage_label,
            flow_detail_label=self.signing_action_controls.detail_label,
            document_review_headline_label=self.document_review_controls.headline_label,
            document_review_detail_label=self.document_review_controls.detail_label,
            document_review_signature_items_label=(
                self.document_review_controls.signature_items_label
            ),
            document_review_signature_selector=(
                self.document_review_controls.signature_selector
            ),
            document_review_signature_detail_label=(
                self.document_review_controls.signature_detail_label
            ),
            document_text_query_input=self.document_text_controls.query_input,
            document_text_find_button=self.document_text_controls.find_button,
            document_text_previous_button=self.document_text_controls.previous_button,
            document_text_next_button=self.document_text_controls.next_button,
            document_text_copy_button=self.document_text_controls.copy_button,
            document_text_select_mode_checkbox=(
                self.document_text_controls.select_mode_checkbox
            ),
            document_text_copy_selection_button=(
                self.document_text_controls.copy_selection_button
            ),
            document_text_clear_selection_button=(
                self.document_text_controls.clear_selection_button
            ),
            document_text_status_label=self.document_text_controls.status_label,
            document_text_detail_label=self.document_text_controls.detail_label,
        )

        self._layout.addWidget(self.properties_scroll, 1)
        self._layout.addWidget(self.document_review_controls.container)
        self._layout.addWidget(self.document_text_controls.container)
        self._layout.addWidget(self.signing_action_controls.container)
        self._layout.addWidget(self.status_region)

    def render_signing_action_state(self, state: SigningActionState) -> None:
        self.sign_button.setEnabled(state.can_sign)
        self.open_signed_output_button.setEnabled(state.can_open_signed_output)
        self.verify_again_button.setEnabled(state.can_verify_again)
        self.return_to_draft_button.setEnabled(state.can_return_to_draft)
        self.open_preserved_copy_button.setEnabled(state.can_open_preserved_copy)
        self.signing_action_controls.stage_label.setText(state.stage_text)
        self.signing_action_controls.detail_label.setText(state.detail_text)
        _set_widget_width_limit(
            self.signing_action_controls.detail_label,
            _panel_available_width(self.container),
        )
        self.result_label.setText(state.result_text)
        self._mark_recommended_action(state.recommended_action)
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

    def _mark_recommended_action(self, action_name: str | None) -> None:
        buttons = {
            "sign": self.sign_button,
            "open_signed_output": self.open_signed_output_button,
            "verify_again": self.verify_again_button,
            "return_to_draft": self.return_to_draft_button,
            "open_preserved_copy": self.open_preserved_copy_button,
        }
        for name, button in buttons.items():
            is_primary = name == action_name
            set_property = getattr(button, "setProperty", None)
            if callable(set_property):
                set_property("foliasealPrimaryAction", is_primary)
            set_style = getattr(button, "setStyleSheet", None)
            if callable(set_style):
                set_style(
                    "font-weight: 700; border: 2px solid #2563eb;"
                    if is_primary
                    else "font-weight: 400;"
                )
            set_accessible_name = getattr(button, "setAccessibleName", None)
            if callable(set_accessible_name):
                labels = {
                    "sign": "Confirm and sign",
                    "open_signed_output": "Open signed PDF",
                    "verify_again": "Verify again",
                    "return_to_draft": "Return to draft",
                    "open_preserved_copy": "Open preserved copy",
                }
                set_accessible_name(
                    "Recommended next action: "
                    + labels.get(name, name)
                    if is_primary
                    else ""
                )
            set_tool_tip = getattr(button, "setToolTip", None)
            if callable(set_tool_tip):
                set_tool_tip("Recommended next action" if is_primary else "")

    def apply_signing_action_state(self, state: SigningActionState) -> None:
        self.render_signing_action_state(state)

    def apply_document_review_workspace_state(
        self,
        state: DocumentReviewWorkspaceState,
        *,
        can_copy_text: bool,
    ) -> None:
        review_state = state.review
        document_text_state = state.document_text
        self.document_review_controls.headline_label.setText(
            review_state.review_summary.headline
        )
        self.document_review_controls.detail_label.setText(
            review_state.review_summary.detail
        )
        self.document_review_controls.signature_items_label.setText(
            format_document_signature_items(review_state.review_summary.signature_items)
        )
        selector = self.document_review_controls.signature_selector
        self._updating_document_review_selector = True
        try:
            selector.clear()
            if not review_state.signature_labels:
                selector.setEnabled(False)
            else:
                selector.addItems(list(review_state.signature_labels))
                selector.setEnabled(review_state.selector_enabled)
                setter = getattr(selector, "setCurrentIndex", None)
                current_text = getattr(selector, "currentText", None)
                current_label = current_text() if callable(current_text) else None
                if (
                    callable(setter)
                    and review_state.selected_signature_index is not None
                    and current_label != review_state.selected_signature_label
                ):
                    setter(review_state.selected_signature_index)
        finally:
            self._updating_document_review_selector = False
        self.document_review_controls.signature_detail_label.setText(
            review_state.selected_signature_detail
        )
        checkbox = self.document_text_controls.select_mode_checkbox
        is_checked = getattr(checkbox, "isChecked", None)
        if (
            callable(is_checked)
            and bool(is_checked()) != document_text_state.selection_mode_enabled
        ):
            self._updating_text_selection_mode_checkbox = True
            try:
                checkbox.setChecked(document_text_state.selection_mode_enabled)
            finally:
                self._updating_text_selection_mode_checkbox = False
        self.document_text_controls.status_label.setText(document_text_state.status_text)
        self.document_text_controls.detail_label.setText(document_text_state.detail_text)
        self.document_text_controls.previous_button.setEnabled(
            document_text_state.search_state.can_go_previous
        )
        self.document_text_controls.next_button.setEnabled(
            document_text_state.search_state.can_go_next
        )
        self.document_text_controls.copy_button.setEnabled(
            document_text_state.search_state.can_copy and can_copy_text
        )
        self.document_text_controls.copy_selection_button.setEnabled(
            document_text_state.selection_state.can_copy and can_copy_text
        )
        self.document_text_controls.clear_selection_button.setEnabled(
            document_text_state.selection_state.can_clear
        )

    def _build_signing_action_controls(
        self,
        *,
        on_choose_output: Callable[[], Any],
        on_sign: Callable[[], Any],
        on_open_signed_output: Callable[[], Any],
        on_verify_again: Callable[[], Any],
        on_return_to_draft: Callable[[], Any],
        on_open_preserved_copy: Callable[[], Any],
    ) -> SigningActionControls:
        container = self._bindings.q_group_box("Sign PDF")
        _style_panel(container)
        layout = self._bindings.q_vbox_layout(container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)
        status_container = self._bindings.q_group_box("Signing status")
        _style_panel(status_container)
        status_layout = self._bindings.q_vbox_layout(status_container)
        status_layout.setContentsMargins(6, 6, 6, 6)
        status_layout.setSpacing(4)
        stage_label = self._bindings.q_label("")
        journey_label = self._bindings.q_label(
            "Workflow: 1 Review → 2 Setup → 3 Place → 4 Ready → 5 Sign → 6 Verify"
        )
        detail_label = self._bindings.q_label("")
        choose_output_button = self._bindings.q_push_button("Choose output...")
        sign_button = self._bindings.q_push_button("Confirm and sign")
        open_signed_output_button = self._bindings.q_push_button("Open signed PDF")
        open_signed_output_button.setEnabled(False)
        verify_again_button = self._bindings.q_push_button("Verify again")
        return_to_draft_button = self._bindings.q_push_button("Return to draft")
        open_preserved_copy_button = self._bindings.q_push_button("Open preserved copy")
        for button in (
            verify_again_button,
            return_to_draft_button,
            open_preserved_copy_button,
        ):
            button.setEnabled(False)
        result_label = self._bindings.q_label("")
        for label in (journey_label, stage_label, detail_label):
            if hasattr(label, "setWordWrap"):
                label.setWordWrap(True)
        if hasattr(result_label, "setWordWrap"):
            result_label.setWordWrap(True)
        if hasattr(stage_label, "setStyleSheet"):
            stage_label.setStyleSheet("font-weight: 700; color: #111827;")
        if hasattr(journey_label, "setStyleSheet"):
            journey_label.setStyleSheet("color: #4b5563; font-size: 11px;")
        if hasattr(detail_label, "setStyleSheet"):
            detail_label.setStyleSheet("color: #374151;")
        if hasattr(result_label, "setStyleSheet"):
            result_label.setStyleSheet("color: #444;")
        choose_output_button.clicked.connect(on_choose_output)  # type: ignore[attr-defined]
        sign_button.clicked.connect(on_sign)  # type: ignore[attr-defined]
        open_signed_output_button.clicked.connect(on_open_signed_output)  # type: ignore[attr-defined]
        verify_again_button.clicked.connect(on_verify_again)  # type: ignore[attr-defined]
        return_to_draft_button.clicked.connect(on_return_to_draft)  # type: ignore[attr-defined]
        open_preserved_copy_button.clicked.connect(on_open_preserved_copy)  # type: ignore[attr-defined]
        layout.addWidget(choose_output_button)
        layout.addWidget(sign_button)
        layout.addWidget(open_signed_output_button)
        layout.addWidget(verify_again_button)
        layout.addWidget(return_to_draft_button)
        layout.addWidget(open_preserved_copy_button)
        status_layout.addWidget(journey_label)
        status_layout.addWidget(stage_label)
        status_layout.addWidget(detail_label)
        status_layout.addWidget(result_label)
        return SigningActionControls(
            container=container,
            status_container=status_container,
            journey_label=journey_label,
            stage_label=stage_label,
            detail_label=detail_label,
            choose_output_button=choose_output_button,
            sign_button=sign_button,
            open_signed_output_button=open_signed_output_button,
            verify_again_button=verify_again_button,
            return_to_draft_button=return_to_draft_button,
            open_preserved_copy_button=open_preserved_copy_button,
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
        set_accessible_name = getattr(query_input, "setAccessibleName", None)
        if callable(set_accessible_name):
            set_accessible_name("Find text in current PDF")
        find_button = self._bindings.q_push_button("Find")
        previous_button = self._bindings.q_push_button("Previous")
        next_button = self._bindings.q_push_button("Next")
        copy_button = self._bindings.q_push_button("Copy result")
        # Keep a hidden checkbox as a state mirror so existing shell render wiring
        # can stay narrow while the real user-facing mode command moves to Edit.
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
        if hasattr(select_mode_checkbox, "setVisible"):
            select_mode_checkbox.setVisible(False)
        if hasattr(copy_selection_button, "setVisible"):
            copy_selection_button.setVisible(False)
        if hasattr(clear_selection_button, "setVisible"):
            clear_selection_button.setVisible(False)
        selection_row = _compose_row(
            self._bindings,
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
        return_pressed = getattr(query_input, "returnPressed", None)
        if hasattr(return_pressed, "connect"):
            return_pressed.connect(on_find_text)
        previous_button.clicked.connect(on_previous_text_match)  # type: ignore[attr-defined]
        next_button.clicked.connect(on_next_text_match)  # type: ignore[attr-defined]
        copy_button.clicked.connect(on_copy_text_match)  # type: ignore[attr-defined]
        select_mode_checkbox.stateChanged.connect(  # type: ignore[attr-defined]
            lambda state: self._handle_text_selection_mode_changed(
                state,
                on_text_selection_mode_changed=on_text_selection_mode_changed,
            )
        )
        copy_selection_button.clicked.connect(on_copy_selected_text)  # type: ignore[attr-defined]
        clear_selection_button.clicked.connect(on_clear_selected_text)  # type: ignore[attr-defined]
        try:
            shortcut_type = getattr(self._bindings, "q_shortcut", None)
            key_sequence_type = getattr(self._bindings, "q_key_sequence", None)
            if shortcut_type is None or key_sequence_type is None:
                raise RuntimeError("Qt shortcut bindings are unavailable")
            previous_shortcut = shortcut_type(key_sequence_type("Shift+Return"), query_input)
            previous_shortcut.activated.connect(on_previous_text_match)
            setattr(query_input, "_foliaseal_previous_search_shortcut", previous_shortcut)
        except Exception:  # pragma: no cover - dynamic Qt/test-double boundary
            pass
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

    def _handle_review_signature_selected(
        self,
        index: int,
        *,
        on_review_signature_selected: Callable[[int], Any],
    ) -> None:
        if self._updating_document_review_selector:
            return
        on_review_signature_selected(index)

    def _handle_text_selection_mode_changed(
        self,
        state: Any,
        *,
        on_text_selection_mode_changed: Callable[[bool], Any],
    ) -> None:
        if self._updating_text_selection_mode_checkbox:
            return
        on_text_selection_mode_changed(bool(state))


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
