# Deepen interactive evidence capture and remove obsolete internal Phase 3 naming

This ExecPlan is a living document and must be maintained in accordance with
`.agents/skills/write-execplan/PLANS.md`. It is a complete one-slice DevLoop:
boundary extraction, compatibility-cruft removal, tests, architecture/spec
review, documentation reconciliation, nomenclature audit, and commit closure
all belong to this plan. Milestones organize the work; they are not stopping
points.

## Purpose / Big Picture

The command that captures one interactive signing run currently crosses the
large `phase3_harness.py` composition root for DTO construction, while
`evidence_interactive_capture.py` already owns the session, artifact, and
report choreography. This split makes the most important capture result pass
through a large dictionary and a private Phase 3-named builder before it can
be validated or written. It also leaves a dead lazy wrapper and duplicated
composition aliases in the harness module.

After this slice, one interactive capture will use an explicit
`InteractiveCaptureEngine` boundary. The engine will own capture finalization
and report input construction, while the Qt session runner remains responsible
for QApplication/window lifecycle and the existing assembler remains responsible
for stable evidence fields. Existing CLI commands, JSON keys, contract version,
summary/checklist paths, artifact names, and acceptance behavior will remain
unchanged. Internal builder aliases and dead wrappers will be removed or
renamed to neutral evidence terminology. The user-visible proof is a green
`phase3-signing-harness` capture with byte-compatible JSON structure and the
same report paths, plus a focused test that constructs the engine without
loading Qt/Pillow/pyHanko until execution.

The nomenclature track is deliberately explicit. The touched interactive
boundary will not introduce or retain obsolete internal `phase3` labels; old
stable external command names, serialized DTO names, JSON fields, artifact
paths, and historical records remain at the compatibility edge until a
separate migration can update consumers and fixtures together.

## Child ExecPlan Dependencies

- [x] Fresh DevLoop explorer reviewed the live capture stack and stable
  contracts on 2026-08-03.
- [x] Minimal, extensible, and common-caller interface designs were compared;
  the recommended hybrid is selected.
- [x] Compliance review findings were fixed inside the interactive capture
  boundary; no child compliance ExecPlan was required.
- [ ] If a future compliance review finds a gap that cannot be fixed inside the
  interactive capture boundary, create a child compliance ExecPlan before
  unrelated edits.

## Progress

- [x] (2026-08-03) Confirmed clean `main` at `cc0edc58c`.
- [x] (2026-08-03) Completed the required fresh DevLoop exploration and
  acknowledged the bounded-slice recommendation before authoring this plan.
- [x] (2026-08-03) Selected the hybrid: one typed interactive capture engine
  boundary with separate existing session and assembler collaborators.
- [x] (2026-08-03) Created this living ExecPlan before implementation.
- [x] Move capture DTO construction/report-input finalization out of
  `phase3_harness.py` and into the interactive capture boundary.
- [x] Remove the dead lazy capture wrapper and obsolete internal builder aliases.
- [x] Add parity, lazy-import, and boundary tests; preserve external output.
- [x] Complete architecture/spec review, documentation reconciliation, and
  touched-scope `phase3` inventory.
- [x] Run the full suite, clean-process/artifact audit, and commit closure.

## Surprises & Discoveries

- Observation: `InteractiveEvidenceRunner.run()` already owns the common
  interactive flow, but its `capture_factory` points back into `phase3_harness.py`.
  Evidence: `evidence_interactive_capture.py:89-183` and
  `evidence_runner_factories.py:50-83`.
- Observation: `_build_phase3_harness_capture` is a large dictionary-to-DTO
  projection with no independent Qt requirement.
  Evidence: `phase3_harness.py:116-170`.
- Observation: `build_interactive_evidence_capture_runner()` has no production
  caller; production uses the lazy operation factory.
  Evidence: `evidence_runner_factories.py:145+` and test-only references in
  `tests/unit/test_phase3_harness.py`.
