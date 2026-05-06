# Visible Signature Semantics Backend Migration

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`. It is plan 4 of 5 for GitHub issue #50, "RFC: Deepen visible signature draft semantics boundary." It depends on the foundation, workflow migration, and preview migration plans.

## Purpose / Big Picture

After this slice, final PDF signing will consume the same visible-signature semantic resolution as preview. This means final stamp text and PDF metadata such as reason, location, and contact info will no longer be composed by separate backend-private rules. Users should see the same visible signature content in preview and signed output, and tests should prove that parity at the semantic boundary.

## Progress

- [x] (2026-05-01T18:19Z) Created this ExecPlan as the fourth issue #50 slice.
- [x] (2026-05-01T19:14Z) Confirmed preview migration is complete and semantics-derived stamp text is available on `SigningDraftPreview.stamp_text`.
- [x] (2026-05-01T19:14Z) Added backend-local pyHanko signer and fixed-clock adapters for `VisibleSignatureSemanticsService`.
- [x] (2026-05-01T19:14Z) Migrated final signing stamp text and PDF metadata derivation to the semantics boundary.
- [x] (2026-05-01T19:14Z) Migrated backend fit validation to use the same semantics-derived stamp text.
- [x] (2026-05-01T19:14Z) Preserved existing signing output behavior and failure-code mapping.
- [x] (2026-05-01T19:14Z) Ran backend, preview, and sign-use-case validation and recorded results here.
- [x] (2026-05-01T21:40Z) Commit this backend migration slice.
- [x] (2026-05-01T21:43Z) Began the cleanup plan.

## Surprises & Discoveries

- Observation: `_build_stamp_text()`, `_visible_reason()`, `_visible_location()`, and `_visible_email()` can stay as backend compatibility wrappers.
  Evidence: production signing now resolves semantics once in `PyHankoPdfSigner.sign()`, while these private helpers delegate to `_resolve_visible_signature_semantics()` for direct tests or transitional callers.

- Observation: The backend still needs a pyHanko-specific certificate-field adapter.
  Evidence: `_PyHankoSignerCertificateFieldReader` converts `SimpleSigner.signing_cert.subject.native` into the field map expected by `VisibleSignatureSemanticsService`; this keeps the semantics core free of pyHanko imports.

- Observation: The old backend text-layout dataclass and composition helper are now dead code.
  Evidence: `rg -n "_compose_visible_signature_text_layout|VisibleSignatureTextLayout" src/foliaseal/application/phase3_signing_backend.py` shows definitions only. The cleanup plan should remove them after this slice is committed.

## Decision Log

- Decision: migrate backend signing after workflow and preview.
  Rationale: backend signing is the highest-risk production path. By migrating it after preview, the codebase already has a semantics boundary and preview parity tests to compare against.
  Date/Author: 2026-05-01 / Codex

- Decision: keep pyHanko style construction outside the semantics service.
  Rationale: semantics should decide text and metadata. `phase3_signing_backend.py` and the visible layout boundary still own pyHanko stamp style construction and signed PDF output.
  Date/Author: 2026-05-01 / Codex

- Decision: keep the pyHanko signer-to-field adapter backend-local.
  Rationale: the adapter depends on `SimpleSigner.signing_cert.subject.native`; moving it into `visible_signature_semantics.py` would make the application semantics boundary depend on concrete pyHanko signing objects.
  Date/Author: 2026-05-01 / Codex

- Decision: resolve final-signing semantics once per signing operation before fit validation and stamp style construction.
  Rationale: a single semantics payload makes fit validation, visible stamp text, and PDF metadata share the same timestamp and certificate-derived values.
  Date/Author: 2026-05-01 / Codex

## Outcomes & Retrospective

Final PDF signing now consumes `VisibleSignatureSemanticsService` for visible stamp text and PDF metadata. `PyHankoPdfSigner.sign()` loads the signer, captures one signing time, resolves final-signing semantics, validates layout fit with `semantics.text.stamp_text`, builds the pyHanko stamp style with the same text, and passes `semantics.text.metadata_reason`, `metadata_location`, and `metadata_contact_info` into `PdfSignatureMetadata`.

The backend-private `_build_stamp_text()`, `_visible_reason()`, `_visible_location()`, and `_visible_email()` helpers were retained as compatibility wrappers and now delegate to semantic resolution. The pyHanko style/layout helpers remain backend-owned.

Validation completed:

    .venv/bin/ruff check src/foliaseal/application/phase3_signing_backend.py src/foliaseal/application/visible_signature_semantics.py tests/unit/test_phase3_signing_backend.py tests/unit/test_visible_signature_semantics.py tests/unit/test_signing_preview_renderer.py
    All checks passed.

    .venv/bin/pytest -q tests/unit/test_phase3_signing_backend.py::test_backend_visible_semantics_resolve_stamp_text_and_metadata tests/unit/test_phase3_signing_backend.py::test_visible_signature_fit_issues_use_semantics_stamp_text
    2 passed in 0.40s.

    .venv/bin/pytest -q tests/unit/test_visible_signature_semantics.py tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py
    154 passed in 25.26s.

    .venv/bin/pytest -q tests/unit/test_sign_pdf_use_case.py tests/unit/test_phase3_signing_backend.py::test_phase3_signing_executor_produces_signed_pdf_and_validates
    22 passed in 0.42s.

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

    cd /home/daekar/FoliaSeal

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
