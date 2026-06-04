# Extract The Signing Workspace Action Bridge

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

This slice will keep the current signing workflow behavior unchanged while moving the remaining shell-facing signing-action glue out of `SigningWorkspaceWidget`. A new `SigningWorkspaceActionBridge` will own output-path selection/overwrite confirmation, sign submission state application, reopen forwarding, certificate-refresh signing-state reload, and the related state-apply/reset helpers.

That continues the same `4+5` hybrid direction: a narrow shell-owned port at the edge with thinner Qt adapters over deeper helper boundaries.

## Child ExecPlan Dependencies

- [x] (2026-06-04 23:04Z) No child ExecPlans are required for this bounded shell-internal extraction slice.

## Progress

- [x] (2026-06-04 23:04Z) Completed the required `explorer-light` audit and fixed the next slice to extracting the remaining shell-facing signing-action glue rather than reopening app-frame, certificate-management, or setup policy seams.
- [x] (2026-06-04 23:05Z) Re-read the signing-action/public-shell cluster in `src/foliaseal/presentation/qt/signing_shell.py`, the architecture debt note in `docs/ARCHITECTURE.md`, and the focused shell tests around output-path selection, sign submission, reopen, and certificate-refresh behavior.
- [x] (2026-06-04 23:12Z) Added `src/foliaseal/presentation/qt/signing_workspace_action_bridge.py` and moved shell-facing signing-action glue out of `SigningWorkspaceWidget` into `SigningWorkspaceActionBridge`.
- [x] (2026-06-04 23:13Z) Updated focused shell tests and added a dialog-cancel regression covering unchanged output-path state when the save dialog returns an empty result.
- [x] (2026-06-04 23:14Z) Ran focused validation with the shell subset, the signing-action boundary/coordinator tests, `ruff check`, and `git diff --check`; all passed.
- [x] (2026-06-04 23:20Z) Ran the architectural compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this ExecPlan; reconciled the remaining ownership wording in `docs/ARCHITECTURE.md`.
- [x] (2026-06-04 23:20Z) Updated documentation to final state.

## Surprises & Discoveries

- Observation: the remaining shell-facing signing-action cluster was already a coherent adapter seam around `SigningActionBoundary`.
  Evidence: `choose_output_pdf_path()`, `submit_sign_request()`, `open_signed_output()`, and `refresh_certificate_configurations()` all shared the same responsibilities: Qt dialog/callback behavior plus applying returned `SigningActionState` into the live shell widgets.

- Compliance review finding: `docs/ARCHITECTURE.md` still described the shell and `SigningActionBoundary` as owning the shell-facing dialog/action glue after the bridge extraction had landed.
  Resolution: updated `docs/ARCHITECTURE.md` so `signing_workspace_action_bridge.py` now owns output-path dialog handling, overwrite confirmation, sign-submit state application, signed-output reopen forwarding, and certificate-refresh signing-state reload, while `SigningActionBoundary` is narrowed to the policy boundary beneath it.

## Decision Log

- Decision: keep `SigningActionBoundary` and `SigningActionCoordinator` unchanged in this slice.
  Rationale: the remaining concentration is shell-local dialog/callback/state glue, not the existing signing-action policy boundary.
  Date/Author: 2026-06-04 / Codex

- Decision: extract a dedicated action bridge instead of folding the behavior into `SigningWorkspaceInteractionBridge`.
  Rationale: the action cluster is about output-path dialogs, sign submission, reopen, and signed-state refresh, which is separate from ordered interaction-plan execution.
  Date/Author: 2026-06-04 / Codex

## Outcomes & Retrospective

The slice is complete. `SigningWorkspaceActionBridge` now owns the remaining shell-facing signing-action glue, including output-path dialog handling, overwrite confirmation, sign-submit state application, signed-output reopen forwarding, and certificate-refresh signing-state reload. `SigningActionBoundary` remains in place as the narrower policy boundary under the bridge, and `SigningActionCoordinator` still owns the state machine.

Validation for the implementation slice already passed before this doc-only reconciliation: the focused shell subset, `tests/unit/test_qt_signing_action_boundary.py`, `tests/unit/test_qt_signing_action_coordinator.py`, `ruff check`, and `git diff --check` all passed.

The compliance review found one stale architecture sentence that still attributed the dialog/action glue to the shell/boundary pair. That wording is now corrected, and `docs/SPEC.md` did not require changes for this slice.

## Context and Orientation

`src/foliaseal/presentation/qt/signing_shell.py` is still the composition root for the interactive signing workspace. Recent slices already moved several clusters out of the shell:

- `src/foliaseal/presentation/qt/signing_shell_port.py` owns the outer workspace bootstrap/port/factory seam used by the app frame.
- `src/foliaseal/presentation/qt/signing_workspace_sidebar.py` owns the grouped sidebar surface and sidebar render paths.
- `src/foliaseal/presentation/qt/signing_workspace_review_bridge.py` owns review/text bridge state and transition application.
- `src/foliaseal/presentation/qt/signing_workspace_interaction_bridge.py` owns `WorkspaceInteractionPlan` execution.

The shell still directly owns the public signing-action verbs and the small surrounding state glue:

- `choose_output_pdf_path()`
- `submit_sign_request()`
- `open_signed_output()`
- `refresh_certificate_configurations()`
- the related signing-state apply/reset helpers

