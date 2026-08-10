from types import SimpleNamespace

from foliaseal.presentation.qt.signing_shell_port import (
    QtSigningWorkspaceSessionPort,
    QtWorkspaceView,
)


class _Shell:
    def __init__(self) -> None:
        self.calls: list[object] = []
        self.container = object()
        self.preview_value = object()
        self.snapshot_value = object()

    def refresh_viewer(self) -> None:
        self.calls.append("refresh_viewer")

    def refresh_document_review(self):
        self.calls.append("refresh_document_review")
        return "review"

    def set_signature_rect(self, **kwargs):
        self.calls.append(("set_signature_rect", kwargs))
        return "rect"

    def apply_signature_rect_placement(self, rect) -> None:
        self.calls.append(("apply_signature_rect_placement", rect))

    def preview(self):
        self.calls.append("preview")
        return self.preview_value

    def snapshot(self):
        self.calls.append("snapshot")
        return self.snapshot_value

    def submit_sign_request(self):
        self.calls.append("submit_sign_request")
        return "request"

    def open_signed_output(self):
        self.calls.append("open_signed_output")
        return "output.pdf"

    def go_to_previous_page(self):
        self.calls.append("previous")

    def go_to_next_page(self):
        self.calls.append("next")

    def reset_zoom_view(self):
        self.calls.append("reset_zoom")

    def fit_page_view(self):
        self.calls.append("fit_page")

    def fit_width_view(self):
        self.calls.append("fit_width")

    def setFocus(self):  # noqa: N802
        self.calls.append("focus")


def test_session_port_delegates_primary_workflow_without_widget_introspection() -> None:
    shell = _Shell()
    session = QtSigningWorkspaceSessionPort(shell)

    session.refresh_viewer()
    assert session.refresh_document_review() == "review"
    assert session.set_signature_rect(
        page_index=1,
        left_pt=10,
        bottom_pt=20,
        width_pt=30,
        height_pt=40,
    ) == "rect"
    session.apply_signature_rect_placement("rect")
    assert session.preview() is shell.preview_value
    assert session.snapshot() is shell.snapshot_value
    assert session.submit_sign_request() == "request"
    assert session.open_signed_output() == "output.pdf"
    session.go_to_previous_page()
    session.go_to_next_page()
    session.reset_zoom_view()
    session.fit_page_view()
    session.fit_width_view()
    session.focus()
    assert [call if isinstance(call, str) else call[0] for call in shell.calls] == [
        "refresh_viewer",
        "refresh_document_review",
        "set_signature_rect",
        "apply_signature_rect_placement",
        "preview",
        "snapshot",
        "submit_sign_request",
        "open_signed_output",
        "previous",
        "next",
        "reset_zoom",
        "fit_page",
        "fit_width",
        "focus",
    ]


def test_qt_workspace_view_exposes_only_mount_and_dispose_contract() -> None:
    class _Container:
        def __init__(self) -> None:
            self.closed = 0
            self.deleted = 0

        def close(self):
            self.closed += 1

        def deleteLater(self):  # noqa: N802
            self.deleted += 1

    container = _Container()
    shell = SimpleNamespace(container=container, close=container.close)
    view = QtWorkspaceView(shell)

    assert view.mount_target() is container
    view.dispose()
    view.dispose()
    assert container.closed == 1
    assert container.deleted == 1
