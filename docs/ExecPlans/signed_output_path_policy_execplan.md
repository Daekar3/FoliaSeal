# Signed Output Path Policy

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this change, FoliaSeal will choose the suggested signed PDF output path through one small application-layer helper instead of duplicating the rule in Qt widgets. When a user opens `contract.pdf`, a new signing draft should still default to `contract-signed.pdf` under the configured output directory. When the user later opens the shell save dialog, the dialog should still start in the configured output directory while reusing the current output filename. The user-visible behavior is intentionally unchanged; the architectural improvement is that path policy becomes testable without constructing Qt widgets.

In this plan, "path policy" means the rule for turning an input PDF path, default output directory, and optional existing output filename into a suggested signed-output file path. It is not the file dialog itself and it is not responsible for writing PDFs.

## Child ExecPlan Dependencies

- [x] The Qt app frame exists and creates `SigningDraftWorkflow` when a PDF is opened.
- [x] The Qt signing shell exists and has `choose_output_pdf_path()` for picking a signed PDF destination.
- [x] The architecture exploration identified signing-shell orchestration as a high-leverage area; the required dev-loop explorer narrowed this slice to duplicated signed-output path policy.

## Progress

- [x] (2026-05-13T10:59Z) Reviewed `src/foliaseal/presentation/qt/signing_shell.py`, `src/foliaseal/presentation/qt/app_frame.py`, related tests, and architecture docs.
- [x] (2026-05-13T10:59Z) Created this ExecPlan for the signed-output path policy extraction.
- [x] (2026-05-13T11:02Z) Added focused application-layer tests for signed-output path suggestions.
- [x] (2026-05-13T11:02Z) Implemented the application helper and exported it from `foliaseal.application`.
- [x] (2026-05-13T11:02Z) Migrated the Qt app frame and signing shell to use the helper.
- [x] (2026-05-13T11:03Z) Updated architecture documentation to describe the shared path policy and reduced Qt ownership.
- [x] (2026-05-13T11:07Z) Ran full validation successfully.
- [ ] Commit the completed slice.

## Surprises & Discoveries

- Observation: The signed-output default is duplicated in two Qt entry points.
  Evidence: `FoliaSealAppFrame.open_pdf_path()` computes `Path(default_output_directory) / f"{source_path.stem}-signed.pdf"` when creating a draft. `SigningWorkspaceWidget._default_output_dialog_path()` computes a related rule using either the current output filename or the input stem.

- Observation: The duplicated rule is pure path computation, not widget behavior.
  Evidence: The rule only needs three values: an input PDF path, a default output directory, and sometimes an existing output path. It does not need Qt bindings, the viewer, a signing executor, or the certificate/preset controls.

- Observation: A hidden dotfile-like input name is not the same as an empty stem in Python's `pathlib`.
  Evidence: The first fallback test used `.pdf` and failed because `Path(".pdf").stem` is `.pdf`, matching the old implementation. The fallback case is a genuinely empty input path such as `""`.

- Observation: Focused validation passed after correcting the fallback test case.
  Evidence: `.venv/bin/python -m pytest -q tests/unit/test_output_path_policy.py tests/unit/test_qt_app_frame.py tests/unit/test_qt_signing_shell.py` reported 85 passed.

- Observation: Full validation passed.
  Evidence: `.venv/bin/python -m ruff check .` reported all checks passed. `.venv/bin/python -m pytest -q` reported 646 passed, 23 skipped, 1 warning in 241.68s.

## Decision Log

- Decision: Extract a small function rather than a service class.
  Rationale: The policy is stateless and deterministic. A service object would add dependency-injection surface before there is any state or backend dependency to inject.
  Date/Author: 2026-05-13 / Codex

- Decision: Keep the helper in the application layer.
  Rationale: The rule is part of signing-session workflow policy, not Qt presentation and not persisted settings storage. Both Qt callers can depend on `foliaseal.application` without creating a new dependency direction.
  Date/Author: 2026-05-13 / Codex

- Decision: Preserve the shell's existing output-filename reuse behavior.
  Rationale: `choose_output_pdf_path()` currently keeps the existing `SigningDraftWorkflow.output_pdf_path` filename while moving the dialog to `AppSettings.default_output_directory`. Changing that would be user-visible and outside this refactor.
  Date/Author: 2026-05-13 / Codex

## Outcomes & Retrospective

This slice is in progress. It will be complete when both Qt callers use a shared application helper, the helper has direct tests for the default and fallback cases, architecture docs are updated, and focused plus full validation pass.

## Context and Orientation

The repository root is `/home/daekar/FoliaSeal`. The Qt app frame lives in `src/foliaseal/presentation/qt/app_frame.py`. It owns the top-level File/Open menu. When a PDF is opened, `FoliaSealAppFrame.open_pdf_path()` creates a `ViewerWorkflow` and a `SigningDraftWorkflow`. The draft's `output_pdf_path` is currently seeded by combining `AppSettings.default_output_directory` with the input PDF stem plus `-signed.pdf`.

