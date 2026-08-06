# Remove Concrete Certificate Storage from Application Services

This living ExecPlan follows `.agents/skills/write-execplan/PLANS.md` and is governed by
`docs/ExecPlans/architecture_improvement_loop_parent_execplan.md`. It is one complete DevLoop slice:
protocol ownership, application migration, boundary fakes/tests, documentation, evidence, cleanup,
and commit closure all belong here.

## Purpose / Big Picture

FoliaSeal's certificate application services still know the concrete filesystem store. That makes
application behavior harder to test without JSON/filesystem setup and forces a catalog model boundary
that was already moved into `application/certificate_models.py` to retain an infra import. After this
slice, `CertificateManager` and `DefaultSignaturePropertiesCoordinator` depend on an
application-owned `CertificateCatalogRepository` protocol. The existing
`CertificateCatalogStore` remains the production adapter constructed by the Qt/app-frame composition
root; its JSON codecs, atomic writes, managed-file paths, deletion guards, export safety, and error
messages remain unchanged.

The user-visible workflow is unchanged: certificate creation/import, saved-password handling,
configuration rename/delete, managed-certificate deletion/export, signing setup refresh, and the
preview/sign flow behave exactly as before. The improvement is observable through application tests
using an in-memory repository, an import-isolation check proving application services do not load the
infra store, the existing storage characterization suite, and the unchanged offscreen acceptance
matrices.

## Child ExecPlan Dependencies

- [x] Parent scan round 18 found `certificate_catalog_repository_boundary` at Priority `65–68`
  with confidence about `0.91` and independent explorer plus orchestrator evidence.
- [x] Parent design selection 18 compared minimal, flexible, and common-caller designs with two
  independent reviews and selected the bounded current-verb repository protocol.
- [x] The current clean baseline is `68ac11807`; `docs/SPEC.md` hash is
  `d929e189269f0f057c6a72b43fd2d430965a975be720b55139fdb1d92afe282b`.
- [x] Qt composition roots already construct `CertificateCatalogStore`; this plan must preserve that
  production wiring while removing only application-layer concrete imports.

## Progress

- [x] (2026-08-06) Created this self-contained plan after scan/design review.
- [x] (2026-08-06) Pre-implementation review confirmed manager creation and rollback use both
  `storage_dir` and `managed_certificate_dir`; the protocol therefore exposes both read-only paths.
- [x] Add the application protocol and in-memory test repository without importing infra modules.
- [x] Migrate `CertificateManager` and `DefaultSignaturePropertiesCoordinator` to the protocol and
  remove their concrete-store imports while preserving defaults and refresh behavior.
- [x] Migrate or strengthen manager/coordinator boundary tests and add protocol import-isolation and
  structural-store conformance checks.
- [x] Reconcile architecture/active plans, run full validation and offscreen evidence, clean all
  temporary roots/processes/dialogs, measure improvement, commit, rescan, and close the plan.

## Architecture Selection Record

The selected design is the flexible-but-bounded current-verb repository protocol. Its approved
interface is deliberately smaller than a generic CRUD service and does not expose JSON payloads,
schema codecs, transaction objects, secret storage, or a filesystem abstraction. It hides the
concrete store type from application callers while keeping application operation sequencing visible
and behavior-bearing.

The production dependency is structural: `CertificateCatalogStore` already implements the protocol
and remains constructed by `app_frame.py`, `app_frame_workspace_open.py`, and signing-shell
composition. Tests use an in-memory repository that stores an application `CertificateCatalog` and a
temporary managed-file directory. The protocol is local-substitutable, not remote or third-party.

The implementation may not silently move manager rollback, secret cleanup, catalog codecs, export
path checks, or managed-file deletion policy into a new generic service. It may not add compatibility
aliases, change the store's public methods, rename phase3 contracts, or edit `docs/SPEC.md`.

## Behavior Preservation Map

`CERT-REPO-1` covers empty/missing catalog load and catalog refresh. The current paths are
`CertificateCatalogStore.load_catalog()` and `DefaultSignaturePropertiesCoordinator._refresh_catalogs()`;
existing storage/coordinator tests must remain green, and the replacement boundary test uses the fake
repository's catalog identity and reload behavior.

