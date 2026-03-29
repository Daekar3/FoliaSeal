# FoliaSeal

Foundations for a Linux desktop PDF signing app.

## What is included
- package skeleton with architecture-aligned module boundaries (`presentation`, `application`, `domain`, `infra`)
- `DocumentOperation` domain contract and operation registry with capability enable/disable flags
- initial config schemas for trust profile, timestamp policy, and signature presets
- Phase 1 headless signing orchestration (`SignPdfUseCase`) with:
  - compatibility policy enforcement for PDF `1.4` to `2.0`
  - strict PDF version parsing (rejects invalid/non-finite version strings)
  - incremental-signing version-preservation checks
  - stable failure-code mapping and structured signing results
  - output-path conflict detection using normalized filesystem paths
  - temp-file + atomic replace output writes with temp-file cleanup
- unit tests for schema validation, compatibility policy, operation registry behavior, and signing orchestration
  - signing orchestration tests include success path plus explicit failure-code mapping checks
    (`OUTPUT_PATH_INVALID`, `PKCS12_WRONG_PASSWORD`, `PKCS12_LOAD_FAILED`,
    `TSA_UNREACHABLE`, `TIMESTAMP_REQUIRED_BUT_MISSING`, `POST_VERIFY_FAILED`,
    `PDF_SIGNING_FAILED`, `ATOMIC_WRITE_FAILED`, `UNEXPECTED_INTERNAL_ERROR`)
- Phase 2 kickoff viewer foundations with:
  - render adapter abstraction (`infra.render`) and fallback backend diagnostics
  - deterministic view↔PDF coordinate transform utilities (zoom, pan, rotation, page-box offsets)
  - pre-sign PDF rectangle bounds validation helper
  - page render LRU cache policy primitives for upcoming viewer integration
  - Qt render backend that augments QtPdf rendering with cached parsed PDF page metadata when available, while falling back to QtPdf page-size geometry for documents the lightweight parser cannot decode and disabling selection-to-PDF mapping on those lossy fallback pages
  - Qt image-buffer extraction hardened for pointer-style `QImage.bits()` APIs used by PySide bindings
  - `ViewerSession` helper for page navigation and zoom/fit interactions
  - `ViewerPerformanceTracker` helper for first-render and navigation timing metrics
  - Phase 2 evidence formatter utilities to capture timing snapshots alongside runtime environment details
  - CLI helper (`foliaseal phase2-evidence ...` or `python -m foliaseal phase2-evidence ...`) to generate Phase 2 markdown timing evidence snippets, including optional auto-capture of startup launch-readiness from a probe command or long-running GUI executable, plus idle memory and bundle-size metrics for FR-16 evidence
  - `ViewerWorkflow` helper that wires renderer output, page geometry, selection transforms, and timing capture for Qt widget integration
  - Qt preview widget adapter (`presentation.qt`) with wheel zoom, scrollbar-backed pan syncing, and drag-selection wiring to viewer workflow
- unit tests expanded for render adapter fallback behavior, coordinate transforms, cache policy, viewer session behavior, Qt widget dependency diagnostics, and deterministic Qt backend availability coverage

## Phase 3 integration contracts

The next implementation step is expected to add a signing-focused workflow layer on top of the existing viewer platform. These are the intended seams for downstream work and testing, even before the full UI is complete.

- `SigningDraftWorkflow` should own the in-session signing draft state for Phase 3.
  - It should track the chosen page, placement rectangle, appearance/property settings, and validation state.
  - It should not duplicate viewer coordinate math or Qt event handling.
- `render_signing_preview()` should turn the normalized draft state into a preview representation.
  - It should be treated as the single source of truth for preview formatting.
  - The Qt shell should reuse it rather than rebuilding preview semantics in widget code.
- `compare_preview_to_request()` should be a narrow consistency check between the preview model and the final signing request.
  - It should be used to catch drift between the visible draft and the request payload.
  - It should not become a second preview renderer or a substitute for validation.
- The Qt signing shell should sit on top of the existing viewer platform.
  - It should reuse `ViewerWorkflow` for page rendering, geometry, and selection-to-PDF mapping.
  - It should reuse the Qt preview widget adapter for render/zoom/navigation behavior.
  - It should keep properties editing, preview refresh, and sign confirmation in the application/UI layers rather than re-implementing viewer math.
- Interactive resize handles are still a Phase 3 UI gap unless a later task adds them explicitly.
  - For now, treat placement and fine-tuning as the target contract, not as a promise that every editor-style affordance is already present.
