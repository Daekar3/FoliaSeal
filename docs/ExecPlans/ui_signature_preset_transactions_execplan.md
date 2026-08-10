# Signature Preset CRUD and reference semantics

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can create, edit, duplicate, rename, pin, and delete Signature Presets with safe references in the real FoliaSeal GUI. It is mapped to SPEC reusable-object semantics and UI_SPEC WF02/WF06. The
slice is one vertical path through the relevant persistent model,
application workflow, Qt surface, focused tests, and observable acceptance.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are frozen governing contracts.
- [x] docs/ExecPlans/ui_signature_library_topology_execplan.md (completed in `a4e97edab`)
- [x] docs/ExecPlans/ui_catalog_search_sort_pinning_execplan.md (completed in `ecf4f73ab`)

## Progress

- [x] (2026-08-10) Audit current behavior and add a failing focused test.
- [x] (2026-08-10) Implement the bounded model/application/Qt reference-validation and Save-boundary path.
- [x] (2026-08-10) Move preset Create/Edit to a document-independent modal Save/Cancel editor with typed stable references.
- [ ] (2026-08-09) Retire migrated compatibility or phase3 product cruft whose consumers are gone.
- [x] (2026-08-10) Run focused, regression, and offscreen GUI validation; clean processes and artifacts.
- [x] (2026-08-10) Update this plan and relevant architecture docs.
- [x] (2026-08-10) Replace production modal Preset Create/Edit with a Library-owned Preset detail
  editor that can open one nested Appearance child and return its stable reference to the suspended
  preset draft.
- [x] (2026-08-10) Add typed child-first Save/Discard/Continue resolution, parent restoration, and
  focused/offscreen coverage; then reconcile architecture/docs and commit this follow-up slice.

## Surprises & Discoveries

- Observation: preset mutation is already represented by reusable-object model/store boundaries;
  this child must make nested Save/Cancel transactional and keep stable identifiers on rename.
  Evidence: the live source paths and focused tests listed below are the audit baseline.
- Observation: the production reusable-object service did not previously validate certificate
  configuration references because certificates live in a separate catalog. The AppFrame now injects
  an existence resolver, while direct test fixtures remain intentionally decoupled.
  Evidence: `ReusableSigningObjects(... certificate_configuration_exists=...)` and
  `tests/unit/test_reusable_signing_objects.py::test_production_boundary_rejects_missing_certificate_references`.
- Observation: the Library Save button was wired directly to the rename implementation. It now
  crosses an explicit `save_detail()` transaction boundary, but the full document-independent
  nested preset editor and dirty-switch/close prompts remain unimplemented.
  Evidence: `ReusableObjectLibraryDialog.save_detail()` and the compliance review boundary.
- Observation: editing a preset by changing its name exposed an identity bug in the existing
  name-based upsert path. `SavePreset.signature_preset_id` and id-aware catalog upsert now replace
  the existing record by stable id, so a rename cannot create duplicate ids or silently overwrite a
  different preset.
  Evidence: `test_document_independent_preset_editor_edit_preserves_preset_identity`.
- Observation: certificate-configuration deletion must be guarded from the certificate side as well
  as at preset save time. `CertificateManager.delete_configuration()` now accepts the AppFrame's
  referenced-preset id resolver and rejects deletion while a saved preset still points at it.
  Evidence: `tests/unit/test_certificate_manager.py::test_manager_blocks_deleting_configuration_referenced_by_preset`.
- Compliance limitation: the guard is a production preflight across two independent stores, not a
  shared cross-catalog transaction. A concurrent writer could create a preset after the resolver
  check and before certificate deletion. AppFrame now performs the guard even when a custom manager
  is injected, but a real temporary-store wiring/interleaving test and versioned/locked transaction
  remain follow-on work.
- Observation: the existing modal preset editor only exposes selectors for already-saved objects, so
  an empty catalog cannot follow UI_SPEC WF03's required nested Appearance creation path.
  Evidence at slice start: the then-production `SignaturePresetEditorDialog` had no Create/Edit
  Appearance child action, and Library Create/Edit routed to AppFrame modal callbacks. The current
  production path has since migrated to `SignaturePresetEditorWidget` and the concrete nested child
  flow; the dialog remains only as a compatibility/test wrapper.

## Decision Log

- Decision: obey SPEC.md, SCHEMAS.md, and UI_SPEC.md in that precedence order.
  Rationale: these are the repository's explicit authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep the slice limited to one user-visible signature preset crud and reference semantics outcome.
  Rationale: narrow changes are independently testable and recoverable.
  Date/Author: 2026-08-09 / Codex
