# Retire the superseded visible-signature corrective wave

This ExecPlan is a living document maintained under
`/home/daekar/.codex/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

The March-April visible-signature corrective wave is still represented by a
parent plan and several child plans that name source files which no longer
exist and retain the obsolete `phase3` label. Leaving those plans open makes
the repository appear to have unfinished implementation work and can send a
future contributor toward dead paths. This slice retires that historical wave
without deleting its evidence or changing product code. The current preview,
fit, and evidence behavior remains governed by the modern UI ExecPlans and
the live modules they name.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/visible_signature_output_analysis_execplan.md` is the
  historical parent being retired.
- [x] The direct worker plans are historical children of that wave:
  `agent_harness_capture_upgrade_execplan.md`,
  `agent_shell_preview_sizing_execplan.md`,
  `agent_shell_preview_scaling_execplan.md`,
  `agent_output_analysis_execplan.md`, and
  `agent_backend_image_fit_execplan.md`; the later backend follow-ups
  `agent_backend_stamp_position_execplan.md` and
  `agent_backend_fit_compact_rect_execplan.md` are retired with them.
- [x] Current owners were verified in `signing_shell.py`, `signing_backend.py`,
  the current harness/evidence modules, and their modern UI ExecPlans.

## Progress

- [x] (2026-08-16) Explorer audit confirmed that the historical parent points
  at missing `phase3` source/test modules while current behavior is covered by
  `signing_backend.py`, `interactive_harness.py`, evidence modules, and current
  Qt-shell/backend tests.
- [x] (2026-08-16) Marked the historical parent and direct workers as retired
  status records, replacing actionable open work with links to current owners.
- [x] (2026-08-16) Preserved historical observations while removing the false
  implication that the missing modules are an active implementation target.
- [x] (2026-08-16) Validated the current owners with the focused shell/backend/
  harness group (`301 passed, 9 skipped, 1 warning`), current-owner Ruff
  checks (`All checks passed!`), and `git diff --check`.
- [x] (2026-08-16) Independent compliance and documentation reviews passed;
  all eight targeted historical plans have no actionable unchecked task, and
  current-owner links/evidence are truthful. The bounded documentation slice
  was committed as `01d7dcdef`; post-commit cleanup is clean.

## Surprises & Discoveries

- Observation: the parent’s open checklist was not evidence of a current
  product defect. Its referenced modules (`phase3_harness.py` and
  `phase3_signing_backend.py`) are absent from the checkout.
  Evidence: current source uses `interactive_harness.py`, evidence projection/
  runtime modules, and `signing_backend.py`; modern tests cover fixed preview
  width and horizontal single-line fit.
- Observation: the old worker plans contain useful historical rationale but
  are not restartable implementation plans because their paths are stale.
  Evidence: the backend worker still instructs a newcomer to edit a missing
  module, while the current implementation and tests have moved on.

## Decision Log

- Decision: retire the historical wave in place instead of deleting the files.
  Rationale: preserve audit history and links while making status truthful;
  deletion would lose the rationale behind the completed preview/fit work.
  Date/Author: 2026-08-16 / Codex.
- Decision: do not reopen or recreate the old implementation tasks under new
  names. Rationale: the current modern plans and tests already own the behavior;
  duplicating the wave would create competing contracts.
  Date/Author: 2026-08-16 / Codex.
- Decision: do not claim release acceptance from this documentation cleanup.
  Rationale: human accessibility, physical DPI/monitor interpretation,
  privileged installation, final release signoff, and Mint 22.3 Wayland remain
  separate external gates.
  Date/Author: 2026-08-16 / Codex.

## Outcomes & Retrospective

The historical corrective wave is now clearly non-actionable, while its
evidence remains available. Current contributors are directed to the modern
preview/fidelity, appearance/layout, signing-backend, and product-support
plans. No source behavior, schema, package, GUI, or Wayland behavior changed.

## Context and Orientation

The retired parent predates the current module split. Its planned shell work
now lives in `src/foliaseal/presentation/qt/signing_shell.py`; backend fit logic
lives in `src/foliaseal/application/signing_backend.py`; harness and evidence
work is distributed among `interactive_harness.py`,
`evidence_harness_projection.py`, `evidence_harness_runtime.py`, and the
signed-acceptance/evidence modules. The authoritative current behavior plans
are `ui_preview_fidelity_fit_validation_execplan.md`,
`ui_appearance_content_layout_execplan.md`, and
`ui_product_support_and_release_execplan.md`.

## Plan of Work

Add a prominent retirement note to the historical parent and each direct worker
plan, including the later backend follow-ups. In the parent, replace the remaining unchecked corrective-wave tasks with
completed “superseded by current owner” records. In the output-analysis child,
close the old manual rerun marker as superseded by current source-tree and
offscreen evidence. Do not rewrite historical measurements or delete files.
Update only the release/status ledgers needed to make the retirement visible;
do not alter product implementation.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    rg -n "phase3_harness|phase3_signing_backend" docs/ExecPlans/visible_signature_output_analysis_execplan.md docs/ExecPlans/agent_*.md
    .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_signing_backend.py tests/unit/test_interactive_harness.py
    .venv/bin/ruff check src/foliaseal/presentation/qt/signing_shell.py src/foliaseal/application/signing_backend.py
    git diff --check

The historical scan may still find words in retired evidence notes, but it
must not leave an unchecked task pointing a contributor at a missing module.

## Validation and Acceptance

Acceptance is documentation truthfulness: every targeted historical plan says
it is retired or superseded, no targeted unchecked item presents dead source
paths as current work, current owner plans are named, and the focused current
tests/lint pass. The release remains explicitly incomplete for its external
gates.

## Idempotence and Recovery

This slice changes Markdown only and is safe to repeat. Preserve unrelated
working-tree changes. Do not delete historical plans, generated evidence,
packages, credentials, or temporary roots. If a current owner cannot be
verified, leave that item open and record the uncertainty instead of retiring
it.

## Artifacts and Notes

Only the eight historical plan files, this retirement plan, and any concise
ledger status entry may be committed. No generated artifacts are in scope.

## Interfaces and Dependencies

The documentation references current Python modules and current ExecPlans only;
it does not add an API or dependency. Wayland is outside this slice.

Revision note: 2026-08-16 / Codex: created after the next-slice explorer found
the visible-signature parent’s open tasks were stale references to removed
`phase3` modules rather than a dependency-ready product gap.
