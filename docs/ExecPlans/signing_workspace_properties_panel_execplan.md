# Extract The Signing Workspace Properties Panel

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

This slice will keep the current signing workflow behavior unchanged while moving the remaining `SignaturePropertiesPanel` cluster out of `signing_shell.py` and into a dedicated shell-local module. The new `signing_workspace_properties_panel.py` module will own the panel widget, preview/validation wiring, setup-session orchestration, preset and certificate selector handling, and panel disposal behavior while `signing_shell.py` remains the composition root.

That continues the same `4+5` hybrid direction: a narrow shell-owned port at the edge with thinner Qt adapters over deeper helper boundaries.

## Child ExecPlan Dependencies

- [x] (2026-06-04 23:04Z) No child ExecPlans are required for this bounded shell-internal extraction slice.

## Progress

- [x] (2026-06-04 23:04Z) Completed the required `explorer-light` audit and fixed the next slice to extracting the `SignaturePropertiesPanel` cluster into its own shell-local module rather than reopening app-frame, certificate-management, or setup policy seams.
- [x] (2026-06-04 23:05Z) Re-read the `SignaturePropertiesPanel` cluster in `src/foliaseal/presentation/qt/signing_shell.py`, the architecture debt note in `docs/ARCHITECTURE.md`, and the focused shell tests around presets, preview refresh, apply-changes, and certificate configuration flows.
- [x] (2026-06-04 23:24Z) Added `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py` and moved the panel cluster out of `signing_shell.py` into `SignaturePropertiesPanel` there while keeping the shell as the composition root.
- [x] (2026-06-04 23:26Z) Updated focused coverage implicitly through the existing shell/preview tests and kept the compatibility import surface in `signing_shell.py` that downstream tests still use.
- [x] (2026-06-04 23:27Z) Ran focused validation with the shell subset, the signature-properties/preview boundary suites, `ruff check`, and `git diff --check`; all passed.
- [x] (2026-06-04 23:40Z) Completed the architectural/spec compliance review locally after the planned explorer-light reviewer hit a usage limit; the implementation matched `docs/SPEC.md`, and the remaining work was documentation-only reconciliation in `docs/ARCHITECTURE.md`.
- [x] (2026-06-04 23:41Z) Updated documentation to final state, including the extracted panel-module ownership and the narrowed `signing_shell.py` debt note.

## Surprises & Discoveries

- Observation: `signing_shell.py` still acts as a compatibility import surface for several preview/layout tests even after the panel lift.
  Evidence: focused preview-layout tests import `SigningDraftPreview`, `SignatureTextStyle`, and `SignatureTimezoneDisplayMode` from `foliaseal.presentation.qt.signing_shell`, so those aliases needed to remain re-exported after the panel code moved.

## Decision Log

- Decision: keep `SigningSetupSession`, `DefaultSignaturePropertiesCoordinator`, `QtCanonicalPreviewLifecycle`, and `QtSignaturePreviewLayout` behavior unchanged in this slice.
  Rationale: the remaining concentration is module ownership in `signing_shell.py`, not the existing panel policy or preview boundaries.
  Date/Author: 2026-06-04 / Codex

- Decision: move the whole panel cluster into its own module instead of shaving smaller helper functions first.
  Rationale: the panel already had a coherent boundary set, and smaller extractions would have preserved most of the concentration in `signing_shell.py`.
  Date/Author: 2026-06-04 / Codex

## Outcomes & Retrospective

The slice is complete. `SignaturePropertiesPanel` and its private helper surface now live in `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py`, while `signing_shell.py` remains the composition root and keeps the compatibility re-exports that downstream tests still expect.

Validation for the implementation slice passed before the documentation closeout:

- `pytest tests/unit/test_qt_signing_shell.py -k 'signature_preset or set_signature_appearance or apply_changes or refresh_preview or certificate_configuration'`
- `pytest tests/unit/test_signature_properties_coordinator.py tests/unit/test_signature_preview_lifecycle.py tests/unit/test_signature_preview_layout.py`
- `ruff check src/foliaseal/presentation/qt/signing_workspace_properties_panel.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py`
- `git diff --check`

The planned explorer-light compliance review became unavailable mid-loop because that subagent hit a usage limit. I finished the compliance pass locally against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this ExecPlan, and the remaining work was documentation-only reconciliation. `docs/SPEC.md` and `README.md` did not require changes for this slice.

## Context and Orientation

`src/foliaseal/presentation/qt/signing_shell.py` is still the composition root for the interactive signing workspace. Recent slices already moved several clusters out of the shell:

- `src/foliaseal/presentation/qt/signing_shell_port.py` owns the outer workspace bootstrap/port/factory seam used by the app frame.
- `src/foliaseal/presentation/qt/signing_workspace_sidebar.py` owns the grouped sidebar surface and sidebar render paths.
- `src/foliaseal/presentation/qt/signing_workspace_review_bridge.py` owns review/text bridge state and transition application.
- `src/foliaseal/presentation/qt/signing_workspace_interaction_bridge.py` owns `WorkspaceInteractionPlan` execution.
- `src/foliaseal/presentation/qt/signing_workspace_action_bridge.py` owns shell-facing signing-action dialog/state glue.

Before this slice, the shell still directly contained the large `SignaturePropertiesPanel` cluster: panel widget construction, setup-session orchestration, preset/certificate control wiring, preview lifecycle/layout wiring, apply-changes behavior, validation handling, and cleanup.

