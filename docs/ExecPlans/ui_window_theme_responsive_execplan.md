# Window geometry, theme, and responsive baseline

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can use the application at minimum size, across themes/DPI/monitors, with safe persisted window behavior in the real FoliaSeal GUI. It is mapped to UI_SPEC section 12 and acceptance scenario 9. The
slice is intentionally one vertical path through the relevant persistent
model, application workflow, Qt surface, focused tests, and observable acceptance; it is not a
generic refactor.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are the frozen governing contracts.
- [x] docs/ExecPlans/ui_launch_no_document_execplan.md

## Progress

- [x] (2026-08-09) Audit the current implementation and write failing focused tests for the typed appearance/minimum-size baseline.
- [x] (2026-08-09) Implement the smallest complete typed settings and Qt frame baseline.
- [ ] (2026-08-09) Remove migrated compatibility or phase3 product cruft whose retirement condition is met.
- [x] (2026-08-09) Run focused, regression, and offscreen Qt validation; record evidence and clean up.
- [ ] (2026-08-09) Update relevant architecture/status documentation, complete geometry/restart/responsive follow-up slices, then commit the whole child outcome.

## Surprises & Discoveries

- Observation: window settings and geometry persistence are currently owned by the frame/settings
  boundary, so responsive and restart behavior must be tested there instead of in child widgets.
  Evidence: the live source paths and focused tests listed below are the audit baseline.
- Observation: the current frame has no close-event or shutdown persistence seam, so this loop can
  safely implement only typed appearance mode and minimum-size initialization; geometry restore,
  monitor clamping, Library sizing, and rail persistence need later lifecycle slices.
  Evidence: `QtAppFrameAdapter.launch()` retains the frame locally and calls `exec()` without a
  frame shutdown hook; `FoliaSealAppFrame` previously set only its title before this slice.

## Decision Log

- Decision: honor SPEC.md product scope, SCHEMAS.md persistent-object semantics, and UI_SPEC.md interaction wording in that order.
  Rationale: the repository explicitly defines those authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep this change limited to one observable window geometry, theme, and responsive baseline outcome.
  Rationale: narrow commits make GUI regressions and recovery auditable.
  Date/Author: 2026-08-09 / Codex
- Decision: Loop 3 is bounded to typed `appearance_mode` (`system`, `light`, `dark`), safe invalid
  fallback to `system`, and the main-frame 1100x700 minimum with UI-chrome palette application.
  Rationale: these behaviors have existing frame/settings seams and can be proven offscreen without
  inventing a premature geometry persistence lifecycle.
  Date/Author: 2026-08-09 / Codex

## Outcomes & Retrospective

The baseline slice is implemented but this child remains open: a user receives a 1100x700 logical
minimum frame and can select a typed System/Light/Dark preference in Application Settings; the
selection persists through AppSettings and invalid modes safely fall back to System. Focused
schema/storage, frame, and offscreen Qt checks prove the baseline, including preservation of the
current native accent role while UI surface/text roles change. Geometry persistence, monitor clamping,
Library minimums/columns, rail width, DPI rerender, and toolbar overflow remain explicitly deferred
to later lifecycle and responsive slices.

## Context and Orientation

The relevant code is app_frame.py; app settings schemas/storage; Qt geometry/palette setup; settings tests. FoliaSeal is a Python/Qt Linux PDF signing application. The
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

Own the canonical AppSettings UI keys and migration: appearance mode, main-window geometry and
maximized state, signing-rail divider, Library geometry, Library columns, last catalog, and sort.
Enforce the 1100x700 main and 1000x650 Library
minimums, remembered geometry/rail width, System/Light/Dark palette selection, high-DPI scaling,
monitor clamping, and non-wrapping toolbar behavior. Do not let PDF or appearance colors follow the app palette. Loop 3 establishes only the typed appearance/minimum-size baseline; add typed seams where the current code passes raw widget internals or compatibility
kwargs. Preserve the public frame/workspace contract while migrating consumers, then delete the
old path once focused tests prove no callers remain. Keep user-facing terminology from UI_SPEC.md,
not schema/backend names. Add typed AppSettings keys for geometry and Library preferences, write a
before/after serialized fixture, and prove old settings are read or deliberately rejected with a
clear fallback before wiring the widgets. Reconcile `linux_packaging_channel` with SCHEMAS.md as
either implementation metadata or an explicit removal/rejection; do not create a second persistence schema.

## Milestones

Milestone 1 adds the typed appearance key and fallback tests. Milestone 2 wires theme and the
1100x700 minimum through the frame. Later milestones must add a close-event-owned geometry/restart
seam before claiming persistence, scaling, Library, rail, or toolbar acceptance.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e 'setMinimumSize|appearance_mode|AppSettings|geometry|theme' src/foliaseal/presentation/qt/app_frame.py src/foliaseal/infra/config
    .venv/bin/pytest -q tests/unit/test_app_settings_storage.py tests/unit/test_qt_app_frame.py
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
walkthrough. Record appearance/minimum-size inputs, observed frame state, evidence path, and cleanup
result; the bounded timeout is only a lifecycle check.

## Validation and Acceptance

Acceptance for Loop 3 is behavioral for the baseline: typed System/Light/Dark settings round-trip with
invalid-value fallback, the real frame enforces a 1100x700 logical minimum, and palette changes are
limited to Qt UI chrome while rendered PDF/appearance content remains data-driven. Geometry/restart,
monitor, Library, rail, DPI, and toolbar acceptance remains open to its later slices. Focused tests,
the full suite, and offscreen Qt evidence must remain green with clean teardown.

## Evidence Record

Before checking this child in the parent, record the governing UI_SPEC requirement, exact focused
test command/result, appearance/minimum-size input sequence and observed frame state, evidence path,
cleanup result, serialized settings result, and compatibility grep proof. Loop 3 evidence explicitly
does not claim restart geometry or Library/rail persistence.

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
reach-through. Create `tests/unit/test_qt_app_frame_responsive.py` for offscreen resize/DPI cases;
the final interface must be exercised by tests/unit/test_app_settings_storage.py,
tests/unit/test_qt_app_frame.py, and that new test file.
workspace surface. Any compatibility adapter retained temporarily must have a named consumer and a
retirement condition recorded in this plan.

Revision note: 2026-08-09 / Codex
Created as child ui_window_theme_responsive_execplan.md of the approved SPEC/UI_SPEC compliance breakdown.
