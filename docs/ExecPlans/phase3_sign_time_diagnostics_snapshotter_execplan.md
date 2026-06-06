# Extract Phase 3 sign-time diagnostics snapshotter

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the interactive Phase 3 harness should keep the same sign-time fit diagnostics payload inside preview captures, but `src/foliaseal/presentation/qt/phase3_harness.py` will stop owning `_snapshot_sign_time_fit_diagnostics(...)` inline. The user-visible proof stays the same: preview captures still preserve the backend fit measurements plus the canonical preview geometry snapshot that downstream evidence and debugging flows use. The architectural gain is one dedicated boundary for sign-time diagnostics shaping instead of one more harness-local payload builder embedded in the large Phase 3 module.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/phase3_appearance_snapshotter_execplan.md` is complete.
- [x] `docs/ExecPlans/phase3_signed_output_render_snapshotter_execplan.md` is complete.

## Progress

- [x] (2026-06-06 23:05Z) Re-read the remaining Phase 3 harness shaping helpers and chose sign-time diagnostics as the next narrowest extracted boundary below the appearance snapshotter.
- [x] (2026-06-06 23:18Z) Extracted `Phase3SignTimeDiagnosticsSnapshotter` into `src/foliaseal/presentation/qt/phase3_sign_time_diagnostics_snapshotter.py` and reduced the harness helper to a thin delegating wrapper.
- [x] (2026-06-06 23:26Z) Added `tests/unit/test_phase3_sign_time_diagnostics_snapshotter.py` and moved the focused payload proof there.
- [x] (2026-06-06 23:29Z) Ran the focused diagnostics validation, Ruff, and `git diff --check`.
- [x] (2026-06-06 23:35Z) Reconciled `docs/ARCHITECTURE.md`, closed this ExecPlan, and prepared the slice for commit.

## Surprises & Discoveries

- Observation: the diagnostics helper only needs the harness-local `_mapping(...)` collaborator, but the payload itself is a real seam because it merges two different evidence sources into one stable capture contract.
  Evidence: `_snapshot_sign_time_fit_diagnostics(...)` combines backend reservation metrics with canonical preview geometry fallbacks and is consumed as one `sign_time_diagnostics` snapshot inside preview evidence.

## Decision Log

- Decision: extract sign-time diagnostics before lower-level geometry/parity helpers.
  Rationale: it is the next smallest Phase 3 harness-owned payload builder with a direct call site, a focused existing proof, and no downstream API churn.
  Date/Author: 2026-06-06 / Codex

## Outcomes & Retrospective

This slice completed successfully. `src/foliaseal/presentation/qt/phase3_sign_time_diagnostics_snapshotter.py` now owns the merged sign-time diagnostics payload that Phase 3 preview evidence stores under `sign_time_diagnostics`. `src/foliaseal/presentation/qt/phase3_harness.py` keeps `_snapshot_sign_time_fit_diagnostics()` as a thin delegating wrapper and remains the composition root that wires the real repository mapping helper into the extracted boundary.

The focused test shape is narrower now. `tests/unit/test_phase3_sign_time_diagnostics_snapshotter.py` owns the backend-fit plus canonical-preview-geometry proof, while `tests/unit/test_phase3_harness.py` keeps only the delegation proof for the harness wrapper. The preview-evidence payload contract stayed stable throughout the extraction.

Focused validation that passed for this slice:

- `.venv/bin/python -m pytest tests/unit/test_phase3_sign_time_diagnostics_snapshotter.py tests/unit/test_phase3_harness.py tests/unit/test_qa_signed_acceptance_evidence.py -k 'sign_time_diagnostics_snapshotter or sign_time_fit_diagnostics or run_signed_acceptance_evidence'`
- `.venv/bin/ruff check src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/presentation/qt/phase3_sign_time_diagnostics_snapshotter.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_sign_time_diagnostics_snapshotter.py tests/unit/test_qa_signed_acceptance_evidence.py`
- `git diff --check`

## Context and Orientation

The Phase 3 runtime now has extracted boundaries for signed-output render analysis, output snapshot shaping, appearance snapshot shaping, and matrix/session runners. The remaining harness-owned seams are narrower, but `phase3_harness.py` still carries the sign-time fit diagnostics payload builder inline.

That helper currently merges backend reservation measurements with canonical preview render geometry into one diagnostics payload that is stored inside the preview snapshot. The payload is useful for acceptance-evidence debugging because it shows both the backend fit gate and the preview-side geometry in one structure.

This slice must keep that payload exactly the same because existing preview evidence and tests rely on its field names and fallback behavior.

## Plan of Work

Create a new helper module at `src/foliaseal/presentation/qt/phase3_sign_time_diagnostics_snapshotter.py`. That module should own the sign-time diagnostics payload shaping while keeping the lower-level harness mapping helper injectable.

Update `src/foliaseal/presentation/qt/phase3_harness.py` so `_snapshot_sign_time_fit_diagnostics()` delegates to the new helper instead of keeping the full merge logic inline. The harness file should remain the composition root that wires the real repository callables into that helper.

Add a focused test module, `tests/unit/test_phase3_sign_time_diagnostics_snapshotter.py`, that exercises the extracted helper directly. Leave only a thin delegation proof in `tests/unit/test_phase3_harness.py`.

Finally, update `docs/ARCHITECTURE.md` so the Phase 3 runtime section names the new sign-time diagnostics snapshotter explicitly and explains that `phase3_harness.py` now delegates this preview-evidence shaping step to it. Keep `docs/SPEC.md` unchanged unless implementation reveals an actual behavior mismatch.

## Concrete Steps

Work from `/home/daekar/FoliaSeal`.

1. Create `src/foliaseal/presentation/qt/phase3_sign_time_diagnostics_snapshotter.py` and move the sign-time diagnostics payload shaping there.
2. Update `src/foliaseal/presentation/qt/phase3_harness.py` to build and delegate to the new helper.
3. Add `tests/unit/test_phase3_sign_time_diagnostics_snapshotter.py` and reduce the moved diagnostics proof from `tests/unit/test_phase3_harness.py`.
4. Run:

    `.venv/bin/python -m pytest tests/unit/test_phase3_sign_time_diagnostics_snapshotter.py tests/unit/test_phase3_harness.py tests/unit/test_qa_signed_acceptance_evidence.py -k 'sign_time_fit_diagnostics or run_signed_acceptance_evidence'`

5. Run:

    `.venv/bin/ruff check src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/presentation/qt/phase3_sign_time_diagnostics_snapshotter.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_sign_time_diagnostics_snapshotter.py tests/unit/test_qa_signed_acceptance_evidence.py`

6. Run:

    `git diff --check`

7. Reconcile `docs/ARCHITECTURE.md` and close this ExecPlan.

## Validation and Acceptance

Acceptance is behavioral. The sign-time diagnostics payload must keep the same backend-fit and canonical-preview-geometry fields while their shaping becomes directly testable in one dedicated helper.

The slice is complete when:

- `src/foliaseal/presentation/qt/phase3_sign_time_diagnostics_snapshotter.py` owns the diagnostics payload shaping;
- `src/foliaseal/presentation/qt/phase3_harness.py` delegates `_snapshot_sign_time_fit_diagnostics(...)` instead of keeping the full logic inline;
- the new focused diagnostics test passes without broad harness monkeypatching;
- `ruff check` and `git diff --check` pass cleanly.

## Idempotence and Recovery

This slice is additive and safe to retry. If the helper import or delegation shape is wrong, restore `_snapshot_sign_time_fit_diagnostics(...)` in the harness first, rerun the focused tests, and then retry the extraction. Do not mix deeper preview-analysis rewrites into this slice.

## Artifacts and Notes

The primary allowed change class for the implementation commit is internal architecture only. Documentation/status updates may follow if required by the compliance review.

## Interfaces and Dependencies

The extracted helper module should end with a stable name for:

- a dedicated sign-time diagnostics snapshotter boundary that accepts:
  - preview render capture,
  - backend reservation snapshot,
  - injected mapping helper;
- and an explicit method for building the merged diagnostics payload.

`src/foliaseal/presentation/qt/phase3_harness.py` should remain the composition root that wires the real repository callables into that helper.

Revision note: Created on 2026-06-06 by Codex after the appearance snapshotter slice exposed sign-time diagnostics as the next narrowest harness-owned payload builder.
