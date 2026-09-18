---
role: standalone
state: complete
depends_on: []
---

# Pilot a visual contract for the Appearance editor

This ExecPlan is a living document. Maintain Progress, Surprises & Discoveries, Decision Log, and Outcomes & Retrospective as implementation proceeds. Follow /home/daekar/.codex/skills/write-execplan/PLANS.md. This is a FoliaSeal project plan in docs/ExecPlans/.

## Purpose / Big Picture

A user should be able to create an Appearance in the Signature Library at its supported 1000 by 650 logical-pixel minimum without losing the labeled sample preview, Name field, or Cancel and Save actions. Long style controls should scroll while the preview and actions stay visible. This pilot also establishes a small native-Qt visual guide and proves a repeatable capture, correction, and review loop on one production surface. Open Signature Library, choose Appearances, then Create to see the result. The approved Appearance wireframe places Name and content controls in a left column and a sticky sample preview in a separate right column; preserve that relationship.

The work preserves the frozen PDF-first topology and transactional Save/cancel behavior. The current nested editor says Back where the governing UI_SPEC and wireframe say Cancel; this slice corrects the label without changing its lossless exit behavior. A screenshot does not prove screen-reader speech, high-contrast legibility, physical-DPI readability, or installed-package release acceptance.

## Child ExecPlan Dependencies

- [x] No prerequisite ExecPlan. docs/UI_SPEC.md SUR03, SUR04, and section 12 govern this standalone pilot directly.

## Progress

- [x] (2026-09-18 18:35Z) Captured the real Cinnamon/X11 baseline at an actual 1000 by 650 client, Ubuntu 10 pt font, Fusion dark style, DPR 1.0, and 180/280/516 splitter widths. The stacked preview was illegible on white in the dark palette; content rows clipped behind horizontal scrolling, and Back/Save were confined to the detail column.
- [x] (2026-09-18 18:38Z) Wrote docs/GUI_STYLE_GUIDE.md as provisional pilot guidance subordinate to the frozen UI_SPEC; it adds no product capability or change to persistent object semantics.
- [x] (2026-09-18 18:41Z) Built three candidates: adjacent content/preview and Cancel label; compact vertical controls with no horizontal scrolling and more detail width; then a Library-wide stationary footer. Focused Qt tests and Ruff pass.
- [x] (2026-09-18 20:26Z) Completed the visual gate after the owner approved one focused fourth pass. Main-thread review loaded the baseline, candidate-4 default, and candidate-4 scrolled PNGs; the blank image box is absent, native Save emphasis and compact right-aligned actions are visible, and the preview/footer remain stable during form scrolling. No material finding remains in these states.
- [x] (2026-09-18 20:26Z) Full validation passed: 1666 passed, 20 skipped, one existing Pillow deprecation warning; Ruff and diff whitespace checks passed. Retained synthetic before/default/scrolled PNG and JSON evidence and reconciled the guide, architecture document, and this plan.

## Surprises & Discoveries

- Observation: the X11 socket exists but was inaccessible inside the managed sandbox; xrandr and the isolated Qt capture succeeded with approved unsandboxed execution. Evidence: the first xcb attempt failed to connect to :0; the same capture command outside the sandbox wrote before-default.png.
- Observation: the baseline at 1000 by 650 had an unreadable white sample under the dark system palette, horizontal clipping in the form, and a stacked preview. Evidence: /tmp/foliaseal-appearance-pilot-20260918/before-default.png and before-default.json.
- Observation: compacting the Appearance-only form removed horizontal scrolling while keeping the shared form's non-compact route and all existing data controls. Reducing catalog/master minimum widths to 120/180 gave the detail 676 logical pixels at the Library minimum. Evidence: candidate-2-default.png, candidate-2-scrolled.png, and focused Qt tests.
- Observation: the third candidate moves the editor action row beneath all three Library columns and keeps preview/footer coordinates stationary while the form scrolls. The equal-width footer actions and blank image sample remain visual judgments for the owner after the three-candidate cap. Evidence: candidate-3-default.png, candidate-3-scrolled.png, and the focused minimum-layout test.
- Observation: the owner approved one focused fourth pass. Qt's app-frame bindings lacked the pixmap factory the Appearance preview already expected, so its no-image visibility logic returned early. Candidate 4 hides the sample without an image, supplies QPixmap for a selected image, and uses a native default Save button with compact right-aligned actions. The final direct PNG review found no material discrepancy. Evidence: docs/visual-evidence/appearance-pilot/after-default.png and after-scrolled.png.
- Observation: asynchronous X11 show geometry briefly made a scrolled candidate-4 capture 1100 by 700 even though the request was 1000 by 650. The capture script now settles and verifies the size before saving; retained default and scrolled reports both record 1000 by 650 with identical style, font, DPR, screen, palette, and splitter widths.

