# Extract Signing Action Coordinator

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the signing action and confirmation workflow will no longer live as intertwined shell methods inside `SigningWorkspaceWidget`. Instead, one local application/presentation boundary will own output-path selection state, signing submission state transitions, reopen/verify enablement, and flow-summary derivation. The Qt shell will remain a thin adapter that applies the returned state to controls and preserves the existing public widget surface.

The user-visible behavior must stay the same:

- `File > Save As...` still delegates through the shell
- overwrite confirmation still appears only for accepted overwrite candidates
- signing still returns `None` on readiness failure and a `SigningRequest` on executor paths
- successful signing still enables both `Open signed PDF` and `Verify signed PDF`
- changing placement, page, or output path still clears the previous signing result and returns the flow summary to the pre-signing state

## Child ExecPlan Dependencies

- [x] (2026-05-25 06:04Z) No child ExecPlans are required for this bounded refactor slice.

## Progress

- [x] (2026-05-25 06:03Z) Explorer pass reviewed the action/status seam and confirmed `SigningWorkspaceWidget` still owns output-path selection, sign submission, reopen state, and flow-summary policy.
- [x] (2026-05-25 06:05Z) Wrote this ExecPlan before implementation.
- [x] (2026-05-25 06:20Z) Added `src/foliaseal/presentation/qt/signing_action_coordinator.py` with `SigningActionCoordinator`, `SigningActionState`, and `SigningActionTransition`.
- [x] (2026-05-25 06:28Z) Rewired `SigningWorkspaceWidget` so output selection, sign submission, reopen logic, and flow-summary/sign-enabled state now delegate to the coordinator boundary.
- [x] (2026-05-25 06:42Z) Added direct boundary coverage in `tests/unit/test_qt_signing_action_coordinator.py` and kept shell/app-frame behavior green.
- [x] (2026-05-25 06:55Z) Completed focused validation, compliance review fixes, and documentation updates.

## Surprises & Discoveries

- Observation: the sidebar is mostly view construction; the real coupling is still in `SigningWorkspaceWidget`.
  Evidence: the explorer found `choose_output_pdf_path()`, `submit_sign_request()`, `open_signed_output()`, `_refresh_sign_button_state()`, and `_refresh_flow_summary()` all concentrated in `src/foliaseal/presentation/qt/signing_shell.py`.

- Observation: app-frame routing is already narrow enough that this slice does not need to change it.
  Evidence: `src/foliaseal/presentation/qt/app_frame.py` only delegates `Save As...` to `choose_output_pdf_path()` and passes `on_open_signed_output=self.open_pdf_path` when building the shell.

- Observation: the first implementation pass left direct boundary coverage incomplete.
  Evidence: compliance review found that `load()` and `invalidate()` state derivation were only exercised indirectly through shell tests, so targeted coordinator tests were added before closing the slice.

## Decision Log

- Decision: keep the new coordinator local to the signing shell/presentation boundary for this slice.
  Rationale: the behavior still depends on Qt-originated output-path choice and overwrite confirmation, so the first safe move is to deepen the shell seam without prematurely forcing the whole flow into the application package.
  Date/Author: 2026-05-25 / Codex

- Decision: preserve the current public shell widget methods and return values.
  Rationale: `app_frame.py` and tests already depend on `choose_output_pdf_path()`, `submit_sign_request()`, `open_signed_output()`, `last_signing_result`, and sign/reopen button behavior. This slice should deepen internals, not widen migration scope.
  Date/Author: 2026-05-25 / Codex

- Decision: let the coordinator own derived action state, not direct Qt widget mutation.
  Rationale: the goal is to replace shell-owned state policy with a deeper module whose behavior can be tested at its boundary.
  Date/Author: 2026-05-25 / Codex

## Outcomes & Retrospective

This slice is complete.

Implemented results:

- Added `src/foliaseal/presentation/qt/signing_action_coordinator.py`.
- Moved the signing action/status state machine out of shell methods and into the coordinator boundary.
- Kept `choose_output_pdf_path()`, `submit_sign_request()`, `open_signed_output()`, and the public widget attributes stable.
- Added direct coordinator tests for `load()`, `accept_output_path()`, `invalidate()`, `submit()`, and `open_signed_output()`.
- Preserved existing shell and app-frame behavior, including reopen/verify callback routing and `Save As...` delegation.

Validation evidence:

- `pytest tests/unit/test_qt_signing_action_coordinator.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py` passed.
- `ruff check src/foliaseal/presentation/qt/signing_action_coordinator.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_action_coordinator.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py` passed.
- `git diff --check` passed.

Retrospective:

- The main follow-up from compliance review was not behavioral but boundary-focused: direct coverage for `load()` and `invalidate()` was necessary because that state derivation is now a first-class responsibility of the new coordinator.
- Keeping dialog handling and callback emission in the shell while moving the action state machine into the coordinator was the right first cut. It deepened the seam without forcing app-frame or sidebar redesign into the same slice.

## Context and Orientation

Before this slice, `src/foliaseal/presentation/qt/signing_shell.py` owned the full action/status workflow around:

- choosing the signed-output path
- confirming overwrite
- clearing stale signing results after draft/output changes
- readiness gating before signing
- invoking the sign executor
- setting success/failure result text
- enabling and disabling reopen/verify actions
- deriving the flow summary stage/detail text

The Qt sidebar in `src/foliaseal/presentation/qt/signing_workspace_sidebar.py` is mainly a view-only composition layer. The app frame in `src/foliaseal/presentation/qt/app_frame.py` is mainly a caller that delegates `Save As...` and signed-output reopen behavior to the shell.

This meant one user concept, “confirm and sign this PDF,” required understanding shell methods, widget state, callbacks, and tests across multiple files. The new boundary hides that orchestration and presents one state-driven interface back to the shell.

Relevant files for this slice:

- `src/foliaseal/presentation/qt/signing_shell.py`
- `src/foliaseal/presentation/qt/signing_workspace_sidebar.py`
- `src/foliaseal/presentation/qt/app_frame.py`
- `tests/unit/test_qt_signing_shell.py`
- `tests/unit/test_qt_app_frame.py`
- `docs/ARCHITECTURE.md`

## Plan of Work

First, add a new local coordinator module for the signing action/status flow. It should own:

- output-path selection state updates after the caller provides a chosen path
- clearing prior signing results when the draft or path changes
- signing submission transitions and success/failure state
- reopen/verify enablement
- flow summary stage/detail derivation
- sign-enabled state

The coordinator should return immutable state to the shell rather than mutating Qt controls directly.

Second, rewire `SigningWorkspaceWidget` so its existing public methods become thin adapters:

- `choose_output_pdf_path()` still opens the dialog and handles overwrite confirmation, then passes the accepted path into the coordinator
- `submit_sign_request()` still returns the current public values, but delegates the internal state machine
- `open_signed_output()` becomes a thin reopen delegate over coordinator-owned state

Third, add direct tests for the new coordinator boundary and thin shell/app-frame tests where detailed state assertions become redundant.

Finally, update `docs/ARCHITECTURE.md` to reflect the new ownership split.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Edit these files:

    src/foliaseal/presentation/qt/signing_action_coordinator.py
    src/foliaseal/presentation/qt/signing_shell.py
    tests/unit/test_qt_signing_action_coordinator.py
    tests/unit/test_qt_signing_shell.py
    tests/unit/test_qt_app_frame.py
    docs/ARCHITECTURE.md
    docs/ExecPlans/signing_action_coordinator_execplan.md

Run focused validation:

    pytest tests/unit/test_qt_signing_action_coordinator.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py
    ruff check src/foliaseal/presentation/qt/signing_action_coordinator.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_action_coordinator.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py
    git diff --check

## Validation and Acceptance

This slice is accepted when all of the following are true:

- signing action/status state transitions are owned by a dedicated coordinator boundary
- `SigningWorkspaceWidget` still exposes the existing public methods and behavior
- app-frame `Save As...` and reopen callback behavior remain unchanged
- boundary tests cover the new state machine directly
- focused shell/app-frame tests pass
- `docs/ARCHITECTURE.md` accurately describes the new boundary

## Idempotence and Recovery

This slice is safe to retry because it is a behavior-preserving refactor inside local presentation code. If the shell migration becomes unstable, keep the new coordinator file and move one public method at a time back to the old shell logic until tests are green, then reattempt the migration in smaller commits. Do not widen this slice into sidebar redesign or app-frame workflow changes.

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

The intended end-state is a local state boundary shaped approximately like:

    @dataclass(frozen=True)
    class SigningActionState:
        can_sign: bool
        stage_text: str
        detail_text: str
        result_text: str
        result_kind: str
        last_successful_output_path: str | None
        last_signing_result: SigningResult | None
        can_open_signed_output: bool

    class SigningActionCoordinator:
        def load(self) -> SigningActionState: ...
        def accept_output_path(self, selected_path: str) -> SigningActionState: ...
        def invalidate(self, reason: str) -> SigningActionState: ...
        def submit(self) -> tuple[SigningRequest | None, SigningActionState]: ...
        def open_signed_output(self) -> str | None: ...

The exact type names can shift during implementation, but the coordinator must own the state machine while the shell remains a renderer and dialog/callback adapter.

Revision note: Created on 2026-05-25 by Codex after the `dev-loop` explorer pass identified the signing action/status seam as the smallest safe next deepening slice.
