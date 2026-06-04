# Rehome The Signing Workspace Port Into The Shell Layer

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

This slice moved the signing workspace's typed bootstrap and caller-facing port out of `src/foliaseal/presentation/qt/app_frame.py` and into a shell-owned module. The user-visible GUI behavior stayed the same: opening a PDF still loads the workspace, `File > Save As...` still routes into the active workspace, live application settings still update the active shell, and certificate-management flows still refresh the active certificate selector.

The visible win is architectural rather than feature-facing. The app frame no longer defines the shell contract that it consumes. Instead, `app_frame.py` depends on a shell-owned module that exposes the stable bootstrap, port, and factory boundary for one signing workspace. That keeps the hybrid `4+5` direction honest: the app frame depends on a narrow workspace boundary, while the shell owns the details of how that boundary is constructed.

## Child ExecPlan Dependencies

- [x] (2026-06-04 01:59Z) No child ExecPlans are required for this bounded tracer-bullet slice.

## Progress

- [x] (2026-06-04 01:59Z) Re-read `src/foliaseal/presentation/qt/app_frame.py`, `src/foliaseal/presentation/qt/signing_shell.py`, `tests/unit/test_qt_app_frame.py`, and `docs/ARCHITECTURE.md` to confirm that the explicit shell port already exists but is still owned by `app_frame.py`.
- [x] (2026-06-04 01:59Z) Fixed the scope of this loop at a behavior-preserving ownership move: new shell-owned port module, app-frame import migration, focused test migration, and documentation reconciliation only.
- [x] (2026-06-04 02:03Z) Added `src/foliaseal/presentation/qt/signing_shell_port.py` with `SigningWorkspaceBootstrap`, `SigningWorkspacePort`, `SigningWorkspaceFactory`, `QtSigningWorkspacePort`, and `QtSigningWorkspaceFactory`, then migrated `app_frame.py` to consume the new shell-owned contract.
- [x] (2026-06-04 02:03Z) Updated `tests/unit/test_qt_app_frame.py` to import the shell-owned bootstrap and added a direct `QtSigningWorkspaceFactory` forwarding test.
- [x] (2026-06-04 02:03Z) Ran focused validation with `pytest tests/unit/test_qt_app_frame.py tests/unit/test_qt_signing_shell.py`, `ruff check`, and `git diff --check`; all passed.
- [x] (2026-06-04 02:07Z) Reconciled `docs/ARCHITECTURE.md` and this ExecPlan to the shell-owned workspace port boundary and current slice status, including the long-form Qt presentation description.
- [x] (2026-06-04 02:08Z) Completed the required architectural compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this ExecPlan. The first pass found stale architecture wording; the second pass confirmed the slice is compliant.
- [x] (2026-06-04 02:09Z) Committed the completed slice as `e9136e292` (`Move signing workspace port ownership into shell layer`).

## Surprises & Discoveries

- Observation: the repo already has an explicit shell port boundary, but it was introduced as an app-frame-local abstraction.
  Evidence: before this slice, `src/foliaseal/presentation/qt/app_frame.py` defined `AppFrameShellBootstrap`, `AppFrameShellPort`, `AppFrameShellFactory`, `QtSigningShellPort`, and `QtSigningShellFactory`.

- Observation: the tests already treat the app frame as depending on exactly four shell behaviors: widget installation, `choose_output_pdf_path()`, `apply_app_settings(...)`, and `refresh_certificate_configurations()`.
  Evidence: the fake shell in `tests/unit/test_qt_app_frame.py` only implements those methods, and the existing tests already pass through a fake factory.

## Decision Log

- Decision: keep this first hybrid slice mechanical and behavior-preserving.
  Rationale: the user asked for the first `dev-loop` on the recommended hybrid, and the safest tracer bullet is to move ownership of the existing boundary before attempting a deeper policy extraction inside `signing_shell.py`.
  Date/Author: 2026-06-04 / Codex

- Decision: rename the shell-contract types from app-frame-specific names to workspace-specific names as part of the move.
  Rationale: keeping `AppFrame...` names inside a shell-owned module would preserve the ownership confusion this slice exists to remove. Renaming now keeps the boundary aligned with the eventual hybrid surface while still remaining behavior-preserving.
  Date/Author: 2026-06-04 / Codex

