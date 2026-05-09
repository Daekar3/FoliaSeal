# Schema Model Alignment Slice 5A: Import Certificate Configuration

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, a GUI user can import an existing PKCS#12 certificate file, such as a `.p12` or `.pfx`, into FoliaSeal's app-managed certificate storage from the top-level application frame. FoliaSeal will copy the source certificate into its managed `Certificates/Managed/` directory, create a `ManagedCertificate` record, create one primary `CertificateConfiguration`, and refresh any currently loaded signing shell so the new configuration appears in the existing certificate selector.

This is the smallest useful first step toward full certificate management. It deliberately does not create self-signed certificates, export/back up certificates, delete certificates, or save certificate passwords. Passwords typed during import are used only to unlock the PKCS#12 long enough to validate it and read non-secret subject fields; they are not persisted.

## Child ExecPlan Dependencies

- [x] Schema model alignment through Slice 4E is complete, including first-class `ManagedCertificate`, `CertificateConfiguration`, `CertificateCatalogStore`, app-frame menus, and signing-shell certificate selection.

## Progress

- [x] (2026-05-09T13:29Z) Reviewed `docs/SPEC.md`, `docs/SCHEMAS.md`, `docs/ARCHITECTURE.md`, schema-alignment plans, and current certificate/app-frame code.
- [x] (2026-05-09T13:29Z) Started the required dev-loop codebase review subagent and incorporated its recommendation to implement a narrow app-frame PKCS#12 import slice.
- [x] (2026-05-09T13:35Z) Added an application-layer certificate import service with focused tests.
- [x] (2026-05-09T13:37Z) Added an app-frame certificate import menu/dialog and loaded-shell refresh behavior with focused tests.
- [x] (2026-05-09T13:39Z) Updated architecture and schema-alignment ExecPlan documentation.
- [x] (2026-05-09T13:42Z) Ran focused tests, Ruff, and the full unit suite successfully.
- [ ] Commit the completed slice.

## Surprises & Discoveries

- Observation: the current signing shell can apply existing certificate configurations but cannot create them.
  Evidence: `src/foliaseal/presentation/qt/signing_shell.py` has `apply_selected_certificate_configuration()` and `CertificateConfigurationControls`, while `docs/ARCHITECTURE.md` says full certificate management is not implemented in the Qt shell yet.

- Observation: `CertificateCatalogStore` already persists managed certificate records, configurations, and a managed files directory.
  Evidence: `src/foliaseal/infra/config/certificate_storage.py` exposes `managed_certificate_dir`, `save_managed_certificate()`, and `save_configuration()`.

- Observation: certificate subject extraction already exists for preview use but returns UI field-key values rather than the certificate catalog subject-summary schema.
  Evidence: `src/foliaseal/application/certificate_preview.py` extracts PKCS#12 subject fields into `SignatureFieldKey` values; this slice should avoid coupling import persistence to visible-signature preview field enums unless reuse is clean.

## Decision Log

- Decision: make this an import-only slice owned by the app frame, not the document-specific signing properties panel.
  Rationale: certificate import is a reusable-object management action. The signing shell should continue selecting/applying configurations for the current document, while the app frame owns top-level management entry points.
  Date/Author: 2026-05-09 / Codex

- Decision: do not persist certificate passwords in this slice.
  Rationale: `docs/SCHEMAS.md` forbids secret material in ordinary config payloads, and the credential-store adapter is still pending. The existing signing shell password field already supports typing the password at apply/sign time.
  Date/Author: 2026-05-09 / Codex

- Decision: add an application service for PKCS#12 import instead of implementing copy/parse logic directly in Qt code.
  Rationale: import validation, subject extraction, id generation, managed filename generation, and catalog persistence are application behavior that can be tested without PySide fakes. The app frame should remain a thin UI owner.
  Date/Author: 2026-05-09 / Codex

## Outcomes & Retrospective

At plan creation time, this slice was expected to close the first concrete part of the documented certificate-management gap: importing an existing certificate configuration. Implementation met this first-slice goal. `CertificateImportService` imports existing PKCS#12 files into managed storage, the app frame exposes `Settings > Import certificate...`, and loaded signing shells can refresh their certificate selector after import. Password persistence, self-signed certificate creation, export/backup, and deletion remain pending.

## Context and Orientation

FoliaSeal is a Qt desktop PDF signing app. A certificate in this context is a PKCS#12 file, usually ending in `.p12` or `.pfx`, that contains signing key material and a certificate. A `ManagedCertificate` is the app-owned file record for a certificate copied into FoliaSeal's managed storage. A `CertificateConfiguration` is the user-facing saved signing identity that points at a managed certificate.

The relevant persistence types live in `src/foliaseal/infra/config/schemas.py`: `ManagedCertificateSubjectSummary`, `ManagedCertificate`, `CertificateConfiguration`, and `CertificateCatalog`. The store lives in `src/foliaseal/infra/config/certificate_storage.py` as `CertificateCatalogStore`. The app frame lives in `src/foliaseal/presentation/qt/app_frame.py` and owns top-level menus. The signing shell lives in `src/foliaseal/presentation/qt/signing_shell.py` and already consumes a `CertificateCatalogStore` to populate a saved-certificate combo box.

