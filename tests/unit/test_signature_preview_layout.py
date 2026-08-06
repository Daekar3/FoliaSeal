from pathlib import Path

from PIL import Image

from foliaseal.application.reusable_signing_models import SignaturePresetCatalog
from foliaseal.application.reusable_signing_objects import (
    InMemoryCatalogRepository,
    ReusableSigningObjects,
)
from foliaseal.application.signing_preview_renderer import (
    CanonicalSignaturePreviewSnapshot,
)
from foliaseal.domain.models import (
    SignatureBoxStyle,
    SignatureLayoutTemplate,
    SignatureRect,
    SignatureStampPosition,
)
from foliaseal.presentation.qt import signature_preview_layout as preview_layout_module
from foliaseal.presentation.qt import signing_shell as signing_shell_module
from foliaseal.presentation.qt import signing_workspace_properties_panel as properties_panel_module
from foliaseal.presentation.qt.signature_preview_lifecycle import (
    CanonicalPreviewRenderState,
)
from tests.support.signing_builders import build_signature_appearance
from tests.unit.test_qt_signing_shell import (
    _fake_bindings,
    _FakeLabel,
    _FakePixmap,
    _FakeQt,
    _workflow,
)


def _panel_and_layout(tmp_path: Path):
    bindings = _fake_bindings()
    panel = properties_panel_module.SignaturePropertiesPanel(
        bindings=bindings,
        workflow=_workflow(tmp_path),
        reusable_objects=ReusableSigningObjects(
            InMemoryCatalogRepository(SignaturePresetCatalog(schema_version=1))
        ),
    )
    layout = preview_layout_module.QtSignaturePreviewLayout(bindings=bindings)
    return panel, layout


def _fallback_render_state(plan) -> CanonicalPreviewRenderState:
    return CanonicalPreviewRenderState(
        snapshot=None,
        pixmap=None,
        card_style=plan.fallback_card_style,
        render_label_visible=False,
        render_body_size=plan.inner_body_size,
    )


def test_preview_layout_reorders_horizontal_right_stamp_content(tmp_path: Path) -> None:
    panel, layout = _panel_and_layout(tmp_path)
    appearance = build_signature_appearance(
        layout_template=SignatureLayoutTemplate.MULTI_LINE,
        stamp_position=SignatureStampPosition.RIGHT,
    )
    panel.set_signature_appearance(appearance)
    panel.set_signature_rect(
        SignatureRect(
            page_index=0,
            left_pt=24.0,
            bottom_pt=18.0,
            width_pt=180.0,
            height_pt=48.0,
        )
    )

    preview = panel.preview
    plan = layout.plan(preview=preview, controls=panel.preview_controls)
    layout.apply(
        preview=preview,
        controls=panel.preview_controls,
        state=plan,
        canonical_render_state=_fallback_render_state(plan),
    )

    controls = panel.preview_controls
    assert controls.single_body_container.visible is False
    assert controls.multi_body_container.visible is True
    assert controls.multi_body_container.layout.items[0][0] is controls.multi_content_container
    assert controls.multi_body_container.layout.items[0][1] == (0, _FakeQt.AlignCenter)
    assert controls.multi_body_container.layout.items[1][0] is controls.multi_stamp_label
    assert controls.multi_body_container.layout.items[1][1] == (0, _FakeQt.AlignCenter)


