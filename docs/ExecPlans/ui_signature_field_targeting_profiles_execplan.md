# Existing unsigned fields and placement-profile mismatch handling

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can target an unsigned field and understand exact Placement-profile mismatches in the real FoliaSeal GUI. It is mapped to UI_SPEC WF02, section 10, SUR06, and acceptance scenario 4. The
slice is one vertical path through the relevant persistent model,
application workflow, Qt surface, focused tests, and observable acceptance.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are frozen governing contracts.
- [x] docs/ExecPlans/ui_document_signatures_review_execplan.md
- [x] docs/ExecPlans/ui_first_use_preset_setup_execplan.md
- [x] docs/ExecPlans/ui_pointer_signature_placement_execplan.md

## Progress

- [x] (2026-08-10) Audited current behavior and added red-to-green focused tests for workflow,
  backend request propagation, existing-field signing, and the review surface.
- [x] (2026-08-10) Implemented the typed field-target path: Document Signatures exposes Use for
  new signature, the draft carries the field name, and pyHanko fills the existing field only.
- [x] (2026-08-10) Locked targeted page/geometry controls and rejected mismatched placement-profile
  dimensions with an explicit Use/adjust/place-manually explanation; no compatibility path was
  added and no obsolete product-facing acceptance label was introduced.
- [x] (2026-08-10) Ran focused tests, full suite (1318 passed, 20 skipped, 1 warning), Ruff, diff
  check, and bounded offscreen GUI lifecycle validation; the isolated single-instance socket
  limitation remained, with no FoliaSeal/python processes or temporary audit root left behind.
- [x] (2026-08-10) Reconciled this plan and the parent plan; implementation committed as the
  field-targeting tranche.

## Surprises & Discoveries

- Observation: field targeting combines document-review state with reusable placement profiles;
  this child must reject page/field mismatches before a signing request is built.
  Evidence: the live source paths and focused tests listed below are the audit baseline.

## Decision Log

- Decision: obey SPEC.md, SCHEMAS.md, and UI_SPEC.md in that precedence order.
  Rationale: these are the repository's explicit authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep the slice limited to one user-visible existing unsigned fields and placement-profile mismatch handling outcome.
  Rationale: narrow changes are independently testable and recoverable.
  Date/Author: 2026-08-09 / Codex

## Outcomes & Retrospective

The Document Signatures dialog now enables Use for new signature only for an unsigned field with
known page geometry. Selecting it carries the exact field name and discovered rectangle through
the draft and signing request; pyHanko signs that existing field with `existing_fields_only=True`.
Targeted page/left/bottom/width/height controls are disabled, and a placement profile with a
different width or height is rejected with an explicit manual-resolution message. Unsigned fields
without geometry remain review-only and direct the user to Place manually. The bounded GUI launch
still cannot claim an isolated local socket in this environment (`SingleInstanceUnavailable`), but
the Qt integration test and backend fixture demonstrate the behavior and cleanup is clean.

## Context and Orientation

The relevant code is document review/signature-field models; signing setup/session; placement profile application; signing rail commands. FoliaSeal is a Python/Qt Linux PDF signing application. The
primary flow is open, review, select reusable setup, place one visible signature, preview
readiness, sign/save, verify, and reopen. V1 excludes tabs, printing, broad PDF editing, cloud
workflow, enterprise trust administration, and multiple pending signatures.

A compatibility surface is an adapter retained only for old callers. “acceptance” names identify legacy
evidence/harness infrastructure and must not be introduced into ordinary product UI or new primary
contracts; production backend/evidence imports may be renamed only after a neutral migration proves
the old name is no longer required.

## Change Slice

Primary change class: behavior change. Allowed changes are the named modules, focused tests,
bounded ignored local evidence, and minimum truthful documentation. Do not mix unrelated evidence
rebaselines, V2 features, or packaging work.

## Plan of Work

Expose explicit Use for new signature for eligible visible unsigned fields, keep selected fields fixed and non-resizable, explain ineligible fields, and implement exact profile application with fixed-page/geometry compatibility proposals. Missing pages navigate for orientation without creating a placement. Add or preserve typed application and public Qt-port boundaries rather than reaching
through private widgets. Keep schema and terminology aligned with the frozen documents. When a
legacy path is replaced, prove its callers are migrated before deleting it.

## Milestones

Milestone 1 tests field discovery, page mismatch, and profile resolution. Milestone 2 wires field
selection to the signing draft without bypassing placement validation. Milestone 3 proves targeting
and rejection paths in the GUI and records cleanup.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e 'field|placement|mismatch|current_page' src/foliaseal/application/document_review.py src/foliaseal/application/signing_setup_session.py src/foliaseal/application/reusable_signing_models.py
    .venv/bin/pytest -q tests/unit/test_document_review.py tests/unit/test_signing_setup_session.py tests/unit/test_reusable_signing_models.py
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
walkthrough. Record field/profile inputs, observed mismatch action, evidence path, and cleanup
result; the bounded timeout is only a lifecycle check.

## Validation and Acceptance

Acceptance is behavioral: A user can target an eligible existing field only through an explicit command; incompatible or missing placement profiles offer Use, Adjust, or Place manually and never auto-scale, clamp, or move. Focused tests must pass, shared-code changes must
leave the full suite green, and the GUI audit must record the visible result and cleanup.

## Evidence Record

Before checking this child in the parent, record the governing UI_SPEC requirement, exact focused
test command/result, field/profile input sequence and observed mismatch action, evidence path and
cleanup result, and compatibility grep proof.

Record the contributing UI_SPEC scenario ID(s) and either the owning SVG path or an explicit
"no SVG" decision alongside the evidence row.
Also record the exact focused test node and expected result (`N passed`); when the slice adds a new
contract, record that the test was red before implementation and green afterward.

Evidence: UI_SPEC WF02, section 10, SUR06, acceptance scenario 4. Focused workflow/use-case/review
tests and `tests/unit/test_signing_backend.py::test_pyhanko_signer_fills_existing_visible_signature_field`
are green; the full command `.venv/bin/pytest -q` reports 1318 passed, 20 skipped, 1 warning.
The backend fixture used field `Approval` at page 0, `(24,36)-(584,216)` and filled that existing
field without creating another one. The mismatch test used a 220x80 profile against a 180x54
target and observed the explicit rejection. No SVG was added: existing document-review and
placement overlays are the owning visual realization. The bounded GUI command exited with the
known isolated `SingleInstanceUnavailable` socket limitation; the audit root and processes were
cleaned. The new contract is typed through `SigningRequest`, `SigningBackendRequest`,
`SigningWorkspaceSessionPort`, and the Qt dialog callback; no legacy adapter was retained solely
for this slice.

## Idempotence and Recovery

Use temporary configuration and sibling output paths. If work fails halfway, preserve user PDFs and
drafts, update Progress with completed/remaining work, clean owned processes and artifacts, and
retry from the recorded state. Do not resurrect removed compatibility paths.

## Artifacts and Notes

Record concise output, focused screenshots or JSON under ignored artifacts/when useful, and exact
changed files. Never commit private keys, passwords, generated PDFs, or machine-local absolute paths.

## Interfaces and Dependencies

Use the existing typed application workflows, schema models, persistence stores, and public Qt frame
or workspace ports. The final behavior must be exercised by tests/unit/test_document_review.py tests/unit/test_signing_setup_session.py and field/profile Qt tests. Any temporary adapter must
name its remaining consumer and retirement condition in this plan.

Revision note: 2026-08-09 / Codex
Created as a dependency-ordered child of the approved SPEC/UI_SPEC compliance breakdown.
