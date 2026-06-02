# Make Signing Setup Selection Outcomes Explicit

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the signing-setup boundary will stop using `None` as the implicit signal for “the user canceled manual certificate-password entry.” `SigningSetupSession` will return an explicit outcome for certificate-configuration and signature-preset selection, and `SignaturePropertiesPanel` will consume that outcome instead of inferring cancel/no-op from a nullable state. The visible behavior must stay the same: canceled prompts must leave the workflow and selectors unchanged, successful retries must still cache passphrases for the session, and non-promptable coordinator errors must still surface unchanged.

The user-visible proof is behavior preservation with a clearer setup boundary. Focused setup-session tests should assert the explicit outcome directly, and thin shell smoke coverage should prove that the panel still renders returned state and leaves the UI untouched on canceled selection attempts.

## Child ExecPlan Dependencies

- [x] (2026-06-02 00:00Z) No child ExecPlans are required for this narrow boundary slice.

## Progress

- [x] (2026-06-02 00:00Z) Dev-loop explorer selected the first hybrid `3+4` signing-setup slice: make selection outcomes explicit in `SigningSetupSession` and have `SignaturePropertiesPanel` consume them.
- [x] (2026-06-02 00:00Z) Wrote this ExecPlan before implementation.
- [x] (2026-06-02 00:18Z) Added `SigningSetupSelectionOutcome`, updated selection methods in `src/foliaseal/application/signing_setup_session.py`, and rewired the panel selection callers in `src/foliaseal/presentation/qt/signing_shell.py`.
- [x] (2026-06-02 00:24Z) Updated `tests/unit/test_signing_setup_session.py` and `tests/unit/test_qt_signing_shell.py` so successful and canceled selection paths assert explicit outcomes and current-state rerendering.
- [x] (2026-06-02 00:26Z) Completed focused validation: `pytest tests/unit/test_signing_setup_session.py tests/unit/test_qt_signing_shell.py`, `ruff check ...`, and `git diff --check` all passed.
- [x] (2026-06-02 00:41Z) Completed the required compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this ExecPlan; reconciled stale docs-only wording in `docs/ARCHITECTURE.md`.

## Surprises & Discoveries

- Observation: `SigningSetupSession` already owns the retry/cache policy, so the thinnest useful slice is to make that boundary return an explicit outcome instead of widening the form or coordinator seam.
  Evidence: `select_signature_preset()` and `select_certificate_configuration()` both already flow through `_run_with_manual_certificate_password_retry(...)`, while the panel only branches on whether the returned state is `None`.

- Observation: returning the current rendered state on canceled selection attempts lets the panel restore the visible selectors to the real workflow-backed state without adding new Qt-only reset logic.
  Evidence: the new canceled preset-selection shell coverage reuses the returned outcome state to snap the preset selector back to `Current signature setup` while leaving the active certificate selection unchanged.

- Observation: the implementation was already correct; the compliance review found stale docs-only language in `docs/ARCHITECTURE.md` that still described nullable cancel signaling.
  Evidence: `SigningSetupSession` already returns `SigningSetupSelectionOutcome(state, applied)` and the Qt panel branches on `outcome.state` plus `outcome.applied`.

## Decision Log

- Decision: keep `QtVisibleSignatureSetupForm` out of this slice.
  Rationale: the form already serves as a clean draft-mapping adapter. The immediate debt is the implicit selection outcome contract between the session and the panel, not widget-to-draft mapping.
  Date/Author: 2026-06-02 / Codex

- Decision: keep this slice behavior-preserving and selection-focused only.
  Rationale: widening into preview rendering, save/delete confirmation ownership, or coordinator command redesign would make the first hybrid slice harder to validate and review.
  Date/Author: 2026-06-02 / Codex

## Outcomes & Retrospective

The implementation, focused validation, and required compliance review are complete. The review found docs-only drift rather than code drift: selection attempts already return an explicit result object, and the Qt panel already consumes `outcome.state` plus `outcome.applied` instead of treating `None` as the session protocol for canceled prompting.

## Context and Orientation

The relevant application boundary is `src/foliaseal/application/signing_setup_session.py`. That module sits above `src/foliaseal/application/signature_properties_coordinator.py`, which owns workflow mutation, certificate resolution, preset persistence, catalog refresh, and projection of the current setup into `SignaturePropertiesViewState`. The setup session adds policy the coordinator intentionally does not own: retrying when manual password entry is required, prompting through a tiny passphrase adapter, and caching typed passphrases for the current session.

The Qt caller is `SignaturePropertiesPanel` in `src/foliaseal/presentation/qt/signing_shell.py`. The panel owns widgets, overwrite/delete confirmation dialogs, preview rendering, and shell-level change notifications. Certificate-configuration and signature-preset selection now call the setup session, render `outcome.state`, and use `outcome.applied` to decide whether to notify change. That makes cancel/no-op behavior explicit at the boundary while keeping the retry/prompt policy in the session.

The current shell and session tests live in `tests/unit/test_qt_signing_shell.py` and `tests/unit/test_signing_setup_session.py`. The architecture contract for the setup session is documented in `docs/ARCHITECTURE.md`; that doc had stale nullable-cancel wording before this reconciliation pass.

This slice must not widen into the visible-signature form in `src/foliaseal/presentation/qt/visible_signature_setup_form.py`, the signing action boundary, workspace interaction routing, app-frame lifecycle work, or certificate lifecycle changes.

