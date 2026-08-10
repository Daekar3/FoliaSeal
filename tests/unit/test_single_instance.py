from pathlib import Path

import pytest

from foliaseal.presentation.qt.single_instance import (
    MAX_REQUEST_BYTES,
    OpenRequest,
    QtLocalInstanceCoordinator,
    decode_open_request,
    encode_open_request,
    endpoint_name,
    request_for_path,
)


def test_request_round_trip_normalizes_absolute_path(tmp_path: Path) -> None:
    request = request_for_path(tmp_path / "contract.pdf")

    assert request == OpenRequest(pdf_path=str((tmp_path / "contract.pdf").resolve()))
    assert decode_open_request(encode_open_request(request)) == request


def test_empty_request_is_valid_for_second_invocation_activation() -> None:
    assert decode_open_request(encode_open_request(OpenRequest(None))) == OpenRequest(None)


def test_request_rejects_relative_or_malformed_paths() -> None:
    with pytest.raises(ValueError, match="absolute"):
        decode_open_request(b'{"pdf_path":"relative.pdf"}')
    with pytest.raises(ValueError, match="invalid"):
        decode_open_request(b"not-json")


def test_request_rejects_oversized_payload() -> None:
    with pytest.raises(ValueError, match="too large"):
        encode_open_request(OpenRequest(pdf_path="/" + "x" * MAX_REQUEST_BYTES))


def test_endpoint_is_scoped_to_the_user_config_directory(tmp_path: Path) -> None:
    endpoint = endpoint_name(tmp_path / "config")

    assert endpoint == str(tmp_path / "config" / "foliaseal-instance.sock")
    assert (tmp_path / "config").is_dir()


def test_owner_lock_prevents_a_second_coordinator_claim(tmp_path: Path) -> None:
    endpoint = str(tmp_path / "foliaseal-instance.sock")
    first = QtLocalInstanceCoordinator(
        endpoint=endpoint,
        q_local_server=object,
        q_local_socket=object,
    )
    second = QtLocalInstanceCoordinator(
        endpoint=endpoint,
        q_local_server=object,
        q_local_socket=object,
    )

    try:
        assert first._acquire_owner_lock() is True
        assert second._acquire_owner_lock() is False
    finally:
        second.close()
        first.close()
