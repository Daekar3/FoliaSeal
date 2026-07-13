from foliaseal.application.coordinate_transform import PdfRect
from foliaseal.application.document_review import (
    DocumentReviewSummary,
    DocumentSignatureReviewItem,
)
from foliaseal.application.document_review_workspace import (
    DocumentReviewCardState,
    DocumentReviewWorkspaceState,
    DocumentTextWorkspaceState,
)
from foliaseal.application.document_text_search import (
    DocumentTextMatch,
    DocumentTextSearchState,
)
from foliaseal.application.document_text_selection import (
    DocumentTextSelection,
    DocumentTextSelectionState,
)
from foliaseal.presentation.qt.signing_workspace_sidebar import (
    SigningWorkspaceSidebar,
)
from tests.unit.test_qt_signing_shell import _fake_bindings


def _build_workspace_state() -> DocumentReviewWorkspaceState:
    return DocumentReviewWorkspaceState(
        review=DocumentReviewCardState(
            review_summary=DocumentReviewSummary(
                headline="Signature review",
                detail="Found 2 embedded signatures.",
                signature_count=2,
                signature_items=(
                    DocumentSignatureReviewItem(
                        label="Signature 1",
                        signer_subject="CN=Bob Example",
                        cryptographic_validation_passed=True,
                        detail="CN=Bob Example: verified locally.",
                        drill_in_detail="Signer: CN=Bob Example.",
                    ),
                    DocumentSignatureReviewItem(
                        label="Signature 2 (latest)",
                        signer_subject="CN=Alice Example",
                        cryptographic_validation_passed=False,
                        detail="CN=Alice Example: needs local verification attention.",
                        drill_in_detail="Signer: CN=Alice Example.",
                    ),
                ),
            ),
            signature_labels=("Signature 1", "Signature 2 (latest)"),
            selected_signature_index=1,
            selected_signature_label="Signature 2 (latest)",
            selected_signature_detail="Signer: CN=Alice Example.",
            selector_enabled=True,
        ),
        document_text=DocumentTextWorkspaceState(
            search_state=DocumentTextSearchState(
                query="Alice",
                match_count=2,
                current_index=0,
                status_text="Found 2 matches for 'Alice'.",
                detail_text="Showing 1 of 2 on page 2.",
                current_match=DocumentTextMatch(
                    page_index=1,
                    start_index=5,
                    end_index=10,
                    text="Alice",
                    context="Signed by Alice Example on page two",
                ),
                can_go_previous=False,
                can_go_next=True,
                can_copy=True,
            ),
            selection_state=DocumentTextSelectionState(
                status_text="Selected text on page 2.",
                detail_text="Alice Example",
                selection=DocumentTextSelection(
                    page_index=1,
                    text="Alice Example",
                    highlight_rects=(PdfRect(x1=10.0, y1=10.0, x2=30.0, y2=16.0),),
                ),
                can_copy=True,
                can_clear=True,
            ),
            selection_mode_enabled=False,
            display_source="search",
            status_text="Found 2 matches for 'Alice'.",
            detail_text="Showing 1 of 2 on page 2.",
        ),
    )


def _build_empty_workspace_state() -> DocumentReviewWorkspaceState:
    return DocumentReviewWorkspaceState(
        review=DocumentReviewCardState(
            review_summary=DocumentReviewSummary(
                headline="Signature review",
                detail="No embedded signatures were found.",
                signature_count=0,
            ),
            signature_labels=(),
            selected_signature_index=None,
            selected_signature_label=None,
            selected_signature_detail="",
            selector_enabled=False,
        ),
        document_text=DocumentTextWorkspaceState(
            search_state=DocumentTextSearchState(
                query="",
                match_count=0,
                current_index=None,
                status_text="Text selection mode is active.",
                detail_text="Drag over the page to capture text.",
                current_match=None,
                can_go_previous=False,
                can_go_next=False,
                can_copy=False,
            ),
            selection_state=DocumentTextSelectionState(
                status_text="Text selection mode is active.",
                detail_text="Drag over the page to capture text.",
                selection=None,
                can_copy=False,
                can_clear=False,
            ),
            selection_mode_enabled=True,
            display_source="selection",
            status_text="Text selection mode is active.",
            detail_text="Drag over the page to capture text.",
        ),
    )


