# Phase 2 Viewer Harness Shared Lifecycle

## Purpose

Move standalone Qt application/window lifecycle ownership out of the Phase 2 viewer harness and
onto the tested `HarnessQtLifecyclePort` introduced for the interactive evidence harness. This is a
single bounded ownership slice: Phase 2 keeps its viewer, controls, capture, checklist, and evidence
command orchestration, while one shared adapter owns QApplication reuse, QMainWindow setup, mounting,
event-loop execution, and idempotent close.

`docs/SPEC.md` remains unchanged. This plan does not rename the public `phase2` or `phase3` contracts,
CLI verbs, JSON keys, checklist paths, or artifact names. The coordinated `phase3` nomenclature
retirement plan remains a separate contract-sensitive migration.

## Baseline and candidate evidence

- Baseline commit: `c246d9b02`, clean `main` before this child slice.
- `src/foliaseal/presentation/qt/phase2_harness.py` is 447 lines and owns a second copy of
  QApplication/QMainWindow creation, title/size setup, central/toolbar/body layout, mount/show/exec,
  and close behavior. Its report-writing path is not protected by one lifecycle `finally` boundary.
- Fresh independent scan priority: approximately `69.34` at confidence `0.90`, above the fixed `60`
  gate. The strongest alternatives were compatibility-surface retirement (~66) and signing-backend
  boundary work (~63.3).
- Design review selected the common-caller migration to the existing lifecycle port (shape ~92),
  over a broader dependency-injected runner extraction (~84.5) and a minimal direct migration (~90.5).

## Stable interface and migration shape

Reuse these existing types unchanged from
`src/foliaseal/presentation/qt/phase3_harness_qt_lifecycle.py`:

```python
HarnessQtBindings
HarnessWindowSpec
HarnessQtSurface
HarnessQtLifecyclePort
QtHarnessLifecycle
```

`run_phase2_viewer_harness()` gains one optional `lifecycle_factory` injection point for fakeable
boundary tests. The real default remains `QtHarnessLifecycle`. The Phase 2 binding loader constructs
the shared `HarnessQtBindings`; no second binding dataclass or lifecycle protocol remains in
`phase2_harness.py`.

The runner starts the lifecycle with title `FoliaSeal Phase 2 Harness - <source name>` and dimensions
1280x900. It creates one Phase 2 content QWidget/VBox containing viewer, metrics, instructions, and
status in their existing vertical order, mounts that content through the lifecycle, and adds the
existing controls to `surface.toolbar`. `show()`, `exec()`, and exactly-once `close()` are delegated to
the lifecycle; all workflow, callback, capture, checklist, evidence-command, and print behavior stays
in the Phase 2 module.

## Behavior invariants and retirement criteria

- `docs/SPEC.md` remains byte-for-byte unchanged.
- Window title, dimensions, control labels, content ordering, initial refresh, and ignored event-loop
  return value remain unchanged.
- Capture JSON, checklist markdown, evidence command construction, default paths, and CLI dispatch
  remain unchanged.
- Lifecycle close runs on binding/widget/viewer/control setup failure, refresh/event-loop failure,
  report/artifact failure, and normal completion, and is idempotent.
- No direct `QApplication`/`QMainWindow` construction, `setCentralWidget`, window `show`/`exec`, or
  local window close calls remain in `phase2_harness.py`; those calls belong only to the shared adapter.
- The Phase 3 lifecycle adapter and app-frame `SigningWorkspaceLifecycle` contracts are not widened or
  merged. No compatibility alias, generic Qt manager, or speculative runner abstraction is added.

## Implementation steps

1. Replace the local Phase 2 binding dataclass with the shared `HarnessQtBindings` alias and add the
   lifecycle factory injection while preserving the public wrapper signature and defaults.
2. Build the content widget/VBox, mount it through `HarnessQtLifecyclePort`, route controls to the
   shared toolbar, and wrap setup/event-loop/report work in one cleanup-safe lifecycle boundary.
3. Add fake-lifecycle tests for successful capture, exact title/size/order, viewer setup failure,
   and report/artifact failure cleanup. Keep existing pure Phase 2 tests passing.
4. Update `docs/ARCHITECTURE.md`, this completion record, and the parent architecture-loop ledger.
5. Run focused and full tests, Ruff, diff checks, application import isolation, CLI help/parser checks,
   offscreen acceptance matrices, explicit temporary-directory cleanup, and process/window audits.
6. Commit the complete slice on `main` and start a fresh three-explorer architecture scan.

## Validation and acceptance

Required evidence:

- Focused Phase 2/lifecycle/session tests and the complete pytest suite pass.
- `.venv/bin/ruff check src tests scripts` and `git diff --check` pass.
- Importing `foliaseal.application` does not load PySide6, Pillow, or pyHanko.
- Canonical CLI help and parser checks pass.
- Offscreen signed acceptance, preview parity, and fit-rejection matrices preserve their existing
  counts and expectations; explicit `/tmp` matrix directories are removed afterward.
- Direct-lifecycle retirement grep is empty for Phase 2; no FoliaSeal/Python harness process or open
  dialog remains after validation.
- `git status --short --branch` is clean after the intentional commit.
- Measured Actual Improvement is at least `0.15`, with no component regression below `-0.10`.

## Out of scope

Do not rename phase nomenclature, change evidence schemas, alter signing/layout policy, redesign the
production app-frame lifecycle, integrate the render cache, or extract a full Phase 2 runner request/
dependency bundle. Those are separate ranked slices.

## Completion record

- [x] (2026-08-06) Implemented the migration: `phase2_harness.py` now consumes the shared
  `HarnessQtLifecyclePort` with the existing 1280x900 title/size and content ordering, and all
  setup, event-loop, report, and artifact paths close the lifecycle exactly once.
- [x] (2026-08-06) Focused Phase 2/shared-lifecycle validation passed: `14 passed` across the
  lifecycle-migration, Phase 2 harness, shared lifecycle, and interactive session-runner tests.
- [x] (2026-08-06) Full validation passed: `1,054 passed, 1 warning`; Ruff, `git diff --check`,
  application import isolation, and CLI help/parser checks passed.
- [x] (2026-08-06) Offscreen acceptance passed signed acceptance (`10` scenarios, `7` successful
  signings, `3` matched intentional rejections), signed preview parity (`18/18` successful), and
  signed fit rejection (`3/3` matched). The canonical and explicit `/tmp` runs produced no crypto,
  annotation, preview-comparison, or expectation failures.
- [x] (2026-08-06) Direct lifecycle retirement is complete: Phase 2 no longer constructs or controls
  QApplication/QMainWindow; only the shared adapter owns those operations. The explicit acceptance
  root and generated repository artifacts were removed, and the FoliaSeal/Python process audit was
  clean.
- [x] (2026-08-06) Architecture documentation and the parent ledger were reconciled. Proxy measures
  are navigation friction `0.25`, change amplification `0.50`, seam-risk reduction `0.50`, boundary
  testability `0.50`, interface compression `0.50`, cohesion `0.50`, and behavioral-uncertainty
  reduction `0.25`; `Actual Improvement = 0.43` versus predicted `0.25`, with no component regression
  below `-0.10`.
- [x] (2026-08-06) Commit closure is complete on `main`; the next scan must use three fresh independent
  explorers and retain the coordinated `phase3` nomenclature retirement as the leading contract-sensitive
  candidate unless a stronger qualifying seam is found.
