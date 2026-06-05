# Extract The Signing Workspace Shell Surface

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

This slice keeps the current signing workspace behavior unchanged while moving the remaining public shell surface out of `src/foliaseal/presentation/qt/signing_shell.py` and into a dedicated helper module. After this change, the shell should still expose the same concrete widget attributes and caller-facing verbs that the app frame and tests already use, but the compatibility-export block and most of the direct public-surface plumbing should no longer live inline inside `SigningWorkspaceWidget`.

The user-visible outcome is stability, not new product behavior: `build_qt_signing_shell()` should still return the same concrete widget surface, `app_frame.py` should still route `Save As...` and live certificate refresh through the loaded shell, and the existing shell tests should still pass. The observable improvement is architectural: a smaller shell module with a dedicated owner for the test-facing and app-frame-facing surface.

## Child ExecPlan Dependencies

- [x] (2026-06-05 03:35Z) No child ExecPlans are required for this bounded shell-surface extraction slice.

## Progress

- [x] (2026-06-05 03:34Z) Completed the required `explorer-light` audit and fixed the next slice to extracting the remaining shell public-surface and compatibility-export block rather than reopening already-deepened review, interaction, action, or properties-panel seams.
- [x] (2026-06-05 03:35Z) Re-read the current shell surface in `src/foliaseal/presentation/qt/signing_shell.py`, the app-frame routing expectations in `tests/unit/test_qt_app_frame.py`, and the architecture debt note in `docs/ARCHITECTURE.md`.
- [x] (2026-06-05 03:58Z) Added `src/foliaseal/presentation/qt/signing_workspace_shell_surface.py` and migrated the compatibility export block plus the narrow public-surface verbs out of `signing_shell.py` while preserving the same live shell/widget contract.
- [x] (2026-06-05 04:06Z) Kept focused coverage green without test-file edits because the live shell/app-frame contract stayed stable and the existing shell/app-frame tests already covered the extracted surface.
- [x] (2026-06-05 04:06Z) Ran focused validation with the shell subset, app-frame subset, `ruff check`, and `git diff --check`.
- [x] (2026-06-05 04:16Z) Completed the required architectural/spec compliance review and reconciled `docs/ARCHITECTURE.md` to match the new shell-surface ownership.
- [x] (2026-06-05 04:18Z) Updated documentation to final state and prepared the slice for a single local closeout commit.

## Surprises & Discoveries

- Observation: The shell/app-frame contract was already covered well enough that this extraction did not need direct test edits.
  Evidence: The focused shell subset (`9 passed`) and app-frame subset (`2 passed`) both stayed green after the helper extraction, and the key existing assertions still hit `widget.sidebar_surface`, `widget.properties_panel`, `choose_output_pdf_path()`, and `refresh_certificate_configurations()`.

- Observation: The main noncompliance after implementation was doc drift, not behavior drift.
  Evidence: Focused validation and the extracted helper were already green, but `docs/ARCHITECTURE.md` still described `signing_shell.py` as the owner of the compatibility-export block and the app-frame/test-facing shell surface.

## Decision Log

- Decision: keep the public shell/widget contract stable in this slice even if some compatibility exports remain awkward.
  Rationale: this tracer bullet is about moving ownership of the surface, not changing app-frame or test callers in the same loop.
  Date/Author: 2026-06-05 / Codex

- Decision: target the dedicated shell-surface/helper boundary next instead of another behavior bridge.
  Rationale: review/text bridging, interaction-plan execution, signing-action glue, and the properties panel already moved behind dedicated helpers, so the remaining concentration is the shell-facing export and routing surface itself.
  Date/Author: 2026-06-05 / Codex

## Outcomes & Retrospective

This slice completed successfully. `signing_workspace_shell_surface.py` now owns the compatibility export block and the caller-facing shell verbs that tests and `app_frame.py` still drive directly, while `signing_shell.py` remains the composition root and event/orchestration edge.

Focused validation passed without test edits:

- `pytest tests/unit/test_qt_signing_shell.py -k 'layout_and_production_sidebar or choose_output_pdf_path or refresh_certificate_configurations or document_text or set_signature_rect or refresh_viewer'` -> `9 passed`
- `pytest tests/unit/test_qt_app_frame.py -k 'choose_open_pdf or reopens_signed_output_from_shell_callback or save_as_action_enables_after_open_and_routes_to_current_shell'` -> `2 passed`
- `ruff check src/foliaseal/presentation/qt/signing_shell.py src/foliaseal/presentation/qt/signing_workspace_shell_surface.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py` -> clean
- `git diff --check` -> clean

