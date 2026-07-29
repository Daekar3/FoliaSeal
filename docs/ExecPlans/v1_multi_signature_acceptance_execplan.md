# Prove reopen-and-add-another approval signature

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this change, a user can reopen FoliaSeal’s signed output, add a second visible approval signature when the document permits it, and see both signatures in the review surface. When a certification restriction forbids another signature, the user instead receives a plain-language block before output is written. This proves the release-bar behavior that the current one-signature walkthrough does not exercise.

## Child ExecPlan Dependencies

- [x] The current GUI audit can create a certificate, save/reselect a preset, sign, reopen, and close all Qt windows.
- [x] This child has no further child ExecPlans.

## Progress

- [x] (2026-07-20) Identified the gap: incremental signing and DocMDP restriction tests exist, but there is no display-backed second-signature acceptance scenario.
- [x] (2026-07-28) Re-explored the review contract: `DocumentReviewSummary` and the Qt selector/card already enumerate multiple embedded signatures; no cardinality/UI model change is needed.
- [x] (2026-07-28) Added an actual-PDF integration test proving a two-signed output produces two locally verified review items with stable `Signature 1` / `Signature 2 (latest)` labels and incremental revision strategy.
- [x] (2026-07-28) Added the failing-then-green allowed-second-signing behavior test; existing `test_certification_hardening.py` coverage already proves the DocMDP `NO_CHANGES` restriction diagnostic and no-output safety path.
- [x] (2026-07-28) Extended the isolated GUI audit with bounded non-overlapping second placement, second output/sign/reopen checkpoints, first-output preservation, and two-item mounted review assertions.
- [x] (2026-07-28) Ran focused backend/document-review/certification/Qt coverage (`231 passed`) and the display-backed acceptance audit; it passed 19 checkpoints and retained both signed outputs plus two-signature review evidence.
- [x] (2026-07-28) Completed compliance review, documentation stewardship, cleanup verification, and final plan-scope reconciliation; no code correction or child plan is needed.
- [ ] Create the dedicated multi-signature behavior/evidence commit and close the parent dependency with its commit hash.

## Surprises & Discoveries

- Observation: `SignPdfUseCase` already uses incremental revision strategy and carries DocMDP restriction facts.
  Evidence: `src/foliaseal/application/sign_pdf_use_case.py` and `tests/unit/test_certification_hardening.py`.
- Observation: the current audit verifies reopening but stops before signing the reopened output.
  Evidence: `scripts/live_gui_parent_audit.py` ends at `reopened-and-verified`.

- Observation: the Phase 3 signer hard-codes the field name `Signature1`, so a second incremental signing attempt collides with the filled field.
  Evidence: `src/foliaseal/application/phase3_signing_backend.py` uses `_SIG_FIELD_NAME = "Signature1"`; a reproduced second executor call fails with `Signature field with name Signature1 appears to be filled already.`

- Observation: the existing review model already supports all embedded signatures, but the current audit's near-full-page placement leaves no safe non-overlapping region for a second signature.
  Evidence: `DocumentReviewSummary.signature_items` and selector/card tests cover two items; `_place_signature_with_viewer_drag` currently spans almost the entire canvas.

- Observation: reopening a signed workspace resets the timestamp URL in the signing DTO even when timestamping is disabled.
  Evidence: the first live multi-signature audit failed before the second signer call with `ValueError: tsa_url must be a non-empty string`; reapplying the offline disabled-timestamp state after reopen made the audit pass.

## Decision Log

- Decision: prove both permitted and forbidden paths without adding certification-policy controls to the V1 GUI.
  Rationale: a second-signature success alone could mask unsafe behavior on a restricted PDF; the restricted case is a read-only safety diagnostic, not a new certification-management feature.
  Date/Author: 2026-07-20 / Codex

- Decision: allocate the next unused PDF signature field name for each signing request while preserving incremental revision signing.
  Rationale: pyHanko rejects filling an existing field, and using `Signature2`, `Signature3`, and so on allows ordinary approval signatures to append without changing the existing DocMDP policy path.
  Date/Author: 2026-07-28 / Codex

- Decision: use bounded, separated placement rectangles in the multi-signature audit rather than the existing full-page drag.
  Rationale: the second signature must be visibly distinct and non-overlapping; the audit should prove that through production canvas events, not by bypassing placement.
  Date/Author: 2026-07-28 / Codex

## Outcomes & Retrospective

At creation, this was unproven release-bar behavior. The implementation now allocates unused incremental field names, and the focused integration test plus 19-checkpoint live audit prove two signatures, two locally verified review items, preserved first output, and clean reopen behavior. Existing certification-hardening tests retain the restricted-case diagnostic/no-output proof; the focused run passed 231 tests, and final compliance/documentation review is complete before commit.

