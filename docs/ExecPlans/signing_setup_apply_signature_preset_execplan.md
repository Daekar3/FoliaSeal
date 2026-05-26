# Add explicit preset-application entrypoint to the signing setup boundary

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

`/home/daekar/FoliaSeal/.agents/skills/write-execplan/PLANS.md` is the governing format reference for this document and this file must be maintained in accordance with it.

## Purpose / Big Picture

The signing setup workflow now exposes an explicit application-layer entrypoint for applying a signature preset, just as it already does for applying the visible-signature draft. The user-visible behavior remains unchanged: selecting a preset still updates the current setup, partial presets still preserve an active certificate when they do not define one, and preset-selection errors still restore the selector state cleanly. The visible benefit is internal clarity: the shell no longer assembles the normal preset-application command itself for the common nonblank selection path.

## Child ExecPlan Dependencies

- [x] No child ExecPlans are planned for this slice.

## Progress

- [x] (2026-05-25) Confirmed the coordinator protocol and default implementation expose `apply_signature_preset(...)` alongside `load()`, `apply_visible_setup()`, and `reconcile()`.
- [x] (2026-05-25) Confirmed `SignaturePropertiesPanel._on_signature_preset_selected()` uses `apply_signature_preset(...)` for nonblank selections and preserves `ClearSelectedSignaturePreset()` for blank selections.
- [x] (2026-05-25) Added focused coordinator and shell regression coverage for the new preset entrypoint, including nonblank dispatch, blank-selection clearing, error reload behavior, partial-preset certificate preservation, control-issue folding, and certificate-bearing preset application.
- [x] (2026-05-25) Updated `docs/ARCHITECTURE.md` and this ExecPlan to match the completed boundary.
- [x] (2026-05-25) Captured final validation evidence from `pytest`, `ruff check`, and `git diff --check` after the follow-up compliance fixes.

## Surprises & Discoveries

- Observation: The preset path is already mostly application-owned; the shell only needed the explicit public wrapper for the common nonblank selection path.
  Evidence: `DefaultSignaturePropertiesCoordinator` exposes `apply_signature_preset(...)` over the existing preset mutation logic, and `SignaturePropertiesPanel._on_signature_preset_selected()` now calls it directly for nonblank selections while blank selections still use the clear-selection command.

- Observation: The visible-signature setup boundary did not need to change to complete this slice.
  Evidence: The coordinator already had the adjacent `load()`, `apply_visible_setup()`, and `reconcile()` entrypoints, so the preset-application addition stayed narrow and did not require Qt form changes.

- Observation: The fake Qt preset combo emits multiple selection-related signals for one `setCurrentText(...)` call, so direct signal-count assertions are brittle in shell tests.
  Evidence: The shell tests had to assert stable behavior through the handler and resulting state rather than exact callback counts when verifying preset-selection dispatch and clear-selection behavior.

## Decision Log

- Decision: Keep blank preset selection on the existing `ClearSelectedSignaturePreset()` command path.
  Rationale: Clearing the selected preset without applying a new one is a different state transition from applying a named preset. Collapsing them into one entrypoint would widen the slice and obscure the current explicit behavior.
  Date/Author: 2026-05-25 / Codex

- Decision: Expose `apply_signature_preset(...)` as the public entrypoint for nonblank preset selections.
  Rationale: The coordinator already owns the real preset application logic, so the shell should call that boundary directly instead of assembling the preset command itself.
  Date/Author: 2026-05-25 / Codex

- Decision: Leave `src/foliaseal/presentation/qt/visible_signature_setup_form.py` unchanged in this slice.
  Rationale: The form is not involved in preset application orchestration. Changing it here would not deepen the chosen seam.
  Date/Author: 2026-05-25 / Codex

## Outcomes & Retrospective

The signing setup boundary now exposes `load()`, `apply_visible_setup()`, `apply_signature_preset()`, and `reconcile()` in the coordinator. `SignaturePropertiesPanel._on_signature_preset_selected()` delegates nonblank selections directly to `apply_signature_preset(...)`, blank selections still use `ClearSelectedSignaturePreset()`, and error handling still reloads current coordinator state before rendering resumes.

This kept the slice narrow. The existing preset mutation and partial-certificate preservation behavior remained in the coordinator, the Qt form contract stayed unchanged, and the shell stopped owning the normal nonblank preset-application command assembly.

Validation evidence for the completed slice:

- `pytest tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py` -> `93 passed`
- `ruff check src/foliaseal/application/signature_properties_coordinator.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py` -> `All checks passed!`
- `git diff --check` -> no output

## Context and Orientation

The signing setup workflow now has three explicit public entrypoints in practice: `load()`, `apply_visible_setup(...)` for the visible-signature draft, and `apply_signature_preset(...)` for the nonblank preset-selection path. Preset application is owned by `src/foliaseal/application/signature_properties_coordinator.py`, which handles catalog lookup, optional certificate material resolution, partial preset semantics, selected-state reconciliation, and workflow mutation. `src/foliaseal/presentation/qt/signing_shell.py` now calls that entrypoint directly for the common nonblank selector path.

This slice makes the setup boundary more symmetrical. The shell says “apply this preset” directly for the common selection path, while blank selection still uses `ClearSelectedSignaturePreset()`. The current error flow remains intact: show the error, reload the current coordinator state, and keep rendering driven by returned state.

The slice must preserve `docs/SPEC.md` requirements, especially the partial preset behavior:

- loading a preset that omits a certificate reference leaves the current certificate selection untouched if one is already active;
- the selected preset name and visible setup state still update normally;
- readiness and validation text still come from coordinator state.

