"""Single-owner request protocol and Qt local-socket transport for the GUI."""

from __future__ import annotations

import fcntl
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

MAX_REQUEST_BYTES = 4096


class SingleInstanceUnavailable(RuntimeError):
    """Raised when a secondary invocation cannot reach the primary owner."""


@dataclass(frozen=True)
class OpenRequest:
    """A validated request delivered to the existing GUI owner."""

    pdf_path: str | None


def request_for_path(pdf_path: str | Path | None) -> OpenRequest:
    """Normalize an optional CLI path into the bounded wire request."""

    if pdf_path is None:
        return OpenRequest(pdf_path=None)
    path = Path(pdf_path).expanduser().resolve(strict=False)
    if not path.is_absolute():  # pragma: no cover - resolve currently guarantees this
        raise ValueError("PDF path must be absolute")
    return OpenRequest(pdf_path=str(path))


def encode_open_request(request: OpenRequest) -> bytes:
    """Encode one newline-delimited, bounded JSON request."""

    payload = json.dumps(
        {"pdf_path": request.pdf_path},
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8") + b"\n"
    if len(payload) > MAX_REQUEST_BYTES:
        raise ValueError("single-instance request is too large")
    return payload


def decode_open_request(payload: bytes) -> OpenRequest:
    """Decode and validate one complete wire request."""

    if len(payload) > MAX_REQUEST_BYTES:
        raise ValueError("single-instance request is too large")
    try:
        decoded = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid single-instance request") from exc
    if not isinstance(decoded, dict) or set(decoded) != {"pdf_path"}:
        raise ValueError("invalid single-instance request shape")
    value = decoded["pdf_path"]
    if value is None:
        return OpenRequest(pdf_path=None)
    if not isinstance(value, str) or not value.strip() or not Path(value).is_absolute():
        raise ValueError("single-instance PDF path must be absolute")
    return OpenRequest(pdf_path=value)


def endpoint_name(config_directory: str | Path) -> str:
    """Return the per-user local endpoint under the application config directory."""

    directory = Path(config_directory)
    directory.mkdir(parents=True, exist_ok=True)
    return str(directory / "foliaseal-instance.sock")


class SingleInstanceCoordinator(Protocol):
    """Owner/secondary boundary consumed by the Qt app launcher."""

    def set_request_handler(self, handler: Callable[[OpenRequest], None]) -> None: ...

    def start_or_forward(self, request: OpenRequest) -> bool: ...

    def close(self) -> None: ...


class NoopSingleInstanceCoordinator:
    """Fallback used by fake Qt bindings that have no QtNetwork classes."""

    def set_request_handler(self, handler: Callable[[OpenRequest], None]) -> None:
        del handler

    def start_or_forward(self, request: OpenRequest) -> bool:
        del request
        return True

    def close(self) -> None:
        return None


class QtLocalInstanceCoordinator:
    """QLocalServer/QLocalSocket implementation of the owner boundary."""

    def __init__(self, *, endpoint: str, q_local_server: Any, q_local_socket: Any) -> None:
        self._endpoint = endpoint
        self._q_local_server = q_local_server
        self._q_local_socket = q_local_socket
        self._server: Any | None = None
        self._handler: Callable[[OpenRequest], None] = lambda _request: None
        self._buffers: dict[int, bytes] = {}
        self._lock_file: Any | None = None

    def set_request_handler(self, handler: Callable[[OpenRequest], None]) -> None:
        self._handler = handler

    def start_or_forward(self, request: OpenRequest) -> bool:
        if not self._acquire_owner_lock():
            if self._send_to_existing_owner(request):
                return False
            raise SingleInstanceUnavailable(
                f"A FoliaSeal owner is active but not accepting requests: {self._endpoint}"
            )
        server = self._q_local_server()
        self._server = server
        socket_option = getattr(self._q_local_server, "SocketOption", None)
        user_access = getattr(socket_option, "UserAccessOption", None)
        set_socket_options = getattr(server, "setSocketOptions", None)
        if user_access is not None and callable(set_socket_options):
            set_socket_options(user_access)
        new_connection = getattr(server, "newConnection", None)
        if hasattr(new_connection, "connect"):
            new_connection.connect(self._accept_connections)
        listen = getattr(server, "listen", None)
        if callable(listen) and listen(self._endpoint):
            return True

        remove_server = getattr(self._q_local_server, "removeServer", None)
        if callable(remove_server):
            remove_server(self._endpoint)
        if callable(listen) and listen(self._endpoint):
            return True
        raise SingleInstanceUnavailable(
            f"Unable to claim or reach the FoliaSeal instance endpoint: {self._endpoint}"
        )

    def _acquire_owner_lock(self) -> bool:
        lock_path = f"{self._endpoint}.lock"
        self._lock_file = open(lock_path, "a+", encoding="utf-8")
        try:
            fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self._lock_file.close()
            self._lock_file = None
            return False
        return True

    def close(self) -> None:
        server = self._server
        if server is not None:
            close = getattr(server, "close", None)
            if callable(close):
                close()
        self._server = None
        self._buffers.clear()
        lock_file = self._lock_file
        self._lock_file = None
        if lock_file is not None:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            lock_file.close()

    def _send_to_existing_owner(self, request: OpenRequest) -> bool:
        socket = self._q_local_socket()
        connect = getattr(socket, "connectToServer", None)
        wait_connected = getattr(socket, "waitForConnected", None)
        if not callable(connect) or not callable(wait_connected):
            return False
        connect(self._endpoint)
        if not wait_connected(750):
            return False
        write = getattr(socket, "write", None)
        wait_written = getattr(socket, "waitForBytesWritten", None)
        if not callable(write) or not callable(wait_written):
            return False
        write(encode_open_request(request))
        if not wait_written(750):
            disconnect = getattr(socket, "disconnectFromServer", None)
            if callable(disconnect):
                disconnect()
            return False
        disconnect = getattr(socket, "disconnectFromServer", None)
        if callable(disconnect):
            disconnect()
        return True

    def _accept_connections(self) -> None:
        server = self._server
        if server is None:
            return
        has_pending = getattr(server, "hasPendingConnections", None)
        next_connection = getattr(server, "nextPendingConnection", None)
        if not callable(has_pending) or not callable(next_connection):
            return
        while has_pending():
            socket = next_connection()
            if socket is None:
                return
            key = id(socket)
            self._buffers[key] = b""
            ready_read = getattr(socket, "readyRead", None)
            if hasattr(ready_read, "connect"):
                ready_read.connect(lambda socket=socket: self._read_socket(socket))
            disconnected = getattr(socket, "disconnected", None)
            if hasattr(disconnected, "connect"):
                disconnected.connect(lambda key=key: self._buffers.pop(key, None))
            self._read_socket(socket)

    def _read_socket(self, socket: Any) -> None:
        key = id(socket)
        read_all = getattr(socket, "readAll", None)
        if not callable(read_all):
            return
        self._buffers[key] += bytes(read_all())
        if len(self._buffers[key]) > MAX_REQUEST_BYTES:
            self._disconnect(socket, key)
            return
        while b"\n" in self._buffers[key]:
            line, remainder = self._buffers[key].split(b"\n", 1)
            self._buffers[key] = remainder
            try:
                request = decode_open_request(line)
            except ValueError:
                self._disconnect(socket, key)
                return
            self._handler(request)

    def _disconnect(self, socket: Any, key: int) -> None:
        self._buffers.pop(key, None)
        disconnect = getattr(socket, "disconnectFromServer", None)
        if callable(disconnect):
            disconnect()
