---
role: child
state: planned
parent: 005-simplify-appearance-sizing-and-reset-reusable-signing-objects.md
depends_on:
  - 005b-implement-canonical-automatic-sizing-and-clean-schema.md
---

# Simplify the Qt editor around one readable representative signature

This is a living ExecPlan maintained under `/home/daekar/.codex/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

A user sees one readable example and a compact set of meaningful Appearance choices. The form fits the Library minimum, selected-image composition does not make typography microscopic, and invalid sample content is explained instead of scaled down.

## Child ExecPlan Dependencies

- [ ] `005b-implement-canonical-automatic-sizing-and-clean-schema.md`.

## Progress

- [ ] Capture deterministic baseline and specify visual discrepancies.
- [ ] Remove manual sizing/prominence and dual preview paths; compose simple primary and secondary controls.
- [ ] Exercise actual PDF placement and bounded visual correction loop.
- [ ] Complete full validation, compliance, docs, and focused commits.

## Surprises & Discoveries

Current source combines a persisted manual-size/prominence model with different text-only/image preview scaling paths. The installed owner has rejected both oversized image cropping and unreadable fitted text. Source geometry/image-presence tests alone have not proved usable typography. Catalog readers also have legacy migration and loose version checks; simply deleting controls would leave old behavior loadable.

## Decision Log

The owner chose automatic text-first sizing and a complete reset rather than preserving old saved choices (conversation on 2026-10-04). No compatibility modes or migration are required. The proposed numeric policy and frozen amendments remain approval-pending until 005a records explicit approval. The implementation uses existing canonical preparation rather than another widget rendering model. Reset is an explicit user-context release step to avoid deleting newly created data on future startup.

## Outcomes & Retrospective

Planning has completed five fresh read-only reviews; identified contract, renderer, DPR and reset gaps were incorporated. The isolated five-plan family passes helper validation; directory-wide historical metadata failures remain recorded, unrelated debt. Implementation has not started; no live user data has been deleted. Owner approval of the concrete frozen packet remains required in 005a. No implementation or release pass is claimed.

## Context and Orientation

Work from `/home/daekar/FoliaSeal`. Governing authority is `docs/SPEC.md`, then `docs/SCHEMAS.md`, then `docs/UI_SPEC.md`; these documents are frozen. `docs/ARCHITECTURE.md` describes current ownership. Follow `/home/daekar/.codex/skills/write-execplan/PLANS.md`. Use the existing Python/PySide6/PyHanko/Pillow stack with no new runtime dependency. A point is 1/72 inch in PDF space. Device pixels are raster resolution, not a text-size policy. The Library minimum is 1000 by 650 logical pixels; the main window minimum is 1100 by 700.

The owner approved simplifying Appearance choices and deleting existing reusable Presets, Appearances, Placements, and their managed image assets, with no compatibility requirement. Certificates, certificate configurations, secret storage, trust settings, application preferences, source image files, recovery records, and existing PDFs are excluded. No signed PDF is rewritten. This planning request does not approve the exact proposed frozen amendments; child 005a must present them and record explicit approval before editing frozen artifacts or activating dependent implementation.

The editor owner is `src/foliaseal/presentation/qt/appearance_profile_editor_widget.py`; shared controls live in `visible_signature_setup_form.py`, host/footer in `app_frame_profile_library.py`, and Qt raster lifecycle in `signature_preview_lifecycle.py`. The installed-review correction currently uses a selected-image fitted overview plus a separate wider text-only horizontally scrollable path and a resize timer. These paths are temporary complexity to remove, not a target to preserve. `scripts/capture_compact_library_layout.py` and `tests/integration/test_appearance_editor_preview.py` already provide deterministic Qt evidence. Existing narrow clipping corrections (filename separate from actions, label attachment, fixed footer) remain valid.

## Milestones

Capture the current real-X11 client with isolated synthetic data and inspect the actual images. Then replace the layout and sample geometry according to 005a, consuming 005b rather than implementing another widget sizing algorithm. Capture default two-field image, reordered fields, selected-image and scrolled/Style-expanded states at equivalent font/style/DPR. Each material finding reopens implementation and requires fresh capture and actual PNG review. Limit autonomous candidates to three, then ask the owner about unresolved visual judgments without declaring acceptance.

Finish with real PDF placement proof at ordinary viewing scale. Check both allowed automatic reductions and too-small-box errors. Run geometry/keyboard/behavior tests, independent compliance and architecture/style/Help updates, and commit only after the visual gate passes.

## Plan of Work

Remove font-size and image-prominence controls throughout the Appearance and workspace refinement surfaces, not merely hide them. Keep fields/order, image controls/position, Compact/Stacked and exact family directly available. Style is initially collapsed and owns bold/italic, color/background/border/alpha settings; border thickness is Thin=1, Medium=2, or Thick=3 PDF pt, not a raw numeric width; Signing details contains time format/zone, label display and signing statement choices. The field-order selector lists visible fields only; enabling a field appends it, disabling removes it, and reenabling appends it again. Disable Move up/down at first/last bounds and both for fewer than two visible fields. Preserve value edits and dirty Save/Discard/Continue semantics when sections collapse. Do not turn collapsed settings into reset operations.

Replace the 720×120 pt synthetic rectangle with approved 216×72 pt geometry and stable 96 logical-DPI display. The 3×1 inches describe PDF geometry; 96 logical px/in is an application display convention, not a guarantee of physical monitor inches or a constraint on future placement dimensions. Render at DPR-adjusted pixel resolution and display the same logical sample scale; never downscale an entire signature to rescue fit. The single preview shows the canonical composition or an explicit sample-fit error. Remove numbered detail duplication if it is not needed to show actual order; if retained, it must not substitute for readable canonical font/image output. No zoom controls, horizontal detail viewport, dual overview/detail, or fixed scale controlled by selected-image presence. Delete obsolete preview-scroll policy and resize rerender mechanisms when the stable scale makes them unnecessary. Preserve lifecycle cleanup and refresh on changes.

Keep vertical-only form scrolling with Name, preview and Library footer stationary. Managed filenames cannot impose minimum row width; Browse/Remove are fully reachable even for a long digest/UUID filename and larger native fonts. Restore no silent image cropping or alpha flattening. Extend safe capture states with long basename, Left image/two fields, all positions, no-image/Stacked, long text/nonfit, and Style-expanded scrolling; retain only representative sanitized images and JSON, not owner signature art or personal catalogs.

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

At 1000×650 with system font/palette, the full signature image and ordinary 9–10 pt text are both legible at the agreed sample scale. No horizontal scrollbar occurs in the form or sample. Changing field order changes the actual canonical raster, not only labels; rendering tests compare real raster content with updated semantics. At DPR 1 and 2, the sample remains 288×96 logical pixels with 288×96 and 576×192 backing rasters respectively. Verify QPixmap devicePixelRatio metadata or an equivalent explicit pixel/logical mapping, not only a zoom argument. Save/Cancel dirty handling, nested Preset editor return, keyboard focus and action access remain correct. Sample nonfit does not prevent Save of meaningful content; the actual tiny placement prevents signing and gives remedies. Open actual default/reordered/image/scrolled PNGs; code or JSON alone is insufficient. Run focused topology/preview/image lifecycle tests and the full command set below.

## Idempotence and Recovery

Tests and samples use owned temporary roots. Repeat contract edits only within the approved packet and never discard unrelated changes. Source rollback uses ordinary corrective commits, not a destructive git reset. A live reset is intentionally irreversible under the owner's deletion decision; it does not preserve old-object backups. The explicit reset is never rerun after creating new objects without a new deletion request. Authentication or owner acceptance can remain pending with an exact artifact and state recorded; neither elapsed time nor successful automated tests counts as owner approval.

## Artifacts and Notes

Retain the frozen approval reference, actual measurement/raster evidence, commands/results, package identity and reset completion evidence during execution. Planned values above are not observed results. Keep owner signature artwork and personal catalogs out of repository evidence. Primary change classes are contract documentation in 005a, behavior in 005b/005c, and reset/release evidence in 005d; do not mix unrelated changes.

## Interfaces and Dependencies

Keep Qt as a thin adapter around approved automatic application preparation and canonical preview lifecycle. Update GUI_STYLE_GUIDE and ARCHITECTURE through architecture-steward; no shared metrics/theme framework or runtime dependency. New evidence belongs to `docs/visual-evidence/automatic-appearance-sizing/` with environment/geometry metadata, sample point dimensions, resolved font size and actual image rectangle.

Revision note: Authored 2026-10-04 after owner approved the simplification and clean deletion scope; exact frozen contract changes await 005a approval.
