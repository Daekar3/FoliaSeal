# Hide Managed-Certificate Material Resolution Behind One Application Port

This ExecPlan is a living document and must be maintained according to
`.agents/skills/write-execplan/PLANS.md`. It is the child plan selected by Scan Round 39 and
Design Selection 40 in `docs/ExecPlans/architecture_improvement_loop_parent_execplan.md`.

## Purpose / Big Picture

When a user selects a saved certificate in the signing workspace, the application should resolve
that selection without making the coordinator or Qt shell know where certificate files live. After
this slice, one application-owned port will turn a configuration id, optional password, and optional
alias into the existing `SigningMaterial` value. The port's repository-backed adapter will own
catalog lookup, managed-filename/path policy, file-existence checks, saved-password retrieval, and
user-facing resolution errors. The coordinator and workspace composition will make one intent-level
call and will no longer dereference `managed_certificate_dir` or thread a concrete certificate store
through a path-resolution helper. Existing signing behavior, password semantics, aliases, error text,
catalog JSON, and phase3 contracts remain unchanged.

The result is observable through the existing signing workspace: selecting a certificate still
applies the same `SigningMaterial`, missing files still produce the same actionable message, and
saved passwords still work. It is also observable through boundary tests that construct the
coordinator with a fake one-method material port and a repository fake with no directory attributes.

## Child ExecPlan Dependencies

- [x] The frozen product contract in `docs/SPEC.md` is unchanged and available for verification.
- [x] `docs/ARCHITECTURE.md` documents the accepted certificate transaction boundary and identifies
  the material-path resolver as the next follow-up.
- [x] `docs/ExecPlans/managed_certificate_transaction_boundary_execplan.md` is accepted at
  commits `081b4087a`, `28e87b791`, and `33e95421e`.
- [x] Scan Round 39 has three independent evidence records and a convergent candidate score above
  the fixed continuation threshold.
- [x] Three designs and two independent reviews are recorded in the parent plan; common-caller
  Shape C is selected without a hybrid.

## Progress

- [x] (2026-08-06) Reconfirmed clean baseline commit `33e95421e`, the frozen specification, active
  architecture ledger, current resolver callers, and the existing resolver/coordinator tests.
- [x] (2026-08-06) Recorded Scan Round 39 candidate scores: medians
  `(NF 4.5, CA 4.0, SR 4.0, TG 4.0, IC 3.5, CC 4.0, MR 2.5, BU 2.0)`, confidence `.948`, and
  Candidate Priority approximately `65.6`.
- [x] (2026-08-06) Compared minimal, flexible, and common-caller designs; selected the standalone
  common-caller port at approximately `92` after two independent reviews. No hybrid qualified.
- [x] (2026-08-06) Captured baseline proxies: three non-infrastructure source modules reference
  `managed_certificate_dir`; the resolver/coordinator/application composition path has 16 direct
  material/path references; resolver/coordinator tests contain 27 path/resolver assertions.
- [x] (2026-08-06) Added application `ManagedCertificateMaterial` and repository `material_for`;
  production and in-memory adapters now own managed-file location/existence policy.
- [x] (2026-08-06) Replaced the path-taking resolver with
  `CertificateSigningMaterialPort` and `RepositoryBackedCertificateSigningMaterialPort`, preserving
  saved-secret, alias, missing-file, and exact error behavior.
- [x] (2026-08-06) Migrated the coordinator and Qt workspace bootstrap graph to one material port;
  resolution-only path and secret-provider plumbing and concrete-store annotations were removed.
- [x] (2026-08-06) Replaced path-coupled resolver tests with adapter/port tests, including no-path
  fakes, unknown/dangling configurations, missing/blank secrets, blank explicit passwords, aliases,
  and exact provider-failure text.
- [x] (2026-08-06) Focused validation passes (`218` tests after the final boundary additions); the
  full suite passes (`1136` tests, one pre-existing Pillow warning). Ruff, compileall, CLI help,
  import isolation, and diff checks pass.
