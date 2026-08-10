# Document Signatures review surface

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can integrity-first Document Signatures review and jump/highlight behavior in the real FoliaSeal GUI. It is mapped to UI_SPEC SUR06, section 16, and acceptance scenario 5. The
slice is one vertical path through the relevant persistent model,
application workflow, Qt surface, focused tests, and observable acceptance.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are frozen governing contracts.
- [x] docs/ExecPlans/ui_document_lifecycle_recovery_execplan.md (bounded dirty-document replacement
  and close policy landed in `6c1ea9faf`; display-backed acceptance remains a parent gate, but this
  slice consumes only its typed lifecycle boundaries).
- [x] docs/ExecPlans/ui_pdf_navigation_zoom_pan_execplan.md (viewer navigation/fit contract landed
  in `2a7ff3d38`; this slice consumes its public page-navigation port).

## Progress

- [x] (2026-08-10) Audit the compact review card, PyHanko signature model, viewer overlay seam,
  app-frame command registry, and modeless-window pattern; the missing stable identity, geometry,
  unsigned-field, and lifecycle contracts are recorded below.
- [x] (2026-08-10) Add application, workspace, viewer, AppFrame, and offscreen integration tests for
  stable review items, signed/unsigned field projection, claimed versus trusted time, typed jump
  effects, modeless ownership, bridge routing, and close/replacement cleanup.
- [x] (2026-08-10) Implement the smallest complete model/application/Qt path: a modeless Document
  Signatures window, a View command, typed selection/jump/highlight, and integrity-first details.
- [ ] Retire migrated compatibility or phase3 product cruft only where this slice proves its callers
  are gone; do not rename unrelated evidence infrastructure.
- [x] (2026-08-10) Run focused, regression, and real offscreen Qt validation; clean processes and
  artifacts.
- [x] (2026-08-10) Update this plan and architecture/status documentation and complete the compliance
  review. Commit is the final handoff gate for this slice.

## Surprises & Discoveries

- Observation: signature review must present integrity states and claimed-versus-trusted time from
  document-review data, not infer them from certificate labels in the Qt surface.
  Evidence: the live source paths and focused tests listed below are the audit baseline.
- Observation: the current `DocumentSignatureReviewItem` is label-based and has no page, rectangle,
  stable identifier, unsigned-field state, or time fields; the sidebar selector therefore cannot
  navigate to a signature or represent an unsigned field.
  Evidence: `src/foliaseal/application/document_review.py` and
  `src/foliaseal/application/document_review_workspace.py` inspected on 2026-08-10.
- Observation: PyHanko exposes filled and empty signature fields through
  `pyhanko.sign.fields.enumerate_sig_fields(reader, filled_status=...)`; each field annotation can
  provide `/Rect` and `/P`, so geometry can remain a PDF-space application value without exposing
  PyHanko objects to Qt.
  Evidence: the installed PyHanko `enumerate_sig_fields` and `get_single_field_annot` source was
  inspected on 2026-08-10.
- Observation: the existing viewer already keeps manual selection and search overlays separate, so
  review highlights need a third public overlay rather than reusing either state.
  Evidence: `PdfViewerWidgetAdapter` exposes `set_text_highlight_overlay` and
  `set_text_search_highlight_overlay`; no review-specific method exists yet.
- Observation: the application frame already owns modeless Library lifetime and typed View actions,
  but its dynamic bindings do not yet expose list/layout/text widgets needed for a three-column
  review window.
  Evidence: `app_frame.py` and `app_frame_profile_library.py` inspected on 2026-08-10.

## Decision Log

- Decision: obey SPEC.md, SCHEMAS.md, and UI_SPEC.md in that precedence order.
  Rationale: these are the repository's explicit authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep the slice limited to one user-visible document signatures review surface outcome.
  Rationale: narrow changes are independently testable and recoverable.
  Date/Author: 2026-08-09 / Codex
- Decision: represent signed and empty signature fields in one immutable document-order tuple, with
  `kind`, stable `signature_id`, optional page/rectangle, integrity text, claimed time, trusted
  timestamp text, and drill-in detail.
  Rationale: UI_SPEC SUR06 requires one modeless list containing signed visible/invisible signatures
  and unsigned fields, while a shared typed item prevents the Qt surface from guessing PDF facts.
  Date/Author: 2026-08-10 / Codex