Those methods form the next coherent shell-local action cluster.

The files that matter for this slice are:

- `src/foliaseal/presentation/qt/signing_shell.py`, which currently owns the shell-facing signing-action glue.
- `src/foliaseal/presentation/qt/signing_action_boundary.py`, which already owns the narrower signing-action policy boundary and must stay unchanged here.
- `src/foliaseal/presentation/qt/signing_action_coordinator.py`, which already owns the signing-action state machine and must stay unchanged here.
- `tests/unit/test_qt_signing_shell.py`, which guards output-path, sign-submit, reopen, and certificate-refresh behavior through the public shell entrypoints.
- `docs/ARCHITECTURE.md`, which will need to describe the new action bridge if the extraction lands.

In this plan, an “action bridge” means the shell-local Qt-facing helper that executes output-path dialog/confirmation behavior, delegates to `SigningActionBoundary`, and applies the returned signing state into the live shell widgets.

## Plan of Work

First, add a new internal helper module under `src/foliaseal/presentation/qt/` for shell-facing signing-action glue. The helper should accept the live collaborators needed for output-path dialogs, overwrite confirmation, state application, sign submission, reopen forwarding, and certificate-refresh reload without reaching back through the whole shell object.

Second, edit `src/foliaseal/presentation/qt/signing_shell.py` so it constructs that helper and delegates the public signing-action verbs and nearby state helpers to it. The public shell behavior surface should stay unchanged.

Third, update focused shell tests. Keep the public entrypoint tests around output-path selection, sign submission, reopen, and certificate-refresh behavior, and add or adjust at least one proof that the new bridge preserves a non-happy-path behavior such as refresh-error/cancel or post-refresh signed-state reapplication.

Finally, run focused validation, perform the required compliance review, update any stale docs, and record the final result here.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Add the internal action bridge helper and migrate the shell.

       apply_patch ... on src/foliaseal/presentation/qt/<new helper>.py
       apply_patch ... on src/foliaseal/presentation/qt/signing_shell.py

2. Update focused shell tests.

       apply_patch ... on tests/unit/test_qt_signing_shell.py

3. Run focused validation.

       pytest tests/unit/test_qt_signing_shell.py -k 'choose_output_pdf_path or submit_sign_request or open_signed_output or refresh_certificate_configurations'
       pytest tests/unit/test_qt_signing_action_boundary.py tests/unit/test_qt_signing_action_coordinator.py
       ruff check src/foliaseal/presentation/qt/<new helper>.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py
       git diff --check

4. Run the required compliance review, reconcile docs if needed, and commit the slice.

## Validation and Acceptance

This slice is accepted when all of the following are true:

- a dedicated internal helper owns the remaining shell-facing signing-action glue that used to live directly in `SigningWorkspaceWidget`
- output-path selection, overwrite confirmation, sign submission, signed-output reopen, and certificate-refresh signing-state reload still behave the same
- `SigningActionBoundary` and `SigningActionCoordinator` remain unchanged and continue to own the same policy/state-machine responsibilities
- focused shell tests prove the shell entrypoints still preserve cancel/error/post-success behavior
- `docs/ARCHITECTURE.md` accurately describes the new action-bridge ownership and shell split

Run:

    pytest tests/unit/test_qt_signing_shell.py -k 'choose_output_pdf_path or submit_sign_request or open_signed_output or refresh_certificate_configurations'
    pytest tests/unit/test_qt_signing_action_boundary.py tests/unit/test_qt_signing_action_coordinator.py

Then run:

    ruff check src/foliaseal/presentation/qt/<new helper>.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py
    git diff --check

Acceptance is behavioral. No GUI flow or text is intended to change.

## Idempotence and Recovery

This is a behavior-preserving extraction. It is safe to retry. If the helper extraction causes confusing ownership of dialog behavior versus state application, keep the collaborator callbacks explicit rather than pulling more shell responsibilities into the helper. Do not recover by duplicating the same signing-action glue in both the shell and the new helper; one owner must remain at the end of the slice.

If the extraction unexpectedly requires changing `SigningActionBoundary` or `SigningActionCoordinator` semantics, stop and split that broader redesign into a later slice instead of widening this one.

## Artifacts and Notes

The most important evidence for this slice will be:

- a new internal helper module for shell-facing signing-action glue
- a smaller shell-side integration surface for sign/output-path/reopen behavior inside `src/foliaseal/presentation/qt/signing_shell.py`
- focused shell tests proving output-path, reopen, and signed-state refresh behavior are unchanged

## Interfaces and Dependencies

This slice uses the `In-process` dependency category.

At the end of the slice, the new helper should expose a stable internal adapter surface approximately like:

    class SigningWorkspaceActionBridge:
        def choose_output_pdf_path(self) -> str | None: ...
        def submit_sign_request(self) -> SigningRequest | None: ...
        def open_signed_output(self) -> str | None: ...
        def refresh_certificate_configurations(self) -> CertificateCatalog: ...

The helper may expose smaller internal methods for signing-state application and overwrite confirmation, but the shell should only need to delegate the high-level action behavior. The shell continues to own the broader workspace composition role and the public shell behavior surface.

Revision note: Created on 2026-06-04 by Codex for the next shell-internal tracer bullet in the same signing-workspace hybrid `4+5` direction, after the interaction bridge slice was completed.
