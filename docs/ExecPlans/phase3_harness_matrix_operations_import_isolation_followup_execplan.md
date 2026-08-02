# Restore true headless import isolation for Phase 3 matrix operations

This child ExecPlan is a living document maintained in accordance with `.agents/skills/write-execplan/PLANS.md`. It records the completed high-risk follow-up for `phase3_harness_matrix_operations_execplan.md`.

## Purpose / Big Picture

The parent slice made `phase3_matrix_operations.py` dependency-light, but the default evidence-service module still imported `phase3_harness.py` at module load. Because the CLI imports the signed-evidence helper while building its parser, even `foliaseal --help` and unrelated commands could load PIL, pyHanko, and PySide6 before selecting an operation.

After this follow-up, importing the application service, signed-evidence default wiring, or CLI parser will not import those optional GUI/PDF runtime trees. The selected preview or signed/capture operation will still import and construct its concrete adapter only when invoked. The follow-up also removes the unused fresh-shell constant/comment that falsely describes signed-run lifecycle behavior.

## Child ExecPlan Dependencies

- [x] Parent implementation created `Phase3MatrixOperations` and migrated default service wiring.
- [x] High-risk review reproduced eager heavy imports and identified the stale shell-recycle constant.

## Progress

- [x] (2026-08-01) Recorded high-risk findings and created this child plan before follow-up edits.
- [x] (2026-08-01) Removed top-level `phase3_harness` and asset-generator imports from `phase3_signed_acceptance_evidence.py`; concrete Qt/PDF factories now import only when selected.
- [x] (2026-08-01) Removed top-level GUI/Phase 2/Phase 3 harness imports from `__main__.py` while preserving lazy wrapper names and CLI defaults; subprocess checks show no `PIL`, `pyhanko`, or `PySide6` imports for default evidence or CLI module import.
- [x] (2026-08-01) Removed the unused `_PREVIEW_MATRIX_SHELL_RECYCLE_INTERVAL` comment/constant without changing signed-run lifecycle semantics.
- [x] (2026-08-01) Updated the parent plan's current orientation/outcomes/progress and reconciled current architecture ownership rows; historical changelog entries remain historical.
- [x] (2026-08-01) Follow-up-focused tests pass (`41 passed`); Ruff and diff checks pass.
- [x] (2026-08-01) Full suite passes (`1040 passed`, one pre-existing Pillow warning); preview matrix reports 8/8 successful with zero errors; signed matrix reports 8 scenarios, 6 successful signings, 2 matched intentional rejections, zero unexpected errors, and passing acceptance expectations. Temporary artifacts and processes were cleaned up.
- [x] (2026-08-01) Completed the second compliance/high-risk review; import isolation, one-shell signed lifecycle cleanup, raw summary parity, and artifact handling remain consistent with the parent acceptance contract.
- [x] (2026-08-01) Re-ran the focused/full validation and matrix checks recorded above; no FoliaSeal/Phase 3 processes or temporary matrix artifacts remained.

## Surprises & Discoveries

- Observation: Importing `phase3_matrix_operations.py` directly is clean, but importing `phase3_signed_acceptance_evidence.py` still reached the heavy harness through a top-level import.
  Evidence: a subprocess import showed `PIL`, `pyhanko`, and `PySide6` in `sys.modules` before any matrix operation ran.
- Observation: `_PREVIEW_MATRIX_SHELL_RECYCLE_INTERVAL` is declared with a fresh-shell comment but has no callers, while `Phase3SignedAcceptanceMatrixRunner.run()` creates one lifecycle before its scenario loop.
  Resolution: delete the stale constant and comment rather than alter the established signed-matrix lifecycle in this follow-up.

## Decision Log

- Decision: Keep concrete harness imports inside operation/capture factories instead of adding a second adapter module in this child.
  Rationale: The application service already owns typed runner ports; local factory imports restore import isolation with the smallest change and avoid another composition layer.
  Date/Author: 2026-08-01 / Codex.
- Decision: Preserve the current signed matrix lifecycle and remove only the unused contradictory constant/comment.
  Rationale: Lifecycle behavior is already covered and the user did not request a fresh-shell redesign; changing it would broaden the slice.
  Date/Author: 2026-08-01 / Codex.

## Outcomes & Retrospective

The follow-up implementation is complete: optional GUI/PDF imports are deferred until selected operations, CLI/default-service imports are clean, and the stale shell-recycle declaration is removed without changing lifecycle behavior. The second compliance/high-risk review and documentation reconciliation are complete; the parent/child commit is intentionally left to the main agent.

