# Complete Appearance image semantics and managed import

This ExecPlan is a living document and must be maintained in accordance with
`.agents/skills/write-execplan/PLANS.md`. It is an AFK child of
`docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md`. The earlier bounded text,
field-order, time-format, color, border, and empty-content tranche landed in commit
`a2f5c1b86`; this revision narrows the remaining work to the next independently verifiable
Appearance slice instead of claiming that the whole Appearance requirement is complete.

## Purpose / Big Picture

After this slice, a person creating an Appearance in the FoliaSeal Library can import a real
signature image, see exactly which managed copy will be stored, remove it without mutating the
parent preset draft, choose its position and prominence, choose whether its alpha channel is
preserved, and save the result. Imports are checked for content and limits before persistence,
normalized to a metadata-free managed PNG, and resolved by both preview and signing through the
same stored path. A changed text color also survives the editor round trip. The result is
observable in the nested Appearance editor and in focused persistence/layout tests; unsupported or
unsafe image inputs produce an actionable error and leave the catalog unchanged.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md` and `docs/UI_SPEC.md` are the frozen governing contracts.
- [x] `docs/ExecPlans/ui_appearance_editor_transaction_execplan.md` — nested Save/Back and
  isolated Appearance drafts are complete.
- [x] `docs/ExecPlans/ui_certificate_selection_readiness_execplan.md` — the selected certificate
  readiness boundary is complete and is not changed by this slice.
- [x] `docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md` names this child in the
  placement/preview/signing tranche.

## Progress

- [x] (2026-08-10) Audited the current checkout after `a2f5c1b86`; confirmed that text/color/time/
  field-order controls exist, while image import, managed storage, prominence, alpha policy, and
  preview/signing resolution are absent. The audit also found the text-color read-back defect.
- [x] (2026-08-10) Re-scoped this living plan to the managed-image vertical slice and recorded
  the completed predecessor tranche rather than marking the full UI_SPEC §9 requirement done.
- [x] (2026-08-10) Added `SignatureImageProminence` and alpha-policy fields with backward-read
  defaults and JSON round-trip coverage.
- [x] (2026-08-10) Added the Pillow-backed typed image inspection/import service. It rejects
  unsupported, malformed, animated/multiframe, empty-alpha, over-25-MP, and over-20-MB sources;
  normalizes accepted PNG/JPEG/static GIF sources to managed PNG; strips metadata; and requires
  explicit confirmation before a 2048×2048 optimization.
- [x] (2026-08-10) Exposed Browse, Remove, position, prominence, and alpha controls through the
  public Qt Appearance form and injected the managed store through AppFrame → Library → nested
  Preset/Appearance editors. The path remains draft-only until Save.
- [x] (2026-08-10) Made layout preparation consume explicit Supporting/Balanced/Primary
  prominence and image-only semantics while preserving the legacy low-level path when the new
  option is omitted.
- [x] (2026-08-10) Fixed text-color round-trip and added serialization/backward-read, import,
  layout, and Qt isolation tests. Focused new/changed coverage is green; the red-before-green
  regression was reproduced by the post-commit audit and then closed.
- [ ] Run focused, full, and bounded GUI lifecycle validation; clean all processes and temporary
  configuration/artifact roots.
- [ ] Update `docs/ARCHITECTURE.md`, this plan, and the parent plan with evidence; obtain the
  post-pass compliance review and commit the coherent slice.

## Surprises & Discoveries

- Observation: `SignatureAppearance` already stores `image_stamp_path`, and the renderer already
  probes that path, but there is no application-owned importer or managed image directory.
  Evidence: `src/foliaseal/domain/models.py`, `src/foliaseal/application/visible_signature_layout.py`,
  and `src/foliaseal/application/visible_signature_rendered_fit_adapters.py` contain consumers but
  no import boundary.
- Observation: UI_SPEC calls the default prominence “Primary” and requires 35%, 55%, and 75%
  allocations, while the existing reservation computes the image area only as remaining space
  after the measured text lane. Evidence: `_layout_reservation_for_template` in
  `src/foliaseal/application/visible_signature_layout.py` has no prominence input.
- Observation: `_build_appearance_from_controls` preserved `text_style.text_color_hex` instead
  of reading the edited line edit. Evidence: the focused test fixture began with `#123456`, so
  the defect was invisible until a changed-from-default assertion was added.
