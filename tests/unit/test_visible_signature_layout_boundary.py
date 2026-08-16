from __future__ import annotations

import inspect
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest

from foliaseal.application import (
    horizontal_signature_reservation,
    signing_draft_workflow,
    signing_preview_renderer,
    visible_signature_artifact_adapters,
    visible_signature_layout,
    visible_signature_layout_adapters,
)
from foliaseal.application.sign_pdf_use_case import SigningBackendAppearance
from foliaseal.application.signature_text_measurement import PreparedTextBox
from foliaseal.application.visible_signature_layout import (
    TextMetrics,
    VisibleSignatureLayoutOptions,
    VisibleSignatureLayoutRequest,
    VisibleSignatureLayoutService,
)
from foliaseal.application.visible_signature_layout_adapters import PyHankoTextMeasurer
from foliaseal.domain.models import (
    SignatureLayoutTemplate,
    SignatureStampPosition,
    SignatureTextStyle,
)
from foliaseal.presentation.qt import signature_preview_layout
from tests.support.signing_builders import build_signature_appearance, build_signature_rect


@dataclass
class _CountingTextMeasurer:
    calls: int = 0

    def measure(self, _text: str, _text_style) -> TextMetrics:
        self.calls += 1
        return TextMetrics(width_pt=72, height_pt=18, line_count=1)


@dataclass(frozen=True)
class _LayoutTestRequest:
    appearance: SigningBackendAppearance
    signature_rect: object
    stamp_text: str
    include_stamp: bool = True
    use_horizontal_ink_reservation: bool = True
    text_measurer: object | None = None
    image_probe: object | None = None
    ink_measurer: object | None = None


def _appearance() -> SigningBackendAppearance:
    return SigningBackendAppearance.from_signature_appearance(
        build_signature_appearance(signer_label_prefix="Digitally signed by")
    )


def _prepare(request: _LayoutTestRequest):
    return VisibleSignatureLayoutService(
        text_measurer=request.text_measurer,
        image_probe=request.image_probe,
        ink_measurer=request.ink_measurer,
    ).prepare(
        VisibleSignatureLayoutRequest(
            appearance=request.appearance,
            signature_rect=request.signature_rect,
            stamp_text=request.stamp_text,
            options=VisibleSignatureLayoutOptions(
                include_stamp=request.include_stamp,
                horizontal_ink_policy=(
                    "auto" if request.use_horizontal_ink_reservation else "disabled"
                ),
            ),
            ink_measurer=request.ink_measurer,
        )
    )


