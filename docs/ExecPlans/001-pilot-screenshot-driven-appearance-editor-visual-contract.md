---
role: standalone
state: planned
depends_on: []
---

# Pilot a visual contract for the Appearance editor

This ExecPlan is a living document. Maintain Progress, Surprises & Discoveries, Decision Log, and Outcomes & Retrospective as implementation proceeds. Follow /home/daekar/.codex/skills/write-execplan/PLANS.md. This is a FoliaSeal project plan in docs/ExecPlans/.

## Purpose / Big Picture

A user should be able to create an Appearance in the Signature Library at its supported 1000 by 650 logical-pixel minimum without losing the labeled sample preview, Name field, or editor exit and Save actions. Long style controls should scroll while the preview and actions stay visible. This pilot also establishes a small native-Qt visual guide and proves a repeatable before/after capture and review method on one production surface. Open Signature Library, choose Appearances, then Create to see the result. The approved Appearance wireframe places Name and content controls in a left column and a sticky sample preview in a separate right column; preserve that relationship.

The work preserves the frozen PDF-first topology and transactional Save/Back behavior. A screenshot does not prove screen-reader speech, high-contrast legibility, physical-DPI readability, or installed-package release acceptance.

## Child ExecPlan Dependencies

- [x] No prerequisite ExecPlan. docs/UI_SPEC.md SUR03, SUR04, and section 12 govern this standalone pilot directly.

## Progress

- [ ] Capture the current Library Create Appearance state on real Cinnamon/X11 after requesting 1000 by 650 logical pixels. Record requested and actual geometry, display scale, and exact visible defects before changing layout code.
- [ ] Write docs/GUI_STYLE_GUIDE.md with restrained native-Qt rules demonstrated by this pilot and check its authority against docs/SPEC.md, docs/SCHEMAS.md, and frozen docs/UI_SPEC.md.
- [ ] Correct only baseline-proven Appearance-editor layout defects and preserve the sample preview, Name order, scrolling content, and Save/Back semantics.
- [ ] Add focused real-Qt geometry assertions; capture the same state after the change; inspect both images and obtain read-only visual review against the criteria below.
- [ ] Run focused and full validation, update this plan and any affected architecture/status documentation, decide whether shared metrics or a GUI skill are justified, and commit the bounded work in focused change classes.

## Surprises & Discoveries

No implementation discoveries yet. Initial source inspection found that AppearanceProfileEditorWidget._build_controls() sets a 500 by 560 container minimum, a 72-pixel-minimum text preview, a 240 by 96 image preview, a scrolling form, and Back/Save after the scroll area. The Library has a 1000 by 650 minimum and remembered splitter geometry. These are observations, not approved visual targets. A live capture must establish what is actually cramped or clipped.

## Decision Log

- Decision: Pilot the Library-owned Create Appearance state with a temporary empty catalog.
  Rationale: It is a bounded production path with previous density concerns and an existing real-Qt integration test. Temporary data avoids personal profiles and PDFs.
  Date/Author: 2026-09-17 / Codex.
- Decision: Keep the visual guide below frozen docs/UI_SPEC.md and defer a global metrics framework.
  Rationale: UI_SPEC intentionally leaves exact pixels and toolkit widgets open; one corrected surface does not justify a shared visual abstraction.
  Date/Author: 2026-09-17 / Codex.
- Decision: Capture only a synthetic, isolated Qt client; after checking it contains no personal data, retain before/after PNGs and geometry JSON as non-normative pilot evidence under docs/visual-evidence/appearance-pilot/.
  Rationale: the user needs a reviewable visual result. The capture must not include the desktop, user catalog, PDF, or certificate. Earlier audit images were temporary because they used live desktop state.
  Date/Author: 2026-09-17 / Codex.
- Decision: Treat the nested editor's current Back label as a navigation/transaction exit while recording that UI_SPEC SUR03 and the approved wireframe call the footer action Cancel.
  Rationale: the existing code connects Back to request_cancel. The label discrepancy must be reviewed without silently changing the frozen interaction contract in a layout fix.
  Date/Author: 2026-09-17 / Codex.
