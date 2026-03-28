# Phase 2 Manual QA Results

Source checklist: `phase2_manual_qa_checklist.md`
Captured PDF: `/home/daekar/Downloads/2019.04.24 Savor MC.PDF`

Update any remaining unchecked items after reviewing the manual session.
This file is the one that `phase2-evidence --qa-checklist-file ...` should consume.

# Phase 2 Manual QA Checklist (Qt-enabled environment)

Date: 2026-03-27  
Owner: FoliaSeal engineering

This checklist is intended for an environment where `PySide6` + `QtPdf` are already available.
It records the manual runtime execution needed to close Phase 2.
Qt dependency readiness belongs in the generated runtime evidence artifact, not in this checklist.
Use this file as the immutable template. The harness now writes a run-specific copy to
`artifacts/phase2_manual_qa_results.md`; that generated results file is what
`phase2-evidence --qa-checklist-file ...` should consume.

## Runtime session setup
- [x] Launch the app with a representative multi-page PDF (portrait + rotated page if available).
- [x] Confirm preview widget loads without dependency errors.

## Viewer interaction checks
- [x] Initial render succeeds on page 1.
- [x] Mouse-wheel zoom-in and zoom-out update preview scale correctly.
- [x] Keyboard zoom shortcuts work (`+`, `-`, `0` reset).
- [x] Page navigation next/previous works and stays within valid bounds.
- [x] Keyboard page navigation works (`PgUp`/`PgDn`, arrows, `Home`/`End`).
- [x] Jump-to-page behavior handles first page, middle page, and last page.
- [x] Drag-selection overlay is visible while dragging.
- [x] Drag-selection callback returns a valid in-bounds PDF rectangle.
- [x] Out-of-bounds selection produces an actionable UI error message.

## Timing baseline evidence (FR-13)
- [x] Record first-render elapsed time in milliseconds.
- [x] Record at least 10 navigation samples in milliseconds.
- [x] Export timing evidence markdown into Phase 2 review notes (recommended command):
  - `python -m foliaseal phase2-evidence --first-render-ms <value> --navigation-ms <value> ... --collect-runtime-footprint --measure-startup-command <pyinstaller_one_dir_executable_or_probe_command> --startup-ready-after-seconds <value> --bundle-dir <pyinstaller_one_dir_output> --qa-checklist-file artifacts/phase2_manual_qa_results.md --qa-issue "<optional issue note>" --check-qt-runtime --write-markdown-file artifacts/phase2_runtime_evidence.md`
  - `--measure-startup-command` measures launch readiness. Use a short-lived probe command when available; for a GUI executable, set `--startup-ready-after-seconds` to the window that should count as a successful launch.
  - The harness seeds `artifacts/phase2_manual_qa_results.md` automatically; review that file and check any remaining manual-only items before running the evidence command.
  - Paste `artifacts/phase2_runtime_evidence.md` into `phase2_review.md` under the latest completion-plan update section.
- [x] Attach hardware + OS context (CPU model, memory, Linux distro/version).

## Exit criteria confirmation
- [x] No unhandled exceptions in widget refresh, zoom, navigation, or selection flow.
- [x] Timing evidence attached to Phase 2 review document.
- [x] Runtime footprint metrics (startup/idle memory/bundle size) attached to Phase 2 review document.
- [x] Mark Phase 2 as complete once runtime + timing requirements are satisfied.
