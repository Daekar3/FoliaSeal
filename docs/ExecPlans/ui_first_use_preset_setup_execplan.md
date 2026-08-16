# First-use preset creation and selection flow

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a first-time user can open the Signature Library from the empty preset rail,
land in the Presets catalog regardless of the last Library catalog used, create a required-
Appearance preset through the nested editor, optionally create or import a Certificate and create
a blank-page Placement, return to the active document, and explicitly select the newly saved
preset. The Library refreshes the live rail without silently applying the preset or mutating the
active signing draft. This is the first-use flow mapped to UI_SPEC WF02/WF03 and acceptance
scenario 2; current-document Placement capture and external acceptance gates remain separate.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are frozen governing contracts.
- [x] docs/ExecPlans/ui_signing_rail_stage_status_execplan.md (bounded rail/status surface is live)
- [x] docs/ExecPlans/ui_signature_preset_transactions_execplan.md (document-independent preset editor is live)
- [x] docs/ExecPlans/ui_appearance_editor_transaction_execplan.md (document-independent Appearance editor is live)
- [x] docs/ExecPlans/ui_placement_editor_transaction_execplan.md (fixed-page editor is live)

## Progress

- [x] (2026-08-10) Audit the no-preset rail state, Library entry point, and callback composition seams.
- [x] (2026-08-10) Implement the smallest complete no-preset guidance and Library create/manage path.
- [x] (2026-08-10) Confirm no acceptance product-facing compatibility path was introduced; the callback uses existing neutral workspace boundaries.
- [x] (2026-08-10) Run focused shell/AppFrame/workspace validation and clean processes/artifacts.
- [x] (2026-08-10) Force first-use Library entry to the Presets catalog without changing the
  persisted last-catalog preference.
- [x] (2026-08-10) Notify the active signing shell after reusable-object saves so the new preset is
  visible in the live rail, while leaving selection explicit.
- [x] (2026-08-10) Add focused/offscreen first-use coverage and reconcile documentation; commit is
  the remaining closeout step.
- [x] (2026-08-16) Added nested Certificate Create/Import actions. Existing certificate dialogs
  return a stable configuration to the suspended Preset, which refreshes and selects it without
  applying anything to the active signing draft.

## Surprises & Discoveries

- Observation: first-use setup crosses the signing shell and reusable-object catalog; the child
  must offer an explicit partial-preset path without silently creating invalid persisted state.
  Evidence: the live source paths and focused tests listed below are the audit baseline.
- Observation: the local collaboration runtime continued to report `agent thread limit reached`
  after prior completed explorer threads were interrupted. A checkout-grounded self-audit was used
  for the required compliance pass; no GUI or application blocker was inferred from that tooling
  limitation.
  Evidence: full Ruff/test/process checks and explicit callback-path inspection below.

## Decision Log

- Decision: obey SPEC.md, SCHEMAS.md, and UI_SPEC.md in that precedence order.
  Rationale: these are the repository's explicit authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep the slice limited to one user-visible first-use preset creation and selection flow outcome.
  Rationale: narrow changes are independently testable and recoverable.
  Date/Author: 2026-08-09 / Codex

## Outcomes & Retrospective

The first-use flow is implemented: a newly opened document with no saved presets renders explicit
guidance and a `Create or manage presets…` button through typed workspace composition. The
modeless Library focuses Presets, supports nested Appearance, Certificate Create/Import, and
blank-page Placement return paths, and successful saves refresh the live signing rail without
auto-selecting the new preset. Current-document Placement capture and external display/package/
release acceptance remain separate boundaries.

## Context and Orientation

The relevant code is signing workspace properties/sidebar; app_frame_profile_library.py; preset/appearance/placement stores. FoliaSeal is a Python/Qt Linux PDF signing application. The
primary flow is open, review, select reusable setup, place one visible signature, preview
readiness, sign/save, verify, and reopen. V1 excludes tabs, printing, broad PDF editing, cloud
workflow, enterprise trust administration, and multiple pending signatures.

