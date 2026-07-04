from pathlib import Path

import pytest
from PIL import Image

import foliaseal.presentation.qt.phase3_harness as phase3_harness_module
from foliaseal.application import SigningDraftWorkflow
from foliaseal.domain.models import (
    SignatureBoxStyle,
    SignatureLayoutTemplate,
    SignatureStampPosition,
    SignatureTextStyle,
    SigningResult,
)
from foliaseal.presentation.qt.phase3_harness_workspace import (
    HeadlessPhase3HarnessWorkspaceAdapter,
    Phase3HarnessCaptureCommand,
    Phase3HarnessScenarioCommand,
    Phase3HarnessWorkspaceSnapshot,
    QtPhase3HarnessWorkspaceAdapter,
    capture_qt_preview_render,
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

    class _FakeTestingAdapter:
        def __init__(self) -> None:
            self.properties_panel = _FakePanel()
            self.viewer_workflow = _FakeViewerWorkflow()
            self.viewer_widget = _FakeViewerWidget()
            self._signature_appearance = build_signature_appearance()
            self.timestamp_required = True
            self.placement_syncs = 0
            self.overlay_syncs = 0
            self.sign_button_refreshes = 0
            self.viewer_refreshes = 0

        def signature_appearance(self):
            return self._signature_appearance

        def set_timestamp_required(self, required: bool) -> None:
            self.timestamp_required = required

        def sync_placement_context_from_viewer(self) -> None:
            self.placement_syncs += 1

        def sync_signature_overlay(self) -> None:
            self.overlay_syncs += 1

        def refresh_sign_button_state(self) -> None:
            self.sign_button_refreshes += 1

        def refresh_viewer(self) -> None:
            self.viewer_refreshes += 1

        def apply_signature_rect_placement(self, signature_rect) -> None:
            self.properties_panel.set_signature_rect(signature_rect)
            self.viewer_workflow.jump_to_page(signature_rect.page_index)
            self.viewer_widget.refresh(navigation=True)
            self.sync_placement_context_from_viewer()
            self.sync_signature_overlay()
            self.refresh_sign_button_state()

    testing_adapter = _FakeTestingAdapter()
    shell = type("_Shell", (), {"testing_adapter": testing_adapter})()

    QtPhase3HarnessWorkspaceAdapter(
        shell=shell,
        profile_store=profile_store,
    ).apply_scenario(command)

    assert testing_adapter.properties_panel.appearance.signer_label_prefix == "Saved Profile"
    assert (
        testing_adapter.properties_panel.appearance.layout_template
        == SignatureLayoutTemplate.SINGLE_LINE
    )
    assert testing_adapter.properties_panel.appearance.stamp_position == SignatureStampPosition.TOP
    assert testing_adapter.timestamp_required is False
    assert testing_adapter.properties_panel.rect is not None
    assert testing_adapter.properties_panel.rect.page_index == 3
    assert testing_adapter.viewer_workflow.jumps == [3]
    assert testing_adapter.viewer_widget.refresh_calls == [True]
    assert testing_adapter.placement_syncs == 1
    assert testing_adapter.overlay_syncs == 1
    assert testing_adapter.sign_button_refreshes == 1
    assert testing_adapter.viewer_refreshes == 1


def test_qt_phase3_harness_workspace_adapter_prefers_dedicated_testing_adapter() -> None:
    command = Phase3HarnessScenarioCommand(
        profile_name=None,
        appearance_overrides=None,
        timestamp_required=True,
        signature_rect=build_signature_rect(page_index=1, width_pt=144.0, height_pt=36.0),
    )

    class _FakeTestingAdapter:
        def __init__(self) -> None:
            self._signature_appearance = build_signature_appearance()
            self.properties_panel = type("_Panel", (), {"set_signature_appearance_calls": []})()
            self.timestamp_required = None
            self.placement_calls = []
            self.viewer_refreshes = 0

        def signature_appearance(self):
            return self._signature_appearance

        def set_timestamp_required(self, required: bool) -> None:
            self.timestamp_required = required

        def apply_signature_rect_placement(self, signature_rect) -> None:
            self.placement_calls.append(signature_rect)

        def refresh_viewer(self) -> None:
            self.viewer_refreshes += 1

    class _FakeCompat:
        def __init__(self) -> None:
            self.used = False

        def signature_appearance(self):
            self.used = True
            return build_signature_appearance()

    testing_adapter = _FakeTestingAdapter()

    def _set_signature_appearance(appearance) -> None:
        testing_adapter.properties_panel.set_signature_appearance_calls.append(appearance)

    testing_adapter.properties_panel.set_signature_appearance = _set_signature_appearance
    shell = type(
        "_Shell",
        (),
        {
            "testing_adapter": testing_adapter,
            "compat_surface": _FakeCompat(),
        },
    )()

    QtPhase3HarnessWorkspaceAdapter(
        shell=shell,
        profile_store=object(),
    ).apply_scenario(command)

    assert testing_adapter.properties_panel.set_signature_appearance_calls
    assert testing_adapter.timestamp_required is True
    assert len(testing_adapter.placement_calls) == 1
    assert testing_adapter.viewer_refreshes == 1
    assert shell.compat_surface.used is False


def test_qt_phase3_harness_workspace_adapter_refreshes_viewer_directly() -> None:
    class _FakeTestingAdapter:
        def __init__(self) -> None:
            self.viewer_refreshes = 0

        def refresh_viewer(self) -> None:
            self.viewer_refreshes += 1

    testing_adapter = _FakeTestingAdapter()
    shell = type("_Shell", (), {"testing_adapter": testing_adapter})()

    QtPhase3HarnessWorkspaceAdapter(
        shell=shell,
        profile_store=object(),
    ).refresh_viewer()

    assert testing_adapter.viewer_refreshes == 1


def test_qt_phase3_harness_workspace_adapter_rejects_compat_surface_only_shell() -> None:
    class _FakeCompat:
        def __init__(self) -> None:
            self.viewer_refreshes = 0

        def refresh_viewer(self) -> None:
            self.viewer_refreshes += 1

    compat = _FakeCompat()
    shell = type("_Shell", (), {"compat_surface": compat})()

    adapter = QtPhase3HarnessWorkspaceAdapter(
        shell=shell,
        profile_store=object(),
    )

    with pytest.raises(
        TypeError,
        match="must expose 'testing_adapter'",
    ):
        adapter.refresh_viewer()

def test_qt_phase3_harness_workspace_adapter_returns_snapshot_with_request_and_result() -> None:
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
        def refresh_preview(self):
            return preview

        def preview_text(self) -> str:
            return "Preview text"

        def validation_text(self) -> str:
            return "Ready to sign."

    class _FakeTestingAdapter:
        def __init__(self) -> None:
            self.properties_panel = _FakePanel()
            self._current_request = request
            self.last_signing_result = SigningResult(success=True, failure_code=None, message="ok")

        def current_request(self):
            return self._current_request

    testing_adapter = _FakeTestingAdapter()
    shell = type("_Shell", (), {"testing_adapter": testing_adapter})()
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

    snapshot = adapter.capture_snapshot(
        Phase3HarnessCaptureCommand(
            request=None,
            artifacts_dir="artifacts/debug",
            artifact_basename="interactive_state_01",
            capture_index=1,
            capture_kind="manual",
        )
    )

    assert isinstance(snapshot, Phase3HarnessWorkspaceSnapshot)
    assert snapshot.current_request == request
    assert snapshot.last_signing_result == testing_adapter.last_signing_result
    assert snapshot.capture_label == "manual_01"
    assert snapshot.preview_text == "Preview text"
    assert snapshot.validation_text == "Ready to sign."
    assert snapshot.sign_request_snapshot == {"layout_template": "single_line"}
    assert snapshot.backend_reservation_snapshot == {"layout_template": "single_line"}
    assert snapshot.preview_snapshot["render_capture"] == {
        "preview_image_path": "artifacts/preview.png"
    }
    assert snapshot.preview_snapshot["sign_time_diagnostics"] == {"fit": "ok"}


def test_capture_qt_preview_render_preserves_gui_preview_and_bordered_analysis_preview(
    monkeypatch, tmp_path: Path
) -> None:
    gui_dir = tmp_path / "gui-preview"
    gui_dir.mkdir()
    gui_path = gui_dir / "preview.png"
    Image.new("RGBA", (40, 20), color=(0, 0, 0, 0)).save(gui_path)

    analysis_dir = tmp_path / "analysis-preview"
    analysis_dir.mkdir()
    analysis_path = analysis_dir / "preview.png"
    Image.new("RGBA", (40, 20), color=(255, 255, 255, 255)).save(analysis_path)

    render_calls: list[dict[str, object]] = []

    def _fake_render(preview, **kwargs):
        render_calls.append(kwargs)
        return type(
            "_Snapshot",
            (),
            {
                "image_path": str(analysis_path),
                "width_px": 52,
                "height_px": 26,
                "text_area_bounds_px": {"x": 1, "y": 2, "width": 48, "height": 20},
                "stamp_area_bounds_px": None,
                "text_bounds_px": {"x": 4, "y": 5, "width": 34, "height": 11},
                "stamp_bounds_px": None,
                "appearance_snapshot": phase3_harness_module.SignatureAppearanceSnapshot(
                    image_path=str(analysis_path),
                    image_size_px={"width": 52, "height": 26},
                    container_bounds_px={"x": 0, "y": 0, "width": 52, "height": 26},
                    border_bounds_px={"x": 0, "y": 0, "width": 52, "height": 26},
                    border_style={
                        "show_border": True,
                        "shape": "rounded",
                        "border_color_hex": "#000000",
                        "border_width_pt": 1.0,
                        "background_color_hex": "#FFFFFF",
                    },
                    text_bounds_px={"x": 4, "y": 5, "width": 34, "height": 11},
                    stamp_bounds_px=None,
                    text_fragments=("Digitally signed by", "Alice Example"),
                    line_bounds_px=(
                        {"x": 4, "y": 5, "width": 18, "height": 5},
                        {"x": 4, "y": 11, "width": 34, "height": 5},
                    ),
                ),
            },
        )()

    monkeypatch.setattr(
        phase3_harness_module,
        "render_canonical_signature_preview",
        _fake_render,
    )

    preview = type(
        "_Preview",
        (),
        {
            "image_stamp_path": None,
            "layout_template": SignatureLayoutTemplate.SINGLE_LINE,
            "stamp_position": SignatureStampPosition.TOP,
            "signature_rect": build_signature_rect(page_index=0, width_pt=220.0, height_pt=30.0),
            "text_style": SignatureTextStyle(
                font_family="Sans Serif",
                font_size_pt=8.5,
                bold=False,
                italic=False,
                text_color_hex="#000000",
            ),
            "box_style": SignatureBoxStyle(
                show_border=True,
                border_color_hex="#000000",
                border_width_pt=1.0,
                background_color_hex="#FFFFFF",
            ),
        },
    )()

    class _FakePanel:
        def __init__(self) -> None:
            self.preview_controls = type(
                "_Controls",
                (),
                {
                    "card_container": type(
                        "_Card",
                        (),
                        {
                            "_canonical_preview_snapshot": type(
                                "_Snapshot",
                                (),
                                {
                                    "image_path": str(gui_path),
                                    "width_px": 40,
                                    "height_px": 20,
                                    "text_area_bounds_px": {
                                        "x": 0,
                                        "y": 0,
                                        "width": 40,
                                        "height": 20,
                                    },
                                    "stamp_area_bounds_px": None,
                                    "text_bounds_px": {"x": 3, "y": 4, "width": 30, "height": 10},
                                    "stamp_bounds_px": None,
                                    "appearance_snapshot": (
                                        phase3_harness_module.SignatureAppearanceSnapshot(
                                            image_path=str(gui_path),
                                            image_size_px={"width": 40, "height": 20},
                                            container_bounds_px={
                                                "x": 0,
                                                "y": 0,
                                                "width": 40,
                                                "height": 20,
                                            },
                                            border_bounds_px=None,
                                            border_style=None,
                                            text_bounds_px={
                                                "x": 3,
                                                "y": 4,
                                                "width": 30,
                                                "height": 10,
                                            },
                                            stamp_bounds_px=None,
                                            text_fragments=(),
                                            line_bounds_px=(),
                                        )
                                    ),
                                },
                            )()
                        },
                    )(),
                    "single_body_container": object(),
                    "multi_body_container": object(),
                    "detail_label": object(),
                    "stamp_label": object(),
                    "multi_detail_label": object(),
                    "multi_stamp_label": object(),
                },
            )()
            self._canonical_preview_render_backend = object()

    shell = type(
        "_Shell",
        (),
        {
            "testing_adapter": type(
                "_TestingAdapter",
                (),
                {"properties_panel": _FakePanel()},
            )(),
        },
    )()
    monkeypatch.setattr(phase3_harness_module, "_widget_is_visible", lambda widget: True)
    monkeypatch.setattr(
        phase3_harness_module,
        "_widget_rect_snapshot",
        lambda widget: {"x": 0, "y": 0, "width": 40, "height": 20},
    )
    monkeypatch.setattr(
        phase3_harness_module,
        "_widget_rect_snapshot_relative_to",
        lambda root, widget: {"x": 0, "y": 0, "width": 40, "height": 20},
    )
    monkeypatch.setattr(phase3_harness_module, "_label_alignment_snapshot", lambda label: None)
    monkeypatch.setattr(phase3_harness_module, "_label_pixmap_size_snapshot", lambda label: None)
    monkeypatch.setattr(phase3_harness_module, "_layout_spacing", lambda layout: 0)
    monkeypatch.setattr(phase3_harness_module, "_size_hint_snapshot", lambda widget: None)
    monkeypatch.setattr(phase3_harness_module, "_text_font_diagnostics", lambda **kwargs: {})
    monkeypatch.setattr(phase3_harness_module, "_preview_edge_distances", lambda **kwargs: None)
    monkeypatch.setattr(phase3_harness_module, "_stamp_edge_diagnostics", lambda **kwargs: {})
    monkeypatch.setattr(phase3_harness_module, "_text_edge_diagnostics", lambda **kwargs: {})
    monkeypatch.setattr(phase3_harness_module, "_analyze_stamp_source_image", lambda path: {})
    monkeypatch.setattr(
        phase3_harness_module,
        "_project_content_bounds_to_preview",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        phase3_harness_module,
        "_project_pixmap_bounds_within_label",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        phase3_harness_module,
        "_detect_text_content_bounds_in_preview",
        lambda **kwargs: ({"x": 6, "y": 7, "width": 28, "height": 9}, None),
    )
    monkeypatch.setattr(
        phase3_harness_module,
        "_detect_text_line_bounds_in_preview",
        lambda **kwargs: (
            (
                {"x": 6, "y": 7, "width": 16, "height": 4},
                {"x": 6, "y": 12, "width": 28, "height": 4},
            ),
            None,
        ),
    )
    monkeypatch.setattr(phase3_harness_module, "_image_crop_sha256", lambda **kwargs: None)
    monkeypatch.setattr(phase3_harness_module, "_write_text_debug_overlay", lambda **kwargs: None)
    monkeypatch.setattr(phase3_harness_module, "_write_stamp_debug_overlay", lambda **kwargs: None)

    capture = capture_qt_preview_render(
        shell=shell,
        preview=preview,
        artifacts_dir=str(tmp_path),
        artifact_basename="interactive_state_01",
        build_preview_render_capture_payload=(
            phase3_harness_module._build_qt_preview_render_capture_payload
        ),
    )

    assert capture["preview_image_path"] is not None
    assert capture["analysis_preview_image_path"] is not None
    assert Path(capture["preview_image_path"]).read_bytes() == gui_path.read_bytes()
    assert Path(capture["analysis_preview_image_path"]).read_bytes() == analysis_path.read_bytes()
    assert capture["analysis_appearance_snapshot"] is not None
    assert capture["analysis_appearance_snapshot"]["image_size_px"] == {"width": 52, "height": 26}
    assert capture["analysis_appearance_snapshot"]["container_bounds_px"] == {
        "x": 0,
        "y": 0,
        "width": 52,
        "height": 26,
    }
    assert capture["analysis_appearance_snapshot"]["text_bounds_px"] == {
        "x": 4,
        "y": 5,
        "width": 34,
        "height": 11,
    }
    assert capture["text_structural_content_bounds_px"] == {
        "x": 3,
        "y": 4,
        "width": 30,
        "height": 10,
    }
    assert capture["text_rendered_content_bounds_px"] == {
        "x": 6,
        "y": 7,
        "width": 28,
        "height": 9,
    }
    assert capture["analysis_appearance_snapshot"]["border_style"]["shape"] == "rounded"
    assert render_calls
    assert render_calls[-1]["include_border"] is True
    assert render_calls[-1]["flatten_to_white"] is True


def test_capture_qt_preview_render_uses_analysis_space_bounds_for_raster_detection(
    monkeypatch, tmp_path: Path
) -> None:
    gui_dir = tmp_path / "gui-preview"
    gui_dir.mkdir()
    gui_path = gui_dir / "preview.png"
    Image.new("RGBA", (80, 40), color=(0, 0, 0, 0)).save(gui_path)

    analysis_dir = tmp_path / "analysis-preview"
    analysis_dir.mkdir()
    analysis_path = analysis_dir / "preview.png"
    Image.new("RGBA", (52, 26), color=(255, 255, 255, 255)).save(analysis_path)

    detector_calls: list[dict[str, object]] = []

    def _fake_render(preview, **kwargs):
        return type(
            "_Snapshot",
            (),
            {
                "image_path": str(analysis_path),
                "width_px": 52,
                "height_px": 26,
                "text_area_bounds_px": {"x": 1, "y": 2, "width": 48, "height": 20},
                "stamp_area_bounds_px": {"x": 1, "y": 1, "width": 48, "height": 8},
                "text_bounds_px": {"x": 4, "y": 5, "width": 34, "height": 11},
                "stamp_bounds_px": None,
                "appearance_snapshot": phase3_harness_module.SignatureAppearanceSnapshot(
                    image_path=str(analysis_path),
                    image_size_px={"width": 52, "height": 26},
                    container_bounds_px={"x": 0, "y": 0, "width": 52, "height": 26},
                    border_bounds_px={"x": 0, "y": 0, "width": 52, "height": 26},
                    border_style={
                        "show_border": True,
                        "shape": "rounded",
                        "border_color_hex": "#000000",
                        "border_width_pt": 1.0,
                        "background_color_hex": "#FFFFFF",
                    },
                    text_bounds_px={"x": 4, "y": 5, "width": 34, "height": 11},
                    stamp_bounds_px=None,
                    text_fragments=("Digitally signed by", "Alice Example"),
                    line_bounds_px=(
                        {"x": 4, "y": 5, "width": 18, "height": 5},
                        {"x": 4, "y": 11, "width": 34, "height": 5},
                    ),
                ),
            },
        )()

    monkeypatch.setattr(
        phase3_harness_module,
        "render_canonical_signature_preview",
        _fake_render,
    )

    preview = type(
        "_Preview",
        (),
        {
            "image_stamp_path": None,
            "layout_template": SignatureLayoutTemplate.SINGLE_LINE,
            "stamp_position": SignatureStampPosition.TOP,
            "signature_rect": build_signature_rect(page_index=0, width_pt=220.0, height_pt=30.0),
            "text_style": SignatureTextStyle(
                font_family="Sans Serif",
                font_size_pt=8.5,
                bold=False,
                italic=False,
                text_color_hex="#000000",
            ),
            "box_style": SignatureBoxStyle(
                show_border=True,
                border_color_hex="#000000",
                border_width_pt=1.0,
                background_color_hex="#FFFFFF",
            ),
        },
    )()

    class _FakePanel:
        def __init__(self) -> None:
            self.preview_controls = type(
                "_Controls",
                (),
                {
                    "card_container": type(
                        "_Card",
                        (),
                        {
                            "_canonical_preview_snapshot": type(
                                "_Snapshot",
                                (),
                                {
                                    "image_path": str(gui_path),
                                    "width_px": 80,
                                    "height_px": 40,
                                    "text_area_bounds_px": {
                                        "x": 0,
                                        "y": 0,
                                        "width": 80,
                                        "height": 40,
                                    },
                                    "stamp_area_bounds_px": None,
                                    "text_bounds_px": {"x": 3, "y": 4, "width": 60, "height": 20},
                                    "stamp_bounds_px": None,
                                },
                            )()
                        },
                    )(),
                    "single_body_container": object(),
                    "multi_body_container": object(),
                    "detail_label": object(),
                    "stamp_label": object(),
                    "multi_detail_label": object(),
                    "multi_stamp_label": object(),
                },
            )()
            self._canonical_preview_render_backend = object()

    shell = type(
        "_Shell",
        (),
        {
            "testing_adapter": type(
                "_TestingAdapter",
                (),
                {"properties_panel": _FakePanel()},
            )(),
        },
    )()
    monkeypatch.setattr(phase3_harness_module, "_widget_is_visible", lambda widget: True)
    monkeypatch.setattr(
        phase3_harness_module,
        "_widget_rect_snapshot",
        lambda widget: {"x": 0, "y": 0, "width": 80, "height": 40},
    )
    monkeypatch.setattr(
        phase3_harness_module,
        "_widget_rect_snapshot_relative_to",
        lambda root, widget: {"x": 0, "y": 0, "width": 80, "height": 40},
    )
    monkeypatch.setattr(phase3_harness_module, "_label_alignment_snapshot", lambda label: None)
    monkeypatch.setattr(phase3_harness_module, "_label_pixmap_size_snapshot", lambda label: None)
    monkeypatch.setattr(phase3_harness_module, "_layout_spacing", lambda layout: 0)
    monkeypatch.setattr(phase3_harness_module, "_size_hint_snapshot", lambda widget: None)
    monkeypatch.setattr(phase3_harness_module, "_text_font_diagnostics", lambda **kwargs: {})
    monkeypatch.setattr(phase3_harness_module, "_preview_edge_distances", lambda **kwargs: None)
    monkeypatch.setattr(phase3_harness_module, "_stamp_edge_diagnostics", lambda **kwargs: {})
    monkeypatch.setattr(phase3_harness_module, "_text_edge_diagnostics", lambda **kwargs: {})
    monkeypatch.setattr(phase3_harness_module, "_analyze_stamp_source_image", lambda path: {})
    monkeypatch.setattr(
        phase3_harness_module,
        "_project_content_bounds_to_preview",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        phase3_harness_module,
        "_project_pixmap_bounds_within_label",
        lambda **kwargs: None,
    )

    def _record_content_detection(**kwargs):
        detector_calls.append(kwargs)
        return {"x": 6, "y": 7, "width": 28, "height": 9}, None

    monkeypatch.setattr(
        phase3_harness_module,
        "_detect_text_content_bounds_in_preview",
        _record_content_detection,
    )
    monkeypatch.setattr(
        phase3_harness_module,
        "_detect_text_line_bounds_in_preview",
        lambda **kwargs: (
            (
                {"x": 6, "y": 7, "width": 16, "height": 4},
                {"x": 6, "y": 12, "width": 28, "height": 4},
            ),
            None,
        ),
    )
    monkeypatch.setattr(phase3_harness_module, "_image_crop_sha256", lambda **kwargs: None)
    monkeypatch.setattr(phase3_harness_module, "_write_text_debug_overlay", lambda **kwargs: None)
    monkeypatch.setattr(phase3_harness_module, "_write_stamp_debug_overlay", lambda **kwargs: None)

    capture_qt_preview_render(
        shell=shell,
        preview=preview,
        artifacts_dir=str(tmp_path),
        artifact_basename="interactive_state_01",
        build_preview_render_capture_payload=(
            phase3_harness_module._build_qt_preview_render_capture_payload
        ),
    )

    assert detector_calls
    assert detector_calls[-1]["preview_image_path"].endswith("_analysis.png")
    assert detector_calls[-1]["text_widget_bounds"] == {"x": 1, "y": 2, "width": 48, "height": 20}


def test_qt_phase3_harness_workspace_adapter_rejects_missing_testing_adapter() -> None:
    adapter = QtPhase3HarnessWorkspaceAdapter(
        shell=type("_Shell", (), {})(),
        profile_store=object(),
    )

    with pytest.raises(
        TypeError,
        match="must expose 'testing_adapter'",
    ):
        adapter.refresh_viewer()


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

    assert snapshot_current_draft_request(workflow) == request

    snapshot = adapter.capture_snapshot(
        Phase3HarnessCaptureCommand(
            request=None,
            artifacts_dir="artifacts/debug",
            artifact_basename="scenario",
            capture_index=1,
            capture_kind="preview_matrix",
        )
    )

    assert isinstance(snapshot, Phase3HarnessWorkspaceSnapshot)
    assert snapshot.current_request == request
    assert snapshot.last_signing_result is None
    assert snapshot.capture_label is None
    assert snapshot.preview_snapshot["render_capture"] == {"preview_image_path": "headless.png"}
    assert snapshot.sign_request_snapshot == {"output_pdf_path": request.output_pdf_path}


def test_headless_phase3_harness_workspace_adapter_refresh_viewer_is_no_op() -> None:
    request = build_signing_request(Path("/tmp"))
    workflow = SigningDraftWorkflow.from_signing_request(request)
    adapter = HeadlessPhase3HarnessWorkspaceAdapter(
        workflow=workflow,
        profile_store=object(),
    )

    adapter.refresh_viewer()

    assert snapshot_current_draft_request(workflow) == request
