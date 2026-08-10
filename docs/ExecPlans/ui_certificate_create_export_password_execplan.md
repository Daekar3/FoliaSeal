# Certificate creation, export, remembered passwords, and deletion

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can create a certificate, export an encrypted backup, remember or clear its password, and delete it safely in the real FoliaSeal GUI. It is mapped to SPEC managed certificate workflow and UI_SPEC section 15. The
slice is one vertical path through the relevant persistent model,
application workflow, Qt surface, focused tests, and observable acceptance.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are frozen governing contracts.
- [ ] docs/ExecPlans/ui_certificate_import_configuration_execplan.md

## Progress

- [ ] (2026-08-09) Audit current behavior and add a failing focused test.
- [ ] (2026-08-09) Implement the smallest complete model/application/Qt path.
- [ ] (2026-08-09) Retire migrated compatibility or phase3 product cruft whose consumers are gone.
- [ ] (2026-08-09) Run focused, regression, and GUI validation; clean processes and artifacts.
- [ ] (2026-08-09) Update this plan and relevant docs, then commit.

## Surprises & Discoveries

- Observation: the current self-signed certificate builder uses a one-year validity period, so
  the five-year UI_SPEC recommendation is an explicit behavior change rather than a label-only
  adjustment.
  Evidence: src/foliaseal/application/certificate_manager.py:358-360.

## Decision Log

- Decision: obey SPEC.md, SCHEMAS.md, and UI_SPEC.md in that precedence order.
  Rationale: these are the repository's explicit authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep the slice limited to one user-visible certificate creation, export, remembered passwords, and deletion outcome.
  Rationale: narrow changes are independently testable and recoverable.
  Date/Author: 2026-08-09 / Codex

## Outcomes & Retrospective

Not started. Record the demonstrated behavior, evidence, and remaining gaps at completion.

## Context and Orientation

The relevant code is src/foliaseal/application/certificate_manager.py, certificate_secret_store.py,
certificate_storage.py, and the certificate dialogs. FoliaSeal is a Python/Qt Linux PDF signing
application. The
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

Implement the guided opinionated self-signed creation flow with fixed five-year validity, password confirmation, optional identity fields, encrypted .p12 backup export, secure remembered-password enable/disable, and deletion that keeps the file/configuration ownership rules explicit. Add or preserve typed application and public Qt-port boundaries rather than reaching
through private widgets. Keep schema and terminology aligned with the frozen documents. When a
legacy path is replaced, prove its callers are migrated before deleting it.
Keep remembered passwords exclusively in the secret store. If catalog fields change, add a
before/after serialized fixture and backward-read or deliberate rejection test; otherwise prove
existing catalog fixtures remain readable.

## Milestones

Milestone 1 audits the manager, secret store, and catalog transaction and adds failing validity and
password tests. Milestone 2 implements five-year creation, encrypted export, remembered-secret
toggle, and deletion through those authorities. Milestone 3 proves the GUI flow without leaking
secret material and records recovery evidence.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e 'create|export|password|delete' src/foliaseal/application/certificate_manager.py src/foliaseal/application/certificate_secret_store.py src/foliaseal/presentation/qt/app_frame_certificate_management.py
    .venv/bin/pytest -q tests/unit/test_certificate_manager.py tests/unit/test_secret_storage.py tests/unit/test_certificate_storage.py tests/unit/test_qt_app_frame_certificate_management.py
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

Acceptance is behavioral: A non-expert can create a local certificate, export an encrypted backup through Save As, optionally remember its password securely, disable that secret, and delete the configuration without accidental key loss. Focused tests must pass, shared-code changes must
leave the full suite green, and the GUI audit must record the visible result and cleanup.

## Required Acceptance Cases

Creation uses the fixed five-year recommended certificate flavor and exposes no algorithm/key-size
controls. Export is encrypted, never emits an unencrypted key or sidecar secret, reports the exact
successful path, and does not mutate managed state. Missing or rejected remembered secrets fall back
to a manual prompt; disabling the secret removes only the stored secret.

## Evidence Record

Before completion, record the exact manager/storage/Qt test command and result, the GUI creation,
export, remember/disable, and delete sequence, evidence path, secret-clearing and cleanup results,
serialized catalog compatibility result, and compatibility grep proof.

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
or workspace ports. The final behavior must be exercised by tests/unit/test_certificate_manager.py tests/unit/test_certificate_storage.py tests/unit/test_secret_storage.py and tests/unit/test_qt_app_frame_certificate_management.py. Any temporary adapter must
name its remaining consumer and retirement condition in this plan.

Revision note: 2026-08-09 / Codex
Created as a dependency-ordered child of the approved SPEC/UI_SPEC compliance breakdown.
