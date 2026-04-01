# Visible Signature Output Analysis and Corrective Wave

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agent/PLANS.md`.

## Purpose / Big Picture

The current visible-signature flow now signs PDFs successfully and no longer crashes in the basic
`Stamp Position` paths, but the harness run shows that preview fidelity and final PDF appearance are
still not trustworthy enough for real use. After this wave, a user should be able to draw a normal
signature rectangle, choose a `Stamp Position`, and rely on the preview as an honest representation
of what the PDF will show. The final PDF should no longer massively overscale the stamp image in
ordinary cases, the preview panel should not widen itself to accommodate overflowing content, and
our tooling should let us inspect the actual PDF appearance instead of guessing from symptoms.

This work matters because the current problems are not just cosmetic. They make it hard to tell
whether the app is respecting the user’s requested layout, and they force repeated manual harness
runs without enough evidence to diagnose the real failure mode.

## Progress

- [x] (2026-03-31 23:58Z) Captured the latest harness findings and created this ExecPlan.
- [ ] Inspect the current shell preview sizing path to stop the side panel from widening itself.
- [ ] Add output-analysis tooling that records actual visible-appearance facts from the signed PDF.
- [ ] Correct the preview contract so it never stretches the preview container to “fit” oversized
  text; it must instead show overflow honestly inside a fixed-size preview card.
- [ ] Correct the backend single-line stamp-image sizing for `Top` and `Bottom` so the image is
  constrained by the true remaining rectangle space.
- [ ] Run focused verification, then perform a narrow harness rerun on `single_line` `Top`,
  `Bottom`, and `Left`.

## Surprises & Discoveries

- Observation: the side panel widening is itself evidence that the preview is cheating.
  Evidence: the user could only “fix” the panel width by shrinking the text size, which means the
  preview widget is expanding to accommodate text instead of staying fixed and showing overflow.

- Observation: our current backend reservation diagnostics are incomplete and partially broken.
  Evidence: the latest harness capture reported `backend_reservation_error` as
  `'SignatureAppearance' object has no attribute 'field_bindings'`, which means the instrumentation
  path is not operating on the same object shape as the actual signing path.

- Observation: visual parity issues differ by stamp position, which strongly suggests that the real
  PDF appearance is being constrained by different geometry than the preview assumes.
  Evidence: `single_line/left` produced a smaller and better-placed stamp than `single_line/top`
  and `single_line/bottom`, while the preview still looked odd and far from the text.

## Decision Log

- Decision: treat “actual output analysis” as a first-class deliverable, not just debugging
  support.
  Rationale: we now have enough evidence that preview heuristics and final-PDF heuristics can drift
  in non-obvious ways. We need tooling that reports what the signed PDF actually contains.
  Date/Author: 2026-03-31 / Codex

- Decision: keep the preview card at a fixed geometry derived from the selected rectangle, even when
  content does not fit.
  Rationale: if the preview expands to accommodate text, it stops being a truthful representation
  of the final output. Honest overflow is better than a lying preview.
  Date/Author: 2026-03-31 / Codex

- Decision: require all spawned agents in this wave to maintain their own ExecPlans before making
  code changes.
  Rationale: the problem has enough moving parts now that vague or plan-only agent work would
  create more confusion than progress.
  Date/Author: 2026-03-31 / Codex

## Outcomes & Retrospective

Pending. The target outcome is a system where the preview stays fixed and honest, the final PDF no
longer grossly overscales the stamp for ordinary rectangles, and the harness artifacts provide
actual evidence about the signed output instead of only surface-level symptoms.

## Context and Orientation

The main files involved are:

- `src/foliaseal/presentation/qt/signing_shell.py`
- `src/foliaseal/presentation/qt/phase3_harness.py`
- `src/foliaseal/application/phase3_signing_backend.py`
- `tests/unit/test_qt_signing_shell.py`
- `tests/unit/test_phase3_harness.py`
- `tests/unit/test_phase3_signing_backend.py`

The Qt shell renders a live preview card. The backend uses pyHanko to build the actual visible
signature that gets embedded in the signed PDF. Right now those two paths are both trying to be
helpful, but they still disagree in important cases. The preview is still stretching or wrapping in
ways that do not match the signed output, and the backend diagnostics in the harness are not
reliably reporting the same object shape as the signer uses.

“Actual output analysis” in this repository should mean code that inspects the produced signed PDF
and extracts useful, machine-readable facts about the visible appearance. That can include the raw
appearance stream, widget annotation rectangle, image XObject dimensions if accessible, and the text
fragments visible in the appearance content stream. The goal is not pixel-perfect rendering inside
tests; the goal is enough objective evidence to explain why the output looks wrong.

## Plan of Work

Start with the shell preview contract. In `src/foliaseal/presentation/qt/signing_shell.py`, stop
the preview card and the surrounding properties panel from widening to accommodate overflowing
content. The preview should stay constrained to the selected rectangle’s aspect ratio, scaled to the
panel, and should allow text or image content to overflow or clip inside that fixed card if needed.
This is the user-visible signal that the chosen font size or fields do not fit.

Then repair the harness-side reservation diagnostics in
`src/foliaseal/presentation/qt/phase3_harness.py` so they use the backend-facing appearance object,
not the domain-side object that lacks `field_bindings`. Without this, every later harness run loses
the exact diagnostics we need.

Next, add actual-output inspection helpers. These should live in
`src/foliaseal/application/phase3_signing_backend.py` or a closely related helper module and should
be callable from the harness. The helpers should extract at least:

- the widget annotation rectangle
- the visible-appearance stream bytes or decoded text operators where feasible
- the text fragments visible in the appearance stream
- the presence and dimensions of any embedded image XObject used by the visible signature

These facts should be serialized into `Phase3HarnessCapture` so the JSON artifact can explain what
the final PDF actually contains.

Only after that tooling is in place should the backend image-fit logic be tightened again for
`single_line` `Top` and `Bottom`. The goal is to constrain the stamp image by the true remaining
stamp area instead of whatever pyHanko happens to do after a generic shrink-to-fit rule. The likely
path is to compute a stricter bounding region from measured text dimensions and the image aspect
ratio, then pass pyHanko a background layout with margins that reflect that target region.

## Concrete Steps

From `/home/daekar/SignPDF/Scratch`:

1. Inspect and patch the shell preview sizing behavior in
   `src/foliaseal/presentation/qt/signing_shell.py`.
2. Repair harness reservation diagnostics in
   `src/foliaseal/presentation/qt/phase3_harness.py`.
3. Add actual-output inspection helpers and harness serialization for them.
4. Tighten backend `single_line` image-fit logic using the new evidence from the output-analysis
   helpers.
5. Run focused tests:

       ./.venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_signing_backend.py
       ./.venv/bin/ruff check src/foliaseal/presentation/qt/signing_shell.py src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/application/phase3_signing_backend.py tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_signing_backend.py

6. Perform a narrow harness rerun covering:
   - `single_line / Top`
   - `single_line / Bottom`
   - `single_line / Left`

## Validation and Acceptance

Acceptance for this wave means all of the following are true:

- the properties panel no longer widens just because preview text is too large
- the preview card remains fixed to the selected rectangle’s aspect ratio and shows overflow or
  clipping honestly
- `backend_reservation_snapshot` no longer fails with the `field_bindings` attribute error
- the harness JSON contains meaningful output-side appearance facts from the actual signed PDF
- `single_line / Top` and `single_line / Bottom` no longer show a grossly oversized stamp in the
  final PDF for an ordinary rectangle
- focused tests pass and lint is clean

The user-visible proof is another harness run where the preview stays fixed, the side panel stays
stable, and the JSON artifact gives enough evidence to explain the final PDF’s actual layout.

## Idempotence and Recovery

These changes are additive and safe to repeat. If the actual-output inspection helpers prove too
ambitious to finish in one pass, land them in a smaller but still useful form rather than dropping
them entirely. For example, extracting annotation rectangle plus decoded appearance-stream text is
already much better than today’s state.

## Artifacts and Notes

- Latest harness findings from 2026-03-31:
  - side panel widens when preview text is too large
  - preview stamp shrinks too far for `single_line/top` and `single_line/bottom`
  - final PDF stamp remains much too large for `single_line/top` and `single_line/bottom`
  - `single_line/left` is stable, but preview and final output still disagree materially
  - `backend_reservation_error` currently reports:

        'SignatureAppearance' object has no attribute 'field_bindings'

- Latest capture highlights:
  - `layout_template: single_line`
  - `stamp_position: left`
  - `font_size_pt: 4.5`
  - `preview_text` still wrapped to multiple lines

## Interfaces and Dependencies

No new third-party dependencies are required by default. Use the existing pyHanko and PDF reader
stack already in the environment.

If a helper module is added, keep it close to `src/foliaseal/application/phase3_signing_backend.py`
so the harness can use the same inspection logic as the signing backend without duplicating PDF
parsing rules.

Any spawned agent in this wave must:

- create and maintain its own ExecPlan in `.agent/`
- explicitly state changed files, verification, and caveats when reporting back
- avoid plan-only responses when given an implementation brief
