# Extract app-frame workspace-open composition behind a narrow boundary

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, opening a PDF in the FoliaSeal app frame will still do exactly what it does now: create a signing workspace, install it as the main window's central widget, enable `File > Save As...`, and allow the shell to reopen signed output through the same top-level open path. The visible GUI behavior does not change.

The architectural win is that `src/foliaseal/presentation/qt/app_frame.py` will stop owning the whole workspace-open composition sequence itself. Instead, a new narrow boundary will own page-count loading, workflow construction, output-path defaulting, shell bootstrap assembly, and shell creation. The app frame will remain the `QMainWindow` owner and will keep compatibility writes such as `window.current_shell`, but it will no longer be the shallow module that knows every step of workspace assembly.

## Child ExecPlan Dependencies

- [x] (2026-06-07 18:10Z) `docs/ExecPlans/app_frame_shell_port_execplan.md` is complete and the explicit shell port is already stable.
- [x] (2026-06-07 18:10Z) `docs/ExecPlans/signing_workspace_shell_port_ownership_execplan.md` is complete and the shell-owned `SigningWorkspacePort` / `SigningWorkspaceFactory` seam already exists.
- [x] (2026-06-07 18:10Z) No child ExecPlan is required for this first tracer-bullet extraction.

## Progress

- [x] (2026-06-07 18:10Z) Re-read the live app-frame open path, the shell-port boundary, the focused app-frame tests, and the earlier app-frame/shell-port ExecPlans.
- [x] (2026-06-07 18:16Z) Ran the required `explorer-light` dev-loop exploration pass and fixed the slice boundary: extract only workspace-open composition; do not change post-open shell verbs, certificate dialogs, widget installation ownership, or compatibility writes.
- [x] (2026-06-07 18:22Z) Wrote this ExecPlan and fixed the implementation target at a one-method workspace-open service with internal page-count and composition adapters.
- [x] (2026-06-07 18:31Z) Added `src/foliaseal/presentation/qt/app_frame_workspace_open.py` with `OpenWorkspaceCommand`, `WorkspaceOpenPort`, `QtPdfPageCountLoader`, `SigningWorkspaceCompositionService`, and `WorkspaceOpenService`, then migrated `FoliaSealAppFrame.open_pdf_path()` to use that boundary.
- [x] (2026-06-07 18:34Z) Added focused boundary tests in `tests/unit/test_qt_app_frame_workspace_open.py` and narrowed the main app-frame success test so it proves installation and compatibility state rather than bootstrap details.
- [x] (2026-06-07 18:35Z) Ran focused validation with `.venv/bin/python -m pytest -q tests/unit/test_qt_app_frame_workspace_open.py tests/unit/test_qt_app_frame.py`, `.venv/bin/python -m ruff check ...`, and `git diff --check`; all passed.
- [x] (2026-06-07 18:39Z) Reconciled `docs/ARCHITECTURE.md` and this ExecPlan to the implemented workspace-open boundary.
- [x] (2026-06-07 18:45Z) Ran the required architectural compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this ExecPlan through a fresh `explorer-light` pass; no findings were reported and no corrective iteration was required.
- [x] (2026-06-07 18:52Z) Updated documentation, created the git commit for the finished slice, and recorded the completed outcome here.

## Surprises & Discoveries

- Observation: the repo already has a stable shell-owned boundary for the live workspace after creation, but the frame still owns workspace-open composition itself.
  Evidence: `src/foliaseal/presentation/qt/signing_shell_port.py` already defines `SigningWorkspaceBootstrap`, `SigningWorkspacePort`, and `SigningWorkspaceFactory`, while `FoliaSealAppFrame.open_pdf_path()` still loads page count, creates both workflows, assembles the bootstrap, and creates the shell.

- Observation: the earlier shell-port slice already established that `window.current_shell` should remain concrete and that the frame should keep owning installation behavior.
  Evidence: `docs/ExecPlans/app_frame_shell_port_execplan.md` records the decision to keep `window.current_shell` concrete while moving the frame's internal dependency to the narrow port.

