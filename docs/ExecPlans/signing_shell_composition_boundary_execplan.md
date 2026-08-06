# Extract the Signing-Shell Composition Boundary

This living ExecPlan follows `.agents/skills/write-execplan/PLANS.md` and is governed by
`docs/ExecPlans/architecture_improvement_loop_parent_execplan.md`.

## Purpose / Big Picture

Reduce top-level lifecycle concentration in `signing_shell.py` without changing the public
`SigningWorkspaceWidget` surface or app-frame behavior. A typed controller will own construction of
the `SigningWorkspaceComposition`, publication of its collaborators, one-time bootstrap, and close
delegation. The widget remains the Qt-facing adapter and keeps its existing properties and methods.
This slice also records the separate atomic plan that will retire obsolete `phase3` nomenclature;
it does not perform a piecemeal rename or add compatibility aliases.

## Child ExecPlan Dependencies

- [x] Parent scan 12 and three independent shell-seam designs selected the minimal controller shape.
- [x] Existing composition fields, bootstrap ordering, close-aware widget behavior, app-frame mount,
  and fake-Qt shell tests were inspected.
- [x] `docs/ExecPlans/phase3_nomenclature_retirement_execplan.md` remains the dedicated atomic
  nomenclature migration plan and is explicitly out of scope for this shell slice.

## Progress

- [x] (2026-08-06) Added `SigningWorkspaceShellController` with typed composition lifecycle methods.
- [x] (2026-08-06) Moved shell construction/publication/bootstrap/close calls behind the controller.
- [x] (2026-08-06) Added focused controller tests and preserved existing fake-Qt shell coverage.
- [x] (2026-08-06) Full Ruff/test/CLI/offscreen validation passed; evidence reported `10` signed
  scenarios (`7` successful), `18/18` preview parity, and `3/3` intentional fit rejections. The
  temporary root was removed and no FoliaSeal/Python process remained.
- [x] (2026-08-06) Actual Improvement measured `0.50` versus predicted `0.40`, with no component
  regression below `-0.10`; implementation and docs are ready for commit.

## Surprises & Discoveries

- The composition has one field, `interaction_bridge`, that was not previously exposed by the
  widget installer list; the controller must publish it to preserve future shell callers.
- The close-aware widget already owns idempotent panel disposal, so controller close must delegate to
  the container rather than duplicating disposal policy.
- The public shell class has many forwarding methods; moving those methods would widen this slice and
  is not required to isolate composition lifecycle ownership.

## Decision Log

- Decision: use a small concrete controller around the existing frozen composition record rather than
  introduce a new graph/port hierarchy. Rationale: it removes the dominant constructor/install/
  bootstrap lifecycle coordination with one stable seam and no caller migration.
- Decision: retain all existing private/public widget attribute names during this slice. Rationale:
  app-frame, compatibility/testing, and fake-Qt consumers are current callers; deleting them would
  conflate lifecycle extraction with the separate nomenclature migration.
- Decision: do not rename `phase3` modules, symbols, CLI commands, fixtures, or serialized fields in
  this child. Rationale: the dedicated atomic retirement plan requires a complete inventory and
  contract migration, not mixed old/new names or permanent shims.

## Outcomes & Retrospective

Implementation completed on 2026-08-06. Focused shell/controller/app-frame coverage passed `110`
tests; Ruff passed; the full suite passed `1,064` tests with `11` skipped and one pre-existing Pillow
warning; CLI help and diff checks passed. Offscreen evidence passed signed acceptance `10/7`, preview
parity `18/18`, and fit rejection `3/3`. The exact temporary root was deleted and process audit found
no application process. The shell now delegates composition lifecycle to the controller while public
attributes and callback ordering remain unchanged. Parent-loop proxy Actual Improvement is `0.50`
versus predicted `0.40`, with no component regression below `-0.10`; commit hash is recorded by the
parent after commit.

## Context and Orientation

`signing_shell.py` creates a close-aware Qt container and layout, builds the composition helper with
the workflow/callback graph, installs roughly twenty collaborators, bootstraps the orchestrator, and
then exposes production and testing forwards. `signing_workspace_composition.py` already owns the
deep construction policy; this child makes its lifecycle explicit without moving behavior-bearing
shell methods.

## Plan of Work

Add the controller, migrate the widget constructor to call `build`, `install_into`, and `bootstrap`,
remove the duplicated installer body, and route `close()` through the controller. Keep callback
closures and attribute names unchanged. Add unit tests for compose-once behavior, collaborator
publication, idempotent bootstrap, and close delegation. Update `docs/ARCHITECTURE.md`, this plan,
the parent ledger, and the nomenclature plan status only where needed to describe the boundary.

## Concrete Steps

    .venv/bin/pytest -q tests/unit/test_signing_workspace_shell_controller.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame_workspace_open.py
    .venv/bin/ruff check src tests scripts
    .venv/bin/pytest -q
    .venv/bin/python -m foliaseal --help
    git diff --check

Run the existing offscreen preview/signed acceptance/fit evidence commands under explicit
`/tmp/foliaseal-shell-composition-evidence-*` roots, collect summaries, remove every root, and audit
for leftover FoliaSeal/Python processes or open Qt dialogs. Do not retain generated evidence unless
this plan explicitly records it.

## Validation and Acceptance

Focused shell/controller tests and the full suite pass without weakening coverage; Ruff and import
isolation pass; CLI help remains deterministic; offscreen acceptance/parity/fit counts and expected
outcomes remain unchanged; `docs/SPEC.md` is byte-for-byte unchanged; worktree is clean after commit.
The parent loop records the measured proxy improvement and starts a fresh three-explorer scan.

## Idempotence and Recovery

The controller is additive and preserves the existing composition field names. If construction or
bootstrap fails, retain the exception and fix the seam rather than restoring the deleted installer
body. If evidence leaves a process or temporary root, terminate/close only the explicit target and
remove only its exact temporary directory before continuing. Do not introduce phase3 aliases.

## Artifacts and Notes

Only explicit temporary offscreen roots and captured command summaries are allowed during validation;
all temporary roots must be deleted before commit. Record any discovered friction or bug in this plan
and the parent ledger before closing the slice.

## Interfaces and Dependencies

`SigningWorkspaceShellController.build(widget, compose)` constructs one controller. `install_into`
publishes the existing composition fields onto the shell, `bootstrap()` is idempotent, and `close()`
delegates to the close-aware container. The controller depends only on the composition record and an
opaque widget/container; no Qt or application policy is imported into the new boundary.
