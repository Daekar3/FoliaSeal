# Complete ExecPlan C with a narrow signing-shell behavior surface

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows the requirements in `.agents/skills/write-execplan/PLANS.md`. It is self-contained so a contributor can resume the slice from only this file and the current repository tree.

## Purpose / Big Picture

FoliaSeal's Qt signing shell no longer leaks its entire backing workspace object, and this slice finished the remaining shell-surface cleanup. Before this change, the returned shell widget still exposed raw workflow objects and the raw sign button to tests, which kept the seam white-box heavy and left `Issue #51` ExecPlan C partially open. After the change, the shell offers a small behavior-oriented surface for the remaining legitimate test needs: changing the logical viewer page without forcing a refresh, reading or setting the signature rectangle, preserving certificate-configuration selection across preset actions, reading the current signature appearance, and checking whether signing is currently enabled.

This slice is intentionally narrow. It completes ExecPlan C's shell-surface cleanup without reopening the coordinator, preview lifecycle, preview layout, or app-frame seams. The only allowed change classes are one behavior change commit for the shell/test seam and one documentation/status update commit if compliance review requires it. Unrelated preview behavior, certificate-management behavior, and acceptance-harness churn are explicitly out of scope.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/signature_properties_coordinator_execplan.md` completed first so signing-properties reconciliation already has its own application-layer boundary.
- [x] `docs/ExecPlans/signature_preview_lifecycle_execplan.md` completed first so canonical preview lifecycle is already outside this slice.
- [x] `docs/ExecPlans/signature_preview_layout_execplan.md` completed first so preview geometry/layout ownership is already outside this slice.
- [x] `docs/ExecPlans/app_frame_shell_public_seam_execplan.md` completed first so the app frame already uses public shell entrypoints.
- [x] `docs/ExecPlans/signing_shell_workspace_surface_execplan.md` completed first so the broad `_signing_workspace` escape hatch is already gone.
- [x] No further child ExecPlan is needed for Issue `#51`; this slice completed the mapped ExecPlan C seam cleanup.

## Progress

- [x] (2026-05-22T14:40:46Z) Completed the required `explorer-light` audit and fixed the final ExecPlan C slice to behavior-surface cleanup for page, placement, certificate-selection, appearance, and sign-enabled access.
- [x] (2026-05-22T14:40:46Z) Reviewed `src/foliaseal/presentation/qt/signing_shell.py`, the remaining white-box shell tests, and the prior ExecPlan C child plans before drafting this plan.
- [x] (2026-05-22T14:48:53Z) Added a narrow public behavior surface to `SigningWorkspaceWidget` and exposed it on the returned shell widget for logical page state, signature rectangle state, selected certificate configuration state, signature appearance, and sign-enabled status.
- [x] (2026-05-22T14:48:53Z) Rewrote the remaining `tests/unit/test_qt_signing_shell.py` cases to use the behavior surface instead of `widget.signing_workflow`, `widget.viewer_workflow`, and `widget.sign_button`.
- [x] (2026-05-22T14:48:53Z) Ran focused validation successfully: `pytest tests/unit/test_qt_signing_shell.py` (`58 passed`), focused `ruff check`, and `git diff --check`.
- [x] (2026-05-22T14:50:22Z) Completed the required `explorer-light` compliance review. It found no code-level gaps and required only completion-state updates in this ExecPlan.
- [x] (2026-05-22T14:50:22Z) Recorded the final slice outcome: Issue `#51` ExecPlan C is complete after this shell behavior-surface cleanup, subject only to commit and issue-close mechanics.

## Surprises & Discoveries

- Observation: the remaining shell-surface debt is tightly clustered and does not require a broad refactor to finish ExecPlan C.
  Evidence: the active `explorer-light` review found the only remaining direct shell-test reach-throughs in `tests/unit/test_qt_signing_shell.py` and recommended one final narrow slice.

- Observation: `SignaturePropertiesPanel` already exposed public `set_signature_rect()` and `set_signature_appearance()` methods, so the missing seam was mostly about shell-level state queries and a small amount of setup convenience.
  Evidence: `src/foliaseal/presentation/qt/signing_shell.py` defines those methods on `SignaturePropertiesPanel`, while the pre-change tests reached through `widget.signing_workflow.update_signature_rect(...)`, `widget.viewer_workflow.session.jump_to_page(...)`, and `widget.sign_button._enabled`.

