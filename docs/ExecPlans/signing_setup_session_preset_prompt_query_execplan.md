# Move Preset Certificate Prompt Lookup Behind the Coordinator

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, `SigningSetupSession` gets preset certificate display names from the coordinator's public `certificate_configuration_name_for_preset()` helper instead of reaching into the coordinator's preset and certificate catalogs directly. The visible behavior stays the same: selecting a signature preset that references a certificate still prompts with that certificate's display name, and presets without a certificate still use the generic prompt. A contributor can prove the slice works by running the focused session and coordinator tests and observing unchanged prompt text with a narrower session boundary.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/signing_setup_session_panel_boundary_execplan.md` completed the panel save-path boundary cleanup.
- [x] `docs/ExecPlans/signing_setup_session_panel_delete_boundary_execplan.md` completed the panel delete-path boundary cleanup.
- [ ] No child ExecPlans are required for this slice.

## Progress

- [x] (2026-06-25 11:41Z) Re-read the current `dev-loop` instructions, inspected the live session/coordinator/workflow seam, and confirmed the panel save/delete boundary work is already in place.
- [x] (2026-06-25 11:46Z) Completed the required `explorer-light` review and fixed the next smallest slice at the preset-certificate prompt-label lookup currently living inside `SigningSetupSession`.
- [x] (2026-06-25 21:18Z) Added `DefaultSignaturePropertiesCoordinator.certificate_configuration_name_for_preset()` and kept it read-only over the existing preset and certificate catalogs.
- [x] (2026-06-25 21:18Z) Updated `SigningSetupSession.select_signature_preset()` to build the prompt label from the coordinator helper instead of walking catalogs directly.
- [x] (2026-06-25 21:18Z) Added focused coordinator and session tests and recorded the passing run below.
- [x] (2026-06-25 21:18Z) Ran the architecture/spec compliance review and confirmed the slice remains aligned with `docs/ARCHITECTURE.md` and `docs/SPEC.md`.

## Surprises & Discoveries

- Observation: the remaining hybrid leak was reduced to a read-only lookup helper and then removed from `SigningSetupSession` entirely.
  Evidence: `src/foliaseal/application/signing_setup_session.py` now calls `DefaultSignaturePropertiesCoordinator.certificate_configuration_name_for_preset()` to compose `prompt_label` before delegating the actual apply operation back to the coordinator.

## Decision Log

- Decision: keep this slice query-only and avoid touching `SigningDraftWorkflow.capture_current_signature_setup()` or `apply_resolved_signature_preset()`.
  Rationale: those workflow methods still define the persistence-facing `ResolvedSignaturePreset` seam, which is broader than the remaining session-boundary leak. Changing them here would mix behavior change with schema/persistence refactoring.
  Date/Author: 2026-06-25 / Codex

- Decision: leave Qt confirmation dialogs and panel behavior unchanged.
  Rationale: the panel methods already sit on the `SigningSetupSession` boundary after the previous two slices. Moving UI confirmation policy into application code would widen this change without advancing the chosen hybrid seam.
  Date/Author: 2026-06-25 / Codex

## Outcomes & Retrospective

This slice is complete. `SigningSetupSession` now asks the coordinator for preset certificate display names through `certificate_configuration_name_for_preset()`, which keeps prompt text unchanged while removing direct catalog traversal from the session. Focused unit tests passed, and the implementation remained aligned with `docs/ARCHITECTURE.md` and `docs/SPEC.md` during review.

## Context and Orientation

The repository root is `/home/daekar/FoliaSeal`. The relevant application-layer session lives in `src/foliaseal/application/signing_setup_session.py`. That session is a deep module that owns repeated signing-setup orchestration above the lower-level `DefaultSignaturePropertiesCoordinator` in `src/foliaseal/application/signature_properties_coordinator.py`. A "signature preset" in this repository is a reusable visible-signature setup persisted through the preset catalog. Some presets also refer to a saved certificate configuration. When the user selects such a preset and the certificate requires a manual password, the session prompts for a password using the certificate display name.

Today, `SigningSetupSession.select_signature_preset()` gets the display name from `self.coordinator.certificate_configuration_name_for_preset(...)` and then delegates preset application through `self.coordinator.apply_signature_preset(...)`. The session no longer walks `self.coordinator.preset_catalog` or `self.coordinator.certificate_catalog` itself for the prompt label, so the remaining boundary is narrower than before.

