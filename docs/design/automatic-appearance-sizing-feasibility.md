# Automatic Appearance sizing: pre-approval evidence

Status: provisional feasibility evidence for ExecPlan 005a, not implemented behavior or owner acceptance.

## Method

On 2026-10-04, source commit `186822d78` was tested without production or frozen edits.
Disposable scripts and original PNG/PDF artifacts are under `/tmp/foliaseal-005a-spike/`.
The scripts use the existing environment and exact bundled faces. No runtime dependency was added.

`probe.py` measures the existing PyHanko text boxes at 10, 9.5 and 9 pt for three families,
four positions, wide/tall images and five content cases (120 combinations, three candidates each).
It applies a disposable text-first region calculation to a 216 by 72 pt rectangle with
4 pt edge margins and a 6 pt text/image gap. These PDF-space budgets match the current policy
at this rectangle. Border-safe inset is the greater of 4 pt and `ceil(border_width_pt / 2) + 1`.
Image sizing maximizes aspect-preserving fit in the remainder; the proposed shorter-side floor is 12 pt.
This is a measurement spike, not a second production layout engine.

`render.py` produces 24 diagnostic PNG/PDF compositions with the canonical bundled-font
TextBoxStyle and PyHanko stamp engine, using Stacked text, four image positions, three families,
and 10/9 pt. It renders at 96 logical pixels per inch (288 by 96 pixels).
The region allocation is disposable proposed logic, not the old production prominence policy.
`baseline.py` separately reproduces the unmodified canonical text-only preview at 10 pt for all families.
The distinction matters: diagnostic renders do not prove that the shared production pipeline has changed.

Commands run successfully:

    PYTHONPATH=src .venv/bin/python /tmp/foliaseal-005a-spike/probe.py
    PYTHONPATH=src .venv/bin/python /tmp/foliaseal-005a-spike/render.py
    PYTHONPATH=src .venv/bin/python /tmp/foliaseal-005a-spike/baseline.py

Sanitized measured results are retained in [geometry.json](automatic-sizing-evidence/geometry.json)
and [render-report.json](automatic-sizing-evidence/render-report.json). Original PDF counterparts
were retained by a wrapper around the existing raster renderer before its normal cleanup.

## Observations

| Serif content at 10 pt | Text box | Wide image at Left | Result |
| --- | --- | --- | --- |
| Compact: Ada Example plus UTC date/time | 172 by 10 pt | 30 by 7.5 pt | Image floor fails, including at 9.5/9 pt |
| Stacked: same two values | 101 by 21 pt | 101 by 25.25 pt | Fits at 10 pt |
| Compact, image Above | 172 by 10 pt | 192 by 48 pt | Fits at 10 pt |

The main thread opened and inspected the actual Serif Left/Above 10 pt and Left 9 pt PNGs.
At their native 288 by 96 extent, text is readable and the entire synthetic image remains visible.
This supports keeping the bounded text range as a proposal. It is not installed owner acceptance.

Representative diagnostic images:

- [Serif, Left, 10 pt](automatic-sizing-evidence/Serif-left-10.png)
- [Serif, Above, 10 pt](automatic-sizing-evidence/Serif-above-10.png)
- [Serif, Left, 9 pt](automatic-sizing-evidence/Serif-left-9.png)
- [Image only](automatic-sizing-evidence/image-only.png)
- [Text only](automatic-sizing-evidence/text-only.png)
- [Statement plus fields and image](automatic-sizing-evidence/statement-fields.png)

`extras.py` also rendered these three Serif 10 pt states. The main thread opened all three
PNGs and found complete, readable content. Empty text in a raw TextStampStyle initially
triggered a font-subsetting exception; the disposable image-only sample avoids creating an
unused bundled text engine. Production image-only handling must keep its existing no-text
materialization path and cover it explicitly in 005b, rather than passing empty text into
a newly created glyph accumulator.

A 3 by 1 inch example cannot promise to fit every meaningful Appearance. In particular,
wide-image Compact signatures can require a wider actual placement, Stacked, fewer fields,
or a different image position. The preview must explain sample nonfit without changing the
saved arrangement or silently omitting content. Meaningful Appearance Save remains available.

