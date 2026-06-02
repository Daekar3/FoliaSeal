# Introduce Ordered Workspace Interaction Effects

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

This slice replaced the workspace-interaction flag bag with one explicit ordered effect plan. `WorkspaceInteractionSession` now returns `WorkspaceInteractionPlan`, and `SigningWorkspaceWidget` executes those ordered effects as a thin shell adapter. The visible behavior stayed the same: viewer selection still routes to review/text selection first and signature placement second, page changes still refresh navigation and invalidate signing readiness, and viewer refreshes still resync placement context, overlay, preview, and signing-action state.

The user-facing proof is behavior preservation. The focused interaction and shell tests should continue to pass, while new boundary tests should assert the explicit effect order directly instead of inspecting boolean fields on a transition object.

## Child ExecPlan Dependencies

- [x] (2026-06-01 00:00Z) No child ExecPlans are required for this narrow refactor slice.

## Progress

- [x] (2026-06-01 00:00Z) Dev-loop explorer selected the first hybrid `1+4` slice: replace the workspace-interaction flag bag with an ordered effect plan and make the shell a thin executor.
- [x] (2026-06-01 00:00Z) Wrote this ExecPlan before implementation.
- [x] (2026-06-01 00:18Z) Replaced `WorkspaceInteractionTransition` with `WorkspaceInteractionPlan` plus an explicit ordered effect vocabulary in `src/foliaseal/application/workspace_interaction_session.py`.
- [x] (2026-06-01 00:23Z) Rewired `src/foliaseal/presentation/qt/signing_shell.py` so the shell now executes ordered interaction effects instead of branching on transition flags.
- [x] (2026-06-01 00:28Z) Updated `tests/unit/test_workspace_interaction_session.py` and `tests/unit/test_qt_signing_shell.py` to assert explicit effect order and thin shell execution.
- [x] (2026-06-01 00:33Z) Completed focused validation: `pytest tests/unit/test_workspace_interaction_session.py tests/unit/test_qt_signing_shell.py tests/unit/test_document_review_workspace.py tests/unit/test_qt_signing_action_boundary.py`, `ruff check ...`, and `git diff --check` all passed.
- [x] (2026-06-01 00:40Z) Completed the required compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this execplan; the implementation matched and only architecture wording needed reconciliation.

## Surprises & Discoveries

- Observation: page-change and navigation-refresh flows cannot safely precompute the refreshed placement context as payload data, because the viewer refresh needs to happen first for the shell-side snapshot to be current.
  Evidence: `ViewerInteractionSession.current_placement_context()` derives from `ViewerWorkflow.snapshot`, while the existing shell order refreshes the viewer before refreshing the current placement context. That forced the ordered plan to include an explicit `RefreshCurrentPlacementContext` effect instead of only payload-carrying `ApplyPlacementContext`.

- Observation: the shell test surface is much easier to validate through effect execution order than through private shell-instance state.
  Evidence: a focused shell test could assert `refresh -> placement -> overlay -> preview -> signing` by patching the exposed viewer widget and boundary classes, without needing direct access to `SigningWorkspaceWidget`.

- Observation: the compliance review found implementation behavior aligned with `docs/SPEC.md` and this execplan, and the only stale artifact was `docs/ARCHITECTURE.md`.
  Evidence: the ordered-effects boundary and shell execution model matched the slice description; no implementation correction was required.

## Decision Log

- Decision: keep the existing public method verbs on `WorkspaceInteractionSession` for this slice.
  Rationale: the seam to deepen is the returned shape and the shell replay logic, not the caller vocabulary. `select_in_viewer()`, `change_page()`, `refresh_navigation_to_page_index()`, `refresh_after_panel_change()`, and `refresh_after_viewer_refresh()` are already stable and narrow enough for the first step.
  Date/Author: 2026-06-01 / Codex

- Decision: do not widen this slice into review/text or signing-action policy changes.
  Rationale: `DocumentReviewWorkspaceSession` and `SigningActionBoundary` already own their respective policies. This slice should only remove the shell’s transition-replay ownership.
  Date/Author: 2026-06-01 / Codex

