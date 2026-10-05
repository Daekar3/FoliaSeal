# Proposed Appearance sizing and reset contract

**Status: Proposed for owner approval. No frozen specification or implementation change is authorized by this document alone.**

This packet presents the exact proposed changes for ExecPlan 005a. The numeric policy is provisional until the disposable renderer spike and owner visual review record measured PDF/PNG evidence. If the spike or rendered review shows that any proposed candidate, minimum image size, or sample scale is not readable and feasible, revise this packet and its proposed SVG before seeking approval. Once approved, the frozen revisions must match this packet exactly or return for approval.

## Decision requested

Approve or reject the complete contract below as one revision set:

- automatic, non-persisted text sizing at the largest fitting candidate from 10, 9.5, and 9 PDF points;
- selected-image minimum displayed shorter side of 12 PDF points;
- a single synthetic 216 × 72 PDF-point example displayed at 96 logical pixels per inch (288 × 96 logical pixels), rasterized at device-pixel ratio without fitting it down to the pane;
- Stacked as the explicit default layout for new Appearances; Compact remains an explicit choice and can legitimately show a non-fit state for a wide image at the 12-point image floor;
- removal of manual font-size and image-prominence settings, with the other controls and disclosures specified below;
- strict schema version 3 for the reusable catalog, `AppearanceProfile`, `PlacementProfile`, and `SignaturePreset`; reject earlier/future versions, unknown keys, and removed fields without migration;
- one explicit reset limited to `profiles.json` and its adjacent managed `signature-images/` directory, under the active user's resolved data root, preserving the excluded data listed below.

The measured spike and final visual review remain required evidence before implementation/release acceptance. Approval settles the rules; it does not claim the code works or authorize running the destructive reset early.

## Exact proposed replacement text

### `docs/SPEC.md` — §4, replace the final V1 appearance paragraph

> Preview/output fidelity is a product principle. If a control or behavior undermines trust between preview and signed output, the product should constrain, move, or remove that control.
>
> V1 should prefer a small number of high-confidence appearance/layout combinations over maximum theoretical expressiveness. Text uses automatic sizing selected from a bounded set for the complete content and actual placement rectangle. The largest candidate that fits is used; size is derived for each prepared signature and is never stored as an Appearance choice. If no candidate fits, signing is blocked with a clear correction. A selected image is aspect-fitted into the remaining space while retaining the same prepared geometry for preview and PDF output.

### `docs/SPEC.md` — §7, append to the readiness behavior

> Appearance readiness includes complete-content layout and fit validation against the actual placement rectangle. Readiness and submit-time validation use the same prepared sizing result and frozen signing time. If the selected content and image do not fit at the minimum supported size, signing remains unavailable and the user is told to enlarge the box, choose Stacked, show fewer fields, or remove the image. The application never omits selected content or silently changes the chosen layout to force a fit.

### `docs/SPEC.md` — `Appearance Profile`, replace its two existing paragraphs

> An `Appearance Profile` captures bounded, signing-specific visible appearance choices. It may include field visibility and order, image selection and position, Compact or Stacked text layout, the bundled font family, and bounded secondary styling. It must not become a freeform design system or general page-composition tool.
>
> Visible content stays semantically tied to certificate/signing metadata. Users may hide fields, reorder fields, choose whether field names and the standardized signing statement appear, and select the image and its position. New Appearances default to Stacked; users may choose Compact explicitly, and fit validation never changes the selected layout. Text size is automatic and depends on the complete current content and placement rectangle. Users cannot save a font size or image prominence. Arbitrary decorative field content, truncation, automatic wrapping, omitted selected content, font substitution, and layout changes made silently to obtain a fit are not part of V1.
>
> Schema version 3 is a deliberate breaking change for reusable data. The application does not migrate, back up, or load prior reusable catalogs or objects. After the replacement package is installed and verified, one explicit active-user reset deletes only the reusable `profiles.json` catalog and its managed `signature-images/` directory, then writes an empty version-3 catalog. Certificates/configurations/secrets, trust and app settings, recovery data, source images, and existing PDFs (including embedded signatures) are preserved. No PDF is rewritten.

### `docs/SCHEMAS.md` — reusable catalog and three object schema sections

All four reusable envelopes use this strict version rule:

> The reusable catalog and each `AppearanceProfile`, `PlacementProfile`, and `SignaturePreset` object have `schema_version` exactly equal to integer `3`. Boolean values do not count as integers for this rule. Readers require exactly the documented keys at each object level; unknown keys, missing keys, older or future versions, and removed properties are validation errors. Every field has the type and allowed values specified below; numeric values must be finite, and IDs/names must be nonempty strings satisfying existing uniqueness and trimming rules. No legacy importer, migration, defaulting of removed choices, or partial load is performed. A missing catalog file is a new empty version-3 catalog in memory; a present blank file, malformed JSON, or wrong top-level JSON type is corrupt and fails closed. Unsupported/corrupt catalogs are reported with reset/recreation guidance. `AppSettings`, managed certificates, and certificate configurations keep their existing versions and readers.

#### Canonical version-3 `AppearanceProfile`

```json
{
  "schema_version": 3,
  "appearance_profile_id": "uuid-or-stable-id",
  "display_name": "Board Approval",
  "pinned": false,
  "text_layout": "stacked",
  "image_position": "left",
  "show_field_names": true,
  "show_signing_statement": true,
  "datetime_format_preset": "compact_numeric",
  "timezone_display_mode": "utc",
  "visible_field_order": [
    "common_name",
    "title",
    "company",
    "signing_time"
  ],
  "hidden_fields": [
    "distinguished_name",
    "email",
    "location",
    "reason"
  ],
  "text_style": {
    "font_family": "Sans Serif",
    "bold": false,
    "italic": false,
    "text_color_hex": "#000000"
  },
  "box_style": {
    "show_border": false,
    "border_color_hex": "#000000",
    "border_thickness": "thin",
    "background_color_hex": "#FFFFFF",
    "transparent_background": false
  },
  "image_asset": {
    "managed_asset_id": "optional-stable-id-or-null",
    "storage_filename": "image_7f4a9b2f.png",
    "original_filename": "wet-signature.gif",
    "width_px": 1400,
    "height_px": 620,
    "has_alpha": true
  }
}
```

`image_asset` is `null` when no managed image is selected. When non-null it has exactly the keys shown. Its managed storage name is an application-owned normalized asset identifier, never an arbitrary path. `font_size_pt` and `image_prominence` are forbidden keys. The inner fields of `text_style`, `box_style`, and non-null `image_asset` also have exact key sets. Existing field enums, bundled-family names, color formats, image metadata, managed-image validation and ownership rules remain in force.

The exact v3 value contract and creation defaults are; every key shown in each JSON example is required even when its value is null or empty:

