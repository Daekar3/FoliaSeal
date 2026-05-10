# Certificate Configuration Management

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, a GUI user who has already imported one or more PKCS#12 certificates can manage the saved `CertificateConfiguration` records that appear in FoliaSeal's certificate selector. A `CertificateConfiguration` is the saved, user-facing signing identity that points at an app-managed certificate file. This slice lets the user rename a configuration, edit its notes, and delete the configuration record without deleting the underlying managed certificate file.

This is a deliberately narrow step toward full V1 certificate management. It does not create self-signed certificates, export or back up managed certificate files, delete managed certificate files, or save certificate passwords. Those actions require separate product and architecture decisions, especially around secret storage and file lifecycle.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/schema_model_alignment_slice5a_certificate_import_execplan.md` is complete; it added `CertificateImportService`, app-frame import UI, `CertificateCatalogStore`, and loaded-shell refresh after import.

## Progress

- [x] (2026-05-09T15:24Z) Reviewed `docs/SPEC.md`, `docs/SCHEMAS.md`, `docs/ARCHITECTURE.md`, current app-frame certificate import code, certificate storage code, and focused tests.
- [x] (2026-05-09T15:24Z) Completed the required dev-loop survey subagent review and accepted its recommendation to implement a narrow app-frame certificate-configuration management slice.
- [x] (2026-05-09T15:32Z) Added store and schema behavior for stable-id configuration delete while retaining existing upsert behavior for rename/update.
- [x] (2026-05-09T15:36Z) Added an app-frame certificate configuration management dialog with rename, notes, and delete actions.
- [x] (2026-05-09T15:39Z) Added focused unit tests for storage and app-frame behavior.
- [x] (2026-05-09T15:50Z) Ran focused tests, Ruff, and the full unit suite successfully.
- [x] (2026-05-09T15:52Z) Updated architecture documentation for the app-frame management action and stable-id delete contract.
- [x] (2026-05-09T16:04Z) Completed two post-commit architecture/compliance reviews; added follow-up tests for dialog loading and duplicate display-name rejection, and enforced the frozen schema rule that one managed certificate has at most one V1 configuration.

## Surprises & Discoveries

- Observation: The store already exposes `save_configuration()` and `delete_configuration(name)`, but deletion by display name is awkward for a management UI because the canonical schema treats display names as mutable metadata.
  Evidence: `docs/SCHEMAS.md` says user-facing names are metadata, while `src/foliaseal/infra/config/certificate_storage.py` deletes configurations by name.

- Observation: The app frame already owns certificate import and a shell refresh hook, so certificate configuration management can stay at the same top-level boundary.
  Evidence: `src/foliaseal/presentation/qt/app_frame.py` defines `show_certificate_import()` and `_refresh_shell_certificate_configurations()`.

- Observation: Adding `QComboBox` to the app-frame dynamic binding contract required updating every test fake that constructs `QtAppFrameBindings`.
  Evidence: Ruff and focused tests passed after `tests/unit/test_qt_app_frame.py` added `_FakeComboBox` and supplied `q_combo_box`.

- Observation: The initial implementation allowed two `CertificateConfiguration` entries to reference one `ManagedCertificate`, which conflicts with the frozen schema rule that V1 has one primary configuration per managed certificate.
  Evidence: Compliance review cited `docs/SCHEMAS.md` and `CertificateCatalog.__post_init__`; the follow-up adds duplicate managed-certificate-reference validation and a focused schema test.

## Decision Log

- Decision: Manage `CertificateConfiguration` records by stable `certificate_configuration_id`, not by display name.
  Rationale: `docs/SCHEMAS.md` says display names are mutable metadata and stable internal identifiers should carry identity. Rename and delete operations are safer when they target stable ids.
  Date/Author: 2026-05-09 / Codex

- Decision: Keep managed certificate file deletion out of this slice.
  Rationale: Deleting a configuration is explicitly separate from deleting a `ManagedCertificate`. File deletion needs reference-counting and a confirmation policy because one managed file can still be referenced or may be intentionally retained for a future configuration.
  Date/Author: 2026-05-09 / Codex

- Decision: Put the first management UI in the app frame settings area, next to certificate import.
  Rationale: Certificate configurations are reusable app-level objects, not document-specific placement or preview state. The app frame already owns top-level settings/import actions and can refresh a loaded shell after catalog changes.
  Date/Author: 2026-05-09 / Codex

## Outcomes & Retrospective

This slice added a focused first-pass management flow for `CertificateConfiguration` records. Users can open the app-frame management dialog, rename a configuration, edit its notes, or delete the configuration record. The delete path targets `certificate_configuration_id` and preserves `ManagedCertificate` records and files. The loaded signing shell refresh hook is reused after save and delete, so already open documents can see catalog changes without reopening.

Remaining gaps are intentionally unchanged: no self-signed certificate creation, no export/backup, no managed certificate file deletion, and no saved-password credential-store adapter.

Post-commit compliance review found no architecture boundary issue in the UI/storage flow, but identified missing test evidence for dialog loading and duplicate-name rejection plus a model invariant gap for duplicate managed-certificate references. The follow-up closes those items with tests and schema validation.

## Context and Orientation

FoliaSeal is a Linux desktop PDF signing application. The GUI app frame in `src/foliaseal/presentation/qt/app_frame.py` owns top-level menus such as `File > Open`, application settings, and certificate import. The signing shell in `src/foliaseal/presentation/qt/signing_shell.py` owns document-specific signing controls and can refresh its certificate selector through `refresh_certificate_configurations()`.

Persistent certificate data is defined in `src/foliaseal/infra/config/schemas.py`. A `ManagedCertificate` describes an app-owned PKCS#12 file in the managed certificate directory. A `CertificateConfiguration` describes a saved signing identity with `certificate_configuration_id`, `display_name`, `managed_certificate_id`, password-save flags, and optional `notes`. The `CertificateCatalog` groups managed certificates and configurations. `CertificateCatalogStore` in `src/foliaseal/infra/config/certificate_storage.py` loads and saves the JSON catalog.

`docs/SPEC.md` and `docs/SCHEMAS.md` are frozen without explicit user permission. This plan uses those documents as requirements but does not edit them.

## Plan of Work

First, extend catalog behavior so management operations can target `certificate_configuration_id`. Add methods on `CertificateCatalog` or `CertificateCatalogStore` for deleting a configuration by id and for saving an edited configuration while preserving the existing id and managed certificate reference. Reuse `CertificateConfiguration` construction for validation so blank names, invalid note values, and duplicate names still fail through existing validation rules.

Second, add tests in `tests/unit/test_certificate_storage.py` that prove deleting by id removes only the configuration record, leaves `managed_certificates` unchanged, and raises `KeyError` for an unknown id. Add a test that renaming through `save_configuration()` preserves the original id and rejects duplicate display names.

Third, extend `src/foliaseal/presentation/qt/app_frame.py` with a first-pass `CertificateConfigurationManagementDialog`. The dialog should load the catalog from the injected `CertificateCatalogStore`, expose the available configuration display names in a combo box, show editable fields for display name and notes, and provide Save, Delete, and Cancel buttons. Save should replace only the selected configuration's `display_name` and `notes`. Delete should remove only the selected configuration record by id. Both successful operations should persist the catalog, reload the dialog list, and call `_refresh_shell_certificate_configurations()` on the app frame so a loaded signing shell updates without reopening the PDF.

Fourth, add or extend fake Qt bindings in `tests/unit/test_qt_app_frame.py` to cover the new dialog without launching a real GUI. Tests should prove the Settings menu contains `Manage certificate configurations...`, the dialog loads existing configurations, Save renames and edits notes, Delete removes the configuration record but leaves the managed certificate record, and both operations refresh a loaded fake shell. Tests should also cover an empty catalog path producing a warning or no-op rather than a crash.

Fifth, update `docs/ARCHITECTURE.md` after implementation if app-frame responsibilities or storage contracts changed. Do not edit frozen `docs/SPEC.md` or `docs/SCHEMAS.md`.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Focused tests while developing:

    .venv/bin/python -m pytest -q tests/unit/test_certificate_storage.py tests/unit/test_qt_app_frame.py

    18 passed in 2.60s

Compliance follow-up focused tests:

    .venv/bin/python -m pytest -q tests/unit/test_config_schemas.py tests/unit/test_certificate_storage.py tests/unit/test_qt_app_frame.py

    48 passed in 2.66s

Before committing:

    .venv/bin/python -m ruff check .

    All checks passed!

    .venv/bin/python -m pytest -q

    590 passed, 23 skipped, 1 warning in 245.85s (0:04:05)

## Validation and Acceptance

This slice is accepted when storage tests prove configuration deletion targets stable ids and never deletes managed certificate records, and app-frame tests prove the GUI management action can rename, edit notes, and delete certificate configurations from the injected store. A loaded shell must refresh after save and delete.

The final validation should include the focused tests above and then Ruff plus the full unit suite. No generated harness artifacts should change.

## Idempotence and Recovery

The storage operations are JSON catalog rewrites and can be repeated safely with the same inputs. Failed validation should leave the previous catalog intact where possible. The dialog should reload from the store after successful operations so repeated Save/Delete clicks operate on the latest catalog state. If a delete fails because the selected id no longer exists, the dialog should show an error and reload.

Do not remove files from `Certificates/Managed/` in this slice. Do not persist passwords or secret references. Do not edit `docs/SPEC.md` or `docs/SCHEMAS.md` without explicit user approval.

## Artifacts and Notes

No generated artifacts are expected.

Validation transcript:

    .venv/bin/python -m pytest -q tests/unit/test_certificate_storage.py tests/unit/test_qt_app_frame.py
    18 passed in 2.60s

    .venv/bin/python -m ruff check .
    All checks passed!

    .venv/bin/python -m pytest -q
    590 passed, 23 skipped, 1 warning in 245.85s (0:04:05)

Compliance follow-up transcript:

    .venv/bin/python -m pytest -q tests/unit/test_config_schemas.py tests/unit/test_certificate_storage.py tests/unit/test_qt_app_frame.py
    48 passed in 2.66s

    .venv/bin/python -m ruff check .
    All checks passed!

Revision note: Created 2026-05-09 by Codex to implement the next schema-alignment certificate-management slice after PKCS#12 import.

Revision note: Updated 2026-05-09 by Codex after implementing stable-id delete, app-frame configuration management, architecture docs, and validation.

Revision note: Updated 2026-05-09 by Codex after post-commit compliance reviews identified missing test coverage and the duplicate managed-certificate-reference invariant.
