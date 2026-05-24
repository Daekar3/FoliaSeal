# Productize the remaining signing-properties sections

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with [.agents/skills/write-execplan/PLANS.md](/home/daekar/FoliaSeal/.agents/skills/write-execplan/PLANS.md).

## Purpose / Big Picture

After this slice, the signing-properties sidebar should read more like a staged product workflow and less like a generic editor. A user opening a PDF should see product-facing sections for signature style, visible text, placement on the page, and signed-appearance preview, rather than raw headings such as `Placement` and `Preview`. The visible result should better match the staged flow in `docs/SPEC.md`: choose a setup, place it, preview it, then sign.

## Child ExecPlan Dependencies

- [x] (2026-05-24 15:07Z) No child ExecPlans are required for this narrow de-harnessing slice.

## Progress

- [x] (2026-05-24 15:07Z) Audited `src/foliaseal/presentation/qt/signing_shell.py` locally and confirmed that the remaining shell-era composition is concentrated in the properties editor.
- [x] (2026-05-24 15:07Z) Recorded this ExecPlan before implementation.
- [x] (2026-05-24 15:18Z) Replaced the remaining raw `Placement` and `Preview` heading-based sections with fully grouped product-facing sections.
- [x] (2026-05-24 15:18Z) Improved product copy for the signing-properties editor so the user-facing section names and summaries align better with `docs/SPEC.md`.
- [x] (2026-05-24 15:25Z) Preserved all current signing, preview, and test-backed workflow behavior after one stale test expectation was updated for the new grouped layout.
- [x] (2026-05-24 15:31Z) Ran validation, reviewed doc alignment, and prepared the slice for commit.

## Surprises & Discoveries

- Observation: the remaining harness feel is now mostly a copy/composition problem, not a feature-gap problem.
  Evidence: `SignaturePropertiesPanel` still mixes group boxes with standalone heading labels, and the preview container itself is still untitled even though preview fidelity is a core product principle in `docs/SPEC.md`.
- Observation: the fake-Qt tests had only one real regression, and it was a stale structure expectation rather than a behavioral break.
  Evidence: `pytest` initially failed only in `test_signing_shell_preview_surfaces_datetime_format_and_image_stamp`, where the appearance container item count still expected the pre-summary two-item layout.

## Decision Log

- Decision: keep this slice presentation-only.
  Rationale: `docs/SPEC.md` already requires the existing behavior set. The next highest-value change is to remove shell-era framing without reopening coordinator, preview-layout, or signing behavior work.
  Date/Author: 2026-05-24 / Codex

- Decision: use product-facing section titles and short summary copy inside the properties editor.
  Rationale: the main remaining problem is that the editor still reads like internal tooling. Better titles and section grouping move the UI closer to the intended desktop-signing workflow without adding more controls.
  Date/Author: 2026-05-24 / Codex

## Outcomes & Retrospective

This slice removed the last raw heading-based sections from the signing-properties editor. The user now sees four clearer product-facing groups: `Signature style`, `Visible text`, `Placement on page`, and `Signed appearance preview`. Each group has short guidance copy, and the preview section now explicitly reinforces preview/output trust instead of behaving like an unlabeled render bucket.

The implementation stayed intentionally narrow. No signing workflow semantics changed. Certificate selection, preset management, placement editing, preview generation, and readiness tracking all continued to work through the same underlying boundaries.

Focused validation passed:

- `pytest tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py`
- `ruff check src/foliaseal/presentation/qt/signing_shell.py src/foliaseal/presentation/qt/signing_workspace_sidebar.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py`
- `git diff --check`

The remaining de-harnessing debt is now less about section titles and more about the density of the properties editor itself. If future work continues in this area, the next slice should simplify or recompose the controls rather than just renaming more labels.

## Context and Orientation

The production GUI now uses a document-left / sidebar-right layout, and the top-level staging rail is already gone. The main remaining visible shell-era composition is inside `src/foliaseal/presentation/qt/signing_shell.py`, specifically `SignaturePropertiesPanel`.

