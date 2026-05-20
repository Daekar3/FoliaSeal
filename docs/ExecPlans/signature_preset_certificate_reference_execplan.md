# Preserve certificate references in signature presets

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

FoliaSeal lets users save a reusable signature preset, which is a named bundle of signing setup choices. The governing schema in `docs/SCHEMAS.md` says a preset may include a certificate configuration reference, and it also says loading a preset that does not include a certificate reference must leave the user's current certificate selection alone. Today the persisted schema can store that reference, but the save and load workflow does not handle it correctly. After this change, saving a preset while a certificate configuration is active records that configuration, loading such a preset restores it, and loading an older or partial preset without a certificate reference does not clear the user's active certificate.

The behavior is demonstrated by focused tests in the schema, workflow, and Qt signing-shell test suites. A user-visible path is: select a certificate configuration, save a signature preset, change or reload the shell, and select the preset; the preset keeps its certificate reference. If a preset only contains appearance or placement choices, selecting it changes those choices without wiping the currently selected certificate.

## Child ExecPlan Dependencies

- [x] Governing schema exists in `docs/SCHEMAS.md` and documents optional `SignaturePreset.certificate_configuration_id`.
- [x] Explorer-light audit confirmed the current save/apply paths do not comply with that schema.
- [x] Existing `SignaturePreset` dataclass already serializes `certificate_configuration_id`; this slice can be limited to threading and preservation behavior.

## Progress

- [x] (2026-05-20 22:28Z) Spawned an `explorer-light` subagent to inspect preset schema, workflow, UI, and tests.
- [x] (2026-05-20 22:28Z) Reviewed `PLANS.md` and created this ExecPlan.
- [x] (2026-05-20 22:31Z) Added focused failing tests for preset certificate reference capture and partial-preset preservation across schema, workflow, and Qt shell paths.
- [x] (2026-05-20 22:33Z) Implemented the minimal schema/workflow changes needed to pass the tests.
- [x] (2026-05-20 22:34Z) Ran focused validation: `pytest tests/unit/test_config_schemas.py tests/unit/test_signing_draft_workflow.py tests/unit/test_qt_signing_shell.py` reported `114 passed in 9.05s`.
- [x] (2026-05-20 22:35Z) Ran focused lint: `ruff check src/foliaseal/infra/config/schemas.py src/foliaseal/application/signing_draft_workflow.py tests/support/phase3_builders.py tests/unit/test_config_schemas.py tests/unit/test_signing_draft_workflow.py tests/unit/test_qt_signing_shell.py` reported `All checks passed!`.
- [x] (2026-05-20 22:36Z) Committed the first pass as `0ef3512fb fix: preserve certificate refs in signature presets`.
- [x] (2026-05-20 22:38Z) Ran two-agent compliance review. One reviewer found no issues; the second found that Qt preset selection restored the certificate id but did not resolve runtime signing material, and that architecture docs omitted the optional certificate reference.
- [x] (2026-05-20 22:45Z) Added follow-up regression coverage and implementation for preset selection applying certificate material.
- [x] (2026-05-20 22:46Z) Ran follow-up focused validation: `pytest tests/unit/test_config_schemas.py tests/unit/test_signing_draft_workflow.py tests/unit/test_qt_signing_shell.py` reported `115 passed in 10.76s`.
- [x] (2026-05-20 22:46Z) Ran follow-up focused lint: `ruff check docs/ExecPlans/signature_preset_certificate_reference_execplan.md docs/ARCHITECTURE.md src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py` reported `All checks passed!`.
- [x] (2026-05-20 22:47Z) Committed the compliance follow-up as `4161bb9d fix: apply preset certificate material`.
- [x] (2026-05-20 22:50Z) Ran final two-agent compliance review. One reviewer found no issues; the other found only this ExecPlan status drift, which this closeout update resolves.

## Surprises & Discoveries

- Observation: The `SignaturePreset` schema object already stores and round-trips `certificate_configuration_id`.
  Evidence: `src/foliaseal/infra/config/schemas.py` defines the field on `SignaturePreset` and includes it in `from_dict()` and `to_dict()`.

