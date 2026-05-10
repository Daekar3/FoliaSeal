# Managed Certificate Export

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, a GUI user can export or back up an app-managed PKCS#12 certificate file from FoliaSeal's certificate management dialog. A `ManagedCertificate` is the app-owned record for a certificate file copied into FoliaSeal's managed storage. Exporting means copying that app-owned PKCS#12 file to a user-chosen destination path without changing the certificate catalog, signing configuration records, or password behavior.

This is a narrow V1 certificate-management slice. It deliberately does not create self-signed certificates, store certificate passwords, change secret references, or alter the certificate import/delete lifecycle.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/schema_model_alignment_slice5a_certificate_import_execplan.md` is complete; imported PKCS#12 files are copied into managed storage with catalog records.
- [x] `docs/ExecPlans/certificate_configuration_management_execplan.md` is complete; app-frame certificate management exists.
- [x] `docs/ExecPlans/managed_certificate_deletion_execplan.md` is complete; managed certificate lifecycle actions now include safe deletion of unreferenced app-managed files.

## Progress

- [x] (2026-05-10T22:51Z) Reviewed the dev-loop explorer recommendation, current certificate storage code, app-frame certificate management dialog, fake Qt tests, and relevant architecture/schema docs.
- [x] (2026-05-10T22:56Z) Added store behavior for exporting a selected `ManagedCertificate` file to a destination path.
- [x] (2026-05-10T22:59Z) Extended the app-frame certificate management dialog with an export/backup action using a save-file dialog.
- [x] (2026-05-10T23:02Z) Added focused storage and app-frame tests for successful export, overwrite behavior, missing source handling, and cancel/no-selection behavior.
- [x] (2026-05-10T23:05Z) Updated architecture and schema-alignment roadmap documentation for managed certificate export.
- [x] (2026-05-10T23:12Z) Ran focused tests, Ruff, and the full unit suite successfully.
- [x] (2026-05-10T23:18Z) Completed post-commit compliance review and added a safety follow-up that rejects managed-storage destinations and symlink destinations.

## Surprises & Discoveries

- Observation: Export does not need a schema change.
  Evidence: `ManagedCertificate.storage_filename` already identifies the app-owned PKCS#12 file under `CertificateCatalogStore.managed_certificate_dir`.

- Observation: The same app-frame management dialog can own export without reaching into the signing shell.
  Evidence: `src/foliaseal/presentation/qt/app_frame.py` already owns certificate import, configuration management, and managed certificate deletion.

- Observation: The app-frame fake file dialog only modeled open-file selection before this slice.
  Evidence: `tests/unit/test_qt_app_frame.py` needed fake `getSaveFileName()` support to test the export path.

- Observation: Exact same-path rejection was not enough to protect the non-mutating export contract.
  Evidence: Compliance review identified that exporting onto another file under `Certificates/Managed/` or through a symlink destination could overwrite app-owned PKCS#12 data. The follow-up rejects destinations inside managed storage and rejects symbolic-link destinations before copying.

## Decision Log

- Decision: Implement export as a file copy only, with no catalog mutation and no shell refresh.
  Rationale: Export/backup is a portability action. It should not change signing identities, managed certificate records, or preview/signing state.
  Date/Author: 2026-05-10 / Codex

- Decision: Allow overwriting the destination path selected by the save-file dialog.
  Rationale: Standard save dialogs normally ask the user to confirm overwrites. The storage method should make overwrite behavior explicit and tests should prove it replaces the destination bytes.
  Date/Author: 2026-05-10 / Codex

- Decision: Reject exporting to the same resolved path as the managed source file.
  Rationale: Copying a file onto itself is not a meaningful backup and can raise platform-dependent errors.
  Date/Author: 2026-05-10 / Codex

## Outcomes & Retrospective

This slice added a focused export path that copies selected managed PKCS#12 bytes to a user-chosen path while leaving all catalog and signing state unchanged. The app-frame management dialog now has an export action, the store handles overwrite and missing-source behavior, and tests cover cancel/no-selection behavior at the UI boundary. A compliance follow-up tightened destination safety so export cannot overwrite files inside FoliaSeal managed certificate storage and cannot write through a symbolic-link destination.

## Context and Orientation

FoliaSeal is a local Linux desktop PDF signing application. Persistent certificate data lives in `src/foliaseal/infra/config/schemas.py`. `ManagedCertificate` records app-owned PKCS#12 certificate files, and each record has a `storage_filename`. `CertificateCatalogStore` in `src/foliaseal/infra/config/certificate_storage.py` owns the root directory `${XDG_DATA_HOME:-~/.local/share}/FoliaSeal/Certificates/` and the managed files directory `Managed/`.

The app-frame UI lives in `src/foliaseal/presentation/qt/app_frame.py`. `CertificateConfigurationManagementDialog` already loads managed certificates into a selector and can delete selected unreferenced managed certificates. Export belongs in that same dialog because it is an app-level certificate lifecycle action, not a document-specific signing action.

`docs/SPEC.md` and `docs/SCHEMAS.md` are frozen without explicit user permission. This slice should use them as requirements but must not edit them.

## Plan of Work

First, add `CertificateCatalogStore.export_managed_certificate_by_id(certificate_id, destination_path)` in `src/foliaseal/infra/config/certificate_storage.py`. It should load the catalog, find the selected `ManagedCertificate`, resolve the source file inside `managed_certificate_dir`, require that the source file exists, reject source and destination paths that resolve to the same path, create the destination parent directory if needed, and copy bytes with metadata preservation where practical. It should return the final destination `Path`. It should not save the catalog.

Second, extend `CertificateConfigurationManagementDialog` in `src/foliaseal/presentation/qt/app_frame.py`. Add an `Export certificate` button. When clicked, read the selected managed certificate id. If none is selected, show an error. Otherwise open `QFileDialog.getSaveFileName()` with a suggested filename equal to the certificate's `storage_filename` and a `PKCS#12 files (*.p12 *.pfx);;All files (*)` filter. If the user cancels, do nothing. If the user chooses a destination, call the new store method and show an informational message. Do not call the shell refresh callback because export does not change app state.

