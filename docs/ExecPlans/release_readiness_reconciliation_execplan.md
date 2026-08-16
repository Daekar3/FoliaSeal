# Release-readiness and active-plan reconciliation

This ExecPlan is a living document and must be maintained in accordance with
`.agents/skills/write-execplan/PLANS.md`. It is an AFK child of
`docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md` and
`docs/ExecPlans/ui_product_support_and_release_execplan.md`.

## Purpose / Big Picture

After this slice, the active ExecPlan corpus distinguishes completed behavior
from stale publication markers and from genuine environment-dependent release
gates. The already-landed backend horizontal-fit, evidence projection,
safe-links/source-recovery, and Document Signatures behavior will be verified
from the current checkout, their stale checkboxes will be reconciled, and the
parent/release ledger will retain explicit open status for human accessibility,
physical DPI/monitor, packaged GUI, privileged installation, and final release
acceptance. This slice makes the project status trustworthy; it does not invent
a new GUI feature or claim Wayland support.

## Child Dependencies

- [x] `docs/SPEC.md`, `docs/UI_SPEC.md`, and `docs/SCHEMAS.md` are the governing
  contracts in that order.
- [x] `docs/ExecPlans/backend_horizontal_fit_followup_execplan.md` contains
  implemented behavior and focused tests; only its validation marker is stale.
- [x] `docs/ExecPlans/evidence_snapshot_projection_boundary_execplan.md` is
  implemented and committed as `4916fa839`; only post-commit reconciliation is
  open.
- [x] `docs/ExecPlans/ui_safe_links_external_changes_execplan.md` has source
  recovery and external-link behavior committed; its old navigation dependency
  marker is stale because the parent ledger already records navigation complete.
- [x] `docs/ExecPlans/ui_document_signatures_review_execplan.md` has implemented
  model/application/Qt behavior and green validation; only cleanup publication
  remains.

## Progress

- [x] (2026-08-16) Fresh explorer audit confirmed no unfinished
  dependency-ready behavior slice in these plans. Remaining open work is
  stale publication or genuine release/HITL/privileged evidence.
- [x] (2026-08-16) Verified each targeted plan's implementation and focused
  tests against the current source rather than historical counts. Backend,
  evidence, safe-links, and Document Signatures behavior all have live callers
  and current regression coverage.
- [x] (2026-08-16) Reconciled stale checkboxes and progress/retrospective
  wording in the four targeted plans and the parent/release ledger.
- [x] (2026-08-16) Ran the four targeted groups: backend `141 passed`, evidence
  `82 passed, 9 skipped, 1 warning`, safe-links `24 passed`, and Document
  Signatures `45 passed`; the full suite ran in four bounded batches for
  `1537 passed, 20 skipped, 1 warning`. Ruff, compileall, collection, and diff
  checks pass; no owned processes or temporary roots remain.
- [x] (2026-08-16) Explorer and architecture/documentation reviews returned
  GO. They found no source, contract, path, evidence-count, cleanup, or
  overclaim issue; the remaining release/HITL/privileged gates are intentional.
- [x] (2026-08-16) Committed as `f283cbcd5` (`docs: reconcile release
  readiness status`); the post-commit checkout and process cleanup are clean.

## Surprises & Discoveries

- The backend horizontal-fit plan still names removed `phase3_*` paths and an
  old 2026 test command, but the implementation now lives in neutral
  `signing_backend.py` and its tests. The plan must be corrected rather than
  merely checked off.
- The safe-links parent’s unchecked navigation dependency is inconsistent with
  both the parent compliance ledger and current AppFrame/session commands.
- A completed child’s “commit is the final handoff gate” wording is not proof of
  an uncommitted worktree. Git history and current tests are the authoritative
  evidence.
- V1 Linux acceptance targets Cinnamon/X11; Wayland validation is intentionally
  deferred to a later compatibility tranche. X11 is the supported current
  display evidence. Screen-reader/high-contrast, physical DPI/monitor,
  packaged GUI, privileged host installation, and final human release matrix
  remain open and must not be converted into AFK checkboxes.

## Decision Log

- Decision: reconcile only plans with current implementation evidence and leave
  genuine external gates open.
  Rationale: closing stale markers improves truthfulness, while claiming a
  display or privileged-install result without the required environment would
  violate SPEC/UI_SPEC evidence boundaries.
  Date/Author: 2026-08-16 / Codex
- Decision: update obsolete backend paths and commands to current neutral paths
  rather than reviving `phase3` nomenclature.
  Rationale: the current source has already migrated; plans must describe the
  checkout that actually exists.
  Date/Author: 2026-08-16 / Codex
- Decision: keep this as documentation/status reconciliation, with no source
  behavior changes.
  Rationale: a fresh source audit found no justified AFK behavior gap; changing
  code now would duplicate completed slices and increase regression risk.
  Date/Author: 2026-08-16 / Codex

## Outcomes & Retrospective

The reconciliation closed only stale publication markers: the backend plan now
uses neutral paths and current validation, the evidence projection records its
post-commit consumer scan, safe-links records the completed navigation
dependency, and Document Signatures records its compatibility audit. Current
focused groups total `292 passed, 9 skipped, 1 warning`; the full suite totals
`1537 passed, 20 skipped, 1 warning`. Explorer and architecture reviews both
returned GO. Human accessibility, physical DPI/monitor, packaged GUI,
privileged installation, final release acceptance, and Wayland remain open or
deferred by design. This reconciliation is committed as `f283cbcd5`; the
post-commit checkout and process cleanup are clean.

