# Extract evidence gateways and begin neutral nomenclature cleanup

This ExecPlan is a living document. It is written and maintained according to `.agents/skills/write-execplan/PLANS.md`. Milestones are progress markers, not stopping points: the complete slice includes implementation, validation, compliance review, documentation reconciliation, and commit.

## Purpose / Big Picture

The Qt evidence tooling currently has a large `phase3_harness.py` composition root. That file still builds the interactive capture runner and both matrix operations, so a change to one evidence mode requires navigating a monolithic module and importing its heavy Qt/PDF dependency graph. This slice makes the three evidence lifecycles explicit at a neutral gateway boundary, moves the composition adapters out of the monolith, and starts removing `phase3` from new internal names. The result remains observable through the existing preview and signed-acceptance commands and produces the same capture JSON, matrix summaries, artifact paths, and intentional rejection behavior.

The naming cleanup is deliberately bounded. Existing CLI commands, artifact directory names, JSON keys, application request/result DTOs, and historical public class names remain stable because they are external contracts. New gateway and artifact-boundary modules use neutral evidence names, private forwarding helpers are removed or renamed, and the old matrix artifact module is replaced rather than left as a compatibility shim. A later slice may migrate the remaining DTOs and filenames after their external consumers are versioned.

## Child ExecPlan Dependencies

No child ExecPlan is required for this one-slice implementation. If compliance review discovers a contract discrepancy that cannot be fixed within this slice, create a child ExecPlan before changing scope; do not silently broaden the rename.

## Progress

- [x] (2026-08-02) Fresh explorer-light reviewed the live checkout, identified the three safe composition adapters, confirmed stable contracts, and reported 28 focused evidence/matrix tests passing on clean `fa241e1d2`.
- [x] (2026-08-02) Hybrid design selected: three explicit gateways plus a narrow filesystem/in-memory artifact port; no generic tagged dispatcher or service locator.
- [x] (2026-08-02) Wrote `evidence_gateways.py` and `evidence_artifacts.py`, migrated both matrix runners, and composed the application service through explicit lazy gateways.
- [x] (2026-08-02) Removed the three composition adapters from `phase3_harness.py`, renamed the private interactive builder and CLI validation callback, and preserved CLI strings and artifact paths.
- [x] (2026-08-02) Migrated artifact-port tests and added gateway laziness/request-forwarding/import-isolation coverage; focused suite passes 116 tests.
- [x] (2026-08-02) Ran the focused suite (116 passed), Ruff, import isolation, CLI help, and full suite (1043 passed, 1 existing Pillow deprecation warning); fixed the preview authoritative-path discrepancy found by the high-risk review.
- [x] (2026-08-02) Completed two independent compliance reviews and reconciled README and `docs/ARCHITECTURE.md` with architecture-steward; no child plan was needed after the path fix.
- [x] (2026-08-02) Ran preview smoke (4 scenarios) and signed-acceptance smoke (3 scenarios) with temporary artifact roots; both persisted and reported matching authoritative `summary_json_path` values. The signed run required `QT_QPA_PLATFORM=offscreen` because the default xcb display was unavailable.
- [x] (2026-08-02) Completed cleanup audit: Ruff and `git diff --check` passed, no live removed-builder/deleted-module references remain, temporary roots were removed, and no FoliaSeal process or core file was left behind.
- [ ] Create the final git commit through the write-git-commit workflow and record its hash.

## Surprises & Discoveries

- Observation: The earlier broad composition plan named a nonexistent `tests/unit/test_phase3_matrix_artifacts.py` file.
  Evidence: The live checkout has artifact-port assertions in `tests/unit/test_phase3_signed_acceptance_lifecycle.py` and `tests/unit/test_phase3_signed_acceptance_matrix_runner.py`; validation commands must name those files instead.
- Observation: `Phase3MatrixArtifactPort` is a real narrow seam, while the preview runner still writes its summary directly and the signed runner intentionally writes twice so `summary_json_path` is included in the authoritative second document.
  Evidence: `phase3_signed_acceptance_matrix_runner.py` calls `write_summary` before and after adding `summary_json_path`; the slice must preserve that sequence.
- Observation: CLI labels, artifact paths, JSON keys, and `Phase3*` application DTOs are externally consumed even though the label is no longer useful internally.
  Evidence: `src/foliaseal/__main__.py`, evidence-service tests, and matrix acceptance tests assert those values.
- Observation: The first preview-port migration discarded the adapter-returned path, which would make custom adapters report the fallback path.
  Evidence: Independent high-risk review found `normalize_matrix_result()` would fall back to `artifacts_dir/summary.json`; preview now records the returned path and performs the same second serialization pass as signed acceptance.

## Decision Log

- Decision: Use three explicit gateway objects (`InteractiveEvidenceGateway`, `PreviewEvidenceGateway`, and `SignedAcceptanceEvidenceGateway`) with `.run(request)` methods and lazy factories.
  Rationale: The lifecycles have different dependencies and side effects; explicit gateways deepen the shallow composition seam without creating a second `run(kind, payload)` dispatcher.
  Date/Author: 2026-08-02 / Codex.
