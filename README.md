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
- `render_signing_preview()` should turn the normalized draft state into a preview representation.
  - It should be treated as the single source of truth for preview formatting.
  - The Qt shell should reuse it rather than rebuilding preview semantics in widget code.
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
  - executor-backed sign/apply integration seams
- The shell can now call an injected signing executor and surface success/failure results.
- The key integration rule is to avoid duplicating semantics across layers.
  - Workflow code should normalize the draft.
  - Preview code should render that normalized state.
  - Qt code should orchestrate user interaction and dispatch, not reinterpret the model.

Not yet production-ready:

- a concrete production signing backend behind the shell's executor seam
- final end-to-end FR-3B acceptance validation

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
- For the current acceptance focus and unresolved items, rely on the Phase 3 checklist and results artifacts rather than treating this README as the project status log.

Run it against a representative PDF:

```bash
.venv/bin/python -m foliaseal phase3-signing-harness \
  --pdf-path "/path/to/representative.pdf" \
  --summary-json-path artifacts/phase3_harness_capture.json \
  --checklist-results-path artifacts/phase3_fr3b_acceptance_results.md
```

What it does:

- launches the current Qt signing shell on the chosen PDF
- records a structured capture of preview availability, selection count, sign-request count, and any surfaced errors
- writes a results file seeded from the Phase 3 checklist at [`artifacts/phase3_fr3b_acceptance_results.md`](/home/daekar/SignPDF/Scratch/artifacts/phase3_fr3b_acceptance_results.md)
- automatically checks the acceptance items that can be observed directly from the harness

What still remains manual:

- whether handle dragging still feels predictable enough for end users
- parity judgment against Acrobat or PDF-XChange
- qualitative UX notes
- signed-output fidelity judgments
- any task steps that require human interpretation rather than observable harness events

See also:

- [phase3_fr3b_acceptance_checklist.md](/home/daekar/SignPDF/Scratch/artifacts/phase3_fr3b_acceptance_checklist.md)
- [phase3_fr3b_acceptance_results.md](/home/daekar/SignPDF/Scratch/artifacts/phase3_fr3b_acceptance_results.md)
- [phase3_parallel_plan.md](/home/daekar/SignPDF/Scratch/phase3_parallel_plan.md)
