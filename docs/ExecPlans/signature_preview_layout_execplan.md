# Extract the signing-shell preview layout boundary

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows the requirements in `.agents/skills/write-execplan/PLANS.md`. It is self-contained so a contributor can resume the slice from only this file and the current repository tree.

## Purpose / Big Picture

FoliaSeal's signing shell already separates certificate and preset reconciliation into an application-layer coordinator and canonical preview rendering into a dedicated lifecycle helper. The remaining preview-specific complexity is the geometry and widget-layout handoff inside `SignaturePropertiesPanel`. After this change, the visible-signature preview card should still look and behave the same, but the sizing math, orientation decisions, stamp/text band sizing, and widget ordering should live behind a smaller presentation-layer boundary that can be tested directly without exercising the full shell.

This is still an internal refactor slice. A user should not see a new feature, but the current preview behavior must remain demonstrably intact by running focused tests that pin the same geometry, padding, orientation, and canonical-render handoff rules.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/signature_properties_coordinator_execplan.md` completed first so preview layout work is not mixed with certificate and preset reconciliation.
- [x] `docs/ExecPlans/signature_preview_lifecycle_execplan.md` completed first so canonical preview snapshot lifecycle is already isolated before this slice moves the remaining geometry and layout handoff.
- [ ] A later child ExecPlan may simplify `SigningWorkspaceWidget` or split `signing_shell.py` more broadly after both preview sub-boundaries exist.

## Progress

- [x] (2026-05-22T15:27:00Z) Completed the required `explorer-light` audit and fixed the next slice to preview geometry and widget-layout handoff only.
- [x] (2026-05-22T15:34:00Z) Wrote this ExecPlan with the boundary constrained to presentation-layer preview layout planning and application of that plan to the existing preview widgets.
- [x] (2026-05-22T16:18:00Z) Added `tests/unit/test_signature_preview_layout.py` and moved preview-layout assertions for available-width selection, card sizing, stamp/text band fitting, widget ordering, canonical-render handoff, and helper-level layout rules onto the new boundary.
- [x] (2026-05-22T16:52:00Z) Introduced `src/foliaseal/presentation/qt/signature_preview_layout.py` and moved sizing, orientation, stamp/text band planning, widget-order application, and canonical-render handoff into `QtSignaturePreviewLayout`.
- [x] (2026-05-22T17:09:00Z) Rewired `SignaturePropertiesPanel` to orchestrate `QtSignaturePreviewLayout.plan()`, `QtCanonicalPreviewLifecycle.refresh()`, and `QtSignaturePreviewLayout.apply()` while keeping widget ownership and coordinator interaction local.
- [x] (2026-05-22T17:46:00Z) Shrunk `tests/unit/test_qt_signing_shell.py` so preview math/helper assertions now live at the layout boundary and the shell remains a thinner integration seam.
- [x] (2026-05-22T18:14:00Z) Closed the review finding that normal widget close could skip preview-snapshot disposal by using close-aware shell/panel widgets and updating the fake Qt close path to exercise `closeEvent`.
- [x] (2026-05-22T18:31:00Z) Ran focused validation, completed the required compliance review against `docs/`, and updated architecture/ExecPlan documentation to match the completed boundary split.

## Surprises & Discoveries

- Observation: the remaining preview complexity is concentrated in `_update_preview_controls()` rather than spread evenly through the shell.
  Evidence: `src/foliaseal/presentation/qt/signing_shell.py` still computes card size, inner-body size, preview orientation, reserved text/stamp sizes, stamp scaling, layout item order, and label visibility in one method before it calls `_apply_canonical_preview_render()`.

- Observation: the next safe split is above the public visible-signature layout boundary, not below it.
  Evidence: current preview geometry reads from `_preview_layout_geometry()` and other helpers that already consume the public preview/layout information; `docs/ARCHITECTURE.md` still marks backend-private layout carryover as debt and says Qt shell tests should stay thin integration.

- Observation: close-triggered cleanup needed its own explicit seam even though lifecycle disposal already existed.
  Evidence: compliance review found that the shell relied on `destroyed`-signal cleanup, while the fake test widget emitted `destroyed` from `close()` and masked the real gap. The completed slice now uses close-aware widgets and a fake `close()` path that exercises `closeEvent`.

## Decision Log

- Decision: the new boundary will live in `src/foliaseal/presentation/qt/`, not in `src/foliaseal/application/`.
  Rationale: the remaining responsibilities are widget-facing decisions such as fixed sizes, visible labels, layout item ordering, and alignment flags. Those are presentation concerns even when they rely on preview geometry data.
  Date/Author: 2026-05-22 / Codex

- Decision: `QtCanonicalPreviewLifecycle` will remain unchanged in this slice and will be consumed as an input boundary.
  Rationale: the prior slice already isolated snapshot lifecycle. Folding it into the new helper would enlarge the change set and blur ownership just after that boundary stabilized.
  Date/Author: 2026-05-22 / Codex

- Decision: the primary change class for the first commit should be behavior change plus direct test movement at the new boundary; documentation/status updates should remain a follow-on commit only if compliance review requires them.
  Rationale: the preview layout extraction is already a narrow behavior slice, and mixing broad documentation churn into the initial edit would make regression review harder.
  Date/Author: 2026-05-22 / Codex

## Outcomes & Retrospective

This slice is now implemented. `src/foliaseal/presentation/qt/signature_preview_layout.py` owns preview geometry/layout planning, stamp/text band fitting, widget ordering, border-aware sizing, canonical-render handoff, and the helper-level preview math that previously lived in `signing_shell.py`.

`SignaturePropertiesPanel` is now narrower. It still owns the preview widget tree, coordinator interaction, lifecycle orchestration, and user-facing panel API, but it no longer owns the geometry/layout implementation details that made `_update_preview_controls()` dense and hard to test directly.

The shell test surface is also narrower. `tests/unit/test_signature_preview_layout.py` now pins the preview layout contract directly, while `tests/unit/test_qt_signing_shell.py` keeps thinner integration checks for preview text, active-snapshot discoverability, scaled canonical render sizing, outer-card chrome suppression, and close-path cleanup.

## Context and Orientation

The signing shell lives in `src/foliaseal/presentation/qt/signing_shell.py`. That file is still large because one class, `SignaturePropertiesPanel`, owns several distinct responsibilities. Two of those responsibilities have already been split out in earlier slices. `DefaultSignaturePropertiesCoordinator` in `src/foliaseal/application/signature_properties_coordinator.py` owns certificate and preset reconciliation, validation text, and readiness state. `QtCanonicalPreviewLifecycle` in `src/foliaseal/presentation/qt/signature_preview_lifecycle.py` owns canonical preview rendering, temporary snapshot replacement and cleanup, render-backend reuse, pixmap loading, and teardown disposal.

Before this slice, the remaining preview-specific logic still lived in `_update_preview_controls()` inside `SignaturePropertiesPanel`. In this repository, the “preview card” is the visible-signature summary widget shown in the signing shell. It has a card container, one vertical preview body, one horizontal preview body, stamp labels, detail labels, and two render labels for canonical preview images. This slice moved the orientation decision, card/body sizing, stamp/text reservation, widget ordering, and canonical-render handoff into `QtSignaturePreviewLayout`.

The preview size and placement helpers now live in `src/foliaseal/presentation/qt/signature_preview_layout.py`. Examples include `_preview_available_width()`, `_preview_body_size()`, `_preview_layout_geometry()`, `_preview_vertical_band_geometry()`, `_fit_vertical_preview_band_geometry()`, `_preview_stamp_max_size()`, and `_preview_card_padding_px()`. Those helpers are now owned by the preview-layout boundary instead of being re-exported through the shell.

The tests that pin this behavior are now split across `tests/unit/test_signature_preview_layout.py` and `tests/unit/test_qt_signing_shell.py`. The new boundary test file covers thick-border padding, available-width rules, vertical versus horizontal body ordering, stamp alignment, reserved text/stamp dimensions, fixed-size behavior, and canonical-render handoff behavior. The shell tests now stay at the thinner integration seam.

This slice added `src/foliaseal/presentation/qt/signature_preview_layout.py` as the boundary for preview geometry and widget-layout handoff. `SignaturePropertiesPanel` still owns the widget tree and still orchestrates the coordinator and the canonical preview lifecycle, but it no longer computes or applies most preview layout rules directly.

## Plan of Work

This slice is complete. The work happened in the order above: add direct boundary tests, create `signature_preview_layout.py`, rewire `SignaturePropertiesPanel`, trim shell-level duplication, close the cleanup finding from compliance review, and update docs/status text to match the final split.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

Inspect the current preview-layout path before editing:

    sed -n '2140,2675p' src/foliaseal/presentation/qt/signing_shell.py
    rg -n "preview_|thick-border|padding|single_body_container|multi_body_container" tests/unit/test_qt_signing_shell.py
    sed -n '1,220p' src/foliaseal/presentation/qt/signature_preview_lifecycle.py

Add the new direct boundary tests and run them together with the affected shell tests:

    pytest tests/unit/test_signature_preview_layout.py tests/unit/test_qt_signing_shell.py -k "preview"

Expected result before the helper exists: the new tests fail because `signature_preview_layout.py` or its public API does not exist yet.

After the new layout module and shell wiring are in place, run the focused suites that exercise the new boundary and the remaining shell seam:

    pytest tests/unit/test_signature_preview_layout.py tests/unit/test_signature_preview_lifecycle.py tests/unit/test_qt_signing_shell.py

Run focused lint for the touched files:

    ruff check src/foliaseal/presentation/qt/signature_preview_layout.py src/foliaseal/presentation/qt/signature_preview_lifecycle.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_signature_preview_layout.py tests/unit/test_signature_preview_lifecycle.py tests/unit/test_qt_signing_shell.py

If documentation changes are needed after compliance review, rerun the relevant focused checks and record the exact command/results here.

## Validation and Acceptance

Acceptance for this slice is behavioral, not structural.

The new preview-layout tests must prove that the extracted boundary preserves the current preview card layout contract. That means the card size and inner-body size remain border-aware, available width uses the correct ancestor width, thick borders adjust padding and horizontal text width correctly, vertical and horizontal preview modes keep the expected widget order and alignment, reserved text and stamp dimensions are honored, and canonical render state still takes over the active preview surface without losing the expected fixed sizes.

The shell tests must remain a smoke test for the integration seam. They should still prove that the panel shows preview text, exposes the canonical snapshot where the shell expects it, sizes the render label/body to the scaled pixmap, suppresses outer card chrome during canonical preview, and cleans up the active snapshot on widget close.

Focused validation passes when the selected `pytest` command and the focused `ruff check` both pass. `git diff --check` must also pass before the slice is considered complete.

## Idempotence and Recovery

This refactor is safe to repeat because it can be introduced additively. First add the new helper and direct tests, then rewire the shell to call it, then trim redundant shell assertions. If the widget ordering breaks during the move, restore the previous `_update_preview_controls()` call path temporarily, keep the new tests, and move one planning block at a time into the helper until the tests pass again.

If the direct tests start depending on the entire shell widget tree, reduce them back to the preview-controls dataclass plus fake widgets from `tests/unit/test_qt_signing_shell.py`. If a regression appears only in canonical preview mode, keep `QtCanonicalPreviewLifecycle` untouched and inspect only the handoff path that consumes `CanonicalPreviewRenderState`.

## Artifacts and Notes

Current evidence for the completed boundary split:

    src/foliaseal/presentation/qt/signature_preview_layout.py
    - QtSignaturePreviewLayout.plan() computes preview orientation, card/body size, reserved text/stamp dimensions, label widths, and stamp scaling.
    - QtSignaturePreviewLayout.apply() owns widget ordering, alignment, visibility, and canonical-render handoff into the active preview surface.

    src/foliaseal/presentation/qt/signing_shell.py
    - _update_preview_controls() is now an orchestration path that coordinates preview-layout planning, canonical preview lifecycle refresh, and preview-layout application.
    - the shell root widget and properties-panel widget both use close-aware cleanup so canonical preview disposal runs on normal close paths.

    tests/unit/test_signature_preview_layout.py
    - pins card size, padding, widget ordering, alignment, reserved geometry, helper-level width math, and canonical render sizing/visibility at the preview-layout boundary.

    tests/unit/test_qt_signing_shell.py
    - now keeps only thin shell integration checks for preview text, canonical snapshot discoverability, scaled render sizing, card chrome suppression, and close-path cleanup.

Expected validation evidence after implementation:

    pytest tests/unit/test_signature_preview_layout.py tests/unit/test_signature_preview_lifecycle.py tests/unit/test_qt_signing_shell.py
    79 passed

    ruff check src/foliaseal/presentation/qt/signature_preview_layout.py src/foliaseal/presentation/qt/signature_preview_lifecycle.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_signature_preview_layout.py tests/unit/test_signature_preview_lifecycle.py tests/unit/test_qt_signing_shell.py
    All checks passed!

    git diff --check
    <no output>

## Interfaces and Dependencies

Define the new layout boundary in `src/foliaseal/presentation/qt/signature_preview_layout.py`. A stable end-state for this slice is:

    @dataclass(frozen=True)
    class PreviewLayoutState:
        is_vertical: bool
        card_size: tuple[int, int]
        body_size: tuple[int, int]
        detail_width: int
        preview_scale: float
        fallback_card_style: str
        render_target: str

    class QtSignaturePreviewLayout:
        def plan(
            self,
            *,
            preview: SigningDraftPreview,
            controls: PreviewControls,
        ) -> PreviewLayoutState: ...

        def apply(
            self,
            *,
            preview: SigningDraftPreview,
            controls: PreviewControls,
            state: PreviewLayoutState,
            canonical_render_state: CanonicalPreviewRenderState | None,
        ) -> None: ...

The exact state fields may grow if needed, but the public boundary must remain explicit and widget-facing. The helper should consume the existing top-level preview math helpers rather than reimplement them from scratch, unless moving a helper into the module clearly simplifies ownership. `SignaturePropertiesPanel` should keep coordinator interaction, lifecycle interaction, validation rendering, and widget-tree ownership. `QtCanonicalPreviewLifecycle` should continue to return `CanonicalPreviewRenderState`; the new helper must treat that as input and must not recreate snapshot lifecycle behavior.

Change note: 2026-05-22 / Codex

This ExecPlan now records the completed preview-layout slice after the preview-lifecycle boundary. The implementation extracted preview geometry/layout ownership into a dedicated Qt boundary, narrowed shell tests to thin integration coverage, and closed the close-path cleanup gap identified during compliance review.
