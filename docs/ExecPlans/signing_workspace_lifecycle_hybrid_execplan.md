# Deepen the app-frame signing-workspace lifecycle boundary

This ExecPlan is a living document and must be maintained in accordance with
`.agents/skills/write-execplan/PLANS.md`. It is intentionally a complete
one-slice DevLoop: interface migration, legacy compatibility removal, focused
tests, architecture/spec review, documentation reconciliation, nomenclature
audit, and commit closure all belong to this plan. Milestones organize the
work; they are not stopping points.

## Purpose / Big Picture

Opening a PDF currently crosses an app-frame service, a composition service, a
Qt shell factory, a lifecycle coordinator, a compatibility payload, and a
second set of frame-owned state fields. The application frame receives a
workspace outcome, extracts `compatibility.shell_widget`, stores the shell port
and compatibility snapshot separately, and later has to keep both synchronized.
This makes replacement failures, widget disposal, and stale shell state harder
to reason about than the user-visible operation warrants.

After this slice, the frame will depend on one typed `SigningWorkspaceHost`.
`open(path)` will compose, mount, publish, and return one `WorkspaceHandle`;
`close()` will be idempotent; and `active()` will be the sole source of the
current workspace. The host will preserve the existing atomic behavior: a new
workspace is mounted before the old one is disposed, and a failed candidate is
disposed while the old workspace remains active. The old
`WorkspaceCompatibilityState`, duplicated frame state, and compatibility-only
widget extraction will be removed or quarantined behind a migration adapter.

The slice also audits and strips obsolete `phase3` nomenclature in the touched
lifecycle cluster. The cluster currently has no behavior-bearing `phase3`
names. Stable Phase 3 CLI commands, manifest keys, JSON fields, artifact paths,
acceptance DTOs, and historical records remain unchanged because renaming
those serialized/external contracts without a migration would break existing
automation. The plan records that boundary and creates a concrete inventory
for a later external-contract migration rather than silently preserving
ambiguous internal aliases.

## Child ExecPlan Dependencies

- [x] Fresh DevLoop explorer reviewed the live lifecycle, app-frame, shell,
  tests, architecture, and nomenclature contracts on 2026-08-03.
- [x] Minimal, flexible, and common-caller interface designs were reviewed;
  the recommended hybrid is selected for implementation.
- [ ] If compliance review identifies a requirement that cannot be fixed in
  this lifecycle slice, create a child compliance ExecPlan before unrelated
  edits. No child is required at authoring time.

## Progress

- [x] (2026-08-03) Confirmed clean checkout at `e753c9807` and identified the
  app-frame/shell lifecycle as the next architectural seam.
- [x] (2026-08-03) Completed the required fresh `explorer-light` DevLoop
  review and acknowledged its findings before authoring this plan.
- [x] (2026-08-03) Selected the common-caller/minimal hybrid: a host with
  `open`, `close`, and `active`, returning a typed workspace handle.
- [x] (2026-08-03) Created this living ExecPlan before implementation.
- [x] (2026-08-03) Added the typed `WorkspaceHandle`/`SigningWorkspaceHost`
  boundary and migrated app-frame state and
  workspace-open composition to it.
- [x] (2026-08-03) Removed obsolete lifecycle compatibility outcome/state,
  duplicate widget extraction, and the production `SigningWorkspacePort.widget()`
  contract while retaining the explicit testing boundary.
  dead shell presentation helpers, and any now-unused forwarding aliases.
- [x] (2026-08-03) Added boundary tests for atomic replacement, failure cleanup,
  active-state
  publication, app-frame behavior, and compatibility removal.
- [x] (2026-08-03) Completed two independent architecture/spec compliance
  reviews, reconciled documentation, and inventoried the touched-scope
  `phase3` inventory.
- [x] (2026-08-03) Ran full validation, clean-process/artifact audit, and
  implementation commit closure.

## Surprises & Discoveries

- Observation: `SigningWorkspaceLifecycle` already enforces mount-before-dispose
  ordering and disposes failed candidates.
  Evidence: `src/foliaseal/presentation/qt/signing_workspace_lifecycle.py:67-106`
  and `tests/unit/test_signing_workspace_lifecycle.py:73-180`.
- Observation: the lifecycle still extracts `outcome.compatibility.shell_widget`
  solely to mount a duplicate compatibility field.
  Evidence: `app_frame_workspace_open.py:150-158` and
  `signing_workspace_lifecycle.py:67-83`.
- Observation: `FoliaSealAppFrame` stores `_current_shell_port` and
  `_current_workspace` separately even though lifecycle owns the active state.
  Evidence: `app_frame.py:286-300, 380-415`.