## Context and Orientation

An approval signature is an ordinary incremental PDF signature added after an earlier signature. “Incremental” means the original signed revision remains in the file and the new signature is appended. DocMDP is the PDF certification permission policy; `no_changes` must block signing. `FoliaSealAppFrame.open_pdf_path()` builds a fresh workspace for a PDF. `SigningWorkspaceActionBridge` owns output selection and confirmation; `SignPdfUseCase` performs signing; `DocumentReviewWorkspace` and `document_review.py` expose embedded signature information in the sidebar.

## Plan of Work

First inspect `DocumentReviewSummary.signature_count`, `signature_items`, and the selector-driven review-card rendering. Add a failing test that proves two embedded signatures become two selectable review items; if the current view is latest-only, extend the model and card before extending the audit. Then add application/Qt tests that sign a fixture twice and assert two embedded signatures, both locally valid review states, distinct output paths, and an untouched first output. The restricted safety proof intentionally remains layered: `tests/unit/test_certification_hardening.py` exercises a real `no_changes` fixture and no-output backend rejection, while `tests/unit/test_document_review.py` and `tests/unit/test_qt_signing_shell.py` prove the diagnostic and mounted next-action guidance. Extend `scripts/live_gui_parent_audit.py`: after reopening, rebind `shell = frame.current_shell` because opening the output replaces the central widget; explicitly select the stored certificate/preset again; place a non-overlapping rectangle large enough to pass content-fit validation; choose a second output; accept confirmation; sign; reopen again; and assert two review items plus valid local verification for each.

## Concrete Steps

From `/home/daekar/FoliaSeal`:

    .venv/bin/python -m pytest -q tests/unit/test_phase3_signing_backend.py tests/unit/test_sign_pdf_use_case.py tests/unit/test_certification_hardening.py tests/unit/test_document_review.py tests/unit/test_qt_signing_shell.py
    .venv/bin/ruff check scripts/live_gui_parent_audit.py src/foliaseal/application/phase3_signing_backend.py src/foliaseal/application/sign_pdf_use_case.py tests/unit
    DISPLAY=:0 timeout 240s .venv/bin/python scripts/live_gui_parent_audit.py --artifacts-dir /tmp/foliaseal-live-gui-multi-signature-audit

Expected audit JSON: `status` is `passed`; it records first-signature, reopened, second-signature, and two-signature-review checkpoints; the final signed output has signature count `2` and both locally verified review items. The restricted safety claim is validated by the named focused tests rather than by this success-path audit.

## Validation and Acceptance

Open a blank representative PDF, sign it, reopen its output, place and sign again, and reopen the second output. The review surface must identify two selectable signatures and give plain-language local verification guidance for both. Certification safety must remain proven by the existing layered tests: a real `DocMDP NO_CHANGES` fixture is rejected before output, the document-review model exposes the restriction reason, and the Qt review surface renders the plain-language next action. A separate live restricted-document chooser flow is intentionally out of scope because the restriction is enforced before the signing dialog can produce output.

## Idempotence and Recovery

Use a new `TemporaryDirectory` per audit run and two distinct output names. The runner must close every top-level Qt widget in `finally`; after each run, verify no FoliaSeal process or dialog remains. If the second sign fails, preserve its isolated artifact directory with `--keep-workspace`, record the exact result in this plan, and fix the behavior before rerunning.

## Artifacts and Notes

Retain `/tmp/foliaseal-live-gui-multi-signature-audit/audit.json`, the two signed outputs, and screenshots of both-signature review. Add only generated evidence paths or checksums to Git documentation, not private PDFs or certificates.

## Interfaces and Dependencies

Use `SignPdfUseCase`, `SigningRequest`, `DocumentReviewSummary`, `FoliaSealAppFrame.open_pdf_path()`, and the existing audit helpers. Do not bypass the app frame by calling storage or signer internals directly. Preserve `RevisionStrategy.INCREMENTAL` and existing DocMDP behavior.

Revision note: 2026-07-20 / Codex
Created as the behavior-change child of `v1_release_compliance_parent_execplan.md`.

Revision note: 2026-07-28 / Codex
Implemented dynamic unused `SignatureN` allocation, added actual-PDF two-signature review coverage, extended the isolated GUI audit through a second signing, and corrected the reopened-workspace timestamp DTO setup discovered during the first live attempt.

Revision note: 2026-07-28 / Codex
Compliance review narrowed the restricted-document acceptance wording to the existing real backend, document-review, and Qt guidance evidence; the live audit remains focused on the permitted second-signature success path.
