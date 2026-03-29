from pathlib import Path

import pytest

from foliaseal.application.coordinate_transform import PageBox, ViewRect, ViewTransform
from foliaseal.application.signing_draft_workflow import (
    SignaturePlacementContext,
    SigningDraftValidationError,
    SigningDraftWorkflow,
)
from foliaseal.domain.models import (
    SignatureAppearance,
    SignatureFieldBinding,
    SignatureFieldSource,
    SignatureLayoutTemplate,
    SignaturePlacementDefaults,
    SignatureRect,
    SignatureTextStyle,
    SignatureTimezoneDisplayMode,
)
from foliaseal.infra.config.schemas import SignaturePreset


def _appearance() -> SignatureAppearance:
    return SignatureAppearance(
        signer_label_prefix="Digitally signed by",
        layout_template=SignatureLayoutTemplate.WRAPPED_BLOCK,
        timezone_display_mode=SignatureTimezoneDisplayMode.UTC,
        datetime_format="%Y-%m-%d %H:%M",
        common_name=SignatureFieldBinding(
            source=SignatureFieldSource.DERIVED,
            show_in_visible_appearance=True,
        ),
        email=SignatureFieldBinding(
            source=SignatureFieldSource.OVERRIDE,
            show_in_visible_appearance=True,
            override_text="alice@example.com",
        ),
        signing_time=SignatureFieldBinding(
            source=SignatureFieldSource.DERIVED,
            show_in_visible_appearance=True,
        ),
        reason=SignatureFieldBinding(
            source=SignatureFieldSource.OVERRIDE,
            show_in_visible_appearance=True,
            override_text="Approved",
        ),
        location=SignatureFieldBinding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        text_style=SignatureTextStyle(
            font_family="Source Sans 3",
            font_size_pt=9.0,
            bold=True,
            italic=False,
            text_color_hex="#112233",
        ),
        image_stamp_path="/tmp/stamp.png",
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


def test_workflow_builds_preview_and_final_request(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    workflow.set_signature_appearance(_appearance())
    workflow.set_signature_rect(
        SignatureRect(
            page_index=2,
            left_pt=24.0,
            bottom_pt=18.0,
            width_pt=220.0,
            height_pt=80.0,
        )
    )

    preview = workflow.preview()
    request = workflow.build_signing_request()

    assert preview.can_submit is True
    assert preview.page_index == 2
    assert preview.signature_rect == request.signature_rect
    assert preview.signer_label_prefix == "Digitally signed by"
    assert preview.layout_template == SignatureLayoutTemplate.WRAPPED_BLOCK
    assert preview.timezone_display_mode == SignatureTimezoneDisplayMode.UTC
    assert preview.show_field_names is False
    assert preview.datetime_format == "%Y-%m-%d %H:%M"
    assert preview.text_style == _appearance().text_style
    assert preview.box_style == _appearance().box_style
    assert preview.image_stamp_path == "/tmp/stamp.png"
    assert [field.field_key.value for field in preview.fields] == [
        "distinguished_name",
        "common_name",
        "email",
        "title",
        "company",
        "signing_time",
        "reason",
        "location",
    ]
    assert preview.fields[1].text == "Common name"
    assert preview.fields[1].hint == "from certificate"
    assert preview.fields[2].text == "alice@example.com"
    assert preview.fields[3].text == "Title"
    assert preview.fields[3].visible is True
    assert preview.fields[4].text == "Company"
    assert preview.fields[5].visible is True
    assert preview.fields[7].visible is False
    assert request.certificate_alias == "signing-cert"
    assert request.signature_appearance == workflow.current_signature_appearance
    assert request.signature_rect == workflow.current_signature_rect


def test_workflow_converts_view_selection_into_pdf_rectangle(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    workflow.set_placement_context(
        SignaturePlacementContext(
            page_index=1,
            page_box=PageBox(left=0.0, bottom=0.0, right=100.0, top=50.0),
            rotation=0,
        )
    )

    rect = workflow.set_signature_rect_from_view_selection(
        ViewRect(x1=10.0, y1=10.0, x2=30.0, y2=20.0),
        transform=ViewTransform(zoom=1.0, pan_x=0.0, pan_y=0.0),
    )

    assert rect.page_index == 1
    assert rect.left_pt == pytest.approx(10.0)
    assert rect.bottom_pt == pytest.approx(30.0)
    assert rect.width_pt == pytest.approx(20.0)
    assert rect.height_pt == pytest.approx(10.0)


def test_workflow_supports_numeric_rectangle_fine_tuning(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    workflow.set_signature_rect(
        SignatureRect(
            page_index=0,
            left_pt=12.0,
            bottom_pt=15.0,
            width_pt=180.0,
            height_pt=72.0,
        )
    )

    updated = workflow.update_signature_rect(left_pt=20.0, width_pt=200.0)

    assert updated.page_index == 0
    assert updated.left_pt == pytest.approx(20.0)
    assert updated.bottom_pt == pytest.approx(15.0)
    assert updated.width_pt == pytest.approx(200.0)
    assert updated.height_pt == pytest.approx(72.0)


def test_workflow_warns_when_geometry_is_unavailable_but_allows_submission(
    tmp_path: Path,
) -> None:
    workflow = _workflow(tmp_path)
    workflow.set_signature_appearance(_appearance())
    workflow.set_signature_rect(
        SignatureRect(
            page_index=0,
            left_pt=10.0,
            bottom_pt=10.0,
            width_pt=120.0,
            height_pt=40.0,
        )
    )

    issues = workflow.validation_issues()

    assert [issue.code for issue in issues] == ["signature_rect_geometry_unavailable"]
    assert issues[0].severity.value == "warning"
    assert workflow.can_build_request() is True
    assert workflow.preview().can_submit is True
    assert workflow.build_signing_request().signature_rect is not None


def test_workflow_flags_out_of_bounds_rectangles_when_geometry_is_known(
    tmp_path: Path,
) -> None:
    workflow = _workflow(tmp_path)
    workflow.set_placement_context(
        SignaturePlacementContext(
            page_index=0,
            page_box=PageBox(left=0.0, bottom=0.0, right=100.0, top=50.0),
            rotation=0,
        )
    )
    workflow.set_signature_appearance(_appearance())
    workflow.set_signature_rect(
        SignatureRect(
            page_index=1,
            left_pt=95.0,
            bottom_pt=10.0,
            width_pt=10.0,
            height_pt=10.0,
        )
    )

    issues = workflow.validation_issues()

    assert [issue.code for issue in issues] == ["signature_rect_page_mismatch"]
    assert all(issue.code != "signature_rect_out_of_bounds" for issue in issues)


def test_workflow_reports_missing_draft_components_as_validation_issues(
    tmp_path: Path,
) -> None:
    workflow = _workflow(tmp_path)

    issues = workflow.validation_issues()

    assert {issue.code for issue in issues} == {
        "signature_rect_missing",
        "signature_appearance_missing",
    }
    assert workflow.can_build_request() is False

    with pytest.raises(SigningDraftValidationError) as exc_info:
        workflow.build_signing_request()

    assert {issue.code for issue in exc_info.value.issues} == {
        "signature_rect_missing",
        "signature_appearance_missing",
    }


def test_workflow_can_capture_and_apply_named_profile(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    appearance = _appearance()
    placement_defaults = SignaturePlacementDefaults(
        width_pt=180.0,
        height_pt=72.0,
    )
    workflow.set_signature_appearance(appearance)
    workflow.signature_placement_defaults = placement_defaults

    captured = workflow.capture_signature_preset("Team Standard")

    assert captured == SignaturePreset(
        schema_version=1,
        name="Team Standard",
        appearance=appearance,
        placement_defaults=placement_defaults,
    )

    workflow.clear_signature_appearance()
    workflow.signature_placement_defaults = None
    workflow.apply_signature_preset(captured)

    assert workflow.current_signature_appearance == appearance
    assert workflow.signature_placement_defaults == placement_defaults


def test_workflow_captures_placement_defaults_from_current_rectangle(
    tmp_path: Path,
) -> None:
    workflow = _workflow(tmp_path)
    workflow.set_signature_appearance(_appearance())
    workflow.set_signature_rect(
        SignatureRect(
            page_index=0,
            left_pt=12.0,
            bottom_pt=18.0,
            width_pt=160.0,
            height_pt=64.0,
        )
    )

    captured = workflow.capture_signature_preset("Compact")

    assert captured.name == "Compact"
    assert captured.placement_defaults == SignaturePlacementDefaults(
        width_pt=160.0,
        height_pt=64.0,
    )
