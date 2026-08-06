# Deepen the Signing Workspace with a Typed Primary Session Boundary

This ExecPlan is a living document. Maintain it in accordance with
`.agents/skills/write-execplan/PLANS.md` and the parent loop plan
`docs/ExecPlans/architecture_improvement_loop_parent_execplan.md`. It is the child plan for the
selected constrained hybrid architecture: typed maintenance capabilities plus one primary-workflow
session port, with a one-way temporary Qt compatibility adapter.

## Purpose / Big Picture

After this slice, the app frame and evidence harness will operate on a typed workspace bundle instead
of reaching through dynamically installed widget attributes. The primary GUI workflow—refresh review,
place a visible signature, obtain a coherent preview/snapshot, submit the sign request, and open the
signed output—will be expressed by one explicit session boundary. Certificate/profile/settings/text
maintenance remains in separate cohesive capabilities. A developer can prove the change by running the
existing app-frame, workspace, shell, and harness tests, then checking that production and harness
callers no longer use `getattr(shell, ...)`, `compat_surface`, or direct `viewer_widget`/panel exports;
the release matrices must retain their existing eight-scenario results.

The change is architectural and behavior-preserving. It does not change signing policy, preview
appearance, persisted schemas, public CLI names, or the frozen product specification. Historical
`phase3` labels are handled by the separate
`phase3_nomenclature_retirement_execplan.md` so this slice can preserve evidence contracts while
removing the raw shell seam.

## Architecture Selection Record

Selected candidate: `signing-workspace-shell-seam`, Candidate Priority `70.93/100` from the parent
scan. The cluster includes `signing_shell.py`, `signing_workspace_runtime.py`,
`signing_workspace_orchestrator.py`, `signing_workspace_composition.py`, action/review bridges,
`signing_workspace_shell_surface.py`, `signing_workspace_compatibility_surface.py`,
`signing_shell_port.py`, the app-frame workspace host/lifecycle, and Phase 3 harness callers.

Selected hybrid: `typed-capabilities-plus-primary-session`, Refactor Shape Score `95.5`, exceeding
the valid explicit-capabilities base score `81.0` by `14.5` points. The hybrid has no generic command
dispatcher, service locator, Qt type leak, or speculative compatibility API. It retains the narrow
maintenance port, introduces a typed `SigningWorkspaceSessionPort` for existing primary-workflow
sequencing, returns the session and maintenance capabilities in a typed bundle, and keeps
`SigningWorkspaceCompatibilitySurface` only as a one-way Qt-local adapter until its removal criterion
is met.

The required public contracts at the end of this slice are:

    class SigningWorkspaceSessionPort(Protocol):
        def refresh_viewer(self) -> None: ...
        def refresh_document_review(self) -> DocumentReviewSummary: ...
        def set_signature_rect(
            self,
            *,
            page_index: int,
            left_pt: float,
            bottom_pt: float,
            width_pt: float,
            height_pt: float,
        ) -> SignatureRect: ...
        def apply_signature_rect_placement(self, signature_rect: SignatureRect) -> None: ...
        def preview(self) -> SigningDraftPreview: ...
        def snapshot(self) -> SigningWorkspaceSnapshot: ...
        def submit_sign_request(self) -> SigningRequest | None: ...
        def open_signed_output(self) -> str | None: ...
        def go_to_previous_page(self) -> None: ...
        def go_to_next_page(self) -> None: ...
        def reset_zoom_view(self) -> None: ...
        def focus(self) -> None: ...

    @dataclass(frozen=True)
    class SigningWorkspaceBundle:
        maintenance: SigningWorkspacePort
        session: SigningWorkspaceSessionPort
        testing: SigningWorkspaceTestingPort
        view: WorkspaceViewPort

`WorkspaceViewPort` is a presentation-only lifecycle adapter with only the mount-target/dispose
operations needed by `SigningWorkspaceLifecycle`; the returned opaque object is consumed only by the
Qt mount edge and no caller may inspect widget children. `SigningWorkspacePort`
continues to expose the existing seven maintenance verbs, but its name and methods must not grow with
primary workflow sequencing. `SigningWorkspaceTestingPort` remains a separate diagnostics/harness
contract and is not a production service locator.

