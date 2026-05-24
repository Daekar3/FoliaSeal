# Deepen the visible-signature setup coordinator boundary

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with [.agents/skills/write-execplan/PLANS.md](/home/daekar/FoliaSeal/.agents/skills/write-execplan/PLANS.md).

## Purpose / Big Picture

After this slice, the application-layer setup coordinator should own the load/apply orchestration for visible-signature setup instead of leaving that work spread across Qt panel methods. A user will not see a new feature, but the visible-signature setup path will become easier to simplify safely in later de-harnessing slices because the panel will behave more like a form adapter over one deeper application boundary.

## Child ExecPlan Dependencies

- [x] (2026-05-24 16:32Z) No child ExecPlans are required for this first refactor slice.

## Progress

- [x] (2026-05-24 16:32Z) Audited the current setup flow locally and identified the first narrow deepening step: move visible-signature setup load/apply orchestration behind the coordinator.
- [x] (2026-05-24 16:32Z) Recorded this ExecPlan before implementation.
- [x] (2026-05-24 16:45Z) Added visible-signature setup draft/state types and an application command for applying them through the coordinator.
- [x] (2026-05-24 16:45Z) Updated `SignaturePropertiesPanel` to load and apply visible-signature setup through coordinator state instead of direct workflow mutation in the main form path.
- [x] (2026-05-24 16:55Z) Added boundary tests for the new coordinator responsibility and kept focused shell tests green.
- [x] (2026-05-24 17:02Z) Reviewed architecture/spec alignment, updated docs, and prepared the slice for commit.

## Surprises & Discoveries

- Observation: the remaining architectural friction is not just the number of controls, but where workflow mutation is triggered.
  Evidence: `SignaturePropertiesPanel.apply_changes()` currently builds the appearance object, mutates `SigningDraftWorkflow` directly, conditionally mutates placement directly, then separately asks the coordinator to recompute state through `load()`.
- Observation: the first useful deepening step did not require a brand-new module.
  Evidence: extending `signature_properties_coordinator.py` with a visible-signature setup draft and command was enough to move the panel’s main setup path behind the application boundary while keeping the slice narrow.

## Decision Log

- Decision: keep this first slice narrow and preserve the existing `signature_properties_coordinator.py` module.
  Rationale: the goal is to deepen the existing boundary first, not to rename or split modules while the interface is still moving.
  Date/Author: 2026-05-24 / Codex

- Decision: model the first deepened boundary around a `VisibleSignatureSetupDraft` and coordinator command rather than redesigning every Qt control interface at once.
  Rationale: that moves orchestration and workflow mutation behind the application layer immediately while keeping the Qt-side form mapping manageable in one slice.
  Date/Author: 2026-05-24 / Codex

## Outcomes & Retrospective

This slice deepened the existing setup boundary without changing the visible product behavior. `DefaultSignaturePropertiesCoordinator` now owns a Qt-independent `VisibleSignatureSetupDraft`, returns that draft in `SignaturePropertiesViewState`, and accepts `ApplyVisibleSignatureSetup` to mutate `SigningDraftWorkflow` on the panel’s main form path.

The result is that `SignaturePropertiesPanel` no longer needs to mutate the workflow directly when the user edits the visible-signature form and preview/readiness are refreshed. The panel still maps raw Qt controls to and from the draft in this slice, but the orchestration moved into the application layer where later de-harnessing and workflow simplification can be tested at a boundary.

Focused validation passed:

- `pytest tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py`
- `ruff check src/foliaseal/application/signature_properties_coordinator.py src/foliaseal/application/__init__.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py`
- `git diff --check`

The next refactor slice should probably move more of the raw control-to-draft mapping out of `signing_shell.py`, because that is now the remaining shallow seam inside the visible-signature setup flow.

## Context and Orientation

The current application boundary in `src/foliaseal/application/signature_properties_coordinator.py` already owns certificate configuration selection, preset selection, readiness text, and catalog refresh. However, the rest of visible-signature setup still lives directly in `src/foliaseal/presentation/qt/signing_shell.py`.

Today, the panel does all of the following itself:

- read appearance and field controls,
- build a `SignatureAppearance`,
- decide whether placement is initialized,
- build a `SignatureRect`,
- clear selected preset state on edits,
- mutate `SigningDraftWorkflow`,
- then ask the coordinator to recompute preview/readiness state.

That is the shallow seam. The coordinator already understands the draft workflow and selected preset/certificate state, but the panel still owns too much orchestration around the same concept.

This slice does not need to redesign all visible-signature controls. It only needs to move the load/apply orchestration for visible-signature setup into the application layer so later UI simplification can target a cleaner boundary.

Relevant files:

- `src/foliaseal/application/signature_properties_coordinator.py`
- `src/foliaseal/application/__init__.py`
- `src/foliaseal/presentation/qt/signing_shell.py`
- `tests/unit/test_signature_properties_coordinator.py`
- `tests/unit/test_qt_signing_shell.py`
- `docs/ARCHITECTURE.md`

## Plan of Work

First, extend `src/foliaseal/application/signature_properties_coordinator.py` with visible-signature setup draft/state types. The draft should capture the current appearance plus the current placement form values in a Qt-independent representation. Add one coordinator command that applies that draft to `SigningDraftWorkflow`, recomputes preview/readiness, and clears selected preset state when the current draft diverges from a selected preset.

Second, add the new draft to `SignaturePropertiesViewState` so the panel can load all visible-signature controls from application-layer state rather than pulling appearance and placement directly from the workflow.

Third, update `SignaturePropertiesPanel` in `src/foliaseal/presentation/qt/signing_shell.py` so its main form path becomes:

- read controls into a visible-signature setup draft,
- hand that draft to the coordinator,
- render returned state.

The panel may still map raw Qt controls to and from the draft in this slice. Preview layout and rendering stay where they already are.

Fourth, add boundary tests in `tests/unit/test_signature_properties_coordinator.py` to prove that the coordinator now owns visible-signature setup load/apply semantics, including preset dirty clearing and placement-enabled behavior. Keep focused shell tests in `tests/unit/test_qt_signing_shell.py` green.

Finally, update `docs/ARCHITECTURE.md` and this ExecPlan so the repository record reflects the deeper setup boundary.

## Concrete Steps

From `/home/daekar/FoliaSeal`, implement and validate this slice with:

    pytest tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py
    ruff check src/foliaseal/application/signature_properties_coordinator.py src/foliaseal/application/__init__.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py
    git diff --check

Manual acceptance target after implementation:

    .venv/bin/foliaseal gui --pdf-path "/path/to/example.pdf"

Expected visible result: the GUI should behave the same, but the setup path should now be driven through the coordinator boundary rather than a mix of Qt-panel mutation and coordinator reload calls.

## Validation and Acceptance

Acceptance is behavioral:

- focused coordinator and shell tests pass;
- visible-signature setup changes still update preview and readiness correctly;
- applying setup through the panel still preserves certificate and preset behavior;
- the coordinator exposes visible-signature setup state through `SignaturePropertiesViewState`;
- `ruff check` and `git diff --check` pass.

## Idempotence and Recovery

This slice is safe to repeat. If regressions appear, restore direct panel-to-workflow mutation while keeping the newer product-facing UI composition work intact. No persisted data shape should change.

## Artifacts and Notes

Pre-change evidence:

    SignaturePropertiesPanel.apply_changes():
    - builds SignatureAppearance directly from controls
    - conditionally builds SignatureRect directly from controls
    - mutates SigningDraftWorkflow directly
    - then calls refresh_preview(), which asks the coordinator to load state

This is the specific orchestration seam the slice is intended to deepen.

## Interfaces and Dependencies

This refactor stays within local in-process and local-substitutable boundaries:

- `DefaultSignaturePropertiesCoordinator` remains the application-layer orchestrator over `SigningDraftWorkflow` and local config stores.
- `SignaturePropertiesPanel` remains a Qt adapter and preview host.
- Preview layout/lifecycle helpers stay untouched in this slice.

The intended new boundary should expose:

- a Qt-independent visible-signature setup draft,
- one coordinator command that applies that draft,
- one state object that returns the current draft plus readiness/preview information.

Revision note: created and completed on 2026-05-24 for the first coordinator-deepening slice of visible-signature setup.
