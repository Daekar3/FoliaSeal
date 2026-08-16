# Retire stale archived harness plan markers

This is a living ExecPlan maintained under `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

The implementation-facing acceptance/evidence terminology migration is complete,
and no `phase3` references remain in `src/`, `tests/`, or `scripts/`. A small
set of completed historical harness/materialization plans still contains
unchecked publication or follow-up markers, which makes a clean plan audit look
like unfinished implementation work. This documentation-only slice closes
those stale markers and labels the plans as archival provenance. It does not
rewrite historical commands, paths, DTO names, artifacts, or evidence.

## Scope

The bounded target set is the 12 plans identified by the pre-edit inventory:

- `phase3_harness_capture_assembler_execplan.md`
- `phase3_harness_current_request_boundary_execplan.md`
- `phase3_harness_qt_preview_capture_boundary_execplan.md`
- `phase3_harness_signature_rect_priming_execplan.md`
- `phase3_harness_signed_acceptance_workspace_execplan.md`
- `phase3_harness_testing_adapter_execplan.md`
- `phase3_harness_timestamp_boundary_execplan.md`
- `phase3_harness_workspace_capture_boundary_execplan.md`
- `phase3_harness_workspace_refresh_boundary_execplan.md`
- `phase3_harness_workspace_scenario_boundary_execplan.md`
- `phase3_preview_render_capture_boundary_execplan.md`
- `phase3_signing_artifact_materialization_boundary_execplan.md`

Historical file names remain unchanged so links and provenance do not break.

## Progress

- [x] (2026-08-16) Fresh explorer audit confirmed no dependency-ready AFK product implementation; remaining open requirements are external/HITL or deferred Wayland.
- [x] (2026-08-16) Inventory found 12 stale unchecked markers in completed historical plans; no source/test/script `phase3` references remain.
- [x] (2026-08-16) Converted stale “create commit”, “no child planned”, and final-review markers to explicit completed/archival records using the evidence already recorded in each plan.
- [x] (2026-08-16) Added archival banners and current-owner guidance where a historical plan could otherwise be mistaken for an active implementation queue.
- [x] (2026-08-16) Independent documentation review passed; no source, test, CLI, schema, or governing-contract changes were introduced.
- [x] (2026-08-16) Ran plan-corpus checks and diff hygiene, committed the slice, and verified a clean checkout with no FoliaSeal processes or temporary roots.

## Decision Log

- Decision: preserve historical plan files and examples rather than mass-rewrite them.
  Rationale: completed evidence and old paths are provenance; changing them would
  reduce auditability and risk corrupting historical claims.
- Decision: close only markers whose own plan already records implementation,
  validation, architecture review, and outcome evidence.
  Rationale: stale-marker cleanup must not conceal genuinely incomplete work.

## Outcomes & Retrospective

The targeted historical plans no longer contain unchecked implementation markers.
Current release blockers remain visible in the active UI/product release plans:
display-backed human accessibility and GUI acceptance, privileged host package
installation, final release signoff, and deferred Mint 22.3 Wayland support.

## Validation

Run from `/home/daekar/FoliaSeal`:

    rg -n '^\\- \\[ \\]' docs/ExecPlans/phase3_harness_* docs/ExecPlans/phase3_preview_render_capture_boundary_execplan.md docs/ExecPlans/phase3_signing_artifact_materialization_boundary_execplan.md
    rg -ni 'phase3|phase 3|Phase3' src tests scripts
    git diff --check

The first command must return no output for the bounded target set. The second
command must return no output. No GUI, Wayland, package installation, or
generated artifact is part of this documentation slice.

## Idempotence and Recovery

If a targeted plan later gains real implementation work, restore a specific
unchecked task with a dated rationale rather than reopening generic markers.
If a marker cannot be proven stale from its own evidence, leave it open and
create a separate implementation plan; do not close it mechanically.

Revision note: 2026-08-16 / Codex — created after the fresh architecture audit
found no AFK product slice and identified stale completed-plan markers as the
remaining agent-facing corpus defect.
