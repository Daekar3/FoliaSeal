# Isolate Harness Event Processing

## Purpose

Remove the last direct Qt application discovery from `phase3_harness_workspace.py`. A one-method
event-pump port will make live event processing injectable and deterministic in tests, while a Qt
adapter preserves the existing graceful no-application behavior and a headless no-op preserves the
headless path. No refresh, rendering, capture, lifecycle, or external contract behavior changes.

`docs/SPEC.md` and the atomic `phase3_nomenclature_retirement_execplan.md` remain unchanged in scope.

## Architecture selection record

- Candidate: repeated live `QApplication.processEvents()` coordination in
  `phase3_harness_workspace.py`; scan Priority approximately `67.54`, confidence `0.90`.
- Dependency category: local-substitutable Qt runtime; production uses a late-bound Qt adapter and
  tests use a recording/fake or no-op adapter.
- Selected design: common-caller `HarnessEventPumpPort.process_events()` injected through workspace
  dependency records, with `QtHarnessEventPump` and `NoOpHarnessEventPump`; Refactor Shape Score
  approximately `93` at Candidate Priority approximately `70`, confidence approximately `0.93`.
- Rejected: a flexible getter/factory protocol (shape ~84) adds extension surface; the minimal port
  (shape ~90.5) is valid but leaves production binding less explicit. No hybrid is justified.

```python
class HarnessEventPumpPort(Protocol):
    def process_events(self) -> None: ...

class QtHarnessEventPump:
    @classmethod
    def from_widget(cls, widget: Any) -> "QtHarnessEventPump": ...
    def process_events(self) -> None: ...

class NoOpHarnessEventPump:
    def process_events(self) -> None: ...
```

The event pump owns only late QApplication discovery and `processEvents()` delegation. It does not
own viewer refresh, rendering, capture, lifecycle close, or any workspace state. The workspace port
and all DTOs remain unchanged.

## Migration and behavior map

| Behavior | Current path/evidence | Replacement boundary | Status |
|---|---|---|---|
| Live scenario synchronization | `QtPhase3HarnessWorkspaceAdapter.apply_scenario()` refreshes then discovers QApplication and pumps | injected pump after refresh | pending |
| Live preview capture synchronization | `capture_snapshot()` refreshes preview, pumps, then renders | injected pump before render capture | pending |
| Headless scenario/capture path | no Qt event processing today | explicit no-op pump, no Qt import | pending |
| Missing QApplication | `_widget_application()` returns no-op when unavailable | Qt adapter returns without calling missing process method | pending |
| Pump failures | current exceptions propagate | port exceptions propagate unchanged to existing runner cleanup | pending |

Required ordering is immutable: `apply effects → refresh viewer → pump`, and `refresh preview → pump
→ render/capture`. No call frequency changes.

## Baseline and predicted improvement

Baseline commit: `5c89e171d`, clean `main`. `phase3_harness_workspace.py` is 379 lines and still
imports `importlib`, dynamically loads `PySide6.QtWidgets`, probes `QApplication`, and repeats the
same direct process-events sequence in two methods. The headless/live boundary has no fakeable event
processing contract.

Predicted component improvements (0–0.5 proxy scale): navigation friction `0.20`, change amplification
`0.35`, seam-risk reduction `0.40`, boundary-test improvement `0.45`, interface compression `0.30`,
cohesion `0.40`, behavioral-uncertainty reduction `0.20`; predicted Actual Improvement `0.23`.

## Acceptance contract

- `docs/SPEC.md`, workspace port signatures, DTOs, CLI names, JSON keys, artifacts, and phase3 naming
  remain unchanged.
- `phase3_harness_workspace.py` has no `importlib`, `PySide6`, `QApplication`, `_widget_application`,
  or `processEvents` references; those belong only to the event-pump adapter.
- Focused event-pump/workspace tests prove exact call order/count, missing-app no-op, headless no-op,
  and exception propagation. Full tests and acceptance matrices preserve counts and expectations.
- New event-pump protocol/no-op module imports without optional GUI/runtime dependencies.
- Temporary roots, generated artifacts, processes, and dialogs are cleaned; `main` is clean after
  commit. Actual Improvement ≥ `0.15`, with no component regression below `-0.10`.

## Implementation steps

1. Add `phase3_harness_event_pump.py` with protocol, Qt adapter, and headless no-op plus boundary tests.
2. Add optional pump dependencies/defaults, migrate both adapters, remove direct Qt discovery, and add
   recording order tests.
3. Update architecture docs, this plan, and the parent ledger.
4. Run focused/full pytest, Ruff, diff/import isolation, CLI checks, offscreen acceptance, cleanup,
   and process audits; commit on `main`.
5. Start a fresh three-explorer scan.

## Out of scope

Do not merge app-frame or Phase 2 lifecycles, move viewer refresh/render/capture policy, rename phase3
contracts, or redesign the workspace port.

## Completion record

- [x] (2026-08-06) Added `HarnessEventPumpPort`, `QtHarnessEventPump`, and
  `NoOpHarnessEventPump`; both workspace adapters now use injected event processing and the workspace
  module no longer imports or discovers Qt directly.
- [x] (2026-08-06) Added boundary tests for Qt processing, missing-application no-op behavior,
  import isolation, and exact live workspace order/count (`22 passed` focused).
- [x] (2026-08-06) Full validation passed: `1,054 passed, 11 skipped, 1 warning`; Ruff, diff checks,
  application and event-pump import isolation, and CLI help checks passed.
- [x] (2026-08-06) Offscreen acceptance passed signed acceptance (`10` scenarios, `7` successful
  signings, `3` matched intentional rejections), signed preview parity (`18/18` successful), and
  signed fit rejection (`3/3` matched). The explicit `/tmp/foliaseal-event-pump-acceptance` root was
  removed and the FoliaSeal/Python process audit was clean.
- [x] (2026-08-06) Retirement grep is clean: workspace has no `importlib`, `PySide6`, `QApplication`,
  `_widget_application`, or `processEvents` references; only the event-pump adapter owns late Qt
  discovery. Proxy measures are navigation friction `0.20`, change amplification `0.35`, seam-risk
  reduction `0.40`, boundary testability `0.45`, interface compression `0.30`, cohesion `0.40`, and
  behavioral-uncertainty reduction `0.20`; `Actual Improvement = 0.31` versus predicted `0.23`, with
  no component regression below `-0.10`.
- [x] (2026-08-06) Architecture documentation and parent-ledger reconciliation are complete; commit
  closure remains the final step for this child.
