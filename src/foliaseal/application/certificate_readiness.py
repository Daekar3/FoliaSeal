"""Non-secret certificate readiness projection for the signing rail."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from cryptography.hazmat.primitives.serialization import pkcs12


class CertificateReadinessStatus(StrEnum):
    """User-visible certificate readiness outcomes."""

    READY = "ready"
    EXPIRING_SOON = "expiring_soon"
    NO_CERTIFICATE_SELECTED = "no_certificate_selected"
    PASSWORD_REQUIRED = "password_required"
    MISSING_FILE = "missing_file"
    MISSING_PRIVATE_KEY = "missing_private_key"
    NOT_YET_VALID = "not_yet_valid"
    EXPIRED = "expired"
    INVALID = "invalid"


@dataclass(frozen=True)
class CertificateReadiness:
    """Plain-language, non-secret certificate readiness for UI consumers."""

    status: CertificateReadinessStatus
    detail: str
    blocking: bool
    warning: bool = False
    subject: str | None = None
    issuer: str | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    self_signed: bool = False


class CertificateReadinessReader(Protocol):
    """Read certificate readiness without exposing private material."""

    def read(self, certificate_path: str, passphrase: str) -> CertificateReadiness:
        """Return a readiness projection for one PKCS#12 file."""


@dataclass(frozen=True)
class Pkcs12CertificateReadinessReader:
    """Inspect a password-protected PKCS#12 certificate at the application boundary."""

    clock: Callable[[], datetime] = lambda: datetime.now(UTC)
    expiry_warning_window: timedelta = timedelta(days=30)

    def read(self, certificate_path: str, passphrase: str) -> CertificateReadiness:
        path = Path(certificate_path)
        if not certificate_path.strip():
            return _blocking(
                CertificateReadinessStatus.NO_CERTIFICATE_SELECTED,
                "Select a certificate configuration before signing.",
            )
        if not path.is_file():
            return _blocking(
                CertificateReadinessStatus.MISSING_FILE,
                "The selected certificate file is missing. Restore it from backup or "
                "import it again.",
            )
        if not passphrase:
            return CertificateReadiness(
                status=CertificateReadinessStatus.PASSWORD_REQUIRED,
                detail="The certificate password will be requested before signing.",
                blocking=False,
                warning=True,
            )
        try:
            key, certificate, _extra = pkcs12.load_key_and_certificates(
                path.read_bytes(), passphrase.encode("utf-8")
            )
        except Exception:
            return _blocking(
                CertificateReadinessStatus.INVALID,
                "The selected certificate could not be read. Check the file and password.",
            )
        if certificate is None:
            return _blocking(
                CertificateReadinessStatus.INVALID,
                "The selected certificate file does not contain a certificate.",
            )
        if key is None:
            return _blocking(
                CertificateReadinessStatus.MISSING_PRIVATE_KEY,
                "The selected certificate does not contain a private key. Choose another "
                "certificate.",
            )

        now = _as_utc(self.clock())
        valid_from = _certificate_datetime(certificate, "not_valid_before")
        valid_until = _certificate_datetime(certificate, "not_valid_after")
        subject = certificate.subject.rfc4514_string() or None
        issuer = certificate.issuer.rfc4514_string() or None
        self_signed = certificate.subject == certificate.issuer
        if now < valid_from:
            return _blocking(
                CertificateReadinessStatus.NOT_YET_VALID,
                f"The selected certificate is not valid until {_format_date(valid_from)}.",
                subject=subject,
                issuer=issuer,
                valid_from=valid_from,
                valid_until=valid_until,
                self_signed=self_signed,
            )
        if now > valid_until:
            return _blocking(
                CertificateReadinessStatus.EXPIRED,
                f"The selected certificate expired on {_format_date(valid_until)}. "
                "Choose another certificate.",
                subject=subject,
                issuer=issuer,
                valid_from=valid_from,
                valid_until=valid_until,
                self_signed=self_signed,
            )

        caveat = (
            " This certificate was created locally. The signature can be validated, but other "
            "systems may not independently recognize the signer unless they trust this certificate."
            if self_signed
            else ""
        )
        if valid_until - now <= self.expiry_warning_window:
            return CertificateReadiness(
                status=CertificateReadinessStatus.EXPIRING_SOON,
                detail=(
                    f"Certificate expires on {_format_date(valid_until)}; signing is allowed."
                    f"{caveat}"
                ),
                blocking=False,
                warning=True,
                subject=subject,
                issuer=issuer,
                valid_from=valid_from,
                valid_until=valid_until,
                self_signed=self_signed,
            )
        return CertificateReadiness(
            status=CertificateReadinessStatus.READY,
            detail=(
                "Self-signed certificate — ready for local signing."
                if self_signed
                else "Certificate ready for signing."
            )
            + caveat,
            blocking=False,
            subject=subject,
            issuer=issuer,
            valid_from=valid_from,
            valid_until=valid_until,
            self_signed=self_signed,
        )


def _blocking(
    status: CertificateReadinessStatus,
    detail: str,
    *,
    subject: str | None = None,
    issuer: str | None = None,
    valid_from: datetime | None = None,
    valid_until: datetime | None = None,
    self_signed: bool = False,
) -> CertificateReadiness:
    return CertificateReadiness(
        status=status,
        detail=detail,
        blocking=True,
        subject=subject,
        issuer=issuer,
        valid_from=valid_from,
        valid_until=valid_until,
        self_signed=self_signed,
    )


def _certificate_datetime(certificate: object, name: str) -> datetime:
    utc_name = f"{name}_utc"
    value = getattr(certificate, utc_name, None)
    if value is None:
        value = getattr(certificate, name)
    return _as_utc(value)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _format_date(value: datetime) -> str:
    return _as_utc(value).date().isoformat()


__all__ = [
    "CertificateReadiness",
    "CertificateReadinessReader",
    "CertificateReadinessStatus",
    "Pkcs12CertificateReadinessReader",
]
