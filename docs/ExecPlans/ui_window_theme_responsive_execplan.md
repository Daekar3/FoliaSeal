# Window geometry, theme, and responsive baseline

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this bounded follow-up, a user can close and relaunch FoliaSeal and recover the main window's
last valid position, size, and maximized state without reopening a document or dialog. This slice
implements only the main-frame geometry portion of UI_SPEC section 12 and acceptance scenario 9.
Rail-divider persistence is now implemented by the dedicated
`ui_rail_divider_persistence_execplan.md` child; Library, DPI/monitor, and toolbar persistence
remain explicit follow-up work. The
slice is one vertical path through typed settings, the frame lifecycle, focused tests, and
observable offscreen acceptance, not a generic refactor.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are the frozen governing contracts.
- [x] docs/ExecPlans/ui_launch_no_document_execplan.md

## Progress

- [x] (2026-08-09) Audit the current implementation and write failing focused tests for the typed appearance/minimum-size baseline.
- [x] (2026-08-09) Implement the smallest complete typed settings and Qt frame baseline.
- [x] (2026-08-09) Audit the missing close-event persistence seam and define a main-frame-only geometry/restart correction.
- [x] (2026-08-09) Add validated JSON geometry projection and restore/capture lifecycle hooks around the Qt event loop.
- [x] (2026-08-09) Review migrated compatibility and phase3 product cruft; no retirement condition in the named geometry/settings seams was met, so no unrelated removal was mixed into this slice.
- [x] (2026-08-09) Run focused, regression, and offscreen Qt validation; record evidence and clean up.
- [x] (2026-08-09) Updated relevant architecture/status documentation and this plan; the bounded
  implementation and validation are complete, with final acceptance owned by the release tranche.

## Surprises & Discoveries

- Observation: window settings and geometry persistence are currently owned by the frame/settings
  boundary, so responsive and restart behavior must be tested there instead of in child widgets.
  Evidence: the live source paths and focused tests listed below are the audit baseline.
- Observation: the current frame has no close-event or shutdown persistence seam, so this loop can
  safely implement only typed appearance mode and minimum-size initialization; geometry restore,
  monitor clamping, Library sizing, and rail persistence need later lifecycle slices.
  Evidence: `QtAppFrameAdapter.launch()` retains the frame locally and calls `exec()` without a
  frame shutdown hook; `FoliaSealAppFrame` previously set only its title before this slice.
- Observation: `AppSettings.ui` already preserves unknown keys and `AppSettingsStore.save_settings`
  already performs atomic replacement, so geometry can be added without a schema-version bump or a
  second persistence store.
  Evidence: `app_settings_ui.py`, `schemas.py`, and `app_settings_storage.py` inspected on
  2026-08-09.

## Decision Log

- Decision: honor SPEC.md product scope, SCHEMAS.md persistent-object semantics, and UI_SPEC.md interaction wording in that order.
  Rationale: the repository explicitly defines those authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep this change limited to one observable window geometry, theme, and responsive baseline outcome.
  Rationale: narrow commits make GUI regressions and recovery auditable.
  Date/Author: 2026-08-09 / Codex
- Decision: Loop 3 is bounded to typed `appearance_mode` (`system`, `light`, `dark`), safe invalid
  fallback to `system`, and the main-frame 1100x700 minimum with UI-chrome palette application.
  Rationale: these behaviors have existing frame/settings seams and can be proven offscreen without
  inventing a premature geometry persistence lifecycle.
  Date/Author: 2026-08-09 / Codex
- Decision: persist only explicit JSON-safe main-window `x`, `y`, `width`, `height`, and `maximized`
  values. Restore them before showing the frame, clamp position to the available screen when Qt
  exposes one, enforce the existing 1100x700 minimum, and capture/save after `app.exec()` returns.
  Do not persist documents, drafts, dialogs, Library state, rail width, or monitor-specific DPI
  data in this geometry-only slice; rail width is owned by the dedicated divider child.
  Rationale: this completes the missing lifecycle seam while keeping the serialized contract stable
  across Qt versions and leaving the larger responsive topology to its owning plans.
  Date/Author: 2026-08-09 / Codex

## Outcomes & Retrospective

The baseline slice is implemented and this follow-up is now scoped to main-frame geometry/restart.
After completion, a valid saved rectangle and maximized flag round-trip through `AppSettings`,
restore before the frame is shown, and capture after the event loop exits. Missing, malformed, or
undersized geometry falls back to the 1100x700 baseline while unknown UI keys survive. Monitor
clamping, Library minimums/columns, DPI rerender, and toolbar overflow remain explicitly deferred
to later lifecycle and responsive slices. The remembered rail divider is tracked and validated in
`ui_rail_divider_persistence_execplan.md`.

## Context and Orientation

The relevant code is app_frame.py; app settings schemas/storage; Qt geometry/palette setup; settings tests. FoliaSeal is a Python/Qt Linux PDF signing application. The
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

