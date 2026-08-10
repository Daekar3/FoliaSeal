from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID

from foliaseal.application.certificate_preview import CertificatePreviewValues
from foliaseal.application.coordinate_transform import PageBox, ViewRect, ViewTransform
from foliaseal.application.reusable_signing_models import (
    DEFAULT_PLACEMENT_SOURCE_PAGE,
    ResolvedSignaturePreset,
)
from foliaseal.application.signing_draft_contracts import (
    SignaturePlacementContext,
    SigningDraftValidationError,
)
from foliaseal.application.signing_draft_workflow import SigningDraftWorkflow
from foliaseal.application.signing_material_resolver import SigningMaterial
from foliaseal.domain.models import (
    SignatureAppearance,
    SignatureFieldBinding,
    SignatureFieldKey,
    SignatureFieldSource,
    SignatureLayoutTemplate,
    SignaturePlacementDefaults,
    SignatureRect,
    SignatureStampPosition,
    SignatureTextStyle,
    SignatureTimezoneDisplayMode,
)
from tests.support.signing_builders import build_certificate_configuration


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


def _write_test_pkcs12(path: Path, *, passphrase: str, common_name: str = "Alice Example") -> None:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "FoliaSeal"),
            x509.NameAttribute(NameOID.TITLE, "Board Secretary"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "QA"),
            x509.NameAttribute(NameOID.EMAIL_ADDRESS, "alice@example.com"),
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
        .not_valid_before(datetime.now(UTC))
        .not_valid_after(datetime.now(UTC) + timedelta(days=365))
        .sign(key, hashes.SHA256())
    )
    path.write_bytes(
        pkcs12.serialize_key_and_certificates(
            name=common_name.encode("utf-8"),
            key=key,
            cert=cert,
            cas=None,
            encryption_algorithm=serialization.BestAvailableEncryption(passphrase.encode("utf-8")),
        )
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
    assert preview.stamp_position == SignatureStampPosition.TOP
    assert preview.timezone_display_mode == SignatureTimezoneDisplayMode.UTC
    assert preview.show_field_names is False
    assert preview.datetime_format == "%Y-%m-%d %H:%M"
    assert preview.text_style == _appearance().text_style
    assert preview.box_style == _appearance().box_style
    assert preview.image_stamp_path == "/tmp/stamp.png"
    assert request.signing_time is not None
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


def test_preview_signing_time_is_invalidated_by_draft_mutation(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    workflow.set_signature_appearance(_appearance())
    workflow.set_signature_rect(
        SignatureRect(page_index=0, left_pt=10.0, bottom_pt=10.0, width_pt=220.0, height_pt=80.0)
    )

    workflow.preview()
    unchanged_request = workflow.build_signing_request()
    assert unchanged_request.signing_time is not None

    workflow.update_signature_rect(left_pt=12.0)
    changed_request = workflow.build_signing_request()
    assert changed_request.signing_time is None


def test_workflow_preview_uses_certificate_values_when_pkcs12_is_readable(tmp_path: Path) -> None:
    cert_path = tmp_path / "cert.p12"
    _write_test_pkcs12(cert_path, passphrase="secret")
    workflow = _workflow(tmp_path)
    workflow.set_signature_appearance(
        SignatureAppearance(
            common_name=SignatureFieldBinding(source=SignatureFieldSource.DERIVED),
            email=SignatureFieldBinding(source=SignatureFieldSource.DERIVED),
            title=SignatureFieldBinding(source=SignatureFieldSource.DERIVED),
            company=SignatureFieldBinding(source=SignatureFieldSource.DERIVED),
            location=SignatureFieldBinding(source=SignatureFieldSource.DERIVED),
        )
    )
    workflow.set_signature_rect(
        SignatureRect(
            page_index=0,
            left_pt=24.0,
            bottom_pt=18.0,
            width_pt=220.0,
            height_pt=80.0,
        )
    )

    preview = workflow.preview()

    assert preview.fields[0].text
    assert "Alice Example" in preview.fields[0].text
    assert "Board Secretary" in preview.fields[0].text
    assert preview.fields[1].text == "Alice Example"
    assert preview.fields[2].text == "alice@example.com"
    assert preview.fields[3].text == "Board Secretary"
    assert preview.fields[4].text == "FoliaSeal"
    assert preview.fields[6].visible is False
    assert preview.fields[7].text == "Wytheville, Virginia, US"


class FakeCertificatePreviewReader:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def read_preview_values(
        self,
        certificate_path: str,
        passphrase: str,
    ) -> CertificatePreviewValues:
        self.calls.append((certificate_path, passphrase))
        return CertificatePreviewValues(
            available=True,
            values={
                SignatureFieldKey.COMMON_NAME: "Injected Signer",
                SignatureFieldKey.EMAIL: "injected@example.com",
            },
        )


def test_workflow_uses_injected_certificate_preview_reader(tmp_path: Path) -> None:
    reader = FakeCertificatePreviewReader()
    workflow = SigningDraftWorkflow(
        input_pdf_path=str(tmp_path / "input.pdf"),
        output_pdf_path=str(tmp_path / "output.pdf"),
        certificate_path=str(tmp_path / "missing-cert.p12"),
        passphrase="secret",
        tsa_url="https://tsa.example.com",
        certificate_preview_reader=reader,
    )
    workflow.set_signature_appearance(
        SignatureAppearance(
            common_name=SignatureFieldBinding(source=SignatureFieldSource.DERIVED),
            email=SignatureFieldBinding(source=SignatureFieldSource.DERIVED),
            signing_time=SignatureFieldBinding(source=SignatureFieldSource.DERIVED),
        )
    )
    workflow.set_signature_rect(
        SignatureRect(
            page_index=0,
            left_pt=24.0,
            bottom_pt=18.0,
            width_pt=220.0,
            height_pt=80.0,
        )
    )

    preview = workflow.preview()

    assert reader.calls == [(str(tmp_path / "missing-cert.p12"), "secret")]
    assert preview.fields[1].text == "Injected Signer"
    assert preview.fields[2].text == "injected@example.com"


def test_workflow_applies_resolved_certificate_configuration(tmp_path: Path) -> None:
    reader = FakeCertificatePreviewReader()
    workflow = SigningDraftWorkflow(
        input_pdf_path=str(tmp_path / "input.pdf"),
        output_pdf_path=str(tmp_path / "output.pdf"),
        certificate_path=str(tmp_path / "old-cert.p12"),
        passphrase="old-secret",
        tsa_url="https://tsa.example.com",
        certificate_preview_reader=reader,
    )
    workflow.set_signature_appearance(
        SignatureAppearance(
            common_name=SignatureFieldBinding(source=SignatureFieldSource.DERIVED),
        )
    )
    workflow.set_signature_rect(
        SignatureRect(
            page_index=0,
            left_pt=24.0,
            bottom_pt=18.0,
            width_pt=220.0,
            height_pt=80.0,
        )
    )
    workflow.preview()
    assert reader.calls == [(str(tmp_path / "old-cert.p12"), "old-secret")]

    workflow.apply_certificate_configuration(
        build_certificate_configuration(
            certificate_configuration_id="cert-config-board",
        ),
        SigningMaterial(
            certificate_path=str(tmp_path / "managed" / "board.p12"),
            passphrase="typed-secret",
            certificate_alias="board-cert",
        ),
    )
    request = workflow.build_signing_request()
    workflow.preview()

    assert workflow.selected_certificate_configuration_id == "cert-config-board"
    assert request.certificate_path == str(tmp_path / "managed" / "board.p12")
    assert request.passphrase == "typed-secret"
    assert request.certificate_alias == "board-cert"
    assert reader.calls[-1] == (str(tmp_path / "managed" / "board.p12"), "typed-secret")


def test_workflow_blocks_compact_rectangles_that_backend_will_reject(
    tmp_path: Path,
) -> None:
    cert_path = tmp_path / "cert.p12"
    _write_test_pkcs12(cert_path, passphrase="secret")
    workflow = _workflow(tmp_path)
    workflow.set_signature_appearance(_appearance())
    workflow.set_signature_rect(
        SignatureRect(
            page_index=0,
            left_pt=35.84,
            bottom_pt=428.48,
            width_pt=261.63,
            height_pt=20.99,
        )
    )

    preview = workflow.preview()

    assert preview.can_submit is False
    assert any(issue.code.startswith("visible_signature_layout") for issue in preview.issues)
    with pytest.raises(SigningDraftValidationError):
        workflow.build_signing_request()


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


def test_workflow_can_capture_and_apply_signature_setup(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    appearance = _appearance()
    placement_defaults = SignaturePlacementDefaults(
        width_pt=180.0,
        height_pt=72.0,
    )
    workflow.set_signature_appearance(appearance)
    workflow.signature_placement_defaults = placement_defaults
    workflow.set_placement_context(
        SignaturePlacementContext(
            page_index=0,
            page_box=PageBox(left=0, bottom=0, right=612, top=792),
            rotation=0,
        )
    )
    workflow.selected_certificate_configuration_id = "cert-config-default"

    captured = workflow.capture_current_signature_setup("Team Standard")

    assert isinstance(captured, ResolvedSignaturePreset)
    assert captured.name == "Team Standard"
    assert captured.appearance == appearance
    assert captured.placement_defaults == placement_defaults
    assert captured.preset.appearance_profile_id == "appearance-team-standard"
    assert captured.preset.placement_profile_id == "placement-team-standard"
    assert captured.preset.certificate_configuration_id == "cert-config-default"

    workflow.clear_signature_appearance()
    workflow.signature_placement_defaults = None
    workflow.selected_certificate_configuration_id = "cert-config-old"
    workflow.apply_resolved_signature_preset(captured)

    assert workflow.current_signature_appearance == appearance
    assert workflow.signature_placement_defaults == placement_defaults
    assert workflow.selected_signature_preset_id == "preset-team-standard"
    assert workflow.selected_certificate_configuration_id == "cert-config-default"
    assert workflow.selected_appearance_profile_id == "appearance-team-standard"
    assert workflow.selected_placement_profile_id == "placement-team-standard"


def test_workflow_preserves_certificate_selection_for_partial_preset(
    tmp_path: Path,
) -> None:
    workflow = _workflow(tmp_path)
    workflow.selected_certificate_configuration_id = "cert-config-current"
    preset = ResolvedSignaturePreset.from_parts(
        name="Visual Only",
        appearance=_appearance(),
        placement_defaults=SignaturePlacementDefaults(
            width_pt=180.0,
            height_pt=72.0,
        ),
        source_page=DEFAULT_PLACEMENT_SOURCE_PAGE,
    )

    workflow.apply_resolved_signature_preset(preset)

    assert workflow.selected_certificate_configuration_id == "cert-config-current"


def test_workflow_apply_signature_preset_values_updates_ids_and_preserves_certificate(
    tmp_path: Path,
) -> None:
    workflow = _workflow(tmp_path)
    appearance = _appearance()
    placement_defaults = SignaturePlacementDefaults(
        width_pt=180.0,
        height_pt=72.0,
    )
    workflow.selected_certificate_configuration_id = "cert-config-current"

    workflow.apply_signature_preset_values(
        appearance=appearance,
        placement_defaults=placement_defaults,
        signature_preset_id="preset-team-standard",
        appearance_profile_id="appearance-team-standard",
        placement_profile_id="placement-team-standard",
        certificate_configuration_id=None,
    )

    assert workflow.current_signature_appearance == appearance
    assert workflow.signature_placement_defaults == placement_defaults
    assert workflow.selected_signature_preset_id == "preset-team-standard"
    assert workflow.selected_certificate_configuration_id == "cert-config-current"
    assert workflow.selected_appearance_profile_id == "appearance-team-standard"
    assert workflow.selected_placement_profile_id == "placement-team-standard"


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
    workflow.set_placement_context(
        SignaturePlacementContext(
            page_index=0,
            page_box=PageBox(left=0, bottom=0, right=612, top=792),
            rotation=0,
        )
    )

    captured = workflow.capture_current_signature_setup("Compact")

    assert captured.name == "Compact"
    assert captured.placement_defaults == SignaturePlacementDefaults(
        width_pt=160.0,
        height_pt=64.0,
    )


def test_workflow_allows_empty_signer_label_prefix_and_keeps_preview_clean(
    tmp_path: Path,
) -> None:
    workflow = _workflow(tmp_path)
    workflow.set_signature_appearance(
        SignatureAppearance(
            signer_label_prefix="",
            common_name=SignatureFieldBinding(
                source=SignatureFieldSource.DERIVED,
                show_in_visible_appearance=True,
            ),
            email=SignatureFieldBinding(
                source=SignatureFieldSource.DERIVED,
                show_in_visible_appearance=True,
            ),
            signing_time=SignatureFieldBinding(
                source=SignatureFieldSource.DERIVED,
                show_in_visible_appearance=True,
            ),
        )
    )
    workflow.set_signature_rect(
        SignatureRect(
            page_index=0,
            left_pt=24.0,
            bottom_pt=18.0,
            width_pt=220.0,
            height_pt=80.0,
        )
    )

    preview = workflow.preview()

    assert preview.signer_label_prefix == ""
    assert preview.title == ""
    assert preview.can_submit is True


def test_workflow_dirty_projection_protects_authored_values_but_not_preset_selection(
    tmp_path: Path,
) -> None:
    workflow = _workflow(tmp_path)

    assert workflow.has_unsaved_changes is False
    workflow.selected_signature_preset_id = "preset-team-standard"
    assert workflow.has_unsaved_changes is False

    workflow.set_signature_rect(
        SignatureRect(
            page_index=0,
            left_pt=12.0,
            bottom_pt=18.0,
            width_pt=160.0,
            height_pt=64.0,
        )
    )
    assert workflow.has_unsaved_changes is True

    workflow.mark_clean()
    assert workflow.has_unsaved_changes is False

    workflow.confirm_output_pdf_path(str(tmp_path / "confirmed.pdf"))
    assert workflow.has_unsaved_changes is True


def test_workflow_discard_clears_session_secret_and_resets_dirty_projection(
    tmp_path: Path,
) -> None:
    workflow = _workflow(tmp_path)
    workflow.set_signature_appearance(_appearance())
    assert workflow.has_unsaved_changes is True

    workflow.discard_draft()

    assert workflow.passphrase == ""
    assert workflow.has_unsaved_changes is False
