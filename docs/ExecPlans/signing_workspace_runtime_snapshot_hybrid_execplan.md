# Deepen the signing workspace with an explicit diagnostic snapshot boundary

This ExecPlan is a living document. Maintain it in accordance with
`.agents/skills/write-execplan/PLANS.md`. Keep `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` current throughout the implementation.

## Purpose / Big Picture

After this slice, the visible signing workflow remains unchanged, but the code has one
authoritative read boundary for the live workspace state used by diagnostics and the Phase 3
harness. The production `SigningWorkspacePort` remains small and continues to serve the app frame.
The broad `compat_surface` remains transitional and continues to install legacy widget exports.

The new behavior is observable through tests and the existing Phase 3 harness: after a workspace
mutation, the harness reads one immutable, Qt-free `SigningWorkspaceSnapshot` containing the current
request, placement, appearance, certificate selection, timestamp flag, page, sign readiness, and
last signing result. It no longer reconstructs those values through a mixture of runtime methods and
callable-or-attribute compatibility checks. A fresh shell still opens, signs, previews, and reports
the same evidence fields as before.

## Child ExecPlan Dependencies

- [x] (2026-07-30) The snapshot contract, runtime producer, compatibility/testing adapter, Phase 3
  consumer, and tests are complete in this parent slice.
- [x] (2026-07-30) Child documentation-compliance plan
  `docs/ExecPlans/signing_workspace_runtime_snapshot_architecture_docs_execplan.md` must reconcile
  `docs/ARCHITECTURE.md` and README wording; the documentation pass and rerun are complete.

## Progress

- [x] (2026-07-30) Reviewed the recommended hybrid and confirmed that the small production port,
  explicit Phase 3 testing adapter, and transitional compatibility surface already exist.
- [x] (2026-07-30) Completed the required fresh explorer reconnaissance. It identified the missing
  immutable snapshot as the smallest complete next seam and confirmed the live consumers and
  compatibility hazards.
- [x] (2026-07-30) Wrote this self-contained one-slice ExecPlan before implementation.
- [x] (2026-07-30) Added the Qt-free immutable snapshot data object and diagnostic protocol.
- [x] (2026-07-30) Added runtime snapshot production from one consistent live workspace state.
- [x] (2026-07-30) Exposed the snapshot through the testing/diagnostic adapter without changing the production
  shell port or removing transitional widget exports.
- [x] (2026-07-30) Migrated the Qt Phase 3 workspace adapter to consume one snapshot per capture and preserve the
  existing scenario/capture JSON contract.
- [x] (2026-07-30) Added snapshot immutability/runtime coverage, adapter parity assertions, and
  Phase 3 fake snapshots; focused shell/harness/app-frame suites pass: 149 tests.
- [x] (2026-07-30) Full repository validation passes: 996 tests with one pre-existing Pillow
  deprecation warning; lint and `git diff --check` pass.
- [x] (2026-07-30) High-risk compliance review passed code, SPEC, snapshot consistency, and Phase 3
  behavior; the first architecture review found only stale documentation wording.
- [x] (2026-07-30) Initial architecture review recorded FAIL for stale Phase 3 compatibility-read
  wording; no code or SPEC defect was found.
- [x] (2026-07-30) Completed the documentation-compliance child plan and reran both architecture/spec
  reviews; both now PASS.
- [x] (2026-07-30) Updated README and `docs/ARCHITECTURE.md` through the architecture-steward pass,
  documenting snapshot ownership, diagnostics/testing ports, the narrow production port, and the
  transitional compatibility surface.
- [x] (2026-07-30) Committed the complete slice and amended the commit with final plan evidence;
  the post-commit worktree, process, and window audit is clean.

## Surprises & Discoveries

- Observation: the recommended hybrid is already partly implemented. The app frame uses the small
  production port, while Phase 3 uses `testing_adapter` and `compat_surface` remains transitional.
  Evidence: `app_frame_workspace_open.py` stores the production port separately, and
  `phase3_harness_workspace.py` requires `shell.testing_adapter`.
