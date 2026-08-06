# Isolate Preview Raster Rendering and Rendered-Ink Measurement

This living ExecPlan follows `.agents/skills/write-execplan/PLANS.md` and the fixed architecture
loop in `docs/ExecPlans/architecture_improvement_loop_parent_execplan.md`. It is one complete DevLoop
slice: the neutral application raster port, rendered-ink measurement seam, application migrations,
boundary tests, architecture documentation, acceptance evidence, cleanup, and commits all belong to
this plan.

## Purpose / Big Picture

FoliaSeal's canonical visible-signature preview is currently an application function that imports a
concrete Qt PDF renderer, while layout fit checks dynamically reach into private signing-backend
helpers. This makes headless testing and agent-targeted automation depend on GUI infrastructure and
requires readers to follow preview, reservation, layout, and backend internals to understand one fit
decision. After this slice, application code will request raster rendering through a small neutral
port and will use an injected rendered-ink measurement port. Qt and infrastructure adapters will be
constructed at presentation or harness composition edges. Preview images, alpha behavior, fit
verdicts, evidence JSON, CLI commands, and visible signing behavior remain unchanged.

The improvement is observable without guessing at internals: an import-isolation test can import the
neutral application modules without Qt or infrastructure rendering; fake raster/ink ports can drive
canonical preview and fit behavior deterministically; the existing preview parity, signed acceptance,
and intentional fit-rejection matrices retain their scenario counts; and repeated measurement no
longer leaves temporary canonical-preview directories behind.

## Child ExecPlan Dependencies

- [x] Parent scan round 19 identified `neutral_preview_render_backend_boundary` at Priority about
  `61–67`, confidence `0.83–0.86`, with two independent evidence clusters.
- [x] Parent design selection 19 compared minimal, flexible, and common-caller shapes and selected
  the constrained ports hybrid at shape score `90`, seven points above the minimal base.
- [x] The clean implementation baseline is `bca2ac712`; `docs/SPEC.md` hash is
  `d929e189269f0f057c6a72b43fd2d430965a975be720b55139fdb1d92afe282b`.
- [x] Existing preview, layout, backend, Qt lifecycle, evidence, and render-backend tests provide
  behavior characterization and fake seams.

## Progress

- [x] (2026-08-06) Created this self-contained plan after scan and design review.
- [x] (2026-08-06) Completed the DevLoop pre-implementation reconnaissance; confirmed the existing
  `render_backend=` keyword, lazy exports, layout request defaults, and test monkeypatch seams that
  must remain compatible during migration.
- [x] (2026-08-06) Added neutral raster request/result/port and rendered-ink measurement port without
  Qt or infra imports in the application boundary.
- [x] (2026-08-06) Migrated canonical preview rendering, horizontal reservation, visible-layout fit
  helpers, backend measurers, and Qt/evidence composition while preserving compatibility keywords and
  lazy exports.
- [x] (2026-08-06) Added boundary/import-isolation/cleanup/alpha-dimension/cache tests and retained
  equivalent existing behavioral coverage.
- [x] (2026-08-06) Reconciled architecture and active plans, ran full and offscreen validation, cleaned
  artifacts and processes, measured improvement, and prepared the implementation for commit/rescan.

## Surprises & Discoveries

Record every hidden caller, import cycle, behavior difference, temporary-directory leak, or matrix
regression here with command/test evidence. Do not restore a concrete application import as a quick
fix.

Initial discovery: `measure_horizontal_single_line_rendered_reference()` returns bounds from a
canonical snapshot but does not clean the snapshot's temporary directory. Evidence: repeated direct
calls create `foliaseal-canonical-preview-*` directories. The new measurement seam must clean in a
`finally` block after copying the needed bounds.

Initial discovery: existing tests monkeypatch both
`foliaseal.application.signing_preview_renderer.render_canonical_signature_preview` and
`foliaseal.application.phase3_signing_backend.detect_text_content_bounds_in_image`. Compatibility
wrappers or updated boundary fixtures must preserve equivalent observable patch points until all
first-party callers migrate.

