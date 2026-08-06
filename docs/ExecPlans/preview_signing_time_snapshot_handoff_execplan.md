# Preserve Preview Signing Time Through Final Signing

This living ExecPlan follows `.agents/skills/write-execplan/PLANS.md` and is governed by
`docs/ExecPlans/architecture_improvement_loop_parent_execplan.md`.

## Purpose / Big Picture

The preview is the canonical representation of a visible signature. Today the draft preview and
final signing can read the system clock separately, so a clock rollover may change the timestamp
text between them. After this slice, an unchanged draft carries the timezone-aware timestamp used by
its preview into final signing. Direct headless requests that have no preview timestamp continue to
use the current clock, and persisted profiles, CLI JSON, artifact schemas, and public command names
do not change.

## Child ExecPlan Dependencies

- [x] Fresh scan 11 and three independent design reviews are recorded in the architecture parent.
- [x] Existing `SigningClock`/`_FixedSigningClock` semantics and `SigningRequest` constructors are
  verified in `visible_signature_semantics.py`, `signing_draft_workflow.py`, and
  `phase3_signing_backend.py`.
- [ ] The atomic phase3 nomenclature plan remains separate and is not a prerequisite.

## Progress

- [x] (2026-08-06) Selected minimal additive timestamp propagation over the larger prepared-submission
  context; direct-call fallback and serialized-contract preservation are explicit gates.
- [x] (2026-08-06) Added optional aware `signing_time` fields to the in-memory request path and
  threaded them through backend request preparation.
- [x] (2026-08-06) Refactored preview to resolve semantics once, cache the timestamp/fingerprint,
  and invalidate it on placement, appearance, preset, and certificate mutations.
- [x] (2026-08-06) Added propagation, mutation-invalidation, explicit-backend-time, direct-fallback,
  and preview/backend parity coverage; focused suite passed `135` tests.
- [x] (2026-08-06) Full suite passed `1,062` tests with `11` skipped and one pre-existing warning;
  Ruff, diff checks, CLI/import validation, and offscreen matrices passed (`10/7/3`, `18/18`,
  `3/3`). Temporary evidence roots were removed and the process audit was clean.
- [x] (2026-08-06) Actual Improvement is `0.45` versus predicted `0.35` (`1.29x`), with no component
  regression below `-0.10`; implementation committed on `main` as `0391d9eb7`.

## Surprises & Discoveries

- Observation: `SigningDraftWorkflow.preview()` initially resolved semantics twice, once while
  validating and again while building display fields, so one preview can already contain two clock
  values.
  Evidence: `signing_draft_workflow.py` calls `validation_issues()` and then
  `_resolve_visible_signature_semantics()` in the preview path.
- Observation: Adding the timestamp to the UI preview DTO changed equality for invalid-form recovery
  tests because each fresh invalid preview read the clock. The timestamp remains internal to the
  request/backend path, preserving the established UI snapshot contract.
  Evidence: two `test_qt_signing_shell.py` equality tests failed before the field was removed; the
  full suite passed after recovery.
- Observation: The application already has an injectable `SigningClock` and backend `_FixedSigningClock`.
  Evidence: `visible_signature_semantics.py` and `phase3_signing_backend.py` define and test both.

## Decision Log

- Decision: Add `signing_time: datetime | None = None` to the in-memory `SigningRequest` and
  `SigningBackendRequest`; do not add it to persisted schemas or JSON snapshot mappings.
  Rationale: this is the smallest one-slice handoff and preserves all direct callers through the
  default `None` path while making the GUI preview token explicit.
  Date/Author: 2026-08-06 / Codex.
- Decision: Cache a timestamp plus a typed fingerprint of visible-signature inputs in
  `SigningDraftWorkflow`; carry the timestamp only when the fingerprint still matches.
  Rationale: mutation invalidation protects against stale previews even when a caller changes state
  without immediately re-rendering. A fingerprint avoids relying on mutable object identity.
  Date/Author: 2026-08-06 / Codex.

## Outcomes & Retrospective

Implementation completed on 2026-08-06. The workflow now captures one aware preview timestamp and
propagates it only while the current fingerprint matches; mutation invalidation and `None` fallback
preserve direct/headless behavior. The backend uses the supplied instant through its existing fixed
clock and retains current-time semantics otherwise. The UI preview DTO and all persisted/serialized
contracts remain unchanged.

Focused workflow/backend/semantics coverage passed `135` tests; full pytest passed `1,062` tests with
`11` skipped and one pre-existing Pillow warning. Ruff, diff checks, CLI/import checks, and offscreen
signed evidence passed the acceptance matrix (`10` scenarios, `7` successful signings, `3` matched
intentional rejections), preview parity (`18/18`), and fit rejection (`3/3`), with zero cryptographic,
annotation, preview-comparison, or expectation failures. Explicit temporary evidence roots were
removed and no FoliaSeal/Python application process remained.

