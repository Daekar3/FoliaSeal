# Remove the panel-facing preset-catalog leak from signing setup delete

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the Qt signing-properties panel will still let users delete a saved signature preset with confirmation, refresh the preset selector, and preserve all existing delete behavior. The visible behavior should not change.

The architectural win is symmetry and narrower caller ownership. The save path already stays on the `SigningSetupSession` state boundary after the previous slice, but `SignaturePropertiesPanel.delete_current_signature_preset()` still returns `SignaturePresetCatalog | None`. This slice removes that last obvious panel-facing reusable-signing-object leak by returning `SignaturePropertiesViewState | None` instead.

## Child ExecPlan Dependencies

- [x] (2026-06-23 23:12Z) `docs/ExecPlans/signing_setup_session_panel_boundary_execplan.md` is complete; the save path already stays on the setup-session state boundary.
- [x] (2026-06-23 23:12Z) No child ExecPlans are required for this narrow delete-path tracer bullet.

## Progress

- [x] (2026-06-23 23:12Z) Re-read `signing_workspace_properties_panel.py`, the relevant shell delete tests, and the setup-session architecture notes.
- [x] (2026-06-23 23:12Z) Completed the required `explorer-light` dev-loop audit and fixed the next slice at the delete-path `SignaturePresetCatalog` leak in `SignaturePropertiesPanel.delete_current_signature_preset()`.
- [x] (2026-06-23 23:14Z) Added a focused failing test that stops treating `panel.delete_current_signature_preset()` as a preset-catalog-returning API.
- [x] (2026-06-23 23:14Z) Updated the panel delete boundary to return `SignaturePropertiesViewState | None` and corrected the stale older ExecPlan interface note.
- [x] (2026-06-23 23:15Z) Ran focused validation with the two shell delete tests, `ruff check`, and `git diff --check`; all passed.
- [x] (2026-06-23 23:16Z) Completed the required `explorer-light` compliance review; the reviewer found the slice compliant with `docs/ARCHITECTURE.md` and `docs/SPEC.md`, and no further correction was needed.
- [x] (2026-08-16) Revalidated the current delete boundary with the focused preset/form suite
  and confirmed the completed implementation is present in the clean checkout; this plan's stale
  commit marker is now reconciled in the closeout documentation commit.

## Surprises & Discoveries

- Observation: the delete path is now the mirror-image leak after the save path was cleaned up.
  Evidence: `save_current_signature_preset()` already returns `SignaturePropertiesViewState | None`, but `delete_current_signature_preset()` still returns `SignaturePresetCatalog | None` after applying state from `SigningSetupSession.delete_preset(...)`.

- Observation: one older execplan still documents the pre-hybrid panel interface.
  Evidence: `docs/ExecPlans/schema_model_alignment_slice3c_preset_terminology_execplan.md` still lists `delete_current_signature_preset() -> SignaturePresetCatalog | None`, which becomes stale once this slice lands.

## Decision Log

- Decision: keep this slice limited to the panel delete caller boundary.
  Rationale: this is the smallest remaining caller-facing reusable-object leak after the save-path cleanup. It deepens the hybrid boundary without widening into coordinator, workflow, or storage refactors.
  Date/Author: 2026-06-23 / Codex

- Decision: return `SignaturePropertiesViewState` from delete instead of introducing a new delete-result type.
  Rationale: the panel already re-renders from that state, so reusing the existing session-facing shape keeps migration cost low and preserves consistency with the save-path slice.
  Date/Author: 2026-06-23 / Codex

## Outcomes & Retrospective

Implementation and focused validation are complete. Panel callers no longer depend on `SignaturePresetCatalog` for the delete path; `delete_current_signature_preset()` now returns refreshed `SignaturePropertiesViewState | None`, matching the existing `SigningSetupSession.delete_preset(...)` boundary.

The slice stayed narrow. It did not change coordinator/workflow/store internals or the persisted
preset format. The compliance review confirmed the current architecture/spec docs already match
this boundary. Current callers and tests confirm the boundary, and the historical commit marker is
reconciled.

## Context and Orientation

The reusable-signing-object hybrid keeps `SigningSetupSession` as the primary deep-module boundary for callers. The first tracer-bullet already removed the `ResolvedSignaturePreset` leak from `save_current_signature_preset()`. The next smallest move is to mirror that cleanup on delete.

Today, `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py` already delegates delete orchestration to `SigningSetupSession.delete_preset(...)`, receives a `SignaturePropertiesViewState`, applies it to the UI, and notifies change. But after that, it still returns `self._coordinator.preset_catalog`, which exposes the transitional catalog object again. The panel caller should stay on the same state boundary it already uses internally.

The relevant files for this slice are `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py`, `tests/unit/test_qt_signing_shell.py`, this ExecPlan, and the one stale interface list in `docs/ExecPlans/schema_model_alignment_slice3c_preset_terminology_execplan.md`. This slice must not alter `SigningSetupSession.delete_preset(...)`, `SignaturePresetCatalog.remove_preset(...)`, `SignaturePresetCatalogStore.delete_preset(...)`, or any persisted preset schema.

