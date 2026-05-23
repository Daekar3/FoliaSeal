# Add a production GUI launch path

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with [.agents/skills/write-execplan/PLANS.md](/home/daekar/FoliaSeal/.agents/skills/write-execplan/PLANS.md).

## Purpose / Big Picture

After this slice, a developer or tester can launch the real FoliaSeal Qt application with a stable command instead of relying on the deprecated viewer/signing harnesses or constructing the app frame manually. The observable result is that `foliaseal gui` opens the real `QMainWindow`, optionally opens a supplied PDF immediately, and has a documented dependency/install path for GUI users.

## Child ExecPlan Dependencies

- [x] (2026-05-23 17:29Z) No child ExecPlans are required for this narrow slice.

## Progress

- [x] (2026-05-23 17:29Z) Gathered `explorer-light` findings for the current GUI-launch gap and identified the smallest useful slice.
- [x] (2026-05-23 17:29Z) Recorded the intended slice as a dedicated ExecPlan before continuing implementation.
- [x] (2026-05-23 17:40Z) Finished the Qt launch seam and CLI parser/dispatch integration, including real exit-code propagation and faithful process-argv forwarding on the `gui` path.
- [x] (2026-05-23 17:41Z) Added focused tests for parser, CLI dispatch, and `QApplication` launch behavior.
- [x] (2026-05-23 17:42Z) Added the `gui` optional dependency extra and updated user/developer launch documentation.
- [x] (2026-05-23 17:49Z) Ran focused validation, completed `docs/` compliance review, and updated the ExecPlan to final state.

## Surprises & Discoveries

- Observation: The current working tree already contains a partially landed GUI-launch implementation.
  Evidence: `src/foliaseal/__main__.py` already imported `launch_qt_app_frame`, and `src/foliaseal/presentation/qt/app_frame.py` already defined `QtAppFrameAdapter.launch()` and `launch_qt_app_frame()`, but tests and packaging/docs had not yet been brought along.

- Observation: The first implementation pass still dropped real CLI argv and the Qt exit code on the normal `gui` launch path.
  Evidence: Compliance review found that `main(argv=None)` forwarded `None` instead of the live process argv and returned `None` instead of the Qt event-loop result; this was corrected before closeout.

## Decision Log

- Decision: Keep the existing default `foliaseal` / `python -m foliaseal` behavior unchanged for this slice and introduce the production GUI launch as the explicit `gui` subcommand.
  Rationale: The repo already has stable harness/evidence commands and a legacy default message. Changing the no-arg default would be a separate CLI contract change. The explicit subcommand is enough to give the user a real launch path now without mixing in a broader CLI migration.
  Date/Author: 2026-05-23 / Codex

- Decision: Add a `gui` optional dependency extra rather than moving `PySide6` into the base runtime dependencies.
  Rationale: The real GUI now has a stable launch command, but the repo still has legitimate headless CLI and evidence workflows that do not require Qt. The extra creates a supportable install path without forcing desktop dependencies into every environment.
  Date/Author: 2026-05-23 / Codex

- Decision: Make `main()` return an integer status code and forward the real process argv to the GUI launcher.
  Rationale: A production launch command should preserve the Qt exit code and should reflect the actual invocation seen by the console-script wrapper rather than a synthetic fallback.
  Date/Author: 2026-05-23 / Codex

## Outcomes & Retrospective

This slice achieved the intended user-visible result: the repo now has a stable production launch command, `foliaseal gui`, for the real Qt app frame. The launch path creates or reuses `QApplication`, shows the real main window, optionally opens an initial PDF, and propagates the Qt event-loop exit code. The package metadata now includes a `gui` extra so the launch path is supportable without requiring the full dev toolchain. The main remaining gap is not launch anymore; it is broader desktop distribution and packaging.

## Context and Orientation

The top-level CLI entrypoint lives in `src/foliaseal/__main__.py`. It already owns argument parsing and dispatch for evidence-generation commands and Qt harness commands. The real top-level GUI wrapper lives in `src/foliaseal/presentation/qt/app_frame.py`. That module defines `FoliaSealAppFrame`, which is the real Qt main-window wrapper around the signing shell and settings/certificate dialogs. A “binding loader” in this repository means a function or object that imports PySide6 late at runtime rather than at module import time, so tests can replace Qt classes with fakes and environments without PySide6 get a clear error.

The current gap for this slice was not that the GUI was missing. The gap was that there was no fully validated, documented, supported command path for launching it as an application. The repo now carries a dedicated `gui` optional dependency group so a non-dev install can opt into the real Qt launch path.

The relevant files for this slice are:

- `src/foliaseal/__main__.py` for CLI parser/dispatch.
- `src/foliaseal/presentation/qt/app_frame.py` for `QApplication` bootstrap and initial-PDF open behavior.
- `src/foliaseal/presentation/qt/__init__.py` for presentation exports.
- `tests/unit/test_cli_parser.py` for parser expectations.
- `tests/unit/test_main_cli.py` for CLI dispatch behavior.
- `tests/unit/test_qt_app_frame.py` for direct launch/bootstrap behavior with fake Qt classes.
- `pyproject.toml` for optional dependency metadata.
- `README.md` and `docs/ARCHITECTURE.md` for user/developer-facing launch documentation and architectural status.

## Plan of Work

First, finish and normalize the Qt launch seam in `src/foliaseal/presentation/qt/app_frame.py`. The public helper must create or reuse `QApplication`, build the real `FoliaSealAppFrame`, show the window, optionally open an initial PDF, and return the event-loop exit code. Keep this behavior behind the existing late-import adapter so tests can drive it with fake Qt classes and so missing PySide6 still raises `QtAppFrameBindingsUnavailable`.

