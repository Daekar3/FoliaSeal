# Interactive harness Qt lifecycle boundary

## Purpose

Remove direct `QApplication`/`QMainWindow` lifecycle ownership from the interactive evidence
harness session runner in one bounded slice. The runner currently interleaves window creation,
layout mounting, event-loop execution, close-on-failure cleanup, shell callback wiring, signing, and
capture assembly. A fakeable lifecycle port will own only the standalone harness window/event loop;
the runner will retain evidence/session policy and all stable output contracts.

`docs/SPEC.md` remains unchanged. This slice does not rename `phase3` modules, public commands,
DTOs, JSON fields, fixture paths, or artifact paths; those remain the coordinated atomic migration
of `phase3_nomenclature_retirement_execplan.md`.

## Baseline and candidate evidence

- Baseline commit: `4c8570724`, clean `main`.
- `phase3_harness_session_runner.py` is 291 lines. `run()` directly creates/reuses
  `QApplication`, constructs/configures a `QMainWindow`, builds toolbar/body layouts, mounts the
  central widget, calls `show()`/`app.exec()`, and closes the window from multiple exception paths.
- Existing tests in `tests/unit/test_phase3_harness_session_runner.py` cover normal capture and shell-
  build failure with fake bindings, including title, size, central mount, show, and close behavior.
- Independent scan priority: approximately `67` at confidence `0.88`, above the fixed `60` gate.
- Design review: minimal port `85`, flexible ports/context `84.5`, common-caller port `88`; the
  constrained hybrid below scores `93.5`, beating the strongest base by `5.5` points.

## Stable interface

Add a presentation-local protocol and typed surface in
`src/foliaseal/presentation/qt/phase3_harness_qt_lifecycle.py`:

```python
@dataclass(frozen=True)
class HarnessWindowSpec:
    title: str
    width: int = 1440
    height: int = 980

@dataclass(frozen=True)
class HarnessQtSurface:
    app: Any
    window: Any
    central: Any
    toolbar: Any
    body: Any

class HarnessQtLifecyclePort(Protocol):
    def start(self, *, spec: HarnessWindowSpec) -> HarnessQtSurface: ...
    def mount(self, surface: HarnessQtSurface, widget: Any) -> None: ...
    def show(self, surface: HarnessQtSurface) -> None: ...
    def exec(self, surface: HarnessQtSurface) -> int: ...
    def close(self, surface: HarnessQtSurface) -> None: ...
```

`QtHarnessLifecycle` adapts the existing `_QtHarnessBindings`, reuses an existing application when
available, creates the window/central/toolbar/body layout in the same order and dimensions, mounts
the workspace target, shows and executes the event loop, and makes close idempotent. A small fake
implementation or fake binding fixture is used by boundary tests. The surface exposes only the
opaque layout targets needed by the runner; it does not expose signing workflows, callbacks,
capture state, or a general widget registry.

## Runner migration

Extend `Phase3HarnessSessionRunnerDeps` with the lifecycle factory/port. Replace direct lifecycle
calls in `run()` with:

1. `surface = lifecycle.start(HarnessWindowSpec(title=..., width=1440, height=980))`.
2. Build the existing toolbar controls against `surface.toolbar` and body content against
   `surface.body`.
3. `lifecycle.mount(surface, workspace_bundle.view.mount_target())`.
4. Call `lifecycle.show(surface)` and `lifecycle.exec(surface)`.
5. Put shell construction, viewer refresh, event-loop execution, final capture, and result shaping
   under one outer `try/finally` that calls `lifecycle.close(surface)` exactly once.

Keep `Phase3HarnessSessionResult`, callback ordering, signed-run capture assembly, intentional fit
rejections, summary JSON, artifact basenames, CLI command names, and error behavior unchanged.
Do not merge with `SigningWorkspaceLifecycle`, whose contract owns app-frame workspace replacement;
do not migrate `phase2_harness.py` in this slice.

## Invariants and retirement criteria

