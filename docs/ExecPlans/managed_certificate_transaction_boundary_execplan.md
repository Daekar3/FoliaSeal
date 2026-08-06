# Move Managed-Certificate Transactions Behind the Repository Boundary

This ExecPlan is a living document and must be maintained according to
`.agents/skills/write-execplan/PLANS.md`. It is the child plan selected by Design Selection 36 in
the architecture-improvement parent plan.

## Purpose / Big Picture

Certificate creation, import, and deletion must leave the catalog, managed PKCS#12 files, and saved
password references consistent even when a filesystem or catalog write fails. Today the application
manager performs path mutation and rollback itself, so a small persistence change requires knowing
filesystem sequencing and an infrastructure exception type. After this slice, the manager will
continue to own certificate policy and user-facing operations, while the repository will own the
file/catalog transaction. The existing GUI and signing behavior will be unchanged and can be
verified with the certificate-manager tests, Qt certificate-dialog tests, and the existing offscreen
acceptance matrices.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md` and `docs/ARCHITECTURE.md` are frozen/current for this slice.
- [x] `CertificateCatalogRepository`, `InMemoryCertificateCatalogRepository`, and
  `CertificateCatalogStore` are present and their existing tests pass.
- [x] Design Selection 36 selected common-caller operation-scoped atomic verbs plus an application-
  owned secret error boundary.
- [x] Implementation, focused/full validation, compliance review, and documentation.
- [x] (2026-08-06) Offscreen acceptance evidence passes; generated summary removed and product
  process audit is clean.
- [ ] Intentional commit and fresh three-explorer rescan.

## Progress

- [x] (2026-08-06) Recorded the baseline seam: manager path writes/staging/rollback and direct
  `SecretStorageError` import; production store deletion is catalog-first then unlink.
- [x] (2026-08-06) Compared minimal, flexible transaction, and common-caller designs; selected
  operation-scoped atomic repository verbs with a narrow secret error protocol.
- [x] (2026-08-06) Clarified delete semantics after implementation review: the repository receives
  both the original and candidate catalogs so it can validate the supplied snapshot before staging.
- [x] (2026-08-06) Added the application-owned secret protocol/error and adapter translation.
- [x] (2026-08-06) Added repository commit/delete operations with filesystem snapshots/quarantine
  recovery and in-memory adapter behavior.
- [x] (2026-08-06) Migrated manager create/import/delete paths; direct manager filesystem
  choreography and infra secret imports are removed.
- [x] (2026-08-06) Added repository/manager rollback, no-path fake, secret cleanup, and import-
  isolation tests; certificate boundary tests pass (`35`).
- [x] (2026-08-06) Reconciled architecture docs and this plan; resolver path properties and phase3
  contracts remain explicitly out of scope.
- [x] (2026-08-06) Focused certificate boundary validation passes (`38` tests); the full suite also
  passes (`1127` tests, one pre-existing Pillow deprecation warning).
- [x] (2026-08-06) Offscreen evidence passes: signed acceptance `10/7`, preview parity `18/18`,
  and fit rejection `3/3`; the generated summary was removed and no product Python/Qt process
  remains.
- [ ] Intentional commit and fresh three-explorer rescan.

## Surprises & Discoveries

- Observation: the application repository protocol exposes `storage_dir` and
  `managed_certificate_dir`, but the signature-properties coordinator still uses the managed
  directory to construct the signing-material resolver.
  Evidence: `src/foliaseal/application/signature_properties_coordinator.py:254-279` and
  `src/foliaseal/application/signing_material_resolver.py:43-100`.
  Consequence: this slice removes manager access and leaves those concrete locator properties as an
  explicitly documented follow-up; deleting them here would mix a resolver migration into the
  transaction refactor.
- Observation: `CertificateCatalogStore.delete_managed_certificate_by_id()` persists the catalog
  before unlinking the file, while the manager has a separate staged-delete implementation.
  Evidence: `src/foliaseal/infra/config/certificate_storage.py:136-145` versus
  `src/foliaseal/application/certificate_manager.py:227-253`.
- Observation: existing tests assert `CertificateOperationResult.managed_file_path` exists.
  Evidence: `tests/unit/test_certificate_manager.py:88-110`.
  Consequence: preserve that field through a typed commit result during this slice; retire the
  remaining path-valued compatibility result only in a later material-resolution migration.
- Observation: the compliance review found adapter parity and failure-reporting gaps beyond the
  original manager choreography: in-memory bytes were not isolated, broken symlink exports were not
  rejected, and a secret provider could raise after deleting its value.
  Evidence: new in-memory byte-map tests, broken-symlink export tests, and partial-secret-delete tests
  now pass; the production adapter uses `Path.is_symlink()` and recovery cleans restore temporaries.

## Decision Log

- Decision: Add operation-scoped repository verbs rather than a generic transaction/context API.
  Rationale: create/import and managed-delete are the only callers; one verb hides all critical
  file/catalog sequencing without exposing a rollback state machine to callers.
  Date/Author: 2026-08-06 / Codex and two independent design reviewers.
- Decision: Preserve `CertificateManager` public methods, request types, operation names, result
  fields, catalog JSON, filenames, secret references, and exception messages wherever current tests
  prove them.
  Rationale: the SPEC-visible certificate workflow is already functional; this is a boundary and
  reliability refactor, not a schema or GUI redesign.
  Date/Author: 2026-08-06 / Codex.
- Decision: Introduce `CertificateSecretStoreError` in an application-owned module. The infra
  `SecretStorageError` adapter error may subclass it so existing adapter tests remain meaningful,
  but `certificate_manager.py` must no longer import `foliaseal.infra.secret_storage`.
  Rationale: application rollback policy must not depend on an infrastructure exception class.
  Date/Author: 2026-08-06 / Codex.
- Decision: Keep repository path properties only for the existing signing-material resolver seam.
  Rationale: removing them now would require migrating `DefaultSignaturePropertiesCoordinator`,
  `CertificateSigningMaterialResolver`, and many GUI tests; that is a separate bounded child.
  Date/Author: 2026-08-06 / Codex.
- Decision: Do not rename phase3 modules, commands, DTOs, JSON keys, fixtures, or artifacts.
  Rationale: the dedicated nomenclature plan requires one atomic/versioned migration.
  Date/Author: 2026-08-06 / Codex.
- Decision: Treat adapter parity/security fixes and partial-secret-delete compensation as part of
  this transaction slice.
  Rationale: they are direct consequences of moving the transaction boundary and were concrete
  compliance findings, not unrelated feature work.
  Date/Author: 2026-08-06 / Codex.

## Outcomes & Retrospective

The transaction boundary is implemented. `CertificateManager` retains certificate policy, PKCS#12
generation/parsing, saved-secret compensation, export, and typed operation results. Atomic managed
certificate commit/delete verbs now live on `CertificateCatalogRepository`; `CertificateCatalogStore`
owns filesystem/catalog staging and recovery, while `InMemoryCertificateCatalogRepository` mirrors
the contract with an isolated filename-to-bytes map. The application-owned `CertificateSecretStoreError`
boundary has an infrastructure `SecretStorageError` subclass. Broken-symlink/export rejection,
missing-file/delete parity, and rollback compensation are covered by the focused boundary tests.

Validation records 38 focused certificate-boundary tests and 1127 full-suite tests passing, plus
Ruff, compileall, CLI help, and diff checks. Offscreen evidence passes signed acceptance `10/7`,
preview parity `18/18`, and fit rejection `3/3`; its generated summary was removed and the product
process audit is clean. Architecture and this child plan were reconciled. Commit and the fresh
three-explorer rescan remain pending; resolver path properties and phase3 nomenclature/contracts
are explicit follow-ups rather than part of this slice.

## Context and Orientation

`src/foliaseal/application/certificate_manager.py` owns certificate names, IDs, PKCS#12 generation
and parsing, secret-save policy, and `CertificateOperationResult`. Its `create()` and `import_()`
methods call `_commit_new_certificate()`, which currently creates directories, writes bytes, saves
the catalog, and manually deletes the file and saved secret on failure. Its
`delete_managed_certificate()` currently stages a file with `Path.replace`, saves a catalog without
the record, unlinks the staged file, and restores both pieces on failure.

`src/foliaseal/application/certificate_catalog_repository.py` is the application persistence port;
`InMemoryCertificateCatalogRepository` is the test adapter. `src/foliaseal/infra/config/
certificate_storage.py` is the production filesystem adapter and must own directory creation,
temporary-file/quarantine handling, catalog persistence ordering, and recovery. The current
`export_managed_certificate_by_id()` security checks remain in the adapter and are not redesigned.

`src/foliaseal/infra/secret_storage.py` talks to Linux Secret Service through `secret-tool`. The
application manager should depend only on the protocol and error declared in the application-owned
secret module. The secret operation is still a separate external side effect; the manager keeps its
existing compensating set/delete/restore ordering and error wording.

## Plan of Work

First add `src/foliaseal/application/certificate_secret_store.py` with the existing
`CertificateSecretStore` protocol and an application-owned `CertificateSecretStoreError`; have
`certificate_manager.py` import the protocol from that module so the lazy application exports and
application boundary stay infrastructure-free.
Change `SecretToolCertificateSecretStore` so its adapter-specific error subclasses the application-
owned error; preserve `SecretStorageError` for its current direct adapter tests, while the manager
translates secret-provider failures through the application-owned boundary and compensates any
partial mutation.

Next extend `CertificateCatalogRepository` with these exact behavior-bearing values and methods:

    @dataclass(frozen=True)
    class ManagedCertificateCommit:
        catalog: CertificateCatalog
        managed_file_path: Path

    def commit_managed_certificate(
        self,
        *,
        payload: bytes,
        managed_certificate: ManagedCertificate,
        catalog: CertificateCatalog,
    ) -> ManagedCertificateCommit: ...

    def delete_managed_certificate(
        self,
        *,
        managed_certificate: ManagedCertificate,
        original_catalog: CertificateCatalog,
        updated_catalog: CertificateCatalog,
    ) -> None: ...

The commit verb must create the managed directory, write the payload, persist the supplied catalog,
and restore the prior file/catalog if any step fails. It returns the adapter-owned path only through
the transitional result needed by `CertificateOperationResult.managed_file_path`. The delete verb
must validate that `updated_catalog` equals
`original_catalog.remove_managed_certificate_by_id(...)` and that the certificate is unreferenced,
quarantine the file before catalog persistence, finalize removal only after persistence succeeds,
and restore both file and catalog on failure. Missing managed files preserve current delete
semantics (the catalog can still be removed).
The adapter must re-raise the original operation error when recovery succeeds and raise
`CertificateManagerError`-compatible failure text only when recovery itself is incomplete.

Implement the same contract in `InMemoryCertificateCatalogRepository` with an in-memory mapping of
storage filename to bytes and snapshots for rollback. Its tests must prove behavior without any
filesystem path attributes. Keep its existing path fields only for the separate resolver tests until
that follow-up migration is executed.

Then migrate `CertificateManager._commit_new_certificate()` to compute the candidate catalog and
call `store.commit_managed_certificate(...)`; remove its directory creation, `write_bytes`, and
file-unlink cleanup. Continue compensating a saved password through `CertificateSecretStore`. Replace
the manager's staged `delete_managed_certificate()` choreography with one repository
`delete_managed_certificate(...)` call using the already validated certificate, original catalog,
and updated catalog.
Keep `save_configuration`, configuration secret restoration, export, request/result classes, and
public operation strings unchanged.

Add tests at the new boundary before removing old shallow assumptions. Use a fake repository with no
`storage_dir` or `managed_certificate_dir` attributes to prove manager create/import/delete use only
the new verbs. Add production-adapter tests for payload-write failure, catalog-save failure, staged
unlink failure, rollback restoration, missing-file deletion, and path-traversal rejection through the
model filename invariant. Add secret failure tests proving a repository failure removes a newly saved
secret and a configuration catalog failure restores the prior secret. Add an import-isolation test
that imports the application manager in a subprocess and asserts no `foliaseal.infra.secret_storage`
module is loaded. Retain equivalent existing manager/Qt tests and update only assertions whose
observable error text or repository call shape necessarily changes.

Update `docs/ARCHITECTURE.md` to state that certificate policy remains in the application manager,
while file/catalog sequencing and recovery belong to the repository adapter; note the separate
material-path follow-up and unchanged phase3 contracts. Update this plan and the parent ledger with
the actual rollback evidence and measurements.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`.

