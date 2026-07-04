# Visible Signature Layout Policy Extraction

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document records the implementation plan for GitHub issue #49, "Extract visible signature layout policy after architecture review." The repository does not currently include the referenced `PLANS.md`; this plan follows the established structure used by the existing ExecPlans in `docs/ExecPlans/`.

## Purpose / Big Picture

After this work, visible-signature geometry will have a deeper application-layer boundary. Backend signing, canonical preview rendering, Qt preview sizing, and Phase 3 harness diagnostics should share one typed layout service rather than passing around backend-private pyHanko reservation objects.

The first slice is intentionally additive and behavior-preserving. It introduces the Issue #49 service facade and migrates backend stamp-style construction onto that facade while leaving the existing `VisibleSignatureLayoutEngine` and `SignatureLayoutPlan.backend_reservation` compatibility payload in place. Later slices can move preview and harness callers and then delete the public backend reservation payload.

## Progress

- [x] (2026-05-02T16:35Z) Created this ExecPlan for issue #49 from the GitHub RFC.
- [x] (2026-05-02T16:35Z) First slice: added `VisibleSignatureLayoutService`, `VisibleSignatureLayoutInput`, `VisibleSignatureLayoutOptions`, and `PyHankoVisibleSignatureStyle` with boundary tests.
- [x] (2026-05-02T16:35Z) First slice: migrated backend `_build_stamp_style()` to use the service facade while preserving rendered-fit fallback behavior.
- [x] (2026-05-02T16:35Z) First slice: ran focused ruff and pytest validation successfully.
- [x] (2026-05-02T16:40Z) First slice: committed the service-facade migration as `c9ec21ca9 Add visible signature layout service facade`.
- [x] (2026-05-02T16:51Z) Second slice: added `CanonicalPreviewLayout` and `VisibleSignatureLayoutService.pyhanko_style_for_canonical_preview()`.
- [x] (2026-05-02T16:51Z) Second slice: moved canonical preview construction and horizontal preview stamp suppression behind the layout service contract.
- [x] (2026-05-02T16:51Z) Second slice: ran focused and adjacent validation successfully.
- [x] (2026-05-02T16:52Z) Second slice: committed the canonical preview facade migration as `d75bcebfe Move canonical preview layout behind service`.
- [x] (2026-05-02T16:55Z) Third slice: replaced Qt shell preview reservation reads with neutral preview geometry.
- [x] (2026-05-02T16:55Z) Third slice: replaced Phase 3 harness backend reservation dimension/content-layout reads with `SignatureLayoutPlan` fields and `LayoutRuleSpec` snapshots.
- [x] (2026-05-02T16:55Z) Third slice: ran focused and adjacent validation successfully.
- [x] (2026-05-02T16:56Z) Third slice: committed the presentation neutral-geometry migration as `20bc6b8cb Use neutral layout geometry in presentation`.
- [x] (2026-05-02T16:59Z) Fourth slice: removed canonical preview optional-layer rendering reads from the backend reservation payload.
- [x] (2026-05-02T16:59Z) Fourth slice: removed `reservation` and `reserved_background_layout` from the public `CanonicalPreviewLayout` facade result.
- [x] (2026-05-02T16:59Z) Fourth slice: ran focused and adjacent validation successfully.
- [x] (2026-05-02T17:00Z) Fourth slice: committed the canonical preview neutral-layout migration as `db62463be Use neutral layout data for preview bounds`.
- [x] (2026-05-02T17:25Z) Fifth slice: moved pyHanko adapter inner-content layout construction from `backend_reservation` to neutral `LayoutRuleSpec`.
- [x] (2026-05-02T17:25Z) Fifth slice: ran focused and adjacent validation successfully.
- [x] (2026-05-02T17:26Z) Fifth slice: committed the neutral pyHanko layout adapter migration as `d0a906866 Build pyHanko layout from neutral spec`.
- [x] (2026-05-02T19:21Z) Sixth slice: moved backend rendered-fit fallback from `_SignatureLayoutReservation` to `SignatureLayoutPlan`.
- [x] (2026-05-02T19:21Z) Sixth slice: ran focused and adjacent validation successfully.
- [ ] Sixth slice: commit the backend rendered-fit neutral-plan migration.
- [x] (2026-07-04T15:02Z) Seventh slice: route background-layout construction through `visible_signature_layout.py` and rewire backend/evidence callers to consume that boundary while preserving preview/signing parity.
- [x] (2026-07-04T15:19Z) Eighth slice: move structural reservation sizing into `visible_signature_layout.py` while preserving `backend_reservation`, backend fit fallback, and preview/signing parity.
- [ ] Later slice: move remaining reservation/fit policy helpers out of `phase3_signing_backend.py` and delete `SignatureLayoutPlan.backend_reservation` from the public result.