def test_preview_layout_uses_reserved_vertical_band_heights(tmp_path: Path) -> None:
    stamp_path = tmp_path / "stamp.png"
    Image.new("RGBA", (96, 32), color=(0, 0, 0, 255)).save(stamp_path)

    panel, layout = _panel_and_layout(tmp_path)
    appearance = build_signature_appearance(
        layout_template=SignatureLayoutTemplate.MULTI_LINE,
        stamp_position=SignatureStampPosition.TOP,
        image_stamp_path=str(stamp_path),
    )
    panel.set_signature_appearance(appearance)
    panel.set_signature_rect(
        SignatureRect(
            page_index=0,
            left_pt=24.0,
            bottom_pt=18.0,
            width_pt=180.0,
            height_pt=48.0,
        )
    )

    preview = panel.preview
    plan = layout.plan(preview=preview, controls=panel.preview_controls)
    layout.apply(
        preview=preview,
        controls=panel.preview_controls,
        state=plan,
        canonical_render_state=_fallback_render_state(plan),
    )

    raw_geometry = preview_layout_module._preview_vertical_band_geometry(
        preview,
        stamp_text=preview_layout_module._preview_stamp_text(preview),
        inner_body_height_px=plan.inner_body_size[1],
        available_width_px=plan.available_width_px,
        stamp_aspect_ratio=preview_layout_module._raw_pixmap_aspect_ratio(plan.raw_stamp_pixmap),
    )
    assert raw_geometry is not None
    text_height, stamp_height, separator_height = (
        preview_layout_module._fit_vertical_preview_band_geometry(
            text_height=raw_geometry[0],
            stamp_height=raw_geometry[1],
            separator_height=raw_geometry[2],
            inner_body_height_px=plan.inner_body_size[1],
            detail_hint_height_px=panel.preview_controls.detail_label.sizeHint().height(),
            rendered_line_count=max(1, plan.stamp_text.count("\n") + 1),
            stamp_visible=plan.raw_stamp_pixmap is not None,
        )
    )

    assert panel.preview_controls.detail_label.fixed_size == (
        plan.inner_body_size[0],
        text_height,
    )
    assert panel.preview_controls.stamp_label.fixed_size == (
        plan.inner_body_size[0],
        stamp_height,
    )
    assert panel.preview_controls.single_body_container.layout.spacing == separator_height


def test_preview_layout_uses_border_aware_padding_for_thick_borders(tmp_path: Path) -> None:
    panel, layout = _panel_and_layout(tmp_path)
    appearance = build_signature_appearance(
        stamp_position=SignatureStampPosition.LEFT,
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        box_style=SignatureBoxStyle(
            show_border=True,
            border_color_hex="#4a4a4a",
            border_width_pt=8.0,
            background_color_hex="#ffffff",
        ),
    )
    panel.set_signature_appearance(appearance)
    panel.set_signature_rect(
        SignatureRect(
            page_index=0,
            left_pt=24.0,
            bottom_pt=18.0,
            width_pt=180.0,
            height_pt=48.0,
        )
    )

    preview = panel.preview
    plan = layout.plan(preview=preview, controls=panel.preview_controls)
    layout.apply(
        preview=preview,
        controls=panel.preview_controls,
        state=plan,
        canonical_render_state=_fallback_render_state(plan),
    )

    expected_padding = preview_layout_module._preview_card_padding_px(preview)
    assert f"padding: {expected_padding:.1f}px;" in panel.preview_controls.card_container.style
    assert panel.preview_controls.card_container.fixed_size == plan.card_size
    assert panel.preview_controls.single_body_container.fixed_size == plan.inner_body_size


def test_preview_layout_applies_canonical_render_state_to_active_surface(
    tmp_path: Path,
) -> None:
    panel, layout = _panel_and_layout(tmp_path)
    preview = panel.preview
    plan = layout.plan(preview=preview, controls=panel.preview_controls)

    preview_path = tmp_path / "preview.png"
    Image.new("RGBA", (120, 60), color=(255, 255, 255, 255)).save(preview_path)
    snapshot = CanonicalSignaturePreviewSnapshot(
        image_path=str(preview_path),
        width_px=120,
        height_px=60,
        text_area_bounds_px={"x": 0, "y": 0, "width": 120, "height": 60},
        stamp_area_bounds_px=None,
        text_bounds_px={"x": 0, "y": 0, "width": 120, "height": 60},
        stamp_bounds_px=None,
    )
    canonical_render_state = CanonicalPreviewRenderState(
        snapshot=snapshot,
        pixmap=_FakePixmap("preview", width=91, height=37),
        card_style="QGroupBox { border: none; background: transparent; padding: 0px; }",
        render_label_visible=True,
        render_body_size=(91, 37),
    )

    layout.apply(
        preview=preview,
        controls=panel.preview_controls,
        state=plan,
        canonical_render_state=canonical_render_state,
    )

    controls = panel.preview_controls
    assert controls.card_container._canonical_preview_snapshot is snapshot
    assert controls.card_container.style == canonical_render_state.card_style
    assert controls.single_render_label.visible is True
    assert controls.single_render_label.fixed_size == (91, 37)
    assert controls.single_body_container.fixed_size == (91, 37)
    assert controls.stamp_label.visible is False
    assert controls.detail_label.visible is False


