# Extract the Qt visible-signature setup form boundary

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with [.agents/skills/write-execplan/PLANS.md](/home/daekar/FoliaSeal/.agents/skills/write-execplan/PLANS.md).

## Purpose / Big Picture

After this slice, `signing_shell.py` should stop owning the raw visible-signature form implementation details. Users should see no behavior change, but the shell should delegate control construction, state loading, draft building, and control-state synchronization for the visible-signature setup area to a dedicated Qt form boundary. That makes later setup-flow simplification safer because the shell can stay focused on orchestration.

## Child ExecPlan Dependencies

- [x] (2026-05-24 17:14Z) No child ExecPlans are required for this narrow extraction slice.

## Progress

- [x] (2026-05-24 17:14Z) Audited the current shell locally and identified the next shallow seam: `signing_shell.py` still owns raw visible-signature control construction, load/build mapping, and control-state sync.
- [x] (2026-05-24 17:14Z) Recorded this ExecPlan before implementation.
- [x] (2026-05-24 18:07Z) Extracted `visible_signature_setup_form.py` with dedicated control dataclasses, draft load/build behavior, field enablement rules, and font-style availability rules.
- [x] (2026-05-24 18:15Z) Rewired `SignaturePropertiesPanel` to delegate visible-signature form responsibilities to that module while keeping preview and higher-level orchestration local.
- [x] (2026-05-24 18:29Z) Added direct form boundary tests and kept focused shell/coordinator tests green.
- [x] (2026-05-24 18:34Z) Reviewed architecture/spec alignment, updated docs, validated, and prepared the slice for commit.

## Surprises & Discoveries

- Observation: after the coordinator deepening slice, the main remaining setup friction is entirely Qt-side.
  Evidence: the panel no longer owns the main workflow mutation path, but it still owns control construction, field enablement rules, font-option availability rules, and draft mapping.

## Decision Log

- Decision: keep the extracted form in the Qt presentation layer, not the application layer.
  Rationale: the remaining responsibilities are widget-specific and should not be forced into application code just to reduce shell size.
  Date/Author: 2026-05-24 / Codex

- Decision: preserve the current panel attributes for now by aliasing them to the extracted form where needed.
  Rationale: this keeps the slice narrow and avoids unnecessary churn in shell tests while the boundary is still being established.
  Date/Author: 2026-05-24 / Codex

## Outcomes & Retrospective

This slice completed the Qt-side extraction that naturally followed the coordinator deepening work. `visible_signature_setup_form.py` now owns visible-signature setup widget construction, load/build mapping for `VisibleSignatureSetupDraft`, field-source override enablement, font-style availability, and generic/page-change callbacks. `SignaturePropertiesPanel` remains the certificate/preset/preview host and higher-level orchestrator, but it no longer owns the raw visible-signature form implementation details.

One small compatibility wrinkle showed up during validation: a few preview tests relied on module-level domain enum aliases and `_format_appearance_summary()` remaining available from `signing_shell.py`. I kept those thin compatibility exports instead of forcing unrelated preview tests to change API shape during this refactor.

Focused validation passed:

- `pytest tests/unit/test_qt_visible_signature_setup_form.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py`
- `ruff check src/foliaseal/presentation/qt/visible_signature_setup_form.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_visible_signature_setup_form.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py`
- `git diff --check`

The remaining shallow seam in this area is not widget construction anymore. It is how much detailed setup-surface complexity still lives in the product UI itself. The next de-harnessing slice should target simplifying the visible-signature setup flow, not re-extracting more raw Qt plumbing.

## Context and Orientation

The previous refactor slice deepened the application boundary by teaching `DefaultSignaturePropertiesCoordinator` to own visible-signature setup state and main-path application through `VisibleSignatureSetupDraft`. That removed the panel’s direct ownership of the main workflow mutation path.

What remains in `src/foliaseal/presentation/qt/signing_shell.py` is still a large amount of raw form logic:

- dataclasses for visible-signature form controls,
- creation of appearance, field, placement, and visible-signature widgets,
- loading form controls from the setup draft,
- rebuilding a setup draft from controls,
- field-source enablement rules,
- font-style availability rules,
- form change signal wiring.

These are all one coherent presentation concern. They should live behind one Qt form module instead of remaining spread through the shell.

Relevant files:

- `src/foliaseal/presentation/qt/signing_shell.py`
- `src/foliaseal/presentation/qt/`
- `tests/unit/test_qt_signing_shell.py`
- `docs/ARCHITECTURE.md`

## Plan of Work

First, add a new Qt module under `src/foliaseal/presentation/qt/` that owns the visible-signature setup form. It should build the visible-signature and placement sections, load from `VisibleSignatureSetupDraft`, build a new draft from current widget state, and manage field/font control availability.

Second, update `SignaturePropertiesPanel` in `src/foliaseal/presentation/qt/signing_shell.py` to instantiate that form and delegate:

- visible-signature section construction,
- placement section construction,
- setup draft loading,
- setup draft building,
- field/state synchronization.

The panel should keep certificate/preset controls, preview rendering, coordinator interaction, and higher-level orchestration in this slice.

Third, add focused form boundary tests and keep shell tests green. The new boundary tests should prove the extracted form can load/build setup drafts and apply its control-state rules without needing the whole shell.

Finally, update `docs/ARCHITECTURE.md` and this ExecPlan so the project record reflects the extracted Qt form boundary.

## Concrete Steps

From `/home/daekar/FoliaSeal`, implement and validate this slice with:

    pytest tests/unit/test_qt_visible_signature_setup_form.py tests/unit/test_qt_signing_shell.py tests/unit/test_signature_properties_coordinator.py
    ruff check src/foliaseal/presentation/qt/visible_signature_setup_form.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_visible_signature_setup_form.py tests/unit/test_qt_signing_shell.py tests/unit/test_signature_properties_coordinator.py
    git diff --check

Manual acceptance target after implementation:

    .venv/bin/foliaseal gui --pdf-path "/path/to/example.pdf"

Expected visible result: no GUI behavior change, but `signing_shell.py` should be thinner and the visible-signature setup form should exist as its own Qt boundary.

## Validation and Acceptance

Acceptance is behavioral:

- the extracted form has direct boundary tests;
- focused shell and coordinator tests still pass;
- visible-signature editing still updates preview/readiness correctly;
- the shell no longer owns the raw form implementation details for the visible-signature setup area;
- `ruff check` and `git diff --check` pass.

## Idempotence and Recovery

This slice is safe to repeat. If regressions appear, restore the old inline shell form implementation while keeping the application-layer setup draft/coordinator work intact. No persisted object shape or signing behavior should change.

## Artifacts and Notes

Pre-change evidence:

    `SignaturePropertiesPanel` still owns:
    - `AppearanceControls`, `PlacementControls`, `VisibleTextControls`, `VisibleSignatureControls`
    - building appearance/field/placement widgets
    - loading widgets from `VisibleSignatureSetupDraft`
    - rebuilding a setup draft from Qt controls
    - field-source enablement and font-style availability rules

These are the responsibilities this slice is meant to extract.

## Interfaces and Dependencies

This remains a local-substitutable Qt presentation refactor:

- the new form module depends on dynamic Qt bindings and the application-layer `VisibleSignatureSetupDraft`
- `SignaturePropertiesPanel` depends on the new form boundary
- the application coordinator and preview helpers do not change responsibility

The extracted form should expose:

- its top-level visible-signature container,
- its placement container,
- a `load(draft)` behavior,
- a `build_draft()` behavior,
- callbacks for generic form changes and page changes.

Revision note: created and completed on 2026-05-24 for the Qt extraction slice following the visible-signature setup coordinator deepening work.
