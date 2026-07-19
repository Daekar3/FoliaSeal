# Complete reusable setup, confirmation, and narrated verification

This ExecPlan is a living document maintained under `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this work a person can save an explicit signature preset that references named appearance and placement profiles, manage those reusable objects in Settings, understand that choosing a certificate activates it for the current PDF, review a final signing summary before the irreversible action, reopen the result, and receive honest local-verification and next-signature guidance. The final proof is the exact GUI audit from `.tmp/gui_user_flow_audit_2026-07-13.md` against a representative PDF.

## Child ExecPlan Dependencies

- [x] Appearance-profile saving is implemented and tested.
- [x] Placement-profile saving is implemented and tested.
- [x] Explicit preset composition and Settings library.
- [x] Certificate-selection semantics.
- [x] Confirmation, verification, and narrated shell flow.

## Progress

- [x] (2026-07-17 00:00Z) Re-explored the live checkout and identified that current preset saving synthesizes profiles instead of composing saved profile references.
- [x] (2026-07-18 00:00Z) Revalidated the next milestone: reference-only preset composition plus minimal Settings management is the prerequisite for certificate confirmation and narration.
- [x] (2026-07-18) Implemented and focused-tested preset composition plus Settings management.
- [x] (2026-07-18) Implemented and focused-tested immediate certificate activation semantics.
- [x] (2026-07-18) Implemented and focused-tested confirmation, reopen/verification guidance, and shell narration.
- [x] (2026-07-18) Completed code/SPEC/architecture reconciliation and the focused integrated suite (163 tests).
- [x] (2026-07-18) Performed display-backed startup audit against the representative PDF. The initial actual-data run exposed the legacy combined-profile migration defect; after adding migration, the workspace opened successfully with the actual saved catalog. The focused Qt suite covers the remaining control interactions because synthetic X-session menu targeting was not stable.

## Surprises & Discoveries

- Observation: independent profile persistence is already present, but `SaveCurrentPreset` still derives new component profiles from the active draft.
  Evidence: `DefaultSignaturePropertiesCoordinator._save_current_preset()` calls `_build_current_preset()` rather than resolving explicit saved profile references.

## Decision Log

- Decision: keep the changes as dependent vertical milestones despite executing under one integration plan.
  Rationale: the confirmation must describe actual saved preset and certificate semantics, so later UI cannot be truthfully implemented first.
  Date/Author: 2026-07-17 / Codex
- Decision: prohibit the existing implicit current-draft preset save path from creating component profiles.
  Rationale: SPEC requires a preset to store references to separately named reusable objects, and a confirmation cannot truthfully identify the active setup otherwise.
  Date/Author: 2026-07-18 / Codex

## Outcomes & Retrospective

All three implementation milestones and their focused automated evidence are
complete. The integrated acceptance audit is intentionally left open: the current
execution environment did not provide a display-backed GUI session, so it would be
incorrect to report the audit as passed.

## Context and Orientation

`SignaturePresetCatalogStore` persists independent appearance and placement profiles. `DefaultSignaturePropertiesCoordinator` is the application boundary between the Qt `SignaturePropertiesPanel` and that store. `FoliaSealAppFrame` owns Settings menus and certificate dialogs. `SigningActionCoordinator` owns signing-action state, while `SigningWorkspaceActionBridge` and `SigningWorkspaceSidebar` render and route shell-edge dialog behavior. A signature preset must reference the stable identifiers of existing reusable profiles; it must not copy a document-specific draft into replacement component objects.

## Plan of Work

First extend the coordinator/session/catalog commands to compose a preset from selected saved profile names and, where selected, a certificate configuration. Add a refinement-dialog preset action that asks for the preset name and chosen component profiles, and add a Settings management surface following certificate management for inspect, rename, and delete actions. Preserve reference guards on profile deletion and refresh the live selector after changes.

Next remove the hidden certificate `Use for this PDF` affordance and make the helper text say that selection applies immediately. Keep a single state transition and cover selection, password prompting, cancellation, and errors.

Finally introduce a confirmation transition before signing. The confirmation surface must display output path, active certificate, saved preset or custom setup, readiness/preview information, and the irreversible effect. On success retain reopen and local verification guidance, including how to add a permitted approval signature. Centralize stage narration so sidebar labels are derived from one truthful flow summary.

## Concrete Steps

Run from `/home/daekar/FoliaSeal` after each vertical behavior:

    .venv/bin/pytest -q tests/unit/test_signature_preset_storage.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py
    .venv/bin/ruff check src tests/unit
    .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf

## Validation and Acceptance

In the GUI, save `Contract approval` appearance and `Bottom right` placement, save a preset using both, select it from the quick selector, then inspect and manage it through Settings. Select a certificate and see immediate activation wording. Choose an output, review the final summary, confirm signing, reopen the output, and see the local verification/next-approval guidance. Re-run every step of `.tmp/gui_user_flow_audit_2026-07-13.md` and record any remaining gap.

## Idempotence and Recovery

Name prompts may be cancelled without mutation. Duplicate saves must not overwrite without explicit consent. Reference-protected profile deletion must explain the dependent preset. A failed/cancelled confirmation must not submit a signing request. Preserve existing dirty work; use patch-level staging only after each coherent milestone is validated.

## Artifacts and Notes

Only behavior changes, focused tests, evidence refresh, and documentation/status updates belong to this recovery tranche. Do not mix unrelated shell refactors. The prior appearance/placement worktree changes remain the prerequisite baseline and must not be reset.

## Interfaces and Dependencies

Use `SignaturePresetCatalogStore` as the sole profile persistence boundary. Keep Qt from importing storage directly. The coordinator must expose explicit preset-composition and profile-management commands; the session wraps them for presentation. `SigningActionCoordinator` must own the confirmation state transition, while Qt bridge code only displays the confirmation and returns the user decision.

Revision note: 2026-07-17 / Codex
Created after the required dev-loop exploration for Steps 3–5 established the live dependency chain.
