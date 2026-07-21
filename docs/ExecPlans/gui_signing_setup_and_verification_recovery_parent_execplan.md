# GUI signing setup and verification recovery parent plan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this parent plan is complete, a first-time user will be able to open a PDF, create or choose a signing certificate, create and save reusable signing setup objects, place a visible signature, review a clearly narrated readiness state, sign, reopen the result, and understand how to verify it and add another approval signature later if permitted. The user-visible gain is that FoliaSeal stops offering only an ad hoc current-document signing path and instead exposes the reusable-object workflow promised by `docs/SPEC.md`.

This parent plan exists because the missing product behavior spanned several related but separately reviewable GUI seams. The completed work now exposes a user-facing route for reusable appearance, placement, and preset objects plus an explicit post-sign verify story. The child ExecPlans remain the durable record of independently validated seams, while this plan records their final end-to-end product narrative and acceptance evidence.

## Child ExecPlan Dependencies

- [x] Reusable signing objects, certificate-selection semantics, confirmation/verification, and shell narration landed together in `8cc188c`.
- [x] Renderer-fidelity child `gui_reopened_pdf_renderer_fidelity_execplan.md` repaired the blank signed-PDF canvas without changing the established QtPdf geometry contract.
- [x] A full representative-PDF GUI walkthrough passed. Focused Qt coverage, renderer diagnostic tests, and the display-backed audit now cover both dialog interactions and the end-to-end flow.

## Progress

- [x] (2026-07-13 00:00Z) Audited the current GUI against `docs/SPEC.md` and wrote `.tmp/gui_user_flow_audit_2026-07-13.md` as an exact click-by-click attempted user procedure.
- [x] (2026-07-13 00:00Z) Wrote `.tmp/gui_findings_and_fix_plan_2026-07-13.md` to summarize confirmed GUI problems and a high-level SPEC-compliant fix direction.
- [x] (2026-07-13 00:00Z) Ran two independent review passes over the audit and findings: one code-surface review and one SPEC-compliance review, then folded their corrections back into the temp artifacts.
- [x] (2026-07-13 00:00Z) Wrote this parent ExecPlan plus the child ExecPlans for reusable signing objects, certificate-selection semantics, sign confirmation plus verification, and main-shell process narration.
- [x] (2026-07-18) Executed the four child plans in `8cc188c` with 163 focused tests, Ruff, and diff checks passing.
- [x] (2026-07-18) Re-ran the display-backed representative-PDF startup smoke audit and reconciled the architecture documentation; README required no capability change.
- [x] (2026-07-19) Completed the full display-backed user-flow audit: profile selection, confirmation, post-sign verification, and reopen are exercised end-to-end by `scripts/live_gui_parent_audit.py`.
- [x] (2026-07-19) Recorded and bounded the native-chooser audit limitation. Synthetic X11 typing is not a trustworthy way to drive the platform chooser; the final semantic Qt audit creates/selects the certificate and uses a narrowly injected non-native Qt save-dialog proxy only for output selection. This is an audit-driver limitation, not a product defect.
- [x] (2026-07-19) Completed the isolated semantic real-Qt route through certificate creation/selection, appearance/placement/preset save and re-selection, visible page drag, output selection, confirmation, signing, reopen, and verification messaging. The runner always closes its Qt windows.
- [x] (2026-07-19) Resolved reopened signed-PDF canvas fidelity: `PopplerPdfRenderBackend` supplies live viewer pixels while QtPdf remains the geometry source. The final audit's `09-reopened-and-verified.png` visibly contains the signed mark and verification state. Evidence: `/tmp/foliaseal-live-gui-parent-audit/audit.json` (`"status": "passed"`, nine checkpoints).
- [x] (2026-07-20) Ran the later certificate/preset UX audit independently: `/tmp/foliaseal-reconciliation-audit/audit.json` passed with twelve checkpoints, adding settings-directory browsing, appearance save, and profile-library clarity. This is additional evidence, not a revision of the historical nine-checkpoint audit above.

## Surprises & Discoveries

- Observation: the most severe GUI problem is not visual clutter but the lack of an exposed reusable-object workflow.
  Evidence: `.tmp/gui_user_flow_audit_2026-07-13.md` reaches a hard stop at the signature-preset save step because the preset-name field and save/delete controls exist in code but are not mounted into the visible layout.

