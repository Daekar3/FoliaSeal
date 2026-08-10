# Certificate import and configuration catalog

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can import a validated Certificate, inspect it, configure it for signing, and recover cleanly from rejection in the real FoliaSeal GUI. It is mapped to SPEC managed certificate workflow and UI_SPEC section 15. The
slice is one vertical path through the relevant persistent model,
application workflow, Qt surface, focused tests, and observable acceptance.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are frozen governing contracts.
- [ ] docs/ExecPlans/ui_signature_library_topology_execplan.md
- [ ] docs/ExecPlans/ui_catalog_search_sort_pinning_execplan.md

## Progress

- [ ] (2026-08-09) Audit current behavior and add a failing focused test.
- [ ] (2026-08-09) Implement the smallest complete model/application/Qt path.
- [ ] (2026-08-09) Retire migrated compatibility or phase3 product cruft whose consumers are gone.
- [ ] (2026-08-09) Run focused, regression, and GUI validation; clean processes and artifacts.
- [ ] (2026-08-09) Update this plan and relevant docs, then commit.

## Surprises & Discoveries

- Observation: certificate import and configuration are split across manager, catalog, and Qt
  management seams; this child must keep retained-but-unconfigured material distinct from a
  signing-ready configuration.
  Evidence: the live source paths and focused tests listed below are the audit baseline.

## Decision Log

- Decision: obey SPEC.md, SCHEMAS.md, and UI_SPEC.md in that precedence order.
  Rationale: these are the repository's explicit authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep the slice limited to one user-visible certificate import and configuration catalog outcome.
  Rationale: narrow changes are independently testable and recoverable.
  Date/Author: 2026-08-09 / Codex

## Outcomes & Retrospective

Not started. Record the demonstrated behavior, evidence, and remaining gaps at completion.

## Context and Orientation

The relevant code is src/foliaseal/application/certificate_manager.py (including import_),
certificate_catalog_repository.py, app_frame_certificate_management.py, and the certificate
stores. FoliaSeal is a Python/Qt Linux PDF signing application. The
primary flow is open, review, select reusable setup, place one visible signature, preview
readiness, sign/save, verify, and reopen. V1 excludes tabs, printing, broad PDF editing, cloud
workflow, enterprise trust administration, and multiple pending signatures.

A compatibility surface is an adapter retained only for old callers. “phase3” names identify legacy
evidence/harness infrastructure and must not be introduced into ordinary product UI or new primary
contracts; production backend/evidence imports may be renamed only after a neutral migration proves
the old name is no longer required.

## Change Slice

Primary change class: behavior change. Allowed changes are the named modules, focused tests,
bounded ignored local evidence, and minimum truthful documentation. Do not mix unrelated evidence
rebaselines, V2 features, or packaging work.

## Plan of Work

Build the user-facing Certificates catalog around content-validated PKCS#12 import, atomic managed storage, identity/issuer/validity/private-key inspection, unique display naming, optional remembered password, and a separate schema-level Certificate Configuration reference. Ordinary UI says Certificate and configuration; it must not expose PKCS#12 or Managed Certificate jargon. Reject duplicates, missing private keys, unsupported content, cancellation, and residue. Add or preserve typed application and public Qt-port boundaries rather than reaching
through private widgets. Keep schema and terminology aligned with the frozen documents. When a
legacy path is replaced, prove its callers are migrated before deleting it.
If the catalog schema changes, add a before/after serialized fixture and backward-read or deliberate
rejection test; if it does not, add a compatibility test proving the existing catalog remains valid.

## Milestones

Milestone 1 establishes import inspection and retained-but-unconfigured catalog tests. Milestone 2
wires the user-facing Certificate configuration flow and explicit readiness transition. Milestone 3
proves import failure recovery and cleanup in the GUI, then records the acceptance handoff.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e 'import_|configuration|private|issuer|validity' src/foliaseal/application/certificate_manager.py src/foliaseal/application/certificate_catalog_repository.py src/foliaseal/presentation/qt/app_frame_certificate_management.py
    .venv/bin/pytest -q tests/unit/test_certificate_manager.py tests/unit/test_certificate_catalog_repository.py tests/unit/test_qt_app_frame_certificate_management.py
    .venv/bin/ruff check src tests
    .venv/bin/pytest -q
    git diff --check

Run this bounded walkthrough from /home/daekar/FoliaSeal with an isolated configuration root:

    audit_root=$(mktemp -d /tmp/foliaseal-plan-audit-XXXXXX)
    timeout --foreground 30s env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf || test "$?" -eq 124
    ps -eo pid,cmd | rg 'FoliaSeal|foliaseal|PySide6|pytest' | rg -v 'rg ' || true
    rm -rf "$audit_root"
    test ! -e "$audit_root"

Expected evidence is the stated user-visible behavior plus a mandatory Qt-test or display-backed
walkthrough. Record the exact input sequence, widget state, expected observation, evidence path, and
cleanup result; the bounded timeout is only a lifecycle check.

## Validation and Acceptance

Acceptance is behavioral: Importing a valid .p12/.pfx produces one configured catalog entry atomically; invalid or cancelled import leaves no managed residue and explains the next action. Focused tests must pass, shared-code changes must
leave the full suite green, and the GUI audit must record the visible result and cleanup.

## Required Acceptance Cases

Import inspects identity, issuer, validity, private-key presence, and warnings. Issuer, validity,
and private-key status are runtime inspection results from the manager/material loader, not password
or secret fields added to the persisted catalog. A retained managed
file without a configuration remains visible as “Not configured for signing” with Configure, Export
backup, and Delete actions; it is not preset-selectable. Cancelled, duplicate, unsupported, and
missing-private-key inputs leave no residue.

## Evidence Record

Before completion, record the exact import/catalog/Qt test command and result, the GUI import and
configuration sequence, retained-but-unconfigured observation, evidence path, serialized fixture
compatibility result, cleanup, and compatibility grep proof.

Record the contributing UI_SPEC scenario ID(s) and either the owning SVG path or an explicit
"no SVG" decision alongside the evidence row.
Also record the exact focused test node and expected result (`N passed`); when the slice adds a new
contract, record that the test was red before implementation and green afterward.

## Idempotence and Recovery

Use temporary configuration and sibling output paths. If work fails halfway, preserve user PDFs and
drafts, update Progress with completed/remaining work, clean owned processes and artifacts, and
retry from the recorded state. Do not resurrect removed compatibility paths.

## Artifacts and Notes

Record concise output, focused screenshots or JSON under ignored artifacts/when useful, and exact
changed files. Never commit private keys, passwords, generated PDFs, or machine-local absolute paths.

## Interfaces and Dependencies

Use the existing typed application workflows, schema models, persistence stores, and public Qt frame
or workspace ports. The final behavior must be exercised by tests/unit/test_certificate_manager.py tests/unit/test_certificate_catalog_repository.py tests/unit/test_qt_app_frame_certificate_management.py. Any temporary adapter must
name its remaining consumer and retirement condition in this plan.

Revision note: 2026-08-09 / Codex
Created as a dependency-ordered child of the approved SPEC/UI_SPEC compliance breakdown.
