"""Compatibility and harness-facing surface for the signing workspace shell."""

from __future__ import annotations

from typing import Any

from foliaseal.domain.models import (
    SignatureAppearance,
    SignatureRect,
    SigningRequest,
    SigningResult,
)
from foliaseal.presentation.qt.signing_workspace_diagnostics import (
    SigningWorkspaceSnapshot,
)
from foliaseal.presentation.qt.signing_workspace_properties_panel import (
    SignaturePropertiesPanel,
)
from foliaseal.presentation.qt.signing_workspace_runtime import (
    SigningWorkspaceRuntime,
)
from foliaseal.presentation.qt.signing_workspace_testing_port import (
    SigningWorkspaceTestingPanelPort,
)


class SigningWorkspaceCompatibilitySurface:
    """Own thin widget exports and the dedicated testing seam."""

    def __init__(
        self,
        *,
        widget: Any,
        runtime: SigningWorkspaceRuntime,
        properties_panel: SignaturePropertiesPanel,
        viewer_widget: Any,
        viewer_navigation_controls: Any,
        properties_scroll: Any,
        sidebar_container: Any,
        sidebar_surface: Any,
    ) -> None:
        self._widget = widget
        self._runtime = runtime
        self._properties_panel = properties_panel
        self._viewer_widget = viewer_widget
        self._viewer_navigation_controls = viewer_navigation_controls
        self._properties_scroll = properties_scroll
        self._sidebar_container = sidebar_container
        self._sidebar_surface = sidebar_surface
        self._testing_adapter = SigningWorkspaceTestingAdapter(self)

    @property
    def properties_panel(self) -> SignaturePropertiesPanel:
        return self._properties_panel

    @property
    def viewer_widget(self) -> Any:
        return self._viewer_widget

    @property
    def sidebar_surface(self) -> Any:
        return self._sidebar_surface

    @property
    def last_signing_result(self) -> Any:
        return getattr(self._widget, "last_signing_result", None)

    @property
    def testing_adapter(self) -> SigningWorkspaceTestingAdapter:
        return self._testing_adapter

    def snapshot(self) -> SigningWorkspaceSnapshot:
        return self._runtime.snapshot(last_signing_result=self.last_signing_result)

    def install_widget_exports(self) -> None:
        self._widget.compat_surface = self  # type: ignore[attr-defined]
        self._widget.testing_adapter = self._testing_adapter  # type: ignore[attr-defined]
        self._widget.properties_panel = self._properties_panel  # type: ignore[attr-defined]
        self._widget.viewer_widget = self._viewer_widget  # type: ignore[attr-defined]
        self._widget.viewer_navigation_controls = self._viewer_navigation_controls  # type: ignore[attr-defined]
        self._widget.properties_scroll = self._properties_scroll  # type: ignore[attr-defined]
        self._widget.sidebar = self._sidebar_container  # type: ignore[attr-defined]
        self._widget.sidebar_surface = self._sidebar_surface  # type: ignore[attr-defined]
        destroyed_signal = getattr(self._widget, "destroyed", None)
        destroy_connect = getattr(destroyed_signal, "connect", None)
        if callable(destroy_connect):
            destroy_connect(lambda *_args: self._properties_panel.dispose())
        self._widget.last_signing_result = None  # type: ignore[attr-defined]
        self._widget.refresh_viewer = self._runtime.refresh_viewer  # type: ignore[attr-defined]
        self._widget.refresh_document_review = (  # type: ignore[attr-defined]
            self._runtime.refresh_document_review
        )
        self._widget.search_document_text = self._runtime.search_document_text  # type: ignore[attr-defined]
        self._widget.next_document_text_match = (  # type: ignore[attr-defined]
            self._runtime.next_document_text_match
        )
        self._widget.previous_document_text_match = (  # type: ignore[attr-defined]
            self._runtime.previous_document_text_match
        )
        self._widget.copy_current_document_text_match = (  # type: ignore[attr-defined]
            self._runtime.copy_current_document_text_match
        )
        self._widget.set_document_text_selection_mode = (  # type: ignore[attr-defined]
            self._runtime.set_document_text_selection_mode
        )
        self._widget.copy_selected_document_text = (  # type: ignore[attr-defined]
            self._runtime.copy_selected_document_text
        )
        self._widget.clear_selected_document_text = (  # type: ignore[attr-defined]
            self._runtime.clear_selected_document_text
        )
        self._widget.set_logical_page_index = self._runtime.set_logical_page_index  # type: ignore[attr-defined]
        self._widget.logical_page_index = self._runtime.logical_page_index  # type: ignore[attr-defined]
        self._widget.set_signature_rect = self._runtime.set_signature_rect  # type: ignore[attr-defined]
        self._widget.signature_rect = self._runtime.signature_rect  # type: ignore[attr-defined]
        self._widget.set_selected_certificate_configuration_id = (  # type: ignore[attr-defined]
            self._runtime.set_selected_certificate_configuration_id
        )
        self._widget.selected_certificate_configuration_id = (  # type: ignore[attr-defined]
            self._runtime.selected_certificate_configuration_id
        )
        self._widget.signature_appearance = self._runtime.signature_appearance  # type: ignore[attr-defined]
        self._widget.set_timestamp_required = self._runtime.set_timestamp_required  # type: ignore[attr-defined]
        self._widget.current_request = self._runtime.current_request  # type: ignore[attr-defined]
        self._widget.is_sign_action_enabled = self._runtime.is_sign_action_enabled  # type: ignore[attr-defined]