- Observation: `signing_shell.py` has no `phase3` names and is already mostly
  an outer adapter, but it still contains dead `_format_appearance_summary`
  and duplicate `SIGNATURE_PRESET_PLACEHOLDER` exports.
  Evidence: fresh explorer search found no source callers; the canonical
  placeholder is in `signing_workspace_properties_panel.py`.
- Observation: `compat_surface` and `testing_adapter` remain active contracts
  for harness/testing consumers.
  Evidence: `signing_workspace_compatibility_surface.py:75-126`,
  `tests/unit/test_qt_phase3_harness_workspace.py`, and the existing shell
  port ExecPlans. They must be migrated or quarantined before deletion.
- Observation: external Phase 3 names are serialized or invoked by automation.
  Evidence: `README.md`, `docs/ARCHITECTURE.md`, CLI parser tests, manifest
  fixtures, JSON schemas, and artifact paths. This slice must not rename them.

## Decision Log

- Decision: Use a typed `WorkspaceHandle` plus `SigningWorkspaceHost.open`,
  `close`, and `active` rather than a generalized workspace registry/event bus.
  Rationale: it makes the dominant app-frame caller deep and testable while
  avoiding speculative abstractions for future workspace kinds.
  Date/Author: 2026-08-03 / Codex.
- Decision: Keep the established mount-before-dispose ordering and frame-level
  error mapping unchanged.
  Rationale: these are tested user-visible safety guarantees; the refactor
  should change ownership, not failure semantics.
  Date/Author: 2026-08-03 / Codex.
- Decision: Remove `WorkspaceCompatibilityState` and duplicate frame state;
  expose workflows only through the typed handle during migration where
  current frame properties still require them.
  Rationale: explicit handle fields are product state, while a compatibility
  snapshot is an accidental transport bundle.
  Date/Author: 2026-08-03 / Codex.
- Decision: Move only proven-dead shell presentation helpers in this slice;
  leave close-aware cleanup, Qt binding loading, and factory construction in
  their current owner until the new host contract migrates their callers.
  Rationale: removing active shell seams speculatively would broaden risk and
  could break harness/testing consumers.
  Date/Author: 2026-08-03 / Codex.
- Decision: Strip obsolete `phase3` labels in the touched lifecycle scope and
  document a separate migration boundary for stable external names.
  Rationale: CLI/manifest/JSON/artifact compatibility is a user-data and
  automation contract, not disposable internal terminology.
  Date/Author: 2026-08-03 / Codex.

## Outcomes & Retrospective

Implementation is complete for the lifecycle slice. The frame now uses
`SigningWorkspaceHost.open(path)`, `.active()`, and `.close()` with one typed
`WorkspaceHandle` containing the widget, production shell port, testing port,
and workflows. `OpenWorkspaceOutcome`, `WorkspaceCompatibilityState`,
duplicate `_current_workspace`/shell-port state, and `SigningWorkspacePort.widget()`
were removed from the production lifecycle path. The intentional
`compat_surface`/`testing_adapter` boundary remains for Phase 3 and testing
callers. The focused lifecycle/app-frame/shell set passes 140 tests. Two
independent compliance reviews passed after architecture and documentation
reconciliation. The Phase 3 inventory covered the touched lifecycle modules,
tests, README, and architecture document: no obsolete internal lifecycle
names remain; stable CLI commands, manifest keys, JSON fields, DTO names, and
artifact paths remain unchanged. The implementation commit is
`2e9caa2458ee124d19b070b7e5bac8424007c889`.

## Context and Orientation

`src/foliaseal/presentation/qt/app_frame.py` owns the top-level window and
menus. It constructs `SigningWorkspaceHost` and updates action state after
opening or closing a PDF; active workspace state comes only from the host
handle.

`app_frame_workspace_open.py` loads the PDF page count, composes
`ViewerWorkflow` and `SigningDraftWorkflow`, calls `SigningWorkspaceFactory`,
and returns a typed `WorkspaceHandle` containing the mount widget, production
port, testing adapter, and both workflows.

`signing_workspace_lifecycle.py` is the atomic coordinator used by the host. It
asks a workspace-open port to build a candidate, mounts the candidate, disposes
the previous widget only after successful mounting, and disposes failed
candidates. The host publishes one explicit handle.

`signing_shell_port.py` defines the production shell port, testing port, and
Qt factory. `signing_shell.py` builds the Qt widget and installs the already
extracted composition/runtime/surface collaborators. The shell remains a Qt
implementation module, but dead presentation helpers and compatibility-only
exports may move to their canonical module or disappear.

