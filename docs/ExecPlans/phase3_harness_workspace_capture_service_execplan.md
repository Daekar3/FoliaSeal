# Extract the Shared Harness Workspace Capture Service

## Purpose

Deepen `phase3_harness_workspace.py` by moving the duplicated, Qt-free snapshot assembly used by
the live and headless workspace adapters into one typed capture service. The adapters will retain
workflow reads, scenario mutation, rendering callbacks, Qt event pumping, and sign-time diagnostics;
the new service will own only stable snapshot construction and JSON-ready mapping policy.

This is a single behavior-preserving architecture slice. `docs/SPEC.md`, public Phase 3 CLI verbs,
DTO names, JSON keys, fixture paths, and artifact paths remain unchanged. The separate
`phase3_nomenclature_retirement_execplan.md` remains the atomic plan for removing the historical
label and must not be piecemealed here.

## Baseline and design selection

- Baseline commit: `5e396932a`, clean `main` after the shared Phase 2 lifecycle migration.
- `phase3_harness_workspace.py` is 540 lines and both `HeadlessPhase3HarnessWorkspaceAdapter` and
  `QtPhase3HarnessWorkspaceAdapter` independently construct `Phase3HarnessWorkspaceSnapshot` values,
  map render/reservation results, and preserve optional live-only fields.
- Fresh three-explorer scan priority: approximately `66` at confidence `0.88` for this mixed
  responsibility; the next alternatives scored about `64.87` (composition-root preview helpers) and
  `63` (signing backend).
- Three independent designs were reviewed: a pure snapshot builder (~90), a flexible scenario
  resolver (~90.5), and a common-caller capture service (~90, Priority ~72). The common-caller design
  is selected because both adapters already converge on one snapshot contract and the service can
  remove duplicated policy without widening the workspace port or moving Qt effects.

## Stable interface

Add a presentation-neutral module
`src/foliaseal/presentation/qt/phase3_harness_workspace_capture.py` containing:

```python
@dataclass(frozen=True)
class Phase3HarnessWorkspaceCaptureInput:
    current_request: SigningRequest | None
    last_signing_result: SigningResult | None
    capture_index: int
    capture_kind: str
    capture_label: str | None
    preview_snapshot: dict[str, Any]
    preview_text: str
    validation_text: str
    sign_request_snapshot: dict[str, Any] | None
    backend_reservation_snapshot: dict[str, Any] | None
    backend_reservation_error: str | None

class Phase3HarnessWorkspaceCaptureService:
    def build_snapshot(
        self, data: Phase3HarnessWorkspaceCaptureInput
    ) -> Phase3HarnessWorkspaceSnapshot: ...
```

The service may own `Phase3HarnessWorkspaceSnapshot` and `as_mapping()` with an import-compatible
re-export from `phase3_harness_workspace.py`. It must not import Qt, Pillow, pyHanko, render adapters,
workflows, or filesystem/artifact code. It performs no policy beyond preserving existing field values,
optional labels, and mapping keys.

## Migration and invariants

- Headless and Qt adapters keep their current request resolution, workflow preview/render calls,
  profile/scenario mutation, event pumping, sign-time diagnostics, and text reads.
- Each adapter creates one `Phase3HarnessWorkspaceCaptureInput` and delegates snapshot construction to
  the service. No duplicate `Phase3HarnessWorkspaceSnapshot(...)` construction remains in the adapter.
- `Phase3HarnessWorkspacePort` signatures and every matrix/session caller remain unchanged.
- `Phase3HarnessWorkspaceSnapshot.as_mapping()` keys and omission rules remain byte-for-byte stable,
  including `capture_label`, reservation snapshots/errors, and current-page placement semantics.
- No compatibility alias, generic evidence manager, public CLI rename, or phase3 nomenclature change is
  introduced. The old module path remains the caller-facing workspace boundary until the atomic naming
  migration.

## Implementation and validation

1. Add the pure capture-input/service module and focused mapping/immutability tests.
2. Migrate both workspace adapters and retain an import-compatible snapshot re-export for existing
   tests/callers only where needed.
3. Add parity tests for equivalent live/headless inputs and preserve existing workspace/matrix tests.
4. Update `docs/ARCHITECTURE.md`, this child plan, and the parent architecture-loop ledger.
5. Run focused/full pytest, Ruff, diff/import isolation, CLI checks, offscreen acceptance matrices,
   explicit `/tmp` cleanup, and process/window audits.
6. Commit on `main`, then start a fresh three-explorer scan. Keep the nomenclature retirement plan
   current with any newly discovered internal references; do not rename them in this slice.

## Acceptance and measurement

Acceptance requires frozen SPEC/contracts, no direct Qt or third-party imports in the new service,
all focused/full tests and acceptance counts passing, no duplicate snapshot construction in the
workspace adapters, clean temporary/process state, and Actual Improvement ≥ `0.15` with no component
regression below `-0.10`.

## Completion record

- [x] (2026-08-06) Added the Qt-free `Phase3HarnessWorkspaceCaptureInput`,
  `Phase3HarnessWorkspaceSnapshot`, and `Phase3HarnessWorkspaceCaptureService` boundary; the live
  and headless adapters now delegate snapshot construction while retaining all runtime effects.
- [x] (2026-08-06) Focused workspace, harness, session, scenario, and capture-service validation
  passed `105` tests with one skipped test and one pre-existing Pillow warning.
- [x] (2026-08-06) Full validation passed: `1,047 passed, 11 skipped, 1 warning`; Ruff, diff
  checks, application and capture-service import isolation, and CLI help checks passed.
- [x] (2026-08-06) Offscreen acceptance passed signed acceptance (`10` scenarios, `7` successful
  signings, `3` matched intentional rejections), signed preview parity (`18/18` successful), and
  signed fit rejection (`3/3` matched). The explicit `/tmp/foliaseal-workspace-capture-acceptance`
  root was removed and the FoliaSeal/Python process audit was clean.
- [x] (2026-08-06) Architecture and parent-ledger updates are complete. Proxy measures are
  navigation friction `0.25`, change amplification `0.50`, seam-risk reduction `0.50`, boundary
  testability `0.50`, interface compression `0.50`, cohesion `0.50`, and behavioral-uncertainty
  reduction `0.25`; `Actual Improvement = 0.43` versus predicted `0.25`, with no component
  regression below `-0.10`.
- [x] (2026-08-06) Commit closure is complete on `main`; no phase3 nomenclature or external evidence
  contract was renamed. The next scan must be fresh and independent.
