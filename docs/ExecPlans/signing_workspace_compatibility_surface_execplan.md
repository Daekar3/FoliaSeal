# Split The Signing Workspace Compatibility Surface

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

This slice keeps the live signing workspace behavior stable while separating two different outer-shell responsibilities that are still mixed together today. After this change, the production shell helper should own only the narrow caller-facing workspace port, while a separate compatibility surface should own the broad widget-export and harness/testing access that still exists. Users should still be able to open a PDF, use `Save As...`, refresh certificate configurations, drive the Phase 3 harness, and run the focused shell tests exactly as before, but the code should make it clear which surface is production-facing and which surface exists for compatibility and evidence tooling.

## Child ExecPlan Dependencies

- [x] (2026-06-05 18:20Z) No child ExecPlans are required for this bounded shell-surface split.

## Progress

- [x] (2026-06-05 18:13Z) Completed the required `explorer-light` audit and fixed the next slice to separating the narrow production shell surface from the broad compatibility/harness surface.
- [x] (2026-06-05 18:18Z) Re-read `signing_workspace_shell_surface.py`, the current shell method delegation block, the app-frame port, and the main Phase 3 harness touch points that still force a broad shell export surface.
- [x] (2026-06-05 19:02Z) Added `signing_workspace_compatibility_surface.py` and moved the broad widget export block plus harness/testing convenience methods out of `signing_workspace_shell_surface.py`.
- [x] (2026-06-05 19:09Z) Narrowed `signing_workspace_shell_surface.py` so it owns only the small caller-facing production verbs that remain part of the live shell port.
- [x] (2026-06-05 19:18Z) Updated shell composition and Phase 3 harness call sites to consume the new compatibility surface explicitly while preserving the live widget contract.
- [x] (2026-06-05 19:31Z) Added focused tests proving the compatibility surface exists and the Phase 3 harness helpers can use it without depending on the production port helper.
- [x] (2026-06-05 19:38Z) Ran focused validation with the shell subset, harness subset, app-frame subset, `ruff check`, and `git diff --check`.
- [x] (2026-06-05 20:04Z) Completed the required architectural/spec compliance review and reconciled docs to reflect the final shell-surface split.
- [x] (2026-06-05 20:08Z) Updated documentation to final state and prepared the slice for commit.

## Surprises & Discoveries

- Observation: At the start of this slice, the biggest remaining shallow seam was no longer constructor wiring or review/action orchestration; it was the mixed outer API shape of the shell helper.
  Evidence: Before the split landed, `SigningWorkspaceShellSurface.install_widget_exports()` installed both production verbs and broad harness/testing helpers onto the returned widget, while `signing_shell_port.py` already showed the real production contract was much smaller.
- Observation: the harness already had a natural seam for this split because it mostly needed deep viewer/panel access and refresh helpers, not the app-frame production port.
  Evidence: `phase3_harness.py` now resolves `getattr(shell, "compat_surface", shell)` and uses that named compatibility object for preview capture, scenario application, and last-result inspection.
- Observation: the first compliance review found doc drift only after the code split landed.
  Evidence: `docs/ARCHITECTURE.md` still attributed the widget export block and deep helper family to `signing_workspace_shell_surface.py` until the closeout reconciliation updated the repo map, Qt presentation-layer summary, debt note, and change log.

## Decision Log

- Decision: keep the live widget behavior and top-level shell contract stable in this slice even if the implementation introduces a new named compatibility surface.
  Rationale: this tracer bullet is about clarifying ownership of the outer shell API, not about forcing the app frame, harness, and focused shell tests to change behavior all at once.
  Date/Author: 2026-06-05 / Codex

- Decision: split the mixed helper by responsibility rather than trying to delete all broad shell access in one pass.
  Rationale: `phase3_harness.py` still needs deep shell access for evidence capture and scenario application. Quarantining that access behind a named compatibility surface is a narrow step that improves the architecture without widening into a multi-slice purge.
  Date/Author: 2026-06-05 / Codex

## Outcomes & Retrospective

This slice landed as a behavior-preserving ownership split between two shell-local helpers.

