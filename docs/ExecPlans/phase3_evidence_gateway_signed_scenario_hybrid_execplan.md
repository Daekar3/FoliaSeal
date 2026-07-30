# Deepen the Phase 3 evidence gateway and signed-acceptance scenario boundary

This ExecPlan is a living document. Maintain it in accordance with `.agents/skills/write-execplan/PLANS.md`. Keep `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` current at every stopping point.

## Purpose / Big Picture

After this slice, automated callers can request a Phase 3 preview or signed-acceptance run through typed application results instead of depending on untyped summary dictionaries. The signed-acceptance matrix will also run through an explicit lifecycle port: the matrix runner will no longer own the Qt application/window open, event processing, and close choreography directly. The existing workspace port remains the shell scenario boundary, while a typed scenario result makes the apply-capture-rewrite-sign-output flow testable without a live Qt window.

The user-visible proof is unchanged but stronger: running the existing preview and signed-acceptance CLI commands still produces the same `summary.json` contracts and acceptance counters, while unit tests can exercise the signed scenario loop with in-memory lifecycle, workspace, artifact, and signing substitutes. A failed scenario remains an evidence row rather than leaking a Qt dialog or leaving a process open.

## Child ExecPlan Dependencies

- [x] Fresh explorer reconnaissance completed and reviewed. It identified `Phase3EvidenceService` as the existing CLI-facing boundary and the signed-acceptance matrix runner plus scenario executor/workspace adapter as the highest-friction seam.
- [x] The preceding visible-signature layout boundary slice is complete and committed; this plan must not modify that completed architecture slice.
- [x] No child ExecPlans are required. The gateway typing, lifecycle/artifact ports, scenario-result normalization, tests, documentation, compliance review, and commit are one deliberately bounded implementation slice.

## Progress

- [x] (2026-07-29) Selected the constrained C+D hybrid: deepen `Phase3EvidenceService` for common callers, and introduce only the lifecycle/artifact ports needed to isolate signed-acceptance orchestration.
- [x] (2026-07-29) Completed the required fresh explorer report and reviewed the call graph, contracts, risks, and one-slice seam.
- [x] (2026-07-29) Wrote this self-contained one-slice ExecPlan before implementation.
- [x] Add typed matrix result DTOs and application-facing preview/signed result methods while preserving legacy dictionary-returning wrappers.
- [x] Add the signed-acceptance lifecycle and artifact ports, default Qt/filesystem adapters, and deterministic fakes for tests.
- [x] Normalize the signed scenario executor result and migrate the matrix runner to the lifecycle/artifact boundaries without changing summary JSON fields.
- [x] Add/replace boundary tests for service result mapping, lifecycle cleanup, scenario error rows, workspace parity, and CLI compatibility.
- [x] Run focused/full validation and both release-fidelity matrices; update this plan with evidence and surprises.
- [x] Run independent architecture/spec compliance review; address findings in this slice if possible.
- [x] Update README, `docs/ARCHITECTURE.md`, and this plan through the architecture-steward documentation pass.
- [x] (2026-07-29) Focused boundary validation passed: 139 tests; full suite passed: 995 tests with one pre-existing Pillow deprecation warning.
- [x] (2026-07-29) Release-fidelity preview matrix passed: 8 scenarios, 0 error rows.
- [x] (2026-07-29) Release-fidelity signed matrix passed: 8 scenarios, 6 successful signings, 2 matched intentional rejections, and all acceptance failure counters at zero.
- [x] (2026-07-29) Independent compliance review findings were resolved: typed scenario rows are wired, artifact paths are authoritative, and lifecycle cleanup covers setup, scenario, and summary failures.
- [x] (2026-07-29) Committed the complete slice as `21a872aa8` and verified a clean worktree, process list, and window list.

## Surprises & Discoveries

- Observation: `Phase3EvidenceService` already owns the CLI-facing verbs, so adding another presentation-level facade would duplicate a stable boundary.
  Evidence: `src/foliaseal/application/phase3_evidence_service.py` is called by `src/foliaseal/__main__.py` for harness, preview matrix, signed matrix, validation, and aggregate evidence commands.
- Observation: the preview matrix runner is already relatively clean and headless; the signed matrix runner is the broad integration seam.
  Evidence: `Phase3SignedAcceptanceMatrixRunner.run()` creates the Qt application/window, shell, workspace, event loop calls, scenario loop, close operation, summary counters, and `summary.json` directly.
