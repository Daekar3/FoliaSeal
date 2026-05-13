# Saved Certificate Password Compliance Follow-Up

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

The previous saved-password slice added optional Linux Secret Service storage through `secret-tool` for imported PKCS#12 certificate passwords. Compliance review found that several failure paths could leave saved-password state misleading or inconsistent. After this follow-up, failures after a password is written to secure storage will clean up or restore the secret as needed, and secret lookup failures from the credential store will surface as storage failures instead of being reported as missing passwords.

This is a narrow compliance fix. It does not add new password-management UI, cross-platform credential storage, in-app certificate creation, or schema changes. It only makes the existing saved-password feature honor the recovery and error-reporting contracts already described by `docs/ExecPlans/saved_certificate_password_secret_tool_execplan.md` and `docs/ARCHITECTURE.md`.

## Child ExecPlan Dependencies

- [x] Commit `ea9ac37 Add secret-tool-backed saved certificate passwords` exists and introduced the saved-password feature.
- [x] Two compliance reviewers inspected that commit against `docs/ARCHITECTURE.md`, `docs/SCHEMAS.md`, `docs/SPEC.md`, and `docs/ExecPlans/saved_certificate_password_secret_tool_execplan.md`.
- [x] The reviewers identified import rollback, configuration-delete rollback, and secret lookup error-classification gaps.

## Progress

- [x] (2026-05-13T00:57Z) Created this follow-up ExecPlan from the combined compliance-review findings.
- [x] (2026-05-13T01:04Z) Added regression tests for import directory-preparation failure after secret write, delete-side catalog failure after secret deletion, and non-missing `secret-tool lookup` failure.
- [x] (2026-05-13T01:04Z) Updated the implementation so those regression tests pass while preserving existing saved-password behavior.
- [x] (2026-05-13T01:05Z) Focused validation passed: `.venv/bin/python -m pytest -q tests/unit/test_secret_storage.py tests/unit/test_signing_material_resolver.py tests/unit/test_certificate_import.py tests/unit/test_qt_app_frame.py` (`40 passed in 6.09s`).
- [x] (2026-05-13T01:14Z) Full validation passed: `.venv/bin/python -m ruff check .` (`All checks passed!`) and `.venv/bin/python -m pytest -q` (`623 passed, 23 skipped, 1 warning in 218.20s`).
- [x] (2026-05-13T01:16Z) Committed the compliance follow-up as `e88ae16 Harden saved certificate password handling`.
- [x] (2026-05-13T01:27Z) Re-review found three follow-up issues: import cleanup failures were explicit only by the original exception, delete restore failures were swallowed, and configurations with already-missing saved secrets became undeletable.
- [x] (2026-05-13T01:30Z) Added regression tests and implementation changes for those re-review findings.
- [x] (2026-05-13T01:31Z) Focused validation passed after the re-review fixes: `.venv/bin/python -m pytest -q tests/unit/test_secret_storage.py tests/unit/test_signing_material_resolver.py tests/unit/test_certificate_import.py tests/unit/test_qt_app_frame.py` (`43 passed in 5.49s`).
- [x] (2026-05-13T01:42Z) Full validation passed after the re-review fixes: `.venv/bin/python -m ruff check .` (`All checks passed!`) and `.venv/bin/python -m pytest -q` (`626 passed, 23 skipped, 1 warning in 220.95s`).
- [ ] Commit the re-review compliance fixes.

## Surprises & Discoveries

- Observation: Both compliance reviewers independently found the same import rollback leak and delete consistency bug.
  Evidence: Review A and Review B both cited `src/foliaseal/application/certificate_import.py` around the saved-secret write and `src/foliaseal/presentation/qt/app_frame.py` around configuration deletion.

- Observation: One reviewer also found that `SecretToolCertificateSecretStore.get_secret()` treated every nonzero `secret-tool lookup` exit as a missing secret.
  Evidence: `src/foliaseal/infra/secret_storage.py` returned `None` for any lookup return code other than zero, so backend or Secret Service failures were indistinguishable from a legitimate missing secret.

- Observation: Re-review found that rollback operations can fail because the same secure storage dependency being cleaned up may be unavailable or read-only.
  Evidence: Import cleanup calls `delete_secret()` after a post-secret-write failure, and delete rollback calls `set_secret()` after a catalog persistence failure. The updated behavior reports those cleanup failures explicitly instead of silently treating rollback as successful.

- Observation: A saved-password configuration may point at a secret that has already been removed outside FoliaSeal.
  Evidence: The Secret Service adapter treats missing secrets as idempotent for deletion, so the app-frame delete path now allows deleting that stale configuration instead of blocking it.

## Decision Log

- Decision: Keep the existing "delete the saved secret before deleting the configuration" user contract, but make the path rollback-aware by reading the secret value first and restoring it if catalog deletion fails.
  Rationale: The prior ExecPlan requires the catalog entry to remain if secure secret deletion is unavailable or fails. Deleting the catalog first would violate that contract. Reading first and restoring on persistence failure preserves the existing behavior while closing the consistency gap found in review.
  Date/Author: 2026-05-13 / Codex

- Decision: Treat `secret-tool lookup` return code `1` as "missing secret" and other nonzero return codes as `SecretStorageError`.
  Rationale: The adapter already treats `secret-tool clear` code `1` as an idempotent missing-secret result. Lookup should keep missing secrets distinct from operational failures so the resolver and GUI can show the correct kind of action.
  Date/Author: 2026-05-13 / Codex

