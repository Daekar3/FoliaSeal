# Visible Signature Semantics Cleanup And Issue Closure

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`. It is plan 5 of 5 for GitHub issue #50, "RFC: Deepen visible signature draft semantics boundary." It depends on the foundation, workflow migration, preview migration, and backend migration plans.

## Purpose / Big Picture

After this slice, issue #50 can close cleanly. The repository should have one visible-signature semantics boundary, production callers should use it, obsolete private-helper tests should be removed or demoted, and architecture documentation should describe the new ownership. Users should see no behavioral change, but future preview/signing changes should be easier to reason about because text and metadata semantics have one owner.

## Progress

- [x] (2026-05-01T18:19Z) Created this ExecPlan as the fifth and final issue #50 slice.
- [x] (2026-05-01T21:43Z) Confirmed plans 1 through 4 are complete and committed: `3e0686e24`, `2ed5a99f7`, `928c4fcd3`, and `9eaf1af86`.
- [x] (2026-05-01T21:43Z) Removed obsolete backend-private semantic helper code after production callers moved to `VisibleSignatureSemanticsService`.
- [x] (2026-05-01T21:43Z) Retained private wrapper tests where they still protect harness diagnostics or backend compatibility around `_build_stamp_text()`.
- [x] (2026-05-01T21:43Z) Updated architecture and ExecPlan documentation with final ownership and remaining debt.
- [x] (2026-05-01T21:43Z) Ran full focused and broader validation and prepared the GitHub issue #50 closure report.
- [x] (2026-05-01T21:43Z) Closed GitHub issue #50: https://github.com/Daekar3/FoliaSeal/issues/50.

## Surprises & Discoveries

- Observation: `_build_stamp_text()` remains useful as a compatibility wrapper even though it no longer owns semantic composition.
  Evidence: `presentation/qt/phase3_harness.py` and backend tests use it to obtain backend-resolved stamp text for diagnostics and layout assertions. The wrapper delegates to `_resolve_visible_signature_semantics()`.

- Observation: The old backend text layout helper and metadata helpers could be deleted.
  Evidence: after backend migration, `_compose_visible_signature_text_layout`, `VisibleSignatureTextLayout`, `_resolve_visible_field_text`, `_visible_reason`, `_visible_location`, `_visible_email`, and `_binding_for_field` had no production call sites.

- Observation: Remaining preview `_preview_stamp_text()` helpers are presentation compatibility, not semantic ownership.
  Evidence: `signing_preview_renderer.py` and `signing_shell.py` first prefer `SigningDraftPreview.stamp_text`; fallback composition only supports direct/test-constructed previews without the semantic field.

## Decision Log

- Decision: cleanup is a separate plan.
  Rationale: deleting or demoting tests is safest only after production workflow, preview, and backend callers have migrated and focused validation is green.
  Date/Author: 2026-05-01 / Codex

- Decision: do not close issue #50 until architecture documentation is updated.
  Rationale: issue #50 is architectural work. The closure report should make future ownership clear to humans and agents.
  Date/Author: 2026-05-01 / Codex

## Outcomes & Retrospective

Issue #50 is complete and closed: https://github.com/Daekar3/FoliaSeal/issues/50.

Final ownership is documented in `docs/ARCHITECTURE.md`: `visible_signature_semantics.py` owns visible fields, certificate fallback semantics, signing-time text, detail text, escaped stamp text, metadata text, and semantic fit issue aggregation. `visible_signature_layout.py` owns geometry and fit planning. `signing_preview_renderer.py` renders textual/canonical previews from resolved preview data. `phase3_signing_backend.py` owns concrete pyHanko signing, stamp style construction, PDF output, timestamping, and verification.

Production callers now consume the semantics boundary:

- `SigningDraftWorkflow.preview()` resolves fields, detail text, stamp text, and visible-fit issues through `VisibleSignatureSemanticsService`.
- Canonical preview rendering consumes `SigningDraftPreview.stamp_text`.
- `PyHankoPdfSigner.sign()` resolves final-signing semantics once and uses that payload for fit validation, visible stamp text, and PDF metadata.

Private helpers remaining:

- `_build_stamp_text()` remains as a backend compatibility wrapper used by tests and harness diagnostics.
- `_semantic_preview_stamp_text()` and Qt `_preview_stamp_text()` remain as compatibility fallbacks for direct `SigningDraftPreview` construction; normal workflow previews provide `stamp_text`.
- Layout-heavy backend helpers remain under issue #49 / later architectural work because they protect pyHanko geometry and rendered-ink behavior, not semantic text ownership.

Validation completed:

    .venv/bin/ruff check src/foliaseal/application/signing_draft_workflow.py src/foliaseal/application/signing_preview_renderer.py src/foliaseal/application/phase3_signing_backend.py src/foliaseal/application/visible_signature_semantics.py tests/unit/test_visible_signature_semantics.py tests/unit/test_signing_draft_workflow.py tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_signing_backend.py
    All checks passed.

    .venv/bin/pytest -q tests/unit/test_visible_signature_semantics.py tests/unit/test_signing_draft_workflow.py tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_signing_backend.py
    165 passed in 27.30s.

    .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py
    59 passed in 3.78s.

    .venv/bin/pytest -q tests/unit/test_sign_pdf_use_case.py tests/unit/test_phase3_harness.py
    116 passed, 1 warning in 1.39s.

## Context and Orientation

By the time this plan starts, these earlier plans should have completed:

- the foundation plan added `src/foliaseal/application/visible_signature_semantics.py`;
- the workflow migration plan moved `SigningDraftWorkflow.preview()` and visible-fit validation to the semantics boundary;
- the preview migration plan stopped canonical preview rendering from composing stamp text independently;
- the backend migration plan moved final signing stamp text and metadata derivation to the semantics boundary.

This cleanup plan is not a feature-building slice. It is a consolidation slice: remove redundant tests, retire old helper seams, update docs, and close the issue only after evidence is recorded.

## Plan of Work

Start by inventorying remaining semantic helper usage. Semantic helpers are functions that decide visible field text, detail text, final stamp text, reason/location/contact metadata, or preview/signing text parity. Layout helpers that decide geometry belong to issue #49 and should not be removed here.

Search for these names:

    _compose_visible_signature_text_layout
    _build_stamp_text
    _preview_stamp_text
    _visible_reason
    _visible_location
    _visible_email
    _build_preview_fields
    _build_preview_detail_text
    _visible_preview_fragments

For each remaining use, choose one of three outcomes:

1. Delete it because production and tests now use `VisibleSignatureSemanticsService`.
2. Keep it as a private compatibility wrapper that delegates to the semantics boundary, and document why.
3. Keep it because it is not semantic text ownership after all; record the reason.

Move or delete redundant tests carefully. Do not delete a test unless an equal or stronger `test_visible_signature_semantics.py` boundary test covers the same behavior. Prefer replacing several shallow tests with one boundary test that exercises the complete semantic resolution.

Update `docs/ARCHITECTURE.md` to add a "Visible signature semantics boundary" component or to expand the existing signing draft/preview section. The doc should say that semantic text and metadata belong to `visible_signature_semantics.py`, while layout geometry belongs to `visible_signature_layout.py`, rendering belongs to `signing_preview_renderer.py`, and PDF signing belongs to `phase3_signing_backend.py`.

Update these five ExecPlans with outcomes, validation, and closure status. If any debt remains, create a follow-up GitHub issue only if it is concrete and not already covered by issue #49.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/SignPDF/Scratch

Inventory semantic helper usage:

    rg -n "_compose_visible_signature_text_layout|_build_stamp_text|_preview_stamp_text|_visible_reason|_visible_location|_visible_email|_build_preview_fields|_build_preview_detail_text|_visible_preview_fragments" src tests

Create or update these files as needed:

    src/foliaseal/application/signing_draft_workflow.py
    src/foliaseal/application/signing_preview_renderer.py
    src/foliaseal/application/phase3_signing_backend.py
    src/foliaseal/application/visible_signature_semantics.py
    tests/unit/test_visible_signature_semantics.py
    tests/unit/test_signing_draft_workflow.py
    tests/unit/test_signing_preview_renderer.py
    tests/unit/test_phase3_signing_backend.py
    docs/ARCHITECTURE.md
    docs/ExecPlans/visible_signature_semantics_foundation_execplan.md
    docs/ExecPlans/visible_signature_semantics_workflow_migration_execplan.md
    docs/ExecPlans/visible_signature_semantics_preview_migration_execplan.md
    docs/ExecPlans/visible_signature_semantics_backend_migration_execplan.md
    docs/ExecPlans/visible_signature_semantics_cleanup_execplan.md

Run focused validation:

    .venv/bin/ruff check src/foliaseal/application/signing_draft_workflow.py src/foliaseal/application/signing_preview_renderer.py src/foliaseal/application/phase3_signing_backend.py src/foliaseal/application/visible_signature_semantics.py tests/unit/test_visible_signature_semantics.py tests/unit/test_signing_draft_workflow.py tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_signing_backend.py
    .venv/bin/pytest -q tests/unit/test_visible_signature_semantics.py tests/unit/test_signing_draft_workflow.py tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_signing_backend.py

Run broader safety checks before closing the issue:

    .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_sign_pdf_use_case.py tests/unit/test_phase3_harness.py

Check working tree state and prepare closure notes:

    git status --short
    gh issue view 50 --json number,title,state,url

## Validation and Acceptance

This final slice is accepted when production semantic text ownership is centralized in `VisibleSignatureSemanticsService`, redundant helper tests have been removed or demoted, architecture documentation is updated, and focused validation passes. A closure report for issue #50 must state:

- which public boundary now owns visible-signature semantics;
- which production callers consume it;
- which tests prove preview/signing parity;
- which private helpers remain, if any, and why;
- whether follow-up debt belongs to issue #49 or a new issue.

## Idempotence and Recovery

Test deletion is the riskiest part of this plan. Delete tests only after adding or confirming stronger boundary coverage. If validation fails after cleanup, restore the deleted test or wrapper and record the reason. Do not close GitHub issue #50 until validation is green and the closure report is written.

## Artifacts and Notes

This plan may update documentation and close GitHub issue #50. It should not refresh generated harness artifacts unless a changed test explicitly requires it, and any such artifact refresh must be recorded as evidence refresh rather than mixed silently into behavior cleanup.

## Interfaces and Dependencies

At the end of issue #50, the intended ownership is:

- `visible_signature_semantics.py` owns visible fields, certificate fallback semantics, signing-time text, detail text, escaped stamp text, metadata text, and semantic fit issue aggregation.
- `visible_signature_layout.py` owns geometry and fit planning for text/stamp placement.
- `signing_preview_renderer.py` owns textual and canonical preview rendering from already-resolved preview/semantic data.
- `phase3_signing_backend.py` owns concrete pyHanko signing, stamp style construction, PDF output, timestamping, and verification.
- `signing_draft_workflow.py` owns draft state and placement coordination, while delegating visible-signature semantic resolution.

Revision note: Created 2026-05-01 by Codex to define the cleanup and closure slice for issue #50.
