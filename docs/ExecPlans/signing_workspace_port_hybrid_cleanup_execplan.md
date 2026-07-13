# Signing workspace port hybrid cleanup

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this change, the live signing workspace will still behave exactly the same for users: opening a PDF still installs the signing shell, Save As still goes through the frame-owned flow, and the Phase 3 harness still reaches the live shell through `testing_adapter`.

The architectural gain is narrower and deeper. The production-facing `SigningWorkspacePort` will remain tiny, but the non-production `SigningWorkspaceTestingPort` will become a neutral sibling contract instead of leaking out of `signing_workspace_compatibility_surface.py`. That makes the production port layer stop importing testing types from an implementation module, keeps the app-frame path clean, and leaves the codebase ready for another `$improve-codebase-architecture` pass on the remaining shell surface instead of on this same dependency-direction seam.

## Child ExecPlan Dependencies

- [x] (2026-07-08 00:54Z) No child ExecPlans are required. This slice is intentionally one pass across contract extraction, test reconciliation, documentation, compliance review, and commit flow.

## Progress

- [x] (2026-07-08 00:54Z) Re-read the chosen hybrid design, the live shell port, compatibility surface, app-frame workspace-open boundary, Phase 3 harness workspace adapter, and the prior signing-workspace ExecPlans.
- [x] (2026-07-08 00:54Z) Completed the required dev-loop explorer pass for the implementation slice and captured exact files, invariants, likely test fallout, and a one-pass implementation order.
- [x] (2026-07-08 00:54Z) Wrote this ExecPlan before implementation.
- [x] (2026-07-08 01:08Z) Extracted `SigningWorkspaceTestingPanelPort` and `SigningWorkspaceTestingPort` into the new neutral contract module `src/foliaseal/presentation/qt/signing_workspace_testing_port.py`, and removed the production port dependency on `signing_workspace_compatibility_surface.py`.
- [x] (2026-07-08 01:08Z) Retargeted the compatibility surface and Phase 3 harness workspace boundary to the neutral testing-port contract without changing live behavior.
- [x] (2026-07-08 01:08Z) Reconciled `docs/ARCHITECTURE.md` with the neutral testing-port ownership and confirmed the focused shell/app-frame/harness suites still pass without test-file edits.
- [x] (2026-07-08 01:13Z) Completed the required explorer-light compliance review. No doc/spec mismatch was found for this seam; the remaining localized cruft is in `phase3_harness_workspace.py`, which is now the next candidate seam for another architecture-improvement pass. A commit step was not performed in this turn.

## Surprises & Discoveries

- Observation: the recommended hybrid is already mostly implemented in behavior; the real remaining problem is dependency direction, not missing functionality.
  Evidence: the explorer found that `app_frame_workspace_open.py` and `app_frame.py` already stay on the narrow production port path, while `signing_shell_port.py` is the only production-facing module that imports `SigningWorkspaceTestingPort` from `signing_workspace_compatibility_surface.py`.

- Observation: this slice should not require changes to `signing_shell.py`, `signing_workspace_composition.py`, or `signing_workspace_shell_surface.py` unless a validation failure proves otherwise.
  Evidence: the explorer found no required functional change there for the dependency-direction fix; the live split is already aligned with the intended hybrid.

- Observation: after the dependency-direction cleanup, the next remaining local cruft is inside `phase3_harness_workspace.py`, not in the production port/factory seam.
  Evidence: the compliance-review explorer found no code/doc mismatch in the hybrid seam and identified only the harness-side callable/attribute compatibility reads plus preview-capture/event-pumping reach-through as remaining localized debt.

## Decision Log

- Decision: implement the hybrid as a neutral testing-port extraction rather than a public port redesign.
  Rationale: the public production port is already appropriately narrow; widening it would reopen the design debate instead of completing the chosen seam cleanup.
  Date/Author: 2026-07-08 / Codex

- Decision: prefer a new neutral contract module over `TYPE_CHECKING` tricks or forward references.
  Rationale: hiding the import would suppress the symptom but would not improve ownership or navigability. A neutral module makes the production/test split explicit and durable.
  Date/Author: 2026-07-08 / Codex

## Outcomes & Retrospective

The implementation stayed on the intended seam. The only runtime-facing code change was contract ownership: `signing_shell_port.py` and `phase3_harness_workspace.py` now depend on `signing_workspace_testing_port.py`, while `signing_workspace_compatibility_surface.py` keeps the concrete `testing_adapter` behavior and widget-export duties.

Focused validation passed without broad fallout:

- `131 passed` across `tests/unit/test_qt_signing_shell.py`, `tests/unit/test_qt_phase3_harness_workspace.py`, `tests/unit/test_qt_app_frame_workspace_open.py`, and `tests/unit/test_qt_app_frame.py`
- `ruff check` passed for the touched Qt seam files and focused tests
- `git diff --check` passed

The compliance review completed without further code changes. `docs/ARCHITECTURE.md` and the touched code agree on the new ownership model, and `docs/SPEC.md` does not conflict with this seam. The next architecture-improvement target should move deeper into `phase3_harness_workspace.py` rather than revisiting this production/testing port split.

## Context and Orientation

The current seam lives in the Qt presentation layer under `src/foliaseal/presentation/qt/`.

`src/foliaseal/presentation/qt/signing_shell_port.py` defines the typed bootstrap inputs for a live signing workspace, the tiny production `SigningWorkspacePort`, the `SigningWorkspaceFactory` protocol, and the `SigningWorkspaceBundle` returned by `QtSigningWorkspaceFactory`. After this refactor it imports `SigningWorkspaceTestingPort` from `src/foliaseal/presentation/qt/signing_workspace_testing_port.py`, which removes the old layering leak where the production contract depended on a testing protocol owned by an implementation module.

`src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py` owns the broad compatibility/test seam. It installs `widget.compat_surface`, `widget.testing_adapter`, and many direct widget exports. It now implements the testing adapters against the neutral protocols defined in `src/foliaseal/presentation/qt/signing_workspace_testing_port.py`, which keeps behavior local without owning the production import boundary.

`src/foliaseal/presentation/qt/phase3_harness_workspace.py` consumes `SigningWorkspaceTestingPort` so the live Phase 3 harness path can mutate appearance, placement, preview, and current-request state through `testing_adapter`. That dependency remains explicit and now targets the neutral contract module rather than the compatibility implementation module.

`src/foliaseal/presentation/qt/app_frame_workspace_open.py` and `src/foliaseal/presentation/qt/app_frame.py` already consume only the narrow production port. They should remain untouched unless test failures show that the contract extraction accidentally widened or tightened runtime behavior.

The focused tests that lock in this seam are:

- `tests/unit/test_qt_signing_shell.py`
- `tests/unit/test_qt_phase3_harness_workspace.py`
- `tests/unit/test_qt_app_frame_workspace_open.py`
- possibly `tests/unit/test_qt_app_frame.py` if the bundle typing changes leak further than expected

The product spec in `docs/SPEC.md` does not require a public change here. This slice is accepted only if behavior stays stable while dependency ownership gets cleaner.

## Plan of Work

First, add a new neutral contract module at `src/foliaseal/presentation/qt/signing_workspace_testing_port.py`. Move only the protocols there: `SigningWorkspaceTestingPanelPort` and `SigningWorkspaceTestingPort`. Keep the names stable. Do not move the concrete adapter implementations into this file; keep behavior in `signing_workspace_compatibility_surface.py`.

Second, update `src/foliaseal/presentation/qt/signing_shell_port.py` so it imports `SigningWorkspaceTestingPort` from the new neutral module. Keep `SigningWorkspacePort`, `SigningWorkspaceFactory`, `SigningWorkspaceBundle`, and `QtSigningWorkspaceFactory` behavior unchanged. The bundle must still return both `port` and `testing_adapter`, and runtime validation must still require `widget.testing_adapter`.

Third, update `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py` to import the protocols from the new neutral module and leave only the concrete adapter implementations plus widget-export behavior in place. The compatibility surface should still own `SigningWorkspaceTestingAdapter` and `SigningWorkspaceTestingPanelAdapter`, and `widget.testing_adapter` must still be distinct from `compat_surface`.

Fourth, update `src/foliaseal/presentation/qt/phase3_harness_workspace.py` to import `SigningWorkspaceTestingPort` from the neutral module. Preserve the existing `_testing_surface(...)` semantics and any compatibility fallback behavior unless focused tests prove it is dead and removable. This slice is about contract ownership, not about deleting fallback behavior opportunistically.

Fifth, update focused tests. `tests/unit/test_qt_signing_shell.py` should continue to prove that the shell exports a distinct `testing_adapter` with the same methods. `tests/unit/test_qt_phase3_harness_workspace.py` should continue to prove the live harness path prefers `testing_adapter`. `tests/unit/test_qt_app_frame_workspace_open.py` should keep proving the workspace-open boundary stays on the production port path and that the bundle contract still carries the testing adapter without leaking it into app-frame behavior.

Sixth, update `docs/ARCHITECTURE.md` so it says the testing-port contract lives in a neutral module and is implemented by `signing_workspace_compatibility_surface.py`. If necessary, update this ExecPlan’s living sections after the implementation lands and after the compliance review completes.

