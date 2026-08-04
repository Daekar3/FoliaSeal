# Extract the neutral preview-analysis boundary and retire obsolete Phase 3 helper names

This ExecPlan is a living document and must be maintained in accordance with
`.agents/skills/write-execplan/PLANS.md`. It defines one complete DevLoop slice:
analysis extraction, caller migration, private compatibility-cruft removal,
focused tests, architecture/spec review, documentation reconciliation,
validation, and commit closure all belong to this plan. Milestones are
progress markers, not stopping points.

## Purpose / Big Picture

Preview evidence currently asks `phase3_harness.py` to coordinate Qt or
headless capture, image files, text-pixel detection, stamp/text edge
diagnostics, font diagnostics, image comparison, and state-transition analysis.
The same analysis choreography is duplicated in the live and headless payload
builders. This makes a small diagnostic change require understanding a large
Qt composition root and makes tests patch private harness functions instead of
testing a stable boundary.

After this slice, both capture paths will supply their existing render inputs
to a neutral `PreviewAnalysisEngine` in
`src/foliaseal/presentation/qt/preview_analysis.py`. The engine will return a
typed result with a compatibility projection that preserves the current
payload keys, artifact suffixes, fallback behavior, and error text. Qt shell
lifecycle, headless workflow lifecycle, matrix iteration, signed-output
snapshotting, and report aggregation will remain in their existing owners.

The touched analysis surface will use neutral names. The obsolete
`phase3_text_geometry_helper.py`, `phase3_image_comparison_helper.py`,
`Phase3TextGeometryHelper`, `Phase3ImageComparisonHelper`, and harness-local
builder/delegation wrappers will be removed after callers migrate. Stable
external CLI commands, persisted `Phase3HarnessCapture` JSON fields, and
artifact paths are compatibility contracts and remain unchanged in this
slice; renaming those serialized edges requires a separate coordinated
migration.

Names of deleted helpers in this plan are historical migration evidence, not
current module or class names. Current architecture is documented in
`docs/ARCHITECTURE.md`; external `phase3` CLI/DTO/JSON/artifact names remain
intentional compatibility contracts.

## Child ExecPlan Dependencies

- [x] Fresh DevLoop explorer reviewed the live duplicated capture paths,
  callers, tests, stable payload consumers, and migration hazards on
  2026-08-04.
- [x] The minimal, extensible, and common-caller interface designs were
  compared; the recommended hybrid was selected by the user.
- [x] No child ExecPlan is required. Implementation stayed within the bounded
  analysis seam; no outside blocker or follow-on child plan was required.

## Progress

- [x] (2026-08-04) Confirmed clean `main` at `80910ae08`.
- [x] (2026-08-04) Completed the required fresh DevLoop exploration and
  reviewed its report before authoring this plan.
- [x] (2026-08-04) Selected the hybrid: one typed preview-analysis engine,
  an explicit transition-analysis entry point, and outer Qt/artifact adapters.
- [x] (2026-08-04) Created this living one-slice ExecPlan before editing code.
- [x] (2026-08-04) Added the neutral analysis module and moved shared
  geometry/comparison/diagnostic behavior into it without changing observable
  payloads.
- [x] (2026-08-04) Migrated Qt/headless payload builders and tests to the
  typed neutral boundary; workspace lifecycle ownership stayed unchanged.
- [x] (2026-08-04) Removed the obsolete phase3-named helper files/classes,
  renamed their focused tests, and removed delegation-only tests. Generic
  harness adapters remain only where signed-output tests and Qt artifact
  seams need an injectable composition boundary.
- [x] (2026-08-04) Completed architecture/spec compliance review and reconciled
  README and architecture documentation with the neutral engine, its text/image
  adapters, Qt/headless adapter edge, and intentional external Phase 3 contracts.
- [x] (2026-08-04) Ran focused/full validation, architecture/documentation
  reconciliation, and the final process/artifact audit; implementation commit
  `334184d90` records the completed source/test/docs slice, with this docs-only
  plan-closure commit recorded separately below.

## Surprises & Discoveries

- Observation: The live and headless payload builders have materially
  different widget/canonical coordinate inputs, so merging them wholesale
  would risk changing geometry semantics.
  Evidence: `phase3_harness.py:1106-1398` and `:1404-1611` use different
  render/reference inputs while emitting the same stable payload keys.
