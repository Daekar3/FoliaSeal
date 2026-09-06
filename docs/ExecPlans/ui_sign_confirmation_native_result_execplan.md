# Make the final sign confirmation submit reliably

This ExecPlan is a living document and must be maintained in accordance with
`/home/daekar/.codex/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, a user who chooses **Sign and save** in FoliaSeal's final
confirmation dialog will reliably start the signing transaction. The signed
PDF will either be created and verified, or the application will show a clear
failure; the dialog must never disappear and silently leave the workflow at
Step 5. The result is observable in the GUI and through focused tests.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/ui_sign_confirmation_output_policy_execplan.md` — owns the
  typed summary, output-path policy, and consequence-labelled confirmation
  surface on which this correction builds.
- [x] Live HITL evidence — the summary dialog displayed correctly, but clicking
  **Sign and save** returned to the unchanged Step 5 state, produced no output,
  and left no transaction journal record.

## Progress

- [x] (2026-09-06) Reproduced the user-visible no-op in the installed package:
  the final dialog closed, the main window remained open at “Step 5 of 6 —
  Confirm and sign” with normal readiness text, and no signed PDF appeared.
- [x] (2026-09-06) Confirmed there was no recent signing journal record or
  diagnostic error. This is inconclusive about executor entry because the
  signing use case discards journals for ordinary pre-staging failures; the
  next evidence must come from assembled transaction state and terminal
  results, not journal absence alone.
- [x] (2026-09-06) Explorer review identified the fragile
  `clickedButton() is affirmative_button` wrapper-identity comparison as the
  most likely silent-cancellation cause; preview generation may account for
  the brief CPU spike.
- [x] (2026-09-06) Replaced wrapper-identity-only matching with semantic
  label/role matching for native Qt confirmation results, while retaining
  identity matching and the lightweight-double fallback.
- [x] (2026-09-06) Added bridge regressions for an equivalent affirmative
  wrapper and an unrecognized result; the latter now surfaces an explicit
  warning and does not submit signing.
- [x] (2026-09-06) Focused bridge validation passes (`12 passed`); updated the
  architecture contract to document semantic native-button matching and
  explicit unexpected-result diagnostics.
- [x] (2026-09-06) Full regression and lint pass: `1626 passed, 20 skipped,
  1 warning` and Ruff/diff checks clean. The remaining validation gate is a
  real installed-package signing attempt through the desktop session.
- [ ] Perform a bounded installed-package retest.
- [ ] Commit the completed behavior and documentation slice.
- [x] (2026-09-06) Retested the rebuilt package in the desktop session. The
  final dialog still closed to unchanged Step 5 with no output, proving the
  first semantic-button correction was insufficient. No transaction journal
  record was created.
- [x] Make missing transaction-runner and transaction-start failures visible,
  add real-Qt confirmation coverage, and rebuild for a second HITL retest.
- [x] (2026-09-06) Added a boundary guard that converts a configured executor
  without an owned transaction runner into a visible `sign_failure` result,
  and preserved the status event in the boundary result.
- [x] (2026-09-06) Added matching startup-failure handling for coordinator
  exceptions and transaction-runner start exceptions: each now reaches a
  terminal `sign_failure` through the normal shell status/error callbacks
  instead of leaving an active Step 5 request without worker delivery.
- [x] (2026-09-06) Added real offscreen PySide6 coverage proving that a native
  **Sign and save** button click is accepted by the confirmation adapter.
- [x] (2026-09-06) Added an end-to-end offscreen bridge test using real Qt
  confirmation controls and the asynchronous submission route; both native
  confirmation integration tests pass (`2 passed`).
- [x] (2026-09-06) Re-ran full validation after the startup-failure guard:
  `1630 passed, 20 skipped, 1 warning`; Ruff and diff checks remain clean.
- [x] (2026-09-06) Rebuilt the package from commits `d0a5741cc`, `222360e45`,
  and `511aa71db`: `/tmp/foliaseal-signing-fix3-dist/foliaseal_0.1.0_amd64.deb`
  (SHA-256 `e2c77aae6484feb1d580acabd98c6534da448505c4b42059255cf0552a65b363`).
