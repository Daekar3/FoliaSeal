# Compact Signature Library visual review

Status: PASS on the replacement composed-preview source candidate. Independent review opened the retained default, reordered, image, and scrolled PNGs after the first candidate was rejected for overlap and clipping. The installed-package gate remains pending.

The reviewer opened and inspected every baseline and candidate PNG. The review
used `docs/UI_SPEC.md` SUR03/SUR04, the two normative Library SVGs, and
`docs/GUI_STYLE_GUIDE.md`. The SVGs were used for topology and hierarchy, not
pixel matching.

## Feedback loop

- Candidate 1 proved the compact header and dominant editor topology, but the
  shared footer stretched Cancel and Save across half the window each. The
  empty Certificates surface also lacked a create action.
- Candidate 2 right-aligned compact footer actions and added Create
  Certificate. Review then found two Placement create controls, including an
  ineffective generic empty-state action, plus irrelevant Name controls in
  true-empty states.
- Candidate 3 leaves exactly one working create action in each true-empty
  catalog and hides ordinary detail fields when no object exists.

## Final judgment

The final captures have a clear header-to-editor-to-footer reading order. The
catalog, saved-object, and sort selectors remain compact; the editor receives
nearly all remaining space. Labels and controls are readable without clipping
or unexpected wrapping at 1000 by 650. Appearance preview text and the selected
image are prominent without crowding the form. Substantial form scrolling does
not move the preview or footer. Cancel and Save have native compact sizing and
stable right alignment. Empty Placement and Certificate states are sparse but
coherent and present one clear applicable create action. No active splitter or
permanent saved-object column remains.

No unresolved material visual discrepancy remains in the normal-theme source
capture scope. Installed-package behavior, keyboard focus visibility, and high
contrast remain separate human gates.

## Installed-package follow-up

The first installed-package HITL accepted the compact Library topology, then
identified three material presentation problems that the source geometry tests
and the first screenshot loop had not exposed:

- `Catalog` and `Saved object` read as detached labels because they were laid
  out far from their associated selectors.
- The new Appearance editor retained inefficient grouping and an awkward
  presentation of the form controls.
- User-facing copy still described implementation history and MVP/preset
  concepts. In particular, `Refine the preset's visible signature with the
  bounded choices used by the MVP` was not suitable product language.

That review reopened implementation under ExecPlan 004. Follow-up candidate 1
attached each header label to its selector, regrouped the Appearance controls,
and replaced the most visible internal wording. Candidate 2 corrected the
remaining spacing and copy issues. Compliance review then found that the
Saved object field could still expand internally, leaving the label effectively
detached; the earlier test asserted only one side of the relationship. Candidate
3 added stretch inside the grouped field and a strict 0–12 px label/control gap
assertion.

The next installed check found that the right-hand preview was only descriptive
text plus a raw selected image; it did not render the configured signature, so
Move field up/down had no visible result there. The first correction fed
deterministic example signer data and the live Appearance draft into the
canonical preview renderer. Its default and reordered reports record distinct
field orders and pixels, the image state uses the composed renderer, and the
scrolled state keeps preview/footer fixed. Actual PNG inspection nevertheless
found overlapping two-line content, a large central blank block, and right-edge
clipping, so that candidate failed the usability gate.

The replacement routes deterministic example data through
`VisibleSignatureSemanticsService`, renders the canonical sample on an opaque
white page context, uses concise values and a wide single-line rectangle, and
adds a numbered field-order guide. Direct inspection confirms that default and
reordered states visibly exchange the first two fields with no overlap or
clipping; the actual raster pixels also differ. The selected image is composed
above the signature text without collision, and scrolling leaves the guide,
raster, and footer stationary. The review did not pixel-match the normative
SVGs.

The installed human review then failed the readability gate: 10 pt text was
barely legible because the 720 pt sample width was compressed to 400 screen
pixels. A narrower 320 pt sample made the text larger but clipped the
single-line content, so it was rejected. The accepted source candidate keeps
the canonical 720 pt sample and presents a 960 px render in a 400 px horizontal
viewport. The visible instruction explains how to inspect the rest. I opened
the refreshed default, reordered, image, and scrolled PNGs. The text is now
legible in the visible portion; moving the first field changes both the guide
and the raster; the image remains composed above the text; and the preview and
footer stay fixed when the form scrolls. The horizontal viewport is an
intentional preview control, not a Library-wide horizontal scrollbar. The
matching JSON records a 960 by 160 sample inside a 416 px viewport with a
544 px horizontal scroll range. The real-Qt test confirms a focused viewport
responds to the Right arrow while the form itself has no horizontal scrollbar.

The readability correction has not yet been accepted as an installed release.
A new commit, fresh package checksum, offline/private/display-backed audits,
reinstall, and repeat installed human review remain required. Keyboard focus,
high contrast, and accessibility technology checks remain separate gates.