- Observation: the current GUI is closer to an ad hoc current-document signing workflow than the V1 product story in `docs/SPEC.md`.
  Evidence: `.tmp/gui_findings_and_fix_plan_2026-07-13.md` reduces the observed flow to `Open -> Create/select certificate configuration -> Edit current document setup -> Place -> Sign`, which is materially narrower than the specified reusable-object and verify/reopen story.

- Observation: some earlier conclusions about the GUI needed tightening after review.
  Evidence: the code-surface reviewer confirmed that main-menu `Copy selected text` becomes enabled immediately after a PDF is opened, while the SPEC reviewer confirmed that default output-path suggestion is allowed by spec and that the larger release-bar gap is missing reusable-object and verify-story behavior, not merely ambiguous output wording.

- Observation: the agent-operated live audit can reach the real certificate-import dialog, but automated text injection is not a trustworthy substitute for the platform-native file chooser.
  Evidence: on 2026-07-19, an attempted import of the deterministic fixture `artifacts/generated_acceptance_assets/signed_acceptance_identity.p12` produced the visible error “Import file does not exist,” including when a lowercase `/tmp` symlink resolved correctly from the shell. The final audit creates and selects an isolated certificate and uses a bounded non-native Qt save-dialog proxy only for output selection. This documents an automation limitation rather than a product defect.

- Observation: the first complete functional audit exposed a preview/output fidelity defect on reopened signed PDFs; the repaired audit now shows the in-app visible mark after reopen.
  Evidence: pre-fix `/tmp/foliaseal-live-gui-parent-audit-fidelity-failure/audit.json` recorded a transparent QtPdf raster while Poppler rendered the retained signed output. `PopplerPdfRenderBackend` now owns live pixels, retains QtPdf geometry, and the passing `/tmp/foliaseal-live-gui-parent-audit/audit.json` records nine screenshots including `09-reopened-and-verified.png`.

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

- Decision: record GUI-audit automation failures as audit evidence and always close all FoliaSeal windows and dialogs before changing approaches.
  Rationale: a failed synthetic interaction neither proves a product defect nor permits stale UI state to leak into the next attempt. Capturing the exact visible error makes the retry reproducible while cleanup keeps the desktop and persistent state controlled.
  Date/Author: 2026-07-19 / Codex

- Decision: keep this parent plan open and create a dedicated renderer-fidelity child slice for the blank reopened canvas.
  Rationale: external output evidence proves signing is correct, while the in-app viewer violates the product's preview/output trust requirement. Treating successful signing or verification text as sufficient would conceal a user-visible defect.
  Date/Author: 2026-07-19 / Codex

- Decision: close the renderer-fidelity child by using Poppler only for the live interactive viewer's page pixels and retaining QtPdf for page geometry, rotation, coordinate transforms, canonical previews, and Phase 2/Phase 3 evidence.
  Rationale: the defect was limited to QtPdf rasterisation of reopened signed PDFs; geometry was already correct. The narrow split repairs visible trust without expanding canonical-preview or harness scope without evidence.
  Date/Author: 2026-07-19 / Codex

- Decision: make the semantic real-Qt audit the parent acceptance artifact and keep its evidence ephemeral under `/tmp`.
  Rationale: it exercises visible mounted FoliaSeal controls, asserts reopened visual fidelity, and closes all top-level Qt windows in `finally`. Its non-native save-dialog proxy is confined to the environment-specific native-chooser edge.
  Date/Author: 2026-07-19 / Codex

## Outcomes & Retrospective

The recovery completed its reusable-object, certificate-selection, confirmation/verification, shell-narration, and renderer-fidelity child slices. The final acceptance audit creates/selects an isolated certificate, saves/reselects appearance/placement/preset objects, drags a visible signature, selects output, confirms, signs, reopens, and reviews verification. It passed with nine screenshots plus retained signed output under `/tmp/foliaseal-live-gui-parent-audit`; `finally` closes all top-level Qt windows. Focused renderer/app-frame/viewer checks (63 tests), Ruff, and diff checks passed. The original synthetic native-chooser typing failure remains documented as bounded audit-driver friction, not as an unresolved GUI defect.

## Context and Orientation

FoliaSeal is a Linux desktop PDF signing application with a Qt GUI. The frozen product requirements live in `docs/SPEC.md`. That file defines the V1 story as: open a PDF, review it, choose or create a signing certificate, choose or refine a signing setup, place a visible signature, preview readiness, sign, save, reopen, verify, and add another approval signature later if document permissions allow it. The current code structure is described in `docs/ARCHITECTURE.md`, but this plan is written to stand alone.

