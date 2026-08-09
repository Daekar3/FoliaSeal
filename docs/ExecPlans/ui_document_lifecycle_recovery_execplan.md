# Document close, dirty-draft, and recovery lifecycle

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can safe document close/replacement and secret-free recovery handling in the real FoliaSeal GUI. It is mapped to UI_SPEC WF01, WF05, section 16, and acceptance scenarios 6 and 7. The
slice is intentionally one vertical path through the relevant persistent
model, application workflow, Qt surface, focused tests, and observable acceptance; it is not a
generic refactor.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are the frozen governing contracts.
- [ ] docs/ExecPlans/ui_launch_no_document_execplan.md, docs/ExecPlans/ui_single_instance_open_routing_execplan.md, and docs/ExecPlans/ui_signing_rail_stage_status_execplan.md

## Progress

- [ ] (2026-08-09) Audit the current implementation and write a failing focused test for the stated outcome.
- [ ] (2026-08-09) Implement the smallest complete model/application/Qt path.
- [ ] (2026-08-09) Remove migrated compatibility or phase3 product cruft whose retirement condition is met.
- [ ] (2026-08-09) Run focused, regression, and GUI validation; record evidence and clean up.
- [ ] (2026-08-09) Update this plan and relevant architecture/status documentation, then commit.

## Surprises & Discoveries

- Observation: replacement and close decisions cross app-frame open routing, draft workflow, and
  lifecycle state; password clearing and recovery must be tested at each terminal transition.
  Evidence: the live source paths and focused tests listed below are the audit baseline.

## Decision Log

- Decision: honor SPEC.md product scope, SCHEMAS.md persistent-object semantics, and UI_SPEC.md interaction wording in that order.
  Rationale: the repository explicitly defines those authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep this change limited to one observable document close, dirty-draft, and recovery lifecycle outcome.
  Rationale: narrow commits make GUI regressions and recovery auditable.
  Date/Author: 2026-08-09 / Codex

## Outcomes & Retrospective

Not started. At completion, state what a novice can now do, which tests and live evidence prove it, and any remaining gap.

## Context and Orientation

The relevant code is app_frame_workspace_open.py; signing_draft_workflow.py; signing_workspace lifecycle/close bridges; output/recovery policy tests. FoliaSeal is a Python/Qt Linux PDF signing application. The
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

Implement action-specific dirty prompts, File Close/Exit behavior, secret-free crash recovery detection, and safe handling of app-owned temporary/final artifacts. A failed transaction must preserve the draft and never delete unrelated files. Add typed seams where the current code passes raw widget internals or compatibility
kwargs. Preserve the public frame/workspace contract while migrating consumers, then delete the
old path once focused tests prove no callers remain. Keep user-facing terminology from UI_SPEC.md,
not schema/backend names.

## Milestones

Milestone 1 adds tests for protected-document prompts, dirty drafts, replacement, and password
clearing. Milestone 2 wires lifecycle transitions through the frame and draft workflow. Milestone 3
proves recovery and cleanup after close, replacement, success, and exit.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

    rg -n -e 'close|discard|recovery|password' src/foliaseal/presentation/qt/app_frame_workspace_open.py src/foliaseal/application/signing_draft_workflow.py src/foliaseal/presentation/qt/signing_workspace_lifecycle.py
    .venv/bin/pytest -q tests/unit/test_qt_app_frame_workspace_open.py tests/unit/test_signing_draft_workflow.py tests/unit/test_signing_workspace_lifecycle.py
    .venv/bin/ruff check src tests
    git diff --check

Run this bounded walkthrough from /home/daekar/FoliaSeal with an isolated configuration root:

    audit_root=$(mktemp -d /tmp/foliaseal-plan-audit-XXXXXX)
    timeout --foreground 30s env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf || test "$?" -eq 124
    ps -eo pid,cmd | rg 'FoliaSeal|foliaseal|PySide6|pytest' | rg -v 'rg ' || true
    find "$audit_root" -mindepth 1 -maxdepth 2 -type f -delete
    rmdir "$audit_root" 2>/dev/null || true

Expected evidence is the stated user-visible behavior plus a mandatory Qt-test or display-backed
walkthrough. Record the exact input sequence, widget state, expected observation, evidence path, and
cleanup result; the bounded timeout is only a lifecycle check.

## Validation and Acceptance

Acceptance is behavioral: Close/Open/Exit preserves data by default, discards only after explicit confirmation, and recovery offers only verified safe actions; ordinary drafts are not silently autosaved or restored. The focused regression suite must pass, the full
suite must remain green when shared code changed, and the GUI audit must record the visible result
and cleanup. A passing import or unit test without the stated user-visible behavior is insufficient.

## Required Acceptance Cases

Password-protected PDFs prompt before replacement. Session password memory is cleared on Close,
replacement, successful signing, and Exit. Certification and ordinary-signature restrictions are
preflighted, uncertain prohibited changes block signing, and recovery never deletes unrelated files
or presents an unverified artifact as safe.

## Evidence Record

Before completion, record agreement with `docs/ui/main-workspace-document-open-exploratory.svg`,
the exact lifecycle/recovery test command and result, each close/replace/
success/exit password-clearing observation, GUI input sequence, evidence path, cleanup, and
compatibility grep proof.

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
reach-through. Create tests/integration/test_document_lifecycle_recovery.py for isolated recovery
fixtures. The final interface must be exercised by tests/unit/test_qt_app_frame_workspace_open.py,
tests/unit/test_signing_draft_workflow.py, and that integration test.
workspace surface. Any compatibility adapter retained temporarily must have a named consumer and a
retirement condition recorded in this plan.

Revision note: 2026-08-09 / Codex
Created as child ui_document_lifecycle_recovery_execplan.md of the approved SPEC/UI_SPEC compliance breakdown.