A compatibility surface is an adapter retained only for old callers. “acceptance” names identify legacy
evidence/harness infrastructure and must not be introduced into ordinary product UI or new primary
contracts; production backend/evidence imports may be renamed only after a neutral migration proves
the old name is no longer required.

## Change Slice

Primary change class: behavior change. Allowed changes are the named modules, focused tests,
bounded ignored local evidence, and minimum truthful documentation. Do not mix unrelated evidence
rebaselines, V2 features, or packaging work.

## Plan of Work

When the empty-preset rail action invokes the Library, pass an explicit first-use intent through the
existing typed callback boundary so `ReusableObjectLibraryDialog` starts at
`LibraryCatalog.PRESETS` without persisting or overwriting `library_last_catalog`. Add a typed
reusable-object-change callback from the Library to AppFrame and route it through the public shell
refresh port (`refresh_signature_profiles`) after successful Appearance and Preset saves. Do not
auto-select the new preset: WF03 requires an explicit user selection in the rail after returning.
Ensure the callback never mutates the active document draft by itself. Add focused tests for
Presets-first entry, nested Appearance Save followed by Preset Save, live rail refresh, explicit
selection, and unchanged draft state. Add or preserve typed application and public Qt-port
boundaries rather than reaching through private widgets. Keep schema and terminology aligned with
the frozen documents. When a legacy path is replaced, prove its callers are migrated before
deleting it.

## Milestones

Milestone 1 audited the empty-catalog state and added a focused no-preset rail test. Milestone 2
wired the first-use Library entry point through typed workspace composition. Milestone 3 makes the
entry Presets-first and connects successful Library saves to the live rail refresh while keeping
selection explicit, then validates the complete offscreen novice path.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e 'preset|Library|Create|select' src/foliaseal/presentation/qt/signing_workspace_properties_panel.py src/foliaseal/presentation/qt/signing_workspace_sidebar.py src/foliaseal/presentation/qt/app_frame_profile_library.py
    .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_reusable_signing_objects.py tests/unit/test_reusable_signing_models.py
    .venv/bin/ruff check src tests
    .venv/bin/pytest -q
    git diff --check

Run this bounded walkthrough from /home/daekar/FoliaSeal with an isolated configuration root:

    audit_root=$(mktemp -d /tmp/foliaseal-plan-audit-XXXXXX)
    timeout --foreground 30s env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf || test "$?" -eq 124
    ps -eo pid,cmd | rg 'FoliaSeal|foliaseal|PySide6|pytest' | rg -v 'rg ' || true
    rm -rf "$audit_root"
    test ! -e "$audit_root"

Expected evidence is the stated user-visible behavior plus a mandatory Qt-test or display-backed
walkthrough. Record the exact input sequence, widget state, expected observation, evidence path, and
cleanup result; the bounded timeout is only a lifecycle check.

## Validation and Acceptance

Acceptance is behavioral: A first-time user can create a required-Appearance preset, return to the Library or rail, explicitly select it, and see only missing per-document inputs requested; selection never silently creates a placement. Focused tests must pass, shared-code changes must
leave the full suite green, and the GUI audit must record the visible result and cleanup.

## Evidence Record

Before checking this child in the parent, record the governing UI_SPEC requirement, exact focused
test command/result, first-use input sequence and observed missing-field state, evidence path and
cleanup result, and compatibility grep proof.

Record the contributing UI_SPEC scenario ID(s) and either the owning SVG path or an explicit
"no SVG" decision alongside the evidence row.
Also record the exact focused test node and expected result (`N passed`); when the slice adds a new
contract, record that the test was red before implementation and green afterward.

Bounded evidence (2026-08-10):

