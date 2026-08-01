# Extract the signature text measurement boundary

This ExecPlan is a living document. Maintain it in accordance with `.agents/skills/write-execplan/PLANS.md`. The entire change is one compatibility-preserving architecture slice: introduce the atomic text-box measurement port and PyHanko adapter, route planner/backend callers through it, preserve compatibility helpers, validate exact typography behavior, update documentation, complete compliance review, and commit the result together.

## Purpose / Big Picture

After this slice, visible-signature layout code will measure text through an explicit application-owned boundary instead of importing private helpers from the concrete PyHanko signing backend. The production signing path and preview path will share one measurement implementation, while tests can inject deterministic metrics without loading PyHanko.

Users will see no intentional visual change: half-point font sizes, bundled bold/italic faces, color conversion, integer dimensions, multiline descender correction, fit errors, and existing signing/preview parity remain unchanged. The improvement is observable through boundary tests that prove exact measurements and through an import audit showing that `visible_signature_layout.py` no longer reaches into backend-private measurement functions.

## Child ExecPlan Dependencies

- [x] The visible-signature planner/IR hybrid is complete on `main` (`ddf250473` plus its plan metadata commit `c368e7293`).
- [x] Fresh explorer-light reconnaissance confirmed the current measurement seam, direct backend bypass, font assets, and compatibility tests.
- [x] No child plan is required initially; any compliance discrepancy must be corrected within this parent slice or captured in a child plan before completion.

## Progress

- [x] (2026-08-01) Re-checked the clean checkout and confirmed the planner/IR hybrid is the current baseline.
- [x] (2026-08-01) Completed fresh reconnaissance of `PyHankoTextMeasurer`, backend measurement helpers, font registry, planner bypasses, and tests.
- [x] (2026-08-01) Selected the atomic `prepare()` measurement boundary with a metrics-only compatibility port; richer multi-provider measurement IR is explicitly deferred.
- [x] (2026-08-01) Wrote this self-contained one-slice ExecPlan before implementation.
- [x] (2026-08-01) Added the neutral `SignatureTextBoxEngine` port and atomic `PreparedTextBox` result.
- [x] (2026-08-01) Moved production measurement access behind `PyHankoSignatureTextBoxEngine`; layout no longer imports backend-private measurement helpers.
- [x] (2026-08-01) Routed backend compact-reservation measurement through the engine while retaining private compatibility helpers.
- [x] (2026-08-01) Added boundary tests for exact typography, multiline correction, injected fakes, public engine behavior, and import ownership.
- [x] (2026-08-01) Updated README and architecture documentation with `PreparedTextBox`/`SignatureTextBoxEngine` ownership, PyHanko adapter scope, compatibility wrappers, lazy-import cycle risk, injected compact-reservation seam, and deferred multi-provider registry.
- [x] (2026-08-01) Completed focused validation, Ruff, full-suite validation, preview/signed release-fidelity matrices, and the source import audit; all required counters passed.
- [x] (2026-08-01) Completed architecture/SPEC review, fixed trailing-newline line-count drift, added compact-engine injection coverage, and reconciled the docs.
- [x] (2026-08-01) Committed the implementation as `909fddd8c` and recorded final plan metadata in the follow-up commit.

## Surprises & Discoveries

- Observation: the existing `TextMeasurer` already provides a useful metrics-only port, but the default `PyHankoTextMeasurer` lazily imports `_build_text_box_style()` and `_measure_text_box_dimensions()` from the backend.
  Evidence: `src/foliaseal/application/visible_signature_layout.py:586-601`.
- Observation: backend reservation checking rebuilds the same style and dimensions independently of the planner’s default measurer.
  Evidence: `_single_line_text_fits_reservation()` in `phase3_signing_backend.py` calls both private helpers directly.
- Observation: font resolution is already centralized and stable in `signature_font_registry.py`; moving font policy into the new measurement boundary would duplicate that source of truth.
  Resolution: the production adapter calls the existing font registry and preserves its exact bundled filenames and missing-asset errors.
