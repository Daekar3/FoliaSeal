# Extract the Phase 3 interactive capture composition boundary

This ExecPlan is a living document and must be maintained in accordance with `docs/PLANS.md` guidance from `.agents/skills/write-execplan/PLANS.md`. It defines one complete implementation slice: extract the interactive capture contract and composition policy from the remaining Phase 3 harness monolith, remove compatibility-only forwarding seams, preserve all evidence behavior, and finish with compliance review, documentation, and commit.

## Purpose / Big Picture

FoliaSeal's Phase 3 evidence service already keeps preview and signed matrix operations lazy and headless-first. Before this slice, `src/foliaseal/presentation/qt/phase3_harness.py` also contained the interactive capture data model, runner, artifact-path policy, and composition wiring alongside thousands of lines of preview, signing, PDF, and rendering helpers. That made a small interactive-capture change require understanding unrelated matrix and evidence code and left tests coupled to private helpers; the extraction below records the completed correction.

After this slice, a dedicated `phase3_interactive_capture.py` module will own the interactive capture result contract, runner behavior, JSON normalization, and narrow artifact policy. `phase3_harness.py` will retain only the concrete Qt/matrix/render helpers it still owns and will no longer publish the interactive runner or capture model as compatibility exports. Default evidence wiring will lazily obtain the new interactive operation only when capture is requested. Existing CLI commands, `Phase3EvidenceService` request/result types, capture JSON fields, checklist/report output, artifact paths, lifecycle cleanup, matrix summaries, and intentional rejection semantics will remain unchanged.

The user-visible proof is the unchanged interactive capture command and unchanged preview/signed matrix commands. The architectural proof is that the interactive capture boundary can be tested through one focused module and that importing or constructing headless matrix operations still does not load Qt, Pillow, or pyHanko.

## Child ExecPlan Dependencies

- [x] The Phase 3 matrix-operation hybrid is complete at commits `0fa69ec5f` and `b0358ff2c`; `Phase3EvidenceService`, `Phase3MatrixOperations`, and lazy default wiring are stable inputs to this slice.
- [x] The required fresh explorer-light review inspected the clean checkout at `b0358ff2c`, identified the interactive capture cluster as the narrow safe seam, and confirmed that signed matrix lifecycle and broad render extraction are out of scope.
- [x] No child ExecPlan is required initially. Create a child only if compliance or high-risk review identifies a concrete additional implementation defect.

## Progress

- [x] (2026-08-01) Selected the recommended hybrid: retain the application service as the sole stable caller boundary, add a private interactive composition module, and use a narrow artifact policy instead of a generic registry.
- [x] (2026-08-01) Completed the required fresh explorer review; confirmed stable contracts, extraction targets, compatibility-cruft candidates, and validation risks.
- [x] (2026-08-01) Wrote this self-contained one-slice ExecPlan before implementation.
- [x] (2026-08-01) Extracted `Phase3HarnessCapture`, its JSON normalization, `Phase3InteractiveHarnessRunner`, and the narrow artifact policy into `src/foliaseal/presentation/qt/phase3_interactive_capture.py`.
- [x] (2026-08-01) Moved the explicit lazy capture factory to the new module and updated default evidence wiring, Qt package exports, and direct imports.
- [x] (2026-08-01) Migrated tests from `phase3_harness.py` compatibility imports to the new boundary; removed the old public interactive export and artifact helper definitions.
- [x] (2026-08-01) Focused interactive tests pass (`90 passed`, one pre-existing Pillow warning); affected Phase 3 tests pass (`138 passed`, one pre-existing Pillow warning); import isolation, Ruff, and diff checks pass.
- [x] (2026-08-01) Full suite passes (`1040 passed`, one pre-existing Pillow warning); preview matrix reports 8/8 successful with zero errors; signed matrix reports 8 scenarios, 6 successful signings, 2 matched intentional rejections, zero unexpected errors, and passing acceptance expectations. Temporary artifacts and processes were cleaned up.
- [x] (2026-08-01) First compliance review found stale architecture ownership text; high-risk review found an off-by-one interactive signing-attempt artifact index. Child plan `phase3_interactive_capture_highrisk_followup_execplan.md` was created and implemented.
- [x] (2026-08-01) Completed repeated compliance/high-risk reviews after the child follow-up; no further implementation defects were found.
- [x] (2026-08-01) Reconciled README, `docs/ARCHITECTURE.md`, and active ExecPlans through architecture-steward; corrected interactive ownership references and marked superseded composition prose historical.
- [x] (2026-08-01) Recorded and validated the artifact-index fix: the first interactive signing attempt uses one-based index `1` (not `2`).
- [x] (2026-08-01) Created focused main-branch commit `60fa8318b` with write-git-commit; the checkout was clean after commit.