The Qt signing shell lives in `src/foliaseal/presentation/qt/signing_shell.py`. Its `SigningWorkspaceWidget.choose_output_pdf_path()` opens the "Save signed PDF" dialog. That method calls `_default_output_dialog_path()`, which starts the dialog in the configured default output directory. If the draft already has an output filename, the shell reuses that filename; otherwise it derives a filename from the input PDF stem and falls back to `signed-signed.pdf` when no stem exists.

The application package lives in `src/foliaseal/application/`. This package already owns workflow helpers such as `SigningDraftWorkflow`, preview rendering, certificate lifecycle coordination, and viewer workflow. This slice should add a new helper module, likely `src/foliaseal/application/output_path_policy.py`, with a pure function named `suggest_signed_output_path()`.

The existing tests are in `tests/unit/test_qt_app_frame.py` and `tests/unit/test_qt_signing_shell.py`. This slice should add direct tests for the new helper, likely in `tests/unit/test_output_path_policy.py`, while keeping Qt tests focused on whether their dialogs and draft wiring still use the same suggested path.

## Plan of Work

First, add application-layer tests in `tests/unit/test_output_path_policy.py`. Cover three cases. A new draft opened from `/docs/contract.pdf` with default output directory `/signed` should suggest `/signed/contract-signed.pdf`. A shell dialog with an existing current output path `/tmp/custom-name.pdf` and default output directory `/signed` should suggest `/signed/custom-name.pdf`. An input path without a useful stem should still fall back to a non-empty filename, preserving the shell's existing `signed-signed.pdf` behavior.

Second, implement `src/foliaseal/application/output_path_policy.py`. Define `suggest_signed_output_path(input_pdf_path: str | Path, default_output_directory: str | Path, current_output_path: str | Path | None = None) -> Path`. The function should convert inputs to `Path`, use `Path(current_output_path).name` when present and non-empty, otherwise use `Path(input_pdf_path).stem or "signed"` plus `-signed.pdf`, and return `Path(default_output_directory) / filename`.

Third, export `suggest_signed_output_path` from `src/foliaseal/application/__init__.py`.

Fourth, migrate `src/foliaseal/presentation/qt/app_frame.py`. Import `suggest_signed_output_path` from `foliaseal.application` and use it when constructing `SigningDraftWorkflow.output_pdf_path` in `open_pdf_path()`. App-frame draft seeding should pass no `current_output_path`.

Fifth, migrate `src/foliaseal/presentation/qt/signing_shell.py`. Import the helper and replace `_default_output_dialog_path()` with a call to `suggest_signed_output_path(input_pdf_path=self._draft_workflow.input_pdf_path, default_output_directory=self._app_settings.default_output_directory, current_output_path=self._draft_workflow.output_pdf_path)`. If `_default_output_dialog_path()` becomes a one-line wrapper, keep it only if it improves readability; otherwise call the helper directly from `choose_output_pdf_path()`.

Sixth, update `docs/ARCHITECTURE.md`. The signing draft workflow and preview rendering section or Qt output path selection section should say the signed-output path suggestion is application policy used by both app frame and signing shell, while Qt owns only file-dialog interaction and workflow mutation after selection.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Focused validation during development:

    .venv/bin/python -m pytest -q tests/unit/test_output_path_policy.py tests/unit/test_qt_app_frame.py tests/unit/test_qt_signing_shell.py

Before committing:

    .venv/bin/python -m ruff check .
    .venv/bin/python -m pytest -q

## Validation and Acceptance

This slice is accepted when direct helper tests prove the path suggestion behavior without Qt, and the existing Qt app-frame and signing-shell tests still prove that opening a PDF and choosing a signed-output path behave as before. The expected focused test result should include all tests passing for `test_output_path_policy.py`, `test_qt_app_frame.py`, and `test_qt_signing_shell.py`.

No user-visible behavior change is expected. Opening `contract.pdf` should still seed `contract-signed.pdf`, and the save-output dialog should still start in the configured default output directory using the current output filename when one exists.

## Idempotence and Recovery

This refactor is additive first and behavior-preserving. If tests fail after migrating one caller, keep the helper and migrate the other caller separately. Since no files are written by the helper itself, retrying tests is safe. If a path edge case is ambiguous, preserve the current Qt behavior and add a test documenting it rather than changing the rule.

## Artifacts and Notes

No generated artifacts are expected. The important evidence will be focused test output, full validation output, and the final commit hash.

## Interfaces and Dependencies

Create `src/foliaseal/application/output_path_policy.py` with:

    def suggest_signed_output_path(
        *,
        input_pdf_path: str | Path,
        default_output_directory: str | Path,
        current_output_path: str | Path | None = None,
    ) -> Path:
        ...

The function depends only on `pathlib.Path`. It must not import Qt, settings stores, viewer workflows, or signing executors.

Revision note: Created 2026-05-13 by Codex after the dev-loop explorer identified duplicated signed-output path policy as a narrow next slice for reducing Qt signing-shell orchestration.