## Decision Log

- Decision: Pilot the Library-owned Create Appearance state with a temporary empty catalog.
  Rationale: It is a bounded production path with previous density concerns and an existing real-Qt integration test. Temporary data avoids personal profiles and PDFs.
  Date/Author: 2026-09-17 / Codex.
- Decision: Keep the visual guide below frozen docs/UI_SPEC.md and defer a global metrics framework.
  Rationale: UI_SPEC intentionally leaves exact pixels and toolkit widgets open; one corrected surface does not justify a shared visual abstraction.
  Date/Author: 2026-09-17 / Codex.
- Decision: Capture only a synthetic, isolated Qt client; after checking it contains no personal data, retain before-default, final after-default, and final after-scrolled PNGs with geometry JSON as non-normative pilot evidence under docs/visual-evidence/appearance-pilot/.
  Rationale: the user needs a reviewable visual result. The capture must not include the desktop, user catalog, PDF, or certificate. Earlier audit images were temporary because they used live desktop state.
  Date/Author: 2026-09-17 / Codex.
- Decision: Correct the nested Appearance editor's visible Back label to Cancel in this presentation slice, while retaining its request_cancel callback, dirty-change prompt, and lossless exit behavior.
  Rationale: UI_SPEC SUR03 and the approved wireframe govern the label; existing implementation wording is lower authority. The correction is local to this surface and does not change the transaction.
  Date/Author: 2026-09-18 / Codex.
- Decision: Reopen implementation after every material visual-review finding, with up to three autonomous candidate review cycles.
  Rationale: the feedback loop, rather than screenshot generation alone, is the pilot. If three candidates leave material findings, present the captures and disputed criteria to the owner for a decision; do not mark the plan complete.
  Date/Author: 2026-09-18 / Codex.
- Decision: Do not create a qt-gui-work skill in this slice.
  Rationale: the pilot should prove the capture, specify, implement, and review sequence before it becomes a reusable instruction set.
  Date/Author: 2026-09-17 / Codex.
- Decision: Keep the style guide provisional until the visual pilot passes, and perform the image gate in the main thread or with a vision-capable high-reasoning reviewer.
  Rationale: a proposed guide is not yet proven across even one full correction loop, and subtle visual judgment should not default to a lightweight read-only reviewer.
  Date/Author: 2026-09-18 / Codex.
- Decision: Accept one focused fourth candidate after the owner selected “One more pass (Recommended)” at the three-candidate gate.
  Rationale: candidate 3 still had two concrete material findings. The approved pass corrected those findings, was recaptured under comparable X11 conditions, and passed direct main-thread review.
  Date/Author: 2026-09-18 / Owner and Codex.

## Outcomes & Retrospective

The pilot completed after four reviewed candidates, with the fourth explicitly approved by the owner. The capture/review loop found dark-theme sample contrast, horizontal form clipping, misplaced footer actions, weak action hierarchy, and a blank image sample that ordinary functional tests had not exposed. The accepted Appearance editor keeps Name and scrollable controls beside a readable stationary synthetic preview, with a stable Library-wide footer. A focused real-Qt test proves minimum-size geometry and dirty-Cancel losslessness. The guide is established for this Qt realization, subordinate to UI_SPEC. The pilot supports a future screenshot-driven GUI skill, while a shared Qt metrics framework remains deferred until more surfaces demonstrate recurring values. This evidence does not claim high-contrast, physical-DPI, keyboard-focus, or installed-package acceptance.

