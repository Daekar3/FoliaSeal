# Managed Certificate Deletion

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, a GUI user can delete an app-managed PKCS#12 certificate file from FoliaSeal's managed certificate storage after first deleting any saved `CertificateConfiguration` that references it. A `ManagedCertificate` is the app-owned record for a certificate file copied into FoliaSeal's data directory. Deleting that object is separate from deleting a `CertificateConfiguration`, which is the saved signing identity that points at the certificate.

This closes one small V1 certificate-management gap while keeping the behavior safe. FoliaSeal should not leave a saved signing identity pointing at a missing certificate file, and this slice should not add certificate creation, export/backup, or saved-password storage.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/schema_model_alignment_slice5a_certificate_import_execplan.md` is complete; imported PKCS#12 files are copied into managed storage with `ManagedCertificate` and `CertificateConfiguration` records.
- [x] `docs/ExecPlans/certificate_configuration_management_execplan.md` is complete; users can rename, edit notes for, and delete `CertificateConfiguration` records separately from managed certificate files.

## Progress

- [x] (2026-05-10T02:39Z) Reviewed the dev-loop explorer recommendation, current architecture/schema docs, certificate storage code, app-frame management dialog, and related tests.
- [x] (2026-05-10T02:45Z) Added catalog/store behavior for deleting an unreferenced `ManagedCertificate` by stable id and removing its managed PKCS#12 file.
- [x] (2026-05-10T02:48Z) Extended the app-frame certificate management dialog with managed certificate selection and delete behavior.
- [x] (2026-05-10T02:52Z) Added focused storage/schema/app-frame tests for blocked referenced deletion and successful unreferenced file cleanup.
- [x] (2026-05-10T02:54Z) Updated architecture documentation for managed certificate deletion.
- [x] (2026-05-10T03:00Z) Ran focused tests, Ruff, and the full unit suite successfully.

## Surprises & Discoveries

- Observation: The last certificate-management slice deliberately kept `CertificateConfiguration` deletion separate from `ManagedCertificate` deletion.
  Evidence: `docs/ExecPlans/certificate_configuration_management_execplan.md` says deletion of configuration records does not remove managed certificate records or files.

- Observation: The current app-frame management dialog already has a safe place to add this UI without touching document-specific signing controls.
  Evidence: `src/foliaseal/presentation/qt/app_frame.py` owns `CertificateConfigurationManagementDialog` and `show_certificate_management()`.

- Observation: The delete path can tolerate a missing managed PKCS#12 file while still removing the catalog record.
  Evidence: `tests/unit/test_certificate_storage.py` covers deleting an unreferenced managed certificate whose file is already absent.

## Decision Log

- Decision: Block managed certificate deletion while any `CertificateConfiguration` references the managed certificate id.
  Rationale: `docs/SCHEMAS.md` says managed-certificate deletion is separate from configuration deletion. Blocking referenced deletion preserves shallow references and prevents a saved signing identity from pointing at a missing file.
  Date/Author: 2026-05-10 / Codex

- Decision: Delete both the `ManagedCertificate` catalog record and the managed PKCS#12 file in the same store operation when the certificate is unreferenced.
  Rationale: The user-facing action is deleting an app-managed certificate, not merely hiding the catalog entry. The managed file is app-owned and should be removed when the record is removed.
  Date/Author: 2026-05-10 / Codex

- Decision: Do not delete or alter saved-password secret references in this slice.
  Rationale: There is no concrete credential-store adapter yet, and this slice blocks deletion while configurations exist. Therefore there should be no configuration secret reference to clean up when a managed certificate can be deleted.
  Date/Author: 2026-05-10 / Codex

## Outcomes & Retrospective

This slice added a safe deletion path for unreferenced managed certificates. `CertificateCatalog` blocks deletion while a configuration references the managed certificate id, `CertificateCatalogStore` removes the managed PKCS#12 file when deleting an unreferenced record, and the app-frame management dialog exposes a managed certificate selector plus delete action. Certificate creation, export/backup, and saved-password storage remain pending.

## Context and Orientation

FoliaSeal is a local Linux desktop PDF signing application. The relevant persistent certificate data lives in `src/foliaseal/infra/config/schemas.py`. `ManagedCertificate` records app-owned PKCS#12 certificate files. `CertificateConfiguration` records saved signing identities and point to `ManagedCertificate` by `managed_certificate_id`. `CertificateCatalog` holds both lists and enforces schema rules such as unique object ids and one V1 configuration per managed certificate.

The store lives in `src/foliaseal/infra/config/certificate_storage.py`. `CertificateCatalogStore.managed_certificate_dir` is the directory where imported PKCS#12 files are copied. Store methods load the catalog, modify it, and save JSON back to `${XDG_DATA_HOME:-~/.local/share}/FoliaSeal/Certificates/certificates.json`.

The app-frame UI lives in `src/foliaseal/presentation/qt/app_frame.py`. It owns top-level certificate actions and the `CertificateConfigurationManagementDialog`, which already lets users edit and delete `CertificateConfiguration` records. The signing shell consumes the catalog but should not own app-wide certificate lifecycle management.

`docs/SPEC.md` and `docs/SCHEMAS.md` are frozen without explicit user permission. This slice should use them as requirements but must not edit them.

## Plan of Work

First, add schema behavior to `CertificateCatalog` for deleting an unreferenced managed certificate by stable `managed_certificate_id`. The method should return a new catalog without the matching `ManagedCertificate`. It should raise `KeyError` when the id does not exist and raise `ConfigValidationError` when any `CertificateConfiguration` still references the id. The error message should explain that certificate configurations must be deleted first.

Second, add a store method to `CertificateCatalogStore` that deletes an unreferenced managed certificate by id. It should load the catalog, find the matching certificate, build the updated catalog, save the updated JSON, and remove the corresponding file from `managed_certificate_dir`. If the file is already missing, the operation should still succeed because the catalog is the source of truth and the user asked to remove the managed certificate record. If file deletion fails, raise the `OSError` after the catalog save so the UI can show the file-system problem. This slice should avoid destructive filesystem behavior outside `managed_certificate_dir`.

Third, extend `CertificateConfigurationManagementDialog` in `src/foliaseal/presentation/qt/app_frame.py` with a second selector for managed certificates and a `Delete certificate` button. The selector should show managed certificate display names and hold `managed_certificate_id` as item data. The delete action should call the new store method, reload both configuration and certificate selectors, refresh the loaded shell through the existing callback, and show an information message. If the certificate is referenced by a configuration, show the store's validation message and leave the catalog/file unchanged.

Fourth, add focused tests. In `tests/unit/test_config_schemas.py`, prove the catalog blocks removal of a referenced managed certificate and removes an unreferenced one. In `tests/unit/test_certificate_storage.py`, prove successful deletion removes the record and managed file, and referenced deletion leaves both intact with a clear validation error. In `tests/unit/test_qt_app_frame.py`, prove the dialog loads managed certificates, blocks deletion while referenced, deletes after the configuration is deleted, and refreshes a loaded shell after successful deletion.

Fifth, update `docs/ARCHITECTURE.md` to state that the app frame can delete unreferenced managed certificates and that creation, export/backup, and secure password storage remain pending. Update this ExecPlan throughout as work proceeds.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Focused tests while developing:

    .venv/bin/python -m pytest -q tests/unit/test_config_schemas.py tests/unit/test_certificate_storage.py tests/unit/test_qt_app_frame.py

    55 passed in 2.79s

Before committing:

    .venv/bin/python -m ruff check .

    All checks passed!

    .venv/bin/python -m pytest -q

    599 passed, 23 skipped, 1 warning in 237.70s (0:03:57)

## Validation and Acceptance

This slice is accepted when storage tests prove referenced managed certificates cannot be deleted, unreferenced managed certificates can be deleted, and successful deletion removes the app-managed PKCS#12 file. It is accepted at the GUI layer when the app-frame management dialog exposes managed certificates, shows a clear error for referenced deletion, and refreshes a loaded shell after successful deletion.

No generated harness artifacts are expected. Full test validation and Ruff must pass before commit.

## Idempotence and Recovery

Deleting a managed certificate by id is safe to retry only until the record is gone. A second deletion attempt should raise `KeyError` or show a user-facing error because the object no longer exists. If the managed file is already missing, the store may still delete the catalog record. If catalog validation fails because a configuration references the certificate, the operation should not write the catalog and should not delete the file.

Do not remove arbitrary paths from user storage. Only remove the file named by `ManagedCertificate.storage_filename` inside `CertificateCatalogStore.managed_certificate_dir`. Do not edit `docs/SPEC.md` or `docs/SCHEMAS.md`.

## Artifacts and Notes

No generated artifacts are expected.

Validation transcript:

    .venv/bin/python -m pytest -q tests/unit/test_config_schemas.py tests/unit/test_certificate_storage.py tests/unit/test_qt_app_frame.py
    55 passed in 2.79s

    .venv/bin/python -m ruff check .
    All checks passed!

    .venv/bin/python -m pytest -q
    599 passed, 23 skipped, 1 warning in 237.70s (0:03:57)

Revision note: Created 2026-05-10 by Codex to implement a safe managed-certificate deletion slice after certificate configuration management.

Revision note: Updated 2026-05-10 by Codex after implementing catalog/store deletion, app-frame managed certificate deletion, architecture docs, and validation.
