# Extract The Signing Workspace Interaction Bridge

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

This slice will keep `WorkspaceInteractionSession` and the public shell behavior unchanged while removing the last large workspace-interaction effect switch from `SigningWorkspaceWidget`. A new shell-local helper will own workspace-interaction plan execution so the shell asks for a `WorkspaceInteractionPlan` and delegates the effect application.

That preserves behavior while continuing the same `4+5` hybrid direction: a narrow shell-owned outer port with thinner Qt adapters over deeper helper boundaries.

## Child ExecPlan Dependencies

- [x] (2026-06-04 22:33Z) No child ExecPlans are required for this bounded shell-internal extraction slice.

## Progress

- [x] (2026-06-04 22:33Z) Completed the required `explorer-light` audit and fixed the next slice to extracting the workspace-interaction plan executor rather than reopening setup, signing action, or app-frame seams.
- [x] (2026-06-04 22:34Z) Re-read the workspace-interaction execution branch in `src/foliaseal/presentation/qt/signing_shell.py`, the shell-control-flow section in `docs/ARCHITECTURE.md`, and the recent signing-workspace ExecPlans for continuity.
- [x] (2026-06-04 22:44Z) Added `src/foliaseal/presentation/qt/signing_workspace_interaction_bridge.py` and moved workspace-interaction plan execution out of `SigningWorkspaceWidget` into `SigningWorkspaceInteractionBridge`.
- [x] (2026-06-04 22:45Z) Updated focused shell tests and added a refresh-error regression covering interaction-bridge error routing.
- [x] (2026-06-04 22:46Z) Ran focused validation with `pytest tests/unit/test_workspace_interaction_session.py tests/unit/test_qt_signing_shell.py`, `ruff check`, and `git diff --check`; all passed.
- [x] (2026-06-04 22:52Z) Ran the architectural compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this ExecPlan; reconciled the stale architecture wording and confirmed no SPEC or README update was needed.
- [x] (2026-06-04 22:52Z) Updated documentation to final state.

## Surprises & Discoveries

- Observation: the interaction bridge must resolve some collaborators lazily instead of capturing every bound method at construction time.
  Evidence: the focused shell suite monkeypatches `widget.properties_panel.refresh_preview` after shell construction; using a constructor-captured bound method skipped that patch until the bridge callback was changed to call the live attribute at execution time.

## Decision Log

- Decision: keep `WorkspaceInteractionSession` unchanged in this slice.
  Rationale: the application boundary already returns ordered effects; the remaining concentration is the Qt-facing effect execution branch in `signing_shell.py`.
  Date/Author: 2026-06-04 / Codex

- Decision: extract a shell-local interaction bridge rather than widening `SigningWorkspaceReviewBridge`.
  Rationale: review/text state application is already one coherent concept; the remaining executor also owns viewer refresh, placement context, signature-rect application, overlay sync, preview refresh, and signing-action follow-up, which is broader than review/text alone.
  Date/Author: 2026-06-04 / Codex

## Outcomes & Retrospective

The slice landed as intended: `SigningWorkspaceWidget` now delegates workspace-interaction plan execution to `SigningWorkspaceInteractionBridge`, and the bridge owns the ordered `WorkspaceInteractionPlan.effects` application against the live viewer, panel, sidebar, review bridge, and signing-action boundary. `WorkspaceInteractionSession` stayed unchanged, and the public shell behavior remained stable.

Validation completed successfully with:

- `pytest tests/unit/test_workspace_interaction_session.py tests/unit/test_qt_signing_shell.py`
- `ruff check`
- `git diff --check`

The compliance review found one stale documentation claim in `docs/ARCHITECTURE.md` stating that `signing_shell.py` still executed the interaction plan directly. That was corrected to name `signing_workspace_interaction_bridge.py` as the executor and describe the shell as delegating to it. The review did not require any changes to `docs/SPEC.md` or `README.md`.

Retrospective: this bridge extraction finished the remaining shell-local effect-execution seam without changing the interaction vocabulary. The shell boundary is now thinner and the plan-execution ownership is explicit in the architecture doc.

## Context and Orientation

`src/foliaseal/presentation/qt/signing_shell.py` is still the composition root for the interactive signing workspace. Recent slices already moved several clusters out of the shell:

- `src/foliaseal/presentation/qt/signing_shell_port.py` owns the outer workspace bootstrap/port/factory seam used by the app frame.
- `src/foliaseal/presentation/qt/signing_workspace_sidebar.py` owns the grouped sidebar surface and sidebar render paths.
- `src/foliaseal/presentation/qt/signing_workspace_review_bridge.py` owns review/text bridge state and transition application.
- `src/foliaseal/application/workspace_interaction_session.py` owns the ordered `WorkspaceInteractionPlan` effect choreography.

