# Demote Certificate Password Entry In The Signing Setup MVP Surface

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with [`.agents/skills/write-execplan/PLANS.md`](/home/daekar/FoliaSeal/.agents/skills/write-execplan/PLANS.md).

## Purpose / Big Picture

After this change, the signing setup remains preset-first and no longer foregrounds a permanent certificate password field in the sidebar. Users can still choose an explicit saved certificate configuration, but certificate passwords are collected only when needed, on demand, through `QInputDialog`, with a session-local passphrase cache instead of occupying the default happy-path surface all the time.

The result is observable in three ways. First, the `Certificate configuration` group no longer renders an always-visible password row. Second, certificate application and preset selection that need a manual password succeed through an on-demand prompt, with the session-local cache avoiding redundant re-prompts inside the slice. Third, saved-password resolution through `CertificateSecretProvider` continues to work without prompting.

## Child ExecPlan Dependencies

- [x] (2026-05-27 01:05Z) No child ExecPlans are required for this slice.

## Progress

- [x] (2026-05-27 01:04Z) Confirmed the slice with an `explorer-light` review and narrowed scope to removing the permanent certificate password row while preserving manual fallback and saved-secret resolution.
- [x] (2026-05-27 01:04Z) Implemented the prompt-driven certificate-password fallback in `src/foliaseal/presentation/qt/signing_shell.py`.
- [x] (2026-05-27 01:04Z) Added the Qt binding and fake-binding support for password prompts.
- [x] (2026-05-27 01:04Z) Updated shell tests in `tests/unit/test_qt_signing_shell.py` to cover the reduced surface and on-demand prompt behavior.
- [x] (2026-05-27 01:04Z) Ran focused validation with `pytest`, `ruff check`, and `git diff --check`.
- [x] (2026-05-27 01:04Z) Ran the required compliance review against `docs/SPEC.md`, `docs/SCHEMAS.md`, and `docs/ARCHITECTURE.md`, then fixed any gaps.
- [x] (2026-05-27 01:04Z) Updated documentation, including this ExecPlan and `docs/ARCHITECTURE.md`, to final state.
- [ ] Commit the slice with one narrow commit.

## Surprises & Discoveries

- Observation: the current certificate password is not validated during certificate selection; it is only required to be present and is later consumed by signing. That means a password cache or prompt path is a UI concern rather than a new application-layer validation rule.
  Evidence: `CertificateSigningMaterialResolver.resolve()` only enforces presence/non-blank for the password and file/reference validity before returning `SigningMaterial`.

## Decision Log

- Decision: Use a resolver-driven retry path instead of inventing a new always-visible certificate editor surface.
  Rationale: `CertificateSigningMaterialResolver` already emits specific user-actionable errors when a manual password is needed. Retrying after a prompt keeps the slice narrow and lets saved-password resolution remain the primary path.
  Date/Author: 2026-05-27 / Codex

- Decision: Keep explicit certificate selection and application in the sidebar.
  Rationale: `docs/SPEC.md` still stages the workflow as `Choose preset/certificate`, and `docs/SCHEMAS.md` keeps `CertificateConfiguration` as the user-facing signing identity selection object.
  Date/Author: 2026-05-27 / Codex

## Outcomes & Retrospective

This section is complete. The slice is implemented, validated, reviewed for compliance, and documented; only the final commit remains. The main user-visible simplification is that certificate password entry is no longer a permanent setup-field distraction, while the underlying certificate-selection capability remains intact.

## Context and Orientation

The relevant production logic lives in [src/foliaseal/presentation/qt/signing_shell.py](/home/daekar/FoliaSeal/src/foliaseal/presentation/qt/signing_shell.py). `SignaturePropertiesPanel` builds the right-side setup surface, applies saved certificate configurations, applies signature presets, and delegates setup reconciliation to `DefaultSignaturePropertiesCoordinator`. The `Certificate configuration` group now builds only a combo box and an apply button; when a manual password is needed, the panel prompts through `QInputDialog` instead of keeping a permanent `password_input` widget.

The application-layer certificate resolution logic already lives below Qt in [src/foliaseal/application/signing_material_resolver.py](/home/daekar/FoliaSeal/src/foliaseal/application/signing_material_resolver.py). It uses either an explicit passphrase or a saved secret from `CertificateSecretProvider`, and when neither is available it raises plain-language errors such as “Enter the password…” or “Saved password storage is not available…”. This slice used those existing messages instead of adding new business rules.

