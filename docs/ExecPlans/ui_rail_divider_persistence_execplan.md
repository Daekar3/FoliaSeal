# Remembered signing-rail divider

This ExecPlan is a living document and must be maintained in accordance with
`.agents/skills/write-execplan/PLANS.md`. It is an AFK child of
`docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md` and follows the completed
main-window geometry work in `docs/ExecPlans/ui_window_theme_responsive_execplan.md`.

## Purpose / Big Picture

After this slice, a user can drag the boundary between the PDF canvas and the signing rail to
choose a comfortable rail width. FoliaSeal remembers that width in the existing per-user UI
settings and restores it the next time a signing workspace is opened, while keeping the existing
approximately 320 logical-pixel default. The canvas and rail remain separate layout regions; the
rail's properties content continues to scroll independently rather than collapsing or becoming
inaccessible. A real offscreen Qt test will prove the splitter, width change, persistence, and
scroll-area ownership without claiming display-backed acceptance.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md` and `docs/UI_SPEC.md` are the governing product contracts.
- [x] `docs/ExecPlans/ui_window_theme_responsive_execplan.md` owns the existing typed app-settings
  and frame shutdown persistence seam.
- [x] `docs/ExecPlans/ui_signing_rail_stage_status_execplan.md` owns the sidebar's protected status
  region; this slice must not move interactive controls into that region.

## Progress

- [x] (2026-08-10) Add the typed divider-width setting, safe defaults, clamping, and unknown-key
  preserving serialization tests.
- [x] (2026-08-10) Replace the workspace canvas/rail HBox boundary with a public binding-backed
  splitter and restore the remembered width.
- [x] (2026-08-10) Capture the live divider width through the workspace view lifecycle before
  frame settings are atomically persisted.
- [x] (2026-08-10) Add a real offscreen integration test for splitter geometry, width movement,
  store save/reload/rebuild, and independently scrollable viewer/properties regions.
- [x] (2026-08-10) Reconcile architecture, parent/child plan status, run focused validation,
  and address the compliance review findings.
- [x] (2026-08-10) Run the final full-suite/package-health checks, clean processes and temporary
  roots, and commit the complete slice.

## Surprises & Discoveries

- Observation: the production composition currently uses a plain `QHBoxLayout` and the sidebar
  hard-codes `RAIL_WIDTH = 320`.
  Evidence: `src/foliaseal/presentation/qt/signing_workspace_composition.py` and
  `src/foliaseal/presentation/qt/signing_workspace_sidebar.py` inspected on 2026-08-10.
- Observation: `QtAppFrameBindings` already exposes `QSplitter`, but the narrower
  `QtSigningWidgetBindings` does not.
  Evidence: `app_frame.py` has `q_splitter`; `signing_shell.py` binding construction did not.
- Observation: frame shutdown already captures `AppSettings` after `app.exec()` returns, so the
  divider can be captured through the existing public workspace-view lifecycle without adding a
  second store or a schema-version migration.
  Evidence: `FoliaSealAppFrame.capture_window_geometry()` and
  `QtAppFrameAdapter.launch()` call the existing capture/save hooks.
- Observation: the existing unit fixture bindings omit `QSplitter`, so a narrow HBox fallback is
  still needed for those isolated tests while production bindings always provide the real Qt
  splitter.
  Evidence: `tests/unit/test_qt_signing_shell.py` supplies a fake binding object without a
  splitter; `SigningShellAdapter._load_bindings()` now loads `QSplitter` in production.
- Observation: capturing settings alone did not prove serialized persistence; the acceptance test
  now saves through `AppSettingsStore`, reloads the JSON mapping, and only then rebuilds the shell.
  Evidence: `tests/integration/test_rail_divider_persistence.py` exercises save/reload and retains
  the unknown `future_preference` key.
- Observation: the real app-frame teardown exposed a stale recovery-cleanup reach-through in the
  shell; cleanup now uses the installed `SigningWorkspaceActionBridge` directly.
  Evidence: the frame-level integration test closes the active workspace without a dialog and
  completes cleanly after `FoliaSealAppFrame.capture_window_geometry()` persists the divider.

## Decision Log

- Decision: persist one JSON-safe integer `rail_width` in `AppUiSettings`, with a 320-pixel
  default and safe lower/upper clamping at projection and splitter-restore boundaries.
  Rationale: UI_SPEC requires a remembered adjustable divider, while malformed or extreme user
  settings must not make the canvas or rail unusable. The field belongs beside the existing typed
  UI preferences and must preserve unknown keys.
  Date/Author: 2026-08-10 / Codex
- Decision: use `QSplitter` only at the canvas/rail boundary; retain the sidebar's existing
  properties `QScrollArea` and protected status-region geometry unchanged.
  Rationale: the splitter is a shell composition concern, while sidebar internals already own
  their independent scrolling and status contract.
  Date/Author: 2026-08-10 / Codex
- Decision: expose divider capture through `WorkspaceViewPort.capture_ui_settings(settings)`
  rather than letting `FoliaSealAppFrame` inspect child widgets.
  Rationale: the frame should remain Qt-topology agnostic and the view lifecycle is the existing
  public boundary for workspace-owned presentation state.
  Date/Author: 2026-08-10 / Codex
- Decision: retain the HBox path only as a compatibility fallback for incomplete fake binding
  objects, with removal conditioned on migrating those fixtures to a splitter binding.
  Rationale: the production path is unconditionally splitter-backed, while removing the fallback
  in this slice would mix a broad test-fixture migration into the user-visible behavior change.
  Date/Author: 2026-08-10 / Codex

## Outcomes & Retrospective

The typed settings, production splitter, public capture seam, and offscreen persistence/rebuild
evidence are complete. Focused validation is green and the compliance review found only the
documentation/evidence issues that this revision corrected. The final full suite and package-health
gate are green, all owned temporary roots/processes are clean, and the complete slice is committed.
Signing behavior, sidebar status semantics, and document persistence policy were unchanged.

## Context and Orientation

FoliaSeal is a Python/PySide6 Linux PDF signing application. `AppSettings` in
`src/foliaseal/infra/config/schemas.py` stores an extensible `ui` mapping; the typed
`AppUiSettings` projection in `src/foliaseal/infra/config/app_settings_ui.py` validates known UI
preferences and merges them back without dropping unknown keys. `AppSettingsStore` writes that
mapping atomically.

`SigningWorkspaceComposition` in
`src/foliaseal/presentation/qt/signing_workspace_composition.py` assembles a viewer column and
`SigningWorkspaceSidebar` into the mounted workspace. `QtSigningWidgetBindings` in
`signing_shell.py` is the injected set of Qt classes used by that composition. A `WorkspaceViewPort`
in `signing_shell_port.py` intentionally hides child widgets from the app frame. The app frame's
shutdown path captures settings after the Qt event loop and then calls `AppSettingsStore`.

## Change Slice

Primary change class: behavior change. Allowed files are the typed UI settings projection, the
Qt binding/composition/view lifecycle seams, focused unit/integration tests, and the minimum
architecture/ExecPlan status updates. Do not mix Library geometry, monitor/DPI rendering, toolbar
overflow, document reopening, signing-state changes, packaging, or phase3 nomenclature migration.
Generated PDFs, private keys, screenshots, and machine-local paths are forbidden in the commit.

## Plan of Work

First add an immutable `rail_width` field to `AppUiSettings`. Define constants for the default and
safe minimum/maximum, project malformed/non-integer values to the default, clamp valid values, and
serialize the field while preserving unknown `ui` keys. Add red tests for absent, malformed,
undersized, oversized, round-tripped, and unknown-key cases.

Next add `q_splitter` to `QtSigningWidgetBindings` and load `QSplitter` from PySide6. In the
composition, create a horizontal splitter containing the existing viewer-column container and
sidebar container, set its child stretch so the canvas receives remaining space, and set the
sidebar width from the typed settings after the workspace has a usable size. Store the splitter in
the composition as the sole public capture handle; do not reach into private sidebar children.

Add a small typed capture method on the composition/shell/view adapter that reads the splitter's
current second-pane width, clamps it, and returns an `AppSettings` value with the updated
`AppUiSettings`. Extend `WorkspaceViewPort` with this method and have `FoliaSealAppFrame` combine
it with its existing geometry capture before `persist_captured_window_geometry()`. Rebuilding a
workspace from the saved settings must restore the same safe width.

Finally add an offscreen integration test that constructs the real production shell with a
temporary `AppSettingsStore`, asserts a `QSplitter` separates the viewer and rail, observes the
320-pixel default, moves the divider and captures settings, rebuilds the shell, and observes the
remembered width. Assert that the viewer widget remains a scrollable canvas and the sidebar's
properties region remains a `QScrollArea`; also cover clamping and disposal. Update the parent
plan, the window-theme child, and `docs/ARCHITECTURE.md` to make this ownership and evidence
truthful.

## Milestones

Milestone 1 proves typed settings and safe projection with red/green unit tests. Milestone 2
proves the real Qt composition uses an adjustable splitter and retains both scroll regions.
Milestone 3 proves capture, atomic persistence, and rebuild restoration through the public frame
view lifecycle. Milestone 4 records focused/full validation, cleanup, and documentation evidence.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    .venv/bin/pytest -q tests/unit/test_config_schemas.py tests/unit/test_app_settings_storage.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_signing_workspace_composition.py tests/integration/test_app_frame_geometry_persistence.py tests/integration/test_signing_rail_layout.py
    QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q tests/integration/test_rail_divider_persistence.py
    .venv/bin/ruff check src tests
    QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q
    git diff --check

Use an isolated temporary configuration root for any launch or persistence walkthrough. After each
run, inspect `ps` for FoliaSeal/PySide6/pytest processes, terminate only processes owned by the
test if necessary, remove the exact temporary root, and assert it no longer exists. Do not leave
dialogs, windows, or `/tmp/foliaseal-*` roots behind.

## Validation and Acceptance

Acceptance is behavioral. A fresh or malformed setting produces a usable 320-pixel rail. A user
can move the visible canvas/rail divider; the rail width changes while the viewer remains the
flexible pane. Capturing, saving through `AppSettingsStore`, reloading settings, and rebuilding the
workspace restores that width.
The viewer and properties panes remain independently scrollable, the protected status region and
interactive action ownership remain unchanged, and unknown UI settings survive the save. Focused
tests must be red before implementation and green afterward; the full suite, Ruff, and diff check
must pass. This offscreen evidence does not close the separate display-backed GUI, package-manager,
or monitor/DPI acceptance gates.

## Evidence Record

Record the exact UI_SPEC requirement (`SUR02` and section 12 persistence), focused test node/result,
default and moved widths, serialized `ui.rail_width`, rebuilt width, scroll-area assertions,
offscreen evidence path if any, cleanup/process result, and the production-binding proof that the
splitter path is used. The narrow HBox fallback is documented as a fake-binding compatibility seam,
not claimed to be gone. Record the contributing topology artifact
`docs/ui/main-workspace-document-open-exploratory.svg`; no screenshot is required for this
offscreen-only slice.

## Idempotence and Recovery

All settings tests use temporary stores and are safe to repeat. If a Qt build fails, dispose the
composition before retrying and remove only the test's temporary configuration root. Preserve
unrelated worktree changes. Do not alter existing user configuration or delete the ignored Debian
package. A partial implementation must be recorded in Progress before stopping.

## Artifacts and Notes

Only source, tests, and governing-document updates belong in the commit. Local JSON, screenshots,
PDFs, and logs may be written under ignored `artifacts/` or a temporary root for evidence, but
must be removed unless the relevant acceptance plan explicitly requires them.

## Interfaces and Dependencies

The final typed interfaces are `AppUiSettings.rail_width`, the `QtSigningWidgetBindings.q_splitter`
binding, a composition-owned splitter capture method, and
`WorkspaceViewPort.capture_ui_settings(AppSettings) -> AppSettings`. The app frame remains the
owner of window-level persistence and atomic save; the workspace view remains the owner of Qt
layout state. PySide6 `QSplitter`, `QScrollArea`, and existing viewer/sidebar widgets are the only
new runtime dependencies.

## Evidence and Retrospective

The exact focused command listed above passed `164 passed` with `QT_QPA_PLATFORM=offscreen`, and
the dedicated real integration file passed `2 passed`, including the frame-level capture/save
path. The final full suite passed `1487 passed, 20 skipped, 1 warning`, with Ruff, `pip check`, and
`git diff --check` clean. The compliance review rerun passed `212 passed` before the final
store-save and frame-lifecycle assertions were added. The real integration nodes
`tests/integration/test_rail_divider_persistence.py::test_real_qt_signing_rail_divider_moves_and_round_trips`
and `::test_real_qt_app_frame_captures_and_persists_workspace_divider` prove the 320px default,
movement to a larger width, production frame capture/persist, `AppSettingsStore` save/reload,
unknown-key preservation, rebuild restoration, independent `QScrollArea` ownership, and clean
composition teardown. No FoliaSeal, PySide6, or pytest process remained, and all `/tmp/foliaseal-*`
temporary roots were removed.

Revision note: 2026-08-10 / Codex
Created after explorer audit identified the remaining UI_SPEC SUR02 remembered-divider gap.
Revision note: 2026-08-10 / Codex
Marked implementation milestones complete, added store save/reload evidence, documented the
test-binding HBox fallback, and reconciled architecture/parent references after compliance review.
Revision note: 2026-08-10 / Codex
Closed the implementation, validation, cleanup, and commit gates after the full regression passed.
