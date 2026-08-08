# Rename the Internal Evidence Core Away from Phase3

This is the first bounded child slice of `phase3_nomenclature_retirement_execplan.md`. It is
maintained according to `.agents/skills/write-execplan/PLANS.md`; milestones are progress markers,
not stopping points. The complete slice includes the rename, validation, architecture/docs
reconciliation, cleanup, and commit.

## Purpose

`phase3` is no longer a useful implementation label. This slice removes it from the two neutral,
application-owned evidence modules that have no reason to carry release-history terminology:
`phase3_evidence_core.py` and `phase3_fidelity_contract.py`. The rename is deliberately limited to
internal Python module paths and their tests/imports. Public CLI commands, persisted JSON keys,
fixture directory names, `Phase3*` edge DTOs, artifact paths, and historical records remain stable
until a later contract-migration slice can change them atomically.

## Scope and naming map

| Current | New | Compatibility decision |
|---|---|---|
| `src/foliaseal/application/phase3_evidence_core.py` | `src/foliaseal/application/evidence_core.py` | No forwarding module; update every first-party import atomically. |
| `tests/unit/test_phase3_evidence_core.py` | `tests/unit/test_evidence_core.py` | Rename the test path and module imports together. |
| `src/foliaseal/application/phase3_fidelity_contract.py` | `src/foliaseal/application/fidelity_contract.py` | No forwarding module; update every first-party import atomically. |
| `tests/unit/test_phase3_fidelity_contract.py` | `tests/unit/test_fidelity_contract.py` | Rename the test path and module imports together. |
| `RELEASE_FIDELITY_CONTRACT_VERSION = "phase3_fidelity_v1"` | unchanged | Persisted/release manifest contract; not an internal module label. |
| `tests/fixtures/phase3/release_fidelity_manifest.json` | unchanged | Fixture path is part of the current evidence corpus and migrates only with the manifest contract. |
| `Phase3MatrixKind` / `Phase3MatrixResult` | unchanged | Public application/service edge DTOs; rename in a later versioned contract slice. |

## Progress

- [x] (2026-08-08) Inventory completed: the two target modules have first-party imports in
  `evidence_service.py`, `signed_acceptance_evidence.py`, `phase3_harness.py`, and the two target
  unit-test modules; no package export or entry-point shim is required.
- [x] (2026-08-08) Scope constrained to internal module/test paths; no compatibility alias will be
  added and no persisted/CLI/fixture contract will be changed.
- [ ] Rename modules and tests, update imports and import-isolation assertions, and remove old paths.
- [ ] Run focused/full validation, naming/import checks, and the offscreen evidence smoke.
- [ ] Reconcile `README.md`, `docs/ARCHITECTURE.md`, the parent nomenclature plan, and this plan.
- [ ] Remove temporary artifacts/processes and commit the complete slice.

## Problem frame

The application evidence core and release-fidelity validator are neutral boundaries, but their
module paths still encode a historical project phase. That leaks obsolete vocabulary into imports,
architecture maps, and test names and encourages future callers to copy the label. The modules are
small and already isolated from Qt/Pillow/PyHanko at import time, so this is a low-risk rename-only
slice with a clear deletion gate: after migration, no live source or test import may reference either
old module path.

## Plan of work

1. Regenerate the inventory with `rg` and record every live import, test path, packaging reference,
   README/architecture mention, and `__all__` export. Confirm the frozen `docs/SPEC.md` is not in
   scope.
2. Move the two source files and two test files using repository-preserving file operations. Update
   imports in `evidence_service.py`, `signed_acceptance_evidence.py`, `phase3_harness.py`, tests,
   README, and `docs/ARCHITECTURE.md`. Rename only module/path references; retain the release
   manifest version, public `Phase3*` result types, CLI command strings, artifact names, and fixture
   paths.
3. Delete any stale compatibility re-export or import fallback discovered during the migration.
   There must be exactly one implementation for each renamed module and no `phase3_evidence_core`
   or `phase3_fidelity_contract` import in live code.
4. Add/adjust import-isolation coverage so importing `foliaseal.application.evidence_core` and
   `foliaseal.application.fidelity_contract` remains Qt/Pillow/pyHanko-free. Keep behavior tests
   unchanged apart from their renamed module path.
5. Reconcile the parent nomenclature plan with the completed first slice and record the next safe
   candidate rather than broadening this change into a harness/CLI/fixture rename.

## Validation and acceptance

- `.venv/bin/ruff check src tests scripts` passes.
- `.venv/bin/python -m pytest -q` passes with no new warnings or failures.
- `.venv/bin/python -m compileall -q src tests` passes.
- Import isolation succeeds for both new modules and the application package; neither import loads
  Qt, Pillow, or pyHanko.
- `rg -n "phase3_evidence_core|phase3_fidelity_contract" src tests scripts README.md docs/ARCHITECTURE.md`
  returns no live reference (historical ExecPlans may mention the old path only when explicitly
  marked as provenance).
- `git diff --exit-code -- docs/SPEC.md` succeeds; CLI `--help` and the existing preview/signed
  acceptance smoke retain their current command names, counts, JSON fields, and artifact paths.
- Offscreen smoke uses a temporary directory and removes it afterward. A process audit shows no
  FoliaSeal, pytest, PySide, or Qt process and no generated artifact remains in the repository.
- Architecture documentation and all active plans describe the new module names and explicitly
  record the remaining external `phase3` contracts.

## Recovery and idempotence

The rename is safe to repeat after checking `git status`. If an import migration is incomplete,
repair only the affected file and rerun the focused tests; do not add a compatibility module to make
the old path pass. If a smoke command writes output, use an explicit `/tmp/foliaseal-*` root and
remove that exact root after collecting evidence. Do not leave a GUI or harness process running.

## Interfaces and dependencies

The new module paths are internal Python imports. Their public symbols and behavior remain unchanged
in this slice. External names intentionally preserved are `phase3-signing-*`, `Phase3*` DTO names,
`phase3_fidelity_v1`, the `tests/fixtures/phase3` corpus path, and existing artifact directories.

## Revision notes

2026-08-08: Created as the first executable internal nomenclature slice after the reusable-object
Qt boundary cleanup. The scope is intentionally narrow enough to complete, validate, document, and
commit in one DevLoop while establishing the deletion/no-alias rule for subsequent renames.
