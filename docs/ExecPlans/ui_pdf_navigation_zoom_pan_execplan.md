# Page navigation, fit, zoom, and pan

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can navigate pages, choose Fit Page or Fit Width, set exact zoom, and pan without changing pages in the real FoliaSeal GUI. It is mapped to UI_SPEC section 8 and WF01. The
slice is one vertical path through the relevant persistent model,
application workflow, Qt surface, focused tests, and observable acceptance.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are frozen governing contracts.
- [x] docs/ExecPlans/ui_document_lifecycle_recovery_execplan.md (implemented in commits
  `6c1ea9faf` and `e64d289c8`; display-backed acceptance remains an environment limitation only).

## Progress

- [x] (2026-08-09) Audit current behavior and identify the bounded viewer path: the application
  already computes fit zooms, but production Qt exposes only reset zoom; the toolbar has no Fit
  Page/Fit Width controls and the wheel always zooms.
- [x] (2026-08-09) Add failing focused tests for UI_SPEC's 10%–800% limits, typed fit routing,
  default Fit Page behavior, and wheel/scrollbar page invariants; the red run reports four
  expected failures before the new seams exist.
- [x] (2026-08-09) Implement the smallest complete model/application/Qt path: zoom limits are
  10%–800%, typed Fit Page/Fit Width session verbs reach the scroll-aware viewer, View actions and
  toolbar controls are visible, first visible rendering requests Fit Page, Ctrl+wheel zooms, and
  ordinary wheel input pans without page mutation.
- [x] (2026-08-09) Audit compatibility and acceptance product cruft for this path; no migrated
  compatibility consumer was left behind and no acceptance-named product command was introduced.
- [x] (2026-08-09) Focused viewer/shell/frame validation passed (`189 passed`), the real offscreen
  fit/navigation shortcut walkthrough passed (`2 passed`), the full suite passed (`1201 passed,
  20 skipped, 1 warning`), Ruff and diff checks passed, and owned Qt resources were cleaned.
- [x] (2026-08-09) Updated this plan and relevant architecture documentation with the typed fit,
  zoom/pan ownership and recorded evidence; implementation and validation are complete.
- [x] (2026-08-10) Closed the remaining keyboard-contract gap found in a fresh compliance scan:
  UI_SPEC §8 requires `Ctrl+Home`/`Ctrl+End`, while the current viewer consumes bare `Home`/`End`
  as page jumps. The modifier guard now preserves unmodified Home/End for the focused widget
  hierarchy; fake-Qt and real offscreen dispatch prove both paths without changing page invariants.
- [x] (2026-08-10) Final validation after the correction passed: the focused viewer/navigation set is
  `47 passed`, the targeted keyboard subset is `7 passed, 33 deselected`, and the full suite is
  `1482 passed, 20 skipped, 1 warning`. Ruff, `pip check`, and `git diff --check` are clean; no
  FoliaSeal/test processes remain and all owned `/tmp/foliaseal-*` roots were removed.

## Surprises & Discoveries

- Observation: the live viewer currently clamps zoom to 25%–400% and maps wheel events to zoom,
  while UI_SPEC requires 10%–800% and wheel/scrollbar panning that does not change pages.
  Evidence: src/foliaseal/application/viewer_session.py:10-18 and
  src/foliaseal/presentation/qt/viewer_widget.py:141-148.
- Observation: `ViewerWorkflow` already owns fit calculations and the phase2 harness exercises
  them, but the production `SigningWorkspaceWidget`, typed session port, and toolbar do not expose
  those operations. Reusing the harness's fit math at the production viewer boundary avoids a
  guessed fixed viewport and keeps private widget access out of app-frame code.
  Evidence: `src/foliaseal/application/viewer_workflow.py`, `src/foliaseal/presentation/qt/phase2_harness.py`,
  and `src/foliaseal/presentation/qt/signing_workspace_composition.py`.
- Observation: the preview widget is a child of a `QScrollArea`; its render image dimensions are
  scaled by the current zoom, so fit operations can derive the unscaled page extent from the
  rendered snapshot and the current zoom, then refresh once with the computed value.
  Evidence: `PdfPreviewWidget._apply_render_result()` and `ViewerRenderSnapshot`.
- Observation: a real offscreen QTest initially exposed that a fit shortcut test must use the
  production `ScrollablePdfViewer` wrapper rather than the raw preview child; the wrapper owns the
  attached scroll container and is the correct focus target for one-dispatch evidence.
  Evidence: `tests/integration/test_view_navigation_shortcuts.py` now passes both page and fit
  shortcut tests with exactly one render per shortcut.
- Observation: fit transforms preserve overlay coordinates only when the current rendered snapshot
  is used to derive the unscaled page extent; the focused overlay test now asserts the transformed
  rectangle after both Fit Page and Fit Width.
  Evidence: `tests/unit/test_qt_viewer_widget.py::test_fit_modes_preserve_signature_overlay_page_and_coordinates`.

## Decision Log

