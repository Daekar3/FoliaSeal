# Deepen the certificate lifecycle boundary and remove obsolete internal naming

This ExecPlan is a living document and must be maintained according to
`.agents/skills/write-execplan/PLANS.md`. It is intentionally a complete,
one-slice DevLoop: implementation, compatibility-cruft removal, validation,
architecture review, documentation reconciliation, nomenclature cleanup, and
commit closure are all part of this plan. Milestones organize the work; they
are not stopping points.

## Purpose / Big Picture

FoliaSeal users can already create, import, rename, export, and delete managed
certificates, but the behavior is split across two nearly identical services,
a thin lifecycle wrapper, concrete infrastructure objects, and Qt dialog
orchestration. After this slice, the application will expose one explicit
certificate manager boundary. It will own certificate policy, catalog updates,
secret-save rules, file sequencing, and rollback while Qt dialogs only collect
inputs and render results. A failure during managed-file deletion will not leave
the catalog and file out of sync.

The existing user-visible catalog schema, managed-file locations, secret-store
behavior, SPEC-required configuration semantics, and certificate import/create
behavior remain intact. Internal duplicate protocols, services, result fields
that describe UI behavior, and dead compatibility exports are removed rather
than preserved as aliases. The slice also begins stripping obsolete `phase3`
nomenclature from the shared test-builder support module, while leaving stable
Phase 3 evidence modules and persisted evidence names untouched because they
are unrelated external contracts.

## Child ExecPlan Dependencies

The compliance follow-up is tracked in
`docs/ExecPlans/certificate_lifecycle_hybrid_compliance_followup_execplan.md`
and is complete. If a future review identifies a required behavior change
outside certificate lifecycle, storage atomicity, Qt certificate dialogs, or
the explicitly scoped test-support rename, create another child plan before
expanding the implementation. Do not add a compatibility shim merely to avoid
deciding ownership.

## Progress

- [x] (2026-08-02) Fresh `explorer-light` review confirmed clean `main`, the current certificate contracts, duplicate secret protocols, catalog-first managed-file deletion, and the safe one-slice boundary.
- [x] (2026-08-02) Selected the recommended hybrid: explicit common lifecycle operations with typed requests/results, internally backed by narrow catalog, file, secret, and certificate-material adapters.
- [x] (2026-08-02) Created this living ExecPlan before implementation.
- [x] (2026-08-02) Baseline certificate slice passed 57 tests on clean `main` at `c4ee23e49`.
- [x] (2026-08-02) Replaced the split creation/import/lifecycle application services with one neutral `CertificateManager`, typed requests/results, and one secret protocol.
- [x] (2026-08-02) Moved policy, rollback, and persistence sequencing out of Qt certificate dialogs and app-frame routing; retained the explicitly tested dialog-inspection snapshot as transitional presentation compatibility.
- [x] (2026-08-02) Hardened managed-certificate deletion with staged file removal and catalog/file restoration on final unlink failure.
- [x] (2026-08-02) Removed duplicate service modules, duplicate secret protocols, and obsolete application exports.
- [x] (2026-08-02) Renamed the shared `tests/support/phase3_builders.py` support module and support test to neutral signing terminology; updated all imports without renaming stable Phase 3 evidence modules.
- [x] (2026-08-02) Focused manager/storage/Qt/support validation passed 36 tests; full suite passed 1021 tests with one pre-existing Pillow warning; Ruff, compileall, and diff checks are clean.
- [x] (2026-08-02) Reconciled current README and architecture documentation to the `CertificateManager` typed request/result boundary, app-frame refresh flow, and actual `ValueError`/`ConfigValidationError` behavior; historical plan records and stable Phase 3 evidence names remain unchanged.
- [x] (2026-08-02) Documentation diff check and `compileall` passed; final review found no stale legacy names in current architecture or README.
- [x] (2026-08-02) Post-fix compliance review passed: focused manager/app-frame/storage/schema validation passed 65 tests; no deleted source/test/support imports or stale current architecture names remain.

## Surprises & Discoveries

- Observation: `CertificateLifecycleService` constructs `CertificateCreationService` and `CertificateImportService` on every call, while those services each declare their own equivalent `CertificateSecretStore` protocol.
  Evidence: `src/foliaseal/application/certificate_lifecycle.py` delegates at lines 80-132; both creation/import modules define the same secret methods.
- Observation: Managed-certificate deletion persists the catalog before unlinking the managed file.
  Evidence: `CertificateCatalogStore.delete_managed_certificate_by_id()` calls `save_catalog()` and then `unlink()`, so an unlink error can orphan the file while the record is already gone.
- Observation: `CertificateDialogOutcome` and `CertificateDialogCompatibilityState` are deliberate frame/test inspection surfaces, not proven-dead aliases.
  Evidence: the explorer found current Qt tests and app-frame routing still inspect those payloads; they must be removed only after callers migrate or retained at a narrow test-only edge.
