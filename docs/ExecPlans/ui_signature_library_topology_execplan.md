# Signature Library window topology

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can open a modeless, document-independent, preset-first three-column Signature Library in the real FoliaSeal GUI. It is mapped to UI_SPEC SUR03, LAY04, WF06, and normative Library topology SVG. The
slice is one vertical path through the relevant persistent model,
application workflow, Qt surface, focused tests, and observable acceptance.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are frozen governing contracts.
- [x] docs/ExecPlans/ui_launch_no_document_execplan.md (no-document frame and one modeless Library
  entry point are implemented; final compatibility cleanup remains separately tracked).
- [x] docs/ExecPlans/ui_command_model_shortcuts_execplan.md (typed File/View/Settings foundations
  required by this window are implemented; unsupported command groups remain open in that child).
- [x] docs/ExecPlans/ui_window_theme_responsive_execplan.md (typed appearance and main-window
  geometry baseline are implemented; Library-specific persistence remains here).
- [x] docs/ExecPlans/ui_placement_editor_transaction_execplan.md (PlacementProfile v2 and the
  document-independent numeric editor landed in `705810fd2`).

## Progress

- [x] (2026-08-10) Audited the live `ReusableObjectLibraryDialog`, AppFrame ownership, catalog
  boundary, Qt bindings, and UI_SPEC SUR03/LAY04/WF06. The current form is modeless but single-column,
  uses a generic object selector, and routes create/edit through a document-bound refinement dialog.
  The replacement must remain modeless and document-independent while keeping
  `ReusableSigningObjects` as the only mutation authority.
- [x] (2026-08-10) Added the implementation boundary and initial red tests for a catalog-aware
  Library session, Presets-first navigation, searchable master list, and a detail column with
  fixed Save/Cancel controls.
- [x] (2026-08-10) Implemented `SignatureLibrarySession`, AppFrame `QSplitter` binding, and a
  modeless three-column Library with explicit catalog navigation, case-insensitive search, typed
  master rows, detail summaries, Save/Cancel footer, and no-document reachability. Existing placement
  create/edit remains reachable through its document-independent editor.
- [x] (2026-08-10) Initial compliance review found dead certificate navigation, non-transactional
  Save/Cancel wiring, and workspace-bound create/edit callbacks. Certificate row projection and
  isolated name-draft tracking were added; nested editors and catalog mutation gaps are now explicit
  deferrals.
- [x] (2026-08-10) Subsequent review confirmed the bounded claims and found one certificate-refresh
  defect; session selection now distinguishes certificate refs from reusable-object refs, and AppFrame
  refreshes the injected certificate catalog on every Library reopen.
- [x] (2026-08-10) Implemented the smallest complete model/application/Qt path for the bounded
  topology outcome; richer nested editors remain deferred to their owning children.
- [x] (2026-08-10) Retained only the test-binding compatibility fallback; no new product-facing
  compatibility or phase3 terminology was introduced. Further retirement remains tracked by the
  owning migration child where consumers still exist.
- [x] (2026-08-10) Ran focused, regression, offscreen GUI, static, and process-cleanup validation;
  no owned FoliaSeal/PySide6/pytest process or temporary audit root remains.
- [x] (2026-08-10) Updated this plan, the parent corpus, and architecture documentation; commit is
  the final handoff gate for this slice.

## Surprises & Discoveries

- Observation: the current Library surface is dialog-oriented and workspace-coupled; this child
  explicitly moves ownership to an AppFrame-owned modeless session with blank-page context.
  Evidence: the live source paths and focused tests listed below are the audit baseline.
- Observation: `ReusableSigningObjects.view()` already provides typed references and catalog-specific
  snapshots, so the Library can project catalog rows without creating a second persistence model.
  Evidence: `src/foliaseal/application/reusable_signing_objects.py` and its catalog tests.
- Observation: the current Qt binding surface has `QListWidget` but no Library-specific splitter or
  list adapter; adding those at the AppFrame binding boundary is smaller and more truthful than
  reaching through private Qt classes from the dialog.
  Evidence: `QtAppFrameBindings` and `QtAppFrameAdapter._load_bindings()` in `app_frame.py`.
