## Phase 2 runtime evidence
### Viewer timing snapshot
- First render: 49.81 ms
- Navigation average: 57.25 ms
- Navigation min/max: 44.12 ms / 65.35 ms
- Navigation samples: 32

### Runtime environment
- OS: Linux (#19~24.04.2-Ubuntu SMP PREEMPT_DYNAMIC Fri Mar  6 23:08:46 UTC 2)
- Machine: x86_64
- Processor: x86_64
- Python: 3.12.3

### Exit criteria quick-check
- ✅ First-render timing recorded
- ✅ Navigation sample count (32/10)

### Runtime footprint snapshot
- Startup latency: 90.76 ms
- Idle memory: 15.73 MiB
- Bundle size (one-dir): 22.61 MiB

### FR-16 runtime metrics quick-check
- ✅ Startup latency recorded
- ✅ Idle memory recorded
- ✅ PyInstaller one-dir bundle size recorded

### Runtime validation sweep
- ⚠️ Checklist status: 8/19 checks passed
- Open issues:
  - Keyboard zoom shortcuts (+, -, 0) plus Home/End jump behavior were not explicitly reconfirmed in the recorded run.
  - Harness capture reported selection_count=0, so drag-selection callback and out-of-bounds selection messaging remain unverified in the saved artifact.

### Qt runtime readiness
- ✅ Ready for Qt host runtime validation
- ✅ PySide6 import available
- ✅ PySide6.QtPdf import available
