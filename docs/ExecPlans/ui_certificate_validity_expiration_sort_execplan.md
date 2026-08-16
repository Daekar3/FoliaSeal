# Persist certificate validity metadata and expose expiration sorting

This ExecPlan is a living document and must be maintained in accordance with
`.agents/skills/write-execplan/PLANS.md`. It is an AFK (agent can implement and
validate without a pending human product decision) child of
`docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md`.

## Purpose / Big Picture

After this slice, FoliaSeal retains the public validity facts it already reads
when importing or creating a certificate. In the Signature Library, a user can
choose “Expiration soonest” and see certificates with known expiration dates in
that order, while entries whose old record has no date remain safely at the end.
The user can also inspect the date in the row details. No private key or
password is persisted in the catalog.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md`, `docs/UI_SPEC.md`, and `docs/SCHEMAS.md` are the governing
  contracts.
- [x] `docs/ExecPlans/ui_catalog_search_sort_pinning_execplan.md` provides the
  Library session, configured-first/pinned-first projection, and preference
  bridge.
- [x] `docs/ExecPlans/ui_certificate_import_configuration_execplan.md` provides
  validated import and managed-file persistence.
- [x] `docs/ExecPlans/ui_certificate_create_export_password_execplan.md` provides
  validated self-signed creation and export/password lifecycle.

## Progress

- [x] (2026-08-10) Audited the governing schema and live source. `SCHEMAS.md`
  requires `issuer_summary`, `valid_from`, `valid_until`, and
  `fingerprint_sha256`; the manager already computes validity during inspection,
  but `ManagedCertificate`, its codec, and the Library projection discard it.
- [x] Added the public metadata to the application model and JSON codec, with
  safe read behavior for older local records that lack the optional fields.
- [x] (2026-08-10) Added secret-free subject DN, issuer, validity, and SHA-256
  fingerprint fields to the application model and codec. Missing fields in old
  local JSON decode as `None`; new manager records populate all fields.
- [x] (2026-08-10) Populated the metadata for both imported and newly created
  certificates from the actual `x509.Certificate`.
- [x] (2026-08-10) Implemented expiration-soonest ordering and the Qt sort option
  while keeping
  pinned and configured rows first.
- [x] (2026-08-10) Added red-to-green focused coverage, reconciled governing and
  architecture docs, ran focused/full validation, completed the bounded Qt
  lifecycle cleanup audit, and prepared the commit.

## Surprises & Discoveries

- Observation: `LibrarySort.EXPIRATION_SOONEST` and
  `LibrarySortOrder.EXPIRATION_SOONEST` already exist, so this is a missing
  projection rather than a new preference schema.
  Evidence: `src/foliaseal/application/signature_library_session.py` and
  `src/foliaseal/infra/config/app_settings_ui.py`.
- Observation: `CertificateImportInspection` already exposes all validity facts,
  but the create/import commit paths only save subject and creation time.
  Evidence: `src/foliaseal/application/certificate_manager.py`.
- Observation: old fixtures and local catalogs omit the four schema fields.
  Decision: decode missing fields as `None`, sort unknown dates last, and ensure
  every newly written manager record contains the canonical public facts. This
  avoids making an old local catalog unloadable while removing no product
  compatibility surface.
- Observation: the canonical schema also names `distinguished_name` inside the
  subject summary, which the earlier model omitted.
  Evidence: `docs/SCHEMAS.md:135-145`; the same metadata extraction now populates
  it for newly imported and created records.

## Decision Log

- Decision: store validity dates as canonical UTC ISO-8601 strings, matching the
  existing `created_at` representation and `SCHEMAS.md` examples.
  Rationale: strings remain JSON-safe and sort predictably after parsing, while
  the model stays independent of cryptography and Qt.
  Date/Author: 2026-08-10 / Codex
- Decision: use `None` only for legacy/unknown metadata; new import and create
  operations must populate all four fields.
  Rationale: expiration sorting must remain useful without pretending that an
  unreadable or old record has a date.
  Date/Author: 2026-08-10 / Codex
- Decision: apply expiration ordering before the existing configured-first and
  pinned-first stable partitions.
  Rationale: those are higher-priority identity affordances mandated by
  `UI_SPEC.md`; the chosen sort orders rows within each partition.
  Date/Author: 2026-08-10 / Codex

## Outcomes & Retrospective

The application now persists secret-free subject-DN, issuer, validity, and
SHA-256 fingerprint metadata for newly created/imported certificates. Old local
records remain readable with unknown expiration. The Library's existing
configured-first/pinned-first identity partitions now sort known certificates by
expiration and expose the third Qt choice through the existing preference key.
No new acceptance vocabulary, duplicate settings path, password, or private key was
introduced. The bounded GUI launch remains limited by the isolated single-instance
socket environment, while fake-binding Qt behavior and the full suite are green.

## Context and Orientation

`src/foliaseal/application/certificate_models.py` owns the dependency-free
`ManagedCertificate` value stored in the `CertificateCatalog`. JSON persistence
is in `src/foliaseal/infra/config/certificate_codecs.py`. The application
boundary in `src/foliaseal/application/certificate_manager.py` creates and
imports PKCS#12 files and already has a typed
`CertificateImportInspection` containing issuer, validity, and certificate
identity facts. `src/foliaseal/application/signature_library_session.py`
projects catalog rows and owns filtering/sorting; its `SignatureLibraryRow` is
display data, not persistence. The Qt controls in
`src/foliaseal/presentation/qt/app_frame_profile_library.py` expose the sort
combo and persist the selected value through the existing AppSettings bridge.

The certificate record must never contain a password, secret-store value, or
private key. “Known expiration” means a non-empty canonical date present in the
managed record; missing/invalid legacy values are displayed as unknown and sort
after known dates.

## Change Slice

This is one behavior-change slice plus the necessary governing-document/status
updates. Allowed files are the certificate model/codec/manager, Library session
and Qt dialog, their focused tests, this plan, the parent/catalog/architecture
records, and ignored temporary audit files. Do not mix signing execution,
placement, packaging, evidence rebaselines, or unrelated acceptance renames.

## Plan of Work

Add optional public metadata fields to `ManagedCertificate` with validation for
non-empty strings. Encode them in new catalog JSON and decode them when present;
missing fields decode to `None` so an existing local catalog remains readable.
Add one manager helper that derives issuer, validity, and SHA-256 fingerprint
from the already-loaded `x509.Certificate`; use it in both create and import
before the atomic managed-file/catalog commit. Keep the model free of
cryptography imports.

Extend `SignatureLibraryRow` with an optional expiration value. Populate it for
managed certificate rows and leave orphan/legacy rows unknown. For
`EXPIRATION_SOONEST`, parse valid ISO values to UTC timestamps, put known dates
first, and use display name as a deterministic tie-breaker. Then apply the
existing configured-first and pinned-first stable partitions. Add the third Qt
combo item and update the fake-binding fallback index logic so persisted
`expiration_soonest` survives reopening the Library.

Add model/codec tests for metadata round trips and missing-field decoding, manager
tests proving created/imported metadata matches the actual certificate, session
tests proving known/unknown expiration ordering plus configured/pinned priority,
and a Qt test proving the third sort choice is exposed and persisted. Update
`SCHEMAS.md`, the catalog and readiness child plans, `docs/ARCHITECTURE.md`, and
the parent plan with exact evidence and remaining gaps.

## Milestones

Milestone 1 is the model/codec and manager metadata path. It is complete when a
created or imported record round-trips with the exact public certificate facts
and old fixture payloads still decode. Milestone 2 is the Library projection and
Qt control. It is complete when expiration sorting works with unknown values and
does not move configured or pinned entries below unconfigured/unpinned ones.
Milestone 3 is the acceptance gate: focused tests, full suite, Ruff, diff check,
bounded Qt lifecycle audit, process cleanup, documentation, and commit all pass.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`.

    rg -n "ManagedCertificate|CertificateImportInspection|EXPIRATION_SOONEST|available_sorts" src tests docs/SCHEMAS.md
    .venv/bin/pytest -q tests/unit/test_certificate_models.py tests/unit/test_config_schemas.py tests/unit/test_certificate_manager.py tests/unit/test_signature_library_session.py tests/unit/test_qt_app_frame_profile_library.py
    # 74 passed
    .venv/bin/ruff check src tests
    .venv/bin/pytest -q
    git diff --check

