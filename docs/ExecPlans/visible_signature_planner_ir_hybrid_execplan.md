# Deepen the visible-signature planner and adapter boundary

This ExecPlan is a living document. Maintain it in accordance with `.agents/skills/write-execplan/PLANS.md`. The entire change is one compatibility-preserving architecture slice: introduce the planner facade, make preview/workflow/Qt callers use explicit public layout and adapter operations, preserve backend compatibility wrappers, validate parity, update documentation, and commit the result together.

## Purpose / Big Picture

After this slice, visible-signature geometry, fit policy, and adapter preparation will have one application-owned entry point. Canonical preview, signing preparation, draft validation, and Qt preview geometry will stop importing backend-private helpers. A caller will be able to prepare one immutable neutral plan and pass that result to the appropriate signing or preview adapter, so preview and signed output continue to use the same layout evidence.

The user-visible behavior remains unchanged: visible signatures keep their current text, image, border, fit-rejection, and parity behavior; invisible signing remains supported; and Qt/CLI callers keep their existing request/result contracts. The architectural improvement is observable through boundary tests that prove one plan is reused and through an import audit showing no new consumer dependency on backend-private names.

## Child ExecPlan Dependencies

- [x] The current `PreparedSigningPlan` slice is present on `main` and its focused/full validation is green.
- [x] Architecture design exploration compared minimal, flexible, and common-caller interfaces; this plan selects the hybrid neutral-plan plus ergonomic-preparation approach.
- [x] No child plan was required; all compliance findings were corrected within this parent slice.

## Progress

- [x] (2026-07-31) Re-checked the clean checkout and the current prepared-signing implementation.
- [x] (2026-07-31) Completed dev-loop reconnaissance of layout, backend, workflow, canonical preview, Qt preview, harness, and tests.
- [x] (2026-07-31) Confirmed the smallest safe slice: promote explicit layout/adapter operations, rewire consumers, and retain backend wrappers because many existing tests still import them.
- [x] (2026-07-31) Wrote this self-contained one-slice ExecPlan before implementation.
- [x] (2026-07-31) Added `VisibleSignaturePlanner`, neutral-plan reuse, public image/fit/inset operations, and delegating compatibility wrappers.
- [x] (2026-07-31) Rewired canonical preview, workflow validation, and Qt preview geometry to public planner/layout/adapter operations.
- [x] (2026-07-31) Added boundary/import-contract coverage while preserving compatibility tests through wrappers.
- [x] (2026-07-31) Focused planner/layout/backend/preview/workflow/Qt validation passes; direct planner adapter and public image/fit error-contract coverage was added after compliance review.
- [x] (2026-07-31) Full suite passed 1,022 tests with one existing Pillow deprecation warning; Ruff and `git diff --check` passed.
- [x] (2026-07-31) Release-fidelity preview ran 8 scenarios with zero error rows; signed acceptance ran 8 scenarios with 6 successful signings, 2 matched intentional rejections, and zero critical counters.
- [x] (2026-07-31) Completed architecture/SPEC compliance review for this slice and reconciled README/ARCHITECTURE/ExecPlan documentation.
- [x] (2026-07-31) Committed the completed slice as `ddf250473` (`Deepen visible-signature planner boundary`); the follow-up plan metadata commit will record this hash.

## Surprises & Discoveries

- Observation: `VisibleSignaturePlan` and `SignatureLayoutPlan` already form a neutral intermediate representation, but `VisibleSignaturePlanRequest` still carries `SigningBackendAppearance` and consumers bypass the boundary through backend-private imports.
  Evidence: `visible_signature_layout.py` defines `VisibleSignaturePlan` around lines 496-516; `signing_preview_renderer.py`, `signing_draft_workflow.py`, and Qt `signature_preview_layout.py` import private backend names.
- Observation: workflow fit validation currently invokes `_build_stamp_style()` and therefore includes PyHanko construction and rendered-ink fallback; replacing it with a pure geometry check would change stable error behavior.
  Resolution: expose a public fit-validation operation that delegates to the existing adapter/fallback path, then retain the old private helper as a delegating compatibility wrapper.
