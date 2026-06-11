from pathlib import Path

from foliaseal.application import SigningDraftWorkflow
from foliaseal.domain.models import (
    SignatureLayoutTemplate,
    SignatureStampPosition,
    SigningResult,
)
from foliaseal.presentation.qt.phase3_harness_workspace import (
    HeadlessPhase3HarnessWorkspaceAdapter,
    Phase3HarnessCaptureCommand,
    Phase3HarnessScenarioCommand,
    QtPhase3HarnessWorkspaceAdapter,
    snapshot_current_draft_request,
)
from tests.support.phase3_builders import (
    build_signature_appearance,
    build_signature_rect,
    build_signing_request,
)


class _FakePreset:
    def __init__(self, appearance) -> None:
        self.appearance = appearance


class _FakeCatalog:
    def __init__(self, appearance) -> None:
        self._appearance = appearance

    def preset_named(self, name: str):
        if name != "Saved Profile":
            raise KeyError(name)
        return _FakePreset(self._appearance)


class _FakeProfileStore:
    def __init__(self, appearance) -> None:
        self._appearance = appearance

    def load_catalog(self):
        return _FakeCatalog(self._appearance)


def test_qt_phase3_harness_workspace_adapter_applies_scenario_and_syncs_viewer() -> None:
    profile_store = _FakeProfileStore(
        build_signature_appearance(signer_label_prefix="Saved Profile")
    )
    command = Phase3HarnessScenarioCommand(
        profile_name="Saved Profile",
        appearance_overrides={
            "layout_template": "single_line",
            "stamp_position": "top",
        },
        timestamp_required=False,
        signature_rect=build_signature_rect(
            page_index=3,
            left_pt=24,
            bottom_pt=18,
            width_pt=120,
            height_pt=36,
        ),
    )

    class _FakePanel:
        def __init__(self) -> None:
            self.appearance = None
            self.rect = None
            self.refresh_calls = 0
            self._workflow = type(
                "_Workflow",
                (),
                {
                    "current_signature_appearance": build_signature_appearance(),
                    "timestamp_required": True,
                },
            )()

        def set_signature_appearance(self, appearance) -> None:
            self.appearance = appearance

        def set_signature_rect(self, signature_rect) -> None:
            self.rect = signature_rect

    class _FakeViewerWorkflow:
        def __init__(self) -> None:
            self.jumps: list[int] = []

        def jump_to_page(self, page_index: int) -> None:
            self.jumps.append(page_index)

    class _FakeViewerWidget:
        def __init__(self) -> None:
            self.refresh_calls: list[bool] = []

        def refresh(self, *, navigation: bool) -> None:
            self.refresh_calls.append(navigation)

    class _FakeCompat:
        def __init__(self) -> None:
            self.properties_panel = _FakePanel()
            self.viewer_workflow = _FakeViewerWorkflow()
            self.viewer_widget = _FakeViewerWidget()
            self.placement_syncs = 0
            self.overlay_syncs = 0
            self.sign_button_refreshes = 0
            self.viewer_refreshes = 0

        def sync_placement_context_from_viewer(self) -> None:
            self.placement_syncs += 1

        def sync_signature_overlay(self) -> None:
            self.overlay_syncs += 1

        def refresh_sign_button_state(self) -> None:
            self.sign_button_refreshes += 1

        def refresh_viewer(self) -> None:
            self.viewer_refreshes += 1

    compat = _FakeCompat()
    shell = type("_Shell", (), {"compat_surface": compat})()

    QtPhase3HarnessWorkspaceAdapter(
        shell=shell,
        profile_store=profile_store,
    ).apply_scenario(command)

    assert compat.properties_panel.appearance.signer_label_prefix == "Saved Profile"
    assert (
        compat.properties_panel.appearance.layout_template
        == SignatureLayoutTemplate.SINGLE_LINE
    )
    assert compat.properties_panel.appearance.stamp_position == SignatureStampPosition.TOP
    assert compat.properties_panel._workflow.timestamp_required is False
    assert compat.properties_panel.rect is not None
    assert compat.properties_panel.rect.page_index == 3
    assert compat.viewer_workflow.jumps == [3]
    assert compat.viewer_widget.refresh_calls == [True]
    assert compat.placement_syncs == 1
    assert compat.overlay_syncs == 1
    assert compat.sign_button_refreshes == 1
    assert compat.viewer_refreshes == 1


