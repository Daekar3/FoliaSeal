# Move Preset Save/Delete Orchestration Behind SigningSetupSession

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with [`.agents/skills/write-execplan/PLANS.md`](/home/daekar/FoliaSeal/.agents/skills/write-execplan/PLANS.md).

## Purpose / Big Picture

The previous slice extracted the common signing-setup workflow into `SigningSetupSession`, but preset mutation is still split: `SignaturePropertiesPanel` still decides how preset saves and deletes are validated, when overwrite detection happens, which coordinator command runs, and how the returned state gets applied. This slice continues the same hybrid by moving preset save/delete orchestration behind explicit session verbs while keeping Qt confirmation dialogs in the panel.

The user-visible behavior should stay the same. Saving a preset should still require a name, still ask before overwriting an existing preset, and still refresh the selector state after success. Deleting a preset should still require a selection, still ask for confirmation, and still remove the deleted preset from the selector/catalog. The change is architectural: preset mutation should look like the other setup actions and no longer require the panel to talk directly to `SaveCurrentPreset` / `DeletePreset`.

## Child ExecPlan Dependencies

- [x] (2026-05-29 18:47Z) No child ExecPlans are required for this bounded slice.

## Progress

- [x] (2026-05-29 18:47Z) Reviewed the current save/delete flows in `src/foliaseal/presentation/qt/signing_shell.py`, the coordinator implementation in `src/foliaseal/application/signature_properties_coordinator.py`, and the affected shell/coordinator tests.
- [x] (2026-05-29 18:47Z) Wrote this ExecPlan and fixed the slice boundary at: preset save/delete orchestration only. Qt confirmation dialogs, preset-name text input, and preview rendering remain where they are.
- [x] (2026-05-29 21:39Z) Added explicit `save_preset(...)` and `delete_preset(...)` verbs to `SigningSetupSession`.
- [x] (2026-05-29 21:39Z) Migrated `SignaturePropertiesPanel` save/delete flows to call the session instead of coordinator commands directly.
- [x] (2026-05-29 21:39Z) Trimmed now-unused shell imports and removed the remaining direct panel dispatch of `SaveCurrentPreset` / `DeletePreset`.
- [x] (2026-05-29 21:39Z) Added direct setup-session tests for preset save/delete behavior and focused shell tests proving the panel now delegates to the session.
- [x] (2026-05-29 21:39Z) Ran focused validation with `pytest`, `ruff check`, and `git diff --check`.
- [x] (2026-05-29 21:39Z) Ran the required compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and `docs/SCHEMAS.md`, then addressed the remaining architecture-doc gap.
- [x] (2026-05-29 21:39Z) Updated documentation, including this ExecPlan, to final state.
- [ ] Commit the slice as one narrow architecture change.

## Surprises & Discoveries

- Observation: the previous setup-session slice left preset mutation as the clearest remaining direct coordinator dependency in `SignaturePropertiesPanel`.
  Evidence: `save_current_signature_preset()` and `delete_current_signature_preset()` still call `self._coordinator.reconcile(SaveCurrentPreset(...))` and `self._coordinator.reconcile(DeletePreset(...))` directly.

- Observation: the panel still needs to own the overwrite/delete confirmation dialogs, but it does not need to own the underlying preset mutation orchestration.
  Evidence: the current overwrite/delete branches are plain `QMessageBox.question(...)` checks followed by coordinator calls; the business rule is still coordinator-backed.

- Observation: one shell test imported `_ready_workflow` implicitly from another file context and failed only after the new direct save-entrypoint test started using it.
  Evidence: the first focused run failed with `NameError: name '_ready_workflow' is not defined` in the new save-entrypoint shell test; importing it from `tests.unit.test_signature_properties_coordinator` resolved the issue.

## Decision Log

- Decision: keep overwrite/delete confirmation dialogs in the panel for this slice.
  Rationale: those are explicitly Qt presentation concerns, while the mutation/reload/state-return logic is the orchestration concern that belongs in the session.
  Date/Author: 2026-05-29 / Codex

- Decision: use setup-session state to detect overwrite candidates instead of adding a new direct catalog helper to the session.
  Rationale: `SignaturePropertiesViewState.signature_preset_names` is already the stable session output needed by the panel, so a new helper would add surface area without increasing clarity.
  Date/Author: 2026-05-29 / Codex

## Outcomes & Retrospective

Implemented result:

- preset save/delete mutation no longer goes directly from `SignaturePropertiesPanel` to coordinator commands
- the panel still owns dialogs and text inputs, but preset mutation sequencing is aligned with the rest of the setup hybrid
- direct setup-session tests cover save/delete behavior
- `SPEC.md` and `SCHEMAS.md` behavior remains intact: reference-only preset persistence, overwrite confirmation, selector refresh, and delete clearing
- focused validation evidence:
  - `pytest tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py tests/unit/test_qt_signing_shell.py -q` -> `112 passed`
  - `ruff check src/foliaseal/application/signing_setup_session.py src/foliaseal/application/__init__.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_signing_setup_session.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py` -> passed
  - `git diff --check` -> passed