For the bounded lifecycle audit, use a unique temporary configuration/cache
root, a 30-second foreground timeout, and remove the root afterward. Check for
owned `FoliaSeal`, `foliaseal`, `PySide6`, and `pytest` processes before and after
the command. The timeout is only lifecycle evidence; it is not display-backed
acceptance. Never leave a dialog or process open.

## Validation and Acceptance

The metadata tests must fail before the model/manager edits and pass afterward.
The focused command must pass, followed by the complete `.venv/bin/pytest -q`,
Ruff, and `git diff --check`. A Library session containing certificates expiring
in 30 and 90 days plus an unknown legacy row must produce the 30-day row first
within the same configured/pinned partition and the unknown row last. Selecting
“Expiration soonest” in the Qt dialog must persist `expiration_soonest` through
the existing AppSettings callback. The catalog JSON must contain no password,
passphrase, private key, or secret reference beyond the separate configuration
secret reference already governed by `SCHEMAS.md`.

## Idempotence and Recovery

All tests use temporary catalogs and certificate storage. If a commit fails,
leave source PDFs and user data untouched, update `Progress` with the exact
completed/remaining work, remove temporary roots, and retry. Do not delete or
rewrite a user catalog merely to make a test pass.

## Artifacts and Notes

Evidence: the initial focused run failed on the old exact codec-shape assertion
because the four metadata keys were absent from its expected set; after the model,
codec, manager, session, and Qt changes the focused command passed `74 passed`.
The full command passed `1269 passed, 20 skipped, 1 warning` in 48.83 seconds;
Ruff and `git diff --check` passed. The session row order for 30-day, 90-day,
and unknown dates was `Sooner, Later, Legacy`; the Qt fake-binding selector
contains `Name A–Z`, `Name Z–A`, and `Expiration soonest`. The bounded command
exited `1` with `SingleInstanceUnavailable` before frame creation; its isolated
root was removed and no FoliaSeal/PySide6/pytest process remained. No SVG was
added because this is an existing Library control, not a new topology.

## Interfaces and Dependencies

`ManagedCertificate` remains a plain application dataclass. The manager may use
`cryptography.x509` at its existing boundary, while codecs remain JSON-only and
the Library remains toolkit-independent. `SignatureLibraryRow.expiration` is
display projection data; it must not become a second persistence authority.
Use the existing `LibrarySort` and `LibrarySortOrder` enum values rather than
adding another setting. Any parsing failure must produce an unknown-last row,
not a crash or fabricated date.

Revision note: 2026-08-10 / Codex
Created after a live compliance audit found that the governing schema's public
validity metadata and the already-declared expiration sort were not connected.

Revision note: 2026-08-10 / Codex
Completed the model/codec/manager/Library/Qt vertical slice, including legacy
read behavior, subject distinguished name, focused red-to-green evidence, full
suite results, and bounded cleanup evidence.