The shell tests in [tests/unit/test_qt_signing_shell.py](/home/daekar/FoliaSeal/tests/unit/test_qt_signing_shell.py) now assert prompt-driven expectations instead of a visible `password_input` control. No coordinator or schema changes were required for this slice.

## Plan of Work

First, `src/foliaseal/presentation/qt/signing_shell.py` no longer exposes a permanent `password_input` widget. The `CertificateConfiguration` surface now keeps the saved-certificate combo and the apply button only. A prompt helper uses Qt input-dialog bindings to ask for a certificate password only when the coordinator reports a recoverable “enter the password manually” style error.

Second, the prompt path is threaded through both certificate application and preset application. Direct certificate selection tries the current coordinator path with no explicit passphrase first. If the coordinator raises a password-entry error, the panel prompts, retries once with the entered passphrase, and keeps that passphrase in a session-local cache keyed by certificate configuration so subsequent preset or certificate operations do not immediately re-prompt. Preset selection uses the same retry path when the selected preset resolves to a certificate configuration that needs a manual password.

Third, the fake Qt bindings in `tests/unit/test_qt_signing_shell.py` were updated so the shell can exercise a fake input dialog. The certificate tests now assert the password row is gone, the prompt is used when needed, saved-password resolution skips the prompt, blank selection still errors cleanly, and preset application with a referenced certificate can still switch identities through the prompt/cache path.

Finally, focused validation and the required compliance review against `docs/SPEC.md`, `docs/SCHEMAS.md`, and `docs/ARCHITECTURE.md` are complete. `docs/ARCHITECTURE.md` now reflects the on-demand certificate password flow.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Implement the shell and binding changes.

       apply_patch ... on src/foliaseal/presentation/qt/signing_shell.py
       apply_patch ... on tests/unit/test_qt_signing_shell.py

2. Run focused validation. Completed.

       pytest tests/unit/test_qt_signing_shell.py
       ruff check src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py
       git diff --check

3. Run a compliance review subagent against `docs/SPEC.md`, `docs/SCHEMAS.md`, `docs/ARCHITECTURE.md`, and the changed files. Completed; no gaps remained after the doc refresh.

4. Update documentation and this ExecPlan to final state, then create one git commit for the slice.

## Validation and Acceptance

Acceptance is behavior-focused:

- The `Certificate configuration` group no longer renders a permanent password row.
- Applying a certificate configuration with no saved password prompts once and succeeds when the user provides a password.
- Applying a certificate configuration with a saved password succeeds without prompting.
- Selecting a preset that references a different certificate configuration can still switch the active certificate and passphrase through the prompt/cache path.
- Blank certificate selection still reports the existing error and does not prompt.

Run:

    pytest tests/unit/test_qt_signing_shell.py

Then run:

    ruff check src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py
    git diff --check

Observed result:

    78 passed in 9.19s
    All checks passed!
    <no output from git diff --check>

## Idempotence and Recovery

These edits are safe to repeat. The tests are fake-Qt unit tests. If the prompt path initially triggers too aggressively, narrow it by keying off the existing resolver messages rather than reintroducing the deleted password row. The session-local passphrase cache is intentionally scoped to the current UI session and should not widen the UI surface.

## Artifacts and Notes

Validation transcript from this slice:

    $ pytest tests/unit/test_qt_signing_shell.py
    ... passed

    $ ruff check src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py
    All checks passed!

    $ git diff --check
    <no output>

## Interfaces and Dependencies

The following interfaces must remain valid at the end of this slice:

- `foliaseal.presentation.qt.signing_shell.SignaturePropertiesPanel.apply_selected_certificate_configuration() -> bool`
- `foliaseal.presentation.qt.signing_shell.SignaturePropertiesPanel._on_signature_preset_selected() -> None`
- `foliaseal.application.signature_properties_coordinator.DefaultSignaturePropertiesCoordinator.apply_certificate_configuration(...)`
- `foliaseal.application.signature_properties_coordinator.DefaultSignaturePropertiesCoordinator.apply_signature_preset(...)`

`CertificateConfigurationControls` in `src/foliaseal/presentation/qt/signing_shell.py` should still expose:

    container
    configuration_combo
    apply_button

It no longer exposes a permanent `password_input` widget. Manual password entry happens through a Qt input-dialog binding only when the coordinator/resolver indicates that a passphrase must be entered manually.

Revision note: Created this ExecPlan for the MVP follow-on slice that demoted direct certificate password entry while preserving explicit certificate selection, on-demand prompting, session-local passphrase caching, and saved-password resolution.

Revision note: Updated the plan after implementation and compliance review to reflect the final prompt-driven behavior, added the session-cache test result, and recorded the final validation evidence.
