# Clean Up Signing Setup Preset Vocabulary

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with [/home/daekar/FoliaSeal/.agents/skills/write-execplan/PLANS.md](/home/daekar/FoliaSeal/.agents/skills/write-execplan/PLANS.md).

## Purpose / Big Picture

After this change, the signing setup sidebar will use preset-specific vocabulary consistently in both its user-visible error handling and its internal Qt control surface. Users will see `Signature preset error` when preset application fails, instead of a certificate-specific error label, and the Qt shell will no longer carry `profile_*` compatibility aliases for preset controls. This is a small slice, but it directly improves MVP polish and keeps the production UI aligned with the canonical `SignaturePreset` language in `docs/SPEC.md` and `docs/SCHEMAS.md`.

The change is observable by running the preset-selection shell tests and by forcing preset application failure in the fake-Qt shell: the dialog title must say `Signature preset error`, and preset controls must only expose `preset_*` names.

## Child ExecPlan Dependencies

- [ ] No child ExecPlans are required for this slice.

## Progress

- [x] 2026-05-26 18:04 EDT: Completed the narrow preset-vocabulary cleanup change in `src/foliaseal/presentation/qt/signing_shell.py`.
- [x] 2026-05-26 18:04 EDT: Updated focused shell tests in `tests/unit/test_qt_signing_shell.py` to prove the corrected error path and removal of profile-era aliases.
- [x] 2026-05-26 18:04 EDT: Reviewed compliance against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and `docs/SCHEMAS.md`; no doc updates were required for this slice.
- [x] 2026-05-26 18:04 EDT: Validated with focused pytest, `ruff check`, and `git diff --check`.
- [x] 2026-05-26 18:08 EDT: Committed the slice after implementation, compliance review, and documentation updates were complete.

## Surprises & Discoveries

- Preset-selection failures should not emit the certificate-path `on_error` side effect. The failure path now uses the preset-specific error helper directly, so the dialog title matches the preset vocabulary and the certificate configuration error path remains reserved for certificate setup failures.

## Decision Log

- Decision: Keep this slice narrow and remove only the remaining preset-path vocabulary drift rather than mixing in broader setup-surface simplification.
  Rationale: The user asked to keep driving toward MVP and to rip out non-compliant cruft. The remaining `profile_*` aliases and certificate-branded preset error path are direct vocabulary drift against the current spec/schema model, and they can be removed safely without reopening the broader setup-form redesign.
  Date/Author: 2026-05-26 / Codex

## Outcomes & Retrospective

- The slice is complete and stays narrowly scoped to the preset vocabulary cleanup. The shell now presents preset failures with preset language, and the Qt surface no longer needs the old profile-era alias names for preset controls.

- Validation already ran cleanly:
  - `pytest tests/unit/test_qt_signing_shell.py -q` -> `77 passed`
  - `ruff check src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py` -> passed
  - `git diff --check` -> passed

- The key follow-up insight was that preset errors should not flow through the certificate-path `on_error` side effect. Keeping that path separate preserves the certificate error semantics and avoids reintroducing vocabulary drift.

## Context and Orientation

The signing setup sidebar lives in `src/foliaseal/presentation/qt/signing_shell.py`. Inside `SignaturePropertiesPanel`, `_build_signature_preset_controls()` constructs the preset-selection Qt controls and currently adds legacy `profile_combo` and `profile_name` attributes onto the `SignaturePresetControls` value. Those aliases are not part of the current schema vocabulary and exist only as compatibility carryover from earlier profile-centric naming.

Preset application also lives in the same module. `_on_signature_preset_selected()` dispatches nonblank selections through `DefaultSignaturePropertiesCoordinator.apply_signature_preset(...)`, but its failure path still reports errors through `_show_certificate_configuration_error(...)`. That produces the wrong dialog title when preset application fails.

The canonical product language is already clear elsewhere in the repository. `docs/SPEC.md` describes the staged V1 flow as `Open -> Review -> Choose preset/certificate -> Place -> Preview readiness -> Sign -> Save -> Verify` and treats visible approval signatures plus reusable signing setups as the main path. `docs/SCHEMAS.md` defines `SignaturePreset` as the reusable signing object that can optionally reference certificate, appearance, and placement objects. This slice keeps the shell aligned with those documents.

