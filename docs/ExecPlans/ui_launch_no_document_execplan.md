# Direct launch and no-document frame

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can reach a stable no-document desktop frame with primary Open a PDF and secondary Manage Signature Library actions in the real FoliaSeal GUI. It is mapped to UI_SPEC LAY01–LAY02 and acceptance scenario 1. The slice is intentionally one vertical path through the relevant persistent
model, application workflow, Qt surface, focused tests, and observable acceptance; it is not a
generic refactor.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are the frozen governing contracts.
- [ ] None.

## Progress

- [x] (2026-08-09) Audited the current no-document frame and added focused unit/integration coverage for
  the landing surface, primary Open PDF action, secondary Signature Library action, and closed state.
- [x] (2026-08-09) Implemented the frame-owned no-document action panel without restoring a document,
  draft, or recent file.
- [x] (2026-08-09) Changed the direct Library entry point to reuse one modeless dialog instance;
  the deeper three-column Library/editor topology remains owned by the next tranche.
- [ ] (2026-08-09) Remove migrated compatibility or acceptance product cruft whose retirement condition is met.
- [x] (2026-08-09) Ran focused Qt tests, Ruff, and the bounded no-document launch cleanup check.
- [x] (2026-08-09) Ran the full regression suite: `1153 passed, 19 skipped, 1 warning`.
- [ ] (2026-08-09) Update this plan and relevant architecture/status documentation, then commit the implementation slice.

## Surprises & Discoveries

- Observation: the current launch path must be exercised as a real Qt frame before downstream
  document and Library slices can claim an end-to-end starting state.
  Evidence: the live source paths and focused tests listed below are the audit baseline.
- Observation: the display-backed audit runner cannot connect to the current `DISPLAY=:0` session.
  Evidence: the runner exited 134 because the Qt xcb platform could not connect; the offscreen real-Qt
  integration test remains the available widget-level evidence and no process was left behind.

## Decision Log

- Decision: honor SPEC.md product scope, SCHEMAS.md persistent-object semantics, and UI_SPEC.md interaction wording in that order.
  Rationale: the repository explicitly defines those authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep this change limited to one observable direct launch and no-document frame outcome.
  Rationale: narrow commits make GUI regressions and recovery auditable.
  Date/Author: 2026-08-09 / Codex
- Decision: close this slice on the direct no-document actions and modeless Library entry point;
  defer the persistent toolbar/rail/status topology to the command, rail, and responsive-frame
  children, and defer keyboard traversal proof to the command-model child.
  Rationale: those surfaces have separate owners and dependencies; duplicating them here would
  create competing frame implementations while still leaving the final scenario gate in the parent.
  Date/Author: 2026-08-09 / Codex

## Outcomes & Retrospective

The no-document frame now exposes direct Open a PDF and Manage Signature Library actions while preserving the
existing closed action state. The Library entry is modeless and reused. Focused unit and real-Qt integration coverage passed (`29 passed`), and
the bounded launch cleanup check left no FoliaSeal processes. Display-backed visual inspection is
deferred until a usable Qt display session is available; the attempted command and xcb failure are
recorded in Surprises & Discoveries. The Qt integration test proves the widget-level state in the
current headless-capable environment. Persistent toolbar/rail/status regions and keyboard traversal
remain explicitly owned by the next foundation children and are not claimed complete here.

## Context and Orientation

The relevant code is src/foliaseal/__main__.py; src/foliaseal/presentation/qt/app_frame.py; app-frame tests. FoliaSeal is a Python/Qt Linux PDF signing application. The
product flow is open, review, select reusable setup, place one visible signature, preview
readiness, sign/save, verify, and reopen. This slice must preserve the V1 anti-goals: no tabs,
printing, general PDF editing, cloud workflow, broad trust administration, or multiple pending
signatures.

The words “compatibility surface” mean an adapter kept only for old callers. “acceptance” names identify
legacy evidence/harness infrastructure and must not appear in ordinary product-facing UI or new
primary contracts; production backend/evidence imports may be renamed only after a neutral migration
proves the old name is no longer required.