## Outcomes & Retrospective

Implementation and compliance review are complete. The ordered-effects boundary is implemented, the shell executes the explicit plan, and `docs/ARCHITECTURE.md` now matches the current ownership split.

## Context and Orientation

The current interaction seam is split between `src/foliaseal/application/workspace_interaction_session.py` and `src/foliaseal/presentation/qt/signing_shell.py`. The session is Qt-free and returns `WorkspaceInteractionPlan`, an ordered effect plan containing explicit follow-up actions such as review-transition application, viewer refresh, placement-context application, signature-rectangle application, overlay sync, preview refresh, signing-action reload, signing-action invalidation, and error emission.

The shell executes those effects in order inside its workspace-interaction executor. That method decides when to:

- apply a `DocumentReviewWorkspaceTransition`
- emit an error
- refresh the viewer, optionally with navigation
- apply either the current placement context or an explicit placement context
- update the signature rectangle through a non-notifying panel path
- sync the signature overlay
- refresh the preview
- reload signing-action state or invalidate it

The split is explicit: the session decides which effects are required, and the shell executes them in order. The tests show the seam clearly: `tests/unit/test_workspace_interaction_session.py` asserts ordered effect plans, while `tests/unit/test_qt_signing_shell.py` spies on session entrypoints and verifies that the shell executes the plan correctly.

This slice now uses one explicit ordered effect plan. The application boundary surfaces the follow-up actions as a small ordered vocabulary of effects, and the shell executes them in order without re-deriving the choreography itself.

Relevant files for this slice are:

- `src/foliaseal/application/workspace_interaction_session.py`
- `src/foliaseal/presentation/qt/signing_shell.py`
- `tests/unit/test_workspace_interaction_session.py`
- `tests/unit/test_qt_signing_shell.py`
- `docs/ARCHITECTURE.md`

Files that must not be widened into this slice:

- `src/foliaseal/application/document_review_workspace.py`
- `src/foliaseal/presentation/qt/signing_action_boundary.py`
- `src/foliaseal/presentation/qt/app_frame.py`
- certificate lifecycle modules
- Phase 3 harness/reporting modules

The primary change class is behavior-preserving architecture refactor. Documentation/status updates are allowed only to record the new ordered-effect ownership split accurately.

## Plan of Work

First, replace `WorkspaceInteractionTransition` in `src/foliaseal/application/workspace_interaction_session.py` with a small explicit ordered-effect model. The new model should keep the current session method names, but each method should return one plan object whose main content is an ordered tuple of explicit effect variants. The effect vocabulary should stay narrow and concrete. It should cover review transition application, viewer refresh, placement-context application, signature-rectangle application, overlay sync, preview refresh, signing-action reload, signing-action invalidation, and error emission. Avoid a giant generic dictionary or stringly typed effect bus.

Second, rewire `src/foliaseal/presentation/qt/signing_shell.py`. Rename or replace `_apply_workspace_interaction_transition(...)` with an executor that iterates the ordered effects and applies them. The shell should no longer inspect boolean transition fields. It should only know how to execute each effect against the viewer widget, properties panel, draft workflow, document-review renderer, and signing-action boundary.

Third, update `tests/unit/test_workspace_interaction_session.py` so the direct boundary tests assert effect order and effect payloads instead of asserting boolean fields on a transition object. Keep the existing behavior scenarios: review-transition consumption, signature-placement fallback, page change, navigation error, panel change, and viewer refresh. Update `tests/unit/test_qt_signing_shell.py` only enough to keep shell coverage thin and focused on delegation plus effect execution outcomes.

Finally, update `docs/ARCHITECTURE.md` to describe the ordered-effect plan and the thinner shell adapter, then run the required compliance review before the documentation worker and commit worker steps required by `dev-loop`.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Edit these files:

    src/foliaseal/application/workspace_interaction_session.py
    src/foliaseal/presentation/qt/signing_shell.py
    tests/unit/test_workspace_interaction_session.py
    tests/unit/test_qt_signing_shell.py
    docs/ARCHITECTURE.md
    docs/ExecPlans/workspace_interaction_ordered_effects_execplan.md

