# Document close, dirty-draft, and recovery lifecycle

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can begin editing a signing draft and then use File > Open, File > Close,
or File > Exit without an accidental replacement or silent discard. A dirty draft is detected from
the user-owned signing values (placement, appearance/content, and an explicitly confirmed output
path); the frame asks whether to continue editing or discard it, and cancellation leaves the
current workspace mounted. The same decision is available to the native window-close event. This
slice is the first safe lifecycle seam for UI_SPEC WF01, WF05, section 16, and acceptance scenarios
6 and 7. Verified interrupted-signing artifact recovery is now supplied by the separate
transaction-journal and recovery-GUI children. This plan does not claim autosave or restoration of
an unsaved in-memory signing session across a process crash; that remains an explicit V1 exclusion.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are the frozen governing contracts.
- [x] docs/ExecPlans/ui_launch_no_document_execplan.md
- [x] docs/ExecPlans/ui_single_instance_open_routing_execplan.md
- [x] docs/ExecPlans/ui_signing_rail_stage_status_execplan.md
- [x] docs/ExecPlans/ui_document_source_change_recovery_execplan.md adds explicit source-change
  recovery while preserving this plan's dirty-draft and candidate lifecycle ownership.

## Progress

- [x] (2026-08-09) Audit the current implementation and identify the missing dirty-state and close-event seams; explorer report recorded below.
- [x] (2026-08-09) Add a red focused contract suite for dirty projection, discard, replacement cancellation, and native close routing; the pre-implementation run was `2 failed, 16 passed` and the focused contract is now green.
- [x] (2026-08-09) Implement the smallest complete workflow/typed-port/Qt frame path, including candidate prepare/commit ordering and action-specific consequence-verb decisions.
- [x] (2026-08-10) Historical source-change recovery increment without product-facing phase labels;
  the journal/recovery-GUI children later supplied verified artifact recovery, while unsaved-session
  autosave/restoration remains explicitly deferred.
- [x] (2026-08-10) Run focused, regression, and real offscreen Qt validation; display-backed GUI acceptance
  remains environment-blocked (`xcb`/`:0`) and stays explicitly open.
- [x] (2026-08-10) Update this plan and relevant architecture/status documentation; the source-change
  recovery child was committed in `0d5116084`.
- [x] (2026-08-16) Reconciled dependency markers and recovery wording against the completed
  transaction-journal and recovery-GUI children. Dirty-draft/source-change behavior remains owned
  here; verified artifact recovery is delegated to those children; unsaved-session autosave remains
  explicitly excluded.

## Surprises & Discoveries

- Observation: replacement and close decisions cross app-frame open routing, draft workflow, and
  lifecycle state; password clearing and recovery must be tested at each terminal transition.
  Evidence: the live source paths and focused tests listed below are the audit baseline.
- Observation: there is no recovery journal, close-event policy hook, or draft baseline in the
  current checkout, and the frame's output-path explicitness is private to the action bridge.
  Evidence: 2026-08-09 explorer review of `app_frame.py`, `signing_draft_workflow.py`,
  `signing_workspace_lifecycle.py`, and `signing_workspace_action_bridge.py`.
- Observation: prompting before composition could discard a dirty draft even when the replacement
  PDF was invalid. The lifecycle now exposes `prepare()` and `replace_prepared()` so candidate
  composition/validation happens first; a canceled decision disposes only the candidate.
  Evidence: `test_app_frame_failed_candidate_does_not_discard_dirty_workspace` and the lifecycle
  boundary implementation.
- Observation: the real QMessageBox can provide explicit `Continue editing`, `Discard draft`, and
  conditional `Sign and save` buttons; fake bindings use the existing question seam for deterministic
  unit coverage. Escape/window close maps to Continue editing.
  Evidence: `_ask_workspace_decision_with_custom_buttons()` and focused app-frame tests.

## Decision Log

- Decision: honor SPEC.md product scope, SCHEMAS.md persistent-object semantics, and UI_SPEC.md interaction wording in that order.
  Rationale: the repository explicitly defines those authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep this change limited to one observable document close, dirty-draft, and recovery lifecycle outcome.
  Rationale: narrow commits make GUI regressions and recovery auditable.
  Date/Author: 2026-08-09 / Codex
- Decision: implement the dirty-state and decision-policy seam first, and defer crash recovery.
  Rationale: no current transaction boundary exposes owned temporary/final artifacts, so a journal
  would either claim unsafe recovery or risk deleting unrelated files. A typed lifecycle seam makes
  the later journal additive and gives Open/Close/Exit correct behavior now.
  Date/Author: 2026-08-09 / Codex