- Decision: derive a stable ID from the fully qualified PDF field name plus occurrence kind, not from
  the mutable display label or list index.
  Rationale: labels may change when signing order changes, while field names are the document identity
  available from PyHanko; the kind suffix prevents collisions in malformed documents.
  Date/Author: 2026-08-10 / Codex
- Decision: use conservative PDF-space annotation rectangles and a temporary review overlay that
  clears on navigation, document replacement, or dialog close; do not mutate signing placement or
  text-selection state.
  Rationale: selecting a review item is inspection-only, and a separate overlay preserves the
  independent search/selection contracts already implemented.
  Date/Author: 2026-08-10 / Codex
- Decision: keep the modeless window AppFrame-owned and replace it when the active workspace closes
  or changes, rather than retaining a stale PDF reference.
  Rationale: the UI topology allows at most one Document Signatures window and review data is tied to
  one PDF revision.
  Date/Author: 2026-08-10 / Codex

## Outcomes & Retrospective

The compact review card remains available, and this slice now adds the separate modeless inspection
surface. The application projection carries stable IDs, signed-visible/signed-invisible/unsigned
items, PDF-space geometry where available, explicit integrity status, claimed signing time, and a
trusted-timestamp value only when PyHanko validates one. The AppFrame owns one modeless dialog and
clears its independent review overlay on close or replacement. Focused and real offscreen tests are
green; broader parent-plan acceptance and the remaining V1 GUI corpus are still open.

## Context and Orientation

The relevant code is `src/foliaseal/application/document_review.py`,
`src/foliaseal/application/document_review_workspace.py`,
`src/foliaseal/presentation/qt/signing_workspace_review_bridge.py`,
`src/foliaseal/presentation/qt/viewer_widget.py`, and `src/foliaseal/presentation/qt/app_frame.py`.
FoliaSeal is a Python/Qt Linux desktop PDF signing application. The current review card is inside
the right signing rail and only selects embedded signed items by label. The new surface must be a
modeless child of the AppFrame, independent of signing-editor state, and must use an immutable
application projection of PyHanko facts. A PDF-space rectangle uses the repository's `PdfRect`
bottom-left coordinate convention; a modeless window is a non-blocking window that leaves the main
frame usable. V1 excludes tabs, printing, broad PDF editing, cloud workflow, enterprise trust
administration, and multiple pending signatures.

A compatibility surface is an adapter retained only for old callers. “phase3” names identify legacy
evidence/harness infrastructure and must not be introduced into ordinary product UI or new primary
contracts; production backend/evidence imports may be renamed only after a neutral migration proves
the old name is no longer required.

## Change Slice

Primary change class: behavior change. Allowed changes are the named modules, focused tests,
bounded ignored local evidence, and minimum truthful documentation. Do not mix unrelated evidence
rebaselines, V2 features, or packaging work.

## Plan of Work

First extend the application review projection. Add a `DocumentSignatureReviewItem` shape that carries
`signature_id`, `kind` (`signed_visible`, `signed_invisible`, or `unsigned_field`), field name,
optional zero-based page index and `PdfRect`, signer, integrity state/detail, claimed signing time,
trusted timestamp state, and drill-in detail. Use `enumerate_sig_fields` twice (filled and empty),
deduplicate by fully qualified field name, preserve document order using field/page order, and use
`get_single_field_annot` to read `/Rect` and `/P` when present. A missing annotation is still a valid
list item but cannot be jumped to. For signed items, use the existing local validation boundary and
format self-reported signing time separately from a validated timestamp token; never call a
certificate chain trusted merely because cryptographic integrity passed. Keep the old summary fields
and compact sidebar behavior compatible while migrating the selection callback to stable IDs.

Then add a typed workspace transition such as `select_review_item(signature_id)` that returns a
`jump_to_page_index`, `review_highlight_page_index`, and `review_highlight_rect` effect for visible
items, or a clear/no-jump effect for invisible or geometry-less items. The review bridge applies a
public viewer method `set_review_highlight_overlay(...)`; the viewer paints a temporary distinct
outline and clears it on page navigation, document replacement, and explicit close. It must not
replace signature-placement, text-selection, or search overlays.

