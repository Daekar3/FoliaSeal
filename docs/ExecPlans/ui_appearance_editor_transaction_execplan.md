# Appearance editor transaction and nested navigation

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can create, edit, preview, save, or cancel nested Appearance changes without mutating the parent draft in the real FoliaSeal GUI. It is mapped to UI_SPEC SUR04, WF03/WF06, and normative appearance SVG. The
slice is one vertical path through the relevant persistent model,
application workflow, Qt surface, focused tests, and observable acceptance.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are frozen governing contracts.
- [x] docs/ExecPlans/ui_signature_library_topology_execplan.md (bounded modeless Library and catalog callbacks are live)
- [x] docs/ExecPlans/ui_signature_preset_transactions_execplan.md (bounded document-independent preset editor is live)

## Progress

- [x] (2026-08-10) Audit current behavior and add focused Save/Cancel and stable-id tests.
- [x] (2026-08-10) Implement the document-independent Appearance create/edit model/application/Qt path.
- [x] (2026-08-10) Confirm no phase3 product-facing compatibility path was introduced; evidence-only phase3 modules remain outside this product slice.
- [x] (2026-08-10) Run focused, regression, and offscreen Qt validation; clean processes and artifacts.
- [x] (2026-08-10) Re-audit the current worktree and confirm the remaining gap is localized to `ReusableObjectLibraryDialog` and its Appearance editor composition; no product decision is pending.
- [x] (2026-08-10) Add a Library-owned Appearance detail/editor mode that preserves the master selection and suspends/restores the parent catalog/name draft.
- [x] (2026-08-10) Add a visible breadcrumb/back path, a sticky preview explicitly labeled as synthetic sample data, and typed Save/Discard/Continue prompts for dirty child state.
- [x] (2026-08-10) Prove nested Save/Cancel, parent restoration, child-widget cleanup, and real offscreen Qt mounting with focused tests.
- [x] (2026-08-10) Complete full-suite validation, final compliance review, documentation reconciliation, bounded GUI audit, and commit.

## Surprises & Discoveries

- Observation: appearance refinement is nested inside signing setup; this child must keep unsaved
  appearance edits isolated until an explicit Save intent and preserve Cancel as a no-op.
  Evidence: the live source paths and focused tests listed below are the audit baseline.
- Observation: the local collaboration runtime refused a fresh explorer after prior completed
  threads remained counted against its thread limit. The required pre-implementation and post-pass
  review was therefore completed as a checkout-grounded self-audit; no implementation blocker was
  inferred from the tooling limitation.
  Evidence: `collaboration.spawn_agent` returned `agent thread limit reached` after completed agents
  were interrupted; focused, regression, full-suite, Ruff, and process-cleanup checks were run here.
- Observation: a modeless nested editor must remove its child widget on every exit, not merely hide
  it, because repeated Create/Back cycles otherwise retain signal-connected editors in the detail
  layout.
  Evidence: the compliance review reproduced host-layout growth from 1 to 3 children before the
  fix; `test_nested_appearance_editor_removes_old_widget_on_reopen` now proves zero children after
  three cycles.
- Observation: a textual synthetic preview can satisfy the labeled/non-persistent contract while
  the final rendered preview remains a separate fidelity concern, provided it stays outside the
  scrolling controls and is explicitly labeled.
  Evidence: the widget keeps the preview label above a `QScrollArea`; the real offscreen test reads
  `Sample preview (synthetic data — never saved)` and the persisted `SignatureAppearance` contains
  no synthetic signer text.

## Decision Log

- Decision: obey SPEC.md, SCHEMAS.md, and UI_SPEC.md in that precedence order.
  Rationale: these are the repository's explicit authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep the slice limited to one user-visible appearance editor transaction and nested navigation outcome.
  Rationale: narrow changes are independently testable and recoverable.
  Date/Author: 2026-08-09 / Codex
- Decision: make `ReusableObjectLibraryDialog` own the nested Appearance editor session instead of opening another modal dialog.
  Rationale: UI_SPEC SUR03/SUR04 and WF03/WF06 require the detail column to be replaced by a breadcrumb-bearing child editor while the parent draft remains suspended; the existing modal `AppearanceProfileEditorDialog` cannot provide that topology.
  Date/Author: 2026-08-10 / Codex
- Decision: reuse the existing typed Appearance draft and `QtVisibleSignatureSetupForm` appearance controls, but compose only content/style controls in the Library detail pane.
  Rationale: this preserves schema and persistence policy while avoiding a second implementation of image/text fields; document placement and active-signature invalidation are outside this slice.
  Date/Author: 2026-08-10 / Codex
- Decision: represent dirty child state with an explicit session object/callback boundary rather than reading widget internals from `AppFrame`.
  Rationale: switching catalogs, Back, and closing the modeless Library must resolve Save, Discard, or Continue editing deterministically and remain testable without a live document.
  Date/Author: 2026-08-10 / Codex
