# FoliaSeal

Foundations for a Linux desktop PDF signing app.

## What is included
- package skeleton with architecture-aligned module boundaries (`presentation`, `application`, `domain`, `infra`)
- `DocumentOperation` domain contract and operation registry with capability enable/disable flags
- initial config schemas for trust profile, timestamp policy, and signature presets
- Phase 1 headless signing orchestration (`SignPdfUseCase`) with:
  - compatibility policy enforcement for PDF `1.4` to `2.0`
  - strict PDF version parsing (rejects invalid/non-finite version strings)
  - incremental-signing version-preservation checks
  - stable failure-code mapping and structured signing results
  - output-path conflict detection using normalized filesystem paths
  - temp-file + atomic replace output writes with temp-file cleanup
- unit tests for schema validation, compatibility policy, operation registry behavior, and signing orchestration
  - signing orchestration tests include success path plus explicit failure-code mapping checks
    (`OUTPUT_PATH_INVALID`, `PKCS12_WRONG_PASSWORD`, `PKCS12_LOAD_FAILED`,
    `TSA_UNREACHABLE`, `TIMESTAMP_REQUIRED_BUT_MISSING`, `POST_VERIFY_FAILED`,
    `PDF_SIGNING_FAILED`, `ATOMIC_WRITE_FAILED`, `UNEXPECTED_INTERNAL_ERROR`)
- Phase 2 viewer foundations with render adapters, coordinate transforms, viewer workflow helpers, Qt preview wiring, and timing/evidence utilities that are still available for historical verification and lower-level regression checks

## Phase 3 integration contracts

Phase 3 builds the first end-user signing workflow on top of the Phase 2 viewer platform.

Current capabilities:

- `SigningDraftWorkflow` owns the in-session signing draft state for Phase 3.
  - It should track the chosen page, placement rectangle, appearance/property settings, and validation state.
  - It should not duplicate viewer coordinate math or Qt event handling.
- Named appearance profiles are now part of the current Phase 3 shell workflow.
  - A user can save the current appearance under a distinct user-provided name.
  - Saved profiles can be selected from a dropdown in the shell.
  - Saving to an existing name uses explicit overwrite confirmation.
  - Saved profiles now persist across relaunches in the user-visible `Signature Profiles`
    storage area.
  - The shell supports delete-current-profile with explicit confirmation.
- `render_signing_preview()` should turn the normalized draft state into a deterministic text
  snapshot for logs, tests, and lower-level parity checks.
  - It should not become a second live-preview formatter alongside the Qt widget path.
- `compare_preview_to_request()` should be a narrow consistency check between the preview model and the final signing request.
  - It should be used to catch drift between the visible draft and the request payload.
  - It should not become a second preview renderer or a substitute for validation.
- The Qt signing shell should sit on top of the existing viewer platform.
  - It should reuse `ViewerWorkflow` for page rendering, geometry, and selection-to-PDF mapping.
  - It should reuse the Qt preview widget adapter for render/zoom/navigation behavior.
  - It should keep properties editing, preview refresh, and sign confirmation in the application/UI layers rather than re-implementing viewer math.
- The signing shell and harness now support meaningful manual review of:
  - placement and resize behavior
  - appearance editing and preview behavior
  - named profile save/select workflows
  - executor-backed sign/apply behavior
- The shell can now call an injected signing executor and surface success/failure results.
- The current concrete signing backend now produces a genuinely cryptographically signed PDF
  through `pyHanko`.
- The key integration rule is to avoid duplicating semantics across layers.
  - Workflow code should normalize the draft.
  - Preview code should render that normalized state.
  - Qt code should orchestrate user interaction and dispatch, not reinterpret the model.
- Architectural simplification rule:
  - keep exactly one authoritative backend-owned visible-signature fit gate
  - keep preview visual
  - keep validation text thin and factual
  - keep the rules that determine visible-signature text/layout inputs in one shared path whose
    output then feeds both preview rendering and pre-submit fit validation
  - prefer deleting duplicate interpretation layers over adding new synchronization logic

Not yet production-ready:

