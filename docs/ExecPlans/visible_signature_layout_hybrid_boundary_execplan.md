# Deepen the visible-signature layout boundary

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date during the implementation. Maintain it in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

FoliaSeal currently computes visible-signature geometry in `visible_signature_layout.py`, but the signing backend and preview renderer still reach through compatibility wrappers and a reverse import into backend-private helpers. After this slice, preview and final PDF signing will request one neutral, reusable layout plan from a single boundary. PyHanko-specific stamp construction will remain an adapter concern, and rendered-ink measurement will remain an injected local adapter. A user will observe no intentional visual change; the demonstrable improvement is that the same layout plan drives preview and signing, backend-private layout helpers are no longer production dependencies, and boundary tests cover the behavior without a live Qt window.

## Child ExecPlan Dependencies

- [x] The architecture exploration identified the hybrid direction: a neutral one-call planner, an internal single resolution pass, optional measurement diagnostics, and PyHanko-specific style construction outside the neutral result.
- [x] The required dev-loop explorer report was reviewed. It confirmed the current `VisibleSignatureLayoutService`, backend wrapper chain, and reverse dependency from `horizontal_signature_reservation.py` to `_text_style_color_rgba`.
- [x] No child ExecPlans are required. This slice intentionally contains the complete planner contract, adapter migration, test migration, documentation review, and commit.

## Progress

- [x] (2026-07-29) Reviewed the architecture candidate and selected the hybrid neutral-planner/adapter direction.
- [x] (2026-07-29) Fresh explorer context reviewed: production callers are `phase3_signing_backend.py` and `signing_preview_renderer.py`; compatibility wrappers remain in the backend; horizontal reservation imports a neutral color helper instead of backend-private RGBA conversion.
- [x] (2026-07-29) Wrote this one-slice ExecPlan before implementation.
- [x] (2026-07-29) Added `VisibleSignaturePlanRequest`, `VisibleSignaturePlan`, and `VisibleSignatureLayoutBoundary.plan()`; the existing service now accepts a precomputed plan for adapter construction.
- [x] (2026-07-29) Moved text-color conversion to `visible_signature_color.py`; horizontal reservation no longer imports `phase3_signing_backend` for that helper.
- [x] (2026-07-29) Migrated backend stamp construction, reservation evidence, and canonical preview construction to the neutral planner while retaining compatibility wrappers for legacy helper callers.
- [x] (2026-07-29) Added boundary tests for one-pass planning, fit diagnostics, signing and canonical-preview plan reuse, stamp inclusion, the neutral/no-PyHanko result contract, and the reverse color-helper dependency.
- [x] (2026-07-29) Replaced four duplicated backend-private background-inset tests with public adapter contract coverage across the supported stamp-position families; retained backend-private tests only for compatibility and rendered-ink fit behavior.
- [x] (2026-07-29) Updated README.md and docs/ARCHITECTURE.md to document the neutral planner boundary, PyHanko adapter split, reverse-dependency removal, and compatibility-shim status.
- [x] (2026-07-29) Independent compliance review completed; the first review failed on missing canonical-preview/reverse-dependency tests and duplicated private-helper coverage, and the required fixes were applied.
- [x] (2026-07-29) Focused suite passed: 211 tests. Full suite passed: 986 tests with one pre-existing Pillow deprecation warning.
- [x] (2026-07-29) Release-fidelity preview matrix passed for 8 scenarios; signed acceptance matrix passed with 6 successful signings, 2 intentional fit rejections, zero cryptographic/preview-output/annotation mismatches, and `acceptance_expectations_passed=true`.
- [x] (2026-07-29) Committed the completed slice and verified the final commit via `git log -1`, with a clean worktree and no FoliaSeal/Qt processes or windows remaining.

## Surprises & Discoveries

- Observation: `VisibleSignatureLayoutService` already exposes separate signing and canonical-preview adapter methods, so the change can be additive and low-risk rather than a renderer rewrite.
  Evidence: `pyhanko_style_for_signing()` and `pyhanko_style_for_canonical_preview()` both construct a `SignatureLayoutPlan` in `src/foliaseal/application/visible_signature_layout.py`.
- Observation: `horizontal_signature_reservation.py` now imports the neutral `visible_signature_color.py` helper, while `phase3_signing_backend.py` still keeps `_text_style_color_rgba` as a delegating compatibility shim.
  Evidence: the import inside `measure_horizontal_single_line_rendered_reference()` now targets `visible_signature_color.text_style_color_rgba`, and the backend helper forwards to that same utility.
- Observation: the backend reservation evidence path now carries a neutral planner snapshot alongside adapter-derived reservation data.
  Evidence: `build_backend_reservation_evidence()` adds `neutral_plan` from `VisibleSignatureLayoutBoundary().plan(...)`.
