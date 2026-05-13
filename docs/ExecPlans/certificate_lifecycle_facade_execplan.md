# Certificate Lifecycle Facade

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this refactor, the Qt app frame will no longer own certificate lifecycle policy. A certificate lifecycle policy is the set of rules for creating, importing, editing, deleting, exporting, and safely rolling back managed certificate records and files. Today that policy is split between `src/foliaseal/presentation/qt/app_frame.py`, `src/foliaseal/application/certificate_creation.py`, `src/foliaseal/application/certificate_import.py`, and `src/foliaseal/infra/config/certificate_storage.py`. This makes tests reach through Qt dialog controls for behavior that is really application policy.

This slice introduces one deeper application boundary, `CertificateLifecycleService`, that the app frame can call for certificate operations. The service will hide catalog persistence, saved-password cleanup/restore, managed-file export/delete calls, and the decision of whether an operation changed the signing-shell certificate selector. The user-visible behavior should not change: `Settings > Create certificate...`, `Settings > Import certificate...`, and `Settings > Manage certificate configurations...` should behave as before.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/in_app_certificate_creation_execplan.md` is complete; create/import/manage/export/delete flows exist and are covered by focused tests.
- [x] The architecture exploration identified App-frame certificate lifecycle as the highest-leverage deepening candidate.
- [x] Four interface-design explorations produced alternatives; this plan adopts a hybrid explicit-method facade rather than a generic command bus or fully ported filesystem/crypto design.

## Progress

- [x] (2026-05-13T10:38Z) Created this ExecPlan from the architecture exploration and interface-design results.
- [x] (2026-05-13T10:44Z) Added `tests/unit/test_certificate_lifecycle.py` covering create, import, save configuration, delete configuration with saved-secret cleanup/restore, delete managed certificate, and export.
- [x] (2026-05-13T10:44Z) Implemented `src/foliaseal/application/certificate_lifecycle.py` and exported the facade from the application package.
- [x] (2026-05-13T10:44Z) Migrated `src/foliaseal/presentation/qt/app_frame.py` certificate dialogs and app-frame wiring to use the lifecycle facade.
- [x] (2026-05-13T10:44Z) Updated architecture documentation to describe the lifecycle facade and reduced app-frame ownership.
- [x] (2026-05-13T10:48Z) Ran focused and full validation successfully.
- [x] (2026-05-13T10:54Z) Committed the initial slice as `793b395 Add certificate lifecycle facade`.
- [x] (2026-05-13T10:54Z) Addressed compliance-review follow-up by closing plan wording, updating the remaining architecture debt reference, and removing duplicate saved-secret rollback coverage from Qt widget tests.
- [x] (2026-05-13T10:54Z) Re-ran follow-up validation successfully.

## Surprises & Discoveries

- Observation: The create and import services already share most of the same policy shape.
  Evidence: Both `CertificateCreationService.create_self_signed_certificate()` and `CertificateImportService.import_pkcs12()` normalize display names, reject duplicates, create managed certificate/configuration records, optionally save a password secret, write a managed file, save the catalog, and perform rollback cleanup.

- Observation: Configuration deletion policy was in the Qt management dialog before this slice.
  Evidence: `CertificateConfigurationManagementDialog.delete_selected_configuration()` reads and deletes saved secrets, restores a secret if catalog deletion fails, emits errors, and only then refreshes the shell.

- Observation: Focused lifecycle and app-frame tests passed after moving the certificate policy boundary.
  Evidence: `.venv/bin/python -m pytest -q tests/unit/test_certificate_lifecycle.py tests/unit/test_qt_app_frame.py tests/unit/test_certificate_creation.py tests/unit/test_certificate_import.py tests/unit/test_certificate_storage.py` reported 69 passed.

- Observation: Full validation passed.
  Evidence: `.venv/bin/python -m ruff check .` reported all checks passed. `.venv/bin/python -m pytest -q` reported 648 passed, 23 skipped, 1 warning in 231.27s.

- Observation: Compliance review found only documentation/test-scope drift after the initial implementation commit.
  Evidence: One reviewer found the ExecPlan still read as in-progress; the other found one remaining architecture debt line that still attributed saved-password cleanup to the app frame and noted duplicate Qt widget coverage for saved-secret rollback already covered by lifecycle tests.

- Observation: Follow-up validation passed after addressing compliance-review drift.
  Evidence: `.venv/bin/python -m ruff check .` reported all checks passed. `.venv/bin/python -m pytest -q tests/unit/test_certificate_lifecycle.py tests/unit/test_qt_app_frame.py` reported 29 passed.

## Decision Log

- Decision: Use explicit facade methods instead of a one-method command bus.
  Rationale: The current callers are simple and benefit from typed method signatures. A command bus would be more flexible but would add indirection before richer certificate authoring or non-Qt callers exist.
  Date/Author: 2026-05-13 / Codex

- Decision: Keep the existing creation/import services and delegate through the lifecycle facade in this slice.
  Rationale: Those services already have focused tests and correct rollback behavior. Wrapping them first deepens the app-frame boundary without mixing in a risky internal rewrite.
  Date/Author: 2026-05-13 / Codex

- Decision: Move configuration delete saved-secret cleanup/restore out of Qt in this slice.
  Rationale: This is the clearest current policy leak in `app_frame.py`. Moving it behind the lifecycle facade reduces widget test coupling and centralizes saved-secret consistency behavior.
  Date/Author: 2026-05-13 / Codex

## Outcomes & Retrospective

This slice is complete. Certificate operations are available through `CertificateLifecycleService`, Qt dialogs call that facade rather than owning persistence policy directly, focused lifecycle boundary tests cover saved-secret cleanup/restore behavior, architecture docs describe the new ownership, and focused plus full validation passed.

## Context and Orientation

FoliaSeal stores managed certificates in a certificate catalog. The catalog is JSON on disk plus app-managed PKCS#12 files under a `Managed/` directory. PKCS#12 is a password-protected certificate bundle containing a private key and certificate.

The existing creation service lives in `src/foliaseal/application/certificate_creation.py`. It creates a self-signed PKCS#12 file, persists a `ManagedCertificate(source_kind="created")`, persists a matching `CertificateConfiguration`, optionally stores the password through a secret store, and rolls back files and secrets on failure.

The existing import service lives in `src/foliaseal/application/certificate_import.py`. It validates an existing PKCS#12 file/password, copies the file into managed storage, creates a `ManagedCertificate(source_kind="imported")`, creates a matching `CertificateConfiguration`, optionally stores the password through a secret store, and rolls back files and secrets on failure.

The catalog store lives in `src/foliaseal/infra/config/certificate_storage.py`. It loads and saves the catalog, deletes configurations, deletes unreferenced managed certificate files, and exports managed certificate files to user-selected destinations. It now removes `certificates.json.tmp` if atomic replace fails.

The Qt app frame lives in `src/foliaseal/presentation/qt/app_frame.py`. Before this slice, it built certificate create/import/manage dialogs, constructed creation/import services directly, called catalog-store methods directly for rename/delete/export, performed saved-secret cleanup/restore for configuration deletion, and refreshed the signing shell after successful catalog changes. After this slice, it delegates certificate lifecycle operations to `CertificateLifecycleService` and only handles dialog state, messages, and shell refresh reaction.

## Plan of Work

First, add `tests/unit/test_certificate_lifecycle.py`. Use a real `CertificateCatalogStore` rooted in `tmp_path` and a fake in-memory secret store. Cover successful create and import through the facade, saving a configuration rename/notes update, deleting a configuration with saved-secret cleanup and restore on catalog failure, deleting an unreferenced managed certificate, exporting a managed certificate, and result metadata such as `refresh_shell` and `user_message`.

Second, implement `src/foliaseal/application/certificate_lifecycle.py`. Define `CertificateLifecycleResult` with fields `catalog`, `refresh_shell`, `user_message`, optional `managed_certificate`, optional `certificate_configuration`, optional `managed_file_path`, and optional `exported_path`. Define `CertificateLifecycleService` with explicit methods `create_self_signed_certificate()`, `import_pkcs12()`, `save_configuration()`, `delete_configuration()`, `delete_managed_certificate()`, and `export_managed_certificate()`. The create/import methods should delegate to the existing services and convert their results to `CertificateLifecycleResult`. The management methods should use `CertificateCatalogStore` and `CertificateSecretStore`, moving saved-secret delete/restore behavior out of the Qt dialog.

Third, export the lifecycle service from `src/foliaseal/application/__init__.py`.

Fourth, migrate `src/foliaseal/presentation/qt/app_frame.py`. `CertificateCreationDialog` and `CertificateImportDialog` should accept a lifecycle service instead of separate creation/import services. `CertificateConfigurationManagementDialog` should call lifecycle methods for save, delete configuration, delete managed certificate, and export. The dialogs can still own control reads, message boxes, selection reload, and calling the app-frame refresh callback when `result.refresh_shell` is true.

Fifth, update tests. Add lifecycle boundary tests and update `tests/unit/test_qt_app_frame.py` so widget tests assert that dialogs call the facade behavior but no longer duplicate saved-secret rollback assertions already covered by lifecycle tests. Keep existing service-specific creation/import tests for low-level PKCS#12 generation and validation.

Sixth, update `docs/ARCHITECTURE.md` to say the application layer now owns certificate lifecycle coordination through `CertificateLifecycleService`, while `app_frame.py` owns only menu/dialog presentation and shell refresh reaction.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Focused validation during development:

    .venv/bin/python -m pytest -q tests/unit/test_certificate_lifecycle.py tests/unit/test_qt_app_frame.py tests/unit/test_certificate_creation.py tests/unit/test_certificate_import.py tests/unit/test_certificate_storage.py

Before committing:

    .venv/bin/python -m ruff check .
    .venv/bin/python -m pytest -q

## Validation and Acceptance

This slice is accepted when lifecycle tests prove that create/import/save/delete/export behavior works through `CertificateLifecycleService` with a temp catalog store and fake secret store, and when Qt app-frame tests still prove the user-facing menu/dialog flows work. The app frame should not contain saved-secret restore logic after this refactor; that logic should be covered by lifecycle boundary tests.

No user-visible behavior change is expected. Existing create/import/manage/export/delete flows should continue to show the same success and error message titles.

## Idempotence and Recovery

The refactor is behavior-preserving and additive at first. If a lifecycle operation fails after writing files or secrets, the same rollback rules from the existing services must apply. If deleting a configuration with a saved password fails after secret deletion, the lifecycle service must attempt to restore the saved secret before returning an error. Existing catalog temp-file cleanup behavior must remain intact.

## Artifacts and Notes

No generated artifacts are expected.

Revision note: Created 2026-05-13 by Codex to deepen the app-frame certificate lifecycle boundary after architecture exploration identified the certificate flow as the highest-leverage refactor candidate.
