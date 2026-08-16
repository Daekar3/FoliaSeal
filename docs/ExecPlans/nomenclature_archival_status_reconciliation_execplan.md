# Reconcile Archival Nomenclature ExecPlan Status

## Purpose

The live FoliaSeal implementation, tests, README, `docs/SPEC.md`, `docs/UI_SPEC.md`, and
current architecture record now use durable evidence/acceptance terminology. Historical
`phase3` and acceptance plan files remain in `docs/ExecPlans/` as provenance, but one early
child plan still presents its already-delivered work as unchecked implementation work. This
one-slice documentation plan makes that status explicit without rewriting historical commands,
paths, or contract names.

## Scope and non-goals

In scope:

- mark `evidence_core_nomenclature_retirement_execplan.md` as superseded/completed by the
  later atomic migration recorded in `phase3_nomenclature_retirement_execplan.md`;
- clarify the no-child decision in `evidence_harness_neutral_nomenclature_execplan.md`;
- record this reconciliation in the parent nomenclature plan;
- preserve historical plan wording, old commands, paths, DTO names, fixture names, and artifact
  paths as archival evidence.

Out of scope:

- renaming or deleting historical ExecPlans or generated artifacts;
- changing CLI verbs, JSON/DTO fields, manifests, fixture directories, or artifact paths;
- changing source or tests, since the explorer audit found no live `phase3` references in those
  surfaces;
- changing frozen governing requirements.

## Progress

- [x] (2026-08-16) Explorer audit classified live contracts versus historical records and found
  no safe implementation rename remaining in source, tests, or governing docs.
- [x] (2026-08-16) The later atomic migration completed the evidence-core module/test rename
  described by the early child plan; no compatibility alias or old module path remains.
- [x] (2026-08-16) Archival child-plan markers and no-child dependency wording reconciled with
  explicit provenance notes; historical examples were intentionally left unchanged.
- [x] (2026-08-16) Focused evidence/CLI tests passed (52 tests), Ruff, compileall, diff checks,
  and CLI help validation passed; the prior clean source state remains covered by the latest
  full-suite evidence (`1535 passed, 20 skipped, 1 warning`).
- [x] (2026-08-16) Independent compliance review and architecture-steward review found only two
  present-tense archival wording ambiguities; both were corrected without changing contracts.
- [x] (2026-08-16) Commit `6debad2ef` recorded the four-file reconciliation; the final audit
  found a clean worktree, clean diff check, no live nomenclature references, and no FoliaSeal,
  pytest, Qt, or GUI processes.

## Plan of work

1. Update the early evidence-core child plan so its four unchecked execution bullets state that
   the work was superseded and delivered by the later atomic migration, with validation evidence.
2. Mark the no-child dependency decision in the neutral harness plan as resolved, retaining its
   conditional rationale for future audits.
3. Add an archival-status entry to the parent nomenclature plan; do not rewrite historical plan
   body text or remove its old terminology.
4. Run focused CLI/evidence checks, static validation, and repository/process cleanup audit.

## Validation and acceptance

- `rg -i 'phase3|phase 3|Phase3' src tests scripts README.md docs/SPEC.md docs/UI_SPEC.md`
  returns no matches.
- Focused evidence tests and `python -m foliaseal --help` pass without changing command or
  serialized contract names.
- Ruff, compileall, and `git diff --check` pass.
- The final diff contains only intended documentation/ExecPlan changes; no FoliaSeal, Qt,
  pytest, dialog, temporary artifact, or core process remains.
- Historical plan references remain present and are clearly archival rather than active work.

## Recovery and idempotence

This pass is text-only and safe to repeat after checking `git status`. If a historical paragraph
appears to describe a current contract, leave it intact and add a status note rather than
rewriting provenance. Use only bounded temporary roots for any smoke command and remove them
before the final audit.

## Completion

The plan is complete when archival markers, validation evidence, the parent status note, and the
commit are recorded. Remaining display-backed, privileged-host, and final-release gates are
external acceptance work and are not silently closed by this status reconciliation.