- Observation: the best first test move is not to delete app-frame tests, but to relocate bootstrap-detail assertions to the new owner.
  Evidence: the dev-loop exploration pass identified `tests/unit/test_qt_app_frame.py::test_app_frame_open_file_uses_settings_defaults_and_builds_signing_shell` and `::test_app_frame_reports_open_errors` as the main open-path facts that belong on the new owner.

- Observation: the one-method workspace-open boundary landed without widening the shell port or reopening certificate dialogs.
  Evidence: the focused validation commands passed immediately after introducing `app_frame_workspace_open.py`, and `src/foliaseal/presentation/qt/app_frame.py` now delegates only open-path composition while keeping `_choose_save_as()`, `_apply_app_settings()`, and `_refresh_shell_certificate_configurations()` unchanged.

## Decision Log

- Decision: keep this first hybrid slice limited to workspace-open composition and leave `QMainWindow` installation, compatibility writes, and the existing shell port untouched.
  Rationale: those post-open behaviors are already stabilized by earlier ExecPlans. Reopening them would turn a narrow architecture extraction into a broader UI migration.
  Date/Author: 2026-06-07 / Codex

- Decision: use one public app-frame-facing method, `open_workspace(command) -> outcome`, but allow the implementation to split page-count loading from workspace composition internally.
  Rationale: this preserves the strongest part of the proposed hybrid design. The caller sees one deep module, while the implementation can still isolate the two main local-substitutable responsibilities.
  Date/Author: 2026-06-07 / Codex

- Decision: keep the new boundary in the Qt presentation layer rather than moving it into `application/`.
  Rationale: this code still depends on Qt PDF document loading, render-backend factory wiring, and the shell-owned workspace factory. It is presentation orchestration, not business logic.
  Date/Author: 2026-06-07 / Codex

## Outcomes & Retrospective

The implementation and compliance work are complete. The slice added a new `app_frame_workspace_open.py` boundary, reduced `FoliaSealAppFrame.open_pdf_path()` to a thin install wrapper, moved bootstrap-detail assertions into a dedicated test module, updated `docs/ARCHITECTURE.md` to the new ownership split, and was committed as one narrow tracer bullet.

The slice stayed narrow exactly as intended: no shell-port expansion, no certificate-dialog migration, and no `QMainWindow` installation logic moved out of the frame. The code, tests, docs, and ExecPlan now all describe the same ownership split.

## Context and Orientation

The top-level Qt application frame lives in `src/foliaseal/presentation/qt/app_frame.py`. `FoliaSealAppFrame` owns the real `QMainWindow`, menu installation, the placeholder label shown before a PDF is open, and the forwarding methods that act on the current shell after one is loaded. The method `open_pdf_path()` currently does too much in one place: it loads the page count through a Qt PDF document object, creates a `ViewerWorkflow`, creates a `SigningDraftWorkflow`, seeds the default output path with `suggest_signed_output_path(...)`, assembles `SigningWorkspaceBootstrap`, creates the shell through `SigningWorkspaceFactory`, then installs the widget and mirrors compatibility state onto the window.

The live workspace seam already exists in `src/foliaseal/presentation/qt/signing_shell_port.py`. In this repository, a “port” means a narrow interface that one module depends on instead of depending on a large concrete object. `SigningWorkspacePort` currently exposes only the live caller-facing shell verbs the frame needs after a workspace is created: `widget()`, `choose_output_pdf_path()`, `apply_app_settings(...)`, and `refresh_certificate_configurations()`. That seam is stable and must not widen in this slice.

The new work belongs in a new Qt presentation helper module that owns opening one workspace. The new boundary should accept the source PDF path, settings, stores, factories, and callbacks; it should return the created `SigningWorkspacePort`, the concrete widget, and the two workflows that the frame still mirrors onto `window.current_*` for compatibility. The frame must remain responsible for `window.setCentralWidget(...)`, save-as enablement, `window.current_shell`, `window.current_viewer_workflow`, `window.current_signing_workflow`, and all current post-open forwarding methods.

The relevant tests live in `tests/unit/test_qt_app_frame.py`. Today they prove both frame behavior and bootstrap internals through the same entrypoint. This slice should add a new focused test module for the workspace-open boundary itself and then leave only installation/error behavior in the app-frame tests. The current architecture description in `docs/ARCHITECTURE.md` must also be updated so the repo describes the new owner of workspace-open composition accurately.

## Plan of Work