- Observation: the per-scenario executor is the narrowest behavior seam where shell application, workspace capture, request rewriting, signing, and successful-output evidence meet.
  Evidence: `Phase3SignedAcceptanceScenarioExecutor.run()` applies a scenario, captures `Phase3HarnessWorkspaceSnapshot`, rewrites `SigningRequest`, executes signing, and snapshots the signed output.
- Observation: the first signed-matrix run exposed a Qt ordering defect after lifecycle extraction: a shell widget was constructed before `QApplication` existed.
  Resolution: `Phase3SignedAcceptanceLifecyclePort.start()` now creates the application/window before shell construction, with `attach_shell()` installing the already-created shell.
- Observation: the first independent compliance review found typed scenario results were declared but not fully wired, the returned artifact path was not persisted in the summary, and setup failures could skip cleanup.
  Resolution: the runner normalizes `Phase3SignedAcceptanceScenarioResult` rows, persists the authoritative `summary_json_path`, and wraps the complete startup-to-publication flow in `try/finally`; regression tests cover all three failure classes.
- Observation: the Qt offscreen release-fidelity run emits existing platform/content-box warnings but completes with the expected counters and no leaked FoliaSeal process or window.

## Decision Log

- Decision: Deepen the existing application evidence service instead of introducing a second common-caller facade.
  Rationale: the CLI already depends on `Phase3EvidenceService`; a second facade would increase indirection without removing the current signed-run coupling.
  Date/Author: 2026-07-29 / Codex.
- Decision: Introduce lifecycle and artifact ports only for the signed-acceptance runner in this slice.
  Rationale: Qt lifecycle and direct summary-file writes are the concrete side effects preventing deterministic orchestration tests. Rendering, signing, and workspace behavior already have narrower injected collaborators and should not be generalized into a large port framework yet.
  Date/Author: 2026-07-29 / Codex.
- Decision: Preserve existing raw summary dictionaries and CLI output through compatibility wrappers while adding typed result methods.
  Rationale: `summary.json`, acceptance-counter names, and CLI callers are external contracts; a typed internal result must normalize them without changing serialized fields.
  Date/Author: 2026-07-29 / Codex.
- Decision: Keep `Phase3HarnessWorkspacePort` as the shell scenario boundary and do not widen it with QApplication lifecycle methods.
  Rationale: the workspace port is already shared by Qt and headless adapters; lifecycle belongs one level above it so headless tests do not need fake GUI methods.
  Date/Author: 2026-07-29 / Codex.
- Decision: Treat generated PDFs, PNGs, and `/tmp` matrix directories as evidence only; do not commit them.
  Rationale: this is a behavior/refactor slice with documentation/status updates, not a fixture refresh.
  Date/Author: 2026-07-29 / Codex.
- Decision: Keep the artifact publication's second write after receiving the adapter path.
  Rationale: the first write establishes the stable file location; the returned path is then inserted into the summary and written again so persisted JSON and the typed CLI result share one authoritative `summary_json_path` value without changing the existing artifact-port contract.
  Date/Author: 2026-07-29 / Codex.

## Outcomes & Retrospective

The completed hybrid keeps the application evidence gateway as the common caller boundary while
adding typed `Phase3MatrixResult`/`Phase3MatrixKind` views over unchanged raw summaries. Signed
scenario rows are typed and serialized through `as_mapping()`. The signed runner now delegates
window/event-loop ownership to `Phase3SignedAcceptanceLifecyclePort` (Qt and fake adapters) and
matrix-directory/summary publication to `Phase3MatrixArtifactPort` (filesystem and memory adapters).
Lifecycle ordering is start, shell attachment, initial event processing, per-scenario event
processing, and unconditional close. The artifact adapter's returned path is authoritative for
`summary_json_path`. CLI command names, labels, exit behavior, and legacy raw-dict methods remain
compatible. README and architecture documentation were updated in this slice; generated evidence
remains outside Git. Validation completed with 139 focused tests and 995 full-suite tests passing.
The preview matrix executed 8 scenarios with 0 error rows. The signed matrix executed 8 scenarios
with 6 successful signings, 2 matched intentional fit rejections, `acceptance_expectations_passed=true`,
and zero expected-outcome, cryptographic-validation, preview-comparison, and annotation-rectangle
failures. The independent compliance review initially failed on typed-result wiring, artifact-path
authority, and setup cleanup; all findings are now covered by code and regression tests.

