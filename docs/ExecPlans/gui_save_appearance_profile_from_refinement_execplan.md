# Save an appearance profile from the refinement dialog

This ExecPlan is a living document. Maintain it according to `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, a person refining a PDF's visible signature can press `Save appearance for reuse...`, enter a name, and find that appearance in the persisted signing-profile catalog after reopening the application. This is the first visible creation path for a reusable signing object required by `docs/SPEC.md`.

## Child ExecPlan Dependencies

- [x] The catalog ownership milestone in `gui_reusable_signing_objects_execplan.md` is complete: independent appearance profiles can be stored without a preset.

## Progress

- [x] (2026-07-17 00:00Z) Identified this as the smallest complete visible tracer bullet after an independent code/spec review.
- [x] (2026-07-17 00:00Z) Added coordinator behavior coverage for named persistence, blank-name rejection, duplicate rejection, and preservation of the live workflow state.
- [x] (2026-07-17 00:00Z) Added a Qt refinement-dialog behavior test that saves an edited appearance, keeps the dialog active, and proves cancellation leaves the live draft unchanged.
- [x] (2026-07-17 00:00Z) Implemented `SaveCurrentAppearanceProfile`, the session wrapper, and the mounted refinement-dialog action.
- [x] (2026-07-17 00:00Z) Ran focused regression evidence: `2 passed` for coordinator appearance tests and `1 passed` for the Qt refinement-dialog save/cancel test.
- [ ] Run the live GUI/restart walkthrough after the Settings library exists, because that is the first visible catalog-inspection surface for a persisted appearance profile.

## Surprises & Discoveries

- Observation: storage already provides `SignaturePresetCatalogStore.save_appearance_profile`; the missing seam is application orchestration and a visible action.
  Evidence: `src/foliaseal/infra/config/profile_storage.py` contains the persistent operation, while `SignaturePropertiesPanel.open_refinement_dialog()` mounts only Apply and Cancel.

## Decision Log

- Decision: implement appearance saving alone before placement/preset/library work.
  Rationale: it is independently useful, exercises the complete UI-to-storage path, and avoids inventing preset-reference semantics before the user can create a component profile.
  Date/Author: 2026-07-17 / Codex

## Outcomes & Retrospective

The appearance-profile tracer bullet is complete at the application and Qt boundaries. A user can save an edited appearance by name from the contextual refinement dialog; the save persists only the appearance, keeps the dialog open, and does not alter the current PDF draft until the user explicitly applies it. The remaining reusable-object work is placement saving, explicit preset composition, and the Settings library that will make persisted profiles inspectable after restart.

## Context and Orientation

`VisibleSignatureSetupDraft` is the Qt-independent representation of the appearance and placement currently being edited for one PDF. `DefaultSignaturePropertiesCoordinator` owns current-draft reconciliation and owns the `SignaturePresetCatalogStore`; `SigningSetupSession` is the presentation-facing wrapper around it. `SignaturePropertiesPanel.open_refinement_dialog()` builds the modal Qt dialog using `QtVisibleSignatureSetupForm`.

An Appearance Profile is a named reusable visible-signature look. It deliberately excludes placement and certificates. The profile-store method already persists it, but Qt must not call that store directly: the coordinator must preserve the separation between presentation, application behavior, and infrastructure.

## Plan of Work

First add a `SaveCurrentAppearanceProfile(name, overwrite=False)` command to `signature_properties_coordinator.py`. Reconcile it by reading `workflow.current_signature_appearance`, rejecting blank names and missing appearances with `SignaturePropertiesCoordinatorError`, detecting duplicate names unless overwrite is explicitly allowed, and delegating persistence through `preset_catalog_store.save_appearance_profile`. Refresh `preset_catalog` from the returned catalog without changing the current certificate, placement, selected preset, or workflow appearance. Expose this through `SigningSetupSession.save_appearance_profile`.

Then extend `RefinementDialogState` and `open_refinement_dialog()` in `signing_workspace_properties_panel.py`. Add a visible `Save appearance for reuse...` button before Apply. Its handler must build the form's current draft, ask `QInputDialog.getText` with title `Save appearance profile` and a plain-language label, apply no placement changes, invoke the session method using `draft.appearance`, and show a warning on failure. Because the action saves only reusable appearance data, it must not close the dialog or alter the live PDF draft; the user still chooses Apply or Cancel separately.

Write tests in `tests/unit/test_signature_properties_coordinator.py` and `tests/unit/test_qt_signing_shell.py`. The Qt test uses the existing fake input dialog, opens the refinement dialog with its `on_exec` callback, changes an appearance control, clicks save, and verifies the catalog contains the named appearance while the dialog remains open. Include duplicate-name cancellation/overwrite behavior only if existing message-box conventions can be reused without new hidden behavior.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    .venv/bin/pytest -q tests/unit/test_signature_properties_coordinator.py -k appearance_profile
    .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py -k refinement_dialog_saves_appearance_without_applying_draft
    .venv/bin/pytest -q tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py tests/unit/test_signature_preset_storage.py

Then launch:

    .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf

## Validation and Acceptance

Open a PDF, press `Refine current setup...`, change a visible signature appearance field, press `Save appearance for reuse...`, enter `Contract approval`, and keep the dialog open. Restart the application and verify the saved profile exists in the profile catalog through the next management slice. The focused tests must pass.

## Idempotence and Recovery

Saving a duplicate must never overwrite silently. Canceling the name prompt or closing the refinement dialog must leave the catalog and live draft unchanged. No migration is required because the existing JSON catalog supports appearance profiles.

## Artifacts and Notes

Allowed change class: behavior change, plus focused tests and this plan's progress updates. Do not add placement, preset composition, Settings library, certificate semantics, or unrelated shell cleanup to this commit.

## Interfaces and Dependencies

Add these public application methods:

    DefaultSignaturePropertiesCoordinator.reconcile(SaveCurrentAppearanceProfile(...))
    SigningSetupSession.save_appearance_profile(name, appearance, overwrite=False, ...)

Use `SignaturePresetCatalogStore.save_appearance_profile` as the sole persistence operation. Keep Qt code in `signing_workspace_properties_panel.py`; do not import infrastructure storage into presentation code.

Revision note: 2026-07-17 / Codex
Closed the application/Qt slice with focused coordinator and shell regression evidence. Deferred the restart walkthrough to the Settings-library milestone because the current shell has no catalog-inspection surface for independent appearance profiles.
