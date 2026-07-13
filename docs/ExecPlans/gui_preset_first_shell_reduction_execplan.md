# GUI preset-first shell reduction

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this change, the primary signing shell will stop looking like an always-open harness editor and will instead emphasize the preset-first signing path described in `docs/SPEC.md`. Users will still be able to refine a signing setup manually when needed, but the default experience will foreground choosing a reusable setup and only expose deeper editing through progressive disclosure or a dedicated management path. This is the change that makes the right-hand side of the app feel like a product workflow instead of a development surface.

## Child ExecPlan Dependencies

- [x] (2026-07-08 13:56Z) This child has no further child ExecPlans. Keep the slice on shell emphasis, progressive disclosure, and placement of deeper editing controls.

## Progress

- [x] (2026-07-08 13:56Z) Wrote this ExecPlan after the live GUI review confirmed that the inline editor still dominates the primary shell.
- [ ] Define the target “preset-first” shell experience in concrete UI terms and record it here.
- [ ] Introduce progressive disclosure so the primary shell emphasizes preset selection and lightweight refinement before deeper editing.
- [ ] Reduce or relocate harness-era inline controls that are not needed in the default happy path.
- [ ] Update focused tests and docs for the new shell shape.
- [ ] Validate manually in the live GUI.

## Surprises & Discoveries

- Observation: recent architectural cleanup did not itself move the shell closer to the intended product posture because the inline editor remained the dominant visible structure.
  Evidence: the user still perceived the right-hand editing surface as the old harness GUI even after newer sidebar panels had been added.

## Decision Log

- Decision: approach the shell reduction as progressive disclosure, not abrupt deletion.
  Rationale: the inline editor likely still contains the only working path for some setup refinements. A staged reduction keeps the product usable while making the default path clearer.
  Date/Author: 2026-07-08 / Codex

## Outcomes & Retrospective

No implementation outcomes yet. Update this after the main shell no longer reads like a harness and the preset-first path is the obvious default.

## Context and Orientation

The current right-hand side of the signing workspace is composed from `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py`, `src/foliaseal/presentation/qt/visible_signature_setup_form.py`, and `src/foliaseal/presentation/qt/signing_workspace_sidebar.py`. The shell already has reusable objects such as certificate configurations and signature presets, and `docs/SPEC.md` says the product should bias toward a `Signature Preset`-first setup flow while still allowing manual refinement when needed. The same spec also says full create/edit/delete management of reusable objects should exist in dedicated library or settings areas. That means this slice must not remove the only working manual assembly path before a replacement refinement or management path exists and has been validated.

The live GUI still shows the deeper signature-editing surface as a large always-open block. That makes the shell feel like a direct descendant of the manual harness rather than like an end-user signing product. This plan changes the emphasis of the shell without losing necessary functionality.

## Plan of Work

Start by defining the desired primary shell story in plain user terms. A user who already has a useful signing setup should be able to pick a preset, confirm the certificate or choose one if needed, place the signature, and sign. A user who needs refinement should be able to expand or open deeper editing intentionally rather than having that entire editing surface dominate the screen from the start.

Implement that story through progressive disclosure. The likely shape is a compact top-level preset and certificate area with explicit “refine setup” or equivalent affordances that reveal deeper appearance and placement controls only when the user requests them. The exact mechanism can be collapsible sections, dialogs, or staged panels, but the default state must visually prioritize the happy path. Keep the implementation grounded in the existing shell modules so that preview, readiness, signing behavior, and manual refinement capability remain intact.

As part of the change, review whether some editing controls belong in dedicated management surfaces rather than in the main shell. Do not solve that with a huge new object-management subsystem in this slice; instead, make the main shell honest and narrow, and record any deeper follow-up needed.

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

3. Implement the shell-emphasis changes, then run focused tests.

       .venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_qt_visible_signature_setup_form.py

4. Validate manually in the live GUI.

       .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf

   Expected result: the default shell presents a preset-first path and no longer looks like a wide-open harness editor.

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

Revision note: 2026-07-08 / Codex
Created this plan after the live GUI review confirmed that the current inline editor still dominates the shell and conflicts with the intended preset-first V1 posture.
