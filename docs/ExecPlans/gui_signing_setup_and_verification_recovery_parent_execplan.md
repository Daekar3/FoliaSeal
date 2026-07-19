# GUI signing setup and verification recovery parent plan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this parent plan is complete, a first-time user will be able to open a PDF, create or choose a signing certificate, create and save reusable signing setup objects, place a visible signature, review a clearly narrated readiness state, sign, reopen the result, and understand how to verify it and add another approval signature later if permitted. The user-visible gain is that FoliaSeal stops offering only an ad hoc current-document signing path and instead exposes the reusable-object workflow promised by `docs/SPEC.md`.

This parent plan exists because the missing product behavior spans several related but separately reviewable GUI seams. The current code can open, review, place, and sign, but it does not expose a complete user-facing route for reusable appearance, placement, and preset objects, and it does not yet present a complete post-sign verify story. The work should therefore be split into child ExecPlans that can be implemented and validated independently without losing the end-to-end product narrative.

## Child ExecPlan Dependencies

- [ ] `docs/ExecPlans/gui_reusable_signing_objects_execplan.md` must land before any plan can claim SPEC-compliant reusable signing setup creation, because the current GUI has no visible create/save path for new signature presets and no management surface for appearance or placement objects.
- [ ] `docs/ExecPlans/gui_certificate_selection_semantics_execplan.md` can run in parallel with the reusable-object work, but it should be complete before the confirmation-flow work lands so the sign-summary surface does not describe ambiguous certificate-selection behavior.
- [ ] `docs/ExecPlans/gui_sign_confirmation_and_verification_execplan.md` depends on the reusable-object plan and certificate-selection semantics plan being understood, because its confirmation and post-sign guidance must describe the actual active signing objects and certificate state.
- [ ] `docs/ExecPlans/gui_main_shell_process_narration_execplan.md` depends on the reusable-object plan and confirmation/verification plan, because the shell cannot truthfully narrate the full process until those surfaces exist.
- [ ] The parent walkthrough is not complete until all four child plans land and one live GUI audit against a representative PDF is rerun using `.tmp/gui_user_flow_audit_2026-07-13.md` as the exact checklist.

## Progress

- [x] (2026-07-13 00:00Z) Audited the current GUI against `docs/SPEC.md` and wrote `.tmp/gui_user_flow_audit_2026-07-13.md` as an exact click-by-click attempted user procedure.
- [x] (2026-07-13 00:00Z) Wrote `.tmp/gui_findings_and_fix_plan_2026-07-13.md` to summarize confirmed GUI problems and a high-level SPEC-compliant fix direction.
- [x] (2026-07-13 00:00Z) Ran two independent review passes over the audit and findings: one code-surface review and one SPEC-compliance review, then folded their corrections back into the temp artifacts.
- [x] (2026-07-13 00:00Z) Wrote this parent ExecPlan plus the child ExecPlans for reusable signing objects, certificate-selection semantics, sign confirmation plus verification, and main-shell process narration.
- [ ] Execute `gui_reusable_signing_objects_execplan.md`.
- [ ] Execute `gui_certificate_selection_semantics_execplan.md`.
- [ ] Execute `gui_sign_confirmation_and_verification_execplan.md`.
- [ ] Execute `gui_main_shell_process_narration_execplan.md`.
- [ ] Re-run the exact user-flow audit live in the GUI, then update `docs/ARCHITECTURE.md`, `README.md`, and any remaining acceptance notes so repository documentation matches the delivered product behavior.

## Surprises & Discoveries

- Observation: the most severe GUI problem is not visual clutter but the lack of an exposed reusable-object workflow.
  Evidence: `.tmp/gui_user_flow_audit_2026-07-13.md` reaches a hard stop at the signature-preset save step because the preset-name field and save/delete controls exist in code but are not mounted into the visible layout.

- Observation: the current GUI is closer to an ad hoc current-document signing workflow than the V1 product story in `docs/SPEC.md`.
  Evidence: `.tmp/gui_findings_and_fix_plan_2026-07-13.md` reduces the observed flow to `Open -> Create/select certificate configuration -> Edit current document setup -> Place -> Sign`, which is materially narrower than the specified reusable-object and verify/reopen story.

- Observation: some earlier conclusions about the GUI needed tightening after review.
  Evidence: the code-surface reviewer confirmed that main-menu `Copy selected text` becomes enabled immediately after a PDF is opened, while the SPEC reviewer confirmed that default output-path suggestion is allowed by spec and that the larger release-bar gap is missing reusable-object and verify-story behavior, not merely ambiguous output wording.

