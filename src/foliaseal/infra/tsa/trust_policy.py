"""Trust-policy helpers for timestamp validation."""

from __future__ import annotations

from pathlib import Path

from asn1crypto import x509 as asn1_x509
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from pyhanko_certvalidator import ValidationContext

from foliaseal.domain.errors import TimestampTrustMaterialError
from foliaseal.domain.models import TimestampTrustPolicy


def build_timestamp_validation_context(
    trust_policy: TimestampTrustPolicy | None,
) -> ValidationContext | None:
    """Build a pyHanko validation context for timestamp trust checks."""
    if trust_policy is None:
        return None

    trust_roots = _load_trust_roots(trust_policy.extra_ca_bundle_path)
    if not trust_policy.use_system_store and not trust_roots:
        raise TimestampTrustMaterialError(
            "Timestamp trust material is required when the system store is disabled."
        )

    validation_kwargs: dict[str, object] = {
        "revocation_mode": trust_policy.revocation_mode,
        "allow_fetching": False,
    }
    if trust_roots:
        if trust_policy.use_system_store:
            validation_kwargs["extra_trust_roots"] = trust_roots
        else:
            validation_kwargs["trust_roots"] = trust_roots
    return ValidationContext(**validation_kwargs)


def _load_trust_roots(bundle_path: str | None) -> tuple[asn1_x509.Certificate, ...]:
    if bundle_path is None:
        return ()

    path = Path(bundle_path)
    if not path.exists():
        raise TimestampTrustMaterialError(f"Timestamp trust bundle not found: {bundle_path}")
    try:
        certs = x509.load_pem_x509_certificates(path.read_bytes())
    except Exception as exc:
        raise TimestampTrustMaterialError(
            f"Timestamp trust bundle is not a valid PEM certificate bundle: {bundle_path}"
        ) from exc
    if not certs:
        raise TimestampTrustMaterialError(
            f"Timestamp trust bundle did not contain any certificates: {bundle_path}"
        )
    return tuple(
        asn1_x509.Certificate.load(cert.public_bytes(serialization.Encoding.DER))
        for cert in certs
    )
