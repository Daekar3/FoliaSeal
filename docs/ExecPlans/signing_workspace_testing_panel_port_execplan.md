# Signing workspace assembly and testing-panel-port refactor

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this change, the live signing workspace will still return a concrete Qt widget and still expose an explicit `testing_adapter`, but the harness/testing seam will no longer depend on the concrete `SignaturePropertiesPanel`. Instead, the shell will expose a narrower typed panel port behind the testing adapter, and the workspace assembly path will make that seam explicit without widening the production app-frame port. The user-visible behavior must stay the same: app-frame callers still get the same `SigningWorkspacePort`, Phase 3 still drives live shells through `testing_adapter`, startup order stays stable, and signature-rectangle placement still preserves the non-notifying internal path.

The proof is focused behavior preservation. The app frame must still open a live shell the same way, the shell tests must still prove the widget/testing seam works, and the Phase 3 harness workspace tests must still pass while no longer reaching through the concrete `properties_panel`.

## Child ExecPlan Dependencies

- [x] No child ExecPlans are required. This slice is intentionally one pass across compatibility surface, composition wiring, Phase 3 consumer updates, tests, and architecture reconciliation.

## Progress

- [x] (2026-07-06 00:44Z) Re-ran the architecture exploration on the post-`143a4082b` tree and selected the hybrid seam: assembly boundary plus narrower testing panel port.
- [x] (2026-07-06 01:06Z) Gathered implementation-scope guidance from an explorer-light subagent for the exact file set, invariants, and sequencing.
- [x] (2026-07-06 01:11Z) Wrote this one-pass ExecPlan before implementation.
- [x] (2026-07-06 02:02Z) Added `SigningWorkspaceTestingPanelPort` and its concrete adapter in `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py`, then moved `SigningWorkspaceTestingPort` to expose `panel` instead of the concrete `properties_panel`.
- [x] (2026-07-06 02:02Z) Kept `src/foliaseal/presentation/qt/signing_workspace_composition.py` unchanged because the compatibility surface can build the panel adapter internally; widget return semantics and bootstrap order were preserved without additional composition wiring.
- [x] (2026-07-06 02:03Z) Updated `src/foliaseal/presentation/qt/phase3_harness_workspace.py` to consume only the typed testing seam for scenario mutation, preview refresh, preview-text reads, validation-text reads, and preview-render capture inputs.
- [x] (2026-07-06 02:05Z) Retargeted the focused shell and Phase 3 harness workspace tests to the new `testing_adapter.panel` seam.
- [x] (2026-07-06 02:11Z) Ran focused validation and reconciled `docs/ARCHITECTURE.md`.
- [x] (2026-07-06 02:24Z) Tightened the panel port again so preview-render capture no longer exposes preview-control internals directly, then added direct pass-through tests for `notify=False` and preview-render capture bridging.

## Surprises & Discoveries

- Observation: the current seam is already narrow on the production side. `SigningWorkspaceBundle.port` is stable; the remaining debt is specifically that `testing_adapter.properties_panel` exposes the concrete panel.
  Evidence: `src/foliaseal/presentation/qt/signing_shell_port.py`, `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py`.

- Observation: `phase3_harness_workspace.py` and its focused tests rely on only a small subset of panel behavior: setting appearance, setting signature rect, and reading preview/validation text through snapshots.
  Evidence: `src/foliaseal/presentation/qt/phase3_harness_workspace.py`, `tests/unit/test_qt_phase3_harness_workspace.py`.

- Observation: composition wiring did not need a structural change because the compatibility surface already receives the concrete `SignaturePropertiesPanel` and can build the narrower testing-panel adapter locally.
  Evidence: `src/foliaseal/presentation/qt/signing_workspace_composition.py`, `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py`.

## Decision Log

- Decision: keep `build_qt_signing_shell()` returning the concrete widget and keep `SigningWorkspaceBundle` unchanged at the production boundary.
  Rationale: the user asked for a one-pass refactor that leaves the repo ready for another architecture pass, not a broader caller migration. The app-frame seam is already in good shape.
  Date/Author: 2026-07-06 / Codex

- Decision: narrow the testing seam by introducing a typed panel port under `SigningWorkspaceTestingPort` instead of exposing the full `SignaturePropertiesPanel`.
  Rationale: this removes the most brittle concrete-panel reach-through while preserving the explicit testing adapter and the current harness entrypoint.
  Date/Author: 2026-07-06 / Codex

