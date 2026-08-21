# Complete the source-tree X11 GUI workflow audit and correct discovered defects

This ExecPlan is a living document maintained according to
`/home/daekar/.codex/skills/write-execplan/PLANS.md`. It defines one controlled audit-and-correction
slice for the real FoliaSeal Qt GUI on the supported Cinnamon/X11 desktop. It must remain
self-contained as findings, decisions, and evidence accumulate.

## Purpose / Big Picture

Before asking a person to repeat HITL acceptance, the project needs trustworthy evidence that the
actual rendered source-tree GUI is coherent and usable across its workflow, not merely that selected
offscreen tests pass. After this slice, the audit will open FoliaSeal on X11, capture the no-document
and open-document states, walk every reachable menu/dialog/editor and signing workflow state, exercise
keyboard traversal and keyboard-operable placement, and record the result as evidence. Any source-tree
defect that can be corrected without a product decision will be fixed, tested, and re-audited. A user
will be able to see the resulting screenshots and JSON/checkpoint evidence, while genuine HITL-only
questions such as Orca speech, high-contrast perception, and final installed-package acceptance remain
explicitly separated rather than being guessed from machine evidence.

## Child ExecPlan Dependencies

- [x] The governing contracts are present: `docs/SPEC.md` defines product scope, `docs/SCHEMAS.md`
  defines persistence semantics, `docs/UI_SPEC.md` defines interaction realization, and
  `docs/ARCHITECTURE.md` defines ownership boundaries.
- [x] The prior GUI surface-layout slice is committed and its source-tree geometry corrections are
  available in `fd096d2d3`.
- [x] Explorer review completed on 2026-08-21 and identified the canonical parent audit, stale title
  expectations, keyboard-coverage gaps, fixture limitations, and the required audit matrix.
- [x] The current one-page unsigned fixture cannot represent signed, restricted, multi-page, or
  unsigned-field states; that limitation is recorded and transferred rather than silently skipped or
  claimed accepted. Additional fixtures remain a separate follow-up before those states are released.

## Progress

- [x] (2026-08-21) Read the dev-loop, ExecPlan, and full PLANS instructions; inspected current plans,
  audit scripts, governing documents, and the clean checkout.
- [x] (2026-08-21) Completed the required explorer review and acknowledged its report.
- [x] (2026-08-21) Reconciled stale title expectations in `scripts/live_gui_parent_audit.py`, fixed
  two pre-existing indentation errors that prevented compilation, and confirmed the harness passes
  Python compilation and Ruff checks.
- [x] (2026-08-21) Built an isolated X11 audit environment and completed the canonical parent workflow:
  19 rendered checkpoints, two signatures, reopen/verify, and clean owned-root teardown. The run
  passed, while native screenshot review exposed a real horizontal rail scrollbar and clipped helper
  text that offscreen assertions had missed.
- [x] (2026-08-21) Audited rendered menus, mnemonics, keyboard traversal, Ctrl+F, Tab/Shift+Tab,
  keyboard placement/edit/delete/cancel, rail states, the manual-refinement/settings/certificate/
  Library dialogs, and the complete two-signature workflow. The final X11 run passed with 22 native
  screenshots/checkpoints.
- [x] (2026-08-21) Recorded each unavailable signed, restricted, multi-page, and unsigned-field state
  with its reason for deferral; generating safe additional fixtures is explicitly outside this audit
  slice and remains a separate follow-up.
- [x] (2026-08-21) Reviewed the final native screenshots at original resolution. Titles and labels are
  title-cased and readable; the rail no longer has a horizontal scrollbar; controls remain inside
  their cards; focus/disabled states are visible; placement overlays and reopened signatures render
  on-page; dialog geometry is usable. The only corrected product findings were rail reflow and the
  status-label inner-width clip.
- [x] (2026-08-21) Corrected source-tree defects through the rail-owned shrink policy, preview reflow
  on resize, and status-detail width correction; added regression assertions and reran the complete
  X11 workflow after each correction.
- [x] (2026-08-21) Ran focused validation: signing-shell tests `111 passed` and rail persistence tests
  `2 passed`; the clean full suite then passed `1605 passed, 20 skipped, 1 warning` in 61.32s.
