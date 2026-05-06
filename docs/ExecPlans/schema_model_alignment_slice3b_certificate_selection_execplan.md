# Wire Certificate Configuration Selection Into the Qt Signing Shell

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows `.agents/skills/write-execplan/PLANS.md` and is a child plan of `docs/ExecPlans/schema_model_alignment_execplan.md`.

## Purpose / Big Picture

This slice lets the Qt signing shell use a saved `CertificateConfiguration` as the user's signing identity instead of treating a raw PKCS#12 path and passphrase as the only available workflow identity. A user-visible certificate selector appears in the signing properties panel when certificate configurations exist. Selecting a configuration and applying it resolves the app-managed certificate file plus either a typed password or a saved-password provider into the runtime fields the current signing backend still needs.

This is not certificate creation, import, export, backup, deletion, or credential-store implementation. It is the narrow wiring slice that proves the canonical certificate object model can drive the existing signing request path.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/schema_model_alignment_slice1_profiles_execplan.md` split reusable appearance, placement, and preset persistence.
- [x] `docs/ExecPlans/schema_model_alignment_slice2_certificates_execplan.md` added `ManagedCertificate`, `CertificateConfiguration`, `CertificateCatalogStore`, and `CertificateSigningMaterialResolver`.
- [x] `docs/ExecPlans/schema_model_alignment_slice3_draft_references_execplan.md` added selected reusable-object ids and canonical draft apply/capture methods.

## Progress

- [x] (2026-05-06 23:02Z) Confirmed the parent ExecPlan's next unfinished slice is Qt shell certificate-configuration wiring.
- [x] (2026-05-06 23:05Z) Inspected the Qt shell profile controls, fake Qt widgets, certificate catalog store, signing-material resolver, and architecture notes.
- [x] (2026-05-06 23:18Z) Added focused workflow tests for applying resolved certificate material to a draft.
- [x] (2026-05-06 23:20Z) Added focused Qt shell tests for selecting a certificate configuration, resolving material, and surfacing helpful resolver errors.
- [x] (2026-05-06 23:23Z) Implemented the draft workflow method and Qt shell certificate selector.
- [x] (2026-05-06 23:28Z) Updated architecture and parent/child ExecPlan documentation.
- [x] (2026-05-06 23:26Z) Ran focused validation and lint successfully.
- [x] (2026-05-06 23:31Z) Ran the full test suite successfully.
- [x] (2026-05-06 23:33Z) Committed the completed slice as `47a51f0bf feat: wire certificate configuration selection`.

## Surprises & Discoveries

- Observation: The fake Qt test bindings already support `QComboBox`, `QLineEdit`, and `QPushButton`, so a compact certificate selector can be tested without adding live GUI dependencies.
  Evidence: `tests/unit/test_qt_signing_shell.py` defines `_FakeComboBox`, `_FakeLineEdit`, and `_FakePushButton`.

- Observation: `SigningDraftWorkflow` already records `selected_certificate_configuration_id`, but there is no method that applies a resolved `CertificateConfiguration` and clears certificate-preview cache state.
  Evidence: `src/foliaseal/application/signing_draft_workflow.py` includes `selected_certificate_configuration_id`, while certificate path/passphrase updates currently happen only through construction or raw field mutation.

- Observation: At the start of this slice, the architecture document still identified certificate configuration UI wiring as pending.
  Evidence: before this slice's architecture update, `docs/ARCHITECTURE.md` said certificate configuration persistence was not wired into the Qt shell yet and recommended refactoring draft workflow and shell certificate selection to use `CertificateConfiguration` references.

- Observation: Focused validation is green after the selector implementation.
  Evidence: `.venv/bin/pytest -q tests/unit/test_signing_draft_workflow.py tests/unit/test_qt_signing_shell.py tests/unit/test_certificate_storage.py tests/unit/test_signing_material_resolver.py` reported `85 passed in 4.26s`, and `.venv/bin/ruff check .` reported `All checks passed!`.

- Observation: Full-suite validation remains green after the Qt certificate selector.
  Evidence: `.venv/bin/pytest -q` reported `586 passed, 1 warning in 37.56s`.

## Decision Log

- Decision: Implement certificate selection as a small properties-panel selector with an optional password entry and explicit Apply button.
  Rationale: The resolver may require a password, so auto-applying on combo selection would either fail noisily or force awkward hidden state. An explicit button keeps the UX familiar and keeps this slice below full certificate management.
  Date/Author: 2026-05-06 / Codex

- Decision: Keep raw `SigningRequest.certificate_path` and `SigningRequest.passphrase` as the backend runtime payload in this slice.
  Rationale: The current signing backend already requires those fields. The schema-alignment goal for this slice is to resolve canonical certificate configuration objects into those runtime inputs, not to redesign the signing backend.
  Date/Author: 2026-05-06 / Codex

- Decision: Do not add create/import/export/delete certificate controls in this slice.
  Rationale: The user requirements include those capabilities, but they belong to certificate management. This slice is only the bridge from persisted certificate configurations to the existing signing shell.
  Date/Author: 2026-05-06 / Codex

## Outcomes & Retrospective

The implementation adds the narrow bridge this plan targeted. Tests can build a certificate catalog, point the shell at a managed certificate file, select a configuration, enter a password, apply it, and see the draft workflow use the resolved path, passphrase, and selected certificate-configuration id. The workflow can also build a final signing request with resolved certificate material. Full certificate-management UX remains future work.

## Context and Orientation

The repository root is `/home/daekar/FoliaSeal`. The Qt signing shell lives in `src/foliaseal/presentation/qt/signing_shell.py`. Its `SignaturePropertiesPanel` currently owns profile controls, appearance controls, placement controls, field visibility controls, preview controls, and validation output. The shell factory `build_qt_signing_shell()` creates a `SigningWorkspaceWidget`, which creates the `SignaturePropertiesPanel`.

The draft workflow lives in `src/foliaseal/application/signing_draft_workflow.py`. A draft workflow is the mutable application object for one currently open signing session. It can build a `SigningRequest`, and for now that runtime request still contains `certificate_path`, `passphrase`, and optional `certificate_alias`.

Certificate configuration persistence lives in `src/foliaseal/infra/config/schemas.py` and `src/foliaseal/infra/config/certificate_storage.py`. A `ManagedCertificate` records an app-owned PKCS#12 file in the app's managed certificate directory. A `CertificateConfiguration` is the user-facing signing identity object that points at a managed certificate and records whether its password should be retrieved from a secret provider.

Runtime certificate resolution lives in `src/foliaseal/application/signing_material_resolver.py`. `CertificateSigningMaterialResolver.resolve_by_configuration_id()` accepts a `CertificateCatalog`, a configuration id, and either an explicit password or a `CertificateSecretProvider`. It returns `SigningMaterial`, which contains the runtime certificate path, passphrase, and optional alias.

## Plan of Work

First, add an application-level test in `tests/unit/test_signing_draft_workflow.py` that builds a `CertificateConfiguration` and a `SigningMaterial`, applies them to a draft workflow, and proves that `build_signing_request()` uses the resolved material. This test should also prove the selected certificate-configuration id is recorded.

Second, add Qt shell tests in `tests/unit/test_qt_signing_shell.py`. One test should create a temporary `CertificateCatalogStore`, save a catalog containing one managed certificate and one certificate configuration, write a dummy PKCS#12 file to the store's managed directory, build the shell with that store, choose the configuration in the properties panel, enter a password, apply it, and verify that the workflow and signing request use the resolved material. Another test should build a catalog whose managed certificate file is missing and verify that applying the configuration reports a helpful error instead of crashing.

Third, update `src/foliaseal/application/signing_draft_workflow.py` with a method named `apply_certificate_configuration(configuration, signing_material)`. It should set `selected_certificate_configuration_id`, `certificate_path`, `passphrase`, and `certificate_alias`, then clear certificate-preview cache state so future previews reflect the newly selected certificate.

Fourth, update `src/foliaseal/presentation/qt/signing_shell.py` to accept optional certificate catalog dependencies through `SignaturePropertiesPanel`, `SigningWorkspaceWidget`, `SigningShellAdapter.create()`, and `build_qt_signing_shell()`. The properties panel should create a compact `Certificate configuration` group before the appearance/profile controls. It should load configuration display names into a combo box, allow a password to be typed, and apply the selected configuration through `CertificateSigningMaterialResolver`. Resolver failures should be reported through the existing error path and warning message box.

Fifth, update `docs/ARCHITECTURE.md`, this child ExecPlan, and the parent schema-alignment ExecPlan to reflect that the shell now consumes certificate configurations for signing material while full certificate management and OS credential storage remain pending.

## Concrete Steps

Run commands from `/home/daekar/FoliaSeal`.

Focused iteration should run:

    .venv/bin/pytest -q tests/unit/test_signing_draft_workflow.py tests/unit/test_qt_signing_shell.py tests/unit/test_certificate_storage.py tests/unit/test_signing_material_resolver.py

Before committing, run:

    .venv/bin/ruff check .
    .venv/bin/pytest -q

Expected successful output is all focused tests passing, ruff reporting `All checks passed!`, and the full pytest suite passing.

Output observed on 2026-05-06:

    .venv/bin/pytest -q tests/unit/test_signing_draft_workflow.py tests/unit/test_qt_signing_shell.py tests/unit/test_certificate_storage.py tests/unit/test_signing_material_resolver.py
    85 passed in 4.26s

    .venv/bin/ruff check .
    All checks passed!

    .venv/bin/pytest -q
    586 passed, 1 warning in 37.56s

## Validation and Acceptance

This slice is accepted when a test can build the Qt shell with a `CertificateCatalogStore`, select a saved certificate configuration, enter a password, apply it, and then observe that `SigningDraftWorkflow.build_signing_request()` contains the managed certificate file path, typed or saved passphrase, and selected certificate-configuration id.

It is also accepted only if resolver errors remain graceful. A missing managed certificate file must produce a helpful message through the shell error path rather than an uncaught exception.

## Idempotence and Recovery

The changes are source, tests, and documentation only. No generated artifacts should be committed. If a partial implementation breaks broad shell tests, keep the new draft method and constructor parameters but make the certificate controls optional when no catalog/store is supplied. Re-running tests is safe because certificate files in this plan are temporary files under pytest's `tmp_path`.

## Artifacts and Notes

No external artifacts are part of this slice. Test-created dummy certificate files are temporary and should never be committed.

## Interfaces and Dependencies

At the end of this slice, these interfaces should exist or be updated:

- `SigningDraftWorkflow.apply_certificate_configuration(configuration: CertificateConfiguration, signing_material: SigningMaterial) -> None`
- `SignaturePropertiesPanel(..., certificate_catalog: CertificateCatalog | None = None, certificate_catalog_store: CertificateCatalogStore | None = None, certificate_secret_provider: CertificateSecretProvider | None = None, ...)`
- `SigningWorkspaceWidget(..., certificate_catalog: CertificateCatalog | None = None, certificate_catalog_store: CertificateCatalogStore | None = None, certificate_secret_provider: CertificateSecretProvider | None = None, ...)`
- `SigningShellAdapter.create(..., certificate_catalog: CertificateCatalog | None = None, certificate_catalog_store: CertificateCatalogStore | None = None, certificate_secret_provider: CertificateSecretProvider | None = None, ...)`
- `build_qt_signing_shell(..., certificate_catalog: CertificateCatalog | None = None, certificate_catalog_store: CertificateCatalogStore | None = None, certificate_secret_provider: CertificateSecretProvider | None = None, ...)`

No new third-party dependencies are needed.

Revision note: created on 2026-05-06 to keep schema-alignment Slice 3B focused on certificate-configuration selection and runtime material resolution.

Revision note: updated on 2026-05-06 after implementation to record the draft method, Qt selector, focused tests, architecture update, and validation evidence.

Revision note: updated on 2026-05-06 after commit to record commit `47a51f0bf` in the progress checklist.
