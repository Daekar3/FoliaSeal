# Close the keyboard and accessibility acceptance contract

This ExecPlan is a living document and must be maintained in accordance with
`.agents/skills/write-execplan/PLANS.md`. It is an AFK child of
`docs/ExecPlans/ui_product_support_and_release_execplan.md` and
`docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md`.

## Purpose / Big Picture

The governing UI contract requires that a keyboard-only user can reach the primary signing path,
that important controls expose names and state without relying on color or pointer position, and
that the application remains usable at its minimum size. The repository already has most of the
behavior and focused tests, but the release plan names a missing consolidated acceptance test and
does not distinguish headless proof from display-backed evidence. This slice supplies that missing
contract and fixes only concrete accessibility gaps exposed by the test.

After this slice, a checkout can run one real-Qt, offscreen acceptance module that proves the
no-document frame, typed menus, support dialogs, settings transaction, focus names, minimum size,
Unicode settings paths, and keyboard F1 flow. A human can repeat the same checks on a real display
for screen-reader, high-contrast, DPI, and tab-order observations; those observations are recorded
as environment-dependent rather than being falsely claimed by headless tests.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md` and `docs/UI_SPEC.md` are the governing V1 contracts.
- [x] `docs/ExecPlans/ui_help_support_execplan.md` supplies the canonical offline Help viewer and F1 route.
- [x] `docs/ExecPlans/ui_support_surfaces_execplan.md` supplies Help support commands, diagnostics,
  and Settings Restore defaults.
- [x] `docs/ExecPlans/ui_window_theme_responsive_execplan.md` supplies the 1100x700 main-window
  baseline and appearance modes.
- [ ] A real display-backed screen-reader/high-contrast/DPI run; this is an acceptance evidence
  dependency, not a source-code prerequisite.

## Progress

- [x] (2026-08-10) Fresh explorer audit confirmed the named behavior slices are implemented and
  that the missing release-plan artifact is `tests/integration/test_accessibility_acceptance.py`.
- [x] (2026-08-10) Created this bounded acceptance child after confirming the current tree is clean
  and the prior support slice is committed.
- [x] (2026-08-10) Added and passed the red/green real-Qt acceptance test for keyboard, names/roles,
  support surfaces, settings, minimum size, and Unicode path handling.
- [x] (2026-08-10) Fixed the concrete accessibility defects exposed by those tests: explicit
  no-document Open/Library accessible names and unique typed View mnemonics.
- [x] (2026-08-10) Ran the real-Qt acceptance and AppFrame regression checks, full suite, Ruff,
  pip check, diff check, and bounded GUI audit; the focused result is `60 passed` and the full
  suite is `1469 passed, 20 skipped, 1 warning`. The bounded GUI attempt returned `gui_rc=1` at
  the isolated `SingleInstanceUnavailable` endpoint, removed its owned root, and left no matching
  process.
- [x] (2026-08-10) Compliance review found missing top-level menu mnemonics, unasserted shortcut/
  disabled-state metadata, an unexercised diagnostic-folder action, and private test cleanup seams.
  Added unique top-level mnemonics, expanded real-Qt assertions, stubbed the launcher at the Qt
  boundary, and switched Settings/cleanup to public frame APIs; the focused follow-up is `64 passed`.
- [x] (2026-08-10) Reran the full suite and bounded GUI audit after the compliance follow-up. Ruff,
  pip check, and diff checks are clean; the full suite is `1469 passed, 20 skipped, 1 warning`.
  The bounded GUI attempt returned `gui_rc=1` at the isolated `SingleInstanceUnavailable` endpoint,
  removed its owned root, and left no matching process. Display-backed screen-reader,
  high-contrast, physical DPI/monitor, installed-package, and final release evidence remain in the
  owning release plan.
- [ ] Commit the compliance correction and record the display-backed evidence limitation.

## Surprises & Discoveries

- Observation: the release plan names `tests/integration/test_accessibility_acceptance.py`, but the
  file is absent while adjacent no-document and Help tests already exercise the production Qt frame.
  Evidence: `rg --files tests/integration` and `docs/ExecPlans/ui_product_support_and_release_execplan.md`.
- Observation: the current no-document frame already provides minimum size, stable primary buttons,
  typed menu actions, and modeless Help/support dialogs; the acceptance gap is consolidated proof,
  not a reason to add placeholder controls.
  Evidence: `tests/integration/test_gui_launch_no_document.py`, `tests/integration/test_help_viewer.py`,
  `src/foliaseal/presentation/qt/app_frame.py`, and `src/foliaseal/presentation/qt/support_dialogs.py`.
- Observation: an offscreen Qt process still cannot prove physical screen-reader, high-contrast,
  or multi-monitor behavior. Evidence must label those as display-backed observations and keep the
  bounded offscreen test separate.
- Observation: the first acceptance pass checked action mnemonics but not top-level menu mnemonics,
  shortcut strings, disabled state, or the diagnostic-folder action. Evidence: the compliance review
  compared `tests/integration/test_accessibility_acceptance.py` with UI_SPEC sections 7 and 13.
- Observation: invoking the real `QDesktopServices.openUrl` can block under the offscreen platform.
  Evidence: the diagnostic-folder acceptance timed out at `QPlatformServices::openDocument`; the
  follow-up stubs that Qt boundary while still asserting FoliaSeal creates the owned log directory.

## Decision Log

- Decision: add one acceptance module rather than duplicating every existing feature test.
  Rationale: the release gate needs a single discoverable contract while feature ownership remains
  in the existing child plans.
  Date/Author: 2026-08-10 / Codex.
- Decision: use real PySide6 widgets with `QT_QPA_PLATFORM=offscreen` for deterministic names,
  action metadata, dialog modality, and keyboard dispatch; do not treat fake bindings as proof of
  Qt accessibility behavior.
  Rationale: fake bindings verify routing, but only real Qt exposes the widget/action properties
  that assistive technology consumes.
  Date/Author: 2026-08-10 / Codex.
- Decision: test Unicode through settings storage and visible Data Locations text, not by placing
  private document contents into logs.
  Rationale: UI_SPEC requires broad Unicode user data while explicitly forbidding sensitive log data.
  Date/Author: 2026-08-10 / Codex.
- Decision: keep screen-reader, high-contrast, physical DPI, and two-monitor evidence as a manual
  display-backed gate; never mark it green from an offscreen return code.
  Rationale: the local bounded launch can stop at `SingleInstanceUnavailable` before a window is
  created, and offscreen Qt cannot represent a real assistive-technology environment.
  Date/Author: 2026-08-10 / Codex.
- Decision: assign unique top-level menu mnemonics as `&File`, `&Edit`, `&View`, `S&igning`,
  `Se&ttings`, and `&Help`, while preserving each menu's stable command metadata.
  Rationale: UI_SPEC requires unique Alt-menu entry even though Signing and Settings share an initial
  letter; these letters are unique and preserve the visible menu words.
  Date/Author: 2026-08-10 / Codex.
- Decision: keep the acceptance test on public frame methods and typed command snapshots; use a
  temporary stub only at the `QDesktopServices.openUrl` boundary and never reach into `_bindings` or
  `_support_dialogs` for behavior or cleanup.
  Rationale: the test verifies the production contract rather than private object layout, while the
  external desktop service is explicitly an environment boundary.
  Date/Author: 2026-08-10 / Codex.

## Outcomes & Retrospective

The bounded slice is implemented. The real-Qt offscreen acceptance verifies 1100x700 minimum
geometry, no-document Open/Library names, typed File/Edit/View/Signing/Settings/Help action order,
tooltips, shortcuts, disabled state, and unique mnemonics (including the corrected View entries),
F1 Help, modeless support dialogs, Settings Restore defaults, and Unicode XDG path display. The
production corrections are explicit accessible names for the no-document buttons, distinct
mnemonics for `Fit Page`, `Find`, and `Document Signatures`, and unique top-level menu accelerators.
The compliance follow-up also asserts shortcuts, disabled state, and diagnostic-folder routing while
keeping tests on public frame APIs. Focused acceptance plus AppFrame regression validation is now
`64 passed`; the full suite is `1469 passed, 20 skipped, 1 warning`. A display-backed screen-reader/high-contrast/DPI/monitor run,
installed-package checks, and the final release matrix remain outstanding and must not be inferred
from offscreen success.

## Context and Orientation

`src/foliaseal/presentation/qt/app_frame.py` constructs the real `QMainWindow`, typed menu actions,
the no-document placeholder, Settings dialog, Help viewer, and support dialogs. The typed metadata
is in `src/foliaseal/presentation/qt/app_frame_command_model.py`. `support_dialogs.py` owns modeless
Keyboard Shortcuts, Data Locations, and About surfaces. `tests/integration/test_gui_launch_no_document.py`
and `tests/integration/test_help_viewer.py` are the nearest real-Qt acceptance examples. PySide6 is
optional at import time, so tests must use `pytest.importorskip("PySide6")` and clean every created
window before returning.

“Accessibility acceptance” here means observable keyboard reachability, truthful enabled/checked
state, descriptive names/tooltips, readable status text, and minimum geometry. It does not mean a
headless test can certify a screen reader or physical monitor setup.

## Change Slice

Primary change class: acceptance behavior/tests plus the minimum source correction needed for a
failing concrete accessibility assertion. Allowed files are the new integration test, a focused Qt
source module if required, this child plan, the parent/release/architecture status docs, and no
generated package or private fixture. Do not add V2 features, broad menu redesign, or phase3 naming
cleanup unrelated to the acceptance findings.

## Plan of Work

Create `tests/integration/test_accessibility_acceptance.py` using a real `QApplication` and the
production `QtAppFrameAdapter`. Build the frame with temporary config/data/state roots and show it
offscreen. Assert the 1100x700 minimum, the two no-document primary buttons and their accessible
names, unique top-level menu mnemonics, all required command IDs/tooltips/shortcuts, and disabled
state for document-only commands. Trigger F1 with `QTest.keyClick`, assert the modeless Help viewer
is focused and searchable, then close it.

Exercise each support command from the Help menu. Assert Keyboard Shortcuts, Data Locations, and
About have descriptive titles, read-only content, accessible names, a keyboard-reachable Close
button, and non-modal behavior. Set XDG paths containing Unicode characters and assert Data
Locations displays those paths. Open Settings, assert Restore defaults is named and focusable,
change a draft, restore, cancel, and prove the persisted settings did not change.

If a test reveals a missing accessible name, state, or cleanup hook, make the smallest correction in
the owning Qt module and add the assertion to the acceptance test. Do not paper over a missing
behavior with a test-only property or direct private-widget reach-through.

After tests pass, run the complete suite and static checks. Attempt the bounded GUI launch with an
owned temporary XDG root, inspect for `SingleInstanceUnavailable`/Qt errors, close any created
dialogs, remove only that root, and verify no FoliaSeal/PySide6/pytest process remains. Update
`docs/ARCHITECTURE.md` with the acceptance boundary and update the parent/release plans so completed
children are checked consistently while display-backed accessibility, package installation, and
remaining final-release evidence remain explicitly open.

## Milestones

### Milestone 1: real-Qt acceptance contract

Add the red integration test and make it pass against the current production frame. The result is a
single command that verifies names, menu state, Help F1, support dialogs, Settings Restore defaults,
minimum geometry, and Unicode paths without needing a display server.

### Milestone 2: compliance correction and evidence

Resolve any concrete failures, run focused and full validation, perform the bounded GUI attempt,
and record cleanup and the known display-backed limitation. The result is a restartable handoff
that distinguishes proven headless behavior from evidence that still requires human interaction.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q tests/integration/test_accessibility_acceptance.py
    .venv/bin/ruff check src tests
    .venv/bin/python -m pip check
    .venv/bin/pytest -q
    git diff --check

For the bounded display-independent application attempt, use an owned root and always clean it:

    audit_root=$(mktemp -d /tmp/foliaseal-accessibility-XXXXXX)
    set +e
    timeout --foreground 30s env QT_QPA_PLATFORM=offscreen \
      XDG_CONFIG_HOME="$audit_root/config" XDG_DATA_HOME="$audit_root/data" \
      XDG_STATE_HOME="$audit_root/state" .venv/bin/python -m foliaseal gui \
      >"$audit_root/gui.log" 2>&1
    rc=$?
    set -e
    printf 'gui_rc=%s\\n' "$rc"
    rg -n 'SingleInstanceUnavailable|xcb|Error|RuntimeError' "$audit_root/gui.log" || true
    ps -eo pid=,cmd= | rg 'FoliaSeal|foliaseal|PySide6|pytest' | rg -v 'rg ' || true
    rm -rf "$audit_root"
    test ! -e "$audit_root"

Expected focused output is one passing real-Qt acceptance test (or a skip only when PySide6 is not
installed); the full suite must remain green. A bounded launch may return nonzero at the isolated
single-instance endpoint, but it must leave no process or temporary root.

## Validation and Acceptance

The slice is accepted when the new integration module passes with real PySide6 and demonstrates:

- minimum main-frame geometry and no-document Open/Library keyboard entry;
- unique, discoverable File/Edit/View/Signing/Settings/Help menu actions with correct shortcuts,
  names, and truthful disabled state;
- F1 opens the modeless offline Help viewer and the viewer exposes named search/content/Close controls;
- all four added support surfaces open modelessly, expose readable named content, and close cleanly;
- Settings Restore defaults is named, keyboard-reachable, and Cancel leaves persisted settings intact;
- a Unicode XDG path is visible in Data Locations without leaking it to diagnostic logs.

Real display-backed screen-reader, high-contrast, DPI/monitor, package installation, and the final
ten-scenario matrix remain open until performed in their appropriate environment; this plan must not
claim those gates from offscreen tests.

## Idempotence and Recovery

Tests use `tmp_path` or a temporary XDG root and close every frame/dialog in `finally` blocks. If a
Qt test fails, terminate only processes started by the test, remove its owned temporary directory,
and rerun. Never delete a user configuration directory, repository artifact, or unrelated process.

## Artifacts and Notes

Do not commit screenshots, packages, private keys, PDFs, logs, or machine-local absolute paths. Keep
any retained GUI transcript under ignored `artifacts/` or `/tmp`; record only concise command output
and the exact known environment limitation in this plan.

## Interfaces and Dependencies

Use `QtAppFrameAdapter.create_frame`, `AppSettingsStore`, `SupportLocations`, the typed command
definitions, and existing support dialog objects. The acceptance test may inspect public properties,
Qt `QAction` metadata, `QWidget.accessibleName()`, `QDialog.isModal()`, `QPushButton`, `QLineEdit`,
`QTextBrowser`, and `QTest`; it must not depend on private child names except for the already-tested
typed command map. No network, PDF content, credential, or secret-store access is required.

Revision note: 2026-08-10 / Codex
Created after a fresh current-checkout audit found the release plan's named accessibility test
missing while the underlying Help/support/settings and command behavior was already implemented.

Revision note: 2026-08-10 / Codex
Updated after the real-Qt acceptance pass to record the explicit accessible-name and unique-mnemonic
corrections, `60` focused passes, full-suite result, bounded GUI cleanup, and remaining display-backed
and package evidence gates.

Revision note: 2026-08-10 / Codex
Updated after compliance review to add top-level menu mnemonics, shortcut/disabled-state assertions,
diagnostic-folder routing coverage, and public-API-only test cleanup; the follow-up focused set is
`64 passed` and requires a fresh full-suite validation before commit.
