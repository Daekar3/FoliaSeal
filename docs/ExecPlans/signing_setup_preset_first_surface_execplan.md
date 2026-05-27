# Make Signing Setup Preset-First And Remove Non-MVP Appearance Cruft

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with [`.agents/skills/write-execplan/PLANS.md`](/home/daekar/FoliaSeal/.agents/skills/write-execplan/PLANS.md).

## Purpose / Big Picture

After this change, the signing sidebar will guide the user through the MVP setup flow that [docs/SPEC.md](/home/daekar/FoliaSeal/docs/SPEC.md) describes: start from a signature preset, then optionally choose a certificate configuration, then only adjust the bounded visible-signature choices that remain in scope for V1. The user should no longer see low-level appearance-editor controls for custom datetime formats, color overrides, border tuning, or image-stamp path entry.

The result must be observable in two ways. First, the right-hand setup surface should render `Signature presets` before `Certificate configuration`, with copy that frames visible-signature editing as preset refinement rather than freeform composition. Second, the visible-signature form should keep placement, field visibility, field order, font family, font size, font emphasis, layout choice, stamp position, timezone mode, signer label prefix, and `Show field names`, while preserving hidden appearance values loaded from presets so previews and signing output still round-trip correctly.

## Child ExecPlan Dependencies

- [x] (2026-05-27 00:00Z) No child ExecPlans are required for this slice.

## Progress

- [x] (2026-05-27 00:10Z) Confirmed the slice with an `explorer-light` review and narrowed scope to preset-first ordering plus bounded appearance-surface simplification.
- [x] (2026-05-27 00:28Z) Reordered the signing-properties panel to render `Signature presets` before `Certificate configuration`.
- [x] (2026-05-27 00:34Z) Simplified `QtVisibleSignatureSetupForm` by removing the redundant appearance row, tightening preset-led copy, and keeping hidden appearance-value preservation through `_appearance_template`.
- [x] (2026-05-27 00:42Z) Updated fake-Qt tests to reflect the reduced surface, assert absence of deleted controls, and cover hidden-value round trips.
- [x] (2026-05-27 00:44Z) Ran focused validation with `pytest`, `ruff check`, and `git diff --check`.
- [x] (2026-05-27 00:48Z) Ran the required post-implementation compliance review against `docs/SPEC.md`, `docs/SCHEMAS.md`, and `docs/ARCHITECTURE.md`; the only gap was documentation drift.
- [x] (2026-05-27 00:52Z) Updated documentation, including this ExecPlan and `docs/ARCHITECTURE.md`, to final state.
- [ ] Commit the slice with a narrow behavior-oriented commit message.

## Surprises & Discoveries

- Observation: `QtVisibleSignatureSetupForm` already preserves loaded `field_order` and caches the loaded `SignatureAppearance` as `_appearance_template`.
  Evidence: `src/foliaseal/presentation/qt/visible_signature_setup_form.py` sets `self._appearance_template = appearance` in `_load_appearance_controls()` and already reuses preserved values in `_build_appearance_from_controls()`.

- Observation: the code had already dropped several legacy appearance widgets, but the fake-Qt shell/form tests still expected them and therefore no longer described the actual product contract.
  Evidence: the first focused `pytest tests/unit/test_qt_visible_signature_setup_form.py tests/unit/test_qt_signing_shell.py -q` run failed on stale `image_stamp_path`, `datetime_format`, and old layout-count assertions before the slice-specific rewrites landed.

## Decision Log

- Decision: Keep field visibility checkboxes and `Show field names` in this slice even while removing other freeform appearance controls.
  Rationale: [docs/SCHEMAS.md](/home/daekar/FoliaSeal/docs/SCHEMAS.md) treats field visibility and order as canonical user-facing state, while [docs/SPEC.md](/home/daekar/FoliaSeal/docs/SPEC.md) explicitly rejects arbitrary custom field content rather than field hiding.
  Date/Author: 2026-05-27 / Codex

- Decision: Remove UI entry points for datetime format, text color, border tuning, background tuning, and image-stamp path entry, but preserve those values when they arrive from loaded presets or direct workflow state.
  Rationale: The product surface should be bounded for MVP, but the underlying appearance model and preview/signing behavior still need to round-trip existing loaded values until later schema or model work intentionally removes them.
  Date/Author: 2026-05-27 / Codex

