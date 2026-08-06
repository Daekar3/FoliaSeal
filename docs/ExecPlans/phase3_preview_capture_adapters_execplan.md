# Isolate Preview Render Evidence Adapters

## Purpose

Deepen the preview-render boundary by moving Qt and headless preview artifact construction out of
`phase3_harness.py` and into a focused render-evidence adapter module. The existing
`PreviewRenderCapturePort` remains the public seam used by the workspace adapters; this slice changes
only the composition and dependency binding behind that seam. Artifact paths, JSON keys, error text,
canonical preview cleanup, preview-analysis values, and all existing phase3 contracts remain stable.

The slice also retires the harness-owned capture orchestration helpers themselves. Low-level widget
and overlay helpers remain available only as explicit dependencies of the adapter until a later scan
proves a smaller, independently valuable seam; no compatibility aliases or duplicate capture paths
are introduced.

## Architecture selection record

- Candidate: preview-capture/render projection in `phase3_harness.py`, selected in parent scan 8 with
  Priority approximately `67.6` and confidence `0.88`.
- Selected design: common-caller optimized Qt/headless render-evidence adapters, shape score
  approximately `91`, Candidate Priority approximately `71.5`, confidence approximately `0.90`.
- Existing `PreviewRenderCapturePort` is intentionally unchanged. The new module owns the two
  render-evidence implementations; the harness supplies a typed dependency bundle at composition
  time so tests can continue to substitute widget probes, analysis engines, and overlay writers.
- Rejected: a broad provider bundle that adds rasterizer/artifact-sink protocols without a current
  caller, and a payload-only builder that leaves headless/Qt artifact policy in the composition root.
- No hybrid was selected: the base design already had the strongest bounded shape and no weakness
  justified a `+5` hybrid gate.

## Interface

```python
@dataclass(frozen=True)
class PreviewRenderEvidenceDependencies:
    render_canonical_signature_preview: Callable[..., Any]
    build_preview_analysis_engine: Callable[[], Any]
    preview_analysis_request_type: type[PreviewAnalysisRequest]
    appearance_snapshot_type: type[SignatureAppearanceSnapshot]
    jsonable_capture: Callable[[Any], dict[str, Any]]
    write_widget_capture_png: Callable[[Any, str], str | None]
    widget_is_visible: Callable[[Any], bool]
    widget_rect_snapshot: Callable[[Any], dict[str, int] | None]
    widget_rect_snapshot_relative_to: Callable[[Any, Any], dict[str, int] | None]
    label_alignment_snapshot: Callable[[Any], str]
    label_pixmap_size_snapshot: Callable[[Any], dict[str, int] | None]
    project_pixmap_bounds_within_label: Callable[..., dict[str, int] | None]
    qt_alignment_flag: Callable[[str], int]
    preview_text_color_rgba: Callable[[Any], tuple[int, int, int, int] | None]
    preview_padding_for_capture: Callable[[Any], int]
    layout_spacing: Callable[[Any], int | None]
    write_stamp_debug_overlay: Callable[..., str | None]
    write_text_debug_overlay: Callable[..., str | None]
    cleanup_canonical_preview_tempdir: Callable[[Any], None]
```

`QtPreviewRenderEvidenceAdapter.capture(...)` and `HeadlessPreviewRenderEvidenceAdapter.capture(...)`
accept the same keyword payload currently passed through `PreviewRenderCapturePort`. They return the
same mapping shape and preserve the same cleanup/error behavior. The adapters do not own workspace
refresh, event pumping, viewer lifecycle, signing, or CLI policy.

## Behavior-preservation map

| Existing behavior | New owner | Acceptance evidence |
|---|---|---|
| Qt canonical snapshot copy and analysis render | Qt evidence adapter | existing Qt workspace capture tests and signed preview parity |
| Qt widget fallback capture and geometry projection | Qt evidence adapter plus injected probes | focused adapter tests and existing widget tests |
| Headless canonical render/copy and analysis mapping | Headless evidence adapter | headless capture tests and signed acceptance |
| Stamp/text debug overlays and diagnostics | adapter calling injected writers | existing overlay tests and artifact assertions |
| Canonical temporary-directory cleanup | adapter calling injected cleanup policy | temp-root audit and existing cleanup assertions |
| `PreviewRenderCapturePort` callback contract | unchanged port/workspace wiring | import isolation, full suite, CLI acceptance |

