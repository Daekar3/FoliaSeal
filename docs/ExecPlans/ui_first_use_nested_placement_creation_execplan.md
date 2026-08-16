# Add nested blank-page Placement creation to the Preset editor

This ExecPlan is a living document and must be maintained in accordance with
`/home/daekar/.codex/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

When a first-time user creates a Signature Preset, the Preset editor currently
lets them choose an existing Placement but offers no way to create one without
leaving the suspended Preset draft. This slice adds a `Create placement…`
action to that editor. The existing fixed-page editor opens with an explicit
blank-page seed, saves transactionally, and returns the new Placement to the
same Preset draft with its selector set to the new object. Canceling the editor
leaves both the Preset draft and catalog unchanged; saving the Preset still does
not apply it to the active document.

The result satisfies the Placement portion of UI_SPEC WF03 without adding
document identity to reusable storage, silently placing a signature, or
introducing a second preset-assembly workflow.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md`, `docs/UI_SPEC.md`, and `docs/SCHEMAS.md` are the governing
  contracts. UI_SPEC WF03 explicitly permits blank-page Placement setup.
- [x] `docs/ExecPlans/ui_first_use_preset_setup_execplan.md` provides the
  Presets-first Library and nested Appearance return path.
- [x] `docs/ExecPlans/ui_placement_editor_transaction_execplan.md` provides the
  transactional fixed-page editor and blank-page seed.
- [x] `docs/ExecPlans/ui_partial_preset_missing_input_guidance_execplan.md`
  provides explicit readiness guidance after the optional Placement remains
  absent.

## Progress

- [x] (2026-08-16) Audited UI_SPEC WF03, the Preset editor, Library composition,
  AppFrame placement callback, and existing blank-page editor tests.
- [x] (2026-08-16) Added the Preset editor create action and selector
  refresh/attachment path.
- [x] (2026-08-16) Returned the saved Placement identity through the AppFrame
  callback while
  preserving the existing Library create/edit behavior.
- [x] (2026-08-16) Added focused and real offscreen tests for create, cancel,
  attachment,
  persistence, and unchanged active-document workflow state.
- [x] (2026-08-16) Completed compliance review, documentation, full validation,
  commit, and owned-process/artifact cleanup.

## Surprises & Discoveries

- The existing Preset editor has nested Appearance ownership but only passive
  Placement and Certificate selectors. Evidence: `signature_preset_editor_widget.py`
  builds selectors and no Placement action.
- The AppFrame already creates a blank-page `PlacementEditorState` and persists
  the resulting profile. The original callback returned only `bool`, so this
  slice changed it to return the saved identity needed by the nested editor.
- The Library refresh path is already safe while a nested Preset editor is
  active: it refreshes catalog rows without replacing the mounted editor.

## Decision Log

- Decision: implement blank-page Placement creation first and leave Certificate
  creation/import as a separate child.
  Rationale: blank-page Placement is already a synchronous, secret-free,
  transactionally tested editor; certificate dialogs require a larger secret and
  managed-material lifecycle and should not be mixed into this slice.
  Date/Author: 2026-08-16 / Codex.
- Decision: return the saved `PlacementProfile` from the AppFrame create callback,
  while preserving truthy behavior for the existing Library button.
  Rationale: the nested Preset editor needs the stable id, and the outer Library
  only needs success/failure.
  Date/Author: 2026-08-16 / Codex.
- Decision: use the existing blank-page 612×792-point seed and do not infer the
  active PDF page in this slice.
  Rationale: UI_SPEC explicitly allows blank-page setup, while current-document
  capture needs a separate context-bearing design.
  Date/Author: 2026-08-16 / Codex.

## Outcomes & Retrospective

The nested Preset editor now exposes `Create placement…`. The existing AppFrame
blank-page editor returns the persisted `PlacementProfile`, the selector refreshes
and attaches its stable id, and Preset Save remains explicit. A falsey callback
result models Cancel and leaves the catalog/draft unchanged; non-`PlacementProfile`
results are rejected. Focused Library/frame/placement/offscreen validation is
`97 passed`; the full suite is `1553 passed, 20 skipped, 1 warning`. Ruff,
compileall, and `git diff --check` are clean. Independent review required and this
slice added active-workflow invariance evidence, stronger callback typing, and the
documentation reconciliation. Certificate creation/import was completed by its owning child, and
current-document placement capture was subsequently completed by
`ui_first_use_nested_current_placement_capture_execplan.md`. Display-backed, privileged,
final-release, and deferred Mint 22.3 Wayland gates remain open.

