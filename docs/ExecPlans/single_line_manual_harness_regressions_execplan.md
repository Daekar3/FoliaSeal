# Single-Line Manual Harness Remediation

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agent/PLANS.md`.

## Purpose / Big Picture

After this change, the real interactive Phase 3 signing harness should present `single_line` signatures the same way a user expects when they use their actual certificate-derived field set, their real stamp image, and an optional signer label. The signer label should be the highest visible element inside the preview border for every `single_line` position, the stamp should remain visible for `left` and `right`, and the preview should not starve or clip content merely because the title line is being counted in the wrong layout bucket.

The proof is a manual harness run with a realistic full-field profile and signer label. In the corrected build, `single/top`, `single/bottom`, `single/left`, and `single/right` should all show the signer label above the body content, keep the stamp visible, and avoid clipping the text glyphs in the live Qt preview.

## Progress

- [x] (2026-04-05 09:26Z) Reviewed the user’s manual harness findings and identified that they are not covered by the unattended matrix corpus.
- [x] (2026-04-05 09:31Z) Traced the live preview composition in `src/foliaseal/presentation/qt/signing_shell.py` and confirmed that the signer label is still folded into the vertical detail block and into horizontal stamp-width reservation.
- [x] (2026-04-05 09:34Z) Traced the backend fit path in `src/foliaseal/application/phase3_signing_backend.py` and confirmed that compact vertical `single_line` top rectangles with the full real field set leave effectively no stamp-height budget by `9.0pt` to `9.5pt`.
- [x] (2026-04-05 09:45Z) Implemented the preview composition fix so the signer label is a dedicated top row for all `single_line` positions and the body sizing accounts for that row explicitly.
- [x] (2026-04-05 09:48Z) Added focused regressions for signer-label ordering, reduced body-height budgeting, and the new horizontal title placement assumptions.
- [x] (2026-04-05 13:42Z) Fixed preview-specific wrapping and alignment drift so `single_line` top/bottom stamp images use left alignment again and horizontal preview uses the backend-style body wrapping rules before sizing the stamp band.
- [x] (2026-04-05 14:12Z) Confirmed the remaining blocker is a backend/output structural mismatch: preview now has a dedicated signer-label row, but backend fit validation and output rendering still budget `signer_label_prefix` inside the body text box.
- [ ] Design and implement a backend title-band reservation model for `single_line` so fit validation and signed output can honor the same signer-label semantics as the preview.

## Surprises & Discoveries

- Observation: the automated single-line matrix mostly avoided this class of bug because it did not stress the full real-world combination of signer label plus dense certificate-derived fields in the live shell.
  Evidence: the user’s manual harness run shows failures with `signer_label_prefix` present and the full field set visible, while the unattended matrix scenarios overwhelmingly used a reduced field set and blank signer label.

- Observation: the signer label is not a real top row in the current vertical preview path.
  Evidence: `_update_preview_controls()` in `src/foliaseal/presentation/qt/signing_shell.py` builds `combined_vertical_text = "\n".join((title_line, visible_detail))` and then hides `title_label` entirely for vertical layouts.

- Observation: the preview body still assumes it owns the full card height even when a signer label is visible.
  Evidence: `_update_preview_controls()` fixes `single_body_container` and `multi_body_container` to the full inner card height without subtracting any title height, while `title_label` is also being rendered in the horizontal path.

- Observation: moving the signer label into a stable top row simplifies both vertical and horizontal preview behavior at once.
  Evidence: after adding `title_label` directly to the card layout and reserving its height explicitly, the focused preview test suite passes with the updated expectations and no longer requires the vertical detail text to contain the signer label.

- Observation: the compact vertical backend reservation for the full manual field set is genuinely near the limit even before the signer label is considered.
  Evidence: for the user-reported `single/top` rectangle around `259pt x 23pt`, measuring the two-line body text alone yields `text_area_height_pt = 19` and `stamp_area_height_pt = 0` by `9.5pt`.

- Observation: the preview had a second independent mismatch in the horizontal cases even after the signer label became a separate top row.
  Evidence: `_preview_detail_text()` was still falling back to the raw one-line `" | "` join when its initial reservation-based wrap attempt raised `ValueError`, while `_build_stamp_text()` in the backend uses a narrower text-width budget for stamped horizontal single-line bodies. That mismatch starved the preview stamp band and made the stamp disappear.

- Observation: the remaining `visible_signature_layout_unavailable` errors are driven by the backend and output model, not the preview after the latest shell fixes.
  Evidence: the harness `render_capture` now shows the preview title row and body geometry behaving as intended, while the blocking error still originates from `backend_reservation_error` and the backend continues to validate `signer_label_prefix` inside the same text box as the body.

## Decision Log

- Decision: split this work from the earlier matrix remediation into a new ExecPlan.
  Rationale: the earlier slice solved content-proximity issues inside the existing composition model, but the manual harness findings expose a different root cause involving signer-label structure and the full real-world field set.
  Date/Author: 2026-04-05 / Codex

- Decision: fix the preview composition first before changing backend fit policy.
  Rationale: the signer-label ordering and horizontal clipping bugs are definitely preview-structure bugs. Backend fit tolerance should only be adjusted after the preview is no longer misleading about available space.
  Date/Author: 2026-04-05 / Codex

- Decision: make the signer label a dedicated top row for every `single_line` preview position, not a special-case child of the horizontal content column.
  Rationale: the user expectation is position-independent, and a shared top row avoids double-counting the title in horizontal stamp-width reservation while also fixing the vertical ordering bug.
  Date/Author: 2026-04-05 / Codex

- Decision: restore left alignment for `single_line` top/bottom preview stamps instead of centering them.
  Rationale: the user explicitly expects left alignment there, and the backend reservation snapshots still use `x_align = align_min` for those vertical stamp bands. The preview should match that output-side semantic rather than the centered-matrix experiment.
  Date/Author: 2026-04-05 / Codex

## Outcomes & Retrospective

The preview-side half of this slice is complete. The preview composition now models the signer label as a real top row for every `single_line` position, reduces the body container height accordingly, restores left alignment for `top/bottom` stamp images, and uses backend-style body wrapping rules before horizontal stamp sizing. This directly addresses the previously confirmed preview-structure bugs where the title was either hidden inside the vertical detail block, counted twice in the horizontal layout budget, or replaced by an overly optimistic one-line fallback that starved the stamp band.

The preview-side half of this slice is complete, but the remaining blocker is now clearly on the backend side. The preview and the backend are using different structural models for `single_line` whenever `signer_label_prefix` is present. The preview has a dedicated title row; the backend and signed-output path still do not. That mismatch is what still drives the `visible_signature_layout_unavailable` errors in cases the preview can display. The next slice therefore needs a true backend title-band reservation design, not another round of padding or tolerance tweaks.

## Context and Orientation

The interactive preview lives in `src/foliaseal/presentation/qt/signing_shell.py`. The key method is `_update_preview_controls()`, which decides what text goes into the title label, the main detail label, and the stamp image label. The preview card is built in `_build_preview_controls()`.

The output-side fit validation lives in `src/foliaseal/application/phase3_signing_backend.py`. The most relevant functions are `_build_stamp_text()`, `_layout_reservation_for_template()`, and `_ensure_layout_can_fit()`. These decide how much space the text and image are allowed to consume inside the PDF signature rectangle.

The new harness diagnostics from `src/foliaseal/presentation/qt/phase3_harness.py` are still useful here, but they are no longer the only source of truth. This slice is driven by the real manual harness findings from the live GUI with the actual field set and signer label present.

## Plan of Work

First, restructure the preview composition in `src/foliaseal/presentation/qt/signing_shell.py` so the signer label always occupies its own top row inside the card. Add `title_label` to the preview card layout as a stable first child and stop folding the title into the vertical detail text or the horizontal stamp-width reservation. Once the title is structurally separate, reduce the fixed body-container height by the visible title height plus the card-layout spacing so the body widgets no longer overflow or clip against an invisible budget mismatch.

Next, update the `single_line` preview measurement helpers so they reserve stamp/text space based only on the body detail text, not the signer label. This should directly address the `single/bottom` “stamp smaller than necessary” report and the `single/left` or `single/right` stamp disappearance caused by over-reserving width for the content column.

Then add tests in `tests/unit/test_qt_signing_shell.py` that pin the new title placement and body-height budgeting behavior. Cover at least one vertical `single_line` case with a signer label and one horizontal `single_line` case with a signer label and image stamp.

Finally, revisit the backend fit logic with the same manual field set. Use a small measurement script or unit test to document whether the `9.5pt` top case is truly geometrically impossible inside the selected rectangle or whether the reservation logic is overly strict. Do not relax backend fit policy unless the traces show a safe output-side change.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/SignPDF/Scratch

Run the focused preview tests while iterating:

    .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_signing_backend.py

If a quick backend measurement is needed for the compact top case, use:

    .venv/bin/python - <<'PY'
    from foliaseal.application.phase3_signing_backend import (
        _build_text_box_style,
        _measure_text_box_dimensions,
        _layout_reservation_for_template,
    )
    from foliaseal.domain.models import (
        SignatureBoxStyle,
        SignatureLayoutTemplate,
        SignatureRect,
        SignatureStampPosition,
        SignatureTextStyle,
    )

    body = "Adam Smith | Secretary.LHI@Outlook.com | Board Secretary\\nLawson Heirs Inc. | 2026-04-04 20:30"
    style = SignatureTextStyle(
        font_family="Serif",
        font_size_pt=9.5,
        bold=False,
        italic=True,
        text_color_hex="#000000",
    )
    text_box_style = _build_text_box_style(style)
    width, height = _measure_text_box_dimensions(body, text_box_style)
    reservation = _layout_reservation_for_template(
        SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.TOP,
        signature_rect=SignatureRect(
            page_index=3,
            left_pt=36.04,
            bottom_pt=429.09,
            width_pt=259.28,
            height_pt=23.35,
        ),
        text_box_width=width,
        text_box_height=height,
        box_style=SignatureBoxStyle(
            show_border=True,
            border_color_hex="#000000",
            border_width_pt=1.0,
            background_color_hex="#FFFFFF",
        ),
    )
    print(width, height, reservation.text_area_height_pt, reservation.stamp_area_height_pt)
    PY

## Validation and Acceptance

This slice is accepted when the following are all true:

- In the live preview logic, the signer label is a real top row for `single/top`, `single/bottom`, `single/left`, and `single/right`.
- The horizontal preview no longer starves the stamp merely because a signer label exists.
- Focused tests pass and pin the new preview structure.
- The backend fit behavior for the compact `single/top` larger-font case is explicitly classified as either a true geometric limit or a remediated false negative, with the reason recorded here.

## Idempotence and Recovery

These steps are safe to rerun. The preview changes are local to the Qt shell and unit tests. If the backend fit investigation suggests a riskier output-side change, record the finding here before editing the backend reservation logic further.

## Artifacts and Notes

The most important manual findings driving this plan are:

- `single/top`: stamp nearly centered but not quite, `9.5pt` triggers a fit error, and the signer label can appear below the stamp
- `single/bottom`: signer label is at the top, but the stamp is smaller than necessary
- `single/left`: stamp disappears and text glyphs are clipped
- `single/right`: stamp disappears while text still looks acceptable

## Interfaces and Dependencies

Do not add new dependencies. Keep this slice concentrated in:

- `src/foliaseal/presentation/qt/signing_shell.py` for the preview composition fix
- `tests/unit/test_qt_signing_shell.py` for preview regressions
- `src/foliaseal/application/phase3_signing_backend.py` only if the backend fit investigation proves a safe reservation change is needed

Revision note: created on 2026-04-05 after a manual harness run exposed signer-label ordering, horizontal stamp visibility, and compact vertical fit issues that were not covered by the unattended single-line matrix corpus.