- Decision: Surface rollback-operation failures instead of swallowing them.
  Rationale: If the secure store cannot delete a newly written secret after import failure or cannot restore a deleted secret after catalog persistence failure, the program cannot truthfully claim full recovery. The next-best compliant behavior is to make that state visible immediately so the user can repair secure storage or remove the saved secret manually.
  Date/Author: 2026-05-13 / Codex

- Decision: Allow deletion of a configuration whose saved secret is already missing.
  Rationale: A missing secret means the configuration is already stale. Blocking deletion traps the user in the broken state; treating missing secret deletion as idempotent matches the `secret-tool clear` adapter behavior.
  Date/Author: 2026-05-13 / Codex

## Outcomes & Retrospective

This follow-up remains open after re-review. The first compliance follow-up was committed as `e88ae16 Harden saved certificate password handling`; re-review then found additional edge cases around rollback failure reporting and already-missing saved secrets. Focused tests, Ruff, and the full unit suite now pass for those edge cases. The remaining work is to commit the re-review fixes and complete a final compliance re-review.

## Context and Orientation

FoliaSeal imports existing PKCS#12 certificates through `src/foliaseal/application/certificate_import.py`. A PKCS#12 file contains a private key and certificate in one password-protected file. When the user checks "Save password securely" in the Qt app frame, `CertificateImportService.import_pkcs12()` stores the password through a secret store and writes only an opaque `password_secret_ref` into `certificates.json`.

The Linux Secret Service adapter lives in `src/foliaseal/infra/secret_storage.py`. It shells out to `secret-tool`, a command-line program that talks to the desktop credential store. The adapter exposes `set_secret()`, `get_secret()`, and `delete_secret()`, and tests inject a fake runner so unit tests do not touch a real credential store.

The certificate-management UI lives in `src/foliaseal/presentation/qt/app_frame.py`. `CertificateConfigurationManagementDialog.delete_selected_configuration()` deletes a saved secret when the deleted configuration has a `password_secret_ref`, then removes the configuration from `CertificateCatalogStore`. The reviewed bug is that a catalog write failure after the secret delete can leave the saved configuration on disk pointing at a secret that no longer exists.

## Plan of Work

First, add regression coverage in `tests/unit/test_certificate_import.py` proving that if `CertificateImportService.import_pkcs12()` writes a secret and then fails while preparing the certificate storage directories, it deletes the just-written secret and does not leave a managed PKCS#12 file.

Second, add regression coverage in `tests/unit/test_qt_app_frame.py` proving that if configuration deletion removes the saved secret and then catalog persistence fails, the dialog restores the saved secret, leaves the configuration in place, reports the persistence error, and does not emit a certificate-catalog change notification. Also cover the two re-review edge cases: if restore itself fails, the dialog reports the restore failure explicitly, and if the saved secret is already missing before deletion, deletion still removes the stale configuration.

Third, add regression coverage in `tests/unit/test_secret_storage.py` and `tests/unit/test_signing_material_resolver.py` proving that `secret-tool lookup` return code `1` still means "missing secret", while another nonzero return code raises `SecretStorageError` and is converted by the resolver into `SigningMaterialResolutionError`.

Fourth, update `src/foliaseal/application/certificate_import.py` so everything that can fail after `set_secret()` is inside the cleanup guard. Update `src/foliaseal/presentation/qt/app_frame.py` so the delete path reads the secret before deletion and restores it if catalog deletion fails. Update `src/foliaseal/infra/secret_storage.py` and `src/foliaseal/application/signing_material_resolver.py` so backend lookup failures surface as storage errors.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Run focused validation while developing:

    .venv/bin/python -m pytest -q tests/unit/test_secret_storage.py tests/unit/test_signing_material_resolver.py tests/unit/test_certificate_import.py tests/unit/test_qt_app_frame.py

Before committing, run:

    .venv/bin/python -m ruff check .
    .venv/bin/python -m pytest -q

## Validation and Acceptance

This follow-up is accepted when the new tests demonstrate that import cleans up a saved secret after directory-preparation failure, import reports secure-storage cleanup failure if cleanup itself fails, configuration deletion restores a saved secret after catalog persistence failure, configuration deletion reports restore failure if restore itself fails, stale configurations whose saved secret is already missing remain deletable, lookup return code `1` remains a missing secret, and other lookup failures become storage-resolution failures. Existing happy-path saved-password import, signing, and deletion tests must continue to pass.

No generated harness artifacts are expected.

## Idempotence and Recovery

The changes are additive and testable. The import cleanup path may be retried safely when secure storage cleanup succeeds because it removes the copied managed file and saved secret before re-raising the original failure. If secure storage cleanup fails, the import reports that failure explicitly so the user can remove the saved secret before retrying. The delete rollback path may be retried safely when restore succeeds because it restores the secret value if the catalog entry remains due to persistence failure. If restore fails, the dialog reports that failure explicitly so the user knows the saved-password configuration remains but its secret could not be restored.

Do not edit `docs/SPEC.md` or `docs/SCHEMAS.md` without explicit user approval.

## Artifacts and Notes

No generated artifacts are expected.

Revision note: Created 2026-05-13 by Codex to address compliance-review findings after the saved certificate password Secret Service slice.

Revision note: Updated 2026-05-13 by Codex after adding rollback and lookup-failure regression tests and passing focused validation.

Revision note: Updated 2026-05-13 by Codex after Ruff and full unit validation passed.

Revision note: Updated 2026-05-13 by Codex after committing the compliance follow-up.

Revision note: Updated 2026-05-13 by Codex after compliance re-review found rollback failure-reporting gaps and an already-missing saved-secret deletion edge case.

Revision note: Updated 2026-05-13 by Codex after Ruff and full unit validation passed for the re-review fixes.
