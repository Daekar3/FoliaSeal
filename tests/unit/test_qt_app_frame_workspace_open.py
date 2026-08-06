from pathlib import Path

import pytest

from foliaseal.application.certificate_models import CertificateCatalog
from foliaseal.infra.config.app_settings_storage import AppSettingsStore
from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
from foliaseal.infra.config.schemas import AppSettings
from foliaseal.presentation.qt.app_frame_workspace_open import (
    OpenWorkspaceCommand,
    QtPdfPageCountLoader,
    SigningWorkspaceCompositionService,
    WorkspaceOpenService,
)
from foliaseal.presentation.qt.signing_shell_port import (
    QtSigningWorkspaceSessionPort,
    QtWorkspaceView,
    SigningWorkspaceBootstrap,
    SigningWorkspaceBundle,
)


class _FakeQPdfDocument:
    class Error:
        None_ = 0
        Failed = 1

    next_status = 0
    next_page_count = 3
    load_calls: list[str] = []

    def load(self, path):
        type(self).load_calls.append(path)
        return type(self).next_status

    def pageCount(self):  # noqa: N802
        return type(self).next_page_count


class _FakeShell:
    def __init__(self) -> None:
        self.testing_adapter = object()

    def choose_output_pdf_path(self):
        return "/tmp/signed-output.pdf"

    def apply_app_settings(self, settings) -> None:
        self.app_settings = settings

    def refresh_certificate_configurations(self) -> CertificateCatalog:
        self.refresh_calls = getattr(self, "refresh_calls", 0) + 1
        return CertificateCatalog(schema_version=1)


class _FakeShellPort:
    def __init__(self, shell_widget) -> None:
        self.shell_widget = shell_widget

    def widget(self):
        return self.shell_widget

    def choose_output_pdf_path(self):
        return self.shell_widget.choose_output_pdf_path()

    def apply_app_settings(self, settings) -> None:
        self.shell_widget.apply_app_settings(settings)

    def refresh_certificate_configurations(self) -> CertificateCatalog:
        return self.shell_widget.refresh_certificate_configurations()


class _FakeShellFactory:
    def __init__(self, shell_widget) -> None:
        self.shell_widget = shell_widget
        self.bootstrap_calls: list[SigningWorkspaceBootstrap] = []

    def create(self, bootstrap: SigningWorkspaceBootstrap):
        self.bootstrap_calls.append(bootstrap)
        return SigningWorkspaceBundle(
            maintenance=_FakeShellPort(self.shell_widget),
            session=QtSigningWorkspaceSessionPort(self.shell_widget),
            testing=self.shell_widget.testing_adapter,
            view=QtWorkspaceView(self.shell_widget),
        )


def _settings(tmp_path: Path) -> AppSettings:
    return AppSettings(
        schema_version=1,
        default_output_directory=str(tmp_path / "signed"),
        default_open_directory=str(tmp_path / "source"),
        linux_packaging_channel="unknown",
        ui={},
    )


def _workspace_open_service(*, shell_factory: _FakeShellFactory) -> WorkspaceOpenService:
    _FakeQPdfDocument.next_status = _FakeQPdfDocument.Error.None_
    _FakeQPdfDocument.next_page_count = 3
    _FakeQPdfDocument.load_calls = []
    return WorkspaceOpenService(
        page_count_port=QtPdfPageCountLoader(_FakeQPdfDocument),
        composition_port=SigningWorkspaceCompositionService(
            render_backend_factory=lambda: object(),
            shell_factory=shell_factory,
        ),
    )


def test_workspace_open_service_builds_shell_outcome_from_command(tmp_path: Path) -> None:
    shell = _FakeShell()
    shell_factory = _FakeShellFactory(shell)
    service = _workspace_open_service(shell_factory=shell_factory)
    secret_provider = object()
    sign_executor = object()
    selected_pdf = tmp_path / "source" / "contract.pdf"

    def _on_sign_request(_request) -> None:
        return None

    def _reopen_target(_path) -> None:
        return None

    outcome = service.open_workspace(
        OpenWorkspaceCommand(
            source_pdf=selected_pdf,
            app_settings=_settings(tmp_path),
            app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
            certificate_catalog_store=CertificateCatalogStore(
                storage_dir=tmp_path / "Certificates"
            ),
            certificate_secret_provider=secret_provider,
            preset_catalog_store=object(),
            sign_executor=sign_executor,
            on_sign_request=_on_sign_request,
            reopen_target=_reopen_target,
            on_error=lambda message: None,
            on_status_change=lambda status: None,
        )
    )

    assert _FakeQPdfDocument.load_calls == [str(selected_pdf)]
    assert outcome.view.mount_target() is shell
    assert outcome.viewer_workflow.document_path == str(selected_pdf)
    assert outcome.viewer_workflow.session.page_count == 3
    assert outcome.signing_workflow.input_pdf_path == str(selected_pdf)
    assert outcome.signing_workflow.output_pdf_path == str(
        tmp_path / "signed" / "contract-signed.pdf"
    )
    assert shell_factory.bootstrap_calls[0].app_settings == _settings(tmp_path)
    assert shell_factory.bootstrap_calls[0].certificate_secret_provider is secret_provider
    assert shell_factory.bootstrap_calls[0].sign_executor is sign_executor
    assert shell_factory.bootstrap_calls[0].on_open_signed_output is _reopen_target


def test_workspace_open_service_raises_when_pdf_load_fails(tmp_path: Path) -> None:
    shell_factory = _FakeShellFactory(_FakeShell())
    service = _workspace_open_service(shell_factory=shell_factory)
    _FakeQPdfDocument.next_status = _FakeQPdfDocument.Error.Failed

    with pytest.raises(RuntimeError, match="Failed to load PDF document"):
        service.open_workspace(
            OpenWorkspaceCommand(
                source_pdf=tmp_path / "broken.pdf",
                app_settings=_settings(tmp_path),
                reopen_target=lambda path: None,
            )
        )

    assert shell_factory.bootstrap_calls == []


def test_workspace_open_service_raises_when_pdf_has_no_pages(tmp_path: Path) -> None:
    shell_factory = _FakeShellFactory(_FakeShell())
    service = _workspace_open_service(shell_factory=shell_factory)
    _FakeQPdfDocument.next_page_count = 0

    with pytest.raises(RuntimeError, match="PDF has no pages"):
        service.open_workspace(
            OpenWorkspaceCommand(
                source_pdf=tmp_path / "empty.pdf",
                app_settings=_settings(tmp_path),
                reopen_target=lambda path: None,
            )
        )

    assert shell_factory.bootstrap_calls == []
