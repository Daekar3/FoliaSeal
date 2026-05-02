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
- [ ] Fourth slice: commit the canonical preview neutral-layout migration.
- [ ] Later slice: move private layout policy helpers out of `phase3_signing_backend.py` and delete `SignatureLayoutPlan.backend_reservation` from the public result.

## Surprises & Discoveries

- Observation: `.agents/skills/dev-loop/SKILL.md` is already modified before this work.
  Evidence: `git status --short` showed `M .agents/skills/dev-loop/SKILL.md`.

- Observation: the repository does not currently have the `PLANS.md` file referenced by the write-execplan skill.
  Evidence: `rg --files -g 'PLANS.md' -g 'plans.md' -g '*PLANS*'` returned no matches.

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

The fourth slice is complete pending commit.

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

## Context and Orientation

Issue #48 introduced `foliaseal.application.visible_signature_layout` and moved production callers toward `VisibleSignatureLayoutEngine`. Issue #49 follows up on the architecture review: the boundary exists, but it still exposes `backend_reservation` and imports backend-private helper functions for the real policy.

The RFC on issue #49 recommends a hybrid service: a neutral typed plan as the real boundary, plus convenience facade methods for backend signing and canonical preview rendering. This plan executes that migration incrementally.

## Plan of Work

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