- Decision: Do not create a qt-gui-work skill in this slice.
  Rationale: the pilot should prove the capture, specify, implement, and review sequence before it becomes a reusable instruction set.
  Date/Author: 2026-09-17 / Codex.

## Outcomes & Retrospective

Implementation has not started. At completion, record what both captures showed, what changed, test results, remaining limits, and whether repeated evidence justifies shared Qt metrics or a dedicated GUI skill. Add canonical Verification records if changing state to complete.

## Context and Orientation

FoliaSeal is a Linux PDF signing application built with PySide6/Qt. docs/SPEC.md controls product scope, docs/SCHEMAS.md controls persistent signing objects, and frozen docs/UI_SPEC.md controls interface organization and interaction. UI_SPEC SUR03 requires a modeless three-column Signature Library with a fixed action footer. SUR04 requires a content-first Appearance editor with a sticky, labeled synthetic sample preview that is never saved. Section 12 requires a 1000 by 650 logical-pixel Library minimum, system font and scale, native palette, and unchanged actual Appearance/PDF colors across themes. A logical pixel is Qt's layout unit before display pixel scaling.

src/foliaseal/presentation/qt/app_frame_profile_library.py owns ReusableObjectLibraryDialog, its splitter, and the production Create Appearance route. Its initial dialog size is 1100 by 700, although its minimum is 1000 by 650; Qt or the window manager may enforce a larger effective size after a resize request. src/foliaseal/presentation/qt/appearance_profile_editor_widget.py owns AppearanceProfileEditorWidget._build_controls() and a public controls record containing the container, breadcrumb, sample preview labels, Name input, setup form, Save button, and visible Back button (named cancel_button in code). It does not expose the preview heading, Name label, scroll area, or action row; tests must locate these by stable object names or add narrow controls fields. src/foliaseal/presentation/qt/visible_signature_setup_form.py owns the embedded form content. tests/integration/test_signature_library_topology.py::test_library_real_qt_mounts_nested_appearance_editor already builds an isolated Qt frame with temporary stores, opens Appearances > Create, and proves Save persists a new item. It does not prove Back/cancel behavior; add that assertion or narrow the acceptance claim.

docs/ExecPlans/gui_surface_layout_correction_execplan.md records earlier cramped surfaces. docs/ExecPlans/x11_visual_layout_audit_execplan.md records successful QWidget.grab() capture of an owned Qt client; a desktop screenshot helper previously captured the wrong window. scripts/live_gui_accessibility_audit.py has an opt-in capture/report pattern for the no-document frame. Reuse its ownership and cleanup principles, without coupling this pilot to its F1/Help audit. A display-backed capture means QT_QPA_PLATFORM=xcb and a working X11 DISPLAY. Qt offscreen is useful for geometry tests but is not the final visual image.

## Milestones

Milestone 1 yields a reproducible baseline and an explicit discrepancy statement. Create a fresh-process script, scripts/capture_appearance_layout.py, which builds the isolated Library state from temporary stores. After opening the editor, request 1000 by 650 on the Library dialog, process Qt events, and use QWidget.grab() on that dialog. Record requested and actual client dimensions, device-pixel ratio, QApplication.style().objectName(), palette window color, splitter widths, and whether preview, Name, Back, and Save are visible without scrolling. If actual geometry exceeds the supported minimum, record that as a defect rather than reporting the requested size as achieved. Inspect the PNG and compare it with docs/ui/appearance-profile-editor-exploratory.svg. If X11 is unavailable, run offscreen geometry checks but leave the display-backed gate open.

Milestone 2 yields a short docs/GUI_STYLE_GUIDE.md. State the governing-document order and specify native Qt layout, system font/palette, spacing, minimum versus initial size, scroll ownership, stable action rows, headings, labels, and wrapping. Explain that PDF and Appearance sample colors may remain white or use their actual color. Include the Appearance pilot as an example. Avoid blanket fixed pixel rules, new product capabilities, and changes to the frozen UI_SPEC or its SVGs.