- Decision: retain `AppearanceProfileEditorDialog` only as a wrapper around
  `AppearanceProfileEditorWidget` for direct/test callers while removing it from production
  AppFrame routing.
  Rationale: the nested Library path is the governing UI topology, but deleting the compatibility
  wrapper in the same behavior slice would unnecessarily break existing direct consumers; its
  retirement condition is no production or test caller outside the wrapper contract.
  Date/Author: 2026-08-10 / Codex

## Outcomes & Retrospective

The bounded prerequisite slice is implemented. `AppearanceProfileEditorDialog` now wraps the shared
`AppearanceProfileEditorWidget`, which reuses the existing
`QtVisibleSignatureSetupForm` appearance controls, opens from Library Create/Edit without an
active document, and persists through `SaveAppearance.appearance_profile_id` so renaming an edited
profile preserves its stable reference. Cancel leaves the catalog unchanged. The implementation is
intentionally modal; the current follow-up migrates the same transaction into the Library detail
pane. The follow-up closes the breadcrumb/detail-pane, labeled sample preview, suspended-parent,
dirty-child, and child-lifecycle gaps for production Appearance Create/Edit. It intentionally does
not claim reason/location defaults, preset-child return, active-placement invalidation, or final
renderer-fidelity validation.

## Context and Orientation

The relevant code is src/foliaseal/presentation/qt/signing_workspace_refinement_dialog.py; visible_signature_setup_form.py; reusable_signing_models.py. FoliaSeal is a Python/Qt Linux PDF signing application. The
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

Start at `src/foliaseal/presentation/qt/app_frame_profile_library.py`, where the modeless
`ReusableObjectLibraryDialog` already owns the three-column catalog and currently routes Appearance
Create/Edit to `AppFrame._run_appearance_profile_editor`. Replace that route with a Library-owned
child-editor state that stores the prior catalog/selection/detail snapshot, mounts the existing
typed Appearance draft controls in the detail column, and exposes a breadcrumb such as
`Signature Library / Appearances / <name>`. The parent selection must remain suspended while the
child is open. Back, catalog switching, and Library close must call one typed resolver that offers
Save, Discard, or Continue editing when the child is dirty; Continue leaves the child active, Save
commits through the existing `SaveAppearance` application boundary and restores the parent detail,
and Discard restores the pre-edit snapshot without changing the catalog.

The child detail must be content-first and include the existing appearance/content controls plus a
sticky preview area with an always-visible `Sample preview` label. Synthetic signer data is local
to the preview widget and must never enter the persisted draft. Do not add placement, document
identity, active-placement invalidation, image normalization, or fit-validation policy here. Add
public typed methods/callbacks for the Library session and keep `AppFrame` responsible only for
composition; do not reach through private Qt widget fields. Once all Appearance callers use the new
Library-owned path and tests prove the modal route is no longer needed, remove only dead compatibility
code made obsolete by this migration and record the removal.

## Milestones

Milestone 1 audited the named editor/session seams and added focused Save/Cancel and stable-id
coverage. Milestone 2 implemented isolated draft editing and explicit commit wiring through the
typed reusable-object boundary. Milestone 3 validated the modal editor offscreen and recorded the
remaining nested-pane/preview gaps for the next slice.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e 'Save|Cancel|Appearance|preview|breadcrumb|dirty' src/foliaseal/presentation/qt/app_frame_profile_library.py src/foliaseal/presentation/qt/appearance_profile_editor_dialog.py src/foliaseal/presentation/qt/visible_signature_setup_form.py
    .venv/bin/pytest -q tests/unit/test_qt_app_frame_profile_library.py tests/unit/test_qt_visible_signature_setup_form.py tests/unit/test_reusable_signing_models.py tests/unit/test_signature_preview_lifecycle.py
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
walkthrough. The exact input sequence is: open Manage Signature Library, choose Appearances, choose
Create or Edit, observe the breadcrumb and `Sample preview` label, change a field, choose Back and
verify the Save/Discard/Continue prompt, then Save or Discard and verify that the parent detail and
stable catalog identity are restored. Record the exact input sequence, widget state, expected
observation, evidence path, and cleanup result; the bounded timeout is only a lifecycle check.

## Validation and Acceptance

Acceptance for this slice is behavioral: creating or editing an Appearance from the modeless Library
replaces only the detail column, displays a breadcrumb and labeled synthetic preview, keeps the
parent selection suspended, and writes only after an explicit Save. Back, catalog switching, and
close resolve dirty child state with Save, Discard, or Continue; Discard leaves the previous
persisted state and selection unchanged; Save preserves stable identity on edit and restores the
parent detail. Focused tests must cover Create, Edit, Save, Cancel/Discard, dirty prompts, and
synthetic-preview non-persistence. Shared-code changes must leave the full suite green, and the GUI
audit must record the visible result and cleanup. Preset-child return, reason/location defaults,
active-placement invalidation, and renderer-fidelity validation remain explicitly outside this
slice and must not be claimed as complete here.

## Evidence Record

Before checking this child in the parent, record the governing UI_SPEC requirement, exact focused
test command/result, GUI input sequence and observed nested-editor state, evidence path and cleanup
result, and compatibility grep proof.

