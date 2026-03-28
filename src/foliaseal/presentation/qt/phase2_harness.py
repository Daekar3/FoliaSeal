"""Interactive Qt harness for Phase 2 viewer validation."""

from __future__ import annotations

import importlib
import json
import re
import shlex
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

from foliaseal.application.coordinate_transform import PdfRect
from foliaseal.application.viewer_session import ViewerSession
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.infra.render.qt_backend import QtPdfRenderBackend
from foliaseal.presentation.qt.viewer_widget import build_qt_pdf_viewer_widget

DEFAULT_CHECKLIST_TEMPLATE_PATH = "phase2_manual_qa_checklist.md"
DEFAULT_CHECKLIST_RESULTS_PATH = "artifacts/phase2_manual_qa_results.md"


@dataclass(frozen=True)
class HarnessCapture:
    """Structured capture emitted by the interactive Qt harness."""

    pdf_path: str
    first_render_ms: float | None
    navigation_samples_ms: tuple[float, ...]
    selection_count: int
    last_selection_pdf_rect: tuple[float, float, float, float] | None
    interaction_counts: dict[str, int]
    errors: tuple[str, ...]

    def to_json(self) -> str:
        """Return a stable JSON representation for later evidence assembly."""

        return json.dumps(asdict(self), indent=2, sort_keys=True)


def build_phase2_evidence_command(
    capture: HarnessCapture,
    *,
    python_executable: str = ".venv/bin/python",
    packaged_executable: str = "dist/foliaseal/foliaseal",
    startup_ready_after_seconds: float = 0.75,
    bundle_dir: str = "dist/foliaseal",
    checklist_path: str = DEFAULT_CHECKLIST_RESULTS_PATH,
    artifact_path: str = "artifacts/phase2_runtime_evidence.md",
) -> str:
    """Build a shell command that folds captured timings into the evidence CLI."""

    parts = [
        shlex.quote(python_executable),
        "-m",
        "foliaseal",
        "phase2-evidence",
    ]
    if capture.first_render_ms is not None:
        parts.extend(["--first-render-ms", f"{capture.first_render_ms:.2f}"])
    for sample in capture.navigation_samples_ms:
        parts.extend(["--navigation-ms", f"{sample:.2f}"])
    parts.extend(
        [
            "--collect-runtime-footprint",
            "--measure-startup-command",
            shlex.quote(packaged_executable),
            "--startup-ready-after-seconds",
            f"{startup_ready_after_seconds:.2f}",
            "--bundle-dir",
            shlex.quote(bundle_dir),
            "--qa-checklist-file",
            shlex.quote(checklist_path),
            "--check-qt-runtime",
            "--write-markdown-file",
            shlex.quote(artifact_path),
        ]
    )
    return " ".join(parts)


def build_checklist_results_markdown(
    capture: HarnessCapture,
    *,
    checklist_template_path: str = DEFAULT_CHECKLIST_TEMPLATE_PATH,
) -> str:
    """Render a run-specific QA checklist seeded from the immutable template."""

    template = Path(checklist_template_path).read_text(encoding="utf-8")
    auto_checked_items = _derive_auto_checked_items(capture)
    checkbox_pattern = re.compile(r"^(\s*-\s*)\[(?: |x|X)\](\s+)(.+)$")

    rendered_lines = [
        "# Phase 2 Manual QA Results",
        "",
        f"Source checklist: `{checklist_template_path}`",
        f"Captured PDF: `{capture.pdf_path}`",
        "",
        "Update any remaining unchecked items after reviewing the manual session.",
        "This file is the one that `phase2-evidence --qa-checklist-file ...` should consume.",
        "",
    ]
    for raw_line in template.splitlines():
        match = checkbox_pattern.match(raw_line)
        if not match:
            rendered_lines.append(raw_line)
            continue
        prefix, spacing, item_text = match.groups()
        marker = "x" if item_text.strip() in auto_checked_items else " "
        rendered_lines.append(f"{prefix}[{marker}]{spacing}{item_text}")
    return "\n".join(rendered_lines) + "\n"


