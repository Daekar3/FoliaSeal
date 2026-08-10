# Placement editor transaction and profile capture

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can edit and save fixed-page Placement values transactionally without storing PDF identity in the real FoliaSeal GUI. It is mapped to UI_SPEC SUR05, section 10, and normative placement SVG. The
slice is one vertical path through the relevant persistent model,
application workflow, Qt surface, focused tests, and observable acceptance.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are frozen governing contracts.
- [x] docs/ExecPlans/ui_launch_no_document_execplan.md (bounded launch landed in `d203e8605`; the
  parent checkbox was stale and is reconciled below).
- [x] docs/ExecPlans/ui_window_theme_responsive_execplan.md (main-frame geometry/theme baseline
  landed before this slice; rail/Library/DPI persistence remains deferred).
- [x] docs/ExecPlans/ui_document_signatures_review_execplan.md (review surface landed in
  `9a064669b`; this slice consumes only its AppFrame lifecycle boundary).

## Progress

- [x] (2026-08-10) Audit SCHEMAS v2, the live legacy placement model, refinement dialog, profile
  store, and Library dependency; the mismatch and migration boundary are recorded below.
- [ ] (2026-08-10) Add red model/storage tests for v2 fields, top-left geometry, pinned/source-page
  validation, and deliberate rejection of legacy payloads without migration context.
- [ ] (2026-08-10) Implement the v2 placement model/codec, migrate SavePlacement and all new profile
  writes, and add an isolated transactional fixed-page editor with Save/Cancel and blank-page input.
- [ ] (2026-08-10) Retire `page_selection_mode`, PDF-space `bottom_pt`, and
  `numeric_fine_tuning_enabled` from placement-profile output after all callers migrate; do not
  rename unrelated evidence/backend modules.
- [ ] (2026-08-10) Run focused, regression, and real offscreen Qt validation; clean processes and
  artifacts.
- [ ] (2026-08-10) Update this plan, parent status, architecture/schema notes, complete compliance
  review, and commit the whole slice.

## Surprises & Discoveries

- Observation: the live PlacementProfile currently stores rectangle and page-selection fields while
  SCHEMAS.md also describes source-page semantics; this child must resolve that contract before
  wiring Save/Cancel.
  Evidence: the live source paths and focused tests listed below are the audit baseline.
- Observation: legacy profiles do not contain page dimensions, so converting `bottom_pt` to the v2
  top-left `top_pt` coordinate is impossible without migration context.
  Evidence: the v1 payload has only `page_selection_mode` and four rectangle values; it has no visible
  page width/height or rotation. Context-free legacy payloads must therefore be rejected rather than
  silently guessed.
- Observation: the existing refinement dialog isolates a draft and uses the public
  `SigningSetupSession.save_placement_profile()` callback, but it edits a document-local PDF-space
  form rather than a reusable fixed-page model.
  Evidence: `signing_workspace_refinement_dialog.py` and `visible_signature_setup_form.py` inspected
  on 2026-08-10.

## Decision Log

- Decision: obey SPEC.md, SCHEMAS.md, and UI_SPEC.md in that precedence order.
  Rationale: these are the repository's explicit authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep the slice limited to one user-visible placement editor transaction and profile capture outcome.
  Rationale: narrow changes are independently testable and recoverable.
  Date/Author: 2026-08-09 / Codex
- Decision: make `PlacementProfile` schema version 2 the only serialized placement output, with a
  one-based fixed `page_number`, immutable visible `source_page`, and top-left `PlacementProfileRect`.
  Rationale: SCHEMAS.md and UI_SPEC section 10 define reusable geometry in visible-page coordinates;
  retaining v1 fields in new output would keep the GUI contract ambiguous.
  Date/Author: 2026-08-10 / Codex
- Decision: reject context-free v1 placement payloads with a clear migration error instead of
  inventing page dimensions or treating bottom-left values as top-left values. Provide an explicit
  migration helper that accepts source-page context for callers that can supply it.
  Rationale: preserving geometry is more important than pretending an unconvertible legacy value is
  safe, and the plan explicitly allows a deliberate-rejection path.
  Date/Author: 2026-08-10 / Codex
- Decision: keep the active PDF-space `VisibleSignaturePlacementDraft` contract and convert to/from
  v2 profile geometry only at the profile/editor boundary using visible page dimensions and rotation.
  Rationale: reusable profiles are document-independent, while the signing draft remains a PDF-boundary
  value.
  Date/Author: 2026-08-10 / Codex

## Outcomes & Retrospective

