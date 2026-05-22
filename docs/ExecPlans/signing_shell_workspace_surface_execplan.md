# Remove the signing-shell workspace escape hatch

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows the requirements in `.agents/skills/write-execplan/PLANS.md`. It is self-contained so a contributor can resume the slice from only this file and the current repository tree.

## Purpose / Big Picture

FoliaSeal's returned Qt signing-shell widget still exposes its entire backing `SigningWorkspaceWidget` object as `widget._signing_workspace`. That means tests and future callers can bypass the intended public surface and reach directly into private viewer, draft, and button internals. After this change, the shell should still behave the same, but the whole-workspace escape hatch will be gone and the few remaining legitimate needs will use explicit public widget attributes instead.

This slice is intentionally narrow. It does not try to remove every white-box test or redesign the shell. It removes `widget._signing_workspace = self` and replaces it with a small explicit surface for the current high-value reads: signing workflow, viewer workflow, sign button, and last signing result.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/signature_properties_coordinator_execplan.md` completed first so state reconciliation already has an application-layer boundary.
- [x] `docs/ExecPlans/signature_preview_lifecycle_execplan.md` completed first so canonical preview lifecycle is not part of this surface cleanup.
- [x] `docs/ExecPlans/signature_preview_layout_execplan.md` completed first so preview geometry/layout ownership is already outside this slice.
- [x] `docs/ExecPlans/app_frame_shell_public_seam_execplan.md` completed first so the app frame already uses public shell entrypoints for settings sync and certificate refresh.
- [ ] A later child ExecPlan may further trim white-box shell tests after the workspace escape hatch is gone.

## Progress

- [x] (2026-05-22T23:20:00Z) Completed the required `explorer-light` audit and fixed the next slice to removing `widget._signing_workspace` plus a few explicit accessors only.
- [x] (2026-05-22T23:31:00Z) Added explicit public widget attributes for `signing_workflow`, `viewer_workflow`, and `sign_button`, while keeping `last_signing_result` on the widget surface.
- [x] (2026-05-22T23:32:00Z) Removed `widget._signing_workspace = self` from `SigningWorkspaceWidget`.
- [x] (2026-05-22T23:35:00Z) Rewrote the focused shell tests to use the explicit public shell surface instead of the workspace alias.
- [x] (2026-05-22T23:38:00Z) Ran focused validation successfully: `pytest tests/unit/test_qt_signing_shell.py` (`58 passed`), focused `ruff check`, and `git diff --check`.
- [x] (2026-05-22T23:52:00Z) Completed the required `explorer-light` compliance review. No code defects remained; the only follow-up was stale historical evidence in an older ExecPlan.

## Surprises & Discoveries

- Observation: the returned shell widget already exposes several stable entrypoints, so the remaining escape hatch is narrower than it first looks.
  Evidence: `signing_shell.py` already exposes `properties_panel`, `viewer_widget`, `choose_output_pdf_path`, `refresh_certificate_configurations`, `submit_sign_request`, `open_signed_output`, `last_signing_result`, and summary labels on the widget object.

- Observation: most remaining `_signing_workspace` usage in tests clusters around only four needs.
  Evidence: the current shell tests use the alias mainly for `last_signing_result`, `_draft_workflow`, `_viewer_workflow`, and `_sign_button`, plus a small number of `properties_panel` reads that are already public.

- Observation: removing the alias did not require any production behavior changes beyond exposing named widget attributes.
  Evidence: after the access-path cleanup, `tests/unit/test_qt_signing_shell.py` still passed unchanged in behavior with `58 passed`; only the attribute names in the tests moved.

## Decision Log

- Decision: Keep this slice to removing the alias and adding only the minimum explicit accessors needed to preserve current tests.
  Rationale: Rewriting every shell test away from all internal object access would be a broader change with more review noise. This slice aims to remove the broadest seam first.
  Date/Author: 2026-05-22 / Codex

- Decision: Expose named widget attributes for workflow/button access instead of returning the whole `SigningWorkspaceWidget`.
  Rationale: The widget already exposes several named attributes. Adding a few more continues that pattern while keeping the surface explicit and smaller than exporting the entire backing object.
  Date/Author: 2026-05-22 / Codex

## Outcomes & Retrospective

This slice is now implemented. The returned shell widget no longer exposes the entire `SigningWorkspaceWidget` as `_signing_workspace`. Instead, the current legitimate needs use explicit public widget attributes for `signing_workflow`, `viewer_workflow`, `sign_button`, `properties_panel`, and `last_signing_result`.

The change stayed narrow as intended. There were no behavioral changes to the shell itself, no app-frame changes, and no preview-boundary churn. The work was an access-path cleanup plus focused test rewrites, and the shell regression set stayed green throughout.

The compliance review also clarified the remaining work. The broadest escape hatch is gone, but many shell tests still inspect detailed workflow and widget state through the explicit surface. That is a follow-on white-box reduction problem, not a failure of this slice.

## Context and Orientation

The Qt signing shell is built in `src/foliaseal/presentation/qt/signing_shell.py`. The main composition object is `SigningWorkspaceWidget`, which owns a viewer workflow, a signing draft workflow, a properties panel, summary cards, output-path selection, and signing execution behavior. It returns a Qt widget object that the rest of the app and the tests interact with.

Today that returned widget still exposes `self` wholesale through `widget._signing_workspace`. That is a backdoor: instead of using a named public surface, callers can reach into `_draft_workflow`, `_viewer_workflow`, `_sign_button`, and other internals. The app frame no longer depends on this escape hatch after the public-seam cleanup, but `tests/unit/test_qt_signing_shell.py` still does in many places.

The narrow goal here is to replace the backdoor with explicit names. The widget should publish the specific objects the tests still legitimately need: the signing draft workflow, the viewer workflow, the sign button, and the last signing result that is already conceptually public. `properties_panel` is already public and should remain so. The alias `widget._signing_workspace` should then be removed.

The focused regression surface is `tests/unit/test_qt_signing_shell.py`. The most sensitive behaviors are output-path selection, selection-driven placement updates, sign-result clearing/reset, sign-button enablement, and flow-summary synchronization. Those behaviors must remain unchanged while the access path used by tests becomes more explicit.

## Plan of Work

First, update `src/foliaseal/presentation/qt/signing_shell.py`. In `SigningWorkspaceWidget.__init__`, expose named public widget attributes for the current backing objects that tests still need: `signing_workflow`, `viewer_workflow`, and `sign_button`. Keep `last_signing_result` updated on the widget as it already is. Remove `self.widget._signing_workspace = self`.

Second, update `tests/unit/test_qt_signing_shell.py`. Replace reads of `widget._signing_workspace.last_signing_result` with `widget.last_signing_result`. Replace reads and writes through `widget._signing_workspace._draft_workflow` with `widget.signing_workflow`. Replace reads through `widget._signing_workspace._viewer_workflow` with `widget.viewer_workflow`. Replace sign-button assertions through `widget._signing_workspace._sign_button` with `widget.sign_button`. Leave `widget.properties_panel` as-is because it is already part of the explicit surface.

Third, run focused validation on the shell tests and lint for the touched files. In the completed slice, the compliance review found no code defects; it only required updating this plan and one stale evidence note in `docs/ExecPlans/signing_flow_summary_shell_execplan.md`.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

Inspect the current backdoor and its test usage:

    rg -n "_signing_workspace" src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py

After editing, run the focused shell regression set:

    pytest tests/unit/test_qt_signing_shell.py

Then run focused lint:

    ruff check src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py

Finally ensure patch hygiene:

    git diff --check

If compliance review requires doc changes, rerun the relevant focused checks and record the final passing commands here.

## Validation and Acceptance

Acceptance is behavioral. After the change, the signing shell should still pass its focused fake-Qt regression suite, but the returned widget should no longer expose the entire backing `SigningWorkspaceWidget` as `_signing_workspace`.

The proof points are:

- `pytest tests/unit/test_qt_signing_shell.py` passes.
- `rg -n "_signing_workspace" src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py` no longer shows the widget alias or test uses of that alias.
- sign-result, placement, viewer-page, and sign-button assertions still work through explicit public widget attributes.

## Idempotence and Recovery

This refactor is safe to repeat because it is an access-path cleanup. Add the named public widget attributes first, switch tests to them, then remove the alias last. If a test still fails because one access path was missed, reintroduce only the missing explicit attribute rather than restoring the whole-workspace alias.

If a behavior regression appears, compare the test before/after path carefully: the goal is to change only how callers reach the existing objects, not the underlying workflow or button behavior.

## Artifacts and Notes

Current backdoor evidence before the change:

    src/foliaseal/presentation/qt/signing_shell.py
    - SigningWorkspaceWidget assigns `self.widget._signing_workspace = self`.

    tests/unit/test_qt_signing_shell.py
    - many tests reach through `_signing_workspace` for draft workflow, viewer workflow, sign button, and last signing result.

Validation evidence after implementation:

    pytest tests/unit/test_qt_signing_shell.py
    58 passed

    ruff check src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py
    All checks passed!

    git diff --check
    <no output>

## Interfaces and Dependencies

At the end of this slice, the returned shell widget in `src/foliaseal/presentation/qt/signing_shell.py` should expose explicit named attributes with roles like:

    self.widget.signing_workflow = self._draft_workflow
    self.widget.viewer_workflow = self._viewer_workflow
    self.widget.sign_button = self._sign_button
    self.widget.last_signing_result = self._last_signing_result

The slice should remove:

    self.widget._signing_workspace = self

The shell tests should depend on those explicit names instead of the whole-workspace alias.

Change note: 2026-05-22 / Codex

Created this ExecPlan from the `explorer-light` recommendation for the next `ExecPlan C` child slice. Updated it after implementation and compliance review to record the completed workspace-surface cleanup, passing focused validation, and the remaining follow-on test-surface debt.
