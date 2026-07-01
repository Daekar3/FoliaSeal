# Add an explicit signing-workspace testing port

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the GUI and Phase 3 harness still behave the same. There is no intended user-visible workflow change.

The architectural win is that the signing workspace now exposes an explicit harness/testing contract instead of making `phase3_harness_workspace.py` discover behavior through ad hoc `testing_adapter`, `compat_surface`, and shell fallbacks. This is the first tracer bullet of the recommended hybrid: keep the production `SigningWorkspacePort` narrow, but make the non-production seam explicit and typed.

## Child ExecPlan Dependencies

- [x] (2026-07-01 00:12Z) The app-frame hybrid cleanup series is complete through `docs/ExecPlans/app_frame_module_raw_window_helper_removal_execplan.md`; this slice intentionally shifts to the recommended signing-workspace compatibility seam.
- [x] (2026-07-01 00:12Z) No child ExecPlans are required for this bounded first slice.

## Progress

- [x] (2026-07-01 00:12Z) Re-read `signing_workspace_compatibility_surface.py`, `phase3_harness_workspace.py`, current architecture notes, and focused tests to confirm the runtime already installs `testing_adapter` while the harness still performs its own fallback probing.
- [x] (2026-07-01 00:18Z) Added `SigningWorkspaceTestingPort` around the existing testing adapter without widening the production shell port.
- [x] (2026-07-01 00:20Z) Updated `phase3_harness_workspace.py` to depend on the new testing port while preserving the `compat_surface` fallback through a small compatibility wrapper.
- [x] (2026-07-01 00:23Z) Updated focused tests and `docs/ARCHITECTURE.md` to reflect the explicit testing-port contract.
- [x] (2026-07-01 00:31Z) Ran focused validation: `.venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_qt_phase3_harness_workspace.py` passed with `107 passed in 10.52s`; `.venv/bin/python -m ruff check ...` passed; `git diff --check` passed.
- [x] (2026-07-01 00:33Z) Completed the compliance review against `docs/ARCHITECTURE.md` and `docs/SPEC.md`; the slice is compliant and required no second iteration.

## Surprises & Discoveries

- Observation: the proposed hybrid already has a natural first seam because `SigningWorkspaceCompatibilitySurface` constructs and installs `testing_adapter` today.
  Evidence: `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py` initializes `_testing_adapter` and exports it on the widget.

- Observation: `phase3_harness_workspace.py` already prefers `testing_adapter` before `compat_surface`.
  Evidence: its `_testing_surface(...)` helper reads `shell.testing_adapter` first, then falls back to `compat_surface`, then the shell itself.

- Observation: the compliance review found the architecture text already aligned after the documentation update; only the debt note remains intentionally transitional.
  Evidence: the explorer review found no stale wording in the inspected `docs/ARCHITECTURE.md` sections and no `docs/SPEC.md` mismatch.

## Decision Log

- Decision: formalize the existing `testing_adapter` as `SigningWorkspaceTestingPort` before changing the deeper harness call graph.
  Rationale: this creates a real non-production contract with minimal graph churn and keeps the production `SigningWorkspacePort` untouched.
  Date/Author: 2026-07-01 / Codex

- Decision: keep the `compat_surface` fallback in this first slice.
  Rationale: older fake shells and focused tests still rely on that compatibility shape; retiring the fallback should be a later slice after call sites migrate.
  Date/Author: 2026-07-01 / Codex

## Outcomes & Retrospective

This slice turned an implementation detail into a typed seam. Focused tests, Ruff, and whitespace checks all passed, and the compliance review found no mismatch with the current architecture notes or the frozen product spec. The next logical seam is shrinking or removing the compatibility fallback once older fake shells no longer need it.

Revision note (2026-07-01 00:23Z): Updated the living plan after landing the code and architecture changes so the progress log and retrospective reflect the explicit testing-port contract and compatibility-wrapper fallback.

## Context and Orientation

The top-level signing workspace is built in `src/foliaseal/presentation/qt/signing_workspace_composition.py`. That composition root constructs both the narrow production shell surface in `signing_workspace_shell_surface.py` and the broad compatibility/testing surface in `signing_workspace_compatibility_surface.py`.

Today, `SigningWorkspaceCompatibilitySurface` creates a `SigningWorkspaceTestingAdapter` and installs it on the widget as `testing_adapter`. The Phase 3 harness boundary in `src/foliaseal/presentation/qt/phase3_harness_workspace.py` already prefers that adapter when present, but it still discovers the seam by probing `testing_adapter`, `compat_surface`, and finally the shell object itself. That means the architecture doc can describe a testing seam, but the code still relies on shell-shape duck typing.

