"""Shell-owned caller-facing port for one live signing workspace."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from foliaseal.application import SigningDraftWorkflow
from foliaseal.application.certificate_catalog_repository import CertificateCatalogRepository
from foliaseal.application.certificate_models import CertificateCatalog
from foliaseal.application.document_review import DocumentReviewSummary
from foliaseal.application.document_review_workspace import DocumentReviewWorkspaceState
from foliaseal.application.document_safety import LinkDecision
from foliaseal.application.document_text_selection import DocumentTextSelectionState
from foliaseal.application.reusable_signing_objects import ReusableSigningObjects
from foliaseal.application.signing_draft_contracts import SigningDraftPreview
from foliaseal.application.signing_material_resolver import CertificateSigningMaterialPort
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.domain.models import SignatureRect, SigningRequest
from foliaseal.infra.config.app_settings_storage import AppSettingsStore
from foliaseal.infra.config.schemas import AppSettings
from foliaseal.presentation.qt.signing_shell import (
    SigningRequestExecutor,
    SigningShellAdapter,
)
from foliaseal.presentation.qt.signing_workspace_diagnostics import SigningWorkspaceSnapshot
from foliaseal.presentation.qt.signing_workspace_testing_port import (
    SigningWorkspaceTestingPort,
)


@dataclass(frozen=True)
class SigningWorkspaceBootstrap:
    """Typed inputs required to create one signing workspace."""

    viewer_workflow: ViewerWorkflow
    signing_workflow: SigningDraftWorkflow
    app_settings: AppSettings
    reusable_objects: ReusableSigningObjects
    app_settings_store: AppSettingsStore | None = None
    certificate_catalog_store: CertificateCatalogRepository | None = None
    certificate_material_port: CertificateSigningMaterialPort | None = None
    sign_executor: SigningRequestExecutor | None = None
    on_sign_request: Callable[[SigningRequest], None] | None = None
    on_open_signed_output: Callable[[str | Path], Any | None] | None = None
    on_error: Callable[[str], None] | None = None
    on_status_change: Callable[[str], None] | None = None
    on_external_link_confirmation: Callable[[LinkDecision], Any] | None = None
    on_source_reload: Callable[[], Any] | None = None
    on_source_ignore: Callable[[], Any] | None = None
    on_source_locate: Callable[[], Any] | None = None
    on_source_close: Callable[[], Any] | None = None
    on_open_signature_library: Callable[[], Any] | None = None
    untrusted_recovery: bool = False


class SigningWorkspacePort(Protocol):
    """Explicit caller-facing contract for an active signing workspace."""

    def has_unsaved_changes(self) -> bool:
        """Return whether user-authored signing values differ from the clean baseline."""

    def discard_draft(self) -> None:
        """Discard the in-memory draft before its workspace is disposed."""

    def cleanup_recovery_artifact(self) -> None:
        """Release any app-owned preserved recovery artifact before disposal."""

    def clear_session_secrets(self) -> None:
        """Clear credentials retained only for the current signing session."""

    def choose_output_pdf_path(self) -> str | None:
        """Drive the shell's Save As behavior."""

    def has_explicit_output_pdf_path(self) -> bool:
        """Return whether the user has accepted an output path for this draft."""

    def apply_app_settings(self, settings: AppSettings) -> None:
        """Apply updated app settings to the live shell."""

    def refresh_certificate_configurations(self) -> CertificateCatalog:
        """Refresh live certificate configuration choices."""

    def refresh_signature_profiles(self) -> None:
        """Refresh reusable signing-profile and preset choices."""

    def open_reusable_object_editor(self) -> bool:
        """Open the contextual reusable-object editor for the active PDF."""

    def set_document_text_selection_mode(self, enabled: bool) -> bool:
        """Toggle document text-selection mode for the live shell."""

    def document_text_selection_mode_enabled(self) -> bool:
        """Return whether document text-selection mode is active."""

    def can_copy_selected_document_text(self) -> bool:
        """Return whether the current document selection can be copied."""

    def copy_selected_document_text(self) -> str | None:
        """Copy the current arbitrary text selection, if any."""


