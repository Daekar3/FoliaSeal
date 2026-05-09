# Schema Model Alignment Slice 5A Compliance Follow-up

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

This follow-up closes compliance findings from the Slice 5A review. After this change, first-pass PKCS#12 import rejects blank import passwords so imported configurations remain compatible with the current signing-material resolver, and the architecture/parent schema-alignment plan describe the newly added certificate import flow without stale pre-catalog wording.

## Child ExecPlan Dependencies

- [x] Slice 5A is implemented and committed as `135372c Add PKCS12 certificate import flow`.
- [x] Slice 5A plan bookkeeping is committed as `64cd524 Record certificate import plan commit`.

## Progress

- [x] (2026-05-09T14:02Z) Received compliance review findings for Slice 5A implementation and documentation.
- [x] (2026-05-09T14:06Z) Rejected blank PKCS#12 import passwords and covered the behavior with tests.
- [x] (2026-05-09T14:07Z) Updated architecture and parent schema-alignment plan wording for certificate import/current certificate state.
- [x] (2026-05-09T14:08Z) Ran focused tests successfully: `108 passed`.
- [x] (2026-05-09T14:13Z) Ran Ruff and the full unit suite successfully.
- [ ] Commit the compliance follow-up.

## Surprises & Discoveries

- Observation: unencrypted PKCS#12 import created a configuration that the current signing-material resolver could not apply, because blank passwords are rejected at signing time.
  Evidence: `CertificateImportService._load_pkcs12()` accepted a blank passphrase as `None`, while `CertificateSigningMaterialResolver` requires a nonblank password when no saved password secret is available.

- Observation: the parent schema-alignment plan still contained current-state wording from before the certificate catalog/resolver work.
  Evidence: compliance review found references to certificate handling as raw runtime state and direct workflow PKCS#12 preview reads.

## Decision Log

- Decision: reject blank import passwords instead of adding no-password signing support in this follow-up.
  Rationale: Slice 5A deliberately avoids password persistence and broader signing-material semantics. Requiring a password-protected PKCS#12 keeps imported configurations compatible with the current shell and resolver while leaving explicit no-password certificate support for a later design slice.
  Date/Author: 2026-05-09 / Codex

## Outcomes & Retrospective

The follow-up closed the Slice 5A compliance findings. `CertificateImportService` now rejects blank import passwords before attempting PKCS#12 parsing or managed-file copy, which keeps imported configurations compatible with the current signing-material resolver. Architecture and parent schema-alignment documentation now describe the app-frame certificate import flow and the current catalog/resolver/import split.

## Context and Orientation

`src/foliaseal/application/certificate_import.py` owns first-pass PKCS#12 import. It stores `CertificateConfiguration(save_password=False, password_secret_ref=None)`, so the user must type the certificate password in the signing shell before applying or signing with the imported configuration. The current `CertificateSigningMaterialResolver` rejects blank passwords for configurations without a saved password reference.

`docs/ARCHITECTURE.md` is the current architecture map. `docs/ExecPlans/schema_model_alignment_execplan.md` is the parent living plan for schema/model alignment. `docs/SPEC.md` and `docs/SCHEMAS.md` remain frozen for this follow-up.

## Plan of Work

First, update `CertificateImportService.import_pkcs12()` or `_load_pkcs12()` to reject blank import passwords with a clear `CertificateImportError`. Add a unit test using an unencrypted PKCS#12 fixture to prove blank-password import fails before copying into managed storage.

Second, update `docs/ARCHITECTURE.md` so the certificate catalog contract lists `CertificateImportService` and the app-frame import dialog as current producers, and so the Qt application-frame control flow includes `Settings > Import certificate...` and loaded-shell refresh.

Third, update `docs/ExecPlans/schema_model_alignment_execplan.md` to replace stale current-state certificate observations with the current catalog/resolver/import split.

Finally, run focused tests, Ruff, and the full unit suite before committing.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Focused validation:

    .venv/bin/python -m pytest -q tests/unit/test_certificate_import.py tests/unit/test_qt_app_frame.py tests/unit/test_qt_signing_shell.py tests/unit/test_certificate_storage.py tests/unit/test_config_schemas.py

Full validation:

    .venv/bin/python -m ruff check .
    .venv/bin/python -m pytest -q

## Validation and Acceptance

The follow-up is accepted when blank-password PKCS#12 import is rejected without leaving a managed copy, existing encrypted import behavior still passes, architecture and parent-plan wording match the Slice 5A implementation, and the validation commands pass.

## Idempotence and Recovery

The new validation happens before managed-file copy, so failed blank-password imports should leave no certificate catalog entries and no managed certificate directory. Documentation edits are additive/current-state corrections only.

## Artifacts and Notes

No generated artifacts are expected.

Validation transcript:

    .venv/bin/python -m pytest -q tests/unit/test_certificate_import.py tests/unit/test_qt_app_frame.py tests/unit/test_qt_signing_shell.py tests/unit/test_certificate_storage.py tests/unit/test_config_schemas.py
    108 passed in 27.06s

    .venv/bin/python -m ruff check .
    All checks passed!

    .venv/bin/python -m pytest -q
    585 passed, 23 skipped, 1 warning in 252.66s (0:04:12)

Revision note: Created 2026-05-09 by Codex after Slice 5A compliance review.