Milestone 3 fixes only defects seen in the baseline image. Adjust AppearanceProfileEditorWidget._build_controls() and, if the host or splitter sizing causes the problem, the smallest relevant part of ReusableObjectLibraryDialog._build_controls(). Preserve the approved content column with Name first and the sticky sample preview in a separate adjacent area. Keep exit/Save reachable while content controls scroll. Prefer layout stretch, size policies, wrapping, and font metrics to new fixed heights. If that approved topology cannot fit at the specified minimum, document the exact contradiction and obtain an approved UI decision before changing topology. Preserve system palette behavior and intentional Appearance/PDF sample colors. No domain, persistence, signing, or package code belongs in this milestone.

Milestone 4 proves behavior and appearance. Extend the existing real-Qt integration test or add a focused adjacent test for required control geometry and non-overlap at the Library minimum. Check that scrolling the long form does not move preview or actions, that Save persists, and that Back exits losslessly after handling the dirty-change prompt. Repeat the X11 capture with the same data, style, requested geometry, splitter, and scale. Give a read-only visual reviewer both images, UI_SPEC SUR03/SUR04, its normative SVG, the guide, and the acceptance criteria. Record each finding and disposition, then run focused tests, Ruff, and the full suite. A default-state image cannot prove focus appearance: create a keyboard-focus capture or leave that claim to a live keyboard check.

## Plan of Work

Preserve the existing Git state. Add a small fresh-process scripts/capture_appearance_layout.py entrypoint based on the temporary-store setup in tests/integration/test_signature_library_topology.py, without importing the pytest module. It accepts --artifacts-dir and --phase before|after, creates a fresh QApplication and temporary stores with the same empty catalog and explicit initial UI settings for each phase, opens the Library editor, explicitly resizes to the requested minimum and applies the same splitter sizes, processes events, captures library.controls.dialog.grab(), and writes a PNG plus small geometry JSON under the supplied root. Report requested and actual dimensions, display scale, style name, palette window color, and actual splitter sizes and widget rectangles. Fail if the target is hidden, the capture is null, or actual size is not recorded. Do not screenshot the desktop. Close the Library and frame on both success and failure.

Write the guide and baseline observations before editing layout, so the intended visual change is explicit. Keep the guide in a documentation/status commit, the Qt source plus focused test/capture script in a behavior commit, and sanitized before/after PNG/JSON evidence in a separate evidence commit. Review each capture for private text before staging it. If the baseline shows no material defect, avoid gratuitous Qt churn: document the observed good state, retain the guide and repeat capture, and explain that result in the retrospective.

After the change, compare the same state and record geometry, hierarchy, wrapping, focus, and readability findings. Update docs/ARCHITECTURE.md only if ownership or public seams change; routine widget sizing does not require an architecture rewrite. Reconcile this plan before committing. Do not close unrelated release/HITL plans.

## Concrete Steps

Run commands from /home/daekar/FoliaSeal. Use the existing .venv if available; otherwise follow README.md to create the development environment. Do not install packages or alter the host desktop merely for this pilot.

    git status --short --branch
    rg -n 'SUR03|SUR04|1000×650|native palette' docs/UI_SPEC.md
    .venv/bin/python -m pytest -q tests/integration/test_signature_library_topology.py

Create an owned temporary root with mktemp -d /tmp/foliaseal-appearance-pilot.XXXXXX. After adding the script, run the two commands below from separate fresh processes with the same DISPLAY and QT_QPA_PLATFORM=xcb. The script must request 1000 by 650 after opening the editor and report actual dimensions; never assume Qt honored the request. PNG pixel dimensions may vary with device-pixel ratio. Replace the example root with the exact mktemp result, then update this section with observed output.

    QT_QPA_PLATFORM=xcb .venv/bin/python scripts/capture_appearance_layout.py --artifacts-dir /tmp/foliaseal-appearance-pilot.EXAMPLE --phase before
    QT_QPA_PLATFORM=xcb .venv/bin/python scripts/capture_appearance_layout.py --artifacts-dir /tmp/foliaseal-appearance-pilot.EXAMPLE --phase after

    QT_QPA_PLATFORM=xcb .venv/bin/python -m pytest -q tests/integration/test_signature_library_topology.py -k appearance_editor
    .venv/bin/python -m pytest -q tests/integration/test_signature_library_topology.py
    .venv/bin/ruff check src/foliaseal/presentation/qt tests/integration/test_signature_library_topology.py
    .venv/bin/python -m pytest -q
    git diff --check