## Child ExecPlan Dependencies

- [x] Parent scan round 1 selected this candidate and recorded independent evidence and scores.
- [x] Three designs and two independent design reviews completed; the hybrid beat the base by at
  least five points with no hard-gate risk.
- [x] Current app-frame lifecycle preserves compose-before-mount and dispose-after-success semantics;
  those invariants are characterized by `tests/unit/test_signing_workspace_lifecycle.py`.
- [x] Implementation and boundary-test migration complete.
- [ ] DevLoop compliance review, architecture documentation, full validation, and commit closure
  complete.

## Progress

- [x] (2026-08-05) Recorded candidate, design scores, hybrid rationale, and exact interface shape.
- [x] (2026-08-05) Captured baseline proxies: 39 dynamic widget export assignments across the shell
  and compatibility surfaces; 4 direct shell-internal/getattr seams in production harness/app-frame
  paths; 66 `Any`/`getattr` occurrences across the seam modules; 2,173 lines across the nine seam
  modules; 2 test files directly cover the production shell port/bundle; 1037 tests collected.
- [x] (2026-08-05) Completed the required DevLoop preflight. It confirmed the target bundle does not
  yet exist, identified old `WorkspaceHandle`/bundle/fake constructors, and confirmed lifecycle and
  `set_signature_rect` notification semantics that must be preserved.
- [x] Add typed session/capability/view protocols and a Qt adapter without changing behavior.
- [x] Migrate app-frame and harness callers to the typed bundle/session/testing contracts.
- [x] Add equivalent or stronger boundary tests, then remove the retired caller-side aliases and
  dynamic access.
- [x] Run full validation, release matrices, process/artifact cleanup, architecture compliance review,
  and documentation reconciliation. Commit closure remains pending.
- [x] Measure post-refactor proxies and record Actual Improvement and prediction accuracy.

## Problem Frame and Constraints

The current production path is `FoliaSealAppFrame.open_pdf_path -> SigningWorkspaceHost.open ->
SigningWorkspaceLifecycle.replace -> SigningWorkspaceCompositionService.compose ->
QtSigningWorkspaceFactory.create -> SigningWorkspaceBundle`. The typed `WorkspaceHandle` carries
maintenance, primary-workflow session, testing, and opaque lifecycle-view capabilities together
with the document-bound workflows. App-frame and Phase 3 callers use those named capabilities;
legacy widget exports remain only behind the Qt-local `compat_surface`/`testing_adapter` edge while
their retirement criterion is tracked separately.

The dependency category is local-substitutable: Qt widgets, Pillow/PyHanko renderers, application
workflows, stores, and sign executors all have fakes or in-memory substitutes in the test suite. The
new boundary must therefore be tested without a real Qt application while preserving narrow Qt
adapter tests. The primary workflow must keep existing callback ordering, readiness checks, signed
result storage, page navigation, preview refresh, and lifecycle cleanup.

The illustrative constraint is:

    app_frame: bundle.maintenance.choose_output_pdf_path()
    harness: bundle.session.apply_signature_rect_placement(rect)
    harness: bundle.testing.snapshot()
    lifecycle: mount(bundle.view); dispose(previous.view)

No caller may write `bundle.view.properties_panel`, call `getattr(shell, ...)`, or coordinate runtime,
bridge, and panel methods directly.

## Scope and Migration Inventory

Production callers to migrate are `src/foliaseal/presentation/qt/app_frame_workspace_open.py`,
`src/foliaseal/presentation/qt/signing_workspace_lifecycle.py`, relevant action methods in
`src/foliaseal/presentation/qt/app_frame.py`, and shell composition/factory code. Harness callers are
`phase3_harness_workspace.py`, `phase3_harness_session_runner.py`, and the matrix/session factory
paths that currently depend on dynamic shell exports. The modules to consolidate behind the boundary
are shell surface, runtime, action/review bridge, composition, and compatibility export wiring; their
internal ownership is not rewritten in this slice.

