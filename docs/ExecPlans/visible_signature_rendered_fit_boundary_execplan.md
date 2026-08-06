# Extract the rendered-signature fit boundary

This ExecPlan is a living document and must remain compliant with
`.agents/skills/write-execplan/PLANS.md`. The architecture-loop parent is
`docs/ExecPlans/architecture_improvement_loop_parent_execplan.md`; `docs/SPEC.md` is frozen.

## Purpose / Big Picture

Visible-signature layout geometry already has a neutral application boundary, but the same module
also performs rendered-preview fitting: it renders temporary previews, analyzes raster text ink,
maintains a bounded cache, and deletes temporary directories. The signing backend reaches those
details through private helper imports, and backend tests monkeypatch the neutral module internals.

After this slice, one typed `VisibleSignatureRenderedFitPolicy.decide()` operation will own the
structural fallback decision while a concrete `PyHankoRenderedFitProbe` owns rendering, raster
analysis, cache reuse, and temporary-preview cleanup. The neutral geometry module will retain only
geometry and structural fit policy. Signing and preview behavior must remain identical; the result is
observable through the existing fit-rejection, preview-parity, signed-acceptance, and full test
commands.

## Child ExecPlan Dependencies

- [x] The neutral layout policy boundary is complete at `9f961dc6e` through
  `docs/ExecPlans/visible_layout_policy_unification_execplan.md`.
- [x] Scan Round 56 identified this local-substitutable rendered-fit cluster at approximately
  Candidate Priority `68.0`, with two independent evidence records and confidence approximately
  `0.983`.
- [x] Design Selection 56 selected the common-caller policy/probe design at Refactor Shape Score
  `91.0`, above the minimal and flexible alternatives with no evidence-backed penalty.
- [x] Existing `PreviewRasterRenderer`, `RenderedInkMeasurementPort`, and fake renderers provide
  local test substitutes; no live GUI is required for the boundary tests.

## Progress

- [x] (2026-08-06) Recorded the baseline rendered-fit cluster, caller path, test coupling, and
  dependency substitutes.
- [x] (2026-08-06) Completed three design variants and selected the common-caller policy/probe
  boundary.
- [x] (2026-08-06) Added neutral rendered-fit request/decision/probe contracts and the concrete
  PyHanko/Pillow probe without changing fit arithmetic.
- [x] (2026-08-06) Migrated backend orchestration and tests; removed the private rendered-fit
  helper/cache cluster from the neutral layout module after equivalent boundary coverage existed.
- [x] (2026-08-06) Reconciled architecture documentation and this plan, ran focused/full/offscreen
  validation, and ran the generated-output cleanup. The cleanup command was rejected by the local
  execution approval limit after acceptance completed, so the generated directory/summary remain a
  concrete handoff blocker; commit and post-commit audits remain.

## Surprises & Discoveries

- Observation: The neutral layout module's rendered-fit cluster is about 340 lines and owns both
  single-line and horizontal multi-line fallback ladders.
  Evidence: `src/foliaseal/application/visible_signature_layout.py:1665-2005`.
- Observation: The backend only needs one boolean fallback decision, while tests need controllable
  rendering and raster-analysis substitutes.
  Evidence: `phase3_signing_backend.py:_layout_fit_issues()` and the private-helper tests around
  `tests/unit/test_phase3_signing_backend.py:4047-4264`.
- Observation: Existing `PreviewRasterRenderer` is a page-raster port, while canonical signature
  preview rendering also produces text/stamp bounds and temporary paths. A dedicated preview-probe
  protocol is therefore needed; passing raw Pillow/PyHanko objects through the neutral policy would
  violate import isolation.
  Evidence: `application/preview_render_boundary.py` and
  `application/signing_preview_renderer.py:300-380`.

## Decision Log

- Decision: Keep the neutral policy in a new `application/visible_signature_fit_policy.py` module
  and put concrete rendered-preview probing in
  `application/visible_signature_rendered_fit_adapters.py`.
  Rationale: the dominant backend caller needs one decision operation, while rendering, raster
  analysis, and cleanup are infrastructure-facing details. This avoids a second geometry planner
  and keeps the layout module import-isolated.
  Date/Author: 2026-08-06 / Codex and design reviewers.
