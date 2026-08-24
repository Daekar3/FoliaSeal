# Consolidate document-review copy actions and restore signing-rail usability

This ExecPlan is a living document and must remain self-contained under
`/home/daekar/.codex/skills/write-execplan/PLANS.md`. It is a focused presentation-and-workflow
behavior slice. The implementation must update this file at every stopping point and must not be
declared complete from unit tests alone.

## Purpose / Big Picture

The installed-package human review found that the document-review area makes several common actions
hard to understand at the supported default window size. Two copy controls describe overlapping
ideas, the empty signature-review state consumes space while presenting a confusing disabled selector,
the fixed right rail hides signing setup behind an unhelpful scroll region, and the output-path action
sounds like an implementation detail rather than a clear save decision.

After this slice, a user opening an unsigned PDF will see one obvious way to copy selected PDF text,
will understand that the document simply has no embedded signatures, will be able to reach signing
preset/certificate/Appearance/Placement controls without fighting the rail layout, and will understand
when and where the signed PDF will be saved. A user who presses the primary signing action without
having confirmed a destination will receive the normal save dialog before signing begins; canceling
that dialog will leave the unsigned draft unchanged.

The result is demonstrated by focused Qt/application tests, a real offscreen 1100x700 rail check, a
fresh source-tree Cinnamon/X11 visual audit, a fresh package audit, and one installed-package review
of the corrected document-open state.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md`, `docs/UI_SPEC.md`, and `docs/SCHEMAS.md` are the governing documents. Product
  scope comes from `SPEC.md`, persistence semantics from `SCHEMAS.md`, and interaction realization
  from `UI_SPEC.md`.
- [x] `docs/ExecPlans/gui_hitl_defect_recovery_parent_execplan.md` owns the observed installed-GUI
  defect family and its final regression acceptance child.
- [x] `docs/ExecPlans/ui_installed_package_hitl_release_matrix_execplan.md` records the fresh package,
  the host installation, and the human observation that motivates this slice.
- [x] `docs/ExecPlans/gui_text_selection_mode_execplan.md` established the real user-facing text
  selection controls in the viewer toolbar and Edit menu; this slice must preserve those controls.
- [x] `docs/ExecPlans/gui_surface_layout_correction_execplan.md` established the fixed PDF-first
  topology, adjustable 280–640 pixel rail bounds, and the existing geometry-test seam.
- [x] The source-tree and package acceptance plans were rerun after implementation; their prior
  green results were not used as certification for this changed surface.

## Progress

- [x] (2026-08-23) Recorded the installed-package observation: no-document layout and keyboard access
  passed, but the first document-open review exposed duplicate-looking copy actions, an unclear empty
  signature state, excessive rail whitespace/scroll pressure, oversized action buttons, and ambiguous
  `Choose output...` wording.
- [x] (2026-08-23) Traced the current behavior to `signing_workspace_sidebar.py`,
  `signing_workspace_composition.py`, `signing_workspace_runtime.py`, `document_review.py`,
  `document_review_workspace.py`, `document_text_search.py`, and `signing_workspace_action_bridge.py`.
- [x] (2026-08-23) Decided that search-match copying and arbitrary selected-text copying are one
  user-facing V1 concept. The visible sidebar `Copy Result` action is therefore retired; the viewer
  toolbar/Edit `Copy selected text` path remains the sole primary copy affordance.
- [x] (2026-08-23) Explorer review found that removing the status floor also requires reconciling
  `UI_SPEC.md` SUR02 and the corresponding `ARCHITECTURE.md` ownership/constraint entries. The
  review further confirmed that restricted unsigned-document guidance must survive the new headline,
  populated selectors need an accessible name, the production bindings have no grid layout, and
  save-path cancellation must precede setup mutation.
- [x] (2026-08-23) Removed the obsolete sidebar search-copy and hidden selection-mirror widgets,
  removed the search `can_copy`/current-match-copy seams, and preserved search navigation/highlighting
  plus toolbar/Edit selected-text copy.
- [x] (2026-08-23) Replaced the unsigned review selector row with `No embedded signatures` guidance,
  preserved restricted-document explanation, added an accessible populated selector label, and
  collapsed empty review/status labels.
- [x] (2026-08-23) Recomposed the lower rail with content-driven status sizing, full-width primary
  actions, compact measured secondary rows, and a real 280-pixel minimum-width regression check.
- [x] (2026-08-23) Renamed the save action and made primary signing request Save As before setup
  mutation when no explicit path exists; cancellation and accepted-path reuse are covered by tests.
- [x] (2026-08-23) Reconciled `UI_SPEC.md` SUR02 and `ARCHITECTURE.md` with content-driven status
  sizing, current copy ownership, and explicit save-path entry. Two compliance explorers confirmed
  the fixed topology and identified/closed readiness, empty-row, restricted-state, and geometry gaps.
- [x] (2026-08-23) Full validation passed: `1607 passed, 20 skipped, 1 warning`. The bounded
  Cinnamon/X11 source audit passed through document review, setup, placement, signing, reopen/verify,
  and a second signature with screenshots under `/tmp/foliaseal-document-review-audit`; no owned
  FoliaSeal process remained afterward. A fresh pre-commit package audit also passed offline,
  private-install-root, and display-backed startup checks.
- [x] (2026-08-23) Added focused regression tests for copy retirement, restricted/unsigned/signed review
  states, 280-pixel rail geometry, readiness wording, chooser ordering, and cancel/accept behavior.
- [x] (2026-08-23) Rebuilt and audited the final package from implementation commit
  `29b27916fa0cbaa77d8faf3503701b559b074479`. Final `.deb` SHA-256 is
  `ade4ba16ac25b498c5bb048ebe20f06fff807cf34472ece46984881ef63abc68`.
  Offline extraction, isolated `dpkg --unpack`, Help/resources/dependency checks, and display-backed
  `qt_platform=xcb` startup all passed. An authenticated host installation of the same implementation
  preceded the final lint-only cleanup; host `dpkg --audit`, installed Help, and a disposable installed
  no-document frame under `/tmp/foliaseal-installed-final-audit` passed, with the process terminated
  cleanly. The final lint-only commit changed no runtime behavior and its exact package is covered by
  the fresh audit above.

## Surprises & Discoveries

- Observation: `Copy Result` copies the current case-insensitive search match span, not the query
  input. The match usually equals the query, but can preserve different source casing or PDF text
  extraction. A search highlight is not a text selection, so the toolbar copy action is technically
  separate today.
  Evidence: `QtPdfDocumentTextSearchEngine.search()` lowercases query/page text, obtains a selected
  span from `QPdfDocument`, and `DocumentTextSearchSession.current_copy_text()` returns that span.

- Observation: the application has no non-UI callers for `copy_current_document_text_match()` or
  `copy_current_text_match()` beyond the sidebar composition and their tests. The search state’s
  `can_copy` field exists only to enable that duplicate control.
  Evidence: repository search on 2026-08-23 found callers only in
  `signing_workspace_sidebar.py`, `signing_workspace_composition.py`, `signing_workspace_runtime.py`,
  `signing_shell.py`, and their focused tests.

- Observation: the empty signature selector is disabled because the fixture has zero embedded
  signatures, not because certificate or preset setup is unavailable. The review summary already
  knows this distinction, but the UI allocates a selector row that cannot contain a useful choice.
  Evidence: `build_document_review_summary(signature_count=0)` and selector rendering in
  `SigningWorkspaceSidebar.apply_document_review_workspace_state()`.

- Observation: the rail is a fixed-width right-hand surface whose root layout places the properties
  scroll area, document review, document text, signing actions, and status region sequentially. The
  status region currently reserves `STATUS_REGION_MINIMUM_HEIGHT = 200`, and several labels remain
  present even when their text is empty. This is why lower controls can consume the height needed by
  the signing setup above them.
  Evidence: `SigningWorkspaceSidebar.__init__()` and `_build_signing_action_controls()`.

- Observation: `Choose output...` is optional in the rail but the File → Save path already has a
  separate “choose if not explicit” behavior. The rail’s direct sign callback can reach the signing
  coordinator without first enforcing an explicitly user-confirmed destination.
  Evidence: `SigningWorkspaceActionBridge.choose_output_pdf_path()`, `has_explicit_output_pdf_path()`,
  `AppFrame._save_document()`, and `SigningWorkspaceActionBridge.submit_sign_request()`.

- Constraint: the production binding surface exposes horizontal layouts but no grid layout. Use
  measured horizontal rows, or add a typed grid binding and its test seam. At the legal 280-pixel
  minimum, the save-path action may need to remain full-width while only short recovery actions are
  paired.
  Evidence: explorer review of `QtSigningWidgetBindings` and the rail-layout tests.

- Constraint: output-path cancellation must occur before `_confirm_signing_request()` applies setup
  changes. Tests must prove cancel leaves setup, output path, dirty state, and submit/begin calls
  unchanged; an accepted path must be consumed exactly once without a duplicate chooser.
  Evidence: `SigningWorkspaceActionBridge.submit_sign_request()` and `_confirm_signing_request()`.

## Decision Log

- Decision: retire the visible sidebar `Copy Result` action and the search-copy-only state seam unless
  implementation discovers an unrecorded non-UI consumer.
  Rationale: search-match copying and arbitrary selected-text copying do not represent sufficiently
  distinct V1 user intents to justify two prominent copy buttons. Search remains fully usable for
  finding and navigating matches; selected-text copy remains available in the viewer toolbar and Edit
  menu.
  Date/Author: 2026-08-23 / Codex.

- Decision: remove hidden checkbox/button mirrors from the sidebar rather than preserving invisible
  compatibility widgets.
  Rationale: `gui_text_selection_mode_execplan.md` moved the user-facing controls to the toolbar/Edit
  command, and the hidden widgets now create duplicate state and layout plumbing. The runtime should
  render from explicit selection-mode state instead.
  Date/Author: 2026-08-23 / Codex.

- Decision: represent zero embedded signatures with compact explanatory text and no disabled selector
  row; show the selector only when one or more embedded signatures exist.
  Rationale: the selector is meaningful only for existing signatures. Removing the empty row improves
  hierarchy and preserves the distinction between document review and signing-material readiness.
  Date/Author: 2026-08-23 / Codex.

- Decision: remove the fixed 200-pixel status minimum and collapse empty status labels, while keeping
  full error/recovery text readable when a non-empty failure state requires it.
  Rationale: the human finding is vertical competition, not a need to shrink the PDF-first canvas or
  change the fixed rail topology. Content-driven sizing fixes the default successful path without
  hiding recovery information.
  Date/Author: 2026-08-23 / Codex.

- Decision: keep an optional explicit save-path command in the rail, rename it `Save signed PDF as...`,
  and make `Confirm and sign` invoke the same chooser when no explicit path has been confirmed.
  Rationale: users may choose a destination early, but the primary workflow must not require them to
  understand an implementation-oriented “output” term or silently sign to a suggested path. The
  existing overwrite/source-safety confirmation remains authoritative.
  Date/Author: 2026-08-23 / Codex.

- Decision: retain a full-width primary `Confirm and sign` button and use a two-column grid only for
  secondary actions whose labels remain readable at the 280-pixel rail minimum.
  Rationale: visual hierarchy must identify one next action, while compact secondary actions reclaim
  vertical space without changing the fixed right-rail topology.
  Date/Author: 2026-08-23 / Codex.

- Decision: update `UI_SPEC.md` SUR02 and the corresponding `ARCHITECTURE.md` ownership/constraint
  entries in this slice when the fixed status floor is removed; document the content-driven status
  region and primary-sign chooser behavior rather than leaving stale protected-region language.
  Date/Author: 2026-08-23 / Codex, after explorer review.

- Decision: preserve restricted-document explanation and add explicit signed/unsigned selector
  accessibility assertions. The selector and its label are hidden only when there are no embedded
  signatures; populated selectors retain an accessible name and enabled state.
  Date/Author: 2026-08-23 / Codex, after explorer review.

- Decision: keep a populated signature selector enabled even when the document contains one embedded
  signature. A single-item selector is still an explicit review surface and avoids encoding a hidden
  special case in accessibility behavior; the empty state alone hides the selector and its label.
  Date/Author: 2026-08-23 / Codex, after compliance review.

## Outcomes & Retrospective

Completed 2026-08-23. The installed document-open surface no longer presents duplicate copy concepts,
an empty disabled signature selector, or a rail whose lower status/actions hide signing setup. Focused
and full-suite validation passed (`1607 passed, 20 skipped, 1 warning`); the real source-tree X11 audit
completed signing, reopen/verify, and a second signature; and the final package from implementation
commit `29b27916fa0cbaa77d8faf3503701b559b074479` passed offline, isolated-install, and display-backed audits.
The audited implementation package was installed in the preceding authenticated session and its
no-document frame was captured and cleaned up; the final post-install commit was lint-only. Orca,
high-contrast, physical-DPI, monitor movement, and broader restricted/multi-page acceptance remain
separate release-matrix gates and are not claimed by this slice.

## Context and Orientation

FoliaSeal is a Python/PySide6 Linux desktop application for reviewing and signing PDFs. The central
viewer is the primary surface. A persistent right-hand signing rail contains reusable setup controls,
document review, text search, signing actions, and status. The rail is intentionally bounded between
280 and 640 logical pixels and must remain in that topology.

The sidebar is assembled by `src/foliaseal/presentation/qt/signing_workspace_sidebar.py` and wired to
the viewer by `src/foliaseal/presentation/qt/signing_workspace_composition.py`. Runtime callbacks and
state live in `src/foliaseal/presentation/qt/signing_workspace_runtime.py`. The document-review summary
is built in `src/foliaseal/application/document_review.py`; review/search/selection transitions are
owned by `src/foliaseal/application/document_review_workspace.py`. Output-path selection and signing
entry are coordinated by `src/foliaseal/presentation/qt/signing_workspace_action_bridge.py` and
`src/foliaseal/presentation/qt/app_frame.py`.

“Search match” means the text span found by the PDF search engine. “Selected text” means text the user
dragged across in the viewer after entering text-selection mode. “Explicit output path” means a path
the user accepted through the save dialog; a suggested filename seeded from settings is not treated as
user confirmation.

The governing UI contract requires a primary canvas, stable right rail, keyboard-accessible controls,
concise state/error guidance, and a user-chosen signed-output path. This slice must preserve those
contracts and must not add a second signing workflow, a general PDF-editing feature, or Wayland scope.

## Plan of Work

First remove the duplicate copy surface from the presentation boundary. Delete the sidebar `Copy Result`
button and its row participation. Remove the hidden checkbox, hidden `Copy Selection`, and hidden
`Clear Selection` widgets that were retained as state mirrors after the toolbar/Edit text-selection
surface was introduced. Replace any render wiring that depended on those widgets with explicit state
callbacks or the existing toolbar refresh callback. Then remove the now-unused search-copy callbacks,
runtime methods, shell-port members, `DocumentTextSearchSession.current_copy_text()`, and
`DocumentTextSearchState.can_copy` only after repository-wide caller and test inventory confirms they
are dead. Search navigation, match count, context, previous/next behavior, highlight overlays, and
toolbar/Edit selected-text copy must remain intact.

Next simplify the document-review empty state. In `document_review.py`, use the user-facing headline
`No embedded signatures` and concise detail that explains the PDF is unsigned and that a visible
approval signature can be placed. In the sidebar state renderer, show that compact message without a
disabled empty selector; when signature labels exist, show an accessible label and enabled selector
with the existing detail behavior. Add state tests for unsigned, signed, and restricted documents so
the selector is not accidentally hidden when it has real choices.

Then recompose the lower rail. Make status and detail labels visible only when they contain meaningful
text, remove the unconditional 200-pixel status minimum, update `UI_SPEC.md` SUR02 and
`ARCHITECTURE.md` to match, and set content-driven size policies that do not force the properties
scroll area to collapse at 1100x700. Keep long error/recovery text readable and test it explicitly.
Arrange `Save signed PDF as...`, `Open signed PDF`, `Verify again`, `Return to draft`, and `Open
preserved copy` in compact measured horizontal rows (or a newly bound grid) where labels remain
readable at 280 pixels. Keep `Confirm and sign` full-width and visually primary; keep the save-path
action full-width if pairing it would clip or elide its label.
Do not change the rail’s 280–640 bounds, the viewer/rail ownership boundary, or persistence behavior.

Finally correct the output-path workflow. Rename the rail button and its accessible name to
`Save signed PDF as...`. Ensure the rail’s primary sign callback checks
`has_explicit_output_pdf_path()` before `_confirm_signing_request()` or any setup mutation; if false,
invoke the existing save dialog and overwrite/source-safety confirmation first. A canceled dialog must
return without starting a transaction, changing setup or the draft output path, or marking the draft
dirty. An accepted path must be reused by the subsequent confirmation/sign operation without a second
chooser. Update readiness copy
so it says “Choose where to save the signed PDF...” when the path is not confirmed and “Review the save
path...” once it is.

## Milestones

The first milestone is copy-surface retirement. Focused application and Qt tests will prove that search
still navigates/highlights matches and that toolbar/Edit copy still copies a direct selection, while no
sidebar or hidden-widget path remains for search-match copying. The milestone is complete when the
dead seam inventory is clean and the focused tests pass.

The second milestone is rail composition. The empty signature state, compact search state, dynamic
status sizing, and secondary-action grid will be visible in an offscreen 1100x700 frame and at the
280-pixel rail minimum. The milestone is complete when setup controls retain usable widths and the
primary action remains reachable without a misleading scroll trap.

The third milestone is save-path behavior and release evidence. Focused tests will prove chooser
cancel/accept behavior from the primary sign action, then a source-tree X11 audit and fresh package
audit will run. The installed-package matrix will be resumed only after those AFK checks pass.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

Before editing, inspect the current callers and preserve unrelated work:

    git status --short
    rg -n "copy_current_document_text_match|copy_current_text_match|can_copy" src tests
    rg -n "Copy Result|Copy Selection|Save signed PDF|Choose output|STATUS_REGION_MINIMUM_HEIGHT" src tests

Implement the focused slice in the named modules, then run the focused tests:

    .venv/bin/pytest -q \
      tests/unit/test_document_text_search.py \
      tests/unit/test_document_review.py \
      tests/unit/test_document_review_workspace.py \
      tests/unit/test_signing_workspace_sidebar.py \
      tests/unit/test_qt_signing_workspace_runtime.py \
      tests/unit/test_qt_signing_action_boundary.py \
      tests/unit/test_qt_signing_action_coordinator.py \
      tests/unit/test_qt_signing_shell.py \
      tests/unit/test_qt_signing_workspace_composition.py \
      tests/integration/test_signing_rail_layout.py

Expected focused validation is zero failures. The new tests must cover removal of the duplicate copy
surface, unsigned/signed review rendering, 280-pixel layout usability, secondary-button geometry,
save-dialog cancellation, save-dialog acceptance, and no duplicate chooser when an explicit path exists.

Run repository checks:

    .venv/bin/ruff check src tests
    .venv/bin/python -m compileall -q src tests
    .venv/bin/pytest -q
    git diff --check

Run the bounded source-tree display audit in the supported Cinnamon/X11 session. It must use a fresh
temporary artifact root, capture the unsigned document-open state, exercise text search/selection, and
capture the rail at the supported minimum. Do not run Wayland and do not leave the GUI process open.

Build and audit a fresh package from the resulting commit using the existing
`src/foliaseal/build/debian_packaging.py` and `scripts/deb_package_audit.py` flow. Keep the `.deb`,
PyInstaller output, reports, and screenshots under one owned `/tmp/foliaseal-*` root and remove that
root after inspection. Do not commit generated packages or screenshots.

## Validation and Acceptance

The copy contract passes when search input still finds and navigates case-insensitive matches, the
viewer toolbar/Edit `Copy selected text` action copies a manually selected span, and no visible or
hidden sidebar `Copy Result`/selection-mirror controls remain. Search must not silently copy the query
input or lose its highlights.

The empty-review contract passes when an unsigned PDF says `No embedded signatures`, explains that the
document can receive a visible approval signature, and does not present a disabled empty selector.
An input containing embedded signatures must show an accessible selector and its detail state; a
restricted document must retain its restriction guidance.

The rail contract passes at 1100x700 and at the legal 280-pixel rail width when setup controls remain
reachable, empty search/status labels do not create large blank regions, secondary actions are readable,
and `Confirm and sign` remains the single primary action. Long failure/recovery text must remain
readable rather than be clipped or silently removed.

The save-path contract passes when the rail says `Save signed PDF as...`, an explicit path can be chosen
early, and pressing `Confirm and sign` without one opens the same chooser before signing. Canceling
leaves the unsigned draft and path unchanged; accepting a path proceeds to the existing confirmation
and signing flow; an already explicit path does not open a duplicate chooser. Source-overwrite and
existing-destination safety confirmations must remain unchanged.

Final acceptance requires the focused tests, full suite, Ruff, compileall, diff check, source-tree X11
audit, and fresh package audit to pass. The installed-package human matrix must then repeat the
document-open review and record whether the copy, empty-review, rail-density, and save-path findings
are resolved before continuing to Orca, scaling, monitor, fixture, and Help gates.

## Idempotence and Recovery

The code and tests are safe to rerun. Keep generated packages, PDFs, screenshots, and logs under one
owned temporary root. If a focused test fails, leave the failure visible, update `Progress` and
`Surprises & Discoveries`, and repair the smallest owning seam. Do not restore the retired duplicate
copy path merely to make an old test pass; update the test to the new single-copy contract.

If save-path behavior fails after the chooser opens, ensure no signing worker or temporary signed output
remains. A canceled chooser must never mutate the draft. If a display audit is interrupted, terminate
only the audit-owned FoliaSeal process, close audit-owned dialogs, remove the exact temporary root, and
verify no matching process/window remains. Never delete user certificates, configuration, unrelated
desktop windows, or shared Orca state.

## Artifacts and Notes

The durable evidence is the focused test output, full-suite summary, concise X11 screenshots/report,
package audit JSON, package commit/checksum, and the installed-package HITL observation. Generated
`.deb` files, PyInstaller directories, screenshots, PDFs, private keys, credentials, and machine-local
absolute paths are disposable and must not be committed.

The expected source ownership remains narrow:

    src/foliaseal/presentation/qt/signing_workspace_sidebar.py
    src/foliaseal/presentation/qt/signing_workspace_composition.py
    src/foliaseal/presentation/qt/signing_workspace_runtime.py
    src/foliaseal/presentation/qt/signing_shell.py
    src/foliaseal/presentation/qt/signing_workspace_action_bridge.py
    src/foliaseal/presentation/qt/app_frame.py
    src/foliaseal/application/document_review.py
    src/foliaseal/application/document_review_workspace.py
    src/foliaseal/application/document_text_search.py
    tests/unit and tests/integration files that cover those contracts

Do not mix certificate lifecycle changes, viewer rendering redesign, schema changes, new PDF fixture
families, Wayland support, or unrelated terminology cleanup into this slice.

## Interfaces and Dependencies

Use the existing `DocumentReviewWorkspaceState` and `SigningActionState` as the state boundaries; do not
introduce a second review model or a second signing action path. The viewer toolbar and Edit menu remain
the public text-selection interface. The action bridge remains the owner of save-dialog and overwrite
confirmation behavior. The rail remains the owner of layout and state projection, not PDF parsing or
certificate persistence.

The implementation may remove the search-copy-only methods and fields only after the caller inventory
in this plan is reproduced and all references are updated. It must retain the existing
`DocumentTextSearchState` query, match, context, navigation, and highlight semantics. It must retain
`has_explicit_output_pdf_path()` as the source of truth for whether the user confirmed a destination.

Revision note: 2026-08-23 / Codex: created after the installed-package acceptance session confirmed
that the no-document frame and keyboard reachability were good but the document-open surface had
duplicate copy affordances, an over-reserved right rail, a confusing empty signature selector, and
ambiguous output-path wording. The plan records the decision to retire the duplicate search-copy
surface and correct the remaining findings in one bounded presentation/workflow slice.

Revision note: 2026-08-23 / Codex: completed the implementation, two-wave compliance review,
full-suite validation, source-tree X11 audit, final package rebuild/audit, authenticated installation,
and installed no-document frame check. Updated governing UI/architecture documentation and recorded
the exact final commit/checksum; all audit-owned processes and temporary roots were cleaned.