- [ ] Install this corrected package, then repeat the desktop
  signing workflow and record the resulting status/output.
- [x] (2026-09-06) Compliance review confirmed the guard aligns with
  SPEC/UI_SPEC, but identified that the current tests do not exercise the full
  production composition from native confirmation through runner completion.
- [ ] Add an end-to-end offscreen composition test for successful and failed
  transactions, then use its route evidence to target the remaining live issue.
- [ ] If the second installed retest still fails, capture the assembled
  production composition's async capability, startup status, terminal status,
  and worker/polling evidence before changing signing behavior again.

## Surprises & Discoveries

- Observation: the confirmation text and summary were correct, but the final
  action was a silent no-op.
  Evidence: the panel returned to “Step 5 of 6 — Confirm and sign”; no output
  file, signing journal record, or error log was created.
- Observation: the current implementation compares Python object identity for
  Qt button wrappers.
  Evidence: `signing_workspace_action_bridge.py::_ask_consequence_confirmation`
  returns true only when `clickedButton() is affirmative_button`.
- Observation: a short CPU spike does not prove signing began.
  Evidence: preparing the confirmation summary calls `apply_changes()` and
  `draft_workflow.preview()`, both of which can perform preview work before the
  confirmation result is interpreted.
- Observation: the rebuilt package still returns to the unchanged Step 5 state
  after the affirmative click.
  Evidence: the installed binary matches the rebuilt artifact, but no signing
  journal record or output file appears. Journal absence is not itself proof
  that the executor was skipped, because ordinary failures before staging
  discard their journal. The next investigation must cover a missing
  transaction runner, an exception before worker start, completion polling, and
  backend terminal failure rather than assuming the dialog result is the only
  boundary.
- Observation: a real offscreen Qt message box accepts the affirmative button
  through the semantic adapter.
  Evidence: `tests/integration/test_qt_sign_confirmation_native.py` passes,
  so the remaining installed failure is most plausibly production wiring or
  pre-worker state transition rather than the native button API itself.
- Observation: the missing-runner guard is defensive rather than the normal
  production route.
  Evidence: `submit_sign_request()` chooses `begin_transaction()` only when
  `supports_async_transaction` is true; otherwise it calls synchronous
  `boundary.submit()`. End-to-end composition coverage is therefore required
  before attributing the live no-op to runner wiring.
- Observation: startup exceptions require the same visible terminal handling
  as a missing runner. `SigningActionBoundary` now converts coordinator and
  worker-start exceptions to `sign_failure`, while runner-start failures use
  the coordinator's ordinary terminal transition. This keeps the shell's
  status/error callbacks as the single user-visible failure path.

## Decision Log

- Decision: Treat the native confirmation result as a semantic Qt result, not a
  Python-wrapper identity comparison.
  Rationale: Qt may return a distinct Python wrapper for the same underlying
  `QAbstractButton`; identity failure currently becomes silent cancellation.
  Date/Author: 2026-09-06 / Codex.

- Decision: Match native confirmation buttons by stable displayed label and,
  when available, their Qt button role; retain identity matching only as a fast
  path and label-only matching for minimal test doubles.
  Rationale: PySide can expose a distinct wrapper for the same native button,
  while the dialog's own labels and roles provide the semantic result needed
  to submit safely.
  Date/Author: 2026-09-06 / Codex.
- Decision: Keep the change limited to final confirmation result handling and
  its tests; do not change signing backend or output-path policy in this slice.
  Rationale: the existing evidence does not distinguish a pre-worker failure
  from an ordinary backend failure whose journal was discarded, so backend
  changes would be speculative and broaden the review.
  Date/Author: 2026-09-06 / Codex.
- Decision: Preserve the Cancel-default behavior and make an unrecognized
  result explicit rather than treating it as cancellation.
  Rationale: irreversible signing must remain safe, but silent no-ops are not
  acceptable and prevent diagnosis.
  Date/Author: 2026-09-06 / Codex.
