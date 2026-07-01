# Remove raw-shell fallback from the Phase 3 testing seam

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the live Phase 3 harness still behaves the same for real signing-workspace shells and for older fakes that expose `compat_surface`. What changes is the last bit of legacy ambiguity: the harness will no longer silently treat an arbitrary shell object as its testing seam.

The user-visible win is stability and clarity for the QA harness boundary. The production signing workspace already installs an explicit `testing_adapter`, so this slice makes the harness rely on an explicit testing or compatibility surface instead of raw shell anatomy. You can see the result by running the focused Qt harness tests and observing that preview capture still works through `testing_adapter` or `compat_surface`, while bare-shell fakes are rejected by the contract.

## Child ExecPlan Dependencies

- [x] (2026-07-01 01:07Z) `docs/ExecPlans/signing_workspace_testing_port_execplan.md` completed the first hybrid slice by introducing `SigningWorkspaceTestingPort` without widening the production shell port.
- [x] (2026-07-01 01:07Z) No child ExecPlans are required for this bounded follow-up slice.

## Progress

- [x] (2026-07-01 01:07Z) Reviewed the current post-`0df724f6e` seam and confirmed that `phase3_harness_workspace.py` still resolves `testing_adapter -> compat_surface -> raw shell`.
- [x] (2026-07-01 01:07Z) Used an `explorer-light` subagent to identify the next smallest safe slice: remove only the raw-shell fallback and update the two preview-render tests that still depend on it.
- [x] (2026-07-01 01:12Z) Removed the raw-shell fallback branch from `src/foliaseal/presentation/qt/phase3_harness_workspace.py` and replaced it with an explicit contract error requiring `testing_adapter` or `compat_surface`.
- [x] (2026-07-01 01:14Z) Updated focused tests and `docs/ARCHITECTURE.md` so they describe and enforce the explicit seam (`testing_adapter` or `compat_surface`) instead of bare shell anatomy.
- [x] (2026-07-01 01:15Z) Ran focused validation: `.venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_qt_signing_shell.py` passed with `108 passed in 10.33s`; `.venv/bin/python -m ruff check ...` passed; `git diff --check` passed.
- [x] (2026-07-01 01:19Z) Completed the compliance review against `docs/ARCHITECTURE.md` and `docs/SPEC.md`; the only issue was one stale repository-map sentence in `docs/ARCHITECTURE.md`, which was corrected in this slice without a second code iteration.

## Surprises & Discoveries

- Observation: the remaining fallback debt is narrower than it first appears because production composition already installs `testing_adapter`.
  Evidence: `src/foliaseal/presentation/qt/signing_workspace_composition.py` bootstraps `SigningWorkspaceCompatibilitySurface.install_widget_exports()`, which exports both `compat_surface` and `testing_adapter`.

- Observation: the only in-tree raw-shell consumers left in the focused workspace tests are the two `capture_qt_preview_render(...)` tests.
  Evidence: `tests/unit/test_qt_phase3_harness_workspace.py` still creates bare shells with only `properties_panel` around the preview-render assertions.

- Observation: after the slice, the focused workspace suite gained one additional passing test because the new contract is now asserted directly.
  Evidence: focused validation passed with `108 passed in 10.33s`, up from the earlier `107 passed`.

- Observation: the compliance review found only one stale architecture summary sentence; the more specific component entries were already aligned with the new code.
  Evidence: the review flagged `docs/ARCHITECTURE.md` repository-map wording while confirming the updated `phase3_harness_workspace.py` entries and `docs/SPEC.md` remained compliant.

## Decision Log

- Decision: keep the `compat_surface` fallback for one more slice while removing the raw-shell fallback now.
  Rationale: this reduces legacy ambiguity without breaking the older fake-shell shape that still appears throughout focused tests, and it preserves the narrow production shell port.
  Date/Author: 2026-07-01 / Codex

- Decision: fix the stale repository-map sentence inside this slice instead of opening a doc-only follow-up.
  Rationale: the mismatch was directly caused by the seam change, the correction was isolated to one sentence, and leaving it stale would make the living plan less restartable.
  Date/Author: 2026-07-01 / Codex

## Outcomes & Retrospective

This slice removed the last untyped fallback in the harness seam while preserving the explicit transitional compatibility surface. Every focused live harness path now enters through `testing_adapter` or `compat_surface`, and future legacy fakes must model one of those contracts explicitly instead of depending on bare shell anatomy. The compliance review found only one stale architecture summary sentence, which this slice corrected without needing a second code iteration.

## Context and Orientation

The live Phase 3 harness workspace boundary lives in `src/foliaseal/presentation/qt/phase3_harness_workspace.py`. That module owns two adapters: `HeadlessPhase3HarnessWorkspaceAdapter` for direct workflow mutation without Qt, and `QtPhase3HarnessWorkspaceAdapter` for a live signing shell. The live adapter currently resolves its testing surface with `_testing_surface(shell)`, which first prefers `shell.testing_adapter`, then wraps `shell.compat_surface`, and finally wraps the shell object itself. That last fallback is the ambiguity this slice removes.

