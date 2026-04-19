from dataclasses import replace
from pathlib import Path

from PIL import Image

from foliaseal.application import compare_preview_to_request, render_signing_preview
from foliaseal.application.coordinate_transform import PageBox
from foliaseal.application.signing_draft_workflow import (
    SignaturePlacementContext,
    SigningDraftWorkflow,
)
from foliaseal.application.signing_preview_renderer import (
    render_canonical_signature_preview,
)
from foliaseal.domain.models import (
    SignatureFieldSource,
    SignatureLayoutTemplate,
    SignatureStampPosition,
)
from tests.support.phase3_builders import (
    build_signature_appearance,
    build_signature_field_binding,
    build_signature_rect,
    build_signing_request,
)


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