## Plan of Work

First, update `src/foliaseal/application/signature_properties_coordinator.py`. Extend the `SignaturePropertiesCoordinator` protocol with `apply_signature_preset(selected_name, *, passphrase=None, control_issue=None) -> SignaturePropertiesViewState`. Implement the method on `DefaultSignaturePropertiesCoordinator` as a thin wrapper over the existing preset-application helper so it preserves the current workflow mutation, optional certificate application, partial preset rules, and returned view-state format. Do not remove or weaken `reconcile(...)`; other preset-related actions still belong there.

Second, update `src/foliaseal/presentation/qt/signing_shell.py`. In `SignaturePropertiesPanel._on_signature_preset_selected()`, keep the empty-selection `ClearSelectedSignaturePreset()` path exactly as it is. For nonblank selections, replace direct construction of `ApplySignaturePreset(...)` with the new coordinator method. Preserve the current `SignaturePropertiesCoordinatorError` handling, including the reload path through `_coordinator.load(...)` and the existing user-visible error reporting.

Third, update tests. In `tests/unit/test_signature_properties_coordinator.py`, add a direct wrapper test for `apply_signature_preset(...)` that proves preset selection updates returned state and preserves an active certificate for a partial preset. In `tests/unit/test_qt_signing_shell.py`, add focused shell coverage that the preset-selection path uses the explicit coordinator entrypoint without changing visible behavior. Keep the existing preset-selection behavior tests as regression coverage rather than replacing them.

Fourth, update `docs/ARCHITECTURE.md` so the signature-properties coordinator contract names `apply_signature_preset(...)` alongside `load()`, `apply_visible_setup()`, and `reconcile()`. Then update this ExecPlan so every living section reflects the actual implementation and validation outcomes.

## Concrete Steps

Work from `/home/daekar/FoliaSeal`.

1. Edit `src/foliaseal/application/signature_properties_coordinator.py` to add `apply_signature_preset(...)` to the protocol and implementation.
2. Edit `src/foliaseal/presentation/qt/signing_shell.py` so `SignaturePropertiesPanel._on_signature_preset_selected()` uses the explicit preset-application entrypoint for nonblank selections.
3. Edit `tests/unit/test_signature_properties_coordinator.py` and `tests/unit/test_qt_signing_shell.py` to cover the new public path.
4. Edit `docs/ARCHITECTURE.md` and then update this ExecPlan.
5. Run:

       pytest tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py
       ruff check src/foliaseal/application/signature_properties_coordinator.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py
       git diff --check

Expected evidence after completion:

       ... passed
       All checks passed!

## Validation and Acceptance

Acceptance is behavior-preserving. The slice is complete because:

- applying a signature preset through the new coordinator method updates selected preset state and preserves partial-preset certificate behavior exactly as before;
- `SignaturePropertiesPanel._on_signature_preset_selected()` still keeps blank selection on the clear-selection path and still uses the same error-reload behavior on failures;
- focused coordinator and shell tests now cover both partial and certificate-bearing preset wrapper paths, nonblank dispatch, blank-selection clearing, and error reload behavior;
- `pytest`, `ruff check`, and `git diff --check` all pass after the follow-up compliance fixes.

## Idempotence and Recovery

This slice is safe to repeat. Re-running tests and lints is idempotent. If the new entrypoint causes stale preset selector state, recover by routing UI refresh through `_apply_coordinator_state(...)` after reload rather than duplicating preset-selection cleanup in the shell. If partial preset behavior changes unexpectedly, restore the existing `_apply_signature_preset(...)` workflow path and keep the wrapper thin.

## Artifacts and Notes

Expected key code shape after implementation:

    class SignaturePropertiesCoordinator(Protocol):
        def load(...): ...
        def apply_visible_setup(...): ...
        def apply_signature_preset(...): ...
        def reconcile(...): ...

    class DefaultSignaturePropertiesCoordinator:
        def apply_signature_preset(...):
            self._apply_signature_preset(
                ApplySignaturePreset(
                    selected_name=selected_name,
                    passphrase=passphrase,
                )
            )
            return self.load(control_issue=control_issue)

The exact implementation may validate the selected name before wrapping it, but it must preserve the same state transition and returned view-state contract as the current command path.

## Interfaces and Dependencies

The public application boundary in `src/foliaseal/application/signature_properties_coordinator.py` must expose:

    class SignaturePropertiesCoordinator(Protocol):
        def load(
            self,
            *,
            control_issue: SigningDraftValidationIssue | None = None,
        ) -> SignaturePropertiesViewState: ...

        def apply_visible_setup(
            self,
            draft: VisibleSignatureSetupDraft,
            *,
            control_issue: SigningDraftValidationIssue | None = None,
        ) -> SignaturePropertiesViewState: ...

        def apply_signature_preset(
            self,
            selected_name: str,
            *,
            passphrase: str | None = None,
            control_issue: SigningDraftValidationIssue | None = None,
        ) -> SignaturePropertiesViewState: ...

        def reconcile(
            self,
            command: SignaturePropertiesCommand,
            *,
            control_issue: SigningDraftValidationIssue | None = None,
        ) -> SignaturePropertiesViewState: ...

`QtVisibleSignatureSetupForm` remains outside this slice. Blank preset selection continues to use `ClearSelectedSignaturePreset()` through `reconcile(...)`, and certificate/preset save-delete-refresh flows remain on explicit command paths.

Revision note: created on 2026-05-25 to implement the next narrow slice of the signing-setup hybrid after the explicit `apply_visible_setup(...)` entrypoint landed.
