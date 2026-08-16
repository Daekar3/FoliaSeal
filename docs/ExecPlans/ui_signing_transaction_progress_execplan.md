# Add truthful non-blocking signing transaction progress

This ExecPlan is a living document maintained under `.agents/skills/write-execplan/PLANS.md`.
It is an AFK child of `docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md` and consumes the
existing signing confirmation, readiness, output-policy, and verification-recovery seams.

## Purpose / Big Picture

After this slice, confirming Sign and save will keep the FoliaSeal window responsive while the
short, non-cancellable signing operation runs. The signing rail will show a truthful transaction
stage after roughly one second, switch to calm longer-than-expected wording after roughly ten
seconds, and retain useful technical stage text for materially longer work. Fast operations will
finish without a distracting progress flash. The UI will never invent a percentage, expose a
destructive timeout, or offer cancellation after confirmation.

The current executor exposes one synchronous `execute(request)` call. This slice therefore owns a
coarse transaction lifecycle around that call—preparing, writing, verifying, and terminal success
or failure—without claiming backend progress that the executor cannot report.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md` and `docs/UI_SPEC.md` are the governing product contracts.
- [x] `docs/ExecPlans/ui_sign_confirmation_output_policy_execplan.md` supplies the confirmed
  request, output-path, and summary behavior.
- [x] `docs/ExecPlans/ui_readiness_caveats_status_execplan.md` supplies ordered readiness and
  source-safety gating.
- [x] `docs/ExecPlans/ui_verification_recovery_reopen_execplan.md` supplies terminal failure and
  preserved-artifact recovery states.
- [x] `docs/ARCHITECTURE.md` assigns the signing action boundary/coordinator and Qt shell separate
  ownership; this child must preserve that split.

## Progress

- [x] (2026-08-10) Explorer audit identified synchronous executor invocation as the remaining
  UI_SPEC WF04/section 11 blocker; the worker/progress portion is complete, while durable artifact
  recovery was tracked separately and is now implemented by the recovery-journal child.
- [x] (2026-08-10) Defined typed transaction lifecycle state and a Qt-safe completion delivery seam;
  synchronous submit remains available for deterministic non-Qt tests.
- [x] (2026-08-10) Runs the executor off the GUI thread in the real Qt composition, preserves
  non-cancellable semantics, and closes the owned worker during workspace disposal.
- [x] (2026-08-10) Projects delayed stage/long-running copy through the signing rail while preserving terminal
  success/failure/recovery behavior.
- [x] (2026-08-10) Added runner/coordinator/boundary unit coverage and a real offscreen Qt timing
  test proving event-loop polling and terminal delivery.
- [x] (2026-08-10) Closed the post-pass findings: worker-start failures now emit only terminal
  failure, sub-second feedback keeps the readiness detail quiet, and the production composition
  path has fake-Qt coverage for timer ownership and worker cleanup.
- [x] (2026-08-10) Reconcile architecture, parent/child plans, and acceptance evidence.
- [x] (2026-08-10) Run focused/full validation, bounded GUI audit, cleanup, and compliance review.
- [x] (2026-08-10) Commit the completed slice as `8208f6666` and record the
  final revision.

## Surprises & Discoveries

- Observation: `SigningActionCoordinator.submit()` currently calls the injected executor directly
  and `SigningActionBoundary.submit()` renders only start and terminal status events.
  Evidence: `src/foliaseal/presentation/qt/signing_action_coordinator.py` and
  `src/foliaseal/presentation/qt/signing_action_boundary.py`.
- Observation: the executor API exposes no stage callback or percentage, so detailed backend
  progress would be invented. Evidence: `SigningRequestExecutor.execute()` is the only protocol
  method and `LazySigningRequestExecutor` delegates one synchronous call.
- Observation: the existing sidebar already owns one read-only stage/detail/result region and
  disables the primary action from `SigningActionState`; the new state should reuse that surface
  instead of adding a second progress widget.
  Evidence: `SigningWorkspaceSidebar.render_signing_action_state()`.

## Decision Log

- Decision: use a typed coarse lifecycle around the existing synchronous executor and do not claim
  backend percentages or cancellation.
  Rationale: UI_SPEC requires truthful stage feedback, while the current executor cannot provide
  finer-grained progress and the post-confirmation transaction is deliberately non-cancellable.
  Date/Author: 2026-08-10 / Codex.
- Decision: deliver worker completion back to the Qt thread through a polling/dispatch adapter owned
  by the mounted signing shell, not by mutating widgets from a worker thread.
  Rationale: Qt widgets must remain GUI-thread-owned, and an owned timer/dispatcher can be stopped
  during workspace disposal and tested without leaking threads.
  Date/Author: 2026-08-10 / Codex.
- Decision: retain synchronous `submit()` as a deterministic application/test seam while the
  production shell uses the asynchronous transaction path.
  Rationale: existing headless callers and unit tests can continue to exercise terminal policy;
  the real Qt path gains responsiveness without a compatibility alias in product terminology.
  Date/Author: 2026-08-10 / Codex.

## Outcomes & Retrospective

Implementation is complete through the production composition seam and real offscreen polling proof.
The production progress slice is committed as `8208f6666`; the current
checkout full suite is `1543 passed, 20 skipped, 1 warning`, with focused
transaction coverage, Ruff, compile, and diff checks clean. Durable journaling
and the verified GUI recovery surface now record and resolve owned staged
artifacts through explicit Open, Save copy as, Replace, and Discard actions.
Display-backed and privileged acceptance gates remain open.

Revision note: 2026-08-16 / Codex: reconciled the stale commit marker and
updated recovery/full-suite status against the current checkout.

## Context and Orientation

`SigningActionCoordinator` in `src/foliaseal/presentation/qt/signing_action_coordinator.py` owns
readiness, request construction, executor invocation, and terminal result state without importing
Qt. `SigningActionBoundary` in the adjacent module translates coordinator transitions into shell
callbacks. `SigningWorkspaceActionBridge` calls that boundary from the signing rail, and
`SigningWorkspaceSidebar` renders `SigningActionState` into one stage/detail/result region.
`SigningWorkspaceComposition` creates these objects; `SigningWorkspaceWidget` owns mounted-shell
cleanup and is the correct owner for a Qt timer or dispatcher. The executor is injected through
`SigningWorkspaceBootstrap` and currently provides only `execute(request)`.

“Non-blocking” means the Qt event loop can repaint and accept ordinary window events while the
executor runs elsewhere. “Coarse lifecycle” means the UI names the application-owned phases around
the one executor call; it does not claim that the backend has reported its internal sub-steps.

## Change Slice

Primary change class: behavior change. The slice may add one small Qt-neutral transaction runner,
typed coordinator/boundary lifecycle methods, shell timer/dispatch ownership, sidebar copy, focused
tests, one offscreen timing test, architecture/plan updates, and ignored local logs. The separate
recovery-journal child owns durable crash journals; do not mix autosave, backend progress callbacks,
cancellation, packaging, or unrelated
phase-nomenclature migration.

## Plan of Work

First add a typed lifecycle projection in `signing_action_coordinator.py`. It must distinguish idle,
running, and terminal state while preserving the existing `SigningActionState` fields used by the
sidebar. A begin operation applies pending controls, checks readiness, builds the request, and marks
the transaction active before returning the request and a signing-stage state. A completion operation
accepts either `SigningResult` or an exception, performs the existing mark-clean/secret-clear or
recovery logic, and returns the same terminal transition currently produced by `submit()`.

Add a Qt-independent runner boundary in a new
`src/foliaseal/presentation/qt/signing_transaction_runner.py`. It must start exactly one worker for
one request, retain the result/exception, expose `is_running()`, `poll_completion()`, and `close()`
or equivalent idempotent cleanup, and never call Qt widgets. Use a daemon-safe owned thread or
executor with an explicit join/shutdown path; `close()` must wait for a worker that is already
finishing and reject a second submission. The runner must not expose cancellation as a user action.

Extend `SigningActionBoundary` with begin/poll transaction methods that emit `sign_started` once,
project a running state, and emit the existing terminal status/error events only from the Qt-thread
poll path. Keep `submit()` as the synchronous deterministic seam for non-Qt callers and tests.

Update `SigningWorkspaceActionBridge` so the production shell begins the transaction and returns the
request immediately, while a mounted-shell timer polls completion and calls `reload_state()` after
each transition. Update `SigningWorkspaceWidget`/composition to construct the runner when a real
executor exists, start a bounded timer, stop it during disposal, and close the runner. If a fake
binding has no timer, the deterministic synchronous path remains available to tests; the real
PySide6 binding must use the non-blocking path.

Update `SigningActionState` and `SigningWorkspaceSidebar.render_signing_action_state()` with stable
copy such as “Signing — preparing and verifying…” and “Signing is taking longer than expected;
FoliaSeal is still working.” The sign button and conflicting output/recovery actions remain disabled
while active. Do not show a percentage, fake spinner claim, cancel button, or timeout that changes
the file operation. The delayed copy must be timer-derived, not executor-duration metadata guessed
in the worker.

## Milestones

### Milestone 1: typed lifecycle and runner proof

Add red coordinator/runner tests with a blocking fake executor. Prove readiness rejection never
starts a worker, a successful result clears secrets only at completion, a failed result preserves
recovery state, duplicate begin is rejected, and `close()` leaves no live worker. Implement until the
Qt-free tests pass.

### Milestone 2: shell projection and timing behavior

Wire the boundary/bridge/widget timer. Add fake-Qt tests proving the first immediate state remains
quiet, the one-second state has a real stage, the ten-second state has calm longer-than-expected
copy, and terminal completion restores existing success/failure/recovery actions.

### Milestone 3: real offscreen acceptance and closeout

Add a real offscreen Qt test using a blocking fake executor and event processing, plus a production
composition fake-Qt test for timer ownership. Observe that a window event can be processed while
signing is active, the stage/detail labels change at bounded thresholds, completion arrives on the
GUI thread, and closing the workspace stops the timer and leaves no worker. Run the full suite,
Ruff, pip check, diff check, bounded GUI launch, compliance review, architecture update, and commit.

## Concrete Steps

Run from `/home/daekar/FoliaSeal` with `.venv`:

    rg -n 'SigningActionCoordinator|SigningActionBoundary|sign_started|sign_success|execute\(|QTimer|QThread' src/foliaseal/presentation/qt src/foliaseal/application
    .venv/bin/pytest -q tests/unit/test_qt_signing_action_coordinator.py tests/unit/test_qt_signing_action_boundary.py tests/unit/test_qt_signing_transaction_runner.py
    QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q tests/integration/test_signing_transaction_progress.py
    .venv/bin/ruff check src tests
    QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q
    .venv/bin/python -m pip check
    git diff --check

For the bounded GUI audit use an owned temporary root and always remove it:

    audit_root=$(mktemp -d /tmp/foliaseal-signing-transaction-XXXXXX)
    set +e
    timeout --foreground 30s env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf
    rc=$?
    set -e
    printf 'gui_rc=%s\n' "$rc"
    ps -eo pid=,cmd= | rg 'FoliaSeal|foliaseal|PySide6|pytest' | rg -v 'rg ' || true
    rm -rf "$audit_root"
    test ! -e "$audit_root"

## Validation and Acceptance

After a user confirms signing, the window remains responsive. For a fast fake executor no running
copy is visible; for a deliberately blocking executor the rail shows the signing stage after about
one second and calm longer-than-expected copy after about ten seconds. Completion on the GUI thread
renders the existing verified-success or failure-recovery state. No percentage, cancellation, or
destructive timeout appears. A second Sign and save attempt is rejected while active. Closing or
replacing the workspace stops the timer and joins/cleans the owned worker without leaving a process
or thread behind. Full tests, focused tests, Ruff, pip check, diff check, and cleanup pass.

Durable crash-journal/restart recovery is covered by
`docs/ExecPlans/signing_transaction_recovery_journal_execplan.md`; this progress child does not
claim the GUI Open, Save copy as, Replace, or Discard surface.

## Idempotence and Recovery

Each runner owns one request and can be closed repeatedly. If composition or timer setup fails,
dispose only the new runner/candidate and leave the existing workspace mounted. Test workers use
short deterministic fakes and are joined in `finally`. Never kill arbitrary processes or delete
user PDFs, credentials, or signing artifacts.

## Artifacts and Notes

Keep timing logs and screenshots under `/tmp` or ignored `artifacts/`; do not commit them. Record
the observed thresholds, thread cleanup, terminal status, full-suite count, GUI return code, and any
known environment limitation in this plan before commit.

## Interfaces and Dependencies

The application/coordinator remains Qt-free. The runner’s minimal contract should be equivalent to:

    class SigningTransactionRunner(Protocol):
        def start(self, request: SigningRequest) -> None: ...
        def is_running(self) -> bool: ...
        def poll_completion(self) -> SigningResult | BaseException | None: ...
        def close(self) -> None: ...

`SigningActionBoundary` owns the typed begin/poll/terminal transition and callbacks. The shell owns
the Qt timer/dispatcher and cleanup. `SigningWorkspaceSidebar` renders only the resulting state.
No interface may add cancellation, fake percentages, or product-facing phase labels. Durable journal
ownership and headless recovery are supplied by the separate recovery-journal child.

Revision note: 2026-08-10 / Codex. Created after the source-change recovery commit and explorer
audit of the remaining UI_SPEC section 11 transaction-feedback gap.
