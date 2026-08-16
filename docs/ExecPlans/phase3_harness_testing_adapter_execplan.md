# Introduce a dedicated Phase 3 harness testing adapter on the signing workspace seam

> **Archived completed plan (2026-08-16).** Retained for provenance; current
> work belongs to the durable acceptance/evidence owners. Do not execute as an
> active implementation queue.

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the Phase 3 harness still drives the live Qt signing shell, applies preview and signed-acceptance scenarios, and captures the same preview and request evidence as before. The visible harness outputs do not change.

The architectural win is that `src/foliaseal/presentation/qt/phase3_harness_workspace.py` now depends on a narrow `testing_adapter` surface for its main live-shell operations instead of reaching directly into the broad `compat_surface` widget export. The signing workspace exposes that adapter for harness and test consumers, and it owns the small set of live-shell behaviors the Phase 3 harness actually needs: apply a scenario, refresh the viewer, read the current request, read the last signing result, and capture the current preview state. The current proof is unchanged harness behavior plus focused tests, with `compat_surface` and the shell itself remaining compatibility fallbacks for older fakes.

## Child ExecPlan Dependencies

- [x] (2026-06-28 17:14Z) `docs/ExecPlans/phase3_harness_workspace_scenario_boundary_execplan.md` is complete; the workspace boundary already owns shared scenario mutation for live and headless harness paths.
- [x] (2026-06-28 17:14Z) `docs/ExecPlans/phase3_harness_workspace_capture_boundary_execplan.md` is complete; the workspace boundary already owns request, result, and capture reads.
- [x] (2026-06-28 17:14Z) `docs/ExecPlans/phase3_harness_workspace_refresh_boundary_execplan.md` is complete; the workspace boundary already owns viewer priming refresh.
- [x] (2026-06-28 17:14Z) No child ExecPlans are required for this narrow harness-only migration slice.

## Progress

- [x] (2026-06-28 17:14Z) Re-read the current hybrid recommendation, the current harness workspace adapter implementation, the workspace composition/bootstrap files, and the architecture debt notes for the Phase 3 harness and signing shell seams.
- [x] (2026-06-28 17:16Z) Ran the required `explorer-light` dev-loop audit and fixed the slice boundary: migrate the Phase 3 harness to a dedicated live-shell testing adapter; explicitly defer app-frame migration.
- [x] (2026-06-28 17:19Z) Wrote this ExecPlan and fixed the implementation scope at one harness-only adapter slice.
- [x] (2026-06-29 00:06Z) Added `SigningWorkspaceTestingAdapter`, installed it on the live shell as `widget.testing_adapter`, and rewired the Phase 3 harness workspace boundary to prefer that adapter before `compat_surface` and shell fallbacks.
- [x] (2026-06-29 00:06Z) Added focused tests proving the new adapter path is preferred, the compatibility fallback remains safe, and the shell exports `testing_adapter`.
- [x] (2026-06-29 00:15Z) Ran focused validation with `.venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_harness.py`, `.venv/bin/python -m ruff check src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py src/foliaseal/presentation/qt/phase3_harness_workspace.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_harness.py`, and `git diff --check`; all passed.
- [x] (2026-06-29 00:15Z) Ran the required architectural compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this ExecPlan; the only gap was stale architecture documentation, which is now reconciled.
- [x] (2026-06-29 00:15Z) Reconciled `docs/ARCHITECTURE.md` and this ExecPlan to the implemented seam.
- [x] (2026-08-16) Historical publication marker closed; implementation commit `3cc7e559b` is recorded above and this plan is archival.

## Surprises & Discoveries

- Observation: the production shell already has a reasonably narrow caller-facing port, so the broad harness dependency is now mostly localized to the testing side.
  Evidence: `src/foliaseal/presentation/qt/signing_shell_port.py` exposes only `widget()`, `choose_output_pdf_path()`, `apply_app_settings(...)`, and `refresh_certificate_configurations()`, while `src/foliaseal/presentation/qt/phase3_harness_workspace.py` now prefers `testing_adapter` and keeps `compat_surface` only as a fallback.

- Observation: the existing workspace boundary already centralizes the harness verbs, so the useful move was changing what backs that boundary rather than moving more harness logic again.
  Evidence: `QtPhase3HarnessWorkspaceAdapter` in `src/foliaseal/presentation/qt/phase3_harness_workspace.py` owns `apply_scenario(...)`, `refresh_viewer()`, `current_request()`, `last_signing_result()`, and `capture_state(...)`; it now resolves the new testing adapter before falling back to shell compatibility helpers.

