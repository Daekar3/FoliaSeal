# Schema Model Alignment Slice 4E Compliance Follow-up ExecPlan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After the Slice 4E compliance review, two issues need a narrow follow-up: stale documentation still implies the signing shell edits app settings, and test coverage should explicitly prove that app-frame settings saves refresh the loaded shell's output-default behavior.

## Child ExecPlan Dependencies

- [x] Depends on `docs/ExecPlans/schema_model_alignment_slice4e_remove_shell_settings_controls_execplan.md`.

## Progress

- [x] (2026-05-08 00:20Z) Created this compliance follow-up plan.
- [x] (2026-05-08 00:23Z) Corrected stale architecture/parent-plan wording.
- [x] (2026-05-08 00:24Z) Strengthened app-frame settings propagation test coverage.
- [ ] Run focused validation and commit the follow-up.

## Surprises & Discoveries

- Observation: compliance review found the implementation correct but identified stale docs.
  Evidence: `docs/ARCHITECTURE.md` still said the signing shell could edit/save default directories.

- Observation: compliance review found a narrow test gap around the loaded shell observing output-default changes after app-frame settings save.
  Evidence: existing app-frame tests asserted propagation but not an output-default effect.

## Decision Log

- Decision: handle this as a documentation/test follow-up rather than amending the implementation commit.
  Rationale: the implementation is already committed and validated; a separate compliance commit preserves review history.
  Date/Author: 2026-05-08 / Codex

## Outcomes & Retrospective

At creation, this follow-up is expected to be small and compliance-only.

The follow-up corrected the stale docs and expanded the propagation test to assert that the saved output directory reaches the loaded shell workspace path that controls future output-dialog defaults.

## Context and Orientation

Files to update:

    docs/ARCHITECTURE.md
    docs/ExecPlans/schema_model_alignment_execplan.md
    tests/unit/test_qt_app_frame.py

## Plan of Work

First, change architecture wording so the app frame is the only app-settings editing surface and the shell is described as a settings consumer for output defaults.

Second, update the parent ExecPlan observation that previously described duplicate editing as a current state so it is clearly historical before Slice 4E.

Third, strengthen `test_app_frame_settings_dialog_refreshes_loaded_shell_settings()` with an assertion that the loaded shell's output-default behavior observes the saved output directory.

## Concrete Steps

Run:

    .venv/bin/pytest -q tests/unit/test_qt_app_frame.py tests/unit/test_qt_signing_shell.py tests/unit/test_app_settings_storage.py
    .venv/bin/ruff check .

## Validation and Acceptance

This follow-up is accepted when stale docs are corrected, the focused test covers output-default propagation, and focused validation passes.

## Idempotence and Recovery

If the test design proves too fake-heavy, keep the assertion at the app-frame propagation boundary and document the remaining limitation. Do not reintroduce shell settings editors.

## Artifacts and Notes

No generated artifacts are expected.
