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
- [ ] (2026-08-10) Complete the full UI_SPEC nested Library detail-pane experience and commit that follow-up slice.

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

## Decision Log

- Decision: obey SPEC.md, SCHEMAS.md, and UI_SPEC.md in that precedence order.
  Rationale: these are the repository's explicit authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep the slice limited to one user-visible appearance editor transaction and nested navigation outcome.
  Rationale: narrow changes are independently testable and recoverable.
  Date/Author: 2026-08-09 / Codex

## Outcomes & Retrospective

The bounded slice is implemented. `AppearanceProfileEditorDialog` reuses the existing
`QtVisibleSignatureSetupForm` appearance controls, opens from Library Create/Edit without an
active document, and persists through `SaveAppearance.appearance_profile_id` so renaming an edited
profile preserves its stable reference. Cancel leaves the catalog unchanged. The implementation is
intentionally modal; UI_SPEC's nested breadcrumb/detail-pane navigation, labeled sample preview,
reason/location defaults, dirty-detail prompts, and active-placement invalidation prompts remain
open follow-up work.

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

Move reusable Appearance editing into the Library detail pane with content-first controls, synthetic
sample preview labeled as sample, breadcrumb navigation, and suspended parent preset draft. The
bounded prerequisite now exists as a document-independent modal editor: it provides the typed
Save/Cancel transaction and stable-id persistence seam without silently applying or closing a parent
document draft. The remaining nested detail-pane and preview behavior must be implemented as a
separate follow-up rather than hidden behind the modal adapter. Add or preserve typed application
and public Qt-port boundaries rather than reaching through private widgets. Keep schema and
terminology aligned with the frozen documents. When a legacy path is replaced, prove its callers
are migrated before deleting it.

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

    rg -n -e 'Save|Cancel|Appearance|preview' src/foliaseal/presentation/qt/signing_workspace_refinement_dialog.py src/foliaseal/presentation/qt/visible_signature_setup_form.py
    .venv/bin/pytest -q tests/unit/test_qt_visible_signature_setup_form.py tests/unit/test_reusable_signing_models.py tests/unit/test_signature_preview_lifecycle.py
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
walkthrough. The bounded slice evidence is `tests/unit/test_qt_app_frame_profile_library.py` and
the offscreen Qt regression suite; the exact input sequence is create/edit from the Library's
Appearances catalog, change signer-label/name, Save or Cancel, and verify catalog identity/state.
Record the exact input sequence, widget state, expected observation, evidence path, and cleanup
result; the bounded timeout is only a lifecycle check.

## Validation and Acceptance

Acceptance for this bounded slice is behavioral: creating or editing an Appearance from the
document-independent Library surface writes only after Save, preserves stable identity on edit,
and leaves the previous persisted state unchanged on Cancel. The full nested behavior remains open:
creating an Appearance from a suspended preset must return to that editor with the reference attached
only after Save, and Cancel at either level must preserve the previous persisted state. Focused tests
must pass, shared-code changes must leave the full suite green, and the GUI audit must record the
visible result and cleanup.

## Evidence Record

Before checking this child in the parent, record the governing UI_SPEC requirement, exact focused
test command/result, GUI input sequence and observed nested-editor state, evidence path and cleanup
result, and compatibility grep proof.

Record the contributing UI_SPEC scenario ID(s) and either the owning SVG path or an explicit
"no SVG" decision alongside the evidence row.
Also record the exact focused test node and expected result (`N passed`); when the slice adds a new
contract, record that the test was red before implementation and green afterward.

Bounded evidence (2026-08-10):

- `.venv/bin/pytest -q tests/unit/test_qt_app_frame_profile_library.py tests/unit/test_reusable_signing_objects.py` — 20 passed.
- `.venv/bin/pytest -q tests/unit/test_qt_app_frame.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_visible_signature_setup_form.py` — 157 passed.
- The Appearances catalog exposes Create appearance and Edit appearance; the modal editor works
  without an active document; Save creates/renames the profile and preserves its stable ref; Cancel
  leaves the previous catalog entry unchanged.
- Process audit after Qt tests showed no FoliaSeal/PySide6/pytest processes or owned temporary
  dialogs. Display-backed xcb acceptance remains unavailable and is not claimed here.
- Remaining gaps: nested breadcrumb navigation, labeled sample preview, suspended preset return,
  reason/location defaults, dirty prompts, and active-placement invalidation.

## Idempotence and Recovery

Use temporary configuration and sibling output paths. If work fails halfway, preserve user PDFs and
drafts, update Progress with completed/remaining work, clean owned processes and artifacts, and
retry from the recorded state. Do not resurrect removed compatibility paths.

## Artifacts and Notes

Record concise output, focused screenshots or JSON under ignored artifacts/when useful, and exact
changed files. Never commit private keys, passwords, generated PDFs, or machine-local absolute paths.

## Interfaces and Dependencies

Use the existing typed application workflows, schema models, persistence stores, and public Qt frame
or workspace ports. Create tests/unit/test_qt_appearance_editor_transaction.py for nested Save/Cancel
behavior. The final behavior must be exercised by tests/unit/test_qt_visible_signature_setup_form.py,
tests/unit/test_signature_appearance_models.py, and that new test. Any temporary adapter must
name its remaining consumer and retirement condition in this plan.

Revision note: 2026-08-09 / Codex
Created as a dependency-ordered child of the approved SPEC/UI_SPEC compliance breakdown.
