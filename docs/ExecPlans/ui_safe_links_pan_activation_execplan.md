# Implement Pan-only PDF link activation and internal navigation

This ExecPlan is a living document maintained under `.agents/skills/write-execplan/PLANS.md`. It
is a bounded behavior child of `docs/ExecPlans/ui_safe_links_external_changes_execplan.md` and
the UI compliance parent. It depends on the already-complete neutral QtPdf link-inspection child,
but it does not implement source-change reload, Locate/Close, or the condition-only banner.

## Purpose / Big Picture

After this slice, a user can click a PDF link while the viewer is in Pan mode and receive the
policy-approved result. A valid internal link changes the visible page and can be reversed with
Back and Forward. An HTTP(S) or mailto link produces a bounded confirmation request without
launching anything; file, executable, JavaScript, embedded-launch, and unknown destinations remain
blocked with a safe status message. Clicking in Select Text or Place Signature mode never activates
a link, and dragging in Pan mode still pans instead of activating a link. The behavior is
demonstrated by pure application tests and an offscreen Qt interaction test.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/ui_safe_links_source_safety_contracts_execplan.md` supplies the pure
  allow/confirm/block policy and Pan-only mode gate.
- [x] `docs/ExecPlans/ui_safe_links_contract_hardening_execplan.md` closes unknown-identity,
  malformed-destination, and mode-gating policy cases.
- [x] `docs/ExecPlans/ui_pdf_link_inspection_execplan.md` supplies `DocumentLink` facts with
  PDF-space rectangles from `QtPdfRenderBackend`.
- [ ] `docs/ExecPlans/ui_document_lifecycle_recovery_execplan.md` remains open; this child must
  not reload or replace a workspace when a source changes.

## Progress

- [x] (2026-08-10) Explorer audit identified the smallest usable consumer boundary: application
  hit testing and policy projection, a typed Qt click callback, internal page navigation/history,
  and non-executing external/blocked outcomes.
- [x] (2026-08-10) Confirmed the production viewer defaults to `PopplerPdfRenderBackend`, whose
  geometry adapter is QtPdf; composition must expose link inspection without widening the generic
  raster-render protocol.
- [x] (2026-08-10) Added the Qt-free `DocumentLinkActivationService` and `ViewerLinkHistory`.
  Hit testing uses inclusive normalized rectangle edges, page matching, existing safety policy,
  and branch-resetting page-index Back/Forward state.
- [x] (2026-08-10) Delegated optional link inspection through `PopplerPdfRenderBackend` and wired
  the capability, typed external-confirmation callback, internal navigation, blocked status, and
  history methods through the signing-workspace composition/runtime seams.
- [x] (2026-08-10) Distinguished stationary Pan clicks from real Pan drags in `viewer_widget.py`,
  mapped clicks through the existing rotation-aware view-to-PDF transform, and kept Text/Signature
  clicks inert.
- [x] (2026-08-10) Added focused application/backend/runtime/widget coverage plus generated QtPdf
  fixtures for 0/90/180/270-degree rotation and non-zero page origins. Real offscreen PySide6
  coverage proves Pan click, Pan drag suppression, and Text/Signature inertness.
- [x] (2026-08-10) Focused validation is `183 passed`; full regression is `1417 passed, 20 skipped,
  1 warning`. Ruff, `pip check`, and diff checks pass. The bounded GUI audit reaches the known
  isolated `SingleInstanceUnavailable` endpoint, leaves no process, and removes its temp root.
- [x] (2026-08-10) Reconciled `docs/ARCHITECTURE.md` and the safe-links parent handoff; the
  remaining parent work is external-confirmation UI and source-change recovery, not this child.
  Commit completion follows after the final regression run.

## Surprises & Discoveries

- Observation: the live viewer rasterizes with Poppler while QtPdf supplies page geometry.
  Evidence: `src/foliaseal/infra/render/poppler_backend.py` delegates geometry to a
  `QtPdfRenderBackend`; the generic `PdfRenderBackend` protocol intentionally has no link method.
- Observation: `PdfViewerWidgetAdapter` already starts Pan drags in `mousePressEvent` and has a
  separate selection path, so a click callback must be emitted only on a left-button release that
  did not move beyond the existing drag threshold.
  Evidence: `src/foliaseal/presentation/qt/viewer_widget.py` tracks `_pan_origin` separately from
  `_drag_origin` and currently drops Pan clicks without a callback.
- Observation: QtPdf extraction tests currently cover only an unrotated, zero-origin page.
  Evidence: `tests/integration/test_qt_pdf_link_inspection.py`; this child must add transformed
  page evidence before using rectangles for production hit testing.

## Decision Log

- Decision: keep link inspection out of `PdfRenderBackend` and expose it through the optional
  `DocumentLinkInspector` capability.
  Rationale: raster-only/null/fake backends should not gain a mandatory annotation API, while the
  live Poppler adapter can delegate to its existing QtPdf geometry backend.
  Date/Author: 2026-08-10 / Codex.
- Decision: represent a no-hit as a typed activation result with no `LinkDecision`, and represent
  external confirmation and blocked outcomes as non-executable callbacks carrying only the
  bounded `LinkDecision`.
  Rationale: the viewer must distinguish “nothing was clicked” from a policy decision, and no
  callback may contain a launcher or perform I/O.
  Date/Author: 2026-08-10 / Codex.
- Decision: store only page indices in the lightweight Back/Forward history.
  Rationale: UI_SPEC requires document navigation history, not restoration of scroll/zoom or draft
  state; page-index history is deterministic and does not couple the model to Qt widget state.
  Date/Author: 2026-08-10 / Codex.
- Decision: do not combine source-change recovery with this slice.
  Rationale: draft-preserving reload and Locate/Ignore/Close need a separate lifecycle seam and
  must not be hidden inside link activation.
  Date/Author: 2026-08-10 / Codex.

## Outcomes & Retrospective

The viewer now consumes neutral QtPdf link facts through a Qt-free activation service. Pan clicks
resolve internal navigation/history or bounded external/blocked policy outcomes; Pan drags and
other interaction modes remain inert. External confirmation UI and source-change recovery remain
open in the parent. Focused validation is `183 passed`; full regression is
`1417 passed, 20 skipped, 1 warning`. The real offscreen interaction test and transformed-page fixtures pass, while the
bounded GUI audit reaches the known isolated `SingleInstanceUnavailable` endpoint with no leftover
process or temporary root.

## Context and Orientation

FoliaSeal is a local Qt PDF signing application. `src/foliaseal/application/document_links.py`
contains the Qt-free `DocumentLink` value and `DocumentLinkInspector` protocol. The concrete
`QtPdfRenderBackend.inspect_links()` adapter extracts link rectangles and destinations without
opening them. `src/foliaseal/application/document_safety.py` classifies a raw destination as
internal-allowed, external-confirmation, or blocked and only allows activation in Pan mode.

`ViewerWorkflow` owns the current rendered page, page geometry, rotation, zoom, pan values, and the
existing view-to-PDF coordinate conversion. `PdfViewerWidgetAdapter` creates the Qt widget and
currently treats a Pan left press/release as a pan gesture even when the pointer did not move.
`SigningWorkspaceRuntime` and `_assemble_signing_workspace_composition()` are the public Qt
composition seams; they already route viewer selection, mode changes, navigation, and status
messages without exposing private widget internals.

The live app constructs `PopplerPdfRenderBackend` for pixels. That adapter owns a QtPdf geometry
backend, so the optional inspector must be delegated there rather than changing the required
`PdfRenderBackend` protocol. No URL launcher, browser call, subprocess, source reload, or signing
draft mutation belongs in this child.

## Plan of Work

Create `src/foliaseal/application/document_link_activation.py` with a Qt-free
`DocumentLinkActivation` result and `DocumentLinkActivationService`. The service accepts the
current interaction mode, current page, PDF-space click coordinates, and page-local
`DocumentLink` values. It selects the first normalized rectangle containing the point using
inclusive edge semantics, ignores links for another page, calls `classify_link_destination()`, and
returns either a no-hit result or the selected link plus its typed `LinkDecision`. It must not read
files, launch URLs, or mutate viewer state.

In the same module, add `ViewerLinkHistory` (or an equivalently named small immutable-state model)
that records page-index transitions caused by accepted internal links, clears Forward entries after
a new link transition, and returns typed Back/Forward targets without calling Qt. Repeated links to
the current page do not create a history entry. Export the new contracts through the lazy
application package exports and cover them with unit tests for multi-rectangle links, boundaries,
no-hit, page mismatch, all policy kinds, mode gating, and Back/Forward branching.

Extend `PopplerPdfRenderBackend` with an optional `inspect_links()` method that delegates to a
callable inspector on its geometry backend and raises a precise unavailable error when no inspector
exists. Do not add this method to the required `PdfRenderBackend` protocol. The default production
composition should pass the backend capability to the runtime as a `DocumentLinkInspector | None`
or equivalent typed port, and tests must prove both the QtPdf-backed default path and the explicit
unavailable path.

Add a runtime callback such as `on_viewer_link_click(pdf_x, pdf_y)` that obtains the current page
and snapshot, asks the inspector for page links, resolves the activation result, and handles each
result without private widget access. Internal allowed results record history, call the existing
`ViewerWorkflow.jump_to_page()` and refresh the viewer through the existing runtime/navigation
path, and emit a navigation status. External confirmation results emit a typed bounded request to
the existing status/host callback; they do not launch anything in this slice. Blocked results emit
the policy reason through the existing status callback. Add runtime methods for Back and Forward
that consume history targets and use the same navigation refresh path. If the inspector is
unavailable or inspection fails, emit a concise status/error and leave the page and draft unchanged.

Extend `PdfViewerWidgetAdapter.create()` with an optional typed link-click callback. In Pan mode,
remember the press point and, on release, emit a click only when the pointer stayed within the
existing click threshold; a real drag must continue to pan and must never emit the callback.
Convert the view point to PDF coordinates using the current snapshot, zoom, pan, page box, and
rotation through the existing coordinate-transform helper. Text and Signature modes must bypass
the callback entirely. Add Back and Forward controls/shortcuts only through the existing public
viewer/runtime action seam; do not put history state in the widget.

Update `docs/ExecPlans/ui_safe_links_external_changes_execplan.md` to list this child as complete
when finished and to keep source-change recovery explicitly open. Update `docs/ARCHITECTURE.md`
with the activation service, history model, optional Poppler delegation, and the non-responsibility
for URL launching/reload. Do not add screenshots or generated PDFs to the repository; generated
fixtures belong under ignored temporary/artifact roots only.

## Milestones

### Milestone 1: prove the pure activation and history boundary

Add red tests for hit rectangles, policy outcomes, mode gating, and Back/Forward branching. Create
the Qt-free service and history model until those tests pass. This milestone is complete when a
novice can run the focused application test files and see the no-hit/internal/confirm/block cases
without importing PySide6.

### Milestone 2: expose the optional production inspector and runtime outcomes

Delegate inspection through Poppler, inject the capability through composition, and add runtime
methods for internal navigation, external confirmation requests, blocked status, Back, and
Forward. Focused composition/runtime tests must show that unavailable inspection leaves the draft
and page unchanged and that internal links use the existing render/navigation path.

### Milestone 3: wire safe Pan clicks and prove the complete interaction path

Add the viewer callback and click-vs-drag logic, then exercise it with offscreen Qt tests for Pan
click, Pan drag, Text click, and Signature click. Include a generated fixture with a rotated page
and a non-zero page box (or a direct adapter/coordinate test that proves the same transformation)
so the link rectangle used for hit testing is consistent with UI_SPEC rotation/page geometry.
Run the full suite, bounded GUI lifecycle audit, compliance review, architecture update, and commit.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal` using the checked-in virtual environment.

    .venv/bin/pytest -q tests/unit/test_document_link_activation.py tests/unit/test_poppler_render_backend.py tests/unit/test_qt_signing_workspace_runtime.py
    .venv/bin/pytest -q tests/unit/test_qt_safe_links_external_changes.py tests/unit/test_qt_viewer_widget.py
    .venv/bin/ruff check src tests
    QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q
    .venv/bin/python -m pip check
    git diff --check