Implementation discovery: the first offscreen evidence run failed with
`AttributeError: 'NoneType' object has no attribute 'render_page'` because a Qt evidence caller can
legitimately provide no canonical backend. The composition adapter now injects a neutral port only
when a backend exists and otherwise preserves the renderer's lazy fallback. The corrected run passed
all three matrices (`10/7`, `18/18`, and `3/3`).

Implementation follow-up: the compliance review also found that the actual signing-plan fit path
could still default lazily when no port was carried into the backend request. `SignPdfUseCase` now
stores the optional port on `SigningBackendRequest`, and the Qt harness composes it through
`QtPreviewRasterRenderer` when building the signing executor. Direct headless callers retain the
existing fallback.

Cleanup discovery: repeated full/offscreen tests left many exact
`/tmp/foliaseal-canonical-preview-*` directories from callers that intentionally retain snapshots.
The acceptance audit removed those exact directories after copying required evidence and confirmed no
matching directories or active FoliaSeal/Python/Qt processes remained.

## Decision Log

- Decision: use a constrained ports hybrid rather than a broad visual coordinator. Rationale: the
  minimal raster port alone leaves private preview/backend imports, while a coordinator would duplicate
  `VisibleSignatureLayoutService` and risk changing fit/cache ordering. The hybrid adds only a raster
  port and a rendered-ink measurement port, borrowing explicit intent/cleanup ownership without
  creating a generic service. Date/Author: 2026-08-06, Codex.
- Decision: keep canonical snapshot assembly in `signing_preview_renderer.py` and layout policy in
  `visible_signature_layout.py`. Rationale: both modules already own cohesive behavior; the seam is
  dependency inversion, not a file-moving or broad coordinator rewrite. Date/Author: 2026-08-06, Codex.
- Decision: retain `render_backend=` and existing lazy exports as temporary compatibility entry points
  with an explicit retirement criterion: delete them only after `rg` shows no first-party production,
  harness, or test caller uses the old keyword or private helper aliases. Rationale: current tests and
  evidence callers encode these names, and a piecemeal rename would break phase3 contracts. Date/Author:
  2026-08-06, Codex.
- Decision: allow a lazy legacy renderer fallback only for direct no-argument callers during migration,
  while all production composition paths pass the neutral port. Rationale: current public preview
  helpers are called without a backend by existing tests and application exports; removing the default
  in this slice would be a behavior change. The fallback has no module-level Qt/infra import and is
  documented for retirement after caller migration. Date/Author: 2026-08-06, Codex.

## Outcomes & Retrospective

Completion record (2026-08-06): focused boundary/seam suite passed `225` tests; full pytest passed
`1,093` tests with one pre-existing Pillow deprecation warning; Ruff, compileall, `git diff --check`,
CLI help, and subprocess import isolation passed. `PreviewRasterResult` validates positive geometry
and exact RGBA byte length; neutral fake rendering preserved request mapping and alpha/dimensions.
The offscreen evidence command passed signed acceptance `10` scenarios with `7` successful signings,
preview parity `18/18`, and fit rejection `3/3`. The explicit evidence root and summary were removed;
the exact canonical-preview temp-directory sweep and process audit were clean.

The Qt lifecycle and evidence composition now construct `QtPreviewRasterRenderer` at the edge. The
application renderer retains only a lazy legacy fallback and `render_backend=` compatibility keyword;
private phase3 preview-helper imports are gone from neutral layout, and no first-party compatibility
alias was retired because current harness/test callers still exercise the old keyword. The port stayed
narrow; the only redesign was the bounded `None` backend fallback correction recorded above.

Proxy measurement: navigation `0.30`, change amplification `0.75`, seam-risk reduction `0.80`,
boundary-test improvement `0.85`, interface compression `0.75`, and boundary isolation `0.90`;
weighted Actual Improvement `0.54` versus predicted `0.40`, with no component regression below
`-0.10`. The next scan must verify whether the remaining lazy compatibility fallback and phase3
nomenclature plan qualify as separate bounded seams.