## Context and Orientation

`src/foliaseal/application/phase3_evidence_service.py` defines the application request objects used by the CLI: `Phase3HarnessCaptureRequest`, `Phase3MatrixRequest`, `Phase3HarnessValidationRequest`, and `Phase3SignedAcceptanceEvidenceRequest`. It forwards capture and matrix calls through injected callables, aggregates signed-acceptance evidence, and now offers typed `Phase3MatrixResult` methods alongside raw-dictionary compatibility methods.

`src/foliaseal/presentation/qt/phase3_harness.py` is the Qt composition root. `Phase3Harness` exposes interactive capture and preview/signed matrix ports, while private builders assemble runners and adapters. It remains a compatibility/composition module in this slice; do not rewrite the whole file.

`src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py` owns signed matrix orchestration and summary shaping. It loads the manifest, validates `timestamping_mode`, builds viewer/signing workflows and the shell, delegates window/event-loop work to `Phase3SignedAcceptanceLifecyclePort`, creates `Phase3HarnessWorkspacePort`, loops typed scenario results, computes counters, evaluates acceptance expectations, and publishes `summary.json` through `Phase3MatrixArtifactPort`.

`src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py` owns one scenario row. It applies `Phase3HarnessScenarioCommand`, captures a `Phase3HarnessWorkspaceSnapshot`, rewrites the request to the scenario output path and certificate/passphrase, invokes the signing executor, and adds successful signed-output evidence.

`src/foliaseal/presentation/qt/phase3_harness_workspace.py` defines the shared Qt/headless `Phase3HarnessWorkspacePort`, normalized scenario/capture commands, and `Phase3HarnessWorkspaceSnapshot`. Keep this port Qt-free and preserve equivalent Qt/headless snapshot fields.

`src/foliaseal/presentation/qt/phase3_preview_matrix_runner.py` is the headless preview runner and should keep its current behavior. `src/foliaseal/presentation/qt/phase3_harness_reporting.py` and `src/foliaseal/application/qa_evidence_contract.py` define the existing report/evidence contracts and should receive normalized payloads, not new schema names.

## Plan of Work

First, add typed application results in `src/foliaseal/application/phase3_evidence_service.py`. Define `Phase3MatrixKind` with `PREVIEW` and `SIGNED_ACCEPTANCE`, plus `Phase3MatrixResult` containing the kind, raw summary mapping, passed flag, artifact directory, summary JSON path, scenario count, successful-run count, errors, and warnings. Add `preview_matrix_result(request)` and `signed_acceptance_matrix_result(request)` methods that call the existing injected runners and normalize their current dictionaries. Keep `run_preview_matrix()` and `run_signed_acceptance_matrix()` as compatibility methods returning the raw dictionaries used by existing CLI code. Add tests proving typed normalization preserves every externally meaningful counter and path.

Next, add a narrow lifecycle port in `src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py` or a nearby module. The port must represent only the runner-owned lifecycle: open a shell session from already-built workflow/shell dependencies, process pending UI events, and close the session. Define a production Qt adapter that wraps the current `QApplication`, `QMainWindow`, shell installation, `show()`, `processEvents()`, and `close()` sequence. Define an in-memory fake for tests. The runner must obtain this port from its dependency bundle and use `try/finally` so close is attempted after scenario errors and summary-writing failures.

Add a narrow artifact port for the runner’s directory creation and summary JSON write. Its production implementation uses `Path.mkdir()` and `Path.write_text()` with the current JSON serialization; the fake records writes in memory. The port must return the summary path so typed results and CLI output can use one source of truth. Do not move all report rendering or every artifact emitted by signed-output snapshotters in this slice; only the matrix run directory and `summary.json` write belong here.

Then normalize the scenario executor in `src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py`. Add a frozen `Phase3SignedAcceptanceScenarioResult` whose fields represent the existing result row and whose `as_mapping()` method emits the current JSON keys. Make `run()` return this type internally, or add a typed `run_result()` while keeping the current mapping adapter for callers that still expect dictionaries. Preserve the existing apply, capture, request rewrite, signing, success-output snapshot, and intentional-fit-rejection behavior. The matrix runner should convert each typed result through `as_mapping()` before calculating existing counters.