- `signing_workspace_shell_surface.py` now owns only the narrow caller-facing production verbs: live `app_settings` mirroring plus `apply_app_settings(...)`, `choose_output_pdf_path()`, `refresh_certificate_configurations()`, `submit_sign_request()`, and `open_signed_output()`.
- `signing_workspace_compatibility_surface.py` now owns the broad widget export block, the named `widget.compat_surface`, deep viewer/panel/sidebar access, document-text commands, page/signature-rect helpers, and the harness/testing convenience surface.
- `signing_workspace_composition.py` now constructs both surfaces and bootstraps them in the right order, while `phase3_harness.py` uses the explicit compatibility surface when present and falls back to older fake shells when needed.

Focused validation passed:

- `tests/unit/test_qt_signing_shell.py -k 'compat_surface or refresh_viewer_uses_workspace_interaction_session_entrypoint or choose_output_pdf_path or refresh_certificate_configurations'` -> `5 passed`
- `tests/unit/test_phase3_harness.py -k 'apply_preview_matrix_scenario_syncs_viewer_to_signature_rect_page or run_phase3_signing_harness'` -> `4 passed`
- `tests/unit/test_qt_app_frame.py -k 'save_as_action_enables_after_open_and_routes_to_current_shell or choose_open_pdf or reopens_signed_output_from_shell_callback'` -> `4 passed`
- `ruff check` on the touched shell/composition/harness/test files -> clean
- `git diff --check` -> clean

The initial implementation became noncompliant only because the docs still described the pre-split `SigningWorkspaceShellSurface` ownership. That was reconciled without widening the slice: the repo map now lists `signing_workspace_compatibility_surface.py`, the Qt presentation-layer summary describes the narrow production surface versus the explicit compatibility surface, and the debt note/change log reflect that the compatibility-export boundary now lives in its own helper.

## Context and Orientation

`src/foliaseal/presentation/qt/signing_shell.py` returns a concrete Qt widget through `build_qt_signing_shell()`. That widget is not the `SigningWorkspaceWidget` instance itself; it is the close-aware `QWidget` stored on `SigningWorkspaceWidget.container`. Because of that, the shell installs a dynamic export block onto the returned widget so production callers, tests, and the Phase 3 harness can all reach what they need.

Recent slices extracted most of the internal behavior clusters:

- `src/foliaseal/presentation/qt/signing_workspace_action_bridge.py` owns shell-facing signing-action glue.
- `src/foliaseal/presentation/qt/signing_workspace_interaction_bridge.py` owns `WorkspaceInteractionPlan` execution.
- `src/foliaseal/presentation/qt/signing_workspace_review_bridge.py` owns the review/text bridge.
- `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py` owns the properties panel.
- `src/foliaseal/presentation/qt/signing_workspace_composition.py` owns constructor-time assembly and bootstrap ordering.

At plan-creation time, `src/foliaseal/presentation/qt/signing_workspace_shell_surface.py` still mixed several responsibilities. At that point the helper both:

- installs the dynamic widget export block on the returned shell widget;
- owns deep compatibility methods such as review refresh, document-text search/selection commands, page/rect setters, and signature-appearance helpers;
- and owns the actual narrow caller-facing verbs such as `apply_app_settings(...)`, `choose_output_pdf_path()`, and `refresh_certificate_configurations()`.

`src/foliaseal/presentation/qt/signing_shell_port.py` already showed the real production port was small. The app frame only needed the concrete widget plus the three verbs above. By contrast, `src/foliaseal/presentation/qt/phase3_harness.py` still reached deeply into the shell for `properties_panel`, `viewer_widget`, preview refresh, request snapshots, and scenario application. This slice was intended to preserve both use cases while making the ownership split explicit.

The key files for this slice are:

- `src/foliaseal/presentation/qt/signing_workspace_shell_surface.py`, which should become the narrow production shell surface;
- `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py`, the new helper module to add in this slice;
- `src/foliaseal/presentation/qt/signing_workspace_composition.py`, which should construct both surfaces and bootstrap their export/install behavior;
- `src/foliaseal/presentation/qt/signing_shell.py`, which should keep the same live shell methods while delegating compatibility concerns to the new helper;
- `src/foliaseal/presentation/qt/phase3_harness.py`, which should use the named compatibility surface for deep shell access instead of treating the broad dynamic export block as if it were the production port;
- `tests/unit/test_qt_signing_shell.py`, `tests/unit/test_qt_app_frame.py`, and `tests/unit/test_phase3_harness.py`, which provide the focused proof points for this boundary split;
- `docs/ARCHITECTURE.md`, which currently describes the shell surface as the owner of the remaining export block and must be updated if this split lands.

This slice must stay narrow. It may separate the production port from the compatibility/harness surface, adjust the focused tests and harness code needed to prove that split, and update the architecture docs. It must not redesign the app-frame port, the Phase 3 evidence-service program, the properties panel contract, or the signing/review/viewer application policies.

## Plan of Work

First, add a new shell-local helper module, `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py`, and move the broad widget export block plus the harness/testing convenience methods there. That helper should own the dynamic export installation on the returned widget, the deep access attributes such as `properties_panel` and `viewer_widget`, the review/text commands, the page/signature-rect helpers, and the explicit named compatibility surface exported as `widget.compat_surface`.

Second, edit `src/foliaseal/presentation/qt/signing_workspace_shell_surface.py` so it becomes a genuinely narrow production helper. It should keep only the caller-facing verbs that are part of the live shell port and closely related shell behavior: applying app settings, choosing the output path, refreshing certificate configurations, submitting a sign request, and reopening the signed output. It should stop owning the broad export installation and the harness/testing helper family.

Third, update `src/foliaseal/presentation/qt/signing_workspace_composition.py` and `src/foliaseal/presentation/qt/signing_shell.py` so they construct, install, and delegate through both helpers. The returned shell widget should still behave the same for existing callers, but the named compatibility surface should now be the explicit place where broad shell access lives.

Fourth, update `src/foliaseal/presentation/qt/phase3_harness.py` so its deep shell access flows through the named compatibility surface when available. The goal is not to break fake-shell tests; where necessary, a small fallback helper may treat older fake shells as their own compatibility surface.

Finally, run the focused validation commands, perform the required compliance review, reconcile `docs/ARCHITECTURE.md` and this ExecPlan, and commit the slice.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Add the compatibility-surface helper and narrow the production shell surface.

       apply_patch ... on src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py
       apply_patch ... on src/foliaseal/presentation/qt/signing_workspace_shell_surface.py
       apply_patch ... on src/foliaseal/presentation/qt/signing_workspace_composition.py
       apply_patch ... on src/foliaseal/presentation/qt/signing_shell.py
       apply_patch ... on src/foliaseal/presentation/qt/phase3_harness.py

2. Update focused tests only where the ownership split changes the best assertion point.

       apply_patch ... on tests/unit/test_qt_signing_shell.py
       apply_patch ... on tests/unit/test_phase3_harness.py
       apply_patch ... on tests/unit/test_qt_app_frame.py

3. Run focused validation.

       .venv/bin/python -m pytest tests/unit/test_qt_signing_shell.py -k 'compat_surface or refresh_viewer_uses_workspace_interaction_session_entrypoint or choose_output_pdf_path or refresh_certificate_configurations'
       .venv/bin/python -m pytest tests/unit/test_phase3_harness.py -k 'apply_preview_matrix_scenario_syncs_viewer_to_signature_rect_page or run_phase3_signing_harness'
       .venv/bin/python -m pytest tests/unit/test_qt_app_frame.py -k 'save_as_action_enables_after_open_and_routes_to_current_shell or choose_open_pdf or reopens_signed_output_from_shell_callback'
       .venv/bin/ruff check src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py src/foliaseal/presentation/qt/signing_workspace_shell_surface.py src/foliaseal/presentation/qt/signing_workspace_composition.py src/foliaseal/presentation/qt/signing_shell.py src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_harness.py tests/unit/test_qt_app_frame.py
       git diff --check

4. Run the required compliance review, reconcile docs if needed, and commit the slice.