- [x] (2026-08-21) Ran Ruff, Python compilation, and `git diff --check`; all passed. Re-ran the final
  privileged X11 parent audit and native no-document/accessibility audit against the final checkout.
- [x] (2026-08-21) Completed the post-implementation architecture/compliance review. The rail and
  preview ownership is consistent with `docs/ARCHITECTURE.md`; the remaining UI terminology conflict,
  fixture gaps, and HITL-only gates are explicitly retained as follow-up rather than overstated.
- [x] (2026-08-21) Committed the complete bounded audit/correction slice as `79f6033d0` and verified
  that no owned GUI process, dialog, or audit temporary root remains.

## Surprises & Discoveries

- Observation: `scripts/live_gui_parent_audit.py` already exercises certificate creation, appearance,
  placement, presets, signing, reopen/verify, and a second signature, but it uses semantic `.click()`
  and mouse events rather than proving keyboard traversal or keyboard placement.
  Evidence: explorer review of the script and its checkpoint functions.
- Observation: the parent audit still expects lowercase titles such as `Create certificate`,
  `Application settings`, and `Refine current PDF setup`, while the current source intentionally uses
  title case. These are harness defects, not product regressions.
  Evidence: source and script search reported by the explorer.
- Observation: `artifacts/preview_sweep_assets/sweep_fixture.pdf` is a one-page, unsigned, unencrypted
  PDF without form fields or unsigned signature fields. It cannot prove multi-page navigation,
  signed-document review, restricted-document behavior, or unsigned-field targeting.
  Evidence: explorer fixture inspection.
- Observation: AT-SPI/Orca warnings must not be treated as GUI defects without observed user-visible
  failure; earlier minimal PySide6 testing established that Qt bridge warnings can coexist with
  functional Orca behavior.
  Evidence: prior controlled accessibility baseline recorded in the recovery plans.
- Observation: the successful parent audit still rendered a horizontal scrollbar in the signing rail;
  `tests/integration/test_rail_divider_persistence.py` measured a 512px properties child against a
  304px viewport, and the native `01-document-review.png`/`07-profile-library-clarity.png` frames
  showed clipped selector/helper content. The fixed-size preview and preferred-width group boxes were
  not reflowing after the rail acquired its real width.
  Evidence: `/tmp/foliaseal-full-x11-audit-073ODn` screenshots and the failing rail assertion.
- Observation: after the rail reflow correction, the status card's fixed detail-label width still
  exceeded its six-pixel card margins by 12px, leaving the shortest setup message visibly clipped at
  the right edge even though the scrollbar was gone. The rendered signed/reopened states wrapped
  correctly because their messages were longer; the initial setup state exposed the defect.
  Evidence: `/tmp/foliaseal-full-x11-audit-ueTPri/01-document-review.png` and the sidebar's
  `RAIL_WIDTH - 16` width calculation.
- Observation: the final bounded X11 run passed keyboard menu activation/dismissal for every top-level
  menu, Ctrl+F focus transfer, Tab/Shift+Tab traversal, Enter/Shift-arrow/Ctrl-arrow/Delete/Escape
  placement editing, and native X11 F1 Help delivery. These are source-tree keyboard guarantees;
  Orca speech remains a human gate.
  Evidence: final `/tmp/foliaseal-full-x11-audit-AEPBUW/audit.json` and the no-document X11 report
  `/tmp/foliaseal-x11-a11y-audit-c6KjPa/audit.json`.
- Observation: native screenshots of the manual refinement, Application Settings, Create Certificate,
  and modeless Signature Library dialogs show usable geometry, readable labels, title-case field names,
  and controls inside their surfaces. The Library remains a three-column modeless master-detail view.
  Evidence: final dialog checkpoints `03`, `05`, `07`, and `09` under `/tmp/foliaseal-full-x11-audit-AEPBUW`.
- Compliance gap retained for follow-up: `UI_SPEC.md` forbids ordinary UI terms such as “Certificate
  Configuration,” “Managed Certificate,” “Appearance Profile,” and “Placement Profile.” Existing
  management/refinement surfaces still expose those labels in `app_frame_certificate_management.py`
  and `signing_workspace_refinement_dialog.py`; changing them is a separate terminology slice because
  it crosses several visible dialogs, tests, and persisted-object explanations.
  Evidence: post-implementation explorer review and `docs/UI_SPEC.md` §3.
