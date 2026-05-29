# Introduce An Explicit App-Frame Shell Port

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with [`.agents/skills/write-execplan/PLANS.md`](/home/daekar/FoliaSeal/.agents/skills/write-execplan/PLANS.md).

## Purpose / Big Picture

After this slice, the FoliaSeal app frame will no longer construct and manage the signing shell through an untyped `shell_builder(**kwargs)` callback plus `getattr(...)` reach-ins for `choose_output_pdf_path()`, `apply_app_settings()`, and `refresh_certificate_configurations()`. Instead, the app frame will depend on one explicit local contract: a shell factory creates a shell port from a typed bootstrap object, and the app frame uses that port for `Save As...`, live settings propagation, and certificate refresh.

This is observable in two ways. First, the user-visible GUI behavior stays the same: opening a PDF still loads the signing workspace, `File > Save As...` still routes to the active shell, application settings still propagate into the active workspace, and certificate create/import/manage still refresh the active certificate selector. Second, the app-frame tests stop depending on raw shell duck typing and instead exercise a narrower fake shell port boundary.

## Child ExecPlan Dependencies

- [x] (2026-05-29 01:57Z) No child ExecPlans are required for this bounded migration slice.

## Progress

- [x] (2026-05-29 01:57Z) Reviewed `src/foliaseal/presentation/qt/app_frame.py`, `tests/unit/test_qt_app_frame.py`, and `docs/ARCHITECTURE.md` to confirm that the app frame still owns shell bootstrap and reaches back into the live shell through `getattr(...)`.
- [x] (2026-05-29 01:57Z) Wrote this ExecPlan and fixed the slice boundary at: explicit shell port/factory types, app-frame migration, focused test migration, and documentation updates only.
- [x] (2026-05-29 02:02Z) Added `AppFrameShellBootstrap`, `AppFrameShellPort`, `AppFrameShellFactory`, `QtSigningShellPort`, and `QtSigningShellFactory` in `src/foliaseal/presentation/qt/app_frame.py`.
- [x] (2026-05-29 02:02Z) Migrated `FoliaSealAppFrame`, `QtAppFrameAdapter`, `build_qt_app_frame(...)`, and `launch_qt_app_frame(...)` to the explicit port/factory contract.
- [x] (2026-05-29 02:02Z) Replaced fake-shell builder tests with fake shell-port/factory tests in `tests/unit/test_qt_app_frame.py`.
- [x] (2026-05-29 02:02Z) Ran focused validation with `pytest`, `ruff check`, and `git diff --check`.
- [x] (2026-05-29 02:02Z) Ran the required compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and `docs/SCHEMAS.md`; the only gap was that the adapter/top-level constructors had not yet threaded through `shell_factory`, so that was added and revalidated.
- [x] (2026-05-29 02:02Z) Updated documentation, including this ExecPlan, to final state.
- [x] (2026-05-29 02:02Z) Committed the slice as one narrow architecture change.

## Surprises & Discoveries

- Observation: `FoliaSealAppFrame` currently exposes both private and window-level shell state at the same time: `_current_shell` and `window.current_shell`.
  Evidence: `src/foliaseal/presentation/qt/app_frame.py` sets both fields in `open_pdf_path()` and then uses `_current_shell` for `Save As...`, settings propagation, and certificate refresh.

- Observation: the current tests are already shaped around the desired contract; they just express it through a raw `_FakeShell`.
  Evidence: `tests/unit/test_qt_app_frame.py` only needs four app-frame shell behaviors in practice: central-widget identity, `choose_output_pdf_path()`, `apply_app_settings()`, and `refresh_certificate_configurations()`.

- Observation: threading the explicit shell factory only through `FoliaSealAppFrame` left the boundary half-internal.
  Evidence: the first green implementation still left `QtAppFrameAdapter.create()`, `QtAppFrameAdapter.launch()`, `build_qt_app_frame(...)`, and `launch_qt_app_frame(...)` without a `shell_factory` parameter, so the compliance pass widened the same slice slightly to keep the contract coherent end to end.

## Decision Log

- Decision: keep this slice behavior-preserving and local to the app-frame/shell seam.
  Rationale: the user asked to continue the proposed hybrid, and the strongest architecture win here is replacing duck typing with an explicit contract, not redesigning window lifecycle or GUI behavior in the same change.
  Date/Author: 2026-05-29 / Codex

- Decision: keep `window.current_shell` pointed at the concrete shell widget even after the app frame starts depending on a shell port.
  Rationale: the app frame should stop using widget duck typing internally, but tests and debug affordances still benefit from a window-level reference to the actual active widget. That keeps the migration narrow without preserving the old internal dependency.
  Date/Author: 2026-05-29 / Codex

