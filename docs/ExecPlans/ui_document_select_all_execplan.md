# Implement viewer Select All for current-page PDF text

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (the agent can implement and validate it
without a pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can focus the PDF viewer and choose Edit → Select All, or press Ctrl+A,
to select all extractable text on the currently visible page. FoliaSeal will show the same current-page
selection highlight and status/copy feedback used by pointer text selection. If the page contains only
an image, has no extractable text, or cannot be read, the existing document-text status explains the
condition without pretending OCR exists. A focused native line/text editor still owns Ctrl+A and native
Select All; the viewer fallback is used only when no native editor has focus. This closes the explicitly
named viewer Select All behavior in UI_SPEC section 7 while preserving the one-page selection rule in
UI_SPEC section 8.

The behavior is observable in the real GUI through Edit → Select All/Ctrl+A, the highlighted current
page, and Edit → Copy/Ctrl+C placing the selected text on the clipboard. The implementation remains
one vertical slice: PDF extraction, application selection state, typed workspace/session ports, Qt
action routing, focused tests, and offscreen acceptance all land together.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are the governing contracts.
- [x] docs/ExecPlans/ui_pdf_navigation_zoom_pan_execplan.md — current-page navigation and viewer page
  state are available.
- [x] docs/ExecPlans/ui_document_search_selection_execplan.md — pointer text selection, copy feedback,
  typed selection overlays, and Qt PDF text extraction foundations are implemented.
- [x] docs/ExecPlans/ui_command_model_shortcuts_execplan.md — native Edit Select All and focus
  precedence are implemented; this child adds only the viewer fallback.

## Progress

- [x] (2026-08-10) Fresh explorer audit selected viewer Select All as the next dependency-ready
  compliance slice; Help remains deferred because its topic corpus, in-app viewer, CLI surface, and
  packaging contract are not ready.
- [x] (2026-08-10) Created this focused child plan and recorded the current application, Qt PDF,
  session, runtime, and AppFrame seams.
- [x] (2026-08-10) Added current-page `select_all` operations to the document text engine/session,
  including empty-text and load-failure state.
- [x] (2026-08-10) Routed the operation through the review workspace, runtime, session port, and
  AppFrame while preserving native-editor precedence and independent selection overlays.
- [x] (2026-08-10) Added red/green unit, Qt adapter, runtime/session, AppFrame, and real offscreen
  acceptance coverage; the focused implementation set is green.
- [x] (2026-08-10) Reconciled architecture, parent/child plan status, and terminology; focused and
  full validation passed, and the bounded GUI/process cleanup audit completed with the known
  isolated `SingleInstanceUnavailable` launch limitation and no lingering owned processes.

## Surprises & Discoveries

- Observation: `DocumentTextSelectionSession` currently accepts only a drag rectangle, while
  `QtPdfDocumentTextSelectionEngine` already converts Qt selection polygons into page-local `PdfRect`
  values and owns PDF loading/error handling.
  Evidence: `src/foliaseal/application/document_text_selection.py` and
  `src/foliaseal/infra/document_text_selection.py`.
- Observation: current-page ownership already exists in `SigningWorkspaceRuntime.logical_page_index()`
  and `DocumentReviewWorkspaceViewerEffects` already carries selection highlight rectangles separately
  from search highlights.
  Evidence: `src/foliaseal/presentation/qt/signing_workspace_runtime.py` and
  `src/foliaseal/application/document_review_workspace.py`.
- Observation: native Edit Select All is already routed by `FoliaSealAppFrame` and is enabled only for
  a focused native editor. The viewer fallback must therefore be a public session operation, not a
  second widget callback or a replacement for native behavior.
  Evidence: `src/foliaseal/presentation/qt/app_frame.py` and
  `docs/ExecPlans/ui_command_model_shortcuts_execplan.md`.
- Observation: `QPdfDocument.getAllText(page)` returns a selection whose text length can be used with
  `getSelectionAtIndex(page, 0, length)` to obtain the page's complete text and highlight polygons.
  Evidence: the installed PySide6 binding exposes both methods; existing search infrastructure already
  uses the same index-selection API.
- Observation: the AppFrame's workspace action state is refreshed from the public session capability
  and selected-text capability, so a successful viewer Select All immediately enables Copy without
  reaching through the viewer widget.
  Evidence: the fake AppFrame path and offscreen shell path both dispatch Select All through
  `QtSigningWorkspaceSessionPort` and leave native editor precedence intact.

## Decision Log

- Decision: implement viewer Select All by extending the existing document text selection engine and
  session rather than creating a second text-selection model.
  Rationale: pointer selection, copy, status text, and overlays already share this boundary; a second
  model would allow Ctrl+A and pointer selection to disagree about state or clearing.
  Date/Author: 2026-08-10 / Codex.
- Decision: select all extractable text on the runtime's current logical page only, never across the
  whole document.
  Rationale: UI_SPEC explicitly makes viewer Select All current-page-only and the viewer is a single-page
  interaction surface.
  Date/Author: 2026-08-10 / Codex.
- Decision: keep native editor precedence in `FoliaSealAppFrame`; only the no-native-editor path calls
  `SigningWorkspaceSessionPort.select_all_document_text()`.
  Rationale: Qt owns native editor semantics, while the public workspace port is the only safe boundary
  for PDF extraction and viewer overlays.
  Date/Author: 2026-08-10 / Codex.
- Decision: use `getAllText()` followed by `getSelectionAtIndex()` to build one complete page selection,
  and reduce each returned polygon to a PDF-space bounding rectangle using the existing coordinate
  conversion.
  Rationale: this reuses the proven Qt PDF text and geometry path, keeps QPdfDocument out of application
  code, and preserves one highlight rectangle per extracted text polygon.
  Date/Author: 2026-08-10 / Codex.
- Decision: an image-only, no-extractable-text, or parser/load failure returns no selection and leaves
  the existing status/detail state authoritative; it does not raise through the Qt action callback.
  Rationale: UI_SPEC requires truthful unavailable-text feedback and no implied OCR, and the existing
  selection session already converts backend exceptions into status state.
  Date/Author: 2026-08-10 / Codex.

## Outcomes & Retrospective

The engine, selection session, review transition, runtime/session port, AppFrame fallback, and real
offscreen extraction path are implemented. Viewer Select All intentionally remains current-page-only;
Help and final release scenario evidence remain separate parent-plan work.

## Context and Orientation

FoliaSeal is a Python/PySide6 Linux PDF signing application. `DocumentTextSelection` in
`src/foliaseal/application/document_text_selection.py` is the Qt-free value containing page index,
selected text, and PDF-space highlight rectangles. `DocumentTextSelectionSession` owns the current
selection and translates backend failures into status/detail/copy/clear capability state.
`QtPdfDocumentTextSelectionEngine` in `src/foliaseal/infra/document_text_selection.py` is the concrete
adapter: it loads a PDF with `QPdfDocument`, asks Qt for selected text, and converts Qt top-left
selection polygons to PDF bottom-left rectangles.

`DocumentReviewWorkspaceSession` in
`src/foliaseal/application/document_review_workspace.py` composes search and selection state and emits
typed `DocumentReviewWorkspaceTransition` effects. `SigningWorkspaceReviewBridge` applies those effects
to the viewer without exposing child widgets to application code. `SigningWorkspaceRuntime` is the
shell-owned orchestration boundary, and `QtSigningWorkspaceSessionPort` in
`src/foliaseal/presentation/qt/signing_shell_port.py` is the typed caller-facing adapter used by
`FoliaSealAppFrame`. The AppFrame already routes Edit Select All to a focused `QLineEdit`/`QTextEdit`;
the new fallback must route through the session port when the focused widget is not a native editor.

A compatibility surface means an adapter kept for an older caller. “phase3” is legacy evidence/harness
nomenclature, not a product feature label; do not add it to new code, tests, UI, or documentation.

## Change Slice

Primary change class: behavior change. Allowed files are the named application selection/workspace
modules, Qt PDF adapter, runtime/session/AppFrame ports and callbacks, focused unit/integration tests,
the owning ExecPlans, and the minimum architecture/status documentation needed to describe the new
boundary. Temporary PDFs/configuration may be written only under ignored temporary/artifact paths and
must be removed. Do not mix Help, packaging, broad viewer refactors, text-search redesign, unrelated
certificate/signing work, or evidence rebaselines into this commit.

## Plan of Work

First extend `DocumentTextSelectionEngine` with `select_all(input_pdf_path, *, page_index)` and add a
matching `DocumentTextSelectionSession.select_all(page_index=...)` operation. The Qt adapter should
validate the path and page, load the document once, read `getAllText(page_index).text()`, return `None`
for empty/whitespace text, and otherwise call `getSelectionAtIndex(page_index, 0, len(text))`. Convert
the selection bounds with the existing page-height transform; if Qt supplies text but no bounds, use a
page-local fallback rectangle only if a safe page-wide bounds can be derived, otherwise return the text
with an empty highlight tuple and let the status remain copyable. Keep load failures as exceptions so
the session can reuse its existing unavailable-state conversion. Guard invalid page indexes and close
the document in `finally` exactly as the pointer-selection path does.

Next add a `select_all_text(page_index)` transition to `DocumentReviewWorkspaceSession`. It should call
the selection session, set display source to `selection`, and return the same selection-highlight effect
used by pointer selection. It must not clear search highlights, must not change the current page, and
must not require text-selection mode to be enabled: Edit Select All is an explicit action, while the
pointer tool remains separately gated by the Select Text mode. Add a state/capability method that the
runtime can use to report whether the current page is eligible; when extraction is unknown or fails,
the action remains available for the active workspace and the resulting status explains why no text was
selected rather than silently disabling an operation the user requested.

Expose the transition in `SigningWorkspaceRuntime` as
`select_all_document_text() -> DocumentTextSelectionState`, applying it through the existing review
bridge and emitting `document_text_selection_changed`. Add
`can_select_all_document_text() -> bool` with the conservative rule “active workspace and valid current
page”; extraction-specific unavailability is communicated by the returned selection state. Add both
methods to `SigningWorkspaceSessionPort` and delegate them through
`QtSigningWorkspaceSessionPort`. Keep `SigningWorkspacePort` (the maintenance port) unchanged.

Update AppFrame action synchronization so a non-native-editor active workspace enables Select All from
`can_select_all_document_text()`, while a focused native editor continues to derive the action from
native capability state. Update `_select_all_edit()` to call the native editor first and otherwise call
the session-port viewer method; synchronize action state after the transition so Copy becomes enabled
when page text was selected. No AppFrame code may import QPdfDocument or inspect viewer children.

Add tests before implementation for the engine/session operation, workspace transition/effect behavior,
runtime/session-port delegation, AppFrame native-precedence/fallback/disabled state, and real offscreen
Qt behavior. The real test must create or use a text-bearing PDF fixture, focus the viewer, trigger
Edit → Select All and Ctrl+A, assert page-local highlighted rectangles and selected text, then trigger
Copy/Ctrl+C and assert the clipboard text. It must also prove a focused native line edit still receives
Ctrl+A and that no active workspace leaves viewer Select All disabled. Add image-only/empty-text and
load-failure assertions without changing the existing pointer-selection contract.

## Milestones

Milestone 1 extends the engine and application session with a red/green current-page select-all
operation. It proves full text, empty text, geometry, failures, copy state, and clear behavior using
Qt-free fakes and Qt adapter doubles.

Milestone 2 wires the workspace transition, runtime, public session port, and AppFrame fallback. It
proves native-editor precedence, no-document disablement, current-page routing, independent search
highlights, and Copy enablement after a successful viewer selection.

Milestone 3 runs the real offscreen Qt Edit action/shortcut flow, updates architecture and parent/child
plan status, runs the full suite and bounded GUI audit, cleans all owned processes and temporary roots,
and commits the complete slice.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal` using the repository virtual environment. Do not use a
system Python or system Qt fallback.

    rg -n "DocumentTextSelection|select_all|Select All|_select_all_edit|logical_page_index" src tests docs/ExecPlans
    .venv/bin/pytest -q tests/unit/test_document_text_selection.py tests/unit/test_document_review_workspace.py
    .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py
    QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q tests/integration/test_gui_launch_no_document.py -k 'select_all or edit'
    .venv/bin/ruff check src tests
    git diff --check
    .venv/bin/pytest -q

For the bounded GUI lifecycle audit, isolate configuration and always clean it:

    audit_root=$(mktemp -d /tmp/foliaseal-select-all-audit-XXXXXX)
    set +e
    timeout --foreground 30s env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf >"$audit_root/gui.log" 2>&1
    gui_rc=$?
    set -e
    printf 'gui_rc=%s\n' "$gui_rc"
    sed -n '1,80p' "$audit_root/gui.log"
    if ps -eo pid=,cmd= | rg 'FoliaSeal|foliaseal|PySide6|pytest' | rg -v 'rg '; then echo process-check=FOUND; else echo process-check=clean; fi
    rm -rf "$audit_root"

The expected bounded-launch result in this environment is `gui_rc=1` with
`SingleInstanceUnavailable`; the process check must be clean and the temporary root must be absent.

## Validation and Acceptance

Acceptance is behavioral. With a PDF workspace open and the viewer focused, Edit → Select All and
Ctrl+A select all extractable text on the current page only, display its highlight rectangles, and
leave search highlights independent. Edit → Copy or Ctrl+C then places that text on the clipboard and
the existing status/card reports the selection. Moving to another page, closing the workspace, or
focusing a native editor prevents the viewer path from mutating unrelated state; native editor Ctrl+A
continues to select only the editor's content. On an image-only/no-text page or a load/parser failure,
the action completes without a traceback and the document-text card says that text selection is
unavailable or absent, with no false copy capability.

The focused red/green tests must cover the new engine/session/workspace/runtime/AppFrame boundaries,
including page index and geometry. The real offscreen test must prove menu and Ctrl+A viewer behavior,
clipboard copy, native-editor precedence, and no-document disablement. The full suite, Ruff, and diff
checks must be green; any existing warning must be reported without hiding a new warning. No FoliaSeal,
PySide6, or pytest processes and no temporary audit root may remain after validation.

## Idempotence and Recovery

All tests use temporary PDFs/configuration and injected engines. If a test or GUI audit fails, close
only processes owned by this slice, remove only its temporary roots, and update Progress with the exact
failure before retrying. Do not delete user PDFs, credentials, generated repository fixtures, or broad
artifact directories. If a Qt PDF selection remains open after an exception, the adapter's `finally`
close must release it before another attempt.

## Artifacts and Notes

Allowed evidence is concise test output, optional screenshots/JSON under ignored `artifacts/`, and the
exact selected-page/clipboard observation. Do not commit generated PDFs, private keys, clipboard data,
or machine-local absolute paths. Record the real text-fixture source and cleanup result in the Evidence
Record below.

## Interfaces and Dependencies

The final interfaces are:

    DocumentTextSelectionEngine.select_all(input_pdf_path: str, *, page_index: int) -> DocumentTextSelection | None
    DocumentTextSelectionSession.select_all(*, page_index: int) -> DocumentTextSelectionState
    DocumentReviewWorkspaceSession.select_all_text(page_index: int) -> DocumentReviewWorkspaceTransition
    SigningWorkspaceRuntime.can_select_all_document_text() -> bool
    SigningWorkspaceRuntime.select_all_document_text() -> DocumentTextSelectionState
    SigningWorkspaceSessionPort.can_select_all_document_text() -> bool
    SigningWorkspaceSessionPort.select_all_document_text() -> DocumentTextSelectionState

`QtPdfDocumentTextSelectionEngine` is the only implementation that may import QPdfDocument. Application
and session protocols use `DocumentTextSelection` and `PdfRect`, never Qt classes. `SigningWorkspaceReviewBridge`
applies the returned transition; `FoliaSealAppFrame` chooses native editor methods before the public
viewer port. The maintenance port remains unchanged. Any compatibility adapter retained temporarily
must name its consumer and retirement condition in this plan.

## Evidence Record

The governing UI_SPEC requirement is the current-page viewer Select All behavior in section 7,
preserving the one-page selection rule in section 8. Focused validation passed with `100 passed`
across the document-selection, workspace, AppFrame/runtime/session-port, and real offscreen Select
All tests. Full validation passed with `1456 passed, 20 skipped, 1 warning`; the
only warning is the existing Pillow `Image.Image.getdata` deprecation in
`tests/unit/test_phase3_harness.py`. The real offscreen flow covers Edit -> Select All/Ctrl+A,
clipboard copy, native-editor precedence, and no-document disablement; the selection engine and
workspace tests cover current-page geometry plus empty/no-text and load-failure soft states. The
bounded GUI launch audit exited through the known isolated `SingleInstanceUnavailable` endpoint;
the process check was clean and its temporary audit root was removed. No new SVG is required: the
existing viewer overlay rendering is the applicable visual surface.

## Revision Notes

Revision note: 2026-08-10 / Codex
Created after a fresh post-`3f0d4f25c` repository/spec audit selected viewer Select All as the next
dependency-ready slice. Native-editor Edit commands remain authoritative when a text widget owns focus;
this child adds only current-page PDF text extraction and the public viewer fallback.
Revision note: 2026-08-10 / Codex
Implemented the engine/session/workspace/runtime/AppFrame path with native precedence, selected-text
capability synchronization, fake-boundary tests, and a real offscreen Qt PDF selection/action/clipboard
test. Remaining gates were documentation reconciliation, full validation, cleanup, and commit; those
gates are now recorded above and this slice is ready for commit.