- Coverage gap retained for follow-up: the live X11 run reviewed the default rail and the regression
  test now exercises the 280px lower boundary, but a native screenshot at every width in the
  280–640px range is intentionally not part of this slice. The 280px semantic render assertion is
  durable evidence that the minimum boundary retains usable content without a horizontal scrollbar.
- Observation: the long green post-signing result initially exceeded the status card's allocated
  label height (`required=120`, `actual=61`) even though shorter states looked correct. The final
  correction reserves the wrapped result label's calculated minimum height; the final X11 run then
  displayed the complete saved path, local-verification summary, and timestamp statement without
  clipping.
  Evidence: failed bounded run `/tmp/foliaseal-full-x11-audit-yiMVut` followed by the passing
  `/tmp/foliaseal-full-x11-audit-vW5qdT/21-second-signature-signed.png`.

## Decision Log

- Decision: treat the canonical source-tree parent audit as the signing-flow backbone, but surround it
  with a broader rendered/keyboard matrix rather than replacing it.
  Rationale: the existing runner already creates realistic signing state; duplicating it would increase
  risk while still leaving keyboard and menu coverage absent.
  Date/Author: 2026-08-21 / Codex.
- Decision: fix stale audit expectations before interpreting audit failures.
  Rationale: a harness that expects intentionally corrected lowercase titles would produce false product
  failures and obscure genuine layout/function findings.
  Date/Author: 2026-08-21 / Codex.
- Decision: classify every unavailable state as product, harness, fixture, or HITL evidence.
  Rationale: a one-page unsigned fixture cannot honestly certify signed-document or accessibility
  behavior, and those categories require different follow-up actions.
  Date/Author: 2026-08-21 / Codex.
- Decision: use Qt's semantic widget access and a bounded X11 input adapter for keyboard checks, not
  screen-coordinate automation, except where the product contract itself is pointer placement.
  Rationale: semantic interaction is deterministic and maintainable; X11 is reserved for proving the
  actual desktop rendering/focus path and the existing pointer placement contract.
  Date/Author: 2026-08-21 / Codex.
- Decision: rail-owned property groups must be horizontally shrinkable, and the fixed preview must
  reapply its geometry when the panel is resized; a hidden scrollbar is not an acceptable fix for
  clipped content.
  Rationale: the rendered audit exposed content loss that a semantic workflow pass did not see.
  Date/Author: 2026-08-21 / Codex.
- Decision: constrain the status detail label to the status card's actual inner width (`rail - 28`)
  so short and long workflow messages use the same readable wrap boundary.
  Rationale: removing a scrollbar is insufficient if a fixed child still paints under the card edge.
  Date/Author: 2026-08-21 / Codex.
- Decision: do not silently relabel schema terms during this audit slice; record the governing-doc
  terminology gap and transfer it to a focused follow-up plan rather than mixing a broad naming
  migration into the rendered-geometry correction.
  Date/Author: 2026-08-21 / Codex.

## Outcomes & Retrospective

Current evidence snapshot (2026-08-21): the source-tree Cinnamon/X11 audit completed with 22 native
rendered/keyboard checkpoints, covering the no-document and open-document surfaces, top-level menus,
Help delivery, Settings/certificate/refinement/Library dialogs, rail states, keyboard placement
editing, signing, reopen/verify, and a second signature. Native screenshot review found and then
verified fixes for rail-owned horizontal overflow, fixed preview reflow after the rail acquired its
real width, and a status-detail label that painted beyond its card's inner width. These are product
corrections, not screenshot-only exceptions. The parent workflow's `audit.json` and PNGs were held
under uniquely named `/tmp/foliaseal-full-x11-audit-*` roots during review and are not repository
artifacts.

The durable fixture remains one-page, unsigned, unencrypted, without form fields or unsigned
signature fields. Signed-document review, restricted-document behavior, multi-page navigation, and
unsigned-field targeting therefore remain explicitly fixture-limited; they must not be called passed
until safe additional fixtures exist. Orca speech, screen-reader announcements, high-contrast/DPI
perception, and installed-package acceptance remain HITL gates. The AT-SPI warnings observed during
the minimal PySide6 baseline remain diagnostic Qt bridge noise unless a user-visible failure is
observed.