def test_neutral_boundary_returns_one_plan_and_json_ready_snapshot() -> None:
    measurer = _CountingTextMeasurer()
    result = _prepare(
        _LayoutTestRequest(
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


def test_pyhanko_text_measurer_delegates_to_injected_atomic_engine() -> None:
    class _FakeEngine:
        def prepare(self, text: str, text_style) -> PreparedTextBox:
            assert text == "Measured"
            assert text_style == _appearance().text_style
            return PreparedTextBox(
                metrics=TextMetrics(width_pt=41, height_pt=13, line_count=1),
                render_style=object(),
            )

    measured = PyHankoTextMeasurer(engine=_FakeEngine()).measure(
        "Measured",
        _appearance().text_style,
    )

    assert measured == TextMetrics(width_pt=41, height_pt=13, line_count=1)


def test_neutral_boundary_preserves_existing_fit_diagnostic() -> None:
    result = _prepare(
        _LayoutTestRequest(
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


def test_planner_facade_returns_the_shared_neutral_plan() -> None:
    request = _LayoutTestRequest(
        appearance=_appearance(),
        signature_rect=build_signature_rect(page_index=0, width_pt=420, height_pt=86),
        stamp_text="Digitally signed by\nMorgan Ellery",
    )

    result = _prepare(request)

    assert result.fit_issues == ()
    assert result.reservation_snapshot["text_area_width_pt"] > 0


def test_planner_facade_uses_injected_measurement_collaborators() -> None:
    measurer = _CountingTextMeasurer()
    VisibleSignatureLayoutService(text_measurer=measurer).prepare(
        VisibleSignatureLayoutRequest(
            appearance=_appearance(),
            signature_rect=build_signature_rect(page_index=0, width_pt=420, height_pt=86),
            stamp_text="Digitally signed by\nMorgan Ellery",
        )
    )

    assert measurer.calls == 1


def test_signing_adapter_consumes_precomputed_plan_without_remeasuring() -> None:
    appearance = _appearance()
    plan = _prepare(
        _LayoutTestRequest(
            appearance=appearance,
            signature_rect=build_signature_rect(
                page_index=0,
                width_pt=420,
                height_pt=86,
            ),
            stamp_text="Digitally signed by\nMorgan Ellery",
        )
    )

    style = plan.signing()

    assert style.layout_plan == plan.layout_plan


def test_canonical_preview_adapter_consumes_precomputed_plan_without_remeasuring() -> None:
    appearance = _appearance()
    rect = build_signature_rect(page_index=0, width_pt=420, height_pt=86)
    plan = _prepare(
        _LayoutTestRequest(
            appearance=appearance,
            signature_rect=rect,
            stamp_text="Digitally signed by\nMorgan Ellery",
        )
    )

    preview = plan.preview()

    assert preview.layout_plan == plan.layout_plan


def test_planner_adapter_methods_consume_the_same_precomputed_plan() -> None:
    appearance = _appearance()
    rect = build_signature_rect(page_index=0, width_pt=420, height_pt=86)
    plan = _prepare(
        _LayoutTestRequest(
            appearance=appearance,
            signature_rect=rect,
            stamp_text="Digitally signed by\nMorgan Ellery",
        )
    )

    signing = plan.signing()
    preview = plan.preview()

    assert signing.layout_plan == plan.layout_plan
    assert preview.layout_plan == plan.layout_plan


def test_prepare_once_materializes_both_targets_without_replanning() -> None:
    measurer = _CountingTextMeasurer()
    preparation = VisibleSignatureLayoutService(text_measurer=measurer).prepare(
        VisibleSignatureLayoutRequest(
            appearance=_appearance(),
            signature_rect=build_signature_rect(page_index=0, width_pt=420, height_pt=86),
            stamp_text="Digitally signed by\nMorgan Ellery",
            options=VisibleSignatureLayoutOptions(allow_fit_issues=True),
        )
    )

    base_plan = preparation.layout_plan
    signing = preparation.signing()
    preview = preparation.preview()

    assert measurer.calls == 1
    assert signing.layout_plan is base_plan
    assert preview.layout_plan is base_plan
    assert preparation.signing() is signing
    assert preparation.preview() is preview


def test_compact_preview_derivation_is_prepared_once_and_memoized(tmp_path) -> None:
    from PIL import Image

    stamp_path = tmp_path / "stamp.png"
    Image.new("RGBA", (400, 100), color=(0, 0, 0, 160)).save(stamp_path)
    appearance = SigningBackendAppearance.from_signature_appearance(
        build_signature_appearance(
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=SignatureStampPosition.LEFT,
            image_stamp_path=str(stamp_path),
        )
    )
    measurer = _CountingTextMeasurer()
    preparation = VisibleSignatureLayoutService(text_measurer=measurer).prepare(
        VisibleSignatureLayoutRequest(
            appearance=appearance,
            signature_rect=build_signature_rect(page_index=0, width_pt=40, height_pt=24),
            stamp_text="Digitally signed by\nMorgan Ellery",
            options=VisibleSignatureLayoutOptions(allow_fit_issues=True),
        )
    )

    assert preparation.preview().stamp_suppressed is True
    assert preparation.preview() is preparation.preview()
    assert preparation.signing().layout_plan is preparation.layout_plan
    assert measurer.calls == 2


def test_horizontal_reservation_has_no_backend_private_color_dependency() -> None:
    source = inspect.getsource(horizontal_signature_reservation)

    assert "signing_backend import _text_style_color_rgba" not in source
    assert "visible_signature_color import text_style_color_rgba" in source


def test_layout_module_uses_the_public_text_measurement_port() -> None:
    source = inspect.getsource(visible_signature_layout)

    assert "_build_text_box_style" not in source
    assert "_measure_text_box_dimensions" not in source


def test_layout_adapter_does_not_reach_back_into_signing_backend() -> None:
    source = inspect.getsource(visible_signature_layout_adapters)

    assert "signing_backend" not in source


def test_artifact_adapter_owns_concrete_metrics_and_style_helpers() -> None:
    style = SignatureTextStyle(
        font_family="Serif",
        font_size_pt=8.5,
        bold=False,
        italic=True,
        text_color_hex="#123456",
    )
    prepared = visible_signature_artifact_adapters.PyHankoSignatureTextBoxEngine().prepare(
        "Line 1\nLine 2\nLine 3",
        style,
    )

    assert prepared.render_style.font_size == 17 / 2
    assert prepared.metrics.line_count == 3
    assert prepared.metrics.height_pt >= 27
    assert prepared.render_style.text_color == pytest.approx(
        (0x12 / 255, 0x34 / 255, 0x56 / 255)
    )


def test_artifact_adapter_import_isolated_from_signing_backend() -> None:
    source = inspect.getsource(visible_signature_artifact_adapters)
    assert "signing_backend" not in source

    script = """
import sys
import foliaseal.application.visible_signature_artifact_adapters
if 'foliaseal.application.signing_backend' in sys.modules:
    raise SystemExit('backend imported')
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_prepared_materializer_preserves_options_and_memoizes_targets() -> None:
    calls: list[dict[str, object]] = []

    class _RecordingMaterializer:
        def build_stamp_style(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(inner_content_layout="content", background_layout="background")

    preparation = VisibleSignatureLayoutService(
        appearance_materializer=_RecordingMaterializer(),
    ).prepare(
        VisibleSignatureLayoutRequest(
            appearance=_appearance(),
            signature_rect=build_signature_rect(page_index=0, width_pt=420, height_pt=86),
            stamp_text="Digitally signed by\nMorgan Ellery",
            stamp_background=object(),
            options=VisibleSignatureLayoutOptions(
                include_border=False,
                include_background=False,
            ),
        )
    )

    signing = preparation.signing()
    assert preparation.signing() is signing
    preview = preparation.preview()
    assert preparation.preview() is preview
    assert len(calls) == 2
    assert calls[0]["layout_plan"] is preparation.layout_plan
    assert calls[0]["include_border"] is False
    assert calls[0]["include_background"] is False
    assert calls[1]["layout_plan"] is preparation.layout_plan


def test_neutral_layout_module_import_isolation() -> None:
    script = """
import importlib
import sys
import foliaseal.application.visible_signature_layout
blocked = (
    'PIL',
    'pyhanko',
    'PyQt',
    'foliaseal.application.signing_backend',
)
loaded = sorted(
    name for name in sys.modules
    if any(name == prefix or name.startswith(prefix + '.') for prefix in blocked)
)
if loaded:
    raise SystemExit(','.join(loaded))
"""
    environment = os.environ.copy()
    source_root = str(Path(__file__).resolve().parents[2] / "src")
    environment["PYTHONPATH"] = os.pathsep.join(
        (source_root, environment.get("PYTHONPATH", ""))
    ).rstrip(os.pathsep)
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout


@pytest.mark.parametrize(
    "imports",
    [
        "import foliaseal.application.visible_signature_layout_adapters\n"
        "import foliaseal.application.signing_backend",
        "import foliaseal.application.signing_backend\n"
        "import foliaseal.application.visible_signature_layout_adapters",
    ],
)
def test_layout_adapter_and_backend_import_order_is_stable(imports: str) -> None:
    completed = subprocess.run(
        [sys.executable, "-c", imports],
        check=False,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_production_consumers_use_public_layout_adapter_names() -> None:
    preview_source = inspect.getsource(signing_preview_renderer)
    workflow_source = inspect.getsource(signing_draft_workflow)
    qt_source = inspect.getsource(signature_preview_layout)

    assert "signing_backend import (\n    RoundedBorderTextStampStyle" not in preview_source
    assert "_stamp_background_for_path" not in preview_source
    assert "_visible_signature_fit_issues_for_stamp_text" not in workflow_source
    assert "_stamp_background_for_path" not in workflow_source
    assert "signing_backend" not in qt_source


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
    baseline = service.prepare(
        VisibleSignatureLayoutRequest(
            appearance=appearance,
            signature_rect=rect,
            stamp_text="Digitally signed by\nMorgan Ellery",
            options=options,
        )
    ).signing()
    with_stamp = service.prepare(
        VisibleSignatureLayoutRequest(
            appearance=appearance,
            signature_rect=rect,
            stamp_text="Digitally signed by\nMorgan Ellery",
            stamp_background=object(),
            options=options,
        )
    ).signing()

    assert getattr(with_stamp.background_layout.margins, margin_name) > getattr(
        baseline.background_layout.margins,
        margin_name,
    )


@pytest.mark.parametrize("include_stamp", [True, False])
def test_boundary_controls_stamp_presence_without_changing_neutral_contract(
    include_stamp: bool,
) -> None:
    result = _prepare(
        _LayoutTestRequest(
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
