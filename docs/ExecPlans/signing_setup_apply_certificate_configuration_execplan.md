# Add explicit certificate-application entrypoint to the signing setup boundary

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

`/home/daekar/FoliaSeal/.agents/skills/write-execplan/PLANS.md` is the governing format reference for this document and this file must be maintained in accordance with it.

## Purpose / Big Picture

After this change, the signing setup workflow will expose an explicit application-layer entrypoint for applying a certificate configuration, matching the already-landed visible-setup and preset-application entrypoints. The user-visible behavior should remain unchanged: applying a certificate still updates the current signing material, still honors typed-password and saved-secret behavior, and still reports certificate errors through the existing reload and message path. The benefit is boundary symmetry: the shell stops assembling the normal certificate-application command itself for the common selector/button path.

## Child ExecPlan Dependencies

- [x] No child ExecPlans are planned for this slice.

## Progress

- [x] (2026-05-26 21:38Z) Reviewed the current post-preset-entrypoint boundary and gathered an `explorer-light` recommendation for the next symmetry slice.
- [x] (2026-05-26 21:38Z) Added `apply_certificate_configuration(...)` to the signing-setup coordinator protocol and default implementation in `src/foliaseal/application/signature_properties_coordinator.py`.
- [x] (2026-05-26 21:38Z) Rewired `SignaturePropertiesPanel.apply_selected_certificate_configuration()` in `src/foliaseal/presentation/qt/signing_shell.py` to use the explicit coordinator entrypoint.
- [x] (2026-05-26 21:38Z) Added or updated focused unit tests in `tests/unit/test_signature_properties_coordinator.py` and `tests/unit/test_qt_signing_shell.py`.
- [x] (2026-05-26 21:38Z) Updated `docs/ARCHITECTURE.md` and this ExecPlan to completion state.
- [x] (2026-05-26 21:38Z) Recorded final validation evidence: `99 passed`, `ruff clean`, `git diff --check clean`.

## Surprises & Discoveries

- Observation: Certificate application was the last common setup action still assembled in the shell instead of being named as a direct coordinator entrypoint.
  Evidence: `SignaturePropertiesPanel.apply_selected_certificate_configuration()` now calls `DefaultSignaturePropertiesCoordinator.apply_certificate_configuration(...)`, matching the already-landed visible-setup and preset-selection paths.

## Decision Log

- Decision: Keep this slice strictly to certificate application and do not mix in refresh, save/delete, or setup-surface redesign work.
  Rationale: The goal is narrow boundary symmetry. Mixing broader changes would make it harder to verify that password forwarding and error behavior stayed stable.
  Date/Author: 2026-05-26 / Codex

- Decision: Preserve the current shell-owned password forwarding and error reporting behavior.
  Rationale: The shell still owns the password textbox and the user-visible error surface. This slice only changes how the normal apply action crosses into the coordinator.
  Date/Author: 2026-05-26 / Codex

## Outcomes & Retrospective

The signing-setup boundary now exposes a public `apply_certificate_configuration(...)` entrypoint on the coordinator, and the Qt shell uses that method directly for the common certificate-application path. That completed the symmetry work so certificate application now matches the already-explicit visible-setup and preset-application paths while preserving the existing password forwarding and error-reporting behavior.

The completion evidence for the slice is recorded as `99 passed`, `ruff clean`, and `git diff --check clean`. The final pass also closed the saved-secret shell regression gap by adding the missing local fake secret provider helper and the empty-password shell-path coverage.

## Context and Orientation

The signing setup workflow now has explicit coordinator entrypoints for loading state, applying the visible-signature draft, applying a nonblank signature preset, and applying a certificate configuration. Before this slice, certificate application was the last common path still assembled in `src/foliaseal/presentation/qt/signing_shell.py`. The real logic lived in `src/foliaseal/application/signature_properties_coordinator.py`: it validates the selected certificate configuration name, resolves signing material from typed passphrase or saved secret, mutates `SigningDraftWorkflow`, and returns updated `SignaturePropertiesViewState`.

This slice made that path symmetrical with the prior hybrid work. The shell now says “apply this certificate configuration” directly, while still passing along the typed passphrase from the Qt field. The implementation preserves:

- typed-password forwarding when the user enters one;
- saved-secret fallback when no passphrase is typed;
- existing error behavior when the certificate file is missing or resolution fails;
- the fact that certificate application does not implicitly clear selected preset state.