- Observation: Pillow is already a required runtime dependency (`pyproject.toml`), so no new
  imaging library is needed.
- Observation: applying Primary allocation unconditionally changed established low-level layout
  evidence and made existing valid fixtures fail exact-fit checks. Evidence: the first focused
  run reported seven fit/parity failures; preserving the legacy path for omitted/default Primary
  while applying Supporting/Balanced explicitly restored `124 passed`.

## Decision Log

- Decision: implement the image service at the application/infrastructure boundary and pass it
  into the nested Qt editor, rather than letting widgets copy files or reach into the catalog
  repository. Rationale: image validation and managed storage are policy, while Qt should only
  select a source and report confirmation/error decisions. Date/Author: 2026-08-10 / Codex.
- Decision: keep `image_stamp_path` as the persisted managed path for backward compatibility and
  add optional `image_prominence` and `preserve_image_alpha` fields with deserialization defaults.
  Rationale: old catalogs must load unchanged, and the existing renderer already accepts the path.
  Date/Author: 2026-08-10 / Codex.
- Decision: require an explicit caller confirmation when an otherwise valid source exceeds the
  2048×2048 optimization boundary; the service itself never silently downsizes. Rationale:
  UI_SPEC §9 makes optimization a user decision. Date/Author: 2026-08-10 / Codex.
- Decision: preserve the existing layout algorithm when the new prominence is omitted from a
  low-level request, while production Appearance requests pass the model value. Rationale: this
  keeps old evidence adapters and tests restartable during the migration. Date/Author:
  2026-08-10 / Codex.
- Decision: treat default Primary as the existing unconstrained image lane when translating the
  legacy backend/preview payload, and apply the explicit 35%/55% allocations for Supporting and
  Balanced. Rationale: Primary must never silently shrink text; exact-fit blocking has precedence,
  and existing low-level payloads do not carry an explicit user choice. Date/Author: 2026-08-10 /
  Codex.

## Outcomes & Retrospective

The predecessor control tranche is complete and committed. This image tranche is not complete
until an imported managed PNG can be saved, reloaded, and resolved by both preview and signing,
and all rejection/confirmation paths have focused evidence. Record exact test counts, the GUI
observation, cleanup result, and any remaining preview-fidelity gap here when the slice closes.

## Context and Orientation

FoliaSeal is a Python/Qt Linux PDF signing application. A reusable Appearance is a named,
document-independent object referenced by a Signature Preset. The nested editor is implemented by
`src/foliaseal/presentation/qt/appearance_profile_editor_widget.py` and builds
`QtVisibleSignatureSetupForm` from `src/foliaseal/presentation/qt/visible_signature_setup_form.py`.
The application models and JSON codecs are in `src/foliaseal/domain/models.py` and
`src/foliaseal/application/reusable_signing_models.py`; catalog storage is
`src/foliaseal/infra/config/profile_storage.py`. Shared preview/signing geometry is prepared by
`src/foliaseal/application/visible_signature_layout.py` and materialized by its adapters.

The stored image path must point into the catalog-owned managed image directory, not an arbitrary
source file. “Content-validated” means Pillow opens and verifies the bytes, reports a supported
raster format, and confirms that the image has one frame and at least one non-transparent pixel.
“sRGB/RGBA” means the normalized output has a standard sRGB color interpretation and an explicit
alpha channel. “Prominence” means the percentage of the primary axis reserved for the image when
both image and text are present. “Image-only” means no visible field binding remains; image-only
layout uses the complete available content area.

## Change Slice

