# Reconcile certificate-manager architecture documentation

This child ExecPlan is a living document maintained under
`.agents/skills/write-execplan/PLANS.md`. It is required to close the parent
certificate-manager slice because compliance review found stale current
architecture text, not a production behavior defect.

## Purpose / Big Picture

Make `docs/ARCHITECTURE.md` describe the implemented `CertificateManager`
boundary and its actual exception surface. Current non-historical paragraphs
still name deleted `CertificateLifecycleService` and `CertificateImportError`,
which would mislead future contributors and violate the architecture map.

## Child ExecPlan Dependencies

- [x] Parent manager implementation, tests, and scoped `phase3` support rename are complete.
- [x] Two independent compliance reviews identified the same documentation-only discrepancy.

## Progress

- [x] (2026-08-02) Recorded review findings at current architecture lines 282, 843, 956, and 1125.
- [x] Updated current architecture ownership, flow, exception, and debt text to use `CertificateManager` and typed request/result contracts.
- [x] Ran documentation search, diff check, compileall, and final compliance review.
- [x] (2026-08-02) Post-fix review passed; focused manager/app-frame/storage/schema validation passed 65 tests and historical ExecPlan references were confirmed archival only.

## Surprises & Discoveries

- Observation: The implementation intentionally uses built-in `ValueError` for malformed PKCS#12 input and `ConfigValidationError` for catalog/name/secret-policy validation; no dedicated import exception remains.
  Evidence: `src/foliaseal/application/certificate_manager.py` has no `CertificateImportError` export.

## Decision Log

- Decision: Reconcile documentation to the current exception surface instead of adding a compatibility exception class.
  Rationale: the user asked to remove legacy cruft, and the implementation already has a coherent manager boundary; adding an alias solely for stale prose would reintroduce dead API.
  Date/Author: 2026-08-02 / Codex.

## Outcomes & Retrospective

The current architecture documentation now names `CertificateManager` as the
application boundary, records typed requests/results and the app-frame refresh
flow, and describes `ValueError` for malformed/missing imports alongside
`ConfigValidationError` for catalog and policy validation. Historical ExecPlan
records and stable Phase 3 evidence nomenclature remain unchanged. The child
plan is closed as part of the parent slice; commit hashes remain to be recorded.

## Context and Orientation

The parent slice replaced the three application certificate services with
`src/foliaseal/application/certificate_manager.py`. Qt dialogs submit typed
requests; `CertificateManager` returns typed operation results. Persisted
catalog schemas and paths are unchanged. Only current architecture prose must
be corrected; historical ExecPlans remain historical records.

## Plan of Work

Update the current app-frame flow description, configuration/reusable-object
ownership section, certificate catalog producer/flow section, and known-debt
table to name `CertificateManager`. Replace the deleted `CertificateImportError`
claim with the actual manager validation behavior: malformed/missing imports
raise `ValueError`, while catalog and policy validation raises
`ConfigValidationError`; secret-tool adapter failures retain their adapter
exception semantics. Preserve historical entries that explicitly document the
old services as past architecture.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    rg -n "CertificateLifecycleService|CertificateImportError" docs/ARCHITECTURE.md
    git diff --check
    .venv/bin/python -m compileall -q src tests

Current non-historical sections must contain no deleted service/error names.

## Validation and Acceptance

The parent and child plans are accepted when current architecture prose matches
the manager implementation, historical records remain intact, diff checks and
compileall pass, and the final compliance reviewer reports no remaining stale
current reference.

## Idempotence and Recovery

Use focused documentation patches only. Do not rewrite historical ExecPlans or
rename stable Phase 3 evidence modules. If a line is too large to patch safely,
have the documentation worker reconcile it with architecture-steward guidance
and verify the resulting diff manually.

## Artifacts and Notes

Record the documentation worker result, search output, final review result, and
commit hash here and in the parent plan.

## Interfaces and Dependencies

The documented boundary is `CertificateManager` with `snapshot()`, `create()`,
`import_()`, `save_configuration()`, `delete_configuration()`,
`delete_managed_certificate()`, and `export()`. No new production interface is
introduced by this child plan.

## Revision Notes

2026-08-02: Created from two independent post-implementation compliance reviews.