- Observation: Existing helper unit tests and workspace tests are hidden
  compatibility consumers of private harness names.
  Evidence: `tests/unit/test_phase3_text_geometry_helper.py`,
  `tests/unit/test_phase3_image_comparison_helper.py`, and
  `tests/unit/test_qt_phase3_harness_workspace.py:610-650,858-903`.
- Observation: Qt reference-label rasterization is not pure analysis and must
  remain an injected outer adapter.
  Evidence: `Phase3TextGeometryHelper.reference_text_content_bounds()` imports
  `PySide6` and writes a temporary PNG.
- Observation: Signed-output render comparison and matrix summaries have
  stable consumers and are outside this extraction.
  Evidence: `phase3_signed_output_render_snapshotter.py`,
  `qa_evidence_contract.py:320-348`, and the matrix runner tests.
- Observation: Existing workspace tests monkeypatched private helper seams,
  so migrating callers required replacing those patches with a fake
  `PreviewAnalysisEngine` that records the typed request. The behavior tests
  then continued to prove the analysis-image coordinate contract directly.
  Evidence: `tests/unit/test_qt_phase3_harness_workspace.py` now asserts
  `PreviewAnalysisRequest.analysis_image_path` and
  `analysis_detection_bounds`.

## Decision Log

- Decision: Create `presentation/qt/preview_analysis.py` as the neutral
  analysis boundary rather than an application-level signing module.
  Rationale: the inputs are presentation capture images and widget/canonical
  bounds, while the module can remain Qt-free and avoid leaking capture policy
  into application signing semantics.
  Date/Author: 2026-08-04 / Codex.
- Decision: Expose `PreviewAnalysisEngine.analyze()` and
  `PreviewAnalysisEngine.analyze_capture_transitions()` only; do not introduce
  a registry or generic analyzer graph in this slice.
  Rationale: the common caller needs one complete deterministic result, while
  a registry would add indirection before a second real consumer exists.
  Date/Author: 2026-08-04 / Codex.
- Decision: Keep Qt reference rasterization and debug artifact writing outside
  the pure engine behind injected callables/ports.
  Rationale: the engine must be testable with deterministic image fixtures and
  must not acquire a Qt application lifecycle or leave temporary artifacts.
  Date/Author: 2026-08-04 / Codex.
- Decision: Strip obsolete `phase3` names from the touched analysis modules,
  helper files, tests, and private wrapper APIs, but preserve external
  `phase3-signing-harness` and serialized `Phase3*` contracts.
  Rationale: private names have no production consumers and are safe cruft to
  remove; changing published JSON/CLI edges in this slice would silently break
  acceptance tooling.
  Date/Author: 2026-08-04 / Codex.

## Outcomes & Retrospective

The implementation boundary is now `PreviewAnalysisEngine` in
`presentation/qt/preview_analysis.py`, with `PreviewTextGeometryAnalyzer` and
`PreviewImageComparisonAnalyzer` providing deterministic sub-adapters. Live Qt
and headless capture paths retain their distinct lifecycle/render inputs and
delegate analysis through the typed request/result boundary. The deleted
phase3-named helper modules/classes and delegation-only seams are no longer
current architecture; their names remain only in historical migration notes.
The stable Phase 3 CLI/DTO/JSON/artifact compatibility edge is intentionally
unchanged and is documented in `README.md` and `docs/ARCHITECTURE.md`.

Focused boundary/harness validation: 107 passed with one existing Pillow
deprecation warning. Full suite: 1,030 passed with the same warning. Payload
and artifact parity stayed green across the Qt/headless workspace and
signed-output snapshot tests. The neutral import-isolation test confirms that
`preview_analysis` does not load PySide6. Final process/artifact audit and
commit hashes are recorded below after commit closure.

## Context and Orientation

`src/foliaseal/presentation/qt/phase3_harness.py` is the current composition
root. It builds workspace/session/matrix collaborators and also contains the
duplicated live/headless preview payload builders. The target builders are
`_build_qt_preview_render_capture_payload()` and
`_capture_headless_preview_render()`.

The current low-level helpers are split between
`phase3_text_geometry_helper.py`, `phase3_image_comparison_helper.py`, and
private functions in `phase3_harness.py`. They operate on PNG paths and plain
mapping-shaped bounds. `phase3_harness_workspace.py` owns shell refresh,
workflow state, and Qt/headless capture lifecycle; it must continue to do so.