## Surprises & Discoveries

- Observation: `.agents/skills/dev-loop/SKILL.md` is already modified before this work.
  Evidence: `git status --short` showed `M .agents/skills/dev-loop/SKILL.md`.

- Observation: the repository does not currently have the `PLANS.md` file referenced by the write-execplan skill.
  Evidence: `rg --files -g 'PLANS.md' -g 'plans.md' -g '*PLANS*'` returned no matches.

- Observation: the next safe deepening slice is smaller than the originally implied “delete backend reservation” endgame.
  Evidence: the 2026-07-04 dev-loop explorer review found that background-layout construction can move first, while `_layout_reservation_for_template()`, fit validation, and `backend_reservation` still couple to rendered-fit fallback and evidence callers.

- Observation: reconstructing background-layout fitting directly from the final neutral `SignatureLayoutPlan` changed single-line left/right preview spacing.
  Evidence: `tests/unit/test_signing_preview_renderer.py` failed on the single-line left/right gap assertions until `PyHankoSignatureAppearanceAdapter.build_background_layout()` switched back to using backend reservation sizing as the structural input for this slice.

- Observation: the structural reservation helper has more callers than the public layout engine alone.
  Evidence: `rg -n "_layout_reservation_for_template\\(" src tests` showed live backend callers in `_build_stamp_style()` support paths, fit helpers, and multiple backend tests, so the ownership move needs a compatibility re-export rather than a hard delete in one cut.

- Observation: backend stamp-style construction can move behind the service facade without moving the backend rendered-fit fallback.
  Evidence: `tests/unit/test_phase3_signing_backend.py` passed after `_build_stamp_style()` switched to `VisibleSignatureLayoutService.pyhanko_style_for_signing()`.

- Observation: canonical preview still needs a temporary reservation compatibility payload for optional text-only and stamp-only layer rendering.
  Evidence: `_render_optional_preview_bounds()` uses the full layout reservation's text and stamp area dimensions. The second slice moved preview style construction into `VisibleSignatureLayoutService.pyhanko_style_for_canonical_preview()` while returning `reservation` and `reserved_background_layout` until a later neutral-geometry slice replaces those reads.

- Observation: Qt preview sizing did not need the backend reservation payload.
  Evidence: `_preview_layout_reservation()` was only used by `tests/unit/test_qt_signing_shell.py` to compute expected text/stamp area dimensions. The production code already used `_QtPreviewLayoutGeometry.from_plan()`, so the private helper could be removed and the test could assert against neutral geometry.

- Observation: Phase 3 harness reservation snapshots can avoid dereferencing `layout_plan.backend_reservation` for their fit-gate dimensions and content layout.
  Evidence: `_snapshot_backend_reservation()` only needed dimensions already exposed on `SignatureLayoutPlan` and a content layout snapshot already exposed as `layout_plan.text_layout`.

- Observation: canonical preview bounds reconstruction can use neutral layout data.
  Evidence: `render_canonical_signature_preview()` needed the reservation object only for text-box, text-area, and stamp-area dimensions plus the reserved stamp layout. These are available as `SignatureLayoutPlan.text_box`, area fields, `text_layout`, and `stamp_layout`.

- Observation: pyHanko stamp-style construction can use neutral layout specs for its inner content layout.
  Evidence: `PyHankoSignatureAppearanceAdapter.build_stamp_style()` only needed `layout_plan.backend_reservation.inner_content_layout`; the same alignment, scaling, and margins are already exposed through `layout_plan.text_layout`.

- Observation: the backend rendered-fit fallback can use neutral layout-plan dimensions.
  Evidence: `_horizontal_multi_line_rendered_layout_fits_reservation()` used `_SignatureLayoutReservation` only for text-box and text-area dimensions. The same values are exposed through `SignatureLayoutPlan.text_box` and `SignatureLayoutPlan.text_area_*`.

