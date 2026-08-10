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
- [x] docs/ExecPlans/ui_launch_no_document_execplan.md

## Progress

- [x] (2026-08-09) Audit the current launcher and write failing protocol/launcher/Qt transport tests.
- [x] (2026-08-09) Implement the bounded single-owner and initial/second-invocation forwarding path.
- [ ] (2026-08-09) Remove migrated compatibility or phase3 product cruft whose retirement condition is met.
- [x] (2026-08-09) Run focused, regression, and bounded Qt validation; record evidence and clean up.
- [ ] (2026-08-09) Update relevant architecture/status documentation, complete deferred-draft policy, then commit the whole child outcome.

## Surprises & Discoveries

- Observation: app-frame open methods are in-process calls and do not by themselves implement a
  second-process handoff; this child must add and test an explicit platform/process boundary.
  Evidence: the live source paths and focused tests listed below are the audit baseline.
- Observation: the current public workspace ports do not expose dirty-draft or active-signing
  deferral state, so this loop stops at safe owner/forwarding transport and leaves pending-request
  UI policy to the document lifecycle child.
  Evidence: `SigningWorkspacePort`, `SigningWorkspaceSessionPort`, and `SigningWorkspaceHost` expose
  open/close/session verbs but no dirty or transaction decision contract.
- Observation: the current sandbox's QLocalServer cannot bind a Unix endpoint (`Unknown error 1`),
  so the production transport has an offscreen integration test that skips with an explicit
  environment diagnostic; pure protocol and injected-launch tests remain green.

## Decision Log

- Decision: honor SPEC.md product scope, SCHEMAS.md persistent-object semantics, and UI_SPEC.md interaction wording in that order.
  Rationale: the repository explicitly defines those authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep this change limited to one observable single-instance and open-request routing outcome.
  Rationale: narrow commits make GUI regressions and recovery auditable.
  Date/Author: 2026-08-09 / Codex
- Decision: Loop 4 delivers a typed bounded JSON protocol, per-user QLocalServer/QLocalSocket owner
  boundary, secondary send-and-exit behavior, Qt-event-loop delivery, and stale-endpoint cleanup;
  dirty-draft deferral, full content validation, and pending-request UI remain a separate child.
  Rationale: those policies require public workspace state seams that do not yet exist.
  Date/Author: 2026-08-09 / Codex

## Outcomes & Retrospective

The bounded owner boundary is implemented: a primary FoliaSeal launch claims a per-user local
endpoint, a second invocation sends an optional absolute PDF path and exits without creating a second
window, and the owner routes queued requests to the existing frame while raising it. Protocol size,
shape, absolute-path, owner-lock, and cleanup seams are tested; focused launcher/Qt tests pass
(`39 passed`, with the environment-limited QLocalServer integration explicitly skipped). Dirty-draft
deferral, password/restriction/first-render validation, pending filename/cancel UI, and the real
two-process smoke evidence remain owned by later lifecycle work; stale-endpoint recovery is not
claimed as live transport evidence in this environment.

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

Implement one-process/one-main-window routing for an OS open request or a second invocation. Loop 4
implements the owner/transport foundation and initial/forwarded delivery. Create
`tests/integration/test_single_instance_open_routing.py` as the process-level contract test; it owns
the primary-owner startup race, second-invocation forwarding, and deferred-request assertions.
Introduce a small platform/process boundary for forwarding the path to the existing frame; do not
pretend the current app-frame methods provide IPC. Validate the candidate PDF before replacing the
current document, defer an external request during active signing, and expose the pending filename
and cancel action in the dependent lifecycle child. Use a localhost-free `QLocalServer`/`QLocalSocket` endpoint derived from the
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

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e 'open_pdf_path|WorkspaceOpenService' src/foliaseal/presentation/qt/app_frame.py src/foliaseal/presentation/qt/app_frame_workspace_open.py
    .venv/bin/pytest -q tests/unit/test_qt_app_frame_workspace_open.py
    .venv/bin/pytest -q tests/integration/test_single_instance_open_routing.py
    .venv/bin/ruff check src tests
    .venv/bin/pytest -q
    git diff --check

Run this bounded walkthrough from /home/daekar/FoliaSeal with an isolated configuration root:

    audit_root=$(mktemp -d /tmp/foliaseal-plan-audit-XXXXXX)
    primary_log="$audit_root/primary.log"
    secondary_log="$audit_root/secondary.log"
    QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui >"$primary_log" 2>&1 & primary_pid=$!
    set +e
    timeout --foreground 10s env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf >"$secondary_log" 2>&1
    secondary_rc=$?
    set -e
    test "$secondary_rc" -eq 0 || test "$secondary_rc" -eq 124
    kill -TERM "$primary_pid" 2>/dev/null || true; wait "$primary_pid" 2>/dev/null || true
    rg -n 'forwarded|already running|open request' "$primary_log" "$secondary_log"
    ! ps -eo pid,cmd | rg 'FoliaSeal|foliaseal|PySide6|pytest' | rg -v 'rg '
    rm -rf "$audit_root"

Expected evidence is the two-process routing logs and a mandatory Qt/integration observation of
forwarding, pending replacement, and no second window. Record both owned process cleanup results;
the bounded timeout is only a lifecycle check.

## Validation and Acceptance

Acceptance for Loop 4 is behavioral for the owner boundary: a second invocation does not create a
second frame, sends a bounded absolute-path request to the primary, and the primary delivers it on
the Qt event loop while raising the existing window. Dirty-draft/active-signing policy and complete
PDF content validation remain explicitly deferred. Focused protocol/launcher tests, the full suite,
and any available Qt transport evidence must remain green with clean process/socket teardown.

## Required Acceptance Cases

Before replacement, the candidate must be a content-validated single PDF whose password, page count,
restrictions, and first-page render succeed. Dropping zero or multiple files is rejected. During an
active signing transaction, a newer pending request replaces the older one with a notice and an
explicit cancel action; no second window or tab is created.

## Evidence Record

Before completion, record the exact protocol/launcher test and available Qt transport result,
primary/secondary input sequence, evidence path, cleanup of owned processes/socket roots, and
compatibility grep proof. The current QLocalServer bind limitation must remain recorded rather than
silently treated as a passing two-process audit.

Record the contributing UI_SPEC scenario ID(s) and either the owning SVG path or an explicit
"no SVG" decision alongside the evidence row.
Also record the exact focused test node and expected result (`N passed`); when the slice adds a new
contract, record that the test was red before implementation and green afterward.

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
