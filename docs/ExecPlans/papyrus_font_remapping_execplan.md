# Papyrus Font Remapping ExecPlan

Superseded:

- Product scope changed after this plan was written.
- User-facing font choices are now intentionally limited to `Sans Serif`, `Serif`, and
  `Monospace`.
- This plan remains historical context only and should not be executed unless that decision
  changes.

## Goal

Replace the current misleading `Fantasy` family with an explicit `Papyrus`
family backed by a real bundled Papyrus-style asset.

This slice has two linked objectives:

1. add a genuine Papyrus-like bundled font asset
2. rename the exposed family from `Fantasy` to `Papyrus`

The rename is part of the fix. The current `Fantasy` label is not carrying its
weight, and the existing implementation behind it is not Papyrus-like.

## Current Problem

The current mapping is explicit but wrong for the intended design direction:

- [`src/foliaseal/application/signature_font_registry.py`](/home/daekar/FoliaSeal/src/foliaseal/application/signature_font_registry.py)
  maps `Fantasy` to `Noto Serif Display`
- [`src/foliaseal/presentation/qt/signing_shell.py`](/home/daekar/FoliaSeal/src/foliaseal/presentation/qt/signing_shell.py)
  exposes `Fantasy` in the font-family control
- [`tests/unit/test_qt_signing_shell.py`](/home/daekar/FoliaSeal/tests/unit/test_qt_signing_shell.py)
  and [`tests/unit/test_signature_font_registry.py`](/home/daekar/FoliaSeal/tests/unit/test_signature_font_registry.py)
  currently lock in that mapping
- docs already describe `Fantasy -> Noto Serif Display`

`Noto Serif Display` is a display serif. It is not a Papyrus-style face.

So the current state has two defects:

1. the asset behind the choice is wrong
2. the family name is vague and unnecessary

## Decision

The new product-facing family name should be `Papyrus`, not `Fantasy`.

That means:

- remove `Fantasy` from the UI family list
- add `Papyrus`
- map `Papyrus` to a real bundled Papyrus-style asset
- keep the rest of the rendering stack honest and explicit

## Relevant Code Path

Primary implementation seam:

- [`src/foliaseal/application/signature_font_registry.py`](/home/daekar/FoliaSeal/src/foliaseal/application/signature_font_registry.py)
  - `_canonical_family(...)`
  - `preview_font_family_supported(...)`
  - `_face_name_for_request(...)`

Preview/UI seam:

- [`src/foliaseal/presentation/qt/signing_shell.py`](/home/daekar/FoliaSeal/src/foliaseal/presentation/qt/signing_shell.py)
  - font-family combo options
  - preview font stack helpers

Tests/docs that must be updated with the rename:

- [`tests/unit/test_signature_font_registry.py`](/home/daekar/FoliaSeal/tests/unit/test_signature_font_registry.py)
- [`tests/unit/test_qt_signing_shell.py`](/home/daekar/FoliaSeal/tests/unit/test_qt_signing_shell.py)
- [`README.md`](/home/daekar/FoliaSeal/README.md)
- [`docs/SPEC.md`](/home/daekar/FoliaSeal/docs/SPEC.md)
- [`docs/ExecPlans/phase3_parallel_plan.md`](/home/daekar/FoliaSeal/docs/ExecPlans/phase3_parallel_plan.md)
- [`docs/ExecPlans/unified_font_engine_signature_rendering_execplan.md`](/home/daekar/FoliaSeal/docs/ExecPlans/unified_font_engine_signature_rendering_execplan.md)

Font asset location:

- [`src/foliaseal/resources/fonts`](/home/daekar/FoliaSeal/src/foliaseal/resources/fonts)

## Required Changes

### 1. Add a real bundled Papyrus-style asset

Add a font asset that is visually aligned with the intended Papyrus-like
direction.

Requirements:

- bundled locally under `src/foliaseal/resources/fonts`
- licensing and redistribution must be acceptable for the repo
- regular face is required
- if bold/italic variants are not available, support must be explicit rather
  than silently substituted

Do not reuse `Noto Serif Display` under a different name.

### 2. Rename the family from `Fantasy` to `Papyrus`

Update the canonical family mapping so:

- `Papyrus` becomes the public family name
- `Fantasy` is removed from the UI options
- optional backward-compatibility aliasing can remain in `_canonical_family(...)`
  for persisted configs, but the UI should stop advertising `Fantasy`

Expected behavior:

- new UI choice: `Papyrus`
- old persisted `Fantasy` values may still resolve to `Papyrus` for migration
- preview and backend use the same new asset

### 3. Make style support explicit

If the chosen Papyrus-style family does not provide all four style variants:

- regular
- italic
- bold
- bold italic

then the registry must reject unsupported combinations explicitly, the same way
`Cursive` already does for unsupported styles.

Do not silently fall back to serif or sans.

### 4. Update preview stack tests and backend mapping tests

Lock in:

- `Papyrus` is supported directly
- `Fantasy` is no longer the advertised UI option
- the preview font stack resolves to the actual Papyrus-style family name
- persisted legacy `Fantasy` values, if migration aliasing is kept, resolve to
  the same canonical family as `Papyrus`

### 5. Add one parity specimen using `Papyrus`

Add one focused preview/signed-output parity specimen using the new family so
the remap is not only a registry-level change.

This does not need a broad matrix expansion. One tracer-bullet case is enough
for this slice.

## TDD Plan

### Red

1. Add registry tests that expect:
   - `Papyrus` to resolve
   - `Fantasy` to disappear from the direct advertised family set
   - unsupported style combinations to fail honestly if the bundled family does
     not support them

2. Add Qt shell tests that expect:
   - the font-family control to offer `Papyrus`
   - the preview stack to mention the actual Papyrus-style family
   - no user-facing `Fantasy` option

3. Add one focused parity specimen using `Papyrus`.

### Green

1. Add the bundled asset
2. update the font registry
3. update the Qt shell option list / preview stack
4. update docs

### Refactor

- keep any legacy `Fantasy -> Papyrus` aliasing contained inside the registry
- do not let `Fantasy` survive as an active UI concept

## Acceptance Criteria

- the UI no longer advertises `Fantasy`
- the UI advertises `Papyrus`
- `Papyrus` resolves to a real bundled Papyrus-style asset
- preview and backend both use that asset
- unsupported style combinations are explicit errors if the asset family lacks
  them
- one preview/signed-output parity specimen using `Papyrus` passes
- docs no longer describe `Fantasy -> Noto Serif Display`

## Constraints

- Keep this slice isolated from harness-fit work.
- Do not broaden into general font-design cleanup.
- Do not silently substitute another family when `Papyrus` is requested.
