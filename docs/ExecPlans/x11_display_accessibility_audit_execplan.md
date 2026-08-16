# Bounded Cinnamon/X11 display accessibility audit

This ExecPlan is a living document and must be maintained in accordance with
`.agents/skills/write-execplan/PLANS.md`. It is an AFK child of
`docs/ExecPlans/ui_accessibility_acceptance_execplan.md` and
`docs/ExecPlans/ui_product_support_and_release_execplan.md`.

## Purpose / Big Picture

The offscreen accessibility contract is green, but a real X11 run exposed that
the existing `QTest.keyClick()` assertion cannot deliver the F1 shortcut when
the test window does not own the desktop focus. This slice adds a bounded,
semantic display-backed audit that uses the real Cinnamon/X11 session and the
system XTest boundary to focus the audit-owned window and send F1. It records
actual minimum geometry, accessible primary controls, menu metadata, F1 Help
reachability, monitor geometry, theme/scaling context, and cleanup. It does not
claim screen-reader speech, high-contrast conformance, privileged package
installation, or Wayland support.

## Child Dependencies

- [x] `docs/ExecPlans/ui_accessibility_acceptance_execplan.md` — real-Qt
  offscreen names, keyboard semantics, menus, Help, Settings, and support
  dialogs are implemented and tested.
- [x] `docs/ExecPlans/ui_product_support_and_release_execplan.md` — owns the
  final cross-surface release bar and genuine external gates.
- [x] Current supported session is Cinnamon/X11; Wayland is deferred for Mint
  22.3 by explicit user direction.

## Progress

- [x] (2026-08-16) Escalated display preflight confirmed Cinnamon/X11 on two
  1920x1080 monitors at 144 Hz; Mint theme is `Mint-Y-Dark` with text scaling
  `1.0`, and Orca `46.1` is installed.
- [x] (2026-08-16) The existing real-display accessibility test failed only at
  F1 Help because `QTest.keyClick()` did not own the desktop focus; no
  production behavior failure was inferred from that weak injection path.
- [x] (2026-08-16) Added the semantic X11 audit runner with an explicit
  libX11/libXtst input boundary, a uniquely titled owned window, and temporary
  configuration/storage.
- [x] (2026-08-16) Ran the audit successfully: direct Help QAction wiring and
  native XTest F1 both opened the modeless Help viewer after exact WM activation;
  the report captured geometry, controls, menu metadata, monitor/theme/scaling/
  Orca context, and cleanup. The runner requires WM activation, enforces a
  15-second deadline, records post-teardown window/process/root checks, and the
  report was removed after inspection.
- [x] (2026-08-16) Addressed review findings by requiring successful exact WM
  activation before XTest input, adding the runner deadline, and making the
  report fail if an owned window, child process, or temporary root remains.
- [x] (2026-08-16) The optional host-Python AT-SPI probe classified the current
  session as unavailable because the session bus lacks
  `org.a11y.atspi.Registry`; native F1, semantic Qt evidence, and cleanup still
  pass. This does not claim an accessible-tree or screen-reader result.
- [x] (2026-08-16) Reconciled the accessibility/release/parent plans and obtained
  independent architecture/documentation review; the focused slice is committed
  as `746025bcb` (`test: audit X11 accessibility input path`).

## Surprises & Discoveries

- A real display exists, but the test process is not necessarily the focused
  desktop client. Qt's direct `QTest.keyClick()` therefore does not prove a
  human keyboard shortcut on X11 even when the same test passes offscreen.
- `wmctrl` and `xrandr` are available in the escalated host session; the audit
  must use exact window/process ownership and must not activate or close the
  user's unrelated terminal/VS Code windows.
- XTest is available through the host `libXtst` boundary but is not a Python
  runtime dependency. The runner uses a tiny ctypes adapter and fails closed
  when the display or library is unavailable.

## Decision Log

- Decision: add a repository audit runner rather than weakening the offscreen
  test or adding a test-only shortcut trigger. The runner first verifies the
  production QAction directly, then separately delivers native F1.
  Rationale: display-backed evidence needs real OS input while the product
  shortcut remains the existing QAction contract.
  Date/Author: 2026-08-16 / Codex
- Decision: use libX11/libXtst only inside the audit script, never in FoliaSeal
  runtime code or package dependencies.
  Rationale: X11 is a platform-realization audit boundary and Wayland is
  intentionally deferred; product code remains toolkit-native and portable.
  Date/Author: 2026-08-16 / Codex
- Decision: report monitor/theme/Orca context but leave screen-reader,
  high-contrast, physical-DPI interpretation, package installation, and final
  human release acceptance open.
  Rationale: metadata and a shortcut event are evidence inputs, not proof of
  assistive-technology output or visual judgment.
  Date/Author: 2026-08-16 / Codex
- Decision: ask the X11 window manager to activate only the uniquely titled
  audit window before sending XTest input.
  Rationale: direct `XSetInputFocus` alone was rejected by the desktop focus
  policy; exact WM activation made native F1 delivery reproducible without
  touching unrelated user windows.
  Date/Author: 2026-08-16 / Codex

## Outcomes & Retrospective

