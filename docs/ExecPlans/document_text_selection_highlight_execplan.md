# Add arbitrary document text selection and highlight support to the signing shell

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows `.agents/skills/write-execplan/PLANS.md` and must be maintained in accordance with that file. It is self-contained so a contributor can resume this slice from only this document and the current repository tree.

## Purpose / Big Picture

`docs/SPEC.md` still requires the V1 GUI to let users select and copy arbitrary document text, not just search for text and copy the current search hit. After this change, a user in the signing shell will be able to enable a text-selection mode, drag across visible document text in the PDF viewer, see the selected region highlighted, and copy the selected text from the `Document text` card. The existing signature-placement drag workflow must continue to work unchanged when text-selection mode is off.

This slice is intentionally narrow. It adds text selection, selection highlight, and copy-selected-text behavior only. It does not add rich multi-selection editing, keyboard text selection, annotation export, or a full viewer rewrite.

The intended change slice is one behavior change commit for the text-selection/highlight feature plus one documentation/status update commit only if compliance review requires it. Preview changes, signing semantics, and unrelated packaging or verification work are forbidden from mixing into this slice.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/document_text_search_shell_execplan.md` completed first so the shell already has a `Document text` card, an application-layer text-search boundary, and a working clipboard seam.
- [x] `docs/ExecPlans/signing_shell_behavior_surface_execplan.md` completed first so the shell surface is already narrower and recent workspace-surface debt is reduced.
- [ ] A later child ExecPlan may deepen highlight fidelity if the initial implementation must move from rectangle-based highlight regions to polygon-accurate highlight painting.

## Progress

- [x] (2026-05-22T17:45:00Z) Completed the required `explorer-light` audit and fixed the target slice to explicit text-selection mode plus highlight overlay rather than a broad viewer redesign.
- [x] (2026-05-22T17:55:00Z) Re-read `.agents/skills/write-execplan/PLANS.md`, `src/foliaseal/presentation/qt/viewer_widget.py`, `src/foliaseal/application/viewer_workflow.py`, relevant shell tests, and the installed `PySide6.QtPdf` typing stubs before drafting this plan.
- [x] (2026-05-22T18:20:00Z) Added `src/foliaseal/application/document_text_selection.py` with `DocumentTextSelectionSession`, immutable selection-state dataclasses, and focused unit coverage in `tests/unit/test_document_text_selection.py`.
- [x] (2026-05-22T18:22:00Z) Added `src/foliaseal/infra/document_text_selection.py` with a `QPdfDocument`-backed arbitrary text-selection adapter that reuses QtPdf instead of adding a second PDF dependency.
- [x] (2026-05-22T18:35:00Z) Added viewer interaction-mode routing plus text-highlight overlay support in `src/foliaseal/presentation/qt/viewer_widget.py` and mode-regression coverage in `tests/unit/test_qt_viewer_widget.py`.
- [x] (2026-05-22T18:42:00Z) Extended the signing shell `Document text` card with explicit selection mode, selected-text copy/clear actions, and shell integration coverage in `tests/unit/test_qt_signing_shell.py`.
- [x] (2026-05-22T18:50:00Z) Focused validation passed: `pytest tests/unit/test_document_text_selection.py tests/unit/test_qt_viewer_widget.py tests/unit/test_qt_signing_shell.py`, `ruff check src/foliaseal/application/document_text_selection.py src/foliaseal/infra/document_text_selection.py src/foliaseal/presentation/qt/viewer_widget.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_document_text_selection.py tests/unit/test_qt_viewer_widget.py tests/unit/test_qt_signing_shell.py`, and `git diff --check`.
- [x] (2026-05-22T19:08:00Z) Completed the required `explorer-light` compliance review, restored search-state labels after leaving text-selection mode, added missing adapter/shell coverage, and updated stale architecture/ExecPlan text.
- [x] (2026-05-22T19:20:00Z) Recorded the next remaining SPEC-alignment gap after arbitrary text selection and brought the ExecPlan to pre-commit final state.

## Surprises & Discoveries

- Observation: the viewer already has the exact user gesture needed for text selection, but it is currently hardwired to signature placement.
  Evidence: `src/foliaseal/presentation/qt/viewer_widget.py` turns every left-button drag into `ViewerWorkflow.selection_to_pdf_rect()` followed by `on_selection(pdf_rect)`.

- Observation: the installed QtPdf bindings already expose selection primitives and clipboard helpers.
  Evidence: `.venv/lib/python3.12/site-packages/PySide6/QtPdf.pyi` defines `QPdfDocument.getSelection(...)`, `QPdfSelection.text()`, `QPdfSelection.bounds()`, `QPdfSelection.boundingRectangle()`, and `QPdfSelection.copyToClipboard()`.

- Observation: `ViewerWorkflow.selection_to_pdf_rect()` was already sufficient for the new mode because the QtPdf selection API accepts page-relative points directly.
  Evidence: the adapter now uses the normalized `PdfRect` corners as `QPointF` selection endpoints, and the focused `pytest tests/unit/test_document_text_selection.py tests/unit/test_qt_viewer_widget.py tests/unit/test_qt_signing_shell.py` set passed without any new view-to-page transform code.

## Decision Log

- Decision: implement an explicit viewer interaction mode instead of trying to infer whether a drag means signature placement or text selection.
  Rationale: mode inference would make the existing signature overlay resize path brittle and would risk collisions between signing and review behavior. An explicit mode keeps the boundary understandable and testable.
  Date/Author: 2026-05-22 / Codex

- Decision: keep the viewer emitting drag selections as page-relative PDF rectangles and let a separate text-selection adapter translate that rectangle into selected text plus highlight metadata.
  Rationale: `ViewerWorkflow.selection_to_pdf_rect()` is already the stable, tested boundary for drag-to-page mapping. Reusing it avoids new coordinate logic in the widget while still allowing a new document-text-selection boundary.
  Date/Author: 2026-05-22 / Codex

- Decision: model highlight state as one or more page-relative PDF rectangles derived from `QPdfSelection.bounds()` polygon bounds instead of introducing polygon-aware paint logic in the first pass.
  Rationale: rectangle highlights are good enough to make selection visible, keep the viewer paint path simple, and preserve a clean upgrade path if polygon fidelity is needed later.
  Date/Author: 2026-05-22 / Codex

## Outcomes & Retrospective

Implementation now adds a second document-review path alongside search: the shell can switch the viewer into text-selection mode, drag-select visible text, highlight the selected region on the current page, and copy the selected text through the existing clipboard seam while leaving normal signature placement intact when text mode is off. The final shell behavior also restores the active search summary when text-selection mode is turned back off, so manual selection does not destroy search-state feedback.

The compliance review initially found one real behavioral gap plus stale docs: leaving text-selection mode wiped the visible search summary even though the search session still existed, the adapter tests did not cover load-failure and empty/fallback selection cases, and the architecture/ExecPlan text still described search-only behavior. Those issues are now closed. After this slice lands, the next remaining SPEC-alignment gap is no longer arbitrary text selection. The most likely remaining gaps are deeper signature-inspection ergonomics or desktop workflow polish such as `File > Save As` and keyboard shortcuts, depending on which remaining `docs/SPEC.md` requirement you want to prioritize next.

## Context and Orientation

The top-level user experience for signing and review lives in `src/foliaseal/presentation/qt/signing_shell.py`. `SigningWorkspaceWidget` constructs the PDF viewer, the properties panel, the `Signing flow` card, the `Document review` card, and the `Document text` card. That `Document text` card already supports search, next/previous search-hit navigation, and copy-current-hit behavior via the application module `src/foliaseal/application/document_text_search.py`.

The PDF viewer widget is implemented in `src/foliaseal/presentation/qt/viewer_widget.py`. In this repository, a “viewer interaction mode” means the meaning assigned to a left-button drag on the rendered page. After this slice there are two explicit modes: `signature` and `text`. In both modes the widget turns a drag rectangle into a `PdfRect`, which is a page-relative rectangle in PDF points, and passes it to `on_selection`, but only signature mode allows persistent signature overlay resize handling. Text mode instead supports a separate text-highlight overlay.

The `ViewerWorkflow` in `src/foliaseal/application/viewer_workflow.py` owns the conversion between view-space rectangles and PDF-space rectangles. “View space” means on-screen widget coordinates after zoom and pan. “PDF space” means the coordinate system of the page itself in points. `selection_to_pdf_rect()` is already the tested seam that converts a drag rectangle from the widget into a page-relative `PdfRect`.

This slice introduces a second read-only text-review boundary in a new file such as `src/foliaseal/application/document_text_selection.py`. In this repository, a “selection session” means an object that owns the currently selected text, the page it came from, the highlight rectangles to render, and plain-language UI state such as whether copy is enabled. The concrete adapter underneath it should live in `src/foliaseal/infra/document_text_selection.py` and use `PySide6.QtPdf.QPdfDocument.getSelection(...)` against the current PDF path and page index.

The viewer must remain mode-safe. When text-selection mode is off, the existing signature placement and overlay-resize behavior must keep working exactly as before. When text-selection mode is on, a left-button drag must select text and update a text highlight instead of creating or resizing a signature rectangle.

## Plan of Work

First, add a new application module `src/foliaseal/application/document_text_selection.py`. Define immutable data objects for one selected text region and one shell-facing selection state. The selected-region object should contain the page index, selected text, and one or more highlight rectangles in PDF coordinates. The state object should contain user-facing status text, detail text, the selected region if one exists, and booleans such as whether copy and clear actions are currently allowed. Add a small `DocumentTextSelectionSession` that accepts a lower-level selection adapter, updates current state from a page/drag rectangle, exposes the currently selected text, and clears selection state when requested.

Second, add a concrete QtPdf selection adapter in `src/foliaseal/infra/document_text_selection.py`. It should accept the current PDF path, page index, and `PdfRect`, open the PDF with `QPdfDocument`, call `getSelection(page, start, end)`, and return selected text plus highlight rectangles. Treat the drag rectangle corners as the selection start and end points in page coordinates because the widget has already converted them into page-relative PDF space. Derive highlight rectangles from `QPdfSelection.bounds()` by taking each polygon’s min/max extents and converting them into `PdfRect` values. If selection text is empty, return an empty selection state rather than raising. Missing or unreadable PDFs must fail soft with an actionable message.

Third, extend `src/foliaseal/presentation/qt/viewer_widget.py` with an explicit interaction mode. Add a small mode value such as `"signature"` and `"text"` or a named enum equivalent. In signature mode, keep the current behavior, including signature overlay handle hit testing and drag-to-placement. In text mode, bypass signature overlay handle drag behavior, still allow middle-drag or shift-drag panning, and let a left-button drag emit the same `PdfRect` selection callback. Also add a second overlay path for text selection highlights so the current page can show one or more translucent highlight rectangles without affecting the persistent signature overlay.

Fourth, extend `src/foliaseal/presentation/qt/signing_shell.py`. Add a `DocumentTextSelectionSession`, inject the concrete selection adapter by default, and wire a new viewer-selection toggle in the `Document text` card. The shell should switch the viewer into text mode when the toggle is active, route viewer selections to text selection instead of signature placement while text mode is on, update the card labels to describe the selected text, copy selected text through the existing clipboard callback, and clear the selection when requested. Search behavior must continue to work, and search-result navigation must not break the new manual text-selection state.

Fifth, add focused tests. Create a new unit test module for the selection session and adapter. Update `tests/unit/test_qt_viewer_widget.py` to prove that drag routing remains mode-safe: signature mode still emits placement rectangles, and text mode still emits drag selections while suppressing signature overlay resize semantics. Update `tests/unit/test_qt_signing_shell.py` with a shell integration test that enables text-selection mode, simulates a viewer drag selection, asserts the shell status labels and highlight/copy behavior, and proves that disabling text mode restores signature placement behavior.

Finally, run focused validation, then perform the required compliance review against `docs/SPEC.md`, `docs/ARCHITECTURE.md`, and this ExecPlan. If the review finds stale docs, update them and rerun the focused checks before committing.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

Inspect the current interfaces before editing:

    sed -n '80,95p' docs/SPEC.md
    sed -n '1,260p' src/foliaseal/presentation/qt/viewer_widget.py
    sed -n '1,220p' src/foliaseal/application/viewer_workflow.py
    sed -n '1,260p' src/foliaseal/application/document_text_search.py
    sed -n '100,180p' .venv/lib/python3.12/site-packages/PySide6/QtPdf.pyi

Start with the new application selection-session tests:

    pytest tests/unit/test_document_text_selection.py

After wiring the viewer mode and shell controls, run the focused integration set:

    pytest tests/unit/test_document_text_selection.py tests/unit/test_qt_viewer_widget.py tests/unit/test_qt_signing_shell.py

Then run focused lint:

    ruff check src/foliaseal/application/document_text_selection.py src/foliaseal/infra/document_text_selection.py src/foliaseal/presentation/qt/viewer_widget.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_document_text_selection.py tests/unit/test_qt_viewer_widget.py tests/unit/test_qt_signing_shell.py

Finally ensure patch hygiene:

    git diff --check

If compliance review requires documentation changes, rerun the relevant focused checks and record the final passing commands in this plan.

## Validation and Acceptance

Acceptance is behavioral. After this change, a user in the signing shell must be able to enable text-selection mode, drag across visible document text in the viewer, see a selection highlight appear on the current page, and copy the selected text from the shell. When text-selection mode is disabled, left-button drag must continue to place or resize the signature rectangle exactly as before.

The proof points are:

- `tests/unit/test_document_text_selection.py` passes and proves blank selection, successful selection, copyable selected text, clearing state, and failure-tolerant unreadable-PDF handling.
- `tests/unit/test_qt_viewer_widget.py` passes and includes mode-routing coverage showing that signature mode and text mode do not collide.
- `tests/unit/test_qt_signing_shell.py` passes and includes a shell-level selection-mode test for selected text, highlight state, copy behavior, and restoration of signature placement after text mode is turned off.
- focused `ruff check` and `git diff --check` pass.

This slice is complete when those proofs hold and the compliance review confirms that the implementation is aligned with the `select/copy document text` portion of `docs/SPEC.md` at the intended first-pass level.

## Idempotence and Recovery

This feature is read-only with respect to the PDF and signing configuration. Re-running searches, toggling text-selection mode, dragging to select text, and copying selected text must not mutate the document or persisted app state.

Implement the application-layer selection session first, then viewer mode, then shell controls. If the text-selection paint path or adapter proves unstable, keep the mode seam in place and fall back to selection-without-highlight only long enough to capture the finding in this plan; do not mix speculative viewer rewrites into the slice. If clipboard access is unavailable in the default Qt path, keep copy disabled and preserve the existing injected callback seam for tests and future platform-specific wiring.

## Artifacts and Notes

Current gap evidence before the change:

    docs/SPEC.md
    - V1 still requires `select/copy document text`.

    src/foliaseal/presentation/qt/viewer_widget.py
    - left-button drag always means placement selection today.

    src/foliaseal/application/document_text_search.py
    - only search/current-hit state exists; no arbitrary selection or highlight state.

    PySide6/QtPdf.pyi
    - `QPdfDocument.getSelection(...)` and `QPdfSelection.bounds()` are available for a concrete adapter.

Validation evidence after implementation:

    pytest tests/unit/test_document_text_selection.py tests/unit/test_qt_viewer_widget.py tests/unit/test_qt_signing_shell.py
    - passed on 2026-05-22

    ruff check src/foliaseal/application/document_text_selection.py src/foliaseal/infra/document_text_selection.py src/foliaseal/presentation/qt/viewer_widget.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_document_text_selection.py tests/unit/test_qt_viewer_widget.py tests/unit/test_qt_signing_shell.py
    - passed on 2026-05-22

    git diff --check
    - passed on 2026-05-22

## Interfaces and Dependencies

At the end of this slice, the application-layer selection boundary should have a shape along these lines:

    @dataclass(frozen=True)
    class DocumentTextSelection:
        page_index: int
        text: str
        highlight_rects: tuple[PdfRect, ...]

    @dataclass(frozen=True)
    class DocumentTextSelectionState:
        status_text: str
        detail_text: str
        selection: DocumentTextSelection | None
        can_copy: bool
        can_clear: bool

    class DocumentTextSelectionEngine(Protocol):
        def select(
            self,
            input_pdf_path: str,
            *,
            page_index: int,
            selection_rect: PdfRect,
        ) -> DocumentTextSelection | None:
            ...

    class DocumentTextSelectionSession:
        def select(
            self,
            *,
            page_index: int,
            selection_rect: PdfRect,
        ) -> DocumentTextSelectionState: ...
        def clear(self) -> DocumentTextSelectionState: ...
        def current_copy_text(self) -> str | None: ...

In `src/foliaseal/presentation/qt/viewer_widget.py`, the viewer should expose a public interaction-mode setter and a public text-highlight overlay setter/clearer alongside the existing signature overlay methods. The shell should consume only the application-layer selection state plus those viewer methods; it must not own QtPdf selection parsing directly.

Change note: 2026-05-22 / Codex

Created this ExecPlan from the required `explorer-light` audit for the next SPEC-alignment slice. It was later revised during compliance closeout to record the final two-mode viewer behavior, the search-state-restore rule on selection-mode exit, and the additional adapter/shell coverage that proved the manual-selection path did not regress search behavior.
