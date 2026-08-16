# Keyboard, numeric geometry, snap, and undo/redo

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

This child gives a keyboard-only user centered placement creation, exact movement, deletion, and
local undo/redo history in the real FoliaSeal GUI. It is mapped to UI_SPEC section 8 and acceptance
scenarios 3 and 8. Resize, numeric traversal, snapping, and off-page recovery remain subsequent
increments because they require additional geometry and focus seams.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are frozen governing contracts.
- [x] docs/ExecPlans/ui_pointer_signature_placement_execplan.md (pointer drag, Escape cancellation,
  and explicit Pan/Place topology are implemented; keyboard/history work remains here)

## Progress

- [x] (2026-08-10) Audited the keyboard-placement requirements and split the broad child at the
  next truthful seam: centered Enter creation plus exact Arrow/Shift+Arrow movement, followed by
  a typed local history seam for Delete and undo/redo.
- [x] (2026-08-10) Implemented typed application placement creation/movement and routed keyboard
  callbacks through the runtime/composition boundary; Enter and exact movement are consumed only in
  Place mode and do not alter Pan/Text behavior.
- [x] (2026-08-10) Reviewed compatibility and acceptance product cruft; no migrated consumer retirement
  condition was proven in this viewer/application seam.
- [x] (2026-08-10) Focused viewer/session/shell/composition/offscreen validation passed (`165 passed`)
  and the full suite passed (`1304 passed, 20 skipped, 1 warning`); bounded GUI launch cleanup is
  confirmed, with the known isolated `SingleInstanceUnavailable` endpoint limitation.
- [x] (2026-08-10) Added `PlacementHistory` at the application boundary and wired Place-mode Delete,
  Ctrl+Z, Ctrl+Shift+Z, and Escape-to-Pan through the viewer/runtime seam. External overlay changes
  synchronize and clear stale history, while lifecycle clearing remains explicit. Focused coverage
  is now `159 passed`.
- [x] (2026-08-10) The offscreen integration sequence also covers Delete, undo, redo, and
  Escape-to-Pan against the real Qt widget; the focused viewer/history/integration set remains
  green (`159 passed`).
- [x] (2026-08-10) Added exact Ctrl+Arrow/Ctrl+Shift+Arrow resize from the fixed bottom/left
  anchor through `ViewerInteractionSession` and the runtime/viewer seam. Invalid non-positive
  dimensions are rejected without clamping; resize mutations enter the same local history. The
  focused application/viewer/integration/runtime set is green (`49 passed` plus `120 passed`), and
  the full suite is `1307 passed, 20 skipped, 1 warning`.
- [x] (2026-08-10) Made direct placement-field edits history-aware through the public viewer/runtime
  seam and gave Page/Left/Bottom/Width/Height controls accessible names plus deterministic tab order.
  Focused viewer/form/runtime coverage is `50 passed`; the full suite is `1308 passed, 20 skipped,
  1 warning`. Numeric traversal remains a follow-up only for richer field-level commands.
- [x] (2026-08-10) Added the pointer-only page-guide snap seam: edges and centers snap within an
  8-point threshold, Alt bypasses the policy, and the viewer paints the resulting guide lines.
  Keyboard and numeric operations never call the snap helper. Focused coordinate/viewer coverage is
  green (`63 passed`); the full suite is `1311 passed, 20 skipped, 1 warning`; off-page recovery
  remains open.
- [x] (2026-08-10) Added off-page recovery: Place-mode `M` moves a non-oversized placement fully
  onto the visible page without scaling, oversized placements explain that resize is required, and
  red page-edge indicators remain visible while a placement crosses a page boundary. The focused
  viewer/application/integration set is `54 passed`; the full suite is `1314 passed, 20 skipped,
  1 warning`.
- [x] (2026-08-10) Completed history lifecycle policy: placement edits append to history, non-
  placement setup changes clear it, external overlay synchronization clears stale branches, and a
  successful signing transition clears the remaining local history. The focused shell/runtime
  validation remains green; no compatibility adapter was widened.
- [x] (2026-08-10) Completed the child behavior tranche: numeric-field traversal, exact placement
  history, pointer snap/guides, off-page recovery, and lifecycle clearing are implemented. Only
  final audit/commit closeout remains.

## Surprises & Discoveries

- Observation: keyboard placement currently spans workspace interaction state and viewer input;
  this child must provide an equivalent path without relying on pointer-only widget focus.
  Evidence: the live source paths and focused tests listed below are the audit baseline.

