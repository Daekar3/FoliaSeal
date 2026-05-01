# Visible Signature Semantics Backend Migration

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`. It is plan 4 of 5 for GitHub issue #50, "RFC: Deepen visible signature draft semantics boundary." It depends on the foundation, workflow migration, and preview migration plans.

## Purpose / Big Picture

After this slice, final PDF signing will consume the same visible-signature semantic resolution as preview. This means final stamp text and PDF metadata such as reason, location, and contact info will no longer be composed by separate backend-private rules. Users should see the same visible signature content in preview and signed output, and tests should prove that parity at the semantic boundary.

## Progress

- [x] (2026-05-01T18:19Z) Created this ExecPlan as the fourth issue #50 slice.
- [ ] Confirm preview migration is complete and semantics-derived stamp text is available.
- [ ] Migrate backend visible stamp text and metadata derivation to the semantics boundary.
- [ ] Preserve existing signing output behavior and failure-code mapping.
- [ ] Run backend, preview, and sign-use-case validation and record results here.

## Surprises & Discoveries

- Observation: No backend migration work has started.
  Evidence: this plan was created before code edits for the backend slice.

## Decision Log

- Decision: migrate backend signing after workflow and preview.
  Rationale: backend signing is the highest-risk production path. By migrating it after preview, the codebase already has a semantics boundary and preview parity tests to compare against.
  Date/Author: 2026-05-01 / Codex

- Decision: keep pyHanko style construction outside the semantics service.
  Rationale: semantics should decide text and metadata. `phase3_signing_backend.py` and the visible layout boundary still own pyHanko stamp style construction and signed PDF output.
  Date/Author: 2026-05-01 / Codex

## Outcomes & Retrospective

No implementation outcome yet. At completion, summarize which backend-private helpers were removed, wrapped, or kept because they protect pyHanko-specific behavior.

## Context and Orientation

`src/foliaseal/application/phase3_signing_backend.py` is the concrete pyHanko signing backend. It owns the functions that load certificates, inspect PDFs, build pyHanko stamp styles, sign PDFs, validate signed output, and integrate timestamping.

Issue #50 focuses only on visible-signature semantics. In backend terms, that means the text that appears inside the visible signature and the metadata strings passed into signing, such as reason, location, and contact information. It does not mean moving certificate loading, timestamping, pyHanko writer setup, style construction, or visible layout planning.

Backend-private helpers to inspect before editing include:

    _compose_visible_signature_text_layout
    _build_stamp_text
    _visible_reason
    _visible_location
    _visible_email
    _visible_signature_fit_issues
    _visible_signature_fit_issues_for_stamp_text

Some of these may remain as compatibility wrappers during the transition, but final backend signing should ask `VisibleSignatureSemanticsService` for semantic text instead of composing it independently.

## Plan of Work

Add a production adapter in `visible_signature_semantics.py` or a small adjacent module if needed. The adapter should be able to read certificate/signer field values for final signing mode. If the existing backend has signer-derived helpers that are hard to expose cleanly in this slice, keep a backend-local adapter class that implements the semantics port and delegates to current signer inspection code.

Update the backend signing path so it resolves `VisibleSignatureSemantics` once per visible signature and uses:

    semantics.text.stamp_text
    semantics.text.metadata_reason
    semantics.text.metadata_location
    semantics.text.metadata_contact_info

Use those values anywhere the backend currently calls `_build_stamp_text()`, `_visible_reason()`, `_visible_location()`, or `_visible_email()`.

Update backend fit validation so the stamp text passed into layout validation is the same semantics-derived stamp text. Preserve the rendered-fit fallback behavior added during issue #48. Do not change layout reservation policy in this slice.

Keep public `SigningBackendRequest` and `SigningBackendAppearance` stable unless a small compatibility addition is unavoidable. If those DTOs need a new semantics payload, record the reason in this plan before adding it.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/SignPDF/Scratch

Inventory backend semantic helper usage:

    rg -n "_compose_visible_signature_text_layout|_build_stamp_text|_visible_reason|_visible_location|_visible_email|_visible_signature_fit_issues" src/foliaseal/application/phase3_signing_backend.py tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py

Create or update these files:

    src/foliaseal/application/phase3_signing_backend.py
    src/foliaseal/application/visible_signature_semantics.py
    tests/unit/test_phase3_signing_backend.py
    tests/unit/test_visible_signature_semantics.py
    tests/unit/test_signing_preview_renderer.py
    docs/ExecPlans/visible_signature_semantics_backend_migration_execplan.md

Run focused validation:

    .venv/bin/ruff check src/foliaseal/application/phase3_signing_backend.py src/foliaseal/application/visible_signature_semantics.py tests/unit/test_phase3_signing_backend.py tests/unit/test_visible_signature_semantics.py tests/unit/test_signing_preview_renderer.py
    .venv/bin/pytest -q tests/unit/test_visible_signature_semantics.py tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py

Run sign-use-case validation because backend signing remains behind the use case:

    .venv/bin/pytest -q tests/unit/test_sign_pdf_use_case.py tests/unit/test_phase3_signing_backend.py::test_phase3_signing_executor_produces_signed_pdf_and_validates

## Validation and Acceptance

This slice is accepted when final backend signing and backend fit validation use semantics-derived stamp text and metadata text, with no change to signed-output behavior. Existing backend tests for visible signatures, timestamp behavior, wrong password mapping, fit rejection, and rendered-ink fallback must pass.

Add or update tests that prove the backend and preview consume the same semantic stamp text for representative single-line, multi-line, and wrapped-block appearances.

## Idempotence and Recovery

This slice is behavior-preserving but higher risk than earlier slices. Keep compatibility wrappers when they reduce risk. If a backend migration causes signed output or fit validation drift, revert only backend changes from this slice and keep prior foundation/workflow/preview migrations. Do not change GitHub issues, generated artifacts, or layout policy in this slice.

## Artifacts and Notes

If any backend-private text helper remains after this slice, record it in this plan under `Surprises & Discoveries` with evidence and a cleanup owner. The final cleanup plan should not delete helpers unless this plan has moved production use away from them.

## Interfaces and Dependencies

Backend code may depend on the public semantics service and on pyHanko. The semantics core must not depend on backend concrete signing objects unless they are behind a port. The backend may provide a pyHanko-backed adapter that implements the port.

Revision note: Created 2026-05-01 by Codex to define the backend migration slice for issue #50.