- Observation: many backend tests directly import private helpers.
  Resolution: do not delete those wrappers in this slice; migrate production consumers first and reserve wrapper removal for a later test-replacement slice.

## Decision Log

- Decision: Keep `SigningRequest`, `SigningResult`, `Phase3SigningExecutor.execute()`, and all Qt/CLI entry points unchanged.
  Rationale: this slice deepens the internal planning seam without expanding the caller contract.
  Date/Author: 2026-07-31 / Codex.
- Decision: Use the existing immutable `VisibleSignaturePlan`/`SignatureLayoutPlan` as the neutral plan instead of introducing a second geometry schema.
  Rationale: duplicating the already-tested intermediate representation would increase migration risk and create another parity surface.
  Date/Author: 2026-07-31 / Codex.
- Decision: Add a small `VisibleSignaturePlanner` facade with neutral planning plus explicit signing/preview preparation methods, while keeping `VisibleSignatureLayoutService` as the concrete adapter implementation.
  Rationale: normal callers get one obvious path, but PyHanko/Pillow objects remain behind adapter methods and existing service behavior remains reusable.
  Date/Author: 2026-07-31 / Codex.
- Decision: Promote backend-private image loading, fit validation, and Qt inset helpers to named public operations; keep private aliases delegating to them.
  Rationale: production callers stop depending on private implementation names without breaking the extensive compatibility tests in the same slice.
  Date/Author: 2026-07-31 / Codex.
- Decision: Do not move the entire `RoundedBorderTextStampStyle` implementation or remove every compatibility helper in this slice.
  Rationale: that would mix a backend relocation with the planner boundary and make the one-slice change wider than its testable objective.
  Date/Author: 2026-07-31 / Codex.

## Outcomes & Retrospective

Implementation is complete for the planner/IR hybrid slice. The focused boundary/layout/backend/preview/workflow/Qt command passes 245 tests, the full suite passes 1,022 tests with one existing Pillow deprecation warning, and Ruff plus `git diff --check` are clean. The neutral `VisibleSignaturePlan`/`SignatureLayoutPlan` remains application-owned; PyHanko/Pillow materialization is explicit in planner adapter methods, and public image/fit/inset operations preserve existing errors and geometry. The preview matrix covers 8 scenarios with zero errors; signed acceptance covers 6 successful signings and 2 matched intentional rejections with all critical counters zero. README and ARCHITECTURE now document ownership, contracts, and the intentional Qt presentation-measurement distinction. Remaining debt is the compatibility layer: backend-private aliases, late-imported measurement helpers, and concrete fit/rejection helpers stay in place until direct legacy-helper coverage can be replaced by boundary coverage. Post-fix architecture/SPEC review found no blocking discrepancy. The final commit hash is recorded after the commit pass.

## Context and Orientation

`src/foliaseal/application/visible_signature_layout.py` owns the shared visible-signature geometry policy. `VisibleSignatureLayoutBoundary.plan()` produces a typed `VisibleSignaturePlan`, whose `layout_plan` contains point-space geometry, image metrics, text layout rules, rendered-ink reservation evidence, and typed fit issues. `VisibleSignatureLayoutService` converts that neutral result into PyHanko signing or canonical-preview adapter bundles.

`src/foliaseal/application/phase3_signing_backend.py` is the concrete PyHanko adapter. It currently owns signing, rendered-fit fallback, image loading, and compatibility wrappers. `PreparedSigningPlan` already lets final signing reuse one prepared layout, but the workflow and preview renderer still reach backend-private helpers.

`src/foliaseal/application/signing_preview_renderer.py` builds deterministic textual previews and canonical raster previews. Its canonical path currently plans through the layout boundary but imports the backend-private image loader and rounded stamp style. `src/foliaseal/application/signing_draft_workflow.py` resolves draft semantics and asks a private backend fit validator to preserve current issue mapping. `src/foliaseal/presentation/qt/signature_preview_layout.py` computes widget-facing geometry and imports three backend-private inset helpers even though their policy implementations live in the layout module.