- Decision: obey SPEC.md, SCHEMAS.md, and UI_SPEC.md in that precedence order.
  Rationale: these are the repository's explicit authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep the slice limited to one user-visible page navigation, fit, zoom, and pan outcome.
  Rationale: narrow changes are independently testable and recoverable.
  Date/Author: 2026-08-09 / Codex
- Decision: implement Fit Page and Fit Width as typed workspace-session verbs that obtain the
  actual scroll-area viewport and current rendered page geometry inside the viewer widget; do not
  pass widget dimensions through the app frame or add fixed viewport constants.
  Rationale: UI_SPEC requires truthful fit behavior across window sizes, and the existing viewer
  already owns the only authoritative render dimensions and scroll container.
  Date/Author: 2026-08-09 / Codex
- Decision: make the wheel pan vertically by default and reserve zoom for Ctrl+wheel, while keeping
  middle-button/Shift-drag panning and page keyboard navigation separate.
  Rationale: UI_SPEC explicitly says wheel and scrollbars pan and never advance pages; modifier
  zoom remains a conventional, discoverable desktop behavior and avoids changing page state.
  Date/Author: 2026-08-09 / Codex
- Decision: expose Fit Page and Fit Width in the typed View command registry and the viewer toolbar,
  and keep unsupported Find, Document Signatures, Back, and Forward commands out of this slice.
  Rationale: these two operations have existing application behavior and satisfy a complete
  observable path; adding placeholder commands would violate UI_SPEC's truthful-action rule.
  Date/Author: 2026-08-09 / Codex
- Decision: use `Ctrl+0` for Fit Page and `Ctrl+Shift+0` for Fit Width, and document both labels
  in the typed registry.
  Rationale: UI_SPEC explicitly reserves `Ctrl+0` for the default fit action; the Shift variant is
  the least surprising adjacent desktop convention for the paired width-fit action, and its visible
  label makes the choice discoverable rather than hiding an invented shortcut.
  Date/Author: 2026-08-09 / Codex
- Decision: consume Home/End for first/last-page navigation only when the Control modifier is
  present; pass bare Home/End through to Qt's ordinary focused-widget behavior.
  Rationale: UI_SPEC §7/§8 reserves `Ctrl+Home`/`Ctrl+End` for document navigation, while bare
  Home/End are conventional text/scroll positioning keys and must not be stolen by the viewer.
  Date/Author: 2026-08-10 / Codex

## Outcomes & Retrospective

The fit/zoom/pan implementation and validation are complete. The fresh keyboard compliance
correction is now complete: only Ctrl+Home/End are consumed for first/last-page navigation, and
bare Home/End reach the base focused-widget handler. The slice still does not claim unfinished
Find, Document Signatures, Back, Forward, or full mode-group/placement behavior owned by later
children.

## Context and Orientation

The relevant code is src/foliaseal/application/viewer_session.py; viewer_workflow.py; presentation/qt/viewer_widget.py; signing shell toolbar. FoliaSeal is a Python/Qt Linux PDF signing application. The
primary flow is open, review, select reusable setup, place one visible signature, preview
readiness, sign/save, verify, and reopen. V1 excludes tabs, printing, broad PDF editing, cloud
workflow, enterprise trust administration, and multiple pending signatures.

A compatibility surface is an adapter retained only for old callers. “acceptance” names identify legacy
evidence/harness infrastructure and must not be introduced into ordinary product UI or new primary
contracts; production backend/evidence imports may be renamed only after a neutral migration proves
the old name is no longer required.

## Change Slice

Primary change class: behavior change. Allowed changes are the named modules, focused tests,
bounded ignored local evidence, and minimum truthful documentation. Do not mix unrelated evidence
rebaselines, V2 features, or packaging work.

## Plan of Work

Expose a single-page viewer with an editable one-based page field, Page Up/Down and Ctrl+Home/End
navigation, Fit Page as the initial view, Fit Width, exact 10%–800% zoom, and wheel/scrollbar pan
that never changes pages. Add typed `fit_page_view()` and `fit_width_view()` session verbs, map
them to the production viewer and toolbar/View menu, and keep render dimensions/viewport queries
inside the viewer boundary. Preserve overlay alignment and page-local render failures. Add or
preserve typed application and public Qt-port boundaries rather than reaching through private
widgets. Keep schema and terminology aligned with the frozen documents. When a legacy path is
replaced, prove its callers are migrated before deleting it.

## Milestones