## Plan of Work

Implemented: `WorkspaceHandle` and `SigningWorkspaceHost` now define the
lifecycle/open boundary, using the existing `SigningWorkspacePort`,
`SigningWorkspaceTestingPort`, viewer workflow, signing workflow, source path,
and mount target as explicit fields. `OpenWorkspaceOutcome` and
`WorkspaceCompatibilityState` are no longer frame-facing contracts; if a temporary
adapter is needed for a remaining harness caller, name it explicitly as a
legacy adapter and keep it out of the production host API.

`SigningWorkspaceCompositionService` now returns a handle directly from
the factory bundle. The mount target comes from the bundle/handle; no production
caller invokes `shell_port.widget()`.
Keep `WorkspaceCompositionRequest` and the broad command internally injected
behind the host so `FoliaSealAppFrame.open_pdf_path()` only supplies a PDF path
to the host. The host may construct the existing command/environment internally
until all collaborators are migrated.

`SigningWorkspaceHost.open(path)` now always
performs atomic replacement, publishes the new handle only after mount succeeds,
and disposes the previous handle after publication. `close()` clears the active
handle and disposes it exactly once. Preserve the current frame behavior of
catching open errors, emitting `Unable to open PDF: ...`, and leaving the prior
workspace intact.

`FoliaSealAppFrame` now uses one `_workspace_host`/active-handle source. It removed
`_current_shell_port`, `_current_workspace`, compatibility-derived state
properties, and duplicate shell-widget extraction. Update save-as, text
selection, certificate refresh, reusable-object refresh, and settings actions to
read the active handle's explicit shell port. Keep public `current_shell`,
`current_viewer_workflow`, and `current_signing_workflow` only as narrow typed
read-only projections if existing callers still require them; they must derive
from the active handle rather than storing parallel state.

Remove dead `_format_appearance_summary` and duplicate placeholder exports from
`signing_shell.py` after migrating or deleting tests that import them. Move any
remaining composition-only contract that is proven unused from `signing_shell.py`
to a focused module; do not move active Qt binding or close-aware disposal code
without a caller migration and regression test. Quarantine, rather than delete,
the broad `compat_surface` and `testing_adapter` only where Phase 3/testing
callers still depend on them.

Boundary tests prove open success, replacement ordering, composition
failure preservation, mount failure cleanup, idempotent close, active-handle
publication, app-frame action routing through the active handle, and no stale
parallel state after close. Delete tests whose only purpose was asserting the
removed compatibility bundle or dead shell helper, replacing them with behavior
assertions through the host/handle boundary.

The touched-scope nomenclature inventory removed obsolete `phase3` names from
new/current lifecycle code and documentation. Record stable external names that
remain in `README.md`, `docs/ARCHITECTURE.md`, CLI/parser tests, fixtures, and
artifact paths as an explicit follow-up migration boundary; do not rename them
in this slice.

## Milestones

### Milestone 1: Typed workspace handle

Introduce the handle and host-facing contracts while preserving the current
composition implementation. Add in-memory/fake mount and factory tests proving
the handle contains the mount target and explicit ports. Existing lifecycle
tests must remain green.

### Milestone 2: App-frame migration and compatibility removal

Route open/close and all frame shell actions through the host's active handle.
Remove the compatibility outcome, duplicated state, duplicate widget extraction,
and dead shell presentation helpers. Keep active harness/testing adapters behind
explicit compatibility boundaries.

### Milestone 3: Compliance, nomenclature, and closure

Run the full test suite, lint, compilation, diff checks, architecture/spec
review, docs reconciliation, `phase3` inventory, and process/temporary-artifact
cleanup. Resolve any review finding in a child ExecPlan before commit closure.

## Concrete Steps

Run every command from `/home/daekar/FoliaSeal`.

    rg -n "WorkspaceCompatibilityState|OpenWorkspaceOutcome|shell_widget|_current_shell_port|_current_workspace|SIGNATURE_PRESET_PLACEHOLDER|_format_appearance_summary" src tests docs/ARCHITECTURE.md
    .venv/bin/python -m pytest -q tests/unit/test_signing_workspace_lifecycle.py tests/unit/test_qt_app_frame_workspace_open.py tests/unit/test_qt_app_frame.py tests/unit/test_qt_signing_shell.py

