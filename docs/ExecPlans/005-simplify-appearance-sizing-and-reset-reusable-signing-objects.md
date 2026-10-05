---
role: parent
state: planned
depends_on: []
---

# Simplify Appearance sizing with one canonical policy and a clean catalog

This is a living ExecPlan maintained under `/home/daekar/.codex/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

Users should choose signing content and arrangement without balancing font-size and image-prominence controls. A normal-size signature must show both readable text and an appropriately fitted image, and a too-small box must fail clearly. This parent coordinates four sequential children; the first obtains approval for every frozen contract change, and the final child deletes the authorized local reusable catalog only after the replacement package is ready.

## Child ExecPlan Dependencies

- [ ] `005a-approve-frozen-automatic-sizing-and-reset-contracts.md`.
- [ ] `005b-implement-canonical-automatic-sizing-and-clean-schema.md`.
- [ ] `005c-simplify-qt-appearance-editing-and-previews.md`.
- [ ] `005d-reset-reusable-objects-and-accept-installed-package.md`.

## Progress

- [ ] Approve the complete frozen-document amendment through child 005a.
- [ ] Implement strict new storage and canonical automatic sizing through child 005b.
- [ ] Replace the Appearance controls and preview through child 005c.
- [ ] Reset authorized user data, install, and obtain human acceptance through child 005d.

## Surprises & Discoveries

Current source combines a persisted manual-size/prominence model with different text-only/image preview scaling paths. The installed owner has rejected both oversized image cropping and unreadable fitted text. Source geometry/image-presence tests alone have not proved usable typography. Catalog readers also have legacy migration and loose version checks; simply deleting controls would leave old behavior loadable.

## Decision Log

The owner chose automatic text-first sizing and a complete reset rather than preserving old saved choices (conversation on 2026-10-04). No compatibility modes or migration are required. The proposed numeric policy and frozen amendments remain approval-pending until 005a records explicit approval. The implementation uses existing canonical preparation rather than another widget rendering model. Reset is an explicit user-context release step to avoid deleting newly created data on future startup.

## Outcomes & Retrospective

Planning has completed five fresh read-only reviews; identified contract, renderer, DPR and reset gaps were incorporated. The isolated five-plan family passes helper validation; directory-wide historical metadata failures remain recorded, unrelated debt. Implementation has not started; no live user data has been deleted. Owner approval of the concrete frozen packet remains required in 005a. No implementation or release pass is claimed.

## Context and Orientation

Work from `/home/daekar/FoliaSeal`. Governing authority is `docs/SPEC.md`, then `docs/SCHEMAS.md`, then `docs/UI_SPEC.md`; these documents are frozen. `docs/ARCHITECTURE.md` describes current ownership. Follow `/home/daekar/.codex/skills/write-execplan/PLANS.md`. Use the existing Python/PySide6/PyHanko/Pillow stack with no new runtime dependency. A point is 1/72 inch in PDF space. Device pixels are raster resolution, not a text-size policy. The Library minimum is 1000 by 650 logical pixels; the main window minimum is 1100 by 700.

The owner approved simplifying Appearance choices and deleting existing reusable Presets, Appearances, Placements, and their managed image assets, with no compatibility requirement. Certificates, certificate configurations, secret storage, trust settings, application preferences, source image files, recovery records, and existing PDFs are excluded. No signed PDF is rewritten. This planning request does not approve the exact proposed frozen amendments; child 005a must present them and record explicit approval before editing frozen artifacts or activating dependent implementation.

The current editor in `src/foliaseal/presentation/qt/appearance_profile_editor_widget.py` uses a 720 by 120 point sample. `signature_preview_lifecycle.py` rasterizes canonically then calls QPixmap.scaled; fitting the full image into a roughly 416 px pane makes 8.5 pt text approximately 5 px high. A readable scrollable text-only sample and a fitted selected-image overview currently have different display rules. `visible_signature_layout.py` allocates 35/55/75 percent image prominence. `domain/models.py` stores font size and prominence in Appearance; `reusable_signing_models.py` serializes them.

`docs/ExecPlans/004-compact-signature-library-editor.md` is active: installed font readability has failed owner review. Its completed compact-header and clipping corrections remain historical evidence. This family supersedes its remaining Appearance acceptance and reusable-data-preservation instructions; it must not claim that 004 passed. During child 005a annotate 004 and its release-matrix callers with the replacement dependency, leaving historical milestones intact and the release gate open.

## Milestones

First execute 005a to draft and secure one owner-approved contract packet; implementation cannot begin while it is planned or blocked. Next execute 005b to remove obsolete storage and resolve automatic geometry in the shared pipeline. Then execute 005c against that policy to simplify the real Qt editor. Finally execute 005d to build from a clean source commit, prove package behavior, reset the exact user-context stores, and obtain installed human acceptance. Each child must record its own passing evidence before being marked complete.

Policy spikes in 005a use disposable examples only and must settle feasibility before owner approval. If implementation uncovers a requirement beyond the approved packet, reopen 005a and seek a narrow approval amendment before touching another frozen contract.

## Plan of Work

Keep contract-only, behavior, and evidence/status commits separate where practical. Generated artifacts allowed are normative SVG revisions approved in 005a, sanitized deterministic PNG/JSON and sample signed PDFs under a dedicated visual-evidence root, and temporary package/audit logs under /tmp. No unrelated security, certificate, timestamp, platform, PDF editing, or broad architecture refactoring is included. Follow the dev-loop compliance/docs/commit gates for each behavior child and qt-gui-work actual-image loop in 005c. No new legacy readers, feature flags, stored sizing modes, or compatibility adapters survive completion.

## Proposed Shared Behavior

The proposed automatic policy tries 10, 9.5, then 9 pt, selecting the largest candidate that fits the complete actual content and any selected image. These values are application policy, never persisted Appearance properties. Measure using the exact bundled face, including bold/italic, and the actual signing text with the frozen signing time. Reserve border/margins and a text/image gap, then the required text region; give the image the maximal aspect-preserving fit in the remaining region, with its original alpha semantics; no additional prominence cap applies. Compact stays one line without truncation or wrapping; Stacked stays one visible field per line. Never omit a selected field, signing statement, or nonempty selected image to obtain a fit. A selected image must have a displayed shorter side of at least 12 PDF points; if a candidate cannot satisfy this plus text fit, try the next candidate. For Left/Right, reserve the measured text block width across the inner height and put the image region on the chosen side after the approved gap; reject text taller than the inner box. For Above/Below, reserve the measured text block height across the inner width and put the image region above/below after that gap; reject text wider than the inner box. Center the aspect-fitted image in its remaining region; retain left-aligned text and center its block on the orthogonal axis. Margins/gaps are deterministic PDF-point budgets from the canonical layout, not Qt theme pixels; the first child records their exact values before approval. No gap is reserved when either region is absent. Image-only content uses the inner box. A visible signing statement consumes text space when enabled, including image-bearing signatures, but statement-only content remains invalid under the existing meaningful-content rule. Text-only content reserves no image region. Fully transparent/empty images follow the existing meaningful-content validation, not a fabricated image reservation.

If none fits, report: `This box is too small for the selected content. Enlarge it, choose Stacked, show fewer fields, or remove the image.` Disable signing, preserve the draft, and show a non-success preview state. Unsupported glyphs remain errors, not reasons to shrink or substitute fonts. There is no upward font scaling above 10 pt. Increasing box size provides image space and whitespace rather than large text. Prefer existing native metric-derived margins and gaps; do not introduce a theme/layout framework.

The Library uses one 216 by 72 point (3 by 1 inch) synthetic example, presented at 96 logical pixels per inch: a 288 by 96 logical-pixel signature inside the preview pane. Preserve this logical display scale across DPR changes; raster at the appropriate resolution without fitting the entire stamp down to the pane. This sample is labeled `Example signature · 3 × 1 in`, uses deterministic synthetic data, and is never saved. If content does not fit this example, show explicit sample-fit guidance but allow saving a meaningful Appearance that could fit a larger real placement. Actual document fit still blocks signing. No preview zoom, sideways detail viewport, duplicate overview/detail panes, automatic box growth, or silent layout switching. The normal PDF viewer zoom remains unchanged.

## Concrete Steps

Run rendering-heavy suites and display captures sequentially. From the repository root run:

    QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q tests/unit
    QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q tests/integration -k 'not real_offscreen_transaction_polls_without_blocking_qt'
    QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q tests/integration/test_signing_transaction_progress.py::test_real_offscreen_transaction_polls_without_blocking_qt
    .venv/bin/python -m ruff check src tests scripts
    git diff --check

Expect passing tests and no new warning/failure; existing skips and the Pillow deprecation warning must be reported rather than hidden. The isolated polling command avoids the previously observed order-dependent integration hang. Do not execute destructive reset as part of an ordinary test; tests use temporary roots and preservation sentinels.

Validate the family with the source-backed helper, using a temporary Cargo target to avoid writing into the skill installation:

    CARGO_TARGET_DIR=/tmp/foliaseal-plan-helper cargo run --quiet --manifest-path /home/daekar/.codex/skills/write-execplan/helper/Cargo.toml -- check --directory docs/ExecPlans

The historical directory contains legacy plans without frontmatter. Record those pre-existing failures explicitly; validate this complete family in an isolated copy of its five files as well as individual source files, without silently migrating unrelated history. A family PASS verifies metadata/status consistency only, not correct behavior.

## Validation and Acceptance

The parent is accepted only when all four child plans are complete, the approved frozen text and current architecture agree, a fresh Library starts empty after the authorized reset, a user creates a new Appearance/Preset and signs a PDF with readable text/image, and subsequent launches preserve newly created objects. The actual placement preview and signed annotation must use the same content, effective font size, layout, alpha behavior, rectangle, and frozen time. Human readability is checked at ordinary PDF viewing scale, not rescued through zoom. Existing on-document navigation/zoom remains normal viewer behavior.

## Idempotence and Recovery

Tests and samples use owned temporary roots. Repeat contract edits only within the approved packet and never discard unrelated changes. Source rollback uses ordinary corrective commits, not a destructive git reset. A live reset is intentionally irreversible under the owner's deletion decision; it does not preserve old-object backups. The explicit reset is never rerun after creating new objects without a new deletion request. Authentication or owner acceptance can remain pending with an exact artifact and state recorded; neither elapsed time nor successful automated tests counts as owner approval.

## Artifacts and Notes

Retain the frozen approval reference, actual measurement/raster evidence, commands/results, package identity and reset completion evidence during execution. Planned values above are not observed results. Keep owner signature artwork and personal catalogs out of repository evidence. Primary change classes are contract documentation in 005a, behavior in 005b/005c, and reset/release evidence in 005d; do not mix unrelated changes.

## Interfaces and Dependencies

Use the existing neutral visible-signature layout boundary and thin Qt adapters. Persist preferences only; computed effective font size and image geometry belong to the per-render preparation result. The existing reusable service remains owner of object transactions, and the reset is an explicit release operation rather than a recurring startup migration.

Revision note: Authored 2026-10-04 after owner approved the simplification and clean deletion scope; exact frozen contract changes await 005a approval.