- `schema_version`: JSON integer exactly `3` (not boolean); object IDs and `display_name`: trimmed nonempty strings; `pinned`: JSON boolean, default `false` on creation.
- `text_layout`: exactly `compact` or `stacked`, with newly created Appearances defaulting to `stacked`. `image_position`: exactly `left`, `right`, `above`, or `below`, default `left`.
- `show_field_names`, `show_signing_statement`, `bold`, `italic`, `show_border`, and `transparent_background`: JSON booleans. `show_field_names` defaults false and `show_signing_statement` defaults true; bold/italic, border, and transparency default off.
- `visible_field_order` and `hidden_fields`: JSON arrays of unique strings from exactly `common_name`, `distinguished_name`, `email`, `title`, `company`, `signing_time`, `reason`, and `location`. The lists are disjoint and together equal the complete eight-field set; the visible array defines order. New appearances start with `common_name` and `signing_time` visible in that order and the other six hidden. No duplicates, overlap, omission, custom keys, field overrides, or raw labels.
- `datetime_format_preset`: exactly `compact_numeric`, `localized_12_hour`, or `iso_utc`, mapping respectively to `2026-08-08 14:35`, `Aug 8, 2026, 2:35 PM`, and `2026-08-08T18:35:00Z`; default `compact_numeric`. `timezone_display_mode`: exactly `utc` or `local`, default `utc`; the resolved zone indicator is always shown. `iso_utc` is valid only with `timezone_display_mode: utc`; selecting it sets UTC and disables the local/UTC control until another date format is selected. A persisted `iso_utc` plus `local` combination is invalid, never silently relabeled.
- `text_style.font_family`: exactly `Sans Serif`, `Serif`, or `Monospace`, default `Sans Serif`; each requested bold/italic combination resolves to the corresponding bundled face. The runtime text size is never serialized. `text_color_hex`, `box_style.border_color_hex`, and `background_color_hex` must match `^#[0-9A-Fa-f]{6}$`; defaults are `#000000`, `#000000`, and `#FFFFFF` respectively.
- `box_style.border_thickness`: exactly `thin`, `medium`, or `thick`, mapped to 1, 2, or 3 PDF points; default `thin`. `show_border=false` means no border regardless of the retained thickness setting. There is no numeric spin-box value or arbitrary width.
- A new Appearance stores `image_asset: null` until the user selects an image. A non-null `image_asset` requires `managed_asset_id` (nonempty string or null), `storage_filename` (managed normalized filename, no path components), `original_filename` (basename only), `width_px` and `height_px` (positive JSON integers, not booleans), and `has_alpha` (boolean). No source path or caller-controlled storage path is allowed. An image whose pixels are all fully transparent is empty: reject it at import/save/fit and never count it as meaningful content. Do not reject opaque white images or infer emptiness from visual color.
- Placement page number is a positive JSON integer (not boolean); page rotation is a JSON integer (not boolean) in 0, 90, 180, or 270 degrees; page dimensions and rectangle coordinates/dimensions are finite JSON numbers, with visible-page dimensions and rectangle width/height positive. Left/Top are nonnegative and the rectangle must be wholly within the source visible page. Preset reference IDs are nonempty strings or null for the optional certificate/placement references; `appearance_profile_id` is a required nonempty string. `reason_default` and `location_default` are required strings, empty when absent. Existing referential integrity, catalog-unique names, and explicit Reason/Location clearing rules remain required.
- The catalog object has exactly these four keys: integer `schema_version` equal to 3, plus JSON arrays `appearance_profiles`, `placement_profiles`, and `signature_presets` containing only their corresponding strict v3 objects. A new/missing catalog is represented by schema version 3 and three empty arrays. An absent catalog is valid as a first-use condition; present blank or malformed catalog content is an error, not an implicit empty catalog.

#### Canonical version-3 `PlacementProfile`

```json
{
  "schema_version": 3,
  "placement_profile_id": "uuid-or-stable-id",
  "display_name": "Purchase Requisition Bottom Right",
  "pinned": false,
  "page_number": 3,
  "source_page": {
    "visible_width_pt": 612.0,
    "visible_height_pt": 792.0,
    "rotation_degrees": 0
  },
  "rect": {
    "left_pt": 360.0,
    "top_pt": 666.0,
    "width_pt": 180.0,
    "height_pt": 54.0
  }
}
```

Nested `source_page` and `rect` objects also require exactly these keys. Existing one-based page, visible-page top-left coordinates, dimensional compatibility, and PDF-boundary transform rules remain unchanged.

#### Canonical version-3 `SignaturePreset`

```json
{
  "schema_version": 3,
  "signature_preset_id": "uuid-or-stable-id",
  "display_name": "Board Approval Default",
  "pinned": false,
  "certificate_configuration_id": "optional-id-or-null",
  "appearance_profile_id": "required-id",
  "placement_profile_id": "optional-id-or-null",
  "reason_default": "optional-string-or-empty",
  "location_default": "optional-string-or-empty"
}
```

The preset remains reference-only. Required/optional reference and Reason/Location-clearing behavior is unchanged.

#### Canonical version-3 `SignaturePresetCatalog`

```json
{
  "schema_version": 3,
  "appearance_profiles": [],
  "placement_profiles": [],
  "signature_presets": []
}
```

The arrays contain only the exact version-3 object shapes above. Empty arrays are valid. The catalog requires exactly these four top-level keys.

#### Rules replacing current Appearance sizing rules

