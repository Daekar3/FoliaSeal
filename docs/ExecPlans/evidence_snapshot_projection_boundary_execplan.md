# Centralize Evidence Snapshot Projection and Schema Normalization

## Purpose

Create one Qt/Pillow/PyHanko/filesystem-free projection boundary for the duplicated snapshot readout
policy in `phase3_harness.py` and `phase3_harness_reporting.py`. The new module owns semantic views
and deterministic modern-over-legacy normalization; the harness continues to acquire Qt/PDF evidence
and build JSON payloads, while reporting continues to render Markdown. Existing Phase 3 module names,
CLI commands, JSON keys, artifact paths, and acceptance counts remain unchanged. This is a bounded
post-cap continuation slice; it does not perform the separate phase3 nomenclature migration.

## Baseline and design decision

- Baseline commit: `2703f1bd0fce7bb749ad564764ad8e7c20abf105`.
- Frozen SPEC hash: `d929e189269f0f057c6a72b43fd2d430965a975be720b55139fdb1d92afe282b`.
- Scan Round 29 had two convergent independent reports: about 20 duplicated helpers / 200 lines,
  Priority approximately `72`, confidence `.90`. Drift includes nested versus top-level edge
  distances, `layout_plan` versus legacy layout keys, and `stamp_art_enabled` versus
  `stamp_background_present`.
- Three design reports and two reviewers selected Shape B, a semantic immutable typed projection,
  scoring `89–91`; minimal functions scored about `82`, while a generic manager scored `76–80` and
  was rejected for overreach and cycle risk.

## Exact interface

Add `src/foliaseal/presentation/qt/evidence_snapshot_projection.py` with stdlib-only imports:

```python
@dataclass(frozen=True)
class RenderCaptureView: ...
@dataclass(frozen=True)
class LayoutView: ...
@dataclass(frozen=True)
class ReservationView: ...
@dataclass(frozen=True)
class SnapshotView: ...

def project_snapshot(snapshot: Mapping[str, Any] | None) -> SnapshotView: ...
def project_visible_appearance(snapshot: Mapping[str, Any] | None) -> VisibleAppearanceView: ...
```

`SnapshotView` owns `layout_template`, `stamp_position`, `show_field_names`, field count,
`RenderCaptureView`, `LayoutView`, and `ReservationView`. The views expose immutable values and
formatting helpers for existing report labels: edge distance by key, visible text presence, six-item
text-fragment summary, image-xobject summary, field/rect/bbox/error strings, and output signature
values. Inputs are treated as untrusted mappings; malformed or missing data never raises.

Precedence is explicit and tested: nested `render_capture.edge_distances_px` precedes direct legacy
edge distances; `layout_plan.*` precedes `{background,content}_layout.inner_content_scaling` and
`content_layout.margins.bottom`; `stamp_art_enabled` precedes `stamp_background_present`; nested
`signature_appearance` fields precede absent direct fallbacks. Numeric values accept int/float but not
bool. Absent values preserve current `None`, `0`, `[]`, `"none"`, and `"not captured"` semantics.

## Migration and retirement

1. Add the four frozen views, projection functions, and focused modern/legacy/malformed fixtures.
2. Migrate reporting helpers and harness callbacks to the projection boundary. Keep Markdown wording,
   JSON builders, capture orchestration, and Qt/PDF probes in their current owners.
3. Replace duplicate private helper implementations with direct projection calls or thin local
   adapters only while callers are migrated. Verify with `rg`; no first-party test should depend on
   a deleted helper. Remove duplicate helpers and temporary aliases after boundary tests pass.
4. Update `docs/ARCHITECTURE.md`, this child plan, and the parent ledger. Do not rename any phase3
   path/symbol or alter persisted keys.

## Validation and acceptance

Add boundary tests for current nested-modern, legacy-direct, mixed-precedence, malformed, missing, and
visible-appearance payloads; assert projector idempotence and no-heavy-dependency import isolation.
Run focused harness/reporting/projection tests, full pytest, Ruff, compileall, CLI help, and all three
offscreen evidence matrices. Assert Markdown output and JSON payloads remain byte/field compatible,
signed acceptance remains `10/7`, preview parity `18/18`, and fit rejection `3/3`. Run `git diff
--check`, remove exact `/tmp` evidence roots and canonical-preview directories, audit for FoliaSeal/
Python/Qt processes, and verify no SPEC diff.

Acceptance gates: no skipped or weakened tests; no critical/major findings; Actual Improvement at least
`.15` with no component regression below `-.10`; the new module has no Qt/Pillow/PyHanko/filesystem/
reporting imports; duplicate helpers are retired or their exact remaining consumer is recorded; and a
clean intentional commit is produced.

## Predicted improvement

Predicted components: navigation `.45`, change amplification `.55`, seam reduction `.55`, boundary
test improvement `.60`, interface compression `.45`, isolation `.70`; weighted expected Actual
Improvement approximately `.55`. The main risk is schema-precedence drift, mitigated by golden parity
fixtures and unchanged external payload assertions.

## Out of scope and recovery

Do not move Qt/PDF/render acquisition, Markdown templates, lifecycle orchestration, JSON key names,
CLI commands, or the phase3 nomenclature migration. If the typed views become a generic bag or import
heavy modules, stop and redesign once within the loop; do not restore duplicate helpers without a
documented caller and retirement criterion. If output differs, compare the modern/legacy fixture
projections and restore only the smallest adapter until parity is proven.

## Status

- [x] Plan created after Scan Round 29 and Design Selection 30 on 2026-08-06.
- [x] Constrained typed semantic projection selected; no generic manager or phase3 rename included.
- [x] (2026-08-06) Added immutable projection views and migrated both harness/reporting readout
  paths; duplicate policy now lives behind one pure module with explicit modern/legacy precedence.
- [x] (2026-08-06) Added modern, legacy, malformed, nested-edge, idempotence, and import-firewall
  tests. Focused projection/harness/reporting validation passed (`86` tests); full suite passed
  (`1,115 passed, 1 warning`).
- [x] (2026-08-06) Reconciled architecture ownership, immutable-view/dependency-firewall rules, and
  the harness/reporting responsibility split.
- [x] (2026-08-06) Compileall, Ruff, CLI help, and diff checks pass; `docs/SPEC.md` is unchanged.
- [x] (2026-08-06) Offscreen evidence passed signed acceptance `10/7` with 3 matched rejections,
  preview parity `18/18`, and fit rejection `3/3`; no mismatches, crypto failures, or annotation
  failures. The exact evidence root and canonical-preview directories were removed and no
  FoliaSeal/Python/Qt process remained.
- [x] (2026-08-06) Conservative component measurements are navigation `.55`, change amplification
  `.70`, seam reduction `.65`, boundary-test improvement `.70`, interface compression `.55`, and
  boundary isolation `.85`, for weighted Actual Improvement approximately `.62` versus predicted
  `.55`; no component regression exceeded `-.10` and no critical/major finding remains.
- [x] (2026-08-06) Committed as `4916fa839` (`Centralize evidence snapshot projection`); the
  post-commit worktree is clean.
- [x] (2026-08-16) Fresh post-commit scan confirms the projection module is
  imported by the harness/reporting consumers and its boundary tests remain
  current. Focused projection/harness/reporting validation passes (`82 passed,
  9 skipped, 1 warning`); final parent/release status is reconciled by
  `release_readiness_reconciliation_execplan.md`.