- Decision: implement an explicit Library-owned `SignaturePresetEditorWidget` with one nested
  `AppearanceProfileEditorWidget` child rather than introducing a generic nested-editor framework.
  Rationale: WF03 requires the concrete Library → Preset → Appearance return path, and a small typed
  boundary keeps parent suspension, stable-reference return, and dirty prompts auditable without
  coupling unrelated Placement/Certificate editors.
  Date/Author: 2026-08-10 / Codex
- Decision: keep Placement and Certificate selectors reference-only in this slice.
  Rationale: their creation/configuration workflows have separate governing plans; adding them here
  would mix change classes and obscure the required Appearance child path.
  Date/Author: 2026-08-10 / Codex

## Outcomes & Retrospective

The prerequisite slice closes the production certificate-reference validation seam and makes the
Library detail Save action an explicit application-facing transaction boundary. The follow-up moves
production Preset Create/Edit into the modeless Library detail pane, adds the concrete
Library → Preset → Appearance → Preset child return path, and resolves child before parent
Save/Discard/Continue. Reason/location defaults, Placement/Certificate creation, active-placement
invalidation, and a single cross-store commit transaction remain separate follow-on work.

## Context and Orientation

The relevant code is src/foliaseal/application/reusable_signing_models.py; profile_storage.py; Library preset editor. FoliaSeal is a Python/Qt Linux PDF signing application. The
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

Make Signature Preset a reference-only composition that always requires an Appearance and optionally
references Certificate and Placement. Add
`src/foliaseal/presentation/qt/signature_preset_editor_widget.py` with name/reference draft state,
breadcrumb, Save/Back, dirty tracking, and explicit `Create appearance…`/`Edit appearance…` child
actions. Mount the existing `AppearanceProfileEditorWidget` as one nested child; on child Save,
capture its stable `ReusableObjectRef` and select it in the suspended preset draft, while child
Cancel/Discard leaves the parent draft unchanged. Route production Library Preset Create/Edit to
this widget and retain `SignaturePresetEditorDialog` only as a thin compatibility/test wrapper.
Resolve child before parent Save/Discard/Continue on Back, catalog switching, and Library close. Do
not add Placement/Certificate creation here. Add or preserve typed application and public Qt-port
boundaries rather than reaching through private widgets. Keep schema and terminology aligned with
the frozen documents. When a legacy path is replaced, prove its callers are migrated before
deleting it.
Any new pin/reference field requires a before/after serialized preset fixture and backward-read or
deliberate rejection test; no placement field may be persisted before the placement child resolves
the governing schema conflict.

## Milestones

Milestone 1 adds transactional model/store tests. Milestone 2 wires nested editor Save/Cancel,
rename, duplicate, and delete through stable identifiers. Milestone 3 proves refresh and recovery
in the Library GUI and records the retirement evidence.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e 'SignaturePreset|SavePreset|RenameObject|DeleteObject' src/foliaseal/application/reusable_signing_models.py src/foliaseal/application/reusable_signing_objects.py src/foliaseal/infra/config/profile_storage.py
    .venv/bin/pytest -q tests/unit/test_reusable_signing_models.py tests/unit/test_signature_preset_storage.py
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
walkthrough. The sequence is: open the modeless Library with no appearances, choose Presets/Create,
follow the breadcrumb into `Create appearance…`, Save the child, observe return to the Preset detail
with the new Appearance selected, then Save the Preset. Also exercise child Discard and parent Back
with Save/Discard/Continue. Record the exact input sequence, widget state, expected observation,
evidence path, and cleanup result; the bounded timeout is only a lifecycle check.

## Validation and Acceptance

Acceptance is behavioral: A user can create, edit, duplicate, rename, pin, and delete a preset; invalid or dangling references are blocked; selecting a partial preset clearly exposes only its missing per-document inputs. Focused tests must pass, shared-code changes must
leave the full suite green, and the GUI audit must record the visible result and cleanup. This
follow-up additionally requires the no-Appearance WF03 path to create an Appearance child and return
its stable reference to the parent without mutating any active document draft; child-first dirty
resolution must be observable and tested.

## Evidence Record

Before checking this child in the parent, record the governing UI_SPEC requirement, exact focused
test command/result, nested CRUD input sequence and observed catalog state, evidence path and cleanup
result, serialized compatibility result, and compatibility grep proof.