## Decision Log

- Decision: make the first issue #49 slice a service-facade introduction, not the full helper extraction.
  Rationale: the RFC calls for removing `backend_reservation` eventually, but the safest first milestone is a public facade that preserves backend behavior and gives later preview/harness migrations a stable target.
  Date/Author: 2026-05-02 / Codex

- Decision: let backend signing continue to own the rendered-fit fallback during the first slice.
  Rationale: the fallback is backend-specific and already depends on signed-output raster behavior. Moving it before the service boundary has parity tests would increase behavior risk.
  Date/Author: 2026-05-02 / Codex

- Decision: keep canonical preview layer-rendering compatibility fields on `CanonicalPreviewLayout` for this slice.
  Rationale: removing `backend_reservation` from preview rendering also requires replacing optional layer reserved-width/height reads with neutral plan data. Keeping the compatibility payload allows the style assembly and stamp-suppression decision to move first without changing preview pixels.
  Date/Author: 2026-05-02 / Codex

- Decision: keep the Phase 3 evidence field names `backend_reservation_snapshot` and `backend_reservation_error` for this slice.
  Rationale: renaming evidence fields would churn the QA evidence contract and fixtures. The implementation now uses neutral layout-plan data for dimensions/content layout, while preserving the external evidence shape for compatibility.
  Date/Author: 2026-05-02 / Codex

- Decision: remove preview reservation compatibility fields before extracting backend helper implementation.
  Rationale: `CanonicalPreviewLayout` no longer needs to expose `reservation` or `reserved_background_layout` once preview bounds use `layout_plan` fields. Removing those payloads narrows the public surface before the larger backend-private helper move.
  Date/Author: 2026-05-02 / Codex

- Decision: convert `LayoutRuleSpec` to pyHanko layout rules inside the layout module adapter.
  Rationale: adapter callers should not need backend reservation objects to build pyHanko styles. A local conversion keeps pyHanko integration behind the adapter while preserving the neutral plan as the public contract.
  Date/Author: 2026-05-02 / Codex

- Decision: keep the backend fallback function in `phase3_signing_backend.py` while changing its input contract.
  Rationale: the fallback still performs backend-specific rendered checks and cleanup. Moving it wholesale into the layout module would mix signing/rendered-output concerns into the neutral policy boundary. Accepting `SignatureLayoutPlan` removes the reservation dependency without changing ownership prematurely.
  Date/Author: 2026-05-02 / Codex

- Decision: split the remaining helper extraction into a background-layout slice and a later reservation/fit slice.
  Rationale: moving background-layout construction behind the application boundary materially removes legacy geometry cruft without risking a larger parity regression in fit rejection, evidence, or preview stamp-suppression behavior. This keeps the current slice SPEC-safe and restartable.
  Date/Author: 2026-07-04 / Codex

- Decision: make the next slice a structural-reservation ownership move only, not a full fit-policy extraction.
  Rationale: `VisibleSignatureLayoutEngine.plan()` still imports `_layout_reservation_for_template()` from the backend, so that is the next real architectural seam. Moving reservation sizing first deepens the layout boundary without forcing the backend rendered-fit fallback or `backend_reservation` consumers to migrate in the same commit.
  Date/Author: 2026-07-04 / Codex

## Outcomes & Retrospective

The first slice is complete and committed.

What changed:

- Added `VisibleSignatureLayoutInput` as the public planning input and retained `LayoutRequest` as a compatibility name.
- Added `VisibleSignatureLayoutOptions` and `PyHankoVisibleSignatureStyle`.
- Added `VisibleSignatureLayoutService.production()`, `VisibleSignatureLayoutService.plan()`, and `VisibleSignatureLayoutService.pyhanko_style_for_signing()`.
- Exported the new layout service and DTOs from `foliaseal.application`.
- Migrated backend `_build_stamp_style()` to obtain its final pyHanko style through the layout service facade after the existing backend fit fallback check.
- Updated `docs/ARCHITECTURE.md` to name the service facade as the preferred new integration point.

