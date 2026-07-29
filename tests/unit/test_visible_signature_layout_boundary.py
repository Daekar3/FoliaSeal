from __future__ import annotations

import inspect
from dataclasses import dataclass

import pytest

from foliaseal.application import horizontal_signature_reservation
from foliaseal.application.sign_pdf_use_case import SigningBackendAppearance
from foliaseal.application.visible_signature_layout import (
    TextMetrics,
    VisibleSignatureLayoutBoundary,
    VisibleSignatureLayoutOptions,
    VisibleSignatureLayoutService,
    VisibleSignaturePlanRequest,
)
from foliaseal.domain.models import SignatureLayoutTemplate, SignatureStampPosition
from tests.support.phase3_builders import build_signature_appearance, build_signature_rect


@dataclass
class _CountingTextMeasurer:
    calls: int = 0

    def measure(self, _text: str, _text_style) -> TextMetrics:
        self.calls += 1
        return TextMetrics(width_pt=72, height_pt=18, line_count=1)


def _appearance() -> SigningBackendAppearance:
    return SigningBackendAppearance.from_signature_appearance(
        build_signature_appearance(signer_label_prefix="Digitally signed by")
    )


def test_neutral_boundary_returns_one_plan_and_json_ready_snapshot() -> None:
    measurer = _CountingTextMeasurer()
    result = VisibleSignatureLayoutBoundary().plan(
        VisibleSignaturePlanRequest(
            appearance=_appearance(),
            signature_rect=build_signature_rect(
                page_index=0,
                width_pt=420,
                height_pt=86,
            ),
            stamp_text="Digitally signed by\nMorgan Ellery",
            text_measurer=measurer,
        )
    )

    assert measurer.calls == 1
    assert result.layout_plan.fit_issues == ()
    assert result.fit_issues == ()
    assert result.reservation_snapshot["text_area_width_pt"] > 0
    assert result.reservation_snapshot["fit_issue_codes"] == []
    assert not hasattr(result, "stamp_style")


def test_neutral_boundary_preserves_existing_fit_diagnostic() -> None:
    result = VisibleSignatureLayoutBoundary().plan(
        VisibleSignaturePlanRequest(
            appearance=_appearance(),
            signature_rect=build_signature_rect(
                page_index=0,
                width_pt=24,
                height_pt=18,
            ),
            stamp_text="A very long visible signature line that cannot fit",
        )
    )

    assert result.fit_issues
    assert result.fit_issues[0].code == "visible_signature_layout_unavailable"
    assert "does not fit inside the selected rectangle" in result.fit_issues[0].message


def test_signing_adapter_consumes_precomputed_plan_without_remeasuring() -> None:
    appearance = _appearance()
    plan = VisibleSignatureLayoutBoundary().plan(
        VisibleSignaturePlanRequest(
            appearance=appearance,
            signature_rect=build_signature_rect(
                page_index=0,
                width_pt=420,
                height_pt=86,
            ),
            stamp_text="Digitally signed by\nMorgan Ellery",
        )
    )

    class _FailingTextMeasurer:
        def measure(self, _text: str, _text_style) -> TextMetrics:
            raise AssertionError("the supplied plan should avoid a second planning pass")

    style = VisibleSignatureLayoutService(
        text_measurer=_FailingTextMeasurer(),
    ).pyhanko_style_for_signing(
        appearance=appearance,
        stamp_text="Digitally signed by\nMorgan Ellery",
        stamp_background=None,
        signature_rect=build_signature_rect(
            page_index=0,
            width_pt=420,
            height_pt=86,
        ),
        options=VisibleSignatureLayoutOptions(allow_fit_issues=True),
        layout_plan=plan.layout_plan,
    )

    assert style.layout_plan == plan.layout_plan


