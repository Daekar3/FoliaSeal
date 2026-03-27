# PDF Signer

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
- Phase 2 kickoff viewer foundations with:
  - render adapter abstraction (`infra.render`) and fallback backend diagnostics
  - deterministic view↔PDF coordinate transform utilities (zoom, pan, rotation, page-box offsets)
  - pre-sign PDF rectangle bounds validation helper
  - page render LRU cache policy primitives for upcoming viewer integration
  - Qt render backend scaffold with graceful diagnostics when Qt bindings are unavailable
  - `ViewerSession` helper for page navigation and zoom/fit interactions
  - `ViewerPerformanceTracker` helper for first-render and navigation timing metrics
  - `ViewerWorkflow` helper that wires renderer output, page geometry, selection transforms, and timing capture for eventual Qt widget integration
- unit tests expanded for render adapter fallback behavior, coordinate transforms, cache policy, and viewer session behavior

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
ruff check .
pytest -q
python -m pdf_signer
```
