# Visible Signature Semantics Workflow Migration

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`. It is plan 2 of 5 for GitHub issue #50, "RFC: Deepen visible signature draft semantics boundary." It depends on `docs/ExecPlans/visible_signature_semantics_foundation_execplan.md`.

## Purpose / Big Picture

After this slice, the live signing draft workflow will use the new visible-signature semantics boundary to build preview fields, detail text, visible-fit validation issues, and request readiness. Users should see no UI behavior change, but the code path that decides what text appears in the preview will be shared with later backend signing migration work.

## Progress

- [x] (2026-05-01T18:19Z) Created this ExecPlan as the second issue #50 slice.
- [x] (2026-05-01T18:40Z) Confirmed the foundation plan added `VisibleSignatureSemanticsService`, public exports, and focused tests.
- [x] (2026-05-01T18:40Z) Migrated `SigningDraftWorkflow.preview()` and visible-fit validation to resolve fields, detail text, stamp text, and fit issues through `VisibleSignatureSemanticsService`.
- [x] (2026-05-01T18:40Z) Preserved existing public methods and `SigningDraftPreview` shape for Qt callers.
- [x] (2026-05-01T18:40Z) Removed now-unused workflow text-composition helpers that imported backend-private `_compose_visible_signature_text_layout()`.
- [x] (2026-05-01T18:40Z) Ran workflow, preview, Qt shell, and semantics validation successfully.
- [x] (2026-05-01T21:43Z) Next slice executed: `docs/ExecPlans/visible_signature_semantics_preview_migration_execplan.md` stopped canonical preview from composing stamp text independently.

## Surprises & Discoveries

- Observation: No migration work has started.
  Evidence: this plan was created before code edits for the workflow slice.

- Observation: `SigningDraftWorkflow` still needs a backend-private fit validator adapter.
  Evidence: after this slice, `rg -n "_compose_visible_signature_text_layout|_visible_signature_fit_issues_for_stamp_text" src/foliaseal/application/signing_draft_workflow.py` shows only `_visible_signature_fit_issues_for_stamp_text` inside the workflow-local `VisibleSignatureFitValidator` adapter. The backend text-composition helper import is gone. The remaining fit helper is transitional because backend fit validation and final signing semantics move in later plans.

## Decision Log

- Decision: migrate the workflow before preview renderer or backend signing.
  Rationale: `SigningDraftWorkflow` is the normal source of `SigningDraftPreview` for the Qt shell. Moving it first lets production preview state use the new semantics while keeping downstream renderers unchanged.
  Date/Author: 2026-05-01 / Codex

- Decision: preserve the existing `SigningDraftWorkflow` API during this slice.
  Rationale: Qt shell and tests already rely on methods such as `preview()`, `validation_issues()`, and `build_signing_request()`. This slice should change internals, not caller contracts.
  Date/Author: 2026-05-01 / Codex

## Outcomes & Retrospective

The workflow migration slice succeeded.

What changed:

- `SigningDraftWorkflow.preview()` now calls `VisibleSignatureSemanticsService.resolve()` and maps resolved fields back into the existing `SigningDraftPreviewField` DTO.
- `_validate_visible_signature_fit()` delegates to the semantics resolver so fit validation receives the same resolved stamp text used for preview detail text.
- Workflow-local adapters now bridge existing PKCS#12 preview value caching and backend fit validation into the new semantics ports.
- Removed unused workflow-private preview field/detail/fragment helpers that duplicated the new semantics boundary and imported backend-private text composition.

What did not change:

- The public `SigningDraftWorkflow` API is unchanged.
- `SigningDraftPreview` shape is unchanged.
- `signing_preview_renderer.py` still has `_preview_stamp_text()` until the next plan.
- Backend signing still owns final signing stamp text and metadata helpers until the backend migration plan.
- The workflow still uses backend-private `_visible_signature_fit_issues_for_stamp_text()` behind a local adapter; this is documented transitional debt for the backend migration plan.

Verification results:

    .venv/bin/ruff check src/foliaseal/application/signing_draft_workflow.py src/foliaseal/application/visible_signature_semantics.py tests/unit/test_signing_draft_workflow.py tests/unit/test_visible_signature_semantics.py
    All checks passed!

    .venv/bin/pytest -q tests/unit/test_visible_signature_semantics.py tests/unit/test_signing_draft_workflow.py
    16 passed in 0.62s

    .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py::test_signing_shell_fresh_workflow_uses_signer_first_default_preview_order tests/unit/test_signing_preview_renderer.py::test_preview_renderer_formats_semantics_deterministically
    2 passed in 0.33s

## Context and Orientation

`SigningDraftWorkflow` in `src/foliaseal/application/signing_draft_workflow.py` is the application state machine used by the Qt signing shell. It stores the input PDF path, output PDF path, certificate path, passphrase, timestamp settings, selected `SignatureRect`, selected `SignatureAppearance`, and optional page geometry. Its `preview()` method returns a `SigningDraftPreview`, which the UI and preview renderer consume.

The workflow currently owns private helpers that issue #50 wants to deepen: `_build_preview_fields()`, `_build_preview_detail_text()`, `_visible_preview_fragments()`, `_certificate_values_for_preview()`, `_preview_signing_time()`, and `_validate_visible_signature_fit()`. It also imports backend-private helpers such as `_compose_visible_signature_text_layout()`, `_stamp_background_for_path()`, and `_visible_signature_fit_issues_for_stamp_text()`.

The previous plan should have added `src/foliaseal/application/visible_signature_semantics.py`. This slice uses that module from the workflow.

## Plan of Work

Add a default semantics service factory or constructor path that `SigningDraftWorkflow` can use without requiring Qt callers to pass new dependencies. Prefer dependency injection on the workflow dataclass only if tests need deterministic ports; otherwise use a small private `_default_visible_signature_semantics_service()` helper in `signing_draft_workflow.py`.

Change `SigningDraftWorkflow.preview()` so it asks `VisibleSignatureSemanticsService.resolve()` for fields, detail text, and semantic issues. Map each resolved `VisibleSignatureField` back into `SigningDraftPreviewField` so external callers see the same preview payload shape.

Change `_validate_visible_signature_fit()` so it no longer imports backend-private text composition helpers directly. The fit issue should come from the semantics resolver and should be based on the same stamp text used in `preview().detail_text`. If keeping `_validate_visible_signature_fit()` as a compatibility wrapper makes the change smaller, keep it private and delegate to the semantics service.

Keep placement validation in `SigningDraftWorkflow` unless the foundation service explicitly owns it. Placement validation means checking that the selected rectangle is on the active page and inside page bounds. It depends on `SignaturePlacementContext` and coordinate geometry, not visible text semantics.

Do not update `signing_preview_renderer.py` or `phase3_signing_backend.py` in this slice. The preview renderer may still call `_preview_stamp_text()` until the preview migration plan.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Confirm foundation files exist:

    test -f src/foliaseal/application/visible_signature_semantics.py
    test -f tests/unit/test_visible_signature_semantics.py

Search current workflow helper usage:

    rg -n "_build_preview_fields|_build_preview_detail_text|_visible_preview_fragments|_certificate_values_for_preview|_validate_visible_signature_fit|_compose_visible_signature_text_layout|_visible_signature_fit_issues_for_stamp_text" src/foliaseal/application/signing_draft_workflow.py tests/unit/test_signing_draft_workflow.py

Create or update these files:

    src/foliaseal/application/signing_draft_workflow.py
    src/foliaseal/application/visible_signature_semantics.py
    tests/unit/test_signing_draft_workflow.py
    tests/unit/test_visible_signature_semantics.py
    docs/ExecPlans/visible_signature_semantics_workflow_migration_execplan.md

Run focused validation:

    .venv/bin/ruff check src/foliaseal/application/signing_draft_workflow.py src/foliaseal/application/visible_signature_semantics.py tests/unit/test_signing_draft_workflow.py tests/unit/test_visible_signature_semantics.py
    .venv/bin/pytest -q tests/unit/test_visible_signature_semantics.py tests/unit/test_signing_draft_workflow.py

Run adjacent UI/preview smoke tests because the workflow feeds the Qt shell and renderer:

    .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py::test_signing_shell_fresh_workflow_uses_signer_first_default_preview_order tests/unit/test_signing_preview_renderer.py::test_preview_renderer_formats_semantics_deterministically

## Validation and Acceptance

This slice is accepted when `SigningDraftWorkflow.preview()` produces the same observable preview fields, detail text, validation issues, and `can_submit` readiness as before, but the semantic decisions come from `VisibleSignatureSemanticsService`.

The workflow test `test_workflow_builds_preview_and_final_request` and certificate preview tests must still pass. New or updated tests should demonstrate that the workflow uses an injected or fake semantics service when practical, so later migrations can rely on the boundary instead of backend-private helpers.

## Idempotence and Recovery

This slice is behavior-preserving and can be retried. If migration fails, revert only the workflow changes made in this slice and keep the foundation semantics module intact. Do not alter profile persistence, Qt widget layout, generated artifacts, or backend signing behavior.

## Artifacts and Notes

The next plan, `visible_signature_semantics_preview_migration_execplan.md`, depends on this one because the preview renderer should receive preview payloads whose text already came from the semantics service.

## Interfaces and Dependencies

The workflow should depend on the public interface of `visible_signature_semantics.py`, not backend-private helpers in `phase3_signing_backend.py`. Any remaining backend-private import in `signing_draft_workflow.py` after this slice must be recorded in this plan with a reason and follow-up owner.

Revision note: Created 2026-05-01 by Codex to define the workflow migration slice for issue #50.

Revision note: Updated 2026-05-01 by Codex after migrating `SigningDraftWorkflow.preview()` and fit validation onto `VisibleSignatureSemanticsService` while preserving the public workflow and preview DTO shape.