Verification:
- Action: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q`
  Result: pass
  Evidence: 1666 passed, 20 skipped, one existing Pillow deprecation warning in 50.79 seconds on 2026-09-18.
- Action: `.venv/bin/ruff check .` and `git diff --check`
  Result: pass
  Evidence: final checks on 2026-09-18; Ruff reported All checks passed and diff whitespace output was empty.
- Action: direct main-thread review of `before-default.png`, `after-default.png`, and `after-scrolled.png`
  Result: pass
  Evidence: `docs/visual-evidence/appearance-pilot/`; paired JSON reports record matching 1000 by 650 X11 client, Fusion, Ubuntu 10 pt, DPR 1.0, and DP-4.
- Action: `execplan-helper check docs/ExecPlans/001-pilot-screenshot-driven-appearance-editor-visual-contract.md`
  Result: pass
  Evidence: installed helper binary reported PASS on 2026-09-18; Cargo wrapper could not write its build lock in the read-only skill directory.

## Context and Orientation

FoliaSeal is a Linux PDF signing application built with PySide6/Qt. docs/SPEC.md controls product scope, docs/SCHEMAS.md controls persistent signing objects, and frozen docs/UI_SPEC.md controls interface organization and interaction. UI_SPEC SUR03 requires a modeless three-column Signature Library with a fixed action footer. SUR04 requires a content-first Appearance editor with a sticky, labeled synthetic sample preview that is never saved. Section 12 requires a 1000 by 650 logical-pixel Library minimum, system font and scale, native palette, and unchanged actual Appearance/PDF colors across themes. A logical pixel is Qt's layout unit before display pixel scaling.

src/foliaseal/presentation/qt/app_frame_profile_library.py owns ReusableObjectLibraryDialog, its splitter, the production Create Appearance route, and the Library-wide nested Appearance footer. Its initial dialog size is 1100 by 700, although its minimum is 1000 by 650; Qt or the window manager may briefly apply a larger show size after a resize request. src/foliaseal/presentation/qt/appearance_profile_editor_widget.py owns AppearanceProfileEditorWidget._build_controls() and a public controls record containing the container, breadcrumb, sample preview labels, Name input, setup form, Save/Cancel buttons, form scroll area, and action row. Cancel still routes through request_cancel. src/foliaseal/presentation/qt/visible_signature_setup_form.py owns the embedded form content, with a compact Appearance-only composition. tests/integration/test_signature_library_topology.py contains the isolated Save path and a separate minimum-layout, scrolling, and dirty-Cancel check.

docs/ExecPlans/gui_surface_layout_correction_execplan.md records earlier cramped surfaces. docs/ExecPlans/x11_visual_layout_audit_execplan.md records successful QWidget.grab() capture of an owned Qt client; a desktop screenshot helper previously captured the wrong window. scripts/live_gui_accessibility_audit.py has an opt-in capture/report pattern for the no-document frame. Reuse its ownership and cleanup principles, without coupling this pilot to its F1/Help audit. A display-backed capture means QT_QPA_PLATFORM=xcb and a working X11 DISPLAY. Qt offscreen is useful for geometry tests but is not the final visual image.

## Milestones

Milestone 1 yields a reproducible baseline and an explicit discrepancy statement. Create a fresh-process script, scripts/capture_appearance_layout.py, which builds the isolated Library state from temporary stores. After opening the editor, request 1000 by 650 on the Library dialog, process Qt events, and use QWidget.grab() on that dialog. Record requested and actual client dimensions, device-pixel ratio, QApplication.style().objectName(), palette window color, effective QApplication font family, point or pixel size, QFontMetrics.height(), splitter widths, and whether preview, Name, current Back, and Save are visible without scrolling. A window manager may return a larger client; record that outcome and inspect its cause rather than treating it as an automatic defect or as proof of 1000-by-650 usability. A separate controlled real-Qt geometry test must exercise the 1000-by-650 minimum. Inspect the before-default PNG and compare its topology and hierarchy with docs/ui/appearance-profile-editor-exploratory.svg without matching pixels. If X11 is unavailable, run offscreen geometry checks but leave the display-backed gate open.

Milestone 2 yields a short docs/GUI_STYLE_GUIDE.md headed “Status: Pilot/provisional.” State that it is subordinate to UI_SPEC.md and becomes established project guidance only when this Appearance-editor pilot completes successfully. State the governing-document order and specify native Qt layout, system font/palette, spacing, minimum versus initial size, scroll ownership, stable action rows, headings, labels, and wrapping. Explain that PDF and Appearance sample colors may remain white or use their actual color. Include the Appearance pilot as an example. Avoid blanket fixed pixel rules, new product capabilities, and changes to the frozen UI_SPEC or its SVGs.

Milestone 3 fixes baseline-proven defects, including the source-visible stacked preview if the capture confirms it, plus the known Back label conflict. Adjust AppearanceProfileEditorWidget._build_controls() and, if the host or splitter sizing causes the problem, the smallest relevant part of ReusableObjectLibraryDialog._build_controls(). Restore the approved content column with Name first and the sticky sample preview in a separate adjacent area; the current vertical composition is not governing design. Show Cancel/Save in the stable footer while content controls scroll; Cancel retains its existing request_cancel semantics. Prefer layout stretch, size policies, wrapping, and font metrics to new fixed heights. If that approved topology cannot fit at the specified minimum, document the exact contradiction and obtain an approved UI decision before changing topology. Preserve system palette behavior and intentional Appearance/PDF sample colors. No domain, persistence, signing, or package code belongs in this milestone.

Milestone 4 is a closed visual-review gate. Extend the existing real-Qt integration test or add a focused adjacent test for required control geometry and non-overlap at a controlled 1000-by-650 Library client. Check that scrolling the long form does not move preview or actions, that Save persists, and that Cancel exits losslessly after handling the dirty-change prompt. For that test, inject a deterministic q_message_box stub through the frame's Qt bindings and choose Discard; assert the catalog remains unchanged and the nested editor closes without displaying a modal dialog. Capture each candidate's default state and a substantially scrolled content state with the same synthetic data, initial settings, requested geometry, style, font, and display scale. Compare the candidate JSON with baseline metadata; a changed style, font, device-pixel ratio, screen, or requested size invalidates the visual comparison, while actual splitter and widget rectangles remain measured outcomes. Perform the visual review in the main thread or with a vision-capable high-reasoning read-only reviewer, not a lightweight reviewer chosen merely because the task is read-only. Give the reviewer the baseline and both candidate PNGs, UI_SPEC SUR03/SUR04, the normative SVG, guide, and criteria. Require the reviewer to load and inspect the PNG files themselves; source code and geometry JSON alone do not satisfy this gate. A material finding reopens Milestone 3: correct it, recapture both candidate states, and repeat the review. Accept only when no material finding remains or the owner explicitly approves a documented disposition. Limit autonomous cycles to three, then present unresolved findings and images to the owner without marking the plan complete. Run focused tests, Ruff, and the full suite on the accepted candidate. A default-state image cannot prove focus appearance: create a keyboard-focus capture or leave that claim to a live keyboard check.

## Plan of Work

Preserve the existing Git state. Add a small fresh-process scripts/capture_appearance_layout.py entrypoint based on the temporary-store setup in tests/integration/test_signature_library_topology.py, without importing the pytest module. It accepts --artifacts-dir, a safe phase name such as before or candidate-1, and --state default|scrolled. It creates a fresh QApplication and temporary stores with the same empty catalog and explicit initial UI settings for each capture, opens the Library editor, explicitly resizes to the requested minimum and applies the same requested splitter sizes, then processes events. Expose the form-content QScrollArea through a narrow controls field or stable object name so tests and the script do not guess which nested scroll area to move. For scrolled state, set that vertical bar to its maximum, process events again, and fail if that maximum is zero. Capture library.controls.dialog.grab() and write a phase-state PNG plus geometry JSON under the supplied root. Report requested and actual dimensions, screen identifier, display scale, style name, palette window color, effective font family and point/pixel size, QFontMetrics.height(), requested and actual splitter sizes, scrollbar value/maximum, and widget rectangles. Fail if the target is hidden, the capture is null, or actual size is not recorded. Do not screenshot the desktop. Close the Library and frame on both success and failure.

Write the guide and baseline observations before editing layout, so the intended visual change is explicit. Keep the guide in a documentation/status commit, the Qt source plus focused test/capture script in a behavior commit, and sanitized before-default, final after-default, and final after-scrolled PNG/JSON evidence in a separate evidence commit. Intermediate candidate images remain in the owned temporary root and their findings are summarized in this plan. Review each retained capture for private text before staging it. If the baseline shows no material layout defect, avoid gratuitous Qt churn: correct only the known Cancel label, document the observed good geometry, retain the guide and repeat captures, and explain that result in the retrospective.

After each candidate, load and compare the PNGs and record geometry, hierarchy, wrapping, and readability findings. Reopen layout work for every material finding, recapture, and rereview before validation. Update docs/ARCHITECTURE.md only if ownership or public seams change; routine widget sizing does not require an architecture rewrite. Reconcile this plan before committing. Do not close unrelated release/HITL plans.

## Concrete Steps

Run commands from /home/daekar/FoliaSeal. Use the existing .venv if available; otherwise follow README.md to create the development environment. Do not install packages or alter the host desktop merely for this pilot.

    git status --short --branch
    rg -n 'SUR03|SUR04|1000×650|native palette' docs/UI_SPEC.md
    .venv/bin/python -m pytest -q tests/integration/test_signature_library_topology.py

Create an owned temporary root with mktemp -d /tmp/foliaseal-appearance-pilot.XXXXXX. After adding the script, run the commands below from separate fresh processes with the same DISPLAY and QT_QPA_PLATFORM=xcb. The script must request 1000 by 650 after opening the editor and report actual dimensions; never assume Qt honored the request. A larger effective X11 size is an observation, not an automatic failure; the focused Qt geometry test owns proof at the actual supported minimum. PNG pixel dimensions may vary with device-pixel ratio. Replace the example root with the exact mktemp result. For further candidates, increment the candidate number and rerun both states under identical initial settings; compare environmental metadata before accepting any visual review. Update this section with observed output.

    QT_QPA_PLATFORM=xcb .venv/bin/python scripts/capture_appearance_layout.py --artifacts-dir /tmp/foliaseal-appearance-pilot.EXAMPLE --phase before --state default
    QT_QPA_PLATFORM=xcb .venv/bin/python scripts/capture_appearance_layout.py --artifacts-dir /tmp/foliaseal-appearance-pilot.EXAMPLE --phase candidate-1 --state default
    QT_QPA_PLATFORM=xcb .venv/bin/python scripts/capture_appearance_layout.py --artifacts-dir /tmp/foliaseal-appearance-pilot.EXAMPLE --phase candidate-1 --state scrolled

    QT_QPA_PLATFORM=xcb .venv/bin/python -m pytest -q tests/integration/test_signature_library_topology.py -k appearance_editor
    .venv/bin/python -m pytest -q tests/integration/test_signature_library_topology.py
    .venv/bin/ruff check src/foliaseal/presentation/qt tests/integration/test_signature_library_topology.py
    .venv/bin/python -m pytest -q
    git diff --check

Record concise observed output, the exact baseline discrepancy, every candidate review, and any correction here. The visual reviewer must load the PNGs with view_image or an equivalent image viewer. After acceptance and confirming the isolated client images contain only synthetic data, copy the baseline default and final candidate default/scrolled PNGs and JSON reports to docs/visual-evidence/appearance-pilot/, naming the final files after-default and after-scrolled. Mark them non-normative in a short README there. Remove only the owned temporary root after that reviewable evidence is staged. Check git status --short before and after focused commits.

## Validation and Acceptance

At the supported Library minimum, Appearances > Create shows the complete synthetic-preview label and sample, Name label and input, and Cancel/Save without clipping or horizontal scrolling. Name and content remain in the content column while the sticky sample remains in a separate adjacent area, following the approved SVG. Cancel and Save form a stable bottom action area beneath the Library/editor content, with clear primary and secondary hierarchy; they do not merely happen to be visible inside a scrolling pane. Controls remain keyboard reachable. Save creates the Appearance; Cancel exits losslessly through the existing confirmation path. The synthetic sample does not become persisted signer data.

The controlled Qt test must exercise a 1000-by-650 Library client after layout events and inspect effective geometry: positive visible rectangles for required controls within the client, no overlap between preview/content/footer regions, and reachable content in the scroll area. It must prove that scrolling changes the form content while the preview and footer rectangles remain stationary. If the test platform refuses the requested size, report that fact and use a controlled widget/layout test to prove minimum-size composition; do not silently substitute a larger window as minimum-size evidence. In real X11 capture, an actual size larger than requested is recorded and explained, not automatically rejected. Add stable object names or narrow controls fields for the currently unexposed label, scroll area, and action-row widgets. Do not assert one font's exact line breaks or fragile absolute coordinates.

The main-thread or vision-capable high-reasoning read-only reviewer must open and inspect the actual before-default, candidate-default, and candidate-scrolled PNGs. The review brief asks for hierarchy and reading order, whitespace and density, truncation and wrapping, grouping and alignment, preview prominence, action hierarchy and its relationship to the whole Library, awkward unused space, and coherence with native Qt desktop conventions. Compare the SVG's topology, hierarchy, and state; do not pixel-match its dimensions, fonts, colors, or widget shapes. Geometry JSON and code inspection supplement the images but cannot replace image inspection. Focus needs a deliberate focused-state capture or live keyboard check. Record image-only unknowns as unverified.

Accept the pilot only after focused integration tests, Ruff, full pytest, source/spec consistency review, and real-X11 visual comparison pass. Any blocking or material visual finding reopens Milestone 3; the next candidate must be recaptured and reviewed under the same conditions. Completion requires no unresolved material discrepancies, unless the owner explicitly approves a documented disposition. After three autonomous candidate cycles, present unresolved findings and captures to the owner for judgment rather than declaring success. If the display is unavailable, state remains short of complete and the missing gate is recorded. This pilot does not satisfy Orca, high contrast, physical DPI, or installed-package release gates.

## Idempotence and Recovery

The test and script use temporary settings/catalog stores and create no real certificate, PDF signing output, or personal profile. Repeated capture may replace files only within the caller-owned phase directory. Never delete an unspecified /tmp path or user XDG data. Close Library and frame after each run. If capture fails, retain a concise error, clean up the owned process, and retry when X11 is available. Do not stage a capture until it has been inspected for private data. If layout work breaks transactions, revise the change rather than modifying frozen UI_SPEC or user data.

## Artifacts and Notes

The retained evidence is under docs/visual-evidence/appearance-pilot/. SHA-256 PNG values are 2f97a11d166db5b8f1da8f8cf9f1dc5dfcfeab7c8c30e1158973a3c49459acce (before-default), a9b75a9e74823be5c808ac0e9f473245e3bbfb37adc77b82741072c35b51133c (after-default), and 0e1a900e69ddbf4fd413c5032005f8637a2f78cac5e1dc6bf602f84f7a718583 (after-scrolled). All three are 1000 by 650 pixels with Fusion style, Ubuntu 10 pt font and 14-pixel metric height, DPR 1.0, dark palette, and screen DP-4. Final splitter widths intentionally change from baseline 180/280/516 to 120/180/676. The final form scrollbar changes from 0 to 637 between default and scrolled while preview and footer rectangles stay fixed. The images contain only the synthetic Ada Example sample and an empty Library catalog; no user content was observed.

## Interfaces and Dependencies

Use the existing PySide6/Qt stack; add no runtime dependency. The script capture interface accepts a caller-owned artifact directory, a safe phase name, and a default or scrolled state; it reports PNG and JSON paths and runs only when invoked. It uses QWidget.grab() on the owned Library QDialog from a fresh QApplication process. Keep AppearanceProfileEditorWidgetControls and ReusableObjectLibraryControls as narrow test-facing surfaces; add only widget references needed for reliable geometry checks. Do not move visual policy into domain/application code. Use QStyle, QFontMetrics, QPalette, layout size policies, and existing Qt scrolling primitives where measured evidence warrants them. Keep the Save and request_cancel callbacks and remembered Library splitter settings while changing the visible Back label to Cancel.

Revision note (2026-09-17): Replaced the generated helper draft with a single-surface pilot. The scope follows the user's decision to test a guide and screenshot-driven GUI loop before standardizing shared metrics or a dedicated skill.

Revision note (2026-09-17): Reviewer findings corrected the approved content/preview topology, clarified Back versus normative Cancel, made minimum-size measurement and capture commands executable, and retained sanitized pilot images so future reviewers can inspect the evidence.

Revision note (2026-09-17): A final code-path review required deterministic empty stores and identical initial splitter settings for both capture phases, with actual splitter sizes recorded.

Revision note (2026-09-18): The owner supplied an external review. This revision turns visual review into a closed, bounded correction loop; aligns the visible exit label with normative Cancel while preserving behavior; requires direct PNG inspection without pixel matching; adds a scrolled final-state capture and system-font metadata; and makes the footer's place beneath the whole Library an explicit acceptance criterion.

Revision note (2026-09-18): Post-composition review separated the 1000-by-650 minimum-size proof from window-manager capture dimensions, specified deterministic dirty-Cancel testing, required comparable capture metadata, and made the source-visible stacked preview an explicit candidate defect to assess against the baseline image.

Revision note (2026-09-18): The owner relayed final review guidance. The guide is explicitly provisional until pilot success, and the visual image gate is assigned to the main thread or a vision-capable high-reasoning reviewer rather than a default lightweight reviewer. Implementation began after this revision.

Revision note (2026-09-18): Recorded the three-candidate capture findings, focused and full validation, and the owner decision gate without claiming visual acceptance or completing the plan.

Revision note (2026-09-18): The owner approved one more focused pass. Candidate 4 corrected button hierarchy and blank-image visibility, the X11 capture was made geometry-stable, the main-thread PNG gate passed, and final test/evidence results closed the plan.
