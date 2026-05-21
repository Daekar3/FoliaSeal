# Add a read-only signature review summary to the signing shell

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows the requirements in `.agents/skills/write-execplan/PLANS.md`. It is self-contained so a contributor can resume the slice from only this file and the current repository tree.

## Purpose / Big Picture

FoliaSeal's V1 GUI spec requires users to inspect existing signatures and verify signed results with plain-language guidance. The signing shell now shows a compact read-only `Document review` card that summarizes the current PDF's signature state, certification restrictions, and plain-language guidance without taking on full text search or text copy.

This slice is intentionally narrow. It does not add document-text search, clipboard support, or a new viewer mode. It only adds a read-only signature/certification summary for the currently opened PDF and keeps the wording honest about what was verified locally.

## Child ExecPlan Dependencies

- [x] Explorer review of the viewer/spec gap completed. The report identified viewer-side signature inspection as the smallest high-leverage next slice and explicitly deferred search/select/copy to later work.
- [x] Documentation update worker reviewed `docs/ARCHITECTURE.md` and this ExecPlan after implementation to describe the new read-only review surface.
- [x] Commit worker created the required git commit once implementation, compliance review, and documentation updates were complete.

## Progress

- [x] (2026-05-21T10:40:19Z) Confirmed the next slice is viewer-side read-only signature inspection rather than text search/copy.
- [x] (2026-05-21T10:40:19Z) Reviewed `docs/SPEC.md`, `docs/ARCHITECTURE.md`, `signing_shell.py`, `phase3_signing_backend.py`, `infra/certification.py`, `phase3_harness.py`, and the existing Qt shell tests to identify the narrowest integration seam.
- [x] (2026-05-21T10:44:05Z) Added `src/foliaseal/application/document_review.py` with a failure-tolerant read-only review inspector and plain-language summary builder for unavailable, unsigned, signed, and certification-restricted PDFs.
- [x] (2026-05-21T10:44:05Z) Added focused helper tests in `tests/unit/test_document_review.py` covering unsigned, signed, certification-restricted, and missing-file review states.
- [x] (2026-05-21T10:44:05Z) Added a read-only `Document review` card to `SigningWorkspaceWidget`, exposed the current document path from `ViewerWorkflow`, and added a shell test that proves the card renders an injected review summary.
- [x] (2026-05-21T10:44:05Z) Updated `docs/ARCHITECTURE.md` and this ExecPlan to describe the implemented document review helper, the `Document review` card, and the current pending compliance-review state.
- [x] (2026-05-21T10:48:47Z) Added file-backed tests for the concrete `PyHankoDocumentReviewInspector` path so the default inspector is exercised for unsigned and signed/certification-restricted PDFs without introducing full PDF fixture matrices.
- [x] (2026-05-21T10:48:47Z) Ran focused validation after the compliance fixes: `pytest tests/unit/test_document_review.py tests/unit/test_qt_signing_shell.py` passed with 80 tests, `ruff check src/foliaseal/application/document_review.py src/foliaseal/application/viewer_workflow.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_document_review.py tests/unit/test_qt_signing_shell.py` passed, and `git diff --check` passed.
- [x] (2026-05-21T10:48:47Z) Spawned an `explorer-light` compliance reviewer for `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and related requirements after the first implementation pass.
- [x] (2026-05-21T10:48:47Z) Spawned a `worker-light` documentation updater after the compliance review found stale architecture and ExecPlan text.
- [x] (2026-05-21T10:50:06Z) Completed the final compliance review after the documentation and coverage fixes. The reviewer reported PASS with no remaining findings and no further documentation work required.
- [x] Spawned the `worker-light` commit worker after the slice was complete.

## Surprises & Discoveries

- Observation: The signing shell already exposes a post-sign plain-language completion message, but there is no general review surface for the currently opened PDF.
  Evidence: `src/foliaseal/presentation/qt/signing_shell.py` updates `sign_result_label` only after `submit_sign_request()`, while the viewer workflow remains limited to render/navigation/selection behavior.

- Observation: Real signature/certification facts already exist in code, but they are split across the signing backend, certification helpers, and the Phase 3 harness snapshot path.
  Evidence: `PyHankoSignatureVerifier.verify()` returns `VerificationSummary`, `inspect_pdf_certification_reader()` classifies DocMDP restrictions, and `_snapshot_output_verification()` already extracts signer subject and local verification facts.

- Observation: Existing shell tests instantiate the widget with fake viewer paths that do not exist on disk, so the new review feature had to fail soft by design.
  Evidence: `tests/unit/test_qt_signing_shell.py` builds the shell with `ViewerWorkflow(document_path="/tmp/sample.pdf", ...)`; the default review inspector now returns a `Review unavailable` summary instead of raising.

## Decision Log

- Decision: Keep this slice in the signing shell instead of extending `viewer_widget.py`.
  Rationale: The shell already owns the broader document-centric workflow and has an existing read-only card pattern (`Signing flow`) that can host another compact review surface without adding new viewer interaction semantics.
  Date/Author: 2026-05-21 / Codex

- Decision: Leave search/select/copy for a later ExecPlan.
  Rationale: Text review requires a separate extraction and clipboard path, while signature inspection can be delivered now by reusing existing verification/certification logic.
  Date/Author: 2026-05-21 / Codex

## Outcomes & Retrospective

Implementation, focused validation, compliance-fix coverage, documentation updates, and final compliance review are complete. The required commit has been created, and the slice is now closed.

## Context and Orientation

The relevant UI lives in `src/foliaseal/presentation/qt/signing_shell.py`. `SigningWorkspaceWidget` composes the viewer, the properties panel, the existing `Signing flow` summary card, the new read-only `Document review` card, the sign button, and the signing result label. The viewer itself is built by `build_qt_pdf_viewer_widget()` and should stay focused on rendering and placement interactions for this slice.

The viewer logic is in `src/foliaseal/application/viewer_workflow.py`. It owns render, zoom, pan, page navigation, and selection-to-PDF-rectangle conversion. It now exposes the current document path through a safe property so the shell can inspect the PDF currently being viewed without reaching into the widget layer.

Signature/certification inspection logic now lives in `src/foliaseal/application/document_review.py`. It wraps the reusable read-only inspection logic in the application layer instead of keeping it trapped in the harness path. `src/foliaseal/application/phase3_signing_backend.py` contains `PyHankoSignatureVerifier.verify()`, which validates the latest embedded signature after signing. `src/foliaseal/infra/certification.py` contains `inspect_pdf_certification_reader()`, which reports DocMDP permission and whether certification restricts further changes. `src/foliaseal/presentation/qt/phase3_harness.py` contains `_snapshot_output_verification()`, which already extracts signer-subject and basic verification facts.

Tests for the shell live in `tests/unit/test_qt_signing_shell.py`. They use fake Qt bindings and a fake viewer widget, so new UI behavior should be verifiable without real Qt or real PDF rendering. New tests for the application review helper should live in a dedicated unit file such as `tests/unit/test_document_review.py`.

## Plan of Work

First, add a new application module for document review, for example `src/foliaseal/application/document_review.py`. Define a small immutable summary model and an inspector protocol or concrete helper that accepts a PDF path and returns read-only facts plus plain-language headline/detail text. The helper must handle four states safely: the file cannot be inspected, the PDF has no embedded signatures, the PDF has signatures and local verification succeeds, and the PDF's certification policy restricts additional changes. The wording must say `verified locally` or equivalent and must not claim broader trust than the code actually proves.

Second, add focused tests for the helper before touching the shell. The tests should verify plain-language outcomes for unsigned, signed, and certification-restricted cases, and should keep the logic independent enough that the shell can consume it without duplicating formatting logic.

Third, extend `ViewerWorkflow` with a simple public accessor for the current document path if one does not already exist. Then update `SigningShellAdapter.create()` / `build_qt_signing_shell()` and `SigningWorkspaceWidget` to accept an optional document-review inspector dependency. Build a new `Document review` group box with two labels, similar to the existing `Signing flow` card, and populate it from the application review helper. Keep the card read-only and additive. Avoid triggering a fresh inspection on every viewer mouse interaction if the path has not changed.

Fourth, add a Qt shell test that injects a fake review inspector and asserts the new card shows the expected headline/detail when the shell is created or refreshed. Existing shell tests should continue to pass even when the backing PDF path does not exist.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

Inspect the relevant files before editing:

    sed -n '70,95p' docs/SPEC.md
    sed -n '145,170p' docs/ARCHITECTURE.md
    sed -n '2840,3285p' src/foliaseal/presentation/qt/signing_shell.py
    sed -n '391,460p' src/foliaseal/application/phase3_signing_backend.py
    sed -n '1,120p' src/foliaseal/infra/certification.py

After adding the helper and tests, run:

    pytest tests/unit/test_document_review.py tests/unit/test_qt_signing_shell.py

Expected outcome: the new helper tests pass and the shell test proves the review card renders the injected summary without breaking existing shell coverage.

Then run focused lint:

    ruff check src/foliaseal/application/document_review.py src/foliaseal/application/viewer_workflow.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_document_review.py tests/unit/test_qt_signing_shell.py

If the new shell test is easier to run by name because `test_qt_signing_shell.py` is large, narrow the pytest invocation and record the exact command/results in this plan.

## Validation and Acceptance

Acceptance for this slice is a demonstrable read-only review surface in the shell, not a full document-review feature set.

The helper tests must prove the application layer produces honest plain-language summaries for:

- an unsigned PDF, showing no signatures and no certification restriction,
- a signed PDF, showing signature presence and local verification wording,
- a certification-restricted PDF, warning that further changes or signatures may be blocked.

The shell test must prove the `Document review` card renders the helper output in the built shell widget. Existing shell construction tests must continue to succeed when the viewer document path does not exist, which means the new review path must fail soft rather than crashing widget creation.

Focused validation passes when the selected pytest command and the focused `ruff check` both pass.

## Idempotence and Recovery

The review helper is read-only. Re-running its tests and re-opening the shell should be safe and should not mutate PDFs or configuration state.

If the real inspection path turns out to require more heavy-weight PDF fixtures than is reasonable for this slice, fall back to testing the pure plain-language summary builder directly and use the shell test with an injected fake inspector to prove integration. Do not expand the slice into a full end-to-end PDF fixture matrix.

If the shell card causes too many existing tests to depend on real files, make the review inspector injectable and keep the default implementation failure-tolerant for missing/unreadable PDFs.

## Artifacts and Notes

Current requirement evidence:

    docs/SPEC.md: V1 must support inspect existing signatures and verify the signed result with plain-language guidance.
    docs/ARCHITECTURE.md: the Qt shell is the document-centric workflow surface and now includes a read-only Document review card backed by the application helper.
    signing_shell.py: currently exposes Signing flow, Document review, and post-sign result text.

Validation evidence after the compliance-fix pass:

    pytest tests/unit/test_document_review.py tests/unit/test_qt_signing_shell.py
    80 passed in 10.31s

    ruff check src/foliaseal/application/document_review.py src/foliaseal/application/viewer_workflow.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_document_review.py tests/unit/test_qt_signing_shell.py
    All checks passed!

## Interfaces and Dependencies

Add an application-layer review API with a stable shape, for example:

    @dataclass(frozen=True)
    class DocumentReviewSummary:
        headline: str
        detail: str
        signature_count: int | None
        signer_subject: str | None = None
        docmdp_permission: str | None = None
        certification_restricted: bool = False
        restriction_reason: str | None = None
        cryptographic_validation_passed: bool | None = None
        inspection_error: str | None = None

    class DocumentReviewInspector(Protocol):
        def inspect(self, input_pdf_path: str) -> DocumentReviewSummary:
            ...

The concrete implementation may use `pyhanko.pdf_utils.reader.PdfFileReader`, `pyhanko.sign.validation.validate_pdf_signature`, and `foliaseal.infra.certification.inspect_pdf_certification_reader`. The shell should consume the summary as already-formatted review text instead of reproducing plain-language formatting rules in the widget layer.