The current GUI entrypoint is `src/foliaseal/presentation/qt/app_frame.py::launch_qt_app_frame`. The top-level frame installs `File`, `Edit`, and `Settings` menus. When a PDF is opened, `src/foliaseal/presentation/qt/app_frame_workspace_open.py` creates a `ViewerWorkflow` and a `SigningDraftWorkflow`, then boots the live signing shell under `src/foliaseal/presentation/qt/`. The main right-hand shell surfaces now live mostly in `signing_workspace_sidebar.py` and `signing_workspace_properties_panel.py`, while current-document appearance and placement editing lives in `visible_signature_setup_form.py` and the modal refinement path opened by `SignaturePropertiesPanel.open_refinement_dialog()`.

The temp audit `.tmp/gui_user_flow_audit_2026-07-13.md` remains the historical baseline that exposed the reusable-object and reopen/verify gaps. The completed product path now supports creating/selecting a certificate, refining a current-document setup, saving/reselecting reusable appearance/placement/preset objects, placing a signature, confirming, signing, reopening, and reviewing verification. The final runnable acceptance evidence is `scripts/live_gui_parent_audit.py` with artifacts under `/tmp/foliaseal-live-gui-parent-audit`.

The relevant terms are simple but must stay precise. A `Certificate Configuration` is the user-facing saved signing identity backed by a managed certificate. An `Appearance Profile` is a reusable visible-signature look. A `Placement Profile` is a reusable placement template. A `Signature Preset` composes references to those reusable objects. The completed GUI exposes creation and selection routes for these objects through the contextual refinement and management surfaces.

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

The historical audit artifact that motivated this plan is:

    .tmp/gui_user_flow_audit_2026-07-13.md

The reviewed findings and high-level fix direction are:

    .tmp/gui_findings_and_fix_plan_2026-07-13.md

The interactive GUI entrypoint remains:

    .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf

The completed bounded display-backed acceptance command is:

    DISPLAY=:0 timeout 120s .venv/bin/python scripts/live_gui_parent_audit.py --artifacts-dir /tmp/foliaseal-live-gui-parent-audit

Its `audit.json`, nine screenshots, and retained `signed-output.pdf` are temporary evidence; the runner closes every top-level Qt window in `finally`.

The key spec anchors are:

    docs/SPEC.md:43-58
    docs/SPEC.md:120-139
    docs/SPEC.md:253-312

## Interfaces and Dependencies

The relevant implementation modules are all under `src/foliaseal/presentation/qt/` plus the rendering adapters under `src/foliaseal/infra/render/`. The top-level frame and menus are in `app_frame.py` and `app_frame_workspace_open.py`; `FoliaSealAppFrame` defaults its live viewer to `PopplerPdfRenderBackend`, which preserves `QtPdfRenderBackend` for geometry. Certificate creation and management dialogs are in `app_frame_certificate_management.py`. The main signing shell is composed through `signing_workspace_composition.py`, `signing_workspace_sidebar.py`, `signing_workspace_properties_panel.py`, `visible_signature_setup_form.py`, `signing_action_coordinator.py`, and the runtime/bridge helpers such as `signing_workspace_action_bridge.py` and `signing_workspace_runtime.py`. Reusable-object semantics below Qt live in `src/foliaseal/application/signature_properties_coordinator.py`, `src/foliaseal/application/signing_setup_session.py`, and the persistent schema/store modules under `src/foliaseal/infra/config/`.

The allowed change classes for the child plans are primarily behavior change plus focused evidence refresh. Documentation/status updates should follow the behavior slices and should not be mixed into unrelated GUI refactors unless the `Decision Log` in the relevant child plan explains why a mixed slice is unavoidable.

Revision note: 2026-07-13 / Codex
Created this parent plan from the reviewed GUI audit because the remaining SPEC gaps were concentrated in reusable signing objects, certificate-selection semantics, sign confirmation plus verification, and explicit process narration.

Revision note: 2026-07-19 / Codex
Closed the parent after the renderer-fidelity child, focused checks, and the nine-checkpoint semantic real-Qt audit passed. The live app now uses Poppler pixels with QtPdf geometry; canonical preview and Phase 2/Phase 3 remain intentionally QtPdf-scoped. Native-chooser automation friction is recorded as a bounded audit-driver limitation, and the runner cleans up all top-level Qt windows.
