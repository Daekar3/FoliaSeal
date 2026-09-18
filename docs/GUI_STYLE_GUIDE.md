# FoliaSeal Qt visual guide

**Status: Established after the Appearance-editor visual-contract pilot.**
This guide is subordinate to the frozen UI_SPEC.md. SPEC.md
governs product scope, SCHEMAS.md governs persistent objects, and UI_SPEC.md
governs interface organization and interaction. This guide describes a
native-Qt realization where those documents leave room for choice.

## Layout

Use Qt layout size policies, font metrics, and the active QStyle for ordinary
spacing and control dimensions. Treat a minimum window size as a usable
composition target, not as the usual opening size. At the supported minimum,
required labels and actions must remain visible and content must not require
routine horizontal scrolling. Long forms may scroll vertically. A preview
marked as sticky and the action footer must remain in place while form
controls scroll.

The Library keeps catalog navigation, saved-object list, and detail editor as
three stable columns. In the Appearance editor, Name and content controls
occupy the content side and the labeled synthetic preview occupies a separate
adjacent area. Cancel and Save form a stable bottom footer beneath the Library
content; Save is the primary action. Do not substitute a reachable button
inside a scroll area for that footer.

## Text and color

Use the system UI font and preserve font scaling, device-pixel ratio, focus,
and high-contrast behavior. Prefer native QPalette roles and system accent for
ordinary text, surfaces, and borders. Actual PDF and Appearance colors are
content and do not change with the application theme; a light sample paper
needs legible sample text even under a dark application palette. Use headings
for sections, concise field labels, sentence-style explanatory copy, and
wrapping for prose rather than truncation. Keep controls in reading and tab
order.

## Visual evidence

For a visual change, record the current state, state the specific discrepancy,
change the owning surface, and capture the same state again. Inspect the
images directly at the same style, font, scale, data, and requested geometry.
Check hierarchy, density, wrapping, grouping, preview prominence, footer
placement, and native desktop coherence. The UI_SPEC wireframes govern
topology, hierarchy, and state; they are not pixel templates. A material
finding requires correction, a new capture, and another review.

This pilot uses the Signature Library Appearance editor. Its approved layout
is documented in UI_SPEC.md SUR03/SUR04 and
ui/appearance-profile-editor-exploratory.svg. The pilot's before/after images
and geometry reports are non-normative evidence under
visual-evidence/appearance-pilot/ after review.
