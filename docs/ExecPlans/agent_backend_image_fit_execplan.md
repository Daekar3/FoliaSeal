# Fix backend stamp image sizing for visible signatures

> **Retired historical child (2026-08-16).** Backend fit behavior now belongs
> to `src/foliaseal/application/signing_backend.py` and its current tests. The
> old worker record is retained for provenance only; its legacy paths and
> nomenclature are not active implementation targets. The remaining body is
> archival and must not be executed.

This ExecPlan is a living document. It must be maintained in accordance with [`.agents/skills/write-execplan/PLANS.md`](/home/daekar/FoliaSeal/.agents/skills/write-execplan/PLANS.md), and it must stay self-contained so a newcomer can pick it up without any prior context.

## Purpose / Big Picture

Users need the final signed PDF to place the stamp image at a sensible size for ordinary visible-signature rectangles, especially for `single_line` layouts with `Top` and `Bottom` stamp positions. Right now the PDF output can grossly overscale the stamp image even when the preview looks more reasonable, which makes the signature box look broken or unreadable. After this fix, a user should be able to draw a normal signature rectangle, choose a stamp position, and see the signed PDF keep the stamp image inside the available stamp area while preserving the image aspect ratio and keeping the existing prefix/body behavior intact.

The work in this plan focuses on `src/foliaseal/application/phase3_signing_backend.py` and `tests/unit/test_phase3_signing_backend.py`, with tightly related support tests only if they are necessary to prove the behavior. The relevant parent plan is [`docs/ExecPlans/visible_signature_output_analysis_execplan.md`](./visible_signature_output_analysis_execplan.md).

## Progress

- [x] (2026-03-31 23:55Z) Created this backend-specific ExecPlan after the harness run showed that `single_line` `Top` and `Bottom` still overscale the stamp image in the signed PDF.
- [x] (2026-03-31 23:58Z) Inspect the current backend image-fit code and identify the exact place where `Top` and `Bottom` are being given too much room or where the stamp image is not being constrained by the reserved stamp area.
- [x] (2026-03-31 23:58Z) Update the backend image-fit logic so `single_line` `Top` and `Bottom` use the actual remaining stamp area more faithfully while preserving the current prefix/body split and not regressing `Left` or `Right`.
- [x] (2026-03-31 23:58Z) Add regression tests that fail before the change and pass after it, including at least one ordinary compact rectangle case that previously produced an oversized stamp image in the final PDF.
- [x] (2026-03-31 23:59Z) Run focused unit tests and a targeted lint check, then record the results and any caveats in this plan.

## Surprises & Discoveries

- Observation: The latest harness run still produced a signed PDF, but the `single_line` `Top` and `Bottom` appearances showed a stamp image that was far too large for the available rectangle, while `Left` was closer to correct.
  Evidence: The harness capture reported `last_signing_result_success: true` for the final signature, but the human-observed PDF output showed the stamp image mostly clipped or oversized for `Top` and `Bottom`.
- Observation: The harness reservation diagnostics are currently broken for the backend-facing reservation snapshot.
  Evidence: `backend_reservation_error` was `"'SignatureAppearance' object has no attribute 'field_bindings'"`.
- Observation: The prefix/body split is now part of the intended contract and must remain intact while adjusting image sizing.
  Evidence: The preview and signed PDF both now show the prefix on its own row for `single_line` layouts.
- Observation: The vertical spacing constants were collapsing the stamp area on compact `single_line` `Top` and `Bottom` rectangles.
  Evidence: Before the change, the 261.63 pt by 22.12 pt compact rectangle left `stamp_area_height_pt` at `0` in the backend reservation path because the fixed separator and margins consumed the whole vertical remainder.
- Observation: Actual PDF appearance analysis was enough to prove the fix once the layout math was adjusted.
  Evidence: After the change, the signed PDF appearance stream for compact `Top` and `Bottom` cases showed a background scale of `0.0269461`, which is visibly larger than the previous near-zero result and leaves the stamp image inside the intended row.

