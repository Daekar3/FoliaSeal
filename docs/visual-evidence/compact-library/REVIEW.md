# Compact Signature Library visual review

Status: PASS on the refreshed follow-up candidate 3, retained as the `final-*` evidence set. The installed-package gate is still pending because these captures were made from the corrected source tree before the replacement package was built and reinstalled.

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
assertion. All six refreshed `final-*` PNG/JSON captures were opened and
rechecked for hierarchy, density, grouping, wrapping, preview prominence, and
native Qt coherence. They passed actual image inspection; the review did not
pixel-match the normative SVGs.

The source correction has not yet been accepted as an installed release. A
new commit, fresh package checksum, offline/private/display-backed audits,
reinstall, and repeat installed human review remain required. Keyboard focus,
high contrast, and accessibility technology checks remain separate gates.
