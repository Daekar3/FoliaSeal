# Fixed signing rail, status regions, and stage model

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can use the approximately 320-pixel right rail whose interactive signing controls remain in
the upper controls area while a protected lower region shows only read-only readiness/result
status and visibly identifies at most one recommended action. This is the bounded portion of UI_SPEC
SUR02, SUR07, section 11, and acceptance scenarios 2 and 5 that the current coordinator can
truthfully support. It does not claim the full asynchronous signing, verification, or dirty-draft
state machine; those remain explicit follow-up work. The remembered divider and independently
scrollable regions are implemented by `ui_rail_divider_persistence_execplan.md`. The slice is one vertical
path through the relevant application workflow, Qt surface, focused tests, and observable
acceptance, not a generic refactor.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are the frozen governing contracts.
- [x] docs/ExecPlans/ui_launch_no_document_execplan.md
- [x] docs/ExecPlans/ui_command_model_shortcuts_execplan.md (File/View foundation slices complete;
  remaining menu groups remain open in the command-model child)

## Progress

- [x] (2026-08-09) Audit the current implementation and write a failing focused test for the stated outcome.
- [x] (2026-08-09) Implement the bounded fixed-rail, protected-status, and typed recommended-action path.
- [x] (2026-08-09) Re-audit commit 8cec447d0 and identify that its status region incorrectly contained interactive controls and that its recommended action was not visibly rendered.
- [x] (2026-08-09) Move interactive signing controls above a read-only status region, add visible and accessible recommended-action treatment, and prove the real Qt geometry.
- [x] (2026-08-09) Review migrated compatibility and phase3 product cruft; no retirement condition in the named sidebar/coordinator modules was met, so no unrelated removal was mixed into this slice.
- [x] (2026-08-09) Run focused, regression, and real offscreen Qt validation; record evidence and clean up.
- [x] (2026-08-09) Updated this plan and relevant architecture/status documentation; the bounded
  implementation and correction are committed in `8d67d1652`, with remaining async/state-machine
  scope explicitly deferred to its owning children.
- [x] (2026-08-10) Closed the previously deferred `Saved but not verified` rail state through the
  readiness/recovery follow-up; this plan remains the owning rail geometry/status boundary while
  `ui_readiness_caveats_status_execplan.md` owns the result discriminator. Coordinator and real
  offscreen sidebar coverage prove the warning, disabled Sign button, and Verify again action.

## Surprises & Discoveries

- Observation: the signing rail is coordinated through sidebar and action-coordinator seams; the
  child must keep readiness state plain-language and derive action enablement from one state model.
  Evidence: the live source paths and focused tests listed below are the audit baseline.
- Observation: the existing sidebar uses a 3:2 stretch split and appends the action panel before
  review/text cards, so its width and status position vary with content. The coordinator has no
  typed primary-action identity even though it already exposes `can_sign` and result capability.
  Evidence: `signing_workspace_composition.py` and `SigningWorkspaceSidebar.__init__` inspected on
  2026-08-09.
- Observation: commit 8cec447d0 placed the entire action-controls group, including Choose output,
  Confirm and sign, and Open signed PDF, inside `status_region`. UI_SPEC SUR02/SUR07 require that
  lower region to be read-only.
  Evidence: explorer review of `signing_workspace_sidebar.py` and the current unit assertion that
  `signing_action_controls.container.parent is status_region`.
- Observation: the dynamic `foliasealPrimaryAction` property had no visible Qt styling or
  accessibility treatment, so a user could not identify the recommended action.
  Evidence: focused tests only inspected the property and no stylesheet or accessible name consumed
  it.
- Observation: the real Qt acceptance test can prove the sidebar's production widget tree and
  fixed geometry, but constructing the entire application bootstrap would pull unrelated signing
  backend dependencies into this narrow contract test.
  Evidence: `tests/integration/test_signing_rail_layout.py` constructs `SigningWorkspaceSidebar`
  with production `QtSigningWidgetBindings` and embeds it in a real `QMainWindow`; the full shell
  composition remains covered by its existing unit/integration tests.

## Decision Log

- Decision: honor SPEC.md product scope, SCHEMAS.md persistent-object semantics, and UI_SPEC.md interaction wording in that order.
  Rationale: the repository explicitly defines those authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep this change limited to one observable fixed signing rail, status regions, and stage model outcome.
  Rationale: narrow commits make GUI regressions and recovery auditable.
  Date/Author: 2026-08-09 / Codex