- `.venv/bin/pytest -q tests/unit/test_qt_signing_shell.py::test_first_use_preset_surface_exposes_library_create_action tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame_workspace_open.py tests/unit/test_signing_workspace_host.py` — 114 passed.
- The empty catalog renders `No saved presets yet...` and the `Create or manage presets…` action;
  clicking it invokes the injected Library callback without changing the active workflow.
- The callback is carried through `OpenWorkspaceCommand`, `SigningWorkspaceEnvironment`,
  `SigningWorkspaceBootstrap`, and `QtSigningWorkspaceComposition` rather than reaching through
  private widgets. The existing no-document Library remains modeless and Presets-first.
- No new SVG: this increment adds the prescribed rail entry action and callback plumbing but does
  not change the normative Library topology.
- Process cleanup after the Qt runs found no FoliaSeal/PySide6/pytest processes. Display-backed xcb
  acceptance remains unavailable and is not claimed here.
- Bounded CLI launch: the isolated `QT_QPA_PLATFORM=offscreen ... foliaseal gui --pdf-path ...`
  walkthrough exited `1` with the known `SingleInstanceUnavailable`/QLocalServer endpoint error
  before the frame was created. The temporary config root was removed and the process audit was
  empty; this is recorded as an environment transport limitation, not first-use evidence.
- First-use implementation evidence: `tests/unit/test_qt_app_frame_profile_library.py` covers
  non-persisting Presets focus and nested Appearance/Preset save notifications; the AppFrame unit
  test proves the active shell refresh callback runs while
  `current_signing_workflow.selected_signature_preset_id` remains `None`.
- Real offscreen first-use integration: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q
  tests/integration/test_signature_library_topology.py` => `4 passed`; it creates and saves a
  required-Appearance preset after forcing Presets-first entry and confirms the Library returns to
  its normal detail surface.
- Focused regression: `.venv/bin/pytest -q tests/unit/test_qt_app_frame_profile_library.py
  tests/unit/test_qt_app_frame.py tests/unit/test_qt_signing_shell.py
  tests/unit/test_qt_app_frame_workspace_open.py tests/unit/test_signing_workspace_host.py
  tests/integration/test_signature_library_topology.py` => `191 passed`; Ruff and
  `git diff --check` are clean.
- Full regression after this slice: `1367 passed, 20 skipped, 1 warning in 50.14s`.
- Final bounded lifecycle audit: exit `1` with the expected isolated `SingleInstanceUnavailable`
  endpoint error; no FoliaSeal/PySide6/pytest processes remained and the temporary root was
  removed.
- Remaining gaps: current-document Placement capture from the nested first-use flow plus external
  display/package/release acceptance. Nested Appearance, Certificate Create/Import, blank-page
  Placement, editor suspension/return, Presets-first entry, live rail refresh, and explicit
  selection behavior are complete in this slice and its dependencies.

## Idempotence and Recovery

Use temporary configuration and sibling output paths. If work fails halfway, preserve user PDFs and
drafts, update Progress with completed/remaining work, clean owned processes and artifacts, and
retry from the recorded state. Do not resurrect removed compatibility paths.

## Artifacts and Notes

Record concise output, focused screenshots or JSON under ignored artifacts/when useful, and exact
changed files. Never commit private keys, passwords, generated PDFs, or machine-local absolute paths.

## Interfaces and Dependencies

Use the existing typed application workflows, schema models, persistence stores, and public Qt frame
or workspace ports. The final behavior must be exercised by tests/unit/test_qt_signing_shell.py, reusable-object tests, and a first-use Qt integration test. Any temporary adapter must
name its remaining consumer and retirement condition in this plan.

Revision note: 2026-08-10 / Codex
Updated after the nested blank-page Placement and nested Certificate Create/Import children:
first-use entry focuses Presets without persisting navigation, successful nested saves refresh the
active shell, the user explicitly selects the new preset, and reusable Certificate/Placement
objects can be created and attached before Preset Save. Current-document Placement capture remains
in its owning follow-up child.
