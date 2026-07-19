# GUI preset-first shell reduction

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this change, the primary signing shell will stop looking like an always-open harness editor and will instead emphasize the preset-first signing path described in `docs/SPEC.md`. Users will still be able to refine a signing setup manually when needed, but the default experience will foreground choosing a reusable setup and only expose deeper editing through progressive disclosure or a dedicated management path. This is the change that makes the right-hand side of the app feel like a product workflow instead of a development surface.

## Child ExecPlan Dependencies

- [x] (2026-07-08 13:56Z) This child has no further child ExecPlans. Keep the slice on shell emphasis, progressive disclosure, and placement of deeper editing controls.

## Progress

- [x] (2026-07-08 13:56Z) Wrote this ExecPlan after the live GUI review confirmed that the inline editor still dominates the primary shell.
- [x] (2026-07-13 14:05Z) Defined the target “preset-first” shell experience for this pass: the default shell should show only preset/certificate selection, the signed-appearance preview, and the sign-flow panel; the always-open inline visible-signature/placement editor should no longer occupy the main sidebar by default.
- [x] (2026-07-13 15:02Z) Introduced progressive disclosure by replacing the always-open inline editor with a compact `Manual refinement` entrypoint that opens a separate dialog for current-PDF appearance and placement editing.
- [x] (2026-07-13 15:02Z) Reduced the default shell to preset selection, certificate selection, preview, and the compact refinement entrypoint; the old harness-style inline `Visible signature` / `Placement on page` blocks are no longer mounted in the main sidebar.
- [x] (2026-07-13 15:02Z) Updated focused shell tests and reconciled the architecture/plan docs with the new default shell shape.
- [ ] Validate manually in the live GUI.

## Surprises & Discoveries

- Observation: recent architectural cleanup did not itself move the shell closer to the intended product posture because the inline editor remained the dominant visible structure.
  Evidence: the user still perceived the right-hand editing surface as the old harness GUI even after newer sidebar panels had been added.

## Decision Log

- Decision: approach the shell reduction as progressive disclosure, not abrupt deletion.
  Rationale: the inline editor likely still contains the only working path for some setup refinements. A staged reduction keeps the product usable while making the default path clearer.
  Date/Author: 2026-07-08 / Codex

- Decision: for this pass, prefer an intentionally narrower shell over a misleading one, even if that leaves some configuration capability unavailable from the default main window.
  Rationale: the user explicitly prefers empty or deferred space over harness-era cruft, and `docs/SPEC.md` already says reusable-object management should live in dedicated library/settings areas rather than as an always-open editor in the main signing shell.
  Date/Author: 2026-07-13 / Codex

## Outcomes & Retrospective

The main shell no longer mounts the old harness-era inline visible-signature editor by default. Instead, it shows the compact preset/certificate/preview flow plus a small manual-refinement affordance that opens a separate dialog for current-PDF appearance and placement edits. Focused Qt shell tests cover both the default narrow layout and the apply/cancel paths of the refinement dialog.

## Context and Orientation

The current right-hand side of the signing workspace is composed from `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py`, `src/foliaseal/presentation/qt/visible_signature_setup_form.py`, and `src/foliaseal/presentation/qt/signing_workspace_sidebar.py`. The shell already has reusable objects such as certificate configurations and signature presets, and `docs/SPEC.md` says the product should bias toward a `Signature Preset`-first setup flow while still allowing manual refinement when needed. The same spec also says full create/edit/delete management of reusable objects should exist in dedicated library or settings areas. That means this slice must not remove the only working manual assembly path before a replacement refinement or management path exists and has been validated.

The live GUI still shows the deeper signature-editing surface as a large always-open block. That makes the shell feel like a direct descendant of the manual harness rather than like an end-user signing product. This plan changes the emphasis of the shell without losing necessary functionality.

## Plan of Work

Start by defining the desired primary shell story in plain user terms. A user who already has a useful signing setup should be able to pick a preset, confirm the certificate or choose one if needed, place the signature, and sign. For this pass, if the deeper editor cannot yet be moved into a dedicated dialog, it is still better to remove it from the default shell than to leave it occupying the primary workflow with misleading harness-era prominence.

Implement that story through progressive disclosure. The concrete shape for this slice is a compact top-level preset and certificate area, followed directly by the signed-appearance preview and a small manual-refinement entrypoint. The existing inline `Visible signature`, `Signature style`, `Visible text`, and `Placement on page` blocks should stop being mounted in the default sidebar layout; instead, the current-PDF refinement path lives in a separate dialog opened from the compact affordance. Keep the implementation grounded in the existing shell modules so that preview, readiness, signing behavior, and mouse-driven placement remain intact.

As part of the change, remove the remaining in-shell preset mutation affordances if they still read like inline harness editing. In this pass, the main shell should bias toward selecting preconfigured objects, not authoring them. Do not solve the missing dedicated appearance/placement library with a huge new subsystem here; instead, make the shell honest and narrow, and record the missing management surfaces as follow-up product work.

Update focused tests for the new shell shape and validate the result manually in the live GUI.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Re-read the shell composition and setup controls.

       sed -n '1,260p' src/foliaseal/presentation/qt/signing_workspace_properties_panel.py
       sed -n '1,260p' src/foliaseal/presentation/qt/visible_signature_setup_form.py
       sed -n '1,260p' src/foliaseal/presentation/qt/signing_workspace_sidebar.py

2. Re-read the spec posture for presets and reusable objects.

       sed -n '120,170p' docs/SPEC.md
       sed -n '248,258p' docs/SPEC.md

3. Implement the shell-reduction changes, then run focused tests.

       .venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_qt_visible_signature_setup_form.py

4. Validate manually in the live GUI.

       .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf

   Expected result: the default shell presents a preset-first path, no longer looks like a wide-open harness editor, and leaves no ambiguous inline authoring controls competing with the main signing workflow.

## Validation and Acceptance

Acceptance is behavioral. Launch the GUI and confirm that the right-hand workflow now foregrounds choosing or confirming a preset and certificate before exposing deeper editing. A user should be able to tell, at a glance, what the fast path is. Deeper appearance and placement refinement must remain available through a validated fallback path, but they should no longer dominate the default view.

Run the focused Qt shell tests that cover the touched modules, then validate manually in the live GUI. If the main shell still feels like a harness after the change, the slice is not done.

## Idempotence and Recovery

This slice should use additive or reversible UI grouping changes where possible. If hiding or relocating an editing surface reveals that some signing path becomes impossible, restore access through explicit progressive disclosure instead of reopening the entire editor by default. Keep the shell usable at every intermediate step.

## Artifacts and Notes

The motivating spec anchors are:

    docs/SPEC.md:127-135
    docs/SPEC.md:255-256

The live UX review artifact is:

    .tmp/gui_ux_review_2026-07-08.md

## Interfaces and Dependencies

The main implementation area is the signing shell presentation layer under `src/foliaseal/presentation/qt/`. This slice should primarily touch `signing_workspace_properties_panel.py`, `visible_signature_setup_form.py`, `signing_workspace_sidebar.py`, and the shell composition code as needed. Keep the visible-signature workflow, preview, and readiness logic intact while changing what is emphasized and when.

Revision note: 2026-07-13 / Codex
Updated the plan with the concrete execution choice for this pass: remove the always-open inline editor from the default shell even before a dedicated appearance/placement management dialog exists, because the misleading harness-era surface is currently worse than a deliberately narrower main workflow.
