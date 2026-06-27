# Move Phase 3 Checklist Rendering Behind The Reporting Boundary

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

This slice is complete. The Phase 3 reporting boundary owns both the final file-writing orchestration and the checklist Markdown renderer, and `phase3_harness.py` now delegates to that reporting-owned renderer instead of defining the formatter locally. A contributor reading the reporting boundary can see the whole post-Qt reporting flow in one place instead of chasing formatting logic back into the large harness module.

The user-visible behavior did not change. The proof is that the generated checklist text stayed byte-for-byte compatible for representative captures, while the tests that assert checklist content live in `tests/unit/test_phase3_harness_reporting.py` instead of the broad harness test file.

## Child ExecPlan Dependencies

- [x] (2026-06-27 00:00Z) The three caller-facing `Phase3Harness` facade slices landed in commits `dba9a8c20`, `14bf61082`, and `0e0ddc41b`, so this follow-on seam can focus on the reporting boundary without mixing entrypoint-shape work.
- [x] (2026-06-27 00:00Z) No child ExecPlans are required for this bounded extraction slice.

## Progress

- [x] (2026-06-27 00:00Z) Ran the required dev-loop explorer audit and selected the reporting-renderer extraction as the safest next seam.
- [x] (2026-06-27 00:00Z) Re-read the current reporting module, checklist renderer, helper cluster, and direct tests.
- [x] (2026-06-27 00:00Z) Wrote this ExecPlan before implementation.
- [x] (2026-06-27 00:00Z) Added the reporting-boundary checklist-rendering coverage in `tests/unit/test_phase3_harness_reporting.py`.
- [x] (2026-06-27 00:00Z) Moved the checklist renderer and checklist-only helper cluster behind `src/foliaseal/presentation/qt/phase3_harness_reporting.py`.
- [x] (2026-06-27 00:00Z) Kept `finalize_phase3_harness_report()` behavior unchanged while switching it to the reporting-owned default renderer.
- [x] (2026-06-27 00:00Z) Re-homed the direct checklist-rendering assertions into `tests/unit/test_phase3_harness_reporting.py` and trimmed the broad harness test file.
- [x] (2026-06-27 00:00Z) Ran focused validation, completed the required compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this ExecPlan, and recorded the result here.
- [x] (2026-06-27 00:00Z) Reconciled docs and prepared the slice for the required commit step in the larger dev-loop.

## Surprises & Discoveries

- Observation: the reporting boundary already owned the right orchestration seam, and the extraction completed without changing the report-finalization contract.
  Evidence: `finalize_phase3_harness_report()` in `src/foliaseal/presentation/qt/phase3_harness_reporting.py` evaluates the evidence contract, creates the finalized capture object, writes summary JSON, renders checklist text through the reporting-owned callable, and writes the checklist file. The renderer now lives in `src/foliaseal/presentation/qt/phase3_harness_reporting.py`.

## Decision Log

- Decision: extract the checklist renderer with its checklist-only helper cluster into the reporting boundary instead of creating a generic shared utility module first.
  Rationale: the formatting logic is already conceptually part of report finalization, and this narrower move gives the reporting boundary the behavior it already claims to own without opening a second naming or ownership question.
  Date/Author: 2026-06-27 / Codex

- Decision: leave helper logic in `phase3_harness.py` when it also serves non-reporting harness behavior.
  Rationale: this slice is only for checklist/report-rendering logic. Shared helpers that are still consumed elsewhere should either stay in place or be duplicated trivially to avoid widening into unrelated extraction work.
  Date/Author: 2026-06-27 / Codex

## Outcomes & Retrospective

The renderer extraction is complete. The reporting boundary now owns the default checklist Markdown renderer, the harness path delegates directly to that renderer, and the checklist-specific assertions live in the reporting test surface. The cleanup pass is done and the behavior of `finalize_phase3_harness_report()` stayed stable.

## Context and Orientation

The relevant files are:

- `src/foliaseal/presentation/qt/phase3_harness.py`
- `src/foliaseal/presentation/qt/phase3_harness_reporting.py`
- `tests/unit/test_phase3_harness.py`
- `tests/unit/test_phase3_harness_reporting.py`

`phase3_harness_reporting.py` defines `build_phase3_checklist_results_markdown(...)` plus the checklist-only helper cluster that derives auto-checked items and renders diagnostic summary lines from `Phase3HarnessCapture`. `phase3_harness.py` imports that renderer and passes it into `finalize_phase3_harness_report(...)` while keeping the interactive harness orchestration separate from report formatting.

This slice stayed narrow. It did not change the interactive harness flow, the capture payload contract, the evidence contract evaluation, or the file-writing order. It moved checklist-rendering ownership to the reporting boundary and relocated the tests that exercise that behavior.