- Observation: `Phase3HarnessCapture` fields and sorted two-space JSON are
  stable downstream contracts, while `Phase3HarnessCaptureAssembler` payload
  keys are documented evidence fields.
  Evidence: `evidence_interactive_capture.py:28-76`,
  `phase3_harness_capture_assembler.py`, and `docs/ARCHITECTURE.md:644-652`.
- Observation: preview capture still forwards certificate/passphrase into
  `SigningDraftWorkflow`; this slice must not invent fake credentials or alter
  invalid-credential error rows.
  Evidence: fresh explorer review of `evidence_interactive_capture.py:120-136`
  and headless matrix workflow construction.
- Observation: Qt/Pillow/pyHanko imports must remain lazy for default program
  construction.
  Evidence: `evidence_runner_factories.py` and import-isolation tests.

## Decision Log

- Decision: Introduce `InteractiveCaptureEngine` as the deep boundary and move
  only final capture DTO/report-input construction into it.
  Rationale: this is the smallest complete vertical slice that removes a
  concrete composition leak without merging Qt lifecycle, matrices, or artifact
  lifecycles.
  Date/Author: 2026-08-03 / Codex.
- Decision: Keep `Phase3HarnessCapture` and assembler field names unchanged at
  the evidence edge.
  Rationale: CLI consumers, JSON fixtures, report generation, and acceptance
  tooling depend on those names and schema semantics.
  Date/Author: 2026-08-03 / Codex.
- Decision: Rename internal `InteractiveEvidenceRunner` and builder helpers to
  neutral capture terminology where all repository callers can migrate in one
  slice; do not rename public `phase3-signing-harness` or serialized names.
  Rationale: remove obsolete internal nomenclature without breaking external
  automation.
  Date/Author: 2026-08-03 / Codex.
- Decision: Delete the test-only `build_interactive_evidence_capture_runner`
  wrapper after updating its test to use the production lazy factory.
  Rationale: duplicate lazy gateways are compatibility cruft and have no
  production consumer.
  Date/Author: 2026-08-03 / Codex.

## Outcomes & Retrospective

Completed 2026-08-03. The interactive capture boundary now exposes
`InteractiveCaptureEngine.run(request)` and the neutral
`build_capture_from_payload(...)` projection. The Qt composition root still
owns render, workspace, session, and matrix collaborators; the engine owns
workflow/report choreography and final DTO construction. The former private
`_build_phase3_harness_capture`, `_Phase3HarnessCapture`, `_jsonable_capture`,
`InteractiveEvidenceRunner`, and test-only
`build_interactive_evidence_capture_runner()` names were removed after all
repository callers migrated. Neutral lazy entry points are
`build_interactive_capture_engine()` and `build_interactive_capture_operation()`.

Stable `Phase3HarnessCapture` fields, `phase3_evidence_v1`, CLI names, JSON
keys, summary/checklist paths, artifact naming, contract verdicts, and captured
state diagnostics remain unchanged. The all-field projection test and sorted
two-space JSON assertion pass. Direct capture-module import/construction and
default `EvidenceProgram` construction remain free of Qt/Pillow/pyHanko
imports. The architecture review passed after README and architecture-map
reconciliation; historical plan references retain old names only to explain
the migration, not as live APIs.

Validation: focused capture/evidence slice 112 passed with one existing Pillow
deprecation warning; full suite 1028 passed with the same warning. Ruff,
compileall, diff-check, and process/artifact audits passed. The implementation
and documentation were committed together; the final commit hash is recorded
in the closure revision below.

## Context and Orientation

`src/foliaseal/application/evidence_service.py` defines the application
`EvidenceCaptureRequest` and the stable `CaptureResultPort` boundary. The CLI
builds that request and dispatches the explicit `EvidenceProgram.capture`
verb. The application boundary must remain Qt-free.

`src/foliaseal/presentation/qt/evidence_interactive_capture.py` owns the live
`InteractiveCaptureEngine`, stable `Phase3HarnessCapture` DTO, JSON serialization,
artifact path policy, and report finalization inputs. It is the correct home for
capture finalization because it already owns session/report choreography.

