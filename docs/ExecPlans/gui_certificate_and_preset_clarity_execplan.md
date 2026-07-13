# GUI certificate and preset clarity

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this change, a user will be able to understand the difference between a managed certificate, a certificate configuration, and a signature preset, and will no longer have to guess what actions such as `Apply certificate` do. The application-settings dialog will also behave more like a standard desktop app by letting users choose directories through a filesystem picker instead of manual path typing alone. This matters because the current wording and empty-state behavior actively obscure the V1 workflow.

## Child ExecPlan Dependencies

- [x] (2026-07-08 13:56Z) This child has no further child ExecPlans. Keep the slice on naming, explanation, empty states, and lightweight desktop affordances.

## Progress

- [x] (2026-07-08 13:56Z) Wrote this ExecPlan from the live GUI review and the current certificate/preset/settings surfaces.
- [x] (2026-07-11 00:00Z) Audited and clarified user-visible certificate/preset terminology in the main shell and management dialogs.
- [x] (2026-07-11 00:00Z) Replaced unclear labels and added helper text and empty-state copy where the UI assumed internal knowledge.
- [x] (2026-07-11 00:00Z) Added directory-picker affordances to application settings for default open/output folders.
- [x] (2026-07-11 00:09Z) Updated focused tests for the wording, helper-text, placeholder, and settings-directory-picker changes; `131 passed` in the focused Qt app-frame/app-frame-certificate-management/signing-shell suite, plus `9 passed` in the adjacent text-selection/page-navigation regression set, and `ruff check` passed for all touched files.
- [ ] Validate manually in the live GUI.

## Surprises & Discoveries

- Observation: the certificate creation dialog itself is not obviously out of spec; the larger problem is that the surrounding surfaces do not explain how created objects participate in the signing flow.
  Evidence: the user could create a certificate successfully, but then could not tell what the management surfaces and `Apply certificate` action meant.

## Decision Log

- Decision: keep this plan separate from the deeper shell simplification work.
  Rationale: users need clearer names and explanations even if the larger inline editor remains temporarily in place, and these changes should be able to land sooner.
  Date/Author: 2026-07-08 / Codex

## Outcomes & Retrospective

The implementation pass for this slice is complete and green on focused tests. The main shell and management dialogs now explain the difference between managed certificates, certificate configurations, and signature presets without relying on internal vocabulary, and the app-frame settings dialog exposes standard directory browsing for the default open and output folders.

This removed the main terminology confusion around `Apply certificate`-style actions and made the app-wide settings dialog feel closer to a standard desktop app while keeping the existing manual path entry behavior available. The remaining acceptance step is a live GUI walkthrough to confirm that the clearer wording actually reads correctly in context and that the new browse buttons feel right in the running app.

## Context and Orientation

FoliaSeal currently exposes several related but distinct reusable signing objects. A managed certificate is the stored certificate material itself. A certificate configuration is the user-facing app object used to choose and configure which stored certificate is active for signing. A signature preset is a saved combination of signing setup references. These concepts are valid according to the frozen spec in `docs/SPEC.md`, but the current GUI does not explain them well enough. The user observed certificate-management dropdowns that appeared empty or purposeless and could not infer what `Apply certificate` in the main shell was supposed to do.

The relevant code lives in `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py` for the main shell controls, `src/foliaseal/presentation/qt/app_frame_certificate_management.py` for creation/import/management dialogs, and `src/foliaseal/presentation/qt/app_frame.py` for the application-settings dialog.

## Plan of Work

Start with a terminology audit. Search the shell, dialogs, and tests for every user-visible label involving certificate, configuration, preset, managed certificate, and apply/select verbs. Compare those labels to the object semantics in `docs/SPEC.md`. Wherever a label exposes internal implementation vocabulary more than product meaning, choose clearer language and record the decision. The goal is not to hide the object model; it is to express it in user terms.

In the main shell, replace or contextualize ambiguous controls such as `Apply certificate`. If the correct product concept is “select this saved certificate configuration for the current signing setup,” say that plainly in the control label, nearby helper text, or empty-state copy. In the management dialogs, add empty-state messages and concise descriptions so a newly created certificate can be understood in relation to a configuration and a preset.

In the application-settings dialog, keep the current text fields but add directory-picker buttons that call the standard Qt directory chooser. The user should still be able to type a path manually, but standard desktop browsing must become the primary easy path.

Update tests for any renamed controls or new helper text, and validate the flows manually in the live GUI.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Re-read the relevant UI modules.

       sed -n '140,210p' src/foliaseal/presentation/qt/app_frame.py
       sed -n '680,760p' src/foliaseal/presentation/qt/signing_workspace_properties_panel.py
       sed -n '210,520p' src/foliaseal/presentation/qt/app_frame_certificate_management.py

2. Audit user-visible wording.

       rg -n "certificate|preset|Apply certificate|managed certificate|configuration" src/foliaseal/presentation/qt tests/unit

3. Implement the wording, helper text, empty states, and settings-directory picker affordances, then run focused tests.

       .venv/bin/python -m pytest -q tests/unit/test_qt_app_frame.py tests/unit/test_qt_signing_shell.py

4. Validate manually in the live GUI.

       .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf

   Expected result: a user can explain what each certificate/preset surface is for and can choose settings directories through standard browsing controls.

## Validation and Acceptance

Acceptance is behavioral. A first-time user should be able to create a certificate, return to the main shell, understand how that certificate relates to the active signing setup, and understand what a preset is meant to do. The application-settings dialog should provide standard directory-chooser buttons for default open and output folders. If a user still asks what `Apply certificate` means after this slice, the slice is not done.

Run the focused tests around the app frame and shell controls, then validate the flows manually in the live GUI.

## Idempotence and Recovery

This slice should be additive and safe. If a renaming change risks drifting from spec terminology, prefer short helper text or subtitle copy over inventing a new domain concept. If directory-picker support becomes awkward in the existing settings dialog layout, expand the layout minimally rather than dropping the feature.

## Artifacts and Notes

The main product review evidence is:

    .tmp/gui_ux_review_2026-07-08.md

The relevant spec anchors are:

    docs/SPEC.md:140-158
    docs/SPEC.md:229-238

## Interfaces and Dependencies

The touched modules should remain `app_frame.py`, `signing_workspace_properties_panel.py`, and `app_frame_certificate_management.py`. Use Qt’s standard directory chooser via `QFileDialog.getExistingDirectory` or the closest dynamic-import equivalent already exposed in `QtAppFrameBindings`. Keep behavior testable through the existing Qt-fake unit suites.

Revision note: 2026-07-11 / Codex
Corrected the living document after implementation so it now reports the slice truthfully as code-complete and test-green, with live GUI validation still pending.