- Decision: Treat a configured signing executor without an available
  transaction runner, or a start-time exception before worker launch, as an
  explicit signing failure instead of leaving the UI at Step 5.
  Rationale: the observed unchanged readiness state and absent journal make a
  pre-worker failure plausible; users need a visible state and diagnostic.
  Date/Author: 2026-09-06 / Codex.
- Decision: Add production-composition coverage before making further runtime
  behavior changes.
  Rationale: isolated button and boundary tests pass, while the installed app
  still remains at Step 5. The missing evidence is the assembled route and its
  timer/worker wiring, not another speculative backend change.
  Date/Author: 2026-09-06 / Codex.
- Decision: Fail visibly when `SigningActionBoundary` receives a request but no
  transaction runner is available, and retain the terminal status event in its
  returned result.
  Rationale: this prevents a miswired production composition from leaving the
  UI indefinitely at Step 5 with no journal or diagnostic.
  Date/Author: 2026-09-06 / Codex.
- Decision: Treat coordinator and worker-start exceptions as terminal startup
  failures on the same boundary seam.
  Rationale: a request must never remain visually active without a worker that
  can deliver completion; routing these failures through `sign_failure`
  preserves the non-cancellable transaction contract and gives the user an
  actionable error.
  Date/Author: 2026-09-06 / Codex.

## Outcomes & Retrospective

The bridge now interprets the native final-dialog result semantically, so an
equivalent PySide wrapper for **Sign and save** reaches the transaction
boundary. Cancel remains lossless. An unrecognized result emits an explicit
warning and does not submit. The boundary also surfaces coordinator, missing
runner, and worker-start failures as terminal `sign_failure` results. Full-suite
validation is complete (`1630 passed, 20 skipped, 1 warning`) after this
startup-failure correction, plus two real offscreen Qt confirmation tests
(`2 passed`). The
first rebuilt installed-package retest still failed to leave Step 5. The second
corrected package has not yet been installed/retested, and full production
composition coverage is still open; a successful installed run must reach Step
6 and produce a verified PDF, otherwise the next evidence must identify
whether confirmation, composition, worker startup, polling, or the backend is
responsible.

## Context and Orientation

FoliaSeal is a Python/PySide6 Linux PDF signing application. The final signing
flow is split across these boundaries:

- `src/foliaseal/presentation/qt/signing_workspace_action_bridge.py` owns the
  Qt-facing output selection and final confirmation dialog. Its
  `submit_sign_request()` method must call `begin_transaction()` only after the
  user accepts the summary.
- `src/foliaseal/presentation/qt/signing_action_boundary.py` starts the owned
  signing worker and delivers terminal results.
- `src/foliaseal/presentation/qt/signing_transaction_runner.py` runs the
  backend away from the Qt event loop and queues either a `SigningResult` or an
  exception.
- `src/foliaseal/presentation/qt/signing_action_coordinator.py` projects the
  transaction into the visible signing status panel.

The real Qt path creates a `QMessageBox`, adds a Cancel button with
`RejectRole` and a Sign and save button with `AcceptRole`, runs the modal event
loop, and reads `clickedButton()`. Test doubles may expose only a simpler
question API. “Semantic result” means a stable fact such as the button role,
button text, or the dialog's accepted result, rather than Python object identity.

## Change Slice

Primary change class: behavior change. Allowed files are the confirmation
bridge, focused bridge tests, this ExecPlan, and the minimum architecture/status
documentation needed to describe the corrected contract. Generated packages,
private certificate material, unrelated UI styling, and signing-backend changes
are forbidden in this slice.

## Plan of Work

First, inspect the concrete PySide6 `QMessageBox` API available to the packaged
application and choose a stable result check. Prefer reading the clicked
button's `text()` or its `buttonRole()` and accepting only the button created
with the affirmative label and `AcceptRole`; retain the existing static
question fallback for legacy harness doubles.

Then change `_ask_consequence_confirmation()` so Cancel remains the default,
affirmative acceptance starts the transaction, and an unexpected result emits
an explicit diagnostic/error path instead of silently returning false. Keep the
public `submit_sign_request()` contract unchanged.