The initial implementation was behaviorally compliant, but not documentation-complete. The only compliance issue was stale architecture wording that still placed the compatibility-export/public-surface cluster in `signing_shell.py`. After the architecture-doc reconciliation, the slice reached final compliant state without needing a child ExecPlan.

## Context and Orientation

`src/foliaseal/presentation/qt/signing_shell.py` remains the composition root for the production signing workspace. Recent slices already extracted several coherent clusters into dedicated shell-local helpers:

- `src/foliaseal/presentation/qt/signing_workspace_review_bridge.py` owns review/text bridge rendering and transition application.
- `src/foliaseal/presentation/qt/signing_workspace_interaction_bridge.py` owns `WorkspaceInteractionPlan` execution.
- `src/foliaseal/presentation/qt/signing_workspace_action_bridge.py` owns shell-facing signing-action dialog and state glue.
- `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py` owns `SignaturePropertiesPanel` and its preview/setup/widget helpers.
- `src/foliaseal/presentation/qt/signing_workspace_sidebar.py` owns the grouped sidebar surface and sidebar render ownership.

What still sits inline in `SigningWorkspaceWidget` is the remaining public shell surface. In this plan, “public shell surface” means two related things:

- the dynamic compatibility attributes that get attached onto `self.widget`, such as `properties_panel`, `viewer_widget`, `sidebar_surface`, `choose_output_pdf_path`, and `refresh_certificate_configurations`;
- the caller-facing shell verbs that mainly exist so those exports, tests, and `app_frame.py` can drive the live workspace without reaching into the behavior helpers directly.

The key files for this slice are:

- `src/foliaseal/presentation/qt/signing_shell.py`, which currently both composes the workspace and directly owns the remaining compatibility export block and public-surface methods;
- `src/foliaseal/presentation/qt/signing_workspace_shell_surface.py`, the new helper module to add in this slice;
- `tests/unit/test_qt_signing_shell.py`, which proves the concrete widget shape and the behavior of the exported surface;
- `tests/unit/test_qt_app_frame.py`, which proves that the top-level frame still routes `Save As...` and shell refreshes through the current shell;
- `docs/ARCHITECTURE.md`, which currently names `signing_shell.py` as still carrying composition plus compatibility-export debt and will need reconciliation after the extraction.

This slice must remain narrow. It may move shell-surface ownership and update the docs/tests needed to prove that move, but it must not redesign the app-frame contract, the bridges, the sidebar, the properties panel, or the signing/setup policy boundaries.

## Plan of Work

First, add a new shell-local helper module under `src/foliaseal/presentation/qt/` that owns the remaining shell public surface. The helper should install the compatibility attributes onto the live widget and should provide the narrow caller-facing shell verbs that mostly delegate to the already-extracted bridges, review workspace, draft workflow, and viewer session. Keep the same concrete behavior and attribute names so existing callers keep working.

Second, edit `src/foliaseal/presentation/qt/signing_shell.py` so `SigningWorkspaceWidget` constructs that helper, delegates the widget export/install block to it, and routes its public methods through the helper where appropriate. The shell should remain the composition root and should keep the lower-level event handlers, overlay syncing, and error/status emission edge behavior that still genuinely belong there.

Third, update focused tests only where the ownership split changes the best assertion point. Keep the shell/app-frame contract stable and preserve the test-facing compatibility attributes that are already intentionally part of the live shell shape.

Finally, run the focused validation commands, do the required compliance review against `docs/ARCHITECTURE.md` and `docs/SPEC.md`, update the docs to describe the new helper boundary, and record the final result here.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Add the new shell-surface helper module and migrate the export block and surface routing.

       apply_patch ... on src/foliaseal/presentation/qt/signing_workspace_shell_surface.py
       apply_patch ... on src/foliaseal/presentation/qt/signing_shell.py

2. Update focused tests only if the extraction changes what needs to be asserted directly.

       apply_patch ... on tests/unit/test_qt_signing_shell.py
       apply_patch ... on tests/unit/test_qt_app_frame.py

3. Run focused validation.

       pytest tests/unit/test_qt_signing_shell.py -k 'layout_and_production_sidebar or choose_output_pdf_path or refresh_certificate_configurations or document_text or set_signature_rect or refresh_viewer'
       pytest tests/unit/test_qt_app_frame.py -k 'choose_open_pdf or reopens_signed_output_from_shell_callback or save_as_action_enables_after_open_and_routes_to_current_shell'
       ruff check src/foliaseal/presentation/qt/signing_shell.py src/foliaseal/presentation/qt/signing_workspace_shell_surface.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py
       git diff --check

4. Run the required compliance review, reconcile docs if needed, and commit the slice.

## Validation and Acceptance

