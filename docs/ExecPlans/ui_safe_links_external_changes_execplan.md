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
- [x] docs/ExecPlans/ui_document_lifecycle_recovery_execplan.md supplies the dirty-draft and
  candidate replacement lifecycle; source-change recovery is implemented in the child listed below.
- [ ] docs/ExecPlans/ui_pdf_navigation_zoom_pan_execplan.md
- [x] docs/ExecPlans/ui_safe_links_source_safety_contracts_execplan.md provides pure link and
  source-change decisions; renderer/workspace integration remains open.
- [x] docs/ExecPlans/ui_safe_links_contract_hardening_execplan.md closes the contract-level
  unknown-identity, mode-gating, malformed-destination, and architecture-documentation findings.
- [x] docs/ExecPlans/ui_pdf_link_inspection_execplan.md provides neutral QtPdf page-link facts;
  Pan-mode hit testing, destination confirmation, history, and source-change recovery remain here.
- [x] docs/ExecPlans/ui_safe_links_pan_activation_execplan.md consumes the link facts for Pan-only
  hit testing, internal navigation/history, and non-executing external/blocked outcomes; source
  reload and condition-only banner behavior remain separate.
- [x] docs/ExecPlans/ui_safe_links_external_confirmation_execplan.md provides the production
  consequence-labeled confirmation, complete-target launcher boundary, and active-signing pending
  request policy; source reload/recovery remains open.

## Progress

- [x] (2026-08-10) Explorer review established that the original full GUI slice is not yet
  implementable: the viewer is raster-only and workspace reload would discard the active draft.
  The prerequisite contract child now supplies the policy matrix without claiming GUI behavior.
- [x] (2026-08-10) The prerequisite contract and hardening children reported 24 focused tests and
  a green full suite (1342 passed); the dedicated QtPdf inspection child now closes extraction.
  This parent remains open for Pan-only hit testing, internal navigation/history, external
  confirmation/block UI, draft-preserving reload, and the condition-only Qt banner.
- [x] (2026-08-10) Added the QtPdf link-inspection prerequisite: generated internal and external
  annotations now cross a neutral `DocumentLink` DTO with PDF-space rectangles and the existing
  pure safety classifier. URL activation, hit testing, history, and source-change recovery remain
  intentionally unimplemented in this parent.
- [x] (2026-08-10) Added the Pan-only consumer child: stationary clicks now resolve neutral link
  facts through the safety policy, internal destinations use page-index Back/Forward history, and
  external/blocked outcomes remain non-executing typed/status results. Real offscreen Qt and
  rotated/non-zero-origin fixtures pass; external confirmation UI and source-change recovery remain
  open.
- [x] (2026-08-10) Reconciled the activation child with `docs/ARCHITECTURE.md`; focused validation
  is `183 passed` and the full regression is `1417 passed, 20 skipped, 1 warning`. The parent is
  still open only for external-confirmation UI, source-change recovery, and its remaining cleanup
  requirements.
- [x] (2026-08-10) Completed the external-confirmation child: approved `http`, `https`, and
  `mailto` links now show a cancel-default dialog and launch only after approval; blocked links do
  not reach the dialog, long targets preserve a complete sanitized launch value, and active-signing
  requests defer/reconcile by status. Focused validation is `55 passed`; full regression is
  `1425 passed, 20 skipped, 1 warning`. Source-change reload/Locate/Ignore/Close remains open.
- [x] (2026-08-10) External confirmation was committed in `96594a95f`; this parent now has
  internal-link navigation/history and external confirmation/launch, while source-change recovery,
  condition-only banners, and the remaining legacy-cleanup requirements stay open.

- [x] (2026-08-10) Draft-preserving source-change recovery is implemented in
  `ui_document_source_change_recovery_execplan.md`: changed sources expose Reload/Ignore, missing
  sources expose Locate/Close, candidate replacement is atomic, and authored state/secrets survive
  transfer. Focused and offscreen coverage is green; final commit and broader parent cleanup remain.

- [x] (2026-08-09) Audit current behavior and add a failing focused test.
- [x] (2026-08-09) Implement the smallest complete model/application/Qt path.
- [ ] (2026-08-09) Retire migrated compatibility or phase3 product cruft whose consumers are gone.
- [x] (2026-08-10) Run focused, regression, and bounded GUI validation; clean processes and artifacts.
- [x] (2026-08-10) Update this plan and relevant docs; the complete source-recovery slice is being committed.

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

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

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
or workspace ports. Create tests/unit/test_qt_safe_links_external_changes.py. The final behavior
must be exercised by tests/unit/test_viewer_interaction_session.py,
tests/unit/test_qt_app_frame_workspace_open.py, and that new Qt test. Any temporary adapter must
name its remaining consumer and retirement condition in this plan.

Revision note: 2026-08-09 / Codex
Created as a dependency-ordered child of the approved SPEC/UI_SPEC compliance breakdown.