## Outcomes & Retrospective

The refactor completed in one pass without widening the production workspace seam. `build_qt_signing_shell()` still returns the concrete widget, `SigningWorkspaceBundle` still carries the same production `port` plus explicit testing adapter, and the app frame remains isolated from the testing seam. The compatibility surface now wraps the live `SignaturePropertiesPanel` behind `SigningWorkspaceTestingPanelPort`, while Phase 3 and its focused tests consume `testing_adapter.panel` instead of the concrete panel. A follow-up tightening pass removed the remaining preview-control leakage by moving preview-render capture behind a panel-port method rather than exposing preview-control internals on the port.

Focused validation passed cleanly:

- `.venv/bin/python -m ruff check src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py src/foliaseal/presentation/qt/phase3_harness_workspace.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_qt_signing_shell.py`
- `.venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py`

Final result after the tightening follow-up: `128 passed in 11.30s`.

## Context and Orientation

The selected seam lives in the Qt signing workspace.

`src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py` currently owns widget export installation and the explicit `SigningWorkspaceTestingAdapter`. That adapter still exposes `properties_panel` as the concrete `SignaturePropertiesPanel`, which lets harness code and tests reach into full panel anatomy.

`src/foliaseal/presentation/qt/signing_workspace_composition.py` builds the live shell graph and currently constructs the compatibility surface directly from the concrete panel and widget collaborators.

`src/foliaseal/presentation/qt/phase3_harness_workspace.py` is the live-shell scenario/capture boundary used by Phase 3. It already requires `testing_adapter`, which is good, but its callers and focused tests still assume the testing adapter exposes concrete panel behavior rather than a narrower panel-oriented contract.

`src/foliaseal/presentation/qt/signing_shell.py` and `src/foliaseal/presentation/qt/signing_shell_port.py` are not the primary refactor targets for this slice. The returned value of `build_qt_signing_shell()` must stay the concrete widget. The app frame must continue to consume only `SigningWorkspacePort` from `SigningWorkspaceBundle`.

This is a `local-substitutable` dependency cluster. The repo already has fake Qt widgets and fake testing adapters, so the correct testing move is to deepen the seam and replace brittle concrete-panel tests with boundary tests, not to add more generic indirection than necessary.

## Plan of Work

First, edit `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py`. Define a new typed panel port protocol with the exact behaviors the testing seam actually needs: setting signature appearance, setting signature rectangle with the existing `notify` flag, refreshing preview, reading preview/validation text, and bridging preview-render capture without exposing preview-control internals directly. Add a concrete adapter implementation around `SignaturePropertiesPanel`. Then update `SigningWorkspaceTestingAdapter` and `SigningWorkspaceTestingPort` so the testing adapter exposes this panel port instead of the full concrete panel object. Preserve the existing top-level testing methods such as `signature_appearance()`, `set_timestamp_required()`, `apply_signature_rect_placement(...)`, `refresh_viewer()`, `current_request()`, and `last_signing_result()`.

Second, verify whether `src/foliaseal/presentation/qt/signing_workspace_composition.py` needs explicit wiring changes. If the compatibility surface can construct the concrete testing panel adapter internally from the already-injected `SignaturePropertiesPanel`, leave composition unchanged so the refactor stays smaller and bootstrap order remains untouched.

Third, edit `src/foliaseal/presentation/qt/phase3_harness_workspace.py` so live-shell scenario application and snapshot capture depend only on the narrowed testing seam. Replace direct `properties_panel` assumptions with the typed panel port and keep the rest of the testing adapter contract unchanged.

Fourth, update `tests/unit/test_qt_phase3_harness_workspace.py` so the fake testing adapters model the new typed panel port instead of exposing an ad hoc concrete `properties_panel`. Update `tests/unit/test_qt_signing_shell.py` so the compatibility-surface smoke test asserts the new panel-port shape on `widget.testing_adapter`, and keep the rest of the shell behavior tests intact. Avoid broad rewrites of the many direct `widget.properties_panel` shell tests in this slice; they still validate the concrete widget behavior, not the testing seam.

