# Reconcile Phase 3 PDF evidence extraction compliance

This child ExecPlan is a living document maintained under `.agents/skills/write-execplan/PLANS.md`. It addresses the findings from the initial compliance review of `phase3_pdf_evidence_deep_module_execplan.md` and must be completed before the parent slice is committed.

## Purpose / Big Picture

The new signed-PDF evidence module must be behavior-preserving, directly tested at its public boundary, and accurately represented in the architecture documentation. This follow-up adds the missing malformed/unsigned/appearance boundary coverage, restores exact legacy fallback behavior where the extraction changed it, and reconciles documentation references to deleted helpers.

## Child ExecPlan Dependencies

- [x] Parent implementation created `Phase3PdfSignatureSnapshotter` and migrated production wiring.
- [x] Initial focused tests and full suite pass before this follow-up.

## Progress

- [x] (2026-08-01) Recorded initial compliance findings before making follow-up edits.
- [x] (2026-08-01) Restored exact malformed-input fallback behavior and added missing/unsigned/malformed direct boundary tests.
- [x] (2026-08-01) Updated architecture and parent-plan references; README requires no change because no user-facing ownership/contract statement was stale.
- [x] (2026-08-01) Re-ran the full suite (`1040 passed`, one pre-existing Pillow warning), focused evidence tests, both release-fidelity matrices, structural cleanup, and process cleanup.
- [x] (2026-08-01) Completed the final independent compliance and high-risk re-reviews; removed the unused signed-run forwarding wrapper and reconciled stale historical references.
- [ ] (2026-08-01) Create the parent-slice commit and verify the checkout is clean.

## Surprises & Discoveries

- Observation: The extraction changed `_snapshot_pdf_numeric` from broad exception handling to narrower exceptions.
  Resolution required: preserve the previous broad `Exception` behavior because malformed pyHanko values are part of the evidence adapter's safe-error contract.
- Observation: Architecture documentation names deleted harness-private helpers as current collaborators.
  Resolution required: describe `Phase3PdfSignatureSnapshotter` and bound methods instead.
- Observation: The high-risk review identified recursive AP-state/hex-text parsing and timestamp-presence semantics as broader inherited evidence debt, not extraction regressions.
  Decision: Preserve the existing evidence contract in this extraction, add malformed/unsigned coverage, and record recursive AP parsing and any timestamp semantic change as a later behavior-focused plan rather than silently changing acceptance output here.

## Decision Log

- Decision: Keep the existing mapping contract and restore prior fallback behavior rather than introduce new typed failure objects in this child.
  Rationale: The parent slice is an extraction, not a serialized evidence schema redesign.
  Date/Author: 2026-08-01 / Codex.

## Outcomes & Retrospective

Parity tests and direct boundary coverage are complete. Architecture and parent-plan reconciliation are complete; README was reviewed and needs no user-facing ownership change. Recursive AP-state/hex-text parsing and timestamp-presence semantic redesign remain explicitly deferred.

## Context and Orientation

`Phase3PdfSignatureSnapshotter` owns signed-PDF evidence primitives. Its public methods return the same JSON-ready mappings previously returned by private helpers in `phase3_harness.py`. `docs/ARCHITECTURE.md` documents module ownership and collaborator direction; tests in `tests/unit/test_phase3_pdf_signature_snapshotter.py` should exercise the new boundary directly.

## Plan of Work

Change `_snapshot_appearance_xobjects` so a failed indirect-object resolution falls back to the original reference object exactly as before, and change `_snapshot_pdf_numeric` to catch `Exception` exactly as before. Add direct tests for unsigned PDFs, malformed appearance/XObject references, timestamp status projections, and metadata values that are not primitive JSON types. Keep tests focused on observable returned mappings, not private implementation names.

Update `docs/ARCHITECTURE.md` to list `phase3_pdf_signature_snapshotter.py`, change signed-output/capture assembler collaborator descriptions to bound snapshotter methods, and add a changelog entry. Update the parent ExecPlan's progress, surprises, outcomes, and artifacts sections with the follow-up result. README needs no user-facing change unless the documentation reviewer finds a stale ownership statement.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

       .venv/bin/python -m pytest -q tests/unit/test_phase3_pdf_signature_snapshotter.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_harness_capture_assembler.py
       .venv/bin/ruff check src tests
       git diff --check
       rg -n "phase3_pdf_signature_snapshotter|_snapshot_output_signature|_snapshot_output_verification|_snapshot_visible_signature_appearance" docs/ARCHITECTURE.md

Then run the parent validation commands, including `.venv/bin/python -m pytest -q` and both release-fidelity matrices, before the final compliance review.

## Validation and Acceptance

Acceptance requires direct boundary tests for missing, unsigned, malformed, and valid signed PDFs; unchanged existing valid-signed mappings; no stale architecture references; full suite and matrix success; and no leftover processes or temporary artifacts. These checks are complete; recursive AP-state/hex-text parsing and timestamp-presence semantic redesign remain deferred to a later behavior-focused plan.

Validation evidence carried forward from the completed slice: 100 focused evidence tests passed (with one warning), 3 direct snapshotter boundary tests passed, the full suite passed with 1040 tests and one pre-existing Pillow deprecation warning, the preview matrix reported 8 scenarios with 0 errors, and the signed matrix reported 8 scenarios with 6 successful signings, 2 intentional rejections, and passing acceptance expectations.

## Idempotence and Recovery

All changes are additive or behavior-preserving. If a malformed-fixture test fails, compare its mapping with the old helper behavior and adjust only the snapshotter. Do not restore duplicate helpers in `phase3_harness.py`.

## Interfaces and Dependencies

Use the existing `Phase3PdfSignatureSnapshotter` methods. Tests may use temporary files and simple fake PDF reference objects; production continues to use pyHanko readers, certification inspection, and timestamp validation adapters.

## Change-Slice Boundary

Allowed changes are snapshotter parity, direct boundary tests, architecture/ExecPlan documentation, and validation artifacts. Do not alter CLI commands, signing semantics, application DTOs, Qt lifecycle, matrix manifests, or unrelated modules.

Plan revision note: created 2026-08-01 after the initial compliance review identified documentation drift, missing direct boundary coverage, and malformed-input parity risks.
