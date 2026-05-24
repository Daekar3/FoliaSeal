# Consolidate visible-signature editing into one primary section

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with [.agents/skills/write-execplan/PLANS.md](/home/daekar/FoliaSeal/.agents/skills/write-execplan/PLANS.md).

## Purpose / Big Picture

After this slice, the signing-properties sidebar should present one primary `Visible signature` section instead of separate top-level `Signature style` and `Visible text` sections. The visible result should make the sidebar read more like a signing workflow centered on visible approval signatures, which is the product posture in `docs/SPEC.md`, and less like a generic stack of editing panels.

## Child ExecPlan Dependencies

- [x] (2026-05-24 15:42Z) No child ExecPlans are required for this narrow de-harnessing slice.

## Progress

- [x] (2026-05-24 15:42Z) Audited the current top-level properties-editor composition locally and identified separate `Signature style` and `Visible text` sections as the next remaining density problem.
- [x] (2026-05-24 15:42Z) Recorded this ExecPlan before implementation.
- [x] (2026-05-24 15:48Z) Consolidated `Signature style` and `Visible text` under one top-level `Visible signature` section.
- [x] (2026-05-24 15:55Z) Preserved all current style, field, preview, and signing behavior. Focused Qt shell and app-frame tests stayed green on the first implementation pass.
- [x] (2026-05-24 16:00Z) Updated focused tests, architecture docs, and prepared the slice for commit.

## Surprises & Discoveries

- Observation: the biggest remaining harness-era feel is now top-level section count, not naming.
  Evidence: the sidebar already uses product-facing labels, but the properties editor still presents six top-level blocks even though `docs/SPEC.md` treats visible signature setup as one coherent concern.
- Observation: this slice did not need any control-level logic changes.
  Evidence: the existing `AppearanceControls` and `VisibleTextControls` could be nested unchanged under a new wrapper, and focused tests passed without any preview or workflow adjustments.

## Decision Log

- Decision: keep the existing `Signature style` and `Visible text` groups as nested subsections rather than flattening their controls.
  Rationale: that reduces visible top-level density without reopening behavior or forcing a larger control redesign in the same slice.
  Date/Author: 2026-05-24 / Codex

- Decision: center the new top-level section on the phrase `Visible signature`.
  Rationale: `docs/SPEC.md` explicitly defines visible approval signatures as the primary V1 path, so this label is both product-facing and contract-aligned.
  Date/Author: 2026-05-24 / Codex

## Outcomes & Retrospective

This slice reduced one more layer of top-level UI density from the signing-properties editor. Instead of treating style and visible-text editing as two peer panels, the production GUI now exposes one top-level `Visible signature` section with the existing `Signature style` and `Visible text` groups nested inside it. That makes the sidebar better match the V1 posture in `docs/SPEC.md`, where visible approval signatures are the primary path.

The implementation remained presentation-only. No signing semantics, preview logic, readiness handling, or reusable-object behavior changed.

Focused validation passed:

- `pytest tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py`
- `ruff check src/foliaseal/presentation/qt/signing_shell.py src/foliaseal/presentation/qt/signing_workspace_sidebar.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py`
- `git diff --check`

The next remaining de-harnessing problem is no longer just section composition. The deeper issue is that the top setup area still exposes certificate-selection, preset management, and detailed style controls as a dense editor surface. The next slice should simplify that workflow rather than just regrouping labels again.

## Context and Orientation

The production GUI has already been de-harnessed in several steps: the top staging rail is gone, the action controls live in a cohesive `Sign PDF` panel, readiness no longer renders as a standalone validation block, and the remaining properties sections already use more product-facing titles.

The current remaining issue is that the top of the properties editor still separates `Signature style` and `Visible text` into two peer sections. In practice, both are part of the same visible-signature setup task. `docs/SPEC.md` emphasizes:

- visible approval signatures as the primary path,
- preview/output trust,
- contextual editing of appearance and placement,
- a staged signing workflow.

That means the next visible cleanup should reduce top-level section count and make the visible-signature configuration read as one coherent step.

Relevant files:

- `src/foliaseal/presentation/qt/signing_shell.py`
- `tests/unit/test_qt_signing_shell.py`
- `docs/ARCHITECTURE.md`

## Plan of Work

First, add a new composite Qt presentation wrapper in `src/foliaseal/presentation/qt/signing_shell.py` that owns a `Visible signature` group. That wrapper should contain short guidance text plus the existing `Signature style` and `Visible text` group boxes. The underlying controls remain unchanged.

Second, update `SignaturePropertiesPanel` so it adds this new composite section to its main layout instead of adding the two existing groups separately.

Third, update focused fake-Qt shell tests in `tests/unit/test_qt_signing_shell.py` so they assert the new top-level composition and the continued presence of the nested groups.

Finally, update `docs/ARCHITECTURE.md` and this ExecPlan so the living project record matches the new visible-signature-centered composition.

## Concrete Steps

From `/home/daekar/FoliaSeal`, implement and validate this slice with:

    pytest tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py
    ruff check src/foliaseal/presentation/qt/signing_shell.py src/foliaseal/presentation/qt/signing_workspace_sidebar.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py
    git diff --check

Manual acceptance target after implementation:

    .venv/bin/foliaseal gui --pdf-path "/path/to/example.pdf"

Expected visible change: the top of the properties editor shows one `Visible signature` section containing the style and visible-text configuration, reducing the feeling of a stacked editor toolkit.

## Validation and Acceptance

Acceptance is behavioral:

- focused Qt shell and app-frame tests pass;
- style controls, visible-text controls, preview updates, and signing readiness still work exactly as before;
- the properties editor exposes fewer top-level sections because `Signature style` and `Visible text` are nested under one visible-signature group;
- `ruff check` and `git diff --check` pass.

## Idempotence and Recovery

This slice is safe to repeat. If a regression appears, restore the previous top-level layout while preserving the already-completed product-facing section titles and readiness behavior. No persisted data or signing semantics should change.

## Artifacts and Notes

Pre-change evidence:

    SignaturePropertiesPanel currently adds these top-level widgets in order:
    - certificate configuration
    - signature presets
    - signature style
    - visible text
    - placement on page
    - signed appearance preview

This slice targets only the separation between the two visible-signature-related sections.

## Interfaces and Dependencies

No new cross-module interfaces are required. This is a local Qt composition change:

- `SignaturePropertiesPanel` continues to own properties-editor layout and preview refresh.
- The existing `AppearanceControls` and `VisibleTextControls` remain intact.
- `SigningWorkspaceSidebar` and application-layer signing boundaries do not change.

Dependencies are limited to fake-Qt-compatible presentation composition and focused shell tests.

Revision note: created and completed on 2026-05-24 for the de-harnessing slice focused on consolidating visible-signature editing.