## Plan of Work

First, add one explicit outcome type in `src/foliaseal/application/signing_setup_session.py` for selection-style setup operations. That type should make two things visible: the current `SignaturePropertiesViewState` when a change is applied, and whether the selection action actually applied or was canceled/no-op before mutation. Preserve the existing passphrase retry logic and passphrase cache semantics. Non-promptable coordinator failures must still raise `SignaturePropertiesCoordinatorError`.

Second, update `SigningSetupSession.select_signature_preset()` and `SigningSetupSession.select_certificate_configuration()` to return the new outcome type. Keep `load()`, `apply_visible_setup()`, `set_signature_appearance()`, `refresh_catalogs()`, `save_preset()`, and `delete_preset()` unchanged for this slice unless a small helper extraction is needed to keep the session readable.

Third, update `SignaturePropertiesPanel` in `src/foliaseal/presentation/qt/signing_shell.py` so the selection handlers consume the explicit outcome. Successful outcomes should still re-render state and notify change. Canceled outcomes should leave the panel and workflow unchanged without pretending failure happened. Error handling for `SignaturePropertiesCoordinatorError` must stay exactly as it works today.

Fourth, update focused tests. In `tests/unit/test_signing_setup_session.py`, replace nullable selection assertions with explicit outcome assertions for successful retry, saved-secret no-prompt, canceled prompt, and preset-driven certificate selection with cache reuse. In `tests/unit/test_qt_signing_shell.py`, keep shell coverage thin and add or adjust one selection-path smoke test that proves the panel still renders returned state and that a canceled prompt path does not mutate the workflow or notify change.

Finally, reconcile `docs/ARCHITECTURE.md` so the setup-session contract describes explicit selection outcomes rather than nullable cancel signaling, then run the required compliance review before the documentation and commit steps required by `dev-loop`.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Edit these files:

    src/foliaseal/application/signing_setup_session.py
    src/foliaseal/presentation/qt/signing_shell.py
    tests/unit/test_signing_setup_session.py
    tests/unit/test_qt_signing_shell.py
    docs/ARCHITECTURE.md
    docs/ExecPlans/signing_setup_selection_outcome_execplan.md

Run focused validation as the slice progresses:

    pytest tests/unit/test_signing_setup_session.py tests/unit/test_qt_signing_shell.py
    ruff check src/foliaseal/application/signing_setup_session.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_signing_setup_session.py tests/unit/test_qt_signing_shell.py
    git diff --check

After the first implementation pass, run the required compliance review against at least:

    docs/ARCHITECTURE.md
    docs/SPEC.md
    docs/ExecPlans/signing_setup_selection_outcome_execplan.md

## Validation and Acceptance

This slice is accepted when all of the following are true:

- `SigningSetupSession` returns an explicit outcome for preset and certificate selection instead of using nullable state for cancel signaling
- canceled manual-password prompts leave the workflow and visible setup state unchanged
- successful retry and cache reuse still work for direct certificate selection and preset-driven certificate selection
- non-promptable coordinator failures still raise `SignaturePropertiesCoordinatorError`
- the Qt panel consumes the explicit outcome without widening its orchestration responsibilities
- focused setup-session and shell tests pass
- `docs/ARCHITECTURE.md` accurately describes the new setup-session contract

Observable proof is a focused test run where selection-cancel tests now assert the explicit outcome, successful retry/cache tests still pass, and shell smoke coverage shows the panel still renders the returned setup state.

## Idempotence and Recovery

This is a behavior-preserving refactor in application and Qt presentation code. It is safe to retry. If the first pass leaves both nullable and explicit selection result paths active, remove the duplicate branch before continuing; do not keep two outcome conventions live in parallel. If a test reveals that the outcome type needs one more field for a clear caller contract, add it at the session boundary instead of pushing the ambiguity back into the panel.

## Artifacts and Notes

Important evidence to capture during implementation:

- the focused setup-session and shell test results after the explicit outcome lands
- any compliance finding about stale architecture wording

Keep this section concise and update it if the slice uncovers a surprising caller dependency on nullable session results.

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category. The boundary depends on in-repo workflow state, local catalog stores, and a tiny passphrase prompt adapter that tests can fake.

At the end of the slice, the setup-selection boundary should look approximately like:

    @dataclass(frozen=True)
    class SigningSetupSelectionOutcome:
        state: SignaturePropertiesViewState
        applied: bool

    class SigningSetupSession:
        def select_signature_preset(
            self,
            selected_name: str,
            *,
            control_issue: SigningDraftValidationIssue | None = None,
        ) -> SigningSetupSelectionOutcome: ...

        def select_certificate_configuration(
            self,
            selected_name: str,
            *,
            control_issue: SigningDraftValidationIssue | None = None,
        ) -> SigningSetupSelectionOutcome: ...

The exact name may shift, but the contract must remain: selection operations return an explicit outcome object whose fields let the Qt panel distinguish applied changes from canceled/no-op attempts without treating `None` as the boundary protocol.

Revision note: Created on 2026-06-02 by Codex after the dev-loop explorer selected the explicit selection-outcome slice for the signing-setup hybrid.

Revision note: Updated on 2026-06-02 by Codex after the first implementation pass to record the concrete `SigningSetupSelectionOutcome` shape, focused validation results, and the discovery that canceled outcomes should carry the current rendered state so Qt selectors can be restored without extra panel-only logic.
