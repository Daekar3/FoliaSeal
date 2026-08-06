# Move Certificate Models Behind the Application Boundary

This living ExecPlan follows `.agents/skills/write-execplan/PLANS.md` and is governed by
`docs/ExecPlans/architecture_improvement_loop_parent_execplan.md`.

## Purpose / Big Picture

The application currently imports certificate records and catalog policy from
`infra/config/schemas.py`. That module mixes immutable certificate objects, catalog lookup/upsert/
delete invariants, validation, and JSON persistence codecs. After this slice, the application owns
the certificate models and catalog policy; infra owns only persistence codecs and the filesystem
store. Application callers no longer import infra schema or certificate-storage modules. Persisted
catalog bytes, keys, schema versions, paths, store methods, validation messages, and Qt behavior remain
unchanged. This removes a real layer leak and avoids adding another compatibility port.

## Child ExecPlan Dependencies

- [x] Parent scan 14 found the same certificate DTO/model leakage in all three independent reports,
  with consensus Priority approximately `64–67` and confidence `0.90`.
- [x] Three designs and two independent scoring reviews are recorded in the parent; the canonical
  application-model/infra-codec design is selected.
- [x] Phase3 nomenclature remains a separate atomic contract migration and is not renamed here.

## Progress

- [x] (2026-08-06) Added this bounded child plan with explicit ownership and preservation gates.
- [x] (2026-08-06) Added application-owned certificate models/catalog policy and migrated validation
  tests; model serialization methods were removed from the application boundary.
- [x] (2026-08-06) Added infra-only JSON codecs and migrated `CertificateCatalogStore`.
- [x] (2026-08-06) Migrated application, Qt, support, and test imports; removed old infra certificate
  definitions and compatibility re-exports.
- [x] (2026-08-06) Focused/full tests, Ruff, import isolation, CLI help, offscreen evidence, docs
  reconciliation, exact-root cleanup, and process audit passed. Commit is pending final staging.

## Problem Space and Constraints

The representative workflow is Open workspace → choose certificate configuration → resolve managed
PKCS#12 material → preview/sign. `CertificateManager` creates/imports/deletes records; the coordinator
and draft workflow read/apply configurations; `CertificateSigningMaterialResolver` resolves stable IDs
to runtime paths/passwords; `CertificateCatalogStore` persists the catalog. Current callers know both
application policy and infra schema types. The new boundary must preserve stable IDs, tuple/catalog
invariants, password-secret coupling, filename safety, atomic store writes, and exact error text.

Illustrative target shape:

```python
# application/certificate_models.py
catalog = CertificateCatalog(schema_version=1).upsert_configuration(configuration)

# infra/config/certificate_codecs.py
payload = encode_certificate_catalog(catalog)
catalog = decode_certificate_catalog(payload)
```

The application model module may import only stdlib and `foliaseal.domain.errors`; it must not import
Qt, Pillow, pyHanko, infra schemas, stores, or secret storage. The codec and store may import the
application models and remain concrete infra adapters.

## Decision Log

- Decision: move `ManagedCertificateSubjectSummary`, `ManagedCertificate`,
  `CertificateConfiguration`, and `CertificateCatalog` plus catalog policy to
  `application/certificate_models.py`. Rationale: these are application concepts with behavior,
  not passive persistence records.
- Decision: move `from_dict`/`to_dict` behavior into
  `infra/config/certificate_codecs.py` as `decode_certificate_catalog()` and
  `encode_certificate_catalog()`. Rationale: persistence knowledge belongs below the application
  boundary and this removes the model/codec coupling rather than relocating it.
- Decision: do not retain infra re-export aliases after first-party imports and tests are migrated.
  Rationale: this is an internal module cleanup requested by the architecture objective; no SPEC,
  CLI, JSON, fixture, or artifact contract uses Python module paths.
- Decision: keep `ConfigValidationError` in `foliaseal.domain.errors` and import it directly from
  application models/codecs. Rationale: it is already a neutral shared error and avoids creating a
  second error identity.

## Surprises & Discoveries

Record any circular-import, hidden caller, codec parity, or exact-error regression here before
working around it. Do not restore compatibility aliases silently; if a first-party consumer is found,
migrate it and update the inventory.

Implementation discoveries: first-party certificate model imports existed in Qt shell/setup surfaces
and shared test builders, so the migration inventory had to include presentation type annotations and
fixture constructors, not only the four application modules. The existing schema tests mixed generic
settings/profile codecs with certificate model serialization; certificate cases were moved to the
codec boundary while unrelated schema tests stayed in place. No hidden first-party import required a
compatibility re-export, and persisted payloads/error strings remained unchanged.

## Outcomes & Retrospective

After implementation record focused model/codec/storage/manager/coordinator/resolver/workflow/Qt test
counts, full suite, Ruff, import isolation, CLI help, offscreen evidence, process/temp-root cleanup,
and the measured Actual Improvement. Acceptance requires Actual Improvement at least `0.15` and no
component regression below `-0.10`. Record the implementation commit and parent-cycle summary here.

Implementation evidence: focused certificate/model/storage/manager/coordinator/resolver/workflow/Qt
coverage passed `256` tests; full pytest passed `1,069` tests with `11` skipped and one pre-existing
Pillow warning; Ruff passed; CLI help and `git diff --check` passed. The subprocess import-isolation
check proved application certificate models load without infra config/storage, PySide6, Pillow, or
pyHanko. Offscreen evidence passed signed acceptance `10` scenarios (`7` successful), preview parity
`18/18`, and fit rejection `3/3`; `/tmp/foliaseal-certificate-model-evidence` was removed and no
FoliaSeal/Python application process remained.