`CERT-REPO-2` covers create/import persistence. `CertificateManager._commit_new_certificate()` must
retain managed PKCS#12 write ordering, catalog upsert ordering, saved-password secret creation, and
cleanup on failure. Existing manager tests plus new fake-repository tests must prove the same returned
operation result and file/secret state.

`CERT-REPO-3` covers configuration save/delete and reference guards. The application manager keeps
the same duplicate-name and secret-rollback behavior; the real storage suite continues to prove
catalog JSON and referenced-managed-certificate deletion errors.

`CERT-REPO-4` covers managed certificate deletion rollback. The manager retains staged-file rename,
catalog save, staged unlink, and restore-on-failure choreography. A fake repository plus temporary
managed directory must prove file restoration and catalog restoration when persistence fails.

`CERT-REPO-5` covers export safety. `CertificateCatalogStore.export_managed_certificate_by_id()`
continues to own missing-source, self-destination, symlink, and managed-directory rejection. Manager
tests continue to observe the same returned path and errors through the protocol.

`CERT-REPO-6` covers signing-properties refresh and resolver setup. The coordinator continues to
load the repository catalog, pass only `managed_certificate_dir` to
`CertificateSigningMaterialResolver`, and preserve Qt state/validation text. Coordinator, setup
session, shell, and offscreen acceptance tests are the evidence.

## Baseline Measurements and Predicted Improvement

Before implementation, the concrete-store import inventory is:

    application/certificate_manager.py: imports CertificateCatalogStore and annotates store
    application/signature_properties_coordinator.py: imports/types/defaults CertificateCatalogStore
    application modules tested with concrete storage: certificate manager and coordinator suites
    production composition: app_frame.py and signing workspace composition construct the concrete store

The baseline proxy values for this slice are navigation `0.30`, change amplification `0.60`, seam-risk
reduction `0.60`, boundary-test improvement `0.55`, interface compression `0.35`, and boundary
isolation `0.55`. Predicted weighted Actual Improvement is `0.38`; no component may regress below
`-0.10`. Repeat the same proxy definitions after migration by counting application-to-infra imports,
concrete type annotations, fakeable operation paths, and unchanged caller contract surfaces.

## Decision Log

- Decision: define one `CertificateCatalogRepository` protocol with only current catalog/store verbs
  plus read-only `storage_dir` and `managed_certificate_dir`. Rationale: it removes the concrete import while preserving manager
  rollback ordering and avoids a speculative filesystem/transaction framework. Date/Author:
  2026-08-06, Codex.
- Decision: retain the field/parameter spelling `store`/`certificate_catalog_store` during this
  migration where Qt callers already use it, but type it against the application protocol. Rationale:
  the architectural boundary is the dependency identity and import direction; a broad naming rewrite
  would add churn without improving ownership in this slice. Date/Author: 2026-08-06, Codex.
- Decision: provide an application-owned in-memory repository for tests and for coordinator instances
  that have an explicitly supplied catalog but no production repository. Rationale: application tests
  must not instantiate an infra adapter merely to render state, while production composition continues
  to inject the real store. Date/Author: 2026-08-06, Codex.
- Decision: do not add `write_managed_certificate()` or move staged file/secret rollback behind the
  protocol. Rationale: current manager sequencing is behavior-bearing and moving it would make this
  one slice larger and less safe; the protocol only abstracts existing store calls and the managed
  directory capability. Date/Author: 2026-08-06, Codex.

## Surprises & Discoveries

Record every hidden caller, default-construction path, protocol mismatch, rollback difference, or
import-cycle here with command/test evidence. If a first-party caller appears, migrate it or document
why it remains a composition edge; do not restore a concrete application import as a shortcut.

Initial discovery: coordinator tests frequently provide an application catalog without a storage
store, while production Qt composition always has a concrete store. The application-owned in-memory
repository supports catalog-only coordinator construction while preserving the existing XDG default
managed-certificate directory for resolver fallback; real signing-shell composition remains
responsible for injecting the production store and managed directory.

Pre-implementation discovery: `CertificateManager._commit_new_certificate()` creates both the store
root and its managed-file directory before writing the PKCS#12 payload, and managed deletion stages
files under the managed directory before catalog persistence. The application port keeps both paths
as read-only capabilities; it does not move filesystem transaction policy or secret rollback into the
repository.

## Plan of Work

