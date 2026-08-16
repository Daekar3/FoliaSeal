"""Phase 1 headless signing orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Protocol
from uuid import uuid4

from foliaseal.application.output_path_policy import paths_refer_to_same_file
from foliaseal.application.pdf_compatibility import (
    PdfCompatibilityError,
    PdfCompatibilityProfile,
)
from foliaseal.application.preview_render_boundary import PreviewRasterRenderer
from foliaseal.application.signing_transaction_recovery import (
    SigningRecoveryCandidate,
    SigningTransactionJournal,
    SigningTransactionRecord,
)
from foliaseal.domain.errors import (
    CertificateLoadError,
    CertificateWrongPasswordError,
    FailureCode,
    TimestampTrustMaterialError,
    TsaUnavailableError,
)
from foliaseal.domain.models import (
    DocumentOperationType,
    RevisionStrategy,
    SignatureAppearance,
    SignatureBoxStyle,
    SignatureFieldKey,
    SignatureFieldSource,
    SignatureImageProminence,
    SignatureLayoutTemplate,
    SignatureRect,
    SignatureStampPosition,
    SignatureTextStyle,
    SignatureTimezoneDisplayMode,
    SigningOutput,
    SigningRequest,
    SigningResult,
    TimestampTrustPolicy,
    VerificationSummary,
)
from foliaseal.infra.certification import (
    CertificationInspectionError,
    CertificationPolicyResult,
    PyHankoCertificationInspector,
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

    def sign(self, request: SigningBackendRequest) -> SigningOutput:
        """Perform the signing operation."""


class SignatureVerifier(Protocol):
    """Performs post-sign checks."""

    def verify(
        self,
        output_pdf_path: str,
        *,
        trust_policy: TimestampTrustPolicy | None = None,
    ) -> VerificationSummary:
        """Return structured verification summary."""


class CertificationInspector(Protocol):
    """Inspects PDFs for certification / DocMDP restrictions."""

    def inspect(self, input_pdf_path: str) -> CertificationPolicyResult:
        """Return the certification policy classification for the input PDF."""


@dataclass(frozen=True)
class SigningBackendFieldBinding:
    """Backend-facing representation of one visible signature field."""

    field_key: SignatureFieldKey
    source: SignatureFieldSource
    show_in_visible_appearance: bool
    override_text: str | None
    display_label: str | None


@dataclass(frozen=True)
class SigningBackendAppearance:
    """Backend-facing signature appearance payload."""

    signer_label_prefix: str
    layout_template: SignatureLayoutTemplate
    stamp_position: SignatureStampPosition
    timezone_display_mode: SignatureTimezoneDisplayMode
    show_field_names: bool
    datetime_format: str
    field_bindings: tuple[SigningBackendFieldBinding, ...]
    text_style: SignatureTextStyle
    box_style: SignatureBoxStyle
    image_stamp_path: str | None = None
    image_prominence: SignatureImageProminence | None = None
    preserve_image_alpha: bool = True

    @classmethod
    def from_signature_appearance(
        cls,
        appearance: SignatureAppearance,
    ) -> SigningBackendAppearance:
        """Map the normalized domain appearance into the backend payload."""
        return cls(
            signer_label_prefix=appearance.signer_label_prefix,
            layout_template=appearance.layout_template,
            stamp_position=appearance.stamp_position,
            timezone_display_mode=appearance.timezone_display_mode,
            show_field_names=appearance.show_field_names,
            datetime_format=appearance.datetime_format,
            field_bindings=tuple(
                SigningBackendFieldBinding(
                    field_key=field_key,
                    source=binding.source,
                    show_in_visible_appearance=binding.show_in_visible_appearance,
                    override_text=binding.override_text,
                    display_label=binding.display_label,
                )
                for field_key, binding in appearance.iter_field_bindings()
            ),
            text_style=appearance.text_style,
            box_style=appearance.box_style,
            image_stamp_path=appearance.image_stamp_path,
            image_prominence=appearance.image_prominence,
            preserve_image_alpha=appearance.preserve_image_alpha,
        )


@dataclass(frozen=True)
class SigningBackendRequest:
    """Backend-facing signing request assembled by the use case."""

    input_pdf_path: str
    output_pdf_path: str
    certificate_path: str
    passphrase: str
    tsa_url: str
    timestamp_required: bool
    certificate_alias: str | None
    signature_rect: SignatureRect | None
    signature_appearance: SigningBackendAppearance | None
    signature_field_name: str | None = None
    signing_time: datetime | None = None
    render_port: PreviewRasterRenderer | None = None

    @classmethod
    def from_signing_request(cls, request: SigningRequest) -> SigningBackendRequest:
        """Normalize the public signing request into the backend payload."""
        if request.signature_rect is None and request.signature_appearance is None:
            appearance = None
        elif request.signature_rect is not None and request.signature_appearance is not None:
            appearance = SigningBackendAppearance.from_signature_appearance(
                request.signature_appearance
            )
        else:
            raise SigningBackendRequestError(
                "signature_rect and signature_appearance must be provided together "
                "for a visible signature."
            )

        return cls(
            input_pdf_path=request.input_pdf_path,
            output_pdf_path=request.output_pdf_path,
            certificate_path=request.certificate_path,
            passphrase=request.passphrase,
            tsa_url=request.tsa_url,
            timestamp_required=request.timestamp_required,
            certificate_alias=request.certificate_alias,
            signature_rect=request.signature_rect,
            signature_appearance=appearance,
            signature_field_name=request.signature_field_name,
            signing_time=request.signing_time,
        )


class SigningBackendRequestError(ValueError):
    """Raised when a public signing request cannot be normalized for signing."""


@dataclass
class SignPdfUseCase:
    """Coordinates phase 1 signing flow and maps failures to stable codes."""

    inspector: PdfInspector
    certificate_loader: CertificateLoader
    signer: PdfSigner
    verifier: SignatureVerifier
    certification_inspector: CertificationInspector = field(
        default_factory=PyHankoCertificationInspector
    )
    compatibility_profile: PdfCompatibilityProfile = PdfCompatibilityProfile()
    preview_render_port: PreviewRasterRenderer | None = None
    transaction_journal: SigningTransactionJournal | None = None

    def verify_preserved_artifact(
        self,
        artifact_path: str,
        *,
        trust_policy: TimestampTrustPolicy | None = None,
    ) -> VerificationSummary:
        """Re-run local verification on an explicitly preserved artifact."""

        return self.verifier.verify(artifact_path, trust_policy=trust_policy)

    def verified_recovery_candidates(self) -> tuple[SigningRecoveryCandidate, ...]:
        """Return only journaled staged artifacts that pass local verification."""

        if self.transaction_journal is None:
            return ()

        def verify(path: str) -> bool:
            summary = self.verify_preserved_artifact(path)
            return (
                summary.signature_count > 0
                and summary.signatures_cryptographically_valid is True
                and not summary.certification_restricted
            )

        try:
            return self.transaction_journal.verified_candidates(verify)
        except OSError:
            # Recovery is opportunistic when the configured user-data location
            # is unavailable (for example, a read-only sandbox).  Signing must
            # retain its normal failure semantics in that environment.
            return ()

    def execute(self, request: SigningRequest) -> SigningResult:
        """Execute the headless signing pipeline."""
        staged_output_path: Path | None = None
        journal_record: SigningTransactionRecord | None = None
        journal_state: str | None = None
        journal = self.transaction_journal
        try:
            if journal is not None:
                journal_record = SigningTransactionRecord.new(
                    transaction_id=str(uuid4()),
                    input_pdf_path=request.input_pdf_path,
                    output_pdf_path=request.output_pdf_path,
                )
                journal.begin(journal_record)
                journal_state = "started"
            if self._paths_conflict(request.input_pdf_path, request.output_pdf_path) and not (
                request.allow_source_overwrite
            ):
                return SigningResult(
                    success=False,
                    failure_code=FailureCode.OUTPUT_PATH_INVALID,
                    message=(
                        "Output path must differ from input path unless source overwrite "
                        "was explicitly authorized."
                    ),
                )

            backend_request = SigningBackendRequest.from_signing_request(request)
            if self.preview_render_port is not None:
                backend_request = replace(
                    backend_request,
                    render_port=self.preview_render_port,
                )
            input_pdf_version = self.inspector.get_pdf_version(request.input_pdf_path)
            self.compatibility_profile.ensure_open_version_supported(input_pdf_version)
            certification = CertificationPolicyResult(
                docmdp_permission=None,
                certification_restricted=False,
                restriction_reason=None,
            )
            if Path(request.input_pdf_path).exists():
                certification = self._inspect_certification(request.input_pdf_path)
            if certification.certification_restricted:
                return SigningResult(
                    success=False,
                    failure_code=FailureCode.PDF_CERTIFICATION_RESTRICTS_SIGNING,
                    message=(
                        certification.restriction_reason
                        or "Certification-restricted document cannot be signed."
                    ),
                    docmdp_permission=certification.docmdp_permission,
                    certification_restricted=True,
                    restriction_reason=certification.restriction_reason,
                    operation_type=DocumentOperationType.SIGN,
                    revision_strategy=RevisionStrategy.INCREMENTAL,
                )
            self.certificate_loader.validate(request.certificate_path, request.passphrase)

            output = self.signer.sign(backend_request)
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

            staged_output_path = self._write_atomically(
                request.output_pdf_path,
                output.output_bytes,
            )
            if journal is not None and journal_record is not None:
                journal.mark_staged(
                    journal_record.transaction_id,
                    str(staged_output_path),
                )
                journal_state = "staged"
            try:
                verification = self.verifier.verify(
                    str(staged_output_path),
                    trust_policy=request.trust_policy,
                )
            except TimestampTrustMaterialError as exc:
                preserved_artifact_path = str(staged_output_path)
                self._mark_journal_preserved(journal, journal_record)
                journal_state = "preserved"
                staged_output_path = None
                return SigningResult(
                    success=False,
                    failure_code=FailureCode.TIMESTAMP_TRUST_MATERIAL_INVALID,
                    message=(
                        "Post-sign verification failed; the preserved artifact must not be "
                        f"relied upon yet: {exc}"
                    ),
                    output_pdf_version=output.output_pdf_version,
                    signature_subfilter=output.signature_subfilter,
                    preserved_artifact_path=preserved_artifact_path,
                )
            except ValueError as exc:
                preserved_artifact_path = str(staged_output_path)
                self._mark_journal_preserved(journal, journal_record)
                journal_state = "preserved"
                staged_output_path = None
                return SigningResult(
                    success=False,
                    failure_code=FailureCode.PDF_SIGNING_FAILED,
                    message=(
                        "Post-sign verification failed; the preserved artifact must not be "
                        f"relied upon yet: {exc}"
                    ),
                    output_pdf_version=output.output_pdf_version,
                    signature_subfilter=output.signature_subfilter,
                    preserved_artifact_path=preserved_artifact_path,
                )
            except Exception as exc:
                preserved_artifact_path = str(staged_output_path)
                self._mark_journal_preserved(journal, journal_record)
                journal_state = "preserved"
                staged_output_path = None
                return SigningResult(
                    success=False,
                    failure_code=FailureCode.POST_VERIFY_FAILED,
                    message=(
                        "Post-sign verification failed; the preserved artifact must not be "
                        f"relied upon yet: {exc}"
                    ),
                    output_pdf_version=output.output_pdf_version,
                    signature_subfilter=output.signature_subfilter,
                    preserved_artifact_path=preserved_artifact_path,
                )
            if request.timestamp_required and not verification.timestamp_present:
                preserved_artifact_path = str(staged_output_path)
                self._mark_journal_preserved(journal, journal_record)
                journal_state = "preserved"
                staged_output_path = None
                return SigningResult(
                    success=False,
                    failure_code=FailureCode.POST_VERIFY_FAILED,
                    message=(
                        "Post-sign verification did not find the expected timestamp token; "
                        "the preserved artifact must not be relied upon yet."
                    ),
                    output_pdf_version=output.output_pdf_version,
                    signature_subfilter=output.signature_subfilter,
                    timestamp_present=verification.timestamp_present,
                    preserved_artifact_path=preserved_artifact_path,
                )
            if request.trust_policy is not None and verification.timestamp_present:
                if (
                    verification.timestamp_cryptographically_valid is False
                    or verification.tsa_chain_trusted is False
                ):
                    preserved_artifact_path = str(staged_output_path)
                    self._mark_journal_preserved(journal, journal_record)
                    journal_state = "preserved"
                    staged_output_path = None
                    return SigningResult(
                        success=False,
                        failure_code=FailureCode.TIMESTAMP_TRUST_FAILED,
                        message=(
                            verification.timestamp_validation_error
                            or "Timestamp trust validation failed."
                        ),
                        output_pdf_version=output.output_pdf_version,
                        signature_subfilter=output.signature_subfilter,
                        timestamp_present=verification.timestamp_present,
                        timestamp_cryptographically_valid=(
                            verification.timestamp_cryptographically_valid
                        ),
                        tsa_chain_trusted=verification.tsa_chain_trusted,
                        timestamp_validation_error=verification.timestamp_validation_error,
                        docmdp_permission=verification.docmdp_permission
                        or certification.docmdp_permission,
                        certification_restricted=verification.certification_restricted,
                        restriction_reason=verification.restriction_reason,
                        preserved_artifact_path=preserved_artifact_path,
                    )

            standards_summary = self.compatibility_profile.build_standards_summary(
                input_pdf_version=input_pdf_version,
                output_pdf_version=output.output_pdf_version,
                signature_subfilter=output.signature_subfilter,
                timestamp_present=verification.timestamp_present,
            )
            if journal is not None and journal_record is not None:
                journal.mark_committing(journal_record.transaction_id)
                journal_state = "committing"
            self._replace_staged(staged_output_path, request.output_pdf_path)
            staged_output_path = None
            if journal is not None and journal_record is not None:
                journal.complete(journal_record.transaction_id)
                journal_state = "completed"
            return SigningResult(
                success=True,
                failure_code=None,
                message="Signing completed successfully.",
                output_pdf_version=output.output_pdf_version,
                signature_subfilter=output.signature_subfilter,
                timestamp_present=verification.timestamp_present,
                timestamp_cryptographically_valid=verification.timestamp_cryptographically_valid,
                tsa_chain_trusted=verification.tsa_chain_trusted,
                timestamp_validation_error=verification.timestamp_validation_error,
                docmdp_permission=verification.docmdp_permission or certification.docmdp_permission,
                certification_restricted=verification.certification_restricted,
                restriction_reason=verification.restriction_reason,
                operation_type=DocumentOperationType.SIGN,
                revision_strategy=RevisionStrategy.INCREMENTAL,
                standards_summary=standards_summary,
            )
        except PdfCompatibilityError as exc:
            return SigningResult(
                success=False,
                failure_code=FailureCode.INPUT_PDF_INVALID,
                message=str(exc),
            )
        except CertificationInspectionError as exc:
            return SigningResult(
                success=False,
                failure_code=FailureCode.INPUT_PDF_INVALID,
                message=str(exc),
                operation_type=DocumentOperationType.SIGN,
                revision_strategy=RevisionStrategy.INCREMENTAL,
            )
        except SigningBackendRequestError as exc:
            return SigningResult(
                success=False,
                failure_code=FailureCode.SIGNATURE_RECT_INVALID,
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
        except TimestampTrustMaterialError as exc:
            return SigningResult(
                success=False,
                failure_code=FailureCode.TIMESTAMP_TRUST_MATERIAL_INVALID,
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
        finally:
            if (
                journal is not None
                and journal_record is not None
                and journal_state not in ("preserved", "committing", "completed")
            ):
                journal.discard(journal_record.transaction_id)
            if staged_output_path is not None and staged_output_path.exists():
                try:
                    staged_output_path.unlink()
                except OSError:
                    pass

    def _mark_journal_preserved(
        self,
        journal: SigningTransactionJournal | None,
        record: SigningTransactionRecord | None,
    ) -> None:
        if journal is not None and record is not None:
            journal.mark_preserved(record.transaction_id)

    @staticmethod
    def _paths_conflict(input_pdf_path: str, output_pdf_path: str) -> bool:
        """Return whether two paths refer to the same intended file."""

        return paths_refer_to_same_file(input_pdf_path, output_pdf_path)

    def _inspect_certification(self, input_pdf_path: str) -> CertificationPolicyResult:
        return self.certification_inspector.inspect(input_pdf_path)

    @staticmethod
    def _write_atomically(output_path: str, output_bytes: bytes) -> Path:
        """Write signed bytes to a sibling temporary path for later verification."""
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_file.write(output_bytes)
            return Path(temp_file.name)

    @staticmethod
    def _replace_staged(staged_path: Path, output_path: str) -> None:
        """Replace the destination only after the staged PDF verifies successfully."""

        staged_path.replace(Path(output_path))