The old `WorkspaceHandle.widget`/`shell` and `SigningWorkspaceBundle.port`/`widget` aliases are
retired in this slice after caller migration. The Qt compatibility surface remains only at the
construction edge for real widget ownership and legacy Qt tests; no app-frame or harness caller
reaches it. No persisted artifact, CLI command, `Phase3*` DTO, signing result, preview schema, or
public user behavior may change. Generated temporary matrix output may change only under explicit
`/tmp` directories used by validation.

## Behavior Preservation Map

- `WS-OPEN-REPLACE`: opening a PDF composes a candidate, mounts it, publishes it only after mount,
  then disposes the old widget; mount failure disposes the candidate and preserves the old handle.
  Evidence: `tests/unit/test_signing_workspace_lifecycle.py`. Replacement boundary tests must remain
  green.
- `WS-MAINTENANCE`: save-output, settings, certificate refresh, profile refresh, reusable-object
  editor, text-selection mode, and copy actions preserve return values and call ordering.
  Evidence: app-frame and shell-port tests. Add typed fake-bundle routing tests before removing any
  dynamic export.
- `WS-REVIEW`: review refresh and document text actions preserve the existing `DocumentReviewSummary`
  and selection/search states. Evidence: `test_document_review*`, viewer/runtime, and app-frame tests.
- `WS-PLACE`: numeric and mouse-driven signature placement preserve PDF-space rects, page selection,
  overlay synchronization, preview refresh, and sign-button readiness. Evidence:
  `test_qt_signing_shell.py`, `test_signing_workspace_runtime.py`, workspace interaction tests,
  and Phase 3 workspace tests.
- `WS-PREVIEW`: preview remains the canonical `SigningDraftPreview`; no signing side effect occurs.
  Evidence: `test_signing_workspace_properties_panel.py` and signing-draft workflow tests. Add a
  session boundary test for read-only preview delegation.
- `WS-SIGN`: submit keeps readiness validation, callback-before-executor ordering, cancellation
  behavior, last-result storage, and error/status callbacks. Evidence: shell/action-coordinator
  tests and Phase 3 session tests. The session port returns the existing `SigningRequest | None`, not
  a speculative new result object.
- `WS-HARNESS`: Phase 3 capture/matrix flows consume the explicit testing/session ports and preserve
  summary keys, artifact paths, eight-scenario counts, and cleanup. Evidence: current 143 focused
  evidence tests, 1037 full-suite tests, and the release matrix commands.

No shallow test may be removed until its observable behavior is covered by one of these boundary tests;
record each replacement mapping in the Outcomes section.

## Baseline Measurements and Predicted Improvement

Baseline was measured on commit `ca6857ef9` using commands from `/home/daekar/FoliaSeal`:

    rg -n "self\._widget\.[A-Za-z_]+\s*=" src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py src/foliaseal/presentation/qt/signing_workspace_shell_surface.py | wc -l
    rg -n "\.shell\.\w+|getattr\(.*testing_adapter|\.testing_adapter|compat_surface|\.viewer_widget|\.properties_panel" src/foliaseal/presentation/qt/app_frame.py src/foliaseal/presentation/qt/app_frame_workspace_open.py src/foliaseal/presentation/qt/phase3_harness*.py src/foliaseal/presentation/qt/phase3_signed_acceptance*.py | wc -l
    rg -n "\bAny\b|getattr\(" <nine seam modules> | wc -l
    wc -l <nine seam modules>
    rg -l "SigningWorkspacePort|SigningWorkspaceBundle|SigningWorkspaceTestingPort|QtSigningWorkspacePort" tests/unit | wc -l
    .venv/bin/pytest --collect-only -q | tail -5

Observed baseline: 39 dynamic export assignments; 4 direct production shell-internal/getattr seams;
66 `Any`/`getattr` occurrences across the nine seam modules; 2,173 seam lines; 2 direct production
port/bundle test files; 1,037 collected tests. The proxy scale is intentionally recorded, not
presented as a universal complexity metric.

