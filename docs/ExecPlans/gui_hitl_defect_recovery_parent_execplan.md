# Recover the installed GUI from observed HITL defects

This ExecPlan is a living document. It is authored under the requirements in
`/home/daekar/.codex/skills/write-execplan/PLANS.md`; that file is the governing plan-format reference
for this repository because FoliaSeal does not check in a separate `PLANS.md`.

## Purpose / Big Picture

The first installed-package human session proved that FoliaSeal can launch, open the disposable PDF,
expose its shell, and begin certificate and placement work, but it also exposed several failures that
prevent meaningful use: clipped certificate instructions, an undersized Appearance editor, a signing
rail that becomes unusably narrow, a wrong-password dead end, high CPU during placement, and a crash
from `Signing -> Adjust Placement`. This plan family turns those observations into reproducible tests,
small implementation slices, and a final installed-package acceptance pass.

After the family is complete, a user will be able to create signing material at the supported default
window size, recover from a wrong certificate password without losing the draft, edit and preview a
reusable Appearance in the Library, keep the document signing rail usable, and create/adjust/cancel/
undo a placement without a crash or runaway update loop. The result is demonstrated first by focused
offscreen tests and then by the installed Debian package in the real Cinnamon/X11 session.

The external HITL evidence is embedded here so a novice can proceed without needing the Downloads file:

- The default Create Certificate dialog clipped its introductory text until manually enlarged.
- The Display name field was not marked optional even though an empty value successfully fell back to
  Full name.
- The Appearance editor opened from Manage reusable signing objects too small for its controls and
  its preview did not visibly represent the selected appearance/image.
- The Import Certificate dialog is also undersized (267×284 in the live source-tree audit), uses the
  lowercase title `Import certificate`, and clips its introductory, inspection, and certificate-field
  copy through a dense form layout.
- Opening a document left the right signing pane too narrow until manually expanded.
- A wrong password for the selected certificate displayed an error but offered no apparent retry,
  reselect, or cancel recovery.