- The key integration rule is to avoid duplicating semantics across layers.
  - Workflow code should normalize the draft.
  - Preview code should render that normalized state.
  - Qt code should orchestrate user interaction and dispatch, not reinterpret the model.

## Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .[dev]
ruff check .
python -m pytest -q
foliaseal
python -m foliaseal
```

## PyInstaller build

Build a one-dir bundle for FR-16 evidence capture:

```bash
.venv/bin/pip install -e .[dev]
./scripts/build_pyinstaller.sh
```

This produces:

- bundle directory: `dist/foliaseal`
- executable: `dist/foliaseal/foliaseal`

You can then generate a fuller Phase 2 evidence block against the packaged app:

```bash
.venv/bin/python -m foliaseal phase2-evidence \
  --first-render-ms 47.54 \
  --navigation-ms 49.35 \
  --navigation-ms 45.06 \
  --navigation-ms 47.68 \
  --navigation-ms 49.00 \
  --navigation-ms 47.79 \
  --navigation-ms 41.84 \
  --navigation-ms 47.68 \
  --navigation-ms 48.70 \
  --navigation-ms 47.14 \
  --navigation-ms 42.44 \
  --navigation-ms 47.98 \
  --navigation-ms 48.33 \
  --navigation-ms 53.64 \
  --navigation-ms 42.77 \
  --navigation-ms 47.17 \
  --navigation-ms 48.19 \
  --navigation-ms 54.07 \
  --navigation-ms 43.07 \
  --navigation-ms 46.57 \
  --navigation-ms 52.18 \
  --measure-startup-command dist/foliaseal/foliaseal \
  --startup-ready-after-seconds 0.75 \
  --collect-runtime-footprint \
  --bundle-dir dist/foliaseal \
  --check-qt-runtime \
  --qa-checklist-file artifacts/phase2_manual_qa_results.md \
  --write-markdown-file artifacts/phase2_runtime_evidence.md
```

`--measure-startup-command` now measures launch readiness rather than waiting for a normal process exit. Short-lived probe commands return their full runtime; long-running GUI commands are treated as started once they stay alive for the configured readiness window and are then terminated by the helper.

If you do not yet have interactive first-render/navigation timings from a manual Qt session, you can still use the same command shape without the timing flags to refresh the packaging-side evidence in [`artifacts/phase2_runtime_evidence.md`](/home/daekar/SignPDF/Scratch/artifacts/phase2_runtime_evidence.md) while leaving the FR-13 items explicitly unrecorded.

## Interactive Phase 2 harness

To capture first-render and navigation timings during a real Qt session, launch the harness against a representative PDF:

```bash
.venv/bin/python -m foliaseal phase2-viewer-harness \
  --pdf-path "/path/to/representative.pdf" \
  --summary-json-path artifacts/phase2_harness_capture.json \
  --evidence-command-path artifacts/phase2_evidence_command.sh \
  --checklist-results-path artifacts/phase2_manual_qa_results.md
```

The harness opens the Qt viewer, records first-render and page-navigation timings automatically, logs selection/error events in the window, and prints a ready-to-run `phase2-evidence` command when you close it.
It also writes a JSON capture with the recorded timing samples and any saved selection callback count, plus a run-specific checklist results file at [`artifacts/phase2_manual_qa_results.md`](/home/daekar/SignPDF/Scratch/artifacts/phase2_manual_qa_results.md).
Review that generated checklist, check any remaining manual-only observations, and then run the printed evidence command so the final markdown report and checklist status come from the same run artifacts.

## Phase 3 acceptance harness

To make Phase 3 acceptance easier, there is also an interactive signing-shell harness that writes a structured capture and a partially completed FR-3B worksheet for you.

Run it against a representative PDF:

```bash
.venv/bin/python -m foliaseal phase3-signing-harness \
  --pdf-path "/path/to/representative.pdf" \
  --summary-json-path artifacts/phase3_harness_capture.json \
  --checklist-results-path artifacts/phase3_fr3b_acceptance_results.md
```

What it does:

- launches the current Qt signing shell on the chosen PDF
- records a structured capture of preview availability, selection count, sign-request count, and any surfaced errors
- writes a results file seeded from the Phase 3 checklist at [`artifacts/phase3_fr3b_acceptance_results.md`](/home/daekar/SignPDF/Scratch/artifacts/phase3_fr3b_acceptance_results.md)
- automatically checks the acceptance items that can be observed directly from the harness

What still remains manual:

- parity judgment against Acrobat or PDF-XChange
- qualitative UX notes
- signed-output fidelity judgments
- any task steps that require human interpretation rather than observable harness events