- Observation: existing tests directly import private backend helpers.
  Resolution: keep those names as compatibility wrappers in this slice; replace their tests with boundary tests only in a later retirement slice.
- Observation: the neutral layout module must not import the concrete backend at module load time.
  Resolution: `PyHankoTextMeasurer` lazily constructs `PyHankoSignatureTextBoxEngine`; this keeps the
  runtime dependency one-way while documenting the deliberate localized import-cycle risk.
- Observation: compact-reservation measurement is a second caller of text-box preparation.
  Resolution: `_single_line_text_fits_reservation()` consumes one injected/default engine result so
  reservation metrics and the eventual style token cannot drift.
- Observation: the first implementation counted trailing-newline text with `splitlines()` while
  multiline height used newline-count semantics.
  Resolution: `PreparedTextBox.metrics.line_count` now uses `max(1, text.count("\\n") + 1)` so
  line count and height share one canonical contract.
- Observation: architecture review found the legacy helper names still owned their implementation.
  Resolution: the concrete engine now owns the implementation functions and the underscored names
  are explicit delegating compatibility wrappers.

## Decision Log

- Decision: Introduce `SignatureTextBoxEngine.prepare()` returning metrics plus an opaque adapter-owned style handle.
  Rationale: one atomic operation prevents the measured dimensions and eventual PyHanko style from drifting apart, while keeping the public application result free of concrete PyHanko types.
  Date/Author: 2026-08-01 / Codex.
- Decision: Preserve `TextMeasurer.measure()` and `PyHankoTextMeasurer` as compatibility interfaces.
  Rationale: layout services, structural-line tests, and existing fakes already depend on the metrics-only port; an additive adapter avoids broad test churn.
  Date/Author: 2026-08-01 / Codex.
- Decision: Keep the concrete PyHanko adapter in the application/backend adapter module for this slice rather than introducing a provider registry or moving all style materialization.
  Rationale: there is one production text provider today; a capability-aware multi-renderer registry would be a separate architecture slice.
  Date/Author: 2026-08-01 / Codex.
- Decision: Preserve `_build_text_box_style()` and `_measure_text_box_dimensions()` as delegating compatibility helpers and retain their exact error/rounding behavior.
  Rationale: direct legacy tests and backend callers still import them; deleting them would mix wrapper retirement with the measurement extraction.
  Date/Author: 2026-08-01 / Codex.
- Decision: Keep horizontal rendered-ink measurement separate from structural text measurement.
  Rationale: ink measurement depends on a rendered preview and geometry context, while this boundary only owns text-box metrics and style construction.
  Date/Author: 2026-08-01 / Codex.

## Outcomes & Retrospective

Implementation and validation are complete for the code slice. Focused boundary/backend/preview
tests pass (222 focused tests after the compliance fixes), Ruff and `git diff --check` pass, and the
full suite passes (1,028 tests, one existing Pillow deprecation warning). The preview matrix ran
eight scenarios with zero error rows. The signed matrix ran eight scenarios with six successful
signings, two matched intentional rejections, zero outcome mismatches, zero cryptographic failures,
zero preview-comparison failures, and zero annotation-rectangle mismatches. Architecture/SPEC review
found missing documentation, an injectable compact-reservation seam, helper-ownership drift, and a
trailing-newline metric inconsistency; all were fixed in this slice. Residual debt is limited to the
retained private compatibility wrappers, the localized lazy-import cycle risk, and the intentionally
deferred multi-provider registry. The process/window audit was clean: no FoliaSeal/Phase 3 Python
processes and no `wmctrl` windows remained. Implementation commit: `909fddd8c`; final plan metadata
commit: `a1dc0ad3f`.

## Context and Orientation