- Pointer placement worked but pegged one CPU core; the keyboard path was not discoverable.
- Choosing `Signing -> Adjust Placement` crashed the application.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md`, `docs/UI_SPEC.md`, and `docs/SCHEMAS.md` are the governing contracts. Product
  scope comes from `SPEC.md`, persistent object semantics from `SCHEMAS.md`, and interaction
  realization from `UI_SPEC.md`.
- [x] `docs/ExecPlans/ui_installed_package_hitl_release_matrix_execplan.md` defines the installed
  package and human-observation boundary; its ten scenarios remain open.
- [x] `docs/ExecPlans/ui_appearance_editor_transaction_execplan.md` and the existing reusable-object
  Library work provide the transaction and nested-editor seams consumed by Child 2.
- [x] Existing placement, rail-divider, and responsive-baseline work provides the seams consumed by
  Child 2 and Child 3; this family corrects observed regressions rather than redesigning the topology.
- [x] `docs/ExecPlans/gui_certificate_and_preset_recovery_execplan.md` passed its source-tree
  correction slice; the final regression child must still certify the installed package.
- [x] `docs/ExecPlans/gui_appearance_and_signing_rail_layout_execplan.md` passed its source-tree
  correction slice; the final regression child must still certify the installed package.
- [x] `docs/ExecPlans/gui_placement_interaction_stability_execplan.md` passed its source-tree
  correction slice; the final regression child must still certify placement behavior in the package.
- [ ] `docs/ExecPlans/gui_hitl_defect_regression_acceptance_execplan.md` is intentionally last; it
  consumes all three correction children and the existing package audit plan.
- [ ] `docs/ExecPlans/gui_preset_pdf_lifecycle_stability_parent_execplan.md` owns the newly observed
  preset-selection resource spike and QtPdf abort; its two children must complete before the installed
  regression matrix resumes.

Children 1–3 may be investigated independently, but each child must finish its own focused tests,
documentation update, and narrow commit before Child 4 starts. If two children discover a shared
seam, record the ownership decision here and in both child Decision Logs rather than silently mixing
change classes.

## Progress

- [x] (2026-08-20) Read the installed-package HITL results and separated completed Gates 0–1 from
  partial Gates 2–3 and untouched Gates 4–12.
- [x] (2026-08-20) Confirmed the observed defects against `UI_SPEC.md`: certificate creation and
  recovery (§15/WF05), Library/Appearance topology (SUR03/SUR04), fixed rail (SUR02), placement
  keyboard contract (SUR05 and §8), and acceptance scenarios 2, 3, 8, and 9.
- [x] (2026-08-20) Audited the likely source seams: `app_frame_certificate_management.py`,
  `certificate_readiness.py`, `signing_material_resolver.py`, `appearance_profile_editor_widget.py`,
  `app_frame_profile_library.py`, `signing_workspace_composition.py`, `app_frame.py`,
  `signing_workspace_runtime.py`, and `viewer_widget.py`.
- [x] (2026-08-20) Completed the required explorer review. It confirmed that certificate recovery
  clears the selected name and only prompts once, the rail already enforces a 280–640 pixel splitter
  range and therefore needs measurement before geometry changes, the Appearance editor has a text-only
  synthetic preview, and command-boundary coverage belongs in `tests/unit/test_qt_app_frame.py`.
- [x] (2026-08-20) Complete the initial Child 1 implementation: readable certificate creation
  geometry/copy, preserved certificate selection, bounded invalid-password retries, and focused
  regression coverage.
- [x] (2026-08-20) Completed the newly discovered Import Certificate and certificate-configuration
  dialog correction in `gui_surface_layout_correction_execplan.md` before Child 4 acceptance.
- [x] (2026-08-20) Completed the cross-surface dialog/menu audit correction pass: title-case
  consistency, explicit minimum/default geometry, and readable layouts for support, certificate,
  Library, and nested-editor surfaces before Child 4 acceptance.
- [x] (2026-08-20) Complete Child 2 implementation: explicit Library/editor minimum geometry, image-aware
  synthetic preview, Library geometry clamping, and existing rail persistence/offscreen proof retained.
- [x] (2026-08-20) Complete Child 3 implementation: controlled disposed-viewer error boundary, visible
  keyboard placement guidance, duplicate pointer-update coalescing, and focused regression coverage.
- [x] (2026-08-20) Completed the integrated source-tree GUI surface correction: explicit geometry and
  title-case conventions for audited dialogs/editors, grouped certificate/settings actions, nested
  editor spacing, and inner rail layout. Added the real-Qt rail assertion at the legal 280-pixel
  minimum; 1,605 tests passed with 20 skips and a bounded X11 sweep found no recurrence of the
  unusable default geometries.
- [x] (2026-08-23) The fresh installed-package session passed the no-document frame and keyboard
  reachability, then exposed a new document-open review slice: `Copy Result` is ambiguous beside the
  separate text-selection copy command; the unsigned review selector is disabled for the correct
  reason but lacks enough explanatory hierarchy; and the default right rail hides signing/presentation
  controls behind a poor scroll allocation with oversized action buttons and an ambiguous `Choose
  output...` label. These findings are recorded for Child 4 follow-up rather than treated as cosmetic.
- [x] Complete the focused document-review correction slice (Child 4a): duplicate copy retirement,
  compact unsigned review state, content-driven rail density, explicit save-path entry, documentation
  reconciliation, and AFK/package evidence are complete in
  `gui_document_review_copy_and_rail_density_execplan.md`.
- [ ] Complete the remaining installed-package regression matrix and final HITL acceptance record.
- [x] (2026-09-04) The installed human pass confirmed Gate 1 and Gate 2 through certificate
  management. The former `Copy Result` check is correctly retired: the sidebar duplicate was removed
  and selected-text copy is the supported command.
- [ ] (2026-09-04) The same pass exposed a release-blocking preset/PDF lifecycle failure: selecting
  an existing preset caused an immediate resource spike, followed by an installed-process SIGABRT
  during certificate creation. The coredump terminates in Qt6Pdf `QPdfDocument::load` from a Qt timer
  callback. A focused reproduction/correction child is required before the remaining matrix gates.
- [x] (2026-09-04) Created the focused stability family
  `gui_preset_pdf_lifecycle_stability_parent_execplan.md` with separate preset-reentrancy and PDF-load
  lifecycle children; independent explorer review is required before implementation.
- [x] (2026-09-04) Implemented the stability family’s AFK slice: preset delivery is single and guarded,
  canonical preview layout preparation is reused, QtPdf load failures are explicit, and failed preview
  snapshots are cleaned. Full validation and fresh package audits pass; the exact host-installed
  preset/certificate retry remains the release-blocking HITL gate.
- [x] Run the full suite, two-wave compliance review, package validation, and source/install visual
  evidence for Child 4a. The remaining Child 4 work is the ordered human release matrix.
- [x] Update parent/release status plans and create the focused implementation commit
  `45bec3135`; final living-plan reconciliation is recorded for the documentation commit below.

## Surprises & Discoveries

- Observation: several reported failures are directly covered by normative UI requirements rather than
  subjective polish.
  Evidence: `UI_SPEC.md` requires a usable 1100×700 main frame, a non-collapsing approximately
  320-pixel signing rail, a content-first Appearance editor with sticky preview, retryable wrong
  passwords, and keyboard placement with Enter/arrows/Escape/Delete/Undo.
- Observation: `CertificateCreationDialog` currently falls back from an empty Display name to the
  common name in `create_certificate()`, but its row label does not communicate optionality.
  Evidence: `src/foliaseal/presentation/qt/app_frame_certificate_management.py` constructs the row as
  `layout.addRow("Display name", display_name)` and substitutes `common_name` before creating the
  request.
- Observation: the Library Appearance editor already uses a scroll area and a synthetic preview label,
  so the observed failure may be a geometry/default-size problem and/or an insufficient preview
  representation rather than a missing navigation transaction.
  Evidence: `src/foliaseal/presentation/qt/appearance_profile_editor_widget.py` creates
  `Sample preview (synthetic data — never saved)`, a 72-pixel minimum label, and a scrollable setup
  form; Child 2 must inspect the rendered result before replacing this seam.
- Observation: `Adjust Placement` is a thin AppFrame command that calls
  `set_viewer_interaction_mode("signature")`; the crash therefore needs a live lifecycle traceback
  before anyone changes viewer geometry or command routing.
  Evidence: `src/foliaseal/presentation/qt/app_frame.py::_adjust_placement` and
  `signing_workspace_runtime.py::set_viewer_interaction_mode`.
- Observation: the automated AT-SPI warnings are not part of this family’s defect list. The observed
  failures are visible GUI behavior and must be corrected even if no accessibility bridge warning is
  emitted.
  Evidence: the minimal PySide6 Orca baseline remained usable while producing the same Qt warnings.
- Observation: the live source-tree surface sweep found several dialogs that are materially unusable
  at their default geometry, beyond the already-tracked Import Certificate and signing-rail defects.
  Application Settings measured 265×246 and truncates directory paths while stacking Browse controls;
  Manage certificate configurations measured 371×392 and compresses explanatory copy, fields, and
  vertically stacked actions; Manage reusable signing objects is 1100×700 but its three-column detail
  area leaves narrow, low-hierarchy control rows and uses the sentence-case title
  `Manage reusable signing objects`.
  Evidence: isolated X11 captures under `/tmp/foliaseal-dev-hitl-fFnbwy/` from the source-tree GUI on
  2026-08-20.
- Observation: the Help support dialogs are hard failures under the live theme. Keyboard Shortcuts,
  Data Locations, and About FoliaSeal each opened at exactly 102×121, clipping their titles and body
  text to a few characters. The Help viewer itself opened at its intended 760×520 and was usable,
  while the native Open PDF chooser opened at 1124×822 without a project-specific layout defect.
  Evidence: `keyboard-shortcuts.png`, `data-locations.png`, `about.png`, `help-viewer2.png`, and
  `open-file-dialog.png` in the same isolated X11 audit root.
- Observation: nested editors expose additional density problems. The Appearance editor keeps the
  synthetic preview and controls in the Library but its detail column is too narrow for several
  labels/format controls; the Preset editor leaves a large unused upper area while compressing the
  appearance, placement, certificate, and footer actions into a small lower band; the Edit Placement
  dialog measured only 236×347 and clips explanatory text/labels. These are layout/readability
  failures, not evidence that the frozen Library topology should be replaced.
  Evidence: `appearance-editor.png`, `preset-editor2.png`, and `preset-editor.png` in the isolated
  X11 audit root.
- Observation: menu labels are mostly readable, but capitalization is inconsistent with the requested
  title convention. Settings uses `Application settings`, `Manage reusable signing objects…`,
  `Create certificate…`, `Import certificate…`, and `Manage certificate configurations…`; Signing
  uses `Sign and save`; dialog titles also include the sentence-case variants. View and File menus fit
  their entries and correctly disable document-dependent commands for the unsigned fixture.
  Evidence: `settings-open2.png`, `signing-menu2.png`, `view-menu2.png`, and the measured dialog titles.
- Observation: a few workflow surfaces could not be opened with the unsigned one-page fixture because
  their enablement is correctly state-dependent: View → Document Signatures and Signing → Place
  Signature/Adjust Placement/Remove Placement/Sign and Save remain disabled until a preset, placement,
  or signed document exists. The audit therefore records their menu state but does not claim visual
  acceptance for the enabled states; a later acceptance run with disposable signing material must
  cover them.
  Evidence: `view-menu2.png` and `signing-menu2.png` from the same live session.
- Observation: the password dead end has two cooperating causes: coordinator error handling clears
  `_selected_certificate_configuration_name`, and `SigningSetupSession._run_with_manual_certificate_password_retry`
  prompts only once; the invalid-password message is not recognized by
  `_should_prompt_for_certificate_password`.
  Evidence: `signature_properties_coordinator.py` and `signing_setup_session.py`.
- Observation: the rail cannot normally shrink below 280 pixels in the splitter path, so the HITL
  report may describe clipped inner controls or a 280-pixel rail rather than an actual zero-width rail.
  Evidence: `SigningWorkspaceSidebar.RAIL_MIN_WIDTH = 280`, `RAIL_MAX_WIDTH = 640`, and delayed
  restoration in `signing_workspace_composition.py`.
- Observation: the installed review surface needs a focused terminology/affordance and rail-density
  correction before the remaining release gates can be judged cleanly. `Copy Result` currently means
  “copy the current search match,” while text-selection mode has a separate toolbar/Edit copy path;
  the unsigned `No signatures found` state disables its existing-signature selector; and the fixed
  320-pixel rail reserves too much vertical space for prose/status while making signing/presentation
  controls hard to discover at the default window size.
  Evidence: installed-package HITL observation on 2026-08-23, plus
  `signing_workspace_sidebar.py`, `document_review.py`, and `document_text_search.py`.
- Observation: output-path wording contributes to the workflow ambiguity. The current `Choose
  output...` command records a destination before signing, although a first-time user may expect the
  save destination only after the signing action.
  Evidence: `SigningActionCoordinator.accept_output_path()` and the installed-package HITL report.
- Decision candidate from the 2026-08-23 review: treat search-match copy and arbitrary selected-text
  copy as one V1 user-facing concept. Search-match copying is technically a case-insensitive matched
  span, while toolbar/Edit copy requires an explicit text selection; nevertheless, two visible copy
  buttons are not justified until usability evidence shows distinct demand. Child 4 should remove or
  demote `Copy Result` rather than silently preserve the duplicate affordance.

## Decision Log

- Decision: preserve the frozen PDF-first topology: primary canvas, persistent right signing rail,
  modeless master-detail Library, and stable controls that disable or fade in place.
  Rationale: the HITL session found regressions within that topology; replacing it would make the
  evidence impossible to compare and would violate `UI_SPEC.md`.
  Date/Author: 2026-08-20 / Codex.
- Decision: investigate first, then correct only the smallest owner of each defect.
  Rationale: the appearance preview, rail divider, and placement command already have typed seams;
  broad rewrites would hide the actual cause and mix unrelated change classes.
  Date/Author: 2026-08-20 / Codex.
- Decision: treat the Adjust Placement crash and wrong-password dead end as release-blocking, the
  clipped/undersized layouts as acceptance failures, and CPU/keyboard discoverability as stability
  and usability defects requiring evidence before severity is finalized.
  Rationale: a crash or irreversible signing dead end prevents the primary workflow; performance and
  discoverability need bounded measurements rather than guesses.
  Date/Author: 2026-08-20 / Codex.
- Decision: do not add compatibility wrappers, legacy product terminology, or a second signing flow.
  Rationale: the correction should deepen the existing modules and remove obsolete cruft only when a
  caller/test inventory proves it is unused; preserving duplicate paths would make the GUI harder to
  reason about.
  Date/Author: 2026-08-20 / Codex.
- Decision: keep the final acceptance child separate from implementation children.
  Rationale: unit/offscreen evidence cannot substitute for installed-package observation, and a human
  must still exercise Orca, high contrast, monitor movement, and the full signing story.
  Date/Author: 2026-08-20 / Codex.

## Revision Note

Revised on 2026-08-20 after the required explorer review to record the concrete coordinator/session
password failure, the rail measurement prerequisite, and the existing AppFrame test owner.

## Outcomes & Retrospective

The source-tree correction children are complete: the previously observed recovery, placement, and
default-layout defects have focused implementation and regression evidence, including the integrated
1,605-pass suite and bounded X11 sweep. Child 4 remains intentionally open because the installed
package and human gates still need to exercise enabled signing, Orca, high contrast, DPI/scaling,
monitor movement, and the complete signing story. Do not mark this parent complete until those package
acceptance observations are recorded.

## Context and Orientation

FoliaSeal is a Python/PySide6 desktop PDF signing application. The AppFrame owns top-level commands and
menus. `signing_workspace_composition.py` assembles the PDF viewer and right signing rail. The rail’s
properties panel owns certificate/preset/appearance selections and the signing readiness summary.
`app_frame_profile_library.py` owns the modeless Signature Library; its nested
`appearance_profile_editor_widget.py` edits a document-independent Appearance transactionally.
`viewer_widget.py` owns page rendering, placement overlays, pointer/keyboard interaction, and placement
history. `app_frame_certificate_management.py` owns create/import/manage dialogs, while application
modules such as `certificate_readiness.py` and `signing_material_resolver.py` define non-Qt certificate
and password semantics.

The supported acceptance target is the installed Debian package on Cinnamon/X11. Offscreen Qt tests
prove deterministic widget behavior; a display-backed X11 audit proves package startup; only the user
can certify speech, physical readability, and workflow comprehension.

## Plan of Work

Child 1 will reproduce the certificate dialog at the 1100×700 main-frame baseline, correct its title,
instruction geometry, optional Display name copy, and default layout, then trace the selected-certificate
password path. It will add a retry/reselect/cancel recovery state that retains the unsigned draft and
does not collapse the rail.

Child 2 will measure Library and Appearance editor geometry at 100% scaling and minimum supported sizes,
inspect whether the current synthetic preview reflects text and imported image changes, and correct the
editor’s scroll/sticky-preview composition. It will also enforce the right rail’s initial and restored
width so opening a document cannot leave its controls unusable.

Child 3 will capture the Adjust Placement crash traceback, add a regression test at the command boundary,
and repair lifecycle/mode routing. It will profile pointer placement refreshes with a bounded fixture,
coalesce or eliminate redundant work only where evidence supports it, and expose the existing Enter,
arrow, Ctrl-arrow, Shift, Delete, Escape, and Undo behavior clearly in the UI.

Child 4 will rebuild the package, run all focused and full tests, repeat the offline/private/X11 audits,
and conduct the installed-package Gates 0–12. It will update this family, the installed-package plan,
the packaged release plan, and the parent compliance status with observed results, then leave no
session-owned process or temporary artifact behind.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`. Before each child, inspect `git status --short`, retain
unrelated changes, and keep that child’s primary change class in its own commit. The expected baseline
commands are:

    .venv/bin/pytest -q tests/unit/test_qt_app_frame_certificate_management.py tests/unit/test_qt_app_frame_profile_library.py tests/unit/test_placement_editor.py
    .venv/bin/pytest -q
    .venv/bin/ruff check src tests
    git diff --check

