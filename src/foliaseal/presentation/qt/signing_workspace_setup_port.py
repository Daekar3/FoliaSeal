"""Stable setup capability boundary for signing-workspace shell callers."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from foliaseal.application import SigningDraftPreview
from foliaseal.application.signature_properties_coordinator import (
    SignaturePropertiesViewState,
)
from foliaseal.domain.models import SignatureAppearance, SignatureRect
from foliaseal.infra.config.schemas import CertificateCatalog


@runtime_checkable
class SigningWorkspaceSetupPort(Protocol):
    """Presentation-facing setup capabilities used by shell bridges."""

    def load_setup_state(self) -> SignaturePropertiesViewState: ...

    def apply_changes(self) -> SigningDraftPreview: ...

    def is_ready_to_sign(self) -> bool: ...

    def validation_text(self) -> str: ...

    def refresh_preview(self) -> SigningDraftPreview: ...

    def refresh_certificate_configurations(self) -> CertificateCatalog: ...

    def refresh_signature_profiles(self) -> SignaturePropertiesViewState: ...

    def apply_selected_certificate_configuration(self) -> bool: ...

    def save_current_signature_preset(self) -> SignaturePropertiesViewState | None: ...

    def delete_current_signature_preset(self) -> SignaturePropertiesViewState | None: ...

    def open_refinement_dialog(self) -> bool: ...

    def set_signature_rect(self, rect: SignatureRect | None, *, notify: bool = True) -> None: ...

    def set_signature_appearance(self, appearance: SignatureAppearance | None) -> None: ...


class PanelSigningWorkspaceSetupAdapter:
    """Structural adapter that keeps the concrete Qt panel at the composition edge."""

    def __init__(self, panel: Any) -> None:
        self._panel = panel

    def load_setup_state(self) -> SignaturePropertiesViewState:
        return self._panel.load_setup_state()

    def apply_changes(self) -> SigningDraftPreview:
        return self._panel.apply_changes()

    def is_ready_to_sign(self) -> bool:
        return self._panel.is_ready_to_sign()

    def validation_text(self) -> str:
        return self._panel.validation_text()

    def refresh_preview(self) -> SigningDraftPreview:
        return self._panel.refresh_preview()

    def refresh_certificate_configurations(self) -> CertificateCatalog:
        return self._panel.refresh_certificate_configurations()

    def refresh_signature_profiles(self) -> SignaturePropertiesViewState:
        return self._panel.refresh_signature_profiles()

    def apply_selected_certificate_configuration(self) -> bool:
        return self._panel.apply_selected_certificate_configuration()

    def save_current_signature_preset(self) -> SignaturePropertiesViewState | None:
        return self._panel.save_current_signature_preset()

    def delete_current_signature_preset(self) -> SignaturePropertiesViewState | None:
        return self._panel.delete_current_signature_preset()

    def open_refinement_dialog(self) -> bool:
        return self._panel.open_refinement_dialog()

    def set_signature_rect(self, rect: SignatureRect | None, *, notify: bool = True) -> None:
        self._panel.set_signature_rect(rect, notify=notify)

    def set_signature_appearance(self, appearance: SignatureAppearance | None) -> None:
        self._panel.set_signature_appearance(appearance)
