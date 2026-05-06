# Add Certificate Configuration Persistence and Resolution

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows `.agents/skills/write-execplan/PLANS.md` and is a child plan of `docs/ExecPlans/schema_model_alignment_execplan.md`.

## Purpose / Big Picture

This slice adds the next canonical reusable signing object family from `docs/SCHEMAS.md`: `ManagedCertificate` and `CertificateConfiguration`. After this change, FoliaSeal will have tested persisted certificate records and a resolver seam that can convert a selected certificate configuration into the runtime certificate path and passphrase currently required by the signing backend. This lets future UI work select a named certificate configuration instead of treating raw certificate paths and passwords as the product-level identity model.

The user-visible workflow is not complete certificate management yet. The observable outcome is developer-facing but high leverage: focused tests can create a managed certificate catalog, save/load it as human-readable JSON, resolve a certificate configuration to signing material, fail gracefully when the managed certificate file is missing, and avoid storing certificate passwords directly in ordinary config JSON.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/schema_model_alignment_slice1_profiles_execplan.md` split appearance, placement, and signature preset persistence.
- [x] `docs/ExecPlans/artifact_fixture_test_reconciliation_execplan.md` restored a green full-suite baseline before this slice.

## Progress

- [x] (2026-05-06 22:24Z) Inspected `docs/SCHEMAS.md`, `docs/SPEC.md`, `docs/ARCHITECTURE.md`, current config schemas/storage, and profile-storage tests.
- [x] (2026-05-06 22:27Z) Added focused tests for certificate schema round trips, duplicate validation, storage load/save behavior, and signing-material resolution.
- [x] (2026-05-06 22:29Z) Implemented certificate schema dataclasses and JSON catalog storage.
- [x] (2026-05-06 22:29Z) Implemented signing-material resolver with a secret-store seam and helpful failure behavior.
- [x] (2026-05-06 22:30Z) Updated architecture and parent ExecPlan documentation.
- [x] (2026-05-06 22:32Z) Ran focused validation, lint, and the full test suite successfully.
- [ ] Commit the completed slice.

## Surprises & Discoveries

- Observation: `SignaturePreset` already has an optional `certificate_configuration_id` field from Slice 1, so this slice can add the referenced object family without changing the preset shape.
  Evidence: `src/foliaseal/infra/config/schemas.py` defines `SignaturePreset(certificate_configuration_id: str | None = None, ...)`.

- Observation: runtime signing still correctly uses raw `certificate_path` and `passphrase` as an internal backend payload.
  Evidence: `src/foliaseal/domain/models.py` defines `SigningRequest(certificate_path, passphrase, ...)`, and the parent ExecPlan explicitly says this can remain usable as an internal runtime payload.

- Observation: The full suite remains green after adding certificate persistence and resolution.
  Evidence: `.venv/bin/pytest -q` reported `581 passed, 1 warning in 37.26s`; `.venv/bin/ruff check .` reported `All checks passed!`.

## Decision Log

- Decision: Add certificate persistence as a separate catalog/store rather than folding it into `SignaturePresetCatalog`.
  Rationale: `ManagedCertificate` and `CertificateConfiguration` have different lifecycle rules from appearance/placement/preset objects. The user said certificate configurations support create/save/rename/edit/delete and managed certificates support export/backup/deletion, so they should not be coupled to signature profile catalog saves.
  Date/Author: 2026-05-06 / Codex

- Decision: Keep password material out of JSON and model password access through a resolver-side secret provider.
  Rationale: `docs/SCHEMAS.md` says certificate passwords must not be stored as plain text in ordinary configuration files. A resolver seam lets future GUI work use an OS credential store while tests can use an in-memory provider.
  Date/Author: 2026-05-06 / Codex

- Decision: Do not implement certificate creation/import/export GUI in this slice.
  Rationale: The next architectural dependency is the persisted object and resolver contract. Certificate creation/import/export requires UI and file-copy flows that should be a separate user-visible slice after the schema model exists.
  Date/Author: 2026-05-06 / Codex

## Outcomes & Retrospective

Completed the slice. The implementation now has canonical persisted certificate records in `src/foliaseal/infra/config/schemas.py`, human-readable certificate catalog storage in `src/foliaseal/infra/config/certificate_storage.py`, and a resolver seam in `src/foliaseal/application/signing_material_resolver.py` that turns a selected `CertificateConfiguration` into runtime signing material. Tests prove that passwords are not stored in ordinary JSON, saved-password configurations reference a secret id, explicit passphrases work for unsaved-password configurations, and missing managed certificate files or unavailable saved-password storage fail with helpful errors.

The slice deliberately stops short of wiring certificate configurations into the Qt shell or implementing import/create/export/delete GUI flows. Those are now better-scoped follow-up slices because they can build on a tested persistence/resolution contract.

## Context and Orientation

The repository root is `/home/daekar/FoliaSeal`. Canonical schema intent lives in `docs/SCHEMAS.md`. The existing reusable signing-object schemas live in `src/foliaseal/infra/config/schemas.py`, and profile catalog storage lives in `src/foliaseal/infra/config/profile_storage.py`. Runtime signing still expects a domain `SigningRequest` with `certificate_path`, `passphrase`, and optional `certificate_alias`; this slice does not change that backend contract.

A `ManagedCertificate` is the app-owned certificate file record. It points to a file name inside a controlled application data directory and contains non-secret summary metadata. A `CertificateConfiguration` is the user-facing selection object that points at a managed certificate and records whether the user chose to save the password. The password itself must live outside ordinary JSON config.

## Plan of Work

First, extend `src/foliaseal/infra/config/schemas.py` with `ManagedCertificateSubjectSummary`, `ManagedCertificate`, `CertificateConfiguration`, and `CertificateCatalog`. Follow the existing dataclass style: validate in `__post_init__`, provide `from_dict()` and `to_dict()`, reject duplicate ids, and reject duplicate certificate configuration display names.

Second, add `src/foliaseal/infra/config/certificate_storage.py`. It should mirror `SignaturePresetCatalogStore` conventions: default to `${XDG_DATA_HOME:-~/.local/share}/FoliaSeal/Certificates`, load empty catalogs when missing or blank, write indented sorted JSON through a temp file, and expose helper methods to save/delete configurations. It should also expose the managed certificate files directory so resolver code has one authoritative root for `storage_filename`.

Third, add `src/foliaseal/application/signing_material_resolver.py`. This module should define a small immutable `SigningMaterial` DTO, a `CertificateSecretProvider` protocol, and `CertificateSigningMaterialResolver`. The resolver should take a `CertificateCatalog`, a selected `CertificateConfiguration`, a managed certificate storage directory, and either an explicit passphrase or a secret provider. It should return the runtime certificate path/passphrase pair required by current signing. It should raise a typed application error with helpful messages for missing managed certificates, missing certificate files, unavailable saved-password storage, or absent passphrases.

Fourth, add focused tests in `tests/unit/test_config_schemas.py`, a new `tests/unit/test_certificate_storage.py`, and a new `tests/unit/test_signing_material_resolver.py`. Tests should prove password values do not appear in persisted JSON, missing files fail gracefully, explicit passphrases can be supplied when `save_password` is false, and saved-password configurations use the secret provider by reference.

Fifth, update `docs/ARCHITECTURE.md` and the parent `docs/ExecPlans/schema_model_alignment_execplan.md` to record Slice 2 completion and the new certificate persistence/resolver boundary.

## Concrete Steps

Run commands from `/home/daekar/FoliaSeal`.

Focused iteration:

    .venv/bin/pytest -q tests/unit/test_config_schemas.py tests/unit/test_certificate_storage.py tests/unit/test_signing_material_resolver.py

    Output observed on 2026-05-06:

        34 passed in 0.25s

Broader regression:

    .venv/bin/ruff check .
    .venv/bin/pytest -q

    Output observed on 2026-05-06:

        All checks passed!
        581 passed, 1 warning in 37.26s

Expected focused evidence after implementation:

    tests/unit/test_config_schemas.py includes ManagedCertificate and CertificateConfiguration round-trip coverage.
    tests/unit/test_certificate_storage.py proves human-readable JSON storage and no plain password persistence.
    tests/unit/test_signing_material_resolver.py proves runtime signing material resolution and graceful missing-file/secret errors.

## Validation and Acceptance

This slice is accepted when code has canonical `ManagedCertificate` and `CertificateConfiguration` persistence types, a human-readable certificate catalog store, and a resolver seam that produces runtime signing material without storing passwords in ordinary config JSON. The focused tests, lint, and full unit suite must pass.

The implementation must not change `docs/SCHEMAS.md` or `docs/SPEC.md` because both are frozen. If implementation discovers an impossible requirement, stop and ask the user before changing those documents.

## Idempotence and Recovery

The changes are additive and safe to retry. The storage tests use temporary directories. The resolver should never delete certificate files. If a test fails after a partial edit, fix the schema/store/resolver and rerun the focused tests; do not add compatibility shims for old local certificate configuration files because V1 explicitly deprioritizes backward compatibility.

## Artifacts and Notes

No generated artifacts should be committed. This slice should only touch source, tests, and documentation.

## Interfaces and Dependencies

Expected new interfaces:

- `ManagedCertificateSubjectSummary`, `ManagedCertificate`, `CertificateConfiguration`, and `CertificateCatalog` in `src/foliaseal/infra/config/schemas.py`.
- `CertificateCatalogStore` and `default_certificate_config_directory()` in `src/foliaseal/infra/config/certificate_storage.py`.
- `SigningMaterial`, `CertificateSecretProvider`, `CertificateSigningMaterialResolver`, and `SigningMaterialResolutionError` in `src/foliaseal/application/signing_material_resolver.py`.

No new third-party dependency is justified in this slice. A real OS credential store adapter can be added later behind the `CertificateSecretProvider` protocol.

Revision note: updated on 2026-05-06 after implementation to record the certificate catalog, signing-material resolver, documentation updates, and successful validation evidence.