- Observation: `signing_workspace_composition.py` did not need a new branch or object-graph split for this slice.
  Evidence: the adapter could be installed entirely inside `SigningWorkspaceCompatibilitySurface.install_widget_exports()`, which kept the production shell port unchanged while still exposing `widget.testing_adapter`.

## Decision Log

- Decision: keep this dev-loop slice Phase 3 harness only and do not bundle the app-frame `window.current_*` cleanup.
  Rationale: the `explorer-light` audit found that the highest-value next move is replacing live-shell harness reach-through first. Mixing in app-frame cleanup would enlarge the blast radius without reducing the Phase 3 debt called out in `docs/ARCHITECTURE.md`.
  Date/Author: 2026-06-28 / Codex

- Decision: add a dedicated testing adapter on the signing workspace seam instead of replacing the production port with a generic command bus.
  Rationale: the production port is already narrow enough for the app frame. The missing seam is specifically for harness/test consumers, so the new boundary should target them directly.
  Date/Author: 2026-06-28 / Codex

- Decision: keep the compatibility fallback in place for now, with the harness preferring `testing_adapter`, then `compat_surface`, then the shell itself.
  Rationale: older fake shells and direct shell proxies still need to pass through the harness boundary during migration, but the new adapter should be the default path.
  Date/Author: 2026-06-28 / Codex

## Outcomes & Retrospective

This slice is implemented in code and the docs now match the landed seam. The live signing workspace exposes `testing_adapter`, `phase3_harness_workspace.py` prefers it by default, and `compat_surface` plus the shell itself remain transitional fallbacks for older fakes. No app-frame/window migration is included here.

## Context and Orientation

The live signing workspace is assembled in `src/foliaseal/presentation/qt/signing_workspace_composition.py`. That composition now installs the narrow production shell surface, the historical compatibility surface, and a dedicated testing adapter onto the concrete shell widget. `src/foliaseal/presentation/qt/signing_workspace_shell_surface.py` owns the narrow production verbs used by the app frame and shell port. `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py` owns the broader export block: widget anatomy, viewer and panel helpers, document-text helpers, signature-rect helpers, and several harness/testing behaviors, plus the new testing adapter wrapper.

The Phase 3 harness does not talk to the whole shell directly anymore. `src/foliaseal/presentation/qt/phase3_harness_workspace.py` provides a narrow harness workspace boundary with live and headless adapters. The headless adapter talks to `SigningDraftWorkflow` directly. The live Qt adapter now resolves the dedicated `testing_adapter` first and only falls back to `compat_surface` or the shell itself when a test double has not been migrated yet.

In this repository, a “testing adapter” means a small explicit interface for tests and harnesses that is separate from the production caller-facing port. The production port stays optimized for app behavior such as mounting the widget, Save As, settings propagation, and certificate refresh. The testing adapter exposes only the extra behaviors needed to drive and inspect the workspace in automated harnesses. This separation is now landed without changing user-visible Qt behavior.

The key files are:

- `src/foliaseal/presentation/qt/signing_workspace_composition.py`, which builds and installs the shell surfaces.
- `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py`, which owns the broad harness/testing export block and the dedicated testing adapter wrapper.
- `src/foliaseal/presentation/qt/phase3_harness_workspace.py`, which is the harness-side boundary that now prefers the dedicated testing adapter.
- `tests/unit/test_qt_phase3_harness_workspace.py`, which proves the harness boundary now prefers the new testing adapter.
- `tests/unit/test_qt_signing_shell.py`, which covers shell surface installation and the adapter export.

This slice must remain behavior-preserving. It must not absorb app-frame cleanup, shell-port redesign, preview-render payload redesign, or broader widget-export deletion.

## Plan of Work

First, the signing workspace seam exposes a dedicated testing adapter in `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py`. The adapter owns only the harness behaviors already centralized in `QtPhase3HarnessWorkspaceAdapter`: scenario application, viewer refresh, current request, last signing result, and capture-state support. It reuses existing compatibility-surface internals so behavior does not change, but the result is now one dedicated adapter object instead of dozens of widget exports.

Second, the adapter is installed onto the concrete shell widget as `testing_adapter` by `SigningWorkspaceCompatibilitySurface.install_widget_exports()`, while the narrow production shell surface remains unchanged.

Third, `src/foliaseal/presentation/qt/phase3_harness_workspace.py` resolves the dedicated testing adapter first, then falls back to `compat_surface`, then to the shell itself. That keeps older fake shells working while avoiding duplicate side effects such as `apply_signature_rect_placement(...)`, preview refresh, or event pumping.

Fourth, the focused tests now cover the preferred adapter path and the shell export wiring. `tests/unit/test_qt_phase3_harness_workspace.py` proves the harness boundary prefers the new testing adapter, and `tests/unit/test_qt_signing_shell.py` proves the shell exposes it after composition.