- Observation: one shell test intentionally depends on the distinction between the logical session page and the last rendered snapshot page.
  Evidence: the snapshot-page validation test must move the current page without triggering a rerender, so the final shell seam uses `set_logical_page_index()` instead of a method that always calls `ViewerWorkflow.jump_to_page()` and refreshes the snapshot.

- Observation: the required compliance review found only living-document drift, not an architectural or code defect.
  Evidence: the `explorer-light` reviewer accepted the shell behavior surface and test rewrites, and asked only for this ExecPlan to be brought from draft state to completion state.

## Decision Log

- Decision: complete ExecPlan C by removing the remaining raw workflow/button surface from tests rather than leaving `widget.signing_workflow`, `widget.viewer_workflow`, and `widget.sign_button` as the permanent public contract.
  Rationale: those names still expose implementation objects instead of stable behavior. A small shell API is a better end-state and is enough to close the issue cleanly.
  Date/Author: 2026-05-22 / Codex

- Decision: keep the new shell surface behavior-oriented and narrow instead of exporting new broad objects.
  Rationale: the explorer findings show only five behavior categories are still needed. Exporting more objects would reopen the same architectural problem under different names.
  Date/Author: 2026-05-22 / Codex

## Outcomes & Retrospective

Implementation, focused validation, and compliance review are complete. The returned shell widget now exposes narrow behavior methods for logical page state, signature-rectangle state, selected certificate-configuration state, signature appearance, and sign-enabled state instead of raw workflow or button objects. The focused shell regression set stayed green, and the reviewer found no code-level or architecture-doc defect in the slice.

This completes the mapped ExecPlan C work for Issue `#51`. The app frame already uses public shell entrypoints, the broad `_signing_workspace` escape hatch is gone, and the last direct workflow/button shell-test reach-throughs have been replaced with explicit behavior methods. No further child ExecPlan is needed to satisfy the issue's coordinator-follow-on scope.

## Context and Orientation

The Qt signing shell is built in `src/foliaseal/presentation/qt/signing_shell.py`. Its main composition object is `SigningWorkspaceWidget`, which owns the viewer workflow, signing draft workflow, properties panel, document review card, flow summary card, output-path selection, and signing execution behavior. The rest of the app does not talk to `SigningWorkspaceWidget` directly; instead, `build_qt_signing_shell()` returns a Qt widget object that exposes selected methods and state on that widget surface.

Recent ExecPlan C child slices already improved this design. `docs/ExecPlans/app_frame_shell_public_seam_execplan.md` moved app-frame interactions onto public shell methods. `docs/ExecPlans/signing_shell_workspace_surface_execplan.md` removed `widget._signing_workspace`, which had exposed the entire workspace object as a backdoor. At the start of this slice, the remaining debt was smaller but still architectural: tests in `tests/unit/test_qt_signing_shell.py` still reached into `widget.viewer_workflow`, `widget.signing_workflow`, and `widget.sign_button` for page setup, placement setup, certificate-selection preservation, appearance assertions, and sign-enabled assertions.

The smallest clean finish is to give the returned shell widget an explicit behavior surface for those needs. In this repository, a "behavior surface" means public methods that describe what the shell can do or report, rather than public access to the backing workflow objects or individual UI controls. The new surface should remain thin and should delegate to the existing workflow, panel, and button logic so no user-visible behavior changes.

## Plan of Work

First, update `src/foliaseal/presentation/qt/signing_shell.py`. Add small public methods on `SigningWorkspaceWidget` for the remaining legitimate interactions: set the logical current page without requiring a viewer refresh, report the current logical page, set a signature rectangle from explicit coordinates, report the current signature rectangle, set and report the selected certificate-configuration identifier, report the current signature appearance, and report whether the sign action is enabled. Expose those methods on the returned shell widget in `SigningWorkspaceWidget.__init__`. Once the methods exist and the tests are switched, remove the older widget attributes `signing_workflow`, `viewer_workflow`, and `sign_button`.

Second, update `tests/unit/test_qt_signing_shell.py`. Replace direct workflow/button reads and writes with the new shell methods. When a test needs to stage placement, call the shell's rectangle setter instead of `signing_workflow.update_signature_rect(...)`. When a test needs to inspect placement, call the shell's rectangle getter. When a test needs to move the logical viewer page without a refresh, call the shell's page method. When a test needs sign readiness, call the shell's sign-enabled method rather than inspecting the fake button internals.