## Decision Log

- Decision: Treat the visible-signature stamp image as the flexible part of the layout for this wave, while preserving the user-selected text size and prefix/body behavior.
  Rationale: The user explicitly asked for the stamp image to shrink much more aggressively before we refuse a layout, and the current bug is the opposite: the stamp overscales in ordinary rectangles.
  Date/Author: 2026-03-31 / Codex
- Decision: Keep this plan limited to backend image-fit corrections plus focused tests, and leave preview-parity or harness analysis tooling to the parent wave unless they are needed to prove the backend fix.
  Rationale: The user asked for a backend image-fit worker with ownership of `src/foliaseal/application/phase3_signing_backend.py` and `tests/unit/test_phase3_signing_backend.py`; the smallest useful change is to fix the final PDF output and cover it with regression tests.
  Date/Author: 2026-03-31 / Codex
- Decision: Reduce the fixed vertical separator and edge margins for compact `single_line` `Top` and `Bottom` rectangles instead of trying to preserve the older larger spacing.
  Rationale: The real output showed that the older 4 pt margins and 6 pt separator left no usable stamp height on an ordinary form-line rectangle; shrinking those values for compact vertical layouts gives the image room to render while still keeping the text readable.
  Date/Author: 2026-03-31 / Codex

## Outcomes & Retrospective

When this plan is complete, the repository should have a backend that produces a visibly sane stamp image for ordinary `single_line` `Top` and `Bottom` signatures, while continuing to honor the existing prefix/body behavior and not regressing `Left`/`Right`. The tests should prove that the image no longer consumes almost the whole rectangle in these common cases, and the actual-output inspection should show a non-trivial image scale rather than the nearly collapsed scale that triggered the bug. If the fix exposes an underlying pyHanko layout limitation, that limitation must be recorded here so the next contributor knows whether the remaining work is a backend constraint or a bad heuristic in our code.

## Context and Orientation

The relevant backend lives in [`src/foliaseal/application/phase3_signing_backend.py`](../src/foliaseal/application/phase3_signing_backend.py). That module builds the concrete Phase 3 signing executor, converts a `SigningRequest` into a signed PDF, and maps the repository’s domain objects into pyHanko signing and stamping objects.

The visible-signature configuration that reaches the backend comes from [`src/foliaseal/application/sign_pdf_use_case.py`](../src/foliaseal/application/sign_pdf_use_case.py) and the `SigningBackendAppearance` dataclass. The important inputs for this task are:

- `layout_template`, which can be `single_line`, `multi_line`, or `wrapped_block`.
- `stamp_position`, which can be `Top`, `Bottom`, `Left`, or `Right`.
- `image_stamp_path`, which may be present or absent.
- `text_style`, which includes the user-selected font size in points.
- `signature_rect`, which is the rectangle the user drew on the page.

The backend already has a prefix/body split for `single_line`, and the user has confirmed that this split must stay intact. The current bug is not about the prefix text; it is about the stamp image being allowed to dominate the final appearance in `Top` and `Bottom` layouts.

The main tests for this work live in [`tests/unit/test_phase3_signing_backend.py`](../tests/unit/test_phase3_signing_backend.py). If a support test is needed, keep it tightly related and explain why in this plan before adding it.

## Plan of Work

First, inspect the backend image-fit helpers in `src/foliaseal/application/phase3_signing_backend.py`, especially the functions that calculate layout reservation, build the `TextStampStyle`, and choose image stamp sizing. The goal is to find the exact path that gives `Top` and `Bottom` too much image area or fails to constrain the image to the remaining reserved stamp box.

Second, change the backend so `single_line` `Top` and `Bottom` use the actual remaining stamp area more faithfully. Prefer a fix that is based on the rectangle height/width, the text block’s measured size, and the image’s aspect ratio, rather than hard-coded scaling constants. Preserve the prefix/body behavior already fixed and do not alter the semantics of `Left` and `Right` unless the same helper must be shared to keep the code coherent.