For the bounded lifecycle audit, use an owned temporary root and always remove it:

    audit_root=$(mktemp -d /tmp/foliaseal-safe-links-XXXXXX)
    set +e
    timeout --foreground 30s env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf
    rc=$?
    set -e
    printf 'gui_rc=%s\n' "$rc"
    ps -eo pid=,cmd= | rg 'FoliaSeal|foliaseal|PySide6|pytest' | rg -v 'rg ' || true
    rm -rf "$audit_root"
    test ! -e "$audit_root"

The known isolated environment may still return `SingleInstanceUnavailable` before window
creation; that is a lifecycle limitation, not evidence of link activation. No FoliaSeal process or
temporary root may remain after the audit.

## Validation and Acceptance

The pure tests must prove that a click on any rectangle edge resolves exactly one link, that a
point outside all rectangles is a no-hit, and that links on another page are ignored. They must
also prove Pan-only policy projection for internal, HTTP(S)/mailto, and blocked destinations and
that history Back/Forward behaves correctly after branching.

The runtime/composition tests must prove that the default Poppler graph delegates to QtPdf link
inspection, an unavailable optional capability produces a safe status without mutation, internal
navigation changes the page through `ViewerWorkflow`, and external/blocked outcomes never call a
launcher. The Qt tests must prove Pan click callback, Pan drag suppression, and no callback in Text
or Signature mode. Rotated/non-zero-origin evidence must pass before the plan claims production
hit-testing support.

