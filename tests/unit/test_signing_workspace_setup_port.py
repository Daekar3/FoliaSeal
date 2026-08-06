from __future__ import annotations

from unittest.mock import Mock

from foliaseal.presentation.qt.signing_workspace_setup_port import (
    PanelSigningWorkspaceSetupAdapter,
    SigningWorkspaceSetupPort,
)


def test_panel_setup_adapter_forwards_only_typed_setup_capabilities() -> None:
    panel = Mock()
    panel.load_setup_state.return_value = object()
    panel.refresh_certificate_configurations.return_value = object()
    panel.refresh_signature_profiles.return_value = object()
    panel.save_current_signature_preset.return_value = object()
    panel.delete_current_signature_preset.return_value = object()
    panel.apply_changes.return_value = object()
    panel.refresh_preview.return_value = object()
    adapter = PanelSigningWorkspaceSetupAdapter(panel)

    assert isinstance(adapter, SigningWorkspaceSetupPort)
    assert adapter.load_setup_state() is panel.load_setup_state.return_value
    assert (
        adapter.refresh_certificate_configurations()
        is panel.refresh_certificate_configurations.return_value
    )
    assert adapter.refresh_signature_profiles() is panel.refresh_signature_profiles.return_value
    assert (
        adapter.save_current_signature_preset()
        is panel.save_current_signature_preset.return_value
    )
    assert (
        adapter.delete_current_signature_preset()
        is panel.delete_current_signature_preset.return_value
    )
    assert adapter.apply_changes() is panel.apply_changes.return_value
    assert adapter.refresh_preview() is panel.refresh_preview.return_value
    adapter.set_signature_rect(None, notify=False)
    adapter.set_signature_appearance(None)
    adapter.open_refinement_dialog()

    panel.set_signature_rect.assert_called_once_with(None, notify=False)
    panel.set_signature_appearance.assert_called_once_with(None)
    panel.open_refinement_dialog.assert_called_once_with()
