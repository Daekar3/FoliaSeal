# Add an atomic signing-workspace lifecycle boundary

This ExecPlan is a living document and must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`. It describes one complete implementation slice: introduce a small lifecycle coordinator and Qt mount adapter so opening a second PDF deterministically disposes the first workspace, while failed opens preserve the current workspace. The existing production shell port, testing adapter, compatibility surface, and user-visible app-frame actions remain available.

## Purpose / Big Picture

Today the app frame composes a new signing workspace and calls `QMainWindow.setCentralWidget()` directly, but it does not explicitly close the previous shell. A user who opens several PDFs in one session can therefore retain stale Qt widgets and signing-panel resources until Qt happens to destroy them. After this slice, opening a PDF is an atomic replacement: the candidate workspace is fully composed before it becomes active, the previous workspace is explicitly closed exactly once after successful mounting, and an invalid or unmountable candidate leaves the existing PDF open. Closing the frame-level workspace is idempotent.

The behavior is observable without a real desktop display. The focused fake-Qt tests will record central-widget mounting and shell cleanup, and the full project suite will continue to pass. A manual GUI smoke test, when a display is available, should show that opening PDF B replaces PDF A without stale dialogs or shells remaining.

## Child ExecPlan Dependencies

There are no child ExecPlans. The existing `app_frame_workspace_open` and `signing_shell_port` boundaries are prerequisites already present at the start of this slice.

## Progress

- [x] (2026-07-30) Reviewed the live checkout with an `explorer-light` subagent and confirmed the missing behavior is explicit old-shell teardown during replacement.
- [x] (2026-07-30) Chosen design: hybrid of a minimal atomic lifecycle facade and a Qt-specific mount adapter; preserve the existing production/testing split.
- [x] (2026-07-30) Added `signing_workspace_lifecycle.py` with Qt-free lifecycle/mount protocols, atomic replacement, candidate cleanup, and idempotent close.
- [x] (2026-07-30) Routed `FoliaSealAppFrame.open_pdf_path()` and placeholder/close handling through the coordinator.
- [x] (2026-07-30) Added focused lifecycle and app-frame tests for successful replacement, failed composition, mount failure, idempotent close, and action/current-state preservation; focused run passed 29 tests.
- [x] (2026-07-30) Ran the shell/app-frame regression set; 121 tests passed in 10.99 seconds.
- [x] (2026-07-30) Ran the full suite; 1,004 tests passed in 44.02 seconds with one pre-existing Pillow deprecation warning.
- [x] (2026-07-30) Compliance review identified and fixed a redundant direct central-widget install and added the missing close-before-open test; `docs/ARCHITECTURE.md` remains the final documentation update.
- [x] (2026-07-30) Updated `docs/ARCHITECTURE.md` through the architecture-steward documentation worker and corrected the remaining historical direct-mount wording.
- [x] (2026-07-30) Re-ran the full suite after remediation; 1,005 tests passed in 44.05 seconds with one pre-existing Pillow deprecation warning.
- [x] (2026-07-30) `git diff --check` passed and the working tree contains only the planned implementation, tests, architecture documentation, and this ExecPlan.
- [x] (2026-07-30) Committed the complete slice as `f1a824ef7` (`Add atomic signing workspace lifecycle`); the final plan-status amendment is ready to be folded into that commit.
- [ ] Run focused tests, the complete suite, and architecture/spec compliance review.
- [ ] Update architecture and relevant README/ExecPlan documentation.
- [ ] Commit the complete slice and record outcomes here.

## Surprises & Discoveries

- Observation: `WorkspaceOpenService` already composes the page count, viewer/signing workflows, shell port, and compatibility state cleanly.
  Evidence: `src/foliaseal/presentation/qt/app_frame_workspace_open.py` returns `OpenWorkspaceOutcome`; no new composition abstraction is needed for this slice.
- Observation: shell-local cleanup is already idempotent, but app-frame replacement does not invoke it.
  Evidence: `src/foliaseal/presentation/qt/signing_shell.py` uses a close-aware widget and `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py` also observes destruction; `FoliaSealAppFrame.open_pdf_path()` only assigns the new central widget.
- Observation: fake shells in existing tests do not implement a production `close()` method.
  Evidence: `_FakeShell` in `tests/unit/test_qt_app_frame.py` implements the public shell verbs but no lifecycle verb. Cleanup must therefore duck-call the widget rather than widen `SigningWorkspacePort`.
- Observation: the repository venv, not the system `pytest`, is the supported validation entrypoint.
  Evidence: the explorer reported `pytest` is not on PATH and validated the focused suite with `.venv/bin/python -m pytest`.
- Observation: the first compliance review caught a redundant direct mount and a missing fresh-close test.
  Evidence: `open_pdf_path()` still called `window.setCentralWidget()` after lifecycle replacement, and the initial lifecycle tests only closed after a successful open; both were corrected before the final suite.

## Decision Log

- Decision: Add `SigningWorkspaceLifecyclePort` and `WorkspaceMountPort` in a new presentation boundary module, keeping them independent of concrete Qt bindings.
  Rationale: The lifecycle needs to be unit-testable with fakes, while only the mount adapter needs to know about `QMainWindow.setCentralWidget()`.
  Date/Author: 2026-07-30 / Codex.
- Decision: Expose only `replace(command)` and `close()` as lifecycle commands; keep `SigningWorkspacePort.widget()` and `SigningWorkspaceBundle` unchanged.
  Rationale: This is the smallest complete vertical slice and avoids breaking harness callers or forcing every fake shell to implement disposal.
  Date/Author: 2026-07-30 / Codex.
- Decision: Compose the candidate before mounting it, mount the candidate before closing the old widget, and dispose a candidate if mounting fails.
  Rationale: This gives users atomic replacement: open failures never destroy the currently usable workspace, and mount failures do not leak the candidate.
  Date/Author: 2026-07-30 / Codex.
- Decision: The lifecycle catches no open errors; `FoliaSealAppFrame` remains the single place that converts exceptions to its existing error callback/message box.
  Rationale: Avoid duplicate warnings and preserve current error behavior.
  Date/Author: 2026-07-30 / Codex.
- Decision: Keep the broader neutral application-session/capability design deferred.
  Rationale: It would be a larger migration than necessary for the concrete leak and replacement bug; this slice establishes the seam needed for that future evolution.
  Date/Author: 2026-07-30 / Codex.

## Outcomes & Retrospective

The slice is complete. `SigningWorkspaceLifecycle` now composes candidates before mounting, disposes the previous widget only after successful mounting, cleans up candidates when mounting fails, and makes close-before-open and repeated close calls safe. `FoliaSealAppFrame` routes replacement and placeholder mounting through the lifecycle/mount seam while preserving current production-port and compatibility behavior. Focused lifecycle/app-frame coverage passes (34 tests), the shell regression set passes (121 tests), and the complete suite passes (1,005 tests, one unchanged Pillow deprecation warning). The architecture document records the new component, contract, control flow, and dependency ownership. Commit `f1a824ef7` contains the implementation, tests, architecture update, and this plan. The broader neutral capability-session redesign remains intentionally deferred for a later architecture slice.

## Context and Orientation

`src/foliaseal/presentation/qt/app_frame.py` owns the top-level `FoliaSealAppFrame`, its menus/actions, the current shell references, and the fakeable Qt bindings. Its `open_pdf_path()` currently builds an `OpenWorkspaceCommand`, invokes `WorkspaceOpenPort.open_workspace()`, stores the returned `SigningWorkspacePort` and `WorkspaceCompatibilityState`, and calls `window.setCentralWidget()`.

`src/foliaseal/presentation/qt/app_frame_workspace_open.py` owns page-count loading and workspace composition. `WorkspaceOpenService.open_workspace()` returns an `OpenWorkspaceOutcome` containing `shell_port` and `compatibility`. `WorkspaceCompatibilityState.shell_widget` is the concrete widget that must be mounted, while `shell_port` is the production caller contract.

`src/foliaseal/presentation/qt/signing_shell_port.py` defines `SigningWorkspacePort`, `SigningWorkspaceFactory`, `SigningWorkspaceBundle`, and `QtSigningWorkspaceFactory`. The bundle separates the production port from `SigningWorkspaceTestingPort`; do not remove or rename those types.

`src/foliaseal/presentation/qt/signing_shell.py` creates a close-aware shell widget whose close path disposes the properties panel. `signing_workspace_compatibility_surface.py` retains compatibility exports and connects widget destruction to the same disposal boundary. The new lifecycle must invoke the widget close path once and must tolerate a second close call.

The relevant tests are `tests/unit/test_qt_app_frame.py`, `tests/unit/test_qt_app_frame_workspace_open.py`, `tests/unit/test_qt_signing_shell.py`, and `tests/unit/test_signing_workspace_shell_surface.py`. They use fake bindings and fake shells, so the new lifecycle tests must remain headless and must not import PySide6 eagerly.

## Plan of Work

First create `src/foliaseal/presentation/qt/signing_workspace_lifecycle.py`. Define a `WorkspaceMountPort` protocol with `mount(widget: Any) -> None` and a `QtWorkspaceMount` adapter that calls `window.setCentralWidget(widget)`. Define `SigningWorkspaceLifecyclePort` with `replace(command: OpenWorkspaceCommand) -> OpenWorkspaceOutcome` and `close() -> None`. Define an internal active-workspace record containing the outcome and widget. The concrete lifecycle receives an existing `WorkspaceOpenPort`, a mount port, and an optional activation callback used by the frame to publish the returned outcome and enable/disable actions.

Implement `replace()` transactionally. Delegate composition to the existing open port first. Obtain the candidate widget from `outcome.compatibility.shell_widget`. Call the mount port. If mounting raises, close/dispose the candidate widget and re-raise, leaving the prior active record untouched. After successful mounting, close/dispose the prior active widget, replace the active record, invoke the activation callback with the new outcome, and return the outcome. Closing must be idempotent: if no active workspace exists it does nothing; otherwise it clears the active record, closes the widget if it has a callable `close`, and calls `deleteLater` when available without requiring either method on test doubles. Keep disposal guarded so repeated lifecycle calls cannot invoke cleanup twice for the same widget.

Then update `src/foliaseal/presentation/qt/app_frame.py`. Construct a `QtWorkspaceMount` around `self.window` and a lifecycle coordinator around the existing `_workspace_open_port`. Move the existing outcome assignment, central-widget installation, and action enabling into a small frame activation callback invoked only after a successful mount. Change `open_pdf_path()` to build the same `OpenWorkspaceCommand` and call lifecycle `replace()`, retaining its current exception-to-`_emit_error()` behavior and return value. Add a frame-level `close_workspace()` method that delegates to the lifecycle and resets `_current_shell_port`, `_current_workspace`, central placeholder, and disabled action state. Ensure `_set_placeholder()` does not accidentally close a newly mounted widget and that menu/action behavior is unchanged. Wire signed-output reopen callbacks through `open_pdf_path()` as today so they use the same atomic replacement path.

Add or adjust fake helpers in `tests/unit/test_qt_app_frame.py` and create focused lifecycle tests in `tests/unit/test_signing_workspace_lifecycle.py`. Test that a successful second open mounts the second widget, closes the first exactly once, updates `current_shell`/`current_workspace`, and keeps Save As/text-selection/copy actions enabled. Test that page-count/composition failure leaves the first widget mounted and unclosed. Test that a mount failure closes the candidate, preserves the first widget and frame state, and still emits exactly one existing error. Test that `close_workspace()` is safe before any open and safe when called twice after an open. Test that a shell without `close` or `deleteLater` remains supported. Preserve existing factory, compatibility-surface, and reopen-callback assertions.

Update `docs/ARCHITECTURE.md` in the Qt presentation map, major-components section, contracts, and open-document control flow to describe the lifecycle coordinator, the Qt mount adapter, atomic replacement order, and the fact that the production shell/testing adapter split remains unchanged. Update the relevant signing-shell section in `README.md` only if its current wording claims the frame directly owns widget replacement. Add implementation evidence and final status to this ExecPlan.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Add the lifecycle module and tests using the existing type/style conventions. Run the focused new and existing tests:

    .venv/bin/python -m pytest -q tests/unit/test_signing_workspace_lifecycle.py tests/unit/test_qt_app_frame.py tests/unit/test_qt_app_frame_workspace_open.py tests/unit/test_signing_workspace_shell_surface.py

   Expected result: all focused tests pass, including new assertions for one-time cleanup and failed replacement preservation.

2. Run the shell/GUI boundary regression set:

    .venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_signing_workspace_shell_surface.py tests/unit/test_qt_app_frame_certificate_management.py

3. Run the complete suite:

    .venv/bin/python -m pytest -q

   Expected result: the full suite passes; a pre-existing Pillow warning is acceptable if it remains unchanged.

4. Inspect the diff and architecture/spec requirements:

    git diff --check
    git status --short
    rg -n "SigningWorkspaceLifecycle|WorkspaceMount|setCentralWidget|close_workspace" src tests docs/ARCHITECTURE.md README.md

5. After documentation and review are complete, stage only the lifecycle implementation, its tests, documentation, and this ExecPlan, then commit with the repository’s normal commit tooling.

## Validation and Acceptance

The slice is accepted when opening PDF B after PDF A causes the fake or real frame to mount B and invokes A’s close/disposal path exactly once; the frame’s current shell/workflow properties refer to B; and the Save As, text-selection, and copy actions remain enabled. If B cannot be composed or mounted, A remains the central widget and current workspace, B is disposed if it was created, and the user receives the existing single error notification. Calling frame `close_workspace()` before opening anything or more than once after opening is harmless and leaves the placeholder/actions disabled.

The focused lifecycle and app-frame tests must pass, the shell/compatibility regression set must pass, and `.venv/bin/python -m pytest -q` must pass. `git diff --check` must report no whitespace errors. The architecture document must describe the implementation as it exists, not an aspirational future session API.

## Idempotence and Recovery

The changes are additive and safe to rerun. Tests use temporary paths and fake widgets; they do not open real documents or mutate user configuration. If a focused test fails, rerun only that test with `-vv`, inspect the lifecycle state transition, and update this plan’s `Surprises & Discoveries` and `Decision Log` before changing behavior. Do not use destructive Git commands. If implementation must be reverted before commit, remove only the new lifecycle module, its tests, and the app-frame/docs edits made by this plan.

## Artifacts and Notes

The key evidence to preserve in this plan is the focused test count, full-suite test count, `git diff --check` result, and the final commit hash. Keep generated GUI screenshots or artifacts out of the commit unless the existing test harness explicitly requires a tracked fixture.

## Interfaces and Dependencies

The new module must use only standard-library typing/dataclasses plus existing FoliaSeal presentation contracts. Its stable interfaces are:

    class WorkspaceMountPort(Protocol):
        def mount(self, widget: Any) -> None: ...

    class SigningWorkspaceLifecyclePort(Protocol):
        def replace(self, command: OpenWorkspaceCommand) -> OpenWorkspaceOutcome: ...
        def close(self) -> None: ...

The concrete lifecycle depends on `WorkspaceOpenPort` and `OpenWorkspaceCommand` from `app_frame_workspace_open.py`, but it must not import PySide6. `QtWorkspaceMount` is the only new object that calls `QMainWindow.setCentralWidget()`. The existing `SigningWorkspacePort` remains the production app-frame contract, and `SigningWorkspaceTestingPort` remains the harness contract. Real Qt widgets and PySide6 are external presentation dependencies; fake widgets, fake mount ports, and fake workspace-open services are local substitutes used by unit tests.

## Change-slice Boundaries

The primary change class is behavior: deterministic workspace replacement and cleanup. The same commit may include the necessary architecture/status documentation because the new lifecycle boundary changes documented control flow. Do not mix certificate/profile redesign, neutral capability-session migration, Phase 3 harness refactors, visible-signature layout work, dependency upgrades, generated artifacts, or unrelated formatting changes into this slice.

Plan revision note (2026-07-30): created after the live explorer confirmed that composition and shell/testing boundaries already exist; narrowed the implementation to lifecycle cleanup and atomic replacement rather than introducing a second broad application-session abstraction.
