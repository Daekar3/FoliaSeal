# Introduce Signing Action Boundary

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the signing-action portion of the Qt signing workspace will no longer be orchestrated directly by shell methods. A new `SigningActionBoundary` will sit between `SigningWorkspaceWidget` and `SigningActionCoordinator`, so the shell becomes a thinner adapter that gathers Qt input, asks the boundary to act, and renders the returned `SigningActionState` through the sidebar.

The user-visible behavior must stay the same. A user must still be able to choose an output PDF path, confirm and sign a PDF, and reopen the signed output through the same buttons and menu flows. The proof is that the focused signing-action tests keep passing while the new boundary gains its own direct tests.

## Child ExecPlan Dependencies

- [x] (2026-06-01 00:00Z) No child ExecPlans are required for this narrow refactor slice.

## Progress

- [x] (2026-06-01 00:00Z) Dev-loop explorer identified the first hybrid `3+4` slice: add a narrow signing-action boundary, keep the sidebar as the renderer, and do not widen into review/text or app-frame lifecycle work.
- [x] (2026-06-01 00:00Z) Wrote this ExecPlan before implementation.
- [x] (2026-06-01 00:12Z) Added `src/foliaseal/presentation/qt/signing_action_boundary.py` with `SigningActionBoundary` and `SigningActionBoundaryResult`.
- [x] (2026-06-01 00:15Z) Rewired `src/foliaseal/presentation/qt/signing_shell.py` so choose/sign/open, load, and invalidation now delegate through the new boundary; kept `SigningWorkspaceSidebar` as the renderer.
- [x] (2026-06-01 00:18Z) Added direct coverage in `tests/unit/test_qt_signing_action_boundary.py` for output-path acceptance, sign success, error routing, open-signed-output callback flow, and invalidation/reset behavior.
- [x] (2026-06-01 00:21Z) Completed focused validation: `pytest tests/unit/test_qt_signing_action_boundary.py tests/unit/test_qt_signing_action_coordinator.py tests/unit/test_qt_signing_shell.py`, `ruff check ...`, and `git diff --check` all passed.
- [x] (2026-06-01 00:35Z) Completed the required architecture/spec compliance review and reconciled the docs; confirmed the boundary needed to be documented explicitly between the shell and coordinator.
- [x] (2026-06-01 00:35Z) Added the missing guarded-disabled `open_signed_output` boundary test so the disabled reopen path is covered directly at the boundary.

## Surprises & Discoveries

- Observation: the shell needed to route signing-action invalidation and reload paths through the boundary too, not just the three direct user actions.
  Evidence: `SigningWorkspaceWidget` still refreshed or invalidated signing-action state from `_clear_previous_signing_result()`, `_refresh_sign_button_state()`, `_refresh_flow_summary()`, and `_apply_workspace_interaction_transition(...)`. Leaving those paths on the coordinator would have split ownership immediately again.

- Observation: the sidebar already had the correct rendering seam; it only needed a naming-level clarification.
  Evidence: adding `render_signing_action_state()` as the explicit renderer kept the width-fallback behavior and all existing shell assertions green while making the role match the chosen hybrid design.

## Decision Log

- Decision: keep the new boundary in `src/foliaseal/presentation/qt/` rather than moving it into `src/foliaseal/application/`.
  Rationale: this first slice still depends on Qt-owned dialog decisions and shell callback behavior. The goal is to deepen the presentation seam without forcing a broader package migration.
  Date/Author: 2026-06-01 / Codex

- Decision: preserve the current public shell handle shape for now.
  Rationale: the hybrid recommendation was explicit about using a deeper internal boundary while keeping common-caller ergonomics stable. `choose_output_pdf_path()`, `submit_sign_request()`, `open_signed_output()`, and `refresh_certificate_configurations()` must remain available on the shell surface during this slice.
  Date/Author: 2026-06-01 / Codex

## Outcomes & Retrospective

Implementation is functionally complete for the first pass. The required compliance review ran and the remaining work was limited to documentation reconciliation.

## Context and Orientation

