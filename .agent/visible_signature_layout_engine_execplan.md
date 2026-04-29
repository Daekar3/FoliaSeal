# Visible Signature Layout Engine Boundary

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agent/PLANS.md`. It records the plan for implementing GitHub issue #48, "RFC: Deepen visible signature layout engine boundary."

## Purpose / Big Picture

After this work, FoliaSeal will have one application-layer boundary for visible-signature layout planning. A visible signature is the rectangular appearance shown on a signed PDF page. Today the rules for dividing that rectangle between text and an optional stamp image are spread across backend signing, canonical preview rendering, horizontal ink measurement, and Qt preview sizing. This makes preview/output parity hard to reason about because several callers import private helper functions and repeat the same sequence of layout decisions.

The first executable slice is intentionally behavior-preserving. It introduces `foliaseal.application.visible_signature_layout` and boundary tests around it, but it does not yet migrate backend signing or Qt preview callers. A developer can see the new boundary working by running the new tests and observing that the new `VisibleSignatureLayoutEngine.plan()` returns the same reservation and fit behavior as the existing helper path.

## Progress

- [x] (2026-04-29T22:29Z) Created this ExecPlan from issue #48 and scoped the first implementation slice to an additive layout boundary plus tests.
- [x] (2026-04-29T22:36Z) Added `src/foliaseal/application/visible_signature_layout.py` with public DTOs, protocol ports, default pyHanko/Pillow-backed probes, and a behavior-preserving `VisibleSignatureLayoutEngine`.
- [x] (2026-04-29T22:36Z) Exported the new boundary from `src/foliaseal/application/__init__.py`.
- [x] (2026-04-29T22:38Z) Added focused tests in `tests/unit/test_visible_signature_layout.py` covering structural reservations, no-stamp behavior, injected ink reservation, conservative fallback, and fit issues.
- [x] (2026-04-29T22:40Z) Ran ruff, the new boundary tests, and adjacent backend/preview/reservation tests successfully.
- [x] (2026-04-29T22:36Z) Committed the first additive boundary slice as `aaa8466dc` with message `Add visible signature layout boundary`.
- [x] (2026-04-29T22:43Z) Added pyHanko adapter equivalence tests and a `PyHankoSignatureAppearanceAdapter` that builds the same observable `RoundedBorderTextStampStyle` fields currently produced by `_build_stamp_style`.
- [x] (2026-04-29T22:47Z) Migrated backend stamp-style construction and backend fit validation to consume `VisibleSignatureLayoutEngine.plan()` through `PyHankoSignatureAppearanceAdapter` while preserving the existing rendered-fit fallback behavior.
- [x] (2026-04-29T22:51Z) Migrated canonical preview layout in `signing_preview_renderer.py` to consume `VisibleSignatureLayoutEngine.plan()` and `PyHankoSignatureAppearanceAdapter` instead of reconstructing reservation and ink alignment separately.
- [ ] Next slice: migrate Qt preview sizing in `signing_shell.py` to consume a Qt geometry adapter derived from `SignatureLayoutPlan`.
- [ ] Final cleanup slice: delete or demote private-helper tests once boundary and adapter tests cover their behavior.

## Surprises & Discoveries

- Observation: `phase3_signing_backend.py` already contains almost all policy needed for the first boundary slice, including `_layout_reservation_for_template`, `_apply_horizontal_single_line_ink_text_alignment`, `_horizontal_single_line_background_text_width`, `_ensure_layout_can_fit`, `_build_text_box_style`, and `_measure_text_box_dimensions`.
  Evidence: reading `src/foliaseal/application/phase3_signing_backend.py` showed the reservation dataclass and helper ladder between the visible-signature text layout helpers and the stamp background helpers.

- Observation: the current tree already has unrelated generated artifact changes.
  Evidence: `git status --short` before this plan showed modified `artifacts/phase3_fr3b_acceptance_results.md` and `artifacts/phase3_harness_capture.json`. This plan must not revert or overwrite those files.

- Observation: the first boundary tests initially had incorrect expectations for the current margin policy rather than exposing implementation bugs.
  Evidence: the first `pytest -q tests/unit/test_visible_signature_layout.py` run failed because existing helper behavior produced `32` points of horizontal usable height, `254` points of no-stamp text width, and an `88` point ink lane. The tests were corrected to match current behavior, and the final run passed with `5 passed`.

- Observation: adapter equivalence can be tested by comparing stable style fields instead of direct pyHanko object identity.
  Evidence: `tests/unit/test_visible_signature_layout.py` now snapshots border settings, background and text layout margins/alignment/scaling, font size, text color, stamp text, and timestamp format. The focused suite passed with `178 passed`.

- Observation: the controlled horizontal rendered-ink path requires patching the backend module's imported `measure_horizontal_single_line_rendered_reference` symbol, not only providing the new engine with a fake ink measurer.
  Evidence: `_build_stamp_style()` calls `_horizontal_single_line_ink_reservation_for_stamp_text()`, which uses the symbol imported into `phase3_signing_backend.py`; the new equivalence test patches that symbol and gives `VisibleSignatureLayoutEngine` an equivalent fake `HorizontalInkMeasurer`.

- Observation: backend migration must preserve the existing rendered-fit fallback after layout planning.
  Evidence: the old `_build_stamp_style()` allowed some nominal `_ensure_layout_can_fit()` failures when `_single_line_rendered_ink_fits_reservation()` or `_horizontal_multi_line_rendered_layout_fits_reservation()` passed. The migrated `_build_stamp_style()` now checks `layout_plan.fit_issues` and applies the same fallback functions before asking the adapter to build the final style.

- Observation: canonical preview still needs `RoundedBorderTextStampStyle` directly for optional text-only and stamp-only bounds rendering.
  Evidence: the first test run after moving `_canonical_preview_layout()` onto the layout engine failed with `NameError: name 'RoundedBorderTextStampStyle' is not defined` in `_render_optional_preview_bounds()`. Restoring that import fixed the preview and backend fallback failures.

## Decision Log

- Decision: implement the first slice as an additive wrapper boundary instead of immediately moving existing helpers.
  Rationale: backend signing, canonical preview rendering, and Qt preview sizing are sensitive parity paths. Wrapping the existing behavior first creates a tested seam without changing production behavior.
  Date/Author: 2026-04-29 / Codex

- Decision: keep production callers on the existing paths during this slice.
  Rationale: the issue describes a multi-step migration. The first independently verifiable milestone is a new boundary with tests. Updating callers belongs in later slices after the plan object has enough test coverage.
  Date/Author: 2026-04-29 / Codex

- Decision: allow the first `SignatureLayoutPlan` to carry the existing pyHanko layout objects as adapter payloads while also exposing plain dimensions and margins.
  Rationale: the existing helper path already computes pyHanko `SimpleBoxLayoutRule` objects. Carrying them avoids behavior drift in the first slice. Later slices can introduce neutral `LayoutRuleSpec` adapters after equivalence tests are in place.
  Date/Author: 2026-04-29 / Codex

- Decision: make the next Issue #48 slice adapter-equivalence work before migrating production callers.
  Rationale: the highest-risk part of the migration is preserving exact pyHanko stamp style behavior. Equivalence tests around a dedicated adapter create a safety net before backend signing or preview rendering is changed.
  Date/Author: 2026-04-29 / Codex

- Decision: compare adapter output through stable snapshots rather than object identity.
  Rationale: pyHanko style objects contain nested library objects whose identity is not meaningful for this migration. The migration risk is whether the effective margins, alignment, scaling, border, text, and timestamp fields match.
  Date/Author: 2026-04-29 / Codex

- Decision: keep `PyHankoSignatureAppearanceAdapter` in `visible_signature_layout.py` for this slice.
  Rationale: the adapter is small and still tightly coupled to the layout plan. Splitting it now would add navigation overhead before production callers have migrated.
  Date/Author: 2026-04-29 / Codex

- Decision: keep the rendered-fit fallback in `phase3_signing_backend.py` during backend migration.
  Rationale: the fallback depends on backend-only raster checks and cache behavior that are not part of the pure layout plan yet. Keeping it at the backend layer preserves current signing behavior while still moving structural layout planning and style construction onto the new boundary.
  Date/Author: 2026-04-29 / Codex

- Decision: keep preview-only stamp suppression in `signing_preview_renderer.py`.
  Rationale: the preview has an existing rule that suppresses a horizontal single-line stamp when the text lane collapses. That behavior is presentation-specific and should not be moved into backend signing during this slice.
  Date/Author: 2026-04-29 / Codex

## Outcomes & Retrospective

The first implementation slice succeeded.

What changed:

- Added `src/foliaseal/application/visible_signature_layout.py` as the new layout-planning boundary.
- Added plain data objects for text metrics, stamp image metrics, rectangle bounds, layout margins, layout rule specs, layout requests, layout plans, horizontal ink measurement, horizontal ink reservation, and fit issues.
- Added ports for text measurement, stamp image probing, and horizontal rendered-ink measurement.
- Added default production helpers `PyHankoTextMeasurer` and `PillowStampImageProbe`.
- Implemented `VisibleSignatureLayoutEngine.plan()` as a behavior-preserving wrapper over the current backend helper ladder.
- Exported the new boundary through `src/foliaseal/application/__init__.py`.
- Added `tests/unit/test_visible_signature_layout.py` with deterministic fake ports so the boundary can be tested without Qt, PDF rendering, temporary files, or image fixtures.

What did not change:

- Backend signing still uses the old helper path.
- Canonical preview rendering still uses the old helper path.
- Qt preview sizing still uses the old helper path.
- Generated harness artifacts under `artifacts/` were left untouched.

Verification results:

    .venv/bin/ruff check --fix src/foliaseal/application/visible_signature_layout.py src/foliaseal/application/__init__.py tests/unit/test_visible_signature_layout.py
    Found 1 error (1 fixed, 0 remaining).

    .venv/bin/ruff check src/foliaseal/application/visible_signature_layout.py src/foliaseal/application/__init__.py tests/unit/test_visible_signature_layout.py
    All checks passed!

    .venv/bin/pytest -q tests/unit/test_visible_signature_layout.py
    5 passed in 0.23s

    .venv/bin/pytest -q tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py tests/unit/test_horizontal_signature_reservation.py
    173 passed in 25.70s

Retrospective:

This is the right first slice because it gives the codebase a public seam without risking preview/output parity. The plan still carries the current backend reservation object as an opaque payload to reduce migration risk. The next slice should add adapter equivalence tests for pyHanko style construction before moving any production caller to the new plan.

Commit:

    aaa8466dc Add visible signature layout boundary

The adapter-equivalence slice also succeeded.

What changed:

- Added `PyHankoSignatureAppearanceAdapter` to build pyHanko `RoundedBorderTextStampStyle` objects from `SignatureLayoutPlan`.
- Exported `PyHankoSignatureAppearanceAdapter` through `src/foliaseal/application/__init__.py`.
- Extended `tests/unit/test_visible_signature_layout.py` with representative adapter-equivalence tests covering single-line, multi-line, wrapped-block, top/bottom/left/right stamp positions, image-stamp and no-image cases, bordered and borderless boxes, and a controlled horizontal rendered-ink reservation.

What did not change:

- Production backend signing still calls `_build_stamp_style()` directly.
- Canonical preview rendering still calls its existing private-helper path.
- Qt preview sizing is still unmigrated.

Verification results:

    .venv/bin/ruff check src/foliaseal/application/visible_signature_layout.py src/foliaseal/application/__init__.py tests/unit/test_visible_signature_layout.py tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py
    All checks passed!

    .venv/bin/pytest -q tests/unit/test_visible_signature_layout.py
    11 passed in 0.29s

    .venv/bin/pytest -q tests/unit/test_visible_signature_layout.py tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py
    178 passed in 25.33s

The next slice should migrate backend signing and backend fit validation to consume `VisibleSignatureLayoutEngine.plan()` through `PyHankoSignatureAppearanceAdapter`. Keep that slice limited to `phase3_signing_backend.py`, the layout module if adapter gaps appear, and the backend-focused tests.

The backend migration slice succeeded.

What changed:

- `_build_stamp_style()` in `src/foliaseal/application/phase3_signing_backend.py` now creates a `LayoutRequest`, plans it through `VisibleSignatureLayoutEngine`, preserves the existing rendered fallback checks when the plan reports fit issues, and delegates final pyHanko style construction to `PyHankoSignatureAppearanceAdapter`.
- Added `_BackendHorizontalInkMeasurer` in `phase3_signing_backend.py` as the bridge from backend signing inputs to the layout engine's `HorizontalInkMeasurer` port.
- Added a small `_rect_bounds_from_mapping()` helper to convert existing rendered-reference dictionaries into `RectBounds` for the layout boundary.
- Updated `PyHankoSignatureAppearanceAdapter.build_stamp_style()` so backend callers can explicitly allow pre-approved fit issues after preserving the existing fallback checks.

What did not change:

- Canonical preview rendering still reconstructs its own plan in `signing_preview_renderer.py`.
- Qt preview sizing still calls private reservation helpers.
- Private backend helper tests remain in place until the preview and Qt migrations are complete.

Verification results:

    .venv/bin/ruff check src/foliaseal/application/phase3_signing_backend.py src/foliaseal/application/visible_signature_layout.py tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py tests/unit/test_sign_pdf_use_case.py tests/unit/test_horizontal_signature_reservation.py
    All checks passed!

    .venv/bin/pytest -q tests/unit/test_sign_pdf_use_case.py tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py tests/unit/test_horizontal_signature_reservation.py tests/unit/test_visible_signature_layout.py
    205 passed in 25.49s

The next slice should migrate canonical preview layout in `src/foliaseal/application/signing_preview_renderer.py` to consume `SignatureLayoutPlan`. Preserve current preview/output parity tests and keep Qt preview sizing for a later slice.

The canonical-preview migration slice succeeded.

What changed:

- `_canonical_preview_layout()` now builds a `LayoutRequest`, plans it through `VisibleSignatureLayoutEngine`, and uses `PyHankoSignatureAppearanceAdapter` to build the canonical preview stamp style.
- Added `_PreviewHorizontalInkMeasurer` in `signing_preview_renderer.py` to bridge canonical preview inputs into the layout engine's `HorizontalInkMeasurer` port.
- Preserved the preview-only horizontal single-line stamp-suppression rule by replanning without an image stamp when the text lane collapses.
- Kept `_render_optional_preview_bounds()` on `RoundedBorderTextStampStyle` for text-only and stamp-only diagnostics.

What did not change:

- Qt preview sizing in `signing_shell.py` still uses its existing reservation helper path.
- Preview text measurement helpers are still imported for structural line-bound diagnostics elsewhere in `signing_preview_renderer.py`.

Verification results:

    .venv/bin/ruff check src/foliaseal/application/signing_preview_renderer.py src/foliaseal/application/visible_signature_layout.py tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_signing_backend.py tests/unit/test_visible_signature_layout.py
    All checks passed!

    .venv/bin/pytest -q tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_signing_backend.py tests/unit/test_visible_signature_layout.py
    178 passed in 25.36s

The next slice should migrate Qt preview sizing in `src/foliaseal/presentation/qt/signing_shell.py` to consume a small Qt geometry adapter derived from `SignatureLayoutPlan`. Keep that slice focused on Qt preview sizing and run the Qt shell, harness, and preview tests named in the validation section.

## Context and Orientation

This repository is a Python package under `src/foliaseal`. The visible-signature layout code currently lives mainly in `src/foliaseal/application/phase3_signing_backend.py`. That module signs PDFs through pyHanko, a PDF signing library, and also contains private helper functions that measure text, decide how much room the text and stamp image should receive, and validate whether a selected rectangle can contain the requested visible signature.

The canonical preview path lives in `src/foliaseal/application/signing_preview_renderer.py`. It renders a preview of the visible signature and currently imports backend-private helpers so preview geometry matches final signing geometry. The Qt shell path lives in `src/foliaseal/presentation/qt/signing_shell.py`. It has preview sizing helpers that call the same backend-private reservation helpers.

The new module `src/foliaseal/application/visible_signature_layout.py` will define the public application boundary. A "boundary" here means the small set of public types and methods callers should use instead of private helper functions. A "plan" means the typed result of applying layout policy to a request. A "port" means a small protocol that hides a dependency such as text measurement, stamp image inspection, or rendered ink measurement. Ports let tests provide deterministic stand-ins.

The first slice does not delete or move existing helpers. Instead, `VisibleSignatureLayoutEngine` delegates to the current helper path so the new tests describe existing behavior. Later slices can move policy into the new module, then update backend signing, canonical preview rendering, Qt preview sizing, and harness diagnostics to consume the plan.

At the time of this revision, the first slice is committed. The remaining Issue #48 work should be done in narrow follow-up slices. The next slice should focus on a pyHanko adapter. In this repository, "pyHanko adapter" means a small object that takes the new `SignatureLayoutPlan` and existing appearance inputs, then returns the pyHanko `RoundedBorderTextStampStyle` used by signing and canonical preview. That adapter should be tested against the current `_build_stamp_style` result before any production caller is migrated.

## Plan of Work

Create `src/foliaseal/application/visible_signature_layout.py`. Define dataclasses for `TextMetrics`, `ImageMetrics`, `RectBounds`, `HorizontalInkMeasurement`, `HorizontalInkReservation`, `LayoutMargins`, `LayoutRuleSpec`, `VisibleSignatureFitIssue`, `LayoutRequest`, and `SignatureLayoutPlan`. Define protocol ports named `TextMeasurer`, `StampImageProbe`, and `HorizontalInkMeasurer`.

The first implementation of `VisibleSignatureLayoutEngine.plan()` should:

1. measure text through the supplied `TextMeasurer`, defaulting to the current pyHanko text measurement helpers;
2. inspect stamp image presence and aspect ratio through the supplied `StampImageProbe`, defaulting to a simple local image probe;
3. call the existing reservation helper to build the structural reservation;
4. optionally build a horizontal single-line ink reservation from an injected `HorizontalInkMeasurer`;
5. recompute and align the reservation when the ink reservation applies;
6. compute `background_text_box_width_pt` using the same existing policy;
7. call the existing fit guard and return typed fit issues instead of throwing;
8. expose plain dimensions and layout-rule margin specs for tests and future adapters.

Update `src/foliaseal/application/__init__.py` to export the new boundary types that downstream application code should use.

Add `tests/unit/test_visible_signature_layout.py`. These tests should use fake ports for text metrics, stamp image metadata, and ink measurement so they run without Qt, PDF rendering, or temporary files. The tests should prove the new boundary can express all core layout cases:

- a horizontal left-stamp plan reserves text and stamp areas and has no fit issues for a roomy rectangle;
- a single-line no-stamp top/bottom plan gives all usable space to text and zero space to stamp;
- an injected ink measurement can reduce the horizontal text lane and records a `HorizontalInkReservation`;
- contradictory or too-large ink measurement falls back to structural layout;
- a rectangle too small for the measured text returns a `visible_signature_layout_unavailable` fit issue.

The next required Issue #48 slice should add adapter-equivalence coverage. Add a `PyHankoSignatureAppearanceAdapter` in `src/foliaseal/application/visible_signature_layout.py` or a small adjacent module if the file becomes too large. It should accept the existing domain/application objects needed for stamp style construction and a `SignatureLayoutPlan`. It should return the same effective pyHanko `RoundedBorderTextStampStyle` currently returned by `_build_stamp_style` in `phase3_signing_backend.py`.

For that next slice, add tests that build the old stamp style and the new adapter stamp style for representative cases:

- single-line, multi-line, and wrapped-block layout templates;
- top, bottom, left, and right stamp positions;
- image-stamp and no-image-stamp cases;
- bordered and borderless boxes;
- horizontal single-line ink reservation when a deterministic fake ink measurement is injected.

The equivalence tests should compare stable observable fields rather than object identity: border width, border color, stamp text, timestamp format, text box style font size, inner-content layout margins and alignment, background layout margins and alignment, and whether a background image/solid background exists. If comparing pyHanko objects directly is brittle, create small helper functions inside the test file that extract these stable fields into dictionaries.

After adapter equivalence is green, migrate production callers one area at a time. The backend signing migration should update `_build_stamp_style` or its caller so `PyHankoPdfSigner.sign()` and `_visible_signature_fit_issues_for_stamp_text()` use `VisibleSignatureLayoutEngine.plan()` and the adapter. The canonical preview migration should update `_canonical_preview_layout()` in `signing_preview_renderer.py` to consume the same plan. The Qt migration should replace `_preview_layout_reservation()` in `signing_shell.py` with a small adapter that derives preview band geometry from `SignatureLayoutPlan`.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/SignPDF/Scratch

Create or update these files:

    .agent/visible_signature_layout_engine_execplan.md
    src/foliaseal/application/visible_signature_layout.py
    src/foliaseal/application/__init__.py
    tests/unit/test_visible_signature_layout.py

Run focused verification:

    .venv/bin/ruff check src/foliaseal/application/visible_signature_layout.py src/foliaseal/application/__init__.py tests/unit/test_visible_signature_layout.py
    .venv/bin/pytest -q tests/unit/test_visible_signature_layout.py

For the next adapter-equivalence slice, run:

    .venv/bin/ruff check src/foliaseal/application/visible_signature_layout.py tests/unit/test_visible_signature_layout.py tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py
    .venv/bin/pytest -q tests/unit/test_visible_signature_layout.py tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py

For the backend migration slice, also run:

    .venv/bin/pytest -q tests/unit/test_sign_pdf_use_case.py tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py tests/unit/test_horizontal_signature_reservation.py

For the Qt preview migration slice, also run:

    .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_harness.py tests/unit/test_signing_preview_renderer.py

If `.venv/bin/pytest` is unavailable, use:

    python -m pytest -q tests/unit/test_visible_signature_layout.py

Expected success is that ruff reports all checks passed and the new test file passes. If a test fails because the new boundary does not exactly match existing helper behavior, adjust the new module rather than changing existing production behavior in this slice.

## Validation and Acceptance

This slice is accepted when all of the following are true:

- `VisibleSignatureLayoutEngine.plan()` exists and returns a `SignatureLayoutPlan` with typed text metrics, stamp image presence, text/stamp area dimensions, layout rule specs, optional ink reservation, background text width, and fit issues.
- The new boundary tests pass and do not instantiate Qt, render PDFs, or require image files.
- Existing production callers remain behaviorally unchanged because they still use the old helper path.
- The ExecPlan records the commands run and outcomes observed.

The next adapter-equivalence slice is accepted when all of the following are true:

- `PyHankoSignatureAppearanceAdapter` or equivalent exists and builds a pyHanko stamp style from a `SignatureLayoutPlan`.
- Representative tests prove the adapter matches the stable observable fields of the existing `_build_stamp_style` path.
- No production caller has been migrated unless those equivalence tests are already green.
- The focused backend and preview suites still pass.

The backend migration slice is accepted when all of the following are true:

- backend signing and backend fit validation consume `VisibleSignatureLayoutEngine.plan()` through the adapter;
- existing signing backend tests still pass without weakening fit checks;
- no canonical preview or Qt caller migration is mixed into the same commit unless required by an import cycle.

The canonical preview and Qt migration slices are accepted when each caller consumes `SignatureLayoutPlan` instead of private backend reservation helpers, and their existing focused suites pass.

The behavior to observe is internal but demonstrable: `pytest -q tests/unit/test_visible_signature_layout.py` should pass, and the tests should show that the new plan boundary can represent current visible-signature layout behavior.

## Idempotence and Recovery

This slice is additive and safe to retry. If a later edit fails, remove only the new file `src/foliaseal/application/visible_signature_layout.py`, the new test file, and the added exports from `src/foliaseal/application/__init__.py`. Do not modify or revert unrelated artifact changes under `artifacts/`.

Avoid destructive git commands. Use `git status --short` to inspect the working tree and keep unrelated generated artifacts separate from this slice.

## Artifacts and Notes

GitHub issue #48 tracks the RFC for the larger migration. This ExecPlan implements the first milestone only.

Key existing private helpers that the first slice wraps:

    _layout_reservation_for_template
    _apply_horizontal_single_line_ink_text_alignment
    _horizontal_single_line_background_text_width
    _ensure_layout_can_fit
    _build_text_box_style
    _measure_text_box_dimensions

## Interfaces and Dependencies

In `src/foliaseal/application/visible_signature_layout.py`, define:

    class TextMeasurer(Protocol):
        def measure(self, text: str, text_style: SignatureTextStyle) -> TextMetrics: ...

    class StampImageProbe(Protocol):
        def inspect(self, image_stamp_path: str | None) -> ImageMetrics | None: ...

    class HorizontalInkMeasurer(Protocol):
        def measure(self, request: HorizontalInkMeasurementRequest) -> HorizontalInkMeasurement | None: ...

    class VisibleSignatureLayoutEngine:
        def plan(self, request: LayoutRequest) -> SignatureLayoutPlan: ...
        def validate(self, request: LayoutRequest) -> tuple[VisibleSignatureFitIssue, ...]: ...

The default text measurer may import private helpers from `phase3_signing_backend.py` during this first slice. The default image probe should use Pillow to read local image dimensions. The injected ink measurer should return measured pixel bounds; the engine should convert those bounds into `HorizontalInkReservation` through the existing `build_horizontal_single_line_ink_reservation` helper.

Revision note: Created 2026-04-29 by Codex to make issue #48 executable as an incremental, behavior-preserving migration plan.

Revision note: Updated 2026-04-29 by Codex after completing the first additive boundary slice and recording verification results.

Revision note: Updated 2026-04-29 by Codex after committing the first slice as `aaa8466dc`; added the required follow-up slices for pyHanko adapter equivalence, backend migration, canonical preview migration, Qt preview migration, and private-helper test cleanup.

Revision note: Updated 2026-04-29 by Codex after completing the pyHanko adapter-equivalence slice; recorded snapshot-based equivalence strategy, verification output, and the next backend-migration target.

Revision note: Updated 2026-04-29 by Codex after migrating backend stamp-style construction and fit validation onto the visible layout engine and pyHanko adapter; recorded fallback-preservation details and focused verification output.

Revision note: Updated 2026-04-29 by Codex after migrating canonical preview layout onto the visible layout engine and pyHanko adapter; recorded preview-only suppression behavior and focused verification output.
