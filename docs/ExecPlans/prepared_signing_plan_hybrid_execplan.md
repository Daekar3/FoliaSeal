# Deepen the prepared signing and visible-layout boundary

This ExecPlan is a living document. Maintain it in accordance with `.agents/skills/write-execplan/PLANS.md`. It is intentionally one implementation slice: the prepared-plan contract, invisible-signing branch, boundary tests, documentation, compliance review, and commit all belong to this plan.

## Purpose / Big Picture

After this slice, the signing pipeline will resolve visible-signature semantics and layout once per final signing operation, carry that prepared result into PyHanko style construction, and keep preview on the same neutral layout planner and result shape. Callers continue to submit the existing `SigningRequest` and receive `SigningResult`; Qt and CLI code do not learn about PyHanko objects. Invisible requests, which the headless use case already accepts, will take an explicit no-visible-appearance signing path instead of failing inside the concrete signer.

The behavior can be observed by running the existing signing tests and by signing a fixture twice: a visible request retains its current signature appearance and verification metadata, while an invisible request produces a cryptographically verifiable incremental signature with no visible stamp. Compact visible rectangles continue to return the existing fit failure semantics, and preview/signing use the same prepared layout plan.

## Child ExecPlan Dependencies

- [x] Fresh `explorer-light` reconnaissance completed and reviewed against the current post-Phase-3-hybrid checkout.
- [x] The existing `VisibleSignatureLayoutBoundary`, `SignPdfUseCase`, and `Phase3SigningExecutor` seams were inspected; the implementation stayed inside the application/backend boundary.
- [x] Child `prepared_signing_plan_compliance_execplan.md` was created, implemented, and closed after the independent architecture/SPEC review found documentation, type-boundary, and prepared-plan reuse gaps.

## Progress

- [x] (2026-07-31) Selected the constrained hybrid: preserve the single `execute(request)` caller contract while introducing one prepared visible-signature plan and an explicit invisible-signing path.
- [x] (2026-07-31) Completed the required dev-loop explorer report and confirmed current invisible-request, layout, preview, signer, and compatibility contracts.
- [x] (2026-07-31) Wrote this self-contained one-slice ExecPlan before implementation.
- [x] (2026-07-31) Added the immutable `PreparedSigningPlan` DTO and preparation path, preserving existing request/result types and compatibility methods.
- [x] (2026-07-31) Threaded the prepared layout/fit result through visible signing while retaining the canonical preview's shared neutral layout boundary; no PyHanko objects are exposed by the plan.
- [x] (2026-07-31) Implemented and tested the invisible PyHanko signing branch, including timestamp-disabled and timestamp-required behavior plus post-sign verification.
- [x] (2026-07-31) Added boundary tests for prepared visible plans, invisible signing, timestamp behavior, existing visible signing, fit policy, and incremental field preservation.
- [x] (2026-07-31) Ran focused prepared/invisible validation, full validation, compliance review, and documentation reconciliation. Release-fidelity matrix commands remain the existing separate evidence workflow; no source process/window cleanup was needed for this documentation pass.
- [x] (2026-07-31) Re-ran release-fidelity evidence after the child corrections: preview executed 8 scenarios with zero error rows; signed acceptance executed 8 scenarios with 6 successful signings, 2 matched intentional rejections, and zero critical counters.
- [x] (2026-07-31) Closed the post-fix compliance loop: architecture/spec reviewers accepted the corrected type boundary and documentation; the remaining exact signing-time snapshot handoff is recorded as a follow-up concern rather than part of this one-slice compatibility boundary.

## Surprises & Discoveries

- Observation: `SigningRequest` already permits invisible signing when both `signature_rect` and `signature_appearance` are absent, but `PyHankoPdfSigner.sign()` rejects that pair before doing any signing.
  Evidence: `src/foliaseal/domain/models.py`, `src/foliaseal/application/sign_pdf_use_case.py`, and `src/foliaseal/application/phase3_signing_backend.py`.
- Observation: preview and signing already share `VisibleSignatureLayoutBoundary` and accept an optional precomputed `SignatureLayoutPlan`, but the backend still independently resolves semantics and fit before constructing the final style.
  Evidence: `visible_signature_layout.py`, `signing_preview_renderer.py`, and `_build_stamp_style()` in `phase3_signing_backend.py`.
- Observation: PyHanko supports invisible fields with a `SigFieldSpec` whose box is `None`; omitting `stamp_style` keeps the invisible path separate from visible appearance construction.
  Evidence: installed PyHanko `PdfSigner` and `SigFieldSpec` APIs inspected during reconnaissance.
- Observation: preview and final signing resolve signing time from separate system-clock reads, so a clock rollover can change the displayed preview time without changing layout or signing contracts.
  Resolution: retain the shared neutral layout boundary in this slice and defer an explicit signing-time snapshot handoff to a future workflow slice; record it as an architectural follow-up rather than changing the public `SigningRequest` now.