- Observation: `tests/support/phase3_builders.py` contains certificate builders mixed with general signing/appearance builders and is imported by many tests.
  Evidence: repository search found certificate and non-certificate consumers; rename the support module mechanically, but do not broaden the slice into production Phase 3 harness renaming.

## Decision Log

- Decision: Use a neutral `CertificateManager` with explicit operations rather than a generic `run(mode=...)` dispatcher.
  Rationale: create, import, rename, delete, and export have different required inputs and failure semantics; explicit methods keep those contracts visible and avoid another tagged registry.
  Date/Author: 2026-08-02 / Codex.
- Decision: Use typed request/result values and remove `refresh_shell` and `user_message` from the application result contract.
  Rationale: refresh and presentation text are Qt concerns. The result will carry operation kind, updated catalog, and affected records/paths; the presentation controller decides how to render and refresh exactly once.
  Date/Author: 2026-08-02 / Codex.
- Decision: Reuse the existing catalog and secret adapters initially, adding narrow protocols at the application boundary rather than introducing a generalized recovery journal or remote certificate-source registry.
  Rationale: this keeps the implementation demonstrable in one slice while still making filesystem, secret, and certificate-material dependencies replaceable in tests. Future source kinds can be added after a real requirement appears.
  Date/Author: 2026-08-02 / Codex.
- Decision: Preserve schema fields, managed storage paths, secret-tool behavior, and SPEC semantics; isolate any legacy JSON conversion below the repository boundary.
  Rationale: these are user data and product contracts. Internal aliases and duplicate protocols are cruft; persisted data is not.
  Date/Author: 2026-08-02 / Codex.
- Decision: Rename only the shared test support module from `phase3_builders` to neutral signing terminology in this slice.
  Rationale: the module is internal and its name is obsolete, while `phase3_harness*`, `phase3_signing_backend`, evidence schema strings, artifact paths, and CLI commands are stable evidence contracts outside certificate lifecycle.
  Date/Author: 2026-08-02 / Codex.

## Outcomes & Retrospective

The manager boundary, deleted compatibility pieces, deletion-failure
restoration, test counts, and neutral support-module rename are complete.
Post-implementation review identified documentation drift: current prose still
named the removed lifecycle/import services and a dedicated import exception.
README, architecture ownership/flow/catalog/error/debt sections, and the living
compliance child plan now describe `CertificateManager`, typed requests/results,
and `ValueError` plus `ConfigValidationError` behavior. Historical ExecPlans
retain their original terminology as records of past architecture, and stable
Phase 3 evidence/harness nomenclature was not changed. Two initial compliance
reviews found only documentation drift; the documentation worker fixed it and a
post-fix review passed.

## Context and Orientation

`src/foliaseal/application/certificate_manager.py` is the current caller
boundary. It validates and materializes self-signed or imported PKCS#12 files,
creates the persisted catalog records, owns configuration edits and
secret/file rollback, and returns typed operation results without Qt refresh or
message policy. The former creation/import/lifecycle modules were removed after
their behavior moved behind this manager.

`src/foliaseal/infra/config/certificate_storage.py` persists
`CertificateCatalog` JSON atomically and owns files below the managed
certificate directory. `src/foliaseal/infra/secret_storage.py` adapts the
system secret tool. `src/foliaseal/infra/config/schemas.py` defines the
persisted `ManagedCertificate` and `CertificateConfiguration` records.

`src/foliaseal/presentation/qt/app_frame_certificate_management.py` owns the
three certificate dialogs and their widget interaction. Dialogs submit typed
requests to the application manager and render messages or errors; they do not
decide catalog mutation, secret policy, file cleanup, or rollback.
`app_frame.py` composes the manager and routes Settings actions. Its dialog
inspection snapshot remains an explicitly transitional presentation seam
because current fake-Qt tests still inspect it.

The SPEC constraints that must remain true are: importing and creating
certificates are supported; configurations can be saved and loaded; saved
passwords are optional and require secure storage; certificates can be
exported/backed up; deleting a configuration does not delete its underlying
managed certificate; and deleting a managed certificate is guarded against
references. Existing IDs, `source_kind`, schema version, and managed paths are
persisted data and are not renamed.

## Plan of Work

First introduce `src/foliaseal/application/certificate_manager.py` as the
neutral application boundary. Define immutable request values for self-signed
creation, PKCS#12 import, configuration save/rename, and export. Define
`CertificateOperationResult` with the updated `CertificateCatalog`, an explicit
operation kind, optional affected certificate/configuration records, and
optional managed/exported paths. Define one application-owned secret protocol
with the methods needed for availability, reference creation, get, set, and
delete. Define narrow catalog/file collaborators if the manager needs them for
testing; the production implementation may adapt the existing
`CertificateCatalogStore`.