def run_phase2_viewer_harness(
    *,
    pdf_path: str,
    summary_json_path: str | None = None,
    evidence_command_path: str | None = None,
    checklist_results_path: str = DEFAULT_CHECKLIST_RESULTS_PATH,
    checklist_template_path: str = DEFAULT_CHECKLIST_TEMPLATE_PATH,
) -> HarnessCapture:
    """Launch an interactive Qt viewer harness for manual Phase 2 validation."""

    bindings = _load_qt_harness_bindings()
    source_path = Path(pdf_path)
    if not source_path.exists():
        raise FileNotFoundError(f"PDF does not exist: {pdf_path}")

    page_count = _load_page_count(bindings=bindings, pdf_path=str(source_path))
    backend = QtPdfRenderBackend()
    diagnostic = backend.diagnostics()
    if not diagnostic.available:
        raise RuntimeError(diagnostic.message)

    workflow = ViewerWorkflow(
        document_path=str(source_path),
        render_backend=backend,
        session=ViewerSession(page_count=page_count),
    )

    selections: list[PdfRect] = []
    errors: list[str] = []
    interaction_counts: Counter[str] = Counter()

    app = bindings.q_application.instance() or bindings.q_application([])
    window = bindings.q_main_window()
    window.setWindowTitle(f"FoliaSeal Phase 2 Harness - {source_path.name}")
    window.resize(1280, 900)

    central = bindings.q_widget()
    layout = bindings.q_v_box_layout(central)
    toolbar = bindings.q_h_box_layout()
    layout.addLayout(toolbar)

    instructions = bindings.q_label(_instructions_text(source_path=source_path))
    instructions.setWordWrap(True)
    metrics_label = bindings.q_label()

    status = bindings.q_plain_text_edit()
    status.setReadOnly(True)
    status.setMaximumBlockCount(200)

    window.setCentralWidget(central)

    def append_status(message: str) -> None:
        status.appendPlainText(message)

    def refocus_viewer() -> None:
        focus_setter = getattr(viewer, "setFocus", None)
        if callable(focus_setter):
            focus_setter()

    def refresh_metrics() -> None:
        snapshot = workflow.timing_tracker.snapshot()
        metrics_label.setText(
            _metrics_text(
                first_render_ms=snapshot.first_render_ms,
                navigation_samples=snapshot.sample_count,
            )
        )

    def on_selection(rect: PdfRect) -> None:
        selections.append(rect)
        append_status(
            "Selection captured: "
            f"({rect.x1:.2f}, {rect.y1:.2f}) -> ({rect.x2:.2f}, {rect.y2:.2f})"
        )
        refresh_metrics()

    def on_error(message: str) -> None:
        errors.append(message)
        append_status(f"Error: {message}")
        refresh_metrics()

    def on_interaction(name: str) -> None:
        interaction_counts[name] += 1
        refresh_metrics()

    selections.clear()
    errors.clear()
    interaction_counts.clear()

    viewer = build_qt_pdf_viewer_widget(
        workflow=workflow,
        on_selection=on_selection,
        on_error=on_error,
        on_interaction=on_interaction,
    )
    layout.addWidget(viewer, 1)
    layout.addWidget(metrics_label)
    layout.addWidget(instructions)
    layout.addWidget(status)
    refresh_metrics()

    def do_refresh() -> None:
        viewer.refresh()
        refresh_metrics()
        refocus_viewer()

    def navigate(action_name: str) -> None:
        action = getattr(viewer, action_name)
        action()
        refresh_metrics()
        refocus_viewer()

    def fit_width() -> None:
        viewport = viewer.viewport()
        page_snapshot = workflow.snapshot
        if page_snapshot is None:
            do_refresh()
            page_snapshot = workflow.snapshot
        if page_snapshot is None:
            return
        workflow.fit_to_width(
            viewport_width_px=float(viewport.width()),
            page_width_px=float(page_snapshot.image_width_px),
        )
        viewer.refresh()
        refresh_metrics()
        refocus_viewer()

    def fit_page() -> None:
        viewport = viewer.viewport()
        page_snapshot = workflow.snapshot
        if page_snapshot is None:
            do_refresh()
            page_snapshot = workflow.snapshot
        if page_snapshot is None:
            return
        workflow.fit_to_page(
            viewport_height_px=float(viewport.height()),
            page_height_px=float(page_snapshot.image_height_px),
        )
        viewer.refresh()
        refresh_metrics()
        refocus_viewer()

    controls = [
        ("Refresh", do_refresh),
        ("Prev Page", lambda: navigate("go_to_previous_page")),
        ("Next Page", lambda: navigate("go_to_next_page")),
        ("Reset Zoom", lambda: navigate("reset_zoom_view")),
        ("Fit Width", fit_width),
        ("Fit Page", fit_page),
    ]
    for label, callback in controls:
        button = bindings.q_push_button(label)
        button.clicked.connect(callback)
        toolbar.addWidget(button)

    toolbar.addStretch(1)

    start = perf_counter()
    viewer.refresh()
    elapsed_ms = (perf_counter() - start) * 1000.0
    append_status(f"Initial render completed in {elapsed_ms:.2f} ms.")
    refresh_metrics()

    window.show()
    refocus_viewer()
    app.exec()

    capture = HarnessCapture(
        pdf_path=str(source_path),
        first_render_ms=workflow.timing_tracker.snapshot().first_render_ms,
        navigation_samples_ms=workflow.timing_tracker.navigation_samples_ms,
        selection_count=len(selections),
        last_selection_pdf_rect=(
            (
                selections[-1].x1,
                selections[-1].y1,
                selections[-1].x2,
                selections[-1].y2,
            )
            if selections
            else None
        ),
        interaction_counts=dict(sorted(interaction_counts.items())),
        errors=tuple(errors),
    )
    _write_optional_text(
        target_path=summary_json_path,
        content=capture.to_json() + "\n",
    )
    checklist_results = build_checklist_results_markdown(
        capture,
        checklist_template_path=checklist_template_path,
    )
    _write_optional_text(
        target_path=checklist_results_path,
        content=checklist_results,
    )
    evidence_command = build_phase2_evidence_command(
        capture,
        checklist_path=checklist_results_path,
    )
    _write_optional_text(
        target_path=evidence_command_path,
        content=evidence_command + "\n",
    )
    print("Phase 2 harness capture")
    print(capture.to_json())
    print()
    print(f"Checklist results file: {checklist_results_path}")
    print("Review it, check any remaining manual-only items, then run:")
    print("Evidence command:")
    print(evidence_command)
    return capture