- visible-signature preview/output parity for every realistic rectangle/layout case
- final manual harness revalidation of the recently simplified `single_line` path with real user
  assets and representative PDFs
- transparent GIF stamp handling in final signed PDF output is not trustworthy yet; PNG remains the safer image-stamp format
- final end-to-end visible-signature fidelity validation against representative signed PDFs
- TSA-backed timestamping and timestamp-required signing flows
- final end-to-end FR-3B acceptance validation

Roadmap note:

- The original Phase 3 scope turned out to bundle several independent failure modes.
- The remaining roadmap is now split into smaller post-Phase-3 slices in
  [pdf_signing_app_feasibility.md](/home/daekar/SignPDF/Scratch/pdf_signing_app_feasibility.md),
  including:
  - preview/output parity and rectangle-aware preview,
  - TSA-backed timestamping,
  - trust/certification hardening,
  - remaining profile portability work,
  - packaging and full release validation.
- The current visible-signature contract is text-first: honor the selected text size in points,
  reserve text space first, let the image stamp shrink aggressively inside the remaining room, and
  fail honestly only when the chosen rectangle cannot support that result.
- The current Phase 3 finish line is narrower than it was earlier in the project:
  - the unattended `single_line` preview matrix is now clean across the checked-in permutation set,
  - `single_line` `Top`, `Bottom`, `Left`, and `Right` share a simpler backend-owned layout path,
  - the evidence-contract/gate machinery now exists,
  - the remaining engineering focus is mainly on the last preview/output parity gaps, horizontal
    signed-output confirmation with real assets, image-format edge cases, and TSA/timestamp support.

## Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .[dev]
ruff check .
python -m pytest -q
foliaseal
python -m foliaseal
```

## PyInstaller build

Build a one-dir bundle for packaging and runtime evidence capture:

```bash
.venv/bin/pip install -e .[dev]
./scripts/build_pyinstaller.sh
```

This produces:

- bundle directory: `dist/foliaseal`
- executable: `dist/foliaseal/foliaseal`

Phase 2 evidence commands and prior runtime notes are still available in:

- [phase2_manual_qa_results.md](/home/daekar/SignPDF/Scratch/artifacts/phase2_manual_qa_results.md)
- [phase2_runtime_evidence.md](/home/daekar/SignPDF/Scratch/artifacts/phase2_runtime_evidence.md)

For lower-level viewer regression checks, you can still run:

```bash
.venv/bin/python -m foliaseal phase2-viewer-harness --pdf-path "/path/to/representative.pdf"
.venv/bin/python -m foliaseal phase2-evidence --write-markdown-file artifacts/phase2_runtime_evidence.md
```

## Phase 3 acceptance harness

To make Phase 3 acceptance easier, there is also an interactive signing-shell harness that writes a structured capture and a partially completed FR-3B worksheet for you.

Current acceptance note:

- The harness helps collect a consistent record, but it does not prove final Phase 3 readiness on its own.
- Use it as a manual-review aid for placement, appearance behavior, named-profile workflows, and signing-flow validation.
- Harness terminal success is non-gating unless the run also produces the required evidence artifacts.
- The harness JSON is now validated against a machine evidence contract; contradictory captures should be treated as failed gate evidence even if the GUI appeared to finish normally.
- For the current acceptance focus and unresolved items, rely on the Phase 3 checklist and results artifacts rather than treating this README as the project status log.

Run it against a representative PDF:

```bash
.venv/bin/python -m foliaseal phase3-signing-harness \
  --pdf-path "/path/to/representative.pdf" \
  --certificate-path "/path/to/identity.p12" \
  --passphrase "your-test-passphrase" \
  --summary-json-path artifacts/phase3_harness_capture.json \
  --checklist-results-path artifacts/phase3_fr3b_acceptance_results.md \
  --artifacts-dir artifacts/phase3_preview_debug
