# Move Preset Save Assembly Up to the Coordinator

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, saving a signature preset through the signing-properties coordinator will no longer require the coordinator to call `SigningDraftWorkflow.capture_current_signature_setup(...)` on the live save path. The visible behavior stays the same: saving still persists the same preset JSON, still derives placement defaults from the current signature rectangle when needed, and still fails with the same error when no signature appearance exists. A contributor can prove the slice works by running focused coordinator, workflow, storage, and schema tests and observing unchanged save behavior with a narrower application-layer seam.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/signing_setup_session_panel_boundary_execplan.md` completed the panel save-path caller cleanup.
- [x] `docs/ExecPlans/signing_preset_apply_boundary_execplan.md` completed the lower preset-apply boundary cleanup.
- [ ] No child ExecPlans are required for this slice.

## Progress

- [x] (2026-06-26 10:08Z) Rechecked the repository state and confirmed the remaining live save seam is `DefaultSignaturePropertiesCoordinator._save_current_preset(...)` calling `SigningDraftWorkflow.capture_current_signature_setup(...)`.
- [x] (2026-06-26 10:15Z) Completed the required `explorer-light` dev-loop audit and selected the next tracer bullet: assemble `ResolvedSignaturePreset` in the coordinator while leaving workflow capture and persistence contracts unchanged.
- [x] (2026-06-26 10:31Z) Tightened focused coordinator save-path coverage so the slice proved unchanged persistence behavior and selected-state behavior.
- [x] (2026-06-26 10:31Z) Moved live save-path preset assembly into `DefaultSignaturePropertiesCoordinator._save_current_preset(...)` without changing `SignaturePresetCatalog.upsert_preset(...)` or `SignaturePresetCatalogStore.save_preset(...)`.
- [x] (2026-06-26 10:31Z) Ran focused validation and recorded the passing evidence: `75 passed in 0.63s`.
- [x] (2026-06-26 10:31Z) Ran the required architecture/spec compliance review and confirmed compliance with `docs/ARCHITECTURE.md` and `docs/SPEC.md`, with only ExecPlan status drift corrected.

## Surprises & Discoveries

- Observation: the next smallest save-side seam is above storage, not inside it.
  Evidence: `SignaturePresetCatalog.upsert_preset(...)` and `SignaturePresetCatalogStore.save_preset(...)` still hard-require `ResolvedSignaturePreset`, but only the coordinator’s live save path is forced to call `SigningDraftWorkflow.capture_current_signature_setup(...)` right now.

## Decision Log

- Decision: leave `SigningDraftWorkflow.capture_current_signature_setup(...)` in place as a compatibility/helper path rather than removing it in this slice.
  Rationale: removing or reshaping that workflow method would create a broader workflow API migration without directly reducing the live coordinator save seam further than this tracer bullet requires.
  Date/Author: 2026-06-26 / Codex

- Decision: keep `SignaturePresetCatalog.upsert_preset(...)` and `SignaturePresetCatalogStore.save_preset(...)` on `ResolvedSignaturePreset` for now.
  Rationale: widening those APIs to a new draft DTO would immediately spill into schema, storage, serialization, and catalog-validation tests, which is too broad for this slice.
  Date/Author: 2026-06-26 / Codex

## Outcomes & Retrospective

This slice is complete. The coordinator now assembles the persistence-shaped preset on the live save path, leaving the workflow capture helper as a non-live compatibility path and leaving persistence behavior unchanged.

Validation confirmed the expected focused result: `75 passed in 0.63s`.

Compliance review result: compliant with `docs/ARCHITECTURE.md` and `docs/SPEC.md`, with only ExecPlan status drift corrected.

## Context and Orientation

The repository root is `/home/daekar/FoliaSeal`. `src/foliaseal/application/signature_properties_coordinator.py` is the application-layer boundary for signing-properties reconciliation. It already owns preset-apply orchestration, certificate-configuration resolution, selected display-name state, and persistence-triggering save/delete commands. `src/foliaseal/application/signing_draft_workflow.py` owns the mutable signing draft and still exposes `capture_current_signature_setup(...)`, which packages the draft state into a `ResolvedSignaturePreset`.

`ResolvedSignaturePreset` lives in `src/foliaseal/infra/config/schemas.py`. It is a persistence-oriented object that combines a reference-style `SignaturePreset` record with resolved appearance and placement profiles. `SignaturePresetCatalog.upsert_preset(...)` and `SignaturePresetCatalogStore.save_preset(...)` both still require that object. Today, the live save path in the coordinator calls `self.workflow.capture_current_signature_setup(name)` and then passes the resulting `ResolvedSignaturePreset` to the catalog and store. That means the application boundary still depends on the workflow capture API even though the coordinator already knows how to validate and persist the result.

This slice narrows only the live save-path seam above persistence. It must not change Qt panel/session behavior, preset JSON shape, catalog schema versioning, `SignaturePresetCatalog.upsert_preset(...)`, `SignaturePresetCatalogStore.save_preset(...)`, or the workflow apply path that was cleaned up in the previous slice. Allowed generated artifacts are application-layer behavior change in the coordinator, focused evidence refresh in tests, and matching documentation/status updates.

## Plan of Work

First, tighten the coordinator save test so it proves not only that the preset name is selected and persisted, but also that the saved catalog still reflects the draft appearance and any placement-default derivation needed by the current save path. This creates a focused red/green signal on the live coordinator seam.

Second, edit `src/foliaseal/application/signature_properties_coordinator.py`. In `_save_current_preset(...)`, replace the call to `self.workflow.capture_current_signature_setup(name)` with local assembly of `ResolvedSignaturePreset.from_parts(...)` using the workflow’s current signature appearance, current placement defaults, rectangle-derived fallback dimensions when needed, and current certificate configuration id. Preserve the existing `ValueError` mapping so a missing appearance still raises `SignaturePropertiesCoordinatorError` with the same message.

Third, leave `SigningDraftWorkflow.capture_current_signature_setup(...)` unchanged and keep persistence layers untouched. The purpose is only to stop the live coordinator save path from depending on that workflow helper. The workflow helper remains as compatibility coverage for direct workflow tests and any non-coordinator callers that still use it.

Finally, rerun the focused tests across coordinator, workflow, storage, and schema modules. If documentation drift appears in the architecture note or this ExecPlan, update only those docs after the compliance review.

## Concrete Steps

Work from `/home/daekar/FoliaSeal`.

1. Edit `tests/unit/test_signature_properties_coordinator.py` to strengthen the save-path test around persisted preset contents.
2. Edit `src/foliaseal/application/signature_properties_coordinator.py` so `_save_current_preset(...)` assembles `ResolvedSignaturePreset.from_parts(...)` locally.
3. Run:

       pytest tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_draft_workflow.py tests/unit/test_signature_preset_storage.py tests/unit/test_config_schemas.py

   Expect all tests in those modules to pass. The tightened coordinator save test should fail before the code change and pass after it.
4. Run the required architecture/spec compliance review and record whether the implementation remains aligned with `docs/ARCHITECTURE.md` and `docs/SPEC.md`.

## Validation and Acceptance

Acceptance is behavior-focused. After the change:

- saving a preset through the coordinator must still persist the preset under the requested name,
- the saved preset must still reflect the current draft appearance,
- placement defaults must still come from the current draft defaults or the current signature rectangle fallback when explicit defaults are absent, and
- saving without a signature appearance must still raise the existing coordinator error.

Running

    pytest tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_draft_workflow.py tests/unit/test_signature_preset_storage.py tests/unit/test_config_schemas.py

must succeed from the repository root.

## Idempotence and Recovery

These edits are safe to repeat because they only narrow one live coordinator seam and refresh focused tests. If the save-path test fails midway, finish the coordinator edit and rerun the same `pytest` command. If local assembly needs a shared helper to stay readable, add a small private coordinator helper instead of widening the change into workflow or storage APIs.

## Artifacts and Notes

Expected validation transcript shape after implementation:

    $ pytest tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_draft_workflow.py tests/unit/test_signature_preset_storage.py tests/unit/test_config_schemas.py
    ...
    4x passed in x.xx s

Record the exact passing transcript and any compliance-review notes once implementation is complete.

## Interfaces and Dependencies

`DefaultSignaturePropertiesCoordinator._save_current_preset(...)` must continue to persist a `ResolvedSignaturePreset`, but after this slice it should create that object itself via `ResolvedSignaturePreset.from_parts(...)` instead of calling `SigningDraftWorkflow.capture_current_signature_setup(...)` on the live path.

The coordinator will need the following current workflow state to assemble that object:

- `current_signature_appearance`
- `signature_placement_defaults`, or a rectangle-derived `SignaturePlacementDefaults` fallback when only `signature_rect` is present
- `selected_certificate_configuration_id`

`SigningDraftWorkflow.capture_current_signature_setup(...)`, `SignaturePresetCatalog.upsert_preset(...)`, and `SignaturePresetCatalogStore.save_preset(...)` must still exist unchanged at the end of this slice.

Revision note: Created on 2026-06-26 by Codex after the required `explorer-light` dev-loop review selected coordinator-side preset save assembly as the next smallest reusable-signing-object tracer bullet.
