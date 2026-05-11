# Saved Certificate Password Secret Tool Adapter

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, a GUI user importing an existing PKCS#12 certificate can choose to save that certificate password securely when the local Linux Secret Service command-line tool, `secret-tool`, is available. `secret-tool` is a small program from libsecret that stores and retrieves secrets from the desktop credential store rather than from ordinary JSON files. FoliaSeal will save only a secret reference in `certificates.json`; the password itself will not be written to the certificate catalog.

This is a narrow saved-password slice. It does not create self-signed certificates, design a full credential-store abstraction for every operating system, or add a plaintext fallback. If secure storage is unavailable, import still works without saving the password, and trying to save the password fails clearly.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/schema_model_alignment_slice5a_certificate_import_execplan.md` is complete; app-frame import creates `ManagedCertificate` and `CertificateConfiguration` records.
- [x] `docs/ExecPlans/certificate_configuration_management_execplan.md` is complete; app-frame certificate management can delete configurations.
- [x] `docs/ExecPlans/managed_certificate_export_execplan.md` is complete; app-frame certificate management can export/back up managed PKCS#12 files.

## Progress

- [x] (2026-05-10T23:50Z) Reviewed the explorer recommendation, resolver secret-provider seam, import service, app-frame import dialog, schemas, architecture, and dependency list.
- [x] (2026-05-10T23:58Z) Added a concrete `secret-tool` backed secret store that can check availability, save, read, and delete certificate passwords by secret reference.
- [x] (2026-05-10T23:59Z) Extended certificate import so callers can request saved-password storage without writing password material to JSON.
- [x] (2026-05-11T00:05Z) Wired the app frame so import can save a password, the signing shell can read it, and deleting a configuration removes the saved secret when one exists.
- [x] (2026-05-11T00:13Z) Added focused tests for secret store behavior, import saved-password behavior, app-frame import wiring, and configuration-delete cleanup.
- [x] (2026-05-11T00:18Z) Updated architecture and schema-alignment roadmap documentation.
- [x] (2026-05-11T00:14Z) Focused validation passed: `pytest tests/unit/test_secret_storage.py tests/unit/test_certificate_import.py tests/unit/test_qt_app_frame.py`.
- [x] (2026-05-11T00:27Z) Full validation passed: `ruff check .` and `pytest -q` (`619 passed, 23 skipped, 1 warning`).

## Surprises & Discoveries

- Observation: The runtime resolver already supports saved-password reads through `CertificateSecretProvider`.
  Evidence: `src/foliaseal/application/signing_material_resolver.py` calls `secret_provider.get_secret()` when `CertificateConfiguration.save_password` is true.

- Observation: The import path already has the password at the only natural point where the app can save it without asking again.
  Evidence: `src/foliaseal/presentation/qt/app_frame.py` has `CertificateImportDialog` with a passphrase field, and `src/foliaseal/application/certificate_import.py` creates the initial `CertificateConfiguration`.

- Observation: `secret-tool clear` may return `1` when there is no matching secret.
  Evidence: The adapter treats return codes `0` and `1` as successful delete outcomes so deletion is idempotent from the app's perspective.

## Decision Log

- Decision: Use `secret-tool` as the first concrete secure adapter and provide no plaintext fallback.
  Rationale: `docs/SCHEMAS.md` permits OS credential storage or an explicitly supported secure fallback, but forbids ordinary config payload storage. `secret-tool` targets the Linux desktop credential store without adding a Python dependency.
  Date/Author: 2026-05-10 / Codex

- Decision: Save passwords only during import in this slice.
  Rationale: The import dialog already has the certificate password and creates the first configuration. Adding a separate edit-password workflow would be another UI flow and should stay out of this bounded slice.
  Date/Author: 2026-05-10 / Codex

- Decision: Delete saved secrets when deleting a `CertificateConfiguration` that references one.
  Rationale: Once a configuration is removed, its secret reference is no longer reachable from the app. Cleaning it up avoids orphaned certificate passwords in the credential store.
  Date/Author: 2026-05-10 / Codex

## Outcomes & Retrospective

The implementation now provides import-time optional saved-password support backed by the Linux Secret Service through `secret-tool`. `CertificateImportService` stores only `save_password=True` and an opaque `password_secret_ref` in `certificates.json`; the password value is written through `SecretToolCertificateSecretStore`. The app frame passes that same provider to the signing shell and to the certificate import/management dialogs. Deleting a configuration with a saved password deletes the referenced secret before deleting the catalog entry, and leaves the configuration in place if secure storage is unavailable or secret deletion fails.

The slice remains intentionally Linux/Secret Service focused. In-app certificate creation and cross-platform credential-store adapters remain future work.

## Context and Orientation

FoliaSeal stores app-managed certificate metadata in `src/foliaseal/infra/config/schemas.py`. A `CertificateConfiguration` has two saved-password fields: `save_password`, a boolean, and `password_secret_ref`, an opaque reference to a secret outside ordinary JSON. The schema requires `password_secret_ref` when `save_password` is true and requires it to be null when `save_password` is false.

Runtime signing material is resolved in `src/foliaseal/application/signing_material_resolver.py`. `CertificateSigningMaterialResolver` accepts a `CertificateSecretProvider`, which currently needs `is_available()` and `get_secret(secret_ref)`. If a configuration asks to save a password and the provider is missing or unavailable, the resolver raises a helpful `SigningMaterialResolutionError`.

Certificate import is implemented in `src/foliaseal/application/certificate_import.py`. It validates the PKCS#12 file and password, copies the file into managed storage, creates a `ManagedCertificate`, creates a `CertificateConfiguration`, and saves the catalog. The app-frame import UI lives in `src/foliaseal/presentation/qt/app_frame.py`.

`docs/SPEC.md` and `docs/SCHEMAS.md` are frozen without explicit user permission. This slice should use them as requirements but must not edit them.

## Plan of Work

First, add `src/foliaseal/infra/secret_storage.py`. Define a `SecretStorageError` and a `SecretToolCertificateSecretStore`. The store should run `secret-tool` through an injectable runner so tests can avoid touching a real credential store. It should expose `is_available()`, `secret_ref_for_configuration(configuration_id)`, `set_secret(secret_ref, secret)`, `get_secret(secret_ref)`, and `delete_secret(secret_ref)`. Use a stable reference format such as `secret-tool://foliaseal/certificate-password/<configuration_id>`. Store and look up secrets with attributes that include `application=FoliaSeal`, `kind=certificate-password`, and `configuration_id=<id>`.

