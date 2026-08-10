# First-use preset creation and selection flow

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can first-use creation and explicit selection of a required-Appearance preset in the real FoliaSeal GUI. It is mapped to UI_SPEC WF02/WF03 and acceptance scenario 2. The
slice is one vertical path through the relevant persistent model,
application workflow, Qt surface, focused tests, and observable acceptance.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are frozen governing contracts.
- [x] docs/ExecPlans/ui_signing_rail_stage_status_execplan.md (bounded rail/status surface is live)
- [x] docs/ExecPlans/ui_signature_preset_transactions_execplan.md (document-independent preset editor is live)
- [x] docs/ExecPlans/ui_appearance_editor_transaction_execplan.md (document-independent Appearance editor is live)
- [x] docs/ExecPlans/ui_placement_editor_transaction_execplan.md (fixed-page editor is live)

## Progress

- [x] (2026-08-10) Audit the no-preset rail state, Library entry point, and callback composition seams.
- [x] (2026-08-10) Implement the smallest complete no-preset guidance and Library create/manage path.
- [x] (2026-08-10) Confirm no phase3 product-facing compatibility path was introduced; the callback uses existing neutral workspace boundaries.
- [x] (2026-08-10) Run focused shell/AppFrame/workspace validation and clean processes/artifacts.
- [ ] (2026-08-10) Complete nested first-use return-to-preset behavior and commit the follow-up slice.

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

The bounded first-use increment is implemented. A newly opened document with no saved presets now
renders explicit guidance in the Signature preset rail group and a `Create or manage presets…`
button. The button crosses the typed workspace composition callback to the existing modeless
Signature Library, whose Presets catalog opens first and exposes the document-independent Appearance
and Preset editors. The current signing draft is not mutated by opening the Library. Full nested
return-to-suspended-preset behavior, certificate creation/configuration from that nested path, and
missing optional per-document input prompts remain follow-up work.

## Context and Orientation

The relevant code is signing workspace properties/sidebar; app_frame_profile_library.py; preset/appearance/placement stores. FoliaSeal is a Python/Qt Linux PDF signing application. The
primary flow is open, review, select reusable setup, place one visible signature, preview
readiness, sign/save, verify, and reopen. V1 excludes tabs, printing, broad PDF editing, cloud
workflow, enterprise trust administration, and multiple pending signatures.

A compatibility surface is an adapter retained only for old callers. “phase3” names identify legacy
evidence/harness infrastructure and must not be introduced into ordinary product UI or new primary
contracts; production backend/evidence imports may be renamed only after a neutral migration proves
the old name is no longer required.

## Change Slice

Primary change class: behavior change. Allowed changes are the named modules, focused tests,
bounded ignored local evidence, and minimum truthful documentation. Do not mix unrelated evidence
rebaselines, V2 features, or packaging work.

## Plan of Work

When no preset exists, make Create preset open the Library, support nested Appearance and optional
Certificate/Placement creation, suspend the parent draft, and return without silently applying the
saved preset. The bounded prerequisite now exposes truthful no-preset guidance and a typed Library
entry point from the rail; the remaining nested return-to-suspended-preset workflow must be added
without making Library launch mutate the active draft. Make the rail selector explicit and start
every new PDF with no active preset. Add or preserve typed application and public Qt-port boundaries
rather than reaching through private widgets. Keep schema and terminology aligned with the frozen
documents. When a legacy path is replaced, prove its callers are migrated before deleting it.

## Milestones

Milestone 1 audited the empty-catalog state and added a focused no-preset rail test. Milestone 2
wired the first-use Library entry point through typed workspace composition. Milestone 3 validated
the offscreen novice entry surface and recorded the remaining nested completion/return gaps.

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
- Remaining gaps: nested editor suspension/return, optional Certificate/Placement creation from the
  nested first-use flow, and explicit missing per-document input prompts.

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

Revision note: 2026-08-09 / Codex
Created as a dependency-ordered child of the approved SPEC/UI_SPEC compliance breakdown.
