# Correct Appearance editor preview and signing-rail geometry

This ExecPlan is a living document and must remain self-contained under
`/home/daekar/.codex/skills/write-execplan/PLANS.md`. It is Child 2 of
`docs/ExecPlans/gui_hitl_defect_recovery_parent_execplan.md`.

## Purpose / Big Picture

After this slice, a user opening Manage reusable signing objects can create or edit an Appearance
without manually resizing the window to find controls, can see a useful synthetic preview that reflects
the current text and imported image choices, and can save or cancel without corrupting the parent draft.
Opening a PDF will also leave the fixed right signing rail wide enough to use; it will not silently
collapse until the user drags a divider.

This corrects the observed undersized Appearance editor, non-representative preview, and unusably narrow
document signing pane. It preserves the modeless master-detail Library, fixed right rail, existing
transactional Save/Cancel semantics, and authoritative on-page preview.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md`, `docs/UI_SPEC.md`, and `docs/SCHEMAS.md` are available and authoritative.
- [x] `docs/ExecPlans/ui_appearance_editor_transaction_execplan.md` supplies the nested Appearance
  editor transaction and cleanup seams.
- [x] `docs/ExecPlans/ui_library_geometry_persistence_execplan.md` and
  `docs/ExecPlans/ui_rail_divider_persistence_execplan.md` are existing geometry owners; inspect and
  extend them instead of creating a second persistence key.
- [x] `docs/ExecPlans/gui_hitl_defect_recovery_parent_execplan.md` records the observed evidence.
- [x] Child 1 certificate-surface corrections were completed in the integrated layout slice;
  Child 4 still depends on this child for installed-package and human acceptance.

## Progress

- [x] (2026-08-20) Confirmed `AppearanceProfileEditorWidget` already has a scroll area, a labeled
  synthetic preview, and Save/Back controls, while the Library sets a 1000×650 minimum.
- [x] (2026-08-20) Confirmed the document rail is assembled by
  `signing_workspace_composition.py` and has a persisted splitter boundary.
- [x] (2026-08-20) Explorer review confirmed the sidebar has a 280–640 pixel splitter range and the
  restored width defaults to 320 only after the splitter has usable width; measurement of actual rail,
  splitter, scroll, and clipped-control widths is required before changing the geometry owner.
- [x] (2026-08-20) Reproduce the relevant geometry through real offscreen Qt coverage and retain the
  existing 320-pixel initial rail / 280–640-pixel adjustable range proof.
- [x] (2026-08-20) Add tests for reachable editor geometry, visible synthetic preview state, and image
  preview controls; existing rail persistence tests continue to prove non-collapsing restoration.
- [x] (2026-08-20) Implement explicit editor minimum/default geometry, image-aware synthetic preview,
  and Library geometry clamping without changing the frozen topology.
- [x] (2026-08-20) Run focused validation: 148 Library/signing-shell tests and 3 real offscreen rail
  integration tests passed.
- [x] (2026-08-20) Display-backed source-tree audit at 1920×1048 exposed additional rail defects before
  menu navigation: the fixed-width rail horizontally clips the preset/certificate rows, the synthetic
  preview is reduced to a shallow cramped strip, the document-text toolbar truncates button labels, and
  long status/detail copy wraps into an over-constrained column. These are visible at native capture
  scale and are not merely screenshot downscaling.
- [x] (2026-08-20) Added the real-Qt minimum-width rail assertion: at the legal 280-pixel minimum,
  query/navigation controls and status/detail labels retain non-zero usable widths.
- [x] (2026-08-20) Source-tree correction validated in the integrated layout slice: 143 focused tests,
  then 1,605 full-suite tests passed with 20 skips; Ruff, compileall, and diff checks passed. A fresh
  bounded X11 sweep confirmed the corrected Library/editor and rail surfaces and cleaned its process
  and temporary root.
- [x] (2026-08-20) Reconciled this child with the integrated correction plan and architecture map;
  installed-package and human acceptance remain in Child 4.

## Surprises & Discoveries

- Observation: the Appearance editor preview is currently a text label with a fixed 72-pixel minimum,
  not necessarily a rendered representation of the selected image/content.
  Evidence: `appearance_profile_editor_widget.py::_build_controls` creates a label titled
  `Sample preview (synthetic data — never saved)` and `_refresh_preview()` updates its text.
- Observation: the Library already declares a 1000×650 minimum and places the editor in a scroll area,
  so the human failure may come from the initial window size, splitter allocation, or nested editor
  minimums rather than absence of scrolling.
  Evidence: `app_frame_profile_library.py` sets `MIN_LIBRARY_WIDTH`/`MIN_LIBRARY_HEIGHT` and uses
  `detail_scroll_area`.
- Observation: the signing rail is a vertical splitter with remembered sizes, which can restore a
  stale or zero-width right pane if the projection does not enforce the product minimum.
  Evidence: `signing_workspace_composition.py` creates `rail_splitter`, applies saved sizes, and
  exposes `RailDividerState`.
- Observation: the normal production splitter prevents a rail below 280 pixels, so the human report
  may be an inner-control clipping problem at 280 pixels rather than a collapsed sidebar.
  Evidence: `SigningWorkspaceSidebar.RAIL_MIN_WIDTH = 280`, `RAIL_MAX_WIDTH = 640`, and delayed
  restoration in `signing_workspace_composition.py`.
- Observation: the maximized source-tree window has a visible 320-ish right rail, but its horizontal
  child layouts still clip meaningful content: preset/certificate selectors truncate, the synthetic
  preview is too shallow to communicate the intended signed-PDF comparison, document-text buttons lose
  their labels, and workflow/status prose is squeezed into narrow wrapped lines.
  Evidence: native X11 capture `/tmp/foliaseal-dev-hitl-fFnbwy/source-maximized.png` from the isolated
  source-tree session; no menus were opened for this observation.
- [x] (2026-08-20) Completed a broader source-tree surface sweep. The Library opens at 1100×700, but
  its nested Appearance editor compresses controls in the detail column, the Preset editor leaves a
  large unused upper region while packing its workflow controls into a narrow lower band, and the
  Edit Placement dialog measures only 236×347 with clipped copy. These surfaces remain within Child 2’s
  Library/editor geometry ownership and must be corrected without changing the three-column topology.

## Decision Log

- Decision: enforce the documented Library minimum and editor scroll behavior rather than inventing a
  compact alternate layout.
  Rationale: UI_SPEC §12 explicitly says V1 has no alternate compact/mobile layout and the Library
  must preserve three columns.
  Date/Author: 2026-08-20 / Codex.
- Decision: use the existing preview/rendering seams where possible; any synthetic preview must remain
  visibly labeled and must never be persisted as an Appearance or signing artifact.
  Rationale: UI_SPEC SUR04 requires a sticky synthetic preview while the document on-page preview remains
  authoritative; duplicating rendering logic would create parity drift.
  Date/Author: 2026-08-20 / Codex.
- Decision: enforce a safe initial rail width and clamp restored divider sizes, but preserve an explicit
  user-adjusted width when it is valid.
  Rationale: the rail must not auto-collapse, while user-adjustable remembered geometry is normative.
  Date/Author: 2026-08-20 / Codex.
- Decision: do not move the Library into the main workspace or replace the right rail with a modal
  setup dialog.
  Rationale: those changes would violate SUR01–SUR04 and erase the spatial memory that this correction
  is meant to stabilize.
  Date/Author: 2026-08-20 / Codex.

## Outcomes & Retrospective

The initial state is a usable but misleading Appearance editor and a rail that can become too narrow.
At completion, the child should have geometry tests proving every required control is reachable at the
minimum, preview tests proving text/image edits visibly update the labeled sample, and splitter tests
proving the rail retains a safe width across document open and settings restore. Record any preview
fidelity limitation explicitly rather than claiming signed-output parity from a synthetic preview.

## Context and Orientation

`src/foliaseal/presentation/qt/app_frame_profile_library.py` owns the modeless three-column Library,
its catalog navigation, detail editor host, scroll area, buttons, and saved geometry. Its nested editor
host mounts `AppearanceProfileEditorWidget` from
`src/foliaseal/presentation/qt/appearance_profile_editor_widget.py`, which owns a staged Appearance
draft, image imports, synthetic sample preview, and Save/Back transaction. The shared
`QtVisibleSignatureSetupForm` supplies appearance controls and image callbacks.

`src/foliaseal/presentation/qt/signing_workspace_composition.py` assembles the PDF viewer and right
signing rail in a splitter. `SignaturePropertiesPanel` in
`signing_workspace_properties_panel.py` owns certificate/preset/placement controls and the read-only
status region. Settings projection and persistence already have dedicated owners; use their typed
geometry contracts.

## Plan of Work

Start with a real PySide6 offscreen mount of the Library at 1000×650 and of the main frame at 1100×700.
Record widget minimum sizes, effective splitter sizes, scroll-bar presence, and whether Save/Back and
all image/content controls are visible. Add failing tests that assert behavior, not platform-specific
pixel coordinates: the editor is scrollable, the footer remains reachable, the preview remains visible
while controls scroll, and the window cannot restore below its contract minimum.

Inspect `_refresh_preview()` and the shared preview/render primitives. If the current text-only sample
cannot show the selected image or meaningful field content, compose a small synthetic render using the
existing appearance preview seam (or extract a reusable pure preview projector first). It must show
the current image when one is staged, show representative visible fields when text is selected, update
after control changes, and retain the explicit “synthetic data — never saved” label. Do not write a
synthetic signer name or image into the persisted `SignatureAppearance`.

Then reproduce the right-pane shrink by opening a PDF from a fresh and a restored settings root. Before
changing geometry code, record `sidebar.container.width()`, splitter sizes, properties-scroll width,
status-region width, and the specific controls that clip at each state. Trace the splitter’s initial
sizes, minimum widths, and post-`showMaximized()` reapplication. Only if the evidence shows a projection
or restoration defect should the child change the typed projection; it must reject zero/negative/stale
values, enforce the approximately 320 logical-pixel rail baseline and protected lower status minimum,
and still honor a valid user-adjusted divider. If the rail is correctly 280 pixels wide but inner
controls are clipped, fix the owning child layout instead. The rail must scroll internally and never
auto-collapse when the document changes.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`.

    rg -n "MIN_LIBRARY|AppearanceProfileEditorWidget|detail_scroll_area|rail_splitter|library_splitter_sizes" src tests
    .venv/bin/pytest -q tests/unit/test_qt_app_frame_profile_library.py tests/unit/test_qt_appearance_image_lifecycle.py tests/unit/test_qt_signing_rail_stage_status.py tests/unit/test_qt_signing_workspace_composition.py
    .venv/bin/ruff check src/foliaseal/presentation/qt/app_frame_profile_library.py src/foliaseal/presentation/qt/appearance_profile_editor_widget.py src/foliaseal/presentation/qt/signing_workspace_composition.py src/foliaseal/presentation/qt/signing_workspace_properties_panel.py tests/unit

