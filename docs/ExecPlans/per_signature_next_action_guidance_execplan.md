# Add plain-language next-action guidance to per-signature review drill-ins

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows `.agents/skills/write-execplan/PLANS.md` and must be maintained in accordance with that file. It is self-contained so a contributor can resume this slice from only this document and the current repository tree.

## Purpose / Big Picture

This slice is now implemented in the working tree. A user selecting a signature in the `Document review` card sees the signer, the local verification status, and the document restriction or permission summary, and signatures that are not clearly verified locally also include one explicit next-action line in plain language. Verified signatures do not gain extra action text.

This slice matters because `docs/SPEC.md` requires plain-language verification guidance and recommends explicit next actions when possible. The application-layer helper already closes that wording gap without expanding the trust model, the app frame, or the UI surface. The remaining work in this document is to keep the architecture and plan text synchronized with that shipped behavior.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/per_signature_review_reopen_execplan.md` completed first so the review card already exposes a compact per-signature list and reopen-and-verify action.
- [x] `docs/ExecPlans/per_signature_review_drill_in_execplan.md` completed first so the review card already exposes a selector-driven drill-in surface for one signature.
- [ ] A later child ExecPlan may deepen review ergonomics into richer trust diagnostics or a dedicated signature browser if one guidance line per signature still proves insufficient.

## Progress

- [x] (2026-05-23T13:15:00Z) Completed the required `explorer-light` audit and fixed the target slice to status-sensitive next-action wording inside the existing per-signature drill-in.
- [x] (2026-05-23T13:18:00Z) Reviewed `docs/SPEC.md`, `src/foliaseal/application/document_review.py`, and the current review-card tests before drafting this plan.
- [x] (2026-05-23T16:52:46Z) Confirmed the working tree already includes the status-sensitive `Recommended next step:` line in `DocumentSignatureReviewItem.drill_in_detail`.
- [x] (2026-05-23T16:52:46Z) Updated `docs/ARCHITECTURE.md` so the document-review summary/drill-in contract matches the current implementation.
- [x] (2026-05-23T16:52:46Z) Revised this ExecPlan so the progress and outcome wording describe the shipped behavior without claiming the commit is finished.
- [ ] Create the commit for this slice.

## Surprises & Discoveries

- Observation: the right seam is still the application review boundary, not the widget. `signing_shell.py` already renders `drill_in_detail` directly and should not become a second place where trust-sensitive wording is assembled.
  Evidence: `src/foliaseal/presentation/qt/signing_shell.py` only selects and displays the current `DocumentSignatureReviewItem.drill_in_detail`.

- Observation: `_verify_signature_locally()` already distinguishes `False` from `None`, which gives this slice two separate guidance branches without needing new low-level review facts.
  Evidence: `src/foliaseal/application/document_review.py` returns `False` on verification exception/failure and `None` when no signer certificate is available.

- Observation: the application helper already appends a `Recommended next step:` line for non-verified signatures, so this pass is documentation synchronization rather than new behavior.
  Evidence: `_signature_drill_in_detail()` calls `_signature_next_action_guidance()` and only appends the extra line when that helper returns a string.

## Decision Log

- Decision: keep the new guidance in the selected signature drill-in only, not in the top-level review summary.
  Rationale: the smallest useful slice is to improve the focused signature detail that the user has already selected. Widening the top-level summary would touch more wording contracts than necessary and make the review card noisier.
  Date/Author: 2026-05-23 / Codex

- Decision: do not imply that the existing `Verify signed PDF` button performs cryptographic verification by itself.
  Rationale: that button reopens the signed output through the app-frame callback. The new guidance can suggest reopening and reviewing again, but it must not describe the button as a trust-engine action it does not perform.
  Date/Author: 2026-05-23 / Codex

- Decision: treat the implementation as complete in the working tree and use this pass to synchronize documentation.
  Rationale: the current code already appends next-action guidance in `drill_in_detail`; the remaining high-value work for this slice is to keep the architecture and execplan prose aligned with the actual behavior.
  Date/Author: 2026-05-23 / Codex

## Outcomes & Retrospective

The intended outcome has been achieved in the working tree: non-verified signatures no longer leave the user at a dead end, because the selected signature detail now states one concrete, plain-language next step that fits the current local-verification outcome without overstating trust or inventing new review workflows. This documentation pass brought `docs/ARCHITECTURE.md` and this ExecPlan back into sync with that implementation. The remaining open item is the commit.

## Context and Orientation

The review wording boundary lives in `src/foliaseal/application/document_review.py`. `DocumentSignatureReviewItem` carries two user-facing strings: `detail` for the compact list line and `drill_in_detail` for the selector-driven signature detail area. `_signature_drill_in_detail()` already assembles the selected signature’s text from signer information, the local cryptographic-verification result, the document certification guidance, and a conservative next-action line for `False` and `None`. The documentation in this slice should describe that current payload shape, not a future one.

The Qt review card lives in `src/foliaseal/presentation/qt/signing_shell.py`. The shell exposes the selector and detail label, but it does not synthesize review wording. For this slice, the shell should only need to render the updated `drill_in_detail` output. The app frame in `src/foliaseal/presentation/qt/app_frame.py` does not need changes because the existing reopen callback is already wired, and the new guidance text can reference reopening/reviewing without adding a new command path.

The relevant tests are `tests/unit/test_document_review.py` and `tests/unit/test_qt_signing_shell.py`. Those files already exercise the current behavior in the working tree. This plan keeps the documentation honest about the current contract rather than describing future test work.

In this plan, “next-action guidance” means one short sentence that tells the user what to do next when FoliaSeal cannot honestly say “verified locally.” For `False`, that likely means reopening the signed PDF and reviewing the signature details carefully before relying on it. For `None`, that likely means reopening the signed PDF and checking the embedded signer information because local verification was not evaluated. The exact wording should stay conservative and must not imply external trust validation, certificate-chain validation, or a stronger verification feature than the current product provides.

## Plan of Work

Update `docs/ARCHITECTURE.md` so the `Document review summary` section, the `DocumentSignatureReviewItem` row, and the `DocumentReviewSummary` row explicitly say that drill-in detail includes status-sensitive next-action guidance for non-verified states. Keep the description of the top-level summary compact and latest-signature oriented.

Update this ExecPlan so the living sections match the current tree: the progress list should show the implementation as already present, the surprises log should note the shipped `Recommended next step:` line, and the outcomes section should summarize the now-correct behavior without claiming the commit is complete.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

Before editing, inspect the current review wording and tests:

    sed -n '1,320p' src/foliaseal/application/document_review.py
    sed -n '1,220p' tests/unit/test_document_review.py
    sed -n '1040,1305p' tests/unit/test_qt_signing_shell.py

After the documentation refresh, verify the diff is limited to the two doc files and that whitespace is clean:

    git diff --check
    git diff -- docs/ARCHITECTURE.md docs/ExecPlans/per_signature_next_action_guidance_execplan.md

## Validation and Acceptance

Acceptance is documentation accuracy. The architecture doc should say that `DocumentSignatureReviewItem.drill_in_detail` includes a conservative `Recommended next step:` line for non-verified signatures, while the plan should no longer describe that wording as pending implementation. The only remaining incomplete item should be the commit itself.

No runtime tests are expected for this documentation-only refresh.

## Idempotence and Recovery

This refresh is safe to repeat because it only changes prose. If the wording drifts again, rerun the same doc edits and make sure the plan still distinguishes between the shipped behavior and the not-yet-performed commit.

## Artifacts and Notes

Historical gap evidence before the change:

    src/foliaseal/application/document_review.py
    - `DocumentSignatureReviewItem.drill_in_detail` already appends `Recommended next step:` for non-verified signatures.

    docs/SPEC.md
    - V1 requires plain-language guidance and recommended next actions when possible.

    docs/ARCHITECTURE.md
    - the summary/drill-in contract needed to be brought back in line with the shipped behavior.

Validation evidence after the refresh will be recorded here.

## Interfaces and Dependencies

At the end of this slice, `src/foliaseal/application/document_review.py` still exposes:

    @dataclass(frozen=True)
    class DocumentSignatureReviewItem:
        label: str
        signer_subject: str | None
        cryptographic_validation_passed: bool | None
        detail: str
        drill_in_detail: str

The intended behavior is that `drill_in_detail` includes a next-action line only for non-verified states. `signing_shell.py` remains a pure renderer of that string and does not gain new review-state branching for this slice.

Change note: 2026-05-23 / Codex

Revised this ExecPlan after confirming the application-layer implementation is already present in the working tree. The earlier plan text was still written as if the next-action guidance was pending; this update keeps the document aligned with the shipped behavior while leaving the commit itself open.
