"""Phase 1 headless signing orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Protocol

from foliaseal.application.pdf_compatibility import (
    PdfCompatibilityError,
    PdfCompatibilityProfile,
)
from foliaseal.domain.errors import (
    CertificateLoadError,
    CertificateWrongPasswordError,
    FailureCode,
    TsaUnavailableError,
)
from foliaseal.domain.models import (
    SigningOutput,
    SigningRequest,
    SigningResult,
    VerificationSummary,
)


class PdfInspector(Protocol):
    """Reads lightweight metadata needed for policy checks."""

    def get_pdf_version(self, input_pdf_path: str) -> str:
        """Return input PDF version as a dotted string, e.g. '1.7'."""


class CertificateLoader(Protocol):
    """Validates and loads signing identity from PKCS#12."""

    def validate(self, certificate_path: str, passphrase: str) -> None:
        """Raise on invalid certificate material or credentials."""


class PdfSigner(Protocol):
    """Signs a PDF and returns output bytes + metadata."""

    def sign(self, request: SigningRequest) -> SigningOutput:
        """Perform the signing operation."""


class SignatureVerifier(Protocol):
    """Performs post-sign checks."""

    def verify(self, output_pdf_path: str) -> VerificationSummary:
        """Return structured verification summary."""


@dataclass
class SignPdfUseCase:
    """Coordinates phase 1 signing flow and maps failures to stable codes."""

    inspector: PdfInspector
    certificate_loader: CertificateLoader
    signer: PdfSigner
    verifier: SignatureVerifier
    compatibility_profile: PdfCompatibilityProfile = PdfCompatibilityProfile()

    def execute(self, request: SigningRequest) -> SigningResult:
        """Execute the headless signing pipeline."""
        try:
            if self._paths_conflict(request.input_pdf_path, request.output_pdf_path):
                return SigningResult(
                    success=False,
                    failure_code=FailureCode.OUTPUT_PATH_INVALID,
                    message="Output path must differ from input path.",
                )

            input_pdf_version = self.inspector.get_pdf_version(request.input_pdf_path)
            self.compatibility_profile.ensure_open_version_supported(input_pdf_version)
            self.certificate_loader.validate(request.certificate_path, request.passphrase)

            output = self.signer.sign(request)
            if request.timestamp_required and not output.timestamp_present:
                return SigningResult(
                    success=False,
                    failure_code=FailureCode.TIMESTAMP_REQUIRED_BUT_MISSING,
                    message="Timestamp is required but missing from signing output.",
                )

            self.compatibility_profile.ensure_output_version_policy(
                input_pdf_version=input_pdf_version,
                output_pdf_version=output.output_pdf_version,
            )

            self._write_atomically(request.output_pdf_path, output.output_bytes)
            verification = self.verifier.verify(request.output_pdf_path)
            if request.timestamp_required and not verification.timestamp_present:
                return SigningResult(
                    success=False,
                    failure_code=FailureCode.POST_VERIFY_FAILED,
                    message="Post-sign verification did not find expected timestamp token.",
                )

            standards_summary = self.compatibility_profile.build_standards_summary(
                input_pdf_version=input_pdf_version,
                output_pdf_version=output.output_pdf_version,
                signature_subfilter=output.signature_subfilter,
                timestamp_present=verification.timestamp_present,
            )
            return SigningResult(
                success=True,
                failure_code=None,
                message="Signing completed successfully.",
                output_pdf_version=output.output_pdf_version,
                signature_subfilter=output.signature_subfilter,
                timestamp_present=verification.timestamp_present,
                standards_summary=standards_summary,
            )
        except PdfCompatibilityError as exc:
            return SigningResult(
                success=False,
                failure_code=FailureCode.INPUT_PDF_INVALID,
                message=str(exc),
            )
        except FileNotFoundError as exc:
            return SigningResult(
                success=False,
                failure_code=FailureCode.INPUT_PDF_INVALID,
                message=str(exc),
            )
        except CertificateWrongPasswordError as exc:
            return SigningResult(
                success=False,
                failure_code=FailureCode.PKCS12_WRONG_PASSWORD,
                message=str(exc),
            )
        except CertificateLoadError as exc:
            return SigningResult(
                success=False,
                failure_code=FailureCode.PKCS12_LOAD_FAILED,
                message=str(exc),
            )
        except TsaUnavailableError as exc:
            return SigningResult(
                success=False,
                failure_code=FailureCode.TSA_UNREACHABLE,
                message=str(exc),
            )
        except PermissionError as exc:
            return SigningResult(
                success=False,
                failure_code=FailureCode.ATOMIC_WRITE_FAILED,
                message=str(exc),
            )
        except ValueError as exc:
            return SigningResult(
                success=False,
                failure_code=FailureCode.PDF_SIGNING_FAILED,
                message=str(exc),
            )
        except OSError as exc:
            return SigningResult(
                success=False,
                failure_code=FailureCode.ATOMIC_WRITE_FAILED,
                message=str(exc),
            )
        except Exception as exc:  # pragma: no cover - defensive mapping for stable contracts.
            return SigningResult(
                success=False,
                failure_code=FailureCode.UNEXPECTED_INTERNAL_ERROR,
                message=str(exc),
            )

    @staticmethod
    def _paths_conflict(input_pdf_path: str, output_pdf_path: str) -> bool:
        """Return whether two paths refer to the same intended file."""
        input_path = Path(input_pdf_path).expanduser().resolve(strict=False)
        output_path = Path(output_pdf_path).expanduser().resolve(strict=False)
        return input_path == output_path

    @staticmethod
    def _write_atomically(output_path: str, output_bytes: bytes) -> None:
        """Write to temp file then atomically replace target path."""
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temp_path: Path | None = None
        try:
            with NamedTemporaryFile(dir=destination.parent, delete=False) as temp_file:
                temp_file.write(output_bytes)
                temp_path = Path(temp_file.name)
            temp_path.replace(destination)
        finally:
            if temp_path and temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