`src/foliaseal/presentation/qt/phase3_harness.py` is a large Qt/Pillow/pyHanko
composition and analysis root. It should continue supplying behavior-bearing
render/workspace/session collaborators in this slice, but it must stop owning
the final capture DTO projection and duplicate lazy wrapper aliases.

`phase3_harness_capture_assembler.py` converts session state into the stable
dictionary payload consumed by report validation. It remains unchanged except
for type/import cleanup required by the moved finalizer. The Qt session runner
continues to own QApplication/window setup, event processing, callbacks, and
cleanup. Matrix runners and their artifact lifecycles are explicitly outside
this slice.

## Plan of Work

Add a typed `InteractiveCaptureEngine` in
`src/foliaseal/presentation/qt/evidence_interactive_capture.py`. It will retain
the existing runner dependencies, expose `run(request)`, and contain a private
or module-level neutral `build_capture_from_payload(...)` function that maps
the assembler payload plus contract result to `Phase3HarnessCapture`. The
engine will call this boundary through the existing report finalizer and will
not import Qt/Pillow/pyHanko at module import time.

Update `evidence_runner_factories.py` to construct the renamed engine and pass
the neutral capture builder directly from `evidence_interactive_capture.py`.
Remove the import of the private capture builder from `phase3_harness.py` while
retaining the behavior-bearing assembler/session helper factories until their
callers are separately migrated. Preserve lazy imports and import-isolation
tests.

The obsolete `build_interactive_evidence_capture_runner()` wrapper and duplicate
aliases such as `_Phase3HarnessCapture` and `_jsonable_capture` were removed after
repository-wide caller migration. The production lazy entry points are now
`build_interactive_capture_engine()` and `build_interactive_capture_operation()`;
do not bulk-delete private render or matrix helpers, which still have active callers.

Migrate `tests/unit/test_phase3_harness.py`, evidence factory tests, service/
program tests, and reporting/assembler tests to exercise the engine directly
where they currently construct the old runner or private builder. Add parity
assertions for every stable capture field, sorted two-space JSON, report paths,
contract verdict, checklist text, and captured-state diagnostics. Add an
import-isolation assertion that default `EvidenceProgram` construction does
not load Qt/Pillow/pyHanko.

Run a touched-scope nomenclature audit. Rename obsolete internal
`InteractiveEvidenceRunner`, `_build_phase3_harness_capture`, and duplicate
lazy wrapper labels where repository callers can migrate. Record stable
`phase3-signing-harness`, `Phase3HarnessCapture`, `phase3_evidence_v1`, JSON
keys, artifact paths, and historical docs as intentionally preserved external
contracts. Do not resurrect the historical `phase3_interactive_capture.py`
module named in older ExecPlans.

## Milestones

### Milestone 1: Capture finalization boundary

The neutral builder and `InteractiveCaptureEngine` exist in the live
interactive capture module. Focused tests prove a synthetic assembler payload
becomes the exact stable capture DTO and JSON without loading Qt.

### Milestone 2: Factory migration and cruft removal

The lazy factory constructs the engine and neutral builder directly. The old
private phase3 capture builder and test-only lazy wrapper are gone, all tests
use the new boundary, and active harness/session/matrix behavior is unchanged.

### Milestone 3: Compliance and closure

Run focused and full validation, review architecture/spec compliance, reconcile
README and architecture docs, record the nomenclature inventory, audit processes
and generated artifacts, and commit the implementation plus living plan.

## Concrete Steps

Run commands from `/home/daekar/FoliaSeal`.

    rg -n "InteractiveEvidenceRunner|build_interactive_evidence_capture_runner|_build_phase3_harness_capture|_Phase3HarnessCapture|_jsonable_capture" src tests
    .venv/bin/python -m pytest -q tests/unit/test_phase3_harness.py tests/unit/test_phase3_harness_capture_assembler.py tests/unit/test_phase3_harness_reporting.py tests/unit/test_phase3_harness_session_runner.py tests/unit/test_evidence_runner_factories.py tests/unit/test_evidence_service.py tests/unit/test_evidence_program.py