- [x] (2026-08-06) Offscreen evidence passes signed acceptance `10/7`, preview parity `18/18`, and
  fit rejection `3/3`; the generated summary was removed and the process audit is clean.
- [x] (2026-08-06) Reconciled architecture/parent/child ownership text and recorded the compliance
  correction restoring the exact saved-password provider error message.
- [ ] Commit implementation and ledger intentionally, then run the fresh three-explorer post-commit
  rescan.

## Surprises & Discoveries

- Observation: `DefaultSignaturePropertiesCoordinator` annotates its dependency with
  `CertificateCatalogRepository` but reads `.managed_certificate_dir`, which is not part of that
  protocol.
  Evidence: `src/foliaseal/application/signature_properties_coordinator.py:252-279` and
  `src/foliaseal/application/certificate_catalog_repository.py:42-77`.
  Consequence: a valid repository fake without path attributes fails during coordinator setup before
  any signing action is attempted.
- Observation: the current resolver combines configuration lookup, managed-file path joining,
  filesystem existence, secret-provider access, password validation, and error translation.
  Evidence: `src/foliaseal/application/signing_material_resolver.py:39-146`.
  Consequence: the selected port must hide all of these decisions while preserving the existing
  `SigningMaterial` and `SigningMaterialResolutionError` contracts.
- Observation: the concrete certificate store property is widely used by storage and certificate
  management tests, but only three application/Qt production modules use it for material resolution.
  Consequence: this slice retires the property from application-facing composition and the protocol,
  while retaining it inside the concrete adapter and storage-focused tests until a separate storage
  contract migration is justified.
- Observation: the coordinator still supplies a default managed root when it creates an in-memory
  repository for callers that provide neither a repository nor a material port.
  Evidence: `signature_properties_coordinator.py:263-270`.
  Consequence: this is test/default repository construction, not a material-resolution path join;
  production Qt composition supplies the repository-backed port. Removing that fallback would be a
  separate constructor-default migration and is not required to restore the selected boundary.

## Decision Log

- Decision: Select the common-caller optimized `CertificateSigningMaterialPort` rather than a
  flexible request repository or a minimal path-bearing source verb.
  Rationale: the dominant coordinator call becomes one stable intent-level operation; the flexible
  design adds a second request abstraction without a current caller need, and the minimal design
  leaks path/material details or leaves policy split across two modules. Review scores were
  approximately C `91.6-93`, B `87.8-91`, and A `47` when its path leak is penalized.
  Date/Author: 2026-08-06 / Codex and two independent design reviewers.
- Decision: Keep `SigningMaterial.certificate_path: str` as the existing signer-facing value, but
  never expose `Path`, managed directories, filenames, or secret providers through the new port.
  Rationale: changing the signer contract would broaden this slice; the repository adapter is the
  only place allowed to construct the backend path.
  Date/Author: 2026-08-06 / Codex and design reviewers.
- Decision: Add `material_for(managed_certificate)` to the application repository protocol and
  return an application-owned `ManagedCertificateMaterial` value. The repository adapter owns path
  construction and existence checks; the material port owns catalog/configuration/secret policy.
  Rationale: the common-caller port needs a repository capability without reintroducing a directory
  property or a generic transaction/locator registry.
  Date/Author: 2026-08-06 / Codex.
- Decision: Remove the old path-taking `CertificateSigningMaterialResolver` implementation after
  first-party callers and tests migrate; do not leave a compatibility alias.
  Rationale: the old constructor is the concrete path leak this slice is intended to retire, and
  repository search shows no external package in this checkout requiring it.
  Date/Author: 2026-08-06 / Codex.
- Decision: Do not rename phase3 modules, commands, DTOs, JSON keys, fixtures, or artifacts here.
  Rationale: `phase3_nomenclature_retirement_execplan.md` requires one separate atomic migration
  with versioned external-contract decisions.
  Date/Author: 2026-08-06 / Codex.
- Decision: Retain the coordinator's default in-memory repository root as a compatibility-safe test
  default, but forbid it from being used for material resolution in production composition.
  Rationale: all production material resolution now enters through the app-frame-composed port;
  deleting the default would broaden this slice into a constructor/API migration with no user-visible
  gain.
  Date/Author: 2026-08-06 / Codex.