This slice is accepted when all of the following are true:

- a dedicated shell-local helper owns the compatibility export block and the narrow public shell surface instead of `signing_shell.py` keeping that cluster inline;
- `build_qt_signing_shell()` still returns the same concrete widget-facing surface expected by the app frame and existing shell tests, including dynamic attrs such as `properties_panel`, `viewer_widget`, `sidebar_surface`, `choose_output_pdf_path`, and `refresh_certificate_configurations`;
- the app frame still routes `Save As...` and loaded-shell certificate refreshes through the current shell without any caller changes;
- the already-extracted behavior helpers remain the owners of their existing responsibilities and are not widened again in this slice;
- `docs/ARCHITECTURE.md` accurately describes the new shell-surface ownership and tightens the remaining `signing_shell.py` debt note.

Run:

    pytest tests/unit/test_qt_signing_shell.py -k 'layout_and_production_sidebar or choose_output_pdf_path or refresh_certificate_configurations or document_text or set_signature_rect or refresh_viewer'
    pytest tests/unit/test_qt_app_frame.py -k 'choose_open_pdf or reopens_signed_output_from_shell_callback or save_as_action_enables_after_open_and_routes_to_current_shell'

Then run:

    ruff check src/foliaseal/presentation/qt/signing_shell.py src/foliaseal/presentation/qt/signing_workspace_shell_surface.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py
    git diff --check

Acceptance is behavioral. No user-facing GUI flow, labels, or shell contract should change in this slice.

## Idempotence and Recovery

This is a behavior-preserving extraction. It is safe to retry. If the helper extraction becomes awkward for a few specific compatibility attrs, keep the public names stable and centralize the awkwardness inside the new helper rather than spreading one-off install logic back through the shell. Do not recover by splitting ownership of the same export block across both files long-term; one helper should remain the owner at the end of the slice.

If the extraction unexpectedly requires changing the app-frame port, the properties-panel contract, or the review/action/interaction helper responsibilities, stop and split that broader redesign into a later slice instead of widening this one.

## Artifacts and Notes

The most important evidence for this slice will be:

- a new shell-local module that owns the compatibility export block and public shell surface;
- a smaller `SigningWorkspaceWidget` surface section in `src/foliaseal/presentation/qt/signing_shell.py`;
- focused shell/app-frame tests proving the live widget and caller-facing contract stayed intact.

## Interfaces and Dependencies

This slice uses the `In-process` dependency category.

At the end of the slice, `src/foliaseal/presentation/qt/signing_workspace_shell_surface.py` should expose one dedicated helper type that the shell composes. The exact name may vary slightly, but it should provide a boundary approximately like:

    class SigningWorkspaceShellSurface:
        def install_widget_exports(self) -> None: ...
        def refresh_viewer(self) -> None: ...
        def refresh_document_review(self) -> DocumentReviewSummary: ...
        def search_document_text(self) -> DocumentTextSearchState: ...
        def next_document_text_match(self) -> DocumentTextSearchState: ...
        def previous_document_text_match(self) -> DocumentTextSearchState: ...
        def copy_current_document_text_match(self) -> str | None: ...
        def set_document_text_selection_mode(self, enabled: bool) -> bool: ...
        def copy_selected_document_text(self) -> str | None: ...
        def clear_selected_document_text(self) -> DocumentTextSelectionState: ...
        def apply_app_settings(self, settings: AppSettings) -> None: ...
        def set_logical_page_index(self, page_index: int) -> None: ...
        def logical_page_index(self) -> int: ...
        def set_signature_rect(...) -> SignatureRect: ...
        def signature_rect(self) -> SignatureRect | None: ...
        def set_selected_certificate_configuration_id(self, configuration_id: str | None) -> None: ...
        def selected_certificate_configuration_id(self) -> str | None: ...
        def signature_appearance(self) -> SignatureAppearance | None: ...
        def is_sign_action_enabled(self) -> bool: ...
        def choose_output_pdf_path(self) -> str | None: ...
        def refresh_certificate_configurations(self) -> CertificateCatalog: ...
        def submit_sign_request(self) -> SigningRequest | None: ...
        def open_signed_output(self) -> str | None: ...

The helper may delegate many of those calls straight into the already-extracted bridges, sessions, or workflows. The point of the slice is ownership and concentration reduction, not behavior reinvention.

Revision note: Created on 2026-06-05 by Codex for the next signing-workspace hybrid `4+5` tracer bullet after the properties-panel extraction slice.
Revision note: Updated on 2026-06-05 by Codex after implementation, focused validation, and the architecture-doc reconciliation that added the explicit shell-surface helper ownership record.
