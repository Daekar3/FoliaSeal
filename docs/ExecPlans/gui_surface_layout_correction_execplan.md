# Correct the audited GUI surface layouts and visible titles

This ExecPlan is a living document and must remain self-contained under
`/home/daekar/.codex/skills/write-execplan/PLANS.md`. It is a focused behavior-and-evidence slice
that implements the complete source-tree GUI corrections found during the 2026-08-20 Cinnamon/X11
audit. Keep the frozen PDF-first topology intact while this plan is active.

## Purpose / Big Picture

After this slice, a user can open FoliaSeal at the supported desktop baseline and use every audited
dialog without manually enlarging it or guessing where clipped controls went. Certificate import and
configuration management, Application Settings, support dialogs, reusable signing objects, nested
Appearance/Preset editors, and placement editing will have deliberate default/minimum geometry,
readable grouping, and stable action rows. The signing rail will retain its approximately 320-pixel
initial width and adjustable divider while its selectors, preview, document-text actions, and status
copy remain usable at the supported minimum. Visible menu and dialog titles will use consistent title
capitalization while explanatory copy remains sentence-style.

The result is demonstrated by focused offscreen Qt tests, the full test/lint/compile checks, and a
fresh display-backed source-tree sweep using the disposable PDF fixture. The later installed-package
acceptance child still owns enabled-state signing, Orca, DPI, high-contrast, and monitor-movement
acceptance; this slice must not claim those human gates are complete.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md`, `docs/UI_SPEC.md`, `docs/SCHEMAS.md`, and `docs/ARCHITECTURE.md` are present and
  authoritative. Product scope comes from `SPEC.md`, persistence semantics from `SCHEMAS.md`, and
  interaction realization from `UI_SPEC.md`.
- [x] The parent and child GUI recovery plans record the live observations and preserve the frozen
  PDF-first workspace, modeless three-column Library, and adjustable 280–640-pixel rail contract.
- [x] Explorer review completed on 2026-08-20 and identified the existing presentation owners and
  test gaps; no domain or architecture rewrite is required.
- [ ] The installed-package regression acceptance plan remains open and depends on this slice for its
  corrected source-tree surfaces.

## Progress

- [x] (2026-08-20) Captured and recorded the live X11 findings, exact default geometries, and state-
  dependent surfaces that could not be enabled with the unsigned fixture.
- [x] (2026-08-20) Reviewed current Qt owners, governing documents, and existing test seams with an
  explorer; confirmed the work is a presentation-layer correction rather than a topology rewrite.
- [x] (2026-08-20) Added guarding offscreen and real-Qt geometry/title tests for every corrected owner.
- [x] (2026-08-20) Corrected certificate import and certificate-configuration dialog geometry,
  grouping, and titles.
- [x] (2026-08-20) Corrected Application Settings and shared support-dialog geometry and action rows.
- [x] (2026-08-20) Corrected Library, nested Appearance/Preset, and reusable placement editor geometry without
  removing scrolling, sticky preview, or transactional Save/Back behavior.
- [x] (2026-08-20) Corrected visible menu/dialog title capitalization across the audited surfaces.
- [x] (2026-08-20) Corrected inner signing-rail layout pressure while preserving the adjustable divider
  contract and 280–640 bounds.
- [x] (2026-08-20) Added a real-Qt minimum-width rail assertion: at 280 pixels, the query/navigation
  controls and status/detail labels retain non-zero usable widths.
- [x] (2026-08-20) Focused tests: 143 passed; full suite: 1,605 passed, 20 skipped; Ruff, compileall,
  and diff checks passed (one existing Pillow deprecation warning remains).
- [x] (2026-08-20) Fresh bounded X11 sweep confirmed readable 680×520 Import Certificate, 680×340
  Application Settings, 640×420 support dialogs, 1,100×700 Library, and 560×500 Placement surfaces;
  all audit processes/dialogs and exact temporary roots were cleaned up.
- [x] (2026-08-20) Recorded remaining enabled-state limitations: Document Signatures and Place/Adjust/
  Remove/Sign actions require a signed or placed-signature fixture and remain installed-package HITL
  gates; no action enablement was weakened to make the unsigned sweep pass.
- [x] Complete the compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and
  `docs/UI_SPEC.md`; the presentation owners, frozen topology, rail bounds, and disabled-state
  semantics remain aligned, with no new persistence/protocol/ownership boundary.
- [x] Update the parent/child ExecPlans and the rail architecture status; the focused commit is
  complete; the final commit is this plan's current HEAD.

## Surprises & Discoveries

- Observation: Application Settings has no explicit minimum/default geometry and its form layout puts
  Browse and action controls on separate rows, producing a 265×246 live window with truncated paths.
  Evidence: `AppSettingsDialog` in `src/foliaseal/presentation/qt/app_frame.py` and the captured X11
  audit.
- Observation: Import Certificate and Manage Certificate Configurations have the same missing-geometry
  pattern in `src/foliaseal/presentation/qt/app_frame_certificate_management.py`; their measured windows
  were 267×284 and 371×392 respectively.
  Evidence: live captures and existing dialog construction code.
- Observation: Keyboard Shortcuts, Data Locations, and About FoliaSeal share a base support-dialog
  implementation with no useful default size; each opened at 102×121 and clipped its title/body.
  Evidence: `src/foliaseal/presentation/qt/support_dialogs.py` and the live X11 measurements.
- Observation: The Help viewer already opens at 760×520 and the native Open PDF chooser at 1124×822;
  they are not included in the implementation change unless a regression test shows otherwise.
  Evidence: live X11 sweep.
- Observation: The Library and nested editors are structurally correct but over-constrained. The
  Appearance detail column clips controls, the Preset editor leaves unused upper space while packing
  workflow actions into a lower band, and Edit Placement measures 236×347.
  Evidence: `app_frame_profile_library.py`, the editor widgets/dialogs, and live captures.
- Observation: In production the rail is bounded to 280–640 pixels by the splitter. The clipping is
  primarily inner-layout pressure: the document-text action row, selector rows, and wrapped status
  copy compete inside the minimum rail.
  Evidence: `signing_workspace_sidebar.py`, `signing_workspace_composition.py`, and the measured rail.
- Observation: View → Document Signatures and several Signing actions remained disabled because the
  fixture was unsigned and had no preset/placement. Their enabled states require the later package
  acceptance run and must not be weakened for this slice.
  Evidence: captured View and Signing menus.

## Decision Log

- Decision: implement all audited source-tree layout/title corrections as one presentation-layer slice
  while keeping the parent recovery children as the governing ownership records.
  Rationale: the defects are cross-surface but share one observable user problem—default GUI surfaces
  are not usable—and splitting them further would leave the audit incomplete.
  Date/Author: 2026-08-20 / Codex.
- Decision: preserve the frozen PDF-first topology, modeless three-column Library, sticky synthetic
  preview, and adjustable rail rather than solving clipping with a large fixed window or modal rewrite.
  Rationale: `UI_SPEC.md` makes those spatial relationships normative and they are already represented
  by typed presentation seams.
  Date/Author: 2026-08-20 / Codex.
- Decision: use explicit minimum/default sizes plus composed horizontal rows, scrollable detail regions,
  and stable bottom action rows; do not rely on platform auto-sizing for text-heavy dialogs.
  Rationale: the live failures are deterministic auto-size failures under the supported theme.
  Date/Author: 2026-08-20 / Codex.
- Decision: normalize visible menu/dialog titles to title case, but leave explanatory sentences and
  field descriptions in normal sentence case.
  Rationale: this addresses the user-visible inconsistency without making instructional prose awkward.
  Date/Author: 2026-08-20 / Codex.
- Decision: add geometry tests that assert minimum/default dimensions and control reachability rather
  than pixel-perfect coordinates.
  Rationale: Qt font metrics and display themes vary; behavior must remain portable while catching the
  102×121/236×347 class of failure.
  Date/Author: 2026-08-20 / Codex.

## Outcomes & Retrospective

This plan starts with all observed layout/title defects open. At completion, record the corrected
minimum/default sizes, focused and full test results, fresh X11 observations, and any remaining
state-dependent acceptance gaps. The plan is complete only when every source-tree observation in the
audit has either been corrected and tested or explicitly transferred to the installed-package HITL
plan with a reason it cannot be certified autonomously.

Completed outcome evidence (2026-08-20): the source-tree correction is green under 1,605 passing tests
and 20 skips, and the display-backed probe measured the corrected surfaces without recurrence of the
102×121, 236×347, 265×246, 267×284, or 371×392 unusable defaults. The remaining release work is
installed-package signing/accessibility/HITL acceptance, not an unresolved source-tree layout defect.

## Context and Orientation

FoliaSeal is a Python/PySide6 desktop PDF signer. `src/foliaseal/presentation/qt/app_frame.py` owns
the top-level window, menus, Application Settings, and command routing. Certificate creation/import
and certificate configuration management live in
`src/foliaseal/presentation/qt/app_frame_certificate_management.py`. The reusable signing-object
Library and its nested editors live in `app_frame_profile_library.py`,
`appearance_profile_editor_widget.py`, `signature_preset_editor_widget.py`, and
`placement_profile_editor_dialog.py`. Shared support windows live in `support_dialogs.py`.
`signing_workspace_sidebar.py`, `signing_workspace_properties_panel.py`, and
`signing_workspace_composition.py` assemble the persistent right signing rail. Tests are primarily in
`tests/unit/test_qt_app_frame.py`, `tests/unit/test_qt_app_frame_certificate_management.py`,
`tests/unit/test_qt_app_frame_profile_library.py`, the appearance/preset/placement editor tests, and
the signing workspace composition/rail tests.

The supported GUI contract is a 1100×700-capable main frame, a persistent adjustable right rail whose
normal width is about 320 logical pixels and whose legal range is 280–640, a modeless three-column
Library with a sticky synthetic preview, and transactional Save/Cancel or Save/Back actions. Qt
widgets belong at the presentation edge; application/domain modules must not gain layout concerns.

## Plan of Work

First add or extend focused offscreen tests in the existing Qt test owners. Assert title strings,
minimum/default geometry, non-zero visible text-browser height, stable action-row visibility, and
reachability of required controls. Add support-dialog coverage for all three subclasses, import and
certificate-configuration geometry coverage, wrapper and nested editor coverage, and rail assertions
that identify clipped child layouts at the minimum effective width without hard-coding one platform’s
pixel coordinates. Update any old sentence-case title assertions at the same time.

Then correct `CertificateImportDialog._build_controls()` and
`CertificateConfigurationManagementDialog._build_controls()`. Use title-case window titles, explicit
minimum/default sizes, horizontal file-path/Choose and action rows, grouped inspection guidance, and
separated configuration versus managed-certificate actions. Keep inspect-before-import, password
handling, destructive-action confirmation, and existing certificate domain contracts unchanged.

Correct `AppSettingsDialog` in `app_frame.py` with a small but explicit default/minimum size. Compose
each directory path with its Browse button in one row, keep Appearance in the form, and put Save,
Cancel, and Restore Defaults in one stable footer. Correct the shared support-dialog base so the text
browser expands to a useful minimum height and Close remains reachable; keep the Help viewer unchanged
unless tests expose a regression.

Correct the Library/editor owners without changing navigation or persistence. Give the nested
Appearance and Preset hosts enough minimum width, keep the preview visible while the form scrolls,
reallocate unused Preset vertical space into readable grouped controls, and give the reusable Placement
dialog an explicit size with a two-column numeric form and readable hint. Apply the same geometry/title
convention to the compatibility editor wrappers if their tests instantiate them. Preserve staged-image
cleanup and Save/Back transactions.

Normalize visible menu and dialog strings in `app_frame_command_model.py`, `app_frame.py`, certificate
management, Library/editor wrappers, and placement/refinement surfaces. Use title case only for names
and commands; do not rewrite user-facing explanatory paragraphs.

Finally measure the real rail before changing the splitter. Keep the 280–640 bounds and approximately
320 initial width. Recompose the document-text controls into a deliberate two-row or compact labeled
layout, allow selector fields to expand, and give status/detail content a stable minimum with vertical
scroll ownership. Do not make the rail permanently oversized or remove its divider.

## Concrete Steps

Run commands from `/home/daekar/FoliaSeal` and preserve unrelated worktree edits.

    git status --short
    rg -n "setWindowTitle|setMinimumSize|resize\(|Document text|Find|Application settings|Import certificate|Manage certificate" src/foliaseal/presentation/qt tests/unit tests/integration

Run the focused tests before changing code to establish the baseline and identify exact test owners:

    .venv/bin/pytest -q tests/unit/test_qt_app_frame.py tests/unit/test_qt_app_frame_certificate_management.py tests/unit/test_qt_app_frame_profile_library.py tests/unit/test_qt_signing_workspace_composition.py tests/unit/test_qt_signing_rail_stage_status.py tests/unit/test_qt_appearance_image_lifecycle.py tests/integration/test_placement_profile_editor.py

After each owner is corrected, run its focused tests. At the end run:

    .venv/bin/pytest -q
    .venv/bin/ruff check src tests
    .venv/bin/python -m compileall -q src
    git diff --check

For the bounded display-backed audit, launch only the source-tree GUI with a unique `/tmp/foliaseal-`
root, open each corrected surface at the default geometry, record native `xwininfo` dimensions, and
capture screenshots. Use the disposable PDF fixture; do not create real certificates or sign a user
document. Close every dialog, stop the exact process, remove the exact temporary root, and verify no
`foliaseal gui` process remains.

## Validation and Acceptance

The slice passes when the focused tests prove all audited dialogs have explicit usable geometry and
reachable required controls; all title/menu assertions use the chosen title convention; the full suite,
Ruff, compileall, and diff checks pass; and the fresh X11 sweep shows no recurrence of the 102×121,
236×347, 265×246, 267×284, or 371×392 unusable layouts. The Library remains three-column and
modeless, Appearance preview remains visible while controls scroll, the rail remains adjustable and
does not clip its selector/document-text/status controls at its supported minimum, and the native Help
viewer/file chooser remain functional. State-dependent enabled actions are recorded as deferred to the
installed-package acceptance plan rather than falsely marked complete.

## Idempotence and Recovery

All changes are confined to existing Qt presentation owners and their tests. Re-run focused tests
after any failed patch; do not reset unrelated changes. Use isolated temporary settings/cache roots for
display tests. If a display run fails, terminate only the exact process created for the run and remove
only its exact temporary root after verifying ownership. Never write screenshots, certificates,
passwords, or PDFs into the repository. If a compatibility wrapper is no longer referenced, remove it
only after a repository-wide caller/test search and record the decision here rather than keeping dead
layout paths.

## Artifacts and Notes

Allowed changes are Qt presentation behavior, focused tests, and narrowly reconciled ExecPlan/
architecture/status documentation. Do not mix signing-domain changes, persistence schema changes,
packaging changes, generated screenshots, or unrelated refactors into this commit. Preserve concise
evidence such as:

    support dialogs -> explicit minimum/default geometry; body text and Close visible
    Import Certificate -> title-cased, grouped file/inspection/form/footer layout
    rail at minimum -> selectors, document-text actions, preview, and status copy readable
    cleanup -> no FoliaSeal GUI process; temporary audit root removed

## Interfaces and Dependencies

Keep all existing application contracts—`CertificateManager`, `CertificateDialogPort`, reusable-object
catalog transactions, `SigningWorkspaceRuntime`, and rail divider persistence—unchanged. Use the
existing Qt binding seam and offscreen test fixtures. Layout composition belongs in the named Qt owners;
do not move geometry or text into application/domain modules. The installed package and enabled signing
workflow remain downstream acceptance dependencies, not reasons to weaken current action enablement.

## Revision Note

Created on 2026-08-20 after the full live X11 surface sweep and explorer review. This plan consolidates
the previously separate Import Certificate, Library/rail, and placement observations with the newly
measured Application Settings, certificate configuration, support-dialog, nested-editor, and title/menu
findings so one dev-loop can complete the source-tree correction slice without losing any audit result.
