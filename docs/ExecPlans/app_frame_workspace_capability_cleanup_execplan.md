# AppFrame workspace capability cleanup

This ExecPlan is a living document. Keep `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` current while executing it.

## Purpose / Big Picture

`FoliaSealAppFrame` already has a typed `WorkspaceHandle` published by the
workspace-open boundary, but two source-recovery paths still reach the active
workspace through the older `current_signing_workflow` and `current_shell`
properties. That duplicates the active-workspace lookup and keeps lifecycle
code coupled to compatibility-oriented accessors. This slice makes the
source-recovery path consume one typed `WorkspaceHandle` capability instead.

The existing `current_*` properties remain as narrow, typed read seams for the
current test and integration contract; removing them would be a separate API
migration, not an incidental cleanup. No GUI behavior, signing policy, or
Wayland probing is part of this slice.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/app_frame_workspace_open_boundary_execplan.md` — publishes `WorkspaceHandle`.
- [x] `docs/ExecPlans/app_frame_workspace_snapshot_execplan.md` — establishes frame-owned current-workspace state.
- [x] `docs/ExecPlans/signing_workspace_lifecycle_hybrid_execplan.md` — establishes typed workspace/session seams.

## Progress

- [x] (2026-08-16) Explorer audit selected this as the strongest dependency-ready AFK slice; external display/package gates and Wayland remain excluded.
- [x] (2026-08-16) Confirmed the only production direct property reads are in `_ignore_source_change`; all other `current_*` references are definitions or test/integration assertions.
- [x] (2026-08-16) Added one typed `_with_current_workspace(...)` capability helper and migrated source-change acknowledgement/refresh to it.
- [x] (2026-08-16) Routed source-safety refresh through `SigningWorkspacePort.refresh_source_safety()` so the AppFrame never inspects the opaque view mount target.
- [x] (2026-08-16) Added focused regression coverage for the capability helper and source-change path; the focused AppFrame/workspace/shell set passes (`189 passed`) and Ruff passes.
- [x] (2026-08-16) Completed independent architecture/compliance review; after routing refresh through the typed maintenance port, no behavioral or contract defects remain.
- [x] (2026-08-16) Created the focused implementation/docs commit and verified a clean checkout with no FoliaSeal processes or temporary roots.

## Surprises & Discoveries

- Observation: `WorkspaceHandle` already contains the exact typed capabilities needed (`maintenance`, `session`, `view`, `viewer_workflow`, and `signing_workflow`).
  Evidence: `src/foliaseal/presentation/qt/app_frame_workspace_open.py`.
- Observation: deleting the public `current_*` properties in this slice would break a broad, intentional integration/test seam and exceed the bounded architecture objective.
  Evidence: repository consumers are concentrated in AppFrame and focused/integration tests; the properties are already typed and frame-owned.

## Decision Log

- Decision: migrate internal lifecycle code to `WorkspaceHandle`, but retain the typed `current_*` properties.
  Rationale: removes duplicate compatibility access from production behavior without silently breaking documented test/integration callers; a public API retirement can be planned separately if desired.
  Date/Author: 2026-08-16 / Codex.
- Decision: use a single callback helper over `WorkspaceHandle` rather than adding another wrapper object.
  Rationale: the workspace-open boundary is already the canonical capability record; another facade would deepen rather than simplify the module graph.
  Date/Author: 2026-08-16 / Codex.

## Outcomes & Retrospective

The source-change acknowledgement path now obtains one active `WorkspaceHandle`
and reads its signing workflow and view mount target directly. The public typed
properties remain stable for existing test/integration callers, while the
production lifecycle path no longer performs separate compatibility lookups.
The focused regression set passes (`189 passed`), Ruff and diff hygiene are
clean, and independent review is recorded below.

## Context and Orientation

`src/foliaseal/presentation/qt/app_frame.py` owns the top-level window and
workspace lifecycle. `SigningWorkspaceHost.active()` returns a
`WorkspaceHandle | None`; its fields are the canonical typed workspace
capabilities. The `_ignore_source_change` method acknowledges the current
source through the signing workflow and refreshes the mounted shell/view.

`docs/ARCHITECTURE.md` §12 identifies remaining AppFrame/shell seams as
architectural debt. This change deepens that seam without changing signing or
viewer behavior. The release plan's display-backed accessibility, package
installation, and human acceptance gates remain external/HITL work.

## Plan of Work

1. Add `_with_current_workspace(action)` beside the existing typed capability
   helpers. It returns `None` when no workspace is mounted and otherwise invokes
   the callback with the active `WorkspaceHandle`.
2. Rewrite `_ignore_source_change` to use this helper and the handle's
   `signing_workflow` and typed maintenance capability. Preserve status events,
   acknowledgement semantics, and safe no-workspace behavior.
3. Add/adjust focused AppFrame tests proving the helper's empty/active behavior
   and the source-change acknowledgement refresh path. The refresh crosses the
   maintenance port rather than inspecting the opaque view mount target. Do not rewrite the
   established public `current_*` test seam in this slice.
4. Update `docs/ARCHITECTURE.md` and the active release/parent plan only as
   needed to describe the completed internal capability migration; do not mark
   external gates complete.
5. Run focused tests, lint, diff hygiene, and an independent architecture review;
   then commit the bounded source/tests/docs change and clean up all owned
   processes and temporary roots.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    rg -n "current_shell|current_viewer_workflow|current_signing_workflow" src tests
    .venv/bin/python -m pytest tests/unit/test_qt_app_frame.py -k 'source_change or ignore_source'
    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/app_frame.py tests/unit/test_qt_app_frame.py
    git diff --check

The final review must also verify that no Wayland command or display-backed
probe was introduced and that no FoliaSeal process/window remains.

## Validation and Acceptance

- The focused AppFrame/workspace/shell regression set passes (`189 passed`); the full suite passes (`1585 passed, 20 skipped, 1 warning`).
- `rg` shows no production use of `self.current_signing_workflow` or
  `self.current_shell` in lifecycle/source-recovery code; only typed property
  definitions and intentional test/integration reads remain.
- Full relevant AppFrame tests pass, Ruff and `git diff --check` are clean.
- `docs/ARCHITECTURE.md` accurately describes the remaining public typed seam.
- Working tree is clean after the focused commit; owned process/temp-root checks
  report zero leftovers.

## Idempotence and Recovery

The helper is null-safe and side-effect free until its callback runs. If a test
fails, first compare the callback's selected handle field with the former
property path; do not restore duplicate property lookups. If documentation
reconciliation exposes a broader API-retirement opportunity, record it as a
new ExecPlan rather than expanding this slice.

## Artifacts and Notes

Primary artifacts are `app_frame.py`, `test_qt_app_frame.py`, this plan, and the
architecture/release-plan status notes. No generated evidence, package, GUI
capture, or Wayland artifact belongs in this slice.

## Interfaces and Dependencies

The retained public read seams are:

    current_workspace -> WorkspaceHandle | None
    current_shell -> Any | None
    current_viewer_workflow -> ViewerWorkflow | None
    current_signing_workflow -> SigningDraftWorkflow | None

The new internal seam is:

    _with_current_workspace(Callable[[WorkspaceHandle], Any | None]) -> Any | None

The maintenance port owns `refresh_source_safety()`; AppFrame does not inspect
the opaque `WorkspaceViewPort` mount target.

Review note: 2026-08-16 / Codex — independent review initially identified an
opaque-view reach-through and missing active-helper assertion; both were fixed
by routing refresh through the typed maintenance port and adding active-path
coverage. Retained `current_*` properties are intentional typed read seams;
remaining release gates are external.

Change note: 2026-08-16 / Codex — created from the architecture explorer's
dependency-ready recommendation; implementation and review entries are added
as the slice progresses.
