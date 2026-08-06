from foliaseal.infra.config.schemas import AppSettings, CertificateCatalog
from foliaseal.presentation.qt.signing_workspace_shell_surface import (
    SigningWorkspaceShellSurface,
)


class _ActionBridge:
    def __init__(self) -> None:
        self.refresh_profile_calls = 0

    def choose_output_pdf_path(self) -> str:
        return "/tmp/signed-output.pdf"

    def refresh_certificate_configurations(self) -> CertificateCatalog:
        return CertificateCatalog(schema_version=1)

    def refresh_signature_profiles(self) -> None:
        self.refresh_profile_calls += 1

    def submit_sign_request(self):
        return None

    def open_signed_output(self):
        return None


def test_shell_surface_exposes_signature_profile_refresh() -> None:
    action_bridge = _ActionBridge()
    settings = AppSettings(
        schema_version=1,
        default_output_directory="/tmp/output",
        default_open_directory="/tmp/open",
        linux_packaging_channel="unknown",
        ui={},
    )
    surface = SigningWorkspaceShellSurface(
        action_bridge=action_bridge,
        set_app_settings=lambda _settings: None,
        set_document_text_selection_mode=lambda enabled: enabled,
        copy_selected_document_text=lambda: None,
        open_reusable_object_editor=lambda: True,
        initial_app_settings=settings,
    )

    surface.refresh_signature_profiles()

    assert action_bridge.refresh_profile_calls == 1