## Context and Orientation

The current preset-save path lives in [src/foliaseal/presentation/qt/signing_shell.py](/home/daekar/FoliaSeal/src/foliaseal/presentation/qt/signing_shell.py). The panel reads the preset name from Qt, checks whether a preset of that name already exists, shows an overwrite confirmation dialog if needed, dispatches `SaveCurrentPreset`, applies the returned state, and returns the saved preset from the coordinator catalog.

The current preset-delete path does the same kind of orchestration: it reads the selected preset name from Qt, enforces that the placeholder is not deletable, shows the delete confirmation dialog, dispatches `DeletePreset`, applies the returned state, and returns the updated catalog.

The new session boundary already owns the other common setup flows:

- `load()`
- `apply_visible_setup(...)`
- `select_signature_preset(...)`
- `clear_selected_signature_preset(...)`
- `select_certificate_configuration(...)`
- `refresh_catalogs(...)`

Save/delete is the obvious remaining gap in the same hybrid.

## Plan of Work

First, extend `SigningSetupSession` with explicit `save_preset(...)` and `delete_preset(...)` verbs. These should just compose the existing coordinator commands and return `SignaturePropertiesViewState`, not introduce a new command bus or a second persistence model.

Second, migrate `SignaturePropertiesPanel` so the save/delete flows call the session. The panel should still:

- own preset-name text input
- decide whether to show overwrite/delete confirmation dialogs
- show signature-preset error messages
- apply returned state to Qt controls and refresh preview

Third, add direct session tests for save/delete and focused shell tests proving the panel now delegates to the session rather than the coordinator directly for those mutation flows.

Finally, run focused validation, review compliance against `ARCHITECTURE.md`, `SPEC.md`, and `SCHEMAS.md`, update docs, and commit the slice.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Edit the session boundary, the signing shell, and focused tests.

       apply_patch ... on src/foliaseal/application/signing_setup_session.py
       apply_patch ... on src/foliaseal/presentation/qt/signing_shell.py
       apply_patch ... on tests/unit/test_signing_setup_session.py
       apply_patch ... on tests/unit/test_qt_signing_shell.py

2. Run focused validation.

       pytest tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py tests/unit/test_qt_signing_shell.py
       ruff check src/foliaseal/application/signing_setup_session.py src/foliaseal/application/__init__.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py tests/unit/test_qt_signing_shell.py
       git diff --check

3. Run the required compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and `docs/SCHEMAS.md`. If the review finds a mismatch, update this ExecPlan, implement the fix, and repeat validation before committing.

4. Update documentation and commit the slice.

## Validation and Acceptance

This slice is accepted when all of the following are true:

- preset save/delete orchestration goes through `SigningSetupSession`
- the panel no longer dispatches `SaveCurrentPreset` / `DeletePreset` directly
- overwrite/delete confirmation dialogs still live in the panel
- preset persistence and deletion still match `SCHEMAS.md`
- direct setup-session tests cover preset save/delete behavior
- focused shell tests still pass
- `docs/ARCHITECTURE.md` describes the updated setup-session boundary accurately

Run:

    pytest tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py tests/unit/test_qt_signing_shell.py

Then run:

    ruff check src/foliaseal/application/signing_setup_session.py src/foliaseal/application/__init__.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py tests/unit/test_qt_signing_shell.py
    git diff --check

Acceptance is behavior-preserving. There is no intended product-surface change in this slice.

## Idempotence and Recovery

This is a behavior-preserving refactor in local application/Qt presentation code. It is safe to retry. If the slice proves broader than expected, keep the save/delete verbs in the session even if the panel still temporarily handles one of the error or return-value branches directly. Do not move confirmation dialogs into the session as a shortcut.

## Artifacts and Notes

The most important evidence for this slice will be:

- the focused `pytest` result covering session, shell, and affected coordinator tests
- a clean `ruff check`
- a clean `git diff --check`
- the updated `docs/ARCHITECTURE.md` description of preset mutation inside the setup session boundary

These transcripts should be recorded back into this ExecPlan as work completes.

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

At the end of this slice, the setup seam should look approximately like:

    class SigningSetupSession(Protocol):
        def load(...) -> SignaturePropertiesViewState: ...
        def apply_visible_setup(...) -> SignaturePropertiesViewState: ...
        def select_signature_preset(...) -> SignaturePropertiesViewState | None: ...
        def clear_selected_signature_preset(...) -> SignaturePropertiesViewState: ...
        def select_certificate_configuration(...) -> SignaturePropertiesViewState | None: ...
        def refresh_catalogs(...) -> SignaturePropertiesViewState: ...
        def save_preset(...) -> SignaturePropertiesViewState: ...
        def delete_preset(...) -> SignaturePropertiesViewState: ...

The panel remains the Qt adapter for dialogs and widget rendering; the session remains the orchestration boundary above the coordinator.

Revision note: Created on 2026-05-29 by Codex for the next signing-setup session hybrid slice.