## Validation and Acceptance

This slice is accepted when all of the following are true:

- `signing_workspace_shell_surface.py` no longer owns the broad widget export block or the deep harness/testing helper family;
- a dedicated compatibility helper owns the broad dynamic widget exports and exposes a named compatibility surface on the returned shell widget;
- the app-frame-facing port behavior remains stable for `choose_output_pdf_path()`, `apply_app_settings(...)`, and `refresh_certificate_configurations()`;
- the Phase 3 harness can still capture preview/signing state and apply preview-matrix scenarios using the new compatibility surface;
- the focused shell/app-frame/harness tests still pass;
- `docs/ARCHITECTURE.md` accurately describes the new split between the narrow production shell surface and the compatibility/harness surface.

Run:

    .venv/bin/python -m pytest tests/unit/test_qt_signing_shell.py -k 'compat_surface or refresh_viewer_uses_workspace_interaction_session_entrypoint or choose_output_pdf_path or refresh_certificate_configurations'
    .venv/bin/python -m pytest tests/unit/test_phase3_harness.py -k 'apply_preview_matrix_scenario_syncs_viewer_to_signature_rect_page or run_phase3_signing_harness'
    .venv/bin/python -m pytest tests/unit/test_qt_app_frame.py -k 'save_as_action_enables_after_open_and_routes_to_current_shell or choose_open_pdf or reopens_signed_output_from_shell_callback'

Then run:

    .venv/bin/ruff check src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py src/foliaseal/presentation/qt/signing_workspace_shell_surface.py src/foliaseal/presentation/qt/signing_workspace_composition.py src/foliaseal/presentation/qt/signing_shell.py src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_harness.py tests/unit/test_qt_app_frame.py
    git diff --check

Acceptance is behavioral. The returned shell widget, the app-frame port, and the Phase 3 harness should keep working the same from a user’s perspective; the architecture improvement is that the broad compatibility surface is now explicit instead of being mixed into the production helper.

## Idempotence and Recovery

This is a behavior-preserving extraction. It is safe to retry. If the harness or fake-shell tests still assume direct top-level shell access, preserve those top-level aliases for now and route them through the compatibility helper rather than widening the production helper again. Do not recover by moving mixed export logic back into `signing_workspace_shell_surface.py`; one narrow production helper plus one explicit compatibility helper should remain the end state of this slice.

If shrinking the production helper unexpectedly requires changing `signing_shell_port.py` or app-frame caller behavior, stop and defer that broader redesign to a later slice instead of widening this one.

## Artifacts and Notes

The most important evidence for this slice will be:

- a new compatibility-surface helper module that owns the broad widget export block;
- a visibly narrower `SigningWorkspaceShellSurface` focused on the production shell port;
- a focused harness proof that deep shell access now flows through `compat_surface`;
- focused shell/app-frame tests showing the live contract is stable.

## Interfaces and Dependencies

This slice uses the `In-process` dependency category.

At the end of the slice, the boundary should look approximately like:

    class SigningWorkspaceShellSurface:
        def install_port_exports(self) -> None: ...
        def apply_app_settings(self, settings: AppSettings) -> None: ...
        def choose_output_pdf_path(self) -> str | None: ...
        def refresh_certificate_configurations(self) -> CertificateCatalog: ...
        def submit_sign_request(self) -> SigningRequest | None: ...
        def open_signed_output(self) -> str | None: ...

    class SigningWorkspaceCompatibilitySurface:
        def install_widget_exports(self) -> None: ...
        def refresh_viewer(self) -> None: ...
        def refresh_document_review(self) -> DocumentReviewSummary: ...
        def search_document_text(self) -> DocumentTextSearchState: ...
        def set_signature_rect(...) -> SignatureRect: ...
        ...

The exact file-local names can vary slightly, but the narrow production helper must stop owning the compatibility export block, and the returned shell widget must expose `compat_surface` as the named home for the broad shell access used by the harness and focused tests.

Revision note: Created on 2026-06-05 by Codex for the next signing-workspace hybrid `4+5` tracer bullet after the workspace-composition extraction slice.
