# Search, text selection, and copy

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can whole-document search and current-page keyboard/pointer text selection with copy feedback in the real FoliaSeal GUI. It is mapped to UI_SPEC section 8 and acceptance scenarios 1 and 8. The
slice is one vertical path through the relevant persistent model,
application workflow, Qt surface, focused tests, and observable acceptance.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are frozen governing contracts.
- [x] docs/ExecPlans/ui_pdf_navigation_zoom_pan_execplan.md (commit `2a7ff3d38`)

## Progress

- [x] (2026-08-09) Audit current behavior and add a failing focused test.
- [x] (2026-08-10) Implement the smallest complete model/application/Qt path: search-match geometry and strong/quiet overlays, typed View → Find focus, and Enter/Shift+Enter navigation.
- [x] (2026-08-10) Audit compatibility and phase3 product cruft; no migrated compatibility path remained in this search boundary, and the Shift+Enter shortcut now uses injected Qt bindings.
- [x] (2026-08-10) Run focused/offscreen/full validation and clean owned processes/artifacts: the
  document/search/viewer/shell/sidebar/app-frame focused set passes `223 passed`, and five real
  offscreen Qt cases cover initial fit, View shortcut dispatch, Ctrl+F focus/select-all, and
  Enter/Shift+Enter navigation; the full suite passes `1209 passed, 20 skipped, 1 warning`.
- [x] (2026-08-10) Update this plan and relevant architecture documentation; the final commit
  remains the handoff gate.

## Surprises & Discoveries

- Observation: text search and selection are application services consumed by the viewer; this
  child must keep highlighting and copy behavior independent of private Qt child-widget state.
  Evidence: the live source paths and focused tests listed below are the audit baseline.

## Decision Log

- Decision: obey SPEC.md, SCHEMAS.md, and UI_SPEC.md in that precedence order.
  Rationale: these are the repository's explicit authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep the slice limited to one user-visible search, text selection, and copy outcome.
  Rationale: narrow changes are independently testable and recoverable.
  Date/Author: 2026-08-09 / Codex
- Decision: keep search and selection highlight state separate, with current-match rectangles
  rendered strongly and other matches on that page rendered quietly.
  Rationale: UI_SPEC §8 requires independent search/selection and distinct current/same-page
  emphasis; a shared rectangle store would erase one interaction when the other changes.
  Date/Author: 2026-08-10 / Codex
- Decision: derive match geometry in the Qt PDF infrastructure adapter and project it through typed
  `PdfRect` values; each Qt selection polygon is reduced to its page-local bounding rectangle.
  Rationale: application and viewer boundaries must not expose QPdfDocument, while the existing
  selection adapter establishes the same bottom-left PDF coordinate conversion. Multi-polygon bounds
  remain a documented conservative highlight shape for this slice.
  Date/Author: 2026-08-10 / Codex
- Decision: use the injected `QtSigningWidgetBindings.q_shortcut`/`q_key_sequence` seam for
  Shift+Return rather than importing Qt directly from the sidebar.
  Rationale: real Qt receives the conventional shortcut while fake-boundary tests remain possible;
  no compatibility fallback is retained when the bindings are absent.
  Date/Author: 2026-08-10 / Codex
- Decision: clear current-page selection when navigation changes page, while preserving search
  status/highlights; same-page search navigation leaves selection independent.
  Rationale: UI_SPEC §8 clears selection on page change but explicitly keeps search and selection
  independent.
  Date/Author: 2026-08-10 / Codex

## Outcomes & Retrospective

Implementation and focused/offscreen/full validation are complete. `DocumentTextMatch` now carries
page-local geometry, the review session emits separate search current/quiet effects, the viewer
renders both without replacing selection overlays, and View → Find (`Ctrl+F`) focuses/selects the
workspace query through a typed session port. Qt PDF load failures distinguish
password/protection/parser cases; empty-text PDFs distinguish image objects from no extractable
text without implying OCR. The final commit remains the only completion gate. The
viewer search geometry intentionally uses conservative per-polygon bounding rectangles;
fragmented/multi-line visual fidelity remains a later refinement if real PDFs demonstrate excessive
whitespace.