- Application creation precedes all QWidget creation.
- Window title and size remain `FoliaSeal Phase 3 Harness - <name>`, 1440x980.
- `close()` runs on shell-build, refresh, event-loop, and final-capture failures and is idempotent.
- `app.exec()` remains called once and its return value remains ignored by the runner.
- No direct `q_application`, `q_main_window`, `setCentralWidget`, `show`, `exec`, or local window
  close calls remain in `phase3_harness_session_runner.py`; the lifecycle adapter owns them.
- The existing `phase3_signed_acceptance_lifecycle.py` remains unchanged unless a narrow protocol
  reuse is proven by tests; no compatibility alias or generic Qt manager is introduced.

## Implementation and validation

1. Add the typed lifecycle module, Qt adapter, fake/boundary tests, and dependency injection.
2. Migrate the session runner while preserving callback/capture behavior and failure cleanup.
3. Add regression tests for normal flow, app reuse, title/size/mount/show ordering, and close on
   shell-build/refresh/final-capture failures.
4. Update `docs/ARCHITECTURE.md`, this child plan, and the parent architecture-loop ledger.
5. Run focused lifecycle/session/harness tests, full pytest, Ruff, diff checks, application import
   isolation, CLI help/parser checks, and offscreen preview/signed acceptance matrices in explicit
   `/tmp` directories. Remove those directories and audit for FoliaSeal/Python processes and open
   Qt windows before commit.

## Acceptance and measurement

The slice is accepted only when `docs/SPEC.md` is byte-for-byte unchanged; all focused/full tests and
lint checks pass; the existing acceptance counts and intentional-rejection semantics remain valid;
the direct-lifecycle retirement grep is zero; no forbidden application imports appear; and the
worktree/process/temp state is clean. Measure navigation friction, change amplification, seam-risk
reduction, testability, interface compression, cohesion, and behavioral uncertainty. Require Actual
Improvement at least `0.15` with no component regression below `-0.10`.

## Out of scope

Do not rename phase3 nomenclature, change evidence schemas, alter signing policy, add acceptance
scenarios, integrate the unused render cache, or redesign the production app-frame lifecycle. Those
remain separate ranked or contract-sensitive work.

## Completion record

Completed 2026-08-06 after implementation, validation, acceptance evidence, cleanup, and commit
closure:

- [x] Added `HarnessQtBindings`, `HarnessWindowSpec`, `HarnessQtSurface`,
  `HarnessQtLifecyclePort`, and `QtHarnessLifecycle`; moved QApplication/QMainWindow creation,
  central/layout mounting, show/exec, and idempotent close out of the session runner.
- [x] Injected the lifecycle factory through `Phase3HarnessSessionRunnerDeps`. The runner retains
  toolbar callbacks, workspace/session orchestration, signing requests, capture assembly, and all
  stable result/artifact behavior. The direct lifecycle retirement grep is zero in the runner.
- [x] Added lifecycle adapter tests for app reuse, title/size/mount/show/exec ordering, and
  idempotent cleanup. Focused lifecycle/session/harness coverage passed 108 tests; the complete
  suite passed 1,051 tests with one pre-existing warning.
- [x] Ruff, `git diff --check`, application import isolation, and CLI help/parser checks passed.
  Offscreen acceptance evidence passed signed acceptance (10 scenarios, 7 successful signings, 3
  matched intentional rejections), signed preview parity (18/18 successful), and signed fit
  rejection (3/3 matched), with zero cryptographic, annotation, or preview-comparison failures and
  `acceptance_expectations_passed=true`. Explicit preview/signed `/tmp` directories were removed;
  no FoliaSeal/Python processes remained.

Measured proxies: navigation friction `0.25`, change amplification `0.50`, seam-risk reduction
`0.50`, boundary-test improvement `0.50`, interface compression `0.50`, cohesion `0.50`, and
behavioral-uncertainty reduction `0.25`; `Actual Improvement = 0.43`, above the `0.15` gate, with
no component regression below `-0.10`. The first non-offscreen Qt attempt is not part of this slice;
all acceptance commands were run with `QT_QPA_PLATFORM=offscreen` in the headless environment.
