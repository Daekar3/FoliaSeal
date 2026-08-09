# Single-instance and open-request routing

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can route an OS open request or second invocation into one existing FoliaSeal
window without tabs or a second document window. It is mapped to UI_SPEC LAY01 and WF01. The slice
is intentionally one vertical path through the relevant persistent
model, application workflow, Qt surface, focused tests, and observable acceptance; it is not a
generic refactor.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are the frozen governing contracts.
- [ ] docs/ExecPlans/ui_launch_no_document_execplan.md

## Progress

- [ ] (2026-08-09) Audit the current implementation and write a failing focused test for the stated outcome.
- [ ] (2026-08-09) Implement the smallest complete model/application/Qt path.
- [ ] (2026-08-09) Remove migrated compatibility or phase3 product cruft whose retirement condition is met.
- [ ] (2026-08-09) Run focused, regression, and GUI validation; record evidence and clean up.
- [ ] (2026-08-09) Update this plan and relevant architecture/status documentation, then commit.

## Surprises & Discoveries

- Observation: app-frame open methods are in-process calls and do not by themselves implement a
  second-process handoff; this child must add and test an explicit platform/process boundary.
  Evidence: the live source paths and focused tests listed below are the audit baseline.

## Decision Log

- Decision: honor SPEC.md product scope, SCHEMAS.md persistent-object semantics, and UI_SPEC.md interaction wording in that order.
  Rationale: the repository explicitly defines those authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep this change limited to one observable single-instance and open-request routing outcome.
  Rationale: narrow commits make GUI regressions and recovery auditable.
  Date/Author: 2026-08-09 / Codex

## Outcomes & Retrospective

Not started. At completion, state what a novice can now do, which tests and live evidence prove it, and any remaining gap.

## Context and Orientation

The relevant code is app_frame.py; app_frame_workspace_open.py; application document-open services; launcher integration tests. FoliaSeal is a Python/Qt Linux PDF signing application. The
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

Implement one-process/one-main-window routing for an OS open request or a second invocation. Create
`tests/integration/test_single_instance_open_routing.py` as the process-level contract test; it owns
the primary-owner startup race, second-invocation forwarding, and deferred-request assertions.
Introduce a small platform/process boundary for forwarding the path to the existing frame; do not
pretend the current app-frame methods provide IPC. Validate the candidate PDF before replacing the
current document, defer an external request during active signing, and expose the pending filename
and cancel action. Use a localhost-free `QLocalServer`/`QLocalSocket` endpoint derived from the
user config directory, with a lock/primary-owner handshake, bounded startup retry, and a clear
fallback error when the primary process is alive but not listening. Add typed seams where the current code passes raw widget internals or compatibility
kwargs. Preserve the public frame/workspace contract while migrating consumers, then delete the
old path once focused tests prove no callers remain. Keep user-facing terminology from UI_SPEC.md,
not schema/backend names.

## Milestones

Milestone 1 prototypes the `QLocalServer`/`QLocalSocket` owner handshake and adds the two-process
integration test. Milestone 2 wires validation, startup retry, pending-request replacement, and
dirty-draft deferral into the existing frame. Milestone 3 runs the real two-process smoke command,
records routing logs, and terminates both processes.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

    rg -n -e 'open_pdf_path|WorkspaceOpenService' src/foliaseal/presentation/qt/app_frame.py src/foliaseal/presentation/qt/app_frame_workspace_open.py
    .venv/bin/pytest -q tests/unit/test_qt_app_frame_workspace_open.py
    .venv/bin/pytest -q tests/integration/test_single_instance_open_routing.py
    .venv/bin/ruff check src tests
    git diff --check

Run this bounded walkthrough from /home/daekar/FoliaSeal with an isolated configuration root:

    audit_root=$(mktemp -d /tmp/foliaseal-plan-audit-XXXXXX)
    primary_log="$audit_root/primary.log"
    secondary_log="$audit_root/secondary.log"
    QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui >"$primary_log" 2>&1 & primary_pid=$!
    timeout --foreground 10s env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf >"$secondary_log" 2>&1
    kill -TERM "$primary_pid" 2>/dev/null || true; wait "$primary_pid" 2>/dev/null || true
    rg -n 'forwarded|already running|open request' "$primary_log" "$secondary_log"
    ! ps -eo pid,cmd | rg 'FoliaSeal|foliaseal|PySide6|pytest' | rg -v 'rg '
    rm -rf "$audit_root"

Expected evidence is the two-process routing logs and a mandatory Qt/integration observation of
forwarding, pending replacement, and no second window. Record both owned process cleanup results;
the bounded timeout is only a lifecycle check.

## Validation and Acceptance

Acceptance is behavioral: A second open request does not create tabs or a second document window; a valid request reaches the existing frame only after validation and dirty-draft policy; an active signing transaction defers it safely. The focused regression suite must pass, the full
suite must remain green when shared code changed, and the GUI audit must record the visible result
and cleanup. A passing import or unit test without the stated user-visible behavior is insufficient.

## Required Acceptance Cases

Before replacement, the candidate must be a content-validated single PDF whose password, page count,
restrictions, and first-page render succeed. Dropping zero or multiple files is rejected. During an
active signing transaction, a newer pending request replaces the older one with a notice and an
explicit cancel action; no second window or tab is created.

## Evidence Record

Before completion, record the exact two-process test and smoke command results, primary/secondary
input sequence and forwarding logs, evidence path, cleanup of both owned processes and temp roots,
and compatibility grep proof.

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
reach-through. The final interface must be exercised by tests/unit/test_qt_app_frame_workspace_open.py
and tests/integration/test_single_instance_open_routing.py.
workspace surface. Any compatibility adapter retained temporarily must have a named consumer and a
retirement condition recorded in this plan.

Revision note: 2026-08-09 / Codex
Created as child ui_single_instance_open_routing_execplan.md of the approved SPEC/UI_SPEC compliance breakdown.
