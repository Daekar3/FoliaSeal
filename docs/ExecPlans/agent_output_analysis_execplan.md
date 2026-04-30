# Visible Signature Output Analysis and Corrective Wave

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agent/PLANS.md` and the parent
plan at `.agent/visible_signature_output_analysis_execplan.md`.

## Purpose / Big Picture

The user already has a signing flow that can produce a valid PDF, but the visible signature is
still not trustworthy in ordinary cases. The preview panel can widen itself instead of staying
fixed, the backend reservation diagnostics are crashing, and the harness cannot yet explain what
the signed PDF actually contains. After this wave, a user should be able to draw a normal
signature rectangle, choose a stamp position, and rely on the harness artifacts to report both
the requested layout and the actual visible appearance facts from the final PDF.

This work matters because preview/output disagreements are currently hard to diagnose. The
requested rectangle, the shell preview, the backend reservation logic, and the actual appearance
stream need to be visible in one capture so we can stop guessing at why a signature looks wrong.

## Progress

- [x] (2026-03-31 23:58Z) Captured the latest harness findings and recorded the overall wave goal.
- [x] (2026-03-31 23:59Z) Identified that the current reservation diagnostics path crashes because it
  asks a `SignatureAppearance` for `field_bindings`.
- [x] (2026-03-31 23:59Z) Fixed the reservation diagnostics path so it converts the request
  appearance into the backend appearance type before measuring or summarizing it.
- [x] (2026-03-31 23:59Z) Added actual-output inspection helpers that extract visible-appearance
  facts from the signed PDF.
- [x] (2026-03-31 23:59Z) Serialized those facts into `Phase3HarnessCapture` and updated the
  markdown summary.
- [x] (2026-03-31 23:59Z) Covered the new diagnostics and output-inspection fields with focused
  tests.
- [x] (2026-03-31 23:59Z) Ran focused verification and style checks on the harness and backend
  surfaces.
- [ ] Schedule the next narrow manual harness rerun when the surrounding shell/output parity work
  is stable enough to interpret the new capture fields interactively.

## Surprises & Discoveries

- Observation: the harness reservation snapshot is asking the wrong object type for backend-only
  layout fields.
  Evidence: the latest harness run reported
  `backend_reservation_error: "'SignatureAppearance' object has no attribute 'field_bindings'"`.

- Observation: the signed PDF already exposes machine-readable appearance content that we can
  inspect after signing.
  Evidence: a temporary pyHanko inspection showed the `/AP` `/N` stream is a PDF stream object with
  decoded bytes, resources, and visible text operators.

- Observation: the current output snapshot only records signature metadata, not the visible
  appearance itself.
  Evidence: `Phase3HarnessCapture` currently stores field name, signer name, byte range, and
  subfilter, but nothing about text fragments or image XObjects.

- Observation: the signed PDF appearance stream is directly inspectable with the existing pyHanko
  reader stack.
  Evidence: a temporary inspection showed `/BBox`, `/Resources`, literal text operators like `Tj`,
  and image XObject names without adding a new dependency.

## Decision Log

- Decision: create a child ExecPlan dedicated to harness/output analysis work.
  Rationale: the wave has enough moving parts that the harness data model and the output-analysis
  tooling need their own living plan instead of being buried in the parent wave plan.
  Date/Author: 2026-03-31 / Codex

- Decision: make actual-output analysis a first-class deliverable.
  Rationale: the preview and the signed PDF already disagree in ordinary cases, and the only way to
  diagnose that safely is to inspect the real visible-appearance stream after signing.
  Date/Author: 2026-03-31 / Codex

- Decision: keep the new output snapshot JSON-safe and compact.
  Rationale: the harness artifact needs to serialize cleanly and remain easy to review, so it
  should store primitive facts such as rectangles, fragments, counts, and XObject summaries rather
  than raw PDF objects.
  Date/Author: 2026-03-31 / Codex

## Outcomes & Retrospective

The harness now reports the request-side layout and the actual visible appearance side by side.
The reservation diagnostics path no longer crashes on `field_bindings`, and the capture now
includes the signed PDF annotation rectangle, appearance bbox, text fragments, and image XObject
summaries. The remaining limitation is that the new evidence is only useful once the next manual
harness rerun is scheduled in a stable enough state to interpret the results against the shell and
backend parity work.

## Context and Orientation

The main file for this wave is `src/foliaseal/presentation/qt/phase3_harness.py`. It owns the
`Phase3HarnessCapture` dataclass, the JSON serialization used by the harness, and the markdown
summary for the acceptance worksheet. It also currently asks the backend reservation helper to
summarize the visible signature request, which is where the `field_bindings` crash occurs.

The signing backend lives in `src/foliaseal/application/phase3_signing_backend.py`. It already
produces a real signed PDF using pyHanko. That is important because the output-analysis helpers in
the harness can inspect the real signed PDF stream and annotation data after the signer returns.

The unit tests that should protect this wave are primarily
`tests/unit/test_phase3_harness.py`, with supporting checks in the backend and shell tests where
capture data or preview semantics change.

In this repository, “actual-output inspection” means code that opens the signed PDF and extracts
facts from the visible signature itself. That can include annotation geometry, appearance-stream
text fragments, and the presence or dimensions of image resources if the PDF exposes them. The
goal is not pixel-perfect rendering in tests; the goal is enough machine-readable evidence to show
what the final signature actually contains.

## Plan of Work

First, repair the reservation diagnostics helper in
`src/foliaseal/presentation/qt/phase3_harness.py`. The helper should convert the request’s
`SignatureAppearance` into the backend-facing `SigningBackendAppearance` before it asks for
backend-only layout information. The summary should continue to include the request geometry and
layout template, but it must stop crashing on `field_bindings`.

Next, add one or more helper functions in the harness or a closely related module that open the
signed PDF produced by the signing run and inspect the visible signature appearance. The helpers
should extract the signed field’s annotation rectangle, the appearance stream bytes, and any text
or image facts that are easy to recover from the stream resources. If the helper cannot extract a
fact reliably, it should say so explicitly instead of inventing a value.

Then, extend `Phase3HarnessCapture` so it stores those visible-appearance facts in structured
fields. The capture should remain JSON-safe and should continue to serialize cleanly with
`to_json()`. Update the markdown summary builder so the new facts are visible in the acceptance
worksheet.

Finally, add focused tests to prove that the reservation diagnostics no longer crash and that the
new actual-output snapshot fields are populated from a real or carefully controlled signed-PDF
fixture. The tests should fail before the change and pass after it.

## Concrete Steps

Work from `/home/daekar/SignPDF/Scratch`.

1. Inspect the harness helper functions around reservation snapshots and output snapshots.

       rg -n "field_bindings|backend_reservation|output_signature_snapshot|Phase3HarnessCapture" \
         src/foliaseal/presentation/qt/phase3_harness.py

2. Patch the reservation snapshot helper so it first converts the incoming request appearance into a
   `SigningBackendAppearance` before measuring backend-only fields.

3. Add output-inspection helpers and extend the capture dataclass.

4. Update the markdown summary builder to mention the new output facts.

5. Add or update unit tests in `tests/unit/test_phase3_harness.py`.

6. Run the targeted tests and the style checker.

       ./.venv/bin/python -m pytest -q tests/unit/test_phase3_harness.py
       ./.venv/bin/ruff check src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_phase3_harness.py

## Validation and Acceptance

The work is complete when `tests/unit/test_phase3_harness.py` passes and the harness JSON capture
contains non-crashing backend reservation data plus at least one structured field that describes the
actual visible appearance of a signed PDF. A human should be able to run the harness, inspect
`artifacts/phase3_harness_capture.json`, and see both the requested layout information and the
signed-output facts without encountering the `field_bindings` crash.

## Idempotence and Recovery

These steps are safe to repeat. If a test fixture or temporary PDF artifact is added during
debugging, keep it under `tmp_inspect/` or `artifacts/` and remove it only after the harness output
is verified. If a capture field turns out to be too large or not JSON-safe, narrow it to the smallest
useful primitive rather than storing the entire PDF object.

## Artifacts and Notes

Expected verification transcript after the main fix should look roughly like:

    ./.venv/bin/python -m pytest -q tests/unit/test_phase3_harness.py
    1 passed in ...

and the markdown summary should no longer report:

    backend_reservation_error: "'SignatureAppearance' object has no attribute 'field_bindings'"

## Interfaces and Dependencies

The harness should depend on `SigningBackendAppearance` from
`src/foliaseal/application/sign_pdf_use_case.py` when summarizing backend reservation data, because
that is the type that carries backend-only layout bindings.

The actual-output inspection code can use pyHanko PDF reader objects already available in the
project. It should not require a new third-party dependency unless a parsing limitation makes that
unavoidable.

The public capture surface is `Phase3HarnessCapture` in
`src/foliaseal/presentation/qt/phase3_harness.py`. Any new fields added there should be simple JSON
primitives or nested dictionaries/lists that serialize cleanly.

## Change Note

This plan was added because the parent output-analysis wave needed its own child document to track
the harness-specific diagnostics fix and the new actual-output inspection work. It has now been
updated to reflect that the requested harness deliverables landed, and the remaining work is the
timing and interpretation of the next manual rerun.
