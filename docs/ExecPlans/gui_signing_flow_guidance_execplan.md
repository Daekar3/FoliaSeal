# GUI signing flow guidance

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this change, the main FoliaSeal window will explain the signing process instead of merely exposing controls. A first-time user will be able to see what stage they are in, what is blocking progress, what action to take next, and when they have moved from review to placement to readiness to an explicit sign confirmation to saved-result verification. The work must preserve the spec’s on-page preview and readiness emphasis rather than hiding it behind generic stage labels. This is the central productization step that turns the real GUI from a harness-derived shell into an understandable desktop workflow.

## Child ExecPlan Dependencies

- [x] (2026-07-08 13:56Z) This child has no further child ExecPlans. Keep the slice on workflow guidance, stage presentation, and mode signaling rather than broad content redesign.

## Progress

- [x] (2026-07-08 13:56Z) Wrote this ExecPlan from the live GUI review, `docs/SPEC.md`, and the current signing sidebar/shell structure.
- [ ] Define the exact staged workflow presentation for the main shell and record it here.
- [ ] Implement UI guidance that makes the active stage, missing prerequisites, and next action explicit.
- [ ] Improve placement-mode signaling, including cursor/mode cues where appropriate.
- [ ] Update focused tests for signing-flow summary and shell rendering behavior.
- [ ] Validate the entire staged flow manually in the live GUI.

## Surprises & Discoveries

- Observation: the shell already has a signing-flow state model, but the live GUI still fails to communicate the process clearly enough for a first-time user.
  Evidence: `signing_workspace_sidebar.py` already renders a `Sign PDF` panel with stage/detail labels, yet the user still could not tell what `Apply certificate` meant or what step should come next.

## Decision Log

- Decision: this plan should treat stage guidance as a product behavior change, not just text tweaking.
  Rationale: the problem is not merely wording. The current arrangement of controls and mode cues fails to teach the intended process even if labels are edited.
  Date/Author: 2026-07-08 / Codex

## Outcomes & Retrospective

No implementation outcomes yet. Update this after the live GUI can be walked end-to-end without developer interpretation.

## Context and Orientation

The frozen product spec in `docs/SPEC.md` defines the intended V1 story: open a PDF, review it, choose or create a signing certificate, choose or refine a signing setup, place a visible signature, preview readiness, sign, save, reopen, and verify. The current shell already contains several relevant pieces: the `Sign PDF` panel in `src/foliaseal/presentation/qt/signing_workspace_sidebar.py`, the signing action state model in `src/foliaseal/presentation/qt/signing_action_coordinator.py`, the certificate and preset controls in `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py`, and the visible-signature setup surface in `src/foliaseal/presentation/qt/visible_signature_setup_form.py`.

The problem is that these pieces currently read like exposed mechanisms rather than like one user journey. The user could not tell what control to use next, what `Apply certificate` meant, or when the app had moved between review, placement, and readiness states. This plan fixes the explanatory structure of the shell.

## Plan of Work

Start by writing down the intended stage model in concrete desktop language. The product does not need a wizard, but it does need a visible “you are here / do this next” story. Reuse the existing signing-flow summary state if possible, but change the rendering and surrounding layout until the stage panel truly helps the user orient themselves. This may require moving or regrouping controls within the shell so that the next action is spatially obvious. Preserve the existing on-page preview/readiness emphasis from the spec: the user must still be able to judge whether the visible signature on the page matches expectations before signing.

The stage model should minimally cover: document review, certificate or preset selection, placement, readiness review, explicit sign confirmation, signing, saved-result review, and verification/reopen. Each state should present a primary instruction in plain language and should suppress or visually de-emphasize irrelevant controls. If placement mode is active, the viewer should say so visibly, not just respond to raw mouse behavior. If the user cannot sign yet, the reason should be concrete and local to the blocking step. The confirmation step before actual signing must remain explicit even if the surrounding flow becomes faster and clearer.

Implement the shell changes in the modules that already own stage rendering and action coordination. Avoid duplicating state or introducing a second workflow engine. The existing `SigningActionState` and sidebar rendering path should remain the primary seam unless it proves too narrow. Add focused tests for the rendered stage text and transitions, then validate the whole flow manually in the live GUI.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Re-read the current flow/state modules.

       sed -n '1,260p' src/foliaseal/presentation/qt/signing_action_coordinator.py
       sed -n '1,260p' src/foliaseal/presentation/qt/signing_workspace_sidebar.py
       sed -n '1,260p' src/foliaseal/presentation/qt/signing_workspace_properties_panel.py

2. Re-read the key workflow requirements.

       sed -n '40,120p' docs/SPEC.md

3. Implement the staged-flow guidance changes, then run focused tests.

       .venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_signing_action_coordinator.py

4. Validate manually in the live GUI.

       .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf

   Expected result: a user can tell what stage they are in and what they must do next without outside explanation.

## Validation and Acceptance

Acceptance is behavioral. Launch the GUI, open the representative PDF, and walk the shell from review through signing without consulting the code. The app should explicitly communicate when the user must review the document, choose a certificate or preset, place the visible signature, inspect readiness and on-page preview fidelity, confirm the sign action explicitly, save, and verify. Ambiguous controls such as `Apply certificate` must either become self-explanatory through surrounding guidance or be renamed/reworked through the sibling clarity plan.

Focused tests should assert the relevant stage/state rendering and transitions. Manual validation is mandatory because the failure mode here is user confusion, not just incorrect internal state.

## Idempotence and Recovery

This slice can be repeated safely, but it should not balloon into a full visual redesign. If a particular stage treatment fails manual review, revise the copy, emphasis, or grouping while keeping the underlying workflow state model stable. If the implementation reveals that existing stage state is insufficient, extend it carefully and document the decision here rather than layering ad hoc UI conditionals.

## Artifacts and Notes

The primary spec anchors are:

    docs/SPEC.md:71
    docs/SPEC.md:169-176

The motivating product review is:

    .tmp/gui_ux_review_2026-07-08.md

## Interfaces and Dependencies

The main dependencies are `signing_action_coordinator.py`, `signing_workspace_sidebar.py`, `signing_shell.py`, and the certificate/preset controls in `signing_workspace_properties_panel.py`. The final UI should expose a stable, explicit stage presentation that can be exercised in tests and seen plainly in the live GUI.

Revision note: 2026-07-08 / Codex
Created this plan after the first live GUI walkthrough showed that the shell had controls and stage state, but still failed to communicate the intended signing process.