- Decision: Remove the duplicate `Style` appearance row instead of preserving it as a transitional surface.
  Rationale: It duplicated controls already present in the bounded MVP surface and only added editor density without corresponding schema or SPEC value.
  Date/Author: 2026-05-27 / Codex

## Outcomes & Retrospective

The slice achieved the intended MVP simplification. The signing setup is now visibly preset-first, the visible-signature editor no longer exposes the low-level appearance controls that had already fallen out of the intended product model, and preview/signing behavior still preserves hidden loaded appearance values. Compliance review found no mismatch against `docs/SPEC.md` or `docs/SCHEMAS.md`; only `docs/ARCHITECTURE.md` and this ExecPlan needed final-state updates.

## Context and Orientation

The relevant production surface lives in [src/foliaseal/presentation/qt/signing_shell.py](/home/daekar/FoliaSeal/src/foliaseal/presentation/qt/signing_shell.py) and [src/foliaseal/presentation/qt/visible_signature_setup_form.py](/home/daekar/FoliaSeal/src/foliaseal/presentation/qt/visible_signature_setup_form.py). `SignaturePropertiesPanel` is the right-side editor inside the signing shell. It owns high-level layout, certificate/preset selectors, preview controls, and the extracted visible-signature setup form. `QtVisibleSignatureSetupForm` is the Qt-local boundary that builds and maps a `VisibleSignatureSetupDraft` to and from widgets.

The domain object that matters here is `SignatureAppearance`. It contains both bounded V1 controls that remain user-editable and lower-level appearance values that the MVP UI should no longer expose directly. This slice must preserve the latter when loading and rebuilding a draft so preset-loaded appearance details still reach preview rendering and signing output.

The most important test files are [tests/unit/test_qt_signing_shell.py](/home/daekar/FoliaSeal/tests/unit/test_qt_signing_shell.py) and [tests/unit/test_qt_visible_signature_setup_form.py](/home/daekar/FoliaSeal/tests/unit/test_qt_visible_signature_setup_form.py). They use fake Qt bindings and include white-box structure assertions, so any UI-order or widget-surface changes must be reflected there intentionally.

## Plan of Work

First, edit `src/foliaseal/presentation/qt/signing_shell.py` inside `SignaturePropertiesPanel.__init__` so the panel adds the preset selector container before the certificate configuration container. In the same file, keep the rest of the setup panel structure intact and ensure the visible-signature copy reads as preset refinement rather than “configure everything.”

Second, edit `src/foliaseal/presentation/qt/visible_signature_setup_form.py` to reduce `AppearanceControls` to the bounded MVP fields. Remove direct widget construction and dataclass fields for datetime format, image stamp path, text-color entry, and box-style tuning. Keep the hidden value preservation path by reusing `_appearance_template` inside `_build_appearance_from_controls()` so removed controls do not zero out preset-loaded appearance details. Preserve `field_order`, per-field visibility, `Show field names`, placement state, and font-style availability behavior.

Third, update the fake-Qt tests. In `tests/unit/test_qt_signing_shell.py`, revise the surface/layout assertions for the new preset-first order and reduced appearance-control structure. Replace the shell test that currently proves the datetime/image-stamp UI surface exists with one that proves hidden appearance values survive when the user edits a remaining bounded control. In `tests/unit/test_qt_visible_signature_setup_form.py`, remove assertions for deleted controls, add explicit absence assertions, and add a direct round-trip test that loads custom hidden appearance values, changes a remaining visible control, and confirms the hidden values remain in the rebuilt draft.

Finally, run focused validation, then perform a compliance pass against `docs/SPEC.md`, `docs/SCHEMAS.md`, and `docs/ARCHITECTURE.md`. Update `docs/ARCHITECTURE.md` so the visible-signature form contract and overall signing-shell description match the reduced control surface and preset-first ordering.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Implement the Qt surface changes and tests.

       apply_patch ... on src/foliaseal/presentation/qt/signing_shell.py
       apply_patch ... on src/foliaseal/presentation/qt/visible_signature_setup_form.py
       apply_patch ... on tests/unit/test_qt_signing_shell.py
       apply_patch ... on tests/unit/test_qt_visible_signature_setup_form.py