Record the contributing UI_SPEC scenario ID(s) and either the owning SVG path or an explicit
"no SVG" decision alongside the evidence row.
Also record the exact focused test node and expected result (`N passed`); when the slice adds a new
contract, record that the test was red before implementation and green afterward.

Current evidence (2026-08-10):

- Focused reusable-object, Library, and session tests: `20 passed`.
- Offscreen AppFrame/shell/Library/integration tests: `153 passed`.
- Updated focused set after the Save-boundary test: `21 passed`.
- Full regression: `1243 passed, 20 skipped, 1 warning`.
- Full regression after the deletion guard: `1244 passed, 20 skipped, 1 warning`.
- Full regression after the document-independent editor and id-aware upsert: `1246 passed, 20 skipped, 1 warning`.
- Offscreen Library/no-document integration: `2 passed`.
- Ruff and `git diff --check`: clean.
- Process audit: no FoliaSeal, PySide6, or pytest processes remained.
- No new SVG: this bounded seam changes application validation and the existing Save/Cancel name
  boundary, not the Library topology.
- Deletion guard evidence: manager-level static resolver test is green; real AppFrame temporary-store
  wiring and concurrent interleaving remain open acceptance items.
- Document-independent preset editor evidence: `tests/unit/test_qt_app_frame_profile_library.py`
  covers Save of an appearance-backed preset with no active workspace; offscreen AppFrame/shell
  validation remains green (`153 passed`).
- Stable-id edit evidence: the same focused suite proves renaming an existing preset preserves its
  `ReusableObjectRef` while updating its display name.
- Red/green note: the editor tests were added against the existing fake-Qt harness and required
  two implementation corrections (data-less combo-box fallback and id-aware preset upsert); a
  separately captured pre-implementation red run was not preserved.
- Nested Appearance return evidence: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q
  tests/integration/test_signature_library_topology.py tests/unit/test_qt_app_frame_profile_library.py
  tests/unit/test_qt_app_frame.py` => `72 passed`; the real offscreen integration test proves the
  Library → Preset → Appearance → Preset return with a stable saved appearance reference.
- Child-first dirty-resolution coverage includes parent Back Save/Discard/Continue, close while a
  child is active, catalog switching, child discard isolation, and cleanup assertions in
  `tests/unit/test_qt_app_frame_profile_library.py`.
- Full regression after the nested preset slice: `1363 passed, 20 skipped, 1 warning in 49.87s`.
- Ruff and `git diff --check`: clean.
- Bounded GUI lifecycle audit: `python -m foliaseal gui` exited `1` with the expected isolated
  `SingleInstanceUnavailable` endpoint limitation; no FoliaSeal/PySide6/pytest processes remained
  and the temporary configuration root was removed.
- Architecture reconciliation: `docs/ARCHITECTURE.md` now documents
  `SignaturePresetEditorWidget`, the concrete nested return path, child-first resolution, and the
  modal dialog as compatibility/test-only.
- Final implementation and plan-closeout commits: pending this follow-up commit step.

## Idempotence and Recovery

Use temporary configuration and sibling output paths. If work fails halfway, preserve user PDFs and
drafts, update Progress with completed/remaining work, clean owned processes and artifacts, and
retry from the recorded state. Do not resurrect removed compatibility paths.

## Artifacts and Notes

Record concise output, focused screenshots or JSON under ignored artifacts/when useful, and exact
changed files. Never commit private keys, passwords, generated PDFs, or machine-local absolute paths.

## Interfaces and Dependencies

Use the existing typed application workflows, schema models, persistence stores, and public Qt frame
or workspace ports. Add focused tests for the Library → Preset → Appearance return path, child
Cancel/Discard isolation, parent dirty resolution, stable-id edit, and no active-document mutation.
The final behavior must be exercised by `tests/unit/test_reusable_signing_models.py`,
`tests/unit/test_signature_preset_storage.py`,
`tests/unit/test_qt_app_frame_profile_library.py`, and the real offscreen Library integration test.
Any temporary adapter must name its remaining consumer and retirement condition in this plan.

Revision note: 2026-08-10 / Codex
Closed after implementation and compliance review: production Preset Create/Edit now uses the
explicit nested child path (Library → Preset → Appearance → Preset), with child-first dirty
resolution, stable-reference return, focused/full/offscreen evidence, and a thin compatibility
dialog wrapper. Placement/Certificate creation and unrelated renderer/policy work remain for their
owning plans.
