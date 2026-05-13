from __future__ import annotations

import subprocess

import pytest

from foliaseal.infra.secret_storage import (
    SecretStorageError,
    SecretToolCertificateSecretStore,
)


class _Runner:
    def __init__(
        self,
        *,
        returncode: int = 0,
        stdout: str = "",
        stderr: str = "",
    ) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.calls: list[tuple[list[str], str | None]] = []

    def __call__(self, args, *, input=None, **_kwargs):
        self.calls.append((list(args), input))
        return subprocess.CompletedProcess(
            args=args,
            returncode=self.returncode,
            stdout=self.stdout,
            stderr=self.stderr,
        )


def test_secret_tool_store_builds_stable_secret_refs() -> None:
    store = SecretToolCertificateSecretStore(availability_checker=lambda: True)

    assert store.secret_ref_for_configuration(" cert-config-default ") == (
        "secret-tool://foliaseal/certificate-password/cert-config-default"
    )


def test_secret_tool_store_saves_password_with_secret_service_attributes() -> None:
    runner = _Runner()
    store = SecretToolCertificateSecretStore(
        executable="secret-tool",
        runner=runner,
        availability_checker=lambda: True,
    )

    store.set_secret(
        "secret-tool://foliaseal/certificate-password/cert-config-default",
        "secret",
    )

    assert runner.calls == [
        (
            [
                "secret-tool",
                "store",
                "--label",
                "FoliaSeal certificate password cert-config-default",
                "application",
                "FoliaSeal",
                "kind",
                "certificate-password",
                "configuration_id",
                "cert-config-default",
            ],
            "secret",
        )
    ]


def test_secret_tool_store_reads_password_and_treats_missing_secret_as_none() -> None:
    found_runner = _Runner(stdout="secret\n")
    found_store = SecretToolCertificateSecretStore(
        runner=found_runner,
        availability_checker=lambda: True,
    )
    missing_runner = _Runner(returncode=1)
    missing_store = SecretToolCertificateSecretStore(
        runner=missing_runner,
        availability_checker=lambda: True,
    )

    assert found_store.get_secret(
        "secret-tool://foliaseal/certificate-password/cert-config-default"
    ) == "secret"
    assert missing_store.get_secret(
        "secret-tool://foliaseal/certificate-password/cert-config-default"
    ) is None


def test_secret_tool_store_raises_when_lookup_operation_fails() -> None:
    runner = _Runner(returncode=2, stderr="service unavailable")
    store = SecretToolCertificateSecretStore(
        runner=runner,
        availability_checker=lambda: True,
    )

    with pytest.raises(SecretStorageError, match="service unavailable"):
        store.get_secret(
            "secret-tool://foliaseal/certificate-password/cert-config-default"
        )


def test_secret_tool_store_deletes_password() -> None:
    runner = _Runner()
    store = SecretToolCertificateSecretStore(
        runner=runner,
        availability_checker=lambda: True,
    )

    store.delete_secret(
        "secret-tool://foliaseal/certificate-password/cert-config-default"
    )

    assert runner.calls[0][0] == [
        "secret-tool",
        "clear",
        "application",
        "FoliaSeal",
        "kind",
        "certificate-password",
        "configuration_id",
        "cert-config-default",
    ]


def test_secret_tool_store_requires_available_storage_for_writes() -> None:
    store = SecretToolCertificateSecretStore(availability_checker=lambda: False)

    with pytest.raises(SecretStorageError, match="not available"):
        store.set_secret(
            "secret-tool://foliaseal/certificate-password/cert-config-default",
            "secret",
        )


def test_secret_tool_store_rejects_unsupported_refs() -> None:
    store = SecretToolCertificateSecretStore(availability_checker=lambda: True)

    with pytest.raises(SecretStorageError, match="Unsupported"):
        store.get_secret("secret://other/cert-config-default")