Add tests through the bridge's public method for affirmative submission,
Cancel-lossless behavior, and an unrecognized clicked-button result. Include a
regression double that returns an equivalent-but-not-identical button wrapper,
which must be accepted when its semantic label and role match.

Finally run the focused Qt signing tests, the full suite and lint, update the
parent confirmation plan and architecture/status documentation if the contract
has changed, and perform one bounded installed-package signing attempt. Record
whether a journal record appears, whether the output is verified, and clean all
owned processes and temporary artifacts.

## Milestones

Milestone 1 establishes a failing regression for an equivalent non-identical
affirmative button result. The test must fail against the current identity
comparison and pass after the semantic-result change.

Milestone 2 implements the smallest confirmation-result adapter and explicit
unexpected-result handling. Focused bridge and shell tests must pass, proving
that acceptance reaches the submission boundary while cancellation remains
lossless.

Milestone 3 validates the installed package and records evidence. A successful
run must create the requested sibling PDF and advance the status panel to
Step 6; a backend failure must remain visible as “Signing failed” with a useful
message rather than returning silently to Step 5.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

    rg -n "clickedButton|addButton|_ask_consequence_confirmation" src/foliaseal/presentation/qt tests/unit
    .venv/bin/pytest -q tests/unit/test_qt_signing_workspace_action_bridge.py tests/unit/test_qt_signing_action_boundary.py tests/unit/test_qt_signing_shell.py
    .venv/bin/ruff check src tests
    .venv/bin/pytest -q
    git diff --check

For installed acceptance, launch the installed package with output capture,
repeat the disposable signing workflow, wait for a terminal status, then check
the requested output path and transaction journal. Do not delete active
application artifacts while the application is open.

    /usr/bin/foliaseal gui 2>&1 | tee /tmp/foliaseal-signing-run.log
    find "$HOME/Downloads" -maxdepth 1 -type f -name '*-signed.pdf' -printf '%TY-%Tm-%Td %TH:%TM:%TS %s %p\\n'
    find "$HOME/.config/FoliaSeal/signing-transactions" -maxdepth 1 -type f -printf '%p\\n' 2>/dev/null || true

## Validation and Acceptance

The focused bridge test must demonstrate that an affirmative semantic result
returns a request and marks the transaction as submitted. A Cancel result must
return `None` without changing the draft. An unexpected result must produce a
visible diagnostic/error rather than silently returning to the ready state.

The full test suite and Ruff must pass. Installed acceptance is successful only
when the requested signed PDF exists, the GUI reaches “Step 6 of 6 — Verify
signed PDF”, and no stale signing worker or modal dialog remains. If the
backend reports a real signing failure, record that failure and its evidence in
this plan instead of claiming completion.

## Idempotence and Recovery

The tests are repeatable and use temporary files. The installed acceptance must
use a disposable PDF and a collision-safe output name. If the app hangs, leave
the process intact long enough to capture its status and logs, then close it
normally; if it exits, inspect the terminal log and coredump list before
retrying. Remove only temporary artifacts owned by this slice and ensure no
FoliaSeal process or modal dialog is left behind.

## Artifacts and Notes

Do not commit the installed `.deb`, private keys, signed user documents, or
absolute machine-local paths. Commit only source, tests, this plan, and concise
status/architecture evidence. Preserve the terminal log path and output/journal
observations in the plan while the audit is active; redact private material.

## Interfaces and Dependencies

The corrected bridge must continue to expose:

    SigningWorkspaceActionBridge.submit_sign_request() -> SigningRequest | None

The method must use `SigningActionBoundary.begin_transaction()` for the real
Qt production path. The confirmation adapter may use PySide6's
`QMessageBox.ButtonRole`, `clickedButton()`, `buttonRole()`, `text()`, and
`exec()` APIs, while retaining the existing static `question()` fallback for
non-Qt test/harness doubles. No new dependency is required.

Revision note: 2026-09-06 / Codex: created after installed HITL evidence showed
that the final confirmation closed without submitting a signing transaction.

Revision note: 2026-09-06 / Codex: implemented semantic native-button result
matching and explicit unexpected-result diagnostics; focused regression tests
are present. Installed-package signing and final display-backed acceptance
remain open.
