---
role: standalone
state: complete
depends_on: []
---

# Validate Import Certificate with the portable Qt visual loop

This ExecPlan is a living document. Maintain its Progress, Surprises & Discoveries, Decision Log, and Outcomes & Retrospective under `/home/daekar/.codex/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

A person importing a certificate must be able to read the introduction, select a file, inspect non-secret certificate facts, enter a display name and password, and reach Cancel and Import. This slice tests the new portable `qt-gui-work` skill on a modal form, which differs from the three-column Appearance editor. The dialog was already corrected from a 267 by 284 clipped window to a 600 by 460 minimum and 680 by 520 default. A fresh capture determines whether more layout work is justified.

## Child ExecPlan Dependencies

- [x] No prerequisite ExecPlans.

The certificate workflow in `docs/UI_SPEC.md` section 15 governs this standalone trial.

## Progress

- [x] (2026-09-19 02:54Z) Built and reviewed real-X11 captures of empty and inspected synthetic states at the 600 by 460 minimum. The retained artifacts are `docs/visual-evidence/import-certificate-trial/empty.png`, `empty.json`, `inspected.png`, and `inspected.json`.
- [x] (2026-09-19 02:56Z) Recorded the visual findings and applied one focused candidate. The candidate uses native password masking, right-aligned Cancel/Import actions, and native default emphasis on Import. Direct image review found no material clipping, overlap, wrapping, or density defect in either state.
- [x] (2026-09-19 03:05Z) Added the focused real-Qt minimum-size regression, cancellation coverage, and fake-binding assertions. Compliance review found no remaining contract or architecture drift. Full validation passed with 1668 tests, 20 skipped, and one existing Pillow warning; Ruff, whitespace, and plan checks pass. Retained only the safe candidate states and prepared the focused commits.

## Surprises & Discoveries

- Observation: The already enlarged dialog is coherent at its declared 600 by 460 minimum in both empty and inspected states; the inspected summary expands vertically without pushing the footer out of view.
  Evidence: `docs/visual-evidence/import-certificate-trial/empty.json` and `inspected.json` both report `actual_size: [600, 460]`; the PNGs show all required controls and facts.
- Observation: The visual review identified two small implementation details that functional tests did not establish: the password field needed an explicit masked echo mode, and the footer needed a stretch before Cancel/Import so the actions remain compact and right aligned.
  Evidence: The retained captures show masked password bullets and 80-pixel native buttons at x=422 and x=508 in the inspected state.
- Observation: Compliance review required a real-Qt geometry regression in addition to the PNGs and fake-binding tests. The new offscreen test verifies the 600 by 460 composition, nonoverlapping footer actions, native default Import action, and real `QLineEdit.Password` echo mode.
  Evidence: `tests/integration/test_certificate_import_dialog_layout.py` and the focused 20-test passing run.

## Decision Log

- Decision: Start as verification, not a presumed redesign.
  Rationale: previous remediation already enlarged the dialog, and code/tests cannot establish that the current pixels are defective.
  Date/Author: 2026-09-18 / Codex.
- Decision: Use only an isolated synthetic PKCS#12 source and never import it during capture.
  Rationale: the inspected state must exercise the production inspection path without mutating a real catalog or exposing user credentials.
  Date/Author: 2026-09-18 / Codex.
- Decision: Keep the correction limited to native Qt action and field presentation; do not redesign the dialog after the baseline review.
  Rationale: both states already satisfy the required 600 by 460 composition, so a broader layout change would add risk without evidence of a material defect.
  Date/Author: 2026-09-19 / Codex.

## Outcomes & Retrospective

The portable visual loop generalized to this modal form without requiring a shared layout framework. It found a security-relevant presentation defect and weak action hierarchy that behavior tests had missed. The accepted captures show a readable empty state and an inspected state with synthetic identity, issuer, validity, private-key status, warning text, masked password, and compact native actions. One candidate was sufficient. Compliance review found no architecture drift, and shared Qt layout metrics remain unjustified.

Verification:
- Action: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q tests/integration/test_certificate_import_dialog_layout.py tests/unit/test_qt_app_frame_certificate_management.py`
  Result: pass
  Evidence: focused certificate validation transcript: 20 passed.