The audit passed on Cinnamon/X11 with `DISPLAY=:0` and `QT_QPA_PLATFORM=xcb`.
Direct QAction wiring passed, and native F1 opened the modeless Help viewer after
`wmctrl -ia` activation of the uniquely titled audit window. It recorded two
1920x1080 144 Hz monitors, `Mint-Y-Dark`, text scaling `1.0`, and Orca `46.1`.
The owned frame/dialog/temp root were cleaned and no matching FoliaSeal audit
process or window remained. This is source-tree native-X11 evidence only; human
screen-reader speech, high contrast, physical-DPI interpretation, packaged GUI,
privileged installation, final release acceptance, and Wayland remain open or
deferred. The final commit is `746025bcb`; the post-commit worktree and owned
process/window cleanup are clean.

## Context and Orientation

`src/foliaseal/presentation/qt/app_frame.py` owns the Help QAction and modeless
Help viewer. `tests/integration/test_accessibility_acceptance.py` owns the
offscreen contract but is intentionally not changed to pretend it is a real
display test. The new runner lives at
`scripts/live_gui_accessibility_audit.py`, writes only ignored JSON under an
explicit artifact directory, and constructs AppFrame through public adapters
with temporary stores.

## Change Slice

Primary change class: executable release evidence. Allowed files are the new
runner, this plan, the accessibility/release/parent plan status records, and
`docs/ARCHITECTURE.md` only if the audit-boundary ownership needs recording.
No runtime product behavior, schema, CLI, package payload, or Wayland code is
changed.

## Plan of Work

1. Implement a runner that builds the real AppFrame with temporary stores,
   shows it on X11, records minimum geometry and accessible controls, and
   records top-level menu/action metadata.
2. Verify the production Help QAction directly, then ask the X11 window manager
   to activate only the uniquely titled audit window, focus it with XSetInputFocus,
   and send F1 through XTestFakeKeyEvent. Assert that the production Help viewer
   is created and modeless; never treat the direct QAction trigger as native-input
   evidence.
3. Capture `xrandr --query`, `gsettings` theme/scaling values, and `orca --version`
   as context when available. Keep the values in the ignored report, not in
   product logs.
4. Close the Help dialog and frame, process events, and verify no audit-owned
   process/window/root remains. Run the existing offscreen accessibility test
   separately; its direct QTest failure on X11 must remain documented as an
   injection limitation, not silently converted to pass.
5. Update the accessibility/release/parent plans with the exact result and
   remaining gates, then obtain post-implementation reviews and commit.

## Concrete Steps

Run from `/home/daekar/FoliaSeal` in the supported host X11 session:

    audit_root=$(mktemp -d /tmp/foliaseal-x11-accessibility-XXXXXX)
    DISPLAY=:0 QT_QPA_PLATFORM=xcb .venv/bin/python scripts/live_gui_accessibility_audit.py \
      --artifacts-dir "$audit_root/report" --timeout-seconds 15
    cat "$audit_root/report/audit.json"
    DISPLAY=:0 wmctrl -l | rg -i 'FoliaSeal' || true
    ps -eo pid=,cmd= | rg 'live_gui_accessibility_audit|foliaseal|PySide6' | rg -v 'rg ' || true
    rm -rf "$audit_root"
    test ! -e "$audit_root"

The runner enforces a 15-second deadline, records owned-resource teardown, and
must be executed with display access. Never run it under Wayland or against the
user's configuration directory.

## Validation and Acceptance

Acceptance requires:

- the runner opens the real X11 AppFrame and records the exact minimum geometry,
  accessible Open/Library controls, menu/action metadata, and F1 Help result;
- the F1 result comes from an XTest OS key event after focusing the audit-owned
  window, not a direct QAction trigger;
- monitor/theme/scaling/Orca context is recorded or explicitly unavailable;
- the runner closes all owned windows and leaves no owned process/root;
- the offscreen acceptance test remains unchanged and its X11 direct-QTest
  focus limitation is documented;
- screen-reader speech, high contrast, physical-DPI interpretation, packaged
  GUI, privileged installation, final release matrix, and Wayland remain open.

## Idempotence and Recovery

All stores and artifacts are under a unique temporary root. On failure, the
runner must close its frame/dialogs in `finally` blocks and remove only its own
root. If XTest is unavailable, return a classified environment result rather
than sending direct QAction events or claiming success.

## Artifacts and Notes

Only concise `audit.json` evidence under ignored temporary/artifact paths is
allowed. Do not commit screenshots, PDFs, certificates, logs, or machine-local
absolute paths.

## Interfaces and Dependencies

The runner uses `QtAppFrameAdapter`, `AppSettingsStore`, certificate/profile
stores, Qt public widget/action metadata, and a private audit-only ctypes
adapter for libX11/libXtst. No runtime package dependency is added.

Revision note: 2026-08-16 / Codex: created after the first escalated X11
accessibility attempt showed that direct Qt test injection does not own desktop
focus; this plan separates real OS input evidence from offscreen semantics.

Revision note: 2026-08-16 / Codex: the runner passed after exact WM activation;
recorded source-tree native X11 evidence while retaining human accessibility,
packaged/privileged release, final acceptance, and Wayland gates.