Run focused validation as the slice progresses:

    pytest tests/unit/test_workspace_interaction_session.py tests/unit/test_qt_signing_shell.py tests/unit/test_document_review_workspace.py tests/unit/test_qt_signing_action_boundary.py
    ruff check src/foliaseal/application/workspace_interaction_session.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_workspace_interaction_session.py tests/unit/test_qt_signing_shell.py tests/unit/test_document_review_workspace.py tests/unit/test_qt_signing_action_boundary.py
    git diff --check

After the first pass implementation, run the required compliance review against at least:

    docs/ARCHITECTURE.md
    docs/SPEC.md
    docs/ExecPlans/workspace_interaction_ordered_effects_execplan.md

## Validation and Acceptance

This slice is accepted when all of the following are true:

- `WorkspaceInteractionSession` returns an explicit ordered effect plan instead of a boolean fan-out object
- the shell executes those ordered effects without re-deriving the choreography from flag fields
- review-transition consumption and error short-circuit behavior remain intact
- page-change, panel-change, viewer-refresh, and viewer-selection follow-up still produce the same observable widget behavior
- direct interaction-session tests assert ordered effects
- focused shell tests still pass
- `docs/ARCHITECTURE.md` accurately describes the new ownership split

Observable proof is a focused test run where the interaction-session tests show the new effect order directly and the shell tests still pass for viewer selection, page changes, panel changes, and viewer refresh.

## Idempotence and Recovery

This is a behavior-preserving refactor in local application and Qt presentation code. It is safe to retry. If the first pass leaves both the old transition fields and the new effect plan active, remove the duplicate path before retrying; do not keep parallel orchestration models longer than one local debugging cycle. If a test reveals that the effect vocabulary is too generic, split the ambiguous effect into two explicit variants rather than reintroducing shell-side branching.

## Artifacts and Notes

Important evidence to capture during implementation:

- the failing interaction-session test before the ordered plan exists
- the passing focused pytest run after wiring is complete
- any compliance finding that requires architecture-doc reconciliation

Keep the artifacts concise and update this section if an unexpected effect-order issue changes the plan.

## Interfaces and Dependencies

This slice uses the `In-process` dependency category. All collaborators are local Python modules and fake Qt surfaces in tests.

At the end of the slice, the interaction seam should look approximately like:

    @dataclass(frozen=True)
    class WorkspaceInteractionPlan:
        effects: tuple[WorkspaceInteractionEffect, ...]

    @dataclass(frozen=True)
    class ApplyReviewTransition:
        transition: DocumentReviewWorkspaceTransition

    @dataclass(frozen=True)
    class RefreshViewer:
        navigation: bool = False

    @dataclass(frozen=True)
    class ApplyPlacementContext:
        placement_context: SignaturePlacementContext | None

    @dataclass(frozen=True)
    class SetSignatureRect:
        signature_rect: SignatureRect
        notify: bool = False

    @dataclass(frozen=True)
    class SyncSignatureOverlay:
        pass

    @dataclass(frozen=True)
    class RefreshPreview:
        pass

    @dataclass(frozen=True)
    class ReloadSigningActionState:
        pass

    @dataclass(frozen=True)
    class InvalidateSigningAction:
        reason: str

    @dataclass(frozen=True)
    class EmitInteractionError:
        message: str

The exact names can shift, but the core requirement must remain: the application boundary owns the ordered effect plan, and the shell only executes those effects.

Revision note: Created on 2026-06-01 by Codex after the `dev-loop` explorer selected the first ordered-effects slice for the workspace-interaction hybrid.

Revision note: Updated on 2026-06-01 by Codex after the first implementation pass to record the new ordered-effect vocabulary, focused validation results, and the discovery that refreshed placement context must remain an explicit effect rather than a precomputed payload.