Add `Document Signatures` to the View command registry only after the callback seam exists. Create a
new `document_signatures_dialog.py` with an AppFrame-owned modeless window: a stable catalog/list
column, a detail column with integrity-first status and claimed/trusted time rows, and a fixed close
footer. Include signed visible/invisible entries and unsigned fields in document order; selecting a
visible item invokes the typed workspace transition, focuses the main window, jumps to the page, and
temporarily highlights the annotation. The dialog refreshes when review state changes and closes when
the active workspace is replaced. Add or preserve typed application and public Qt-port boundaries
rather than reaching through private widgets. Keep terminology aligned with SPEC/UI_SPEC and delete
only compatibility paths whose callers are proven migrated.

## Milestones

Milestone 1 adds red application tests and deterministic fake PyHanko field/signature fixtures for
valid, changed, invalid, could-not-verify, empty-field, claimed-time, and trusted-timestamp states.
The projection must pass before any Qt code is added.

Milestone 2 wires the stable-ID workspace transition, public review overlay, and page-jump bridge;
unit tests prove the effect is independent from signing placement, text selection, and search.

Milestone 3 builds the modeless AppFrame-owned dialog and View command, then runs a real offscreen
Qt test that opens the dialog, selects a visible and an unsigned item, observes the detail/jump state,
and closes/replaces the document without leaving a window or overlay behind.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e 'signature|valid|timestamp|field|highlight|Document Signatures' src/foliaseal/application/document_review.py src/foliaseal/application/document_review_workspace.py src/foliaseal/presentation/qt/signing_workspace_review_bridge.py src/foliaseal/presentation/qt/viewer_widget.py src/foliaseal/presentation/qt/app_frame.py
    .venv/bin/pytest -q tests/unit/test_document_review.py tests/unit/test_document_review_workspace.py tests/unit/test_qt_viewer_widget.py tests/unit/test_qt_app_frame.py
    .venv/bin/pytest -q tests/integration/test_document_signatures_review.py tests/integration/test_gui_launch_no_document.py
    .venv/bin/ruff check src tests
    .venv/bin/pytest -q
    git diff --check

Run this bounded walkthrough from /home/daekar/FoliaSeal with an isolated configuration root:

    audit_root=$(mktemp -d /tmp/foliaseal-plan-audit-XXXXXX)
    timeout --foreground 30s env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf || test "$?" -eq 124
    ps -eo pid,cmd | rg 'FoliaSeal|foliaseal|PySide6|pytest' | rg -v 'rg ' || true
    rm -rf "$audit_root"
    test ! -e "$audit_root"

Expected evidence is the stated user-visible behavior plus a mandatory real offscreen Qt test or
display-backed walkthrough. Record the exact input sequence, widget state, expected observation,
evidence path, and cleanup result; a bounded timeout alone is only a lifecycle check and cannot prove
the dialog topology.

## Validation and Acceptance

Acceptance is behavioral: View → Document Signatures opens at most one modeless window without
blocking the main frame. Its list shows signed visible/invisible signatures and eligible empty
signature fields in document order; the detail view puts integrity and restrictions before signer
trust, distinguishes claimed signing time from a trusted timestamp, and uses plain-language
failure states. Selecting a visible item jumps the main PDF viewer to its page and applies a
temporary review highlight; selecting an invisible or geometry-less item does not invent a location.
Closing or replacing the document clears the dialog and review overlay without changing the signing
draft. Focused tests must pass, shared-code changes must leave the full suite green, and the GUI audit
must record the visible result and cleanup.

## Required Acceptance Cases

The review surface must render valid, changed-after-signature (including permitted changes), invalid,
could-not-verify, and unsigned states. It distinguishes claimed signing time from a trusted timestamp
and keeps certificate trust secondary to integrity.

## Evidence Record

Before completion, record the exact deterministic review fixture/test command and result, the GUI
status sequence for every integrity/time state and the jump/highlight observation, evidence path,
cleanup, and compatibility grep proof. Record whether the fixture exposes empty fields and a trusted
timestamp; if a dependency cannot produce one, keep that state explicitly marked unavailable instead
of claiming it.

