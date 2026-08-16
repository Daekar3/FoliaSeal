# Complete X11 Single-Instance and Live-Harness Acceptance

## Purpose

Mint 22.3 currently provides a real Cinnamon/X11 session but no supported Wayland session. The
single-instance transport and interactive harness were previously tested only offscreen because
the sandbox could not access `DISPLAY=:0`; a bounded unsandboxed X11 probe now proves that the
display and Qt can be reached. This slice uses that session to close the concrete X11 acceptance
gap without claiming Wayland support or full accessibility/release completion.

## Scope and explicit exclusions

In scope:

- real X11 two-process open-request forwarding and primary-owner lifecycle;
- real X11 interactive-harness launch, representative visual checkpoint, normal close, and
  process/artifact cleanup;
- reconciliation of the manual-harness, single-instance, release, accessibility, and parent
  ExecPlans with exact X11 evidence.

Out of scope:

- Wayland, which is intentionally deferred until Mint treats it as a first-class supported
  session;
- screen-reader interoperability, physical DPI/multi-monitor certification, or high-contrast
  human acceptance beyond what is explicitly observed;
- privileged host package installation;
- source behavior changes unless the X11 transport test exposes a real defect.

## Progress

- [x] (2026-08-16) Explorer audit identified X11 two-process routing as the strongest newly
  unblocked acceptance slice and confirmed current source/test ownership.
- [x] (2026-08-16) `xdpyinfo` and a temporary Qt window succeeded against `DISPLAY=:0`; a real
  FoliaSeal window and interactive-harness window were observed and closed with clean process
  cleanup.
- [x] (2026-08-16) Ran the two-process X11 forwarding smoke with direct PID ownership. The primary
  remained alive with one FoliaSeal window, the secondary exited `0`, and the primary exposed the
  forwarded request without creating a second owner. The focused integration test passed `1 passed`
  under X11.
- [x] (2026-08-16) Ran the interactive harness on the real X11 desktop with the checked-in
  checklist supplied explicitly, captured `/tmp/foliaseal-x11-harness-screen.png`, observed the
  harness window, closed it normally, and obtained `harness_rc=0`, a written summary/results pair,
  and three local capture artifacts. The disposable run used
  `/tmp/foliaseal-x11-harness-2FTB5t/summary.json` and
  `/tmp/foliaseal-x11-harness-2FTB5t/results.md`, with checklist source
  `artifacts/phase3_fr3b_acceptance_checklist.md`; its capture directory contained
  `interactive_final.png`, `interactive_final_stamp_debug.png`, and one additional rendered
  preview artifact before cleanup. The automated verdict was correctly `non_gating` because no
  placement/signing action was performed in this bounded smoke.
- [x] (2026-08-16) Reconciled the owning plans, README, and architecture record; the post-
  implementation explorer found no source/spec discrepancy after clarifying historical sandbox
  failures, and the architecture/docs review confirmed that packaged, accessibility, privileged,
  final-release, and Wayland claims remain correctly open/deferred. `git diff --check`, Ruff,
  compileall, focused tests (`78 passed, 10 skipped`), and the full suite (`1535 passed, 20 skipped,
  1 warning`) are green. Commit remains the final handoff step.

## Validation and acceptance

- Primary `foliaseal gui` remains alive and owns one endpoint/window.
- A secondary `foliaseal gui --pdf-path ...` exits successfully by forwarding to the primary;
  no second FoliaSeal process/window is created, and the primary receives the request.
- `tests/integration/test_single_instance_open_routing.py` runs without the prior
  `QLocalServer` skip under X11, plus the pending-open integration test passes.
- `interactive-harness` opens the representative PDF with the test identity, produces a live
  X11 window/checkpoint, and closes normally with no FoliaSeal/PySide6/pytest residue.
- Ruff, compileall, focused tests, and `git diff --check` pass.
- Wayland and the remaining human/privileged gates remain explicitly unchecked.

## Friction and follow-up

- The first real harness launch used the CLI default checklist path and failed at report finalization
  because `artifacts/acceptance_fr3b_acceptance_checklist.md` is absent from this checkout. Re-running
  with the available checked-in checklist path succeeded; the missing default is a release/documentation
  follow-up, not a GUI startup failure.
- The visual checkpoint proves that the current X11 desktop can host the harness, but it does not close
  the four-tracer-case human audit, screen-reader/high-contrast, physical-DPI/multi-monitor, packaged
  desktop, or privileged-install gates.

## Recovery and idempotence

Use one exact temporary XDG config/cache root shared by the two processes so the endpoint is
shared, and keep `XDG_RUNTIME_DIR=/run/user/1000`, `DISPLAY=:0`, and
`XAUTHORITY=/home/daekar/.Xauthority`. Terminate only PIDs created by this run, close owned
windows normally first, remove the exact temporary root, and verify no process or socket remains.
