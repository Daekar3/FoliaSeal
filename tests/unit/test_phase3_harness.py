import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID
from PIL import Image
from pyhanko.pdf_utils import generic
from pyhanko.pdf_utils.writer import PageObject, PdfFileWriter

from foliaseal.application import SigningDraftWorkflow
from foliaseal.application.phase3_signing_backend import build_phase3_signing_executor
from foliaseal.domain.models import (
    SignatureAppearance,
    SignatureFieldBinding,
    SignatureFieldKey,
    SignatureLayoutTemplate,
    SignatureRect,
    SignatureStampPosition,
    SigningRequest,
)
from foliaseal.presentation.qt.phase3_harness import (
    Phase3HarnessCapture,
    _snapshot_backend_reservation,
    _snapshot_current_draft_request,
    _snapshot_visible_signature_appearance,
    build_phase3_checklist_results_markdown,
)
from tests.support.phase3_builders import (
    build_signature_appearance,
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
        or build_signature_rect(page_index=0, width_pt=620.0, height_pt=180.0),
        signature_appearance=signature_appearance
        or build_signature_appearance(
            image_stamp_path=str(stamp_path),
            show_field_names=True,
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=SignatureStampPosition.TOP,
        ),
    )
    build_phase3_signing_executor().execute(request)
    return output_pdf


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


def test_phase3_harness_capture_to_json_handles_nested_non_json_objects(
    tmp_path: Path,
) -> None:
    opaque_path = tmp_path / "opaque.bin"
    opaque_path.write_bytes(b"opaque")

    with opaque_path.open("rb") as opaque_handle:
        capture = Phase3HarnessCapture(
            pdf_path="/tmp/sample.pdf",
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
        show_field_names=True,
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.TOP,
    )
    request = build_signing_request(
        tmp_path,
        input_name="input.pdf",
        output_name="output.pdf",
        certificate_name="cert.p12",
        passphrase="secret",
        timestamp_required=False,
        signature_rect=build_signature_rect(page_index=0, width_pt=620.0, height_pt=180.0),
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
    assert snapshot["annotation_rect"] == [24.0, 18.0, 644.0, 198.0]
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
    assert snapshot["annotation_rect_size"] == {"width": 620.0, "height": 180.0}
    assert snapshot["text_fragment_count"] == len(fragments)
    assert snapshot["image_xobject_count"] == snapshot["appearance_image_xobject_count"]