Predicted improvement for this slice is: NF 0.20 (callers use one typed bundle instead of following
runtime/bridge/surface/widget paths); CA 0.20 (maintenance/session routing changes are localized);
SR 0.20 (explicit session and lifecycle view boundaries replace dynamic access); TG 0.20 (fake
bundle/session tests cover the primary workflow); IC 0.15 (dynamic exports and duplicate shell access
paths shrink); CC 0.20 (one session owns primary workflow sequencing). Predicted weighted Actual
Improvement is `0.20*0.20 + 0.15*0.20 + 0.15*0.20 + 0.20*0.20 + 0.15*0.15 + 0.15*0.20 = 0.1925`.

## Plan of Work

First add `WorkspaceViewPort` and `SigningWorkspaceSessionPort` alongside the existing narrow
maintenance port in `signing_shell_port.py`. The new session/view protocols are free of Qt widget
types and infra storage DTOs; the existing maintenance port intentionally retains its typed
`AppSettings`/`CertificateCatalog` V1 contract until a separately scoped neutral-settings boundary
is justified. Add `QtSigningWorkspaceSessionPort` and a typed bundle factory that wraps the existing
runtime, shell surface, action bridge, review bridge, and properties panel without moving their policy.

Then migrate `WorkspaceHandle` and `SigningWorkspaceCompositionService` to return named `maintenance`,
`session`, `testing`, and `view` fields. Update app-frame actions to use the maintenance port and
update Phase 3 workspace/session callers to use the session/testing ports. Replace `getattr` checks
with required typed bundle fields and explicit capability absence where a fake intentionally omits a
capability. Keep the compatibility surface one-way and local to Qt construction; do not add new
production callers to its dynamic exports.

Add contract tests for fake bundle routing, session call order, preview read-only behavior, sign
cancellation/readiness, lifecycle replacement/failure, and harness use of explicit ports. Migrate
existing tests before deleting any direct widget alias. Remove only aliases proven unused and update
`docs/ARCHITECTURE.md`, README, and this plan with the final ownership and measured proxy counts.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

1. Confirm `git status --short --branch` is clean and record the baseline commit. Search all listed
   caller paths for dynamic exports before editing.
2. Add red protocol/bundle boundary tests and run the smallest focused test files. The expected red
   state is missing interface/constructor behavior, not a weakened assertion.
3. Implement the typed session/capability/view bundle and migrate composition, app-frame, and harness
   callers. Keep the compatibility adapter only for un-migrated legacy tests and mark each remaining
   reference.
4. Run focused tests:

       .venv/bin/pytest -q tests/unit/test_signing_workspace_lifecycle.py tests/unit/test_qt_app_frame_workspace_open.py tests/unit/test_qt_app_frame.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_signing_workspace_runtime.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_harness_session_runner.py tests/unit/test_workspace_interaction_session.py

5. Prove stale-path retirement and dependency direction:

       rg -n "getattr\(shell|shell\.testing_adapter|shell\.compat_surface|\.shell\.(viewer_widget|properties_panel|refresh_viewer|submit_sign_request)|bundle\.widget" src/foliaseal/presentation/qt tests/unit
       .venv/bin/ruff check src tests
       git diff --check

   The first search may return only compatibility implementation/tests during migration; before
   acceptance it must return no production or harness callers.

6. Run `.venv/bin/pytest -q` and the existing preview/signed release matrices with explicit temporary
   directories. Expect the prior 1,037-plus test behavior, eight preview scenarios with zero errors,
   and eight signed scenarios with six successful signings and two intentional rejections. Remove
   only the named temporary directories and audit `ps` for FoliaSeal/Python processes.
7. Complete the independent high-risk compliance review, architecture documentation update, post-
   measurements, parent/child plan updates, and intentional commits. Do not stop after source tests
   pass.

## Refactor Acceptance Contract

