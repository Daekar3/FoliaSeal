# Extract the signing-shell preview lifecycle boundary

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows the requirements in `.agents/skills/write-execplan/PLANS.md`. It is self-contained so a contributor can resume the slice from only this file and the current repository tree.

## Purpose / Big Picture

FoliaSeal's signing shell now has an application-layer boundary for certificate and preset reconciliation, but preview refresh still mixes too many concerns inside `SignaturePropertiesPanel`: it pulls the latest draft state, updates preview widgets, invokes canonical pyHanko rendering, replaces temporary snapshot files, and manages the reusable render backend. After this slice, the shell will still show the same preview card, but the preview and canonical-render lifecycle will run through a dedicated boundary that can be tested without driving the full shell widget.

This slice is intentionally narrow. It extracts only the preview/canonical-render lifecycle: refresh, snapshot replacement and cleanup, backend reuse, pixmap loading, and the handoff from `SigningDraftPreview` to preview-card presentation. It does not migrate the remaining `_preview_*` sizing and geometry helpers, and it does not broaden into workspace orchestration or a larger shell-file breakup.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/signature_properties_coordinator_execplan.md` completed first so preview migration is not mixed with certificate/preset reconciliation work.
- [ ] A later child ExecPlan may extract the remaining `_preview_*` geometry and sizing helpers after this lifecycle boundary exists.
- [ ] A later child ExecPlan may simplify `SigningWorkspaceWidget` and broader shell composition once both the state boundary and preview boundary are in place.

## Progress

- [x] (2026-05-22T02:48:00Z) Reviewed the completed coordinator slice and confirmed that preview lifecycle extraction is the next high-leverage boundary.
- [x] (2026-05-22T02:56:00Z) Completed the required `explorer-light` review of `signing_shell.py`, preview-rendering code, relevant tests, and current docs before drafting this plan.
- [x] (2026-05-22T03:05:00Z) Wrote this ExecPlan with the slice boundary fixed to preview/canonical-render lifecycle only.
- [x] (2026-05-22T03:31:00Z) Added `tests/unit/test_signature_preview_lifecycle.py` to pin canonical render params, backend reuse, snapshot replacement/cleanup, repeated-refresh retention, fallback behavior, and disposal cleanup at the new boundary.
- [x] (2026-05-22T03:46:00Z) Introduced `src/foliaseal/presentation/qt/signature_preview_lifecycle.py` and moved canonical snapshot render/replace/cleanup logic, pixmap loading, and backend reuse into `QtCanonicalPreviewLifecycle`.
- [x] (2026-05-22T04:02:00Z) Rewired `SignaturePropertiesPanel.refresh_preview()` and related paths to use the new lifecycle boundary while preserving preview-card behavior and keeping geometry helpers in the shell.
- [x] (2026-05-22T04:18:00Z) Moved lifecycle-specific assertions out of `tests/unit/test_qt_signing_shell.py`, leaving thin shell integration checks for card chrome, scaled pixmap sizing, snapshot discoverability, and widget-teardown cleanup.
- [x] (2026-05-22T04:44:00Z) Ran focused validation, completed the required compliance review, fixed teardown disposal, and updated architecture/ExecPlan documentation to match the implemented boundary.

## Surprises & Discoveries

- Observation: `SignaturePropertiesPanel.refresh_preview()` now has two kinds of responsibilities layered together: state synchronization from `SignaturePropertiesCoordinator` and preview/canonical-render lifecycle in the Qt layer.
  Evidence: the method calls `self._coordinator.load(...)`, updates widget state, and then calls `_update_preview_controls()`, which eventually calls `_apply_canonical_preview_render()`.

- Observation: the main regression risk is ordering, not just code location.
  Evidence: `_apply_canonical_preview_render()` currently renders a new snapshot, cleans up the previous snapshot directory, updates card chrome, loads the Qt pixmap, and toggles render-label visibility in one ordered path; the existing shell tests pin all of those behaviors.

- Observation: teardown cleanup was a real gap after the first extraction pass.
  Evidence: compliance review found that `QtCanonicalPreviewLifecycle.dispose()` existed but was not called when the shell root widget was destroyed, leaving a temp-dir leak path until widget destruction was wired to `SignaturePropertiesPanel.dispose()`.

## Decision Log

- Decision: The new boundary will live in `src/foliaseal/presentation/qt/`, not in the application layer and not as an expansion of `DefaultSignaturePropertiesCoordinator`.
  Rationale: This slice still depends on Qt binding details such as pixmap loading and widget-facing render state. The application layer should continue to own draft semantics and certificate/preset reconciliation, while the presentation layer owns the canonical preview lifecycle.
  Date/Author: 2026-05-22 / Codex

- Decision: This slice will extract lifecycle responsibilities first and leave `_preview_*` geometry helpers in place.
  Rationale: The explorer review showed that geometry/sizing cleanup is a separate concern with a broader blast radius. Pulling both into one slice would make failures harder to attribute and would enlarge the change set beyond the narrow ExecPlan B target.
  Date/Author: 2026-05-22 / Codex

- Decision: Existing shell tests that pin canonical snapshot behavior will be adapted or moved, not duplicated.
  Rationale: The point of the new boundary is to replace brittle shell-level assertions with boundary tests. Keeping the same behavior asserted in both places would create redundant maintenance burden without increasing confidence.
  Date/Author: 2026-05-22 / Codex

## Outcomes & Retrospective

This slice is now implemented. Canonical preview lifecycle ownership moved into `src/foliaseal/presentation/qt/signature_preview_lifecycle.py`, which now owns canonical render invocation, `QtPdfRenderBackend` reuse, pixmap loading, snapshot replacement/cleanup, and explicit disposal of the active snapshot on widget teardown.

The shell is narrower but intentionally not fully decomposed. `SignaturePropertiesPanel` still owns preview controls, preview geometry helpers, and the final UI rendering/layout handoff, but it no longer owns the stateful canonical snapshot lifecycle. That reduced white-box pressure in `tests/unit/test_qt_signing_shell.py` and moved the brittle cleanup/reuse semantics into dedicated boundary tests.

The compliance review surfaced one real defect: closing the shell root widget did not dispose the active preview snapshot after the first refactor pass. Wiring widget-destruction cleanup and adding direct disposal tests closed that gap before commit.

## Context and Orientation

The signing UI still lives in `src/foliaseal/presentation/qt/signing_shell.py`. `SignaturePropertiesPanel` still owns the preview card UI, including textual preview labels, image-stamp placement, preview geometry helpers, and the final handoff of render state into the single-line or multi-line card. The panel uses `DefaultSignaturePropertiesCoordinator` for certificate/preset reconciliation and now delegates canonical preview lifecycle work to `src/foliaseal/presentation/qt/signature_preview_lifecycle.py`.

The draft state source remains `src/foliaseal/application/signing_draft_workflow.py`. The panel asks the coordinator for a `SigningDraftPreview`, then uses that preview to drive both the textual preview controls and canonical preview rendering. The canonical snapshot renderer itself is defined in `src/foliaseal/application/signing_preview_renderer.py` as `render_canonical_signature_preview()`, which returns `CanonicalSignaturePreviewSnapshot`. That snapshot points at a temporary PNG file and includes structural bounds metadata used elsewhere in tests and evidence.

The new lifecycle module owns a reusable `QtPdfRenderBackend` instance and the active `_current_snapshot`. `QtCanonicalPreviewLifecycle.refresh()` renders a new canonical snapshot, cleans up the prior snapshot directory when appropriate, loads a Qt pixmap through the widget bindings, and returns widget-facing render state. `dispose()` now cleans up any remaining snapshot when the panel or shell root widget is destroyed.

The main lifecycle assertions now live in `tests/unit/test_signature_preview_lifecycle.py`. Those tests assert that canonical preview rendering uses `include_border=True` and `flatten_to_white=False`, that replaced snapshots are cleaned up, that repeated refreshes keep only the latest snapshot directory, that one render backend is reused across refreshes, that `dispose()` cleans up the final snapshot, and that the lifecycle falls back cleanly when canonical rendering is unavailable. `tests/unit/test_qt_signing_shell.py` now keeps thinner shell-level checks for card chrome, scaled pixmap sizing, snapshot discoverability, and root-widget teardown cleanup.

The architecture document in `docs/ARCHITECTURE.md` now records the implemented split: preview lifecycle responsibilities live behind `signature_preview_lifecycle.py`, while preview geometry helpers and final UI rendering remain in `signing_shell.py`.

## Plan of Work

This slice is complete. `src/foliaseal/presentation/qt/signature_preview_lifecycle.py` defines `CanonicalPreviewRenderState` plus `QtCanonicalPreviewLifecycle`, which owns canonical render invocation, `QtPdfRenderBackend` reuse, pixmap loading, snapshot replacement/cleanup, and explicit disposal. `SignaturePropertiesPanel` now calls that boundary, stores the current snapshot on the card container for shell compatibility, and renders the returned state into the existing preview surfaces while keeping preview geometry helpers local.

The tests are now split across two layers. `tests/unit/test_signature_preview_lifecycle.py` covers the lifecycle boundary directly without a full shell widget. `tests/unit/test_qt_signing_shell.py` remains a thinner shell seam that proves the lifecycle result still lands correctly in the card UI and that widget teardown triggers cleanup.

The documentation step is also complete: `docs/ARCHITECTURE.md`, this ExecPlan, and the earlier coordinator ExecPlan now match the implemented boundary split.

## Concrete Steps

The completed steps for this slice were:

1. Add `tests/unit/test_signature_preview_lifecycle.py` first and pin the lifecycle contract outside the shell.
2. Introduce `src/foliaseal/presentation/qt/signature_preview_lifecycle.py` with `CanonicalPreviewRenderState` and `QtCanonicalPreviewLifecycle`.
3. Rewire `SignaturePropertiesPanel` to use the lifecycle boundary instead of directly rendering/replacing/loading canonical snapshots.
4. Trim shell-level lifecycle duplication and keep only the thin card-integration assertions in `tests/unit/test_qt_signing_shell.py`.
5. Run focused validation, perform the required compliance review, then close the teardown-cleanup finding and update the supporting documentation.

## Validation and Acceptance

Acceptance for this slice is behavioral, not structural.

The new lifecycle tests must prove that the extracted boundary preserves the canonical render contract: it renders with `include_border=True` and `flatten_to_white=False`, reuses one render backend across refreshes, cleans up replaced snapshot directories, keeps only the latest snapshot after repeated refreshes, and falls back cleanly when canonical rendering cannot produce a snapshot.

The shell tests must still prove that the signing shell preview card integrates the lifecycle output correctly. In particular, when a canonical preview is active the outer card chrome should be suppressed, the render label/body should size to the scaled pixmap, and the current snapshot should remain discoverable where the shell expects it.

Focused validation for the completed slice passed with:

    pytest tests/unit/test_signature_preview_lifecycle.py tests/unit/test_qt_signing_shell.py
    77 passed in 12.13s

    ruff check src/foliaseal/presentation/qt/signature_preview_lifecycle.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_signature_preview_lifecycle.py tests/unit/test_qt_signing_shell.py
    All checks passed!

    git diff --check
    <no output>

## Idempotence and Recovery

This refactor is safe to repeat because the lifecycle extraction can be introduced additively: add the new module and tests, wire the shell to call it, then trim redundant shell tests. If the shell preview breaks during rewiring, restore the previous direct call path for canonical rendering, keep the lifecycle tests, and move one responsibility at a time into the new boundary until the tests pass again.

If the lifecycle tests start depending on full Qt widget trees, reduce them back to binding-level fakes and move any purely widget-composition assertion to the shell smoke tests. If a snapshot cleanup failure leaves temporary directories behind during test development, delete only the test-created `foliaseal-canonical-preview-*` directories under `tmp_path` and rerun the focused tests.

## Artifacts and Notes

Current lifecycle evidence:

    src/foliaseal/presentation/qt/signature_preview_lifecycle.py
    - QtCanonicalPreviewLifecycle owns canonical render invocation, QtPdfRenderBackend reuse, snapshot replacement/cleanup, pixmap loading, and disposal.

    src/foliaseal/presentation/qt/signing_shell.py
    - refresh_preview() loads coordinator state, updates preview widgets, and invokes the lifecycle boundary through _apply_canonical_preview_render().
    - the shell root widget and panel widget both dispose the lifecycle on destruction.

    tests/unit/test_signature_preview_lifecycle.py
    - pins render params, backend reuse, replacement cleanup, repeated-refresh retention, fallback for both invalid previews and unavailable Qt render backends, and dispose cleanup.

    tests/unit/test_qt_signing_shell.py
    - proves the shell still exposes the current snapshot, sizes the render label/body to the scaled pixmap, suppresses card chrome when canonical preview is active, and cleans up the active snapshot on widget close.

## Interfaces and Dependencies

The preview-lifecycle boundary now lives in `src/foliaseal/presentation/qt/signature_preview_lifecycle.py` with this widget-facing contract:

    @dataclass(frozen=True)
    class CanonicalPreviewRenderState:
        snapshot: CanonicalSignaturePreviewSnapshot | None
        pixmap: Any | None
        card_style: str
        render_label_visible: bool
        render_body_size: tuple[int, int]

    class CanonicalPreviewLifecycle:
        def refresh(
            self,
            *,
            preview: SigningDraftPreview,
            preview_scale: float,
            inner_body_width: int,
            inner_body_height: int,
        ) -> CanonicalPreviewRenderState: ...

        def current_snapshot(self) -> CanonicalSignaturePreviewSnapshot | None: ...

        def dispose(self) -> None: ...

The concrete implementation uses `render_canonical_signature_preview()` from `src/foliaseal/application/signing_preview_renderer.py`, holds one reusable `QtPdfRenderBackend`, loads the Qt pixmap through the existing binding object, and owns cleanup of temporary `foliaseal-canonical-preview-*` directories when replacing or disposing a snapshot. `SignaturePropertiesPanel` remains responsible for `_preview_*` geometry helpers, text/stamp placement, and choosing whether to attach the render result to the single-line or multi-line preview surface.

Change note: 2026-05-22 / Codex

This ExecPlan now records the completed preview-lifecycle slice after the coordinator boundary. The implementation extracted canonical preview lifecycle management into a dedicated presentation-layer module, added direct lifecycle tests, preserved the existing preview card behavior, and closed the teardown-cleanup gap found during compliance review.