## Outcomes & Retrospective

The shell-owned workspace port boundary is in place, validation passed, and the architecture docs now describe the moved ownership correctly. The compliance review found one real gap, which was stale long-form architecture wording; that was corrected without reopening the code slice. The slice is complete and committed.

## Context and Orientation

FoliaSeal’s Qt presentation layer lives under `src/foliaseal/presentation/qt/`. `app_frame.py` owns the top-level `QMainWindow` wrapper and menu actions. `signing_shell.py` owns the interactive signing workspace widget. The current code now has a typed seam between them, and that seam is defined on the shell-owned side: `signing_shell_port.py` defines the bootstrap object that describes one workspace, the port that exposes the live shell’s small callable surface, and the production factory that wraps `build_qt_signing_shell(...)`.

That means `app_frame.py` is now only the consumer of the shell boundary. The result is shallow ownership no longer being a problem: the shell does the real work and owns the shell contract, while the app frame depends on that narrow workspace seam without changing runtime behavior.

The files that matter for this slice are:

- `src/foliaseal/presentation/qt/signing_shell_port.py`, which defines the shell-owned workspace port/factory boundary.
- `src/foliaseal/presentation/qt/app_frame.py`, which consumes the port/factory boundary.
- `src/foliaseal/presentation/qt/signing_shell.py`, which exports `build_qt_signing_shell(...)` and the concrete signing shell behavior.
- `tests/unit/test_qt_app_frame.py`, which already uses a fake shell and fake factory to exercise the boundary.
- `docs/ARCHITECTURE.md`, which now describes the app frame as consuming the shell-owned workspace boundary.

In this repository, a “port” means a narrow interface that one module depends on instead of depending on a large concrete object. A “bootstrap” means a typed bundle of inputs required to construct one live workspace instance. A “factory” means an object with one `create(...)` method that takes the bootstrap and returns the port.

## Plan of Work

First, add a new shell-owned module at `src/foliaseal/presentation/qt/signing_shell_port.py`. Move the current bootstrap, port, and production factory definitions there, but rename them to `SigningWorkspaceBootstrap`, `SigningWorkspacePort`, `SigningWorkspaceFactory`, `QtSigningWorkspacePort`, and `QtSigningWorkspaceFactory`. Keep the implementation thin: the factory should continue to call `build_qt_signing_shell(...)`, and the port should continue to forward `widget()`, `choose_output_pdf_path()`, `apply_app_settings(...)`, and `refresh_certificate_configurations()` to the concrete shell widget.

Second, edit `src/foliaseal/presentation/qt/app_frame.py` so it imports these types from the new shell-owned module instead of defining them locally. `FoliaSealAppFrame`, `QtAppFrameAdapter`, `build_qt_app_frame(...)`, and `launch_qt_app_frame(...)` must all keep the current behavior while using the new type names. `window.current_shell` must remain the concrete widget, and `self._current_shell_port` must remain the live narrow port.

Third, update `tests/unit/test_qt_app_frame.py` to import the bootstrap type from the new module and to add one direct production-adapter proof for `QtSigningWorkspacePort` or `QtSigningWorkspaceFactory`. Keep the tests focused on the narrow contract; do not widen them into `signing_shell.py` internals.

Finally, update `docs/ARCHITECTURE.md` so the Qt presentation section accurately states that the signing shell owns the workspace bootstrap/port/factory seam and the app frame consumes it. Then run focused validation, perform the compliance review, and record the final result here.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Create the new shell-owned contract module and migrate `app_frame.py`.

       apply_patch ... on src/foliaseal/presentation/qt/signing_shell_port.py
       apply_patch ... on src/foliaseal/presentation/qt/app_frame.py

2. Update focused tests.

       apply_patch ... on tests/unit/test_qt_app_frame.py

3. Run focused validation.

       pytest tests/unit/test_qt_app_frame.py tests/unit/test_qt_signing_shell.py
       ruff check src/foliaseal/presentation/qt/signing_shell_port.py src/foliaseal/presentation/qt/app_frame.py tests/unit/test_qt_app_frame.py tests/unit/test_qt_signing_shell.py
       git diff --check

