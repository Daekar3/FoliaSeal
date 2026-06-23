# Remove the panel-facing resolved-preset leak from signing setup

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the Qt signing-properties panel will still let users save the current signing setup as a reusable signature preset, update the preset selector, and preserve all existing overwrite/error behavior. The visible behavior should not change.

The architectural win is narrower caller ownership. `SigningSetupSession` already owns the save orchestration and returns `SignaturePropertiesViewState`, but `SignaturePropertiesPanel.save_current_signature_preset()` still leaks the legacy `ResolvedSignaturePreset` object back to callers. This slice keeps callers on the setup-session state boundary by making the panel return refreshed state (or `None`) instead of a resolved schema object.

## Child ExecPlan Dependencies

- [x] (2026-06-23 22:58Z) The reusable-signing-object architecture exploration is complete and the hybrid direction is chosen: keep `SigningSetupSession` as the primary deep-module boundary for callers.
- [x] (2026-06-23 22:58Z) No child ExecPlans are required for this narrow first tracer-bullet slice.

## Progress

- [x] (2026-06-23 22:58Z) Re-read `signing_workspace_properties_panel.py`, `signing_setup_session.py`, the relevant shell tests, and the hybrid recommendation.
- [x] (2026-06-23 22:58Z) Completed the required `explorer-light` dev-loop audit and fixed the first slice at the `ResolvedSignaturePreset` leak in `SignaturePropertiesPanel.save_current_signature_preset()`.
- [x] (2026-06-23 23:01Z) Added a focused failing test on the overwrite-confirmation shell path that stops treating `panel.save_current_signature_preset()` as a resolved-preset-returning API.
- [x] (2026-06-23 23:01Z) Updated the panel boundary to return `SignaturePropertiesViewState | None` and kept the save orchestration inside `SigningSetupSession`.
- [x] (2026-06-23 23:02Z) Ran focused validation with the exact shell save tests, `test_signing_setup_session.py -k save_preset`, `ruff check`, and `git diff --check`; all passed.
- [x] (2026-06-23 23:04Z) Completed the required `explorer-light` compliance review; it found the slice architecture/spec compliant but surfaced one stale shell test that still asserted `result.name`.
- [x] (2026-06-23 23:05Z) Fixed the stale shell test and reran the expanded shell save set plus `ruff check` and `git diff --check`; all passed.
- [ ] Create the git commit for the finished slice.

## Surprises & Discoveries

- Observation: the panel already depends on `SigningSetupSession` for the real save orchestration.
  Evidence: `save_current_signature_preset()` calls `self._setup_session.save_preset(...)` and already applies the returned `SignaturePropertiesViewState`; the only remaining leak is the final `self._coordinator.preset_catalog.preset_named(name)` return value.

- Observation: the resolved-preset shape is still required deeper in the workflow/schema internals.
  Evidence: `SigningDraftWorkflow.capture_current_signature_setup(...)`, `SigningDraftWorkflow.apply_resolved_signature_preset(...)`, and `SignaturePresetCatalog.upsert_preset(...)` still depend on `ResolvedSignaturePreset`, so this slice must not widen into workflow/schema refactors.

- Observation: the generic `-k signature_preset_save` shell test filter did not hit the overwrite-confirmation path that still exposed the leak.
  Evidence: the targeted failing case was `tests/unit/test_qt_signing_shell.py::test_signing_shell_signature_preset_overwrite_requires_confirmation`, which failed on `ResolvedSignaturePreset` before the implementation change.

## Decision Log

- Decision: keep the first slice at the panel/session caller boundary only.
  Rationale: this is the smallest move that deepens the hybrid design without dragging schema persistence, workflow preset application, or catalog serialization into the same review.
  Date/Author: 2026-06-23 / Codex

- Decision: return refreshed state from `save_current_signature_preset()` instead of introducing a new preset-summary DTO yet.
  Rationale: the panel already consumes and applies `SignaturePropertiesViewState`, so using that existing caller-facing shape reduces migration cost and avoids premature new abstraction.
  Date/Author: 2026-06-23 / Codex

## Outcomes & Retrospective

Implementation and focused validation are complete. Panel callers no longer depend on `ResolvedSignaturePreset` for the save path; `save_current_signature_preset()` now returns refreshed `SignaturePropertiesViewState | None`, which matches the existing `SigningSetupSession.save_preset(...)` boundary.

The slice stayed narrow. It did not change workflow/schema/storage internals or the persisted preset format. The only remaining work is the compliance review and final commit.
The slice stayed narrow. It did not change workflow/schema/storage internals or the persisted preset format. The compliance review found one stale shell test outside the original focused set; after correcting that assertion, the slice remained compliant. Only the final commit remains.

## Context and Orientation

The reusable-signing-object seam currently spans schema/catalog types, the setup coordinator/session, the signing workflow, and the Qt properties panel. The chosen hybrid direction keeps `SigningSetupSession` as the primary deep-module boundary for callers and gradually removes legacy `ResolvedSignaturePreset` exposure from UI-facing paths.

Today, `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py` already delegates preset saving to `SigningSetupSession.save_preset(...)`, receives a `SignaturePropertiesViewState`, applies it to the UI, and notifies change. But after doing that, it still returns `self._coordinator.preset_catalog.preset_named(name)`, which exposes `ResolvedSignaturePreset` again. That means callers and tests can keep depending on the transitional resolved-preset shape even though the setup session already provides a better boundary.

