# Add a typed signing-readiness projection

This ExecPlan is a living document and must be maintained in accordance with
`.agents/skills/write-execplan/PLANS.md`. It is a narrow child of
`docs/ExecPlans/ui_readiness_caveats_status_execplan.md` and the V1 compliance parent.

## Purpose / Big Picture

After this slice, the open-document signing workspace will describe readiness with one typed,
ordered projection instead of asking separate callbacks whether signing is allowed and what text to
display. The rail will distinguish selecting a preset, completing setup, placing a signature,
reviewing a blocker, and being ready to sign; each state will carry at most one recommended action
and any non-blocking certificate caveat. A user can observe the result by opening a PDF and changing
the setup controls; existing signing, verification-recovery, and no-document behavior remain
unchanged.

This slice does not implement the Signature Library's nested return flow, document link monitoring,
crash recovery, or a new certificate inspector. It reuses the existing certificate-readiness
projection and keeps all policy independent of Qt.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md`, `docs/UI_SPEC.md`, and `docs/ARCHITECTURE.md` are the governing documents.
- [x] `docs/ExecPlans/ui_signing_rail_stage_status_execplan.md` provides the existing rail and
  action-state surface.
- [x] `docs/ExecPlans/ui_certificate_selection_readiness_execplan.md` provides the typed
  certificate readiness and self-signed caveat.
- [x] `docs/ExecPlans/ui_signature_field_targeting_profiles_execplan.md` provides the current
  placement/field state consumed by the setup panel.
- [ ] `docs/ExecPlans/ui_safe_links_external_changes_execplan.md` remains open; document-safety
  monitoring is deliberately represented as a future input rather than reimplemented here.

## Progress

- [x] (2026-08-10) Explorer audit confirmed that certificate readiness already exists, while the
  action coordinator still derives stage text from untyped `is_ready_to_sign` and `validation_text`
  callbacks.
- [x] Add red tests for the ordered readiness matrix, caveats, and exactly one recommended action.
- [x] Implement the Qt-free readiness contract and adapt the setup port/panel.
- [x] Replace the production action coordinator's callback pair with the typed readiness provider;
  migrate all production and focused test callers, then remove the obsolete pair.
- [x] Run focused, full, offscreen, and cleanup validation.
- [x] Complete compliance review, update architecture/parent status, and commit this slice.

## Surprises & Discoveries

- Observation: no-document state is rendered by `FoliaSealAppFrame._set_placeholder()` and has no
  signing sidebar. Evidence: the app-frame placeholder owns Open PDF and Library actions, so this
  slice must not force a fake readiness object into a missing workspace.
- Observation: certificate blocking and warning text are already computed by
  `DefaultSignaturePropertiesCoordinator` and `CertificateReadiness`; duplicating certificate
  inspection would create contradictory states. Evidence: `SignaturePropertiesViewState` already
  carries `certificate_readiness` and composed validation text.
- Observation: the legacy callback pair is used by the production composition seam and unit tests,
  while acceptance evidence captures only serialized validation text. The migration can therefore be
  limited to the production action coordinator/setup port without expanding legacy evidence
  infrastructure.

## Decision Log

- Decision: define readiness as an immutable application contract with state, heading/detail,
  `can_sign`, and one typed recommended action. Rationale: UI_SPEC section 11 requires ordered,
  plain-language states and at most one next action; separate callbacks cannot enforce that
  invariant. Date/Author: 2026-08-10 / Codex.
- Decision: classify an empty preset catalog with no selected preset as `SELECT_PRESET`; when saved
  presets exist but a manual edit clears the selection, preserve the existing setup path until the
  dedicated preset-selection semantics child defines a replacement-selection requirement. Rationale:
  first-use must be explicit without breaking valid manual setup or existing document fixtures.
  Date/Author: 2026-08-10 / Codex.
- Decision: treat a directly configured certificate path as selected material when the existing
  workflow already supplies one, while catalog-backed readiness remains authoritative whenever a
  managed certificate is selected. Rationale: this preserves the supported direct-material path for
  current workflows and tests without duplicating certificate inspection; the broader certificate
  lifecycle child owns eventual convergence on catalog-only selection. Date/Author: 2026-08-10 / Codex.
- Decision: keep certificate caveats in the ready state's detail and keep warnings non-blocking.
  Rationale: the existing certificate-readiness contract already distinguishes blocking states from
  self-signed/expiring warnings, and UI_SPEC says caveats must not displace Ready. Date/Author:
  2026-08-10 / Codex.
- Decision: retain recovery/result state precedence above draft readiness. Rationale: a preserved
  artifact or verified signed output has a different user action model and is already covered by
  the recovery child. Date/Author: 2026-08-10 / Codex.

## Outcomes & Retrospective

Implemented on 2026-08-10. The pure projection covers the ordered `SELECT_PRESET`,
`SETUP_REQUIRED`, `PLACE_SIGNATURE`, `REVIEW_READINESS`, and `READY` branches, with one typed
recommended action and non-blocking certificate caveats. `PLACE_SIGNATURE` and `REVIEW_READINESS`
are ordered sub-states within UI_SPEC's top-level `Setup required` status until the full rail
state-machine child defines its final presentation mapping. `SigningActionCoordinator` now
consumes one `SigningReadiness` provider; the old callback pair has no action-coordinator
production callers, while setup/testing ports retain serialized accessors for existing harness
evidence. Focused readiness/coordinator/shell validation is green (`181 passed` across the
selected regression set); full-suite, lint, bounded offscreen, and compliance-review results are
recorded below. Document-safety input and the remaining full rail state machine remain open in
their owning children.

## Context and Orientation

`src/foliaseal/application/signing_readiness.py` will own the Qt-free contract. The existing
`SignaturePropertiesViewState` in `signature_properties_coordinator.py` is the source of selected
preset, placement, certificate readiness, validation text, and `ready_to_sign`. The panel adapter in
`signing_workspace_setup_port.py` is the public seam used by
`signing_workspace_composition.py`. `SigningActionCoordinator` currently receives two callbacks
(`is_ready_to_sign` and `validation_text`) and chooses stage text in `_build_state()`; the new
provider replaces those callbacks. `SigningWorkspaceSidebar` already renders stage/detail labels and
one highlighted primary action, so this slice exposes the typed action even when its owning button
belongs to a later Library/placement child.

The product states implemented here are `SELECT_PRESET`, `SETUP_REQUIRED`, `PLACE_SIGNATURE`,
`REVIEW_READINESS`, and `READY`. `SIGNED`, `RECOVERY`, and `NO_DOCUMENT` remain owned by existing
coordinator/app-frame branches. A recommended action is a stable value such as
`choose_setup`, `complete_setup`, `place_signature`, `review_readiness`, or `sign`.

## Change Slice

Primary change class: behavior change with focused tests and minimum architecture/status updates.
Allowed files are the new application contract, setup port/panel, signing action coordinator and
composition seam, focused tests, `docs/ARCHITECTURE.md`, this plan, the readiness parent, and the
V1 compliance parent. Do not add Qt buttons, document monitoring, certificate parsing, recovery
journaling, generated PDFs, or acceptance evidence refactors in this slice.

## Plan of Work

Create immutable `SigningReadiness`, `SigningReadinessStage`, and `SigningReadinessAction` types in
`src/foliaseal/application/signing_readiness.py`, plus a pure `project_signing_readiness()` function
that accepts the selected preset name, certificate blocking/warning detail, placement presence,
validation text, and current `ready_to_sign` result. Evaluate in this order: missing preset,
blocking certificate/setup, missing placement, blocking validation, then ready. Preserve a warning
detail in the ready state without making `can_sign` false. Normalize empty details to safe
plain-language defaults and enforce that a result exposes no more than one recommended action.

Add `readiness()` to `SigningWorkspaceSetupPort` and its panel adapter. The panel should load its
current `SignaturePropertiesViewState`, translate it into the pure input, and return the projection;
the adapter must not reach through private child widgets.

Change `SigningActionCoordinator` and `SigningWorkspaceComposition` to accept one readiness provider.
Use the projection for submit gating, stage/detail text, and recommended action while retaining the
existing signed-output and recovery precedence. Migrate focused coordinator fixtures to return
explicit projections and remove the old callback parameters after `rg` proves no production caller
remains. Keep the testing adapter's serialized `validation_text` for existing evidence consumers.

Add unit tests for every ordered branch, missing/partial presets, blocking versus warning
certificate readiness, placement and appearance blockers, ready caveats, and the single-action
invariant. Add an offscreen shell/action test proving the rail receives the typed stage/detail and
that a ready self-signed certificate remains signable.

## Milestones

Milestone 1 defines the pure matrix and turns red contract tests green without Qt. Milestone 2
migrates the setup port and action coordinator while preserving signing/recovery regressions.
Milestone 3 proves the real offscreen shell projection, updates architecture and living-plan
evidence, runs the full suite, and commits the complete slice.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    .venv/bin/pytest -q tests/unit/test_signing_readiness.py tests/unit/test_qt_signing_action_coordinator.py
    .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py
    .venv/bin/ruff check src tests
    .venv/bin/pytest -q
    git diff --check

Run the bounded offscreen lifecycle audit with an isolated configuration root. Record its exit,
remove the temporary root, and verify that no FoliaSeal/PySide6/pytest process remains:

    audit_root=$(mktemp -d /tmp/foliaseal-readiness-audit-XXXXXX)
    timeout --foreground 30s env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf || test "$?" -eq 124
    ps -eo pid,cmd | rg 'FoliaSeal|foliaseal|PySide6|pytest' | rg -v 'rg ' || true
    rm -rf "$audit_root"
    test ! -e "$audit_root"

The isolated local-socket limitation may still prevent frame creation; record it exactly rather
than treating it as GUI success. Offscreen Qt tests are the authoritative observable evidence for
this AFK slice.

## Validation and Acceptance

Acceptance requires that the pure matrix produces exactly one ordered state and at most one
recommended action; missing preset/setup/placement and blocking validation cannot expose Sign as
ready; a ready state can sign; self-signed or expiring warnings remain non-blocking and visible;
signed/recovery states retain their existing behavior; and no production caller uses the removed
callback pair. Focused tests, Ruff, diff checks, and the full suite must pass. The offscreen audit
must clean its owned processes and temporary root.

## Idempotence and Recovery

The projection is pure and safe to rerun. If migration breaks a caller, use `rg` to find it and
restore the typed provider at that seam rather than reintroducing parallel readiness logic. Do not
delete unrelated compatibility or evidence modules. Remove only this slice's temporary audit root.

## Artifacts and Notes

No generated artifacts are required. Record test counts, the exact isolated-socket diagnostic if it
occurs, changed files, and cleanup results in Progress and Evidence. Do not commit PDFs, keys,
passwords, screenshots containing private data, or machine-local absolute paths.

## Interfaces and Dependencies

The pure projection should remain standard-library-only. The setup port returns
`SigningReadiness`; the action coordinator accepts `readiness: Callable[[], SigningReadiness]` and
does not inspect the Qt panel. Existing `CertificateReadiness` values remain the sole certificate
truth source. Future document-safety integration can add an input to the pure projection in a
separate child after the renderer/source-monitor seam exists.

Evidence record (2026-08-10): focused pure/coordinator/shell validation passed (`181 passed`),
`rg` found no production `is_ready_to_sign=` or coordinator `validation_text=` constructor callers,
the adapter-forwarding contract is covered by `test_signing_workspace_setup_port.py`, and the
architecture/compliance review accepted the typed seam after clarifying that setup/testing
accessors remain for harness evidence. The bounded offscreen launch used
an isolated XDG root and was cleaned up; this environment still reports the known
`SingleInstanceUnavailable` local-socket limitation before frame creation, so offscreen Qt tests are
the authoritative GUI evidence. The full suite passed with `1349 passed, 20 skipped, 1 warning`.
No process or temporary audit directory was left behind.

Revision note: 2026-08-10 / Codex. Created after explorer review found that the existing rail had
duplicated untyped readiness callbacks and omitted the normative state/action vocabulary; the plan
intentionally leaves document safety monitoring and nested Library actions to their owning plans.
