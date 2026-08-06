# Extract the preview-widget evidence policy boundary

This living ExecPlan is the Cycle 4 child of
`docs/ExecPlans/architecture_improvement_loop_parent_execplan.md`. It is intentionally one slice:
extract shared preview geometry, scalar snapshot, and overlay-coordinate policy from the harness
composition root without changing the Qt/headless lifecycles, artifact schema, or public names.

## Purpose / Big Picture

`phase3_harness.py` still owns a large cluster of reusable preview evidence helpers. After this
slice, `presentation/qt/preview_widget_evidence.py` owns the shared duck-typed geometry, text-color,
pixmap-projection, and overlay-coordinate policy. The harness remains the composition root and keeps
Qt ancestor mapping, canonical rendering, artifact writing, and matrix orchestration local. This is
the constrained hybrid selected by two independent design reviews: deeper ownership without a
speculative generic renderer or live/headless lifecycle unification.

## Progress

- [x] (2026-08-05) Fresh post-commit scans ranked the residual preview/widget evidence cluster above
  threshold (`~66.5`, `~65.7`) and identified backend fit-policy extraction as a lower alternative.
- [x] (2026-08-05) Compared minimal relocation, flexible ports/adapters, common-caller unification,
  and constrained hybrid designs. Selected the constrained hybrid (23/25 local safety score; 90.1
  provisional review score).
- [x] (2026-08-05) Added `preview_widget_evidence.py` and routed shared geometry/color/projection/
  overlay helpers through it. Qt alignment resolution and ancestor mapping remain local.
- [x] (2026-08-05) Added focused pure-helper tests and preserved existing harness/workspace parity
  coverage.
- [x] Run full validation and release matrices, reconcile architecture docs and parent plan, measure
  improvement, and clean generated evidence. Commit and the next fresh scan are tracked by the
  parent loop.

## Decision Log

- Keep `phase3_harness.py` as orchestration. Do not move canonical render acquisition, Pillow file
  writers, Qt event-loop ownership, or headless/interactive lifecycle code in this slice.
- Keep the new module under `presentation/qt`: it is presentation policy and must not leak Qt,
  Pillow, or pyHanko imports into `foliaseal.application`.
- Use direct imports rather than compatibility aliases. The extracted helpers have no external
  consumers, so retaining duplicate legacy implementations would be cruft.

## Interfaces

The module exposes pure, duck-typed helpers: `widget_rect_snapshot`, `size_hint_snapshot`,
`label_pixmap_size_snapshot`, `label_alignment_snapshot`, `project_pixmap_bounds_within_label`,
`preview_text_color_rgba`, `draw_overlay_rect`, and `offset_rect`. The projection helper receives an
injected `alignment_flag(name)` callback so PySide6 resolution remains at the Qt edge.

## Validation and Acceptance

Acceptance requires unchanged preview evidence mapping/artifact names, separate Qt/headless
lifecycle behavior, no application import leak, and measured Actual Improvement >= `0.15` with no
component below `-0.10`. Run:

    .venv/bin/pytest -q
    .venv/bin/ruff check src tests
    git diff --check
    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-preview-matrix --pdf-path artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf --certificate-path artifacts/generated_acceptance_assets/signed_acceptance_identity.p12 --passphrase secret --scenario-manifest-path tests/fixtures/phase3/release_fidelity_manifest.json --artifacts-dir /tmp/foliaseal-widget-evidence-preview
    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-acceptance-matrix --pdf-path artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf --certificate-path artifacts/generated_acceptance_assets/signed_acceptance_identity.p12 --passphrase secret --scenario-manifest-path tests/fixtures/phase3/release_fidelity_manifest.json --artifacts-dir /tmp/foliaseal-widget-evidence-signed

The matrices must report 8 scenarios, zero preview errors, 6 successful signings, 2 expected
rejections, zero cryptographic/annotation/preview-output failures, and
`acceptance_expectations_passed=True`. Remove both explicit temporary directories and confirm no
FoliaSeal/Qt/pytest processes remain.

## Out of Scope

No CLI/DTO/JSON/artifact rename, no `phase3` public nomenclature migration, no canonical renderer
or backend fit-policy redesign, no generalized widget port, and no GUI redesign. The separate
`phase3_nomenclature_retirement_execplan.md` remains the atomic naming migration plan.

## Outcomes & Retrospective

Implementation completed on 2026-08-05. Shared geometry, scalar widget snapshots, text-color
parsing, pixmap projection, and overlay-coordinate policy now live in
`preview_widget_evidence.py`; the harness retains environment-specific Qt mapping, canonical
rendering, artifact publication, and orchestration. The public phase3 contracts and separate
live/headless lifecycles are unchanged.

Evidence: focused tests plus harness/workspace parity passed; full suite `1046 passed` with one
pre-existing Pillow warning; Ruff and `git diff --check` passed. Preview matrix: 8 scenarios, 0
error rows. Signed matrix: 8 scenarios, 6 successful signings, 2 matched intentional rejections,
zero cryptographic/annotation/preview-output failures, and `acceptance_expectations_passed=True`.
Temporary matrix directories were removed and no FoliaSeal/Qt/pytest process remained.

Using the parent formula, navigation `0.0`, change amplification `0.5`, seam reduction `0.5`,
boundary-test improvement `0.25`, interface compression `0.5`, and boundary isolation `0.5` yield
`Actual Improvement = 0.30`; predicted `0.25`, accuracy `1.20x`, no component below `-0.10`.
