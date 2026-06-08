from foliaseal.application import SigningDraftWorkflow
from foliaseal.domain.models import SignatureLayoutTemplate, SignatureStampPosition
from foliaseal.presentation.qt.phase3_harness_workspace import (
    HeadlessPhase3HarnessWorkspaceAdapter,
    Phase3HarnessScenarioCommand,
    QtPhase3HarnessWorkspaceAdapter,
)
from tests.support.phase3_builders import build_signature_appearance, build_signature_rect


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
