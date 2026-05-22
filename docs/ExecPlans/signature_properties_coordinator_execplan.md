# Introduce a signature-properties coordinator boundary

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows the requirements in `.agents/skills/write-execplan/PLANS.md`. It is self-contained so a contributor can resume the slice from only this file and the current repository tree.

## Purpose / Big Picture

FoliaSeal's signing shell used to mix Qt widget concerns with certificate-configuration application, signature-preset reconciliation, validation messaging, and sign-readiness rules. That state has now been split: the shell still renders the same controls, but those responsibilities are driven by a dedicated `SignaturePropertiesCoordinator` that returns an immutable view state. A contributor or user can prove the change worked by running focused unit tests: coordinator tests exercise certificate and preset flows without inspecting Qt internals, and the shell tests still show that the panel renders and updates correctly.

This slice is intentionally narrow. It introduced the coordinator/state boundary described by issue `#51`, but it did not migrate canonical preview rendering, preview-layout helpers, or the preview snapshot lifecycle. Those stay in the Qt panel for a later slice so this record can focus on state reconciliation and test-surface cleanup.

## Child ExecPlan Dependencies

- [ ] A later child ExecPlan may move canonical preview rendering and preview-layout orchestration behind the coordinator once this plan's state boundary exists.
- [ ] A later child ExecPlan may simplify `SigningWorkspaceWidget` and `app_frame.py` refresh seams after callers depend on the new coordinator contract instead of widget internals.

## Progress

- [x] (2026-05-21T15:12:00Z) Reviewed issue `#51` and confirmed that ExecPlan A was the next slice to execute.
- [x] (2026-05-21T15:23:00Z) Completed the required `explorer-light` codebase review before drafting or implementing the slice.
- [x] (2026-05-21T15:34:00Z) Wrote the initial ExecPlan with the coordinator/state boundary explicitly separated from later preview migration work.
- [x] (2026-05-22T02:12:00Z) Added `src/foliaseal/application/signature_properties_coordinator.py`, rewired `SignaturePropertiesPanel` to use it for certificate/preset reconciliation, and kept preview/canonical-render responsibilities in `signing_shell.py`.
- [x] (2026-05-22T02:24:00Z) Added `tests/unit/test_signature_properties_coordinator.py` and expanded it to cover typed-password, saved-password, preset-apply, save/delete, and catalog-refresh reconciliation paths.
- [x] (2026-05-22T02:37:00Z) Completed focused validation (`pytest`, `ruff check`, `git diff --check`) and the required compliance review; updated `docs/ARCHITECTURE.md` and this ExecPlan to match the implemented boundary.

## Surprises & Discoveries

- Observation: `DefaultSignaturePropertiesCoordinator` needs an explicit `ClearSelectedSignaturePreset` command so the panel can mark a preset selection dirty after appearance or placement edits without mutating the workflow a second time.
  Evidence: the panel still uses `_suspend_updates` around UI refreshes, but the actual preset-selection reset now happens through the coordinator API instead of widget-private state.

- Observation: `load()` and `reconcile()` accept an optional control issue, which lets the panel fold appearance/placement validation errors into the same readiness text that the coordinator returns.
  Evidence: the implementation no longer duplicates validation-message formatting in `SignaturePropertiesPanel`; the panel passes `_control_issue` through to the coordinator and renders the returned view state.

- Observation: `SigningDraftWorkflow` still owns the invariant that applying a preset without a certificate reference must not clear the active certificate configuration.
  Evidence: the coordinator defers to `apply_resolved_signature_preset()`, which only overwrites `selected_certificate_configuration_id` when the preset contains one.

## Decision Log

- Decision: The coordinator keeps a dedicated `ClearSelectedSignaturePreset` command instead of inferring dirty-state resets from unrelated control edits.
  Rationale: The panel needs a narrow way to clear the current preset selection after manual edits without reimplementing workflow reconciliation or creating another widget-private dirty flag.
  Date/Author: 2026-05-21 / Codex

- Decision: `load()` and `reconcile()` accept `control_issue` as an optional argument.
  Rationale: The signing shell already computes placement/appearance validation errors locally, and threading that issue into the coordinator keeps validation text and readiness state in one place.
  Date/Author: 2026-05-21 / Codex

- Decision: Preview/canonical-render responsibilities stay in `SignaturePropertiesPanel` for this slice.
  Rationale: The preview path is still the brittle, geometry-heavy part of the module. Keeping it local avoided widening the change set and kept the coordinator boundary focused on state reconciliation.
  Date/Author: 2026-05-21 / Codex

## Outcomes & Retrospective

This slice is now implemented. The signing-properties interface is smaller and clearer: certificate and preset reconciliation, catalog refresh, dirty-selection clearing, validation text, and readiness state are now application-layer concerns, while `signing_shell.py` keeps the preview and canonical-render work.

