# Single-instance and open-request routing

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can route an OS open request or second invocation into one existing FoliaSeal
window without tabs or a second document window. If a request arrives while signing is active, the
same window keeps the current document, visibly names the newest queued PDF, and offers an explicit
Cancel pending open action. The request is considered only after signing succeeds or returns to a
recoverable draft. It is mapped to UI_SPEC LAY01, WF01, and the active-signing safety rule in §16.
The slice is intentionally one vertical path through the application workflow, Qt surface, focused
tests, and observable acceptance; it is not a generic refactor.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are the frozen governing contracts.
- [x] docs/ExecPlans/ui_launch_no_document_execplan.md

## Progress

- [x] (2026-08-09) Audit the current launcher and write failing protocol/launcher/Qt transport tests.
- [x] (2026-08-09) Implement the bounded single-owner and initial/second-invocation forwarding path.
- [x] (2026-08-10) Route forwarded requests through the existing frame and defer the newest request during active signing.
- [x] (2026-08-10) Add the condition-only queued-filename surface and keyboard-accessible Cancel pending open action.
- [ ] (2026-08-10) Remove migrated compatibility or acceptance product cruft whose retirement condition is met.
- [x] (2026-08-16) Run the real X11 two-process owner/secondary smoke with direct PID tracking; the
  primary stayed alive with one FoliaSeal window, the secondary exited `0`, and the focused
  integration test passed `1 passed` without the prior QLocalServer skip.
- [x] (2026-08-09) Run focused, regression, and bounded Qt validation; record evidence and clean up.
- [x] (2026-08-10) Run focused production-widget and regression validation, then reconcile architecture/status documentation; commit remains an explicit parent handoff step.

## Surprises & Discoveries

- Observation: app-frame open methods are in-process calls and do not by themselves implement a
  second-process handoff; this child must add and test an explicit platform/process boundary.
  Evidence: the live source paths and focused tests listed below are the audit baseline.
- Observation: active-signing deferral is an AppFrame policy boundary, not a workspace-port concern.
  `FoliaSealAppFrame` tracks signing terminal states, retains only the newest `OpenRequest`, and
  delegates replacement through the existing open/dirty lifecycle policy. Evidence:
  `handle_open_request()`, `_offer_pending_open_request()`, and `_handle_status_change()` in
  `src/foliaseal/presentation/qt/app_frame.py`.
- Observation: the current sandbox's QLocalServer cannot bind a Unix endpoint (`Unknown error 1`),
  so the production transport has an offscreen integration test that skips with an explicit
  environment diagnostic; pure protocol and injected-launch tests remain green.

- Observation: the queued request is transient application state, while its filename/Cancel affordance
  is a condition-only app-chrome surface. It is hidden with no pending request and cleared on cancel,
  terminal acceptance/cancellation, or workspace close. Evidence: `PendingOpenRequestSurface` and
  AppFrame cleanup/terminal-state paths, with unit and real offscreen Qt coverage.

## Decision Log

- Decision: honor SPEC.md product scope, SCHEMAS.md persistent-object semantics, and UI_SPEC.md interaction wording in that order.
  Rationale: the repository explicitly defines those authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep this change limited to one observable single-instance and open-request routing outcome.
  Rationale: narrow commits make GUI regressions and recovery auditable.
  Date/Author: 2026-08-09 / Codex
- Decision: Loop 4 delivers a typed bounded JSON protocol, per-user QLocalServer/QLocalSocket owner
  boundary, secondary send-and-exit behavior, Qt-event-loop delivery, and stale-endpoint cleanup;
  dirty-draft validation and policy are routed through the existing frame, and active-signing
  deferral is owned by the frame and its pending-request surface.
  Rationale: the frame already owns the signing transaction state and the one-window replacement
  decision, while the visible queue is an application-chrome concern rather than a document widget.
  Date/Author: 2026-08-09 / Codex
- Decision: Implement the pending-request affordance as a condition-only Qt status surface owned by
  the app frame, with the queued basename and a keyboard-accessible Cancel pending open button.
  Rationale: a status surface does not consume permanent viewer or right-rail space, remains visible
  while the transaction runs, and gives one stable owner for replacement, cancellation, and cleanup.
  Date/Author: 2026-08-10 / Codex