Record concise observed output and the exact baseline discrepancy here. Inspect the images with an image viewer or view_image. After confirming the isolated client images contain only synthetic data, copy the two PNGs and JSON reports to docs/visual-evidence/appearance-pilot/ and mark them non-normative in a short README there. Remove only the owned temporary root after that reviewable evidence is staged. Check git status --short before and after focused commits.

## Validation and Acceptance

At the supported Library minimum, Appearances > Create shows the complete synthetic-preview label and sample, Name label and input, and editor exit/Save without clipping or horizontal scrolling. Name and content remain in the content column while the sticky sample remains in a separate adjacent area, following the approved SVG. Exit and Save remain reachable and stationary while long style controls scroll. Controls remain keyboard reachable. Save creates the Appearance; the current Back action exits losslessly through its confirmation path. Record the Back-versus-Cancel label discrepancy without silently changing the frozen contract. The synthetic sample does not become persisted signer data.

The test must inspect effective Qt geometry after layout events: positive visible rectangles for required controls within the Library client, no overlap between preview/content/footer regions, and reachable content in the scroll area. It must fail if actual dialog dimensions exceed the specified minimum, rather than treating a resize request as success. Add stable object names or narrow controls fields for the currently unexposed label, scroll area, and action-row widgets. Do not assert one font's exact line breaks or fragile absolute coordinates. The image reviewer assesses reading order, density, wrapping, and action hierarchy; focus needs a deliberate focused-state capture or live keyboard check. Record image-only unknowns as unverified.

Accept the pilot only after focused integration tests, Ruff, full pytest, source/spec consistency review, and real-X11 visual comparison pass. If the display is unavailable, state remains short of complete and the missing gate is recorded. This pilot does not satisfy Orca, high contrast, physical DPI, or installed-package release gates.

## Idempotence and Recovery

The test and script use temporary settings/catalog stores and create no real certificate, PDF signing output, or personal profile. Repeated capture may replace files only within the caller-owned phase directory. Never delete an unspecified /tmp path or user XDG data. Close Library and frame after each run. If capture fails, retain a concise error, clean up the owned process, and retry when X11 is available. Do not stage a capture until it has been inspected for private data. If layout work breaks transactions, revise the change rather than modifying frozen UI_SPEC or user data.

## Artifacts and Notes

At implementation time, record Git baseline, exact capture command and private temporary root, requested/actual geometry, PNG dimensions/hashes, theme/DPI/splitter geometry, before/after observations, reviewer findings, test summaries, and commit hashes. The tracked outputs are this plan, docs/GUI_STYLE_GUIDE.md, focused Qt source only if justified by the baseline, focused test/capture code, and sanitized non-normative PNG/JSON/README evidence under docs/visual-evidence/appearance-pilot/. Do not commit real profile data, PDFs, certificates, packages, desktop screenshots, or unrelated refactors.

## Interfaces and Dependencies

Use the existing PySide6/Qt stack; add no runtime dependency. The script capture interface accepts a caller-owned artifact directory and explicit phase ('before' or 'after'), reports PNG and JSON paths, and runs only when invoked. It uses QWidget.grab() on the owned Library QDialog from a fresh QApplication process. Keep AppearanceProfileEditorWidgetControls and ReusableObjectLibraryControls as narrow test-facing surfaces; add only widget references needed for reliable geometry checks. Do not move visual policy into domain/application code. Use QStyle, QFontMetrics, QPalette, layout size policies, and existing Qt scrolling primitives where measured evidence warrants them. Preserve Save and request_cancel callbacks and remembered Library splitter settings.

Revision note (2026-09-17): Replaced the generated helper draft with a single-surface pilot. The scope follows the user's decision to test a guide and screenshot-driven GUI loop before standardizing shared metrics or a dedicated skill.

Revision note (2026-09-17): Reviewer findings corrected the approved content/preview topology, clarified Back versus normative Cancel, made minimum-size measurement and capture commands executable, and retained sanitized pilot images so future reviewers can inspect the evidence.

Revision note (2026-09-17): A final code-path review required deterministic empty stores and identical initial splitter settings for both capture phases, with actual splitter sizes recorded.
