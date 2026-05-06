# Phase 3 Harness Visual Capture and Scenario Matrix

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this change, a Phase 3 harness run will produce enough GUI evidence that an agent can inspect the actual preview appearance instead of inferring behavior from semantic state alone. The harness will capture preview-card screenshots, rendered widget geometry, and explicit edge-distance metrics, and it will support a repeatable scenario matrix so a contributor can sweep stamp images, border widths, stamp positions, and rectangle shapes without manually reconfiguring the GUI every time.

The user-visible proof is straightforward. Run the interactive harness with preview artifact output enabled and inspect the written PNG/JSON files. Then run the new scenario-matrix command against a JSON manifest and inspect the artifact directory; each scenario will have its own preview capture, geometry metrics, and summary entry that can be reviewed without relaunching the GUI manually for each permutation.

## Progress

- [x] (2026-04-04 21:02Z) Read `Agents.md`, `.agents/skills/write-execplan/PLANS.md`, `src/foliaseal/presentation/qt/phase3_harness.py`, `src/foliaseal/__main__.py`, and the existing harness tests to scope the missing instrumentation surface.
- [x] (2026-04-04 22:10Z) Implemented interactive harness preview artifact capture, widget geometry snapshots, and explicit edge-distance metrics, including preview PNG output, widget bounds, size hints, spacing, and border-to-content distance telemetry.
- [x] (2026-04-04 22:28Z) Implemented a repeatable `phase3-signing-preview-matrix` runner with manifest-driven appearance overrides, per-scenario artifact directories, and summary JSON output.
- [x] (2026-04-04 22:41Z) Updated `README.md`, `docs/ExecPlans/phase3_parallel_plan.md`, `artifacts/phase3_handoff_2026-04-03.md`, and the template artifacts so future contributors can run the new instrumentation without reconstructing the workflow.
- [x] (2026-04-04 22:55Z) Added regression coverage for the new preview capture payloads and CLI surface, then completed focused verification with `106` passing tests across the touched harness, parser, preview, and backend suites.

## Surprises & Discoveries

- Observation: the current Phase 3 harness already captures semantic preview state, request state, backend reservation diagnostics, and final output appearance metadata, but it does not capture the actual Qt-rendered preview card or any geometry for the preview widgets.
  Evidence: `src/foliaseal/presentation/qt/phase3_harness.py` serializes `preview_snapshot`, `backend_reservation_snapshot`, and `output_visible_appearance_snapshot`, while `_snapshot_preview()` currently stops at semantic fields such as `layout_template`, `box_style`, and `fields`.

- Observation: the remaining `single_line/bottom` bug reports are now dominated by how the preview is rendered, not by a total absence of backend reservation data.
  Evidence: the latest harness capture contains `background_layout`, `content_layout`, and their margins/alignment, but the visual imbalance still cannot be judged mechanically because no preview PNG or widget bounds are recorded.

## Decision Log

- Decision: extend the existing interactive harness instead of creating a separate preview-debug tool.
  Rationale: Phase 3 acceptance already flows through `phase3-signing-harness`, so the new evidence must live in the same capture path to stay useful for real acceptance and debugging runs.
  Date/Author: 2026-04-04 / Codex

- Decision: add a scenario-matrix runner as a separate CLI command rather than overloading the interactive harness with hidden automation behavior.
  Rationale: the interactive harness should remain a human-operated acceptance tool, while scenario sweeps need deterministic batch behavior and artifact naming that are easier to express as a dedicated command.
  Date/Author: 2026-04-04 / Codex

## Outcomes & Retrospective

The harness can now produce the visual evidence that was previously missing. Interactive runs may write preview-card PNGs plus geometry-rich `render_capture` data directly into the capture JSON, and the new preview-matrix command can sweep named scenarios from a JSON manifest to produce one artifact set per scenario. That closes the main loop that was slowing down preview/layout debugging: contributors no longer need to describe what they saw by hand before an agent can reason about the GUI output.

The implementation stayed additive and low-risk. It reused the existing harness/shell objects instead of introducing a second preview-debug codepath, and it kept the batch sweep separate from the human-operated acceptance harness so each mode remains understandable. The biggest follow-on opportunity is expanding the matrix manifests and asset corpus over time so repeated regressions can be caught with saved scenario sets rather than recreated ad hoc.

## Context and Orientation

The interactive Phase 3 harness lives in `src/foliaseal/presentation/qt/phase3_harness.py`. That file launches the Qt signing shell, records semantic capture data, and writes the JSON/Markdown artifacts used by acceptance review. The shell itself lives in `src/foliaseal/presentation/qt/signing_shell.py`, where the preview card is built and updated. The CLI surface for both harness commands lives in `src/foliaseal/__main__.py`.

In this repository, a “preview card” means the visible signature appearance widget shown inside the Phase 3 signing shell. A “scenario matrix” means a JSON file that lists multiple named preview configurations so the harness can apply them one by one and capture artifacts for each. A “geometry snapshot” means the rendered size and position of the preview card and its key child widgets, measured in Qt widget coordinates after layout has settled.

The missing capability is concrete GUI evidence. Today the harness can say what layout and border width were requested, but it cannot show what Qt actually drew. That is why iterative fixes keep depending on human reports. This change fills that gap by capturing preview images and geometry directly from the running UI.

## Plan of Work

