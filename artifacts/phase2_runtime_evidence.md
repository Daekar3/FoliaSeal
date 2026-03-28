## Phase 2 runtime evidence
### Viewer timing snapshot
- First render: not recorded
- Navigation average: not recorded
- Navigation min/max: not recorded / not recorded
- Navigation samples: 0

### Runtime environment
- OS: Linux (#19~24.04.2-Ubuntu SMP PREEMPT_DYNAMIC Fri Mar  6 23:08:46 UTC 2)
- Machine: x86_64
- Processor: x86_64
- Python: 3.12.3

### Exit criteria quick-check
- ⚠️ First-render timing recorded
- ⚠️ Navigation sample count (0/10)

### Runtime footprint snapshot
- Startup latency: not recorded
- Idle memory: 15.24 MiB
- Bundle size (one-dir): not recorded

### FR-16 runtime metrics quick-check
- ⚠️ Startup latency recorded
- ✅ Idle memory recorded
- ⚠️ PyInstaller one-dir bundle size recorded

### Runtime validation sweep
- ⚠️ Checklist status: 0/20 checks passed
- Open issues:
  - Install runtime dependencies (`PySide6`, `QtPdf` modules available in Python import path).
  - Launch the app with a representative multi-page PDF (portrait + rotated page if available).
  - Confirm preview widget loads without dependency errors.
  - Initial render succeeds on page 1.
  - Mouse-wheel zoom-in and zoom-out update preview scale correctly.
  - Keyboard zoom shortcuts work (`+`, `-`, `0` reset).
  - Page navigation next/previous works and stays within valid bounds.
  - Keyboard page navigation works (`PgUp`/`PgDn`, arrows, `Home`/`End`).
  - Jump-to-page behavior handles first page, middle page, and last page.
  - Drag-selection overlay is visible while dragging.
  - Drag-selection callback returns a valid in-bounds PDF rectangle.
  - Out-of-bounds selection produces an actionable UI error message.
  - Record first-render elapsed time in milliseconds.
  - Record at least 10 navigation samples in milliseconds.
  - Export timing evidence markdown into Phase 2 review notes (recommended command):
  - Attach hardware + OS context (CPU model, memory, Linux distro/version).
  - No unhandled exceptions in widget refresh, zoom, navigation, or selection flow.
  - Timing evidence attached to Phase 2 review document.
  - Runtime footprint metrics (startup/idle memory/bundle size) attached to Phase 2 review document.
  - Mark Phase 2 as complete once runtime + timing requirements are satisfied.

### Qt runtime readiness
- ✅ Ready for Qt host runtime validation
- ✅ PySide6 import available
- ✅ PySide6.QtPdf import available
