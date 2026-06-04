# Narrow The Signing Shell Sidebar Surface

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

This slice is complete. The signing workspace widget now exports a grouped sidebar surface instead of mirroring most sidebar control objects directly onto `widget.<control_name>`. The user-visible GUI behavior stayed the same, but the shell-facing surface is narrower and more intentional: callers and tests use one grouped sidebar surface instead of a long list of top-level mutable Qt control aliases.

This mattered because the hybrid `4+5` direction was trying to make `SigningWorkspaceWidget` a thinner adapter over deeper helpers. The broad top-level alias spray in `src/foliaseal/presentation/qt/signing_shell.py` worked against that goal by making the shell widget itself the owner of a very wide mutable control contract. Grouping that surface under the sidebar kept the shell’s orchestration verbs intact while shrinking the amount of UI structure the shell claims as its own.

## Child ExecPlan Dependencies

- [x] (2026-06-04 21:26Z) No child ExecPlans are required for this bounded shell-internal cleanup slice.

## Progress

- [x] (2026-06-04 21:26Z) Completed the required `explorer-light` audit and fixed the next slice to a grouped sidebar surface rather than reopening app-frame concerns or workspace-interaction policy.
- [x] (2026-06-04 21:26Z) Re-read `src/foliaseal/presentation/qt/signing_shell.py`, `src/foliaseal/presentation/qt/signing_workspace_sidebar.py`, `tests/unit/test_qt_signing_shell.py`, and `tests/unit/test_signing_workspace_sidebar.py` to confirm that the mutable alias spray is concentrated in shell-owned widget exports.
- [x] (2026-06-04 21:29Z) Added `SigningWorkspaceSidebarSurface` in `signing_workspace_sidebar.py` and migrated `SigningWorkspaceWidget` to export `widget.sidebar_surface` instead of the old top-level mutable sidebar control aliases.
- [x] (2026-06-04 21:29Z) Updated focused shell/sidebar tests to consume the grouped surface and added an explicit contract check that the removed top-level aliases are no longer exported.
- [x] (2026-06-04 21:29Z) Ran focused validation with `pytest tests/unit/test_qt_signing_shell.py tests/unit/test_signing_workspace_sidebar.py`, `ruff check`, and `git diff --check`; all passed.
- [x] (2026-06-04 21:29Z) Ran the required architectural compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this ExecPlan; no mismatches were found.
- [x] (2026-06-04 21:29Z) Updated documentation to final state.
- [x] (2026-06-04 21:33Z) Committed the slice as `eb8032bb8` (`qt: narrow signing shell sidebar surface`).

## Surprises & Discoveries

- Observation: almost all remaining top-level shell-widget alias sprawl comes from sidebar-owned controls, not from app-frame or viewer behavior.
  Evidence: the alias block in `src/foliaseal/presentation/qt/signing_shell.py` exports `flow_stage_label`, `document_review_signature_selector`, `document_text_*`, `choose_output_button`, and related controls even though those widgets are built and rendered by `SigningWorkspaceSidebar`.

- Observation: the code outside tests does not appear to rely on those individual aliases.
  Evidence: repository search shows those names are used overwhelmingly in `tests/unit/test_qt_signing_shell.py`, while production code already talks to the sidebar and shell behavior methods directly.

## Decision Log

- Decision: keep this slice surface-focused and avoid changing `WorkspaceInteractionPlan`, `SigningActionBoundary`, or `SigningSetupSession`.
  Rationale: the goal is to reduce shell-owned mutable UI surface, not to reopen already-deepened policy seams in the same commit.
  Date/Author: 2026-06-04 / Codex

- Decision: replace many top-level widget aliases with one grouped `sidebar_surface` export instead of deleting all test-visible structure at once.
  Rationale: this still narrows the shell contract materially, but it avoids unnecessary churn in test ergonomics and keeps the remaining surface explicit.
  Date/Author: 2026-06-04 / Codex

## Outcomes & Retrospective

The shell now exports `sidebar_surface` for the sidebar-owned controls and no longer mirrors the old top-level mutable sidebar aliases. Focused shell/sidebar tests were updated to use the grouped surface, and the direct sidebar render tests still cover the underlying widget composition. The architectural review found no remaining spec or architecture mismatches. The slice is complete and committed.

## Context and Orientation

`src/foliaseal/presentation/qt/signing_shell.py` constructs the viewer, properties panel, and sidebar, then attaches many convenience attributes onto the concrete `widget` object so tests and callers can inspect the live shell. Some of those exports are still reasonable shell-level behavior hooks, such as `apply_app_settings()`, `refresh_certificate_configurations()`, `set_signature_rect()`, `logical_page_index()`, and `submit_sign_request()`. The remaining sidebar-owned controls are grouped behind `widget.sidebar_surface` instead of being mirrored one-by-one onto the shell widget, which keeps the shell from owning a very wide mutable control contract.

This slice introduced one grouped sidebar surface in `src/foliaseal/presentation/qt/signing_workspace_sidebar.py` and has `SigningWorkspaceWidget` export that grouped surface rather than exporting each mutable sidebar control individually. The shell keeps its behavior methods and any non-sidebar structure that still matters, and it no longer pretends to own every mutable sidebar control.

The files that matter for this slice are:

- `src/foliaseal/presentation/qt/signing_workspace_sidebar.py`, which builds the mutable signing-action, review, and document-text widgets and will now expose a grouped shell-facing surface for them.
- `src/foliaseal/presentation/qt/signing_shell.py`, which currently mirrors the sidebar controls onto the top-level widget.
- `tests/unit/test_qt_signing_shell.py`, which currently uses many of the top-level sidebar control aliases.
- `tests/unit/test_signing_workspace_sidebar.py`, which already covers direct sidebar rendering and should remain the primary place for widget-level sidebar assertions.
- `docs/ARCHITECTURE.md`, which describes the shell/sidebar ownership split.

