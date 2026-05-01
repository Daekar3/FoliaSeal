# Visible Signature Semantics Boundary Foundation

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`. It is plan 1 of 5 for GitHub issue #50, "RFC: Deepen visible signature draft semantics boundary." The five plans are:

1. `docs/ExecPlans/visible_signature_semantics_foundation_execplan.md`
2. `docs/ExecPlans/visible_signature_semantics_workflow_migration_execplan.md`
3. `docs/ExecPlans/visible_signature_semantics_preview_migration_execplan.md`
4. `docs/ExecPlans/visible_signature_semantics_backend_migration_execplan.md`
5. `docs/ExecPlans/visible_signature_semantics_cleanup_execplan.md`

## Purpose / Big Picture

After this slice, FoliaSeal will have a new application-layer module that can answer one question consistently: "what visible signature fields, text, metadata, and fit issues does this draft imply?" A visible signature is the rectangle of text and optional stamp image shown on the signed PDF. Today the draft workflow, preview renderer, and backend signing code each know part of this answer. This first slice adds the boundary and tests without changing production callers, so later migrations can be small and behavior-preserving.

## Progress

- [x] (2026-05-01T18:19Z) Created this ExecPlan from GitHub issue #50 and split the overall work into five independently verifiable plans.
- [x] (2026-05-01T18:36Z) Added `src/foliaseal/application/visible_signature_semantics.py` with public data types, ports, default no-op/local adapters, and a behavior-preserving resolver.
- [x] (2026-05-01T18:36Z) Added deterministic boundary tests covering preview field resolution, certificate fallback, signing-time formatting, single-line/multi-line/wrapped-block text composition, percent escaping, metadata derivation, final-signing fallback behavior, and fit-validator propagation.
- [x] (2026-05-01T18:36Z) Exported the new boundary from `src/foliaseal/application/__init__.py`.
- [x] (2026-05-01T18:36Z) Ran focused validation and adjacent workflow/preview/backend validation successfully.
- [ ] Next slice: execute `docs/ExecPlans/visible_signature_semantics_workflow_migration_execplan.md` to move `SigningDraftWorkflow` onto the new boundary.

## Surprises & Discoveries

- Observation: No implementation work has started.
  Evidence: this plan was created before code edits for issue #50.

- Observation: `SignatureAppearance` shows `SIGNING_TIME` by default.
  Evidence: the first `test_visible_signature_semantics.py` run failed two tests because default appearances included the fixed signing time in `detail_text` and fit-validator `stamp_text`. The tests were corrected to hide signing time where they were only asserting certificate-field behavior.

## Decision Log

- Decision: split issue #50 into five ExecPlans instead of one.
  Rationale: issue #50 crosses semantic resolution, draft workflow, canonical preview rendering, backend signing, and cleanup. Each has different risk and tests. Splitting keeps commits narrow and makes it possible to stop after any slice with a working repository.
  Date/Author: 2026-05-01 / Codex

- Decision: this first slice must not migrate production callers.
  Rationale: adding the boundary and proving behavior with fakes creates a stable target before changing `SigningDraftWorkflow`, `signing_preview_renderer.py`, or `phase3_signing_backend.py`.
  Date/Author: 2026-05-01 / Codex

## Outcomes & Retrospective

The foundation slice succeeded.

What changed:

- Added `src/foliaseal/application/visible_signature_semantics.py`.
- Added `CertificateFieldReader`, `SigningClock`, and `VisibleSignatureFitValidator` ports so tests and later production adapters can provide certificate values, timestamps, and fit issues without coupling the core semantic resolver to local files, Qt, pyHanko signing, PDF rendering, or image loading.
- Added `VisibleSignatureSemanticsService.resolve()` to produce resolved fields, `detail_text`, escaped `stamp_text`, metadata values for reason/location/contact info, fit issues, and a readiness boolean.
- Added default `UnavailableCertificateFieldReader`, `SystemSigningClock`, and `NoopVisibleSignatureFitValidator` adapters for additive use before production migration.
- Added `tests/unit/test_visible_signature_semantics.py` with in-memory fake ports.
- Exported the public boundary from `src/foliaseal/application/__init__.py`.

What did not change:

- `SigningDraftWorkflow.preview()` still uses the existing workflow/backend helper path.
- `signing_preview_renderer.py` still has its existing `_preview_stamp_text()` path.
- `phase3_signing_backend.py` still owns final signing stamp text and metadata helpers.
- No production caller was migrated in this slice.

Verification results:

    .venv/bin/ruff check src/foliaseal/application/visible_signature_semantics.py src/foliaseal/application/__init__.py tests/unit/test_visible_signature_semantics.py
    All checks passed!

    .venv/bin/pytest -q tests/unit/test_visible_signature_semantics.py
    5 passed in 0.21s

    .venv/bin/pytest -q tests/unit/test_signing_draft_workflow.py tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_signing_backend.py
    157 passed in 27.84s

## Context and Orientation

The current signing draft flow lives in `src/foliaseal/application/signing_draft_workflow.py`. A signing draft is the in-memory state the Qt UI edits before producing a final `SigningRequest`. The draft currently builds a `SigningDraftPreview`, reads PKCS#12 certificate fields for preview, formats signing-time text, validates the selected rectangle, and imports backend-private helpers from `src/foliaseal/application/phase3_signing_backend.py` to compose visible text and validate layout fit.

The preview renderer lives in `src/foliaseal/application/signing_preview_renderer.py`. It consumes `SigningDraftPreview` and also has `_preview_stamp_text()`, which independently reconstructs the text used for canonical preview rendering.

The signing backend lives in `src/foliaseal/application/phase3_signing_backend.py`. It signs PDFs through pyHanko and owns private helpers such as `_compose_visible_signature_text_layout()`, `_visible_reason()`, `_visible_location()`, and `_visible_email()`. These helpers determine final signed visible text and PDF metadata.

The backend-facing appearance DTO is `SigningBackendAppearance` in `src/foliaseal/application/sign_pdf_use_case.py`. A DTO is a data transfer object: a plain object used to pass normalized data between layers. It is currently reused by backend, preview, and layout code.

The new boundary should live in `src/foliaseal/application/visible_signature_semantics.py`. A "semantic" value means meaning-level data such as visible fields, detail text, final stamp text, and metadata values. It is not rendering, Qt widgets, PDF writing, or pyHanko style construction.

## Plan of Work

Create `src/foliaseal/application/visible_signature_semantics.py`. Define immutable dataclasses for certificate values, a request, resolved fields, resolved text, a fit-validation request, and the final semantics result. Define small protocol ports so tests can provide deterministic stand-ins:

    class CertificateFieldReader(Protocol):
        def read_fields(self, certificate_path: str, passphrase: str) -> CertificateFieldValues: ...

    class SigningClock(Protocol):
        def now(self, mode: SignatureTimezoneDisplayMode) -> datetime: ...

    class VisibleSignatureFitValidator(Protocol):
        def validate(self, request: VisibleSignatureFitRequest) -> tuple[SigningDraftValidationIssue, ...]: ...

The resolver should be named `VisibleSignatureSemanticsService`. Its public method should be:

    def resolve(self, request: VisibleSignatureSemanticsRequest) -> VisibleSignatureSemantics: ...

The first implementation may copy the current pure rules from `SigningDraftWorkflow` and `phase3_signing_backend.py` where needed. Copying is acceptable in this first slice because production callers are not yet migrated. Do not delete the old helpers yet.

The resolver must own these behaviors:

- field labels for all `SignatureFieldKey` values;
- hidden field and `show_in_visible_appearance` handling;
- override text handling;
- certificate-derived field lookup and fallback label behavior when the certificate is unavailable;
- signing-time formatting using the injected `SigningClock`;
- body fragment construction with or without field names;
- detail text and stamp text composition for `SINGLE_LINE`, `MULTI_LINE`, and `WRAPPED_BLOCK`;
- percent escaping for pyHanko stamp text;
- metadata text values for reason, location, and contact info;
- fit issue propagation from `VisibleSignatureFitValidator` using the same resolved stamp text.

Add `tests/unit/test_visible_signature_semantics.py`. Use in-memory fake ports for certificate fields, clock, and fit validation. Do not read real certificates or images in the boundary tests. A small production adapter test for PKCS#12 may be added here only if a production certificate reader is implemented in this slice.

Update `src/foliaseal/application/__init__.py` to export only the public boundary types that callers should use. Avoid exporting internal helpers.

Do not change `SigningDraftWorkflow.preview()`, `signing_preview_renderer.py`, or `phase3_signing_backend.py` in this slice except for imports needed by tests. Those migrations belong to later ExecPlans.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/SignPDF/Scratch

Inspect the current behavior before editing:

    rg -n "_field_label|_preview_signing_time|_compose_visible_signature_text_layout|_visible_reason|_visible_location|_visible_email|_preview_stamp_text" src/foliaseal/application tests/unit

Create or update these files:

    src/foliaseal/application/visible_signature_semantics.py
    src/foliaseal/application/__init__.py
    tests/unit/test_visible_signature_semantics.py
    docs/ExecPlans/visible_signature_semantics_foundation_execplan.md

Run focused checks:

    .venv/bin/ruff check src/foliaseal/application/visible_signature_semantics.py src/foliaseal/application/__init__.py tests/unit/test_visible_signature_semantics.py
    .venv/bin/pytest -q tests/unit/test_visible_signature_semantics.py

Then run adjacent existing tests to prove no production behavior changed:

    .venv/bin/pytest -q tests/unit/test_signing_draft_workflow.py tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_signing_backend.py

## Validation and Acceptance

This slice is accepted when `test_visible_signature_semantics.py` proves that the new service can resolve fields, detail text, escaped stamp text, metadata text, and fit issues without Qt, pyHanko signing, PDF rendering, or local image files. Existing signing draft, preview renderer, and backend tests must still pass because production callers have not changed.

The observable behavior is internal but demonstrable: a fake certificate reader returning a common name, email, title, company, and location should produce the same visible field text and stamp text that the current workflow/backend rules produce.

## Idempotence and Recovery

This slice is additive and safe to retry. If a partial implementation fails, remove only `src/foliaseal/application/visible_signature_semantics.py`, its exports from `src/foliaseal/application/__init__.py`, and `tests/unit/test_visible_signature_semantics.py`. Do not modify generated artifacts. Avoid destructive git commands.

## Artifacts and Notes

GitHub issue #50 is the parent RFC. Issue #48 created `src/foliaseal/application/visible_signature_layout.py`; this new semantics module is related but separate. Layout decides how text and stamps fit in a rectangle. Semantics decides what the text and metadata are.

## Interfaces and Dependencies

The module must import domain types from `src/foliaseal/domain/models.py` and validation issue types from `src/foliaseal/application/signing_draft_workflow.py` unless those issue types are moved in a later cleanup. It may import `SigningBackendAppearance` from `src/foliaseal/application/sign_pdf_use_case.py` for compatibility during the transition.

The module must not import Qt, instantiate pyHanko signers, render PDFs, write files, or call timestamp services. Production adapters may use cryptography or pyHanko later, but the core boundary tests should use in-memory fake ports.

Revision note: Created 2026-05-01 by Codex to define the first, additive boundary slice for issue #50.