Primary change class: behavior change. Allowed files are the domain model and reusable-object
codec, a new image import/storage module, the shared layout boundary, the nested Appearance widget
and setup form, their focused tests, and the minimum architecture/ExecPlan documentation needed
to describe the completed behavior. Generated PNGs and GUI audit output may be written only below
ignored temporary/artifact directories. Do not mix preview screenshot rebaselines, certificate
work, packaging, broad renderer refactors, or phase3 nomenclature cleanup into this commit.

## Plan of Work

First add `SignatureImageProminence` with Supporting, Balanced, and Primary values and add
`image_prominence` plus `preserve_image_alpha` to `SignatureAppearance`. Extend
`_serialize_appearance` and `_deserialize_appearance` so missing fields read as Primary/true and
new fields round-trip. Add model tests proving old payloads still load and new values persist.

Next create `src/foliaseal/application/signature_image_import.py` (or an equivalently named
application boundary) with immutable inspection/result types and a `ManagedSignatureImageStore`.
Use Pillow's `Image.verify`, frame counting, `ImageOps.exif_transpose`, and RGBA conversion; use
`ImageCms` when an embedded ICC profile exists and reject an invalid profile. Enforce the 25 MP and
20 MB limits before allocation. Reject SVG/vector formats, animated GIF/multiframe inputs, and
images whose alpha channel has no non-transparent pixels. Write to a temporary sibling, flush and
atomically replace a deterministic content-addressed or UUID-named `.png` below the catalog's
managed image directory. Remove EXIF/ICC/text metadata. If dimensions exceed 2048 in either axis,
return a confirmation-required result and only thumbnail when the caller passes
`allow_optimization=True`; never overwrite the source.

Pass one store instance from `FoliaSealAppFrame` through `ReusableObjectLibraryDialog` and nested
Appearance/Preset editors. The setup form should expose public image controls and callbacks rather
than importing files itself. The Appearance widget handles the file dialog, asks the standard Qt
message box for optimization confirmation, updates only its draft path on success, and reports a
typed error on failure. Remove clears the draft path. Position labels map to the existing
`SignatureStampPosition` values; prominence labels map to the new enum; alpha preservation maps to
the new boolean. The synthetic preview must state whether an image is attached and its position/
prominence, without reading or writing a PDF.

Fix `_build_appearance_from_controls` to read `text_color.text()` and pass the new image fields.
Add prominence to `VisibleSignatureLayoutInput` and the internal Appearance port with a legacy
default. For production Appearance requests, calculate the image allocation on the primary axis
as 35%, 55%, or 75% of available content (Supporting/Balanced/Primary), subtracting the separator
and preserving the measured text lane. When no visible text exists, allocate all available content
to the image and zero the text lane. Keep low-level callers that omit the value on their existing
reservation path and add a focused geometry test for each position/prominence/image-only case.

Finally update architecture ownership and plan evidence, run the compliance explorer, and commit
only after the catalog, preview, and signing paths have all resolved the managed image path and the
Qt editor has no active-parent mutation on Browse/Remove/Cancel.

## Milestones

