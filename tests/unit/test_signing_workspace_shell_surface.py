from foliaseal.infra.config.schemas import AppSettings, CertificateCatalog
from foliaseal.presentation.qt.signing_workspace_shell_surface import (
    SigningWorkspaceShellSurface,
)


class _Widget:
    pass


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


def test_install_port_exports_exposes_signature_profile_refresh() -> None:
    widget = _Widget()
    action_bridge = _ActionBridge()
    settings = AppSettings(
        schema_version=1,
        default_output_directory="/tmp/output",
        default_open_directory="/tmp/open",
        linux_packaging_channel="unknown",
        ui={},
    )
    surface = SigningWorkspaceShellSurface(
        widget=widget,
        action_bridge=action_bridge,
        set_app_settings=lambda _settings: None,
        set_document_text_selection_mode=lambda enabled: enabled,
        copy_selected_document_text=lambda: None,
        initial_app_settings=settings,
    )

    surface.install_port_exports()

    widget.refresh_signature_profiles()

    assert action_bridge.refresh_profile_calls == 1