Own the canonical AppSettings UI projection for `MainWindowGeometry` and keep the existing
appearance mode and unknown-key merge behavior. Validate integer `x`, `y`, `width`, `height`, and
boolean `maximized`; reject malformed or undersized records to the normal baseline. In
`FoliaSealAppFrame`, restore geometry before `show()`, clamp the position to the available screen
when possible, and expose a capture method that updates the current settings. In
`QtAppFrameAdapter.launch()`, call capture and atomically save after `app.exec()` returns while
allowing shutdown to complete if saving fails. Do not persist document, draft, dialog, Library,
rail, DPI, or toolbar state in this slice. Preserve the public frame/workspace contract and keep
user-facing terminology from UI_SPEC.md, not schema/backend names.

## Milestones

Milestone 1 adds the typed geometry projection and malformed/undersized fallback tests. Milestone 2
wires restore-before-show and capture-after-event-loop through the frame/adapter seams. Milestone 3
proves an offscreen save/relaunch round trip and records the deferred responsive surfaces.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e 'setMinimumSize|appearance_mode|AppSettings|geometry|theme' src/foliaseal/presentation/qt/app_frame.py src/foliaseal/infra/config
    .venv/bin/pytest -q tests/unit/test_config_schemas.py tests/unit/test_app_settings_storage.py tests/unit/test_qt_app_frame.py tests/integration/test_app_frame_geometry_persistence.py
    .venv/bin/ruff check src tests
    .venv/bin/pytest -q
    git diff --check

Run this bounded walkthrough from /home/daekar/FoliaSeal with an isolated configuration root:

    audit_root=$(mktemp -d /tmp/foliaseal-plan-audit-XXXXXX)
    timeout --foreground 30s env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf || test "$?" -eq 124
    ps -eo pid,cmd | rg 'FoliaSeal|foliaseal|PySide6|pytest' | rg -v 'rg ' || true
    rm -rf "$audit_root"
    test ! -e "$audit_root"

Expected evidence is the stated user-visible behavior plus a mandatory Qt-test or display-backed
walkthrough. Record geometry input, restore-before-show ordering, captured settings, observed frame
state, maximized-state round trip, evidence path, and cleanup result; the bounded timeout is only a
lifecycle check.

The real offscreen integration test recreated a frame after saving a rectangle and maximized flag;
the focused geometry/settings/frame pass completed with `87 passed`, and the full suite completed
with `1185 passed, 20 skipped, 1 warning`. The bounded CLI audit again exited with
`GUI_RC=1` because this environment cannot claim the Qt local single-instance endpoint; no FoliaSeal
process remained and the temporary audit root was removed (`AUDIT_ROOT_CLEAN=1`).

## Validation and Acceptance

Acceptance for this bounded follow-up is behavioral: a valid main-window rectangle and maximized flag
round-trip through settings; malformed, undersized, or absent geometry falls back to the 1100x700
baseline; restore happens before the frame is shown; capture happens after normal event-loop return
and also in the controlled exception cleanup path; and unknown UI keys remain intact. Position is
clamped when an available Qt screen is exposed, while full multi-monitor resizing remains deferred.
The existing typed System/Light/Dark and UI-chrome palette behavior must remain green. Library,
monitor/DPI, and toolbar persistence remain open to later slices; the rail-divider follow-up has
its own focused evidence record. Focused tests, the full suite, and offscreen Qt evidence must pass
with clean teardown.

## Evidence Record

Before checking this child in the parent, record the governing UI_SPEC requirement, exact focused
test command/result, geometry input and observed restore/capture/maximized state, evidence path,
cleanup result, serialized settings result, and compatibility grep proof. This bounded evidence
explicitly does not claim Library, full monitor/DPI, or toolbar persistence; rail-divider evidence
is recorded by `ui_rail_divider_persistence_execplan.md`.

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
reach-through. `AppUiSettings.main_window_geometry` is the typed persistence projection;
`FoliaSealAppFrame.restore_window_geometry()` and `capture_window_geometry()` own the frame-level
conversion; `QtAppFrameAdapter.launch()` owns event-loop ordering and atomic save. Create
`tests/unit/test_qt_app_frame_responsive.py` for offscreen frame seams and
`tests/integration/test_app_frame_geometry_persistence.py` for the settings/relaunch path. The
final interface must be exercised by those files plus the existing settings/storage and frame tests.
workspace surface. Any compatibility adapter retained temporarily must have a named consumer and a
retirement condition recorded in this plan.

Revision note: 2026-08-09 / Codex
Created as child ui_window_theme_responsive_execplan.md of the approved SPEC/UI_SPEC compliance breakdown.
Revision note: 2026-08-09 / Codex
Added and validated the main-window geometry/maximized persistence vertical slice, including typed
fallbacks, lifecycle ordering, offscreen recreation evidence, and explicit monitor/responsive
deferrals.
Revision note: 2026-08-09 / Codex
Narrowed the child to main-window geometry/maximized persistence after the explorer audit identified
the missing restore/capture lifecycle; rail, Library, monitor/DPI, and toolbar behavior remain
explicitly deferred.