The explicit non-production contract already exists in `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py` as `SigningWorkspaceTestingPort`. The concrete signing shell installs that seam during composition by exporting `widget.compat_surface` and `widget.testing_adapter`. Because production already exposes the explicit seam, this slice does not need to edit `signing_workspace_composition.py` or widen `signing_workspace_shell_surface.py`.

The focused tests for this area live in `tests/unit/test_qt_phase3_harness_workspace.py` and `tests/unit/test_qt_signing_shell.py`. Most live-shell tests already model `compat_surface` or `testing_adapter`, but the two preview-render tests still construct bare shells with only `properties_panel`. Those tests should be updated to provide an explicit compatibility surface instead.

`docs/ARCHITECTURE.md` currently says the live harness path falls back to `compat_surface` or the shell itself. After this slice it must instead say that the live path falls back only to a compatibility wrapper over `compat_surface`.

## Plan of Work

First, edit `src/foliaseal/presentation/qt/phase3_harness_workspace.py`. Keep the `testing_adapter` preference and the compatibility wrapper around `compat_surface`, but replace the final raw-shell fallback with an explicit `TypeError` that says the shell must expose either `testing_adapter` or `compat_surface` for Phase 3 harness access. This keeps the failure narrow and obvious for future fake shells.

Second, edit `tests/unit/test_qt_phase3_harness_workspace.py`. Update the two `capture_qt_preview_render(...)` tests so the fake shell exposes a minimal `compat_surface` object carrying `properties_panel`. Add one focused test that proves a bare shell without `testing_adapter` or `compat_surface` is rejected with the new explicit error.

Third, reconcile `docs/ARCHITECTURE.md` so the `phase3_harness_workspace.py` entry and the known architectural debt note stop claiming that the live harness still falls back to the shell itself. The architecture text should match the new state precisely: `testing_adapter` first, then `compat_surface` through a wrapper, nothing else.

Finally, run focused validation. If the compliance review finds only stale architecture wording, fix it in this same slice. If it finds a production caller still relying on raw-shell fallback, stop and document that before widening any port.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Update the workspace seam and focused tests.

       apply_patch ... on src/foliaseal/presentation/qt/phase3_harness_workspace.py
       apply_patch ... on tests/unit/test_qt_phase3_harness_workspace.py
       apply_patch ... on docs/ARCHITECTURE.md
       apply_patch ... on docs/ExecPlans/signing_workspace_raw_shell_fallback_removal_execplan.md

2. Run focused validation.

       .venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_qt_signing_shell.py
       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_harness_workspace.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_qt_signing_shell.py
       git diff --check

   Observed result:

       108 passed in 10.33s
       All checks passed!

## Validation and Acceptance

This slice is accepted when all of the following are true:

- the live harness no longer wraps the raw shell object as a testing surface;
- `testing_adapter` remains the preferred path for real shells;
- `compat_surface` continues to work through the compatibility wrapper for older fake shells;
- preview-render tests model an explicit compatibility surface rather than a bare shell;
- focused tests, lint, and whitespace checks pass.

Run:

    .venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_qt_signing_shell.py

Then run:

    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_harness_workspace.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_qt_signing_shell.py
    git diff --check

Acceptance is behavioral. The live harness should still capture and mutate preview state through the explicit testing seam, but a fake that exposes only arbitrary shell anatomy should now fail fast instead of being silently accepted.

## Idempotence and Recovery

This is a behavior-preserving refactor for real shells and an intentional contract-tightening for fake shells. It is safe to retry. If a test breaks because a fake shell no longer exposes a supported seam, repair the fake by adding `testing_adapter` or `compat_surface`; do not reintroduce the raw-shell fallback.

## Artifacts and Notes

The key evidence for this slice will be:

- `src/foliaseal/presentation/qt/phase3_harness_workspace.py` raising a clear contract error instead of wrapping the raw shell;
- updated preview-render tests in `tests/unit/test_qt_phase3_harness_workspace.py`;
- focused validation output showing the harness still works through explicit seams only.

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

The important interface remains:

    class SigningWorkspaceTestingPort(Protocol):
        properties_panel: SignaturePropertiesPanel
        def signature_appearance(...) -> SignatureAppearance | None
        def set_timestamp_required(...) -> None
        def apply_signature_rect_placement(...) -> None
        def refresh_viewer(...) -> None
        def current_request(...) -> SigningRequest | None
        def last_signing_result(...) -> SigningResult | None

At the end of this slice, `QtPhase3HarnessWorkspaceAdapter` still accepts a live shell object, but the shell must expose one of two explicit seams:

    shell.testing_adapter
    shell.compat_surface

The raw shell object itself is no longer a valid implicit harness surface.
