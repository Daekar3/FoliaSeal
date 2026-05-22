# Add per-signature review details and reopen-and-verify guidance to the signing shell

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows `.agents/skills/write-execplan/PLANS.md` and must be maintained in accordance with that file. It is self-contained so a contributor can resume this slice from only this document and the current repository tree.

## Purpose / Big Picture

`docs/SPEC.md` requires users to inspect existing signatures and verify signed output with plain-language guidance. Today the Qt shell only shows one aggregate review summary and only reports the latest signature. After this change, the review card will show a compact per-signature list for the current PDF and expose one explicit reopen-and-verify action that reuses the existing signed-output reopen path. Users will be able to understand how many signatures the PDF contains, inspect each one at a glance, and use a review-card action to reopen the newly signed output for verification.

This slice is intentionally narrow. It adds structured per-signature review data, renders that data in the existing review card, and surfaces one explicit review action. It does not add a full signature browser, trust-store management, or deep certificate-path diagnostics.

The intended change slice is one behavior change commit for the per-signature review/reopen feature plus one documentation/status update commit only if compliance review requires it. Reworking signature validation policy, adding trust configuration UI, or changing signing mechanics is forbidden from mixing into this slice.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/viewer_signature_review_summary_execplan.md` completed first so the shell already has a document-review injection seam and summary-card pattern.
- [x] `docs/ExecPlans/document_text_selection_highlight_execplan.md` completed first so the review shell surface already supports richer read-only review cards without reopening the viewer architecture.
- [ ] A later child ExecPlan may deepen signature inspection beyond list-level summaries if V1 still needs drill-in details after this slice.

## Progress

- [x] (2026-05-22T20:10:00Z) Completed the required `explorer-light` audit and fixed the target slice to structured per-signature summaries plus a review-card reopen/verify action.
- [x] (2026-05-22T20:13:00Z) Reviewed `docs/SPEC.md`, `docs/ARCHITECTURE.md`, `src/foliaseal/application/document_review.py`, `src/foliaseal/presentation/qt/signing_shell.py`, and the existing review tests before drafting this plan.
- [x] (2026-05-22T20:31:00Z) Added `DocumentSignatureReviewItem`, extended `DocumentReviewSummary.signature_items`, and covered multi-signature review generation in `tests/unit/test_document_review.py`.
- [x] (2026-05-22T20:36:00Z) Extended the `Document review` card with a compact per-signature list plus a `Verify signed PDF` action that reuses `open_signed_output()`, and added focused shell coverage for both behaviors.
- [x] (2026-05-22T20:48:00Z) Ran focused validation: `pytest tests/unit/test_document_review.py tests/unit/test_qt_signing_shell.py`, `ruff check src/foliaseal/application/document_review.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_document_review.py tests/unit/test_qt_signing_shell.py`, and `git diff --check`.
- [x] (2026-05-22T20:58:00Z) Completed the compliance pass and updated `docs/ARCHITECTURE.md` so the review boundary and shell card descriptions match the implemented per-signature/reopen behavior.
- [x] (2026-05-22T20:58:00Z) Prepared the slice for commit and recorded the next remaining SPEC-alignment gap after this review deepening slice.

## Surprises & Discoveries

- Observation: the current review inspector already enumerates all embedded signatures, but it only summarizes the latest one.
  Evidence: `src/foliaseal/application/document_review.py` converts `reader.embedded_signatures` to a list and then only inspects `embedded_signatures[-1]`.

- Observation: the reopen-and-verify path already exists and is public, but it is not surfaced as part of the review workflow.
  Evidence: `src/foliaseal/presentation/qt/signing_shell.py` already exposes `open_signed_output()` and the app frame already reopens signed output through `on_open_signed_output=self.open_pdf_path`.

## Decision Log

- Decision: keep `DocumentReviewSummary` backward-compatible and extend it with a per-signature item list rather than replacing it with a new top-level review type.
  Rationale: the shell and tests already depend on the summary payload, and this slice only needs to deepen it, not replace it.
  Date/Author: 2026-05-22 / Codex

- Decision: render the per-signature details as a compact read-only list in the existing review card instead of adding a separate review dialog.
  Rationale: this keeps the slice small, preserves the current shell structure, and still materially advances the “inspect existing signatures” requirement.
  Date/Author: 2026-05-22 / Codex

- Decision: the explicit verify action in this slice will reuse the existing reopen-signed-output path rather than attempting in-place shell mutation.
  Rationale: the app frame already rebuilds the shell on reopen, and that behavior is the safest way to guarantee review state is refreshed from the actual signed file.
  Date/Author: 2026-05-22 / Codex

## Outcomes & Retrospective

This slice completed the narrow review deepening target without reopening trust-policy or signing-engine scope. The application review boundary now preserves the existing top-level summary while also returning one plain-language item per embedded signature. The shell review card now renders those items directly and exposes a `Verify signed PDF` action that reuses the existing signed-output reopen path instead of inventing a second verification flow.

The compliance pass found only documentation drift:

- `docs/ARCHITECTURE.md` still described the review card as summary-only.
- This ExecPlan was still written mostly in future tense.

Those issues were corrected locally. No `docs/SPEC.md` changes were needed or allowed because the spec is frozen without explicit user approval.

## Context and Orientation

The application-layer review boundary lives in `src/foliaseal/application/document_review.py`. Right now it exposes one immutable `DocumentReviewSummary` dataclass and one `DocumentReviewInspector` protocol. The concrete `PyHankoDocumentReviewInspector` reads the PDF, collects embedded signatures, validates only the latest one locally, and returns a flat summary with one signer subject and one cryptographic-validation result.

The Qt shell review surface lives in `src/foliaseal/presentation/qt/signing_shell.py`. `SigningWorkspaceWidget` builds a `Document review` group box with two labels: a headline and a detail string. `refresh_document_review()` calls the inspector and writes those two labels. The shell also already knows how to reopen the last successful output path through `open_signed_output()`, but that action currently lives outside the review card.

The relevant tests are `tests/unit/test_document_review.py` and `tests/unit/test_qt_signing_shell.py`. The current review tests prove unsigned, signed, and restricted summary strings plus missing-file behavior. The shell tests prove that an injected review summary populates the two existing labels.

In this slice, a “per-signature review item” means a read-only summary for one embedded signature, suitable for display in a compact list. It should contain the signer subject when available, whether local cryptographic verification passed, and a short plain-language note. The review helper should keep the existing aggregate summary for compatibility, but also expose the list of per-signature items so the shell can render them.

## Plan of Work

First, extend `src/foliaseal/application/document_review.py`. Add a new immutable item dataclass for one signature review line, such as `DocumentSignatureReviewItem`, and extend `DocumentReviewSummary` with a tuple of those items. Update `summarize_document_review()` so it can accept and preserve that list while keeping the current headline/detail behavior intact. Update `PyHankoDocumentReviewInspector.inspect()` so it creates one review item per embedded signature, still summarizes the latest signature at the top level, and remains failure-tolerant for missing or unreadable PDFs.

Second, extend `src/foliaseal/presentation/qt/signing_shell.py`. Expand the `DocumentReviewControls` dataclass and `_build_document_review_controls()` so the review card can render a compact list label for the per-signature items plus a button like `Verify signed PDF`. That button should reuse the existing signed-output reopen path and stay disabled unless there is a current signed output path and a reopen callback is available. `refresh_document_review()` should write the aggregate summary and the per-signature list. A small helper should format the signature items into plain-language list lines without over-claiming trust.

Third, add focused tests. Extend `tests/unit/test_document_review.py` with multi-signature coverage, proving that the top-level latest-signature summary remains correct while the per-signature item list contains all embedded signatures. Extend `tests/unit/test_qt_signing_shell.py` with one shell test that injects a multi-signature review summary and asserts the review card renders all items, and one test that proves the new review-card verify button delegates to the same reopen path as `open_signed_output()`.

Finally, run focused validation, then perform the required compliance review against `docs/SPEC.md`, `docs/ARCHITECTURE.md`, and this ExecPlan. If the review finds stale docs, update them and rerun the focused checks before committing.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

Inspect the current interfaces before editing:

    sed -n '1,260p' src/foliaseal/application/document_review.py
    sed -n '1960,2425p' src/foliaseal/presentation/qt/signing_shell.py
    sed -n '1,240p' tests/unit/test_document_review.py
    sed -n '980,1105p' tests/unit/test_qt_signing_shell.py

After updating the application review helper and shell review card, run:

    pytest tests/unit/test_document_review.py tests/unit/test_qt_signing_shell.py

Then run focused lint:

    ruff check src/foliaseal/application/document_review.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_document_review.py tests/unit/test_qt_signing_shell.py

Finally ensure patch hygiene:

    git diff --check

If compliance review requires documentation changes, rerun the relevant focused checks and record the final passing commands in this plan.

## Validation and Acceptance

Acceptance is behavioral. After this change, a user opening a signed PDF in the Qt shell must see a plain-language review summary plus a compact list of all embedded signatures. After signing a PDF successfully, the review surface must expose an explicit action that reopens the signed output for verification using the existing shell/app-frame path.

The proof points are:

- `tests/unit/test_document_review.py` passes and proves unsigned, single-signature, and multi-signature review behavior, including per-signature item generation.
- `tests/unit/test_qt_signing_shell.py` passes and includes a shell-level test for rendering multi-signature review details and a test for the review-card reopen/verify action.
- `ruff check` and `git diff --check` pass.

This slice is complete when those proofs hold and the compliance review confirms that the implementation materially advances the `inspect existing signatures` and `verify signed result with plain-language guidance` portions of `docs/SPEC.md`.

## Idempotence and Recovery

This feature is read-only with respect to the PDF. Refreshing the review card, reopening the signed output for verification, and rendering per-signature summaries must not mutate the document or signing configuration.

Implement the tests first, then extend the review helper, then render the extra review-card details. If the per-signature list starts to bloat the shell UI, keep the item formatting compact rather than introducing a separate dialog in this slice. Do not change validation policy or trust semantics here; keep the existing “verified locally” wording.

## Artifacts and Notes

Historical gap evidence before the change:

    docs/SPEC.md
    - V1 still requires users to inspect existing signatures and verify the signed result with plain-language guidance.

    src/foliaseal/application/document_review.py
    - only the latest signature is summarized today.

    src/foliaseal/presentation/qt/signing_shell.py
    - the review card renders only headline/detail labels and has no explicit review action.

Validation evidence after implementation:

    pytest tests/unit/test_document_review.py tests/unit/test_qt_signing_shell.py
    - 71 passed

    ruff check src/foliaseal/application/document_review.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_document_review.py tests/unit/test_qt_signing_shell.py
    - all checks passed

    git diff --check
    - passed

## Interfaces and Dependencies

At the end of this slice, the review boundary should have a shape along these lines:

    @dataclass(frozen=True)
    class DocumentSignatureReviewItem:
        label: str
        signer_subject: str | None
        cryptographic_validation_passed: bool | None
        detail: str

    @dataclass(frozen=True)
    class DocumentReviewSummary:
        headline: str
        detail: str
        signature_count: int | None
        signature_items: tuple[DocumentSignatureReviewItem, ...] = ()
        ...

The shell review controls should grow by one compact details label and one review action button, but the shell must still consume the review helper as an injected dependency and must still rely on the existing `on_open_signed_output` callback for reopening signed output.

Next remaining SPEC-alignment gap after this slice:

- The review surface now shows all signatures at a glance and makes reopen-and-verify explicit, but it still does not provide a deeper per-signature drill-in workflow or richer plain-language next-action guidance beyond the compact item list. That remains the next review ergonomics slice if tighter alignment with `inspect existing signatures` is needed.

Change note: 2026-05-22 / Codex

Created this ExecPlan from the required `explorer-light` audit for the next highest-value SPEC-alignment slice, then closed it after implementation, focused validation, and a local compliance pass. The chosen approach stayed intentionally narrow by deepening the existing review helper and reusing the established reopen path.