## Surprises & Discoveries

- Observation: `phase3_matrix_operations.py` and signed-evidence default wiring are already correctly lazy and should not be reopened.
  Evidence: subprocess import checks show no `PySide6`, `PIL`, or `pyhanko` modules for matrix operations, signed-evidence wiring, or CLI import.
- Observation: The remaining safe seam is the top interactive cluster in `phase3_harness.py`, not the preview/render payload helpers.
  Evidence: the interactive runner spans Qt loading, workflow construction, session execution, capture assembly, reporting, and artifact policy; preview render capture still mixes widget anatomy, geometry, image analysis, and filesystem output.
- Observation (pre-extraction): Tests directly imported `Phase3HarnessCapture`, `Phase3InteractiveHarnessRunner`, artifact-path helpers, and the public capture factory from `phase3_harness.py`.
  Resolution: migrate those imports to the new focused module and remove the old module exports instead of retaining compatibility aliases.
- Observation: `docs/ExecPlans/phase3_headless_interactive_composition_execplan.md` describes an older `Phase3Composition` design that is not present in current source.
  Resolution: do not resurrect that removed facade; reconcile its current-status wording during documentation review and use this narrower extraction plan as the active plan.
- Observation: The initial affected-test command named `tests/unit/test_phase3_matrix_artifacts.py`, but that file does not exist in the current checkout.
  Resolution: removed that path from the executed validation command and retained the existing matrix-runner and evidence-service coverage.
- Observation: The first high-risk review found `len(sign_requests) + 1` after appending the request, which selected `_002` for the first interactive signing output.
  Resolution: the child follow-up now passes the one-based current request count and asserts the first attempt uses index `1`.

## Decision Log

- Decision: Make `phase3_interactive_capture.py` the deep module for interactive capture, while keeping `Phase3EvidenceService` as the only stable application-facing boundary.
  Rationale: the service already owns operation dispatch and result normalization; a second public composition facade would recreate the compatibility cruft removed by the prior slice.
  Date/Author: 2026-08-01 / Codex.
- Decision: Add `Phase3InteractiveCaptureArtifactPolicy` with only artifact-directory, signed-output-path, and optional-text-writing behavior.
  Rationale: these concerns cross the runner/report boundary, while runner-local Qt, workspace, lifecycle, render, and signing dependencies already have focused bundles and should not be collapsed into a service locator.
  Date/Author: 2026-08-01 / Codex.
- Decision: Move the interactive capture factory out of `phase3_harness.py` and remove its old public export.
  Rationale: the factory is composition-owned and has no reason to be discoverable from the matrix/render helper module; callers can use the application service's lazy capture dependency.
  Date/Author: 2026-08-01 / Codex.
- Decision: Do not extract preview matrix scenario execution, signed matrix lifecycle, or broad PDF/render/image helpers in this slice.
  Rationale: those areas have different lifecycles and artifact semantics, and the fresh review identified them as high-risk seams requiring separate boundary work.
  Date/Author: 2026-08-01 / Codex.
- Decision: Remove compatibility-only mapping/fallback helpers only when search proves no live consumer remains and a boundary test covers the canonical typed result.
  Rationale: stable serialized evidence fields are contracts; private aliases and legacy mapping readers are not contracts once all current consumers migrate.
  Date/Author: 2026-08-01 / Codex.

## Outcomes & Retrospective

The primary extraction and child artifact-numbering correction are implemented, validated, documented, and committed in `60fa8318b`. Repeated compliance/high-risk review and documentation reconciliation are complete. Broad preview/render extraction remains a separate future opportunity.

## Context and Orientation

The application boundary is `src/foliaseal/application/phase3_evidence_service.py`, which accepts `Phase3HarnessCaptureRequest` and matrix requests and exposes capture, preview, signed-acceptance, validation, and evidence operations. `src/foliaseal/application/phase3_evidence_orchestrator.py` dispatches those typed requests for CLI commands. Neither module should import Qt, Pillow, pyHanko, or filesystem-specific presentation code.