The tests that cover this area live in `tests/unit/test_qt_signing_shell.py`. They use fake Qt bindings and fake viewer widgets, so behavior is validated through dialog-call capture and control inspection rather than through a live GUI.

## Plan of Work

Edit `src/foliaseal/presentation/qt/signing_shell.py` in two places. First, in `_build_signature_preset_controls()`, return `SignaturePresetControls` directly without attaching `profile_combo` or `profile_name`. Second, in `_on_signature_preset_selected()`, change the `SignaturePropertiesCoordinatorError` branch to call `_show_signature_preset_error(...)` before reloading current state. Do not change the coordinator, form draft handling, or blank-selection behavior.

Then update `tests/unit/test_qt_signing_shell.py`. Adjust the preset-selection error regression so it expects `Signature preset error` instead of `Certificate configuration error`. Add a focused assertion that the preset controls no longer expose `profile_combo` or `profile_name`. Keep the existing certificate error tests unchanged so the certificate path remains separately verified.

If the compliance review shows that `docs/ARCHITECTURE.md` still describes profile-era aliases or misses the corrected preset error path, update that document and record the completed state in this ExecPlan.

## Concrete Steps

From `/home/daekar/FoliaSeal`, make the code change, run the focused validations, and inspect the worktree.

Expected commands:

    pytest tests/unit/test_qt_signing_shell.py
    ruff check src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py
    git diff --check

Expected outcomes:

    - the preset-selection error regression passes with the dialog title `Signature preset error`
    - the new alias-removal assertion passes
    - `ruff check` reports no issues
    - `git diff --check` reports no whitespace or merge-marker problems

## Validation and Acceptance

Acceptance is entirely behavior-focused for this slice.

Run `pytest tests/unit/test_qt_signing_shell.py` from `/home/daekar/FoliaSeal` and expect the suite to pass. The specific regression `test_signing_shell_signature_preset_selection_error_reloads_current_state` must prove that preset failures surface a `Signature preset error` dialog while still reloading current state. A focused assertion must also prove that `SignaturePresetControls` no longer exposes `profile_combo` or `profile_name`.

Run `ruff check src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py` and expect a clean pass. Run `git diff --check` and expect no output.

If `docs/ARCHITECTURE.md` changes, it must describe the new steady state accurately: preset handling should be referred to only with preset terminology, not profile terminology.

## Idempotence and Recovery

This slice is safe to repeat. Re-running the tests and lint command should be harmless. If an edit goes wrong, re-open the targeted functions in `src/foliaseal/presentation/qt/signing_shell.py` and restore the intended steady state: preset controls expose only preset names, preset failures use the preset error helper, and certificate failures continue using the certificate error helper.

## Artifacts and Notes

The most important evidence for this slice is expected to be short and test-driven:

    pytest tests/unit/test_qt_signing_shell.py -q
    77 passed

    ruff check src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py
    passed

    git diff --check
    passed

## Interfaces and Dependencies

This slice must leave the public setup boundary untouched. The coordinator entrypoints remain:

    DefaultSignaturePropertiesCoordinator.apply_visible_setup(...)
    DefaultSignaturePropertiesCoordinator.apply_signature_preset(...)
    DefaultSignaturePropertiesCoordinator.apply_certificate_configuration(...)
    DefaultSignaturePropertiesCoordinator.reconcile(...)

Within `src/foliaseal/presentation/qt/signing_shell.py`, `SignaturePropertiesPanel._on_signature_preset_selected()` must still dispatch nonblank selections through `apply_signature_preset(...)` and blank selections through `ClearSelectedSignaturePreset()`. The only behavior change there is which UI error helper is used on preset failures.

The `SignaturePresetControls` value returned by `_build_signature_preset_controls()` must expose:

    container
    preset_combo
    preset_name
    save_button
    delete_button

It must no longer expose `profile_combo` or `profile_name`.

Revision note: Created on 2026-05-26 to drive the narrow preset-vocabulary cleanup slice identified by the current dev-loop explorer review.