After implementation, run:

    .venv/bin/pytest -q tests/unit/test_qt_app_frame_profile_library.py tests/unit/test_qt_appearance_image_lifecycle.py tests/unit/test_qt_signing_rail_stage_status.py tests/unit/test_qt_signing_workspace_composition.py tests/unit/test_qt_app_frame_workspace_open.py
    .venv/bin/pytest -q
    .venv/bin/ruff check src tests
    .venv/bin/python -m compileall -q src
    git diff --check

Use an isolated display-backed audit root for visual verification. At 100% scaling, open Manage
reusable signing objects, enter Appearance Create/Edit, record editor and inner-control geometry before
manually resizing, and verify
the initial layout already exposes the preview and an obvious path to every control. Open the fixture
PDF and verify that the right rail remains usable without dragging its divider.

## Validation and Acceptance

The child passes when:

- Library Create/Edit starts at or above 1000×650, preserves three columns, keeps the nested editor
  scrollable, and leaves Save/Back reachable.
- The synthetic preview is visible without hiding the controls, is labeled as synthetic, updates for
  text and staged image changes, and never persists its sample data.
- The main frame honors the 1100×700 minimum; the rail starts approximately 320 logical pixels wide,
  retains a protected status region, and never becomes unusably narrow after opening a document or
  restoring settings.