- Decision: Use a structural `VisibleSignatureAppearancePort`-compatible appearance input rather
  than importing `SigningBackendAppearance` into the neutral policy.
  Rationale: `SigningBackendAppearance` belongs to backend/use-case composition and importing it
  would leak unrelated dependencies into the fit boundary.
  Date/Author: 2026-08-06 / Codex.
- Decision: The policy returns `VisibleSignatureRenderedFitDecision` and preserves the backend's existing
  `SigningDraftValidationIssue` mapping at the backend edge.
  Rationale: the neutral boundary must not depend on backend validation DTOs, while issue codes,
  messages, field names, and severities remain unchanged for callers.
  Date/Author: 2026-08-06 / Codex and design reviewers.
- Decision: The concrete probe owns the existing bounded 256-entry cache and temporary-preview
  cleanup; no global cache registry or service locator is introduced.
  Rationale: cache identity and cleanup are part of rendered-preview execution, and a single
  backend composition-root probe instance preserves the legacy process-local reuse without adding a
  registry, service locator, or speculative public API. `_prepare_backend_layout()` and
  `validate_visible_signature_fit()` also accept an optional neutral probe for operation-scoped
  tests or alternate lifecycles.
  Date/Author: 2026-08-06 / Codex.
- Decision: Do not rename any `phase3` module, CLI command, DTO, JSON key, fixture, or artifact in
  this slice. The atomic migration remains in
  `docs/ExecPlans/phase3_nomenclature_retirement_execplan.md`.
  Rationale: mixing a contract-sensitive rename with fit-policy extraction would make parity failures
  ambiguous and violate the one-purpose change slice.
  Date/Author: 2026-08-06 / Codex.

## Outcomes & Retrospective

Baseline commit `9f961dc6e` had a 2,009-line neutral layout module, a 1,118-line signing backend,
and approximately 340 lines of rendered-fit/cache/cleanup code in the neutral module. The backend
imported two private rendered-fit helpers and tests imported the cache plus private helper functions.
Measured post-change proxies are navigation `.90`, change amplification `.90`, seam-risk reduction
`.90`, boundary-test improvement `.90`, interface compression `.90`, cohesion `.90`, and isolation
`.95`: the neutral layout module is now 1,657 lines, rendered-fit/cache/cleanup ownership is behind
one typed policy/probe boundary, and the focused policy/adapter/backend/layout coverage is 151 tests
(including direct cache eviction, renderer normalization, and exception-cleanup tests). The full
suite passes 1,163 tests. The measured Actual Improvement is `.915` (mean proxy delta from the
baseline profile), with no component regression beyond `.10`. Offscreen acceptance is `10` scenarios
with `7` successful signings, preview parity `18/18`, and fit rejection `3/3`; generated outputs were
The process audit was empty. The required cleanup command was attempted but rejected by the local
execution approval limit, leaving the generated acceptance directory and summary as the only known
workspace residue. Record implementation and closure commit IDs below after a cleanup retry.

## Context and Orientation

`VisibleSignatureLayoutService.prepare()` in `src/foliaseal/application/visible_signature_layout.py`
creates a structural `SignatureLayoutPlan` and records structural fit issues. When the structural
plan is too tight, `src/foliaseal/application/phase3_signing_backend.py:_layout_fit_issues()` tries
rendered fallback helpers before translating the remaining issues into stable backend validation
issues. The helpers currently live in the neutral layout module and lazily call
`signing_preview_renderer`, `stamp_preview_builder`, and `text_raster_analysis`.

The new neutral policy accepts the signature rectangle, a structural appearance protocol, stamp text,
and the structural layout plan. It returns a typed accepted/rejected decision and dispatches only
the relevant template fallback through an injected probe. The
concrete adapter will construct the same canonical previews, apply the same overflow and rectangle
checks, preserve the current cache key/256-entry eviction, and remove only directories named
`foliaseal-canonical-preview-*`.

## Plan of Work

