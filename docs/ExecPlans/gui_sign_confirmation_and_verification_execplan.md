# GUI sign confirmation and verification recovery

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this change, a user will encounter an unmistakable final confirmation/review state before the PDF is signed, and after signing they will be guided through reopening and verifying the result in plain language. The visible win is that `Confirm and sign` becomes part of a complete, trustworthy end-user story instead of a direct submit button with an incomplete post-sign follow-up.

## Child ExecPlan Dependencies

- [x] (2026-07-13 00:00Z) This child has no further child ExecPlans. Keep the slice on confirmation, post-sign reopen, verification guidance, and acceptance evidence.

## Progress

- [x] (2026-07-13 00:00Z) Confirmed from the reviewed audit that the current GUI does not yet prove a full explicit confirmation/review state and does not yet document a complete plain-language verify path.
- [x] (2026-07-18) Defined a final modal confirmation at the shell edge, immediately before submission.
- [x] (2026-07-18) The confirmation summarizes the output, active certificate, active preset or current-document custom setup, and irreversible effect; declining it submits no request.
- [x] (2026-07-18) The signed stage now directs users to reopen the output, inspect local verification, retain trust caveats, and add an approval signature only when document permissions permit it.
- [x] (2026-07-18) Focused integrated coverage passed (163 tests) and architecture documentation was reconciled.
- [ ] Validate the complete pre-sign/post-sign story in the representative-PDF GUI audit. Pending because this run has no display-backed evidence.

## Surprises & Discoveries

- Observation: the current sign panel already has a stage model, so this slice should deepen that model instead of replacing it.
  Evidence: `src/foliaseal/presentation/qt/signing_action_coordinator.py` already computes stages such as `Place signature`, `Review preview`, `Confirm/sign`, and `Signed`.

## Decision Log

- Decision: keep this slice focused on visible confirmation and verification behavior, not on reusable-object creation or certificate-selection semantics.
  Rationale: those other behaviors are prerequisites, but mixing them here would obscure whether the confirmation and verify story is actually fixed.
  Date/Author: 2026-07-13 / Codex

## Outcomes & Retrospective

The confirmation and post-sign guidance are implemented and covered by the focused
shell suite. The final live walkthrough remains an explicit outstanding acceptance
artifact rather than an assumed result.

## Context and Orientation

The current sign panel is rendered by `src/foliaseal/presentation/qt/signing_workspace_sidebar.py`, and its state is computed by `src/foliaseal/presentation/qt/signing_action_coordinator.py`. Output-path dialogs and sign-submit glue live in `src/foliaseal/presentation/qt/signing_workspace_action_bridge.py`. The signing workflow itself is backed by `src/foliaseal/application/signing_draft_workflow.py`, and document-review state after reopening is mediated through the review workspace and bridge modules under `src/foliaseal/presentation/qt/` plus `src/foliaseal/application/document_review.py`.

Today, the stage model already says `Confirm/sign` when the draft is ready, but the audit did not find a distinct, unmistakable final confirmation state or a complete plain-language verify walkthrough. In plain language: users need one obvious moment where the app says “here is exactly what will happen and what signing objects are active,” followed by an equally obvious “here is how to inspect and understand the signed result.”

## Plan of Work

First, define the final confirmation surface. That can be a dedicated dialog or a dedicated sidebar state, but it must be unmistakably different from ordinary editing. It must show the active certificate configuration, the active preset or current-document setup name, the output target, readiness caveats, and the preview as the primary visual anchor. The actual irreversible submit should happen only from that state.

Second, clarify the post-sign story. After a successful sign, the app should make the next actions visible: reopen the signed PDF, inspect the document review panel, and understand the verification summary in plain language. If document permissions allow adding another approval signature later, the GUI should say so plainly rather than leaving the user to infer it from internal review details.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Re-read the current sign-state and sign-bridge code.

       sed -n '1,260p' src/foliaseal/presentation/qt/signing_action_coordinator.py
       sed -n '1,220p' src/foliaseal/presentation/qt/signing_workspace_action_bridge.py
       sed -n '260,420p' src/foliaseal/presentation/qt/signing_workspace_sidebar.py

2. Re-read the review/verification surfaces.

       sed -n '1,240p' src/foliaseal/application/document_review.py
       sed -n '1,260p' src/foliaseal/presentation/qt/signing_workspace_review_bridge.py

3. Implement the confirmation plus verification flow and run focused tests.

       .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py -k "signing_action or sign_success or verification or open_signed"

4. Validate manually in the live GUI.

       .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf

   Expected result: the user reaches a clear final confirmation state before the file is signed, then can reopen the signed PDF and follow plain-language verification guidance immediately afterward.

## Validation and Acceptance

Acceptance is behavioral. A user should be able to tell when they are merely editing the draft and when they are at the final confirmation step. That confirmation step must summarize the active signing objects and output target in plain language. After a successful sign, the app must guide the user to reopen and inspect the result, and the reopened review state must communicate verification honestly and understandably. Focused tests must pass, and a live walkthrough must prove the full pre-sign and post-sign path.

## Idempotence and Recovery

Keep the current sign path working while introducing the new confirmation surface. If the new confirmation state is added behind a temporary feature branch in the UI flow, make sure ordinary draft editing still works and that the sign request is built exactly once. If the verify story is partially complete, prefer additive hints and reopen affordances over removing the existing `Open signed PDF` path.

## Artifacts and Notes

The motivating findings for this slice are in:

    .tmp/gui_findings_and_fix_plan_2026-07-13.md

The critical proof point is that the GUI must no longer rely on implicit understanding at the moment of signing or immediately after it.

## Interfaces and Dependencies

The key presentation files are `src/foliaseal/presentation/qt/signing_workspace_sidebar.py`, `src/foliaseal/presentation/qt/signing_action_coordinator.py`, `src/foliaseal/presentation/qt/signing_workspace_action_bridge.py`, and the review bridge modules. The application-layer inputs come from `src/foliaseal/application/signing_draft_workflow.py` and `src/foliaseal/application/document_review.py`. Reuse the existing stage-state model rather than inventing an unrelated confirmation subsystem. The main allowed change class is behavior change, followed by focused evidence refresh and documentation updates.

Revision note: 2026-07-13 / Codex
Created this ExecPlan from the reviewed GUI audit because the current sign panel does not yet provide a full explicit confirmation/review state or a complete post-sign verification story.