- Decision: implement a 320 logical-pixel rail, a protected 200-pixel minimum status region pinned
  after the upper controls, and a typed `recommended_action` projection for the currently supported
  coordinator states. Preserve secondary output/reopen controls and defer true asynchronous Signing
  and broader verification state machines to their named children; the Saved-but-not-verified state
  is now closed by the readiness/recovery follow-up.
  Rationale: these changes make truthful states stable and actionable without inventing verification
  results or fake progress.
  Date/Author: 2026-08-09 / Codex
- Decision: keep the interactive signing action group outside `status_region`; the lower region will
  contain only journey, stage, detail, and result labels. Apply a visible border/weight treatment,
  tooltip, and accessible name to the one recommended button while retaining the typed property for
  styling and tests.
  Rationale: UI_SPEC defines the status region as read-only and requires one clear next action using
  text, icon, or color. This corrects the prior foundation without inventing unsupported workflow
  states.
  Date/Author: 2026-08-09 / Codex

## Outcomes & Retrospective

The first Loop 6 commit established the fixed width and typed coordinator projection, but its
compliance review found that the lower region was not read-only and that the recommended action was
not visible. The correction now leaves a 320-pixel rail with interactive signing controls above a
read-only status region, visible and accessible recommended-action styling, coordinator transition
coverage, and real offscreen Qt geometry evidence. The coordinator now also projects a typed
`saved_but_not_verified` status for `POST_VERIFY_FAILED` with a preserved artifact, retaining
recovery actions and disabling Sign and save until recovery resolves; ordinary pre-write failures
use `signing_failed`. Full asynchronous Signing and dirty-draft policy remain deferred to their
owning plans; independent scroll regions and remembered divider width are covered by
`ui_rail_divider_persistence_execplan.md`.
This bounded child is complete in `8d67d1652`.

## Context and Orientation

The relevant code is signing_workspace_sidebar.py; signing_action_coordinator.py; signing_workspace_composition.py; signing shell tests. FoliaSeal is a Python/Qt Linux PDF signing application. The
product flow is open, review, select reusable setup, place one visible signature, preview
readiness, sign/save, verify, and reopen. This slice must preserve the V1 anti-goals: no tabs,
printing, general PDF editing, cloud workflow, broad trust administration, or multiple pending
signatures.

The words “compatibility surface” mean an adapter kept only for old callers. “phase3” names identify
legacy evidence/harness infrastructure and must not appear in ordinary product-facing UI or new
primary contracts; production backend/evidence imports may be renamed only after a neutral migration
proves the old name is no longer required.

## Change Slice

Primary change class: behavior change. Allowed changes are the named implementation modules,
focused tests, bounded local evidence, and the minimum docs/status corrections needed to keep the
repository truthful. Do not mix unrelated architecture scans, V2 features, broad evidence
rebaselines, or packaging changes unless this slice explicitly requires them.

## Plan of Work

Reshape the mounted workspace into a stable right signing rail with an upper interactive controls
group and a protected lower status group. In `signing_workspace_sidebar.py`, split the existing
`SigningActionControls` widget tree so its buttons remain in the upper action group while its
journey, stage, detail, and result labels are owned by a read-only `status_container`. Keep the
existing `SigningWorkspaceSidebarSurface` fields and callback paths stable. Render
`recommended_action` with the existing dynamic property plus a visible style and accessibility
text, and add coordinator transition assertions for the supported setup, ready, success,
unavailable-output, and failure cases. Add a real offscreen Qt test that constructs the sidebar and
checks the fixed width, protected status height, read-only status children, and visible primary
action. Update architecture and plan documentation to state supported states and explicit
deferrals. Do not claim the full UI_SPEC state machine, remembered divider, or asynchronous progress
until their dedicated plans implement them.

## Milestones

Milestone 1 defines one readiness/action state and adds coordinator/sidebar tests. Milestone 2 wires
the fixed-width rail with an upper action group and read-only lower status through public ports.
Milestone 3 proves the real Qt geometry, visible primary-action treatment, disabled actions, and
supported status transitions in an offscreen audit. Full UI_SPEC state coverage remains a separate
set of child plans.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e 'class SigningWorkspaceSidebar|class SigningActionCoordinator' src/foliaseal/presentation/qt/signing_workspace_sidebar.py src/foliaseal/presentation/qt/signing_action_coordinator.py
    .venv/bin/pytest -q tests/unit/test_qt_signing_action_coordinator.py tests/unit/test_qt_signing_shell.py tests/unit/test_signing_workspace_sidebar.py tests/unit/test_qt_signing_rail_stage_status.py tests/integration/test_signing_rail_layout.py
    .venv/bin/ruff check src tests
    .venv/bin/pytest -q
    git diff --check

