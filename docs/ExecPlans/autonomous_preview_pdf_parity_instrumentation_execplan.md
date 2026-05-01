# Autonomous Signature Appearance Instrumentation

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agent/PLANS.md`.

## Purpose / Big Picture

After this change, a contributor should be able to fix preview-versus-signed-PDF appearance defects without depending on a human to inspect every iteration. The repository will produce a shared appearance snapshot for both the preview and the signed PDF, compare those snapshots structurally and visually, and fail tests when the signed PDF drifts from what the preview promised.

The user-visible proof is straightforward. A real harness run will still write the GUI preview and the signed PDF artifacts, but the automation will also write a machine-readable appearance snapshot for each side, a comparison result that explains which layer failed, and a deterministic parity regression suite that can be run repeatedly during implementation. The target outcome is a genuine fix-test-iterate-test loop for visible signature appearance, not merely a pile of screenshots.

## Progress

- [x] (2026-04-19 14:47Z) Added a shared `SignatureAppearanceSnapshot` model plus layered comparison types in `src/foliaseal/application/signing_preview_renderer.py`, and threaded the canonical preview renderer through that model.
- [x] (2026-04-19 14:58Z) Updated `src/foliaseal/presentation/qt/phase3_harness.py` so preview captures and signed-output analysis both emit appearance snapshots and a layer-by-layer parity result instead of only raster-derived booleans.
- [x] (2026-04-19 15:04Z) Added focused regression coverage in `tests/unit/test_signing_preview_renderer.py` and `tests/unit/test_phase3_harness.py` for shared snapshots and structural parity reporting.
- [x] (2026-04-19 15:11Z) Fixed rollout compatibility issues in the Qt shell tests and matrix summary serialization so the richer instrumentation can coexist with existing callers and artifact writers.
- [x] (2026-04-19 15:18Z) Revalidated the slice with `python -m ruff check`, `pytest -q`, and an offscreen signed acceptance matrix run writing to `artifacts/signed_acceptance_matrix_run_autonomous_parity/summary.json`.

## Surprises & Discoveries

- Observation: the repository already has enough rendering infrastructure to produce comparable preview and signed-output crops, but the comparison logic still relies too heavily on pixel inference.
  Evidence: `src/foliaseal/presentation/qt/phase3_harness.py` already writes `interactive_final_analysis.png`, `normalized_signature_crop_path`, and parity booleans, but recent manual RCA showed border pixels being misclassified as text.

- Observation: the preview and the signed PDF now share much more of the same rendering path than they did earlier in the project, but they still do not emit the same structural metadata.
  Evidence: `src/foliaseal/application/signing_preview_renderer.py` returns `CanonicalSignaturePreviewSnapshot` with preview-side bounds, while signed-output analysis in the harness reconstructs meaning from raster images after signing.

- Observation: the current manual harness is still valuable because it exercises the actual Qt shell, but it should no longer be the primary discovery mechanism for appearance mismatches.
  Evidence: the headless preview matrices are stable and the signed acceptance matrix is green, yet parity defects still required manual screenshot review because no first-class border/text/stamp layer comparison existed.

- Observation: matrix and acceptance summaries still write raw Python objects unless they explicitly use the harness JSON serializer.
  Evidence: the first signed acceptance rerun failed with `TypeError: Object of type SignatureAppearanceSnapshot is not JSON serializable` until the summary writers were switched to `_jsonable_capture(...)`.

- Observation: a few Qt shell tests were brittle for reasons unrelated to this slice and surfaced only when the full suite was rerun.
  Evidence: `tests/unit/test_qt_signing_shell.py::test_signing_shell_single_line_horizontal_preview_reserves_width_for_stamp` compared two independently generated preview strings across a minute boundary and had to be rewritten around stable fragments.

## Decision Log

- Decision: treat instrumentation as the primary change class for this slice, with evidence refresh and documentation/status updates allowed only when they directly prove the instrumentation works.
  Rationale: the user asked for autonomous fix-test-iterate behavior. That requires better observability first, not another narrow visual tweak.
  Date/Author: 2026-04-19 / Codex

- Decision: introduce one shared appearance snapshot model for both preview and signed output instead of adding more raster heuristics to the harness.
  Rationale: structural metadata is the only reliable way to compare borders, text blocks, and stamp placement without repeated false positives from dark pixels.
  Date/Author: 2026-04-19 / Codex

- Decision: keep the GUI preview artifact and the analysis artifact separate.
  Rationale: the on-screen preview must stay visually correct for the user, while analysis needs flattened, normalized, comparable surfaces and metadata. Mixing those concerns caused the recent border and parity confusion.
  Date/Author: 2026-04-19 / Codex

- Decision: do not broaden this slice into new layout policy, fit logic, font changes, TSA work, or certification work.
  Rationale: the objective is to make existing appearance defects autonomously diagnosable and testable. Unrelated behavior changes would make the slice hard to evaluate and harder to trust.
  Date/Author: 2026-04-19 / Codex

## Outcomes & Retrospective

This plan starts from a stronger place than earlier instrumentation efforts. The repository already has a canonical preview renderer, a headless preview matrix, a signed acceptance matrix, and a harness that writes preview and signed-output artifacts. What is missing is not raw artifact generation. What is missing is a shared, explicit description of what those artifacts contain and a comparison layer that can distinguish border drift from text drift from stamp drift.

The expected result of this plan is a step change in debugging speed. Instead of repeatedly asking whether a crop “looks different,” the automation should report facts such as “border radius mismatched,” “text block moved 3 px downward,” or “stamp content overflowed the reserved band.” If this plan is completed correctly, the next appearance defect should be fixable from tests and saved evidence without another round of hand inspection just to discover what is wrong.

That result is now in place for the first major slice. The repository can emit a shared structural appearance snapshot for both preview and signed output, the harness can compare those snapshots by layer, and the signing regression suite remains green. The remaining work is not “invent more parity booleans.” The remaining work is to use the richer layer data to drive the next real appearance fixes and, when needed, extend the snapshot model with any additional geometry that a concrete mismatch proves necessary.

## Context and Orientation

The relevant code is split across four main files.

`src/foliaseal/application/phase3_signing_backend.py` is the canonical visible-signature layout and signed-stamp engine. It composes text, sizes stamp images, decides layout reservations, and now also owns the rounded-border stamp drawing path used in the signed PDF.

`src/foliaseal/application/signing_preview_renderer.py` renders a preview of that same visible signature without signing a PDF. In this repository, a “canonical preview” means a preview produced from the same underlying stamp engine that the signed PDF uses, rather than from ad hoc Qt labels.

`src/foliaseal/presentation/qt/phase3_harness.py` is the acceptance harness. It drives the interactive GUI and the headless preview matrix, writes JSON and PNG artifacts, and currently performs the preview-versus-signed-output parity analysis.

`src/foliaseal/presentation/qt/signing_shell.py` is the actual Qt user interface. It remains important because the user still sees and interacts with that shell, but it should not be the only place where appearance truth exists.

In this plan, an “appearance snapshot” means a machine-readable description of one rendered visible signature. It must include more than a flat image path. It must describe the border geometry, the text block geometry, the stamp geometry, the crop size, and the normalization assumptions used to compare it to another render.

In this repository, “parity” means that the preview shown to the user and the visible signature embedded into the signed PDF match closely enough that the preview is a trustworthy promise. The current harness already records parity booleans. This plan upgrades that into a layered comparison model that can explain failures and drive autonomous iteration.

The relevant documents already point in this direction. `README.md` and `docs/ExecPlans/phase3_parallel_plan.md` treat preview/output parity as a first-class acceptance concern. `docs/pdf_signing_app_feasibility.md` Phase 4A explicitly calls for stronger preview/output instrumentation, structured comparisons, and reduced reliance on manual harness runs.

## Plan of Work

Start by defining a shared snapshot type in `src/foliaseal/application/signing_preview_renderer.py` or a new nearby module such as `src/foliaseal/application/signature_appearance_snapshot.py`. The type should be plain data. It should describe one rendered visible signature in normalized coordinates. It must include the image path or in-memory image reference, the full crop bounds, the border bounds and style, the text bounds, the stamp bounds, and any line-level text geometry that the renderer can expose without guesswork. If a field is not available for a given render, record that explicitly as `None` rather than letting downstream code guess.

Then update `render_canonical_signature_preview(...)` so it returns this richer snapshot instead of only ad hoc pixel bounds. The preview side already knows the layout reservation, the border style, and the rendered bounds. That information should be promoted into the snapshot directly. Preserve the existing GUI preview behavior. The change here is to make the analysis output first-class and explicit.

Next, upgrade the signed-output analysis path in `src/foliaseal/presentation/qt/phase3_harness.py`. After signing succeeds and the signed crop is rendered, build the same appearance snapshot shape for the signed output. The harness should no longer be forced to derive “text bounds” by treating every dark pixel as possible text. Instead, it should compute comparison layers in this order: border layer, text layer, stamp layer, then full composite. Raster detection may remain as a fallback confirmation tool, but it must not remain the primary source of truth where explicit metadata is available.

After both sides emit the same snapshot shape, add a dedicated comparison function in the harness or a small analysis module. That function should produce a structured result, not just booleans. It should compare border geometry, text geometry, stamp geometry, and normalized image dimensions separately. It should then synthesize the existing pass/fail booleans from those layer-specific facts so the current harness summary format remains usable.

Once the snapshot and comparison model exist, add a deterministic parity regression suite in `tests/unit/test_phase3_harness.py` and, if it keeps the code clearer, a new file such as `tests/unit/test_signature_appearance_parity.py`. Use tracer-bullet scenarios that reflect real failures already seen in the project: a `single_line` no-stamp case, a dense serif italic case, a `multi_line` image-stamp case, and a `wrapped_block` sparse stamp case. For each scenario, assert that the harness writes both preview and signed-output snapshots, that the layer-specific comparison identifies the right kind of mismatch when intentionally perturbed, and that the normal path passes when the surfaces align.

After the test suite is in place, update the harness JSON contract in `src/foliaseal/presentation/qt/phase3_harness.py` so the saved capture includes the new snapshot and comparison structure. Keep existing fields where practical, but add explicit nested objects for preview appearance snapshot, signed appearance snapshot, and parity layer results. This is an instrumentation slice, so richer evidence is allowed to change the capture schema as long as the result is documented and tested.

Finally, update `README.md`, `docs/ExecPlans/phase3_parallel_plan.md`, and if necessary `docs/pdf_signing_app_feasibility.md` so the repository’s current truth is explicit: appearance parity is now expected to be debuggable through saved structural snapshots and autonomous parity tests, not only through manual image inspection.

## Milestones

### Milestone 1: Shared appearance snapshot for the preview

At the end of this milestone, the canonical preview renderer will emit a complete, structured appearance snapshot that describes what was rendered. A contributor should be able to run the focused preview-renderer tests and see that the preview side now records border, text, and stamp information in a stable format.

The work belongs in `src/foliaseal/application/signing_preview_renderer.py` and any new helper module created to hold snapshot types. Update or add tests in `tests/unit/test_signing_preview_renderer.py`. Run the focused tests and confirm they pass before moving on.

### Milestone 2: Matching appearance snapshot for signed-output analysis

At the end of this milestone, the signed-output path in the harness will build the same snapshot shape from the rendered signed crop. The result will be a comparable preview snapshot and signed-output snapshot for one harness case, even if parity still fails.

The work belongs primarily in `src/foliaseal/presentation/qt/phase3_harness.py`, with tests in `tests/unit/test_phase3_harness.py`. Run the focused harness tests and verify that the saved capture payload contains both snapshots.

### Milestone 3: Layered parity comparison and autonomous tracer-bullet suite

At the end of this milestone, parity will no longer depend on one undifferentiated text detector. The harness will compare border, text, stamp, and full composite layers separately, and the autonomous parity tests will assert behavior on real scenarios.

The work belongs in `src/foliaseal/presentation/qt/phase3_harness.py` or a small new helper module for comparison logic, with tests in `tests/unit/test_phase3_harness.py` and optionally `tests/unit/test_signature_appearance_parity.py`. Run the full test suite and then the signed acceptance matrix. The matrix does not need new scenarios in this slice unless a tracer-bullet parity case must be added to prove the instrumentation works.

### Milestone 4: Evidence contract and documentation refresh

At the end of this milestone, the harness JSON, repository docs, and plan/status docs will all describe the new autonomous appearance instrumentation. A novice contributor should be able to open the harness capture JSON, see the preview and signed-output snapshots, and understand how to interpret a parity failure without reading old discussion.

This work belongs in `README.md`, `docs/ExecPlans/phase3_parallel_plan.md`, and optionally `docs/pdf_signing_app_feasibility.md` if the instrumentation expectations need a clearer statement there. Run the same validation commands again after the documentation edits to ensure nothing drifted.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/SignPDF/Scratch

While implementing Milestone 1, run:

    .venv/bin/pytest -q tests/unit/test_signing_preview_renderer.py

Expected result after Milestone 1:

    <N> passed

with new or updated tests that assert the preview snapshot contains explicit border/text/stamp fields.

While implementing Milestone 2 and Milestone 3, run:

    .venv/bin/pytest -q tests/unit/test_phase3_harness.py

Expected result after Milestone 3:

    <N> passed

with new or updated tests that assert both preview and signed-output snapshots are present and that the comparison result names the failing layer when one is intentionally perturbed.

After the focused tests are green, run the full suite:

    .venv/bin/pytest -q

Expected result:

    <current total> passed

with the total updated to include the new instrumentation tests.

Then rerun the signed acceptance matrix from the repository root:

    .venv/bin/python -m foliaseal phase3-signing-acceptance-matrix \
      --pdf-path artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf \
      --certificate-path artifacts/generated_acceptance_assets/signed_acceptance_identity.p12 \
      --passphrase secret \
      --scenario-manifest-path artifacts/preview_sweep_assets/signed_acceptance_matrix.json \
      --artifacts-dir artifacts/signed_acceptance_matrix_run_autonomous_parity

Expected result:

    Phase 3 signed acceptance matrix
    - scenarios executed: <N>
    - successful signings: <M>
    - acceptance expectations passed: true

If the signed acceptance matrix writes richer parity output, that is expected in this slice.

## Validation and Acceptance

This plan is complete when a contributor can run the focused tests and the signed acceptance matrix and observe all of the following.

The canonical preview path emits a structured appearance snapshot that includes border, text, and stamp metadata without relying on a later raster detector to rediscover them.

The signed-output analysis path emits the same snapshot shape for the normalized signed crop.

The harness comparison result distinguishes at least these failure classes: border mismatch, text geometry mismatch, stamp geometry mismatch, and composite image mismatch.

At least one autonomous tracer-bullet parity test proves the loop end to end by asserting that preview and signed-output parity pass for a real scenario and fail with a clear layer-specific report when a known mismatch is injected.

The signed acceptance matrix remains green after the instrumentation upgrade.

The harness capture JSON now contains enough information that a contributor can identify what visually drifted without opening the images first.

## Idempotence and Recovery

This work is additive. Re-running the focused tests, the full test suite, or the signed acceptance matrix is safe. Re-running the matrix into the same artifact directory may overwrite the current JSON and image artifacts; that is acceptable for this slice because the goal is to keep the latest instrumentation truth, not to preserve every intermediate run.

If a partially implemented comparison model produces failing tests, keep the snapshot schema stable where possible and advance one layer at a time. The safest recovery path is to finish the current milestone’s focused tests before refreshing matrix evidence. Avoid refreshing matrix artifacts while the snapshot schema is in flux unless the refresh itself is the subject of the change.

## Artifacts and Notes

The most important artifacts produced by this plan are:

- the new ExecPlan itself at `.agent/autonomous_preview_pdf_parity_instrumentation_execplan.md`
- richer harness capture JSON with preview and signed-output appearance snapshots
- any new parity-specific unit tests
- an updated signed acceptance matrix run showing the richer parity data

The change slice for this plan is intentionally narrow. The primary change class is instrumentation. Evidence refresh is allowed when needed to prove the new instrumentation. Documentation/status updates are allowed only to explain the new instrumentation and how to use it. Do not mix in unrelated behavior changes such as font substitutions, fit-policy changes, stamp-position tweaks, TSA work, certification work, or packaging changes.

## Interfaces and Dependencies

Use the existing canonical rendering stack. Do not add a new rendering engine. The preview side must continue to go through `src/foliaseal/application/signing_preview_renderer.py`, and the signed PDF must continue to use `src/foliaseal/application/phase3_signing_backend.py`.

Define one stable snapshot type. The exact module path may be `src/foliaseal/application/signing_preview_renderer.py` or a new helper file such as `src/foliaseal/application/signature_appearance_snapshot.py`, but the end state must expose a clear Python data type for appearance snapshots. The type should include, at minimum:

    image_path: str | None
    image_size_px: dict[str, int] | None
    container_bounds_px: dict[str, int] | None
    border_bounds_px: dict[str, int] | None
    border_style: dict[str, object] | None
    text_bounds_px: dict[str, int] | None
    stamp_bounds_px: dict[str, int] | None
    text_fragments: tuple[str, ...]
    line_bounds_px: tuple[dict[str, int], ...] | tuple()

Define one stable comparison result type in the harness or a nearby helper module. It should include layer-specific booleans and mismatch reasons, rather than only one final pass/fail boolean.

Prefer existing dependencies only. The repository already uses PySide6, Pillow, and pyHanko. The point of this slice is to promote existing layout knowledge into explicit instrumentation, not to introduce another image-analysis library.

Revision note: created on 2026-04-19 in response to the need for fully autonomous signature preview versus signed-PDF appearance debugging. This plan consolidates current parity, harness, and rendering work into one instrumentation-first execution path.

Revision note (2026-04-19, implementation update): the first slice is complete. Shared appearance snapshots now exist on both preview and signed-output paths, harness parity is layer-based, the new focused tests pass, the full suite passes, and the signed acceptance matrix rerun completed successfully with the richer snapshot schema.