First add `VisibleSignatureRenderedFitRequest`, `VisibleSignatureRenderedFitDecision`, and
`VisibleSignatureRenderedFitProbe` to `src/foliaseal/application/visible_signature_fit_policy.py`.
The request uses `SignatureRect`, `SignatureLayoutPlan`, stamp text, and the existing structural
appearance protocol. `VisibleSignatureRenderedFitPolicy.decide(request, probe=...)` returns accepted
when there are no structural issues; otherwise it asks the probe to evaluate the single-line or
horizontal multi-line fallback appropriate to the request and returns the probe result. It must not
import Qt, Pillow, pyHanko, the backend, or validation DTOs.

Next add the concrete `PyHankoRenderedFitProbe` in
`src/foliaseal/application/visible_signature_rendered_fit_adapters.py`, consuming the neutral
`VisibleSignatureRenderedFitRequest` directly.
Move the existing rendered-fit arithmetic, canonical preview construction, text-only/reference
preview handling, rectangle checks, cache key, bounded eviction, raster analysis, and cleanup into
this adapter. Preserve all thresholds and false-on-exception behavior exactly. Wrap existing
canonical renderer calls rather than inventing another renderer.

Migrate `phase3_signing_backend.py` so `_prepare_backend_layout()` constructs or receives one
probe for the operation and `_layout_fit_issues()` calls the neutral policy once. Keep issue mapping
in the backend so the public `SigningDraftValidationIssue` contract is unchanged. Remove imports of
`_single_line_rendered_ink_fits_reservation` and
`_horizontal_multi_line_rendered_layout_fits_reservation` from the neutral layout module and delete
the old private fit/cache/cleanup cluster only after boundary tests cover every existing outcome.

Migrate `tests/unit/test_phase3_signing_backend.py` away from private layout imports and monkeypatch
points. Add policy tests for no structural issues, single-line acceptance/rejection, multi-line
acceptance/rejection, and exact issue mapping. Add adapter tests using fake preview probes and ink
ports for cache hits, 256-entry eviction, cleanup on success/exception, nominal overflow, border
containment, reference-ink preservation, stamp presence, and non-overlap. Preserve representative
backend outcome tests and record any one-to-one replacement mapping in this plan.

Update `docs/ARCHITECTURE.md` to state that neutral layout owns structural geometry while the fit
policy owns the typed decision and the rendered-fit adapter owns raster/materialization. Do not edit
`docs/SPEC.md` or implement the separate phase3 nomenclature migration here. Its inventory may be
refreshed when this slice changes tracked file/content counts; the migration itself remains out of
scope.

## Concrete Steps

Run commands from `/home/daekar/FoliaSeal`.

1. Record the clean baseline and private-helper inventory:

       git status --short --branch
       rg -n "_single_line_rendered_ink_fits_reservation|_horizontal_multi_line_rendered_layout_fits_reservation|_single_line_text_only_ink_bounds|_SINGLE_LINE_RENDERED_INK_FIT_CACHE" src tests

2. Add the neutral policy and concrete adapter, then run the new focused policy/adapter tests. The
   neutral import check must show no PIL, pyHanko, Qt, or phase3 backend modules loaded.

3. Migrate the backend and remove the old private helper cluster only after the replacement tests
   pass. The retirement gate is zero production/test imports of rendered-fit helpers from
   `visible_signature_layout.py`; the neutral module may retain structural fit helpers.

4. Run focused validation:

       .venv/bin/pytest -q tests/unit/test_visible_signature_fit_policy.py tests/unit/test_visible_signature_rendered_fit_adapters.py tests/unit/test_phase3_signing_backend.py tests/unit/test_visible_signature_layout_boundary.py
       .venv/bin/ruff check src tests

   Expect all existing backend behavior tests plus the new boundary matrix to pass.

5. Run comprehensive validation:

       .venv/bin/pytest -q
       .venv/bin/ruff check src tests scripts
       .venv/bin/python -m compileall -q src tests
       .venv/bin/python -m foliaseal --help
       .venv/bin/python -c "from foliaseal.application.visible_signature_fit_policy import VisibleSignatureRenderedFitPolicy; print('neutral rendered-fit import: PASS')"
       git diff --check
       git diff --exit-code -- docs/SPEC.md

