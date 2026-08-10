"""JSON codecs for application-owned certificate models."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from foliaseal.application.certificate_models import (
    CertificateCatalog,
    CertificateConfiguration,
    ManagedCertificate,
    ManagedCertificateSubjectSummary,
)
from foliaseal.domain.errors import ConfigValidationError


def _require_value(payload: Mapping[str, Any], field: str) -> Any:
    if field not in payload:
        raise ConfigValidationError(f"Field '{field}' is required.")
    return payload[field]


def _require_mapping(payload: Mapping[str, Any], field: str) -> dict[str, Any]:
    value = _require_value(payload, field)
    if not isinstance(value, dict):
        raise ConfigValidationError(f"Field '{field}' must be an object.")
    return value


def _require_int(payload: Mapping[str, Any], field: str) -> int:
    value = _require_value(payload, field)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigValidationError(f"Field '{field}' must be an int.")
    return value


def _require_bool(payload: Mapping[str, Any], field: str) -> bool:
    value = _require_value(payload, field)
    if not isinstance(value, bool):
        raise ConfigValidationError(f"Field '{field}' must be a bool.")
    return value


def _require_str(payload: Mapping[str, Any], field: str) -> str:
    value = _require_value(payload, field)
    if not isinstance(value, str):
        raise ConfigValidationError(f"Field '{field}' must be a str.")
    return value


def _require_non_empty_str(payload: Mapping[str, Any], field: str) -> str:
    value = _require_str(payload, field)
    if not value.strip():
        raise ConfigValidationError(f"Field '{field}' must be a non-empty str.")
    return value


def _optional_str(payload: Mapping[str, Any], field: str) -> str | None:
    value = payload.get(field)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ConfigValidationError(f"Field '{field}' must be a str when present.")
    return value


def _decode_subject(payload: Mapping[str, Any]) -> ManagedCertificateSubjectSummary:
    return ManagedCertificateSubjectSummary(
        common_name=_optional_str(payload, "common_name"),
        distinguished_name=_optional_str(payload, "distinguished_name"),
        email=_optional_str(payload, "email"),
        title=_optional_str(payload, "title"),
        company=_optional_str(payload, "company"),
    )


def _decode_managed_certificate(payload: Mapping[str, Any]) -> ManagedCertificate:
    return ManagedCertificate(
        schema_version=_require_int(payload, "schema_version"),
        managed_certificate_id=_require_non_empty_str(payload, "managed_certificate_id"),
        display_name=_require_non_empty_str(payload, "display_name"),
        storage_filename=_require_non_empty_str(payload, "storage_filename"),
        source_kind=_require_non_empty_str(payload, "source_kind"),
        created_at=_require_non_empty_str(payload, "created_at"),
        subject_summary=_decode_subject(_require_mapping(payload, "subject_summary")),
        pinned=_require_bool(payload, "pinned") if "pinned" in payload else False,
        issuer_summary=_optional_str(payload, "issuer_summary"),
        valid_from=_optional_str(payload, "valid_from"),
        valid_until=_optional_str(payload, "valid_until"),
        fingerprint_sha256=_optional_str(payload, "fingerprint_sha256"),
    )


def _decode_configuration(payload: Mapping[str, Any]) -> CertificateConfiguration:
    return CertificateConfiguration(
        schema_version=_require_int(payload, "schema_version"),
        certificate_configuration_id=_require_non_empty_str(
            payload, "certificate_configuration_id"
        ),
        display_name=_require_non_empty_str(payload, "display_name"),
        managed_certificate_id=_require_non_empty_str(payload, "managed_certificate_id"),
        save_password=_require_bool(payload, "save_password"),
        password_secret_ref=_optional_str(payload, "password_secret_ref"),
        notes=_optional_str(payload, "notes"),
        pinned=_require_bool(payload, "pinned") if "pinned" in payload else False,
    )


def decode_certificate_catalog(payload: Mapping[str, Any]) -> CertificateCatalog:
    """Decode one persisted certificate catalog payload."""
    raw_managed = _require_value(payload, "managed_certificates")
    raw_configurations = _require_value(payload, "certificate_configurations")
    for field_name, entries in (
        ("managed_certificates", raw_managed),
        ("certificate_configurations", raw_configurations),
    ):
        if not isinstance(entries, list):
            raise ConfigValidationError(f"Field '{field_name}' must be a list.")
    managed = []
    for entry in raw_managed:
        if not isinstance(entry, dict):
            raise ConfigValidationError(
                "Field 'managed_certificates' must contain objects only."
            )
        managed.append(_decode_managed_certificate(entry))
    configurations = []
    for entry in raw_configurations:
        if not isinstance(entry, dict):
            raise ConfigValidationError(
                "Field 'certificate_configurations' must contain objects only."
            )
        configurations.append(_decode_configuration(entry))
    return CertificateCatalog(
        schema_version=_require_int(payload, "schema_version"),
        managed_certificates=tuple(managed),
        certificate_configurations=tuple(configurations),
    )


def _encode_subject(subject: ManagedCertificateSubjectSummary) -> dict[str, Any]:
    return {
        "common_name": subject.common_name,
        "distinguished_name": subject.distinguished_name,
        "email": subject.email,
        "title": subject.title,
        "company": subject.company,
    }


def _encode_managed_certificate(certificate: ManagedCertificate) -> dict[str, Any]:
    return {
        "schema_version": certificate.schema_version,
        "managed_certificate_id": certificate.managed_certificate_id,
        "display_name": certificate.display_name,
        "storage_filename": certificate.storage_filename,
        "source_kind": certificate.source_kind,
        "created_at": certificate.created_at,
        "subject_summary": _encode_subject(certificate.subject_summary),
        "pinned": certificate.pinned,
        "issuer_summary": certificate.issuer_summary,
        "valid_from": certificate.valid_from,
        "valid_until": certificate.valid_until,
        "fingerprint_sha256": certificate.fingerprint_sha256,
    }


def _encode_configuration(configuration: CertificateConfiguration) -> dict[str, Any]:
    return {
        "schema_version": configuration.schema_version,
        "certificate_configuration_id": configuration.certificate_configuration_id,
        "display_name": configuration.display_name,
        "managed_certificate_id": configuration.managed_certificate_id,
        "save_password": configuration.save_password,
        "password_secret_ref": configuration.password_secret_ref,
        "notes": configuration.notes,
        "pinned": configuration.pinned,
    }


def encode_certificate_catalog(catalog: CertificateCatalog) -> dict[str, Any]:
    """Encode one application certificate catalog for persisted JSON."""
    if not isinstance(catalog, CertificateCatalog):
        raise ConfigValidationError("catalog must be a CertificateCatalog value.")
    return {
        "schema_version": catalog.schema_version,
        "managed_certificates": [
            _encode_managed_certificate(certificate)
            for certificate in catalog.managed_certificates
        ],
        "certificate_configurations": [
            _encode_configuration(configuration)
            for configuration in catalog.certificate_configurations
        ],
    }


__all__ = ["decode_certificate_catalog", "encode_certificate_catalog"]