`src/foliaseal/application/visible_signature_layout.py` owns neutral signature geometry. Its `TextMetrics` value records width, height, and line count in PDF points. `TextMeasurer` is the injected metrics port used by `VisibleSignatureLayoutEngine`, `VisibleSignatureLayoutService`, and structural line-bound calculations.

`src/foliaseal/application/phase3_signing_backend.py` owns concrete PyHanko signing and currently contains `_build_text_box_style()` plus `_measure_text_box_dimensions()`. Those functions normalize half-point sizes, resolve bundled fonts, construct PyHanko `TextBoxStyle` objects, render a temporary `TextBox`, round dimensions, and add one point of height for multiline descenders. The same module also performs a direct style/measurement pass for compact single-line reservation checks.

`src/foliaseal/application/signature_font_registry.py` is the canonical resolver for bundled Noto Sans, Noto Serif, and DejaVu Sans Mono assets. It must remain the source of family/style mapping and missing-font `ValueError` messages.

PyHanko is a true external dependency. The neutral measurement port must expose only application data (`SignatureTextStyle`, `TextMetrics`, and an opaque result token); PyHanko `TextBoxStyle`, writers, and font factories remain inside the production adapter. Tests use deterministic fake engines or metrics ports and do not require PyHanko internals for geometry behavior.

## Plan of Work

Create `src/foliaseal/application/signature_text_measurement.py` with an application-owned `PreparedTextBox` frozen value and `SignatureTextBoxEngine` protocol. `PreparedTextBox.metrics` is the existing neutral `TextMetrics`; `PreparedTextBox.render_style` is an opaque adapter token typed as `object` at the application boundary. The protocol exposes one `prepare(text, text_style)` method. Keep this module independent of `visible_signature_layout.py` at runtime so imports cannot cycle.

Add `PyHankoSignatureTextBoxEngine` in `phase3_signing_backend.py` as the production implementation. It must call the existing style/dimension logic without changing it: preserve `Fraction` half-point rounding, bundled font resolution, `_hex_to_rgb`, integer rounding, line count, and multiline `ceil(line_count * font_size) + 1` minimum height. Keep `_build_text_box_style()` and `_measure_text_box_dimensions()` as compatibility functions backed by the same implementation, so direct legacy tests continue to pass.

Change `PyHankoTextMeasurer` in `visible_signature_layout.py` to hold an optional `SignatureTextBoxEngine` and delegate `measure()` to `engine.prepare(...).metrics`. Its default path may lazily construct `PyHankoSignatureTextBoxEngine`, but it must not import or call backend-private helper names. Preserve the existing zero-argument construction and `TextMeasurer` protocol so all current services and fakes remain valid.

Change backend compact-reservation measurement to use one `PyHankoSignatureTextBoxEngine.prepare()` result for both metrics and, where applicable, the style token. Route planner/backend construction through the existing `VisibleSignaturePlanner` service injection rather than adding another direct `VisibleSignatureLayoutBoundary` or private measurement path. Do not change horizontal rendered-ink measurement, image probing, geometry policy, signing metadata, or the public `SigningRequest`/`SigningResult` contracts.

Add boundary tests in `tests/unit/test_visible_signature_layout_boundary.py` or a focused neighboring test module. Cover exact 8.5-point sizing, bundled bold/italic face selection, color/style construction through the production adapter contract, multiline minimum height and line count, missing-font error preservation, deterministic fake-engine injection, and a source/import assertion that `visible_signature_layout.py` no longer imports `_build_text_box_style` or `_measure_text_box_dimensions` from the backend. Add one backend test proving the compact reservation path consumes the engine while retaining existing fit behavior. Retain the existing private-helper tests as compatibility coverage for this slice.

Update `README.md`, `docs/ARCHITECTURE.md`, and this ExecPlan. Document the neutral measurement port, the PyHanko adapter ownership, the compatibility wrappers, and the explicit decision not to add a multi-provider capability registry yet. Record any discovered import-cycle or typography discrepancy in `Surprises & Discoveries`, update `Progress` at each milestone, and complete the required compliance review before committing.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

