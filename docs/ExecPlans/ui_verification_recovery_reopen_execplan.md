# Verification failure recovery, reopen, and later approval

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can understand verification results, recover preserved artifacts, reopen the document, and add a later approval in the real FoliaSeal GUI. It is mapped to SPEC primary story and UI_SPEC WF05/SUR06/section 16. The
slice is one vertical path through the relevant model, application workflow,
Qt surface, focused tests, and observable acceptance.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are frozen governing contracts.
- [x] docs/ExecPlans/ui_document_signatures_review_execplan.md, docs/ExecPlans/ui_atomic_sign_write_safety_execplan.md
  (their bounded implementations are committed; parent checkboxes are being reconciled separately)

## Progress

- [x] (2026-08-10) Audited the post-write verifier cleanup path, result projection, action coordinator,
  boundary, sidebar, and production composition. The staged artifact was deleted after verification
  failures and the GUI exposed only a generic error.
- [x] (2026-08-10) Added red focused coverage for preserved post-verification artifacts and typed
  recovery actions; the tests failed before the new result/state contract and pass after it.
- [x] (2026-08-10) Implemented the bounded application/Qt recovery path: failed post-write
  verification preserves an explicitly untrusted sibling, `SigningResult` carries its path, and
  the action rail exposes Verify again, Return to draft, and Open preserved copy.
- [x] (2026-08-10) Added a distinct untrusted-recovery workspace mode for Open preserved copy.
  Its reopen callback carries recovery context, the new workspace blocks Sign and save, and the
  rail keeps Verify again as the recommended action until explicit verification succeeds. The
  original preserved file remains app-owned until Return to draft cleanup.
- [x] (2026-08-10) Added the bounded permission-aware reopen gate: a preserved workspace remains
  non-signable until Verify again proves every signature and the summary reports no certification
  restriction (or an allowed `fill_forms`/`annotate` DocMDP permission). Known restrictions and
  uncertain/unknown trust remain blocked with the recovery warning.
- [x] (2026-08-10) Reviewed compatibility and phase3 product cruft. No safe retirement condition
  was met; historical evidence names remain external contracts and no new product-facing phase3
  nomenclature was introduced.
- [x] (2026-08-10) Ran focused, regression, and GUI validation; clean processes and artifacts
  (historical closeout at that revision): the recovery/app-frame/sidebar/document-review command
  was `52 passed`; the full suite was `1440 passed, 20 skipped, 1 warning`; backend/recovery
  coverage remained green; Ruff and
  diff checks clean. The
  bounded offscreen app launch exits at `SingleInstanceUnavailable`, leaves no matching processes,
  and removes its temporary configuration root. Lifecycle disposal now also removes an app-owned
  preserved artifact when the recovery workspace is discarded or replaced, and a `try/finally`
  guard releases the view even if cleanup itself raises.
- [x] (2026-08-10) Updated this plan, the parent plan, and `docs/ARCHITECTURE.md`; independent
  review findings were addressed for strict validity, required timestamp/trust, every-signature
  verification, explicit artifact cleanup, and the distinct untrusted reopen/permission gate.
  Display-backed recovery acceptance remains environment-blocked by `SingleInstanceUnavailable`.
- [x] (2026-08-10) Committed the completed recovery closeout and recorded the remaining
  dependency-ordered blockers as `6370e3f0b`.
- [x] (2026-08-10) Reconciled the rail-facing recovery vocabulary with UI_SPEC §11: a preserved
  `POST_VERIFY_FAILED` result is rendered as `Saved but not verified`, while the artifact remains
  untrusted and the recovery actions remain the only truthful next steps until verification succeeds.

## Surprises & Discoveries

- Observation: verification, document review, and workspace reopening are separate seams; this
  child must preserve the original draft on failure and verify every existing signature before
  reopening for another approval.
  Evidence: the live source paths and focused tests listed below are the audit baseline.

## Decision Log

- Decision: obey SPEC.md, SCHEMAS.md, and UI_SPEC.md in that precedence order.
  Rationale: these are the repository's explicit authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep the slice limited to one user-visible verification failure recovery, reopen, and later approval outcome.
  Rationale: narrow changes are independently testable and recoverable.
  Date/Author: 2026-08-09 / Codex
