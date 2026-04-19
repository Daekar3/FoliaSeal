"""pyHanko timestamper adapters used by the signing backend."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from functools import lru_cache
from urllib.parse import urlparse

from asn1crypto import keys as asn1_keys
from asn1crypto import x509 as asn1_x509
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from pyhanko.sign.timestamps.dummy_client import DummyTimeStamper
from pyhanko.sign.timestamps.requests_client import HTTPTimeStamper

from foliaseal.domain.errors import TsaUnavailableError


@lru_cache(maxsize=1)
def build_dummy_timestamper() -> DummyTimeStamper:
    """Build a deterministic in-memory TSA for tests and acceptance matrices."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, "FoliaSeal TSA"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "FoliaSeal"),
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        ]
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(UTC) - timedelta(days=1))
        .not_valid_after(datetime.now(UTC) + timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )
    tsa_cert = asn1_x509.Certificate.load(cert.public_bytes(serialization.Encoding.DER))
    tsa_key = asn1_keys.PrivateKeyInfo.load(
        key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    return DummyTimeStamper(
        tsa_cert=tsa_cert,
        tsa_key=tsa_key,
        fixed_dt=datetime(2024, 1, 1, tzinfo=UTC),
    )


def build_http_timestamper(tsa_url: str, *, timeout: int = 5) -> HTTPTimeStamper:
    """Build a concrete HTTP timestamper from a configured TSA URL."""
    parsed = urlparse(tsa_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise TsaUnavailableError(f"Invalid TSA URL: {tsa_url!r}")
    return HTTPTimeStamper(
        tsa_url,
        https=parsed.scheme == "https",
        timeout=timeout,
    )
