# GUI main-shell process narration recovery

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this change, the main signing shell will tell the user what is active, what is missing, what can be saved for reuse, and what the next meaningful action is. A novice will no longer need source-code knowledge to understand the relationship among certificate configuration, reusable signing objects, current-document setup, placement, output target, and the sign action. The user-visible proof is that a first-time user can read the right-hand shell and correctly describe the next step at each stage of the signing workflow.

## Child ExecPlan Dependencies

- [x] (2026-07-13 00:00Z) This child has no further child ExecPlans. Keep the slice on main-shell narration, summaries, labels, and stage-to-control alignment.

## Progress

- [x] (2026-07-13 00:00Z) Confirmed from the audit and reviewed findings that the shell still relies on too much user inference even after earlier terminology and shell-reduction work.
- [x] (2026-07-18) Centralized stage-appropriate narration in the signing-action state: placement, preview review, confirm/sign, and signed-result guidance.
- [x] (2026-07-18) Made the active setup and output target explicit in the final confirmation, while signed guidance points to reopen and local verification.
- [x] (2026-07-18) Focused integrated coverage passed (163 tests) and architecture documentation was reconciled.
- [x] (2026-07-18) Ran the representative-PDF display-backed startup audit; focused Qt coverage verifies stage, readiness, confirmation, output, and signed-state narration.
- [ ] Complete the live narrated flow through signing and reopen; the startup smoke audit only verifies initial rendering.

## Surprises & Discoveries

- Observation: the shell already has enough structural pieces that this slice should be mostly composition and wording rather than a large new subsystem.
  Evidence: the sidebar already contains a sign panel, review panel, text panel, preset/certificate selectors, preview card, and refinement entrypoint; the gap is how those pieces narrate the process together.

## Decision Log

- Decision: do this slice after reusable objects and confirmation/verification are in place.
  Rationale: the shell cannot narrate truths about reusable setup and sign confirmation until those behaviors exist visibly.
  Date/Author: 2026-07-13 / Codex

## Outcomes & Retrospective

The shell now narrates the sign lifecycle from the state coordinator and confirmation
dialog instead of relying on an implicit transition to the irreversible action.
The remaining outcome is a display-backed audit, not further inferred completion.

## Context and Orientation

The right-hand shell is assembled in `src/foliaseal/presentation/qt/signing_workspace_sidebar.py` and `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py`, with state contributions from `src/foliaseal/presentation/qt/signing_action_coordinator.py` and the review/text bridge modules. Earlier GUI recovery work already improved page navigation, text selection, terminology, and default shell shape. The remaining problem is that the shell still assumes the user can infer object relationships and next steps.

In plain language, the shell needs to answer these questions at all times: Which certificate is active? Which reusable signing setup is active? Am I editing only this document or saving something reusable? Do I still need to place the signature? Where will the output go? What happens if I press the sign button now? The audit confirms that those answers are not currently explicit enough.

## Plan of Work

First, define the user-facing summaries and stage text that the repaired GUI should show. The preset and certificate sections should state whether they are selection-only or whether the current setup is unsaved custom state. The sign panel should surface the current output target and the exact next step. The refinement entrypoint should state that it edits the current document setup and should point visibly toward the reusable-object save path once that exists.

Second, align control visibility and emphasis with the stage model. When the user still needs to place a signature, the shell should foreground placement guidance. When the user has an unsaved custom setup, the shell should say so and show how to save it for reuse. When the user is ready to sign, the shell should foreground the final review path. After signing, the shell should foreground reopen and verification.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Re-read the current shell composition and action-state wording.

       sed -n '260,420p' src/foliaseal/presentation/qt/signing_workspace_sidebar.py
       sed -n '520,980p' src/foliaseal/presentation/qt/signing_workspace_properties_panel.py
       sed -n '1,260p' src/foliaseal/presentation/qt/signing_action_coordinator.py

2. Re-read the motivating audit and findings.

       sed -n '1,260p' .tmp/gui_user_flow_audit_2026-07-13.md
       sed -n '1,260p' .tmp/gui_findings_and_fix_plan_2026-07-13.md

3. Implement the shell narration updates and run focused tests.

       .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py -k "flow_summary or stage_text or output or preset"

4. Validate manually in the live GUI.

       .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf

   Expected result: a novice can look only at the right-hand shell and correctly identify the current state and next action.

## Validation and Acceptance

Acceptance is behavioral. Launch the GUI, open a representative PDF, and walk through certificate selection, reusable-object save/reuse, placement, confirmation, signing, and reopen. At each point, a first-time user should be able to answer “what is active?” and “what do I do next?” from the visible shell alone. If the user still needs an external explanation to understand the difference between saved setup, current-document setup, output target, or sign stage, this slice is not done.

## Idempotence and Recovery

Prefer text and composition changes that can be tested without destabilizing the working signing logic. If stage wording changes force test rewrites, keep the new wording centralized so future edits are narrow. Avoid mixing unrelated structural refactors into this slice; it should mainly be behavior and presentation alignment on top of the already-repaired capabilities.

## Artifacts and Notes

The motivating audit and findings are:

    .tmp/gui_user_flow_audit_2026-07-13.md
    .tmp/gui_findings_and_fix_plan_2026-07-13.md

This slice is the final narration layer, not the place to invent new persistence or signing engines.

## Interfaces and Dependencies

The key files are `src/foliaseal/presentation/qt/signing_workspace_sidebar.py`, `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py`, and `src/foliaseal/presentation/qt/signing_action_coordinator.py`, with test coverage in `tests/unit/test_qt_signing_shell.py`. Reuse the existing sidebar/property-panel composition and stage-state plumbing. The primary allowed change class is behavior change, followed by focused evidence refresh and documentation updates once the live shell wording is settled.

Revision note: 2026-07-13 / Codex
Created this ExecPlan from the reviewed GUI audit because the repaired capabilities still need explicit main-shell narration so the full signing process becomes understandable without developer explanation.
