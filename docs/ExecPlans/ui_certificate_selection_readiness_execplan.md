# Per-document certificate selection and certificate readiness

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can select a Certificate for the current document and understand whether signing is ready, blocked, or caveated in the real FoliaSeal GUI. It is mapped to SPEC goals 6–7 and UI_SPEC sections 3, 11, and 15. The
slice is one vertical path through the relevant persistent model,
application workflow, Qt surface, focused tests, and observable acceptance.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are frozen governing contracts.
- [ ] docs/ExecPlans/ui_signing_rail_stage_status_execplan.md
- [ ] docs/ExecPlans/ui_first_use_preset_setup_execplan.md
- [ ] docs/ExecPlans/ui_certificate_import_configuration_execplan.md
- [ ] docs/ExecPlans/ui_certificate_create_export_password_execplan.md

## Progress

- [x] (2026-08-10) Audited the live catalog-backed rail, resolver, workflow preview, and Qt
  controls. Added focused contracts for ready/self-signed, expiry warning, expired/not-yet-valid,
  missing-file, missing-private-key, password-promptable, and no-selection outcomes. A separate
  pre-implementation red run was not captured; the contract tests are recorded as green below.
- [x] (2026-08-10) Implemented `certificate_readiness.py` as a typed application projection and
  connected it through `SignaturePropertiesViewState` to the certificate helper label and signing
  readiness gate. The catalog-backed GUI now evaluates the selected PKCS#12 file, private key,
  validity window, and self-signed caveat without exposing secrets; direct headless callers with
  explicit material retain their existing boundary.
- [x] (2026-08-10) Reviewed compatibility and phase3 product cruft. This slice adds no phase3
  nomenclature or compatibility wrapper; existing evidence names remain because their external
  CLI/fixture contracts still have consumers. No safe retirement condition was met here.
- [x] (2026-08-10) Ran focused application/Qt tests, Ruff, the full suite, and a bounded offscreen
  launch attempt. The final focused readiness/coordinator/session/shell command reports 162 passed;
  Ruff and `git diff --check` are clean; the full suite reports 1256 passed, 20 skipped, and one
  existing Pillow deprecation warning. The offscreen CLI still exits before frame creation with the
  known isolated `SingleInstanceUnavailable` transport limit. Temporary configuration roots and
  processes were cleaned.
- [x] (2026-08-10) Updated this plan, the parent progress record, and `docs/ARCHITECTURE.md`; the
  implementation is ready for the commit gate and the remaining dependency gaps are recorded below.

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

The catalog-backed signing rail now has one typed readiness projection. Empty selection explains
the next action, selected valid material reports identity/validity and the exact neutral
self-signed caveat, expiry within 30 days warns without disabling signing, and expired,
not-yet-valid, missing-file, invalid, or missing-private-key material blocks with a corrective
action. Password entry remains promptable and is not treated as a durable readiness failure.

This is a bounded readiness increment, not completion of the certificate corpus. Retained
unconfigured-file rows, import inspection/configuration, create/export/password-management, and
the full signing-rail stage machine remain in their owning ExecPlans. The direct-material fallback
exists only for headless/evidence callers and is not used by the catalog-backed app-frame path.

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

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e 'certificate|ready|expired|password' src/foliaseal/presentation/qt/signing_workspace_properties_panel.py src/foliaseal/application/signing_setup_session.py src/foliaseal/application/signing_material_resolver.py
    .venv/bin/pytest -q tests/unit/test_certificate_readiness.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py tests/unit/test_qt_signing_shell.py
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
cleanup result; the bounded timeout is only a lifecycle check. In this slice the display-backed
walkthrough was unavailable, so the real Qt fake-binding acceptance test is the authoritative
visible-state evidence and the offscreen launch limitation is recorded rather than overstated.

## Validation and Acceptance

Acceptance is behavioral: A partial preset clearly requests an explicit certificate; selecting one updates readiness and identity preview; expired or missing-key entries block with one next action while self-signed/local trust remains nonblocking. Focused tests must pass, shared-code changes must
leave the full suite green, and the GUI audit must record the visible result and cleanup.

## Required Acceptance Cases

Readiness warns but permits expiry within 30 days, blocks expired/not-yet-valid/missing-file/missing-key
states, prompts for a missing password, and uses the exact local/self-signed caveat from UI_SPEC.md.
Selecting a partial preset never carries a certificate from another document.

## Evidence Record Requirements

Before completion, record the exact resolver/coordinator test command and result, the GUI selection
sequence and ready/warning/blocked observations, evidence path, cleanup, and compatibility grep proof.

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
or workspace ports. The final behavior must be exercised by tests/unit/test_signing_setup_session.py tests/unit/test_signing_material_resolver.py tests/unit/test_qt_signing_shell.py. Any temporary adapter must
name its remaining consumer and retirement condition in this plan.

## Evidence Record

- Focused contract/coordinator/Qt command: `.venv/bin/pytest -q
  tests/unit/test_certificate_readiness.py tests/unit/test_signature_properties_coordinator.py
  tests/unit/test_signing_setup_session.py tests/unit/test_qt_signing_shell.py` — 162 passed in
  9.22s after the final visible-state test was added.
- Repository validation: `.venv/bin/ruff check src tests`, `git diff --check`, and `.venv/bin/pytest
  -q` — Ruff/diff clean; 1256 passed, 20 skipped, one existing Pillow deprecation warning in
  48.12s.
- Visible sequence: open a catalog-backed workspace with no selected certificate (helper reads
  `Select a certificate configuration before signing.`); choose `Corporate Records Signing`, enter
  the password, and observe `Self-signed certificate — ready for local signing` plus the neutral
  local-trust caveat in the certificate helper. Expiry and blocking states are covered by the
  application reader contract tests.
- GUI evidence path: `tests/unit/test_qt_signing_shell.py::test_signing_shell_renders_certificate_readiness_detail`;
  no screenshot/SVG was added because this is an existing certificate-group surface, not a new
  topology. The bounded command exited `1` with `SingleInstanceUnavailable` before frame creation;
  its isolated root was removed and no FoliaSeal/PySide6/pytest processes remained after validation.
- Compatibility proof: no new `phase3` imports or product-facing labels were introduced; existing
  phase3 evidence modules remain outside this product readiness boundary.

Revision note: 2026-08-10 / Codex
Implemented the typed catalog-backed readiness projection and Qt helper-state slice.

Revision note: 2026-08-09 / Codex
Created as a dependency-ordered child of the approved SPEC/UI_SPEC compliance breakdown.