> `text_layout` is `compact` or `stacked`; `image_position` is `left`, `right`, `above`, or `below`. There is no image-prominence property. Font family is exactly one bundled Sans Serif, Serif, or Monospace asset; there is no persisted text-size property.
>
> Each prepared signature measures all selected, nonempty visible content using the chosen bundled family, style, and frozen signing data. It selects the largest fitting size from 10, 9.5, and 9 PDF points. These are application policy values, not object fields. New Appearances default to Stacked. Compact remains one line without wrapping or truncation; Stacked remains one selected field per line. The content inset from each box edge is 4 points when the border is off and `max(4, ceil(border_width_pt / 2) + 1)` points when it is on. Reserve a 6-point text/image gap only when both regions exist. Fit text first, then aspect-fit a selected image into the remaining region. The image's displayed shorter side must be at least 12 PDF points. No selected field, signing statement, or nonempty selected image may be discarded to pass fit validation. Unsupported glyphs remain errors and do not trigger font substitution.
>
> If no candidate fits the actual placement rectangle, signing is blocked with: “This box is too small for the selected content. Enlarge it, choose Stacked, show fewer fields, or remove the image.” The Appearance can still be saved when its content is meaningful even if it does not fit the fixed synthetic example; fit is required at the actual signing placement. Preview, readiness and PDF output consume the same resolved prepared geometry, image alpha behavior, bundled face, and frozen signing time.

The disposable renderer spike measured this representative 216 × 72-point case with bundled Serif: “Ada Example • 2026-01-15 14:30 UTC” in Compact requires 172 points of text width at 10 pt. A 4:1 image requires 48 points of width to meet the 12-point shorter-side floor; with 4-point edge insets and a 6-point gap, the combination cannot fit in the 216-point box at any of the three candidate sizes. The same text in Stacked measures 101 × 21 points; a fitted 101 × 25.25-point image plus the 6-point gap fits within the 64-point inner height at 10 pt. This is expected behavior: Stacked is the default, while the user may explicitly choose Compact and see non-fit guidance; the editor must not silently switch layouts. The main thread inspected the fitting Stacked 10 pt PDF/PNG examples; Compact non-fit is established by all three candidates failing the image floor in the disposable geometry, so there is intentionally no successful Compact raster to present. Review of the actual Qt fit-error message and preview state belongs to 005c after implementation; contract approval does not depend on an unimplemented widget.

The spike found a PDF font-width mismatch for bundled Monospace: source shaping correctly divides advances by the face UPEM, but PDF CID `/W` widths emit raw font units, which PDF interprets as 1000 units per em. The bundled face uses 2048 UPEM, so canonical PDF preview output had excessive letter spacing and clipped text. A same-face disposable normalization to 1000 UPEM has rendered all four Monospace styles readably in canonical output; the main thread inspected the PNGs. The frozen implementation must apply this same-face normalization (or an equivalent PDF width correction), preserve exact family/glyph outlines/license identity, and prove measured bounds agree with rendered PDF/raster ink. Do not substitute system fonts or add/upgrade font dependencies. The corrected disposable renders cover all three families and four image positions, but the production path still requires complete three-family tests and output inspection. See [the feasibility report](automatic-appearance-sizing-feasibility.md), [normalized regular Monospace](automatic-sizing-evidence/normalized-Monospace.png), the four `Monospace-bold*-italic*.png` variants, [the corrected render report](automatic-sizing-evidence/corrected-render-report.json), and [both boundary examples](automatic-sizing-evidence/boundary-report.json).

#### Canonical-to-runtime mapping to document beside these rules

The canonical v3 shape above remains the product-facing persisted shape. Runtime drafts/preparation may use different names, but this mapping is explicit and transient:

| Canonical value | Runtime meaning |
|---|---|
| `visible_field_order` plus `hidden_fields` | The ordered set of enabled canonical field bindings. Every canonical field is either visible once or hidden once; custom field keys and duplicate order entries are invalid. |
| `text_layout: compact` / `stacked` | Map to runtime `SINGLE_LINE` / `MULTI_LINE` respectively. `WRAPPED_BLOCK` is not a valid mapping. |
| `image_position: left/right/above/below` | Map to runtime left/right/top/bottom stamp position, preserving the user-facing Above/Below labels. |
| `datetime_format_preset` | `compact_numeric` renders `2026-08-08 14:35`; `localized_12_hour` renders `Aug 8, 2026, 2:35 PM`; `iso_utc` renders `2026-08-08T18:35:00Z`. Runtime formatting is selected by this bounded enum, never by a persisted/raw format string. |
| `timezone_display_mode` | `utc`/`local` selects the bounded zone policy with UTC default and explicit zone; `iso_utc` requires UTC and its `Z` is the zone indicator. |
| `show_signing_statement` | The standardized localized statement toggle; arbitrary prefix/custom statement text is rejected. |
| `image_asset` metadata | Lookup by managed asset ID/filename within the owned image store. Source paths are never loaded from catalog data. |
| `transparent_background` | `true` preserves existing source alpha; `false` flattens transparent pixels to white; it does not manufacture alpha. |
| `box_style.border_thickness` | `thin`/`medium`/`thick` map to 1/2/3 PDF points; `show_border=false` draws no border. |
| Bounded colors, bold, italic, and family | Map to runtime styling with the exact selected bundled face and glyphs. |
| No `font_size_pt` | A per-preparation resolved candidate derived from actual content and rectangle; never written back to the catalog or draft as a user preference. |
| No `image_prominence` | Aspect-fit into the remaining rectangle after deterministic text-first reservation and gap. |

