"""Compatibility and harness-facing surface for the signing workspace shell."""

from __future__ import annotations

from collections.abc import Callable
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
        shell_surface: Any,
    ) -> None:
        self._widget = widget
        self._runtime = runtime
        self._properties_panel = properties_panel
        self._viewer_widget = viewer_widget
        self._viewer_navigation_controls = viewer_navigation_controls
        self._properties_scroll = properties_scroll
        self._sidebar_container = sidebar_container
        self._sidebar_surface = sidebar_surface
        self._shell_surface = shell_surface
        self._testing_adapter = SigningWorkspaceTestingAdapter(
            runtime=runtime,
            properties_panel=properties_panel,
            last_signing_result=lambda: getattr(widget, "last_signing_result", None),
        )
        self._legacy_exports = SigningWorkspaceLegacyWidgetExports(
            widget=widget,
            runtime=runtime,
            properties_panel=properties_panel,
            viewer_widget=viewer_widget,
            viewer_navigation_controls=viewer_navigation_controls,
            properties_scroll=properties_scroll,
            sidebar_container=sidebar_container,
            sidebar_surface=sidebar_surface,
            shell_surface=shell_surface,
            testing_adapter=self._testing_adapter,
            compatibility_surface=self,
        )

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
        """Install the transitional aliases through the explicit Qt-local installer."""
        self._legacy_exports.install()

class SigningWorkspaceLegacyWidgetExports:
    """Qt-local installer for transitional widget aliases."""

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
        shell_surface: Any,
        testing_adapter: SigningWorkspaceTestingAdapter,
        compatibility_surface: Any,
    ) -> None:
        self._widget = widget
        self._runtime = runtime
        self._properties_panel = properties_panel
        self._viewer_widget = viewer_widget
        self._viewer_navigation_controls = viewer_navigation_controls
        self._properties_scroll = properties_scroll
        self._sidebar_container = sidebar_container
        self._sidebar_surface = sidebar_surface
        self._shell_surface = shell_surface
        self._testing_adapter = testing_adapter
        self._compatibility_surface = compatibility_surface
        self._installed = False

    def install(self) -> None:
        if self._installed:
            return
        self._installed = True
        widget = self._widget
        widget.compat_surface = self._compatibility_surface  # type: ignore[attr-defined]
        widget.testing_adapter = self._testing_adapter  # type: ignore[attr-defined]
        widget.properties_panel = self._properties_panel  # type: ignore[attr-defined]
        widget.viewer_widget = self._viewer_widget  # type: ignore[attr-defined]
        widget.viewer_navigation_controls = self._viewer_navigation_controls  # type: ignore[attr-defined]
        widget.properties_scroll = self._properties_scroll  # type: ignore[attr-defined]
        widget.sidebar = self._sidebar_container  # type: ignore[attr-defined]
        widget.sidebar_surface = self._sidebar_surface  # type: ignore[attr-defined]
        destroyed_signal = getattr(widget, "destroyed", None)
        destroy_connect = getattr(destroyed_signal, "connect", None)
        if callable(destroy_connect):
            destroy_connect(lambda *_args: self._properties_panel.dispose())
        widget.last_signing_result = None  # type: ignore[attr-defined]
        widget.refresh_viewer = self._runtime.refresh_viewer  # type: ignore[attr-defined]
        widget.refresh_document_review = self._runtime.refresh_document_review  # type: ignore[attr-defined]
        widget.search_document_text = self._runtime.search_document_text  # type: ignore[attr-defined]
        widget.next_document_text_match = self._runtime.next_document_text_match  # type: ignore[attr-defined]
        widget.previous_document_text_match = self._runtime.previous_document_text_match  # type: ignore[attr-defined]
        widget.copy_current_document_text_match = self._runtime.copy_current_document_text_match  # type: ignore[attr-defined]
        widget.set_document_text_selection_mode = self._runtime.set_document_text_selection_mode  # type: ignore[attr-defined]
        widget.copy_selected_document_text = self._runtime.copy_selected_document_text  # type: ignore[attr-defined]
        widget.clear_selected_document_text = self._runtime.clear_selected_document_text  # type: ignore[attr-defined]
        widget.set_logical_page_index = self._runtime.set_logical_page_index  # type: ignore[attr-defined]
        widget.logical_page_index = self._runtime.logical_page_index  # type: ignore[attr-defined]
        widget.set_signature_rect = self._runtime.set_signature_rect  # type: ignore[attr-defined]
        widget.signature_rect = self._runtime.signature_rect  # type: ignore[attr-defined]
        widget.set_selected_certificate_configuration_id = (  # type: ignore[attr-defined]
            self._runtime.set_selected_certificate_configuration_id
        )
        widget.selected_certificate_configuration_id = (  # type: ignore[attr-defined]
            self._runtime.selected_certificate_configuration_id
        )
        widget.signature_appearance = self._runtime.signature_appearance  # type: ignore[attr-defined]
        widget.set_timestamp_required = self._runtime.set_timestamp_required  # type: ignore[attr-defined]
        widget.current_request = self._runtime.current_request  # type: ignore[attr-defined]
        widget.is_sign_action_enabled = self._runtime.is_sign_action_enabled  # type: ignore[attr-defined]
        widget.choose_output_pdf_path = self._shell_surface.choose_output_pdf_path  # type: ignore[attr-defined]
        widget.apply_app_settings = self._shell_surface.apply_app_settings  # type: ignore[attr-defined]
        widget.refresh_certificate_configurations = (  # type: ignore[attr-defined]
            self._shell_surface.refresh_certificate_configurations
        )
        widget.refresh_signature_profiles = self._shell_surface.refresh_signature_profiles  # type: ignore[attr-defined]
        widget.open_reusable_object_editor = self._shell_surface.open_reusable_object_editor  # type: ignore[attr-defined]
        widget.submit_sign_request = self._shell_surface.submit_sign_request  # type: ignore[attr-defined]
        widget.open_signed_output = self._shell_surface.open_signed_output  # type: ignore[attr-defined]


class SigningWorkspaceTestingAdapter:
    """Dedicated harness/testing adapter over the live runtime/controller seam."""

    def __init__(
        self,
        *,
        runtime: SigningWorkspaceRuntime,
        properties_panel: SignaturePropertiesPanel,
        last_signing_result: Callable[[], SigningResult | None],
    ) -> None:
        self._runtime = runtime
        self._last_signing_result = last_signing_result
        self._panel = SigningWorkspaceTestingPanelAdapter(properties_panel)

    @property
    def panel(self) -> SigningWorkspaceTestingPanelPort:
        return self._panel

    def signature_appearance(self) -> SignatureAppearance | None:
        return self._runtime.signature_appearance()

    def set_timestamp_required(self, required: bool) -> None:
        self._runtime.set_timestamp_required(required)

    def apply_signature_rect_placement(self, signature_rect: SignatureRect) -> None:
        self._runtime.apply_signature_rect_placement(signature_rect)

    def refresh_viewer(self) -> None:
        self._runtime.refresh_viewer()

    def current_request(self) -> SigningRequest | None:
        return self._runtime.current_request()

    def last_signing_result(self) -> SigningResult | None:
        signing_result = self._last_signing_result()
        return signing_result if isinstance(signing_result, SigningResult) else None

    def snapshot(self) -> SigningWorkspaceSnapshot:
        return self._runtime.snapshot(last_signing_result=self.last_signing_result())


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