First, add a new module under `src/foliaseal/presentation/qt/` for the workspace-open boundary. Define one public app-frame-facing command/result pair and one public port that exposes a single method, `open_workspace(...)`. Inside that module, define a small page-count port and a small composition port. The page-count adapter should be backed by the current Qt PDF document loading logic. The composition adapter should build `ViewerWorkflow`, `SigningDraftWorkflow`, and `SigningWorkspaceBootstrap`, call the existing `SigningWorkspaceFactory`, and package the result as a narrow outcome containing the live shell port plus explicit compatibility state.

Second, edit `src/foliaseal/presentation/qt/app_frame.py` so `FoliaSealAppFrame` constructs and stores the new workspace-open service from the existing bindings, stores, factories, and callbacks. `open_pdf_path()` should become a thin method: build the command, call `open_workspace(...)`, handle exceptions by reporting one error, then install the returned widget and mirror the returned compatibility state. The app frame must continue to own widget installation, `window.current_*` writes, and save-as enablement. The existing `_choose_save_as()`, `_apply_app_settings()`, and `_refresh_shell_certificate_configurations()` methods must remain unchanged except for using the same live `_current_shell_port` they already use.

Third, add focused tests for the new boundary in a new unit test module. Those tests must prove that page-count load failures raise, that the default output path is derived from `AppSettings.default_output_directory`, that the resulting bootstrap carries the reopen callback and the existing stores/settings, and that the boundary builds an outcome without mutating any frame state. Then trim the existing app-frame tests so the main success path proves open-dialog behavior, widget installation, save-as enablement, and compatibility writes, while the error-path test proves that failure still reports through `_emit_error(...)` and leaves `window.current_shell` unset.

Fourth, run focused validation, then update `docs/ARCHITECTURE.md` and this ExecPlan to describe the new boundary as the owner of workspace-open composition. The docs must explain that the frame still owns installation and compatibility writes while the new module owns page-count loading and workspace assembly.

Finally, run the required architectural compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and any nearby ExecPlans needed to confirm that the slice stayed narrow. If the review finds stale documentation or a boundary mismatch, fix only those issues inside this slice, rerun focused validation, and then create a commit that captures the finished tracer bullet. The compliance review completed successfully with no findings, and the finished slice was then committed without widening scope.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Add the new workspace-open boundary module and migrate `app_frame.py` to use it.

       apply_patch ... on src/foliaseal/presentation/qt/app_frame_workspace_open.py
       apply_patch ... on src/foliaseal/presentation/qt/app_frame.py

2. Add focused boundary tests and adjust the existing app-frame tests to match the new ownership.

       apply_patch ... on tests/unit/test_qt_app_frame_workspace_open.py
       apply_patch ... on tests/unit/test_qt_app_frame.py

3. Run focused validation for the new module and the app-frame path.

       .venv/bin/python -m pytest -q tests/unit/test_qt_app_frame_workspace_open.py tests/unit/test_qt_app_frame.py
       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/app_frame_workspace_open.py src/foliaseal/presentation/qt/app_frame.py tests/unit/test_qt_app_frame_workspace_open.py tests/unit/test_qt_app_frame.py
       git diff --check

4. Reconcile `docs/ARCHITECTURE.md` and this ExecPlan to the implemented boundary, then rerun the focused validation commands if any documentation-driven code or test changes were needed.

5. Run the architectural compliance review, then create a git commit for the finished slice.

## Validation and Acceptance

This slice is accepted when all of the following are true:

- opening a PDF still installs the signing workspace as the app frame's central widget and enables `File > Save As...`;
- `File > Save As...`, live settings propagation, and certificate refresh still route through the unchanged `SigningWorkspacePort` methods after a workspace is loaded;
- the new workspace-open boundary, not `FoliaSealAppFrame`, proves page-count failure handling, output-path defaulting, shell bootstrap callback wiring, and shell creation;
- `open_pdf_path()` becomes a thin wrapper around the new boundary plus frame-owned installation work;
- `window.current_shell`, `window.current_viewer_workflow`, and `window.current_signing_workflow` are still updated by the frame on success and remain unchanged on failure;
- `docs/ARCHITECTURE.md` describes the new boundary accurately.