After migration, run:

    .venv/bin/python -m pytest -q
    .venv/bin/ruff check src tests
    .venv/bin/python -m compileall -q src tests
    git diff --check
    rg -n -i "phase3" src/foliaseal/presentation/qt/evidence_interactive_capture.py src/foliaseal/presentation/qt/evidence_capture_engine.py tests/unit/test_evidence_runner_factories.py || true
    ps -eo comm= | rg '^(python|python3|foliaseal)$' || true
    git status --short

Expected results are green focused/full suites, clean lint/compile/diff checks,
no obsolete internal builder/wrapper names, no new `phase3` names in the
neutral capture boundary, stable external JSON/artifact contracts, no project
processes, and a clean tree after commit.

## Validation and Acceptance

An existing `phase3-signing-harness` invocation must still write the same
summary JSON, checklist results, and artifact paths, with the same stable field
names, contract version, gate verdict, and captured-state diagnostics. When no
summary path is provided, the CLI must still print the capture JSON and review
instructions.

The engine boundary tests must pass without importing Qt/Pillow/pyHanko during
default application construction. Session lifecycle tests must still prove
QApplication/window cleanup in `finally`. Report and assembler tests must prove
all stable fields survive the moved builder. Full suite, Ruff, compileall, and
diff checks must pass. Architecture review must confirm that lifecycle and
matrix ownership remain separate, compatibility cruft is removed only after
caller migration, and stable evidence contracts were not silently renamed.

## Idempotence and Recovery

The changes are safe to repeat because tests use temporary PDFs, certificates,
artifact directories, and fake session/report collaborators. Keep the old
builder only until all repository callers migrate; if a hidden import is found,
move it to the explicit compatibility serializer rather than restoring a
private phase3 alias. Never rename stable CLI/JSON/artifact contracts without a
fixture-backed migration. If a full harness test fails, first compare the
pre/post `Phase3HarnessCapture.to_json()` output before changing behavior.

## Artifacts and Notes

Record concise evidence here at completion:

    focused capture/evidence tests: 112 passed, 1 existing Pillow deprecation warning
    full suite: 1028 passed, 1 existing Pillow deprecation warning
    stable capture JSON/artifact parity: pass
    phase3 inventory: obsolete internal names removed; stable external contracts retained
    import isolation: direct capture module and default program construction remain headless
    process audit: no FoliaSeal/Python process; no generated artifacts left untracked
    implementation and plan-closure commit hashes: recorded in final revision notes

Generated harness artifacts must remain ignored or temporary and must be
removed after manual checks. No GUI process, dialog, certificate, or generated
file may remain open or untracked.

## Interfaces and Dependencies

The live capture module must expose a contract equivalent to:

    @dataclass(frozen=True)
    class InteractiveCaptureEngine:
        load_qt_harness_bindings: Callable[[], _QtHarnessBindings]
        ...
        def run(self, request: EvidenceCaptureRequest) -> Phase3HarnessCapture: ...

    def build_capture_from_payload(
        *, capture_payload: Mapping[str, Any], contract: Any,
        summary_json_path: str | None, checklist_results_path: str,
        checklist_results_written: bool,
    ) -> Phase3HarnessCapture: ...

The engine depends on `Phase3HarnessCaptureAssembler`,
`Phase3HarnessReportRequest`, the contract evaluator, checklist renderer,
report finalizer, and artifact policy through injected collaborators. It must
not own Qt lifecycle or matrix execution. `CaptureResultPort.to_json()` remains
the application boundary; `Phase3HarnessCapture` remains the stable evidence
DTO until a separate serialized-contract migration exists.

## Revision Notes

2026-08-03: Created after a fresh DevLoop exploration and the recommended
common-caller/minimal hybrid comparison. Bounded the slice to interactive
capture finalization and dead composition-wrapper removal, explicitly keeping
Qt lifecycle, matrices, stable evidence fields, and external Phase 3 names
outside the destructive rename scope.
