# Close evidence-program compliance findings

This child ExecPlan is a living document maintained under `.agents/skills/write-execplan/PLANS.md`. It is a bounded follow-up to `docs/ExecPlans/evidence_program_hybrid_nomenclature_execplan.md`; it must be completed before the parent slice can be closed.

## Purpose / Big Picture

The first compliance review found five concrete issues that could invalidate the evidence-program refactor: an accidentally changed default summary path, eager construction-time imports, stale documentation, an internal protocol name that still says `Phase3`, and aggregate validation that can pass when a scenario error row exists. After this child slice, observable artifact paths and lifecycle behavior are restored, construction remains headless-safe, documentation matches the code, internal naming is neutral, and aggregate evidence rejects scenario errors.

## Child ExecPlan Dependencies

- [x] Parent implementation of the neutral `EvidenceProgram` boundary and deleted matrix holder is present in the working tree.
- [x] Parent plan documentation and implementation commit remain open until this child is validated and reviewed.

## Progress

- [x] (2026-08-02) Two independent compliance reviews reproduced the findings.
- [x] Restore the historical signed-evidence summary path and add a construction-time import-isolation regression test.
- [x] Rename/remove the remaining internal service protocol wording and add the aggregate scenario-error regression test.
- [x] Reconcile README and `docs/ARCHITECTURE.md` so deleted matrix-holder symbols are absent from current sections.
- [x] Run focused/full validation and two independent post-fix compliance reviews, then close the parent plan.

## Surprises & Discoveries

- Observation: A mechanical nomenclature replacement changed the default markdown summary path even though it is an external artifact contract.
  Evidence: The reviews found `artifacts/signed_acceptance_evidence_summary.md` where the established path is `artifacts/phase3_signed_acceptance_evidence_summary.md`.
- Observation: Aggregate signed-evidence validation did not include `error_scenario_count` in its rejection set.
  Evidence: A synthetic summary with one error row and all critical counters zero returned no validation errors.

## Decision Log

- Decision: Restore the historical artifact path instead of adding a compatibility fallback.
  Rationale: The path is already the authoritative persisted contract; a fallback would preserve the accidental rename rather than remove cruft.
  Date/Author: 2026-08-02 / Codex.
- Decision: Share the existing critical-counter rejection semantics by adding `error_scenario_count` to the aggregate validator and regression-test it.
  Rationale: Scenario execution errors must never produce passing aggregate evidence, and the typed matrix normalizer already encodes that rule.
  Date/Author: 2026-08-02 / Codex.

## Outcomes & Retrospective

The compliance fixes are complete. The default signed-evidence summary remains
`artifacts/phase3_signed_acceptance_evidence_summary.md`; construction is lazy and headless-safe;
aggregate validation rejects nonzero `error_scenario_count`; and current README/architecture sections
describe `evidence_runner_factories.py` as the sole lazy runner/operation composition owner. Historical
names are retained only in explicitly historical plan/changelog context, while CLI and persisted
Phase3 contracts remain unchanged.

## Context and Orientation

The parent slice renamed the application service/program and moved lazy matrix operation construction into `src/foliaseal/presentation/qt/evidence_runner_factories.py`. `src/foliaseal/application/phase3_evidence_core.py` still owns persisted matrix result models and validation decisions. `src/foliaseal/presentation/qt/signed_acceptance_evidence.py` builds the default service and `src/foliaseal/__main__.py` exposes the existing CLI commands. README and `docs/ARCHITECTURE.md` contain the current module ownership map and must not claim that the deleted `phase3_matrix_operations.py` exists.

## Plan of Work

Restore `artifacts/phase3_signed_acceptance_evidence_summary.md` in both the service request default and the presentation default constant, and update any current README/test expectations that were mechanically changed. Defer signed-asset generation behind a callable so constructing the default program does not import Pillow, pyHanko, Qt, or cryptography. Add a subprocess test that constructs `_build_evidence_program()` and asserts those modules are absent.

Rename `EvidenceServicePort` to a neutral internal name or remove the protocol if the concrete service already satisfies the program boundary. Update the aggregate validator to reject nonzero `error_scenario_count`, add a regression test, and reconcile current documentation wording about explicit verbs and matrix lazy ownership. Historical changelog entries may retain old names only when explicitly labeled historical.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`. Apply the code/test fixes, then run:

    .venv/bin/python -m pytest -q tests/unit/test_evidence_runner_factories.py tests/unit/test_evidence_program.py tests/unit/test_evidence_service.py tests/unit/test_phase3_evidence_core.py tests/unit/test_qa_signed_acceptance_evidence.py
    .venv/bin/ruff check src tests
    .venv/bin/python -m compileall -q src tests
    .venv/bin/python -m pytest -q
    git diff --check

Expected result: all tests pass, the existing Pillow warning is the only known warning, and no current docs/source reference claims the deleted matrix holder exists.

## Validation and Acceptance

The default program can be constructed without heavy GUI/PDF modules. The historical signed-evidence summary path remains the default. A summary containing `error_scenario_count > 0` fails aggregate validation and writes the failure report before raising. CLI headings, persisted JSON, artifact paths, and intentional rejection rows remain unchanged.

## Idempotence and Recovery

Use focused patches and rerun the regression tests after each fix. Do not add aliases or fallback paths. If a documentation reference is historical, label it rather than deleting useful history. Temporary smoke artifacts must be removed before parent closure.

## Artifacts and Notes

Record the construction-isolation test, aggregate-validator regression test, full-suite result, documentation worker result, and final commit hash in both this child plan and the parent plan.

## Interfaces and Dependencies

The neutral program remains explicit and lazy. The signed-evidence default builder must use a deferred asset-generator callable. The aggregate validator must treat `error_scenario_count` as a failing counter alongside the existing critical counters. No generic dispatcher or compatibility alias is permitted.

## Revision Notes

2026-08-02: Created from the two independent compliance reviews of the parent evidence-program slice.
2026-08-02: Completed implementation, validation, two independent post-fix compliance reviews, and documentation reconciliation; no current docs claim the deleted matrix holder exists. Final commit hash remains to be recorded.
