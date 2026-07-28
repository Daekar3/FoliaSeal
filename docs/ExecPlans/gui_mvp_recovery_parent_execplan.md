# GUI MVP recovery parent plan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this plan is complete, a first-time user will be able to launch the real FoliaSeal GUI, open a PDF, review the document, navigate pages, switch intentionally between document review and signature placement modes, choose a certificate or preset with understandable language, place a visible signature, sign, save, and understand how to verify the result. The immediate win is not new cryptographic capability; it is that the existing desktop product stops feeling like a harness and starts behaving like the V1 workflow described in `docs/SPEC.md`.

This parent plan exists because the current problems are tightly related but should not be implemented as one giant change. The work needs to stay reviewable and restartable. Each child ExecPlan below owns one coherent user-visible slice that can be implemented and validated independently while still moving the overall GUI toward MVP.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/gui_document_review_usability_execplan.md` landed before staged-flow completion.
- [x] `docs/ExecPlans/gui_text_selection_mode_execplan.md` landed before staged-flow completion.
- [x] `docs/ExecPlans/gui_signing_flow_guidance_execplan.md` landed in `08d1021c7` and completed its direct isolated real-Qt acceptance on 2026-07-20.
- [x] `docs/ExecPlans/gui_certificate_and_preset_clarity_execplan.md` completed its live GUI validation in `7d940ab3f`.
- [x] `docs/ExecPlans/gui_preset_first_shell_reduction_execplan.md` implemented progressive disclosure after staged-flow guidance landed; its direct default-shell acceptance completed on 2026-07-28 with the isolated 14-checkpoint audit and retained screenshot review.
- [x] The refinement/profile-library fallback path is verified by the current reusable-object audit; it remains available while the default shell stays narrow.

## Progress

- [x] (2026-07-08 13:35Z) Re-ran the live GUI, captured direct user observations, and wrote `.tmp/gui_ux_review_2026-07-08.md` to separate product failures from internal architecture concerns.
- [x] (2026-07-08 13:42Z) Cross-checked the live observations against `docs/SPEC.md` and the Qt code to confirm which issues are direct MVP/spec misses versus secondary UX debt.
- [x] (2026-07-08 13:56Z) Wrote this parent ExecPlan plus the child ExecPlans needed to cover document usability, staged flow, certificate/preset clarity, and removal of harness-shaped shell dominance.
- [x] (2026-07-10 18:55Z) Completed `gui_document_review_usability_execplan.md`, including relocation of page navigation into a compact toolbar above the viewer, editable page jump, focused tests, and live GUI validation with follow-up sizing polish.
- [x] (2026-07-11 00:12Z) Completed `gui_text_selection_mode_execplan.md`, including classic desktop command placement, viewer cursor/mode signaling, working select/copy behavior, toolbar icon polish, focused tests, and live GUI validation.
- [x] (2026-07-20) Revalidated certificate/preset clarity and settings-directory browsing in a fresh 12-checkpoint display-backed audit.
- [x] (2026-07-20) Completed the staged-flow direct acceptance required by `gui_signing_flow_guidance_execplan.md`: the isolated real-Qt route passed twelve checkpoints through certificate/setup, placement, explicit confirmation, signing, reopen, and local verification; retained screenshots received visual review.
- [x] (2026-07-28) Completed the direct default-shell assertion required by `gui_preset_first_shell_reduction_execplan.md`; the isolated audit passed `preset-first-default-shell` and `manual-refinement-dialog`, and cleanup found no FoliaSeal process or window.
- [x] (2026-07-20) Ran an end-to-end representative-PDF walkthrough covering profile creation/reselection, placement, output selection, confirmation, signing, reopen, and verification. This broader audit did not replace the separately specified direct acceptance checks; the later staged-flow and preset-first audits now close those gaps. `docs/ARCHITECTURE.md` remains current, and README now records the preset-first default-shell boundary.

## Surprises & Discoveries

- Observation: the repository already has a real GUI entrypoint and enough product surface for meaningful UX review, so the main blocker is no longer “missing GUI” but “wrong or incomplete workflow.”
  Evidence: `src/foliaseal/__main__.py` dispatches `foliaseal gui` to `launch_qt_app_frame(...)`, and the user successfully opened a PDF in the live app.

- Observation: at least two of the live problems are direct misses against the frozen spec, not matters of taste.
  Evidence: `docs/SPEC.md` explicitly requires page navigation and document text selection/copy, while the user could not discover visible page navigation and could not get text selection to function.

- Observation: the current shell still exposes too much harness-shaped editing in the primary workflow even after the recent architectural cleanup.
  Evidence: the main shell still renders `Certificate configuration`, `Signature presets`, and the full `Visible signature` editing surface inline in the right-hand workflow pane.

## Decision Log

- Decision: split the product recovery into five child ExecPlans instead of one large GUI rewrite plan.
  Rationale: document usability, staged-flow guidance, terminology/empty-state clarity, and shell simplification can each be validated separately and would be hard to review if mixed into one giant slice.
  Date/Author: 2026-07-08 / Codex

- Decision: treat page navigation and text selection as separate child plans even though both live in the document-review experience.
  Rationale: page navigation is primarily about discoverability and control surface, while text selection is a deeper interaction-mode and cursor-behavior problem. They will likely touch different code and should not block each other unnecessarily.
  Date/Author: 2026-07-08 / Codex

- Decision: make the shell simplification a child plan that follows staged-flow guidance rather than leading with a big removal/refactor.
  Rationale: removing inline editing before the replacement workflow is clear would risk breaking the only available path without giving users a better one.
  Date/Author: 2026-07-08 / Codex

## Outcomes & Retrospective

Two document-review recovery slices are complete. The live GUI now exposes viewer-local page navigation, direct page jump, intentional text-selection mode, working copy behavior, and compact toolbar icons that fit the existing dark shell more cleanly than the earlier text-button pass. Those changes removed the most obvious review-stage spec misses, but they also clarified the next bottleneck: the right-hand shell still uses harness-era terminology and object relationships that are not intelligible enough for a first-time user.

The parent plan is now ready for its integrated final walkthrough: the certificate/preset clarity, staged-flow, and preset-first shell slices all have current live GUI evidence, including the 14-checkpoint audit proving the default-shell/refinement boundary. The parent remains open until that final walkthrough and release-bar reconciliation are recorded.

## Context and Orientation

FoliaSeal is a Linux desktop PDF signing application with a Qt GUI. The governing product requirements live in `docs/SPEC.md`. That file is frozen and defines the intended V1 user story: open a PDF, review it, choose or create a certificate, choose or refine a signing setup, place a visible signature, preview readiness, sign, save, reopen, and verify the result. The codebase structure and current implementation notes live in `docs/ARCHITECTURE.md`, but this parent plan is written to stand on its own.

The live GUI entrypoint is the `gui` subcommand in `src/foliaseal/__main__.py`. It dispatches to `src/foliaseal/presentation/qt/app_frame.py::launch_qt_app_frame`, which creates the top-level `FoliaSealAppFrame`. That frame owns the `File` and `Settings` menus and constructs one live signing workspace when a PDF is opened. The signing workspace itself is composed through the Qt presentation modules under `src/foliaseal/presentation/qt/`, especially `signing_shell.py`, `signing_workspace_sidebar.py`, `signing_workspace_properties_panel.py`, `visible_signature_setup_form.py`, and the viewer modules such as `viewer_widget.py`.

The key product problem discovered in the live walkthrough is that the GUI exposes mechanisms without clearly presenting the user workflow. Page navigation exists as keyboard behavior, but not as obvious GUI affordances. A `Select text` checkbox exists, but the user could not make it perform visible text selection. The main shell still devotes major space to inline editing controls that resemble a harness rather than a product. The frozen spec also says the product should bias toward a `Signature Preset`-first flow and place full object management in dedicated settings or library areas, which is in tension with the always-open inline editor shape in the current shell.

These plans intentionally focus on the product gaps uncovered in the live review. They do not replace or waive other existing spec responsibilities such as numeric placement refinement, offline verification honesty, or reopening a signed PDF to add another approval signature later. Any child plan that changes the shell or stage guidance must preserve those capabilities or explicitly state why they are not in scope for that slice.

The review artifact `.tmp/gui_ux_review_2026-07-08.md` captures the direct observations that motivated this plan set. That file is not governing, but it is the best starting evidence for why the child plans exist.

## Plan of Work

Begin with document usability because a signing flow cannot be productized if the user cannot comfortably review and navigate the PDF. The first child plan adds explicit page-navigation controls and current-page status to the document workspace. The second child plan fixes text-selection mode so it works visibly, uses correct cursor feedback, and has a more product-appropriate control shape than a passive checkbox that appears to do nothing.

Once document review is usable, reshape the overall workflow. The staged-flow child plan should make the main shell communicate what stage the user is in, what is incomplete, and what the next meaningful action is. That work should include placement-mode signaling and make the signing path read like the spec’s `Open -> Review -> Choose preset/certificate -> Place -> Preview readiness -> Sign -> Save -> Verify` story instead of a collection of disconnected controls.

In parallel with staged-flow guidance, fix terminology and clarity around certificates and presets. The certificate/preset clarity child plan should explain the difference between managed certificates and certificate configurations, rename or restyle confusing actions such as `Apply certificate`, improve empty states, and add stronger desktop affordances in the application-settings dialog for choosing directories. This is still product work, not merely wording cleanup, because the current labels fail to explain the process.

Only after the primary flow is clear and the certificate/preset surfaces are understandable should the shell reduction child plan begin to de-emphasize or relocate the harness-shaped inline editor. That plan should keep the product usable at every step, likely through a temporary hybrid period where preset-first setup becomes primary before deeper inline surfaces are reduced or moved into dedicated management dialogs. It must not remove the only remaining path for manual setup refinement that the spec still allows.

Finally, after the child plans land, run one live GUI walkthrough on a representative PDF and update the docs and acceptance notes so the repository’s written status matches the actual user experience.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Re-open the governing product review context before each child plan starts.

       sed -n '1,260p' docs/SPEC.md
       sed -n '1,220p' .tmp/gui_ux_review_2026-07-08.md

   Expect to see the explicit V1 flow and the recorded live GUI observations.

2. Execute the document usability child plans first.

       sed -n '1,260p' docs/ExecPlans/gui_document_review_usability_execplan.md
       sed -n '1,260p' docs/ExecPlans/gui_text_selection_mode_execplan.md

3. Execute the workflow/productization child plans next.

       sed -n '1,260p' docs/ExecPlans/gui_signing_flow_guidance_execplan.md
       sed -n '1,260p' docs/ExecPlans/gui_certificate_and_preset_clarity_execplan.md
       sed -n '1,260p' docs/ExecPlans/gui_preset_first_shell_reduction_execplan.md

4. After the children land, validate the complete GUI flow manually.

       .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf

   The expected result is that a user can visibly navigate pages, intentionally enter and use text-selection mode, understand how to choose a certificate or preset, place a signature with appropriate cursor/mode feedback, and follow the signing path without guessing what control comes next.

5. Reconcile docs and status after the live validation pass.

       rg -n "navigate pages|select/copy document text|Signature Preset|verify the signed result" docs/SPEC.md README.md docs/ARCHITECTURE.md

## Validation and Acceptance

This parent plan is successful only when the child plans collectively deliver an observable improvement to the live GUI, not just to the code. A novice should be able to launch the GUI with `foliaseal gui`, open a PDF, find the page-navigation controls without prior instruction, select and copy text through a visibly working interaction mode, understand the distinction between certificate and preset choices, place a signature with correct mode/cursor feedback, and follow the staged flow through save and verify without deciphering harness-era terminology.

Each child plan must carry its own tests and manual validation. The parent acceptance pass is the final human walkthrough. Run the live GUI on `artifacts/preview_sweep_assets/sweep_fixture.pdf` and confirm that the user-visible journey now resembles the V1 flow described in `docs/SPEC.md`. If any step still requires explanation from a developer, the parent plan is not done.

## Idempotence and Recovery

This plan is safe to revisit multiple times because it is orchestration and documentation, not a destructive migration. Child plans should be executed one at a time and kept narrow. If one child plan stalls or is reverted, leave the parent document updated so the dependency list and progress accurately show which slices remain open. Do not mark the parent done based on passing tests alone; repeat the live GUI walkthrough after any meaningful UX change.

## Artifacts and Notes

The primary evidence for why this plan exists is the GUI review note:

    .tmp/gui_ux_review_2026-07-08.md

The key product requirements it responds to are:

    docs/SPEC.md:83-93
    docs/SPEC.md:127-135
    docs/SPEC.md:255-256

The live GUI entrypoint used for validation is:

    .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf

## Interfaces and Dependencies

The relevant implementation modules are all under `src/foliaseal/presentation/qt/`. The top-level application frame is `app_frame.py`. The live document viewer behavior is concentrated in `viewer_widget.py` and the viewer workflow modules. The right-hand signing and review surface is split across `signing_workspace_sidebar.py`, `signing_workspace_properties_panel.py`, `visible_signature_setup_form.py`, `signing_shell.py`, and the workspace runtime/bridge helpers. Certificate creation and management dialogs live in `app_frame_certificate_management.py`. The child plans should prefer additive, user-visible changes and should update tests under `tests/unit/` plus any docs needed to keep `README.md` and `docs/ARCHITECTURE.md` truthful.

Revision note: 2026-07-11 / Codex
Updated the parent plan after the document-review and text-selection child plans landed so the progress list reflects the completed slices and identifies certificate/preset clarity as the next active recovery step.