The relevant files for this slice are `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py`, `src/foliaseal/application/signing_setup_session.py`, `tests/unit/test_qt_signing_shell.py`, and optionally `tests/unit/test_signing_setup_session.py` if a small direct save-state assertion is useful. This slice must not alter `signing_draft_workflow.py`, `infra/config/schemas.py`, or preset storage behavior.

## Plan of Work

First, tighten the focused shell tests in `tests/unit/test_qt_signing_shell.py`. Replace assertions that treat `panel.save_current_signature_preset()` as returning a resolved preset object with assertions on refreshed panel state and persisted catalog behavior instead. The test should fail if code still expects `.name` from a returned `ResolvedSignaturePreset`.

Second, edit `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py`. Change `save_current_signature_preset()` to return the `SignaturePropertiesViewState` produced by `SigningSetupSession.save_preset(...)`, or `None` on cancel/error, instead of resolving and returning the saved preset object from the coordinator catalog. Leave overwrite prompts, error dialogs, `_apply_coordinator_state(...)`, and `_notify_change()` exactly as they are.

Third, update any adjacent tests that rely on the old return type only if needed. Prefer replacing internal-object assertions with UI-state and persisted-catalog assertions.

Finally, run focused validation and the required compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this ExecPlan. Only update docs if the review finds a real mismatch.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Add the focused failing test.

       apply_patch ... on tests/unit/test_qt_signing_shell.py
       .venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py -k signature_preset_save

2. Update the panel boundary.

       apply_patch ... on src/foliaseal/presentation/qt/signing_workspace_properties_panel.py

3. Re-run focused validation.

       .venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py -k signature_preset_save
       .venv/bin/python -m pytest -q tests/unit/test_signing_setup_session.py -k save_preset
       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/signing_workspace_properties_panel.py tests/unit/test_qt_signing_shell.py tests/unit/test_signing_setup_session.py
       git diff --check

4. Perform the compliance review and create the commit.

## Validation and Acceptance

This slice is accepted when all of the following are true:

- `SignaturePropertiesPanel.save_current_signature_preset()` no longer returns `ResolvedSignaturePreset`;
- callers still see the same save/overwrite/error behavior;
- the saved preset still persists correctly and the panel still selects it after save;
- `SigningSetupSession` remains the public caller-facing save boundary for this path; and
- no workflow/schema/storage refactor is mixed into the slice.

Run:

    .venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py -k signature_preset_save

Then run:

    .venv/bin/python -m pytest -q tests/unit/test_signing_setup_session.py -k save_preset
    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/signing_workspace_properties_panel.py tests/unit/test_qt_signing_shell.py tests/unit/test_signing_setup_session.py
    git diff --check

Acceptance is behavioral. The UI flow should stay the same, but the caller-facing return type must move one step closer to the setup-session state boundary.

## Idempotence and Recovery

This is a behavior-preserving boundary cleanup inside Qt presentation code. It is safe to retry. If a caller unexpectedly needs direct preset details after save, add that through the session/state boundary in a later slice instead of restoring the resolved-preset return.

Do not widen recovery into `ResolvedSignaturePreset` removal from schema/workflow internals. That is a later slice with much broader persistence and workflow impact.

## Artifacts and Notes

The most important final evidence for this slice will be:

- a smaller `save_current_signature_preset()` caller contract in `signing_workspace_properties_panel.py`;
- focused tests that assert on refreshed panel state and persisted catalog contents instead of returned `ResolvedSignaturePreset` shape; and
- green focused validation proving the visible behavior stayed the same.

Validation evidence:

    $ .venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py::test_signing_shell_signature_preset_overwrite_requires_confirmation tests/unit/test_qt_signing_shell.py::test_signing_shell_signature_preset_save_without_name_reports_error
    ..                                                                       [100%]
    2 passed in 0.32s

    $ .venv/bin/python -m pytest -q tests/unit/test_signing_setup_session.py -k save_preset
    .                                                                        [100%]
    1 passed, 10 deselected in 0.24s

    $ .venv/bin/python -m ruff check src/foliaseal/presentation/qt/signing_workspace_properties_panel.py tests/unit/test_qt_signing_shell.py tests/unit/test_signing_setup_session.py
    All checks passed!

    $ git diff --check
    <no output>

    $ explorer-light compliance review
    Compliant overall; one stale shell test assertion updated from `result.name` to `result.selected_signature_preset_name`.

    $ .venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py::test_signing_shell_signature_preset_save_uses_setup_session_entrypoint tests/unit/test_qt_signing_shell.py::test_signing_shell_signature_preset_overwrite_requires_confirmation tests/unit/test_qt_signing_shell.py::test_signing_shell_signature_preset_save_without_name_reports_error
    ...                                                                      [100%]
    3 passed in 0.72s

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

At the end of this slice, the important caller-facing boundary should remain:

    class SigningSetupSession:
        def save_preset(...) -> SignaturePropertiesViewState: ...

and the panel should stay aligned with that boundary:

    class SignaturePropertiesPanel:
        def save_current_signature_preset(self) -> SignaturePropertiesViewState | None: ...

This slice must not change `SigningDraftWorkflow.capture_current_signature_setup(...)`, `SigningDraftWorkflow.apply_resolved_signature_preset(...)`, `SignaturePresetCatalog.upsert_preset(...)`, or the persisted preset catalog format.

Revision note: Created on 2026-06-23 by Codex as the first `dev-loop` tracer bullet for the reusable-signing-object hybrid seam. This slice intentionally removes only the panel-facing `ResolvedSignaturePreset` leak.