Record the contributing UI_SPEC scenario ID(s) and either the owning SVG path or an explicit
"no SVG" decision alongside the evidence row.
Also record the exact focused test node and expected result (`N passed`); when the slice adds a new
contract, record that the test was red before implementation and green afterward.

## Idempotence and Recovery

Use temporary configuration and sibling output paths. If work fails halfway, preserve user PDFs and
drafts, update Progress with completed/remaining work, clean owned processes and artifacts, and retry
from the recorded state. Close any modeless dialog created by a test before quitting `QApplication`
and verify no FoliaSeal, PySide6, or pytest process remains. Do not resurrect removed compatibility
paths.

## Artifacts and Notes

Record concise output, focused screenshots or JSON under ignored artifacts/when useful, and exact
changed files. Never commit private keys, passwords, generated PDFs, or machine-local absolute paths.

2026-08-10 evidence: `.venv/bin/pytest -q tests/unit/test_document_review.py
tests/unit/test_document_review_workspace.py tests/unit/test_qt_app_frame.py
tests/unit/test_qt_signing_shell.py tests/unit/test_qt_viewer_widget.py
tests/unit/test_signing_workspace_session_port.py tests/integration/test_document_signatures_review.py
tests/integration/test_gui_launch_no_document.py` => `206 passed`; `.venv/bin/pytest -q` =>
`1215 passed, 20 skipped, 1 warning`. `.venv/bin/ruff check src tests` and `git diff --check` pass.
The offscreen integration test routes a visible and unsigned selection through the real
`DocumentReviewWorkspaceSession` and `SigningWorkspaceReviewBridge`, observes page-jump and review
overlay effects, then verifies dialog close and replacement cleanup leave no stale dialog or overlay.

## Interfaces and Dependencies

Use the existing typed application workflows, schema models, persistence stores, and public Qt frame
or workspace ports. Add or update these boundaries:

- `DocumentSignatureReviewItem` in `src/foliaseal/application/document_review.py` is the immutable
  application projection; it must not expose PyHanko dictionaries or Qt types.
- `DocumentReviewWorkspaceViewerEffects` in
  `src/foliaseal/application/document_review_workspace.py` carries an independent review page and
  rectangle effect, plus explicit clear semantics.
- `SigningWorkspaceReviewBridge` invokes public viewer methods only; it must never inspect the
  dialog's child widgets.
- `PdfViewerWidgetAdapter` and its scroll wrapper expose
  `set_review_highlight_overlay(page_index, highlight_rect)` and
  `clear_review_highlight_overlay()` while preserving existing overlay state.
- `FoliaSealAppFrame` owns one `DocumentSignaturesDialog` handle and a typed
  `show_document_signatures()` callback; closing/replacing the workspace disposes it.
- `QtAppFrameBindings` gains only the widget/layout types needed by the modeless surface, with
  optional defaults so existing fake-boundary tests remain valid.

The final behavior must be exercised by `tests/unit/test_document_review.py`,
`tests/unit/test_document_review_workspace.py`, `tests/unit/test_qt_viewer_widget.py`,
`tests/unit/test_qt_app_frame.py`, a new dialog unit test, and
`tests/integration/test_document_signatures_review.py`. Any temporary adapter must name its
remaining consumer and retirement condition in this plan.

Revision note: 2026-08-09 / Codex
Created as a dependency-ordered child of the approved SPEC/UI_SPEC compliance breakdown.
Revision note: 2026-08-10 / Codex
Fresh explorer review selected this child as the next highest-value slice after the committed
search UX. The plan was expanded with stable IDs, unsigned-field extraction, distinct time states,
modeless lifecycle, and real offscreen acceptance requirements so implementation cannot claim
Document Signatures compliance from the compact sidebar alone.
Revision note: 2026-08-10 / Codex
Implemented the model/application/Qt path, added explicit integrity-status classification and
bridge-routed offscreen acceptance, updated architecture documentation, and recorded focused/full
suite evidence. Broader parent compliance remains open; this child is ready for commit.
