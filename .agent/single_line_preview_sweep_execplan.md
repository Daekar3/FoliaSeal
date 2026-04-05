# Phase 3 Single-Line Preview Sweep and Fixes

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agent/PLANS.md`.

## Purpose / Big Picture

After this work, the new preview-matrix instrumentation will be used the way it was intended: to run an unattended sweep of `single_line` preview configurations across `top`, `bottom`, `left`, and `right`, using multiple border weights, stamp assets, and signature-rectangle shapes. Any spacing, scaling, or overlap defects discovered in those captures will be fixed in code and locked down with tests.

The user-visible proof is straightforward. A single batch command should generate a directory full of preview PNGs plus geometry metrics, and those captures should be clean enough that an agent can identify whether `single_line` layouts are balanced and non-overlapping without relying on a human description of what appeared on screen.

## Progress

- [x] (2026-04-04 23:10Z) Read `Agents.md`, the PDF skill instructions, the new matrix-runner implementation, and the relevant Phase 3 planning docs to set the sweep scope.
- [x] (2026-04-04 23:28Z) Generated repository-local sweep assets: a four-page PDF fixture, a valid local PKCS#12, three transparent stamp images, and a 12-scenario single-line matrix manifest.
- [x] (2026-04-04 23:45Z) Ran the preview matrix offscreen, inspected the generated PNGs and geometry metrics, and identified two real problems: the harness capture path did not handle real Qt widget visibility correctly, and compact vertical single-line preview bands could clip text because the preview used reservation proportions without respecting Qt label size hints.
- [x] (2026-04-05 00:09Z) Implemented the required harness/preview fixes, added regression coverage, and reran the matrix plus focused tests successfully.
- [x] (2026-04-05 00:12Z) Updated this ExecPlan with the sweep findings, local asset locations, and the final verification outcome.
- [x] (2026-04-05 01:20Z) Expanded the manifest and harness overrides so sweep scenarios can pin `visible_fields` and vary text size explicitly, then reran the matrix to make the captures easier to interpret.
- [x] (2026-04-05 01:47Z) Fixed the remaining preview-side single-line issues surfaced by the refreshed sweep review: stale widget size constraints were bleeding between scenarios, compact vertical previews were letting text overtake the reserved stamp band, and separator slack was not being returned to the stamp band.

## Surprises & Discoveries

- Observation: the repository now has enough harness instrumentation to support an unattended visual sweep, but it still needs a curated scenario set to make that power practical.
  Evidence: `src/foliaseal/presentation/qt/phase3_harness.py` can write preview PNGs and edge-distance metrics, and `phase3-signing-preview-matrix` can apply manifest scenarios, but the checked-in template only contains two starter cases.

- Observation: the first real offscreen run found a gap between the fake-widget tests and PySide itself.
  Evidence: `_capture_preview_render()` was reading `.visible` directly, which worked with the fake test doubles but crashed against real Qt widgets that expose `isVisible()`.

- Observation: compact vertical `single_line` preview clipping was primarily a preview-layout issue, not a backend reservation issue.
  Evidence: the matrix PNGs showed text clipping and nearly invisible stamps in valid `top`/`bottom` scenarios, while the backend continued to report `Ready to sign.` for the compact cases that actually fit.

- Observation: several deliberately broad scenarios are invalid by design once the content becomes too verbose, and the new matrix now makes that obvious.
  Evidence: the final summary in `artifacts/preview_sweep_runs/single_line_matrix/summary.json` cleanly separates valid `Ready to sign.` scenarios from the intentionally overfull cases that emit `visible_signature_layout_unavailable`.

- Observation: compact single-line sweeps are much easier to judge when the manifest constrains the visible field set explicitly.
  Evidence: after adding `visible_fields` support to matrix overrides and updating the checked-in sweep to focus most compact cases on `common_name` plus `signing_time`, the left/right tight scenarios became readable enough to distinguish geometry bugs from content-density noise.

- Observation: part of the stubborn bottom/compact preview drift was stateful rather than purely geometric.
  Evidence: preview labels were carrying fixed-size constraints from prior scenarios, which meant later matrix captures could inherit stale height assumptions and overgrow the text band before the current scenario had even been measured.

## Decision Log

- Decision: prefer repository-local generated assets over personal user files for the automated sweep when the environment supports it.
  Rationale: local assets make the sweep reproducible and safe to rerun by agents or CI-style scripts without depending on machine-specific paths.
  Date/Author: 2026-04-04 / Codex

- Decision: keep the sweep broad, but normalize the local certificate subject and manifest page selection so the “valid” scenarios stay focused on layout behavior instead of avoidable setup noise.
  Rationale: the goal of this pass is to judge preview layout quality, not to spend most of the matrix on stale page-selection errors or pathological field verbosity.
  Date/Author: 2026-04-05 / Codex

- Decision: teach the matrix manifest to override `visible_fields` and include explicit text-size variants instead of inferring those permutations from whatever happens to be in the active appearance.
  Rationale: that keeps scenario intent obvious and makes future unattended sweeps useful for both field-density and font-size regression checks.
  Date/Author: 2026-04-05 / Codex

- Decision: for compact vertical `single_line` preview, treat the backend reservation split as authoritative and only add a tiny Qt safety slack rather than expanding the text band all the way to the live label hint.
  Rationale: the matrix showed that honoring the full live hint made bottom-mode previews consume the stamp band and produce misleadingly tiny or invisible stamps even when the backend still considered the scenario valid.
  Date/Author: 2026-04-05 / Codex

## Outcomes & Retrospective

The unattended sweep is now genuinely useful. It can be run entirely from repository-local assets, it produces preview PNGs that are easy to inspect without a human operator, and it already paid for itself by catching multiple issues the earlier unit coverage missed: a real-Qt visibility bug in the harness capture path, compact vertical preview clipping caused by sizing the preview bands purely from backend reservation proportions, stale widget geometry leaking between matrix scenarios, and compact separator slack being wasted as dead air instead of preserving stamp size.

After the latest fixes, the valid `single_line` scenarios in the checked-in matrix look materially better. Compact `bottom` previews now keep the stamp visible in cases where it was previously reduced to a barely perceptible sliver, compact `top`/`bottom` cases share a more faithful stamp/text split, and `left`/`right` sweeps are easier to judge because the manifest now constrains the visible field set explicitly and includes text-size variants. The remaining edge cases are now narrower: mostly product-judgment questions about how close to the border a compact valid scenario should be allowed to look, rather than obvious preview bugs or hidden scenario ambiguity.

## Context and Orientation

The preview-matrix command lives in `src/foliaseal/presentation/qt/phase3_harness.py` and is exposed through `src/foliaseal/__main__.py`. The single-line preview layout logic lives primarily in `src/foliaseal/presentation/qt/signing_shell.py`, while the backend reservation and visible-signature layout logic live in `src/foliaseal/application/phase3_signing_backend.py`.

The new instrumentation captures two kinds of evidence: PNG images of the real rendered preview card, and JSON geometry/spacing metrics that quantify the relationship between the border and the content bands. Both are needed: the metrics can flag likely imbalances quickly, and the PNGs let the agent visually confirm what the user would actually see.

## Plan of Work

First, create a small, stable local asset suite under `artifacts/` or `tmp/` that includes one test PDF and multiple distinct stamp images. The stamp suite should include at least one wide signature-like image, one taller/narrower mark, and one transparent asset so the sweep covers different scaling behavior. Then create a scenario manifest that combines those assets with `single_line` top/bottom/left/right, multiple border widths, and several rectangle aspect ratios.

Second, run the matrix command in an offscreen Qt session so the sweep is unattended. Inspect both the summary JSON and the captured PNGs. Use the recorded border-to-content distances as quick triage, but treat the PNGs as the source of truth for whether spacing looks balanced and whether borders encroach on text or imagery.

Third, if any defects appear, fix them in the smallest shared layout path that covers preview/backend parity without speculative refactors. Add tests that encode the discovered failure modes, rerun the focused test suite, and rerun the matrix until the captures are clean.

Fourth, update this ExecPlan and any directly relevant documentation so the sweep findings and any new test assets/manifests are easy to reuse.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/SignPDF/Scratch

Generate or refresh the local sweep assets and manifest, then run the matrix:

    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-preview-matrix \
      --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf \
      --certificate-path artifacts/preview_sweep_assets/test_identity.p12 \
      --passphrase "preview-passphrase" \
      --scenario-manifest-path artifacts/preview_sweep_assets/single_line_matrix.json \
      --artifacts-dir artifacts/preview_sweep_runs/single_line_matrix

Run the focused verification after any fixes:

    .venv/bin/pytest -q tests/unit/test_phase3_harness.py tests/unit/test_cli_parser.py \
      tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_signing_backend.py \
      tests/unit/test_signing_preview_renderer.py

## Validation and Acceptance

The work is accepted when all of the following are true:

- The matrix command completes using repository-local assets without depending on personal user paths.
- The sweep covers `single_line` `top`, `bottom`, `left`, and `right` across multiple border weights and rectangle shapes.
- Captured PNGs show no obvious overlap or severe padding imbalance for the exercised scenarios.
- Any discovered defects are fixed in code and backed by regression tests.
- The ExecPlan records what was found and what changed.

## Idempotence and Recovery

This work is additive. Re-running the asset-generation step should overwrite the local sweep assets deterministically. Re-running the preview matrix should overwrite the corresponding PNG/JSON artifacts with fresh captures. If a scenario fails, keep its artifact directory and error record so the failure can be diagnosed and the sweep can be rerun after a fix.

## Artifacts and Notes

The main artifacts produced by this work are:

- a repository-local sweep PDF and stamp-image suite
- a reusable single-line scenario manifest
- preview PNGs and summary JSON for the matrix run
- any regression tests added to lock in fixes

## Interfaces and Dependencies

Do not add new runtime dependencies. Prefer existing `Pillow`, `PySide6`, and the current harness code. Keep the sweep Linux-only and offscreen-friendly in line with current project scope.

Revision note: created on 2026-04-04 to drive the first unattended, repository-local sweep of Phase 3 single-line preview configurations using the new harness instrumentation.

Revision note (2026-04-05, completion): the sweep now ships with local PDF/stamp/certificate fixtures under `artifacts/preview_sweep_assets/`, a reusable matrix manifest, real-Qt-safe harness capture logic, compact vertical preview band fitting that respects Qt size hints, and regression tests covering both the harness and preview fixes.

Revision note (2026-04-05, follow-up): the matrix manifest now supports explicit `visible_fields` control and checked-in text-size variants, while the preview layout now clears stale widget-size constraints between scenarios and returns reclaimed separator slack to the compact vertical stamp band.
