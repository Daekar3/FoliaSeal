# Visible Signature Output Analysis and Corrective Wave

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

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
- [x] (2026-03-31 23:59Z) Identified that the current harness diagnostics path is broken by a
  `field_bindings` attribute mismatch.
- [x] (2026-03-31 23:59Z) Fixed the harness diagnostics path so it converts the request appearance
  into the backend appearance type before summarizing it.
- [x] (2026-03-31 23:59Z) Added actual-output inspection helpers that capture the signed PDF’s
  annotation rectangle, appearance stream facts, and image XObject summaries.
- [ ] Inspect the current shell preview sizing path to stop the side panel from widening itself.
- [ ] Correct the preview contract so it never stretches the preview container to “fit” oversized
  text; it must instead show overflow honestly inside a fixed-size preview card.
- [ ] Correct the backend single-line stamp-image sizing for `Top` and `Bottom` so the image is
  constrained by the true remaining rectangle space.
- [x] (2026-04-01 00:00Z) Launched the next corrective wave with three explicit ownership slices:
  shell preview sizing, harness/output diagnostics, and backend fit correction.
- [x] (2026-03-31 23:59Z) Ran focused verification on the harness slice that exercises the new
  capture fields.
- [x] (2026-04-01 00:15Z) Integrated the first three-worker corrective wave and verified the
  merged shell, harness, and backend slices together (`64 passed`, `ruff` clean).
- [ ] Fix the preview card so it scales to the available panel width instead of staying at a small
  fixed viewport that can render text effectively invisible.
- [ ] Fix the preview card/body sizing contract so the card is not fixed to the inner body height
  and does not clip title/detail content into an apparently empty preview.
- [ ] Improve `single_line` horizontal (`Left`/`Right`) stamp sizing so the backend uses the real
  wrapped text footprint more effectively and does not leave excessive unused space beside the text.
- [ ] Run the narrow harness rerun on `single_line` `Top`, `Bottom`, and `Left` when the shell
  preview and backend fit work are stable enough to interpret together.
- [x] (2026-04-01 00:40Z) Recorded the proposed next instrumentation upgrade wave so the current
  preview/output work has a clear follow-on path once the remaining Phase 3 parity issues settle.

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

- Observation: the current backend diagnostics path is still wired to the wrong appearance object
  shape.
  Evidence: the harness captured `backend_reservation_error` as
  `'SignatureAppearance' object has no attribute 'field_bindings'` after the latest run.

- Observation: the signed PDF appearance stream itself is good enough to analyze without adding a
  new parsing library.
  Evidence: the harness can inspect the `/AP` `/N` stream, decode visible text fragments, and list
  image XObject summaries from the existing pyHanko reader stack.

- Observation: the recent preview fix stopped raw-point sizing, but the preview is still too small
  because it is capped to a tiny static viewport and the whole card is being fixed to the body area.
  Evidence: the latest manual run showed the preview taking only roughly one-third to one-half of
  the available width, and in some `single_line` cases the border remained visible while the text
  appeared absent until the font was reduced.

- Observation: the backend output for vertical `single_line` is now in much better shape than the
  preview, while horizontal `Left`/`Right` still leaves too much unused space beside the text.
  Evidence: the user reported that `single_line/top` and `single_line/bottom` now look good in the
  signed PDF, but `single_line/left` and `single_line/right` still produce a stamp that is smaller
  than necessary despite plenty of unused horizontal space.

- Observation: richer PDF-object instrumentation still does not fully answer “what did the human
  actually see?”
  Evidence: even after adding reservation snapshots and appearance-stream facts, the remaining
  disagreements are still about preview usability, clipping, and visual balance rather than missing
  PDF metadata.

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

- Decision: prioritize actual-output analysis tooling before more backend heuristics.
  Rationale: the current harness shows we need facts from the signed PDF itself, not only request
  snapshots and preview text, to understand why the image sizing diverges.
  Date/Author: 2026-03-31 / Codex

- Decision: keep the output-analysis snapshot focused on primitive facts rather than PDF objects.
  Rationale: the harness capture needs to remain JSON-safe, reviewable, and easy to diff in future
  acceptance runs.
  Date/Author: 2026-03-31 / Codex

- Decision: split the new corrective wave into three disjoint workers rather than one broad agent.
  Rationale: the preview scaling, harness diagnostics, and backend stamp-fit changes are related
  but can be implemented and verified independently; splitting them reduces overlap risk and keeps
  each worker's ExecPlan focused.
  Date/Author: 2026-04-01 / Codex

- Decision: treat the next pass as a narrower follow-up wave rather than reopening the whole
  harness/output-analysis effort.
  Rationale: the latest manual evidence shows the remaining problems are now concentrated in shell
  preview card sizing/clipping and horizontal `Left`/`Right` stamp fit, while the harness and
  vertical `Top`/`Bottom` output are materially improved.
  Date/Author: 2026-04-01 / Codex