Migrate the signed matrix runner to use the lifecycle and artifact ports. Keep source-path validation, manifest parsing, timestamping-mode validation, workflow construction, workspace construction, scenario iteration, exception-to-error-row mapping, counters, acceptance expectation evaluation, and summary keys unchanged. The runner must process events through the lifecycle port after initial refresh and after each scenario, close the session in `finally`, and write the summary through the artifact port. The preview runner and interactive capture path should continue to use their existing behavior; only add typed service methods where they consume matrix results.

Update `src/foliaseal/__main__.py` only as needed to consume typed results in new internal helpers without changing command names, printed labels, exit behavior, or summary paths. Existing raw-returning service methods remain available for compatibility until a later cleanup slice.

Replace white-box tests only where the new boundary makes them redundant. Keep the existing workspace adapter tests for Qt/headless parity and keep one composition test for default wiring. Add lifecycle fake tests proving close occurs on scenario exceptions and summary-write failures. Add artifact fake tests proving the exact `summary.json` payload and path are emitted. Add scenario-result tests proving `as_mapping()` preserves existing keys, successful signed-output evidence, and intentional rejection rows. Extend `tests/unit/test_phase3_evidence_service.py` for typed result normalization and failure mapping. Update `tests/unit/test_phase3_signed_acceptance_matrix_runner.py` and `tests/unit/test_phase3_signed_acceptance_scenario_executor.py` to assert public boundary outcomes instead of private orchestration details. Keep CLI tests for command dispatch and output labels.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

Before implementation, confirm the baseline is clean:

    git status --short
    .venv/bin/pytest -q tests/unit/test_phase3_evidence_service.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_signed_acceptance_scenario_executor.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_main_cli.py

Implement the typed service result, lifecycle/artifact ports, scenario result normalization, runner migration, and focused tests. Then run:

    .venv/bin/ruff check src/foliaseal/application/phase3_evidence_service.py src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py src/foliaseal/presentation/qt/phase3_harness_workspace.py tests/unit/test_phase3_evidence_service.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_signed_acceptance_scenario_executor.py
    .venv/bin/pytest -q tests/unit/test_phase3_evidence_service.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_signed_acceptance_scenario_executor.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_harness.py tests/unit/test_main_cli.py

Expected focused validation is green. The exact count may increase with new boundary tests; report the observed count in `Progress` and `Outcomes & Retrospective`.

Run the full suite:

    .venv/bin/pytest -q

Run the release-fidelity commands with generated output kept outside Git:

    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-preview-matrix --pdf-path artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf --certificate-path artifacts/generated_acceptance_assets/signed_acceptance_identity.p12 --passphrase secret --scenario-manifest-path tests/fixtures/phase3/release_fidelity_manifest.json --artifacts-dir /tmp/foliaseal-evidence-hybrid-preview
    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-acceptance-matrix --pdf-path artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf --certificate-path artifacts/generated_acceptance_assets/signed_acceptance_identity.p12 --passphrase secret --scenario-manifest-path tests/fixtures/phase3/release_fidelity_manifest.json --artifacts-dir /tmp/foliaseal-evidence-hybrid-signed

The preview summary must report eight scenarios without error rows. The signed summary must report eight scenarios, six successful signings, two intentional fit rejections, `acceptance_expectations_passed=true`, and zero expected-outcome, cryptographic, preview-output, and annotation-rectangle failures.

Finish with:

    git diff --check
    git status --short
    ps -eo pid=,comm=,args= | awk '$2 ~ /python/ && $0 ~ /foliaseal|phase3/ {print}'
    wmctrl -l 2>/dev/null || true

The worktree must be clean and no FoliaSeal or Qt process/window may remain.

## Validation and Acceptance

The application boundary is accepted when typed preview and signed result methods preserve the existing summary schema, artifact paths, counters, and error semantics. The signed runner is accepted when a fake lifecycle port proves cleanup runs for both scenario exceptions and summary-write failures, while the production Qt adapter still opens, processes, and closes the shell exactly once per matrix run.

The scenario boundary is accepted when a fake workspace and signing executor can execute a scenario without Qt, produce the same `Phase3HarnessWorkspaceSnapshot`-derived result keys, rewrite output paths safely, preserve intentional fit rejections, and include successful signed-output evidence when the output exists.