`src/foliaseal/presentation/qt/phase3_signed_acceptance_evidence.py` builds the default service and already imports concrete harness code only inside selected-operation factories. Its lazy interactive capture closure should continue to be the only default-service path that imports the interactive composition module.

Before extraction, the interactive cluster at the top of `src/foliaseal/presentation/qt/phase3_harness.py` contained `Phase3HarnessCapture`, `Phase3InteractiveHarnessRunner`, the capture factory, JSON normalizer, and default artifact-path helpers. The current `phase3_interactive_capture.py` boundary owns that contract, runner choreography, normalization, artifact policy, and lazy factory; `phase3_harness.py` retains `_build_phase3_interactive_harness_runner()` as the concrete builder/composition root for Qt bindings, page loading, rendering, workflows, profile/signing factories, session/assembler/report dependencies, and output policy callables.

The new `phase3_interactive_capture.py` module will own that interactive contract and composition policy. It may use lazy imports for the heavy concrete builder in `phase3_harness.py` to avoid import cycles, but it must not make matrix construction eager. `phase3_harness.py` will import the new model/normalizer only as an internal dependency and will no longer be the supported import location for the interactive result or factory. The Qt package's lazy export map must point `Phase3HarnessCapture` to the new module.

## Plan of Work

First create `src/foliaseal/presentation/qt/phase3_interactive_capture.py`. Move the `Phase3HarnessCapture` dataclass and its stable `to_json()` behavior, the recursive JSON-normalization helper, the `Phase3InteractiveHarnessRunner` execution method, and the lazy capture callable into this module. Add a frozen `Phase3InteractiveCaptureArtifactPolicy` whose methods preserve the current artifact-directory derivation, signed-output naming, and optional text-file writing. Keep request/result fields and output formatting byte-for-byte compatible where the existing tests cover them.

The new runner must receive its existing operation-local dependencies explicitly: Qt binding loader, page-count loader, render-backend factory, profile-store factory, signing-executor factory, session runner, capture assembler, contract evaluator, capture factory, checklist renderer, text writer, report finalizer, and artifact policy. The new module may provide a private default builder that lazily imports `phase3_harness` only when interactive capture is first invoked; it must not import or instantiate that graph during module import or headless service construction.

Then update `phase3_harness.py`. Remove the old interactive dataclass, runner, public capture factory, capture-model constructor, and artifact helper definitions from that file. Keep the concrete workspace, matrix, snapshotter, and render helpers that are still live dependencies, and have the private composition builder construct the new runner/dependency object. Any remaining references to the moved model or JSON normalizer must use the focused module explicitly rather than recreating aliases. Do not retain a `Phase3Composition`, `Phase3Harness`, or forwarding compatibility export.

Update `phase3_signed_acceptance_evidence.py` to lazy-import the new interactive capture factory directly. Update `presentation/qt/__init__.py` so `Phase3HarnessCapture` resolves from `phase3_interactive_capture.py`. Migrate reporting, harness, evidence, and CLI tests to the new module. Delete direct tests for removed forwarding names; replace them with boundary tests that prove lazy construction, exact capture request forwarding, artifact-policy naming, capture JSON parity, report/checklist output, and success/failure cleanup.

After the first implementation pass, search for old imports and compatibility symbols. If `Phase3SignedAcceptanceScenarioExecutor.run()` or report fallback readers are found to have no live consumers, remove them in this same slice and update their boundary tests; otherwise record why they remain and leave them untouched rather than guessing at a schema migration.

Finally update README and architecture documentation to describe the new ownership, mark the older composition plan as historical/stale where appropriate, and record the removed compatibility surface. Run focused and full validation, execute both release-fidelity matrix commands, remove only the named temporary directories, verify no process remains, complete compliance reviews, and commit the complete slice.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

1. Confirm the clean baseline and inventory current callers:

       git status --short --branch
       git log -1 --oneline
       rg -n "Phase3HarnessCapture|Phase3InteractiveHarnessRunner|build_interactive_phase3_capture_runner|_default_harness_artifacts_dir|_default_harness_output_pdf_path|_jsonable_capture" src tests README.md docs/ARCHITECTURE.md