- Valid user-adjusted divider sizes persist and invalid/legacy sizes recover safely.
- Focused tests, full suite, Ruff, compileall, and diff checks pass.

## Idempotence and Recovery

Geometry tests use fake settings and isolated temporary roots. Do not overwrite the user’s saved UI
settings. If a stale divider value is encountered, test the migration/fallback path rather than editing
the user file manually. Staged image imports must be deleted only through the editor’s owned cleanup
seam when a draft is discarded. Any X11 audit window or process must be identified by its unique title
and closed after observation.

## Artifacts and Notes

The commit may contain only Appearance/Library/rail source, focused tests, this plan, and narrow status
documentation. Do not commit screenshots with document content or machine-local geometry. Preserve safe
evidence such as effective minimum sizes, splitter sizes before/after open, and preview update assertions.

## Interfaces and Dependencies

Use `AppearanceProfileEditorWidgetControls`, `QtVisibleSignatureSetupForm`,
`ReusableSigningObjects`, `RailDividerState`, `LibraryGeometry`, and the existing AppSettings UI
projection. If a preview projector is extracted, make it Qt-independent and return a render model or
safe image/text inputs; the widget remains responsible for presentation and the catalog remains
responsible for persistence. Do not make the main AppFrame own appearance internals or create a second
rail state store.

## Revision Note

Revised on 2026-08-20 after the required explorer review to distinguish the intentional text-only
synthetic preview from editor geometry, and to require measured rail/splitter/inner-control widths
before changing a rail implementation that already enforces a 280–640 pixel range.
