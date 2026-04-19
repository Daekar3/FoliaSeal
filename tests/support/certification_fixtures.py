"""Helpers for generating certification and approval-signing test PDFs."""

from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path

from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import fields
from pyhanko.sign.signers import PdfSignatureMetadata, PdfSigner, SimpleSigner
from pyhanko.sign.validation.pdf_embedded import MDPPerm

_PDF_VERSION_PATTERN = re.compile(br"%PDF-(\d+\.\d+)")


def write_pdf_with_version(
    source_path: Path,
    target_path: Path,
    version: str,
) -> Path:
    """Copy a PDF and rewrite its version header."""
    data = source_path.read_bytes()
    replacement = f"%PDF-{version}".encode("ascii")
    if _PDF_VERSION_PATTERN.search(data) is None:
        raise ValueError(f"Could not locate a PDF version header in {source_path}.")
    updated, count = _PDF_VERSION_PATTERN.subn(replacement, data, count=1)
    if count != 1:
        raise ValueError(f"Could not rewrite the PDF version header in {source_path}.")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(updated)
    return target_path


def sign_pdf_for_certification(
    source_path: Path,
    target_path: Path,
    *,
    certificate_path: Path,
    passphrase: str,
    certify: bool,
    docmdp_permissions: MDPPerm = MDPPerm.FILL_FORMS,
    field_name: str = "Signature1",
) -> Path:
    """Sign a PDF for test fixtures, optionally producing a certification signature."""
    signer = SimpleSigner.load_pkcs12(
        str(certificate_path),
        passphrase=passphrase.encode("utf-8"),
    )
    metadata = PdfSignatureMetadata(
        field_name=field_name,
        md_algorithm="sha256",
        certify=certify,
        docmdp_permissions=docmdp_permissions,
    )
    field_spec = fields.SigFieldSpec(
        sig_field_name=field_name,
        on_page=0,
        box=(10, 10, 110, 30),
    )

    with source_path.open("rb") as input_stream:
        writer = IncrementalPdfFileWriter(input_stream)
        output = BytesIO()
        signer_engine = PdfSigner(metadata, signer, new_field_spec=field_spec)
        signer_engine.sign_pdf(writer, output=output)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(output.getvalue())
    return target_path