2. Add the focused module and migrate the interactive runner. Run the focused boundary tests:

       .venv/bin/python -m pytest -q tests/unit/test_phase3_harness.py tests/unit/test_phase3_harness_reporting.py tests/unit/test_phase3_harness_capture_assembler.py tests/unit/test_phase3_harness_session_runner.py

   Expect the migrated capture/model/report tests to pass without importing the moved symbols from `phase3_harness.py`.

3. Verify default service and import isolation:

       .venv/bin/python -m pytest -q tests/unit/test_phase3_matrix_operations.py tests/unit/test_qa_signed_acceptance_evidence.py tests/unit/test_phase3_evidence_service.py tests/unit/test_phase3_evidence_orchestrator.py tests/unit/test_main_cli.py
       .venv/bin/ruff check src tests
       git diff --check

   A subprocess import of `phase3_matrix_operations`, `phase3_signed_acceptance_evidence`, and `foliaseal.__main__` must show no `PySide6`, `PIL`, or `pyhanko` modules loaded.

4. Run the affected Phase 3 behavior set:

       .venv/bin/python -m pytest -q tests/unit/test_phase3_harness.py tests/unit/test_phase3_harness_reporting.py tests/unit/test_phase3_harness_capture_assembler.py tests/unit/test_phase3_harness_session_runner.py tests/unit/test_phase3_preview_matrix_runner.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_signed_acceptance_scenario_executor.py tests/unit/test_phase3_evidence_service.py tests/unit/test_phase3_evidence_orchestrator.py tests/unit/test_main_cli.py

5. Run the complete suite and observable release-fidelity matrices:

       .venv/bin/python -m pytest -q
       QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-preview-matrix --pdf-path artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf --certificate-path artifacts/generated_acceptance_assets/signed_acceptance_identity.p12 --passphrase secret --scenario-manifest-path tests/fixtures/phase3/release_fidelity_manifest.json --artifacts-dir /tmp/foliaseal-phase3-interactive-preview
       QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-acceptance-matrix --pdf-path artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf --certificate-path artifacts/generated_acceptance_assets/signed_acceptance_identity.p12 --passphrase secret --scenario-manifest-path tests/fixtures/phase3/release_fidelity_manifest.json --artifacts-dir /tmp/foliaseal-phase3-interactive-signed

   Expect 8 preview scenarios with zero errors; 8 signed scenarios with 6 successful signings, 2 matched intentional rejections, zero unexpected errors, and passing acceptance expectations.

6. Prove structural cleanup and clean the environment:

       rg -n "from foliaseal\.presentation\.qt\.phase3_harness import (Phase3HarnessCapture|Phase3InteractiveHarnessRunner|build_interactive_phase3_capture_runner)|Phase3Composition|Phase3Harness\b" src tests README.md
       rm -rf /tmp/foliaseal-phase3-interactive-preview /tmp/foliaseal-phase3-interactive-signed
       ps -eo pid,args | awk '/python.*foliaseal|python.*phase3/ && !/awk/ {print}'

   The structural search must show no removed facade or old interactive export in live source/tests, and the process check must print nothing.

7. After the first implementation pass, spawn an explorer-light compliance reviewer for `docs/ARCHITECTURE.md`, `docs/SPEC.md`, README, and active ExecPlans. Spawn a second explorer-light high-risk reviewer for Qt lazy imports, window/event-loop cleanup, capture JSON/report parity, artifact paths, and compatibility removal. If either finds a concrete discrepancy, create and execute a child ExecPlan, then repeat both reviews.

8. Spawn a worker-light documentation reviewer using architecture-steward to reconcile README, `docs/ARCHITECTURE.md`, the stale prior composition plan, and this active plan. Then spawn a worker-light using write-git-commit to stage only intended files and create the focused main-branch commit. Verify `git status --short --branch` is clean.

## Validation and Acceptance

The slice is accepted when the interactive capture DTO, runner, JSON normalization, lazy factory, and artifact policy live in the focused module; no current caller imports those symbols from `phase3_harness.py`; and the default evidence service remains headless/lazy until capture is selected. Interactive capture must preserve its current capture fields, JSON ordering/indentation, summary/checklist paths, stdout labels, report contents, and success/failure window cleanup. Preview and signed matrices must retain their current summary mappings, artifact paths, lifecycle behavior, and intentional rejection semantics.