The current production signing workspace lives in `src/foliaseal/presentation/qt/signing_shell.py`. `SigningWorkspaceWidget` builds the viewer, the properties panel, and `SigningWorkspaceSidebar`. The sidebar in `src/foliaseal/presentation/qt/signing_workspace_sidebar.py` already owns the concrete widget mutation for the `Sign PDF` card by applying `SigningActionState` to labels and buttons. The coordinator in `src/foliaseal/presentation/qt/signing_action_coordinator.py` already owns the signing state machine: it decides when signing is ready, how success and failure are represented, when reopen is enabled, and how stage/detail text is derived.

The remaining friction is that `SigningWorkspaceWidget` still bridges everything itself. In `choose_output_pdf_path()` it shows the save dialog, confirms overwrite, forwards the chosen path into the coordinator, and immediately renders the resulting state. In `submit_sign_request()` it submits through the coordinator, renders the returned state, and then emits status or error callbacks. In `open_signed_output()` it asks the coordinator for the saved output path and then forwards that path to the shell callback. This means one concept, “drive the signing action flow,” still requires understanding shell methods plus the coordinator plus the sidebar renderer.

This slice introduces one more layer: a `SigningActionBoundary` that becomes the shell-facing action port. The coordinator remains the internal state engine, and the sidebar remains the renderer. The shell should become a thinner adapter that handles only Qt-specific input and callback edges.

Relevant files for this slice are:

- `src/foliaseal/presentation/qt/signing_action_coordinator.py`
- `src/foliaseal/presentation/qt/signing_action_boundary.py` (new)
- `src/foliaseal/presentation/qt/signing_workspace_sidebar.py`
- `src/foliaseal/presentation/qt/signing_shell.py`
- `tests/unit/test_qt_signing_action_coordinator.py`
- `tests/unit/test_qt_signing_shell.py`
- `docs/ARCHITECTURE.md`

The slice must not widen into:

- document review or document text behavior
- app-frame lifecycle or menu behavior
- viewer interaction routing
- certificate-lifecycle refactors outside the existing `refresh_certificate_configurations()` shell entry point

The intended primary change class is behavior-preserving architecture refactor. Documentation/status updates are allowed only insofar as they record the new boundary accurately. No unrelated evidence refresh belongs in this slice.

## Plan of Work

First, add `src/foliaseal/presentation/qt/signing_action_boundary.py`. That module should define the narrow shell-facing boundary for the signing-action flow. It must expose stable, explicit operations for the three user actions in this slice: accepting a chosen output path, submitting the sign request, and opening the most recent successful output. It may also expose a load or invalidate operation if that makes the shell wiring clearer, but it must not become a general workspace command bus. The boundary should own the orchestration that currently lives in shell methods, while delegating the actual state machine to `SigningActionCoordinator`.

Second, rewire `src/foliaseal/presentation/qt/signing_shell.py`. `SigningWorkspaceWidget` should instantiate the new boundary next to the coordinator. `submit_sign_request()`, `open_signed_output()`, and `choose_output_pdf_path()` should become thin adapters that gather Qt-specific input and then delegate into the boundary. `_apply_signing_action_state()` should continue to exist only if it is still the narrow shell-to-renderer bridge; if possible, align the naming with a sidebar render method such as `render_signing_action_state()` and keep the shell from owning any signing-action policy.

Third, update `src/foliaseal/presentation/qt/signing_workspace_sidebar.py` only as needed to make its renderer role explicit. It already applies `SigningActionState`; this slice should preserve that responsibility and avoid moving policy back into widgets. Any naming change must remain compatible with the fake Qt test surfaces and must preserve the width fallback for the detail label.

Fourth, add direct tests for the new boundary in `tests/unit/test_qt_signing_action_boundary.py`. Those tests must exercise output-path acceptance, sign success, sign failure, open-signed-output enablement, and invalidation/reset behavior through the new boundary rather than through the shell. `tests/unit/test_qt_signing_action_coordinator.py` remains the state-machine guardrail, and `tests/unit/test_qt_signing_shell.py` should keep only the thin smoke coverage needed to prove delegation and callback wiring.