First, extend `src/foliaseal/presentation/qt/phase3_harness.py` so the interactive harness can optionally write preview artifacts. The harness will accept an artifact-directory path, capture the preview card pixmap, and write a PNG plus a JSON-friendly geometry snapshot. The preview snapshot payload will gain a `render_capture` section that records the artifact file path, preview card size, inner body size, title/detail/stamp widget bounds, pixmap size, layout spacing, and explicit top/bottom/left/right distances from the preview border to the rendered content bands.

Second, add small helper functions in `src/foliaseal/presentation/qt/phase3_harness.py` that can read the preview controls from the built shell and compute those distances deterministically. The geometry data must come from the actual widgets after `refresh_preview()` and after Qt has processed layout updates. The helper must not swallow failures silently; if a preview artifact cannot be captured, the capture payload should include an explicit error string.

Third, add a dedicated batch command in `src/foliaseal/__main__.py` plus corresponding harness support that reads a JSON scenario manifest. Each scenario will define a name plus appearance and placement overrides such as layout template, stamp position, image stamp path, border width, and signature rectangle. The runner will build the shell, apply each scenario deterministically, refresh the preview, capture the preview artifact and geometry, append a per-scenario summary object, and write an overall matrix summary JSON. This command is for preview validation only; it does not need to submit a signing request.

Fourth, update `README.md` and `docs/ExecPlans/phase3_parallel_plan.md` so contributors know that preview debugging should now use visual artifacts rather than terminal output alone. Add a short operator-facing note to `artifacts/phase3_handoff_2026-04-03.md` or a refreshed handoff artifact so the next contributor knows where the preview PNGs and matrix summaries live and how to use them.

Fifth, add or update tests in `tests/unit/test_phase3_harness.py` and `tests/unit/test_cli_parser.py`. The tests must cover the new preview capture fields, the matrix-manifest parsing path, and the new CLI command wiring. Focus the assertions on observable payload shape and deterministic artifact naming rather than brittle pixel data.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Run the focused harness and CLI tests after implementation:

    .venv/bin/pytest -q tests/unit/test_phase3_harness.py tests/unit/test_cli_parser.py

Run the preview-related shell/backend tests to ensure the new harness capture does not regress preview behavior:

    .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py

Exercise the new scenario-matrix command with a JSON manifest:

    .venv/bin/python -m foliaseal phase3-signing-preview-matrix \
      --pdf-path "/path/to/test.pdf" \
      --certificate-path "/path/to/identity.p12" \
      --passphrase "secret" \
      --scenario-manifest-path artifacts/phase3_preview_matrix.json \
      --artifacts-dir artifacts/phase3_preview_matrix

Expected command behavior after implementation:

    Phase 3 preview matrix
    - scenarios executed: <N>
    - artifacts directory: artifacts/phase3_preview_matrix
    - summary json: artifacts/phase3_preview_matrix/summary.json

## Validation and Acceptance

The new behavior is accepted when all of the following are true:

- Running `foliaseal phase3-signing-harness` with preview artifact output enabled writes a preview PNG and records its file path plus geometry metrics in the capture JSON.
- The preview snapshot records enough geometry to compare top/bottom and left/right content distances without relying on visual guesswork.
- Running `foliaseal phase3-signing-preview-matrix` against a manifest writes one artifact set per scenario plus a summary JSON that names the scenarios and their preview captures.
- The new tests pass, and existing Phase 3 harness evidence validation still passes.
- The updated docs explain when to use the interactive harness versus the batch preview matrix.

## Idempotence and Recovery

This work is additive. Re-running the interactive harness or the preview-matrix command with the same artifact directory is safe; files may be overwritten with fresh captures for the same scenario names. If an artifact capture fails partway through a scenario matrix, the summary JSON should still include the scenario and record the explicit error so the run can be retried after fixing the underlying problem. No destructive recovery step is required.

## Artifacts and Notes

The most important artifacts produced by this work are:

- preview card PNG captures for interactive or matrix runs
- geometry-rich preview capture JSON entries
- a scenario-matrix summary JSON that an agent can inspect without reopening the GUI

## Interfaces and Dependencies

In `src/foliaseal/presentation/qt/phase3_harness.py`, extend `Phase3HarnessCapture` so the JSON can carry preview artifact metadata. The preview snapshot payload should gain a nested `render_capture` mapping with stable keys such as `preview_image_path`, `card_size_px`, `single_body_size_px`, `multi_body_size_px`, `detail_label_bounds_px`, `stamp_label_bounds_px`, `multi_detail_bounds_px`, `multi_stamp_bounds_px`, `layout_spacing_px`, and explicit edge-distance metrics.

In `src/foliaseal/__main__.py`, add a `phase3-signing-preview-matrix` command that accepts a scenario manifest path and an artifacts directory. The manifest format must be JSON and must be simple enough to hand-edit. Each scenario object must at least support `name`, `signature_rect`, and an `appearance_overrides` object for common preview controls.

Do not add new runtime dependencies. Use the existing Qt objects already available in the harness and shell.

Revision note: created on 2026-04-04 to make Phase 3 preview debugging self-sufficient by capturing rendered GUI evidence and enabling repeatable scenario sweeps.

Revision note (2026-04-04, completion): the harness now records preview PNGs, widget geometry, and border-distance metrics, exposes `--artifacts-dir` on the interactive command, adds the `phase3-signing-preview-matrix` command, ships a starter scenario manifest template, and documents the new workflow in the Phase 3 README and handoff notes.