## Context and Orientation

`src/foliaseal/application/signing_preview_renderer.py` builds a temporary PDF with the canonical
pyHanko stamp style, renders it to RGBA PNGs, and returns
`CanonicalSignaturePreviewSnapshot`. It currently imports `QtPdfRenderBackend` and
`infra.render.base.RenderPageRequest` and constructs a Qt backend when no backend is passed.
`src/foliaseal/application/horizontal_signature_reservation.py` creates roomy reference previews and
uses `text_raster_analysis` to derive rendered glyph bounds. `src/foliaseal/application/visible_signature_layout.py`
contains fallback fit checks for single-line and horizontal multi-line image stamps; those checks
currently import private helpers from `phase3_signing_backend.py` dynamically. The backend's
`_BackendHorizontalInkMeasurer` and `_layout_fit_issues()` call the same paths.

`src/foliaseal/infra/render/qt_backend.py` implements the concrete `render_page` operation using
QtPdf and returns width, height, and RGBA bytes. `src/foliaseal/presentation/qt/signature_preview_lifecycle.py`,
`phase3_harness.py`, evidence adapters, and app-frame composition are the correct places to construct
that adapter. Existing tests use fake objects with `render_page`, and the Qt backend characterization
suite proves byte and dimension behavior.

## Plan of Work

Create `src/foliaseal/application/preview_render_boundary.py` with application-only immutable DTOs
and protocols:

    @dataclass(frozen=True)
    class PreviewRasterRequest:
        document_path: str
        page_index: int
        zoom: float

    @dataclass(frozen=True)
    class PreviewRasterResult:
        width_px: int
        height_px: int
        rgba_bytes: bytes

    class PreviewRasterRenderer(Protocol):
        def render_page(self, request: PreviewRasterRequest) -> PreviewRasterResult: ...

    class RenderedInkMeasurementPort(Protocol):
        def measure(self, request: RenderedInkMeasurementRequest) -> RenderedInkMeasurementResult: ...

The measurement request/result must carry only image paths and integer rectangle mappings, text color,
and an optional structural reference bound. The port must not expose Qt, Pillow image objects, pyHanko,
or infrastructure request types. A small adapter can delegate to the existing
`detect_text_content_bounds_in_image`; a fake returns deterministic bounds and records requests.

Refactor `_render_preview_style()` and `render_canonical_signature_preview()` to consume the neutral
raster port. The adapter maps the neutral request to the existing `RenderPageRequest` and maps the
result back byte-for-byte, validating positive dimensions and `len(rgba_bytes) == width_px * height_px * 4`.
Preserve `flatten_to_white`, transparent PNG behavior, output filenames, snapshot fields, and safe
temporary-directory cleanup. Keep `render_backend=` as a temporary structural compatibility keyword
that is wrapped, not re-annotated with a concrete infra type.

Move `_signing_draft_preview_for_stamp_text()` and its text-splitting logic to a neutral application
preview helper or expose an application-owned public builder from the renderer. Update visible-layout
fit checks to use that neutral builder and the injected measurement/raster seam; they must not import
`phase3_signing_backend` private helpers. Thread the port through the backend layout preparation and
horizontal measurer where available, preserving the current `False`/`None` fallback on renderer or
analysis failure and the 256-entry fit-cache key/eviction behavior.

Update `horizontal_signature_reservation.py` to accept the neutral raster/ink collaborator, copy the
needed bounds, and clean every canonical snapshot in `finally`. Update Qt lifecycle, evidence, harness,
and app-frame composition to construct the concrete adapter once per existing lifetime and pass it
through existing callable/dependency records. Do not rename phase3 modules, commands, DTOs, JSON keys,
fixture paths, artifact paths, or public application exports in this slice.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    rg -n "QtPdfRenderBackend|RenderPageRequest|_signing_draft_preview_for_stamp_text|render_backend=" src/foliaseal/application src/foliaseal/presentation/qt tests
    .venv/bin/pytest -q tests/unit/test_signing_preview_renderer.py tests/unit/test_horizontal_signature_reservation.py tests/unit/test_visible_signature_layout.py tests/unit/test_phase3_signing_backend.py
    .venv/bin/ruff check src tests scripts
    .venv/bin/pytest -q
    .venv/bin/python -m foliaseal --help
    git diff --check