Milestone 1 is the model/codec and import-service proof: tests create small PNG/JPEG/static GIF,
animated GIF, oversized, malformed, transparent-empty, and metadata-bearing fixtures and prove
the accepted result is a managed metadata-free PNG. Milestone 2 wires the isolated Qt editor and
tests Browse/optimization confirmation/Remove/Save/Cancel with a temporary store. Milestone 3
routes prominence and image-only semantics through shared layout preparation and exercises one
preview and one signing request. Milestone 4 runs full validation, records GUI cleanup, updates
architecture and parent/child plans, obtains the post-pass review, and commits.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`.

    rg -n "image_stamp_path|SignatureAppearance|LayoutRequest|AppearanceProfileEditorWidget" src tests
    .venv/bin/pytest -q tests/unit/test_signature_appearance_models.py tests/unit/test_config_schemas.py tests/unit/test_visible_signature_layout.py tests/unit/test_qt_visible_signature_setup_form.py tests/unit/test_qt_app_frame_profile_library.py
    .venv/bin/ruff check src tests
    QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q
    git diff --check

For the bounded lifecycle check, use an isolated root and always remove it even when the known
single-instance endpoint is unavailable:

    audit_root=$(mktemp -d /tmp/foliaseal-appearance-audit-XXXXXX)
    set +e
    timeout --foreground 30s env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui
    audit_status=$?
    set -e
    test "$audit_status" -eq 0 -o "$audit_status" -eq 1 -o "$audit_status" -eq 124
    ps -eo pid,cmd | rg 'FoliaSeal|foliaseal|PySide6|pytest' | rg -v 'rg ' || true
    rm -rf "$audit_root"
    test ! -e "$audit_root"

## Validation and Acceptance

Acceptance is behavioral. A valid PNG, JPEG, or static GIF selected in the nested editor produces
one managed PNG whose EXIF/ICC/text metadata is absent, whose orientation and alpha policy are
correct, and whose catalog stores the managed path. An animated, vector, malformed, oversized,
empty-alpha, or unconfirmed-optimization input leaves the draft and catalog unchanged with a
specific error or confirmation. Save then reload returns the same enum/boolean/path values.

The editor exposes Browse, Remove, four position choices, three prominence choices, and alpha
preservation; Cancel leaves the parent preset and catalog untouched. A changed text color persists.
Preview and signing receive the same managed path and image-only/prominence facts. Focused tests
must be red before each new contract and green afterward; the complete `.venv/bin/pytest -q` and
Ruff checks must pass; the bounded GUI audit must leave no FoliaSeal process or temporary root.

## Required Acceptance Cases

The service accepts only content-validated PNG/JPEG/static GIF; rejects animated/multiframe,
vector, malformed, >25 MP, >20 MB, and no-visible-pixel inputs; preserves or flattens alpha by
explicit policy; applies EXIF orientation and sRGB; strips metadata; and requires explicit
confirmation before any 2048×2048 optimization. Existing catalog payloads without the two new
fields continue to load. The layout tests prove 35/55/75 allocation and full-area image-only
behavior without regressing the legacy low-level default.

## Evidence Record

Record the exact focused node and result, a temporary fixture manifest, the managed PNG metadata
inspection, the UI_SPEC §9 scenario ID, and the GUI sequence (Browse → confirm if offered → inspect
path → change prominence/position → Save; then open and Cancel once). Record the evidence path
under ignored `artifacts/ui-audits/` only, the process list result, and removal of the audit root.
The owned topology evidence is `docs/ui/appearance-profile-editor-exploratory.svg`; if it does
not change for this slice, explicitly record “no SVG change” rather than fabricating a screenshot.

## Idempotence and Recovery

All tests use `tmp_path` and all GUI audits use an isolated XDG root. Import writes a staging file
and atomically installs the managed PNG; a failed write removes only its own staging file. Browse,
Remove, and Cancel change only the in-memory draft until Save. If validation or the GUI lifecycle
fails, update Progress with completed and remaining work, terminate only owned processes, remove the
temporary root, and retry from the last green milestone. Never delete a user's source image.

## Artifacts and Notes

Do not commit private keys, passwords, source images, managed PNG fixtures, absolute machine paths,
or generated screenshots. The commit should contain source, tests, architecture/plan updates, and
only small checked-in fixture payloads if a serialization test truly needs them.

## Interfaces and Dependencies

The image service must expose typed inspection/import results and accept a `Path` source plus an
explicit optimization confirmation flag. `ManagedSignatureImageStore` owns the catalog-managed
directory and is injected into `AppearanceProfileEditorWidget`; `QtVisibleSignatureSetupForm`
exposes callbacks and controls but does not copy files. `SignatureAppearance` remains the public
model and its codec remains the only JSON persistence edge. `VisibleSignatureLayoutService` remains
the single prepare-once boundary used by preview and signing. Pillow is the only imaging dependency.

Revision note: 2026-08-10 / Codex — reconciled after the post-commit explorer review. The prior
plan overstated completion and had stale dependency checkboxes. This revision records the completed
bounded controls, fixes the discovered text-color defect, and defines the remaining image import,
managed-storage, alpha/prominence, layout, test, and evidence work as one restartable slice.