- Observation: The missing behavior is split across save and apply paths, not storage.
  Evidence: `SigningDraftWorkflow.capture_current_signature_setup()` calls `ResolvedSignaturePreset.from_parts()` without passing the active certificate id, while `apply_resolved_signature_preset()` unconditionally assigns the nullable preset field back into the workflow.

- Observation: Restoring the certificate id alone is insufficient for signing.
  Evidence: Compliance review noted that `SigningDraftWorkflow.build_signing_request()` uses `certificate_path` and `passphrase`, so Qt preset selection must also resolve the referenced certificate configuration into runtime signing material.

## Decision Log

- Decision: Keep this slice limited to preset certificate-reference semantics.
  Rationale: The audit also found overwrite confirmation and stale README issues, but the preset bug is the highest-severity docs compliance issue and can be fixed independently with a narrow behavior-change commit.
  Date/Author: 2026-05-20 / Codex

- Decision: Treat a missing preset certificate reference as “do not change the current certificate” during apply.
  Rationale: `docs/SCHEMAS.md` explicitly defines partial preset load semantics this way, and it preserves compatibility with older presets that predate certificate references.
  Date/Author: 2026-05-20 / Codex

- Decision: When Qt preset selection includes a certificate reference, resolve and apply the referenced certificate configuration before applying the rest of the preset.
  Rationale: Applying the certificate through the same resolver used by the explicit Apply button keeps the signing draft's certificate path, passphrase, alias, selected id, and combo state coherent. Applying it before the visual preset keeps failure behavior safe: if certificate resolution fails, the visual preset is not partially applied.
  Date/Author: 2026-05-20 / Codex

## Outcomes & Retrospective

This plan is complete. New tests prove that captured presets include the active certificate id, that partial presets without a certificate id preserve the active certificate selection, and that the Qt signing shell stores and reapplies the reference through its existing preset controls.

The first implementation pass was committed as `0ef3512fb` and focused validation passed. Compliance review found that the first pass restored the certificate id but not the runtime signing material in the Qt shell. The follow-up implementation was committed as `4161bb9d`; it resolves and applies the referenced certificate configuration during preset selection, updates the architecture contract text, and passes focused validation. Final compliance review found no remaining behavior or documentation issues for this slice after this status closeout.

## Context and Orientation

A certificate configuration is a saved signing identity entry stored in the certificate catalog. The signing draft workflow keeps the currently selected certificate configuration id in `SigningDraftWorkflow.selected_certificate_configuration_id`. A signature preset is a reference-only saved object in `SignaturePresetCatalog`; it points to reusable appearance and placement profiles and may also point to a certificate configuration.

The main files for this slice are:

`src/foliaseal/infra/config/schemas.py` defines `SignaturePreset`, `ResolvedSignaturePreset`, and helper constructors used when the UI saves a preset.

`src/foliaseal/application/signing_draft_workflow.py` owns the draft state. `capture_current_signature_setup()` turns the current draft into a `ResolvedSignaturePreset`, and `apply_resolved_signature_preset()` applies one back to the draft.

`src/foliaseal/presentation/qt/signing_shell.py` wires the Qt preset controls to those workflow methods. The shell should not need broad rewrites if the workflow methods behave correctly.

The relevant tests are `tests/unit/test_config_schemas.py`, `tests/unit/test_signing_draft_workflow.py`, and `tests/unit/test_qt_signing_shell.py`.

## Plan of Work

First, add regression tests. In `tests/unit/test_config_schemas.py`, strengthen the reference-only preset round-trip test so it proves `certificate_configuration_id` is persisted alongside appearance and placement references. In `tests/unit/test_signing_draft_workflow.py`, update the capture/apply test to set `selected_certificate_configuration_id` before capture and assert the captured preset includes it. Add a second workflow test that starts with an active certificate id, applies a preset with no certificate id, and verifies the active id remains unchanged. In `tests/unit/test_qt_signing_shell.py`, extend the preset save/reload round-trip to configure a certificate catalog, select a certificate configuration, save a preset, and verify the stored preset includes the certificate id and applying the saved preset restores that id. If practical, add a Qt-shell assertion that applying an existing preset without a certificate id does not clear a selected certificate.