Final evidence (2026-08-21):

- `DISPLAY=:0 QT_QPA_PLATFORM=xcb PYTHONPATH="$PWD/src" .venv/bin/python scripts/live_gui_parent_audit.py`
  passed with 22 checkpoints, two signed outputs, and `output_signature_count: 2`. The reviewed root was
  `/tmp/foliaseal-final-x11-audit-FPs46G`; it was removed after review.
- The native no-document audit passed with XCB, 1100×700 minimum/window geometry, F1 Help delivery,
  menu/action metadata, and owned-window/temp-root cleanup. The reviewed root was
  `/tmp/foliaseal-final-a11y-audit-Y2MsyH`; it was removed after review.
- Native review covered the no-document frame, default/minimum rail behavior, menu mnemonics and
  Escape dismissal, Ctrl+F, Tab/Shift+Tab, placement Enter/Shift-arrow/Ctrl-arrow/Delete/Escape,
  four dialog surfaces, reopen/verify, and the complete second-signature path. The final result label
  now reserves wrapped height and shows the full saved-path/local-verification message.

The plan is complete only when the source-tree audit has either passed each representable requirement
or transferred it with an explicit reason to a fixture/package/HITL follow-up; “the script ran” is not
sufficient evidence.

## Context and Orientation

FoliaSeal is a Python/PySide6 desktop PDF signer. `src/foliaseal/presentation/qt/app_frame.py` owns
the main window, menus, Settings, and top-level dialog routing. Certificate flows live in
`app_frame_certificate_management.py`; the modeless three-column reusable-object Library lives in
`app_frame_profile_library.py`; Appearance, Preset, and Placement editors live in their focused Qt
modules. `signing_workspace_sidebar.py`, `signing_workspace_properties_panel.py`, and
`signing_workspace_composition.py` assemble the PDF-first canvas and adjustable 280–640px signing
rail. `scripts/live_gui_parent_audit.py` is the existing semantic signing-flow runner; the
accessibility/X11 helpers are in `scripts/live_gui_accessibility_audit.py` and
`scripts/x11_atspi_probe.py`.

The supported source-tree acceptance target is Cinnamon/X11 with a main-window minimum of 1100×700,
an initially approximately 320px right rail that may resize from 280 to 640px, and a modeless Library
with three columns. Menus must expose unique mnemonics, arrow/Enter/Escape behavior, shortcuts, and
truthful enablement. Placement must remain cancelable and keyboard-operable. A dialog being visible
is not proof that its labels, focus, action, or state behavior is correct.

## Plan of Work

First reconcile the audit harness. Update only audit expectations and audit metadata in
`scripts/live_gui_parent_audit.py` for the current title-case strings, and add checks for visible
window titles, menu labels, and checkpoint state. Keep product semantics untouched. Run the script’s
unit tests or the narrow audit tests before display execution so failures distinguish harness drift
from GUI behavior.

Next launch the source-tree GUI or the semantic parent audit under a unique temporary settings/data/
cache/state root and an isolated `XDG_RUNTIME_DIR`. Record the exact PID and root. Capture the
no-document frame first, then open the disposable PDF and capture the main workspace at default and
minimum rail widths. Review the rendered screenshots at native scale, not only image dimensions.

Walk the menu tree in order: File, Edit, View, Signing, Settings, and Help. For each menu record its
visible capitalization, mnemonic uniqueness, enabled/disabled state, keyboard activation, and whether
Escape dismisses it without side effects. Exercise viewer toolbar navigation, zoom/fit/pan/select,
find/copy/clear, and output/status controls. Use the current fixture where possible and label
multi-page or signed-only states as unavailable when it is not possible to represent them.

Walk the Library catalogs (Presets, Appearances, Placements, Certificates), search/sort, selection,
rename, create/edit, Save/Cancel/Discard, nested editor return paths, and modeless behavior. Inspect
Settings, certificate creation/import/configuration, Help, Keyboard Shortcuts, Data Locations, About,
diagnostic-folder behavior, and Document Signatures. For each surface verify title capitalization,
label clarity, default/minimum geometry, focus visibility, Tab order, Enter activation, Escape
dismissal, and that every enabled control does what its label promises.