The result mappings feed `Phase3HarnessWorkspaceSnapshot`, the capture
assembler, `Phase3SignedOutputRenderSnapshotter`, the evidence contract, and
reporting. Their existing keys and artifact names are observable contracts.

## Plan of Work

First create `preview_analysis.py` with small immutable value objects for
pixel rectangles and a `PreviewAnalysisRequest` containing image paths,
text/stamp/card bounds, optional structural/reference bounds, text color, and
injected raster/reference/artifact callables. Define
`PreviewAnalysisResult.as_mapping()` to emit the exact existing analysis
payload fields and `PreviewAnalysisEngine.analyze()` to own text geometry,
stamp/text edge diagnostics, font diagnostics, image hashes, normalized image
change/aspect calculations, and deterministic error/fallback handling.

Move the implementation from `Phase3TextGeometryHelper`,
`Phase3ImageComparisonHelper`, and the shared pure/private analysis functions
into this neutral module. Keep Qt `QLabel` reference capture as an injected
`reference_text_bounds` producer supplied by the workspace/composition layer.
Keep debug overlay writes as an injected artifact sink or outer adapter so the
engine can run without a GUI or filesystem side effects in unit tests.

Add `analyze_capture_transitions(states)` to the same module for the existing
state-transition diagnostics. It must preserve issue codes, thresholds, and
mapping keys; it must not inspect Qt widgets or run matrix aggregation.

Update both live and headless payload builders to construct the typed request,
invoke the engine, and merge `as_mapping()` into the existing payload. Update
workspace dependency bundles and composition wiring so Qt/reference capture
and artifact paths remain at the adapter edge. Remove direct harness calls to
the old helper factories and private delegation functions.

Delete the obsolete helper modules and rename their test modules to neutral
names. Remove tests that only prove private delegation or compatibility alias
behavior. Retain deterministic image/text boundary tests, one Qt/headless
payload-contract integration test, stable capture JSON tests, and signed-output
snapshotter tests.

Run a touched-scope nomenclature audit. No active source/test/docs reference
to the removed helper filenames, classes, or private `phase3` analysis wrappers
may remain. Leave only explicitly documented external `phase3` CLI/DTO/JSON/
artifact compatibility names and historical migration notes.

## Milestones

### Milestone 1: Neutral analysis engine

The new module exposes the typed request/result and transition-analysis entry
point. Deterministic PNG tests prove text bounds, line grouping, edge
diagnostics, font classification, hashing, normalized comparison, error
fallbacks, and stable mapping serialization without importing Qt.

### Milestone 2: Live/headless migration and cruft removal

Both payload builders use the same engine while retaining their distinct
capture inputs. Old helper modules, private wrappers, phase3 helper names, and
delegation-only tests are deleted. Existing payload consumers and artifact
paths remain unchanged.

### Milestone 3: Compliance and closure

Run focused and full validation, perform the required architecture/spec review,
reconcile README and architecture documentation with the neutral boundary and
intentional external compatibility edge, audit processes/artifacts, update
this living plan with evidence, and commit the completed slice.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

    rg -n "_build_phase3_text_geometry_helper|_build_phase3_image_comparison_helper|Phase3TextGeometryHelper|Phase3ImageComparisonHelper|phase3_text_geometry_helper|phase3_image_comparison_helper" src tests docs README.md
    .venv/bin/python -m pytest -q tests/unit/test_phase3_harness.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_preview_text_geometry.py tests/unit/test_preview_image_comparison.py tests/unit/test_preview_analysis.py tests/unit/test_phase3_appearance_snapshotter.py tests/unit/test_phase3_sign_time_diagnostics_snapshotter.py tests/unit/test_phase3_preview_matrix_runner.py

After migration, run:

    .venv/bin/python -m pytest -q
    .venv/bin/ruff check src tests
    .venv/bin/python -m compileall -q src tests
    git diff --check
    rg -n "phase3_(text_geometry_helper|image_comparison_helper)|Phase3(TextGeometryHelper|ImageComparisonHelper)|_build_phase3_(text_geometry_helper|image_comparison_helper)" src tests README.md docs/ARCHITECTURE.md || true
    ps -eo comm= | rg '^(python|python3|foliaseal)$' || true
    git status --short

Expected results are green focused and full suites, no removed helper names in
active code/tests/current architecture docs, unchanged stable payload key
sets and artifact suffixes, no running FoliaSeal/Python process, and a clean
worktree after commit. Historical ExecPlans may retain their original names
as migration records.

