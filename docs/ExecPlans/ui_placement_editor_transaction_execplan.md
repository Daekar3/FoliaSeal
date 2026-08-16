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
- [x] (2026-08-10) Added red model/storage tests for v2 fields, top-left geometry, pinned/source-page
  validation, context-aware legacy conversion, and safe dropping of unconvertible legacy combined
  profile placement defaults.
- [x] (2026-08-10) Implemented the v2 placement model/codec, migrated SavePlacement and workflow
  profile writes, added PDF↔visible-page conversion helpers, and added an isolated transactional
  fixed-page editor with Save/Cancel and blank-page defaults.
- [x] (2026-08-10) Retired `page_selection_mode`, PDF-space `bottom_pt`, and
  `numeric_fine_tuning_enabled` from placement-profile output; active signing drafts retain their
  PDF-space `bottom_pt` contract at the document boundary.
- [x] (2026-08-10) Focused validation is green (211 tests including offscreen editor, Library
  reachability, coordinator, workflow, and storage coverage); full-suite validation is green after
  regression fixes (exact evidence is recorded below); no GUI process or temporary audit artifact
  is left behind.
- [x] (2026-08-10) Updated this plan, parent status, architecture notes, and compliance record;
  the bounded slice is ready for one coherent implementation commit.

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
- Observation: source-page context cannot be safely inferred at a reusable-object persistence seam.
  Evidence: `SavePlacement`, `PlacementProfile.from_defaults()`, and resolved-preset capture now
  reject missing context; blank-page creation supplies an explicit 612x792-point seed instead.
- Observation: the dedicated numeric editor is now production-reachable from the modeless Library,
  while pointer handles, drag/resize, keyboard placement, snapping, and undo/redo remain outside
  this bounded transaction slice.
  Evidence: Library create/edit callbacks and offscreen reachability tests landed; those interactions
  remain owned by `ui_pointer_signature_placement_execplan.md` and the later Library-topology child.

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
- Decision: require explicit source-page and page-number context whenever placement defaults are
  persisted or captured; only a deliberately blank-page editor seed may provide synthetic geometry.
  Rationale: guessed dimensions would silently corrupt reusable placement semantics.
  Date/Author: 2026-08-10 / Codex
- Decision: mount the numeric editor through Library create/edit actions without pretending this
  child implements the full SUR05 pointer interaction contract.
  Rationale: the transaction/schema boundary is independently testable; canvas handles, keyboard
  equivalents, snapping, undo/redo, and the three-column management topology need their own vertical
  slices.
  Date/Author: 2026-08-10 / Codex

## Outcomes & Retrospective

This slice delivered the fixed-page PlacementProfile v2 contract, explicit PDF/visible coordinate
conversion, transactional application state, and a numeric Qt editor reachable from Library create/
edit actions. Save/Cancel isolation, pinned state, restart round-trip, migration rejection/contextual
conversion, and offscreen Qt lifecycle evidence are covered. The implementation intentionally does
not claim pointer handles, drag/resize, keyboard placement, snapping, undo/redo, or the final
three-column Library; those remain explicit follow-on slices rather than hidden compatibility debt.

## Context and Orientation

The relevant code is src/foliaseal/presentation/qt/signing_workspace_refinement_dialog.py; reusable models; coordinate transforms/profile storage. FoliaSeal is a Python/Qt Linux PDF signing application. The
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

Adopted the frozen SCHEMAS.md v2 contract: serialize `page_number`, `source_page`,
`top_pt`, `left_pt`, `width_pt`, `height_pt`, and `pinned`; never add `page_selection_mode`,
`bottom_pt`, or `numeric_fine_tuning_enabled` to v2 output. Add a pure migration helper that accepts
the legacy mapping plus an explicit `PlacementProfileSourcePage` and one-based page number, converts
bottom-left to top-left using `top_pt = visible_height_pt - bottom_pt - height_pt`, and rejects a
legacy mapping when that context is absent. Reject unknown schema shapes with a clear validation
error. Update `PlacementProfile`, `PlacementProfileRect`, `SavePlacement`, catalog codecs, storage,
and all profile builders to use v2 values. Keep active document drafts in PDF-space and convert only
at the profile boundary.

Provided a fixed-page Placement editor from a current PDF or explicit blank-page context with direct
Page/Left/Top/Width/Height point fields, a visible source-page summary, and Save/Cancel. The editor
must own an immutable draft until Save; Cancel closes without changing the active signing draft or
preset. Store only schema-approved reusable geometry and compatibility metadata, never PDF identity
or content. Add or preserve typed application and public Qt-port boundaries rather than reaching
through private widgets. When a legacy path is replaced, prove its callers are migrated before
deleting it.

