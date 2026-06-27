# Tighten The Signing Workspace Apply-Changes Control-Issue Path

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the signing workspace properties panel will still own form-build validation for `apply_changes()`, but that path will be explicit and easier to reason about. Invalid visible-signature form state should still surface as the existing `signature_appearance_invalid` validation issue, still preserve preview rendering, and still leave later setup-session calls using one consistent `_control_issue` lifecycle instead of a hand-rolled branch inside `apply_changes()`.

The user-visible proof is unchanged behavior with a tighter shell-local seam. The properties panel should continue to show the correct validation text and preview after invalid form input, while the tests prove that invalid input, recovery, and later refreshes all pass through one predictable path.

## Child ExecPlan Dependencies

- [x] (2026-06-27 00:00Z) No child ExecPlans are required for this bounded Qt-panel slice.

## Progress

- [x] (2026-06-27 00:00Z) Re-read the current panel path in `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py`, the current architecture/spec wording, and the existing shell tests around `apply_changes()`, readiness text, and `_control_issue`.
- [x] (2026-06-27 00:00Z) Used the required `explorer-light` dev-loop audit to confirm the next hybrid slice: tighten the panel-local `apply_changes()` / `_control_issue` path without widening `SigningSetupSession` or `DefaultSignaturePropertiesCoordinator`.
- [x] (2026-06-27 00:00Z) Wrote this ExecPlan before implementation.
- [x] (2026-06-27 00:00Z) Added failing shell-surface coverage proving two missing behaviors: deeper session `ValueError` must not be rewritten as a form issue, and `_control_issue` must clear on the next successful apply and stay clear across a later refresh.
- [x] (2026-06-27 00:00Z) Refactored `SignaturePropertiesPanel.apply_changes()` so only `build_draft()` `ValueError` becomes `signature_appearance_invalid`, and introduced one shared `_render_setup_state(...)` choke point for success, invalid apply, and explicit preview refresh.
- [x] (2026-06-27 00:00Z) Ran focused validation: `.venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py -k 'apply_changes or set_signature_appearance_uses_setup_session_entrypoint or validation_text'`, `.venv/bin/python -m ruff check src/foliaseal/presentation/qt/signing_workspace_properties_panel.py tests/unit/test_qt_signing_shell.py`, and `git diff --check` all passed.
- [x] (2026-06-27 00:00Z) Completed the required `explorer-light` compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this ExecPlan. The first review flagged the still-split render path and missing recovery coverage; both were fixed in-slice, and the second review found no remaining code or architecture drift.
- [ ] Prepare the slice for the required commit step in the larger dev-loop.

## Surprises & Discoveries

- Observation: the deeper setup boundary is no longer the problem; the remaining hybrid edge is panel-local state choreography around `_control_issue`.
  Evidence: `SigningSetupSession.set_signature_appearance()` already delegates to the coordinator, while `SignaturePropertiesPanel.apply_changes()` still catches form `ValueError`, constructs `signature_appearance_invalid`, and re-enters the render path through `refresh_preview()`.

## Decision Log

- Decision: keep invalid-draft mapping inside the Qt panel for this slice.
  Rationale: the invalid-draft exception currently comes from `QtVisibleSignatureSetupForm.build_draft()`, which is a presentation-layer concern. Pulling that into the application boundary would blur the shell/session split and widen the slice beyond what the explorer recommended.
  Date/Author: 2026-06-27 / Codex

- Decision: prefer a behavior-preserving refactor over a new public interface.
  Rationale: the problem is the shape of the control-flow path, not the caller contract. The panel API should stay stable while the internal path becomes more explicit and easier to test.
  Date/Author: 2026-06-27 / Codex

## Outcomes & Retrospective

Implementation, focused validation, and compliance review are complete. The main improvement is boundary correctness rather than new user-facing behavior: invalid form input is still surfaced as `signature_appearance_invalid`, but downstream `ValueError`s are no longer silently mislabeled as form issues, and success/error/refresh rendering now converges through one helper path. The final compliance pass confirmed no `docs/ARCHITECTURE.md` or `docs/SPEC.md` changes were required for this slice.

## Context and Orientation

The relevant module is `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py`. This module owns the shell-local `SignaturePropertiesPanel` class, including the visible-signature form, validation text, preview rendering, preset/certificate control wiring, and the `_control_issue` field that threads panel-local validation state through later setup-session loads.

The deeper setup boundary below it is already in better shape. `src/foliaseal/application/signing_setup_session.py` wraps common setup orchestration and delegates application rules to `src/foliaseal/application/signature_properties_coordinator.py`. Those modules already own selection flows, session-local password retry, preset operations, and appearance/visible-setup application. This slice must not widen their responsibilities.

The remaining local concentration is `SignaturePropertiesPanel.apply_changes()`. Today it clears `_control_issue`, tries to build a form draft, passes that draft to `SigningSetupSession.apply_visible_setup(...)`, and if `QtVisibleSignatureSetupForm.build_draft()` raises `ValueError`, it constructs a `SigningDraftValidationIssue` with code `signature_appearance_invalid`, stores that as `_control_issue`, and refreshes preview state through `refresh_preview()`. The path is short but ad hoc: success and invalid-input flows use different render entrypoints even though both end up relying on `_apply_coordinator_state(...)` and later panel methods reuse `_control_issue` through `load()` calls.

