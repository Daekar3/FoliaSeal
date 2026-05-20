# Require explicit signed-output overwrite confirmation

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

FoliaSeal writes the final signed PDF to a user-selected output path. The project specification says the app must use an explicit save dialog and, when the platform save dialog does not warn about overwriting an existing file, the app itself must require explicit confirmation before replacing that file. Today the Qt shell opens a save dialog and records the chosen path, but the repository does not enforce or test an app-level overwrite confirmation for an existing different destination. After this change, choosing an existing signed-output path will show a confirmation prompt before the draft output path changes. Canceling the prompt leaves the old output path and any previous signing result alone; confirming the prompt updates the path and clears stale signed-result state.

This is visible in tests by selecting an existing output file through the fake Qt save dialog. A declined confirmation returns `None`, keeps `SigningDraftWorkflow.output_pdf_path` unchanged, and leaves the signed result visible. An accepted confirmation returns the selected path and updates the draft as before.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md` defines signed-output save-dialog and overwrite-confirmation requirements.
- [x] Existing Qt signing shell output-path chooser is implemented in `SigningWorkspaceWidget.choose_output_pdf_path()`.
- [x] Explorer-light audit confirmed that same-file rejection and atomic replacement exist, and that the remaining gap is explicit app-level confirmation for existing different destinations.

## Progress

- [x] (2026-05-20 23:16Z) Spawned an `explorer-light` subagent to inspect signed-output requirements, current code paths, and test seams.
- [x] (2026-05-20 23:16Z) Reviewed `PLANS.md`, `docs/SPEC.md`, `signing_shell.py`, and existing Qt signing-shell tests.
- [x] (2026-05-20 23:16Z) Created this ExecPlan.
- [x] (2026-05-20 23:20Z) Added focused failing tests for existing-output cancel and confirm behavior.
- [x] (2026-05-20 23:21Z) Implemented explicit overwrite confirmation in `SigningWorkspaceWidget.choose_output_pdf_path()`.
- [x] (2026-05-20 23:22Z) Ran focused validation: `pytest tests/unit/test_qt_signing_shell.py` reported `72 passed in 10.35s`.
- [x] (2026-05-20 23:22Z) Ran focused lint: `ruff check src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py docs/ExecPlans/signed_output_overwrite_confirmation_execplan.md` reported `All checks passed!`.
- [x] (2026-05-20 23:24Z) Ran two-agent compliance review. One reviewer found no issues; the second found that same-current-output paths still skipped confirmation and noted possible duplicate prompting when native dialogs already warn.
- [x] (2026-05-20 23:27Z) Added same-current-output overwrite regression coverage and updated the implementation.
- [x] (2026-05-20 23:28Z) Ran follow-up focused validation: `pytest tests/unit/test_qt_signing_shell.py` reported `73 passed in 10.35s`.
- [x] (2026-05-20 23:28Z) Ran follow-up focused lint: `ruff check src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py docs/ExecPlans/signed_output_overwrite_confirmation_execplan.md` reported `All checks passed!`.
- [x] (2026-05-20 23:30Z) Reran two-agent compliance review. Both reviewers found the behavior compliant; one found low architecture documentation drift.
- [x] (2026-05-20 23:31Z) Updated `docs/ARCHITECTURE.md` to document the explicit overwrite confirmation branch.
- [x] (2026-05-20 23:32Z) Reran final focused validation after documentation update: `pytest tests/unit/test_qt_signing_shell.py` reported `73 passed in 10.37s`.
- [x] (2026-05-20 23:32Z) Reran final focused lint: `ruff check src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py docs/ExecPlans/signed_output_overwrite_confirmation_execplan.md docs/ARCHITECTURE.md` reported `All checks passed!`.
- [ ] Commit the completed slice.

## Surprises & Discoveries

- Observation: The backend is already protected against signing over the input file and writes atomically.
  Evidence: The explorer reported existing `SignPdfUseCase` tests for same-path rejection and atomic replacement.

- Observation: The remaining gap is user confirmation for existing output files, not output path selection itself.
  Evidence: `SigningWorkspaceWidget.choose_output_pdf_path()` already calls `QFileDialog.getSaveFileName()` and only mutates the draft after a non-empty selected path.

## Decision Log

- Decision: Implement confirmation in the Qt shell path chooser, not in the signing use case.
  Rationale: The specification frames overwrite confirmation as UI behavior tied to the save dialog. The signing use case may legitimately atomically replace a path after the UI has confirmed it, and it already rejects the higher-risk same-input/same-output case.
  Date/Author: 2026-05-20 / Codex

- Decision: Prompt when the selected path exists, even if it is already the current draft output path.
  Rationale: A current output path can still point to an existing signed PDF that would be replaced on the next sign operation. The specification requires explicit confirmation before overwriting an existing file when the app cannot prove the platform dialog already provided that warning.
  Date/Author: 2026-05-20 / Codex

- Decision: Keep an app-level confirmation even though some native dialogs may already warn.
  Rationale: The current `QFileDialog.getSaveFileName()` call does not expose whether a native overwrite warning was shown, and the test fakes cannot prove native behavior. A redundant prompt is less severe than silent replacement and gives the repository a deterministic, test-backed safety gate.
  Date/Author: 2026-05-20 / Codex

## Outcomes & Retrospective

This plan is complete pending commit. Tests prove that an existing selected output path requires confirmation, that canceling confirmation leaves the draft and prior signing result untouched, and that confirming still updates the output path and clears stale signed-result state.

The first implementation pass passed focused validation, but compliance review found that it incorrectly skipped confirmation when the selected path was already the current draft output path. The follow-up changes the rule to prompt whenever the selected path exists. Canceling the confirmation returns `None` and preserves existing state; confirming continues with the existing output-path update flow. Follow-up focused validation now passes.

Follow-up compliance review found the behavior compliant and identified only architecture documentation drift. The architecture document now says that existing selected output paths require explicit overwrite confirmation before the draft output path mutates.

Final focused validation and lint pass after the documentation update. The only remaining action is committing the completed slice.

## Context and Orientation

The Qt signing shell is the graphical signing workflow in `src/foliaseal/presentation/qt/signing_shell.py`. `SigningWorkspaceWidget.choose_output_pdf_path()` opens the save dialog and writes the chosen path to `SigningDraftWorkflow.output_pdf_path`. A signed result is stale after the output path changes, so existing code calls `_clear_previous_signing_result()` after accepting a new path. The tests for this behavior live in `tests/unit/test_qt_signing_shell.py` and use `_FakeFileDialog` plus `_FakeMessageBox`.

An overwrite confirmation means asking the user whether to continue before choosing an output path that already exists on disk. The prompt should use the same `QMessageBox.question()` pattern already used by signature-preset overwrite confirmation in the signing shell tests. If the fake or real message box returns the `Yes` value, the path change proceeds; any other value cancels the path change.

## Plan of Work

First add tests in `tests/unit/test_qt_signing_shell.py`. Add one test where the fake file dialog returns an existing file, the fake message box returns `No`, and `choose_output_pdf_path()` returns `None` without changing `workflow.output_pdf_path`, clearing `last_signing_result`, or changing the sign-result label. Add one test where the existing file is confirmed with `Yes`, and the path updates exactly as the current non-existing-path test does. Keep or extend the existing new-file test to prove it does not require a confirmation call.

Then update `SigningWorkspaceWidget.choose_output_pdf_path()` in `src/foliaseal/presentation/qt/signing_shell.py`. After normalizing the selected path and before mutating `_draft_workflow.output_pdf_path`, call a small helper such as `_confirm_output_overwrite(selected_path)` when `Path(selected_path).exists()` and the selected path differs from the current draft output path. The helper should call `self._bindings.q_message_box.question(self.widget, "Overwrite signed PDF?", "...")` and compare the result with `q_message_box.Yes`, falling back to `q_message_box.StandardButton.Yes` when needed, matching the existing defensive Qt binding style.

No backend signing code should change in this slice. No generated artifacts should be updated. Architecture docs already state the output path chooser behavior broadly enough; update docs only if compliance review finds the wording incomplete.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Run focused tests while iterating:

    pytest tests/unit/test_qt_signing_shell.py

Run focused lint before review:

    ruff check src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py docs/ExecPlans/signed_output_overwrite_confirmation_execplan.md

## Validation and Acceptance

Acceptance requires three observable behaviors. When the selected output path does not exist, `choose_output_pdf_path()` should not prompt and should keep existing behavior. When the selected output path exists and the user declines overwrite confirmation, `choose_output_pdf_path()` should return `None`, leave the previous draft output path unchanged, and leave any previous successful signing result visible. When the selected output path exists and the user confirms overwrite, `choose_output_pdf_path()` should return the selected path, update `SigningDraftWorkflow.output_pdf_path`, clear previous signing result state, and show the updated output path message.

The focused test command should pass with the new tests included.

## Idempotence and Recovery

The implementation is safe to rerun. Tests use temporary directories and fake Qt bindings, so no user files are overwritten. If a test fails midway, rerun the same focused command after fixing the shell helper or fake assertion. Do not change `SignPdfUseCase` atomic-write behavior or same-input/same-output rejection in this slice.

## Artifacts and Notes

Explorer-light audit summary:

    Current code already covers explicit save dialog, reusable suggested output path, same-file conflict rejection, and atomic replacement. The remaining gap is a testable explicit confirm-overwrite step for an existing different destination, which the shell currently leaves to Qt/native dialog behavior.

## Interfaces and Dependencies

`SigningWorkspaceWidget.choose_output_pdf_path()` should continue to return `str | None`.

Add an internal helper with behavior equivalent to:

    def _confirm_output_overwrite(self, selected_path: str) -> bool:
        ...

It should return `True` when no prompt is required or the user confirms, and `False` when the user declines.

## Revision Notes

- 2026-05-20: Created plan from the signed-output overwrite audit and current Qt signing-shell code inspection.
- 2026-05-20: Updated progress and outcomes after adding tests, implementing overwrite confirmation, and passing focused validation.
- 2026-05-20: Updated progress, decision log, and outcomes after compliance review found the same-current-output path still needed confirmation.
- 2026-05-20: Updated progress and outcomes after same-current-output overwrite coverage and follow-up validation passed.
- 2026-05-20: Updated progress and outcomes after follow-up compliance review and architecture documentation update.
- 2026-05-20: Updated progress and outcomes after final focused validation and lint passed.