Milestone 1 implemented the v2 codec, contextual migration/rejection behavior, and every persistence
consumer. Milestone 2 built and tested the reusable application/Qt editor, then mounted it through
Library create/edit callbacks. The later pointer and Library-topology plans still own the richer
canvas and management interactions.

## Milestones

Milestone 1 resolved the SCHEMAS placement serialization decision and added migration fixtures for
`top_pt`, `page_number`, and `source_page`, including explicit rejection when context is absent.
Milestone 2 implemented the editor transaction and profile persistence with explicit source context.
Milestone 3 proved Save, Cancel, restart, blank-page editing, Library reachability, and no draft
mutation with focused and offscreen GUI evidence. Full pointer interaction remains deferred.

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

Acceptance is behavioral: a user can create and save a named, pinned or unpinned fixed-page
Placement from an explicit blank-page seed or a captured PDF context, edit it from Library, reopen it
after reload, and cancel without changing a live signing draft. Focused tests, shared-code regression
tests, Ruff, and offscreen Qt lifecycle evidence must be green. This child does not claim direct
pointer placement, keyboard movement/resizing, snapping, undo/redo, or the final three-column Library;
those are acceptance obligations of their owning children.

## Evidence Record

Evidence recorded for the completed slice:

- Governing requirements: `docs/SCHEMAS.md` PlacementProfile v2, `docs/UI_SPEC.md` §10 and SUR05;
  exploratory reference `docs/ui/placement-profile-editor-exploratory.svg` was reviewed. The
  numeric field subset is implemented; pointer/handle layers are explicitly deferred.
- Red/green proof: before implementation, the model test collection failed because
  `PlacementProfileSourcePage` and the v2 contract were absent; after implementation the focused
  command below passed.
- Focused command/result: `.venv/bin/python -m pytest -q tests/unit/test_reusable_signing_models.py
  tests/unit/test_reusable_signing_objects.py tests/unit/test_signature_preset_storage.py
  tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_draft_workflow.py
  tests/unit/test_coordinate_transform.py tests/unit/test_placement_editor.py
  tests/unit/test_qt_app_frame_profile_library.py tests/unit/test_qt_signing_shell.py
  tests/integration/test_placement_profile_editor.py` — `211 passed`.
- Offscreen lifecycle: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q
  tests/integration/test_placement_profile_editor.py` — passed; Save and Cancel were exercised,
  including pinned persistence and stable-id edit behavior.
- Full regression: `.venv/bin/python -m pytest -q` — `1230 passed, 20 skipped, 1 warning in 47.60s`.
- Static hygiene: `.venv/bin/python -m ruff check src tests` — `All checks passed`; `git diff --check`
  — clean.
- Migration: contextual v1 bottom-left payloads convert to visible top-left `top_pt`; context-free
  payloads and malformed non-boolean `pinned` values are rejected. Legacy combined profiles retain
  appearance and omit incompatible placement defaults rather than inventing page dimensions.
- Cleanup: the process audit showed no FoliaSeal/PySide6/pytest process owned by this slice and
  the temporary configuration root must be removed. Display-backed xcb evidence remains unavailable
  in this environment and is not claimed by the offscreen result.

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
or workspace ports. The slice introduces `PlacementProfileSourcePage`, top-left
`PlacementProfileRect`, `migrate_legacy_placement_payload`, `PlacementEditorState`/
`PlacementEditorSession`, and `PlacementProfileEditorDialog`; `SavePlacement` requires explicit
source-page and page-number context. The final behavior is exercised by the model, coordinate,
editor, Library, coordinator, workflow, storage, and offscreen integration tests listed in the
Evidence Record. Pointer interactions remain owned by
`ui_pointer_signature_placement_execplan.md`.
Any temporary adapter must
name its remaining consumer and retirement condition in this plan.

Revision note: 2026-08-09 / Codex
Created as a dependency-ordered child of the approved SPEC/UI_SPEC compliance breakdown.

Revision note: 2026-08-10 / Codex
Completed the bounded PlacementProfile v2/editor transaction slice, reconciled the architecture and
parent status, recorded compliance deferrals, and prepared the implementation for commit. The child
is complete for schema/persistence/numeric editing; pointer placement and final Library topology remain
open in their owning plans.
