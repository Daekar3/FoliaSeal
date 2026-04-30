## Signed Preview Parity Matrix Remediation

### Goal

Use the new layered appearance instrumentation to remove the two dominant false parity channels exposed by the signed preview-parity matrix:

- preview-side border metadata dropping in the headless analysis path
- preview/signed text-fragment mismatch caused by inconsistent fragment modeling and dynamic signing-time drift

This slice does not change fit policy, layout policy, or stamp sizing.

### Observed Failures

From `artifacts/signed_preview_parity_matrix_run_v1/summary.json`:

- `14` scenarios total
- `3` scenarios fail before signing for valid fit reasons
- `11` successful signings
- `11/11` successful signings report border-layer mismatch
- `11/11` successful signings report text-layer mismatch
- `0` stamp-layer mismatches
- `0` composite-layer mismatches

### Scope

1. Normalize preview text fragments to the same semantic model as signed output.
2. Normalize text-fragment comparison so signing-time drift does not produce false failures.
3. Harden preview appearance snapshot reconstruction so border metadata cannot disappear in the headless analysis path.

### Acceptance

- Focused unit tests cover title-aware preview fragments, timestamp-normalized text comparison, and border-style fallback.
- `pytest -q` passes.
- The signed preview-parity matrix reruns successfully.
- Border-layer mismatches caused only by dropped preview metadata are gone.
- Text-layer mismatches caused only by signing-time drift are gone.

### Result

This slice landed cleanly.

- Focused tests passed, then the full suite passed (`444 passed`).
- The rerun matrix completed at `artifacts/signed_preview_parity_matrix_run_v2/summary.json`.
- The three non-signing scenarios remain legitimate fit failures.
- The previous border-layer mismatches are gone.
- The previous text-fragment mismatches are gone.
- The only remaining parity channel is rendered text-bounds mismatch after normalization.

That is the correct next defect. The instrumentation is now separating semantic text agreement from geometric text-bounds disagreement, which is what the autonomous parity loop needed.
