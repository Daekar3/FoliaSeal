# Fixed signing rail, status regions, and stage model

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can use a fixed right rail that shows truthful readiness/result stages and one next action in the real FoliaSeal GUI. It is mapped to UI_SPEC SUR02, SUR07, section 11, and acceptance scenarios 2 and 5. The
slice is intentionally one vertical path through the relevant persistent
model, application workflow, Qt surface, focused tests, and observable acceptance; it is not a
generic refactor.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are the frozen governing contracts.
- [ ] docs/ExecPlans/ui_launch_no_document_execplan.md
- [ ] docs/ExecPlans/ui_command_model_shortcuts_execplan.md

## Progress

- [ ] (2026-08-09) Audit the current implementation and write a failing focused test for the stated outcome.
- [ ] (2026-08-09) Implement the smallest complete model/application/Qt path.
- [ ] (2026-08-09) Remove migrated compatibility or phase3 product cruft whose retirement condition is met.
- [ ] (2026-08-09) Run focused, regression, and GUI validation; record evidence and clean up.
- [ ] (2026-08-09) Update this plan and relevant architecture/status documentation, then commit.

## Surprises & Discoveries

- Observation: the signing rail is coordinated through sidebar and action-coordinator seams; the
  child must keep readiness state plain-language and derive action enablement from one state model.
  Evidence: the live source paths and focused tests listed below are the audit baseline.

## Decision Log

- Decision: honor SPEC.md product scope, SCHEMAS.md persistent-object semantics, and UI_SPEC.md interaction wording in that order.
  Rationale: the repository explicitly defines those authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep this change limited to one observable fixed signing rail, status regions, and stage model outcome.
  Rationale: narrow commits make GUI regressions and recovery auditable.
  Date/Author: 2026-08-09 / Codex

## Outcomes & Retrospective

Not started. At completion, state what a novice can now do, which tests and live evidence prove it, and any remaining gap.

## Context and Orientation

The relevant code is signing_workspace_sidebar.py; signing_action_coordinator.py; signing_workspace_composition.py; signing shell tests. FoliaSeal is a Python/Qt Linux PDF signing application. The
product flow is open, review, select reusable setup, place one visible signature, preview
readiness, sign/save, verify, and reopen. This slice must preserve the V1 anti-goals: no tabs,
printing, general PDF editing, cloud workflow, broad trust administration, or multiple pending
signatures.

The words “compatibility surface” mean an adapter kept only for old callers. “phase3” names identify
legacy evidence/harness infrastructure and must not appear in ordinary product-facing UI or new
primary contracts; production backend/evidence imports may be renamed only after a neutral migration
proves the old name is no longer required.

## Change Slice

Primary change class: behavior change. Allowed changes are the named implementation modules,
focused tests, bounded local evidence, and the minimum docs/status corrections needed to keep the
repository truthful. Do not mix unrelated architecture scans, V2 features, broad evidence
rebaselines, or packaging changes unless this slice explicitly requires them.

## Plan of Work

Reshape the mounted workspace into a stable right signing rail with upper controls, a protected lower readiness/result region, and one plain-language next action. Keep the canvas primary, prevent status from moving into the toolbar, and map all specified states without a wizard. Add typed seams where the current code passes raw widget internals or compatibility
kwargs. Preserve the public frame/workspace contract while migrating consumers, then delete the
old path once focused tests prove no callers remain. Keep user-facing terminology from UI_SPEC.md,
not schema/backend names.

## Milestones

Milestone 1 defines one readiness/action state and adds coordinator/sidebar tests. Milestone 2 wires
the fixed-width rail and plain-language stages through public ports. Milestone 3 proves tab order,
disabled actions, and status transitions in a recorded GUI audit.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

    rg -n -e 'class SigningWorkspaceSidebar|class SigningActionCoordinator' src/foliaseal/presentation/qt/signing_workspace_sidebar.py src/foliaseal/presentation/qt/signing_action_coordinator.py
    .venv/bin/pytest -q tests/unit/test_qt_signing_action_coordinator.py tests/unit/test_qt_signing_shell.py tests/unit/test_signing_workspace_sidebar.py
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

Acceptance is behavioral: At minimum, no-document, setup-required, placement, ready, signing, signed-verified, and failed states render in the rail with one clear next action and no needless reflow. The focused regression suite must pass, the full
suite must remain green when shared code changed, and the GUI audit must record the visible result
and cleanup. A passing import or unit test without the stated user-visible behavior is insufficient.

## Evidence Record

Before checking this child in the parent, record the governing UI_SPEC requirement and
`docs/ui/sign-and-save-states-exploratory.svg`, exact focused test command/result, rail keyboard sequence and observed status/action,
evidence path and cleanup result, and compatibility grep proof.

Record the contributing UI_SPEC scenario ID(s) and either the owning SVG path or an explicit
"no SVG" decision alongside the evidence row.

## Idempotence and Recovery

Use temporary sibling outputs and isolated configuration for repeatable tests. If implementation
fails halfway, keep the source PDF and unsigned draft intact, terminate owned processes, remove only
this slice's generated artifacts, and update Progress with completed and remaining work. Re-running
the tests must not mutate user data or resurrect retired compatibility code.

## Artifacts and Notes

Record concise command output, focused screenshots/JSON under ignored artifacts/ when useful, and
the exact files changed. Do not commit generated PDFs, private keys, passwords, or machine-local
absolute paths.

## Interfaces and Dependencies

Use existing typed application workflows and public Qt ports rather than private child-widget
reach-through. Create `tests/unit/test_qt_signing_rail_stage_status.py` for offscreen rail state;
the final interface must be exercised by tests/unit/test_qt_signing_action_coordinator.py,
tests/unit/test_qt_signing_shell.py, and that new test file.
workspace surface. Any compatibility adapter retained temporarily must have a named consumer and a
retirement condition recorded in this plan.

Revision note: 2026-08-09 / Codex
Created as child ui_signing_rail_stage_status_execplan.md of the approved SPEC/UI_SPEC compliance breakdown.
