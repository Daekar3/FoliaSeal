# Add explicit visible-setup entrypoint to the signing setup boundary

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

`/home/daekar/FoliaSeal/.agents/skills/write-execplan/PLANS.md` is the governing format reference for this document and this file must be maintained in accordance with it.

## Purpose / Big Picture

After this change, the signing setup workflow will have an explicit application-layer entrypoint for the most common product action: applying the current visible-signature setup draft. The user-visible behavior should stay the same, but the code will more clearly separate the Qt form from the application logic that mutates the signing draft. A contributor should be able to prove the change by running the existing signing-shell and coordinator tests and seeing that preset clearing, validation text, and preview state all behave exactly as before.

## Child ExecPlan Dependencies

- [x] No child ExecPlans are planned for this slice.

## Progress

- [x] (2026-05-25) Reviewed the current signing setup boundary, including `src/foliaseal/application/signature_properties_coordinator.py`, `src/foliaseal/presentation/qt/signing_shell.py`, `src/foliaseal/presentation/qt/visible_signature_setup_form.py`, `docs/SPEC.md`, and `docs/ARCHITECTURE.md`.
- [x] (2026-05-25) Gathered an `explorer-light` report confirming that the safest first slice is an explicit `apply_visible_setup(...)` coordinator entrypoint with no Qt form changes.
- [x] (2026-05-25) Added the explicit coordinator entrypoint and updated the protocol surface in `src/foliaseal/application/signature_properties_coordinator.py`.
- [x] (2026-05-25) Rewired `SignaturePropertiesPanel.apply_changes()` in `src/foliaseal/presentation/qt/signing_shell.py` to use the explicit entrypoint while preserving current validation folding and preview refresh behavior.
- [x] (2026-05-25) Added or updated focused unit tests in `tests/unit/test_signature_properties_coordinator.py` and `tests/unit/test_qt_signing_shell.py`.
- [x] (2026-05-25) Updated `docs/ARCHITECTURE.md` and this ExecPlan to reflect the completed boundary change.
- [x] (2026-05-25) Ran focused validation, recorded outcomes here, and completed the slice.

## Surprises & Discoveries

- Observation: The existing coordinator already owns the real visible-setup mutation logic through `ApplyVisibleSignatureSetup`; the first slice is mostly API clarification rather than new behavior.
  Evidence: `DefaultSignaturePropertiesCoordinator.reconcile()` already dispatches `ApplyVisibleSignatureSetup`, and `SignaturePropertiesPanel.apply_changes()` already sends that command after building a draft from the Qt form.

- Observation: The new public entrypoint did not require any Qt form contract change.
  Evidence: `SignaturePropertiesPanel.apply_changes()` now calls `DefaultSignaturePropertiesCoordinator.apply_visible_setup()` directly, while the form still only loads and rebuilds `VisibleSignatureSetupDraft` values.

## Decision Log

- Decision: Keep this slice behavior-preserving and avoid modifying `src/foliaseal/presentation/qt/visible_signature_setup_form.py`.
  Rationale: The form already behaves like the intended editor port with stable `load(...)`, `build_draft()`, and `set_placement_enabled(...)` operations. Changing it now would widen the slice without moving the chosen boundary forward.
  Date/Author: 2026-05-25 / Codex

- Decision: Add a dedicated public `apply_visible_setup(...)` method instead of replacing `reconcile(...)`.
  Rationale: Certificate, preset, save/delete, and catalog operations still benefit from explicit command objects. The visible-signature setup path is the one common operation that benefits from a smaller, more direct entrypoint.
  Date/Author: 2026-05-25 / Codex

- Decision: Keep `apply_visible_setup(...)` as a thin wrapper over the existing workflow mutation path.
  Rationale: The slice is about making the shell/coordinator boundary explicit without altering preset clearing, validation folding, or preview refresh semantics.
  Date/Author: 2026-05-25 / Codex

## Outcomes & Retrospective

The signing setup boundary now exposes `apply_visible_setup(...)` as a public coordinator entrypoint, and `SignaturePropertiesPanel.apply_changes()` uses that path directly. The implementation stayed behavior-preserving: visible-signature setup changes still flow through the same workflow mutation logic, preset clearing still happens when the draft diverges, and the panel still receives the returned coordinator state for rendering and preview refresh.

Focused validation completed cleanly in the implementation branch. The completed slice kept the Qt form boundary unchanged, tightened the public coordinator API around the common visible-setup action, and made the shell orchestration easier to read without widening the surface area.

Validation evidence for the completed slice:

    pytest tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py
    87 passed

    ruff check src/foliaseal/application/signature_properties_coordinator.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py
    All checks passed!

    git diff --check
    <no output>

## Context and Orientation

The signing setup workflow spans two existing boundaries. `src/foliaseal/application/signature_properties_coordinator.py` is the application-layer owner of certificate selection, preset selection, visible-signature setup state, readiness text, preview state, and preset clearing when the current draft diverges from a saved preset. `src/foliaseal/presentation/qt/visible_signature_setup_form.py` is a Qt-only editor that loads a `VisibleSignatureSetupDraft` into widgets and rebuilds that draft from the current controls. `src/foliaseal/presentation/qt/signing_shell.py` contains `SignaturePropertiesPanel`, which renders the selectors and preview card, owns the Qt form instance, and applies form changes through `apply_visible_setup(...)`.