Run:

    .venv/bin/python -m pytest -q tests/unit/test_qt_app_frame_workspace_open.py tests/unit/test_qt_app_frame.py

Then run:

    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/app_frame_workspace_open.py src/foliaseal/presentation/qt/app_frame.py tests/unit/test_qt_app_frame_workspace_open.py tests/unit/test_qt_app_frame.py
    git diff --check

Acceptance is behavioral. The user-visible GUI flow must not change in this slice.

## Idempotence and Recovery

This is a behavior-preserving extraction inside local Qt presentation code. It is safe to retry. If the new boundary causes a failure, keep the new module and move one construction step back at a time only long enough to identify the missing collaborator; do not delete the new boundary outright unless the worktree is being intentionally rolled back. If a focused test fails because the boundary still depends on frame-owned installation state, fix the boundary so it returns a richer outcome rather than letting it mutate `QMainWindow` directly.

If a compliance review finds that the new seam stopped too low, the allowed recovery within this slice is to thread the new dependency coherently through `FoliaSealAppFrame` and the top-level Qt app-frame builders. The forbidden recovery is to widen `SigningWorkspacePort` or move certificate-dialog orchestration into the same extraction.

## Artifacts and Notes

The most important final evidence for this slice will be:

- a new `src/foliaseal/presentation/qt/app_frame_workspace_open.py` module that owns page-count loading and workspace-open composition;
- a visibly smaller `FoliaSealAppFrame.open_pdf_path()` in `src/foliaseal/presentation/qt/app_frame.py`;
- a new focused unit test module for the workspace-open boundary;
- focused validation output showing the new tests and the existing app-frame tests still pass.

Compliance review outcome:

- no findings; the slice remained within the frozen spec and the declared ExecPlan boundary;
- no additional code or documentation follow-up was required after review.

Current validation transcript:

    $ .venv/bin/python -m pytest -q tests/unit/test_qt_app_frame_workspace_open.py tests/unit/test_qt_app_frame.py
    ............................
    28 passed in 0.74s

    $ .venv/bin/python -m ruff check src/foliaseal/presentation/qt/app_frame_workspace_open.py src/foliaseal/presentation/qt/app_frame.py tests/unit/test_qt_app_frame_workspace_open.py tests/unit/test_qt_app_frame.py
    All checks passed!

    $ git diff --check
    <no output>

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

At the end of this slice, the new public boundary should have this shape:

    @dataclass(frozen=True)
    class OpenWorkspaceCommand:
        source_pdf: Path
        app_settings: AppSettings
        app_settings_store: AppSettingsStore | None
        certificate_catalog_store: CertificateCatalogStore | None
        certificate_secret_provider: Any | None
        preset_catalog_store: SignaturePresetCatalogStore | None
        sign_executor: SigningRequestExecutor | None
        on_sign_request: Callable[[SigningRequest], None] | None
        reopen_target: Callable[[str | Path], Any | None]
        on_error: Callable[[str], None] | None
        on_status_change: Callable[[str], None] | None

    @dataclass(frozen=True)
    class WorkspaceCompatibilityState:
        shell_widget: Any
        viewer_workflow: ViewerWorkflow
        signing_workflow: SigningDraftWorkflow

    @dataclass(frozen=True)
    class OpenWorkspaceOutcome:
        shell_port: SigningWorkspacePort
        compatibility: WorkspaceCompatibilityState

    class WorkspaceOpenPort(Protocol):
        def open_workspace(self, command: OpenWorkspaceCommand) -> OpenWorkspaceOutcome: ...

Internally, the implementation may define:

    class PdfPageCountPort(Protocol):
        def load_page_count(self, pdf_path: Path) -> int: ...

    class WorkspaceCompositionPort(Protocol):
        def compose(...) -> OpenWorkspaceOutcome: ...

The app frame must depend only on `WorkspaceOpenPort` and the existing `SigningWorkspacePort`. It must not gain new shell verbs, and the new boundary must not own `QMainWindow` installation.

Revision note: Created on 2026-06-07 by Codex for the first `dev-loop` implementation slice of the app-frame workspace-open hybrid boundary.

Revision note: Updated on 2026-06-07 after implementation, focused validation, architecture reconciliation, compliance review, and final commit creation to record the completed slice.