4. Review architectural compliance, then reconcile docs if needed.

5. Commit the completed slice.

## Validation and Acceptance

This slice is accepted when all of the following are true:

- opening a PDF still installs the signing workspace and enables `File > Save As...`
- `File > Save As...` still routes through the live workspace port
- application settings still propagate into the active workspace through the port
- certificate create/import/manage still refresh the live workspace certificate choices through the port
- `tests/unit/test_qt_app_frame.py` depends on the shell-owned workspace contract rather than on app-frame-local types
- `docs/ARCHITECTURE.md` accurately describes the moved boundary

Run:

    pytest tests/unit/test_qt_app_frame.py tests/unit/test_qt_signing_shell.py

Then run:

    ruff check src/foliaseal/presentation/qt/signing_shell_port.py src/foliaseal/presentation/qt/app_frame.py tests/unit/test_qt_app_frame.py tests/unit/test_qt_signing_shell.py
    git diff --check

Acceptance is behavioral. No GUI flow is supposed to change in this slice.

## Idempotence and Recovery

This is a behavior-preserving refactor in the Qt presentation layer. It is safe to retry. If the move introduces import-cycle problems, keep the new shell-owned module extremely thin and move only the type family plus the `build_qt_signing_shell(...)` wrapper there. Do not recover by copying the same definitions into both modules; the boundary must have one owner at the end of the slice.

If a test fails because it still imports the old app-frame-local type, fix the import site rather than re-exporting the old name unless doing so is required for compatibility in another active code path.

## Artifacts and Notes

The most important evidence for this slice will be:

- a new `src/foliaseal/presentation/qt/signing_shell_port.py` module containing the workspace contract
- a diff in `src/foliaseal/presentation/qt/app_frame.py` that removes local contract ownership and imports the shell-owned one
- focused test output proving the behavior stayed stable

Validation transcript:

    $ pytest tests/unit/test_qt_app_frame.py tests/unit/test_qt_signing_shell.py
    ============================= test session starts ==============================
    ...
    ============================= 115 passed in 10.59s =============================

    $ ruff check src/foliaseal/presentation/qt/signing_shell_port.py src/foliaseal/presentation/qt/app_frame.py tests/unit/test_qt_app_frame.py tests/unit/test_qt_signing_shell.py
    All checks passed!

    $ git diff --check
    <no output>

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

At the end of this slice, the shell-owned interface family should look like this:

    @dataclass(frozen=True)
    class SigningWorkspaceBootstrap:
        viewer_workflow: ViewerWorkflow
        signing_workflow: SigningDraftWorkflow
        app_settings: AppSettings
        app_settings_store: AppSettingsStore | None = None
        certificate_catalog_store: CertificateCatalogStore | None = None
        certificate_secret_provider: Any | None = None
        preset_catalog_store: SignaturePresetCatalogStore | None = None
        sign_executor: SigningRequestExecutor | None = None
        on_sign_request: Callable[[SigningRequest], None] | None = None
        on_open_signed_output: Callable[[str | Path], Any | None] | None = None
        on_error: Callable[[str], None] | None = None
        on_status_change: Callable[[str], None] | None = None

    class SigningWorkspacePort(Protocol):
        def widget(self) -> Any: ...
        def choose_output_pdf_path(self) -> str | None: ...
        def apply_app_settings(self, settings: AppSettings) -> None: ...
        def refresh_certificate_configurations(self) -> None: ...

    class SigningWorkspaceFactory(Protocol):
        def create(self, bootstrap: SigningWorkspaceBootstrap) -> SigningWorkspacePort: ...

    @dataclass(frozen=True)
    class QtSigningWorkspacePort:
        shell_widget: Any

    class QtSigningWorkspaceFactory:
        def create(self, bootstrap: SigningWorkspaceBootstrap) -> SigningWorkspacePort: ...

`app_frame.py` must consume these interfaces. It must no longer define the shell boundary itself.

Revision note: Created on 2026-06-04 by Codex for the first signing-workspace hybrid tracer bullet after the shell seam was re-ranked as the top remaining architecture target.
