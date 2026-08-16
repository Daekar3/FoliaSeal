# Audit the current live signing harness and its headless evidence

This ExecPlan is a living document and must be maintained in accordance with
`/home/daekar/.codex/skills/write-execplan/PLANS.md`. It replaces the historical
`manual_harness_sanity_pass_execplan.md`, whose command names and module paths predate the
acceptance-nomenclature migration.

## Purpose / Big Picture

The automated signing evidence is green, but the project still needs an honest user-facing check
of the current signing harness. This slice will regenerate the ignored local QA inputs, run the
current headless evidence workflow, inspect representative preview and signed-output artifacts, and
attempt the same four tracer-bullet cases through the live Qt path. A successful result will provide
current, restartable evidence for three comfortable signing cases and one intentional fit rejection;
if the environment cannot display Qt, the plan will record that exact external limitation instead of
claiming that a manual GUI review happened.

The user-visible outcome is evidence that a real operator would see a coherent preview, a matching
signed PDF, and a clear rejection without an output file. This plan is an evidence/status slice, not
a license for speculative rendering changes. Any concrete visual defect must become its own targeted
implementation plan.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/signed_evidence_gate_separation_execplan.md` closed the automated strict gates:
  18 successful preview-parity signings and 3 matched fit rejections.
- [x] `docs/SPEC.md` and `docs/UI_SPEC.md` are the governing behavior documents for preview fidelity,
  validation honesty, signing state, and user-facing error reporting.
- [x] A display-enabled Cinnamon/X11 environment is now available for the bounded live Qt portion.
  Offscreen Qt remains sufficient for deterministic evidence but cannot prove what a human sees.

## Progress

- [x] (2026-08-16) Fresh explorer review confirmed the historical manual plan is stale: its
  `phase3-*` commands and `phase3_harness.py` path no longer exist.
- [x] (2026-08-16) Fresh explorer identified current commands (`interactive-harness`, `signed-acceptance`,
  and `signed-acceptance-evidence`), the four suitable tracer cases, and the ignored QA inputs that
  must be regenerated.
- [x] (2026-08-16) Fresh environment check found `DISPLAY=:0`, but `xdpyinfo -display :0` cannot open
  it; this is a display-access blocker for the live HITL portion, not for offscreen Qt evidence.
- [x] (2026-08-16) Regenerated the fixture PDF, identity, stamp, and all three manifests under
  `/tmp/foliaseal-current-harness-audit` through `signed-acceptance-evidence`.
- [x] (2026-08-16) Ran the current strict gates: parity passed with 18 successful signings and fit
  rejection passed with 3 matched intentional rejections. Inspected the four selected tracer rows'
  preview/analysis/comparison artifacts and structured summaries.
- [x] (historical sandboxed attempt, 2026-08-16) The sandboxed `interactive-harness` HITL attempt
  could not open `DISPLAY=:0` and the xcb Qt plugin aborted before the shell started. That historical
  limitation did not describe the later unsandboxed Cinnamon/X11 session below.
- [x] (2026-08-16) Re-ran the current `interactive-harness` on the real Cinnamon/X11 session with
  an explicit available checklist template. The harness window was observed and closed normally;
  it returned `0`, wrote a valid summary/results pair, and left no owned FoliaSeal process, dialog,
  or temporary root. This closes the bounded X11 launch/visual-checkpoint/cleanup gate, but not the
  four-tracer-case human walkthrough or the separate accessibility/package gates.
- [x] (2026-08-16) Reconciled the historical plan/status references, completed explorer compliance
  review, updated the current architecture/README evidence-mode wording, removed the temporary
  evidence root and generated caches, and confirmed no GUI/process debris remains. The four-case
  display-dependent HITL walkthrough checkbox remains open; the bounded X11 launch/visual-checkpoint
  gate is complete, and commit of this documentation/evidence-status slice remains.

## Surprises & Discoveries

- Observation: the historical manual plan is not executable from the current checkout.
  Evidence: `phase3-signing-harness`, `phase3-signing-acceptance-matrix`, and
  `src/foliaseal/presentation/qt/phase3_harness.py` are absent after the nomenclature migration.
- Observation: the repository intentionally does not track the QA PDF, PKCS#12 identity, stamp, or
  generated manifests required by the harness.
  Evidence: the current checkout lacks those files under `artifacts/`; the supported evidence command
  generates them locally and they are ignored disposable inputs.
- Observation: the current environment advertises `DISPLAY=:0` but cannot open that display.
  Evidence: `xdpyinfo -display :0` returns `unable to open display ":0"`; therefore an offscreen run
  cannot be described as human visual acceptance.
- Observation: the safest tracer set avoids known single-line stress/clipping boundaries while still
  covering no-stamp, image-stamp, wrapped-block, and rejection behavior.
  Evidence: the current generator names are `single_line_top_no_stamp_sparse_large`,
  `multi_line_top_medium_relaxed`, `wrapped_block_right_medium_relaxed`, and
  `single_line_left_stamp_sparse_large`.
- Observation: the current strict run produces coherent visual artifacts for all three successful
  tracer rows and a clear rejection preview; the no-stamp row's comparison metadata reports
  `output_image_presence_matches_preview=false` and `output_text_bounds_match_preview=false`, but
  its layer comparison, text fragments, and overall `preview_vs_signed_output_passed` remain true.
  Evidence: the generated comparison image for `single_line_top_no_stamp_sparse_large` shows matching
  text and border on both sides; the two image-presence fields are known diagnostic projections, not
  strict failure counters.
- Observation: the attempted live command fails before Qt window creation, not after leaving a dialog
  open.
  Evidence: `interactive-harness` exits `134` with `qt.qpa.xcb: could not connect to display :0` and
  `Could not load the Qt platform plugin "xcb"`; the process audit is empty afterward.

## Decision Log

- Decision: create a new current audit plan and mark the older manual plan historical rather than
  silently editing its dated evidence into a false current claim.
  Rationale: the old plan preserves provenance, but its commands and module names are invalid after
  the migration; a restartable current plan must name only live interfaces.
  Date/Author: 2026-08-16 / Codex.
- Decision: separate headless evidence from live HITL acceptance.
  Rationale: offscreen Qt can prove artifact generation and structured contracts, but only a display
  can prove the visual experience a human sees. The two claims must not be conflated.
  Date/Author: 2026-08-16 / Codex.
- Decision: use the existing evidence generator and runners, not a new manual runner or layout change.
  Rationale: the current architecture already owns scenario setup, signing, capture, and evidence;
  adding another path would create a second contract and obscure defects.
  Date/Author: 2026-08-16 / Codex.
- Decision: close the headless evidence portion while keeping the live HITL checkbox open.
  Rationale: the current structured and visual artifact evidence is strong enough to prove the
  deterministic contract, but the display failure is an environmental limitation and cannot prove
  human GUI behavior. The next display-enabled run must reuse this exact tracer set.
  Date/Author: 2026-08-16 / Codex.

## Outcomes & Retrospective

The deterministic portion completed on 2026-08-16. The strict command wrote
`/tmp/foliaseal-current-harness-audit/summary.md` and passed exactly two required gates:

- `signed_preview_parity_matrix`: 18 scenarios, 18 successful signings, zero preview/output
  comparison failures, and zero scenario errors;
- `signed_fit_rejection_matrix`: 3 scenarios, zero successful signings, and 3 matched intentional
  rejections.

The four selected rows have preview/analysis images and structured evidence. The three successful
rows also have signed PDFs, normalized crops, and side-by-side comparisons; direct inspection found
coherent border, stamp, and text placement. The rejection row reports the expected fit message and
`output_file_exists=false`. The earlier live display attempt was incomplete because the sandboxed xcb
process could not open the available `DISPLAY=:0`; a later bounded unsandboxed Cinnamon/X11 run
reached the harness and closed cleanly. No production defect was discovered in either review. The
four-case human walkthrough remains open because the bounded run intentionally stopped at a
representative visual checkpoint.

Documentation/compliance review and cleanup are complete. Current architecture and README wording
now distinguish deterministic headless/offscreen evidence from display-backed human acceptance;
`docs/SPEC.md` remains unchanged because it is frozen. The bounded X11 launch gate is complete,
while the four-case human GUI walkthrough, accessibility, package, and final release gates remain
open.

## Context and Orientation

The application-facing evidence boundary is `src/foliaseal/application/evidence_service.py`; its
strict command runs the success-only `signed_preview_parity_matrix` and the rejection-only
`signed_fit_rejection_matrix`. The generated manifests and fixture assets come from
`src/foliaseal/application/qa_signed_acceptance_generation.py`. Qt composition and scenario capture
are now split across `src/foliaseal/presentation/qt/interactive_harness.py`,
`acceptance_harness_workspace.py`, `interactive_harness_session_runner.py`,
`preview_matrix_runner.py`, and `signed_acceptance_matrix_runner.py`.

The four tracer cases are deliberately representative rather than boundary stress tests:

- `single_line_top_no_stamp_sparse_large`: comfortable no-image baseline;
- `multi_line_top_medium_relaxed`: comfortable image-stamp, two-region layout;
- `wrapped_block_right_medium_relaxed`: comfortable wrapped-block image-stamp layout;
- `single_line_left_stamp_sparse_large`: expected validation rejection with a deliberately small
  rectangle.

## Plan of Work

First, run the current command help and generate a fresh evidence root under `/tmp`. The generator
must create the fixture PDF, identity, stamp image, and all three manifests. Then run the strict
evidence command and retain its Markdown/JSON summary long enough to inspect counters and the four
tracer rows. Use the standalone `signed-acceptance` command only when it is necessary to inspect the
mixed diagnostic manifest; it must not replace the strict gates.

Next, inspect the generated preview images, signed-output crops/comparisons, structured snapshots,
validation issues, and rejection output paths for the four named cases. If the display can be opened,
launch the current `interactive-harness` command with the generated fixture inputs and perform the
same short human review. If it cannot, record the exact display diagnostic and leave the HITL box
unchecked.

Finally, update this plan, mark the old plan as superseded, update architecture/status documentation
only where current facts changed, run the full relevant validation, remove every disposable root and
generated cache, audit processes/dialogs, and commit only the evidence/status changes or a concrete
targeted defect fix discovered by the audit.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    .venv/bin/python -m foliaseal interactive-harness --help
    .venv/bin/python -m foliaseal signed-acceptance --help
    .venv/bin/python -m foliaseal signed-acceptance-evidence --help
    rm -rf /tmp/foliaseal-current-harness-audit
    mkdir -p /tmp/foliaseal-current-harness-audit
    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal signed-acceptance-evidence \
      --artifacts-root /tmp/foliaseal-current-harness-audit \
      --summary-markdown-path /tmp/foliaseal-current-harness-audit/summary.md

The 2026-08-16 run produced the expected two passing rows. The four tracer names were found in the
generated manifests and summaries, and the inspected artifact paths were under
`/tmp/foliaseal-current-harness-audit/artifacts/signed_acceptance_evidence/`; none are committed.

Check display access explicitly before attempting HITL:

    printf 'DISPLAY=%s\\n' "${DISPLAY-}"
    xdpyinfo -display "${DISPLAY:-:0}" >/tmp/foliaseal-display-check.txt

The 2026-08-16 check failed with `xdpyinfo: unable to open display ":0"`. The subsequent current
`interactive-harness` attempt exited `134` before window creation because the xcb plugin could not
connect; the process audit found no remaining FoliaSeal, PySide6, or pytest process. On a display-
enabled rerun, launch the command using the help-documented options and close the application
normally after the four cases.

## Validation and Acceptance

The deterministic portion is accepted when the strict command exits zero, reports exactly the two
required gates, and the selected success rows have preview images, signed-output crops/comparisons,
and structured snapshots with no unexpected errors. The rejection row must report the expected
validation issue and no signed PDF path.

The human portion is accepted only when a display-backed operator can inspect the three successful
previews alongside their signed outputs and the rejection state, then close the harness cleanly.
When display access is unavailable, acceptance is explicitly partial: headless evidence may close,
but the HITL requirement remains open for the next display-enabled slice.

Also run the focused evidence tests, full test suite, Ruff, compileall, `git diff --check`, and the
active terminology scan. The final process audit must show no `foliaseal`, `PySide6`, or `pytest`
processes and no stray dialogs owned by the run.

## Idempotence and Recovery

Each run uses a new explicit temporary root and can be repeated safely. If generation or signing
fails, retain the summary until the failure is classified, then remove the root before retrying. Do
not delete tracked files or weaken validators to obtain a green result. If a live Qt process remains,
close it through its normal exit path first; use process termination only for a process demonstrably
owned by this audit, and record the cleanup.

## Artifacts and Notes

Only concise counters, artifact paths, and display diagnostics belong in this plan. PDFs, identities,
stamps, screenshots, JSON manifests, and signed outputs are disposable local evidence. The old plan
remains as historical provenance; this file is the sole current owner of the audit status.

## Interfaces and Dependencies

Use the existing CLI entry points in `src/foliaseal/__main__.py`, the injected evidence service in
`src/foliaseal/application/evidence_service.py`, and the current Qt harness composition in
`src/foliaseal/presentation/qt/interactive_harness.py`. Do not add a compatibility alias for retired
command names or module paths. Keep the application boundary Qt-free and keep generated evidence
outside the repository.

Revision note: 2026-08-16 / Codex
Created after a fresh explorer audit found the historical manual plan stale, the ignored QA assets
absent, and the current display unavailable. This plan separates headless evidence that can proceed
now from the genuinely display-dependent HITL claim.

Revision note: 2026-08-16 / Codex
Recorded the regenerated two-gate evidence, four-row artifact inspection, failed sandboxed
display-backed attempt, and clean process result. The deterministic audit is complete; live HITL
remained explicitly open until the later unsandboxed X11 checkpoint below.

Revision note: 2026-08-16 / Codex
Recorded compliance findings, supersession-reference cleanup, temporary-root removal, and the final
process audit. No production behavior changed in this evidence/status slice.

Revision note: 2026-08-16 / Codex
Recorded the newly available unsandboxed Cinnamon/X11 session, the successful interactive-harness
visual checkpoint and clean close, the explicit checklist-template friction, and the remaining
four-case/accessibility/package gates. Wayland is intentionally deferred until Mint provides a
first-class supported session.

Revision note: 2026-08-16
The sibling `x11_parent_workflow_acceptance_execplan.md` completed the deeper source-tree semantic
parent audit on the same Cinnamon/X11 session: 19 checkpoints passed through two locally verified
signatures and reopen. This strengthens the X11 source-tree evidence but does not close this plan's
four-case human walkthrough, screen-reader/high-contrast/DPI/monitor, packaged, privileged-install,
or final release gates. Wayland remains intentionally deferred.
