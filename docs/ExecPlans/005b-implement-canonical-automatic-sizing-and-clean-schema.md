---
role: child
state: planned
parent: 005-simplify-appearance-sizing-and-reset-reusable-signing-objects.md
depends_on:
  - 005a-approve-frozen-automatic-sizing-and-reset-contracts.md
---

# Implement one automatic-sizing pipeline and strict clean reusable schema

This is a living ExecPlan maintained under `/home/daekar/.codex/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

Given an approved policy, a real placement uses readable bounded text and a proportional image, or rejects insufficient space clearly. The same result drives fit checks, Qt preview and signed PDF. Reusable files store only appearance choices and reject old formats.

## Child ExecPlan Dependencies

- [ ] `005a-approve-frozen-automatic-sizing-and-reset-contracts.md`.

## Progress

- [ ] Write failing policy/schema/parity cases using isolated fixtures.
- [ ] Remove persisted manual size/prominence and legacy reusable readers.
- [ ] Resolve text-first automatic size and image allocation once for all rendering consumers.
- [ ] Prove preview/PDF/fit parity and update architecture; complete compliance and commit.

## Surprises & Discoveries

Current source combines a persisted manual-size/prominence model with different text-only/image preview scaling paths. The installed owner has rejected both oversized image cropping and unreadable fitted text. Source geometry/image-presence tests alone have not proved usable typography. Catalog readers also have legacy migration and loose version checks; simply deleting controls would leave old behavior loadable.

## Decision Log

The owner chose automatic text-first sizing and a complete reset rather than preserving old saved choices (conversation on 2026-10-04). No compatibility modes or migration are required. The proposed numeric policy and frozen amendments remain approval-pending until 005a records explicit approval. The implementation uses existing canonical preparation rather than another widget rendering model. Reset is an explicit user-context release step to avoid deleting newly created data on future startup.

## Outcomes & Retrospective

Planning has completed five fresh read-only reviews; identified contract, renderer, DPR and reset gaps were incorporated. The isolated five-plan family passes helper validation; directory-wide historical metadata failures remain recorded, unrelated debt. Implementation has not started; no live user data has been deleted. Owner approval of the concrete frozen packet remains required in 005a. No implementation or release pass is claimed.

## Context and Orientation

Work from `/home/daekar/FoliaSeal`. Governing authority is `docs/SPEC.md`, then `docs/SCHEMAS.md`, then `docs/UI_SPEC.md`; these documents are frozen. `docs/ARCHITECTURE.md` describes current ownership. Follow `/home/daekar/.codex/skills/write-execplan/PLANS.md`. Use the existing Python/PySide6/PyHanko/Pillow stack with no new runtime dependency. A point is 1/72 inch in PDF space. Device pixels are raster resolution, not a text-size policy. The Library minimum is 1000 by 650 logical pixels; the main window minimum is 1100 by 700.

The owner approved simplifying Appearance choices and deleting existing reusable Presets, Appearances, Placements, and their managed image assets, with no compatibility requirement. Certificates, certificate configurations, secret storage, trust settings, application preferences, source image files, recovery records, and existing PDFs are excluded. No signed PDF is rewritten. This planning request does not approve the exact proposed frozen amendments; child 005a must present them and record explicit approval before editing frozen artifacts or activating dependent implementation.

`src/foliaseal/domain/models.py` currently puts font_size_pt in SignatureTextStyle and image_prominence in SignatureAppearance. `src/foliaseal/application/reusable_signing_models.py` serializes both and loosely checks schema versions; `src/foliaseal/infra/config/profile_storage.py` migrates combined legacy profiles. `visible_signature_semantics.py` composes signing fields; `visible_signature_layout.py` owns neutral layout preparation, `visible_signature_layout_adapters.py` injects measurements, `visible_signature_artifact_adapters.py` builds exact PyHanko styles, and `visible_signature_fit_policy.py` / `visible_signature_rendered_fit_adapters.py` own fit decisions/probing. `signing_backend.py`, `signing_preview_renderer.py`, `horizontal_signature_reservation.py`, `signing_draft_contracts.py` and Qt preview consumers project this data. Read the architecture boundary descriptions before edits; retain neutral-core import isolation.

## Milestones

First prove red tests for removal of old serialized fields/versions, largest-fitting candidate, image remaining-region geometry, and unchanged choices across rendering. Remove old reusable migration/default readers and use strict schema-3 validation at catalog and every object envelope, including nested obsolete properties. Define allowlists and reject unknown keys at the catalog, each object envelope and every nested Appearance/text_style/box_style/image_asset/source_page/rect level; reject arbitrary extra keys as well as retired sizing properties. Missing stores yield an empty schema-3 catalog; nonempty unsupported/corrupt files fail explicitly and never overwrite themselves. Empty corrupt files are not silently treated as success.

Next implement the policy at the existing preparation/fit seam, separating persisted font preferences from effective runtime font metrics. An existing internal style/DTO may still carry a resolved point size because rendering needs it; there must be no user-editable or stored size. Resolve complete text including clock once, probe candidates without re-entering semantics/backend preparation, and capture the selected preparation for all materializers. Finish by proving page-preview/signed-annotation parity and failure diagnostics before updating architecture and committing.

## Plan of Work

The 005a spike found a concrete prerequisite: bundled DejaVu Monospace uses 2048 units/em,
while the current PyHanko PDF CID-width emission assumes 1000. Measurement normalizes advances
but the PDF renders excessive spacing and clips complete text. A disposable same-face copy
normalized to 1000 units/em renders correctly. Normalize all four bundled Monospace styles
deterministically, preserving face identity, glyphs, license and metadata; document regeneration
and test units/em plus actual canonical PDF/raster text for regular/bold/italic/bold-italic.
Use the existing FontTools tooling, with no runtime dependency or font fallback. Update font
resource documentation and packaging checks. Resolve fractional measurement boundaries
conservatively so actual rendered extents never exceed the allocated region despite rounding.

Remove SignatureImageProminence, percentage branches, and old fields from first-party models, backend appearance projections, preview DTOs, signatures/kwargs, fixtures, serializers, tests and UI bindings in a coordinated change. Child 005c performs final UI simplification; this child must keep imports/runnable composition green with a thin removal of now-invalid size/prominence controls, not a legacy compatibility adapter. Inventory all consumers with rg before deletion. Do not remove the effective font size required in a prepared raster/text artifact. Name a neutral immutable resolved result (for example ResolvedSignatureSizing) with effective_font_size_pt, text/image allocated rectangles and explicit issues, and attach it to VisibleSignaturePreparation so materializers reuse a captured decision. The exact plan/request consumed by both preview and PDF materializers carries the effective point size and allocated regions; change `build_stamp_style` and its input boundary so neither materializer reads a persisted/preferred size. Do not merely attach an unused DTO.

Candidate selection uses actual measured text, font face/glyph checks, image dimensions/alpha and the actual rectangle. Compute border/gap budgets first. For each descending candidate, preserve complete Compact/Stacked semantics, protect text region, and aspect-fit the image in the remainder; require the approved image floor. Validate actual rendered ink after structural measurement where the existing fit policy requires it. Horizontal ink reservation and rendered-fit probes receive each candidate's effective style and the same candidate geometry. No fallback may accept an allocation violating complete-text fit or the image floor. A spy/call-count test proves candidate probing does not re-enter semantics/backend preparation and uses the candidate size rather than an old default. Do not recursively invoke the canonical renderer through the selector to select itself. Cache keys include resolved font size, actual geometry, text/time, image identity, style and policy revision. No clipping/tolerance branch or compact-image suppression may turn a failed candidate into success. Existing horizontal reservation/rendered-fit code must either consume the same result or be deleted when obsolete.

Implement the approved canonical version-3 JSON shape from 005a, including bounded layout/date/border/statement/visibility mapping, instead of simply relabeling the old source payload version 3. Test a complete canonical round-trip and explicit rejection of retired nested field bindings, source paths, raw format strings and layout enums. Runtime domain mappings may differ from JSON, but serializers must have one unambiguous approved shape.

Update signing confirmation so the selected time and effective sizing are recomputed/captured together and remain fixed for the accepted attempt; stale draft preview sizing is not reused for different data/rectangles. Invisible signatures bypass visible sizing. Failed attempts cannot alter old signed revisions. Update ARCHITECTURE and all current Help claims affected by manual sizing removal. Mixed source plus immediate control-removal is allowed to keep the schema break runnable, but the final visual layout remains child 005c.

## Proposed Shared Behavior

The proposed automatic policy tries 10, 9.5, then 9 pt, selecting the largest candidate that fits the complete actual content and any selected image. These values are application policy, never persisted Appearance properties. Measure using the exact bundled face, including bold/italic, and the actual signing text with the frozen signing time. Reserve border/margins and a text/image gap, then the required text region; give the image the maximal aspect-preserving fit in the remaining region, with its original alpha semantics; no additional prominence cap applies. Compact stays one line without truncation or wrapping; Stacked stays one visible field per line. New Appearances default to Stacked, so the common fields-plus-wide-image example is useful at 10 pt; Compact remains an explicit choice. This default change is part of the first child's frozen approval packet, not a silent implementation adjustment. Never omit a selected field, signing statement, or nonempty selected image to obtain a fit. A selected image must have a displayed shorter side of at least 12 PDF points; if a candidate cannot satisfy this plus text fit, try the next candidate. For Left/Right, reserve the measured text block width across the inner height and put the image region on the chosen side after the approved gap; reject text taller than the inner box. For Above/Below, reserve the measured text block height across the inner width and put the image region above/below after that gap; reject text wider than the inner box. Center the aspect-fitted image in its remaining region; retain left-aligned text and center its block on the orthogonal axis. Margins/gaps are deterministic PDF-point budgets from the canonical layout, not Qt theme pixels; the first child records their exact values before approval. No gap is reserved when either region is absent. Image-only content uses the inner box. A visible signing statement consumes text space when enabled, including image-bearing signatures, but statement-only content remains invalid under the existing meaningful-content rule. Text-only content reserves no image region. Fully transparent (all-alpha-zero) images are empty and rejected at import/save/fit, never accepted by omitting them; opaque white images are not rejected by a color heuristic. This explicit meaningful-image rule is part of 005a approval.

If none fits, report: `This box is too small for the selected content. Enlarge it, choose Stacked, show fewer fields, or remove the image.` Disable signing, preserve the draft, and show a non-success preview state. Unsupported glyphs remain errors, not reasons to shrink or substitute fonts. There is no upward font scaling above 10 pt. Increasing box size provides image space and whitespace rather than large text. For the proposed sample and actual stamp, use 4 PDF pt edge margins and 6 PDF pt text/image gap, increasing edge inset to ceil(border_width_pt / 2) + 1 when larger. These deterministic canonical budgets are part of the approval packet; Qt form spacing separately follows native metrics. Do not introduce a theme/layout framework.

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

Tests show 10 pt when fit, 9.5 or 9 pt only when required, explicit failure below the lower bound, no growth above preferred size, all four image positions, image-only/text-only/signing-statement cases, long field values, unsupported glyphs, transparent images and extreme image aspect ratios. Use synthetic PKCS#12/PDF/image fixtures for actual canonical raster and signed-annotation comparison, and verify the signed PDF signature remains valid. Actual placement resize/order/time/font/image edits invalidate stale preparation. Round-trip version-3 files contain no obsolete choices; version1/2 and restored old properties fail closed. New/repeated save/rename/delete transactions retain stable ids. Run the full commands below and focused tests `tests/unit/test_visible_signature_layout.py`, `test_visible_signature_semantics.py`, `test_signing_preview_renderer.py`, `test_signing_backend.py`, `test_reusable_signing_models.py`, `test_signature_preset_storage.py`, and `tests/integration/test_preview_signed_output_parity.py` and adjacent fit/materializer tests. Include old combined `profiles` migration input, blank/malformed catalog files, arbitrary nested keys and future-version rejection; missing files alone yield a new empty catalog.

## Idempotence and Recovery

Tests and samples use owned temporary roots. Repeat contract edits only within the approved packet and never discard unrelated changes. Source rollback uses ordinary corrective commits, not a destructive git reset. A live reset is intentionally irreversible under the owner's deletion decision; it does not preserve old-object backups. The explicit reset is never rerun after creating new objects without a new deletion request. Authentication or owner acceptance can remain pending with an exact artifact and state recorded; neither elapsed time nor successful automated tests counts as owner approval.

## Artifacts and Notes

Retain the frozen approval reference, actual measurement/raster evidence, commands/results, package identity and reset completion evidence during execution. Planned values above are not observed results. Keep owner signature artwork and personal catalogs out of repository evidence. Primary change classes are contract documentation in 005a, behavior in 005b/005c, and reset/release evidence in 005d; do not mix unrelated changes.

## Interfaces and Dependencies

Use existing injected measurement/preview ports and immutable preparation; no Qt/Pillow/PyHanko dependency enters neutral models/layout. Numeric policy comes from approved 005a and is not duplicated in widgets. Internal resolved font-size output is transient, not backward compatibility. No old-profile import command, fallback version, auto-migration or preservation mode remains.

Revision note: Authored 2026-10-04 after owner approved the simplification and clean deletion scope; exact frozen contract changes await 005a approval.