Run the complete suite and expect all tests green with no new failures; record the exact count in
this plan. Ruff, `pip check`, and `git diff --check` must pass. The bounded audit must remove its
owned temporary root and leave no FoliaSeal/PySide6 process. The safe-links parent remains open
for external confirmation UI and source-change recovery until their own children land.

## Idempotence and Recovery

All new tests use temporary generated PDFs and in-memory collaborators. Re-running them is safe.
If a Qt test leaves a widget or process alive, stop only the process started by the audit, remove
its owned temporary root, and rerun the focused test in a fresh process. Do not delete repository
fixtures or broad system directories. If composition wiring fails, retain the typed unavailable
path rather than silently treating “no links” as proof that a PDF has none.

## Artifacts and Notes

Keep generated PDFs and screenshots under ignored `artifacts/` or a temporary directory. Record
only concise test counts, the bounded GUI return code/cleanup result, and the exact changed files
in this plan. Do not commit URLs beyond test fixture values, private data, credentials, or machine-
local absolute paths.

## Interfaces and Dependencies

The application boundary must remain Qt-free:

    DocumentLinkActivationService.resolve(
        *,
        page_index: int,
        pdf_x: float,
        pdf_y: float,
        links: tuple[DocumentLink, ...],
        interaction_mode: LinkInteractionMode,
    ) -> DocumentLinkActivation

`DocumentLinkActivation` contains the selected `DocumentLink | None`, selected `PdfRect | None`,
and `LinkDecision | None`; all three are absent for a no-hit. `ViewerLinkHistory` exposes typed
`record_internal_navigation(from_page_index, to_page_index)`, `back()`, `forward()`, and
`reset(current_page_index)` operations and no Qt or file-I/O dependency.

`PopplerPdfRenderBackend.inspect_links(document_path, page_index)` is an optional concrete
capability delegated to a geometry backend; the required `PdfRenderBackend` protocol remains
unchanged. `PdfViewerWidgetAdapter.create(..., on_link_click=...)` accepts one optional callback
with PDF-space coordinates. `SigningWorkspaceRuntime` owns inspection, policy projection,
history, navigation, and status/confirmation emission; widgets only detect gestures and map
coordinates. No interface may carry a URL launcher, browser callback, source reload operation, or
signing-draft mutation.

Revision note: 2026-08-10 / Codex. Created from the post-link-inspection explorer audit to provide
the next complete, bounded safe-links consumer slice without combining source-change lifecycle
recovery.
