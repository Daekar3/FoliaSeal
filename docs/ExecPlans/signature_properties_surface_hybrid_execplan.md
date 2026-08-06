# Signature-properties surface hybrid

## Purpose

Deepen the Qt signature-properties boundary in one complete vertical slice. The current
`SignaturePropertiesPanel` is 1,163 lines and combines Qt construction, certificate/preset
selectors, reusable-object refinement, preview handoff, and application-session orchestration.
The slice keeps domain decisions in `SigningSetupSession` and
`DefaultSignaturePropertiesCoordinator`, extracts the modal refinement workflow into a focused Qt
adapter, and gives shell callers a stable setup port so they no longer reach the panel's private
session.

The frozen contract in `docs/SPEC.md` is unchanged. The coordinated `phase3` nomenclature
retirement remains a separate contract migration; this plan records its dependency but does not
rename public artifact, CLI, or serialized names piecemeal.

## Baseline and design decision

- Baseline: clean `main` after the persisted reusable-signing-model boundary slice; the properties
  panel is 1,163 lines.
- Verified leak: `SigningWorkspaceActionBridge._confirm_signing_request()` reads
  `properties_panel._setup_session.load()` directly.
- Verified composition coupling: the composition root passes concrete panel methods into action,
  interaction, and shell bridges.
- Three independent scan/design reviews ranked the panel at Candidate Priority about 64.3. Minimal
  dialog extraction scored 78/100, a broad application session port 84/100, and a common-caller setup
  port 82/100. The constrained hybrid scores 87.5/100, exceeding the best base by 5.5 points.

## Stable boundary

Add `SigningWorkspaceSetupPort` in `presentation/qt/signing_workspace_setup_port.py`. It exposes
only presentation-facing setup operations and typed values; it must not expose widgets, the
coordinator, workflow, stores, or the private `SigningSetupSession` object:

```python
class SigningWorkspaceSetupPort(Protocol):
    def load_setup_state(self) -> SignaturePropertiesViewState: ...
    def refresh_certificate_configurations(self) -> CertificateCatalog: ...
    def refresh_signature_profiles(self) -> SignaturePropertiesViewState: ...
    def apply_selected_certificate_configuration(self) -> bool: ...
    def save_current_signature_preset(self) -> SignaturePropertiesViewState | None: ...
    def delete_current_signature_preset(self) -> SignaturePropertiesViewState | None: ...
    def apply_changes(self) -> SigningDraftPreview: ...
    def is_ready_to_sign(self) -> bool: ...
    def validation_text(self) -> str: ...
    def refresh_preview(self) -> SigningDraftPreview: ...
    def open_refinement_dialog(self) -> bool: ...
    def set_signature_rect(self, rect: SignatureRect | None, *, notify: bool = True) -> None: ...
```

The existing panel is the production implementation through a thin structural adapter used by
composition. `load_from_workflow()` remains a Qt-local compatibility alias until all production
callers use `load_setup_state`; the alias is not exported from the port.

## Refinement dialog extraction

Move the modal construction and save-profile/preset callbacks into
`presentation/qt/signing_workspace_refinement_dialog.py`. The new
`SignatureRefinementDialog` owns only Qt controls and receives callbacks for state loading,
application, error reporting, and certificate-configuration identity. It returns a typed
`RefinementDialogResult` containing acceptance and an optional `VisibleSignatureSetupDraft`.

The panel remains responsible for applying an accepted draft to the application session and
notifying the rest of the workspace. During this slice the existing `_active_refinement_dialog`
test bridge is retained as a temporary compatibility seam so current acceptance tests can inspect
the live controls. Its retirement criterion is explicit: equivalent dialog tests must use the new
adapter result/fixture surface and `rg` must show no test or production consumer of the private
attribute.

## Behavior map and invariants

- Accept applies the draft exactly once and refreshes the panel preview/state.
- Cancel or a non-accepted dialog leaves the live setup form unchanged.
- Saving appearance or placement profiles persists them without applying the draft; choices refresh
  in the same dialog.