The goal of this slice is not to redesign preset storage or the workflow model. `src/foliaseal/application/signing_draft_workflow.py` still owns `capture_current_signature_setup()` and `apply_resolved_signature_preset()` and still works with `ResolvedSignaturePreset`. That broader seam must remain untouched here. Allowed generated artifacts for this slice are behavior changes in the two application modules, focused evidence refresh in unit tests, and the documentation/status update in this ExecPlan. Unrelated UI wording, schema changes, storage format changes, and broad workflow refactors are forbidden from being mixed into this slice.

## Plan of Work

Add a tiny public query on `DefaultSignaturePropertiesCoordinator` in `src/foliaseal/application/signature_properties_coordinator.py` that accepts a preset name and returns the certificate configuration display name for that preset, or `None` when no prompt-specific certificate name can be resolved. The helper should use the coordinator's current preset and certificate catalogs, match the existing fallback behavior, and stay read-only.

Then update `src/foliaseal/application/signing_setup_session.py` so `select_signature_preset()` builds its prompt label from the new coordinator helper and remove the private `_certificate_configuration_name_for_preset()` catalog walk. Keep `_run_with_manual_certificate_password_retry(...)`, passphrase caching, and actual preset application behavior exactly as they are today.

Finally, add narrow tests. In `tests/unit/test_signature_properties_coordinator.py`, add direct coverage for the new helper across the resolved name and `None` fallback cases. In `tests/unit/test_signing_setup_session.py`, keep the existing preset retry/caching test and assert that the prompt text still names the certificate display name. Do not add new Qt shell coverage for this slice.

## Concrete Steps

Work from `/home/daekar/FoliaSeal`.

1. Edit `src/foliaseal/application/signature_properties_coordinator.py` to add the read-only preset certificate display-name helper.
2. Edit `src/foliaseal/application/signing_setup_session.py` so `select_signature_preset()` uses that helper and delete the redundant private catalog lookup method.
3. Edit `tests/unit/test_signature_properties_coordinator.py` and `tests/unit/test_signing_setup_session.py` to add focused coverage for the new helper and preserve the prompt-label behavior.
4. Run:

       pytest tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py

   The run completed successfully with `35 passed in 0.30s`.
5. Run the architecture/spec compliance review and record whether this commit remains aligned with `docs/ARCHITECTURE.md` and `docs/SPEC.md`.

## Validation and Acceptance

Acceptance is behavior-focused. After the change, selecting a preset that references a certificate must still prompt with the certificate display name when manual password entry is required, and selecting a preset with no resolvable certificate must still fall back to the generic prompt. A direct coordinator unit test must show that the new helper returns the expected certificate display name when the preset and certificate exist and `None` otherwise. Running

    pytest tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py

must succeed from the repository root. It did: `35 passed in 0.30s`.

## Idempotence and Recovery

These edits are safe to repeat because they only narrow a read-only lookup boundary and update unit tests. If a test fails midway, re-run the same `pytest` command after finishing the remaining edits. If the new helper proves insufficient, prefer expanding its internal lookup logic rather than reintroducing direct catalog access in `SigningSetupSession`.

## Artifacts and Notes

Expected validation transcript shape after implementation:

    $ pytest tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py
    ...
    35 passed in 0.30s

Passing transcript:

    $ pytest tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py
    ============================= test session starts ==============================
    platform linux -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0
    rootdir: /home/daekar/FoliaSeal
    configfile: pyproject.toml
    collected 35 items

    tests/unit/test_signature_properties_coordinator.py .................... [ 57%]
    ....                                                                     [ 68%]
    tests/unit/test_signing_setup_session.py ...........                     [100%]

    ============================== 35 passed in 0.30s ==============================

Compliance review notes: no conflicts were identified with `docs/ARCHITECTURE.md` or `docs/SPEC.md`; the slice remains a narrow application-layer boundary change.

## Interfaces and Dependencies

In `src/foliaseal/application/signature_properties_coordinator.py`, define a public method on `DefaultSignaturePropertiesCoordinator` with a stable narrow interface:

    def certificate_configuration_name_for_preset(
        self,
        preset_name: str,
    ) -> str | None:
        ...

This method must be read-only and must not mutate workflow state, selection state, or catalogs. It may inspect `self.preset_catalog` and `self.certificate_catalog`.

`src/foliaseal/application/signing_setup_session.py` must continue exposing:

    def select_signature_preset(...) -> SigningSetupSelectionOutcome

but after this slice it should depend on the coordinator query above instead of its own private catalog traversal helper.

Revision note: Created on 2026-06-25 by Codex after the required `explorer-light` dev-loop review identified the preset-certificate prompt-label lookup as the next smallest hybrid seam.