## Context and Orientation

`src/foliaseal/presentation/qt/phase3_signed_acceptance_evidence.py` builds `Phase3EvidenceService`; it should import only application contracts and the dependency-light matrix-operation module at module load. Its preview/signed/capture factories may import `phase3_harness.py` inside the callable that is selected at runtime.

`src/foliaseal/__main__.py` imports the signed-evidence helper to obtain the default summary path and service builder. Keeping that helper lightweight prevents parser construction and unrelated commands from requiring Qt/PIL/pyHanko.

`src/foliaseal/presentation/qt/phase3_harness.py` still owns concrete runner factories and the interactive capture implementation. It may remain heavy when explicitly imported or when a selected operation invokes its factory. `phase3_signed_acceptance_matrix_runner.py` owns the established lifecycle and closes it in its existing `finally` path; this child does not change that flow.

## Plan of Work

Remove the top-level import of `build_phase3_matrix_operations` and `build_interactive_phase3_capture_runner` from `phase3_signed_acceptance_evidence.py`. Keep the lightweight `build_headless_phase3_matrix_operations` import. Add private local factory functions that import `phase3_harness._build_preview_matrix_operation`, `phase3_harness._build_signed_acceptance_matrix_operation`, and `phase3_harness.build_interactive_phase3_capture_runner` only when a selected operation needs them. Wrap the capture factory in one lazy closure so the harness runner is built once on the first capture request and never during service construction.

Remove `_PREVIEW_MATRIX_SHELL_RECYCLE_INTERVAL` and its misleading comment from `phase3_harness.py`. Do not modify the signed runner’s lifecycle loop or introduce a new shell-recycling policy.

Add subprocess-based tests proving that importing `phase3_signed_acceptance_evidence`, constructing the default service, importing `foliaseal.__main__`, and parsing `--help` do not load modules whose names begin with `PySide6`, `PIL`, or `pyhanko`. Keep operation-boundary tests proving selected execution still reaches the concrete factories.

Update the parent ExecPlan so its orientation describes the post-migration module ownership, its outcomes no longer say pending, and its progress records the child follow-up. Update `docs/ARCHITECTURE.md` current rows for the Qt package, matrix operations, and session/matrix entrypoints; historical changelog entries may remain explicitly historical.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

       .venv/bin/python -m pytest -q tests/unit/test_phase3_matrix_operations.py tests/unit/test_phase3_evidence_service.py tests/unit/test_phase3_evidence_orchestrator.py tests/unit/test_main_cli.py
       .venv/bin/ruff check src tests
       git diff --check

Then run the parent full suite and both release-fidelity matrix commands. Use subprocess output to verify no heavy-module names are loaded before operation invocation. Remove only the named temporary matrix directories and verify no FoliaSeal/Phase 3 process remains.

## Validation and Acceptance

The follow-up is accepted when importing the signed-evidence helper, default service, CLI module, or CLI parser does not load `PySide6`, `PIL`, or `pyhanko`; selected preview, signed, and capture operations still execute through the existing concrete adapters; full tests and both matrices pass; and the stale shell-recycle constant/comment is absent without any lifecycle behavior change.

## Idempotence and Recovery

Local imports and lazy closures are safe to rerun. If an import-isolation test fails, inspect the import graph and move only the concrete harness import behind the selected factory; do not weaken the test or eagerly import the heavy module. If a matrix fails, remove only the two temporary directories and rerun.

## Artifacts and Notes

Record evidence here:

       eager-import subprocess result: <module list>
       focused follow-up tests: <count>
       full suite: <count> passed
       matrices: preview 8/8; signed 6 successful, 2 intentional rejections
       stale shell-recycle symbol: absent
       follow-up commit: <hash>

## Interfaces and Dependencies

The parent interfaces remain unchanged. `Phase3EvidenceService` continues to receive `CaptureRunnerPort` and `MatrixRunnerPort` callables. The child only changes when their concrete Qt-backed factories are imported and built. No new public dispatcher or compatibility alias is permitted.

## Change-Slice Boundary

Allowed changes are lazy imports in signed-evidence/CLI composition, removal of the unused shell-recycle constant/comment, current architecture/ExecPlan reconciliation, focused import-isolation tests, and validation artifacts. Forbidden changes include signing semantics, matrix lifecycle redesign, CLI command names, summary schemas, artifact paths, Qt workspace behavior, and broad render/PDF extraction.

Plan revision note: created 2026-08-01 after the high-risk compliance review reproduced eager optional-dependency imports and found the unused shell-recycle declaration.