def test_canonical_preview_adapter_consumes_precomputed_plan_without_remeasuring() -> None:
    appearance = _appearance()
    rect = build_signature_rect(page_index=0, width_pt=420, height_pt=86)
    plan = VisibleSignatureLayoutBoundary().plan(
        VisibleSignaturePlanRequest(
            appearance=appearance,
            signature_rect=rect,
            stamp_text="Digitally signed by\nMorgan Ellery",
        )
    )

    class _FailingTextMeasurer:
        def measure(self, _text: str, _text_style) -> TextMetrics:
            raise AssertionError("the supplied plan should avoid a second planning pass")

    preview = VisibleSignatureLayoutService(
        text_measurer=_FailingTextMeasurer(),
    ).pyhanko_style_for_canonical_preview(
        appearance=appearance,
        stamp_text="Digitally signed by\nMorgan Ellery",
        stamp_background=None,
        signature_rect=rect,
        options=VisibleSignatureLayoutOptions(allow_fit_issues=True),
        layout_plan=plan.layout_plan,
    )

    assert preview.layout_plan == plan.layout_plan


def test_horizontal_reservation_has_no_backend_private_color_dependency() -> None:
    source = inspect.getsource(horizontal_signature_reservation)

    assert "phase3_signing_backend import _text_style_color_rgba" not in source
    assert "visible_signature_color import text_style_color_rgba" in source


@pytest.mark.parametrize(
    ("layout_template", "stamp_position", "image_size", "margin_name"),
    [
        (SignatureLayoutTemplate.MULTI_LINE, SignatureStampPosition.TOP, (40, 12), "top"),
        (
            SignatureLayoutTemplate.WRAPPED_BLOCK,
            SignatureStampPosition.BOTTOM,
            (12, 40),
            "bottom",
        ),
        (
            SignatureLayoutTemplate.WRAPPED_BLOCK,
            SignatureStampPosition.RIGHT,
            (40, 12),
            "right",
        ),
        (
            SignatureLayoutTemplate.WRAPPED_BLOCK,
            SignatureStampPosition.LEFT,
            (40, 12),
            "left",
        ),
    ],
)
def test_public_signing_adapter_preserves_stamp_border_facing_inset(
    tmp_path,
    layout_template: SignatureLayoutTemplate,
    stamp_position: SignatureStampPosition,
    image_size: tuple[int, int],
    margin_name: str,
) -> None:
    image_path = tmp_path / "stamp.png"
    from PIL import Image

    Image.new("RGBA", image_size, color=(0, 0, 0, 255)).save(image_path)
    appearance = SigningBackendAppearance.from_signature_appearance(
        build_signature_appearance(
            layout_template=layout_template,
            stamp_position=stamp_position,
            image_stamp_path=str(image_path),
        )
    )
    rect = build_signature_rect(page_index=0, width_pt=260, height_pt=62)
    service = VisibleSignatureLayoutService()
    options = VisibleSignatureLayoutOptions(allow_fit_issues=True)
    baseline = service.pyhanko_style_for_signing(
        appearance=appearance,
        stamp_text="Digitally signed by\nMorgan Ellery",
        stamp_background=None,
        signature_rect=rect,
        options=options,
    )
    with_stamp = service.pyhanko_style_for_signing(
        appearance=appearance,
        stamp_text="Digitally signed by\nMorgan Ellery",
        stamp_background=object(),
        signature_rect=rect,
        options=options,
    )

    assert getattr(with_stamp.background_layout.margins, margin_name) > getattr(
        baseline.background_layout.margins,
        margin_name,
    )


@pytest.mark.parametrize("include_stamp", [True, False])
def test_boundary_controls_stamp_presence_without_changing_neutral_contract(
    include_stamp: bool,
) -> None:
    result = VisibleSignatureLayoutBoundary().plan(
        VisibleSignaturePlanRequest(
            appearance=_appearance(),
            signature_rect=build_signature_rect(
                page_index=0,
                width_pt=420,
                height_pt=86,
            ),
            stamp_text="Digitally signed by\nMorgan Ellery",
            include_stamp=include_stamp,
        )
    )

    assert result.layout_plan.has_visible_stamp_image is False
    assert set(result.reservation_snapshot) >= {
        "container_width_pt",
        "container_height_pt",
        "fit_issue_codes",
    }
