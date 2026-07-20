# Restore reopened signed-PDF rendering fidelity

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, a person who signs and reopens a PDF in FoliaSeal sees the same on-page visible signature that was written to the PDF, rather than a blank canvas beside otherwise-correct verification text. The observable proof is the real-Qt audit in `scripts/live_gui_parent_audit.py`: its reopened checkpoint shows the signed mark and its JSON report has `"status": "passed"`.

## Child ExecPlan Dependencies

- [x] The parent GUI signing-setup recovery work created reusable signing objects and the sign/reopen workflow.
- [x] The retained signed output and a Poppler command-line render proved that the blank reopened canvas was a QtPdf rasterisation defect rather than a signing or reopen-lifecycle defect.
- [x] The parent audit runner now drives the visible mounted refinement control, all reusable-object selections, output/confirmation/sign/reopen controls, and the reopened visual-fidelity assertion through a real Qt application.

## Progress

- [x] (2026-07-19) Added `PopplerPdfRenderBackend`, which delegates page geometry to QtPdf and uses the installed `pdftoppm` program only for live interactive-viewer pixels; `FoliaSealAppFrame` now uses it by default.
- [x] (2026-07-19) Added focused diagnostic coverage for unavailable `pdftoppm`/Qt geometry, nonzero Poppler exit, missing raster output, one-based Poppler page selection, zoom-to-DPI conversion, opaque RGBA conversion, and app-frame default wiring. Focused renderer/app-frame/viewer checks passed (63 tests), as did Ruff and `git diff --check`.
- [x] (2026-07-19) Drove the mounted `Refine current setup...` control and the visible reusable-object/output/confirmation/sign/reopen controls in the full real-Qt audit. `DISPLAY=:0 timeout 120s .venv/bin/python scripts/live_gui_parent_audit.py --artifacts-dir /tmp/foliaseal-live-gui-parent-audit` exited successfully with `audit.json` status `passed`, nine checkpoints, and the reopened visible signature plus verification state.
- [x] (2026-07-19) Reconciled `docs/ARCHITECTURE.md`, this child plan, and the parent plan with the live renderer split and completed evidence.

## Surprises & Discoveries

- Observation: QtPdf reports that the signed PDF is ready and has one page, yet returns an entirely transparent raster for it.
  Evidence: the pre-fix retained audit at `/tmp/foliaseal-live-gui-parent-audit-fidelity-failure/audit.json` and the renderer investigation both found a 612 by 792 transparent Qt image while Poppler displayed the signature.

- Observation: the repaired real-Qt walkthrough produced an opaque reopened page containing the signed mark and verification messaging.
  Evidence: `/tmp/foliaseal-live-gui-parent-audit/audit.json` records `"status": "passed"`, all nine checkpoints, the retained `signed-output.pdf`, and `09-reopened-and-verified.png`.

- Observation: the system-native chooser is not reliably automation-addressable in the bounded local display environment.
  Evidence: the audit uses a narrow non-native Qt save-dialog proxy only for output-path selection; all FoliaSeal workflow controls remain visible, semantic Qt controls. This is an audit-driver limitation, not a product defect.

## Decision Log

- Decision: use Poppler for interactive viewer pixels while retaining `QtPdfRenderBackend` for PDF page boxes, rotation, and coordinate transforms.
  Rationale: existing placement calculations already rely on QtPdf geometry and were correct; only raster pixels were defective. This smaller split repairs the user-visible failure without replacing unrelated geometry behavior.
  Date/Author: 2026-07-19 / Codex

- Decision: retain QtPdf defaults for canonical preview generation and phase-two/phase-three evidence unless a focused failure proves they are affected.
  Rationale: those paths render newly generated preview PDFs or dedicated evidence rather than reopening the affected signed document. Broad replacement would increase validation scope without evidence of a defect.
  Date/Author: 2026-07-19 / Codex

- Decision: keep the real-Qt audit runner as durable acceptance evidence and isolate its temporary artifacts under `/tmp`.
  Rationale: the runner exercises actual mounted controls and now asserts visible reopened fidelity, while its `finally` block closes every top-level Qt window. The non-native save-dialog proxy is confined to the environment-specific chooser edge.
  Date/Author: 2026-07-19 / Codex

## Outcomes & Retrospective

The implementation fixed the reopened live viewer, closed the audit-semantic and diagnostic-test review findings, and passed the complete end-to-end real-Qt audit. The parent recovery plan can now rely on this child for viewer-fidelity acceptance rather than treating external Poppler output as a substitute for in-app visual evidence.

## Context and Orientation

