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

- preview/output parity still needs signed-output acceptance coverage for representative real PDFs
- the stress matrices still expose remaining text-fit regressions under dense, realistic content
- transparent GIF stamp handling in final signed PDF output is not trustworthy yet; PNG remains the safer image-stamp format
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
- The current Phase 3 finish line is now split into two distinct validation tracks:
  - preview matrices cover layout geometry and content-density regression safety,
  - signed-output acceptance covers cryptographic validity and preview/output parity on the actual
    signed PDF.
- The baseline preview matrices are currently structurally green, but the stress matrices still
  expose the remaining text-fit regressions under realistic content pressure.
- The evidence-contract/gate machinery now exists, but it is an engineering validation layer rather
  than a substitute for signed-output acceptance.
- The remaining engineering focus is on closing the stress-matrix green-path gaps, broadening the
  signed-output acceptance checks, and finishing TSA/timestamp support.

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
- Use it as a manual-review aid for placement, appearance behavior, named-profile workflows, signed-output evidence, and signing-flow validation.
- Harness terminal success is non-gating unless the run also produces the required evidence artifacts.
- The harness JSON is now validated against a machine evidence contract; contradictory captures should be treated as failed gate evidence even if the GUI appeared to finish normally.
- For the current acceptance focus and unresolved items, rely on the Phase 3 checklist and results artifacts rather than treating this README as the project status log.

Signed-output acceptance:

- Preview matrices are for geometry and content-density sweeps.
- Signed-output acceptance is the end-to-end check that the actual signed PDF is cryptographically valid and that its rendered visible appearance matches the reviewed preview within acceptable tolerance.
- The signed-output evidence captured by the harness should be reviewed separately from preview-matrix status.
- A broad representative signed-output matrix is the next acceptance layer after the preview matrices are stable.

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
- lets you click `Capture State` during the same GUI run so one summary JSON can preserve several manually chosen configuration states before you close the harness
- can capture the live preview card as a PNG plus widget geometry and border-to-content distance metrics when `--artifacts-dir` is supplied
- can capture signed-output render evidence when a signing run succeeds, including a rendered crop of the signed annotation region and preview-vs-output comparison metadata
- classifies the run as `engineering_run` or `gate_candidate` and records the automated gate verdict
- validates the capture for internal evidence consistency before writing the artifacts
- writes a results file seeded from the Phase 3 checklist at [`artifacts/phase3_fr3b_acceptance_results.md`](/home/daekar/SignPDF/Scratch/artifacts/phase3_fr3b_acceptance_results.md)
- automatically checks the acceptance items that can be observed directly from the harness

The summary JSON keeps the existing top-level final-state fields and now also includes a
`captured_states` history array. Each manual capture entry stores the current preview snapshot,
preview text, validation text, request snapshot, and backend reservation snapshot so several
configurations can be reviewed from one run.

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
- summary-level text diagnostics broken out into:
  - total clipping-risk scenarios
  - signable clipping-risk scenarios
  - rejected clipping-risk scenarios
  - total text/stamp-overlap scenarios
  - signable text/stamp-overlap scenarios
  - rejected text/stamp-overlap scenarios
- summary-level stamp diagnostics broken out into:
  - total stamp-warning scenarios
  - signable stamp-warning scenarios
  - rejected stamp-warning scenarios
  - total stamp-edge-touch scenarios
  - signable stamp-edge-touch scenarios
  - rejected stamp-edge-touch scenarios

What signed-output acceptance should add on top:

- the signed PDF page render containing the final visible appearance
- a crop of the signed annotation region
- a preview-vs-signed-output comparison image or summary
- cryptographic status details needed to prove the output is not only visually plausible but also actually signed correctly
- explicit evidence that the signed annotation rect landed where requested and that preview/output parity stayed within tolerance

Representative signed acceptance matrix:

```bash
.venv/bin/python -m foliaseal phase3-signing-acceptance-matrix \
  --pdf-path "/absolute/path/to/document.pdf" \
  --certificate-path "/absolute/path/to/signer.p12" \
  --passphrase "secret" \
  --scenario-manifest-path artifacts/preview_sweep_assets/signed_acceptance_matrix.json \
  --artifacts-dir artifacts/signed_acceptance_matrix_run
```

