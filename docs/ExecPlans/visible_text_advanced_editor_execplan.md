# Completed: move the visible-text field matrix behind an advanced editor

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` are now in completion state and record what was delivered, what was observed, and how it was validated.

This document is maintained in accordance with [.agents/skills/write-execplan/PLANS.md](/home/daekar/FoliaSeal/.agents/skills/write-execplan/PLANS.md).

## Purpose / Big Picture

This slice is complete. The default visible-signature setup path in the production GUI is simpler: a user setting up a visible approval signature can still choose presets, configure the visible signature, place it on the page, preview it, and sign it, but the dense eight-row field matrix for visible text no longer dominates the main path. Those low-level field controls now live behind a secondary advanced surface, which keeps the flow aligned with [docs/SPEC.md](/home/daekar/FoliaSeal/docs/SPEC.md) and its document-centric, preset-first guidance.

The implemented user-visible behavior is straightforward. In the signing sidebar, the main `Visible signature` area shows the primary style controls, keeps `Show field names` visible, and includes a concise visible-text summary. The detailed field matrix appears only after the user explicitly opens the advanced text editor. Preview and signing behavior are unchanged.

## Child ExecPlan Dependencies

- [x] The visible-signature setup coordinator deepening slice is complete in [visible_signature_setup_coordinator_execplan.md](/home/daekar/FoliaSeal/docs/ExecPlans/visible_signature_setup_coordinator_execplan.md).
- [x] The Qt visible-signature setup form extraction slice is complete in [qt_visible_signature_setup_form_execplan.md](/home/daekar/FoliaSeal/docs/ExecPlans/qt_visible_signature_setup_form_execplan.md).
- [x] No child ExecPlans are required for this narrow product-surface simplification.

## Progress

- [x] Requested an `explorer-light` audit of the next highest-value de-harnessing slice before planning.
- [x] Reviewed the explorer findings and selected the narrow slice: move the per-field visible-text matrix behind a secondary advanced editor while preserving setup-draft parity.
- [x] Implemented the advanced visible-text editor surface in the extracted Qt setup form and kept the main `Visible signature` path concise.
- [x] Updated focused fake-Qt tests and shell integration expectations for the new structure.
- [x] Ran validation, reviewed the result against `docs/SPEC.md` and `docs/ARCHITECTURE.md`, and updated the docs for completion.

## Surprises & Discoveries

- Observation: the remaining density was concentrated in the visible-text field matrix, not in placement or preview.
  Evidence: the extracted Qt setup form keeps `Show field names` in the main path, adds a summary/detail copy pair for visible text, and hides the eight per-field rows behind an explicit advanced editor toggle.

- Observation: the advanced surface stayed fake-Qt friendly without changing the draft contract.
  Evidence: the new editor boundary remains inside `src/foliaseal/presentation/qt/visible_signature_setup_form.py`, and `load()` / `build_draft()` still round-trip the same `VisibleSignatureSetupDraft` shape.

- Observation: [docs/SPEC.md](/home/daekar/FoliaSeal/docs/SPEC.md) explicitly allows low-level controls to move into secondary views as long as the end-to-end signing story remains intact.
  Evidence: the spec says V1 may "aggressively simplify and reorganize the current GUI" and that some low-level controls may "move into secondary views."

## Decision Log

- Decision: keep this slice entirely in the Qt presentation layer.
  Rationale: the coordinator and draft shape were already in the right place. The problem here was presentation density, not application semantics.
  Date/Author: 2026-05-24 / Codex

- Decision: preserve `VisibleSignatureSetupDraft` load/build parity exactly in this slice.
  Rationale: hiding the field matrix must not silently change what data can be edited or how preview/signing semantics are derived.
  Date/Author: 2026-05-24 / Codex

- Decision: keep `Show field names` visible in the main path while moving the detailed per-field source/override rows behind an advanced surface.
  Rationale: that kept the common visible-text toggle close to the main workflow while pushing the low-level matrix out of the default path.
  Date/Author: 2026-05-24 / Codex

## Outcomes & Retrospective

The slice is complete. The signing sidebar now keeps `Show field names` visible in the default visible-signature path while moving the per-field visible-text matrix behind an explicit advanced editor in `visible_signature_setup_form.py`. The main section now reads as a concise setup surface instead of an always-expanded field editor, and the underlying draft mapping, field enablement rules, preview behavior, and signing behavior remain intact.

Validation evidence:

- `pytest tests/unit/test_qt_visible_signature_setup_form.py tests/unit/test_qt_signing_shell.py` -> `73 passed`
- `ruff check src/foliaseal/presentation/qt/visible_signature_setup_form.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_visible_signature_setup_form.py tests/unit/test_qt_signing_shell.py` -> `All checks passed!`
- `git diff --check` -> no whitespace or patch-format errors

## Context and Orientation

The current production signing UI is assembled in [src/foliaseal/presentation/qt/signing_shell.py](/home/daekar/FoliaSeal/src/foliaseal/presentation/qt/signing_shell.py), but raw visible-signature setup controls live in [src/foliaseal/presentation/qt/visible_signature_setup_form.py](/home/daekar/FoliaSeal/src/foliaseal/presentation/qt/visible_signature_setup_form.py). That extracted Qt form owns widget construction, state loading, draft building, field-source enablement rules, and font-style availability rules, and it also owns the advanced visible-text disclosure that hides the per-field matrix behind an explicit toggle.

The main signing path required by [docs/SPEC.md](/home/daekar/FoliaSeal/docs/SPEC.md) is document-centric and preset-first: open a PDF, review it, choose or assemble a signing setup, place a visible approval signature, preview readiness, sign, save, and verify. The default confirmation/setup experience stays simple and unintimidating, and low-level controls can move into secondary views.

In the implemented state, the main `Visible signature` section contains:

- the `Signature style` controls,
- the `Show field names` toggle,
- concise visible-text summary text,
- and an explicit advanced editor toggle that reveals the eight per-field rows for `Distinguished name`, `Common name`, `Email`, `Title`, `Company`, `Signing time`, `Reason`, and `Location`.

That structure keeps the common path readable without removing access to per-field editing.

## Completed Work

The implementation kept the form contract stable. `load()` still populates all field controls. `build_draft()` still reads all field controls. The field-source enablement rules still work. The only behavior change is which controls are visible by default.

The Qt form now uses an explicit advanced editor surface for the field rows. `Show field names` remains in the default path, the visible-text summary stays concise, and the per-field matrix is hidden until the user opens the advanced editor.

The focused tests cover the new boundary directly, including draft parity, initial collapsed state, explicit expansion, and the fact that toggling the advanced editor does not itself emit a draft-change callback.

## Validation Summary

From `/home/daekar/FoliaSeal`, the following checks passed:

    pytest tests/unit/test_qt_visible_signature_setup_form.py tests/unit/test_qt_signing_shell.py
    ruff check src/foliaseal/presentation/qt/visible_signature_setup_form.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_visible_signature_setup_form.py tests/unit/test_qt_signing_shell.py
    git diff --check

## Validation and Acceptance

Acceptance was behavioral:

- the visible-signature setup form still round-trips `VisibleSignatureSetupDraft`;
- the field rows still affect preview/signing semantics after opening the advanced editor;
- the main setup path is visually simpler because the field matrix is no longer always expanded;
- focused fake-Qt form and shell tests passed;
- `ruff check` and `git diff --check` passed.

The most important regression to avoid was silently losing access to per-field source or override editing. Those controls still exist and are exercised by tests.

## Idempotence and Recovery

This slice is safe to repeat. If the advanced surface ever needs to be revisited, the fallback remains to keep the extracted setup form module but restore the always-expanded visible-text section without changing the coordinator or draft interfaces. No persisted data migration is involved.

## Artifacts and Notes

Post-change evidence:

    `Visible signature` currently contains:
    - summary copy
    - `Signature style`
    - `Visible text`
      - `Show field names`
      - concise visible-text summary
      - advanced editor toggle
      - 8 per-field rows hidden by default

This is the simplified setup-surface density delivered by the slice.

## Interfaces and Dependencies

This slice stays within the existing local-substitutable Qt presentation boundaries:

- `QtVisibleSignatureSetupForm` in `src/foliaseal/presentation/qt/visible_signature_setup_form.py` remains the producer of visible-signature form widgets and draft mapping.
- `SignaturePropertiesPanel` in `src/foliaseal/presentation/qt/signing_shell.py` remains the consumer of that form boundary.
- `VisibleSignatureSetupDraft` and coordinator command/state types in `src/foliaseal/application/signature_properties_coordinator.py` did not change shape in this slice.

The form still exposes:

- `visible_signature_controls`
- `visible_text_controls`
- `field_controls`
- `load(draft)`
- `build_draft()`
- change and page-change callback behavior

The advanced editor toggle lives inside `VisibleTextControls` so the boundary remains coherent.

Revision note: completed on 2026-05-24 after the advanced visible-text editor slice, validation, and documentation update.