2. Run focused validation.

       pytest tests/unit/test_qt_visible_signature_setup_form.py tests/unit/test_qt_signing_shell.py
       ruff check src/foliaseal/presentation/qt/visible_signature_setup_form.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_visible_signature_setup_form.py tests/unit/test_qt_signing_shell.py
       git diff --check

   Completed result:

       82 passed in 11.23s
       All checks passed!
       <no output from git diff --check>

3. Run a compliance review subagent against `docs/SPEC.md`, `docs/SCHEMAS.md`, `docs/ARCHITECTURE.md`, and the changed files. If it finds gaps, fix them and re-run the focused validation commands above.

4. Update documentation and this ExecPlan to final state, then create one git commit for the slice.

## Validation and Acceptance

Acceptance was satisfied with the following observed behavior:

- The signing properties panel should render the preset selector before the certificate selector in fake-Qt structure tests.
- The visible-signature form should no longer expose datetime-format, image-stamp-path, text-color, border, or background controls.
- Loading an appearance with hidden values such as custom `datetime_format`, `image_stamp_path`, or box-style values, then editing a remaining visible control and rebuilding the draft, must preserve those hidden values.
- Existing preview behavior for hidden appearance values loaded from a preset or workflow state must still work after the UI reduction.

Run:

    pytest tests/unit/test_qt_visible_signature_setup_form.py tests/unit/test_qt_signing_shell.py

Observed result:

    82 passed in 11.23s

Then run:

    ruff check src/foliaseal/presentation/qt/visible_signature_setup_form.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_visible_signature_setup_form.py tests/unit/test_qt_signing_shell.py
    git diff --check

Observed result:

    All checks passed!
    <no output from git diff --check>

## Idempotence and Recovery

These edits are safe to repeat. The tests are deterministic fake-Qt unit tests. If a first pass removes a control too aggressively and draft rebuilding starts dropping hidden appearance values, restore preservation through `_appearance_template` rather than reintroducing the deleted UI. If white-box tests fail because structure counts changed, update them only to the new intentional surface; do not re-add dead controls to satisfy stale assertions.

## Artifacts and Notes

Validation transcript from this slice:

    $ pytest tests/unit/test_qt_visible_signature_setup_form.py tests/unit/test_qt_signing_shell.py
    ... passed

    $ ruff check src/foliaseal/presentation/qt/visible_signature_setup_form.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_visible_signature_setup_form.py tests/unit/test_qt_signing_shell.py
    All checks passed!

    $ git diff --check
    <no output>

## Interfaces and Dependencies

The following interfaces must remain valid at the end of this slice:

- `foliaseal.presentation.qt.visible_signature_setup_form.QtVisibleSignatureSetupForm.load(draft: VisibleSignatureSetupDraft) -> None`
- `foliaseal.presentation.qt.visible_signature_setup_form.QtVisibleSignatureSetupForm.build_draft() -> VisibleSignatureSetupDraft`
- `foliaseal.presentation.qt.signing_shell.SignaturePropertiesPanel.apply_changes() -> SigningDraftPreview`

`AppearanceControls` in `src/foliaseal/presentation/qt/visible_signature_setup_form.py` should still expose the remaining bounded fields:

    signer_label_prefix
    layout_template
    stamp_position
    timezone_display_mode
    font_family
    font_size
    bold
    italic
    show_field_names

It must no longer expose deleted freeform controls for datetime formatting, direct image-stamp-path entry, text color, or box-style tuning. Hidden values for those fields must still flow through `SignatureAppearance` by preservation from the loaded `_appearance_template`.

Revision note: Created this ExecPlan for the combined preset-first ordering and non-MVP visible-signature surface simplification slice, because the initial explorer found both concerns are best handled together as one bounded MVP-facing change.

Revision note: Updated the plan after implementation and compliance review to record the completed behavior, the stale-test discovery, the doc-sync-only compliance gap, and the final validation evidence.