Audit/setup completed. The live model remains v1-shaped and no implementation or acceptance evidence
is claimed yet. The next milestones must prove v2 round-trip/migration behavior before the editor is
mounted, then prove Save/Cancel isolation and restart persistence in a real offscreen Qt surface.

## Context and Orientation

The relevant code is src/foliaseal/presentation/qt/signing_workspace_refinement_dialog.py; reusable models; coordinate transforms/profile storage. FoliaSeal is a Python/Qt Linux PDF signing application. The
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

Begin by adopting the frozen SCHEMAS.md v2 contract: serialize `page_number`, `source_page`,
`top_pt`, `left_pt`, `width_pt`, `height_pt`, and `pinned`; never add `page_selection_mode`,
`bottom_pt`, or `numeric_fine_tuning_enabled` to v2 output. Add a pure migration helper that accepts
the legacy mapping plus an explicit `PlacementProfileSourcePage` and one-based page number, converts
bottom-left to top-left using `top_pt = visible_height_pt - bottom_pt - height_pt`, and rejects a
legacy mapping when that context is absent. Reject unknown schema shapes with a clear validation
error. Update `PlacementProfile`, `PlacementProfileRect`, `SavePlacement`, catalog codecs, storage,
and all profile builders to use v2 values. Keep active document drafts in PDF-space and convert only
at the profile boundary.

Then provide a fixed-page Placement editor from a current PDF or blank-page context with direct
Page/Left/Top/Width/Height point fields, a visible source-page summary, and Save/Cancel. The editor
must own an immutable draft until Save; Cancel closes without changing the active signing draft or
preset. Store only schema-approved reusable geometry and compatibility metadata, never PDF identity
or content. Add or preserve typed application and public Qt-port boundaries rather than reaching
through private widgets. When a legacy path is replaced, prove its callers are migrated before
deleting it.

Milestone 1 is the foundation gate and may proceed after launch and typed settings: implement the
v2 codec, migration fixture, backward-read or deliberate-rejection test, and update every persistence
consumer. Milestone 2 builds and tests the editor as a reusable public Qt/application component with
an isolated host; the later Library plan mounts that component after this child completes. This
avoids a circular dependency while ensuring the Library consumes the already-settled schema rather
than redefining it.

## Milestones

Milestone 1 resolves the SCHEMAS placement serialization decision and adds migration fixtures for
`top_pt`, `page_number`, and `source_page` (or an explicit rejection path). Milestone 2 implements
the editor transaction and profile persistence only after that decision. Milestone 3 proves Save,
Cancel, restart, and no-PDF editing with focused and GUI evidence.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e 'Placement|page|left|top|width|height|Save|Cancel' src/foliaseal/presentation/qt/signing_workspace_refinement_dialog.py src/foliaseal/application/reusable_signing_models.py
    .venv/bin/pytest -q tests/unit/test_reusable_signing_models.py tests/unit/test_qt_visible_signature_setup_form.py
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

Acceptance is behavioral: A user can create and save a named Placement from a PDF or blank page, reopen it in the Library, and cancel without changing a live signing draft. Focused tests must pass, shared-code changes must
leave the full suite green, and the GUI audit must record the visible result and cleanup.

## Evidence Record

Before checking this child in the parent, record the governing UI_SPEC requirement and
`docs/ui/placement-profile-editor-exploratory.svg`,
exact focused test command/result, Save/Cancel input sequence and observed persisted fields, evidence
path and cleanup result, serialized migration result, and compatibility grep proof.

Record the contributing UI_SPEC scenario ID(s) and either the owning SVG path or an explicit
"no SVG" decision alongside the evidence row.
Also record the exact focused test node and expected result (`N passed`); when the slice adds a new
contract, record that the test was red before implementation and green afterward.

## Idempotence and Recovery

Use temporary configuration and sibling output paths. If work fails halfway, preserve user PDFs and
drafts, update Progress with completed/remaining work, clean owned processes and artifacts, and
retry from the recorded state. Do not resurrect removed compatibility paths.

## Artifacts and Notes

Record concise output, focused screenshots or JSON under ignored artifacts/when useful, and exact
changed files. Never commit private keys, passwords, generated PDFs, or machine-local absolute paths.

## Interfaces and Dependencies

Use the existing typed application workflows, schema models, persistence stores, and public Qt frame
or workspace ports. The final behavior must be exercised by tests/unit/test_reusable_signing_models.py,
tests/unit/test_qt_visible_signature_setup_form.py, and tests/unit/test_signature_preset_storage.py.
Any temporary adapter must
name its remaining consumer and retirement condition in this plan.

Revision note: 2026-08-09 / Codex
Created as a dependency-ordered child of the approved SPEC/UI_SPEC compliance breakdown.
