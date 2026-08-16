# Protect placed signatures from material reusable-object changes

This ExecPlan is a living document and must be maintained in accordance with
`docs/ExecPlans/PLANS.md` (repository guidance is in `/home/daekar/.codex/skills/write-execplan/PLANS.md`).
It is an AFK child of `docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md`.

## Purpose / Big Picture

When a user has placed a signature and edits or deletes the reusable Appearance, Placement, or
Preset that supplies that signature, FoliaSeal must not silently leave a stale placed signature in
the draft. After this slice, the Library mutation path detects material changes, asks the
consequence-labeled question `Remove the placed signature and continue?`, defaults to safe Cancel,
and removes the placement only after explicit confirmation. Rename, pinning, duplicate, and
unrelated catalog changes must not prompt. The active document remains unchanged when the user
cancels.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md`, `docs/UI_SPEC.md`, and `docs/SCHEMAS.md` are governing contracts.
- [x] `docs/ExecPlans/ui_first_use_preset_setup_execplan.md` provides the modeless Library and
  nested editor mutation path.
- [x] `docs/ExecPlans/ui_first_use_nested_current_placement_capture_execplan.md` provides the
  current workspace placement read seam and is committed.
- [x] `docs/ExecPlans/ui_pointer_signature_placement_execplan.md` and
  `docs/ExecPlans/ui_keyboard_numeric_placement_execplan.md` provide the removable placement
  action and history behavior.

## Progress

- [x] (2026-08-16) Audited UI_SPEC WF06 and confirmed the active invalidation requirement is not
  implemented; Library refresh currently has no mutation identity or material-change signal.
- [x] (2026-08-16) Added a typed reusable-object mutation event that identifies the changed stable reference,
  operation, and whether persisted content materially changed.
- [x] (2026-08-16) Exposed selected preset/appearance/placement IDs through the typed workspace session seam.
- [x] (2026-08-16) Added AppFrame dependency detection and the cancel-default removal confirmation;
  cancellation rejects the catalog mutation before persistence, while confirmation removes the
  placement before allowing the reusable-object write.
- [x] (2026-08-16) Added focused application and Qt coverage, including the real offscreen
  Library/workspace mutation path and safe deletion-cancellation handling.
- [x] (2026-08-16) Independent second-pass review completed; it required real offscreen wiring,
  explicit default-button assertions, complete mutation classification coverage, silent delete
  cancellation, and stale-documentation corrections. All corrections are now applied.
- [x] (2026-08-16) Documentation reconciled in `docs/ARCHITECTURE.md` and the parent UI ExecPlan;
  active invalidation is now recorded as implemented while display/HITL/release gates remain
  external.
- [x] (2026-08-16) Full validation, commit, and cleanup completed; exact evidence is recorded
  below.

## Surprises & Discoveries

- Observation: `ReusableSigningObjects.execute()` already has the before/after catalogs needed to
  classify a mutation, but currently publishes only a snapshot and the Library callback has no
  stable-reference context.
  Evidence: `src/foliaseal/application/reusable_signing_objects.py` computes `catalog` and `updated`
  in one method, while `ReusableObjectLibraryDialog._notify_reusable_objects_changed()` accepts no
  arguments.
- Observation: the active draft stores selected stable IDs and the current rectangle in
  `SigningDraftWorkflow`, but the public Qt session adapter exposes neither selected reusable ID.
  Evidence: `src/foliaseal/application/signing_draft_workflow.py` fields
  `selected_*_profile_id`; `SigningWorkspaceSessionPort` currently exposes only `signature_rect()`.
- Observation: the fake QMessageBox used by unit tests supports the three-argument question call,
  so the prompt must use the existing `_question_with_buttons()` fallback and retain Cancel as the
  default without requiring a real display.

## Decision Log

- Decision: publish mutation metadata from the reusable-object application service rather than
  infer it from display names in the Qt Library.
  Rationale: stable IDs and before/after content comparisons belong at the persistence/application
  boundary; display names are mutable and cannot safely identify dependencies.
  Date/Author: 2026-08-16 / Codex.
- Decision: classify only Appearance content, Placement geometry/page/source metadata, Preset
  component references, and deletion as material. Rename, pinning, and duplication are nonmaterial.
  Rationale: UI_SPEC explicitly exempts rename/pinning/unrelated edits from invalidation and the
  user should not lose a valid placement for a cosmetic catalog operation.
  Date/Author: 2026-08-16 / Codex.
- Decision: keep the prompt at the AppFrame boundary and remove through the typed session port.
  Rationale: the AppFrame owns the modeless Library and consequence dialogs; the runtime already
  owns placement-history clearing and overlay synchronization.
  Date/Author: 2026-08-16 / Codex.
- Decision: do not run Wayland acceptance. Mint 22.3 treats it as experimental and it is not a
  prerequisite for this AFK behavior slice.
  Date/Author: 2026-08-16 / Codex.

## Outcomes & Retrospective

This section will record the implementation, review corrections, exact validation, documentation
updates, commit, cleanup, and any remaining external gates.

Implementation result: the reusable-object application boundary now emits typed mutation facts and
can reject a material mutation before persistence. AppFrame matches stable reusable IDs against the
active placed draft, shows the exact consequence prompt with safe Cancel default, and removes the
placement only after Yes. The nested Library editors preserve Cancel without catalog or placement
changes; deletion cancellation is silent. Rename, pin, duplicate, and unselected-object changes do
not invalidate a placed signature.

Review corrections: the independent review required a real offscreen AppFrame/Library/workspace
scenario, five-argument QMessageBox default-button coverage, Placement/Preset/Delete/Duplicate and
unselected-object classification cases, silent rejected Delete handling, and architecture/plan
wording reconciliation. Those changes are included in the final implementation.

Validation evidence (2026-08-16):

- Focused reusable-object/AppFrame/Library/runtime/offscreen topology tests: `145 passed`.
- Full suite: `.venv/bin/python -m pytest -q` — `1574 passed, 20 skipped, 1 warning`.
- `.venv/bin/ruff check src tests` — passed.
- `.venv/bin/python -m compileall -q src tests` — passed.
- `git diff --check` — passed.
- Cleanup audit found no FoliaSeal-owned process or temporary root; Wayland was not run.

Commit: `aabd86eef feat: protect placed signatures from reusable changes`.

## Context and Orientation

`ReusableSigningObjects` in `src/foliaseal/application/reusable_signing_objects.py` is the typed
application boundary over the persisted Signature Preset catalog. It receives commands such as
`SaveAppearance`, `SavePlacement`, `SavePreset`, `RenameObject`, `DuplicateObject`, `SetPinned`, and
`DeleteObject`, then atomically saves a new catalog snapshot. `ReusableObjectLibraryDialog` in
`src/foliaseal/presentation/qt/app_frame_profile_library.py` owns the modeless three-column Library
and nested editors. `FoliaSealAppFrame` owns the active workspace and all consequence dialogs.
`SigningDraftWorkflow` stores selected reusable IDs and the ephemeral `signature_rect`; the typed
`SigningWorkspaceSessionPort` is the only AppFrame-facing route to remove that rectangle.

The active dependency rule is: prompt only when a workspace has a completed placed signature and
the mutation's stable reference matches the selected reusable object. A canceled prompt rejects the
catalog mutation before persistence, preserving both the catalog and current placement; a confirmed
prompt removes the placement immediately and lets existing placement history/overlay synchronization
run.

## Scope

In scope are mutation metadata, typed selected-ID reads, AppFrame prompt/removal behavior, focused
tests, offscreen integration coverage, and status documentation. Out of scope are schema changes,
automatic preset selection, silent removal, redesign of the Library, display-backed screen-reader
or DPI acceptance, privileged package installation, final release acceptance, and Wayland.

## Plan of Work

First add `ReusableObjectMutation` and an optional mutation callback to
`ReusableSigningObjects`. Derive the affected `ReusableObjectRef` from command IDs or the prior
name, compare before/after persisted content, and publish only after the repository save and
snapshot update. Keep existing callers valid when no callback is supplied.

Next add read-only selected-ID methods to `SigningWorkspaceSessionPort`,
`QtSigningWorkspaceSessionPort`, `SigningWorkspaceWidget`, and `SigningWorkspaceRuntime`. They
must return the workflow's selected preset, appearance, and placement IDs without mutating state;
legacy/fake shell adapters should return `None` when the optional method is absent.

Then inject an AppFrame mutation callback. If the active session has a signature rectangle and the
mutation is material and matches one of the selected IDs, ask through the existing QMessageBox
button helper. The title should identify FoliaSeal, the text must be exactly
`Remove the placed signature and continue?`, and Cancel must be the default. On Yes, call the typed
`remove_signature_placement()` seam; on Cancel, do nothing. Nonmaterial mutations and mutations for
unselected objects must never open the prompt.

Finally add service tests for material classification, session-port delegation tests, AppFrame fake
tests for Yes/Cancel and no-match behavior, and a real offscreen integration test that places a
signature, edits the selected Appearance through the Library, observes the prompt, and proves the
selected result. Preserve existing nested editor and active-draft invariance tests.

## Milestones

### M1 — Typed mutation fact

The application service publishes one stable-reference mutation event after a successful save.
Unit tests distinguish material content changes from rename/pin/duplicate operations.

### M2 — Typed workspace dependency reads

The AppFrame can read selected reusable IDs and the current rectangle through the public session
port, with no private widget access. Runtime and adapter tests prove read-only behavior.

### M3 — Safe user-visible invalidation

Editing or deleting a selected reusable component while a signature is placed shows the exact
Cancel-default question. Yes removes the placement; Cancel preserves it. Unrelated mutations do
not prompt.

### M4 — Closeout

Independent review, focused/offscreen validation, full suite, architecture/ExecPlan updates,
commit, and cleanup are complete. Wayland remains explicitly deferred.

## Concrete Steps

Work from `/home/daekar/FoliaSeal` with the repository virtual environment.

    .venv/bin/python -m pytest -q tests/unit/test_reusable_signing_objects.py tests/unit/test_qt_app_frame.py tests/unit/test_qt_signing_workspace_runtime.py tests/integration/test_signature_library_topology.py
    .venv/bin/ruff check src tests
    .venv/bin/python -m pytest -q
    .venv/bin/python -m compileall -q src tests
    git diff --check

After Qt tests or any GUI audit, remove only exact FoliaSeal-owned temporary roots and verify no
owned process remains:

    find /tmp -maxdepth 1 -mindepth 1 -name 'foliaseal-*' -exec rm -rf -- {} +
    ps -eo pid=,comm=,args= | awk '$2 ~ /^(foliaseal|FoliaSeal|PySide6|pytest|live_gui)$/ {print}'

## Validation and Acceptance

The application service tests must prove stable references and material comparisons. The fake Qt
tests must prove exact prompt text, Cancel default/fallback behavior, confirmed removal, no prompt
for rename/pin/unselected mutations, and no-document/no-placement no-op behavior. The offscreen
integration must exercise Library mutation against an active workspace and show the placement
removed only after confirmation. Full Ruff, compileall, diff, and pytest validation must pass with
exact counts recorded here. No claim may include Wayland or human display acceptance.

## Idempotence and Recovery

Mutation events are notifications after an already committed catalog write; retrying a failed
notification must not repeat persistence. Prompt Cancel is lossless for the active draft. If a test
fails after a dialog is opened, close the dialog, remove exact `/tmp/foliaseal-*` roots, and verify
the owned-process audit before retrying. Do not delete broad temporary directories.

## Artifacts and Notes

Do not commit PDFs, certificates, screenshots, passwords, or generated package artifacts. Record
only concise test output and cleanup evidence. Update `docs/ARCHITECTURE.md`, the UI parent plan,
`ui_product_support_and_release_execplan.md`, and the reusable-object child plan with the final
status and remaining external gates.

## Interfaces and Dependencies

The event interface is application-owned and Qt-free. The session methods are typed read-only
delegations. AppFrame remains the sole owner of the QMessageBox consequence prompt and calls only
`SigningWorkspaceSessionPort.remove_signature_placement()` to change the draft. Existing
`PlacementHistory` and overlay synchronization remain authoritative for removal behavior.

## Revision Notes

- 2026-08-16: Created after the active UI_SPEC WF06 audit found that reusable-object mutation
  invalidation was still a genuine AFK gap. Wayland and external acceptance were explicitly
  excluded.