def test_qt_phase3_harness_workspace_adapter_captures_current_request_and_signing_result() -> None:
    preview = type(
        "_Preview",
        (),
        {
            "title": "Digitally signed by",
            "signer_label_prefix": "Digitally signed by",
            "layout_template": SignatureLayoutTemplate.SINGLE_LINE,
            "stamp_position": SignatureStampPosition.TOP,
            "timezone_display_mode": None,
            "show_field_names": False,
            "datetime_format": "%Y-%m-%d %H:%M",
            "image_stamp_path": None,
            "signature_rect": build_signature_rect(page_index=1, width_pt=180.0, height_pt=32.0),
            "text_style": None,
            "box_style": None,
            "fields": (),
            "issues": (),
            "can_submit": True,
        },
    )()
    request = build_signing_request(
        Path("/tmp"),
        signature_rect=preview.signature_rect,
        signature_appearance=build_signature_appearance(
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=SignatureStampPosition.TOP,
        ),
    )

    class _FakePanel:
        def __init__(self) -> None:
            self._workflow = SigningDraftWorkflow.from_signing_request(request)

        def refresh_preview(self):
            return preview

        def preview_text(self) -> str:
            return "Preview text"

        def validation_text(self) -> str:
            return "Ready to sign."

    class _FakeCompat:
        def __init__(self) -> None:
            self.properties_panel = _FakePanel()
            self.last_signing_result = SigningResult(success=True, failure_code=None, message="ok")

    compat = _FakeCompat()
    shell = type("_Shell", (), {"compat_surface": compat})()
    adapter = QtPhase3HarnessWorkspaceAdapter(
        shell=shell,
        profile_store=object(),
        capture_preview_render=lambda **_kwargs: {"preview_image_path": "artifacts/preview.png"},
        snapshot_preview=lambda preview, **kwargs: {
            "title": preview.title,
            "render_capture": kwargs["render_capture"],
            "sign_time_diagnostics": kwargs["sign_time_diagnostics"],
        },
        snapshot_signing_request=lambda current_request: (
            None
            if current_request is None
            else {"layout_template": current_request.signature_appearance.layout_template.value}
        ),
        build_backend_reservation_evidence=lambda current_request: type(
            "_Reservation",
            (),
            {
                "snapshot": {
                    "layout_template": current_request.signature_appearance.layout_template.value
                },
                "error": None,
            },
        )(),
        snapshot_sign_time_fit_diagnostics=lambda **_kwargs: {"fit": "ok"},
        interactive_capture_label=lambda **kwargs: (
            f"{kwargs['capture_kind']}_{kwargs['capture_index']:02d}"
        ),
    )

    capture = adapter.capture_state(
        Phase3HarnessCaptureCommand(
            request=None,
            artifacts_dir="artifacts/debug",
            artifact_basename="interactive_state_01",
            capture_index=1,
            capture_kind="manual",
        )
    )

    assert adapter.current_request() == request
    assert adapter.last_signing_result() == compat.last_signing_result
    assert capture["capture_label"] == "manual_01"
    assert capture["preview_text"] == "Preview text"
    assert capture["validation_text"] == "Ready to sign."
    assert capture["sign_request_snapshot"] == {"layout_template": "single_line"}
    assert capture["backend_reservation_snapshot"] == {"layout_template": "single_line"}
    assert capture["preview_snapshot"]["render_capture"] == {
        "preview_image_path": "artifacts/preview.png"
    }
    assert capture["preview_snapshot"]["sign_time_diagnostics"] == {"fit": "ok"}