Use the existing parent workflow to create a disposable certificate/preset/placement, place a
signature, sign, reopen/verify, and add a second signature. Add keyboard checks around the semantic
steps: menu mnemonics, Tab traversal, `Ctrl+F`, `Ctrl+C`, placement arrows and modifiers, Delete, and
Escape. Do not claim Orca speech, high-contrast perception, DPI comfort, or installed-package
behavior from this source-tree audit; retain those as HITL gates.

Every defect found must be classified and recorded before editing. Harness-only drift belongs in the
audit script/tests; product behavior/layout belongs in a child plan entry and the existing Qt owner;
fixture gaps belong in a fixture-generation follow-up; subjective accessibility belongs in the HITL
matrix. After corrections, rerun the same checkpoints and compare before/after evidence.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    git status --short
    .venv/bin/pytest -q tests/integration/test_accessibility_acceptance.py tests/integration/test_signature_library_topology.py tests/integration/test_placement_profile_editor.py tests/integration/test_signing_rail_layout.py
    DISPLAY=:0 QT_QPA_PLATFORM=xcb PYTHONPATH="$PWD/src" .venv/bin/python scripts/live_gui_parent_audit.py --artifacts-dir /tmp/foliaseal-full-x11-audit

Use a unique temporary artifact/settings/runtime root rather than the example path if it already
exists. Inspect `audit.json` and every PNG at native scale. If the run fails, preserve the concise
exception and checkpoint evidence, terminate only the exact owned PID, remove only the exact owned
root, and update `Progress` before retrying with the next safe approach.

After implementation, run:

    .venv/bin/pytest -q
    .venv/bin/ruff check src tests scripts
    .venv/bin/python -m compileall -q src scripts
    git diff --check

## Validation and Acceptance

The audit passes when the no-document and open-document screenshots show the required topology and
readable labels; every representable menu/dialog/control has a verified title, state, keyboard path,
and observable action; the parent signing workflow reaches placement, signing, reopen/verify, and
second-signature checkpoints; and `audit.json` records no unexplained product or harness failures.
The minimum rail test must demonstrate non-zero usable widths for document-text and status controls.
Fixture-limited signed/restricted/multi-page states and HITL-only Orca/high-contrast/DPI/installed-
package evidence must be explicitly listed as remaining rather than marked pass.

## Idempotence and Recovery

All audit settings, certificates, profiles, signed PDFs, screenshots, and runtime endpoints must live
under one uniquely named temporary root. The audit must close every owned dialog and main window in a
`finally` path, terminate only its recorded process, and remove only its recorded root. Never close or
kill an unrelated user FoliaSeal process. Rerunning the audit should create a fresh root and must not
mutate repository fixtures or user configuration. If a dialog blocks the runner, add a bounded semantic
driver or classify the behavior as a harness issue; do not leave it open or abandon the plan.

## Artifacts and Notes

The allowed change slice is source-tree audit evidence, audit harness/test corrections, product GUI
corrections required by observed defects, ExecPlan/status documentation, and one focused commit. Do
not mix unrelated architecture refactors, schema changes, packaging changes, or generated screenshots
into the repository. Temporary evidence may remain outside the repository only while actively reviewed
and must be removed before completion unless the plan explicitly records a user-approved retention.

## Interfaces and Dependencies

Use the existing Qt binding seams and public AppFrame/workspace ports. Keep domain, persistence, and
signing policy out of the audit harness. Use `QApplication` event processing for semantic interaction,
the existing X11 helper for bounded native input/window activation, and the existing certificate/signing
builders for disposable workflow state. Optional AT-SPI probing is diagnostic evidence only; it cannot
replace observed keyboard/function checks or a real Orca HITL session.

## Revision Note

Created on 2026-08-21 after the explorer review of the current source-tree audit tooling. This plan
expands the prior layout-only verification into a complete rendered, keyboard, menu, dialog, and
workflow audit while preserving the frozen PDF-first topology and separating product defects from
harness, fixture, and HITL limitations.