### `docs/UI_SPEC.md` — SUR04 replacement

> **SUR04 — Appearance editor**
>
> The editor gives most of the surface to a scrollable content form on the left and one sticky synthetic preview on the right. The name remains above the form scroll. New Appearances default to Stacked. The primary controls are visible fields and their order, field-label choice, image selection/removal and image position, Compact or Stacked layout, and bundled font family. Enabling a hidden field appends it to the visible order; disabling it removes it, and enabling it again appends it again. The field-order selector contains only visible fields. Move up/down operate on that order, are disabled at the respective first/last boundary, and are both disabled when fewer than two fields are visible. Changes refresh the actual canonical preview. A collapsed **Signing details** disclosure below those controls contains the bounded date/time format, timezone, and standardized signing-statement controls. Choosing ISO UTC sets the timezone to UTC and disables that selector while ISO UTC is active. A collapsed **Style** disclosure follows it and contains bold, italic, text/background/border colors, border visibility/thickness, and background transparency. There is no font-size or image-prominence control. The scrollable form does not move the name, preview, or Library Save/Cancel footer. Synthetic preview values are visibly labeled and never persisted; the actual on-page preview remains authoritative.

### `docs/UI_SPEC.md` — §9 replacement

> An Appearance is valid only if it can resolve meaningful signing text or a nonempty image. An all-fully-transparent image is empty and is rejected at import/save/fit; it cannot make an Appearance valid or be omitted as a successful fit. Do not use color heuristics to reject opaque white artwork. Border, background, spacing, empty image region, and the standardized signing statement alone do not count.
>
> - Text layout is Compact (one line, no wrapping or truncation) or Stacked (one selected field per line). Image position is Left, Right, Above, or Below. There is no prominence choice.
> - For each complete prepared signature, measure all selected nonempty text with the exact bundled font face, bold/italic style, actual values and frozen signing time. Select the largest size that completely fits from 10, 9.5, and 9 PDF points. No size is persisted or directly user-adjustable. Compact and Stacked never silently change to one another.
> - The content inset from each box edge is 4 points when the border is off and `max(4, ceil(border_width_pt / 2) + 1)` points when it is on. Reserve a 6-point text/image gap only when both regions exist. Fit text first, then aspect-fit the selected image into the remaining region. The displayed image's shorter side is at least 12 PDF points. Do not omit selected content, truncate text, wrap Compact text, substitute a font, distort or silently remove an image. Unsupported glyphs block signing with field/character guidance.
> - If none of the candidates fits the actual placement rectangle, block signing and recommend: “This box is too small for the selected content. Enlarge it, choose Stacked, show fewer fields, or remove the image.” A failed synthetic sample does not prevent saving an otherwise meaningful Appearance, because the actual placement may be larger.
> - The Library shows one synthetic 216 × 72 PDF-point (3 × 1 inch) sample at 96 logical pixels per inch (288 × 96 logical pixels). Preserve that logical size across device-pixel-ratio changes and rasterize at the corresponding device resolution; never shrink the whole stamp merely to fit the preview pane. Label it as synthetic/example content. Show a clear sample-fit state when it cannot fit; do not silently grow the sample, switch layout, zoom, or clip away its detail. Stacked is the default. The user may explicitly select Compact; with a wide image and full Compact text, that selection can yield the sample-fit state. There is one readable preview, not separate overview and detail previews.
> - The actual document preview, readiness/fit validation and PDF output use the same resolved preparation, exact bundled font, geometry, alpha behavior and frozen signing time. Viewer zoom behavior is unchanged.
>
> Image import normalization, limits, alpha/compositing, font-family assets and glyph policy, bounded time formats/timezone, localized signing statement, color picker behavior, and border defaults remain as currently specified. An image with all alpha values zero is rejected at import/save/fit; opaque white images are accepted without color-based heuristics. Text color/background/border color remain solid colors; transparency remains only the existing background compositing choice.