- Observation: the old create/edit callback opens the document refinement dialog, which violates
  the document-independent Library contract when no PDF is open. This slice provides a catalog
  detail surface and keeps the already landed blank-page placement editor as the only direct editor
  mounted here; richer nested editors remain owned by their child plans.
  Evidence: `_open_reusable_object_editor()` delegates to `workspace.maintenance` and fails with no
  active workspace.

## Decision Log

- Decision: obey SPEC.md, SCHEMAS.md, and UI_SPEC.md in that precedence order.
  Rationale: these are the repository's explicit authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep the slice limited to one user-visible signature library window topology outcome.
  Rationale: narrow changes are independently testable and recoverable.
  Date/Author: 2026-08-09 / Codex
- Decision: make Presets the landing catalog and model the other three catalogs as explicit navigation
  choices, with a searchable master list and detail pane. Keep the existing typed catalog service as
  the mutation authority.
  Rationale: this directly satisfies SUR03/LAY04 without duplicating catalog invariants in Qt.
  Date/Author: 2026-08-10 / Codex
- Decision: make the Library session own selection and draft UI state, but keep persistence writes
  behind `ReusableSigningObjects`; Save/Cancel closes or discards only the active detail draft.
  Rationale: a modeless window must survive main-frame focus changes without leaking a partially edited
  object into the catalog.
  Date/Author: 2026-08-10 / Codex
- Decision: keep nested Appearance, Certificate, and full pointer editors out of this slice; the
  detail pane exposes truthful catalog summaries and routes supported placement create/edit through
  the existing document-independent placement editor.
  Rationale: those editors have separate governing contracts and mixing them would make this slice
  neither independently testable nor restartable.
  Date/Author: 2026-08-10 / Codex

## Outcomes & Retrospective

The bounded topology outcome now exists: the old single-selector form has been replaced by a
modeless three-column surface with an AppFrame-owned session, Presets-first navigation, typed search
rows, certificate projection, and an isolated name draft. The review also established the remaining
compliance boundary: nested document-independent editors, certificate mutations, Duplicate/Pin,
dirty close prompts, and Library preference persistence are not implemented by this child and must
remain visible as follow-on work.

## Context and Orientation

The relevant code is src/foliaseal/presentation/qt/app_frame_profile_library.py; reusable_signing_objects.py; profile stores. FoliaSeal is a Python/Qt Linux PDF signing application. The
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

Replace the current simple management form and `dialog.exec()`-oriented editor callbacks with an
AppFrame-owned `SignatureLibrarySession` and one modeless window handle. The session owns the active
catalog, selected typed reference, search text, and an isolated detail draft; it does not write files.
`ReusableSigningObjects` remains the sole persistence/mutation authority.

In `src/foliaseal/application/signature_library_session.py`, define the catalog enum, immutable row
  projection, and selection/search transitions. Sort rows by display name for this topology slice;
  persistent pin fields and pinned-first ordering remain owned by
  `ui_catalog_search_sort_pinning_execplan.md`. Filter case-insensitively over display name and detail
  text. In `app_frame_profile_library.py`, replace the
form layout with catalog navigation, a searchable `QListWidget` master list, and a detail pane whose
footer has Save and Cancel. Preserve Rename/Delete for supported refs, make the selected catalog and
draft explicit, and show a clear message when a component editor is not yet mounted.

Add `q_list_widget` and `q_splitter` bindings only at the AppFrame composition edge.
`FoliaSealAppFrame.show_reusable_object_library()` must reuse one modeless instance, refresh it on
reopen, and work with no active workspace. Placement create/edit continues to use the already landed
blank-page editor; appearance/certificate/preset nested editors remain follow-on child boundaries.
When the old selector path is replaced, preserve compatibility attributes only for existing tests or
callers and record their retirement condition; do not introduce new product-facing phase3 names.

## Milestones

