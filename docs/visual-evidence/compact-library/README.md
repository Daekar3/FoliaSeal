# Compact Signature Library visual evidence

These files are non-normative review evidence for ExecPlan 004. The frozen
`docs/UI_SPEC.md` remains the interface authority. Reviewers must open the PNG
files and judge hierarchy, density, clipping, wrapping, grouping, selector and
action prominence, preview usefulness, footer placement, empty space, and
native Qt coherence. The wireframes define topology and hierarchy, not exact
pixels.

`before-default.png` is the rejected installed-package baseline. It shows the
Appearance catalog with a new Appearance editor and no selected image. The
source package was version 0.1.0, built from commit
`158777339782b3b5b97dd28dec58f2c4e6561568`, with package SHA-256
`3a34429ecbb627bc201fd1abd906ff2040be43c1b8738356760fd837d373c4ae`.
The image came from the isolated installed-package HITL session under
`/tmp/foliaseal-about-version-tYIwnn/`. Its matching JSON records the facts
that remain available. The earlier capture did not record client geometry,
screen, device-pixel ratio, font, palette, or Qt style, so those values remain
explicitly unavailable instead of being inferred from the image.

The final evidence is generated with
`scripts/capture_compact_library_layout.py` on a real Qt `xcb` display at a
1000 by 650 client size. It uses temporary settings, certificate, profile, and
image roots. The deterministic states are final Presets, a true-empty
Placements catalog, Certificates, and Appearance default, reordered-field,
selected-image, and substantially scrolled states. The default and reordered
captures use identical conditions and demonstrate that moving the first field
down changes the composed signature preview. Each generated PNG has a matching JSON report
with actual geometry, style, font metrics, palette, screen, device-pixel
ratio, active catalog, object selector state, scrollbar state, and relevant
widget geometry.

The images and geometry reports do not prove keyboard order, focus visibility,
high-contrast behavior, physical-display quality, accessibility technology
behavior, persistence, or installed-package behavior. Those claims require
their separate automated or human acceptance gates.