Finally, run focused validation, perform the required explorer-light compliance review against `docs/ARCHITECTURE.md` and `docs/SPEC.md`, fix any mismatch, and only then move to the commit step.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Add the neutral testing-port contract module and retarget imports.

       apply_patch ... on src/foliaseal/presentation/qt/signing_workspace_testing_port.py
       apply_patch ... on src/foliaseal/presentation/qt/signing_shell_port.py
       apply_patch ... on src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py
       apply_patch ... on src/foliaseal/presentation/qt/phase3_harness_workspace.py

2. Update focused tests and architecture docs.

       apply_patch ... on tests/unit/test_qt_signing_shell.py
       apply_patch ... on tests/unit/test_qt_phase3_harness_workspace.py
       apply_patch ... on tests/unit/test_qt_app_frame_workspace_open.py
       apply_patch ... on docs/ARCHITECTURE.md
       apply_patch ... on docs/ExecPlans/signing_workspace_port_hybrid_cleanup_execplan.md

3. Run focused validation and whitespace checks.

       .venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_qt_app_frame_workspace_open.py tests/unit/test_qt_app_frame.py
       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/signing_workspace_testing_port.py src/foliaseal/presentation/qt/signing_shell_port.py src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py src/foliaseal/presentation/qt/phase3_harness_workspace.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_qt_app_frame_workspace_open.py tests/unit/test_qt_app_frame.py docs/ARCHITECTURE.md
       git diff --check

4. Perform the required compliance review and fix any doc/spec mismatch before committing.

## Validation and Acceptance

This slice is accepted only when all of the following are true.

The production-facing `SigningWorkspacePort` is still tiny and unchanged in behavior. `FoliaSealAppFrame` and the workspace-open boundary still consume only that port for central-widget installation, Save As, live app-settings propagation, and certificate refresh.

The non-production seam is still explicit and behaviorally unchanged. `SigningWorkspaceBundle` still exposes `testing_adapter`, the shell still installs `widget.testing_adapter`, and the Phase 3 harness still consumes the testing seam instead of broad widget anatomy.

The production contract no longer imports the testing protocol from `signing_workspace_compatibility_surface.py`. Instead, both the production bundle and the compatibility surface depend on a neutral testing-port contract module.

Run:

    .venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_qt_app_frame_workspace_open.py tests/unit/test_qt_app_frame.py

Then run:

    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/signing_workspace_testing_port.py src/foliaseal/presentation/qt/signing_shell_port.py src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py src/foliaseal/presentation/qt/phase3_harness_workspace.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_qt_app_frame_workspace_open.py tests/unit/test_qt_app_frame.py docs/ARCHITECTURE.md
    git diff --check

Acceptance is behavioral. No visible review/search/selection/signing flow should change. The only intended observable difference is that the codebase becomes easier to navigate because the production/test split is explicit in the contract ownership.

## Idempotence and Recovery

This is a behavior-preserving refactor. It is safe to retry. If a partial edit breaks the build because imports move, restore the neutral testing-port module and update imports first before touching tests. If the testing seam temporarily disappears, repair `widget.testing_adapter` installation rather than widening the production port or teaching callers to reach through `compat_surface`.

## Artifacts and Notes

The important proof for this slice will be:

- `src/foliaseal/presentation/qt/signing_workspace_testing_port.py` defining the neutral testing-port contracts
- `src/foliaseal/presentation/qt/signing_shell_port.py` importing those contracts instead of the compatibility implementation module
- focused tests proving that the shell exports, app-frame behavior, and Phase 3 harness seam still behave the same
- `docs/ARCHITECTURE.md` describing the new ownership accurately

## Interfaces and Dependencies

At the end of this slice, `src/foliaseal/presentation/qt/signing_workspace_testing_port.py` must define:

    class SigningWorkspaceTestingPanelPort(Protocol):
        def set_signature_appearance(self, appearance: SignatureAppearance) -> None: ...
        def set_signature_rect(self, signature_rect: SignatureRect, *, notify: bool = True) -> None: ...
        def refresh_preview(self) -> Any: ...
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

`src/foliaseal/presentation/qt/signing_shell_port.py` must continue to define:

    class SigningWorkspacePort(Protocol):
        def widget(self) -> Any: ...
        def choose_output_pdf_path(self) -> str | None: ...
        def apply_app_settings(self, settings: AppSettings) -> None: ...
        def refresh_certificate_configurations(self) -> CertificateCatalog: ...

    @dataclass(frozen=True)
    class SigningWorkspaceBundle:
        port: SigningWorkspacePort
        testing_adapter: SigningWorkspaceTestingPort

This slice uses the `In-process` dependency category. The goal is not to add new external seams, only to make ownership and import direction match the actual architectural split.
