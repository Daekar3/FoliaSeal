from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

from foliaseal.application.signing_draft_contracts import (
    SigningDraftPreview,
    SigningDraftValidationIssue,
    SigningDraftValidationSeverity,
)
from foliaseal.presentation.qt.signing_action_coordinator import SigningActionState
from foliaseal.presentation.qt.signing_workspace_action_bridge import (
    SigningWorkspaceActionBridge,
)
from tests.support.signing_builders import build_signature_rect
from tests.unit.test_qt_signing_shell import _fake_bindings


class _FakeDraftWorkflow:
    preview_signing_time = datetime(2026, 8, 10, 12, 34, 56, tzinfo=UTC)

    def __init__(
        self,
        *,
        input_pdf_path: str = "/tmp/source.pdf",
        output_pdf_path: str = "/tmp/source-signed.pdf",
    ) -> None:
        self.input_pdf_path = input_pdf_path
        self.output_pdf_path = output_pdf_path

    def preview(self) -> SigningDraftPreview:
        return SigningDraftPreview(
            title="Approval",
            page_index=2,
            signature_rect=build_signature_rect(page_index=2),
            signer_label_prefix="Signed by",
            layout_template=None,
            stamp_position=None,
            timezone_display_mode=None,
            show_field_names=True,
            datetime_format=None,
            text_style=None,
            box_style=None,
            image_stamp_path=None,
            fields=(),
            detail_text="Ready to sign.",
            issues=(
                SigningDraftValidationIssue(
                    code="certificate_local",
                    message="Self-signed certificate is intended for local validation.",
                    severity=SigningDraftValidationSeverity.WARNING,
                ),
            ),
            can_submit=True,
        )


class _FakeBoundary:
    def __init__(self) -> None:
        self.submitted = False
        self.accepted_paths: list[tuple[str, bool]] = []
        self.state = SigningActionState(
            can_sign=True,
            stage_text="Step 5 of 6 — Confirm and sign",
            detail_text="Ready to sign.",
            result_text="",
            result_kind="neutral",
            last_signing_result=None,
            last_successful_output_path=None,
            can_open_signed_output=False,
            recommended_action="sign",
        )

    def load(self) -> SigningActionState:
        return self.state

    def accept_output_path(self, path: str, *, allow_source_overwrite: bool = False):
        self.accepted_paths.append((path, allow_source_overwrite))
        return SimpleNamespace(state=self.state)

    def submit(self):
        self.submitted = True
        return SimpleNamespace(state=self.state, request=object())


class _CustomMessageBox:
    class ButtonRole:
        RejectRole = "reject"
        AcceptRole = "accept"

    next_clicked_label = "Cancel"
    instances = []

    def __init__(self, _parent):
        self.buttons = []
        self.title = ""
        self.text = ""
        self.default_button = None
        self.clicked = None
        type(self).instances.append(self)

    def addButton(self, label, role):  # noqa: N802
        button = SimpleNamespace(label=label, role=role)
        self.buttons.append(button)
        return button

    def setWindowTitle(self, title):  # noqa: N802
        self.title = title

    def setText(self, text):  # noqa: N802
        self.text = text

    def setDefaultButton(self, button):  # noqa: N802
        self.default_button = button

    def exec(self):
        self.clicked = next(
            button
            for button in self.buttons
            if button.label == type(self).next_clicked_label
        )

    def clickedButton(self):  # noqa: N802
        return self.clicked


def _bridge(
    bindings,
    boundary: _FakeBoundary,
    *,
    draft_workflow: _FakeDraftWorkflow | None = None,
    apply_changes=None,
) -> SigningWorkspaceActionBridge:
    return SigningWorkspaceActionBridge(
        widget=object(),
        bindings=bindings,
        sidebar=SimpleNamespace(render_signing_action_state=lambda _state: None),
        setup_port=SimpleNamespace(
            apply_changes=apply_changes or (lambda: None),
            load_setup_state=lambda: SimpleNamespace(
                selected_certificate_configuration_name="Board certificate",
                selected_signature_preset_name="Board approval",
            )
        ),
        signing_action_boundary=boundary,
        draft_workflow=draft_workflow or _FakeDraftWorkflow(),
        app_settings_getter=lambda: SimpleNamespace(default_output_directory=str(Path("/tmp"))),
    )


def test_sign_confirmation_cancel_is_lossless_and_contains_frozen_summary() -> None:
    bindings = _fake_bindings()
    bindings.q_message_box.next_result = bindings.q_message_box.No
    boundary = _FakeBoundary()

    result = _bridge(bindings, boundary).submit_sign_request()

    assert result is None
    assert boundary.submitted is False
    _, title, text = bindings.q_message_box.calls[-1]
    assert title == "Confirm signing"
    assert "Preset: Board approval" in text
    assert "Certificate: Board certificate" in text
    assert "Output: /tmp/source-signed.pdf" in text
    assert "Page: 3" in text
    assert "Field: New visible signature field" in text
    assert "Signing time: 2026-08-10T12:34:56+00:00" in text
    assert "Self-signed certificate is intended for local validation." in text
    assert "Sign and save" in text


def test_sign_confirmation_yes_submits_after_summary_review() -> None:
    bindings = _fake_bindings()
    bindings.q_message_box.next_result = bindings.q_message_box.Yes
    boundary = _FakeBoundary()

    result = _bridge(bindings, boundary).submit_sign_request()

    assert result is not None
    assert boundary.submitted is True


def test_sign_confirmation_uses_consequence_labeled_buttons_when_available() -> None:
    bindings = replace(_fake_bindings(), q_message_box=_CustomMessageBox)
    _CustomMessageBox.next_clicked_label = "Sign and save"
    _CustomMessageBox.instances.clear()
    boundary = _FakeBoundary()

    result = _bridge(bindings, boundary).submit_sign_request()

    assert result is not None
    dialog = _CustomMessageBox.instances[-1]
    assert [button.label for button in dialog.buttons] == ["Cancel", "Sign and save"]
    assert dialog.default_button.label == "Cancel"
    assert "Preset: Board approval" in dialog.text


def test_sign_confirmation_synchronizes_setup_before_preview() -> None:
    bindings = _fake_bindings()
    bindings.q_message_box.next_result = bindings.q_message_box.No
    boundary = _FakeBoundary()
    applied = []

    assert _bridge(
        bindings,
        boundary,
        apply_changes=lambda: applied.append(True),
    ).submit_sign_request() is None

    assert applied == [True]


def test_source_overwrite_requires_cancel_default_warning_and_explicit_authorization(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"source")
    bindings = _fake_bindings()
    bindings.q_file_dialog.next_save_file_name = str(source)
    boundary = _FakeBoundary()
    bridge = _bridge(
        bindings,
        boundary,
        draft_workflow=_FakeDraftWorkflow(
            input_pdf_path=str(source),
            output_pdf_path=str(tmp_path / "source-signed.pdf"),
        ),
    )

    bindings.q_message_box.next_result = bindings.q_message_box.No
    assert bridge.choose_output_pdf_path() is None
    assert boundary.accepted_paths == []
    assert "Cancel keeps the original source unchanged." in bindings.q_message_box.calls[-1][2]

    bindings.q_message_box.next_result = bindings.q_message_box.Yes
    assert bridge.choose_output_pdf_path() == str(source)
    assert boundary.accepted_paths == [(str(source), True)]
