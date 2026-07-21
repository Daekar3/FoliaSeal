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
- [ ] Locate the `DocumentReviewSummary` cardinality/UI contract and add a targeted failing test before assuming two review rows are already rendered.
- [ ] Add failing behavior tests for allowed second signing and an existing read-only restriction diagnostic on a restricted document.
- [ ] Extend the isolated GUI audit with a second-signature scenario and stable checkpoints.
- [ ] Run focused tests and the display-backed acceptance audit; inspect two signatures and local review text.
- [ ] Perform compliance review, reconcile docs, verify cleanup, and commit.

## Surprises & Discoveries

- Observation: `SignPdfUseCase` already uses incremental revision strategy and carries DocMDP restriction facts.
  Evidence: `src/foliaseal/application/sign_pdf_use_case.py` and `tests/unit/test_certification_hardening.py`.
- Observation: the current audit verifies reopening but stops before signing the reopened output.
  Evidence: `scripts/live_gui_parent_audit.py` ends at `reopened-and-verified`.

## Decision Log

- Decision: prove both permitted and forbidden paths without adding certification-policy controls to the V1 GUI.
  Rationale: a second-signature success alone could mask unsafe behavior on a restricted PDF; the restricted case is a read-only safety diagnostic, not a new certification-management feature.
  Date/Author: 2026-07-20 / Codex

## Outcomes & Retrospective

At creation, this is unproven release-bar behavior. At completion, record the two-signature count, review-card evidence, restricted-case message, and all cleanup checks.

## Context and Orientation

An approval signature is an ordinary incremental PDF signature added after an earlier signature. “Incremental” means the original signed revision remains in the file and the new signature is appended. DocMDP is the PDF certification permission policy; `no_changes` must block signing. `FoliaSealAppFrame.open_pdf_path()` builds a fresh workspace for a PDF. `SigningWorkspaceActionBridge` owns output selection and confirmation; `SignPdfUseCase` performs signing; `DocumentReviewWorkspace` and `document_review.py` expose embedded signature information in the sidebar.

## Plan of Work

First inspect `DocumentReviewSummary.signature_count`, `signature_items`, and the selector-driven review-card rendering. Add a failing test that proves two embedded signatures become two selectable review items; if the current view is latest-only, extend the model and card before extending the audit. Then add application/Qt tests that sign a fixture twice and assert two embedded signatures, both locally valid review states, distinct output paths, and an untouched first output. Reuse `tests/support/certification_fixtures.py` for a `no_changes` input and assert the mounted sign action is disabled or its visible pre-submit error names the restriction, with no second output written. Extend `scripts/live_gui_parent_audit.py`: after reopening, rebind `shell = frame.current_shell` because opening the output replaces the central widget; explicitly select the stored certificate/preset again; place a non-overlapping rectangle large enough to pass content-fit validation; choose a second output; accept confirmation; sign; reopen again; and assert two review items plus valid local verification for each. Do not drive a native chooser in the restricted scenario.

## Concrete Steps

From `/home/daekar/FoliaSeal`:

    .venv/bin/python -m pytest -q tests/unit/test_sign_pdf_use_case.py tests/unit/test_certification_hardening.py tests/unit/test_document_review.py tests/unit/test_qt_signing_shell.py
    .venv/bin/ruff check scripts/live_gui_parent_audit.py src/foliaseal/application/sign_pdf_use_case.py tests/unit
    DISPLAY=:0 timeout 240s .venv/bin/python scripts/live_gui_parent_audit.py --artifacts-dir /tmp/foliaseal-live-gui-multi-signature-audit

Expected audit JSON: `status` is `passed`; it records first-signature, reopened, second-signature, and two-signature-review checkpoints; the final signed output has signature count `2` and both locally verified review items.

## Validation and Acceptance

Open a blank representative PDF, sign it, reopen its output, place and sign again, and reopen the second output. The review surface must identify two selectable signatures and give plain-language local verification guidance for both. A certification-restricted fixture must disable signing or display the existing restriction diagnostic before submission; no extra output may be produced.

## Idempotence and Recovery

Use a new `TemporaryDirectory` per audit run and two distinct output names. The runner must close every top-level Qt widget in `finally`; after each run, verify no FoliaSeal process or dialog remains. If the second sign fails, preserve its isolated artifact directory with `--keep-workspace`, record the exact result in this plan, and fix the behavior before rerunning.

## Artifacts and Notes

Retain `/tmp/foliaseal-live-gui-multi-signature-audit/audit.json`, the two signed outputs, and screenshots of both-signature review. Add only generated evidence paths or checksums to Git documentation, not private PDFs or certificates.

## Interfaces and Dependencies

Use `SignPdfUseCase`, `SigningRequest`, `DocumentReviewSummary`, `FoliaSealAppFrame.open_pdf_path()`, and the existing audit helpers. Do not bypass the app frame by calling storage or signer internals directly. Preserve `RevisionStrategy.INCREMENTAL` and existing DocMDP behavior.

Revision note: 2026-07-20 / Codex
Created as the behavior-change child of `v1_release_compliance_parent_execplan.md`.