- Decision: Keep the request queue in memory and replace older requests with the newest request;
  never persist a path or show a second window.
  Rationale: UI_SPEC defines pending requests as transient safety state and explicitly requires newest
  request replacement.
  Date/Author: 2026-08-10 / Codex

## Outcomes & Retrospective

The bounded owner boundary and application-level deferral policy are implemented: a primary FoliaSeal
launch claims a per-user local endpoint, a second invocation sends an optional absolute PDF path and
exits without creating a second window, and the owner routes requests to the existing frame while
raising it. During active signing, the newest request replaces any older request in memory and is
shown by the AppFrame-owned condition-only status surface. Cancel leaves the current workspace
untouched; after a terminal signing/recovery state, the existing open/dirty policy decides whether to
replace it, and terminal/close paths clear the surface. Focused validation is `62 passed, 1 skipped`;
the full suite is `1447 passed, 20 skipped, 1 warning`; the real offscreen pending-open widget test
passes. QLocalServer cannot bind a Unix endpoint in the isolated/offscreen test environment
(`Unknown error 1`), so that test remains explicitly skipped; a dedicated Cinnamon/X11 smoke now
proves the real two-process route. Compatibility/acceptance retirement and the broader
display-backed/accessibility/release gates remain open.

## Context and Orientation

The relevant code is app_frame.py; app_frame_workspace_open.py; application document-open services; launcher integration tests. FoliaSeal is a Python/Qt Linux PDF signing application. The
product flow is open, review, select reusable setup, place one visible signature, preview
readiness, sign/save, verify, and reopen. This slice must preserve the V1 anti-goals: no tabs,
printing, general PDF editing, cloud workflow, broad trust administration, or multiple pending
signatures.

The words “compatibility surface” mean an adapter kept only for old callers. “acceptance” names identify
legacy evidence/harness infrastructure and must not appear in ordinary product-facing UI or new
primary contracts; production backend/evidence imports may be renamed only after a neutral migration
proves the old name is no longer required.

## Change Slice

Primary change class: behavior change. Allowed changes are the named implementation modules,
focused tests, bounded local evidence, and the minimum docs/status corrections needed to keep the
repository truthful. Do not mix unrelated architecture scans, V2 features, broad evidence
rebaselines, or packaging changes unless this slice explicitly requires them.

## Plan of Work

Implement one-process/one-main-window routing for an OS open request or a second invocation. The owner/
transport foundation and initial/forwarded delivery are already landed. This slice completes the
visible active-signing queue behavior. Keep
`tests/integration/test_single_instance_open_routing.py` as the process-level contract test; it owns
the primary-owner startup race, second-invocation forwarding, and deferred-request assertions.
The frame must validate candidates through the existing open service before replacement, defer an
external request during active signing, and expose the pending filename and Cancel pending open in
the app chrome. Use a localhost-free `QLocalServer`/`QLocalSocket` endpoint derived from the
user config directory, with a lock/primary-owner handshake, bounded startup retry, and a clear
fallback error when the primary process is alive but not listening. Add typed seams where the current code passes raw widget internals or compatibility
kwargs. Preserve the public frame/workspace contract while migrating consumers, then delete the
old path once focused tests prove no callers remain. Keep user-facing terminology from UI_SPEC.md,
not schema/backend names.

## Milestones

Milestone 1 established the `QLocalServer`/`QLocalSocket` owner handshake and protocol tests.
Milestone 2 wired validation, startup retry, pending-request replacement, and active-signing
deferral into the existing frame. Milestone 3 added the condition-only status surface, proved its
production Qt visibility and keyboard-accessible Cancel action offscreen, and preserved the explicit
QLocalServer limitation and cleanup requirement for a future display/environment audit.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e 'open_pdf_path|WorkspaceOpenService' src/foliaseal/presentation/qt/app_frame.py src/foliaseal/presentation/qt/app_frame_workspace_open.py
    .venv/bin/pytest -q tests/unit/test_qt_app_frame_workspace_open.py
    .venv/bin/pytest -q tests/integration/test_single_instance_open_routing.py
    .venv/bin/pytest -q tests/integration/test_gui_launch_no_document.py -k pending_open
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