## Context and Orientation

`src/foliaseal/presentation/qt/signature_preset_editor_widget.py` owns the
document-independent Preset draft and its nested Appearance editor. It receives
catalog data from `ReusableObjectLibraryDialog` in
`app_frame_profile_library.py`. `FoliaSealAppFrame._open_placement_profile_editor`
opens `PlacementProfileEditorDialog`, which uses `PlacementEditorSession` and
returns a persisted `PlacementProfile` through a callback. The active signing
workflow is separate; creating or selecting a reusable object in the Library
must not mutate it.

## Plan of Work

1. Extend `SignaturePresetEditorWidgetControls` with a `create_placement_button`
   and add an optional `on_create_placement` callback to the widget. Render the
   button beside the existing Placement selector. On success, rebuild only the
   Placement selector from the current reusable-object snapshot, select the new
   stable id, mark the Preset draft dirty, and notify the existing refresh seam.
2. Pass the Library’s existing `on_create_placement` callback into the Preset
   editor. Change the AppFrame blank-page creation callback to return the saved
   `PlacementProfile | None`; keep edit callbacks and the outer Library behavior
   compatible with truthy success.
3. Add fake-Qt and real offscreen tests proving the action opens the existing
   editor callback, the saved id is attached to the Preset draft, Cancel leaves
   the catalog unchanged, saving the Preset persists the reference, and the
   active signing workflow remains unchanged.
4. Update this plan, the first-use/parent/release status, and
   `docs/ARCHITECTURE.md`. Run focused tests, full Ruff/compileall/pytest,
   independent compliance review, commit, and cleanup. Do not run Wayland.

## Milestones

Milestone 1 adds the callback/control and pure selector refresh behavior with a
fake saved profile. Milestone 2 wires the real AppFrame blank-page editor and
proves persistence through the Library. Milestone 3 completes documentation,
compliance review, full validation, commit, and cleanup.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    .venv/bin/python -m pytest -q tests/unit/test_qt_app_frame_profile_library.py tests/integration/test_signature_library_topology.py tests/integration/test_placement_profile_editor.py
    .venv/bin/python -m ruff check src tests
    .venv/bin/python -m compileall -q src tests
    .venv/bin/python -m pytest -q
    git diff --check

Use `QT_QPA_PLATFORM=offscreen` for deterministic GUI tests. Any live X11
check must use the supported Cinnamon/X11 session and clean its exact
`/tmp/foliaseal-*` roots. Do not run Wayland.

## Validation and Acceptance

Acceptance requires that a user can open Create Preset, click Create placement,
save a blank-page profile, see it selected in the suspended Preset editor, and
save a Preset that references it. Canceling the placement editor must leave no
new profile and no Preset reference. The active document workflow, selected
preset, placement rectangle, and signing request must be unchanged throughout.
Existing Library placement creation/editing, Appearance nesting, and Preset
Save/Cancel behavior must remain green. Blocking certificate/readiness behavior
and certificate creation are outside this child.

## Idempotence and Recovery

The editor is transactional and safe to open repeatedly. If a test fails,
close only windows created by that test, remove only its exact temporary root,
and retry from the recorded Progress entry. Never delete user configuration,
PDFs, credentials, or unrelated `/tmp` entries.

## Artifacts and Notes

No generated artifact belongs in the commit. Record only concise test output and
the final cleanup result. No SVG is needed because the existing Placement editor
topology is reused unchanged.

## Interfaces and Dependencies

The application layer remains Qt-free. The presentation boundary may return a
`PlacementProfile | None` from the AppFrame create callback so the nested editor
can attach its stable `placement_profile_id`. `PlacementProfileEditorDialog`,
`PlacementEditorState.from_blank_page`, and `ReusableSigningObjects.SavePlacement`
remain the sole persistence path. No schema, CLI, signing, certificate-secret,
Wayland, or active-document workflow contracts may change.

Revision note: 2026-08-16 / Codex — created after the post-partial-preset audit
identified first-use nested optional Placement creation/attachment as the next
dependency-ready AFK product gap.
