# GUI reusable signing objects recovery

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this change, a user will be able to refine a signing setup in document context and then save that work as reusable named objects instead of losing it as one-off current-document state. A novice will be able to create an appearance profile, create a placement profile, create a signature preset that composes them, and later re-select those saved objects from the main shell. This is the core missing product behavior blocking the audited GUI from matching `docs/SPEC.md`.

The user-visible proof is simple. Launch the GUI, open a PDF, create or select a certificate configuration, open the refinement dialog, change the visible signature appearance and placement, save that work into reusable objects, close the dialog, and then select the saved preset from the main shell. The preview and placement state should reload from the saved objects without depending on hidden controls or test-only paths.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/gui_save_appearance_profile_from_refinement_execplan.md` is complete at the application and Qt boundaries; placement-profile, preset-composition, and management-library work may now proceed.

## Progress

- [x] (2026-07-13 00:00Z) Confirmed through `.tmp/gui_user_flow_audit_2026-07-13.md` that the current GUI has no visible path to save a new reusable signature preset.
- [x] (2026-07-13 00:00Z) Confirmed through `.tmp/gui_findings_and_fix_plan_2026-07-13.md` that appearance-profile and placement-profile user-facing management is also missing.
- [x] (2026-07-17 00:00Z) Reconciled the plan with the live checkout: main-shell preset save/delete controls are mounted, but independent appearance/placement management and the required dedicated library are absent.
- [x] (2026-07-17 00:00Z) Defined the GUI boundary: live-PDF edits stay in the refinement dialog; the main shell is quick preset selection; Settings opens the reusable-signing-object library.
- [x] (2026-07-17 00:00Z) Completed the catalog ownership milestone: profiles can be persisted independently, preset deletion retains profiles, and deleting a referenced profile is rejected.
- [x] (2026-07-17 00:00Z) Ran `pytest -q tests/unit/test_signature_preset_storage.py`; 6 tests passed.
- [x] (2026-07-17 00:00Z) Completed the appearance-profile save tracer bullet with coordinator and Qt dialog regression coverage; the remaining restart walkthrough is deferred until the Settings library can inspect independent profiles.
- [x] (2026-07-18) Implemented visible refinement-dialog saves and explicit reference-only preset composition; composition selects saved component profiles instead of creating replacements from the current PDF draft.
- [x] (2026-07-18) Added `Settings > Manage signing profiles...` for inspection, rename, and reference-guarded deletion of appearance profiles, placement profiles, and presets; mounted-shell refresh follows catalog changes.
- [x] (2026-07-18) Added focused application, storage, frame, and shell coverage; the integrated focused suite passed (163 tests).
- [ ] Run the exact representative-PDF GUI audit. This remains pending: this execution environment has no display-backed audit evidence.
- [x] (2026-07-18) Reconciled `docs/ARCHITECTURE.md` with the completed code paths.

## Surprises & Discoveries

- Observation: the earlier audit is stale about preset controls: save/delete controls are mounted in the main shell, but they implicitly create and later garbage-collect their component profiles.
  Evidence: `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py` mounts `Save preset` and `Delete preset`; `src/foliaseal/infra/config/schemas.py` implements `remove_preset()` by removing component profiles no longer referenced by a preset.

- Observation: certificate configuration management already has a dedicated dialog pattern that can guide the reusable-object work.
  Evidence: `src/foliaseal/presentation/qt/app_frame_certificate_management.py` already owns dialog construction, execution, refresh, and save/delete flows for one reusable object family.

## Decision Log

- Decision: keep live-document editing contextual and add explicit “save for reuse” actions rather than restoring the old always-open inline editor.
  Rationale: `docs/SPEC.md` says appearance and placement editing should remain contextual, and the current refinement dialog already provides that context without polluting the main shell.
  Date/Author: 2026-07-13 / Codex

- Decision: treat appearance profile, placement profile, and signature preset as visibly distinct objects in the GUI.
  Rationale: the spec defines them as separate reusable named objects. Hiding that separation would perpetuate the current confusion.
  Date/Author: 2026-07-13 / Codex

- Decision: preserve independently saved appearance and placement profiles when a signature preset is deleted, and make preset save compose references to those independently managed objects.
  Rationale: deleting a preset must not silently delete reusable objects the user deliberately saved. Stable IDs and explicit catalog upsert/remove operations are necessary before the library can safely manage reuse.
  Date/Author: 2026-07-17 / Codex

- Decision: expose full reusable-object management from Settings, while adding only save-for-reuse actions to the contextual refinement dialog.
  Rationale: this directly satisfies the SPEC distinction between contextual document editing and a dedicated reusable-object library, without returning legacy configuration controls to the main shell.
  Date/Author: 2026-07-17 / Codex

## Outcomes & Retrospective

Implementation and focused automated validation are complete. The catalog now has a
single reference-only composition path, and the Settings library exposes management
without allowing a referenced component profile to be deleted. The manual GUI audit
is deliberately not claimed: no display-backed evidence was captured in this run.

The catalog now honors independent reusable-object ownership: deleting a signature preset no longer destroys its appearance and placement profiles. The remaining work is intentionally separated at the application and Qt boundaries so that the visible library does not reach into JSON storage directly.

## Context and Orientation

The current main shell is built in `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py`. It shows a `Signature preset` combo box, a `Certificate configuration` combo box, a preview card, and a `Manual refinement` button that opens a modal refinement dialog. The refinement dialog is built with `src/foliaseal/presentation/qt/visible_signature_setup_form.py`, which exposes current-document appearance and placement controls.

Below Qt, reusable signing setup state is reconciled by `src/foliaseal/application/signature_properties_coordinator.py` and `src/foliaseal/application/signing_setup_session.py`. Persisted signing objects live in the profile schema and storage modules under `src/foliaseal/infra/config/`, especially `profile_storage.py` and `schemas.py`. Those modules already understand appearance profiles, placement profiles, and signature presets as separate concepts, even though the GUI does not currently expose them well.

In ordinary English: an appearance profile is the reusable look of the visible signature. A placement profile is the reusable size and position template. A signature preset is the reusable named combination of those objects, and may also reference a certificate configuration. Today, the user can edit the current-document setup but cannot visibly save or manage those reusable objects through the GUI.

## Plan of Work

First, make the catalog capable of independent object ownership. Add catalog and store commands that upsert/remove appearance profiles and placement profiles by their own stable identifiers. A preset must refer to existing component-profile identifiers rather than always synthesizing profile objects from its name. Deleting a preset must remove only that preset; deleting a component profile must be rejected when a preset still references it. This prevents a library action from corrupting another saved object.

Second, define the user-facing flow. The refinement dialog remains the place where the user edits the current document’s appearance and placement. It gains visible `Save appearance for reuse...`, `Save placement for reuse...`, and `Save signature preset...` actions. Each asks for an explicit name through the existing input-dialog binding and saves the currently edited state without requiring the user to understand internal identifiers.

Second, add a dedicated reusable-object management surface. Follow the certificate-configuration pattern: a separate dialog reachable from the app frame or the refinement workflow that lets the user review, rename, and delete saved appearance profiles, placement profiles, and signature presets. This surface does not need to become a complex library browser, but it must satisfy the spec’s requirement that full create/edit/delete management exist in a dedicated library or settings area rather than only in the main shell.

Third, add the dedicated `Manage signing profiles...` Settings dialog. It presents the separately named appearance profiles, placement profiles, and signature presets with delete actions and enough description for users to recognize each object. The main shell `Signature preset` combo remains the quick selection surface. Saving a preset from the refinement dialog refreshes and selects it there without replacing the live draft or certificate unexpectedly.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Re-read the current shell and refinement-dialog code.

       sed -n '520,980p' src/foliaseal/presentation/qt/signing_workspace_properties_panel.py
       sed -n '1,520p' src/foliaseal/presentation/qt/visible_signature_setup_form.py
       sed -n '1,240p' src/foliaseal/application/signature_properties_coordinator.py
       sed -n '1,220p' src/foliaseal/application/signing_setup_session.py

2. Re-read the reusable-object schema/storage boundary.

       sed -n '1,320p' src/foliaseal/infra/config/schemas.py
       sed -n '1,260p' src/foliaseal/infra/config/profile_storage.py

3. Write a failing behavior-level test for each catalog ownership rule, then implement the catalog/store/coordinator/session commands one behavior at a time. Write Qt tests for the three refinement save actions and the Settings management entry point, then implement those surfaces.

   .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_signature_preset_storage.py tests/unit/test_qt_app_frame.py

4. Validate manually in the live GUI.

       .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf

   Expected result: the user can save a named appearance, placement, and preset visibly, inspect and delete unreferenced objects in Settings, then re-select the preset from the main shell without hidden controls.

## Validation and Acceptance

Acceptance is behavioral. A first-time user should be able to open the refinement dialog, change the current document’s visible signature setup, save reusable named objects, return to the main shell, and select the saved preset from the visible combo box. A second pass should prove that saved objects can be renamed or deleted from a dedicated management surface and that the main shell refreshes accordingly. Run the focused tests above and then repeat the live GUI walkthrough. If saving a reusable preset still requires hidden controls or code knowledge, this slice is not done.

## Idempotence and Recovery

Prefer additive GUI surfaces over destructive rewrites. If a new management dialog lands before all shell wiring is complete, keep the existing quick-selection combo working so the app remains usable. When changing persisted-object behavior, keep tests around store load/save flows green at every step. If a rename/delete flow behaves unexpectedly, use the dedicated management dialog as the single repair path rather than scattering duplicate controls back into the main shell.

## Artifacts and Notes

The motivating audit evidence is:

    .tmp/gui_user_flow_audit_2026-07-13.md

The reviewed findings for this slice are:

    .tmp/gui_findings_and_fix_plan_2026-07-13.md

The critical proof point is that the visible GUI must no longer dead-end at preset save.

## Interfaces and Dependencies

The main Qt files are `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py`, `src/foliaseal/presentation/qt/visible_signature_setup_form.py`, and possibly `src/foliaseal/presentation/qt/app_frame.py` if the dedicated management surface is launched from a top-level menu. The application-layer coordination lives in `src/foliaseal/application/signature_properties_coordinator.py` and `src/foliaseal/application/signing_setup_session.py`. Persisted-object semantics live in `src/foliaseal/infra/config/schemas.py` and `src/foliaseal/infra/config/profile_storage.py`. Reuse those boundaries rather than inventing parallel object stores.

The primary allowed change class for this slice is behavior change. Evidence refresh and documentation updates may follow once the behavior is stable, but do not mix unrelated shell-cleanup work into this slice.

Revision note: 2026-07-17 / Codex
Reconciled the plan with the live mounted controls and added the catalog-ownership prerequisite. The prior plan incorrectly described the mounted preset controls as absent; the actual gap is independent profile ownership and a dedicated management surface.

Revision note: 2026-07-17 / Codex
Split the next executable behavior into `gui_save_appearance_profile_from_refinement_execplan.md` after the required dev-loop review established that it is the smallest complete visible path.
