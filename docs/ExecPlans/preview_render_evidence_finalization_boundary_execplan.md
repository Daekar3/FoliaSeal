# Centralize Qt and Headless Preview-Evidence Finalization

This ExecPlan is a living document and must remain compliant with
`.agents/skills/write-execplan/PLANS.md`. It is one bounded continuation slice of
`docs/ExecPlans/architecture_improvement_loop_parent_execplan.md` after commit `c62b5d1c4`.

## Purpose / Big Picture

FoliaSeal's live Qt and headless preview-capture paths currently perform the same analysis-value
extraction, diagnostic grouping, debug-overlay projection, appearance-snapshot fallback, and
JSON-ready mapping independently. A change to the evidence contract therefore requires two edits
and two parity investigations. After this slice, each environment will still acquire its own
geometry and rendered image, but one typed projection boundary will own the shared finalization
policy. The existing preview and signed acceptance matrices will continue to emit the same keys,
artifact suffixes, errors, and scenario counts.

The user-visible proof is unchanged but stronger: running the existing offscreen matrices produces
the same successful/rejected scenario totals, while focused boundary tests can exercise the shared
evidence policy without constructing Qt widgets or a full harness.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/phase3_preview_capture_adapters_execplan.md` and
  `docs/ExecPlans/backend_layout_preparation_boundary_execplan.md` are implemented and committed.
- [x] Three independent post-commit scans and three independent design reviews are recorded in the
  architecture parent and summarized in this plan's Decision Log.
- [x] The external `PreviewRenderCapturePort` request/result contract and the historical
  `phase3-signing-*` CLI/DTO/JSON/artifact labels are frozen for this slice.
- [ ] The atomic phase3 nomenclature plan remains a separate future migration; it is not a
  prerequisite and must not be partially executed here.

## Progress

- [x] (2026-08-06) Consolidated scan 10 evidence and selected the preview-evidence finalization
  candidate at approximately Priority 74–75 with confidence at least 0.86.
- [x] (2026-08-06) Reviewed minimal, flexible, and common-caller designs. Selected the constrained
  typed-frame plus shared-assembler hybrid, rescored at 91.5 versus the minimal base at 86.0; the
  hybrid exceeds the base by 5.5 points and introduces no new hard-gate risk.
- [x] (2026-08-06) Added the Qt-free `PreviewEvidenceFrame`, shared request builder, and projection
  assembler in `preview_render_evidence_projection.py`.
- [x] (2026-08-06) Migrated headless first and Qt second; both adapters preserve canonical-vs-widget
  precedence, analysis-space bounds, artifact names, and one-owner temp cleanup.
- [x] (2026-08-06) Added projection request/mapping parity and import-isolation tests before removing
  the duplicated finalization blocks; focused coverage passed `94` tests with one skipped test.
- [x] (2026-08-06) Reconciled `docs/ARCHITECTURE.md`, the historical preview-capture plan, and the
  atomic phase3 nomenclature plan without renaming any external contract.
- [x] (2026-08-06) Ruff, diff checks, full pytest (`1,060 passed, 11 skipped, 1 warning`), application
  and projection import isolation, CLI help, and offscreen signed evidence passed. Acceptance totals
  were `10/7/3`, `18/18`, and `3/3`; explicit temporary roots were removed and the process audit was
  clean.
- [x] (2026-08-06) Proxy measurements were navigation `0.50`, change amplification `0.50`, seam
  reduction `0.50`, boundary-test improvement `1.00`, interface compression `0.50`, and isolation
  improvement `1.00`; `Actual Improvement = 0.63` versus predicted `0.40`, with no component below
  `-0.10`. Commit closure remains in the parent loop after the intentional git commit.

## Surprises & Discoveries

- Observation: Both adapters duplicate the same analysis extraction and mapping policy, but their
  acquisition paths differ only in widget/canonical geometry and image materialization.
  Evidence: `preview_render_evidence_adapters.py` contains two large bodies beginning at
  `build_qt_preview_render_capture_payload()` and `capture_headless_preview_render()`; both build
  `PreviewAnalysisRequest`, filter `stamp_`/`text_`/font diagnostics, write the same debug overlays,
  and emit the same mapping keys.
- Observation: The existing typed `PreviewRenderCapturePort` already protects workspace callers;
  replacing it would add migration risk without improving the duplicate policy seam.
  Evidence: `phase3_preview_render_capture.py` defines the request/result/port and both workspace
  adapters consume one `capture()` call.
- Observation: Existing adapter tests monkeypatch module-level helper names. Those names must remain
  thin forwarding wrappers until direct callers and tests have migrated; they must not retain a
  second implementation.
  Evidence: `tests/unit/test_preview_render_evidence_adapters.py` monkeypatches both helpers.

## Decision Log

- Decision: Select a constrained A+B hybrid: normalize environment-specific values into one frozen
  `PreviewEvidenceFrame`, then call shared `build_preview_analysis_request()` and
  `assemble_preview_evidence()` functions.
  Rationale: the minimal finalizer shape scored approximately 86, the flexible multi-provider shape
  approximately 77, and the common-caller service approximately 89–90. The hybrid preserves the
  existing adapter seam while exposing a small, testable policy boundary. Rescored dimensions give
  `91.5`, 5.5 points above the minimal base, satisfying the fixed hybrid gate.
  Date/Author: 2026-08-06 / Codex after three independent design reviews.
- Decision: Keep rendering, widget probing, Qt/Pillow artifact writes, and canonical temp-directory
  cleanup in the environment adapters; the shared module only consumes normalized values and
  injected callbacks.
  Rationale: moving acquisition and cleanup simultaneously would change canonical-vs-widget
  precedence and enlarge the parity-sensitive slice. The chosen boundary hides the duplicated
  policy without becoming a generic renderer.
  Date/Author: 2026-08-06 / Codex.
- Decision: Do not rename any `phase3` source path, CLI, DTO, JSON key, fixture, or artifact in this
  slice. Update the atomic nomenclature plan and stale historical wording only.
  Rationale: the live inventory contains external and persisted labels that require one coordinated
  parser/fixture/artifact migration; piecemeal aliases would increase cruft and break contracts.
  Date/Author: 2026-08-06 / Codex.

## Outcomes & Retrospective

Implementation completed on 2026-08-06. `PreviewEvidenceFrame`,
`build_preview_analysis_request()`, and `assemble_preview_evidence()` now own one shared
analysis/diagnostic/appearance/mapping policy while Qt/headless adapters retain only environment
acquisition and canonical temp cleanup. The duplicate 668-line policy bodies were replaced by
thin, typed delegation without changing the `PreviewRenderCapturePort` or any serialized contract.

Focused adapter/harness/workspace coverage passed `94` tests with one skipped test; the full suite
passed `1,060` tests with `11` skipped and one pre-existing Pillow warning. Ruff, diff checks,
application/projection import isolation, and CLI help passed. Offscreen signed evidence passed the
signed acceptance matrix (`10` scenarios, `7` successful signings, `3` matched intentional
rejections), signed preview parity (`18/18`), and signed fit rejection (`3/3`), with zero
cryptographic, annotation, preview-comparison, or expectation failures. Explicit temporary evidence
roots were removed and no FoliaSeal/Python application process remained.

Measured proxies before -> after: two policy owners -> one (`0.50` navigation), two coordinated
adapter edits -> one (`0.50` change amplification), two duplicate finalization seams -> one (`0.50`),
no shared boundary coverage -> complete frame/assembler coverage (`1.00`), two policy concepts ->
one typed projection policy (`0.50`), and no neutral isolation -> one Qt-free module (`1.00`). The
weighted `Actual Improvement` is `0.63` versus predicted `0.40` (`1.56x`), with no component
regression below `-0.10`. The parent records the commit and starts the next fresh scan.

## Context and Orientation

`src/foliaseal/presentation/qt/preview_render_evidence_adapters.py` is a presentation-edge module.
`QtPreviewRenderEvidenceAdapter` reads Qt widgets and canonical snapshots; the headless adapter
renders a canonical preview without widgets. Both receive `PreviewRenderEvidenceDependencies`, a
bundle of injected functions for rendering, analysis, geometry, artifacts, and serialization. Their
current bodies differ in acquisition but repeat the final evidence policy.

Create `src/foliaseal/presentation/qt/preview_render_evidence_projection.py`. It may import the
existing application preview-analysis request and appearance snapshot types, but it must not import
PySide6, Pillow, pyHanko, or the harness composition root. The module receives only a normalized
frame and the existing injected callbacks. “Projection” means turning an already captured image,
geometry, and analysis mapping into the stable JSON-ready evidence dictionary consumed by workspace
snapshots and CLI reports.

The public compatibility wrappers in `preview_render_evidence_adapters.py` and the private wrappers
in `phase3_harness.py` remain during migration. They may forward to the new implementation, but no
duplicated analysis/mapping body may remain after the final migration.

## Plan of Work

First define a frozen `PreviewEvidenceFrame` with the normalized fields currently assembled by both
adapters: preview and artifact identity, image/analysis paths and error, card/body/detail/stamp
bounds, analysis-detection bounds, structural/reference text bounds and errors, stamp pixmap size
and alignment, size hint, layout spacing, preview padding, active label, canonical snapshot, and
optional analysis snapshot. Define a small dependency protocol or structural callback type for the
existing engine builder, request type, appearance snapshot type, JSON serializer, debug-overlay
writers, and preview padding/text-color helpers. Do not copy the 22-callable bundle into a second
service-locator class.

Next implement `build_preview_analysis_request(frame, dependencies)` and
`assemble_preview_evidence(frame, analysis_values, dependencies)`. The first must construct the
existing `PreviewAnalysisRequest` with exactly the same values and one analysis invocation. The
second must own stamp/text/font diagnostic filtering, edge distances, debug-overlay path/error
mapping, text-image hash projection, appearance-snapshot fallback/replacement, and every existing
mapping key. It must not own temp-directory cleanup; the adapter that created a canonical snapshot
continues to clean it exactly once.

Migrate the headless function first: retain canonical rendering and file copying, construct a frame,
call the shared request/analyzer and assembler, then perform the existing canonical cleanup. Run
headless boundary tests and compare all keys before migrating Qt. Migrate the Qt function second:
retain widget reads, canonical rendering, fallback image flattening, and geometry precedence,
construct the same frame, and delegate the repeated tail. Preserve the Qt-specific size hints,
alignment, and label bounds as frame fields.

Delete the old duplicated finalization blocks only after equivalent boundary tests pass. Keep
`build_qt_preview_render_capture_payload()` and `capture_headless_preview_render()` as thin module
entry points because existing tests monkeypatch them; their bodies must only build/delegate, not
reimplement policy. Update `__all__` and imports accordingly.

Update `docs/ARCHITECTURE.md` to describe the new projection owner and the adapter responsibilities.
Correct `docs/ExecPlans/phase3_preview_render_capture_boundary_execplan.md` so it no longer claims
the callback bodies remain in `phase3_harness.py`; they now live in the evidence-adapter module and
are being centralized in this slice. Update `docs/ExecPlans/phase3_nomenclature_retirement_execplan.md`
only with the current inventory/retirement boundary; do not perform the rename.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    rg -n "build_qt_preview_render_capture_payload|capture_headless_preview_render|PreviewAnalysisRequest" src tests
    .venv/bin/pytest -q tests/unit/test_preview_render_evidence_adapters.py tests/unit/test_phase3_harness.py tests/unit/test_qt_phase3_harness_workspace.py
    .venv/bin/ruff check src tests

After the projection module and each adapter migration, run its focused tests. The final validation is:

    .venv/bin/pytest -q
    .venv/bin/ruff check src tests scripts
    git diff --check
    .venv/bin/python -c 'import sys; import foliaseal.presentation.qt.preview_render_evidence_projection; assert "PySide6" not in sys.modules'
    .venv/bin/python -m foliaseal --help
    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-preview-matrix --pdf-path artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf --certificate-path artifacts/generated_acceptance_assets/signed_acceptance_identity.p12 --passphrase secret --scenario-manifest-path tests/fixtures/phase3/release_fidelity_manifest.json --artifacts-dir /tmp/foliaseal-preview-finalization-preview
    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-acceptance-matrix --pdf-path artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf --certificate-path artifacts/generated_acceptance_assets/signed_acceptance_identity.p12 --passphrase secret --scenario-manifest-path tests/fixtures/phase3/release_fidelity_manifest.json --artifacts-dir /tmp/foliaseal-preview-finalization-signed

The matrices must retain their prior scenario totals and zero unexpected errors. Remove both explicit
temporary roots after inspection and verify no FoliaSeal/Python application process or dialog remains.

## Validation and Acceptance

Acceptance requires equivalent or stronger boundary tests for canonical and non-canonical captures,
artifact and no-artifact runs, missing images, diagnostic omission rules, appearance fallback, and
exact cleanup call counts. The full suite, Ruff, diff checks, application import isolation, CLI help,
preview matrix, signed acceptance matrix, and process/temp cleanup audit must pass. Every existing
render-capture key, error string, artifact suffix, `None` value, and scenario expectation must remain
unchanged. The shared module must import without PySide6.

Measure the same proxy dimensions used by the parent. Baseline: two duplicated analysis/finalization
blocks, two mapping policy owners, and no neutral projection boundary. Predicted improvement is `0.40`.
Accept only if Actual Improvement is at least `0.15`, no component regresses below `-0.10`, and the
worktree is clean after the intentional commit.

## Idempotence and Recovery

The migration is additive until parity tests pass. If one adapter fails, retain its old body in the
working tree, compare its mapping with the new assembler on the same fake frame, and fix the frame or
projection without changing CLI contracts. Do not delete artifacts outside the two named temporary
roots. If a compatibility wrapper remains, document its direct caller and retirement criterion; do
not create a second implementation under a renamed phase3 path.

## Artifacts and Notes

Expected evidence after completion includes focused projection tests, the full pytest count, the
preview/signed matrix summaries, and a clean process audit. Record concise command outputs here as
the plan evolves. The stale historical wording to correct is the claim that callback bodies remain
in `phase3_harness.py`; the current implementation already places them in
`preview_render_evidence_adapters.py`.

## Interfaces and Dependencies

In `src/foliaseal/presentation/qt/preview_render_evidence_projection.py`, define:

    @dataclass(frozen=True)
    class PreviewEvidenceFrame: ...

    def build_preview_analysis_request(*, frame: PreviewEvidenceFrame, dependencies: Any) -> Any: ...

    def assemble_preview_evidence(*, frame: PreviewEvidenceFrame, analysis_values: Mapping[str, Any], dependencies: Any) -> dict[str, Any]: ...

`QtPreviewRenderEvidenceAdapter` and `HeadlessPreviewRenderEvidenceAdapter` remain the environment
adapters. `PreviewRenderCapturePort`, `PreviewRenderCaptureRequest`, and
`PreviewRenderCaptureResult` remain unchanged. The projection module owns no event loop, matrix
iteration, canonical renderer, widget access, or temp cleanup.