The first command is exploratory because the repository’s exact placement test filename must be checked
before execution; each child plan gives its authoritative focused command. Never use `rm -rf` on a broad
path. Generated audit roots belong under a uniquely named `/tmp/foliaseal-*` directory and are removed
only after their process and file ownership have been verified.

## Validation and Acceptance

The family is accepted only when all three correction children have green focused tests and the final
installed package passes the relevant UI_SPEC scenarios. Specifically, the default dialogs must be
readable without manual enlargement; a wrong password must offer retry, reselect, or cancel; the
Appearance editor and rail must remain usable at supported minimums; Adjust Placement must not crash;
pointer placement must not show sustained runaway CPU in the bounded measurement; and a keyboard user
must be able to discover and complete placement. The final package must still pass the existing payload,
Help, font/icon, Poppler, offline, private install-root, and X11 startup audits.

## Idempotence and Recovery

All diagnosis is read-only until a child’s focused failing test is written. A failed child may be retried
from its last progress entry; do not reset or discard unrelated work. GUI tests use isolated temporary
configuration and cache roots. Certificate tests use generated disposable PKCS#12 material and never
write secrets into repository fixtures. If an implementation attempt makes the app unlaunchable, revert
only that child’s uncommitted edits or use its focused commit, then preserve the failing evidence in the
child plan. Host package installation and human acceptance remain in Child 4 and require explicit user
authorization; no child may mutate the host package database during ordinary tests.

## Artifacts and Notes

Keep only source tests, plan updates, and concise safe logs. Do not commit `.deb` files, PyInstaller
directories, screenshots containing private data, passwords, private keys, PDF contents, or machine-local
temporary roots. A useful final evidence record contains focused test counts, the Adjust Placement
traceback or regression result, a bounded CPU measurement, package audit summaries, and the human
Gate 0–12 result.

## Interfaces and Dependencies

Use the existing typed AppFrame command registry (`AppFrameCommandId`), `SigningWorkspaceRuntime`,
`SigningShellPort`, `QtVisibleSignatureSetupForm`, `AppearanceProfileEditorWidget`,
`CertificateManager`, `CertificateReadiness`, and `SigningMaterialResolver` seams. Do not introduce a
second certificate store, a second preview renderer, a new signing transaction, or a new UI topology.
When a new test seam is needed, expose a narrow public behavior boundary rather than reaching into Qt
private fields. Every new error message must be plain language, must not contain passwords or PDF
contents, and must leave the unsigned draft recoverable.
