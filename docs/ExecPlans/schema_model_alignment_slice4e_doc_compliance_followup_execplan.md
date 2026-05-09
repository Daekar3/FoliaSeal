# Schema Model Alignment Slice 4E Documentation Compliance Follow-Up

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this follow-up, the Slice 4E ExecPlan will describe the repository as it exists after commit `08feda1`, not as it existed before implementation. The behavior is already correct: app-wide default-directory editing lives in the app-frame settings dialog, and the signing shell only consumes `AppSettings` for output defaults. This small documentation-only slice removes stale present-tense wording from the Slice 4E plan so a future contributor can use it as an accurate restart/audit document.

## Child ExecPlan Dependencies

- [x] Slice 4E implementation commit `08feda1` exists and removed the duplicate signing-shell settings controls.
- [x] Compliance review identified stale wording in `docs/ExecPlans/schema_model_alignment_slice4e_remove_shell_settings_execplan.md`.

## Progress

- [x] (2026-05-09T13:03Z) Created this follow-up ExecPlan from the second compliance review finding.
- [x] (2026-05-09T13:03Z) Rewrote stale Slice 4E wording so observations and context distinguish pre-change evidence from current state.
- [x] (2026-05-09T13:03Z) Ran a focused documentation consistency search and confirmed remaining removed-symbol matches are historical evidence, removal instructions, or validation search terms.
- [x] (2026-05-09T13:03Z) Committed the documentation compliance follow-up as `fd0f5bc Clarify slice 4E plan state`.
- [x] (2026-05-09T13:03Z) Addressed re-review finding that the Slice 4E purpose still said the removed panel editor "currently" lets users edit defaults.
- [x] (2026-05-09T13:03Z) Received explicit user approval to update frozen `docs/SCHEMAS.md` and replaced the stale implementation-drift wording.

## Surprises & Discoveries

- Observation: the first Slice 4E commit correctly removed the settings editor from code, but the new plan still contained present-tense pre-change wording.
  Evidence: the compliance review reported that `docs/ExecPlans/schema_model_alignment_slice4e_remove_shell_settings_execplan.md` said `signing_shell.py` still defines `AppSettingsControls`, `_app_settings_controls`, `save_app_settings()`, and `_load_app_settings_controls()` even though those names no longer exist in `src/foliaseal/presentation/qt/signing_shell.py`.

- Observation: the second compliance review found one additional stale word in the Slice 4E purpose statement.
  Evidence: `docs/ExecPlans/schema_model_alignment_slice4e_remove_shell_settings_execplan.md` said the removed side-panel `Settings` group "currently lets users edit" app defaults after commit `08feda1` had already removed it.

- Observation: a compliance review also identified stale implementation-drift wording in frozen `docs/SCHEMAS.md`.
  Evidence: `docs/SCHEMAS.md` says the current code still has a `SignaturePreset` schema that behaves like an appearance-profile store, while current `src/foliaseal/infra/config/schemas.py` has reference-only `SignaturePreset` plus split appearance and placement profile catalogs.

- Observation: the user explicitly approved the proposed `docs/SCHEMAS.md` wording before the file was edited.
  Evidence: user message: "THe proposed changes to SCHEMAS.md are approved. Make that specific change."

## Decision Log

- Decision: fix the stale Slice 4E plan directly rather than changing product docs or implementation.
  Rationale: the compliance issue is documentation-only and does not indicate product/spec/schema mismatch. The correct fix is to make the living ExecPlan accurately describe before/after state.
  Date/Author: 2026-05-09 / Codex

- Decision: do not edit `docs/SCHEMAS.md` without explicit user permission.
  Rationale: `docs/SCHEMAS.md` has a Document Governance section that says no changes may be made without explicit user permission. The stale drift wording is real, but the file is frozen.
  Date/Author: 2026-05-09 / Codex

- Decision: update only the `Current Implementation Drift` section of `docs/SCHEMAS.md`.
  Rationale: the user approved the specific proposed language, and the compliance issue was limited to that stale drift section.
  Date/Author: 2026-05-09 / Codex

## Outcomes & Retrospective

At creation time, this follow-up was expected to be documentation-only. It met that scope: the Slice 4E plan now describes pre-change evidence as pre-change evidence, records commit `08feda1` as the implementation, no longer claims removed panel settings controls exist in current code, and the frozen `docs/SCHEMAS.md` drift section was updated after explicit user approval.

## Context and Orientation

The relevant implementation is in `src/foliaseal/presentation/qt/signing_shell.py`. After Slice 4E, `SignaturePropertiesPanel` no longer has an `AppSettingsControls` dataclass, `_app_settings_controls` attribute, `save_app_settings()` method, `_build_app_settings_controls()` method, or `_load_app_settings_controls()` method. `SigningWorkspaceWidget` still keeps app settings and uses them for the output save dialog.

The stale documentation is in `docs/ExecPlans/schema_model_alignment_slice4e_remove_shell_settings_execplan.md`. That file should remain useful as a living plan: its early observations may mention pre-change evidence, but they must clearly say that evidence was pre-change and must not describe removed code as current.

## Plan of Work

Edit only `docs/ExecPlans/schema_model_alignment_slice4e_remove_shell_settings_execplan.md` and this follow-up plan unless validation finds another stale documentation reference introduced by Slice 4E. Change current-state paragraphs to completed-state language. Remove or narrow the sentence about keeping `on_app_settings_change` constructor flow in `SignaturePropertiesPanel`, because the panel no longer owns that callback.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Run the focused search:

    rg -n "still defines|still builds|on_app_settings_change|AppSettingsControls|_app_settings_controls|save_app_settings|_load_app_settings_controls" docs/ExecPlans/schema_model_alignment_slice4e_remove_shell_settings_execplan.md src/foliaseal/presentation/qt/signing_shell.py

Expected outcome: no current-state stale claim remains. Historical removed-symbol references may remain in the plan if they are explicitly described as pre-change evidence, removal instructions, or validation search terms.

## Validation and Acceptance

This follow-up is accepted when the Slice 4E plan no longer states that removed signing-shell settings controls currently exist, and when `git diff --check` passes. No Python tests are required because this is documentation-only and the previous implementation commit already passed focused tests, Ruff, and the full unit suite.

## Idempotence and Recovery

The edits are documentation-only and can be repeated safely. If the search still finds stale current-state wording, rewrite the sentence to clarify whether it describes pre-change evidence, desired removal, or completed behavior.

## Artifacts and Notes

No generated artifacts are expected.

Validation transcript:

    rg -n "still defines|still builds|on_app_settings_change|AppSettingsControls|_app_settings_controls|save_app_settings|_load_app_settings_controls" docs/ExecPlans/schema_model_alignment_slice4e_remove_shell_settings_execplan.md src/foliaseal/presentation/qt/signing_shell.py
    <matches only for completed progress, pre-change evidence, removal instructions, validation commands, and idempotence guidance>

    git diff --check
    <no output>

Revision note: Created 2026-05-09 by Codex to address compliance-review documentation staleness after Slice 4E implementation.

Revision note: Updated 2026-05-09 by Codex after fixing the stale Slice 4E plan wording and running the focused consistency search.

Revision note: Updated 2026-05-09 by Codex after the re-review found one remaining stale "currently" phrase and a frozen `docs/SCHEMAS.md` drift note that requires explicit user permission before editing.

Revision note: Updated 2026-05-09 by Codex after the user explicitly approved the proposed `docs/SCHEMAS.md` replacement text and the stale drift section was updated.