def test_headless_phase3_harness_workspace_adapter_applies_same_scenario_fields() -> None:
    workflow = SigningDraftWorkflow(
        input_pdf_path="input.pdf",
        output_pdf_path="output.pdf",
        certificate_path="cert.p12",
        passphrase="secret",
        tsa_url="https://tsa.example.invalid",
        timestamp_required=True,
        signature_appearance=build_signature_appearance(),
    )
    profile_store = _FakeProfileStore(
        build_signature_appearance(signer_label_prefix="Saved Profile")
    )
    command = Phase3HarnessScenarioCommand(
        profile_name="Saved Profile",
        appearance_overrides={
            "layout_template": "single_line",
            "stamp_position": "top",
        },
        timestamp_required=False,
        signature_rect=build_signature_rect(
            page_index=2,
            left_pt=42,
            bottom_pt=24,
            width_pt=144,
            height_pt=48,
        ),
    )

    HeadlessPhase3HarnessWorkspaceAdapter(
        workflow=workflow,
        profile_store=profile_store,
    ).apply_scenario(command)

    assert workflow.current_signature_appearance is not None
    assert workflow.current_signature_appearance.signer_label_prefix == "Saved Profile"
    assert (
        workflow.current_signature_appearance.layout_template
        == SignatureLayoutTemplate.SINGLE_LINE
    )
    assert workflow.current_signature_appearance.stamp_position == SignatureStampPosition.TOP
    assert workflow.timestamp_required is False
    assert workflow.current_signature_rect is not None
    assert workflow.current_signature_rect.page_index == 2


def test_headless_phase3_harness_workspace_adapter_captures_preview_state() -> None:
    request = build_signing_request(Path("/tmp"))
    workflow = SigningDraftWorkflow.from_signing_request(request)
    preview = type(
        "_Preview",
        (),
        {
            "title": "Headless preview",
            "layout_template": SignatureLayoutTemplate.SINGLE_LINE,
            "stamp_position": SignatureStampPosition.BOTTOM,
        },
    )()
    adapter = HeadlessPhase3HarnessWorkspaceAdapter(
        workflow=workflow,
        profile_store=object(),
        headless_preview_text=lambda _preview: "Preview text",
        headless_validation_text=lambda _preview: "Ready to sign.",
        capture_headless_preview_render=lambda **_kwargs: {"preview_image_path": "headless.png"},
        snapshot_preview=lambda current_preview, **kwargs: {
            "title": current_preview.title,
            "render_capture": kwargs["render_capture"],
        },
        snapshot_signing_request=lambda current_request: (
            None
            if current_request is None
            else {"output_pdf_path": current_request.output_pdf_path}
        ),
        build_backend_reservation_evidence=lambda current_request: type(
            "_Reservation",
            (),
            {"snapshot": {"output_pdf_path": current_request.output_pdf_path}, "error": None},
        )(),
    )
    workflow.preview = lambda: preview  # type: ignore[method-assign]

    capture = adapter.capture_state(
        Phase3HarnessCaptureCommand(
            request=None,
            artifacts_dir="artifacts/debug",
            artifact_basename="scenario",
            capture_index=1,
            capture_kind="preview_matrix",
        )
    )

    assert snapshot_current_draft_request(workflow) == request
    assert adapter.current_request() == request
    assert adapter.last_signing_result() is None
    assert capture["capture_index"] == 1
    assert capture["preview_snapshot"]["render_capture"] == {"preview_image_path": "headless.png"}
    assert capture["preview_text"] == "Preview text"
    assert capture["validation_text"] == "Ready to sign."
    assert capture["sign_request_snapshot"] == {"output_pdf_path": request.output_pdf_path}
    assert capture["backend_reservation_snapshot"] == {"output_pdf_path": request.output_pdf_path}