## Outcomes & Retrospective

The implementation is complete and behaviorally validated. `CertificateSigningMaterialPort` now
reduces coordinator/Qt resolution to one intent-level call; repository adapters own managed-file
location/existence; the old path-taking resolver is gone; and the graph no longer exposes concrete
store or secret-provider resolution plumbing. Boundary tests cover both adapters, exact error
messages, saved/manual/blank/missing secret paths, aliases, dangling/unknown records, and no-path
fakes. Focused validation is `218` tests and the full suite is `1136` tests with one pre-existing
Pillow warning. Offscreen evidence is `10/7`, `18/18`, and `3/3`; SPEC is unchanged and cleanup is
clean. Architecture and parent/child plan reconciliation is complete; intentional commit and
post-commit rescan remain pending. Repeated proxies moved from three non-infrastructure path-ref
modules and 16 resolver/path references to zero path-resolution references in the coordinator/Qt
graph, while boundary-test coverage grew from 27 path/resolver assertions to 30 material-boundary
assertion sites. Conservative component measurements are navigation `.45`, change amplification
`.45`, seam reduction `.50`, boundary-test improvement `.60`, interface compression `.50`, cohesion
`.45`, and isolation `.65`, for weighted Actual Improvement approximately `.53` versus predicted
`.48`; no component regressed beyond `-.10`.

## Context and Orientation

`src/foliaseal/application/signing_material_resolver.py` defines `SigningMaterial`,
`SigningMaterialResolutionError`, a `CertificateSecretProvider` protocol, the
`CertificateSigningMaterialPort`, and its repository-backed implementation. The implementation
loads a catalog snapshot, resolves the selected configuration and managed record through the
repository, reads a saved password when needed, and returns backend-ready material without owning a
directory or joining a storage path.

`src/foliaseal/application/signature_properties_coordinator.py` owns selection state and mutable
signing-draft workflow updates. In `__post_init__` it creates an in-memory repository when no store
is supplied, then composes the repository-backed material port when a caller has not injected one.
Its apply-certificate and apply-preset paths call that port and wrap resolution failures in
`SignaturePropertiesCoordinatorError`.

`src/foliaseal/application/certificate_catalog_repository.py` is the application persistence port;
`InMemoryCertificateCatalogRepository` is its test adapter. The production implementation is
`src/foliaseal/infra/config/certificate_storage.py`, which owns the managed directory and catalog
files. Both adapters now implement the deterministic `material_for` operation.

The Qt composition graph begins in `app_frame_workspace_open.py`, carries the application port
through `signing_workspace_host.py` and `signing_shell_port.py`, and constructs the properties panel
through `signing_workspace_composition.py`. The app frame composes the port from the concrete store
and secret service; downstream Qt modules carry only the repository protocol and port. Other
certificate management operations remain unchanged.

## Plan of Work

First add an application-owned `ManagedCertificateMaterial` frozen value with a backend-ready
`certificate_path: str` field and a `material_for(managed_certificate: ManagedCertificate)` method
to `CertificateCatalogRepository`. The value is opaque to callers: only repository adapters may
construct or inspect the storage path. `CertificateCatalogStore.material_for` must validate the
managed record's filename through the existing model invariant, join it under the managed directory,
and raise `FileNotFoundError` when the file is absent. `InMemoryCertificateCatalogRepository` must
return a deterministic virtual path when its byte map contains the filename, preserve its existing
physical-file fallback for current tests, and raise the same missing-file error otherwise.

Next replace the path-based resolver implementation in
`application/signing_material_resolver.py` with an application-owned
`CertificateSigningMaterialPort` protocol and a
`RepositoryBackedCertificateSigningMaterialPort` implementation. Its sole public operation is:

    def resolve(
        self,
        *,
        certificate_configuration_id: str,
        passphrase: str | None = None,
        certificate_alias: str | None = None,
    ) -> SigningMaterial: ...

