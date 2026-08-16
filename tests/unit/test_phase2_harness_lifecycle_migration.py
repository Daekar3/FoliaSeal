from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import foliaseal.presentation.qt.phase2_harness as phase2_module
from foliaseal.presentation.qt.interactive_harness_qt_lifecycle import HarnessQtSurface


class _Layout:
    def __init__(self, parent=None):
        self.items = []
        if parent is not None:
            parent.layout = self

    def addLayout(self, layout, *args):  # noqa: N802
        self.items.append((layout, args))

    def addWidget(self, widget, *args):  # noqa: N802
        self.items.append((widget, args))

    def addStretch(self, value):  # noqa: N802
        self.items.append(("stretch", value))


class _Widget:
    def __init__(self):
        self.layout = None


class _Signal:
    def connect(self, callback):
        self.callback = callback


class _Button:
    def __init__(self, _label):
        self.clicked = _Signal()


class _Label:
    def __init__(self, text=""):
        self._text = text

    def setWordWrap(self, _value):  # noqa: N802
        return None

    def setText(self, value):  # noqa: N802
        self._text = value


class _Status:
    def setReadOnly(self, _value):  # noqa: N802
        return None

    def setMaximumBlockCount(self, _value):  # noqa: N802
        return None

    def appendPlainText(self, _value):  # noqa: N802
        return None


class _Bindings:
    q_widget = _Widget
    q_v_box_layout = _Layout
    q_h_box_layout = _Layout
    q_label = _Label
    q_plain_text_edit = _Status
    q_push_button = _Button


class _Lifecycle:
    def __init__(self, _bindings):
        self.events = []
        self.surface = HarnessQtSurface(
            app=SimpleNamespace(),
            window=SimpleNamespace(),
            central=SimpleNamespace(),
            toolbar=_Layout(),
            body=_Layout(),
        )

    def start(self, *, spec):
        self.events.append(("start", spec))
        return self.surface

    def mount(self, surface, widget):
        self.events.append(("mount", widget))
        surface.body.addWidget(widget, 1)

    def show(self, _surface):
        self.events.append(("show",))

    def exec(self, _surface):
        self.events.append(("exec",))
        return 0

    def close(self, _surface):
        self.events.append(("close",))


class _Backend:
    def diagnostics(self):
        return SimpleNamespace(available=True, message="ok")


class _Workflow:
    def __init__(self, **_kwargs):
        self.timing_tracker = SimpleNamespace(
            snapshot=lambda: SimpleNamespace(
                first_render_ms=12.5,
                sample_count=0,
                navigation_samples_ms=(),
            ),
            navigation_samples_ms=(),
        )
        self.snapshot = None


class _Viewer:
    def refresh(self):
        return None

    def setFocus(self):  # noqa: N802
        return None

    def viewport(self):
        return SimpleNamespace(width=lambda: 100, height=lambda: 100)

    def go_to_previous_page(self):
        return None

    def go_to_next_page(self):
        return None

    def reset_zoom_view(self):
        return None


def _patch_phase2_dependencies(monkeypatch, *, build_viewer):
    lifecycle = _Lifecycle
    monkeypatch.setattr(phase2_module, "_load_qt_harness_bindings", lambda: _Bindings)
    monkeypatch.setattr(phase2_module, "_load_page_count", lambda **_kwargs: 1)
    monkeypatch.setattr(phase2_module, "QtPdfRenderBackend", _Backend)
    monkeypatch.setattr(phase2_module, "ViewerWorkflow", _Workflow)
    monkeypatch.setattr(phase2_module, "build_qt_pdf_viewer_widget", build_viewer)
    return lifecycle


def test_phase2_harness_uses_shared_lifecycle_and_preserves_capture(
    monkeypatch,
    tmp_path: Path,
) -> None:
    lifecycle_instances = []

    def lifecycle_factory(bindings):
        lifecycle = _Lifecycle(bindings)
        lifecycle_instances.append(lifecycle)
        return lifecycle

    _patch_phase2_dependencies(
        monkeypatch,
        build_viewer=lambda **_kwargs: _Viewer(),
    )
    source = tmp_path / "input.pdf"
    source.write_bytes(b"pdf")
    checklist = tmp_path / "checklist.md"
    checklist.write_text("# checklist\n", encoding="utf-8")

    capture = phase2_module.run_phase2_viewer_harness(
        pdf_path=str(source),
        summary_json_path=str(tmp_path / "summary.json"),
        evidence_command_path=str(tmp_path / "evidence.txt"),
        checklist_results_path=str(tmp_path / "results.md"),
        checklist_template_path=str(checklist),
        lifecycle_factory=lifecycle_factory,
    )

    assert capture.first_render_ms == 12.5
    assert [event[0] for event in lifecycle_instances[0].events] == [
        "start",
        "mount",
        "show",
        "exec",
        "close",
    ]
    spec = lifecycle_instances[0].events[0][1]
    assert spec.width == 1280
    assert spec.height == 900
    assert spec.title == "FoliaSeal Phase 2 Harness - input.pdf"
    mounted_content = lifecycle_instances[0].events[1][1]
    assert [type(item[0]).__name__ for item in mounted_content.layout.items] == [
        "_Viewer",
        "_Label",
        "_Label",
        "_Status",
    ]


def test_phase2_harness_closes_when_viewer_setup_fails(monkeypatch, tmp_path: Path) -> None:
    lifecycle_instances = []

    def lifecycle_factory(bindings):
        lifecycle = _Lifecycle(bindings)
        lifecycle_instances.append(lifecycle)
        return lifecycle

    _patch_phase2_dependencies(
        monkeypatch,
        build_viewer=lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("viewer failed")),
    )
    source = tmp_path / "input.pdf"
    source.write_bytes(b"pdf")

    with pytest.raises(RuntimeError, match="viewer failed"):
        phase2_module.run_phase2_viewer_harness(
            pdf_path=str(source),
            checklist_template_path=str(tmp_path / "missing.md"),
            lifecycle_factory=lambda bindings: (
                lifecycle_instances.append(_Lifecycle(bindings)) or lifecycle_instances[-1]
            ),
        )

    assert [event[0] for event in lifecycle_instances[0].events] == ["start", "close"]


def test_phase2_harness_closes_when_report_write_fails(monkeypatch, tmp_path: Path) -> None:
    lifecycle_instances = []

    _patch_phase2_dependencies(
        monkeypatch,
        build_viewer=lambda **_kwargs: _Viewer(),
    )
    monkeypatch.setattr(
        phase2_module,
        "_write_optional_text",
        lambda **_kwargs: (_ for _ in ()).throw(OSError("report failed")),
    )
    source = tmp_path / "input.pdf"
    source.write_bytes(b"pdf")
    checklist = tmp_path / "checklist.md"
    checklist.write_text("# checklist\n", encoding="utf-8")

    with pytest.raises(OSError, match="report failed"):
        phase2_module.run_phase2_viewer_harness(
            pdf_path=str(source),
            summary_json_path=str(tmp_path / "summary.json"),
            checklist_template_path=str(checklist),
            lifecycle_factory=lambda bindings: (
                lifecycle_instances.append(_Lifecycle(bindings)) or lifecycle_instances[-1]
            ),
        )

    assert [event[0] for event in lifecycle_instances[0].events] == [
        "start",
        "mount",
        "show",
        "exec",
        "close",
    ]
