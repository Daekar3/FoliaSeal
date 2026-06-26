# Narrow the Signature Preset Apply Path Below the Coordinator

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, applying a signature preset through the signing-properties coordinator will no longer require the coordinator to hand a full `ResolvedSignaturePreset` persistence object to the workflow. The visible behavior stays the same: preset selection still updates appearance and placement defaults, still preserves the active certificate when the preset does not carry one, and still applies certificate material first when the preset references a certificate configuration. A contributor can prove the slice works by running the focused coordinator, workflow, and setup-session unit tests and observing unchanged preset-application behavior with a narrower application-layer seam.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/signing_setup_session_panel_boundary_execplan.md` completed the panel save-path boundary cleanup.
- [x] `docs/ExecPlans/signing_setup_session_panel_delete_boundary_execplan.md` completed the panel delete-path boundary cleanup.
- [x] `docs/ExecPlans/signing_setup_session_preset_prompt_query_execplan.md` completed the prompt-label query cleanup above the coordinator.
- [ ] No child ExecPlans are required for this slice.

## Progress

- [x] (2026-06-26 09:20Z) Rechecked the current repository state and confirmed the next live hybrid seam is the coordinator-to-workflow preset apply path, not the save/persist path.
- [x] (2026-06-26 09:27Z) Completed the required `explorer-light` dev-loop audit and selected the next tracer bullet: narrow preset application below `DefaultSignaturePropertiesCoordinator` while leaving save/persistence on `ResolvedSignaturePreset`.
- [x] (2026-06-26) Added a narrow workflow helper for applying preset values without requiring a full `ResolvedSignaturePreset` object at the coordinator boundary.
- [x] (2026-06-26) Updated `DefaultSignaturePropertiesCoordinator._apply_signature_preset(...)` to call `SigningDraftWorkflow.apply_signature_preset_values(...)` on the live apply path while keeping `apply_resolved_signature_preset(...)` as a compatibility wrapper.
- [x] (2026-06-26) Ran the focused workflow/coordinator/setup-session validation and recorded the passing evidence here: `50 passed in 0.66s`.
- [x] (2026-06-26) Completed the required architecture/spec compliance review; it found the slice compliant after the architecture note was reconciled to the live apply helper boundary.

## Surprises & Discoveries

- Observation: the apply path is a thinner next seam than the save path because it stays in the application layer and avoids `profile_storage.py` and JSON schema code entirely.
  Evidence: `src/foliaseal/application/signature_properties_coordinator.py` currently decomposes certificate handling locally but still hands the full resolved schema object into `SigningDraftWorkflow.apply_resolved_signature_preset(...)`, while save still persists that same object through `SignaturePresetCatalogStore.save_preset(...)`.

## Decision Log

- Decision: keep `capture_current_signature_setup(...)`, `SignaturePresetCatalog.upsert_preset(...)`, and `SignaturePresetCatalogStore.save_preset(...)` unchanged in this slice.
  Rationale: those methods define the persistence-facing `ResolvedSignaturePreset` seam for preset saving. Mixing them into the apply-path cleanup would widen this tracer bullet into storage/schema work.
  Date/Author: 2026-06-26 / Codex

- Decision: add a narrow workflow helper for preset application and keep `apply_resolved_signature_preset(...)` as a compatibility wrapper for now.
  Rationale: the workflow should keep ownership of the actual draft mutations, but the coordinator no longer needs to depend on the workflow API that advertises a persistence-shaped input object.
  Date/Author: 2026-06-26 / Codex

## Outcomes & Retrospective

This slice is complete. The coordinator now applies preset values through `SigningDraftWorkflow.apply_signature_preset_values(...)` on the live apply path, while `apply_resolved_signature_preset(...)` remains as a compatibility wrapper for older callers. Focused validation passed, and the architecture/spec compliance review found the slice compliant after the architecture note was updated to match the implemented boundary.

## Context and Orientation

The repository root is `/home/daekar/FoliaSeal`. `src/foliaseal/application/signature_properties_coordinator.py` is the application-layer boundary for the Qt signing-properties panel. It owns display-name selection state, validation/readiness text, preset and certificate apply commands, and coordinator-driven catalog refresh. `src/foliaseal/application/signing_draft_workflow.py` owns the mutable signing draft: active certificate selection, visible-signature appearance, placement defaults, selected reusable-object identifiers, validation issues, and preview/request derivation.

A `ResolvedSignaturePreset` in this repository is a persistence-oriented object from `src/foliaseal/infra/config/schemas.py` that combines a reference-style preset record with resolved appearance and placement defaults. Today, the coordinator still uses that object in the preset apply path: it loads a preset from the catalog, resolves certificate material if needed, and then calls `SigningDraftWorkflow.apply_resolved_signature_preset(...)`. That means the coordinator-to-workflow boundary still advertises a persistence-shaped input even though the workflow only needs a handful of draft mutation values from it.

This slice only narrows the preset apply path. It must not redesign preset saving, catalog persistence, JSON shape, or schema versioning. Allowed generated artifacts for this slice are behavior changes in the application layer, evidence refresh in focused unit tests, and the matching documentation/status updates. Forbidden changes include edits to `src/foliaseal/infra/config/profile_storage.py`, `src/foliaseal/infra/config/schemas.py`, preset JSON migration logic, Qt prompt/cancel/cache behavior, and broad reusable-object refactors outside the apply path.

## Plan of Work

First, extend `src/foliaseal/application/signing_draft_workflow.py` with a narrow helper that applies signature-preset values to the draft without accepting a full `ResolvedSignaturePreset`. The helper should take the appearance, placement defaults, preset id, appearance profile id, placement profile id, and optional certificate configuration id that actually drive draft state. It must preserve the current certificate selection when the provided certificate id is `None`, matching the current workflow behavior.

Second, rewrite `SigningDraftWorkflow.apply_resolved_signature_preset(...)` as a thin compatibility wrapper over the new helper. That keeps existing workflow-oriented tests and any remaining callers working while making the narrower mutation surface available.

Third, edit `src/foliaseal/application/signature_properties_coordinator.py` so `_apply_signature_preset(...)` decomposes the catalog-loaded preset and calls the new workflow helper directly after certificate material resolution. The coordinator should continue to resolve and apply certificate material first when the preset carries a certificate reference, and should continue to preserve the active certificate when the preset has no certificate reference.

Finally, tighten focused tests. `tests/unit/test_signing_draft_workflow.py` should cover the new workflow helper behavior directly, especially the partial-preset certificate-preservation rule. `tests/unit/test_signature_properties_coordinator.py` and `tests/unit/test_signing_setup_session.py` should continue proving that coordinator and session behavior is unchanged for both certificate-free and certificate-backed preset application.

## Concrete Steps

Work from `/home/daekar/FoliaSeal`.

1. Edit `src/foliaseal/application/signing_draft_workflow.py` to add the narrow preset-application helper and to reimplement `apply_resolved_signature_preset(...)` as a wrapper.
2. Edit `src/foliaseal/application/signature_properties_coordinator.py` so `_apply_signature_preset(...)` calls the narrow helper instead of `apply_resolved_signature_preset(...)`.
3. Edit `tests/unit/test_signing_draft_workflow.py`, `tests/unit/test_signature_properties_coordinator.py`, and, only if needed, `tests/unit/test_signing_setup_session.py` to cover the helper and preserve behavior-level evidence.
4. Run:

       pytest tests/unit/test_signing_draft_workflow.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py

   Expect all tests in those modules to pass. At least one new or tightened test should fail before the code change and pass after it.
5. Run the required architecture/spec compliance review and record whether the implementation remains aligned with `docs/ARCHITECTURE.md` and `docs/SPEC.md`.

## Validation and Acceptance

Acceptance is behavior-focused. After the change, selecting a signature preset through the coordinator or setup session must still:

- apply appearance and placement defaults from the preset,
- preserve the active certificate selection when the preset has no certificate reference, and
- apply the referenced certificate material first when the preset carries a certificate configuration id.

Running

    pytest tests/unit/test_signing_draft_workflow.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py

must succeed from the repository root.

## Idempotence and Recovery

These edits are safe to repeat because they only narrow an application-layer boundary and refresh focused tests. If a test fails midway, finish the remaining edits and rerun the same `pytest` command. If the narrower workflow helper proves incomplete, extend that helper rather than reintroducing direct coordinator dependence on `apply_resolved_signature_preset(...)`.

## Artifacts and Notes

Expected validation transcript shape after implementation:

    $ pytest tests/unit/test_signing_draft_workflow.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py
    ...
    4x passed in x.xx s

Record the exact passing transcript and any compliance-review notes once implementation is complete.

## Interfaces and Dependencies

In `src/foliaseal/application/signing_draft_workflow.py`, define a narrow workflow helper with a stable draft-oriented interface. The exact name can be chosen during implementation, but it must have the shape:

    def <preset_apply_helper>(
        self,
        *,
        appearance: SignatureAppearance,
        placement_defaults: SignaturePlacementDefaults | None,
        signature_preset_id: str | None,
        appearance_profile_id: str | None,
        placement_profile_id: str | None,
        certificate_configuration_id: str | None,
    ) -> None:
        ...

This helper must preserve `selected_certificate_configuration_id` when `certificate_configuration_id` is `None`.

`apply_resolved_signature_preset(...)` should remain available at the end of this slice, but only as a compatibility wrapper over the narrow helper.

`DefaultSignaturePropertiesCoordinator._apply_signature_preset(...)` must stop calling `SigningDraftWorkflow.apply_resolved_signature_preset(...)` directly and instead call the narrow workflow helper using values extracted from the catalog-loaded preset.

Revision note: Created on 2026-06-26 by Codex after the required `explorer-light` dev-loop review selected the coordinator-to-workflow preset apply path as the next smallest reusable-signing-object tracer bullet.
