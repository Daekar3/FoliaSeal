# GUI signing flow guidance

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this change, the main FoliaSeal window will explain the signing process instead of merely exposing controls. A first-time user will be able to see what stage they are in, what is blocking progress, what action to take next, and when they have moved from review to placement to readiness to an explicit sign confirmation to saved-result verification. The work must preserve the spec’s on-page preview and readiness emphasis rather than hiding it behind generic stage labels. This is the central productization step that turns the real GUI from a harness-derived shell into an understandable desktop workflow.

## Child ExecPlan Dependencies

- [x] (2026-07-08 13:56Z) This child has no further child ExecPlans. Keep the slice on workflow guidance, stage presentation, and mode signaling rather than broad content redesign.

## Progress

- [x] (2026-07-08 13:56Z) Wrote this ExecPlan from the live GUI review, `docs/SPEC.md`, and the current signing sidebar/shell structure.
- [x] (2026-07-18) Re-explored the current state engine and viewer interaction cues; selected the existing signing-action coordinator/sidebar and viewer-toolbar seams for implementation.
- [x] (2026-07-18) Defined the persistent six-step journey: Review, Setup, Place, Ready, Sign, Verify. The state panel identifies the current actionable stage without pretending that review is a one-time locked wizard step.
- [x] (2026-07-18) Implemented plain-language setup, placement, readiness, confirmation, and verification guidance in the Qt-free action coordinator and sidebar renderer.
- [x] (2026-07-18) Added a persistent viewer-toolbar mode cue that distinguishes placement dragging from text selection, alongside the existing cursor change.
- [x] (2026-07-18) Updated focused coordinator and shell behavior coverage; `112 passed` and Ruff passed.
- [x] (2026-07-18) Performed a display-backed representative-PDF startup smoke audit. It visibly showed the six-step journey and setup guidance; full sign/reopen click-through remains covered by focused Qt tests, not claimed as a manual end-to-end walkthrough.
- [x] (2026-07-20) Re-explored the direct acceptance seam. `scripts/live_gui_parent_audit.py` drives isolated real Qt widgets through certificate creation, placement, the real confirmation dialog, signing, reopen, and verification; it is suitable for reproducible direct workflow evidence when its retained screenshots are visually reviewed.
- [x] (2026-07-20) Ran `DISPLAY=:0 timeout 180s .venv/bin/python scripts/live_gui_parent_audit.py --artifacts-dir /tmp/foliaseal-staged-flow-audit`; all twelve real-Qt workflow checkpoints passed, including readiness, signing, reopened signed PDF, and verification.
- [x] (2026-07-20) Visually reviewed `01-document-review.png`, `09-ready-to-sign.png`, and `12-reopened-and-verified.png`; they show the persistent journey/setup guidance, Step 5 readiness with visible placement, and reopened visible signature with local verification text. `wmctrl -lx` and a process scan found no FoliaSeal window or audit process afterward.
- [x] (2026-07-20) Re-ran focused staged-flow evidence: `113 passed` for `tests/unit/test_qt_signing_shell.py` and `tests/unit/test_qt_signing_action_coordinator.py`; Ruff passed for the coordinator and sidebar modules.

## Surprises & Discoveries

- Observation: the shell already has a signing-flow state model, but the live GUI still fails to communicate the process clearly enough for a first-time user.
  Evidence: `signing_workspace_sidebar.py` already renders a `Sign PDF` panel with stage/detail labels, yet the user still could not tell what `Apply certificate` meant or what step should come next.

- Observation: a numbered active-stage label alone can imply a rigid wizard and omit the always-available document-review step.
  Evidence: the first implementation only derived actionable states 2 through 6; focused compliance review required a permanently visible journey that includes Review.

- Observation: launching `foliaseal gui` directly uses a person's configured certificate and profile stores, while the parent audit runner supplies isolated stores and a temporary PDF/output path.
  Evidence: `scripts/live_gui_parent_audit.py` constructs and closes the Qt workflow in its own temporary environment; this makes its direct GUI route safer and repeatable for acceptance evidence.

- Observation: the retained `ready-to-sign` frame shows Step 5 and the real `Confirm and sign` action with the output path, while the reopened frame shows the embedded visible signature and local verification review.
  Evidence: `/tmp/foliaseal-staged-flow-audit/09-ready-to-sign.png` and `/tmp/foliaseal-staged-flow-audit/12-reopened-and-verified.png`; `audit.json` reports twelve passed checkpoints.

## Decision Log

