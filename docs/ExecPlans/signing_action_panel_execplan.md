# Consolidate signing actions into one production panel

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with [.agents/skills/write-execplan/PLANS.md](/home/daekar/FoliaSeal/.agents/skills/write-execplan/PLANS.md).

## Purpose / Big Picture

After this slice, the right-side production sidebar should read less like scaffolding and more like a coherent signing surface. The observable change is that the “next step” guidance, output-path action, sign action, reopen action, and result message all live inside one `Sign PDF` panel instead of being split between a small status card and several loose buttons/labels.

## Child ExecPlan Dependencies

- [x] (2026-05-23 18:16Z) No child ExecPlans are required for this narrow sidebar follow-up.

## Progress

- [x] (2026-05-23 18:16Z) Audited the new sidebar and identified that the remaining visible cruft was the old flow-summary pattern plus loose action controls outside any cohesive panel.
- [x] (2026-05-23 18:19Z) Folded output/sign/reopen/result controls into one `Sign PDF` panel owned by `signing_workspace_sidebar.py`.
- [x] (2026-05-23 18:20Z) Updated focused fake-Qt shell tests to assert the new panel ownership.
- [x] (2026-05-23 18:22Z) Ran focused validation successfully.

## Surprises & Discoveries

- Observation: After the first sidebar extraction, the biggest remaining harness-era feel came from layout semantics, not feature semantics.
  Evidence: The sidebar still presented status text in one card and the real actions as loose controls immediately below it. Grouping those controls was enough to make the surface read more like a product panel without touching signing behavior.

## Decision Log

- Decision: Keep the existing flow-stage labels for now, but move them inside a `Sign PDF` action panel.
  Rationale: The labels still help the current flow, and deleting them outright would be a product decision. This slice removes the shell scaffolding around them first.
  Date/Author: 2026-05-23 / Codex

## Outcomes & Retrospective

This slice made the production sidebar more cohesive without expanding scope. The visible result is modest but real: one signing panel now owns status, actions, reopen behavior, and result messaging. Future cleanup should target the remaining large properties editor and broader workspace orchestration.

## Context and Orientation

The previous slice introduced `src/foliaseal/presentation/qt/signing_workspace_sidebar.py` and moved the production shell to a document-left / sidebar-right composition. That removed the top staged rail, but the sidebar still showed a residual shell pattern: a small status panel followed by several loose action buttons and the result label outside any panel. This slice treats that as the next piece of harness-era UI debt.

The relevant files are:

- `src/foliaseal/presentation/qt/signing_workspace_sidebar.py`
- `src/foliaseal/presentation/qt/signing_shell.py`
- `tests/unit/test_qt_signing_shell.py`
- `docs/ARCHITECTURE.md`

## Plan of Work

Move the output-path chooser, sign button, reopen button, and result label into the sidebar’s signing panel so one panel owns the primary action flow. Keep the shell’s current public methods and current sign/reopen behavior unchanged.

## Concrete Steps

From `/home/daekar/FoliaSeal`, validate this slice with:

    pytest tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py
    ruff check src/foliaseal/presentation/qt/signing_shell.py src/foliaseal/presentation/qt/signing_workspace_sidebar.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py
    git diff --check

Observed result:

    pytest tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py
    93 passed

## Validation and Acceptance

Acceptance is behavioral:

- the shell still supports choose-output, sign, reopen, review, and text tools;
- the signing actions now belong to a single `Sign PDF` panel rather than floating in the sidebar;
- focused tests pass;
- formatting/lint checks pass.

## Idempotence and Recovery

This slice is safe to repeat. If a regression appears, restore the previous sidebar composition while keeping the sidebar module boundary intact.

## Artifacts and Notes

Focused structural proof in the fake-Qt shell test now asserts that:

    - `choose_output_button` is parented by the signing action panel
    - `sign_result_label` is parented by the signing action panel

## Interfaces and Dependencies

No new public app-facing interfaces were added. The internal sidebar boundary now owns a richer `Sign PDF` panel. Dependencies remain `Local-substitutable` because the work is pure Qt composition with fake-Qt tests.

Revision note: created on 2026-05-23 for the second production-sidebar cleanup slice, focused on consolidating the primary signing actions into one cohesive panel.