Then implement the minimal code change. In `src/foliaseal/infra/config/schemas.py`, add an optional `certificate_configuration_id` keyword to `SignaturePreset.from_profile_parts()` and `ResolvedSignaturePreset.from_parts()`, and pass it into the created `SignaturePreset`. In `src/foliaseal/application/signing_draft_workflow.py`, pass `self.selected_certificate_configuration_id` into `ResolvedSignaturePreset.from_parts()` during capture. In `apply_resolved_signature_preset()`, only assign `self.selected_certificate_configuration_id` when `preset.preset.certificate_configuration_id` is not `None`.

Finally, run focused tests. If those pass, run the broader preset/certificate-adjacent tests. Keep this plan updated with exact command results.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Run focused tests while iterating:

    pytest tests/unit/test_config_schemas.py tests/unit/test_signing_draft_workflow.py tests/unit/test_qt_signing_shell.py

Before committing the slice, run:

    ruff check src/foliaseal/infra/config/schemas.py src/foliaseal/application/signing_draft_workflow.py tests/unit/test_config_schemas.py tests/unit/test_signing_draft_workflow.py tests/unit/test_qt_signing_shell.py
    pytest tests/unit/test_config_schemas.py tests/unit/test_signing_draft_workflow.py tests/unit/test_qt_signing_shell.py

## Validation and Acceptance

Acceptance requires tests proving three behaviors. Saving a preset while `SigningDraftWorkflow.selected_certificate_configuration_id` is set produces a `SignaturePreset` whose `certificate_configuration_id` matches the active id. Applying a preset with a certificate id sets the workflow to that id. Applying a preset without a certificate id preserves the workflow's existing selected certificate id.

Qt-shell acceptance requires the UI save path to store the selected certificate id in the catalog and the UI load path to leave the selected certificate intact when the preset omits the field. The focused test command must pass without failures.

The compliance follow-up adds one more acceptance condition: selecting a preset with a different certificate reference must update `SigningDraftWorkflow.certificate_path` and `SigningDraftWorkflow.passphrase` to the referenced certificate configuration's resolved material, not only update `selected_certificate_configuration_id`.

## Idempotence and Recovery

The implementation is additive and safe to rerun. Tests use temporary directories and fake Qt controls, so they do not mutate user configuration. If a test edit fails, revert only the files touched by this slice or adjust the tests to match the documented schema behavior. Do not change unrelated certificate lifecycle, signing backend, or packaging behavior in this slice.

## Artifacts and Notes

Explorer-light audit summary:

    SignaturePreset already models an optional certificate_configuration_id, but saving a preset drops the active certificate reference and loading a preset with no certificate reference clears the current certificate. SignaturePresetCatalogStore persists whatever it receives, so the fix belongs in capture/apply threading.

## Interfaces and Dependencies

`SignaturePreset.from_profile_parts()` should accept:

    certificate_configuration_id: str | None = None

`ResolvedSignaturePreset.from_parts()` should accept the same optional keyword and pass it through to `SignaturePreset.from_profile_parts()`.

`SigningDraftWorkflow.capture_current_signature_setup()` should call `ResolvedSignaturePreset.from_parts()` with `certificate_configuration_id=self.selected_certificate_configuration_id`.

`SigningDraftWorkflow.apply_resolved_signature_preset()` should leave `selected_certificate_configuration_id` unchanged when the preset has `certificate_configuration_id is None`; otherwise it should set the workflow field to the preset value.

## Revision Notes

- 2026-05-20: Created plan from the governing-docs audit and explorer-light implementation review.
- 2026-05-20: Updated progress and outcomes after adding tests, implementing the preset certificate-reference fix, and running focused pytest successfully.
- 2026-05-20: Updated progress after focused lint passed.
- 2026-05-20: Updated progress, discoveries, decision log, and acceptance criteria after compliance review found that preset certificate references also need to apply runtime signing material.
- 2026-05-20: Updated progress and outcomes after the compliance follow-up implementation passed focused pytest and lint.
- 2026-05-20: Closed the plan status after committing the compliance follow-up and running final two-agent compliance review.