- Decision: preserve only artifacts produced after the write boundary and label them explicitly
  untrusted; pre-write failures and successful replacement continue to remove owned temporary files.
  Rationale: recovery needs bytes for Verify again/Open preserved copy without weakening the guarantee
  that an unverified artifact is never reported as the signed output.
  Date/Author: 2026-08-10 / Codex
- Decision: explicit Return to draft is the cleanup boundary for a preserved artifact; Verify again
  retains it for further inspection, and Open preserved copy never promotes or replaces the requested
  destination.
  Rationale: recovery files are app-owned but must remain available across the user's recovery
  choices without becoming indefinite orphaned temporary files.
  Date/Author: 2026-08-10 / Codex
- Decision: Verify again requires an explicit cryptographically-valid summary, required timestamp,
  and required timestamp trust; the backend validates every embedded signature before returning
  that summary.
  Rationale: a non-raising verifier result or a valid newest signature must not make an older or
  trust-incomplete artifact appear safe for later approval.
  Date/Author: 2026-08-10 / Codex
- Decision: Open preserved copy uses a distinct recovery reopen intent and mounts an untrusted
  workspace that cannot sign until recovery verification succeeds.
  Rationale: routing through the ordinary verified-output callback would lose the warning state and
  allow an unverified artifact to look like a normal signing source.
  Date/Author: 2026-08-10 / Codex
- Decision: only an explicitly verified artifact with a non-restrictive/allowed DocMDP projection
  re-enables Sign and save in a recovery workspace; unknown or restricted permission remains blocked.
  Rationale: later approval must never be enabled by a generic successful open or an ambiguous
  certification result.
  Date/Author: 2026-08-10 / Codex

## Outcomes & Retrospective

The bounded recovery path now preserves post-write verification failures and projects the normative
`Saved but not verified` rail state with typed retry, return, and preserved-copy actions. Verification retry interprets structured
cryptographic validity, every-signature coverage, required timestamp, and required timestamp trust;
it remains read-only and never promotes the preserved artifact to `last_successful_output_path`.
Explicit Return to draft removes only the app-owned preserved file. The bounded later-approval
permission gate is implemented and this child is closed; broader document-reopen policy and
display-backed acceptance remain explicit follow-up/environment gates.

## Context and Orientation

The relevant code is document_review.py; signing_workspace_review_bridge.py; signing_completion.py; app-frame reopen/open flow; verification surfaces. FoliaSeal is a Python/Qt Linux PDF signing application. The
primary flow is open, review, select reusable setup, place one visible signature, preview
readiness, sign/save, verify, and reopen. V1 excludes tabs, printing, broad PDF editing, cloud
workflow, enterprise trust administration, and multiple pending signatures.

A compatibility surface is an adapter retained only for old callers. “phase3” names identify legacy
evidence/harness infrastructure and must not be introduced into ordinary product UI or new primary
contracts; production backend/evidence imports may be renamed only after a neutral migration proves
the old name is no longer required.

## Change Slice

Primary change class: behavior change. Allowed changes are the named modules, focused tests, bounded
ignored local evidence, and the minimum truthful status documentation. Package construction and
installed-package evidence belong only to ui_product_support_and_release_execplan.md.

## Plan of Work

Render successful local verification as a terminal signed state with clear reopen guidance. On post-write verification failure preserve the artifact and offer Verify again, Return to draft, Open preserved copy, and technical details. Reopening must permit another approval only when permissions allow and must explain invalid/changed/unverifiable signatures plainly. Use typed application contracts and public Qt ports, not private child-widget reach-through.
Keep persistent objects and secrets within the schemas/storage rules. Retire obsolete compatibility
paths only after proving their consumers migrated, and record every retirement in the Decision Log.

## Milestones

Milestone 1 adds verification/reopen fixtures including every existing signature and failure modes.
Milestone 2 wires recovery actions and reopen/add-approval behavior after successful verification.
Milestone 3 proves failed and successful paths in the GUI and records cleanup.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e 'verify|reopen|recovery|signature|permission' src/foliaseal/application/document_review.py src/foliaseal/application/signing_completion.py src/foliaseal/presentation/qt/app_frame_workspace_open.py
    .venv/bin/pytest -q tests/unit/test_signing_completion.py tests/unit/test_document_review.py tests/unit/test_document_review_workspace.py tests/unit/test_qt_app_frame_workspace_open.py tests/unit/test_qt_signing_action_coordinator.py tests/unit/test_signing_workspace_sidebar.py
    .venv/bin/ruff check src tests
    .venv/bin/pytest -q
    git diff --check