Move the behavior currently duplicated in `certificate_creation.py` and
`certificate_import.py` behind private manager helpers or a small internal
certificate-source module. The manager must validate names and passwords,
allocate IDs/timestamps through injected factories, materialize or copy the
PKCS#12 file, stage saved-password writes, commit catalog records, and reverse
file/secret side effects when catalog persistence fails. Keep cryptography
details behind the source helper and keep the manager responsible for policy
and sequencing. Delete the old creation/import service modules after all
callers and tests use the manager; do not leave deprecated aliases in
`application/__init__.py`.

Move configuration rename, configuration deletion, managed-certificate
deletion, and export into the same manager. Preserve the SPEC rule that
configuration deletion removes only that configuration and its saved secret.
For managed-certificate deletion, validate the reference guard, stage the file
for removal (a temporary/quarantine path is acceptable), commit the catalog,
then finalize removal; if any step fails, restore the catalog/file where
possible and raise a typed lifecycle error with cleanup details. Export must
retain the existing outside-managed-directory and symlink protections.

Update `app_frame_certificate_management.py` to use the manager’s typed
requests/results. Keep widget validation, dialog presentation, and one refresh
callback in the presentation layer. Remove application-specific `refresh_shell`
and `user_message` decisions from the manager. Remove
`CertificateDialogOutcome`/`CertificateDialogCompatibilityState` only if
repository-wide search shows no remaining production or test consumer; if a
window-level inspection contract is still required, keep the smallest explicit
presentation adapter and record it as transitional debt rather than exposing
it from the application manager.

Rename `tests/support/phase3_builders.py` to
`tests/support/signing_builders.py`, rename its support test to neutral signing
terminology, and update every import. Preserve function behavior. Do not
rename `phase3_harness.py`, `phase3_signing_backend.py`, Phase 3 evidence
result names, schema strings, CLI commands, artifact paths, or unrelated
historical ExecPlans in this slice; repository search must document these as
intentional external or out-of-scope contracts.

Replace service-specific tests with manager-boundary tests. Cover successful
create/import/rename/configuration-delete/managed-delete/export; duplicate and
invalid input; optional saved-password behavior; secret-unavailable behavior;
catalog-save failure rollback; managed-file unlink failure; reference guards;
export path traversal/symlink rejection; and Qt request/response mapping with
exactly one refresh. Keep small adapter tests for catalog JSON and secret-tool
behavior, but delete tests that only assert private service delegation or
compatibility aliases.

## Concrete Steps

Run every command from `/home/daekar/FoliaSeal`.

1. Confirm the clean starting point and baseline certificate tests:

       git status --short
       git log -1 --oneline
       .venv/bin/python -m pytest -q tests/unit/test_certificate_creation.py tests/unit/test_certificate_import.py tests/unit/test_certificate_lifecycle.py tests/unit/test_certificate_storage.py tests/unit/test_qt_app_frame_certificate_management.py

   Record the baseline count in `Progress` before editing.

2. Add the manager request/result types and injected collaborators. Migrate
   `app_frame.py`, signing setup/coordinator callers, and tests to the manager
   while keeping the existing catalog and secret adapters. Run the focused
   certificate tests after each dependency-order group.

3. Move create/import logic behind the manager, delete duplicate secret
   protocols and old service exports, and add rollback tests. Then harden
   `CertificateCatalogStore.delete_managed_certificate_by_id()` or replace its
   use with manager-owned staged deletion so a failed unlink cannot silently
   lose the catalog record.

4. Migrate the Qt certificate dialogs to typed manager requests/results. Verify
   dialogs contain no catalog mutation, secret-store, or managed-file policy.
   Remove only proven-dead compatibility outcome/state objects and record any
   retained transitional adapter in the plan.

5. Rename the shared test support module and update imports. Run:

       rg -n "phase3_builders|Phase3Builders" src tests docs --glob '!docs/ExecPlans/*'

   The command must return no current support-module references. Remaining
   `phase3_*` matches must be stable evidence contracts or explicitly recorded
   historical/out-of-scope names.

6. Run focused tests, static checks, and the full suite:

       .venv/bin/python -m pytest -q tests/unit/test_certificate_creation.py tests/unit/test_certificate_import.py tests/unit/test_certificate_lifecycle.py tests/unit/test_certificate_storage.py tests/unit/test_secret_storage.py tests/unit/test_qt_app_frame_certificate_management.py tests/unit/test_certificate_manager.py
       .venv/bin/ruff check src tests
       .venv/bin/python -m compileall -q src tests
       .venv/bin/python -m pytest -q
       git diff --check

   Record exact counts and any pre-existing warnings in the plan.

