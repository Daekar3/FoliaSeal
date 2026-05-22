from pathlib import Path

from PIL import Image

from foliaseal.application import SigningDraftWorkflow
from foliaseal.domain.models import SignatureRect
from foliaseal.presentation.qt.signature_preview_lifecycle import (
    QtCanonicalPreviewLifecycle,
)
from tests.support.phase3_builders import build_signature_appearance


class _FakePixmap:
    def __init__(self, path: str = "", width: int = 120, height: int = 80) -> None:
        self.path = path
        self.width = width
        self.height = height

    def isNull(self):  # noqa: N802
        return not self.path

    def scaled(self, width, height, *_args):  # noqa: N802
        if not self.path:
            return _FakePixmap("")
        aspect = self.width / self.height if self.height else 1.0
        if width / height > aspect:
            scaled_height = height
            scaled_width = max(1, int(height * aspect))
        else:
            scaled_width = width
            scaled_height = max(1, int(width / aspect))
        return _FakePixmap(self.path, scaled_width, scaled_height)


class _FakeQt:
    KeepAspectRatio = 1
    SmoothTransformation = 2


class _FakeRenderBackend:
    pass


def _workflow(tmp_path: Path) -> SigningDraftWorkflow:
    workflow = SigningDraftWorkflow(
        input_pdf_path=str(tmp_path / "input.pdf"),
        output_pdf_path=str(tmp_path / "output.pdf"),
        certificate_path=str(tmp_path / "cert.p12"),
        passphrase="secret",
        tsa_url="https://tsa.example.com",
        timestamp_required=True,
        certificate_alias="signing-cert",
    )
    workflow.set_signature_appearance(build_signature_appearance())
    workflow.set_signature_rect(
        SignatureRect(
            page_index=0,
            left_pt=24.0,
            bottom_pt=18.0,
            width_pt=180.0,
            height_pt=48.0,
        )
    )
    return workflow


def test_preview_lifecycle_requests_bordered_canonical_render(tmp_path: Path) -> None:
    preview_path = tmp_path / "preview.png"
    Image.new("RGBA", (120, 60), color=(255, 255, 255, 255)).save(preview_path)
    recorded_calls: list[dict[str, object]] = []

    def _render_snapshot(preview, **kwargs):
        recorded_calls.append(kwargs)
        from foliaseal.application.signing_preview_renderer import (
            CanonicalSignaturePreviewSnapshot,
        )

        return CanonicalSignaturePreviewSnapshot(
            image_path=str(preview_path),
            width_px=120,
            height_px=60,
            text_area_bounds_px={"x": 0, "y": 0, "width": 120, "height": 60},
            stamp_area_bounds_px=None,
            text_bounds_px={"x": 0, "y": 0, "width": 120, "height": 60},
            stamp_bounds_px=None,
        )

    lifecycle = QtCanonicalPreviewLifecycle(
        q_pixmap=_FakePixmap,
        qt=_FakeQt,
        render_backend_factory=_FakeRenderBackend,
        render_snapshot=_render_snapshot,
    )

    state = lifecycle.refresh(
        preview=_workflow(tmp_path).preview(),
        preview_scale=1.0,
        inner_body_width=100,
        inner_body_height=50,
        fallback_card_style="fallback-style",
    )

    assert recorded_calls
    assert recorded_calls[-1]["include_border"] is True
    assert recorded_calls[-1]["flatten_to_white"] is False
    assert state.render_label_visible is True
    assert state.snapshot is not None


