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
    runtime: SigningWorkspaceRuntime
    compatibility_surface: SigningWorkspaceCompatibilitySurface
    shell_surface: SigningWorkspaceShellSurface
    main_row: Any

    def bootstrap(self) -> None:
        self.compatibility_surface.install_widget_exports()
        self.shell_surface.install_port_exports()
        self.compatibility_surface.refresh_viewer()
        self.review_bridge.apply_state(self.document_review_workspace.load())
        self.action_bridge.reload_state()


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
    runtime.bind(
        viewer_interaction_session=viewer_interaction_session,
        document_review_workspace=document_review_workspace,
        workspace_interaction_session=workspace_interaction_session,
        review_bridge=review_bridge,
        interaction_bridge=interaction_bridge,
        viewer_widget=viewer_widget,
        result_label=result_label,
    )
    compatibility_surface = SigningWorkspaceCompatibilitySurface(
        widget=widget,
        properties_panel=properties_panel,
        viewer_widget=viewer_widget,
        properties_scroll=properties_scroll,
        sidebar_container=sidebar.container,
        sidebar_surface=sidebar.surface,
        sign_button=sign_button,
        document_text_query_input=document_text_controls.query_input,
        on_copy_text=on_copy_text,
        draft_workflow=signing_workflow,
        document_review_workspace=document_review_workspace,
        review_bridge=review_bridge,
        viewer_workflow=viewer_workflow,
        viewer_interaction_session=viewer_interaction_session,
        workspace_interaction_session=workspace_interaction_session,
        interaction_bridge=interaction_bridge,
    )
    shell_surface = SigningWorkspaceShellSurface(
        widget=widget,
        set_app_settings=set_app_settings,
        action_bridge=action_bridge,
        initial_app_settings=app_settings,
    )
    main_row = bindings.q_hbox_layout()
    main_row.setContentsMargins(0, 0, 0, 0)
    main_row.setSpacing(8)
    main_row.addWidget(viewer_widget, 3)
    main_row.addWidget(sidebar.container, 2)
    layout.addLayout(main_row)
    return SigningWorkspaceComposition(
        document_review_inspector=inspector,
        viewer_interaction_session=viewer_interaction_session,
        document_review_workspace=document_review_workspace,
        workspace_interaction_session=workspace_interaction_session,
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
        runtime=runtime,
        compatibility_surface=compatibility_surface,
        shell_surface=shell_surface,
        main_row=main_row,
    )