- Action: `QT_QPA_PLATFORM=xcb .venv/bin/python scripts/capture_import_certificate_layout.py --artifacts-dir docs/visual-evidence/import-certificate-trial --phase candidate-1 --state empty` and the matching `inspected` command
  Result: pass
  Evidence: `docs/visual-evidence/import-certificate-trial/empty.png`, `inspected.png`, and matching JSON reports; direct PNG review.
- Action: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q`, `.venv/bin/ruff check .`, and `git diff --check`
  Result: pass
  Evidence: 1668 passed, 20 skipped, one existing Pillow deprecation warning in 45.31 seconds; Ruff reported All checks passed and the whitespace check had no output.
- Action: one-file ExecPlan helper check
  Result: pass
  Evidence: helper reported PASS for this plan on 2026-09-19.

## Context and Orientation

`src/foliaseal/presentation/qt/app_frame_certificate_management.py` owns `CertificateImportDialog`. Its `show_import_dialog` service entrypoint immediately calls the dialog's blocking modal `exec`, so the capture must not call that service method. It constructs `CertificateImportDialog` directly with the real frame bindings, frame window, and certificate manager, then calls `dialog.controls.dialog.show()`. The layout contains an introduction, file row, Inspect action, inspection summary, display name/password controls, Remember password checkbox, and Cancel/Import footer. `tests/support/signing_builders.py::write_test_pkcs12` creates an encrypted synthetic certificate. `tests/unit/test_qt_app_frame_certificate_management.py` checks import and inspection behavior with fake Qt bindings. `docs/UI_SPEC.md` section 15 requires identity, issuer, validity, private-key status, and warnings before import; cancellation or rejection must leave no residue. `docs/GUI_STYLE_GUIDE.md` supplies subordinate native Qt guidance. The portable skill source is `/home/daekar/AI Tools/AI-Skills/qt-gui-work/SKILL.md` at commit `681e34b`; its matching installed copy supplies the visual loop. This plan defines the repository-specific surface and evidence.

## Milestones

First, add `scripts/capture_import_certificate_layout.py` as an opt-in fresh-process X11 capture using temporary settings and certificate stores. It accepts an artifact directory, phase, and `empty` or `inspected` state. Show the real parent frame for window ownership, construct the import dialog directly, and never invoke the blocking service entrypoint. The inspected state writes a synthetic `.p12`, fills a synthetic display name and password, calls `inspect_certificate()`, and captures only the shown dialog with `QWidget.grab()`. Both captures request 600 by 460, settle X11, and record actual `dialog.size()`; accept an effective size at or above the declared minimum only when the required layout remains usable. JSON records style, font, device-pixel ratio, screen, and rectangles for the dialog, introduction, file path, Choose, Inspect, inspection summary, display name, password, Remember password, Cancel, and Import controls. Open both PNGs and state exact discrepancies, if any.

Second, correct only baseline-proven material visual issues in `CertificateImportDialog._build_controls()`. Retain validation, import transaction, modal semantics, and native palette. After a correction, recapture both states under equivalent conditions and review the PNGs directly. If the baseline is coherent and readable, leave production layout code unchanged. Limit autonomous candidates to three; present unresolved material judgments to the owner.

Third, run focused and full validation, review against `docs/SPEC.md`, `docs/UI_SPEC.md`, and `docs/ARCHITECTURE.md`, retain only synthetic non-normative captures with a short README under `docs/visual-evidence/import-certificate-trial/`, update this plan, and commit. Captures do not prove keyboard speech, high contrast, physical DPI, or installed-package acceptance; those remain in the release HITL matrix.

## Plan of Work

Use the Appearance capture script only as an ownership and metadata pattern, not as a shared framework. Build the Import dialog through real Qt bindings in an isolated fresh process. Use a relative synthetic filename in the inspected dialog so the capture does not expose random temporary paths. Never save or import the certificate through the dialog. Record actual geometry rather than assuming a requested resize succeeded. Compare empty and inspected states under matching display conditions and judge hierarchy, density, wrapping, control grouping, inspection readability, and footer stability. If a fix is needed, add a focused real-Qt geometry regression rather than a pixel-match test. Keep behavior, evidence, and plan updates in reviewable commits; do not change domain, persistence, signing, or unrelated screens.

## Concrete Steps

Run from `/home/daekar/FoliaSeal` with the existing `.venv` and real Cinnamon/X11 display. Use a caller-owned temporary artifact directory. After adding the script, run:

    QT_QPA_PLATFORM=xcb .venv/bin/python scripts/capture_import_certificate_layout.py --artifacts-dir /tmp/foliaseal-import-visual-trial --phase before --state empty
    QT_QPA_PLATFORM=xcb .venv/bin/python scripts/capture_import_certificate_layout.py --artifacts-dir /tmp/foliaseal-import-visual-trial --phase before --state inspected
    QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q tests/unit/test_qt_app_frame_certificate_management.py
    .venv/bin/ruff check .
    QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q
    git diff --check
    CARGO_TARGET_DIR=/tmp/foliaseal-execplan-helper-target cargo run --quiet --manifest-path /home/daekar/.codex/skills/write-execplan/helper/Cargo.toml -- check docs/ExecPlans/002-validate-import-certificate-with-portable-qt-visual-loop.md

If a layout candidate is necessary, use `--phase candidate-1` and repeat both states. Inspect the PNGs before retaining them. A failed or mismatched X11 capture cannot pass the visual gate; rerun under comparable conditions or leave the plan active with that exact blocker.

## Validation and Acceptance

At the requested minimum, the introduction, file controls, Inspect action, inspection facts, display-name/password controls, and Cancel/Import actions are readable, nonoverlapping, and reachable in the actual measured client. The inspected state shows synthetic identity, issuer, validity, private-key status, and warnings. The password field is visibly masked; no password or temporary path appears in retained evidence. The empty state remains understandable. Direct image review must find no material visual discrepancy, or each remaining finding needs an explicit owner disposition. Existing import/inspection tests must pass. If production behavior changes, add a cancellation test proving the catalog remains unchanged; any production layout change needs a focused real-Qt geometry check. Full pytest, Ruff, and ExecPlan structural validation must pass before completion.

## Idempotence and Recovery

The capture uses a temporary catalog and certificate, never a user profile or installed package. Each phase/state filename may be replaced only in the caller-supplied artifact directory. Close the dialog and app frame in `finally`, restore any changed working directory, and remove temporary secrets when the process ends. Retain only reviewed client captures with synthetic data. If the display is unavailable, offscreen geometry may help diagnose layout, but it does not replace the X11 visual gate.

## Artifacts and Notes

Record captures, metadata, reviewer observations, tests, and commits here as work proceeds. `docs/visual-evidence/import-certificate-trial/` contains only the accepted empty and inspected PNG/JSON pairs and a short non-normative README. Direct review found no desktop content or real certificate data in the retained images. Do not retain a desktop screenshot or a real certificate.

## Interfaces and Dependencies

Use existing PySide6, `CertificateImportDialog`, `QtAppFrameAdapter`, `CertificateManager`, and the synthetic PKCS#12 builder. Add no runtime dependency or generic capture framework. The script is an opt-in development tool and does not affect application launch or release packaging.

Revision note (2026-09-18): The portable skill's second-surface trial begins with a current-state capture because earlier Import Certificate density defects were already corrected.

Revision note (2026-09-19): Recorded the candidate-1 X11 captures and direct visual review. The current evidence supports retaining the dialog layout, with only native password masking and compact default action presentation required. Added the compliance-requested real-Qt regression and final validation, then completed the plan.
