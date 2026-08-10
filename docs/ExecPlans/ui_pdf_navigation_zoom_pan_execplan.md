# Page navigation, fit, zoom, and pan

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can navigate pages, choose Fit Page or Fit Width, set exact zoom, and pan without changing pages in the real FoliaSeal GUI. It is mapped to UI_SPEC section 8 and WF01. The
slice is one vertical path through the relevant persistent model,
application workflow, Qt surface, focused tests, and observable acceptance.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are frozen governing contracts.
- [ ] docs/ExecPlans/ui_document_lifecycle_recovery_execplan.md

## Progress

- [ ] (2026-08-09) Audit current behavior and add a failing focused test.
- [ ] (2026-08-09) Implement the smallest complete model/application/Qt path.
- [ ] (2026-08-09) Retire migrated compatibility or phase3 product cruft whose consumers are gone.
- [ ] (2026-08-09) Run focused, regression, and GUI validation; clean processes and artifacts.
- [ ] (2026-08-09) Update this plan and relevant docs, then commit.

## Surprises & Discoveries

- Observation: the live viewer currently clamps zoom to 25%–400% and maps wheel events to zoom,
  while UI_SPEC requires 10%–800% and wheel/scrollbar panning that does not change pages.
  Evidence: src/foliaseal/application/viewer_session.py:10-18 and
  src/foliaseal/presentation/qt/viewer_widget.py:141-148.

## Decision Log

- Decision: obey SPEC.md, SCHEMAS.md, and UI_SPEC.md in that precedence order.
  Rationale: these are the repository's explicit authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep the slice limited to one user-visible page navigation, fit, zoom, and pan outcome.
  Rationale: narrow changes are independently testable and recoverable.
  Date/Author: 2026-08-09 / Codex

## Outcomes & Retrospective

Not started. Record the demonstrated behavior, evidence, and remaining gaps at completion.

## Context and Orientation

The relevant code is src/foliaseal/application/viewer_session.py; viewer_workflow.py; presentation/qt/viewer_widget.py; signing shell toolbar. FoliaSeal is a Python/Qt Linux PDF signing application. The
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

Expose a single-page viewer with an editable one-based page field, Page Up/Down and Ctrl+Home/End navigation, Fit Page default, Fit Width, exact 10%-800% zoom, and wheel/scrollbar pan that never changes pages. Preserve overlay alignment and page-local render failures. Add or preserve typed application and public Qt-port boundaries rather than reaching
through private widgets. Keep schema and terminology aligned with the frozen documents. When a
legacy path is replaced, prove its callers are migrated before deleting it.

## Milestones

Milestone 1 changes viewer-session limits and adds page/zoom/pan tests. Milestone 2 replaces the
wheel event behavior with the specified pan/zoom modifier contract while preserving overlay alignment.
Milestone 3 proves navigation and page-local recovery with recorded GUI evidence.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

    rg -n -e 'zoom|page|wheel|render' src/foliaseal/application/viewer_session.py src/foliaseal/application/viewer_workflow.py src/foliaseal/presentation/qt/viewer_widget.py
    .venv/bin/pytest -q tests/unit/test_viewer_session.py tests/unit/test_viewer_workflow.py tests/unit/test_qt_viewer_widget.py
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

Acceptance is behavioral: A user can open a multi-page PDF, see the current page of total pages, navigate without guessing, pan with wheel/scrollbars, change zoom, and retain the signature overlay on the correct page. Focused tests must pass, shared-code changes must
leave the full suite green, and the GUI audit must record the visible result and cleanup.

## Evidence Record

Before checking this child in the parent, record the governing UI_SPEC requirement, exact focused
test command/result, page/zoom/pan input sequence and observed overlay state, evidence path and
cleanup result, and compatibility grep proof.

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
or workspace ports. The final behavior must be exercised by tests/unit/test_viewer_session.py tests/unit/test_viewer_workflow.py tests/unit/test_qt_viewer_widget.py. Any temporary adapter must
name its remaining consumer and retirement condition in this plan.

Revision note: 2026-08-09 / Codex
Created as a dependency-ordered child of the approved SPEC/UI_SPEC compliance breakdown.
