from types import SimpleNamespace

import pytest

from foliaseal.application.visible_signature_fit_policy import (
    VisibleSignatureRenderedFitPolicy,
    VisibleSignatureRenderedFitRequest,
)
from foliaseal.domain.models import SignatureLayoutTemplate, SignatureStampPosition


def _request(
    *,
    layout_template: SignatureLayoutTemplate = SignatureLayoutTemplate.SINGLE_LINE,
    stamp_position: SignatureStampPosition = SignatureStampPosition.LEFT,
    image_stamp_path: str | None = "stamp.png",
    fit_issues: tuple[object, ...] = (object(),),
) -> VisibleSignatureRenderedFitRequest:
    appearance = SimpleNamespace(
        layout_template=layout_template,
        stamp_position=stamp_position,
        image_stamp_path=image_stamp_path,
    )
    plan = SimpleNamespace(fit_issues=fit_issues)
    return VisibleSignatureRenderedFitRequest(
        signature_rect=SimpleNamespace(),
        appearance=appearance,
        stamp_text="signed",
        layout_plan=plan,
    )


class _Probe:
    def __init__(self, *, single: bool = False, multi: bool = False) -> None:
        self.single = single
        self.multi = multi
        self.calls: list[str] = []

    def single_line_fits(self, request) -> bool:
        del request
        self.calls.append("single")
        return self.single

    def horizontal_multi_line_fits(self, request) -> bool:
        del request
        self.calls.append("multi")
        return self.multi


def test_policy_accepts_structurally_fit_plan_without_probe_call() -> None:
    probe = _Probe(single=False, multi=False)
    decision = VisibleSignatureRenderedFitPolicy.decide(
        _request(fit_issues=()),
        probe=probe,
    )

    assert decision.accepted
    assert probe.calls == []


@pytest.mark.parametrize(
    ("layout_template", "stamp_position", "expected_call"),
    [
        (SignatureLayoutTemplate.SINGLE_LINE, SignatureStampPosition.TOP, "single"),
        (SignatureLayoutTemplate.SINGLE_LINE, SignatureStampPosition.RIGHT, "single"),
        (SignatureLayoutTemplate.MULTI_LINE, SignatureStampPosition.LEFT, "multi"),
        (SignatureLayoutTemplate.MULTI_LINE, SignatureStampPosition.RIGHT, "multi"),
    ],
)
def test_policy_dispatches_only_relevant_rendered_fallback(
    layout_template: SignatureLayoutTemplate,
    stamp_position: SignatureStampPosition,
    expected_call: str,
) -> None:
    probe = _Probe(single=True, multi=True)
    decision = VisibleSignatureRenderedFitPolicy.decide(
        _request(
            layout_template=layout_template,
            stamp_position=stamp_position,
        ),
        probe=probe,
    )

    assert decision.accepted
    assert probe.calls == [expected_call]


def test_policy_rejects_unsupported_structural_fallback_without_probe_call() -> None:
    probe = _Probe(single=True, multi=True)
    decision = VisibleSignatureRenderedFitPolicy.decide(
        _request(
            layout_template=SignatureLayoutTemplate.MULTI_LINE,
            stamp_position=SignatureStampPosition.TOP,
        ),
        probe=probe,
    )

    assert not decision.accepted
    assert probe.calls == []