- Decision: keep `build_qt_signing_shell(...)` as the concrete shell constructor and wrap it behind a small factory/port adapter for this slice.
  Rationale: the current signing shell already exposes the required behavior. Wrapping it behind an explicit port deepens the app-frame seam without dragging `signing_shell.py` into a larger redesign.
  Date/Author: 2026-05-29 / Codex

## Outcomes & Retrospective

This slice is complete.

Implemented results:

- `FoliaSealAppFrame` no longer accepts or stores a raw `shell_builder`; it depends on `AppFrameShellFactory` and stores a private `AppFrameShellPort`.
- `open_pdf_path()` now builds an `AppFrameShellBootstrap`, creates a port through `QtSigningShellFactory`, installs the concrete widget from `port.widget()`, and still returns the concrete shell widget for callback continuity.
- `_choose_save_as()`, `_apply_app_settings()`, and `_refresh_shell_certificate_configurations()` no longer use `getattr(...)`; they call explicit shell-port methods.
- `QtAppFrameAdapter.create()`, `QtAppFrameAdapter.launch()`, `build_qt_app_frame(...)`, and `launch_qt_app_frame(...)` now all accept the same optional `shell_factory` seam.
- `tests/unit/test_qt_app_frame.py` now proves the app-frame boundary through `_FakeShellFactory` and `_FakeShellPort` rather than a raw callback builder.

Validation evidence:

- `pytest tests/unit/test_qt_app_frame.py tests/unit/test_main_cli.py` passed with `44 passed`.
- `ruff check src/foliaseal/presentation/qt/app_frame.py tests/unit/test_qt_app_frame.py tests/unit/test_main_cli.py` passed.
- `git diff --check` passed.

Retrospective:

- The main correction came from the compliance review, not from failing tests. The first implementation was behaviorally correct but stopped the new seam too low in the stack.
- Keeping `window.current_shell` as the concrete widget while moving the frame’s internal dependency to an explicit port was the right compromise for this slice. It removed the duck typing without forcing unrelated window/test rewrites.

## Context and Orientation

The production code for this seam lives in [src/foliaseal/presentation/qt/app_frame.py](/home/daekar/FoliaSeal/src/foliaseal/presentation/qt/app_frame.py). `FoliaSealAppFrame` owns the top-level `QMainWindow`, the menu actions, and the transition from “placeholder window” to “active signing workspace”. When `open_pdf_path()` runs, it loads the PDF page count, constructs a `ViewerWorkflow`, constructs a `SigningDraftWorkflow`, builds an `AppFrameShellBootstrap`, asks an `AppFrameShellFactory` for a shell port, sets the resulting concrete shell widget as the central widget, and enables `File > Save As...`.

The important current split is:

- `AppFrameShellBootstrap` defines everything the factory needs to create one workspace.
- `AppFrameShellPort` defines everything the app frame is allowed to do with a loaded workspace after creation.
- `QtSigningShellFactory` and `QtSigningShellPort` adapt the existing `build_qt_signing_shell(...)` implementation to that contract.

The relevant tests are in [tests/unit/test_qt_app_frame.py](/home/daekar/FoliaSeal/tests/unit/test_qt_app_frame.py). They now pass a `_FakeShellFactory` into `FoliaSealAppFrame`, assert that the bootstrap object contains the expected workflows/settings/callbacks, and prove that `Save As...`, settings propagation, and certificate refresh route through the explicit fake shell port.

This slice does not redesign the signing shell. It only deepens the app-frame boundary. The signing shell remains responsible for its own internal behavior; the app frame now owns a narrower, typed way to bootstrap and talk to it.

## Plan of Work

First, add the explicit contract types. Define a typed bootstrap object that contains the workflows, settings, catalog stores, secret provider, executor, and callbacks required to create a signing workspace for one PDF. Define a shell port protocol that exposes exactly the app-frame behaviors needed after creation:

- `widget()` to return the concrete central widget
- `choose_output_pdf_path()` for `File > Save As...`
- `apply_app_settings(settings)` for live settings propagation
- `refresh_certificate_configurations()` for post-lifecycle selector refresh

Define a shell factory protocol that accepts the bootstrap object and returns the shell port.

Second, add the production adapter. The simplest safe implementation is a small wrapper around the existing `build_qt_signing_shell(...)` result. The wrapper should hold the real shell widget and implement the shell port by forwarding those three shell methods plus `widget()`. The production factory should create that wrapper from the bootstrap object.

Third, migrate the app frame. Replace `shell_builder` with `shell_factory` in `FoliaSealAppFrame` and thread that through `QtAppFrameAdapter`, `build_qt_app_frame(...)`, and `launch_qt_app_frame(...)` as needed for tests and production wiring. `open_pdf_path()` should build an `AppFrameShellBootstrap`, ask the factory for a port, store the port privately, store the concrete widget on `window.current_shell`, set the central widget from `port.widget()`, and keep the existing `window.current_viewer_workflow` and `window.current_signing_workflow` behavior. `_choose_save_as()`, `_apply_app_settings()`, and `_refresh_shell_certificate_configurations()` should then call the explicit shell-port methods directly.