Evidence is the focused protocol/launcher/widget result, the real offscreen pending-open observation,
and two-process routing logs where the endpoint is available. The current run records `62 passed, 1
skipped` for the focused app-frame/open-routing set, `1447 passed, 20 skipped, 1 warning` for the
full suite, and a passing real offscreen test for queued filename visibility and Cancel activation.
QLocalServer remains unavailable in the isolated/offscreen test environment (`Unknown error 1`), so
that test skip is retained. A dedicated unsandboxed Cinnamon/X11 run proved the real two-process
acceptance instead: the primary PID stayed alive, the secondary returned `0`, one primary window
remained, and the owned endpoint/window/root cleanup was empty afterward.

## Validation and Acceptance

Acceptance is behavioral for the owner boundary and the active-signing queue: a second invocation
does not create a second frame, sends a bounded absolute-path request to the primary, and the primary
delivers it on the Qt event loop while raising the existing window. During signing, the current
workspace remains mounted; the status surface visibly names the newest queued basename, exposes an
accessible Cancel pending open button, and removes the surface after cancel, acceptance, or workspace
close. Focused protocol/launcher/widget tests, the full suite, and any available Qt transport
evidence must remain green with clean process/socket teardown.

## Required Acceptance Cases

Before replacement, the candidate must be a content-validated single PDF whose password, page count,
restrictions, and first-page render succeed. Dropping zero or multiple files is rejected. During an
active signing transaction, a newer pending request replaces the older one with a visible filename,
replacement notice, and explicit Cancel pending open action; cancel leaves the current workspace
untouched, and accepting after a terminal state applies the existing open/dirty policy. No second
window or tab is created.

## Evidence Record

Before completion, record the exact protocol/launcher test and available Qt transport result,
primary/secondary input sequence, evidence path, cleanup of owned processes/socket roots, and
compatibility grep proof. The isolated/offscreen `QLocalServer` bind limitation must remain
recorded rather than silently treated as a passing transport test; the bounded unsandboxed
Cinnamon/X11 smoke is the separate source-tree two-process acceptance evidence.

Record the contributing UI_SPEC scenario ID(s) and either the owning SVG path or an explicit
"no SVG" decision alongside the evidence row.
Also record the exact focused command and result (`62 passed, 1 skipped`); the new condition-only
surface is green in fake-Qt unit coverage and
`test_real_qt_pending_open_surface_is_visible_and_cancelable`. The full regression result is
`1447 passed, 20 skipped, 1 warning`.

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

Use existing typed application workflows and a small app-frame-owned Qt surface rather than private
child-widget reach-through. The implemented
`src/foliaseal/presentation/qt/pending_open_request_surface.py` with a
`PendingOpenRequestSurface` that owns a `QStatusBar`-compatible container, a filename label, and a
Cancel pending open button. Extend `QtAppFrameBindings` with the status-bar class and expose only the
surface's `show_request`, `clear`, and visibility/widget inspection needed by tests. The final
interface is exercised by `tests/unit/test_qt_app_frame.py`,
`tests/unit/test_qt_app_frame_workspace_open.py`,
`tests/integration/test_single_instance_open_routing.py`, and one real offscreen Qt test. Any
compatibility adapter retained temporarily must have a named consumer and a
retirement condition recorded in this plan.

Revision note: 2026-08-09 / Codex
Created as child ui_single_instance_open_routing_execplan.md of the approved SPEC/UI_SPEC compliance breakdown.

Revision note: 2026-08-10 / Codex
The open-routing policy landed in commit `47c875112`, but the fresh compliance audit found that UI_SPEC
§16 also requires a persistent queued filename and explicit Cancel pending open surface. This revision
narrows the remaining child work to that condition-only app-frame status surface, its production
offscreen coverage, documentation reconciliation, and evidence; it does not reopen the completed IPC
transport.

Revision note: 2026-08-10 / Codex (historical status before the X11 smoke)
The condition-only AppFrame status surface, replacement/cancel/terminal cleanup behavior, focused
production-widget coverage, and architecture reconciliation are complete. Focused validation is
`62 passed, 1 skipped`; full regression is `1447 passed, 20 skipped, 1 warning`. QLocalServer bind
failure (`Unknown error 1`) remains an environment limitation; compatibility retirement and
display-backed two-process smoke acceptance remained open at that point.

Revision note: 2026-08-16 / Codex
Recorded successful unsandboxed Cinnamon/X11 two-process routing (`secondary_rc=0`, primary window
retained, no second owner) and the focused integration result (`1 passed`). The offscreen QLocalServer
skip remains an isolated-test limitation; compatibility retirement and broader release acceptance
remain open. Wayland is intentionally deferred until Mint supports it as a first-class session.