Second, make the CLI surface in `src/foliaseal/__main__.py` clean and intentional. The parser must expose `foliaseal gui [--pdf-path ...]`, and `main()` must dispatch that subcommand to `launch_qt_app_frame()` without disturbing the existing default no-arg behavior.

Third, add focused tests. `tests/unit/test_cli_parser.py` must prove the new `gui` parser accepts an optional `--pdf-path`. `tests/unit/test_main_cli.py` must prove the `gui` command dispatches the supplied `argv` and PDF path to the launcher. `tests/unit/test_qt_app_frame.py` must prove the adapter creates a `QApplication` when needed, reuses an existing one when present, shows the window, optionally opens a PDF, and returns the event-loop exit code.

Fourth, make the launch path supportable outside a dev-only install. The narrowest change is to add a `gui` optional dependency extra in `pyproject.toml` that includes `PySide6`, while leaving `dev` intact. Then update `README.md` so a user can install the GUI requirements and launch the real app with a single documented command, and update `docs/ARCHITECTURE.md` so it no longer describes GUI launcher packaging as completely open.

## Concrete Steps

From `/home/daekar/FoliaSeal`, implement and validate this slice with:

    pytest tests/unit/test_cli_parser.py tests/unit/test_main_cli.py tests/unit/test_qt_app_frame.py
    ruff check src/foliaseal/__main__.py src/foliaseal/presentation/qt/__init__.py src/foliaseal/presentation/qt/app_frame.py tests/unit/test_cli_parser.py tests/unit/test_main_cli.py tests/unit/test_qt_app_frame.py
    git diff --check

Observed result during implementation:

    pytest tests/unit/test_cli_parser.py tests/unit/test_main_cli.py tests/unit/test_qt_app_frame.py
    47 passed

    ruff check src/foliaseal/__main__.py src/foliaseal/presentation/qt/__init__.py src/foliaseal/presentation/qt/app_frame.py tests/unit/test_cli_parser.py tests/unit/test_main_cli.py tests/unit/test_qt_app_frame.py
    All checks passed!

For manual proof on a desktop session with Qt dependencies installed, the expected launch command will be:

    python -m pip install -e .[gui]
    foliaseal gui --pdf-path /path/to/example.pdf

Expected observable behavior: the real FoliaSeal main window appears, the chosen PDF opens immediately when `--pdf-path` is supplied, and the File/Settings menus are the same menus exercised by `tests/unit/test_qt_app_frame.py`.

## Validation and Acceptance

Acceptance is behavioral:

- `pytest tests/unit/test_cli_parser.py tests/unit/test_main_cli.py tests/unit/test_qt_app_frame.py` passes, and the new tests specifically prove the `gui` subcommand and the Qt launch lifecycle.
- `ruff check ...` passes on all touched production and test files.
- `git diff --check` passes so the slice is cleanly formatted.
- On a real desktop session with Qt available, `foliaseal gui` shows the actual GUI rather than a harness or a placeholder message.

## Idempotence and Recovery

The code and test steps are safe to repeat. If the launch helper fails because PySide6 is unavailable, the expected recovery path is to install the `gui` extra and retry. If a local desktop session lacks the required X11/Wayland Qt platform support, that is an environment problem rather than a repo-state problem; the CLI launch command should still be correct.

## Artifacts and Notes

Important pre-implementation evidence from the repo audit:

    python -m foliaseal
    FoliaSeal phase 0 skeleton ready

    python -m foliaseal phase2-evidence --check-qt-runtime
    ### Qt runtime readiness
    - ✅ PySide6 import available
    - ✅ PySide6.QtPdf import available

These showed that the real GUI dependencies existed in the current environment before the launch path was finalized.

Post-implementation runtime proof from this environment:

    python -m foliaseal gui --help
    usage: foliaseal gui [-h] [--pdf-path PDF_PATH]

    QT_QPA_PLATFORM=offscreen python -c "from PySide6.QtCore import QTimer; from PySide6.QtWidgets import QApplication; from foliaseal.presentation.qt.app_frame import launch_qt_app_frame; app = QApplication([]); QTimer.singleShot(0, app.quit); raise SystemExit(launch_qt_app_frame(argv=['foliaseal', 'gui']))"
    This plugin does not support propagateSizeHints()

The offscreen run exited successfully, which is enough to prove that the real launch path can bootstrap the GUI in this environment even though there is no interactive display server.

## Interfaces and Dependencies

At the end of this slice, the following public interfaces must exist and be exercised by tests:

- `foliaseal.__main__._build_parser()` must accept the `gui` subcommand with optional `--pdf-path`.
- `foliaseal.__main__.main(argv: Sequence[str] | None = None) -> int` must dispatch `gui` to `launch_qt_app_frame(argv=argv or sys.argv, initial_pdf_path=args.pdf_path)` and return the resulting exit code.
- `foliaseal.presentation.qt.app_frame.QtAppFrameAdapter.launch(...) -> int` must create or reuse `QApplication`, show the `FoliaSealAppFrame` window, optionally open an initial PDF, and return the Qt event-loop exit code.
- `foliaseal.presentation.qt.app_frame.launch_qt_app_frame(...) -> int` must remain the public helper used by the CLI.

Revision note: created on 2026-05-23 to capture the explicit GUI-launch slice that enables the real Qt app to be launched outside the deprecated harness workflows. Revised later the same day to record the completed implementation, the `gui` optional dependency extra, the exit-code/argv compliance fix, and the final validation evidence.
