# Add restriction-specific next-action guidance to per-signature review drill-ins

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows `.agents/skills/write-execplan/PLANS.md` and must be maintained in accordance with that file. It is self-contained so a contributor can resume this slice from only this document and the current repository tree.

## Purpose / Big Picture

After this change, a user selecting a signature in the `Document review` card will still see the current `Recommended next step:` line for non-verified signatures, but that sentence will now change when the PDF is certification-restricted. The user-visible gain is that FoliaSeal will no longer give the same generic “reopen and review” advice whether further changes are still allowed or whether document restrictions may already block additional signing.

This slice matters because `docs/SPEC.md` requires plain-language guidance and explicit recommended next actions when possible. The current wording already recommends a next step, but it does not react to certification restrictions even though the review helper already knows those facts. This slice closes that remaining wording gap without changing the widget structure, the app frame, or the trust model.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/per_signature_review_drill_in_execplan.md` completed first so the review card already exposes a selector-driven drill-in surface.
- [x] `docs/ExecPlans/per_signature_next_action_guidance_execplan.md` completed first so non-verified signatures already carry a conservative `Recommended next step:` line.
- [ ] A later child ExecPlan may deepen review ergonomics into a dedicated restricted-document warning surface or richer trust diagnostics if sentence-level guidance remains insufficient.

## Progress

- [x] (2026-05-23T13:49:00Z) Completed the required `explorer-light` audit and fixed the target slice to certification-aware wording in the application review payload.
- [x] (2026-05-23T13:52:00Z) Reviewed the current helper and test surfaces in `src/foliaseal/application/document_review.py`, `tests/unit/test_document_review.py`, and `tests/unit/test_qt_signing_shell.py` before drafting this plan.
- [x] (2026-05-23T14:05:00Z) Added certification-aware next-action wording for non-verified signatures in the application review helper while keeping verified-local wording unchanged.
- [x] (2026-05-23T14:08:00Z) Added focused tests for restricted failed-validation guidance, restricted not-evaluated guidance, a restricted shell render-through assertion, and a regression check that restricted but locally verified signatures remain action-free.
- [x] (2026-05-23T14:10:00Z) Ran focused validation: `pytest tests/unit/test_document_review.py tests/unit/test_qt_signing_shell.py`, `ruff check src/foliaseal/application/document_review.py tests/unit/test_document_review.py tests/unit/test_qt_signing_shell.py`, and `git diff --check`.
- [x] (2026-05-23T14:13:00Z) Completed the required `explorer-light` compliance review, then closed the final verified-local regression gap and refreshed this ExecPlan to completion-state wording.
- [x] (2026-05-23) Created and recorded the implementation commit
  `4cb84e52a`; any richer review surface remains a separate follow-on.

## Surprises & Discoveries

- Observation: the current review helper already threads `certification_restricted` and `restriction_reason` into `_signature_drill_in_detail()`, so this slice does not need new low-level inspection facts.
  Evidence: `src/foliaseal/application/document_review.py` already builds a `Document restrictions:` or `Document permissions:` line before adding `Recommended next step:`.

- Observation: the Qt shell remains a pure renderer for this slice. It only displays `DocumentSignatureReviewItem.drill_in_detail`.
  Evidence: `src/foliaseal/presentation/qt/signing_shell.py` renders the current selected item detail and does not synthesize review wording.

## Decision Log

- Decision: keep the new wording in the selected-signature drill-in only, not in the top-level summary.
  Rationale: the smallest useful slice is to make the focused recommendation more context-specific. Widening the top-level summary would touch more wording contracts than necessary and would make the card noisier.
  Date/Author: 2026-05-23 / Codex

- Decision: the restriction-specific wording must remain conservative and must not imply that certification restrictions determine cryptographic validity.
  Rationale: restrictions affect whether further changes may be allowed, not whether the signature itself is valid. The guidance should mention possible blocking of further changes without conflating the two concepts.
  Date/Author: 2026-05-23 / Codex

## Outcomes & Retrospective

The implemented outcome is that a selected signature on a certification-restricted PDF now receives different practical advice than one on an unrestricted PDF, while the rest of the review surface stays unchanged. The drill-in guidance remains conservative: it does not imply that certification restrictions determine cryptographic validity, and it does not describe the reopen action as a cryptographic verification engine.

The only follow-up found during compliance review was a missing regression assertion for the restricted-but-verified-local case. That gap was closed locally by proving that verified-local restricted signatures still do not receive a `Recommended next step:` line.

## Context and Orientation

The review wording boundary lives in `src/foliaseal/application/document_review.py`. `DocumentSignatureReviewItem` carries `drill_in_detail`, the ready-to-render plain-language string that the shell shows for the currently selected signature. `_signature_drill_in_detail()` builds that string from four classes of facts that are already available in the application layer: signer information, local cryptographic-verification outcome, document permission or restriction status, and the current next-action helper. `_signature_next_action_guidance()` currently only looks at `cryptographic_validation_passed`, which means it gives the same recommendation for restricted and unrestricted PDFs.

The review UI lives in `src/foliaseal/presentation/qt/signing_shell.py`, but it should not change for this slice. The shell already renders the selected signature’s `drill_in_detail` text and should remain passive. The current tests that matter most live in `tests/unit/test_document_review.py` and `tests/unit/test_qt_signing_shell.py`. Those tests already cover unrestricted failed-validation guidance and unrestricted not-evaluated guidance. This slice should add the missing restricted variants.

In this plan, “restriction-specific next-action guidance” means that the `Recommended next step:` line changes when `certification_restricted` or `restriction_reason` is present. For example, a restricted PDF should nudge the user to reopen the signed PDF, review the selected signature details, and be aware that further changes may be blocked. An unrestricted PDF should keep the current generic review-again guidance. The wording must remain honest about what the current product actually does and must not imply a stronger verification engine than exists today.

## Plan of Work

Start in `src/foliaseal/application/document_review.py`. Update `_signature_next_action_guidance()` so it accepts certification restriction inputs in addition to `cryptographic_validation_passed`. Use those new inputs to branch the non-verified guidance text into two families: unrestricted and restricted. Then update `_signature_drill_in_detail()` to pass the existing restriction facts into that helper. Keep the signer line, verification line, compact-list `detail`, and permissions or restrictions line unchanged.

Next, update `tests/unit/test_document_review.py`. Add one restricted failed-validation assertion and one restricted not-evaluated assertion that exercise the real helper path instead of only manually constructed fixture text. Then update `tests/unit/test_qt_signing_shell.py` with one injected restricted-signature fixture and one rendered-detail assertion so the shell proves it displays the new wording through the existing drill-in surface.

After the behavior is green, run the required compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this plan. If the wording change makes `docs/ARCHITECTURE.md` stale, update it. Do not change `docs/SPEC.md`; it is frozen unless the user explicitly approves a spec edit.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

Before editing, inspect the current helper and tests:

    sed -n '200,340p' src/foliaseal/application/document_review.py
    sed -n '1,260p' tests/unit/test_document_review.py
    sed -n '1100,1305p' tests/unit/test_qt_signing_shell.py

After updating the helper and tests, run:

    pytest tests/unit/test_document_review.py tests/unit/test_qt_signing_shell.py

Then run focused lint:

    ruff check src/foliaseal/application/document_review.py tests/unit/test_document_review.py tests/unit/test_qt_signing_shell.py

Finally check patch hygiene:

    git diff --check

If compliance review requires documentation changes, rerun the focused checks and record the final passing commands here before committing.

## Validation and Acceptance

Acceptance is behavioral. After this change, selecting a signature on a certification-restricted PDF must show a different `Recommended next step:` sentence than selecting a similar non-verified signature on an unrestricted PDF. Verified-local signatures must remain unchanged and should not gain warning or action text.

The proof points are:

- `tests/unit/test_document_review.py` passes and proves the restriction-aware guidance for `cryptographic_validation_passed=False` and `None`.
- `tests/unit/test_qt_signing_shell.py` passes and proves that the selected signature detail label renders the restricted next-action wording.
- `ruff check` and `git diff --check` pass.

This slice is complete when those proofs hold and the compliance review confirms that the wording is more context-specific without widening the trust semantics.

## Idempotence and Recovery

This feature is read-only with respect to the PDF. Updating the selected signature guidance wording must not mutate the document, the signing draft, or the reopen path.

The changes are safe to repeat because they are additive and covered by focused tests. If the wording starts to overfit one restriction case or imply more certainty than the current review helper actually has, simplify it back to a conservative sentence rather than creating a broader warning framework in this slice.

## Artifacts and Notes

Historical gap evidence before the change:

    src/foliaseal/application/document_review.py
    - the next-action helper is status-aware but not restriction-aware, so restricted and unrestricted PDFs get the same recommendation.

    docs/SPEC.md
    - V1 requires explicit recommended next actions when possible.

Validation evidence after implementation:

    pytest tests/unit/test_document_review.py tests/unit/test_qt_signing_shell.py
    - 80 passed

    ruff check src/foliaseal/application/document_review.py tests/unit/test_document_review.py tests/unit/test_qt_signing_shell.py
    - all checks passed

    git diff --check
    - passed

## Interfaces and Dependencies

At the end of this slice, `src/foliaseal/application/document_review.py` should still expose:

    @dataclass(frozen=True)
    class DocumentSignatureReviewItem:
        label: str
        signer_subject: str | None
        cryptographic_validation_passed: bool | None
        detail: str
        drill_in_detail: str

The only intended behavior change is in the contents of `drill_in_detail` for non-verified restricted signatures. `signing_shell.py` should remain a pure renderer of that string and should not gain new review-state branching for this slice.

Change note: 2026-05-23 / Codex

Created this ExecPlan from the required `explorer-light` audit for the next narrow review-wording slice. The chosen scope stays inside the existing application review payload and deliberately avoids new controls, app-frame changes, or trust-policy expansion.

Change note: 2026-05-23 / Codex

Updated this ExecPlan after implementation and compliance review so the progress log, retrospective, and validation evidence match the completed restriction-aware guidance behavior committed as `4cb84e52a`.
