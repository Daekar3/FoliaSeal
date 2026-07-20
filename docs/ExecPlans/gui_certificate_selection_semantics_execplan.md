# GUI certificate-selection semantics cleanup

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this change, a user will understand exactly how a saved certificate configuration becomes active for the current PDF. The GUI will use one user-facing selection model, not a mix of hidden button semantics and auto-apply behavior. The observable gain is that a first-time user can create a certificate, return to the main shell, and know unambiguously whether choosing an item in the certificate selector immediately activates it or whether a second confirmation click is required.

## Child ExecPlan Dependencies

- [x] (2026-07-13 00:00Z) This child has no further child ExecPlans. Keep the slice on visible certificate-selection semantics, helper text, and tests.

## Progress

- [x] (2026-07-13 00:00Z) Confirmed that the code auto-applies certificate selection on combo-box change while still constructing a hidden `Use for this PDF` button.
- [x] (2026-07-18) Chose immediate application: selecting a saved certificate configuration applies it to the current PDF setup through the existing session/coordinator outcome path.
- [x] (2026-07-18) Aligned helper wording and the mounted selector with that one transition.
- [x] (2026-07-18) Retired the unmounted alternative `Use for this PDF` affordance.
- [x] (2026-07-18) Focused integrated coverage passed (163 tests) and architecture documentation was reconciled.
- [x] (2026-07-18) Ran the representative-PDF display-backed startup audit; focused Qt coverage verifies immediate selection, password prompting, cancellation, and error rollback.
- [x] (2026-07-19) Completed the semantic real-Qt certificate create/select walkthrough in `scripts/live_gui_parent_audit.py`: the visible Create certificate dialog persisted one isolated configuration and the mounted selector immediately applied it before placement, signing, reopen, and verification.

## Surprises & Discoveries

- Observation: the confusing part is not certificate creation but certificate activation semantics in the main shell.
  Evidence: `src/foliaseal/presentation/qt/app_frame_certificate_management.py` already provides visible create/import/manage dialogs, while `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py` both constructs a `Use for this PDF` button and auto-applies selection changes.

## Decision Log

- Decision: this slice should not change certificate cryptographic behavior, only how selection is exposed and explained in the GUI.
  Rationale: the underlying certificate lifecycle and password-prompt behavior already exist; the product gap is clarity and consistency.
  Date/Author: 2026-07-13 / Codex

## Outcomes & Retrospective

Immediate selection is now the single production behavior. The old unmounted
alternative has been removed; cancellation and resolution failures continue to
return a non-applied selection outcome. The 2026-07-19 semantic real-Qt audit
created an isolated certificate and selected its saved configuration through the
mounted shell before the full sign/reopen flow, closing the live-proof gap.

## Context and Orientation

Certificate creation, import, and management live in `src/foliaseal/presentation/qt/app_frame_certificate_management.py`. The main shell certificate selector lives in `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py`. When the user chooses a certificate configuration there, `SigningSetupSession.select_certificate_configuration(...)` resolves any required password, possibly prompting through a Qt input dialog, and then applies the resulting signing material to the `SigningDraftWorkflow`.

Today, the visible GUI only shows the combo box and helper text, while the code also still constructs an unmounted `Use for this PDF` button. A novice cannot reliably infer whether selection is immediate or staged. This plan makes the product choose one model and express it clearly.

## Plan of Work

First, decide whether the GUI should auto-apply certificate configurations or require an explicit apply button. Either model is acceptable if the surface is consistent. Auto-apply is simpler and matches current behavior; explicit apply may read more clearly in a staged workflow. Record the decision in the `Decision Log` before implementing.

Second, make the shell reflect that decision completely. If auto-apply wins, update helper text, remove dead button construction, and keep tests focused on selection-driven application. If explicit apply wins, remount the apply button visibly, stop selection-time auto-apply, and update stage and error behavior accordingly. In either case, password prompting and session-local passphrase caching should continue to work.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Re-read the certificate-selection and prompt flow.

       sed -n '1,220p' src/foliaseal/application/signing_setup_session.py
       sed -n '620,980p' src/foliaseal/presentation/qt/signing_workspace_properties_panel.py
       sed -n '1,220p' src/foliaseal/presentation/qt/signing_action_coordinator.py

2. Re-read the focused tests.

       rg -n "certificate configuration|apply_selected_certificate_configuration|typed-secret|stored-secret" tests/unit/test_qt_signing_shell.py

3. Implement the chosen surface and run focused tests.

       .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py -k "certificate_selection or certificate_configuration"

4. Validate manually in the live GUI.

       .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf

   Expected result: a user can tell at a glance how certificate selection takes effect, and the shell behaves exactly that way.

## Validation and Acceptance

Acceptance is behavioral. A first-time user should be able to create a certificate from the Settings menu, return to the main shell, choose that certificate configuration, and understand without guessing whether it is already active. Password prompt, cancel, and cache-reuse behavior must remain correct. The focused certificate-selection tests must pass, and the live GUI must no longer contain a hidden or contradictory alternate certificate-application path.

## Idempotence and Recovery

Keep one certificate-selection path active at all times. Do not remove the current auto-apply behavior until the replacement visible behavior is in place and covered by tests. If the chosen model proves too confusing in the live GUI, revert to the other single model rather than keeping both.

## Artifacts and Notes

The motivating findings for this slice are in:

    .tmp/gui_findings_and_fix_plan_2026-07-13.md

This slice should stay narrow: certificate-selection semantics only, not full sign-flow narration.

## Interfaces and Dependencies

The key files are `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py`, `src/foliaseal/application/signing_setup_session.py`, and the relevant tests in `tests/unit/test_qt_signing_shell.py`. Reuse the existing `SigningSetupSelectionOutcome` and manual passphrase-prompt path. The primary allowed change class is behavior change, with focused evidence refresh and minimal documentation follow-up.

Revision note: 2026-07-13 / Codex
Created this ExecPlan from the GUI audit because the main shell currently exposes certificate-selection behavior inconsistently and later confirmation/narration work must build on a single clear model.

Revision note: 2026-07-19 / Codex
Closed the stale live-walkthrough checkbox with the certificate creation and immediate-selection steps in `scripts/live_gui_parent_audit.py`.