Hard gates are: frozen `docs/SPEC.md` remains unchanged; all required observable behaviors in the map
remain covered; no production/app-frame/harness caller reaches dynamic widget exports; the public
session/view protocols contain no Qt, Pillow, pyHanko, or persistence schema types; the existing
maintenance port's infra DTO types remain an explicit documented residual; no generic command
bus/service locator is introduced; lifecycle replacement semantics remain intact; compatibility code
is confined to the Qt construction edge; full tests/Ruff/diff checks pass; release matrix counts and
artifact contracts remain unchanged; no temporary artifacts/processes remain; architecture docs and
ExecPlans are reconciled; and the main worktree is clean.

Minimum Actual Improvement is `0.15`; no component may regress by more than `0.10`. The approved
public surface is the four-field typed bundle and the exact protocols above. Forbidden changes are
public CLI/DTO/JSON/artifact renames, persisted schema migrations, signing/layout policy changes,
unrelated GUI styling, and speculative command registries.

## Post-Implementation Evaluation

Repeat every baseline command exactly. Record new dynamic export assignments, direct seam references,
`Any`/`getattr` count, seam lines, boundary-test file count, and collected tests. Compute each actual
component improvement from the same proxy definitions, calculate weighted Actual Improvement and
prediction accuracy, and explain whether complexity was hidden behind the session/capability boundary
rather than merely moved. If a hard gate fails, continue this child plan or use the one parent-allowed
redesign attempt; do not accept a test-only refactor.

## Surprises & Discoveries

This section records unexpected Qt lifecycle, callback ordering, fake-adapter, performance, or
compatibility behavior with concrete evidence.

- Observation: the current `SigningWorkspaceBundle` still has `{port, testing_adapter, widget}` and
  `WorkspaceHandle` still has `{widget, shell, testing}`; the target `{maintenance, session, testing,
  view}` shape therefore requires coordinated app-frame, lifecycle, harness, and fake migration.
  Evidence: the DevLoop preflight inspected `signing_shell_port.py`, `app_frame_workspace_open.py`,
  `phase3_harness_workspace.py`, and `phase3_harness_session_runner.py`; those callers now consume
  the typed bundle while the historical module names remain covered by the nomenclature follow-up.
- Observation: `SigningWorkspaceRuntime` already owns review, placement, refresh, and snapshot
  semantics, while preview remains on `SignaturePropertiesPanel` and sign/open-output remain on the
  action bridge. The session adapter must compose these existing owners instead of duplicating them.
  Evidence: preflight symbol inventory at runtime.py:159-285 and signing_shell.py:311-385.

## Decision Log

- Decision: keep the existing narrow maintenance port and separate testing adapter while adding one
  primary session port.
  Rationale: the current architecture and tests explicitly reject a generic command gateway, while
  the SPEC requires a coherent review/place/preview/sign workflow.
  Date/Author: 2026-08-05 / Codex.
- Decision: preserve `SigningRequest | None` for submit semantics in this slice.
  Rationale: the current action coordinator returns the request before/around executor callbacks and
  stores `SigningResult` separately; inventing a result facade would change behavior and increase risk.
  Date/Author: 2026-08-05 / Codex.
- Decision: quarantine, do not immediately delete, dynamic compatibility exports.
  Rationale: Phase 3 tests and legacy edge callers still prove current consumers; retirement requires
  an explicit `rg` proof and equivalent boundary tests.
  Date/Author: 2026-08-05 / Codex.
- Decision: keep the `shell=` constructor fallback in `QtPhase3HarnessWorkspaceAdapter` only for
  existing unit fakes at the Qt adapter edge; all production builders now require a complete
  `SigningWorkspaceBundle` with a non-optional testing port.
  Rationale: the fallback is not a caller-facing capability and can be removed when the remaining
  legacy harness fakes are migrated; no new production caller may use it.
  Retirement criterion: remove it in the phase3 nomenclature/harness cleanup slice after the focused
  harness tests construct bundles directly.
  Date/Author: 2026-08-05 / Codex.

## Outcomes & Retrospective