Finally, reconcile `docs/ARCHITECTURE.md`. The repo map and long-form Qt architecture narrative must say that the testing seam exposes a typed panel port under `SigningWorkspaceTestingPort` rather than the full concrete properties panel. Leave `docs/SPEC.md` unchanged.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Implement the narrowed testing panel seam.

       rg -n "properties_panel|SigningWorkspaceTestingPort|testing_adapter" src/foliaseal/presentation/qt tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_qt_signing_shell.py

2. Run focused checks.

       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py src/foliaseal/presentation/qt/signing_workspace_composition.py src/foliaseal/presentation/qt/phase3_harness_workspace.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_phase3_harness_workspace.py docs/ARCHITECTURE.md

       .venv/bin/python -m pytest tests/unit/test_qt_signing_shell.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_qt_app_frame.py

3. If the focused tests expose runtime-side fallout, expand validation to include:

       .venv/bin/python -m pytest tests/unit/test_qt_signing_workspace_runtime.py tests/unit/test_qt_app_frame_workspace_open.py

## Validation and Acceptance

Acceptance requires all of the following.

The compatibility-surface smoke test proves the live widget still exposes `compat_surface`, still exposes `testing_adapter`, and that `testing_adapter` now exposes a typed panel port instead of the concrete panel object while preserving the current top-level testing methods.

The Phase 3 harness workspace tests prove that scenario application, request/result capture, preview text capture, validation text capture, and signature-rect placement still work through `testing_adapter` without direct dependence on the concrete `SignaturePropertiesPanel`.

The app-frame tests prove there was no accidental widening or breakage of the production `SigningWorkspaceBundle.port` seam.

The final focused validation should include:

       .venv/bin/python -m pytest tests/unit/test_qt_signing_shell.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_qt_app_frame.py

If runtime or app-frame-open fallout appears, add:

       .venv/bin/python -m pytest tests/unit/test_qt_signing_workspace_runtime.py tests/unit/test_qt_app_frame_workspace_open.py

## Idempotence and Recovery

This is a behavior-preserving internal refactor. If a partial edit breaks the harness seam, restore `widget.testing_adapter` first and then reintroduce the narrowed panel port behind it. Do not fall back to exposing raw shell internals or teaching Phase 3 to use `compat_surface` directly. If a partial edit breaks widget return semantics, restore `build_qt_signing_shell()` to returning the concrete widget before continuing.

## Artifacts and Notes

The most important artifact for this slice is the focused validation transcript showing shell, harness-workspace, and app-frame tests passing with the narrower testing seam.

- 2026-07-06: `.venv/bin/python -m ruff check ...` reported `All checks passed!`.
- 2026-07-06: `.venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py` reported `126 passed in 11.02s` on the first pass and `128 passed in 11.30s` after the seam-tightening follow-up added two direct adapter pass-through tests.

## Interfaces and Dependencies

At the end of this slice, `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py` must define a typed panel protocol and a testing seam that looks approximately like:

    class SigningWorkspaceTestingPanelPort(Protocol):
        def set_signature_appearance(self, appearance: SignatureAppearance) -> None: ...
        def set_signature_rect(
            self,
            signature_rect: SignatureRect,
            *,
            notify: bool = True,
        ) -> None: ...
        def refresh_preview(self) -> None: ...
        def preview_text(self) -> str: ...
        def validation_text(self) -> str: ...
        def capture_preview_render(...) -> dict[str, Any]: ...

    class SigningWorkspaceTestingPort(Protocol):
        @property
        def panel(self) -> SigningWorkspaceTestingPanelPort: ...
        def signature_appearance(self) -> SignatureAppearance | None: ...
        def set_timestamp_required(self, required: bool) -> None: ...
        def apply_signature_rect_placement(self, signature_rect: SignatureRect) -> None: ...
        def refresh_viewer(self) -> None: ...
        def current_request(self) -> SigningRequest | None: ...
        def last_signing_result(self) -> SigningResult | None: ...

The exact protocol names may vary slightly, but the key outcome is fixed: the testing adapter must expose a typed panel-oriented seam instead of the concrete `SignaturePropertiesPanel`, while preserving the existing top-level testing operations, keeping preview-render capture behind the port instead of leaking preview controls directly, and keeping the current concrete-widget return path.

Revision note: Created on 2026-07-06 by Codex for the one-pass signing-workspace assembly plus testing-panel-port hybrid refactor selected through `$improve-codebase-architecture`.
