# Close prepared-signing-plan compliance gaps

This child ExecPlan is part of `docs/ExecPlans/prepared_signing_plan_hybrid_execplan.md` and follows `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

The prepared signing boundary is functionally working, but its declared fit-issue type, boundary-test coverage, and architecture documentation must match the implementation. This child slice makes the contract truthful and demonstrates that a prepared layout plan is actually consumed by the visible signer.

## Child ExecPlan Dependencies

- [x] Parent prepared-signing-plan implementation exists and its focused/full tests pass.
- [x] Independent architecture and SPEC reviews identified the documentation, type, and reuse-test gaps.

## Progress

- [x] (2026-07-31) Confirmed the fit issue mismatch: `SignatureLayoutPlan.fit_issues` contains `VisibleSignatureFitIssue`, while `PreparedSigningPlan` declares `SigningDraftValidationIssue`.
- [x] (2026-07-31) Confirmed missing README/architecture ownership documentation and missing prepared-plan signer reuse coverage.
- [x] (2026-07-31) Convert layout fit issues to the declared application validation type at the prepared boundary.
- [x] (2026-07-31) Add a regression test proving `PyHankoPdfSigner.sign(prepared=...)` consumes the supplied plan and preserves visible output behavior.
- [x] (2026-07-31) Update README, `docs/ARCHITECTURE.md`, parent/child plans, and rerun compliance validation.
- [x] (2026-07-31) Repeated the architecture/spec compliance review after the corrections; no blocking discrepancy remains. Exact signing-time snapshot handoff remains a separately documented fidelity follow-up.

## Surprises & Discoveries

- Observation: the two fit-issue dataclasses have matching fields but are distinct types from different modules.
  Evidence: `visible_signature_layout.py:455` and `signing_draft_workflow.py:57`.
- Observation: existing lower-level image/layout tests cover rendering helpers, but no prepared-plan boundary test exercises a supplied plan through the concrete signer.
  Evidence: `tests/unit/test_phase3_signing_backend.py` prepared-plan coverage before this child.

## Decision Log

- Decision: Convert `VisibleSignatureFitIssue` values into `SigningDraftValidationIssue` at the prepared-plan boundary rather than widening the plan type to a union.
  Rationale: callers of the application preparation contract already consume signing-draft validation issues, and the conversion prevents presentation/layout implementation types from leaking outward.
  Date/Author: 2026-07-31 / Codex.
- Decision: Test plan reuse by supplying a prepared plan to `PyHankoPdfSigner.sign()` and asserting successful visible output, while retaining existing lower-level image tests.
  Rationale: this proves the new optional path without deleting valuable regression tests or broadening into a full preview renderer rewrite.
  Date/Author: 2026-07-31 / Codex.

## Outcomes & Retrospective

Completed 2026-07-31. `_layout_fit_issues()` now converts neutral layout issues into
`SigningDraftValidationIssue` values before exposing them through `PreparedSigningPlan`. The
supplied-plan signer regression covers visible output and verifier acceptance, while the invisible
headless branch covers timestamp-disabled and timestamp-required signing. README and architecture
documentation now describe the application/adapter ownership split and unchanged `execute(request)`
compatibility facade. Focused prepared/invisible backend validation passed (5 tests), Ruff passed,
and the full suite passed (1,016 tests; one existing Pillow deprecation warning).
The post-fix compliance review accepted the boundary; independent preview/signing clock snapshots
remain a low-priority follow-up rather than a blocker for this compatibility-preserving slice.

## Context and Orientation

`PreparedSigningPlan` is defined in `src/foliaseal/application/phase3_signing_backend.py`. It is built by `prepare_phase3_signing_plan()` and optionally supplied to `PyHankoPdfSigner.sign()`. `SignatureLayoutPlan.fit_issues` is owned by `visible_signature_layout.py`; the prepared application boundary must expose `SigningDraftValidationIssue` values instead. README and `docs/ARCHITECTURE.md` describe the public application flow and must record the invisible headless branch and ownership split.

## Plan of Work

Add a small converter in `phase3_signing_backend.py` that maps each layout issue's code, message, field name, and severity into `SigningDraftValidationIssue`. Use it in `_layout_fit_issues()` before returning non-empty failures. Add a test that creates a compact visible request, prepares it, and asserts every exposed issue is a `SigningDraftValidationIssue`.

Add a prepared-plan reuse test that builds a valid visible request, calls `prepare_phase3_signing_plan()`, passes the result to `PyHankoPdfSigner.sign()`, writes the returned bytes, and verifies the resulting PDF with `PyHankoSignatureVerifier`. This must exercise the optional prepared argument rather than the compatibility path.

Update README and `docs/ARCHITECTURE.md` to document `PreparedSigningPlan`, `prepare_phase3_signing_plan()`, the unchanged `execute(request)` facade, the invisible PyHanko field path, and the fact that external PyHanko/Pillow objects remain adapter-owned. Update the parent and child plan status and record compliance evidence.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    .venv/bin/pytest -q tests/unit/test_phase3_signing_backend.py -k 'prepared or invisible'
    .venv/bin/ruff check src/foliaseal/application/phase3_signing_backend.py tests/unit/test_phase3_signing_backend.py
    .venv/bin/pytest -q

Re-run the two release-fidelity matrix commands from the parent plan and verify no FoliaSeal process or window remains.

## Validation and Acceptance

Acceptance requires non-empty prepared fit issues to be `SigningDraftValidationIssue` values, a supplied prepared plan to produce a valid visible signed PDF, the README and architecture document to match code ownership, and all existing focused/full/matrix validation to remain green.

## Idempotence and Recovery

The corrections are additive. Do not delete existing layout/image regression tests. Generated PDFs remain under `/tmp`; if the prepared signer test fails, compare the supplied plan's layout to the style adapter arguments before changing layout policy.

## Artifacts and Notes

Only source, tests, docs, and ExecPlans are tracked. Final compliance result: accepted. Generated
signing artifacts remain outside Git.

## Interfaces and Dependencies

The prepared boundary remains:

    def prepare_phase3_signing_plan(request: SigningBackendRequest) -> PreparedSigningPlan: ...
    def sign(request: SigningBackendRequest, *, prepared: PreparedSigningPlan | None = None) -> SigningOutput: ...

Its `fit_issues` field contains only `SigningDraftValidationIssue` values. No new PyHanko or Pillow dependency is introduced.

## Revision Note

2026-07-31 / Codex: Created after the first post-implementation architecture/SPEC review identified documentation drift, a fit-issue type mismatch, and missing supplied-plan signer coverage.