- Observation: the current test suite includes boundary coverage for the new layout seam and still patches some backend-private helpers for compatibility.
  Evidence: `tests/unit/test_visible_signature_layout_boundary.py` covers plan/result reuse and reverse-dependency removal; `tests/unit/test_phase3_signing_backend.py` still contains direct calls to `_layout_reservation_for_template`, `_build_stamp_style`, and rendered-ink fit helpers.
- Observation: the independent compliance review initially rejected the slice because boundary tests did not explicitly cover canonical-preview plan reuse, the reverse color-helper dependency, or public replacement of duplicated inset tests.
  Evidence: the follow-up boundary suite now has those tests, and the four duplicated backend inset tests were removed from `tests/unit/test_phase3_signing_backend.py`.
- Observation: the full release-fidelity matrices emit existing pyHanko content-box and offscreen Qt warnings while returning successful summaries and exit code 0.
  Evidence: `/tmp/foliaseal-layout-hybrid-preview/summary.json` and `/tmp/foliaseal-layout-hybrid-signed/summary.json` report the expected scenario counts and zero critical counters.

## Decision Log

- Decision: Use a neutral planner request/result as the production contract, keep PyHanko style construction in the existing adapter, and make measurement tracing optional rather than introducing a session object.
  Rationale: this combines the common-caller simplicity of the recommended design with the single-pass resolution of the minimal design while avoiding PyHanko leakage and unnecessary lifecycle surface.
  Date/Author: 2026-07-29 / Codex.
- Decision: Keep backend-private wrapper names temporarily as compatibility shims, but ensure production signing, preview, and reservation-evidence paths call the neutral boundary directly.
  Rationale: existing evidence and focused tests still exercise those names; deleting them in the same change would mix a broad test rewrite with the architectural move and increase visual-regression risk.
  Date/Author: 2026-07-29 / Codex.
- Decision: Treat `visible_signature_color.py` as the shared neutral helper for RGBA conversion, and keep `_text_style_color_rgba` only as a delegating compatibility wrapper.
  Rationale: this removes the reverse dependency without forcing a larger backend API change.
  Date/Author: 2026-07-29 / Codex.
- Decision: Treat this as one behavior/refactor slice. Generated PDFs, PNGs, and `/tmp` matrix outputs are evidence only and must not be committed.
  Rationale: the observable behavior is preview/signing parity, while documentation and plan updates are required closeout work rather than separate product changes.
  Date/Author: 2026-07-29 / Codex.
- Decision: Keep the remaining backend-private helper tests that exercise compatibility shims or rendered-ink fallback ladders, but move duplicated layout-inset assertions to the public service contract.
  Rationale: deleting all backend tests would erase coverage for backend-specific fallback behavior; replacing the four duplicated inset tests proves the boundary migration without broadening this slice into a full test-file rewrite.
  Date/Author: 2026-07-29 / Codex.

## Outcomes & Retrospective

Final boundary: `VisibleSignatureLayoutBoundary.plan(VisibleSignaturePlanRequest)` returns a PyHanko-free `VisibleSignaturePlan`; `VisibleSignatureLayoutService` converts the plan into signing or canonical-preview PyHanko styles. Production callers migrated are `phase3_signing_backend.py` (stamp style and reservation evidence) and `signing_preview_renderer.py` (canonical preview). The horizontal reservation path now depends on `visible_signature_color.py` rather than a backend-private helper.

Focused validation passed with 211 tests; the full suite passed with 986 tests and one pre-existing Pillow deprecation warning. The preview matrix passed all 8 scenarios. The signed acceptance matrix passed 6 successful signings and 2 intentional fit rejections, with zero expected-outcome, cryptographic, preview/output, or annotation-rectangle failures and `acceptance_expectations_passed=true`. Representative preview and signed-output comparison images were inspected from `/tmp/foliaseal-layout-hybrid-preview` and `/tmp/foliaseal-layout-hybrid-signed`.

The independent compliance review initially failed on missing explicit canonical-preview/reverse-dependency tests and duplicated private-helper coverage; those findings were fixed by adding the missing boundary tests and replacing four low-level inset tests with public adapter coverage. README and `docs/ARCHITECTURE.md` now document the neutral planner, adapter split, evidence snapshot, and compatibility shims. The final commit hash is verified by `git log -1`, and the final worktree/process check is clean. Remaining compatibility wrappers (`_build_stamp_style`, `_layout_reservation_for_template`, `_background_layout_for_stamp`, `_text_style_color_rgba`, and related fit helpers) should be removed only after downstream callers and compatibility tests migrate to the neutral boundary.

