# Reconcile completed lifecycle and readiness children

This ExecPlan is a living document maintained in accordance with
`.agents/skills/write-execplan/PLANS.md`. It is an AFK documentation/status slice under
`docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md`.

## Purpose / Big Picture

FoliaSeal already protects dirty drafts, source changes, signing recovery artifacts, and readiness
states in the live application. Two child plans still show unchecked dependencies and describe those
behaviors as deferred or incomplete, which makes the governing corpus unreliable for the next agent.
This slice will reconcile the lifecycle and readiness plans, the parent dependency map, and the
architecture record with the current source and tests. A maintainer will be able to tell which
behavior is implemented and which remaining gates are genuinely display-backed or release-related.
No lifecycle or readiness behavior is added here.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md` and `docs/UI_SPEC.md` are the governing contracts.
- [x] `docs/ExecPlans/ui_document_lifecycle_recovery_execplan.md` contains the implemented dirty,
  source-change, and recovery lifecycle evidence.
- [x] `docs/ExecPlans/ui_readiness_caveats_status_execplan.md` contains the implemented ordered
  readiness and source-safety evidence.
- [x] Explorer audit of source, tests, parent status, and release gates completed on 2026-08-16.

## Progress

- [x] (2026-08-16) Confirmed lifecycle behavior covers dirty-draft decisions, candidate replacement,
  source Reload/Ignore/Locate/Close, pending-open safety, and verified transaction recovery.
- [x] (2026-08-16) Confirmed readiness behavior covers ordered source/setup/certificate/placement/
  review states, source-safety blocking, caveats, and `Saved but not verified` recovery projection.
- [x] Rewrite stale dependency, deferred-behavior, outcome, and acceptance wording in both children.
- [x] Reconcile parent markers and architecture records without closing display/HITL or release gates.
- [x] (2026-08-16) Run documentation/static validation, clean artifacts, and prepare the reconciliation for commit. Ruff, compileall, `git diff --check`, focused lifecycle/readiness coverage (`28 passed`), and process cleanup are green.
- [x] (2026-08-16) Commit the five-file reconciliation as `d27c23114`; the worktree is clean.

## Surprises & Discoveries

- Observation: lifecycle plan dependencies still show launch, single-instance, and rail children as
  unchecked even though the parent marks those children complete. Evidence: the current parent map
  and the lifecycle plan have contradictory checkboxes.
- Observation: lifecycle wording says crash recovery is unimplemented even though the journal and GUI
  recovery children now supply verified artifact recovery. Evidence: recovery source and plans under
  `signing_transaction_recovery_*`.
- Observation: readiness wording says document safety/full readiness remain elsewhere even though
  source monitoring, post-write status, preview-fit, and rail projections are implemented. Evidence:
  `signing_readiness.py`, `signing_action_coordinator.py`, and current focused/full test evidence.

## Decision Log

- Decision: reconcile the plans rather than create another behavior child. Rationale: the explorer
  found no missing AFK lifecycle or readiness behavior; adding code would duplicate existing seams.
  Date/Author: 2026-08-16 / Codex.
- Decision: retain explicit exclusions for unsaved-draft autosave/restoration, display-backed HITL,
  and privileged package installation where SPEC/UI_SPEC or the environment still excludes them.
  Rationale: status cleanup must not turn a deliberate non-goal or unavailable gate into a false
  completion claim. Date/Author: 2026-08-16 / Codex.

## Outcomes & Retrospective

The lifecycle and readiness child plans and the parent now distinguish implemented behavior from
independent final acceptance gates. No source, test, persisted format, or compatibility surface
changed. The remaining project blockers are limited to actual release/HITL evidence and other
parent-open plans with concrete gaps.

## Context and Orientation

`app_frame_workspace_open.py`, `signing_workspace_lifecycle.py`, and
`signing_draft_workflow.py` own dirty-draft and source-replacement policy. `DocumentSourceMonitor`
produces source identity decisions; `signing_readiness.py` orders blockers; and
`signing_action_coordinator.py` projects typed rail status including `saved_but_not_verified`.
The transaction journal/resolver plans own verified interrupted-signing artifact recovery. The parent
plan is the dependency authority; architecture records must describe these ownership boundaries as
implemented facts.

## Plan of Work

Update the lifecycle child so its dependencies match the parent, its outcomes describe source-change
and transaction recovery correctly, and its crash/autosave exclusion is explicitly limited to
unsaved-session restoration rather than verified artifact recovery. Update the readiness child to
describe the current source monitor, ordered projection, and post-write state, while leaving future
rail/release work assigned to its owning plans.

The two parent child entries are complete because their implementation evidence is current. The
architecture record adds only ownership corrections needed to remove contradictions. The parent’s
display-backed, accessibility, package, and final-release checkboxes remain open.

## Concrete Steps

From `/home/daekar/FoliaSeal`:

    rg -n "^[-*] \[ \]|remain|defer|open|not implemented|unimplemented|full suite" docs/ExecPlans/ui_document_lifecycle_recovery_execplan.md docs/ExecPlans/ui_readiness_caveats_status_execplan.md
    rg -n "DocumentSourceMonitor|saved_but_not_verified|POST_VERIFY_FAILED|Reload|Locate|Ignore|RecoveryAction" src tests
    .venv/bin/ruff check src tests
    .venv/bin/python -m compileall -q src tests
    git diff --check

The final status must have no source/test changes, no generated artifacts, and a clean process scan.

## Validation and Acceptance

Acceptance is truthful plan state: lifecycle and readiness children are marked complete only for the
implemented behavior they own, all dependency checkboxes reflect the parent, and explicit display/
privileged-release/HITL limits remain open. Static checks pass, and the existing latest full-suite
evidence remains cited without inventing a new test count for a documentation-only change.

## Idempotence and Recovery

The reconciliation is documentation-only and safe to repeat. Preserve historical progress entries
as dated audit records; update their wording only when a present-tense claim would contradict current
source. Remove no user files or ignored QA artifacts.

## Artifacts and Notes

Record the current source/test evidence, changed plan paths, architecture history note if needed, and
the commit hash (`d27c23114`). Do not commit PDFs, certificates, screenshots, caches, or package
roots.

## Interfaces and Dependencies

This slice changes no Python interfaces. Its correctness depends on the existing lifecycle,
readiness, source-monitor, transaction-recovery, and Qt action-coordinator contracts plus their
recorded focused/full validation. The next behavioral slice must be selected only after this stale
status reconciliation and a fresh parent audit.
