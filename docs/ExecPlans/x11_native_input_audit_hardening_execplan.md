# Harden the supported X11 native-input audit boundary

This ExecPlan is a living document and must be maintained in accordance with
`/home/daekar/.codex/skills/write-execplan/PLANS.md`. It is a documentation,
audit-tooling, and test slice under
`docs/ExecPlans/ui_product_support_and_release_execplan.md` and
`docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md`.

## Purpose / Big Picture

The supported Cinnamon/X11 accessibility audit already proves that FoliaSeal's
real Qt Help action can receive a native F1 event, but one run failed after the
window manager reported activation even though direct Qt and offscreen F1 tests
passed. A later run passed without a product change. This indicates a desktop
focus race in the audit boundary, not a missing application shortcut.

After this slice, a future X11 audit will record the native input focus it saw,
reactivate the owned window between bounded native-F1 attempts when the Help
viewer has not opened, and report the attempt/focus diagnostics. The product
shortcut and UI behavior remain unchanged. A person
can see the result by running the audit on the supported X11 display and
observing a passed Help check or a precise focus-delivery diagnostic instead of
an unexplained assertion.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md` and `docs/UI_SPEC.md` require the F1 Help route and do not
  authorize Wayland coverage for this Mint 22.3 audit.
- [x] `docs/ExecPlans/ui_product_support_and_release_execplan.md` records the
  intermittent native-F1 failure and the successful follow-up run.
- [x] `scripts/live_gui_accessibility_audit.py` is the existing bounded X11
  audit owner, and product F1 wiring is covered by real-Qt tests.

## Progress

- [x] (2026-08-16) Audited the current source, tests, release plans, and
  independent review evidence. The failure is isolated to the `wmctrl`/
  `XSetInputFocus`/XTest delivery boundary; no AppFrame change is justified.
- [x] (2026-08-16) Added a small, testable X11 focus-observation and bounded retry seam to
  `scripts/live_gui_accessibility_audit.py` without changing the default
  display requirement or probing Wayland.
- [x] (2026-08-16) Added focused headless tests for retry success, activation
  exhaustion, delivery-error diagnostics, and invalid attempt bounds; the
  focused Qt/F1 group is `6 passed`.
- [x] (2026-08-16) Ran the supported X11 audit. The first native-F1 attempt
  retained the same focused window but did not open Help; the second bounded
  attempt observed the focus transition and opened the modeless Help viewer.
  The report recorded `attempt_count=2`, `opened=true`, AT-SPI
  `unavailable` because the registry is absent, and `cleanup.passed=true`.
- [x] (2026-08-16) Ran the full suite (`1578 passed, 20 skipped, 1 warning`),
  Ruff, compileall, and diff checks; removed the exact audit root and verified
  no FoliaSeal/PySide6/pytest process or owned window remained.
- [x] (2026-08-16) Independent review confirmed the slice is audit-only,
  bounded, JSON-safe, cleanup-preserving, and consistent with SPEC/UI_SPEC/
  ARCHITECTURE. The plan wording was tightened to describe reactivation and
  retry rather than claiming an explicit pre-first-attempt settle.
- [ ] Commit the bounded slice and verify the post-commit checkout and owned
  resource cleanup.

## Surprises & Discoveries

- Observation: the same native-X11 audit failed once and passed on the next
  run with unchanged product code.
  Evidence: the failure was `native X11 F1 did not open the Help viewer`, while
  the follow-up reached the modeless viewer and cleaned up successfully.
- Observation: the current report records WM activation but not the X11 input
  focus actually observed immediately before injection.
  Evidence: `native_input` currently contains only the two `wmctrl` booleans.
- Observation: offscreen and real-Qt `QTest.keyClick` tests already exercise
  the application shortcut, including a focused child editor.
  Evidence: `tests/integration/test_help_viewer.py` and
  `tests/integration/test_accessibility_acceptance.py` pass F1 through Qt.
- Observation: the live hardened audit reproduced the transient boundary
  without reproducing a product failure: the first attempt had the expected
  X11 focus ID but no Help viewer, while the second attempt saw a new focus ID
  and opened Help.
  Evidence: the temporary report recorded two attempts, both WM activations
  true, `opened=true`, and clean teardown.

## Decision Log

- Decision: harden only the audit boundary, not product shortcut wiring.
  Rationale: direct QAction and Qt tests pass, and changing AppFrame would
  obscure a desktop focus race and risk altering user behavior.
  Date/Author: 2026-08-16 / Codex.
- Decision: use at most three native-F1 attempts, reactivating between failed
  attempts and recording each attempt and observed focus window.
  Rationale: the audit must tolerate a transient WM race without hanging or
  masking a real failure; a fixed bound keeps the evidence deterministic while
  matching the actual X11 timing boundary.
  Date/Author: 2026-08-16 / Codex.
- Decision: keep the audit X11-only and reject no-display/Wayland conditions as
  before.
  Rationale: Mint 22.3 Wayland is experimental by user direction, and this
  slice must not create unsupported evidence or imply product support.
  Date/Author: 2026-08-16 / Codex.

## Outcomes & Retrospective

The audit-tooling improvement is complete with no product source change. The
report now distinguishes activation from actual X11 focus and a bounded retry
handled a real first-attempt delivery miss without masking it. Remaining human
screen-reader, high-contrast, physical-DPI/monitor, privileged-install, and
final release gates remain external; AT-SPI speech was not claimed because the
session registry is unavailable.

## Context and Orientation

`scripts/live_gui_accessibility_audit.py` builds one uniquely titled
`QtAppFrameAdapter` window, activates it with `wmctrl`, directly triggers the
Help QAction, closes it, and then uses `ctypes` to call `libX11` and
`libXtst` for one native F1 press. `XSetInputFocus` selects the target window;
`XTestFakeKeyEvent` sends the press/release pair. The audit pumps the Qt event
loop and expects `frame.help_viewer` to become non-`None`.

The application implementation is in
`src/foliaseal/presentation/qt/app_frame.py` and
`src/foliaseal/presentation/qt/app_frame_command_model.py`; these files already
define the F1 command and must not be changed by this slice. Existing focused
tests prove the product path. New tests should load the audit script as a
module and exercise only the deterministic retry/diagnostic seam, never require
the desktop, and never open a user window.

## Change Slice

The primary change class is audit-tooling behavior plus focused tests and
truthful ExecPlan documentation. Allowed files are
`scripts/live_gui_accessibility_audit.py`, a new focused test module under
`tests/`, this plan, and the two owning release-plan status records. Generated
JSON, screenshots, packages, credentials, and machine-local paths are ignored
and must not be committed. Product Qt behavior, schemas, CLI commands, and
Wayland code are forbidden in this slice.

## Plan of Work

First extract or add a small helper around `_X11Input` that can report the
current X11 input-focus window ID using `XGetInputFocus`, while safely returning
an explicit unavailable value if the display cannot provide it. Add a bounded
native-F1 delivery helper that accepts the Qt event-pump/wait callback and the
target window ID, records the focus before each attempt, and retries only when
the Help viewer is still absent. Each attempt re-activates the same owned
window, records the resulting focus, sends one F1 press/release pair, and waits
for Help; a short delay is used only between unsuccessful attempts.

Keep the existing direct QAction check before native input. Extend
`report["native_input"]` with a versioned, JSON-safe attempt list or equivalent
fields containing activation result, observed focus IDs, attempt count, and the
final delivery result. Preserve the existing `status`, `error`, and cleanup
fields so downstream release evidence remains compatible. Do not make a failed
native event pass merely because `wmctrl` returned zero; Help must actually open.

Add focused unit tests for: a first-attempt success; a transient first failure
followed by success; exhaustion after the fixed attempt bound; focus IDs being
recorded; and exceptions remaining explicit. Tests must use fakes for X11,
activation, event pumping, and time, so they run headlessly. Run existing
integration F1 tests unchanged to prove product behavior has not moved.

## Milestones

### Milestone 1: deterministic retry seam

The audit module exposes a small internal helper whose fake-driven tests prove
bounded retry, focus diagnostics, and failure propagation without a display.

### Milestone 2: live X11 integration

The real audit uses that helper after WM activation, records native focus and
attempts, opens the modeless Help viewer on the supported X11 display, and
performs its existing owned-window/temp-root cleanup.

### Milestone 3: release closeout

Focused and full validation, independent SPEC/UI_SPEC/ARCHITECTURE review,
plan reconciliation, a focused commit, and final process/window/temp-root
inspection are complete. The report must still distinguish source-tree X11
evidence from human and privileged release acceptance.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    .venv/bin/pytest -q tests/unit/test_x11_accessibility_audit.py tests/integration/test_help_viewer.py tests/integration/test_accessibility_acceptance.py
    .venv/bin/ruff check scripts/live_gui_accessibility_audit.py tests/unit/test_x11_accessibility_audit.py
    .venv/bin/python -m compileall -q scripts/live_gui_accessibility_audit.py
    DISPLAY=:0 XDG_SESSION_TYPE=x11 .venv/bin/python scripts/live_gui_accessibility_audit.py --artifacts-dir /tmp/foliaseal-x11-input-hardening --capture-screenshot --probe-atspi
    .venv/bin/pytest -q

Inspect the JSON report before closeout. A successful live run includes
`native_input` attempt/focus diagnostics, `help.opened=true`, and
`cleanup.passed=true`. A limited AT-SPI result is acceptable when the session
bus lacks `org.a11y.atspi.Registry`; it is not screen-reader acceptance.
Remove the exact audit root and verify no FoliaSeal/PySide6/pytest process or
owned window remains. Never run the command with a Wayland display.

## Validation and Acceptance

Acceptance is behavioral and diagnostic: Qt F1 integration tests remain green;
the headless retry tests prove the fixed bound and transparent failure; and a
supported X11 run either opens Help after native input or reports the observed
focus/activation sequence without leaving resources behind. Full-suite, Ruff,
compile, and diff checks must pass. No source product behavior or Wayland
support claim may change.

## Idempotence and Recovery

The unit tests are repeatable and headless. The live command owns only its
uniquely named window, temporary configuration, and report root. If the live
audit fails, preserve its JSON long enough to inspect the diagnostics, then
remove that exact root and retry once; do not close unrelated windows or delete
unrelated `/tmp` entries. If X11 is unavailable, record the environment gate
as unavailable and do not substitute Wayland.

## Artifacts and Notes

Only the source script, focused tests, this plan, and concise release-plan
status text may be committed. Screenshots and JSON remain temporary. Record
the focused test count, full-suite count, audit status, cleanup result, and
commit hash in `Progress` and `Outcomes & Retrospective` when complete.

## Interfaces and Dependencies

Use Python `ctypes` bindings already present in `_X11Input`, `wmctrl` for
activation, Qt's existing `QApplication.processEvents()` loop, and the current
`HelpViewerDialog` observable (`frame.help_viewer`). Do not add dependencies.
The helper must be callable with fake collaborators so test code does not load
Qt or connect to X11; the live path remains the only caller that opens the
desktop display.

Revision note: 2026-08-16 / Codex: created after a successful follow-up X11
run confirmed that the prior native-F1 failure was an intermittent focus/input
delivery race rather than a product shortcut defect. The slice hardens the
evidence boundary without changing product behavior or probing Wayland.
Revision note: 2026-08-16 / Codex: implementation and live evidence completed;
the first attempt missed Help, the second attempt succeeded, and the full
suite remained green. Independent review and commit closeout remain.
