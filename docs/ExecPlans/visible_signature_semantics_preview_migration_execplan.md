# Visible Signature Semantics Preview Migration

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`. It is plan 3 of 5 for GitHub issue #50, "RFC: Deepen visible signature draft semantics boundary." It depends on the foundation and workflow migration plans.

## Purpose / Big Picture

After this slice, canonical preview rendering will no longer reconstruct visible signature stamp text independently. The rendered preview should use text produced by the same semantics boundary as the live draft workflow. Users should see no visual change, but the risk of preview/signing text drift will be lower.

## Progress

- [x] (2026-05-01T18:19Z) Created this ExecPlan as the third issue #50 slice.
- [ ] Confirm `SigningDraftWorkflow.preview()` now receives text from the semantics boundary.
- [ ] Migrate canonical preview stamp-text construction away from `_preview_stamp_text()` duplication.
- [ ] Preserve preview/output parity tests and canonical preview geometry behavior.
- [ ] Run focused preview, layout, workflow, and Qt shell validation and record results here.

## Surprises & Discoveries

- Observation: No preview migration work has started.
  Evidence: this plan was created before code edits for the preview slice.

## Decision Log

- Decision: migrate preview rendering before backend signing.
  Rationale: preview rendering has its own `_preview_stamp_text()` duplicate. Removing that duplicate first lets later backend migration compare final signing against a preview path that already consumes resolved semantics.
  Date/Author: 2026-05-01 / Codex

- Decision: keep canonical raster rendering outside the semantics boundary.
  Rationale: issue #50 is about semantic text and metadata, not Qt/PDF raster rendering. Folding rendering into the semantics service would make the interface broad and expensive for common draft updates.
  Date/Author: 2026-05-01 / Codex

## Outcomes & Retrospective

No implementation outcome yet. At completion, summarize whether `_preview_stamp_text()` was deleted, demoted to a compatibility wrapper, or retained for a documented reason.

## Context and Orientation

`src/foliaseal/application/signing_preview_renderer.py` turns `SigningDraftPreview` into textual preview snapshots and canonical raster previews. A canonical raster preview is an image rendered using pyHanko-style stamp rendering so tests and the UI can compare the preview with signed output.

The current renderer has `_preview_stamp_text(preview)`, which combines `preview.signer_label_prefix`, `preview.title`, and `preview.detail_text` into stamp text. This duplicates the stamp text composition rules in `phase3_signing_backend.py` and should be replaced by semantics-derived text.

The preview renderer also builds a temporary `SigningBackendAppearance` inside `_canonical_preview_layout()`. That construction may remain if it is only an adapter for layout/style rendering, but the stamp text should come from the semantics boundary or from a new field on `SigningDraftPreview` populated by the workflow migration.

## Plan of Work

Choose the smallest contract that prevents duplicate stamp-text composition. Preferred approach: extend `SigningDraftPreview` with a `stamp_text` or `semantic_stamp_text` field populated by `SigningDraftWorkflow.preview()` from `VisibleSignatureSemantics.text.stamp_text`. If adding a new field is too disruptive, add a small public helper in `visible_signature_semantics.py` that converts a `SigningDraftPreview` back into semantics only as a transitional adapter. Prefer the field because it makes the preview payload explicit.

Update `_canonical_preview_layout()` so it uses the semantics-derived stamp text when `include_text` is true. Keep the existing `" "` placeholder for text-suppressed rendering.

Update `_canonical_preview_text_fragments()` and any tests that inspect rendered fragments so they reflect the semantics-derived stamp text. Do not change layout planning, image stamp suppression, bounds inference, or Qt preview sizing in this slice.

Keep `render_signing_preview()` textual summary behavior stable. If it needs the new field, make sure older tests that construct `SigningDraftPreview` directly are updated with the field or given a safe default.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/SignPDF/Scratch

Inspect preview text call sites:

    rg -n "_preview_stamp_text|_canonical_preview_text_fragments|_canonical_preview_layout|SigningDraftPreview\\(" src/foliaseal/application/signing_preview_renderer.py tests/unit/test_signing_preview_renderer.py tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_harness.py

Create or update these files:

    src/foliaseal/application/signing_draft_workflow.py
    src/foliaseal/application/signing_preview_renderer.py
    src/foliaseal/application/visible_signature_semantics.py
    tests/unit/test_signing_preview_renderer.py
    tests/unit/test_signing_draft_workflow.py
    tests/unit/test_qt_signing_shell.py
    docs/ExecPlans/visible_signature_semantics_preview_migration_execplan.md

Run focused validation:

    .venv/bin/ruff check src/foliaseal/application/signing_preview_renderer.py src/foliaseal/application/signing_draft_workflow.py src/foliaseal/application/visible_signature_semantics.py tests/unit/test_signing_preview_renderer.py tests/unit/test_signing_draft_workflow.py
    .venv/bin/pytest -q tests/unit/test_visible_signature_semantics.py tests/unit/test_signing_draft_workflow.py tests/unit/test_signing_preview_renderer.py

Run representative Qt and harness checks because direct `SigningDraftPreview` construction is common in those tests:

    .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py::test_signing_shell_uses_canonical_preview_snapshot_when_assets_are_renderable tests/unit/test_phase3_harness.py::test_capture_preview_render_preserves_gui_preview_and_bordered_analysis_preview

## Validation and Acceptance

This slice is accepted when canonical preview rendering uses semantics-derived stamp text and no longer has an independent text-composition rule that can drift from the workflow. Existing preview geometry tests must still pass. Tests should include a case where a wrapped-block preview with hidden/visible fields renders the same text fragments as the semantics boundary.

## Idempotence and Recovery

This slice can be retried safely. If adding a field to `SigningDraftPreview` causes too much churn, record that discovery here and use a transitional helper while keeping behavior unchanged. Do not change backend signing, final PDF output, or layout reservation policy in this slice.

## Artifacts and Notes

This plan intentionally leaves backend signing text helpers in place. The next plan migrates backend signing after preview is using the semantic text.

## Interfaces and Dependencies

`signing_preview_renderer.py` may depend on `SigningDraftPreview` and the public semantics types, but it must not import new private helpers from `phase3_signing_backend.py` for semantic text. It may continue to use backend pyHanko style objects for canonical rendering until separate layout/backend plans remove them.

Revision note: Created 2026-05-01 by Codex to define the preview migration slice for issue #50.