- Observation: runtime state is currently fragmented. `SigningWorkspaceRuntime` exposes individual
  accessors such as `current_request()`, `signature_appearance()`, and `is_sign_action_enabled()`,
  while `SigningWorkspaceCompatibilitySurface` obtains `last_signing_result` from a widget export.
  Evidence: `signing_workspace_runtime.py` and `signing_workspace_compatibility_surface.py` read
  the values through separate paths.
- Observation: the Qt harness still accepts both callable and attribute forms for
  `last_signing_result`, which makes the capture boundary harder to reason about.
  Resolution: the real testing adapter will expose one snapshot method; compatibility widget
  exports remain for existing callers, while the harness migrates to the new method.
- Observation: the first architecture compliance review found stale Phase 3 wording in
  `docs/ARCHITECTURE.md`, even though code and SPEC behavior were compliant.
  Resolution: create and execute a documentation-only child plan before commit; it will document
  the snapshot producer/consumer and preserve the transitional compatibility description.

## Decision Log

- Decision: Leave `SigningWorkspacePort` unchanged in this slice.
  Rationale: app-frame callers already depend on a small, coherent production contract. Adding
  diagnostics or harness-only operations to it would make the common caller pay for a broader seam.
  Date/Author: 2026-07-30 / Codex.
- Decision: Define the snapshot as a Qt-free immutable data object in a neutral diagnostics module.
  Rationale: the snapshot is a read model shared by runtime and testing consumers, not a widget or
  compatibility implementation detail. A neutral module keeps imports one-directional and makes
  boundary tests independent of PySide6.
  Date/Author: 2026-07-30 / Codex.
- Decision: Keep the existing `SigningWorkspaceTestingPort` methods as compatibility helpers while
  adding `snapshot()`; migrate the Phase 3 capture path to the snapshot immediately.
  Rationale: existing harness and unit-test callers can transition without a broad breaking change,
  while the principal consumer stops assembling state piecemeal in this slice.
  Date/Author: 2026-07-30 / Codex.
- Decision: Include `last_signing_result` in the snapshot through the compatibility surface's
  existing action-coordinator-backed value rather than duplicating signing state in runtime.
  Rationale: the action coordinator owns the authoritative result state; runtime owns draft, viewer,
  review, and placement state. The snapshot composes both without creating a second state machine.
  Date/Author: 2026-07-30 / Codex.
- Decision: Preserve `Phase3HarnessWorkspaceSnapshot` and its serialized keys.
  Rationale: this slice changes how live state is read, not the evidence contract consumed by the
  release-fidelity matrices and downstream validators.
  Date/Author: 2026-07-30 / Codex.
- Decision: Treat stale architecture wording as a blocking compliance finding and resolve it in a
  child documentation plan before commit.
  Rationale: the DevLoop requires architecture/spec alignment, and the architecture document is a
  governing map for future agents even when runtime behavior is already correct.
  Date/Author: 2026-07-30 / Codex.

## Outcomes & Retrospective

The slice added a Qt-free immutable `SigningWorkspaceSnapshot`, a diagnostics/testing protocol,
runtime snapshot production, compatibility/testing adapter exposure, and Phase 3 consumption of one
snapshot per live capture without widening `SigningWorkspacePort` or changing evidence keys. Focused
shell/harness/app-frame validation passed with 149 tests; the full suite passed with 996 tests and one
pre-existing Pillow deprecation warning. The initial architecture review failed only on stale
documentation wording; the architecture-steward child plan corrected README and `docs/ARCHITECTURE.md`,
and the rerun architecture/spec review passed. The high-risk runtime review passed. The slice was
committed and then amended with this final plan evidence. The post-amend worktree, process, and
window audit is clean; the final commit is the current `HEAD` on `main`.

Documentation-compliance outcome (2026-07-30): The initial architecture review FAIL (stale Phase 3
compatibility-read wording) was resolved by updating `README.md`, `docs/ARCHITECTURE.md`, this plan,
and the child plan. The final architecture/spec reviews PASS. Focused workspace/runtime/harness
tests and `git diff --check` pass. The complete slice is committed on `main`; the post-amend
worktree, process, and window audit is clean.

## Context and Orientation