The files that matter for this slice are:

- `src/foliaseal/presentation/qt/signing_shell.py`, which previously owned the `SignaturePropertiesPanel` implementation and now should only import and compose it.
- `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py`, which now owns the extracted panel cluster.
- `tests/unit/test_qt_signing_shell.py`, which guards preset, certificate-configuration, preview-refresh, and apply-changes behavior through the public shell/panel surface.
- `tests/unit/test_signature_properties_coordinator.py`, `tests/unit/test_signature_preview_lifecycle.py`, and `tests/unit/test_signature_preview_layout.py`, which provide the narrow safety net around the reused deeper boundaries.
- `docs/ARCHITECTURE.md`, which will need to describe the new panel module if the extraction lands.

In this plan, a “properties panel module” means the extracted Qt-facing module that owns `SignaturePropertiesPanel` and its local helper surface while leaving `SigningWorkspaceWidget` as the composition root.

## Plan of Work

First, add a new shell-local module under `src/foliaseal/presentation/qt/` for `SignaturePropertiesPanel` and its local helper surface. The module should own the panel widget, preview controls, setup-session prompt adapter, and private helper functions without changing panel behavior.

Second, edit `src/foliaseal/presentation/qt/signing_shell.py` so it imports `SignaturePropertiesPanel` from the new module and keeps only the workspace composition role. The public shell/panel behavior surface should stay unchanged.

Third, update focused coverage as needed. Keep the public shell tests around preset/certificate/preview behavior, and use the existing signature-properties and preview boundary suites as the narrow safety net. If compatibility imports need to stay in `signing_shell.py` for test callers, preserve them explicitly.

Finally, run focused validation, perform the required compliance review, update any stale docs, and record the final result here.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Add the extracted properties panel module and migrate the shell.

       apply_patch ... on src/foliaseal/presentation/qt/<new helper>.py
       apply_patch ... on src/foliaseal/presentation/qt/signing_shell.py

2. Update focused tests if needed.

       apply_patch ... on tests/unit/test_qt_signing_shell.py

3. Run focused validation.

       pytest tests/unit/test_qt_signing_shell.py -k 'signature_preset or set_signature_appearance or apply_changes or refresh_preview or certificate_configuration'
       pytest tests/unit/test_signature_properties_coordinator.py tests/unit/test_signature_preview_lifecycle.py tests/unit/test_signature_preview_layout.py
       ruff check src/foliaseal/presentation/qt/<new helper>.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py
       git diff --check

4. Run the required compliance review, reconcile docs if needed, and commit the slice.

## Validation and Acceptance

This slice is accepted when all of the following are true:

- a dedicated shell-local module owns `SignaturePropertiesPanel` and its helper surface instead of `signing_shell.py`
- preset, certificate-configuration, preview-refresh, validation, and disposal behavior still behave the same
- the setup-session/coordinator/preview lifecycle/preview layout boundaries remain unchanged and continue to own the same responsibilities
- focused shell tests plus the narrow preview/coordinator suites prove the extraction preserved behavior
- `docs/ARCHITECTURE.md` accurately describes the new panel-module ownership and shell split

Run:

    pytest tests/unit/test_qt_signing_shell.py -k 'signature_preset or set_signature_appearance or apply_changes or refresh_preview or certificate_configuration'
    pytest tests/unit/test_signature_properties_coordinator.py tests/unit/test_signature_preview_lifecycle.py tests/unit/test_signature_preview_layout.py

Then run:

    ruff check src/foliaseal/presentation/qt/<new helper>.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py
    git diff --check

Acceptance is behavioral. No GUI flow or text is intended to change.

## Idempotence and Recovery

This is a behavior-preserving extraction. It is safe to retry. If the module extraction causes awkward compatibility needs for tests or neighboring helpers, keep explicit re-export aliases in `signing_shell.py` rather than moving callers in the middle of this slice. Do not recover by duplicating the same panel implementation in both files; one owner must remain at the end of the slice.

If the extraction unexpectedly requires changing setup-session, coordinator, preview-lifecycle, or preview-layout semantics, stop and split that broader redesign into a later slice instead of widening this one.

## Artifacts and Notes

The most important evidence for this slice will be:

- a new shell-local module for `SignaturePropertiesPanel`
- a smaller shell-side integration surface inside `src/foliaseal/presentation/qt/signing_shell.py`
- focused shell tests and preview/coordinator tests proving preset/certificate/preview behavior is unchanged

## Interfaces and Dependencies

This slice uses the `In-process` dependency category.

At the end of the slice, the new module should continue to expose the same panel class surface approximately like:

    class SignaturePropertiesPanel:
        def load_from_workflow(self) -> None: ...
        def refresh_preview(self) -> SigningDraftPreview: ...
        def apply_changes(self) -> SigningDraftPreview: ...
        def set_signature_rect(...) -> None: ...
        def set_signature_appearance(...) -> None: ...
        def refresh_certificate_configurations(self) -> CertificateCatalog: ...

The module may keep its smaller helper classes/functions private, but the shell should only need to import and compose `SignaturePropertiesPanel`. The shell continues to own the broader workspace composition role and the public shell behavior surface.

Revision note: Created on 2026-06-04 by Codex for the next shell-internal tracer bullet in the same signing-workspace hybrid `4+5` direction, after the action bridge slice was completed.
