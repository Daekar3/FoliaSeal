# Extract Phase 3 appearance snapshotter

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the Phase 3 appearance parity model should keep the same `SignatureAppearanceSnapshot` payloads, but `src/foliaseal/presentation/qt/phase3_harness.py` will stop owning both `_preview_appearance_snapshot_from_capture(...)` and `_signed_output_appearance_snapshot(...)` inline. The user-visible proof stays the same: preview-side and signed-output-side appearance snapshots still reconstruct the same border, text, stamp, and line-bound state that downstream parity comparisons rely on. The architectural gain is one dedicated boundary for appearance snapshot shaping instead of two harness-local helpers that define opposite sides of the same comparison model.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/phase3_signed_output_render_snapshotter_execplan.md` is complete.
- [x] `docs/ExecPlans/phase3_signed_output_snapshotter_execplan.md` is complete.

## Progress

- [x] (2026-06-06 18:05Z) Re-read the preview-side and signed-output-side appearance snapshot builders to confirm them as the next narrowest Phase 3 seam.
- [x] (2026-06-06 18:18Z) Extracted `Phase3AppearanceSnapshotter` into `src/foliaseal/presentation/qt/phase3_appearance_snapshotter.py` and reduced both harness helpers to thin delegating wrappers.
- [x] (2026-06-06 18:27Z) Added `tests/unit/test_phase3_appearance_snapshotter.py` and moved the focused preview/signed appearance snapshot proofs there.
- [x] (2026-06-06 18:33Z) Ran the focused appearance-snapshot validation, Ruff, and `git diff --check`.
- [x] (2026-06-06 18:41Z) Reconciled `docs/ARCHITECTURE.md`, closed this ExecPlan, and prepared the slice for commit.

## Surprises & Discoveries

- Observation: the two helpers are not duplicates, but they are still one seam because they shape the two sides of the same `SignatureAppearanceSnapshot` comparison contract.
  Evidence: both helpers produce `SignatureAppearanceSnapshot` values whose fields are consumed together by the signed-output render snapshotter’s appearance parity comparison.
- Observation: the existing focused tests moved cleanly onto the new helper with only thin delegation checks left in the harness file.
  Evidence: the preview border-restoration proof and the signed-output structural-line reconstruction proof now live in `tests/unit/test_phase3_appearance_snapshotter.py`, while `tests/unit/test_phase3_harness.py` only checks wrapper delegation.

## Decision Log

- Decision: extract the appearance snapshot builders together rather than splitting preview-side and signed-output-side shaping into separate slices.
  Rationale: they form one coherent comparison-model boundary, and splitting them would leave the parity contract divided across files without reducing much complexity.
  Date/Author: 2026-06-06 / Codex

## Outcomes & Retrospective

This slice completed successfully. `src/foliaseal/presentation/qt/phase3_appearance_snapshotter.py` now owns both sides of the Phase 3 appearance parity model: preview-side appearance snapshot reconstruction and signed-output-side appearance snapshot reconstruction. `src/foliaseal/presentation/qt/phase3_harness.py` keeps `_preview_appearance_snapshot_from_capture()` and `_signed_output_appearance_snapshot()` as thin delegating wrappers and remains the composition root that wires the real repository callables into the helper.

The focused test shape is narrower now. `tests/unit/test_phase3_appearance_snapshotter.py` owns the preview border-restoration and signed-output structural-line reconstruction proofs, while `tests/unit/test_phase3_harness.py` keeps only the thin delegation proofs for the harness wrappers. The signed-output render snapshotter and evidence-service contract remained stable throughout the extraction.

Focused validation that passed for this slice:

- `.venv/bin/python -m pytest tests/unit/test_phase3_appearance_snapshotter.py tests/unit/test_phase3_signed_output_render_snapshotter.py tests/unit/test_phase3_harness.py tests/unit/test_qa_signed_acceptance_evidence.py -k 'appearance_snapshotter or signed_output_render_snapshotter or preview_appearance_snapshot or signed_output_appearance_snapshot or run_signed_acceptance_evidence'`
- `.venv/bin/ruff check src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/presentation/qt/phase3_appearance_snapshotter.py src/foliaseal/presentation/qt/phase3_signed_output_render_snapshotter.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_appearance_snapshotter.py tests/unit/test_phase3_signed_output_render_snapshotter.py tests/unit/test_qa_signed_acceptance_evidence.py`
- `git diff --check`

## Context and Orientation

The Phase 3 runtime now has extracted boundaries for signed-output render analysis and signed-output evidence shaping. The remaining parity-model seam inside `phase3_harness.py` is the pair `_preview_appearance_snapshot_from_capture(...)` and `_signed_output_appearance_snapshot(...)`.

Those helpers currently shape the two `SignatureAppearanceSnapshot` values that the signed-output render snapshotter compares. One reconstructs preview-side appearance state from captured render evidence; the other reconstructs signed-output-side appearance state from normalized render evidence plus visible-appearance metadata.

This slice must keep the resulting `SignatureAppearanceSnapshot` values exactly the same because the render snapshotter and its tests rely on their fields and parity behavior.

## Plan of Work

Create a new helper module at `src/foliaseal/presentation/qt/phase3_appearance_snapshotter.py`. That module should own both preview-side and signed-output-side appearance snapshot shaping while keeping the lower-level harness collaborators injectable.

Update `src/foliaseal/presentation/qt/phase3_harness.py` so `_preview_appearance_snapshot_from_capture()` and `_signed_output_appearance_snapshot()` delegate to the new helper instead of keeping the full logic inline. The harness file should remain the composition root that wires the real repository callables into that helper.

Add a focused test module, `tests/unit/test_phase3_appearance_snapshotter.py`, that exercises the extracted helper directly. Those tests should verify at least: preview border-style restoration when analysis snapshots omit border metadata, and signed-output structural line-bound reconstruction.

Finally, update `docs/ARCHITECTURE.md` so the Phase 3 runtime section names the new appearance snapshotter explicitly and explains that `phase3_harness.py` now delegates both sides of the appearance parity model to it. Keep `docs/SPEC.md` unchanged unless implementation reveals an actual behavior mismatch.

## Concrete Steps

Work from `/home/daekar/FoliaSeal`.

1. Create `src/foliaseal/presentation/qt/phase3_appearance_snapshotter.py` and move the preview/signed appearance snapshot shaping there.
2. Update `src/foliaseal/presentation/qt/phase3_harness.py` to build and delegate to the new helper.
3. Add `tests/unit/test_phase3_appearance_snapshotter.py` and reduce the moved appearance-snapshot proofs from `tests/unit/test_phase3_harness.py`.
4. Run:

    `.venv/bin/python -m pytest tests/unit/test_phase3_appearance_snapshotter.py tests/unit/test_phase3_signed_output_render_snapshotter.py tests/unit/test_phase3_harness.py tests/unit/test_qa_signed_acceptance_evidence.py -k 'appearance_snapshotter or signed_output_render_snapshotter or preview_appearance_snapshot or signed_output_appearance_snapshot or run_signed_acceptance_evidence'`

5. Run:

    `.venv/bin/ruff check src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/presentation/qt/phase3_appearance_snapshotter.py src/foliaseal/presentation/qt/phase3_signed_output_render_snapshotter.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_appearance_snapshotter.py tests/unit/test_phase3_signed_output_render_snapshotter.py tests/unit/test_qa_signed_acceptance_evidence.py`

6. Run:

    `git diff --check`

7. Reconcile `docs/ARCHITECTURE.md` and close this ExecPlan.

## Validation and Acceptance

Acceptance is behavioral. The preview-side and signed-output-side `SignatureAppearanceSnapshot` values must keep the same fields and meanings while their shaping becomes directly testable in one dedicated helper.

The slice is complete when:

- `src/foliaseal/presentation/qt/phase3_appearance_snapshotter.py` owns both appearance snapshot builders;
- `src/foliaseal/presentation/qt/phase3_harness.py` delegates those builders instead of keeping the full logic inline;
- the new focused appearance-snapshot tests pass without broad unrelated harness monkeypatching;
- the signed-output render snapshotter and evidence-service contract still pass against the unchanged parity payload contract;
- `ruff check` and `git diff --check` pass cleanly.

## Idempotence and Recovery

This slice is additive and safe to retry. If the helper import or delegation shape is wrong, restore the two harness helpers first, rerun the focused tests, and then retry the extraction. Do not mix deeper layout-engine or text-analysis rewrites into this slice.

## Artifacts and Notes

The primary allowed change class for the implementation commit is internal architecture only. Documentation/status updates may follow if required by the compliance review.

## Interfaces and Dependencies

The extracted helper module should end with stable names for:

- a dedicated appearance snapshotter boundary that accepts:
  - preview snapshots / visible-appearance snapshots / normalized image info as appropriate,
  - injected mapping helpers,
  - injected text-style reconstruction,
  - injected structural-line reconstruction,
  - injected visible-appearance text/image helpers,
  - injected rectangle union / text-box reconstruction helpers;
- and explicit methods for the preview-side and signed-output-side snapshot flows.

`src/foliaseal/presentation/qt/phase3_harness.py` should remain the composition root that wires the real repository callables into that helper.

Revision note: Created on 2026-06-06 by Codex after the signed-output render snapshotter slice exposed the appearance parity model as the next narrowest Phase 3 seam.