The implementation uses the single edge-inset formula above (not additive 4-point and border reserves), conditional 6-point text/image gap, and three-value border-width mapping. These values are part of the proposed frozen policy.

### `docs/UI_SPEC.md` — readiness and acceptance scenario 5

Append to WF04's readiness-order sentence:

> Appearance content/glyph/image/fit is evaluated using the complete actual placement rectangle and the same resolved preparation later frozen at submit time. A sample-fit message is advisory for editing; actual-placement fit failure blocks readiness and signing.

Replace acceptance scenario 5 with:

> The synthetic Library sample is deterministic, labeled, and never persisted. The actual on-page preview and signed PDF use the same selected content, managed image alpha behavior, bundled font, automatically resolved complete-content geometry, and frozen signing time; unsupported glyphs or actual-rectangle overflow block signing before submission. Previewing at a different device-pixel ratio preserves the sample's logical dimensions and does not shrink its contents to the available pane.

### Proposed normative SVG

The proposed arrangement is shown in [`proposed-appearance-editor.svg`](proposed-appearance-editor.svg). It removes the prominence selector, keeps the name and preview sticky, puts primary arrangement/family controls and the collapsed Signing details/Style disclosures inside the left scrollable form, and gives Stacked the default selection. The active interface shows one 3:1 sample that fits in Stacked; an annotation below and outside the interface shows Compact's non-fit state with a wide image. It is a proposed topology and hierarchy, not a pixel specification. It becomes normative only after owner approval and transfer into `docs/ui/appearance-profile-editor-exploratory.svg`.

## Exact amendment map

| Frozen file | Required amendment | Current conflict to remove |
|---|---|---|
| `docs/SPEC.md` | §4 WYSIWYG policy; §7 readiness; Appearance Profile retained/removed choices, Stacked default, and explicit data break/reset exclusions | General expressiveness wording does not specify sizing; current behavior can be interpreted as allowing any controls. |
| `docs/SCHEMAS.md` | Reusable catalog and Appearance/Placement/Preset envelopes/rules; current implementation drift note if it advertises legacy loaders as acceptable | Appearance currently persists `image_prominence` and `text_style.font_size_pt`; Placement/Preset examples are v2; catalog/object readers are not exact-version/strict-key contracts. |
| `docs/UI_SPEC.md` | SUR04; §9 complete numeric/rendering behavior including Stacked default, fit, transparent-image invalidity, bounded border values and ISO/UTC behavior; WF04 readiness; acceptance scenario 5 | SUR04 is generic; §9 allows 35/55/75 prominence, 6–48 pt, and “Text never silently shrinks”; scenario only says overflow blocks. |
| `docs/ui/appearance-profile-editor-exploratory.svg` | Remove its existing prominence selector and revise secondary-control grouping; show a fitting Stacked sample and separate Compact non-fit note | The drawing includes prominence choices and does not visualize automatic sizing, sample scale, or sample non-fit behavior. It has no distinct font-size widget; the 6–48 pt restriction is text in frozen UI_SPEC §9. |

The cross-document scan is complete: the Appearance-profile SVG contains the actual prominence selector; other `font-size` matches in normative SVGs are drawing/CSS typography, and other prominence words refer to image visibility or action hierarchy. Frozen `UI_SPEC.md` §9 contains the 6–48 pt manual-size rule and no-shrink sentence. No additional frozen control claims were found. Do not change viewer zoom, placement geometry, image import rules, certificate/configuration/settings schemas, or unrelated layout contracts.

## Constraints that remain frozen