Third, add focused tests. In `tests/unit/test_certificate_storage.py`, test successful export copies exact bytes, overwrites an existing destination, rejects a missing managed source file, and rejects copying onto itself. In `tests/unit/test_qt_app_frame.py`, extend the fake file dialog with save-file support and test that the dialog exports the selected managed certificate, shows information, does not refresh the shell, and does nothing on cancel or no selection.

Fourth, update `docs/ARCHITECTURE.md` to state that the app frame can export/back up managed PKCS#12 files, and that certificate creation and secure password storage remain pending. Update the stale certificate-management gap text so export is no longer listed as pending.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Focused tests while developing:

    .venv/bin/python -m pytest -q tests/unit/test_certificate_storage.py tests/unit/test_qt_app_frame.py

    30 passed in 2.85s

Compliance follow-up focused tests:

    .venv/bin/python -m pytest -q tests/unit/test_certificate_storage.py tests/unit/test_qt_app_frame.py

    32 passed in 1.69s

Before committing:

    .venv/bin/python -m ruff check .

    All checks passed!

    .venv/bin/python -m pytest -q

    605 passed, 23 skipped, 1 warning in 243.26s (0:04:03)

## Validation and Acceptance

This slice is accepted when storage tests prove a managed PKCS#12 file can be exported to a chosen destination with exact bytes, existing destinations are overwritten, missing source files fail clearly, and same-source/destination paths are rejected. It is accepted at the GUI layer when the app-frame management dialog opens a save-file flow, exports the selected certificate, shows success, and leaves catalog/signing state unchanged.

No generated harness artifacts are expected. Full test validation and Ruff must pass before commit.

## Idempotence and Recovery

Export can be repeated safely. Repeating export to the same destination overwrites that destination with the current managed certificate bytes. If the source managed file is missing, the catalog is left unchanged and no destination is written. If the save-file dialog is canceled, no file operation occurs.

Do not mutate certificate catalog JSON in this slice. Do not edit `docs/SPEC.md` or `docs/SCHEMAS.md` without explicit user approval.

## Artifacts and Notes

No generated artifacts are expected.

Validation transcript:

    .venv/bin/python -m pytest -q tests/unit/test_certificate_storage.py tests/unit/test_qt_app_frame.py
    30 passed in 2.85s

    .venv/bin/python -m ruff check .
    All checks passed!

    .venv/bin/python -m pytest -q
    605 passed, 23 skipped, 1 warning in 243.26s (0:04:03)

Compliance follow-up transcript:

    .venv/bin/python -m pytest -q tests/unit/test_certificate_storage.py tests/unit/test_qt_app_frame.py
    32 passed in 1.69s

    .venv/bin/python -m ruff check .
    All checks passed!

Revision note: Created 2026-05-10 by Codex to implement a managed-certificate export/backup slice after import, configuration management, and deletion.

Revision note: Updated 2026-05-10 by Codex after implementing store export, app-frame export UI, docs, and validation.

Revision note: Updated 2026-05-10 by Codex after compliance review identified destination-safety gaps around managed-storage destinations and symbolic-link destinations.
