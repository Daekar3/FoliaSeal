# TSA Trust and Certificate Hardening ExecPlan

## Summary

Timestamp-required signing is already implemented and verified. The next slice is trust hardening: make TSA trust anchors, timestamp trust validation, and trust reporting explicit instead of implicit.

This slice must be tracked in this ExecPlan end to end. The plan is the source of truth for:

- scope boundaries
- trust-policy behavior
- test cases
- rerun/acceptance criteria
- documentation updates

## Key Changes

- Add a trust-policy seam that can build pyHanko validation contexts from an explicit policy object.
- Thread that policy through the signing request / draft workflow / post-sign verification path.
- Distinguish three cases in reporting:
  - timestamp token present
  - timestamp cryptographically valid
  - TSA chain trusted under configured anchors
- Keep the dummy TSA path available for deterministic CI, but mark it clearly as non-production trust evidence.
- Map missing or malformed trust material to a stable failure code, and map an untrusted timestamp chain to a separate stable failure code.

## Test Plan

- Add unit tests for:
  - trust-policy loading and validation-context creation
  - happy-path timestamp trust reporting with a real trust anchor chain
  - missing / malformed trust material
  - untrusted timestamp chain
  - stable failure mapping in the signing use case
- Extend request and result snapshot tests so trust reporting is serialized honestly.
- Rerun:
  - `ruff check .`
  - `pytest -q`

## Assumptions and Defaults

- No preview/layout/font changes belong in this slice.
- No UI redesign is required; trust policy can remain code/config driven unless a later slice needs a visible control.
- Dummy TSA remains CI-only and should not be treated as production trust evidence.
- If revocation policy wiring becomes broad or unstable, defer it to a follow-on slice and keep this one centered on trust anchors and clear failure mapping.

## Execution Notes

- Added a runtime `TimestampTrustPolicy` model and threaded it through:
  - signing request assembly
  - draft workflow conversion
  - signer result reporting
  - post-sign verification
- Added timestamp trust reporting fields:
  - `timestamp_cryptographically_valid`
  - `tsa_chain_trusted`
  - `timestamp_validation_error`
- Added stable failure mapping for:
  - missing or malformed trust material
  - untrusted timestamp chains when trust policy is configured
- Verified with:
  - targeted trust/timestamp unit tests
  - full `pytest -q`
  - the signed acceptance matrix using the existing dummy TSA path