- Preset composition uses the currently selected certificate configuration and preserves
  `current_page` placement semantics.
- Certificate/preset errors still surface through the existing panel error callback.
- Shell action confirmation displays the same certificate and preset labels, obtained via the setup
  port rather than a private panel field.

## Implementation steps

1. Add the typed setup port and adapter, replace the action bridge's private-session access, and wire
   composition's dominant setup callbacks through the port.
2. Extract the refinement dialog and replace the panel's large inline workflow with a small wrapper;
   preserve the temporary active-dialog test bridge.
3. Add boundary and dialog tests, update existing shell tests only where the new seam is observable,
   and remove unused inline helpers/imports.
4. Reconcile `docs/ARCHITECTURE.md`, this plan, and the parent architecture-loop ledger. Record the
   phase3 retirement dependency and the exact internal names that remain frozen until its atomic
   migration.
5. Run focused tests, full pytest, Ruff, diff checks, CLI help/parser checks, preview/signed
   acceptance matrices, and explicit process/artifact cleanup. Commit all implementation and docs
   changes on `main`.

## Acceptance and measurement

The slice is accepted only if the frozen SPEC remains unchanged, the private-session caller grep is
zero, focused and full tests pass, Ruff and diff checks pass, both acceptance matrices retain their
baseline outcomes, and no Qt/FoliaSeal processes or temporary output directories remain. Measure
panel/source movement together with the new boundary: navigation, change amplification, seam risk,
testability, interface compression, cohesion, and behavioral uncertainty. Require Actual Improvement
at least 0.15 with no component regression below -0.10; do not count a file move alone as progress.

## Out of scope

Do not redesign `SigningSetupSession`, change certificate DTO ownership, wire the unused render
cache, or rename `phase3` public CLI/JSON/artifact identifiers in this slice. Those remain ranked
follow-up work under their existing ExecPlans.

## Completion record — 2026-08-06

- [x] Added `SigningWorkspaceSetupPort` and `PanelSigningWorkspaceSetupAdapter`; composition and
  action/interaction/shell callers use the typed setup surface, and the private-session grep is
  zero outside the panel's own application boundary.
- [x] Extracted `SignatureRefinementDialog`, `RefinementDialogState`, and
  `RefinementDialogResult`; accept/cancel, profile persistence, preset composition, and
  `current_page` behavior remain covered by the existing shell tests. The private active-dialog
  bridge is intentionally retained until a later test-surface migration.
- [x] Added setup-port forwarding/boundary coverage and reconciled `docs/ARCHITECTURE.md` plus the
  parent loop ledger. The panel fell from 1,163 to 1,008 lines; the extracted focused modules are
  247 and 88 lines respectively, with behavior-bearing ownership moved rather than deleted.
- [x] Focused tests: 158 passed. Full suite: 1,049 passed with one pre-existing warning. Ruff and
  `git diff --check` passed. CLI help/parser checks passed.
- [x] Offscreen acceptance evidence passed: signed acceptance 10 scenarios (7 successful, 3
  matched intentional rejections), signed preview parity 18/18 successful, signed fit rejection
  3/3 matched, zero cryptographic/annotation/preview comparison failures, and expectations passed.
  A one-scenario preview matrix and the ten-scenario signed matrix also passed in explicit `/tmp`
  directories; those directories and all generated processes were removed.
- [x] The first acceptance attempt failed before execution because the environment selected the
  unavailable `xcb` Qt plugin. Re-running with `QT_QPA_PLATFORM=offscreen` completed successfully;
  this is an environment invocation note, not a product regression.

Measured proxies: panel navigation surface `0.25`, change amplification `0.25`, seam-risk reduction
`0.25`, boundary-test improvement `0.50`, interface compression `0.25`, cohesion `0.25`, and
behavioral uncertainty `0.25`; `Actual Improvement = 0.25`, above the `0.15` gate, with no component
regression below `-0.10`. The slice is accepted pending the parent commit closure.