def test_preview_lifecycle_reuses_one_render_backend(tmp_path: Path) -> None:
    preview_path = tmp_path / "preview.png"
    Image.new("RGBA", (120, 60), color=(255, 255, 255, 255)).save(preview_path)
    backend_construction_count = {"value": 0}
    captured_backends: list[object] = []

    class _CountingRenderBackend:
        def __init__(self) -> None:
            backend_construction_count["value"] += 1

    def _render_snapshot(preview, **kwargs):
        captured_backends.append(kwargs["render_backend"])
        from foliaseal.application.signing_preview_renderer import (
            CanonicalSignaturePreviewSnapshot,
        )

        return CanonicalSignaturePreviewSnapshot(
            image_path=str(preview_path),
            width_px=120,
            height_px=60,
            text_area_bounds_px={"x": 0, "y": 0, "width": 120, "height": 60},
            stamp_area_bounds_px=None,
            text_bounds_px={"x": 0, "y": 0, "width": 120, "height": 60},
            stamp_bounds_px=None,
        )

    lifecycle = QtCanonicalPreviewLifecycle(
        q_pixmap=_FakePixmap,
        qt=_FakeQt,
        render_backend_factory=_CountingRenderBackend,
        render_snapshot=_render_snapshot,
    )

    preview = _workflow(tmp_path).preview()
    for _ in range(5):
        lifecycle.refresh(
            preview=preview,
            preview_scale=1.0,
            inner_body_width=100,
            inner_body_height=50,
            fallback_card_style="fallback-style",
        )

    assert backend_construction_count["value"] == 1
    assert len(captured_backends) == 5
    assert all(backend is captured_backends[0] for backend in captured_backends)


def test_preview_lifecycle_cleans_up_replaced_snapshots(tmp_path: Path) -> None:
    created_dirs: list[Path] = []
    call_count = {"value": 0}

    def _render_snapshot(preview, **kwargs):
        index = call_count["value"]
        call_count["value"] += 1
        image_dir = tmp_path / f"foliaseal-canonical-preview-{index}"
        image_dir.mkdir()
        image_path = image_dir / "preview.png"
        Image.new("RGBA", (16, 16), color=(0, 0, 0, 255)).save(image_path)
        created_dirs.append(image_dir)
        from foliaseal.application.signing_preview_renderer import (
            CanonicalSignaturePreviewSnapshot,
        )

        return CanonicalSignaturePreviewSnapshot(
            image_path=str(image_path),
            width_px=16,
            height_px=16,
            text_area_bounds_px={"x": 0, "y": 0, "width": 16, "height": 16},
            stamp_area_bounds_px=None,
            text_bounds_px={"x": 0, "y": 0, "width": 16, "height": 16},
            stamp_bounds_px=None,
        )

    lifecycle = QtCanonicalPreviewLifecycle(
        q_pixmap=_FakePixmap,
        qt=_FakeQt,
        render_backend_factory=_FakeRenderBackend,
        render_snapshot=_render_snapshot,
    )
    preview = _workflow(tmp_path).preview()

    lifecycle.refresh(
        preview=preview,
        preview_scale=1.0,
        inner_body_width=100,
        inner_body_height=50,
        fallback_card_style="fallback-style",
    )
    first_snapshot = lifecycle.current_snapshot()
    assert first_snapshot is not None
    first_dir = Path(first_snapshot.image_path).parent
    assert first_dir.exists()

    lifecycle.refresh(
        preview=preview,
        preview_scale=1.0,
        inner_body_width=100,
        inner_body_height=50,
        fallback_card_style="fallback-style",
    )
    second_snapshot = lifecycle.current_snapshot()
    assert second_snapshot is not None
    second_dir = Path(second_snapshot.image_path).parent

    assert second_dir.exists()
    assert second_dir != first_dir
    assert not first_dir.exists()


def test_preview_lifecycle_keeps_only_latest_snapshot_after_many_refreshes(
    tmp_path: Path,
) -> None:
    created_dirs: list[Path] = []
    call_count = {"value": 0}

    def _render_snapshot(preview, **kwargs):
        index = call_count["value"]
        call_count["value"] += 1
        image_dir = tmp_path / f"foliaseal-canonical-preview-{index}"
        image_dir.mkdir()
        image_path = image_dir / "preview.png"
        Image.new("RGBA", (16, 16), color=(0, 0, 0, 255)).save(image_path)
        created_dirs.append(image_dir)
        from foliaseal.application.signing_preview_renderer import (
            CanonicalSignaturePreviewSnapshot,
        )

        return CanonicalSignaturePreviewSnapshot(
            image_path=str(image_path),
            width_px=16,
            height_px=16,
            text_area_bounds_px={"x": 0, "y": 0, "width": 16, "height": 16},
            stamp_area_bounds_px=None,
            text_bounds_px={"x": 0, "y": 0, "width": 16, "height": 16},
            stamp_bounds_px=None,
        )

    lifecycle = QtCanonicalPreviewLifecycle(
        q_pixmap=_FakePixmap,
        qt=_FakeQt,
        render_backend_factory=_FakeRenderBackend,
        render_snapshot=_render_snapshot,
    )
    preview = _workflow(tmp_path).preview()

    for _ in range(24):
        lifecycle.refresh(
            preview=preview,
            preview_scale=1.0,
            inner_body_width=100,
            inner_body_height=50,
            fallback_card_style="fallback-style",
        )

    current_snapshot = lifecycle.current_snapshot()
    assert current_snapshot is not None
    current_dir = Path(current_snapshot.image_path).parent
    assert current_dir.exists()
    assert sum(1 for path in created_dirs if path.exists()) == 1
    assert current_dir == created_dirs[-1]