Run this bounded walkthrough from /home/daekar/FoliaSeal with an isolated configuration root:

    audit_root=$(mktemp -d /tmp/foliaseal-plan-audit-XXXXXX)
    timeout --foreground 30s env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf || test "$?" -eq 124
    ps -eo pid,cmd | rg 'FoliaSeal|foliaseal|PySide6|pytest|build_deb|build_pyinstaller' | rg -v 'rg ' || true
    rm -rf "$audit_root"
    test ! -e "$audit_root"

Expected evidence is the stated user-visible behavior plus a mandatory Qt-test or display-backed
walkthrough. Record recovery inputs, observed verification/reopen state, evidence path, and cleanup
result; the bounded timeout is only a lifecycle check. Package evidence belongs only to the final
release plan.

## Validation and Acceptance

Acceptance is behavioral: A user can sign, reopen the output, inspect the verification result, and add another approval when allowed; failed verification never presents the artifact as safe or destroys the original. Focused tests and the full suite must pass; the
final acceptance record must distinguish headless evidence from real Qt interaction and must include
cleanup evidence.

## Required Acceptance Cases

Post-write verification failure says the artifact must not yet be relied upon and offers Verify again,
Return to draft, Open preserved copy, and technical details. Successful verified signing is terminal for
the workspace; reopening the signed output exposes later approval signing only when permissions allow.

## Evidence Record

Before completion, record the exact verification/reopen test command and result, successful and
failed GUI recovery sequences, every-signature verification observation, evidence path, cleanup,
and compatibility grep proof.

Record the contributing UI_SPEC scenario ID(s) and either the owning SVG path or an explicit
"no SVG" decision alongside the evidence row.
Also record the exact focused test node and expected result (`N passed`); when the slice adds a new
contract, record that the test was red before implementation and green afterward.

## Idempotence and Recovery

Use temporary configuration, sibling output, and disposable package-install roots. If a build or GUI
audit fails, retain source data, update Progress, clean owned processes/artifacts, and retry from
the recorded state. Never delete unrelated temporary files or private material.

## Artifacts and Notes

Record exact package name/path, launch command, help output, accessibility observations, and concise
acceptance evidence. Do not commit generated packages, private keys, passwords, or machine-local
absolute paths unless the repository explicitly requires a fixture.

## Interfaces and Dependencies

Use AppSettings, the public Qt frame/workspace ports, packaged Markdown help, the CLI parser in
src/foliaseal/__main__.py, and build helpers under src/foliaseal/build/. The final behavior must be
exercised by tests/unit/test_sign_pdf_use_case.py, tests/unit/test_qt_signing_action_coordinator.py,
tests/unit/test_signing_workspace_sidebar.py, tests/unit/test_signing_completion.py,
tests/unit/test_document_review.py, tests/unit/test_document_review_workspace.py, and
tests/unit/test_qt_app_frame_workspace_open.py. A dedicated integration test node is not present in
this checkout; the offscreen launch audit remains a bounded lifecycle check and is recorded as
environment-limited.
New help/diagnostic surfaces must not expose secrets, PDF contents, selected
text, Reason, Location, or private keys.

Revision note: 2026-08-10 / Codex
Implemented and validated the bounded preserved-artifact recovery vertical slice after the live
audit and red tests; updated dependencies and the architecture boundary. The isolated GUI launch
still stops before frame creation at `SingleInstanceUnavailable`; no process or temporary-config
debris remains. Independent review and commit completed in the closeout below.
Revision note: 2026-08-10 / Codex
Closed the recovery child after reconciling the parent and architecture docs. Historical focused
recovery/app-frame/sidebar/document-review evidence is `52 passed`; the full suite at that revision
was `1440 passed, 20 skipped, 1 warning`; the bounded GUI launch remains environment-limited by
`SingleInstanceUnavailable`, with owned processes and temporary roots cleaned up. The closeout is
committed as `6370e3f0b`.
