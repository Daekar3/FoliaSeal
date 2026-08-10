import subprocess
import sys

import pytest

from foliaseal.application.certificate_models import CertificateCatalog
from foliaseal.domain.errors import ConfigValidationError
from foliaseal.infra.config.certificate_codecs import (
    decode_certificate_catalog,
    encode_certificate_catalog,
)
from tests.support.signing_builders import build_certificate_catalog


def test_application_certificate_models_import_without_infra_or_gui() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; import foliaseal.application.certificate_models; "
                "assert 'foliaseal.infra.config.schemas' not in sys.modules; "
                "assert 'foliaseal.infra.config.certificate_storage' not in sys.modules; "
                "assert not any(name.startswith(('PySide6', 'PIL', 'pyhanko')) "
                "for name in sys.modules)"
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_certificate_codec_preserves_catalog_shape_and_round_trip() -> None:
    original = build_certificate_catalog()

    payload = encode_certificate_catalog(original)
    restored = decode_certificate_catalog(payload)

    assert restored == original
    assert set(payload) == {
        "schema_version",
        "managed_certificates",
        "certificate_configurations",
    }
    assert set(payload["managed_certificates"][0]) == {
        "schema_version",
        "managed_certificate_id",
        "display_name",
        "storage_filename",
        "source_kind",
        "created_at",
        "subject_summary",
        "pinned",
    }


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"schema_version": 1}, "managed_certificates"),
        (
            {
                "schema_version": 1,
                "managed_certificates": {},
                "certificate_configurations": [],
            },
            "must be a list",
        ),
    ],
)
def test_certificate_codec_rejects_malformed_catalog(payload: dict, message: str) -> None:
    with pytest.raises(ConfigValidationError, match=message):
        decode_certificate_catalog(payload)


def test_catalog_policy_remains_application_owned() -> None:
    catalog = CertificateCatalog(schema_version=1)

    assert catalog.managed_certificates == ()
    assert catalog.certificate_configurations == ()


def test_certificate_pin_metadata_round_trips_and_updates_by_stable_id() -> None:
    original = build_certificate_catalog()
    managed = original.managed_certificates[0]
    configuration = original.certificate_configurations[0]

    updated = original.set_managed_certificate_pinned(managed.managed_certificate_id, True)
    updated = updated.set_configuration_pinned(configuration.certificate_configuration_id, True)

    assert updated.managed_certificates[0].pinned is True
    assert updated.certificate_configurations[0].pinned is True
    assert decode_certificate_catalog(encode_certificate_catalog(updated)) == updated