## Context and Orientation

The relevant code is src/foliaseal/application/document_text_search.py; document_text_selection.py; presentation/qt/viewer_widget.py; signing shell actions. FoliaSeal is a Python/Qt Linux PDF signing application. The
primary flow is open, review, select reusable setup, place one visible signature, preview
readiness, sign/save, verify, and reopen. V1 excludes tabs, printing, broad PDF editing, cloud
workflow, enterprise trust administration, and multiple pending signatures.

A compatibility surface is an adapter retained only for old callers. “phase3” names identify legacy
evidence/harness infrastructure and must not be introduced into ordinary product UI or new primary
contracts; production backend/evidence imports may be renamed only after a neutral migration proves
the old name is no longer required.

## Change Slice

Primary change class: behavior change. Allowed changes are the named modules, focused tests,
bounded ignored local evidence, and minimum truthful documentation. Do not mix unrelated evidence
rebaselines, V2 features, or packaging work.

## Plan of Work

Implement Ctrl+F whole-document search with current/total, next/previous and strong-current/quiet-
same-page highlights, Enter/Shift+Enter navigation, and a typed public focus seam from the app frame
to the workspace search field. Extend the existing Qt PDF adapter to return page-local match geometry
through `PdfRect` values, keeping QPdfDocument private to infrastructure. Preserve the mutually
exclusive current-page text-selection mode and copy feedback, and keep search and selection overlays
independent. Distinguish image-only/no-extractable-text, password or permission, and parser/load
failures without implying OCR. Add or preserve typed application and public Qt-port boundaries rather
than reaching through private widgets. Keep schema and terminology aligned with the frozen documents.
When a legacy path is replaced, prove its callers are migrated before deleting it.

## Milestones

Milestone 1 tests search normalization, typed match geometry, failure copy, selection ranges, and
copy behavior at the application boundary. Milestone 2 wires current/quiet search highlights and
typed View → Find focus/keyboard navigation to the viewer without private widget access. Milestone 3
records a GUI search/selection observation and cleanup evidence.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e 'search|selection|copy|highlight|Ctrl\\+F|Return' src/foliaseal/application/document_text_search.py src/foliaseal/application/document_text_selection.py src/foliaseal/application/document_review_workspace.py src/foliaseal/presentation/qt/viewer_widget.py src/foliaseal/presentation/qt/signing_workspace_sidebar.py src/foliaseal/presentation/qt/app_frame_command_model.py
    .venv/bin/pytest -q tests/unit/test_document_text_search.py tests/unit/test_document_text_selection.py tests/unit/test_document_review_workspace.py tests/unit/test_qt_viewer_widget.py tests/unit/test_qt_app_frame.py
    .venv/bin/pytest -q tests/integration/test_view_navigation_shortcuts.py tests/integration/test_gui_launch_no_document.py tests/integration/test_signing_rail_layout.py
    .venv/bin/ruff check src tests
    .venv/bin/pytest -q
    git diff --check

Run this bounded walkthrough from /home/daekar/FoliaSeal with an isolated configuration root:

    audit_root=$(mktemp -d /tmp/foliaseal-plan-audit-XXXXXX)
    timeout --foreground 30s env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf || test "$?" -eq 124
    ps -eo pid,cmd | rg 'FoliaSeal|foliaseal|PySide6|pytest' | rg -v 'rg ' || true
    rm -rf "$audit_root"
    test ! -e "$audit_root"

Expected evidence is the stated user-visible behavior plus a mandatory Qt-test or display-backed
walkthrough. Record the exact input sequence, widget state, expected observation, evidence path, and
cleanup result; the bounded timeout is only a lifecycle check.

## Validation and Acceptance