The biggest behavioral constraint held: a preset without a certificate reference still preserves the active certificate configuration, and catalog refreshes reconcile stale display-name selections instead of forcing the user back into widget-private recovery paths.

The remaining structural debt is also clearer now. `signing_shell.py` is still a large module, but the state-reconciliation portion of the file has been removed from the Qt layer. The next clean boundary, if one is needed, is the preview/canonical-render path rather than the signature-properties workflow.

## Context and Orientation

The current signing UI still lives in `src/foliaseal/presentation/qt/signing_shell.py`. Inside that file, `SignaturePropertiesPanel` builds the certificate configuration selector, signature preset controls, appearance controls, placement controls, preview card, and validation label. It now delegates certificate configuration application, preset apply/save/delete, catalog refresh, dirty-selection clearing, and validation/readiness reconciliation to `DefaultSignaturePropertiesCoordinator`, then renders the returned state back into the Qt controls.

The preview path remains in the panel on purpose. `signing_shell.py` still owns canonical preview rendering, preview geometry, and snapshot cleanup, so the slice stays narrow and the brittle layout work is isolated from the state-boundary refactor.

`src/foliaseal/application/signing_draft_workflow.py` is the mutable application-layer state machine for a visible-signature draft. It owns the draft's current certificate path, passphrase, selected object identifiers, signature rectangle, appearance, preview data, and validation issues. It also captures and applies `ResolvedSignaturePreset` values. This file is already the source of truth for draft invariants, so the new coordinator must work with it rather than duplicate its rules.

`src/foliaseal/application/signing_material_resolver.py` converts a `CertificateConfiguration` plus optional passphrase input into runtime signing material. It is responsible for graceful failure when the managed certificate file is missing, the password cannot be found, or secure storage is unavailable. `src/foliaseal/infra/config/certificate_storage.py` and `src/foliaseal/infra/config/profile_storage.py` provide local file-backed stores for certificate catalogs and signature preset catalogs, and the coordinator now owns the reconciliation layer that reads from those stores and writes back to them when needed.

Tests for the current shell are concentrated in `tests/unit/test_qt_signing_shell.py`. Many of them exercise behavior through the full fake-Qt shell, even when the behavior under test is actually preset/certificate/state logic. This slice introduces a deeper application-layer seam so new tests can verify behavior through a coordinator interface instead of through widget-private details.

`docs/SCHEMAS.md` constrains this work. Stable internal identifiers, not display names, are the storage keys. `SignaturePreset` remains reference-only and must not merge or partially override other reusable objects. Secret material must not be stored in ordinary configuration payloads. That means the coordinator may use display names in view state for the current UI, but it must preserve the underlying workflow identifiers and continue to resolve passwords through `CertificateSigningMaterialResolver`.

## Plan of Work

This slice is complete. `src/foliaseal/application/signature_properties_coordinator.py` defines the immutable view state, command objects, and default coordinator for signing-shell certificate/preset reconciliation. `SignaturePropertiesPanel` now depends on that coordinator for certificate application, preset apply/save/delete, catalog refresh, dirty-selection clearing, validation text, and ready-to-sign state. The panel still owns Qt-only control construction, preview-card rendering, canonical preview rendering, preview widget geometry, and snapshot cleanup.

The tests are split across two layers. `tests/unit/test_signature_properties_coordinator.py` covers the boundary directly without Qt, including initial load, certificate application, missing managed certificate errors, preset application with and without certificate references, save/delete, and refresh reconciliation. `tests/unit/test_qt_signing_shell.py` remains the thin shell seam that proves the panel still responds to coordinator-backed state.

The documentation step is also part of the slice now: `docs/ARCHITECTURE.md` has been updated to describe the application-layer coordinator boundary and the responsibilities that remain in `signing_shell.py`.

## Concrete Steps

The implementation is already in place. The completed slice corresponds to the following concrete actions:

1. Add `src/foliaseal/application/signature_properties_coordinator.py` with immutable view state, command dataclasses, and the default coordinator implementation.
2. Rewire `SignaturePropertiesPanel` to issue coordinator commands for certificate application, preset apply/save/delete, catalog refresh, and preset dirtying, then render the returned state.
3. Leave canonical preview rendering, preview sizing, and snapshot cleanup in `signing_shell.py`.
4. Add `tests/unit/test_signature_properties_coordinator.py` so the reconciliation boundary is tested without Qt.
5. Keep `tests/unit/test_qt_signing_shell.py` focused on the thin shell seam around the coordinator-backed panel and preview rendering.
6. Update `docs/ARCHITECTURE.md` and this ExecPlan so the documentation matches the current boundary.

## Validation and Acceptance

Acceptance for this slice is behavioral, not structural.

