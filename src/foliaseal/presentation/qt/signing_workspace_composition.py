"""Typed workspace composition helper for the Qt signing shell."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from foliaseal.application import (
    WorkspaceInteractionSession,
)
from foliaseal.application.document_review import (
    DocumentReviewInspector,
    PyHankoDocumentReviewInspector,
)
from foliaseal.application.document_review_workspace import (
    DocumentReviewWorkspaceSession,
    DocumentTextWorkspaceState,
)
from foliaseal.application.document_text_search import (
    DocumentTextSearchEngine,
    DocumentTextSearchSession,
)
from foliaseal.application.document_text_selection import (
    DocumentTextSelectionEngine,
    DocumentTextSelectionSession,
)
from foliaseal.application.signing_material_resolver import CertificateSecretProvider
from foliaseal.application.viewer_interaction_session import (
    ViewerInteractionSession,
)
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.domain.models import (
    SigningRequest,
)
from foliaseal.infra.config.app_settings_storage import AppSettingsStore
from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
from foliaseal.infra.config.schemas import (
    AppSettings,
    CertificateCatalog,
    SignaturePresetCatalog,
)
from foliaseal.infra.document_text_search import QtPdfDocumentTextSearchEngine
from foliaseal.infra.document_text_selection import QtPdfDocumentTextSelectionEngine
from foliaseal.presentation.qt.signing_action_boundary import (
    SigningActionBoundary,
)
from foliaseal.presentation.qt.signing_action_coordinator import (
    SigningActionCoordinator,
)
from foliaseal.presentation.qt.signing_workspace_action_bridge import (
    SigningWorkspaceActionBridge,
)
from foliaseal.presentation.qt.signing_workspace_compatibility_surface import (
    SigningWorkspaceCompatibilitySurface,
)
from foliaseal.presentation.qt.signing_workspace_interaction_bridge import (
    SigningWorkspaceInteractionBridge,
)
from foliaseal.presentation.qt.signing_workspace_orchestrator import (
    SigningWorkspaceOrchestrator,
)
from foliaseal.presentation.qt.signing_workspace_properties_panel import (
    SignaturePropertiesPanel,
)
from foliaseal.presentation.qt.signing_workspace_review_bridge import (
    SigningWorkspaceReviewBridge,
)
from foliaseal.presentation.qt.signing_workspace_runtime import (
    SigningWorkspaceRuntime,
)
from foliaseal.presentation.qt.signing_workspace_shell_surface import (
    SigningWorkspaceShellSurface,
)
from foliaseal.presentation.qt.signing_workspace_sidebar import (
    SigningWorkspaceSidebar,
)
from foliaseal.resources.icons import icon_path

if TYPE_CHECKING:
    from foliaseal.application import SigningDraftWorkflow
    from foliaseal.presentation.qt.signing_shell import (
        QtSigningWidgetBindings,
        SigningRequestExecutor,
    )


@dataclass(frozen=True)
class SigningWorkspaceComposition:
    """Concrete collaborators and bootstrap behavior for one shell instance."""

    document_review_inspector: DocumentReviewInspector
    viewer_interaction_session: ViewerInteractionSession
    document_review_workspace: DocumentReviewWorkspaceSession
    workspace_interaction_session: WorkspaceInteractionSession
    viewer_navigation_controls: Any
    viewer_widget: Any
    properties_panel: SignaturePropertiesPanel
    sidebar: SigningWorkspaceSidebar
    document_text_controls: Any
    properties_scroll: Any
    sign_button: Any
    result_label: Any
    review_bridge: SigningWorkspaceReviewBridge
    signing_action_coordinator: SigningActionCoordinator
    signing_action_boundary: SigningActionBoundary
    action_bridge: SigningWorkspaceActionBridge
    interaction_bridge: SigningWorkspaceInteractionBridge
    orchestrator: SigningWorkspaceOrchestrator
    runtime: SigningWorkspaceRuntime
    compatibility_surface: SigningWorkspaceCompatibilitySurface
    shell_surface: SigningWorkspaceShellSurface
    main_row: Any

    def bootstrap(self) -> None:
        self.orchestrator.bootstrap()


def build_signing_workspace_composition(
    *,
    bindings: QtSigningWidgetBindings,
    widget: Any,
    layout: Any,
    viewer_workflow: ViewerWorkflow,
    signing_workflow: SigningDraftWorkflow,
    certificate_catalog: CertificateCatalog | None = None,
    certificate_catalog_store: CertificateCatalogStore | None = None,
    certificate_secret_provider: CertificateSecretProvider | None = None,
    preset_catalog: SignaturePresetCatalog | None = None,
    preset_catalog_store: SignaturePresetCatalogStore | None = None,
    app_settings: AppSettings,
    app_settings_store: AppSettingsStore | None = None,
    document_review_inspector: DocumentReviewInspector | None = None,
    document_text_selection_engine: DocumentTextSelectionEngine | None = None,
    document_text_search_engine: DocumentTextSearchEngine | None = None,
    sign_executor: SigningRequestExecutor | None = None,
    on_sign_request: Callable[[SigningRequest], None] | None = None,
    on_open_signed_output: Callable[[str], Any] | None = None,
    on_copy_text: Callable[[str], Any] | None = None,
    on_error: Callable[[str], None] | None = None,
    on_status_change: Callable[[str], None] | None = None,
    viewer_widget_builder: Callable[..., Any],
    runtime: SigningWorkspaceRuntime,
    choose_output_pdf_path: Callable[[], str | None],
    submit_sign_request: Callable[[], SigningRequest | None],
    open_signed_output: Callable[[], str | None],
    search_document_text: Callable[[], Any],
    previous_document_text_match: Callable[[], Any],
    next_document_text_match: Callable[[], Any],
    copy_current_document_text_match: Callable[[], str | None],
    set_document_text_selection_mode: Callable[[bool], bool],
    copy_selected_document_text: Callable[[], str | None],
    clear_selected_document_text: Callable[[], Any],
    get_app_settings: Callable[[], AppSettings],
    set_app_settings: Callable[[AppSettings], None],
) -> SigningWorkspaceComposition:
    def _safe_int(text: str) -> int | None:
        try:
            return int(text)
        except (TypeError, ValueError):
            return None

    def _set_text(widget: Any, value: str) -> None:
        setter = getattr(widget, "setText", None)
        if callable(setter):
            setter(value)

    def _text(widget: Any) -> str:
        getter = getattr(widget, "text", None)
        return str(getter()) if callable(getter) else ""

    inspector = document_review_inspector or PyHankoDocumentReviewInspector()
    viewer_interaction_session = ViewerInteractionSession(
        viewer_workflow=viewer_workflow
    )
    document_text_selection_session = DocumentTextSelectionSession(
        input_pdf_path=viewer_workflow.document_path,
        selection_engine=document_text_selection_engine
        or QtPdfDocumentTextSelectionEngine(),
    )
    document_text_search_session = DocumentTextSearchSession(
        input_pdf_path=viewer_workflow.document_path,
        search_engine=document_text_search_engine or QtPdfDocumentTextSearchEngine(),
    )
    document_review_workspace = DocumentReviewWorkspaceSession(
        document_review_inspector=inspector,
        document_text_search_session=document_text_search_session,
        document_text_selection_session=document_text_selection_session,
        input_pdf_path=viewer_workflow.document_path,
    )
    workspace_interaction_session = WorkspaceInteractionSession(
        viewer_workflow=viewer_workflow,
        viewer_interaction_session=viewer_interaction_session,
        document_review_workspace=document_review_workspace,
    )
    viewer_widget = viewer_widget_builder(
        workflow=viewer_workflow,
        on_selection=runtime.on_viewer_selection,
        on_error=runtime.on_viewer_error,
        on_interaction=runtime.on_viewer_interaction,
    )
    viewer_navigation_container = bindings.q_widget()
    viewer_navigation_row = bindings.q_hbox_layout(viewer_navigation_container)
    viewer_navigation_row.setContentsMargins(0, 0, 0, 0)
    viewer_navigation_row.setSpacing(4)
    previous_page_button = bindings.q_push_button("<")
    next_page_button = bindings.q_push_button(">")
    page_input = bindings.q_line_edit("1")
    total_pages_label = bindings.q_label(f"of {viewer_workflow.session.page_count}")
    interaction_mode_label = bindings.q_label(
        "Placement mode — drag on the page to draw or resize the signature"
    )
    text_selection_button = bindings.q_push_button("")
    copy_selection_button = bindings.q_push_button("")
    for button in (previous_page_button, next_page_button):
        button_fixed_width = getattr(button, "setFixedWidth", None)
        if callable(button_fixed_width):
            button_fixed_width(28)
    for button, width in ((text_selection_button, 32), (copy_selection_button, 32)):
        button_fixed_width = getattr(button, "setFixedWidth", None)
        if callable(button_fixed_width):
            button_fixed_width(width)
    fixed_width = getattr(page_input, "setFixedWidth", None)
    if callable(fixed_width):
        fixed_width(44)
    set_checkable = getattr(text_selection_button, "setCheckable", None)
    if callable(set_checkable):
        set_checkable(True)
    for button, tooltip, icon_name in (
        (text_selection_button, "Text selection mode", "text-select.svg"),
        (copy_selection_button, "Copy selected text", "copy.svg"),
    ):
        set_icon = getattr(button, "setIcon", None)
        if callable(set_icon):
            set_icon(bindings.q_icon(icon_path(icon_name)))
        set_tooltip = getattr(button, "setToolTip", None)
        if callable(set_tooltip):
            set_tooltip(tooltip)
    previous_page_button.setEnabled(False)
    next_page_button.setEnabled(viewer_workflow.session.page_count > 1)
    copy_selection_button.setEnabled(False)
    viewer_navigation_row.addWidget(previous_page_button)
    viewer_navigation_row.addWidget(page_input)
    viewer_navigation_row.addWidget(total_pages_label)
    viewer_navigation_row.addWidget(next_page_button)
    if hasattr(viewer_navigation_row, "addSpacing"):
        viewer_navigation_row.addSpacing(8)
    else:
        toolbar_gap = bindings.q_widget()
        set_fixed_width = getattr(toolbar_gap, "setFixedWidth", None)
        if callable(set_fixed_width):
            set_fixed_width(8)
        viewer_navigation_row.addWidget(toolbar_gap)
    viewer_navigation_row.addWidget(text_selection_button)
    viewer_navigation_row.addWidget(copy_selection_button)
    viewer_navigation_row.addWidget(interaction_mode_label)
    if hasattr(viewer_navigation_row, "addStretch"):
        viewer_navigation_row.addStretch()

    def refresh_page_navigation_state() -> None:
        current_page = viewer_workflow.session.current_page
        page_count = viewer_workflow.session.page_count
        previous_page_button.setEnabled(current_page > 0)
        next_page_button.setEnabled(current_page < (page_count - 1))
        _set_text(page_input, str(current_page + 1))
        _set_text(total_pages_label, f"of {page_count}")

    def go_previous_page() -> None:
        target = max(viewer_workflow.session.current_page - 1, 0)
        runtime.refresh_review_jump_to_page_index(target)

    def go_next_page() -> None:
        target = min(
            viewer_workflow.session.current_page + 1,
            viewer_workflow.session.page_count - 1,
        )
        runtime.refresh_review_jump_to_page_index(target)

    def jump_to_entered_page() -> None:
        page_number = _safe_int(_text(page_input).strip())
        if page_number is None:
            refresh_page_navigation_state()
            return
        target = page_number - 1
        if target < 0 or target >= viewer_workflow.session.page_count:
            refresh_page_navigation_state()
            return
        runtime.refresh_review_jump_to_page_index(target)

    def refresh_text_selection_toolbar_state(
        document_text_state: DocumentTextWorkspaceState,
    ) -> None:
        set_checked = getattr(text_selection_button, "setChecked", None)
        if callable(set_checked):
            set_checked(document_text_state.selection_mode_enabled)
        copy_selection_button.setEnabled(document_text_state.selection_state.can_copy)
        _set_text(
            interaction_mode_label,
            (
                "Text selection mode — drag across PDF text to select and copy"
                if document_text_state.selection_mode_enabled
                else "Placement mode — drag on the page to draw or resize the signature"
            ),
        )

    def toggle_text_selection_mode() -> None:
        is_checked = getattr(text_selection_button, "isChecked", None)
        enabled = bool(is_checked()) if callable(is_checked) else False
        result = runtime.set_document_text_selection_mode(enabled)
        set_checked = getattr(text_selection_button, "setChecked", None)
        if callable(set_checked):
            set_checked(result)

    previous_page_button.clicked.connect(go_previous_page)  # type: ignore[attr-defined]
    next_page_button.clicked.connect(go_next_page)  # type: ignore[attr-defined]
    text_selection_button.clicked.connect(toggle_text_selection_mode)  # type: ignore[attr-defined]
    copy_selection_button.clicked.connect(copy_selected_document_text)  # type: ignore[attr-defined]
    return_pressed = getattr(page_input, "returnPressed", None)
    if hasattr(return_pressed, "connect"):
        return_pressed.connect(jump_to_entered_page)  # type: ignore[attr-defined]
    viewer_navigation_controls = {
        "container": viewer_navigation_container,
        "previous_page_button": previous_page_button,
        "page_input": page_input,
        "total_pages_label": total_pages_label,
        "next_page_button": next_page_button,
        "text_selection_button": text_selection_button,
        "copy_selection_button": copy_selection_button,
        "interaction_mode_label": interaction_mode_label,
    }
    properties_panel = SignaturePropertiesPanel(
        bindings=bindings,
        workflow=signing_workflow,
        certificate_catalog=certificate_catalog,
        certificate_catalog_store=certificate_catalog_store,
        certificate_secret_provider=certificate_secret_provider,
        preset_catalog=preset_catalog,
        preset_catalog_store=preset_catalog_store,
        app_settings=app_settings,
        on_change=runtime.on_panel_change,
        on_page_change=runtime.on_page_change,
        on_error=runtime.emit_error,
    )
    sidebar = SigningWorkspaceSidebar(
        bindings=bindings,
        properties_widget=properties_panel.container,
        on_choose_output=choose_output_pdf_path,
        on_sign=submit_sign_request,
        on_open_signed_output=open_signed_output,
        on_find_text=search_document_text,
        on_previous_text_match=previous_document_text_match,
        on_next_text_match=next_document_text_match,
        on_copy_text_match=copy_current_document_text_match,
        on_review_signature_selected=runtime.on_document_review_signature_selected,
        on_text_selection_mode_changed=set_document_text_selection_mode,
        on_copy_selected_text=copy_selected_document_text,
        on_clear_selected_text=clear_selected_document_text,
    )
    document_text_controls = sidebar.document_text_controls
    properties_scroll = sidebar.properties_scroll
    sign_button = sidebar.sign_button
    result_label = sidebar.result_label
    review_bridge = SigningWorkspaceReviewBridge(
        sidebar=sidebar,
        viewer_widget=viewer_widget,
        document_review_workspace=document_review_workspace,
        on_jump_to_page_index=runtime.refresh_review_jump_to_page_index,
        can_copy_text=on_copy_text is not None,
        on_document_text_state_changed=refresh_text_selection_toolbar_state,
    )
    signing_action_coordinator = SigningActionCoordinator(
        workflow=signing_workflow,
        apply_changes=properties_panel.apply_changes,
        is_ready_to_sign=properties_panel.is_ready_to_sign,
        validation_text=properties_panel.validation_text,
        sign_executor=sign_executor,
        on_sign_request=on_sign_request,
        can_open_signed_output=on_open_signed_output is not None,
    )
    signing_action_boundary = SigningActionBoundary(
        coordinator=signing_action_coordinator,
        emit_error=runtime.emit_error,
        on_error=on_error,
        on_status_change=on_status_change,
        on_open_signed_output=on_open_signed_output,
    )
    action_bridge = SigningWorkspaceActionBridge(
        widget=widget,
        bindings=bindings,
        sidebar=sidebar,
        properties_panel=properties_panel,
        signing_action_boundary=signing_action_boundary,
        draft_workflow=signing_workflow,
        app_settings_getter=get_app_settings,
    )
    interaction_bridge = SigningWorkspaceInteractionBridge(
        review_bridge=review_bridge,
        viewer_widget=viewer_widget,
        viewer_interaction_session=viewer_interaction_session,
        apply_placement_context=runtime.apply_placement_context,
        apply_signature_rect=lambda signature_rect, notify: (
            properties_panel.set_signature_rect(
                signature_rect,
                notify=notify,
            )
        ),
        sync_signature_overlay=runtime.sync_signature_overlay,
        refresh_preview=lambda: properties_panel.refresh_preview(),
        load_signing_action_state=action_bridge.reload_state,
        invalidate_signing_action_state=action_bridge.invalidate_state,
        emit_error=runtime.emit_error,
    )
    shell_surface = SigningWorkspaceShellSurface(
        set_app_settings=set_app_settings,
        set_document_text_selection_mode=runtime.set_document_text_selection_mode,
        copy_selected_document_text=runtime.copy_selected_document_text,
        open_reusable_object_editor=properties_panel.open_refinement_dialog,
        action_bridge=action_bridge,
        initial_app_settings=app_settings,
    )
    compatibility_surface = SigningWorkspaceCompatibilitySurface(
        widget=widget,
        runtime=runtime,
        properties_panel=properties_panel,
        viewer_widget=viewer_widget,
        viewer_navigation_controls=viewer_navigation_controls,
        properties_scroll=properties_scroll,
        sidebar_container=sidebar.container,
        sidebar_surface=sidebar.surface,
        shell_surface=shell_surface,
    )
    orchestrator = SigningWorkspaceOrchestrator(
        interaction_bridge=interaction_bridge,
        compatibility_surface=compatibility_surface,
        shell_surface=shell_surface,
        review_bridge=review_bridge,
        document_review_workspace=document_review_workspace,
        action_bridge=action_bridge,
        refresh_viewer=runtime.refresh_viewer,
    )
    runtime.bind(
        viewer_interaction_session=viewer_interaction_session,
        viewer_workflow=viewer_workflow,
        document_review_workspace=document_review_workspace,
        workspace_interaction_session=workspace_interaction_session,
        review_bridge=review_bridge,
        orchestrator=orchestrator,
        properties_panel=properties_panel,
        viewer_widget=viewer_widget,
        document_text_query_input=document_text_controls.query_input,
        sign_button=sign_button,
        refresh_sign_button_state=action_bridge.reload_state,
        refresh_page_navigation_state=refresh_page_navigation_state,
        result_label=result_label,
    )
    refresh_page_navigation_state()
    viewer_column_container = bindings.q_widget()
    viewer_column = bindings.q_vbox_layout(viewer_column_container)
    viewer_column.setContentsMargins(0, 0, 0, 0)
    viewer_column.setSpacing(4)
    viewer_column.addWidget(viewer_navigation_container)
    viewer_column.addWidget(viewer_widget)
    main_row = bindings.q_hbox_layout()
    main_row.setContentsMargins(0, 0, 0, 0)
    main_row.setSpacing(8)
    main_row.addWidget(viewer_column_container, 3)
    main_row.addWidget(sidebar.container, 2)
    layout.addLayout(main_row)
    return SigningWorkspaceComposition(
        document_review_inspector=inspector,
        viewer_interaction_session=viewer_interaction_session,
        document_review_workspace=document_review_workspace,
        workspace_interaction_session=workspace_interaction_session,
        viewer_navigation_controls=viewer_navigation_controls,
        viewer_widget=viewer_widget,
        properties_panel=properties_panel,
        sidebar=sidebar,
        document_text_controls=document_text_controls,
        properties_scroll=properties_scroll,
        sign_button=sign_button,
        result_label=result_label,
        review_bridge=review_bridge,
        signing_action_coordinator=signing_action_coordinator,
        signing_action_boundary=signing_action_boundary,
        action_bridge=action_bridge,
        interaction_bridge=interaction_bridge,
        orchestrator=orchestrator,
        runtime=runtime,
        compatibility_surface=compatibility_surface,
        shell_surface=shell_surface,
        main_row=main_row,
    )
