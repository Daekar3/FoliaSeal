# Harness Capture Upgrade for Pre-Submit Diagnostics

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md` and the parent wave plan
`docs/ExecPlans/visible_signature_output_analysis_execplan.md`.

## Purpose / Big Picture

The Phase 3 harness already captures much more than it did earlier, but the latest manual run
showed an important blind spot: when the shell blocks signing before any request is emitted,
`backend_reservation_snapshot` becomes `null`, which leaves the acceptance artifact unable to
explain why the current draft failed. After this change, the harness should still record the
backend-style reservation context from the current draft even when the sign button is disabled or
submission never succeeds. The capture should also expose the actual-output evidence using stable,
human-readable primitive fields that match the names we want reviewers to inspect.

This matters because the current wave is explicitly about understanding layout failures. If the
harness only records reservation data after a successful sign request, then the moment the UI says
“does not fit” we lose the most important evidence.

## Progress

- [x] (2026-04-01 00:18Z) Created this child ExecPlan for the harness/output-analysis worker.
- [x] (2026-04-01 00:20Z) Inspected `src/foliaseal/presentation/qt/phase3_harness.py` and
  `tests/unit/test_phase3_harness.py` to confirm the current capture only snapshots reservation
  data from emitted signing requests.
- [x] (2026-04-01 00:28Z) Added a harness helper that derives a draft-style `SigningRequest` from
  the current workflow so
  reservation data can be captured even when `sign_request_count == 0`.
- [x] (2026-04-01 00:29Z) Normalized the visible-appearance snapshot with stable alias keys such as
  `visible_text_present`, `text_fragments`, and `image_xobjects`.
- [x] (2026-04-01 00:30Z) Updated markdown summary/tests to prove the new pre-submit reservation
  capture and output
  aliases work.
- [x] (2026-04-01 00:32Z) Ran focused tests and lint on the harness slice.

## Surprises & Discoveries

- Observation: the current harness already fixed the old `field_bindings` type mismatch for real
  sign requests, but the latest user run still showed `backend_reservation_snapshot: null`.
  Evidence: `sign_request_count` was `0`, so the code never called `_snapshot_backend_reservation`.

- Observation: the current visible-appearance snapshot already contains useful facts, but the field
  names are more backend-internal than reviewer-friendly.
  Evidence: the snapshot exposes `appearance_has_visible_text`,
  `appearance_text_fragments`, and `appearance_xobjects`, while the current review checklist asks
  for `visible_text_present`, `text_fragments`, and `image_xobjects`.

- Observation: the current-draft request can be synthesized safely without validating the draft.
  Evidence: `SigningDraftWorkflow` already stores the exact request fields needed for reservation
  capture, and the new focused test proved the synthesized request matches the workflow state.

## Decision Log

- Decision: keep the harness fix entirely inside `phase3_harness.py` by synthesizing a
  `SigningRequest` from the current draft workflow state instead of reaching into unrelated modules.
  Rationale: this keeps the worker within scope and avoids stepping on the shell or backend tracks.
  Date/Author: 2026-04-01 / Codex

- Decision: preserve the existing visible-appearance fields and add stable aliases rather than
  renaming the old keys outright.
  Rationale: the existing tests and any already-generated artifacts can continue to work, while new
  reviews get the clearer names they asked for.
  Date/Author: 2026-04-01 / Codex

## Outcomes & Retrospective

The harness now preserves reservation evidence even when the UI blocks signing before a request is
submitted. The end-of-run capture chooses the last real request when available, otherwise it
synthesizes a request from the current draft workflow and feeds that to the reservation helpers.
This means the next blocked harness rerun should no longer produce the empty combination of
`sign_request_count: 0`, `backend_reservation_error: null`, and `backend_reservation_snapshot:
null`.

The visible-appearance snapshot also now exposes reviewer-friendly alias keys while keeping the
older names intact. That keeps existing tests and artifacts stable while making the JSON easier to
inspect manually during acceptance.

## Context and Orientation

The relevant file is `src/foliaseal/presentation/qt/phase3_harness.py`. It owns the
`Phase3HarnessCapture` dataclass, the JSON serialization logic, the markdown acceptance summary,
and the post-run capture assembly. The latest gap is in `run_phase3_signing_harness()`, which only
calls `_snapshot_backend_reservation()` and `_backend_reservation_error()` when a signing request
was emitted.

The companion tests live in `tests/unit/test_phase3_harness.py`. They already cover JSON-safe
capture serialization, reservation snapshots for good/bad requests, and visible-appearance facts
from a signed PDF. They do not yet cover the pre-submit capture path where the draft never became a
`SigningRequest`.

In this repository, “backend reservation snapshot” means a summary of the backend-facing
visible-signature layout inputs and the measured pyHanko stamp style metadata, expressed as
primitive JSON values. “Actual-output evidence” means facts extracted from the signed PDF’s visible
appearance, not guesses from the preview.

## Plan of Work

First, add a tiny helper in `src/foliaseal/presentation/qt/phase3_harness.py` that can synthesize a
`SigningRequest` from the current `SigningDraftWorkflow` state already owned by the shell. This
helper must not attempt to validate the draft; it should simply mirror the current workflow values
into a request-like object when both a signature rectangle and signature appearance exist. That is
enough for reservation diagnostics.

Second, update `run_phase3_signing_harness()` so it chooses the most useful request context in this
order: the last emitted signing request if one exists, otherwise the synthesized current-draft
request. Use that request for `backend_reservation_snapshot`, `backend_reservation_error`, page
metadata, and the request snapshot itself only when no real sign request exists. This will keep the
capture informative even when the UI blocks signing.

Third, extend `_snapshot_visible_signature_appearance()` to add stable alias keys for the existing
facts so the next review can look for `visible_text_present`, `text_fragments`, `image_xobjects`,
`annotation_rect`, and `appearance_bbox` without translating the older names mentally.

Finally, update the harness tests to cover the new helper and the alias keys, then run the focused
test and lint commands.

## Concrete Steps

From `/home/daekar/FoliaSeal`:

1. Edit `src/foliaseal/presentation/qt/phase3_harness.py` to add a current-draft request helper
   and to use it during capture assembly.
2. Add visible-appearance alias keys in the same file.
3. Update `tests/unit/test_phase3_harness.py` with:
   - a test for the synthesized draft request helper
   - assertions that reservation data is still captured when a draft is available
   - assertions for the new visible-appearance alias keys
4. Run:

       ./.venv/bin/python -m pytest -q tests/unit/test_phase3_harness.py
       ./.venv/bin/ruff check src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_phase3_harness.py

## Validation and Acceptance

Acceptance is reached when the harness slice proves all of the following:

- a draft with a signature rectangle and signature appearance can produce a backend reservation
  snapshot even if no sign request was emitted
- the capture remains JSON-safe
- the visible-appearance snapshot exposes reviewer-friendly alias keys without losing the existing
  facts
- focused tests pass and lint is clean

The human-visible proof is the next harness rerun: if the UI blocks signing, the JSON should still
show a meaningful `backend_reservation_snapshot` instead of `null`.

Focused verification completed from `/home/daekar/FoliaSeal`:

    ./.venv/bin/python -m pytest -q tests/unit/test_phase3_harness.py
    7 passed in 0.44s

    ./.venv/bin/ruff check src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_phase3_harness.py
    All checks passed!

## Idempotence and Recovery

These edits are additive and safe to repeat. If a helper proves too broad, narrow it to the
smallest useful draft-to-request conversion inside the harness rather than widening scope into the
shell. If an alias field turns out to duplicate too much data, keep the shorter reviewer-friendly
name and drop only the redundant copy after updating tests.

## Artifacts and Notes

Latest motivating evidence from the user’s harness capture:

    "sign_request_count": 0,
    "backend_reservation_error": null,
    "backend_reservation_snapshot": null,
    "validation_text": "ERROR visible_signature_layout_unavailable: Visible signature content does not fit inside the selected rectangle ..."

That combination means the harness lost the most useful layout evidence at exactly the point where
the user needed it.

## Interfaces and Dependencies

Use only the existing types already imported in `src/foliaseal/presentation/qt/phase3_harness.py`,
especially `SigningRequest` and `SigningDraftWorkflow`. No new third-party dependency is needed.

The public surface affected by this work is:

- `Phase3HarnessCapture` JSON payloads
- `build_phase3_checklist_results_markdown()`
- `_snapshot_visible_signature_appearance()`
- the end-of-run capture assembly in `run_phase3_signing_harness()`

Update note: created on 2026-04-01 after the latest manual harness run showed that blocked
submissions still leave `backend_reservation_snapshot` empty. This child plan narrows the worker
scope to preserving that evidence and making the actual-output snapshot easier to inspect.

Update note: revised on 2026-04-01 after implementation and verification completed. The revision
records the synthesized current-draft request path, the new visible-appearance alias keys, and the
focused test/lint results so the next contributor can resume from the current validated state.