After implementation, run:

    .venv/bin/python -m pytest -q
    .venv/bin/ruff check src tests
    .venv/bin/python -m compileall -q src tests
    git diff --check
    rg -n -i "phase3" src/foliaseal/presentation/qt/signing_workspace_lifecycle.py src/foliaseal/presentation/qt/app_frame_workspace_open.py src/foliaseal/presentation/qt/signing_workspace_host.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_signing_workspace_lifecycle.py tests/unit/test_qt_app_frame_workspace_open.py || true
    ps -eo comm= | rg '^(python|python3|foliaseal)$' || true
    git status --short

The expected final result is a green full suite, clean Ruff/compile/diff
checks, no obsolete compatibility names in the current lifecycle boundary, no
`phase3` names in the touched lifecycle scope, no project processes, and a
clean working tree after commit.

## Validation and Acceptance

Opening a valid PDF through the app frame must return and mount a
`WorkspaceHandle`, expose its shell port to save-as/text-selection/settings
actions, and publish it as the only active workspace. Opening a second PDF must
mount the second candidate before disposing the first. A page-count, composition,
or mount failure must dispose only the candidate and leave the first workspace
active. Closing twice must not raise or dispose the same widget twice.

The focused lifecycle/app-frame/shell tests and the full project suite must pass.
Ruff, compileall, and `git diff --check` must be clean. Architecture review must
confirm that app-frame state is sourced from the host handle, compatibility
payloads are removed or explicitly quarantined, and no active testing/harness
contract was silently deleted. Documentation must describe the new boundary and
the deliberate preservation of stable external Phase 3 names.

## Idempotence and Recovery

The refactor is safe to repeat because tests use fake factories, fake mount
ports, and temporary data. Keep the existing lifecycle tests while migrating;
remove old tests only after equivalent boundary tests pass. If a Qt constructor
fails after creating a candidate widget, dispose that candidate before re-raising.
If any caller still needs compatibility fields, add a named adapter and record
the caller rather than restoring the old production outcome. Never delete or
rename serialized Phase 3 command/manifest/JSON/artifact contracts without a
separate migration plan and fixtures.

## Artifacts and Notes

The completed plan must record evidence in this section:

    focused lifecycle/app-frame/shell tests: 140 passed
    full suite: 1026 passed, one pre-existing Pillow deprecation warning
    architecture/spec review: two independent reviews passed; no child plan required
    phase3 inventory: no obsolete names in touched lifecycle scope; stable external names retained across CLI, manifests, JSON/DTOs, and artifact paths
    git diff --check: clean
    process audit: no FoliaSeal/Python process
    implementation commit: 2e9caa2458ee124d19b070b7e5bac8424007c889
    plan-closure commit: pending parent-agent update

No generated artifacts, dialogs, certificates, or GUI processes may remain open
or untracked after the audit.

## Interfaces and Dependencies

The new frame-facing contract should be equivalent to:

    @dataclass(frozen=True)
    class WorkspaceHandle:
        source_pdf: Path
        widget: Any
        shell: SigningWorkspacePort
        testing: SigningWorkspaceTestingPort
        viewer_workflow: ViewerWorkflow
        signing_workflow: SigningDraftWorkflow

    class SigningWorkspaceHost:
        def open(self, source_pdf: Path) -> WorkspaceHandle: ...
        def close(self) -> None: ...
        def active(self) -> WorkspaceHandle | None: ...

The implementation may keep `OpenWorkspaceCommand` and the existing composition
ports internally, but the app frame must not construct or inspect them. The
production Qt adapter remains responsible for widgets and `deleteLater()`;
tests use fake workspace factories, fake mount hosts, and plain disposable
objects. `SigningWorkspacePort` remains explicit and typed; `widget()` is
removed from the production caller contract. The remaining
`compat_surface`/`testing_adapter` seam is intentional for legacy widget
exports and Phase 3/testing callers.

## Revision Notes

2026-08-03: Created after the required fresh DevLoop explorer review and the
recommended common-caller/minimal hybrid comparison. Added explicit legacy
compatibility-removal scope and a touched-scope `phase3` nomenclature audit
while preserving stable external evidence contracts.

2026-08-03: Closed implementation and documentation reconciliation. Recorded
the `SigningWorkspaceHost`/`WorkspaceHandle` flow, removal of
`OpenWorkspaceOutcome`, `WorkspaceCompatibilityState`, duplicate frame state,
and `SigningWorkspacePort.widget()`, the intentional compatibility/testing
boundary, two compliance reviews, 140 focused tests, and the Phase 3 inventory
scope. Full-suite and commit-closure evidence are complete. Full suite passed
1026 tests with one pre-existing Pillow deprecation warning; Ruff, compileall,
diff checks, and the process audit passed. Implementation commit:
`2e9caa2458ee124d19b070b7e5bac8424007c889`.
