# Visible Signature Layout Engine Boundary

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`. It records the plan for implementing GitHub issue #48, "RFC: Deepen visible signature layout engine boundary."

## Purpose / Big Picture

After this work, FoliaSeal will have one application-layer boundary for visible-signature layout planning. A visible signature is the rectangular appearance shown on a signed PDF page. Today the rules for dividing that rectangle between text and an optional stamp image are spread across backend signing, canonical preview rendering, horizontal ink measurement, and Qt preview sizing. This makes preview/output parity hard to reason about because several callers import private helper functions and repeat the same sequence of layout decisions.

The initial production migration is complete. `foliaseal.application.visible_signature_layout` exists, backend signing uses it for stamp style planning, canonical preview uses it for pyHanko preview layout, and Qt preview sizing derives widget geometry from `SignatureLayoutPlan`. The next slice is a cleanup and boundary-hardening slice: move obsolete private-helper test coverage to the visible layout boundary where practical, keep only tests that protect genuinely backend-specific pyHanko behavior, and document or close any remaining private-helper call sites such as harness diagnostics.

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
- [x] (2026-04-29T22:56Z) Migrated Qt preview sizing in `signing_shell.py` to consume a local Qt preview geometry adapter derived from `SignatureLayoutPlan`.
- [x] (2026-04-30T22:15Z) Reviewed Issue #48 state after the Qt migration and architecture documentation. Focused ruff passed and the focused Issue #48 pytest set passed with `332 passed, 1 warning`.
- [x] (2026-04-30T22:20Z) Completed the first private-helper coverage cleanup pass by moving representative generic reservation expectations into `tests/unit/test_visible_signature_layout.py` and deleting duplicated backend-private reservation tests.
- [x] (2026-04-30T22:26Z) Committed the first private-helper cleanup pass as `b105d9d8d` with message `Move layout reservation tests to boundary`.
- [x] (2026-04-30T22:26Z) Refined the next Issue #48 slice around residual generic reservation policy tests and a bounded harness-diagnostic assessment.
- [x] (2026-04-30T22:32Z) Executed pass two of private-helper cleanup: moved optical alignment, compact vertical clearance, border-aware inset, and horizontal edge-invariant tests to the public layout boundary and switched harness reservation diagnostics to `VisibleSignatureLayoutEngine.plan()`.
- [x] (2026-04-30T22:32Z) Committed the second private-helper cleanup pass as `df5a79bb1` with message `Move remaining layout policy tests to boundary`.
- [x] (2026-05-01T00:53Z) Fixed GitHub CI dependency coverage by adding `PySide6>=6.7` to the `dev` extra and committed it as `16fe757ff` with message `Add PySide6 to dev dependencies`.
- [x] (2026-05-01T00:53Z) Updated the next Issue #48 slice after the CI fix; remaining work is preview diagnostics and backend test ownership, not dependency setup.
- [x] (2026-05-01T01:00Z) Executed the preview diagnostics and backend test ownership slice: moved preview structural line measurement onto `PyHankoTextMeasurer` and renamed remaining generic-sounding backend reservation tests around backend fit/structural behavior.
- [x] (2026-05-01T01:00Z) Committed the preview diagnostics cleanup as `ad48a19b8` with message `Move preview diagnostics onto layout boundary`.
- [x] (2026-05-01T03:03Z) Refined the next Issue #48 slice so it starts with a layout-policy ownership decision instead of additional test relocation.
- [x] (2026-05-01T03:28Z) Accepted deferred policy extraction as the Issue #48 end state: production callers use `VisibleSignatureLayoutEngine`, while the engine may delegate to backend compatibility helpers until architecture-steward follow-up defines the final module split.
- [x] (2026-05-01T03:30Z) Closed the Issue #48 documentation loop: `docs/ARCHITECTURE.md` now records the transitional visible-signature layout boundary and GitHub issue #49 tracks post-architecture-steward layout-policy extraction.
- [x] (2026-05-01T03:35Z) Prepared the Issue #48 closure report: validation is green, remaining private-helper usage matches the documented allowed categories, and future extraction is assigned to GitHub issue #49.
- [ ] Next slice: run a new architecture-discovery pass before selecting the next refactor RFC; do not assume issue #49 is automatically the next best architecture slice.

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

- Observation: Qt preview sizing can avoid image-file reads while still planning through the visible layout engine.
  Evidence: the Qt tests pass fake `/tmp/stamp.png` paths and a loaded pixmap aspect ratio. The new `_PreviewStampImageProbe` uses the provided aspect ratio to produce `ImageMetrics`, preserving the old helper path's no-I/O behavior.

- Observation: the production backend, canonical preview, and Qt preview sizing call paths now consume `SignatureLayoutPlan`, but harness diagnostics and several backend tests still import private layout helpers directly.
  Evidence: `rg -n "_layout_reservation_for_template|_build_stamp_style|_build_text_box_style|_measure_text_box_dimensions" src tests` on 2026-04-30 showed remaining private-helper imports in `src/foliaseal/presentation/qt/phase3_harness.py`, `tests/unit/test_phase3_signing_backend.py`, `tests/unit/test_signing_preview_renderer.py`, and the layout engine's compatibility delegation.

- Observation: the layout boundary is public but not yet fully neutral.
  Evidence: `SignatureLayoutPlan` still exposes `backend_reservation`, `VisibleSignatureLayoutEngine.plan()` imports `_layout_reservation_for_template()` and related helpers from `phase3_signing_backend.py`, and `PyHankoSignatureAppearanceAdapter` still reads `layout_plan.backend_reservation.inner_content_layout`.

- Observation: the first private-helper cleanup pass removed the most duplicated generic reservation tests, but a deliberate residue remains in backend tests.
  Evidence: after the pass, `tests/unit/test_phase3_signing_backend.py` still imports `_layout_reservation_for_template()` for backend-adjacent background-layout comparisons, border-facing inset assertions, rendered-fit fallback setup, and detailed layout policy assertions that should be moved or justified in a later slice. `_build_text_box_style()`, `_measure_text_box_dimensions()`, and `_build_stamp_style()` remain covered there because they protect pyHanko font/style construction and rendered signing behavior.

- Observation: the next cleanup pass has a concrete, bounded test set to inspect before touching production code.
  Evidence: on 2026-04-30, the remaining generic reservation tests in `tests/unit/test_phase3_signing_backend.py` included `test_layout_reservation_for_single_line_bottom_without_stamp_uses_optical_text_alignment`, `test_layout_reservation_for_compact_vertical_single_line_uses_symmetric_outer_clearance`, `test_layout_reservation_for_compact_vertical_single_line_increases_outer_clearance_with_border`, `test_layout_reservation_uses_border_aware_outer_insets`, and the horizontal left/right edge-invariant tests near the remaining `_layout_reservation_for_template()` calls. These assert public layout policy through a private helper and are the best next candidates for relocation to `tests/unit/test_visible_signature_layout.py`.

- Observation: harness reservation diagnostics can use the public planning boundary while preserving the evidence fields.
  Evidence: `_reconstruct_text_box_bounds_px()` and `_snapshot_backend_reservation()` now build a `LayoutRequest` and call `VisibleSignatureLayoutEngine.plan()` for text metrics, fit issues, and reservation dimensions. They still use `_background_layout_for_stamp()` where the evidence specifically snapshots backend-rendered background layout.

- Observation: GitHub CI failures after the cleanup were dependency-related, not layout-policy regressions.
  Evidence: the GitHub job installs `pip install -e .[dev]`, but `PySide6` was not listed in the `dev` extra. All reported Qt shell and canonical preview failures raised `No module named 'PySide6'`; the rendered-ink fallback failure also depends on the Qt render backend and returned `False` when PySide6 was unavailable. Adding `PySide6>=6.7` to `pyproject.toml` fixed the environment gap, and the affected local suites passed with `205 passed in 28.52s`.

- Observation: preview structural line diagnostics no longer need backend-private text measurement imports.
  Evidence: `_structural_line_bounds_px()` now calls `PyHankoTextMeasurer` from the visible layout boundary. The remaining direct preview-side private helper import is `_stamp_background_for_path()` plus `RoundedBorderTextStampStyle`, which are used for pyHanko preview rendering and optional text/stamp-only bounds, not for generic layout policy.

- Observation: remaining backend reservation tests are backend-specific enough to keep in `tests/unit/test_phase3_signing_backend.py`.
  Evidence: the remaining `_layout_reservation_for_template()` calls support background-layout comparison, rendered-fit fallback setup, ink-validation reservation setup, pyHanko stamp-style parity, and fit gate behavior. Generic public layout-policy expectations have been moved to `tests/unit/test_visible_signature_layout.py`.

- Observation: moving the remaining helper implementation now would be more than a safe mechanical extraction.
  Evidence: `VisibleSignatureLayoutEngine.plan()` still imports backend reservation and fit helpers; `SignatureLayoutPlan` still carries `backend_reservation`; `PyHankoSignatureAppearanceAdapter` still reads pyHanko-shaped layout objects; and backend rendered-fit fallback behavior still depends on backend-specific rendering checks. Extracting these helpers before the architecture-steward follow-up defines a clean split risks moving backend-shaped implementation into the public layout module.

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

- Decision: keep the Qt geometry adapter local to `signing_shell.py`.
  Rationale: the adapter converts a `SignatureLayoutPlan` into widget sizing dimensions and depends on Qt-preview concerns such as loaded pixmap aspect ratios. Keeping it in the presentation layer avoids pushing UI-only semantics into the application layout boundary.
  Date/Author: 2026-04-29 / Codex

- Decision: make the next slice a test cleanup and boundary-hardening slice, not a policy-moving slice.
  Rationale: moving the remaining layout policy out of `phase3_signing_backend.py` would be a larger behavior-risk slice. The immediate next value is to reduce private-helper test coupling while preserving green parity suites, then record which private helpers remain because production compatibility still depends on them.
  Date/Author: 2026-04-30 / Codex

- Decision: keep harness diagnostics out of the next cleanup unless a small adapter replacement is obviously behavior-neutral.
  Rationale: `phase3_harness.py` uses backend-private helpers to snapshot diagnostic reservation data. That is not part of the main production preview/signing path, and changing harness evidence shape should not be mixed with private-helper test cleanup unless the replacement is a direct call to `VisibleSignatureLayoutEngine.plan()` with identical output fields.
  Date/Author: 2026-04-30 / Codex

- Decision: make the first cleanup execution a coverage relocation pass only.
  Rationale: the obvious duplicated tests could be moved behind `VisibleSignatureLayoutEngine.plan()` without production changes. The remaining private-helper assertions are either backend-specific or detailed enough that moving them should be done with focused public-boundary additions, not opportunistically during the same pass.
  Date/Author: 2026-04-30 / Codex

- Decision: do not try to eliminate all private-helper imports in the next slice.
  Rationale: `_build_stamp_style()`, `_build_text_box_style()`, and `_measure_text_box_dimensions()` still protect pyHanko-specific font, style, measurement, and rendered output behavior. The next useful reduction is to move generic reservation policy expectations to `SignatureLayoutPlan` assertions while preserving backend-specific tests in the backend test file.
  Date/Author: 2026-04-30 / Codex

- Decision: keep backend-private helpers for rendered background and stamp-style evidence after harness migration.
  Rationale: `phase3_harness.py` still needs `_background_layout_for_stamp()` and `_build_stamp_style()` to snapshot rendered backend behavior and surface backend reservation errors. Replacing those with public layout planning would hide the backend-specific evidence the harness is meant to capture.
  Date/Author: 2026-04-30 / Codex

- Decision: keep `PySide6` in the repository's `dev` dependency group.
  Rationale: the default GitHub lint-and-test workflow runs the full unit suite after installing `.[dev]`, and the canonical preview, Qt shell, and rendered-ink fallback tests require QtPdf-capable PySide6. Treating PySide6 as a dev dependency matches the current CI command and avoids silently depending on an out-of-band local virtualenv package.
  Date/Author: 2026-05-01 / Codex

- Decision: keep the current backend-private reservation tests, but name generic-looking cases around backend ownership.
  Rationale: after moving public layout-policy expectations to `test_visible_signature_layout.py`, the remaining reservation tests protect backend fit gates, rendered fallback setup, background-layout comparison, and pyHanko stamp-style parity. Removing them now would reduce backend safety without further clarifying the public boundary.
  Date/Author: 2026-05-01 / Codex

- Decision: defer layout-policy extraction from `phase3_signing_backend.py` until after architecture-steward follow-up.
  Rationale: Issue #48 has achieved the caller-facing boundary: backend signing, canonical preview, Qt preview sizing, and harness diagnostics consume `VisibleSignatureLayoutEngine` or `SignatureLayoutPlan`. The remaining helper implementation is entangled with pyHanko layout objects and backend rendered-fit behavior. Deferring extraction avoids turning `visible_signature_layout.py` into a backend-shaped module before the architecture documentation defines the target ownership model.
  Date/Author: 2026-05-01 / Codex

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

The Qt-preview migration slice succeeded.

What changed:

- Added `_preview_layout_plan()` in `signing_shell.py` so Qt preview sizing now asks `VisibleSignatureLayoutEngine` for a `SignatureLayoutPlan`.
- Added `_QtPreviewLayoutGeometry` as the local presentation adapter from `SignatureLayoutPlan` to text/stamp widget sizing dimensions.
- Added `_PreviewStampImageProbe` so Qt preview planning uses the already-loaded pixmap aspect ratio without reading fake or missing image paths from tests and UI preview state.
- Updated preview text width limits, stamp max-size calculations, vertical band geometry, and `_update_preview_controls()` to consume `_QtPreviewLayoutGeometry` instead of backend-private reservation helpers.
- Kept `_preview_layout_reservation()` as a compatibility wrapper around the plan for existing focused tests.
- Removed direct imports of `_build_text_box_style`, `_measure_text_box_dimensions`, and `_layout_reservation_for_template` from `signing_shell.py`.

What did not change:

- Qt preview still uses existing presentation-specific inset helpers for stamp pixmap fitting.
- Private backend helper tests remain in place until the final cleanup slice.

Verification results:

    .venv/bin/ruff check --fix src/foliaseal/presentation/qt/signing_shell.py
    Found 1 error (1 fixed, 0 remaining).

    .venv/bin/ruff check src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_harness.py tests/unit/test_signing_preview_renderer.py
    All checks passed!

    .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_harness.py tests/unit/test_signing_preview_renderer.py
    203 passed, 1 warning in 18.66s

The next slice should clean up tests and private-helper coverage now that backend signing, canonical preview, and Qt preview sizing all consume the visible layout boundary.

The Issue #48 state review after architecture documentation found the codebase in a good post-migration state but not architecturally complete.

What is complete:

- The public layout boundary exists and is exported.
- Backend signing uses `VisibleSignatureLayoutEngine.plan()` and `PyHankoSignatureAppearanceAdapter`.
- Canonical preview uses `VisibleSignatureLayoutEngine.plan()` and `PyHankoSignatureAppearanceAdapter`.
- Qt preview sizing uses a local geometry adapter derived from `SignatureLayoutPlan`.
- Focused Issue #48 ruff and pytest validation passed.

What remains:

- `tests/unit/test_phase3_signing_backend.py` still contains broad direct coverage of `_layout_reservation_for_template()`, `_build_stamp_style()`, `_build_text_box_style()`, and `_measure_text_box_dimensions()`.
- `tests/unit/test_signing_preview_renderer.py` still imports `_build_stamp_style()` for a parity check.
- `src/foliaseal/presentation/qt/phase3_harness.py` still uses private backend helpers for diagnostic snapshots.
- `VisibleSignatureLayoutEngine` still delegates layout policy to private helpers and `SignatureLayoutPlan.backend_reservation` remains an opaque backend payload.

Verification results:

    .venv/bin/ruff check src/foliaseal/application/visible_signature_layout.py src/foliaseal/application/phase3_signing_backend.py src/foliaseal/application/signing_preview_renderer.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_visible_signature_layout.py tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_harness.py
    All checks passed!

    .venv/bin/pytest -q tests/unit/test_visible_signature_layout.py tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_harness.py
    332 passed, 1 warning in 30.15s

The next slice should make private-helper tests less central without changing production behavior. Treat this as a cleanup/status slice: move representative layout-reservation expectations into `tests/unit/test_visible_signature_layout.py`, keep or rename only backend tests that protect backend-only pyHanko behavior, and update this ExecPlan with the exact helpers that remain intentionally private.

The first private-helper cleanup pass succeeded.

What changed:

- Added public-boundary tests in `tests/unit/test_visible_signature_layout.py` for horizontal single-line overwide text, horizontal text-first stamp allocation, and template-specific text/stamp area allocation for single-line, multi-line, and wrapped-block layouts.
- Deleted duplicated backend-private reservation tests from `tests/unit/test_phase3_signing_backend.py` that asserted the same generic layout policy through `_layout_reservation_for_template()`.
- Left backend tests that still protect pyHanko style construction, font/text measurement, background-layout rendering details, rendered-fit fallback behavior, and signed PDF behavior.
- Left `phase3_harness.py` diagnostics unchanged in this pass.

Verification results:

    .venv/bin/ruff check tests/unit/test_visible_signature_layout.py tests/unit/test_phase3_signing_backend.py
    All checks passed!

    .venv/bin/pytest -q tests/unit/test_visible_signature_layout.py tests/unit/test_phase3_signing_backend.py
    128 passed in 11.27s

    .venv/bin/ruff check src/foliaseal/application/visible_signature_layout.py tests/unit/test_visible_signature_layout.py tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py src/foliaseal/presentation/qt/phase3_harness.py
    All checks passed!

    .venv/bin/pytest -q tests/unit/test_visible_signature_layout.py tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_harness.py
    272 passed, 1 warning in 26.25s

Remaining private-helper usage after this pass:

- `tests/unit/test_visible_signature_layout.py` imports `_build_stamp_style()` only to compare `PyHankoSignatureAppearanceAdapter` output with the legacy backend path.
- `tests/unit/test_signing_preview_renderer.py` imports `_build_stamp_style()` for a preview/backend parity check.
- `tests/unit/test_phase3_signing_backend.py` still imports `_layout_reservation_for_template()`, `_build_stamp_style()`, `_build_text_box_style()`, and `_measure_text_box_dimensions()` for backend-specific behavior and residual detailed layout-policy tests.
- `src/foliaseal/presentation/qt/phase3_harness.py` still imports private helpers for diagnostic snapshot generation and remains intentionally deferred.

The next slice should continue this cleanup by moving or justifying the remaining generic `_layout_reservation_for_template()` assertions around border-aware outer insets, optical text alignment, compact vertical single-line layout, and horizontal left/right edge invariants.

The second private-helper cleanup pass succeeded.

What changed:

- Added public-boundary tests in `tests/unit/test_visible_signature_layout.py` for no-stamp bottom optical alignment, compact vertical symmetric outer clearances, border-width-sensitive clearances, border-aware outer insets, and horizontal left/right edge invariants.
- Deleted the matching generic `_layout_reservation_for_template()` tests from `tests/unit/test_phase3_signing_backend.py`.
- Updated `src/foliaseal/presentation/qt/phase3_harness.py` so reservation diagnostic snapshots build a `LayoutRequest` and consume `VisibleSignatureLayoutEngine.plan()` for text metrics, fit issues, and reservation dimensions.
- Kept harness use of `_background_layout_for_stamp()` and `_build_stamp_style()` because those evidence paths intentionally snapshot backend-rendered background layout and backend stamp-style failures.

Verification results:

    .venv/bin/pytest -q tests/unit/test_visible_signature_layout.py
    31 passed in 0.30s

    .venv/bin/ruff check src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_visible_signature_layout.py tests/unit/test_phase3_signing_backend.py
    All checks passed!

    .venv/bin/pytest -q tests/unit/test_visible_signature_layout.py tests/unit/test_phase3_signing_backend.py tests/unit/test_phase3_harness.py
    223 passed, 1 warning in 12.45s

    .venv/bin/ruff check src/foliaseal/application/visible_signature_layout.py tests/unit/test_visible_signature_layout.py tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py src/foliaseal/presentation/qt/phase3_harness.py
    All checks passed!

    .venv/bin/pytest -q tests/unit/test_visible_signature_layout.py tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_harness.py
    272 passed, 1 warning in 26.38s

Remaining private-helper usage after this pass:

- `tests/unit/test_phase3_signing_backend.py` still imports `_layout_reservation_for_template()` for backend-specific rendered-fit setup, background-layout comparison, and stamp-style behavior that is not generic layout policy.
- `tests/unit/test_phase3_signing_backend.py` keeps `_build_stamp_style()`, `_build_text_box_style()`, and `_measure_text_box_dimensions()` coverage for pyHanko style/font/text measurement and signed output behavior.
- `src/foliaseal/presentation/qt/phase3_harness.py` now uses `_build_stamp_style()` only for backend reservation error diagnostics.
- `src/foliaseal/application/signing_preview_renderer.py` still imports `_build_text_box_style()` and `_measure_text_box_dimensions()` for structural line-bound diagnostics outside the main canonical preview layout path.

The next slice should reassess whether the remaining preview structural line-bound diagnostics should move behind a public text-measurement or layout-boundary helper, and rename or narrow any backend reservation tests that are now backend-specific rather than generic layout-policy specifications.

The CI dependency follow-up succeeded.

What changed:

- Added `PySide6>=6.7` to the `dev` optional dependency group in `pyproject.toml`.
- Confirmed the CI failure cluster was caused by GitHub installing `.[dev]` without PySide6 while local validation used a virtualenv where PySide6 was already present.
- Confirmed the lone rendered-ink fallback failure was also caused by the same missing Qt render backend dependency because that fallback renders a canonical preview internally.

Verification results:

    .venv/bin/ruff check pyproject.toml tests/unit/test_phase3_signing_backend.py tests/unit/test_qt_signing_shell.py tests/unit/test_signing_preview_renderer.py
    All checks passed!

    .venv/bin/pytest -q tests/unit/test_phase3_signing_backend.py::test_single_line_rendered_ink_fallback_caches_identical_checks tests/unit/test_qt_signing_shell.py::test_signing_shell_selection_updates_request tests/unit/test_signing_preview_renderer.py::test_canonical_preview_renderer_produces_raster_and_bounds
    3 passed in 0.51s

    .venv/bin/pytest -q tests/unit/test_phase3_signing_backend.py tests/unit/test_qt_signing_shell.py tests/unit/test_signing_preview_renderer.py
    205 passed in 28.52s

Commit:

    16fe757ff Add PySide6 to dev dependencies

The preview diagnostics and backend test ownership slice succeeded.

What changed:

- `src/foliaseal/application/signing_preview_renderer.py` no longer imports `_build_text_box_style()` or `_measure_text_box_dimensions()` from `phase3_signing_backend.py`.
- `_structural_line_bounds_px()` now uses the public `PyHankoTextMeasurer` boundary to derive line dimensions for preview appearance snapshots.
- Renamed remaining generic-sounding backend reservation tests so their names describe backend fit gate and structural-reservation ownership:
  - `test_backend_horizontal_multi_line_fit_gate_can_fail_from_height_not_width`
  - `test_backend_horizontal_single_line_structural_reservation_keeps_separator`
- Re-ran the private-helper inventory and confirmed remaining private helper usages are backend-specific or pyHanko parity/evidence-specific.

Verification results:

    .venv/bin/ruff check src/foliaseal/application/signing_preview_renderer.py src/foliaseal/application/visible_signature_layout.py tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py
    All checks passed!

    .venv/bin/pytest -q tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_signing_backend.py tests/unit/test_visible_signature_layout.py
    177 passed in 24.92s

    .venv/bin/pytest -q tests/unit/test_phase3_signing_backend.py::test_single_line_rendered_ink_fallback_caches_identical_checks tests/unit/test_qt_signing_shell.py::test_signing_shell_selection_updates_request tests/unit/test_signing_preview_renderer.py::test_canonical_preview_renderer_produces_raster_and_bounds
    3 passed in 0.55s

Remaining private-helper usage after this pass:

- `tests/unit/test_visible_signature_layout.py` still imports `_build_stamp_style()` only for adapter equivalence against the legacy backend path.
- `tests/unit/test_signing_preview_renderer.py` still imports `_build_stamp_style()` for preview/signed-PDF pyHanko layout parity.
- `tests/unit/test_phase3_signing_backend.py` keeps `_layout_reservation_for_template()`, `_build_stamp_style()`, `_build_text_box_style()`, and `_measure_text_box_dimensions()` where they protect backend-specific fit, style, font, measurement, and rendered-output behavior.
- `src/foliaseal/presentation/qt/phase3_harness.py` keeps `_build_stamp_style()` for backend reservation error diagnostics.

The next slice should not move more test expectations by default. It should decide the architectural end state for Issue #48: either move the remaining layout-policy implementation itself from `phase3_signing_backend.py` into `visible_signature_layout.py`, or explicitly document why the current public boundary over backend compatibility helpers is sufficient for now.

Commit:

    ad48a19b8 Move preview diagnostics onto layout boundary

The layout-policy ownership decision slice chose deferred extraction.

Decision:

- Do not move the remaining layout helper implementation out of `phase3_signing_backend.py` as part of Issue #48.
- Treat the current state as an intentional transitional architecture: production callers consume `VisibleSignatureLayoutEngine`, `LayoutRequest`, `SignatureLayoutPlan`, and `PyHankoSignatureAppearanceAdapter`; the engine and adapter may delegate to backend compatibility helpers internally.
- Let the architecture-steward follow-up define the final ownership split for pure layout policy, pyHanko layout adapters, backend rendered-fit fallback, preview diagnostics, and harness evidence before moving helper implementation.

Rationale:

- The caller-facing boundary goal is already complete.
- The remaining implementation is not neutral: it still uses pyHanko-shaped reservation objects, `backend_reservation`, backend text/style measurement, and rendered-fit fallback checks.
- Extracting now would likely move backend-shaped code into `visible_signature_layout.py`, making the boundary larger but not cleaner.

Verification results:

    .venv/bin/ruff check src/foliaseal/application/signing_preview_renderer.py src/foliaseal/application/visible_signature_layout.py tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py
    All checks passed!

    .venv/bin/pytest -q tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_signing_backend.py tests/unit/test_visible_signature_layout.py
    177 passed in 24.92s

    .venv/bin/pytest -q tests/unit/test_phase3_signing_backend.py::test_single_line_rendered_ink_fallback_caches_identical_checks tests/unit/test_qt_signing_shell.py::test_signing_shell_selection_updates_request tests/unit/test_signing_preview_renderer.py::test_canonical_preview_renderer_produces_raster_and_bounds
    3 passed in 0.55s

The next slice should close the documentation loop: update `docs/ARCHITECTURE.md` if needed and create a follow-up issue for post-architecture-steward layout-policy extraction rather than continuing to expand Issue #48.

The documentation-closure slice succeeded.

What changed:

- `docs/ARCHITECTURE.md` now states that production callers must use `VisibleSignatureLayoutEngine`, `LayoutRequest`, `SignatureLayoutPlan`, and adapter APIs for visible-signature geometry.
- The architecture doc explicitly limits direct backend-private layout helper use to compatibility wrappers, backend-specific tests, adapter parity tests, and pyHanko-rendered evidence.
- The architecture doc records the deferred extraction debt: remaining helper implementation should move only after architecture-steward follow-up defines ownership for neutral policy, pyHanko adapters, backend rendered-fit fallback, preview diagnostics, and harness evidence.
- GitHub issue #49, "Extract visible signature layout policy after architecture review," now tracks the deferred extraction work.

What did not change:

- No production visible-signature layout code moved.
- No test expectations changed.
- Issue #48 remains scoped to the public caller boundary and documentation of the transitional state.

Verification results:

    gh issue list --state open --search "layout policy extraction" --json number,title,url
    []

    gh issue create --title "Extract visible signature layout policy after architecture review" --body ...
    https://github.com/Daekar3/FoliaSeal/issues/49

    rg -n "_layout_reservation_for_template|_build_stamp_style|_build_text_box_style|_measure_text_box_dimensions" src tests
    Confirmed remaining direct helper usage is limited to visible layout compatibility delegation, backend helper definitions/internal backend calls, backend-specific tests, adapter parity tests, preview parity tests, and phase 3 harness backend error diagnostics.

    git diff --check
    No output.

    .venv/bin/ruff check src/foliaseal/application/signing_preview_renderer.py src/foliaseal/application/visible_signature_layout.py src/foliaseal/application/phase3_signing_backend.py src/foliaseal/presentation/qt/phase3_harness.py docs/ARCHITECTURE.md tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py tests/unit/test_visible_signature_layout.py
    All checks passed!

    .venv/bin/pytest -q tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_signing_backend.py tests/unit/test_visible_signature_layout.py
    177 passed in 25.34s

The next slice should prepare the Issue #48 closure report and avoid further helper extraction in this issue unless a validation failure shows the public caller boundary is incomplete.

The Issue #48 closure-report slice succeeded.

Closure summary:

- The GitHub issue requested a public visible-signature layout boundary that callers use instead of importing scattered private helpers.
- `VisibleSignatureLayoutEngine`, `LayoutRequest`, `SignatureLayoutPlan`, and `PyHankoSignatureAppearanceAdapter` now form that boundary.
- Backend signing, canonical preview rendering, Qt preview sizing, and harness reservation diagnostics consume the public plan boundary.
- Broad generic reservation-policy tests have moved to `tests/unit/test_visible_signature_layout.py`.
- Remaining backend-private helper usage is intentionally limited to compatibility delegation, backend-specific pyHanko/rendered-fit behavior, adapter parity tests, preview parity tests, and harness backend error diagnostics.
- Layout-policy implementation extraction is explicitly deferred to GitHub issue #49 so architecture-steward work can define the final ownership split first.

Final validation before closing the issue:

    git diff --check
    No output.

    .venv/bin/ruff check src/foliaseal/application/signing_preview_renderer.py src/foliaseal/application/visible_signature_layout.py src/foliaseal/application/phase3_signing_backend.py src/foliaseal/presentation/qt/phase3_harness.py docs/ARCHITECTURE.md tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py tests/unit/test_visible_signature_layout.py
    All checks passed!

    .venv/bin/pytest -q tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_signing_backend.py tests/unit/test_visible_signature_layout.py
    177 passed in 25.34s

Recommendation after closure:

- Do not automatically execute issue #49 next.
- If the next goal is broader architectural improvement through `$improve-codebase-architecture`, first run a fresh architecture-discovery pass and compare issue #49 against other coupling clusters.
- Treat issue #49 as a strong candidate, not the default next slice, because extracting the remaining visible-signature policy before the next architecture pass may prematurely lock in module boundaries.

## Context and Orientation

This repository is a Python package under `src/foliaseal`. The visible-signature layout code currently lives mainly in `src/foliaseal/application/phase3_signing_backend.py`. That module signs PDFs through pyHanko, a PDF signing library, and also contains private helper functions that measure text, decide how much room the text and stamp image should receive, and validate whether a selected rectangle can contain the requested visible signature.

The canonical preview path lives in `src/foliaseal/application/signing_preview_renderer.py`. It renders a preview of the visible signature and currently imports backend-private helpers so preview geometry matches final signing geometry. The Qt shell path lives in `src/foliaseal/presentation/qt/signing_shell.py`. It has preview sizing helpers that call the same backend-private reservation helpers.

The new module `src/foliaseal/application/visible_signature_layout.py` will define the public application boundary. A "boundary" here means the small set of public types and methods callers should use instead of private helper functions. A "plan" means the typed result of applying layout policy to a request. A "port" means a small protocol that hides a dependency such as text measurement, stamp image inspection, or rendered ink measurement. Ports let tests provide deterministic stand-ins.

The first slice did not delete or move existing helpers. Instead, `VisibleSignatureLayoutEngine` delegates to the current helper path so the new tests describe existing behavior. Later slices migrated backend signing, canonical preview rendering, and Qt preview sizing to consume the plan. The remaining work is to reduce private-helper test coupling and then, in a later larger slice, consider moving policy itself out of `phase3_signing_backend.py`.

At the time of this revision, the boundary, adapter, backend migration, canonical preview migration, Qt preview migration, two private-helper cleanup passes, preview diagnostics cleanup, the layout-policy ownership decision, documentation closure, and closure report are complete. Future policy extraction belongs to GitHub issue #49 after the next architecture-discovery or architecture-steward pass, not to more Issue #48 cleanup.

The CI dependency gap is also closed: GitHub's default `pip install -e .[dev]` path now installs PySide6 for the QtPdf-backed preview and rendered-ink tests. Do not spend the next slice changing Qt test skips or CI commands unless a new CI failure shows PySide6 installation itself is not viable.

## Plan of Work

The next implementation slice is a new architecture-discovery pass, not more Issue #48 implementation.

Start by classifying the remaining production and test imports of these private helpers only to confirm no caller-facing regression has been introduced:

    _layout_reservation_for_template
    _build_stamp_style
    _build_text_box_style
    _measure_text_box_dimensions

Use `rg` to find them in `src/foliaseal/application/visible_signature_layout.py`, `src/foliaseal/application/phase3_signing_backend.py`, `tests/unit/test_phase3_signing_backend.py`, `tests/unit/test_signing_preview_renderer.py`, `tests/unit/test_visible_signature_layout.py`, and `src/foliaseal/presentation/qt/phase3_harness.py`. For this closure slice, do not move the helpers. Instead, record why each remaining category is intentionally allowed:

1. `visible_signature_layout.py` may import backend helpers internally as compatibility delegates.
2. `phase3_signing_backend.py` may retain compatibility helper definitions and backend-specific pyHanko/rendered-fit behavior.
3. Tests may import backend helpers only for backend-specific coverage or adapter equivalence.
4. Harness evidence may import backend helpers only for backend error diagnostics or pyHanko-rendered evidence.

Do not change visible-signature layout policy in this slice. If a test fails because the public boundary does not expose a value currently asserted through a private helper, add the smallest neutral field or test helper around existing `SignatureLayoutPlan` data only if it improves the public boundary. Do not add new production behavior just to preserve a private-helper assertion.

Use the cleanup passes as the baseline: broad overwide-text, text-priority, template-area allocation, optical alignment, compact vertical clearances, border-aware insets, horizontal edge-invariant expectations, preview structural line measurements, and production caller migrations already live behind the public boundary. The next pass should not alter production behavior.

Execute the next pass in this order:

1. Use `$improve-codebase-architecture` to explore the current repo state organically.
2. Compare issue #49 against newly discovered candidates instead of assuming it is next.
3. Pick the highest-value architecture candidate and create or update a refactor RFC.
4. If issue #49 wins, start by designing the target ownership split before moving helper implementation.

Do not change helper implementation as part of Issue #48. Extraction belongs to GitHub issue #49 only if it remains the chosen architecture candidate after discovery.

Historical completed work is retained below for context.

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

    docs/ExecPlans/visible_signature_layout_engine_execplan.md
    src/foliaseal/application/visible_signature_layout.py
    src/foliaseal/application/__init__.py
    tests/unit/test_visible_signature_layout.py

For the completed layout-policy ownership decision and documentation-closure slices, create or update these files only as needed:

    docs/ExecPlans/visible_signature_layout_engine_execplan.md
    docs/ARCHITECTURE.md
    src/foliaseal/application/visible_signature_layout.py
    src/foliaseal/application/phase3_signing_backend.py
    src/foliaseal/application/__init__.py
    tests/unit/test_visible_signature_layout.py
    tests/unit/test_phase3_signing_backend.py

Start with this inventory command:

    rg -n "_layout_reservation_for_template|_build_stamp_style|_build_text_box_style|_measure_text_box_dimensions" tests src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/application/signing_preview_renderer.py src/foliaseal/application/phase3_signing_backend.py src/foliaseal/application/visible_signature_layout.py

The layout-policy ownership decision has already been made: defer extraction to GitHub issue #49. For Issue #48 closure, inspect remaining direct helper usage only to verify the documented allowed categories:

    rg -n "_layout_reservation_for_template|_build_stamp_style|_build_text_box_style|_measure_text_box_dimensions" src tests

Then run focused validation:

    .venv/bin/ruff check src/foliaseal/application/signing_preview_renderer.py src/foliaseal/application/visible_signature_layout.py tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py
    .venv/bin/pytest -q tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_signing_backend.py tests/unit/test_visible_signature_layout.py

Because the default CI path exercises Qt-backed preview rendering, also run this representative Qt/rendered-ink check before committing:

    .venv/bin/pytest -q tests/unit/test_phase3_signing_backend.py::test_single_line_rendered_ink_fallback_caches_identical_checks tests/unit/test_qt_signing_shell.py::test_signing_shell_selection_updates_request tests/unit/test_signing_preview_renderer.py::test_canonical_preview_renderer_produces_raster_and_bounds

If harness diagnostics or Qt preview sizing are touched unexpectedly, also run:

    .venv/bin/pytest -q tests/unit/test_phase3_harness.py tests/unit/test_qt_signing_shell.py

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

The final cleanup slice is accepted when obsolete private-helper tests are deleted or demoted without losing behavior coverage at the visible layout boundary, and the visible layout, backend, canonical preview, Qt shell, and horizontal reservation focused suites pass.

The preview-diagnostics and backend-test-ownership slice is accepted when all of the following are true:

- `src/foliaseal/application/signing_preview_renderer.py` no longer imports backend-private text measurement helpers unless the ExecPlan records a concrete reason they remain preview-specific;
- remaining `_layout_reservation_for_template()` tests in `tests/unit/test_phase3_signing_backend.py` are named and scoped around backend-specific behavior rather than generic layout policy;
- `tests/unit/test_phase3_signing_backend.py` keeps private-helper coverage only where it protects backend-specific pyHanko style construction, text measurement, rendered-fit fallback, background image layout, certificate/timestamp behavior, or signed PDF output;
- `src/foliaseal/presentation/qt/phase3_harness.py` retains only backend-private helper usage that is evidence-specific, such as `_background_layout_for_stamp()` or `_build_stamp_style()` error diagnostics;
- focused ruff and pytest validation passes.

The next layout-policy ownership decision slice is accepted when all of the following are true:

- the ExecPlan records whether remaining layout-policy helper implementation will move into `visible_signature_layout.py` now or remain as backend compatibility delegation for a later issue;
- if helpers move, compatibility wrappers preserve existing backend imports and all focused layout/backend/preview tests pass;
- if helpers do not move, production caller rules are explicit: callers use `VisibleSignatureLayoutEngine`, and direct backend-private helper use is limited to backend tests, pyHanko evidence, or compatibility wrappers;
- focused ruff and pytest validation passes.

The documentation-closure slice is accepted when all of the following are true:

- `docs/ARCHITECTURE.md` records the transitional visible-signature layout architecture and the allowed categories for direct backend-private helper usage;
- a follow-up GitHub issue tracks post-architecture-steward layout-policy extraction;
- this ExecPlan records the architecture documentation update, follow-up issue number, and validation results;
- no production helper implementation is moved as part of Issue #48.

The Issue #48 closure-report slice is accepted when the report confirms that production callers use the public layout boundary, remaining private-helper usage matches documented allowed categories, validation passes, and future extraction is explicitly assigned to issue #49.

The next architecture-discovery pass is accepted when it presents ranked deepening opportunities, compares issue #49 against them, and asks which candidate to explore before proposing interfaces.

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

Revision note: Updated 2026-04-29 by Codex after migrating Qt preview sizing onto a local geometry adapter derived from `SignatureLayoutPlan`; recorded no-I/O stamp probing and focused verification output.

Revision note: Updated 2026-04-30 by Codex after reviewing Issue #48 against the current repo; converted the next step into a private-helper coverage cleanup and boundary-hardening slice, updated the plan path to `docs/PLANS.md`, and recorded current focused validation results.

Revision note: Updated 2026-04-30 by Codex after executing the first private-helper coverage cleanup pass; moved representative generic reservation expectations behind the visible layout boundary, deleted duplicated backend-private tests, and scoped the next cleanup pass to remaining generic reservation details and harness diagnostics.

Revision note: Updated 2026-04-30 by Codex after committing the first cleanup pass as `b105d9d8d`; narrowed the next Issue #48 slice to specific generic reservation tests, preserved backend-specific private-helper coverage, and added harness diagnostic inspection steps.

Revision note: Updated 2026-04-30 by Codex after executing the second private-helper cleanup pass; moved optical alignment, compact clearance, border inset, and horizontal edge-invariant expectations to public layout tests, switched harness reservation diagnostics to `VisibleSignatureLayoutEngine.plan()`, and scoped the next slice to preview diagnostics and remaining backend test ownership.

Revision note: Updated 2026-05-01 by Codex after fixing GitHub CI dependency coverage with `PySide6>=6.7` in the `dev` extra; recorded the dependency-root-cause analysis, affected-suite validation, and clarified that the next Issue #48 slice should stay focused on preview diagnostics and backend test ownership.

Revision note: Updated 2026-05-01 by Codex after executing the preview diagnostics and backend test ownership slice; moved structural line measurement to `PyHankoTextMeasurer`, renamed remaining generic-sounding backend reservation tests, and scoped the next slice to the layout-policy ownership decision.

Revision note: Updated 2026-05-01 by Codex after committing the preview diagnostics cleanup as `ad48a19b8`; clarified the next slice should first decide whether to extract layout policy now or explicitly defer extraction behind the public boundary.

Revision note: Updated 2026-05-01 by Codex after accepting deferred extraction, documenting the transitional architecture in `docs/ARCHITECTURE.md`, and creating GitHub issue #49 for post-architecture-steward layout-policy extraction.

Revision note: Updated 2026-05-01 by Codex after preparing the Issue #48 closure report and recommending a fresh architecture-discovery pass before deciding whether issue #49 should be next.
