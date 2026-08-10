# Add typed View zoom commands

This ExecPlan is a living document and must be maintained in accordance with
`.agents/skills/write-execplan/PLANS.md`. It is a focused child of
`docs/ExecPlans/ui_command_model_shortcuts_execplan.md` and the V1 compliance parent.

## Purpose / Big Picture

After this slice, a user can operate the viewer's existing exact zoom behavior from the normative
View menu: Zoom In, Zoom Out, and Reset Zoom are real typed commands with conventional shortcuts,
accessible descriptions, and truthful document-dependent enablement. The commands route through the
public signing-workspace session port, so the application frame never reaches into viewer widgets.
Fit Page, Fit Width, page navigation, search, and text selection retain their existing behavior.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md`, `docs/UI_SPEC.md`, and `docs/ARCHITECTURE.md` are the governing documents.
- [x] `docs/ExecPlans/ui_command_model_shortcuts_execplan.md` provides the typed frame command
  registry and menu-routing seam.
- [x] `docs/ExecPlans/ui_pdf_navigation_zoom_pan_execplan.md` provides the existing clamped
  10%–800% viewer zoom implementation and typed reset/fit methods.
- [x] `docs/ExecPlans/ui_signing_rail_stage_status_execplan.md` provides the active workspace shell
  lifecycle used by the frame action state.

## Progress

- [x] (2026-08-10) Explorer audit confirmed that viewer zoom behavior exists but is not represented
  in the app-frame command registry or public session port.
- [x] Add red registry, frame-routing, and session-port tests for Zoom In/Out/Reset.
- [x] Add the typed command definitions and route them through the existing public session port.
- [x] Validate shortcut/menu behavior without creating duplicate viewer dispatch in the fake frame
  action surface and public viewer adapter tests.
- [x] Run focused/full/lint/offscreen validation and clean all owned processes and temp roots.
- [x] Complete compliance review and update architecture/parent status; commit remains the final
  handoff step for this slice.

## Surprises & Discoveries

- Observation: `ViewerWidget` already handles `+`, `-`, and unmodified `0` locally and the
  application/session layers already expose reset zoom, but the frame registry has no zoom commands.
  Evidence: `src/foliaseal/presentation/qt/viewer_widget.py`, `signing_shell.py`, and
  `signing_shell_port.py` contain the behavior while `app_frame_command_model.py` has only fit
  commands.
- Observation: adding the commands to the registry must preserve the existing viewer-local fallback
  keys; action-trigger tests therefore assert one public-port call rather than relying on raw key
  delivery through a child widget.

## Decision Log

- Decision: expose Zoom In, Zoom Out, and Reset Zoom as View actions with `Ctrl++`, `Ctrl+-`, and
  `Ctrl+0`-equivalent semantics only where they do not collide with Fit Page; use `Ctrl+0` for Fit
  Page and leave Reset Zoom as a menu action without a shortcut because UI_SPEC assigns `Ctrl+0` to
  Fit Page. Rationale: the governing document requires exact zoom and conventional zoom shortcuts,
  while duplicate shortcuts would make one key invoke two policies. Date/Author: 2026-08-10 / Codex.
- Decision: route actions through `SigningWorkspaceSessionPort.zoom_in_view()`,
  `zoom_out_view()`, and `reset_zoom_view()` rather than exposing viewer internals. Rationale: the
  existing fit/navigation actions establish this public boundary and keep Qt composition honest.
  Date/Author: 2026-08-10 / Codex.

## Outcomes & Retrospective

Implemented on 2026-08-10. The View menu now exposes Zoom In (`Ctrl++`), Zoom Out (`Ctrl+-`), and
Reset Zoom, all disabled without an open workspace and routed through the typed session port when a
workspace exists. The existing viewer zoom limits and local key fallback remain intact. Focused
frame/session/viewer validation passed (`86 passed`), the real offscreen command/shortcut suite
passed (`7 passed`), and the full suite passed (`1351 passed, 20 skipped, 1 warning`). The bounded
launch audit exited with the known `SingleInstanceUnavailable` local-socket limitation and left no
process or temporary-root debris.

## Context and Orientation

`AppFrameCommandId` and the command-definition tuples in
`src/foliaseal/presentation/qt/app_frame_command_model.py` are the single registry for top-level
menu metadata. `FoliaSealAppFrame._install_menus()` creates Qt actions from that registry and
`_apply_workspace_action_state()` controls document-dependent enablement. The frame calls
`SigningWorkspaceSessionPort`, whose Qt adapter delegates to `SigningWorkspace` and then the
existing `ViewerWidget`. `ViewerWorkflow.zoom_in()`, `zoom_out()`, and `reset_zoom()` already clamp
the semantic zoom to the configured 10%–800% range; this slice only makes those capabilities
truthfully reachable from the frame command surface.

## Change Slice

Primary change class: behavior change with focused tests and minimum architecture/status updates.
Allowed files are the command registry, app-frame action construction/state routing, session/shell
ports, focused command/frame/session tests, this plan, `docs/ARCHITECTURE.md`, and the V1 parent
status. Do not alter zoom math, PDF rendering, search, fit algorithms, or unrelated menu families.

## Plan of Work

Add three stable `AppFrameCommandId` values and definitions under View. Use `Ctrl++` and `Ctrl+-`
for incremental zoom and no shortcut for Reset Zoom to avoid colliding with the existing Fit Page
`Ctrl+0` action. Add the three session-port protocol methods and Qt adapter delegates, then add
frame callbacks and action fields. Enable all three only when a workspace is open; preserve the
existing page-local viewer key fallback and verify that action triggers call the public session port
exactly once. Update architecture/status prose to describe the command surface and leave Back/
Forward, Signing, Help, and remaining Edit actions to their owning children.

## Milestones

Milestone 1 adds red pure registry and fake-session tests. Milestone 2 wires the frame and ports and
turns the tests green. Milestone 3 exercises the real offscreen action/menu path, runs the full
suite, performs compliance review, updates living plans, and commits the complete slice.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    .venv/bin/pytest -q tests/unit/test_qt_app_frame.py tests/unit/test_signing_workspace_session_port.py tests/unit/test_qt_viewer_widget.py tests/integration/test_view_navigation_shortcuts.py
    .venv/bin/ruff check src tests
    .venv/bin/pytest -q
    git diff --check

Run the bounded GUI lifecycle audit with owned temporary state:

    audit_root=$(mktemp -d /tmp/foliaseal-zoom-audit-XXXXXX)
    timeout --foreground 30s env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf || test "$?" -eq 124
    ps -eo pid,cmd | rg 'FoliaSeal|foliaseal|PySide6|pytest' | rg -v 'rg ' || true
    rm -rf "$audit_root"
    test ! -e "$audit_root"

The expected bounded-launch limitation is `SingleInstanceUnavailable` when the isolated local
socket cannot be claimed. It is not GUI success; real offscreen Qt tests are the authoritative
action evidence. Never leave FoliaSeal, PySide6, pytest, or temporary audit processes running.

## Validation and Acceptance

Acceptance is behavioral: View exposes Zoom In and Zoom Out with conventional shortcuts and Reset
Zoom as a real menu action; all three are disabled without a document and enabled with one; each
action routes once through the typed session port and preserves the viewer's clamped exact zoom
behavior. Existing Fit Page/Fit Width, navigation, search, and text-selection tests remain green.

## Idempotence and Recovery

The changes are additive and safe to rerun. If a shortcut collides with an existing action, keep the
existing Fit Page binding authoritative and remove only the conflicting new shortcut, documenting
the result in the Decision Log. Clean only the temporary audit root created by this plan.

## Artifacts and Notes

Do not commit generated PDFs, keys, screenshots containing private data, or local absolute paths.

Evidence Record (2026-08-10):

- `.venv/bin/pytest -q tests/unit/test_qt_app_frame.py tests/unit/test_signing_workspace_session_port.py tests/unit/test_qt_viewer_widget.py` — `86 passed`.
- `.venv/bin/pytest -q tests/integration/test_view_navigation_shortcuts.py` — `7 passed`, including a real Qt `Ctrl++` test proving the action and viewer-local fallback do not double-dispatch.
- `.venv/bin/pytest -q` — `1351 passed, 20 skipped, 1 warning`; Ruff and `git diff --check` passed.
- Bounded launch used an isolated XDG root, exited `1` with `SingleInstanceUnavailable`, found no FoliaSeal/PySide6/pytest processes afterward, and removed the audit root.
- Compliance review found no functional or architectural defect; the plan's command path and evidence record were corrected before commit.

## Interfaces and Dependencies

The final public interface includes `zoom_in_view()`, `zoom_out_view()`, and `reset_zoom_view()` on
`SigningWorkspaceSessionPort` and `QtSigningWorkspaceSessionPort`. The frame owns QAction creation;
the shell owns viewer delegation; `ViewerWorkflow` remains the sole zoom policy authority. No Qt
types may cross into application/domain modules.

Revision note: 2026-08-10 / Codex. Created after the viewer command-surface audit found that zoom
math and local key behavior were complete but the normative frame command registry lacked typed
zoom actions.

Revision note: 2026-08-10 / Codex. Marked implementation and validation complete after the
compliance review, corrected the focused command path to use the existing app-frame test module,
and added real offscreen shortcut evidence for single-dispatch behavior.