- Decision: treat preset selection alone as clean; compare only placement, appearance/content, and
  explicit output-path confirmation in the draft baseline.
  Rationale: UI_SPEC describes reusable preset choice as a selection aid, while those three values
  are the user-authored signing draft that must be protected.
  Date/Author: 2026-08-09 / Codex
- Decision: compose an Open candidate before asking the dirty decision, then mount it only after the
  decision succeeds.
  Rationale: UI_SPEC requires candidate validation before replacing a document; disposing a dirty
  draft before a failed PDF load would silently lose the user's edits.
  Date/Author: 2026-08-09 / Codex
- Decision: use an explicit custom QMessageBox when the real Qt binding is available and retain a
  three-argument question fallback for existing fake bindings.
  Rationale: real users need consequence verbs and Continue editing as the default, while the
  fallback keeps headless tests deterministic without introducing a second policy.
  Date/Author: 2026-08-09 / Codex

## Outcomes & Retrospective

Implementation and focused validation are complete. The lifecycle-focused unit suite and source-change
child cover dirty-draft protection, candidate replacement, Reload/Locate/Ignore/Close, pending-open
handling, and secret clearing. The separate journal/recovery-GUI children now cover verified
interrupted-signing artifacts, including Open, Save copy as, Replace, and Discard. The latest recorded
full suite is green (`1535 passed, 20 skipped, 1 warning`); bounded launch/display acceptance remains
environment-limited. Unsaved in-memory session autosave/restoration is intentionally not part of V1.

## Context and Orientation

The relevant code is app_frame_workspace_open.py; signing_draft_workflow.py; signing_workspace lifecycle/close bridges; output/recovery policy tests. FoliaSeal is a Python/Qt Linux PDF signing application. The
product flow is open, review, select reusable setup, place one visible signature, preview
readiness, sign/save, verify, and reopen. This slice must preserve the V1 anti-goals: no tabs,
printing, general PDF editing, cloud workflow, broad trust administration, or multiple pending
signatures.

The words “compatibility surface” mean an adapter kept only for old callers. “acceptance” names identify
legacy evidence/harness infrastructure and must not appear in ordinary product-facing UI or new
primary contracts; production backend/evidence imports may be renamed only after a neutral migration
proves the old name is no longer required.

## Change Slice

Primary change class: behavior change. Allowed changes are the named implementation modules,
focused tests, bounded local evidence, and the minimum docs/status corrections needed to keep the
repository truthful. Do not mix unrelated architecture scans, V2 features, broad evidence
rebaselines, or packaging changes unless this slice explicitly requires them.

## Plan of Work

Implement a typed dirty-state projection on `SigningDraftWorkflow` and expose it through the
maintenance port of the workspace bundle. Add explicit `discard_draft()` and
`clear_session_secrets()` operations so the frame does not reach through child widgets. Route Open,
Close, Exit, and the native `QMainWindow.closeEvent` through one frame-owned policy that asks before
discarding a dirty draft; cancellation must preserve the active handle and mounted widget. Mark a
draft clean after successful signing. Preserve the public frame/workspace contract while migrating
consumers, then delete any old path only after focused tests prove no callers remain. Keep
user-facing terminology from UI_SPEC.md, not schema/backend names. Do not add a recovery journal in
this slice; create a follow-on plan when transaction-owned artifact paths are available.

## Milestones

Milestone 1 adds red tests for dirty projection, preset-only cleanliness, discard, replacement
cancellation, and native close routing. Milestone 2 wires lifecycle transitions through the frame,
typed workspace maintenance port, and draft workflow. Milestone 3 runs the full regression and
bounded GUI checks, records that secrets are cleared on the implemented discard/close path, and
documents the separately required recovery-journal follow-on.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e 'close|discard|recovery|password|dirty|unsaved' src/foliaseal/presentation/qt/app_frame.py src/foliaseal/application/signing_draft_workflow.py src/foliaseal/presentation/qt/signing_workspace_lifecycle.py src/foliaseal/presentation/qt/signing_workspace_action_bridge.py
    .venv/bin/pytest -q tests/unit/test_qt_app_frame.py tests/unit/test_signing_draft_workflow.py tests/unit/test_signing_workspace_lifecycle.py
    .venv/bin/ruff check src tests
    .venv/bin/pytest -q
    git diff --check

Run this bounded walkthrough from /home/daekar/FoliaSeal with an isolated configuration root:

    audit_root=$(mktemp -d /tmp/foliaseal-plan-audit-XXXXXX)
    timeout --foreground 30s env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf || test "$?" -eq 124
    ps -eo pid,cmd | rg 'FoliaSeal|foliaseal|PySide6|pytest' | rg -v 'rg ' || true
    rm -rf "$audit_root"
    test ! -e "$audit_root"