In this plan, a “surface” means a deliberately grouped object that exposes a smaller, coherent set of related UI handles. It is still concrete and test-friendly, but it narrows who claims ownership of those handles.

## Plan of Work

First, a small grouped surface type now lives in `src/foliaseal/presentation/qt/signing_workspace_sidebar.py`. That surface exposes the sidebar container, the properties scroll area, and the mutable controls that belong to the sidebar-owned signing-action, document-review, and document-text sections. The existing direct `document_review_controls`, `document_text_controls`, and `signing_action_controls` remain for sidebar-local rendering code; the grouped surface is the shell-facing export.

Second, `src/foliaseal/presentation/qt/signing_shell.py` exports `sidebar_surface` and no longer attaches the individual top-level mutable sidebar control aliases. The behavior methods and non-sidebar structural attributes that still serve as the shell contract remain intact. The orchestration methods, ordered effect execution, and sign/setup logic were not changed in this slice.

Third, `tests/unit/test_qt_signing_shell.py` uses the grouped sidebar surface for sign-panel, review, and document-text control assertions. The existing shell smoke coverage remains, while `tests/unit/test_signing_workspace_sidebar.py` continues to carry the more direct sidebar render assertions.

Finally, focused validation ran, the required compliance review completed, stale docs were updated, and the final outcome is recorded here.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Add the grouped sidebar surface and migrate the shell exports.

       apply_patch ... on src/foliaseal/presentation/qt/signing_workspace_sidebar.py
       apply_patch ... on src/foliaseal/presentation/qt/signing_shell.py

2. Update focused tests.

       apply_patch ... or bulk edit on tests/unit/test_qt_signing_shell.py
       apply_patch ... on tests/unit/test_signing_workspace_sidebar.py if needed

3. Run focused validation.

       pytest tests/unit/test_qt_signing_shell.py tests/unit/test_signing_workspace_sidebar.py
       ruff check src/foliaseal/presentation/qt/signing_workspace_sidebar.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py tests/unit/test_signing_workspace_sidebar.py
       git diff --check

4. Run the required compliance review, reconcile docs, and commit the slice.

## Validation and Acceptance

This slice is accepted when all of the following are true:

- the signing shell still behaves the same for viewer selection, page changes, review refresh, text search/selection, and signing action state changes
- the shell widget exports one grouped sidebar surface instead of a long list of individual mutable sidebar control aliases
- focused shell tests now consume the grouped sidebar surface where they previously depended on top-level sidebar control aliases
- direct sidebar render tests still prove populated state, empty state, and selector-recursion safety
- `docs/ARCHITECTURE.md` accurately describes the shell/sidebar ownership split

Run:

    pytest tests/unit/test_qt_signing_shell.py tests/unit/test_signing_workspace_sidebar.py

Then run:

    ruff check src/foliaseal/presentation/qt/signing_workspace_sidebar.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py tests/unit/test_signing_workspace_sidebar.py
    git diff --check

Acceptance is behavioral. No GUI flow or user-facing copy changed.

## Idempotence and Recovery

This is a behavior-preserving shell-surface cleanup. It is safe to retry. If removing a specific top-level alias breaks too many tests at once, keep the grouped `sidebar_surface` and migrate the tests first, then remove only the redundant alias set in the same slice before committing. Do not recover by exporting both the full old alias spray and the new grouped surface permanently; that would defeat the purpose of the change.

If an unexpected external production caller depends on one removed alias, add a narrowly justified compatibility export and record that exception in the `Decision Log` rather than reintroducing the whole alias block.

## Artifacts and Notes

The most important evidence for this slice will be:

- a grouped sidebar surface in `src/foliaseal/presentation/qt/signing_workspace_sidebar.py`
- a smaller top-level widget export block in `src/foliaseal/presentation/qt/signing_shell.py`
- focused test output showing the same behavior through the narrower grouped surface

Validation completed successfully with `pytest tests/unit/test_qt_signing_shell.py tests/unit/test_signing_workspace_sidebar.py`, `ruff check`, and `git diff --check`.

## Interfaces and Dependencies

This slice uses the `In-process` dependency category.

At the end of the slice, the sidebar module should expose a grouped surface that looks approximately like:

    @dataclass(frozen=True)
    class SigningWorkspaceSidebarSurface:
        container: Any
        properties_scroll: Any
        signing_action_panel: Any
        choose_output_button: Any
        sign_button: Any
        open_signed_output_button: Any
        sign_result_label: Any
        flow_stage_label: Any
        flow_detail_label: Any
        document_review_headline_label: Any
        document_review_detail_label: Any
        document_review_signature_items_label: Any
        document_review_signature_selector: Any
        document_review_signature_detail_label: Any
        document_text_query_input: Any
        document_text_find_button: Any
        document_text_previous_button: Any
        document_text_next_button: Any
        document_text_copy_button: Any
        document_text_select_mode_checkbox: Any
        document_text_copy_selection_button: Any
        document_text_clear_selection_button: Any
        document_text_status_label: Any
        document_text_detail_label: Any

`SigningWorkspaceWidget` should export `widget.sidebar_surface = self._sidebar.surface` and should not continue to mirror each of those mutable controls individually at the top level.

Revision note: Created on 2026-06-04 by Codex for the next shell-internal tracer bullet in the same signing-workspace hybrid `4+5` direction, after the shell-owned port move was completed. Updated on 2026-06-04 to reflect completion of the grouped sidebar surface slice.
