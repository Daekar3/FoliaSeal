# Direct launch and no-document frame

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can reach a stable no-document desktop frame with primary Open PDF and secondary Library actions in the real FoliaSeal GUI. It is mapped to UI_SPEC LAY01–LAY02 and acceptance scenario 1. The slice is intentionally one vertical path through the relevant persistent
model, application workflow, Qt surface, focused tests, and observable acceptance; it is not a
generic refactor.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are the frozen governing contracts.
- [ ] None.

## Progress

- [ ] (2026-08-09) Audit the current implementation and write a failing focused test for the stated outcome.
- [ ] (2026-08-09) Implement the smallest complete model/application/Qt path.
- [ ] (2026-08-09) Remove migrated compatibility or phase3 product cruft whose retirement condition is met.
- [ ] (2026-08-09) Run focused, regression, and GUI validation; record evidence and clean up.
- [ ] (2026-08-09) Update this plan and relevant architecture/status documentation, then commit.

## Surprises & Discoveries

- Observation: the current launch path must be exercised as a real Qt frame before downstream
  document and Library slices can claim an end-to-end starting state.
  Evidence: the live source paths and focused tests listed below are the audit baseline.

## Decision Log

- Decision: honor SPEC.md product scope, SCHEMAS.md persistent-object semantics, and UI_SPEC.md interaction wording in that order.
  Rationale: the repository explicitly defines those authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep this change limited to one observable direct launch and no-document frame outcome.
  Rationale: narrow commits make GUI regressions and recovery auditable.
  Date/Author: 2026-08-09 / Codex

## Outcomes & Retrospective

Not started. At completion, state what a novice can now do, which tests and live evidence prove it, and any remaining gap.

## Context and Orientation

The relevant code is src/foliaseal/__main__.py; src/foliaseal/presentation/qt/app_frame.py; app-frame tests. FoliaSeal is a Python/Qt Linux PDF signing application. The
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

Make direct launch create a stable FoliaSeal window with disabled document actions, a primary Open PDF action, a secondary Signature Library action, no recent-file restoration, and an honest empty state. Keep the frame present before any PDF is opened and route existing settings/library services through the public frame boundary. Add typed seams where the current code passes raw widget internals or compatibility
kwargs. Preserve the public frame/workspace contract while migrating consumers, then delete the
old path once focused tests prove no callers remain. Keep user-facing terminology from UI_SPEC.md,
not schema/backend names.

## Milestones

Milestone 1 adds the no-document frame and keyboard reachability red tests. Milestone 2 wires the
frame-owned actions and empty state without restoring a document. Milestone 3 runs the no-argument
GUI launch, records the frame observation, and verifies no process or temporary state remains.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

    rg -n -e 'FoliaSealAppFrame|launch_qt_app_frame' src/foliaseal/presentation/qt/app_frame.py
    .venv/bin/pytest -q tests/unit/test_qt_app_frame.py
    .venv/bin/ruff check src tests
    git diff --check

Run this bounded walkthrough from /home/daekar/FoliaSeal with an isolated configuration root:

    audit_root=$(mktemp -d /tmp/foliaseal-plan-audit-XXXXXX)
    timeout --foreground 30s env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui
    ! ps -eo pid,cmd | rg 'FoliaSeal|foliaseal|PySide6|pytest' | rg -v 'rg '
    rm -rf "$audit_root"

Expected evidence is a recorded no-document frame observation: window title, Open PDF and Library
actions, disabled document actions, and keyboard tab order, saved under
`artifacts/ui-audits/launch-no-document.txt` or an equivalent ignored file. The timeout and clean
process assertion are necessary cleanup checks, not substitutes for that observation.

## Validation and Acceptance

Acceptance is behavioral: Launching foliaseal gui shows the no-document frame; keyboard users can reach Open PDF and Signature Library; no document, draft, recent file, or stale harness panel is restored. The focused regression suite must pass, the full
suite must remain green when shared code changed, and the GUI audit must record the visible result
and cleanup. A passing import or unit test without the stated user-visible behavior is insufficient.

## Evidence Record

Before checking this child in the parent, record the governing UI_SPEC requirement and
`docs/ui/main-workspace-no-document-exploratory.svg` plus
`docs/ui/main-workspace-document-open-exploratory.svg`, exact focused test command/result,
no-document launch and tab-order input sequence, observed frame state, evidence path and cleanup
result, and compatibility grep proof.

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
reach-through. Create tests/integration/test_gui_launch_no_document.py for the widget-state
walkthrough. The final interface must be exercised by tests/unit/test_qt_app_frame.py and that
integration test.
workspace surface. Any compatibility adapter retained temporarily must have a named consumer and a
retirement condition recorded in this plan.

Revision note: 2026-08-09 / Codex
Created as child ui_launch_no_document_execplan.md of the approved SPEC/UI_SPEC compliance breakdown.