Create `src/foliaseal/application/certificate_catalog_repository.py`. Define
`CertificateCatalogRepository(Protocol)` with read-only `storage_dir: Path`,
`managed_certificate_dir: Path`,
`load_catalog() -> CertificateCatalog`, `save_catalog(catalog) -> None`,
`save_configuration(configuration) -> CertificateCatalog`,
`delete_configuration_by_id(configuration_id) -> CertificateCatalog`, and
`export_managed_certificate_by_id(certificate_id, destination_path) -> Path`. Add
`InMemoryCertificateCatalogRepository` with the same behavior for catalog state and temporary
managed files; it must import only standard-library modules, application certificate models, and
domain validation errors. Its export method is a test-only copy seam; export path/symlink/managed-
directory safety remains exclusively characterized by the real infra adapter rather than duplicated
in the fake. Provide the existing XDG default managed-directory calculation in this application-owned
composition fallback so no-store coordinator callers retain prior resolver behavior.

Change `src/foliaseal/application/certificate_manager.py` to import the protocol rather than
`infra.config.certificate_storage.CertificateCatalogStore` and annotate `store` with the protocol.
Retain both directory-creation calls because the manager writes the managed payload before the
catalog adapter persists anything. Retain all staged-file, catalog-save, secret-rollback, and export
calls exactly.

Change `src/foliaseal/application/signature_properties_coordinator.py` to use the protocol. When a
repository is supplied, load and refresh through it exactly as today. When a caller supplies an
application catalog but no repository, create an in-memory repository using the existing XDG default
managed directory so state-only coordinator tests remain application-isolated without changing
resolver fallback behavior; production composition must continue passing the real store. Use the
protocol's `managed_certificate_dir` when constructing the resolver. Remove the
`CertificateCatalogStore.default()` fallback from this application module.

Add or migrate tests in `tests/unit/test_certificate_catalog_repository.py`,
`tests/unit/test_certificate_manager.py`, and `tests/unit/test_signature_properties_coordinator.py`.
The new boundary tests must use fake/in-memory repositories for create/import/delete/refresh and
assert exact catalog/file/secret outcomes. Keep all existing `tests/unit/test_certificate_storage.py`
tests as real-store characterization and conformance coverage. Add a subprocess assertion that
importing the application repository, manager, and coordinator does not load
`foliaseal.infra.config.certificate_storage`.

Update `docs/ARCHITECTURE.md` to list the protocol and fake, revise application/store ownership and
dependency rules, and add a dated changelog entry. Update this child and the parent cycle ledger with
measurements, evidence, discoveries, commit, and the next fresh scan. Do not edit `docs/SPEC.md` or
rename any phase3 contract.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    rg -n "CertificateCatalogStore|certificate_catalog_store|managed_certificate_dir" src/foliaseal/application tests/unit/test_certificate_manager.py tests/unit/test_signature_properties_coordinator.py
    .venv/bin/pytest -q tests/unit/test_certificate_catalog_repository.py tests/unit/test_certificate_manager.py tests/unit/test_certificate_storage.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py
    .venv/bin/ruff check src tests scripts
    .venv/bin/pytest -q
    .venv/bin/python -m foliaseal --help
    git diff --check

Run the existing offscreen preview-parity, signed-acceptance, and fit-rejection matrix commands under
an explicit `/tmp/foliaseal-certificate-repository-evidence` root using generated local acceptance
assets if the ignored assets are absent. Record scenario counts and summary paths, then remove that
exact root and audit for FoliaSeal/Python/Qt processes and dialogs. Never leave generated repository
acceptance assets or temporary files behind.

## Validation and Acceptance

Acceptance requires all of the following: application modules import no concrete certificate storage;
the protocol module imports no infra/Qt/Pillow/pyHanko; `CertificateCatalogStore` remains structurally
compatible and its storage tests pass; manager create/import/delete/export and secret rollback retain
exact behavior; coordinator refresh/state/resolver behavior and Qt setup remain unchanged; full pytest,
Ruff, CLI help, diff checks, and subprocess import isolation pass; preview/signed/fit matrices match
their baseline scenario counts and expected outcomes; `docs/SPEC.md` hash is unchanged; no phase3
CLI/DTO/JSON/artifact name changes occur; temporary roots/processes/dialogs are cleaned; and `main`
is clean after intentional commits.

The cycle is accepted only if measured weighted Actual Improvement is at least `0.15` and no proxy
component regresses below `-0.10`. Record the exact post-migration proxies and calculation in this
section and the parent. If a hard gate fails, continue this plan or use the one allowed redesign;
do not accept a partial protocol that leaves application concrete imports.

