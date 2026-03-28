# Phase 2 Manual QA Checklist (Qt-enabled environment)

Date: 2026-03-27  
Owner: FoliaSeal engineering

This checklist is intended for an environment where `PySide6` + `QtPdf` are already available.
It records the manual runtime execution needed to close Phase 2.
Qt dependency readiness belongs in the generated runtime evidence artifact, not in this checklist.

## Runtime session setup
- [ ] Launch the app with a representative multi-page PDF (portrait + rotated page if available).
- [ ] Confirm preview widget loads without dependency errors.

## Viewer interaction checks
- [ ] Initial render succeeds on page 1.
- [ ] Mouse-wheel zoom-in and zoom-out update preview scale correctly.
- [ ] Keyboard zoom shortcuts work (`+`, `-`, `0` reset).
- [ ] Page navigation next/previous works and stays within valid bounds.
- [ ] Keyboard page navigation works (`PgUp`/`PgDn`, arrows, `Home`/`End`).
- [ ] Jump-to-page behavior handles first page, middle page, and last page.
- [ ] Drag-selection overlay is visible while dragging.
- [ ] Drag-selection callback returns a valid in-bounds PDF rectangle.
- [ ] Out-of-bounds selection produces an actionable UI error message.

## Timing baseline evidence (FR-13)
- [ ] Record first-render elapsed time in milliseconds.
- [ ] Record at least 10 navigation samples in milliseconds.
- [ ] Export timing evidence markdown into Phase 2 review notes (recommended command):
  - `python -m foliaseal phase2-evidence --first-render-ms <value> --navigation-ms <value> ... --collect-runtime-footprint --measure-startup-command <pyinstaller_one_dir_executable_or_probe_command> --startup-ready-after-seconds <value> --bundle-dir <pyinstaller_one_dir_output> --qa-checklist-file phase2_manual_qa_checklist.md --qa-issue "<optional issue note>" --check-qt-runtime --write-markdown-file artifacts/phase2_runtime_evidence.md`
  - `--measure-startup-command` measures launch readiness. Use a short-lived probe command when available; for a GUI executable, set `--startup-ready-after-seconds` to the window that should count as a successful launch.
  - Paste `artifacts/phase2_runtime_evidence.md` into `phase2_review.md` under the latest completion-plan update section.
- [ ] Attach hardware + OS context (CPU model, memory, Linux distro/version).

## Exit criteria confirmation
- [ ] No unhandled exceptions in widget refresh, zoom, navigation, or selection flow.
- [ ] Timing evidence attached to Phase 2 review document.
- [ ] Runtime footprint metrics (startup/idle memory/bundle size) attached to Phase 2 review document.
- [ ] Mark Phase 2 as complete once runtime + timing requirements are satisfied.