The true external dependencies are PyHanko, Pillow, Qt, and PDF rasterization. They must remain behind adapter/composition code. Geometry, fit decisions, and plan evidence are in-process computations. Text measurement, image probing, and rendered-ink measurement use local substitutes in tests.

## Plan of Work

First, deepen `visible_signature_layout.py` without creating a second geometry model. Add an application-owned `VisibleSignaturePlanner` that exposes a neutral `plan(VisibleSignaturePlanRequest) -> VisibleSignaturePlan` operation and explicit adapter preparation methods that accept an optional precomputed plan and delegate to the existing `VisibleSignatureLayoutService`. Add stable public layout operations for the three Qt inset policies and for stamp-background loading/fit validation where the operation is adapter-owned. Preserve the existing `VisibleSignaturePlan` and `SignatureLayoutPlan` fields so evidence and downstream adapters remain compatible.

Next, update `phase3_signing_backend.py` to use the planner facade for prepared visible signing and to expose named public adapter operations for image loading and fit validation. Leave the old underscored functions as thin delegating wrappers. The public fit operation must preserve the current rendered-ink fallback, PyHanko style construction, exception-to-`SigningDraftValidationIssue` mapping, and exact error messages. The existing `PreparedSigningPlan` remains the signing-side immutable bundle; no PyHanko or Pillow object may be added to it.

Then, rewire `signing_preview_renderer.py` to obtain its canonical plan and style through the planner/service public boundary. Replace direct backend-private imports. Preserve the optional precomputed `layout_plan`, preview-only text/stamp/border suppression, flattening behavior, and the use of a borderless `TextStampStyle` for optional bounds when no rounded border is needed. Rewire `signing_draft_workflow.py` to call the public fit/image operations while preserving certificate-preview availability behavior and stable validation issue codes. Rewire `signature_preview_layout.py` to import only public layout inset operations; its Qt geometry remains a presentation adapter and must not import the signing backend.

Add boundary tests that prove the planner returns the same layout evidence for preview and signing inputs, that supplied plans are consumed without a second planning pass, that public fit validation preserves current messages and severity, that image-load errors remain stable, and that Qt geometry no longer imports backend-private helpers. Retain existing backend helper tests through the compatibility wrappers. Add an import-contract test or static assertion over the production modules so future code cannot silently reintroduce the private imports removed by this slice.

Finally, update `README.md` and `docs/ARCHITECTURE.md` using the architecture-steward guidance. Document the planner as the application-owned neutral boundary, the service/adapters as the PyHanko/Qt/Pillow materialization boundary, the unchanged public signing contract, and the compatibility-wrapper retirement debt. Update this plan with validation evidence, run the compliance review, correct any discrepancies through a child plan if necessary, and commit the complete slice.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

Baseline and focused checks:

    git status --short --branch
    .venv/bin/pytest -q tests/unit/test_visible_signature_layout.py tests/unit/test_visible_signature_layout_boundary.py tests/unit/test_signing_preview_renderer.py tests/unit/test_signing_draft_workflow.py tests/unit/test_signature_preview_layout.py tests/unit/test_phase3_signing_backend.py

After implementation:

    .venv/bin/ruff check src/foliaseal/application/visible_signature_layout.py src/foliaseal/application/phase3_signing_backend.py src/foliaseal/application/signing_preview_renderer.py src/foliaseal/application/signing_draft_workflow.py src/foliaseal/presentation/qt/signature_preview_layout.py tests/unit/test_visible_signature_layout.py tests/unit/test_visible_signature_layout_boundary.py tests/unit/test_signing_preview_renderer.py tests/unit/test_signing_draft_workflow.py tests/unit/test_signature_preview_layout.py tests/unit/test_phase3_signing_backend.py
    .venv/bin/pytest -q tests/unit/test_visible_signature_layout.py tests/unit/test_visible_signature_layout_boundary.py tests/unit/test_signing_preview_renderer.py tests/unit/test_signing_draft_workflow.py tests/unit/test_signature_preview_layout.py tests/unit/test_phase3_signing_backend.py
    .venv/bin/pytest -q