The safety net now sits primarily in `tests/unit/test_phase3_harness_reporting.py`, which is the direct home for checklist-rendering assertions, and secondarily in `tests/unit/test_phase3_harness.py`, which keeps covering the broad harness behavior without owning the formatter details.

## Plan of Work

First, a red-phase checklist-rendering test was added in `tests/unit/test_phase3_harness_reporting.py` by moving or copying one of the current direct Markdown assertions from `tests/unit/test_phase3_harness.py`. The test exercises the reporting-owned renderer through its public surface and pins representative output lines such as acceptance tier, request snapshot origin, visible appearance details, and auto-checked checklist items.

Second, the checklist renderer and the checklist-only helper cluster were moved into `src/foliaseal/presentation/qt/phase3_harness_reporting.py`. If importing `Phase3HarnessCapture` directly would create a cycle, the renderer should stay typed loosely there and rely on the capture object’s existing attributes instead of pulling the concrete dataclass back across the boundary. Leave any helper that still serves non-reporting harness logic in `phase3_harness.py`.

Third, `finalize_phase3_harness_report()` kept its behavior unchanged. It continues to accept an injected renderer for tests, and the reporting module is the natural owner of the default checklist renderer implementation. `phase3_harness.py` now imports and uses the reporting-owned renderer instead of defining it locally.

Fourth, the direct checklist-rendering tests were moved or removed from `tests/unit/test_phase3_harness.py`, leaving the harness test file focused on harness orchestration rather than report formatting internals.

Fifth, focused validation was run, the required compliance review was performed, and `docs/ARCHITECTURE.md` did not need a wording fix because it already matched the reporting-boundary ownership split. `docs/SPEC.md` stayed unchanged because the rendered worksheet contract did not change.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Edit these files:

    src/foliaseal/presentation/qt/phase3_harness.py
    src/foliaseal/presentation/qt/phase3_harness_reporting.py
    tests/unit/test_phase3_harness.py
    tests/unit/test_phase3_harness_reporting.py
    docs/ExecPlans/phase3_harness_reporting_renderer_execplan.md
    docs/ARCHITECTURE.md   # only if wording needs reconciliation

Suggested order:

1. Add a failing reporting-owned renderer test.
2. Move the renderer and checklist-only helpers into the reporting boundary.
3. Switch the harness module to use the reporting-owned renderer.
4. Re-home or trim the old harness-file renderer assertions.
5. Re-run focused tests and hygiene.
6. Perform the required compliance review.

Run focused validation as the slice progresses:

    .venv/bin/python -m pytest -q tests/unit/test_phase3_harness_reporting.py
    .venv/bin/python -m pytest -q tests/unit/test_phase3_harness.py -k 'checklist_results_markdown or signing_harness'
    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/presentation/qt/phase3_harness_reporting.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_harness_reporting.py
    git diff --check

After the first implementation pass, run the required compliance review against at least:

    docs/ARCHITECTURE.md
    docs/SPEC.md
    docs/ExecPlans/phase3_harness_reporting_renderer_execplan.md

## Validation and Acceptance

This slice is accepted when all of the following are true:

- the default checklist Markdown renderer is owned by the reporting boundary instead of `phase3_harness.py`
- the generated checklist text remains unchanged for representative captures
- the direct checklist-rendering assertions live in the reporting test file
- focused reporting and harness tests pass
- any architecture wording affected by the renderer ownership move is reconciled

Observable proof is a focused test run where the reporting-owned renderer test fails before the move and passes after it, while the interactive harness/report-finalization tests remain green.

## Idempotence and Recovery

This was a behavior-preserving extraction and is safe to retry. If a future pass starts moving non-reporting helpers or creates an import cycle between `phase3_harness.py` and `phase3_harness_reporting.py`, stop and re-scope the extraction so the reporting boundary owns only the checklist-rendering logic and any checklist-only helpers.

## Artifacts and Notes

Capture and keep concise:

- the focused reporting renderer test run
- any compliance finding about whether `docs/ARCHITECTURE.md` needed a renderer-ownership update

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

At the end of the slice, the reporting boundary exposes and owns the effective default renderer shape:

    def build_phase3_checklist_results_markdown(
        capture,
        *,
        checklist_template_path: str,
    ) -> str: ...

`finalize_phase3_harness_report()` continues to accept an injected `checklist_renderer` callable for testability, and the production path in `phase3_harness.py` imports the renderer from the reporting boundary rather than defining it inline.

Revision note: Created on 2026-06-27 by Codex after the required dev-loop explorer selected the checklist/report-rendering extraction as the safest next Phase 3 harness hybrid seam. Updated on 2026-06-27 after the extraction completed and the reporting boundary became the renderer owner.