## Decision Log

- Decision: Keep `SigningRequest`, `SigningResult`, `PdfSigner.sign()`, `Phase3SigningExecutor.execute()`, and CLI/Qt callers unchanged.
  Rationale: these are existing application contracts; the architectural improvement belongs behind them.
  Date/Author: 2026-07-31 / Codex.
- Decision: Introduce one immutable prepared plan for visible semantics/layout and pass its `SignatureLayoutPlan` into the PyHanko style adapter; do not create a backend registry or multi-backend plugin framework in this slice.
  Rationale: there is one production backend, and a strategy registry would add abstraction without a second implementation. The prepared plan directly addresses preview/signing drift.
  Date/Author: 2026-07-31 / Codex.
- Decision: Implement invisible signing explicitly in the existing PyHanko adapter rather than changing GUI workflow validation.
  Rationale: invisible signing is a headless use-case contract, while the Qt workflow intentionally requires visible placement for its primary user flow.
  Date/Author: 2026-07-31 / Codex.
- Decision: Keep PyHanko/Pillow types inside backend and adapter code; the prepared plan exposes only application/domain data, fit issues, and layout evidence.
  Rationale: true-external dependencies must remain replaceable at the boundary, and callers must not depend on third-party objects.
  Date/Author: 2026-07-31 / Codex.

## Outcomes & Retrospective

Completed 2026-07-31. The constrained hybrid landed as designed: `PreparedSigningPlan` and
`prepare_phase3_signing_plan()` resolve visible semantics/layout once, typed fit issues stay at the
application boundary, and `PyHankoPdfSigner` owns third-party materialization, invisible field
construction, TSA, signing, and verification. `Phase3SigningExecutor.execute(request)` and the
existing use-case facade remain unchanged. Focused prepared/invisible validation passed (5 tests),
Ruff passed, and the full suite passed (1,016 tests; one existing Pillow deprecation warning).
Documentation now records that invisible signing is headless-compatible rather than a new GUI flow.
The post-fix architecture/spec review found no blocking discrepancy; the independent signing-time
snapshot concern is documented as the next fidelity-focused architecture slice.
Implementation commit: `42e4fe3c3` (`Complete prepared signing plan boundary`).

## Context and Orientation

`src/foliaseal/application/sign_pdf_use_case.py` is the application boundary. It normalizes a domain `SigningRequest` into `SigningBackendRequest`, validates PDF/certificate policy, invokes a `PdfSigner`, writes output atomically, verifies the result, and maps exceptions to stable `FailureCode` values.

`src/foliaseal/application/phase3_signing_backend.py` is the concrete PyHanko adapter. It currently loads PKCS#12 material, resolves certificate-derived visible text, checks layout fit, builds a visible stamp, creates an incremental signature field, handles TSA errors, and verifies signed output. Its `PyHankoPdfSigner.sign()` method must remain usable by existing tests and compatibility callers.

`src/foliaseal/application/visible_signature_layout.py` owns the neutral layout planner and can return a `SignatureLayoutPlan` plus fit issues. `src/foliaseal/application/signing_preview_renderer.py` builds canonical preview styles through the same planner. The prepared plan must make this shared result explicit without moving PyHanko rendering into the domain.

The public domain request in `src/foliaseal/domain/models.py` permits either a complete visible pair (`signature_rect` and `signature_appearance`) or both values absent for an invisible signature. A partial pair remains invalid and must continue returning `FailureCode.SIGNATURE_RECT_INVALID`.

## Plan of Work

First, add a focused application/backend prepared-plan type, either in `phase3_signing_backend.py` or a small neighboring application module that does not import Qt. It must contain the normalized backend request, resolved visible semantics when present, the optional `SignatureLayoutPlan`, fit issues, and the resolved stamp text. Invisible plans contain no visible semantics or layout and explicitly identify the invisible mode. Keep third-party PyHanko objects out of the plan.

Add a preparation function used by `PyHankoPdfSigner.sign()` when no prepared plan is supplied. It must preserve current certificate-field resolution, fixed signing-time semantics, rendered-ink fallback checks, fit issue messages, and image-stamp errors. The visible style builder must accept the prepared layout plan so it does not plan a second time. Existing private helpers may remain as compatibility wrappers, but the new public boundary tests must assert behavior through preparation and `execute()` rather than private helper state.

Thread the prepared plan through the concrete signer and style adapter. `Phase3SigningExecutor.execute()` and `SignPdfUseCase.execute()` continue to accept only `SigningRequest`; preparation is an internal optimization and policy boundary. Preview construction must accept or produce the same neutral layout-plan shape and continue honoring canonical single-line stamp suppression and rendered-ink measurement.