@dataclass(frozen=True)
class _QtHarnessBindings:
    q_application: type[Any]
    q_main_window: type[Any]
    q_widget: type[Any]
    q_v_box_layout: type[Any]
    q_h_box_layout: type[Any]
    q_push_button: type[Any]
    q_label: type[Any]
    q_plain_text_edit: type[Any]
    qpdf_document: type[Any]


def _load_qt_harness_bindings() -> _QtHarnessBindings:
    widgets = importlib.import_module("PySide6.QtWidgets")
    qtpdf = importlib.import_module("PySide6.QtPdf")
    return _QtHarnessBindings(
        q_application=getattr(widgets, "QApplication"),
        q_main_window=getattr(widgets, "QMainWindow"),
        q_widget=getattr(widgets, "QWidget"),
        q_v_box_layout=getattr(widgets, "QVBoxLayout"),
        q_h_box_layout=getattr(widgets, "QHBoxLayout"),
        q_push_button=getattr(widgets, "QPushButton"),
        q_label=getattr(widgets, "QLabel"),
        q_plain_text_edit=getattr(widgets, "QPlainTextEdit"),
        qpdf_document=getattr(qtpdf, "QPdfDocument"),
    )


def _load_page_count(*, bindings: _QtHarnessBindings, pdf_path: str) -> int:
    document = bindings.qpdf_document()
    status = document.load(pdf_path)
    if status != bindings.qpdf_document.Error.None_:
        raise RuntimeError(f"Failed to load PDF document: {pdf_path}")
    return int(document.pageCount())


def _instructions_text(*, source_path: Path) -> str:
    return (
        f"Loaded PDF: {source_path}\n"
        "Use the toolbar, mouse wheel, keyboard shortcuts, and drag-selection to complete "
        "the Phase 2 manual checklist. Close the window when finished to print the captured "
        "timings and a ready-to-run evidence command."
    )


def _metrics_text(*, first_render_ms: float | None, navigation_samples: int) -> str:
    first_render = (
        f"{first_render_ms:.2f} ms" if first_render_ms is not None else "not recorded yet"
    )
    return (
        f"First render: {first_render} | "
        f"Navigation samples captured: {navigation_samples}"
    )


def _derive_auto_checked_items(capture: HarnessCapture) -> set[str]:
    interaction_counts = capture.interaction_counts
    auto_checked: set[str] = set()

    if capture.first_render_ms is not None:
        auto_checked.add("Confirm preview widget loads without dependency errors.")
        auto_checked.add("Initial render succeeds on page 1.")
        auto_checked.add("Record first-render elapsed time in milliseconds.")

    if (
        interaction_counts.get("key_zoom_in", 0) > 0
        and interaction_counts.get("key_zoom_out", 0) > 0
        and interaction_counts.get("key_zoom_reset", 0) > 0
    ):
        auto_checked.add("Keyboard zoom shortcuts work (`+`, `-`, `0` reset).")

    if (
        interaction_counts.get("key_page_next", 0) > 0
        and interaction_counts.get("key_page_previous", 0) > 0
    ):
        auto_checked.add(
            "Page navigation next/previous works and stays within valid bounds."
        )

    if (
        interaction_counts.get("key_page_next", 0) > 0
        and interaction_counts.get("key_page_previous", 0) > 0
        and interaction_counts.get("key_jump_home", 0) > 0
        and interaction_counts.get("key_jump_end", 0) > 0
    ):
        auto_checked.add(
            "Keyboard page navigation works (`PgUp`/`PgDn`, arrows, `Home`/`End`)."
        )
        auto_checked.add(
            "Jump-to-page behavior handles first page, middle page, and last page."
        )

    if capture.selection_count > 0 and capture.last_selection_pdf_rect is not None:
        auto_checked.add(
            "Drag-selection callback returns a valid in-bounds PDF rectangle."
        )

    if interaction_counts.get("selection_error", 0) > 0:
        auto_checked.add(
            "Out-of-bounds selection produces an actionable UI error message."
        )

    if len(capture.navigation_samples_ms) >= 10:
        auto_checked.add("Record at least 10 navigation samples in milliseconds.")

    return auto_checked


def _write_optional_text(*, target_path: str | None, content: str) -> None:
    if target_path is None:
        return
    path = Path(target_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
