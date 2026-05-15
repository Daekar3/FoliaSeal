# Signing Flow Summary Shell

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

FoliaSeal V1 needs a document-centric signing workflow that is explicitly staged: review the document, choose signing setup, place the visible signature, preview readiness, confirm signing, save, and verify. The current Qt signing shell already has most mechanics, but the UI reads as a flat control stack with a bare `Confirm and sign` button. After this change, the shell will show a read-only flow summary near the top of the signing workspace so a tester can see the current stage without reading developer notes.

This is a narrow behavior and UI-architecture slice for Brief F in `docs/ExecPlans/phase3_parallel_plan.md`. It must not redesign the full signing shell, change signing behavior, alter persisted schemas, modify preview rendering internals, or remove existing controls. No generated artifacts are allowed to be committed.

## Child ExecPlan Dependencies

- [x] V1 product requirements in `docs/SPEC.md` define an explicitly staged workflow: `Open -> Review -> Choose preset/certificate -> Place -> Preview readiness -> Sign -> Save -> Verify`.
- [x] Brief F in `docs/ExecPlans/phase3_parallel_plan.md` assigns the next product-facing Phase 3 wave to signing-flow UX architecture.
- [x] An explorer inspected the shell, app frame, viewer widget, and fake-Qt tests, and recommended a state-driven flow summary/header as the smallest useful slice.

## Progress

- [x] (2026-05-15T10:43Z) Started the dev-loop slice for Signing Flow UX Architecture.
- [x] (2026-05-15T10:43Z) Spawned an explorer to inspect the current shell and recommend a narrow implementation slice.
- [x] (2026-05-15T10:43Z) Reviewed `docs/SPEC.md`, Brief F, `signing_shell.py`, and the relevant fake-Qt tests.
- [x] (2026-05-15T10:44Z) Created this ExecPlan.
- [x] (2026-05-15T10:45Z) Added failing fake-Qt tests for a visible flow summary and state-driven stage changes.
- [x] (2026-05-15T10:46Z) Implemented a read-only flow summary in `SigningWorkspaceWidget` driven by existing draft/signing state.
- [x] (2026-05-15T10:47Z) Ran focused shell and app-frame tests plus lint successfully.
- [x] (2026-05-15T10:48Z) Updated README and architecture documentation to record the staged shell summary.
- [x] (2026-05-15T10:49Z) Ran the full Qt signing shell unit file successfully after touching shared workspace refresh paths.
- [ ] Commit the completed slice.
- [ ] Run post-commit architectural compliance review.

## Surprises & Discoveries

- Observation: the current fake-Qt test suite explicitly asserts the shell does not have a stage box.
  Evidence: `tests/unit/test_qt_signing_shell.py::test_signing_shell_uses_split_layout_without_stage_box` checks `not hasattr(widget._signing_workspace, "_flow_summary_box")`.

- Observation: the workspace already has stable state transition hooks.
  Evidence: `SigningWorkspaceWidget.refresh_viewer()`, `_handle_viewer_selection()`, `_handle_panel_change()`, `choose_output_pdf_path()`, and `submit_sign_request()` all converge through signing readiness/result state and can refresh a summary without inventing a new model.

- Observation: a successful signing run without an open-output callback still has a useful signed-output path for the summary.
  Evidence: `SigningWorkspaceWidget.submit_sign_request()` calls `_set_last_successful_output_path(request.output_pdf_path)` on success, while `_set_last_successful_output_path()` separately disables the `Open signed PDF` button when no callback exists.

## Decision Log

- Decision: add a read-only workspace-level flow summary instead of reorganizing the whole properties panel in this slice.
  Rationale: Brief F is large. A state-driven header creates an observable staged workflow signal while keeping the implementation reviewable and preserving all current mechanics.
  Date/Author: 2026-05-15 / Codex

- Decision: derive the stage from existing workflow state instead of adding a new persisted or UI-owned state machine.
  Rationale: The governing docs ask for legible stages, not another data model. Existing state already distinguishes review/place/preview/confirm/sign outcomes well enough for this first slice.
  Date/Author: 2026-05-15 / Codex

## Outcomes & Retrospective

This plan is in progress. Completion requires failing tests, a state-driven flow summary implementation, focused validation, commit, and post-commit compliance review.

## Context and Orientation

The relevant UI is in `src/foliaseal/presentation/qt/signing_shell.py`. `SigningWorkspaceWidget` owns the overall signing workspace: a PDF viewer on the left, a `SignaturePropertiesPanel` on the right, output/sign/open buttons below, and a result label. `SignaturePropertiesPanel` owns the detailed controls for certificate configuration, signature presets, appearance, visible fields, placement, preview, and validation.

The V1 spec says the main workflow should be explicitly staged and not rigid. In plain language, a user should know whether they are reviewing the PDF, choosing setup, placing the signature, checking readiness, signing, or reviewing the signed output. The current shell has the needed controls but no visible "you are here" marker. This slice adds that marker as a read-only summary at the workspace level.

## Plan of Work

First, update `tests/unit/test_qt_signing_shell.py`. Replace the old `test_signing_shell_uses_split_layout_without_stage_box` expectation with a test that asserts the workspace exposes a `flow_stage_label` and `flow_detail_label`, and that initial text directs the user to place a signature. Add a second focused test that emits a viewer selection and observes the stage advance to a preview/readiness state. If practical, extend an existing signing-success test to assert the summary reaches a signed/verify state after a successful executor result.