Validation:

    .venv/bin/ruff check src/foliaseal/application/visible_signature_layout.py src/foliaseal/application/phase3_signing_backend.py src/foliaseal/application/__init__.py tests/unit/test_visible_signature_layout.py
    All checks passed.

    .venv/bin/pytest -q tests/unit/test_visible_signature_layout.py
    32 passed in 0.36s.

    .venv/bin/pytest -q tests/unit/test_phase3_signing_backend.py
    100 passed in 12.15s.

    .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py
    59 passed in 3.54s.

    .venv/bin/pytest -q tests/unit/test_signing_preview_renderer.py
    50 passed in 14.70s.

The second slice is complete and committed.

What changed:

- Added `CanonicalPreviewLayout` as the layout-service result for canonical preview style construction.
- Added `VisibleSignatureLayoutService.pyhanko_style_for_canonical_preview()`.
- Moved canonical preview style construction and horizontal single-line preview stamp suppression out of `signing_preview_renderer.py`.
- Kept the existing reservation compatibility payload on the preview result so optional layer rendering remains behavior-preserving.
- Updated `docs/ARCHITECTURE.md` to document the canonical-preview service facade.

Validation so far:

    .venv/bin/ruff check src/foliaseal/application/visible_signature_layout.py src/foliaseal/application/signing_preview_renderer.py src/foliaseal/application/__init__.py tests/unit/test_visible_signature_layout.py
    All checks passed.

    .venv/bin/pytest -q tests/unit/test_visible_signature_layout.py
    34 passed in 0.37s.

    .venv/bin/pytest -q tests/unit/test_signing_preview_renderer.py
    50 passed in 15.19s.

    .venv/bin/pytest -q tests/unit/test_phase3_signing_backend.py
    100 passed in 12.56s.

    .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py
    59 passed in 3.69s.

The third slice is complete and committed.

What changed:

- Removed `_preview_layout_reservation()` from the Qt signing shell and updated the Qt test to use `_preview_layout_geometry()`.
- Changed Phase 3 harness backend reservation snapshots to take fit-gate dimensions and content layout from `SignatureLayoutPlan` neutral fields.
- Extended `_snapshot_layout_rule()` so it can snapshot both pyHanko layout rules and public `LayoutRuleSpec` values.

Validation:

    .venv/bin/ruff check src/foliaseal/presentation/qt/signing_shell.py src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_qt_signing_shell.py
    All checks passed.

    .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py
    59 passed in 3.41s.

    .venv/bin/pytest -q tests/unit/test_phase3_harness.py
    95 passed, 1 warning in 1.43s.

The fourth slice is complete and committed.

What changed:

- Changed canonical preview appearance bounds to use `layout_plan.text_layout`, `layout_plan.stamp_layout`, `layout_plan.text_box`, and neutral area dimensions.
- Removed `reservation` and `reserved_background_layout` from `CanonicalPreviewLayout`.
- Updated the visible layout boundary test to assert canonical preview facade parity without relying on the backend reservation payload.

Validation:

    .venv/bin/ruff check src/foliaseal/application/visible_signature_layout.py src/foliaseal/application/signing_preview_renderer.py tests/unit/test_visible_signature_layout.py
    All checks passed.

    .venv/bin/pytest -q tests/unit/test_visible_signature_layout.py
    34 passed in 0.36s.

    .venv/bin/pytest -q tests/unit/test_signing_preview_renderer.py
    50 passed in 14.35s.

    .venv/bin/pytest -q tests/unit/test_phase3_signing_backend.py
    100 passed in 12.25s.

    .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py
    59 passed in 3.47s.

The fifth slice is complete and committed.

What changed:

- Migrated `PyHankoSignatureAppearanceAdapter` so `inner_content_layout` is reconstructed from `layout_plan.text_layout` instead of read from `layout_plan.backend_reservation`.
- Added a local `LayoutRuleSpec` to pyHanko `SimpleBoxLayoutRule` converter inside `visible_signature_layout.py`.

Validation:

    .venv/bin/ruff check src/foliaseal/application/visible_signature_layout.py tests/unit/test_visible_signature_layout.py
    All checks passed.

    .venv/bin/pytest -q tests/unit/test_visible_signature_layout.py
    34 passed in 0.35s.

    .venv/bin/pytest -q tests/unit/test_phase3_signing_backend.py
    100 passed in 12.72s.

    .venv/bin/pytest -q tests/unit/test_signing_preview_renderer.py
    50 passed in 14.83s.

    .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py
    59 passed in 3.31s.

The sixth slice is complete pending commit.