Run this bounded walkthrough from /home/daekar/FoliaSeal with an isolated configuration root:

    audit_root=$(mktemp -d /tmp/foliaseal-plan-audit-XXXXXX)
    timeout --foreground 30s env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf || test "$?" -eq 124
    ps -eo pid,cmd | rg 'FoliaSeal|foliaseal|PySide6|pytest' | rg -v 'rg ' || true
    rm -rf "$audit_root"
    test ! -e "$audit_root"

Expected evidence is the stated user-visible behavior plus a mandatory real Qt test or display-backed
walkthrough. The real test records a 320px sidebar, a label-only status region, and accessible/visible
recommended action. Record the exact input sequence, widget state, expected observation, evidence
path, and cleanup result; the bounded timeout is only a lifecycle check.

The bounded launch audit was attempted with an isolated configuration root on 2026-08-09. The
application exited with `GUI_RC=1` and `SingleInstanceUnavailable: Unable to claim or reach the
FoliaSeal instance endpoint`; this environment cannot bind the local Qt single-instance endpoint.
No FoliaSeal/PySide6 process remained, and the temporary audit root was removed (`AUDIT_ROOT_CLEAN=1`).
The real offscreen widget test is therefore the authoritative geometry/accessibility evidence for
this slice, while the launch limitation remains recorded rather than hidden.

## Validation and Acceptance

Acceptance is behavioral for the currently supported coordinator states: the real Qt sidebar is
320 logical pixels wide, interactive signing buttons are outside the lower status group, the status
group contains only read-only labels and retains its 200-pixel minimum, and exactly one enabled
recommended action receives visible styling when the state supplies one. Setup-required,
placement, ready, successful-output, unavailable-output, and failure transitions must be covered by
coordinator tests. The focused regression suite, full suite, and offscreen Qt geometry test must
pass, and the bounded GUI audit must record the visible result and cleanup. The `Saved but not
verified` state is now implemented by the readiness/recovery follow-up and is covered at both the
coordinator and sidebar-rendering boundaries. The remaining full UI_SPEC items are No document open,
Signing progress and dirty-draft prompts; independent scroll regions and remembered divider are
covered by the dedicated divider child, not claimed as part of this bounded coordinator slice.

## Evidence Record

Before checking this child in the parent, record the governing UI_SPEC requirement and
`docs/ui/sign-and-save-states-exploratory.svg`, exact focused test command/result, real Qt rail
geometry and read-only status observation, recommended-action styling observation, evidence path
and cleanup result, and compatibility grep proof. Record deferred full-state requirements rather
than implying that this bounded test proves them.

Record the contributing UI_SPEC scenario ID(s) and either the owning SVG path or an explicit
"no SVG" decision alongside the evidence row.
Also record the exact focused test node and expected result (`135 passed` in the current recovery/
rail pass; the full suite is `1482 passed, 20 skipped, 1 warning`);
when the slice adds a new contract, record that the test was red before implementation and green
afterward. The focused recovery/rail command completed with `135 passed`; Ruff and
`git diff --check` both passed.

## Idempotence and Recovery

Use temporary sibling outputs and isolated configuration for repeatable tests. If implementation
fails halfway, keep the source PDF and unsigned draft intact, terminate owned processes, remove only
this slice's generated artifacts, and update Progress with completed and remaining work. Re-running
the tests must not mutate user data or resurrect retired compatibility code.

## Artifacts and Notes

Record concise command output, focused screenshots/JSON under ignored artifacts/ when useful, and
the exact files changed. Do not commit generated PDFs, private keys, passwords, or machine-local
absolute paths.

## Interfaces and Dependencies

Use existing typed application workflows and public Qt ports rather than private child-widget
reach-through. `SigningActionControls` exposes both its interactive `container` and read-only
`status_container`; `SigningWorkspaceSidebarSurface.status_region` refers to the latter. Create
`tests/unit/test_qt_signing_rail_stage_status.py` for fake-binding state and
`tests/integration/test_signing_rail_layout.py` for real offscreen geometry. The final interface
must be exercised by those files plus `tests/unit/test_qt_signing_action_coordinator.py` and
`tests/unit/test_qt_signing_shell.py`. Any compatibility adapter retained temporarily must have a
named consumer and a retirement condition recorded in this plan.

Revision note: 2026-08-09 / Codex
Created as child ui_signing_rail_stage_status_execplan.md of the approved SPEC/UI_SPEC compliance breakdown.
Revision note: 2026-08-09 / Codex
Narrowed the claim and added a correction milestone after review found interactive controls in the
read-only status region, invisible recommended-action metadata, and missing real-Qt evidence.
