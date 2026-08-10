# Safe links and external-source change handling

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can follow safe internal links, understand blocked external actions, and recover explicitly from source changes in the real FoliaSeal GUI. It is mapped to UI_SPEC section 16 and WF01/WF05. The
slice is one vertical path through the relevant persistent model,
application workflow, Qt surface, focused tests, and observable acceptance.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are frozen governing contracts.
- [ ] docs/ExecPlans/ui_document_lifecycle_recovery_execplan.md
- [ ] docs/ExecPlans/ui_pdf_navigation_zoom_pan_execplan.md

## Progress

- [ ] (2026-08-09) Audit current behavior and add a failing focused test.
- [ ] (2026-08-09) Implement the smallest complete model/application/Qt path.
- [ ] (2026-08-09) Retire migrated compatibility or phase3 product cruft whose consumers are gone.
- [ ] (2026-08-09) Run focused, regression, and GUI validation; clean processes and artifacts.
- [ ] (2026-08-09) Update this plan and relevant docs, then commit.

## Surprises & Discoveries

- Observation: external-link and changed-file handling crosses viewer interaction and app-frame
  open services; this child must preserve the draft while making Reload/Locate/Close choices clear.
  Evidence: the live source paths and focused tests listed below are the audit baseline.

## Decision Log

- Decision: obey SPEC.md, SCHEMAS.md, and UI_SPEC.md in that precedence order.
  Rationale: these are the repository's explicit authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep the slice limited to one user-visible safe links and external-source change handling outcome.
  Rationale: narrow changes are independently testable and recoverable.
  Date/Author: 2026-08-09 / Codex

## Outcomes & Retrospective

Not started. Record the demonstrated behavior, evidence, and remaining gaps at completion.

## Context and Orientation

The relevant code is viewer interaction/session modules; signing workspace interaction bridge; app-frame open state. FoliaSeal is a Python/Qt Linux PDF signing application. The
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

Allow internal PDF links only in Pan mode with Back/Forward history. Intercept external http, https, and mailto destinations for confirmation and block file, executable, JavaScript, embedded launch, and arbitrary schemes. Monitor the source without auto-reloading and offer a condition-only Reload/Ignore or Locate/Close banner. Add or preserve typed application and public Qt-port boundaries rather than reaching
through private widgets. Keep schema and terminology aligned with the frozen documents. When a
legacy path is replaced, prove its callers are migrated before deleting it.

## Milestones

Milestone 1 tests external-link validation and changed-file decisions. Milestone 2 wires Reload,
Locate, Ignore, and Close through the open service while preserving drafts. Milestone 3 proves the
recovery choices in the GUI and records cleanup.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

    rg -n -e 'link|external|Reload|Ignore|Locate|Close' src/foliaseal/application/viewer_interaction_session.py src/foliaseal/presentation/qt/signing_workspace_interaction_bridge.py src/foliaseal/presentation/qt/app_frame_workspace_open.py
    .venv/bin/pytest -q tests/unit/test_viewer_interaction_session.py tests/unit/test_qt_app_frame_workspace_open.py
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

Acceptance is behavioral: Link clicks cannot escape the explicit safety policy; source edits never silently replace the viewed document or permit signing against an unacknowledged changed source. Focused tests must pass, shared-code changes must
leave the full suite green, and the GUI audit must record the visible result and cleanup.

## Evidence Record

Before checking this child in the parent, record the governing UI_SPEC requirement, exact focused
test command/result, link/change decision sequence and observed draft preservation, evidence path and
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
or workspace ports. Create tests/unit/test_qt_safe_links_external_changes.py. The final behavior
must be exercised by tests/unit/test_viewer_interaction_session.py,
tests/unit/test_qt_app_frame_workspace_open.py, and that new Qt test. Any temporary adapter must
name its remaining consumer and retirement condition in this plan.

Revision note: 2026-08-09 / Codex
Created as a dependency-ordered child of the approved SPEC/UI_SPEC compliance breakdown.