def test_preview_lifecycle_falls_back_when_rendering_is_unavailable(tmp_path: Path) -> None:
    def _render_snapshot(preview, **kwargs):
        raise ValueError("cannot render")

    lifecycle = QtCanonicalPreviewLifecycle(
        q_pixmap=_FakePixmap,
        qt=_FakeQt,
        render_backend_factory=_FakeRenderBackend,
        render_snapshot=_render_snapshot,
    )

    state = lifecycle.refresh(
        preview=_workflow(tmp_path).preview(),
        preview_scale=1.0,
        inner_body_width=100,
        inner_body_height=50,
        fallback_card_style="fallback-style",
    )

    assert state.snapshot is None
    assert state.pixmap is None
    assert state.card_style == "fallback-style"
    assert state.render_label_visible is False
    assert lifecycle.current_snapshot() is None


def test_preview_lifecycle_falls_back_when_qt_render_backend_is_unavailable(
    tmp_path: Path,
) -> None:
    def _render_snapshot(preview, **kwargs):
        raise RuntimeError("QtPdf backend unavailable")

    lifecycle = QtCanonicalPreviewLifecycle(
        q_pixmap=_FakePixmap,
        qt=_FakeQt,
        render_backend_factory=_FakeRenderBackend,
        render_snapshot=_render_snapshot,
    )

    state = lifecycle.refresh(
        preview=_workflow(tmp_path).preview(),
        preview_scale=1.0,
        inner_body_width=100,
        inner_body_height=50,
        fallback_card_style="fallback-style",
    )

    assert state.snapshot is None
    assert state.pixmap is None
    assert state.card_style == "fallback-style"
    assert state.render_label_visible is False
    assert lifecycle.current_snapshot() is None


def test_preview_lifecycle_cleans_up_last_snapshot_on_dispose(tmp_path: Path) -> None:
    image_dir = tmp_path / "foliaseal-canonical-preview-final"
    image_dir.mkdir()
    image_path = image_dir / "preview.png"
    Image.new("RGBA", (16, 16), color=(0, 0, 0, 255)).save(image_path)

    def _render_snapshot(preview, **kwargs):
        from foliaseal.application.signing_preview_renderer import (
            CanonicalSignaturePreviewSnapshot,
        )

        return CanonicalSignaturePreviewSnapshot(
            image_path=str(image_path),
            width_px=16,
            height_px=16,
            text_area_bounds_px={"x": 0, "y": 0, "width": 16, "height": 16},
            stamp_area_bounds_px=None,
            text_bounds_px={"x": 0, "y": 0, "width": 16, "height": 16},
            stamp_bounds_px=None,
        )

    lifecycle = QtCanonicalPreviewLifecycle(
        q_pixmap=_FakePixmap,
        qt=_FakeQt,
        render_backend_factory=_FakeRenderBackend,
        render_snapshot=_render_snapshot,
    )

    lifecycle.refresh(
        preview=_workflow(tmp_path).preview(),
        preview_scale=1.0,
        inner_body_width=100,
        inner_body_height=50,
        fallback_card_style="fallback-style",
    )
    assert image_dir.exists()

    lifecycle.dispose()

    assert lifecycle.current_snapshot() is None
    assert not image_dir.exists()
