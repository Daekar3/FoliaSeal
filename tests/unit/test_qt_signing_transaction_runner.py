from pathlib import Path
from threading import Event
from time import sleep

from foliaseal.domain.models import SigningResult
from foliaseal.presentation.qt.signing_transaction_runner import (
    ThreadSigningTransactionRunner,
)
from tests.support.signing_builders import build_signing_request


def test_thread_runner_delivers_completion_and_closes_owned_worker(tmp_path: Path) -> None:
    started = Event()
    release = Event()
    result = SigningResult(
        success=True,
        failure_code=None,
        message="Signing completed successfully.",
    )

    def execute(_request):
        started.set()
        release.wait(timeout=2)
        return result

    runner = ThreadSigningTransactionRunner(execute)
    runner.start(build_signing_request(tmp_path))
    assert started.wait(timeout=1)
    assert runner.is_running() is True
    assert runner.poll_completion() is None

    release.set()
    completion = None
    for _ in range(100):
        completion = runner.poll_completion()
        if completion is not None:
            break
        sleep(0.01)
    assert completion == result
    assert runner.is_running() is False
    runner.close()
    runner.close()


def test_thread_runner_delivers_worker_exception(tmp_path: Path) -> None:
    def execute(_request):
        raise ValueError("boom")

    runner = ThreadSigningTransactionRunner(execute)
    runner.start(build_signing_request(tmp_path))

    completion = None
    for _ in range(100):
        completion = runner.poll_completion()
        if completion is not None:
            break
    assert isinstance(completion, ValueError)
    runner.close()
