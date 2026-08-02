# Correct interactive signing-attempt artifact numbering

This child ExecPlan is a living document maintained in accordance with `.agents/skills/write-execplan/PLANS.md`. It addresses the concrete high-risk finding from the parent interactive-capture extraction review before the parent slice is committed.

## Purpose / Big Picture

The interactive session runner increments the sign-request list before calculating the next output filename and then adds one again. As a result, the first signing attempt is named `_002` instead of `_001`, and every later attempt is offset. This violates the parent plan's requirement to preserve intentional artifact naming semantics and makes the newly isolated artifact policy misleading.

The fix is a one-line behavioral correction plus a regression test that records the requested attempt index. It must not change matrix lifecycles, capture JSON, report fields, or Qt cleanup behavior.

## Child ExecPlan Dependencies

- [x] Parent plan implemented the focused interactive-capture module and migrated its tests.
- [x] High-risk review reproduced the off-by-one attempt index; no other matrix or evidence discrepancy was found.

## Progress

- [x] (2026-08-01) Recorded the high-risk finding and created this child plan before the corrective edit.
- [x] (2026-08-01) Changed `Phase3HarnessSessionRunner.on_sign_request()` to pass the current one-based request count without adding one twice.
- [x] (2026-08-01) Added a focused regression assertion for first-attempt artifact naming; focused session/harness tests pass (`85 passed`, one pre-existing Pillow warning).
- [x] (2026-08-01) Repeated compliance/high-risk review found no further defects; reconciled parent/child documentation and recorded the artifact-index correction. The focused commit remains with the parent plan.

## Surprises & Discoveries

- Observation: Existing tests exercised sign-request capture but never asserted the output path attempt index.
  Evidence: the high-risk review found `len(sign_requests) + 1` after `sign_requests.append(request)` at `phase3_harness_session_runner.py`.
- Observation: Window cleanup for setup exceptions occurs before the existing event-loop `try/finally` and is inherited behavior, not introduced by this extraction.
  Resolution: do not broaden this child into a Qt lifecycle redesign; record it as a separate future seam unless a focused reproducible failure requires it.

## Decision Log

- Decision: Correct only the attempt-number arithmetic and add a direct regression assertion.
  Rationale: this restores the established one-based naming contract with minimal risk and keeps the child bounded.
  Date/Author: 2026-08-01 / Codex.

## Outcomes & Retrospective

The off-by-one artifact index is corrected and covered by a focused regression assertion. Repeated compliance/high-risk review and parent/child documentation reconciliation are complete; the focused commit remains with the parent plan.

## Context and Orientation

`Phase3HarnessSessionRunner.run()` in `src/foliaseal/presentation/qt/phase3_harness_session_runner.py` collects signing requests in `sign_requests`. Its `on_sign_request()` callback updates `SigningDraftWorkflow.output_pdf_path` through the injected `default_harness_output_pdf_path` function. Because the append occurs before path calculation, the correct first attempt index is `len(sign_requests)`, not `len(sign_requests) + 1`.

## Plan of Work

Change the callback to pass `sign_attempt_index=len(sign_requests)`. In `tests/unit/test_phase3_harness_session_runner.py`, record the indices received by the fake output-path helper and assert the first sign request receives `1` (and, if the fixture triggers another request, the next receives `2`). Keep all existing window cleanup and capture assertions unchanged.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    .venv/bin/python -m pytest -q tests/unit/test_phase3_harness_session_runner.py tests/unit/test_phase3_harness.py
    .venv/bin/ruff check src tests
    git diff --check
    .venv/bin/python -m pytest -q

Then rerun both release-fidelity matrices from the parent plan, remove only their temporary directories, and verify no FoliaSeal/Phase 3 process remains.

## Validation and Acceptance

The first interactive signing request must select `_001` output naming, subsequent requests must advance by one, and all existing focused/full/matrix tests must remain green. No CLI, JSON, summary, or matrix behavior may change.

## Idempotence and Recovery

The edit is deterministic and safe to rerun. If a test reveals a fixture that intentionally expects another index, update only the fixture's explicit expectation after comparing the pre-fix behavior; do not restore the double increment.

## Artifacts and Notes

    high-risk finding: first sign request used attempt index 2
    corrected attempt index: 1-based request count
    focused tests: 85 passed (one pre-existing Pillow warning)
    full suite: 1040 passed (one pre-existing Pillow warning)
    child commit: included in parent focused commit; not committed separately

## Interfaces and Dependencies

The existing `Phase3HarnessSessionRunnerDeps.default_harness_output_pdf_path` callable remains the only artifact-path dependency. No new public interface is introduced.

## Change-Slice Boundary

Allowed changes are the attempt-index arithmetic, its focused regression assertion, parent/child plan updates, and validation evidence. Forbidden changes include Qt lifecycle redesign, matrix runner changes, evidence schema changes, signing semantics, or broad cleanup unrelated to artifact numbering.

Plan revision note: created 2026-08-01 after the required high-risk review reproduced the artifact-numbering discrepancy.
