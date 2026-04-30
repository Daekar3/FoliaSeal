# Certification Constraints Hardening ExecPlan

## Summary

The remaining backend gap is certification-constraint enforcement. Trust/timestamp hardening is already in place and tracked in `.agent/tsa_trust_hardening_execplan.md`; this slice focuses on DocMDP / permissions handling, operation classification, and release-readiness evidence.

This ExecPlan is the source of truth for:

- scope boundaries
- certification-policy behavior
- classification and audit fields
- test matrix coverage
- rerun / acceptance criteria
- documentation updates

## Key Changes

- Add a certification-policy seam that reads DocMDP / permissions state from input PDFs using pyHanko certification APIs.
- Block signing on `NO_CHANGES` documents with a stable, user-facing failure code.
- Allow signing on permitted certification states while reporting the permission class honestly.
- Extend signing and verification summaries with certification/audit fields:
  - `docmdp_permission`
  - `certification_restricted`
  - `restriction_reason`
  - `operation_type`
  - `revision_strategy`
- Build a deterministic compatibility matrix across PDF versions, unsigned inputs, approval-signed inputs, and certification-restricted inputs.

## Test Plan

- Add unit tests for:
  - DocMDP / permission parsing
  - unrestricted vs certified document classification
  - blocked signing on certification-restricted PDFs
  - stable failure mapping to `PDF_CERTIFICATION_RESTRICTS_SIGNING`
  - serialization of certification/audit metadata
- Add matrix tests covering representative combinations of:
  - PDF version
  - unsigned / approval-signed / certification-restricted input state
  - allowed vs blocked signing outcomes
- Rerun:
  - `ruff check .`
  - `pytest -q`
  - the signed acceptance matrix, to confirm certification enforcement does not regress the signing path

## Assumptions and Defaults

- No UI redesign is required in this slice.
- The new certification-policy seam should fail closed when the input cannot be classified.
- The production signing path remains incremental for allowed cases.
- If broader operation support is needed later, the `operation_type` / `revision_strategy` audit fields will carry forward without changing the policy core.

## Execution Notes

- Created as the source of truth before implementation.