Repository acceptance requires focused tests, the full suite, both release-fidelity matrices, `git diff --check`, updated architecture documentation, a clean worktree, and no leftover processes/windows. Existing CLI command names and printed summary labels must remain compatible.

## Idempotence and Recovery

The changes are additive and safe to rerun. Use only the named `/tmp/foliaseal-evidence-hybrid-*` directories for generated matrix evidence. If a test fails after lifecycle extraction, first inspect whether the fake or production lifecycle port missed a `finally` close; do not weaken cleanup assertions. If summary JSON differs, compare the normalized `Phase3SignedAcceptanceScenarioResult.as_mapping()` output with the previous row keys before changing serializers. Do not use destructive Git commands. If a GUI command is interrupted, close the window/process and rerun the process/window checks before continuing.

## Artifacts and Notes

Tracked changes for this slice are the ExecPlan, application result types, lifecycle/artifact adapters, signed scenario normalization, focused tests, and documentation. Generated matrix output must remain outside Git at:

    /tmp/foliaseal-evidence-hybrid-preview/summary.json
    /tmp/foliaseal-evidence-hybrid-signed/summary.json

Record the final test counts, matrix counter summaries, compliance findings, documentation changes, and commit hash in this plan before completion.

## Interfaces and Dependencies

In `src/foliaseal/application/phase3_evidence_service.py`, define stable typed result objects equivalent to:

    class Phase3MatrixKind(StrEnum):
        PREVIEW = "preview"
        SIGNED_ACCEPTANCE = "signed_acceptance"

    @dataclass(frozen=True)
    class Phase3MatrixResult:
        kind: Phase3MatrixKind
        summary: Mapping[str, Any]
        passed: bool
        artifacts_dir: str
        summary_json_path: str
        scenario_count: int | None
        successful_run_count: int | None
        errors: tuple[str, ...]
        warnings: tuple[str, ...]

    class Phase3EvidenceService:
        def preview_matrix_result(self, request: Phase3MatrixRequest) -> Phase3MatrixResult: ...
        def signed_acceptance_matrix_result(self, request: Phase3MatrixRequest) -> Phase3MatrixResult: ...

The existing `run_preview_matrix()` and `run_signed_acceptance_matrix()` raw-dictionary methods remain compatibility shims and must delegate to the same runner calls.

In `src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py` or a focused neighboring module, define a lifecycle port equivalent to:

    class Phase3SignedAcceptanceLifecyclePort(Protocol):
        def start(self, *, title: str) -> None: ...
        def attach_shell(self, shell: Any) -> None: ...
        def process_events(self) -> None: ...
        def close(self) -> None: ...

The production adapter owns the current QApplication/QMainWindow setup, `setCentralWidget`, `show`, `processEvents`, and `close`. The fake records calls and performs no GUI work. The runner must use it in a `try/finally` block.

Define an artifact port equivalent to:

    class Phase3MatrixArtifactPort(Protocol):
        def prepare(self, artifacts_dir: str) -> Path: ...
        def write_summary(self, artifacts_dir: Path, summary: Mapping[str, Any]) -> str: ...

The production adapter preserves the existing `summary.json` serialization; the fake records the mapping and returns a deterministic path.

In `src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py`, define a typed `Phase3SignedAcceptanceScenarioResult` with `as_mapping()` preserving all current row keys. Do not add PySide6, pyHanko, or filesystem imports to the application service result module.

## Revision Note

2026-07-29 / Codex: Created this one-slice plan after fresh explorer reconnaissance. The plan deliberately narrows the C+D recommendation to typed common-caller results plus lifecycle/artifact isolation at the signed-acceptance seam, preserving current CLI, JSON, workspace, and matrix contracts while avoiding an oversized generic port framework.

2026-07-29 / Codex: Implementation and documentation completed. The typed gateway, signed
scenario result, lifecycle/artifact adapters, runner ordering, and compatibility contracts now
match the code; README and `docs/ARCHITECTURE.md` record the resulting boundaries.

2026-07-29 / Codex: Validation completed with 139 focused tests, 995 full-suite tests, and both
release-fidelity matrices green. The independent compliance review's final setup-cleanup finding
was resolved by widening the runner `try/finally` to cover startup through artifact publication;
commit `21a872aa8` contains the complete intentional slice and the final process/window audit is
clean.
