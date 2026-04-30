# Stamp Position Harness Follow-Up

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agent/PLANS.md`.

## Purpose / Big Picture

The first real harness pass with the new `Stamp Position` control exposed three important gaps:

- the new `Stamp Position` control is wasting vertical form space
- the shell preview for `single_line` is still behaving incorrectly for several positions
- horizontal `single_line` preview updates can crash the Qt shell with deleted-label errors
- the final signed PDF still does not honor the intended `Top` / `Bottom` behavior, and the stamp
  image is still oversized in the actual PDF appearance

The goal of this corrective wave is to restore shell stability, tighten the preview/layout
contract, and fix the remaining single-line visible-signature behavior so another harness run is
worth doing.

## Progress

- [x] (2026-03-31 00:40Z) Captured the harness findings and created this ExecPlan.
- [x] (2026-03-31 00:41Z) Inspected the shell preview container lifetime bug and current
  `single_line` preview behavior.
- [x] (2026-03-31 00:42Z) Started shell and backend corrective work in parallel with worker
  ExecPlan requirements.
- [x] (2026-03-31 00:52Z) Integrated the local shell fix, condensed the form row, and landed the
  backend `single_line` prefix/body split.
- [x] (2026-03-31 00:55Z) Ran focused verification: 63 passed, lint clean.

## Surprises & Discoveries

- Observation: the shell can still pass all fake-Qt tests while failing in real PySide due to
  widget ownership and layout clearing behavior.
  Evidence: harness run produced repeated `Internal C++ object ... already deleted` failures while
  the fake Qt tests remained green.
- Observation: the immediate PySide crash was self-inflicted by the earlier centering fix, which
  moved `multi_detail_label` out of its dedicated content container and back into the horizontal row.
  Evidence: the crash stack pointed at `_set_container_widgets()` re-adding `QLabel` instances after
  layout clearing, and `multi_detail_label` was being reparented directly instead of the stable
  `multi_content_container`.
- Observation: the actual PDF prefix/body mismatch came from `_build_stamp_text()` treating the
  prefix as just another `single_line` fragment.
  Evidence: the failing focused test expected no newline at all, and the user saw the prefix folded
  into the pipe-separated inline body in the actual PDF.

## Decision Log

- Decision: split this into shell/harness and backend/layout tracks so the Qt lifetime bug does not
  block inspection of the single-line PDF appearance logic.
  Rationale: these failures are related in user experience, but the shell crash and the backend
  stamp-size/layout semantics are separable technical problems.
  Date/Author: 2026-03-31 / Codex
- Decision: restore the horizontal preview row to use the stable `multi_content_container` instead
  of reparenting `multi_detail_label` directly.
  Rationale: the dedicated content container keeps ownership and layout stable under real PySide,
  while still letting the preview align the text block beside the stamp.
  Date/Author: 2026-03-31 / Codex
- Decision: put `Stamp Position` on the same form row as `Signer label prefix`.
  Rationale: the user feedback is correct; both controls are short and fit naturally on one row,
  which frees vertical space in the appearance panel.
  Date/Author: 2026-03-31 / Codex
- Decision: split `single_line` backend text into a prefix line plus a wrapped body line/block when
  a prefix is present.
  Rationale: this matches the product contract implied by the preview and the user’s expectations
  for `Top` / `Bottom`, and avoids folding the prefix into the pipe-separated body text.
  Date/Author: 2026-03-31 / Codex

## Outcomes & Retrospective

- The shell-side deleted-widget crash path is corrected locally, the new control layout is more
  compact, and the backend no longer forces the `single_line` prefix inline with the body text.
- The remaining unresolved question is empirical: whether the stamp image now looks reasonably sized
  and whether `Top` / `Bottom` distinguish themselves clearly enough in the real signed PDF. That
  requires another harness pass.

## Context and Orientation

Relevant files likely include:

- `src/foliaseal/presentation/qt/signing_shell.py`
- `src/foliaseal/presentation/qt/phase3_harness.py`
- `src/foliaseal/application/phase3_signing_backend.py`
- `tests/unit/test_qt_signing_shell.py`
- `tests/unit/test_phase3_signing_backend.py`
- `tests/unit/test_phase3_harness.py`

The current review and harness observations suggest the shell preview is reparenting or clearing
widgets in a way that is safe for fakes but unsafe for real PySide objects. The visible signature
backend also appears not to be honoring `Top` vs `Bottom` distinctly for `single_line`, and the
stamp image is still oversized in the final PDF.

## Plan of Work

First inspect the shell lifetime problem and reproduce the relevant code path locally. Then run two
fix tracks in parallel:

- shell/harness track: fix the deleted-widget crash, improve the `Stamp Position` control layout,
  and tighten preview behavior for `single_line`
- backend track: inspect and correct `single_line` `Top` / `Bottom` semantics and stamp scaling in
  the final PDF appearance

Require any spawned workers to maintain their own ExecPlans and report with explicit changed files,
verification, and caveats.

## Concrete Steps

1. Inspect `signing_shell.py` preview widget/container ownership and control layout.
2. Inspect `phase3_signing_backend.py` single-line layout reservation and final stamp-style logic.
3. Spawn one shell-focused worker and one backend-focused worker, each with an ExecPlan
   requirement.
4. Integrate the resulting changes locally.
5. Run focused tests and lint.

## Validation and Acceptance

Acceptance for this follow-up means:

- changing `Stamp Position` no longer crashes the live Qt shell
- `Stamp Position` control sits on the same row as `Signer label prefix`
- `single_line` preview behaves plausibly for `Top`, `Bottom`, `Left`, and `Right`
- the final PDF distinguishes `Top` and `Bottom` correctly for `single_line`
- the stamp image no longer dominates the rectangle in ordinary cases
- focused tests pass and lint is clean

## Idempotence and Recovery

These fixes are additive and localized. If worker patches overlap, integrate carefully rather than
reverting user-visible improvements from the current tree.

## Artifacts and Notes

- Harness observations from 2026-03-31:
  - `single_line/top` and `single_line/bottom` previews wrapped unexpectedly
  - `single_line/top` and `single_line/bottom` final PDF output looked too similar
  - `single_line/left` caused deleted-widget crashes in the shell
  - actual PDF stamp image remained oversized
- Focused verification after the corrective patch:

      ./.venv/bin/python -m pytest -q tests/unit/test_phase3_signing_backend.py tests/unit/test_qt_signing_shell.py tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_harness.py
      63 passed in 1.37s

      ./.venv/bin/ruff check src/foliaseal/application/phase3_signing_backend.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_phase3_signing_backend.py tests/unit/test_qt_signing_shell.py tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_harness.py
      All checks passed!

## Interfaces and Dependencies

No new dependencies are expected. The main interfaces involved are the Qt preview controls in
`signing_shell.py` and the visible-signature layout helpers in `phase3_signing_backend.py`.

Update note: revised on 2026-03-31 after the first harness-driven corrective patch to record the
local shell fix, the condensed appearance-row layout, the backend `single_line` prefix/body split,
and the focused verification results.