def _build_sidebar(
    *,
    on_review_signature_selected=None,
    on_text_selection_mode_changed=None,
) -> SigningWorkspaceSidebar:
    bindings = _fake_bindings()
    callbacks = {
        "on_choose_output": lambda: None,
        "on_sign": lambda: None,
        "on_open_signed_output": lambda: None,
        "on_find_text": lambda: None,
        "on_previous_text_match": lambda: None,
        "on_next_text_match": lambda: None,
        "on_copy_text_match": lambda: None,
        "on_review_signature_selected": on_review_signature_selected or (lambda index: None),
        "on_text_selection_mode_changed": (
            on_text_selection_mode_changed or (lambda enabled: None)
        ),
        "on_copy_selected_text": lambda: None,
        "on_clear_selected_text": lambda: None,
    }
    return SigningWorkspaceSidebar(
        bindings=bindings,
        properties_widget=bindings.q_widget(),
        **callbacks,
    )


def test_signing_workspace_sidebar_renders_document_review_and_text_state() -> None:
    sidebar = _build_sidebar()

    sidebar.apply_document_review_workspace_state(
        _build_workspace_state(),
        can_copy_text=True,
    )

    assert sidebar.surface.container is sidebar.container
    assert sidebar.surface.signing_action_panel is sidebar.signing_action_controls.container
    assert (
        sidebar.surface.document_review_signature_selector
        is sidebar.document_review_controls.signature_selector
    )
    assert (
        sidebar.surface.document_text_find_button
        is sidebar.document_text_controls.find_button
    )
    assert sidebar.document_review_controls.headline_label.text() == "Signature review"
    assert sidebar.document_review_controls.detail_label.text() == (
        "Found 2 embedded signatures."
    )
    assert sidebar.document_review_controls.signature_items_label.text() == (
        "Signature 1: CN=Bob Example: verified locally.\n"
        "Signature 2 (latest): CN=Alice Example: needs local verification attention."
    )
    assert sidebar.document_review_controls.signature_selector.count() == 2
    assert (
        sidebar.document_review_controls.signature_selector.currentText()
        == "Signature 2 (latest)"
    )
    assert (
        sidebar.document_review_controls.signature_detail_label.text()
        == "Signer: CN=Alice Example."
    )
    assert sidebar.document_text_controls.status_label.text() == (
        "Found 2 matches for 'Alice'."
    )
    assert sidebar.document_text_controls.detail_label.text() == (
        "Showing 1 of 2 on page 2."
    )
    assert sidebar.document_text_controls.previous_button._enabled is False
    assert sidebar.document_text_controls.next_button._enabled is True
    assert sidebar.document_text_controls.copy_button._enabled is True
    assert sidebar.document_text_controls.copy_selection_button._enabled is True
    assert sidebar.document_text_controls.clear_selection_button._enabled is True


def test_signing_workspace_sidebar_ignores_selector_events_during_render() -> None:
    calls = []
    sidebar = _build_sidebar(on_review_signature_selected=calls.append)

    sidebar.apply_document_review_workspace_state(
        _build_workspace_state(),
        can_copy_text=False,
    )

    assert calls == []
    assert sidebar.document_text_controls.copy_button._enabled is False
    assert sidebar.document_text_controls.copy_selection_button._enabled is False

    sidebar.document_review_controls.signature_selector.setCurrentIndex(0)

    assert calls == [0]


def test_signing_workspace_sidebar_renders_empty_review_state_and_checkbox_state() -> None:
    sidebar = _build_sidebar()

    sidebar.apply_document_review_workspace_state(
        _build_empty_workspace_state(),
        can_copy_text=False,
    )

    assert sidebar.document_review_controls.signature_selector.count() == 0
    assert sidebar.document_review_controls.signature_selector.enabled is False
    assert sidebar.document_review_controls.signature_detail_label.text() == ""
    assert sidebar.document_text_controls.select_mode_checkbox.isChecked() is True
    assert sidebar.document_text_controls.status_label.text() == (
        "Text selection mode is active."
    )
    assert sidebar.document_text_controls.detail_label.text() == (
        "Drag over the page to capture text."
    )
    assert sidebar.document_text_controls.copy_button._enabled is False
    assert sidebar.document_text_controls.copy_selection_button._enabled is False
    assert sidebar.document_text_controls.clear_selection_button._enabled is False


def test_signing_workspace_sidebar_hides_text_selection_checkbox() -> None:
    sidebar = _build_sidebar()

    assert sidebar.document_text_controls.select_mode_checkbox.visible is False
    assert sidebar.document_text_controls.copy_selection_button.visible is False
    assert sidebar.document_text_controls.clear_selection_button.visible is False


def test_signing_workspace_sidebar_does_not_reemit_hidden_checkbox_sync() -> None:
    calls = []
    sidebar = _build_sidebar(on_text_selection_mode_changed=calls.append)

    sidebar.apply_document_review_workspace_state(
        _build_empty_workspace_state(),
        can_copy_text=False,
    )

    assert calls == []

    sidebar._handle_text_selection_mode_changed(1, on_text_selection_mode_changed=calls.append)

    assert calls == [True]
