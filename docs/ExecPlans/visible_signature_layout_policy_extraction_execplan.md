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
- [ ] First slice: commit the service-facade migration.
- [ ] Later slice: move canonical preview construction to `pyhanko_style_for_canonical_preview()` and keep preview-only stamp suppression behind the service contract.
- [ ] Later slice: replace Qt shell and Phase 3 harness `backend_reservation` dereferences with neutral plan fields or diagnostic snapshots.
- [ ] Later slice: move private layout policy helpers out of `phase3_signing_backend.py` and delete `SignatureLayoutPlan.backend_reservation` from the public result.

## Surprises & Discoveries

- Observation: `.agents/skills/dev-loop/SKILL.md` is already modified before this work.
  Evidence: `git status --short` showed `M .agents/skills/dev-loop/SKILL.md`.

- Observation: the repository does not currently have the `PLANS.md` file referenced by the write-execplan skill.
  Evidence: `rg --files -g 'PLANS.md' -g 'plans.md' -g '*PLANS*'` returned no matches.

- Observation: backend stamp-style construction can move behind the service facade without moving the backend rendered-fit fallback.
  Evidence: `tests/unit/test_phase3_signing_backend.py` passed after `_build_stamp_style()` switched to `VisibleSignatureLayoutService.pyhanko_style_for_signing()`.

## Decision Log

- Decision: make the first issue #49 slice a service-facade introduction, not the full helper extraction.
  Rationale: the RFC calls for removing `backend_reservation` eventually, but the safest first milestone is a public facade that preserves backend behavior and gives later preview/harness migrations a stable target.
  Date/Author: 2026-05-02 / Codex

- Decision: let backend signing continue to own the rendered-fit fallback during the first slice.
  Rationale: the fallback is backend-specific and already depends on signed-output raster behavior. Moving it before the service boundary has parity tests would increase behavior risk.
  Date/Author: 2026-05-02 / Codex

## Outcomes & Retrospective

The first slice is complete pending commit.

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