```

The harness defaults to `timestamp_required=False` today, so it is suitable for real signed-PDF
testing even before TSA-backed timestamping support lands. The certificate CLI arguments are meant
for local development/manual QA; avoid using a production identity in shell history if that is a
concern in your environment.

What it does:

- launches the current Qt signing shell on the chosen PDF
- records a structured capture of preview availability, selection count, sign-request count, and any surfaced errors
- can capture the live preview card as a PNG plus widget geometry and border-to-content distance metrics when `--artifacts-dir` is supplied
- classifies the run as `engineering_run` or `gate_candidate` and records the automated gate verdict
- validates the capture for internal evidence consistency before writing the artifacts
- writes a results file seeded from the Phase 3 checklist at [`artifacts/phase3_fr3b_acceptance_results.md`](/home/daekar/SignPDF/Scratch/artifacts/phase3_fr3b_acceptance_results.md)
- automatically checks the acceptance items that can be observed directly from the harness

For repeatable preview sweeps across many settings permutations, run the preview matrix command with a JSON manifest:

```bash
.venv/bin/python -m foliaseal phase3-signing-preview-matrix \
  --pdf-path "/path/to/representative.pdf" \
  --certificate-path "/path/to/identity.p12" \
  --passphrase "your-test-passphrase" \
  --scenario-manifest-path artifacts/phase3_preview_matrix_template.json \
  --artifacts-dir artifacts/phase3_preview_matrix
```

What the preview matrix writes:

- one preview PNG per scenario
- one stamp-focused debug PNG per stamped scenario, with overlay rectangles for the reserved band,
  rendered pixmap, and projected non-transparent stamp content bounds
- one summary JSON at `artifacts/phase3_preview_matrix/summary.json`
- per-scenario preview geometry, rendered widget bounds, and top/bottom border-distance metrics
- per-scenario preview settings, including any manifest overrides for `visible_fields`,
  `text_style.font_size_pt`, border width, and stamp image choice
- per-scenario stamp diagnostics, including alpha-aware source-image content bounds and explicit
  clipping/proximity flags for stamp content versus the reserved stamp band

Use the interactive harness when you want to manipulate the GUI manually. Use the preview matrix when you want a deterministic sweep across saved images, border widths, and rectangle aspect ratios.

The repo now also includes a reusable local sweep fixture set under `artifacts/preview_sweep_assets/`,
including `sweep_fixture.pdf`, `test_identity.p12`, three transparent stamp images, and
`single_line_matrix.json` for unattended `single_line` preview sweeps. That checked-in manifest now
also demonstrates two practical sweep controls that matter for layout triage:

- `visible_fields` to constrain which derived fields participate in a compact preview scenario
- explicit text-size variation scenarios so preview regressions can be checked at more than one
  `font_size_pt`

Status note:

- the checked-in unattended `single_line` matrix is currently green in automation
- use it as a regression net, not as a substitute for the pending manual harness confirmation with
  real signing assets

Validate an existing harness capture without relaunching the GUI:

```bash
.venv/bin/python -m foliaseal phase3-signing-harness-validate \
  --summary-json-path artifacts/phase3_harness_capture.json
```

Gate interpretation:

- `engineering_run`: useful for debugging and iteration, but not gate evidence
- `gate_candidate`: required artifacts are present and the capture is internally consistent enough for review
- `release_gate_passed`: must be recorded explicitly in the FR-3B worksheet after manual review; automation does not grant this verdict by itself

What still remains manual:

- whether handle dragging still feels predictable enough for end users
- parity judgment against Acrobat or PDF-XChange
- qualitative UX notes
- signed-output fidelity judgments
- timestamping behavior and any timestamp-required failure paths
- any task steps that require human interpretation rather than observable harness events

See also:

- [phase3_fr3b_acceptance_checklist.md](/home/daekar/SignPDF/Scratch/artifacts/phase3_fr3b_acceptance_checklist.md)
- [phase3_fr3b_acceptance_results.md](/home/daekar/SignPDF/Scratch/artifacts/phase3_fr3b_acceptance_results.md)
- [phase3_handoff_2026-04-03.md](/home/daekar/SignPDF/Scratch/artifacts/phase3_handoff_2026-04-03.md)
- [phase3_parallel_plan.md](/home/daekar/SignPDF/Scratch/phase3_parallel_plan.md)
- [phase3_preview_matrix_template.json](/home/daekar/SignPDF/Scratch/artifacts/phase3_preview_matrix_template.json)
