"""Certificate-derived visible signature preview values."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID

from foliaseal.domain.models import SignatureFieldKey


@dataclass(frozen=True)
class CertificatePreviewValues:
    """Certificate field values used for visible-signature preview semantics."""

    available: bool
    values: dict[SignatureFieldKey, str]


class CertificatePreviewReader(Protocol):
    """Read visible-signature preview fields from certificate material."""

    def read_preview_values(
        self,
        certificate_path: str,
        passphrase: str,
    ) -> CertificatePreviewValues:
        """Return certificate-derived preview field values."""


class Pkcs12CertificatePreviewReader:
    """Read preview fields from a PKCS#12 certificate file."""

    def read_preview_values(
        self,
        certificate_path: str,
        passphrase: str,
    ) -> CertificatePreviewValues:
        """Return certificate-derived preview field values."""
        try:
            key, certificate, _extra = pkcs12.load_key_and_certificates(
                Path(certificate_path).read_bytes(),
                passphrase.encode("utf-8"),
            )
        except Exception:
            return CertificatePreviewValues(available=False, values={})

        if key is None or certificate is None:
            return CertificatePreviewValues(available=False, values={})

        subject = certificate.subject

        def _first_attr(oid: NameOID) -> str | None:
            attributes = subject.get_attributes_for_oid(oid)
            if not attributes:
                return None
            value = attributes[0].value.strip()
            return value or None

        common_name = _first_attr(NameOID.COMMON_NAME)
        email = _first_attr(NameOID.EMAIL_ADDRESS)
        title = _first_attr(NameOID.TITLE) or _first_attr(NameOID.ORGANIZATIONAL_UNIT_NAME)
        company = _first_attr(NameOID.ORGANIZATION_NAME)
        location_parts = tuple(
            value
            for value in (
                _first_attr(NameOID.LOCALITY_NAME),
                _first_attr(NameOID.STATE_OR_PROVINCE_NAME),
                _first_attr(NameOID.COUNTRY_NAME),
            )
            if value
        )
        distinguished_name_parts = tuple(
            value
            for value in (
                common_name,
                email,
                title,
                company,
                *location_parts,
            )
            if value
        )

        values: dict[SignatureFieldKey, str] = {}
        if distinguished_name_parts:
            values[SignatureFieldKey.DISTINGUISHED_NAME] = ", ".join(
                distinguished_name_parts
            )
        if common_name:
            values[SignatureFieldKey.COMMON_NAME] = common_name
        if email:
            values[SignatureFieldKey.EMAIL] = email
        if title:
            values[SignatureFieldKey.TITLE] = title
        if company:
            values[SignatureFieldKey.COMPANY] = company
        if location_parts:
            values[SignatureFieldKey.LOCATION] = ", ".join(location_parts)

        return CertificatePreviewValues(available=True, values=values)
