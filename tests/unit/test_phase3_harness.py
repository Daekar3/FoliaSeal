import importlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID
from PIL import Image
from pyhanko.pdf_utils import generic
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.pdf_utils.writer import PageObject, PdfFileWriter

from foliaseal.application import SigningDraftWorkflow
from foliaseal.application.phase3_signing_backend import build_phase3_signing_executor
from foliaseal.application.qa_evidence_contract import (
    ENGINEERING_RUN,
    GATE_CANDIDATE,
    NON_GATING,
    PHASE3_EVIDENCE_CONTRACT_VERSION,
    evaluate_phase3_evidence_contract,
)
from foliaseal.application.qa_preview_stress_fixtures import (
    STRESS_VISIBLE_APPEARANCE_PROFILE,
)
from foliaseal.application.qa_signed_acceptance_assets import (
    SIGNED_ACCEPTANCE_FIXTURE_PDF,
    SIGNED_ACCEPTANCE_IDENTITY_P12,
    SIGNED_ACCEPTANCE_SCENARIO_MANIFEST,
)
from foliaseal.domain.models import (
    SignatureAppearance,
    SignatureFieldBinding,
    SignatureFieldKey,
    SignatureFieldSource,
    SignatureLayoutTemplate,
    SignatureRect,
    SignatureStampPosition,
    SignatureTextStyle,
    SignatureTimezoneDisplayMode,
    SigningRequest,
)
from foliaseal.presentation.qt.phase3_harness import (
    Phase3HarnessCapture,
    _analyze_capture_state_transitions,
    _analyze_stamp_source_image,
    _apply_appearance_overrides,
    _apply_preview_matrix_scenario,
    _apply_visible_fields_override,
    _capture_interactive_state,
    _default_harness_artifacts_dir,
    _default_harness_output_pdf_path,
    _detect_text_content_bounds_in_preview,
    _evaluate_signed_matrix_acceptance_expectations,
    _interactive_capture_label,
    _load_preview_matrix_manifest,
    _preview_edge_distances,
    _preview_matrix_diagnostic_summary,
    _preview_matrix_error_result,
    _project_content_bounds_to_preview,
    _signed_matrix_diagnostic_summary,
    _snapshot_backend_reservation,
    _snapshot_current_draft_request,
    _snapshot_output_verification,
    _snapshot_preview,
    _snapshot_signed_output_render,
    _snapshot_visible_signature_appearance,
    _stamp_edge_diagnostics,
    _text_edge_diagnostics,
    _text_font_diagnostics,
    _widget_application,
    _widget_is_visible,
    _write_stamp_debug_overlay,
    _write_text_debug_overlay,
    build_phase3_checklist_results_markdown,
)
from tests.support.phase3_builders import (
    build_signature_appearance,
    build_signature_field_binding,
    build_signature_rect,
    build_signing_request,
)


def _write_test_pdf(path: Path) -> None:
    writer = PdfFileWriter()
    empty_stream = writer.add_object(generic.StreamObject(stream_data=b""))
    writer.insert_page(PageObject(contents=empty_stream, media_box=(0, 0, 612, 792)))
    with path.open("wb") as handle:
        writer.write(handle)


def _write_test_pkcs12(
    path: Path,
    *,
    passphrase: str,
    common_name: str = "Test User",
) -> x509.Certificate:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "FoliaSeal"),
            x509.NameAttribute(NameOID.TITLE, "Board Secretary"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "QA"),
            x509.NameAttribute(NameOID.EMAIL_ADDRESS, "test@example.com"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Wytheville"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Virginia"),
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        ]
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(UTC) - timedelta(days=1))
        .not_valid_after(datetime.now(UTC) + timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )
    pfx = pkcs12.serialize_key_and_certificates(
        name=common_name.encode("utf-8"),
        key=key,
        cert=cert,
        cas=None,
        encryption_algorithm=serialization.BestAvailableEncryption(passphrase.encode("utf-8")),
    )
    path.write_bytes(pfx)
    return cert


def _write_test_stamp_image(path: Path) -> None:
    image = Image.new("RGB", (96, 48), color=(215, 235, 255))
    image.save(path, format="PNG")


def _write_transparent_test_stamp_image(path: Path) -> None:
    image = Image.new("RGBA", (100, 50), color=(0, 0, 0, 0))
    for x in range(12, 84):
        for y in range(8, 38):
            image.putpixel((x, y), (32, 48, 96, 255))
    image.save(path, format="PNG")


def _write_fully_transparent_stamp_image(path: Path) -> None:
    Image.new("RGBA", (40, 20), color=(0, 0, 0, 0)).save(path, format="PNG")


def _write_signed_test_pdf(
    tmp_path: Path,
    *,
    signature_appearance: SignatureAppearance | None = None,
    signature_rect: SignatureRect | None = None,
) -> Path:
    input_pdf = tmp_path / "input.pdf"
    output_pdf = tmp_path / "output.pdf"
    cert_path = tmp_path / "cert.p12"
    stamp_path = tmp_path / "stamp.png"
    _write_test_pdf(input_pdf)
    _write_test_pkcs12(cert_path, passphrase="secret")
    _write_test_stamp_image(stamp_path)
    request = build_signing_request(
        tmp_path,
        input_name="input.pdf",
        output_name="output.pdf",
        certificate_name="cert.p12",
        passphrase="secret",
        timestamp_required=False,
        signature_rect=signature_rect
        or build_signature_rect(page_index=0, width_pt=540.0, height_pt=120.0),
        signature_appearance=signature_appearance
        or build_signature_appearance(
            image_stamp_path=str(stamp_path),
            signer_label_prefix="Digitally signed by",
            show_field_names=False,
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=SignatureStampPosition.TOP,
            distinguished_name=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
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
            text_style=SignatureTextStyle(
                font_family="Serif",
                font_size_pt=8.0,
                bold=False,
                italic=False,
                text_color_hex="#000000",
            ),
        ),
    )
    build_phase3_signing_executor().execute(request)
    return output_pdf


def _capture_metadata_defaults(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "summary_json_path": "artifacts/phase3_harness_capture.json",
        "summary_json_written": True,
        "checklist_results_path": "artifacts/phase3_fr3b_acceptance_results.md",
        "checklist_results_written": True,
        "evidence_contract_version": PHASE3_EVIDENCE_CONTRACT_VERSION,
        "acceptance_tier": GATE_CANDIDATE,
        "gate_verdict": GATE_CANDIDATE,
        "evidence_validation_passed": True,
        "evidence_validation_errors": (),
        "evidence_validation_warnings": (),
    }
    payload.update(overrides)
    return payload