Baseline:

    git status --short --branch
    .venv/bin/pytest -q tests/unit/test_visible_signature_layout_boundary.py tests/unit/test_visible_signature_layout.py tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py

After the first implementation cycle:

    .venv/bin/ruff check src/foliaseal/application/signature_text_measurement.py src/foliaseal/application/visible_signature_layout.py src/foliaseal/application/phase3_signing_backend.py tests/unit/test_visible_signature_layout_boundary.py tests/unit/test_phase3_signing_backend.py
    .venv/bin/pytest -q tests/unit/test_visible_signature_layout_boundary.py tests/unit/test_visible_signature_layout.py tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py

Final validation:

    .venv/bin/pytest -q
    git diff --check

Re-run the existing Phase 3 preview and signed-acceptance matrix commands using the tracked release manifest and `/tmp` artifact directories. Expect eight preview scenarios with zero error rows, six successful signed scenarios, two matched intentional fit rejections, and zero critical comparison, cryptographic, and annotation counters.

Finish with:

    git status --short
    ps -eo pid=,comm=,args= | awk '$2 ~ /python/ && $0 ~ /foliaseal|phase3/ {print}'
    wmctrl -l 2>/dev/null || true

## Validation and Acceptance

The slice is accepted when `visible_signature_layout.py` depends only on the public measurement port and no longer reaches into backend-private measurement functions. The production PyHanko adapter produces the same widths, heights, line counts, font faces, colors, and multiline correction as before. A fake engine can drive layout tests without PyHanko, and backend compact-reservation checks use the same production engine contract.

All existing visible-signature, signing, invisible-signing, incremental-signing, TSA, Qt, CLI, and harness tests must remain green. Focused typography/measurement tests, Ruff, the full suite, release-fidelity matrices, import audit, diff check, and process/window audit are required evidence. No generated PDFs, images, or logs may be committed.

## Idempotence and Recovery

The change is additive and safe to rerun. Keep matrix artifacts under `/tmp`. If an import cycle appears, keep `signature_text_measurement.py` runtime-independent from `visible_signature_layout.py` and use lazy construction for the PyHanko adapter. If a typography assertion changes, compare the old compatibility helper output and the new engine output before changing rounding or font policy. Do not delete private helpers until a separate retirement plan replaces their direct tests. Never use destructive Git commands.

## Artifacts and Notes

Tracked artifacts are the new measurement boundary, adapter/backend/layout/test changes, README, architecture documentation, and this ExecPlan. Generated matrix artifacts remain outside Git. Record focused/full test transcripts, import-audit evidence, compliance findings, residual debt, and both commit hashes here.

## Interfaces and Dependencies

Create `src/foliaseal/application/signature_text_measurement.py` with:

    @dataclass(frozen=True)
    class PreparedTextBox:
        metrics: TextMetrics
        render_style: object

    class SignatureTextBoxEngine(Protocol):
        def prepare(
            self,
            text: str,
            text_style: SignatureTextStyle,
        ) -> PreparedTextBox: ...

`TextMetrics` remains the existing neutral value in `visible_signature_layout.py`. `PyHankoSignatureTextBoxEngine` implements the protocol in the backend adapter and returns a `PreparedTextBox` containing the exact neutral metrics plus its internal PyHanko style token. `PyHankoTextMeasurer` remains a metrics-only compatibility adapter and accepts an optional engine for deterministic tests. Existing `VisibleSignaturePlanner` and `VisibleSignatureLayoutService` constructors remain compatible; production defaults create the real adapter lazily, while tests inject fakes.

## Revision Note

2026-08-01 / Codex: Created after fresh post-hybrid reconnaissance selected the atomic text-box measurement boundary plus common-caller planner wiring. The slice intentionally excludes a capability-aware multi-renderer registry, horizontal rendered-ink redesign, and compatibility-wrapper retirement.