`src/foliaseal/presentation/qt/app_frame.py` creates the live workspace and supplies its rendering backend through `app_frame_workspace_open.py` to `application/viewer_workflow.py`. A rendering backend returns page pixels and PDF-space geometry. `QtPdfRenderBackend` uses PySide6's QtPdf bindings for both; `PopplerPdfRenderBackend` in `src/foliaseal/infra/render/poppler_backend.py` keeps QtPdf for geometry but runs the locally installed `pdftoppm` executable to create an opaque RGBA (red, green, blue, alpha) image for the viewer.

`scripts/live_gui_parent_audit.py` opens a real FoliaSeal window against a temporary configuration directory, creates a certificate, saves reusable profiles, places and signs, reopens, takes screenshots, and closes all Qt windows in a `finally` block. It may use a non-native Qt save dialog proxy because the system-native chooser is opaque to an unattended Qt event loop; it must not bypass any visible FoliaSeal workflow control.

## Plan of Work

The production app frame keeps `PopplerPdfRenderBackend` as its default. `tests/unit/test_poppler_render_backend.py` covers absent executable, unavailable Qt geometry, nonzero Poppler exit, and missing output PNG with faked executable/subprocess boundaries, so those failure checks do not depend on a system program.

`scripts/live_gui_parent_audit.py` opens refinement through the visible `Refine current setup...` button and reads profiles/presets through visible dialog and sidebar combo boxes rather than private panel fields. Its bounded non-native QFileDialog proxy remains only at the native-chooser automation edge and is recorded as audit evidence.

`docs/ARCHITECTURE.md` and the parent plan record the final split, external late-resolved `pdftoppm` requirement, passing audit, and intentional canonical-preview/harness scope boundary. Generated audit images remain ephemeral `/tmp` evidence rather than repository content.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Run focused checks:

       .venv/bin/python -m pytest -q tests/unit/test_poppler_render_backend.py tests/unit/test_qt_app_frame.py
       .venv/bin/ruff check src/foliaseal/infra/render scripts/live_gui_parent_audit.py tests/unit/test_poppler_render_backend.py

   Expect all tests and lint checks to pass.

2. Run the full GUI audit on the local display:

       DISPLAY=:0 timeout 120s .venv/bin/python scripts/live_gui_parent_audit.py --artifacts-dir /tmp/foliaseal-live-gui-parent-audit

   Expect `audit.json` to contain `"status": "passed"`, nine screenshots through `09-reopened-and-verified.png`, and no remaining FoliaSeal window after the runner exits.

3. Run the repository suite:

       .venv/bin/python -m pytest -q

   Expect a zero exit status. Then run `git diff --check` before committing.

## Validation and Acceptance

Acceptance is met by both automated and visible evidence. Focused backend tests prove actionable Poppler/Qt-geometry failures; the live audit creates/selects a certificate, saves/reselects appearance/placement/preset objects, drags a visible placement, chooses output, confirms, signs, reopens, and shows the signature plus verification text. The runner closes every window it opened even when a checkpoint fails.

## Idempotence and Recovery

The unit tests do not write persistent application data. The audit uses a fresh temporary workspace and may be rerun after removing only `/tmp/foliaseal-live-gui-parent-audit`. If a run fails, inspect that directory's `audit.json` and screenshots, record the failure in this plan, close any remaining FoliaSeal windows, then retry after the focused fix. Do not remove files in the repository or in the user's application configuration.

## Artifacts and Notes

The passing audit stores temporary evidence outside the repository:

    /tmp/foliaseal-live-gui-parent-audit/audit.json
    /tmp/foliaseal-live-gui-parent-audit/09-reopened-and-verified.png

The JSON file names all nine checkpoints and the output PDF. It is intentionally ephemeral: source, tests, and this plan are the durable record.

## Interfaces and Dependencies

`PopplerPdfRenderBackend` implements the existing `PdfRenderBackend` protocol with `diagnostics()`, `get_page_geometry(document_path, page_index)`, and `render_page(RenderPageRequest)`. It late-resolves `pdftoppm` through `shutil.which`; its diagnostic must name the missing program. It invokes one-based Poppler page numbers for the zero-based FoliaSeal request and returns opaque RGBA bytes. It must never change the `QtPdfRenderBackend` geometry contract or the dependency-injection constructor parameters used by test callers.

## Plan revision note

Created on 2026-07-19 after the parent plan's first renderer compliance review found that the functional Poppler fix needed audit-semantic, failure-test, and documentation closeout before the parent could truthfully complete. Revised on 2026-07-19 after those findings closed: the focused checks passed, the nine-checkpoint real-Qt audit passed, its artifacts remained under `/tmp`, and its cleanup closed all top-level Qt windows.
