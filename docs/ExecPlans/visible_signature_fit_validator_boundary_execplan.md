# Extract the Visible-Signature Fit Validator Boundary

## Purpose

Move the signing-draft workflow's concrete fit-validation choreography behind the existing typed
`VisibleSignatureFitValidator` protocol. The workflow must no longer import
`phase3_signing_backend` or construct a private validator. Preserve backend-authoritative rendered-ink
fallback, exact validation issues, signing/preview/evidence behavior, and all historical `phase3`
CLI/DTO/JSON/artifact names. This is one bounded adapter/injection slice; the separate
`phase3_nomenclature_retirement_execplan.md` remains out of scope.

## Baseline and evidence

- Baseline commit: `f9f339919`.
- Scan Round 26 converged on this seam at Priority `68–69`, confidence `.90–.97`.
- The workflow still owns `_WorkflowVisibleSignatureFitValidator` and lazily imports the backend;
  `_validate_visible_signature_fit` is dead. Backend `validate_visible_signature_fit` remains the
  authoritative rendered-ink/layout gate.
- Two independent design reviews scored: minimal adapter ~70, typed-port ~80, constrained
  common-caller service ~84 but with higher cycle risk. Select the typed-port design for boundedness.

## Exact interface

Use the existing `VisibleSignatureFitRequest` and `VisibleSignatureFitValidator` protocol in
`visible_signature_semantics.py` unchanged. Add
`application/visible_signature_fit_validator.py`:

```python
class BackendVisibleSignatureFitValidator:
    def validate(
        self, request: VisibleSignatureFitRequest
    ) -> tuple[SigningDraftValidationIssue, ...]: ...
```

The implementation may import the backend and `SigningBackendAppearance` only inside `validate`,
converts a domain `SignatureAppearance` with the existing adapter, loads the stamp background through
the neutral helper, and delegates to `phase3_signing_backend.validate_visible_signature_fit`.
Missing certificate/image/appearance behavior and the exact
`visible_signature_layout_unavailable` issue mapping remain unchanged.

## Scope and migration

1. Add the adapter with no module-level PyHanko, Qt, Pillow, or workflow import. Add a firewall test.
2. Add an optional `fit_validator` field to `SigningDraftWorkflow`, defaulting to the adapter. Remove
   the nested `_WorkflowVisibleSignatureFitValidator`, the dead `_validate_visible_signature_fit`,
   and the workflow's backend/stamp-background local imports.
3. Keep `VisibleSignatureSemanticsService` and `VisibleSignatureFitValidator` signatures unchanged.
   Migrate workflow tests to inject a fake validator for deterministic issue assertions, while keeping
   backend tests as the authoritative rendered-ink regression suite.
4. Retire `_visible_signature_fit_issues_for_stamp_text` only if no first-party callers remain; if
   preview tests still need it, keep the public backend validator and record the wrapper's consumer.
5. Update `docs/ARCHITECTURE.md`, this plan, and the parent ledger with ownership, dependency, and
   compatibility decisions. Do not rename phase3 modules or public commands.

## Validation and acceptance

Run focused workflow/semantics/backend/layout tests, the full suite, Ruff, compileall, CLI help, and
the three offscreen evidence matrices. Add subprocess assertions that importing the workflow does not
load `phase3_signing_backend` until validation is invoked, and that the adapter import itself loads no
Qt/Pillow/PyHanko module. Preserve exact issue code/message/field/severity, rendered-ink fallback,
preview parity, signed acceptance counts (`10/7`, `18/18`), and fit rejection (`3/3`). Run `git diff
--check`, remove named `/tmp` roots and canonical-preview directories, and verify no FoliaSeal/Python/Qt
process remains.

Acceptance gates: full suite green with no skips; no SPEC diff; zero critical/major review findings;
Actual Improvement >= `.15` with no component regression below `-.10`; no first-party workflow import
of `phase3_signing_backend`; and a clean committed worktree.

## Out of scope and recovery

Do not move `_prepare_backend_layout`, PyHanko style materialization, certificate/signing semantics, or
the phase3 nomenclature migration in this slice. If adapter default wiring creates a cycle, retain a
composition-provided validator and document the exact caller; never add a workflow/backend alias or
restore the deleted dead wrapper. If matrix output changes, restore only the adapter indirection,
compare issue tuples and prepared-plan identity, and rerun the focused suite before proceeding.

## Status

- [x] Plan created after Scan Round 26 and two independent design reviews on 2026-08-06.
- [x] Typed-port design selected for one-slice boundedness; constrained service retained as a future
  option only if a neutral layout-preparation port is proven safe.
- [x] (2026-08-06) Added the typed backend fit-validator adapter, injected it into
  `SigningDraftWorkflow`, and retained the backend as the authoritative rendered-ink/layout gate.
- [x] (2026-08-06) Added adapter import-firewall and workflow injection coverage; focused validation
  passed for the adapter and workflow suites.
- [x] (2026-08-06) Reconciled architecture ownership, dependency direction, and compatibility notes.
- [x] (2026-08-06) Full suite passed: `1,111 passed, 1 warning` (the existing Pillow deprecation
  warning); offscreen signed acceptance `10/7`, preview parity `18/18`, and fit rejection `3/3`.
- [x] (2026-08-06) Named evidence roots and canonical-preview directories were removed; no
  FoliaSeal/Python/Qt processes remained; `git diff --check` passed and `docs/SPEC.md` was unchanged.
- [x] (2026-08-06) Conservative component measurements were navigation `0.25`, change amplification
  `0.35`, seam reduction `0.50`, boundary-test improvement `0.45`, interface compression `0.20`,
  and boundary isolation `0.65`, for Actual Improvement approximately `0.40` versus predicted `0.40`;
  no component regressed below `-0.10` and no critical/major review finding remains.
- [ ] Intentional commit and fresh post-commit scan ledger update.
