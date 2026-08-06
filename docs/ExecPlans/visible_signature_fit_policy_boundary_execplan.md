# Centralize the visible-signature fit-gate policy

This living ExecPlan is the Cycle 5 child of
`docs/ExecPlans/architecture_improvement_loop_parent_execplan.md`. It is the final planned
architecture-improvement slice in this run and must preserve the prepare-once signing contract.

## Purpose / Big Picture

Visible-signature preparation and public fit validation both independently apply the same
`fit_gate_passed` / `fit_gate_error` mutation after rendered-ink fallback evaluation. This slice
introduces the neutral `VisibleSignatureFitDecision` and one `apply_visible_signature_fit_gate()`
policy helper. The backend remains the composition root for concrete PyHanko/Pillow measurement;
no signer, TSA, renderer, CLI, JSON, or artifact contract changes.

## Progress

- [x] (2026-08-05) Fresh scans ranked rendered-ink/fit-policy extraction at approximately `65.1`,
  above the fixed threshold; app-frame lifecycle and nomenclature migration were lower or broader.
- [x] (2026-08-05) Independent design reviews compared minimal, flexible ports, common-caller,
  and constrained hybrid shapes. Selected constrained hybrid: neutral decision/gate policy, backend
  measurement retained as an adapter, and the existing preparation remains the sole memoized gate.
- [x] (2026-08-05) Added `visible_signature_fit_policy.py` and routed both preparation and public
  validation through the shared decision/gate application.
- [x] (2026-08-05) Added focused policy coverage; existing backend/layout/preview fit suites remain
  the parity suite.
- [x] Run full validation, release matrices, docs reconciliation, measurement, and cleanup. The
  intentional commit and final post-cycle stopping decision are tracked by the parent loop.

## Interfaces and Guardrails

`VisibleSignatureFitDecision` is an immutable issue tuple with an `accepted` projection.
`apply_visible_signature_fit_gate(preparation, decision)` is the only mutation helper. The module
must stay free of Qt, Pillow, PyHanko, and `phase3_signing_backend` imports. Concrete rendered-ink
measurement and canonical preview fallback remain in the existing backend adapter for this slice.

Do not change `PreparedSigningPlan`, `VisibleSignaturePreparation`, fit error codes, serialized
reservation evidence, or public `phase3-signing-*` names. Do not add compatibility aliases or a
second fit gate.

## Validation and Acceptance

Run `.venv/bin/pytest -q`, `.venv/bin/ruff check src tests`, and `git diff --check`, then both
offscreen release matrices in explicit `/tmp/foliaseal-fit-policy-*` directories. Expected evidence
is 8 preview scenarios/0 errors; 8 signed scenarios/6 successful/2 intentional rejections; zero
cryptographic, annotation, and preview-output failures; `acceptance_expectations_passed=True`.
Remove generated directories and audit for FoliaSeal/Qt/pytest processes. Acceptance requires
unchanged fit behavior, no import leak, and Actual Improvement >= `0.15` with no component below
`-0.10`.

## Outcomes & Retrospective

Implementation completed on 2026-08-05. Both prepared-plan and public validation paths now apply a
single immutable `VisibleSignatureFitDecision` through `apply_visible_signature_fit_gate()`. The
concrete rendered-ink measurement and all existing fit error/evidence contracts remain unchanged.

Evidence: full suite `1047 passed` with one pre-existing Pillow warning; Ruff and diff checks clean;
preview matrix 8 scenarios/0 error rows; signed matrix 8 scenarios/6 successful signings/2 matched
intentional rejections/zero cryptographic, annotation, and preview-output failures/
`acceptance_expectations_passed=True`. Temporary directories were removed and the process audit
found no FoliaSeal, Qt, or pytest processes.

Proxy measurement: navigation `0.0`, change amplification `0.5`, seam reduction `0.5`,
boundary-test improvement `0.25`, interface compression `0.5`, boundary isolation `0.5`;
`Actual Improvement = 0.30`, predicted `0.25`, prediction accuracy `1.20x`, no component below
`-0.10`.