Fourth, update the tests. Replace `_FakeShell`-through-`shell_builder` setup with a fake shell port plus fake shell factory. Keep the current behavior checks, but make them prove the explicit contract instead of implicit duck typing. Do not widen the tests into signing-shell internals.

Finally, run focused validation and update `docs/ARCHITECTURE.md` so it describes the app frame as depending on an explicit shell factory/port boundary rather than directly managing a shell widget API.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Edit the app-frame implementation and tests.

       apply_patch ... on src/foliaseal/presentation/qt/app_frame.py
       apply_patch ... on tests/unit/test_qt_app_frame.py

2. Run focused validation. Completed.

       pytest tests/unit/test_qt_app_frame.py tests/unit/test_main_cli.py
       ruff check src/foliaseal/presentation/qt/app_frame.py tests/unit/test_qt_app_frame.py tests/unit/test_main_cli.py
       git diff --check

3. Run the required compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and `docs/SCHEMAS.md`. Completed. The review found that `shell_factory` had not been threaded through `QtAppFrameAdapter` and the top-level build/launch helpers, so that was added and the focused validation commands were rerun.

4. Update documentation and this ExecPlan to final state, then commit the slice.

## Validation and Acceptance

This slice is accepted when all of the following are true:

- opening a PDF still loads the signing workspace and enables `File > Save As...`
- `File > Save As...` still routes to the active shell workspace through the new port
- application settings still propagate into the active shell workspace
- certificate create/import/manage still refresh the active shell workspace when one is loaded
- reopen-after-signing still routes back through `open_pdf_path()`
- `tests/unit/test_qt_app_frame.py` exercises the fake shell dependency through the explicit port/factory contract instead of a raw `shell_builder`
- `docs/ARCHITECTURE.md` describes the new app-frame shell boundary accurately

Run:

    pytest tests/unit/test_qt_app_frame.py tests/unit/test_main_cli.py

Then run:

    ruff check src/foliaseal/presentation/qt/app_frame.py tests/unit/test_qt_app_frame.py tests/unit/test_main_cli.py
    git diff --check

Acceptance is behavioral. There is no intended CLI or GUI flow change in this slice.

## Idempotence and Recovery

This is a behavior-preserving refactor in local Qt presentation code. It is safe to retry. If the port migration breaks too many tests at once, keep the explicit types and restore one call site at a time behind the port until `test_qt_app_frame.py` is green again. Do not reintroduce `getattr(...)` reach-ins as the recovery path; if a required shell behavior is missing, add it explicitly to the port and fake implementations.

## Artifacts and Notes

Validation transcript from this slice:

    $ pytest tests/unit/test_qt_app_frame.py tests/unit/test_main_cli.py
    ============================= test session starts ==============================
    ...
    ============================== 44 passed in 0.51s ==============================

    $ ruff check src/foliaseal/presentation/qt/app_frame.py tests/unit/test_qt_app_frame.py tests/unit/test_main_cli.py
    All checks passed!

    $ git diff --check
    <no output>

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

At the end of this slice, the app-frame seam should look approximately like:

    @dataclass(frozen=True)
    class AppFrameShellBootstrap:
        viewer_workflow: ViewerWorkflow
        signing_workflow: SigningDraftWorkflow
        app_settings: AppSettings
        app_settings_store: AppSettingsStore | None = None
        certificate_catalog_store: CertificateCatalogStore | None = None
        certificate_secret_provider: CertificateSecretProvider | None = None
        preset_catalog_store: SignaturePresetCatalogStore | None = None
        sign_executor: SigningRequestExecutor | None = None
        on_sign_request: Callable[[SigningRequest], None] | None = None
        on_open_signed_output: Callable[[str | Path], Any | None] | None = None
        on_error: Callable[[str], None] | None = None
        on_status_change: Callable[[str], None] | None = None

    class AppFrameShellPort(Protocol):
        def widget(self) -> Any: ...
        def choose_output_pdf_path(self) -> str | None: ...
        def apply_app_settings(self, settings: AppSettings) -> None: ...
        def refresh_certificate_configurations(self) -> None: ...

    class AppFrameShellFactory(Protocol):
        def create(self, bootstrap: AppFrameShellBootstrap) -> AppFrameShellPort: ...

The exact helper type names may shift, but the shape must remain explicit. `FoliaSealAppFrame` should depend on the shell port, not a raw widget or a generic callback.

Revision note: Created on 2026-05-29 by Codex for the first implementation slice of the app-frame/shell ports-and-adapters hybrid identified in the architecture pass.

Revision note: Updated on 2026-05-29 after implementation, validation, and compliance review to record the completed shell-port migration, the adapter/top-level `shell_factory` follow-up, and the final validation evidence.
