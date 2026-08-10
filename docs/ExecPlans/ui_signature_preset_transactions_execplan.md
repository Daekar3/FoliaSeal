# Signature Preset CRUD and reference semantics

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can create, edit, duplicate, rename, pin, and delete Signature Presets with safe references in the real FoliaSeal GUI. It is mapped to SPEC reusable-object semantics and UI_SPEC WF02/WF06. The
slice is one vertical path through the relevant persistent model,
application workflow, Qt surface, focused tests, and observable acceptance.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are frozen governing contracts.
- [x] docs/ExecPlans/ui_signature_library_topology_execplan.md (completed in `a4e97edab`)
- [x] docs/ExecPlans/ui_catalog_search_sort_pinning_execplan.md (completed in `ecf4f73ab`)

## Progress

- [x] (2026-08-10) Audit current behavior and add a failing focused test.
- [x] (2026-08-10) Implement the bounded model/application/Qt reference-validation and Save-boundary path.
- [ ] (2026-08-09) Retire migrated compatibility or phase3 product cruft whose consumers are gone.
- [x] (2026-08-10) Run focused, regression, and offscreen GUI validation; clean processes and artifacts.
- [x] (2026-08-10) Update this plan and relevant architecture docs.
- [ ] Commit the slice after compliance review.

## Surprises & Discoveries

- Observation: preset mutation is already represented by reusable-object model/store boundaries;
  this child must make nested Save/Cancel transactional and keep stable identifiers on rename.
  Evidence: the live source paths and focused tests listed below are the audit baseline.
- Observation: the production reusable-object service did not previously validate certificate
  configuration references because certificates live in a separate catalog. The AppFrame now injects
  an existence resolver, while direct test fixtures remain intentionally decoupled.
  Evidence: `ReusableSigningObjects(... certificate_configuration_exists=...)` and
  `tests/unit/test_reusable_signing_objects.py::test_production_boundary_rejects_missing_certificate_references`.
- Observation: the Library Save button was wired directly to the rename implementation. It now
  crosses an explicit `save_detail()` transaction boundary, but the full document-independent
  nested preset editor and dirty-switch/close prompts remain unimplemented.
  Evidence: `ReusableObjectLibraryDialog.save_detail()` and the compliance review boundary.

## Decision Log

- Decision: obey SPEC.md, SCHEMAS.md, and UI_SPEC.md in that precedence order.
  Rationale: these are the repository's explicit authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep the slice limited to one user-visible signature preset crud and reference semantics outcome.
  Rationale: narrow changes are independently testable and recoverable.
  Date/Author: 2026-08-09 / Codex

## Outcomes & Retrospective

This slice closes the production certificate-reference validation seam and makes the Library detail
Save action an explicit application-facing transaction boundary. It does not complete the full
UI_SPEC WF06 editor: preset component editing remains routed through the contextual signing
workflow, reason/location defaults are not yet modeled, and dirty-switch/close or active-placement
invalidation prompts remain open follow-on work.

## Context and Orientation

The relevant code is src/foliaseal/application/reusable_signing_models.py; profile_storage.py; Library preset editor. FoliaSeal is a Python/Qt Linux PDF signing application. The
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

Make Signature Preset a reference-only composition that always requires an Appearance and optionally references Certificate and Placement. Implement Save/Cancel, dirty editor prompts, duplicate/rename/delete, explicit conflict resolution, and no silent carry-over from another document. Add or preserve typed application and public Qt-port boundaries rather than reaching
through private widgets. Keep schema and terminology aligned with the frozen documents. When a
legacy path is replaced, prove its callers are migrated before deleting it.
Any new pin/reference field requires a before/after serialized preset fixture and backward-read or
deliberate rejection test; no placement field may be persisted before the placement child resolves
the governing schema conflict.

## Milestones

Milestone 1 adds transactional model/store tests. Milestone 2 wires nested editor Save/Cancel,
rename, duplicate, and delete through stable identifiers. Milestone 3 proves refresh and recovery
in the Library GUI and records the retirement evidence.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e 'SignaturePreset|SavePreset|RenameObject|DeleteObject' src/foliaseal/application/reusable_signing_models.py src/foliaseal/application/reusable_signing_objects.py src/foliaseal/infra/config/profile_storage.py
    .venv/bin/pytest -q tests/unit/test_reusable_signing_models.py tests/unit/test_signature_preset_storage.py
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

Acceptance is behavioral: A user can create, edit, duplicate, rename, pin, and delete a preset; invalid or dangling references are blocked; selecting a partial preset clearly exposes only its missing per-document inputs. Focused tests must pass, shared-code changes must
leave the full suite green, and the GUI audit must record the visible result and cleanup.

## Evidence Record

Before checking this child in the parent, record the governing UI_SPEC requirement, exact focused
test command/result, nested CRUD input sequence and observed catalog state, evidence path and cleanup
result, serialized compatibility result, and compatibility grep proof.

Record the contributing UI_SPEC scenario ID(s) and either the owning SVG path or an explicit
"no SVG" decision alongside the evidence row.
Also record the exact focused test node and expected result (`N passed`); when the slice adds a new
contract, record that the test was red before implementation and green afterward.

Current evidence (2026-08-10):

- Focused reusable-object, Library, and session tests: `20 passed`.
- Offscreen AppFrame/shell/Library/integration tests: `153 passed`.
- Updated focused set after the Save-boundary test: `21 passed`.
- Full regression: `1243 passed, 20 skipped, 1 warning`.
- Offscreen Library/no-document integration: `2 passed`.
- Ruff and `git diff --check`: clean.
- Process audit: no FoliaSeal, PySide6, or pytest processes remained.
- No new SVG: this bounded seam changes application validation and the existing Save/Cancel name
  boundary, not the Library topology.

## Idempotence and Recovery

Use temporary configuration and sibling output paths. If work fails halfway, preserve user PDFs and
drafts, update Progress with completed/remaining work, clean owned processes and artifacts, and
retry from the recorded state. Do not resurrect removed compatibility paths.

## Artifacts and Notes

Record concise output, focused screenshots or JSON under ignored artifacts/when useful, and exact
changed files. Never commit private keys, passwords, generated PDFs, or machine-local absolute paths.

## Interfaces and Dependencies

Use the existing typed application workflows, schema models, persistence stores, and public Qt frame
or workspace ports. The final behavior must be exercised by tests/unit/test_reusable_signing_models.py tests/unit/test_signature_preset_storage.py and Library preset tests. Any temporary adapter must
name its remaining consumer and retirement condition in this plan.

Revision note: 2026-08-09 / Codex
Created as a dependency-ordered child of the approved SPEC/UI_SPEC compliance breakdown.
