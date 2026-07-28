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
- [x] (2026-07-20) Re-explored the mounted shell and existing audit. Product code already keeps legacy editor groups unparented in the default sidebar and mounts them only in `Refine current PDF setup`; the audit lacked explicit visible-shell assertions.
- [x] (2026-07-20) Added a bounded `live_gui_parent_audit.py` checkpoint that requires the visible default preset/certificate/preview/refinement groups, rejects visible inline editor and legacy preset-authoring controls, then opens and records the real refinement dialog with its `Visible signature` and `Placement on page` groups.
- [x] (2026-07-20) Completed focused shell regression coverage: `111 passed` for `tests/unit/test_qt_signing_shell.py` and `tests/unit/test_qt_visible_signature_setup_form.py`; Ruff passed for the audit runner and properties panel.
- [x] (2026-07-20) Completed architecture/SPEC compliance review and documentation stewardship. The strengthened audit rejects legacy inline preset mutation controls; no child plan, README, or architecture-document change is needed.
- [ ] Run the isolated display-backed audit, inspect both retained shell screenshots, and verify cleanup. Blocked on 2026-07-20: the environment rejected the required display escalation before execution because its Codex usage limit was exhausted; no GUI process, dialog, artifact directory, or audit evidence was created.

## Surprises & Discoveries

- Observation: recent architectural cleanup did not itself move the shell closer to the intended product posture because the inline editor remained the dominant visible structure.
  Evidence: the user still perceived the right-hand editing surface as the old harness GUI even after newer sidebar panels had been added.

- Observation: prior end-to-end GUI evidence could traverse manual refinement but did not assert that the old editor was absent from the default shell.
  Evidence: `scripts/live_gui_parent_audit.py` drove the visible refinement entrypoint but emitted no checkpoint for default-shell group titles or visible inline authoring actions.

- Observation: the display-backed acceptance cannot be substituted with a headless test when its required evidence is a visible mounted shell and modal dialog.
  Evidence: on 2026-07-20 the display escalation was rejected before the audit command executed because the environment usage limit was exhausted. Focused tests passed, but they do not create the required screenshots.

- Observation: the environment usage-limit lock also prevented the normal Git staging/commit escalation after the focused checks passed.
  Evidence: the commit worker verified only this plan and `scripts/live_gui_parent_audit.py` were modified and that `git diff --check` passed, but its `git add`/`git commit` request was rejected before execution. The changes remain unstaged and recoverable in the worktree.

## Decision Log

- Decision: approach the shell reduction as progressive disclosure, not abrupt deletion.
  Rationale: the inline editor likely still contains the only working path for some setup refinements. A staged reduction keeps the product usable while making the default path clearer.
  Date/Author: 2026-07-08 / Codex

- Decision: for this pass, prefer an intentionally narrower shell over a misleading one, even if that leaves some configuration capability unavailable from the default main window.
  Rationale: the user explicitly prefers empty or deferred space over harness-era cruft, and `docs/SPEC.md` already says reusable-object management should live in dedicated library/settings areas rather than as an always-open editor in the main signing shell.
  Date/Author: 2026-07-13 / Codex

- Decision: extend the isolated real-Qt parent audit instead of using a person's configured GUI state for the remaining direct acceptance.
  Rationale: the runner can assert mounted visible controls, retain default-shell and refinement-dialog screenshots, use temporary stores, and close every Qt top-level window. This provides repeatable product evidence without changing user profiles or leaving dialogs open.
  Date/Author: 2026-07-20 / Codex

## Outcomes & Retrospective

The main shell no longer mounts the old harness-era inline visible-signature editor by default. Instead, it shows the compact preset/certificate/preview flow plus a small manual-refinement affordance that opens a separate dialog for current-PDF appearance and placement edits. Focused Qt shell tests cover both the default narrow layout and the apply/cancel paths of the refinement dialog. The remaining proof is display-backed: inspect the narrow mounted shell and the refinement dialog separately, rather than inferring the first from the second.

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

4. Run the isolated real-Qt audit and inspect its retained default-shell and refinement-dialog evidence.

       DISPLAY=:0 timeout 180s .venv/bin/python scripts/live_gui_parent_audit.py \
           --artifacts-dir /tmp/foliaseal-preset-first-audit

   Expected result: `audit.json` reports passed checkpoints including `preset-first-default-shell` and `manual-refinement-dialog`. The first screenshot shows only preset/certificate/preview/refinement setup, while the dialog screenshot shows `Visible signature` and `Placement on page` only after the visible refinement action is invoked.

## Validation and Acceptance

Acceptance is behavioral. Run the isolated display-backed GUI audit and inspect the retained `preset-first-default-shell` and `manual-refinement-dialog` screenshots. The default right-hand workflow must foreground choosing or confirming a preset and certificate before exposing deeper editing. The audit must reject visible `Visible signature`, `Signature style`, `Visible text`, `Placement on page`, and inline profile-authoring actions in that default shell. It must then open the visible `Refine current setup...` control and confirm that current-PDF appearance and placement editing remains available in the modal dialog.

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

Revision note: 2026-07-20 / Codex
Converted the remaining manual acceptance into a bounded isolated real-Qt audit extension. The product shell was already implemented; this evidence slice adds explicit visible-shell assertions and retains both the default and refinement modal screenshots.

Revision note: 2026-07-20 / Codex
Focused tests and lint passed. The final display-backed acceptance remains explicitly open because the required escalation was rejected before execution by an external environment usage limit; no GUI cleanup was needed because no GUI process started.

Revision note: 2026-07-20 / Codex
Architecture review strengthened the audit to reject legacy inline preset mutation buttons and their preset-name field as well as the old visible-signature editor groups.

Revision note: 2026-07-20 / Codex
The external usage-limit lock also blocked the normal final commit. The unfinished audit extension remains deliberately unstaged in the cleanly scoped worktree for resumption; it must not be represented as a completed plan.