The narrow cleanup is therefore to define an explicit `SigningWorkspaceTestingPort` protocol at the compatibility-surface layer, make the existing testing adapter implement it, and have the Phase 3 workspace boundary normalize its fallback path to that port. This keeps the current behavior and fallback semantics, but replaces “whatever shell shape is available” with “a known testing port contract.”

## Plan of Work

First, edit `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py`. Add a `SigningWorkspaceTestingPort` protocol that describes only the non-production verbs the harness needs right now. It should include the panel surface needed for scenario application and preview capture plus the current request/result and refresh/placement/timestamp methods. Keep `SigningWorkspaceTestingAdapter` as the concrete implementation and update property annotations accordingly.

Second, edit `src/foliaseal/presentation/qt/phase3_harness_workspace.py`. Import the new testing-port protocol. Replace the untyped `_testing_surface(...) -> Any` helper with a helper that returns a `SigningWorkspaceTestingPort`. Preserve the fallback semantics by wrapping `compat_surface` or the shell in a tiny compatibility adapter that conforms to the new port, rather than widening the protocol to match arbitrary shell anatomy.

Third, update focused tests. In `tests/unit/test_qt_signing_shell.py`, keep the assertion that the shell installs a distinct `testing_adapter`, and strengthen it to assert the adapter exposes the expected testing-port methods. In `tests/unit/test_qt_phase3_harness_workspace.py`, keep the preference and fallback tests but make them prove the harness adapter now consumes the explicit testing-port contract.

Fourth, reconcile `docs/ARCHITECTURE.md`. The Qt presentation summary and the `phase3_harness_workspace.py` component entry should say that the live harness path prefers an explicit `SigningWorkspaceTestingPort` installed by `signing_workspace_compatibility_surface.py`, then falls back through a compatibility wrapper for older fake shells.

Finally, run focused validation. If the compliance review finds only stale architecture wording, fix it in this slice. If it reveals that a real production caller now depends on the testing port, document that dependency instead of widening the production port.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Add the testing-port protocol and normalize the harness seam to it.

       apply_patch ... on src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py
       apply_patch ... on src/foliaseal/presentation/qt/phase3_harness_workspace.py

2. Update focused tests and architecture docs.

       apply_patch ... on tests/unit/test_qt_signing_shell.py
       apply_patch ... on tests/unit/test_qt_phase3_harness_workspace.py
       apply_patch ... on docs/ARCHITECTURE.md
       apply_patch ... on docs/ExecPlans/signing_workspace_testing_port_execplan.md

3. Run focused validation.

       .venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_qt_phase3_harness_workspace.py
       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py src/foliaseal/presentation/qt/phase3_harness_workspace.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_phase3_harness_workspace.py
       git diff --check

## Validation and Acceptance

This slice is accepted when all of the following are true:

- `SigningWorkspaceTestingPort` exists as an explicit protocol;
- `SigningWorkspaceTestingAdapter` implements that protocol;
- `phase3_harness_workspace.py` depends on the testing port rather than raw shell anatomy for its preferred path;
- the `compat_surface` fallback still works for older fake shells;
- focused tests, lint, and whitespace checks pass.

Run:

    .venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_qt_phase3_harness_workspace.py

Then run:

    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py src/foliaseal/presentation/qt/phase3_harness_workspace.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_phase3_harness_workspace.py
    git diff --check

Acceptance is behavioral. The harness should keep working the same, but the preferred live-shell seam should now be a typed testing port instead of an implementation detail.

## Idempotence and Recovery

This is a behavior-preserving refactor. It is safe to retry. If a fallback fake shell breaks, restore compatibility by extending only the tiny compatibility wrapper, not by widening the production shell port or reverting to ad hoc probing everywhere.

## Artifacts and Notes

The most important final evidence for this slice will be:

- `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py` defining `SigningWorkspaceTestingPort`;
- `src/foliaseal/presentation/qt/phase3_harness_workspace.py` normalizing fallback resolution to that port;
- focused tests proving the explicit testing adapter is preferred and the compatibility fallback still works;
- architecture text reflecting the explicit testing-port seam.

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

The important interfaces at the end of the slice should be:

    class SigningWorkspaceTestingPort(Protocol):
        properties_panel: SignaturePropertiesPanel
        def signature_appearance(...) -> SignatureAppearance | None
        def set_timestamp_required(...) -> None
        def apply_signature_rect_placement(...) -> None
        def refresh_viewer(...) -> None
        def current_request(...) -> SigningRequest | None
        def last_signing_result(...) -> SigningResult | None

    class Phase3HarnessWorkspacePort(Protocol):
        def apply_scenario(...) -> None
        def refresh_viewer(...) -> None
        def current_request(...) -> SigningRequest | None
        def last_signing_result(...) -> SigningResult | None
        def capture_state(...) -> dict[str, Any]

The production shell port must remain narrow. The new testing port is explicitly non-production and should be consumed only by harness/test boundaries.