The signing workspace is a Qt presentation-layer shell assembled by
`src/foliaseal/presentation/qt/signing_workspace_composition.py`. The composition creates the
viewer, document-review sessions, signature-properties panel, sidebar, action coordinator, review
bridge, interaction bridge, orchestrator, runtime, compatibility surface, and small production shell
surface.

`src/foliaseal/presentation/qt/signing_shell_port.py` defines the production-facing
`SigningWorkspacePort` and returns a `SigningWorkspaceBundle` containing both that port and the
explicit `SigningWorkspaceTestingPort`. The app frame uses only the production port for normal
workspace operations. Do not widen it in this slice.

`src/foliaseal/presentation/qt/signing_workspace_runtime.py` owns shell-local orchestration and
currently exposes many individual reads and mutations. It already has access to the draft workflow,
viewer workflow/session, review workspace, properties panel, sign button, and refresh callbacks. It
is the correct producer for a coherent runtime snapshot.

`src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py` owns transitional widget
exports and constructs `SigningWorkspaceTestingAdapter`. It can combine the runtime snapshot with
the action coordinator's existing `widget.last_signing_result` value without exposing the concrete
widget to Phase 3.

`src/foliaseal/presentation/qt/signing_workspace_testing_port.py` is the neutral harness/testing
contract module. It currently defines panel and testing protocols. Add the diagnostic snapshot type
and a `snapshot()` method here or import the type from the neutral diagnostics module; do not make
the contract import the concrete compatibility surface.

`src/foliaseal/presentation/qt/phase3_harness_workspace.py` has separate headless and Qt adapters.
The Qt adapter applies preview scenarios through `SigningWorkspaceTestingPort`, then captures a
`Phase3HarnessWorkspaceSnapshot` containing preview, validation, request, backend, and signing-result
evidence. Migrate only the live-state reads to the new snapshot; keep artifact rendering and backend
diagnostic collaborators unchanged.

Relevant tests are `tests/unit/test_qt_signing_workspace_runtime.py`,
`tests/unit/test_qt_signing_shell.py`, `tests/unit/test_qt_phase3_harness_workspace.py`,
`tests/unit/test_qt_app_frame_workspace_open.py`, and `tests/unit/test_qt_app_frame.py`. Preserve
the existing `test_workspace_interaction_session.py` coverage of ordered interaction-plan creation.

## Plan of Work

First, add `src/foliaseal/presentation/qt/signing_workspace_diagnostics.py` with a frozen,
Qt-free `SigningWorkspaceSnapshot` dataclass. It must contain the stable read model needed by
diagnostics and Phase 3: `logical_page_index`, `signature_rect`, `signature_appearance`,
`selected_certificate_configuration_id`, `timestamp_required`, `current_request`,
`sign_action_enabled`, and `last_signing_result`. Use existing domain/application types; do not add
PySide6, widget, panel, or artifact-rendering fields.

Next, update `signing_workspace_runtime.py` with `snapshot(*, last_signing_result: SigningResult | None = None)`. Build the request using the existing private draft snapshot helper, read the current page and draft values from the already-bound workflow, read sign readiness through the existing sign-button accessor, and return `SigningWorkspaceSnapshot`. The method must fail with the same clear binding errors as the existing accessors when called before composition binding.

Then update `signing_workspace_testing_port.py` to expose the neutral snapshot type and a
`SigningWorkspaceDiagnosticsPort` protocol with `snapshot() -> SigningWorkspaceSnapshot`. Make
`SigningWorkspaceTestingPort` extend or include that method while retaining its existing mutation
and panel methods. In `signing_workspace_compatibility_surface.py`, add a `snapshot()` method on the
compatibility surface that passes the action-coordinator-backed `last_signing_result` into the
runtime snapshot. Add the same method to `SigningWorkspaceTestingAdapter`, delegating to the
compatibility surface. Keep all existing widget exports and legacy testing methods intact.