What it writes:

- a signed PDF per scenario
- the signed page render and signed annotation crop
- preview-vs-signed-output side-by-side comparisons
- cryptographic verification details for the embedded signature
- a summary JSON with per-scenario signing/parity verdicts

Use the interactive harness when you want to manipulate the GUI manually. Use the preview matrix when you want a deterministic sweep across saved images, border widths, and rectangle aspect ratios.

Current interpretation of the checked-in preview-matrix summaries:

- treat `signable_*` counts as the true green-path regression signal
- treat `rejected_*` counts as negative-test coverage for cases the validator is already blocking
- stamp warnings now mean border-facing near-border crowding only; text-facing stamp/text
  conflicts are tracked by the text overlap/clipping diagnostics instead of being inferred
  indirectly from stamp-band geometry
- after anti-aliased stamp-content detection was tightened, a remaining 1px border-facing gap is
  treated as acceptable raster clearance rather than a warning; actual border contact is still
  reported explicitly by the stamp edge-touch counts
- the baseline matrices are broad structural sweeps; they are useful for regression safety, but
  they do not by themselves prove realistic content-density coverage
- the stress matrices are the realistic-content companion sweeps; they use anonymized long-field
  fixture data shaped to reproduce the pressure of real signing identities without baking user
  strings into the repository
- as of the latest rechecks:
  - baseline `single_line`: `0` signable text clipping risks, `42` rejected text clipping risks,
    `0` signable stamp warnings, `0` signable stamp edge-touch cases
  - baseline `multi_line`: `0` signable text risks, `0` signable stamp warnings,
    `0` signable stamp edge-touch cases
  - baseline `wrapped_block`: `0` signable text risks, `0` signable stamp warnings,
    `0` signable stamp edge-touch cases
  - stress `single_line`: `150` signable text clipping risks, `680` rejected text clipping risks
  - stress `multi_line`: `18` signable text clipping risks, `264` rejected text clipping risks
  - stress `wrapped_block`: `15` signable text clipping risks, `423` rejected text clipping risks

In other words, the baseline green path is still structurally clean, but the new stress corpus
immediately exposed remaining green-path text-fit problems under realistic content pressure. That
is an expected and useful result of the stronger methodology, not a reason to ignore the stress
suite.

The repo now also includes a reusable local sweep fixture set under
`artifacts/preview_sweep_assets/`, including `sweep_fixture.pdf`, `test_identity.p12`, three
transparent stamp images, and `single_line_matrix.json` for unattended `single_line` preview
sweeps. The fixture set now includes both baseline and stress full-matrix manifests for all three
current layout families:

- `single_line_full_matrix.json`
- `multi_line_full_matrix.json`
- `wrapped_block_full_matrix.json`
- `single_line_full_matrix_stress.json`
- `multi_line_full_matrix_stress.json`
- `wrapped_block_full_matrix_stress.json`

Those checked-in manifests demonstrate three practical sweep controls that matter for layout triage:

- `visible_fields` to constrain which derived fields participate in a compact preview scenario
- explicit text-size variation scenarios so preview regressions can be checked at more than one
  `font_size_pt`
- `fixture_profile` to swap between the short generic test corpus and the anonymized
  long-field stress corpus

Status note:

- the checked-in baseline `single_line`, `multi_line`, and `wrapped_block` matrices are currently
  green in automation
- the checked-in stress matrices are intentionally not green yet; they are currently exposing
  remaining green-path clipping regressions under realistic content pressure
- preview typography semantics are layout-invariant: the selected point size means the same thing in
  `single_line`, `multi_line`, and `wrapped_block`; layout mode may change reservation geometry,
  wrapping, and fit outcomes, but it must not silently change the meaning of the chosen text size
- harness captures written with `--summary-json-path` must now also preserve preview render
  artifacts; missing preview image paths in saved captures are treated as an evidence-contract
  defect rather than an optional convenience
- use both baseline and stress matrices as the regression net, not as a substitute for the pending
  manual harness confirmation with real signing assets

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