The implementation evidence is focused and offscreen Qt coverage plus the recorded bounded launch
limitation. A display-backed walkthrough remains a separate parent/release gate; an offscreen run
must not be described as human visual acceptance.

Historical validation evidence: an earlier `.venv/bin/pytest -q` completed with `1191 passed, 20
skipped, 1 warning`; lifecycle-focused tests completed with `75 passed`; the real offscreen
native-close test completed with `1 passed`; Ruff and `git diff --check` passed. Current repository
regression evidence is `1535 passed, 20 skipped, 1 warning` in the parent/recovery closeouts. The
offscreen CLI walkthrough exited `1` because the sandbox could not claim the local-instance socket;
the display-backed audit exited `134` because `xcb` could not connect to `DISPLAY=:0`. Both exact
temporary roots were removed and process inspection found no FoliaSeal/PySide6 processes. A
display-backed session remains an environment-dependent follow-on acceptance check.

## Validation and Acceptance

Acceptance is behavioral: Close/Open/Exit preserves a dirty draft when the user cancels, discards
only after explicit confirmation, and clears the in-memory passphrase on the confirmed discard/close
path. A successful sign marks the draft clean. Native window close uses the same policy. Verified
interrupted-signing artifacts are accepted only through the separate journal/recovery-GUI contracts;
unsaved in-memory crash restoration is not offered. Focused/full validation and cleanup must remain
green, while display-backed GUI acceptance is recorded separately.

## Required Acceptance Cases

Password-protected drafts prompt before replacement. Session password memory is cleared when the
confirmed discard/close path runs. Successful signing marks the draft clean. Certification and
ordinary-signature restrictions remain owned by the existing signing preflight. Unsaved-session
autosave/restoration is outside the V1 acceptance claim; verified artifact recovery and ownership-safe
cleanup are accepted by the dedicated recovery children.

## Evidence Record

Before completion, record agreement with `docs/ui/main-workspace-document-open-exploratory.svg`,
the exact lifecycle test command and result, dirty/preset/cancel/discard/native-close observations,
the in-memory password-clearing assertion, linked journal/recovery-GUI evidence, display-backed
availability or exact limitation, evidence path, cleanup, and compatibility grep proof. Do not
duplicate recovery-journal policy in this child.

Record the contributing UI_SPEC scenario ID(s) and either the owning SVG path or an explicit
"no SVG" decision alongside the evidence row.

Revision note: 2026-08-16 / Codex
Reconciled this child with the completed transaction-journal/recovery-GUI children and the parent’s
completed dependency markers. Verified artifact recovery is delegated to those plans; only unsaved
in-memory autosave/restoration remains excluded, and display-backed acceptance remains environment-
dependent.
Also record the exact focused test node and expected result (`N passed`); when the slice adds a new
contract, record that the test was red before implementation and green afterward.

## Idempotence and Recovery

Use temporary sibling outputs and isolated configuration for repeatable tests. If implementation
fails halfway, keep the source PDF and unsigned draft intact, terminate owned processes, remove only
this slice's generated artifacts, and update Progress with completed and remaining work. Re-running
the tests must not mutate user data or resurrect retired compatibility code. Because this slice does
not create a recovery journal, do not claim that a crash can be recovered.

## Artifacts and Notes

Record concise command output, focused screenshots/JSON under ignored artifacts/ when useful, and
the exact files changed. Do not commit generated PDFs, private keys, passwords, or machine-local
absolute paths.

## Interfaces and Dependencies

Use existing typed application workflows and public Qt ports rather than private child-widget
reach-through. Add `has_unsaved_changes()`, `discard_draft()`, and `clear_session_secrets()` to the
maintenance port and its Qt adapter. Add a frame-owned decision helper and a native close-event
adapter in `app_frame.py`. Exercise the final interface with `tests/unit/test_qt_app_frame.py`,
`tests/unit/test_signing_draft_workflow.py`, and `tests/unit/test_signing_workspace_lifecycle.py`;
add an integration recovery fixture only in the follow-on artifact-journal plan. Any compatibility
adapter retained temporarily must have a named consumer and a retirement condition recorded in this
plan.

Revision note: 2026-08-09 / Codex
Narrowed the original recovery/lifecycle proposal to the implementable dirty-state and close-policy
vertical slice after explorer review found no transaction-owned artifact boundary for safe crash
recovery. Added candidate prepare/commit ordering and UI_SPEC consequence-verb decisions after
compliance review found premature discard and generic prompting. Updated purpose, progress,
discoveries, decisions, milestones, validation, acceptance, evidence, and interfaces to prevent
overstating completion.
