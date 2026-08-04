from pathlib import Path

from foliaseal.infra.config.schemas import AppSettings
from foliaseal.presentation.qt.app_frame_workspace_open import WorkspaceHandle
from foliaseal.presentation.qt.signing_workspace_host import (
    SigningWorkspaceEnvironment,
    SigningWorkspaceHost,
)


class _Widget:
    def __init__(self) -> None:
        self.close_calls = 0
        self.delete_later_calls = 0

    def close(self) -> None:
        self.close_calls += 1

    def deleteLater(self) -> None:  # noqa: N802
        self.delete_later_calls += 1


class _OpenPort:
    def __init__(self, handle: WorkspaceHandle) -> None:
        self.handle = handle
        self.commands = []

    def open_workspace(self, command):
        self.commands.append(command)
        return self.handle


class _Mount:
    def __init__(self) -> None:
        self.widgets = []

    def mount(self, widget) -> None:
        self.widgets.append(widget)


def _settings() -> AppSettings:
    return AppSettings(
        schema_version=1,
        default_output_directory="/tmp/signed",
        default_open_directory="/tmp/source",
        linux_packaging_channel="unknown",
        ui={},
    )


def _environment() -> SigningWorkspaceEnvironment:
    return SigningWorkspaceEnvironment(
        app_settings=_settings,
        app_settings_store=None,
        certificate_catalog_store=None,
        certificate_secret_provider=None,
        preset_catalog_store=None,
        sign_executor=None,
        on_sign_request=None,
        reopen_target=None,
        on_error=None,
        on_status_change=None,
    )


def test_host_builds_command_and_publishes_active_handle() -> None:
    widget = _Widget()
    handle = WorkspaceHandle(
        source_pdf=Path("source.pdf"),
        widget=widget,
        shell=object(),
        testing=object(),
        viewer_workflow=object(),
        signing_workflow=object(),
    )
    open_port = _OpenPort(handle)
    host = SigningWorkspaceHost(
        environment=_environment(),
        workspace_open_port=open_port,
        mount_port=_Mount(),
    )

    opened = host.open("source.pdf")

    assert opened is handle
    assert host.active() is handle
    assert open_port.commands[0].source_pdf == Path("source.pdf")
    assert open_port.commands[0].app_settings == _settings()


def test_host_close_is_idempotent_and_clears_active_handle() -> None:
    widget = _Widget()
    handle = WorkspaceHandle(
        source_pdf=Path("source.pdf"),
        widget=widget,
        shell=object(),
        testing=object(),
        viewer_workflow=object(),
        signing_workflow=object(),
    )
    host = SigningWorkspaceHost(
        environment=_environment(),
        workspace_open_port=_OpenPort(handle),
        mount_port=_Mount(),
    )
    host.open("source.pdf")

    host.close()
    host.close()

    assert host.active() is None
    assert widget.close_calls == 1
    assert widget.delete_later_calls == 1