class SigningWorkspaceTestingAdapter:
    """Dedicated harness/testing adapter over the live runtime/controller seam."""

    def __init__(self, compatibility_surface: SigningWorkspaceCompatibilitySurface) -> None:
        self._compatibility_surface = compatibility_surface
        self._panel = SigningWorkspaceTestingPanelAdapter(
            compatibility_surface.properties_panel
        )

    @property
    def panel(self) -> SigningWorkspaceTestingPanelPort:
        return self._panel

    def signature_appearance(self) -> SignatureAppearance | None:
        return self._compatibility_surface._runtime.signature_appearance()

    def set_timestamp_required(self, required: bool) -> None:
        self._compatibility_surface._runtime.set_timestamp_required(required)

    def apply_signature_rect_placement(self, signature_rect: SignatureRect) -> None:
        self._compatibility_surface._runtime.apply_signature_rect_placement(signature_rect)

    def refresh_viewer(self) -> None:
        self._compatibility_surface._runtime.refresh_viewer()

    def current_request(self) -> SigningRequest | None:
        return self._compatibility_surface._runtime.current_request()

    def last_signing_result(self) -> SigningResult | None:
        signing_result = self._compatibility_surface.last_signing_result
        return signing_result if isinstance(signing_result, SigningResult) else None

    def snapshot(self) -> SigningWorkspaceSnapshot:
        return self._compatibility_surface.snapshot()


class SigningWorkspaceTestingPanelAdapter:
    """Wrap the live properties panel behind a smaller testing-oriented port."""

    def __init__(self, properties_panel: SignaturePropertiesPanel) -> None:
        self._properties_panel = properties_panel

    def set_signature_appearance(self, appearance: SignatureAppearance) -> None:
        self._properties_panel.set_signature_appearance(appearance)

    def set_signature_rect(
        self,
        signature_rect: SignatureRect,
        *,
        notify: bool = True,
    ) -> None:
        self._properties_panel.set_signature_rect(signature_rect, notify=notify)

    def refresh_preview(self) -> Any:
        return self._properties_panel.refresh_preview()

    def preview_text(self) -> str:
        return self._properties_panel.preview_text()

    def validation_text(self) -> str:
        return self._properties_panel.validation_text()

    def capture_preview_render(
        self,
        *,
        preview: Any,
        artifacts_dir: str | None,
        artifact_basename: str,
        build_preview_render_capture_payload: Any,
    ) -> dict[str, Any]:
        return build_preview_render_capture_payload(
            preview_controls=self._properties_panel.preview_controls,
            canonical_preview_render_backend=getattr(
                self._properties_panel,
                "_canonical_preview_render_backend",
                None,
            ),
            preview=preview,
            artifacts_dir=artifacts_dir,
            artifact_basename=artifact_basename,
        )
