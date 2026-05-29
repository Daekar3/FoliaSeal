# Extract A Signing Setup Session Boundary

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with [`.agents/skills/write-execplan/PLANS.md`](/home/daekar/FoliaSeal/.agents/skills/write-execplan/PLANS.md).

## Purpose / Big Picture

After this slice, the signing setup workflow will no longer be orchestrated directly inside `SignaturePropertiesPanel`. The panel will still own Qt widgets, confirmation dialogs, and preview rendering, but one explicit session boundary will own the common setup flow for loading state, applying visible-signature edits, selecting presets, selecting certificate configurations, retrying manual certificate passwords when needed, and refreshing setup catalogs.

The user-visible behavior should stay the same. The preset-first setup remains intact, partial presets still preserve an active certificate when they do not define one, manual certificate passwords are still prompted on demand, and the canonical preview still refreshes after setup changes. The observable change is architectural: more setup-heavy shell tests should be replaceable by boundary tests against the new session.

## Child ExecPlan Dependencies

- [x] (2026-05-29 18:28Z) No child ExecPlans are required for this bounded first slice.

## Progress

- [x] (2026-05-29 18:28Z) Reviewed `src/foliaseal/presentation/qt/signing_shell.py`, `src/foliaseal/application/signature_properties_coordinator.py`, `src/foliaseal/presentation/qt/visible_signature_setup_form.py`, and the relevant tests to confirm that `SignaturePropertiesPanel` still owns too much setup orchestration.
- [x] (2026-05-29 18:28Z) Wrote this ExecPlan and fixed the slice boundary at: common setup orchestration only. Preview rendering, editor widget construction, and save/delete confirmation dialogs remain where they are.
- [x] (2026-05-29 18:36Z) Added `src/foliaseal/application/signing_setup_session.py` with explicit verbs for load, visible-setup apply, preset selection, certificate selection, blank preset clear, and catalog refresh.
- [x] (2026-05-29 18:36Z) Moved manual certificate-password retry and session-local passphrase caching out of `SignaturePropertiesPanel` into the new session boundary.
- [x] (2026-05-29 18:36Z) Migrated `SignaturePropertiesPanel` to become a thinner Qt adapter over the new session for the common setup flows.
- [x] (2026-05-29 18:36Z) Added direct boundary tests in `tests/unit/test_signing_setup_session.py`; existing shell tests remained valid as thin adapter coverage for the migrated flows.
- [x] (2026-05-29 18:36Z) Ran focused validation with `pytest`, `ruff check`, and `git diff --check`.
- [x] (2026-05-29 18:36Z) Ran the required compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and `docs/SCHEMAS.md`, then addressed the remaining architecture-doc gap.
- [x] (2026-05-29 18:36Z) Updated documentation, including this ExecPlan, to final state.
- [x] (2026-05-29 18:36Z) Commit the slice as one narrow architecture change.

## Surprises & Discoveries

- Observation: the current coordinator already owns the business rules the panel needs for the common setup flows.
  Evidence: `DefaultSignaturePropertiesCoordinator` already exposes `load()`, `apply_visible_setup()`, `apply_signature_preset()`, `apply_certificate_configuration()`, and `reconcile(RefreshCatalogs())`.

- Observation: the panel still owns one real policy that is not merely Qt rendering: manual certificate-password retry and passphrase caching.
  Evidence: `_apply_certificate_configuration_with_manual_password_retry()`, `_apply_signature_preset_with_manual_password_retry()`, `_run_with_manual_certificate_password_retry()`, and `_session_certificate_passphrases` all live in `src/foliaseal/presentation/qt/signing_shell.py`.

- Observation: the only red test during implementation was a boundary-test setup mistake, not a production behavior gap.
  Evidence: the first version of the partial-preset test canceled the initial certificate-selection prompt, so no active certificate existed to preserve. The session logic itself already matched `SPEC.md`.

## Decision Log

- Decision: keep this first slice focused on the common setup flows and leave preset save/delete confirmation dialogs in the panel.
  Rationale: save/delete still need direct Qt confirmation boxes, while the highest-value repeated orchestration is load/apply/select/refresh plus passphrase retry. Splitting those concerns keeps the change narrow and lowers regression risk.
  Date/Author: 2026-05-29 / Codex