The coordinator test suite is the primary proof of the boundary. It exercises certificate configuration application, preset apply/save/delete, catalog refresh reconciliation, validation text, and readiness-to-sign without instantiating a Qt widget. The important invariants are preserved: presets without certificate references keep the active certificate configuration, missing managed certificate files surface the existing helpful error text, and refreshes keep valid selections while dropping stale ones.

The shell tests remain a smoke test for the Qt seam. They prove that the panel still builds, renders, and responds to coordinator-backed updates without reasserting the coordinator logic through widget internals.

The documentation acceptance criterion is that `docs/ARCHITECTURE.md` now describes the coordinator boundary and the preview responsibilities that remain in `signing_shell.py`.

## Idempotence and Recovery

This refactor is safe to repeat because it is additive at first: add the coordinator module and tests, wire the panel to it, then trim redundant tests. If the panel wiring causes a UI feedback loop, restore the previous call path for the failing control handler, keep the coordinator tests, and reintroduce the next handler one path at a time under `_suspend_updates`.

If a store-backed test becomes flaky because it writes to disk, switch it to a temporary directory under pytest's `tmp_path`. If a shell test starts depending on preview internals, move that assertion down into the coordinator suite or postpone it to the later preview-migration ExecPlan.

## Artifacts and Notes

Current responsibility evidence:

    src/foliaseal/presentation/qt/signing_shell.py
    - SignaturePropertiesPanel still builds the Qt controls, preview card, and canonical preview rendering path.
    - Certificate/preset reconciliation now routes through DefaultSignaturePropertiesCoordinator.
    - Preview widget geometry and snapshot cleanup remain panel responsibilities.

    src/foliaseal/application/signature_properties_coordinator.py
    - Owns display-name reconciliation, catalog refresh/save/delete, dirty-selection clearing, validation text, and ready-to-sign state.
    - Uses SigningDraftWorkflow as the source of truth and delegates certificate-material resolution to CertificateSigningMaterialResolver.

    src/foliaseal/application/signing_draft_workflow.py
    - apply_resolved_signature_preset() preserves the active certificate selection when the preset does not carry one.
    - apply_certificate_configuration() is the authoritative workflow mutation for resolved signing material.

Expected validation evidence for this completed slice:

    pytest tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py
    84 passed in 10.42s

    ruff check src/foliaseal/application/signature_properties_coordinator.py src/foliaseal/application/__init__.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py
    All checks passed!

    git diff --check
    <no output>

## Interfaces and Dependencies

Define the new application-layer interface in `src/foliaseal/application/signature_properties_coordinator.py`:

    @dataclass(frozen=True)
    class SignaturePropertiesViewState:
        selected_certificate_configuration_name: str | None
        selected_signature_preset_name: str | None
        certificate_configuration_names: tuple[str, ...]
        signature_preset_names: tuple[str, ...]
        validation_text: str
        ready_to_sign: bool
        preview: SigningDraftPreview

    @dataclass(frozen=True)
    class ApplyCertificateConfiguration:
        selected_name: str
        passphrase: str | None = None

    @dataclass(frozen=True)
    class ApplySignaturePreset:
        selected_name: str
        passphrase: str | None = None

    @dataclass(frozen=True)
    class SaveCurrentPreset:
        name: str
        overwrite: bool = False

    @dataclass(frozen=True)
    class DeletePreset:
        name: str

    @dataclass(frozen=True)
    class RefreshCatalogs:
        pass

    @dataclass(frozen=True)
    class ClearSelectedSignaturePreset:
        pass

    SignaturePropertiesCommand = (
        ApplyCertificateConfiguration
        | ApplySignaturePreset
        | SaveCurrentPreset
        | DeletePreset
        | RefreshCatalogs
        | ClearSelectedSignaturePreset
    )

    class SignaturePropertiesCoordinator(Protocol):
        def load(
            self,
            *,
            control_issue: SigningDraftValidationIssue | None = None,
        ) -> SignaturePropertiesViewState: ...
        def reconcile(
            self,
            command: SignaturePropertiesCommand,
            *,
            control_issue: SigningDraftValidationIssue | None = None,
        ) -> SignaturePropertiesViewState: ...

The concrete coordinator uses `SigningDraftWorkflow`, `CertificateCatalogStore`, `SignaturePresetCatalogStore`, and `CertificateSigningMaterialResolver`. The stores are local-substitutable dependencies and are exercised in tests with `tmp_path` directories or in-memory data. `CertificateSecretProvider` remains the mock boundary for saved-password lookup. The panel should not duplicate reconciliation logic after this slice; it should read control values, choose the command, call the coordinator, and render the returned state.

Change note: 2026-05-21 / Codex

This ExecPlan now records the completed `#51` ExecPlan A slice. The implementation introduced the application-layer signature-properties coordinator, moved certificate/preset reconciliation and validation/readiness state out of the Qt panel, and left preview/canonical-render responsibilities in `signing_shell.py` for a later slice.
