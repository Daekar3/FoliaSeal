# Remembered Signature Library geometry and columns

This ExecPlan is a living document and must be maintained in accordance with
`.agents/skills/write-execplan/PLANS.md`. It is an AFK child of
`docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md` and follows the completed
`ui_rail_divider_persistence_execplan.md` settings slice.

## Purpose / Big Picture

After this slice, a user can resize or reposition the modeless Signature Library and adjust its
three columns to suit their workflow. FoliaSeal remembers the Library dialog rectangle and the
three-column splitter widths in the existing per-user UI settings, restores them before showing
the Library again, and keeps the existing catalog and sort preferences unchanged. A real offscreen
Qt test will move the dialog and splitter, save and reload settings, reopen the Library, and verify
the visible geometry and column widths.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md` and `docs/UI_SPEC.md` are the governing product contracts.
- [x] `docs/ExecPlans/ui_window_theme_responsive_execplan.md` established typed UI settings and
  frame capture/persistence around the Qt event loop.
- [x] `docs/ExecPlans/ui_signature_library_topology_execplan.md` established the modeless
  three-column Library and its public controls surface.

## Progress

- [ ] (2026-08-10) Add typed, malformed-safe Library geometry and three-column splitter settings
  that preserve unknown UI keys.
- [ ] (2026-08-10) Expose a narrow dialog layout capture/restore seam and apply saved layout before
  the modeless Library is shown.
- [ ] (2026-08-10) Capture Library layout through `FoliaSealAppFrame` settings persistence without
  reopening the Library automatically.
- [ ] (2026-08-10) Add unit, offscreen topology, and frame persistence evidence; reconcile docs,
  run full validation, clean temporary roots/processes, and commit.

## Surprises & Discoveries

- Observation: the Library already creates one horizontal `QSplitter` with navigation, master list,
  and detail columns, but no splitter or dialog geometry is retained.
  Evidence: `ReusableObjectLibraryDialog._build_controls()` in
  `src/foliaseal/presentation/qt/app_frame_profile_library.py` inspected on 2026-08-10.
- Observation: the AppFrame keeps one Library object after it is closed and reuses it on the next
  open, so capture can safely read the public dialog surface without creating a second persistence
  store or reopening the Library at startup.
  Evidence: `FoliaSealAppFrame.show_reusable_object_library()` and
  `self._reusable_object_library` lifecycle in `app_frame.py`.

## Decision Log

- Decision: persist `LibraryGeometry` separately from `MainWindowGeometry`, with a 900x600 minimum
  and a nullable value so a fresh installation does not open the Library automatically.
  Rationale: UI_SPEC requires remembered Library geometry but explicitly forbids reopening dialogs
  automatically; the Library has a smaller independent window contract.
  Date/Author: 2026-08-10 / Codex
- Decision: persist exactly three integer `library_splitter_sizes` values, normalized to safe
  positive column widths, rather than Qt's opaque `saveState()` byte array.
  Rationale: JSON-safe typed values are inspectable, resilient across Qt versions, and match the
  existing `AppSettings.ui` contract; the three values correspond to navigation, master list, and
  detail columns.
  Date/Author: 2026-08-10 / Codex
- Decision: expose capture and restore on `ReusableObjectLibraryDialog` and let the AppFrame combine
  that projection with its existing window capture. The frame must not inspect private child
  widgets, and settings capture must never cause a hidden dialog to be shown.
  Rationale: the dialog owns Qt layout state while the frame owns atomic persistence.
  Date/Author: 2026-08-10 / Codex

## Outcomes & Retrospective

This section will be completed after implementation and validation. The intended outcome is
remembered Library geometry and column widths with no change to catalog/sort semantics, nested
editor behavior, or automatic startup behavior.

## Context and Orientation

FoliaSeal is a Python/PySide6 Linux PDF signing application. `AppSettings` stores an extensible
`ui` mapping, and `AppUiSettings` in `src/foliaseal/infra/config/app_settings_ui.py` projects known
preferences while preserving unknown keys. `AppSettingsStore` writes settings atomically.

`ReusableObjectLibraryDialog` in
`src/foliaseal/presentation/qt/app_frame_profile_library.py` owns the modeless Signature Library
dialog. It creates a horizontal `QSplitter` containing catalog navigation, the saved-object master
list, and the detail/editor column. `FoliaSealAppFrame.show_reusable_object_library()` constructs
or reuses the dialog, and `capture_window_geometry()` is the existing shutdown capture boundary.
The AppFrame must continue to own persistence and must not reopen dialogs, documents, or drafts on
startup.

## Change Slice

Primary change class: behavior change. Allowed files are the typed UI settings projection, the
Library dialog and AppFrame capture/restore seams, focused unit/integration tests, and the minimum
architecture/ExecPlan status updates. Do not mix monitor/DPI support, toolbar persistence,
certificate lifecycle, nested editor redesign, signing behavior, package work, or phase3
nomenclature migration. Generated PDFs, private keys, screenshots, and machine-local paths are
forbidden in the commit.

## Plan of Work

Add `LibraryGeometry` with JSON-safe x/y/width/height/maximized fields and a 900x600 minimum. Add
`library_geometry: LibraryGeometry | None` and `library_splitter_sizes: tuple[int, int, int]` to
`AppUiSettings`; malformed values fall back to no geometry and default positive column sizes, while
valid values clamp safely and serialize only when non-default or already present. Update every
existing `AppUiSettings(...)` reconstruction in `app_frame.py` so these fields cannot be lost when
appearance, Library preferences, rail width, or main-window geometry changes.

Extend `ReusableObjectLibraryControls` with its splitter. The dialog constructor receives the typed
initial geometry and sizes, applies them before `show()`, and exposes `capture_ui_settings(settings)`
that reads the dialog rectangle and splitter sizes through public Qt methods. The capture method
returns a new `AppSettings` projection and leaves hidden/closed state untouched. The AppFrame passes
saved values when creating the dialog and calls the dialog capture method before its existing
window-geometry capture; its atomic save path then persists both. Reusing the hidden dialog must
restore the latest captured state without changing catalog/sort behavior.

Add unit tests for absent, malformed, undersized, oversized, round-tripped, and unknown-key-safe
Library settings. Extend `tests/integration/test_signature_library_topology.py` with a real
offscreen test that moves the dialog and splitter, invokes AppFrame capture/save, reloads the store,
and opens a new frame to prove geometry and all three sizes return before the dialog is shown.
Preserve the existing modeless and nested-editor tests and close every dialog in `finally` blocks.

## Milestones

Milestone 1 proves the typed settings projection and safe fallback behavior. Milestone 2 proves
dialog restore/capture through the narrow Library surface. Milestone 3 proves AppFrame atomic
save/reload and offscreen reopen geometry/columns. Milestone 4 reconciles architecture and plan
status, runs the full suite, and cleans all owned resources.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    .venv/bin/pytest -q tests/unit/test_config_schemas.py tests/unit/test_app_settings_storage.py tests/unit/test_qt_app_frame.py tests/integration/test_signature_library_topology.py
    .venv/bin/ruff check src tests
    .venv/bin/python -m pip check
    QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q
    git diff --check

After every Qt test, inspect for FoliaSeal/PySide6/pytest processes and remove only explicit
`/tmp/foliaseal-*` temporary roots created by the run. Assert that no matching root remains. Never
leave the modeless Library dialog open and never delete the ignored Debian package.

## Validation and Acceptance

Acceptance is behavioral: absent or malformed settings create the existing default Library window;
valid saved geometry and three splitter widths are applied before the dialog becomes visible; moving
the dialog or any splitter handle changes the captured values; AppSettingsStore save/reload retains
them and unknown UI keys; reopening the Library in a new frame restores the values; and the dialog
remains modeless without being opened automatically at startup. Existing catalog selection, sort,
nested editor, and close behavior must remain green. Focused tests, the full suite, Ruff, pip check,
and diff checks must pass.

## Evidence Record

Record the exact UI_SPEC section 12 requirement and SUR03 topology, focused test node/results,
initial/moved/restored geometry, all three serialized splitter sizes, unknown-key preservation,
modeless visibility timing, cleanup/process result, and the topology artifact
`docs/ui/signature-library-presets-exploratory.svg`.

## Idempotence and Recovery

Use temporary AppSettingsStore directories for persistence tests. If a dialog or frame fails during
construction, close it and remove only the test's temporary root before retrying. Preserve unrelated
worktree changes. Re-running the tests must not mutate user configuration or reopen a dialog.

## Artifacts and Notes

Only source, tests, and governing-document updates belong in the commit. Local JSON, logs, or
screenshots may be written under ignored `artifacts/` or temporary roots for evidence and must be
removed unless a governing acceptance plan explicitly requires them.

## Interfaces and Dependencies

The final typed interfaces are `AppUiSettings.library_geometry`,
`AppUiSettings.library_splitter_sizes`, `ReusableObjectLibraryDialog.capture_ui_settings(AppSettings)`,
and the dialog's public restore inputs. The AppFrame remains the owner of atomic persistence and
startup policy; the Library dialog remains the owner of Qt geometry/splitter state. PySide6
`QDialog`, `QSplitter`, and existing controls are the only runtime dependencies.

Revision note: 2026-08-10 / Codex
Created after explorer audit identified the remaining UI_SPEC Signature Library geometry/column
persistence gap.