Second, extend `src/foliaseal/application/certificate_import.py`. Add an optional secret store argument and an import parameter such as `save_password`. When `save_password` is false, preserve current behavior. When it is true, require an available secret store, create the configuration id first, compute its secret reference, save the passphrase to the secret store, and create `CertificateConfiguration(save_password=True, password_secret_ref=<ref>)`. If file copy or catalog save fails after writing the secret, delete the secret before re-raising.

Third, extend `src/foliaseal/presentation/qt/app_frame.py`. Add `q_check_box` to `QtAppFrameBindings` and `CertificateImportDialogControls`. Add a "Save password securely" checkbox to the import dialog. The app frame should create or receive a certificate secret store, pass it into `CertificateImportService`, and pass it as the `certificate_secret_provider` argument when building the signing shell. When deleting a certificate configuration from `CertificateConfigurationManagementDialog`, if it has a saved `password_secret_ref`, delete the secret before or during configuration deletion. If deleting the secret fails, show an error and leave the configuration in place so the user can retry.

Fourth, add focused tests. Add `tests/unit/test_secret_storage.py` for the `secret-tool` adapter command construction, availability, get/set/delete behavior, and missing secret behavior. Update `tests/unit/test_certificate_import.py` so saved-password import sets only the secret reference in JSON, calls the secret store, and cleans up on catalog-save failure. Update `tests/unit/test_qt_app_frame.py` so checking the save-password box stores the password, passes the provider into the loaded shell, and configuration deletion cleans up saved secrets. Update resolver tests only if protocol test fakes need a delete method.

Fifth, update `docs/ARCHITECTURE.md` and the schema-alignment roadmap ExecPlan to describe the `secret-tool` adapter and to remove secure password storage from the pending list while making clear that in-app certificate creation remains pending.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Focused tests while developing:

    .venv/bin/python -m pytest -q tests/unit/test_secret_storage.py tests/unit/test_certificate_import.py tests/unit/test_qt_app_frame.py tests/unit/test_signing_material_resolver.py

Before committing:

    .venv/bin/python -m ruff check .
    .venv/bin/python -m pytest -q

## Validation and Acceptance

This slice is accepted when tests prove that saved-password import writes only a secret reference to `certificates.json`, the password is stored through the secure adapter rather than JSON, the signing shell receives the provider and can resolve saved passwords, and deleting a configuration with a saved password deletes the referenced secret. It is also accepted when imports without the save-password checkbox continue to produce `save_password=False` configurations.

No generated harness artifacts are expected. Full test validation and Ruff must pass before commit.

## Idempotence and Recovery

Import without saved-password storage remains repeatable in temporary test directories. Import with saved-password storage writes a new secret reference based on the new configuration id. If catalog save fails after writing a secret, the import service must delete the secret and copied file before re-raising. Deleting a configuration with a saved password should delete the secret first; if that fails, do not remove the catalog entry.

Do not store passwords in ordinary config JSON. Do not edit `docs/SPEC.md` or `docs/SCHEMAS.md` without explicit user approval.

## Artifacts and Notes

No generated artifacts are expected.

Revision note: Created 2026-05-10 by Codex to implement the first concrete saved-password storage slice after certificate import/export/delete management.
