# Split Phase 3 evidence composition into headless matrices and opt-in interactive capture

This ExecPlan is a living document and must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`. It describes one complete implementation slice: deepen the Phase 3 harness composition root so ordinary preview, signed-acceptance, validation, and evidence callers do not construct the interactive Qt graph, while keeping interactive capture explicit, preserving every CLI/JSON/artifact contract, and removing obsolete compatibility gateways and duplicate wrappers.

## Purpose / Big Picture

FoliaSeal's Phase 3 commands let maintainers run preview matrices, signed-acceptance matrices, interactive harness captures, and evidence validation. Today the default evidence builder constructs `Phase3Harness`, whose default dependency bundle eagerly constructs all three operation graphs. This makes a headless command depend on the presentation/Qt composition root even when it never opens a window, and it forces maintainers and tests to understand a 4,321-line module before changing one matrix operation.

After this slice, the ordinary preview and signed-matrix paths use a typed headless-first composition. Interactive Qt capture is installed only through an explicit interactive composition. A user can run the existing commands unchanged and observe the same summary paths, JSON keys, scenario counts, intentional rejection rows, signed PDFs, and checklist output. Tests can exercise matrix and capture boundaries with fake renderers, lifecycles, artifact sinks, and profile stores without importing or starting Qt. The old thin matrix gateway classes and duplicate private forwarding helpers are removed rather than preserved as new compatibility layers.

## Child ExecPlan Dependencies

- [x] The previous visible-signature prepare-once slice is present at commit `1c45d2db0`; this plan depends on its clean `main` baseline and does not alter its layout contract.
- [x] A fresh explorer-light pre-plan review inspected the current harness callers, eager construction, stable output contracts, CLI dispatch, and validation targets.
- [x] No child ExecPlans are required. This is one bounded composition-root slice whose implementation, test migration, documentation, compliance review, and commit must land together.

## Progress

- [x] (2026-08-01) Reviewed the recommended C/B hybrid designs and selected headless-first matrix composition with explicit interactive capture.
- [x] (2026-08-01) Completed the required fresh explorer review of `phase3_harness.py`, the evidence service/orchestrator, matrix runners, CLI, tests, and architecture requirements.
- [x] (2026-08-01) Wrote this self-contained one-slice ExecPlan before implementation.
- [x] (2026-08-01) Introduced `Phase3Composition.default_headless()` with lazy preview/signed operations and explicit lazy interactive capture; preserved the three public verbs and request/result contracts.
- [x] (2026-08-01) Migrated default evidence wiring and injected the signed runner's profile-store factory; focused harness/matrix/evidence tests pass.
- [x] (2026-08-01) Removed redundant matrix gateway classes and unused `_run_phase3_harness_session`/`_build_phase3_harness_capture_payload` wrappers; migrated tests to typed composition fakes.
- [x] (2026-08-01) Ran focused and complete validation: `1037 passed` with one pre-existing Pillow deprecation warning; Ruff and `git diff --check` passed.
- [x] (2026-08-01) Ran release-fidelity CLI matrices: preview `8/8` successful with `0` errors; signed `8` scenarios with `6` successful signings, `2` matched intentional rejections, and acceptance expectations passed; temporary artifacts were removed and no FoliaSeal/Phase 3 process remained.
- [x] (2026-08-01) Completed initial/high-risk compliance review, added explicit interactive-composition and success/failure window-cleanup coverage, and reconciled README, architecture, and this ExecPlan; commit remains the parent agent's handoff responsibility.

## Surprises & Discoveries

- Observation: `Phase3HarnessDependencies.default()` constructs interactive, preview, and signed runner adapters together.
  Evidence: `src/foliaseal/presentation/qt/phase3_harness.py` builds `_build_phase3_interactive_harness_runner()`, `_build_phase3_preview_matrix_port()`, and `_build_phase3_signed_acceptance_matrix_port()` in one default factory.
- Observation: The preview matrix is headless, while signed acceptance requires Qt bindings, a render backend, a shell/workspace lifecycle, and event processing.
  Evidence: `phase3_preview_matrix_runner.py` has no Qt lifecycle; `phase3_signed_acceptance_matrix_runner.py` loads Qt bindings, starts a lifecycle, builds a shell, and processes events.
- Observation: `build_default_phase3_evidence_service()` constructs `Phase3Harness()` before the application orchestrator chooses an operation.
  Evidence: `phase3_signed_acceptance_evidence.py` binds all three harness methods into `Phase3EvidenceService`, so validation/read-only callers inherit the presentation composition.
- Observation: The signed runner currently writes the summary artifact in two stages so the final payload can contain its authoritative `summary_json_path`.
  Evidence: `Phase3SignedAcceptanceMatrixRunner.run()` obtains the artifact path before final serialization; preserve this observable contract or centralize it without changing the final JSON.
- Observation: Historical `run_phase3_*` aliases are already absent from live source; remaining cleanup is limited to redundant gateway dataclasses and private wrappers whose only callers are tests or local builders.
  Evidence: repository search at the pre-plan baseline found those names only in historical plan prose, while gateway/helper symbols remain in `phase3_harness.py` and its tests.
- Observation (implementation): The lazy matrix adapter must translate the public `Phase3MatrixRequest` into the existing runner keyword contract; direct fake composition operations can still accept the typed request.
  Evidence: Existing matrix runners expose keyword-only `run()` methods, while `Phase3EvidenceService` passes typed request objects to the harness boundary.
- Observation (implementation): `Phase3HarnessSessionResult` was only incidentally re-exported through the large harness module; deleting unused wrappers exposed a test import that needed to target `phase3_harness_session_runner.py` directly.
  Evidence: The focused harness suite remained green after migrating that test import, confirming the re-export was compatibility cruft rather than behavior.
- Observation (compliance): The high-risk review found that interactive capture closed its event loop but did not close the top-level window when final capture/report assembly failed.
  Resolution: `Phase3HarnessSessionRunner.run()` now closes the window in a `finally` block, with parameterized success/failure tests proving cleanup; signed-matrix lifecycle cleanup was already covered by its existing lifecycle port tests.

## Decision Log

- Decision: Keep three explicit public operations—`capture`, `preview_matrix`, and `signed_acceptance_matrix`—instead of introducing a tagged union `run()` gateway.
  Rationale: These verbs already match `Phase3EvidenceService`, the CLI orchestrator, and stable result types. A union result would overlap the application orchestrator and make unsupported operations easier to hide.
  Date/Author: 2026-08-01 / Codex.
- Decision: Make headless matrix composition the default and interactive Qt capture opt-in/lazy.
  Rationale: Preview and validation do not need Qt; signed acceptance needs Qt but only when that operation runs. Separating construction reduces import/runtime coupling and makes test doubles local.
  Date/Author: 2026-08-01 / Codex.
- Decision: Use operation-specific typed ports and private runner-local dependency bundles, not a generic `OperationPort[Any, Any]` registry or a giant public service locator.
  Rationale: Typed operation contracts keep the three supported flows discoverable and preserve compile-time/test-time exhaustiveness while still allowing renderer, signer, lifecycle, artifact, and report adapters to be replaced.
  Date/Author: 2026-08-01 / Codex.
- Decision: Remove redundant `Phase3PreviewMatrixPort`/`Phase3SignedAcceptanceMatrixPort` gateways and duplicate private forwarding helpers after caller/test migration; preserve stable DTOs, CLI labels, summary schemas, and artifact paths.
  Rationale: The user explicitly requires legacy compatibility pieces and cruft to be stripped. These wrappers add indirection without owning behavior, while the serialized contracts are genuine compatibility surfaces.
  Date/Author: 2026-08-01 / Codex.
- Decision: Inject `profile_store_factory`, signed lifecycle/artifact factories, and other concrete factories through runner dependency bundles where tests currently rely on direct defaults.
  Rationale: This is required for local-substitutable boundary tests and prevents the composition refactor from merely moving hidden global construction into a new facade.
  Date/Author: 2026-08-01 / Codex.

## Outcomes & Retrospective

Final outcome: `Phase3Composition.default_headless()` lazily owns preview and signed-matrix operations, while `with_interactive_qt()` installs the interactive capture operation lazily. `Phase3Harness` preserves the stable `capture()`, `preview_matrix()`, and `signed_acceptance_matrix()` adapter verbs and the existing application request/result DTOs. Operation-local dependency bundles now carry profile-store, lifecycle, render-backend, artifact, and signing factories so tests can substitute collaborators at the boundary. The redundant `Phase3PreviewMatrixPort`/`Phase3SignedAcceptanceMatrixPort` gateways and duplicate `_run_phase3_harness_session`/`_build_phase3_harness_capture_payload` forwarding wrappers were removed; no CLI labels, JSON keys, summary paths, artifact contracts, or intentional rejection semantics were changed.

Validation recorded during implementation: focused and complete validation reported `1037 passed` with one pre-existing Pillow deprecation warning; Ruff and `git diff --check` passed. Release-fidelity evidence reported 8/8 preview scenarios successful with 0 errors, and 8 signed scenarios with 6 successful signings plus 2 matched intentional rejections; acceptance expectations passed. Temporary artifacts were removed and no FoliaSeal/Phase 3 process remained. Documentation reconciliation updated `README.md` and `docs/ARCHITECTURE.md` to describe the headless-first/lazy-interactive split, operation-local dependencies, stable contracts, and removed compatibility cruft. Initial compliance review found stale architecture references and a missing explicit-interactive test; both were corrected. High-risk review found the interactive window cleanup gap; the session runner now closes the window in `finally`, with success and final-capture-failure tests. Commit hash is intentionally left to the parent agent's focused commit.

## Context and Orientation

The application layer in `src/foliaseal/application/phase3_evidence_service.py`, `phase3_evidence_orchestrator.py`, `phase3_evidence_core.py`, and `phase3_evidence_ports.py` owns typed evidence requests, operation dispatch, result normalization, and stable counters. The presentation layer in `src/foliaseal/presentation/qt/phase3_harness.py` currently acts as the composition root: it wires interactive capture, preview matrix execution, and signed acceptance matrix execution. `phase3_signed_acceptance_evidence.py` supplies default collaborators to the application service. `__main__.py` dispatches CLI commands only through the application orchestrator and must remain unchanged at its user-facing surface.

`Phase3HarnessCapture` is the structured interactive capture DTO and its sorted/indented `to_json()` output is consumed by acceptance tooling. Preview and signed matrix runners return mappings that the application evidence core normalizes into typed matrix results; their `summary.json` artifacts contain scenario counts, diagnostics, results, paths, and signed-acceptance expectation fields. A local-substitutable dependency is a collaborator that can be replaced with a fake, in-memory object, or temporary-directory implementation in tests. Qt bindings, pyHanko signing, Pillow rendering, and host `pdftoppm` remain concrete adapters at the edge rather than becoming application-level dependencies.

## Plan of Work

First introduce a composition module or a narrowly scoped section in `phase3_harness.py` that exposes an explicit headless-first `Phase3Composition` (name may be finalized during implementation) with the existing three operation verbs. Its default constructor must build only the preview and signed matrix operation ports needed by the caller; it must not construct or import the interactive runner graph until an explicit `with_interactive_qt()`/interactive factory is used. Keep the public request/result types unchanged. The composition may retain a private compatibility adapter for `Phase3Harness` during migration, but no new public generic gateway is allowed.

Then migrate `build_default_phase3_evidence_service()` so the application evidence service receives the headless matrix operations and an explicit interactive capture operation without eagerly building the Qt capture runner. Preserve the existing `Phase3EvidenceService` and `Phase3EvidenceOrchestrator` contracts. Ensure the signed matrix still creates its Qt lifecycle, shell, workspace, event processing, dummy/real timestamp mode, artifact root, and final summary path exactly as before, but make `profile_store_factory`, lifecycle factory, artifact port factory, render backend factory, Qt binding loader, and signing executor factory injectable through the signed runner's local dependency bundle.

Retire `Phase3PreviewMatrixPort` and `Phase3SignedAcceptanceMatrixPort` if their behavior is only request-to-runner forwarding. Replace test construction of those gateways with direct fakes implementing the typed operation contract. Remove local wrappers such as `_run_phase3_harness_session`, `_build_phase3_harness_capture_payload`, and duplicate capture/sign-result forwarding helpers when `rg` proves they have no production/test behavior beyond delegation. Do not remove `Phase3HarnessWorkspacePort`, `Phase3HarnessCapture`, `Phase3HarnessCaptureRequest`, `Phase3MatrixRequest`, `Phase3MatrixResult`, or stable report/artifact serializers; these own actual contracts.

Keep interactive capture separate from matrix execution. Its private runner may continue to own QApplication/Qt binding loading, page-count/render backend diagnostics, signing workflow construction, session lifecycle, capture assembly, evidence contract evaluation, checklist rendering, summary writing, and stdout messaging. The composition root should only assemble those collaborators and expose the operation; it must not leak their callback list to callers.

Update tests at the new boundary. Add tests proving default headless composition does not instantiate the interactive runner, explicit interactive composition does, operation requests are forwarded unchanged, fake profile/lifecycle/artifact/render/signing collaborators are used, lifecycle cleanup occurs on success and failure, summary JSON keys/paths and expected rejection rows remain stable, and the application orchestrator/CLI still dispatches the same operation. Delete tests that only assert removed gateway/helper names or implementation wiring.

Finally reconcile `README.md`, `docs/ARCHITECTURE.md` through the architecture-steward skill, and this ExecPlan. Document headless-first composition, explicit interactive capture, operation-local dependency ownership, preserved evidence contracts, and removed compatibility cruft. Run all validations, inspect matrix summaries, delete only temporary artifacts created by this slice, verify no FoliaSeal/Phase 3 processes remain, and commit all source/tests/docs/plan changes as one focused commit.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

1. Confirm `main` is clean at `1c45d2db0` or later and inventory the live composition symbols:

       git status --short --branch
       rg -n "Phase3HarnessDependencies|Phase3PreviewMatrixPort|Phase3SignedAcceptanceMatrixPort|build_default_phase3_evidence_service|_run_phase3_harness_session|_build_phase3_harness_capture_payload|_build_phase3_harness_capture" src tests docs/ARCHITECTURE.md

2. Implement the headless-first composition and lazy interactive capture. Run the focused harness/evidence tests after each caller migration:

       .venv/bin/python -m pytest -q tests/unit/test_phase3_harness.py tests/unit/test_phase3_evidence_service.py tests/unit/test_phase3_evidence_orchestrator.py

   The new tests must prove that constructing the default headless composition does not call Qt binding, shell, or interactive lifecycle factories.

3. Inject signed-runner factories and migrate tests away from redundant gateways. Validate matrix and lifecycle contracts:

       .venv/bin/python -m pytest -q tests/unit/test_phase3_preview_matrix_runner.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_signed_acceptance_scenario_executor.py tests/unit/test_phase3_matrix_artifacts.py

4. Run the broader affected test set:

       .venv/bin/python -m pytest -q tests/unit/test_phase3_harness.py tests/unit/test_phase3_evidence_service.py tests/unit/test_phase3_evidence_orchestrator.py tests/unit/test_main_cli.py tests/unit/test_phase3_preview_matrix_runner.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_signed_acceptance_scenario_executor.py tests/unit/test_phase3_harness_capture_assembler.py tests/unit/test_phase3_harness_reporting.py
       .venv/bin/ruff check src tests
       git diff --check

5. Run the complete suite and observable matrix commands using the tracked release-fidelity fixture:

       .venv/bin/python -m pytest -q
       QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-preview-matrix --pdf-path artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf --certificate-path artifacts/generated_acceptance_assets/signed_acceptance_identity.p12 --passphrase secret --scenario-manifest-path tests/fixtures/phase3/release_fidelity_manifest.json --artifacts-dir /tmp/foliaseal-phase3-composition-preview
       QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-acceptance-matrix --pdf-path artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf --certificate-path artifacts/generated_acceptance_assets/signed_acceptance_identity.p12 --passphrase secret --scenario-manifest-path tests/fixtures/phase3/release_fidelity_manifest.json --artifacts-dir /tmp/foliaseal-phase3-composition-signed

   Expect 8 preview scenarios with zero errors, and 8 signed scenarios with 6 successful signings and 2 matched intentional rejections. Inspect both `summary.json` files for stable keys, paths, counters, and no unexpected errors.

6. Run structural cleanup and process checks:

       rg -n "Phase3PreviewMatrixPort|Phase3SignedAcceptanceMatrixPort|_run_phase3_harness_session|_build_phase3_harness_capture_payload|_build_phase3_harness_capture|run_phase3_" src tests
       rm -rf /tmp/foliaseal-phase3-composition-preview /tmp/foliaseal-phase3-composition-signed
       ps -eo pid,args | awk '/python.*foliaseal|python.*phase3/ && !/awk/ {print}'

   The structural search must show no removed gateway/helper symbols in live source or tests, and the process check must print nothing. If a display is unavailable, rely on the offscreen commands and record that limitation rather than leaving a process running.

7. After the first implementation pass, spawn the required explorer-light compliance review, plus a second high-risk explorer review because this slice crosses Qt lifecycle, signing, filesystem artifacts, and stable evidence contracts. Address findings in the same living plan; if a finding requires additional implementation, record the child work and repeat focused/full validation before continuing.

8. Spawn a worker-light documentation reviewer using architecture-steward to update README, `docs/ARCHITECTURE.md`, and this ExecPlan. Then spawn a worker-light using write-git-commit to stage only intentional source/tests/docs/plan changes and create one focused commit. Verify the final worktree is clean.

## Validation and Acceptance

The slice is accepted only when the default evidence/preview path can be constructed and exercised without constructing the interactive Qt capture graph, while the explicit interactive capture operation still starts and cleans up its Qt lifecycle correctly. Existing CLI commands must print the same headings and summary paths. Preview summaries must retain their scenario counts, diagnostics, result rows, and artifact directory; signed summaries must retain timestamping mode, acceptance expectations, counters, result rows, and authoritative summary path; interactive captures must retain `Phase3HarnessCapture.to_json()` fields and checklist/report artifacts.

Focused harness/evidence/matrix tests, the complete pytest suite, Ruff, and diff checks must pass. The release-fidelity preview matrix must execute 8 scenarios with zero errors. The signed matrix must execute 8 scenarios with 6 successful signings, 2 matched intentional rejections, and zero unexpected outcome, cryptographic, annotation, or comparison failures. Structural searches must show that removed gateway/helper symbols are absent. The final process check must show no FoliaSeal or Phase 3 Python process, and temporary directories created by this plan must be gone.

## Idempotence and Recovery

The migration is safe to repeat because the public application request/result contracts remain unchanged and each operation can be moved behind the new composition one at a time. If a matrix test fails, restore behavior inside the operation-specific runner or adapter; do not restore a generic gateway or eagerly constructed interactive dependency. If a summary path or JSON key changes, compare the old and new `summary.json` payloads and correct the artifact/report adapter before proceeding. Remove only the two explicitly named temporary directories. Never delete tracked PDFs, certificates, fixtures, catalogs, or broad workspace paths.

## Artifacts and Notes

Record concise evidence here during implementation:

       headless construction guard: interactive Qt factory not called
       focused harness/evidence/matrix tests: 141 passed, 1 warning (pre-fix); post-fix session/harness tests: 91 passed, 1 warning
       full suite: 1037 passed, 1 pre-existing Pillow deprecation warning
       preview matrix: 8 scenarios, 0 errors
       signed matrix: 8 scenarios, 6 successful signings, 2 intentional rejections, 0 critical failures
       compatibility guard: removed gateway/helper symbols absent from src/tests
       process cleanup: no matching FoliaSeal/Phase 3 process
       commit: <hash>

Do not paste full JSON summaries or large diffs into this plan.

## Interfaces and Dependencies

At the presentation composition boundary, define typed operation contracts without a generic untyped operation registry:

    class Phase3CaptureOperation(Protocol):
        def run(self, request: Phase3HarnessCaptureRequest) -> Phase3HarnessCapture: ...

    class Phase3MatrixOperation(Protocol):
        def run(self, request: Phase3MatrixRequest) -> Mapping[str, Any]: ...

    @dataclass(frozen=True)
    class Phase3Composition:
        preview_matrix: Phase3MatrixOperation
        signed_acceptance_matrix: Phase3MatrixOperation
        interactive_capture: Phase3CaptureOperation | None = None

        @classmethod
        def default_headless(cls) -> "Phase3Composition": ...

        def with_interactive_qt(self) -> "Phase3InteractiveComposition": ...

        def preview_matrix(self, request: Phase3MatrixRequest) -> Mapping[str, Any]: ...

        def signed_acceptance_matrix(self, request: Phase3MatrixRequest) -> Mapping[str, Any]: ...

    @dataclass(frozen=True)
    class Phase3InteractiveComposition:
        capture: Phase3CaptureOperation

        def capture_interactive(self, request: Phase3HarnessCaptureRequest) -> Phase3HarnessCapture: ...

The exact class names may be adjusted to avoid a field/method name collision, but the final API must preserve the existing `Phase3Harness` three-verb behavior and make interactive capture explicit. `Phase3EvidenceService` and `Phase3EvidenceOrchestrator` remain the application-facing dispatch boundaries. `Phase3PreviewMatrixRunnerDeps`, `Phase3SignedAcceptanceMatrixRunnerDeps`, `Phase3HarnessSessionRunnerDeps`, and workspace dependency bundles remain private operation-local injection structures. Add factories for profile stores, render backends, Qt bindings, signing executors, lifecycles, and artifact ports where direct defaults prevent local tests.

The dependency category is local-substitutable: tests provide fake operation runners, fake Qt bindings, fake lifecycle/shell/workspace ports, fake render backends with diagnostics, fake signing executors, in-memory or temporary artifact ports, and deterministic report writers. Real Qt/PySide6, pyHanko, Pillow, filesystem artifacts, and host rendering tools stay in production adapters. Stable JSON/CLI fields are compatibility contracts; internal gateway classes, duplicate forwarding helpers, and private aliases are not.

## Change-Slice Boundary

This is one primary architecture/refactor change with directly affected boundary tests and documentation/status updates. Allowed changes are the Phase 3 composition root, operation-local factory injection, default evidence wiring, affected harness/matrix/evidence tests, README/architecture/ExecPlan updates, and temporary matrix artifacts. Forbidden changes include redesigning the application evidence DTOs, changing CLI commands or printed labels, altering signed PDF semantics, changing scenario manifests, redesigning the signing workspace, adding a generic plugin/operation registry, or mixing unrelated GUI styling and certificate work.

Plan revision note: created 2026-08-01 after the required fresh explorer review. The hybrid was selected because it keeps the existing three operation verbs and stable evidence contracts while preventing headless callers from constructing the interactive Qt graph. The user's compatibility-cleanup requirement is part of the slice: remove redundant gateways and duplicate wrappers after migration rather than carrying them forward.