What changed:

- Changed `_horizontal_multi_line_rendered_layout_fits_reservation()` to accept `SignatureLayoutPlan`.
- Changed backend `_build_stamp_style()` to pass the neutral plan to the rendered-fit fallback instead of `layout_plan.backend_reservation`.

Validation:

    .venv/bin/ruff check src/foliaseal/application/phase3_signing_backend.py src/foliaseal/application/visible_signature_layout.py
    All checks passed.

    .venv/bin/pytest -q tests/unit/test_phase3_signing_backend.py
    100 passed in 12.51s.

    .venv/bin/pytest -q tests/unit/test_visible_signature_layout.py tests/unit/test_signing_preview_renderer.py
    84 passed in 14.90s.

    .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py
    59 passed in 3.37s.

    .venv/bin/pytest -q tests/unit/test_phase3_harness.py
    95 passed, 1 warning in 1.43s.

The seventh slice is complete.

What this slice will change:

- host public background-layout construction in `src/foliaseal/application/visible_signature_layout.py` so callers enter the layout boundary for pyHanko background-layout assembly;
- rewire backend `_build_stamp_style()` and backend reservation evidence assembly to consume that boundary instead of calling backend-private `_background_layout_for_stamp()` directly;
- migrate generic background-layout assertions from `tests/unit/test_phase3_signing_backend.py` into `tests/unit/test_visible_signature_layout.py`;
- keep preview/backend parity coverage in `tests/unit/test_signing_preview_renderer.py` and keep rendered-fit fallback ownership in `src/foliaseal/application/phase3_signing_backend.py`.

What this slice will not change:

- `SignatureLayoutPlan.backend_reservation` remains in place;
- `_layout_reservation_for_template()` remains backend-owned;
- rendered-fit fallback and fit rejection remain backend-owned;
- preview stamp-suppression behavior remains unchanged.

## Context and Orientation

Issue #48 introduced `foliaseal.application.visible_signature_layout` and moved production callers toward `VisibleSignatureLayoutEngine`. Issue #49 follows up on the architecture review: the boundary exists, but it still exposes `backend_reservation` and imports backend-private helper functions for the real policy.

The RFC on issue #49 recommends a hybrid service: a neutral typed plan as the real boundary, plus convenience facade methods for backend signing and canonical preview rendering. This plan executes that migration incrementally.

As of 2026-07-04, most neutral-plan migration work is already landed. The remaining legacy geometry cruft is concentrated in `src/foliaseal/application/phase3_signing_backend.py`, where reservation sizing, fit validation, and rendered-fit fallback still own the structural geometry inputs that pyHanko style assembly depends on. Before this slice, `_background_layout_for_stamp()` also owned the public call path for stamp/background placement math. The canonical preview path in `src/foliaseal/application/signing_preview_renderer.py` already goes through the layout service and must stay pixel-parity aligned with backend signing because `docs/SPEC.md` treats preview/output trust as a product principle.

## Plan of Work

For the seventh slice:

1. In `src/foliaseal/application/visible_signature_layout.py`, add a service-owned background-layout construction path that takes the meaningful inputs the backend currently uses: layout template, stamp position, optional image background, signature rectangle, text box dimensions, and box style. Keep the pyHanko-specific return type behind the layout service boundary. For this slice, allow the implementation to keep using backend reservation sizing as its structural input so long as the caller-facing ownership moves to the layout boundary.

2. In `PyHankoSignatureAppearanceAdapter.build_stamp_style()`, stop importing backend-private `_background_layout_for_stamp()` and instead call the new local background-layout helper. This is the core behavior change for the slice: backend stamp-style assembly should still happen, but the geometry policy should come from the layout boundary.

3. In `src/foliaseal/application/phase3_signing_backend.py`, rewire `_build_stamp_style()` and `build_backend_reservation_evidence()` so they no longer call `_background_layout_for_stamp()` directly. If the backend still needs a compatibility wrapper for internal callers, keep it as a thin pass-through to the layout boundary and mark it as transitional in comments only if the flow would otherwise be unclear.

4. In `tests/unit/test_visible_signature_layout.py`, add boundary tests that assert background-layout behavior for representative layout-template and stamp-position combinations. These tests should become the primary proof of background-layout math. In `tests/unit/test_phase3_signing_backend.py`, trim generic geometry assertions so the backend tests focus on backend-specific behavior: fit rejection, rounded-border style selection, rendered-fit fallback, and service wiring.

