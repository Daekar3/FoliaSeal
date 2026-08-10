# Document Signatures review surface

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can integrity-first Document Signatures review and jump/highlight behavior in the real FoliaSeal GUI. It is mapped to UI_SPEC SUR06, section 16, and acceptance scenario 5. The
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

- Observation: signature review must present integrity states and claimed-versus-trusted time from
  document-review data, not infer them from certificate labels in the Qt surface.
  Evidence: the live source paths and focused tests listed below are the audit baseline.

## Decision Log

- Decision: obey SPEC.md, SCHEMAS.md, and UI_SPEC.md in that precedence order.
  Rationale: these are the repository's explicit authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep the slice limited to one user-visible document signatures review surface outcome.
  Rationale: narrow changes are independently testable and recoverable.
  Date/Author: 2026-08-09 / Codex

## Outcomes & Retrospective

Not started. Record the demonstrated behavior, evidence, and remaining gaps at completion.

## Context and Orientation

The relevant code is src/foliaseal/application/document_review.py; presentation/qt/signing_workspace_review_bridge.py; modeless review dialog. FoliaSeal is a Python/Qt Linux PDF signing application. The
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

Build the modeless Document Signatures surface listing signed visible/invisible signatures and unsigned fields in document order, with optional signing-order sort, integrity-first plain language, and an explicit review-bridge `jump_to_signature(signature_id)` event that navigates and highlights the chosen visible item. Do not reuse generic viewer selection callbacks for review navigation. Add or preserve typed application and public Qt-port boundaries rather than reaching
through private widgets. Keep schema and terminology aligned with the frozen documents. When a
legacy path is replaced, prove its callers are migrated before deleting it.

## Milestones

Milestone 1 adds review fixtures for valid, changed, invalid, could-not-verify, unsigned, claimed
time, and trusted timestamp states. Milestone 2 wires the modeless review surface and jump/highlight
bridge. Milestone 3 proves the complete status vocabulary in the GUI and records evidence.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

    rg -n -e 'signature|valid|timestamp|highlight' src/foliaseal/application/document_review.py src/foliaseal/application/document_review_workspace.py src/foliaseal/presentation/qt/signing_workspace_review_bridge.py
    .venv/bin/pytest -q tests/unit/test_document_review.py tests/unit/test_document_review_workspace.py
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

Acceptance is behavioral: Opening Document Signatures shows existing signatures and eligible fields without exposing a general PDF-properties inspector; selecting a visible item navigates and highlights it. Focused tests must pass, shared-code changes must
leave the full suite green, and the GUI audit must record the visible result and cleanup.

## Required Acceptance Cases

The review surface must render valid, changed-after-signature (including permitted changes), invalid,
could-not-verify, and unsigned states. It distinguishes claimed signing time from a trusted timestamp
and keeps certificate trust secondary to integrity.

## Evidence Record

Before completion, record the exact review fixture/test command and result, the GUI status sequence
for every integrity/time state and the jump/highlight observation, evidence path, cleanup, and
compatibility grep proof.

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
or workspace ports. The final behavior must be exercised by tests/unit/test_document_review.py and Qt review-bridge tests. Any temporary adapter must
name its remaining consumer and retirement condition in this plan.

Revision note: 2026-08-09 / Codex
Created as a dependency-ordered child of the approved SPEC/UI_SPEC compliance breakdown.
