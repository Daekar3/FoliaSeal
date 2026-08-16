# Document the selector-driven per-signature drill-in review card

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows `.agents/skills/write-execplan/PLANS.md` and must be maintained in accordance with that file. It is self-contained so a contributor can resume this slice from only this document and the current repository tree.

## Purpose / Big Picture

The selector-driven per-signature drill-in is implemented in the signing-shell review card. A user opening a signed PDF in FoliaSeal can stay inside the existing `Document review` card, see the review summary and compact per-signature list, choose one embedded signature, and read a richer plain-language detail block for that specific signature without opening a separate dialog or review window. The user-visible gain is that “inspect existing signatures” moves beyond a list-at-a-glance view into a lightweight drill-in while the `Verify signed PDF` action remains in place.

This slice matters because `docs/SPEC.md` requires signature inspection and plain-language verification guidance. The current tree now meets that requirement through an interactive, selector-based drill-in on top of the existing review card. The remaining work for this file is to keep the plan accurate as a living record and to track any future follow-on slice if the inline drill-in later proves insufficient.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/viewer_signature_review_summary_execplan.md` completed first so the shell already had a document-review injection seam and summary-card pattern.
- [x] `docs/ExecPlans/per_signature_review_reopen_execplan.md` completed first so the shell already exposed a compact per-signature list and a review-card reopen/verify action.
- [ ] A later child ExecPlan may deepen signature inspection into a dedicated browser or richer certificate-path diagnostics if the inline card drill-in still falls short of `docs/SPEC.md`.

## Progress

- [x] (2026-05-22T21:15:00Z) Completed the required `explorer-light` audit and fixed the target slice to an inline selector-based drill-in inside the existing `Document review` card.
- [x] (2026-05-22T21:19:00Z) Reviewed `docs/SPEC.md`, `docs/ARCHITECTURE.md`, `src/foliaseal/application/document_review.py`, `src/foliaseal/presentation/qt/signing_shell.py`, and the current review tests before writing this plan.
- [x] (2026-05-22T21:35:00Z) The selector-driven drill-in behavior is already implemented in the tree; this plan now records that completed state instead of describing a future implementation.
- [x] (2026-05-22) Refreshed the publication record; the implemented slice
  is committed as `8cddd7546`.

## Surprises & Discoveries

- Observation: `tests/unit/test_qt_signing_shell.py` already provides a fake combo-box surface with `currentIndexChanged`, `setCurrentIndex()`, and `currentText()`, so a selector-driven drill-in can be tested without adding new fake widget infrastructure.
  Evidence: `_FakeComboBox` in `tests/unit/test_qt_signing_shell.py`.

- Observation: the current review boundary already computes enough stable facts to keep the shell thin if the richer drill-in wording is produced in the application layer rather than assembled in the widget.
  Evidence: `src/foliaseal/application/document_review.py` already owns plain-language summary construction and per-signature item generation.

- Observation: the review card now exposes selector-driven per-signature detail in addition to the compact list.
  Evidence: reflected in the current `src/foliaseal/presentation/qt/signing_shell.py` workflow and this documentation refresh.

## Decision Log

- Decision: keep the drill-in inside the existing `Document review` card rather than introducing a separate dialog or review page.
  Rationale: the audit showed that the smallest meaningful move toward `inspect existing signatures` is a focused drill-in on top of the existing review card. A new seam would increase scope and coordination cost without buying enough user value for this slice.
  Date/Author: 2026-05-22 / Codex

- Decision: use a selector-based drill-in, not an always-expanded block for every signature.
  Rationale: an always-expanded list would bloat the card for multi-signature PDFs, while a selector keeps the shell compact and still makes one signature’s details immediately visible.
  Date/Author: 2026-05-22 / Codex

- Decision: keep the application layer responsible for plain-language drill-in wording.
  Rationale: `document_review.py` already owns the user-facing review language. Keeping detailed wording there prevents `signing_shell.py` from becoming the second place where verification language is synthesized.
  Date/Author: 2026-05-22 / Codex

## Outcomes & Retrospective

The implemented outcome is that the review card supports an explicit “inspect one signature” workflow without leaving the card, without creating new review windows, and without widening local verification claims beyond the current “verified locally” wording. This section remains a living retrospective and should be updated again only if a future follow-on changes the user-visible flow.

## Context and Orientation

The read-only review boundary lives in `src/foliaseal/application/document_review.py`. It exposes `DocumentReviewSummary`, which carries the top-level review state for the currently open PDF, and `DocumentSignatureReviewItem`, which now carries the compact list line plus the drill-in detail payload for each embedded signature. `PyHankoDocumentReviewInspector.inspect()` is the concrete adapter that reads the PDF, walks `reader.embedded_signatures`, and generates those payloads.

The Qt review surface lives in `src/foliaseal/presentation/qt/signing_shell.py`. `SigningWorkspaceWidget.refresh_document_review()` calls the inspector and writes the current `Document review` controls. The card holds a headline label, a detail label, a compact list label, a selector for choosing one signature, a drill-in detail label for the selected signature, and a `Verify signed PDF` button.

The relevant tests are `tests/unit/test_document_review.py` and `tests/unit/test_qt_signing_shell.py`. The document-review tests prove unsigned, signed, restricted, missing-file, and multi-signature review behavior. The shell tests prove that an injected review summary populates the current card, that the selector changes the drill-in detail, and that the review-card verify button reuses the existing reopen path.

In this plan, a “drill-in” means a read-only detail block for one selected embedded signature. It is not a certificate-chain browser, not a trust-policy report, and not a timestamp diagnostics view. The implemented drill-in explains three things in plain language: who the signer is when known, what FoliaSeal’s local cryptographic verification concluded for that signature, and what current document restrictions or permissions matter for additional signing.

## Plan of Work

`src/foliaseal/application/document_review.py` carries both the compact list line and the richer plain-language drill-in payload on `DocumentSignatureReviewItem`. The helper that builds that text stays close to the current signature facts and document certification facts. `PyHankoDocumentReviewInspector.inspect()` continues to summarize the latest signature at the top level and produces a richer drill-in payload for every embedded signature in order.

`src/foliaseal/presentation/qt/signing_shell.py` extends `DocumentReviewControls` and `_build_document_review_controls()` with a combo box for choosing the active signature detail and a label for displaying the selected item’s drill-in text. `refresh_document_review()` populates the selector from `summary.signature_items`, preserves a sensible default selection, and renders the current selected detail. When there are no signature items, the selector and drill-in label stay empty or disabled without affecting the existing top-level summary behavior. The `Verify signed PDF` button keeps its current behavior.

The test suite already reflects the selector-based drill-in. `tests/unit/test_document_review.py` covers the richer drill-in text ordering for multiple signatures and the plain-language verification wording. `tests/unit/test_qt_signing_shell.py` covers selector-driven shell rendering, including switching the selected signature and proving that the drill-in label updates to the selected item. The existing verify-button delegation test and current compact-list assertions remain in place.

The documentation review for this slice is already reflected in `docs/ARCHITECTURE.md` and this plan. If a future code change re-opens the slice, run the same compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this plan. Do not change `docs/SPEC.md`; it is frozen unless the user explicitly approves a spec edit.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

Before editing, inspect the current review boundary and shell review card when the slice needs to be reopened:

    sed -n '1,260p' src/foliaseal/application/document_review.py
    sed -n '1995,2465p' src/foliaseal/presentation/qt/signing_shell.py
    sed -n '1,260p' tests/unit/test_document_review.py
    sed -n '995,1495p' tests/unit/test_qt_signing_shell.py

After adjusting the richer item payload, selector-driven shell rendering, or related tests, run:

    pytest tests/unit/test_document_review.py tests/unit/test_qt_signing_shell.py

Then run focused lint:

    ruff check src/foliaseal/application/document_review.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_document_review.py tests/unit/test_qt_signing_shell.py

Finally check patch hygiene:

    git diff --check

If compliance review requires documentation changes, rerun the focused checks and record the final passing commands here before committing.

## Validation and Acceptance

Acceptance is behavioral. The implemented slice lets a user opening a signed PDF with multiple embedded signatures choose a signature in the `Document review` card and see a richer plain-language detail block for that selected signature without opening a dialog or leaving the current shell. The existing headline, aggregate summary, compact list, and `Verify signed PDF` action continue to work.

The proof points are:

- `tests/unit/test_document_review.py` passes and proves that the per-signature drill-in payload is generated in order, preserves existing compact-list data, and uses plain-language local-verification wording.
- `tests/unit/test_qt_signing_shell.py` passes and includes a shell-level test that changes the selected signature and proves the drill-in detail label updates accordingly.
- `ruff check` and `git diff --check` pass.

This slice is complete: the focused proofs and documentation review hold, and
the implementation is committed as `8cddd7546` without widening the trust
claims made by the current local verification path.

## Idempotence and Recovery

This feature is read-only with respect to the PDF. Refreshing the review card, changing the selected signature in the drill-in selector, and reopening the signed output must not mutate the document or the signing draft.

The changes are safe to iterate on repeatedly because they are additive and covered by focused tests. If the selector rendering becomes brittle in a future change, fall back to a deterministic first-item selection rather than introducing persistent UI state in this slice. If the richer wording starts depending on certificate-chain or timestamp facts that are not already available, stop and treat that as a follow-on slice instead of stretching this one.

## Artifacts and Notes

Historical gap evidence before the change:

    docs/SPEC.md
    - V1 still requires users to inspect existing signatures more deeply than a compact list-at-a-glance view.

    src/foliaseal/presentation/qt/signing_shell.py
    - the review card exposes the list and verify action, but no focused per-signature detail view.

Validation evidence for the implemented slice will be recorded here when this plan is next reopened for a behavior change.

## Interfaces and Dependencies

At the end of this slice, `src/foliaseal/application/document_review.py` exposes:

    @dataclass(frozen=True)
    class DocumentSignatureReviewItem:
        label: str
        signer_subject: str | None
        cryptographic_validation_passed: bool | None
        detail: str
        drill_in_detail: str

`drill_in_detail` is the plain-language string for the selector-driven detail surface. It remains honest about local verification and mentions document restrictions or permissions in the same style as the existing top-level summary.

`src/foliaseal/presentation/qt/signing_shell.py` exposes review-card controls along these lines:

    @dataclass(frozen=True)
    class DocumentReviewControls:
        container: Any
        headline_label: Any
        detail_label: Any
        signature_items_label: Any
        signature_selector: Any
        signature_detail_label: Any
        verify_button: Any

The selector uses the existing Qt binding surface (`q_combo_box`) because the test doubles already support it. The shell continues to consume the injected `DocumentReviewInspector` dependency and continues to reuse `open_signed_output()` for the verify action.

Change note: 2026-05-22 / Codex

Updated this ExecPlan to match the implemented selector-driven drill-in and to keep the document in completion-state wording without implying that the commit has already been created. The chosen scope stays inside the current review card and deliberately avoids dialogs, app-frame changes, or trust-policy expansion.