`docs/SPEC.md` and `docs/SCHEMAS.md` are frozen without explicit user permission. Do not edit those files in this slice. Update `docs/ARCHITECTURE.md` because this slice changes app-frame responsibilities and partially closes a known debt. Update this plan and the parent schema-alignment plan because they are active implementation documentation.

## Plan of Work

First, add `src/foliaseal/application/certificate_import.py`. Define a `CertificateImportService` that receives a `CertificateCatalogStore` and imports one PKCS#12 file. The public method should accept a source path, a display name, and a passphrase string. It should read and parse the PKCS#12 using `cryptography.hazmat.primitives.serialization.pkcs12.load_key_and_certificates()`. It should reject missing files, blank display names, malformed PKCS#12 payloads, wrong passwords, and payloads without both private key and certificate. On success, it should generate stable ids with `uuid.uuid4()`, generate an app-owned storage filename such as `cert_<uuid>.p12`, copy the source bytes into `store.managed_certificate_dir`, create a `ManagedCertificate` with `source_kind="imported"`, create a `CertificateConfiguration` with `save_password=False` and no secret reference, and persist both in one catalog save. Subject summary fields should come from certificate subject common name, email, title or organizational unit, and organization.

Second, add focused unit tests in a new `tests/unit/test_certificate_import.py`. Use a small local helper to create a temporary PKCS#12 with `cryptography`. Test that import copies the file, persists both records, extracts subject summary, does not save passwords, and rejects wrong passwords or duplicate display names clearly. If duplicate display names are already rejected by `CertificateCatalog` validation, the service should surface `ConfigValidationError` without copying a second managed file.

Third, extend `src/foliaseal/presentation/qt/app_frame.py`. Add `q_check_box` only if needed; the preferred first version needs no checkbox because password saving is out of scope. Add a `CertificateImportDialog` with file path, display name, password, Import, and Cancel controls. Add a menu action under `Settings` named `Import certificate...`. The dialog may include a "Choose..." button that calls `QFileDialog.getOpenFileName()` for `PKCS#12 files (*.p12 *.pfx);;All files (*)`; tests may also set the file path line edit directly. When import succeeds, call the service, update the app-frame's certificate catalog store if needed, show an informational message if available, and refresh a loaded shell.

Fourth, add a public refresh method to `SigningWorkspaceWidget` if needed. Avoid reaching into private panel fields from the app frame. A small method such as `refresh_certificate_configurations()` can delegate to the properties panel to reload its certificate catalog and combo box from the existing store. If a shell is loaded when a certificate is imported, the app frame should call that method so the new configuration appears without reopening the PDF.

Fifth, update tests in `tests/unit/test_qt_app_frame.py` and possibly `tests/unit/test_qt_signing_shell.py`. App-frame tests should prove the menu action opens the certificate import dialog, saving imports a PKCS#12 into the injected store, and a loaded fake shell refresh method is called. Signing-shell tests should prove the public refresh method reloads the certificate combo from the store. Keep these tests fake-binding friendly and avoid launching a real GUI.

Finally, update `docs/ARCHITECTURE.md` and `docs/ExecPlans/schema_model_alignment_execplan.md`. Architecture should say the app frame now owns a first-pass certificate import dialog and that full management is still pending for create/export/delete/secure password storage.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Focused tests while developing:

    .venv/bin/python -m pytest -q tests/unit/test_certificate_import.py tests/unit/test_qt_app_frame.py tests/unit/test_qt_signing_shell.py tests/unit/test_certificate_storage.py

Before commit:

    .venv/bin/python -m ruff check .
    .venv/bin/python -m pytest -q

## Validation and Acceptance

This slice is accepted when a test can import a real temporary PKCS#12 through the application service and observe a copied managed file plus persisted `ManagedCertificate` and `CertificateConfiguration` records. It is accepted at the GUI layer when the app-frame menu exposes `Import certificate...`, the dialog imports through `CertificateCatalogStore`, and an already loaded shell refreshes its certificate selector.

The full unit suite and Ruff must pass. No generated harness artifacts are expected.

## Idempotence and Recovery

If import validation fails, the service should raise a clear exception and should not leave a copied managed file behind for that failed attempt. If persistence fails after copying, delete the just-copied file before re-raising where practical. Re-running tests should create fresh temporary directories and should not depend on global user certificate storage.

Do not edit `docs/SPEC.md` or `docs/SCHEMAS.md` without explicit user approval. Do not include self-signed certificate creation, certificate export/backup, certificate deletion, or password persistence in this slice.

## Artifacts and Notes

No generated artifacts were expected or produced.

Validation transcript:

    .venv/bin/python -m pytest -q tests/unit/test_certificate_import.py tests/unit/test_qt_app_frame.py tests/unit/test_qt_signing_shell.py tests/unit/test_certificate_storage.py
    79 passed in 26.11s

    .venv/bin/python -m ruff check .
    All checks passed!

    .venv/bin/python -m pytest -q
    584 passed, 23 skipped, 1 warning in 231.92s (0:03:51)

Revision note: Created 2026-05-09 by Codex to implement the first certificate-management slice after schema/app-settings cleanup.

Revision note: Updated 2026-05-09 by Codex after implementing the service, app-frame dialog, shell refresh, docs, and validation.