Migrate `QtPhase3HarnessWorkspaceAdapter.capture_snapshot()` in
`phase3_harness_workspace.py` to obtain one `workspace_state = testing_surface.snapshot()` before
building the evidence row. Use `workspace_state.signature_appearance` for appearance fallback,
`workspace_state.current_request` for request capture, and `workspace_state.last_signing_result` for
the result field. Preserve the existing callable/attribute compatibility only in a small helper for
legacy fake adapters if focused tests demonstrate that it is still needed; the production adapter
must use `snapshot()` directly. Do not alter the headless adapter.

Add focused tests. Test the snapshot dataclass's immutability and complete field mapping. Test a
bound runtime with fake workflow/widgets and assert that one snapshot reflects page, rect,
appearance, certificate, timestamp, request, sign readiness, and supplied last result. Test that the
compatibility/testing adapter returns the same snapshot values as the shell. Update Qt harness
workspace fakes to implement `snapshot()` and assert that capture consumes the snapshot rather than
legacy individual reads. Keep tests proving the production port and widget exports are unchanged.

Run the focused suites, then the full suite. If a Qt ordering or fake-binding issue appears, fix the
adapter/test seam rather than adding a production-port method. After code validation, run the
architecture/spec compliance review, reconcile documentation, rerun affected tests, and commit only
the intentional one-slice changes.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

1. Confirm the starting point is clean and inspect the plan before editing:

       git status --short
       sed -n '1,260p' docs/ExecPlans/signing_workspace_runtime_snapshot_hybrid_execplan.md

2. Add the neutral snapshot type, runtime producer, diagnostics/testing protocol, compatibility
   adapter method, and Phase 3 consumer with `apply_patch`. Keep generated evidence outside Git.

3. Run the focused validation:

       .venv/bin/python -m pytest -q \
         tests/unit/test_signing_workspace_runtime.py \
         tests/unit/test_qt_signing_workspace_runtime.py \
         tests/unit/test_qt_signing_shell.py \
         tests/unit/test_qt_phase3_harness_workspace.py \
         tests/unit/test_qt_app_frame_workspace_open.py \
         tests/unit/test_qt_app_frame.py

   Expected result: all selected tests pass; the exact count will be recorded in `Progress`.

4. Run lint and whitespace checks on every touched source and test file:

       .venv/bin/python -m ruff check \
         src/foliaseal/presentation/qt/signing_workspace_diagnostics.py \
         src/foliaseal/presentation/qt/signing_workspace_testing_port.py \
         src/foliaseal/presentation/qt/signing_workspace_runtime.py \
         src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py \
         src/foliaseal/presentation/qt/phase3_harness_workspace.py \
         tests/unit/test_signing_workspace_runtime.py \
         tests/unit/test_qt_signing_workspace_runtime.py \
         tests/unit/test_qt_signing_shell.py \
         tests/unit/test_qt_phase3_harness_workspace.py \
         tests/unit/test_qt_app_frame_workspace_open.py \
         tests/unit/test_qt_app_frame.py
       git diff --check

5. Run the complete repository suite:

       .venv/bin/python -m pytest -q

   Record the observed total and any pre-existing warnings. No generated matrix artifacts should
   be added to the repository for this behavior-preserving seam change.

6. Perform the required independent compliance review against `docs/ARCHITECTURE.md`,
   `docs/SPEC.md`, and relevant ExecPlans. Because this is a shell/harness seam, use a second
   explorer-light review as a high-risk check. If either review finds a discrepancy, update this
   plan with the finding, fix the code/docs, and rerun focused and full validation before proceeding.

7. Run the documentation pass using the architecture-steward skill. Update `README.md`,
   `docs/ARCHITECTURE.md`, and this plan so they describe the snapshot ownership, production-port
   boundary, transitional compatibility surface, and Phase 3 consumption accurately.

8. Before commit, verify cleanup:

       git diff --check
       git status --short
       ps -eo pid=,comm=,args= | awk '$2 ~ /python/ && $0 ~ /foliaseal|phase3/ {print}'
       wmctrl -l 2>/dev/null || true

   The worktree must contain only intentional changes, with no leftover FoliaSeal or Qt process/window.

## Validation and Acceptance

The slice is accepted when all of these behavioral claims hold:

- The app frame still mounts the same live widget and uses the same small production port methods.
- `SigningWorkspaceBundle` still returns both `port` and `testing_adapter`; no production caller is
  required to reach through `compat_surface`.
- The testing adapter exposes one immutable snapshot whose values are internally consistent with
  the runtime draft and action-coordinator result state.
- The Qt Phase 3 harness captures the same `Phase3HarnessWorkspaceSnapshot` fields and serialized
  evidence as before, while reading live state through one snapshot call.
- Ordered workspace interaction plans still execute in the same order; placement, review, text,
  preview, and signing behavior remain unchanged.
- Focused tests, the full suite, lint, and `git diff --check` pass.
- Architecture/spec compliance review returns PASS after any findings are resolved.
- Documentation names the new diagnostic boundary and transitional ownership accurately.

## Idempotence and Recovery

The changes are additive and safe to retry. The snapshot is read-only and does not write files or
alter persisted settings. If a fake adapter fails because it lacks `snapshot()`, update that fake to
construct the same neutral `SigningWorkspaceSnapshot`; do not reintroduce direct widget reads into
the production Phase 3 adapter. If a shell test fails because a widget export is missing, preserve
the legacy export and add the snapshot beside it. If full-suite failures reveal a caller outside the
focused inventory, retain the old testing methods and add a compatibility bridge rather than widening
`SigningWorkspacePort`.

## Artifacts and Notes

This is a behavior-change/refactor slice. Tracked changes are limited to the neutral snapshot and
diagnostic contract, runtime/compatibility/testing/harness consumers, focused tests, documentation,
and this ExecPlan. Generated PDFs, images, and matrix directories are not part of the slice.

The key evidence artifacts are:

    src/foliaseal/presentation/qt/signing_workspace_diagnostics.py
    src/foliaseal/presentation/qt/signing_workspace_testing_port.py
    tests/unit/test_qt_phase3_harness_workspace.py
    docs/ARCHITECTURE.md

## Interfaces and Dependencies

In `src/foliaseal/presentation/qt/signing_workspace_diagnostics.py`, define:

    @dataclass(frozen=True)
    class SigningWorkspaceSnapshot:
        logical_page_index: int
        signature_rect: SignatureRect | None
        signature_appearance: SignatureAppearance | None
        selected_certificate_configuration_id: str | None
        timestamp_required: bool
        current_request: SigningRequest | None
        sign_action_enabled: bool
        last_signing_result: SigningResult | None

In `src/foliaseal/presentation/qt/signing_workspace_testing_port.py`, define:

    class SigningWorkspaceDiagnosticsPort(Protocol):
        def snapshot(self) -> SigningWorkspaceSnapshot: ...

    class SigningWorkspaceTestingPort(SigningWorkspaceDiagnosticsPort, Protocol):
        @property
        def panel(self) -> SigningWorkspaceTestingPanelPort: ...
        def signature_appearance(self) -> SignatureAppearance | None: ...
        def set_timestamp_required(self, required: bool) -> None: ...
        def apply_signature_rect_placement(self, signature_rect: SignatureRect) -> None: ...
        def refresh_viewer(self) -> None: ...
        def current_request(self) -> SigningRequest | None: ...
        def last_signing_result(self) -> SigningResult | None: ...

In `signing_workspace_runtime.py`, define:

    def snapshot(
        self,
        *,
        last_signing_result: SigningResult | None = None,
    ) -> SigningWorkspaceSnapshot: ...

In `signing_workspace_compatibility_surface.py` and its testing adapter, define:

    def snapshot(self) -> SigningWorkspaceSnapshot: ...

The dependency category is local-substitutable: application state is in-process, while Qt widgets
and signing-action presentation state are accessed through existing fake-friendly adapters. No new
network or external service dependency is introduced. The production shell port remains unchanged.

## Revision Note

2026-07-30 / Codex: Created this one-slice ExecPlan after fresh DevLoop reconnaissance. The plan
narrows the recommended hybrid to the missing immutable runtime/diagnostic snapshot, preserves the
small production port and transitional compatibility surface, and migrates the Phase 3 capture path
without changing evidence schema or user-visible behavior.