- Eight bounded signing fields only: Common Name, Distinguished Name, Email, Title, Company, Signing Time, Reason, and Location. No custom content. Reason/Location defaults must be explicitly cleared if their fields are hidden.
- Presets remain reference-only compositions. Managed images remain normalized immutable PNGs, source-path-free, with existing import limits, alpha semantics and shared-reference ownership.
- Exact bundled Sans Serif, Serif, and Monospace assets remain. Missing glyphs are errors; never use silent system-font fallback.
- Compact separators, label behavior, empty-value behavior, standardized localized signing statement, default UTC, and always-visible timezone indicator remain.
- Preserve existing color picker capabilities, black text/border defaults, white background default, border-off/Thin defaults, and transparency/compositing semantics. Remove image prominence, font size, and freeform numeric border width; retain the three explicitly bounded border thickness choices.
- The normal PDF viewer keeps its zoom controls/behavior. The proposal removes zoom from the Appearance sample only.
- Sample-fit is an editing message; inability to fit a real placement is a signing/readiness blocker. An Appearance with meaningful content remains saveable when it fails only the fixed synthetic example.
- No font growth above 10 pt. No automatic wrapping, truncation, font fallback, content omission, image distortion, or silent layout switching.
- No compatibility/migration path for old reusable objects. Reset is a separate, explicit active-user release action after the new package is ready.

## Exact reset boundary

The current store resolves `XDG_DATA_HOME` when present, otherwise `$HOME/.local/share`. For the active owner, resolve and validate that root before any operation; an explicitly supplied but relative `XDG_DATA_HOME` is an error. The only deletion targets are:

1. `${resolved_data_home}/FoliaSeal/Signature Profiles/signature-images/` — the complete application-managed image directory and its owned files;
2. `${resolved_data_home}/FoliaSeal/Signature Profiles/profiles.json` — the one reusable catalog, replaced only after image removal succeeds with an empty strict version-3 catalog.

The exact catalog path is `$XDG_DATA_HOME/FoliaSeal/Signature Profiles/profiles.json` when `XDG_DATA_HOME` is set to an absolute path, otherwise `$HOME/.local/share/FoliaSeal/Signature Profiles/profiles.json`; `signature-images/` is its sibling directory. An explicitly set empty or relative `XDG_DATA_HOME` is rejected, not interpreted as the default. A read-only resolution on 2026-10-04 found euid/uid 1000, `HOME=/home/daekar`, unset `XDG_DATA_HOME`, and the exact targets `/home/daekar/.local/share/FoliaSeal/Signature Profiles/profiles.json` and `/home/daekar/.local/share/FoliaSeal/Signature Profiles/signature-images/`; both targets exist, are owned by uid 1000, and have no symlinked user-path components. The inventory inspected target/path metadata only, not catalog contents, and deleted nothing. The release utility runs as the active non-root owner and requires `uid == euid`, absolute resolved `HOME` and any set `XDG_DATA_HOME`. It checks symlinks/ownership from the user data root through the targets (system-owned ancestors such as `/home` are not required to be user-owned); a root/euid mismatch, relative value, symlink in a checked component, or unexpected target type fails before mutation. It inventories these exact absolute targets, refuses unexpected subdirectories inside the image store, and treats a missing image directory or catalog as empty. It removes owned images before atomically writing the new empty version-3 catalog; if image removal or catalog replacement fails, report the partial state and require explicit rerun before any app session can write. Install and verify the audited package before reset; keep the app closed until reset succeeds. Authentication timeout leaves existing user data intact. Require explicit `--apply`. It is never a startup hook or Debian post-install action, and it never automatically acts on a future/new data root.

Preserve certificates, certificate configurations and managed certificate files under `FoliaSeal/Certificates/`; secrets/credential-store entries; application configuration and settings; trust settings; recovery journals/records; source image files outside `signature-images/`; all PDFs and embedded signatures; all other files under `FoliaSeal/`. Never delete the enclosing `FoliaSeal/` or `Signature Profiles/` directory wholesale. Do not retain backups or deleted catalog contents. Stop the app before release reset and do not let it write during the operation. An interrupted removal requires rerunning the explicit reset before opening the app. This approval covers deletion of the named reusable data at release after package acceptance gates; it does not authorize deletion of any other user's profile or data root.

## Approval record

- Owner decision: **pending**.
- Approved packet revision/hash: pending.
- Approval date/time (UTC): pending.
- Renderer spike evidence reference: pending.
- Frozen edits must not begin until the owner has approved this exact packet revision after reviewing the recorded spike and wireframe.