5. In `tests/unit/test_signing_preview_renderer.py`, keep the existing preview/backend parity assertions intact or strengthen them if necessary so that any accidental drift between preview and backend output remains visible during validation.

6. Update `docs/ARCHITECTURE.md` after the code lands so the visible-layout boundary description says background-layout construction now routes through the layout service, while reservation sizing and fit helpers remain backend-owned. Do not claim the broader reservation/fit extraction is done; this slice is only a call-path ownership move.

Validation for the completed slice:

    .venv/bin/python -m ruff check src/foliaseal/application/visible_signature_layout.py src/foliaseal/application/phase3_signing_backend.py tests/unit/test_visible_signature_layout.py tests/unit/test_signing_preview_renderer.py
    All checks passed.

    .venv/bin/python -m pytest -q tests/unit/test_visible_signature_layout.py tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py
    195 passed in 28.07s.

Change note (2026-07-04): Revised the seventh-slice language after compliance review to describe the landed behavior accurately. The call path now enters the layout boundary for background-layout construction, but the implementation still uses backend reservation geometry and therefore does not complete the broader helper extraction.

The eighth slice is complete.

What this slice changed:

- moved `_SignatureLayoutReservation` and `_layout_reservation_for_template()` ownership into `src/foliaseal/application/visible_signature_layout.py`;
- updated `VisibleSignatureLayoutEngine.plan()` and `PyHankoSignatureAppearanceAdapter.build_background_layout()` to use the layout-owned reservation helper directly;
- changed `src/foliaseal/application/phase3_signing_backend.py` so its `_layout_reservation_for_template()` name is now a compatibility delegate to the layout module instead of the owning implementation;
- preserved `SignatureLayoutPlan.backend_reservation`, backend fit fallback, and backend-facing helper names so downstream callers and tests did not need to migrate in the same slice.

Validation for the completed slice:

    .venv/bin/python -m ruff check src/foliaseal/application/visible_signature_layout.py src/foliaseal/application/phase3_signing_backend.py
    All checks passed.

    .venv/bin/python -m pytest -q tests/unit/test_visible_signature_layout.py
    39 passed in 0.41s.

    .venv/bin/python -m pytest -q tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py
    156 passed in 27.93s.

Change note (2026-07-04): Added the eighth-slice completion notes after compliance review confirmed that structural reservation sizing now lives in `visible_signature_layout.py` while backend compatibility wrappers and fit fallbacks remain intentionally in place.

For the first slice:

1. Add `VisibleSignatureLayoutInput` and make the current `LayoutRequest` compatibility type derive from it.
2. Add `VisibleSignatureLayoutOptions` for include-border/include-background/fit-policy flags.
3. Add `PyHankoVisibleSignatureStyle` and `VisibleSignatureLayoutService.pyhanko_style_for_signing()`.
4. Add a boundary test proving the service facade produces the same observable style as the current engine-plus-adapter path.
5. Change backend `_build_stamp_style()` to call `VisibleSignatureLayoutService.pyhanko_style_for_signing()` after its existing fit fallback check.
6. Export the new service and DTOs from `foliaseal.application`.

## Validation and Acceptance

The first slice is accepted when:

- focused ruff passes for changed files;
- `tests/unit/test_visible_signature_layout.py` passes;
- `tests/unit/test_phase3_signing_backend.py` passes;
- the backend style construction tests still preserve current behavior.

## Idempotence and Recovery

This slice is additive. If validation exposes behavior drift, keep `VisibleSignatureLayoutEngine` and `PyHankoSignatureAppearanceAdapter` unchanged, revert only the backend call-site migration, and leave the service facade tested as an additive boundary until the mismatch is understood.

## Artifacts and Notes

Do not refresh generated Phase 3 harness artifacts in this slice. The only expected files are application code, focused tests, exports, this ExecPlan, and any directly relevant architecture documentation.

## Interfaces and Dependencies

The first slice keeps pyHanko object construction behind `PyHankoSignatureAppearanceAdapter` and exposes it through `VisibleSignatureLayoutService.pyhanko_style_for_signing()`. Text measurement, image probing, and horizontal ink measurement remain local-substitutable ports.