The main tests live in `tests/unit/test_qt_signing_shell.py`, especially `test_signing_shell_apply_changes_maps_form_value_error_to_validation_issue` plus nearby tests that inspect `validation_text()`, readiness state, preset clearing, and the presence of `_control_issue`.

This slice must not widen into:

- `src/foliaseal/application/signing_setup_session.py`
- `src/foliaseal/application/signature_properties_coordinator.py`
- certificate-password prompting or selection flows
- preview layout/rendering semantics
- signing action, workspace interaction, or app-frame seams

## Plan of Work

First, strengthen the shell-surface test coverage in `tests/unit/test_qt_signing_shell.py`. Add one focused test that proves the `_control_issue` lifecycle more directly than the current invalid-draft test. Suitable targets include proving that a successful `apply_changes()` clears an earlier invalid `_control_issue`, or proving that invalid and valid paths both drive the same panel render/update entrypoint. Keep the test at the panel public surface; do not test private helper names directly.

Second, refactor `SignaturePropertiesPanel.apply_changes()` in `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py` so the method has one explicit successful-apply path and one explicit invalid-draft path, with shared rendering/notification behavior kept in one place. A small private helper is acceptable if it removes duplicate state-application/preview-refresh logic or makes `_control_issue` reset and reuse clearer.

Third, rerun the focused shell tests and panel-adjacent smoke coverage. If the refactor changes the architecture wording in a meaningful way, update `docs/ARCHITECTURE.md`; otherwise keep documentation changes limited to this ExecPlan’s progress and outcomes.

Finally, perform the required compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this ExecPlan, record any findings, fix them in-slice if they are narrow, and prepare the resulting change for the required commit step in the broader dev-loop.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Edit these files:

    src/foliaseal/presentation/qt/signing_workspace_properties_panel.py
    tests/unit/test_qt_signing_shell.py
    docs/ExecPlans/signing_workspace_apply_changes_control_issue_execplan.md
    docs/ARCHITECTURE.md   # only if contract wording changes materially

Suggested order:

1. Add one failing shell-level behavior test for the `_control_issue` lifecycle.
2. Refactor `apply_changes()` minimally to make success and invalid-input handling explicit.
3. Re-run focused shell tests and hygiene.
4. Perform the required compliance review and update docs only if needed.

Run focused validation as the slice progresses:

    .venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py -k 'apply_changes or set_signature_appearance_uses_setup_session_entrypoint or validation_text'
    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/signing_workspace_properties_panel.py tests/unit/test_qt_signing_shell.py
    git diff --check

After the first implementation pass, run the required compliance review against at least:

    docs/ARCHITECTURE.md
    docs/SPEC.md
    docs/ExecPlans/signing_workspace_apply_changes_control_issue_execplan.md

## Validation and Acceptance

This slice is accepted when all of the following are true:

- `SignaturePropertiesPanel.apply_changes()` still maps invalid form state to `signature_appearance_invalid`.
- the `_control_issue` lifecycle across invalid apply, successful apply, and later refreshes is covered more directly than before.
- the panel still renders preview and validation state through one coherent path without duplicated ad hoc refresh behavior.
- no session/coordinator responsibilities are widened in this slice.
- focused shell tests pass.
- any architecture wording affected by the refactor is reconciled.

Observable proof is a focused shell test run where the new tracer-bullet test fails before the refactor and passes after it, while the existing invalid-draft and neighboring validation tests remain green.

## Idempotence and Recovery

This is a behavior-preserving shell-local refactor and is safe to retry. If the first pass introduces both old and new `_control_issue` handling paths, remove the duplicate branch before considering the slice complete. If the refactor reveals that the form error should actually become an application-layer contract, stop and split that boundary change into a later ExecPlan instead of widening this one implicitly.

## Artifacts and Notes

Capture and keep concise:

- the focused shell test run proving the strengthened `_control_issue` lifecycle
- any compliance finding about stale architecture wording

## Interfaces and Dependencies

This slice uses the `In-process` dependency category.

At the end of the slice, the panel-facing surface should remain approximately:

    class SignaturePropertiesPanel:
        def apply_changes(self) -> SigningDraftPreview: ...
        def refresh_preview(self) -> SigningDraftPreview: ...
        def validation_text(self) -> str: ...
        def is_ready_to_sign(self) -> bool: ...

The contract change is internal, not public: `apply_changes()` should use one explicit control-flow shape for successful form application and invalid form input while keeping `_control_issue` as the panel-local validation token that is passed back through setup-session loads.

Revision note: Created on 2026-06-27 by Codex after the required dev-loop explorer selected the next hybrid slice: tighten the Qt-panel `apply_changes()` / `_control_issue` path without widening the deeper setup boundary.

Revision note: Updated on 2026-06-27 by Codex after the first red-green pass to record the new session-`ValueError` guard test, the invalid-then-recover lifecycle test, and the shared `_render_setup_state(...)` panel render path.