## Decision Log

- Decision: write a new parent plan instead of extending the earlier GUI MVP recovery parent plan.
  Rationale: the earlier parent plan focused on page navigation, text selection, staged guidance, terminology, and shell reduction. This new tranche begins from the audited remaining gaps: reusable signing objects, explicit confirmation/verify flow, and complete process narration. Keeping them in a distinct parent plan preserves a clean recovery boundary.
  Date/Author: 2026-07-13 / Codex

- Decision: split the remaining work into four child plans rather than one large GUI rewrite.
  Rationale: reusable-object flow, certificate-selection semantics, sign confirmation plus verification, and shell narration touch different presentation seams and should be reviewable and testable independently.
  Date/Author: 2026-07-13 / Codex

- Decision: treat the reusable-object flow as the first child and the gating dependency for the rest of the tranche.
  Rationale: the confirmation summary, process narration, and full spec story cannot be truthful until the user can visibly create and reuse appearance, placement, and preset objects.
  Date/Author: 2026-07-13 / Codex

## Outcomes & Retrospective

No implementation outcomes yet. This plan begins after the audit phase and before the recovery implementation slices. The immediate outcome is that the remaining GUI work is now decomposed into a parent/child plan set that is directly grounded in the exact user-flow audit and reviewed SPEC findings rather than in general impressions about the shell.

## Context and Orientation

FoliaSeal is a Linux desktop PDF signing application with a Qt GUI. The frozen product requirements live in `docs/SPEC.md`. That file defines the V1 story as: open a PDF, review it, choose or create a signing certificate, choose or refine a signing setup, place a visible signature, preview readiness, sign, save, reopen, verify, and add another approval signature later if document permissions allow it. The current code structure is described in `docs/ARCHITECTURE.md`, but this plan is written to stand alone.

The current GUI entrypoint is `src/foliaseal/presentation/qt/app_frame.py::launch_qt_app_frame`. The top-level frame installs `File`, `Edit`, and `Settings` menus. When a PDF is opened, `src/foliaseal/presentation/qt/app_frame_workspace_open.py` creates a `ViewerWorkflow` and a `SigningDraftWorkflow`, then boots the live signing shell under `src/foliaseal/presentation/qt/`. The main right-hand shell surfaces now live mostly in `signing_workspace_sidebar.py` and `signing_workspace_properties_panel.py`, while current-document appearance and placement editing lives in `visible_signature_setup_form.py` and the modal refinement path opened by `SignaturePropertiesPanel.open_refinement_dialog()`.

The temp audit `.tmp/gui_user_flow_audit_2026-07-13.md` is the authoritative description of what a user can and cannot do today. It confirms that FoliaSeal can open a PDF, create a certificate and matching certificate configuration, refine a current-document setup, place a signature, and sign. It also confirms that the user currently has no visible GUI path to create and save a new reusable signature preset, and no visible dedicated management path for appearance or placement objects. The reviewed findings file `.tmp/gui_findings_and_fix_plan_2026-07-13.md` sharpens that into the remaining SPEC gap: the current GUI still does not expose the full reusable-object workflow or a complete reopen/verify story.

The relevant terms are simple but must stay precise. A `Certificate Configuration` is the user-facing saved signing identity backed by a managed certificate. An `Appearance Profile` is a reusable visible-signature look. A `Placement Profile` is a reusable placement template. A `Signature Preset` composes references to those reusable objects. In the current GUI, certificate configurations have visible create/manage surfaces, while the other object classes do not yet have equivalent user-facing management.

## Plan of Work

Start with the missing reusable-object workflow. The first child plan should make it possible to create, save, edit, and reuse appearance, placement, and preset objects without reintroducing the old always-open harness editor. That work should keep live-document editing contextual, most likely by extending the current refinement dialog with explicit “save for reuse” actions and by adding a dedicated management surface reachable from the main shell or settings area.

In parallel or immediately after that, make certificate-selection behavior singular and explicit. The code currently auto-applies certificate selection on combo-box change while also constructing a hidden `Use for this PDF` button. The second child plan should choose one user-facing model and make the helper text, state transitions, and tests all agree with that model.

Once signing objects and certificate semantics are stable, add a clear sign confirmation plus verification story. The third child plan should make `Confirm and sign` lead into an unmistakable final confirmation state that shows the active signing objects, output path, readiness caveats, and the user-visible next step after a successful sign. That same plan should make the reopen-and-verify path explicit, truthful, and testable.

