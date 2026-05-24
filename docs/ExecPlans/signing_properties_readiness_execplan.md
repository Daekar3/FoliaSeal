# Productize signing properties and readiness presentation

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with [.agents/skills/write-execplan/PLANS.md](/home/daekar/FoliaSeal/.agents/skills/write-execplan/PLANS.md).

## Purpose / Big Picture

After this slice, the right-side editor should feel less like an internal shell panel and more like a production signing setup surface. The observable result should be that readiness guidance is presented from the `Sign PDF` action panel, while the properties editor is regrouped around visible signature content and placement instead of standalone shell-era headings like `Visible Fields` and `Validation`.

## Child ExecPlan Dependencies

- [x] (2026-05-24 14:06Z) No child ExecPlans are required for this narrow de-harnessing slice.

## Progress

- [x] (2026-05-24 14:06Z) Audited the current shell locally and identified the next visible shell-era concentration: the properties panel still exposes `Visible Fields`, `Preview`, and `Validation` as internal editor scaffolding.
- [x] (2026-05-24 14:06Z) Recorded the intended slice in this ExecPlan before editing code.
- [x] (2026-05-24 14:24Z) Moved the primary readiness presentation out of the properties editor and into the `Sign PDF` action panel while keeping `SignaturePropertiesPanel.validation_text()` as an orchestration seam.
- [x] (2026-05-24 14:24Z) Regrouped the field-editing controls into a single product-facing `Visible text` section instead of a heading plus free-floating controls.
- [x] (2026-05-24 14:35Z) Preserved signing behavior, preview refresh, and current test-backed workflows. Focused Qt shell and app-frame tests stayed green after the presentation change.
- [x] (2026-05-24 14:35Z) Ran validation, updated docs alignment, and prepared the slice for commit.

## Surprises & Discoveries

- Observation: the remaining “harness shell” feel is now more about editor semantics than overall page composition.
  Evidence: after the sidebar extraction, the most obviously internal-looking parts are the standalone `Validation` section and the raw field-control stack inside `SignaturePropertiesPanel`.
- Observation: no application-layer API change was required to move the readiness display.
  Evidence: the existing `validation_text()` seam was already enough to let the action panel own the visible readiness message while the properties editor stopped rendering its own label.

## Decision Log

- Decision: keep the underlying `SignaturePropertiesPanel` behavior and coordinator boundary intact while changing presentation.
  Rationale: `SPEC.md` still requires certificate, appearance, placement, preview, and readiness behavior. The most efficient next slice is presentation cleanup, not another behavior rewrite.
  Date/Author: 2026-05-24 / Codex

- Decision: use the `Sign PDF` panel as the primary readiness surface.
  Rationale: `SPEC.md` explicitly calls for a clear ready-to-sign state. The action panel is the right product-facing place for that summary, not a separate low-level validation block inside the editor.
  Date/Author: 2026-05-24 / Codex

## Outcomes & Retrospective

This slice removed one of the last obvious shell-era editor affordances from the production GUI without changing signing semantics. The signature-properties editor no longer shows its own `Validation` section. Instead, the `Sign PDF` action panel owns the primary readiness display, which aligns better with the flow in `docs/SPEC.md`: review readiness where the user actually takes the signing action.

The field override area also reads more like product UI now. Rather than a heading plus a loose checkbox and row stack, the editor presents one `Visible text` section that groups field visibility and field override controls into a clearer visible-signature-content area.

Focused validation passed:

- `pytest tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py`
- `ruff check src/foliaseal/presentation/qt/signing_shell.py src/foliaseal/presentation/qt/signing_workspace_sidebar.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py`
- `git diff --check`

The remaining de-harnessing debt is still concentrated in `signing_shell.py`, but this slice moved the visible behavior closer to the staged production workflow described in `SPEC.md` without deleting any review, preview, placement, or signing capabilities.

## Context and Orientation

The production GUI now uses a document-left / sidebar-right composition. The next remaining visible shell-era concentration is the properties editor in `src/foliaseal/presentation/qt/signing_shell.py`. `SignaturePropertiesPanel` still lays out its contents using internal section headings like `Visible Fields`, `Preview`, and `Validation`, then exposes the validation text through a standalone label inside the editor.

That is at odds with the product shape described in `docs/SPEC.md`. The spec wants:

- a clear ready-to-sign state,
- visible approval signatures as the primary path,
- preview/output trust,
- reusable signing objects,
- plain-language readiness and failure handling.

The current editor behavior mostly exists, but the presentation still reads as a debugging or staging surface. This slice should not remove core capabilities. It should move the readiness story to the action panel and regroup the field controls into a more obviously product-facing visible-signature section.

Relevant files:

- `src/foliaseal/presentation/qt/signing_shell.py`
- `src/foliaseal/presentation/qt/signing_workspace_sidebar.py`
- `tests/unit/test_qt_signing_shell.py`
- `docs/ARCHITECTURE.md`

## Plan of Work

First, change the properties panel so readiness/validation text is no longer rendered as its own editor section. The panel should still compute validation text, but the primary display of that text should move to the `Sign PDF` action panel. That keeps the signing action and readiness state together.

Second, regroup the visible signature field controls into a single clearly labeled section. Keep the existing field behaviors, but stop presenting them as a heading plus a loose checkbox and many flat rows. Use a product-facing label such as `Visible text`.

Third, update shell tests to assert the new ownership of readiness text and the revised grouping structure without relying on brittle widget-internal details beyond what is needed to prove the product-facing composition change.

## Concrete Steps

From `/home/daekar/FoliaSeal`, implement and validate this slice with:

    pytest tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py
    ruff check src/foliaseal/presentation/qt/signing_shell.py src/foliaseal/presentation/qt/signing_workspace_sidebar.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py
    git diff --check

Manual acceptance target after implementation:

    .venv/bin/foliaseal gui --pdf-path "/path/to/example.pdf"

Expected visible change: the right-side editor no longer shows a standalone `Validation` section, and the readiness story is instead part of the signing action panel. The field-editing area reads as one visible-signature content section instead of raw shell scaffolding.

## Validation and Acceptance

Acceptance is behavioral:

- focused Qt shell/app-frame tests pass;
- readiness text still reflects current signing state, but it is presented from the action panel;
- the properties editor still supports certificate selection, preset selection, appearance editing, placement editing, preview refresh, and field visibility/override editing;
- the visible field controls are grouped into one product-facing section;
- `ruff check` and `git diff --check` pass.

## Idempotence and Recovery

This slice is safe to repeat. If a regression appears, restore the previous validation-label placement while keeping the rest of the sidebar and shell composition intact. No persisted data or signing semantics should change.

## Artifacts and Notes

Pre-change evidence:

    SignaturePropertiesPanel currently lays out:
    - certificate configuration
    - signature presets
    - appearance
    - heading: Visible Fields
    - show-field-names checkbox
    - one widget row per field
    - heading: Placement
    - placement controls
    - heading: Preview
    - preview controls
    - heading: Validation
    - validation label

This is the shell-era structure the slice is meant to productize.

## Interfaces and Dependencies

No new public app-facing interfaces are required. The slice works within existing Qt presentation boundaries:

- `SignaturePropertiesPanel` continues to own editor state and preview refresh.
- `SigningWorkspaceSidebar` continues to own action/status presentation.
- `SigningWorkspaceWidget` continues to orchestrate between them.

Dependencies are `Local-substitutable`: this is pure Qt presentation composition covered by fake-Qt tests.

Revision note: created and completed on 2026-05-24 for the de-harnessing slice focused on properties-panel presentation and ready-to-sign guidance.