Run a subprocess import firewall proving that importing the neutral preview boundary, renderer,
horizontal reservation, and visible-layout modules does not load `foliaseal.infra.render` or Qt.
Run the existing offscreen preview-parity, signed-acceptance, and fit-rejection matrices under an
explicit `/tmp/foliaseal-neutral-preview-evidence` root using the tracked/generated acceptance assets.
Record counts and summary paths, then remove that exact root and audit for FoliaSeal/Python/Qt/dialog
processes. Never leave canonical-preview temp directories or generated assets behind.

## Validation and Acceptance

Acceptance requires: application preview/layout/reservation modules have no module-level concrete Qt
or infra-render imports; private phase3 backend preview-helper imports are gone from neutral layout;
neutral fake ports can exercise canonical rendering and rendered-ink fit behavior; RGBA dimensions,
alpha flattening, snapshot geometry, cleanup, cache hits, `None` fallbacks, error codes, and evidence
JSON remain unchanged; real Qt composition still renders the same visible signatures; full pytest,
Ruff, CLI help, import isolation, and diff checks pass; preview/signed/fit matrices retain their
baseline scenario counts and expected outcomes; `docs/SPEC.md` hash is unchanged; no phase3 external
contract changes occur; temporary roots and processes are clean; and `main` is clean after commits.

The cycle is accepted only when measured weighted Actual Improvement is at least `0.15` and no proxy
component regresses below `-0.10`. Baseline proxies are navigation `0.35`, change amplification
`0.65`, seam-risk reduction `0.70`, boundary-test improvement `0.60`, interface compression `0.45`,
and boundary isolation `0.45`; predicted weighted Actual Improvement is `0.40`. Repeat the same proxy
definitions after migration and record arithmetic in this plan and the parent.

## Idempotence and Recovery

The migration is additive: introduce neutral DTOs and adapters, prove fake/real parity, then remove
private imports. If a caller still relies on `render_backend=`, keep the wrapper and record its caller
until the retirement grep is clean. If a renderer fails, preserve the current `None`/`False` fallback
and cleanup behavior. If a matrix differs, stop acceptance, record the exact scenario and artifact,
and repair the port mapping rather than weakening the expectation. Cleanup uses only the exact named
temporary root and canonical-preview directories created by this run.

## Artifacts and Notes

Durable artifacts are the neutral boundary module, migrated application/presentation code, boundary
tests, architecture documentation, this child plan, and parent ledger updates. Generated PNGs, PDFs,
and summaries are allowed only under the explicit temporary evidence root and must be removed before
commit. `docs/SPEC.md` and all phase3 external names are frozen.

## Interfaces and Dependencies

The final application boundary must expose neutral `PreviewRasterRequest`, `PreviewRasterResult`,
`PreviewRasterRenderer`, and rendered-ink request/result/port types. The concrete Qt adapter may use
`infra.render.base.RenderPageRequest` internally, but that type must not cross into application code.
The existing `VisibleSignatureLayoutService` remains the owner of layout policy and consumes an
injected `HorizontalInkMeasurer`; the backend remains the owner of certificate semantics and signing.
Pillow and pyHanko remain implementation dependencies of canonical stamp materialization, not types
in the raster port. The temporary compatibility wrapper has a dated retirement criterion and may not
become a second renderer implementation.

Revision note: created 2026-08-06 after scan round 19 and design selection 19; selected constrained
ports hybrid over the incomplete minimal port and over-broad visual coordinator.