## Change Slice

Primary change class: behavior change. Allowed changes are the named implementation modules,
focused tests, bounded local evidence, and the minimum docs/status corrections needed to keep the
repository truthful. Do not mix unrelated architecture scans, V2 features, broad evidence
rebaselines, or packaging changes unless this slice explicitly requires them.

## Plan of Work

Make direct launch create a stable FoliaSeal window with disabled document actions, a primary Open a PDF action, a secondary Manage Signature Library action, no recent-file restoration, and an honest empty state. Keep the frame present before any PDF is opened and route existing settings/library services through the public frame boundary. Add typed seams where the current code passes raw widget internals or compatibility
kwargs. Preserve the public frame/workspace contract while migrating consumers, then delete the
old path once focused tests prove no callers remain. Keep user-facing terminology from UI_SPEC.md,
not schema/backend names.

## Milestones

Milestone 1 adds the no-document frame and keyboard reachability red tests. Milestone 2 wires the
frame-owned actions and empty state without restoring a document. Milestone 3 runs the no-argument
GUI launch, records the frame observation, and verifies no process or temporary state remains.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e 'FoliaSealAppFrame|launch_qt_app_frame' src/foliaseal/presentation/qt/app_frame.py
    .venv/bin/pytest -q tests/unit/test_qt_app_frame.py
    .venv/bin/ruff check src tests
    .venv/bin/pytest -q
    git diff --check

Run this bounded walkthrough from /home/daekar/FoliaSeal with an isolated configuration root:

    audit_root=$(mktemp -d /tmp/foliaseal-plan-audit-XXXXXX)
    set +e
    timeout --foreground 30s env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui
    gui_rc=$?
    set -e
    test "$gui_rc" -eq 0 || test "$gui_rc" -eq 124
    ! ps -eo pid,cmd | rg 'FoliaSeal|foliaseal|PySide6|pytest' | rg -v 'rg '
    rm -rf "$audit_root"

Expected evidence is a recorded no-document frame observation: window title, Open PDF and Library
actions, disabled document actions, and keyboard tab order, saved under
`artifacts/ui-audits/launch-no-document.txt` or an equivalent ignored file. The timeout and clean
process assertion are necessary cleanup checks, not substitutes for that observation.

## Validation and Acceptance

Acceptance for this slice is behavioral: Launching `foliaseal gui` shows the no-document action panel;
the panel exposes the normative Open a PDF and Manage Signature Library actions; the Library entry
opens one reusable modeless window; and no document, draft, recent file, or stale harness panel is
restored. The focused regression suite and full suite must pass, and the Qt evidence must record the
visible result and cleanup. Persistent toolbar/rail/status topology and keyboard traversal are
explicitly accepted by their named follow-up children and the parent scenario matrix.

## Evidence Record

Before checking this child in the parent, record the governing UI_SPEC requirement and
`docs/ui/main-workspace-no-document-exploratory.svg` plus
`docs/ui/main-workspace-document-open-exploratory.svg`, exact focused test command/result,
no-document launch and tab-order input sequence, observed frame state, evidence path and cleanup
result, and compatibility grep proof.

Record the contributing UI_SPEC scenario ID(s) and either the owning SVG path or an explicit
"no SVG" decision alongside the evidence row.
Also record the exact focused test node and expected result (`N passed`); when the slice adds a new
contract, record that the test was red before implementation and green afterward.

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
reach-through. The final interface is exercised by tests/unit/test_qt_app_frame.py and
tests/integration/test_gui_launch_no_document.py. Any compatibility adapter retained temporarily must have a named consumer and a
retirement condition recorded in this plan.

Revision note: 2026-08-09 / Codex
Created as child ui_launch_no_document_execplan.md of the approved SPEC/UI_SPEC compliance breakdown.
Updated during implementation loop 1 with the no-document action panel, focused red/green tests,
integration evidence, and cleanup results.