## Idempotence and Recovery

The migration is additive until protocol/fake tests pass. If a real store method signature differs,
adapt the protocol to the existing method rather than wrapping behavior. If coordinator construction
without a store breaks a test, use the in-memory repository only for catalog-only state; never restore
an infra default import. If rollback or export evidence differs, preserve the failure and repair the
protocol migration without changing error ordering or file safety. Generated evidence is always under
the exact named temporary root and is removed after validation.

## Artifacts and Notes

Durable artifacts are the protocol module, application migrations, boundary tests, architecture docs,
this child plan, and parent ledger updates. The only generated artifacts permitted are files under the
explicit temporary evidence root; remove them before commit. No SPEC edit, phase3 rename, compatibility
alias, broad filesystem abstraction, or unrelated GUI redesign belongs in this slice.

## Outcomes & Retrospective

At completion, record focused/full test counts, Ruff/import/CLI results, offscreen matrix counts,
cleanup audit, commit hashes, measured improvement, and any residual concrete store references (which
should be composition-root-only). Explain whether the protocol stayed cohesive and identify the next
fresh-scan candidate.

### Outcomes & Retrospective — completed 2026-08-06

Implementation is complete. `CertificateCatalogRepository` now owns the application protocol and
`InMemoryCertificateCatalogRepository` supplies an application-only catalog/file seam. The manager
and signature-properties coordinator no longer import or type the concrete infra store; Qt/app-frame
composition continues to inject `CertificateCatalogStore` at the edge. The coordinator's no-store
fallback preserves the existing XDG managed-directory resolver path, and the fake intentionally does
not duplicate infra export path-safety policy. The dedicated boundary suite covers in-memory
catalog/config/export behavior, real-store structural conformance, and subprocess import isolation.

Validation evidence: focused certificate/storage/coordinator tests `56 passed`; full suite `1,088
passed, 1 warning`; Ruff, CLI help, and `git diff --check` passed; application import isolation
passed; `docs/SPEC.md` hash remained
`d929e189269f0f057c6a72b43fd2d430965a975be720b55139fdb1d92afe282b`. Offscreen evidence under the
explicit temporary root passed preview parity `18/18` with zero errors, signed acceptance `10`
scenarios with `7` successful signings, zero errors/mismatches/cryptographic failures, and fit
rejection `3/3` matched intentional rejections. Expected self-signed TSA diagnostics were emitted
but the signed matrix exited successfully. The temporary root was removed and the process audit found
no FoliaSeal/Python/Qt harness processes.

Post-migration proxies are navigation `0.30`, change amplification `0.70`, seam-risk reduction
`0.75`, boundary-test improvement `0.80`, interface compression `0.75`, and boundary isolation
`0.85`; weighted Actual Improvement is `0.52` against predicted `0.38`, with no component regression
below `-0.10`. The application boundary remains cohesive because it abstracts existing catalog verbs
and read-only path capabilities without introducing a generic transaction/filesystem framework.

## Interfaces and Dependencies

The final application repository module must expose:

    class CertificateCatalogRepository(Protocol):
        @property
        def storage_dir(self) -> Path: ...

        @property
        def managed_certificate_dir(self) -> Path: ...
        def load_catalog(self) -> CertificateCatalog: ...
        def save_catalog(self, catalog: CertificateCatalog) -> None: ...
        def save_configuration(self, configuration: CertificateConfiguration) -> CertificateCatalog: ...
        def delete_configuration_by_id(self, configuration_id: str) -> CertificateCatalog: ...
        def export_managed_certificate_by_id(self, certificate_id: str, destination_path: str | Path) -> Path: ...

    class InMemoryCertificateCatalogRepository:
        catalog: CertificateCatalog
        managed_certificate_dir: Path

`CertificateManager.store` and `DefaultSignaturePropertiesCoordinator.certificate_catalog_store`
accept the protocol. `CertificateCatalogStore` remains the concrete infra implementation and keeps its
existing public methods and filesystem behavior. No application module may import
`foliaseal.infra.config.certificate_storage` after migration.

Revision note: created 2026-08-06 after resumed round-18 scan and design review; selected the bounded
current-verb protocol (Design B) over incomplete annotation-only and migration-heavy transaction shapes.
