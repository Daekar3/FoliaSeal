# Harden safe-link and source-change policy contracts

This ExecPlan is a living document and must be maintained in accordance with
`.agents/skills/write-execplan/PLANS.md`. It is a correction child of
`docs/ExecPlans/ui_safe_links_source_safety_contracts_execplan.md`.

## Purpose / Big Picture

The first safety-contract slice exposed a conservative-policy bug: when source identity was not
measured, the decision model called it unchanged. This correction makes uncertainty require review,
prevents obvious malformed/network-relative destinations from being treated as internal merely
because a page index was supplied, and lets the future viewer enforce the UI_SPEC Pan-only rule at
the typed boundary. The user-visible GUI remains deferred; the observable outcome is a stricter,
fully tested policy contract that cannot silently authorize an unknown source.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/ui_safe_links_source_safety_contracts_execplan.md` is implemented in
  `0c9b20564`.
- [x] `docs/UI_SPEC.md` section 16 and `docs/ARCHITECTURE.md` are available for review.

## Progress

- [x] (2026-08-10) Compliance review identified unknown-fingerprint false-unchanged behavior,
  malformed internal-destination acceptance, missing mode gating, and missing architecture entry.
- [x] (2026-08-10) Added red tests for unknown source identity, mode gating, malformed internal
  destinations, and bounded display text; implemented the conservative typed behavior.
- [x] (2026-08-10) Ran focused validation (24 passed), updated `docs/ARCHITECTURE.md`, and
  recorded the corrected living-plan handoff; full-suite validation remains the final gate.
- [x] (2026-08-10) Full validation reports 1342 passed, 20 skipped, 1 warning; the bounded GUI
  lifecycle reaches the known isolated endpoint limitation and cleans its root/processes. The
  correction is committed in `45e5187d2` and hands renderer/workspace integration to the parent
  plans.

## Surprises & Discoveries

- Observation: two `None` fingerprints are not evidence of equality. Evidence: compliance review of
  `source_change_decision` found it returned `UNCHANGED/NONE` for `(None, None)`.
- Observation: a future PDF adapter can legitimately provide no URI for an internal page target, so
  the classifier must distinguish `raw_destination is None` from an explicitly empty string.

## Decision Log

- Decision: add `SourceChangeStatus.UNKNOWN` with `SourceChangeAction.REVIEW_REQUIRED` whenever
  either fingerprint is unavailable while the source exists. Rationale: unknown identity must never
  authorize signing or silent continuation. Date/Author: 2026-08-10 / Codex.
- Decision: accept a missing raw destination only when a validated nonnegative internal page index is
  supplied; reject explicit empty strings, control characters, network-relative `//` values, and
  malformed `scheme ://` values. Rationale: preserve valid PDF internal links without widening the
  trust boundary. Date/Author: 2026-08-10 / Codex.
- Decision: add a typed `LinkInteractionMode` and return BLOCK for Select Text or Place Signature;
  only Pan may activate links. Rationale: UI_SPEC section 16 makes mode gating a safety invariant,
  not a widget convention. Date/Author: 2026-08-10 / Codex.

## Outcomes & Retrospective

The corrected matrix now treats unavailable source identity as `UNKNOWN/REVIEW_REQUIRED`, blocks
link activation outside Pan mode, rejects malformed/network-relative/empty internal destinations,
and bounds confirmation display text while retaining no launcher or I/O behavior. The architecture
document now names `document_safety.py` and its explicit non-responsibilities. Renderer extraction,
source monitoring, draft-preserving reload, and condition-only banner integration remain open.

## Context and Orientation

The module `src/foliaseal/application/document_safety.py` is pure standard-library code. It returns
non-executable decisions consumed later by a PDF link extractor, a Pan-only viewer hit tester, and a
source-monitor/banner surface. It must not open URLs, read files, or mutate a signing draft. The
current `LinkDecision.destination` is a future display value, so it must be bounded and free of
control characters before a confirmation dialog renders it.

## Change Slice

Primary change class: behavior correction and tests, plus the owning architecture/plan notes.
Allowed files are the safety module, its focused tests, `docs/ARCHITECTURE.md`, and the three safety
ExecPlans. Do not add renderer APIs, Qt controls, filesystem monitoring, or external launching.

## Plan of Work

Add `LinkInteractionMode` with `PAN`, `SELECT_TEXT`, and `PLACE_SIGNATURE`. Extend
`classify_link_destination` with an `interaction_mode` keyword defaulting to `PAN`; non-Pan modes
return BLOCK before any destination classification. Add `SourceChangeStatus.UNKNOWN` and
`SourceChangeAction.REVIEW_REQUIRED`; `source_change_decision` returns UNKNOWN whenever `exists` is
true but either fingerprint is `None`. Keep missing and changed outcomes unchanged.

Harden destination normalization: preserve `None` as a distinct value for validated internal links,
reject explicit empty strings and control characters, reject values beginning `//`, and reject a
value containing `://` when `_scheme` cannot parse a valid scheme. Bound the display destination to
512 characters after control-character removal and whitespace normalization. Add red-to-green tests
for all new branches, including Select/Place blocking and `(None, None)` source identity.

Add a concise Application Boundaries entry to `docs/ARCHITECTURE.md` naming
`document_safety.py` as a pure policy module and documenting its future consumers and explicit
non-responsibilities. Update both safety plans with the review findings and corrected evidence.

## Milestones

Milestone 1 adds one red unknown-fingerprint test and turns it green. Milestone 2 adds mode gating
and malformed-destination tests one behavior at a time. Milestone 3 runs complete validation and
records the exact handoff to renderer/workspace integration.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    .venv/bin/pytest -q tests/unit/test_document_safety.py
    .venv/bin/ruff check src tests
    .venv/bin/pytest -q
    git diff --check

Expected focused tests include the original 14 plus the new correction cases (24 total); the full suite must
remain green. Run the bounded offscreen GUI lifecycle command from the parent plan and clean its
temporary root/processes. `SingleInstanceUnavailable` remains an environment transport limitation,
not a safety-contract failure.

## Validation and Acceptance

Acceptance requires that unknown source identity returns review-required, no non-Pan mode can produce
an allowed or confirmation-required link decision, valid internal page links remain allowed, and
obvious malformed/network-relative/empty destinations are blocked. Confirmation text is bounded and
contains no control characters. Tests must prove the module remains pure and no browser/file opener
is imported.

## Idempotence and Recovery

All changes are pure and safe to rerun. If a test fails, keep the last green focused result in
Progress and do not broaden the slice. No generated artifacts or external state are permitted.

## Artifacts and Notes

No artifacts are required. Record test output and the architecture/plan edits only.

## Interfaces and Dependencies

The module continues to use only Python standard-library types. The renderer child will pass a
validated page index and raw destination plus `LinkInteractionMode.PAN`; the workspace child will
interpret `REVIEW_REQUIRED` as a signing-blocking condition until source identity is acknowledged.

Revision note: 2026-08-10 / Codex. Created from the post-implementation compliance review of
`0c9b20564` to close the unknown-identity and mode/destination safety gaps before GUI integration.
