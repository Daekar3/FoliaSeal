## Signed Output Acceptance Harness ExecPlan

### Objective

Upgrade the Phase 3 harness from preview-only confidence plus basic signing facts
to repeatable signed-output acceptance evidence that can verify:

- cryptographic validity of produced signatures
- signature annotation placement and size
- signed visible-appearance parity with the reviewed preview
- representative end-to-end behavior across a small signed acceptance matrix

### Scope

1. Extend harness capture payloads with explicit signed-output verification and
   comparison snapshots.
2. Harden signed-output render/crop comparison so it records geometry deltas,
   text/image presence parity, and comparison tolerances instead of a single
   loose diff signal.
3. Enforce successful-sign evidence requirements in the Phase 3 evidence
   contract.
4. Add a representative signed acceptance matrix command and manifest.
5. Cover the new behavior with unit tests and document the workflow.

### Constraints

- Do not change visible-signature layout policy in this slice.
- Reuse the existing pyHanko verification path as the cryptographic source of
  truth.
- Keep the signed acceptance matrix intentionally small and representative.
- Prefer extending the existing harness summary/evidence model over creating a
  second report format.

### Implementation Plan

1. Inspect and extend the current signed-output snapshot helpers.
2. Add `output_verification_snapshot` and strengthen
   `signed_output_render_snapshot` / `signed_output_preview_comparison`.
3. Add evidence-contract rules for successful visible-signature runs.
4. Add a signed acceptance matrix runner and manifest using the existing scenario
   language.
5. Add targeted tests for:
   - verification snapshot extraction
   - signed-output render/comparison snapshot behavior
   - evidence-contract enforcement
   - signed acceptance manifest presence/parsing
6. Review delegated documentation updates and align README/canonical docs with
   the new harness capabilities.

### Acceptance Criteria

- Successful signing runs persist cryptographic verification evidence and
  signed-output comparison evidence.
- Evidence contract fails a sign-success run if required signed-output evidence
  is missing or preview/output parity fails.
- The repo contains a checked-in signed acceptance manifest with representative
  scenarios.
- The test suite covers the new contract and helper behavior.
