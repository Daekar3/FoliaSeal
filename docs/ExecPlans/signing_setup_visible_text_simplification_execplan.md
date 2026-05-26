# Simplify Signing Setup Visible Text Surface

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document is maintained in accordance with [/home/daekar/FoliaSeal/.agents/skills/write-execplan/PLANS.md](/home/daekar/FoliaSeal/.agents/skills/write-execplan/PLANS.md).

This slice is complete. The record below describes the final implementation, the validation that was run, and the lessons learned.

## Purpose / Big Picture

The signing setup sidebar now exposes only the V1-visible text controls that the product still supports. Users can still choose appearance, placement, and whether field names are shown, but they no longer get an advanced per-field source/override editor. The simplified form keeps the visible-text section small, preserves loaded field order, leaves hidden fields hidden when the form is rebuilt, and normalizes custom override text away. The shell boundary also no longer exposes `field_controls`, so the GUI and its tests reflect the same smaller contract.

## Child ExecPlan Dependencies

- [x] No child ExecPlans are required for this slice.

## Progress

- [x] (2026-05-26 18:24 EDT) Removed the advanced visible-text editor and field-control wiring from `src/foliaseal/presentation/qt/visible_signature_setup_form.py`.
- [x] (2026-05-26 18:24 EDT) Removed the shell exposure of now-dead `field_controls` from `src/foliaseal/presentation/qt/signing_shell.py`.
- [x] (2026-05-26 18:24 EDT) Updated the focused form and shell tests to match the simplified surface and the normalization of legacy field overrides.
- [x] (2026-05-26 18:24 EDT) Reviewed `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and `docs/SCHEMAS.md`, then updated the architecture and plan docs to match the final implementation.
- [x] (2026-05-26 18:24 EDT) Validated the slice with `pytest tests/unit/test_qt_visible_signature_setup_form.py tests/unit/test_qt_signing_shell.py` (`82 passed`), `ruff check ...` (passed), and `git diff --check` (passed).
- [x] (2026-05-26 18:24 EDT) Closed out the slice and recorded the retrospective below.

## Surprises & Discoveries

- Observation: Preserving the loaded `field_order` and stripping custom override text can coexist cleanly. The visible-text section stays stable across rebuilds without keeping the removed override editor alive.
  Evidence: `pytest tests/unit/test_qt_visible_signature_setup_form.py tests/unit/test_qt_signing_shell.py` -> `82 passed`.
- Observation: Removing `field_controls` from the shell did not require any preview or signing-flow changes. The shell still renders and drives the same signing workflow, just with a narrower setup-form boundary.
  Evidence: `pytest tests/unit/test_qt_visible_signature_setup_form.py tests/unit/test_qt_signing_shell.py` -> `82 passed`.

## Decision Log

- Decision: Remove the advanced visible-text editor instead of hiding it behind a smaller disclosure.
  Rationale: The advanced per-field source and override UI is outside the V1 product scope, so removing it keeps the setup surface aligned with `docs/SPEC.md` rather than preserving dead UI chrome.
  Date/Author: 2026-05-26 / Codex
- Decision: Preserve loaded `field_order` while normalizing custom override text away on rebuild.
  Rationale: Users should keep the same visible ordering when reopening or reapplying a draft, but unsupported override text should not survive a rebuild because it is no longer part of the supported surface.
  Date/Author: 2026-05-26 / Codex
- Decision: Remove `field_controls` from the shell-facing boundary outright.
  Rationale: A compatibility alias would still imply that the advanced editor exists. The slimmer boundary is clearer and keeps the shell contract aligned with the real UI.
  Date/Author: 2026-05-26 / Codex

## Outcomes & Retrospective

The slice completed as intended. The visible-text section now stays small and predictable, the shell no longer exposes `field_controls`, and rebuilds preserve loaded field order while dropping custom override text. The focused test suite passed cleanly, so the final implementation and the docs now agree on the user-visible contract.

The main lesson from this slice is that field ordering and field content should be treated separately. Once the order was preserved independently from per-field override text, it was straightforward to simplify the UI without destabilizing the draft model or the surrounding shell workflow.

## Context and Orientation

The visible-signature form lives in `src/foliaseal/presentation/qt/visible_signature_setup_form.py`. It still builds the appearance and placement controls, but its `Visible text` group is now intentionally small: it keeps `Show field names` and the per-field visibility checkboxes, and it no longer offers an advanced editor for custom per-field source or override text. When the form is rebuilt from a loaded appearance, it preserves the incoming field order, keeps hidden fields hidden, and normalizes custom override text away.

The shell adapter in `src/foliaseal/presentation/qt/signing_shell.py` now consumes that slimmer form boundary instead of re-exporting `field_controls`. The domain model still requires a complete `SignatureAppearance` with one `SignatureFieldBinding` per visible-signature field, so the simplification stays entirely in the Qt/presentation layer.

`docs/SPEC.md` remains the product intent source for why the advanced editor was removed, and `docs/SCHEMAS.md` still governs the persisted object model. No schema change was needed for this slice because the behavior change is limited to the UI and the shell boundary.

## Plan of Work

The implementation removed the advanced per-field editor from `src/foliaseal/presentation/qt/visible_signature_setup_form.py`, narrowed the visible-text controls to the remaining supported options, and changed `build_draft()` so it rebuilds field bindings from the loaded order while normalizing custom override text away.

The shell update in `src/foliaseal/presentation/qt/signing_shell.py` removed `field_controls` from the `SignaturePropertiesPanel` surface so the shell no longer suggests that the advanced editor is still part of the contract.

The tests in `tests/unit/test_qt_visible_signature_setup_form.py` and `tests/unit/test_qt_signing_shell.py` were updated to assert the smaller visible-text surface, the hidden-field rebuild behavior, the preserved field order, and the absence of shell-exposed `field_controls`.

Finally, `docs/ARCHITECTURE.md` was updated to describe the final contract and this ExecPlan was marked complete with the validation results and retrospective notes.

## Concrete Steps

From `/home/daekar/FoliaSeal`, the final validation commands were:

    pytest tests/unit/test_qt_visible_signature_setup_form.py tests/unit/test_qt_signing_shell.py
    -> 82 passed

    ruff check src/foliaseal/presentation/qt/visible_signature_setup_form.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_visible_signature_setup_form.py tests/unit/test_qt_signing_shell.py
    -> passed

    git diff --check
    -> passed

## Validation and Acceptance

The slice is accepted because the visible-text area now presents only the supported V1 controls, the form rebuild keeps hidden fields hidden and preserves loaded field order, custom override text is normalized away, and the shell no longer exposes `field_controls`.

The focused regression suite passed exactly as expected:

- `pytest tests/unit/test_qt_visible_signature_setup_form.py tests/unit/test_qt_signing_shell.py` -> `82 passed`
- `ruff check ...` -> passed
- `git diff --check` -> passed

## Idempotence and Recovery

This slice is safe to rerun. The validation commands are read-only, and the documentation edits are additive. If the visible-text contract ever drifts again, rerunning the same focused tests and checking the architecture note are the quickest way to confirm whether the UI boundary still matches the expected behavior.

## Artifacts and Notes

The most important evidence for this slice is the final validation transcript:

    pytest tests/unit/test_qt_visible_signature_setup_form.py tests/unit/test_qt_signing_shell.py
    82 passed

    ruff check src/foliaseal/presentation/qt/visible_signature_setup_form.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_visible_signature_setup_form.py tests/unit/test_qt_signing_shell.py
    passed

    git diff --check
    passed

The architecture doc now says the visible text section keeps `Show field names` plus per-field visibility checkboxes, preserves loaded `field_order`, and normalizes custom override text away.

## Interfaces and Dependencies

At the Qt form boundary, `QtVisibleSignatureSetupForm` still exposes `appearance_controls`, `placement_controls`, `visible_text_controls`, `visible_signature_controls`, `load(...)`, `build_draft(...)`, and `set_placement_enabled(...)`.

It now must also preserve these behaviors:

- `Visible text` keeps `Show field names` and per-field visibility checkboxes.
- `build_draft()` preserves the loaded `field_order`.
- Hidden fields remain hidden on rebuild.
- Custom override text is normalized away.

It must not expose `field_controls` or any advanced per-field override editor behavior.

At the shell boundary, `SignaturePropertiesPanel` should only surface the slimmer form contract and should not reintroduce any field-control alias.

Revision note: Updated on 2026-05-26 after the implementation landed so the ExecPlan, validation evidence, and architecture notes all reflect the final simplified visible-text surface and shell boundary.
