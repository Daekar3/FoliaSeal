# Move signing-action rendering into the sidebar and centralize app-frame shell forwarding

This ExecPlan is complete. It records the finished state of the slice: the sidebar renders `SigningActionState`, the shell keeps orchestration, dialog handling, callback emission, and the public shell surface, and the app frame forwards active-shell calls through one helper instead of repeating the same null-check logic.

The user-visible behavior did not change. A user can still open a PDF, choose an output path, sign, reopen the signed result, and see the same status guidance. What changed is the ownership boundary behind that behavior: the `Sign PDF` panel now renders from the sidebar module, and the app frame no longer repeats the same active-shell forwarding pattern for save-as, settings, and certificate refresh.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/signing_workspace_sidebar_execplan.md` completed first so the production sidebar already existed as a dedicated module.
- [x] `docs/ExecPlans/signing_action_coordinator_execplan.md` completed first so signing-action state already had a Qt-free state source.
- [x] `docs/ExecPlans/signing_action_panel_execplan.md` completed first so the `Sign PDF` controls already lived in one sidebar panel.
- [x] No child ExecPlan was required for this narrow first hybrid `1+3` slice.

## Progress

- [x] (2026-05-31T20:38:38Z) Completed the required `explorer-light` audit for the recommended hybrid `1+3` shell seam and fixed the slice to signing-action render ownership plus app-frame forwarding cleanup.
- [x] (2026-05-31T20:38:38Z) Reviewed the existing shell signing-action application path in `src/foliaseal/presentation/qt/signing_shell.py` and the repeated active-shell forwarding in `src/foliaseal/presentation/qt/app_frame.py`.
- [x] (2026-05-31T20:38:38Z) Implemented the sidebar render-owner split in `src/foliaseal/presentation/qt/signing_workspace_sidebar.py`.
- [x] (2026-05-31T20:38:38Z) Simplified `src/foliaseal/presentation/qt/signing_shell.py` so it keeps orchestration and the public widget surface while delegating `SigningActionState` widget mutation to the sidebar.
- [x] (2026-05-31T20:38:38Z) Centralized app-frame active-shell forwarding in `src/foliaseal/presentation/qt/app_frame.py` via `_with_current_shell_port(...)`.
- [x] (2026-05-31T20:38:38Z) Discovered and fixed the sidebar width fallback issue so the flow-detail label still renders legibly when the container reports zero width during early layout or test harness setup.
- [x] (2026-05-31T20:38:38Z) Validated the finished slice with the focused shell/app-frame test suite and the targeted lint/diff checks.

## Surprises & Discoveries

- Observation: the sidebar container can report zero width before layout stabilizes, especially in the test harness.
  Evidence: the `Sign PDF` detail label would otherwise collapse; `SigningWorkspaceSidebar.apply_signing_action_state()` now uses `_panel_available_width(...)` with a 520px fallback before applying a width limit.

- Observation: the app frame had the same active-shell forwarding pattern in three places.
  Evidence: `_choose_save_as()`, `_apply_app_settings()`, and `_refresh_shell_certificate_configurations()` all delegated through the same `_current_shell_port` guard before the helper refactor.

- Observation: the ownership split was small but meaningful enough to require an architecture update.
  Evidence: the sidebar now mutates the `Sign PDF` widgets directly, while the shell keeps orchestration, dialog handling, callback emission, and the public shell-facing widget attributes.

## Decision Log

- Decision: move only `SigningActionState` rendering into `SigningWorkspaceSidebar` and leave dialog handling, callback emission, and public shell-facing widget exposure in `signing_shell.py`.
  Rationale: this was the smallest meaningful ownership split. It deepened the existing sidebar boundary without widening the slice into document-review or viewer choreography.
  Date/Author: 2026-05-31 / Codex

- Decision: preserve current app-frame no-shell-loaded behavior while removing repeated forwarding code.
  Rationale: `File > Save As...`, settings propagation, and certificate refresh already returned early when `_current_shell_port` was `None`; the helper only removed duplication.
  Date/Author: 2026-05-31 / Codex

- Decision: add a width fallback in the sidebar renderer.
  Rationale: the container can be zero-width during early layout and in tests, so the fallback keeps the flow-detail text readable and makes the render owner robust.
  Date/Author: 2026-05-31 / Codex

- Decision: update `docs/ARCHITECTURE.md` because the ownership split changed the actual implementation truth.
  Rationale: the sidebar now owns `SigningActionState` rendering, which is a material boundary change that should be documented in the project architecture.
  Date/Author: 2026-05-31 / Codex

## Outcomes & Retrospective

The slice is finished and the finished implementation is narrow and behavior-preserving. The sidebar now owns `SigningActionState` rendering, the shell still owns orchestration and the public shell surface, and the app frame has one forwarding helper for active-shell operations.

The only notable implementation wrinkle was the sidebar width fallback. Without it, the detail label could collapse when the container had not yet established a width. That fallback is now part of the documented boundary and the validation surface.

No follow-on ExecPlan is required from this slice. The next work in this area should start from the current sidebar/render split rather than rebuilding the ownership boundary.

## Context and Orientation

The production Qt signing workspace lives in `src/foliaseal/presentation/qt/signing_shell.py`. It builds the viewer, the properties panel, the sidebar, the document-review session, the text session, the viewer-interaction session, the workspace-interaction session, and the signing-action coordinator.

The sidebar lives in `src/foliaseal/presentation/qt/signing_workspace_sidebar.py`. It now owns the `Sign PDF` panel widget tree and the rendering of `SigningActionState`.

The signing-action state machine lives in `src/foliaseal/presentation/qt/signing_action_coordinator.py`. It produces immutable `SigningActionState` values, but it does not mutate widgets itself.

The top-level app frame lives in `src/foliaseal/presentation/qt/app_frame.py`. It owns the `QMainWindow` wrapper and now uses a single helper, `_with_current_shell_port(...)`, to forward save-as, settings, and certificate-refresh calls to the active shell when one is loaded.

In this plan, “render owner” means the code that changes the visible widgets for a specific panel. “Public shell surface” means the shell-facing widget attributes and app-frame callbacks that other code still inspects or invokes.

## Plan of Work

The work was completed in four small edits. First, `src/foliaseal/presentation/qt/signing_workspace_sidebar.py` gained `apply_signing_action_state(...)`, so the sidebar can paint the `Sign PDF` panel from `SigningActionState` and apply its own width limit to the flow-detail label.

Second, `src/foliaseal/presentation/qt/signing_shell.py` stopped mutating the sign panel widgets directly. Its `_apply_signing_action_state(...)` method now updates the shell-owned `widget.last_signing_result` field and delegates widget mutation to the sidebar.

Third, `src/foliaseal/presentation/qt/app_frame.py` gained `_with_current_shell_port(...)`, and `_choose_save_as()`, `_apply_app_settings()`, and `_refresh_shell_certificate_configurations()` now use that helper instead of repeating the same null-check and forward pattern.

Finally, `docs/ARCHITECTURE.md` and this ExecPlan were updated so the documentation matches the completed ownership split instead of the earlier shell-owned rendering model.

## Concrete Steps

Run these commands from `/home/daekar/FoliaSeal`:

    pytest tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py
    ruff check src/foliaseal/presentation/qt/signing_shell.py src/foliaseal/presentation/qt/signing_workspace_sidebar.py src/foliaseal/presentation/qt/app_frame.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py
    git diff --check

Expected result:

    - the focused Qt shell/app-frame tests pass;
    - `ruff check` reports no issues;
    - `git diff --check` prints nothing.

## Validation and Acceptance

The accepted behavior is:

- the sidebar owns the visible mutation of the `Sign PDF` panel from `SigningActionState`;
- the shell still owns orchestration, dialog handling, callback emission, and the public shell-facing widget attributes;
- `File > Save As...`, settings propagation, and certificate refresh still work when a shell is loaded and still no-op when no shell is loaded;
- the `Sign PDF` detail label still has a sensible width limit even when the sidebar container starts at zero width.

The focused unit tests are the proof point for that behavior. The result is accepted when those tests pass and the lint/diff checks stay clean.

## Idempotence and Recovery

The changes are safe to rerun conceptually because they are additive ownership shifts inside existing Qt code. If the sidebar ever starts mutating the same `Sign PDF` controls as the shell again, restore one render owner before proceeding. If the app-frame helper regresses no-shell behavior, revert only the helper usage and keep the test coverage that proves the forwarding contract.

## Artifacts and Notes

The most important implementation points are:

    src/foliaseal/presentation/qt/signing_workspace_sidebar.py
    SigningWorkspaceSidebar.apply_signing_action_state(...)
    _panel_available_width(...)

    src/foliaseal/presentation/qt/signing_shell.py
    def _apply_signing_action_state(self, state: SigningActionState) -> None:
        self.widget.last_signing_result = state.last_signing_result
        self._sidebar.apply_signing_action_state(state)

    src/foliaseal/presentation/qt/app_frame.py
    def _with_current_shell_port(self, action: Callable[[AppFrameShellPort], Any | None]) -> Any | None:
        shell_port = self._current_shell_port
        if shell_port is None:
            return None
        return action(shell_port)

## Interfaces and Dependencies

`src/foliaseal/presentation/qt/signing_workspace_sidebar.py` now exposes:

    def apply_signing_action_state(self, state: SigningActionState) -> None

`src/foliaseal/presentation/qt/app_frame.py` now exposes the forwarding helper:

    def _with_current_shell_port(
        self,
        action: Callable[[AppFrameShellPort], Any | None],
    ) -> Any | None

The sidebar depends on `SigningActionState` from `signing_action_coordinator.py`, and the shell depends on the sidebar for sign-panel rendering. The app frame depends on `AppFrameShellPort` for forwarding, but it must continue to preserve the no-shell-loaded no-op behavior.

Revision note: updated on 2026-05-31 to record the completed sidebar render-owner split, the app-frame forwarding helper, the width fallback discovery, and the architecture-doc closeout.