The shell still directly executes the plan effects by branching over each effect type. That code is coherent together and is the next remaining shell-internal interaction cluster.

The files that matter for this slice are:

- `src/foliaseal/presentation/qt/signing_shell.py`, which currently applies each workspace-interaction effect directly.
- `src/foliaseal/presentation/qt/signing_workspace_review_bridge.py`, which already owns the review/text effect branch used by one of those effects.
- `src/foliaseal/application/workspace_interaction_session.py`, which must stay unchanged and continue to emit the same effect objects.
- `tests/unit/test_qt_signing_shell.py`, which guards public shell behavior for viewer selection, page changes, and interaction follow-up.
- `docs/ARCHITECTURE.md`, which currently documents the shell as the executor of the interaction plan.

In this plan, an “interaction bridge” means the Qt-facing helper that executes `WorkspaceInteractionPlan.effects` against the live viewer, panel, sidebar, review bridge, and signing-action boundary.

## Plan of Work

First, add a new internal helper module under `src/foliaseal/presentation/qt/` for workspace-interaction plan execution. The helper should accept the live collaborators needed to execute the existing effects in order without reaching back through the whole shell object.

Second, edit `src/foliaseal/presentation/qt/signing_shell.py` so it constructs that helper and delegates `_apply_workspace_interaction_plan(...)` and effect execution to it. The public shell verbs and all surrounding behavior should stay unchanged.

Third, update focused shell tests. Keep the public entrypoint tests around viewer selection and panel/view refresh behavior, and add or adjust a focused proof that the effect ordering still results in the expected visible behavior.

Finally, run focused validation, perform the required compliance review, update any stale docs, and record the final result here.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Add the internal interaction bridge helper and migrate the shell.

       apply_patch ... on src/foliaseal/presentation/qt/<new helper>.py
       apply_patch ... on src/foliaseal/presentation/qt/signing_shell.py

2. Update focused shell tests.

       apply_patch ... on tests/unit/test_qt_signing_shell.py

3. Run focused validation.

       pytest tests/unit/test_workspace_interaction_session.py tests/unit/test_qt_signing_shell.py
       ruff check src/foliaseal/presentation/qt/<new helper>.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py
       git diff --check

4. Run the required compliance review, reconcile docs if needed, and commit the slice.

## Validation and Acceptance

This slice is accepted when all of the following are true:

- a dedicated internal helper owns the workspace-interaction plan execution logic that used to live directly in `SigningWorkspaceWidget`
- the shell still behaves the same for ordered effect execution, including review-transition application, viewer refresh, placement-context updates, signature-rectangle application, overlay sync, preview refresh, signing-action reload/invalidation, and error emission
- `WorkspaceInteractionSession` remains unchanged and still emits the same ordered effect objects
- focused shell tests prove the effect order still holds through the public shell entrypoints
- `docs/ARCHITECTURE.md` accurately describes the new helper ownership and shell split

Run:

    pytest tests/unit/test_workspace_interaction_session.py tests/unit/test_qt_signing_shell.py

Then run:

    ruff check src/foliaseal/presentation/qt/<new helper>.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py
    git diff --check

Acceptance is behavioral. No GUI flow or text is intended to change.

## Idempotence and Recovery

This is a behavior-preserving extraction. It is safe to retry. If the helper extraction causes confusing ownership of one specific effect, keep that collaborator explicit instead of expanding the helper into a new shell superclass. Do not recover by duplicating the same effect-execution logic in both the shell and the new helper; one owner must remain at the end of the slice.

If the extraction unexpectedly requires changing the application effect vocabulary, stop and split that broader redesign into a later slice instead of widening this one.

## Artifacts and Notes

The most important evidence for this slice will be:

- a new internal helper module for workspace-interaction plan execution
- a smaller shell-side integration surface for interaction plan execution inside `src/foliaseal/presentation/qt/signing_shell.py`
- focused shell tests proving ordered-effect behavior is unchanged

## Interfaces and Dependencies

This slice uses the `In-process` dependency category.

At the end of the slice, the new helper should expose a stable internal adapter surface approximately like:

    class SigningWorkspaceInteractionBridge:
        def apply_plan(self, plan: WorkspaceInteractionPlan) -> None: ...

The helper may expose smaller internal methods for effect execution, but the shell should only need to delegate the high-level plan application. The shell continues to own the broader workspace composition role and the public shell behavior surface.

Revision note: Created on 2026-06-04 by Codex for the next shell-internal tracer bullet in the same signing-workspace hybrid `4+5` direction, after the review/text bridge slice was completed.