## Rendered-font issue and disposable correction

The actual Monospace PNG shows excessive character spacing and clips the time value despite
the neutral measurement claiming sufficient space. The same defect appears in the unmodified
canonical text-only baseline, so it is not solely an error in the disposable region allocation.
The main thread inspected both images. See [canonical Monospace baseline](automatic-sizing-evidence/baseline-Monospace.png).

Some diagnostic renders also emit a container-width warning at fractional boundaries;
measured integer rounding must not allow actual rendered extents to exceed the allocated region.
The existing font-subsetting `FFTM` warnings were reported, not suppressed.

The investigation identified the cause: DejaVu Monospace uses 2048 units/em; the current
PyHanko shaping measurements divide advances by that value, but PDF CID `/W` widths emit raw
font units, which PDF interprets as 1000 units/em. Noto Serif/Sans already use 1000 units/em.
A temporary same-face Monospace copy normalized with the existing FontTools `scale_upem`
tool to 1000 units/em renders correctly through the unmodified canonical preview. The main
thread opened the corrected regular, bold, italic, and bold-italic PNGs and saw the complete
UTC date/time with normal spacing. See [corrected regular](automatic-sizing-evidence/normalized-Monospace.png)
and the `Monospace-bold*-italic*.png` files alongside it. No repository font asset changed.

A second disposable render uses explicit calculated regions, conservative 1 pt measurement
headroom, and normalized fonts. This avoids the generic layout fitter's floating-boundary
margin-discard warning. It produced 24 complete diagnostic PDF/PNGs, with only the existing
FFTM subsetting warnings. The main thread inspected representative Left/Right/Above/Below
outputs across all three families. See [corrected results](automatic-sizing-evidence/corrected-render-report.json)
and [Monospace with image](automatic-sizing-evidence/corrected-Monospace-left-10.png).
Two corresponding unsigned diagnostic PDFs are retained: [Serif](automatic-sizing-evidence/diagnostic-Serif-left-10.pdf)
and [Monospace](automatic-sizing-evidence/diagnostic-Monospace-left-10.pdf). They are synthetic feasibility samples, not signed-output acceptance.
These are feasibility corrections, not landed production fixes. 005b must normalize all four
Monospace styles, retain face/glyph/license identity, and materialize the exact resolved
regions without a fitter silently dropping margins. Actual rendered extent remains the gate.
Do not remove Monospace or substitute system fonts to obtain a pass.

The 9.5 and 9 pt candidates also have rendered boundary examples: a 159 by 72 pt box selects
9.5; a 154 by 72 pt box selects 9. The larger candidates fail the image floor in each case.
The main thread opened both native-size PNGs and verified complete readable text. See
[boundary results](automatic-sizing-evidence/boundary-report.json),
[9.5 pt](automatic-sizing-evidence/boundary-9.5.png), and [9 pt](automatic-sizing-evidence/boundary-9.png).

The synthetic image has transparent pixels plus opaque ink. Its retained PDF has an image
soft mask (`/SMask`), preserving alpha rather than flattening the source. A fully transparent
image has no alpha bounding box; it must be rejected as empty before allocation instead of
claiming meaningful image content. See [alpha results](automatic-sizing-evidence/alpha-report.json).
This is a proposed explicit validity rule, not a claim that the old editor already rejects it.
Dense Compact and long-value cases in the geometry table correctly have no fitting candidate;
no successful raster should be produced for those rejected allocations. Stacked, fewer fields,
a different image position or a larger actual box can make other cases fit without any silent switch.

These observations support presenting the numeric proposal for owner approval, subject to
production corrections and later acceptance. A new Appearance should default to Stacked;
Compact remains explicit. Bounded border thickness is proposed as Thin=1 pt, Medium=2 pt,
Thick=3 pt (default Thin when enabled), replacing the raw width control under the same approval.
DPR, real-X11 composition, signed-PDF parity and installed human readability remain later gates.