The focused and affected tests, full pytest suite, Ruff, diff checks, import-isolation checks, and both release-fidelity matrices must pass. No removed compatibility facade, old interactive export, or duplicate forwarding helper may remain in live source/tests unless the plan records a concrete current consumer. Temporary directories created by this plan must be removed and no FoliaSeal or Phase 3 process may remain.

## Idempotence and Recovery

The extraction is safe to retry because it preserves the application request/result DTOs and moves behavior behind an adapter rather than changing evidence schemas. If an import cycle occurs, keep the new module dependency-light and move the concrete harness import inside the first-call lazy factory; do not restore the old public alias. If a capture JSON or report test fails, compare the serialized output with the pre-migration fixture and correct the moved normalizer or artifact policy, not the application contract. If a matrix command fails, remove only the two named temporary directories and rerun. Never delete tracked fixtures, certificates, catalogs, or broad workspace paths.

## Artifacts and Notes

Record concise evidence during execution:

       baseline commit: b0358ff2c
       focused interactive-capture tests: 90 passed, 1 pre-existing Pillow warning
       affected tests: 138 passed, 1 pre-existing Pillow warning
       full suite: 1040 passed, 1 pre-existing Pillow deprecation warning
       preview matrix: 8 scenarios, 0 errors
       signed matrix: 8 scenarios, 6 successful signings, 2 intentional rejections, expectations passed
       import isolation: no PySide6/PIL/pyhanko before selected operation
       compatibility cleanup: old harness capture/runner exports absent from live source/tests
       process cleanup: no matching FoliaSeal/Phase 3 process
       implementation commit: 60fa8318b

## Interfaces and Dependencies

In `src/foliaseal/presentation/qt/phase3_interactive_capture.py`, define the focused boundary:

    @dataclass(frozen=True)
    class Phase3InteractiveCaptureArtifactPolicy:
        default_artifacts_dir: Callable[..., str | None]
        output_pdf_path: Callable[..., str]
        write_text: Callable[..., None]

    @dataclass(frozen=True)
    class Phase3InteractiveHarnessRunner:
        load_qt_harness_bindings: Callable[..., _QtHarnessBindings]
        load_page_count: Callable[..., int]
        render_backend_factory: Callable[[], Any]
        profile_store_factory: Callable[[], Any]
        build_phase3_signing_executor: Callable[[], Any]
        session_runner: Phase3HarnessSessionRunner
        capture_assembler: Phase3HarnessCaptureAssembler
        contract_evaluator: Callable[..., Any]
        capture_factory: Callable[..., Phase3HarnessCapture]
        checklist_renderer: Callable[..., str]
        report_finalizer: Callable[..., Any]
        artifact_policy: Phase3InteractiveCaptureArtifactPolicy

        def run(self, request: Phase3HarnessCaptureRequest) -> Phase3HarnessCapture: ...

    def build_interactive_phase3_capture_runner() -> Callable[
        [Phase3HarnessCaptureRequest], Phase3HarnessCapture
    ]: ...

The application service and orchestrator remain the stable caller boundary. `Phase3HarnessCaptureRequest`, `Phase3HarnessCapture`, capture JSON, matrix request/result types, CLI labels, and artifact/report fields are compatibility contracts. Qt, Pillow, pyHanko, PDF readers, render backends, profile stores, signing executors, lifecycle/workspace adapters, and filesystem writers are local or external adapters injected behind the interactive runner; they must not leak into the application layer.

## Change-Slice Boundary

This is one primary architecture/refactor change with directly affected tests and documentation/status updates. Allowed changes are the new interactive-capture module, migration of its callers/tests/Qt exports, narrow artifact-policy extraction, removal of obsolete interactive compatibility exports and proven forwarding helpers, current README/architecture/ExecPlan updates, and temporary matrix artifacts. Forbidden changes include redesigning `Phase3EvidenceService` DTOs, changing CLI commands or printed labels, changing matrix lifecycle/manifest/signing semantics, broad preview/render/PDF helper extraction, redesigning the signing workspace, modifying `docs/SPEC.md` requirements, or unrelated GUI/certificate work.

Plan revision note: created 2026-08-01 after the required fresh explorer review. This plan supersedes the stale prose in `phase3_headless_interactive_composition_execplan.md` for the current extraction slice without resurrecting the removed `Phase3Composition`/`Phase3Harness` facades.
