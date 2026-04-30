# Signed Acceptance Matrix Expansion and Fixture Hardening

## Goal

Turn the signed-output acceptance layer from a proof-of-plumbing into a repeatable
end-to-end product check by formalizing the clean signing fixture, expanding the
acceptance manifest, and making success/rejection expectations machine-checkable.

## Decisions

- Treat `artifacts/preview_sweep_assets/sweep_fixture.pdf` as preview-only.
- Treat `artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf` as the
  canonical clean fixture for signed acceptance runs.
- Keep the signed acceptance matrix intentionally small, but require broad coverage:
  `single_line`, `multi_line`, `wrapped_block`, at least one image-stamp success,
  at least one dense success, and one intentional rejection per layout family.
- Encode expectations directly in the manifest so the batch summary can tell us if
  outcomes matched intent.

## Implementation

- Added canonical signing-acceptance asset constants in
  `src/foliaseal/application/qa_signed_acceptance_assets.py`.
- Extended signed-acceptance scenario parsing to support:
  - `fixture_role`
  - root-level `acceptance_expectations`
  - per-scenario `expected_outcome`
  - per-scenario `expected_failure_message_contains`
- Extended the signed matrix summary to report:
  - expected success scenario count
  - expected intentional rejection count
  - matched expected successes
  - matched expected intentional rejections
  - expected outcome mismatch count
  - batch-level acceptance pass/fail and expectation errors
- Replaced the starter manifest with a balanced 10-scenario acceptance set targeting:
  - 7 successful signed outputs
  - 3 intentional fit-validation rejections

## Verification

- Added tests for:
  - canonical signing fixture asset presence and parseability
  - signed acceptance manifest contract and family coverage
  - signed matrix expectation summary behavior
- Final verification should include:
  - `ruff check .`
  - `pytest -q`
  - a real signed batch against `artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf`
