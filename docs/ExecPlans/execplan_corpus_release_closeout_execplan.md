# Reconcile the remaining active release and ExecPlan closeout markers

This ExecPlan is a living document and must be maintained in accordance with
`.agents/skills/write-execplan/PLANS.md`. It is a documentation/status slice
under `docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md` and
`docs/ExecPlans/ui_product_support_and_release_execplan.md`.

## Purpose / Big Picture

A contributor reading the active UI plans should be able to distinguish completed
implementation from a stale publication checkbox and from a genuine external
acceptance gate. This slice does not add product behavior. It verifies the
current implementation and evidence, closes only stale markers in the active
plans, records the current commits and validation, and keeps human
screen-reader/contrast/DPI/monitor review, privileged host installation, final
release acceptance, and Wayland explicitly open or deferred.

The observable result is a truthful, restartable release ledger: the parent and
release plans point to current evidence, completed signing/progress children no
longer appear unfinished merely because their commit checkbox was not updated,
and no status edit claims more than the available X11/offscreen/package evidence.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md`, `docs/UI_SPEC.md`, and `docs/SCHEMAS.md` are the
  governing contracts.
- [x] `docs/ExecPlans/release_readiness_reconciliation_execplan.md` already
  verified that no dependency-ready behavior gap exists in the relevant
  implementation paths.
- [x] Source-tree X11, packaged-X11, and visual-layout evidence are committed
  and their owned resources were cleaned.

## Progress

- [x] (2026-08-16) Explorer audit reviewed the current parent, release, signing,
  evidence, safe-links, and review plans and found no stronger AFK feature slice;
  remaining work is stale publication or external release evidence.
- [x] (2026-08-16) Verified the targeted plans' source paths, commits, and
  focused tests from the current checkout before changing a checkbox.
- [x] (2026-08-16) Reconciled stale progress/outcome/dependency markers in the
  targeted plans and parent/release architecture ledger.
- [x] (2026-08-16) Ran focused validation (`26 passed` for the corrected
  transaction command, `124` and `89` in the review/signing groups), the full
  suite (`1543 passed, 20 skipped, 1 warning`), Ruff, compileall, and diff
  checks. Independent documentation/architecture review returned GO; explorer
  review findings were corrected and the follow-up review returned GO.
- [x] (2026-08-16) Committed the documentation/status closeout as
  `ec2170db6` and verified the post-commit worktree is clean.

## Surprises & Discoveries

- Observation: `ui_signing_transaction_progress_execplan.md` has complete
  implementation and validation entries but retains an unchecked commit line;
  Git history contains `8208f6666` for the implementation.
- Observation: `ui_atomic_sign_write_safety_execplan.md` still lists the
  confirmation/output-policy child as incomplete even though that child records
  implementation and commit `def5ce0f5`, and later recovery/progress children
  cover the remaining behavior.
- Observation: the active release plan already records packaged-X11 and
  source-tree X11 evidence; its remaining gates are human/privileged/final
  release gates, not missing local implementation.
- Observation: older `phase3` and acceptance-named plans contain historical
  checklists that are not active dependencies of the UI parent. They must not
  be mass-checked; only current active-plan markers with current evidence are
  reconciled in this slice.

## Decision Log

- Decision: limit edits to status/plan/architecture documentation and do not
  change runtime code.
  Rationale: the fresh implementation audit found no unimplemented AFK product
  seam; inventing behavior would duplicate completed children and risk
  regressions.
  Date/Author: 2026-08-16 / Codex.
- Decision: close a marker only when a current source/test/Git artifact proves
  it; preserve external acceptance markers.
  Rationale: a green narrow test cannot prove human accessibility, privileged
  installation, or final release acceptance.
  Date/Author: 2026-08-16 / Codex.
- Decision: leave historical phase/nomenclature plans unchanged except where an
  active parent explicitly depends on them.
  Rationale: historical records are evidence of prior work, not current
  implementation blockers, and broad renaming would create unrelated churn.
  Date/Author: 2026-08-16 / Codex.

## Outcomes & Retrospective

The targeted status audit found that signing progress (`8208f6666`), atomic
signing's confirmation dependency (`def5ce0f5`), Document Signatures
(`9a064669b`), and per-signature guidance (`8cddd7546`, `4cb84e52a`,
`5d05e71b5`) were implemented but had stale publication markers. Those markers
are now reconciled in their plans and in the parent/release/architecture
ledger. The remaining release items are human screen-reader/contrast/DPI/
monitor review, privileged host installation, final release acceptance, and
Wayland deferral. Validation, independent review, commit `ec2170db6`, and
cleanup are complete; the post-commit worktree is clean.

## Context and Orientation

The active compliance parent is
`docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md`; its release child is
`docs/ExecPlans/ui_product_support_and_release_execplan.md`. The signing
transaction implementation is owned by
`src/foliaseal/presentation/qt/signing_action_coordinator.py`,
`src/foliaseal/presentation/qt/signing_action_boundary.py`, and the signing
workspace composition. Confirmation/output policy is owned by the corresponding
application and Qt action bridge modules. The status records must refer to
actual current source paths and commits, not old plan-only intentions.

This slice targets, at minimum, the signing progress and atomic-sign plans,
their completed confirmation/output-policy dependency, the parent/release
ledger, and `docs/ARCHITECTURE.md`. Additional plan edits are allowed only
when a fresh consumer/evidence check proves the marker stale. Generated
packages, screenshots, PDFs, credentials, and machine-local paths are never
committed.

## Plan of Work

First inspect the targeted plans, source ownership, Git history, and focused
tests. For signing progress, prove the asynchronous runner/completion path and
run its coordinator, boundary, and Qt timing tests; record commit
`8208f6666`. For atomic signing, prove the default executor and verified
staging paths, then mark the already-completed confirmation/output-policy
dependency as complete while retaining any genuinely external release gate.

Reconcile each plan's Progress and Outcomes sections so they state what is
implemented, what evidence is current, and what remains. Update the parent,
release child, and architecture history only where their current status is
inaccurate. Do not turn HITL or privileged work into AFK checkboxes, and do not
claim Wayland support.

Run the focused tests, the full suite, Ruff, compile checks, and diff checks.
Obtain one explorer compliance review and one documentation/architecture review.
Commit only the bounded plan/status changes and verify the checkout, processes,
windows, and temporary roots are clean.

## Milestones

### Milestone 1: evidence audit

The targeted plan markers are mapped to current source, tests, and commits.
A marker without proof stays open and is documented as such.

### Milestone 2: status reconciliation

The active plans and architecture ledger consistently describe completed
implementation and remaining external gates. Historical plan records remain
historical.

### Milestone 3: validation and closeout

Focused/full checks and independent reviews pass, the documentation-only commit
is created, and no owned process or disposable artifact remains.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    git status --short --branch
    git log --all --oneline -- src/foliaseal/presentation/qt/signing_action_coordinator.py
    .venv/bin/python -m pytest -q tests/unit/test_qt_signing_action_coordinator.py tests/unit/test_qt_signing_action_boundary.py tests/integration/test_signing_transaction_progress.py
    .venv/bin/python -m pytest -q
    .venv/bin/python -m ruff check src tests scripts
    .venv/bin/python -m compileall -q src tests scripts
    git diff --check

Expected focused tests are green; the full suite should report the current
checkout's complete count. If a test or source audit contradicts a status
claim, leave that marker open and record the contradiction instead of forcing
closure.

## Validation and Acceptance

Acceptance is documentation behavior: a fresh reader can trace each closed
marker to a current source path, focused test, and/or Git commit; the parent and
release plans still show human accessibility, physical-DPI/monitor,
privileged-host, final-release, and Wayland gates as open/deferred; and no
active plan claims a stale limitation as a current implementation blocker.

The full test suite, Ruff, compileall, and diff checks must pass. The final
checkout must be clean and no FoliaSeal/PySide6/pytest audit process, owned
window, or temporary root may remain.

## Idempotence and Recovery

This slice is documentation-only and safe to repeat. Preserve unrelated dirty
changes. If a marker cannot be proven stale, do not edit it. Remove only exact
temporary roots created by validation; never remove user configuration or
unrelated desktop windows.

## Artifacts and Notes

Record current test counts, reconciled file names, review decisions, commit
hash, and cleanup proof here. Do not commit generated runtime evidence.

## Interfaces and Dependencies

This slice changes no runtime interface. It relies on the existing typed signing
action/coordinator boundaries, Qt workspace composition, current pytest/Ruff
tooling, Git history, and the precedence of SPEC.md → SCHEMAS.md → UI_SPEC.md.

Revision note: 2026-08-16 / Codex: created after a fresh corpus audit found
the remaining active unchecked markers were status inconsistencies or external
acceptance gates rather than a new AFK implementation dependency.