## Decision Log

- Decision: obey SPEC.md, SCHEMAS.md, and UI_SPEC.md in that precedence order.
  Rationale: these are the repository's explicit authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep each keyboard increment limited to one user-visible placement outcome and one typed
  state seam.
  Rationale: creation/movement and history mutation are independently testable and recoverable.
  Date/Author: 2026-08-09 / Codex

## Outcomes & Retrospective

The creation/movement and history increments are complete: Place-mode Enter creates a centered
3×1-inch placement scaled proportionally to a smaller page; Arrow/Shift+Arrow move it by exact
1/10-point deltas; Ctrl+Arrow/Ctrl+Shift+Arrow resize from the fixed anchor by exact 1/10-point
deltas; Delete removes it; and Ctrl+Z/Ctrl+Shift+Z restore local placement mutations. Escape exits
Place mode to Pan while preserving a completed overlay. Numeric fields now follow deterministic Tab
order, pointer snap/guides are Alt-bypassable, off-page placements are visibly recoverable, and the
history lifecycle clears at product boundaries. The child behavior tranche is complete.
History also clears on non-placement setup changes and successful signing, while external overlay
synchronization prevents stale branches from crossing document or panel boundaries.

## Context and Orientation

The relevant code is signing_workspace_properties_panel.py; viewer widget keyboard handling; workspace interaction session; undo history. FoliaSeal is a Python/Qt Linux PDF signing application. The
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

Add Enter-created centered 3x1-inch placement, arrow/Shift movement, Ctrl resize, Tab traversal, Delete removal, exact numeric operations, edge/center snap with Alt bypass, off-page recovery, one-step drag history, Escape rollback, and history clearing at specified lifecycle boundaries. Add or preserve typed application and public Qt-port boundaries rather than reaching
through private widgets. Keep schema and terminology aligned with the frozen documents. When a
legacy path is replaced, prove its callers are migrated before deleting it.

## Milestones

Milestone 1 adds keyboard movement, resize, undo, redo, delete, and snap tests at the interaction
boundary. Milestone 2 connects focus-independent commands to the viewer and properties panel.
Milestone 3 proves keyboard-only placement and records the GUI observation and cleanup.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e 'Arrow|resize|Delete|Undo|Redo|snap' src/foliaseal/presentation/qt/signing_workspace_properties_panel.py src/foliaseal/application/workspace_interaction_session.py src/foliaseal/presentation/qt/viewer_widget.py
    .venv/bin/pytest -q tests/unit/test_workspace_interaction_session.py tests/unit/test_qt_viewer_widget.py
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

Acceptance is behavioral: A keyboard-only user can create, move, resize, remove, undo, redo, and recover an off-page placement without pointer precision or silent clamp/scale. Focused tests must pass, shared-code changes must
leave the full suite green, and the GUI audit must record the visible result and cleanup.

## Evidence Record

Before checking this child in the parent, record the governing UI_SPEC requirement, exact focused
test command/result, keyboard input sequence and observed rectangle/undo state, evidence path and
cleanup result, and compatibility grep proof.

Record the contributing UI_SPEC scenario ID(s) and either the owning SVG path or an explicit
"no SVG" decision alongside the evidence row.
Also record the exact focused test node and expected result (`N passed`); when the slice adds a new
contract, record that the test was red before implementation and green afterward.

## Idempotence and Recovery

Use temporary configuration and sibling output paths. If work fails halfway, preserve user PDFs and
drafts, update Progress with completed/remaining work, clean owned processes and artifacts, and
retry from the recorded state. Do not resurrect removed compatibility paths.

## Artifacts and Notes

Record concise output, focused screenshots or JSON under ignored artifacts/when useful, and exact
changed files. Never commit private keys, passwords, generated PDFs, or machine-local absolute paths.

## Interfaces and Dependencies

Use the existing typed application workflows, schema models, persistence stores, and public Qt frame
or workspace ports. The final behavior must be exercised by tests/unit/test_workspace_interaction_session.py tests/unit/test_qt_viewer_widget.py and the relevant signing-shell Qt tests. Any temporary adapter must
name its remaining consumer and retirement condition in this plan.

Revision note: 2026-08-10 / Codex
Implemented the complete keyboard/numeric placement behavior, pointer snap/guides, off-page
recovery, and explicit history lifecycle after the Pan/Place topology landed. Final audit and
commit closeout are recorded in the parent plan.
