## Goal

Unify visible-signature preview, validation, and final signed rendering around one real font asset set and one glyph-metric-driven measurement path. Remove the current split where backend validation/final output use pyHanko's average-width base-font engine while preview uses Qt fallback stacks.

## Why This Slice Exists

- Manual harness evidence exposed a fundamental seam: preview can look valid while validation goes red because backend width measurement is based on `len(text) * avg_width * font_size` instead of real glyph metrics.
- This is not a coverage problem. It is an architectural mismatch.
- Project policy is now explicit: we do the hard work of getting calculations right. We do not mask modeling defects with broad tolerances.

## Target State

1. Backend validation and final rendering use bundled OpenType fonts through pyHanko's OpenType shaping path.
2. Preview uses the same bundled font assets instead of generic CSS/system fallback stacks.
3. Unsupported style combinations are rejected explicitly instead of silently coerced.
4. Harness diagnostics and matrices reflect the new direct font mapping story honestly.
5. Docs describe the new rendering contract and the distinction between baseline preview coverage, stress preview coverage, and signed acceptance coverage.

## Constraints

- Prefer ruthless simplicity over elaborate compatibility scaffolding.
- Maintain two font engines only where unavoidable:
  - pyHanko OpenType shaping remains the source of truth for fit validation and final PDF content.
  - Qt may still rasterize the on-screen preview, but it must do so with the same bundled font assets and must not silently substitute generic families.
- No percentage-based fit tolerances are to be introduced in this slice.

## Work Plan

### 1. Add a canonical bundled font registry

Create a small application-layer font registry that:

- maps the UI families to bundled font assets
- resolves `(family, bold, italic)` to an exact OpenType font file
- exposes whether a requested style combination is supported
- provides the preview family name used after font registration

Planned bundled mapping:

- `Sans Serif` -> `Noto Sans` (regular, italic, bold, bold italic)
- `Serif` -> `Noto Serif` (regular, italic, bold, bold italic)
- `Monospace` -> `DejaVu Sans Mono` (regular, oblique, bold, bold oblique)
- `Fantasy` -> `Noto Serif Display` (regular, italic, bold, bold italic)
- `Cursive` -> explicit bundled script faces with limited support; unsupported style combinations must block signing rather than falling back silently

### 2. Switch backend measurement/final rendering to OpenType shaping

Update the Phase 3 signing backend so `_build_text_box_style()` uses `GlyphAccumulatorFactory` with the bundled font file selected by the registry.

Expected code impact:

- remove `SimpleFontEngineFactory` from the visible-signature path
- keep font-size preservation semantics, including half-point sizes
- surface unsupported style combinations as validation issues rather than faking another family

### 3. Align preview with the same bundled assets

Update the Qt signing shell so the preview:

- registers the bundled fonts with Qt at shell startup
- uses the resolved bundled family names instead of generic font stacks
- no longer reports `Cursive` / `Fantasy` as unsupported direct preview mappings when those bundled assets are present

The preview may still use Qt to rasterize text, but it must use the same font assets and style choices as the backend.

### 4. Update validation/harness contracts

Adjust harness assumptions to reflect the new direct mapping contract:

- font diagnostics should report all five UI families as direct preview mappings when the bundled assets are loaded
- transition diagnostics should remain active for "control changed but preview barely changed" regressions
- no detector thresholds are to be loosened to accommodate the architectural change

### 5. Update tests

Add or update tests for:

- bundled font registry resolution
- unsupported style handling for limited cursive combinations
- backend text-style construction using OpenType factories
- preview font-family resolution using bundled assets
- harness font diagnostics reflecting the new direct mapping story
- regression coverage for the dense real-world single-line case that originally exposed the width-model failure

### 6. Update docs and plans

Refresh:

- `README.md`
- `phase3_parallel_plan.md`
- `pdf_signing_app_feasibility.md`

to describe:

- the new bundled-font / OpenType rendering contract
- the fact that PDF base-font average-width measurement is no longer the visible-signature truth source
- any remaining limitations for cursive/fantasy style combinations
- the expectation that preview, validation, and signed output now share the same font assets

### 7. Verification

At minimum:

- `ruff check .`
- focused unit suites for backend, preview shell, and harness font diagnostics
- `pytest -q`

If implementation is stable enough in this slice, rerun:

- at least one preview stress matrix family that previously showed preview/validation font disagreement
- the signed acceptance matrix to ensure preview/output parity remains clean after the font-engine change

## Acceptance Criteria

- No visible-signature backend measurement uses `SimpleFontEngineFactory`.
- Backend fit decisions for visible signatures are driven by real OpenType glyph metrics.
- Preview uses bundled fonts directly instead of generic CSS fallback stacks.
- Unsupported style combinations are explicit validation errors, not silent substitutions.
- Docs and harness language reflect the new unified font story accurately.

## Execution Notes

Implemented in this slice:

- added a canonical bundled font registry for visible-signature families and style support
- vendored the bundled font assets used by that registry
- switched backend visible-signature text measurement and final rendering to pyHanko's OpenType
  shaping path
- updated the Qt preview to load the same bundled font assets and use their exact family names
- updated harness font diagnostics and test coverage to reflect direct preview mapping for all five
  UI font families
- updated project docs to describe the new bundled-font/OpenType rendering contract honestly

Observed outcome from verification:

- unit/integration suite remains green
- signed acceptance matrix remains green on the canonical clean signing fixture
- broad preview matrices are not yet fully green under the new font path

Interpretation:

- the architectural error in backend text measurement is corrected
- preview now uses the same font assets, but it still rasterizes through Qt rather than the exact
  same shaping/rendering path as the final PDF
- remaining preview-matrix failures are therefore evidence that "same assets" is not yet the same
  thing as "one engine"; a further preview-canonical-rendering slice is still needed if we want
  true one-engine parity

## Follow-on Slice: Canonical Preview Rendering

Implemented in the current follow-on slice:

- added `render_canonical_signature_preview(...)` in
  `src/foliaseal/application/signing_preview_renderer.py`
- the canonical renderer now:
  - builds a temporary one-page PDF sized to the signature rectangle
  - applies the same `TextStampStyle` content model used by signing
  - rasterizes that page through the Qt PDF render backend
  - records both reserved-area bounds and rendered-content bounds for text and stamp content
- the Qt signing shell now prefers that canonical raster as the visible preview artifact when the
  required assets are renderable
- the Phase 3 harness now prefers the canonical preview image and canonical bounds metadata over
  widget capture plus hidden-`QLabel` reference geometry when that metadata is available
- added focused regression coverage for:
  - canonical preview raster generation
  - shell attachment of canonical preview snapshots when assets are renderable

Current status of that follow-on slice:

- focused tests are green
- full suite is green
- the broad preview-matrix rerun is still the gating verification step for this sub-slice because
  the first rerun exposed and then helped fix a harness-integration bug where canonical full-image
  bounds were being fed back into clipping diagnostics as text/stamp-area bounds

## Follow-on Slice: Canonical Preview Rebaseline and Runner Stability

Implemented in the current slice:

- fixed canonical preview bounds extraction so text-only and stamp-only bounds are derived from the
  same full reservation layout instead of being recomputed from separate partial layouts
- corrected canonical stamp-area reporting to use the reserved stamp band rather than the
  content-centered background layout
- added shell-side cleanup for replaced canonical preview snapshot directories
- tightened hot image-open paths in the canonical renderer and Phase 3 harness to use bounded
  `with Image.open(...)` lifetimes instead of leaving file-backed image handles to accumulate
- added runner-level coverage that:
  - verifies preview-matrix summaries are written for a small batch
  - verifies long batches recycle shell/window lifecycles
  - verifies repeated preview refreshes keep only the latest canonical snapshot
  - verifies one canonical preview render backend instance is reused across repeated refreshes

Observed outcome:

- `multi_line` baseline canonical preview rerun is clean for signable clipping/overlap
- targeted `multi_line` stress subsets around the previously suspected stop region are clean
- full test suite remains green
- the full `wrapped_block` stress canonical preview batch now completes and writes `summary.json`
  cleanly on the current codebase
- the earlier native abort does not reproduce on the current wrapped-block stress rerun

Current classification:

- the earlier large `multi_line/top` overlap/clipping cluster was a canonical-bounds integration
  bug and is fixed
- the wrapped-block stress matrix is now rebaselined cleanly on the current codebase
- any future long-run preview-matrix abort should be treated as a fresh runner issue and isolated
  with a new reproducible subset before changing layout policy

Implication for the next slice:

- stop trying to coax the existing Qt-shell-based preview matrix through the full stress run
- either:
  - move the preview matrix to a headless canonical-render path that bypasses the widget shell for
    per-scenario preview artifact generation, or
  - isolate and replace the remaining native component that is accumulating process-wide state
- do not loosen diagnostics or change fit policy while addressing the runner crash

## TSA / Timestamping Update

Implemented in a later slice:

- added a concrete TSA adapter seam in `src/foliaseal/infra/tsa/`
- wired the signing backend to honor `timestamp_required=True` using a real timestamper path
- kept optional no-TSA signing available as the dev/admin override path
- added deterministic dummy-TSA support to the signed acceptance matrix so required timestamp
  behavior can be exercised in CI without depending on a public TSA

Current status:

- timestamp-required signing is now an implemented backend capability, not a known gap
- the next finish work is trust/certification hardening rather than basic timestamp wiring

## TSA Trust Hardening Update

- created a dedicated ExecPlan for the trust-hardening slice:
  - `.agent/tsa_trust_hardening_execplan.md`
- the trust-hardening slice now adds:
  - explicit timestamp trust-policy inputs
  - timestamp trust validation reporting separate from token presence
  - stable failure mapping for missing trust material and untrusted TSA chains
- dummy TSA runs remain CI/test-only evidence; they are not production trust proof

Policy note:

- the canonical preview path is still the correct direction because it removes Qt label layout from
  the preview truth source
- no new fit tolerances or detector slack were introduced while wiring it in

## Follow-on Slice: Headless Canonical Preview Matrix Runner

Implemented in the current slice:

- moved preview-matrix execution off the Qt signing shell and onto a headless canonical path in the
  Phase 3 harness
- each preview-matrix scenario now builds a fresh draft workflow, derives the preview directly, and
  captures artifacts from canonical preview metadata rather than widget geometry
- preserved the existing preview-matrix summary/artifact contract while eliminating the long-run
  native aborts that were specific to the Qt-shell batch path

Observed outcome:

- all six preview matrices now complete successfully on the headless path
- all signable text-clipping and signable text/stamp-overlap counts are `0`
- signed acceptance remains green
- remaining signable preview findings were reduced to narrow stamp edge-touch clusters rather than
  text-fit disagreements

## Follow-on Slice: Top-Stamp Border-Facing Inset

Implemented in the current slice:

- added a real border-facing inset for non-single-line `TOP` stamp layouts in the stamp background
  layout path instead of changing detector thresholds
- added focused regressions covering:
  - backend reserved top inset for `multi_line/top`
  - canonical preview top inset for `multi_line/top` and `wrapped_block/top`
  - headless harness diagnostics for the previously failing sparse `multi_line/top` case

Observed outcome:

- `multi_line` baseline and stress preview matrices are now clean for signable stamp warnings and
  signable stamp edge-touch
- `wrapped_block` baseline preview matrix remains clean
- `wrapped_block` stress preview matrix is now also clean on the headless path
- signed acceptance remains green
- the headless preview-matrix rebaseline is now complete for all six checked-in families

Current classification:

- the top-stamp policy goal is now satisfied without loosening diagnostics
- there is no remaining signable preview cluster in the checked-in matrices
- any future preview regression should be treated as a new layout-policy or runner defect on its own
