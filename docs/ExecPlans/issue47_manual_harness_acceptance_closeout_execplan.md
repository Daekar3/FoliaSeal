# Close Issue 47 Manual Harness Acceptance

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

Issue #47 asked for a manual acceptance pass over the visually sensitive horizontal `single_line` signature cases. The latest manual run found one defect, cap 9 border clipping without red validation, while the other cap previews and signed PDFs looked acceptable. That defect has now been converted into a focused child plan and fixed. This close-out slice gathers the final evidence, records why the issue can be closed, and leaves the repository ready for the next architecture or build-process slice.

## Progress

- [x] (2026-05-02T15:00Z) Created this close-out ExecPlan for Issue #47.
- [x] (2026-05-02T15:00Z) Reviewed Issue #47 acceptance criteria and the completed manual harness sanity and cap 9 validation-honesty plans.
- [x] (2026-05-02T15:01Z) Ran focused automated verification for the manual cap ladder, canonical preview geometry replay, signed parity manifest coverage, and cap 9 regression.
- [x] (2026-05-02T15:01Z) Updated this plan with the verification results and closure rationale.
- [x] (2026-05-02T15:01Z) Closed GitHub Issue #47 after focused verification stayed green.
- [x] (2026-05-02T15:01Z) Prepared the documentation and issue-status updates for the close-out commit.

## Surprises & Discoveries

- Observation: Issue #47 does not require new production code if the existing focused evidence still passes.
  Evidence: its acceptance criteria are manual-harness judgments for cap 4 through cap 8, signed preview/PDF appearance, and converting any mismatch into a focused issue. The only reported mismatch was cap 9 validation honesty, which is now covered by `docs/ExecPlans/cap9_single_line_validation_honesty_execplan.md`.

- Observation: cap 9 was outside the original Issue #47 checklist but still blocked honest closure.
  Evidence: the user reported that cap 9 should be red because characters were severely cut off by the border; the child plan added `test_single_line_rendered_ink_fallback_rejects_border_flush_text` and tightened backend validation.

## Decision Log

- Decision: treat this as a documentation/status close-out slice, not a new layout behavior change.
  Rationale: the manual acceptance defect has already been fixed. The remaining work is to prove and record that Issue #47's criteria are either satisfied or represented by completed follow-up work.
  Date/Author: 2026-05-02 / Codex

- Decision: use focused automated backstops plus the user's manual review notes instead of launching a new interactive GUI session from this loop.
  Rationale: the latest manual run is the human visual evidence. The current environment cannot add a better human judgment by running an offscreen GUI, so the useful work is to verify the durable tests and documentation that preserve that judgment.
  Date/Author: 2026-05-02 / Codex

## Outcomes & Retrospective

This plan is in progress. It is complete when focused verification is recorded here and GitHub Issue #47 is closed or a concrete remaining blocker is named.

Focused verification passed and Issue #47 is closed. The issue could be closed because the user completed the manual visual review, the only reported mismatch was converted into the cap 9 validation-honesty fix, and the focused automated backstops for the manual cap ladder and parity manifest remain green.

## Context and Orientation

Issue #47 is titled "Run manual harness acceptance pass for horizontal single-line parity." Its acceptance criteria are:

- Cap 4-style geometry remains red when the selected stamp has no real lane.
- Cap 5/6-style geometry shows improved stamp sizing and acceptable text/stamp spacing.
- Cap 7/8-style geometry validates green when it visibly fits.
- Signed PDF appearance matches preview for text, stamp, and rounded border.
- Harness artifacts are reviewed and any remaining mismatch is converted into a new focused issue.

The parent manual evidence lives in `docs/ExecPlans/manual_harness_sanity_pass_execplan.md`. The cap 9 follow-up lives in `docs/ExecPlans/cap9_single_line_validation_honesty_execplan.md`. The durable cap ladder fixture is `tests/fixtures/phase3_horizontal_single_line_manual_replay.json`.

The focused automated backstops are:

- `tests/unit/test_phase3_signing_backend.py::test_manual_caps_4_to_8_replay_backend_validation_ladder`, which preserves the backend red/green validation ladder for the manual cap geometries.
- `tests/unit/test_signing_preview_renderer.py::test_manual_caps_4_to_8_replay_preserves_preview_geometry`, which preserves canonical preview spacing and non-overlap for the manual cap geometries.
- `tests/unit/test_phase3_signing_backend.py::test_single_line_rendered_ink_fallback_rejects_border_flush_text`, which preserves the cap 9 validation-honesty fix.
- `tests/unit/test_phase3_harness.py::test_signed_preview_parity_manifest_covers_layout_families_and_positions`, which keeps the signed parity manifest representative across layout families and stamp positions.

## Plan of Work

First, run the focused tests listed above. If they fail, inspect the failure and update this plan with the remaining blocker instead of closing Issue #47.

Second, update `docs/ExecPlans/manual_harness_sanity_pass_execplan.md` and this plan with the close-out judgment. The judgment should state that Issue #47's manual acceptance criteria are satisfied by the user manual review plus the completed cap 9 validation-honesty fix.

Third, close GitHub Issue #47 with a concise reason that names the evidence and the cap 9 follow-up fix.

Fourth, commit this close-out documentation slice. Do not include generated artifact directories in the commit.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/SignPDF/Scratch

Run focused verification:

    .venv/bin/pytest -q tests/unit/test_phase3_signing_backend.py::test_manual_caps_4_to_8_replay_backend_validation_ladder tests/unit/test_signing_preview_renderer.py::test_manual_caps_4_to_8_replay_preserves_preview_geometry tests/unit/test_phase3_signing_backend.py::test_single_line_rendered_ink_fallback_rejects_border_flush_text tests/unit/test_phase3_harness.py::test_signed_preview_parity_manifest_covers_layout_families_and_positions

Run documentation hygiene:

    git diff --check

Close the GitHub issue only after the focused verification passes:

    gh issue close 47 --comment "Closed after the manual harness acceptance pass was reviewed, the cap 9 validation-honesty mismatch was fixed, and focused cap-ladder/parity checks passed."

## Validation and Acceptance

Acceptance for this close-out slice means the focused pytest command passes, `git diff --check` is clean, Issue #47 is closed on GitHub, and this ExecPlan records the closure rationale.

## Idempotence and Recovery

The focused tests are safe to repeat. Closing Issue #47 is safe only once; if a later problem is found, open a new focused issue rather than reopening this acceptance-pass issue unless the problem directly invalidates the recorded manual review.

## Artifacts and Notes

Do not commit new generated harness artifact directories in this slice. The important durable artifacts are the ExecPlans and focused test output.

Focused verification output from 2026-05-02:

    .venv/bin/pytest -q tests/unit/test_phase3_signing_backend.py::test_manual_caps_4_to_8_replay_backend_validation_ladder tests/unit/test_signing_preview_renderer.py::test_manual_caps_4_to_8_replay_preserves_preview_geometry tests/unit/test_phase3_signing_backend.py::test_single_line_rendered_ink_fallback_rejects_border_flush_text tests/unit/test_phase3_harness.py::test_signed_preview_parity_manifest_covers_layout_families_and_positions
    4 passed in 7.30s

    git diff --check
    no output

GitHub issue close result:

    gh issue close 47 --comment "Closed after the manual harness acceptance pass was reviewed..."
    Closed issue #47 (Run manual harness acceptance pass for horizontal single-line parity)

## Interfaces and Dependencies

This slice should not change production Python code. It depends on GitHub CLI access for closing Issue #47 and on the existing pytest environment for focused verification.

Revision note: Created 2026-05-02 by Codex as the `$dev-loop` close-out slice for Issue #47.

Revision note: Updated 2026-05-02 by Codex after focused verification passed and before closing Issue #47.

Revision note: Updated 2026-05-02 by Codex after closing GitHub Issue #47.