Finally, update `docs/ARCHITECTURE.md` so the signing-action section states clearly that the shell now delegates the user-facing signing actions through `SigningActionBoundary`, the coordinator remains the state machine, and the sidebar remains the Qt renderer for `SigningActionState`.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Edit these files:

    src/foliaseal/presentation/qt/signing_action_boundary.py
    src/foliaseal/presentation/qt/signing_shell.py
    src/foliaseal/presentation/qt/signing_workspace_sidebar.py
    tests/unit/test_qt_signing_action_boundary.py
    tests/unit/test_qt_signing_shell.py
    docs/ARCHITECTURE.md
    docs/ExecPlans/signing_action_boundary_execplan.md

Run focused validation as the slice progresses:

    pytest tests/unit/test_qt_signing_action_boundary.py tests/unit/test_qt_signing_action_coordinator.py tests/unit/test_qt_signing_shell.py
    ruff check src/foliaseal/presentation/qt/signing_action_boundary.py src/foliaseal/presentation/qt/signing_shell.py src/foliaseal/presentation/qt/signing_workspace_sidebar.py tests/unit/test_qt_signing_action_boundary.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_signing_action_coordinator.py
    git diff --check

After the first pass implementation, run the required compliance review against at least:

    docs/ARCHITECTURE.md
    docs/SPEC.md
    docs/ExecPlans/signing_action_boundary_execplan.md

The compliance review must happen before the documentation worker and commit worker steps required by `dev-loop`.

## Validation and Acceptance

This slice is accepted when all of the following are true:

- the signing-action user flows are driven through a dedicated `SigningActionBoundary`
- `SigningActionCoordinator` still owns the state machine rather than duplicating policy in the boundary or the shell
- `SigningWorkspaceSidebar` remains the renderer for `SigningActionState`
- `SigningWorkspaceWidget` still exposes the current common-caller methods and behavior
- the new boundary has direct focused tests
- the focused coordinator and shell tests pass unchanged in behavior
- `docs/ARCHITECTURE.md` accurately describes the new ownership split

Observable proof is a focused test run where the new boundary tests pass and the pre-existing signing shell tests still show the same behaviors around output-path messages, success/failure text, and reopen enablement.

## Idempotence and Recovery

This slice is safe to retry because it is a behavior-preserving refactor inside local presentation code. If a first pass leaves both shell logic and boundary logic partially active, keep the coordinator as the single owner of signing state and remove the duplicate path before retrying. Do not widen the rollback by touching app-frame, review/text, or viewer-interaction modules. If a naming change in the sidebar breaks fake-widget tests, restore the old method name as a compatibility alias and reattempt the cleanup more narrowly.

## Artifacts and Notes

Important evidence to capture during implementation:

- the failing boundary test before the new boundary exists
- the passing focused pytest run after wiring is complete
- any compliance finding that requires doc reconciliation

Keep the artifacts concise and update this section with short snippets if unexpected behavior changes the plan.

## Interfaces and Dependencies

This slice uses the `In-process` dependency category. All collaborators are local Python modules and Qt test doubles.

At the end of the slice, the codebase should contain a boundary shaped approximately like this:

    @dataclass(frozen=True)
    class SigningActionBoundaryResult:
        state: SigningActionState
        request: SigningRequest | None = None
        opened_output_path: str | None = None
        status_event: str | None = None
        error_message: str | None = None
        error_via_emit: bool = False

    class SigningActionBoundary:
        def load(self) -> SigningActionState: ...
        def accept_output_path(self, selected_path: str) -> SigningActionBoundaryResult: ...
        def submit(self) -> SigningActionBoundaryResult: ...
        def open_signed_output(self) -> SigningActionBoundaryResult: ...
        def invalidate(self, reason: str) -> SigningActionBoundaryResult: ...

The exact names may shift, but the behavior must remain the same: the boundary owns shell-facing orchestration, the coordinator owns the state machine, and the sidebar renders the returned `SigningActionState`. The shell must not re-derive signing-action policy after this slice.

Revision note: Created on 2026-06-01 by Codex after the `dev-loop` explorer selected the first hybrid `3+4` slice as a narrow signing-action boundary over the existing coordinator and sidebar renderer.

Revision note: Updated on 2026-06-01 by Codex after the first implementation pass to record the completed boundary extraction, focused validation results, and the discovery that invalidation/reload paths also had to delegate through the boundary to keep ownership coherent.