1. Add the application secret protocol/error and repository commit result/verbs. Run focused contract
   tests to expose missing adapter methods before migrating the manager.
2. Implement filesystem and in-memory adapter transaction behavior, then run
   `.venv/bin/pytest -q tests/unit/test_certificate_catalog_repository.py tests/unit/test_certificate_storage.py`.
3. Migrate `CertificateManager`, add/import/delete rollback and import-firewall tests, and run
   `.venv/bin/pytest -q tests/unit/test_certificate_manager.py tests/unit/test_secret_storage.py tests/unit/test_qt_app_frame_certificate_management.py`.
4. Run `.venv/bin/pytest -q`, `.venv/bin/ruff check src tests`, `.venv/bin/python -m compileall -q src`,
   `.venv/bin/python -m foliaseal --help`, and `git diff --check`.
5. Run the unchanged offscreen evidence command and expect signed acceptance `10` scenarios with `7`
   successful signings, preview parity `18/18`, and fit rejection `3/3`. Remove its generated
   summary and any explicit temporary roots afterward.
6. Verify `git diff -- docs/SPEC.md` is empty; audit product processes with
   `ps -eo pid=,comm= | awk '$2 ~ /^(python|python3|FoliaSeal|foliaseal|PySide|Qt)/ {print}'`;
   expect no product process. Have explorer-light reviewers check SPEC/ARCHITECTURE and the
   application import firewall, then have a worker-light agent use `$write-git-commit` for the
   intentional files.
