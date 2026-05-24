# Migrate the Qt shell to the deeper signing setup boundary

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with [.agents/skills/write-execplan/PLANS.md](/home/daekar/FoliaSeal/.agents/skills/write-execplan/PLANS.md).

## Purpose / Big Picture

After this slice, the Qt signing shell should behave like a thin adapter over the deeper current-signing-setup boundary created in Child A. A user should see the same certificate configuration, preset, and visible-signature setup behavior, but the shell should own much less orchestration, and many white-box shell tests should become unnecessary or thinner.

This is the second child slice of the parent effort in [signing_setup_boundary_parent_execplan.md](/home/daekar/FoliaSeal/docs/ExecPlans/signing_setup_boundary_parent_execplan.md). It starts only after the deeper coordinator behavior exists.

## Child ExecPlan Dependencies

- [ ] Child A in [signing_setup_boundary_coordinator_deepening_execplan.md](/home/daekar/FoliaSeal/docs/ExecPlans/signing_setup_boundary_coordinator_deepening_execplan.md) must be complete before this plan begins.

## Progress

- [x] (2026-05-24 20:18Z) Recorded the child plan before implementation.
- [ ] Rewire `SignaturePropertiesPanel` to render setup state from the deeper coordinator boundary and reduce shell-owned setup synchronization.
- [ ] Replace redundant white-box shell tests with boundary tests where the deeper coordinator now carries the behavior.
- [ ] Perform compliance review against `docs/SPEC.md` and `docs/ARCHITECTURE.md`.
- [ ] Update docs and close out the parent plan.

## Surprises & Discoveries

- Observation: many shell tests are really setup-behavior tests in disguise.
  Evidence: preset save/reload, preset selection, and certificate configuration tests in `tests/unit/test_qt_signing_shell.py` still reach into private widget bags and catalog state instead of testing a stable setup boundary.

- Observation: not all setup behavior can leave the shell.
  Evidence: confirmation dialogs for overwrite/delete and raw widget composition are still Qt presentation concerns and should stay there.

## Decision Log

- Decision: move behavior tests out of the shell only when a deeper boundary now exists to own that behavior.
  Rationale: deleting shell tests without a real replacement would reduce coverage rather than deepen the module.
  Date/Author: 2026-05-24 / Codex

- Decision: keep user confirmation dialogs in the shell.
  Rationale: dialog display is a presentation concern even if the resulting commands go through the deeper boundary.
  Date/Author: 2026-05-24 / Codex

## Outcomes & Retrospective

This section will be completed after the slice is implemented and validated.

## Context and Orientation

`SignaturePropertiesPanel` in [src/foliaseal/presentation/qt/signing_shell.py](/home/daekar/FoliaSeal/src/foliaseal/presentation/qt/signing_shell.py) currently mixes:

- Qt widget construction for certificate and preset controls,
- user-facing confirmation dialogs,
- selector reload logic,
- selected-name synchronization,
- and command forwarding to the coordinator.

The form boundary in [src/foliaseal/presentation/qt/visible_signature_setup_form.py](/home/daekar/FoliaSeal/src/foliaseal/presentation/qt/visible_signature_setup_form.py) is already fairly cohesive, so this child plan is mainly about making the shell consume the deeper setup boundary from Child A rather than coordinating setup behavior itself.

Relevant files:

- `src/foliaseal/presentation/qt/signing_shell.py`
- `src/foliaseal/presentation/qt/visible_signature_setup_form.py`
- `tests/unit/test_qt_signing_shell.py`
- `tests/unit/test_signature_properties_coordinator.py`
- `docs/ARCHITECTURE.md`

## Plan of Work

First, identify every setup-related shell method that can become “read widget intent -> issue command -> render returned state” after Child A. The likely targets are:

- certificate configuration apply/reload handlers,
- preset apply/save/delete handlers,
- selector reload helpers,
- and dirty-preset clearing flow around visible-signature edits.

Second, migrate `SignaturePropertiesPanel` so its setup render path is driven by the deeper coordinator state. Where the shell still needs helper methods, keep them presentation-focused: dialog confirmation, user-visible error messaging, and widget rendering only.

Third, audit [tests/unit/test_qt_signing_shell.py](/home/daekar/FoliaSeal/tests/unit/test_qt_signing_shell.py) and replace redundant white-box setup tests with coordinator boundary tests where possible. The shell suite should keep thin integration checks that prove the Qt adapter wires the deeper boundary correctly.

Finally, update [docs/ARCHITECTURE.md](/home/daekar/FoliaSeal/docs/ARCHITECTURE.md) so it accurately describes the thinner shell and the deeper setup boundary.

## Concrete Steps

From `/home/daekar/FoliaSeal`, implement and validate this slice with:

    pytest tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py
    ruff check src/foliaseal/presentation/qt/signing_shell.py src/foliaseal/presentation/qt/visible_signature_setup_form.py src/foliaseal/application/signature_properties_coordinator.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py
    git diff --check

Manual acceptance target after this child slice:

    .venv/bin/foliaseal gui --pdf-path "/path/to/example.pdf"

Expected behavior:

- certificate configuration and preset flows still work,
- visible-signature setup still works,
- the shell has less private synchronization logic in the setup area,
- and setup behavior coverage shifts toward the deeper application boundary.

## Validation and Acceptance

Acceptance is behavioral:

- the shell still surfaces the same user actions and errors,
- setup behavior continues to work end to end,
- coordinator tests carry more of the setup semantics,
- shell tests become thinner where deeper boundary tests now exist,
- and `docs/ARCHITECTURE.md` matches the implemented ownership split.

This child slice is complete when the shell is materially thinner in the signing-setup area and the test suite reflects that new boundary.

## Idempotence and Recovery

This slice is safe to retry after Child A. If some white-box shell tests still provide unique value, keep them temporarily and mark the remaining debt explicitly instead of forcing deletion for its own sake. Avoid mixing unrelated preview, review-card, or output-path work into this migration.

## Artifacts and Notes

Pre-change evidence:

    `tests/unit/test_qt_signing_shell.py` still contains setup-heavy white-box tests that:
    - poke `_certificate_controls`
    - poke `_signature_preset_controls`
    - inspect `_preset_catalog`
    - rely on selector reload details

These tests should be replaced only where a deeper boundary now provides equivalent behavioral coverage.

## Interfaces and Dependencies

This child plan depends on the deeper application boundary from Child A and the existing Qt form boundary:

- `SignaturePropertiesCoordinator`
- `SignaturePropertiesViewState`
- `QtVisibleSignatureSetupForm`

The shell should continue to own:

- widget construction for certificate/preset controls,
- confirmation dialogs,
- and user-visible error display.

The shell should stop owning:

- as much setup-state synchronization as the deeper coordinator can reasonably own,
- and redundant white-box setup test coverage where boundary tests now exist.

Revision note: created on 2026-05-24 as Child B of the current signing setup boundary refactor.