class SigningWorkspaceSessionPort(Protocol):
    """Primary review/place/preview/sign flow for one active workspace."""

    def refresh_viewer(self) -> None: ...
    def refresh_document_review(self) -> DocumentReviewSummary: ...
    def document_review_state(self) -> DocumentReviewWorkspaceState: ...
    def select_document_review_item(self, signature_id: str) -> DocumentReviewWorkspaceState: ...
    def clear_document_review_highlight(self) -> None: ...
    def set_viewer_interaction_mode(self, mode: str) -> str: ...
    def can_place_signature_placement(self) -> bool: ...
    def can_adjust_signature_placement(self) -> bool: ...
    def can_remove_signature_placement(self) -> bool: ...
    def remove_signature_placement(self) -> bool: ...
    def can_undo_placement(self) -> bool: ...
    def can_redo_placement(self) -> bool: ...
    def undo_placement(self) -> SignatureRect | None: ...
    def redo_placement(self) -> SignatureRect | None: ...

    def set_signature_rect(
        self,
        *,
        page_index: int,
        left_pt: float,
        bottom_pt: float,
        width_pt: float,
        height_pt: float,
    ) -> SignatureRect: ...

    def select_signature_field(self, field_name: str, signature_rect: SignatureRect) -> None: ...

    def apply_signature_rect_placement(self, signature_rect: SignatureRect) -> None: ...
    def preview(self) -> SigningDraftPreview: ...
    def snapshot(self) -> SigningWorkspaceSnapshot: ...
    def submit_sign_request(self) -> SigningRequest | None: ...
    def can_submit_sign_request(self) -> bool: ...
    def open_signed_output(self) -> str | None: ...
    def go_to_previous_page(self) -> None: ...
    def go_to_next_page(self) -> None: ...
    def can_go_previous_page(self) -> bool: ...
    def can_go_next_page(self) -> bool: ...
    def go_back_link(self) -> None: ...
    def go_forward_link(self) -> None: ...
    def can_go_back_link(self) -> bool: ...
    def can_go_forward_link(self) -> bool: ...
    def reset_zoom_view(self) -> None: ...
    def zoom_in_view(self) -> None: ...
    def zoom_out_view(self) -> None: ...
    def fit_page_view(self) -> None: ...
    def fit_width_view(self) -> None: ...
    def focus_document_search(self) -> None: ...
    def can_select_all_document_text(self) -> bool: ...
    def select_all_document_text(self) -> DocumentTextSelectionState: ...
    def focus(self) -> None: ...


class WorkspaceViewPort(Protocol):
    """Opaque lifecycle view; callers cannot inspect child widgets."""

    def mount_target(self) -> object: ...
    def dispose(self) -> None: ...
    def capture_ui_settings(self, settings: AppSettings) -> AppSettings: ...


class SigningWorkspaceFactory(Protocol):
    """Create a live signing workspace from typed bootstrap inputs."""

    def create(self, bootstrap: SigningWorkspaceBootstrap) -> SigningWorkspaceBundle:
        """Build and return the active workspace port."""


@dataclass(frozen=True)
class SigningWorkspaceBundle:
    """Caller-facing bundle for one live workspace instance."""

    maintenance: SigningWorkspacePort
    session: SigningWorkspaceSessionPort
    testing: SigningWorkspaceTestingPort
    view: WorkspaceViewPort


@dataclass(frozen=True)
class QtWorkspaceView:
    """Qt-local lifecycle adapter around the composite shell facade."""

    shell: Any
    _disposed: bool = field(default=False, init=False, compare=False)

    def mount_target(self) -> object:
        return getattr(self.shell, "container", self.shell)

    def dispose(self) -> None:
        if self._disposed:
            return
        object.__setattr__(self, "_disposed", True)
        close = getattr(self.shell, "close", None)
        if callable(close):
            close()
        container = getattr(self.shell, "container", self.shell)
        delete_later = getattr(container, "deleteLater", None)
        if callable(delete_later):
            delete_later()

    def capture_ui_settings(self, settings: AppSettings) -> AppSettings:
        capture = getattr(self.shell, "capture_ui_settings", None)
        if not callable(capture):
            return settings
        return capture(settings)


