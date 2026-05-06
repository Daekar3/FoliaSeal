from __future__ import annotations

from pathlib import Path

import pytest
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign.validation.pdf_embedded import MDPPerm

from foliaseal.application.phase3_signing_backend import build_phase3_signing_executor
from foliaseal.domain.errors import FailureCode
from foliaseal.domain.models import SigningRequest
from foliaseal.infra.certification import (
    PyHankoCertificationInspector,
    inspect_pdf_certification_reader,
)
from tests.support.certification_fixtures import (
    sign_pdf_for_certification,
    write_pdf_with_version,
)
from tests.support.phase3_builders import (
    build_signature_appearance,
    build_signature_rect,
)

BASE_ACCEPTANCE_PDF = Path("artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf")
BASE_ACCEPTANCE_IDENTITY = Path(
    "artifacts/generated_acceptance_assets/signed_acceptance_identity.p12"
)
pytestmark = pytest.mark.skipif(
    not BASE_ACCEPTANCE_PDF.exists() or not BASE_ACCEPTANCE_IDENTITY.exists(),
    reason="local QA artifact fixtures are absent because artifacts/ is ignored",
)


def _build_request(input_pdf_path: Path, output_pdf_path: Path) -> SigningRequest:
    return SigningRequest(
        input_pdf_path=str(input_pdf_path),
        output_pdf_path=str(output_pdf_path),
        certificate_path=str(BASE_ACCEPTANCE_IDENTITY),
        passphrase="secret",
        tsa_url="https://tsa.example.com",
        timestamp_required=False,
        signature_rect=build_signature_rect(
            page_index=0,
            width_pt=620.0,
            height_pt=180.0,
        ),
        signature_appearance=build_signature_appearance(
            image_stamp_path=None,
            show_field_names=True,
            signer_label_prefix="",
        ),
    )


def _make_versioned_input_pdf(tmp_path: Path, version: str) -> Path:
    return write_pdf_with_version(
        BASE_ACCEPTANCE_PDF,
        tmp_path / f"input_{version}.pdf",
        version,
    )


def _make_signed_input_pdf(
    tmp_path: Path,
    *,
    version: str,
    certify: bool,
    docmdp_permissions: MDPPerm = MDPPerm.FILL_FORMS,
) -> Path:
    input_pdf = _make_versioned_input_pdf(tmp_path, version)
    output_pdf = tmp_path / (
        f"{'certified' if certify else 'approved'}_{version}.pdf"
    )
    return sign_pdf_for_certification(
        input_pdf,
        output_pdf,
        certificate_path=BASE_ACCEPTANCE_IDENTITY,
        passphrase="secret",
        certify=certify,
        docmdp_permissions=docmdp_permissions,
        field_name="CertificationSig" if certify else "ApprovalSig",
    )


@pytest.mark.parametrize(
    "version,input_state,docmdp_permissions,expected_restricted,expected_permission",
    [
        ("1.4", "unsigned", MDPPerm.FILL_FORMS, False, None),
        ("1.7", "approval_signed", MDPPerm.FILL_FORMS, False, None),
        ("2.0", "certified_fill_forms", MDPPerm.FILL_FORMS, False, "fill_forms"),
        ("1.4", "certified_no_changes", MDPPerm.NO_CHANGES, True, "no_changes"),
        ("1.7", "certified_no_changes", MDPPerm.NO_CHANGES, True, "no_changes"),
        ("2.0", "unsigned", MDPPerm.FILL_FORMS, False, None),
    ],
)
def test_certification_policy_matrix_blocks_only_no_changes(
    tmp_path: Path,
    version: str,
    input_state: str,
    docmdp_permissions: MDPPerm,
    expected_restricted: bool,
    expected_permission: str | None,
) -> None:
    if input_state == "unsigned":
        input_pdf = _make_versioned_input_pdf(tmp_path, version)
    elif input_state == "approval_signed":
        input_pdf = _make_signed_input_pdf(
            tmp_path,
            version=version,
            certify=False,
        )
    elif input_state == "certified_fill_forms":
        input_pdf = _make_signed_input_pdf(
            tmp_path,
            version=version,
            certify=True,
            docmdp_permissions=docmdp_permissions,
        )
    elif input_state == "certified_no_changes":
        input_pdf = _make_signed_input_pdf(
            tmp_path,
            version=version,
            certify=True,
            docmdp_permissions=docmdp_permissions,
        )
    else:  # pragma: no cover - defensive guard for the matrix definition.
        raise AssertionError(f"Unknown input state: {input_state}")

    request = _build_request(input_pdf, tmp_path / f"output_{version}_{input_state}.pdf")
    executor = build_phase3_signing_executor()

    result = executor.execute(request)

    assert result.operation_type.value == "sign"
    assert result.revision_strategy.value == "incremental"
    assert result.docmdp_permission == expected_permission
    assert result.certification_restricted is expected_restricted
    if expected_restricted:
        assert result.success is False
        assert result.failure_code == FailureCode.PDF_CERTIFICATION_RESTRICTS_SIGNING
        assert "forbids signing" in result.message
        assert not Path(request.output_pdf_path).exists()
    else:
        assert result.success is True
        assert result.failure_code is None
        assert Path(request.output_pdf_path).exists()


@pytest.mark.parametrize(
    "version,certify,docmdp_permissions,expected_permission,expected_restricted",
    [
        ("1.4", False, MDPPerm.FILL_FORMS, None, False),
        ("1.7", True, MDPPerm.FILL_FORMS, "fill_forms", False),
        ("2.0", True, MDPPerm.NO_CHANGES, "no_changes", True),
    ],
)
def test_certification_inspector_reports_docmdp_state(
    tmp_path: Path,
    version: str,
    certify: bool,
    docmdp_permissions: MDPPerm,
    expected_permission: str | None,
    expected_restricted: bool,
) -> None:
    if certify:
        input_pdf = _make_signed_input_pdf(
            tmp_path,
            version=version,
            certify=True,
            docmdp_permissions=docmdp_permissions,
        )
    else:
        input_pdf = _make_versioned_input_pdf(tmp_path, version)

    inspector = PyHankoCertificationInspector()
    result = inspector.inspect(str(input_pdf))

    assert result.docmdp_permission == expected_permission
    assert result.certification_restricted is expected_restricted
    if expected_restricted:
        assert result.restriction_reason is not None


def test_certification_reader_reports_state_from_open_reader(tmp_path: Path) -> None:
    input_pdf = _make_signed_input_pdf(
        tmp_path,
        version="1.7",
        certify=True,
        docmdp_permissions=MDPPerm.NO_CHANGES,
    )

    with input_pdf.open("rb") as handle:
        reader = PdfFileReader(handle)
        result = inspect_pdf_certification_reader(reader)

    assert result.docmdp_permission == "no_changes"
    assert result.certification_restricted is True