- Decision: this plan should treat stage guidance as a product behavior change, not just text tweaking.
  Rationale: the problem is not merely wording. The current arrangement of controls and mode cues fails to teach the intended process even if labels are edited.
  Date/Author: 2026-07-08 / Codex

- Decision: render the full six-step journey persistently in the sidebar and derive only the current actionable setup, placement, readiness, confirmation, or verification state from `SigningActionCoordinator`.
  Rationale: review is continuously available through the document-centric viewer, not a one-time acknowledgement. This shows the complete product story without inventing a second wizard state machine.
  Date/Author: 2026-07-18 / Codex

- Decision: make the viewer toolbar own the persistent mode cue, while the existing viewer remains responsible for the CrossCursor and I-beam cursor behavior.
  Rationale: the toolbar is visible while the user drags on the page, so it can explain the active interaction mode without duplicating workflow state in the viewer.
  Date/Author: 2026-07-18 / Codex

- Decision: close the remaining direct acceptance with the display-backed isolated Qt audit runner and visual inspection of its retained artifacts.
  Rationale: it exercises the actual mounted controls, confirmation dialog, signing, reopen, and verification path while avoiding mutation of the user's configured profiles or output files. The evidence will be described accurately as semantic real-Qt interaction plus visual review, not as an independent human-input usability study.
  Date/Author: 2026-07-20 / Codex

## Outcomes & Retrospective

The sidebar now exposes the complete `Review → Setup → Place → Ready → Sign → Verify` journey, while the active state gives a direct next action. Missing certificate material directs the user to setup; missing placement explains that page dragging is active; invalid drafts point to readiness review; valid drafts lead to explicit confirmation; and successful signing leads to local verification/reopen guidance. The viewer toolbar visibly changes between placement and text-selection instructions. Focused Qt behavior tests passed (`113 passed`), and the isolated real-Qt certificate-to-reopen audit passed all twelve checkpoints. Visual review confirmed the setup, readiness, and reopened-verification states; its semantic automation is recorded accurately as direct mounted-GUI behavior evidence rather than a separate human-input usability study.

## Context and Orientation

The frozen product spec in `docs/SPEC.md` defines the intended V1 story: open a PDF, review it, choose or create a signing certificate, choose or refine a signing setup, place a visible signature, preview readiness, sign, save, reopen, and verify. The current shell already contains several relevant pieces: the `Sign PDF` panel in `src/foliaseal/presentation/qt/signing_workspace_sidebar.py`, the signing action state model in `src/foliaseal/presentation/qt/signing_action_coordinator.py`, the certificate and preset controls in `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py`, and the visible-signature setup surface in `src/foliaseal/presentation/qt/visible_signature_setup_form.py`.

The problem is that these pieces currently read like exposed mechanisms rather than like one user journey. The user could not tell what control to use next, what `Apply certificate` meant, or when the app had moved between review, placement, and readiness states. This plan fixes the explanatory structure of the shell. `signing_workspace_composition.py` owns the persistent viewer-toolbar mode cue and updates it from review/text-selection state; the viewer continues to own its CrossCursor/I-beam behavior.

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

The main dependencies are `signing_action_coordinator.py`, `signing_workspace_sidebar.py`, `signing_workspace_composition.py`, `signing_shell.py`, and the certificate/preset controls in `signing_workspace_properties_panel.py`. `signing_workspace_composition.py` owns the toolbar's persistent placement-versus-text-selection instruction label; `signing_workspace_review_bridge.py` supplies the review/text state that drives it, and the viewer retains cursor ownership. The final UI exposes a stable, explicit stage presentation exercised by focused tests and by the isolated real-Qt audit at `/tmp/foliaseal-staged-flow-audit`. That audit drives the mounted certificate, placement, output, confirmation, signing, reopen, and verification route, then retains screenshots for visual review. Its evidence is semantic automation plus visual inspection, not an independent human-input usability study.

Revision note: 2026-07-18 / Codex
Completed the staged guidance and viewer mode-cue implementation, recorded the persistent-journey decision, and corrected manual-audit scope to startup smoke evidence rather than an unperformed end-to-end walkthrough.

Revision note: 2026-07-20 / Codex
Added the isolated real-Qt acceptance route after re-exploration. It is the safe, reproducible way to close the required sign-and-reopen evidence without mutating a user's configured GUI state; artifact inspection remains mandatory.

Revision note: 2026-07-20 / Codex
Completed the direct staged-flow acceptance with isolated real-Qt execution, retained-artifact inspection, focused tests, and explicit GUI cleanup verification.

Revision note: 2026-07-20 / Codex
Compliance review removed the obsolete startup-only evidence statement so the interface section matches the completed audit scope.