The slice must remain compatible with `docs/SPEC.md`. Certificate handling is still a product-facing V1 requirement, and nothing here should weaken partial preset behavior or readiness reporting.

## Plan of Work

First, update `src/foliaseal/application/signature_properties_coordinator.py`. Extend the `SignaturePropertiesCoordinator` protocol with `apply_certificate_configuration(selected_name, *, passphrase=None, control_issue=None) -> SignaturePropertiesViewState`. Implement `DefaultSignaturePropertiesCoordinator.apply_certificate_configuration(...)` as a thin wrapper over the existing certificate-application helper so it preserves name validation, signing-material resolution, workflow mutation, selected-state reconciliation, and returned view-state formatting.

Second, update `src/foliaseal/presentation/qt/signing_shell.py`. In `SignaturePropertiesPanel.apply_selected_certificate_configuration()`, replace direct construction of `ApplyCertificateConfiguration(...)` with the new coordinator method. Keep the current `SignaturePropertiesCoordinatorError` handling, `_apply_coordinator_state(...)`, and `_notify_change()` behavior intact.

Third, update tests. In `tests/unit/test_signature_properties_coordinator.py`, add wrapper coverage for both typed-password and saved-secret certificate application, and keep the existing resolution-failure coverage aligned with the wrapper path if needed. In `tests/unit/test_qt_signing_shell.py`, add focused shell coverage that the certificate-selection path uses the new coordinator method and still preserves the current success/error behavior.

Fourth, update `docs/ARCHITECTURE.md` so the signature-properties coordinator contract names `apply_certificate_configuration(...)` alongside the other explicit entrypoints. Then update this ExecPlan so every living section reflects the final implementation and validation outcomes.

## Concrete Steps

Work from `/home/daekar/FoliaSeal`.

1. Edit `src/foliaseal/application/signature_properties_coordinator.py` to add `apply_certificate_configuration(...)` to the protocol and implementation.
2. Edit `src/foliaseal/presentation/qt/signing_shell.py` so `SignaturePropertiesPanel.apply_selected_certificate_configuration()` uses the explicit coordinator entrypoint.
3. Edit `tests/unit/test_signature_properties_coordinator.py` and `tests/unit/test_qt_signing_shell.py` to cover the new public path.
4. Edit `docs/ARCHITECTURE.md` and then update this ExecPlan.
5. Run:

       pytest tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py
       ruff check src/foliaseal/application/signature_properties_coordinator.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py
       git diff --check

Recorded evidence after completion:

       99 passed
       ruff clean
       git diff --check clean

## Validation and Acceptance

Acceptance is behavior-preserving. The slice is complete if:

- applying a certificate through the new coordinator method preserves typed-password and saved-secret behavior exactly as before;
- `SignaturePropertiesPanel.apply_selected_certificate_configuration()` still reports errors through the same path and still refreshes rendered state from the returned coordinator state on success;
- focused coordinator and shell tests pass without changing the visible-signature form contract or preset behavior;
- the recorded validation evidence for the finished slice is `99 passed`, `ruff clean`, and `git diff --check clean`.

## Idempotence and Recovery

This slice is safe to repeat. Re-running the focused tests and linter is idempotent. If the new entrypoint breaks password handling, recover by routing the call back through the existing `_apply_certificate_configuration(...)` helper and checking the exact `passphrase` values passed from the shell. If selector state drifts, restore rendering through `_apply_coordinator_state(...)` rather than adding shell-side repair logic.

## Artifacts and Notes

Final key code shape:

    class SignaturePropertiesCoordinator(Protocol):
        def load(...): ...
        def apply_visible_setup(...): ...
        def apply_signature_preset(...): ...
        def apply_certificate_configuration(...): ...
        def reconcile(...): ...

    class DefaultSignaturePropertiesCoordinator:
        def apply_certificate_configuration(...):
            self._apply_certificate_configuration(
                ApplyCertificateConfiguration(
                    selected_name=selected_name,
                    passphrase=passphrase,
                )
            )
            return self.load(control_issue=control_issue)

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

        def apply_certificate_configuration(
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

This slice must not change `QtVisibleSignatureSetupForm`, refresh/catalog commands, save/delete preset commands, or any signing execution logic.

Revision note: revised on 2026-05-26 to close the signing-setup certificate-application slice, record the final validation evidence, and mark the living plan sections complete.