Proxy measurement: navigation `0.35`, change amplification `0.65`, seam-risk reduction `0.75`,
boundary-test improvement `0.75`, interface compression `0.75`, and boundary isolation `0.85`;
weighted `Actual Improvement = 0.55` versus predicted `0.45`, with no component regression below
`-0.10`. The implementation is ready for the parent acceptance commit.

## Plan of Work

1. Copy the certificate model validation and catalog policy into the application module without
   changing constructor signatures, dataclass equality, lookup semantics, duplicate/reference guards,
   or error strings.
2. Implement codec functions that reproduce every existing nested key, `schema_version`, list/tuple
   conversion, malformed-payload error, and empty/missing catalog behavior. Keep `AppSettings`, trust,
   timestamp, profile, and unrelated schema classes in `schemas.py`.
3. Update `CertificateCatalogStore` to use the codec functions and canonical application models.
4. Migrate `SigningDraftWorkflow`, `SignaturePropertiesCoordinator`, `CertificateSigningMaterialResolver`,
   `CertificateManager`, Qt setup/shell surfaces, test builders, and unit tests to application imports.
5. Replace direct certificate model serialization tests with model-invariant and codec golden-payload
   tests. Remove old certificate classes and unused schema helper imports only after `rg` proves no
   first-party caller remains.
6. Reconcile architecture and active plans, run all gates, clean exact temporary roots/processes, and
   commit the complete slice.

## Interfaces and Dependencies

Application exports:

```python
@dataclass(frozen=True)
class ManagedCertificateSubjectSummary: ...
@dataclass(frozen=True)
class ManagedCertificate: ...
@dataclass(frozen=True)
class CertificateConfiguration: ...
@dataclass(frozen=True)
class CertificateCatalog:
    def configuration_named(self, name: str) -> CertificateConfiguration: ...
    def configuration_by_id(self, configuration_id: str) -> CertificateConfiguration: ...
    def managed_certificate_by_id(self, certificate_id: str) -> ManagedCertificate: ...
    def upsert_managed_certificate(self, certificate: ManagedCertificate) -> CertificateCatalog: ...
    def upsert_configuration(self, configuration: CertificateConfiguration) -> CertificateCatalog: ...
    def remove_managed_certificate_by_id(self, certificate_id: str) -> CertificateCatalog: ...
    def remove_configuration(self, name: str) -> CertificateCatalog: ...
    def remove_configuration_by_id(self, configuration_id: str) -> CertificateCatalog: ...
```

Infra exports only codec functions and the existing `CertificateCatalogStore` API:

```python
def decode_certificate_catalog(payload: Mapping[str, Any]) -> CertificateCatalog: ...
def encode_certificate_catalog(catalog: CertificateCatalog) -> dict[str, Any]: ...
```

No application module may import `foliaseal.infra.config.schemas`, `certificate_storage`, Qt, or
secret-storage modules for certificate model behavior after migration.

## Validation and Acceptance

- `docs/SPEC.md` hash is unchanged.
- Model tests cover every constructor invariant, lookup, upsert, deletion/reference guard, and exact
  error message previously protected by schema tests.
- Codec tests cover exact round-trip payloads, malformed fields, empty/missing catalogs, and schema
  version/key preservation.
- Certificate storage tests cover atomic writes, file deletion/export, and store API identity.
- Resolver, manager, coordinator, draft workflow, Qt shell/app-frame, and reusable-object suites pass.
- A subprocess import-isolation test proves importing `foliaseal.application.certificate_models` loads
  neither infra config/storage nor Qt/Pillow/pyHanko.
- `rg` proves no application or presentation certificate caller imports infra schema model classes;
  exactly one canonical definition exists.
- Ruff, full pytest, CLI help, offscreen signed acceptance/parity/fit matrices, process audit, and
  temporary-root cleanup pass.

## Concrete Steps

    rg -n "CertificateCatalog|CertificateConfiguration|ManagedCertificate" src tests
    .venv/bin/pytest -q tests/unit/test_config_schemas.py tests/unit/test_certificate_storage.py tests/unit/test_certificate_manager.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_material_resolver.py tests/unit/test_signing_draft_workflow.py
    .venv/bin/ruff check src tests scripts
    .venv/bin/pytest -q
    PYTHONPATH=src .venv/bin/python -c "import foliaseal.application.certificate_models"
    .venv/bin/python -m foliaseal --help
    git diff --check

Run the existing offscreen acceptance evidence command under an explicit
`/tmp/foliaseal-certificate-model-evidence` root, remove that exact root, and audit for leftover
FoliaSeal/Python processes or dialogs before committing.

## Idempotence and Recovery

Keep codec migration one-way: application models never import codecs or stores. If a hidden first-party
caller appears, migrate it instead of restoring a re-export. If JSON parity fails, compare the old
golden payload and exact error text before changing model validation. Do not alter persisted files,
CLI commands, phase3 DTOs, fixtures, or artifact paths. If a migration cannot satisfy all gates in
this slice, record the concrete failure and continue the same plan or use the one allowed redesign;
do not accept a partial port that leaves duplicate ownership.
