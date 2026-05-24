# Deepen the coordinator into the owner of current signing setup

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with [.agents/skills/write-execplan/PLANS.md](/home/daekar/FoliaSeal/.agents/skills/write-execplan/PLANS.md).

## Purpose / Big Picture

After this slice, the application-layer coordinator should own the full current signing setup concept, not just parts of it. The user-visible workflow should remain the same, but the shell should stop owning separate certificate/preset synchronization rules that the coordinator can own more coherently.

This is the first child slice of the parent effort in [signing_setup_boundary_parent_execplan.md](/home/daekar/FoliaSeal/docs/ExecPlans/signing_setup_boundary_parent_execplan.md). A user should still be able to choose a certificate configuration, choose or save a preset, edit the visible signature draft, and see accurate preview/readiness behavior after the refactor.

## Child ExecPlan Dependencies

- [x] (2026-05-24 20:18Z) No child ExecPlans are required for this bounded application-layer slice.

## Progress

- [x] (2026-05-24 20:18Z) Recorded the child plan before implementation.
- [x] (2026-05-24 21:24Z) Removed the shell-owned preset pre-clear path from visible-signature edit handlers so `ApplyVisibleSignatureSetup` is the only owner of dirty-preset clearing for the main form path.
- [x] (2026-05-24 21:31Z) Updated `SignaturePropertiesPanel._apply_coordinator_state()` to re-render setup selector state from `SignaturePropertiesViewState` when coordinator-owned selection state changes.
- [x] (2026-05-24 21:42Z) Validated the narrowed slice with focused coordinator and shell tests, then updated docs for Child B handoff.

## Surprises & Discoveries

- Observation: the existing coordinator already has the right center of gravity.
  Evidence: it already owns `load()`, `reconcile()`, `VisibleSignatureSetupDraft`, preview/readiness state, and persistence-backed certificate/preset reconciliation.

- Observation: the remaining friction is not command semantics, but shell-owned state synchronization around those commands.
  Evidence: `signing_shell.py` still mirrors selected names, reloads selector widgets manually, and coordinates stale-selection clearing around coordinator calls.

- Observation: removing the shell's duplicate preset-clearing path exposed a separate render seam in the shell.
  Evidence: the first validation pass failed because the coordinator correctly cleared the selected preset after `ApplyVisibleSignatureSetup`, but `_apply_coordinator_state()` was not yet reloading the preset selector from `SignaturePropertiesViewState`.

## Decision Log

- Decision: preserve the explicit command model from the existing coordinator.
  Rationale: it already matches the domain language and avoids a generic “kitchen sink” intent payload.
  Date/Author: 2026-05-24 / Codex

- Decision: keep this child slice behavior-preserving.
  Rationale: the goal is to deepen ownership first, then migrate the shell to it in Child B without mixing UI redesign into the application-layer refactor.
  Date/Author: 2026-05-24 / Codex

- Decision: keep certificate password capture in the shell for this slice.
  Rationale: the shell still needs to translate blank widget input to `None` so coordinator-side saved-secret fallback continues working; moving that behavior now would broaden the slice unnecessarily.
  Date/Author: 2026-05-24 / Codex

## Outcomes & Retrospective

Child A landed as a narrow boundary-deepening slice rather than a broad coordinator rewrite.

Implemented outcome:

- visible-signature edits no longer pre-clear preset state in the shell before dispatching `ApplyVisibleSignatureSetup`
- the coordinator remains the sole owner of that dirty-preset semantic for the main setup form path
- the shell now renders preset/certificate selector state from returned coordinator state when selections change

Validation outcome:

- `pytest tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py`
- `ruff check src/foliaseal/application/signature_properties_coordinator.py src/foliaseal/application/__init__.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py`
- `git diff --check`

The first test pass surfaced one real issue: removing the duplicate shell clear left the preset selector visually stale after a visible-signature edit. That was fixed by re-rendering selector state inside `_apply_coordinator_state()` from `SignaturePropertiesViewState` instead of restoring the old duplicate clear path.

Child B can now focus on broader shell migration work without preserving the old preset-dirty workaround.

## Context and Orientation