Record the contributing UI_SPEC scenario ID(s) and either the owning SVG path or an explicit
"no SVG" decision alongside the evidence row.
Also record the exact focused test node and expected result (`N passed`); when the slice adds a new
contract, record that the test was red before implementation and green afterward.

Bounded prerequisite evidence (2026-08-10):

- `.venv/bin/pytest -q tests/unit/test_qt_app_frame_profile_library.py tests/unit/test_reusable_signing_objects.py` — 20 passed.
- `.venv/bin/pytest -q tests/unit/test_qt_app_frame.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_visible_signature_setup_form.py` — 157 passed.
- The Appearances catalog exposes Create appearance and Edit appearance; the modal editor works
  without an active document; Save creates/renames the profile and preserves its stable ref; Cancel
  leaves the previous catalog entry unchanged.
- Process audit after Qt tests showed no FoliaSeal/PySide6/pytest processes or owned temporary
  dialogs. Display-backed xcb acceptance remains unavailable and is not claimed here.
- Remaining gaps: nested breadcrumb navigation, labeled sample preview, suspended preset return,
  reason/location defaults, dirty prompts, and active-placement invalidation.

Follow-up evidence (2026-08-10):

- Focused command/result: `.venv/bin/pytest -q tests/unit/test_qt_app_frame_profile_library.py tests/unit/test_qt_app_frame.py tests/integration/test_signature_library_topology.py` — 66 passed; `.venv/bin/pytest -q tests/unit/test_qt_app_frame_profile_library.py tests/unit/test_qt_visible_signature_setup_form.py` — 23 passed.
- UI_SPEC IDs and normative SVG: `SUR03`, `SUR04`, `WF03`, `WF06`; `docs/ui/appearance-profile-editor-exploratory.svg`.
- GUI input sequence: open the modeless Library, choose Appearances, choose Create, observe
  `Signature Library / Appearances / New appearance` and `Sample preview (synthetic data — never
  saved)`, edit the name, choose Back, select Discard, and verify the parent detail returns without
  a catalog entry. A real offscreen Qt test also saves `Offscreen appearance` and verifies the
  nested editor closes and the catalog contains the saved name. Repeated open/back cycles remove the
  child widget from the host layout.
- `.venv/bin/pytest -q` — 1357 passed, 20 skipped, 1 existing Pillow deprecation warning.
- `.venv/bin/ruff check src tests` and `git diff --check` — clean.
- Bounded lifecycle command with isolated `XDG_CONFIG_HOME`/`XDG_CACHE_HOME` exited 1 with the
  known `SingleInstanceUnavailable` endpoint error; no FoliaSeal/PySide6/pytest processes remained
  and the temporary audit root was removed. This environment limitation does not invalidate the
  offscreen Qt integration test and is not claimed as display-backed acceptance.
- Compatibility proof: production `app_frame.py` no longer imports or routes through
  `AppearanceProfileEditorDialog`; the remaining wrapper is only directly exercised by its focused
  compatibility tests and is documented with its retirement condition above.

Commit closeout: `3f571f9d2 feat(gui): add transactional appearance editor`; the worktree was clean
after the commit and `git show --check` passed.

## Idempotence and Recovery

Use temporary configuration and sibling output paths. If work fails halfway, preserve user PDFs and
drafts, update Progress with completed/remaining work, clean owned processes and artifacts, and
retry from the recorded state. Do not resurrect removed compatibility paths.

## Artifacts and Notes

Record concise output, focused screenshots or JSON under ignored artifacts/when useful, and exact
changed files. Never commit private keys, passwords, generated PDFs, or machine-local absolute paths.

## Interfaces and Dependencies

Use the existing typed application workflows, schema models, persistence stores, and public Qt frame
or workspace ports. Extend or create
`tests/unit/test_qt_appearance_editor_transaction.py` for nested Save/Cancel, dirty-resolution,
breadcrumb, and synthetic-preview non-persistence behavior. The final behavior must be exercised by
`tests/unit/test_qt_app_frame_profile_library.py`,
`tests/unit/test_qt_visible_signature_setup_form.py`,
`tests/unit/test_signature_appearance_models.py`, and that transaction test. Any temporary adapter
must name its remaining consumer and retirement condition in this plan.

Outcomes & Retrospective closeout (2026-08-10): The production Library now provides a complete
Appearance child transaction for the scoped UI_SPEC surface: nested detail replacement, breadcrumb,
sticky labeled synthetic preview, content-only controls, stable-id Save, typed dirty resolution,
parent restoration, and child-widget cleanup. Full validation reached 1357 passed and 20 skipped;
the bounded launch audit still reports the environment's isolated single-instance endpoint error,
with no leaked processes or temporary roots. The compatibility modal wrapper remains deliberately
thin and its retirement condition is documented. Preset-child suspension, reason/location defaults,
active-placement invalidation, and final rendered-preview fidelity are the next separate slices.

Revision note: 2026-08-10 / Codex
Reconciled after a fresh checkout review. The follow-up slice is now explicit about the
Library-owned nested detail mode, suspended parent state, dirty-resolution contract, labeled
synthetic preview, exact UI_SPEC/SVG evidence, and forbidden scope so the implementation can be
completed and audited without relying on prior conversation.
