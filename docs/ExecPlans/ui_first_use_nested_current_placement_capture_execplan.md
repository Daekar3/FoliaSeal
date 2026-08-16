# First-use nested current-document Placement capture

## Purpose / Big Picture

Complete the remaining first-use Preset workflow required by `docs/SPEC.md` and
`docs/UI_SPEC.md`: while a PDF is open, the suspended nested Preset editor must offer an explicit
`Capture placement from current PDF…` action. The action seeds the existing transactional Placement
editor from the active page context and current signature rectangle when one exists, returns a
persisted reusable `PlacementProfile`, and attaches only its stable ID to the suspended Preset
draft. Saving the Preset remains explicit and must not apply the Preset or mutate the active
signing document.

The existing blank-page `Create placement…` path remains available for no-document/blank-page
setup. This slice adds the typed read seam and current-document callback only; it does not redesign
Placement persistence, pointer editing, or active-document placement behavior.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md`, `docs/UI_SPEC.md`, and `docs/SCHEMAS.md` are governing contracts.
- [x] `docs/ExecPlans/ui_first_use_preset_setup_execplan.md` provides the Presets-first Library and
  suspended Preset path.
- [x] `docs/ExecPlans/ui_first_use_nested_placement_creation_execplan.md` provides blank-page
  Placement creation and selector attachment.
- [x] `docs/ExecPlans/ui_placement_editor_transaction_execplan.md` provides
  `PlacementEditorState.from_current_page()` and transactional persistence.
- [x] `docs/ExecPlans/ui_first_use_nested_certificate_creation_import_execplan.md` provides the
  completed nested reusable-object pattern.

## Progress

- [x] (2026-08-16) Explorer audit confirmed the application layer already converts active page
  context and an existing current-page rectangle without retaining document identity.
- [x] (2026-08-16) Add typed `current_placement_context()` and `signature_rect()` read methods to the public
  workspace session seam and Qt adapter.
- [x] (2026-08-16) Add a separate nested Preset capture callback/action and thread it through the Library.
- [x] (2026-08-16) Add AppFrame current-workspace capture wiring with explicit no-document behavior.
- [x] (2026-08-16) Add focused fake-Qt, boundary, and real offscreen integration coverage.
- [x] (2026-08-16) Complete independent review and documentation reconciliation. The review found
  retained-Library callback staleness; AppFrame now keeps the callback available before a PDF is
  open and reports the error at invocation. Focused validation passed `123` tests; full validation
  passed `1565 passed, 20 skipped, 1 warning`; Ruff, compileall, and `git diff --check` are clean.
- [x] (2026-08-16) Cleaned exact `/tmp/foliaseal-*` roots and verified no FoliaSeal, Qt, pytest, or
  live-audit process remained. The bounded implementation is ready for its focused commit.

## Surprises & Discoveries

- `PlacementEditorState.from_current_page()` already handles visible page dimensions, rotation, and
  PDF-to-visible top-left conversion. It uses the existing rectangle only when it belongs to the
  current page; otherwise it creates a centered default rectangle.
- `SigningWorkspaceRuntime` already owns both `signature_rect()` and the viewer interaction
  session's `current_placement_context()`, but the typed `SigningWorkspaceSessionPort` does not
  expose them. AppFrame must use that public seam rather than reaching through private widgets.
- A current-document capture with no active workspace must return `None` and report an explicit
  error; the blank-page action remains usable without an open document.
- Wayland acceptance is deliberately deferred because Mint 22.3 treats Wayland as experimental.

## Decision Log

- Preserve two explicit actions: `Create placement…` for blank-page setup and `Capture placement
  from current PDF…` for document-context setup.
- Return the saved `PlacementProfile` through the callback, then attach only its stable ID to the
  suspended Preset. Do not save PDF paths, document identity, or secrets.
- Reuse the existing `PlacementEditorState.from_current_page(context, signature_rect=...)` and
  `_run_placement_profile_editor()` boundaries; no schema/storage changes are needed.
- When a current page has no completed rectangle, the existing state factory's centered default is
  acceptable; the user still explicitly saves the reusable object.
- Keep active document mutation out of scope. Creating the reusable object may refresh catalogs but
  must preserve the active workflow snapshot.

## Outcomes & Retrospective

The nested Preset editor now exposes `Capture placement from current PDF…` alongside the existing
blank-page `Create placement…` action. The typed workspace seam supplies current visible-page
context and the current signature rectangle; AppFrame seeds the existing transactional editor via
`PlacementEditorState.from_current_page()`, and the suspended Preset attaches only the saved
`placement_profile_id` after a successful return. Cancellation, invalid results, no-document
capture, current-page rotation/rectangle conversion, and active-draft invariance are covered by
focused tests and a real offscreen Library → Preset → Capture → Save integration path. Focused
validation passed `123` tests. Wayland is deferred for Mint 22.3; human display/accessibility,
packaged/privileged installation, and final-release gates remain external.

## Context and Orientation

`SignaturePresetEditorWidget` owns the suspended Preset draft. `ReusableObjectLibraryDialog` mounts
it and already threads blank-page Placement and certificate callbacks. `FoliaSealAppFrame` owns the
active `SigningWorkspaceHost`, the typed `SigningWorkspaceSessionPort`, and the existing
`PlacementProfileEditorDialog` runner. `SigningWorkspaceRuntime` exposes the underlying current
rectangle and viewer context; `PlacementEditorState.from_current_page()` converts those facts to
reusable visible-page geometry.

## Scope

### In scope

- Typed workspace session read methods for current placement context and rectangle.
- Separate nested capture action/callback and provider wiring.
- AppFrame active-workspace callback and explicit no-document failure.
- Focused unit, boundary, offscreen integration, and active-workflow invariance tests.
- Architecture, first-use, parent, and release-plan status reconciliation.

### Out of scope

- Changes to `PlacementProfile` schema, persistence, pointer interaction, or numeric editor rules.
- Blank-page creation behavior (already complete).
- Automatic placement, automatic Preset selection, or signing.
- Wayland execution/acceptance, human accessibility/DPI/monitor validation, packaged installation,
  privileged host changes, or final release acceptance.

## Plan of Work

1. Add `current_placement_context() -> SignaturePlacementContext | None` and
   `signature_rect() -> SignatureRect | None` to `SigningWorkspaceSessionPort`, its Qt adapter,
   and the shell/runtime delegation seam.
2. Add `on_capture_placement` and a public Capture control to the nested Preset widget. Suspend
   parent controls while the callback runs; reject invalid results; refresh/select the returned
   stable ID; mark only the Preset draft dirty.
3. Thread the callback through `ReusableObjectLibraryDialog`. In AppFrame, resolve the active
   workspace, seed `PlacementEditorState.from_current_page`, and invoke the existing editor runner.
4. Add focused tests for conversion/seam behavior, no-document cancellation, capture attachment,
   parent save, and active-workflow invariance. Add a real offscreen Library → Preset → capture →
   save integration test.
5. Run independent compliance review, correct findings, update docs, run full validation, commit,
   and clean all owned processes and temporary roots.

## Milestones

- **M1 — Public context seam:** session/runtime expose typed read-only context and rectangle facts.
- **M2 — Nested capture:** explicit action returns and attaches a saved Placement without applying it.
- **M3 — Evidence:** fake/offscreen tests prove current page/rotation conversion, cancel/no-document,
  persistence, and active-draft invariance.
- **M4 — Closeout:** review, docs, full suite, and cleanup complete; focused commit is in progress.

## Concrete Steps

- Update `src/foliaseal/presentation/qt/signing_shell_port.py`,
  `src/foliaseal/presentation/qt/signing_shell.py`, and
  `src/foliaseal/presentation/qt/signing_workspace_runtime.py` with the typed read seam.
- Update `src/foliaseal/presentation/qt/signature_preset_editor_widget.py`,
  `src/foliaseal/presentation/qt/app_frame_profile_library.py`, and
  `src/foliaseal/presentation/qt/app_frame.py` with capture action and callback wiring.
- Extend `tests/unit/test_placement_editor.py`,
  `tests/unit/test_qt_signing_workspace_runtime.py`,
  `tests/unit/test_qt_app_frame_profile_library.py`,
  `tests/unit/test_qt_app_frame.py`, and
  `tests/integration/test_signature_library_topology.py`.
- Update `docs/ARCHITECTURE.md`, `docs/ExecPlans/ui_first_use_preset_setup_execplan.md`,
  `docs/ExecPlans/ui_product_support_and_release_execplan.md`, and
  `docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md`.

## Validation and Acceptance

- `PlacementEditorState.from_current_page()` tests prove page number, rotation, visible dimensions,
  and current-rectangle conversion with no document identity persistence.
- Typed session boundary tests prove context/rectangle delegation and no-document `None` behavior.
- Nested fake-Qt tests prove Capture action, stable-ID attachment, cancel/invalid result behavior,
  and parent preservation.
- Real offscreen integration proves Library → Preset → Capture → Save and active-workflow
  invariance.
- Ruff, compileall, `git diff --check`, and the full pytest suite pass with exact results recorded.
- Working tree is clean; no FoliaSeal/Qt/pytest/audit process or `foliaseal-*` temporary root
  remains.

## Idempotence and Recovery

Capture is a reusable-object write independent of the parent Preset save. Cancel/failure leaves the
Preset draft unchanged. If the user saves a captured Placement and later cancels the Preset, the
Placement remains reusable, matching existing catalog behavior. Tests use isolated roots; cleanup
targets only exact FoliaSeal-owned prefixes.

## Artifacts and Notes

Do not store source PDF paths or generated documents in reusable Placement records. Record exact
test results and any review corrections here; do not claim display-backed or Wayland acceptance.

Focused closeout evidence (2026-08-16): `123 passed`. Full suite evidence: `1565 passed, 20
skipped, 1 warning in 56.86s`. No display-backed or Wayland acceptance is inferred. Mint 22.3
Wayland execution remains deliberately deferred; human accessibility/DPI/monitor, privileged host
installation, and final release gates remain open.

## Interfaces and Dependencies

- `SignaturePlacementContext` and `SignatureRect` are read-only facts crossing the workspace seam.
- `PlacementEditorState.from_current_page()` is the sole context-to-reusable-geometry conversion.
- `PlacementProfile.placement_profile_id` is the only value attached to the Preset.
- Existing `on_reusable_objects_changed` remains notification-only and must not apply placement.

## Revision Notes

- 2026-08-16: Created after explorer audit of the remaining current-document capture gap. Wayland,
  packaging, and human acceptance explicitly deferred.
- 2026-08-16: Closed implementation, independent review, documentation reconciliation, focused and
  full validation, and owned-process cleanup. Review correction retained the capture callback in a
  no-document modeless Library; commit is the final mechanical closeout step.