Run the existing Phase 3 preview and signed-acceptance matrix commands with generated artifacts under `/tmp`. Expect eight preview scenarios with zero error rows, six successful signed scenarios, two intentional fit rejections, and zero critical parity, cryptographic, or annotation counters.

Finish with:

    git diff --check
    git status --short
    ps -eo pid=,comm=,args= | awk '$2 ~ /python/ && $0 ~ /foliaseal|phase3/ {print}'
    wmctrl -l 2>/dev/null || true

## Validation and Acceptance

The slice is accepted when all visible-signature production callers use the public planner/layout/adapter boundary rather than backend-private imports, while compatibility wrappers remain available for existing tests. A prepared plan supplied to signing is consumed without recomputing layout. Canonical preview and visible signing continue to produce matching layout evidence, fit issue codes/messages, image behavior, and rendered output. Qt preview geometry remains numerically unchanged.

The existing signing, invisible-signing, TSA, incremental-signing, certificate, CLI, and Qt contracts must remain green. Focused tests, Ruff, the full suite, both release-fidelity matrices, the diff check, and the process/window audit are required evidence. No generated PDF/image artifacts may be committed.

## Idempotence and Recovery

The changes are additive and safe to rerun. Keep generated evidence under `/tmp`. If a preview parity test fails, compare the supplied `SignatureLayoutPlan` and adapter options before changing geometry policy. If workflow fit messages change, route validation back through the public adapter operation rather than weakening the expected issue mapping. If a broad helper move causes import cycles, revert only that move and retain the public delegating facade; do not delete compatibility wrappers. Never use destructive Git commands.

## Artifacts and Notes

Tracked artifacts are the planner/layout source, backend and preview rewires, focused tests, README, architecture documentation, and this ExecPlan. Generated matrix output stays outside Git. Record concise test transcripts, import-audit evidence, compliance findings, and the final commit hash here.

## Interfaces and Dependencies

The intended application-owned facade is:

    class VisibleSignaturePlanner:
        def plan(self, request: VisibleSignaturePlanRequest) -> VisibleSignaturePlan: ...
        def prepare_signing_style(
            self,
            *,
            appearance: SigningBackendAppearance,
            stamp_text: str,
            stamp_background: object | None,
            signature_rect: SignatureRect,
            layout_plan: SignatureLayoutPlan | None = None,
            options: VisibleSignatureLayoutOptions | None = None,
        ) -> PyHankoVisibleSignatureStyle: ...
        def prepare_preview_style(
            self,
            *,
            appearance: SigningBackendAppearance,
            stamp_text: str,
            stamp_background: object | None,
            signature_rect: SignatureRect,
            layout_plan: SignatureLayoutPlan | None = None,
            options: VisibleSignatureLayoutOptions | None = None,
        ) -> CanonicalPreviewLayout: ...

The exact placement may remain in `visible_signature_layout.py` if that avoids a needless module split. The planner must return only application/domain data in its neutral result. PyHanko/Pillow objects are allowed only in the explicit adapter result methods. Public image/fit operations must retain stable `ValueError` and `SigningDraftValidationIssue` behavior. Existing private names remain compatibility wrappers until a later slice replaces their direct tests with boundary tests.

## Revision Note

2026-07-31 / Codex: Created after architecture exploration selected the planner/IR plus common-caller hybrid. The scope deliberately removes consumer-private imports and centralizes plan reuse without attempting a risky wholesale relocation of every PyHanko helper.
2026-07-31 / Codex: Completed the implementation/documentation slice. Focused validation: 245 passed. Compatibility wrappers remain by design; full/release-fidelity evidence and commit recording are parent-owned follow-up steps.
2026-07-31 / Codex: Completed the implementation/documentation slice and post-fix compliance review. Full validation and both release-fidelity matrices are now recorded; compatibility wrappers remain by design until a later boundary-test retirement slice. Implementation commit: `ddf250473`.