Acceptance is behavioral: Keyboard and pointer users can focus Find with Ctrl+F, search the whole
PDF, see current/total state, use Enter/Shift+Enter and Previous/Next, see a strong current match and
quiet same-page matches, select current-page text independently, copy it, and understand why copying
or searching is unavailable when it is unavailable. Focused tests must pass, shared-code changes must
leave the full suite green, and the GUI audit must record the visible result and cleanup.

## Evidence Record

Before checking this child in the parent, record the governing UI_SPEC requirement, exact focused
test command/result, search/selection/copy input sequence and observed viewer state, evidence path
and cleanup result, and compatibility grep proof.

Record the contributing UI_SPEC scenario ID(s) and either the owning SVG path or an explicit
"no SVG" decision alongside the evidence row.
Also record the exact focused test node and expected result (`N passed`); when the slice adds a new
contract, record that the test was red before implementation and green afterward.

Current evidence: the red application/command/workspace tests failed before implementation; the
focused document/search/viewer/shell/sidebar/app-frame suite passes `223 passed`; the real offscreen
Qt set passes five cases, including initial viewer fit, View shortcut dispatch, Ctrl+F focus/select-all,
and Enter/Shift+Enter search navigation; Ruff and `git diff --check` pass. No SVG is assigned to this
search/text slice: UI_SPEC §8 is normative and the existing main-workspace SVGs do not define the
search result overlay treatment. Empty-text and Qt load-error classification tests cover image-only,
no-extractable-text, password/protection, invalid-format, and unknown parser paths. The full suite
passes `1209 passed, 20 skipped, 1 warning`; the warning is the existing Pillow deprecation in the
legacy Phase 3 harness test. Process inspection after both focused and full runs found no FoliaSeal,
PySide6, or pytest processes, and no temporary audit root or generated artifact was left behind.

## Idempotence and Recovery

Use temporary configuration and sibling output paths. If work fails halfway, preserve user PDFs and
drafts, update Progress with completed/remaining work, clean owned processes and artifacts, and
retry from the recorded state. Do not resurrect removed compatibility paths.

## Artifacts and Notes

Record concise output, focused screenshots or JSON under ignored artifacts/when useful, and exact
changed files. Never commit private keys, passwords, generated PDFs, or machine-local absolute paths.

## Interfaces and Dependencies

Use the existing typed application workflows, schema models, persistence stores, and public Qt frame
or workspace ports. The final behavior must be exercised by
`tests/unit/test_document_text_search.py`, `tests/unit/test_document_text_selection.py`,
`tests/unit/test_document_review_workspace.py`, `tests/unit/test_qt_viewer_widget.py`,
`tests/unit/test_qt_app_frame.py`, and a real/offscreen integration test for View → Find. Any
temporary adapter must name its remaining consumer and retirement condition in this plan.

Implementation boundary for this revision: `DocumentTextMatch.highlight_rects` carries immutable
page-local geometry; `DocumentReviewWorkspaceViewerEffects` carries separate search current/quiet
rects from selection rects; the bridge invokes a public search-overlay viewer method; and
`SigningWorkspaceSessionPort.focus_document_search()` is the only app-frame-to-search-focus seam.
`QtSigningWidgetBindings` owns the optional QShortcut/QKeySequence types used for Shift+Return.

Revision note: 2026-08-09 / Codex
Created as a dependency-ordered child of the approved SPEC/UI_SPEC compliance breakdown.
Revision note: 2026-08-09 / Codex
Re-audited after viewer fit/zoom/pan commit `2a7ff3d38`; narrowed the remaining search slice to
production match geometry, independent strong/quiet overlays, typed Find focus, keyboard navigation,
and truthful unavailable-text failure copy.
Revision note: 2026-08-10 / Codex
Implemented and re-audited the production search path, injected the keyboard shortcut boundary,
added page-change selection clearing, and recorded focused/offscreen/full evidence; documentation is
reconciled and the final commit is the remaining handoff gate.