Third, run focused validation on the shell test module and lint for the touched files. After the first pass, spawn the required `explorer-light` compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and the touched ExecPlan/docs state. If the reviewer finds stale documentation, update the docs and rerun any affected focused checks.

Fourth, if compliance is clean, commit the slice and then verify whether Issue `#51` is now complete. The expected answer is yes if no additional app-frame/shell seam debt remains in the issue's mapped ExecPlan C scope.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

Inspect the remaining white-box shell-test surface before editing:

    rg -n "widget\\.(signing_workflow|viewer_workflow|sign_button)" tests/unit/test_qt_signing_shell.py
    sed -n '1726,2145p' src/foliaseal/presentation/qt/signing_shell.py

After editing, run the focused shell regression set:

    pytest tests/unit/test_qt_signing_shell.py

Then run focused lint:

    ruff check src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py

Finally ensure patch hygiene:

    git diff --check

If compliance review requires documentation updates, rerun the relevant focused checks and record the final passing commands in this file.

## Validation and Acceptance

Acceptance is behavioral. After the change, the focused shell regression set passes, and the returned shell widget no longer requires `widget.signing_workflow`, `widget.viewer_workflow`, or `widget.sign_button` for the remaining tests.

The proof points are:

- `pytest tests/unit/test_qt_signing_shell.py` passes.
- `rg -n "widget\\.(signing_workflow|viewer_workflow|sign_button)" tests/unit/test_qt_signing_shell.py` returns no matches.
- the remaining page-selection, placement, preset-preservation, appearance, and sign-enabled tests all pass using the new behavior methods.
- focused `ruff check` and `git diff --check` pass.

Those proofs now hold, and the compliance review did not identify additional open scope under Issue `#51`. This slice completes ExecPlan C.

## Idempotence and Recovery

This refactor is safe to repeat because it is a seam cleanup. Add the new behavior methods first, switch the tests to them, and only then remove the older widget attributes. If a test still fails because one behavior was not covered, add the narrowest missing method rather than restoring raw workflow or button access.

If a regression appears, compare the old and new paths carefully. The goal is not to change how page movement, placement, certificate selection, or sign readiness work; the goal is only to change how tests and callers reach those existing behaviors.

## Artifacts and Notes

Historical white-box shell-test evidence before the change:

    tests/unit/test_qt_signing_shell.py
    - uses `widget.viewer_workflow.session.jump_to_page(...)`
    - uses `widget.signing_workflow.update_signature_rect(...)`
    - uses `widget.signing_workflow.signature_rect`
    - uses `widget.signing_workflow.selected_certificate_configuration_id`
    - uses `widget.signing_workflow.signature_appearance`
    - uses `widget.sign_button._enabled`

Validation evidence after implementation:

    pytest tests/unit/test_qt_signing_shell.py
    58 passed

    ruff check src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py
    All checks passed!

    git diff --check
    <no output>

## Interfaces and Dependencies

At the end of this slice, `src/foliaseal/presentation/qt/signing_shell.py` should expose a shell behavior surface along these lines:

    class SigningWorkspaceWidget:
        def set_logical_page_index(self, page_index: int) -> None: ...
        def logical_page_index(self) -> int: ...
        def set_signature_rect(
            self,
            *,
            page_index: int,
            left_pt: float,
            bottom_pt: float,
            width_pt: float,
            height_pt: float,
        ) -> SignatureRect: ...
        def signature_rect(self) -> SignatureRect | None: ...
        def set_selected_certificate_configuration_id(
            self,
            configuration_id: str | None,
        ) -> None: ...
        def selected_certificate_configuration_id(self) -> str | None: ...
        def signature_appearance(self) -> SignatureAppearance | None: ...
        def is_sign_action_enabled(self) -> bool: ...

The returned shell widget should expose those methods directly, for example:

    self.widget.set_logical_page_index = self.set_logical_page_index
    self.widget.signature_rect = self.signature_rect
    self.widget.is_sign_action_enabled = self.is_sign_action_enabled

The slice should remove these older widget attributes once tests no longer need them:

    self.widget.signing_workflow = self._draft_workflow
    self.widget.viewer_workflow = self._viewer_workflow
    self.widget.sign_button = self._sign_button

Change note: 2026-05-22 / Codex

Created this ExecPlan from the required `explorer-light` findings for the final Issue `#51` ExecPlan C slice. Updated it after implementation, focused validation, and compliance review to record the completed shell behavior-surface cleanup and the conclusion that Issue `#51` can now be closed.