- Decision: keep the new session Qt-free but inject a tiny passphrase-prompt port.
  Rationale: the user explicitly wants the UI layer separated from core logic. A small prompt protocol allows the session to own retry/cancel/cache policy without importing Qt.
  Date/Author: 2026-05-29 / Codex

- Decision: keep the new boundary above the existing coordinator instead of replacing the coordinator.
  Rationale: the coordinator is already the correct owner for signing-draft reconciliation rules. The missing deep module is the orchestration layer that composes coordinator calls into the actual setup workflow.
  Date/Author: 2026-05-29 / Codex

## Outcomes & Retrospective

Implemented result:

- `SignaturePropertiesPanel` no longer owns manual password retry/cache policy for the common setup flows.
- the panel delegates `load`, visible-setup apply, preset selection, certificate selection, blank preset clear, and catalog refresh to an explicit session boundary.
- direct boundary tests now cover the setup-session behavior without needing to drive fake Qt controls for each rule.
- `SPEC.md` and `SCHEMAS.md` behavior remains intact: preset-first setup, partial preset behavior, on-demand password prompting, and preview parity.
- focused validation evidence:
  - `pytest tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py tests/unit/test_qt_signing_shell.py -q` -> `108 passed`
  - `ruff check src/foliaseal/application/signing_setup_session.py src/foliaseal/application/__init__.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_signing_setup_session.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py` -> passed
  - `git diff --check` -> passed

## Context and Orientation

The production seam lives in [src/foliaseal/presentation/qt/signing_shell.py](/home/daekar/FoliaSeal/src/foliaseal/presentation/qt/signing_shell.py). `SignaturePropertiesPanel` builds the `Signature presets`, `Certificate configuration`, visible-signature form, placement controls, and preview card. It already delegates the core signing-draft reconciliation rules to [src/foliaseal/application/signature_properties_coordinator.py](/home/daekar/FoliaSeal/src/foliaseal/application/signature_properties_coordinator.py), but it still owns the workflow that decides which coordinator entrypoint to call, how to retry after missing manual certificate passwords, when to reuse a cached passphrase, and how to recover UI state after errors.

The visible-signature editor itself lives in [src/foliaseal/presentation/qt/visible_signature_setup_form.py](/home/daekar/FoliaSeal/src/foliaseal/presentation/qt/visible_signature_setup_form.py). That module should remain the Qt-local editor port for this slice. It builds widgets, loads a `VisibleSignatureSetupDraft` into controls, and builds a new `VisibleSignatureSetupDraft` from the controls. It should not become the owner of setup workflow policy.

The coordinator already owns the meaningful signing-draft rules. It resolves certificate material through the resolver, preserves active certificates when partial presets omit a certificate reference, refreshes stale selections against current catalogs, and returns immutable `SignaturePropertiesViewState` values that carry the ready-to-sign text and preview. This slice should not re-implement any of those rules.

The relevant tests are:

- [tests/unit/test_signature_properties_coordinator.py](/home/daekar/FoliaSeal/tests/unit/test_signature_properties_coordinator.py)
- [tests/unit/test_qt_signing_shell.py](/home/daekar/FoliaSeal/tests/unit/test_qt_signing_shell.py)
- [tests/unit/test_qt_visible_signature_setup_form.py](/home/daekar/FoliaSeal/tests/unit/test_qt_visible_signature_setup_form.py)

Today, many of the shell tests still reach through `SignaturePropertiesPanel` to prove behavior that should be expressible at a deeper setup boundary.

## Plan of Work

First, add a new Qt-free setup-session boundary. It should live near the existing signing setup application boundary and expose explicit verbs for the common setup actions:

- `load()`
- `apply_visible_setup(draft, ...)`
- `select_signature_preset(name, ...)`
- `select_certificate_configuration(name, ...)`
- `refresh_catalogs(...)`

The session should depend on the existing `SignaturePropertiesCoordinator` plus a very small prompt interface for manual certificate-password entry. The session should own:

- deciding whether to retry after a coordinator error
- prompting for a passphrase when the error indicates manual password entry is required
- caching passphrases by certificate configuration display name for the current UI session
- returning `None` on user-canceled prompts instead of forcing the panel to interpret cancellation

Second, migrate `SignaturePropertiesPanel` so the common flows call the new session instead of assembling the orchestration locally. The panel should still:

- build and own the Qt widgets
- render `SignaturePropertiesViewState` into controls
- show preset/certificate error message boxes
- handle preset save/delete confirmation and preview rendering

Third, add direct tests for the session boundary. These tests should prove:

- partial preset application still preserves an active certificate when appropriate
- manual password retry happens only when the coordinator raises a prompt-worthy error
- canceled prompts return `None` without mutating state
- the session-local passphrase cache avoids repeat prompts
- catalog refresh and visible-setup apply still return the same coordinator-backed state shape

Finally, update the shell tests only where they should now assert thin adapter behavior instead of orchestration details, run focused validation, and update `docs/ARCHITECTURE.md`.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Edit the new setup-session boundary, the signing shell, and focused tests.

       apply_patch ... on src/foliaseal/application/<new setup session module>.py
       apply_patch ... on src/foliaseal/presentation/qt/signing_shell.py
       apply_patch ... on tests/unit/<new setup session test module>.py
       apply_patch ... on tests/unit/test_qt_signing_shell.py

2. Run focused validation.

       pytest tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py tests/unit/<new setup session test module>.py
       ruff check src/foliaseal/application/<new setup session module>.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py tests/unit/<new setup session test module>.py
       git diff --check

3. Run the required compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and `docs/SCHEMAS.md`. If that review finds a mismatch, update this ExecPlan, implement the fix, and repeat validation before committing.

4. Update documentation and commit the slice.

## Validation and Acceptance

This slice is accepted when all of the following are true:

- `SignaturePropertiesPanel` delegates the common setup flows to an explicit session boundary
- manual certificate-password retry and the session-local passphrase cache no longer live in the panel
- the visible-signature form remains the Qt editor port and the preview modules remain the preview owners
- partial preset behavior still matches `SPEC.md` and `SCHEMAS.md`
- direct tests cover the new session boundary
- focused shell tests still pass
- `docs/ARCHITECTURE.md` describes the new setup boundary accurately

Run:

    pytest tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py tests/unit/<new setup session test module>.py

Then run:

    ruff check src/foliaseal/application/<new setup session module>.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py tests/unit/<new setup session test module>.py
    git diff --check

Acceptance is behavior-focused. There is no intended change to the visible signing workflow in this slice.

## Idempotence and Recovery

This is a behavior-preserving refactor in local application/Qt presentation code. It is safe to retry. If the first session extraction is too broad, keep the new session boundary and move one flow at a time behind it, starting with preset selection and certificate selection, then visible-setup apply and refresh. Do not move preview rendering or form widget construction into the new session as a recovery shortcut.

## Artifacts and Notes

The most important evidence for this slice will be:

- the focused `pytest` result covering the new session tests plus affected shell/coordinator tests
- a clean `ruff check`
- a clean `git diff --check`
- the updated `docs/ARCHITECTURE.md` description of the setup session boundary

These transcripts should be recorded back into this ExecPlan as work completes.

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

At the end of this slice, the setup seam should look approximately like:

    class CertificatePassphrasePrompter(Protocol):
        def prompt(self, label: str) -> str | None: ...

    class SigningSetupSession(Protocol):
        def load(...) -> SignaturePropertiesViewState: ...
        def apply_visible_setup(...) -> SignaturePropertiesViewState: ...
        def select_signature_preset(...) -> SignaturePropertiesViewState | None: ...
        def select_certificate_configuration(...) -> SignaturePropertiesViewState | None: ...
        def refresh_catalogs(...) -> SignaturePropertiesViewState: ...

The exact module path and helper type names may shift, but the shape must remain explicit. The session should depend on the coordinator and a prompt port, while the panel becomes a thinner renderer/editor adapter over that session.

Revision note: Created on 2026-05-29 by Codex for the first implementation slice of the proposed signing-setup session hybrid.
