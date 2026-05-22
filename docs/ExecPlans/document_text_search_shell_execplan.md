# Add document text search and copy-current-hit to the signing shell

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows the requirements in `.agents/skills/write-execplan/PLANS.md`. It is self-contained so a contributor can resume the slice from only this file and the current repository tree.

## Purpose / Big Picture

`docs/SPEC.md` requires the V1 GUI to let users review PDFs with document text search and text copy. Today FoliaSeal can inspect signatures, navigate pages, zoom, pan, and place visible signatures, but it cannot search document text or copy reviewed text anywhere in the GUI. This slice adds the smallest meaningful step toward that requirement: a read-only document-text search card in the signing shell that can search the active PDF, step through hits, jump the viewer to the hit page, and copy the current hit text.

This slice is intentionally narrow. It does not add arbitrary freeform text selection, highlight overlays, or a broad viewer redesign. It adds one application-layer search state boundary, one concrete Qt PDF text-search adapter, and one shell card that exposes search, next/previous result navigation, and copy-current-hit behavior.

The allowed change classes are one behavior change commit for the search/copy feature and one documentation/status update commit if compliance review requires it. Preview refactors, arbitrary text-selection geometry, and unrelated trust/timestamp work are explicitly out of scope.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/viewer_signature_review_summary_execplan.md` completed first so the shell already has a document-review injection seam and a read-only review-card pattern.
- [x] `docs/ExecPlans/signing_shell_behavior_surface_execplan.md` completed first so the shell surface is already narrowed and recent shell seam debt is resolved.
- [ ] A later child ExecPlan may add arbitrary text selection/highlighting if the V1 release bar still requires stronger `select/copy` semantics than copy-current-hit.

## Progress

- [x] (2026-05-22T15:00:00Z) Completed the required `explorer-light` audit and fixed the next SPEC-alignment slice to document text search plus copy-current-hit rather than freeform text selection.
- [x] (2026-05-22T15:00:00Z) Reviewed `docs/SPEC.md`, `src/foliaseal/presentation/qt/signing_shell.py`, `src/foliaseal/presentation/qt/viewer_widget.py`, `src/foliaseal/application/viewer_workflow.py`, and `tests/unit/test_qt_signing_shell.py` before drafting this plan.
- [x] (2026-05-22T16:10:00Z) Added `src/foliaseal/application/document_text_search.py` with `DocumentTextSearchSession`, immutable search-state dataclasses, and unit coverage in `tests/unit/test_document_text_search.py`.
- [x] (2026-05-22T16:20:00Z) Added `src/foliaseal/infra/document_text_search.py` with a `QPdfDocument`-backed search adapter that uses Qt PDF text primitives instead of introducing a second parser dependency.
- [x] (2026-05-22T16:35:00Z) Added a read-only `Document text` card to `src/foliaseal/presentation/qt/signing_shell.py` with query, next/previous, and copy-current-hit behavior plus shell integration coverage.
- [x] (2026-05-22T17:02:00Z) Focused validation passed: `pytest tests/unit/test_document_text_search.py tests/unit/test_qt_signing_shell.py`, `ruff check src/foliaseal/application/document_text_search.py src/foliaseal/infra/document_text_search.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_document_text_search.py tests/unit/test_qt_signing_shell.py`, and `git diff --check`.
- [x] (2026-05-22T17:25:00Z) Completed the required `explorer-light` compliance review, fixed stale architecture/ExecPlan text, and added shell coverage for the default clipboard callback path.
- [x] (2026-05-22T17:25:00Z) Recorded the next remaining SPEC-alignment gap after search/copy-current-hit and brought the ExecPlan to pre-commit final state.

## Surprises & Discoveries

- Observation: the current viewer already has the right rendering/page-navigation seam but no text model at all.
  Evidence: `src/foliaseal/presentation/qt/viewer_widget.py` only handles render, zoom, pan, and geometric selection; `src/foliaseal/application/viewer_workflow.py` has no text/search state.

- Observation: the installed PySide6 Qt PDF bindings expose text primitives, so this slice can avoid a new PDF parser dependency.
  Evidence: `PySide6/QtPdf.pyi` defines `QPdfDocument.getAllText(page)` and `QPdfDocument.getSelectionAtIndex(page, startIndex, maxLength)`.

## Decision Log

- Decision: deliver copy-current-hit in this slice instead of arbitrary freeform text selection.
  Rationale: it materially advances both `search document text` and `select/copy document text` from `docs/SPEC.md` while avoiding page-to-text coordinate mapping, highlight rendering, and selection-mode conflicts with signature placement.
  Date/Author: 2026-05-22 / Codex

- Decision: add an application-layer search session boundary with a concrete Qt PDF search adapter underneath it.
  Rationale: the missing blocker is not just widget wiring; it is the lack of reusable search/query state. The shell should render state and route actions, not own text-search logic directly.
  Date/Author: 2026-05-22 / Codex

## Outcomes & Retrospective

Implementation now adds a shell-level `Document text` review card that lets a user search the active PDF, step through hits, copy the current hit text, and jump the viewer to the hit page without changing placement-selection behavior. The search logic now lives behind an application-layer `DocumentTextSearchSession`, and the default desktop path uses a concrete `QPdfDocument` adapter so the feature reuses the existing Qt PDF dependency surface. The navigation behavior clamps at the first/last hit instead of cycling, and the final shell tests cover both the injected copy callback seam and the default Qt clipboard callback seam.

The compliance review initially found stale architecture/ExecPlan text plus a missing default-clipboard-path test. Those issues are now closed. After this slice lands, the next remaining SPEC-alignment gap will be stronger review ergonomics: arbitrary text selection/highlighting if the current copy-current-hit behavior is judged insufficient, or deeper per-signature inspection and verification guidance if search/copy is accepted as complete for the text-review requirement.

## Context and Orientation

The main GUI composition surface is `src/foliaseal/presentation/qt/signing_shell.py`. `SigningWorkspaceWidget` already owns read-only `Signing flow`, `Document review`, and `Document text` cards, and this slice extends that review-oriented card pattern rather than introducing a separate viewer mode. The shell also already owns viewer-page coordination through `_handle_page_change()` and shell-to-viewer refresh wiring through `refresh_viewer()`.

The viewer rendering path is in `src/foliaseal/presentation/qt/viewer_widget.py` and `src/foliaseal/application/viewer_workflow.py`. These modules already support page navigation, zoom, pan, and geometric drag selection for signature placement. They do not track text, search hits, clipboard state, or text selection.

The app frame in `src/foliaseal/presentation/qt/app_frame.py` already constructs the shell per opened PDF and injects document-centric behavior such as reopen-after-sign. The shell builder pattern already supports optional injected helpers such as `DocumentReviewInspector`, which gives this slice a natural seam for an additional document-review-oriented helper.

This slice adds a new application-layer boundary in a file such as `src/foliaseal/application/document_text_search.py`. In this repository, a “search session” means an object that owns the active query, the immutable hit list for that query, the current hit index, and plain-language state for the UI. It does not own rendering. A concrete Qt PDF adapter underneath it should open the current PDF path and enumerate text matches page by page using `QPdfDocument`.

## Plan of Work

First, add a new application module for document-text search state, for example `src/foliaseal/application/document_text_search.py`. Define immutable dataclasses for one text match and one search state summary, plus a protocol for a lower-level search engine. Add a small session object that accepts the current PDF path and a concrete engine, performs a search for a query string, tracks current hit index, returns `next`/`previous` states, and exposes the current hit text for copy operations. The state object should already contain user-facing status text so the shell does not duplicate formatting rules.

Second, add a concrete Qt PDF search adapter in `src/foliaseal/infra/` or another concrete-adapter layer. It should use `PySide6.QtPdf.QPdfDocument` to load the current PDF path, iterate all pages, call `getAllText(page).text()` to find matches, and call `getSelectionAtIndex(page, startIndex, maxLength)` to capture the exact matched text. Match search should be case-insensitive and should preserve original case in copied text. The adapter must fail soft for missing/unreadable PDFs and surface a user-actionable message instead of raising uncaught exceptions into the shell.

Third, extend `SigningShellAdapter.create()` / `build_qt_signing_shell()` and `SigningWorkspaceWidget` to accept an optional document-text search session or engine dependency plus an optional text-copy callback. The default Qt path should build a concrete adapter and, when PySide6 clipboard access is available, copy text through the platform clipboard. The shell should add a new `Document text` group box with a query line edit, `Find`, `Previous`, `Next`, and `Copy result` buttons, plus one status/detail label. `Find` should perform a search, jump the viewer to the current hit page, and refresh navigation. `Previous` and `Next` should clamp at the first/last hit while keeping the viewer page synchronized. `Copy result` should copy only the current hit text.

Fourth, add focused tests. Create a new unit file for the application search session, for example `tests/unit/test_document_text_search.py`, using fake engine results to prove blank query behavior, no-hit behavior, next/previous navigation, copyable text exposure, and failure-state messaging. Update `tests/unit/test_qt_signing_shell.py` with a shell integration test that injects a fake text-search engine and a fake copy callback, performs a search through the new controls, asserts the status text, page jump, and copy behavior, and proves that the new card does not break existing shell construction or signing behavior.

Fifth, run focused validation, then perform the required compliance review against `docs/SPEC.md`, `docs/ARCHITECTURE.md`, and this ExecPlan. If the review finds stale documentation, update the relevant docs and rerun the focused checks.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

Inspect the relevant files before editing:

    sed -n '80,95p' docs/SPEC.md
    sed -n '1768,2260p' src/foliaseal/presentation/qt/signing_shell.py
    sed -n '1,220p' src/foliaseal/presentation/qt/viewer_widget.py
    sed -n '35,120p' /home/daekar/FoliaSeal/.venv/lib/python3.12/site-packages/PySide6/QtPdf.pyi

After adding the application search session, run the focused application tests:

    pytest tests/unit/test_document_text_search.py

After wiring the shell card, run the focused integration set:

    pytest tests/unit/test_document_text_search.py tests/unit/test_qt_signing_shell.py

Then run focused lint:

    ruff check src/foliaseal/application/document_text_search.py src/foliaseal/infra/document_text_search.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_document_text_search.py tests/unit/test_qt_signing_shell.py

Finally ensure patch hygiene:

    git diff --check

If compliance review requires documentation changes, rerun the relevant focused checks and record the final passing commands in this plan.

## Validation and Acceptance

Acceptance is behavioral. After the change, a user in the signing shell must be able to type a query, find text in the active PDF, move between hits, have the viewer jump to the hit page, and copy the current hit text without entering a separate viewer mode.

The proof points are:

- `tests/unit/test_document_text_search.py` passes and proves blank-query, no-hit, navigation, and copyable-text state.
- `tests/unit/test_qt_signing_shell.py` passes and includes a shell-level test for search, page synchronization, and copy-current-hit behavior.
- the copy path is disabled or inert when there is no current hit text.
- focused `ruff check` and `git diff --check` pass.

This slice is complete when those proofs hold and the compliance review confirms that the implementation is aligned with the `search document text` / `select/copy document text` portion of `docs/SPEC.md` at the intended first-pass level.

## Idempotence and Recovery

This feature is read-only with respect to PDFs and configuration state. Re-running searches, navigating hits, and copying current-hit text should not mutate the document or signing draft.

Implement the application-layer session first, then wire the shell card, and remove no existing selection behavior. If a shell integration test fails, keep the search logic behind the injected engine/session seam and fix the shell wiring rather than coupling it directly to viewer internals. If the default Qt clipboard callback is unavailable, leave copy disabled in the default path and keep the injected callback seam for tests and future platform-specific wiring.

## Artifacts and Notes

Current gap evidence before the change:

    docs/SPEC.md
    - V1 requires `search document text` and `select/copy document text`.

    src/foliaseal/presentation/qt/viewer_widget.py
    - only geometric drag-selection exists today, for signature placement.

    src/foliaseal/application/viewer_workflow.py
    - no text extraction or search state exists.

    PySide6/QtPdf.pyi
    - `QPdfDocument.getAllText(page)` and `QPdfDocument.getSelectionAtIndex(page, startIndex, maxLength)` are available for a concrete adapter.

Validation evidence after implementation:

    pytest tests/unit/test_document_text_search.py tests/unit/test_qt_signing_shell.py
    - passed on 2026-05-22

    ruff check src/foliaseal/application/document_text_search.py src/foliaseal/infra/document_text_search.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_document_text_search.py tests/unit/test_qt_signing_shell.py
    - passed on 2026-05-22

    git diff --check
    - passed on 2026-05-22

## Interfaces and Dependencies

At the end of this slice, the application-layer search boundary should have a shape along these lines:

    @dataclass(frozen=True)
    class DocumentTextMatch:
        page_index: int
        start_index: int
        end_index: int
        text: str
        context: str

    @dataclass(frozen=True)
    class DocumentTextSearchState:
        query: str
        match_count: int
        current_index: int | None
        status_text: str
        detail_text: str
        current_match: DocumentTextMatch | None
        can_go_previous: bool
        can_go_next: bool
        can_copy: bool

    class DocumentTextSearchEngine(Protocol):
        def search(self, input_pdf_path: str, query: str) -> tuple[DocumentTextMatch, ...]:
            ...

    class DocumentTextSearchSession:
        def search(self, query: str) -> DocumentTextSearchState: ...
        def next_match(self) -> DocumentTextSearchState: ...
        def previous_match(self) -> DocumentTextSearchState: ...
        def current_copy_text(self) -> str | None: ...

The concrete Qt adapter should use `PySide6.QtPdf.QPdfDocument` and should not leak Qt objects into the application-layer state. The shell should consume only `DocumentTextSearchState` plus the current-copy-text string.

Change note: 2026-05-22 / Codex

Created this ExecPlan from the required `explorer-light` findings for the next SPEC-alignment slice. It will be updated after implementation and compliance review to record the completed document-text search/copy-current-hit feature and the next remaining SPEC gap.
