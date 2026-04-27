import json
from dataclasses import replace
from pathlib import Path

import pytest
from PIL import Image

from foliaseal.application import compare_preview_to_request, render_signing_preview
from foliaseal.application.coordinate_transform import PageBox
from foliaseal.application.signing_draft_workflow import (
    SignaturePlacementContext,
    SigningDraftPreview,
    SigningDraftWorkflow,
)
from foliaseal.application.signing_preview_renderer import (
    SignatureAppearanceSnapshot,
    compare_signature_appearance_snapshots,
    render_canonical_signature_preview,
)
from foliaseal.application.text_raster_analysis import detect_text_content_bounds_in_image
from foliaseal.domain.models import (
    SignatureBoxStyle,
    SignatureFieldSource,
    SignatureLayoutTemplate,
    SignatureStampPosition,
    SignatureTextStyle,
)
from tests.support.phase3_builders import (
    build_signature_appearance,
    build_signature_field_binding,
    build_signature_rect,
    build_signing_request,
)

_MANUAL_HORIZONTAL_SINGLE_LINE_REPLAY_PATH = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "phase3_horizontal_single_line_manual_replay.json"
)


def _load_manual_horizontal_single_line_replay() -> dict:
    return json.loads(_MANUAL_HORIZONTAL_SINGLE_LINE_REPLAY_PATH.read_text())


def _replay_stamp_position(case: dict) -> SignatureStampPosition:
    if case.get("stamp_position") == "right":
        return SignatureStampPosition.RIGHT
    return SignatureStampPosition.LEFT


def _workflow(tmp_path: Path) -> SigningDraftWorkflow:
    return SigningDraftWorkflow(
        input_pdf_path=str(tmp_path / "input.pdf"),
        output_pdf_path=str(tmp_path / "output.pdf"),
        certificate_path=str(tmp_path / "cert.p12"),
        passphrase="secret",
        tsa_url="https://tsa.example.com",
        timestamp_required=True,
        certificate_alias="signing-cert",
    )


def _rectangles_overlap(first: dict[str, int], second: dict[str, int]) -> bool:
    return (
        first["x"] < second["x"] + second["width"]
        and second["x"] < first["x"] + first["width"]
        and first["y"] < second["y"] + second["height"]
        and second["y"] < first["y"] + first["height"]
    )