## Plan of Work

First, tighten the focused shell delete tests in `tests/unit/test_qt_signing_shell.py`. Replace assertions that treat `panel.delete_current_signature_preset()` as returning a `SignaturePresetCatalog` with assertions on refreshed selection state and persisted catalog contents instead. The test should fail if code still expects `result.preset_names()`.

Second, edit `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py`. Change `delete_current_signature_preset()` to return the `SignaturePropertiesViewState` produced by `SigningSetupSession.delete_preset(...)`, or `None` on cancel/error, instead of returning the coordinator catalog after the delete. Leave confirmation prompts, error dialogs, `_apply_coordinator_state(...)`, and `_notify_change()` as they are.

Third, update the stale interface note in `docs/ExecPlans/schema_model_alignment_slice3c_preset_terminology_execplan.md` so it no longer claims the panel returns `SignaturePresetCatalog | None` for delete. Keep that doc update limited to interface accuracy; do not reopen that older plan.

Finally, run focused validation and the required compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and the touched ExecPlans. Only change `docs/ARCHITECTURE.md` if the review finds a real mismatch.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Add the focused failing test.

       apply_patch ... on tests/unit/test_qt_signing_shell.py
       .venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py::test_signing_shell_signature_preset_delete_requires_confirmation_and_refreshes_catalog

2. Update the panel delete boundary and the stale interface note.

       apply_patch ... on src/foliaseal/presentation/qt/signing_workspace_properties_panel.py
       apply_patch ... on docs/ExecPlans/schema_model_alignment_slice3c_preset_terminology_execplan.md

3. Re-run focused validation.

       .venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py::test_signing_shell_signature_preset_delete_requires_confirmation_and_refreshes_catalog tests/unit/test_qt_signing_shell.py::test_signing_shell_signature_preset_delete_cancellation_keeps_catalog_intact
       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/signing_workspace_properties_panel.py tests/unit/test_qt_signing_shell.py
       git diff --check

4. Perform the compliance review and create the commit.

## Validation and Acceptance

This slice is accepted when all of the following are true:

- `SignaturePropertiesPanel.delete_current_signature_preset()` no longer returns `SignaturePresetCatalog`;
- callers still see the same delete confirmation, selector refresh, and persisted catalog behavior;
- the panel still deselects the removed preset after delete;
- the stale older ExecPlan interface note is corrected; and
- no coordinator/workflow/store/persistence refactor is mixed into the slice.

Run:

    .venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py::test_signing_shell_signature_preset_delete_requires_confirmation_and_refreshes_catalog tests/unit/test_qt_signing_shell.py::test_signing_shell_signature_preset_delete_cancellation_keeps_catalog_intact

Then run:

    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/signing_workspace_properties_panel.py tests/unit/test_qt_signing_shell.py
    git diff --check

Acceptance is behavioral. The delete flow should stay the same, but the caller-facing return type must stay on the setup-session state boundary instead of the catalog object.

## Idempotence and Recovery

This is a behavior-preserving boundary cleanup inside Qt presentation code. It is safe to retry. If a caller unexpectedly needs catalog details after delete, expose those through the session/state boundary in a later slice rather than restoring the catalog return from the panel.

Do not widen recovery into `SignaturePresetCatalog` or store refactors. The point here is only to remove the panel-facing leak.

## Artifacts and Notes

The most important final evidence for this slice will be:

- a smaller `delete_current_signature_preset()` caller contract in `signing_workspace_properties_panel.py`;
- focused shell delete tests that assert on refreshed state and persisted catalog contents instead of `SignaturePresetCatalog` shape; and
- one corrected older ExecPlan interface note.

Validation evidence:

    $ .venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py::test_signing_shell_signature_preset_delete_can_be_canceled_and_keeps_preset tests/unit/test_qt_signing_shell.py::test_signing_shell_signature_preset_delete_requires_confirmation_and_refreshes_catalog
    ..                                                                       [100%]
    2 passed in 0.33s

    $ .venv/bin/python -m ruff check src/foliaseal/presentation/qt/signing_workspace_properties_panel.py tests/unit/test_qt_signing_shell.py
    All checks passed!

    $ git diff --check
    <no output>

    $ explorer-light compliance review
    Compliant; no additional docs or code correction required.

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

At the end of this slice, the important caller-facing boundary should remain:

    class SigningSetupSession:
        def delete_preset(...) -> SignaturePropertiesViewState: ...

and the panel should align with it:

    class SignaturePropertiesPanel:
        def delete_current_signature_preset(self) -> SignaturePropertiesViewState | None: ...

This slice must not change `SignaturePresetCatalog.remove_preset(...)`, `SignaturePresetCatalogStore.delete_preset(...)`, or the persisted preset catalog format.

Revision note: Created on 2026-06-23 by Codex as the next `dev-loop` tracer bullet for the reusable-signing-object hybrid seam. This slice intentionally removes only the panel-facing preset-catalog leak from the delete path.
