# Placement editor transaction and profile capture

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can edit and save fixed-page Placement values transactionally without storing PDF identity in the real FoliaSeal GUI. It is mapped to UI_SPEC SUR05, section 10, and normative placement SVG. The
slice is one vertical path through the relevant persistent model,
application workflow, Qt surface, focused tests, and observable acceptance.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are frozen governing contracts.
- [ ] docs/ExecPlans/ui_launch_no_document_execplan.md
- [ ] docs/ExecPlans/ui_window_theme_responsive_execplan.md

## Progress

- [ ] (2026-08-09) Audit current behavior and add a failing focused test.
- [ ] (2026-08-09) Implement the smallest complete model/application/Qt path.
- [ ] (2026-08-09) Retire migrated compatibility or phase3 product cruft whose consumers are gone.
- [ ] (2026-08-09) Run focused, regression, and GUI validation; clean processes and artifacts.
- [ ] (2026-08-09) Update this plan and relevant docs, then commit.

## Surprises & Discoveries

- Observation: the live PlacementProfile currently stores rectangle and page-selection fields while
  SCHEMAS.md also describes source-page semantics; this child must resolve that contract before
  wiring Save/Cancel.
  Evidence: the live source paths and focused tests listed below are the audit baseline.

## Decision Log

- Decision: obey SPEC.md, SCHEMAS.md, and UI_SPEC.md in that precedence order.
  Rationale: these are the repository's explicit authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep the slice limited to one user-visible placement editor transaction and profile capture outcome.
  Rationale: narrow changes are independently testable and recoverable.
  Date/Author: 2026-08-09 / Codex

## Outcomes & Retrospective

Not started. Record the demonstrated behavior, evidence, and remaining gaps at completion.

## Context and Orientation

The relevant code is src/foliaseal/presentation/qt/signing_workspace_refinement_dialog.py; reusable models; coordinate transforms/profile storage. FoliaSeal is a Python/Qt Linux PDF signing application. The
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

Begin by adopting the frozen SCHEMAS.md v2 contract: serialize `page_number`, `source_page`,
`top_pt`, `left_pt`, `width_pt`, `height_pt`, and `pinned`; migrate live `bottom_pt` by converting
from the current page coordinate system. Treat legacy `page_selection_mode="current_page"` as
input-only migration data and map it to a concrete serialized `page_number`; never add
`page_selection_mode` to the v2 output. Reject unknown legacy shapes with a clear migration error. The migration
must explicitly cover/removal-review `page_selection_mode`, `left_pt`, `bottom_pt`, `width_pt`,
`height_pt`, and `numeric_fine_tuning_enabled`; record a before/after fixture and backward-read test
before deleting old fields. Then provide a fixed-page Placement editor from a current PDF or blank page with direct
Page/Left/Top/Width/Height point fields and handles. Store only schema-approved reusable geometry
and compatibility metadata, never PDF identity or content; Save/Cancel must not mutate the active
document placement or preset. Add or preserve typed application and public Qt-port boundaries rather
than reaching through private widgets. When a legacy path is replaced, prove its callers are
migrated before deleting it.

Milestone 1 is the foundation gate and may proceed after launch and typed settings: implement the
v2 codec, migration fixture, backward-read or deliberate-rejection test, and update every persistence
consumer. Milestone 2 builds and tests the editor as a reusable public Qt/application component with
an isolated host; the later Library plan mounts that component after this child completes. This
avoids a circular dependency while ensuring the Library consumes the already-settled schema rather
than redefining it.

## Milestones

Milestone 1 resolves the SCHEMAS placement serialization decision and adds migration fixtures for
`top_pt`, `page_number`, and `source_page` (or an explicit rejection path). Milestone 2 implements
the editor transaction and profile persistence only after that decision. Milestone 3 proves Save,
Cancel, restart, and no-PDF editing with focused and GUI evidence.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

    rg -n -e 'Placement|page|left|top|width|height|Save|Cancel' src/foliaseal/presentation/qt/signing_workspace_refinement_dialog.py src/foliaseal/application/reusable_signing_models.py
    .venv/bin/pytest -q tests/unit/test_reusable_signing_models.py tests/unit/test_qt_visible_signature_setup_form.py
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

Acceptance is behavioral: A user can create and save a named Placement from a PDF or blank page, reopen it in the Library, and cancel without changing a live signing draft. Focused tests must pass, shared-code changes must
leave the full suite green, and the GUI audit must record the visible result and cleanup.

## Evidence Record

Before checking this child in the parent, record the governing UI_SPEC requirement and
`docs/ui/placement-profile-editor-exploratory.svg`,
exact focused test command/result, Save/Cancel input sequence and observed persisted fields, evidence
path and cleanup result, serialized migration result, and compatibility grep proof.

Record the contributing UI_SPEC scenario ID(s) and either the owning SVG path or an explicit
"no SVG" decision alongside the evidence row.

## Idempotence and Recovery

Use temporary configuration and sibling output paths. If work fails halfway, preserve user PDFs and
drafts, update Progress with completed/remaining work, clean owned processes and artifacts, and
retry from the recorded state. Do not resurrect removed compatibility paths.

## Artifacts and Notes

Record concise output, focused screenshots or JSON under ignored artifacts/when useful, and exact
changed files. Never commit private keys, passwords, generated PDFs, or machine-local absolute paths.

## Interfaces and Dependencies

Use the existing typed application workflows, schema models, persistence stores, and public Qt frame
or workspace ports. The final behavior must be exercised by tests/unit/test_reusable_signing_models.py,
tests/unit/test_qt_visible_signature_setup_form.py, and tests/unit/test_signature_preset_storage.py.
Any temporary adapter must
name its remaining consumer and retirement condition in this plan.

Revision note: 2026-08-09 / Codex
Created as a dependency-ordered child of the approved SPEC/UI_SPEC compliance breakdown.
