from datetime import UTC, datetime, timedelta
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID

from foliaseal.application.certificate_readiness import (
    CertificateReadinessStatus,
    Pkcs12CertificateReadinessReader,
)


def _write_pkcs12(
    path: Path,
    *,
    passphrase: str,
    now: datetime,
    not_valid_before: datetime | None = None,
    not_valid_after: datetime | None = None,
    include_key: bool = True,
    self_signed: bool = True,
) -> None:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Readiness Example")])
    issuer = subject
    if not self_signed:
        issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Issuing CA")])
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(not_valid_before or now - timedelta(days=1))
        .not_valid_after(not_valid_after or now + timedelta(days=365))
        .sign(key, hashes.SHA256())
    )
    path.write_bytes(
        pkcs12.serialize_key_and_certificates(
            name=b"readiness",
            key=key if include_key else None,
            cert=certificate,
            cas=None,
            encryption_algorithm=serialization.BestAvailableEncryption(passphrase.encode()),
        )
    )


def test_reader_reports_ready_self_signed_identity_and_caveat(tmp_path: Path) -> None:
    now = datetime(2026, 8, 10, tzinfo=UTC)
    path = tmp_path / "ready.p12"
    _write_pkcs12(path, passphrase="secret", now=now)

    readiness = Pkcs12CertificateReadinessReader(clock=lambda: now).read(str(path), "secret")

    assert readiness.status is CertificateReadinessStatus.READY
    assert readiness.blocking is False
    assert readiness.self_signed is True
    assert readiness.subject == "CN=Readiness Example"
    assert "Self-signed certificate — ready for local signing" in readiness.detail
    assert "other systems may not independently recognize" in readiness.detail


def test_reader_warns_for_expiry_within_thirty_days(tmp_path: Path) -> None:
    now = datetime(2026, 8, 10, tzinfo=UTC)
    path = tmp_path / "soon.p12"
    _write_pkcs12(
        path,
        passphrase="secret",
        now=now,
        not_valid_after=now + timedelta(days=10),
    )

    readiness = Pkcs12CertificateReadinessReader(clock=lambda: now).read(str(path), "secret")

    assert readiness.status is CertificateReadinessStatus.EXPIRING_SOON
    assert readiness.blocking is False
    assert readiness.warning is True
    assert "signing is allowed" in readiness.detail


def test_reader_blocks_expired_and_not_yet_valid_certificates(tmp_path: Path) -> None:
    now = datetime(2026, 8, 10, tzinfo=UTC)
    expired = tmp_path / "expired.p12"
    _write_pkcs12(
        expired,
        passphrase="secret",
        now=now,
        not_valid_before=now - timedelta(days=20),
        not_valid_after=now - timedelta(days=1),
    )
    future = tmp_path / "future.p12"
    _write_pkcs12(
        future,
        passphrase="secret",
        now=now,
        not_valid_before=now + timedelta(days=1),
        not_valid_after=now + timedelta(days=365),
    )

    reader = Pkcs12CertificateReadinessReader(clock=lambda: now)

    expired_readiness = reader.read(str(expired), "secret")
    future_readiness = reader.read(str(future), "secret")

    assert expired_readiness.status is CertificateReadinessStatus.EXPIRED
    assert expired_readiness.blocking is True
    assert future_readiness.status is CertificateReadinessStatus.NOT_YET_VALID
    assert future_readiness.blocking is True


def test_reader_distinguishes_missing_file_key_password_and_selection(
    tmp_path: Path,
    monkeypatch,
) -> None:
    now = datetime(2026, 8, 10, tzinfo=UTC)
    no_key = tmp_path / "no-key.p12"
    _write_pkcs12(no_key, passphrase="secret", now=now)
    reader = Pkcs12CertificateReadinessReader(clock=lambda: now)

    assert reader.read("", "").status is CertificateReadinessStatus.NO_CERTIFICATE_SELECTED
    assert reader.read(str(tmp_path / "missing.p12"), "secret").status is (
        CertificateReadinessStatus.MISSING_FILE
    )
    _key, certificate, _cas = pkcs12.load_key_and_certificates(
        no_key.read_bytes(), b"secret"
    )
    monkeypatch.setattr(
        pkcs12,
        "load_key_and_certificates",
        lambda *_args, **_kwargs: (None, certificate, None),
    )
    assert reader.read(str(no_key), "secret").status is (
        CertificateReadinessStatus.MISSING_PRIVATE_KEY
    )
    assert reader.read(str(no_key), "").status is CertificateReadinessStatus.PASSWORD_REQUIRED