@dataclass(frozen=True)
class QtSigningWorkspacePort:
    """Port adapter over the concrete Qt signing shell widget."""

    shell_widget: Any

    def has_unsaved_changes(self) -> bool:
        return bool(self.shell_widget.has_unsaved_changes())

    def discard_draft(self) -> None:
        self.shell_widget.discard_draft()

    def cleanup_recovery_artifact(self) -> None:
        self.shell_widget.cleanup_recovery_artifact()

    def clear_session_secrets(self) -> None:
        self.shell_widget.clear_session_secrets()

    def choose_output_pdf_path(self) -> str | None:
        return self.shell_widget.choose_output_pdf_path()

    def has_explicit_output_pdf_path(self) -> bool:
        return bool(self.shell_widget.has_explicit_output_pdf_path())

    def apply_app_settings(self, settings: AppSettings) -> None:
        self.shell_widget.apply_app_settings(settings)

    def refresh_certificate_configurations(self) -> CertificateCatalog:
        return self.shell_widget.refresh_certificate_configurations()

    def refresh_signature_profiles(self) -> None:
        self.shell_widget.refresh_signature_profiles()

    def open_reusable_object_editor(self) -> bool:
        return self.shell_widget.open_reusable_object_editor()

    def set_document_text_selection_mode(self, enabled: bool) -> bool:
        return self.shell_widget.set_document_text_selection_mode(enabled)

    def document_text_selection_mode_enabled(self) -> bool:
        return bool(self.shell_widget.document_text_selection_mode_enabled())

    def can_copy_selected_document_text(self) -> bool:
        return bool(self.shell_widget.can_copy_selected_document_text())

    def copy_selected_document_text(self) -> str | None:
        return self.shell_widget.copy_selected_document_text()


