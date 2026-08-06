"""Application-owned managed-certificate models and catalog policy.

Persistence codecs live in the infra configuration adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from foliaseal.domain.errors import ConfigValidationError


def _require_int_value(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigValidationError(f"Field '{field}' must be an int.")
    return value


def _require_bool(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise ConfigValidationError(f"Field '{field}' must be a bool.")
    return value


def _require_non_empty_str_value(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigValidationError(f"Field '{field}' must be a non-empty str.")
    return value


def _require_optional_non_empty_str_value(value: object, field: str) -> str | None:
    if value is None:
        return None
    return _require_non_empty_str_value(value, field)


@dataclass(frozen=True)
class ManagedCertificateSubjectSummary:
    """Non-secret certificate subject fields shown in certificate lists."""

    common_name: str | None = None
    email: str | None = None
    title: str | None = None
    company: str | None = None

    def __post_init__(self) -> None:
        for field_name in ("common_name", "email", "title", "company"):
            object.__setattr__(
                self,
                field_name,
                _require_optional_non_empty_str_value(getattr(self, field_name), field_name),
            )

@dataclass(frozen=True)
class ManagedCertificate:
    """Application-managed certificate file record."""

    schema_version: int
    managed_certificate_id: str
    display_name: str
    storage_filename: str
    source_kind: str
    created_at: str
    subject_summary: ManagedCertificateSubjectSummary

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "schema_version",
            _require_int_value(self.schema_version, "schema_version"),
        )
        object.__setattr__(
            self,
            "managed_certificate_id",
            _require_non_empty_str_value(self.managed_certificate_id, "managed_certificate_id"),
        )
        object.__setattr__(
            self,
            "display_name",
            _require_non_empty_str_value(self.display_name, "display_name"),
        )
        storage_filename = _require_non_empty_str_value(
            self.storage_filename,
            "storage_filename",
        )
        if (
            "/" in storage_filename
            or "\\" in storage_filename
            or storage_filename
            in {
                ".",
                "..",
            }
        ):
            raise ConfigValidationError("Field 'storage_filename' must be a filename, not a path.")
        object.__setattr__(self, "storage_filename", storage_filename)
        source_kind = _require_non_empty_str_value(self.source_kind, "source_kind")
        if source_kind not in {"created", "imported"}:
            raise ConfigValidationError("Field 'source_kind' must be 'created' or 'imported'.")
        object.__setattr__(self, "source_kind", source_kind)
        object.__setattr__(
            self,
            "created_at",
            _require_non_empty_str_value(self.created_at, "created_at"),
        )
        if not isinstance(self.subject_summary, ManagedCertificateSubjectSummary):
            raise ConfigValidationError(
                "Field 'subject_summary' must be a ManagedCertificateSubjectSummary."
            )

@dataclass(frozen=True)
class CertificateConfiguration:
    """User-facing signing identity configuration."""

    schema_version: int
    certificate_configuration_id: str
    display_name: str
    managed_certificate_id: str
    save_password: bool
    password_secret_ref: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "schema_version",
            _require_int_value(self.schema_version, "schema_version"),
        )
        object.__setattr__(
            self,
            "certificate_configuration_id",
            _require_non_empty_str_value(
                self.certificate_configuration_id,
                "certificate_configuration_id",
            ),
        )
        object.__setattr__(
            self,
            "display_name",
            _require_non_empty_str_value(self.display_name, "display_name"),
        )
        object.__setattr__(
            self,
            "managed_certificate_id",
            _require_non_empty_str_value(self.managed_certificate_id, "managed_certificate_id"),
        )
        object.__setattr__(
            self,
            "save_password",
            _require_bool(self.save_password, "save_password"),
        )
        object.__setattr__(
            self,
            "password_secret_ref",
            _require_optional_non_empty_str_value(self.password_secret_ref, "password_secret_ref"),
        )
        if self.save_password and self.password_secret_ref is None:
            raise ConfigValidationError(
                "Field 'password_secret_ref' is required when 'save_password' is true."
            )
        if not self.save_password and self.password_secret_ref is not None:
            raise ConfigValidationError(
                "Field 'password_secret_ref' must be null when 'save_password' is false."
            )
        object.__setattr__(
            self,
            "notes",
            _require_optional_non_empty_str_value(self.notes, "notes"),
        )

@dataclass(frozen=True)
class CertificateCatalog:
    """Catalog of managed certificates and certificate configurations."""

    schema_version: int
    managed_certificates: tuple[ManagedCertificate, ...] = ()
    certificate_configurations: tuple[CertificateConfiguration, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "schema_version",
            _require_int_value(self.schema_version, "schema_version"),
        )
        self._validate_object_tuple(
            self.managed_certificates,
            ManagedCertificate,
            "managed_certificates",
            "managed_certificate_id",
        )
        self._validate_object_tuple(
            self.certificate_configurations,
            CertificateConfiguration,
            "certificate_configurations",
            "certificate_configuration_id",
        )
        seen_names: set[str] = set()
        seen_managed_certificate_ids: set[str] = set()
        for configuration in self.certificate_configurations:
            if configuration.display_name in seen_names:
                raise ConfigValidationError(
                    "Field 'certificate_configurations' must not contain duplicate names."
                )
            seen_names.add(configuration.display_name)
            if configuration.managed_certificate_id in seen_managed_certificate_ids:
                raise ConfigValidationError(
                    "Field 'certificate_configurations' must not contain duplicate "
                    "managed certificate references."
                )
            seen_managed_certificate_ids.add(configuration.managed_certificate_id)

    @staticmethod
    def _validate_object_tuple(
        values: tuple[Any, ...],
        expected_type: type,
        field_name: str,
        id_field_name: str,
    ) -> None:
        if not isinstance(values, tuple):
            raise ConfigValidationError(f"Field '{field_name}' must be a tuple.")
        seen_ids: set[str] = set()
        for value in values:
            if not isinstance(value, expected_type):
                raise ConfigValidationError(
                    f"Field '{field_name}' must contain {expected_type.__name__} values only."
                )
            object_id = getattr(value, id_field_name)
            if object_id in seen_ids:
                raise ConfigValidationError(f"Field '{field_name}' must not contain duplicate ids.")
            seen_ids.add(object_id)

    def configuration_named(self, name: str) -> CertificateConfiguration:
        """Return a certificate configuration by display name."""
        normalized_name = _require_non_empty_str_value(name, "name")
        for configuration in self.certificate_configurations:
            if configuration.display_name == normalized_name:
                return configuration
        raise KeyError(normalized_name)

    def configuration_by_id(self, configuration_id: str) -> CertificateConfiguration:
        """Return a certificate configuration by stable id."""
        normalized_id = _require_non_empty_str_value(
            configuration_id,
            "certificate_configuration_id",
        )
        for configuration in self.certificate_configurations:
            if configuration.certificate_configuration_id == normalized_id:
                return configuration
        raise KeyError(normalized_id)

    def managed_certificate_by_id(self, certificate_id: str) -> ManagedCertificate:
        """Return a managed certificate by stable id."""
        normalized_id = _require_non_empty_str_value(
            certificate_id,
            "managed_certificate_id",
        )
        for certificate in self.managed_certificates:
            if certificate.managed_certificate_id == normalized_id:
                return certificate
        raise KeyError(normalized_id)

    def upsert_managed_certificate(
        self,
        certificate: ManagedCertificate,
    ) -> CertificateCatalog:
        """Return a catalog with a managed certificate inserted or replaced."""
        if not isinstance(certificate, ManagedCertificate):
            raise ConfigValidationError("certificate must be a ManagedCertificate value.")
        return CertificateCatalog(
            schema_version=self.schema_version,
            managed_certificates=tuple(
                self._upsert_by_id(
                    list(self.managed_certificates),
                    certificate,
                    "managed_certificate_id",
                )
            ),
            certificate_configurations=self.certificate_configurations,
        )

    def remove_managed_certificate_by_id(self, certificate_id: str) -> CertificateCatalog:
        """Return a catalog without an unreferenced managed certificate."""
        normalized_id = _require_non_empty_str_value(
            certificate_id,
            "managed_certificate_id",
        )
        for configuration in self.certificate_configurations:
            if configuration.managed_certificate_id == normalized_id:
                raise ConfigValidationError(
                    "Managed certificate is still used by a certificate configuration; "
                    "delete the configuration first."
                )
        updated_certificates = tuple(
            certificate
            for certificate in self.managed_certificates
            if certificate.managed_certificate_id != normalized_id
        )
        if len(updated_certificates) == len(self.managed_certificates):
            raise KeyError(normalized_id)
        return CertificateCatalog(
            schema_version=self.schema_version,
            managed_certificates=updated_certificates,
            certificate_configurations=self.certificate_configurations,
        )

    def upsert_configuration(
        self,
        configuration: CertificateConfiguration,
    ) -> CertificateCatalog:
        """Return a catalog with a certificate configuration inserted or replaced."""
        if not isinstance(configuration, CertificateConfiguration):
            raise ConfigValidationError("configuration must be a CertificateConfiguration value.")
        return CertificateCatalog(
            schema_version=self.schema_version,
            managed_certificates=self.managed_certificates,
            certificate_configurations=tuple(
                self._upsert_by_id(
                    list(self.certificate_configurations),
                    configuration,
                    "certificate_configuration_id",
                )
            ),
        )

    @staticmethod
    def _upsert_by_id(values: list[Any], replacement: Any, id_field_name: str) -> list[Any]:
        updated: list[Any] = []
        replaced = False
        replacement_id = getattr(replacement, id_field_name)
        for value in values:
            if getattr(value, id_field_name) == replacement_id:
                updated.append(replacement)
                replaced = True
            else:
                updated.append(value)
        if not replaced:
            updated.append(replacement)
        return updated

    def remove_configuration(self, name: str) -> CertificateCatalog:
        """Return a catalog without the named certificate configuration."""
        normalized_name = _require_non_empty_str_value(name, "name")
        updated_configurations = tuple(
            configuration
            for configuration in self.certificate_configurations
            if configuration.display_name != normalized_name
        )
        if len(updated_configurations) == len(self.certificate_configurations):
            raise KeyError(normalized_name)
        return CertificateCatalog(
            schema_version=self.schema_version,
            managed_certificates=self.managed_certificates,
            certificate_configurations=updated_configurations,
        )

    def remove_configuration_by_id(self, configuration_id: str) -> CertificateCatalog:
        """Return a catalog without the certificate configuration with the given id."""
        normalized_id = _require_non_empty_str_value(
            configuration_id,
            "certificate_configuration_id",
        )
        updated_configurations = tuple(
            configuration
            for configuration in self.certificate_configurations
            if configuration.certificate_configuration_id != normalized_id
        )
        if len(updated_configurations) == len(self.certificate_configurations):
            raise KeyError(normalized_id)
        return CertificateCatalog(
            schema_version=self.schema_version,
            managed_certificates=self.managed_certificates,
            certificate_configurations=updated_configurations,
        )
