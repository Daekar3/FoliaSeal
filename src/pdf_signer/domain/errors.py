"""Domain-level error and failure code definitions."""

from __future__ import annotations

from enum import Enum


class FailureCode(str, Enum):  # noqa: UP042
    """Stable failure codes surfaced to UI/logging layers."""

    INPUT_PDF_INVALID = "input_pdf_invalid"
    OUTPUT_PATH_INVALID = "output_path_invalid"
    PKCS12_LOAD_FAILED = "pkcs12_load_failed"
    PKCS12_WRONG_PASSWORD = "pkcs12_wrong_password"
    SIGNATURE_RECT_INVALID = "signature_rect_invalid"
    PDF_CERTIFICATION_RESTRICTS_SIGNING = "pdf_certification_restricts_signing"
    PDF_SIGNING_FAILED = "pdf_signing_failed"
    TSA_UNREACHABLE = "tsa_unreachable"
    TIMESTAMP_REQUIRED_BUT_MISSING = "timestamp_required_but_missing"
    POST_VERIFY_FAILED = "post_verify_failed"
    ATOMIC_WRITE_FAILED = "atomic_write_failed"
    UNEXPECTED_INTERNAL_ERROR = "unexpected_internal_error"
