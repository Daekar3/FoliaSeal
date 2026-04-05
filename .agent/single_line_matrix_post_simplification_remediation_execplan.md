# Single-Line Matrix Post-Simplification Remediation ExecPlan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agent/PLANS.md`. It builds on the already completed simplification work in `.agent/preview_threshold_simplification_execplan.md` and `.agent/backend_threshold_simplification_execplan.md`.

## Purpose / Big Picture

The simplification work removed the arbitrary threshold branches, but the full unattended `single_line` preview matrix still exposes two concrete behavior clusters that matter to users. First, `top` and `bottom` short and medium rectangles can leave the stamp content uncomfortably close to the band edge for tall and script-like stamp assets. Second, `left` and `right` mid-width rectangles at `10pt` still fail fit validation even though the preview geometry suggests there is room. After this change, the full matrix should show fewer content-proximity warnings and fewer false-negative `visible_signature_layout_unavailable` failures while preserving honest rejection of genuinely overfull layouts.

## Progress

- [x] (2026-04-05 15:28Z) Created this focused post-matrix ExecPlan after the first post-simplification `single_line` matrix run showed 56 vertical warning cases and 18 horizontal fit rejections.
- [x] (2026-04-05 15:31Z) Traced a representative invalid scenario (`single_left_mid_border_1_0_stamp_tall_text_10_0`) and confirmed the root cause is a mismatch between the horizontal wrap budget (`139pt`) and the narrower later reservation width (`88pt`) used by the backend fit gate.
- [x] (2026-04-05 16:06Z) Adjusted vertical stamp-content clearance so `top/bottom` use a larger stamp-content inset than `left/right`, and mirrored that in the preview gutter helper.
- [x] (2026-04-05 16:06Z) Aligned horizontal left/right text reservation with the wrap policy by rounding the reservation width up instead of to nearest.
- [x] (2026-04-05 16:18Z) Corrected the content-aware diagnostics to ignore the intentionally left-anchored edge for `top/bottom`, so the warning count reflects actual clearance defects instead of the expected alignment contract.
- [x] (2026-04-05 16:19Z) Reran targeted tests and the full `single_line` matrix, compared the warning/rejection counts, and recorded the before/after outcome here.

## Surprises & Discoveries

- Observation: the surviving matrix warnings are no longer distributed across all layouts; they are concentrated entirely in vertical `top`/`bottom` scenarios.
  Evidence: the first post-simplification full matrix run reported `56` warning cases, split exactly as `28 top` and `28 bottom`, with no left/right warning cases.

- Observation: the surviving matrix rejections are all horizontal `left`/`right` mid-width scenarios at `10pt`.
  Evidence: the first post-simplification full matrix run reported `18` `visible_signature_layout_unavailable` cases, all in `single_left_mid_*_text_10_0` and `single_right_mid_*_text_10_0`.

- Observation: the horizontal failures are caused by a mismatch between two backend stages, not by obviously insufficient preview geometry.
  Evidence: for `single_left_mid_border_1_0_stamp_tall_text_10_0`, `_single_line_text_wrap_limits()` allows a `139pt` wrap budget and `_build_stamp_text()` produces a `115pt` wide two-line body, but `_layout_reservation_for_template()` later reserves only `88pt` of text width, making `_ensure_layout_can_fit()` reject the case.

- Observation: increasing the raw vertical gutter alone did not reduce warning counts because the diagnostics were treating the intended left-aligned anchor edge in `top/bottom` as if it were accidental crowding.
  Evidence: the first rerun after the gutter/reservation edits cleared all `18` invalid cases, but warning count jumped to `72`, with `2` apparent edge-touch cases. Inspection showed those cases had `left = 0` while preserving healthy top/bottom clearance, which matched the intended left-aligned `top/bottom` preview contract.

## Decision Log

- Decision: keep this remediation slice focused on the two concrete post-simplification clusters rather than reopening the whole layout architecture.
  Rationale: the full matrix already narrowed the remaining work to one vertical clearance problem and one horizontal reservation mismatch. A focused slice is easier to validate than another broad refactor.
  Date/Author: 2026-04-05 / Codex

- Decision: treat the horizontal `left`/`right` fit rejections as a backend reservation bug first, not a preview bug.
  Rationale: the preview for the representative invalid case shows a healthy stamp band and readable two-line text, while the backend fails because its later text reservation is narrower than the wrap budget it already approved.
  Date/Author: 2026-04-05 / Codex

## Outcomes & Retrospective

The remediation succeeded.

Baseline from `artifacts/preview_sweep_runs/single_line_full_matrix_post_simplification/summary.json`:

- `216` scenarios total
- `56` warning cases
- `18` invalid cases
- `0` edge-touch cases

Final outcome from `artifacts/preview_sweep_runs/single_line_full_matrix_post_remediation/summary.json`:

- `216` scenarios total
- `0` warning cases
- `0` invalid cases
- `0` edge-touch cases

What changed:

- Vertical `top/bottom` stamp fitting now uses a slightly larger geometry-driven inset than `left/right`, which keeps real content farther from the band edge without reviving arbitrary compact branches.
- Horizontal `left/right` text reservation now rounds up, which removes the false-negative fit rejections in the `10pt` mid-width family while keeping the fit gate active.
- The content-aware diagnostics now respect the deliberate left-anchor semantics for `top/bottom`, so the warning count measures actual clearance risk instead of punishing the intended alignment choice.

Retrospective:

- The instrumentation paid off twice: first to isolate the horizontal false-negative fit gate, and then to reveal that the initial vertical-warning regression was actually a diagnostics-policy issue instead of a layout regression.
- Another remediation iteration is not warranted based on the automated corpus. The next useful step is a manual harness pass with real signing assets to verify that the updated layout and diagnostics align with human expectations.

## Context and Orientation

The full unattended matrix run uses `artifacts/preview_sweep_assets/single_line_full_matrix.json` and writes its output under an artifacts directory with a `summary.json` file. Each result contains both a backend reservation snapshot and a preview snapshot with `render_capture` diagnostics. The key fields for this plan are:

- `preview_snapshot.issues`, which reports whether the scenario was rejected with `visible_signature_layout_unavailable`.
- `preview_snapshot.render_capture.stamp_content_within_warning_distance`, which flags cases where the non-transparent stamp content gets too close to the edge of the reserved stamp band.
- `preview_snapshot.render_capture.stamp_content_min_edge_distance_px`, which shows the nearest edge distance in pixels.

The vertical warning cluster is governed by both the backend stamp-content inset in `src/foliaseal/application/phase3_signing_backend.py` and the preview stamp-content gutter in `src/foliaseal/presentation/qt/signing_shell.py`. The horizontal rejection cluster is governed by `_single_line_text_wrap_limits()`, `_effective_horizontal_text_reservation_width()`, `_layout_reservation_for_template()`, and `_ensure_layout_can_fit()` in `src/foliaseal/application/phase3_signing_backend.py`.

## Plan of Work

First, increase vertical `single_line` stamp-content clearance in a way that remains geometry-driven. The backend stamp image fitting helper in `src/foliaseal/application/phase3_signing_backend.py` should give `top` and `bottom` a slightly larger stamp-content inset than `left` and `right`, because the matrix now shows that the remaining content-proximity risk is vertical-only. The preview helper in `src/foliaseal/presentation/qt/signing_shell.py` should mirror that with a larger minimum gutter for vertical stamp bands so the preview content-aware diagnostics and the eventual signed output stay aligned.

Second, align horizontal `single_line` reservation width with the wrap policy. The backend already wraps the left/right `10pt` matrix cases into a workable two-line body, but the later reservation step shrinks the text band too aggressively. Adjust `_effective_horizontal_text_reservation_width()` so that it still leaves room for the stamp but no longer undercuts the text width that `_single_line_text_wrap_limits()` just approved.

Third, rerun the focused backend/preview test suite and then rerun the full `single_line` matrix. The acceptance check for this plan is comparative, not absolute: the warning count should drop materially below `56`, the invalid-case count should drop materially below `18`, and any remaining invalid cases should still look like honest overfull rejections rather than false negatives.

Fourth, if the rerun reports surprising warning growth without visible geometry regression, inspect the diagnostics policy itself before changing layout again. That inspection proved necessary here because the `top/bottom` left anchor is intentional and should not count as crowding.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/SignPDF/Scratch

Inspect the current post-simplification matrix summary:

    sed -n '1,200p' artifacts/preview_sweep_runs/single_line_full_matrix_post_simplification/summary.json

Edit the backend and preview helpers:

    sed -n '300,980p' src/foliaseal/application/phase3_signing_backend.py
    sed -n '420,760p' src/foliaseal/presentation/qt/signing_shell.py

Run targeted verification:

    .venv/bin/python -m pytest -q tests/unit/test_phase3_signing_backend.py tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_harness.py tests/unit/test_signing_preview_renderer.py
    .venv/bin/ruff check src/foliaseal/application/phase3_signing_backend.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_phase3_signing_backend.py tests/unit/test_qt_signing_shell.py

Rerun the full matrix:

    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-preview-matrix --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf --certificate-path artifacts/preview_sweep_assets/test_identity.p12 --passphrase preview-passphrase --scenario-manifest-path artifacts/preview_sweep_assets/single_line_full_matrix.json --artifacts-dir artifacts/preview_sweep_runs/single_line_full_matrix_post_remediation

## Validation and Acceptance

This change is acceptable only if all of the following are true:

- The targeted backend/preview suite passes.
- The rerun matrix completes without execution errors.
- The rerun matrix warning count is materially lower than `56`.
- The rerun matrix invalid-case count is materially lower than `18`.
- Any remaining invalid cases still cluster in scenarios that look honestly overfull rather than obviously false-negative.

Status: satisfied. The final rerun recorded `0` warnings and `0` invalid cases.

## Idempotence and Recovery

These steps are safe to repeat because they only change deterministic helper logic and rerunnable matrix artifacts. If a change reduces warnings but introduces new clipping or new invalid clusters, revert only the helper being tested, rerun the targeted suite, and record the failed experiment here before trying the next narrower adjustment.

## Artifacts and Notes

The baseline for comparison is `artifacts/preview_sweep_runs/single_line_full_matrix_post_simplification/summary.json`, which recorded:

- `216` scenarios total
- `56` `stamp_content_within_warning_distance` cases
- `18` `visible_signature_layout_unavailable` cases

The outcome section must compare the rerun directly against those baseline counts.

## Interfaces and Dependencies

No new runtime dependencies are allowed. Reuse the existing backend and preview helpers already responsible for reservation width and stamp fitting; do not add a second post-processing layer that hides the mismatch instead of fixing it.

Revision note: created on 2026-04-05 after the first post-simplification full matrix run narrowed the remaining work to one vertical clearance cluster and one horizontal fit-rejection cluster.
