# Per-document certificate selection and certificate readiness

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can per-document Certificate selection and readiness states in the real FoliaSeal GUI. It is mapped to SPEC goals 6–7 and UI_SPEC sections 3, 11, and 15. The
slice is one vertical path through the relevant persistent model,
application workflow, Qt surface, focused tests, and observable acceptance.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are frozen governing contracts.
- [ ] docs/ExecPlans/ui_signing_rail_stage_status_execplan.md, docs/ExecPlans/ui_first_use_preset_setup_execplan.md, docs/ExecPlans/ui_certificate_import_configuration_execplan.md, and docs/ExecPlans/ui_certificate_create_export_password_execplan.md

## Progress

- [ ] (2026-08-09) Audit current behavior and add a failing focused test.
- [ ] (2026-08-09) Implement the smallest complete model/application/Qt path.
- [ ] (2026-08-09) Retire migrated compatibility or phase3 product cruft whose consumers are gone.
- [ ] (2026-08-09) Run focused, regression, and GUI validation; clean processes and artifacts.
- [ ] (2026-08-09) Update this plan and relevant docs, then commit.

## Surprises & Discoveries

- Observation: certificate selection resolves material separately from readiness; the child must
  represent expired, missing-password, retained-unconfigured, and ready states distinctly.
  Evidence: the live source paths and focused tests listed below are the audit baseline.

## Decision Log

- Decision: obey SPEC.md, SCHEMAS.md, and UI_SPEC.md in that precedence order.
  Rationale: these are the repository's explicit authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep the slice limited to one user-visible per-document certificate selection and certificate readiness outcome.
  Rationale: narrow changes are independently testable and recoverable.
  Date/Author: 2026-08-09 / Codex

## Outcomes & Retrospective

Not started. Record the demonstrated behavior, evidence, and remaining gaps at completion.

## Context and Orientation

The relevant code is signing_workspace_properties_panel.py; signing_setup_session.py; certificate readiness/material resolver. FoliaSeal is a Python/Qt Linux PDF signing application. The
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

Integrate the Certificates catalog into the preset-first rail. Apply a selected certificate configuration immediately without carrying one from another document, expose self-signed/expiry/password states in plain language, and block only genuinely non-ready certificates while permitting warnings. Add or preserve typed application and public Qt-port boundaries rather than reaching
through private widgets. Keep schema and terminology aligned with the frozen documents. When a
legacy path is replaced, prove its callers are migrated before deleting it.

## Milestones

Milestone 1 adds resolver tests for ready, expired, missing-key, and retained-unconfigured states.
Milestone 2 connects those states to the properties panel and signing coordinator. Milestone 3
records plain-language GUI observations, focused results, and cleanup.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

    rg -n -e 'certificate|ready|expired|password' src/foliaseal/presentation/qt/signing_workspace_properties_panel.py src/foliaseal/application/signing_setup_session.py src/foliaseal/application/signing_material_resolver.py
    .venv/bin/pytest -q tests/unit/test_signing_setup_session.py tests/unit/test_signing_material_resolver.py tests/unit/test_qt_signing_shell.py
    .venv/bin/ruff check src tests
    git diff --check

Run this bounded walkthrough from /home/daekar/FoliaSeal with an isolated configuration root:

    audit_root=$(mktemp -d /tmp/foliaseal-plan-audit-XXXXXX)
    timeout --foreground 30s env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf || test "$?" -eq 124
    ps -eo pid,cmd | rg 'FoliaSeal|foliaseal|PySide6|pytest' | rg -v 'rg ' || true
    find "$audit_root" -mindepth 1 -maxdepth 2 -type f -delete
    rmdir "$audit_root" 2>/dev/null || true

Expected evidence is the stated user-visible behavior plus a mandatory Qt-test or display-backed
walkthrough. Record the exact input sequence, widget state, expected observation, evidence path, and
cleanup result; the bounded timeout is only a lifecycle check.

## Validation and Acceptance

Acceptance is behavioral: A partial preset clearly requests an explicit certificate; selecting one updates readiness and identity preview; expired or missing-key entries block with one next action while self-signed/local trust remains nonblocking. Focused tests must pass, shared-code changes must
leave the full suite green, and the GUI audit must record the visible result and cleanup.

## Required Acceptance Cases

Readiness warns but permits expiry within 30 days, blocks expired/not-yet-valid/missing-file/missing-key
states, prompts for a missing password, and uses the exact local/self-signed caveat from UI_SPEC.md.
Selecting a partial preset never carries a certificate from another document.

## Evidence Record

Before completion, record the exact resolver/coordinator test command and result, the GUI selection
sequence and ready/warning/blocked observations, evidence path, cleanup, and compatibility grep proof.

## Idempotence and Recovery

Use temporary configuration and sibling output paths. If work fails halfway, preserve user PDFs and
drafts, update Progress with completed/remaining work, clean owned processes and artifacts, and
retry from the recorded state. Do not resurrect removed compatibility paths.

## Artifacts and Notes

Record concise output, focused screenshots or JSON under ignored artifacts/when useful, and exact
changed files. Never commit private keys, passwords, generated PDFs, or machine-local absolute paths.

## Interfaces and Dependencies

Use the existing typed application workflows, schema models, persistence stores, and public Qt frame
or workspace ports. The final behavior must be exercised by tests/unit/test_signing_setup_session.py tests/unit/test_signing_material_resolver.py tests/unit/test_qt_signing_shell.py. Any temporary adapter must
name its remaining consumer and retirement condition in this plan.

Revision note: 2026-08-09 / Codex
Created as a dependency-ordered child of the approved SPEC/UI_SPEC compliance breakdown.