Second, update `src/foliaseal/presentation/qt/signing_shell.py`. Add a small dataclass such as `SigningFlowSummaryControls` with `container`, `stage_label`, and `detail_label`. Build it in `SigningWorkspaceWidget.__init__` before the viewer/properties row. The labels should use existing fake-Qt-friendly APIs only: `q_group_box`, `q_vbox_layout`, `q_label`, `setWordWrap`, and optional `setStyleSheet`.

Third, add helper methods on `SigningWorkspaceWidget`: `_build_flow_summary_controls()`, `_refresh_flow_summary()`, and `_flow_summary_text()`. The summary should be derived from existing state:

- if a successful signing result exists and an output path is available, show `Signed` with guidance to open or verify the signed PDF;
- else if the properties panel is ready to sign, show `Confirm/sign` with guidance to confirm the output path and sign;
- else if no signature rectangle exists, show `Place signature` with guidance to drag on the page or enter placement values;
- else show `Review preview` with guidance from the panel validation text.

Refresh the summary from `refresh_viewer()`, `_handle_viewer_selection()`, `_handle_panel_change()`, `choose_output_pdf_path()`, and `submit_sign_request()` after the underlying state changes. Expose `flow_stage_label` and `flow_detail_label` on `self.widget` for focused fake-Qt tests.

Fourth, run focused tests and lint. Update this ExecPlan with validation transcripts and any discoveries.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

After adding tests but before implementation, run the focused shell tests and confirm the new assertions fail:

    .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py::test_signing_shell_shows_state_driven_flow_summary tests/unit/test_qt_signing_shell.py::test_signing_shell_flow_summary_advances_after_signature_placement

After implementation, run:

    .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py::test_signing_shell_shows_state_driven_flow_summary tests/unit/test_qt_signing_shell.py::test_signing_shell_flow_summary_advances_after_signature_placement tests/unit/test_qt_signing_shell.py::test_signing_shell_selection_updates_request tests/unit/test_qt_signing_shell.py::test_signing_shell_page_selection_and_resize_controls_update_workflow tests/unit/test_qt_signing_shell.py::test_signing_shell_executes_real_sign_flow_when_executor_is_supplied
    .venv/bin/pytest -q tests/unit/test_qt_app_frame.py::test_app_frame_open_file_uses_settings_defaults_and_builds_signing_shell
    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py

Expected final result: all focused tests pass and ruff reports `All checks passed!`.

## Validation and Acceptance

Acceptance is met when a fake-Qt tester can build the signing shell and inspect the exposed labels to see the current stage. Initially, the summary should guide placement. After a viewer selection creates a signature rectangle, the summary should move to preview/readiness or confirm/sign depending on validation state. After successful signing, the summary should mention signed output and verification. Existing selection, placement, signing, and app-frame shell construction tests must still pass.

This slice does not claim full V1 flow completion. It is the first observable Brief F step that makes the existing shell staged.

## Idempotence and Recovery

The tests use fake Qt bindings and temporary paths, so they are safe to rerun. If the stage wording needs adjustment, update the tests to assert stable stage names rather than brittle full sentences. Do not stage ignored caches, generated artifacts, or unrelated docs.

## Artifacts and Notes

Validation transcripts will be recorded here as work proceeds.

Red focused tests before implementation:

    .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py::test_signing_shell_shows_state_driven_flow_summary tests/unit/test_qt_signing_shell.py::test_signing_shell_flow_summary_advances_after_signature_placement
    FF                                                                       [100%]
    AttributeError: '_FakeWidget' object has no attribute 'flow_stage_label'

Focused shell tests and lint after implementation:

    .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py::test_signing_shell_shows_state_driven_flow_summary tests/unit/test_qt_signing_shell.py::test_signing_shell_flow_summary_advances_after_signature_placement tests/unit/test_qt_signing_shell.py::test_signing_shell_executes_real_sign_flow_when_executor_is_supplied
    ...                                                                      [100%]
    3 passed in 2.68s

    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py
    All checks passed!

Focused shell/app-frame regression set after docs update:

    .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py::test_signing_shell_shows_state_driven_flow_summary tests/unit/test_qt_signing_shell.py::test_signing_shell_flow_summary_advances_after_signature_placement tests/unit/test_qt_signing_shell.py::test_signing_shell_selection_updates_request tests/unit/test_qt_signing_shell.py::test_signing_shell_page_selection_and_resize_controls_update_workflow tests/unit/test_qt_signing_shell.py::test_signing_shell_executes_real_sign_flow_when_executor_is_supplied tests/unit/test_qt_app_frame.py::test_app_frame_open_file_uses_settings_defaults_and_builds_signing_shell
    ......                                                                   [100%]
    6 passed in 4.21s

Full Qt signing shell unit file:

    .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py
    ..................................................................       [100%]
    66 passed in 26.43s

## Interfaces and Dependencies

The implementation stays in `src/foliaseal/presentation/qt/signing_shell.py`. It should not change the signatures of `build_qt_signing_shell()`, `SigningWorkspaceWidget`, `SignaturePropertiesPanel`, or application-layer workflow classes. The new summary uses only existing Qt binding primitives already represented in `QtSigningWidgetBindings`.

The tests stay in `tests/unit/test_qt_signing_shell.py` and should use the existing fake bindings, `_FakeViewerWidget`, `_workflow()`, and `_viewer_workflow()` helpers.

Revision note: Created 2026-05-15 by Codex to implement the first Signing Flow UX Architecture slice from Brief F.

Revision note: Updated 2026-05-15 by Codex after adding the flow summary implementation, focused tests, and durable documentation updates.