## Context and Orientation

The four targeted plans are historical children of the UI compliance parent.
Their current implementation evidence is in:

- `src/foliaseal/application/signing_backend.py` and
  `tests/unit/test_signing_backend.py` for horizontal fit;
- `src/foliaseal/presentation/qt/evidence_snapshot_projection.py` and its
  projection/harness/reporting tests;
- `src/foliaseal/application/document_safety.py`, viewer/session/AppFrame safe
  link paths, and source-change recovery tests;
- `src/foliaseal/application/document_review.py`, review workspace/bridge, and
  Document Signatures integration tests.

The product story remains open → review → reusable setup → placement → preview
→ sign/save → verify/reopen. No schema, CLI, JSON, artifact, or user-facing
product contract changes belong in this reconciliation slice.

## Change Slice

Primary change class: documentation/status reconciliation. Allowed files are
this plan, the four targeted child plans, `docs/ExecPlans/ui_product_support_and_release_execplan.md`,
`docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md`, and
`docs/ARCHITECTURE.md` if a current ownership statement is inaccurate. Generated
artifacts and package outputs are disposable and must not be committed.

## Plan of Work

1. Verify current implementations and focused test nodes with `rg`, focused
   pytest, and Git history. Record current counts; do not repeat stale counts
   from 2026-08-10 as if they were current.
2. In the backend plan, replace obsolete `phase3_*` paths with neutral current
   paths, mark the implemented validation complete, and record current focused
   evidence.
3. In the evidence projection plan, mark the post-commit scan/ledger closure
   complete with a current consumer/import scan and retain its historical
   implementation commit.
4. In the safe-links plan, mark the already-complete navigation dependency as
   reconciled and retain only the genuine compatibility/release closeout.
5. In the Document Signatures plan, record the compatibility audit result and
   current commit/validation state without claiming richer V2 drill-in.
6. Update parent/release status to point at this reconciliation and preserve
   open external gates. Record Wayland deferral consistently.
7. Run focused tests for all four areas, Ruff, compileall, the full suite in
   bounded batches if one monolithic invocation is unstable, `git diff --check`,
   and process/temp-root cleanup. Then obtain independent reviews and commit.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    git status --short --branch
    rg -n 'phase3_|phase3|LayoutRequest|compatibility|acceptance' src tests docs/ExecPlans/backend_horizontal_fit_followup_execplan.md docs/ExecPlans/evidence_snapshot_projection_boundary_execplan.md docs/ExecPlans/ui_safe_links_external_changes_execplan.md docs/ExecPlans/ui_document_signatures_review_execplan.md
    .venv/bin/pytest -q tests/unit/test_signing_backend.py tests/unit/test_visible_signature_layout_boundary.py
    .venv/bin/pytest -q tests/unit/test_evidence_snapshot_projection.py tests/unit/test_interactive_harness.py tests/unit/test_interactive_harness_reporting.py
    .venv/bin/pytest -q tests/unit/test_document_safety.py tests/unit/test_viewer_interaction_session.py tests/unit/test_qt_app_frame_workspace_open.py tests/integration/test_qt_pdf_link_inspection.py
    .venv/bin/pytest -q tests/unit/test_document_review.py tests/unit/test_document_review_workspace.py tests/integration/test_document_signatures_review.py
    .venv/bin/ruff check src tests
    .venv/bin/python -m compileall -q src tests
    .venv/bin/pytest --collect-only -q
    git diff --check

Run no Wayland command. Any bounded GUI check must use the supported X11 or
offscreen path, track owned PIDs, and remove its exact temporary root.

## Validation and Acceptance

Acceptance requires:

- each targeted plan describes current neutral source paths and current
  evidence, with stale checkboxes closed only where implementation is proven;
- no active source/test consumer is accidentally renamed or deleted by this
  docs-only slice;
- focused tests, full regression, Ruff, compileall, and diff checks pass;
- parent/release plans still leave human accessibility, physical DPI/monitor,
  packaged GUI, privileged installation, and final release acceptance open;
- the V1 Cinnamon/X11 target and later Wayland compatibility tranche are stated
  without making an external Mint maturity claim;
- the AT-SPI timeout is documented as a controlled session/bridge evidence
  limitation after normal, forced, Orca-active, and minimal-Qt comparison;
- no FoliaSeal/Qt/pytest process, dialog, or owned temporary root remains.

## Idempotence and Recovery

This slice is source-independent and safe to repeat. If a status claim cannot
be verified from current code/tests/Git history, leave it open and record the
missing evidence rather than closing it. Preserve unrelated dirty changes and
remove only exact disposable artifacts created by validation.

## Artifacts and Notes

Record exact focused/full results, scans, review decisions, and final commit in
this plan. Do not commit generated PDFs, certificates, package outputs,
screenshots, or machine-local absolute paths.

## Interfaces and Dependencies

This plan changes no runtime interface. It reconciles the existing application,
Qt, evidence, and document-review boundaries described by SPEC/UI_SPEC/SCHEMAS
and `docs/ARCHITECTURE.md`. Historical `phase3` names may be mentioned only as
migration context; new plan text must use current neutral paths.

Revision note: 2026-08-16 / Codex: created after a fresh explorer audit found
the remaining open markers were stale publication or external release gates,
not a current dependency-ready behavior defect.
