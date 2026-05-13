# Post-Sign Completion Surface

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this change, a user who signs a PDF in the GUI will see a compact completion surface that says where the signed file was saved, summarizes the local verification evidence already returned by the signing backend, and offers an explicit `Open signed PDF` action. This advances the V1 product story from `sign offline` toward `reopen and verify the result` without redesigning the whole signing shell.

In this plan, "completion surface" means the small area below the signing controls that currently contains only one result label. "Local verification" means the post-sign checks already performed by the signing backend and represented on `SigningResult`; it does not mean broad online trust or revocation checks.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/signed_output_path_policy_execplan.md` is complete; output path selection is shared application policy.
- [x] The backend signing use case already returns `SigningResult` values with verification fields such as `timestamp_present`, `timestamp_cryptographically_valid`, `tsa_chain_trusted`, `docmdp_permission`, `restriction_reason`, and `standards_summary`.
- [x] The Qt app frame already exposes `FoliaSealAppFrame.open_pdf_path()` for opening any PDF path.
- [x] The dev-loop explorer confirmed the narrowest high-value slice is a post-sign completion surface plus explicit reopen callback, not a broad GUI redesign.

## Progress

- [x] (2026-05-13T11:19Z) Reviewed `docs/SPEC.md`, architecture docs, signing backend result fields, existing Qt shell sign flow, and app-frame open flow.
- [x] (2026-05-13T11:19Z) Created this ExecPlan for the post-sign completion surface.
- [x] (2026-05-13T11:23Z) Added pure formatter tests for plain-language post-sign completion text.
- [x] (2026-05-13T11:23Z) Implemented an application-layer formatter for `SigningResult` completion guidance.
- [x] (2026-05-13T11:23Z) Added an `Open signed PDF` action to the Qt signing shell and wired it to an injected callback.
- [x] (2026-05-13T11:23Z) Wired the app frame to pass `open_pdf_path` as the shell reopen callback.
- [x] (2026-05-13T11:23Z) Updated architecture documentation for the completion surface and reopen flow.
- [x] (2026-05-13T11:28Z) Ran focused and full validation successfully.
- [ ] Commit the completed slice.

## Surprises & Discoveries

- Observation: The backend already does the verification work needed for a first GUI completion surface.
  Evidence: `SignPdfUseCase.execute()` calls `self.verifier.verify(request.output_pdf_path, trust_policy=request.trust_policy)` after writing the signed output and copies verification fields into `SigningResult`.

- Observation: The existing Qt shell has only a one-line success label.
  Evidence: `SigningWorkspaceWidget.submit_sign_request()` currently sets `f"{result.message} Output: {request.output_pdf_path}"` when signing succeeds.

- Observation: Reopen can be a callback instead of a new app-frame dependency from the shell.
  Evidence: `FoliaSealAppFrame.open_pdf_path()` already opens any PDF path, while `build_qt_signing_shell()` already accepts callbacks such as `on_sign_request`, `on_error`, and `on_status_change`.

- Observation: Focused formatter, shell, and app-frame tests passed after wiring the completion surface.
  Evidence: `.venv/bin/python -m pytest -q tests/unit/test_signing_completion.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py` reported 89 passed.

- Observation: Full validation passed.
  Evidence: `.venv/bin/python -m ruff check .` reported all checks passed. `.venv/bin/python -m pytest -q` reported 653 passed, 23 skipped, 1 warning in 219.27s.

## Decision Log

- Decision: Add explicit `Open signed PDF` instead of auto-opening the output.
  Rationale: Auto-open would replace the current document immediately after signing and could surprise users. The SPEC requires reopening and verification, but an explicit action keeps control with the user.
  Date/Author: 2026-05-13 / Codex

- Decision: Format completion guidance in an application helper and keep Qt responsible only for displaying it.
  Rationale: The wording depends on `SigningResult` semantics, not widget state. A helper makes the plain-language rules testable without constructing Qt fakes.
  Date/Author: 2026-05-13 / Codex

- Decision: Reuse the existing app-frame `open_pdf_path()` path rather than creating a separate document-reopen service in this slice.
  Rationale: The app frame already owns top-level document opening and shell replacement. A new service would add indirection before a second caller exists.
  Date/Author: 2026-05-13 / Codex

## Outcomes & Retrospective

This slice is in progress. It will be complete when successful signing displays a multi-line completion summary, an `Open signed PDF` action is available only after a successful sign, clicking that action calls the injected reopen callback with the signed output path, architecture docs describe the flow, and focused plus full validation pass.

## Context and Orientation

The repository root is `/home/daekar/FoliaSeal`. The product spec in `docs/SPEC.md` says the V1 user story includes saving the signed output, reopening it, and verifying the result with plain-language guidance. The current GUI can sign through the Qt shell but only shows a one-line result after success.

The stable signing result type is `SigningResult` in `src/foliaseal/domain/models.py`. It includes the plain success/failure message plus verification-related fields: `output_pdf_version`, `signature_subfilter`, `timestamp_present`, `timestamp_cryptographically_valid`, `tsa_chain_trusted`, `timestamp_validation_error`, `docmdp_permission`, `certification_restricted`, `restriction_reason`, and `standards_summary`.

The headless signing use case is `SignPdfUseCase` in `src/foliaseal/application/sign_pdf_use_case.py`. It writes signed output and then verifies it. The Qt shell does not need to verify again in this slice; it should present the `SigningResult` it already receives.

The Qt signing shell lives in `src/foliaseal/presentation/qt/signing_shell.py`. `SigningWorkspaceWidget.submit_sign_request()` applies pending controls, builds a `SigningRequest`, executes the injected signing executor, stores `last_signing_result`, and updates `sign_result_label`. It already creates `Confirm and sign` and `Choose output...` buttons.

The Qt app frame lives in `src/foliaseal/presentation/qt/app_frame.py`. `FoliaSealAppFrame.open_pdf_path()` opens a PDF path and replaces the current central shell. This slice should pass that method into the signing shell as a callback so the shell can offer `Open signed PDF` after success without importing the app frame.

## Plan of Work

First, add tests for a small application helper, likely `tests/unit/test_signing_completion.py`. The helper should accept a `SigningResult` and output path and return a multi-line string. A successful result with `standards_summary` and `timestamp_present=False` should include "Signing completed successfully.", "Saved to:", the standards summary, and a plain statement that no timestamp token was found or required. A result with `timestamp_cryptographically_valid=False` or `tsa_chain_trusted=False` should include the backend validation error plainly. A result with `certification_restricted=True` or `restriction_reason` should mention that adding another signature may be blocked or restricted.

Second, implement the helper in a new application module, likely `src/foliaseal/application/signing_completion.py`. Define `format_signing_completion_message(result: SigningResult, output_pdf_path: str | Path) -> str`. The helper should not import Qt. It should not claim broad trust if trust fields are `None`; it should say local verification completed and indicate when timestamp trust was not evaluated.

Third, export the helper from `src/foliaseal/application/__init__.py`.

Fourth, update `src/foliaseal/presentation/qt/signing_shell.py`. Add an optional `on_open_signed_output: Callable[[str], Any] | None` parameter through `build_qt_signing_shell()`, `SigningShellAdapter`, and `SigningWorkspaceWidget`. Add a button labeled `Open signed PDF`, initially disabled. Store the last successful output path. On successful sign, call `format_signing_completion_message(result, request.output_pdf_path)`, enable the open button, and keep firing `on_status_change("sign_success")`. On failure or pre-submit validation failure, disable the open button and clear the stored successful output path. Clicking the button should call the injected callback with the stored output path if both exist.

Fifth, update `src/foliaseal/presentation/qt/app_frame.py` so `open_pdf_path()` passes `on_open_signed_output=self.open_pdf_path` to the shell builder. This means the opened signed PDF uses the same page-count load, viewer workflow, signing workflow, settings, certificate store, and shell builder path as any other opened file.

Sixth, update tests. In `tests/unit/test_qt_signing_shell.py`, extend the success test to assert completion text includes the output path and verification summary and that the open button becomes enabled. Add a test that clicking the open button calls the callback with `request.output_pdf_path`. Add a failure test to prove the button is disabled and no stale path opens. In `tests/unit/test_qt_app_frame.py`, assert the shell builder receives `on_open_signed_output` and that invoking it reopens the signed output path.

Seventh, update `docs/ARCHITECTURE.md` to describe the post-sign completion surface and explicit reopen callback in the Qt signing workflow section.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Focused validation during development:

    .venv/bin/python -m pytest -q tests/unit/test_signing_completion.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py tests/unit/test_sign_pdf_use_case.py

Before committing:

    .venv/bin/python -m ruff check .
    .venv/bin/python -m pytest -q

## Validation and Acceptance

This slice is accepted when a successful GUI sign displays a multi-line completion message that includes saved path and local verification guidance, and when a visible `Open signed PDF` action calls the app-frame reopen path with the signed output. Direct formatter tests should prove the wording does not overstate trust when trust fields are unknown. Existing signing success and failure tests must keep passing.

No backend signing behavior should change in this slice. The signing executor remains the source of truth for success/failure and verification fields.

## Idempotence and Recovery

The changes are additive and behavior-preserving for the backend. If the UI wiring fails, keep the formatter tests and revert only the shell/app-frame callback wiring. The open-signed-output button must be disabled unless a successful signing result has produced a concrete output path, so repeated failed signing attempts cannot accidentally reopen an old file.

## Artifacts and Notes

No generated artifacts are expected. The important evidence will be focused test output, full validation output, and the final commit hash.

## Interfaces and Dependencies

Create `src/foliaseal/application/signing_completion.py` with:

    def format_signing_completion_message(
        result: SigningResult,
        output_pdf_path: str | Path,
    ) -> str:
        ...

Update the Qt shell construction path to accept:

    on_open_signed_output: Callable[[str], Any] | None = None

This callback should be passed from `FoliaSealAppFrame.open_pdf_path()` to `build_qt_signing_shell()` as `self.open_pdf_path`.

Revision note: Created 2026-05-13 by Codex after the functional-sprint recommendation to advance the SPEC.md V1 signing completion, reopen, and verification requirements.