Third, add one or more regression tests in `tests/unit/test_phase3_signing_backend.py` that build a realistic compact rectangle, sign with a stamp image, and assert that the visible appearance text and image are still present but the image is constrained in the intended way. The most valuable test is one that would have failed before this change because the backend stamped an absurdly large image in a normal rectangle.

Fourth, if the backend fix exposes a more precise helper that should be reused by the shell or harness, note it in this plan but do not widen scope unless the implementation truly needs it.

## Concrete Steps

From `/home/daekar/FoliaSeal`, inspect the backend image-fit code and the existing regression tests:

    rg -n "_background_layout_for_stamp|_build_stamp_style|_layout_reservation_for_template|_measure_text_box_dimensions|stamp_position" src/foliaseal/application/phase3_signing_backend.py tests/unit/test_phase3_signing_backend.py

Then run the focused backend tests that exercise image stamping and layout reservation:

    ./.venv/bin/python -m pytest -q tests/unit/test_phase3_signing_backend.py

Then run lint on the touched files:

    ./.venv/bin/ruff check src/foliaseal/application/phase3_signing_backend.py tests/unit/test_phase3_signing_backend.py

If the tests expose a new failure, inspect the failure message and update this plan with the exact surprise before changing the code again.

## Validation and Acceptance

The change is acceptable only if the backend can sign a normal compact rectangle with a stamp image without grossly overscaling the image for `single_line` `Top` and `Bottom`. The easiest proof is a regression test that signs a realistic rectangle and inspects the resulting PDF appearance stream or other deterministic evidence that the stamp image remained within the intended reserved area.

Acceptance should be observed in two ways. First, the relevant pytest case should fail before the change and pass after it. Second, a manual harness run should no longer show the stamp image consuming almost the entire rectangle for ordinary `Top` and `Bottom` cases.

## Idempotence and Recovery

These edits are safe to repeat because they are code and test changes only. If a test fails while you are adjusting the backend, keep the existing file state and update the plan rather than trying to undo unrelated user work. If a change makes the signed output worse, revert only the local backend edit you just made and keep the plan in sync with the reverted state.

## Artifacts and Notes

Current evidence from the latest harness run:

    backend_reservation_error: "'SignatureAppearance' object has no attribute 'field_bindings'"
    preview_snapshot.stamp_position: "left"
    preview_snapshot.layout_template: "single_line"
    preview_snapshot.text_style.font_size_pt: 4.5
    sign_request_snapshot.signature_appearance.stamp_position: "left"
    sign_request_snapshot.signature_appearance.layout_template: "single_line"

That evidence strongly suggests the backend fit problem is not merely a preview issue. The final signed PDF still has a visible-appearance path that needs to respect the reserved stamp area more tightly.

## Interfaces and Dependencies

The implementation must keep using `SigningBackendAppearance`, `SigningBackendFieldBinding`, `SigningBackendRequest`, `SignatureLayoutTemplate`, `SignatureStampPosition`, and the pyHanko classes already imported in `src/foliaseal/application/phase3_signing_backend.py`.

If a helper is added or adjusted, prefer to keep it in `src/foliaseal/application/phase3_signing_backend.py` so the backend logic remains easy to trace. If a helper is only needed for tests, keep it in `tests/unit/test_phase3_signing_backend.py` or a nearby support module rather than inventing a new public API.

The backend must continue to produce a `SigningOutput` and preserve the existing verification flow through `PyHankoSignatureVerifier`.

### Note on this revision

This plan was created on 2026-03-31 after a harness run showed that ordinary compact rectangles still produce grossly oversized or otherwise badly fit stamp images in `single_line` `Top` and `Bottom` layouts. The revision reason is to narrow the next change to backend image-fit correctness and its regression coverage, while leaving preview parity and broader analysis tooling to the parent wave. This revision also records the later discovery that the compact vertical spacing values were collapsing the stamp row and that actual PDF appearance analysis could verify the corrected scale.
