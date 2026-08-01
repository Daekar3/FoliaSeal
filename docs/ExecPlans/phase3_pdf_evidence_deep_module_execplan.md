# Extract the Phase 3 signed-PDF evidence deep module

This ExecPlan is a living document and must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`. It defines one complete implementation slice after the headless-first composition work committed at `0a86d5eaf2ee5c14d72e9bd7b0d6d04d5076c484`.

## Purpose / Big Picture

After this slice, changing signed-PDF evidence will no longer require navigating the 4,297-line `phase3_harness.py`. Signature counting, signature metadata, cryptographic verification, certification restrictions, timestamp diagnostics, visible appearance parsing, and PDF appearance-stream helpers will live behind one focused `Phase3PdfSignatureSnapshotter` module. The Qt harness will only compose that module with the existing signed-output and capture assemblers.

Users will observe the same Phase 3 behavior: interactive captures keep the same JSON fields and checklist output, preview and signed matrices keep the same summary keys and artifact paths, and intentional rejection rows remain distinguishable from execution errors. The change is architectural and testability-focused; it must not alter signing semantics or CLI behavior.

The user's compatibility-cleanup requirement is part of this slice. The duplicate `_snapshot_signing_result_payload` implementation, obsolete forwarding helpers, and tests that target removed harness-private implementations will be deleted after their callers move to the focused module. No compatibility alias will be added merely to preserve an internal test import.

## Child ExecPlan Dependencies

- [x] The prior headless-first `Phase3Composition`/lazy interactive slice is present at commit `0a86d5eaf2ee5c14d72e9bd7b0d6d04d5076c484`.
- [x] A fresh explorer-light review inspected the live post-commit harness, private helper usage, stable output contracts, and extraction risks before this plan was written.
- [x] The compliance follow-up child ExecPlan was created and completed after the initial review found parity, direct-boundary-test, and documentation gaps.

## Progress

- [x] (2026-08-01) Selected the recommended hybrid: retain the application evidence service/orchestrator and headless-first composition, while deepening the remaining pure signed-PDF evidence seam.
- [x] (2026-08-01) Completed the required fresh explorer review at the current clean `main` tree.
- [x] (2026-08-01) Wrote this self-contained one-slice ExecPlan before implementation.
- [x] (2026-08-01) Added `Phase3PdfSignatureSnapshotter` and moved pure signature/AP/verification/timestamp parsing helpers out of `phase3_harness.py`.
- [x] (2026-08-01) Migrated harness builders, signed-output/capture wiring, and tests; removed the duplicate signing-result serializer and stale helper definitions/import targets.
- [x] (2026-08-01) Ran focused affected tests, full suite (`1040 passed`, one pre-existing Pillow warning), Ruff, diff checks, release-fidelity matrices, structural cleanup, and process cleanup.
- [x] (2026-08-01) Completed initial and high-risk compliance reviews; restored malformed-input parity, added direct snapshotter boundary coverage, and reconciled architecture ownership/collaborator references through the child follow-up.
- [x] (2026-08-01) Completed the final independent compliance and high-risk re-reviews; removed the dead signed-run forwarding wrapper and reconciled the historical plan references they identified.
- [x] (2026-08-01) Created focused implementation commit `06697aec0` and verified the checkout is clean on `main`.

## Surprises & Discoveries

- Observation: The previous composition slice already moved lazy operation construction into `Phase3Composition`; repeating that extraction would create churn rather than deepen the remaining module.
  Evidence: `Phase3Composition.default_headless()` and `with_interactive_qt()` are live at `src/foliaseal/presentation/qt/phase3_harness.py:234-278`, and the completed ExecPlan records their validation at `docs/ExecPlans/phase3_headless_interactive_composition_execplan.md`.
- Observation: Signed-PDF evidence functions are a cohesive pure boundary even though they currently sit among Qt and preview helpers.
  Evidence: `_count_embedded_signatures`, `_snapshot_output_signature`, `_snapshot_output_verification`, `_snapshot_visible_signature_appearance`, timestamp-status helpers, appearance XObject parsing, PDF rectangle conversion, and metadata serialization are all used by signed-output/capture assemblers and have no widget ownership.
- Observation: `_snapshot_signing_result_payload` is duplicated in `phase3_harness.py` and `phase3_harness_capture_assembler.py`.
  Evidence: The capture assembler's implementation is already used by `build_signed_run_bundle`; the harness copy is injected only into the signed scenario executor. One canonical implementation can serve both callers without changing its mapping keys.
- Observation: Several harness-private wrappers exist only to make white-box tests patch the monolithic module.
  Evidence: Tests directly import `_snapshot_output_verification`, `_snapshot_visible_signature_appearance`, and composition helper builders, while production runners consume injected callables. The migration must retarget those tests to the new boundary before deleting the old names.
- Observation (implementation): The existing PDF text parser decodes escaped literal strings and counts `Tj`/`TJ` operators with a regular expression; a naïve character scanner changed behavior.
  Resolution: The new snapshotter retained the exact regex and escape-decoding behavior before deleting the harness copies; valid signed-appearance tests and both release-fidelity matrices remained green.
- Observation (compliance): High-risk review found recursive appearance-state/hex-text parsing and timestamp-presence semantics are inherited evidence debt rather than extraction regressions.
  Resolution: Preserve the existing serialized contract in this slice, add malformed/unsigned boundary coverage, and defer recursive AP parsing and timestamp-semantic redesign to a later behavior-focused plan.

## Decision Log

- Decision: Extract pure signed-PDF evidence before preview/Qt widget geometry.
  Rationale: The PDF/AP/verification cluster has a cohesive dependency boundary and low coupling to `testing_adapter`, `processEvents()`, and Qt widget state. Preview-render extraction is higher risk and remains a later candidate.
  Date/Author: 2026-08-01 / Codex.
- Decision: Keep `Phase3HarnessCapture`, `Phase3Composition`, `Phase3Harness`, the application request DTOs, and matrix summary mappings stable.
  Rationale: These are current contracts consumed by the CLI, evidence service, reporting, and acceptance tooling. This slice removes internal cruft without reopening the completed composition migration.
  Date/Author: 2026-08-01 / Codex.
- Decision: Define `Phase3PdfSignatureSnapshotter` as a focused dataclass with methods for signature count, signature metadata, verification, and visible-appearance snapshots; keep JSON-compatible dictionaries at this presentation/evidence edge.
  Rationale: The existing capture and matrix contracts are mapping-based serialized evidence. Introducing a second typed DTO hierarchy in the same slice would broaden risk without improving the observable contract.
  Date/Author: 2026-08-01 / Codex.
- Decision: Delete the duplicate signing-result serializer and migrate tests instead of preserving a compatibility alias.
  Rationale: The user explicitly requested removal of legacy compatibility pieces and cruft. The serializer's mapping keys are the contract; its old module location is not.
  Date/Author: 2026-08-01 / Codex.

## Outcomes & Retrospective

The completed slice owns pure signed-PDF evidence in `phase3_pdf_signature_snapshotter.py`; the harness composition root supplies bound methods to existing assemblers. Direct boundary coverage and malformed-input parity are complete, and `docs/ARCHITECTURE.md` now records the ownership and collaborator direction. The final compliance review also removed the unused `_build_signed_run_bundle` forwarding wrapper and reconciled stale historical references. Recursive AP-state/hex-text parsing and timestamp-presence semantic changes remain deferred behavior-focused debt. The implementation commit is `06697aec0` (`Extract Phase 3 PDF evidence snapshotter`).

## Context and Orientation

The application layer in `src/foliaseal/application/phase3_evidence_service.py` and `phase3_evidence_orchestrator.py` owns caller requests, operation dispatch, result normalization, and evidence decisions. The Qt presentation layer supplies concrete runners. `src/foliaseal/presentation/qt/phase3_harness.py` remains the composition root for `Phase3Harness`, `Phase3Composition`, interactive capture, preview/signed matrix builders, and a large set of helper functions.

The target cluster reads signed PDFs after signing. It counts embedded signatures, extracts field metadata and byte ranges, validates cryptographic integrity and timestamp trust, inspects certification restrictions, parses visible appearance streams, counts text operators, summarizes image XObjects, and serializes pyHanko/PDF values into JSON-safe values. It must not own Qt windows, event loops, shell callbacks, scenario mutation, matrix iteration, checklist rendering, or application request validation.

The existing `Phase3SignedOutputSnapshotter` in `phase3_signed_output_snapshotter.py` already owns the orchestration of these evidence pieces for one successful output, and `Phase3HarnessCaptureAssembler` owns stable capture payload shaping. The new snapshotter supplies their low-level PDF evidence collaborators. `Phase3SignedOutputRenderSnapshotter` remains responsible for rasterizing signed output and comparing it with the preview; that Qt/render seam is intentionally outside this slice.

## Plan of Work

First create `src/foliaseal/presentation/qt/phase3_pdf_signature_snapshotter.py`. Define a frozen `Phase3PdfSignatureSnapshotter` with methods equivalent to the current behavior: `count_embedded_signatures(output_file)`, `snapshot_output_signature(output_file)`, `snapshot_output_verification(output_file, trust_policy=None)`, and `snapshot_visible_signature_appearance(output_file)`. Move the private timestamp-status helpers, appearance XObject/text parsing helpers, PDF rectangle/name/numeric serializers, and pyHanko metadata serializer needed only by those methods into the new module. Keep exception-to-JSON behavior and all existing error strings stable.

Then update `phase3_harness.py` to construct one snapshotter in its existing builder path and pass bound methods into `Phase3HarnessCaptureAssembler`, `Phase3SignedOutputSnapshotter`, and any signed scenario dependency bundle. Import only the small helper needed by `_render_signed_annotation_appearance_direct` if that function still needs PDF rectangle conversion. Do not make the new module import `phase3_harness.py`; the dependency direction must remain from the harness composition root into the focused snapshotter.

Move the canonical `_snapshot_signing_result_payload` implementation into a small shared evidence-format location, preferably `phase3_harness_capture_assembler.py` if no second module is needed, and import it from the signed scenario wiring. Delete the duplicate implementation from `phase3_harness.py`. Remove `_snapshot_successful_signed_output` and `_build_signed_run_bundle` forwarding wrappers if callers can use the existing `Phase3SignedOutputSnapshotter` and `Phase3HarnessCaptureAssembler` directly without changing production behavior. Do not remove wrappers still needed by live workspace/session composition in this slice.

Retarget tests that directly import the removed PDF helpers to `Phase3PdfSignatureSnapshotter`. Add boundary tests proving missing files, unsigned PDFs, valid signed outputs, certification metadata, timestamp trust fields, visible text/image appearance facts, malformed appearance streams, and JSON-safe metadata serialization preserve the prior mappings. Keep one capture-assembler contract test and one signed-output snapshotter integration test to prove the new module is wired into real callers.

Update `docs/ARCHITECTURE.md`, `README.md` if the module ownership is user-relevant, and this ExecPlan. Document that pure signed-PDF evidence is owned by the new snapshotter, while Qt/render comparison remains in its existing adapter. Record every removed compatibility helper and the rationale for leaving preview/widget extraction to a later slice.

## Concrete Steps

Run commands from `/home/daekar/FoliaSeal`.

1. Confirm the clean baseline and inventory target symbols:

       git status --short --branch
       rg -n "_count_embedded_signatures|_snapshot_output_signature|_snapshot_output_verification|_snapshot_visible_signature_appearance|_snapshot_signing_result_payload|_snapshot_pdf_rect|_snapshot_appearance_xobjects" src tests

2. Add the focused snapshotter and migrate production wiring. Run the focused tests after each migration:

       .venv/bin/python -m pytest -q tests/unit/test_phase3_harness.py tests/unit/test_phase3_harness_capture_assembler.py tests/unit/test_phase3_signed_output_snapshotter.py tests/unit/test_phase3_signed_output_render_snapshotter.py

   The tests must continue to validate the old capture and signed-output mappings while the low-level implementation now lives in the new module.

3. Run the affected evidence and CLI tests:

       .venv/bin/python -m pytest -q tests/unit/test_phase3_harness.py tests/unit/test_phase3_harness_capture_assembler.py tests/unit/test_phase3_harness_reporting.py tests/unit/test_phase3_signed_acceptance_scenario_executor.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_evidence_service.py tests/unit/test_phase3_evidence_orchestrator.py tests/unit/test_main_cli.py
       .venv/bin/ruff check src tests
       git diff --check

4. Run the complete suite and release-fidelity matrices. The repository fixture and certificate paths are tracked and must not be modified:

       .venv/bin/python -m pytest -q
       QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-preview-matrix --pdf-path artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf --certificate-path artifacts/generated_acceptance_assets/signed_acceptance_identity.p12 --passphrase secret --scenario-manifest-path tests/fixtures/phase3/release_fidelity_manifest.json --artifacts-dir /tmp/foliaseal-phase3-pdf-evidence-preview
       QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-acceptance-matrix --pdf-path artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf --certificate-path artifacts/generated_acceptance_assets/signed_acceptance_identity.p12 --passphrase secret --scenario-manifest-path tests/fixtures/phase3/release_fidelity_manifest.json --artifacts-dir /tmp/foliaseal-phase3-pdf-evidence-signed

   Expect the current baseline behavior: eight preview scenarios with zero errors; eight signed scenarios with six successful signings, two matched intentional rejections, zero unexpected errors, and acceptance expectations passing.

5. Prove compatibility cleanup and cleanup the environment:

       rg -n "_snapshot_signing_result_payload|_count_embedded_signatures|_snapshot_output_signature|_snapshot_output_verification|_snapshot_visible_signature_appearance" src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_phase3_harness.py
       rm -rf /tmp/foliaseal-phase3-pdf-evidence-preview /tmp/foliaseal-phase3-pdf-evidence-signed
       ps -eo pid,args | awk '/python.*foliaseal|python.*phase3/ && !/awk/ {print}'

   The search should show no deleted duplicate/helper definitions or stale test imports in the monolithic harness. The process check must print nothing.

6. After the first implementation pass, run two independent explorer-light compliance reviews: one against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, README, and stable evidence contracts; one high-risk review focused on pyHanko/PDF parsing, malformed-file handling, serializer parity, Qt/render lifecycle boundaries, and artifact cleanup. Address any findings in this plan and code before documentation and commit.

7. Spawn a worker-light documentation reviewer using `architecture-steward` to reconcile README, `docs/ARCHITECTURE.md`, and this ExecPlan. Then spawn a worker-light using `write-git-commit` to stage only intended files and create one focused commit. Verify `git status --short --branch` is clean afterward.

## Validation and Acceptance

The slice is accepted when `Phase3PdfSignatureSnapshotter` owns the pure signed-PDF evidence primitives and `phase3_harness.py` no longer defines them or their duplicate signing-result serializer. Existing callers still receive identical JSON-compatible signature, verification, certification, timestamp, visible-appearance, and error mappings. The interactive capture and matrix commands retain their current CLI headings, summary paths, counters, artifact names, intentional rejection semantics, and cleanup behavior.

The focused tests, complete pytest suite, Ruff, and diff checks must pass. The release-fidelity preview matrix must report eight successful scenarios and zero errors. The signed matrix must report eight scenarios, six successful signings, two matched intentional rejections, zero unexpected errors, and passing acceptance expectations. Structural searches must show removed helpers absent from the monolithic harness/tests, and no FoliaSeal or Phase 3 process may remain.

## Idempotence and Recovery

The extraction is repeatable because it preserves callable signatures and serialized mappings. If a test fails after moving a helper, compare the new snapshotter output with the pre-migration fixture and correct only the adapter or serializer; do not restore duplicate helpers in `phase3_harness.py`. Keep a temporary compatibility import only during the same migration command if needed, then remove it before acceptance. Delete only the two explicitly named temporary directories. Never delete tracked PDFs, certificates, fixtures, catalogs, or broad workspace paths.

## Artifacts and Notes

Record concise evidence here during implementation:

       baseline commit: 0a86d5eaf2ee5c14d72e9bd7b0d6d04d5076c484
       focused snapshotter/assembler tests: 100 passed, 1 warning
       direct snapshotter boundary tests: 3 passed
       full suite: 1040 passed, 1 pre-existing Pillow deprecation warning
       preview matrix: 8 scenarios, 0 errors
       signed matrix: 8 scenarios, 6 successful signings, 2 intentional rejections, expectations passed
       compatibility cleanup: duplicate PDF helpers/serializer and unused `_build_signed_run_bundle` forwarding wrapper absent from phase3_harness.py; stale private-helper test seams removed
       process cleanup: no matching FoliaSeal/Phase 3 process
       commit: 06697aec0 (Extract Phase 3 PDF evidence snapshotter)

## Interfaces and Dependencies

In `src/foliaseal/presentation/qt/phase3_pdf_signature_snapshotter.py`, define:

    @dataclass(frozen=True)
    class Phase3PdfSignatureSnapshotter:
        def count_embedded_signatures(self, output_file: Path) -> int | None: ...
        def snapshot_output_signature(self, output_file: Path) -> dict[str, Any] | None: ...
        def snapshot_output_verification(
            self,
            output_file: Path,
            trust_policy: TimestampTrustPolicy | None = None,
        ) -> dict[str, Any] | None: ...
        def snapshot_visible_signature_appearance(
            self,
            output_file: Path,
        ) -> dict[str, Any] | None: ...

The snapshotter may use pyHanko PDF readers/validation, `ValidationContext`, certification inspection, and timestamp trust helpers because it is a presentation/evidence adapter. It must not import Qt widgets or `phase3_harness.py`. Its methods return the existing JSON-ready mappings so `Phase3SignedOutputSnapshotter` and `Phase3HarnessCaptureAssembler` can consume bound methods through their existing callable dependency fields.

The stable serialized fields include signature field/name/location/contact information, byte ranges, subfilter, digest algorithm, coverage, DocMDP level, cryptographic validity, integrity, trust, signature count, timestamp fields, certification restrictions, signer subject, annotation rectangle, appearance bounding box, stream length, text fragments/operators, image XObjects, and existing error fields. Preserve `None` versus `False` distinctions and existing exception-to-mapping behavior.

## Change-Slice Boundary

This is one primary architecture/refactor change with affected tests and documentation/status updates. Allowed changes are the new signed-PDF snapshotter, its helper ownership, harness/signed-output/capture wiring, duplicate serializer/wrapper removal, focused test migration, README/architecture/ExecPlan updates, and temporary matrix artifacts. Forbidden changes include redesigning application evidence DTOs, changing CLI commands or labels, changing signing semantics, changing scenario manifests, changing Qt workspace/testing-adapter behavior, broad preview-render extraction, certificate work, or unrelated GUI styling.

Plan revision note: created 2026-08-01 after the required fresh explorer review. The plan deliberately targets the remaining pure signed-PDF evidence cluster because the prior headless-first composition slice is already complete; the user's compatibility-cleanup requirement is limited here to duplicate serializers, obsolete forwarding wrappers, and stale white-box test seams.
