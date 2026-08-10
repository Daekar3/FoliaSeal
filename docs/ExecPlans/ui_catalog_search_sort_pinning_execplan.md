# Catalog search, sort, pinning, naming, and deletion rules

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can search, sort, pin, rename, duplicate, and delete catalog entries safely across restarts in the real FoliaSeal GUI. It is mapped to UI_SPEC sections 6 and 14; SCHEMAS storage rules. The
slice is one vertical path through the relevant persistent model,
application workflow, Qt surface, focused tests, and observable acceptance.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are frozen governing contracts.
- [ ] docs/ExecPlans/ui_signature_library_topology_execplan.md
- [ ] docs/ExecPlans/ui_window_theme_responsive_execplan.md

## Progress

- [ ] (2026-08-09) Audit current behavior and add a failing focused test.
- [ ] (2026-08-09) Implement the smallest complete model/application/Qt path.
- [ ] (2026-08-09) Retire migrated compatibility or phase3 product cruft whose consumers are gone.
- [ ] (2026-08-09) Run focused, regression, and GUI validation; clean processes and artifacts.
- [ ] (2026-08-09) Update this plan and relevant docs, then commit.

## Surprises & Discoveries

- Observation: catalog persistence is implemented separately from the AppSettings restart state;
  this child owns the explicit bridge for last-catalog, sort, and stable pin semantics.
  Evidence: the live source paths and focused tests listed below are the audit baseline.

## Decision Log

- Decision: obey SPEC.md, SCHEMAS.md, and UI_SPEC.md in that precedence order.
  Rationale: these are the repository's explicit authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep the slice limited to one user-visible catalog search, sort, pinning, naming, and deletion rules outcome.
  Rationale: narrow changes are independently testable and recoverable.
  Date/Author: 2026-08-09 / Codex

## Outcomes & Retrospective

Not started. Record the demonstrated behavior, evidence, and remaining gaps at completion.

## Context and Orientation

The relevant code is reusable signing models/catalog store; Library list/detail widgets; schemas/profile storage. FoliaSeal is a Python/Qt Linux PDF signing application. The
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

Implement case-insensitive live search, Name A-Z/Z-A sorting, expiration sort for certificates, pinned-first ordering, trimmed case-insensitive unique names, and explicit Rename/Duplicate/Delete rules. Prevent dangling references and preserve pins across rename and merged results. Add or preserve typed application and public Qt-port boundaries rather than reaching
through private widgets. Keep schema and terminology aligned with the frozen documents. When a
legacy path is replaced, prove its callers are migrated before deleting it.

Consume the canonical AppSettings keys owned by
`docs/ExecPlans/ui_window_theme_responsive_execplan.md` for `library_last_catalog` and
`library_sort`; do not create a second settings schema. Add catalog fixtures proving those keys are
preserved while Library open state/session drafts remain non-restorable.

## Milestones

Milestone 1 adds model/store tests for normalized names, stable pins, sorting, and AppSettings keys.
Milestone 2 wires the Library controls and refresh behavior through the catalog authority. Milestone
3 proves restart persistence and deletion safety in the GUI, then records evidence and cleanup.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e 'pin|sort|search|duplicate|delete|display_name' src/foliaseal/application/reusable_signing_models.py src/foliaseal/application/reusable_signing_objects.py src/foliaseal/infra/config/profile_storage.py
    .venv/bin/pytest -q tests/unit/test_reusable_signing_models.py tests/unit/test_reusable_signing_objects.py tests/unit/test_signature_preset_storage.py
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

Acceptance is behavioral: Each of the four catalogs has predictable live filtering and sorting; invalid names and referenced-object deletion are explained and cannot corrupt persisted references. Focused tests must pass, shared-code changes must
leave the full suite green, and the GUI audit must record the visible result and cleanup.

## Required Acceptance Cases

Pins persist by stable object reference across restart; last catalog and sort persist in AppSettings;
search exists only while the Library is open. Names are trimmed and case-insensitively unique.
Referenced deletion is blocked or resolved without dangling references, and pinned entries remain first
after rename or merged search results.

## Evidence Record

Before completion, record the exact catalog/AppSettings test command and result, the GUI search,
sort, pin, rename, and delete sequence with observed rows, the evidence path and restart result,
serialized fixture compatibility result, cleanup, and compatibility grep proof.

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
or workspace ports. The final behavior must be exercised by tests/unit/test_reusable_signing_models.py tests/unit/test_reusable_signing_objects.py tests/unit/test_signature_preset_storage.py. Any temporary adapter must
name its remaining consumer and retirement condition in this plan.

Revision note: 2026-08-09 / Codex
Created as a dependency-ordered child of the approved SPEC/UI_SPEC compliance breakdown.
