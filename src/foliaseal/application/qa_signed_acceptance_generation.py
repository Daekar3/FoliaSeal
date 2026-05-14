"""Generate local signed-acceptance fixture assets from tracked code."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID
from PIL import Image
from pyhanko.pdf_utils import generic
from pyhanko.pdf_utils.writer import PageObject, PdfFileWriter

from foliaseal.application.qa_preview_stress_fixtures import (
    STRESS_VISIBLE_APPEARANCE_PROFILE,
)
from foliaseal.application.qa_signed_acceptance_assets import (
    SIGNED_ACCEPTANCE_FIXTURE_PDF,
    SIGNED_ACCEPTANCE_IDENTITY_P12,
    SIGNED_ACCEPTANCE_SCENARIO_MANIFEST,
    SIGNED_FIT_REJECTION_SCENARIO_MANIFEST,
    SIGNED_PREVIEW_PARITY_SCENARIO_MANIFEST,
)

SIGNED_ACCEPTANCE_STAMP_IMAGE = (
    "artifacts/generated_acceptance_assets/signed_acceptance_stamp.png"
)
SIGNED_ACCEPTANCE_IDENTITY_PASSPHRASE = b"secret"


@dataclass(frozen=True)
class GeneratedSignedAcceptanceAssets:
    """Paths written by the signed acceptance asset generator."""

    fixture_pdf: Path
    identity_p12: Path
    stamp_image: Path
    signed_acceptance_manifest: Path
    signed_preview_parity_manifest: Path
    signed_fit_rejection_manifest: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "fixture_pdf": self.fixture_pdf,
            "identity_p12": self.identity_p12,
            "stamp_image": self.stamp_image,
            "signed_acceptance_manifest": self.signed_acceptance_manifest,
            "signed_preview_parity_manifest": self.signed_preview_parity_manifest,
            "signed_fit_rejection_manifest": self.signed_fit_rejection_manifest,
        }


def _artifact_path(root: Path, relative_path: str) -> Path:
    return root / relative_path


def _signature_rect(
    *,
    left_pt: float,
    bottom_pt: float,
    width_pt: float,
    height_pt: float,
) -> dict[str, float | int]:
    return {
        "page_index": 0,
        "left_pt": left_pt,
        "bottom_pt": bottom_pt,
        "width_pt": width_pt,
        "height_pt": height_pt,
    }


def _appearance(
    *,
    layout_template: str,
    stamp_position: str,
    image_stamp_path: str | None,
    visible_fields: list[str],
    signer_label_prefix: str = "Digitally signed by",
    show_field_names: bool = False,
    font_size_pt: float = 8.5,
    border_width_pt: float = 1.0,
) -> dict[str, Any]:
    return {
        "fixture_profile": STRESS_VISIBLE_APPEARANCE_PROFILE,
        "layout_template": layout_template,
        "stamp_position": stamp_position,
        "image_stamp_path": image_stamp_path,
        "visible_fields": visible_fields,
        "signer_label_prefix": signer_label_prefix,
        "show_field_names": show_field_names,
        "text_style": {
            "font_size_pt": font_size_pt,
            "font_color_hex": "#1F2933",
            "bold": False,
            "italic": False,
        },
        "box_style": {
            "border_width_pt": border_width_pt,
            "border_color_hex": "#2F4F6F",
            "background_color_hex": "#FFFFFF",
        },
    }


def _scenario(
    name: str,
    *,
    layout_template: str,
    stamp_position: str,
    image_stamp_path: str | None,
    visible_fields: list[str],
    signature_rect: dict[str, float | int],
    expected_outcome: str = "success",
    signer_label_prefix: str = "Digitally signed by",
    show_field_names: bool = False,
    font_size_pt: float = 8.5,
    border_width_pt: float = 1.0,
    timestamp_required: bool = False,
) -> dict[str, Any]:
    return {
        "name": name,
        "expected_outcome": expected_outcome,
        "timestamp_required": timestamp_required,
        "signature_rect": signature_rect,
        "appearance_overrides": _appearance(
            layout_template=layout_template,
            stamp_position=stamp_position,
            image_stamp_path=image_stamp_path,
            visible_fields=visible_fields,
            signer_label_prefix=signer_label_prefix,
            show_field_names=show_field_names,
            font_size_pt=font_size_pt,
            border_width_pt=border_width_pt,
        ),
    }


def _expectations(
    *,
    scenarios: list[dict[str, Any]],
    minimum_successful_signing_run_count: int,
    expected_intentional_rejection_count: int,
) -> dict[str, int | bool]:
    return {
        "scenario_count": len(scenarios),
        "minimum_successful_signing_run_count": minimum_successful_signing_run_count,
        "expected_intentional_rejection_count": expected_intentional_rejection_count,
        "require_zero_cryptographic_validation_failures": True,
        "require_zero_preview_output_comparison_failures": True,
        "require_zero_annotation_rect_mismatches": True,
    }


def _manifest(
    *,
    fixture_role: str,
    scenarios: list[dict[str, Any]],
    minimum_successful_signing_run_count: int,
    expected_intentional_rejection_count: int,
) -> dict[str, Any]:
    return {
        "fixture_profile": STRESS_VISIBLE_APPEARANCE_PROFILE,
        "fixture_role": fixture_role,
        "timestamping_mode": "dummy",
        "acceptance_expectations": _expectations(
            scenarios=scenarios,
            minimum_successful_signing_run_count=minimum_successful_signing_run_count,
            expected_intentional_rejection_count=expected_intentional_rejection_count,
        ),
        "scenarios": scenarios,
    }


def build_signed_acceptance_manifest(stamp_image_path: str) -> dict[str, Any]:
    scenarios = [
        _scenario(
            "single_line_top_label_success",
            layout_template="single_line",
            stamp_position="top",
            image_stamp_path=None,
            visible_fields=["common_name", "signing_time"],
            signature_rect=_signature_rect(
                left_pt=84, bottom_pt=612, width_pt=420, height_pt=82
            ),
            timestamp_required=True,
        ),
        _scenario(
            "single_line_bottom_label_success",
            layout_template="single_line",
            stamp_position="bottom",
            image_stamp_path=None,
            visible_fields=["common_name", "company", "signing_time"],
            signature_rect=_signature_rect(left_pt=84, bottom_pt=96, width_pt=420, height_pt=86),
        ),
        _scenario(
            "single_line_left_label_reject",
            layout_template="single_line",
            stamp_position="left",
            image_stamp_path=stamp_image_path,
            visible_fields=["common_name", "email", "title", "company", "signing_time"],
            signature_rect=_signature_rect(left_pt=48, bottom_pt=330, width_pt=190, height_pt=54),
            expected_outcome="validation_rejection",
            font_size_pt=10,
        ),
        _scenario(
            "multi_line_top_medium_success",
            layout_template="multi_line",
            stamp_position="top",
            image_stamp_path=stamp_image_path,
            visible_fields=["common_name", "title", "company", "signing_time"],
            signature_rect=_signature_rect(left_pt=80, bottom_pt=484, width_pt=450, height_pt=150),
        ),
        _scenario(
            "multi_line_bottom_medium_success",
            layout_template="multi_line",
            stamp_position="bottom",
            image_stamp_path=stamp_image_path,
            visible_fields=["common_name", "title", "company", "signing_time"],
            signature_rect=_signature_rect(left_pt=80, bottom_pt=214, width_pt=450, height_pt=150),
        ),
        _scenario(
            "multi_line_right_medium_reject",
            layout_template="multi_line",
            stamp_position="right",
            image_stamp_path=stamp_image_path,
            visible_fields=["common_name", "email", "title", "company", "signing_time"],
            signature_rect=_signature_rect(left_pt=340, bottom_pt=320, width_pt=190, height_pt=72),
            expected_outcome="validation_rejection",
            font_size_pt=10,
        ),
        _scenario(
            "wrapped_block_left_plain_success",
            layout_template="wrapped_block",
            stamp_position="left",
            image_stamp_path=stamp_image_path,
            visible_fields=["common_name", "email", "signing_time"],
            signature_rect=_signature_rect(left_pt=70, bottom_pt=360, width_pt=470, height_pt=150),
            signer_label_prefix="",
        ),
        _scenario(
            "wrapped_block_right_plain_reject",
            layout_template="wrapped_block",
            stamp_position="right",
            image_stamp_path=stamp_image_path,
            visible_fields=[
                "common_name",
                "email",
                "title",
                "company",
                "signing_time",
                "location",
                "reason",
            ],
            signature_rect=_signature_rect(left_pt=330, bottom_pt=230, width_pt=190, height_pt=74),
            expected_outcome="validation_rejection",
            signer_label_prefix="",
            font_size_pt=10,
        ),
        _scenario(
            "wrapped_block_top_plain_success",
            layout_template="wrapped_block",
            stamp_position="top",
            image_stamp_path=stamp_image_path,
            visible_fields=["common_name", "email", "signing_time"],
            signature_rect=_signature_rect(left_pt=72, bottom_pt=190, width_pt=470, height_pt=154),
            signer_label_prefix="",
        ),
        _scenario(
            "wrapped_block_bottom_dense_success",
            layout_template="wrapped_block",
            stamp_position="bottom",
            image_stamp_path=stamp_image_path,
            visible_fields=["common_name", "title", "company", "signing_time"],
            signature_rect=_signature_rect(left_pt=58, bottom_pt=500, width_pt=500, height_pt=210),
            show_field_names=True,
            font_size_pt=7.5,
        ),
    ]
    return _manifest(
        fixture_role="signed_acceptance",
        scenarios=scenarios,
        minimum_successful_signing_run_count=7,
        expected_intentional_rejection_count=3,
    )


def build_signed_preview_parity_manifest(stamp_image_path: str) -> dict[str, Any]:
    scenarios = [
        _scenario(
            "single_line_top_no_stamp_sparse_large",
            layout_template="single_line",
            stamp_position="top",
            image_stamp_path=None,
            visible_fields=["common_name", "signing_time"],
            signature_rect=_signature_rect(left_pt=72, bottom_pt=600, width_pt=470, height_pt=92),
        ),
        _scenario(
            "single_line_bottom_no_stamp_sparse_relaxed",
            layout_template="single_line",
            stamp_position="bottom",
            image_stamp_path=None,
            visible_fields=["common_name", "signing_time"],
            signature_rect=_signature_rect(left_pt=72, bottom_pt=86, width_pt=440, height_pt=88),
        ),
        _scenario(
            "single_line_left_stamp_sparse_relaxed",
            layout_template="single_line",
            stamp_position="left",
            image_stamp_path=stamp_image_path,
            visible_fields=["common_name", "signing_time"],
            signature_rect=_signature_rect(left_pt=64, bottom_pt=455, width_pt=470, height_pt=104),
        ),
        _scenario(
            "single_line_right_no_stamp_sparse_relaxed",
            layout_template="single_line",
            stamp_position="right",
            image_stamp_path=None,
            visible_fields=["common_name", "signing_time"],
            signature_rect=_signature_rect(left_pt=78, bottom_pt=335, width_pt=440, height_pt=90),
        ),
        _scenario(
            "single_line_top_stamp_sparse_relaxed",
            layout_template="single_line",
            stamp_position="top",
            image_stamp_path=stamp_image_path,
            visible_fields=["common_name", "signing_time"],
            signature_rect=_signature_rect(left_pt=76, bottom_pt=500, width_pt=460, height_pt=118),
        ),
        _scenario(
            "single_line_bottom_stamp_sparse_relaxed",
            layout_template="single_line",
            stamp_position="bottom",
            image_stamp_path=stamp_image_path,
            visible_fields=["common_name", "signing_time"],
            signature_rect=_signature_rect(left_pt=76, bottom_pt=210, width_pt=460, height_pt=118),
        ),
        _scenario(
            "single_line_left_no_stamp_sparse_relaxed",
            layout_template="single_line",
            stamp_position="left",
            image_stamp_path=None,
            visible_fields=["common_name", "signing_time"],
            signature_rect=_signature_rect(left_pt=86, bottom_pt=280, width_pt=430, height_pt=86),
        ),
        _scenario(
            "single_line_right_stamp_sparse_relaxed",
            layout_template="single_line",
            stamp_position="right",
            image_stamp_path=stamp_image_path,
            visible_fields=["common_name", "signing_time"],
            signature_rect=_signature_rect(left_pt=72, bottom_pt=150, width_pt=470, height_pt=104),
        ),
        _scenario(
            "multi_line_bottom_sparse_large",
            layout_template="multi_line",
            stamp_position="bottom",
            image_stamp_path=stamp_image_path,
            visible_fields=["common_name", "email", "signing_time"],
            signature_rect=_signature_rect(left_pt=70, bottom_pt=84, width_pt=470, height_pt=166),
        ),
        _scenario(
            "multi_line_top_medium_relaxed",
            layout_template="multi_line",
            stamp_position="top",
            image_stamp_path=stamp_image_path,
            visible_fields=["common_name", "title", "company", "signing_time"],
            signature_rect=_signature_rect(left_pt=70, bottom_pt=580, width_pt=470, height_pt=166),
        ),
        _scenario(
            "multi_line_bottom_medium_relaxed",
            layout_template="multi_line",
            stamp_position="bottom",
            image_stamp_path=stamp_image_path,
            visible_fields=["common_name", "title", "company", "signing_time"],
            signature_rect=_signature_rect(left_pt=70, bottom_pt=275, width_pt=470, height_pt=166),
        ),
        _scenario(
            "multi_line_right_medium_large",
            layout_template="multi_line",
            stamp_position="right",
            image_stamp_path=stamp_image_path,
            visible_fields=["common_name", "title", "company", "signing_time"],
            signature_rect=_signature_rect(left_pt=54, bottom_pt=390, width_pt=500, height_pt=150),
        ),
        _scenario(
            "multi_line_left_sparse_relaxed",
            layout_template="multi_line",
            stamp_position="left",
            image_stamp_path=stamp_image_path,
            visible_fields=["common_name", "email", "signing_time"],
            signature_rect=_signature_rect(left_pt=62, bottom_pt=255, width_pt=480, height_pt=146),
        ),
        _scenario(
            "multi_line_top_sparse_large",
            layout_template="multi_line",
            stamp_position="top",
            image_stamp_path=None,
            visible_fields=["common_name", "email", "signing_time"],
            signature_rect=_signature_rect(left_pt=74, bottom_pt=430, width_pt=460, height_pt=138),
        ),
        _scenario(
            "wrapped_block_left_sparse_large",
            layout_template="wrapped_block",
            stamp_position="left",
            image_stamp_path=stamp_image_path,
            visible_fields=["common_name", "email", "signing_time"],
            signature_rect=_signature_rect(left_pt=62, bottom_pt=470, width_pt=500, height_pt=152),
        ),
        _scenario(
            "wrapped_block_top_sparse_relaxed",
            layout_template="wrapped_block",
            stamp_position="top",
            image_stamp_path=stamp_image_path,
            visible_fields=["common_name", "email", "signing_time"],
            signature_rect=_signature_rect(left_pt=70, bottom_pt=300, width_pt=470, height_pt=154),
        ),
        _scenario(
            "wrapped_block_right_medium_relaxed",
            layout_template="wrapped_block",
            stamp_position="right",
            image_stamp_path=stamp_image_path,
            visible_fields=["common_name", "title", "company", "signing_time", "location"],
            signature_rect=_signature_rect(left_pt=54, bottom_pt=142, width_pt=500, height_pt=160),
        ),
        _scenario(
            "wrapped_block_bottom_sparse_relaxed",
            layout_template="wrapped_block",
            stamp_position="bottom",
            image_stamp_path=None,
            visible_fields=["common_name", "email", "signing_time"],
            signature_rect=_signature_rect(left_pt=72, bottom_pt=86, width_pt=468, height_pt=146),
        ),
    ]
    return _manifest(
        fixture_role="signed_preview_parity",
        scenarios=scenarios,
        minimum_successful_signing_run_count=len(scenarios),
        expected_intentional_rejection_count=0,
    )


def build_signed_fit_rejection_manifest(stamp_image_path: str) -> dict[str, Any]:
    scenarios = [
        _scenario(
            "single_line_left_stamp_sparse_large",
            layout_template="single_line",
            stamp_position="left",
            image_stamp_path=stamp_image_path,
            visible_fields=["common_name", "email", "signing_time"],
            signature_rect=_signature_rect(left_pt=48, bottom_pt=410, width_pt=170, height_pt=48),
            expected_outcome="validation_rejection",
            font_size_pt=10,
        ),
        _scenario(
            "single_line_right_stamp_sparse_large",
            layout_template="single_line",
            stamp_position="right",
            image_stamp_path=stamp_image_path,
            visible_fields=["common_name", "email", "signing_time"],
            signature_rect=_signature_rect(left_pt=390, bottom_pt=335, width_pt=170, height_pt=48),
            expected_outcome="validation_rejection",
            font_size_pt=10,
        ),
        _scenario(
            "wrapped_block_top_dense_large",
            layout_template="wrapped_block",
            stamp_position="top",
            image_stamp_path=stamp_image_path,
            visible_fields=[
                "common_name",
                "email",
                "title",
                "company",
                "signing_time",
                "location",
                "reason",
            ],
            signature_rect=_signature_rect(left_pt=86, bottom_pt=252, width_pt=190, height_pt=62),
            expected_outcome="validation_rejection",
            show_field_names=True,
            font_size_pt=10,
        ),
    ]
    return _manifest(
        fixture_role="signed_fit_rejection",
        scenarios=scenarios,
        minimum_successful_signing_run_count=0,
        expected_intentional_rejection_count=len(scenarios),
    )


def _write_pdf(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = PdfFileWriter()
    empty_stream = writer.add_object(generic.StreamObject(stream_data=b""))
    writer.insert_page(PageObject(contents=empty_stream, media_box=(0, 0, 612, 792)))
    with path.open("wb") as handle:
        writer.write(handle)


def _write_identity(path: Path, *, passphrase: bytes) -> x509.Certificate:
    path.parent.mkdir(parents=True, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, "FoliaSeal Acceptance Identity"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "FoliaSeal"),
            x509.NameAttribute(NameOID.TITLE, "Acceptance Signer"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "QA"),
            x509.NameAttribute(NameOID.EMAIL_ADDRESS, "acceptance@example.invalid"),
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
    payload = pkcs12.serialize_key_and_certificates(
        name=b"FoliaSeal Acceptance Identity",
        key=key,
        cert=cert,
        cas=None,
        encryption_algorithm=serialization.BestAvailableEncryption(passphrase),
    )
    path.write_bytes(payload)
    return cert


def _write_stamp_image(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGBA", (640, 160), color=(255, 255, 255, 0))
    for x in range(42, 598):
        for y in range(34, 126):
            image.putpixel((x, y), (47, 79, 111, 170))
    image.save(path, format="PNG")


def _write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def generate_signed_acceptance_assets(
    *,
    root: Path = Path("."),
    passphrase: bytes = SIGNED_ACCEPTANCE_IDENTITY_PASSPHRASE,
) -> GeneratedSignedAcceptanceAssets:
    root = Path(root)
    fixture_pdf = _artifact_path(root, SIGNED_ACCEPTANCE_FIXTURE_PDF)
    identity_p12 = _artifact_path(root, SIGNED_ACCEPTANCE_IDENTITY_P12)
    stamp_image = _artifact_path(root, SIGNED_ACCEPTANCE_STAMP_IMAGE)
    acceptance_manifest = _artifact_path(root, SIGNED_ACCEPTANCE_SCENARIO_MANIFEST)
    parity_manifest = _artifact_path(root, SIGNED_PREVIEW_PARITY_SCENARIO_MANIFEST)
    rejection_manifest = _artifact_path(root, SIGNED_FIT_REJECTION_SCENARIO_MANIFEST)
    manifest_stamp_path = str(Path(SIGNED_ACCEPTANCE_STAMP_IMAGE))

    _write_pdf(fixture_pdf)
    _write_identity(identity_p12, passphrase=passphrase)
    _write_stamp_image(stamp_image)
    _write_manifest(acceptance_manifest, build_signed_acceptance_manifest(manifest_stamp_path))
    _write_manifest(parity_manifest, build_signed_preview_parity_manifest(manifest_stamp_path))
    _write_manifest(rejection_manifest, build_signed_fit_rejection_manifest(manifest_stamp_path))

    return GeneratedSignedAcceptanceAssets(
        fixture_pdf=fixture_pdf,
        identity_p12=identity_p12,
        stamp_image=stamp_image,
        signed_acceptance_manifest=acceptance_manifest,
        signed_preview_parity_manifest=parity_manifest,
        signed_fit_rejection_manifest=rejection_manifest,
    )