## Context and Orientation

`src/foliaseal/application/visible_signature_layout.py` is the application-layer geometry policy. `VisibleSignatureLayoutEngine.plan()` measures text and images, reserves stamp/text regions, applies horizontal rendered-ink reservation when available, and returns `SignatureLayoutPlan` with fit issues. `VisibleSignatureLayoutBoundary.plan()` wraps that engine in a neutral result object with a JSON-ready reservation snapshot, and `VisibleSignatureLayoutService` remains the adapter/composition root for PyHanko style construction.

`src/foliaseal/application/phase3_signing_backend.py` owns certificate loading, visible-signature semantics, PyHanko signing, verification, and compatibility wrappers around layout helpers. `src/foliaseal/application/signing_preview_renderer.py` builds the canonical preview and now requests the neutral plan before asking the layout service for a PyHanko-style preview. `src/foliaseal/application/horizontal_signature_reservation.py` measures rendered text ink in a roomy canonical preview and now imports the neutral color helper instead of a backend-private one.

The term “neutral planner” means a function that returns geometry, layout rules, image metrics, and fit diagnostics without returning a PyHanko object. An “adapter” is the code that converts that neutral plan into a library-specific object, such as a PyHanko `TextStampStyle`. A “compatibility shim” is a retained old helper name that delegates to the new boundary while callers migrate.

## Plan of Work

First add a `VisibleSignaturePlanRequest` and `VisibleSignaturePlan` to `src/foliaseal/application/visible_signature_layout.py`. The request must contain the `SigningBackendAppearance`, `SignatureRect`, stamp text, whether the stamp is included, whether horizontal ink reservation is enabled, and optional injected text/image/ink adapters. The result must contain the `SignatureLayoutPlan`, its fit issues, and a JSON-ready neutral reservation snapshot sufficient for evidence callers; it must not contain a PyHanko `TextStampStyle`.

Add `VisibleSignatureLayoutBoundary.plan(request)` as the one common production entry point. It must build `LayoutRequest` exactly once, delegate to `VisibleSignatureLayoutEngine.plan()`, and expose an optional diagnostic measurement trace without making tracing part of the normal caller path. The existing `VisibleSignatureLayoutService` remains the adapter/composition root: its signing and canonical-preview methods accept an already-computed plan so they do not silently recompute policy. Preserve the existing public `SignatureLayoutPlan`, `VisibleSignatureFitIssue`, `VisibleSignatureLayoutOptions`, and adapter result types unless a compatibility-preserving alias is required.

Move the color conversion helper used by rendered-ink measurement to the neutral layout module or a small layout-owned utility in the application layer. Update `horizontal_signature_reservation.py` to import that neutral helper and remove its import of `phase3_signing_backend`. Leave the backend helper as a delegating compatibility shim if existing tests require the name.

Update `phase3_signing_backend.py` so `_build_stamp_style()` obtains a plan from `VisibleSignatureLayoutBoundary`, performs the existing rendered-ink fallback decision against that plan, and passes the accepted plan into `VisibleSignatureLayoutService.pyhanko_style_for_signing()`. Update `build_backend_reservation_evidence()` and any production fit-gate path to use the same boundary result. Keep signing semantics, certificate loading, timestamping, failure codes, and PyHanko field placement unchanged.

Update `signing_preview_renderer.py` so `_canonical_preview_layout()` obtains the same neutral plan for the same appearance, rectangle, stamp text, and options, then passes it into the canonical-preview adapter. Preserve stamp suppression behavior and all preview snapshot fields. Update the backend and preview horizontal-ink measurers to use the neutral color helper and the existing reservation port.

Add boundary tests in `tests/unit/test_visible_signature_layout.py` or a new `tests/unit/test_visible_signature_layout_boundary.py` covering: one plan is produced for each supported template/position family; fit errors retain their existing codes/messages; missing or invalid image stamps use existing diagnostics; a supplied fake ink measurer is used; signing and canonical-preview adapter calls consume the same plan; and the neutral result contains no PyHanko style. Add a regression test proving importing and using `horizontal_signature_reservation.py` does not require `phase3_signing_backend` to provide `_text_style_color_rgba`.

Migrate the highest-value private-helper tests to boundary assertions: reservation and fit behavior should assert the planner result, while low-level compatibility-shim tests should be limited to delegation. Do not delete a test until an equivalent boundary assertion covers the observable behavior. Keep the rest of the suite unchanged unless a failing test demonstrates a stale private import that is directly caused by this slice.