@dataclass(frozen=True)
class QtSigningWorkspaceSessionPort:
    """Typed adapter over the shell's primary workflow methods."""

    shell_widget: Any

    def refresh_viewer(self) -> None:
        self.shell_widget.refresh_viewer()

    def refresh_document_review(self) -> DocumentReviewSummary:
        return self.shell_widget.refresh_document_review()

    def document_review_state(self) -> DocumentReviewWorkspaceState:
        getter = getattr(self.shell_widget, "document_review_state", None)
        if not callable(getter):
            raise RuntimeError("The active shell does not expose document review state.")
        return getter()

    def select_document_review_item(self, signature_id: str) -> DocumentReviewWorkspaceState:
        selector = getattr(self.shell_widget, "select_document_review_item", None)
        if not callable(selector):
            raise RuntimeError("The active shell does not expose document review selection.")
        return selector(signature_id)

    def clear_document_review_highlight(self) -> None:
        clearer = getattr(self.shell_widget, "clear_document_review_highlight", None)
        if callable(clearer):
            clearer()

    def set_viewer_interaction_mode(self, mode: str) -> str:
        return self.shell_widget.set_viewer_interaction_mode(mode)

    def can_place_signature_placement(self) -> bool:
        capability = getattr(self.shell_widget, "can_place_signature_placement", None)
        return bool(capability()) if callable(capability) else False

    def can_adjust_signature_placement(self) -> bool:
        capability = getattr(self.shell_widget, "can_adjust_signature_placement", None)
        return bool(capability()) if callable(capability) else False

    def can_remove_signature_placement(self) -> bool:
        capability = getattr(self.shell_widget, "can_remove_signature_placement", None)
        return bool(capability()) if callable(capability) else False

    def remove_signature_placement(self) -> bool:
        remove = getattr(self.shell_widget, "remove_signature_placement", None)
        return bool(remove()) if callable(remove) else False

    def can_undo_placement(self) -> bool:
        capability = getattr(self.shell_widget, "can_undo_placement", None)
        return bool(capability()) if callable(capability) else False

    def can_redo_placement(self) -> bool:
        capability = getattr(self.shell_widget, "can_redo_placement", None)
        return bool(capability()) if callable(capability) else False

    def undo_placement(self) -> SignatureRect | None:
        undo = getattr(self.shell_widget, "undo_placement", None)
        return undo() if callable(undo) else None

    def redo_placement(self) -> SignatureRect | None:
        redo = getattr(self.shell_widget, "redo_placement", None)
        return redo() if callable(redo) else None

    def set_signature_rect(
        self,
        *,
        page_index: int,
        left_pt: float,
        bottom_pt: float,
        width_pt: float,
        height_pt: float,
    ) -> SignatureRect:
        return self.shell_widget.set_signature_rect(
            page_index=page_index,
            left_pt=left_pt,
            bottom_pt=bottom_pt,
            width_pt=width_pt,
            height_pt=height_pt,
        )

    def apply_signature_rect_placement(self, signature_rect: SignatureRect) -> None:
        self.shell_widget.apply_signature_rect_placement(signature_rect)

    def select_signature_field(self, field_name: str, signature_rect: SignatureRect) -> None:
        self.shell_widget.select_signature_field(field_name, signature_rect)

    def preview(self) -> SigningDraftPreview:
        return self.shell_widget.preview()

    def snapshot(self) -> SigningWorkspaceSnapshot:
        return self.shell_widget.snapshot()

    def submit_sign_request(self) -> SigningRequest | None:
        return self.shell_widget.submit_sign_request()

    def can_submit_sign_request(self) -> bool:
        capability = getattr(self.shell_widget, "can_submit_sign_request", None)
        if callable(capability):
            return bool(capability())
        try:
            return bool(self.shell_widget.preview().can_submit)
        except Exception:
            return False

    def open_signed_output(self) -> str | None:
        return self.shell_widget.open_signed_output()

    def go_to_previous_page(self) -> None:
        self.shell_widget.go_to_previous_page()

    def go_to_next_page(self) -> None:
        self.shell_widget.go_to_next_page()

    def can_go_previous_page(self) -> bool:
        capability = getattr(self.shell_widget, "can_go_previous_page", None)
        return bool(capability()) if callable(capability) else False

    def can_go_next_page(self) -> bool:
        capability = getattr(self.shell_widget, "can_go_next_page", None)
        return bool(capability()) if callable(capability) else False

    def go_back_link(self) -> None:
        self.shell_widget.go_back_link()

    def go_forward_link(self) -> None:
        self.shell_widget.go_forward_link()

    def can_go_back_link(self) -> bool:
        capability = getattr(self.shell_widget, "can_go_back_link", None)
        return bool(capability()) if callable(capability) else False

    def can_go_forward_link(self) -> bool:
        capability = getattr(self.shell_widget, "can_go_forward_link", None)
        return bool(capability()) if callable(capability) else False

    def reset_zoom_view(self) -> None:
        self.shell_widget.reset_zoom_view()

    def zoom_in_view(self) -> None:
        self.shell_widget.zoom_in_view()

    def zoom_out_view(self) -> None:
        self.shell_widget.zoom_out_view()

    def fit_page_view(self) -> None:
        self.shell_widget.fit_page_view()

    def fit_width_view(self) -> None:
        self.shell_widget.fit_width_view()

    def focus_document_search(self) -> None:
        self.shell_widget.focus_document_search()

    def can_select_all_document_text(self) -> bool:
        capability = getattr(self.shell_widget, "can_select_all_document_text", None)
        return bool(capability()) if callable(capability) else False

    def select_all_document_text(self) -> DocumentTextSelectionState:
        selector = getattr(self.shell_widget, "select_all_document_text", None)
        if not callable(selector):
            raise RuntimeError("The active shell does not expose viewer Select All.")
        return selector()

    def focus(self) -> None:
        self.shell_widget.setFocus()


def build_qt_signing_workspace_bundle(shell_widget: Any) -> SigningWorkspaceBundle:
    """Adapt one Qt shell widget into the typed workspace bundle at the Qt edge."""
    testing_adapter = shell_widget.testing_adapter
    return SigningWorkspaceBundle(
        maintenance=QtSigningWorkspacePort(shell_widget=shell_widget),
        session=QtSigningWorkspaceSessionPort(shell_widget=shell_widget),
        testing=testing_adapter,
        view=QtWorkspaceView(shell=shell_widget),
    )


class QtSigningWorkspaceFactory:
    """Production factory that wraps the Qt signing shell behind a port."""

    def __init__(
        self,
        shell_adapter_factory: Callable[[], SigningShellAdapter] | None = None,
    ) -> None:
        self._shell_adapter_factory = shell_adapter_factory or SigningShellAdapter

    def create(self, bootstrap: SigningWorkspaceBootstrap) -> SigningWorkspaceBundle:
        if bootstrap.reusable_objects is None:
            raise ValueError("reusable_objects is required to create a signing workspace.")
        shell_widget = self._shell_adapter_factory().create_from_bootstrap(bootstrap)
        return build_qt_signing_workspace_bundle(shell_widget)