- Decision: the next instrumentation upgrade should target application-level visual artifacts and
  structured UI-state capture rather than display-server protocol tracing.
  Rationale: app-level snapshots, rendered preview/output crops, and deterministic replay are much
  more portable and actionable for this project than low-level X11/Wayland tracing.
  Date/Author: 2026-04-01 / Codex

## Outcomes & Retrospective

The harness/output-analysis slice is now providing the key evidence the wave needed: request-side
layout, backend reservation data, and actual signed-PDF visible-appearance facts are all captured in
one place. The first backend follow-up also brought `single_line` `Top` and `Bottom` much closer to
acceptable output. The remaining work is now narrower: make the preview card scale and clip
honestly inside the available panel width, and improve horizontal `Left`/`Right` stamp fit so the
stamp uses the reserved area more effectively. A future instrumentation upgrade should build on this
foundation with preview snapshots, rendered output crops, and deterministic replay support.

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
helpful, but they still disagree in important cases. The preview panel can widen itself to
accommodate content, the harness diagnostics path is still asking the wrong object for reservation
data, and the actual PDF can overscale the stamp image in ways the preview does not explain.

“Actual output analysis” in this repository should mean code that inspects the produced signed PDF
and extracts useful, machine-readable facts about the visible appearance. That can include the
appearance stream, widget annotation rectangle, image XObject dimensions if accessible, and the
text fragments visible in the appearance content stream. The goal is not pixel-perfect rendering
inside tests; the goal is enough objective evidence to explain why the output looks wrong.

## Plan of Work

Start with the shell preview contract again, but now target the remaining specific failure. In
`src/foliaseal/presentation/qt/signing_shell.py`, the preview should scale to the available panel
width while preserving the selected rectangle’s aspect ratio. The preview card itself should not be
fixed to the inner body height; only the body region should be constrained. The goal is a preview
that stays stable, uses the available horizontal space, and clips/overflows honestly instead of
collapsing into an empty-looking miniature card.

Then tighten the backend’s horizontal `single_line` fit logic in
`src/foliaseal/application/phase3_signing_backend.py`. The current `Left`/`Right` path measures a
text box and reserves width conservatively, which leaves too much unused space and makes the stamp
smaller than necessary. The next pass should use the real wrapped body footprint more effectively so
the stamp can grow when the text occupies less width than the current reservation assumes.

## Concrete Steps

From `/home/daekar/FoliaSeal`:

1. Inspect and patch the shell preview card/body sizing behavior in
   `src/foliaseal/presentation/qt/signing_shell.py`.
2. Tighten backend `single_line` horizontal image-fit logic in
   `src/foliaseal/application/phase3_signing_backend.py`.
5. Run focused tests:

       ./.venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_signing_backend.py
       ./.venv/bin/ruff check src/foliaseal/presentation/qt/signing_shell.py src/foliaseal/application/phase3_signing_backend.py tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_signing_backend.py

6. Perform a narrow harness rerun covering:
   - `single_line / Top`
   - `single_line / Bottom`
   - `single_line / Left`
   - `single_line / Right`

## Validation and Acceptance

Acceptance for this wave means all of the following are true:

- the properties panel no longer widens just because preview text is too large
- the preview card uses the available panel width while preserving the selected rectangle’s aspect
  ratio
- the preview card does not clip title/detail content into an apparently empty card when the backend
  still considers the layout signable
- `single_line / Top` and `single_line / Bottom` continue to produce the improved final PDF output
  observed in the latest manual run
- `single_line / Left` and `single_line / Right` use the horizontal stamp area more effectively and
  stop leaving obvious unused space beside the text
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
  - side panel still widened as soon as the rectangle was drawn in the latest manual run
  - preview card still used only about one-third to one-half of the available horizontal space
  - preview could show only the border with no visible text even when validation later allowed
    signing after field/font adjustments
  - final PDF output for `single_line/top` and `single_line/bottom` looked good after the recent
    backend changes
  - final PDF output for `single_line/left` and `single_line/right` still left too much unused
    horizontal space beside the text because the stamp was smaller than necessary

## Interfaces and Dependencies

No new third-party dependencies are required by default. Use the existing pyHanko and PDF reader
stack already in the environment.

If a helper module is added, keep it close to `src/foliaseal/application/phase3_signing_backend.py`
so the harness can use the same inspection logic as the signing backend without duplicating PDF
parsing rules.

Any spawned agent in this wave must:

- create and maintain its own ExecPlan in `docs/ExecPlans/`
- explicitly state changed files, verification, and caveats when reporting back
- avoid plan-only responses when given an implementation brief

Update note: revised on 2026-03-31 after the next harness run showed the preview still widening,
the backend reservation snapshot still failing on `field_bindings`, and the final PDF still
overscaling the stamp for `single_line/top` and `single_line/bottom`. The new version explicitly
calls for actual-output inspection tooling so the next corrective pass has better evidence.