After implementation, run the focused layout/backend/preview tests, then the full repository suite. Run the canonical release fidelity preview and signed matrices if the full suite is green; their summaries must continue to report eight scenarios, six successful signings, two intentional fit rejections, and zero critical counters. Inspect one representative preview/output pair and verify no FoliaSeal or Qt process/window remains.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

    .venv/bin/python -m pytest -q tests/unit/test_visible_signature_layout.py tests/unit/test_horizontal_signature_reservation.py tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py
    .venv/bin/python -m pytest -q
    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-preview-matrix --pdf-path artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf --certificate-path artifacts/generated_acceptance_assets/signed_acceptance_identity.p12 --passphrase secret --scenario-manifest-path tests/fixtures/phase3/release_fidelity_manifest.json --artifacts-dir /tmp/foliaseal-layout-hybrid-preview
    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-acceptance-matrix --pdf-path artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf --certificate-path artifacts/generated_acceptance_assets/signed_acceptance_identity.p12 --passphrase secret --scenario-manifest-path tests/fixtures/phase3/release_fidelity_manifest.json --artifacts-dir /tmp/foliaseal-layout-hybrid-signed
    git diff --check

Expected focused and full suites are green. The signed matrix must report `acceptance_expectations_passed=true`, six matched successful scenarios, two matched intentional validation rejections, and zero expected-outcome, cryptographic, preview/output, and annotation-rectangle failures. Offscreen Qt warnings are non-blocking only when the summary and exit code are successful.

## Validation and Acceptance

Acceptance is behavioral. A canonical preview generated from a supported appearance must use the same plan dimensions, fit decision, text/stamp placement, and border/background rules as the subsequently signed PDF. An intentionally too-small layout must still be rejected with the existing actionable fit diagnostic before signing. The release fidelity matrix must remain green, and all existing signing, timestamp, certification, and GUI-fake tests must pass.

The architecture acceptance check is that production callers no longer import or call backend-private layout policy helpers, `horizontal_signature_reservation.py` no longer imports `phase3_signing_backend.py`, and the neutral planner result contains no PyHanko-specific object. Compatibility shims may remain only when they delegate to the boundary and are covered by a focused delegation test.

## Idempotence and Recovery

The refactor is additive until callers and tests pass. Re-running focused tests and matrix commands is safe; always use the named `/tmp/foliaseal-layout-hybrid-*` directories and do not add generated files to Git. If a migration causes a layout mismatch, preserve the failing test/artifact, compare the old and new `SignatureLayoutPlan`, and restore the caller to the adapter path while correcting the planner rather than weakening fit checks. Do not use destructive Git commands. Before handoff, close any application launched for validation and confirm the worktree is clean after the commit.

## Artifacts and Notes

The tracked artifacts for this slice are the ExecPlan, source/test changes, and documentation updates. Generated matrix summaries and images remain outside Git at:

    /tmp/foliaseal-layout-hybrid-preview/summary.json
    /tmp/foliaseal-layout-hybrid-signed/summary.json

Record the final manifest digest only if the manifest changes; this slice must not change the release corpus. Record representative image paths and the final test transcript in the plan before completion.

## Interfaces and Dependencies

In `src/foliaseal/application/visible_signature_layout.py`, define stable neutral types equivalent to:

    @dataclass(frozen=True)
    class VisibleSignaturePlanRequest:
        appearance: SigningBackendAppearance
        signature_rect: SignatureRect
        stamp_text: str
        include_stamp: bool = True
        use_horizontal_ink_reservation: bool = True
        text_measurer: TextMeasurer | None = None
        image_probe: StampImageProbe | None = None
        ink_measurer: HorizontalInkMeasurer | None = None

    @dataclass(frozen=True)
    class VisibleSignaturePlan:
        layout_plan: SignatureLayoutPlan
        fit_issues: tuple[VisibleSignatureFitIssue, ...]
        reservation_snapshot: dict[str, object]

    class VisibleSignatureLayoutBoundary:
        def plan(self, request: VisibleSignaturePlanRequest) -> VisibleSignaturePlan: ...

The boundary must remain independent of PyHanko style objects. `VisibleSignatureLayoutService.pyhanko_style_for_signing()` and `.pyhanko_style_for_canonical_preview()` remain the adapter methods and must accept an optional precomputed `SignatureLayoutPlan` so the policy is not recomputed. `TextMeasurer`, `StampImageProbe`, and `HorizontalInkMeasurer` remain local test-substitutable ports. PyHanko, Pillow, Qt preview rendering, and text-raster analysis stay behind those adapters; no network service or new dependency is permitted.

Revision note: 2026-07-29 / Codex
Created this one-slice ExecPlan from the hybrid architecture recommendation. It deliberately includes the complete neutral boundary, adapter migration, reverse-dependency removal, test migration, compliance review, documentation, and commit rather than splitting implementation into follow-on plans.