def test_preview_renderer_formats_semantics_deterministically(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    workflow.set_signature_appearance(
        build_signature_appearance(
            datetime_format="%Y-%m-%d %H:%M",
            image_stamp_path="/tmp/stamp.png",
            stamp_position=SignatureStampPosition.LEFT,
            show_field_names=True,
        )
    )
    workflow.set_placement_context(
        SignaturePlacementContext(
            page_index=2,
            page_box=PageBox(left=0.0, bottom=0.0, right=400.0, top=300.0),
            rotation=0,
        )
    )
    workflow.set_signature_rect(build_signature_rect(page_index=2))

    preview = workflow.preview()
    snapshot = render_signing_preview(preview)

    assert snapshot == render_signing_preview(preview)
    assert snapshot.title == "Digitally signed by"
    assert snapshot.can_submit is True
    assert snapshot.field_count == 8
    assert snapshot.visible_field_count == 7
    assert snapshot.hidden_field_count == 1
    assert snapshot.issue_count == 0
    assert snapshot.lines[0].kind.value == "title"
    assert snapshot.lines[0].text == "Digitally signed by"
    assert any(line.text.startswith("Placement: page=2") for line in snapshot.lines)
    assert any(
        line.kind.value == "field" and "[visible] Email: alice@example.com (override)" in line.text
        for line in snapshot.lines
    )
    assert any(
        line.kind.value == "field" and line.text == "[hidden] Location"
        for line in snapshot.lines
    )
    assert any(
        line.kind.value == "summary" and "Text style: Source Sans 3" in line.text
        for line in snapshot.lines
    )
    assert any(
        line.kind.value == "summary" and "Datetime format: %Y-%m-%d %H:%M" in line.text
        for line in snapshot.lines
    )
    assert any(
        line.kind.value == "summary" and "Image stamp: /tmp/stamp.png" in line.text
        for line in snapshot.lines
    )
    assert any(
        line.kind.value == "summary" and "Stamp position: left" in line.text
        for line in snapshot.lines
    )
    assert any(
        line.kind.value == "status" and line.text == "Ready to sign"
        for line in snapshot.lines
    )


def test_preview_renderer_omits_blank_title_line_when_prefix_is_empty(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    workflow.set_signature_appearance(
        build_signature_appearance(
            signer_label_prefix="",
        )
    )
    workflow.set_signature_rect(build_signature_rect(page_index=2))

    preview = workflow.preview()
    snapshot = render_signing_preview(preview)

    assert preview.title == ""
    assert all(line.kind.value != "title" for line in snapshot.lines)
    assert snapshot.lines[0].kind.value == "summary"


def test_preview_renderer_defaults_to_value_only_field_text(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    workflow.set_signature_appearance(build_signature_appearance())
    workflow.set_signature_rect(build_signature_rect(page_index=2))

    preview = workflow.preview()
    snapshot = render_signing_preview(preview)

    field_lines = [line.text for line in snapshot.lines if line.kind.value == "field"]

    assert preview.show_field_names is False
    assert field_lines[0].startswith("[visible] Distinguished name (derived")
    assert field_lines[1].startswith("[visible] Common name (derived")
    assert field_lines[2] == "[visible] alice@example.com (override)"
    assert field_lines[3] == "[visible] Director (override)"
    assert field_lines[4] == "[visible] FoliaSeal (override)"
    assert field_lines[5].startswith("[visible] 2026-")
    assert field_lines[6] == "[visible] Approved (override)"


def test_preview_parity_report_matches_the_final_request(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    appearance = build_signature_appearance()
    rect = build_signature_rect(page_index=2)
    workflow.set_signature_appearance(appearance)
    workflow.set_signature_rect(rect)

    preview = workflow.preview()
    request = workflow.build_signing_request()
    report = compare_preview_to_request(preview, request)

    assert report.is_consistent is True
    assert report.issues == ()


def test_preview_parity_report_detects_request_drift(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    appearance = build_signature_appearance()
    workflow.set_signature_appearance(appearance)
    workflow.set_signature_rect(build_signature_rect(page_index=2))

    preview = workflow.preview()
    request = build_signing_request(
        tmp_path,
        signature_rect=build_signature_rect(page_index=3),
        signature_appearance=appearance,
    )
    report = compare_preview_to_request(preview, request)

    assert report.is_consistent is False
    assert {issue.code for issue in report.issues} == {"signature_rect_mismatch"}


def test_preview_parity_uses_structural_checks_for_derived_fields(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    appearance = build_signature_appearance()
    workflow.set_signature_appearance(appearance)
    workflow.set_signature_rect(build_signature_rect(page_index=2))

    preview = workflow.preview()
    derived_field = preview.fields[1]
    mutated_preview = replace(
        preview,
        fields=(
            preview.fields[0],
            replace(
                derived_field,
                text="Any derived text is structural here",
            ),
            *preview.fields[2:],
        ),
    )

    report = compare_preview_to_request(mutated_preview, workflow.build_signing_request())

    assert report.is_consistent is True
    assert report.issues == ()


def test_preview_parity_reports_metadata_drift(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    appearance = build_signature_appearance(
        datetime_format="%d/%m/%Y",
        image_stamp_path="/tmp/stamp.png",
    )
    workflow.set_signature_appearance(appearance)
    workflow.set_signature_rect(build_signature_rect(page_index=2))

    preview = workflow.preview()
    drifted_preview = replace(
        preview,
        datetime_format="%Y-%m-%d %H:%M",
        image_stamp_path="/tmp/other-stamp.png",
    )

    report = compare_preview_to_request(drifted_preview, workflow.build_signing_request())

    assert report.is_consistent is False
    assert {issue.code for issue in report.issues} == {
        "datetime_format_mismatch",
        "image_stamp_path_mismatch",
    }


def test_preview_parity_reports_stamp_position_drift(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    appearance = build_signature_appearance()
    workflow.set_signature_appearance(appearance)
    workflow.set_signature_rect(build_signature_rect(page_index=2))

    preview = workflow.preview()
    drifted_preview = replace(preview, stamp_position=SignatureStampPosition.RIGHT)

    report = compare_preview_to_request(drifted_preview, workflow.build_signing_request())

    assert report.is_consistent is False
    assert {issue.code for issue in report.issues} == {"stamp_position_mismatch"}


def test_canonical_preview_renderer_produces_raster_and_bounds(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    stamp_path = tmp_path / "stamp.png"
    Image.new("RGBA", (96, 32), color=(0, 0, 0, 255)).save(stamp_path)
    workflow.set_signature_appearance(
        build_signature_appearance(
            image_stamp_path=str(stamp_path),
            layout_template=SignatureLayoutTemplate.MULTI_LINE,
            stamp_position=SignatureStampPosition.LEFT,
        )
    )
    workflow.set_signature_rect(build_signature_rect(page_index=2, width_pt=180.0, height_pt=48.0))

    preview = workflow.preview()
    snapshot = render_canonical_signature_preview(preview, zoom=2.0)

    assert snapshot is not None
    assert Path(snapshot.image_path).exists()
    assert snapshot.width_px > 0
    assert snapshot.height_px > 0
    assert snapshot.text_bounds_px is not None
    assert snapshot.stamp_bounds_px is not None
    assert snapshot.appearance_snapshot.image_path == snapshot.image_path
    assert snapshot.appearance_snapshot.border_style is not None
    assert snapshot.appearance_snapshot.text_fragments


def test_canonical_preview_renderer_optically_centers_no_stamp_single_line_text(
    tmp_path: Path,
) -> None:
    workflow = _workflow(tmp_path)
    workflow.set_signature_appearance(
        build_signature_appearance(
            signer_label_prefix="Digitally signed by",
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=SignatureStampPosition.TOP,
            image_stamp_path=None,
            show_field_names=False,
            datetime_format="%Y-%m-%d %H:%M:%S %Z",
            text_style=SignatureTextStyle(
                font_family="Sans Serif",
                font_size_pt=8.5,
                bold=False,
                italic=False,
                text_color_hex="#000000",
            ),
            box_style=SignatureBoxStyle(
                show_border=True,
                border_color_hex="#000000",
                border_width_pt=1.0,
                background_color_hex="#FFFFFF",
            ),
            distinguished_name=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            common_name=build_signature_field_binding(
                source=SignatureFieldSource.OVERRIDE,
                show_in_visible_appearance=True,
                override_text="Morgan Ellery",
            ),
            email=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            title=build_signature_field_binding(
                source=SignatureFieldSource.OVERRIDE,
                show_in_visible_appearance=True,
                override_text="Board Secretary",
            ),
            company=build_signature_field_binding(
                source=SignatureFieldSource.OVERRIDE,
                show_in_visible_appearance=True,
                override_text="FoliaSeal",
            ),
            signing_time=build_signature_field_binding(
                source=SignatureFieldSource.OVERRIDE,
                show_in_visible_appearance=True,
                override_text="2026-04-19 01:18",
            ),
            reason=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            location=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
        )
    )
    workflow.set_signature_rect(
        build_signature_rect(page_index=2, width_pt=260.612, height_pt=23.554)
    )

    snapshot = render_canonical_signature_preview(
        workflow.preview(),
        zoom=1.0,
        include_border=False,
    )

    assert snapshot is not None
    assert snapshot.stamp_area_bounds_px is None
    assert snapshot.stamp_bounds_px is None
    assert snapshot.text_area_bounds_px is not None
    assert snapshot.text_bounds_px is not None

    top_gap = snapshot.text_bounds_px["y"] - snapshot.text_area_bounds_px["y"]
    bottom_gap = (
        snapshot.text_area_bounds_px["y"] + snapshot.text_area_bounds_px["height"]
    ) - (
        snapshot.text_bounds_px["y"] + snapshot.text_bounds_px["height"]
    )

    assert bottom_gap >= 0
    assert abs(top_gap - bottom_gap) <= 2


def test_canonical_preview_renderer_can_preserve_transparency_for_gui_use(
    tmp_path: Path,
) -> None:
    workflow = _workflow(tmp_path)
    workflow.set_signature_appearance(
        build_signature_appearance(
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=SignatureStampPosition.TOP,
            image_stamp_path=None,
        )
    )
    workflow.set_signature_rect(
        build_signature_rect(page_index=2, width_pt=260.0, height_pt=24.0)
    )

    snapshot = render_canonical_signature_preview(
        workflow.preview(),
        zoom=1.0,
        include_border=False,
        flatten_to_white=False,
    )

    assert snapshot is not None
    with Image.open(snapshot.image_path).convert("RGBA") as image:
        alpha_values = {
            image.getpixel((x, y))[3]
            for y in range(image.height)
            for x in range(image.width)
        }

    assert 0 in alpha_values


def test_canonical_preview_renderer_keeps_multi_line_top_stamp_and_text_bounds_separate(
    tmp_path: Path,
) -> None:
    workflow = _workflow(tmp_path)
    stamp_path = tmp_path / "stamp.png"
    Image.new("RGBA", (96, 32), color=(0, 0, 0, 255)).save(stamp_path)
    workflow.set_signature_appearance(
        build_signature_appearance(
            signer_label_prefix="Digitally signed by",
            layout_template=SignatureLayoutTemplate.MULTI_LINE,
            stamp_position=SignatureStampPosition.TOP,
            show_field_names=False,
            datetime_format="%Y-%m-%d %H:%M:%S %Z",
            image_stamp_path=str(stamp_path),
            distinguished_name=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            common_name=build_signature_field_binding(
                source=SignatureFieldSource.OVERRIDE,
                show_in_visible_appearance=True,
                override_text="Preview Sweep User",
            ),
            email=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            title=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            company=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            signing_time=build_signature_field_binding(
                source=SignatureFieldSource.OVERRIDE,
                show_in_visible_appearance=True,
                override_text="2026-04-17 02:15:53 UTC",
            ),
            reason=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            location=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
        )
    )
    workflow.set_signature_rect(build_signature_rect(page_index=2, width_pt=260.0, height_pt=46.0))

    snapshot = render_canonical_signature_preview(workflow.preview(), zoom=2.0)

    assert snapshot is not None
    assert snapshot.text_area_bounds_px is not None
    assert snapshot.stamp_area_bounds_px is not None
    assert snapshot.text_bounds_px is not None
    assert snapshot.stamp_bounds_px is not None
    assert snapshot.stamp_area_bounds_px["height"] > 0
    assert snapshot.text_bounds_px["y"] >= (
        snapshot.stamp_bounds_px["y"] + snapshot.stamp_bounds_px["height"]
    )


def test_canonical_preview_renderer_preserves_top_inset_for_multi_line_top_stamp(
    tmp_path: Path,
) -> None:
    workflow = _workflow(tmp_path)
    stamp_path = tmp_path / "tall_stamp.png"
    Image.new("RGBA", (12, 32), color=(0, 0, 0, 255)).save(stamp_path)
    workflow.set_signature_appearance(
        build_signature_appearance(
            signer_label_prefix="Digitally signed by",
            layout_template=SignatureLayoutTemplate.MULTI_LINE,
            stamp_position=SignatureStampPosition.TOP,
            show_field_names=False,
            image_stamp_path=str(stamp_path),
            distinguished_name=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            common_name=build_signature_field_binding(
                source=SignatureFieldSource.OVERRIDE,
                show_in_visible_appearance=True,
                override_text="Preview Sweep User",
            ),
            email=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            title=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            company=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            signing_time=build_signature_field_binding(
                source=SignatureFieldSource.OVERRIDE,
                show_in_visible_appearance=True,
                override_text="2026-04-17 02:15:53 UTC",
            ),
            reason=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            location=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
        )
    )
    workflow.set_signature_rect(build_signature_rect(page_index=2, width_pt=260.0, height_pt=46.0))

    snapshot = render_canonical_signature_preview(workflow.preview(), zoom=2.0)

    assert snapshot is not None
    assert snapshot.stamp_area_bounds_px is not None
    assert snapshot.stamp_bounds_px is not None
    assert snapshot.stamp_bounds_px["y"] > snapshot.stamp_area_bounds_px["y"]


def test_canonical_preview_renderer_preserves_top_inset_for_wrapped_block_top_stamp(
    tmp_path: Path,
) -> None:
    workflow = _workflow(tmp_path)
    stamp_path = tmp_path / "tall_stamp_wrapped.png"
    Image.new("RGBA", (12, 32), color=(0, 0, 0, 255)).save(stamp_path)
    workflow.set_signature_appearance(
        build_signature_appearance(
            signer_label_prefix="Digitally signed by",
            layout_template=SignatureLayoutTemplate.WRAPPED_BLOCK,
            stamp_position=SignatureStampPosition.TOP,
            show_field_names=True,
            image_stamp_path=str(stamp_path),
            distinguished_name=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            common_name=build_signature_field_binding(
                source=SignatureFieldSource.OVERRIDE,
                show_in_visible_appearance=True,
                override_text="Preview Sweep User",
            ),
            email=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            title=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            company=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            signing_time=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            reason=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            location=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
        )
    )
    workflow.set_signature_rect(build_signature_rect(page_index=2, width_pt=260.0, height_pt=54.0))

    snapshot = render_canonical_signature_preview(workflow.preview(), zoom=2.0)

    assert snapshot is not None
    assert snapshot.stamp_area_bounds_px is not None
    assert snapshot.stamp_bounds_px is not None
    assert snapshot.stamp_bounds_px["y"] > snapshot.stamp_area_bounds_px["y"]


def test_canonical_preview_renderer_preserves_bottom_inset_for_wrapped_block_bottom_stamp(
    tmp_path: Path,
) -> None:
    workflow = _workflow(tmp_path)
    stamp_path = tmp_path / "bottom_tall_stamp.png"
    Image.new("RGBA", (12, 40), color=(0, 0, 0, 255)).save(stamp_path)
    workflow.set_signature_appearance(
        build_signature_appearance(
            signer_label_prefix="Digitally signed by",
            layout_template=SignatureLayoutTemplate.WRAPPED_BLOCK,
            stamp_position=SignatureStampPosition.BOTTOM,
            show_field_names=True,
            image_stamp_path=str(stamp_path),
            distinguished_name=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            common_name=build_signature_field_binding(
                source=SignatureFieldSource.OVERRIDE,
                show_in_visible_appearance=True,
                override_text="Preview Sweep User",
            ),
            email=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            title=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            company=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            signing_time=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            reason=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            location=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
        )
    )
    workflow.set_signature_rect(build_signature_rect(page_index=2, width_pt=260.0, height_pt=54.0))

    snapshot = render_canonical_signature_preview(workflow.preview(), zoom=2.0)

    assert snapshot is not None
    assert snapshot.stamp_area_bounds_px is not None
    assert snapshot.stamp_bounds_px is not None
    stamp_bottom = snapshot.stamp_bounds_px["y"] + snapshot.stamp_bounds_px["height"]
    area_bottom = snapshot.stamp_area_bounds_px["y"] + snapshot.stamp_area_bounds_px["height"]
    assert stamp_bottom < area_bottom


def test_canonical_preview_renderer_preserves_right_inset_for_wrapped_block_right_stamp(
    tmp_path: Path,
) -> None:
    workflow = _workflow(tmp_path)
    stamp_path = tmp_path / "right_script_stamp.png"
    Image.new("RGBA", (40, 12), color=(0, 0, 0, 255)).save(stamp_path)
    workflow.set_signature_appearance(
        build_signature_appearance(
            signer_label_prefix="Digitally signed by",
            layout_template=SignatureLayoutTemplate.WRAPPED_BLOCK,
            stamp_position=SignatureStampPosition.RIGHT,
            show_field_names=True,
            image_stamp_path=str(stamp_path),
            distinguished_name=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            common_name=build_signature_field_binding(
                source=SignatureFieldSource.OVERRIDE,
                show_in_visible_appearance=True,
                override_text="Preview Sweep User",
            ),
            email=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            title=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            company=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            signing_time=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            reason=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            location=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
        )
    )
    workflow.set_signature_rect(build_signature_rect(page_index=2, width_pt=220.0, height_pt=62.0))

    snapshot = render_canonical_signature_preview(workflow.preview(), zoom=2.0)

    assert snapshot is not None
    assert snapshot.stamp_area_bounds_px is not None
    assert snapshot.stamp_bounds_px is not None
    stamp_right = snapshot.stamp_bounds_px["x"] + snapshot.stamp_bounds_px["width"]
    area_right = snapshot.stamp_area_bounds_px["x"] + snapshot.stamp_area_bounds_px["width"]
    assert stamp_right < area_right


def test_canonical_preview_renderer_preserves_left_inset_for_wrapped_block_left_stamp(
    tmp_path: Path,
) -> None:
    workflow = _workflow(tmp_path)
    stamp_path = tmp_path / "left_script_stamp.png"
    Image.new("RGBA", (40, 12), color=(0, 0, 0, 255)).save(stamp_path)
    workflow.set_signature_appearance(
        build_signature_appearance(
            signer_label_prefix="Digitally signed by",
            layout_template=SignatureLayoutTemplate.WRAPPED_BLOCK,
            stamp_position=SignatureStampPosition.LEFT,
            show_field_names=True,
            image_stamp_path=str(stamp_path),
            distinguished_name=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            common_name=build_signature_field_binding(
                source=SignatureFieldSource.OVERRIDE,
                show_in_visible_appearance=True,
                override_text="Preview Sweep User",
            ),
            email=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            title=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            company=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            signing_time=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            reason=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            location=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
        )
    )
    workflow.set_signature_rect(build_signature_rect(page_index=2, width_pt=220.0, height_pt=62.0))

    snapshot = render_canonical_signature_preview(workflow.preview(), zoom=2.0)

    assert snapshot is not None
    assert snapshot.stamp_area_bounds_px is not None
    assert snapshot.stamp_bounds_px is not None
    assert snapshot.stamp_bounds_px["x"] > snapshot.stamp_area_bounds_px["x"]


def test_canonical_preview_renderer_suppresses_stamp_when_single_line_left_text_lane_collapses(
    tmp_path: Path,
) -> None:
    stamp_path = tmp_path / "left_script_stamp.png"
    Image.new("RGBA", (640, 160), color=(0, 0, 0, 160)).save(stamp_path)
    preview = SigningDraftPreview(
        title="Digitally signed by",
        page_index=0,
        signature_rect=build_signature_rect(
            page_index=0,
            left_pt=35.84,
            bottom_pt=427.46,
            width_pt=258.302,
            height_pt=89.608,
        ),
        signer_label_prefix="Digitally signed by",
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.LEFT,
        timezone_display_mode=None,
        show_field_names=False,
        datetime_format="%Y-%m-%d %H:%M",
        text_style=SignatureTextStyle(
            font_family="Serif",
            font_size_pt=8.5,
            bold=False,
            italic=False,
            text_color_hex="#000000",
        ),
        box_style=SignatureBoxStyle(
            show_border=True,
            border_color_hex="#000000",
            border_width_pt=1.0,
            background_color_hex="#FFFFFF",
        ),
        image_stamp_path=str(stamp_path),
        fields=(),
        detail_text="Morgan Ellery | Board Secretary | FoliaSeal | 2026-04-25 02:37",
        issues=(),
        can_submit=False,
    )

    snapshot = render_canonical_signature_preview(
        preview,
        zoom=1.0,
        use_horizontal_ink_reservation=False,
    )

    assert snapshot is not None
    assert snapshot.stamp_bounds_px is None
    assert snapshot.text_bounds_px is not None
    assert snapshot.text_bounds_px["x"] < snapshot.width_px


def test_canonical_preview_renderer_suppresses_stamp_when_single_line_left_text_would_overlap(
    tmp_path: Path,
) -> None:
    stamp_path = tmp_path / "left_script_stamp.png"
    Image.new("RGBA", (640, 160), color=(0, 0, 0, 160)).save(stamp_path)
    preview = SigningDraftPreview(
        title="Digitally signed by",
        page_index=0,
        signature_rect=build_signature_rect(
            page_index=0,
            left_pt=36.35,
            bottom_pt=428.48,
            width_pt=257.538,
            height_pt=55.288,
        ),
        signer_label_prefix="Digitally signed by",
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.LEFT,
        timezone_display_mode=None,
        show_field_names=False,
        datetime_format="%Y-%m-%d %H:%M",
        text_style=SignatureTextStyle(
            font_family="Serif",
            font_size_pt=8.5,
            bold=False,
            italic=False,
            text_color_hex="#000000",
        ),
        box_style=SignatureBoxStyle(
            show_border=True,
            border_color_hex="#000000",
            border_width_pt=1.0,
            background_color_hex="#FFFFFF",
        ),
        image_stamp_path=str(stamp_path),
        fields=(),
        detail_text="Morgan Ellery | Board Secretary | FoliaSeal | 2026-04-25 02:52",
        issues=(),
        can_submit=False,
    )

    snapshot = render_canonical_signature_preview(
        preview,
        zoom=1.0,
        use_horizontal_ink_reservation=False,
    )

    assert snapshot is not None
    assert snapshot.stamp_bounds_px is None
    assert snapshot.text_bounds_px is not None
    assert snapshot.text_bounds_px["width"] > 100


def test_canonical_preview_renderer_keeps_best_effort_stamp_for_usable_text_lane(
    tmp_path: Path,
) -> None:
    stamp_path = tmp_path / "left_script_stamp.png"
    Image.new("RGBA", (640, 160), color=(0, 0, 0, 160)).save(stamp_path)
    preview = SigningDraftPreview(
        title="Digitally signed by",
        page_index=0,
        signature_rect=build_signature_rect(
            page_index=0,
            left_pt=35.33,
            bottom_pt=428.48,
            width_pt=343.044,
            height_pt=49.144,
        ),
        signer_label_prefix="Digitally signed by",
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.LEFT,
        timezone_display_mode=None,
        show_field_names=False,
        datetime_format="%Y-%m-%d %H:%M",
        text_style=SignatureTextStyle(
            font_family="Serif",
            font_size_pt=8.5,
            bold=False,
            italic=False,
            text_color_hex="#000000",
        ),
        box_style=SignatureBoxStyle(
            show_border=True,
            border_color_hex="#000000",
            border_width_pt=1.0,
            background_color_hex="#FFFFFF",
        ),
        image_stamp_path=str(stamp_path),
        fields=(),
        detail_text="Morgan Ellery | Board Secretary | FoliaSeal | 2026-04-25 13:19",
        issues=(),
        can_submit=False,
    )

    snapshot = render_canonical_signature_preview(preview, zoom=1.0)

    assert snapshot is not None
    assert snapshot.stamp_bounds_px is not None
    assert snapshot.text_bounds_px is not None
    assert snapshot.stamp_bounds_px["x"] < snapshot.text_bounds_px["x"]


def test_canonical_preview_renderer_sizes_horizontal_single_line_stamp_from_remaining_lane(
    tmp_path: Path,
) -> None:
    stamp_path = tmp_path / "right_script_stamp.png"
    Image.new("RGBA", (1400, 334), color=(0, 0, 0, 160)).save(stamp_path)
    preview = SigningDraftPreview(
        title="Digitally signed by",
        page_index=3,
        signature_rect=build_signature_rect(
            page_index=3,
            left_pt=34.82,
            bottom_pt=428.48,
            width_pt=373.25,
            height_pt=36.86,
        ),
        signer_label_prefix="Digitally signed by",
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.RIGHT,
        timezone_display_mode=None,
        show_field_names=False,
        datetime_format="%Y-%m-%d %H:%M",
        text_style=SignatureTextStyle(
            font_family="Serif",
            font_size_pt=8.5,
            bold=False,
            italic=False,
            text_color_hex="#000000",
        ),
        box_style=SignatureBoxStyle(
            show_border=True,
            border_color_hex="#000000",
            border_width_pt=1.0,
            background_color_hex="#FFFFFF",
        ),
        image_stamp_path=str(stamp_path),
        fields=(),
        detail_text="Morgan Ellery | Board Secretary | FoliaSeal | 2026-04-25 15:26",
        issues=(),
        can_submit=False,
    )

    snapshot = render_canonical_signature_preview(
        preview,
        zoom=1.0,
        use_horizontal_ink_reservation=False,
    )

    assert snapshot is not None
    assert snapshot.text_area_bounds_px is not None
    assert snapshot.stamp_area_bounds_px is not None
    assert snapshot.stamp_bounds_px is not None
    assert snapshot.text_area_bounds_px["width"] >= 254
    assert snapshot.stamp_area_bounds_px["width"] < 115
    assert snapshot.stamp_bounds_px["width"] <= snapshot.stamp_area_bounds_px["width"]
    assert snapshot.text_area_bounds_px["x"] + snapshot.text_area_bounds_px["width"] <= (
        snapshot.stamp_area_bounds_px["x"]
    )


def test_canonical_preview_renderer_uses_ink_reservation_for_horizontal_single_line_stamp(
    tmp_path: Path,
) -> None:
    stamp_path = tmp_path / "script_stamp.png"
    Image.new("RGBA", (1400, 334), color=(0, 0, 0, 160)).save(stamp_path)
    preview = SigningDraftPreview(
        title="Digitally signed by",
        page_index=3,
        signature_rect=build_signature_rect(
            page_index=3,
            left_pt=34.82,
            bottom_pt=428.48,
            width_pt=373.25,
            height_pt=36.86,
        ),
        signer_label_prefix="Digitally signed by",
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.LEFT,
        timezone_display_mode=None,
        show_field_names=False,
        datetime_format="%Y-%m-%d %H:%M",
        text_style=SignatureTextStyle(
            font_family="Serif",
            font_size_pt=8.5,
            bold=False,
            italic=False,
            text_color_hex="#000000",
        ),
        box_style=SignatureBoxStyle(
            show_border=True,
            border_color_hex="#000000",
            border_width_pt=1.0,
            background_color_hex="#FFFFFF",
        ),
        image_stamp_path=str(stamp_path),
        fields=(),
        detail_text="Morgan Ellery | Board Secretary | FoliaSeal | 2026-04-26 21:19",
        issues=(),
        can_submit=True,
    )

    structural_snapshot = render_canonical_signature_preview(
        preview,
        zoom=1.0,
        use_horizontal_ink_reservation=False,
    )
    ink_snapshot = render_canonical_signature_preview(preview, zoom=1.0)

    assert structural_snapshot is not None
    assert structural_snapshot.stamp_area_bounds_px is not None
    assert ink_snapshot is not None
    assert ink_snapshot.stamp_area_bounds_px is not None
    assert ink_snapshot.stamp_area_bounds_px["width"] > structural_snapshot.stamp_area_bounds_px[
        "width"
    ]
    assert ink_snapshot.stamp_bounds_px is not None
    assert ink_snapshot.text_area_bounds_px is not None
    text_bounds, error = detect_text_content_bounds_in_image(
        preview_image_path=ink_snapshot.image_path,
        text_widget_bounds=ink_snapshot.text_area_bounds_px,
        text_color_rgba=(0, 0, 0, 255),
        reference_text_content_bounds=ink_snapshot.text_bounds_px,
    )

    assert error is None
    assert text_bounds is not None
    assert not _rectangles_overlap(text_bounds, ink_snapshot.stamp_bounds_px)
    assert ink_snapshot.width_px - (text_bounds["x"] + text_bounds["width"]) > 0


def test_canonical_preview_renderer_keeps_left_stamp_when_only_nominal_height_overflows(
    tmp_path: Path,
) -> None:
    stamp_path = tmp_path / "left_script_stamp.png"
    Image.new("RGBA", (1400, 334), color=(0, 0, 0, 160)).save(stamp_path)
    preview = SigningDraftPreview(
        title="Digitally signed by",
        page_index=3,
        signature_rect=build_signature_rect(
            page_index=3,
            left_pt=34.3,
            bottom_pt=428.99,
            width_pt=423.43,
            height_pt=24.068,
        ),
        signer_label_prefix="Digitally signed by",
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.LEFT,
        timezone_display_mode=None,
        show_field_names=False,
        datetime_format="%Y-%m-%d %H:%M",
        text_style=SignatureTextStyle(
            font_family="Serif",
            font_size_pt=8.5,
            bold=False,
            italic=False,
            text_color_hex="#000000",
        ),
        box_style=SignatureBoxStyle(
            show_border=True,
            border_color_hex="#000000",
            border_width_pt=1.0,
            background_color_hex="#FFFFFF",
        ),
        image_stamp_path=str(stamp_path),
        fields=(),
        detail_text="Morgan Ellery | Board Secretary | FoliaSeal | 2026-04-26 17:27",
        issues=(),
        can_submit=False,
    )

    snapshot = render_canonical_signature_preview(preview, zoom=1.0)

    assert snapshot is not None
    assert snapshot.stamp_area_bounds_px is not None
    assert snapshot.stamp_bounds_px is not None
    assert snapshot.stamp_bounds_px["height"] <= snapshot.stamp_area_bounds_px["height"]
    assert snapshot.text_bounds_px is not None
    assert snapshot.stamp_bounds_px["x"] < snapshot.text_bounds_px["x"]


def test_canonical_preview_renderer_preserves_horizontal_text_border_guard(
    tmp_path: Path,
) -> None:
    stamp_path = tmp_path / "left_script_stamp.png"
    Image.new("RGBA", (1400, 334), color=(0, 0, 0, 160)).save(stamp_path)
    preview = SigningDraftPreview(
        title="Digitally signed by",
        page_index=3,
        signature_rect=build_signature_rect(
            page_index=3,
            left_pt=35.84,
            bottom_pt=428.99,
            width_pt=296.96,
            height_pt=22.53,
        ),
        signer_label_prefix="Digitally signed by",
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.LEFT,
        timezone_display_mode=None,
        show_field_names=False,
        datetime_format="%Y-%m-%d %H:%M",
        text_style=SignatureTextStyle(
            font_family="Serif",
            font_size_pt=8.5,
            bold=False,
            italic=False,
            text_color_hex="#000000",
        ),
        box_style=SignatureBoxStyle(
            show_border=True,
            border_color_hex="#000000",
            border_width_pt=1.0,
            background_color_hex="#FFFFFF",
        ),
        image_stamp_path=str(stamp_path),
        fields=(),
        detail_text="Morgan Ellery | Board Secretary | FoliaSeal | 2026-04-26 17:34",
        issues=(),
        can_submit=True,
    )

    snapshot = render_canonical_signature_preview(preview, zoom=1.0)

    assert snapshot is not None
    assert snapshot.text_area_bounds_px is not None
    text_bounds, error = detect_text_content_bounds_in_image(
        preview_image_path=snapshot.image_path,
        text_widget_bounds=snapshot.text_area_bounds_px,
        text_color_rgba=(0, 0, 0, 255),
        reference_text_content_bounds=snapshot.text_bounds_px,
    )

    assert error is None
    assert text_bounds is not None
    assert snapshot.width_px - (text_bounds["x"] + text_bounds["width"]) >= 1


def test_canonical_preview_renderer_aligns_left_stamp_text_ink_to_border(
    tmp_path: Path,
) -> None:
    stamp_path = tmp_path / "left_script_stamp.png"
    Image.new("RGBA", (1400, 334), color=(0, 0, 0, 160)).save(stamp_path)
    preview = SigningDraftPreview(
        title="Digitally signed by",
        page_index=3,
        signature_rect=build_signature_rect(
            page_index=3,
            left_pt=36.7,
            bottom_pt=428.6,
            width_pt=328.19,
            height_pt=22.53,
        ),
        signer_label_prefix="Digitally signed by",
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.LEFT,
        timezone_display_mode=None,
        show_field_names=False,
        datetime_format="%Y-%m-%d %H:%M",
        text_style=SignatureTextStyle(
            font_family="Serif",
            font_size_pt=8.5,
            bold=False,
            italic=False,
            text_color_hex="#000000",
        ),
        box_style=SignatureBoxStyle(
            show_border=True,
            border_color_hex="#000000",
            border_width_pt=1.0,
            background_color_hex="#FFFFFF",
        ),
        image_stamp_path=str(stamp_path),
        fields=(),
        detail_text="Morgan Ellery | Board Secretary | FoliaSeal | 2026-04-27 12:04",
        issues=(),
        can_submit=True,
    )

    snapshot = render_canonical_signature_preview(preview, zoom=1.0)

    assert snapshot is not None
    assert snapshot.text_area_bounds_px is not None
    assert snapshot.stamp_bounds_px is not None
    text_bounds, error = detect_text_content_bounds_in_image(
        preview_image_path=snapshot.image_path,
        text_widget_bounds=snapshot.text_area_bounds_px,
        text_color_rgba=(0, 0, 0, 255),
        reference_text_content_bounds=snapshot.text_bounds_px,
    )

    assert error is None
    assert text_bounds is not None
    right_border_gap_px = snapshot.width_px - (
        text_bounds["x"] + text_bounds["width"]
    )
    assert 1 <= right_border_gap_px <= 6
    assert not _rectangles_overlap(text_bounds, snapshot.stamp_bounds_px)


@pytest.mark.parametrize(
    "stamp_position",
    [SignatureStampPosition.LEFT, SignatureStampPosition.RIGHT],
)
def test_canonical_preview_renderer_preserves_both_horizontal_text_edges(
    tmp_path: Path,
    stamp_position: SignatureStampPosition,
) -> None:
    stamp_path = tmp_path / "script_stamp.png"
    Image.new("RGBA", (1400, 334), color=(0, 0, 0, 160)).save(stamp_path)
    preview = SigningDraftPreview(
        title="Digitally signed by",
        page_index=3,
        signature_rect=build_signature_rect(
            page_index=3,
            left_pt=35.0,
            bottom_pt=428.0,
            width_pt=430.0,
            height_pt=44.0,
        ),
        signer_label_prefix="Digitally signed by",
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=stamp_position,
        timezone_display_mode=None,
        show_field_names=False,
        datetime_format="%Y-%m-%d %H:%M",
        text_style=SignatureTextStyle(
            font_family="Serif",
            font_size_pt=8.5,
            bold=False,
            italic=False,
            text_color_hex="#000000",
        ),
        box_style=SignatureBoxStyle(
            show_border=True,
            border_color_hex="#000000",
            border_width_pt=1.0,
            background_color_hex="#FFFFFF",
        ),
        image_stamp_path=str(stamp_path),
        fields=(),
        detail_text="Morgan Ellery | Board Secretary | FoliaSeal | 2026-04-26 17:34",
        issues=(),
        can_submit=True,
    )

    snapshot = render_canonical_signature_preview(preview, zoom=1.0)

    assert snapshot is not None
    assert snapshot.text_area_bounds_px is not None
    assert snapshot.stamp_bounds_px is not None
    text_bounds, error = detect_text_content_bounds_in_image(
        preview_image_path=snapshot.image_path,
        text_widget_bounds=snapshot.text_area_bounds_px,
        text_color_rgba=(0, 0, 0, 255),
        reference_text_content_bounds=snapshot.text_bounds_px,
    )

    assert error is None
    assert text_bounds is not None
    assert not _rectangles_overlap(text_bounds, snapshot.stamp_bounds_px)
    if stamp_position == SignatureStampPosition.LEFT:
        assert snapshot.width_px - (text_bounds["x"] + text_bounds["width"]) > 0
        assert text_bounds["x"] - (
            snapshot.stamp_bounds_px["x"] + snapshot.stamp_bounds_px["width"]
        ) > 0
    else:
        assert text_bounds["x"] > 0
        assert snapshot.stamp_bounds_px["x"] - (
            text_bounds["x"] + text_bounds["width"]
        ) > 0


def test_manual_caps_4_to_8_replay_preserves_preview_geometry(
    tmp_path: Path,
) -> None:
    replay = _load_manual_horizontal_single_line_replay()
    stamp_path = tmp_path / "manual-replay-signature.png"
    Image.new("RGBA", (1400, 334), color=(0, 0, 0, 160)).save(stamp_path)
    appearance_config = replay["appearance"]
    _title, detail_text = appearance_config["stamp_text"].split("\n", 1)

    for case in replay["cases"]:
        stamp_position = _replay_stamp_position(case)
        preview = SigningDraftPreview(
            title=appearance_config["signer_label_prefix"],
            page_index=3,
            signature_rect=build_signature_rect(
                page_index=3,
                left_pt=36.7,
                bottom_pt=428.6,
                width_pt=case["width_pt"],
                height_pt=case["height_pt"],
            ),
            signer_label_prefix=appearance_config["signer_label_prefix"],
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=stamp_position,
            timezone_display_mode=None,
            show_field_names=False,
            datetime_format=appearance_config["datetime_format"],
            text_style=SignatureTextStyle(
                font_family=appearance_config["font_family"],
                font_size_pt=appearance_config["font_size_pt"],
                bold=False,
                italic=False,
                text_color_hex="#000000",
            ),
            box_style=SignatureBoxStyle(
                show_border=True,
                border_color_hex="#000000",
                border_width_pt=1.0,
                background_color_hex="#FFFFFF",
            ),
            image_stamp_path=str(stamp_path),
            fields=(),
            detail_text=detail_text,
            issues=(),
            can_submit=case["expected_backend_ready"],
        )

        snapshot = render_canonical_signature_preview(preview, zoom=1.0)

        assert snapshot is not None, case["label"]
        assert snapshot.text_area_bounds_px is not None, case["label"]
        text_bounds, error = detect_text_content_bounds_in_image(
            preview_image_path=snapshot.image_path,
            text_widget_bounds=snapshot.text_area_bounds_px,
            text_color_rgba=(0, 0, 0, 255),
            reference_text_content_bounds=snapshot.text_bounds_px,
        )

        assert error is None, case["label"]
        assert text_bounds is not None, case["label"]
        assert snapshot.width_px - (text_bounds["x"] + text_bounds["width"]) > 0, (
            case["label"]
        )
        if snapshot.stamp_bounds_px is not None:
            assert not _rectangles_overlap(text_bounds, snapshot.stamp_bounds_px), (
                case["label"]
            )
            if stamp_position == SignatureStampPosition.LEFT:
                assert text_bounds["x"] - (
                    snapshot.stamp_bounds_px["x"] + snapshot.stamp_bounds_px["width"]
                ) > 0, case["label"]
            else:
                assert snapshot.stamp_bounds_px["x"] - (
                    text_bounds["x"] + text_bounds["width"]
                ) > 0, case["label"]


def test_compare_signature_appearance_snapshots_reports_layer_specific_mismatch() -> None:
    preview = SignatureAppearanceSnapshot(
        image_path="preview.png",
        image_size_px={"width": 120, "height": 40},
        container_bounds_px={"x": 0, "y": 0, "width": 120, "height": 40},
        border_bounds_px={"x": 0, "y": 0, "width": 120, "height": 40},
        border_style={"show_border": True, "shape": "rounded"},
        text_bounds_px={"x": 8, "y": 10, "width": 90, "height": 12},
        stamp_bounds_px=None,
        text_fragments=("Morgan Ellery", "2026-04-11 09:00"),
        line_bounds_px=(),
    )
    signed = SignatureAppearanceSnapshot(
        image_path="signed.png",
        image_size_px={"width": 120, "height": 40},
        container_bounds_px={"x": 0, "y": 0, "width": 120, "height": 40},
        border_bounds_px={"x": 0, "y": 0, "width": 120, "height": 40},
        border_style={"show_border": True, "shape": "square"},
        text_bounds_px={"x": 8, "y": 10, "width": 90, "height": 12},
        stamp_bounds_px=None,
        text_fragments=("Morgan Ellery", "2026-04-11 09:00"),
        line_bounds_px=(),
    )

    comparison = compare_signature_appearance_snapshots(preview, signed)

    assert comparison.is_consistent is False
    assert comparison.border.matches is False
    assert comparison.border.reason == "Border style differs between preview and signed output."
    assert comparison.text.matches is True
    assert comparison.stamp.matches is True


def test_compare_signature_appearance_snapshots_normalizes_signing_time_text() -> None:
    preview = SignatureAppearanceSnapshot(
        image_path="preview.png",
        image_size_px={"width": 120, "height": 40},
        container_bounds_px={"x": 0, "y": 0, "width": 120, "height": 40},
        border_bounds_px={"x": 0, "y": 0, "width": 120, "height": 40},
        border_style={"show_border": True, "shape": "rounded"},
        text_bounds_px={"x": 8, "y": 10, "width": 90, "height": 12},
        stamp_bounds_px=None,
        text_fragments=("Digitally signed by", "Morgan Ellery | 2026-04-20 00:55:03 UTC"),
        line_bounds_px=(),
    )
    signed = SignatureAppearanceSnapshot(
        image_path="signed.png",
        image_size_px={"width": 120, "height": 40},
        container_bounds_px={"x": 0, "y": 0, "width": 120, "height": 40},
        border_bounds_px={"x": 0, "y": 0, "width": 120, "height": 40},
        border_style={"show_border": True, "shape": "rounded"},
        text_bounds_px={"x": 8, "y": 10, "width": 90, "height": 12},
        stamp_bounds_px=None,
        text_fragments=("Digitally signed by", "Morgan Ellery | 2026-04-20 00:55:04 UTC"),
        line_bounds_px=(),
    )

    comparison = compare_signature_appearance_snapshots(preview, signed)

    assert comparison.text.matches is True


def test_compare_signature_appearance_snapshots_prefers_line_bounds_when_available() -> None:
    preview = SignatureAppearanceSnapshot(
        image_path="preview.png",
        image_size_px={"width": 120, "height": 40},
        container_bounds_px={"x": 0, "y": 0, "width": 120, "height": 40},
        border_bounds_px={"x": 0, "y": 0, "width": 120, "height": 40},
        border_style={"show_border": True, "shape": "rounded"},
        text_bounds_px={"x": 8, "y": 10, "width": 90, "height": 20},
        stamp_bounds_px=None,
        text_fragments=("Digitally signed by", "Morgan Ellery"),
        line_bounds_px=(
            {"x": 8, "y": 10, "width": 70, "height": 8},
            {"x": 8, "y": 22, "width": 90, "height": 8},
        ),
    )
    signed = SignatureAppearanceSnapshot(
        image_path="signed.png",
        image_size_px={"width": 120, "height": 40},
        container_bounds_px={"x": 0, "y": 0, "width": 120, "height": 40},
        border_bounds_px={"x": 0, "y": 0, "width": 120, "height": 40},
        border_style={"show_border": True, "shape": "rounded"},
        text_bounds_px={"x": 8, "y": 10, "width": 90, "height": 20},
        stamp_bounds_px=None,
        text_fragments=("Digitally signed by", "Morgan Ellery"),
        line_bounds_px=(
            {"x": 8, "y": 10, "width": 70, "height": 8},
            {"x": 18, "y": 22, "width": 90, "height": 8},
        ),
    )

    comparison = compare_signature_appearance_snapshots(preview, signed)

    assert comparison.text.matches is False
    assert comparison.text.reason == "Rendered text line bounds differ after normalization."


def test_render_canonical_preview_includes_title_in_text_fragments(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    workflow.set_signature_appearance(
        build_signature_appearance(
            signer_label_prefix="Digitally signed by",
            show_field_names=False,
        )
    )
    workflow.set_signature_rect(build_signature_rect(page_index=0, width_pt=320.0, height_pt=42.0))

    snapshot = render_canonical_signature_preview(workflow.preview())

    assert snapshot is not None
    assert snapshot.appearance_snapshot is not None
    assert snapshot.appearance_snapshot.text_fragments[0] == "Digitally signed by"
    assert len(snapshot.appearance_snapshot.line_bounds_px) == len(
        snapshot.appearance_snapshot.text_fragments
    )
    assert (
        snapshot.appearance_snapshot.line_bounds_px[0]["y"]
        < snapshot.appearance_snapshot.line_bounds_px[1]["y"]
    )