## Baseline and predicted improvement

Baseline commit: `075007eaa`, clean `main`. `phase3_harness.py` is approximately `2,255` lines;
the two capture functions span roughly lines `874–1410`, while widget/overlay/temp cleanup helpers
continue below them. Qt and headless workspace adapters currently bind callbacks to private harness
functions, so changing artifact policy requires navigating the composition root and its unrelated
snapshot/acceptance logic.

Predicted proxy improvements (0–0.5): navigation friction `0.35`, change amplification `0.40`,
seam-risk reduction `0.40`, boundary-test improvement `0.40`, interface compression `0.30`, cohesion
`0.45`, behavioral-uncertainty reduction `0.30`; predicted Actual Improvement `0.37`.

## Implementation steps

1. Add `preview_render_evidence_adapters.py` with the dependency record and Qt/headless adapter
   implementations. Keep the module free of workspace/session imports and optional Qt imports.
2. Replace the two harness capture bodies with composition wrappers that construct the dependency
   record from current harness collaborators; bind the workspace adapters to those wrappers.
3. Add focused adapter boundary tests for Qt/headless success, unavailable canonical render, widget
   fallback, cleanup, and exact artifact/error mapping. Preserve and adapt existing monkeypatch seams
   without adding compatibility aliases.
4. Update `docs/ARCHITECTURE.md`, this child plan, and the parent ledger with measured results and
   any bounded implementation adjustment. Do not rename phase3 contracts in this slice.
5. Run Ruff, diff checks, focused/full pytest, import isolation, CLI help, offscreen signed acceptance,
   preview parity, and fit rejection. Remove explicit `/tmp` roots and audit FoliaSeal/Python
   processes/dialogs before committing on `main`.

## Acceptance contract

- `PreviewRenderCapturePort`, workspace ports, DTOs, CLI commands, JSON keys, artifacts, and phase3
  nomenclature are unchanged.
- `phase3_harness.py` contains no Qt/headless render-evidence orchestration bodies; it only binds the
  adapter dependency record and retains unrelated snapshot/acceptance composition.
- New adapter module imports without starting Qt or requiring a live `QApplication`.
- Focused tests prove both adapters preserve mapping keys, cleanup behavior, fallback/error paths, and
  dependency substitution. Full suite and all three offscreen matrices preserve prior counts and
  expectations.
- Actual Improvement is at least `0.15`, with no component regression below `-0.10`; worktree is clean
  after intentional commit and no FoliaSeal/Python processes or temporary acceptance roots remain.

## Out of scope

Do not rename phase3 nomenclature, redesign the workspace port, merge signing-backend policy, move
preview analysis internals wholesale, or alter public CLI/JSON/artifact contracts. Do not retain a
second live capture implementation for compatibility.

## Status

- [x] (2026-08-06) Added `preview_render_evidence_adapters.py` with the explicit dependency record,
  Qt/headless adapters, and the retired capture-projection bodies; the harness retains only dynamic
  composition wrappers so existing substitutions remain valid without a duplicate implementation.
- [x] (2026-08-06) Added adapter-forwarding and Qt-free import-isolation tests; existing widget and
  workspace tests continue to exercise the full projection through the new dependency bundle.
- [x] (2026-08-06) Ruff, diff checks, focused tests (`92 passed, 1 skipped`), full suite (`1,057
  passed, 11 skipped, 1 warning`), import isolation, and CLI help checks passed. Offscreen acceptance
  passed signed acceptance (`10` scenarios, `7` successful signings, `3` matched intentional
  rejections), signed preview parity (`18/18`), and signed fit rejection (`3/3`); the explicit
  `/tmp/foliaseal-preview-capture-acceptance` root was removed and no FoliaSeal/Python app process
  remained.
- [x] (2026-08-06) Updated `docs/ARCHITECTURE.md` and the parent ledger. Proxy measures are
  navigation friction `0.35`, change amplification `0.40`, seam-risk reduction `0.40`, boundary
  testability `0.40`, interface compression `0.30`, cohesion `0.45`, and behavioral-uncertainty
  reduction `0.30`; `Actual Improvement = 0.37` versus predicted `0.37`, with no component
  regression below `-0.10`.
- [ ] Committed on `main`; fresh three-explorer rescan remains the next loop step.