- Decision: Introduce `evidence_artifacts.py` with neutral `EvidenceArtifactPort`, filesystem, and memory adapters and remove `phase3_matrix_artifacts.py` rather than adding a compatibility re-export.
  Rationale: This is a small, fully-tested internal seam and is the safest concrete start to stripping obsolete nomenclature. Existing artifact paths and serialization remain unchanged.
  Date/Author: 2026-08-02 / Codex.
- Decision: Preserve CLI command strings, `DEFAULT_PHASE3_*` artifact paths, `Phase3*` application DTOs, and the remaining historical module names in this slice.
  Rationale: Renaming those values would silently break automation and evidence consumers; neutral gateway names provide progress without an unversioned external migration.
  Date/Author: 2026-08-02 / Codex.
- Decision: Keep the signed artifact port's two-write behavior and migrate preview summary publication to the same port, including a second write after recording the returned authoritative path.
  Rationale: Sharing the narrow publication boundary removes direct filesystem work from the preview runner while ensuring custom artifact adapters cannot be silently replaced by the fallback `artifacts_dir/summary.json` path.
  Date/Author: 2026-08-02 / Codex.

## Outcomes & Retrospective

The slice extracted explicit lazy interactive, preview, and signed-acceptance gateways into `evidence_gateways.py`, moved matrix summary publication into neutral `evidence_artifacts.py`, removed the old artifact module and private forwarding wrappers, and renamed the private interactive/CLI validation builders. Stable CLI command strings, artifact paths, JSON fields, and `Phase3*` DTOs were intentionally retained. Focused tests (116) and the full suite (1043) pass; preview and signed smoke runs verified authoritative summary paths; the only warning is the pre-existing Pillow deprecation. The next architecture slice should migrate additional internal DTO/module names only after an explicit external-contract inventory and should continue deleting compatibility facades rather than adding aliases.

## Context and Orientation

The application layer in `src/foliaseal/application/phase3_evidence_service.py` accepts callable boundaries for interactive capture, preview matrices, and signed-acceptance matrices. `src/foliaseal/presentation/qt/phase3_signed_acceptance_evidence.py` currently assembles those callables, while `src/foliaseal/presentation/qt/phase3_harness.py` constructs the concrete Qt/PDF runners and contains unrelated rendering helpers. `src/foliaseal/presentation/qt/phase3_interactive_capture.py` owns the stable capture DTO and lazy runner contract. The two matrix runners publish `summary.json`; signed acceptance also preserves the path in a second authoritative write. Tests under `tests/unit/` exercise these contracts.

In this plan, a gateway is a small object with one explicit `run` method that hides lazy construction of one evidence lifecycle. An artifact port is a tiny interface for preparing an artifact directory and writing its JSON summary; it is not a general storage system. “Neutral nomenclature” means new internal files, functions, and boundary types use `evidence` instead of `phase3`; it does not mean changing unversioned external command names in this slice.

## Plan of Work

First create `src/foliaseal/presentation/qt/evidence_gateways.py`. Define typed request aliases and three explicit gateway classes. Each class lazily constructs exactly one existing concrete runner and forwards the fields of `Phase3HarnessCaptureRequest` or `Phase3MatrixRequest` without changing their shape. Provide `build_interactive_evidence_gateway`, `build_preview_evidence_gateway`, and `build_signed_acceptance_evidence_gateway`; keep heavy Qt/PDF imports inside the factory closures so importing the application evidence service remains headless-safe. Do not add a tagged operation registry.

Next create `src/foliaseal/presentation/qt/evidence_artifacts.py` by moving the existing prepare/write behavior into neutral `EvidenceArtifactPort`, `FilesystemEvidenceArtifactPort`, and `MemoryEvidenceArtifactPort` types. Update `phase3_signed_acceptance_matrix_runner.py` to use these names and update `phase3_preview_matrix_runner.py` to receive an optional artifact-port factory, defaulting to the filesystem adapter. Preserve directory creation, newline/indent/sort-key JSON serialization, and the signed runner's two writes.

Then remove `_build_preview_matrix_operation` and `_build_signed_acceptance_matrix_operation` from `phase3_harness.py`. Rename `_build_phase3_interactive_harness_runner` to `_build_interactive_evidence_runner` and update the lazy capture boundary to import that new private builder. Replace the local forwarding closures in `phase3_signed_acceptance_evidence.py` with the three neutral gateway factories; the application service still receives plain callables (`gateway.run`) and therefore keeps its public contract. Rename the private CLI callback `_run_phase3_harness_validate` to `_run_evidence_harness_validate`, but leave the parser command, help text, output paths, and `DEFAULT_PHASE3_*` constants unchanged.