7. Exercise a temporary-directory end-to-end certificate flow with deterministic
   fake secret storage: create a self-signed certificate, import a fixture,
   rename a configuration, delete the configuration while retaining the
   managed file, export a managed file outside the store, and delete an
   unreferenced managed certificate. Inject a failing unlink/store fake and
   verify the catalog/file recovery behavior. Remove the temporary directory
   and confirm no FoliaSeal/Python processes remain.

8. Spawn the required compliance explorer(s) to review `docs/SPEC.md`,
   `docs/ARCHITECTURE.md`, and current certificate tests/source. If they find a
   real discrepancy, create and execute a child compliance ExecPlan before
   closure; do not stop at the first review finding.

9. Spawn the documentation worker with architecture-steward instructions to
   update `README.md`, `docs/ARCHITECTURE.md`, and this plan. The documentation
   must describe neutral manager ownership, preserved persisted contracts,
   deletion recovery, removed compatibility cruft, and the intentionally
   unchanged stable Phase 3 evidence names.

10. Spawn the git worker with `$write-git-commit` instructions. Stage only the
    implementation, tests, documentation, and living plan(s); exclude unrelated
    historical ExecPlans and generated artifacts. Verify the commit, clean
    worktree, and final plan closure before reporting outcomes.

## Validation and Acceptance

The slice is accepted when all certificate operations are reachable through one
neutral manager boundary and the Qt layer no longer owns persistence or secret
policy. Creating/importing a certificate returns an updated catalog and typed
operation result; configuration deletion removes only the configuration and
saved secret; managed-certificate deletion refuses referenced records and keeps
catalog/file state recoverable on unlink failure; export preserves path safety;
and all existing persisted fields and managed paths remain unchanged.

The manager must be constructible with in-memory catalog/file/secret fakes. The
focused boundary suite must cover success and failure paths, including the
managed-file deletion failure that was previously unprotected. The full suite,
Ruff, compileall, and diff checks must pass. The neutral test-support rename
must be complete, and any remaining `phase3` names must be documented stable or
out of scope rather than hidden behind aliases.

## Idempotence and Recovery

Use `git mv` for module/test-support renames and update imports before deleting
old files. Keep catalog writes atomic through the existing temporary-file
replace mechanism. Stage managed-file deletions so a failed catalog commit or
unlink can restore the prior state; never delete the only copy before the
catalog commit is known to succeed. Use `tmp_path` or a fresh `mktemp` directory
for end-to-end tests and remove it afterward. If a rename or migration fails,
restore only the affected working-tree change from the current diff; do not use
destructive repository resets.

## Artifacts and Notes

Record baseline and final focused/full test counts, the exact deletion-failure
transcript, nomenclature search output, compliance findings and fixes, docs
worker result, and commit hashes here. The expected final evidence includes a
clean `git status --short`, no running FoliaSeal/Python processes, and no
temporary certificate artifacts outside the repository.

## Interfaces and Dependencies

At completion, `src/foliaseal/application/certificate_manager.py` owns the
following application-facing shape:

    class CertificateManager:
        def snapshot(self) -> CertificateCatalog: ...
        def create(self, request: CreateCertificateRequest) -> CertificateOperationResult: ...
        def import_(self, request: ImportCertificateRequest) -> CertificateOperationResult: ...
        def save_configuration(self, request: SaveConfigurationRequest) -> CertificateOperationResult: ...
        def delete_configuration(self, configuration_id: str) -> CertificateOperationResult: ...
        def delete_managed_certificate(self, certificate_id: str) -> CertificateOperationResult: ...
        def export(self, request: ExportCertificateRequest) -> CertificateOperationResult: ...

`CertificateOperationResult` contains the updated catalog, an operation kind,
optional affected records, and optional managed/export paths. It contains no Qt
refresh flag or presentation message policy. The manager depends on narrow
application protocols for catalog persistence, managed-file staging, and saved
passwords. Production adapters are the existing certificate catalog store and
secret-tool implementation; tests provide in-memory or temporary-directory
fakes. Cryptography and PKCS#12 parsing stay behind internal source helpers.

The stable persisted types remain `ManagedCertificate`,
`CertificateConfiguration`, and `CertificateCatalog` from
`infra/config/schemas.py`, including schema version, IDs, `source_kind`, and
storage filenames. Stable Phase 3 evidence modules and artifact contracts are
not renamed as part of certificate lifecycle work.

## Revision Notes

2026-08-02: Created after the required live explorer review and the three
certificate-manager interface designs. Selected the bounded hybrid of explicit
common operations, typed results, internal ports, rollback-safe storage, Qt
request/response dialogs, legacy-cruft removal, and scoped test-support
`phase3` nomenclature cleanup.