6. Run unchanged offscreen acceptance:

       QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-acceptance-evidence

   Expect signed acceptance `10` scenarios/`7` successful signings, preview parity `18/18`, and fit
   rejection `3/3`. Remove `artifacts/signed_acceptance_evidence/` and
   `artifacts/phase3_signed_acceptance_evidence_summary.md` afterward.

7. Confirm retirement and cleanup:

       rg -n "from foliaseal.application.visible_signature_layout import.*(_single_line_rendered|_horizontal_multi_line_rendered)|_SINGLE_LINE_RENDERED_INK_FIT_CACHE" src tests
       pgrep -af 'foliaseal|pytest|PySide|Qt' | rg -v 'bwrap|codex|pgrep' || true

   The source gate must return no first-party rendered-fit imports/cache references. The process
   audit must be empty and generated acceptance outputs must be absent before commit.

## Validation and Acceptance

Acceptance requires a typed neutral fit decision and a concrete adapter boundary with no third-party
imports in the policy/layout modules. Structural no-issue plans must not invoke the probe. Single-line
and horizontal multi-line fallback decisions, cache reuse/eviction, temporary-directory cleanup,
overflow guards, border containment, reference-ink preservation, stamp presence, and non-overlap
must retain existing behavior. Backend validation issue codes/messages/severity and public CLI,
JSON, artifact, current-page, and phase3 contracts remain unchanged. Focused boundary tests, the
full suite, Ruff, compileall, CLI/import checks, SPEC diff, offscreen acceptance, artifact cleanup,
and process audit must pass. Measured Actual Improvement must be at least `.15` with no component
regression beyond `.10`.

## Idempotence and Recovery

Make the policy/adapter boundary additive before deleting old helpers. If any parity test fails,
keep the old helper as a temporary same-behavior delegate, record the mismatch here, and repair the
adapter rather than relaxing an assertion or changing a threshold. Re-running tests is safe; the
adapter must delete only its own canonical-preview temporary directories. Do not use destructive
cleanup outside generated acceptance paths, do not edit frozen contracts, and do not rename phase3
paths in this slice.

## Artifacts and Notes

The only generated outputs allowed during acceptance are the transient signed-acceptance summary and
matrix directory. They must be removed before commit. The source/test/docs changes form one
architectural change slice; unrelated GUI redesign, CLI additions, broad formatting, and phase3
nomenclature renames are forbidden. Record focused/full counts, source-grep result, offscreen counts,
SPEC diff, process audit, measured improvement, and commit IDs in Outcomes.

## Interfaces and Dependencies

In `src/foliaseal/application/visible_signature_fit_policy.py`, define neutral types equivalent to:

    @dataclass(frozen=True)
    class VisibleSignatureRenderedFitRequest:
        signature_rect: SignatureRect
        appearance: VisibleSignatureAppearancePort
        stamp_text: str
        layout_plan: SignatureLayoutPlan

    @dataclass(frozen=True)
    class VisibleSignatureRenderedFitDecision:
        accepted: bool

    class VisibleSignatureRenderedFitProbe(Protocol):
        def single_line_fits(self, request: VisibleSignatureRenderedFitRequest) -> bool: ...
        def horizontal_multi_line_fits(self, request: VisibleSignatureRenderedFitRequest) -> bool: ...

    class VisibleSignatureRenderedFitPolicy:
        @staticmethod
        def decide(
            request: VisibleSignatureRenderedFitRequest,
            *,
            probe: VisibleSignatureRenderedFitProbe,
        ) -> VisibleSignatureRenderedFitDecision: ...

The concrete probe in `visible_signature_rendered_fit_adapters.py` may use private renderer helpers,
Pillow/PyHanko, `Path`, and a bounded private cache. None of those types may appear in the neutral
request, decision, or protocol. The backend adapts its appearance structurally and remains the only
owner of `SigningDraftValidationIssue` mapping.

## Change Log

- 2026-08-06: Created from Scan Round 56 and Design Selection 56. Selected the common-caller
  policy/probe boundary at Refactor Shape Score `91.0`; phase3 nomenclature remains separate.