Proxy measurements before -> after were navigation `0.25`, change amplification `0.40`, seam
reduction `0.50`, boundary-test improvement `0.75`, interface compression `0.25`, and boundary
isolation `0.50`; weighted `Actual Improvement = 0.45` versus predicted `0.35` (`1.29x`), with no
component regression below `-0.10`.

Implementation commit: `0391d9eb7` (`fix: preserve preview signing time`). A fresh three-explorer
scan is required before selecting the next candidate.

## Context and Orientation

`SigningDraftWorkflow.preview()` builds the visible preview, while `build_signing_request()` creates
the domain request consumed by `SignPdfUseCase` and `SigningBackendRequest.from_signing_request()`.
`prepare_phase3_signing_plan()` resolves final visible semantics and currently obtains signing time
from `_current_signing_time()`. `VisibleSignatureSemanticsService` accepts a `SigningClock`, so a
fixed clock can make preview and signing use the same aware instant and display mode.

## Plan of Work

Add the optional timestamp field with a default of `None` to `SigningRequest` and
`SigningBackendRequest`. Update `from_signing_request()` and request construction so existing
positional/keyword callers remain valid. Ensure request snapshot/JSON helpers omit the field.

In `SigningDraftWorkflow`, store `_preview_signing_time` and a typed fingerprint containing all
inputs that affect visible semantics: certificate identity, signature rectangle, appearance,
timezone display mode, datetime format, and relevant visible fields. Refactor `preview()` to resolve
semantics once, derive validation issues and display fields from that result, and store the aware
timestamp/fingerprint. `build_signing_request()` copies the timestamp only on a matching fingerprint;
otherwise it emits `None`. Clear the cache in every setter or preset/certificate/appearance mutation
that can alter those inputs. Reject or ignore naive timestamps rather than converting them twice.

In `prepare_phase3_signing_plan()`, use the supplied timestamp through `_FixedSigningClock` when
present, otherwise retain `_current_signing_time()` exactly. Preserve `PreparedSigningPlan`, fit
issues, reservation evidence, CLI/JSON/artifact mappings, invisible-signature behavior, and direct
headless fallback.

Add tests for one-preview single-resolution, unchanged-preview propagation, mutation invalidation,
clock rollover parity, UTC/local display modes, explicit backend time, `None` fallback, and unchanged
request snapshot serialization. Update architecture and this plan; record phase3 nomenclature as
unchanged atomic debt.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    rg -n "class SigningRequest|class SigningBackendRequest|def preview|def build_signing_request|_current_signing_time|_FixedSigningClock" src tests
    .venv/bin/pytest -q tests/unit/test_signing_draft_workflow.py tests/unit/test_phase3_signing_backend.py tests/unit/test_visible_signature_semantics.py
    .venv/bin/ruff check src tests scripts
    .venv/bin/pytest -q
    git diff --check

Then run the existing offscreen signed acceptance evidence command under an explicit `/tmp` root,
remove the root, and audit for FoliaSeal/Python processes. Expected behavior is unchanged acceptance
counts and `acceptance_expectations_passed=true`.

## Validation and Acceptance

The full suite and new boundary tests must pass with no weakened/skipped tests. A fake clock test
must prove that preview at instant `t1` followed by final signing after the clock reports `t2` still
uses `t1` when the draft is unchanged. A mutation test must prove the next submission falls back to
fresh time until a new preview is rendered. Direct requests with `signing_time=None` must retain
current-time behavior. UTC and local display modes must preserve the existing timezone conversion.
Ruff, import isolation, CLI help, signed acceptance/parity/fit matrices, cleanup, and process audits
must pass. Predicted improvement is `0.35`; accept only with Actual Improvement at least `0.15` and
no component regression below `-0.10`.

## Idempotence and Recovery

The timestamp field is optional and additive. If a caller does not render a preview, behavior is
unchanged. If a mutation invalidation test fails, retain the cache-clearing path and fix the input
fingerprint before changing the backend. Do not alter persisted schemas or external JSON to make the
test pass, and do not rename phase3 contracts.

## Artifacts and Notes

Record the fake-clock rollover transcript, focused/full test counts, signed evidence summary,
temporary-root removal, and clean process audit here after implementation. The only allowed generated
artifacts are explicit temporary acceptance roots, all removed before commit.

## Interfaces and Dependencies

`SigningRequest.signing_time` and `SigningBackendRequest.signing_time` are optional aware
`datetime` values. `SigningDraftWorkflow` owns the private timestamp/fingerprint cache. The backend
continues to use `VisibleSignatureSemanticsService` with `_FixedSigningClock` only when an explicit
timestamp exists; otherwise it uses its existing current-time clock. No new public CLI, JSON, or
persistence interface is introduced.