Finally, the architecture doc and this ExecPlan are reconciled to the implemented seam. Validation and compliance-review commands remain the same reference points if this slice needs to be re-opened, but the current code path is already on the dedicated adapter.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Add the dedicated testing adapter to the signing workspace seam and wire it through shell composition.

       apply_patch ... on src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py

2. Rewire the Phase 3 harness workspace boundary to prefer the new adapter and keep a safe fallback.

       apply_patch ... on src/foliaseal/presentation/qt/phase3_harness_workspace.py

3. Add focused tests for the preferred adapter path and shell export wiring.

       apply_patch ... on tests/unit/test_qt_phase3_harness_workspace.py
       apply_patch ... on tests/unit/test_qt_signing_shell.py

4. Run focused validation.

       .venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_harness.py
       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py src/foliaseal/presentation/qt/phase3_harness_workspace.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_harness.py
       git diff --check

5. Reconcile `docs/ARCHITECTURE.md`, rerun validation if necessary, run the compliance review, and create the git commit.

## Validation and Acceptance

This slice is accepted when all of the following are true:

- the live Phase 3 harness still applies scenarios, refreshes the viewer, reads the current request, reads the last signing result, and captures preview state exactly as before;
- `QtPhase3HarnessWorkspaceAdapter` prefers the dedicated testing adapter and only falls back to `compat_surface` or the shell itself for compatibility;
- the shell exposes that dedicated testing adapter after composition;
- older tests or fake shells that do not yet expose the adapter still work through the compatibility fallback;
- no app-frame migration, shell-port redesign, or broad compatibility-export deletion is mixed into this slice.

Run:

    .venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_harness.py

Then run:

    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py src/foliaseal/presentation/qt/phase3_harness_workspace.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_harness.py
    git diff --check

Acceptance is behavioral. The same Phase 3 scenarios must still run, but the harness-side dependency now terminates at a dedicated testing adapter rather than the broad compatibility surface.

## Idempotence and Recovery

This is a behavior-preserving extraction inside local Qt harness code. If the dedicated testing adapter is missing a side effect, add that behavior inside the adapter implementation rather than re-expanding `phase3_harness_workspace.py` into shell anatomy again.

If a test fails because a fake shell does not provide the new adapter, preserve the compatibility fallback in the harness boundary and update only the necessary focused tests. Do not pull app-frame or unrelated shell cleanup into this slice as a workaround.

## Artifacts and Notes

The most important final evidence for this slice will be:

- a dedicated testing adapter exposed by the live signing workspace;
- a narrower `src/foliaseal/presentation/qt/phase3_harness_workspace.py` that prefers that adapter;
- focused tests proving the preferred path and compatibility fallback;
- focused validation output showing the harness and shell tests still pass.

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

At the end of this slice, the production port should remain narrow and unchanged in shape:

    class SigningWorkspacePort(Protocol):
        def widget(self) -> Any: ...
        def choose_output_pdf_path(self) -> str | None: ...
        def apply_app_settings(self, settings: AppSettings) -> None: ...
        def refresh_certificate_configurations(self) -> CertificateCatalog: ...

The new testing adapter should be explicit and small. Its final names may vary, but it should end up equivalent to:

    class SigningWorkspaceTestingAdapter(Protocol):
        def signature_appearance(self) -> SignatureAppearance | None: ...
        def apply_signature_appearance(self, appearance: SignatureAppearance) -> None: ...
        def set_timestamp_required(self, required: bool) -> None: ...
        def apply_signature_rect_placement(self, signature_rect: SignatureRect) -> None: ...
        def refresh_viewer(self) -> None: ...
        def current_request(self) -> SigningRequest | None: ...
        def last_signing_result(self) -> SigningResult | None: ...
        def capture_preview_state(...) -> dict[str, Any]: ...
        @property
        def properties_panel(self) -> SignaturePropertiesPanel: ...

`phase3_harness_workspace.py` may keep a temporary fallback helper that resolves, in order, the dedicated testing adapter, `compat_surface`, or the shell itself. That fallback is transitional and should be documented as such. This slice does not widen the production shell port just to satisfy harness callers.

Revision note: Updated on 2026-06-28 by Codex to reflect the landed Phase 3 harness testing-adapter slice. The harness now prefers `testing_adapter` first, with `compat_surface` and the shell itself retained only as compatibility fallbacks.
Revision note: Updated on 2026-06-29 by Codex to correct the implementation record: the adapter is installed through `signing_workspace_compatibility_surface.py`, not a separate change to `signing_workspace_composition.py`, and the focused validation/compliance evidence is now recorded.