def test_preview_layout_available_width_uses_parent_width_not_stale_preview_width(
    tmp_path: Path,
) -> None:
    panel, _layout = _panel_and_layout(tmp_path)
    preview_controls = panel.preview_controls
    preview_controls.container.fixed_width = 198

    available_width = preview_layout_module._preview_available_width(
        panel.preview,
        container=preview_controls.container,
    )

    assert available_width == 428


def test_preview_layout_available_width_uses_tightest_ancestor_width(tmp_path: Path) -> None:
    panel, _layout = _panel_and_layout(tmp_path)
    preview_controls = panel.preview_controls

    panel.container._width_value = 638
    preview_controls.container.parent._width_value = 550
    preview_controls.container.fixed_width = 622

    available_width = preview_layout_module._preview_available_width(
        panel.preview,
        container=preview_controls.container,
    )

    assert available_width == 498


def test_preview_layout_body_size_caps_card_to_physical_pdf_scale() -> None:
    preview = signing_shell_module.SigningDraftPreview(
        title="",
        page_index=0,
        signature_rect=signing_shell_module.SignatureRect(
            page_index=0,
            left_pt=24.0,
            bottom_pt=18.0,
            width_pt=96.0,
            height_pt=80.0,
        ),
        signer_label_prefix="",
        layout_template=SignatureLayoutTemplate.MULTI_LINE,
        stamp_position=SignatureStampPosition.TOP,
        timezone_display_mode=signing_shell_module.SignatureTimezoneDisplayMode.UTC,
        show_field_names=False,
        datetime_format="%Y-%m-%d %H:%M",
        text_style=signing_shell_module.SignatureTextStyle(
            font_family="Serif",
            font_size_pt=8.5,
            bold=False,
            italic=True,
            text_color_hex="#000000",
        ),
        box_style=SignatureBoxStyle(
            show_border=True,
            border_color_hex="#000000",
            border_width_pt=1.0,
            background_color_hex="#FFFFFF",
        ),
        image_stamp_path=None,
        fields=(),
        detail_text="Adam Smith\nSecretary.LHI@Outlook.com",
        issues=(),
        can_submit=True,
    )

    width, height = preview_layout_module._preview_body_size(
        preview,
        available_width_px=520,
    )

    assert width == 128
    assert height == 107


def test_preview_layout_fit_vertical_band_geometry_preserves_reserved_text_height() -> None:
    fitted = preview_layout_module._fit_vertical_preview_band_geometry(
        text_height=15,
        stamp_height=13,
        separator_height=10,
        inner_body_height_px=38,
        detail_hint_height_px=30,
        rendered_line_count=2,
        stamp_visible=True,
    )

    assert fitted == (33, 0, 5)


def test_preview_layout_fit_vertical_band_geometry_preserves_band_split_when_roomy() -> None:
    fitted = preview_layout_module._fit_vertical_preview_band_geometry(
        text_height=18,
        stamp_height=16,
        separator_height=6,
        inner_body_height_px=56,
        detail_hint_height_px=16,
        rendered_line_count=1,
        stamp_visible=True,
    )

    assert fitted == (18, 32, 6)


def test_preview_layout_vertical_descender_budget_scales_with_line_count() -> None:
    assert preview_layout_module._vertical_preview_descender_budget_px(1) == 2
    assert preview_layout_module._vertical_preview_descender_budget_px(2) == 3
    assert preview_layout_module._vertical_preview_descender_budget_px(5) == 4