The adapter loads one catalog snapshot through the repository, finds the configuration and managed
record, calls `material_for`, resolves a saved password through the injected
`CertificateSecretProvider`, validates explicit/loaded passwords, preserves aliases, and maps
missing records/files, unavailable secret storage, provider failures, missing secrets, and blank
passwords to the current `SigningMaterialResolutionError` messages. It must not import Qt, concrete
certificate storage, `Path` in its public interface, or `SecretStorageError`.

Then migrate `DefaultSignaturePropertiesCoordinator` to accept a
`certificate_material_port: CertificateSigningMaterialPort`, compose the repository-backed adapter
at its default construction point, and make `_resolve_signing_material` call only the port with the
configuration id and typed passphrase. Remove its `.managed_certificate_dir` dereference and the
old resolver construction. Preserve the coordinator's catalog selection state, workflow mutation,
error wrapping, alias behavior, and refresh behavior.

Migrate the Qt graph (`app_frame_workspace_open.py`, `signing_workspace_host.py`,
`signing_shell_port.py`, `signing_shell.py`, `signing_workspace_composition.py`, and
`signing_workspace_properties_panel.py`) to carry the application port instead of a concrete store
and secret provider for resolution. Compose the repository-backed adapter at the app-frame or
workspace-open root where the concrete store and secret service are already available. Remove the
now-unused provider/path fields and imports from these resolution-only DTOs and constructors;
certificate-management code may continue to use the concrete store at its existing infrastructure
edge. Do not alter unrelated signing-shell compatibility or phase3 harness contracts.

Before removing the old path resolver tests, add contract tests for both repository adapters and the
new port. Cover explicit passwords, saved passwords, unavailable/missing/failing secret providers,
blank passwords, aliases, unknown configurations, dangling managed records, missing files, and a
broken repository fake with no path attributes. Add coordinator tests proving one port call and
unchanged error/selection/workflow behavior. Update Qt construction tests to pass a fake material
port and assert no application/Qt resolution module accesses `managed_certificate_dir`. Only after
these boundary tests pass should the old path-taking resolver class and its path-coupled tests be
deleted; record the old-test-to-boundary-test mapping in this plan.

