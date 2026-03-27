"""Configuration schemas for phase 0 foundations."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class TrustProfile:
    """Trust and revocation behavior for validation/timestamping."""

    schema_version: int
    use_system_store: bool
    extra_ca_bundle_path: str | None
    revocation_mode: str

    @classmethod
    def from_dict(cls, payload: dict) -> TrustProfile:
        """Build from persisted mapping."""
        return cls(
            schema_version=int(payload["schema_version"]),
            use_system_store=bool(payload["use_system_store"]),
            extra_ca_bundle_path=payload.get("extra_ca_bundle_path"),
            revocation_mode=str(payload["revocation_mode"]),
        )

    def to_dict(self) -> dict:
        """Convert to a persisted mapping."""
        return asdict(self)


@dataclass(frozen=True)
class TimestampPolicy:
    """RFC 3161 timestamp requirements and connectivity settings."""

    schema_version: int
    required: bool
    tsa_url: str
    timeout_seconds: int

    @classmethod
    def from_dict(cls, payload: dict) -> TimestampPolicy:
        """Build from persisted mapping."""
        return cls(
            schema_version=int(payload["schema_version"]),
            required=bool(payload["required"]),
            tsa_url=str(payload["tsa_url"]),
            timeout_seconds=int(payload["timeout_seconds"]),
        )

    def to_dict(self) -> dict:
        """Convert to a persisted mapping."""
        return asdict(self)


@dataclass(frozen=True)
class SignaturePreset:
    """Reusable visible signature appearance profile."""

    schema_version: int
    name: str
    show_common_name: bool
    show_email: bool
    show_signing_time: bool
    reason: str
    location: str
    datetime_format: str

    @classmethod
    def from_dict(cls, payload: dict) -> SignaturePreset:
        """Build from persisted mapping."""
        return cls(
            schema_version=int(payload["schema_version"]),
            name=str(payload["name"]),
            show_common_name=bool(payload["show_common_name"]),
            show_email=bool(payload["show_email"]),
            show_signing_time=bool(payload["show_signing_time"]),
            reason=str(payload["reason"]),
            location=str(payload["location"]),
            datetime_format=str(payload["datetime_format"]),
        )

    def to_dict(self) -> dict:
        """Convert to a persisted mapping."""
        return asdict(self)
