# In-App Certificate Creation

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, a FoliaSeal GUI user can create a basic self-signed signing certificate from inside the app instead of bringing an existing PKCS#12 file from another tool. The user-visible flow is intentionally small: `Settings > Create certificate...` opens a dialog asking for a display name, a certificate password, and whether to save that password securely. On success, FoliaSeal writes an app-managed PKCS#12 certificate file, creates a `ManagedCertificate(source_kind="created")`, creates a matching `CertificateConfiguration`, optionally stores the password through the existing Secret Service adapter, and refreshes any open signing shell so the new configuration is selectable.

This is a first in-app creation slice, not a general certificate-authoring product. It does not add custom subject fields, certificate validity controls, key algorithm choices, CA workflows, trust-chain management, or cross-platform secret backends. The certificate subject should be derived from the display name so the created certificate is usable immediately and the slice stays narrow.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/schema_model_alignment_slice5a_certificate_import_execplan.md` is complete; certificate import creates `ManagedCertificate` and `CertificateConfiguration` records.
- [x] `docs/ExecPlans/certificate_configuration_management_execplan.md` is complete; the app frame can manage and delete certificate configurations.
- [x] `docs/ExecPlans/saved_certificate_password_secret_tool_execplan.md` and `docs/ExecPlans/saved_certificate_password_compliance_followup_execplan.md` are complete; optional saved passwords use the existing `SecretToolCertificateSecretStore`.
- [x] A dev-loop explorer reviewed the current certificate code and recommended this narrow creation flow.

## Progress

- [x] (2026-05-13T01:22Z) Created this ExecPlan from the dev-loop explorer report and current certificate/app-frame code.
- [x] (2026-05-13T01:30Z) Added application-service tests for creating a self-signed PKCS#12 certificate, saving it in managed storage, optional saved-password storage, duplicate-name rejection, and rollback cleanup.
- [x] (2026-05-13T01:34Z) Implemented the certificate creation application service.
- [x] (2026-05-13T01:34Z) Added Qt app-frame tests for the `Settings > Create certificate...` flow, menu wiring, secure-save behavior, error reporting, and shell refresh.
- [x] (2026-05-13T01:34Z) Wired the Qt app frame to the creation service and dialog.
- [x] (2026-05-13T01:38Z) Updated architecture and schema-alignment roadmap documentation.
- [x] (2026-05-13T01:35Z) Focused service and app-frame validation passed: `.venv/bin/python -m pytest -q tests/unit/test_certificate_creation.py tests/unit/test_qt_app_frame.py` (`30 passed in 3.03s`).
- [x] (2026-05-13T01:39Z) Focused ExecPlan validation passed: `.venv/bin/python -m pytest -q tests/unit/test_certificate_creation.py tests/unit/test_qt_app_frame.py tests/unit/test_certificate_storage.py` (`47 passed in 3.19s`).
- [x] (2026-05-13T01:47Z) Full validation passed: `.venv/bin/python -m ruff check .` (`All checks passed!`) and `.venv/bin/python -m pytest -q` (`635 passed, 23 skipped, 1 warning in 198.76s`).
- [x] (2026-05-13T01:49Z) Committed the completed slice as `fa98f0b Add in-app certificate creation flow`.
- [x] (2026-05-13T01:55Z) Compliance review found that rollback cleanup could skip saved-secret deletion when file cleanup failed, and noted whitespace-only passwords were not rejected.
- [x] (2026-05-13T01:58Z) Updated rollback cleanup to attempt file and secret cleanup independently and added regression coverage for cleanup failure and whitespace-only passwords.
- [x] (2026-05-13T01:59Z) Focused validation passed for the compliance follow-up: `.venv/bin/python -m pytest -q tests/unit/test_certificate_creation.py tests/unit/test_qt_app_frame.py tests/unit/test_certificate_storage.py` (`49 passed in 3.21s`).
- [x] (2026-05-13T02:03Z) Full validation passed for the compliance follow-up: `.venv/bin/python -m ruff check .` (`All checks passed!`) and `.venv/bin/python -m pytest -q` (`637 passed, 23 skipped, 1 warning in 195.31s`).
- [ ] Commit the compliance follow-up.

## Surprises & Discoveries

- Observation: No persisted schema change is required for this slice.
  Evidence: `src/foliaseal/infra/config/schemas.py` already allows `ManagedCertificate.source_kind` to be either `created` or `imported`, and `CertificateConfiguration` already stores the optional saved-password reference.

- Observation: The app frame is already the certificate-management boundary.
  Evidence: `src/foliaseal/presentation/qt/app_frame.py` owns `show_certificate_import()`, `show_certificate_management()`, menu actions under `Settings`, the app-frame-provided certificate secret provider, and `_refresh_shell_certificate_configurations()`.

- Observation: The certificate creation service can share the same rollback pattern as import.
  Evidence: `src/foliaseal/application/certificate_creation.py` mirrors the saved-secret cleanup behavior used by `CertificateImportService` after the saved-password compliance follow-up.

- Observation: Rollback cleanup must not be ordered so one cleanup failure prevents another cleanup attempt.
  Evidence: The first compliance review found `managed_path.unlink()` ran before `delete_secret()`, so a file cleanup failure could skip saved-secret cleanup entirely.

## Decision Log

- Decision: Generate one opinionated self-signed PKCS#12 certificate using the existing `cryptography` dependency.
  Rationale: `cryptography` is already used to parse imported PKCS#12 files in `src/foliaseal/application/certificate_import.py`. Reusing it avoids adding dependencies and keeps the first creation slice focused on the app workflow rather than certificate-authoring options.
  Date/Author: 2026-05-13 / Codex

- Decision: Keep the first UI to display name, password, and secure-save checkbox.
  Rationale: The main user gap is creating a usable managed certificate without leaving the app. A rich subject editor would multiply validation and UI states without being necessary for the first working behavior.
  Date/Author: 2026-05-13 / Codex

- Decision: Reuse the saved-password contract from import.
  Rationale: Created and imported certificates should resolve through the same `CertificateConfiguration` and `CertificateSecretProvider` path. That keeps signing behavior uniform and avoids a second password-storage model.
  Date/Author: 2026-05-13 / Codex

- Decision: Attempt every rollback cleanup operation and report incomplete cleanup explicitly.
  Rationale: A local file cleanup failure and a secure-store cleanup failure are independent. Attempting both gives the app the best chance of leaving no orphaned state, and an explicit combined error is more accurate than silently losing one cleanup attempt.
  Date/Author: 2026-05-13 / Codex

## Outcomes & Retrospective

This slice is in compliance follow-up after the first implementation commit `fa98f0b Add in-app certificate creation flow`. The service and Qt app-frame flow are implemented, docs describe the new state, focused tests pass, and full validation passes. Compliance review identified a rollback cleanup ordering issue and a whitespace-password validation gap; those fixes are implemented locally and validation passes. The remaining work is to commit the follow-up and re-review compliance.

## Context and Orientation

FoliaSeal stores managed certificate metadata in `src/foliaseal/infra/config/schemas.py`. A `ManagedCertificate` is a record for one app-owned PKCS#12 file under the certificate storage directory. PKCS#12 is a password-protected file format that can contain a private key and certificate. A `CertificateConfiguration` is the selectable user-facing signing configuration that points at one managed certificate and may point at a saved password outside JSON.

Imported certificates currently flow through `src/foliaseal/application/certificate_import.py`. `CertificateImportService.import_pkcs12()` validates an existing PKCS#12 file and password, copies the file into `CertificateCatalogStore.managed_certificate_dir`, creates a `ManagedCertificate(source_kind="imported")`, creates a `CertificateConfiguration`, optionally saves the password through a `CertificateSecretStore`, and persists the catalog.

The new creation service should mirror that shape in a new file, `src/foliaseal/application/certificate_creation.py`. It should generate a new private key and self-signed certificate, serialize them into a PKCS#12 file encrypted by the password, write that file into managed storage, create a `ManagedCertificate(source_kind="created")`, create a matching `CertificateConfiguration`, optionally save the password through the same secret-store protocol, and roll back written files or secrets if persistence fails.

The Qt app frame lives in `src/foliaseal/presentation/qt/app_frame.py`. It already has `CertificateImportDialog`, `CertificateConfigurationManagementDialog`, `show_certificate_import()`, `show_certificate_management()`, and `_install_menus()`. The new flow should add a sibling `CertificateCreationDialog`, a `show_certificate_creation()` method, and a `Settings > Create certificate...` menu action. The dialog should call the creation service and then invoke `_refresh_shell_certificate_configurations()` on success.

Do not edit `docs/SPEC.md` or `docs/SCHEMAS.md` without explicit user approval. Treat them as requirements inputs only.

## Plan of Work

First, add `tests/unit/test_certificate_creation.py` and define test helpers similar to `tests/unit/test_certificate_import.py`. The tests should drive a new `CertificateCreationService` without touching Qt. Cover a successful created certificate, saved-password creation, secure-store unavailable rejection, duplicate display name rejection, and rollback cleanup when catalog save fails after a file or secret is written. The successful test should reload the generated PKCS#12 using `cryptography.hazmat.primitives.serialization.pkcs12.load_key_and_certificates()` and the supplied password to prove the file is usable.

Second, implement `src/foliaseal/application/certificate_creation.py`. Define `CertificateCreationError`, `CertificateCreationResult`, a `CertificateSecretStore` protocol compatible with the import service protocol, and `CertificateCreationService`. The main method should be named `create_self_signed_certificate()` and accept keyword-only arguments `display_name: str`, `passphrase: str`, and `save_password: bool = False`. It should reject blank display names and blank passwords. It should reject duplicate `CertificateConfiguration.display_name` values before writing any file or secret. It should generate a 2048-bit RSA key, a self-signed X.509 certificate with common name equal to the display name, a not-before timestamp of now minus one day, and a not-after timestamp around one year in the future. It should serialize with `pkcs12.serialize_key_and_certificates()` and `serialization.BestAvailableEncryption(passphrase.encode("utf-8"))`. Use injected `id_factory` and `clock` arguments, matching `CertificateImportService`, so tests can assert deterministic ids and timestamps.

Third, export the new service from `src/foliaseal/application/__init__.py` so the app frame can import it through the existing application package boundary.

Fourth, add Qt tests in `tests/unit/test_qt_app_frame.py`. Extend the fake bindings only if needed. Tests should prove the Settings menu includes `Create certificate...`, `show_certificate_creation()` attaches a dialog to the window, a successful dialog creates catalog entries and refreshes the open shell, checking save-password saves only a secret reference in JSON, and unavailable secure storage produces the existing warning style without creating a catalog entry.

Fifth, implement the app-frame dialog and wiring in `src/foliaseal/presentation/qt/app_frame.py`. Add a controls dataclass for the creation dialog, a `CertificateCreationDialog` class with display name, password, save-password checkbox, create button, and cancel button. Add `show_certificate_creation()` to `FoliaSealAppFrame`, expose it on `window`, and add the `Settings > Create certificate...` action near import/manage certificate actions. Reuse the existing `_show_error()` and `_show_information()` patterns from the import and management dialogs.

Sixth, update documentation. In `docs/ARCHITECTURE.md`, change the current statements that certificate creation is pending so they describe the first-pass in-app creation flow. In `docs/ExecPlans/schema_model_alignment_execplan.md`, update the roadmap status so saved-password and in-app creation are no longer listed as pending after this slice, while still noting any future work such as richer certificate-authoring options or cross-platform credential stores. Do not edit frozen `docs/SPEC.md` or `docs/SCHEMAS.md`.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

During development, run focused tests:

    .venv/bin/python -m pytest -q tests/unit/test_certificate_creation.py tests/unit/test_qt_app_frame.py tests/unit/test_certificate_storage.py

Before committing, run:

    .venv/bin/python -m ruff check .
    .venv/bin/python -m pytest -q

Expected focused output after implementation should be similar to:

    ... passed in ...s

Expected full output should report all unit tests passing, with any existing skipped tests and known Pillow deprecation warning remaining acceptable.

## Validation and Acceptance

This slice is accepted when a test can create a self-signed PKCS#12 certificate through `CertificateCreationService`, reload the PKCS#12 with the chosen password, and observe a persisted `ManagedCertificate(source_kind="created")` plus a matching `CertificateConfiguration`. It is accepted when the Qt app-frame tests show `Settings > Create certificate...` can create a certificate, refresh an already-open shell, optionally save the password through the existing secret provider, and report errors without partial catalog records.

The implementation must not write plaintext certificate passwords to `certificates.json`. When `save_password=True`, JSON may contain only `save_password=True` and an opaque `password_secret_ref`; the password value must go through the secret store.

No generated harness artifacts are expected.

## Idempotence and Recovery

Creation with a unique display name is repeatable and produces a new managed certificate id and configuration id each time. Duplicate display names should fail before writing files or secrets. If any step fails after writing the managed PKCS#12 file, attempt to delete that file before re-raising. If any step fails after saving a password secret, attempt to delete the secret before re-raising. File cleanup and secret cleanup must both be attempted even if one cleanup operation fails. If any cleanup operation fails, report that rollback cleanup was incomplete and include the failed cleanup operation in the error.

The app should leave existing certificates and configurations untouched on failure. The new service should use temporary local variables and only persist the updated catalog after both the file and optional secret have been prepared.

## Artifacts and Notes

No generated artifacts are expected.

Revision note: Created 2026-05-13 by Codex to implement the first in-app certificate creation slice after import, export, deletion, and saved-password support.

Revision note: Updated 2026-05-13 by Codex after implementing the creation service and Qt app-frame flow and passing focused tests.

Revision note: Updated 2026-05-13 by Codex after updating architecture documentation and passing the full focused validation command.

Revision note: Updated 2026-05-13 by Codex after Ruff and full unit validation passed.

Revision note: Updated 2026-05-13 by Codex after committing the completed implementation slice.

Revision note: Updated 2026-05-13 by Codex after compliance review found rollback cleanup ordering and whitespace-password validation gaps.

Revision note: Updated 2026-05-13 by Codex after focused and full validation passed for the compliance follow-up.