The target boundary for this slice is simple. The coordinator should explicitly expose the visible-signature setup application path so the shell can say “apply this draft” without packaging that common action as a command first. The Qt form remains a local editor port and should not change behavior or contract in this slice.

This plan must preserve requirements from `docs/SPEC.md`. In particular, V1 should stay simple, visible signatures remain the primary path, partial presets must not unnecessarily wipe certificate selection, and the UI must still present accurate readiness feedback before signing.

## Plan of Work

First, update `src/foliaseal/application/signature_properties_coordinator.py`. Extend the `SignaturePropertiesCoordinator` protocol with `apply_visible_setup(draft, *, control_issue=None) -> SignaturePropertiesViewState`. Implement the method on `DefaultSignaturePropertiesCoordinator` as a thin wrapper that forwards to the existing `ApplyVisibleSignatureSetup` logic and returns `load(...)` output in the same format as `reconcile(...)`. Do not change how preset clearing, certificate handling, or validation text work. This slice is about making the boundary explicit, not changing policy.

Second, update `src/foliaseal/presentation/qt/signing_shell.py`. In `SignaturePropertiesPanel.apply_changes()`, keep the current `ValueError` handling and `_control_issue` mapping, but replace the direct `reconcile(ApplyVisibleSignatureSetup(...))` call with the new coordinator method. Keep `_apply_coordinator_state(...)` and preview update sequencing unchanged so selector rendering and preview state remain driven by returned coordinator state.

Third, update tests. In `tests/unit/test_signature_properties_coordinator.py`, add a focused test that calls the new method directly and proves it updates the workflow, clears preset selection, and returns current state the same way as the command path. In `tests/unit/test_qt_signing_shell.py`, update or add a focused shell test that proves `SignaturePropertiesPanel.apply_changes()` still clears preset selection and preserves the existing validation path when the form draft changes. Prefer narrow assertions around returned state and visible behavior, not new white-box coupling.

Fourth, update `docs/ARCHITECTURE.md` so the signature-properties coordinator contract names the dedicated visible-setup entrypoint alongside `load()` and `reconcile()`. Then update this ExecPlan so every living section reflects the actual implementation and validation outcomes.

## Concrete Steps

Work from `/home/daekar/FoliaSeal`.

1. Edit `src/foliaseal/application/signature_properties_coordinator.py` to add `apply_visible_setup(...)` to the protocol and implementation.
2. Edit `src/foliaseal/presentation/qt/signing_shell.py` so `SignaturePropertiesPanel.apply_changes()` uses the explicit coordinator entrypoint.
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

Acceptance is behavior-preserving. The change is correct if:

- applying a visible-signature setup draft through the new coordinator method updates the workflow and clears any selected preset state exactly as before;
- `SignaturePropertiesPanel.apply_changes()` still returns a refreshed preview, still maps form-build `ValueError`s into `_control_issue`, and still leaves selector rendering driven by returned coordinator state;
- the focused coordinator and shell tests pass without expanding the Qt form surface.

Run the commands in `## Concrete Steps` and expect both test modules to pass, `ruff` to report no issues, and `git diff --check` to report no whitespace problems.

## Idempotence and Recovery

This slice is safe to repeat. Re-running the tests and linter is idempotent. If the new entrypoint causes stale selector or preset state, recover by routing all selector refreshes back through `_apply_coordinator_state(...)` rather than reintroducing duplicate shell-side clearing logic. If validation behavior changes unexpectedly, restore the current `ValueError` to `_control_issue` mapping in `SignaturePropertiesPanel.apply_changes()` and keep the new entrypoint as a thin wrapper only.

## Artifacts and Notes

Actual key code shape after implementation:

    class SignaturePropertiesCoordinator(Protocol):
        def load(...): ...
        def apply_visible_setup(...): ...
        def reconcile(...): ...

    class DefaultSignaturePropertiesCoordinator:
        def apply_visible_setup(...):
            self._apply_visible_signature_setup(ApplyVisibleSignatureSetup(draft=draft))
            return self.load(control_issue=control_issue)

The implementation is intentionally thin and preserves the same state transition and returned view-state contract.

## Interfaces and Dependencies

The public application boundary in `src/foliaseal/application/signature_properties_coordinator.py` exposes:

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

        def reconcile(
            self,
            command: SignaturePropertiesCommand,
            *,
            control_issue: SigningDraftValidationIssue | None = None,
        ) -> SignaturePropertiesViewState: ...

`QtVisibleSignatureSetupForm` remains a presentation-layer dependency only. This slice must not change its load/build contract or move preview rendering, catalog persistence, or signing execution into the coordinator.

Revision note: created on 2026-05-25 to implement the first narrow slice of the signing-setup hybrid selected during the latest architecture pass.
