# Remove Misleading Review-Panel Verify Affordance

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with [/home/daekar/FoliaSeal/.agents/skills/write-execplan/PLANS.md](/home/daekar/FoliaSeal/.agents/skills/write-execplan/PLANS.md).

## Purpose / Big Picture

After this change, the document review card will be read-only again. The sidebar will no longer show a `Verify signed PDF` button that only reopens the signed output path and duplicates the primary `Open signed PDF` action in the sign panel. This reduces product confusion and keeps the reopen flow in one obvious place, which is closer to the staged `Sign -> Save -> Verify` flow in `docs/SPEC.md`.

The change is observable in the fake-Qt shell tests and in the live GUI. After a successful sign, only the sign-panel reopen button should become enabled. The document review card should show review details only and no longer expose a misleading verify affordance.

## Child ExecPlan Dependencies

- [x] No child ExecPlans are required for this slice.

## Progress

- [x] (2026-05-27 09:41 EDT) Removed the review-panel verify/reopen affordance from `src/foliaseal/presentation/qt/signing_workspace_sidebar.py`.
- [x] (2026-05-27 09:41 EDT) Removed the matching shell export and enablement path from `src/foliaseal/presentation/qt/signing_shell.py`.
- [x] (2026-05-27 09:41 EDT) Updated focused shell tests in `tests/unit/test_qt_signing_shell.py`.
- [x] (2026-05-27 09:41 EDT) Reviewed compliance against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and `docs/SCHEMAS.md`, then updated docs to match the final one-button reopen flow.
- [x] (2026-05-27 09:41 EDT) Validated with `pytest tests/unit/test_qt_signing_shell.py` (`76 passed`), `ruff check ...` (passed), and `git diff --check` (passed).
- [x] (2026-05-27 06:29 EDT) Commit the slice once implementation, compliance review, and documentation updates are complete.

## Surprises & Discoveries

- Observation: Removing the review-card button did not require any change to the signing action coordinator or app-frame integration. The reopen flow was already fully owned by the primary sign panel and the shell callback surface.
  Evidence: `pytest tests/unit/test_qt_signing_shell.py` -> `76 passed`.

## Decision Log

- Decision: Delete the review-card verify button instead of renaming or repurposing it.
  Rationale: The existing button does not perform verification; it only reuses `on_open_signed_output`. Keeping a mislabeled affordance would preserve product confusion and a redundant reopen path.
  Date/Author: 2026-05-26 / Codex

## Outcomes & Retrospective

- The slice is complete at the code-and-doc level. The review card is read-only again, the misleading `Verify signed PDF` label is gone, and reopening the last successful output now lives only in the primary sign panel.
- The focused shell suite stayed green after the cleanup, which confirms the removed affordance was redundant rather than structurally important.

## Context and Orientation

The right-hand production sidebar is built in `src/foliaseal/presentation/qt/signing_workspace_sidebar.py`. It contains the primary `Sign PDF` action panel plus a `Document review` card. Before this slice, the review card added a `Verify signed PDF` button and wired it directly to `on_open_signed_output`. That button was mislabeled: it did not run verification logic or refresh document review state, it just reopened the last signed PDF path.

The shell adapter in `src/foliaseal/presentation/qt/signing_shell.py` previously mirrored that redundant surface by exporting `widget.document_review_verify_button` and enabling or disabling it alongside the real `Open signed PDF` button in `_set_last_successful_output_path()`. The current state removes that review-side export and keeps reopening only in the primary sign panel.

The product intent in `docs/SPEC.md` is a staged flow where reopen/verify happens after signing, but that does not require two separate reopen buttons in the same sidebar. The sign panel already owns the real reopen action. The review card should stay read-only and focus on explaining existing signatures and verification results, not pretending to be an action surface.

## Plan of Work

Edit `src/foliaseal/presentation/qt/signing_workspace_sidebar.py` first. Remove `verify_button` from `DocumentReviewControls`, delete its construction in `_build_document_review_controls()`, stop accepting or using `on_open_signed_output` in that builder, and remove the button from the layout.

Then edit `src/foliaseal/presentation/qt/signing_shell.py`. Remove the exported `widget.document_review_verify_button` test surface and delete the review-side enablement branch from `_set_last_successful_output_path()`. Do not change the primary sign-panel `Open signed PDF` behavior.

Then update `tests/unit/test_qt_signing_shell.py`. Remove the test that clicks the review-card verify button. Update the successful-sign and failure-path tests so they only assert the sign-panel reopen button state. Keep the rest of the signing action coverage intact.

If the architecture doc still claims the shell enables both `Open signed PDF` and `Verify signed PDF`, update it to describe the slimmer one-button reopen flow.

## Concrete Steps

From `/home/daekar/FoliaSeal`, implement the sidebar and shell cleanup, then run focused validation.

Expected commands:

    pytest tests/unit/test_qt_signing_shell.py
    ruff check src/foliaseal/presentation/qt/signing_workspace_sidebar.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py
    git diff --check

Expected outcomes:

    - the review card has no verify/reopen button
    - the sign-panel `Open signed PDF` button still enables after successful signing
    - the sign failure path still disables reopen
    - `ruff check` reports no issues
    - `git diff --check` reports no whitespace or merge-marker problems

## Validation and Acceptance

Run `pytest tests/unit/test_qt_signing_shell.py` from `/home/daekar/FoliaSeal` and expect the suite to pass. The successful-sign test must prove that `open_signed_output_button` is enabled after success and no review-side verify button is present. The failure-path test must still prove reopen stays disabled after a failed sign.

Run `ruff check src/foliaseal/presentation/qt/signing_workspace_sidebar.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py` and expect a clean pass. Run `git diff --check` and expect no output.

If `docs/ARCHITECTURE.md` changes, it must describe the review card as read-only and the reopen action as living in the primary sign panel only.

## Idempotence and Recovery

This slice is safe to repeat. The validation commands are read-only. If an edit goes wrong, restore the intended steady state: the review card contains only labels and selector/detail widgets, the shell no longer exports `document_review_verify_button`, and only the sign-panel reopen button is enabled after a successful sign.

## Artifacts and Notes

The most important evidence for this slice should be concise:

    pytest tests/unit/test_qt_signing_shell.py
    ... passed

    ruff check src/foliaseal/presentation/qt/signing_workspace_sidebar.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py
    All checks passed!

## Interfaces and Dependencies

This slice must leave the signing action coordinator unchanged. Reopen behavior still flows through:

    SigningActionCoordinator.open_signed_output()
    SigningWorkspaceWidget.open_signed_output()

At the sidebar boundary, `DocumentReviewControls` must expose only read-only review widgets:

    container
    headline_label
    detail_label
    signature_items_label
    signature_selector
    signature_detail_label

It must stop exposing:

    verify_button

At the shell boundary, `widget.document_review_verify_button` must disappear, and `_set_last_successful_output_path()` must only enable or disable the sign-panel `open_signed_output_button`.

Revision note: Created on 2026-05-26 to drive the removal of the misleading review-card verify affordance and keep reopening in the primary sign flow only.
Revision note: Updated on 2026-05-27 after implementation and compliance review so the plan reflects the completed one-button reopen flow, validation evidence, and final architecture wording.