def test_preview_layout_font_stack_distinguishes_supported_core_families() -> None:
    assert "Noto Sans" in preview_layout_module._preview_font_stack("Sans Serif")
    assert "Noto Serif" in preview_layout_module._preview_font_stack("Serif")
    assert "DejaVu Sans Mono" in preview_layout_module._preview_font_stack("Monospace")
    assert preview_layout_module._preview_font_stack("Sans Serif") != (
        preview_layout_module._preview_font_stack("Serif")
    )
    assert preview_layout_module._preview_font_stack("Cursive") == "'Noto Sans', sans-serif"
    assert preview_layout_module._preview_font_stack("Fantasy") == "'Noto Sans', sans-serif"


def test_preview_layout_reset_widget_size_constraints_clears_fake_geometry() -> None:
    label = _FakeLabel("Preview")
    label.fixed_size = (140, 32)
    label.fixed_width = 140
    label.maximum_width = 140
    label.minimum_width = 80

    preview_layout_module._reset_widget_size_constraints(label)

    assert label.fixed_size is None
    assert label.fixed_width is None
    assert label.maximum_width is None
    assert label.minimum_width is None


def test_preview_layout_stamp_max_size_is_not_capped_to_legacy_dimensions() -> None:
    appearance = build_signature_appearance(
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.RIGHT,
        image_stamp_path="/tmp/stamp.png",
        signer_label_prefix="",
    )
    preview = signing_shell_module.SigningDraftPreview(
        title="",
        page_index=0,
        signature_rect=signing_shell_module.SignatureRect(
            page_index=0,
            left_pt=24.0,
            bottom_pt=18.0,
            width_pt=320.0,
            height_pt=80.0,
        ),
        signer_label_prefix="",
        layout_template=appearance.layout_template,
        stamp_position=appearance.stamp_position,
        timezone_display_mode=appearance.timezone_display_mode,
        show_field_names=appearance.show_field_names,
        datetime_format=appearance.datetime_format,
        text_style=appearance.text_style,
        box_style=appearance.box_style,
        image_stamp_path=appearance.image_stamp_path,
        fields=(),
        detail_text="Adam Smith",
        issues=(),
        can_submit=True,
    )

    max_width, max_height = preview_layout_module._preview_stamp_max_size(
        preview,
        stamp_text="Adam Smith",
        raw_pixmap=_FakePixmap("/tmp/stamp.png", width=400, height=50),
        stamp_aspect_ratio=8.0,
        available_width_px=520,
    )

    assert max_width > 140
    assert max_height > 0


def test_preview_layout_stamp_max_size_keeps_horizontal_single_line_stamp_inside_short_lane() -> (
    None
):
    appearance = build_signature_appearance(
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.LEFT,
        image_stamp_path="/tmp/stamp.png",
        signer_label_prefix="Digitally signed by",
        text_style=signing_shell_module.SignatureTextStyle(
            font_family="Serif",
            font_size_pt=8.5,
            bold=False,
            italic=False,
            text_color_hex="#000000",
        ),
    )
    preview = signing_shell_module.SigningDraftPreview(
        title="Digitally signed by",
        page_index=3,
        signature_rect=signing_shell_module.SignatureRect(
            page_index=3,
            left_pt=36.86,
            bottom_pt=429.5,
            width_pt=384.506,
            height_pt=28.678,
        ),
        signer_label_prefix=appearance.signer_label_prefix,
        layout_template=appearance.layout_template,
        stamp_position=appearance.stamp_position,
        timezone_display_mode=appearance.timezone_display_mode,
        show_field_names=appearance.show_field_names,
        datetime_format=appearance.datetime_format,
        text_style=appearance.text_style,
        box_style=appearance.box_style,
        image_stamp_path=appearance.image_stamp_path,
        fields=(),
        detail_text="Morgan Ellery | Board Secretary | FoliaSeal | 2026-04-26 17:08",
        issues=(),
        can_submit=True,
    )

    _max_width, max_height = preview_layout_module._preview_stamp_max_size(
        preview,
        stamp_text=(
            "Digitally signed by\nMorgan Ellery | Board Secretary | FoliaSeal | 2026-04-26 17:08"
        ),
        raw_pixmap=_FakePixmap("/tmp/stamp.png", width=1400, height=334),
        stamp_aspect_ratio=1400 / 334,
        available_width_px=514,
    )

    assert max_height <= 23
