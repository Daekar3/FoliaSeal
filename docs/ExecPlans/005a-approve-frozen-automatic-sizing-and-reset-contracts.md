---
role: child
state: active
parent: 005-simplify-appearance-sizing-and-reset-reusable-signing-objects.md
depends_on: []
---

# Approve all frozen automatic-sizing, simplified-editor, and reset contracts

This is a living ExecPlan maintained under `/home/daekar/.codex/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

This first child makes the exact product, data, and interface changes reviewable together so later children do not repeatedly discover frozen conflicts. Its deliverable is an explicit owner-approved contract packet and then the matching frozen revisions; it performs no live deletion and no production sizing implementation.

## Child ExecPlan Dependencies

- [x] No prerequisite ExecPlans.

## Progress

- [x] Complete metric-based disposable examples and settle the numeric proposal for approval (2026-10-05 02:39Z). Synthetic canonical-font PNG/PDF evidence supports 10/9.5/9 pt, 12 pt image floor and 216×72 pt sample. The disposable Monospace correction was checked in all four styles; actual production fixes remain 005b requirements.
- [ ] Present the complete replacement text and normative SVG in an unfrozen approval artifact.
- [ ] Record explicit owner approval for exact files and clauses; only then apply frozen amendments.
- [ ] Reconcile old plan/release dependencies and validate governing documents.

Execution started 2026-10-04. Initial dev-loop context review is complete. Disposable measurements
cover 120 content/font/position/aspect combinations and 24 proposed-layout canonical-font renders,
followed by 24 corrected renders, reduced-size boundaries, image-only/text-only/statement states
and alpha-mask inspection. Monospace measurement/render mismatch was reproduced through the
unmodified canonical preview and corrected in temporary same-face assets in all four styles.
See `docs/design/automatic-appearance-sizing-feasibility.md`. Exact frozen approval remains pending.

## Surprises & Discoveries

Current source combines a persisted manual-size/prominence model with different text-only/image preview scaling paths. The installed owner has rejected both oversized image cropping and unreadable fitted text. Source geometry/image-presence tests alone have not proved usable typography. Catalog readers also have legacy migration and loose version checks; simply deleting controls would leave old behavior loadable.

## Decision Log

The owner chose automatic text-first sizing and a complete reset rather than preserving old saved choices (conversation on 2026-10-04). No compatibility modes or migration are required. The proposed numeric policy and frozen amendments remain approval-pending until 005a records explicit approval. The implementation uses existing canonical preparation rather than another widget rendering model. Reset is an explicit user-context release step to avoid deleting newly created data on future startup.

## Outcomes & Retrospective

005a has completed disposable sizing feasibility and an unfrozen exact approval packet. The initial five plan reviews and two execution compliance reviews informed the proposal. JSON/link/XML, actual image inspection and isolated five-plan family validation passed; historical directory-wide metadata failures remain unrelated debt. Exact owner approval is pending. Production implementation and live reset have not started, and no release or installed acceptance is claimed.

## Context and Orientation

Work from `/home/daekar/FoliaSeal`. Governing authority is `docs/SPEC.md`, then `docs/SCHEMAS.md`, then `docs/UI_SPEC.md`; these documents are frozen. `docs/ARCHITECTURE.md` describes current ownership. Follow `/home/daekar/.codex/skills/write-execplan/PLANS.md`. Use the existing Python/PySide6/PyHanko/Pillow stack with no new runtime dependency. A point is 1/72 inch in PDF space. Device pixels are raster resolution, not a text-size policy. The Library minimum is 1000 by 650 logical pixels; the main window minimum is 1100 by 700.

The owner approved simplifying Appearance choices and deleting existing reusable Presets, Appearances, Placements, and their managed image assets, with no compatibility requirement. Certificates, certificate configurations, secret storage, trust settings, application preferences, source image files, recovery records, and existing PDFs are excluded. No signed PDF is rewritten. This planning request does not approve the exact proposed frozen amendments; child 005a must present them and record explicit approval before editing frozen artifacts or activating dependent implementation.

Frozen files requiring revision are `docs/SPEC.md`, `docs/SCHEMAS.md`, `docs/UI_SPEC.md`, and the UI_SPEC-indexed normative `docs/ui/appearance-profile-editor-exploratory.svg`. SPEC §4 WYSIWYG (around lines 110–121), §7 readiness, and Appearance Profile semantics need the automatic-text-first policy and simpler choice list. SCHEMAS AppearanceProfile canonical JSON/rules currently contain image_prominence and text_style.font_size_pt. UI_SPEC SUR04, §9 image/font/fit rules, readiness, and acceptance scenario 5 require corresponding changes. UI_SPEC §9 explicitly forbids text shrinking and defines prominence percentages. The SVG draws prominence controls and labels its preview balanced. These are contract conflicts, not merely code defects.

Current durable catalog examples and implementation are already inconsistent: catalog/model readers allow arbitrary integer versions; examples use version 2 while actual defaults frequently use 1. This child chooses a single new version 3 for the reusable catalog, AppearanceProfile, PlacementProfile, and SignaturePreset. Certificate/configuration/settings versions remain unchanged. All four envelopes must be exactly version 3; earlier and future versions are rejected, not read, migrated, or partially accepted.

## Milestones

First prototype sizing feasibility with the exact bundled fonts and current measurement adapters in an owned /tmp root, using no production/frozen edits. Compare 10, 9.5, 9 pt at 216 by 72 points using exact bundled Serif and representative Sans Serif/Monospace metrics. Use a small orthogonal set: two-field horizontal and vertical arrangements covering Left/Right/Above/Below, one wide and one tall synthetic image, image-only, text-only, signing-statement-with-fields, and dense/long-value Compact and Stacked failures. Include alpha/empty-image validation. Inspect actual canonical PNG/PDF output, not em-height alone; settle whether the image floor and terminal 9 pt candidate work for these supported cases. Check ordinary-scale output in actual PNG/PDF images. The purpose is to settle the proposed minimum and image floor, not to build a parallel implementation. If the proposals fail practical readability, revise the numeric policy in this packet before requesting approval.

Second write `docs/design/automatic-appearance-sizing-approval.md` and an unfrozen proposed SVG beside it. Include full replacement paragraphs/JSON and a file/section amendment map, not only a high-level summary. State the impact of retaining the current rules: dependent implementation would violate frozen contracts. Request explicit approval once for this concrete packet and stop dependent work while awaiting it. Third apply only the approved revisions and normative SVG, record the approval reference and UTC time, validate links/XML/requirements consistency, and commit the governing change separately.

## Plan of Work

SPEC: revise WYSIWYG, readiness, and Appearance semantics to retain field visibility/order, image/position, Compact/Stacked, font family and bounded secondary styling; define automatic size and clear refusal for insufficient space. Record the owner-authorized break and exact reset exclusions without turning it into a general PDF design feature.

SCHEMAS: remove image_prominence and font_size_pt from Appearance JSON and rules; derive size only from current rectangle/content. Define version-3 catalog/object envelopes and rejection of earlier versions and obsolete properties. Do not introduce persisted auto/fixed modes or migrate old values. Retain ids, pinned flags, reference-only presets, metadata, image assets, certificate references, and placement coordinates. The canonical new JSON follows the existing product-facing shape, rather than blessing the implementation's old nested `appearance`/field-binding payload. Map visible_field_order/hidden_fields, Compact/Stacked, bounded datetime presets, standardized signing statement, background transparency and bounded border thickness to internal runtime values explicitly. Reject stored raw date-format strings, custom field/prefix overrides, image source paths and retired layout names. These existing canonical constraints remain in force; their implementation mapping must be specified in the approval packet, with no general cleanup of unrelated certificate/settings schemas. Define runtime resolved sizing in the ephemeral draft/preparation discussion, not as new durable objects. Record one explicit reset of `${XDG_DATA_HOME:-~/.local/share}/FoliaSeal/Signature Profiles/profiles.json` and its adjacent `signature-images/` directory. The packet records the resolved active-user root read-only and the exact deletion boundary, preserving original source images, certificate stores and all listed unrelated stores. No live reset occurs in this child.

UI_SPEC: replace §9 prominence percentages, manual size range, and no-shrink clause with the complete proposed bounded policy. Clarify that a sample fit error allows Appearance Save if meaningful content exists, but actual-placement fit blocks signing. SUR04 and §9 expose fields/order, image/position, arrangement and font family; group bold/italic, text/background/border colors, border thickness, and transparency in collapsed Style. Time format/zone, field labels, and signing-statement controls retain bounded canonical semantics; ISO UTC visibly selects UTC and disables the zone choice, with a stored ISO UTC/local combination rejected. Border thickness is exactly Thin=1, Medium=2, or Thick=3 PDF pt (default Thin), replacing raw numeric widths. Fully transparent assets are rejected as empty. These clarifications join the frozen amendment set. All retained controls and remain available in a compact Signing details disclosure. No automatic wrap, font fallback, truncation, image omission, or aspect distortion. Define the 3 by 1 inch single preview, logical scale and DPI behavior. Update readiness and acceptance scenario 5 so synthetic Library content differs intentionally from actual data while page preview and PDF share the resolved policy. Viewer zoom is not removed.

Normative SVG: remove prominence and font-size selectors/ratio annotations; show primary arrangement/font-family controls and Style/Signing details disclosures; keep Name/preview/footer sticky and vertical-only form scroll. Show readable text and proportionate image in the representative sample and an insufficient-sample state annotation. Inspect all other normative SVGs and frozen text for repeated old control claims and include every confirmed conflict in the approval packet before asking. Do not change normative governance or scope unrelated to this proposal.

The approval packet enumerates unchanged canonical rules explicitly: eight bounded fields and no custom content; reference-only Presets and explicit clearing of Reason/Location defaults when hidden; exact bundled families and glyph failures; managed normalized immutable images, import limits and shared-asset ownership; alpha/compositing; bounded time presets, default UTC and always-visible zone; localized default-On statement, Compact separators/labels/empty values; solid-color picker capabilities, defaults and bounded border choices. Preserve these while removing only obsolete sizing choices. Cite both SPEC §7 readiness and UI_SPEC WF04 readiness ordering in the amendment map.

Reconcile 004 as superseded for outstanding Appearance acceptance and deletion-preservation scope; do not mark it complete or infer owner acceptance. Identify its active release parents/matrix and make the new family their explicit required dependency in prose, avoiding a dependency cycle. Keep these status edits separate from frozen behavior approval.

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

Approval must cover the full policy, version/reset scope, control removals/grouping, sample geometry/scale, and all frozen file revisions. Validate SVG with Python XML parsing and inspect it visually; validate Markdown references by repository-relative paths. Search governing artifacts for obsolete manual-size, prominence-ratio, never-shrink, and legacy-preservation claims; each remaining occurrence must be historical or unrelated and recorded. No unresolved policy numeric choice or schema/reset scope may be handed to child 005b.

## Idempotence and Recovery

Tests and samples use owned temporary roots. Repeat contract edits only within the approved packet and never discard unrelated changes. Source rollback uses ordinary corrective commits, not a destructive git reset. A live reset is intentionally irreversible under the owner's deletion decision; it does not preserve old-object backups. The explicit reset is never rerun after creating new objects without a new deletion request. Authentication or owner acceptance can remain pending with an exact artifact and state recorded; neither elapsed time nor successful automated tests counts as owner approval.

## Artifacts and Notes

Approval-review checkpoint (2026-10-05 02:39Z): the unfrozen packet is
`docs/design/automatic-appearance-sizing-approval.md`, with proposed SVG
`docs/design/proposed-appearance-editor.svg` and the linked feasibility report/evidence.
Packet SHA-256: `fa12f925f1e2b73af1eaafc34dc59265f0629d9ba2a593eb438cd9fbc90893b8`.
SVG SHA-256: `87e5c08f31de6fab18e335bb47d6c902959d52d2b44ca5658ca34680b1de4113`.
Two read-only compliance reviews found schema/path specificity, inset ambiguity, missing SPEC
reset text, and an initial wireframe grouping issue; these were corrected. JSON parsing/field
partition, local links, SVG XML/render inspection, `git diff --check`, and isolated-family helper
validation passed. No production behavior, frozen artifact, or live user data changed. This
documentation/evidence checkpoint supports the exact approval request; it is not child completion.

Retain the frozen approval reference, actual measurement/raster evidence, commands/results, package identity and reset completion evidence during execution. Planned values above are not observed results. Keep owner signature artwork and personal catalogs out of repository evidence. Primary change classes are contract documentation in 005a, behavior in 005b/005c, and reset/release evidence in 005d; do not mix unrelated changes.

## Interfaces and Dependencies

The packet proposes automatic candidates 10/9.5/9 pt, 12 pt image shorter-side floor, 216×72 pt example at 96 logical DPI, and schema version 3. The first prototype can refine these values only before approval; then synchronize every child description. There is no new runtime dependency or permission to edit frozen artifacts until the owner approves the exact packet.

Revision note: Authored 2026-10-04 after owner approved the simplification and clean deletion scope; exact frozen contract changes await 005a approval.
