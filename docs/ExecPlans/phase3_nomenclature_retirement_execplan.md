# Retire the Historical Phase 3 Nomenclature

This is a bounded follow-up ExecPlan from the architecture-improvement loop. It removes the
historical `phase3` label from implementation-facing names now that the acceptance/evidence system
is a continuing product capability rather than a temporary phase. The plan must be executed as one
coherent migration slice and maintained under `.agents/skills/write-execplan/PLANS.md`.

## Purpose

Replace obsolete `phase3`/`Phase3` nomenclature across source modules, Python symbols, CLI-facing
documentation, tests, fixtures, and active ExecPlans with names that describe the durable capability:
`acceptance`, `evidence`, `preview_matrix`, `signed_acceptance`, or `interactive_harness`. Remove
compatibility aliases and stale plan references once the repository-wide inventory proves that no
V1 contract requires the historical spelling. `docs/SPEC.md` remains frozen.

## Scope and naming map

Inventory every tracked path with case-insensitive `phase3` before editing. Classify each occurrence
as a Python module/path, public CLI command, DTO/type/field, serialized/artifact path, test/fixture,
documentation/plan text, or historical record. The default replacements are:

- `phase3_harness*` -> `acceptance_harness*` or `interactive_harness*` according to behavior.
- `phase3_signed_acceptance*` -> `signed_acceptance*`.
- `phase3_preview_matrix*` -> `preview_matrix*`.
- `Phase3Harness*` -> `AcceptanceHarness*` or a narrower `Harness*` type.
- `Phase3*Evidence*` -> `AcceptanceEvidence*`/`Evidence*`.
- `phase3-signing-*` CLI commands -> durable `acceptance-*`/`preview-matrix` names only after
  parser, README, tests, and release evidence are migrated together.

Do not rename opaque persisted JSON keys, artifact schemas, or external commands piecemeal. For each
such occurrence, either migrate the contract in the same slice with an explicit versioned reader/writer
change, or record it as a non-renamable compatibility boundary. The preferred V1 outcome is removal,
not a permanent alias; any retained reader must have a dated retirement criterion and no new caller.

## Required migration

1. Capture the complete inventory and identify all import edges, `__all__` exports, packaging entry
   points, fixtures, generated-artifact paths, README/docs links, and active ExecPlans.
2. Choose the replacement name per occurrence using the map above and add a temporary mapping table
   to this plan. Reject ambiguous blanket replacements.
3. Rename modules and symbols atomically with their imports, tests, fixtures, scripts, CLI parser
   branches, help text, and documentation. Keep behavior, result fields, exit codes, artifact
   contents, and acceptance counts unchanged unless an explicitly versioned contract is migrated.
4. Delete stale compatibility aliases, duplicate imports, old module shims, and completed plans whose
   only purpose was the historical phase label. Do not leave a second implementation under the old
   name.
5. Update `docs/ARCHITECTURE.md`, README, active parent/child ExecPlans, and release instructions to
   describe the durable acceptance/evidence capabilities without phase language. Do not rewrite
   immutable historical evidence; annotate archival references only where needed for provenance.

## Acceptance contract

- `docs/SPEC.md` is byte-for-byte unchanged.
- `rg -ni "phase3|phase 3|Phase3" src tests scripts README.md docs --glob '!docs/ExecPlans/phase3_nomenclature_retirement_execplan.md'`
  returns no active implementation, test, CLI, or architecture/documentation references; any
  retained archival/provenance lines are explicitly listed in this plan with rationale.
- No old module import, symbol alias, CLI branch, fixture path, or compatibility shim remains unless
  its non-renamable external-contract rationale and retirement date are recorded.
- Full tests, Ruff, CLI parser tests, preview/signed acceptance matrices, and artifact/process cleanup
  pass with the same expected scenario counts and acceptance status.
- Import isolation remains true for `foliaseal.application`; no Qt/Pillow/pyHanko import leaks into
  the neutral application boundary.
- `docs/ARCHITECTURE.md`, README, and all active ExecPlans agree on the new names.

## Validation commands

    rg -ni "phase3|phase 3|Phase3" src tests scripts README.md docs
    .venv/bin/ruff check src tests scripts
    .venv/bin/pytest -q
    .venv/bin/python -m foliaseal --help
    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal preview-matrix --help
    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal signed-acceptance --help

Run the existing preview and signed release matrices in explicit `/tmp/foliaseal-*` directories,
remove those directories after collecting summaries, and audit for leftover FoliaSeal/Python
processes. Commit the migration in intentional groups: implementation/renames, tests/fixtures, then
docs and plan reconciliation.

## Out of scope

No signing-policy changes, GUI redesign, schema redesign unrelated to the naming migration, new
acceptance scenarios, or edits to frozen `docs/SPEC.md`. If a persisted or external contract cannot
be renamed safely in this slice, leave it unchanged and record the exact boundary rather than adding
an unbounded compatibility layer.

## Status

- [x] Plan created from the signing-workspace hybrid slice on 2026-08-05.
- [x] Current external-contract boundary recorded: established `phase3` CLI commands, DTO/type
  names, JSON fields, fixtures, and artifact paths remain unchanged until an atomic migration is
  approved and validated.
- [ ] Inventory and replacement mapping recorded.
- [ ] Atomic rename/migration implemented.
- [ ] Compatibility debris removed and validation completed.
- [ ] Architecture/README/ExecPlans reconciled and committed.