Milestone 1 extracts the AppFrame-owned `SignatureLibrarySession` and defines refresh/close
lifecycle around `ReusableSigningObjects`. Milestone 2 replaces modal `dialog.exec()` with one
modeless three-column window and blank-page editor context. Milestone 3 proves no-document
reachability, catalog navigation/search, the bounded Save/Cancel name draft, and clean close in the
GUI. Nested no-document creation, restart preferences, and richer catalog mutations remain explicit
follow-on milestones in their owning children.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e 'ReusableObjectLibraryDialog|show_reusable_object_library' src/foliaseal/presentation/qt/app_frame_profile_library.py src/foliaseal/presentation/qt/app_frame.py
    .venv/bin/pytest -q tests/unit/test_reusable_signing_objects.py tests/unit/test_qt_app_frame.py
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

Acceptance for this bounded topology slice is behavioral: the Library opens modelessly from the
no-document frame and an active-document frame, uses Presets as its landing catalog, exposes
Appearances/Placements/Certificates navigation, filters typed rows case-insensitively, and presents
an isolated name draft whose Save commits a rename while Cancel discards it. Certificate rows are
projected from the injected catalog, but certificate mutation remains owned by the certificate child.
Nested Appearance/Preset editors, Duplicate, Pin, dirty-window prompts, Library geometry/preferences,
and no-document nested creation remain explicit follow-on acceptance items. Focused tests, Ruff, and
the full regression suite must remain green; the offscreen Qt test must close the dialog and main
window cleanly.

## Evidence Record

Evidence recorded for the bounded slice:

- Governing requirements: `docs/UI_SPEC.md` SUR03, LAY04, WF06 and
  `docs/ui/signature-library-presets-exploratory.svg`. The structural/topology subset is implemented;
  nested editors, catalog mutations, and preferences are explicitly deferred.
- Red/green proof: the new session test initially failed collection because
  `signature_library_session.py` did not exist; after implementation the focused suite passed.
- Focused command/result: `.venv/bin/python -m pytest -q tests/unit/test_signature_library_session.py
  tests/unit/test_qt_app_frame_profile_library.py tests/integration/test_signature_library_topology.py
  tests/unit/test_qt_app_frame.py tests/integration/test_gui_launch_no_document.py` — `51 passed`.
- Regression command/result: `.venv/bin/python -m pytest -q` — `1235 passed, 20 skipped, 1 warning`.
- Static hygiene: `.venv/bin/python -m ruff check src tests` — `All checks passed`; `git diff --check`
  — clean.
- GUI observation: offscreen integration opens the no-document frame, shows one modeless Library,
  verifies four catalog entries with Presets selected, a searchable master list, a detail column, and
  one `QSplitter`, then closes both windows. No FoliaSeal/PySide6/pytest process may remain.
- Certificate behavior: managed certificate rows are projected with subject/source details; mutation
  remains behind the certificate-management boundary until its owning child lands.
- Review correction: refreshing while a certificate row is selected no longer routes that typed
  certificate ref through `ReusableSigningObjects.resolve()`, and a reopened Library reloads the
  certificate catalog from its repository.

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

Use `SignatureLibrarySession` in `src/foliaseal/application/signature_library_session.py` for
catalog/search/selection/draft state, `ReusableSigningObjects` for appearance/placement/preset
queries and mutations, and the injected `CertificateCatalog` for managed certificate/configuration
rows. `ReusableObjectLibraryDialog` owns only Qt adaptation and AppFrame lifecycle; it must not
reimplement catalog invariants. `QtAppFrameBindings.q_splitter` and `q_list_widget` are the typed
composition edge for the three columns. The final interface is exercised by
`tests/unit/test_signature_library_session.py`,
`tests/unit/test_qt_app_frame_profile_library.py`,
`tests/integration/test_signature_library_topology.py`, and existing AppFrame/no-document tests.
Any compatibility adapter retained temporarily must have a named consumer and retirement condition
recorded in this plan.

Revision note: 2026-08-09 / Codex
Created as a dependency-ordered child of the approved SPEC/UI_SPEC compliance breakdown.

Revision note: 2026-08-10 / Codex
Revised during implementation to record the live topology audit, certificate-row and transaction-draft
corrections, exact evidence, the final validation gate, and the remaining nested-editor/catalog-
preference deferrals. The plan now describes the bounded outcome rather than implying full WF06
compliance.
