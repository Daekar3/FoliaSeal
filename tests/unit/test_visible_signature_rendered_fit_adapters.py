from pathlib import Path
from types import SimpleNamespace

from foliaseal.application import visible_signature_rendered_fit_adapters as rendered_fit_adapters
from foliaseal.application.visible_signature_fit_policy import VisibleSignatureRenderedFitRequest
from foliaseal.application.visible_signature_rendered_fit_adapters import (
    PyHankoRenderedFitProbe,
    _cleanup_canonical_preview_snapshot,
)
from foliaseal.domain.models import (
    SignatureBoxStyle,
    SignatureLayoutTemplate,
    SignatureStampPosition,
    SignatureTextStyle,
)


def _request(*, render_port: object | None = None) -> VisibleSignatureRenderedFitRequest:
    return VisibleSignatureRenderedFitRequest(
        signature_rect=SimpleNamespace(
            page_index=0,
            left_pt=10.0,
            bottom_pt=20.0,
            width_pt=120.0,
            height_pt=40.0,
        ),
        appearance=SimpleNamespace(
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=SignatureStampPosition.LEFT,
            image_stamp_path=None,
            signer_label_prefix="Signed by",
            datetime_format="%Y-%m-%d",
            show_field_names=True,
            text_style=SignatureTextStyle(
                font_family="Helvetica",
                font_size_pt=10.0,
                bold=False,
                italic=False,
                text_color_hex="#000000",
            ),
            box_style=SignatureBoxStyle(
                show_border=True,
                border_color_hex="#000000",
                border_width_pt=1.0,
                background_color_hex="#ffffff",
            ),
        ),
        stamp_text="signed",
        layout_plan=SimpleNamespace(fit_issues=(object(),)),
        render_port=render_port,
    )


def test_probe_caches_single_line_decision_by_render_request(monkeypatch) -> None:
    probe = PyHankoRenderedFitProbe()
    calls = 0

    def fake_uncached(request) -> bool:
        nonlocal calls
        del request
        calls += 1
        return True

    monkeypatch.setattr(probe, "_single_line_fits_uncached", fake_uncached)
    request = _request()

    assert probe.single_line_fits(request)
    assert probe.single_line_fits(request)
    assert calls == 1


def test_probe_level_render_port_is_normalized_before_cache_and_probe_call(monkeypatch) -> None:
    render_port = object()
    probe = PyHankoRenderedFitProbe(render_port=render_port)
    seen: list[object | None] = []

    def fake_uncached(request) -> bool:
        seen.append(request.render_port)
        return True

    monkeypatch.setattr(probe, "_single_line_fits_uncached", fake_uncached)

    assert probe.single_line_fits(_request())
    assert seen == [render_port]


def test_probe_evicts_bounded_cache_before_adding_257th_request(monkeypatch) -> None:
    probe = PyHankoRenderedFitProbe()
    calls = 0

    def fake_uncached(request) -> bool:
        nonlocal calls
        del request
        calls += 1
        return True

    monkeypatch.setattr(probe, "_single_line_fits_uncached", fake_uncached)
    render_ports = [object() for _ in range(257)]
    for render_port in render_ports:
        assert probe.single_line_fits(_request(render_port=render_port))

    assert calls == 257
    assert probe.single_line_fits(_request(render_port=render_ports[-1]))
    assert calls == 257
    assert probe.single_line_fits(_request(render_port=render_ports[0]))
    assert calls == 258


def test_probe_cleans_snapshot_when_rendered_fit_analysis_raises(monkeypatch, tmp_path) -> None:
    owned = tmp_path / "foliaseal-canonical-preview-exception"
    owned.mkdir()
    snapshot = SimpleNamespace(
        image_path=str(owned / "preview.png"),
        text_area_bounds_px={"x": 0, "y": 0, "width": 20, "height": 10},
        stamp_area_bounds_px=None,
        stamp_bounds_px=None,
        text_bounds_px={"x": 0, "y": 0, "width": 20, "height": 10},
        width_px=20,
        height_px=10,
    )
    monkeypatch.setattr(
        rendered_fit_adapters,
        "signing_draft_preview_for_stamp_text",
        lambda **kwargs: object(),
    )
    monkeypatch.setattr(
        rendered_fit_adapters._signing_preview_renderer,
        "render_canonical_signature_preview",
        lambda *args, **kwargs: snapshot,
    )
    monkeypatch.setattr(
        rendered_fit_adapters,
        "_single_line_text_only_ink_bounds",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("analysis failed")),
    )

    assert not PyHankoRenderedFitProbe().single_line_fits(_request())
    assert not owned.exists()


def test_cleanup_removes_only_owned_canonical_preview_directory(tmp_path) -> None:
    owned = tmp_path / "foliaseal-canonical-preview-owned"
    owned.mkdir()
    owned_image = owned / "preview.png"
    owned_image.touch()
    _cleanup_canonical_preview_snapshot(SimpleNamespace(image_path=str(owned_image)))
    assert not owned.exists()

    unrelated = tmp_path / "unrelated"
    unrelated.mkdir()
    unrelated_image = unrelated / "preview.png"
    unrelated_image.touch()
    _cleanup_canonical_preview_snapshot(SimpleNamespace(image_path=str(unrelated_image)))
    assert Path(unrelated_image).exists()