The current editor already has product-relevant behaviors:

- certificate configuration selection,
- signature preset selection,
- appearance editing,
- visible text field editing,
- placement editing,
- preview generation,
- readiness tracking through the `Sign PDF` action panel.

The remaining problem was presentation. The editor mixed full group boxes such as `Appearance` with raw heading labels for `Placement` and `Preview`, and the preview group itself had no explicit product-facing title. `docs/SPEC.md` describes a document-centric staged workflow:

`Open -> Review -> Choose preset/certificate -> Place -> Preview readiness -> Sign -> Save -> Verify`

This slice should make the properties editor read more like that flow without changing any signing semantics.

Relevant files:

- `src/foliaseal/presentation/qt/signing_shell.py`
- `tests/unit/test_qt_signing_shell.py`
- `docs/ARCHITECTURE.md`

## Plan of Work

First, update the signing-properties section builders in `src/foliaseal/presentation/qt/signing_shell.py` so the remaining raw-heading sections become full group boxes. The appearance section should use clearer product-facing wording, the visible-text section can keep its current grouped behavior but may gain explanatory copy, the placement section should become an explicit on-page placement group, and the preview section should become a clearly named signed-appearance preview group.

Second, add short, plain-language summary labels inside these groups where they improve orientation. Keep them brief and directly tied to the user’s next action. The preview section should reinforce preview/output trust rather than reading like a generic render container.

Third, update focused Qt shell tests in `tests/unit/test_qt_signing_shell.py` so they assert the new grouped composition and summary ownership without reintroducing brittle whole-widget-tree assertions.

Finally, update `docs/ARCHITECTURE.md` and this ExecPlan so the living repo documentation reflects the product-facing editor composition.

## Concrete Steps

From `/home/daekar/FoliaSeal`, implement and validate this slice with:

    pytest tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py
    ruff check src/foliaseal/presentation/qt/signing_shell.py src/foliaseal/presentation/qt/signing_workspace_sidebar.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py
    git diff --check

Manual acceptance target after implementation:

    .venv/bin/foliaseal gui --pdf-path "/path/to/example.pdf"

Expected visible change: the right-side editor no longer shows raw section headings for `Placement` and `Preview`. Instead, the sidebar reads as a sequence of product-facing grouped sections for signing style, visible text, placement on the page, and signed-appearance preview.

## Validation and Acceptance

Acceptance is behavioral:

- focused Qt shell and app-frame tests pass;
- the properties editor still supports all current certificate, preset, appearance, visible-text, placement, and preview interactions;
- the preview section is explicitly presented as a signed-appearance preview rather than an unlabeled render block;
- the remaining standalone shell-style section headings are removed from the properties editor;
- `ruff check` and `git diff --check` pass.

## Idempotence and Recovery

This slice is safe to repeat. If a regression appears, restore the previous layout composition while keeping the already-completed sidebar and readiness changes intact. No persisted data or signing behavior should change.

## Artifacts and Notes

Pre-change evidence:

    SignaturePropertiesPanel currently mixes:
    - group boxes for certificate configuration, signature presets, appearance, and visible text
    - standalone heading labels for Placement and Preview
    - an untitled preview container nested under the Preview heading

This mixed composition is the remaining shell-era surface this slice is meant to remove.

## Interfaces and Dependencies

No new cross-module interfaces are required. This slice stays inside the existing Qt presentation boundary:

- `SignaturePropertiesPanel` continues to own properties-editor composition and preview refresh.
- `SigningWorkspaceSidebar` continues to own the outer production sidebar.
- `DefaultSignaturePropertiesCoordinator` remains the application-layer source of readiness state and preview-backed editor state.

Dependencies are local and substitutable. The work is limited to Qt widget composition and fake-Qt test coverage.

Revision note: created and completed on 2026-05-24 for the de-harnessing slice focused on the remaining signing-properties section composition.