The current coordinator in [src/foliaseal/application/signature_properties_coordinator.py](/home/daekar/FoliaSeal/src/foliaseal/application/signature_properties_coordinator.py) already owns:

- certificate configuration application,
- preset application/save/delete,
- visible-signature setup application through `VisibleSignatureSetupDraft`,
- preview/readiness state generation,
- catalog refresh,
- and selection-name recovery from workflow-backed ids.

However, the shell in [src/foliaseal/presentation/qt/signing_shell.py](/home/daekar/FoliaSeal/src/foliaseal/presentation/qt/signing_shell.py) still owns additional signing-setup behavior:

- reading certificate passwords from widgets and forwarding them in multiple places,
- manually reloading certificate/preset selectors,
- clearing selected preset state after form edits,
- and deciding when to keep or drop local selected-name state.

This child slice should move as much of that setup synchronization as possible behind the coordinator while keeping the existing Qt form and shell entry points working.

Relevant files:

- `src/foliaseal/application/signature_properties_coordinator.py`
- `src/foliaseal/application/__init__.py`
- `tests/unit/test_signature_properties_coordinator.py`
- `src/foliaseal/presentation/qt/signing_shell.py`
- `docs/ARCHITECTURE.md`

## Plan of Work

This child slice intentionally narrowed to the smallest safe ownership move:

- remove shell-side preset clearing from visible-signature edit handlers
- rely on `ApplyVisibleSignatureSetup` for the dirty-preset semantic
- make the shell render selector changes from `SignaturePropertiesViewState` instead of pre-clearing widgets itself

Broader shell choreography changes remain for Child B.

## Concrete Steps

From `/home/daekar/FoliaSeal`, implement and validate this slice with:

    pytest tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py
    ruff check src/foliaseal/application/signature_properties_coordinator.py src/foliaseal/application/__init__.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py
    git diff --check

Observed outcomes after this child slice:

- the coordinator owns more of the signing-setup synchronization semantics,
- existing coordinator boundary tests continue covering dirty-preset semantics directly,
- and Child B can migrate the shell mostly by rendering coordinator state and forwarding commands.

## Validation and Acceptance

Acceptance was behavioral:

- coordinator tests prove certificate/preset refresh and stale-selection behavior directly,
- partial preset behavior remains intact,
- typed and saved password resolution still works,
- visible-signature setup edits still clear selected preset state when appropriate,
- and focused shell tests stay green even if they still use compatibility paths temporarily.

This child slice is complete because the main setup form no longer clears preset state in the shell before dispatching to the coordinator, and the focused shell/coordinator tests prove the selector state still updates correctly.

## Idempotence and Recovery

This slice was safe to retry. The one failed first-pass test exposed a missing render step rather than a boundary-model problem, so the recovery path was to make state application render selectors from coordinator state instead of restoring duplicate shell semantics. Avoid changing Qt widget composition here; that belongs to Child B or later product-surface work.

## Artifacts and Notes

Pre-change evidence:

    `signing_shell.py` still owns:
    - selector reload methods
    - some selected-name mirroring
    - repeated widget -> command password propagation
    - dirty-preset clearing triggers around setup edits

This child slice aims to make those responsibilities application-owned where possible.

## Interfaces and Dependencies

The target interface remains the existing coordinator shape:

- `SignaturePropertiesCoordinator.load(...) -> SignaturePropertiesViewState`
- `SignaturePropertiesCoordinator.reconcile(command, ...) -> SignaturePropertiesViewState`

The explicit command types should remain the primary public vocabulary:

- `ApplyCertificateConfiguration`
- `ApplySignaturePreset`
- `SaveCurrentPreset`
- `DeletePreset`
- `RefreshCatalogs`
- `ClearSelectedSignaturePreset`
- `ApplyVisibleSignatureSetup`

Dependencies remain local-substitutable:

- `SigningDraftWorkflow`
- `CertificateCatalogStore`
- `SignaturePresetCatalogStore`
- `CertificateSecretProvider`

Qt must not leak into this boundary.

Revision note: created on 2026-05-24 as Child A of the current signing setup boundary refactor.