## Validation and Acceptance

For a deterministic PNG fixture, calling `PreviewAnalysisEngine.analyze()`
must return the same text/stamp/edge/font/image analysis values and error
strings currently emitted by both live and headless payload builders. Its
`as_mapping()` output must contain the same keys and `None` behavior as the
pre-migration render payload.

The existing Qt and headless capture paths must still produce the same
`preview_image_path`, `analysis_preview_image_path`, analysis bounds,
`edge_distances_px`, text/stamp diagnostics, debug artifact suffixes, and
cleanup behavior. Existing evidence-contract, reporting, and signed-output
snapshot tests must remain green.

Importing the neutral analysis module must not import `PySide6`. Unit tests must
use temporary deterministic PNGs and injected fakes; no GUI process or dialog
may remain open. The full suite, Ruff, compileall, and diff checks must pass.

## Idempotence and Recovery

The migration is safe to repeat because tests use temporary images and artifact
directories. If a payload differs, first compare sorted JSON keys and the
pre/post analysis mapping before changing thresholds. If Qt reference capture
fails, keep the previous structural/reference fallback and report the same
error string rather than silently substituting a different coordinate space.
Do not restore deleted private aliases to make tests pass; migrate the caller
or add a properly typed injected dependency. If a stable external contract
would need to change, stop that change and record it as a separate migration
plan instead.

## Artifacts and Notes

Record concise evidence here at completion:

    focused preview/harness tests: 107 passed, 1 Pillow deprecation warning
    full suite: 1030 passed, 1 Pillow deprecation warning
    stable payload/artifact parity: pass
    removed internal phase3 analysis names: pass; external compatibility edge documented
    import isolation: neutral analysis module remains Qt-free
    process/artifact audit: pass; worktree clean, no FoliaSeal/Python process running, and no generated untracked PNG/PDF/JSON artifacts
    implementation commit: 334184d90
    plan-closure commit: pending this docs-only follow-up commit (record its hash after creation)

Generated PNGs, PDFs, debug overlays, certificates, and dialogs must be
temporary or ignored and must be removed after validation. No GUI process may
remain open.

## Interfaces and Dependencies

Create `src/foliaseal/presentation/qt/preview_analysis.py` with an interface
equivalent to:

    @dataclass(frozen=True)
    class PreviewAnalysisRequest:
        preview_image_path: str | None
        analysis_image_path: str | None
        card_bounds: RectPx | None
        text_widget_bounds: RectPx | None
        stamp_band_bounds: RectPx | None
        text_color_rgba: tuple[int, int, int, int] | None
        reference_text_bounds: RectPx | None
        structural_text_bounds: RectPx | None
        structural_line_bounds: tuple[RectPx, ...]
        stamp_content_bounds: RectPx | None
        artifact_sink: PreviewAnalysisArtifactSink | None

    @dataclass(frozen=True)
    class PreviewAnalysisResult:
        ...
        def as_mapping(self) -> dict[str, object]: ...

    class PreviewAnalysisEngine:
        def analyze(self, request: PreviewAnalysisRequest) -> PreviewAnalysisResult: ...
        def analyze_capture_transitions(
            self, states: Sequence[Mapping[str, Any]]
        ) -> tuple[Mapping[str, Any], ...]: ...

`RectPx` is a validated immutable pixel rectangle. `PreviewAnalysisArtifactSink`
is a narrow injected writer for optional debug overlays; production wiring may
use the existing filesystem helpers, while tests use an in-memory or temporary
sink. Text/image raster reading and Qt reference-label capture must be injected
or performed by outer adapters. The engine may depend on Pillow through a
local-substitutable raster adapter, but it must not import PySide6 or own the
Qt event loop.

`Phase3HarnessWorkspaceSnapshot`, evidence result DTOs, report serializers,
CLI command names, and persisted JSON/artifact keys remain unchanged. The
neutral engine is an internal presentation analysis boundary, not a new public
application command.

## Revision Notes

2026-08-04: Created after the required fresh DevLoop exploration and the
minimal/common-caller hybrid comparison. Scoped the one-slice implementation
to shared pure preview analysis, explicit Qt/artifact adapters, private
compatibility-cruft removal, neutral internal nomenclature, and stable
external evidence-contract preservation.
