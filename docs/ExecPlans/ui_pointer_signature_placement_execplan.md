# Pointer-driven signature placement

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can enter Place mode and position one visible signature with the pointer in the real FoliaSeal GUI. It is mapped to UI_SPEC section 8 and acceptance scenario 3. The
slice is one vertical path through the relevant persistent model,
application workflow, Qt surface, focused tests, and observable acceptance.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are frozen governing contracts.
- [x] docs/ExecPlans/ui_pdf_navigation_zoom_pan_execplan.md (implemented; display-backed acceptance remains environment-limited)
- [x] docs/ExecPlans/ui_first_use_preset_setup_execplan.md (bounded setup path implemented)
- [x] docs/ExecPlans/ui_certificate_selection_readiness_execplan.md (bounded readiness path implemented)

## Progress

- [x] (2026-08-10) Audited the existing pointer path and added a failing focused Escape-cancellation
  contract; drag already crossed the typed viewer/session/workspace bridge.
- [x] (2026-08-10) Implemented cancellation for unfinished placement and overlay-resize drags without
  mutating the completed draft overlay; a completed pointer drag remains persistent across refreshes
  and mode changes.
- [x] (2026-08-10) Reviewed compatibility and phase3 product cruft; no migrated consumer retirement
  condition was proven in this narrow viewer edge, and no new phase3 nomenclature was introduced.
- [x] (2026-08-10) Focused viewer/interaction and offscreen pointer integration validation passed
  (`40 passed`); the full suite passed (`1296 passed, 20 skipped, 1 warning`), with GUI audit,
  docs, and commit gates remaining.
- [x] (2026-08-10) Added explicit mutually exclusive Pan and Place viewer tools at the production
  toolbar and public session boundary; Pan is the production default, consumes left-drag as panning,
  Place consumes pointer rectangles/handles, and completed overlays persist across mode switches.
  Focused shell/viewer/composition/integration validation is `156 passed`; full-suite validation is
  `1297 passed, 20 skipped, 1 warning`; final GUI audit, documentation reconciliation, and commit
  remain.
- [x] (2026-08-10) Reconciled the completed pointer contract with the later placement increments:
  pointer-only page-guide snapping, Alt bypass, rendered guides, and explicit off-page indicators
  now live in the coordinate/viewer seams. Current full-suite evidence is `1314 passed, 20 skipped,
  1 warning`; the bounded GUI launch remains limited only by the isolated single-instance endpoint,
  with cleanup confirmed.

## Surprises & Discoveries

- Observation: pointer placement crosses viewer interaction and signing-draft state; the drag path
  must remain page-local and must not bypass the application placement contract.
  Evidence: the live source paths and focused tests listed below are the audit baseline.

## Decision Log

- Decision: obey SPEC.md, SCHEMAS.md, and UI_SPEC.md in that precedence order.
  Rationale: these are the repository's explicit authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep the slice limited to one user-visible pointer-driven signature placement outcome.
  Rationale: narrow changes are independently testable and recoverable.
  Date/Author: 2026-08-09 / Codex

## Outcomes & Retrospective

The bounded pointer path and explicit Pan/Place mode topology are implemented through the current
viewer/session/composition seams. Pointer snap/guides and off-page indicators are implemented by
the later placement child; keyboard/numeric history remains owned by that child rather than this
pointer-specific contract.

## Context and Orientation

The relevant code is presentation/qt/viewer_widget.py; viewer interaction/session; signing workspace interaction bridge; coordinate transforms. FoliaSeal is a Python/Qt Linux PDF signing application. The
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

Make Place Signature a mutually exclusive mode that creates no object on entry, creates a rectangle only after a pointer drag, keeps completed placement visible in every mode, uses visible-page coordinates, and provides handles only while placing. A click alone must not create a signature. Add or preserve typed application and public Qt-port boundaries rather than reaching
through private widgets. Keep schema and terminology aligned with the frozen documents. When a
legacy path is replaced, prove its callers are migrated before deleting it.

## Milestones

Milestone 1 tests pointer coordinate conversion and page-local bounds. Milestone 2 wires drag/drop
placement through the application draft and public viewer port. Milestone 3 proves pointer placement
and undo/recovery in the GUI and records cleanup.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e 'interaction_mode|signature|mouse|drag|overlay' src/foliaseal/presentation/qt/viewer_widget.py src/foliaseal/application/viewer_interaction_session.py
    .venv/bin/pytest -q tests/unit/test_qt_viewer_widget.py tests/unit/test_viewer_interaction_session.py
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

Acceptance is behavioral: A pointer user can enter Place mode, drag one visible rectangle on the current page, adjust it, leave the mode without losing it, and remove it explicitly. Focused tests must pass, shared-code changes must
leave the full suite green, and the GUI audit must record the visible result and cleanup.

## Evidence Record

Before checking this child in the parent, record the governing UI_SPEC requirement, exact focused
test command/result, Place-mode pointer sequence and observed page-local rectangle, evidence path and
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
or workspace ports. Create tests/integration/test_pointer_signature_placement.py for the pointer
walkthrough. The final behavior must be exercised by tests/unit/test_qt_viewer_widget.py,
tests/unit/test_viewer_interaction_session.py, and that integration test. Any temporary adapter must
name its remaining consumer and retirement condition in this plan.

Revision note: 2026-08-10 / Codex
Completed the bounded pointer-placement cancellation increment after auditing the existing drag →
page-local rectangle → typed workspace bridge. Broader mode-group and keyboard-placement behavior
remains explicitly open; full validation, GUI audit, documentation reconciliation, and commit are
the remaining gates.