Finally, adjust the main shell narration so that the user can understand the end-to-end process without outside explanation. The fourth child plan should make the right-hand shell state read like a product workflow: what is active, what is missing, what can be saved for reuse, what the next action is, and how the post-sign story continues.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Re-open the governing spec and the audited GUI findings before each child plan starts.

       sed -n '1,320p' docs/SPEC.md
       sed -n '1,260p' .tmp/gui_user_flow_audit_2026-07-13.md
       sed -n '1,260p' .tmp/gui_findings_and_fix_plan_2026-07-13.md

   Expect to see the exact user-flow blockage at preset save plus the remaining SPEC gaps around reusable objects and verification.

2. Read and execute the reusable-object child plan first.

       sed -n '1,320p' docs/ExecPlans/gui_reusable_signing_objects_execplan.md

3. Read and execute the remaining child plans in dependency order.

       sed -n '1,260p' docs/ExecPlans/gui_certificate_selection_semantics_execplan.md
       sed -n '1,320p' docs/ExecPlans/gui_sign_confirmation_and_verification_execplan.md
       sed -n '1,320p' docs/ExecPlans/gui_main_shell_process_narration_execplan.md

4. After the children land, re-run the live GUI walkthrough on a representative PDF.

       .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf

   The expected result is that a novice can complete the audited story without hitting a dead end: create a certificate, save reusable signing objects, place a signature, review a clear confirmation state, sign, reopen the result, and understand verification and next-step guidance.

5. Reconcile docs after the live walkthrough.

       rg -n "Appearance Profile|Placement Profile|Signature Preset|verify|Open signed PDF|Confirm and sign" docs/ARCHITECTURE.md README.md docs/SPEC.md

## Validation and Acceptance

This parent plan is successful only when the child plans collectively deliver a visible, restartable, novice-usable signing workflow. Passing unit tests alone is not enough. A human should be able to launch the GUI, open a PDF, create a certificate, create and save reusable signing objects, re-select those objects, place a visible signature, understand the current readiness state, sign, reopen the result, and follow plain-language verification guidance without asking a developer what any of the core controls mean.

Each child plan must carry its own focused tests and manual validation. The parent acceptance pass is the final live GUI walkthrough using `.tmp/gui_user_flow_audit_2026-07-13.md` as a checklist. If any step in that audited story still requires hidden controls, code knowledge, or unstated assumptions, the parent plan is not done.

## Idempotence and Recovery

This parent plan is orchestration and documentation, so it is safe to revisit many times. Child plans should remain narrow and additive. If one child stalls or is reverted, update this parent plan immediately so the dependency list and progress section show the actual open gaps. Do not mark the parent done based on one successful slice; the live end-to-end walkthrough must be rerun after all child work lands.

## Artifacts and Notes

The audit artifact that motivates this plan is:

    .tmp/gui_user_flow_audit_2026-07-13.md

The reviewed findings and high-level fix direction are:

    .tmp/gui_findings_and_fix_plan_2026-07-13.md

The live GUI entrypoint used for validation is:

    .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf

The key spec anchors are:

    docs/SPEC.md:43-58
    docs/SPEC.md:120-139
    docs/SPEC.md:253-312

## Interfaces and Dependencies

The relevant implementation modules are all under `src/foliaseal/presentation/qt/`. The top-level frame and menus are in `app_frame.py` and `app_frame_workspace_open.py`. Certificate creation and management dialogs are in `app_frame_certificate_management.py`. The main signing shell is composed through `signing_workspace_composition.py`, `signing_workspace_sidebar.py`, `signing_workspace_properties_panel.py`, `visible_signature_setup_form.py`, `signing_action_coordinator.py`, and the runtime/bridge helpers such as `signing_workspace_action_bridge.py` and `signing_workspace_runtime.py`. Reusable-object semantics below Qt live in `src/foliaseal/application/signature_properties_coordinator.py`, `src/foliaseal/application/signing_setup_session.py`, and the persistent schema/store modules under `src/foliaseal/infra/config/`.

The allowed change classes for the child plans are primarily behavior change plus focused evidence refresh. Documentation/status updates should follow the behavior slices and should not be mixed into unrelated GUI refactors unless the `Decision Log` in the relevant child plan explains why a mixed slice is unavoidable.

Revision note: 2026-07-13 / Codex
Created this parent plan from the reviewed GUI audit because the remaining SPEC gaps are now concentrated in reusable signing objects, certificate-selection semantics, sign confirmation plus verification, and explicit process narration.
