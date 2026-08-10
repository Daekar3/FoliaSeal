from foliaseal.application.signing_executor import LazySigningRequestExecutor


class _FakeExecutor:
    def __init__(self) -> None:
        self.requests = []

    def execute(self, request):
        self.requests.append(request)
        return "result"


def test_lazy_signing_executor_constructs_backend_once_on_first_request() -> None:
    builds = []
    delegate = _FakeExecutor()
    executor = LazySigningRequestExecutor(factory=lambda: builds.append(True) or delegate)

    assert builds == []
    assert executor.execute("first") == "result"
    assert executor.execute("second") == "result"

    assert builds == [True]
    assert delegate.requests == ["first", "second"]