Reconcile `docs/ARCHITECTURE.md` so ownership says: repository adapters own managed-file location
and existence; the material port owns configuration-to-signing-material and secret/error policy; the
coordinator owns selection and workflow mutation; Qt composes the port but never joins paths. Update
this child and the parent ledger with the exact tests, scans, measurements, and any surprises.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`.

1. Add `ManagedCertificateMaterial`, the repository `material_for` verb, and adapter implementations.
   Run the repository and storage tests plus a new material contract test. Expected result: existing
   certificate storage behavior remains green and missing material is reported deterministically.
2. Replace the path-based resolver with the port/adapter and add its boundary tests. Run
   `.venv/bin/pytest -q tests/unit/test_signing_material_resolver.py tests/unit/test_certificate_catalog_repository.py tests/unit/test_certificate_storage.py`.
3. Migrate the coordinator and Qt composition graph, then run the focused coordinator, signing-shell,
   app-frame workspace-open, certificate-management, and setup-session tests. The new fake-port test
   must construct the coordinator without any `managed_certificate_dir` attribute.
4. Run `.venv/bin/pytest -q`, `.venv/bin/ruff check src tests`, `.venv/bin/python -m compileall -q src`,
   `.venv/bin/python -m foliaseal --help`, and `git diff --check`.
5. Run the unchanged offscreen evidence command:

    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-acceptance-evidence

   Expect signed acceptance `10` scenarios with `7` successful signings, preview parity `18/18`,
   and fit rejection `3/3`. Remove only its generated summary and any explicit temporary roots.
6. Verify `docs/SPEC.md` has no diff; run the import firewall and the product-process audit:

    ps -eo pid=,comm= | awk '$2 ~ /^(python|python3|FoliaSeal|foliaseal|PySide|Qt)$/ {print}'

   Expect no product process. Run a final compliance review, update measurements, and use an
   intentional commit for source/tests/docs followed by a clean ledger closure if needed.
7. Spawn three fresh explorer-light scans against the clean commit. Record the next candidate or
   below-threshold confirmation in the parent before closing this plan.

## Validation and Acceptance

Acceptance requires the full existing suite and the new boundary tests to pass without weakening
behavioral assertions. The coordinator must accept a fake port with no filesystem/path attributes;
the repository adapters must agree on managed-record validation, missing-file behavior, and filename
confinement; and no application or Qt resolution module may import the concrete certificate store or
read `managed_certificate_dir`. The existing `SigningMaterial` path string remains unchanged only
at the adapter-to-signer edge.

The signing workspace must still apply a selected certificate, preserve manual and saved-password
flows, preserve aliases, and report the existing actionable resolution messages. Offscreen evidence
must remain signed acceptance `10/7`, preview parity `18/18`, and fit rejection `3/3`. `docs/SPEC.md`
must be byte-for-byte unchanged. No phase3 path/symbol/CLI/JSON/fixture/artifact may change. No
critical or major review finding may remain; Actual Improvement must be at least `.15`, no component
may regress below `-.10`, generated evidence must be removed, no product process may remain, and the
final worktree must be clean.

Baseline proxies to repeat after implementation are: three non-infrastructure source modules with
`managed_certificate_dir` references; 16 resolver/path references across application/Qt production
composition; 27 path/resolver assertions in resolver/coordinator tests; and a coordinator construction
path that crosses the concrete store, resolver, secret provider, and catalog workflow. Predicted
component improvements are navigation `.45`, change amplification `.45`, seam reduction `.50`,
boundary-test improvement `.55`, interface compression `.45`, cohesion `.45`, and isolation `.55`,
for predicted weighted Actual Improvement approximately `.48` with no expected regression.

## Idempotence and Recovery

Repository material resolution is read-only. Re-running tests or composition construction must not
write catalogs, mutate secret storage, or create unmanaged directories. If a test or migration fails,
retain the failing boundary test, restore only the named source/doc files, and rerun the focused suite;
do not use broad deletion or reset commands. Generated offscreen summaries must be removed by exact
path. Keep the concrete storage property until all first-party material-resolution callers are gone,
then verify with a scoped `rg` before deleting it from the application protocol or in-memory adapter.

## Artifacts and Notes

Allowed changes are `certificate_catalog_repository.py`, `certificate_storage.py`,
`signing_material_resolver.py`, `signature_properties_coordinator.py`, the named Qt composition
modules, their focused tests, `docs/ARCHITECTURE.md`, this child plan, and the parent ledger. The
offscreen evidence summary may be generated transiently and must be removed before commit. Do not
edit `docs/SPEC.md`, rename phase3 files, change signing policy, or mix in broad shell compatibility
retirement, GUI redesign, or CLI additions.

## Interfaces and Dependencies

The application-facing interfaces at completion are:

    @dataclass(frozen=True)
    class ManagedCertificateMaterial:
        certificate_path: str

    class CertificateCatalogRepository(Protocol):
        def material_for(
            self,
            managed_certificate: ManagedCertificate,
        ) -> ManagedCertificateMaterial: ...

    class CertificateSigningMaterialPort(Protocol):
        def resolve(
            self,
            *,
            certificate_configuration_id: str,
            passphrase: str | None = None,
            certificate_alias: str | None = None,
        ) -> SigningMaterial: ...

`RepositoryBackedCertificateSigningMaterialPort` is the production composition adapter. Its
constructor receives only `CertificateCatalogRepository` and the application secret-provider
protocol. Its public port exposes no `Path`, `CertificateCatalogStore`, `SecretStorageError`,
managed directory, storage filename, or Qt type. `CertificateManager` remains responsible for
certificate creation/import/deletion policy; the repository remains responsible for persistence and
managed-file location; the material port resolves runtime inputs; the coordinator owns selection and
workflow mutation; Qt owns widget presentation and composition only.

## Revision Note

Created 2026-08-06 after Scan Round 39 and Design Selection 40. This plan deliberately completes the
certificate transaction boundary's deferred material-resolution seam in one implementation slice,
while leaving the separately governed phase3 nomenclature migration untouched.