7. Repeat the baseline measurements, record Actual Improvement and regression gates, confirm a clean
   worktree, and run three fresh explorer-light scans for the next candidate.

## Validation and Acceptance

Acceptance requires all existing certificate manager, storage, secret, Qt-dialog, and full-suite
tests to pass without weakening assertions. New boundary tests must prove that application manager
code never accesses repository path properties or imports infra secret modules, and that the
production adapter restores both catalog and managed bytes when any file/catalog/finalization step
fails. The UI must still create/import/export/delete certificates, preserve saved-password behavior,
and report the same operation results. Offscreen evidence must remain signed acceptance `10/7`,
preview parity `18/18`, and fit rejection `3/3`, with no crypto, annotation, or mismatch failures.

The SPEC must be byte-for-byte unchanged. No phase3 path/symbol/CLI/JSON/fixture/artifact may change.
No critical/major review finding may remain; Actual Improvement must be at least `.15`; no component
may regress below `-.10`; and the final worktree must be clean with no product processes or generated
evidence roots.

## Idempotence and Recovery

All repository operations must be safe to retry after a failed test: use explicit temporary/quarantine
names under the adapter's managed directory and clean them during rollback. Never use broad deletion
commands. If a rollback test fails, retain the failing test and inspect the adapter's pre-operation
catalog/file snapshot before changing manager policy. If a compatibility result path cannot be
preserved without leaking new internals, keep the existing result field and record the remaining
path-resolution migration rather than broadening this slice.

## Artifacts and Notes

Allowed changes are the application secret boundary, certificate repository protocol/adapters,
`certificate_manager.py`, focused certificate tests, architecture/docs, and the parent/child plans.
Generated evidence may use only explicit `/tmp/foliaseal-*` roots and must be removed before commit.
Do not edit `docs/SPEC.md`, rename phase3 artifacts, modify signing policy, or migrate the viewer
resolver in this slice.

## Interfaces and Dependencies

The application repository contract may use `Path` only for the existing transitional
`ManagedCertificateCommit.managed_file_path` result; it must not expose directory properties to the
manager's transaction methods. `CertificateCatalogStore` owns filesystem I/O and JSON codecs;
`InMemoryCertificateCatalogRepository` supplies a deterministic byte-level fake. The secret protocol
is application-owned, while `SecretToolCertificateSecretStore` is its infrastructure adapter.
Cryptography and PKCS#12 policy stay in `CertificateManager`. Existing Qt callers continue to use
the manager's explicit methods and typed results.

## Revision Note

Created 2026-08-06 after Scan Round 35 and Design Selection 36. This plan deliberately separates
certificate transaction ownership from the remaining material-path resolver seam and the atomic
phase3 nomenclature migration.