def test_phase3_checklist_results_markdown_auto_checks_supported_items(
    tmp_path: Path,
) -> None:
    template = tmp_path / "phase3_template.md"
    template.write_text(
        "\n".join(
            [
                (
                    "- [ ] Confirm the signature properties flow is reachable from the "
                    "main signing UI."
                ),
                (
                    "- [ ] Confirm the selected PDF can be used without unexpected "
                    "dependency or backend errors."
                ),
                "- [ ] The user can draw a signature rectangle on the preview.",
                "- [ ] The sign action is available from the properties flow.",
                "- [ ] Reused settings preserve layout and style choices.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    capture = Phase3HarnessCapture(
        pdf_path="/tmp/sample.pdf",
        **_capture_metadata_defaults(),
        first_render_ms=52.4,
        selection_count=1,
        sign_request_count=1,
        last_signature_page_index=0,
        last_signature_page_number=1,
        last_signature_has_visible_appearance=True,
        last_signature_output_path="/tmp/sample-signed.pdf",
        last_signing_result_message="Signing completed successfully.",
        last_signing_result_success=True,
        preview_snapshot={
            "title": "Alice Example",
            "signer_label_prefix": "Digitally signed by",
            "layout_template": "single_line",
            "stamp_position": "top",
            "timezone_display_mode": "utc",
            "show_field_names": False,
            "datetime_format": "%Y-%m-%d %H:%M:%S %Z",
            "image_stamp_path": None,
            "signature_rect": {
                "page_index": 0,
                "page_number": 1,
                "left_pt": 10.0,
                "bottom_pt": 20.0,
                "width_pt": 30.0,
                "height_pt": 40.0,
            },
            "text_style": {
                "font_family": "Sans Serif",
                "font_size_pt": 10.0,
                "bold": False,
                "italic": False,
                "text_color_hex": "#000000",
            },
            "box_style": {
                "show_border": True,
                "border_color_hex": "#000000",
                "border_width_pt": 1.0,
                "background_color_hex": "#FFFFFF",
            },
            "fields": [
                {
                    "field_key": "common_name",
                    "label": "Common name",
                    "text": "Alice Example",
                    "visible": True,
                    "source": "derived",
                    "hint": "from certificate",
                }
            ],
            "issues": [],
            "can_submit": True,
        },
        sign_request_snapshot={
            "input_pdf_path": "/tmp/sample.pdf",
            "output_pdf_path": "/tmp/sample-signed.pdf",
            "certificate_path": "/tmp/cert.p12",
            "certificate_alias": None,
            "timestamp_required": False,
            "tsa_url": "https://tsa.example.invalid",
            "signature_rect": {
                "page_index": 0,
                "page_number": 1,
                "left_pt": 10.0,
                "bottom_pt": 20.0,
                "width_pt": 30.0,
                "height_pt": 40.0,
            },
            "signature_appearance": {
                "signer_label_prefix": "Digitally signed by",
                "layout_template": "single_line",
                "stamp_position": "top",
                "timezone_display_mode": "utc",
                "show_field_names": False,
                "datetime_format": "%Y-%m-%d %H:%M:%S %Z",
                "field_order": [
                    "distinguished_name",
                    "common_name",
                    "email",
                    "title",
                    "company",
                    "signing_time",
                    "reason",
                    "location",
                ],
                "text_style": {
                    "font_family": "Sans Serif",
                    "font_size_pt": 10.0,
                    "bold": False,
                    "italic": False,
                    "text_color_hex": "#000000",
                },
                "box_style": {
                    "show_border": True,
                    "border_color_hex": "#000000",
                    "border_width_pt": 1.0,
                    "background_color_hex": "#FFFFFF",
                },
                "image_stamp_path": None,
                "fields": [],
            },
        },
        backend_reservation_snapshot={
            "layout_template": "single_line",
            "stamp_position": "top",
            "signature_rect": {
                "page_index": 0,
                "page_number": 1,
                "left_pt": 10.0,
                "bottom_pt": 20.0,
                "width_pt": 30.0,
                "height_pt": 40.0,
            },
            "stamp_text": "Digitally signed by\nAlice Example",
            "stamp_text_length": 33,
            "stamp_text_line_count": 2,
            "stamp_background_present": False,
            "text_style": {
                "font_family": "Sans Serif",
                "font_size_pt": 10.0,
                "bold": False,
                "italic": False,
                "text_color_hex": "#000000",
            },
            "box_style": {
                "show_border": True,
                "border_color_hex": "#000000",
                "border_width_pt": 1.0,
                "background_color_hex": "#FFFFFF",
            },
            "background_layout": {
                "x_align": "align_mid",
                "y_align": "align_mid",
                "inner_content_scaling": "stretch_to_fit",
                "margins": {
                    "left": 4,
                    "right": 4,
                    "top": 4,
                    "bottom": 4,
                },
            },
            "content_layout": {
                "x_align": "align_mid",
                "y_align": "align_min",
                "inner_content_scaling": "no_scaling",
                "margins": {
                    "left": 4,
                    "right": 4,
                    "top": 4,
                    "bottom": 14,
                },
            },
        },
        backend_reservation_error=None,
        output_file_exists=True,
        output_file_size_bytes=12345,
        output_signature_count=1,
        output_signature_snapshot={
            "field_name": "Signature1",
            "name": "Adam Smith <Secretary.LHI@Outlook.com>",
            "location": "Wytheville, Virginia, US",
            "contact_info": "Secretary.LHI@Outlook.com",
            "byte_range": [0, 123, 456, 789],
            "subfilter": "/adbe.pkcs7.detached",
            "md_algorithm": "sha256",
            "coverage": "known",
            "docmdp_level": None,
        },
        output_visible_appearance_snapshot={
            "field_name": "Signature1",
            "annotation_rect": [24.0, 18.0, 644.0, 198.0],
            "appearance_bbox": [0.0, 180.0, 620.0, 0.0],
            "appearance_stream_length": 650,
            "appearance_text_fragments": [
                "Digitally signed by",
                "Alice Example",
            ],
            "appearance_text_snippet": "Digitally signed by ...",
            "appearance_text_operator_count": 3,
            "appearance_xobjects": [
                {
                    "name": "/Img4f98d153-5c97-4ad4-89f4-d08f26ccc303",
                    "subtype": "/Image",
                    "width": 96,
                    "height": 48,
                    "bbox": None,
                }
            ],
            "appearance_image_xobject_count": 1,
            "appearance_has_visible_text": True,
        },
        preview_available=True,
        preview_text="Digitally signed by\nAlice Example",
        validation_text="Ready to sign.",
        interaction_counts={"selection_success": 1},
        errors=(),
    )

    markdown = build_phase3_checklist_results_markdown(
        capture,
        checklist_template_path=str(template),
    )

    assert "Phase 3 FR-3B Acceptance Results" in markdown
    assert "- Acceptance tier: `gate_candidate`" in markdown
    assert "- Automated gate verdict: `gate_candidate`" in markdown
    assert "- Evidence contract version: `phase3_evidence_v1`" in markdown
    assert "- Evidence validation passed: yes" in markdown
    assert "- Request snapshot origin: submitted request" in markdown
    assert "- Last signature page number: 1" in markdown
    assert "- Output embedded signature count: 1" in markdown
    assert "- Output signature field name: Signature1" in markdown
    assert "- Output signature name: Adam Smith <Secretary.LHI@Outlook.com>" in markdown
    assert "- Output signature location: Wytheville, Virginia, US" in markdown
    assert "- Output signature contact info: Secretary.LHI@Outlook.com" in markdown
    assert "- Output signature byte range: [0, 123, 456, 789]" in markdown
    assert "- Output signature subfilter: /adbe.pkcs7.detached" in markdown
    assert "- Output signature md algorithm: sha256" in markdown
    assert "- Output visible appearance field name: Signature1" in markdown
    assert "- Output visible appearance annotation rect: [24.0, 18.0, 644.0, 198.0]" in markdown
    assert "- Output visible appearance bbox: [0.0, 180.0, 620.0, 0.0]" in markdown
    assert "- Output visible appearance stream length: 650 bytes" in markdown
    assert "- Output visible appearance has visible text: yes" in markdown
    assert (
        "- Output visible appearance text fragments: "
        "['Digitally signed by', 'Alice Example']"
        in markdown
    )
    assert (
        "- Output visible appearance image XObjects: "
        "[/Img4f98d153-5c97-4ad4-89f4-d08f26ccc303:/Image 96x48]"
        in markdown
    )
    assert "- Output visible appearance error: none" in markdown
    assert "- Backend reservation layout template: single_line" in markdown
    assert "- Backend reservation stamp position: top" in markdown
    assert "- Backend reservation stamp text length: 33" in markdown
    assert "- Backend reservation stamp background: no" in markdown
    assert "- Backend reservation background scaling: stretch_to_fit" in markdown
    assert "- Backend reservation content scaling: no_scaling" in markdown
    assert "- Backend reservation content bottom margin: 14" in markdown
    assert "- Last request layout template: single_line" in markdown
    assert "- Last request stamp position: top" in markdown
    assert "- Last request show field names: no" in markdown
    assert "- Preview layout template: single_line" in markdown
    assert "- Preview stamp position: top" in markdown
    assert "- Preview show field names: no" in markdown
    assert (
        "- [x] Confirm the signature properties flow is reachable from the main signing UI."
        in markdown
    )
    assert (
        "- [x] Confirm the selected PDF can be used without unexpected dependency or backend "
        "errors." in markdown
    )
    assert "- [x] The user can draw a signature rectangle on the preview." in markdown
    assert "- [x] The sign action is available from the properties flow." in markdown
    assert "- [ ] Reused settings preserve layout and style choices." in markdown


def test_phase3_checklist_results_markdown_leaves_manual_items_unchecked(
    tmp_path: Path,
) -> None:
    template = tmp_path / "phase3_template.md"
    template.write_text(
        "- [ ] The placed rectangle can be resized or repositioned in the workflow.\n",
        encoding="utf-8",
    )
    capture = Phase3HarnessCapture(
        pdf_path="/tmp/sample.pdf",
        **_capture_metadata_defaults(
            acceptance_tier=ENGINEERING_RUN,
            gate_verdict=NON_GATING,
            evidence_validation_warnings=("debug-only run",),
        ),
        first_render_ms=None,
        selection_count=0,
        sign_request_count=0,
        last_signature_page_index=None,
        last_signature_page_number=None,
        last_signature_has_visible_appearance=False,
        last_signature_output_path=None,
        last_signing_result_message=None,
        last_signing_result_success=None,
        preview_snapshot={
            "title": "Signature draft",
            "signer_label_prefix": None,
            "layout_template": None,
            "timezone_display_mode": None,
            "show_field_names": False,
            "datetime_format": None,
            "image_stamp_path": None,
            "signature_rect": None,
            "text_style": None,
            "box_style": None,
            "fields": [],
            "issues": [],
            "can_submit": False,
        },
        sign_request_snapshot=None,
        backend_reservation_snapshot=None,
        backend_reservation_error=None,
        output_file_exists=False,
        output_file_size_bytes=None,
        output_signature_count=None,
        output_signature_snapshot=None,
        output_visible_appearance_snapshot=None,
        preview_available=False,
        preview_text="",
        validation_text="",
        interaction_counts={},
        errors=("render failed",),
    )

    markdown = build_phase3_checklist_results_markdown(
        capture,
        checklist_template_path=str(template),
    )

    assert "- [ ] The placed rectangle can be resized or repositioned in the workflow." in markdown
    assert "- Automated gate verdict: `non_gating`" in markdown
    assert "- Evidence validation warnings: ['debug-only run']" in markdown


def test_evidence_contract_rejects_success_without_output_file() -> None:
    evaluation = evaluate_phase3_evidence_contract(
        {
            "summary_json_written": True,
            "checklist_results_written": True,
            "sign_request_count": 1,
            "last_signing_result_success": True,
            "last_signature_has_visible_appearance": True,
            "output_file_exists": False,
            "output_signature_count": None,
            "output_visible_appearance_snapshot": None,
            "preview_snapshot": {
                "can_submit": True,
                "layout_template": "single_line",
                "stamp_position": "top",
                "show_field_names": False,
                "datetime_format": "%Y-%m-%d",
                "signer_label_prefix": "",
                "timezone_display_mode": "utc",
                "image_stamp_path": None,
            },
            "sign_request_snapshot": {
                "signature_appearance": {
                    "layout_template": "single_line",
                    "stamp_position": "top",
                    "show_field_names": False,
                    "datetime_format": "%Y-%m-%d",
                    "signer_label_prefix": "",
                    "timezone_display_mode": "utc",
                    "image_stamp_path": None,
                }
            },
            "backend_reservation_snapshot": {"layout_template": "single_line"},
            "backend_reservation_error": None,
            "validation_text": "Ready to sign.",
            "preview_available": True,
        }
    )

    assert evaluation.passed is False
    assert evaluation.acceptance_tier == ENGINEERING_RUN
    assert evaluation.gate_verdict == NON_GATING
    assert any("output_file_exists is false" in item for item in evaluation.errors)
    assert any("output_signature_count is missing" in item for item in evaluation.errors)
    assert any(
        "output_visible_appearance_snapshot is missing" in item
        for item in evaluation.errors
    )


def test_evidence_contract_accepts_consistent_success_state() -> None:
    evaluation = evaluate_phase3_evidence_contract(
        {
            "summary_json_path": "artifacts/phase3_harness_capture.json",
            "summary_json_written": True,
            "checklist_results_written": True,
            "sign_request_count": 1,
            "last_signing_result_success": True,
            "last_signature_has_visible_appearance": True,
            "output_file_exists": True,
            "output_signature_count": 1,
            "output_verification_snapshot": {
                "cryptographic_validation_passed": True,
                "signature_count": 1,
                "error": None,
            },
            "output_visible_appearance_snapshot": {"field_name": "Signature1"},
            "signed_output_render_snapshot": {
                "page_render_path": "artifacts/final_signed_output_page.png",
                "signature_crop_path": "artifacts/final_signed_output_crop.png",
                "page_render_error": None,
                "signature_crop_error": None,
            },
            "signed_output_preview_comparison": {
                "signature_crop_path": "artifacts/final_signed_output_crop.png",
                "comparison_path": "artifacts/final_signed_output_compare.png",
                "preview_vs_signed_output_passed": True,
                "preview_vs_signed_output_error": None,
            },
            "preview_snapshot": {
                "can_submit": True,
                "layout_template": "single_line",
                "stamp_position": "top",
                "show_field_names": False,
                "datetime_format": "%Y-%m-%d",
                "signer_label_prefix": "",
                "timezone_display_mode": "utc",
                "image_stamp_path": None,
                "render_capture": {
                    "preview_image_path": "artifacts/phase3_harness_capture_artifacts/current.png",
                    "preview_image_error": None,
                    "text_debug_image_path": (
                        "artifacts/phase3_harness_capture_artifacts/current_text_debug.png"
                    ),
                    "stamp_debug_image_path": (
                        "artifacts/phase3_harness_capture_artifacts/current_stamp_debug.png"
                    ),
                    "text_rendered_content_bounds_px": {"x": 1, "y": 2, "width": 3, "height": 4},
                    "text_content_clipped_in_preview": False,
                    "stamp_content_within_warning_distance": False,
                },
            },
            "sign_request_snapshot": {
                "signature_appearance": {
                    "layout_template": "single_line",
                    "stamp_position": "top",
                    "show_field_names": False,
                    "datetime_format": "%Y-%m-%d",
                    "signer_label_prefix": "",
                    "timezone_display_mode": "utc",
                    "image_stamp_path": None,
                }
            },
            "backend_reservation_snapshot": {"layout_template": "single_line"},
            "backend_reservation_error": None,
            "validation_text": "Ready to sign.",
            "preview_available": True,
            "captured_states": [
                {
                    "preview_snapshot": {
                        "render_capture": {
                            "preview_image_path": (
                                "artifacts/phase3_harness_capture_artifacts/manual.png"
                            ),
                            "preview_image_error": None,
                            "text_debug_image_path": (
                                "artifacts/phase3_harness_capture_artifacts/manual_text_debug.png"
                            ),
                            "stamp_debug_image_path": (
                                "artifacts/phase3_harness_capture_artifacts/manual_stamp_debug.png"
                            ),
                            "text_rendered_content_bounds_px": {
                                "x": 1,
                                "y": 2,
                                "width": 3,
                                "height": 4,
                            },
                            "text_content_clipped_in_preview": False,
                            "stamp_content_within_warning_distance": False,
                        }
                    }
                }
            ],
        }
    )

    assert evaluation.passed is True
    assert evaluation.acceptance_tier == GATE_CANDIDATE
    assert evaluation.gate_verdict == GATE_CANDIDATE
    assert evaluation.errors == ()


def test_evidence_contract_rejects_saved_capture_without_preview_artifacts() -> None:
    evaluation = evaluate_phase3_evidence_contract(
        {
            "summary_json_path": "artifacts/phase3_harness_capture.json",
            "summary_json_written": True,
            "checklist_results_written": True,
            "sign_request_count": 0,
            "last_signing_result_success": False,
            "last_signature_has_visible_appearance": False,
            "output_file_exists": False,
            "output_signature_count": None,
            "output_visible_appearance_snapshot": None,
            "preview_snapshot": {
                "can_submit": False,
                "layout_template": "single_line",
                "stamp_position": "top",
                "show_field_names": False,
                "datetime_format": "%Y-%m-%d",
                "signer_label_prefix": "",
                "timezone_display_mode": "utc",
                "image_stamp_path": None,
                "render_capture": {
                    "preview_image_path": None,
                    "preview_image_error": None,
                },
            },
            "sign_request_snapshot": None,
            "backend_reservation_snapshot": None,
            "backend_reservation_error": None,
            "validation_text": "Will fail to sign.",
            "preview_available": True,
            "captured_states": [
                {
                    "preview_snapshot": {
                        "render_capture": {
                            "preview_image_path": None,
                            "preview_image_error": None,
                        }
                    }
                }
            ],
        }
    )

    assert evaluation.passed is False
    assert any(
        "current preview snapshot is missing preview_image_path" in item
        for item in evaluation.errors
    )
    assert any(
        "captured_states[1] is missing preview_image_path" in item
        for item in evaluation.errors
    )


def test_evidence_contract_rejects_signable_render_clipping() -> None:
    evaluation = evaluate_phase3_evidence_contract(
        {
            "summary_json_path": "artifacts/phase3_harness_capture.json",
            "summary_json_written": True,
            "checklist_results_written": True,
            "sign_request_count": 0,
            "last_signing_result_success": False,
            "last_signature_has_visible_appearance": False,
            "output_file_exists": False,
            "output_signature_count": None,
            "output_visible_appearance_snapshot": None,
            "preview_snapshot": {
                "can_submit": True,
                "layout_template": "multi_line",
                "stamp_position": "bottom",
                "show_field_names": False,
                "datetime_format": "%Y-%m-%d",
                "signer_label_prefix": "",
                "timezone_display_mode": "utc",
                "image_stamp_path": None,
                "render_capture": {
                    "preview_image_path": "artifacts/phase3_harness_capture_artifacts/current.png",
                    "preview_image_error": None,
                    "text_debug_image_path": "artifacts/current_text_debug.png",
                    "stamp_debug_image_path": "artifacts/current_stamp_debug.png",
                    "text_rendered_content_bounds_px": {"x": 1, "y": 2, "width": 3, "height": 4},
                    "text_content_clipped_in_preview": True,
                    "text_content_overlaps_stamp_band": False,
                    "text_content_overlaps_stamp_content": False,
                    "stamp_content_touches_band_edge": False,
                    "stamp_content_within_warning_distance": False,
                },
            },
            "sign_request_snapshot": None,
            "backend_reservation_snapshot": None,
            "backend_reservation_error": None,
            "validation_text": "Ready to sign.",
            "preview_available": True,
        }
    )

    assert evaluation.passed is False
    assert any(
        "user-visible fit failure" in item
        for item in evaluation.errors
    )


def test_evidence_contract_requires_signed_output_evidence_for_success() -> None:
    evaluation = evaluate_phase3_evidence_contract(
        {
            "summary_json_path": "artifacts/phase3_harness_capture.json",
            "summary_json_written": True,
            "checklist_results_written": True,
            "sign_request_count": 1,
            "last_signing_result_success": True,
            "last_signature_has_visible_appearance": True,
            "output_file_exists": True,
            "output_signature_count": 1,
            "output_visible_appearance_snapshot": {"field_name": "Signature1"},
            "preview_snapshot": {
                "can_submit": True,
                "layout_template": "single_line",
                "stamp_position": "top",
                "show_field_names": False,
                "datetime_format": "%Y-%m-%d",
                "signer_label_prefix": "",
                "timezone_display_mode": "utc",
                "image_stamp_path": None,
                "render_capture": {
                    "preview_image_path": "artifacts/current.png",
                    "preview_image_error": None,
                    "text_debug_image_path": "artifacts/current_text_debug.png",
                    "stamp_debug_image_path": "artifacts/current_stamp_debug.png",
                    "text_rendered_content_bounds_px": {"x": 1, "y": 2, "width": 3, "height": 4},
                    "text_content_clipped_in_preview": False,
                    "text_content_overlaps_stamp_band": False,
                    "text_content_overlaps_stamp_content": False,
                    "stamp_content_touches_band_edge": False,
                    "stamp_content_within_warning_distance": False,
                },
            },
            "sign_request_snapshot": {"signature_appearance": {"layout_template": "single_line"}},
            "backend_reservation_snapshot": {"layout_template": "single_line"},
            "backend_reservation_error": None,
            "validation_text": "Ready to sign.",
            "preview_available": True,
        }
    )

    assert evaluation.passed is False
    assert any("output_verification_snapshot is missing" in item for item in evaluation.errors)
    assert any(
        "signed_output_preview_comparison is missing" in item for item in evaluation.errors
    )


def test_phase3_harness_capture_to_json_handles_nested_non_json_objects(
    tmp_path: Path,
) -> None:
    opaque_path = tmp_path / "opaque.bin"
    opaque_path.write_bytes(b"opaque")

    with opaque_path.open("rb") as opaque_handle:
        capture = Phase3HarnessCapture(
            pdf_path="/tmp/sample.pdf",
            **_capture_metadata_defaults(
                acceptance_tier=ENGINEERING_RUN,
                gate_verdict=NON_GATING,
            ),
            first_render_ms=None,
            selection_count=0,
            sign_request_count=0,
            last_signature_page_index=None,
            last_signature_page_number=None,
            last_signature_has_visible_appearance=False,
            last_signature_output_path=None,
            last_signing_result_message=None,
            last_signing_result_success=None,
            preview_snapshot={"opaque": opaque_handle},
            sign_request_snapshot=None,
            backend_reservation_snapshot=None,
            backend_reservation_error=None,
            output_file_exists=False,
            output_file_size_bytes=None,
            output_signature_count=None,
            output_signature_snapshot=None,
            output_visible_appearance_snapshot=None,
            preview_available=False,
            preview_text="",
            validation_text="",
            interaction_counts={},
            errors=(),
        )

        payload = json.loads(capture.to_json())

    assert payload["preview_snapshot"]["opaque"].startswith("<_io.BufferedReader")


def test_phase3_harness_capture_to_json_serializes_captured_states() -> None:
    capture = Phase3HarnessCapture(
        pdf_path="/tmp/sample.pdf",
        **_capture_metadata_defaults(),
        first_render_ms=12.5,
        selection_count=1,
        sign_request_count=0,
        last_signature_page_index=None,
        last_signature_page_number=None,
        last_signature_has_visible_appearance=False,
        last_signature_output_path=None,
        last_signing_result_message=None,
        last_signing_result_success=None,
        preview_snapshot={"title": "Current"},
        sign_request_snapshot=None,
        backend_reservation_snapshot=None,
        backend_reservation_error=None,
        output_file_exists=False,
        output_file_size_bytes=None,
        output_signature_count=None,
        output_signature_snapshot=None,
        output_visible_appearance_snapshot=None,
        preview_available=True,
        preview_text="Current",
        validation_text="Ready to sign.",
        interaction_counts={},
        errors=(),
        captured_states=(
            {
                "capture_index": 1,
                "capture_kind": "manual",
                "capture_label": "manual_01_single_line_top",
                "preview_snapshot": {"title": "Manual"},
                "preview_text": "Manual",
                "validation_text": "Ready to sign.",
                "sign_request_snapshot": None,
                "backend_reservation_snapshot": None,
                "backend_reservation_error": None,
            },
            {
                "capture_index": 2,
                "capture_kind": "final",
                "capture_label": "final_02_single_line_top",
                "preview_snapshot": {"title": "Final"},
                "preview_text": "Final",
                "validation_text": "Ready to sign.",
                "sign_request_snapshot": None,
                "backend_reservation_snapshot": None,
                "backend_reservation_error": None,
            },
        ),
    )

    payload = json.loads(capture.to_json())

    assert len(payload["captured_states"]) == 2
    assert payload["captured_states"][0]["capture_kind"] == "manual"
    assert payload["captured_states"][1]["capture_kind"] == "final"


def test_snapshot_output_verification_reports_cryptographic_details(tmp_path: Path) -> None:
    output_pdf = _write_signed_test_pdf(tmp_path)

    snapshot = _snapshot_output_verification(output_pdf)

    assert snapshot is not None
    assert snapshot["cryptographic_validation_passed"] is True
    assert snapshot["signature_count"] == 1
    assert snapshot["byte_range_present"] is True
    assert snapshot["subfilter"] is not None
    assert snapshot["signer_subject"]


def test_snapshot_signed_output_render_captures_output_parity(monkeypatch, tmp_path: Path) -> None:
    preview_path = tmp_path / "preview.png"
    Image.new("RGBA", (120, 48), color=(255, 255, 255, 255)).save(preview_path)
    output_pdf = tmp_path / "signed.pdf"
    output_pdf.write_bytes(b"%PDF-1.7\n")

    class _FakeBackend:
        def diagnostics(self):
            return type("_Diag", (), {"available": True, "message": "ok"})()

        def render_page(self, request):
            image = Image.new("RGBA", (300, 400), color=(255, 255, 255, 255))
            return type(
                "_Render",
                (),
                {
                    "width_px": image.width,
                    "height_px": image.height,
                    "rgba_bytes": image.tobytes(),
                },
            )()

        def get_page_geometry(self, document_path: str, page_index: int):
            return type(
                "_Geom",
                (),
                {"crop_box": (0.0, 0.0, 300.0, 400.0), "rotation": 0},
            )()

    monkeypatch.setattr(
        "foliaseal.presentation.qt.phase3_harness.QtPdfRenderBackend",
        _FakeBackend,
    )
    monkeypatch.setattr(
        "foliaseal.presentation.qt.phase3_harness._detect_text_content_bounds_in_preview",
        lambda **kwargs: ({"x": 14, "y": 12, "width": 64, "height": 18}, None),
    )
    monkeypatch.setattr(
        "foliaseal.presentation.qt.phase3_harness._normalized_image_crop_change_ratio",
        lambda **kwargs: 0.1,
    )

    snapshot = _snapshot_signed_output_render(
        output_pdf_path=str(output_pdf),
        page_index=0,
        preview_snapshot={
            "image_stamp_path": "/tmp/stamp.png",
            "signature_rect": {
                "left_pt": 10.0,
                "bottom_pt": 20.0,
                "width_pt": 120.0,
                "height_pt": 48.0,
            },
            "text_style": {"text_color_hex": "#000000"},
            "render_capture": {
                "preview_image_path": str(preview_path),
                "card_bounds_px": {"x": 0, "y": 0, "width": 120, "height": 48},
                "text_rendered_content_bounds_px": {"x": 14, "y": 12, "width": 64, "height": 18},
            },
            "box_style": {
                "show_border": True,
                "border_color_hex": "#000000",
                "border_width_pt": 1.0,
                "background_color_hex": "#FFFFFF",
            },
            "layout_template": "single_line",
            "stamp_position": "top",
        },
        preview_text="Morgan Ellery | Northwind Ledger Holdings | 2026-04-11 09:00",
        output_visible_appearance_snapshot={
            "annotation_rect": [10.0, 20.0, 130.0, 68.0],
            "image_xobject_count": 1,
            "appearance_has_visible_text": True,
            "text_fragments": [
                "Morgan Ellery",
                "Northwind Ledger Holdings",
                "2026-04-11 09:00",
            ],
        },
        artifacts_dir=str(tmp_path),
        artifact_basename="signed_case",
    )

    assert snapshot is not None
    assert snapshot["signature_crop_path"] is not None
    assert snapshot["comparison_path"] is not None
    assert snapshot["annotation_rect_matches_request"] is True
    assert snapshot["output_image_presence_matches_preview"] is None
    assert snapshot["output_text_bounds_match_preview"] is True


def test_snapshot_signed_output_render_composites_transparent_page_over_white(
    monkeypatch, tmp_path: Path
) -> None:
    preview_path = tmp_path / "preview.png"
    Image.new("RGBA", (120, 48), color=(255, 255, 255, 255)).save(preview_path)
    output_pdf = tmp_path / "signed.pdf"
    output_pdf.write_bytes(b"%PDF-1.7\n")

    class _FakeBackend:
        def diagnostics(self):
            return type("_Diag", (), {"available": True, "message": "ok"})()

        def render_page(self, request):
            image = Image.new("RGBA", (300, 400), color=(0, 0, 0, 0))
            return type(
                "_Render",
                (),
                {
                    "width_px": image.width,
                    "height_px": image.height,
                    "rgba_bytes": image.tobytes(),
                },
            )()

        def get_page_geometry(self, document_path: str, page_index: int):
            return type(
                "_Geom",
                (),
                {"crop_box": (0.0, 0.0, 300.0, 400.0), "rotation": 0},
            )()

    monkeypatch.setattr(
        "foliaseal.presentation.qt.phase3_harness.QtPdfRenderBackend",
        _FakeBackend,
    )
    monkeypatch.setattr(
        "foliaseal.presentation.qt.phase3_harness._detect_text_content_bounds_in_preview",
        lambda **kwargs: ({"x": 14, "y": 12, "width": 64, "height": 18}, None),
    )
    monkeypatch.setattr(
        "foliaseal.presentation.qt.phase3_harness._normalized_image_crop_change_ratio",
        lambda **kwargs: 0.0,
    )

    snapshot = _snapshot_signed_output_render(
        output_pdf_path=str(output_pdf),
        page_index=0,
        preview_snapshot={
            "image_stamp_path": None,
            "signature_rect": {
                "left_pt": 10.0,
                "bottom_pt": 20.0,
                "width_pt": 120.0,
                "height_pt": 48.0,
            },
            "text_style": {"text_color_hex": "#000000"},
            "render_capture": {
                "preview_image_path": str(preview_path),
                "card_bounds_px": {"x": 0, "y": 0, "width": 120, "height": 48},
                "text_rendered_content_bounds_px": {"x": 14, "y": 12, "width": 64, "height": 18},
            },
            "box_style": {
                "show_border": True,
                "border_color_hex": "#000000",
                "border_width_pt": 1.0,
                "background_color_hex": "#FFFFFF",
            },
            "layout_template": "single_line",
            "stamp_position": "top",
        },
        preview_text="Morgan Ellery | Northwind Ledger Holdings | 2026-04-11 09:00",
        output_visible_appearance_snapshot={
            "annotation_rect": [10.0, 20.0, 130.0, 68.0],
            "text_fragments": ["Morgan Ellery", "Northwind Ledger Holdings", "2026-04-11 09:00"],
        },
        artifacts_dir=str(tmp_path),
        artifact_basename="signed_white_bg",
    )

    assert snapshot is not None
    page_image = Image.open(snapshot["page_render_path"]).convert("RGBA")
    assert page_image.getpixel((0, 0)) == (255, 255, 255, 255)


def test_signed_matrix_diagnostic_summary_counts_failures() -> None:
    summary = _signed_matrix_diagnostic_summary(
        [
            {
                "name": "expected_success_but_failed",
                "signing_result": {"success": True},
                "expected_outcome": "success",
                "output_verification_snapshot": {"cryptographic_validation_passed": False},
                "signed_output_preview_comparison": {
                    "preview_vs_signed_output_passed": False,
                    "annotation_rect_matches_request": False,
                },
            },
            {
                "name": "expected_rejection_and_rejected",
                "signing_result": {
                    "success": False,
                    "message": (
                        "Visible signature content does not fit inside the selected rectangle."
                    ),
                },
                "expected_outcome": "validation_rejection",
                "expected_failure_message_contains": "does not fit inside the selected rectangle",
                "output_verification_snapshot": {"cryptographic_validation_passed": True},
                "signed_output_preview_comparison": {
                    "preview_vs_signed_output_passed": True,
                    "annotation_rect_matches_request": True,
                },
            },
            {
                "name": "expected_success_and_succeeded",
                "signing_result": {"success": True},
                "expected_outcome": "success",
                "output_verification_snapshot": {"cryptographic_validation_passed": True},
                "signed_output_preview_comparison": {
                    "preview_vs_signed_output_passed": True,
                    "annotation_rect_matches_request": True,
                },
            },
        ]
    )

    assert summary["successful_signing_run_count"] == 2
    assert summary["cryptographic_validation_failure_count"] == 1
    assert summary["preview_output_comparison_failure_count"] == 1
    assert summary["annotation_rect_mismatch_count"] == 1
    assert summary["expected_success_scenario_count"] == 2
    assert summary["expected_intentional_rejection_count"] == 1
    assert summary["matched_expected_success_count"] == 2
    assert summary["matched_expected_intentional_rejection_count"] == 1
    assert summary["expected_outcome_mismatch_count"] == 0
    assert summary["acceptance_expectation_errors"] == []


def test_evaluate_signed_matrix_acceptance_expectations_flags_contract_failures() -> None:
    passed, errors = _evaluate_signed_matrix_acceptance_expectations(
        summary={
            "scenario_count": 10,
            "successful_signing_run_count": 6,
            "cryptographic_validation_failure_count": 1,
            "preview_output_comparison_failure_count": 0,
            "annotation_rect_mismatch_count": 0,
            "matched_expected_intentional_rejection_count": 3,
            "expected_outcome_mismatch_count": 1,
        },
        manifest_expectations={
            "scenario_count": 10,
            "minimum_successful_signing_run_count": 7,
            "expected_intentional_rejection_count": 3,
            "require_zero_cryptographic_validation_failures": True,
            "require_zero_preview_output_comparison_failures": True,
            "require_zero_annotation_rect_mismatches": True,
        },
    )

    assert passed is False
    assert any("at least 7 successful signings" in item for item in errors)
    assert any("zero cryptographic validation failures" in item for item in errors)
    assert any("zero per-scenario expectation mismatches" in item for item in errors)


def test_default_harness_artifacts_dir_prefers_explicit_override() -> None:
    assert (
        _default_harness_artifacts_dir(
            summary_json_path="artifacts/phase3_harness_capture.json",
            artifacts_dir="artifacts/manual_override",
        )
        == "artifacts/manual_override"
    )


def test_default_harness_artifacts_dir_derives_from_summary_json_path() -> None:
    assert (
        _default_harness_artifacts_dir(
            summary_json_path="artifacts/phase3_harness_capture.json",
            artifacts_dir=None,
        )
        == "artifacts/phase3_harness_capture_artifacts"
    )


def test_default_harness_output_pdf_path_uses_artifacts_dir_and_numbering() -> None:
    output_path = _default_harness_output_pdf_path(
        pdf_path="/tmp/input.pdf",
        artifacts_dir="artifacts/phase3_harness_capture_artifacts",
        sign_attempt_index=3,
    )

    assert (
        output_path
        == "artifacts/phase3_harness_capture_artifacts/input_harness_signed_003.pdf"
    )


def test_default_harness_output_pdf_path_falls_back_to_source_directory() -> None:
    output_path = _default_harness_output_pdf_path(
        pdf_path="/tmp/input.pdf",
        artifacts_dir=None,
        sign_attempt_index=2,
    )

    assert output_path == "/tmp/input-signed.pdf"


def test_interactive_capture_label_uses_layout_and_stamp_names() -> None:
    preview = type(
        "_Preview",
        (),
        {
            "layout_template": SignatureLayoutTemplate.SINGLE_LINE,
            "stamp_position": SignatureStampPosition.BOTTOM,
        },
    )()

    label = _interactive_capture_label(
        preview=preview,
        capture_index=3,
        capture_kind="manual",
    )

    assert label == "manual_03_single_line_bottom"


def test_capture_interactive_state_collects_preview_and_backend_snapshots(monkeypatch) -> None:
    preview = type(
        "_Preview",
        (),
        {
            "title": "Inkslapped by",
            "signer_label_prefix": "Inkslapped by",
            "layout_template": SignatureLayoutTemplate.SINGLE_LINE,
            "stamp_position": SignatureStampPosition.TOP,
            "timezone_display_mode": SignatureTimezoneDisplayMode.LOCAL,
            "show_field_names": False,
            "datetime_format": "%Y-%m-%d %H:%M",
            "image_stamp_path": None,
            "signature_rect": build_signature_rect(page_index=0, width_pt=220.0, height_pt=30.0),
            "text_style": None,
            "box_style": None,
            "fields": (),
            "issues": (),
            "can_submit": True,
        },
    )()

    class _FakePanel:
        def refresh_preview(self):
            return preview

        def preview_text(self) -> str:
            return "Preview text"

        def validation_text(self) -> str:
            return "Ready to sign."

    shell = type("_Shell", (), {"properties_panel": _FakePanel()})()

    monkeypatch.setattr(
        "foliaseal.presentation.qt.phase3_harness._capture_preview_render",
        lambda **_kwargs: {"preview_image_path": "artifacts/preview.png"},
    )
    monkeypatch.setattr(
        "foliaseal.presentation.qt.phase3_harness._snapshot_backend_reservation",
        lambda request: {"layout_template": request.signature_appearance.layout_template.value},
    )
    monkeypatch.setattr(
        "foliaseal.presentation.qt.phase3_harness._backend_reservation_error",
        lambda _request: None,
    )

    request = build_signing_request(
        Path("/tmp"),
        signature_appearance=build_signature_appearance(
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=SignatureStampPosition.TOP,
        ),
    )
    state = _capture_interactive_state(
        shell=shell,
        request=request,
        artifacts_dir="artifacts/debug",
        artifact_basename="interactive_state_01",
        capture_index=1,
        capture_kind="manual",
    )

    assert state["capture_index"] == 1
    assert state["capture_kind"] == "manual"
    assert state["capture_label"] == "manual_01_single_line_top"
    assert state["preview_text"] == "Preview text"
    assert state["validation_text"] == "Ready to sign."
    assert state["preview_snapshot"]["render_capture"] == {
        "preview_image_path": "artifacts/preview.png"
    }
    assert state["backend_reservation_snapshot"] == {"layout_template": "single_line"}


def test_analyze_capture_state_transitions_flags_negligible_font_size_change(
    tmp_path: Path,
) -> None:
    image_a = tmp_path / "a.png"
    image_b = tmp_path / "b.png"
    base = Image.new("RGBA", (60, 20), color=(255, 255, 255, 255))
    variant = Image.new("RGBA", (60, 20), color=(255, 255, 255, 255))
    for x in range(5, 25):
        for y in range(5, 12):
            base.putpixel((x, y), (0, 0, 0, 255))
            variant.putpixel((x, y), (0, 0, 0, 255))
    variant.putpixel((26, 12), (0, 0, 0, 255))
    base.save(image_a, format="PNG")
    variant.save(image_b, format="PNG")

    diagnostics = _analyze_capture_state_transitions(
        (
            {
                "capture_label": "manual_01_multi_line_top",
                "preview_text": "Adam Smith\n2026-04-11 17:05",
                "preview_snapshot": {
                    "layout_template": "multi_line",
                    "stamp_position": "top",
                    "signature_rect": {"width_pt": 200.0, "height_pt": 40.0},
                    "text_style": {"font_family": "Serif", "font_size_pt": 8.5},
                    "render_capture": {
                        "preview_image_path": str(image_a),
                        "text_widget_bounds_px": {"x": 0, "y": 0, "width": 60, "height": 20},
                        "text_rendered_content_bounds_px": {
                            "x": 5,
                            "y": 5,
                            "width": 20,
                            "height": 7,
                        },
                        "effective_text_font_category": "serif",
                    },
                },
            },
            {
                "capture_label": "manual_02_multi_line_top",
                "preview_text": "Adam Smith\n2026-04-11 17:05",
                "preview_snapshot": {
                    "layout_template": "multi_line",
                    "stamp_position": "top",
                    "signature_rect": {"width_pt": 200.0, "height_pt": 40.0},
                    "text_style": {"font_family": "Serif", "font_size_pt": 8.0},
                    "render_capture": {
                        "preview_image_path": str(image_b),
                        "text_widget_bounds_px": {"x": 0, "y": 0, "width": 60, "height": 20},
                        "text_rendered_content_bounds_px": {
                            "x": 5,
                            "y": 5,
                            "width": 20,
                            "height": 7,
                        },
                        "effective_text_font_category": "serif",
                    },
                },
            },
        )
    )

    assert len(diagnostics) == 1
    assert diagnostics[0]["issue_code"] == "font_size_change_had_negligible_visual_effect"
    assert diagnostics[0]["previous_font_size_pt"] == 8.5
    assert diagnostics[0]["current_font_size_pt"] == 8.0
    assert diagnostics[0]["changed_pixel_ratio"] == pytest.approx(1 / 1200, rel=0.01)


def test_analyze_capture_state_transitions_ignores_signing_time_differences(
    tmp_path: Path,
) -> None:
    image_a = tmp_path / "a.png"
    image_b = tmp_path / "b.png"
    base = Image.new("RGBA", (60, 20), color=(255, 255, 255, 255))
    variant = Image.new("RGBA", (60, 20), color=(255, 255, 255, 255))
    for x in range(5, 25):
        for y in range(5, 12):
            base.putpixel((x, y), (0, 0, 0, 255))
            variant.putpixel((x, y), (0, 0, 0, 255))
    variant.putpixel((26, 12), (0, 0, 0, 255))
    base.save(image_a, format="PNG")
    variant.save(image_b, format="PNG")

    diagnostics = _analyze_capture_state_transitions(
        (
            {
                "capture_label": "manual_01_multi_line_top",
                "preview_text": "Adam Smith\n2026-04-11 17:05",
                "preview_snapshot": {
                    "layout_template": "multi_line",
                    "stamp_position": "top",
                    "signature_rect": {"width_pt": 200.0, "height_pt": 40.0},
                    "text_style": {"font_family": "Serif", "font_size_pt": 8.5},
                    "render_capture": {
                        "preview_image_path": str(image_a),
                        "text_widget_bounds_px": {"x": 0, "y": 0, "width": 60, "height": 20},
                        "text_rendered_content_bounds_px": {
                            "x": 5,
                            "y": 5,
                            "width": 20,
                            "height": 7,
                        },
                        "effective_text_font_category": "serif",
                    },
                },
            },
            {
                "capture_label": "manual_02_multi_line_top",
                "preview_text": "Adam Smith\n2026-04-11 17:06",
                "preview_snapshot": {
                    "layout_template": "multi_line",
                    "stamp_position": "top",
                    "signature_rect": {"width_pt": 200.0, "height_pt": 40.0},
                    "text_style": {"font_family": "Serif", "font_size_pt": 8.0},
                    "render_capture": {
                        "preview_image_path": str(image_b),
                        "text_widget_bounds_px": {"x": 0, "y": 0, "width": 60, "height": 20},
                        "text_rendered_content_bounds_px": {
                            "x": 5,
                            "y": 5,
                            "width": 20,
                            "height": 7,
                        },
                        "effective_text_font_category": "serif",
                    },
                },
            },
        )
    )

    assert len(diagnostics) == 1
    assert diagnostics[0]["issue_code"] == "font_size_change_had_negligible_visual_effect"


def test_capture_interactive_state_preserves_render_artifacts_when_preview_capture_succeeds(
    monkeypatch,
) -> None:
    preview = type(
        "_Preview",
        (),
        {
            "title": "Digitally signed by",
            "signer_label_prefix": "Digitally signed by",
            "layout_template": SignatureLayoutTemplate.MULTI_LINE,
            "stamp_position": SignatureStampPosition.TOP,
            "timezone_display_mode": SignatureTimezoneDisplayMode.UTC,
            "show_field_names": False,
            "datetime_format": "%Y-%m-%d %H:%M",
            "image_stamp_path": None,
            "signature_rect": build_signature_rect(page_index=0, width_pt=260.0, height_pt=46.0),
            "text_style": None,
            "box_style": None,
            "fields": (),
            "issues": (),
            "can_submit": True,
        },
    )()

    class _FakePanel:
        def refresh_preview(self):
            return preview

        def preview_text(self) -> str:
            return "Preview text"

        def validation_text(self) -> str:
            return "Ready to sign."

    shell = type("_Shell", (), {"properties_panel": _FakePanel()})()

    monkeypatch.setattr(
        "foliaseal.presentation.qt.phase3_harness._capture_preview_render",
        lambda **_kwargs: {
            "preview_image_path": "artifacts/debug/state.png",
            "text_debug_image_path": "artifacts/debug/state_text_debug.png",
            "stamp_debug_image_path": "artifacts/debug/state_stamp_debug.png",
            "text_rendered_content_bounds_px": {"x": 10, "y": 12, "width": 80, "height": 18},
            "stamp_rendered_content_bounds_px": {"x": 20, "y": 4, "width": 60, "height": 10},
        },
    )
    monkeypatch.setattr(
        "foliaseal.presentation.qt.phase3_harness._snapshot_backend_reservation",
        lambda request: {"layout_template": request.signature_appearance.layout_template.value},
    )
    monkeypatch.setattr(
        "foliaseal.presentation.qt.phase3_harness._backend_reservation_error",
        lambda _request: None,
    )

    request = build_signing_request(
        Path("/tmp"),
        signature_appearance=build_signature_appearance(
            layout_template=SignatureLayoutTemplate.MULTI_LINE,
            stamp_position=SignatureStampPosition.TOP,
        ),
    )
    state = _capture_interactive_state(
        shell=shell,
        request=request,
        artifacts_dir="artifacts/debug",
        artifact_basename="interactive_state_02",
        capture_index=2,
        capture_kind="manual",
    )

    render_capture = state["preview_snapshot"]["render_capture"]
    assert render_capture["preview_image_path"] == "artifacts/debug/state.png"
    assert render_capture["text_debug_image_path"] == "artifacts/debug/state_text_debug.png"
    assert render_capture["stamp_debug_image_path"] == "artifacts/debug/state_stamp_debug.png"
    assert render_capture["text_rendered_content_bounds_px"] == {
        "x": 10,
        "y": 12,
        "width": 80,
        "height": 18,
    }


def test_snapshot_preview_includes_render_capture_payload() -> None:
    preview = type(
        "_Preview",
        (),
        {
            "title": "",
            "signer_label_prefix": "",
            "layout_template": SignatureLayoutTemplate.SINGLE_LINE,
            "stamp_position": SignatureStampPosition.TOP,
            "timezone_display_mode": SignatureTimezoneDisplayMode.UTC,
            "show_field_names": False,
            "datetime_format": "%Y-%m-%d",
            "image_stamp_path": None,
            "signature_rect": build_signature_rect(page_index=0, width_pt=220.0, height_pt=30.0),
            "text_style": None,
            "box_style": None,
            "fields": (),
            "issues": (),
            "can_submit": True,
        },
    )()

    snapshot = _snapshot_preview(
        preview,
        render_capture={"preview_image_path": "artifacts/preview.png"},
    )

    assert snapshot["render_capture"] == {"preview_image_path": "artifacts/preview.png"}


def test_analyze_stamp_source_image_reports_alpha_bounds(tmp_path: Path) -> None:
    image_path = tmp_path / "transparent_stamp.png"
    image = Image.new("RGBA", (20, 10), color=(0, 0, 0, 0))
    for x in range(4, 16):
        for y in range(2, 8):
            image.putpixel((x, y), (10, 40, 90, 255))
    image.save(image_path, format="PNG")

    analysis = _analyze_stamp_source_image(str(image_path))

    assert analysis["stamp_source_image_size_px"] == {"width": 20, "height": 10}
    assert analysis["stamp_source_content_bounds_px"] == {
        "x": 4,
        "y": 2,
        "width": 12,
        "height": 6,
    }
    assert analysis["stamp_source_content_error"] is None


def test_project_content_bounds_to_preview_scales_source_bounds() -> None:
    projected = _project_content_bounds_to_preview(
        source_image_size={"width": 20, "height": 10},
        source_content_bounds={"x": 4, "y": 2, "width": 12, "height": 6},
        pixmap_bounds={"x": 10, "y": 5, "width": 100, "height": 50},
    )

    assert projected == {"x": 30, "y": 15, "width": 60, "height": 30}


def test_stamp_edge_diagnostics_flags_touching_but_not_one_pixel_clearance() -> None:
    preview = type(
        "_Preview",
        (),
        {
            "box_style": type(
                "_BoxStyle",
                (),
                {"show_border": True, "border_width_pt": 3.5},
            )(),
        },
    )()

    diagnostics = _stamp_edge_diagnostics(
        preview=preview,
        stamp_band_bounds={"x": 0, "y": 0, "width": 100, "height": 40},
        stamp_pixmap_bounds={"x": 0, "y": 5, "width": 80, "height": 20},
        stamp_content_bounds={"x": 1, "y": 6, "width": 70, "height": 18},
    )

    assert diagnostics["stamp_pixmap_touches_band_edge"] is True
    assert diagnostics["stamp_content_touches_band_edge"] is False
    assert diagnostics["stamp_content_within_warning_distance"] is False
    assert diagnostics["stamp_content_warning_threshold_px"] == 0
    assert diagnostics["stamp_content_min_edge_distance_px"] == 1


def test_write_stamp_debug_overlay_writes_debug_crop(tmp_path: Path) -> None:
    preview_image_path = tmp_path / "preview.png"
    output_path = tmp_path / "stamp_debug.png"
    Image.new("RGBA", (120, 60), color=(255, 255, 255, 255)).save(preview_image_path)

    error = _write_stamp_debug_overlay(
        preview_image_path=str(preview_image_path),
        output_path=str(output_path),
        stamp_band_bounds={"x": 10, "y": 8, "width": 70, "height": 24},
        stamp_pixmap_bounds={"x": 14, "y": 10, "width": 52, "height": 18},
        stamp_content_bounds={"x": 18, "y": 12, "width": 40, "height": 12},
        crop_padding=6,
    )

    assert error is None
    assert output_path.exists()


def test_detect_text_content_bounds_in_preview_finds_rendered_pixels(tmp_path: Path) -> None:
    preview_path = tmp_path / "preview.png"
    image = Image.new("RGBA", (80, 40), color=(255, 255, 255, 255))
    for x in range(18, 46):
        for y in range(12, 21):
            image.putpixel((x, y), (0, 0, 0, 255))
    image.save(preview_path, format="PNG")

    bounds, error = _detect_text_content_bounds_in_preview(
        preview_image_path=str(preview_path),
        text_widget_bounds={"x": 10, "y": 8, "width": 50, "height": 20},
        text_color_rgba=(0, 0, 0, 255),
    )

    assert error is None
    assert bounds == {"x": 18, "y": 12, "width": 28, "height": 9}


def test_detect_text_content_bounds_in_preview_captures_antialiased_text_edges(
    tmp_path: Path,
) -> None:
    preview_path = tmp_path / "preview_antialias.png"
    image = Image.new("RGBA", (80, 40), color=(255, 255, 255, 255))
    # Dark core
    for x in range(22, 40):
        for y in range(12, 18):
            image.putpixel((x, y), (0, 0, 0, 255))
    # Gray anti-aliased fringe that should still count as text.
    for x in range(20, 42):
        image.putpixel((x, 11), (120, 120, 120, 255))
        image.putpixel((x, 18), (120, 120, 120, 255))
    image.putpixel((21, 12), (120, 120, 120, 255))
    image.putpixel((40, 17), (120, 120, 120, 255))
    image.save(preview_path, format="PNG")

    bounds, error = _detect_text_content_bounds_in_preview(
        preview_image_path=str(preview_path),
        text_widget_bounds={"x": 10, "y": 8, "width": 40, "height": 20},
        text_color_rgba=(0, 0, 0, 255),
    )

    assert error is None
    assert bounds == {"x": 20, "y": 11, "width": 22, "height": 8}


def test_detect_text_content_bounds_in_preview_ignores_border_strokes(
    tmp_path: Path,
) -> None:
    preview_path = tmp_path / "preview_border.png"
    image = Image.new("RGBA", (80, 40), color=(255, 255, 255, 255))
    for x in range(10, 60):
        image.putpixel((x, 27), (0, 0, 0, 255))
    for x in range(22, 38):
        for y in range(14, 19):
            image.putpixel((x, y), (0, 0, 0, 255))
    image.save(preview_path, format="PNG")

    bounds, error = _detect_text_content_bounds_in_preview(
        preview_image_path=str(preview_path),
        text_widget_bounds={"x": 10, "y": 8, "width": 50, "height": 20},
        text_color_rgba=(0, 0, 0, 255),
    )

    assert error is None
    assert bounds == {"x": 22, "y": 14, "width": 16, "height": 5}


def test_detect_text_content_bounds_in_preview_uses_reference_envelope_to_reject_wide_noise(
    tmp_path: Path,
) -> None:
    preview_path = tmp_path / "preview_reference_guided.png"
    image = Image.new("RGBA", (120, 50), color=(255, 255, 255, 255))
    for x in range(10, 110):
        image.putpixel((x, 30), (0, 0, 0, 255))
    for x in range(28, 52):
        for y in range(16, 22):
            image.putpixel((x, y), (0, 0, 0, 255))
    image.save(preview_path, format="PNG")

    bounds, error = _detect_text_content_bounds_in_preview(
        preview_image_path=str(preview_path),
        text_widget_bounds={"x": 10, "y": 10, "width": 100, "height": 24},
        text_color_rgba=(0, 0, 0, 255),
        reference_text_content_bounds={"x": 18, "y": 4, "width": 28, "height": 10},
    )

    assert error is None
    assert bounds == {"x": 28, "y": 16, "width": 24, "height": 6}


def test_text_edge_diagnostics_flags_stamp_facing_touch_and_overlap() -> None:
    preview = type(
        "_Preview",
        (),
        {"stamp_position": SignatureStampPosition.BOTTOM},
    )()

    diagnostics = _text_edge_diagnostics(
        preview=preview,
        card_bounds={"x": 0, "y": 0, "width": 120, "height": 80},
        text_widget_bounds={"x": 10, "y": 10, "width": 80, "height": 30},
        text_content_bounds={"x": 12, "y": 12, "width": 60, "height": 28},
        reference_text_content_bounds={"x": 12, "y": 12, "width": 60, "height": 28},
        stamp_band_bounds={"x": 10, "y": 40, "width": 80, "height": 20},
        stamp_content_bounds={"x": 15, "y": 42, "width": 40, "height": 12},
    )

    assert diagnostics["text_content_stamp_facing_distance_px"] == 0
    assert diagnostics["text_content_touches_stamp_facing_edge"] is True
    assert diagnostics["text_content_overlaps_stamp_band"] is False
    assert diagnostics["text_content_clipped_in_preview"] is False


def test_text_edge_diagnostics_flags_reference_content_loss_as_clipping() -> None:
    preview = type(
        "_Preview",
        (),
        {"stamp_position": SignatureStampPosition.BOTTOM},
    )()

    diagnostics = _text_edge_diagnostics(
        preview=preview,
        card_bounds={"x": 0, "y": 0, "width": 120, "height": 80},
        text_widget_bounds={"x": 10, "y": 10, "width": 80, "height": 30},
        text_content_bounds={"x": 10, "y": 10, "width": 56, "height": 24},
        reference_text_content_bounds={"x": 12, "y": 12, "width": 60, "height": 28},
        stamp_band_bounds={"x": 10, "y": 40, "width": 80, "height": 20},
        stamp_content_bounds={"x": 15, "y": 42, "width": 40, "height": 12},
    )

    assert diagnostics["text_content_reference_width_loss_px"] == 4
    assert diagnostics["text_content_reference_height_loss_px"] == 4
    assert diagnostics["text_content_clipped_in_preview"] is True


def test_text_edge_diagnostics_ignores_reference_loss_without_edge_contact() -> None:
    preview = type(
        "_Preview",
        (),
        {"stamp_position": SignatureStampPosition.TOP},
    )()

    diagnostics = _text_edge_diagnostics(
        preview=preview,
        card_bounds={"x": 0, "y": 0, "width": 200, "height": 80},
        text_widget_bounds={"x": 10, "y": 10, "width": 140, "height": 40},
        text_content_bounds={"x": 14, "y": 18, "width": 120, "height": 18},
        reference_text_content_bounds={"x": 0, "y": 0, "width": 120, "height": 24},
        stamp_band_bounds={"x": 10, "y": 52, "width": 140, "height": 14},
        stamp_content_bounds={"x": 15, "y": 54, "width": 70, "height": 8},
    )

    assert diagnostics["text_content_reference_height_loss_px"] == 6
    assert diagnostics["text_content_touches_widget_edge"] is False
    assert diagnostics["text_content_clipped_in_preview"] is False


def test_text_edge_diagnostics_flags_small_height_loss_at_edge() -> None:
    preview = type(
        "_Preview",
        (),
        {"stamp_position": SignatureStampPosition.TOP},
    )()

    diagnostics = _text_edge_diagnostics(
        preview=preview,
        card_bounds={"x": 0, "y": 0, "width": 120, "height": 80},
        text_widget_bounds={"x": 10, "y": 10, "width": 80, "height": 20},
        text_content_bounds={"x": 12, "y": 10, "width": 60, "height": 18},
        reference_text_content_bounds={"x": 12, "y": 10, "width": 60, "height": 20},
        stamp_band_bounds={"x": 10, "y": 0, "width": 80, "height": 8},
        stamp_content_bounds={"x": 15, "y": 1, "width": 40, "height": 6},
    )

    assert diagnostics["text_content_reference_height_loss_px"] == 2
    assert diagnostics["text_content_clipped_in_preview"] is True


def test_text_font_diagnostics_reports_cursive_as_direct_preview_family() -> None:
    preview = type(
        "_Preview",
        (),
        {
            "text_style": type(
                "_TextStyle",
                (),
                {"font_family": "Cursive", "font_size_pt": 8.5},
            )(),
        },
    )()

    class _Font:
        def family(self) -> str:
            return "Liberation Sans"

        def pointSizeF(self) -> float:
            return 8.5

    class _Label:
        def font(self):
            return _Font()

        def fontInfo(self):
            return _Font()

    diagnostics = _text_font_diagnostics(preview=preview, active_label=_Label())

    assert diagnostics["requested_text_font_category"] == "cursive"
    assert diagnostics["effective_text_font_category"] == "sans_serif"
    assert diagnostics["font_family_direct_preview_mapping_supported"] is True
    assert diagnostics["font_family_category_mismatch"] is True


def test_text_font_diagnostics_classifies_sans_serif_and_bracketed_qt_family() -> None:
    preview = type(
        "_Preview",
        (),
        {
            "text_style": type(
                "_TextStyle",
                (),
                {"font_family": "Sans Serif", "font_size_pt": 10.0},
            )(),
        },
    )()

    class _Font:
        def family(self) -> str:
            return "Arial [Mono]"

        def pointSizeF(self) -> float:
            return 10.0

    class _Label:
        def font(self):
            return _Font()

        def fontInfo(self):
            return _Font()

    diagnostics = _text_font_diagnostics(preview=preview, active_label=_Label())

    assert diagnostics["requested_text_font_category"] == "sans_serif"
    assert diagnostics["effective_text_font_category"] == "sans_serif"
    assert diagnostics["font_family_category_mismatch"] is False


def test_write_text_debug_overlay_writes_expected_file(tmp_path: Path) -> None:
    preview_path = tmp_path / "preview.png"
    output_path = tmp_path / "text_debug.png"
    Image.new("RGBA", (120, 60), color=(255, 255, 255, 255)).save(preview_path)

    error = _write_text_debug_overlay(
        preview_image_path=str(preview_path),
        output_path=str(output_path),
        text_widget_bounds={"x": 10, "y": 12, "width": 50, "height": 18},
        text_content_bounds={"x": 14, "y": 16, "width": 30, "height": 8},
        stamp_band_bounds={"x": 10, "y": 34, "width": 50, "height": 12},
        crop_padding=6,
    )

    assert error is None
    assert output_path.exists() is True


def test_preview_edge_distances_report_top_and_bottom_clearance() -> None:
    preview = type(
        "_Preview",
        (),
        {
            "signature_rect": build_signature_rect(page_index=0, width_pt=220.0, height_pt=28.0),
            "layout_template": SignatureLayoutTemplate.SINGLE_LINE,
            "stamp_position": SignatureStampPosition.BOTTOM,
            "box_style": None,
        },
    )()

    distances = _preview_edge_distances(
        preview=preview,
        card_bounds={"x": 0, "y": 0, "width": 200, "height": 80},
        body_bounds={"x": 6, "y": 6, "width": 188, "height": 68},
        detail_bounds={"x": 0, "y": 0, "width": 188, "height": 28},
        stamp_bounds={"x": 0, "y": 40, "width": 188, "height": 20},
    )

    assert distances["text_top_to_border_px"] == 6
    assert distances["stamp_bottom_to_border_px"] == 14
    assert distances["content_top_to_border_px"] == 6
    assert distances["content_bottom_to_border_px"] == 14


def test_analyze_stamp_source_image_reports_alpha_content_bounds(tmp_path: Path) -> None:
    stamp_path = tmp_path / "transparent_stamp.png"
    _write_transparent_test_stamp_image(stamp_path)

    analysis = _analyze_stamp_source_image(str(stamp_path))

    assert analysis["stamp_source_image_size_px"] == {"width": 100, "height": 50}
    assert analysis["stamp_source_content_bounds_px"] == {
        "x": 12,
        "y": 8,
        "width": 72,
        "height": 30,
    }
    assert analysis["stamp_source_content_error"] is None


def test_analyze_stamp_source_image_reports_empty_alpha_as_error(tmp_path: Path) -> None:
    stamp_path = tmp_path / "empty_stamp.png"
    _write_fully_transparent_stamp_image(stamp_path)

    analysis = _analyze_stamp_source_image(str(stamp_path))

    assert analysis["stamp_source_image_size_px"] == {"width": 40, "height": 20}
    assert analysis["stamp_source_content_bounds_px"] is None
    assert analysis["stamp_source_content_error"] == (
        "Stamp source image contains no non-transparent pixels."
    )


def test_project_content_bounds_to_preview_scales_into_pixmap_bounds() -> None:
    projected = _project_content_bounds_to_preview(
        source_image_size={"width": 100, "height": 50},
        source_content_bounds={"x": 10, "y": 5, "width": 60, "height": 20},
        pixmap_bounds={"x": 40, "y": 12, "width": 80, "height": 40},
    )

    assert projected == {"x": 48, "y": 16, "width": 48, "height": 16}


def test_stamp_edge_diagnostics_flags_touching_without_one_pixel_warning() -> None:
    preview = type(
        "_Preview",
        (),
        {
            "box_style": type(
                "_BoxStyle",
                (),
                {"show_border": True, "border_width_pt": 3.5},
            )(),
        },
    )()

    diagnostics = _stamp_edge_diagnostics(
        preview=preview,
        stamp_band_bounds={"x": 10, "y": 10, "width": 60, "height": 20},
        stamp_pixmap_bounds={"x": 10, "y": 12, "width": 58, "height": 18},
        stamp_content_bounds={"x": 11, "y": 12, "width": 56, "height": 17},
    )

    assert diagnostics["stamp_pixmap_touches_band_edge"] is True
    assert diagnostics["stamp_content_touches_band_edge"] is False
    assert diagnostics["stamp_content_warning_threshold_px"] == 0
    assert diagnostics["stamp_content_min_edge_distance_px"] == 1
    assert diagnostics["stamp_content_within_warning_distance"] is False


def test_stamp_edge_diagnostics_ignores_left_anchor_for_top_and_bottom() -> None:
    preview = type(
        "_Preview",
        (),
        {
            "stamp_position": SignatureStampPosition.TOP,
            "box_style": type(
                "_BoxStyle",
                (),
                {"show_border": True, "border_width_pt": 3.5},
            )(),
        },
    )()

    diagnostics = _stamp_edge_diagnostics(
        preview=preview,
        stamp_band_bounds={"x": 10, "y": 10, "width": 60, "height": 20},
        stamp_pixmap_bounds={"x": 10, "y": 12, "width": 30, "height": 16},
        stamp_content_bounds={"x": 10, "y": 13, "width": 20, "height": 14},
    )

    assert diagnostics["stamp_content_edge_distances_px"] == {
        "top": 3,
        "right": 40,
        "bottom": 3,
        "left": 0,
    }
    assert diagnostics["stamp_content_min_edge_distance_px"] == 3
    assert diagnostics["stamp_content_touches_band_edge"] is False
    assert diagnostics["stamp_content_within_warning_distance"] is False


def test_stamp_edge_diagnostics_uses_uniform_touch_only_threshold() -> None:
    for layout_template in (
        SignatureLayoutTemplate.SINGLE_LINE,
        SignatureLayoutTemplate.MULTI_LINE,
        SignatureLayoutTemplate.WRAPPED_BLOCK,
    ):
        preview = type(
            "_Preview",
            (),
            {
                "layout_template": layout_template,
                "stamp_position": SignatureStampPosition.RIGHT,
                "box_style": type(
                    "_BoxStyle",
                    (),
                    {"show_border": True, "border_width_pt": 3.5},
                )(),
            },
        )()

        diagnostics = _stamp_edge_diagnostics(
            preview=preview,
            stamp_band_bounds={"x": 10, "y": 10, "width": 40, "height": 40},
            stamp_pixmap_bounds={"x": 14, "y": 14, "width": 24, "height": 24},
            stamp_content_bounds={"x": 12, "y": 12, "width": 26, "height": 26},
        )

        assert diagnostics["stamp_content_warning_threshold_px"] == 0
        assert diagnostics["stamp_content_min_edge_distance_px"] == 12
        assert diagnostics["stamp_content_within_warning_distance"] is False


def test_stamp_edge_diagnostics_ignores_text_facing_edge_for_multi_line_top() -> None:
    preview = type(
        "_Preview",
        (),
        {
            "layout_template": SignatureLayoutTemplate.MULTI_LINE,
            "stamp_position": SignatureStampPosition.TOP,
            "box_style": type(
                "_BoxStyle",
                (),
                {"show_border": True, "border_width_pt": 1.0},
            )(),
        },
    )()

    diagnostics = _stamp_edge_diagnostics(
        preview=preview,
        stamp_band_bounds={"x": 7, "y": 24, "width": 234, "height": 59},
        stamp_pixmap_bounds={"x": 7, "y": 28, "width": 230, "height": 55},
        stamp_content_bounds={"x": 8, "y": 30, "width": 228, "height": 53},
    )

    assert diagnostics["stamp_content_edge_distances_px"] == {
        "left": 1,
        "top": 6,
        "right": 5,
        "bottom": 0,
    }
    assert diagnostics["stamp_content_min_edge_distance_px"] == 6
    assert diagnostics["stamp_content_touches_band_edge"] is False
    assert diagnostics["stamp_content_within_warning_distance"] is False


def test_stamp_edge_diagnostics_ignores_text_facing_edge_for_single_line_top() -> None:
    preview = type(
        "_Preview",
        (),
        {
            "layout_template": SignatureLayoutTemplate.SINGLE_LINE,
            "stamp_position": SignatureStampPosition.TOP,
            "box_style": type(
                "_BoxStyle",
                (),
                {"show_border": True, "border_width_pt": 3.5},
            )(),
        },
    )()

    diagnostics = _stamp_edge_diagnostics(
        preview=preview,
        stamp_band_bounds={"x": 9, "y": 9, "width": 341, "height": 11},
        stamp_pixmap_bounds={"x": 10, "y": 12, "width": 8, "height": 8},
        stamp_content_bounds={"x": 10, "y": 13, "width": 7, "height": 7},
    )

    assert diagnostics["stamp_content_edge_distances_px"] == {
        "bottom": 0,
        "left": 1,
        "right": 333,
        "top": 4,
    }
    assert diagnostics["stamp_content_min_edge_distance_px"] == 4
    assert diagnostics["stamp_content_touches_band_edge"] is False
    assert diagnostics["stamp_content_within_warning_distance"] is False


def test_write_stamp_debug_overlay_writes_expected_file(tmp_path: Path) -> None:
    preview_path = tmp_path / "preview.png"
    output_path = tmp_path / "stamp_debug.png"
    Image.new("RGBA", (120, 60), color=(255, 255, 255, 255)).save(preview_path)

    error = _write_stamp_debug_overlay(
        preview_image_path=str(preview_path),
        output_path=str(output_path),
        stamp_band_bounds={"x": 10, "y": 12, "width": 50, "height": 18},
        stamp_pixmap_bounds={"x": 14, "y": 14, "width": 32, "height": 12},
        stamp_content_bounds={"x": 18, "y": 16, "width": 20, "height": 8},
        crop_padding=6,
    )

    assert error is None
    assert output_path.exists() is True


def test_widget_is_visible_supports_real_and_fake_widget_shapes() -> None:
    fake_widget = type("_FakeWidget", (), {"visible": False})()
    qt_like_widget = type(
        "_QtLikeWidget",
        (),
        {"isVisible": lambda self: True},
    )()

    assert _widget_is_visible(fake_widget) is False
    assert _widget_is_visible(qt_like_widget) is True
    assert _widget_is_visible(object()) is True


def test_preview_matrix_error_result_records_scenario_name_and_error_type() -> None:
    result = _preview_matrix_error_result(
        scenario={"name": "Broken Scenario", "profile_name": "Saved Profile"},
        error=ValueError("bad border width"),
    )

    assert result == {
        "name": "Broken Scenario",
        "profile_name": "Saved Profile",
        "error": "bad border width",
        "error_type": "ValueError",
    }


def test_preview_matrix_diagnostic_summary_counts_text_risks() -> None:
    summary = _preview_matrix_diagnostic_summary(
        [
            {
                "preview_snapshot": {
                    "can_submit": True,
                    "render_capture": {
                        "text_content_clipped_in_preview": True,
                        "text_content_overlaps_stamp_band": False,
                        "text_content_overlaps_stamp_content": False,
                        "stamp_content_within_warning_distance": True,
                        "stamp_content_touches_band_edge": False,
                    }
                }
            },
            {
                "preview_snapshot": {
                    "can_submit": False,
                    "render_capture": {
                        "text_content_clipped_in_preview": False,
                        "text_content_overlaps_stamp_band": True,
                        "text_content_overlaps_stamp_content": False,
                        "stamp_content_within_warning_distance": False,
                        "stamp_content_touches_band_edge": True,
                    }
                }
            },
            {"error": "boom"},
        ]
    )

    assert summary == {
        "text_clipping_risk_scenario_count": 1,
        "signable_text_clipping_risk_scenario_count": 1,
        "rejected_text_clipping_risk_scenario_count": 0,
        "text_stamp_overlap_risk_scenario_count": 1,
        "signable_text_stamp_overlap_risk_scenario_count": 0,
        "rejected_text_stamp_overlap_risk_scenario_count": 1,
        "stamp_warning_scenario_count": 1,
        "signable_stamp_warning_scenario_count": 1,
        "rejected_stamp_warning_scenario_count": 0,
        "stamp_edge_touch_scenario_count": 1,
        "signable_stamp_edge_touch_scenario_count": 0,
        "rejected_stamp_edge_touch_scenario_count": 1,
    }


def test_apply_preview_matrix_scenario_syncs_viewer_to_signature_rect_page() -> None:
    class _FakeProfileStore:
        def load_catalog(self):
            return type(
                "_Catalog",
                (),
                {"profile_named": lambda self, name: (_ for _ in ()).throw(KeyError(name))},
            )()

    class _FakePanel:
        def __init__(self) -> None:
            self.appearance = None
            self.rect = None
            self._workflow = type(
                "_Workflow",
                (),
                {"current_signature_appearance": build_signature_appearance()},
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

    shell = type(
        "_Shell",
        (),
        {
            "properties_panel": _FakePanel(),
            "_viewer_workflow": _FakeViewerWorkflow(),
            "_viewer_widget": _FakeViewerWidget(),
            "refresh_viewer": lambda self: None,
        },
    )()

    _apply_preview_matrix_scenario(
        shell=shell,
        scenario={
            "name": "Page Four",
            "signature_rect": {
                "page_index": 3,
                "left_pt": 24,
                "bottom_pt": 18,
                "width_pt": 120,
                "height_pt": 36,
            },
            "appearance_overrides": {
                "layout_template": "single_line",
                "stamp_position": "top",
            },
        },
        profile_store=_FakeProfileStore(),
    )

    assert shell.properties_panel.rect is not None
    assert shell.properties_panel.rect.page_index == 3
    assert shell._viewer_workflow.jumps == [3]
    assert shell._viewer_widget.refresh_calls == [True]


def test_widget_application_returns_none_when_pyside_is_unavailable(
    monkeypatch,
) -> None:
    real_import_module = importlib.import_module

    def _fake_import_module(name: str, package: str | None = None):
        if name == "PySide6.QtWidgets":
            raise ModuleNotFoundError(name)
        return real_import_module(name, package)

    monkeypatch.setattr(importlib, "import_module", _fake_import_module)

    assert _widget_application(object()) is None


def test_load_preview_matrix_manifest_accepts_object_or_array(tmp_path: Path) -> None:
    object_manifest = tmp_path / "object.json"
    array_manifest = tmp_path / "array.json"
    object_manifest.write_text(
        json.dumps(
            {
                "scenarios": [
                    {
                        "name": "Compact Top",
                        "signature_rect": {
                            "page_index": 0,
                            "left_pt": 1,
                            "bottom_pt": 2,
                            "width_pt": 3,
                            "height_pt": 4,
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    array_manifest.write_text(
        json.dumps(
            [
                {
                    "name": "Compact Bottom",
                    "signature_rect": {
                        "page_index": 0,
                        "left_pt": 1,
                        "bottom_pt": 2,
                        "width_pt": 3,
                        "height_pt": 4,
                    },
                }
            ]
        ),
        encoding="utf-8",
    )

    assert (
        _load_preview_matrix_manifest(str(object_manifest))["scenarios"][0]["name"]
        == "Compact Top"
    )
    assert (
        _load_preview_matrix_manifest(str(array_manifest))["scenarios"][0]["name"]
        == "Compact Bottom"
    )


def test_stress_preview_manifests_exist_and_parse() -> None:
    for name in (
        "single_line_full_matrix_stress.json",
        "multi_line_full_matrix_stress.json",
        "wrapped_block_full_matrix_stress.json",
    ):
        manifest = _load_preview_matrix_manifest(str(Path("artifacts/preview_sweep_assets") / name))
        assert manifest["scenarios"]


def test_signed_acceptance_manifest_exists_and_parses() -> None:
    manifest = _load_preview_matrix_manifest(SIGNED_ACCEPTANCE_SCENARIO_MANIFEST)

    assert len(manifest["scenarios"]) >= 9
    assert manifest["fixture_profile"] == STRESS_VISIBLE_APPEARANCE_PROFILE
    assert manifest["fixture_role"] == "signed_acceptance"
    assert manifest["acceptance_expectations"]["minimum_successful_signing_run_count"] >= 6
    assert manifest["acceptance_expectations"]["expected_intentional_rejection_count"] >= 3
    assert any("single_line" in scenario["name"] for scenario in manifest["scenarios"])
    assert any("multi_line" in scenario["name"] for scenario in manifest["scenarios"])
    assert any("wrapped_block" in scenario["name"] for scenario in manifest["scenarios"])
    assert all(
        scenario.get("expected_outcome") in {"success", "validation_rejection"}
        for scenario in manifest["scenarios"]
    )


def test_signed_acceptance_fixture_assets_exist_and_are_parseable() -> None:
    fixture_pdf = Path(SIGNED_ACCEPTANCE_FIXTURE_PDF)
    fixture_identity = Path(SIGNED_ACCEPTANCE_IDENTITY_P12)

    assert fixture_pdf.exists()
    assert fixture_identity.exists()

    with fixture_pdf.open("rb") as handle:
        reader = PdfFileReader(handle)
        assert len(list(reader.root["/Pages"]["/Kids"])) >= 1


def test_stress_preview_manifests_reference_stress_fixture_profile() -> None:
    for name in (
        "single_line_full_matrix_stress.json",
        "multi_line_full_matrix_stress.json",
        "wrapped_block_full_matrix_stress.json",
    ):
        payload = json.loads((Path("artifacts/preview_sweep_assets") / name).read_text())
        assert payload["fixture_profile"] == STRESS_VISIBLE_APPEARANCE_PROFILE
        assert all(
            scenario["appearance_overrides"]["fixture_profile"] == STRESS_VISIBLE_APPEARANCE_PROFILE
            for scenario in payload["scenarios"]
        )


def test_single_line_stress_manifest_includes_required_dense_field_sets() -> None:
    payload = json.loads(
        Path("artifacts/preview_sweep_assets/single_line_full_matrix_stress.json").read_text()
    )
    field_sets = {
        tuple(scenario["appearance_overrides"]["visible_fields"])
        for scenario in payload["scenarios"]
    }
    assert ("common_name", "signing_time") in field_sets
    assert ("common_name", "company", "signing_time") in field_sets
    assert (
        "common_name",
        "email",
        "title",
        "company",
        "signing_time",
    ) in field_sets


def test_signed_acceptance_manifest_includes_required_positive_and_negative_families() -> None:
    payload = json.loads(Path(SIGNED_ACCEPTANCE_SCENARIO_MANIFEST).read_text())
    names = [scenario["name"] for scenario in payload["scenarios"]]
    expected_outcomes = {
        scenario["name"]: scenario["expected_outcome"] for scenario in payload["scenarios"]
    }

    assert "single_line_top_no_stamp_sparse_large" in names
    assert "single_line_top_stamp_sparse_large" in names
    assert "multi_line_top_sparse_large" in names
    assert "multi_line_left_medium_large" in names
    assert "multi_line_left_dense_large" in names
    assert "wrapped_block_top_medium_relaxed" in names
    assert "wrapped_block_right_sparse_large" in names
    assert "single_line_top_dense_compact_reject" in names
    assert "multi_line_left_dense_compact_reject" in names
    assert "wrapped_block_top_dense_reject" in names
    assert expected_outcomes["single_line_top_dense_compact_reject"] == "validation_rejection"
    assert expected_outcomes["multi_line_left_dense_compact_reject"] == "validation_rejection"
    assert expected_outcomes["wrapped_block_top_dense_reject"] == "validation_rejection"


def test_stress_preview_manifests_preserve_expected_family_variants() -> None:
    expectations = {
        "multi_line_full_matrix_stress.json": {
            "field_sets": {
                ("common_name", "email", "signing_time"),
                ("common_name", "title", "company", "signing_time"),
                (
                    "common_name",
                    "email",
                    "title",
                    "company",
                    "signing_time",
                    "location",
                    "reason",
                ),
            },
            "label_tokens": {"_label_", "_nolabel_"},
        },
        "wrapped_block_full_matrix_stress.json": {
            "field_sets": {
                ("common_name", "email", "signing_time"),
                ("common_name", "title", "company", "signing_time", "location"),
                (
                    "common_name",
                    "email",
                    "title",
                    "company",
                    "signing_time",
                    "location",
                    "reason",
                ),
            },
            "label_tokens": {"_label_", "_nolabel_"},
            "name_tokens": {"_named", "_plain"},
        },
    }
    for manifest_name, expectation in expectations.items():
        payload = json.loads((Path("artifacts/preview_sweep_assets") / manifest_name).read_text())
        names = [scenario["name"] for scenario in payload["scenarios"]]
        field_sets = {
            tuple(scenario["appearance_overrides"]["visible_fields"])
            for scenario in payload["scenarios"]
        }
        assert expectation["field_sets"].issubset(field_sets)
        for token in expectation["label_tokens"]:
            assert any(token in name for name in names)
        for token in expectation.get("name_tokens", set()):
            assert any(token in name for name in names)


def test_apply_appearance_overrides_updates_common_preview_controls() -> None:
    appearance = build_signature_appearance()

    updated = _apply_appearance_overrides(
        appearance,
        {
            "layout_template": "single_line",
            "stamp_position": "bottom",
            "image_stamp_path": "/tmp/stamp.png",
            "box_style": {
                "border_width_pt": 3.5,
                "background_color_hex": "#EEEEEE",
            },
            "text_style": {
                "font_size_pt": 8.5,
                "italic": True,
            },
        },
    )

    assert updated.layout_template == SignatureLayoutTemplate.SINGLE_LINE
    assert updated.stamp_position == SignatureStampPosition.BOTTOM
    assert updated.image_stamp_path == "/tmp/stamp.png"
    assert updated.box_style.border_width_pt == 3.5
    assert updated.box_style.background_color_hex == "#EEEEEE"


def test_apply_appearance_overrides_can_apply_stress_fixture_profile() -> None:
    updated = _apply_appearance_overrides(
        build_signature_appearance(),
        {"fixture_profile": STRESS_VISIBLE_APPEARANCE_PROFILE},
    )

    assert updated.common_name.override_text == "Morgan Ellery"
    assert updated.email.override_text == "records.operations@northwindledger.org"
    assert updated.company.override_text == "Northwind Ledger Holdings"


def test_apply_appearance_overrides_can_limit_visible_fields() -> None:
    appearance = build_signature_appearance()

    updated = _apply_appearance_overrides(
        appearance,
        {
            "visible_fields": ["common_name", "signing_time"],
        },
    )

    assert updated.common_name.show_in_visible_appearance is True
    assert updated.signing_time.show_in_visible_appearance is True
    assert updated.distinguished_name.source.value == "hidden"
    assert updated.email.source.value == "hidden"
    assert updated.title.source.value == "hidden"
    assert updated.company.source.value == "hidden"


def test_apply_visible_fields_override_rejects_empty_or_unknown_values() -> None:
    appearance = build_signature_appearance()

    with pytest.raises(ValueError):
        _apply_visible_fields_override(appearance, [])
    with pytest.raises(ValueError):
        _apply_visible_fields_override(appearance, ["not_a_field"])


def test_backend_reservation_snapshot_retains_error_details_for_bad_request() -> None:
    appearance = SignatureAppearance(
        signer_label_prefix="Digitally signed by",
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        common_name=SignatureFieldBinding(),
        email=SignatureFieldBinding(),
        title=SignatureFieldBinding(),
        company=SignatureFieldBinding(),
        signing_time=SignatureFieldBinding(),
        reason=SignatureFieldBinding(),
        location=SignatureFieldBinding(),
        field_order=(
            SignatureFieldKey.DISTINGUISHED_NAME,
            SignatureFieldKey.COMMON_NAME,
            SignatureFieldKey.EMAIL,
            SignatureFieldKey.TITLE,
            SignatureFieldKey.COMPANY,
            SignatureFieldKey.SIGNING_TIME,
            SignatureFieldKey.REASON,
            SignatureFieldKey.LOCATION,
        ),
    )
    request = SigningRequest(
        input_pdf_path="/tmp/sample.pdf",
        output_pdf_path="/tmp/sample-signed.pdf",
        certificate_path="/tmp/missing-cert.p12",
        passphrase="passphrase",
        tsa_url="https://tsa.example.invalid",
        timestamp_required=False,
        signature_rect=SignatureRect(
            page_index=0,
            left_pt=10.0,
            bottom_pt=20.0,
            width_pt=30.0,
            height_pt=40.0,
        ),
        signature_appearance=appearance,
    )

    snapshot = _snapshot_backend_reservation(request)

    assert snapshot is not None
    assert snapshot["layout_template"] == "single_line"
    assert snapshot["signature_rect"]["page_number"] == 1
    assert "missing-cert.p12" in snapshot["error"]


def test_snapshot_current_draft_request_uses_workflow_state(tmp_path: Path) -> None:
    request = build_signing_request(
        tmp_path,
        input_name="input.pdf",
        output_name="output.pdf",
        certificate_name="cert.p12",
        passphrase="secret",
        timestamp_required=False,
        signature_rect=build_signature_rect(page_index=1, width_pt=320.0, height_pt=64.0),
        signature_appearance=build_signature_appearance(
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=SignatureStampPosition.LEFT,
        ),
    )

    draft_request = _snapshot_current_draft_request(
        SigningDraftWorkflow.from_signing_request(request)
    )

    assert draft_request is not None
    assert draft_request.input_pdf_path == request.input_pdf_path
    assert draft_request.output_pdf_path == request.output_pdf_path
    assert draft_request.certificate_path == request.certificate_path
    assert draft_request.signature_rect == request.signature_rect
    assert draft_request.signature_appearance == request.signature_appearance


def test_backend_reservation_snapshot_uses_backend_appearance_fields(tmp_path: Path) -> None:
    input_pdf = tmp_path / "input.pdf"
    cert_path = tmp_path / "cert.p12"
    stamp_path = tmp_path / "stamp.png"
    _write_test_pdf(input_pdf)
    _write_test_pkcs12(cert_path, passphrase="secret")
    _write_test_stamp_image(stamp_path)

    appearance = build_signature_appearance(
        image_stamp_path=str(stamp_path),
        signer_label_prefix="Digitally signed by",
        show_field_names=False,
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.TOP,
        distinguished_name=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
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
        text_style=SignatureTextStyle(
            font_family="Serif",
            font_size_pt=8.0,
            bold=False,
            italic=False,
            text_color_hex="#000000",
        ),
    )
    request = build_signing_request(
        tmp_path,
        input_name="input.pdf",
        output_name="output.pdf",
        certificate_name="cert.p12",
        passphrase="secret",
        timestamp_required=False,
        signature_rect=build_signature_rect(page_index=0, width_pt=540.0, height_pt=120.0),
        signature_appearance=appearance,
    )

    snapshot = _snapshot_backend_reservation(request)

    assert snapshot is not None
    assert snapshot["layout_template"] == "single_line"
    assert snapshot["stamp_position"] == "top"
    assert snapshot["signature_rect"]["page_number"] == 1
    assert "error" not in snapshot
    assert snapshot["stamp_text_length"] > 0
    assert snapshot["background_layout"]["inner_content_scaling"] == "shrink_to_fit"


def test_snapshot_visible_signature_appearance_extracts_text_and_image_facts(
    tmp_path: Path,
) -> None:
    output_pdf = _write_signed_test_pdf(tmp_path)

    snapshot = _snapshot_visible_signature_appearance(output_pdf)

    assert snapshot is not None
    assert snapshot["field_name"] == "Signature1"
    assert snapshot["annotation_rect"] == [24.0, 18.0, 564.0, 138.0]
    assert snapshot["appearance_stream_length"] > 0
    assert snapshot["appearance_has_visible_text"] is True
    assert snapshot["visible_text_present"] is True
    fragments = snapshot["appearance_text_fragments"]
    assert snapshot["text_fragments"] == fragments
    assert any("Digitally signed by" in fragment for fragment in fragments)
    assert any("Test User" in fragment for fragment in fragments)
    assert snapshot["appearance_image_xobject_count"] >= 1
    assert snapshot["appearance_xobjects"]
    assert snapshot["image_xobjects"] == snapshot["appearance_xobjects"]
    assert snapshot["annotation_rect_size"] == {"width": 540.0, "height": 120.0}
    assert snapshot["text_fragment_count"] == len(fragments)
    assert snapshot["image_xobject_count"] == snapshot["appearance_image_xobject_count"]