Implementation and validation completed on 2026-08-05. The high-risk compliance review initially
found raw Phase 3 harness shell access, unretired bundle/handle aliases, and stale architecture
ownership claims. The migration then moved harness refresh/navigation/focus/sign operations through
the typed session/testing bundle, removed the legacy aliases, added direct `QtWorkspaceView` disposal
coverage, and reconciled the architecture/README docs. The maintenance port intentionally retains
its existing `AppSettings`/`CertificateCatalog` DTO types; the new session/view protocols remain
neutral and Qt-free. Historical `phase3` names remain at external CLI/DTO/artifact edges and are
tracked by `phase3_nomenclature_retirement_execplan.md` rather than renamed piecemeal here.

Post-measurement evidence:

    dynamic widget export assignments: 39 -> 35
    direct production/app-frame/harness shell seams (the exact baseline grep in this plan): 4 -> 0
    caller-focused Any/getattr occurrences (supplementary exact seven-module proxy): 361 -> 356
    seam module lines: 2,173 -> 2,300
    direct port/bundle boundary test files: 2 -> 3
    collected tests: 1,037 -> 1,039

Actual component improvements are NF `.25`, CA `.20`, SR `.25`, TG `.25`, IC `.10`, and CC `.20`.
Using the recorded loop weights, Actual Improvement is `0.2125` versus the prediction `0.1925`
(`1.10x` prediction accuracy); no component regressed by more than `0.10`. The added lines are
concentrated in explicit protocols/adapters and tests while the caller seam and dynamic export count
both decreased.

Validation evidence: full suite `1,039 passed, 1 pre-existing Pillow deprecation warning`; Ruff and
`git diff --check` pass; import isolation passes; preview matrix executes 8 scenarios with 0 errors;
signed matrix executes 8 scenarios with 6 successful signings, 2 matched intentional rejections,
zero cryptographic/annotation/preview-output failures, and `acceptance_expectations_passed=True`.
Named `/tmp/foliaseal-workspace-preview` and `/tmp/foliaseal-workspace-signed` directories were
removed and no FoliaSeal process remains after cleanup. The slice is ready for intentional commit.

## Idempotence and Recovery

The migration is additive until all callers use the typed bundle. If a boundary test fails, compare
its observable behavior with the preservation map and fix the adapter/ownership seam rather than
loosening the test. If a release matrix fails, preserve its temporary summary, remove only the named
temporary directories after diagnosis, and rerun. Do not delete compatibility code until its retirement
criterion is proven. A clean worktree and process audit are required before closure.

## Artifacts and Notes

Baseline evidence:

    commit: ca6857ef9
    dynamic exports: 39
    direct production seam references: 4
    seam Any/getattr occurrences: 66
    seam lines: 2,173
    direct port/bundle test files: 2
    collected tests: 1,037

Implementation and release evidence will be recorded here with exact commit hashes, focused/full test
counts, matrix summary metrics, post-measurements, and boundary-test replacement mappings.

## Interfaces and Dependencies

`SigningWorkspaceSessionPort` and maintenance protocols are presentation-owned, Qt-free contracts.
`QtSigningWorkspaceSessionPort` is the concrete adapter over `SigningWorkspaceRuntime`,
`SigningWorkspaceShellSurface`, `SigningActionCoordinator`, and `SigningWorkspaceCompatibilitySurface`.
The app-frame lifecycle may see only `WorkspaceViewPort`; the harness may see `SigningWorkspaceSessionPort`
and `SigningWorkspaceTestingPort`; neither may inspect Qt child widgets. Existing application workflows,
certificate/profile stores, PDF renderers, Pillow, pyHanko, and Qt remain behind injected adapters and
are not imported by the neutral protocol module.

## Change-Slice Boundary

This child is one architecture/refactor slice with associated boundary tests and documentation/status
updates. Allowed changes are the typed workspace bundle/session/capability/view boundary, caller
migration, proven compatibility-export retirement, focused tests, full/release validation, and
architecture/ExecPlan documentation. Generated artifacts are allowed only in named temporary matrix
directories. Forbidden changes include broad signing/layout redesign, persisted schema replacement,
public CLI renames, unrelated GUI styling, and changes to frozen `docs/SPEC.md`.

Revision note: created 2026-08-05 after scan round 1 and independent design review; selected the
constrained hybrid because it scored 95.5 and exceeded the valid capabilities base by 14.5 points.