Add the invisible branch to `PyHankoPdfSigner.sign()`. Allocate the next signature field as required by the existing incremental-signing behavior, construct `PdfSignatureMetadata` without visible stamp style, use an invisible `SigFieldSpec` with no visible box, preserve TSA setup, write the incremental output, and return the existing `SigningOutput` metadata. Do not alter `SignPdfUseCase` failure mapping except where a typed fit/preparation error is needed to preserve an existing stable failure code.

Add tests at the application/backend boundary. Use existing fixture builders and dummy timestamp/certificate helpers. Cover visible preparation and style-plan reuse, visible fit rejection and message preservation, invisible signing with timestamp disabled and enabled, post-sign verification, invalid certificate/TSA mapping, and two sequential signatures preserving prior revisions. Retain lower-level layout tests that protect the existing fallback ladder until the new boundary proves parity; do not broaden the slice into a Qt workflow refactor.

Update `docs/ARCHITECTURE.md`, `README.md`, and this plan. The architecture document must state that the application prepared-plan boundary owns normalized visible semantics/layout evidence, while the PyHanko adapter owns third-party materialization, invisible field construction, signing, TSA, and verification. Record that Qt callers remain on `SigningRequest` and that invisible signing is headless-compatible rather than a new GUI workflow.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

Baseline:

    git status --short --branch
    .venv/bin/pytest -q tests/unit/test_sign_pdf_use_case.py tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py

After adding the prepared plan and tests:

    .venv/bin/ruff check src/foliaseal/application/sign_pdf_use_case.py src/foliaseal/application/phase3_signing_backend.py src/foliaseal/application/visible_signature_layout.py src/foliaseal/application/signing_preview_renderer.py tests/unit/test_sign_pdf_use_case.py tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py
    .venv/bin/pytest -q tests/unit/test_sign_pdf_use_case.py tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py
    .venv/bin/pytest -q

Run the existing Phase 3 release-fidelity preview and signed-acceptance matrix commands with generated artifacts under `/tmp`, and expect the established eight-scenario contract: preview has zero error rows; signed acceptance has six successful signings, two intentional fit rejections, and zero critical parity/cryptographic/annotation failures.

Finish with:

    git diff --check
    git status --short
    ps -eo pid=,comm=,args= | awk '$2 ~ /python/ && $0 ~ /foliaseal|phase3/ {print}'
    wmctrl -l 2>/dev/null || true

## Validation and Acceptance

The prepared boundary is accepted when visible signing and canonical preview consume equivalent layout-plan data, fit failures remain precise and backward compatible, and no PyHanko/Pillow object is required by callers. Invisible signing is accepted when a valid headless `SigningRequest` with no rectangle or appearance produces a signed output that the existing verifier accepts, including the timestamp-required path. This acceptance evidence is present in the focused tests and full-suite run recorded above.

Compatibility is accepted when `Phase3SigningExecutor.execute()`, `SignPdfUseCase.execute()`, CLI commands, Qt signing actions, `SigningBackendRequest` normalization, and existing serialized evidence remain unchanged. The full test suite, focused backend/use-case tests, release-fidelity matrices, Ruff, diff check, and process/window audit must all pass.

## Idempotence and Recovery

The changes are additive and safe to rerun. Generated PDFs, PNGs, and matrix summaries belong under `/tmp` and must not be committed. If invisible signing fails, first inspect the `SigFieldSpec(box=None)` branch and post-sign verification; do not weaken visible-signature tests. If preview/signing layouts diverge, compare the prepared plan and adapter arguments before changing tolerances. Do not use destructive Git commands.

## Artifacts and Notes

Tracked artifacts are source, tests, README, architecture documentation, and this ExecPlan. Generated evidence remains outside Git. Record focused/full test counts, invisible-signing verification evidence, release-fidelity counters, compliance findings, documentation changes, and the final commit hash (`42e4fe3c3`) in this plan.

## Interfaces and Dependencies

The existing public interfaces remain stable:

    class PdfSigner(Protocol):
        def sign(self, request: SigningBackendRequest) -> SigningOutput: ...

    class Phase3SigningExecutor:
        def execute(self, request: SigningRequest) -> SigningResult: ...

The new internal prepared boundary must be immutable and application-owned. Its equivalent shape is:

    @dataclass(frozen=True)
    class PreparedSigningPlan:
        backend_request: SigningBackendRequest
        visible_semantics: VisibleSignatureSemantics | None
        layout_plan: SignatureLayoutPlan | None
        fit_issues: tuple[SigningDraftValidationIssue, ...]
        stamp_text: str
        visible: bool

The concrete PyHanko signer may accept an optional prepared plan internally, but legacy direct calls without it must continue to work. The invisible branch must use PyHanko's existing `PdfSigner` with no visible stamp style and an invisible signature field specification.

## Revision Note

2026-07-31 / Codex: Created after the architecture exploration and dev-loop explorer selected the constrained prepared-plan plus common-executor hybrid. The slice intentionally excludes a second-backend registry, Qt workflow refactor, and broad removal of compatibility helpers.