Milestone 1 changes viewer-session limits and adds red tests for zoom limits and fit state. Milestone
2 adds typed fit verbs, toolbar/View actions, and the default Fit Page presentation. Milestone 3
replaces the wheel event behavior with the specified pan/zoom modifier contract, proves overlay
alignment and page invariants, and records Qt evidence plus cleanup.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e 'zoom|fit|page|wheel|render' src/foliaseal/application/viewer_session.py src/foliaseal/application/viewer_workflow.py src/foliaseal/presentation/qt/viewer_widget.py src/foliaseal/presentation/qt/signing_workspace_composition.py src/foliaseal/presentation/qt/app_frame_command_model.py
    .venv/bin/pytest -q tests/unit/test_viewer_session.py tests/unit/test_viewer_workflow.py tests/unit/test_qt_viewer_widget.py
    .venv/bin/pytest -q tests/integration/test_view_navigation_shortcuts.py
    .venv/bin/pytest -q tests/unit/test_qt_viewer_widget.py -k 'key_press_event or home or end'
    .venv/bin/ruff check src tests
    .venv/bin/pytest -q   # 1201 passed, 20 skipped, 1 warning at this revision
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

Acceptance is behavioral: A user can open a multi-page PDF, see the current page of total pages,
navigate without guessing, start in Fit Page, choose Fit Width, zoom between exactly 10% and 800%,
and pan with wheel/scrollbars without changing pages. Ctrl+wheel and the existing keyboard zoom
keys change zoom without changing pages. Fit/zoom/pan retain the signature overlay on the correct
page. Focused tests must pass, shared-code changes must leave the full suite green, and a real Qt
walkthrough must record the visible controls, input sequence, render state, and cleanup.

## Evidence Record

Before checking this child in the parent, record the governing UI_SPEC requirement, exact focused
test command/result, page/zoom/pan input sequence and observed overlay state, evidence path and
cleanup result, and compatibility grep proof. The focused suite must include the red-before/green-
after registry and typed-port tests; the real Qt test must assert Fit Page/Fit Width action labels,
shortcut metadata, initial enablement, and no page transition when wheel panning.

Record the contributing UI_SPEC scenario ID(s) and either the owning SVG path or an explicit
"no SVG" decision alongside the evidence row.
Also record the exact focused test node and expected result (`N passed`); when the slice adds a new
contract, record that the test was red before implementation and green afterward.

This revision records the concrete evidence: `tests/unit/test_viewer_session.py`,
`tests/unit/test_qt_viewer_widget.py`, `tests/unit/test_signing_workspace_session_port.py`,
`tests/unit/test_qt_app_frame.py`, and `tests/unit/test_qt_signing_shell.py` together passed 189
focused tests after a red run; `tests/integration/test_view_navigation_shortcuts.py` passed 2 real
offscreen QTest cases, including one render per Ctrl+0/Ctrl+Shift+0 fit shortcut and initial Fit
Page state; the full suite passed 1201 tests with 20 skips and one existing Pillow deprecation
warning. The no-document real-Qt menu integration remains green, and process inspection after the
run found no FoliaSeal/PySide6/pytest processes. No SVG is assigned to this viewer-only command
increment; the normative UI_SPEC §8 text and main-workspace SVGs remain the parent/open-review
owners.

The 2026-08-10 correction adds red/green evidence in
`tests/unit/test_qt_viewer_widget.py::test_key_press_event_wires_keyboard_affordances` and
`tests/integration/test_view_navigation_shortcuts.py::test_page_shortcut_navigates_once_with_viewer_focus`:
bare Home/End are forwarded without acceptance or render, while Ctrl+Home/End perform exactly one
page jump/render. The combined viewer/integration command passes `47 passed`; the targeted keyboard
subset passes `7 passed, 33 deselected`.

## Idempotence and Recovery

Use temporary configuration and sibling output paths. If work fails halfway, preserve user PDFs and
drafts, update Progress with completed/remaining work, clean owned processes and artifacts, and
retry from the recorded state. Do not resurrect removed compatibility paths.

## Artifacts and Notes

Record concise output, focused screenshots or JSON under ignored artifacts/when useful, and exact
changed files. Never commit private keys, passwords, generated PDFs, or machine-local absolute paths.

## Interfaces and Dependencies

Use the existing typed application workflows, schema models, persistence stores, and public Qt frame
or workspace ports. The final behavior must be exercised by tests/unit/test_viewer_session.py tests/unit/test_viewer_workflow.py tests/unit/test_qt_viewer_widget.py. Any temporary adapter must
name its remaining consumer and retirement condition in this plan.

At completion, `SigningWorkspaceSessionPort` and `QtSigningWorkspaceSessionPort` expose
`fit_page_view() -> None` and `fit_width_view() -> None`; `SigningWorkspaceWidget` forwards those
verbs to the scroll-aware viewer. `VIEW_COMMAND_DEFINITIONS` owns the stable IDs and shortcuts, while
`ViewerSession.zoom_limits` reports the 0.10–8.0 range and `zoom_mode` reports the active fit/custom
projection for tests and diagnostics.

Revision note: 2026-08-09 / Codex
Created as a dependency-ordered child of the approved SPEC/UI_SPEC compliance breakdown.
Revision note: 2026-08-09 / Codex
Re-audited after the typed text-command commit. Marked the implemented lifecycle predecessor
complete, narrowed this slice to truthful production Fit Page/Fit Width plus 10%–800% zoom and
wheel-pan semantics, and recorded the existing harness fit math and typed-port gaps.
