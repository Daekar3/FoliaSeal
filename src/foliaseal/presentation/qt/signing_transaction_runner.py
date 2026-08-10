"""Owned worker boundary for one non-cancellable signing transaction."""

from __future__ import annotations

from collections.abc import Callable
from queue import Empty, Queue
from threading import Thread
from typing import Protocol

from foliaseal.domain.models import SigningRequest, SigningResult


class SigningTransactionRunner(Protocol):
    """Run one signing request away from the Qt event loop."""

    def start(self, request: SigningRequest) -> None:
        """Start exactly one request."""

    def is_running(self) -> bool:
        """Return whether the owned worker is still executing."""

    def poll_completion(self) -> SigningResult | BaseException | None:
        """Return the terminal result once, or ``None`` while pending."""

    def close(self) -> None:
        """Join the owned worker and release the runner."""


class ThreadSigningTransactionRunner:
    """Execute one injected signing operation on an owned daemon thread."""

    def __init__(self, execute: Callable[[SigningRequest], SigningResult]) -> None:
        self._execute = execute
        self._completion: Queue[SigningResult | BaseException] = Queue(maxsize=1)
        self._thread: Thread | None = None
        self._closed = False

    def start(self, request: SigningRequest) -> None:
        if self._closed:
            raise RuntimeError("Signing transaction runner is closed.")
        if self._thread is not None:
            raise RuntimeError("A signing transaction is already running.")

        def run() -> None:
            try:
                self._completion.put(self._execute(request))
            except BaseException as exc:  # noqa: BLE001 - deliver worker failures to Qt thread
                self._completion.put(exc)

        self._thread = Thread(target=run, name="foliaseal-signing-transaction", daemon=True)
        self._thread.start()

    def is_running(self) -> bool:
        thread = self._thread
        return thread is not None and thread.is_alive()

    def poll_completion(self) -> SigningResult | BaseException | None:
        try:
            result = self._completion.get_nowait()
        except Empty:
            return None
        thread = self._thread
        if thread is not None:
            thread.join()
        self._thread = None
        return result

    def close(self) -> None:
        self._closed = True
        thread = self._thread
        if thread is not None:
            thread.join()
            self._thread = None

    def dispose(self) -> None:
        """Qt-composition cleanup alias."""
        self.close()


__all__ = ["SigningTransactionRunner", "ThreadSigningTransactionRunner"]
