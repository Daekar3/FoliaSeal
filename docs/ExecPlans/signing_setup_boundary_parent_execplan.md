# Deepen the current signing setup boundary

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with [.agents/skills/write-execplan/PLANS.md](/home/daekar/FoliaSeal/.agents/skills/write-execplan/PLANS.md).

## Purpose / Big Picture

After this refactor, the production signing GUI should have one deeper owner for the “current signing setup” concept instead of spreading that behavior across Qt shell handlers, the signature-properties coordinator, and the visible-signature setup form. A user will not gain a brand-new feature, but the existing certificate configuration, preset, and visible-signature setup flow will become easier to evolve safely toward the [SPEC.md](/home/daekar/FoliaSeal/docs/SPEC.md) document-centric, preset-first workflow.

The most important user-visible effect is stability and simplification of future work. After the refactor, the shell should behave like a thin adapter that renders a single setup state snapshot and forwards explicit setup commands, rather than owning password propagation, stale-selection recovery, catalog refresh choreography, and dirty-preset clearing itself.

## Child ExecPlan Dependencies

- [x] Child A: [signing_setup_boundary_coordinator_deepening_execplan.md](/home/daekar/FoliaSeal/docs/ExecPlans/signing_setup_boundary_coordinator_deepening_execplan.md) completed on 2026-05-24. Child B can now assume the main visible-signature form path clears preset state only through `ApplyVisibleSignatureSetup` and that selector rendering follows returned coordinator state.
- [x] Child B: [signing_setup_boundary_shell_migration_execplan.md](/home/daekar/FoliaSeal/docs/ExecPlans/signing_setup_boundary_shell_migration_execplan.md) completed on 2026-05-24. The Qt-side migration, test replacement, and documentation closeout are done.

## Progress

- [x] (2026-05-24 20:01Z) Explored the current signing setup seam with multiple `explorer-light` agents and identified the highest-value deepening target.
- [x] (2026-05-24 20:12Z) Chose the hybrid design centered on deepening the existing coordinator boundary rather than introducing a separate intent bag or a heavier ports-and-adapters layer.
- [x] (2026-05-24 20:18Z) Recorded this parent ExecPlan and its required child plans before implementation.
- [x] (2026-05-24 21:42Z) Completed Child A as a narrow coordinator-deepening slice: removed shell-side preset pre-clearing on visible-signature edits and made selector rendering follow returned coordinator state.
- [x] (2026-05-24) Completed Child B to migrate the shell to the new boundary and collapse white-box tests into boundary tests where possible.
- [x] (2026-05-24) Performed the final compliance review against `docs/SPEC.md` and `docs/ARCHITECTURE.md`, then updated this parent plan to completion state.

## Surprises & Discoveries

- Observation: the highest remaining setup friction is no longer raw form extraction.
  Evidence: `visible_signature_setup_form.py` already owns appearance/placement editing, but `signing_shell.py` still owns certificate/preset event choreography, password reads, selected-name mirroring, reload behavior, and dirty-preset reset calls.

- Observation: two independent design explorations converged on the same core shape.
  Evidence: both the “minimal interface” and “flexible interface” explorations favored keeping `load()` plus a command-driven reconcile/apply entry point centered on the existing coordinator.

- Observation: Child A did not need a new command or state object.
  Evidence: the existing `ApplyVisibleSignatureSetup` plus `SignaturePropertiesViewState` were already sufficient; the real remaining bug was that the shell was not rendering returned selector state after coordinator-owned selection changes.

## Decision Log

- Decision: treat this as one architectural effort with two child slices rather than one giant refactor.
  Rationale: the shell migration is too coupled to the boundary change to plan safely as one commit, but it also should not begin before the deeper application boundary exists.
  Date/Author: 2026-05-24 / Codex

- Decision: keep the refactor centered on the existing `DefaultSignaturePropertiesCoordinator`.
  Rationale: the codebase is already moving in that direction, and replacing it with an entirely different facade would add naming churn without solving the real problem.
  Date/Author: 2026-05-24 / Codex

- Decision: preserve explicit command semantics instead of using one large generic intent object as the primary boundary.
  Rationale: explicit commands better match the current domain language and reduce the risk of contradictory or partially populated requests.
  Date/Author: 2026-05-24 / Codex

## Outcomes & Retrospective

The full boundary migration is complete. Child A deepened the coordinator boundary, and Child B finished the Qt-side shell migration so the shell now behaves as a thinner adapter over that boundary.

The remaining setup behavior is documented and tested at the correct layer: coordinator tests carry the deeper setup semantics, shell tests are thinner integration checks, and the docs now match the implemented ownership split.

Validation for the parent effort was completed through the focused child test suites and the documented compliance review against `docs/SPEC.md` and `docs/ARCHITECTURE.md`.

## Context and Orientation

The production signing setup flow currently spans three modules:

- [src/foliaseal/application/signature_properties_coordinator.py](/home/daekar/FoliaSeal/src/foliaseal/application/signature_properties_coordinator.py) owns command reconciliation, catalog persistence, password-backed signing-material resolution, selected-name recovery, visible-signature draft state, validation text, readiness state, and preview recomputation.
- [src/foliaseal/presentation/qt/signing_shell.py](/home/daekar/FoliaSeal/src/foliaseal/presentation/qt/signing_shell.py) still owns certificate/preset widgets, password reads, event handlers, error messaging, catalog reload choreography, selected-name reload logic, and dirty-preset clearing triggers.
- [src/foliaseal/presentation/qt/visible_signature_setup_form.py](/home/daekar/FoliaSeal/src/foliaseal/presentation/qt/visible_signature_setup_form.py) owns appearance and placement widget construction plus `VisibleSignatureSetupDraft` load/build mapping.

In this repository, “current signing setup” means the full state required to choose a certificate configuration, choose or save a signature preset, edit the visible signature draft, reconcile stale selections after refresh, and surface readiness/preview information back to the shell.

The architectural goal is a deep module: a small interface that hides the large amount of setup reconciliation currently spread through the shell. The [SPEC.md](/home/daekar/FoliaSeal/docs/SPEC.md) workflow is explicitly preset-first and document-centric, so the shell should not continue behaving like a low-level setup controller if that can be moved behind an application boundary.

## Plan of Work

Child A will deepen the existing coordinator into the owner of the full current signing setup concept. That child will keep the current command-driven model, but it will widen the coordinator’s responsibility so the shell no longer needs to own certificate/preset reload choreography and setup-selection bookkeeping as separate concerns.

Child B will then migrate `signing_shell.py` to become a thin adapter over that deeper boundary. The shell should render state, surface confirmation dialogs where necessary, and forward explicit commands, but it should stop owning the private synchronization patterns that currently force many white-box tests.

After both child slices are complete, the final review for this parent plan must confirm:

- the shell no longer owns the old setup choreography,
- the coordinator owns the intended setup semantics,
- focused tests verify behavior at the deeper boundary instead of asserting internal widget state where that is no longer necessary,
- and the docs reflect the new ownership model accurately.

## Concrete Steps

From `/home/daekar/FoliaSeal`, execute the child plans in order:

    1. Implement Child A in `docs/ExecPlans/signing_setup_boundary_coordinator_deepening_execplan.md`
    2. Validate Child A with its listed `pytest`, `ruff`, and `git diff --check` commands
    3. Implement Child B in `docs/ExecPlans/signing_setup_boundary_shell_migration_execplan.md`
    4. Validate Child B with its listed `pytest`, `ruff`, and `git diff --check` commands
    5. Run a final focused compliance review against `docs/SPEC.md` and `docs/ARCHITECTURE.md`

Manual acceptance target after both children are complete:

    .venv/bin/foliaseal gui --pdf-path "/path/to/example.pdf"

Expected behavior:

- the signing sidebar still supports certificate configuration selection, preset selection/save/delete, visible-signature editing, placement, preview, and signing readiness,
- but `signing_shell.py` should be noticeably thinner and less stateful in the setup area,
- and boundary tests should carry more of the setup behavior coverage.

## Validation and Acceptance

Acceptance for the full parent effort is behavioral:

- certificate configuration selection still works with typed and saved passwords,
- preset selection/save/delete still works, including partial presets and stale-selection refresh behavior,
- visible-signature setup still round-trips through `VisibleSignatureSetupDraft`,
- preview and readiness still react correctly after setup changes,
- the shell is thinner because setup orchestration moved into the deeper boundary,
- and the relevant focused test suites pass cleanly.

This parent plan is complete. Both child plans are complete and the final compliance review found no mismatches.

## Idempotence and Recovery

The child plans are ordered so the work can be retried safely. If Child A lands but Child B reveals migration trouble, the deeper coordinator can remain in place while the shell continues using compatibility shims temporarily. Do not merge unrelated product-surface redesign into this effort. The allowed change classes here are:

- behavior-preserving architecture refactor,
- focused test replacement,
- documentation/status update.

Do not mix unrelated signing features, packaging changes, or review-card work into this parent effort.

## Artifacts and Notes

Pre-refactor evidence:

    `SignaturePropertiesPanel` still owns:
    - certificate configuration widgets and password reads
    - preset widgets and save/delete confirmation flow
    - reload choreography for certificate and preset selectors
    - dirty-preset clearing triggers after visible-signature edits
    - selected-name mirroring and workflow-facing reload logic

These are the responsibilities this parent effort is meant to concentrate behind a deeper boundary.

## Interfaces and Dependencies

The intended final boundary remains local-substitutable:

- `SigningDraftWorkflow` stays the source of truth.
- The application boundary may depend on `CertificateCatalogStore`, `SignaturePresetCatalogStore`, and `CertificateSecretProvider`.
- Qt-specific concerns remain in `signing_shell.py`, `visible_signature_setup_form.py`, and the preview/sidebar modules.

At the end of the full effort, the shell should depend primarily on:

- a deeper coordinator-style setup boundary with `load()` and explicit command reconciliation,
- the visible-signature setup form as a Qt editor port for draft load/build behavior,
- and stable state objects returned from the application layer.

Revision note: created on 2026-05-24 to coordinate the multi-slice refactor that deepens the current signing setup boundary.