Update tests to import the neutral artifact adapters and to patch/test gateway factories instead of removed private operation wrappers. Add coverage proving each gateway constructs lazily, forwards every request field, and does not import the heavy harness module during gateway-module import. Add preview-runner coverage for injected in-memory artifacts and retain signed two-write/path assertions. Update `README.md` and `docs/ARCHITECTURE.md` to describe the neutral gateway/artifact boundary, explicitly list retained external `phase3` names as compatibility contracts, and remove references to the deleted artifact module. Do not revive stale historical ExecPlans; note this plan as the current active slice.

Finally run the focused evidence tests, the complete test suite, lint/type checks used by the repository, import-isolation subprocess checks, both matrix commands with temporary artifact directories, and a repository/process cleanup audit. Search for removed private builders and the deleted artifact module; any remaining occurrences must be either stable external names or historical documentation explicitly marked as such. Update this plan after every milestone and finish by committing all intended changes.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

1. Inspect and edit the modules named above with `apply_patch`; keep the working tree on `main` and do not reset unrelated user changes.
2. Run the focused suite:

       .venv/bin/python -m pytest -q tests/unit/test_phase3_harness.py tests/unit/test_phase3_matrix_operations.py tests/unit/test_phase3_evidence_service.py tests/unit/test_phase3_evidence_orchestrator.py tests/unit/test_phase3_preview_matrix_runner.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_signed_acceptance_lifecycle.py

   Expect all selected tests to pass; the exact count is recorded in `Artifacts and Notes` after execution.
3. Run import and naming checks:

       .venv/bin/python -c "import foliaseal.presentation.qt.evidence_gateways; import foliaseal.presentation.qt.evidence_artifacts"
       rg -n "_build_preview_matrix_operation|_build_signed_acceptance_matrix_operation|phase3_matrix_artifacts" src tests README.md docs/ARCHITECTURE.md

   The first command must succeed without constructing Qt state. The search may show this plan or historical plans, but must show no live import or removed private builder.
4. Exercise preview and signed matrix runners with their existing repository commands and temporary directories. Confirm a `summary.json` is produced, retains existing keys, and the signed summary's second write contains `summary_json_path`. Remove temporary directories and terminate every process started for validation.
5. Run the repository lint/test commands (at minimum `.venv/bin/ruff check src tests` and `.venv/bin/python -m pytest -q`) and record the results. If an environment-specific optional GUI dependency prevents a command, record the exact error and run the closest headless validation instead.
6. Inspect `git diff --check`, `git status --short`, and the process list. The final tree must contain only intended source, test, documentation, and ExecPlan changes; no Qt dialog, harness, or temporary artifact process may remain.

## Validation and Acceptance

Acceptance is behavioral. Importing `evidence_gateways` and `evidence_artifacts` must not import or construct the heavy Qt harness graph. Building the application evidence service must remain lazy. A preview request must return the same summary counters and result rows and write the same `summary.json`; a signed request must preserve intentional rejection rows, `timestamping_mode`, and the authoritative `summary_json_path`. Interactive capture must emit the same JSON fields and captured-state data. Existing CLI command names and artifact paths must continue to work unchanged. Focused and full tests, lint, import isolation, and matrix smoke runs must pass, and no removed private builder or deleted artifact-module import may remain in live code.

## Idempotence and Recovery

All edits are additive until imports and tests pass; deleting the old artifact module happens only after every live import is migrated. Re-running tests is safe because matrix smoke runs use a temporary directory. If a migration fails, restore only the affected file from the working diff (never `git reset --hard`) and rerun the focused tests. Do not leave generated artifacts in the repository or background GUI processes running.

## Artifacts and Notes

Recorded evidence: focused evidence/matrix suite 116 passed; full suite 1043 passed with one pre-existing Pillow deprecation warning; Ruff clean; gateway and CLI import isolation clean; documentation worker updated README and `docs/ARCHITECTURE.md`; independent reviews found and resolved the preview authoritative-path discrepancy. Add matrix smoke paths, cleanup result, and final commit hash before closing the plan.

## Interfaces and Dependencies

At completion, `src/foliaseal/presentation/qt/evidence_gateways.py` must expose three explicit gateway classes with `run` methods and the three lazy builder functions named in the Plan of Work. `src/foliaseal/presentation/qt/evidence_artifacts.py` must expose `EvidenceArtifactPort`, `FilesystemEvidenceArtifactPort`, and `MemoryEvidenceArtifactPort`, each implementing `prepare(artifacts_dir: str) -> Path` and `write_summary(artifacts_dir: Path, summary: Mapping[str, Any]) -> str`. The matrix runners depend only on these narrow ports; the application evidence service depends only on callable gateway methods; Qt/PDF libraries remain presentation-edge dependencies.

## Revision Notes

2026-08-02: Initial one-slice plan created after the required fresh explorer review. The scope combines the recommended hybrid gateway extraction with a bounded internal nomenclature cleanup, while explicitly preserving stable external `phase3` contracts.
2026-08-02: Updated after independent compliance reviews to document the preview authoritative-path fix, architecture/README reconciliation, full-suite and smoke evidence, and cleanup audit. The final commit remains the only open progress item.
