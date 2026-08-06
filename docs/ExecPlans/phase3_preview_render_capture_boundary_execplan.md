# Extract the Phase 3 preview-render capture boundary

This ExecPlan is a living document and must remain compliant with `PLANS.md`. It is the next
one-slice child of `docs/ExecPlans/architecture_improvement_loop_parent_execplan.md` after commit
`4554c6922`.

## Purpose / Big Picture

The preview matrix and interactive harness currently ask `phase3_harness.py` to coordinate widget
geometry, canonical rendering, raster analysis, debug overlays, artifact paths, and JSON-ready
diagnostic shaping. This makes preview evidence hard to test and makes a small rendering change
require edits across a 2,386-line composition root. After this slice, both live Qt and headless
preview callers will use one small capture request/result boundary while their environment-specific
rendering remains in separate adapters. Running the existing 8-scenario preview matrix must produce
the same artifact names, summary keys, diagnostics, and zero error rows.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/visible_signature_layout_adapter_boundary_execplan.md` is implemented and
  committed as `4554c6922`.
- [x] Three independent post-commit scans and two independent design reviews are recorded in the
  parent plan and this plan.
- [ ] No other feature or nomenclature-renaming plan is a prerequisite; the external
  `phase3-signing-*` names remain stable during this slice.

## Progress

- [x] (2026-08-05) Selected `phase3-preview-render-capture-boundary` from the fresh scan with
  Candidate Priority `65.7`.
- [x] (2026-08-05) Reviewed minimal, flexible ports/adapters, and common-caller designs. Selected
  constrained A+B: one typed capture request/result and one common sequencing engine, with separate
  Qt and headless adapters and no lifecycle unification.
- [x] (2026-08-05) Added the typed request/result/port and separate Qt/headless adapter objects at
  the presentation boundary.
- [x] (2026-08-05) Migrated both workspace dependency bundles and production harness composition to
  one typed `.capture()` call. The existing environment-specific payload builders remain the
  adapter callbacks for this bounded slice; no duplicate lifecycle or mapping projection was added.
- [x] Keep the existing environment-specific callback bodies in the composition root for this
  bounded slice; the typed adapter objects are the accepted boundary and the large-body extraction
  is explicitly a separately ranked follow-on, not unfinished work in this plan.
- [x] Add boundary forwarding/projection coverage and run focused/full validation plus both release
  matrices. Existing harness/workspace parity tests remain the behavioral parity suite because the
  callback bodies and artifact contract are intentionally unchanged.
- [x] Reconcile docs and parent plan, measure the cycle, clean temporary processes/artifacts, and
  complete the implementation commit; the required post-commit rescan is tracked by the parent loop.

## Surprises & Discoveries

- Observation: `Phase3HarnessWorkspaceAdapter.capture_snapshot()` is already the common caller for
  live and headless capture; the two adapters differ in widget access and canonical rendering, not
  in matrix lifecycle.
  Evidence: `src/foliaseal/presentation/qt/phase3_harness_workspace.py:183-214` and `:285-336`.
- Observation: preview evidence contracts require non-empty `render_capture`, image paths, text
  bounds, debug paths, clipping, and stamp-warning fields.
  Evidence: `src/foliaseal/application/qa_evidence_contract.py:312-329`.
- Observation: a broad generic renderer/manager would create a second lifecycle abstraction and
  risk changing stable artifacts. The selected shape keeps existing mappings and suffixes while
  extracting only capture sequencing and adapters.
- Observation: the existing Qt/headless payload builders have extensive private-helper and artifact
  parity coverage. Moving their bodies in the same slice would duplicate or disturb the stable
  evidence contract, so the new typed adapters own the environment boundary while the callback bodies
  remain composition-root implementation details for a measured follow-on.
  Evidence: focused harness/workspace tests remained green after the typed migration (`96 passed`).

## Decision Log

- Decision: Select the constrained A+B hybrid rather than a broad generic ports registry or full
  live/headless unification.
  Rationale: the flexible design scored highest before penalties, but only a small request/result
  boundary with environment-specific adapters preserves the stable CLI/JSON/artifact contracts and
  avoids leaking Qt/Pillow into analysis code. The hybrid rescored to `91.5`, at least five points
  above the minimal base `82.0`, with no hard-gate risk.
  Date/Author: 2026-08-05 / Codex, after two independent design reviews.
- Decision: Keep `PreviewAnalysisEngine` as the existing analysis collaborator and leave signed
  output, matrix iteration, Qt event-loop ownership, and Phase 3 CLI names out of this slice.
  Rationale: those are established boundaries or external contracts, not preview-capture ownership.
  Date/Author: 2026-08-05 / Codex.
- Decision: Retire direct private capture helpers after production callers and tests migrate, rather
  than leave permanent forwarding aliases.
  Rationale: the project favors removal of compatibility debris when no current consumer requires it;
  the old payload mapping remains the compatibility projection.
  Date/Author: 2026-08-05 / Codex.

## Outcomes & Retrospective

Implementation and validation completed on 2026-08-05. The accepted slice introduces one typed
`PreviewRenderCapturePort` request/result seam, keeps Qt and headless adapters separate, and routes
both workspace snapshot paths through exactly one `.capture()` call. The existing callback bodies
remain in `phase3_harness.py` by deliberate scope decision: moving the artifact-heavy bodies would
be a larger parity-sensitive slice, so the fresh architecture scan will rank that residual rather
than silently treating it as completed extraction.

Evidence:

- Focused boundary/harness/workspace tests: `96 passed`.
- Full suite: `1044 passed`, one pre-existing Pillow deprecation warning.
- Ruff and `git diff --check`: clean.
- Preview matrix: 8 scenarios, 0 error rows.
- Signed acceptance matrix: 8 scenarios, 6 successful signings, 2 matched intentional rejections,
  zero cryptographic/annotation/preview-output failures, `acceptance_expectations_passed=True`.
- Explicit `/tmp/foliaseal-preview-capture-preview` and
  `/tmp/foliaseal-preview-capture-signed` directories were removed; process audit found no
  FoliaSeal, Qt harness, or pytest processes.

Measured proxies (before -> after): two untyped callback seams -> one typed port per workspace
dependency; two duplicated caller orchestrations -> one typed capture call at each caller; no
stable request/result boundary -> one frozen request/result pair. Using the parent formula:
navigation `0.0`, change amplification `0.5`, seam reduction `1.0`, boundary-test improvement
`0.25`, interface compression `0.5`, boundary isolation `0.0` gives `Actual Improvement = 0.35`.
Predicted improvement was `0.30`, prediction accuracy `1.17x`, and no component is below `-0.10`.
The cycle is accepted; the residual callback-body extraction and internal `phase3_*` naming are
explicit follow-on candidates for fresh ranking and the atomic nomenclature plan.

## Context and Orientation

`src/foliaseal/presentation/qt/phase3_harness.py` is the Qt composition root. Its
`_build_qt_preview_render_capture_payload()` reads widget geometry, canonical snapshots, writes
preview/debug images, invokes `PreviewAnalysisEngine`, and shapes the `render_capture` mapping.
`_capture_headless_preview_render()` performs the corresponding canonical-render path for unattended
matrices. `phase3_harness_workspace.py` injects those callbacks into Qt and headless workspace
adapters, and `signing_workspace_testing_port.py` exposes the Qt testing-panel bridge. The
`PreviewAnalysisEngine` is already a reusable typed analyzer; do not duplicate it.

The external contracts are frozen: `phase3-signing-preview-matrix` and related commands, summary
JSON keys, preview/debug PNG suffixes, artifact directories, and signed-matrix lifecycle must not
change. “Adapter” here means code that knows how to read Qt/Pillow/canonical-renderer details;
“neutral capture service” means the small sequencing object that only coordinates typed request,
render result, analysis result, and artifact publication.

## Plan of Work

First add `src/foliaseal/presentation/qt/phase3_preview_render_capture.py`. Define frozen
`PreviewRenderCaptureRequest` (`preview`, `artifacts_dir`, `artifact_basename`) and
`PreviewRenderCaptureResult` with the existing JSON-ready render-capture mapping plus typed artifact
references/errors. Define `PreviewRenderCapturePort.capture(request)` as the one caller-facing method.
The module may import presentation dependencies because it is not an application-neutral module, but
it must not own a Qt event loop or matrix lifecycle.

Next wire the existing live and headless capture callbacks through
`QtPreviewRenderCaptureAdapter` and `HeadlessPreviewRenderCaptureAdapter`. Keep widget reads and
canonical renderer/image materialization in their existing composition-root callbacks for this
bounded slice, reuse `PreviewAnalysisEngine`, and preserve every required `qa_evidence_contract`
field, artifact basename, error mapping, and cleanup path. The common result exposes an
`as_mapping()` projection so existing workspace snapshots and CLI summaries remain compatible where
the old path emitted a value. A later scan may rank moving the large callback bodies into the
adapter module, but that is deliberately not part of this accepted slice.

Change `phase3_harness_workspace.py` dependency records so both adapters receive one typed
`PreviewRenderCapturePort`; each `capture_snapshot()` implementation makes exactly one `capture()`
call. Update `phase3_harness.py` composition to build the two environment-specific adapters.
Retain the old private callback functions as the implementation callbacks for this slice, migrate
their production callers to the typed port, and keep the existing payload-compatibility tests until
a future body-extraction slice can retire them safely.

Do not move `_snapshot_signing_request`, signed-output evidence, matrix iteration, Qt application
creation/closure, or `PreviewAnalysisEngine` into the new service. Do not rename any `phase3` CLI,
DTO, JSON, or artifact label in this slice; the separate nomenclature-retirement plan remains the
place for that future atomic migration.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    rg -n "_build_qt_preview_render_capture_payload|_capture_headless_preview_render|capture_preview_render|capture_headless_preview_render" src tests
    .venv/bin/pytest -q tests/unit/test_phase3_preview_analysis.py tests/unit/test_phase3_harness.py tests/unit/test_qt_phase3_harness_workspace.py
    .venv/bin/ruff check src tests

During migration, run the new boundary tests after each adapter is wired. The final commands are:

    .venv/bin/pytest -q
    .venv/bin/ruff check src tests
    git diff --check
    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-preview-matrix --pdf-path artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf --certificate-path artifacts/generated_acceptance_assets/signed_acceptance_identity.p12 --passphrase secret --scenario-manifest-path tests/fixtures/phase3/release_fidelity_manifest.json --artifacts-dir /tmp/foliaseal-preview-capture-preview
    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-acceptance-matrix --pdf-path artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf --certificate-path artifacts/generated_acceptance_assets/signed_acceptance_identity.p12 --passphrase secret --scenario-manifest-path tests/fixtures/phase3/release_fidelity_manifest.json --artifacts-dir /tmp/foliaseal-preview-capture-signed

The two matrices must report 8 scenarios, zero preview error rows, 6 successful signed scenarios,
2 matched intentional rejections, zero cryptographic/annotation/preview-output failures, and
`acceptance_expectations_passed=True`. Remove both explicit `/tmp` directories after inspection and
confirm no FoliaSeal/Qt harness processes remain.

## Validation and Acceptance

Acceptance is behavioral: `Phase3HarnessWorkspaceAdapter.capture_snapshot()` and its headless peer
produce the same existing `render_capture` keys and artifact suffixes as before; required evidence
validation passes; live and headless lifecycles remain separate; and failure/cleanup paths do not
leave dialogs, Qt processes, or temporary directories. Boundary forwarding tests plus the existing
harness/workspace parity suite prove mapping shape and capture sequencing without duplicating the
large artifact implementation. Full suite, Ruff, diff checks, and both release matrices must pass.

The architecture loop will accept the cycle only if the measured proxies show at least `0.15` Actual
Improvement and no component regression below `-0.10`. Baseline proxies are: five implementation
units in the preview workflow, two duplicated capture orchestrators, two untyped callback seams,
and no stable typed capture boundary. Repeat those counts after migration and record the arithmetic
in this plan and the parent. The deferred callback-body extraction remains an explicit residual
candidate rather than an unreported acceptance failure.

## Idempotence and Recovery

Keep the old mapping projection until both adapters and boundary tests are green. If a render or
artifact migration fails, restore only the affected adapter wiring while retaining the typed request
tests; do not change external keys to make a test pass. Matrix artifacts belong only in the explicit
`/tmp` directories above and must be removed after inspection. Never delete a broad workspace path.

## Artifacts and Notes

The durable artifacts are source, tests, docs, and this plan. Generated PNGs, JSON summaries, and
temporary PDFs from the matrices are evidence only and must not be committed. Record concise matrix
summary counts and the final commit hash here before marking the plan complete.

## Interfaces and Dependencies

The selected hybrid requires these stable interfaces:

    class PreviewRenderCapturePort(Protocol):
        def capture(self, request: PreviewRenderCaptureRequest) -> PreviewRenderCaptureResult | None: ...

    @dataclass(frozen=True)
    class PreviewRenderCaptureRequest:
        preview: SigningDraftPreview
        artifacts_dir: str | None
        artifact_basename: str
        workspace: object | None = None

    @dataclass(frozen=True)
    class PreviewRenderCaptureResult:
        mapping: Mapping[str, object]

        # artifact_paths and errors are derived read-only projections over mapping;
        # they are not duplicated storage.

`QtPreviewRenderCaptureAdapter` owns QWidget/testing-panel access and uses the existing canonical
renderer and image analysis. `HeadlessPreviewRenderCaptureAdapter` owns the canonical headless
renderer and the same analysis contract. `Phase3HarnessWorkspaceAdapter` owns only workspace/session
sequencing and delegates capture through the port. No generic registry, optional planner, or new
public CLI command is permitted.
